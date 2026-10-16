"""Markdown 文档接入器: 按标题层级切成章节, 每章节一个条目。

稳定 id 来自 (source, locator, heading_path), 与内容无关; 支持简单 front matter (acl)。
"""
from __future__ import annotations

import re

from ..chunking import make_items
from ..models import KnowledgeItem, RawDocument
from . import Connector

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    """解析文件头部 `---` 包裹的 key: value 块, 返回 (meta, 正文)。"""
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            meta: dict[str, str] = {}
            for line in lines[1:i]:
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
            return meta, "\n".join(lines[i + 1:])
    return {}, text


def parse_sections(text: str) -> list[tuple[str, str, str, int]]:
    """返回 [(heading_path, title, body_with_heading, level)], 忽略代码块内的 '#'。"""
    sections: list[tuple[str, str, str, int]] = []
    stack: list[tuple[int, str]] = []
    cur_title, cur_level, buf = "", 0, []
    in_fence = False

    def flush() -> None:
        body = "\n".join(buf).strip()
        if body:
            path = " > ".join(t for _, t in stack) if stack else ""
            text_out = (f"{'#' * cur_level} {cur_title}\n{body}" if cur_title else body)
            sections.append((path, cur_title, text_out, cur_level))

    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
        m = None if in_fence else HEADING_RE.match(line)
        if m:
            flush()
            level, title = len(m.group(1)), m.group(2).strip()
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
            cur_title, cur_level, buf = title, level, []
        else:
            buf.append(line)
    flush()
    return sections


class MarkdownConnector(Connector):
    kind = "doc"
    suffixes = (".md", ".markdown")

    def extract(self, raw: RawDocument, source_id: str) -> list[KnowledgeItem]:
        meta, body = parse_front_matter(raw.text)
        acl = [a.strip() for a in re.split(r"[,\s]+", meta.get("acl", "all").strip("[]")) if a.strip()] or ["all"]
        doc_title = next((t for _, t, _, lvl in parse_sections(body) if lvl == 1), raw.locator.rsplit("/", 1)[-1])
        sections = []
        for path, title, text, level in parse_sections(body):
            md = {"doc_title": doc_title, "level": level, "chars": len(text)}
            sections.append((path or "(前言)", title or doc_title, text, md))
        return make_items(source_id, raw.locator, self.kind, sections, acl=acl)
