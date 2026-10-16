# 排序服务 Runbook

排序服务 (ranking-serving, PSM `rec.ranking.serving`) 的值班手册, 覆盖告警处理、常见错误、回滚与扩容。

## 服务概览

排序服务从特征平台取特征, 加载 `configs/ranking_model.yaml` 中配置的模型 (model.name、model.version) 进行打分。
服务入口为 `serving_client.RankingClient.score(request)`, 打分超时 `ranking.serving.timeout_ms` 默认 50ms。

## 告警处理

`FeatureFetchTimeout` 告警: 特征服务 p99 延迟超过 50ms 持续 5 分钟触发。
处理步骤: 1) 检查 FeatureServer 负载与 QPS; 2) 若 FeatureServer 过载, 先扩容; 3) 紧急情况下开启降级开关
`ranking.serving.degrade_mode = true`, 排序服务使用默认特征值继续打分。

## 常见错误与处理

- `ModelLoadError`: 模型加载失败, 通常是模型文件 checksum 校验不通过 (checksum mismatch), 检查模型文件是否完整上传, 必要时回滚到上一个版本。
- `ScoreOverflow`: 打分溢出, 多由特征值范围异常引起 (例如 item_ctr_1d 大于 1), 检查上游特征值范围, 临时可将异常特征置为缺失。
- `p99 latency exceeds` 告警: 打分 p99 延迟超过 50ms, 先看特征取数是否变慢, 再看模型是否变大。

## 回滚步骤

1. 在发布平台选择上一个稳定版本 (model.version 减一)。
2. 执行 `deployctl rollback rec.ranking.serving --to <version>`。
3. 观察 10 分钟核心指标 (ctr、stay_time、latency_p99) 恢复后关闭告警。

## 扩容

排序服务容量以 `ranking.serving.max_qps` 为准 (默认 20000), 峰值 QPS 超过 80% 容量时需要提前扩容。
扩容通过发布平台调整实例数, 扩容后需要预热 5 分钟再接流量。
