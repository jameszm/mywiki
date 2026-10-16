# 训练任务排障 SOP

排序模型训练任务 (`training_job.py`) 的排障手册。先按失败分类定位, 再按对应小节处理。

## 任务失败分类

训练任务失败分为四类: OOM、数据缺失 (MissingPartition)、参数错误 (loss 发散) 和平台故障。
排查顺序: 先看任务日志最后 200 行的 ERROR, 再看监控面板的内存与 loss 曲线。

## OOM 处理

日志出现 `CUDA out of memory` 或 `Worker killed (OOM)` 时为显存/内存不足。
处理: 减小 `ranking.training.batch_size` (默认 4096, 建议减半到 2048) 或开启梯度累积; 训练脚本会在 OOM 后自动把 batch_size 减半重试一次。

## Loss 发散

日志出现 `loss is nan` 表示学习率过大或特征未归一化。
学习率 `ranking.model.learning_rate` 默认 0.001, 发散时先减半重试; 同时检查新加特征是否做了归一化。

## 数据缺失

日志出现 `MissingPartition` 时, 检查 hive 表 `rec.training_samples` 对应日期的分区是否生成。
分区由上游任务 `feature_daily_agg` 产出, 通常延迟 2 小时内会补齐; 超过 2 小时联系特征平台值班。

## 任务重试

从 checkpoint 恢复: `python training_job.py --config ranking_model.yaml --resume --checkpoint <path>`。
checkpoint 目录由 `ranking.training.checkpoint_dir` 指定, 默认 `/data/ckpt/ranking`。
