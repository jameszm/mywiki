"""对话与反馈日志。

- log_turn: 记录 query/user/session、检索到的条目 (id@version, rank, 各信号分数)、引用的条目、答案与检索轨迹。
- log_feedback: 显式 (+1/-1)、隐式 (reformulated -0.5 / applied_action +0.5 / task_success +0.5)、纠错文本。
- 纠错文本命中 “不对/其实/应该是/…” -> 候选知识 (lesson) 进入 curation_queue(promote_candidate), 带对话 id 证据。
- promote_candidate 是显式的人工动作: 策展从不静默修改知识。
"""
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .answer import Answer, compose_answer
from .chunking import content_hash, finalize_item, stable_id
from .index import Index
from .llm import HeuristicLLM, LLMClient
from .models import CitationEvent, ConversationTurn, CurationTask, FeedbackEvent, KnowledgeItem, RetrievalEvent, utc_now
from .search import SearchResult, deep_search
from .store import Store

CORRECTION_RE = re.compile(r"不对|其实|应该是|实际上|错了|已经改成|现在是|已经不是|不再是|改为|改成了|不是这样")
IMPLICIT_VALUES = {"reformulated": -0.5, "applied_action": 0.5, "task_success": 0.5, "correction": 0.0}


def log_turn(store: Store, query: str, user_id: str, session_id: str, result: SearchResult, answer: Answer,
             llm_name: str = "heuristic", now: str | None = None, metadata: dict | None = None, max_logged: int = 10) -> ConversationTurn:
    turn_id = f"t{store.count_turns() + 1:05d}"
    now = now or utc_now()
    retrievals = [RetrievalEvent(turn_id, h.item.id, h.item.version, rank, h.score, h.signals(), 0)
                  for rank, h in enumerate(result.hits[:max_logged], 1)]
    citations = [CitationEvent(turn_id, iid, ver, pos) for pos, (iid, ver) in enumerate(answer.citations, 1)]
    turn = ConversationTurn(turn_id, session_id, user_id, query, answer.text, now, max_score=round(result.max_relevance, 4),
                            abstained=answer.abstained, trace=result.trace.to_dict(),
                            metadata={"llm": llm_name, "evidence_ids": answer.evidence_ids, **(metadata or {})})
    store.log_turn(turn, retrievals, citations)
    return turn


def log_feedback(store: Store, turn_id: str, kind: str, value: float | None = None, text: str = "", now: str | None = None) -> FeedbackEvent:
    if kind == "explicit":
        if value not in (1, -1, 1.0, -1.0):
            raise ValueError("explicit 反馈必须是 +1 或 -1")
    elif kind not in IMPLICIT_VALUES:
        raise ValueError(f"未知反馈类型: {kind}")
    v = float(value) if value is not None else IMPLICIT_VALUES[kind]
    if store.get_turn(turn_id) is None:
        raise ValueError(f"对话不存在: {turn_id}")
    fb = store.log_feedback(FeedbackEvent(None, turn_id, kind, v, text, now or utc_now()))
    if kind == "correction" and text:
        extract_lesson_candidate(store, turn_id, text, now)
    return fb


def extract_lesson_candidate(store: Store, turn_id: str, text: str, now: str | None = None) -> CurationTask | None:
    """从纠错文本抽取候选知识 -> promote_candidate 任务 (证据: 对话 id + 当时引用的条目)。"""
    if not CORRECTION_RE.search(text):
        return None
    turn = store.get_turn(turn_id)
    if turn is None:
        return None
    cited = store.citations(turn_id)
    lesson = text.strip()
    task = CurationTask(
        id=None, task_type="promote_candidate", item_ids=sorted({c.item_id for c in cited}), priority=0.8,
        reason=f"用户纠错: {lesson[:60]}",
        evidence={"turn_ids": [turn_id], "query": turn.query, "correction": lesson, "user": turn.user_id,
                  "cited": [f"{c.item_id}@{c.item_version}" for c in cited],
                  "candidate": {"kind": "lesson", "title": f"经验: {turn.query[:40]}", "text": lesson}},
        created_at=now or utc_now(), fingerprint=f"promote_candidate:{turn_id}",
    )
    return store.add_curation_task(task)


def promote_candidate(store: Store, task_id: int, now: str | None = None) -> KnowledgeItem:
    """人工确认后把候选经验写入知识库 (kind=lesson), 任务标记 done。"""
    task = store.get_task(task_id)
    if task is None or task.task_type != "promote_candidate":
        raise ValueError(f"不是 promote_candidate 任务: {task_id}")
    now = now or utc_now()
    cand = task.evidence["candidate"]
    turn_id = task.evidence["turn_ids"][0]
    locator = f"lessons/{turn_id}"
    text = f"{cand['text']}\n(来源: 对话 {turn_id} 的用户纠错, 原问题: {task.evidence.get('query', '')})"
    item = KnowledgeItem(id=stable_id("curation", locator, "lesson", "lesson"), source_id="curation", locator=locator,
                         kind="lesson", title=cand["title"], text=text, content_hash=content_hash(text),
                         metadata={"turn_ids": task.evidence["turn_ids"], "task_id": task_id, "based_on": task.evidence.get("cited", [])},
                         heading_path="lesson")
    latest = store.get_item(item.id)
    finalize_item(item, (latest.version + 1) if latest else 1, now)
    if latest and latest.valid_to is None:
        store.close_item(latest.id, latest.version, now, item.key, "superseded")
    store.insert_item(item)
    store.set_task_status(task_id, "done", now)
    return item


@dataclass
class ReplaySummary:
    turns: int = 0
    cited_turns: int = 0
    abstained: int = 0
    feedback_events: int = 0
    corrections: int = 0
    reformulations: int = 0
    users: Counter = field(default_factory=Counter)
    turn_ids: list[str] = field(default_factory=list)

    @property
    def cited_rate(self) -> float:
        return self.cited_turns / self.turns if self.turns else 0.0


def replay_scenarios(store: Store, index: Index, path: str | Path, llm: LLMClient | None = None,
                     corpus_version: int = 0, acl_of: Callable[[str], list[str] | None] | None = None) -> ReplaySummary:
    """回放 scenarios/conversations.jsonl: 检索 -> 回答 -> 记录对话与反馈。"""
    llm = llm or HeuristicLLM()
    entries = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    summary = ReplaySummary()
    turn_of: dict[str, str] = {}
    for e in entries:
        acl = acl_of(e["user"]) if acl_of else e.get("groups")
        result = deep_search(index, e["query"], llm=llm, acl=acl)
        ans = compose_answer(e["query"], result, llm)
        turn = log_turn(store, e["query"], e["user"], e.get("session", e["user"]), result, ans, llm.name,
                        metadata={"scenario_id": e.get("id"), "corpus_version": corpus_version})
        turn_of[str(e.get("id"))] = turn.id
        summary.turns += 1
        summary.turn_ids.append(turn.id)
        summary.users[e["user"]] += 1
        summary.cited_turns += bool(ans.cited_item_ids)
        summary.abstained += ans.abstained
        prev = turn_of.get(str(e.get("reformulation_of")))
        if prev:
            log_feedback(store, prev, "reformulated")
            summary.reformulations += 1
            summary.feedback_events += 1
        if e.get("feedback") in (1, -1):
            log_feedback(store, turn.id, "explicit", e["feedback"])
            summary.feedback_events += 1
        for kind in ("applied_action", "task_success"):
            if e.get(kind):
                log_feedback(store, turn.id, kind)
                summary.feedback_events += 1
        if e.get("correction"):
            log_feedback(store, turn.id, "correction", text=e["correction"])
            summary.feedback_events += 1
            summary.corrections += 1
    return summary
