"""测试公用: 临时小语料。"""
from __future__ import annotations

from pathlib import Path

DOC_V1 = """# 指南

## 取数

特征取数超时默认 50ms, 超时抛出 FeatureFetchTimeout。

## 回滚

执行 deployctl rollback 回滚到上一个版本, 观察 10 分钟。
"""
DOC_V2 = DOC_V1.replace("观察 10 分钟", "观察 30 分钟并通知值班")
CODE = '''"""客户端模块。"""


class FeatureClient:
    """取数客户端。"""

    def fetch(self, keys, timeout_ms=50):
        """按 key 取特征, 超时抛 FeatureFetchTimeout。"""
        return {k: None for k in keys}


def helper(x):
    """辅助函数。"""
    return x * 2
'''
CONFIG_V1 = """# 排序配置
ranking:
  model:
    learning_rate: 0.001   # 学习率
  serving:
    timeout_ms: 50
"""
CONFIG_V2 = CONFIG_V1.replace("0.001", "0.0005")
LOG = """2026-10-01 08:00:00 ERROR FeatureFetchTimeout key=user:1 timeout_ms=50
2026-10-01 08:00:01 ERROR FeatureFetchTimeout key=user:2 timeout_ms=50
2026-10-01 08:00:02 WARN p99 latency 70ms exceeds 50ms threshold
"""


def write_corpus(root: Path, doc: str = DOC_V1, config: str = CONFIG_V1, with_code: bool = True, extra: dict[str, str] | None = None) -> Path:
    root = Path(root)
    for sub in ("docs", "code", "configs", "logs"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    (root / "docs" / "guide.md").write_text(doc, encoding="utf-8")
    code_path = root / "code" / "client.py"
    if with_code:
        code_path.write_text(CODE, encoding="utf-8")
    elif code_path.exists():
        code_path.unlink()
    (root / "configs" / "ranking.yaml").write_text(config, encoding="utf-8")
    (root / "logs" / "serving.log").write_text(LOG, encoding="utf-8")
    for rel, text in (extra or {}).items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")
    return root
