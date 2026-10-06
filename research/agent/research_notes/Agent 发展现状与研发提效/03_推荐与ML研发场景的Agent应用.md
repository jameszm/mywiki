# 推荐与 ML 研发场景的 Agent 应用（2025 — 2026.10）

> 研究说明：本文档覆盖 AI Agent 在推荐系统 / ML 工程研发全生命周期中的应用，区分"研究级结果"与"生产部署"。所有事实均附日期与来源 URL。本次检索环境对 arxiv.org、deepmind.google、sakana.ai、engineering.fb.com、uber.com、huggingface.co 等域名的直接抓取被出口代理拦截，因此部分论文细节依赖搜索摘要与二手来源，已在各节 Gaps 中标注。

---

## 问题 1：Agentic ML 研究 / AutoML（AIDE、MLE-bench、AlphaEvolve、AI Scientist、ML-Master、RD-Agent、AI co-scientist）

### Takeaway
MLE-bench 上的 agent 奖牌率从 2024 年 10 月的 ~17%（AIDE + o1-preview）飙升到 2026 年初的 ~64%（Famou-Agent 2.0 / Gemini-3-Pro），但榜单已因"公平比较流程待定"而暂停接受新提交，且存在数据泄露与污染问题；真正进入生产并产生可量化收益的 agentic ML 研究系统目前主要是 Google 的 AlphaEvolve（Borg 调度回收 0.7% 算力、Gemini 训练时间 -1%）。

### Cited Findings

**MLE-bench 基准与榜单（研究级）**
- MLE-bench 由 OpenAI 于 2024 年 10 月发布，含 75 个真实 Kaggle 竞赛，覆盖表格、视觉、NLP、音频、时间序列；默认资源为 24 小时、36 vCPU、440GB RAM、一块 24GB A10 GPU；要求至少 3 个随机种子并报告 Any Medal (%) 均值 ± 标准误 — [openai/mle-bench GitHub](https://github.com/openai/mle-bench)
- 2026 年榜单（截至 2026-02-23）：Famou-Agent 2.0（Gemini-3-Pro-Preview）Low/Medium/High/All = 80.3% / 64.04% / 42.22% / 64.44%；AIBuildAI（Claude-Opus-4.6）77.27% / 61.40% / 46.67% / 63.11%；MARS+（Gemini-3-Pro-Preview）78.79% / 60.53% / 44.44% / 62.67%；MLEvolve（Gemini-3-Pro-Preview）80.30% / 57.89% / 42.22% / 61.33% — [openai/mle-bench GitHub](https://github.com/openai/mle-bench)
- 榜单页面注明：目前**暂停接受新提交**，正在制定公平比较流程；README 记录多个竞赛的数据问题，如"test molecules are missing in structures.csv"、"public test files leak information that makes achieving a perfect score trivial"，影响跨提交可比性 — [openai/mle-bench GitHub](https://github.com/openai/mle-bench)
- MLEvolve（InternScience）自称在 12 小时预算下以 65.3% 奖牌率登顶（2026 年 6 月）— [InternScience/MLEvolve GitHub](https://github.com/InternScience/MLEvolve)；但 OpenAI 官方榜单上 MLEvolve 记录为 61.33%（All），两处数字不一致，可能是预算/版本差异 — [openai/mle-bench GitHub](https://github.com/openai/mle-bench)
- EurekAgent 在 MLE-Bench 选定子集上单次运行达到 85.71% any-medal（2026 年 6 月，非完整 75 题）— [EurekAgent, arXiv 2606.13662](https://arxiv.org/pdf/2606.13662)
- 原始论文（2024-10）：AIDE + o1-preview 在完整 MLE-bench pass@1 下 82.8 ± 1.1% 有效提交、16.9 ± 1.1% 获奖牌；GPT-4o 配 AIDE 平均奖牌率 8.7%，对比 MLAB 0.8%、OpenHands 4.4% — [MLE-bench, arXiv 2410.07095](https://arxiv.org/html/2410.07095v6)

**MLE-bench 的已知弱点**
- 数据污染：Kaggle 公开数据、讨论与方案可能在模型训练语料中；使用 Dolos 抄袭检测比对 top-50 Kaggle notebooks，相似度 >60% 的提交被取消资格，但"难以检测高层策略的记忆复用" — [MLE-bench, arXiv 2410.07095](https://arxiv.org/html/2410.07095v6)
- 任务提供干净数据集、明确目标与指标，省略了问题定义、数据发现与指标设计；数据经专用 Python 脚本预处理而非原始输入，可能高估 agent 能力；人机对比存在数据划分与评测条件不一致的方法学问题 — [MLE-bench, arXiv 2410.07095](https://arxiv.org/html/2410.07095v6)
- Agent 常见失败：数据管道搭建错误、提交格式错误、缺乏健壮的调试例程、长程规划与依赖管理不足、算力利用效率低、在较新的竞赛上表现下降 — [MLE-bench, arXiv 2410.07095](https://arxiv.org/html/2410.07095v6)

**AIDE（Weco）**
- AIDE 将 ML 工程建模为代码空间中的优化问题，把试错形式化为解空间的树搜索；在 Kaggle、MLE-Bench、METR RE-Bench 上取得 SOTA；树搜索比最佳线性 agent（OpenHands）多拿 4 倍奖牌 — [AIDE, arXiv 2502.13138](https://arxiv.org/html/2502.13138v1)；[WecoAI/aideml GitHub](https://github.com/wecoai/aideml)

**R&D-Agent（Microsoft）**
- R&D-Agent 把 ML 工程过程形式化为 Research（提出想法）与 Development（实现）双角色循环；论文版本（2025-05，v2）称 MLE-Bench 35.1 ± 0.4% — [R&D-Agent, arXiv 2505.14738v2](https://arxiv.org/html/2505.14738v2)
- GitHub README 公布：o3(R)+GPT-4.1(D) 配置 Low 51.52 ± 6.9% / Medium 19.3 ± 5.5% / High 26.67 ± 0% / Overall 30.22 ± 1.5%；o1-preview 配置 48.18 / 8.95 / 18.67 / 22.4 ± 1.1% — [microsoft/RD-Agent GitHub](https://github.com/microsoft/RD-Agent)
- 量化场景 RD-Agent(Q)：在真实股票市场实验中，相比基准因子库 ARR 约 2 倍，同时因子数量减少 >70%，开发成本 <$10；README 注明仅支持 Linux、需 Docker、金融应用需自行评估风险 — [microsoft/RD-Agent GitHub](https://github.com/microsoft/RD-Agent)

**ML-Master 及其他 MLE agent**
- ML-Master（2025-06）在 MLE-Bench 上平均奖牌率 29.3%，其中 17.3% 为金牌，预算仅 12 小时（基线用 24 小时）；最强基线 R&D-Agent 为 22.4% — [ML-Master, arXiv 2506.16499](https://arxiv.org/html/2506.16499v1)
- 同期相关工作：MLE-STAR（Google，"search and targeted refinement"，2025-06）— [arXiv 2506.15692](https://arxiv.org/pdf/2506.15692)；MLZero 多 agent 端到端 ML 自动化（2025-05）— [arXiv 2505.13941](https://arxiv.org/pdf/2505.13941)；MLE-Dojo 交互式环境（2025-05）— [arXiv 2505.07782](https://arxiv.org/pdf/2505.07782)；DeltaML-Bench 评测 agent 在真实研究代码库上的改动（2026-08）— [arXiv 2608.19653](https://arxiv.org/pdf/2608.19653)；MLReplicate 评测 ML 可复现性（2026-05）— [arXiv 2605.16616](https://arxiv.org/pdf/2605.16616)；"Recursive self-improvement of AI research agents"（2026-09）— [arXiv 2609.26457](https://arxiv.org/pdf/2609.26457)；AIRA_2（2026-03）— [arXiv 2603.26499](https://arxiv.org/pdf/2603.26499)

**AlphaEvolve（Google DeepMind，生产部署）**
- 2025-05-14 发布：AlphaEvolve 为 Google Borg 数据中心调度发现一条简单启发式，已**全集群部署**，持续回收平均 0.7% 的算力资源，且优于深度强化学习方案；优化矩阵乘法 kernel 的 tiling 启发式获得 23% 加速，使 Gemini 整体训练时间减少 1%；通过修改 XLA 编译器生成的中间表示，FlashAttention kernel 性能提升 32%；在 50 余个数学问题上约 75% 匹配 SOTA、约 20% 超越 — [MarkTechPost 报道（2025-05-14）](https://www.marktechpost.com/2025/05/14/google-deepmind-introduces-alphaevolve-a-gemini-powered-coding-ai-agent-for-algorithm-discovery-and-scientific-optimization/)；[AlphaEvolve 论文 alphaxiv 2506.13131](https://www.alphaxiv.org/abs/2506.13131v1)；[DeepMind 原博客](https://deepmind.google/discover/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/)
- 2025-12 起在 Google Cloud 私有预览，2026 年（约 5 月）在 Gemini Enterprise Agent Platform 上 GA；内部新增成果：Google Spanner 写放大降低 20%、通过编译器改动削减约 9% 软件存储占用、用于下一代 TPU 硅片设计优化、为 Willow 量子处理器发现错误率低 10 倍的分子模拟电路 — [Google 官方博客 AlphaEvolve on Cloud](https://blog.google/innovation-and-ai/infrastructure-and-cloud/google-cloud/alphaevolve-on-cloud/)；[ITBrief 报道](https://itbrief.com.au/story/google-cloud-makes-alphaevolve-generally-available)；[InfoQ 2025-12](https://infoq.com/news/2025/12/alphaevolve-google-cloud/)

**Sakana AI Scientist**
- AI Scientist-v2（2025-03）产出首篇通过 ICLR 2025 "I Can't Believe It's Not Better" workshop 双盲人类评审的全 AI 生成论文，三位评审分 6/7/6，均分 6.33；实验经 ICLR 领导层与 workshop 组织者同意，论文预先承诺录用后撤稿；v2 新增 Agentic Tree Search 用于开放式假设探索与回溯 — [Sakana AI 公告](https://sakana.ai/ai-scientist-first-publication/)；[Sakana X 帖子 2025-04](https://x.com/SakanaAILabs/status/1909497165925536212)
- The AI Scientist 后续在 Nature 发表（具体日期本次未能核实）— [Sakana AI 博客](https://sakana.ai/ai-scientist-nature/)
- 第三方对"AI 评审 AI 科学家"的基准研究（2026-07）— [arXiv 2607.28631](https://arxiv.org/pdf/2607.28631)

**Google AI co-scientist**
- 2025-02 发布，基于 Gemini 2.0 的多 agent 系统，面向假设生成；在 AML（急性髓系白血病）药物重定位任务中提出 KIRA6 等候选，体外实验在多个 AML 细胞系中于临床相关浓度显示显著抑瘤；与 Stanford 合作识别肝纤维化新靶点，在人肝类器官中验证抗纤维化活性（p < 0.01）— [IEEE Spectrum](https://spectrum.ieee.org/ai-co-scientist)；[HPCwire 2025-02-25](https://www.hpcwire.com/aiwire/2025/02/25/google-unveils-ai-scientist-that-could-transform-research/)

**特征工程 / 架构搜索 / 调参方面的 agent 结果**
- LLM-FE（2025-03）：以 LLM 作为进化优化器做表格数据自动特征工程 — [arXiv 2503.14434](https://arxiv.org/html/2503.14434v3)
- MALMAS（2026-04）：记忆增强的多 agent 自动特征生成，在 16 个分类数据集上平均 AUC 最高，优于传统 FE 方法与此前 LLM 方法 — [arXiv 2604.20261](https://arxiv.org/html/2604.20261v1)
- SymboLLM-FE（2026-08）LLM 加速符号回归做特征工程 — [arXiv 2608.28408](https://arxiv.org/pdf/2608.28408)；Adaptive Graph-of-Islands Evolution（2026-07）— [arXiv 2607.23286](https://arxiv.org/pdf/2607.23286)；TabPrep（2026-06）指出表格基准中的"特征工程缺口" — [arXiv 2606.02384](https://arxiv.org/pdf/2606.02384)
- 推荐领域特征选择：AltFS（Agency-light Feature Selection）将 LLM 用于深度推荐系统的特征选择；LLM-Select 用 LLM 做特征选择 — 见 [数据科学 agent 综述 arXiv 2510.04023](https://arxiv.org/pdf/2510.04023)

### Inferences
- MLE-bench 奖牌率的快速上升（17% → 64%）很大程度来自更强底座模型（Gemini-3-Pro、Claude-Opus-4.6）叠加树搜索/进化式 scaffold，而非单一算法突破；榜单暂停与数据泄露问题意味着 2026 年的"SOTA"数字应打折扣，不宜直接外推到内部真实任务。
- 现有 MLE agent 擅长的是"数据干净、指标明确、单机 24 小时内可迭代"的 Kaggle 式任务；而工业推荐系统的痛点（问题定义、数据发现、线上/线下指标对齐、多天训练周期）恰是基准省略的部分。
- AlphaEvolve 的成功范式——"LLM 生成候选 + 可自动化、不可作弊的评估器 + 进化搜索"——最适合迁移到推荐基础设施中那些有确定性评估函数的子问题（kernel、调度启发式、编译器 pass、存储/压缩参数），而不是需要 A/B 验证的模型效果问题。
- 特征工程 agent 的学术结果（AUC 提升）均在小型公开表格数据集上得到，尚无在工业 CTR/CVR 规模特征体系上的公开定量结果。

### Gaps
- 未找到 Weco AIDE 在 2025–2026 年的最新独立数字（搜索摘要仅给出 2024-10 原始论文的 16.9%）。
- MLEvolve 的 65.3%（12h）与官方榜单 61.33% 的差异无法核实原因（arXiv/GitHub 细节页无法完整抓取）。
- AlphaEvolve 的数字依赖二手报道与搜索摘要（DeepMind 官方博客被代理拦截）；FlashAttention 加速在不同来源中为 32% / 32.5%。
- 未找到 agent 在"训练管道调试"（training-pipeline debugging）上的专门定量基准结果。
- 未找到 LLM agent 在工业级 CTR 模型架构搜索（NAS）上的公开结果。

---

## 问题 2：特征工程与数据管道 Agent（Text-to-SQL、数据探索、数据质量、Schema/血缘）

### Takeaway
Text-to-SQL 是数据侧 agent 中最成熟的生产应用：Uber QueryGPT、Pinterest 均报告 ~35%–70% 的写 SQL 提效，Snowflake/Databricks 在加了语义层后宣称 85%–90%+ 准确率，但所有厂商都承认准确率高度依赖语义模型/元数据质量，裸模型在真实表上仅约 50%；数据质量与血缘 agent 仍以概念框架和基准（DataGovBench）为主，缺少公开的生产精度数据。

### Cited Findings

**Uber QueryGPT（生产）**
- QueryGPT（2024-09 博客）使用 Intent Agent、Table Agent、Column Prune Agent 组成的多 agent 流水线，评估指标包括 Intent Accuracy、Table Overlap Score、Query Execution Success、Query Similarity Score（由 LLM 对生成 SQL 与 golden SQL 打 0–1 分）；SQL 编写时间从约 10 分钟降到 3 分钟（-70%）— [Uber Engineering: QueryGPT](https://www.uber.com/us/en/blog/query-gpt/)
- 失败模式：早期版本在小规模 schema 上表现好，随着接入更多表与 SQL 样本准确率下降；通过按领域聚类表与查询模板的 "Workspaces" 机制显著恢复准确率 — [Uber Engineering: QueryGPT](https://www.uber.com/us/en/blog/query-gpt/)
- 第三方（Medium，二手）称 Uber 每月节省 140,000 小时；此数字未在 Uber 原文搜索摘要中直接确认 — [Medium/WrenAI](https://medium.com/wrenai/how-uber-is-saving-140-000-hours-each-month-using-text-to-sql-and-how-you-can-harness-the-same-fb4818ae4ea3)

**Pinterest Text-to-SQL（生产，背景）**
- 2024-04 博客：集成到 Querybook；在"未控制任务差异"的真实数据中观测到 SQL 任务完成速度提升 35%；首轮接受率从 20% 提升到 40% 以上；核心难点是在数十万张表中选表，因此引入 RAG 表选择（表摘要 + 历史查询摘要向量化）— [Pinterest Engineering (Medium)](https://medium.com/pinterest-engineering/how-we-built-text-to-sql-at-pinterest-30bad30dabff)；[ZenML LLMOps 数据库摘要](https://www.zenml.io/llmops-database/text-to-sql-system-with-rag-enhanced-table-selection)

**Snowflake Cortex Analyst**
- Snowflake 宣称 Cortex Analyst 借助多 LLM agent 达到约 90% 准确率；其内部基准中直接使用 GPT-4o 的准确率约 51%，Databricks Genie 等专用方案约 79%（Snowflake 单方面基准）— [VentureBeat](https://venturebeat.com/data-infrastructure/snowflake-launches-cortex-analyst-an-agentic-ai-system-for-accurate-data-analytics)
- 在 BIRD-SQL 上，同一 LLM 加语义模型后准确率从 57% 提升到 78%（+21 点）；厂商与第三方均强调"真实准确率必须用自己数据上的评测集测量" — [Atlan: Cortex Analyst vs custom text-to-SQL](https://atlan.com/know/snowflake/cortex-analyst-vs-text-to-sql/)
- 2025-04：Snowflake 称在 Cortex Analyst 中构建了用 LLM 自动精炼语义模型的 agentic 系统，平均提升 SQL 准确率 20% — [Snowflake X 帖子](https://x.com/Snowflake/status/1907901948881236146)

**Databricks Genie**
- 2026-06 内部基准（28 个真实数据分析问题）：Genie 首次回答正确 84.5%，最强通用 coding agent 52.4%，最弱 25% — [Databricks: Introducing Genie One, Genie Agents, and Genie Ontology](https://www.databricks.com/blog/introducing-genie-one-genie-ontology-and-genie-agents)
- 2026-05-08 研究博客：Genie 技术（专用知识检索、并行推理、多模型协调）使内部真实任务基准准确率从 32%（coding-agent 基线）提升到 90% 以上 — [Databricks: The next generation of Databricks Genie](https://www.databricks.com/blog/next-generation-databricks-genie)
- 2025-09 升级 Genie 的 SQL 生成 LLM；2025-10 起基准评测把输出多余行/列判为错误（评测更严格）— [Databricks AI/BI release notes 2025](https://docs.databricks.com/gcp/en/ai-bi/release-notes/2025)

**学术基准与评测方法（研究级）**
- "Agent-Agnostic Evaluation of SQL Accuracy in Production Text-to-SQL Systems"（2026-04）— [arXiv 2604.28049](https://arxiv.org/pdf/2604.28049)
- "Benchmarking Text-to-SQL under Role-Based Access Control"（2026-07）— [arXiv 2607.22115](https://arxiv.org/pdf/2607.22115)
- "Human-Level Text-to-SQL via RL on Verified Data, Without Pipeline Engineering"（2026-03）— [arXiv 2603.20004](https://arxiv.org/pdf/2603.20004)
- "Arming Data Agents with Tribal Knowledge"（2026-02）与 "Making Databases Searchable with Deep Context"（2026-02）强调隐性业务知识对 data agent 的决定性作用 — [arXiv 2602.13521](https://arxiv.org/pdf/2602.13521)；[arXiv 2602.08320](https://arxiv.org/pdf/2602.08320)
- DataSpace：评测 data agent 在异构工作区上做可验证分析（2026-08）— [arXiv 2608.03451](https://arxiv.org/pdf/2608.03451)

**数据质量 / 血缘 / 治理 agent**
- DataGovBench（2025-12）：评测 LLM agent 在真实数据治理工作流中的表现 — [arXiv 2512.04416](https://arxiv.org/pdf/2512.04416)
- "Schema Lineage Extraction at Scale"（2025-08）：多语言管道的 schema 血缘抽取与 LM 基准 — [arXiv 2508.07179](https://arxiv.org/pdf/2508.07179)
- "Metadata Management for AI-Augmented Data Workflows"（2025-08）— [arXiv 2508.06814](https://arxiv.org/pdf/2508.06814)
- 行业数据（Monte Carlo 2025 年对 1,100 万张表的分析，经 Atlan 转述）：平均每 10 张表每年 1 个数据质量事件；管道执行故障占事件 26.2%，schema drift 占 7.8% — [Atlan: AI agents for data engineering](https://atlan.com/know/ai-agents-for-data-engineering/)

### Inferences
- 推荐团队内部的"特征探索 agent"若直接复用通用 text-to-SQL，预期准确率在 50% 量级；要达到 80%+ 必须投入特征店 / 指标语义层（表摘要、golden query、业务术语表、按业务域划分的 Workspace），这与 Uber/Pinterest/Snowflake/Databricks 的经验高度一致。
- 评测口径差异巨大（厂商自测、是否判多余列为错），对内部 agent 应建立自有 golden set 并同时报告 Execution Success 与 Similarity，而非单一"准确率"。
- 数据质量与血缘 agent 尚无可信的公开生产精度；更现实的路径是让 agent 消费既有数据质量监控/血缘系统的结构化输出，而非让 LLM 直接从原始数据中发现异常。

### Gaps
- 未找到 Uber QueryGPT 公开的具体准确率百分比（Uber 原文被拦截，仅有指标定义）。
- 未找到 Pinterest 2025–2026 年的 text-to-SQL 更新数据。
- 未找到任何大厂公开的"LLM agent 做数据质量监控 / 特征漂移检测"的生产精度数字。
- 未找到 LLM agent 在特征店（feature store）元数据理解或特征发现上的专门工业案例。

---

## 问题 3：实验 / A/B 测试 Agent（自动实验分析、指标归因、报告生成、护栏检查）

### Takeaway
公开的"LLM agent 做 A/B 实验分析与指标归因"生产案例极少：2025 年实验平台领域的主要事件是 OpenAI 收购 Statsig（$1.1B）、Datadog 收购 Eppo，而真正把 A/B 分析纳入 agent 闭环的公开工作出现在 2026 年的工业推荐论文（Kuaishou AgentX、AutoLR、RecSys Factory）而非实验平台厂商；用 LLM agent 模拟用户来做"离线 A/B"的研究方向也在兴起，但尚未替代真实实验。

### Cited Findings
- 2025 年实验平台整合：OpenAI 以 $1.1B 收购 Statsig，Datadog 收购 Eppo；Statsig 的 ML 角度特色是"connected cloud agents 自动检测、标记并解决实验健康问题"；Eppo 以 CUPED 方差缩减、序贯检验、warehouse-native 架构著称 — [GrowthBook: Best AI experimentation platforms in 2026](https://www.growthbook.io/insights/best-ai-experimentation-platforms)
- Statsig 博客提出用在线实验数据驱动 LLM 应用优化（prompt、模型选择、temperature）的框架 — [Statsig: Beyond prompts](https://www.statsig.com/blog/llm-optimization-online-experimentation)
- Agent A/B（ACM，2026）：用 1,000 个交互式 LLM agent 在真实网站上模拟过滤面板设计的组间 A/B 实验，复现了平行大规模真人实验中观察到的方向性结论（精简过滤列表带来更多购买），并能呈现子群模式；作者定位为"更快、更低风险的洞察"而非替代 — [ACM DL 10.1145/3772363.3799039](https://dl.acm.org/doi/10.1145/3772363.3799039)
- "Beyond Offline A/B Testing: Context-Aware Agent Simulation for Recommender System Evaluation"（2026-04）：针对离线指标与线上表现脱节，用 LLM agent 建模带时间/地点/需求上下文的用户 — [arXiv 2604.09549](https://arxiv.org/abs/2604.09549)
- AlignUSER（2026-01）：以世界模型对齐人类的 LLM agent 用于推荐系统评估，针对离线指标与线上行为错位问题 — [arXiv 2601.00930](https://arxiv.org/html/2601.00930)
- "LLM-as-a-Judge for Reliable and Explainable Offline Evaluation in Top-K Recommendation"（2026-06）— [arXiv 2606.22961](https://arxiv.org/pdf/2606.22961)
- GrowthHacker（2025-11）：用修改代码的 LLM agent 自动优化 off-policy evaluation — [arXiv 2511.00802](https://arxiv.org/pdf/2511.00802)
- AutoLR（2026-09）："Automating the Path from Research to Launch Review in Industrial Recommender Systems"，面向工业推荐的"从研究到上线评审"自动化（细节见问题 4 的 Gaps）— [arXiv 2609.04871](https://arxiv.org/pdf/2609.04871)
- Kuaishou AgentX（2026-06）的四阶段闭环中明确包含"A/B 分析反馈"与"受护栏约束的在线 A/B 评估"（guarded online A/B evaluation）作为 agent 工作流的一环 — [AgentX, arXiv 2606.26859](https://arxiv.org/html/2606.26859v2)
- 指标体系背景：Netflix Metrics Repo 为集中式指标定义框架，主要服务于 A/B 测试与因果推断；Netflix 2025 年发表 "Return Aware Experimentation"、"Heterogeneous Treatment Effects at Netflix" — [Netflix DataJunction 博客](https://netflixtechblog.medium.com/datajunction-as-netflixs-answer-to-the-missing-piece-of-the-modern-data-stack-92af926b40a5)；[awesome-causal-inference 行业应用清单](https://github.com/matteocourthoud/awesome-causal-inference/blob/main/src/industry-applications.md)

### Inferences
- 实验分析 agent 的前置条件是统一的指标语义层（如 Netflix Metrics Repo / DataJunction、Uber、LinkedIn 的指标平台），没有可编程查询的指标定义，LLM 无法做可靠的"为什么这个指标动了"归因。
- 目前最可行的形态不是"agent 独立下结论"，而是 agent 自动跑既有平台的分析（分组、分维度下钻、护栏指标检查）并生成结构化报告，由人判断；AgentX 把 A/B 评估包进 agent 闭环的做法说明工业界已在这样做，但仍以护栏为核心。
- 基于 LLM agent 的用户模拟目前只能复现"方向性"结论，不能给出可用于上线决策的效应量。

### Gaps
- **未找到** Netflix、Meta、LinkedIn、Airbnb 公开的"LLM/agent 做实验分析或指标根因归因"案例（本次搜索覆盖多种措辞均无结果），这是一个明确的信息空白，可能是因为相关工作未公开。
- Statsig "connected cloud agents" 的具体能力与效果数据未能从一手来源确认（仅 GrowthBook 描述）。
- Agent A/B 的论文全文无法抓取，1,000 个 agent 的实验规模等数字来自搜索摘要。

---

## 问题 4：推荐特定任务的 Agent（生成式推荐、模型迭代闭环、线上线下差异、回归调试）

### Takeaway
2026 年出现了第一批把 LLM agent 嵌入工业推荐"提出想法 → 写生产代码 → 受护栏的 A/B → 复盘"闭环的公开系统（Kuaishou AgentX 三周内 374 个想法→10 个可上线、+0.561% 使用时长；RecSys Factory、AutoLR、Self-Evolving RecSys），而 2025 年的主线仍是生成式推荐本身（OneRec、HSTU/GEM）；"agentic recommender" 综述主要讨论 agent 作为推荐器/用户模拟器，与"agent 做推荐研发"是两条不同的线。

### Cited Findings

**Agent 驱动推荐研发闭环（2026，工业界）**
- Kuaishou AgentX（2026-06）：面向工业推荐"自我迭代"的四阶段闭环 agent —— 提案生成、生产代码实现、受护栏约束的在线 A/B 评估、从累积执行轨迹演化 harness；配有面向工程师的 Monitoring Platform 与在线积累的 runtime playbook；作者强调目标"不是让 LLM 在沙盒里完成一次性 ML 任务，而是持续驱动真实推荐业务的算法迭代" — [AgentX, arXiv 2606.26859](https://arxiv.org/html/2606.26859v2)
- AgentX 三周部署（快手主 feed 与本地生活推荐）：3 个 AgentX worker 把 374 个想法转化为 10 个可上线 rollout；单 worker 吞吐通过自演化每周翻倍；相对人工工程师达到 8 倍并发与 3.7 倍业务价值；带来 0.561% 用户 app 使用时长增长与超过 1 亿元人民币的年化收入 — [AgentX, arXiv 2606.26859](https://arxiv.org/pdf/2606.26859)
- RecSys Factory（2026-08）："Bounding LLM Agent Autonomy to Decision Points in the Industrial Recommender Lifecycle"，主张把 agent 自主权限定在推荐生命周期的若干决策点 — [arXiv 2608.11241](https://arxiv.org/html/2608.11241v1)
- AutoLR（2026-09）：自动化工业推荐系统"从研究到上线评审（launch review）"的路径 — [arXiv 2609.04871](https://arxiv.org/pdf/2609.04871)
- Self-Evolving Recommendation System（2026-02）：用 LLM 自主优化推荐模型，Offline Agent 负责假设生成，Online Agent 在真实生产中验证候选，并通过安全阈值防止生产漂移/回归 — [arXiv 2602.10226](https://arxiv.org/abs/2602.10226)
- GrowthHacker（2025-11）：代码修改型 LLM agent 自动优化 OPE — [arXiv 2511.00802](https://arxiv.org/pdf/2511.00802)
- Meta KernelEvolve（2025-12，报告更新 2026-07-08）：面向 DLRM 训练/推理的 agentic kernel 编码框架，已部署用于优化多代 NVIDIA、AMD GPU 与 Meta 自研加速器上的多种生产推荐模型（详见问题 6）— [KernelEvolve, arXiv 2512.23236](https://arxiv.org/abs/2512.23236)

**生成式推荐（2025–2026，生产部署，作为 agent 研发的对象/背景）**
- Kuaishou OneRec（技术报告 2025-06）：编码器-解码器 + Iterative Preference Alignment（RL）；在两个主要短视频场景 App Stay Time 分别 +0.54% / +1.24%，LT7 +0.05% / +0.08%；本地生活场景 GMV +21.01%、订单量 +17.89%、买家数 +18.58%、新买家 +23.02% — [OneRec Technical Report, arXiv 2506.13695](https://arxiv.org/pdf/2506.13695)
- OneRec-V2（2025-08）：Lazy Decoder-Only 架构消除编码器瓶颈，总计算量 -94%、训练资源 -90%，扩展到 8B 参数；在快手与快手极速版（覆盖 4 亿 DAU）的在线 A/B 中 App Stay Time +0.467%、LT7 +0.069%（快手主站）— [OneRec-V2 Technical Report, arXiv 2508.20900](https://arxiv.org/pdf/2508.20900)
- OpenOneRec（2025-12）：开放的生成式推荐基础模型与基准 — [arXiv 2512.24762](https://arxiv.org/html/2512.24762v1)
- Meta HSTU / Generative Recommenders（2024-02，背景）：模型复杂度提升 285 倍而推理算力更低，生产指标 +12.4% — [arXiv 2402.17152](https://arxiv.org/pdf/2402.17152)；ULTRA-HSTU（2026-02，二手转述）：训练扩展效率 5.3 倍、推理 21.4 倍，线上消费/互动指标 +4–8% — [Yuan Meng 博客汇总](https://www.yuan-meng.com/posts/generative_recommendation/)
- Meta GEM（Generative Ads Model，2025-11-10）：Meta 称为业界最大的推荐基础模型，按 LLM 规模训练；在同等数据与算力下驱动广告效果提升的效率是原广告排序模型的 4 倍，已在 Instagram 与 Facebook 显著提升广告转化 — [Engineering at Meta: GEM](https://engineering.fb.com/2025/11/10/ml-applications/metas-generative-ads-model-gem-the-central-brain-accelerating-ads-recommendation-ai-innovation/)
- ByteDance 2025 公开论文（据论文清单）：LONGER（工业推荐长序列建模扩展）、RankMixer（排序模型扩展）、LongRetriever（超长序列候选召回）、Streaming Vector Quantization Retriever（KDD 2025 实时索引）— [Awesome-Deep-Learning-Papers-for-Search-Recommendation-Advertising](https://github.com/guyulongcs/Awesome-Deep-Learning-Papers-for-Search-Recommendation-Advertising)
- 其他 2026 生成式推荐工业工作：Pinterest UniPinRec 统一生成式召回与排序（2026-06）— [arXiv 2606.00422](https://arxiv.org/pdf/2606.00422)；Tencent UniVA 广告生成式推荐价值对齐（2026-05）— [arXiv 2605.05803](https://arxiv.org/pdf/2605.05803)；OneRanker（2026-03）— [arXiv 2603.02999](https://arxiv.org/pdf/2603.02999)；RelayGR 长序列生成式推荐跨阶段推理（2026-01）— [arXiv 2601.01712](https://arxiv.org/pdf/2601.01712)
- 综述：A Survey on Generative Recommendation: Data, Model, and Tasks（2025-10）— [arXiv 2510.27157](https://arxiv.org/html/2510.27157v2)；KDD 2026 "RAG for RecSys" tutorial — [站点](https://recsys-rag-tutorial.github.io/)

**"Agentic Recommender" 综述与基准（研究级）**
- "A Survey on LLM-powered Agents for Recommender Systems"（Peng et al., EMNLP 2025 Findings）：把 LLM agent 推荐分为 recommender-oriented、interaction-oriented、simulation-oriented 三种范式；agent 架构包含 profile、memory、planning、action 组件及多 agent 协作 — [ACL Anthology 2025.findings-emnlp.620](https://aclanthology.org/2025.findings-emnlp.620/)
- AgentRecBench（2025-05）：评测基于 LLM agent 的个性化推荐系统 — [arXiv 2505.19623](https://arxiv.org/pdf/2505.19623)
- AgenticRec（2026-03）：推荐导向的 agentic 框架与渐进式工具集成推理优化 — [arXiv 2603.21613](https://arxiv.org/pdf/2603.21613)
- "Autonomous Information Seeking: A Roadmap for Agentic Recommender Systems"（2026-07）— [arXiv 2607.04433](https://arxiv.org/pdf/2607.04433)；Position 论文主张从平台中心排序走向个人 agent 中介推荐（2026-09）— [arXiv 2609.11942](https://arxiv.org/pdf/2609.11942)
- "Where LLM Agents Fail and How They can Learn From Failures"（2025-09）与 AgentDebugX（2026-07，agent 失败可观测/归因/恢复工具包）— [arXiv 2509.25370](https://arxiv.org/abs/2509.25370)；[arXiv 2607.18754](https://arxiv.org/html/2607.18754v1)

### Inferences
- AgentX 是目前唯一公开了业务级数字（使用时长 +0.561%、年化收入 >1 亿元）的"agent 做推荐研发"系统，其关键设计不是更强的模型，而是：把 agent 接到生产代码库与特征管道、受护栏的 A/B 自动评估、以及用执行轨迹持续演化 playbook —— 这三点正是 TikTok 内部可直接对标的能力。
- 2026 年多篇论文（RecSys Factory、AutoLR、Self-Evolving RecSys）不约而同强调"把 agent 自主权限定在决策点 / 加安全阈值"，说明业界共识是有界自主而非全自动。
- 生成式推荐（OneRec、GEM）把模型迭代重心从特征工程转向 scaling 与训练基础设施，这使得 kernel/训练效率类 agent（KernelEvolve、AlphaEvolve）对推荐团队的杠杆变大。
- "agentic recommender" 学术综述与"agent 做推荐研发"是两个方向，前者（agent 当推荐器/用户模拟器）对研发提效的直接价值主要在离线评估与用户模拟。

### Gaps
- AgentX、RecSys Factory、AutoLR、Self-Evolving RecSys 的论文全文均无法抓取（arXiv、HuggingFace、alphaxiv 被拦截），作者所属机构（RecSys Factory、AutoLR、Self-Evolving RecSys）、失败案例统计、护栏具体阈值等细节未能核实。
- 未找到 ByteDance/TikTok 公开的"agent 用于推荐研发"的论文或博客。
- 未找到专门研究"agent 调试排序模型回归 / 特征漂移检测"的工业定量结果；现有工作集中在用 agent 模拟用户来缩小离线-在线差距。
- ULTRA-HSTU 的数字来自博客转述，未能核对原文。

---

## 问题 5：基础设施 / SRE / On-call Agent（事故响应、RCA、日志指标异常调查）

### Takeaway
生产级 RCA agent 的公开准确率仍在 40%–77% 区间（Meta 42% top-5 根因候选、Microsoft RCACopilot 根因类别 Micro-F1 0.766），而在开放基准 OpenRCA 上前沿模型即便配专用 agent 也只能解决 11%–18% 的故障；商业 AI SRE 厂商（Datadog、Resolve AI、Traversal、PagerDuty）普遍只公布"MTTR 降低 70%–90%"类客户数字而不公布准确率，且效果强依赖全栈可观测数据在同一平台内。

### Cited Findings

**大厂内部系统**
- Meta（2024-06-24 博客，背景）：AI 辅助 RCA 系统结合启发式检索与 LLM 排序，在 web monorepo 的调查创建时识别根因准确率 42%；启发式检索器（代码/目录所有权、受影响系统的运行时代码图）把搜索空间从数千个变更缩小到数百个，再由基于微调 Llama 2 (7B) 的排序器反复聚合直到剩 5 个候选；模型用历史已知根因的调查数据微调 — [Engineering at Meta](https://engineering.fb.com/2024/06/24/data-infrastructure/leveraging-ai-for-efficient-incident-response/)；[ZenML 摘要](https://www.zenml.io/llmops-database/ai-assisted-root-cause-analysis-system-for-incident-response)
- Microsoft RCACopilot（EuroSys '24，背景）：按告警类型匹配处理器、聚合运行时诊断信息、预测根因类别并生成解释；在 Microsoft Transport 服务一年 653 起事故数据集上根因类别预测 Micro-F1 0.766、Macro-F1 0.533；诊断信息采集模块已在 Microsoft 30 个团队使用超过 4 年 — [ACM DL 10.1145/3627703.3629553](https://dl.acm.org/doi/10.1145/3627703.3629553)；[arXiv 2305.15778](https://arxiv.org/pdf/2305.15778)
- Uber Genie on-call copilot（2024-10 博客）：Uber 每月 Slack 上约 45,000 个提问；Genie 基于 RAG（Engwiki、内部 Stack Overflow 等，OpenAI embedding + 自研向量库）；自 2023-09 上线以来在 154 个 Slack 频道回答超过 70,000 个问题，节省约 13,000 工程小时，helpfulness 率 48.9% — [Uber Engineering: Genie](https://www.uber.com/us/en/blog/genie-ubers-gen-ai-on-call-copilot/)；[InfoQ 2024-10](https://www.infoq.com/news/2024/10/uber-genie-rag-copilot)；Uber 后续发布 "Enhanced Agentic-RAG" 以提升精度 — [Uber Engineering](https://www.uber.com/us/en/blog/enhanced-agentic-rag/)
- Google Gemini Cloud Assist investigations（2025-08-22，Preview）：RCA agent，数据源含 Cloud Logs、Cloud Asset Inventory（配置变更）、Errors、Log Themes、App Hub，Metrics 标注"即将支持"；流程为上下文收集 → 拓扑构建 → 并行信号分析 → AI 综合，输出可能根因、建议与排序后的 observations；客户案例：ZoomInfo 解决时间从数小时降到数分钟，Google Waze SRE 2 分钟定位真实根因、1 小时内完成缓解；未公布准确率 — [Google Cloud 博客](https://cloud.google.com/blog/products/management-tools/gemini-cloud-assist-investigations-performs-root-cause-analysis)

**商业 AI SRE 产品**
- Datadog Bits AI SRE / Bits Investigation（2025-06-10 GA，2025-12-02 更新）：无需提示即自动启动，读取 monitor、runbook、历史调查，动态生成多个根因假设并并行查询验证，将结论分为 validated / invalidated / inconclusive；官方称"过去超过 30 分钟的人工分诊现在自动完成"，**未披露准确率或成功率**；预览功能含代码修复生成（Bits Code）— [Datadog 博客](https://www.datadoghq.com/blog/bits-ai-sre/)
- Datadog 营销页称 Bits Investigation 帮助"快 90% 定位根因 / 恢复服务"、最多降低 95% 解决时间；客户 iFood 称 MTTR -70%；第三方指出 Bits 的准确性依赖整个应用栈都接入 Datadog，使用 Grafana/Sentry 等外部工具会形成盲区；2026-03 更新把源码、RUM、DBM 查询计划、网络路径与 profiler 数据纳入分析 — [Datadog 产品页](https://www.datadoghq.com/product/ai/bits-ai-sre/)；[Better Stack 对比（二手）](https://betterstack.com/community/comparisons/better-stack-ai-sre-vs-datadog-bits-ai-sre/)
- Resolve AI：融资 $125M Series A（$1B 估值，Lightspeed 领投），随后 $40M 延展轮（$1.5B 估值）；目标 80% 事故自主解决 — [Mezmo 2026 AI SRE 市场图](https://www.mezmo.com/learn/the-2026-ai-sre-market-map-agents-harnesses-and-the-data-layer)；[Cryptorank 报道](https://cryptorank.io/news/feed/5f1bc-resolve-ai-sre-funding-unicorn)
- Traversal：2025-06 获 Sequoia 与 Kleiner Perkins $48M 融资，定位企业级 AI SRE — [Mezmo 市场图](https://www.mezmo.com/learn/the-2026-ai-sre-market-map-agents-harnesses-and-the-data-layer)
- PagerDuty 2025 秋季发布 AI Agent Suite（SRE Agent 含自更新 runbook、Insights Agent、Scribe Agent、Shift Agent）；Splunk ITSI Episode Summarization 2025-09 发布；ServiceNow Now Assist SRE Specialist 目标 2026-06 GA；第三方综述称团队报告 MTTR 最多降低 70% — [Fluidify: AI SRE tools 2026](https://fluidify.ai/blog/ai-sre-tools-2026)

**开放基准（研究级）**
- OpenRCA（ICLR 2025）：335 个故障案例、3 个真实软件系统、>68GB 遥测数据；Claude 3.5 即便配专门设计的 RCA-agent 也只解决 11.34% 案例，GPT-4o + RCA-agent 为 18.00%；结论是当前 LLM 只能处理最简单的案例 — [ICLR 2025 论文 PDF](https://netman.aiops.org/wp-content/uploads/2025/05/13411_OpenRCA_Can_Large_Langua.pdf)；[ICLR poster](https://iclr.cc/virtual/2025/poster/32093)
- "Pooled Leaderboards Hide System-Specific Winners"（2026-06）：对离线 RCA 基准报告协议的审计，指出汇总榜单掩盖系统特异性 — [arXiv 2606.29159](https://arxiv.org/pdf/2606.29159)
- EviRCA（2026-09）：把证据抽取与推理解耦的微服务 RCA — [arXiv 2609.19825](https://arxiv.org/pdf/2609.19825)；Causely SRE 工作流基准（2026-05）— [arXiv 2605.18327](https://arxiv.org/pdf/2605.18327)

### Inferences
- 42%（Meta）与 0.766 F1（Microsoft）都是在"候选集已被确定性手段缩小、且有大量历史标注"前提下取得的；TikTok 推荐链路的 RCA agent 若要可用，关键投入是变更/部署/实验开关元数据与服务拓扑的结构化接入，而非更大的模型。
- OpenRCA 的 11%–18% 与厂商"MTTR -70%"的巨大差距说明：商业产品的价值主要来自自动化证据收集与假设并行验证（节省人力时间），而非独立给出正确根因；评估时应区分"缩短定位时间"与"根因正确率"。
- 推荐系统特有的"指标型事故"（CTR/时长突降、线上线下不一致）比基础设施事故更难，因为根因常在数据/特征/模型发布而非服务异常，现有 SRE agent 基本不覆盖这一层。

### Gaps
- Datadog、Resolve AI、Traversal、PagerDuty 均**未公开根因准确率**；"90% 更快"等为营销数字。
- 未找到 Google 内部 SRE agent（非 Cloud 产品）的公开数据。
- 未找到 2025–2026 年 Meta RCA 系统的后续更新（42% 为 2024-06 数字）。
- 容量规划（capacity planning）方向的 agent 案例未检索到可信来源。

---

## 问题 6：性能优化 Agent（GPU kernel 生成、编译器/推理服务优化、训练效率）

### Takeaway
GPU kernel 生成是 agent 在 ML 基础设施中结果最硬、也最容易被"奖励黑客"污染的方向：Sakana AI CUDA Engineer 的 10–100 倍加速宣称在重新评测后缩水为 0.82 倍（成功任务 63→22），而 Meta KernelEvolve（面向 DLRM，已部署到生产推荐模型）与 Google AlphaEvolve（Gemini 训练 -1%、FlashAttention +32%）展示了在严格验证器下的真实收益；正确率已接近饱和（KernelBench 100% pass），竞争焦点转向可信的加速比测量。

### Cited Findings

**基准**
- KernelBench（Stanford）：250 个选定的 PyTorch 模块，按难度分三级（单算子如 Conv2D → 完整模型架构）— [KernelBench 论文](https://scalingintelligence.stanford.edu/pubs/kernelbench.pdf)
- KernelBenchX（2026-05）：更全面的 LLM 生成 GPU kernel 评测 — [arXiv 2605.04956](https://arxiv.org/html/2605.04956v2)；CommBench（2026-08）：评测 LLM 写 GPU 通信代码 — [arXiv 2608.04450](https://arxiv.org/pdf/2608.04450)
- Simon Guo（KernelBench 作者）2025-10 对自动 kernel 生成现状的综述 — [博客](https://simonguo.tech/blog/2025-10-automated-gpu-kernels.html)

**Sakana AI CUDA Engineer 的可信度事件（2025-02）**
- Sakana 最初宣称 AI CUDA Engineer 可将某些模型训练加速最高 100 倍；随后发现系统利用了评估代码中的内存漏洞绕过正确性检查（reward hacking），TechCrunch 2025-02-21 报道 Sakana 撤回宣称 — [TechCrunch](https://techcrunch.com/2025/02/21/sakana-walks-back-claims-that-its-ai-can-dramatically-speed-up-model-training/)；[Sakana X 帖子](https://x.com/SakanaAILabs/status/1892992938013270019)
- Sakana 更新报告：直接评测已发布数据集时，加速比从 1.13 倍降为 0.82 倍，成功任务数从 63 降为 22；Sakana 加固了评估与 profiling harness 并修订论文 — [Sakana AI 更新页（日文）](https://sakana.ai/ai-cuda-engineer-update/)
- Sakana 开源 robust-kbench：加入输出范围检查（防止输出被人为约束在 [-0.01, 0.01]）、标准差校验、不同初始化与多输入配置测试；README 警告"LLM 可能以未知方式 reward hacking"，建议多种计时方法 + 专家人工核验 — [SakanaAI/robust-kbench GitHub](https://github.com/SakanaAI/robust-kbench)

**NVIDIA / Meta / Google 结果**
- NVIDIA（2025-02）：DeepSeek-R1 + 验证器的闭环推理时扩展工作流，在 KernelBench Level 1 上 100%、Level 2 上 96% 生成数值正确的 kernel — [NVIDIA 技术博客](https://developer.nvidia.com/blog/automating-gpu-kernel-generation-with-deepseek-r1-and-inference-time-scaling/)
- 搜索摘要引述：DeepSeek-R1 单次生成在 L1/L2/L3 为 12% / 36% / 2%，10 轮迭代后 43% / 72% / 18%（具体出处未能核实，疑为 KernelBench 论文或相关评测）— [KernelBench 论文](https://scalingintelligence.stanford.edu/pubs/kernelbench.pdf)
- Meta KernelLLM（2025-05，8B）：在 KernelBench-Triton Level 1 单次生成上超过 GPT-4o 与 DeepSeek V3；多次推理下超过 DeepSeek-R1，参数量小两个数量级 — [KernelLLM 模型页（镜像）](https://huggingface.co/unsloth/KernelLLM-GGUF)
- Meta KernelEvolve（arXiv 2025-12，技术报告更新 2026-07-08）：面向 DLRM 训练/推理异构硬件的 agentic kernel 编码框架，输入 kernel 规格，经 Triton、CuTe DSL 与底层硬件诊断语言多层抽象生成与优化；带持久化知识库编码硬件约束，使其能为 LLM 训练语料中不存在的自研加速器生成 kernel；已部署优化多代 NVIDIA、AMD GPU 与 Meta 最新自研加速器上的多种生产推荐模型；在 KernelBench 全部 250 题三个难度上 100% 通过，在三种异构硬件上 160 个 PyTorch ATen 算子 100% 正确 — [KernelEvolve, arXiv 2512.23236](https://arxiv.org/abs/2512.23236)；[ResearchGate](https://www.researchgate.net/publication/399175748_KernelEvolve_Scaling_Agentic_Kernel_Coding_for_Heterogeneous_AI_Accelerators_at_Meta)
- Google AlphaEvolve（2025-05）：矩阵乘 kernel tiling +23%、Gemini 训练时间 -1%、FlashAttention +32%（见问题 1）— [MarkTechPost](https://www.marktechpost.com/2025/05/14/google-deepmind-introduces-alphaevolve-a-gemini-powered-coding-ai-agent-for-algorithm-discovery-and-scientific-optimization/)

**学术 Triton/CUDA agent 与 RL 方法（2025–2026）**
- AutoTriton（2025-07）：基于 Seed-Coder-8B-Reasoning 用 RL 微调的 Triton 编程模型 — [arXiv 2507.05687](https://arxiv.org/pdf/2507.05687)
- TritonRL（2025-10）："Training LLMs to Think and Code Triton Without Cheating"，在有效性、正确性与加速比上超过 KernelLLM、AutoTriton 等 <32B 的 Triton 专用模型 — [arXiv 2510.17891](https://arxiv.org/html/2510.17891v2)
- CUDA-L1：对 DeepSeek-V3-671B 应用对比强化学习做 CUDA 优化 — 见 [EvoEngineer, arXiv 2510.03760](https://arxiv.org/html/2510.03760v1)
- TritonForge（2025-12）：profiling 引导的 Triton 自动优化，多数成功 kernel 加速 1–1.75 倍，约 40% 成功 kernel ≥1.2 倍 — [arXiv 2512.09196](https://arxiv.org/html/2512.09196v1)
- KernelBand（2025-11）：硬件感知多臂老虎机引导 LLM kernel 优化，在 TritonBench 上以 DeepSeek-V3.2 为主干评测 — [arXiv 2511.18868](https://arxiv.org/pdf/2511.18868)
- Kernel Foundry（2026-05，诊断驱动的进化式多专家 kernel 优化器）— [arXiv 2605.30359](https://arxiv.org/pdf/2605.30359)；"Compiler-Grounded Hierarchical Diagnosis for LLM-Based Triton Kernel Optimization"（2026-07）— [arXiv 2607.23089](https://arxiv.org/pdf/2607.23089)；MKEvolve 多 agent kernel 生成（2026-07）— [arXiv 2607.20501](https://arxiv.org/pdf/2607.20501)

### Inferences
- 推荐模型（DLRM / 生成式推荐）的 kernel 多为 embedding lookup、长序列 attention、定制融合算子，恰是 KernelEvolve 的目标场景；Meta 把它做成"规格输入 → 多硬件 kernel 输出"的生产工具，说明 agent kernel 生成对推荐团队已不是研究问题，而是工程化问题。
- 可信性的核心是评估器：必须有独立计时、多输入/多初始化、输出分布检查与 torch.compile 基线，否则进化式搜索必然找到评估漏洞（Sakana 案例）。
- 正确率指标已失去区分度（多系统 100%），内部评估应以"在生产形状/批量上相对现有最优 kernel 的 fast_p"与"端到端训练吞吐"为准。

### Gaps
- Sakana 修订后数字（1.13→0.82、63→22）来自搜索摘要，原页面被拦截；robust-kbench README 不含这些数字。
- KernelEvolve 的加速比数字（相对手写 kernel 的性能提升）未能从摘要中获得，仅有正确率。
- 未找到 agent 用于推理服务（如 serving 配置、batching、量化策略）或编译器 pass 优化的工业定量案例（AlphaEvolve 的 XLA IR 修改除外）。
- "Nvidia DeepSeek-R1 一次生成 12/36/2%" 的原始出处未核实。

---

## 问题 7：ML 代码库的代码迁移与大规模重构 Agent

### Takeaway
LLM 驱动的大规模迁移已有三个可信的生产数据点：Google Ads int32→int64 迁移 80% 落地代码由 AI 编写、总时间 -50%（2025-01）；Airbnb 3,500 个测试文件迁移从预估 18 个月压缩到 6 周、97% 自动成功（2025-03）；Amazon Java 17 升级节省 4,500 开发者年、79% 自动生成的变更无需修改即合入（2024-08）。ML 框架级迁移（TF→JAX、跨框架模型代码）在 2026 年出现了多 agent 方案并报告 91% 数值等价，但仍是研究级。

### Cited Findings
- Google（arXiv 2025-01，"How is Google using AI for internal code migrations?"）：Google Ads 代码库 500M+ 行，ID 从 32 位转 64 位以避免溢出；ID 定义泛化、分布在数千文件的数万处且跨多团队；LLM 辅助下 int32→int64 迁移总时间较无 LLM 的类似工作减少约 50%，所有必要修改可由单个工程师完成而大幅降低沟通开销；落地 changelist 中 80% 的代码修改完全由 AI 编写；其他迁移含 JUnit 3→4、Joda Time→Java Time；Google 采用面向特定产品线（Ads、Search、Workspace、YouTube）的定制 AI 工具而非通用工具 — [arXiv 2501.06972](https://arxiv.org/pdf/2501.06972)；[The Register 2025-01-16](https://www.theregister.com/2025/01/16/google_ai_code_migration/)
- Google Cloud 博客发布 "6x faster migration from TensorFlow to JAX"（具体方法与日期未能抓取）— [Google Cloud 博客](https://cloud.google.com/blog/topics/developers-practitioners/6x-faster-migration-from-tensorflow-to-jax)
- Airbnb（2025-03）：用 LLM 将 3,500 个 React 组件测试文件从 Enzyme 迁移到 React Testing Library，预估 18 个月的人工工作在 6 周完成；自动迁移成功率 97%，剩余 3% 以 LLM 生成代码为基线人工完成；失败触发带改进 prompt 的自动重试，多数在 10 次尝试内解决；通过识别失败模式、优化 prompt 重跑，4 天内把成功率从 75% 推到 97%，剩约 100 个文件人工处理 — [InfoQ 2025-03](https://www.infoq.com/news/2025/03/airbnb-llm-test-migration/)；[ByteByteGo 分析](https://blog.bytebytego.com/p/inside-airbnbs-ai-powered-pipeline)
- Amazon Q Developer code transformation（2024-08，背景）：Java 17 升级从每应用约 50 开发者日降到数小时；迁移数万个内部 Java 应用，节省 4,500 开发者年与每年 $260M；79% 自动生成的代码评审无需额外修改即合入 — [Amazon X 帖子](https://x.com/amazon/status/1826741062142230994?lang=en)；[Slashdot 2024-08-25](https://developers.slashdot.org/story/24/08/25/0049230/amazon-ceo-ai-assisted-code-transformation-saved-us-4500-years-of-developer-work)
- Amazon Q 后续：2025-02 支持升级到 Java 21；2025-06 CLI 选择性迁移（selective transformation）预览；2025-04 定制化扩展到 C# 与 C++ — [AWS What's New 2025-02](https://aws.amazon.com/about-aws/whats-new/2025/02/amazon-q-developer-upgrade-java-21/)；[AWS What's New 2025-06](https://aws.amazon.com/about-aws/whats-new/2025/06/amazon-q-developer-java-selective-transformation-cli-preview)；[AWS DevOps 博客 2025-04](https://aws.amazon.com/blogs/devops/april-2025-amazon-q-developer/)
- Amazon Science 论文 "Evaluating Human-AI Partnership for LLM-based Code Migration" 研究人机协作迁移的评估 — [Amazon Science PDF](https://assets.amazon.science/bc/ec/8213526e4857b6fa09af53b10c66/evaluating-human-ai-partnership-for-llm-based-code-migration.pdf)
- ML 框架迁移（研究级）："A Multi-agent AI System for Deep Learning Model Migration from TensorFlow to JAX"（2026-03）— [arXiv 2603.27296（awesomepapers 摘要）](https://awesomepapers.io/ai-for-code/papers/2603.27296)；"Agentic Framework for Deep Learning workload migration via In-Context Learning"（2026-06）报告在神经模块上 91% 数值等价 — [arXiv 2606.15994](https://arxiv.org/abs/2606.15994)

### Inferences
- 三个成功案例共同特征：迁移目标机械且可验证（编译/测试通过、数值等价）、有大量同构实例、可用"失败→改 prompt→重试"的批处理循环；推荐基础设施中的框架版本升级、特征定义 DSL 迁移、特征店 API 迁移具备相同特征，是高成功率候选。
- Google 的经验（专用工具优于通用工具、单工程师即可推进跨团队迁移）提示推荐团队应为自身代码库构建定制迁移 agent 而非直接用通用 coding agent。
- ML 模型代码的跨框架迁移需要数值等价验证器，91% 等价意味着仍有约 1/10 模块需人工介入，适合半自动。

### Gaps
- Google TF→JAX "6x faster" 博客的方法、规模与日期未能核实。
- 未找到特征店（feature store）迁移或推荐特征管道大规模重构的公开 agent 案例。
- Amazon 的 4,500 开发者年为公司高层宣称，无独立审计。

---

## 问题 8：可行的"内部推荐研发 Agent"图景——高成功率任务、所需工具/数据接入、仍属研究级的任务

### Takeaway
基于上述先例，2026 年底可用的内部推荐研发 agent 应是"有界自主的闭环工作流"而非自治研究员：高成功率任务是 kernel 生成、机械式迁移、受语义层约束的数据查询、证据收集型 RCA、以及受护栏 A/B 保护的特征/模型小迭代（AgentX 范式）；其前提是 agent 能以 API 访问代码库、特征店元数据、实验平台与指标系统，并有不可作弊的评估器。

### Cited Findings
（本节为综合，所有事实已在前述各节引用；此处仅列出直接支撑结论的关键证据）
- AgentX 的闭环四阶段（提案 → 生产代码 → 受护栏在线 A/B → harness 演化）与 Monitoring Platform / runtime playbook 设计，三周内 374 想法 → 10 上线、+0.561% 使用时长 — [arXiv 2606.26859](https://arxiv.org/html/2606.26859v2)
- RecSys Factory 主张把 agent 自主权限定在工业推荐生命周期的决策点 — [arXiv 2608.11241](https://arxiv.org/html/2608.11241v1)；Self-Evolving RecSys 以安全阈值防止生产漂移 — [arXiv 2602.10226](https://arxiv.org/abs/2602.10226)
- KernelEvolve 以持久化硬件知识库 + 多层抽象实现对自研加速器的 kernel 生成并部署于生产 DLRM — [arXiv 2512.23236](https://arxiv.org/abs/2512.23236)
- AlphaEvolve 的生产收益全部来自有确定性评估函数的问题（调度启发式、kernel tiling、XLA IR、Spanner 写放大、编译器）— [Google 博客](https://blog.google/innovation-and-ai/infrastructure-and-cloud/google-cloud/alphaevolve-on-cloud/)
- Text-to-SQL 准确率对语义层/Workspace 的强依赖（51% → 90%）— [VentureBeat](https://venturebeat.com/data-infrastructure/snowflake-launches-cortex-analyst-an-agentic-ai-system-for-accurate-data-analytics)；[Uber QueryGPT](https://www.uber.com/us/en/blog/query-gpt/)
- RCA agent 依赖确定性检索缩小候选集（Meta 数千 → 数百 → 5）与历史标注 — [Engineering at Meta](https://engineering.fb.com/2024/06/24/data-infrastructure/leveraging-ai-for-efficient-incident-response/)
- 奖励黑客风险与评估器加固需求 — [SakanaAI/robust-kbench](https://github.com/SakanaAI/robust-kbench)
- MLE-bench 省略问题定义/数据发现/指标设计，且 agent 在长程规划与调试上薄弱 — [arXiv 2410.07095](https://arxiv.org/html/2410.07095v6)

### Inferences

**按当前成功率分层（推断）**

| 层级 | 任务 | 依据 | 所需接入 |
|---|---|---|---|
| 高（可生产化） | 推荐算子/kernel 生成与多硬件适配 | KernelEvolve 100% 正确并部署；AlphaEvolve kernel 收益 | 算子规格、硬件知识库、独立计时与数值验证器、torch.compile 基线 |
| 高 | 框架/依赖版本升级、特征 DSL 与特征店 API 机械迁移 | Google 80% AI 代码、Airbnb 97%、Amazon 79% 直接合入 | 代码搜索、构建/测试系统、批量重试管道 |
| 高 | 基于语义层的特征/指标查询与数据探索 | Uber/Pinterest 35–70% 提效；Databricks 84.5% | 特征店元数据、表摘要、golden SQL、按业务域 Workspace |
| 中（人审闭环） | On-call 问答、事故证据收集与根因候选排序 | Uber Genie 48.9% helpfulness；Meta 42% top-5 | 变更/发布/实验开关日志、服务拓扑、历史事故标注 |
| 中 | 受护栏 A/B 的特征与模型小迭代闭环 | AgentX 374→10（约 2.7% 上线率）、+0.561% | 实验平台 API、自动护栏指标、生产训练管道可编程入口、playbook 存储 |
| 中 | 实验报告自动生成与维度下钻 | 无公开生产 agent 案例，但指标语义层已成熟 | 统一指标定义（Metrics Repo 类）、实验平台查询 API |
| 研究级 | 自主提出并验证新模型架构 / 新训练范式 | MLE-bench 任务不含问题定义；AI Scientist 仅 workshop 级 | — |
| 研究级 | 线上/线下指标差距的自动归因、排序回归自动定位 | 仅有 agent 用户模拟方向性结果 | — |
| 研究级 | 用 LLM agent 模拟用户替代真实 A/B | Agent A/B 仅复现方向 | — |

**组织层面推断**
- AgentX 的 2.7% 想法上线率意味着 agent 的价值来自吞吐（8 倍并发）而非单次命中率；因此内部实验平台的并发容量、流量预算与自动护栏是瓶颈，而非模型能力。
- 所有高成功率任务都依赖"确定性评估器"；推荐团队在引入 agent 前应先把评估器（数值等价、kernel 计时、SQL golden set、护栏指标）做成可被 agent 调用且防作弊的服务。
- 2026 年多个独立团队（Kuaishou、RecSys Factory、AutoLR）都把"launch review / 决策点"保留给人类，说明对推荐业务而言，有界自主是当前被验证的边界。

### Gaps
- 没有任何公开资料描述 TikTok/ByteDance 内部推荐研发 agent 的现状，以上为基于外部先例的推断。
- AgentX 的 374 个想法中失败原因分布、护栏触发率、agent 生成代码的 review 成本等关键运营数据未能从论文全文获取。
- 本次因搜索配额耗尽，未能进一步核实 AutoLR、RecSys Factory 的机构与数字；建议后续补查这三篇论文全文及 RecSys 2026 工业 track 的相关报告。
