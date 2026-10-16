"""检索索引: BM25 (k1=1.5, b=0.75) + 字符 3-gram TF-IDF 余弦, RRF 融合。

- 分词: 英文/标识符 (snake_case、CamelCase、key.path 拆分) + 中文二元组 (无分词器)。
- 支持增量 add/remove (同步时只重建受影响条目), 过滤: kind / acl / 仅当前有效 (或 as_of)。
- 每个命中返回各信号分数与可读的 why 字符串。
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .models import KnowledgeItem

if TYPE_CHECKING:  # pragma: no cover
    from .store import Store

EN_STOP = {"the", "a", "an", "of", "to", "in", "on", "for", "and", "or", "is", "are", "be", "with", "by", "as", "at",
           "it", "this", "that", "from", "how", "what", "when", "which", "do", "does", "can", "should", "def", "self",
           "return", "none", "true", "false", "if", "else", "import", "class", "str", "int", "float", "list", "dict"}
CJK_STOP_CHARS = set("的了吗呢么请把被让就也都或呀啊吧")
CJK_STOP_BIGRAMS = {"怎么", "什么", "如何", "多少", "是多", "哪些", "哪个", "可以", "应该", "需要", "现在", "一下", "为什",
                    "意思", "请问", "怎样", "是什", "还是", "是否", "能不", "不能", "有没", "没有", "一个", "这个", "那个",
                    "一般", "通常", "到底", "究竟", "有哪", "些什", "是怎", "是不", "不是", "还有", "以及", "以后", "之后"}
TOKEN_RE = re.compile(
    r"[一-鿿]+|[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+|[A-Za-z_][A-Za-z0-9_]*|\d+(?:\.\d+)?(?:[eE][-+]?\d+)?%?"
)
CAMEL_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+")


def _cjk_tokens(run: str) -> list[str]:
    if len(run) == 1:
        return [] if run in CJK_STOP_CHARS else [run]
    out = []
    for i in range(len(run) - 1):
        bg = run[i:i + 2]
        if bg[0] in CJK_STOP_CHARS or bg[1] in CJK_STOP_CHARS or bg in CJK_STOP_BIGRAMS:
            continue
        out.append(bg)
    return out


def _split_identifier(s: str) -> list[str]:
    """snake_case / CamelCase / key.path 拆成子词 (保留完整形式与各级组件)。"""
    out = [s.lower()]
    comps = s.split(".")
    if len(comps) > 1:
        out.extend(c.lower() for c in comps)
    for comp in comps:
        parts = [p for p in comp.split("_") if p]
        subs: list[str] = []
        for p in parts:
            subs.extend(CAMEL_RE.findall(p) if any(ch.isupper() for ch in p[1:]) else [p])
        if len(subs) > 1 or len(parts) > 1 or len(comps) > 1:
            out.extend(x.lower() for x in subs if len(x) > 1)
    seen, uniq = set(), []
    for t in out:
        if t not in seen and t not in EN_STOP:
            seen.add(t)
            uniq.append(t)
    return uniq


def tokenize(text: str) -> list[str]:
    """中英混合分词 (确定性)。"""
    tokens: list[str] = []
    for m in TOKEN_RE.finditer(text):
        s = m.group(0)
        c = s[0]
        if "一" <= c <= "鿿":
            tokens.extend(_cjk_tokens(s))
        elif c.isdigit():
            tokens.append(s)
        else:
            tokens.extend(_split_identifier(s))
    return tokens


def trigrams(text: str) -> Counter:
    norm = re.sub(r"\s+", " ", text.lower()).strip()
    return Counter(norm[i:i + 3] for i in range(len(norm) - 2)) if len(norm) >= 3 else Counter({norm: 1} if norm else {})


class BM25:
    """增量 BM25; postings[token] = {key: tf}。"""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1, self.b = k1, b
        self.postings: dict[str, dict[str, int]] = {}
        self.doc_len: dict[str, int] = {}
        self.doc_tokens: dict[str, Counter] = {}

    def add(self, key: str, tokens: list[str]) -> None:
        if key in self.doc_len:
            self.remove(key)
        tf = Counter(tokens)
        self.doc_tokens[key] = tf
        self.doc_len[key] = len(tokens)
        for t, n in tf.items():
            self.postings.setdefault(t, {})[key] = n

    def remove(self, key: str) -> None:
        tf = self.doc_tokens.pop(key, None)
        if tf is None:
            return
        del self.doc_len[key]
        for t in tf:
            plist = self.postings.get(t)
            if plist:
                plist.pop(key, None)
                if not plist:
                    del self.postings[t]

    @property
    def n_docs(self) -> int:
        return len(self.doc_len)

    def idf(self, token: str) -> float:
        df = len(self.postings.get(token, ()))
        return math.log(1 + (self.n_docs - df + 0.5) / (df + 0.5))

    def score(self, query_tokens: list[str], candidates: set[str] | None = None) -> dict[str, float]:
        if not self.doc_len:
            return {}
        avgdl = sum(self.doc_len.values()) / len(self.doc_len)
        scores: dict[str, float] = {}
        for t in set(query_tokens):
            plist = self.postings.get(t)
            if not plist:
                continue
            idf = self.idf(t)
            for key, tf in plist.items():
                if candidates is not None and key not in candidates:
                    continue
                dl = self.doc_len[key]
                scores[key] = scores.get(key, 0.0) + idf * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * dl / avgdl))
        return scores

    def ideal_score(self, query_tokens: list[str]) -> float:
        """查询所有词项都饱和命中时的分数上界, 用于把 BM25 归一化到 [0,1)。"""
        return sum(self.idf(t) * (self.k1 + 1) for t in set(query_tokens)) or 1.0


class TrigramIndex:
    """字符 3-gram TF-IDF 余弦 (权重 (1+ln tf)*idf, 文档范数在变更后惰性重算)。"""

    def __init__(self) -> None:
        self.doc_grams: dict[str, Counter] = {}
        self.postings: dict[str, dict[str, int]] = {}
        self._norms: dict[str, float] = {}
        self._idf: dict[str, float] = {}
        self._dirty = True

    def add(self, key: str, text: str) -> None:
        if key in self.doc_grams:
            self.remove(key)
        grams = trigrams(text)
        self.doc_grams[key] = grams
        for g, n in grams.items():
            self.postings.setdefault(g, {})[key] = n
        self._dirty = True

    def remove(self, key: str) -> None:
        grams = self.doc_grams.pop(key, None)
        if grams is None:
            return
        for g in grams:
            plist = self.postings.get(g)
            if plist:
                plist.pop(key, None)
                if not plist:
                    del self.postings[g]
        self._dirty = True

    def _ensure(self) -> None:
        if not self._dirty:
            return
        n = len(self.doc_grams) or 1
        self._idf = {g: math.log((n + 1) / (len(p) + 1)) + 1 for g, p in self.postings.items()}
        self._norms = {}
        for key, grams in self.doc_grams.items():
            self._norms[key] = math.sqrt(sum(((1 + math.log(c)) * self._idf[g]) ** 2 for g, c in grams.items())) or 1.0
        self._dirty = False

    def score(self, query: str, candidates: set[str] | None = None) -> dict[str, float]:
        self._ensure()
        q = trigrams(query)
        if not q:
            return {}
        qw = {g: (1 + math.log(c)) * self._idf.get(g, 1.0) for g, c in q.items()}
        qnorm = math.sqrt(sum(w * w for w in qw.values())) or 1.0
        dots: dict[str, float] = {}
        for g, w in qw.items():
            for key, c in self.postings.get(g, {}).items():
                if candidates is not None and key not in candidates:
                    continue
                dots[key] = dots.get(key, 0.0) + w * (1 + math.log(c)) * self._idf[g]
        return {k: v / (qnorm * self._norms[k]) for k, v in dots.items()}


@dataclass
class Hit:
    item: KnowledgeItem
    score: float
    bm25: float = 0.0
    bm25_norm: float = 0.0
    cosine: float = 0.0
    rank_bm25: int = 0
    rank_cos: int = 0
    why: str = ""
    queries: list[str] = field(default_factory=list)

    @property
    def key(self) -> str:
        return self.item.key

    def signals(self) -> dict:
        return {"rrf": round(self.score, 5), "bm25": round(self.bm25, 3), "bm25_norm": round(self.bm25_norm, 3),
                "cosine": round(self.cosine, 3), "rank_bm25": self.rank_bm25, "rank_cos": self.rank_cos, "queries": list(self.queries)}


def rrf_fuse(rankings: list[list[str]], k: int = 60) -> dict[str, float]:
    """Reciprocal Rank Fusion: score(d) = Σ_r 1/(k + rank_r(d))。"""
    fused: dict[str, float] = {}
    for ranking in rankings:
        for rank, key in enumerate(ranking, start=1):
            fused[key] = fused.get(key, 0.0) + 1.0 / (k + rank)
    return fused


class Index:
    """组合索引; 条目以物理键 id@version 存放。"""

    def __init__(self, k1: float = 1.5, b: float = 0.75, rrf_k: int = 60) -> None:
        self.items: dict[str, KnowledgeItem] = {}
        self.bm25 = BM25(k1, b)
        self.tri = TrigramIndex()
        self.rrf_k = rrf_k

    @classmethod
    def from_store(cls, store: "Store", as_of: str | None = None, include_history: bool = False) -> "Index":
        idx = cls()
        if include_history:
            items = store.all_items()
        elif as_of:
            items = store.items_as_of(as_of)
        else:
            items = store.current_items()
        idx.add_items(items)
        return idx

    def __len__(self) -> int:
        return len(self.items)

    def add_items(self, items: list[KnowledgeItem]) -> int:
        for it in items:
            self.items[it.key] = it
            text = it.indexed_text()
            self.bm25.add(it.key, tokenize(text))
            self.tri.add(it.key, text)
        return len(items)

    def remove_items(self, keys: list[str]) -> int:
        n = 0
        for key in keys:
            if self.items.pop(key, None) is not None:
                self.bm25.remove(key)
                self.tri.remove(key)
                n += 1
        return n

    def _candidates(self, kinds: tuple[str, ...] | None, acl: list[str] | None, as_of: str | None) -> set[str]:
        out = set()
        groups = set(acl) if acl is not None else None
        for key, it in self.items.items():
            if kinds and it.kind not in kinds:
                continue
            if groups is not None and "all" not in it.acl and not groups.intersection(it.acl):
                continue
            if as_of:
                if it.valid_from > as_of or (it.valid_to is not None and it.valid_to <= as_of):
                    continue
            elif it.valid_to is not None:
                continue
            out.add(key)
        return out

    def search(self, query: str, top_k: int = 10, kinds: tuple[str, ...] | None = None, acl: list[str] | None = None,
               as_of: str | None = None, candidate_n: int = 50) -> list[Hit]:
        cands = self._candidates(kinds, acl, as_of)
        if not cands:
            return []
        q_tokens = tokenize(query)
        bm = self.bm25.score(q_tokens, cands)
        cos = self.tri.score(query, cands)
        bm_rank = [k for k, _ in sorted(bm.items(), key=lambda kv: (-kv[1], kv[0]))[:candidate_n]]
        cos_rank = [k for k, _ in sorted(cos.items(), key=lambda kv: (-kv[1], kv[0]))[:candidate_n]]
        fused = rrf_fuse([bm_rank, cos_rank], self.rrf_k)
        ideal = self.bm25.ideal_score(q_tokens)
        bm_pos = {k: i + 1 for i, k in enumerate(bm_rank)}
        cos_pos = {k: i + 1 for i, k in enumerate(cos_rank)}
        hits: list[Hit] = []
        for key, score in sorted(fused.items(), key=lambda kv: (-kv[1], kv[0]))[:top_k]:
            item = self.items[key]
            matched = [t for t in dict.fromkeys(q_tokens) if t in self.bm25.doc_tokens.get(key, ())]
            matched.sort(key=lambda t: -self.bm25.idf(t))
            why = (f"BM25 {bm.get(key, 0.0):.2f} (命中: {', '.join(matched[:4]) or '无'}) · "
                   f"3-gram余弦 {cos.get(key, 0.0):.2f} · RRF {score:.4f}")
            hits.append(Hit(item=item, score=score, bm25=bm.get(key, 0.0), bm25_norm=min(1.0, bm.get(key, 0.0) / ideal),
                            cosine=cos.get(key, 0.0), rank_bm25=bm_pos.get(key, 0), rank_cos=cos_pos.get(key, 0), why=why, queries=[query]))
        return hits
