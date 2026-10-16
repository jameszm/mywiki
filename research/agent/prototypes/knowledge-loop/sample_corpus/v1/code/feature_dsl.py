"""特征 DSL 编译器。

把 `feature <name> = <expr> window <window>` 一行声明编译为 FeatureSpec, 并校验命名规范。
"""
from __future__ import annotations

import re
from dataclasses import dataclass

EXAMPLE = "feature user_click_cnt_7d = count(click) window 7d"
NAME_RE = re.compile(r"^(user|item|author)_[a-z]+_[a-z]+_(\d+[hd])$")
LINE_RE = re.compile(r"^feature\s+(?P<name>\w+)\s*=\s*(?P<expr>.+?)\s+window\s+(?P<window>\d+[hd])\s*$")
BUILTINS = ("count", "sum", "avg", "last", "decay", "bucketize")


class FeatureDSLError(ValueError):
    """DSL 语法或命名规范错误。"""


@dataclass(frozen=True)
class FeatureSpec:
    """编译后的特征规格: 名称、表达式、窗口与推断出的数据类型。"""

    name: str
    expr: str
    window: str
    dtype: str = "float"


def validate_name(name: str) -> None:
    """校验命名规范 <实体>_<统计量>_<窗口>, 例如 user_click_cnt_7d。"""
    if not NAME_RE.match(name):
        raise FeatureDSLError(f"特征名不符合命名规范 <实体>_<统计量>_<窗口>: {name}")


def infer_dtype(expr: str) -> str:
    """count 类表达式为 int, 其余为 float。"""
    return "int" if expr.startswith("count(") else "float"


def parse_feature(line: str) -> FeatureSpec:
    """只做语法解析, 不校验命名。"""
    m = LINE_RE.match(line.strip())
    if not m:
        raise FeatureDSLError(f"语法错误, 期望 'feature <name> = <expr> window <w>': {line}")
    func = m.group("expr").split("(", 1)[0]
    if func not in BUILTINS:
        raise FeatureDSLError(f"未知内置函数: {func}")
    return FeatureSpec(m.group("name"), m.group("expr"), m.group("window"), infer_dtype(m.group("expr")))


def compile_feature(line: str) -> FeatureSpec:
    """解析 + 命名校验 + 窗口一致性校验, 返回可注册的 FeatureSpec。"""
    spec = parse_feature(line)
    validate_name(spec.name)
    if not spec.name.endswith("_" + spec.window):
        raise FeatureDSLError(f"特征名窗口后缀 {spec.name} 与 window {spec.window} 不一致")
    return spec


def compile_file(path: str) -> list[FeatureSpec]:
    """编译一个 DSL 文件, 忽略空行与 # 注释。"""
    specs = []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if line and not line.startswith("#"):
                specs.append(compile_feature(line))
    return specs
