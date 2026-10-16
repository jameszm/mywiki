import unittest

from kloop.chunking import split_text, stable_id
from kloop.connectors.config_files import ConfigConnector, flatten, parse_scalar, parse_yaml
from kloop.connectors.log_files import LogConnector, link_templates_to_docs, mask_line, mine_templates, template_keywords
from kloop.connectors.markdown_docs import MarkdownConnector, parse_front_matter, parse_sections
from kloop.connectors.python_code import PythonConnector
from kloop.models import RawDocument

YAML = """# 顶部注释
ranking:
  model:
    name: dnn_v3          # 模型名
    learning_rate: 0.001
    layers: [512, 256, 128]
    quoted: "a: b # 不是注释"
  serving:
    degrade_mode: false
    note: null
features:
  - name: user_click_cnt_7d
    dtype: int
  - name: item_ctr_1d
    dtype: float
tags:
  - a
  - b
"""


def raw(locator: str, text: str, kind: str) -> RawDocument:
    return RawDocument(locator=locator, text=text, mtime=0.0, sha256="x", kind=kind)


class YamlParserTests(unittest.TestCase):
    def test_nested_maps_lists_scalars_comments(self):
        data, comments = parse_yaml(YAML)
        self.assertEqual(data["ranking"]["model"]["name"], "dnn_v3")
        self.assertEqual(data["ranking"]["model"]["learning_rate"], 0.001)
        self.assertEqual(data["ranking"]["model"]["layers"], [512, 256, 128])
        self.assertEqual(data["ranking"]["model"]["quoted"], "a: b # 不是注释")
        self.assertIs(data["ranking"]["serving"]["degrade_mode"], False)
        self.assertIsNone(data["ranking"]["serving"]["note"])
        self.assertEqual(data["features"][1], {"name": "item_ctr_1d", "dtype": "float"})
        self.assertEqual(data["tags"], ["a", "b"])
        self.assertEqual(comments["ranking.model.name"], "模型名")
        self.assertEqual(comments["ranking"], "顶部注释")

    def test_flatten_and_scalars(self):
        data, _ = parse_yaml(YAML)
        pairs = dict(flatten(data))
        self.assertEqual(pairs["ranking.model.layers"], [512, 256, 128])
        self.assertEqual(pairs["features[0].name"], "user_click_cnt_7d")
        self.assertEqual(parse_scalar("42"), 42)
        self.assertEqual(parse_scalar("'x'"), "x")
        self.assertEqual(parse_scalar("yes"), True)
        self.assertEqual(parse_scalar("[1, a]"), [1, "a"])

    def test_config_connector_items(self):
        items = ConfigConnector().extract(raw("configs/r.yaml", YAML, "config"), "src")
        self.assertEqual([i.heading_path for i in items], ["ranking", "features", "tags"])
        self.assertEqual(items[0].metadata["kv"]["ranking.model.learning_rate"], "0.001")
        self.assertIn("ranking.model.name = dnn_v3  # 模型名", items[0].text)
        json_items = ConfigConnector().extract(raw("configs/e.json", '{"traffic_ratio": 0.05, "buckets": ["a", "b"]}', "config"), "src")
        self.assertEqual({i.heading_path for i in json_items}, {"traffic_ratio", "buckets"})


class LogMiningTests(unittest.TestCase):
    def test_masking(self):
        masked = mask_line("FeatureFetchTimeout key=user:123 ip=10.1.2.3:6379 file=/models/a.pb hex=0xdead p99 55ms id=job-12345 date=2026-10-01")
        for tok in ("<NUM>", "<IP>", "<PATH>", "<HEX>", "<ID>", "<DATE>", "p99"):
            self.assertIn(tok, masked)
        self.assertNotIn("123", masked)

    def test_templates_counts_samples_severity(self):
        lines = [
            "2026-10-01 08:00:00 ERROR FeatureFetchTimeout key=user:1 timeout_ms=50",
            "2026-10-01 08:00:01 ERROR FeatureFetchTimeout key=user:2 timeout_ms=50",
            "2026-10-01 08:00:02 ERROR FeatureFetchTimeout key=user:3 timeout_ms=80",
            "2026-10-01 08:00:03 ERROR FeatureFetchTimeout key=user:4 timeout_ms=50",
            "2026-10-01 08:00:04 WARN p99 latency 70ms exceeds 50ms threshold",
            "2026-10-01 08:00:05 WARN p99 latency 90ms exceeds 50ms threshold",
            "2026-10-01 08:00:06 ERROR ModelLoadError checksum mismatch file=/m/a.pb",
            "garbage line without level",
        ]
        tpls = mine_templates(lines)
        self.assertEqual([t.count for t in tpls], [4, 2, 1])
        self.assertEqual(tpls[0].template, "FeatureFetchTimeout key=user:<NUM> timeout_ms=<NUM>")
        self.assertEqual(len(tpls[0].samples), 3)
        self.assertEqual((tpls[0].first_seen, tpls[0].last_seen), ("2026-10-01 08:00:00", "2026-10-01 08:00:03"))
        self.assertEqual(tpls[1].level, "WARN")
        self.assertEqual(template_keywords(tpls[0].template), ["FeatureFetchTimeout", "timeout_ms", "user"])
        items = LogConnector().extract(raw("logs/s.log", "\n".join(lines), "log"), "src")
        self.assertEqual(items[0].metadata["count"], 4)
        self.assertIn("出现次数: 4", items[0].text)

    def test_link_to_docs(self):
        logs = LogConnector().extract(raw("logs/s.log", "2026-10-01 08:00:00 ERROR FeatureFetchTimeout key=user:1 timeout_ms=50", "log"), "src")
        docs = MarkdownConnector().extract(raw("docs/r.md", "# R\n\n## 告警\n\nFeatureFetchTimeout 告警的处理步骤。\n\n## 其它\n\n无关内容。", "doc"), "src")
        n = link_templates_to_docs(logs, docs)
        self.assertEqual(n, 1)
        self.assertEqual(logs[0].metadata["related_docs"][0]["section"], "R > 告警")


class MarkdownTests(unittest.TestCase):
    def test_sections_and_fences(self):
        text = "# T\n\n前言。\n\n## A\n\n```\n# 不是标题\n```\n正文 A。\n\n### A1\n\n正文 A1。\n\n## B\n\n正文 B。"
        secs = parse_sections(text)
        self.assertEqual([s[0] for s in secs], ["T", "T > A", "T > A > A1", "T > B"])
        self.assertIn("# 不是标题", secs[1][2])

    def test_front_matter_and_stable_ids(self):
        text = "---\nacl: [ranking-team, oncall]\n---\n# 文档\n\n## 节\n\n内容。"
        meta, body = parse_front_matter(text)
        self.assertEqual(meta["acl"], "[ranking-team, oncall]")
        items = MarkdownConnector().extract(raw("docs/x.md", text, "doc"), "src")
        self.assertEqual(items[0].acl, ["ranking-team", "oncall"])
        again = MarkdownConnector().extract(raw("docs/x.md", text + "\n更多内容。", "doc"), "src")
        self.assertEqual([i.id for i in items], [i.id for i in again])  # 内容变化不改 id
        self.assertEqual(items[0].id, stable_id("src", "docs/x.md", "doc", "文档 > 节"))

    def test_long_section_is_chunked(self):
        body = "\n\n".join(f"第 {i} 段, " + "内容" * 100 for i in range(12))
        items = MarkdownConnector().extract(raw("docs/l.md", f"# 长\n\n## 节\n\n{body}", "doc"), "src")
        self.assertGreater(len(items), 1)
        self.assertEqual(len({i.id for i in items}), len(items))
        self.assertTrue(all(len(i.text) <= 1500 for i in items))
        self.assertEqual(len(split_text("a" * 10, max_chars=1500)), 1)


class PythonCodeTests(unittest.TestCase):
    def test_ast_items(self):
        src = '"""模块说明。"""\n\nclass Client(Base):\n    """客户端。"""\n\n    def fetch(self, keys: list, timeout_ms: int = 50) -> dict:\n        """取数。"""\n        x = 1\n        return {}\n\n\ndef helper(a):\n    return a\n'
        items = PythonConnector().extract(raw("code/c.py", src, "code"), "src")
        quals = [i.heading_path for i in items]
        self.assertEqual(quals, ["module", "c.Client", "c.Client.fetch", "c.helper"])
        fetch = items[2]
        self.assertIn("def fetch(self, keys: list, timeout_ms: int=50) -> dict:", fetch.text)
        self.assertIn("取数。", fetch.text)
        self.assertIn("x = 1", fetch.text)
        self.assertEqual(fetch.metadata["args"], ["self", "keys", "timeout_ms"])
        self.assertIn("模块说明", items[0].text)
        self.assertIn("class Client(Base):", items[1].text)


if __name__ == "__main__":
    unittest.main()
