import tempfile
import unittest
from pathlib import Path

from kloop.evaluate import (METRICS, EvalRun, GoldenEntry, citation_precision, compare_runs, evaluate_entry, groundedness, keyword_coverage,
                            load_golden, mine_golden_candidates, mrr, ndcg_at_k, recall_at_k, run_eval, select_entries, write_reports)
from kloop.feedback import log_feedback, log_turn
from kloop.index import Index
from kloop.llm import HeuristicLLM
from kloop.answer import compose_answer
from kloop.search import deep_search
from kloop.store import Store
from kloop.sync import sync_source
from tests.helpers import CONFIG_V2, write_corpus

T1, T2 = "2026-01-01T00:00:00.000000+00:00", "2026-01-02T00:00:00.000000+00:00"


class MetricMathTests(unittest.TestCase):
    def test_recall_mrr_ndcg(self):
        ranked, rel = ["a", "b", "c", "a", "d"], ["a", "c", "e"]
        self.assertAlmostEqual(recall_at_k(ranked, rel, 5), 2 / 3)
        self.assertAlmostEqual(recall_at_k(ranked, rel, 1), 1 / 3)
        self.assertAlmostEqual(mrr(ranked, rel), 1.0)
        self.assertAlmostEqual(mrr(["x", "c"], rel), 0.5)
        self.assertEqual(mrr(["x"], rel), 0.0)
        self.assertAlmostEqual(ndcg_at_k(ranked, rel, 5), 0.7039, places=3)  # (1 + 1/log2 4) / (1 + 1/log2 3 + 1/log2 4)
        self.assertEqual(ndcg_at_k(ranked, [], 5), 1.0)
        self.assertAlmostEqual(ndcg_at_k(["c", "a"], ["a", "c"], 10), 1.0)

    def test_answer_metrics(self):
        self.assertAlmostEqual(keyword_coverage("默认 50ms 超时", ["50ms", "FeatureFetchTimeout"]), 0.5)
        self.assertAlmostEqual(citation_precision(["a", "b", "c"], ["a"]), 1 / 3)
        self.assertEqual(citation_precision([], ["a"]), 0.0)
        ans = "根据知识库中的相关内容：\n- 特征取数超时默认 50ms, 超时抛出 FeatureFetchTimeout。 [K-aaaaaaaaaaaa]\n- 这句话完全是编造的内容。 [K-aaaaaaaaaaaa]\n\n参考来源:\n[K-aaaaaaaaaaaa] x"
        self.assertAlmostEqual(groundedness(ans, ["特征取数超时默认 50ms, 超时抛出 FeatureFetchTimeout 异常。"]), 0.5)

    def test_select_entries(self):
        entries = [GoldenEntry("a", "q", [], [], expects_version=1), GoldenEntry("b", "q", [], [], expects_version=1, valid_until_version=1),
                   GoldenEntry("c", "q", [], [], expects_version=2)]
        self.assertEqual([e.id for e in select_entries(entries, 1)], ["a", "b"])
        self.assertEqual([e.id for e in select_entries(entries, 2)], ["a", "c"])
        self.assertEqual([e.id for e in select_entries(entries, 2, freshness_only=True)], ["c"])
        self.assertEqual([e.id for e in select_entries(entries, 1, freshness_only=True)], [])


class FreshnessAndRegressionTests(unittest.TestCase):
    def test_freshness_logic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = write_corpus(Path(tmp) / "c")
            store, llm = Store(":memory:"), HeuristicLLM()
            sync_source(store, "src", root, now=T1)
            write_corpus(root, config=CONFIG_V2)
            sync_source(store, "src", root, now=T2)
            entry = GoldenEntry("f1", "learning_rate 默认值", ["configs/ranking.yaml"], ["0.0005"], kind="freshness", expects_version=2)
            latest = store.latest_versions()
            rec = evaluate_entry(store, Index.from_store(store), entry, llm, latest)
            self.assertTrue(rec["top_hit_current"] and rec["no_superseded_cited"] and rec["freshness_pass"])
            self.assertEqual(rec["keyword_coverage"], 1.0)
            stale_index = Index()
            stale_index.add_items([it for it in store.items_as_of("2026-01-01T12:00:00.000000+00:00")])
            for it in stale_index.items.values():  # 让旧版本看起来“当前有效”, 模拟索引未同步的情况
                it.valid_to = None
            rec_stale = evaluate_entry(store, stale_index, entry, llm, latest)
            self.assertFalse(rec_stale["top_hit_current"])
            self.assertFalse(rec_stale["no_superseded_cited"])
            self.assertEqual(rec_stale["keyword_coverage"], 0.0)

    def test_run_eval_reports_and_regression(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = write_corpus(Path(tmp) / "c")
            store, llm = Store(":memory:"), HeuristicLLM()
            sync_source(store, "src", root, now=T1)
            golden = [GoldenEntry("g1", "特征取数超时默认是多少", ["docs/guide.md", "configs/ranking.yaml"], ["50"], expects_version=1),
                      GoldenEntry("g2", "Kafka 分区数怎么配置", [], [], kind="unanswerable", expects_version=1)]
            run = run_eval(store, Index.from_store(store), golden, llm, name="t", corpus_version=1)
            self.assertEqual(run.summary["n"], 2)
            self.assertEqual(run.summary["abstain_ok_rate"], 1.0)
            self.assertIsNotNone(store.get_eval_run(run.id))
            jp, mp = write_reports(run, Path(tmp) / "out")
            self.assertTrue(jp.exists() and mp.exists() and "g1" in mp.read_text(encoding="utf-8"))
            worse = EvalRun("b", "b", T2, dict(run.summary), [dict(r) for r in run.per_query])
            worse.per_query[0]["recall@10"] -= 0.5
            worse.per_query[0]["mrr"] -= 0.5
            diff = compare_runs(run, worse)
            self.assertEqual(diff["common"], 2)
            self.assertEqual([r["id"] for r in diff["regressions"]], ["g1"])
            self.assertAlmostEqual(diff["per_query"][0]["d_recall@10"], -0.5)

    def test_golden_mining_and_loader(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = write_corpus(Path(tmp) / "c")
            store, llm = Store(":memory:"), HeuristicLLM()
            sync_source(store, "src", root, now=T1)
            idx = Index.from_store(store)
            res = deep_search(idx, "FeatureFetchTimeout 超时默认多少", llm=llm)
            ans = compose_answer("FeatureFetchTimeout 超时默认多少", res, llm)
            turn = log_turn(store, "FeatureFetchTimeout 超时默认多少", "u", "s", res, ans, metadata={"corpus_version": 1})
            self.assertTrue(ans.cited_item_ids)
            self.assertEqual(len(store.citations(turn.id)), len(ans.cited_item_ids))
            self.assertEqual(mine_golden_candidates(store), [])
            log_feedback(store, turn.id, "explicit", 1)
            cands = mine_golden_candidates(store)
            self.assertEqual(len(cands), 1)
            self.assertIn("FeatureFetchTimeout", cands[0]["relevant_keywords"])
            self.assertTrue(cands[0]["relevant_locators"])
            path = Path(tmp) / "g.jsonl"
            path.write_text('{"id": "x", "query": "q", "relevant_locators": ["a"], "relevant_keywords": ["k"], "expects_version": 2}\n', encoding="utf-8")
            self.assertEqual(load_golden(path)[0].expects_version, 2)



class EvaluateRegressionTests(unittest.TestCase):
    """回归: 黄金集 null 字段 / 新鲜度条目忽略 valid_until_version / 弃答 groundedness / 回归汇总差值混入不同 query 集 / 陈旧索引中的墓碑被判为当前版本。"""

    def test_load_golden_tolerates_null_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "g.jsonl"
            path.write_text('{"id": 7, "query": "Kafka 分区数", "relevant_locators": null, "relevant_keywords": null, "kind": null, '
                            '"expects_version": null, "notes": null, "valid_until_version": "1"}\n', encoding="utf-8")
            e = load_golden(path)[0]
            self.assertEqual((e.id, e.relevant_locators, e.relevant_keywords, e.kind, e.expects_version, e.notes, e.valid_until_version),
                             ("7", [], [], "doc", 1, "", 1))
            self.assertTrue(e.expects_abstain)
            self.assertEqual((mrr([], e.relevant_locators), recall_at_k([], e.relevant_locators, 5)), (1.0, 1.0))

    def test_select_entries_freshness_respects_valid_until(self):
        entries = [GoldenEntry("a", "q", ["x"], [], expects_version=2, valid_until_version=2), GoldenEntry("b", "q", ["x"], [], expects_version=2)]
        self.assertEqual([e.id for e in select_entries(entries, 2, freshness_only=True)], ["a", "b"])
        self.assertEqual([e.id for e in select_entries(entries, 3, freshness_only=True)], ["b"])
        self.assertEqual([e.id for e in select_entries(entries, 3)], ["b"])

    def test_abstained_answer_is_not_scored_as_ungrounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = write_corpus(Path(tmp) / "c")
            store, llm = Store(":memory:"), HeuristicLLM()
            sync_source(store, "src", root, now=T1)
            entry = GoldenEntry("u", "Kafka 分区数怎么配置", [], [], kind="unanswerable")
            rec = evaluate_entry(store, Index.from_store(store), entry, llm, store.latest_versions())
            self.assertTrue(rec["abstained"] and rec["abstain_ok"])
            self.assertEqual((rec["groundedness"], rec["citation_precision"], rec["keyword_coverage"]), (1.0, 1.0, 1.0))
        # 函数本身的语义不变: 有断言句但无引用仍为 0
        self.assertEqual(groundedness("根据知识库中的相关内容：\n- 这是一条没有引用支撑的断言句子。", []), 0.0)

    def test_compare_runs_summary_delta_uses_common_queries_only(self):
        def row(id_, v):
            return {"id": id_, "query": id_, **{m: v for m in METRICS}}
        base = EvalRun("b", "b", T1, {m: 0.5 for m in METRICS}, [row("q1", 1.0), row("q2", 0.0)])
        new = EvalRun("n", "n", T2, {m: 1.0 for m in METRICS}, [row("q1", 1.0), row("q3", 1.0)])  # q2 只在 base, q3 只在 new
        diff = compare_runs(base, new)
        self.assertEqual(diff["common"], 1)
        self.assertEqual(diff["summary_delta"]["recall@10"], 0.0)  # 共同 query q1 无变化; 整体 summary 之差 (+0.5) 只是条目构成不同
        self.assertEqual((diff["regressions"], diff["improvements"]), ([], []))
        self.assertEqual(compare_runs(base, EvalRun("e", "e", T2, {}, []))["summary_delta"]["mrr"], 0.0)  # 无共同 query

    def test_top_hit_current_uses_store_truth_for_tombstones(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = write_corpus(Path(tmp) / "c")
            store, llm = Store(":memory:"), HeuristicLLM()
            sync_source(store, "src", root, now=T1)
            write_corpus(root, with_code=False)  # 删除代码文件 -> 其条目成为墓碑 (也是该 id 的最新版本)
            sync_source(store, "src", root, now=T2)
            stale = Index()
            stale.add_items(store.items_as_of("2026-01-01T12:00:00.000000+00:00"))
            for it in stale.items.values():
                it.valid_to = None  # 索引未同步: 墓碑版本仍被当作当前有效
            entry = GoldenEntry("f", "FeatureClient.fetch 超时 timeout_ms", ["code/client.py"], ["timeout_ms"], kind="freshness", expects_version=2)
            rec = evaluate_entry(store, stale, entry, llm, store.latest_versions())
            self.assertEqual(rec["top_locators"][0], "code/client.py")
            self.assertFalse(rec["top_hit_current"])
            self.assertFalse(rec["freshness_pass"])


if __name__ == "__main__":
    unittest.main()
