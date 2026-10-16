"""接入器基类与注册表。

Connector.scan(root) -> list[RawDocument]; Connector.extract(raw, source_id) -> list[KnowledgeItem] (草稿)。
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from ..models import KnowledgeItem, RawDocument


class Connector:
    """接入器基类: 子类声明 kind 与文件后缀, 实现 extract。"""

    kind: str = ""
    suffixes: tuple[str, ...] = ()

    def matches(self, path: Path) -> bool:
        return path.suffix.lower() in self.suffixes

    def scan(self, root: Path) -> list[RawDocument]:
        root = Path(root)
        docs: list[RawDocument] = []
        for path in sorted(p for p in root.rglob("*") if p.is_file() and self.matches(p)):
            docs.append(read_raw(path, root, self.kind))
        return docs

    def extract(self, raw: RawDocument, source_id: str) -> list[KnowledgeItem]:  # pragma: no cover - abstract
        raise NotImplementedError


def read_raw(path: Path, root: Path, kind: str) -> RawDocument:
    data = path.read_bytes()
    return RawDocument(
        locator=path.relative_to(root).as_posix(),
        text=data.decode("utf-8", errors="replace"),
        mtime=path.stat().st_mtime,
        sha256=hashlib.sha256(data).hexdigest(),
        kind=kind,
    )


def default_connectors() -> list[Connector]:
    from .config_files import ConfigConnector
    from .log_files import LogConnector
    from .markdown_docs import MarkdownConnector
    from .python_code import PythonConnector

    return [MarkdownConnector(), PythonConnector(), ConfigConnector(), LogConnector()]


def scan_all(root: Path, connectors: list[Connector] | None = None) -> list[tuple[Connector, RawDocument]]:
    """扫描根目录, 返回 (connector, raw) 对, 按 locator 排序保证确定性。"""
    pairs: list[tuple[Connector, RawDocument]] = []
    for conn in connectors or default_connectors():
        for raw in conn.scan(Path(root)):
            pairs.append((conn, raw))
    pairs.sort(key=lambda p: p[1].locator)
    return pairs
