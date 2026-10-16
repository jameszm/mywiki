"""在线服务客户端: 特征取数 (FeatureClient) 与排序打分 (RankingClient)。"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


class FeatureFetchTimeout(TimeoutError):
    """特征取数超过 timeout_ms 抛出; 调用方应重试 1 次后降级。"""


class ModelLoadError(RuntimeError):
    """模型文件 checksum 校验失败或文件缺失。"""


@dataclass
class ScoreRequest:
    user_id: str
    item_ids: list[str]
    context: dict[str, Any] = field(default_factory=dict)


class FeatureClient:
    """FeatureServer 客户端。"""

    def __init__(self, endpoint: str, timeout_ms: int = 50, max_retries: int = 1) -> None:
        self.endpoint = endpoint
        self.timeout_ms = timeout_ms
        self.max_retries = max_retries

    def fetch(self, keys: list[str], features: list[str], timeout_ms: int | None = None) -> dict[str, dict[str, Any]]:
        """按 key 批量取特征; 超过 timeout_ms (默认 50ms) 抛 FeatureFetchTimeout, 内部重试 max_retries 次。"""
        timeout = timeout_ms or self.timeout_ms
        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                return self._rpc(keys, features, timeout)
            except FeatureFetchTimeout as exc:
                last_exc = exc
                time.sleep(0.001 * attempt)
        raise FeatureFetchTimeout(f"fetch {len(keys)} keys timed out after {self.max_retries + 1} attempts: {last_exc}")

    def _rpc(self, keys: list[str], features: list[str], timeout_ms: int) -> dict[str, dict[str, Any]]:
        started = time.monotonic()
        result = {k: {f: None for f in features} for k in keys}
        if (time.monotonic() - started) * 1000 > timeout_ms:
            raise FeatureFetchTimeout(f"timeout_ms={timeout_ms}")
        return result


class RankingClient:
    """排序服务客户端; degrade_mode 下使用默认特征值打分。"""

    def __init__(self, feature_client: FeatureClient, model_path: str, degrade_mode: bool = False) -> None:
        self.feature_client = feature_client
        self.model_path = model_path
        self.degrade_mode = degrade_mode
        self._model = None

    def load_model(self, expected_checksum: str) -> None:
        """加载模型并校验 checksum, 不匹配抛 ModelLoadError。"""
        actual = self._checksum(self.model_path)
        if actual != expected_checksum:
            raise ModelLoadError(f"checksum mismatch file={self.model_path} expected={expected_checksum} actual={actual}")
        self._model = object()

    def score(self, request: ScoreRequest) -> dict[str, float]:
        """对 request.item_ids 打分; 特征取数超时且 degrade_mode 为 true 时用默认特征值。"""
        try:
            feats = self.feature_client.fetch(request.item_ids, ["item_ctr_1d"])
        except FeatureFetchTimeout:
            if not self.degrade_mode:
                raise
            feats = {i: {"item_ctr_1d": -1} for i in request.item_ids}
        return {i: float(feats[i].get("item_ctr_1d") or 0.0) for i in request.item_ids}

    @staticmethod
    def _checksum(path: str) -> str:
        return "deadbeef"
