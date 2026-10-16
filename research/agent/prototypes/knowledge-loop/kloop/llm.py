"""可插拔 LLM 客户端。

- LLMClient 协议: plan_queries / compose_answer / judge_relevance。
- HeuristicLLM (默认): 确定性、无模型 —— 抽取式答案、规则查询分解、关键词重叠判别。
- AnthropicLLM: 仅当环境变量 KLOOP_LLM=anthropic 且已安装 anthropic 包并设置 ANTHROPIC_API_KEY 时启用;
  模型 id 取自 KLOOP_MODEL (默认 claude-opus-5-5)。任何失败都回退到启发式实现, 保证离线可用。
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .index import tokenize
from .search import extract_identifiers, plan_queries_heuristic

DEFAULT_ANTHROPIC_MODEL = "claude-opus-5-5"
CITE_RE = re.compile(r"\[K-([0-9a-f]{12})\]")
SENT_SPLIT_RE = re.compile(r"(?<=[。！？；;])\s*|(?<=[!?])\s+|\n+")  # 不在 != / ?= 处断句


@dataclass
class Evidence:
    item_id: str
    version: int
    title: str
    locator: str
    text: str
    rank: int
    kind: str = "doc"


KIND_BONUS = {"doc": 0.1, "lesson": 0.1, "config": 0.05}  # 抽取时略偏好说明性文本而非代码行/日志行


@runtime_checkable
class LLMClient(Protocol):
    name: str

    def plan_queries(self, query: str) -> list[str]: ...

    def compose_answer(self, query: str, evidence: list[Evidence]) -> str: ...

    def judge_relevance(self, query: str, text: str) -> float: ...


def split_sentences(text: str) -> list[str]:
    """按中英文句末标点与换行切句; 跳过 markdown 标题行与过短片段。"""
    return [s.strip() for s in SENT_SPLIT_RE.split(text) if len(s.strip()) >= 4 and not s.strip().startswith("#")]


class HeuristicLLM:
    """确定性启发式实现, 不调用任何模型。"""

    name = "heuristic"

    def __init__(self, max_sentences: int = 6, per_item: int = 2) -> None:
        self.max_sentences = max_sentences
        self.per_item = per_item

    def plan_queries(self, query: str) -> list[str]:
        return plan_queries_heuristic(query)

    def judge_relevance(self, query: str, text: str) -> float:
        need = {t for t in tokenize(query) if len(t) > 1}
        if not need:
            return 0.0
        have = set(tokenize(text))
        return len(need & have) / len(need)

    def compose_answer(self, query: str, evidence: list[Evidence]) -> str:
        need = {t for t in tokenize(query) if len(t) > 1}
        idents = [i.lower() for i in extract_identifiers(query)]
        cands: list[tuple[float, int, int, str, Evidence]] = []
        for ev in evidence:
            for pos, sent in enumerate(split_sentences(ev.text)):
                toks = set(tokenize(sent))
                ov = len(toks & need) / len(need) if need else 0.0
                bonus = (0.3 if any(i in sent.lower() for i in idents) else 0.0) + KIND_BONUS.get(ev.kind, 0.0)
                if ov + bonus > KIND_BONUS.get(ev.kind, 0.0):
                    cands.append((-(ov + bonus), ev.rank, pos, sent, ev))
        cands.sort(key=lambda c: (c[0], c[1], c[2]))
        chosen, per = [], {}
        for c in cands:
            if per.get(c[4].item_id, 0) >= self.per_item:
                continue
            per[c[4].item_id] = per.get(c[4].item_id, 0) + 1
            chosen.append(c)
            if len(chosen) >= self.max_sentences:
                break
        if not chosen and evidence:
            chosen = [(0.0, evidence[0].rank, i, s, evidence[0]) for i, s in enumerate(split_sentences(evidence[0].text)[:2])]
        chosen.sort(key=lambda c: (c[1], c[2]))
        lines = [f"- {sent.lstrip('#- ').strip()} [K-{ev.item_id}]" for _, _, _, sent, ev in chosen]
        return "根据知识库中的相关内容：\n" + "\n".join(lines)


class AnthropicLLM:
    """基于 Anthropic SDK 的实现 (可选)。import 被保护; 调用失败时回退到启发式。"""

    name = "anthropic"

    def __init__(self, model: str | None = None, max_tokens: int = 2048) -> None:
        try:
            import anthropic  # type: ignore
        except ImportError as exc:  # pragma: no cover - 环境相关
            raise RuntimeError("anthropic 包未安装") from exc
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("缺少 ANTHROPIC_API_KEY")
        self.model = model or os.environ.get("KLOOP_MODEL", DEFAULT_ANTHROPIC_MODEL)
        self.max_tokens = max_tokens
        self._client = anthropic.Anthropic()
        self._fallback = HeuristicLLM()

    def _complete(self, system: str, user: str) -> str:
        try:
            resp = self._client.messages.create(
                model=self.model, max_tokens=self.max_tokens, system=system,
                messages=[{"role": "user", "content": user}],
            )
        except Exception as exc:  # pragma: no cover - 网络相关
            print(f"[AnthropicLLM] 调用失败, 回退启发式: {exc}", file=sys.stderr)
            return ""
        if getattr(resp, "stop_reason", "") == "refusal":
            return ""
        return "".join(getattr(b, "text", "") for b in resp.content if getattr(b, "type", "") == "text").strip()

    def plan_queries(self, query: str) -> list[str]:
        out = self._complete(
            "你是检索规划器。把用户问题拆成 1-4 个用于关键词检索的子查询, 保留原问题作为第一条, 只输出 JSON 字符串数组。",
            query,
        )
        try:
            arr = json.loads(out[out.index("["): out.rindex("]") + 1])
            qs = [q for q in arr if isinstance(q, str) and q.strip()]
            return qs[:4] if qs else self._fallback.plan_queries(query)
        except (ValueError, IndexError):
            return self._fallback.plan_queries(query)

    def compose_answer(self, query: str, evidence: list[Evidence]) -> str:
        blocks = "\n\n".join(f"[K-{e.item_id}] {e.title} ({e.locator})\n{e.text}" for e in evidence)
        out = self._complete(
            "你是内部工程知识助手。只能依据给定证据回答; 每个要点句末必须带引用标记 [K-<id>], 不要编造证据之外的内容; "
            "证据不足时明确说明。输出简体中文要点列表。",
            f"问题: {query}\n\n证据:\n{blocks}",
        )
        valid = {e.item_id for e in evidence}
        if out and any(m in valid for m in CITE_RE.findall(out)):
            return out
        return self._fallback.compose_answer(query, evidence)

    def judge_relevance(self, query: str, text: str) -> float:
        out = self._complete("给出 0 到 1 之间的一个数字, 表示文本对回答问题的相关程度。只输出数字。", f"问题: {query}\n文本: {text[:1500]}")
        m = re.search(r"\d*\.?\d+", out)
        try:
            return max(0.0, min(1.0, float(m.group(0)))) if m else self._fallback.judge_relevance(query, text)
        except ValueError:
            return self._fallback.judge_relevance(query, text)


def get_llm(name: str | None = None) -> LLMClient:
    """按 KLOOP_LLM 选择后端; anthropic 不可用时打印提示并回退启发式。"""
    choice = (name or os.environ.get("KLOOP_LLM", "heuristic")).lower()
    if choice == "anthropic":
        try:
            return AnthropicLLM()
        except RuntimeError as exc:
            print(f"[kloop] 无法启用 AnthropicLLM ({exc}), 使用 HeuristicLLM", file=sys.stderr)
    return HeuristicLLM()
