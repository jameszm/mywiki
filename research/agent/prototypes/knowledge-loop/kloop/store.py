"""SQLite 存储层: 版本化知识条目 + 全部日志表。

设计要点:
- 条目主键 (id, version); valid_to IS NULL 即当前有效; 删除以 status='deleted' 的墓碑关闭。
- 所有写入使用参数化 SQL; WAL 模式; locator/kind/valid_to 上建索引。
- 对话/检索/引用/反馈四张日志表是评分与评测的唯一事实来源 (可随时重算)。
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from .models import (
    ConversationTurn,
    CitationEvent,
    CurationTask,
    EvalRun,
    FeedbackEvent,
    ItemScore,
    KnowledgeItem,
    RetrievalEvent,
    Source,
    utc_now,
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY, root TEXT NOT NULL, kind_hint TEXT, created_at TEXT NOT NULL,
    last_sync_at TEXT, sync_count INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS source_files (
    source_id TEXT NOT NULL, locator TEXT NOT NULL, sha256 TEXT NOT NULL, mtime REAL, kind TEXT,
    first_seen_at TEXT NOT NULL, last_changed_at TEXT NOT NULL, deleted_at TEXT,
    PRIMARY KEY (source_id, locator));
CREATE TABLE IF NOT EXISTS items (
    id TEXT NOT NULL, version INTEGER NOT NULL, source_id TEXT NOT NULL, locator TEXT NOT NULL,
    kind TEXT NOT NULL, title TEXT NOT NULL, text TEXT NOT NULL, context_header TEXT NOT NULL,
    content_hash TEXT NOT NULL, valid_from TEXT NOT NULL, valid_to TEXT, superseded_by TEXT,
    metadata TEXT NOT NULL, acl TEXT NOT NULL, last_verified_at TEXT NOT NULL,
    heading_path TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active',
    PRIMARY KEY (id, version));
CREATE INDEX IF NOT EXISTS idx_items_locator ON items(source_id, locator);
CREATE INDEX IF NOT EXISTS idx_items_kind ON items(kind);
CREATE INDEX IF NOT EXISTS idx_items_valid_to ON items(valid_to);
CREATE TABLE IF NOT EXISTS sync_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT, source_id TEXT NOT NULL, root TEXT NOT NULL,
    started_at TEXT NOT NULL, finished_at TEXT NOT NULL, added INTEGER, updated INTEGER,
    unchanged INTEGER, deleted INTEGER, items_reindexed INTEGER, details TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS turns (
    id TEXT PRIMARY KEY, session_id TEXT NOT NULL, user_id TEXT NOT NULL, query TEXT NOT NULL,
    answer TEXT NOT NULL, created_at TEXT NOT NULL, max_score REAL NOT NULL DEFAULT 0,
    abstained INTEGER NOT NULL DEFAULT 0, trace TEXT NOT NULL, metadata TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS retrievals (
    id INTEGER PRIMARY KEY AUTOINCREMENT, turn_id TEXT NOT NULL, item_id TEXT NOT NULL,
    item_version INTEGER NOT NULL, rank INTEGER NOT NULL, score REAL NOT NULL,
    signals TEXT NOT NULL, step INTEGER NOT NULL DEFAULT 0);
CREATE INDEX IF NOT EXISTS idx_retrievals_turn ON retrievals(turn_id);
CREATE INDEX IF NOT EXISTS idx_retrievals_item ON retrievals(item_id, item_version);
CREATE TABLE IF NOT EXISTS citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT, turn_id TEXT NOT NULL, item_id TEXT NOT NULL,
    item_version INTEGER NOT NULL, position INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS idx_citations_turn ON citations(turn_id);
CREATE INDEX IF NOT EXISTS idx_citations_item ON citations(item_id, item_version);
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT, turn_id TEXT NOT NULL, kind TEXT NOT NULL,
    value REAL NOT NULL, text TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_feedback_turn ON feedback(turn_id);
CREATE TABLE IF NOT EXISTS item_scores (
    item_id TEXT NOT NULL, version INTEGER NOT NULL, exposures INTEGER, citations INTEGER,
    citation_rate REAL, helpfulness REAL, staleness_flags TEXT NOT NULL, conflict_flags TEXT NOT NULL,
    health REAL, components TEXT NOT NULL, reasons TEXT NOT NULL, computed_at TEXT NOT NULL,
    PRIMARY KEY (item_id, version));
CREATE TABLE IF NOT EXISTS curation_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT, task_type TEXT NOT NULL, item_ids TEXT NOT NULL,
    priority REAL NOT NULL, reason TEXT NOT NULL, evidence TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open', created_at TEXT NOT NULL, resolved_at TEXT,
    fingerprint TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS eval_runs (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at TEXT NOT NULL, summary TEXT NOT NULL,
    per_query TEXT NOT NULL, corpus_version INTEGER NOT NULL DEFAULT 0);
"""


def _dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


class Store:
    """仓储: 所有函数显式接收 store, 无全局状态。"""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        if self.path != ":memory:":
            self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.init_schema()

    def init_schema(self) -> None:
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    @contextmanager
    def tx(self) -> Iterator[sqlite3.Connection]:
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    # ---------------------------------------------------------------- sources
    def upsert_source(self, source: Source) -> None:
        with self.tx() as c:
            c.execute(
                "INSERT INTO sources(id, root, kind_hint, created_at, last_sync_at, sync_count) VALUES(?,?,?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET root=excluded.root, last_sync_at=excluded.last_sync_at, "
                "sync_count=excluded.sync_count",
                (source.id, source.root, source.kind_hint, source.created_at or utc_now(), source.last_sync_at, source.sync_count),
            )

    def get_source(self, source_id: str) -> Source | None:
        row = self.conn.execute("SELECT * FROM sources WHERE id=?", (source_id,)).fetchone()
        return Source(**dict(row)) if row else None

    def list_sources(self) -> list[Source]:
        return [Source(**dict(r)) for r in self.conn.execute("SELECT * FROM sources ORDER BY id")]

    # ----------------------------------------------------------- source files
    def source_files(self, source_id: str, include_deleted: bool = False) -> dict[str, dict[str, Any]]:
        sql = "SELECT * FROM source_files WHERE source_id=?" + ("" if include_deleted else " AND deleted_at IS NULL")
        return {r["locator"]: dict(r) for r in self.conn.execute(sql, (source_id,))}

    def upsert_source_file(self, source_id: str, locator: str, sha256: str, mtime: float, kind: str, now: str, changed: bool) -> None:
        with self.tx() as c:
            row = c.execute("SELECT * FROM source_files WHERE source_id=? AND locator=?", (source_id, locator)).fetchone()
            if row is None:
                c.execute(
                    "INSERT INTO source_files(source_id, locator, sha256, mtime, kind, first_seen_at, last_changed_at, deleted_at) VALUES(?,?,?,?,?,?,?,NULL)",
                    (source_id, locator, sha256, mtime, kind, now, now),
                )
            else:
                last_changed = now if (changed or row["deleted_at"]) else row["last_changed_at"]
                c.execute(
                    "UPDATE source_files SET sha256=?, mtime=?, kind=?, last_changed_at=?, deleted_at=NULL WHERE source_id=? AND locator=?",
                    (sha256, mtime, kind, last_changed, source_id, locator),
                )

    def mark_source_file_deleted(self, source_id: str, locator: str, now: str) -> None:
        with self.tx() as c:
            c.execute("UPDATE source_files SET deleted_at=?, last_changed_at=? WHERE source_id=? AND locator=?", (now, now, source_id, locator))

    # ------------------------------------------------------------------ items
    @staticmethod
    def _row_to_item(row: sqlite3.Row) -> KnowledgeItem:
        d = dict(row)
        d["metadata"] = json.loads(d["metadata"])
        d["acl"] = json.loads(d["acl"])
        return KnowledgeItem(**d)

    def insert_item(self, item: KnowledgeItem) -> None:
        with self.tx() as c:
            c.execute(
                "INSERT INTO items(id, version, source_id, locator, kind, title, text, context_header, content_hash, "
                "valid_from, valid_to, superseded_by, metadata, acl, last_verified_at, heading_path, status) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    item.id, item.version, item.source_id, item.locator, item.kind, item.title, item.text,
                    item.context_header, item.content_hash, item.valid_from, item.valid_to, item.superseded_by,
                    _dumps(item.metadata), _dumps(item.acl), item.last_verified_at, item.heading_path, item.status,
                ),
            )

    def close_item(self, item_id: str, version: int, valid_to: str, superseded_by: str | None, status: str) -> None:
        """关闭一个版本: 写 valid_to / superseded_by / status (superseded 或 deleted=墓碑)。"""
        with self.tx() as c:
            c.execute(
                "UPDATE items SET valid_to=?, superseded_by=?, status=? WHERE id=? AND version=?",
                (valid_to, superseded_by, status, item_id, version),
            )

    def update_item_fields(self, item_id: str, version: int, **fields: Any) -> None:
        allowed = {"metadata", "last_verified_at", "acl", "title"}
        sets, vals = [], []
        for k, v in fields.items():
            if k not in allowed:
                raise ValueError(f"field not updatable: {k}")
            sets.append(f"{k}=?")
            vals.append(_dumps(v) if k in ("metadata", "acl") else v)
        with self.tx() as c:
            c.execute(f"UPDATE items SET {', '.join(sets)} WHERE id=? AND version=?", (*vals, item_id, version))

    def current_items(self, source_id: str | None = None, kinds: tuple[str, ...] | None = None) -> list[KnowledgeItem]:
        sql, args = "SELECT * FROM items WHERE valid_to IS NULL", []
        if source_id:
            sql += " AND source_id=?"
            args.append(source_id)
        if kinds:
            sql += f" AND kind IN ({','.join('?' * len(kinds))})"
            args.extend(kinds)
        sql += " ORDER BY locator, heading_path, id"
        return [self._row_to_item(r) for r in self.conn.execute(sql, args)]

    def items_as_of(self, as_of: str) -> list[KnowledgeItem]:
        rows = self.conn.execute(
            "SELECT * FROM items WHERE valid_from<=? AND (valid_to IS NULL OR valid_to>?) ORDER BY locator, heading_path, id",
            (as_of, as_of),
        )
        return [self._row_to_item(r) for r in rows]

    def all_items(self) -> list[KnowledgeItem]:
        return [self._row_to_item(r) for r in self.conn.execute("SELECT * FROM items ORDER BY locator, heading_path, id, version")]

    def current_items_by_locator(self, source_id: str, locator: str) -> list[KnowledgeItem]:
        rows = self.conn.execute(
            "SELECT * FROM items WHERE source_id=? AND locator=? AND valid_to IS NULL ORDER BY heading_path, id",
            (source_id, locator),
        )
        return [self._row_to_item(r) for r in rows]

    def get_item(self, item_id: str, version: int | None = None) -> KnowledgeItem | None:
        if version is None:
            row = self.conn.execute("SELECT * FROM items WHERE id=? ORDER BY version DESC LIMIT 1", (item_id,)).fetchone()
        else:
            row = self.conn.execute("SELECT * FROM items WHERE id=? AND version=?", (item_id, version)).fetchone()
        return self._row_to_item(row) if row else None

    def item_history(self, item_id: str) -> list[KnowledgeItem]:
        rows = self.conn.execute("SELECT * FROM items WHERE id=? ORDER BY version", (item_id,))
        return [self._row_to_item(r) for r in rows]

    def latest_versions(self) -> dict[str, int]:
        return {r["id"]: r["v"] for r in self.conn.execute("SELECT id, MAX(version) AS v FROM items GROUP BY id")}

    def count_items(self, current_only: bool = True) -> int:
        sql = "SELECT COUNT(*) FROM items" + (" WHERE valid_to IS NULL" if current_only else "")
        return int(self.conn.execute(sql).fetchone()[0])

    # -------------------------------------------------------------- sync runs
    def record_sync_run(self, source_id: str, root: str, started_at: str, finished_at: str, counts: dict[str, int], details: dict[str, Any]) -> int:
        with self.tx() as c:
            cur = c.execute(
                "INSERT INTO sync_runs(source_id, root, started_at, finished_at, added, updated, unchanged, deleted, items_reindexed, details) "
                "VALUES(?,?,?,?,?,?,?,?,?,?)",
                (source_id, root, started_at, finished_at, counts["added"], counts["updated"], counts["unchanged"],
                 counts["deleted"], counts["items_reindexed"], _dumps(details)),
            )
            return int(cur.lastrowid or 0)

    def sync_runs(self) -> list[dict[str, Any]]:
        out = []
        for r in self.conn.execute("SELECT * FROM sync_runs ORDER BY id"):
            d = dict(r)
            d["details"] = json.loads(d["details"])
            out.append(d)
        return out

    # ------------------------------------------------------------------ turns
    def count_turns(self) -> int:
        return int(self.conn.execute("SELECT COUNT(*) FROM turns").fetchone()[0])

    def log_turn(self, turn: ConversationTurn, retrievals: list[RetrievalEvent], citations: list[CitationEvent]) -> None:
        with self.tx() as c:
            c.execute(
                "INSERT INTO turns(id, session_id, user_id, query, answer, created_at, max_score, abstained, trace, metadata) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (turn.id, turn.session_id, turn.user_id, turn.query, turn.answer, turn.created_at, turn.max_score,
                 int(turn.abstained), _dumps(turn.trace), _dumps(turn.metadata)),
            )
            c.executemany(
                "INSERT INTO retrievals(turn_id, item_id, item_version, rank, score, signals, step) VALUES(?,?,?,?,?,?,?)",
                [(r.turn_id, r.item_id, r.item_version, r.rank, r.score, _dumps(r.signals), r.step) for r in retrievals],
            )
            c.executemany(
                "INSERT INTO citations(turn_id, item_id, item_version, position) VALUES(?,?,?,?)",
                [(x.turn_id, x.item_id, x.item_version, x.position) for x in citations],
            )

    @staticmethod
    def _row_to_turn(row: sqlite3.Row) -> ConversationTurn:
        d = dict(row)
        d["trace"] = json.loads(d["trace"])
        d["metadata"] = json.loads(d["metadata"])
        d["abstained"] = bool(d["abstained"])
        return ConversationTurn(**d)

    def get_turn(self, turn_id: str) -> ConversationTurn | None:
        row = self.conn.execute("SELECT * FROM turns WHERE id=?", (turn_id,)).fetchone()
        return self._row_to_turn(row) if row else None

    def turns(self) -> list[ConversationTurn]:
        return [self._row_to_turn(r) for r in self.conn.execute("SELECT * FROM turns ORDER BY created_at, id")]

    def retrievals(self, turn_id: str | None = None) -> list[RetrievalEvent]:
        sql, args = "SELECT * FROM retrievals", ()
        if turn_id:
            sql, args = sql + " WHERE turn_id=?", (turn_id,)
        out = []
        for r in self.conn.execute(sql + " ORDER BY turn_id, rank", args):
            out.append(RetrievalEvent(r["turn_id"], r["item_id"], r["item_version"], r["rank"], r["score"], json.loads(r["signals"]), r["step"]))
        return out

    def citations(self, turn_id: str | None = None) -> list[CitationEvent]:
        sql, args = "SELECT * FROM citations", ()
        if turn_id:
            sql, args = sql + " WHERE turn_id=?", (turn_id,)
        return [CitationEvent(r["turn_id"], r["item_id"], r["item_version"], r["position"])
                for r in self.conn.execute(sql + " ORDER BY turn_id, position", args)]

    def log_feedback(self, fb: FeedbackEvent) -> FeedbackEvent:
        with self.tx() as c:
            cur = c.execute(
                "INSERT INTO feedback(turn_id, kind, value, text, created_at) VALUES(?,?,?,?,?)",
                (fb.turn_id, fb.kind, fb.value, fb.text, fb.created_at or utc_now()),
            )
            fb.id = int(cur.lastrowid or 0)
        return fb

    def feedback(self, turn_id: str | None = None) -> list[FeedbackEvent]:
        sql, args = "SELECT * FROM feedback", ()
        if turn_id:
            sql, args = sql + " WHERE turn_id=?", (turn_id,)
        return [FeedbackEvent(r["id"], r["turn_id"], r["kind"], r["value"], r["text"], r["created_at"])
                for r in self.conn.execute(sql + " ORDER BY id", args)]

    # ----------------------------------------------------------------- scores
    def upsert_item_scores(self, scores: list[ItemScore]) -> None:
        with self.tx() as c:
            c.executemany(
                "INSERT INTO item_scores(item_id, version, exposures, citations, citation_rate, helpfulness, staleness_flags, "
                "conflict_flags, health, components, reasons, computed_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(item_id, version) DO UPDATE SET exposures=excluded.exposures, citations=excluded.citations, "
                "citation_rate=excluded.citation_rate, helpfulness=excluded.helpfulness, staleness_flags=excluded.staleness_flags, "
                "conflict_flags=excluded.conflict_flags, health=excluded.health, components=excluded.components, "
                "reasons=excluded.reasons, computed_at=excluded.computed_at",
                [(s.item_id, s.version, s.exposures, s.citations, s.citation_rate, s.helpfulness, _dumps(s.staleness_flags),
                  _dumps(s.conflict_flags), s.health, _dumps(s.components), _dumps(s.reasons), s.computed_at) for s in scores],
            )

    def item_scores(self) -> list[ItemScore]:
        out = []
        for r in self.conn.execute("SELECT * FROM item_scores ORDER BY health DESC, item_id, version"):
            d = dict(r)
            for k in ("staleness_flags", "conflict_flags", "components", "reasons"):
                d[k] = json.loads(d[k])
            out.append(ItemScore(**d))
        return out

    # --------------------------------------------------------------- curation
    def add_curation_task(self, task: CurationTask) -> CurationTask:
        """按 fingerprint 去重: 已存在 (任意状态) 则返回已有任务, 重开已 resolved 的任务。"""
        with self.tx() as c:
            row = c.execute("SELECT * FROM curation_queue WHERE fingerprint=?", (task.fingerprint,)).fetchone()
            if row:
                if row["status"] == "resolved":
                    c.execute("UPDATE curation_queue SET status='open', resolved_at=NULL, priority=?, reason=?, evidence=? WHERE id=?",
                              (task.priority, task.reason, _dumps(task.evidence), row["id"]))
                task.id = int(row["id"])
                return task
            cur = c.execute(
                "INSERT INTO curation_queue(task_type, item_ids, priority, reason, evidence, status, created_at, fingerprint) VALUES(?,?,?,?,?,?,?,?)",
                (task.task_type, _dumps(task.item_ids), task.priority, task.reason, _dumps(task.evidence), task.status,
                 task.created_at or utc_now(), task.fingerprint),
            )
            task.id = int(cur.lastrowid or 0)
            return task

    def resolve_tasks_not_in(self, task_types: tuple[str, ...], keep_fingerprints: set[str], now: str) -> int:
        """把指定类型中、本次重算未再生成的 open 任务标记为 resolved; 返回数量。"""
        rows = self.conn.execute(
            f"SELECT id, fingerprint FROM curation_queue WHERE status='open' AND task_type IN ({','.join('?' * len(task_types))})",
            task_types,
        ).fetchall()
        stale = [r["id"] for r in rows if r["fingerprint"] not in keep_fingerprints]
        with self.tx() as c:
            c.executemany("UPDATE curation_queue SET status='resolved', resolved_at=? WHERE id=?", [(now, i) for i in stale])
        return len(stale)

    def set_task_status(self, task_id: int, status: str, now: str | None = None) -> None:
        with self.tx() as c:
            c.execute("UPDATE curation_queue SET status=?, resolved_at=? WHERE id=?", (status, now or utc_now(), task_id))

    def curation_tasks(self, status: str | None = "open") -> list[CurationTask]:
        sql, args = "SELECT * FROM curation_queue", ()
        if status:
            sql, args = sql + " WHERE status=?", (status,)
        out = []
        for r in self.conn.execute(sql + " ORDER BY priority DESC, id", args):
            out.append(CurationTask(r["id"], r["task_type"], json.loads(r["item_ids"]), r["priority"], r["reason"],
                                    json.loads(r["evidence"]), r["status"], r["created_at"], r["fingerprint"]))
        return out

    def get_task(self, task_id: int) -> CurationTask | None:
        for t in self.curation_tasks(status=None):
            if t.id == task_id:
                return t
        return None

    # ------------------------------------------------------------------- eval
    def save_eval_run(self, run: EvalRun) -> None:
        with self.tx() as c:
            c.execute(
                "INSERT OR REPLACE INTO eval_runs(id, name, created_at, summary, per_query, corpus_version) VALUES(?,?,?,?,?,?)",
                (run.id, run.name, run.created_at, _dumps(run.summary), _dumps(run.per_query), run.corpus_version),
            )

    def get_eval_run(self, run_id: str) -> EvalRun | None:
        row = self.conn.execute("SELECT * FROM eval_runs WHERE id=?", (run_id,)).fetchone()
        if not row:
            return None
        return EvalRun(row["id"], row["name"], row["created_at"], json.loads(row["summary"]), json.loads(row["per_query"]), row["corpus_version"])

    def list_eval_runs(self) -> list[EvalRun]:
        return [EvalRun(r["id"], r["name"], r["created_at"], json.loads(r["summary"]), json.loads(r["per_query"]), r["corpus_version"])
                for r in self.conn.execute("SELECT * FROM eval_runs ORDER BY created_at, id")]
