"""数据模型 (纯 dataclass, 无行为依赖)。

所有时间戳均为 ISO-8601 (UTC, 微秒精度) 字符串, 字符串字典序即时间序,
便于 SQLite 中直接用 <, > 比较并做 as_of 查询。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

KINDS = ("doc", "code", "config", "log", "lesson")
FEEDBACK_KINDS = ("explicit", "reformulated", "applied_action", "task_success", "correction")
TASK_TYPES = ("verify", "update", "deprecate", "merge", "fill_gap", "promote_candidate")


def utc_now() -> str:
    """当前 UTC 时间, ISO-8601 微秒精度。"""
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def item_key(item_id: str, version: int) -> str:
    """物理键: 逻辑 id + 版本号, 日志中精确记录“哪一版”被检索/引用。"""
    return f"{item_id}@{version}"


def parse_key(key: str) -> tuple[str, int]:
    item_id, _, ver = key.partition("@")
    return item_id, int(ver or 1)


@dataclass
class Source:
    """知识来源 (一个语料根目录)。同一 source 跨版本同步时按 locator 对齐。"""

    id: str
    root: str
    kind_hint: str = "mixed"
    created_at: str = ""
    last_sync_at: str | None = None
    sync_count: int = 0


@dataclass
class RawDocument:
    """接入器扫描得到的原始文件。locator 为相对语料根目录的 posix 路径。"""

    locator: str
    text: str
    mtime: float
    sha256: str
    kind: str


@dataclass
class KnowledgeItem:
    """知识条目 (版本化)。

    id 是稳定逻辑 id = sha1(source|locator|kind|heading_path)[:12];
    内容变化时产生新 version, 旧版本写入 valid_to / superseded_by;
    来源文件消失时旧版本以 status="deleted" 作为墓碑 (tombstone) 关闭。
    """

    id: str
    source_id: str
    locator: str
    kind: str
    title: str
    text: str
    context_header: str = ""
    content_hash: str = ""
    version: int = 1
    valid_from: str = ""
    valid_to: str | None = None
    superseded_by: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    acl: list[str] = field(default_factory=lambda: ["all"])
    last_verified_at: str = ""
    heading_path: str = ""
    status: str = "active"  # active | superseded | deleted

    @property
    def key(self) -> str:
        return item_key(self.id, self.version)

    @property
    def is_current(self) -> bool:
        return self.valid_to is None

    def indexed_text(self) -> str:
        """进入索引的文本 = 上下文头 + 标题 + 正文。"""
        return f"{self.context_header}\n{self.title}\n{self.text}"


@dataclass
class ConversationTurn:
    id: str
    session_id: str
    user_id: str
    query: str
    answer: str
    created_at: str
    max_score: float = 0.0
    abstained: bool = False
    trace: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalEvent:
    turn_id: str
    item_id: str
    item_version: int
    rank: int
    score: float
    signals: dict[str, Any] = field(default_factory=dict)
    step: int = 0


@dataclass
class CitationEvent:
    turn_id: str
    item_id: str
    item_version: int
    position: int


@dataclass
class FeedbackEvent:
    id: int | None
    turn_id: str
    kind: str  # FEEDBACK_KINDS
    value: float
    text: str = ""
    created_at: str = ""


@dataclass
class ItemScore:
    item_id: str
    version: int
    exposures: int = 0
    citations: int = 0
    citation_rate: float = 0.0
    helpfulness: float = 0.0
    staleness_flags: list[str] = field(default_factory=list)
    conflict_flags: list[str] = field(default_factory=list)
    health: float = 0.0
    components: dict[str, float] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    computed_at: str = ""

    @property
    def key(self) -> str:
        return item_key(self.item_id, self.version)


@dataclass
class CurationTask:
    id: int | None
    task_type: str  # TASK_TYPES
    item_ids: list[str]
    priority: float
    reason: str
    evidence: dict[str, Any] = field(default_factory=dict)
    status: str = "open"  # open | resolved | done
    created_at: str = ""
    fingerprint: str = ""


@dataclass
class EvalRun:
    id: str
    name: str
    created_at: str
    summary: dict[str, Any] = field(default_factory=dict)
    per_query: list[dict[str, Any]] = field(default_factory=list)
    corpus_version: int = 0
