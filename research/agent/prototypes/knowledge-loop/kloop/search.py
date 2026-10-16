"""DeepSearch 风格的迭代检索循环。

plan (子查询 + 标识符) -> retrieve -> read -> coverage 检查 -> 伪相关反馈扩展 -> 停止
(coverage >= 0.8 / max_steps=4 / 预算用尽 / 无新查询), 全过程记录 SearchTrace。
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field, asdict
from typing import TYPE_CHECKING

from .index import EN_STOP, Hit, Index, tokenize

if TYPE_CHECKING:  # pragma: no cover
    from .llm import LLMClient

LATIN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.]{2,}")
SPLIT_RE = re.compile(r"\s*(?:，|,|；|;|以及|并且|然后|\bthen\b|\band\b|和|与|跟)\s*")
IDENT_PATTERNS = [
    re.compile(r"\b[a-z][a-z0-9]*(?:\.[a-z_][a-z0-9_]*)+\b"),  # key.path
    re.compile(r"\b[a-z0-9]+(?:_[a-z0-9]+)+\b"),  # snake_case
    re.compile(r"\b[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+\b"),  # CamelCase
    re.compile(r"\b[A-Z]{2,}[-_]?\d{2,}\b|\bE\d{3,}\b|\b0x[0-9a-fA-F]+\b|\b[A-Z]{3,}\b"),  # 错误码 / 大写缩写
    re.compile(r"(?<![\w.])--?[a-z][a-z0-9-]+\b"),  # 命令行参数
]


def extract_identifiers(query: str) -> list[str]:
    """提取 snake_case / CamelCase / key.path / 错误码 等标识符 (保序去重)。"""
    found: list[str] = []
    for pat in IDENT_PATTERNS:
        for m in pat.finditer(query):
            tok = m.group(0)
            if tok.lower() in EN_STOP or tok in found:
                continue
            found.append(tok)
    return found


def plan_queries_heuristic(query: str, max_queries: int = 4) -> list[str]:
    """规则式查询分解: 原查询 + 连接词切分的子句 + 标识符单独成查询。"""
    out = [query.strip()]
    parts = [p.strip(" ?？。.!！") for p in SPLIT_RE.split(query)]
    parts = [p for p in parts if len(p) >= 4 and p != query.strip()]
    if len(parts) >= 2:
        out.extend(parts)
    for ident in extract_identifiers(query):
        if ident not in out:
            out.append(ident)
    seen, uniq = set(), []
    for q in out:
        if q and q not in seen:
            seen.add(q)
            uniq.append(q)
    return uniq[:max_queries]


def need_terms(query: str) -> set[str]:
    """覆盖率分母: 查询中的内容词 (标识符 + 子词 + 中文二元组)。"""
    terms = set(tokenize(query))
    for ident in extract_identifiers(query):
        terms.add(ident.lower())
    return {t for t in terms if len(t) > 1 or "一" <= t <= "鿿"}


def coverage_of(need: set[str], texts: list[str]) -> float:
    if not need:
        return 1.0
    have: set[str] = set()
    for t in texts:
        have.update(tokenize(t))
        have.update(w.lower() for w in re.findall(r"[A-Za-z_][\w.]*", t))
    return len(need & have) / len(need)


def identifier_known(index: Index, query: str) -> bool | None:
    """查询中的英文标识符 (>=3 字符) 是否至少有一个出现在索引词表中; 无标识符返回 None。

    全部未知 (如问 Kafka 而语料没有 Kafka) 是“知识库没有相关内容”的强信号, 用于弃答与缺口检测。
    """
    parts: set[str] = set()
    for tok in LATIN_RE.findall(query):
        parts.update(t for t in tokenize(tok) if len(t) >= 3 and not t.isdigit())
    if not parts:
        return None
    return any(p in index.bm25.postings for p in parts)


def prf_terms(hits: list[Hit], index: Index, exclude: set[str], n: int = 3) -> list[str]:
    """伪相关反馈: 从前几名命中的文本中选 idf 最高且未出现在查询中的词。"""
    counts: Counter = Counter()
    for h in hits:
        for tok in set(tokenize(h.item.text)):
            if tok in exclude or len(tok) < 2 or tok.isdigit():
                continue
            counts[tok] += 1
    scored = sorted(counts.items(), key=lambda kv: (-(kv[1] * index.bm25.idf(kv[0])), kv[0]))
    return [t for t, _ in scored[:n]]


@dataclass
class SearchStep:
    step: int
    query: str
    hits: list[str]
    new_evidence: int
    coverage: float
    note: str = ""


@dataclass
class SearchTrace:
    queries: list[str] = field(default_factory=list)
    steps: list[SearchStep] = field(default_factory=list)
    stop_reason: str = ""
    coverage: float = 0.0
    hits_read: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SearchResult:
    query: str
    hits: list[Hit]
    trace: SearchTrace
    identifier_known: bool | None = None  # 查询标识符是否出现在语料中 (None = 查询无标识符)

    @property
    def max_relevance(self) -> float:
        return max((h.bm25_norm for h in self.hits), default=0.0)

    @property
    def answerable(self) -> bool:
        return self.identifier_known is not False and bool(self.hits)


def deep_search(index: Index, query: str, llm: "LLMClient | None" = None, top_k: int = 8, max_steps: int = 4,
                budget: int = 40, coverage_target: float = 0.8, kinds: tuple[str, ...] | None = None,
                acl: list[str] | None = None, as_of: str | None = None) -> SearchResult:
    """多步检索; 最终命中按跨子查询的 RRF 分数求和排序 (多跳证据被多个子查询命中会上浮)。"""
    if llm is None:
        from .llm import HeuristicLLM
        llm = HeuristicLLM()
    pending = llm.plan_queries(query) or [query]
    need = need_terms(query)
    trace = SearchTrace(queries=list(pending))
    evidence: dict[str, Hit] = {}
    agg: dict[str, float] = {}
    issued: set[str] = set()
    stop = "max_steps"
    for step_no in range(1, max_steps + 1):
        if not pending:
            stop = "no_more_queries"
            break
        q = pending.pop(0)
        issued.add(q)
        hits = index.search(q, top_k=top_k, kinds=kinds, acl=acl, as_of=as_of)
        trace.hits_read += len(hits)
        new = 0
        for h in hits:
            agg[h.key] = agg.get(h.key, 0.0) + h.score
            if h.key in evidence:
                ev = evidence[h.key]
                ev.queries.append(q)
                if h.bm25_norm > ev.bm25_norm:
                    ev.bm25, ev.bm25_norm, ev.cosine, ev.why = h.bm25, h.bm25_norm, h.cosine, h.why
            else:
                evidence[h.key] = h
                new += 1
        top_keys = [k for k, _ in sorted(agg.items(), key=lambda kv: (-kv[1], kv[0]))[:5]]
        cov = coverage_of(need, [evidence[k].item.text for k in top_keys])
        note = ""
        if cov >= coverage_target:
            stop = "coverage_reached"
        elif trace.hits_read >= budget:
            stop = "budget_exhausted"
        elif not pending:
            exp = prf_terms([evidence[k] for k in top_keys[:2]], index, need | set(tokenize(query)))
            if exp:
                nq = f"{query} {' '.join(exp)}"
                if nq not in issued:
                    pending.append(nq)
                    note = f"PRF 扩展: {', '.join(exp)}"
        trace.steps.append(SearchStep(step_no, q, [h.key for h in hits], new, round(cov, 3), note))
        trace.coverage = cov
        if stop in ("coverage_reached", "budget_exhausted"):
            break
    trace.stop_reason = stop
    final: list[Hit] = []
    for key, score in sorted(agg.items(), key=lambda kv: (-kv[1], kv[0])):
        h = evidence[key]
        h.score = score
        final.append(h)
    return SearchResult(query=query, hits=final, trace=trace, identifier_known=identifier_known(index, query))
