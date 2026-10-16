"""Python 代码接入器 (基于 ast): 模块 docstring、类、函数 (签名 + docstring + 函数体摘录)。

稳定 id 来自限定名 (qualified name), 重构不改名则 id 不变。
"""
from __future__ import annotations

import ast

from ..chunking import make_items
from ..models import KnowledgeItem, RawDocument
from . import Connector

BODY_LINES = 12


def _signature(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> str:
    if isinstance(node, ast.ClassDef):
        bases = ", ".join(ast.unparse(b) for b in node.bases)
        return f"class {node.name}({bases})" if bases else f"class {node.name}"
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    ret = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    return f"{prefix} {node.name}({ast.unparse(node.args)}){ret}"


def _body_excerpt(node: ast.AST, lines: list[str], max_lines: int = BODY_LINES) -> str:
    body = getattr(node, "body", [])
    if not body:
        return ""
    start = body[0].lineno - 1
    if isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
        if len(body) == 1:
            return ""
        start = body[1].lineno - 1
    end = min(getattr(node, "end_lineno", start + 1), start + max_lines)
    excerpt = lines[start:end]
    more = "\n    ..." if getattr(node, "end_lineno", 0) > end else ""
    return "\n".join(excerpt) + more


class PythonConnector(Connector):
    kind = "code"
    suffixes = (".py",)

    def extract(self, raw: RawDocument, source_id: str) -> list[KnowledgeItem]:
        try:
            tree = ast.parse(raw.text)
        except SyntaxError as exc:  # 语法错误的文件整体作为一个条目, 不中断同步
            return make_items(source_id, raw.locator, self.kind, [("module", raw.locator, f"(语法错误: {exc})\n{raw.text[:800]}", {})])
        lines = raw.text.splitlines()
        modname = raw.locator.rsplit("/", 1)[-1].removesuffix(".py")
        sections: list[tuple[str, str, str, dict]] = []
        top_names = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        consts = [ast.unparse(n) for n in tree.body if isinstance(n, ast.Assign) and len(ast.unparse(n)) < 120]
        mod_doc = ast.get_docstring(tree) or ""
        mod_text = f"模块 {modname}\n{mod_doc}\n定义: {', '.join(top_names)}"
        if consts:
            mod_text += "\n常量:\n" + "\n".join(consts)
        sections.append(("module", f"{modname} 模块", mod_text, {"qualname": modname, "names": top_names}))

        def add_func(node: ast.FunctionDef | ast.AsyncFunctionDef, qual: str) -> None:
            doc = ast.get_docstring(node) or ""
            decos = [f"@{ast.unparse(d)}" for d in node.decorator_list]
            text = "\n".join(decos + [_signature(node) + ":"])
            if doc:
                text += f'\n    """{doc}"""'
            excerpt = _body_excerpt(node, lines)
            if excerpt:
                text += "\n" + excerpt
            args = [a.arg for a in node.args.args + node.args.kwonlyargs]
            sections.append((qual, qual, text, {"qualname": qual, "lineno": node.lineno, "args": args, "decorators": decos}))

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                add_func(node, f"{modname}.{node.name}")
            elif isinstance(node, ast.ClassDef):
                qual = f"{modname}.{node.name}"
                methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                doc = ast.get_docstring(node) or ""
                text = f"{_signature(node)}:\n"
                if doc:
                    text += f'    """{doc}"""\n'
                text += "方法: " + ", ".join(_signature(m) for m in methods)
                sections.append((qual, qual, text, {"qualname": qual, "lineno": node.lineno, "methods": [m.name for m in methods]}))
                for m in methods:
                    add_func(m, f"{qual}.{m.name}")
        return make_items(source_id, raw.locator, self.kind, sections)
