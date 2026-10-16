# 评分报告 v2 (增量同步后)

评分条目 115, 冲突 1, 缺口 4, 开放任务 36, 本次关闭任务 3

## 健康度 Top 5

| 条目 | 版本 | health | 分量 | 原因 |
|---|---|---|---|---|
| 在线取数 (docs/特征平台使用指南.md) | v1 | 0.88 | helpful=0.704, freshness=1.0, consistency=1.0, usage=1.0 | 曝光 7 次, 引用 3 次 (引用率 43%); 反馈份额 +0.41 (显式 +0.32) |
| OOM 处理 (docs/训练任务排障SOP.md) | v1 | 0.88 | helpful=0.86, freshness=1.0, consistency=1.0, usage=0.333 | 曝光 3 次, 引用 1 次 (引用率 33%); 反馈份额 +0.72 (显式 +0.48) |
| serving_client.ModelLoadError (code/serving_client.py) | v1 | 0.88 | helpful=0.86, freshness=1.0, consistency=1.0, usage=0.333 | 曝光 2 次, 引用 1 次 (引用率 50%); 反馈份额 +0.72 (显式 +0.48) |
| training_job.MissingPartition (code/training_job.py) | v1 | 0.88 | helpful=0.86, freshness=1.0, consistency=1.0, usage=0.333 | 曝光 5 次, 引用 1 次 (引用率 20%); 反馈份额 +0.72 (显式 +0.48) |
| 排序服务 Runbook (docs/排序服务runbook.md) | v1 | 0.88 | helpful=0.86, freshness=1.0, consistency=1.0, usage=0.333 | 曝光 3 次, 引用 1 次 (引用率 33%); 反馈份额 +0.72 (显式 +0.48) |

## 健康度 Bottom 5

| 条目 | 版本 | health | 分量 | 原因 |
|---|---|---|---|---|
| 邮件审批 (docs/旧版模型发布流程(废弃).md) | v1 | 0.39 | helpful=0.38, freshness=0.0, consistency=1.0, usage=0.333 | 曝光 3 次, 引用 1 次 (引用率 33%); 反馈份额 -0.24 (显式 -0.24); 陈旧: tombstoned |
| 命名规范 (docs/特征DSL说明.md) | v1 | 0.40 | helpful=0.5, freshness=0.0, consistency=1.0, usage=0.0 | 曝光 2 次, 引用 0 次 (引用率 0%); 陈旧: superseded |
| ranking_model.yaml: features (configs/ranking_model.yaml) | v1 | 0.40 | helpful=0.5, freshness=0.0, consistency=1.0, usage=0.0 | 曝光 1 次, 引用 0 次 (引用率 0%); 陈旧: superseded |
| ranking_config_loader 模块 (code/ranking_config_loader.py) | v1 | 0.40 | helpful=0.42, freshness=0.0, consistency=1.0, usage=0.333 | 曝光 5 次, 引用 1 次 (引用率 20%); 反馈份额 -0.16 (显式 -0.16); 陈旧: superseded |
| 旧版模型发布流程 (废弃) (docs/旧版模型发布流程(废弃).md) | v1 | 0.40 | helpful=0.34, freshness=0.0, consistency=1.0, usage=0.667 | 曝光 3 次, 引用 2 次 (引用率 67%); 反馈份额 -0.32 (显式 -0.32); 陈旧: tombstoned |

## 冲突

- value_mismatch ranking.model.learning_rate: 文档 docs/训练任务排障SOP.md 写 0.001, 配置 configs/ranking_model.yaml 为 0.0005

## 缺口

- [gpu] 2 个对话 (负反馈 2): GPU 配额怎么申请 / 怎么申请更多 GPU 卡训练
- [kafka] 2 个对话 (负反馈 2): Kafka 消费组的分区数怎么配置 / kafka topic 分区数量在哪里配置
- [warmup] 2 个对话 (负反馈 2): warmup_steps 是什么配置 / 学习率预热步数 warmup 在哪里设置
- [connection] 1 个对话 (负反馈 1): RedisConnectionReset 是什么错误

## 策展队列 (按类型)

### fill_gap (4)
- #14 p=0.80 知识缺口 [gpu]: 2 个对话没有可靠依据, 2 个负反馈 | items=[] | evidence={"identifiers": ["gpu"], "queries": ["GPU 配额怎么申请", "怎么申请更多 GPU 卡训练"], "turn_ids": ["t00017", "t00018"]}
- #15 p=0.80 知识缺口 [kafka]: 2 个对话没有可靠依据, 2 个负反馈 | items=[] | evidence={"identifiers": ["kafka", "topic"], "queries": ["Kafka 消费组的分区数怎么配置", "kafka topic 分区数量在哪里配置"], "turn_ids": ["t00005", "t00006"]}
- #16 p=0.80 知识缺口 [warmup]: 2 个对话没有可靠依据, 2 个负反馈 | items=[] | evidence={"identifiers": ["steps", "warmup", "warmup_steps"], "queries": ["warmup_steps 是什么配置", "学习率预热步数 warmup 在哪里设置"], "turn_ids": ["t00031", "t00032"]}
- #17 p=0.70 知识缺口 [connection]: 1 个对话没有可靠依据, 1 个负反馈 | items=[] | evidence={"identifiers": ["connection", "redis", "redisconnectionreset", "reset"], "queries": ["RedisConnectionReset 是什么错误"], "turn_ids": ["t00037"]}

### promote_candidate (3)
- #1 p=0.80 用户纠错: 不对，学习率现在已经改成 0.0005 了，10 月起训练默认减半，文档还没更新 | items=['5a5c27aa925a', '70b16353e9b3', '8af1aed59fc0', 'bb8b7714050a'] | evidence={"candidate": {"kind": "lesson", "text": "不对，学习率现在已经改成 0.0005 了，10 月起训练默认减半，文档还没更新", "title": "经验: 学习率默认值是多少"}, "cited": ["70b16353e9b3@1", "bb8b7714050a@1", "8
- #2 p=0.80 用户纠错: 其实旧版邮件审批流程已经废弃了，应该按模型上线流程走工单和架构评审 | items=['23dc7c605ab9', 'a179a79cf571', 'e0429f683710', 'f16222e1bb98'] | evidence={"candidate": {"kind": "lesson", "text": "其实旧版邮件审批流程已经废弃了，应该按模型上线流程走工单和架构评审", "title": "经验: 旧版模型发布流程是怎样的"}, "cited": ["23dc7c605ab9@1", "a179a79cf571@1", "e0429
- #3 p=0.80 用户纠错: 不对，我问的是 Flink 实时任务的 checkpoint，不是训练任务的 checkpoint，知识库里没有 Fli | items=['1c4a48b39953', '5f358bce2018', 'fdf224ffac8f'] | evidence={"candidate": {"kind": "lesson", "text": "不对，我问的是 Flink 实时任务的 checkpoint，不是训练任务的 checkpoint，知识库里没有 Flink 的内容", "title": "经验: Flink 任务 checkpoint 失败怎么办"}, "cited

### update (1)
- #39 p=0.90 取值冲突 ranking.model.learning_rate: 文档 docs/训练任务排障SOP.md 写 0.001, 配置 configs/ranking_model.yaml 为 0.0005 | items=['bb8b7714050a@1'] | evidence={"keys": ["bb8b7714050a@1", "5a5c27aa925a@2"], "path": "ranking.model.learning_rate"}

### verify (28)
- #6 p=0.60 引用后反馈偏负 (helpfulness -0.27), 需人工核对 | items=['5f358bce2018@1'] | evidence={"negative_turns": ["t00029"], "turn_ids": ["t00029"]}
- #28 p=0.60 来源文件在上次核验后已变化, 该章节未变但需复核上下文是否仍一致 | items=['61fb48f6ec2a@1'] | evidence={"last_verified_at": "2026-10-16T09:42:28.463132+00:00", "locator": "code/ranking_config_loader.py"}
- #9 p=0.54 被检索 7 次但从未被引用, 可能标题/内容与问题不匹配 | items=['a3499fdac14a@1'] | evidence={"exposures": 7}
- #30 p=0.50 来源文件在上次核验后已变化, 该章节未变但需复核上下文是否仍一致 | items=['8732966d674b@1'] | evidence={"last_verified_at": "2026-10-16T09:42:28.463132+00:00", "locator": "docs/特征DSL说明.md"}
- #37 p=0.50 来源文件在上次核验后已变化, 该章节未变但需复核上下文是否仍一致 | items=['fd78b0d4f27c@1'] | evidence={"last_verified_at": "2026-10-16T09:42:28.463132+00:00", "locator": "docs/特征DSL说明.md"}
- #5 p=0.48 被检索 4 次但从未被引用, 可能标题/内容与问题不匹配 | items=['5e7b58ff338c@1'] | evidence={"exposures": 4}
- #10 p=0.48 被检索 4 次但从未被引用, 可能标题/内容与问题不匹配 | items=['c54a44a2f709@1'] | evidence={"exposures": 4}
- #11 p=0.48 被检索 4 次但从未被引用, 可能标题/内容与问题不匹配 | items=['ec47ade7d52c@1'] | evidence={"exposures": 4}
- #7 p=0.46 被检索 3 次但从未被引用, 可能标题/内容与问题不匹配 | items=['7ad05a298991@1'] | evidence={"exposures": 3}
- #12 p=0.46 被检索 3 次但从未被引用, 可能标题/内容与问题不匹配 | items=['fe268022c43e@1'] | evidence={"exposures": 3}
- #19 p=0.40 来源文件在上次核验后已变化, 该章节未变但需复核上下文是否仍一致 | items=['34780b8cd181@1'] | evidence={"last_verified_at": "2026-10-16T09:42:28.463132+00:00", "locator": "logs/serving_errors.log"}
- #22 p=0.40 来源文件在上次核验后已变化, 该章节未变但需复核上下文是否仍一致 | items=['4c0c7cbd3f50@1'] | evidence={"last_verified_at": "2026-10-16T09:42:28.463132+00:00", "locator": "logs/serving_errors.log"}
- #23 p=0.40 来源文件在上次核验后已变化, 该章节未变但需复核上下文是否仍一致 | items=['4e91515119ed@1'] | evidence={"last_verified_at": "2026-10-16T09:42:28.463132+00:00", "locator": "logs/serving_errors.log"}
- #26 p=0.40 来源文件在上次核验后已变化, 该章节未变但需复核上下文是否仍一致 | items=['542d74366de2@1'] | evidence={"last_verified_at": "2026-10-16T09:42:28.463132+00:00", "locator": "code/feature_dsl.py"}
- #27 p=0.40 来源文件在上次核验后已变化, 该章节未变但需复核上下文是否仍一致 | items=['5b7c34784996@1'] | evidence={"last_verified_at": "2026-10-16T09:42:28.463132+00:00", "locator": "logs/serving_errors.log"}
- #32 p=0.40 来源文件在上次核验后已变化, 该章节未变但需复核上下文是否仍一致 | items=['989fa2631324@1'] | evidence={"last_verified_at": "2026-10-16T09:42:28.463132+00:00", "locator": "code/ranking_config_loader.py"}
- #33 p=0.40 来源文件在上次核验后已变化, 该章节未变但需复核上下文是否仍一致 | items=['a7b8f9a39f5f@1'] | evidence={"last_verified_at": "2026-10-16T09:42:28.463132+00:00", "locator": "code/feature_dsl.py"}
- #34 p=0.40 来源文件在上次核验后已变化, 该章节未变但需复核上下文是否仍一致 | items=['b5bbc17daf52@1'] | evidence={"last_verified_at": "2026-10-16T09:42:28.463132+00:00", "locator": "code/feature_dsl.py"}
- #35 p=0.40 来源文件在上次核验后已变化, 该章节未变但需复核上下文是否仍一致 | items=['e6391e4c3454@1'] | evidence={"last_verified_at": "2026-10-16T09:42:28.463132+00:00", "locator": "logs/serving_errors.log"}
- #18 p=0.30 来源文件在上次核验后已变化, 该章节未变但需复核上下文是否仍一致 | items=['2550fdfb93cc@1'] | evidence={"last_verified_at": "2026-10-16T09:42:28.463132+00:00", "locator": "docs/特征DSL说明.md"}
- #20 p=0.30 来源文件在上次核验后已变化, 该章节未变但需复核上下文是否仍一致 | items=['36576196b7e3@1'] | evidence={"last_verified_at": "2026-10-16T09:42:28.463132+00:00", "locator": "configs/feature_schema.yaml"}
- #21 p=0.30 来源文件在上次核验后已变化, 该章节未变但需复核上下文是否仍一致 | items=['43a14b4bb980@1'] | evidence={"last_verified_at": "2026-10-16T09:42:28.463132+00:00", "locator": "docs/特征DSL说明.md"}
- #24 p=0.30 来源文件在上次核验后已变化, 该章节未变但需复核上下文是否仍一致 | items=['51e425e8b8eb@1'] | evidence={"last_verified_at": "2026-10-16T09:42:28.463132+00:00", "locator": "code/feature_dsl.py"}
- #25 p=0.30 来源文件在上次核验后已变化, 该章节未变但需复核上下文是否仍一致 | items=['5214891d2bf2@1'] | evidence={"last_verified_at": "2026-10-16T09:42:28.463132+00:00", "locator": "code/ranking_config_loader.py"}
- #29 p=0.30 来源文件在上次核验后已变化, 该章节未变但需复核上下文是否仍一致 | items=['67dbfa3ffb82@1'] | evidence={"last_verified_at": "2026-10-16T09:42:28.463132+00:00", "locator": "code/feature_dsl.py"}
- #31 p=0.30 来源文件在上次核验后已变化, 该章节未变但需复核上下文是否仍一致 | items=['91dc2207713b@1'] | evidence={"last_verified_at": "2026-10-16T09:42:28.463132+00:00", "locator": "code/ranking_config_loader.py"}
- #36 p=0.30 来源文件在上次核验后已变化, 该章节未变但需复核上下文是否仍一致 | items=['ec47ade7d52c@1'] | evidence={"last_verified_at": "2026-10-16T09:42:28.463132+00:00", "locator": "code/ranking_config_loader.py"}
- #38 p=0.30 来源文件在上次核验后已变化, 该章节未变但需复核上下文是否仍一致 | items=['fe268022c43e@1'] | evidence={"last_verified_at": "2026-10-16T09:42:28.463132+00:00", "locator": "code/feature_dsl.py"}

