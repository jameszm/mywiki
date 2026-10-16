# Demo 输出

```
知识闭环原型演示 (LLM 后端: heuristic)

== 步骤 1: 初始化数据库 ======================================================
   outputs/kloop.db 已创建, 表: citations, curation_queue, eval_runs, feedback, item_scores, items, retrievals, source_files, sources, sqlite_sequence, sync_runs, turns

== 步骤 2: 同步语料 v1 (全量首次) ==============================================
   文件: 扫描 16 / 新增 16 / 变更 0 / 未变跳过 0 / 删除 0; 条目: 新增 101 / 更新(新版本) 0 / 未变 0 / 墓碑 0; 重建索引条目 101 (语料版本 v1)
   条目类型分布: code=40, config=12, doc=38, log=11

== 步骤 3: 黄金集评测 (expects_version=1) ===================================
   条目 26, 弃答 3, 平均步数 1.73
       recall@5 |    recall@10 |          mrr |       ndcg@5 |      ndcg@10 | keyword_coverage | citation_precision | groundedness | abstain_ok_rate
          0.929 |        0.949 |        0.949 |        0.885 |        0.894 |        0.962 |        0.748 |        0.885 |        1.000
   报告: outputs/eval_v1.json, outputs/eval_v1.md

== 步骤 4: 回放模拟对话 (search -> answer -> 记录对话与反馈) ========================
   对话 38 轮, 用户 8 人, 带引用 31 轮 (引用率 82%), 弃答 7, 反馈事件 50 (改写 3, 纠错 3)
   每轮都记录了检索条目 (id@version, rank, 各信号分数) 与引用条目: retrievals=330, citations=131

== 步骤 5: 基于日志评分 / 缺口 / 策展队列 ==========================================
   评分条目 101 (含被替代/墓碑版本), 冲突 1, 缺口簇 4, 开放任务 17, 本次关闭 0
   健康度 Top 5:
     0.88 在线取数 (docs/特征平台使用指南.md v1) :: 曝光 7 次, 引用 3 次 (引用率 43%); 反馈份额 +0.41 (显式 +0.32)
     0.88 OOM 处理 (docs/训练任务排障SOP.md v1) :: 曝光 3 次, 引用 1 次 (引用率 33%); 反馈份额 +0.72 (显式 +0.48)
     0.88 示例 (docs/特征DSL说明.md v1) :: 曝光 2 次, 引用 1 次 (引用率 50%); 反馈份额 +0.72 (显式 +0.48)
     0.88 serving_client.ModelLoadError (code/serving_client.py v1) :: 曝光 2 次, 引用 1 次 (引用率 50%); 反馈份额 +0.72 (显式 +0.48)
     0.88 training_job.MissingPartition (code/training_job.py v1) :: 曝光 5 次, 引用 1 次 (引用率 20%); 反馈份额 +0.72 (显式 +0.48)
   健康度 Bottom 5:
     0.68 training_job.TrainingJob.save_checkpoint (code/training_job.py v1) :: 曝光 3 次, 引用 1 次 (引用率 33%); 反馈份额 -0.27 (显式 -0.27)
     0.68 training_job.TrainingJob.__init__ (code/training_job.py v1) :: 曝光 7 次, 引用 0 次 (引用率 0%)
     0.68 training_job.TrainingJob._partition_exists (code/training_job.py v1) :: 曝光 4 次, 引用 0 次 (引用率 0%)
     0.68 [INFO] checkpoint saved to <PATH> (logs/training_job.log v1) :: 曝光 4 次, 引用 0 次 (引用率 0%)
     0.68 ranking_config_loader.load_ranking_config (code/ranking_config_loader.py v1) :: 曝光 4 次, 引用 0 次 (引用率 0%)
   缺口簇:
     [gpu] 2 个对话, 负反馈 2: GPU 配额怎么申请 / 怎么申请更多 GPU 卡训练
     [kafka] 2 个对话, 负反馈 2: Kafka 消费组的分区数怎么配置 / kafka topic 分区数量在哪里配置
     [warmup] 2 个对话, 负反馈 2: warmup_steps 是什么配置 / 学习率预热步数 warmup 在哪里设置
     [connection] 1 个对话, 负反馈 1: RedisConnectionReset 是什么错误
   策展队列 (按类型): deprecate=1, fill_gap=4, merge=1, promote_candidate=3, verify=8
     [deprecate] #4 p=0.50 条目自称废弃/deprecated 但仍被检索到
     [fill_gap] #14 p=0.80 知识缺口 [gpu]: 2 个对话没有可靠依据, 2 个负反馈
     [fill_gap] #15 p=0.80 知识缺口 [kafka]: 2 个对话没有可靠依据, 2 个负反馈
     [fill_gap] #16 p=0.80 知识缺口 [warmup]: 2 个对话没有可靠依据, 2 个负反馈
     [merge] #13 p=0.70 近重复内容 (Jaccard 0.615): docs/旧版模型发布流程(废弃).md ↔ docs/上线流程.md
     [promote_candidate] #1 p=0.80 用户纠错: 不对，学习率现在已经改成 0.0005 了，10 月起训练默认减半，文档还没更新
     [promote_candidate] #2 p=0.80 用户纠错: 其实旧版邮件审批流程已经废弃了，应该按模型上线流程走工单和架构评审
     [promote_candidate] #3 p=0.80 用户纠错: 不对，我问的是 Flink 实时任务的 checkpoint，不是训练任务的 checkpoint，知识库里没有 Fli
     [verify] #6 p=0.60 引用后反馈偏负 (helpfulness -0.27), 需人工核对
     [verify] #8 p=0.60 引用后反馈偏负 (helpfulness -0.24), 需人工核对
     [verify] #9 p=0.54 被检索 7 次但从未被引用, 可能标题/内容与问题不匹配

== 步骤 6: 同步语料 v2 (增量) ================================================
   文件: 扫描 16 / 新增 1 / 变更 6 / 未变跳过 9 / 删除 1; 条目: 新增 5 / 更新(新版本) 9 / 未变 89 / 墓碑 3; 重建索引条目 26 (语料版本 v2)
   只重建了受影响条目: 新增 5 + 更新 9 + 墓碑 3 = 26; 未变 89 条未触碰 (索引大小 103 = 当前有效条目 103)
   变更文件: code/feature_dsl.py, code/ranking_config_loader.py, configs/feature_schema.yaml, configs/ranking_model.yaml, docs/特征DSL说明.md, logs/serving_errors.log; 删除文件: docs/旧版模型发布流程(废弃).md
   版本链 5ea52db78cf1 (feature_dsl 模块): v1 valid_to=2026-10-16T09:42:28 superseded_by=5ea52db78cf1@2 status=superseded -> v2 当前有效
   版本链 e52206e1b8f8 (feature_dsl.validate_name): v1 valid_to=2026-10-16T09:42:28 superseded_by=e52206e1b8f8@2 status=superseded -> v2 当前有效
   版本链 8af1aed59fc0 (ranking_config_loader 模块): v1 valid_to=2026-10-16T09:42:28 superseded_by=8af1aed59fc0@2 status=superseded -> v2 当前有效
   墓碑示例 23dc7c605ab9@1 (旧版模型发布流程 (废弃), docs/旧版模型发布流程(废弃).md): status=deleted valid_to=2026-10-16T09:42:28

== 步骤 7: 新鲜度评测 (expects_version=2) ===================================
   条目 7, freshness_pass_rate=1.00, 关键词覆盖 1.00
   ✓ g27 学习率默认值是多少: top命中为当前版本=True, 未引用被替代版本=True, 关键词覆盖=1.00
       答案: - 读取 configs/ranking_model.yaml, 提供带默认值的访问函数; [K-8af1aed59fc0]
   ✓ g28 7 天点击次数特征现在叫什么名字: top命中为当前版本=True, 未引用被替代版本=True, 关键词覆盖=1.00
       答案: - 用户 7 天点击次数特征定义为: `feature user_click_count_7d = count(click) window 7d` (原名 user_click_cnt_7d 已重命名)。 [K-3d81
   ✓ g29 灰度发布分几个阶段，什么时候自动回滚: top命中为当前版本=True, 未引用被替代版本=True, 关键词覆盖=1.00
       答案: - 每个阶段自动比较灰度实例与基线实例的 error_rate 与 latency_p99: [K-fd246f3f6c49]
   ✓ g30 RedisConnectionReset 错误出现过多少次: top命中为当前版本=True, 未引用被替代版本=True, 关键词覆盖=1.00
       答案: - 日志模板 [ERROR]: RedisConnectionReset host=<IP> retry=<NUM> pool=feature-cache [K-21b5e1eab18a]
   ✓ g31 warmup_steps 是什么配置: top命中为当前版本=True, 未引用被替代版本=True, 关键词覆盖=1.00
       答案: - 配置 ranking_model.yaml 的 ranking 段 (排序模型配置 (ranking-serving 与 training_job 共用)): [K-5a5c27aa925a]
   ✓ g32 模型发布流程现在应该看哪个文档: top命中为当前版本=True, 未引用被替代版本=True, 关键词覆盖=1.00
       答案: - 2026-10 起排序服务的全量发布改为分阶段灰度 (canary), 由 `deployctl canary` 控制, 替代一次性全量。 [K-fc8ca10a1ad4]
   ✓ g33 _cnt_ 后缀还能用吗: top命中为当前版本=True, 未引用被替代版本=True, 关键词覆盖=1.00
       答案: - `_cnt_` 已废弃, 统一使用 `_count_`。 [K-e52206e1b8f8]

== 步骤 8: v2 全量评测 + 与步骤 3 的回归对比 =======================================
   条目 29 (含 7 条新鲜度条目)
       recall@5 |    recall@10 |          mrr |       ndcg@5 |      ndcg@10 | keyword_coverage | citation_precision | groundedness | abstain_ok_rate
          0.960 |        0.971 |        0.954 |        0.905 |        0.910 |        0.966 |        0.731 |        0.931 |        1.000
   回归对比 (共同 query 22): recall@5 +0.030, recall@10 +0.023, mrr +0.005, ndcg@5 +0.019, ndcg@10 +0.016, keyword_coverage +0.004, citation_precision -0.018, groundedness +0.046
   回归 0 条, 改进 0 条; 逐条非零差值:
     g04 训练任务 OOM 怎么办: recall@5 +0.50, ndcg@5 +0.26, ndcg@10 +0.05
     g06 loss 变成 nan 怎么处理: ndcg@5 -0.08, ndcg@10 -0.08, citation_precision +0.25
     g11 模型上线需要哪些审批: citation_precision +0.15
     g14 FeatureClient.fetch 的超时参: citation_precision -0.25

== 步骤 9: 再次评分: 陈旧/冲突标记的变化 + 黄金集候选挖掘 ==================================
   陈旧标记 v1 -> v2: {} -> {'tombstoned': 3, 'file_changed_since_verified': 21, 'superseded': 9}
   冲突已清除: near_duplicate  docs/旧版模型发布流程(废弃).md ↔ docs/上线流程.md
   冲突新出现: value_mismatch ranking.model.learning_rate 文档 docs/训练任务排障SOP.md 写 0.001, 配置 configs/ranking_model.yaml 为 0.0005
   来源文件变更后未复核的条目 21 条 (低优先级 verify 任务), 例如: 内置函数; [ERROR] ModelLoadError checksum mismatch file=<PATH> expected=<HEX> actual=<HEX>; feature_schema.yaml: defaults; 语法概览
   被替代版本 (superseded) 9 条, 墓碑 3 条 (它们仍在日志中有曝光/引用记录, 健康度降至最低)
   任务变化: 本次关闭 3 个不再成立的任务; 开放任务 fill_gap=4, promote_candidate=3, update=1, verify=28
   健康度 Bottom 5 (被替代/墓碑版本沉底):
     0.39 邮件审批 (docs/旧版模型发布流程(废弃).md v1) :: 曝光 3 次, 引用 1 次 (引用率 33%); 反馈份额 -0.24 (显式 -0.24); 陈旧: tombstoned
     0.40 命名规范 (docs/特征DSL说明.md v1) :: 曝光 2 次, 引用 0 次 (引用率 0%); 陈旧: superseded
     0.40 ranking_model.yaml: features (configs/ranking_model.yaml v1) :: 曝光 1 次, 引用 0 次 (引用率 0%); 陈旧: superseded
     0.40 ranking_config_loader 模块 (code/ranking_config_loader.py v1) :: 曝光 5 次, 引用 1 次 (引用率 20%); 反馈份额 -0.16 (显式 -0.16); 陈旧: superseded
     0.40 旧版模型发布流程 (废弃) (docs/旧版模型发布流程(废弃).md v1) :: 曝光 3 次, 引用 2 次 (引用率 67%); 反馈份额 -0.32 (显式 -0.32); 陈旧: tombstoned
   黄金集候选 (显式 +1 且有引用的对话): 25 条 -> outputs/golden_candidates.jsonl (不自动合并), 例如: 特征取数超时默认是多少毫秒 -> ['code/ranking_config_loader.py', 'code/serving_client.py', 'configs/ranking_model.yaml', 'docs/特征平台使用指南.md']

全部完成, 总耗时 0.5s; 输出目录: outputs/
```
