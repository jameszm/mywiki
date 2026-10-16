# 评分报告 v1 (对话回放后)

评分条目 101, 冲突 1, 缺口 4, 开放任务 17, 本次关闭任务 0

## 健康度 Top 5

| 条目 | 版本 | health | 分量 | 原因 |
|---|---|---|---|---|
| 在线取数 (docs/特征平台使用指南.md) | v1 | 0.88 | helpful=0.704, freshness=1.0, consistency=1.0, usage=1.0 | 曝光 7 次, 引用 3 次 (引用率 43%); 反馈份额 +0.41 (显式 +0.32) |
| OOM 处理 (docs/训练任务排障SOP.md) | v1 | 0.88 | helpful=0.86, freshness=1.0, consistency=1.0, usage=0.333 | 曝光 3 次, 引用 1 次 (引用率 33%); 反馈份额 +0.72 (显式 +0.48) |
| 示例 (docs/特征DSL说明.md) | v1 | 0.88 | helpful=0.86, freshness=1.0, consistency=1.0, usage=0.333 | 曝光 2 次, 引用 1 次 (引用率 50%); 反馈份额 +0.72 (显式 +0.48) |
| serving_client.ModelLoadError (code/serving_client.py) | v1 | 0.88 | helpful=0.86, freshness=1.0, consistency=1.0, usage=0.333 | 曝光 2 次, 引用 1 次 (引用率 50%); 反馈份额 +0.72 (显式 +0.48) |
| training_job.MissingPartition (code/training_job.py) | v1 | 0.88 | helpful=0.86, freshness=1.0, consistency=1.0, usage=0.333 | 曝光 5 次, 引用 1 次 (引用率 20%); 反馈份额 +0.72 (显式 +0.48) |

## 健康度 Bottom 5

| 条目 | 版本 | health | 分量 | 原因 |
|---|---|---|---|---|
| training_job.TrainingJob.save_checkpoint (code/training_job.py) | v1 | 0.68 | helpful=0.364, freshness=1.0, consistency=1.0, usage=0.333 | 曝光 3 次, 引用 1 次 (引用率 33%); 反馈份额 -0.27 (显式 -0.27) |
| training_job.TrainingJob.__init__ (code/training_job.py) | v1 | 0.68 | helpful=0.45, freshness=1.0, consistency=1.0, usage=0.0 | 曝光 7 次, 引用 0 次 (引用率 0%) |
| training_job.TrainingJob._partition_exists (code/training_job.py) | v1 | 0.68 | helpful=0.45, freshness=1.0, consistency=1.0, usage=0.0 | 曝光 4 次, 引用 0 次 (引用率 0%) |
| [INFO] checkpoint saved to <PATH> (logs/training_job.log) | v1 | 0.68 | helpful=0.45, freshness=1.0, consistency=1.0, usage=0.0 | 曝光 4 次, 引用 0 次 (引用率 0%) |
| ranking_config_loader.load_ranking_config (code/ranking_config_loader.py) | v1 | 0.68 | helpful=0.45, freshness=1.0, consistency=1.0, usage=0.0 | 曝光 4 次, 引用 0 次 (引用率 0%) |

## 冲突

- near_duplicate : docs/旧版模型发布流程(废弃).md ↔ docs/上线流程.md

## 缺口

- [gpu] 2 个对话 (负反馈 2): GPU 配额怎么申请 / 怎么申请更多 GPU 卡训练
- [kafka] 2 个对话 (负反馈 2): Kafka 消费组的分区数怎么配置 / kafka topic 分区数量在哪里配置
- [warmup] 2 个对话 (负反馈 2): warmup_steps 是什么配置 / 学习率预热步数 warmup 在哪里设置
- [connection] 1 个对话 (负反馈 1): RedisConnectionReset 是什么错误

## 策展队列 (按类型)

### deprecate (1)
- #4 p=0.50 条目自称废弃/deprecated 但仍被检索到 | items=['23dc7c605ab9@1'] | evidence={"turn_ids": ["t00012", "t00038"]}

### fill_gap (4)
- #14 p=0.80 知识缺口 [gpu]: 2 个对话没有可靠依据, 2 个负反馈 | items=[] | evidence={"identifiers": ["gpu"], "queries": ["GPU 配额怎么申请", "怎么申请更多 GPU 卡训练"], "turn_ids": ["t00017", "t00018"]}
- #15 p=0.80 知识缺口 [kafka]: 2 个对话没有可靠依据, 2 个负反馈 | items=[] | evidence={"identifiers": ["kafka", "topic"], "queries": ["Kafka 消费组的分区数怎么配置", "kafka topic 分区数量在哪里配置"], "turn_ids": ["t00005", "t00006"]}
- #16 p=0.80 知识缺口 [warmup]: 2 个对话没有可靠依据, 2 个负反馈 | items=[] | evidence={"identifiers": ["steps", "warmup", "warmup_steps"], "queries": ["warmup_steps 是什么配置", "学习率预热步数 warmup 在哪里设置"], "turn_ids": ["t00031", "t00032"]}
- #17 p=0.70 知识缺口 [connection]: 1 个对话没有可靠依据, 1 个负反馈 | items=[] | evidence={"identifiers": ["connection", "redis", "redisconnectionreset", "reset"], "queries": ["RedisConnectionReset 是什么错误"], "turn_ids": ["t00037"]}

### merge (1)
- #13 p=0.70 近重复内容 (Jaccard 0.615): docs/旧版模型发布流程(废弃).md ↔ docs/上线流程.md | items=['e0429f683710@1', 'f16222e1bb98@1'] | evidence={"jaccard": 0.615, "locators": ["docs/旧版模型发布流程(废弃).md", "docs/上线流程.md"]}

### promote_candidate (3)
- #1 p=0.80 用户纠错: 不对，学习率现在已经改成 0.0005 了，10 月起训练默认减半，文档还没更新 | items=['5a5c27aa925a', '70b16353e9b3', '8af1aed59fc0', 'bb8b7714050a'] | evidence={"candidate": {"kind": "lesson", "text": "不对，学习率现在已经改成 0.0005 了，10 月起训练默认减半，文档还没更新", "title": "经验: 学习率默认值是多少"}, "cited": ["70b16353e9b3@1", "bb8b7714050a@1", "8
- #2 p=0.80 用户纠错: 其实旧版邮件审批流程已经废弃了，应该按模型上线流程走工单和架构评审 | items=['23dc7c605ab9', 'a179a79cf571', 'e0429f683710', 'f16222e1bb98'] | evidence={"candidate": {"kind": "lesson", "text": "其实旧版邮件审批流程已经废弃了，应该按模型上线流程走工单和架构评审", "title": "经验: 旧版模型发布流程是怎样的"}, "cited": ["23dc7c605ab9@1", "a179a79cf571@1", "e0429
- #3 p=0.80 用户纠错: 不对，我问的是 Flink 实时任务的 checkpoint，不是训练任务的 checkpoint，知识库里没有 Fli | items=['1c4a48b39953', '5f358bce2018', 'fdf224ffac8f'] | evidence={"candidate": {"kind": "lesson", "text": "不对，我问的是 Flink 实时任务的 checkpoint，不是训练任务的 checkpoint，知识库里没有 Flink 的内容", "title": "经验: Flink 任务 checkpoint 失败怎么办"}, "cited

### verify (8)
- #6 p=0.60 引用后反馈偏负 (helpfulness -0.27), 需人工核对 | items=['5f358bce2018@1'] | evidence={"negative_turns": ["t00029"], "turn_ids": ["t00029"]}
- #8 p=0.60 引用后反馈偏负 (helpfulness -0.24), 需人工核对 | items=['a179a79cf571@1'] | evidence={"negative_turns": ["t00012"], "turn_ids": ["t00012"]}
- #9 p=0.54 被检索 7 次但从未被引用, 可能标题/内容与问题不匹配 | items=['a3499fdac14a@1'] | evidence={"exposures": 7}
- #5 p=0.48 被检索 4 次但从未被引用, 可能标题/内容与问题不匹配 | items=['5e7b58ff338c@1'] | evidence={"exposures": 4}
- #10 p=0.48 被检索 4 次但从未被引用, 可能标题/内容与问题不匹配 | items=['c54a44a2f709@1'] | evidence={"exposures": 4}
- #11 p=0.48 被检索 4 次但从未被引用, 可能标题/内容与问题不匹配 | items=['ec47ade7d52c@1'] | evidence={"exposures": 4}
- #7 p=0.46 被检索 3 次但从未被引用, 可能标题/内容与问题不匹配 | items=['7ad05a298991@1'] | evidence={"exposures": 3}
- #12 p=0.46 被检索 3 次但从未被引用, 可能标题/内容与问题不匹配 | items=['fe268022c43e@1'] | evidence={"exposures": 3}

