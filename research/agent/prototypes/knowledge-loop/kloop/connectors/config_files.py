"""配置文件接入器: JSON 与 YAML 子集 (无 PyYAML)。

每个顶层 section 一个条目, 文本为 `key.path = value  # 注释` 行; metadata.kv 保存扁平键值对,
供冲突检测 (同一 key-path 不同取值) 使用。
"""
from __future__ import annotations

import json
import re
from typing import Any

from ..chunking import make_items
from ..models import KnowledgeItem, RawDocument
from . import Connector


class YamlError(ValueError):
    pass


def _split_comment(line: str) -> tuple[str, str]:
    """去掉行尾注释 (引号内的 # 不算)。"""
    quote = None
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            return line[:i].rstrip(), line[i + 1:].strip()
    return line.rstrip(), ""


def parse_scalar(raw: str) -> Any:
    s = raw.strip()
    if s == "" or s in ("null", "~", "None"):
        return None
    if (s[0] == s[-1]) and s[0] in ("'", '"') and len(s) >= 2:
        return s[1:-1]
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        return [parse_scalar(p) for p in inner.split(",")] if inner else []
    if s.startswith("{") and s.endswith("}"):
        out: dict[str, Any] = {}
        for part in filter(None, (p.strip() for p in s[1:-1].split(","))):
            k, _, v = part.partition(":")
            out[k.strip()] = parse_scalar(v)
        return out
    low = s.lower()
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    if re.fullmatch(r"[-+]?\d+", s):
        return int(s)
    if re.fullmatch(r"[-+]?(\d+\.\d*|\.\d+|\d+)([eE][-+]?\d+)?", s):
        return float(s)
    return s


def parse_yaml(text: str) -> tuple[Any, dict[str, str]]:
    """YAML 子集解析: 映射/列表/标量/注释/行内列表; 返回 (data, {key_path: 注释})。"""
    lines: list[list[Any]] = []  # [indent, content, trailing_comment, preceding_comments]
    pending: list[str] = []
    for raw in text.splitlines():
        if not raw.strip():
            continue
        content, comment = _split_comment(raw)
        if not content.strip():
            pending.append(comment)
            continue
        indent = len(content) - len(content.lstrip(" "))
        lines.append([indent, content.strip(), comment, " ".join(pending)])
        pending = []
    comments: dict[str, str] = {}

    def is_list_item(c: str) -> bool:
        return c == "-" or c.startswith("- ")

    def parse_block(i: int, indent: int, path: str) -> tuple[Any, int]:
        if i >= len(lines):
            return None, i
        return (parse_list if is_list_item(lines[i][1]) else parse_map)(i, indent, path)

    def parse_map(i: int, indent: int, path: str) -> tuple[dict[str, Any], int]:
        out: dict[str, Any] = {}
        while i < len(lines) and lines[i][0] == indent and not is_list_item(lines[i][1]):
            ind, content, comment, pre = lines[i]
            if ":" not in content:
                raise YamlError(f"第 {i + 1} 行不是 key: value: {content!r}")
            key, _, rest = content.partition(":")
            key, rest = key.strip().strip("'\""), rest.strip()
            kp = f"{path}.{key}" if path else key
            note = comment or pre
            if note:
                comments[kp] = note
            if rest == "":
                if i + 1 < len(lines) and lines[i + 1][0] > indent:
                    out[key], i = parse_block(i + 1, lines[i + 1][0], kp)
                elif i + 1 < len(lines) and lines[i + 1][0] == indent and is_list_item(lines[i + 1][1]):
                    out[key], i = parse_list(i + 1, indent, kp)  # 与键同缩进的列表
                else:
                    out[key], i = None, i + 1
            else:
                out[key], i = parse_scalar(rest), i + 1
        if i < len(lines) and lines[i][0] > indent:
            raise YamlError(f"第 {i + 1} 行缩进异常: {lines[i][1]!r}")
        return out, i

    def parse_list(i: int, indent: int, path: str) -> tuple[list[Any], int]:
        out: list[Any] = []
        while i < len(lines) and lines[i][0] == indent and is_list_item(lines[i][1]):
            ind, content, comment, pre = lines[i]
            rest = content[1:].strip()
            kp = f"{path}[{len(out)}]"
            if comment or pre:
                comments[kp] = comment or pre
            if rest == "":
                val, i = parse_block(i + 1, lines[i + 1][0], kp) if i + 1 < len(lines) else (None, i + 1)
            elif re.match(r"^[\w'\"-]+\s*:(\s|$)", rest):  # "- key: value" 开头的映射项
                virtual = indent + (len(content) - len(rest))
                lines[i] = [virtual, rest, comment, pre]
                val, i = parse_map(i, virtual, kp)
            else:
                val, i = parse_scalar(rest), i + 1
            out.append(val)
        return out, i

    data, i = parse_block(0, lines[0][0] if lines else 0, "")
    if i < len(lines):
        raise YamlError(f"第 {i + 1} 行无法解析: {lines[i][1]!r}")
    return data, comments


def flatten(data: Any, prefix: str = "") -> list[tuple[str, Any]]:
    """扁平化为 [(key.path, scalar)], 列表用 [i] 下标。"""
    out: list[tuple[str, Any]] = []
    if isinstance(data, dict):
        for k, v in data.items():
            out.extend(flatten(v, f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(data, list):
        if all(not isinstance(v, (dict, list)) for v in data):
            out.append((prefix, data))
        else:
            for i, v in enumerate(data):
                out.extend(flatten(v, f"{prefix}[{i}]"))
    else:
        out.append((prefix, data))
    return out


def fmt_value(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return "null"
    if isinstance(v, list):
        return "[" + ", ".join(fmt_value(x) for x in v) + "]"
    return str(v)


class ConfigConnector(Connector):
    kind = "config"
    suffixes = (".yaml", ".yml", ".json")

    def extract(self, raw: RawDocument, source_id: str) -> list[KnowledgeItem]:
        comments: dict[str, str] = {}
        try:
            if raw.locator.endswith(".json"):
                data, fmt = json.loads(raw.text), "json"
            else:
                (data, comments), fmt = parse_yaml(raw.text), "yaml"
        except (ValueError, YamlError) as exc:
            return make_items(source_id, raw.locator, self.kind, [("(parse_error)", raw.locator, f"配置解析失败: {exc}\n{raw.text[:800]}", {})])
        fname = raw.locator.rsplit("/", 1)[-1]
        if not isinstance(data, dict):
            data = {"root": data}
        sections = []
        for top, sub in data.items():
            pairs = flatten(sub, top)
            lines, kv = [], {}
            for kp, val in pairs:
                note = comments.get(kp, "")
                lines.append(f"{kp} = {fmt_value(val)}" + (f"  # {note}" if note else ""))
                kv[kp] = fmt_value(val)
            head = comments.get(top, "")
            text = f"配置 {fname} 的 {top} 段" + (f" ({head})" if head else "") + ":\n" + "\n".join(lines)
            sections.append((top, f"{fname}: {top}", text, {"kv": kv, "format": fmt, "comments": {k: v for k, v in comments.items() if k == top or k.startswith(top + ".") or k.startswith(top + "[")}}))
        return make_items(source_id, raw.locator, self.kind, sections)
