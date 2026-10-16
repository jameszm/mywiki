# 04 知识库与 RAG 评测方法：检索质量、答案质量、新鲜度、条目级质量、回归与在线影响（截至 2026-10）

*研究说明：本笔记面向"部门级 AI 助手（面向文档/代码/配置/日志的系统迭代）+ 持续更新的内部知识库，且每轮对话与每个被检索知识条目均有日志"的评测程序设计。时间范围以 2025–2026-10 为主，2023–2024 作为基础背景；每条事实尽量标注日期与来源性质：【官方文档】工具/产品文档，【厂商声明】供应商自报性能，【独立研究】学术或第三方实证，【企业博客】公司自报案例，【二手来源】博客/摘要转述。沙箱限制：arxiv.org、docs.ragas.io、snowflake.com、uber.com、medium.com、hamel.dev、eugeneyan.com、glean.com、platform.openai.com、promptfoo.dev、docs.smith.langchain.com、arize.com、huggingface.co、zenml.io 等域名无法直接抓取；本轮共享的 WebSearch 配额在研究中途耗尽。因此部分论文仅依据搜索摘要（已标注"摘要"），部分数字无法核实者列入 Gaps。*

---

## Q1. 评测框架与指标：RAGAS / ARES / TruLens / DeepEval / Galileo / Braintrust / LangSmith / Promptfoo / Arize Phoenix / Inspect 各测什么、LLM-judge 与人工标签的一致性、2026 年推荐用法

### Takeaway
2026 年的主流框架已经收敛为两类：**指标库**（RAGAS、DeepEval、autoevals、TruLens、Phoenix evals、Promptfoo 断言、Inspect scorers）与**实验/追踪平台**（Braintrust、LangSmith、Phoenix、Galileo）。它们的 RAG 指标定义高度同构（faithfulness = 被上下文支持的 claim 占比；context precision = 按排名加权的 precision@k；context recall = 参考答案中被上下文覆盖的 claim 占比），差异主要在工程接口与 judge 校准能力。独立证据表明，通用 LLM-judge 在"groundedness/faithfulness"上与人工一致性中等偏好（F1≈0.8、Cohen's κ≈0.5），在"context relevance"上 precision 偏低（≈0.5）且比人类更宽松；系统级排名相关性高、单条样本级可靠性低。因此 2026 年的推荐用法是：用框架指标做**系统级对比与回归**，用经人工校准的**二元单失败模式 judge** 做样本级判定，不把框架默认分数当作真值。

### Cited Findings

**RAGAS（指标定义与测试集生成）**
- Faithfulness 定义：`Faithfulness = 响应中被检索上下文支持的 claim 数 / 响应中 claim 总数`，0–1；另提供 `FaithfulnesswithHHEM` 变体，用 Vectara HHEM-2.1-Open（小型开源 T5 分类器）替代 LLM 做 claim 验证 —【官方文档】[RAGAS faithfulness.md](https://github.com/explodinggradients/ragas/blob/main/docs/concepts/metrics/available_metrics/faithfulness.md)
- Context Precision 定义：`Context Precision@K = Σ_k (Precision@k × v_k) / top-K 中相关条目数`，v_k 为第 k 位是否相关；变体包括 `ContextPrecision`（LLM + reference）、`ContextUtilization`（LLM、无 reference，以生成的 response 判断每个 chunk 是否被用到；文档示例显示把一个无关 chunk 移到第一位会使分数从≈1.0 降到≈0.5）、`NonLLMContextPrecisionWithReference`（Levenshtein 等字符串相似度，需 rapidfuzz）、`IDBasedContextPrecision`（按文档 ID 匹配）；legacy API 在 0.4 弃用、1.0 移除 —【官方文档】[RAGAS context_precision.md](https://github.com/explodinggradients/ragas/blob/main/docs/concepts/metrics/available_metrics/context_precision.md)
- Context Recall：LLM 版 = `reference 中可归因到检索上下文的 claim / reference claim 总数`（用 reference 答案代替人工标注的 reference_contexts）；非 LLM 版 = `检出的相关上下文数 / reference_contexts 总数`；`IDBasedContextRecall` 按 ID 比较 —【官方文档】[RAGAS context_recall.md](https://github.com/explodinggradients/ragas/blob/main/docs/concepts/metrics/available_metrics/context_recall.md)
- Context Entities Recall = `|检索上下文中的实体 ∩ reference 实体| / |reference 实体|`，面向实体密集领域 —【官方文档】[RAGAS context_entities_recall.md](https://github.com/explodinggradients/ragas/blob/main/docs/concepts/metrics/available_metrics/context_entities_recall.md)
- Answer/Response Relevancy = 由响应反向生成 N 个问题（默认 N=3，`strictness` 可调）与原问题 embedding 的平均余弦相似度；不检查事实正确性，相关但错误的答案可得高分 —【官方文档】[RAGAS answer_relevance.md](https://github.com/explodinggradients/ragas/blob/main/docs/concepts/metrics/available_metrics/answer_relevance.md)
- Noise Sensitivity（源自 RAGChecker）= `响应中错误 claim 数 / claim 总数`，分 relevant/irrelevant 两种模式，衡量系统在相关或无关检索文档存在时犯错的频率，越低越好；需要 reference —【官方文档】[RAGAS noise_sensitivity.md](https://github.com/explodinggradients/ragas/blob/main/docs/concepts/metrics/available_metrics/noise_sensitivity.md)
- 当前指标总目录：RAG 类（Context Precision/Recall/Entities Recall、Noise Sensitivity、Response Relevancy、Faithfulness、Multimodal Faithfulness/Relevance）、Nvidia 类（Answer Accuracy、Context Relevance、Response Groundedness）、Agent 类（Topic Adherence、Tool Call Accuracy、Tool Call F1、Agent Goal Accuracy）、文本比较类（Factual Correctness、Semantic Similarity、BLEU/CHRF/ROUGE/Exact Match 等）、SQL 类（Datacompy 执行比对、SQL 等价）、通用类（Aspect Critic、Simple Criteria、Rubrics、Instance-specific Rubrics）—【官方文档】[RAGAS available_metrics index](https://github.com/explodinggradients/ragas/blob/main/docs/concepts/metrics/available_metrics/index.md)
- Agent 指标定义：Topic Adherence 的 precision/recall/F1（按"回答了的在域内/域外问题"与"应答却拒答"计算）；Tool Call Accuracy = 参数准确率 × (序列对齐则 1 否则 0)，可 `strict_order=False`；Agent Goal Accuracy 为二元，有/无 reference 两种 —【官方文档】[RAGAS agents.md](https://github.com/explodinggradients/ragas/blob/main/docs/concepts/metrics/available_metrics/agents.md)
- 测试集生成采用 Knowledge Graph 方法：文档切分为层级节点 → Extractors（LLM 或规则，如 NERExtractor）抽取信息 → Relationship Builders（如 JaccardSimilarityBuilder）建边 → Transforms 顺序/并行应用；Scenario = 节点 + 查询长度 + 查询风格（web search/chat）+ Persona；query 分为 single-hop/multi-hop × specific/abstract —【官方文档】[RAGAS test_data_generation/rag.md](https://github.com/explodinggradients/ragas/blob/main/docs/concepts/test_data_generation/rag.md)
- 入门文档给出默认 query distribution：single-hop specific 0.5、multi-hop abstract 0.25、multi-hop specific 0.25；示例文档集经 `default_transforms` 生成 48 节点/605 关系的图 —【官方文档】[RAGAS rag_testset_generation.md](https://github.com/explodinggradients/ragas/blob/main/docs/getstarted/rag_testset_generation.md)；但当前源码 `default_query_distribution` 对可用的三个 synthesizer 等权（各 1/3），与入门文档的 0.5/0.25/0.25 不一致 —【官方源码】[ragas/testset/synthesizers/__init__.py](https://github.com/explodinggradients/ragas/blob/main/src/ragas/testset/synthesizers/__init__.py)
- RAGAS README 未给出任何与人工判断一致性的声明；默认开启匿名遥测（`RAGAS_DO_NOT_TRACK` 可关）—【官方文档】[ragas GitHub](https://github.com/explodinggradients/ragas)
- 二手来源称 2026 年当前线为 0.4.x（0.4.3，2026-01），新增 `ragas.metrics.collections` API 并弃用旧类名 —【二手来源】[dev.to 2026 guide](https://dev.to/dublecc/rag-evaluation-metrics-guide-2026-faithfulness-context-precision-and-how-to-score-a-pipeline-46gi)

**ARES（Stanford，NAACL 2024）**
- 方法：对 context relevance、answer faithfulness、answer relevance 三项，用合成数据微调轻量 LM judge，再用少量人工标注做 Prediction-Powered Inference（PPI）校正并给出置信区间；论文称跨 KILT/SuperGLUE/AIS 八项任务只需"几百条"人工标注，且在 query/文档类型变化（domain shift）下仍准确 —【独立研究·摘要】[ARES arXiv 2311.09476](https://arxiv.org/abs/2311.09476v1)、[ACL Anthology](https://aclanthology.org/2024.naacl-long.20)
- README 实操参数：人工校验集"至少 50 条，理想几百条"（示例用 300 条）；示例输出 ARES 预测 0.606，CI [0.547, 0.664]，覆盖 4,421 条无标签样本；示例 judge 对真值准确率 0.789；支持 OpenAI/vLLM 本地模型作 judge —【官方文档】[ARES GitHub](https://github.com/stanford-futuredata/ARES)

**TruLens RAG Triad（TruEra/Snowflake）**
- 三元组定义：Context Relevance（每个检索 chunk 与查询相关性）、Groundedness（把响应拆成 claim，逐条在上下文中找证据）、Answer Relevance（最终响应是否回答了输入）；三项均合格时"在知识库的范围内可视为无幻觉（hallucination free up to the limit of its knowledge base）" —【官方文档】[TruLens rag_triad.md](https://github.com/truera/trulens/blob/main/docs/getting_started/core_concepts/rag_triad.md)
- TruLens README 自报（2025–2026）："TruLens judges 开箱即对人工标注做了校准"；Groundedness 在 LLM-AggreFact 上 F1 0.81、在 11,000 条留出集上优于 Bespoke-MiniCheck-7B；Context Relevance NDCG@5 0.93，对抗性近似复制段落的胜负比 4.2:1（次优工具 3.3:1，来源为 AIMultiple 比较）；agent 错误检出 267/281（95%）vs 基线 trace judge 55%（引 arXiv 2510.08847）—【厂商声明】[trulens GitHub](https://github.com/truera/trulens)
- Snowflake 工程博客的基准（搜索摘要）：Groundedness 在 LLM-AggreFact 上 F1 81%、precision 78%、recall 85%、Cohen's κ 0.54；Context Relevance 在 TREC-DL 上 F1 64%、precision 51%、recall 87%；Answer Relevance 在 HotpotQA 评测；默认输出刻度 0–3；实验默认 judge 为 GPT-4o —【厂商声明】[Snowflake: Benchmarking LLM-as-a-Judge for the RAG Triad](https://www.snowflake.com/en/engineering-blog/benchmarking-LLM-as-a-judge-RAG-triad-metrics/)
- Snowflake 后续"eval-guided optimization"：对 judge 提示做优化后 Groundedness precision 提升约 16%（recall 降 2.5%，LLM-AggreFact F1 +8%）；Context Relevance precision +4.26%、recall −3.7%，TREC-DL F1 +2.4% —【厂商声明】[Snowflake: Eval-Guided Optimization of LLM Judges](https://www.snowflake.com/en/engineering-blog/eval-guided-optimization-llm-judges-rag-triad/)

**DeepEval（Confident AI）**
- README 指标清单：RAG（Answer Relevancy、Faithfulness、Contextual Recall/Precision/Relevancy，以及四项平均的 RAGAS 复合分）；Agentic（Task Completion、Tool Correctness、Goal Accuracy、Step Efficiency、Plan Adherence/Quality、Tool Use、Argument Correctness）；多轮（Knowledge Retention、Conversation Completeness、Turn Relevancy、Turn Faithfulness、Role Adherence）；MCP 指标；G-Eval（自定义标准）、DAG（图式确定性 judge 构建器）、JevEval（称输出"calibrated probabilities"）；pytest 风格 `assert_test` + `deepeval test run`；合成数据生成器支持单轮/多轮；README 未提供任何人工一致性数据 —【官方文档】[deepeval GitHub](https://github.com/confident-ai/deepeval)
- 入门文档：所有指标输出 0–1，阈值默认 0.5；contextual precision/recall 需要 expected output —【官方文档】[deepeval getting-started-rag](https://deepeval.com/docs/getting-started-rag)

**Galileo（ChainPoll / Luna / RAGBench）**
- ChainPoll（2023-10）：聚合带 CoT 的多次布尔判断；自建 RealHall 基准上聚合 AUROC 0.781，SelfCheck-BERTScore 0.673，随机 0.500 —【厂商声明（论文）】[ChainPoll arXiv 2310.18344](https://arxiv.org/pdf/2310.18344)、[Galileo blog](https://galileo.ai/blog/chainpoll)
- Luna 评测基础模型（2024-06）：厂商称比用 GPT-3.5 评测"便宜 97%、快 11 倍、准 18%"，高风险客户按客户微调以达 95%+ 准确率；未见独立第三方基准 —【厂商声明】[SiliconANGLE 报道](https://siliconangle.com/2024/06/06/ai-accuracy-startup-galileos-new-llm-family-designed-evaluate-llms/)、[AIwire](https://aiwire.net/2024/06/06/galileo-introduces-first-of-its-kind-evaluation-foundation-models-for-enterprise-genai-evaluations)
- RAGBench（Galileo，2024）：10 万样本、五个行业域（生物医学、通识、法律、客服、金融），TRACe 框架四指标 uTilization / Relevance / Adherence / Completeness；论文结论"LLM-based RAG 评测方法难以与微调的 RoBERTa 竞争" —【独立研究（厂商作者）·摘要】[RAGBench arXiv 2407.11005](https://arxiv.org/abs/2407.11005v2)

**Braintrust / autoevals**
- autoevals 开源评分器：LLM-as-judge（Battle、Closed QA、Humor、Factuality、Moderation、Security、Summarization、SQL、Translation、微调二分类器）、RAG（Context precision/relevancy/recall/entity recall、Faithfulness、Answer relevancy/similarity/correctness）、启发式（Levenshtein、Exact match、Numeric diff、JSON diff）、Embedding similarity；`LLMClassifier` 支持 `use_cot=True` 并把选项映射为分数；输出 0–1 的 `Score` 附 rationale；多数评测改编自 OpenAI evals —【官方文档】[autoevals GitHub](https://github.com/braintrustdata/autoevals)
- Anthropic 的 agent 评测文章把 Braintrust（离线评测+可观测+autoevals）、LangSmith、Langfuse（自托管）、Arize Phoenix/AX、Harbor（容器化 agent 试验与基准注册）列为可选框架，并强调"框架的价值取决于你跑的任务与 grader" —【官方文档】[Anthropic: Demystifying evals for AI agents, 2026-01-09](https://anthropic.com/engineering/demystifying-evals-for-ai-agents)

**LangSmith**
- 概念文档：Dataset（examples/splits/versions，可来自人工撰写、生产 trace（按用户反馈/启发式/LLM 标注筛选）、合成）；Evaluator 四类（human、heuristic、LLM-as-judge、pairwise）；离线评测含 benchmarking、unit tests（CI 中缓存 LLM 调用）、regression tests（对比视图标红/绿）、backtesting（把生产日志回放到新版本）、pairwise；在线评测"无 dataset、无 reference outputs"，用于监控与为离线集挑样本；Annotation queues 聚合待审 run；RAG 建议：有 reference 的 correctness 离线跑，reference-free 的 faithfulness/helpfulness/document relevance 在线跑；Agent 评测分 final response / single step / trajectory 三层 —【官方文档】[LangSmith evaluation concepts](https://github.com/langchain-ai/langsmith-docs/blob/main/docs/evaluation/concepts/index.mdx)

**Promptfoo**
- RAG 评测指南：建议检索与生成分开测；检索用 Python provider 脚本 + `contains-all` 等确定性断言，可并列多个向量库对比；生成端用 `factuality`、`answer-relevance`、`similar`、`contains`、`llm-rubric`；上下文指标 `context-faithfulness`、`context-relevance`、`context-recall`，上下文可由 `contextTransform` 从 provider 响应中抽取；端到端脚本作为 provider 以捕获回归；跨语言时避免 `context-recall` 与字符串指标 —【官方文档】[Promptfoo evaluate-rag](https://github.com/promptfoo/promptfoo/blob/main/site/docs/guides/evaluate-rag.md)
- `context-faithfulness` 实现：抽取响应 claim → 逐条对照 context → 分数 = 支持 claim/总 claim，默认阈值 0.5（示例用 0.8–0.9）；局限：依赖 judge 质量、可能漏隐含 claim、长上下文精度下降 —【官方文档】[context-faithfulness.md](https://github.com/promptfoo/promptfoo/blob/main/site/docs/configuration/expected-outputs/model-graded/context-faithfulness.md)
- CI/CD：`--fail-on-error`，或用 jq 读取 `results.json` 计算通过率并设门槛（示例 95%）；按 prompt 文件哈希缓存；`--share` 产出可分享链接；JUnit XML 输出；`--tag` 附加 git sha/run id；文档未提供基线对比功能 —【官方文档】[Promptfoo ci-cd.md](https://github.com/promptfoo/promptfoo/blob/main/site/docs/integrations/ci-cd.md)

**Arize Phoenix**
- README：OpenTelemetry/OpenInference 追踪（Python/TS/Java/Go SDK），evals 包含"RAG relevance、answer relevance 等"，版本化数据集 + Experiments；许可证 Elastic License 2.0（第三方比较中有人误记为 Apache 2.0）—【官方文档】[phoenix GitHub](https://github.com/Arize-ai/phoenix)；许可证冲突见【二手来源】[Arize 平台对比](https://arize.com/resources/llm-and-agent-evaluation-platforms/)

**Inspect（UK AI Security Institute）**
- Task = dataset + solver + scorer；`model_graded_qa()`（开放式）与 `model_graded_fact()`（事实是否出现）默认要求 CoT 后输出 `GRADE: C/I`，`partial_credit` 折算 0.5；grader 可按 `model_roles={"grader": ...}` 绑定并与被测模型分离；传入模型列表即组成 panel，默认 `majority` 归约（过半才判定，不可解析的投票弃权）；默认 `grade_pattern` 取最后一个 `GRADE:` 以抵御提示注入，并中和 `[BEGIN DATA]/[END DATA]` 标记；建议 temperature=0 + seed，并多 epoch 检查评分方差 —【官方文档】[Inspect model-graded.qmd](https://github.com/UKGovernmentBEIS/inspect_ai/blob/main/docs/model-graded.qmd)、[inspect.aisi.org.uk](https://inspect.aisi.org.uk/model-graded.html)

**OpenAI evals（模板分类，作为 judge 输出格式的参考）**
- 基础模板 Match/Includes/FuzzyMatch/JsonMatch；模型评分模板 `fact`（A 子集/B 超集/C 相等/D 矛盾/E 差异无关）、`closedqa`（相关/简洁/正确 yes-no）、`battle`（两两对比）；`eval_type` 推荐 `cot_classify`（先推理后给选项）—【官方文档】[openai/evals eval-templates.md](https://github.com/openai/evals/blob/main/docs/eval-templates.md)

**LLM-judge 与人工一致性的独立证据**
- MT-Bench：GPT-4 judge 与人类一致性"超过 80%"，与人−人一致性相当；发布 3.3K 条人工标注；推荐 single-answer grading（10 分制）—【独立研究】[FastChat llm_judge README](https://github.com/lm-sys/FastChat/blob/main/fastchat/llm_judge/README.md)
- TREC 2024 RAG Track 相关性标注（UMBRELA）：77 个 run / 19 支队伍，UMBRELA 自动标注诱导的系统排名与 NIST 人工排名在 nDCG@20/nDCG@100/Recall@100 上高度相关；人工在环版本没有带来明显收益；人类比 UMBRELA 更严格 —【独立研究·摘要】[arXiv 2411.08275](https://arxiv.org/abs/2411.08275v1)
- TREC 2024 RAG Track 引用支持（support）评测：GPT-4o 与人工 judge 在 run 级 Kendall τ > 0.79；分歧研究中独立第三方更同意 GPT-4o（Cohen's κ 0.27 vs 人工 0.07）—【独立研究·摘要】[arXiv 2504.15205](https://arxiv.org/html/2504.15205)
- AutoNuggetizer：全自动 nugget 评测与人工变体在 run 级强一致，仅自动化 assignment 时更强；**per-topic 相关性较低，不适合单条答案的细粒度调试** —【独立研究·摘要】[arXiv 2504.15068](https://arxiv.org/abs/2504.15068v1)
- Glean（企业搜索/助手厂商）给出的评分器经验：需要数值标签时"低精度刻度（0–3）优于高精度刻度（0–100）" —【企业博客·摘要】[Glean AI Evaluator](https://glean.com/blog/glean-ai-evaluator)
- Anthropic 平台文档对评分方法排序："Code-based 最快最可靠最可扩展但缺乏细腻；Human 最灵活高质量但慢且贵，能免则免；LLM-based 快、灵活、可扩展，适合复杂判断，先测可靠性再扩展"；LLM 评分三条建议：详细清晰的 rubric、输出经验性/具体结论（如仅输出 correct/incorrect 或 1–5）、用 thinking 鼓励先推理；并注明"最佳实践是用不同于生成模型的模型来评分" —【官方文档】[Claude docs: develop-tests](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests)

### Inferences
- 对本场景（文档/代码/配置/日志）而言，RAGAS/DeepEval/autoevals 的 RAG 指标在"系统 A vs B"的相对比较上足够可靠，但**样本级 pass/fail 不应直接用默认 judge**；TREC 证据（run 级 τ>0.79、per-topic 相关性低）与 Snowflake 的 context relevance precision≈0.5 共同说明：用框架分数做发布门槛前，必须按 Q3 的方法对 judge 做本地校准。
- ARES 的 PPI 思路（小人工集 + 大无标签集 + 置信区间）最适合"每轮对话都有日志"的场景：用几百条人工标注把 judge 在全量日志上的估计偏差校正掉，并给出区间，这与 Hamel 体系的 Rogan-Gladen 偏差校正（见 Q3）是同一数学。
- 工具选型建议：追踪与数据集管理（Phoenix/LangSmith/Braintrust 任一，注意 Phoenix 为 ELv2 许可）+ 指标实现（RAGAS collections API 或 autoevals）+ CI 门槛（Promptfoo 或 Inspect 式 scorer）+ 自研 judge 校准脚本（TPR/TNR、bootstrap CI）。RAGAS 文档与源码在默认 query 分布上不一致，说明合成集的分布应显式配置而非依赖默认值。

### Gaps
- RAGAS 原论文在 WikiEval 上的人工一致性数字（faithfulness/answer relevance/context relevance 与人工的 agreement）无法在沙箱核实（arXiv 2309.15217 不可达），本笔记未引用。
- RAGBench 中 LLM judge 与微调 RoBERTa/DeBERTa 的具体 AUROC/RMSE 数字未能获取（仅摘要结论）。
- Phoenix 预置评测器（hallucination、Q&A correctness、retrieval relevance）对人工标注集的 precision/recall 基准表未能抓取（arize.com 不可达）。
- Databricks 2023 年"LLM auto-eval best practices for RAG"博客中关于 GPT-4 judge 与人工一致性（常被引为 >80%）及 0–3 刻度建议未能核实（databricks.com 不可达）。
- Braintrust 官方文档（Eval(data, task, scores) 结构、在线打分）未能抓取，仅有 autoevals README 与二手比较。

---

## Q2. 检索评测：recall@k / precision@k / MRR / nDCG、agentic "hit rate"、从日志构建相关性标签（点击/引用伪标签、LLM 标注与校准）、multi-hop、reranker 与 query rewriting、DeepSearch 循环评测

### Takeaway
检索评测应以 **Recall@k 为第一指标**（未检出的内容生成器无法弥补），reranking 用 Precision@k/nDCG，单事实查找用 MRR，multi-hop 用"两跳 Recall@k"；相关性标签可由 LLM（UMBRELA 式 0–3 刻度）大规模生成且在系统级排名上与人工高度一致，但需用少量人工标注校准其"比人类宽松"的偏差。Agentic/DeepSearch 场景需把检索评测从"单次 top-k"扩展为"轨迹级"：是否最终命中黄金证据、步数/成本、证据覆盖率（nugget recall）与无效搜索恢复率。

### Cited Findings

**指标选择与阈值（实践指南）**
- "Recall@k：top-k 中找到的相关文档比例，首轮检索优先；Precision@k：top-k 中相关比例，用于 reranking；MRR：首个相关文档出现得多早，适合单事实查找；NDCG@k：分级相关度；两跳 Recall@k：multi-hop 查询中两个真值 chunk 同时出现在 top-k 的比例"；建议事实查找 k=1–2，综合类查询 k=5–10；并先做 chunking 网格搜索（示例：256 token/128 overlap 得 Recall@5 0.89、NDCG@5 0.77，128 token 无 overlap 为 0.82）—【实践指南】[ai-evals-course evaluate-rag SKILL.md](https://github.com/ai-evals-course/evals-skills/blob/main/skills/evaluate-rag/SKILL.md)
- 同一指南的诊断模式："context relevance 高 + faithfulness 高 + answer relevance 低 → 生成器关注了正确文档的错误部分；context relevance 高 + faithfulness 低 → 幻觉/误读；context relevance 低 → 检索问题（修 chunking/embedding/查询预处理）"；常见错误包括"只用一个端到端正确率指标""过拟合合成数据，需定期用真实查询验证" —【实践指南】[同上](https://github.com/ai-evals-course/evals-skills/blob/main/skills/evaluate-rag/SKILL.md)
- RAGAS 提供 ID-based precision/recall（直接比较检索到的文档 ID 与参考 ID），适合有条目级日志的系统 —【官方文档】[RAGAS context_precision.md](https://github.com/explodinggradients/ragas/blob/main/docs/concepts/metrics/available_metrics/context_precision.md)

**LLM 相关性标注（替代人工 qrels）**
- UMBRELA 工具：以 LLM 给 query-document 对打 0–3 四级相关性，复现 Bing 评估器提示（`bing`/`basic` 两种模板），支持 GPT/Gemini/HF/开源模型与 `EnsembleJudge` 多数投票；`umbrela evaluate` 可直接对 TREC DL qrels 评估 —【官方文档】[castorini/umbrela](https://github.com/castorini/umbrela)
- TREC 2024 RAG：UMBRELA 系统排名与人工高度相关，人工比 LLM 更严格，人工在环未带来收益 —【独立研究·摘要】[arXiv 2411.08275](https://arxiv.org/abs/2411.08275v1)
- Nugget 评测工具链：`nuggetizer create` 从相关文档（默认只用 judgment≥2 的段落）生成带 vital/okay 重要性的 nugget，`assign` 把 nugget 判为 full(1.0)/partial(0.5) 支持；输出 `strict_vital_score`、`strict_all_score`、`vital_score`、`all_score` —【官方文档】[castorini/nuggetizer](https://github.com/castorini/nuggetizer)
- Glean 指出传统点击指标不适用于"自己生成答案、无需用户进一步交互"的助手，且 up/down 投票只来自部分用户、有偏 —【企业博客·摘要】[Glean AI Evaluator](https://glean.com/blog/glean-ai-evaluator)
- LangSmith 的 dataset 构建方式之一是"从生产 trace 中按用户反馈、启发式或 LLM 标注筛选" —【官方文档】[LangSmith concepts](https://github.com/langchain-ai/langsmith-docs/blob/main/docs/evaluation/concepts/index.mdx)

**Multi-hop**
- MultiHop-RAG（COLM 2024）：2,556 条查询，每条的证据分布在 2–4 个文档中，查询涉及文档元数据；提供检索与 QA 两套评测脚本 —【独立研究】[MultiHop-RAG GitHub](https://github.com/yixuantt/MultiHop-RAG)
- FRAMES（Google/Harvard，2024-09）：824 条 multi-hop 问题，每题需 2–15 篇 Wikipedia 文章，约 36% 含多重约束；无检索准确率 0.40，迭代生成/精炼查询的多步检索流水线提升到≈0.66 —【独立研究】[FRAMES arXiv 2409.12941](https://arxiv.org/html/2409.12941v1)

**Reranker 与 query rewriting 评测**
- BRIGHT 显示 MTEB 榜首模型 SFR-Embedding-Mistral（MTEB 59.0）在推理密集型检索上 nDCG@10 仅 18.3 —【独立研究】[BRIGHT arXiv 2407.12883](https://arxiv.org/pdf/2407.12883)
- 2025-11 "Practical RAG Evaluation" 提出诊断框架：区分受"候选池覆盖（coverage，query rewriting 有效）"限制还是受"排序（ordering，更强 reranking 有效）"限制 —【独立研究·摘要】[arXiv 2511.09545](https://arxiv.org/html/2511.09545v1)
- 2025-08 对 LLM reranker 的实证研究引入 2025-04 之后的新查询集，以规避 TREC DL/BEIR 被预训练污染 —【独立研究·摘要】[arXiv 2508.16757](https://arxiv.org/pdf/2508.16757)
- 实践者报告：reranker 提升了 NDCG 与 MRR 但没有改善端到端 QA 结果 —【二手来源（论坛）】[Arize community thread](https://community.arize.com/x/phoenix-support/msg_iAkTeJVE45rC/evaluating-rag-with-rerankers-best-practices-and-e)
- RaFe（2024）评估 query rewriting 时同时比较"是否对检索文档 rerank 后取 top-5" —【二手来源】[RaFe 评述](https://www.themoonlight.io/tw/review/rafe-ranking-feedback-improves-query-rewriting-for-rag)

**Agentic / DeepSearch 循环**
- 2026 SoK 综述提出 Progress Rate（推动任务前进的推理步比例）与 Effective Information Rate（检索材料被利用程度），并指出 BLEU/ROUGE 无法区分"靠逻辑答对"与"靠运气答对" —【独立研究·摘要】[SoK Agentic RAG arXiv 2603.07379](https://arxiv.org/pdf/2603.07379)
- CRISP（2026）：当某步的观察包含黄金证据文档 ID 时记为"evidence-bearing step"，仅在最终答案正确的轨迹上分析关键步 —【独立研究·摘要】[arXiv 2608.01867](https://arxiv.org/pdf/2608.01867)
- RAVine（2025-07）：对 agentic search 用按查询聚类的 nugget 评 completeness/faithfulness，并把 latency 与 cost 作为效率指标 —【独立研究·摘要】[arXiv 2507.16725](https://arxiv.org/pdf/2507.16725)
- "Rethinking Agentic RAG"（2026）：按搜索意图分组检索动作，度量 query 改写是否真的改变了返回证据、以及 agent 是否从失败搜索中恢复；并通过移除黄金段落测 refusal/hallucination/"gold leak"（证据被移除仍答对）率 —【独立研究·摘要】[arXiv 2605.27123](https://arxiv.org/pdf/2605.27123)
- Anthropic 对 research agent 的评测建议：组合 groundedness（claim 有来源）、coverage（必含事实齐全）、source-quality（来源权威）三类 grader，LLM rubric 需频繁对专家校准；推荐 BrowseComp —【官方文档】[Anthropic Demystifying evals](https://anthropic.com/engineering/demystifying-evals-for-ai-agents)
- BrowseComp（OpenAI，2025-04）：1,266 道多跳难检索题；Deep Research 51.5%，o1（无浏览）9.9%，GPT-4o 带浏览 <2%；OpenAI 注明 Deep Research 针对该类任务训练过；带浏览的模型对错误答案过度自信；推理算力增加提升准确率，Best-of-N 聚合最强 —【官方/二手】[openai.com/index/browsecomp](https://openai.com/index/browsecomp/)、[W&B 报道](https://wandb.ai/byyoung3/ml-news/reports/OpenAI-s-new-browsing-benchmark-BrowseComp--VmlldzoxMjI4MTE0Nw)

### Inferences
- 对"每个被检索条目都有日志"的系统，可直接实现 **ID-based recall/precision**：golden set 每题标注黄金条目 ID 集合（而非文本），检索评测完全确定性、无 judge 成本；LLM-judge 只用于补标未覆盖的新条目。
- 伪标签构建的可行分层：(1) 引用伪标签——答案中被引用且用户给出 Resolved/Helpful 的条目记为正例（Uber Genie 式反馈，见 Q7）；(2) 点击/展开伪标签权重应低于引用，因为 Glean 指出助手场景点击信号稀疏；(3) 对正例候选用 UMBRELA 式 0–3 LLM 标注，再抽样 100–300 条人工校准（ARES/PPI），并记录"LLM 比人宽松"的偏差方向。
- agentic "hit rate" 的定义建议为 `轨迹任一步的检索结果 ⊇ 黄金条目 ID` 的比例（CRISP 的 evidence-bearing step 思路），并同时报告"首次命中步数""总工具调用数""token 成本"与"gold-leak 率"（黄金条目移除后仍答对，意味着答案来自参数知识或污染）。
- reranker/查询改写的离线收益（nDCG/MRR）与端到端 QA 可能脱节（Arize 论坛案例），所以每次检索侧变更都应同时跑端到端 golden set，并按 2511.09545 的框架先判定瓶颈是 coverage 还是 ordering。

### Gaps
- 未找到 2025–2026 年关于"点击/引用伪标签 vs LLM 标签 vs 人工标签"在企业内部助手场景的定量对比研究（搜索配额耗尽前未能完成该检索）。
- UMBRELA 论文的文档级 Cohen's κ 与具体 τ 值未能获取（仅系统级"高度相关"的定性结论）。
- MultiHop-RAG 的查询类型分布（inference/comparison/temporal/null）与 Hits@k 结果未能从 README 获取。
- BRIGHT 中"LLM 推理改写查询 +nDCG"的具体增益数字与当前榜单未能核实（项目站点不可达）。

---

## Q3. 答案评测：correctness / groundedness / completeness / abstention / 有害建议检查；LLM-as-judge 设计（rubric、pairwise、二元 pass-fail、position bias、self-preference）；人工误差分析流程与样本量

### Takeaway
2025–2026 年实践共识（Hamel Husain/Shreya Shankar 课程体系、Anthropic、OpenAI evals、Inspect）是：**每个 judge 只判一个失败模式、输出二元 Pass/Fail、先写 critique 再给 verdict、few-shot 来自与 dev/test 分离的训练切分**；judge 上线前需对 ~50 Pass/~50 Fail 的专家标注计算 TPR/TNR（目标 >90%，底线 >80%），并用 Rogan-Gladen 公式校正全量估计。误差分析以"约 100 条 trace 达到饱和"为经验目标，采样强调多样性（聚类代表 + 随机）而非频率估计。abstention 是独立能力：AbstentionBench 显示 reasoning 微调平均使弃答能力下降 24%，必须单独建"应弃答"用例。

### Cited Findings

**误差分析（error analysis）流程与样本量**
- eval-audit："误差分析约 100 条 trace 是饱和的粗略目标"；"评估器若非来自误差分析，只会度量通用品质（helpfulness、coherence）而非真实失败模式"；"生产中的 judge 没有验证数据是严重问题" —【实践指南】[eval-audit SKILL.md](https://github.com/ai-evals-course/evals-skills/blob/main/skills/eval-audit/SKILL.md)
- error-discovery 采样："先看 5–10 条了解数据形态；KMeans 聚 6–10 簇；初始样本 15–25 条（数据集 >50 时），其中聚类代表约 60–70%（每簇离质心最近的 1–2 条，混合类别），随机样本约 30–40%；去重；优先多样性——目标是发现失败模式，不是估计其频率"；review-loop："当新发现速率下降时建议停止或收窄焦点" —【实践指南】[error-discovery SKILL.md](https://github.com/ai-evals-course/evals-skills/blob/main/skills/error-discovery/SKILL.md)、[review-loop.md](https://github.com/ai-evals-course/evals-skills/blob/main/skills/error-discovery/review-loop.md)
- Anthropic："读 transcript。不读大量试验的 transcript 与评分就无法知道 grader 是否工作……失败应当显得公平：清楚 agent 错在哪、为什么" —【官方文档】[Anthropic Demystifying evals](https://anthropic.com/engineering/demystifying-evals-for-ai-agents)
- Lenny's Newsletter 对 Hamel 的访谈要点：二元评估比任意质量分更有用；一个失败模式一个 judge；"Helpfulness: 4.2"之类的复合分难以行动 —【二手来源】[Lenny's Newsletter](https://www.lennysnewsletter.com/p/evals-error-analysis-and-better-prompts)、[ChatPRD 摘要](https://chatprd.ai/how-i-ai/hamel-husains-guide-to-ai-evals-with-error-analysis)

**Judge 设计与校准**
- write-judge-prompt 四要素：(1) 任务与评估标准（"每个 judge 只检查一件事"）；(2) 明确 Pass/Fail 定义（来自误差分析的失败模式描述）；(3) few-shot：2–4 个人工标注示例，含至少一个边界案例，"4–8 个后性能趋平"；(4) 结构化输出且"critique 先于 verdict"；"Likert 分数听起来精确但无法校准；需要严重度时用多个二元 judge"；"单一 judge 覆盖多维度会产生不可行动的判决"；"用尽代码检查后再用 judge"；"从最强模型开始，校准确认后再降成本"；"judge 只喂它需要的输入" —【实践指南】[write-judge-prompt SKILL.md](https://github.com/ai-evals-course/evals-skills/blob/main/skills/write-judge-prompt/SKILL.md)
- validate-evaluator："每个失败模式约 100 条二元标注，~50 Pass + ~50 Fail（即使真实分布偏斜也保持均衡）""标签必须来自领域专家而非外包标注员"；切分 train 10–20%（few-shot 来源）/ dev 40–45%（迭代）/ test 40–45%（最终测量，只跑一次）；用 TPR（人工 Pass 中 judge 也 Pass）与 TNR（人工 Fail 中 judge 也 Fail）而非 accuracy/precision/recall；偏差校正 `θ̂ = (p_obs + TNR − 1)/(TPR + TNR − 1)`（示例 TPR 0.92、TNR 0.88、p_obs 0.80 → θ̂≈0.85），bootstrap 给 2.5/97.5 分位区间；目标 TPR、TNR >90%，底线 >80%；"低于约 60 条样本置信区间很宽" —【实践指南】[validate-evaluator SKILL.md](https://github.com/ai-evals-course/evals-skills/blob/main/skills/validate-evaluator/SKILL.md)
- eval-audit 反模式 5："类别不平衡时，总是判 Pass 的 judge 也能有高 accuracy 却抓不到任何失败；Cohen's κ 只用于人−人一致性" —【实践指南】[eval-audit SKILL.md](https://github.com/ai-evals-course/evals-skills/blob/main/skills/eval-audit/SKILL.md)
- write-code-eval：可用代码判定的失败包括结构（解析必填字段）、文本模式、**引用（"比较被引用 ID 与被检索 ID"以抓"引用了未检索到的文档"）**、工具调用（对照 schema 或在安全环境执行）、数值；混合型失败"客观部分用代码，其余用 judge" —【实践指南】[write-code-eval SKILL.md](https://github.com/ai-evals-course/evals-skills/blob/main/skills/write-code-eval/SKILL.md)
- EvalGen（UIST 2024）提出"criteria drift"：人们在给输出打分的过程中会改变评分标准，部分标准依赖于观察到的具体输出而非可先验定义，这对"评估独立于观察模型输出"的假设提出严重质疑 —【独立研究】[Who Validates the Validators, arXiv 2404.12272](https://arxiv.org/pdf/2404.12272)、[UIST 版本](https://people.eecs.berkeley.edu/~bjoern/papers/shankar-validators-uist2024.pdf)
- Eugene Yan "Product Evals in Three Simple Steps"（2025-11）：标注一些数据 → 对齐 LLM 评估器 → 每次变更跑评测 harness；一则中文转述称其把评估器对齐当作标准 ML 问题，dev/test 按 75%/25% 切分 —【二手来源】[博客索引](https://minifeed.net/blogs/NTyMhN)、[人人都是产品经理转述](https://www.woshipm.com/ai/6338088.html)
- Anthropic grader 设计："能确定性就确定性，必要时 LLM，人工用于验证""评分看产出而非路径""多组件任务给部分分""给 LLM 一个 Unknown 出口以减少幻觉""结构化 rubric，每个维度用独立的 judge 而不是一个 judge 评所有维度""grader 要抗 hack"；CORE-Bench 案例：Opus 4.5 从 42% 修正评分 bug 后到 95%（刚性评分如期望 96.124991 却惩罚 96.12、规格模糊、不可复现的随机任务）—【官方文档】[Anthropic Demystifying evals](https://anthropic.com/engineering/demystifying-evals-for-ai-agents)
- Inspect 的 grader 工程细节（多 grader 多数投票、最后一个 GRADE 生效、temperature 0 + seed、多 epoch 看方差）见 Q1 —【官方文档】[Inspect model-graded](https://github.com/UKGovernmentBEIS/inspect_ai/blob/main/docs/model-graded.qmd)

**Judge 偏差的独立证据**
- Position bias（Shi et al.，IJCNLP-AACL 2025）：15 个 judge、>150,000 评测实例；位置偏差非随机、因 judge 与任务而异；受提示组件长度影响弱，受候选质量差距影响强 —【独立研究】[ACL Anthology 2025.ijcnlp-long.18](https://aclanthology.org/2025.ijcnlp-long.18/)
- Self-preference（Wataoka et al.，2024-10/2025-06 修订）：GPT-4 自我偏好分最高 0.520；偏好与低困惑度相关，LLM 对低困惑度文本的偏好远强于人类 —【独立研究】[alphaxiv 2410.21819](https://www.alphaxiv.org/abs/2410.21819)
- 2026 年一项研究（arXiv 2603.03319，ID 未能核实）称 judge 与人类一致率约 70%，并观察到 claude-sonnet-4.5 在 pairwise 中 >60% 偏好 Response B —【独立研究·摘要，未核实】[arXiv 2603.03319](https://arxiv.org/pdf/2603.03319)
- W&B 文章引用 MT-Bench/Chatbot Arena：强 judge（GPT-4）与人类偏好一致 >80% —【二手来源】[W&B Exploring LLM-as-a-Judge](https://wandb.ai/site/articles/exploring-llm-as-a-judge/)
- LLM-as-a-Judge 综述（arXiv 2411.15594）列出 self-enhancement 等任务无关偏差，并指出 judge 表现不是静态的（3 月版可接受、6 月版因安全微调而惩罚）—【独立研究·摘要】[arXiv 2411.15594](https://arxiv.org/html/2411.15594v6)

**Abstention / "I don't know" 校准**
- AbstentionBench（Meta FAIR，NeurIPS 2025）：20 个数据集、6 类弃答场景（从上下文不足到过期数据/stale data），含 FreshQA、SituatedQA、SQuAD 2.0、FalseQA 等；20 个前沿模型评测结论："弃答是未解决问题，扩大模型规模几乎无助"；"reasoning 微调平均使弃答能力下降 24%"，包括其训练领域的数学/科学；精心设计的 system prompt 可提高弃答但不解决根本问题；弃答与正确性由"human-validated"的 LLM judge 判定 —【独立研究】[AbstentionBench GitHub](https://github.com/facebookresearch/AbstentionBench)、[arXiv 2506.09038](https://arxiv.org/abs/2506.09038v1)
- CRAG 评分把"missing（弃答）"记 0、"incorrect/hallucinated"记 −1、正确 +1，以此奖励弃答优于幻觉 —【官方文档】[facebookresearch/CRAG README](https://github.com/facebookresearch/CRAG)
- LongMemEval 把 abstention 列为五项记忆能力之一，`_abs` 题在检索评测中跳过 —【独立研究】[LongMemEval GitHub](https://github.com/xiaowu0162/LongMemEval)
- Anthropic 平台文档示例：隐私保护用"是/否"二元 LLM 判定（500 条病人查询，含显式/假设/隐式 PHI 边界用例）—【官方文档】[Claude docs develop-tests](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests)

**Groundedness 的替代检测器**
- Vectara HHEM 幻觉排行榜（2026-09-22 更新）：对 >7,700 篇文章做"仅依据原文"摘要，幻觉率 = 100 − 事实一致率；最低者 antgroup/finix_s1_32b 1.8%、gpt-5.4-nano 3.1%、gemini-2.5-flash-lite 3.3%；方法论警示：仅覆盖摘要场景、由模型（HHEM-2.3）而非人工打分、抽取式摘要可"刷"到 0%、仅英文、数据集不公开 —【厂商声明（带方法论说明）】[vectara/hallucination-leaderboard](https://github.com/vectara/hallucination-leaderboard)
- RAGAS 的 `FaithfulnesswithHHEM` 可用 HHEM-2.1-Open 替代 LLM 做 claim 验证（成本更低）—【官方文档】[RAGAS faithfulness.md](https://github.com/explodinggradients/ragas/blob/main/docs/concepts/metrics/available_metrics/faithfulness.md)

### Inferences
- 对运维/runbook 场景的"有害建议"检查，可按 write-code-eval 原则拆分：代码层检查（命令是否命中破坏性操作黑名单、是否引用了未检索到的条目、是否缺少前置确认语句）+ 二元 judge（"是否在缺乏环境信息时给出了不可逆操作建议"），并把"应弃答/应追问"用例按 AbstentionBench 的六类场景（未知答案、上下文不足、错误前提、主观、过期信息等）分层构建。
- 位置偏差与自我偏好意味着：pairwise 比较必须交换顺序双跑；judge 模型应与生成模型不同族（Anthropic 文档也如此建议），或至少在校准集上检验 self-preference。
- 由于 judge 分数在 run 级可靠、样本级不可靠（TREC 证据），发布门槛应以"校准后的二元 judge 的 θ̂ 及其置信区间"而非原始 judge 均值表达。

### Gaps
- Hamel Husain 本人博文（"Your AI Product Needs Evals"、"Creating a LLM-as-a-Judge That Drives Business Results"、evals FAQ）原文不可达，其中的"critique shadowing""单一主要领域专家"等细节仅有课程 skill 文件与二手转述；本笔记以 skill 文件为准。
- Eugene Yan 2024 年"Evaluating the Effectiveness of LLM-Evaluators"原文不可达，未能引用其对各类评估器的量化回顾。
- Chip Huyen《AI Engineering》第 3–4 章关于 AI judge 的具体建议只能确认章节结构与三类方法（functional correctness / similarity / AI-as-judge）—【二手来源】[ODSC 摘要](https://opendatascience.com/building-ai-applications-with-foundation-models-key-insights-from-chip-huyen/)，细节未核实。
- 未找到针对"运维指令类回答的有害建议"专门 benchmark 或已发表的检查清单。

---

## Q4. Golden set 构建与维护：从对话日志挖掘（采样、去重、隐私）、合成生成（RAGAS/evol-instruct 式、从文档出题与难度控制）、规模指导（Anthropic 20–50 题起步）、按知识类型/新鲜度/难度分层、KB 更新时防止陈旧（as-of 版本化期望）

### Takeaway
起步规模的权威建议是 **20–50 个来自真实失败的任务**（Anthropic，2026-01），随后以"每个失败模式约 100 条、~50/50 均衡"的粒度扩充；真实日志优先（≥100 条代表性 trace 时做分层抽样），合成数据用于冷启动与补齐稀疏维度（维度–元组法或 RAGAS 的知识图谱法），并用 LLM 真实度评分（1–5，留 ≥4）过滤。任务必须"两名专家能独立得出同一 pass/fail"，配备参考解与正反两面用例；版本化数据集 + 把 golden 期望绑定到知识条目 ID/版本是防止 KB 更新后 golden set 失效的可行机制（后者为推断，未见现成文献）。

### Cited Findings
- Anthropic："团队常等到有几百个任务才开始，但 20–50 个来自真实失败的简单任务就是很好的开始；早期变化影响大，小样本足够"；"从你已经在测的开始：把手动发布前检查与常见用户任务变成测试；生产中挖 bug tracker 与支持队列，按用户影响排序"；"任务要无歧义并带参考解：两名领域专家能否独立得出相同 pass/fail？每个任务都应能被正确遵循指令的 agent 通过；跨多次试验 0% 通过率通常意味着任务或 grader 坏了"；"构建平衡的问题集：既测应发生也测不应发生（Claude.ai 搜索：天气应触发搜索、谁创立了 Apple 不应），单边评测导致单边优化" —【官方文档】[Anthropic Demystifying evals](https://anthropic.com/engineering/demystifying-evals-for-ai-agents)
- Anthropic 平台文档："设计反映真实任务分布的 eval，别忘记边界用例（无关/不存在的输入、超长输入、有害输入、歧义）""优先数量而非质量：更多问题 + 略低信号的自动评分，优于更少问题 + 高质量人工评分" —【官方文档】[Claude docs develop-tests](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests)
- generate-synthetic-data（维度–元组法）："从 3 个维度开始（如任务类型、用户角色、查询清晰度），只有当 trace 暴露新失败轴时再加"；先与用户共同起草 20 个元组并确认真实性；LLM 每次生成 10 个随机组合；**元组→自然语言查询用单独的 prompt**（合并生成会降低措辞多样性）；用 LLM 对真实度 1–5 打分、丢弃 <3；目标"~100 条高质量多样 trace"作为饱和启发；"已有 100+ 代表性真实 trace 时改用分层抽样（按高方差维度分组，人工或 embedding K-means 标注），用合成数据填补稀疏类型"；"无人能判断真实性、法律/医疗等复杂领域内容、低资源语言时避免合成" —【实践指南】[generate-synthetic-data SKILL.md](https://github.com/ai-evals-course/evals-skills/blob/main/skills/generate-synthetic-data/SKILL.md)
- evaluate-rag 的检索测试集构建：人工策划（最高质量，问题映射到确切 chunk）；"从 chunk 合成 QA：让 LLM 从每个 chunk 抽取一个自包含事实并写出只能由该事实回答的问题（JSON fact/question）"；**对抗性问题：取含清晰事实的 chunk A，用 embedding 搜索找相似干扰 chunk B、C，用 B/C 的术语写只有 A 能回答的问题**；few-shot LLM 真实度评分保留 4–5 分；该指南不涉及从生产日志构建 —【实践指南】[evaluate-rag SKILL.md](https://github.com/ai-evals-course/evals-skills/blob/main/skills/evaluate-rag/SKILL.md)
- RAGAS 知识图谱法生成 single-hop/multi-hop × specific/abstract 查询，scenario 包含查询长度、风格与 persona（文档标注"coming soon"），示例默认分布 0.5/0.25/0.25 —【官方文档】[RAGAS rag.md](https://github.com/explodinggradients/ragas/blob/main/docs/concepts/test_data_generation/rag.md)、[rag_testset_generation.md](https://github.com/explodinggradients/ragas/blob/main/docs/getstarted/rag_testset_generation.md)
- ARES 用 few-shot prompt 从你的文档合成查询来训练 judge，人工校验集 ≥50（理想几百）—【官方文档】[ARES GitHub](https://github.com/stanford-futuredata/ARES)
- LangSmith：dataset 支持 splits（小切分快速迭代、大切分最终评测）与 versions（每次更改生成新版本，可打 tag 用于 CI 防止意外破坏）；annotation queue 中标注过的 run 可移入 dataset —【官方文档】[LangSmith concepts](https://github.com/langchain-ai/langsmith-docs/blob/main/docs/evaluation/concepts/index.mdx)
- Databricks Genie 基准：每个 Genie space 最多 500 个基准问题，建议同一问题加入多种措辞；以 SQL 结果集比对判定 Good（行值一致即可，忽略排序与列名）；无 SQL 答案的问题需人工审核 —【官方文档】[Databricks Genie benchmarks](https://docs.databricks.com/aws/en/genie/benchmarks)
- CRAG 按 domain × 8 种问题类型 × 动态性（static/slow-changing/fast-changing/real-time）× 流行度（head/torso/tail，各桶题量大致相等）分层 —【官方文档】[CRAG dataset.md](https://github.com/facebookresearch/CRAG/blob/main/docs/dataset.md)
- LiveRAG（2025-11）：面向 RAG 评测的"不同难度等级"问答集；同期研究指出合成 QA 基准在特定领域 RAG 中的可靠性尚未被系统评估 —【独立研究·摘要】[LiveRAG arXiv 2511.14531](https://arxiv.org/html/2511.14531v1)
- Glean 的评测器在每个客户部署内运行以避免数据外泄 —【企业博客·摘要】[Glean AI Evaluator](https://glean.com/blog/glean-ai-evaluator)
- Anthropic 的 saturation 警示：SWE-bench Verified 一年内从≈30–40% 到 >80%，接近饱和后增益看起来很小；Qodo 发现单轮评测漏掉了 Opus 4.5 在长任务上的进步，于是改建 agentic eval；"capability eval 高通过率后应毕业进入 regression suite 持续运行" —【官方文档】[Anthropic Demystifying evals](https://anthropic.com/engineering/demystifying-evals-for-ai-agents)

### Inferences
- 推荐的分层键（本场景）：知识类型（doc/code/config/log）× 问题类型（借 CRAG 的 simple / simple_w_condition / comparison / aggregation / set / false_premise / post-processing / multi-hop）× 动态性（static/slow/fast）× 流行度（head/torso/tail，用条目被引用频次代替）× 应答类型（应答/应弃答/应追问）。CRAG 证明按动态性与流行度分层能暴露 RAG 的系统性弱点（动态、长尾、复杂题准确率显著更低，见 Q8）。
- 日志挖掘流程（综合 LangSmith/error-discovery/Glean）：候选池 = 有显式反馈（Resolved/Helpful/Not Relevant）或 guardrail 触发的会话 → embedding 聚类去重（K-means 6–10 簇，簇代表 + 随机）→ PII/凭据脱敏并保留条目 ID 引用 → 专家写参考解与黄金条目 ID → 版本化入库。隐私处理可借鉴 Glean "评测在部署域内运行"的原则：golden set 与 judge 全部在内网运行。
- "as-of 版本化期望"（推断，未见文献直接描述）：每条 golden 记录存 `{question, expected_answer, gold_item_ids, kb_snapshot_id, valid_from, valid_to}`；KB 更新流水线在条目被修改/删除时自动把引用该条目的 golden 标记为"待复核"，并生成"旧答案应被新答案取代"的 freshness 用例（见 Q5）。LangSmith 的 dataset versioning 与 Databricks 的 SQL 结果集判定（而非文本比对）是两种可借鉴的工程实现。
- 防止 golden set 被 KB 更新"打坏"的另一手段：把期望写成**可执行断言**（Databricks 式：结果集/ID 集合/正则）而非固定文本，减少文本漂移带来的假失败。

### Gaps
- 未找到公开文献或博客直接描述"知识库版本与 golden 期望绑定（as-of）"的具体实现；以上为推断。
- 关于从生产日志去重/采样的量化策略（如 near-duplicate 阈值、每簇配额）没有找到带数字的权威来源；error-discovery 的 15–25 条初始样本是发现失败模式的样本量，不是评测集规模。
- Pinterest Text-to-SQL 的评测集构建与接受率数字未能核实（见 Q7 Gaps）。

---

## Q5. 新鲜度与时间评测：验证更新知识替换旧知识（无陈旧引用）、时间敏感 QA 基准（FreshQA、RealTimeQA、PAT-Questions、DailyQA、HoH、RecencyQA）、staleness rate 与 time-to-freshness、每次 KB 变更的回归套件、跨版本 diff、canary 查询

### Takeaway
公开基准已把"时间敏感"细分为 never/slow/fast-changing + false-premise（FreshQA）、"现在时锚定"（PAT-Questions）、"过期文档混入检索"（HoH，96k 题）、"答案变化频率"（RecencyQA，2026）与"知识更新/冲突"（LongMemEval knowledge-updates、ConflictBank temporal 165 万对），证据一致显示 LLM 容易被检索到的过期/冲突证据带偏，且高动态性问题准确率显著更低（CRAG）。企业内部 KB 没有现成的 staleness rate / time-to-freshness 标准指标，需要自建：以条目版本日志为基础，构造"更新前后答案应改变"的成对 canary 用例，在每次 KB 变更后跑回归并 diff 两个 KB 版本的评测结果。

### Cited Findings
- FreshQA（Google，2023-10；GitHub 持续更新）：数据集"每周或按需更新"，最新版本 2026-04-21，下次更新 2026-05-11（页面所示），最早版本 2024-02-26；评测分 RELAXED / STRICT 两种模式，FreshEval 自动评估器"与人工评分高度一致"（论文附录 B），作者建议用 gpt-4-1106-preview 作评估器（小规模测试中与人工一致性略好）；按问题类别分别计算准确率 —【独立研究】[freshllms/freshqa GitHub](https://github.com/freshllms/freshqa)；四类问题（never-changing / slow-changing / fast-changing / false-premise）及"无搜索增强的模型在 fast-changing 上表现差、检索增强可缩小大部分差距"—【二手来源】[DAIR 论文页](https://academy.dair.ai/papers/freshllms-freshqa)
- RealTimeQA：每周从新闻站抓取的多选测验流，用于衡量检索新鲜度 —【二手来源】[Emergent Mind RTQA](https://www.emergentmind.com/topics/rtqa)
- PAT-Questions（ACL Findings 2024）：自更新的"现在时锚定"问题（如"谁目前效力于某队"），SOTA 模型 EM 仅 1.5%–15.5%，multi-hop 尤难 —【独立研究】[arXiv 2402.11034](https://arxiv.org/html/2402.11034v2)
- DailyQA（2025-05）：评测 web 检索增强 LLM 对频繁更新信息的捕捉，结论"LLM 处理频繁更新信息仍有显著挑战" —【独立研究·摘要】[arXiv 2505.17162](https://arxiv.org/html/2505.17162v1)
- HoH（2025-03）：评估"过期信息"对 RAG 影响的动态基准，96,124 条时间敏感问题、219,463 篇文章 —【独立研究·摘要】[arXiv 2503.04800](https://arxiv.org/pdf/2503.04800)
- RecencyQA（2026-03）：批评现有数据集把时间有效性简化为"当前 vs 过期"二分，而未建模"答案预期变化的频率" —【独立研究·摘要】[arXiv 2603.16544](https://arxiv.org/html/2603.16544v1)
- ConflictBank（NeurIPS 2024）：7,453,853 条 claim-evidence 对、553,117 QA，冲突类型为 misinformation / temporal / semantic，其中 temporal 冲突 1,650,026 对；质量过滤用 DeBERTa-v3 NLI 与 all-mpnet-base-v2；结论"LLM 易被外部证据带偏，即使与其已知知识矛盾" —【独立研究】[conflictbank GitHub](https://github.com/zhaochen0110/conflictbank)、[arXiv 2408.12076](https://arxiv.org/abs/2408.12076v1)
- Micro-Act（2025-06）在三类冲突（misinformation/temporal/semantic）数据集上以多选 QA 准确率评测；另一研究发现更强的 LLM 即使有正确外部证据也常坚持错误的内部记忆 —【独立研究·摘要】[arXiv 2506.05278](https://arxiv.org/pdf/2506.05278)
- LongMemEval：五项能力含 knowledge updates 与 temporal reasoning；2025-09 清理了历史会话以防干扰 —【独立研究】[LongMemEval GitHub](https://github.com/xiaowu0162/LongMemEval)
- CRAG：动态性字段 static / slow-changing / fast-changing / real-time；论文称"事实动态性更高、流行度更低、复杂度更高的问题准确率低得多"，业界 SOTA RAG 仅 63% 回答无幻觉 —【官方文档】[CRAG dataset.md](https://github.com/facebookresearch/CRAG/blob/main/docs/dataset.md)、【独立研究·摘要】[CRAG arXiv 2406.04744](https://arxiv.org/pdf/2406.04744)
- AbstentionBench 把"stale data/过期信息"列为弃答场景之一（含 FreshQA 子集）—【独立研究】[AbstentionBench GitHub](https://github.com/facebookresearch/AbstentionBench)
- 回归评测机制：Anthropic "regression evals 应接近 100% 通过率，capability eval 毕业后持续运行以捕获漂移"；LangSmith regression tests 以对比视图标注回归/改进，backtesting 把生产日志回放到新版本；Promptfoo CI 以通过率门槛失败构建并按 git sha 打 tag；Inspect 建议多 epoch 看评分方差 —【官方文档】[Anthropic](https://anthropic.com/engineering/demystifying-evals-for-ai-agents)、[LangSmith](https://github.com/langchain-ai/langsmith-docs/blob/main/docs/evaluation/concepts/index.mdx)、[Promptfoo ci-cd](https://github.com/promptfoo/promptfoo/blob/main/site/docs/integrations/ci-cd.md)、[Inspect](https://github.com/UKGovernmentBEIS/inspect_ai/blob/main/docs/model-graded.qmd)
- 引用层面的确定性检查："比较被引用 ID 与被检索 ID" —【实践指南】[write-code-eval](https://github.com/ai-evals-course/evals-skills/blob/main/skills/write-code-eval/SKILL.md)

### Inferences
- **Freshness 用例的构造法（推断，综合 FreshQA/HoH/ConflictBank/LongMemEval 的设计）**：从 KB 条目版本日志取 (item_v_old, item_v_new) 对，对每对生成三类题：(a) 答案应随更新改变的"替换题"（期望：引用 new 版本、答案匹配新值、不出现旧值）；(b) 答案不变的"稳定题"（防止过度敏感）；(c) 旧版本被显式保留/软删除时的"冲突题"（期望：优先新版本或指出版本差异）。指标：`staleness rate = 引用了 superseded 条目或含旧值的回答 / 时间敏感题总数`；`time-to-freshness = 条目更新落库时刻到回归用例首次通过的时间`（覆盖索引延迟、缓存、重排序）。
- **Canary 查询**：对每类高频变更源（配置默认值、服务 owner、runbook 步骤、代码接口签名）保持一小组固定问题，每次 KB 更新与每日定时跑，按条目 ID 断言引用，与 Anthropic 的"regression eval 接近 100%"门槛一致。
- **跨 KB 版本 diff**：固定模型与 prompt，仅变更 KB 快照，比较两次评测的逐题结果（pass→fail 列表、引用条目变化、检索 ID 集合 Jaccard），其价值在于把"KB 变更"与"模型/提示变更"的影响隔离（Anthropic 强调评测需把变更与噪声分离；Inspect 建议多 epoch 以区分噪声）。
- ConflictBank 与 CRAG 的结论意味着：仅靠"新文档入库"不能保证"旧答案被替换"，需要在检索层做版本去重/时间加权，并在评测中显式测 temporal conflict。

### Gaps
- 未找到任何公开的"企业 KB staleness rate / time-to-freshness"定义或基准数字；上述指标为本笔记提出的操作化定义。
- HoH、RecencyQA、DailyQA 的具体准确率下降幅度未能获取（arXiv 不可达，仅摘要）。
- "TAQA" 未检索到对应基准（任务书中提及），无法确认其指代。
- 未找到关于"canary 查询"在 RAG/KB 场景的公开实践文章；该做法为从监控领域类比的推断。

---

## Q6. 知识条目级与来源级评测：由结果归因到单个条目（RAGAS context utilization / ContextCite）、反事实消融（移除条目→答案质量变化）、识别有害条目（引用与负反馈相关）、覆盖/缺口分析、重复/冲突检测

### Takeaway
条目级评分有三条可用路径：(1) **贡献归因**：ContextCite 用随机消融 + 稀疏线性代理（LASSO，约 32 次消融即可）给每个上下文来源打贡献分，但代价约为生成的 32 倍；(2) **利用率/支持度指标**：RAGAS ContextUtilization（无 reference 的 context precision）、TRACe 的 Utilization、nugget 支持度；(3) **结果关联**：把条目被引用与 Resolved/Helpful/Not Relevant 等反馈做统计关联（Uber Genie 式反馈是可用信号）。重复/冲突检测的学术基础是 ConflictBank 的 NLI + embedding 过滤流水线；"有害条目"与"覆盖缺口"的量化方法没有现成公开标准，需自建。

### Cited Findings
- ContextCite（MadryLab，2024-09）：以句子为来源单位做上下文消融，跟踪"保留哪些来源时原响应生成概率如何变化"，对 logit 变换后用稀疏线性函数（LASSO）拟合，权重即贡献分；"仅 32 次消融就持续优于基线"，256 次更好；用 top-k 来源做验证的分数显著高于用全部上下文；局限：删除句子可能破坏指代依赖，归因成本约为生成的 32×，线性代理在强非线性/多源复杂上下文下可能退化；区分 contributive（真正影响生成）与 corroborative（能支持）归因 —【独立研究·摘要】[ContextCite arXiv 2409.00729](https://arxiv.org/pdf/2409.00729)；API：`ContextCiter.from_pretrained(model, context, query)` → `get_attributions(top_k=5)`，可对响应的指定 span 归因 —【官方文档】[MadryLab/context-cite](https://github.com/MadryLab/context-cite)
- SelfCite（2025-02）在 ContextCite 衍生的引用上做自监督对齐以改进上下文归因 —【独立研究·摘要】[arXiv 2502.09604](https://arxiv.org/pdf/2502.09604)
- RAGAS `ContextUtilization`（= `LLMContextPrecisionWithoutReference`）：用生成的 response 判断每个检索 chunk 是否相关/被用到，按排名加权 —【官方文档】[RAGAS context_precision.md](https://github.com/explodinggradients/ragas/blob/main/docs/concepts/metrics/available_metrics/context_precision.md)
- RAGBench/TRACe 的 uTilization 指标专门度量上下文被利用的程度 —【独立研究·摘要】[RAGBench](https://arxiv.org/abs/2407.11005v2)
- Nugget 支持度：`nuggetizer assign` 给每个 nugget 标 full/partial 支持，可反推"哪些文档贡献了被支持的 nugget" —【官方文档】[castorini/nuggetizer](https://github.com/castorini/nuggetizer)
- 黄金证据移除实验："移除 gold passages 测 refusal / hallucination / gold leak 率" —【独立研究·摘要】[arXiv 2605.27123](https://arxiv.org/pdf/2605.27123)；CRISP 以"观察中包含黄金证据文档 ID"标记证据步 —【独立研究·摘要】[arXiv 2608.01867](https://arxiv.org/pdf/2608.01867)
- Noise Sensitivity（RAGChecker→RAGAS）衡量在相关/无关检索文档存在时的错误率，可用于识别"引入后导致错误增多"的条目 —【官方文档】[RAGAS noise_sensitivity.md](https://github.com/explodinggradients/ragas/blob/main/docs/concepts/metrics/available_metrics/noise_sensitivity.md)
- Uber Genie 的用户反馈选项为 Resolved / Helpful / Not Relevant，通过指标框架跟踪；评测流水线含 LLM-as-judge 与基础 NLP 指标，结果在 UI 中发布 —【企业博客·摘要】[InfoQ 报道 2024-10](https://www.infoq.com/news/2024/10/uber-genie-rag-copilot)、[Uber Feature Store Summit 2024 slides](https://content.hopsworks.ai/hubfs/Feature%20Store%20Summit%202024/FS%20Summit%2024%20-%20Ubers%20-%20GenAI%20Oncall%20Co-Pilot.pdf)
- Glean："点击指标不适用于生成答案的助手""投票只来自部分用户、有偏" —【企业博客·摘要】[Glean AI Evaluator](https://glean.com/blog/glean-ai-evaluator)
- ConflictBank 构建流水线：Wikidata 抽事实 → 构造冲突 claim → 生成冲突证据 → DeBERTa-v3 NLI + all-mpnet-base-v2 embedding 质量过滤 —【独立研究】[conflictbank GitHub](https://github.com/zhaochen0110/conflictbank)
- BRIGHT 的相关性定义来自"被采纳/高票答案引用的文档"，且标注者需一致同意正例 —【独立研究】[BRIGHT arXiv 2407.12883](https://arxiv.org/pdf/2407.12883)
- TruLens："若向量库只含准确信息，RAG 的答案也准确"——即 groundedness 合格不等于条目正确 —【官方文档】[TruLens rag_triad.md](https://github.com/truera/trulens/blob/main/docs/getting_started/core_concepts/rag_triad.md)

### Inferences
- **条目级评分卡（推断）**：对每个条目 i 维护 (a) 曝光：被检索次数、被引用次数、ContextUtilization 均值；(b) 结果：被引用会话的 Resolved/Helpful 率与 Not Relevant 率、judge 判定 faithful 率；(c) 反事实：对引用 i 的 golden 题做"移除 i"重跑，记录答案 pass 率变化（ContextCite 适合离线小样本精细归因，全量用引用/反馈关联代替）；(d) 风险：被 judge 标为"错误 claim 的支持来源"次数（noise sensitivity 的来源级分解）。"有害条目"= 曝光高且负反馈率显著高于同类基线（需要显著性检验，因为反馈稀疏且有偏，Glean 已指出）。
- **覆盖/缺口分析**：把用户问题聚类（error-discovery 的 K-means 流程）后，统计每簇中"检索 top-k 的最高相关性 <阈值"或"答案弃答/被判不可答"的比例，高比例簇即知识缺口；对每簇抽样让专家确认是否应补文档。
- **重复/冲突检测**：借 ConflictBank 的管线——条目两两（同主题簇内）做 embedding 近邻 + NLI（entailment/contradiction）判定，contradiction 对需人工裁决或按版本/时间戳优先；重复对（高相似 + entailment 双向）合并。该管线同时是 Q5 temporal conflict 的检测器。
- 由于 TruLens 明确 groundedness 只保证"相对知识库"的正确，条目级评测应引入"条目本身的正确性/时效性"标签（owner 复核、最近验证时间），作为独立于对话指标的来源质量维度。

### Gaps
- 未找到公开研究或企业博客给出"条目引用与负反馈关联 → 有害条目"的具体统计方法与阈值；为推断。
- 未找到针对企业 KB 的 duplicate/conflict 检测公开指标（如冲突率、重复率）；ConflictBank 为模型行为基准而非语料清洗工具。
- ContextCite 在 RAG 规模（长上下文、多文档）下的代价/效果公开数据不足（论文承认非线性退化）。
- Uber 2025 年"Enhanced Agentic-RAG"博客（涉及文档质量改进与精度提升）不可达，未能引用其数字。

---

## Q7. 在线评测：deflection / resolution / task-success、"answer accepted"/"code applied"、CSAT、知识库版本或检索器版本级别的 interleaving 与 A/B、guardrail 指标、样本量，以及企业报告方式（Uber Genie、Pinterest、LinkedIn、Intercom Fin、Glean）

### Takeaway
企业自报的在线指标口径差异很大：Uber Genie 用"用户标记的 helpfulness 48.9%"；LinkedIn 用"中位每工单解决时间下降 28.6%"；Intercom Fin 用"resolution rate"（开箱 51%，第三方称 2026 年升至 67–76%），而 resolution 的定义（用户停止回复即算解决）受到质疑。排序类变更（检索器/重排/KB 版本）应优先用 interleaving（灵敏度比 A/B 高 1–2 个数量级，Airbnb 称≈50×）做快速筛选，再用 A/B 验证业务结果；A/B 的弱点是慢、需流量、只能测已部署变更且难解释原因（Anthropic）。

### Cited Findings
- Uber Genie（2024-10）：在 154 个 Slack 频道回答 >70,000 个问题，用户评定 helpfulness rate 48.9%，估计节省约 13,000 工程小时；反馈项 Resolved / Helpful / Not Relevant；Uber 博客称这些频道每月约 45,000 个问题；评测流水线包含 LLM-as-judge 与基础 NLP 指标 —【企业博客（自报）】[InfoQ](https://www.infoq.com/news/2024/10/uber-genie-rag-copilot)、[Uber blog 2024-10-10](https://www.uber.com/gt/en/blog/genie-ubers-gen-ai-on-call-copilot/)、[Uber slides](https://content.hopsworks.ai/hubfs/Feature%20Store%20Summit%202024/FS%20Summit%2024%20-%20Ubers%20-%20GenAI%20Oncall%20Co-Pilot.pdf)
- LinkedIn 客服 RAG+知识图谱（2024-04 论文）：约六个月部署，中位每工单解决时间下降 28.6%；离线基准 MRR 提升 77.6%，BLEU +0.32 —【企业研究（自报）】[arXiv 2404.17723](https://export.arxiv.org/abs/2404.17723)、[alphaxiv 摘要](https://alphaxiv.org/overview/2404.17723v2)；某博客称"平均解决时间下降 63%"，论文中无此数，不采信 —【二手来源】[eliteaiadvantage](https://eliteaiadvantage.com/blog/knowledge-graphs-reduce-support-tickets)
- Intercom Fin（Claude 客户案例页，2026）：开箱 51% 平均 resolution rate；单客户最高 86%；Lightspeed 最高 65%；Fundrise 自报 95% 响应准确率；"每次变更（无论大小）都对照生产基线测试，评测覆盖答案准确率、解决率、CSAT、响应质量"，用"数百万真实客户对话"比较模型 —【厂商案例（自报）】[claude.com/customers/intercom](https://claude.com/customers/intercom)
- 第三方对 Fin 解决率的后续说法：Fin 3 发布时"跨所有客户平均 67%"（2025 末）—【二手来源】[createwith.com](https://createwith.com/tool/intercom/updates/intercom-ships-200-updates-in-2025-fin-3-reaches-67-average-resolution-rate)；"从上线时 23% 升至 2026-06 的 76%，跨 12,000+ 客户，每周 200 万次解决"—【二手来源】[AI Agent Index](https://theaiagentindex.com/agents/intercom-fin)；批评者指出 Fin 把"客户停止回复"计为已解决，可能虚高 —【二手来源（竞品/咨询方）】[myaskai 审计指南](https://myaskai.com/blog/how-to-improve-intercom-fin-resolution-rate)；Fin 定价 $0.99/resolution —【二手来源】[dev.to 定价分析](https://dev.to/omar_bni_f6856a8bb0e021e9/intercom-fin-pricing-in-2026-the-real-math-behind-099-62j)
- Glean：用 LLM 评测器替代不适用的点击指标与稀疏投票；招聘信息显示其 LLM judge 评 correctness / completeness / response quality 并与人工判断对齐，有 golden set 并以评测把关发布 —【企业博客·摘要】[Glean AI Evaluator](https://glean.com/blog/glean-ai-evaluator)、[Glean 招聘页](https://jobs.therundown.ai/jobs/333695451-machine-learning-engineer-llm-evals-+-observability)
- Databricks（第三方 Pebblous 博客转述）：Databricks 在 28 个企业数据分析问题上测得 Genie One 首次正确 84.5%，最佳通用编码 agent 52.4%，最弱 25%；未能核对原始来源 —【二手来源，未核实】[pebblous blog](https://blog.pebblous.ai/blog/databricks-genie-one-governed-data/en/)
- Interleaving 灵敏度：Microsoft（SIGIR 2015，38 个大规模实验、>30 亿点击）称 interleaving 灵敏度比 A/B 高 1–2 个数量级，并首次把用户满意度指标与 interleaving 结合，对 A/B 指标一致性最多提升 22%（>50% 误差降低）—【独立研究（企业）】[Microsoft Research](https://www.microsoft.com/en-us/research/publication/predicting-search-satisfaction-metrics-with-interleaved-comparisons/)；Amazon Search 文献综述称 10–100× —【企业研究】[Amazon debiased balanced interleaving](https://cdn.amazon.science/a9/c8/c9016a1c47caac6a634768e7491d/debiased-balanced-interleaving-at-amazon-search.pdf)；Airbnb（2025-08）称≈50× 加速，一天小流量即可检出 A/B 需数周才能发现的负向转化效应，但 interleaving 会漏掉"优化次要目标而转化中性"的 ranker，因而仅作 A/B 前的筛选 —【企业研究·摘要】[Airbnb arXiv 2508.00751](https://arxiv.org/pdf/2508.00751)；原始 interleaving 不能直接对比两个以上系统 —【企业研究】[Amazon interleaved online testing](https://cdn.amazon.science/c1/4d/7945330e47539fdd870cb5c73613/interleaved-online-testing-in-large-scale-systems.pdf)
- Anthropic 的整体评测方法矩阵：自动评测（可每次提交运行，但可能与真实使用脱节）、生产监控（真实但被动、噪声大、缺真值）、A/B（测真实结果、控混杂，但慢、需流量、只能测已部署变更、难解释原因）、用户反馈（稀疏、偏向严重问题、靠用户发现问题会伤害用户）、人工 transcript 审阅、系统性人工研究（校准 grader 的金标准）；时序：自动评测在发布前与 CI/CD，监控在发布后，流量足够时 A/B —【官方文档】[Anthropic Demystifying evals](https://anthropic.com/engineering/demystifying-evals-for-ai-agents)
- LangSmith 在线评测："无 dataset、无 reference"，用于监控异常并为离线集分类采样 —【官方文档】[LangSmith concepts](https://github.com/langchain-ai/langsmith-docs/blob/main/docs/evaluation/concepts/index.mdx)
- 偏差校正后的在线通过率估计与 bootstrap 置信区间（Rogan-Gladen）—【实践指南】[validate-evaluator](https://github.com/ai-evals-course/evals-skills/blob/main/skills/validate-evaluator/SKILL.md)；ARES 的 PPI 置信区间示例（4,421 条，CI 宽约 ±0.06）—【官方文档】[ARES GitHub](https://github.com/stanford-futuredata/ARES)

### Inferences
- 本场景的在线指标层级建议：L1 自动可得——会话内"引用条目被点击/展开""回答被复制""后续追问率""升级到人工/值班的比例（escalation）""guardrail 触发率（引用未检索条目、破坏性命令建议）"；L2 轻量显式——Uber 式三选一反馈（Resolved/Helpful/Not Relevant）；L3 结果型——"代码/配置变更被应用（code applied）"可通过与代码仓库/配置系统的事件关联定义为"回答后 N 小时内相关文件被提交且引用了回答中的标识符"（推断，未见公开实现）；"task success"对系统迭代类助手可定义为工单/PR 的关闭。
- 排序层变更（embedding、reranker、KB 快照）用 interleaving：两套检索器的 top-k 交错展示并按引用/点击记分，一天即可出结论（Airbnb/Microsoft 证据）；答案层变更（prompt、模型）用 A/B 或日志回放（backtesting）+ 校准 judge。
- 样本量：显式反馈率低（Glean 指出仅部分用户投票），A/B 以 helpfulness 率为主指标时需按二项比例检验估算；可用校准 judge 在全量日志上做 PPI/Rogan-Gladen 估计，把"需要用户反馈的样本量"降到几百条人工标注 + 全量自动标注（ARES 与 validate-evaluator 均提供区间公式）。
- resolution 类指标必须公开定义（Intercom 的争议表明"用户不再回复"口径会虚高），建议用"用户显式确认 or 24h 内无同主题再提问 and 无升级"作为复合定义并同时报告两种口径。

### Gaps
- Pinterest Text-to-SQL 博客（Medium，2024-04）不可达；任务书提到的"接受率 20%→40%"与常被引用的"任务完成速度提升 35%""表检索命中率 40%→90%"均未能核实，本笔记不采用。
- Uber Genie 的 LLM-judge 具体指标定义与 2025 年后的更新数字（含"Enhanced Agentic-RAG"）未能获取。
- LinkedIn SQL Bot（2025）的用户评测结果（常被引用的"95% 用户评为通过及以上"）不可达，未采用。
- GitHub Copilot 的"acceptance rate / persistence rate"作为"code applied"类指标的公开研究（CACM 2024）不可达，未能引用具体数字。
- 未找到 Intercom 官方（intercom.com/fin.ai）关于 2026 年平均 resolution rate 的一手页面；67%/76% 为二手来源。
- 未找到针对 LLM 助手 A/B 的样本量计算专文；上述为基于二项比例检验的推断。

---

## Q8. 与工程/代码知识相关的 benchmark：CRAG、FRAMES、BRIGHT、CodeRAG-Bench、CoIR、LongMemEval/LoCoMo、BrowseComp、SWE-bench + 检索、EnterpriseRAG-Bench / RAGBench / LiveRAG、Databricks Genie；它们对内部 KB 评测能说明与不能说明什么

### Takeaway
公开基准能告诉你**组件能力的相对强弱与系统性弱点类型**（推理密集型检索远弱于语义匹配、动态/长尾/多跳问题准确率骤降、带检索的代码生成并非总是受益、记忆系统在知识更新与弃答上薄弱、浏览 agent 过度自信），但它们的语料与问题分布与内部 KB 无关，不能替代内部 golden set；最有迁移价值的是它们的**分层设计与评分规则**（CRAG 的 ±1/0 评分与动态性/流行度分层、BRIGHT 的"引用即相关"标注、CodeRAG-Bench 的 canonical docs、LongMemEval 的五能力、BrowseComp 的校准误差）。

### Cited Findings
- CRAG（Meta，KDD Cup 2024）：4,409 QA，五域（finance、sports、music、movies、open），每题最多 50 个 HTML 页面 + 约 260 万实体的 mock KG，30 秒预算；8 种问题类型（simple、simple_w_condition、comparison、aggregation、set、false_premise、post-processing、multi-hop）；动态性四档；流行度 head/torso/tail；评分 perfect/acceptable/missing/incorrect，自动评测 correct +1、missing 0、incorrect −1；业界 SOTA RAG 仅 63% 无幻觉作答；动态性高、流行度低、复杂度高的问题准确率显著更低 —【独立研究】[CRAG arXiv 2406.04744](https://arxiv.org/pdf/2406.04744)、[CRAG dataset.md](https://github.com/facebookresearch/CRAG/blob/main/docs/dataset.md)、[CRAG README](https://github.com/facebookresearch/CRAG)；比赛两阶段，db3（北大）获全部任务第一，APEX（中科大）任务 2/3 第二 —【独立研究·摘要】[arXiv 2410.00005](https://arxiv.org/html/2410.00005v1)、[arXiv 2409.15337](https://arxiv.org/html/2409.15337v1)
- FRAMES：824 题、2–15 篇文章、36% 多重约束；无检索 0.40（NAACL 版 0.408），多步检索 0.66 —【独立研究】[arXiv 2409.12941](https://arxiv.org/html/2409.12941v1)、[NAACL 2025](https://preview.aclanthology.org/moar-dois/2025.naacl-long.243.pdf)
- BRIGHT（ICLR 2025）：1,384 条真实查询、12 个数据集（StackExchange 七域含 Stack Overflow、LeetCode、Pony、AoPS、TheoremQA）；StackExchange 子集相关性 = 被采纳/高票答案引用的文档且标注者一致同意；编码子集相关性 = 需要的语法文档（Pony）或共享算法（LeetCode）；SFR-Embedding-Mistral nDCG@10 18.3（MTEB 59.0）；13 个检索器评测 —【独立研究】[arXiv 2407.12883](https://arxiv.org/pdf/2407.12883)、[BRIGHT GitHub](https://github.com/xlang-ai/BRIGHT)；BRIGHT-PRO（2026）只用 StackExchange 子集，因编码/定理子集依赖特定语法或形式逻辑 —【独立研究·摘要】[arXiv 2605.04018](https://arxiv.org/pdf/2605.04018)
- CodeRAG-Bench：六类任务（基础：HumanEval/MBPP/LiveCodeBench；开放域：DS-1000/ODEX；仓库级：RepoEval/SWE-bench-Lite）；检索语料含编程题解、教程、库文档、StackOverflow、GitHub 文件；检索用 NDCG@10（并报 MRR/recall/precision），生成用 pass@1；SWE-bench-Lite 通过外部 harness 评测；仅单语言 —【独立研究】[arXiv 2406.14497](https://arxiv.org/html/2406.14497v2)、[code-rag-bench GitHub](https://github.com/code-rag-bench/code-rag-bench)、[CoIR 对比表](https://preview.aclanthology.org/landing_page/2025.acl-long.1072.pdf)
- CoIR（ACL 2025）：10 个数据集、8 项检索任务、7 个领域、14 种编程语言；四类任务 text-to-code / code-to-code / code-to-text / hybrid；与 MTEB/BEIR 同数据 schema 的 pip 框架；SOTA 检索器仍表现挣扎 —【独立研究】[arXiv 2407.02883](https://arxiv.org/html/2407.02883v1)
- LongMemEval：500 题、五能力（信息抽取、多会话推理、时间推理、知识更新、弃答）；S 版约 115k token（Llama 3 约 40 会话），M 版约 500 会话；用 gpt-4o 自动评分 —【独立研究】[LongMemEval GitHub](https://github.com/xiaowu0162/LongMemEval)；LoCoMo（ACL 2024）：公开 10 个长对话（原 50 个的子集），QA 含类别与证据对话 ID，含 RAG QA 设置 —【独立研究】[locomo GitHub](https://github.com/snap-research/locomo)；厂商分数互相争议：Mem0 自报 LoCoMo 92.5%、LongMemEval 94.4%，Zep 自报 LoCoMo 94.7%、LongMemEval 90.2% —【厂商声明】[Mem0 2026](https://mem0.ai/blog/ai-memory-benchmarks-in-2026)、[Zep research](https://getzep.com/research)
- BrowseComp：1,266 题；Deep Research 51.5%、o1 9.9%、GPT-4o+浏览 <2%；过度自信；Best-of-N 最佳；Parallel 2025-06 自报 27%（并称已过时）—【官方/厂商】[openai.com/index/browsecomp](https://openai.com/index/browsecomp/)、[Parallel](https://parallel.ai/blog/deep-research-browsecomp)、[InfoQ](https://www.infoq.com/news/2025/05/openai-browsecomp-ai-benchmark)
- SWE-bench 仓库提供 `bm25_retrieval.py` 与 `eval_retrieval.py` 用于构建/评测检索式推理数据集（BM25 检索设置）—【官方文档】[SWE-bench make_datasets](https://github.com/SWE-bench/SWE-bench/tree/main/swebench/inference/make_datasets)；Anthropic 指出 SWE-bench Verified 一年内从≈40% 到 >80%，接近饱和 —【官方文档】[Anthropic](https://anthropic.com/engineering/demystifying-evals-for-ai-agents)
- EnterpriseRAG-Bench（2026-05）：50 万份合成企业文档、9 种来源类型、500 题 10 类、"correction-aware"评测框架，公开数据/生成框架/harness/榜单；计划加入多模态、真多跳、人员中心问题 —【独立研究·摘要】[arXiv 2605.05253](https://arxiv.org/pdf/2605.05253)
- RAGBench（10 万样本，五域，TRACe）与 LiveRAG（分难度）见 Q1/Q4 —【独立研究】[RAGBench](https://arxiv.org/abs/2407.11005v2)、[LiveRAG](https://arxiv.org/html/2511.14531v1)
- Databricks Genie 基准功能（最多 500 题、结果集比对）见 Q4；Microsoft ISE 基于 LiveSQLBench 的自建评测在文档稀疏数据库上达约 75% —【企业博客】[Microsoft ISE 2026-05](https://devblogs.microsoft.com/ise/llm-sql-query-generation/)
- τ-Bench/τ²-Bench（对话 agent）、Terminal-Bench、WebArena/OSWorld（计算机使用）被 Anthropic 列为对应 agent 类型的参考基准 —【官方文档】[Anthropic](https://anthropic.com/engineering/demystifying-evals-for-ai-agents)

### Inferences
- 对内部 KB 的**可迁移设计**：(1) CRAG 的 +1/0/−1 评分直接鼓励"不确定就弃答"，适合运维助手；(2) BRIGHT 的"引用即相关"可转化为"被值班工程师在工单/PR 中引用的文档即正例"，自动获得推理密集型检索标注；(3) CodeRAG-Bench 的 canonical docs 思路对应"每个 API/配置项的权威条目"，用 ID 做检索真值；(4) LongMemEval 的 knowledge-update 与 abstention 题型对应 KB 更新与未知问题。
- 公开基准**不能**说明的：内部术语/缩写的检索难度、代码仓库私有结构、日志语义；BRIGHT/CoIR 的结论（通用 embedding 在推理密集/代码检索上弱）提示本场景需要混合检索与 reranker，但其收益必须用内部 golden set 验证（Q2 的离线-端到端脱节案例）。
- 厂商在记忆基准上的互相争议说明：对外部 benchmark 分数应要求可复现脚本与固定 judge 版本后再采信。

### Gaps
- CodeRAG-Bench 的核心结论（检索何时帮助/损害代码生成、哪类语料最有效）未能从可达来源确认（论文与站点不可达）。
- BRIGHT 当前榜单、LLM 改写查询的增益、长上下文/重排发现未能核实。
- LongMemEval 论文中"商用聊天助手在持续交互中记忆准确率下降约 30%"的常被引用数字未在 README 中出现，未采用。
- SWE-bench 原论文中 BM25 检索 vs oracle 检索的解决率数字不可达，未采用。
- "EnterpriseBench"（任务书用名）未检索到；最接近的是 EnterpriseRAG-Bench（2026）。

---

## Q9. 反模式：优化 judge 分数而非结果、日志同时用于调优与评测造成污染、引用率的 Goodhart、模型更新导致 judge 漂移

### Takeaway
已被文献与实践指南明确记录的反模式有：Likert/综合分不可校准、omnibus judge 不可行动、judge 未经人工验证、用 accuracy/κ 掩盖类别不平衡、few-shot 泄漏进 dev/test、评测集过拟合合成数据、"set-and-forget"评估器、judge 模型静默更新造成"幻影回归"、单边评测导致单边优化、grader 可被 hack、公开基准被预训练污染、抽取式复制可把幻觉率刷到 0%。引用率 Goodhart（为提高引用率而堆砌引用）没有找到专门文献，但 TREC 的 support 评测与"引用 ID ⊆ 检索 ID"代码检查提供了对策。

### Cited Findings
- eval-audit 八类反模式：Likert/模糊分数；通用/整体式 judge 与相似度指标作主评估；评估器不来自误差分析；judge 无人工标签验证；用 accuracy/κ 而非 TPR/TNR；few-shot 数据泄漏（"用评测数据做 few-shot 会虚高一致性并掩盖 judge 失败"）；用 LLM 判可代码检查的标准；"set-and-forget"（"评估器随流水线演化而退化"，需重新验证与重做误差分析）—【实践指南】[eval-audit SKILL.md](https://github.com/ai-evals-course/evals-skills/blob/main/skills/eval-audit/SKILL.md)
- evaluate-rag："过拟合合成数据——定期用真实用户查询验证" —【实践指南】[evaluate-rag](https://github.com/ai-evals-course/evals-skills/blob/main/skills/evaluate-rag/SKILL.md)
- Anthropic："单边评测产生单边优化""grader 要抗 hack：通过必须靠解决问题而非利用漏洞""评分看产出不看路径（过度指定路径会惩罚合理的创造性解法）""在接近饱和时增益看起来很小""不要在有人读 transcript 之前相信分数"；CORE-Bench 评分 bug 导致 42%→95% 的差异；METR 发现误配置任务惩罚遵循指令的模型；共享环境状态可能让模型从前次试验的 git 历史中获得不公平优势 —【官方文档】[Anthropic Demystifying evals](https://anthropic.com/engineering/demystifying-evals-for-ai-agents)
- Judge 漂移：综述指出 judge 表现随模型更新而变（3 月版 vs 6 月版）—【独立研究·摘要】[arXiv 2411.15594](https://arxiv.org/html/2411.15594v6)；"LLM-Evaluation Tropes"（2025-04）列出漂移信号（顶尖系统排名变化、与人工标签分歧、未判样本标签更不稳定）并要求"持续重新验证，因为无法保证长期访问特定模型版本" —【独立研究·摘要】[arXiv 2504.19076](https://arxiv.org/pdf/2504.19076)；实践者博客（2026-04）：供应商常对生产别名做无版本号的行为刷新，建议不用 "latest" 别名、固定 judge 快照、保留归档输出与人工锚点集、仅在同一 judge 版本内报告差值，并指出 temperature 0 下仍有采样方差需重复运行 —【二手来源】[tianpan.co judge drift](https://tianpan.co/blog/2026-04-23-llm-judge-drift-evaluator-upgrade-phantom-regression)；Inspect 建议 temperature 0 + seed + 多 epoch 看方差 —【官方文档】[Inspect](https://github.com/UKGovernmentBEIS/inspect_ai/blob/main/docs/model-graded.qmd)
- 基准污染：LLM reranker 研究为避开 TREC DL/BEIR 被预训练数据污染而使用 2025-04 之后的新查询 —【独立研究·摘要】[arXiv 2508.16757](https://arxiv.org/pdf/2508.16757)；BrowseComp 中 OpenAI 自述 Deep Research 在该类任务上训练过，分数不代表通用能力 —【官方】[BrowseComp](https://openai.com/index/browsecomp/)
- 指标可被刷：Vectara 指出抽取式摘要器可得 0% 幻觉率，因此幻觉率只能与其他指标并用 —【厂商（方法论声明）】[hallucination-leaderboard](https://github.com/vectara/hallucination-leaderboard)
- 自我偏好与位置偏差（见 Q3）：GPT-4 自我偏好 0.520；位置偏差随候选质量差距而变 —【独立研究】[alphaxiv 2410.21819](https://www.alphaxiv.org/abs/2410.21819)、[ACL 2025.ijcnlp-long.18](https://aclanthology.org/2025.ijcnlp-long.18/)
- Criteria drift（标准随观察输出而变）—【独立研究】[EvalGen](https://arxiv.org/pdf/2404.12272)
- 结果口径虚高：Intercom "停止回复即解决"的争议 —【二手来源】[myaskai](https://myaskai.com/blog/how-to-improve-intercom-fin-resolution-rate)
- 引用支持的可自动检查部分："比较被引用 ID 与被检索 ID" —【实践指南】[write-code-eval](https://github.com/ai-evals-course/evals-skills/blob/main/skills/write-code-eval/SKILL.md)；TREC 2024 的 support 评测以 GPT-4o 判"引用是否支持陈述"，run 级 τ>0.79 —【独立研究·摘要】[arXiv 2504.15205](https://arxiv.org/html/2504.15205)

### Inferences
- **日志污染的防线**：把日志按会话 ID 哈希分成"调优池"（用于 prompt/检索调参、few-shot、合成数据种子）与"评测池"（golden set 与 judge 校准），并在数据集元数据中记录来源池；任何从日志挖出的 golden 题必须排除其会话曾用于 few-shot 或调参（eval-audit 反模式 6 的推广）。
- **引用率 Goodhart 的对策**：不把"引用率"作目标指标，改用"引用支持率（被引用条目确实支持该 claim，judge 校准后）+ 引用 ID ⊆ 检索 ID 的代码检查 + 过度引用惩罚（无关引用计入 noise）"。
- **judge 漂移的运维化**：judge 模型版本进入评测结果的元数据；每次 judge 变更时在固定锚点集（~100 条专家标注）上重算 TPR/TNR，若变化超阈值则双 judge 并行一段时间；所有历史对比仅在同 judge 版本内进行。
- **优化 judge 分数而非结果**：以 Anthropic 的分层（自动评测 → 监控 → A/B → 用户反馈 → 人工审阅）作为"真值梯度"，judge 分数只在与在线结果（Resolved 率、升级率）保持相关时才作为代理；定期（如每季度）重算 judge 分数与在线结果的相关性。

### Gaps
- 未找到专门研究"引用率/引用数量被 Goodhart 化"的论文或博客。
- 未找到量化"同一日志用于调优与评测"造成偏差幅度的研究。
- judge 漂移的实证论文（Modelwire 转述的"更换 judge 即改变分数"研究）原文未能核实 —【二手来源】[themodelwire](https://themodelwire.com/article/llm-judges-produce-inconsistent-scores-across-model-versions-01KX4Y0KSRYBRYX9ZWE0A71M4S)。

---

## Q10. 综合：面向"部门级系统迭代助手 + 持续更新 KB、全量对话与条目日志"的评测程序蓝图（基于上述证据的推断）

### Takeaway
评测程序应分五层：**检索层（确定性 ID 指标）→ 答案层（校准的二元 judge 集）→ 新鲜度层（条目版本驱动的成对 canary）→ 条目层（曝光/结果/反事实评分卡）→ 在线层（interleaving 筛选 + A/B 验证 + 校准 judge 的全量估计）**，并以 20–50 个真实失败任务起步、每个失败模式 ~100 条专家标注扩充、judge 版本与 KB 快照全部进入结果元数据。

### Cited Findings
- 起步规模与任务质量标准、capability/regression 分离、pass@k vs pass^k（50% pass@1；75% 单次 → 3 次全成功≈42%；k=10 时 pass@k→100% 而 pass^k→0%）、分层评测方法矩阵 —【官方文档】[Anthropic Demystifying evals](https://anthropic.com/engineering/demystifying-evals-for-ai-agents)
- Judge 设计四要素、~50/50 标注、TPR/TNR ≥90% 目标、Rogan-Gladen 校正、~100 条 trace 饱和 —【实践指南】[write-judge-prompt](https://github.com/ai-evals-course/evals-skills/blob/main/skills/write-judge-prompt/SKILL.md)、[validate-evaluator](https://github.com/ai-evals-course/evals-skills/blob/main/skills/validate-evaluator/SKILL.md)、[eval-audit](https://github.com/ai-evals-course/evals-skills/blob/main/skills/eval-audit/SKILL.md)
- 检索优先 Recall@k、两跳 Recall@k、分开评测检索与生成 —【实践指南】[evaluate-rag](https://github.com/ai-evals-course/evals-skills/blob/main/skills/evaluate-rag/SKILL.md)
- ID-based precision/recall 与 ContextUtilization —【官方文档】[RAGAS](https://github.com/explodinggradients/ragas/blob/main/docs/concepts/metrics/available_metrics/context_precision.md)
- CRAG 的 +1/0/−1 评分与动态性/流行度分层 —【独立研究】[CRAG](https://github.com/facebookresearch/CRAG/blob/main/docs/dataset.md)
- Interleaving 1–2 个数量级灵敏度 —【独立研究】[Microsoft Research](https://www.microsoft.com/en-us/research/publication/predicting-search-satisfaction-metrics-with-interleaved-comparisons/)
- PPI/置信区间 —【官方文档】[ARES](https://github.com/stanford-futuredata/ARES)
- 多 grader 多数投票、抗注入 grade 解析、temperature 0 + seed —【官方文档】[Inspect](https://github.com/UKGovernmentBEIS/inspect_ai/blob/main/docs/model-graded.qmd)

### Inferences
1. **数据模型**：`conversation(turn_id, user_query, answer, cited_item_ids[], retrieved_item_ids[]@rank, model_version, prompt_version, kb_snapshot_id, feedback∈{Resolved,Helpful,NotRelevant,∅}, escalation, guardrail_flags)`；`item(item_id, version, type∈{doc,code,config,log}, owner, last_verified_at, superseded_by)`；`golden(question, gold_item_ids[], expected(assertion|text), category, dynamism, popularity, answer_type∈{answer,abstain,clarify}, valid_from, valid_to)`。
2. **离线套件**：(a) Retrieval：Recall@5/10、两跳 Recall、MRR、按 type/dynamism/popularity 分层；agentic 轨迹报"最终命中率、首次命中步数、工具调用数、token 成本、gold-leak 率"；(b) Answer：每个失败模式一个二元 judge（faithfulness-to-citations、completeness-vs-nuggets、harmful-ops-advice、should-abstain、should-clarify、stale-citation），全部经 ~100 条专家标注校准；(c) Freshness：条目版本对生成替换/稳定/冲突三类题，报 staleness rate 与 time-to-freshness；(d) Regression：capability 套件毕业后进入 regression，门槛接近 100%，每次 KB 快照/模型/prompt 变更运行并 diff。
3. **条目层**：周级计算每条目曝光/引用/Helpful 率/Not Relevant 率/被判错误 claim 来源次数/ContextUtilization；对 top 引用条目做移除重跑；对同簇条目跑 NLI 冲突/重复检测；输出"缺口簇、冲突对、疑似有害条目、长期未验证条目"四张清单给 owner。
4. **在线层**：排序变更用 interleaving（按引用/点击记分，1–3 天）；答案变更用 A/B 或 backtesting；全量日志用校准 judge + Rogan-Gladen/PPI 估计并给区间；主结果指标为 Resolved 率、升级率、"code applied"事件关联率；guardrail 指标为引用越界率、破坏性命令建议率、幻觉举报率。
5. **治理**：judge 版本、KB 快照、prompt 版本作为所有评测结果的主键；judge 更换时锚点集重校准；日志分调优池/评测池；每季度重做误差分析（新失败模式 → 新 judge），并检查 judge 分数与在线结果的相关性以防 Goodhart。

### Gaps
- 以上蓝图中"code applied"事件定义、staleness/time-to-freshness 定义、as-of 版本化期望、有害条目统计判据均为本笔记推断，未见直接公开先例。
- 本次研究因搜索配额与站点封锁，未能覆盖：Pinterest/LinkedIn/Uber 2025 年后的最新数字、Databricks 与 Phoenix 的 judge 校准数据、RAGAS 原论文一致性数据、CodeRAG-Bench 与 BRIGHT 的详细结论；建议后续以这些为补充检索目标。
