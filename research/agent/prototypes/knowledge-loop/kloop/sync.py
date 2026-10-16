"""增量同步。

算法 (按 source):
1. 全量扫描文件 -> 与 source_files 表中的 sha256 逐 locator 对比; 文件未变 -> 其全部条目跳过 (不抽取、不重建索引)。
2. 文件变化/新增 -> 抽取条目草稿, 按稳定 id 与当前版本对比 content_hash:
   相同 -> unchanged; 不同 -> 新版本 (旧版本写 valid_to + superseded_by, status=superseded);
   新 id -> 插入; 当前有而草稿没有 -> 墓碑 (status=deleted)。
3. 扫描不到的 locator -> 其全部当前条目写墓碑。
4. 记录 sync_run; 若传入 index, 只对受影响条目做 remove/add。
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path

from .chunking import finalize_item
from .connectors import Connector, scan_all
from .connectors.log_files import link_templates_to_docs
from .index import Index
from .models import KnowledgeItem, Source, utc_now
from .store import Store


@dataclass
class SyncReport:
    source_id: str
    root: str
    added: int = 0
    updated: int = 0
    unchanged: int = 0
    deleted: int = 0
    items_reindexed: int = 0
    files_scanned: int = 0
    files_added: int = 0
    files_changed: int = 0
    files_skipped: int = 0
    files_deleted: int = 0
    changed_locators: list[str] = field(default_factory=list)
    deleted_locators: list[str] = field(default_factory=list)
    added_keys: list[str] = field(default_factory=list)
    updated_keys: list[str] = field(default_factory=list)
    deleted_keys: list[str] = field(default_factory=list)
    run_id: int = 0
    corpus_version: int = 0
    started_at: str = ""
    finished_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        return (f"文件: 扫描 {self.files_scanned} / 新增 {self.files_added} / 变更 {self.files_changed} / 未变跳过 {self.files_skipped} / 删除 {self.files_deleted}; "
                f"条目: 新增 {self.added} / 更新(新版本) {self.updated} / 未变 {self.unchanged} / 墓碑 {self.deleted}; "
                f"重建索引条目 {self.items_reindexed} (语料版本 v{self.corpus_version})")


def sync_source(store: Store, source_id: str, root: str | Path, index: Index | None = None,
                connectors: list[Connector] | None = None, now: str | None = None) -> SyncReport:
    now = now or utc_now()
    root = Path(root)
    if not root.is_dir():  # 路径不存在时直接报错; 否则 "扫描不到任何文件" 会把该 source 的全部条目写成墓碑
        raise FileNotFoundError(f"语料目录不存在: {root}")
    source = store.get_source(source_id) or Source(id=source_id, root=str(root), created_at=now)
    report = SyncReport(source_id=source_id, root=str(root), started_at=now)
    known = store.source_files(source_id)
    seen: set[str] = set()
    to_insert: list[KnowledgeItem] = []
    to_remove: list[str] = []
    changed_files: list[tuple[str, str, float, str, bool, list[KnowledgeItem]]] = []

    for conn, raw in scan_all(root, connectors):
        seen.add(raw.locator)
        report.files_scanned += 1
        prev = known.get(raw.locator)
        if prev and prev["sha256"] == raw.sha256:
            report.files_skipped += 1
            report.unchanged += len(store.current_items_by_locator(source_id, raw.locator))
            continue
        drafts = conn.extract(raw, source_id)
        changed_files.append((raw.locator, raw.sha256, raw.mtime, raw.kind, prev is not None, drafts))

    # 日志模板 <-> 文档关联 (metadata, 不参与 content_hash)
    doc_items = [it for it in store.current_items(source_id, kinds=("doc",)) if it.locator not in {c[0] for c in changed_files}]
    for _, _, _, _, _, drafts in changed_files:
        doc_items.extend(d for d in drafts if d.kind == "doc")
    for _, _, _, _, _, drafts in changed_files:
        logs = [d for d in drafts if d.kind == "log"]
        if logs:
            link_templates_to_docs(logs, doc_items)

    latest = store.latest_versions()
    for locator, sha, mtime, kind, existed, drafts in changed_files:
        if existed:
            report.files_changed += 1
            report.changed_locators.append(locator)
        else:
            report.files_added += 1
        current = {it.id: it for it in store.current_items_by_locator(source_id, locator)}
        for d in drafts:
            cur = current.pop(d.id, None)
            if cur is None:
                finalize_item(d, latest.get(d.id, 0) + 1, now)
                to_insert.append(d)
                report.added += 1
                report.added_keys.append(d.key)
            elif cur.content_hash == d.content_hash:
                report.unchanged += 1
                if d.kind == "log" and d.metadata.get("related_docs") != cur.metadata.get("related_docs"):
                    store.update_item_fields(cur.id, cur.version, metadata={**cur.metadata, "related_docs": d.metadata.get("related_docs", [])})
                if list(d.acl) != list(cur.acl):  # 内容未变但 acl 变了 (如 front matter): 就地更新, 不产生新版本; 索引中的对象同步更新
                    store.update_item_fields(cur.id, cur.version, acl=list(d.acl))
                    if index is not None and cur.key in index.items:
                        index.items[cur.key].acl = list(d.acl)
            else:
                finalize_item(d, cur.version + 1, now)
                store.close_item(cur.id, cur.version, now, d.key, "superseded")
                to_insert.append(d)
                to_remove.append(cur.key)
                report.updated += 1
                report.updated_keys.append(d.key)
        for cur in current.values():  # 文件仍在但章节消失 -> 墓碑
            store.close_item(cur.id, cur.version, now, None, "deleted")
            to_remove.append(cur.key)
            report.deleted += 1
            report.deleted_keys.append(cur.key)
        store.upsert_source_file(source_id, locator, sha, mtime, kind, now, changed=existed)

    for locator in sorted(set(known) - seen):  # 文件消失 -> 全部墓碑
        report.files_deleted += 1
        report.deleted_locators.append(locator)
        for cur in store.current_items_by_locator(source_id, locator):
            store.close_item(cur.id, cur.version, now, None, "deleted")
            to_remove.append(cur.key)
            report.deleted += 1
            report.deleted_keys.append(cur.key)
        store.mark_source_file_deleted(source_id, locator, now)

    for it in to_insert:
        store.insert_item(it)
    report.items_reindexed = len(to_insert) + len(to_remove)
    if index is not None:
        index.remove_items(to_remove)
        index.add_items(to_insert)

    source.root, source.last_sync_at, source.sync_count = str(root), now, source.sync_count + 1
    store.upsert_source(source)
    report.corpus_version = source.sync_count
    report.finished_at = utc_now()
    counts = {k: getattr(report, k) for k in ("added", "updated", "unchanged", "deleted", "items_reindexed")}
    report.run_id = store.record_sync_run(source_id, str(root), report.started_at, report.finished_at, counts, {
        "changed_locators": report.changed_locators, "deleted_locators": report.deleted_locators,
        "added_keys": report.added_keys, "updated_keys": report.updated_keys, "deleted_keys": report.deleted_keys,
        "files": {"scanned": report.files_scanned, "added": report.files_added, "changed": report.files_changed,
                  "skipped": report.files_skipped, "deleted": report.files_deleted}})
    return report
