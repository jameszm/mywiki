"""切分、上下文头与稳定 id。"""
from __future__ import annotations

import hashlib
import re

from .models import KnowledgeItem

MAX_CHARS = 1500  # 单条目最大字符数, 超过则按段落切分


def stable_id(source: str, locator: str, kind: str, heading_path: str) -> str:
    """稳定 id = sha1(source|locator|kind|heading_path)[:12], 与内容无关。"""
    raw = f"{source}|{locator}|{kind}|{heading_path}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:12]


def content_hash(text: str) -> str:
    """内容哈希: 归一化空白后的 sha1, 用于判断条目是否变化。"""
    norm = re.sub(r"\s+", " ", text).strip()
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()


def build_context_header(item: KnowledgeItem) -> str:
    """上下文头: 来源/路径/章节/版本, 作为条目文本的前缀进入索引与证据。"""
    section = item.heading_path or item.title
    return f"来源: {item.source_id} | 路径: {item.locator} | 章节: {section} | 版本: v{item.version}"


def split_text(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    """按段落切分到大小上限; 单段落超限时按行硬切。"""
    text = text.strip()
    if len(text) <= max_chars:
        return [text] if text else []
    chunks: list[str] = []
    buf = ""
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if not para:
            continue
        if len(para) > max_chars:  # 超长段落按行硬切
            for line in para.splitlines():
                if len(buf) + len(line) + 1 > max_chars and buf:
                    chunks.append(buf.strip())
                    buf = ""
                buf += line + "\n"
            continue
        if len(buf) + len(para) + 2 > max_chars and buf:
            chunks.append(buf.strip())
            buf = ""
        buf += para + "\n\n"
    if buf.strip():
        chunks.append(buf.strip())
    return chunks


def make_items(
    source_id: str,
    locator: str,
    kind: str,
    sections: list[tuple[str, str, str, dict]],
    acl: list[str] | None = None,
    max_chars: int = MAX_CHARS,
) -> list[KnowledgeItem]:
    """把接入器产出的 (heading_path, title, text, metadata) 列表变成条目草稿。

    版本号与上下文头由 sync 在确定版本后填写 (finalize_item)。
    """
    items: list[KnowledgeItem] = []
    for heading_path, title, text, meta in sections:
        chunks = split_text(text, max_chars)
        for i, chunk in enumerate(chunks):
            hp = heading_path if len(chunks) == 1 else f"{heading_path} #{i + 1}"
            md = dict(meta)
            if len(chunks) > 1:
                md["chunk"] = i + 1
                md["chunks"] = len(chunks)
            items.append(
                KnowledgeItem(
                    id=stable_id(source_id, locator, kind, hp),
                    source_id=source_id,
                    locator=locator,
                    kind=kind,
                    title=title if len(chunks) == 1 else f"{title} (第{i + 1}段)",
                    text=chunk,
                    content_hash=content_hash(chunk),
                    metadata=md,
                    acl=list(acl or ["all"]),
                    heading_path=hp,
                )
            )
    return items


def finalize_item(item: KnowledgeItem, version: int, now: str) -> KnowledgeItem:
    """同步时确定版本号后补全上下文头与时间戳。"""
    item.version = version
    item.valid_from = now
    item.valid_to = None
    item.superseded_by = None
    item.status = "active"
    item.last_verified_at = now
    item.context_header = build_context_header(item)
    return item
