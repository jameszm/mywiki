import unittest

from kloop.chunking import finalize_item
from kloop.index import BM25, Index, rrf_fuse, tokenize
from kloop.models import KnowledgeItem


def item(id_: str, text: str, kind: str = "doc", acl=None, version: int = 1, now: str = "2026-01-01T00:00:00") -> KnowledgeItem:
    it = KnowledgeItem(id=id_, source_id="s", locator=f"docs/{id_}.md", kind=kind, title=id_, text=text, acl=acl or ["all"], heading_path=id_)
    return finalize_item(it, version, now)


class TokenizeTests(unittest.TestCase):
    def test_identifiers_and_cjk(self):
        toks = tokenize("ranking.model.learning_rate 学习率默认值是多少 FeatureFetchTimeout")
        for t in ("ranking.model.learning_rate", "learning_rate", "learning", "rate", "学习", "习率", "featurefetchtimeout", "feature", "timeout"):
            self.assertIn(t, toks)
        self.assertNotIn("多少", toks)  # 停用二元组
        self.assertEqual(tokenize("batch_size=4096"), ["batch_size", "batch", "size", "4096"])


class BM25Tests(unittest.TestCase):
    def test_ordering_tf_and_idf(self):
        bm = BM25()
        bm.add("A", tokenize("learning rate learning rate"))  # 同长度下 tf 高者得分高
        bm.add("B", tokenize("learning rate batch size"))
        bm.add("C", tokenize("batch size tuning"))
        bm.add("D", tokenize("kafka partition count"))
        scores = bm.score(tokenize("learning rate"))
        self.assertGreater(scores["A"], scores["B"])
        self.assertNotIn("C", scores)
        rare = bm.score(tokenize("kafka"))
        self.assertEqual(list(rare), ["D"])
        self.assertGreater(bm.idf("kafka"), bm.idf("learning"))
        self.assertLess(scores["A"] / bm.ideal_score(tokenize("learning rate")), 1.0)
        bm.remove("A")
        self.assertNotIn("A", bm.score(tokenize("learning rate")))


class RRFTests(unittest.TestCase):
    def test_fusion_math(self):
        fused = rrf_fuse([["a", "b"], ["b", "a"]], k=60)
        self.assertAlmostEqual(fused["a"], fused["b"])
        fused = rrf_fuse([["a", "b"], ["a", "c"]], k=60)
        self.assertAlmostEqual(fused["a"], 2 / 61)
        self.assertAlmostEqual(fused["b"], 1 / 62)
        self.assertEqual(max(fused, key=fused.get), "a")


class IndexSearchTests(unittest.TestCase):
    def setUp(self):
        self.idx = Index()
        self.idx.add_items([
            item("timeout", "特征取数超时默认 50ms, 超时抛出 FeatureFetchTimeout 异常。"),
            item("rollback", "执行 deployctl rollback 回滚到上一个版本。"),
            item("secret", "特征取数超时的内部排查记录 (仅 oncall 可见)。", acl=["oncall"]),
            item("cfg", "ranking.serving.timeout_ms = 50", kind="config"),
        ])

    def test_search_ranks_relevant_first_with_why(self):
        hits = self.idx.search("特征取数超时默认多少 FeatureFetchTimeout")
        self.assertEqual(hits[0].item.id, "timeout")
        self.assertIn("BM25", hits[0].why)
        self.assertTrue(0 <= hits[0].bm25_norm <= 1)
        self.assertGreater(hits[0].cosine, 0)

    def test_filters_kind_and_acl(self):
        self.assertEqual([h.item.id for h in self.idx.search("timeout_ms", kinds=("config",))], ["cfg"])
        ids_public = [h.item.id for h in self.idx.search("特征取数超时", acl=["ranking-team"])]
        self.assertNotIn("secret", ids_public)
        ids_oncall = [h.item.id for h in self.idx.search("特征取数超时", acl=["oncall"])]
        self.assertIn("secret", ids_oncall)
        self.assertIn("secret", [h.item.id for h in self.idx.search("特征取数超时")])  # 不传 acl 不过滤

    def test_validity_and_as_of(self):
        old = item("timeout", "特征取数超时默认 30ms (旧版)。", version=0, now="2025-12-01T00:00:00")
        old.valid_to, old.status = "2026-01-01T00:00:00", "superseded"
        self.idx.add_items([old])
        self.assertEqual([h.item.version for h in self.idx.search("特征取数超时默认") if h.item.id == "timeout"], [1])
        as_of = self.idx.search("特征取数超时默认", as_of="2025-12-15T00:00:00")
        self.assertEqual([h.item.version for h in as_of if h.item.id == "timeout"], [0])

    def test_incremental_remove(self):
        self.idx.remove_items(["rollback@1"])
        self.assertEqual([h.item.id for h in self.idx.search("deployctl rollback")], [])
        self.assertEqual(len(self.idx), 3)


if __name__ == "__main__":
    unittest.main()
