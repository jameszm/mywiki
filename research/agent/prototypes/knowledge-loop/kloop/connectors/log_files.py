"""日志接入器: Drain 风格的模板挖掘。

分词 -> 屏蔽数字/十六进制/IP/路径/id -> 按 (级别, token 数) 分桶 -> 与桶内模板按位置相似度合并
(>= 0.6, 差异位置写成 <*>) -> 每个模板一个条目 (次数 / 首末次出现 / 3 条样例 / 严重级别)。
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

from ..chunking import make_items
from ..models import KnowledgeItem, RawDocument
from . import Connector

LINE_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?)?\s*\[?(?P<level>TRACE|DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL)\]?\s*(?P<msg>.*)$"
)
MASKS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?"), "<TS>"),
    (re.compile(r"\b\d{4}-\d{2}-\d{2}\b"), "<DATE>"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?\b"), "<IP>"),
    (re.compile(r"\b0x[0-9a-fA-F]+\b"), "<HEX>"),
    (re.compile(r"(?<![\w/])/[\w./-]+"), "<PATH>"),
    (re.compile(r"\b[A-Za-z]+[-_](?:[0-9a-f]{6,}|\d{3,})\b"), "<ID>"),
    (re.compile(r"\b[0-9a-f]{12,}\b"), "<HEX>"),
    (re.compile(r"(?<![A-Za-z0-9_])[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?(?:ms|s|%|MB|GB|KB|m|h)?(?![A-Za-z_])"), "<NUM>"),
]
SEVERITY = {"TRACE": 0, "DEBUG": 1, "INFO": 2, "WARN": 3, "WARNING": 3, "ERROR": 4, "FATAL": 5, "CRITICAL": 5}
SIM_THRESHOLD = 0.6
WORD_STOP = {"error", "warn", "warning", "info", "debug", "failed", "failure", "with", "from", "for", "retry",
             "after", "exceeds", "saved", "step", "epoch", "loss", "the", "and", "not", "found", "while"}


def mask_line(msg: str) -> str:
    for pat, rep in MASKS:
        msg = pat.sub(rep, msg)
    return msg


def parse_line(line: str) -> tuple[str, str, str] | None:
    m = LINE_RE.match(line.strip())
    if not m or not m.group("msg"):
        return None
    level = m.group("level")
    return m.group("ts") or "", "WARN" if level == "WARNING" else level, m.group("msg").strip()


@dataclass
class LogTemplate:
    level: str
    tokens: list[str]
    count: int = 0
    first_seen: str = ""
    last_seen: str = ""
    samples: list[str] = field(default_factory=list)

    @property
    def template(self) -> str:
        return " ".join(self.tokens)

    def absorb(self, tokens: list[str], ts: str, line: str) -> None:
        self.tokens = [a if a == b else "<*>" for a, b in zip(self.tokens, tokens)]
        self.count += 1
        if ts:
            self.first_seen = min(self.first_seen or ts, ts)
            self.last_seen = max(self.last_seen, ts)
        if len(self.samples) < 3:
            self.samples.append(line.strip())


def _similarity(a: list[str], b: list[str]) -> float:
    return sum(1 for x, y in zip(a, b) if x == y or x == "<*>") / max(1, len(a))


def mine_templates(lines: list[str], threshold: float = SIM_THRESHOLD) -> list[LogTemplate]:
    """按文件顺序处理, 结果确定; 返回模板列表 (按首次出现顺序)。"""
    buckets: dict[tuple[str, int], list[LogTemplate]] = {}
    order: list[LogTemplate] = []
    for line in lines:
        parsed = parse_line(line)
        if not parsed:
            continue
        ts, level, msg = parsed
        tokens = mask_line(msg).split()
        bucket = buckets.setdefault((level, len(tokens)), [])
        best, best_sim = None, 0.0
        for t in bucket:
            sim = _similarity(t.tokens, tokens)
            if sim > best_sim:
                best, best_sim = t, sim
        if best is None or best_sim < threshold:
            best = LogTemplate(level=level, tokens=list(tokens))
            bucket.append(best)
            order.append(best)
        best.absorb(tokens, ts, line)
    return order


def template_keywords(template: str) -> list[str]:
    """模板中的标识符类关键词 (CamelCase / snake_case / 长单词), 用于与文档关联。"""
    out = []
    for tok in re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}", template):
        if tok.lower() in WORD_STOP or tok.startswith("<"):
            continue
        out.append(tok)
    return sorted(set(out))


class LogConnector(Connector):
    kind = "log"
    suffixes = (".log",)

    def extract(self, raw: RawDocument, source_id: str) -> list[KnowledgeItem]:
        sections = []
        for t in mine_templates(raw.text.splitlines()):
            kws = template_keywords(t.template)
            text = (
                f"日志模板 [{t.level}]: {t.template}\n出现次数: {t.count}\n首次出现: {t.first_seen or '未知'}\n"
                f"最近出现: {t.last_seen or '未知'}\n严重级别: {t.level}\n关键词: {', '.join(kws) or '无'}\n样例:\n"
                + "\n".join(f"  {s}" for s in t.samples)
            )
            meta = {"template": t.template, "count": t.count, "first_seen": t.first_seen, "last_seen": t.last_seen,
                    "severity": t.level, "severity_rank": SEVERITY.get(t.level, 2), "keywords": kws, "samples": t.samples}
            sections.append((f"{t.level} {t.template}", f"[{t.level}] {t.template}", text, meta))
        return make_items(source_id, raw.locator, self.kind, sections)


def link_templates_to_docs(log_items: list[KnowledgeItem], doc_items: list[KnowledgeItem], max_links: int = 2) -> int:
    """按关键词重叠把日志模板关联到 runbook/文档条目 (写入 metadata.related_docs); 返回建立的链接数。"""
    linked = 0
    docs = [(d, d.text.lower()) for d in doc_items]
    for item in log_items:
        kws = item.metadata.get("keywords") or []
        scored = []
        for d, low in docs:
            score = 0
            for kw in kws:
                if kw.lower() in low:
                    score += 2 if ("_" in kw or re.search(r"[a-z][A-Z]", kw)) else 1
            if score >= 2:
                scored.append((-score, d.locator, d.heading_path, d.id))
        scored.sort()
        item.metadata["related_docs"] = [{"item_id": s[3], "locator": s[1], "section": s[2]} for s in scored[:max_links]]
        linked += len(item.metadata["related_docs"])
    return linked
