"""排序模型训练任务入口。

支持从 checkpoint 恢复 (--resume --checkpoint <path>), OOM 时自动把 batch_size 减半重试一次。
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

from ranking_config_loader import get_batch_size, get_learning_rate, load_ranking_config

log = logging.getLogger("training_job")


class MissingPartition(RuntimeError):
    """训练样本 hive 分区不存在 (上游 feature_daily_agg 未产出)。"""


class TrainingJob:
    """封装一次训练: 数据检查 -> 逐 epoch 训练 -> 保存 checkpoint。"""

    def __init__(self, cfg: dict[str, Any], checkpoint_dir: str = "/data/ckpt/ranking") -> None:
        self.cfg = cfg
        self.batch_size = get_batch_size(cfg)
        self.learning_rate = get_learning_rate(cfg)
        self.checkpoint_dir = Path(checkpoint_dir)
        self.step = 0

    def check_partitions(self, dates: list[str]) -> None:
        """检查 rec.training_samples 的日期分区, 缺失抛 MissingPartition。"""
        for d in dates:
            if not self._partition_exists(d):
                raise MissingPartition(f"rec.training_samples date={d} 分区缺失, 上游 feature_daily_agg 未产出")

    def train_epoch(self, epoch: int) -> float:
        """训练一个 epoch; 捕获 OOM 后把 batch_size 减半重试一次, 返回平均 loss。"""
        try:
            return self._run_epoch(epoch, self.batch_size)
        except MemoryError:
            log.warning("Worker killed (OOM) batch_size=%d, 减半重试", self.batch_size)
            self.batch_size //= 2
            return self._run_epoch(epoch, self.batch_size)

    def save_checkpoint(self) -> Path:
        """保存 checkpoint 到 checkpoint_dir/step-<step>.pt。"""
        path = self.checkpoint_dir / f"step-{self.step}.pt"
        log.info("checkpoint saved to %s", path)
        return path

    def resume(self, checkpoint: str) -> None:
        """从 checkpoint 恢复 step 与优化器状态。"""
        self.step = int(Path(checkpoint).stem.split("-")[-1])
        log.info("resumed from %s at step %d", checkpoint, self.step)

    def _run_epoch(self, epoch: int, batch_size: int) -> float:
        self.step += 1
        return 0.5

    @staticmethod
    def _partition_exists(date: str) -> bool:
        return True


def run_training(config_path: str, resume: bool = False, checkpoint: str | None = None, epochs: int = 3) -> float:
    """命令行入口: 加载配置, 可选从 checkpoint 恢复, 训练 epochs 轮, 返回最终 loss。"""
    cfg = load_ranking_config(config_path)
    job = TrainingJob(cfg)
    if resume and checkpoint:
        job.resume(checkpoint)
    loss = 0.0
    for epoch in range(epochs):
        loss = job.train_epoch(epoch)
        if loss != loss:  # nan
            raise RuntimeError("loss is nan, 请减小 learning_rate")
        job.save_checkpoint()
    return loss


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--checkpoint")
    args = parser.parse_args()
    run_training(args.config, args.resume, args.checkpoint)


if __name__ == "__main__":
    main()
