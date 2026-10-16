"""答案合成: 证据 -> 带 [K-<id>] 引用标记的答案 + 参考来源列表。

证据不足 (最高相关度低于阈值) 时弃答 (abstain), 不编造, 仍记录候选条目供缺口分析。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .index import Hit
from .llm import CITE_RE, Evidence, HeuristicLLM, LLMClient
from .search import SearchResult

ABSTAIN_THRESHOLD = 0.12  # 最高 bm25_norm 低于此值视为证据不足


@dataclass
class Answer:
    text: str
    cited_item_ids: list[str]
    evidence_ids: list[str]
    versions: dict[str, int] = field(default_factory=dict)
    abstained: bool = False
    max_relevance: float = 0.0

    @property
    def citations(self) -> list[tuple[str, int]]:
        return [(i, self.versions[i]) for i in self.cited_item_ids]


def to_evidence(hits: list[Hit], max_items: int = 5) -> list[Evidence]:
    return [Evidence(h.item.id, h.item.version, h.item.title, h.item.locator, h.item.text, rank, h.item.kind) for rank, h in enumerate(hits[:max_items], 1)]


def compose_answer(query: str, result: SearchResult | list[Hit], llm: LLMClient | None = None, max_evidence: int = 5,
                   abstain_threshold: float = ABSTAIN_THRESHOLD) -> Answer:
    """由检索结果合成答案; 证据不足或查询标识符不在语料中时弃答。"""
    llm = llm or HeuristicLLM()
    hits = result.hits if isinstance(result, SearchResult) else result
    unknown_ident = isinstance(result, SearchResult) and result.identifier_known is False
    evidence = to_evidence(hits, max_evidence)
    versions = {e.item_id: e.version for e in evidence}
    max_rel = max((h.bm25_norm for h in hits[:max_evidence]), default=0.0)
    if not evidence or max_rel < abstain_threshold or unknown_ident:
        near = "\n".join(f"- {e.title} ({e.locator})" for e in evidence[:3])
        why = "问题中的标识符在知识库中没有出现" if unknown_ident else "检索到的内容相关度过低"
        text = f"知识库中没有找到足够可靠的依据来回答这个问题 ({why}), 建议补充相关文档。" + (f"\n最接近的条目 (未引用):\n{near}" if near else "")
        return Answer(text, [], [e.item_id for e in evidence], versions, abstained=True, max_relevance=max_rel)
    body = llm.compose_answer(query, evidence)
    valid = [e.item_id for e in evidence]
    cited = [m for m in dict.fromkeys(CITE_RE.findall(body)) if m in valid]
    if not cited:  # 保证每个答案都带引用
        body += f" [K-{valid[0]}]"
        cited = [valid[0]]
    refs = "\n".join(f"[K-{e.item_id}] {e.title} — {e.locator} (v{e.version})" for e in evidence if e.item_id in cited)
    text = f"{body}\n\n参考来源:\n{refs}"
    return Answer(text, cited, valid, versions, abstained=False, max_relevance=max_rel)
