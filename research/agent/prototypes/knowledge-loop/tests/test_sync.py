import tempfile
import unittest
from pathlib import Path

from kloop.index import Index
from kloop.store import Store
from kloop.sync import sync_source
from tests.helpers import CONFIG_V2, DOC_V2, write_corpus

T1, T2, T3 = "2026-01-01T00:00:00.000000+00:00", "2026-01-02T00:00:00.000000+00:00", "2026-01-03T00:00:00.000000+00:00"


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = write_corpus(Path(self.tmp.name) / "corpus")
        self.store = Store(":memory:")
        self.index = Index()

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_first_sync_adds_everything(self):
        rep = sync_source(self.store, "src", self.root, index=self.index, now=T1)
        self.assertGreater(rep.added, 0)
        self.assertEqual((rep.updated, rep.unchanged, rep.deleted), (0, 0, 0))
        self.assertEqual(rep.items_reindexed, rep.added)
        self.assertEqual(rep.files_added, 4)
        self.assertEqual(len(self.index), self.store.count_items())
        self.assertEqual(self.store.get_source("src").sync_count, 1)
        self.assertEqual(len(self.store.sync_runs()), 1)
        item = self.store.current_items(kinds=("doc",))[0]
        self.assertIn("来源: src | 路径: docs/guide.md", item.context_header)
        self.assertIn("版本: v1", item.context_header)

    def test_resync_unchanged_skips_everything(self):
        first = sync_source(self.store, "src", self.root, index=self.index, now=T1)
        rep = sync_source(self.store, "src", self.root, index=self.index, now=T2)
        self.assertEqual((rep.added, rep.updated, rep.deleted, rep.items_reindexed), (0, 0, 0, 0))
        self.assertEqual(rep.unchanged, first.added)
        self.assertEqual(rep.files_skipped, 4)

    def test_modified_section_supersedes_old_version(self):
        sync_source(self.store, "src", self.root, index=self.index, now=T1)
        before = {it.id: it for it in self.store.current_items()}
        write_corpus(self.root, doc=DOC_V2)
        rep = sync_source(self.store, "src", self.root, index=self.index, now=T2)
        self.assertEqual((rep.added, rep.updated, rep.deleted), (0, 1, 0))
        self.assertEqual(rep.unchanged, len(before) - 1)
        self.assertEqual(rep.items_reindexed, 2)  # 移除旧版本 + 加入新版本
        self.assertEqual(rep.changed_locators, ["docs/guide.md"])
        new_key = rep.updated_keys[0]
        item_id, ver = new_key.split("@")
        self.assertEqual(ver, "2")
        hist = self.store.item_history(item_id)
        self.assertEqual([h.version for h in hist], [1, 2])
        old, new = hist
        self.assertEqual((old.status, old.valid_to, old.superseded_by), ("superseded", T2, new_key))
        self.assertTrue(new.is_current and new.valid_from == T2 and "观察 30 分钟" in new.text)
        self.assertIn(new_key, self.index.items)
        self.assertNotIn(old.key, self.index.items)
        self.assertEqual(set(before), {it.id for it in self.store.current_items()})  # 逻辑 id 集合不变

    def test_deleted_file_creates_tombstones(self):
        sync_source(self.store, "src", self.root, index=self.index, now=T1)
        code_items = self.store.current_items_by_locator("src", "code/client.py")
        write_corpus(self.root, with_code=False)
        rep = sync_source(self.store, "src", self.root, index=self.index, now=T2)
        self.assertEqual(rep.deleted, len(code_items))
        self.assertEqual(rep.files_deleted, 1)
        self.assertEqual(rep.deleted_locators, ["code/client.py"])
        for it in code_items:
            latest = self.store.get_item(it.id)
            self.assertEqual((latest.status, latest.valid_to, latest.superseded_by), ("deleted", T2, None))
            self.assertNotIn(it.key, self.index.items)
        self.assertEqual(self.store.current_items_by_locator("src", "code/client.py"), [])
        # 文件回归后版本号继续递增
        write_corpus(self.root, with_code=True)
        rep3 = sync_source(self.store, "src", self.root, index=self.index, now=T3)
        self.assertEqual(rep3.added, len(code_items))
        self.assertEqual(self.store.get_item(code_items[0].id).version, 2)

    def test_new_file_added(self):
        sync_source(self.store, "src", self.root, index=self.index, now=T1)
        write_corpus(self.root, extra={"docs/new.md": "# 新文档\n\n## 节\n\n新增内容。"})
        rep = sync_source(self.store, "src", self.root, index=self.index, now=T2)
        self.assertEqual((rep.added, rep.updated, rep.deleted, rep.files_added), (1, 0, 0, 1))

    def test_stable_ids_across_runs(self):
        sync_source(self.store, "src", self.root, now=T1)
        other = Store(":memory:")
        sync_source(other, "src", self.root, now=T2)
        self.assertEqual({it.id for it in self.store.current_items()}, {it.id for it in other.current_items()})
        other.close()

    def test_as_of_view(self):
        sync_source(self.store, "src", self.root, now=T1)
        write_corpus(self.root, config=CONFIG_V2)
        sync_source(self.store, "src", self.root, now=T2)
        cfg_old = [it for it in self.store.items_as_of("2026-01-01T12:00:00.000000+00:00") if it.kind == "config"][0]
        cfg_new = [it for it in self.store.items_as_of(T2) if it.kind == "config"][0]
        self.assertIn("0.001", cfg_old.text)
        self.assertIn("0.0005", cfg_new.text)
        self.assertEqual((cfg_old.version, cfg_new.version), (1, 2))



class SyncRegressionTests(unittest.TestCase):
    """回归: 稳定 id 碰撞 / acl 变更被忽略 / 目录不存在时整库墓碑。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = write_corpus(Path(self.tmp.name) / "corpus")
        self.store = Store(":memory:")
        self.index = Index()

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_duplicate_heading_paths_do_not_collide(self):
        # 同一文件里两个同名章节 (相同 heading_path) 以前会生成相同的稳定 id -> INSERT 主键冲突, 同步中途崩溃
        doc = "# 文档\n\n## 步骤\n\n第一段内容。\n\n## 其他\n\n其他内容。\n\n## 步骤\n\n第二段内容, 与第一段不同。\n"
        write_corpus(self.root, extra={"docs/dup.md": doc})
        rep = sync_source(self.store, "src", self.root, index=self.index, now=T1)
        items = self.store.current_items_by_locator("src", "docs/dup.md")
        self.assertEqual(len(items), 3)
        self.assertEqual(len({it.id for it in items}), 3)
        self.assertEqual(sorted(it.heading_path for it in items), ["文档 > 其他", "文档 > 步骤", "文档 > 步骤 (2)"])
        self.assertEqual(len(self.index), rep.added)
        # 只改第二个同名章节 -> 只有它产生新版本, 第一个保持 v1
        write_corpus(self.root, extra={"docs/dup.md": doc.replace("第二段内容", "第二段新内容")})
        rep2 = sync_source(self.store, "src", self.root, index=self.index, now=T2)
        self.assertEqual((rep2.added, rep2.updated, rep2.deleted), (0, 1, 0))
        by_path = {it.heading_path: it for it in self.store.current_items_by_locator("src", "docs/dup.md")}
        self.assertEqual((by_path["文档 > 步骤"].version, by_path["文档 > 步骤 (2)"].version), (1, 2))

    def test_acl_change_without_content_change_is_applied(self):
        body = "# 内部\n\n## 排查\n\n仅 oncall 可见的排查记录。\n"
        write_corpus(self.root, extra={"docs/secret.md": body})
        sync_source(self.store, "src", self.root, index=self.index, now=T1)
        self.assertEqual([h.item.locator for h in self.index.search("排查记录", acl=["ranking-team"])], ["docs/secret.md"])
        write_corpus(self.root, extra={"docs/secret.md": "---\nacl: oncall\n---\n" + body})  # 只改 front matter, 正文不变
        rep = sync_source(self.store, "src", self.root, index=self.index, now=T2)
        self.assertEqual((rep.added, rep.updated, rep.deleted), (0, 0, 0))  # 不产生新版本
        item = self.store.current_items_by_locator("src", "docs/secret.md")[0]
        self.assertEqual((item.version, item.acl), (1, ["oncall"]))
        self.assertEqual(self.index.items[item.key].acl, ["oncall"])  # 索引中的对象同步更新
        self.assertEqual([h.item.locator for h in self.index.search("排查记录", acl=["ranking-team"])], [])
        self.assertEqual([h.item.locator for h in self.index.search("排查记录", acl=["oncall"])], ["docs/secret.md"])

    def test_missing_root_raises_instead_of_tombstoning(self):
        sync_source(self.store, "src", self.root, index=self.index, now=T1)
        n = self.store.count_items()
        with self.assertRaises(FileNotFoundError):
            sync_source(self.store, "src", Path(self.tmp.name) / "typo", index=self.index, now=T2)
        self.assertEqual((self.store.count_items(), len(self.index)), (n, n))
        self.assertEqual(self.store.get_source("src").sync_count, 1)


if __name__ == "__main__":
    unittest.main()
