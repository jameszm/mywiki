import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from kloop.chunking import finalize_item
from kloop.feedback import log_feedback
from kloop.models import CitationEvent, ConversationTurn, KnowledgeItem, RetrievalEvent
from kloop.scoring import compute_scores, detect_near_duplicates, detect_value_conflicts, rank_weights
from kloop.store import Store
from kloop.sync import sync_source
from tests.helpers import DOC_V2, write_corpus

T0, T1, T2 = "2025-12-31T00:00:00.000000+00:00", "2026-01-01T00:00:00.000000+00:00", "2026-01-02T00:00:00.000000+00:00"


def mk(id_: str, text: str, kind: str = "doc", locator: str | None = None, kv: dict | None = None) -> KnowledgeItem:
    it = KnowledgeItem(id=id_, source_id="s", locator=locator or f"docs/{id_}.md", kind=kind, title=id_, text=text, heading_path=id_,
                       metadata={"kv": kv} if kv else {})
    return finalize_item(it, 1, T1)


def log(store: Store, turn_id: str, query: str, retrieved: list[str], cited: list[str], abstained: bool = False, max_score: float = 0.5) -> None:
    turn = ConversationTurn(turn_id, "s", "u", query, "answer", f"{T1}{turn_id}", max_score=max_score, abstained=abstained)
    store.log_turn(turn, [RetrievalEvent(turn_id, k.split("@")[0], int(k.split("@")[1]), r, 1.0 / r, {}, 0) for r, k in enumerate(retrieved, 1)],
                   [CitationEvent(turn_id, k.split("@")[0], int(k.split("@")[1]), p) for p, k in enumerate(cited, 1)])


class CreditAssignmentTests(unittest.TestCase):
    def test_rank_weights(self):
        w = rank_weights(3)
        self.assertAlmostEqual(sum(w), 1.0)
        self.assertTrue(w[0] > w[1] > w[2])
        self.assertAlmostEqual(rank_weights(2)[0], 2 / 3)

    def test_helpfulness_shares(self):
        store = Store(":memory:")
        for it in (mk("A", "A 内容 " * 10), mk("B", "B 内容 " * 10), mk("C", "C 内容 " * 10)):
            store.insert_item(it)
        log(store, "t1", "q1", ["A@1", "B@1", "C@1"], ["A@1", "B@1"])
        log_feedback(store, "t1", "explicit", 1)
        log(store, "t2", "q2", ["B@1", "C@1"], ["B@1"])
        log_feedback(store, "t2", "explicit", -1)
        log_feedback(store, "t2", "reformulated")
        rep = compute_scores(store, now=T2)
        by = {s.item_id: s for s in rep.scores}
        self.assertAlmostEqual(by["A"].helpfulness, 2 / 3, places=4)
        self.assertAlmostEqual(by["B"].helpfulness, ((1 / 3) + (-1.5)) / 2, places=4)
        self.assertEqual((by["A"].exposures, by["A"].citations, by["A"].citation_rate), (1, 1, 1.0))
        self.assertEqual((by["B"].exposures, by["B"].citations), (2, 2))
        self.assertEqual((by["C"].exposures, by["C"].citations), (2, 0))
        self.assertGreater(by["A"].health, by["C"].health)
        self.assertGreater(by["C"].health, by["B"].health)
        self.assertTrue(any(t.task_type == "deprecate" and t.item_ids == ["B@1"] for t in rep.tasks))  # 两次引用均为负 -> 建议下线
        self.assertEqual(len(store.item_scores()), 3)


class StalenessTests(unittest.TestCase):
    def test_flags_after_source_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = write_corpus(Path(tmp) / "c")
            store = Store(":memory:")
            sync_source(store, "src", root, now=T1)
            docs = store.current_items_by_locator("src", "docs/guide.md")
            rollback = next(d for d in docs if "回滚" in d.heading_path)
            fetch = next(d for d in docs if "取数" in d.heading_path)
            log(store, "t1", "回滚", [rollback.key], [rollback.key])  # 引用的是 v1
            write_corpus(root, doc=DOC_V2)
            sync_source(store, "src", root, now=T2)
            rep = compute_scores(store, now=T2)
            by = {s.key: s for s in rep.scores}
            self.assertIn("file_changed_since_verified", by[fetch.key].staleness_flags)  # 未变章节, 但文件变了
            self.assertIn("superseded", by[f"{rollback.id}@1"].staleness_flags)
            self.assertEqual(by[f"{rollback.id}@2"].staleness_flags, [])
            self.assertLess(by[f"{rollback.id}@1"].health, by[f"{rollback.id}@2"].health)
            self.assertTrue(any(t.task_type == "verify" and t.item_ids == [fetch.key] for t in rep.tasks))


class ConflictTests(unittest.TestCase):
    def test_near_duplicates(self):
        base = "模型上线分三步: 离线评估达标, 小流量实验, 全量发布。每一步都有明确的准入门槛, 未达标不得进入下一步。整个流程以工单形式跟踪。"
        a = mk("a", base, locator="docs/a.md")
        b = mk("b", base.replace("工单", "邮件"), locator="docs/b.md")
        c = mk("c", "完全不同的内容, 讲的是特征平台的在线取数与超时重试策略以及降级开关。", locator="docs/c.md")
        same = mk("d", base, locator="docs/d.md")
        pairs = detect_near_duplicates([a, b, c])
        self.assertEqual([(p[0], p[1]) for p in pairs], [("a@1", "b@1")])
        self.assertGreaterEqual(pairs[0][2], 0.6)
        self.assertEqual(detect_near_duplicates([a, same]), [])  # 完全相同不算冲突 (是重复)

    def test_value_conflicts(self):
        cfg = mk("cfg", "ranking.model.learning_rate = 0.0005", kind="config", locator="configs/r.yaml", kv={"ranking.model.learning_rate": "0.0005"})
        doc = mk("sop", "学习率 `ranking.model.learning_rate` 默认 0.001, 发散时减半。", locator="docs/sop.md")
        ok = mk("ok", "学习率 `ranking.model.learning_rate` 默认值为 0.0005。", locator="docs/ok.md")
        op = mk("op", "紧急时把 ranking.model.learning_rate = 0.01 作为临时操作。", locator="docs/op.md")
        conflicts = detect_value_conflicts([cfg, doc, ok, op])
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["path"], "ranking.model.learning_rate")
        self.assertEqual(conflicts[0]["keys"], ["sop@1", "cfg@1"])
        cfg2 = mk("cfg2", "ranking.model.learning_rate = 0.001", kind="config", locator="configs/other.yaml", kv={"ranking.model.learning_rate": "0.001"})
        self.assertTrue(any(c["keys"] == ["cfg2@1", "cfg@1"] for c in detect_value_conflicts([cfg, cfg2])))


class GapAndTaskTests(unittest.TestCase):
    def test_gap_clusters_and_idempotent_tasks(self):
        store = Store(":memory:")
        store.insert_item(mk("old", "旧版发布流程 (废弃), 通过邮件审批。"))
        log(store, "t1", "Kafka 消费组的分区数怎么配置", ["old@1"], [], abstained=True, max_score=0.05)
        log(store, "t2", "kafka topic 分区数量在哪里配置", [], [], abstained=True, max_score=0.0)
        log(store, "t3", "GPU 配额怎么申请", [], [], abstained=True, max_score=0.0)
        log_feedback(store, "t3", "explicit", -1)
        rep = compute_scores(store, now=T2)
        keys = {g.key: g for g in rep.gaps}
        self.assertEqual(set(keys), {"kafka", "gpu"})
        self.assertEqual(sorted(keys["kafka"].turn_ids), ["t1", "t2"])
        self.assertEqual(keys["gpu"].negative_feedback, 1)
        types = rep.tasks_by_type()
        self.assertEqual(len(types["fill_gap"]), 2)
        self.assertEqual(len(types["deprecate"]), 1)  # 自称废弃且被检索到
        n_open = len(store.curation_tasks("open"))
        compute_scores(store, now=T2)  # 幂等: 重算不产生重复任务
        self.assertEqual(len(store.curation_tasks("open")), n_open)
        store.conn.execute("DELETE FROM turns WHERE id='t3'")
        store.conn.commit()
        rep3 = compute_scores(store, now=T2)
        self.assertEqual(rep3.resolved_tasks, 1)  # gpu 缺口不再成立 -> resolved
        self.assertEqual(len(store.curation_tasks("resolved")), 1)



class ScoringRegressionTests(unittest.TestCase):
    """回归: 缺口标签不确定 (hash 随机化) / open 任务重算后证据与优先级不刷新。"""

    def test_gap_label_is_deterministic_across_hash_seeds(self):
        snippet = (
            "from kloop.store import Store\nfrom kloop.models import ConversationTurn\nfrom kloop.scoring import compute_scores\n"
            "s = Store(':memory:')\n"
            "s.log_turn(ConversationTurn('t1', 's', 'u', 'RedisConnectionReset 是什么错误', 'a', '2026-01-01T00:00:00', max_score=0.0, abstained=True), [], [])\n"
            "r = compute_scores(s, now='2026-01-02T00:00:00')\nprint(r.gaps[0].key, r.tasks[0].fingerprint)\n"
        )
        outs = set()
        for seed in ("1", "2", "3"):
            env = {**os.environ, "PYTHONHASHSEED": seed, "PYTHONPATH": str(Path(__file__).resolve().parent.parent)}
            outs.add(subprocess.run([sys.executable, "-c", snippet], env=env, capture_output=True, text=True, check=True).stdout.strip())
        self.assertEqual(outs, {"connection fill_gap::connection"})  # 同频标识符按字典序取第一个, 与 set 迭代顺序无关

    def test_open_task_refreshed_on_recompute(self):
        store = Store(":memory:")
        store.insert_item(mk("A", "A 内容 " * 10))
        for t in ("t1", "t2", "t3"):
            log(store, t, "q", ["A@1"], [])
        rep = compute_scores(store, now=T1)
        task = next(t for t in rep.tasks if t.task_type == "verify")
        self.assertEqual((task.priority, task.evidence["exposures"]), (0.46, 3))
        for t in ("t4", "t5", "t6", "t7"):
            log(store, t, "q", ["A@1"], [])
        rep2 = compute_scores(store, now=T2)
        task2 = next(t for t in rep2.tasks if t.task_type == "verify")
        self.assertEqual(task2.id, task.id)  # 同一 fingerprint, 不产生重复任务
        self.assertEqual((task2.priority, task2.evidence["exposures"]), (0.54, 7))
        self.assertIn("被检索 7 次", task2.reason)
        self.assertEqual(len(store.curation_tasks("open")), 1)


if __name__ == "__main__":
    unittest.main()
