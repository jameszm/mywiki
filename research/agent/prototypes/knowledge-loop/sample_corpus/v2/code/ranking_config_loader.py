"""排序模型配置加载器。

读取 configs/ranking_model.yaml, 提供带默认值的访问函数; 配置缺失时使用模块内默认值。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_LEARNING_RATE = 0.0005
DEFAULT_WARMUP_STEPS = 1000
DEFAULT_BATCH_SIZE = 4096
DEFAULT_TIMEOUT_MS = 50


class ConfigError(RuntimeError):
    """配置文件缺失或字段非法。"""


def load_ranking_config(path: str | Path) -> dict[str, Any]:
    """加载配置 (json 或 yaml); yaml 由平台的 config-service 预先转换为 json。"""
    p = Path(path)
    if not p.exists():
        raise ConfigError(f"配置文件不存在: {p}")
    if p.suffix == ".json":
        return json.loads(p.read_text(encoding="utf-8"))
    raise ConfigError("yaml 配置需先经 config-service 转换为 json")


def get_path(cfg: dict[str, Any], dotted: str, default: Any = None) -> Any:
    """按 'ranking.model.learning_rate' 形式的点路径取值。"""
    cur: Any = cfg
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def get_learning_rate(cfg: dict[str, Any]) -> float:
    """学习率 ranking.model.learning_rate, 缺省 DEFAULT_LEARNING_RATE (0.0005, 2026-10 起减半)。"""
    lr = float(get_path(cfg, "ranking.model.learning_rate", DEFAULT_LEARNING_RATE))
    if lr <= 0 or lr > 0.1:
        raise ConfigError(f"learning_rate 超出合理范围 (0, 0.1]: {lr}")
    return lr


def get_batch_size(cfg: dict[str, Any]) -> int:
    """batch_size ranking.training.batch_size, 缺省 4096。"""
    return int(get_path(cfg, "ranking.training.batch_size", DEFAULT_BATCH_SIZE))


def get_serving_timeout_ms(cfg: dict[str, Any]) -> int:
    """特征取数/打分超时 ranking.serving.timeout_ms, 缺省 50ms。"""
    return int(get_path(cfg, "ranking.serving.timeout_ms", DEFAULT_TIMEOUT_MS))
