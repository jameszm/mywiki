# A/B 实验平台指南

推荐排序相关的实验统一在 A/B 实验平台 (ABHub) 上创建与分析。本文说明创建实验、分层与流量、指标与显著性、实验下线。

## 创建实验

实验通过 `configs/experiment.json` 描述, 关键字段: experiment_id、layer、traffic_ratio、buckets、metrics、min_days。
使用命令 `abctl create --config experiment.json` 创建实验, 创建后状态为 draft, 需要 owner 审批才能启动。

## 分层与流量

实验分层 (layer) 之间正交, 同一层内的实验互斥。排序模型实验固定使用 `ranking_layer`。
流量比例 traffic_ratio 建议从 0.05 (5%) 起步, 观察 1 天无异常后再放量到 0.2。
每个实验至少 2 个 bucket: control 与 treatment, 桶大小必须一致。

## 指标与显著性

核心指标为 stay_time、ctr、finish_rate, 护栏指标为 report_rate 与 latency_p99。
显著性判定: p-value < 0.05 且实验至少运行 7 天 (min_days=7), 覆盖完整的周内周期。
不要在实验运行不足 7 天时下结论, 周末流量结构与工作日差异很大。

## 实验下线

实验结束后使用 `abctl stop <experiment_id>` 下线。
全量 (ramp 到 100%) 属于模型上线, 需要走上线流程并通过架构评审。
