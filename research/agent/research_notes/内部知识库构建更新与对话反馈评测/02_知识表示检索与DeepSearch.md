# 02 内部工程知识的表示、分块、索引与检索：从 one-shot RAG 到 Agentic "DeepSearch"（截至 2026-10）

> 研究日期：2026-10-16。目标读者：TikTok 推荐架构负责人，需要为“系统迭代用的部门级 AI 助手/编码与运维 Agent”选型知识表示与检索架构。
> 证据标注：**[厂商自报]** = 厂商/作者自评测；**[独立基准]** = 第三方论文或公开基准；**[二手]** = 博客/聚合页转述，未能核对原文；**[官方文档]** = 产品官方文档。
> 环境限制：本沙箱屏蔽了 arxiv.org（含 export/alphaxiv/papers.cool 镜像）、huggingface.co、jina.ai、cursor.com、sourcegraph.com、augmentcode.com、research.trychroma.com、openai.com、docs.github.com、zenml.io 等；能直接打开的主要是 anthropic.com、platform.claude.com、code.claude.com、github.com、microsoft.com。论文类数字多数来自搜索摘要与 GitHub README，已逐条标注；各节 Gaps 列出未能核实的项。

---

## KQ1 分块与增强（Chunking & Enrichment）：按模态的 2025–2026 最佳实践

### Takeaway
2025–2026 的共识是“结构优先、上下文补全、再评测”：文档按结构/语义切 200–800 token 并给每个 chunk 加 50–100 token 的文档级上下文（Anthropic Contextual Retrieval 报告 top-20 检索失败率 −49%，加重排 −67%，代码域仅 −41%）；代码按 AST 切（cAST：RepoEval Recall@5 +4.3、SWE-bench Pass@1 +2.67）；chunk 大小没有通用最优值（同一方法在不同数据集上最优值从 64 到 512 token 不等），必须用自己的 query 集评测。

### Cited Findings
**Contextual Retrieval（Anthropic，2024-09-19，[厂商自报]，至今仍是最常被引用的增强基线）**
- 方法：对每个 chunk，用 Claude 3 Haiku 在整篇文档上下文下生成 50–100 token 的“情境说明”并前置到 chunk，再同时做 embedding 与 BM25；chunk “通常不超过几百 token”，成本示例按 800-token chunk、8k-token 文档计算 — [Anthropic](https://www.anthropic.com/news/contextual-retrieval)
- 结果（top-20，指标 = 1 − recall@20，跨 codebases/fiction/ArXiv/science 四域平均，Gemini Text 004 embedding）：基线 5.7% → Contextual Embeddings 3.7%（−35%）→ + Contextual BM25 2.9%（−49%）→ + Cohere rerank（召回 150 重排取 20）1.9%（−67%） — [Anthropic](https://www.anthropic.com/news/contextual-retrieval)
- 一次性情境生成成本：借助 prompt caching 为 **$1.02 / 百万文档 token**（假设 800-token chunk、8k 文档、50-token 指令、100-token 情境）；缓存使延迟降低 >2×、成本最高降 90% — [Anthropic](https://www.anthropic.com/news/contextual-retrieval)
- 负面结论：通用“文档摘要前置”只有“very limited gains”；HyDE 与 summary-based indexing 在其评测中“performed poorly”；top-20 优于 top-10/5 但更多 chunk 可能分散模型注意力；知识库 <200k token（约 500 页）时建议整体放入 prompt 而不做 RAG — [Anthropic](https://www.anthropic.com/news/contextual-retrieval)
- 第三方拆解 [二手]：67% 是四域平均，fiction 高达 84%，而 “Codebases-Vague” 类只有 41%，即代码/模糊查询收益显著低于叙事文本 — [Medium/Almond AI](https://medium.com/almond-ai/responding-to-anthropics-contextual-retrieval-for-rag-apps-why-context-is-not-all-you-need-af503985aa55)

**代码：AST 结构化分块 cAST（CMU + Augment Code，Findings of EMNLP 2025，arXiv 2506.15655，[独立基准]）**
- 算法：把代码解析为 AST，自顶向下“split-then-merge”：超预算的节点递归拆分，过小的兄弟节点合并，预算以**非空白字符数**计；结果是语法完整的自包含单元。报告 RepoEval 检索 Recall@5 **+4.3 分**、SWE-bench 生成 Pass@1 **+2.67 分** — [arXiv 2506.15655 摘要（搜索摘要，未能打开全文）](https://arxiv.org/abs/2506.15655)；[ACL Anthology 2025.findings-emnlp.430](https://preview.aclanthology.org/dashboard/2025.findings-emnlp.430)
- 开源实现 astchunk：参数 `max_chunk_size`（非空白字符，示例用 1500/1800/2000）、`chunk_overlap`（以 AST 节点数计）、`chunk_expansion`（为 chunk 加元数据头，如 filepath）；“Full support” 语言仅 Python / Java / C# / TypeScript — [GitHub yilinjz/astchunk](https://github.com/yilinjz/astchunk)
- Cursor 的索引管线同样采用 tree-sitter AST-aware 分块 [二手] — [Towards Data Science](https://towardsdatascience.com/how-cursor-actually-indexes-your-codebase/)

**Late Chunking（Jina AI，arXiv 2409.04701，2024，[厂商自报]）**
- 先用长上下文 embedding 模型编码整篇文档，再在 transformer 之后、mean-pooling 之前切分，使每个 chunk 向量条件于全文；无需训练；报告 BEIR nDCG@10 提升 2.70–3.63%；已在 jina-embeddings-v3 API 提供 — [arXiv 2409.04701](https://arxiv.org/html/2409.04701v1)；[GitHub jina-ai/late-chunking](https://github.com/jina-ai/late-chunking)；[DataCamp 教程（二手）](https://www.datacamp.com/tutorial/late-chunking)

**chunk 大小：没有通用最优值（[独立基准]）**
- “Rethinking Chunk Size for Long-Document Retrieval”（arXiv 2505.21700，2025）：固定 64/128/256/512/1024 token、无 overlap、stella_en_1.5B_v5 与 snowflake-arctic-embed-l-v2.0：SQuAD 在 64 token 时 recall@1 最高（64.1%）；NewsQA 峰值在 512 token（55.9%）；**TechQA（技术文档）从 128 token 的 16.5% 升到 512 token 的 61.3%** — [arXiv 2505.21700](https://arxiv.org/pdf/2505.21700)
- 实践者默认 [二手]：递归切分 ≈512 token、10–25% overlap 是 2026 年最常见默认；Chroma 的评测显示同一语料上最好与最差分块策略 recall 相差可达 9%；Vectara（NAACL 2025）被引述称分块配置对检索质量的影响不亚于 embedding 模型选择 — [PremAI 2026 分块指南](https://blog.premai.io/rag-chunking-strategies-the-2026-benchmark-guide)；[Splunk](https://www.splunk.com/en_us/blog/artificial-intelligence/chunking-techniques.html)
- Firecrawl 对比（[二手]，未核实）：递归 ~512 token ≈69% 准确率 vs 语义分块 54% — [PremAI](https://blog.premai.io/rag-chunking-strategies-the-2026-benchmark-guide)

**元数据/过滤相关（[官方文档]）**
- Claude Code 强调文件系统元数据（目录位置、命名、大小、时间戳）本身就是相关性信号；Glob 结果按修改时间排序、上限 100 个文件 — [Anthropic Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)；[Claude Code tools reference](https://code.claude.com/docs/en/tools-reference)
- 为 agent 写检索工具时：返回“名称”而非 UUID 可降低幻觉、提升检索精度；提供 `response_format`（CONCISE 72 token vs DETAILED 206 token）；Claude Code 默认把工具返回截断在 25,000 token — [Anthropic Writing Tools for Agents (2025-09-11)](https://www.anthropic.com/engineering/writing-tools-for-agents)

### Inferences
- **按模态的分块建议（综合以上证据的推断）**：
  - 设计文档/Wiki/会议纪要：按标题层级做结构分块（目标 300–800 token），每块前置“文档标题 + 章节路径 + 50–100 token LLM 情境”；Contextual Retrieval 的 $1/百万 token 成本对部门级语料（数亿 token 量级）是可承受的一次性投入，但要在 **技术文档上单独评测**，因为其代码域收益（41%）明显低于叙事文本。
  - 代码（C++/Python/DSL）：AST 分块（函数/类/模板为单元 + 文件路径 + 符号签名头）；astchunk 未“Full support” C++，需基于 tree-sitter-cpp 自行扩展；DSL 若无 tree-sitter grammar，退化为“以语法块/缩进块为边界 + 文件级 header”。
  - 配置（YAML/JSON/Protobuf/特征配置）：不要按 token 切；按“键路径”（如 `model.tower.user.emb_dim`）展平为键值行并附文件路径与版本/commit，做 BM25/精确匹配优先的索引（配置查询几乎全是精确标识符查询，见 KQ2 的 BM25 结论）。
  - 日志/告警：先结构化（模板抽取/去参数化）再索引模板而非原文；原文只保留指针（path + 时间窗），由 agent 按需用工具拉取（Just-in-time 原则，见 KQ6）。
  - 实验记录/发布记录：结构化表（实验 ID、特征、模型、指标 delta、上线决策）走 SQL/语义层（KQ4），自然语言结论段落再做 chunk + 情境化。
  - Runbook/SOP：不按 token 切，整篇作为一个“Skill/Playbook”单元（KQ7），只索引其 name/description。
- 应把“chunk 大小”当作超参并保存评测集：TechQA 结果（128→512 token 准确率 16.5%→61.3%）表明技术文档偏好较大 chunk，而精确事实（配置项、指标定义）偏好小 chunk；一库两索引（小粒度精确 + 大粒度语义）比单一粒度更稳。

### Gaps
- cAST 论文全文（RepoEval/SWE-bench 基线值、CrossCodeEval 与 CoIR 表格、最终 chunk size 结论）未能打开（arXiv/ACL Anthology 均被屏蔽），仅有摘要数字。
- Late Chunking 没有找到独立复现；Contextual Retrieval 的代码域结果仅有一篇二手拆解。
- 未找到针对“配置文件/日志/实验记录”这类半结构化模态的分块对照实验，上述模态建议属推断。

---

## KQ2 检索栈：hybrid BM25 + dense + reranker、融合、查询改写、2026 embedding/reranker 格局

### Takeaway
生产级默认栈仍是“BM25 + dense 双路召回 → RRF/加权融合 → cross-encoder/listwise 重排（召回 100–150 重排取 10–20）”，证据显示融合收益从 +1% 到 +20% 以上随语料差异极大、未调参的融合甚至会倒退；2026 年 MTEB 多语榜已由开源模型（Microsoft harrier-oss-v1-27b 74.31、Tencent KaLM-Embedding-Gemma3-12B 72.32、Qwen3-Embedding-8B 70.75）领先，而闭源旗舰（voyage-4、Cohere embed-v4、gemini-embedding-2）基本未提交 MTEB；中文与代码场景可直接选 Qwen3-Embedding/Qwen3-Reranker（Apache 2.0、C-MTEB 73.84、reranker MTEB-Code 81.2）或 voyage-code-3/4（闭源、独立基准 CoQuIR 中唯一稳定高于随机基线的模型）。推理密集型检索（BRIGHT）仍是短板：顶级 MTEB 模型 BRIGHT nDCG@10 仅 ~18。

### Cited Findings
**Hybrid 与融合的实际收益（多为 [二手] 博客复现，波动大）**
- WANDS（电商）：BM25 0.6983、dense 0.6953、RRF hybrid 0.7068 NDCG（≈+1%）；调参（加权 + boosting tiers）后 0.7497（+7.4%）；一次未调参的融合 MRR 0.390 低于 dense-only 0.410 — [tianpan.co 2026-04-12](https://tianpan.co/blog/2026-04-12-hybrid-search-production-bm25-dense-embeddings)
- Weaviate 结果被引述：BEIR SciFact +5% 到 BRIGHT Biology +24%；OpenSearch 的 BEIR 测试被引述称 RRF 比分数融合（CombSUM）低 3–4% NDCG — [denser.ai 2026 指南](https://denser.ai/blog/hybrid-search-for-rag/)；[PremAI hybrid search](https://blog.premai.io/hybrid-search-for-rag-bm25-splade-and-vector-search-combined)
- 2026 年一篇 1,856 篇 NLP 维基语料论文：BM25 + E5-base 的 RRF 取得最高 nDCG@10 0.416 — [PremAI 转述](https://blog.premai.io/hybrid-search-for-rag-bm25-splade-and-vector-search-combined)
- Elastic 官方 hybrid retrieval 说明（RRF 实现与收益） — [Elastic Search Labs](https://www.elastic.co/search-labs/es/blog/improving-information-retrieval-elastic-stack-hybrid)
- Anthropic 的实验：在 contextual embeddings 之上加 contextual BM25，失败率再降 14 个百分点（35%→49%），说明精确标识符/术语匹配对技术语料不可或缺 — [Anthropic](https://www.anthropic.com/news/contextual-retrieval)
- “Is Grep All You Need?”（arXiv 2605.15184，2026-05-14，[独立基准]）：在 LongMemEval-S（116 题）上，inline 交付下 **词法 grep 检索在每一个 harness–model 组合上都优于 dense 向量检索**；但 harness 本身影响同样大（同一 Claude Opus 4.6 在 Chronos harness 93.1% vs Claude Code 76.7%）；programmatic 交付下结论会重排 — [arXiv 2605.15184](https://arxiv.org/abs/2605.15184)（搜索摘要）；[DAIR.AI 解读](https://academy.dair.ai/papers/is-grep-all-you-need)

**查询改写 / HyDE / multi-query**
- Anthropic：HyDE 在其评测中表现差 — [Anthropic](https://www.anthropic.com/news/contextual-retrieval)
- BRIGHT：在查询中加入显式推理（reasoning-augmented queries）最多提升 12.2 nDCG 分 — [BRIGHT ICLR 2025](https://www.iclr.cc/virtual/2025/poster/27702)
- Anthropic 多 agent 研究系统：agent 默认倾向写又长又具体的查询导致召回稀少；提示其“先短而宽、再逐步收窄” — [Anthropic multi-agent research](https://www.anthropic.com/engineering/multi-agent-research-system)
- LazyGraphRAG 的查询细化：LLM 先拆 3–5 个子查询再重组为扩展查询 — [Microsoft Research](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/)

**Embedding 模型（2025-06 → 2026-09）**
- Qwen3-Embedding（2025-06，Apache 2.0 [二手确认]，[厂商自报]）：0.6B/4B/8B，32K 上下文，维度 1024/2560/4096，支持 MRL 与 instruction；MTEB(Multilingual) 8B 70.58、MTEB(Eng v2) 75.22、**C-MTEB 73.84（Retrieval 78.21）**；Qwen3-Reranker 0.6B/4B/8B，MTEB-Code 81.20/81.22（4B/8B）、CMTEB-R 77.45（8B）、MLDR 70.19 — [GitHub QwenLM/Qwen3-Embedding](https://github.com/QwenLM/Qwen3-Embedding)；[arXiv 2506.05176](https://arxiv.org/pdf/2506.05176)
- 2026-09 MTEB(Multilingual, v2) 榜单 [二手]：Microsoft harrier-oss-v1-27b 74.31、Tencent KaLM-Embedding-Gemma3-12B 72.32、Qwen3-Embedding-8B 70.75；gemini-embedding-001 68.84；**voyage-4 / voyage-4-large / Cohere embed-v4.0 在 131 个多语任务中只有 2 个有提交结果、38 个英文任务无提交，gemini-embedding-2 完全无提交**，所以这些闭源模型“MTEB 分数”多为厂商自述 — [andrew.ooo 2026 排名](https://andrew.ooo/answers/best-embedding-models-2026-ranked/)；[deploybase](https://deploybase.ai/articles/best-embedding-models)
- 价格 [二手]：voyage-4-large $0.12/百万 token、voyage-4-lite $0.02；Voyage 4 系列共享向量空间（可用小模型建库、大模型查询）；Gemini Embedding 2 $0.20/百万文本 token、支持图/音/视频同空间，但与 gemini-embedding-001 不兼容需全量重嵌 — [andrew.ooo](https://andrew.ooo/answers/best-embedding-models-2026-ranked/)
- 中文：bge-m3（BAAI，2024-01-30）dense+sparse+multi-vector 三合一、100+ 语言、8192 token，发布时 MIRACL/MKQA SOTA [厂商自报]；FlagEmbedding 页面最新条目止于 2025-03（BGE-VL），未见 2026 新文本模型 — [GitHub FlagOpen/FlagEmbedding](https://github.com/FlagOpen/FlagEmbedding)
- 代码：voyage-code-3（2024-12）[厂商自报] 在 32 个代码检索集上比 OpenAI text-embedding-3-large 高 13.8%、比 CodeSage-large 高 16.8%；维度 2048/1024/512/256，1024-d binary ≈ 2048-d float32；32K 上下文 — [W&B 报道](https://wandb.ai/byyoung3/ml-news/reports/Voyage-Code-3-Smarter-More-Efficient-Code-Retrieval-with-Nested-Embeddings---VmlldzoxMDkzNDg1NQ)；**独立基准 CoQuIR**（arXiv 2506.11066）：除 voyage-code-3 外所有模型至少在一个数据集低于随机基线，voyage-code-3 在多数指标上稳定领先 — [arXiv 2506.11066](https://arxiv.org/pdf/2506.11066)
- voyage-code-4（AWS Marketplace 列表，[厂商自报]）：声称在 agentic code retrieval 上超过 Cohere Embed v4 与 Gemini Embedding 2，比 voyage-code-3 高 27.54% / 13.98%（两套评测） — [AWS Marketplace](https://aws.amazon.com/marketplace/pp/prodview-5vximy4qv7vew)
- 推理密集型检索 BRIGHT（ICLR 2025，[独立基准]）：MTEB 榜首模型（59.0 nDCG@10）在 BRIGHT 上仅 18.0（ICLR 版）/18.3（arXiv v3，SFR-Embedding-Mistral）；1,384–1,398 条查询；BRIGHT-Pro 变体改用 α-nDCG 的多轮 agentic 协议，分数不可与原版比较 — [ICLR 2025](https://www.iclr.cc/virtual/2025/poster/27702)；[arXiv 2407.12883](https://export.arxiv.org/pdf/2407.12883)；[BRIGHT-Pro 说明页](https://benchmarklist.com/benchmarks/rethinking_reasoning_intensive_retrieval_evaluating_and_advancing_retrievers_in_agentic_search_systems/)

**Reranker（2026，[二手] 为主，无同条件对比）**
- Cohere Rerank 4：仅 API、32K 上下文、Pro 版约 $0.0025/次检索 — [andrew.ooo 对比页](https://andrew.ooo/answers/voyage-rerank-3-vs-cohere-rerank-4-vs-jina-reranker-v3-5-2026/)；[FutureAGI](https://futureagi.com/blog/best-rerankers-for-rag-2026/)
- jina-reranker-v3：listwise，一次处理 64 文档 / 131K token，BEIR nDCG@10 61.94，0.6B，**CC BY-NC 4.0（限制商用）** — [FutureAGI](https://futureagi.com/blog/best-rerankers-for-rag-2026/)
- Qwen3-Reranker：Apache 2.0、100+ 语言、32K；数字见上文 Qwen 表 — [OpenRouter 对比](https://openrouter.ai/compare/cohere/rerank-4-pro/qwen/qwen3-reranker-8b)
- Anthropic 的重排配置：召回 150 → rerank → 取 20；重排增加延迟与成本，需权衡 — [Anthropic](https://www.anthropic.com/news/contextual-retrieval)

**Late interaction / 多向量（ColBERT 系）**
- 生产线索：ColBERTv2（2022）蒸馏 + 残差压缩、PLAID 降延迟、MUVERA（2024）把多向量检索转为单向量 ANN；LightOn ColBERT-Zero（2026-02）从零训练多向量模型，Apache 2.0；Sentence Transformers v6.0（2026-08-18）原生支持多向量，可加载 PyLate 与 Stanford ColBERT 权重 — [LightOn](https://lighton.ai/lighton-blogs/day-zero-of-multi-vector-retrieval)；[HF blog](https://huggingface.co/blog/multi-vector-encoder)

### Inferences
- 面向内部工程知识（标识符密集：PSM 名、特征名、配置键、指标名、实验 ID），**BM25/精确匹配应是第一公民而不是补充**：Anthropic 的 BM25 增益、“Is Grep All You Need”的 grep 全面优于 dense、CodeRAG-Bench 的“低词法重叠时检索失败”（KQ3）三者指向一致。建议默认 RRF（k=60）起步，再用自有 query 集调加权；监控“精确标识符查询”的 recall 作为独立指标。
- 模型选型（截至 2026-10 的推断）：中文 + 代码 + 可自托管 → Qwen3-Embedding-8B（或 4B 做吞吐）+ Qwen3-Reranker-4B/8B 是最少法律/合规摩擦的组合；若允许闭源 API，代码库可单独用 voyage-code-3/4 建索引（CoQuIR 独立证据支持），但要注意 Voyage 4 系列才共享空间、换代需重嵌。
- 不要信任厂商“MTEB 分数”（闭源旗舰几乎未提交）；内部应建 200–500 条真实问题的 golden set（含 BRIGHT 式“需要推理才能判断相关性”的问题），因为 MTEB 高分与推理检索强相关性很弱（59.0 vs 18）。
- ColBERT/多向量在 2026 已有成熟工具链，但对内部语料的增益缺乏独立证据；可作为第二阶段实验而非首发。

### Gaps
- 没有找到 Cohere Rerank 4 / Qwen3-Reranker / jina-reranker-v3 的同条件头对头基准。
- CoIR 代码检索榜单当前分数、BRIGHT 2026 榜首（ReasonIR/DIVER/Seed1.5-Embedding 等）未能核实（搜索额度耗尽、HF 被屏蔽）；一篇第三方论文（arXiv 2609.20563）表中 Qwen3-Embedding-4B “BRIGHT 64.1” 列标签不明，疑为误读，不采信。
- C-MTEB 2026 年榜单快照、SPLADE/学习型稀疏在 2026 的状态未获取。

---

## KQ3 代码检索：Cursor / Cody / Augment / Claude Code / Codex / Aider / Copilot 的路线与“agentic grep vs 向量索引”证据

### Takeaway
两条路线在 2026 已经明确互补而非替代：Claude Code 官方工具链只有 Glob/Grep(ripgrep)/Read/LSP 而无向量工具，靠 CLAUDE.md + 即时检索 + 子 agent 控制上下文；Cursor 的 Merkle-tree 增量同步 + tree-sitter 分块 + 自训 embedding（基于 agent 轨迹）在其评测中让 agent 问答准确率平均 +12.5%（6.5–23.5%），且“语义检索 + grep 组合最优”；独立研究则显示 harness 设计对结果的影响与检索器同量级。超大 monorepo 的现实做法是：按目录分层 CLAUDE.md/skills + LSP 插件 + 把已有代码搜索/RAG 索引以 MCP 工具暴露给 agent。

### Cited Findings
**Claude Code（Anthropic，[官方文档]）**
- 工具清单中没有任何向量/语义索引工具；Grep 基于 ripgrep（正则语法为 ripgrep 而非 POSIX）；Glob 按修改时间排序、上限 100 文件；Read 单次最多 25,000 token、拒绝 >256 KB 整文件；Bash 输出内联上限约 30,000 字符，超出保存为文件并给 2,000 字符预览 — [Claude Code tools reference](https://code.claude.com/docs/en/tools-reference)
- 代码智能（跳转定义/引用、类型错误）通过 LSP 插件（TypeScript/Python/Go/Rust 等）实现，用于“替代大量文件读取与 grep” — [Claude Code large codebases](https://code.claude.com/docs/en/large-codebases)
- 上下文策略：启动时加载 CLAUDE.md（及祖先目录）、auto memory 前 200 行/25KB、skills 的 name/description；子目录 CLAUDE.md 在 Claude 读写该目录文件时按需加载；内容搜索默认遵守 .gitignore — [Claude Code memory](https://code.claude.com/docs/en/memory)；[how Claude Code works](https://code.claude.com/docs/en/how-claude-code-works)
- Monorepo 指南：分层 CLAUDE.md（root + 每包/子系统）、`claudeMdExcludes` 排除他队文件、`Read` deny 规则屏蔽生成/第三方代码、`worktree.sparsePaths` 稀疏检出、每目录 skills、LSP 插件；并明确写道：“如果你的组织已经在仓库上运行代码搜索或 RAG 索引，把它暴露为 MCP 工具让 Claude 查询，而不是直接读文件”；skills 过多时部分描述会被截断 — [Claude Code large codebases](https://code.claude.com/docs/en/large-codebases)
- Anthropic 的设计理由：即时检索（文件路径、grep、head/tail）避免预检索的陈旧与冗余，缺点是更慢且可能走弯路；推荐“CLAUDE.md 预加载 + 即时探索”的混合策略；子 agent 消耗数万 token 后只返回 1,000–2,000 token 摘要 — [Anthropic Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- Claude Code 官方失败模式：“infinite exploration”——未限定范围的调查会读数百个文件撑满上下文，修复是缩小范围或用子 agent — [Claude Code best practices](https://code.claude.com/docs/en/best-practices)
- 二手观点：索引在每小时变动的代码库里“建成即过期”，无索引省去同步/分块/嵌入管线；反方：大而稳定、高频查询的库会被 grep 反复全量扫描 — [jacar.es](https://jacar.es/en/code-agents-without-vector-search/)；[aiskill.market](https://aiskill.market/blog/agentic-search-vs-rag-why-claude-code-doesnt-index)
- turbopuffer 工程师在 AI Engineer Europe 2026 的评测 [二手]：给 Claude Code 加语义检索使上下文发现“更有选择性”，但 recall 取决于任务类型以及 agent 是否知道该用哪个检索工具 — [AI Engineer talk](https://www.ai.engineer/talks/zKk7sDMGDEQ-benchmarking-semantic-code-retrieval-on-claude)
- 第三方插件 index1 给 Claude Code 加 BM25+向量 hybrid，作者自称广查询下节省 90–99% 上下文 [厂商自报] — [PyPI index1](https://pypi.org/project/index1/)

**Cursor（[厂商自报] + [二手]）**
- 管线：客户端扫描并构建文件哈希 Merkle tree 同步到服务端做增量索引；tree-sitter AST-aware 分块；自研 embedding；向量存 Turbopuffer；服务端不存源码，只返回掩码路径与行范围，客户端本地读文件拼 prompt — [Towards Data Science](https://towardsdatascience.com/how-cursor-actually-indexes-your-codebase/)；[Bito 2026 指南](https://bito.ai/blog/how-cursors-codebase-indexing-works-2026-guide/)
- 2025-11 “Improving agent with semantic search”：离线 Cursor Context Bench 上问答准确率平均 **+12.5%**（按模型 6.5%–23.5%），所有模型均获益；线上 A/B：代码留存 +0.3%（大代码库 +2.6%）、不满意追问 −2.2%；embedding 用 agent 会话轨迹训练；**语义检索与 grep 组合效果最佳** — [Cursor blog](https://cursor.com/blog/semsearch)；[ZenML LLMOps DB 摘要](https://www.zenml.io/llmops-database/enhancing-ai-coding-agent-performance-with-custom-semantic-search)

**Aider repo map（开源，[官方文档]）**
- 用 tree-sitter 从 AST 抽取 definitions/references tags，构建文件依赖图，用图排序算法挑出“被引用最多”的符号，按 `--map-tokens`（默认 1k）预算裁剪后随每次请求发送；map 大小会随聊天状态动态变化（未加文件时可显著变大）；LLM 据此请求需要的文件 — [aider repomap 文档](https://raw.githubusercontent.com/Aider-AI/aider/main/aider/website/docs/repomap.md)；[2023-10-22 原文](https://raw.githubusercontent.com/Aider-AI/aider/main/aider/website/_posts/2023-10-22-repomap.md)
- 第三方实现描述 PageRank 以聊天中提到的标识符做个性化，并用二分搜索把 tags 填到预算的 15% 以内 [二手] — [agentpatterns.ai](https://agentpatterns.ai/context-engineering/repository-map-pattern/)；[RepoMapper](https://github.com/Cryect/RepoMapper)

**Sourcegraph（[官方文档] + [二手]）**
- Deep Search（2025-06，v6.4 research preview，企业版）：接收自然语言问题，作为 agent 调用多种 Code Search 与 Code Navigation 工具后给出详细回答；当时仅支持 Claude Sonnet 4 — [Sourcegraph 6.4 docs](https://6.4.sourcegraph.com/code-search/types/deep-search)
- 底层 Zoekt：trigram 索引 + 语法解析，支持 substring/regexp/布尔；用 universal-ctags 符号信息作为排序关键信号 — [GitHub sourcegraph/zoekt](https://github.com/sourcegraph/zoekt)

**Augment Code（[厂商自报]）**
- Context Engine：对整个技术栈（代码、依赖、文档、风格、最近变更、issue）做实时语义索引，示例从 4,456 个来源筛到 682 个；2026-02 开放 MCP 接口供任意 agent 调用；自称 SWE-bench Pro 51.8%、在 Claude Code/Cursor/Codex 上提升 >70% agentic coding 表现（无独立验证） — [augmentcode.com/context-engine](https://augmentcode.com/context-engine)；[SiliconANGLE 2026-02-06](https://siliconangle.com/2026/02/06/augment-code-makes-semantic-coding-capability-available-ai-agent/)；[morphllm 对比](https://www.morphllm.com/comparisons/augment-code-vs-claude-code)

**定位/检索基准（[独立基准]）**
- LocAgent 表（arXiv 2503.09089）：文件级定位 BM25 Acc@1 38.7% / Acc@5 61.7%；代码专用 embedding CodeRankEmbed 52.6% / 84.7%；Agentless（Claude 3.5）72.6% Acc@1；LocAgent 需要显著更多 LLM 调用 — [arXiv 2503.09089](https://arxiv.org/pdf/2503.09089)
- Agentless（arXiv 2407.01489）分层定位：LLM 看仓库结构选文件 → 剪枝目录 → text-embedding-3-small 向量检索 → 投票合并 → 类/函数 → 编辑位置 — [arXiv 2407.01489](https://www.arxiv.org/pdf/2407.01489)
- SpIDER（arXiv 2512.16956）：BM25 变体在 SWE-PolyBench 上落后于 dense — [arXiv 2512.16956](https://arxiv.org/pdf/2512.16956)
- CodeRAG-Bench（NAACL 2025 Findings）：10 检索器 × 10 模型、约 9k 任务、2,500 万文档；高质量检索能提升代码生成，但检索器常找不到有用上下文（query 与文档词法重叠低时最差），生成器也难以利用多段上下文；无关上下文可能有害 [二手确认] — [arXiv 2406.14497](https://arxiv.org/html/2406.14497v2)；[Moonlight 综述](https://www.themoonlight.io/review/coderag-bench-can-retrieval-augment-code-generation)

**AGENTS.md（跨工具约定）**
- 开放格式，GitHub 约 25k star；Claude Code v2.1.277+ 在无 CLAUDE.md 时直接读取 AGENTS.md，可用 `@AGENTS.md` import 或 symlink 共享一份 — [GitHub agentsmd/agents.md](https://github.com/agentsmd/agents.md)；[Claude Code memory](https://code.claude.com/docs/en/memory)

### Inferences
- 对 TikTok 规模（数百万文件、C++/Python/DSL 混合）的推荐架构推断：
  1. **底层统一的 trigram/词法索引（Zoekt 式）+ 符号索引（ctags/LSP/SCIP）作为 agent 的 grep/定位工具**——这是 grep 路线在 monorepo 上可扩展的前提（本地 ripgrep 无法秒级扫数百万文件）；
  2. **语义索引作为第二工具**而不是唯一入口（Cursor 的“组合最优”、turbopuffer 的“工具选择决定 recall”）；按子系统/仓库分 namespace，Merkle 增量同步；
  3. 两者都通过 **MCP 工具**暴露给 Claude Code/Codex 等 harness（Anthropic 官方推荐方式），工具描述要明确“何时用词法、何时用语义”，并返回路径+行范围而不是大段代码（KQ1 的工具输出原则）；
  4. 以 Aider repo map 思路为每个子系统生成 1–4k token 的“符号地图”放进目录级 CLAUDE.md 或 skill，作为低成本预加载上下文。
- 评测不要只看 retrieval recall：LocAgent/Agentless 数据表明分层 LLM 定位（72.6%）远好于任何单一检索器（≤52.6%），harness 设计（“Is grep”论文中 16 个百分点差距）与检索器同样重要。
- DSL（特征/模型配置 DSL）没有现成 AST 工具时，退而求其次的办法是：生成器侧输出“符号表 + 依赖边”导入到同一符号索引，让 grep/LSP 路线也覆盖 DSL。

### Gaps
- GitHub Copilot（remote index/本地 index 上限）与 OpenAI Codex 的代码上下文机制：docs.github.com 被屏蔽、搜索额度耗尽，未获取。
- Sourcegraph Cody 当前（2026）上下文引擎细节、Deep Search 的定量效果未找到。
- Cursor 索引的规模上限（文件数/大小）、Augment 的独立评测均未找到。
- LongCodeArena、SWE-bench 检索子集的 2026 最新结果未获取。

---

## KQ4 图与结构化知识：GraphRAG / LazyGraphRAG / LightRAG / HippoRAG 2、text-to-SQL 与语义层、推荐系统工件的属性图

### Takeaway
2025–2026 证据对“图”的定位已经收敛：对局部事实问答，向量/词法 RAG 仍是最强基线且 GraphRAG 常常更差；图的价值在“全局/聚合/关联”问题与多跳推理（HippoRAG 2 在 MuSiQue 54.4 显著领先），而 Microsoft 自家 LazyGraphRAG 以 0.1% 的索引成本、>700× 更低的查询成本替代了重索引的 GraphRAG，并在 1M token 上下文的 GPT-4.1 对照下仍胜出。对“配置/特征/实验/上线”这类强结构工件，证据更支持 **语义层 + text-to-SQL**（dbt：90.0→98.2%、84.1→100%；Genie 小样本 53→80→100%）而不是 LLM 抽取的通用知识图。

### Cited Findings
**LazyGraphRAG 与 BenchmarkQED（Microsoft Research，[厂商自报] 但方法公开）**
- 2024-11-25：索引成本与向量 RAG 相同、为完整 GraphRAG 的 0.1%；全局问题答案质量与 GraphRAG Global Search 相当而查询成本低 >700×；在 GraphRAG 全局查询 4% 成本下显著优于全部对照（含 C2）；数据 5,590 篇 AP 新闻、100 条合成查询（50 局部/50 全局）、指标 comprehensiveness/diversity/empowerment；机制：NLP 名词短语抽概念图 + 社区层次、LLM 拆 3–5 子查询、“relevance test budget”控制成本-质量、迭代深化 + map-reduce — [Microsoft Research](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/)
- BenchmarkQED（2025-06-05）：AutoQ 生成 data-local/activity-local/data-global/activity-global 四类查询各 50 条、6 次试验、GPT-4.1 判官；同用 GPT-4o 生成器时 LazyGraphRAG 在全部 96 组对照中胜出（仅 1 组不显著）；局部查询最强对手是向量 RAG，全局查询最强对手是 GraphRAG Global/Drift；**把向量 RAG 上下文从 8k 扩到 120k 并未缩小差距；GPT-4.1 1M token 上下文下 LazyGraphRAG 仍全面胜出**（仅 DataLocal 的 relevance 不显著） — [Microsoft Research BenchmarkQED](https://www.microsoft.com/en-us/research/blog/benchmarkqed-automated-benchmarking-of-rag-systems/)

**LightRAG（HKU，开源，[厂商自报]）**
- 对 NaiveRAG 胜率：Agriculture 67.6%、CS 61.2%、Legal 84.8%、Mix 60.0%；对 GraphRAG 胜率 54.8/52.0/52.8/49.6%（Mix 上略输）；优势维度主要是 Diversity；检索模式 local/global/hybrid/naive/mix（默认 mix）；增量更新可复用索引期 LLM 缓存；无 token/成本数字 — [GitHub HKUDS/LightRAG](https://github.com/HKUDS/LightRAG)

**HippoRAG 2（OSU，ICML 2025，arXiv 2502.14802，[独立论文自评]）**
- OpenIE + Personalized PageRank + passage 节点；声称在 factual（NQ、PopQA）、sense-making（NarrativeQA）、associativity（MuSiQue、2Wiki、HotpotQA、LV-Eval）全类别超过 NV-Embed-v2/GraphRAG/LightRAG/RAPTOR，且离线索引资源显著更少 — [GitHub OSU-NLP-Group/HippoRAG](https://github.com/OSU-NLP-Group/HippoRAG)
- 2026 年 RAGU 论文对照：HippoRAG 2 在 MuSiQue 54.4 vs RAGU 40.1，差距在简短答案提示下缩小 — [arXiv 2607.11683](https://arxiv.org/pdf/2607.11683)
- 综述性对比 [二手]：HippoRAG 2 强在多跳；LazyGraphRAG/LightRAG 强在成本 — [Medium Graph Praxis](https://medium.com/graph-praxis/graphrag-vs-hipporag-vs-pathrag-vs-og-rag-choosing-the-right-architecture-for-your-knowledge-graph-a4745e8b125f)

**“When to use Graphs in RAG”（GraphRAG-Bench，ICLR 2026，[独立基准]）**
- 动机陈述：“GraphRAG 在许多真实任务上频繁不如 vanilla RAG”；基准分四级任务（fact retrieval / complex reasoning / contextual summarization / creative generation），评估整条管线（建图→检索→生成）；批评 HotpotQA/MultiHopRAG 等只强调检索难度而忽视推理复杂度 — [arXiv 2506.05690](https://arxiv.org/pdf/2506.05690)；[GitHub GraphRAG-Bench](https://github.com/GraphRAG-Bench/GraphRAG-Benchmark)

**Text-to-SQL 与语义层（[厂商自报]/[二手] 居多）**
- Uber QueryGPT：引入 Workspaces（按 Ads/Mobility/Core Services 等业务域策划的 SQL 样本 + 表集合）与 intent 分类，原因是“随着表和 SQL 样本增多准确率下降”且纯相似度检索返回不相关结果；限量发布 300 DAU、78% 用户报告显著省时、写 SQL 从约 10 分钟降到 3 分钟（非准确率指标） — [Uber Engineering](https://www.uber.com/blog/query-gpt)；[ZenML LLMOps DB](https://www.zenml.io/llmops-database/natural-language-to-sql-query-generation-at-scale)
- dbt Labs（2026-04）：在语义层上回答使 Claude Sonnet 4.6 90.0%→98.2%、GPT-5.3-Codex 84.1%→100%（11 题）；仅做 schema 建模（无语义层）即 64.5%→90.0%；dbt 自承基线把整个 schema 塞进上下文、大库不现实 — [dbt blog](https://docs.getdbt.com/blog/semantic-layer-vs-text-to-sql-2026)
- Databricks AI/BI Genie 被引述：15 题供应链集 53%（裸 schema）→80%（元数据增强）→100%（指标定义 + 示例 SQL）；Genie Ontology 把工程师纠错沉淀为语义规则 — [Atlan](https://atlan.com/know/ai-agent/data-for-ai/text-to-sql-for-enterprise/)；[businesstechnavigator](https://businesstechnavigator.com/news/databricks-genie-agents-ontology-2026)
- Snowflake Cortex Analyst 自称语义模型下 >90% SQL 准确率、约为单发 GPT-4o 的 2× [厂商自报]；批评者指出各研究差距主要反映“schema 翻译工作做了多少”与评分宽松度 — [HackerNoon](https://hackernoon.com/why-better-schema-modeling-beats-better-text-to-sql-models)

**推荐系统工件知识库（直接相关的两篇工业论文，[论文自述]，全文未能打开）**
- Kuaishou AgentX（arXiv 2606.26859，2026）：System KB 是结构化领域 wiki，存模型架构、特征定义、pipeline 边界，用于减少 Brainstorm Agent 提出“代码路径敏感”想法时的幻觉；**三层结构：schema 层、Markdown wiki 条目层、可回溯的原始来源层**；通过 ingest–query–lint 生命周期保鲜；部署中 3 个 AgentX worker 处理 374 个实验想法产出 10 个可发表结果 — [arXiv 2606.26859](https://arxiv.org/pdf/2606.26859)；[besthub 解读](https://www.besthub.dev/articles/how-kuaishou-s-agentx-enables-self-iterating-industrial-recommender-systems-70bd1a0f6215)
- RecSys Factory（arXiv 2608.11241，v1.0 2026-07-01）：PitfallStore 以 SQLite 表存 400 条运维教训，严重度 7 高/1 低/其余中，来源 200 条来自 skill spec 文件、194 条来自项目 changelog、其余来自根级文档；高频标签 log、data、spark、scheduler、cvr；与 Tencent 的归属未能从摘要确认 — [arXiv 2608.11241](https://arxiv.org/pdf/2608.11241)

### Inferences
- **什么时候图胜过向量**（基于 BenchmarkQED/LightRAG/HippoRAG 2/GraphRAG-Bench）：问题需要跨多个文档聚合（“过去半年哪些实验改了 user tower 并上线”）、多跳关联（特征 → 模型 → 实验 → 上线 → 事故）、或要求答案覆盖面/多样性时；单点事实（“这个配置项默认值是多少”）用词法/向量更准更便宜。成本：LLM 抽取式 GraphRAG 索引成本是向量 RAG 的 ~1000×（LazyGraphRAG 0.1% 的反推），对持续变动的工程语料不可持续；LazyGraphRAG 式“索引时只做 NLP 概念图、查询时花 LLM 预算”更合适。
- 对推荐系统工件，**不要用 LLM 从文本里“抽”图**，而应从系统本身导出 **属性图/关系表**：特征注册表、模型配置、实验平台、发布系统、服务拓扑（PSM 上下游）都已有结构化事实源；把它们建成带版本与时间的表（Postgres/图库均可）并配 **语义层（指标/实体/关系定义 + 示例 SQL/Cypher）**，用 text-to-SQL/Cypher 作为 agent 的一个工具（dbt/Genie 的证据说明语义层是准确率的主要杠杆）。AgentX 的“schema + wiki + 原始来源”三层正是这种设计。
- 非结构化文档中的实体（特征名、实验 ID）应做 **实体链接到上述结构化表**（轻量 KG），这比全文 GraphRAG 便宜得多，且能支持“先查表、再读文档”的两跳。
- 评测要分类型做：局部事实（向量/词法基线必须赢）、全局聚合（图/语义层应赢）、多跳（HippoRAG 2 风格 PPR 可作候选）。

### Gaps
- GraphRAG-Bench 的具体结论（哪类任务图胜、胜多少、建图 token 成本）无法打开（arXiv/github.io 被屏蔽，README 不含榜单）。
- HippoRAG 2 对 NV-Embed-v2/GraphRAG/LightRAG 的精确分数在 README 中以图片形式存在，未获取。
- 未找到“服务拓扑/特征血缘知识图 + LLM agent 做 RCA”的 2025–2026 公开量化案例（搜索额度耗尽）。
- Uber QueryGPT 的 SQL 准确率指标未公开。

---

## KQ5 Agentic 检索 / DeepSearch：架构、RL 训练的搜索 agent、相对单发 RAG 的收益与代价，以及在内部 KB 上的落地

### Takeaway
DeepSearch = “search → read → reason” 的带预算状态机循环（Jina 2025-02 定义），工业实现统一为 orchestrator + 并行子 agent + 独立引用/验证阶段；收益是实打实的（Anthropic 多 agent 比单 agent Opus 4 高 90.2%；OpenAI Deep Research BrowseComp 51.5% vs GPT-4o+浏览 1.9%；RL 训练使 Kimi-Researcher HLE 8.6%→26.9%），代价同样明确（多 agent 消耗约 15× 聊天 token，token 用量解释了 BrowseComp 80% 的方差；每题平均 12–23 步检索/推理，延迟以分钟计）。对内部工程知识，“RAG 已死”不成立——证据显示 harness、工具交付方式和词法检索质量对 agentic 搜索结果的影响与模型同级，DeepSearch 的正确姿势是“把高质量的词法/语义/结构化检索做成工具，让 agent 迭代调用并带预算与验证”。

### Cited Findings
**定义与参考架构**
- Jina “A Practical Guide to Implementing DeepSearch/DeepResearch”（Han Xiao，2025-02-25）：DeepSearch 是读-搜-推理的循环直到找到答案或超预算，可视为带 searcher/reader 工具的 LLM agent，本质是由 LLM 控制状态转移的状态机；可用普通模型加精心提示，或用推理模型推断下一步；node-deepresearch 于 2025-02-02（与 OpenAI/Google 同日）开源；早期“长报告”原型严重幻觉、章节冗余，促成后续按句/段的 grounding 与事实核查 — [Jina AI（搜索摘要，站点被屏蔽）](https://jina.ai/news/a-practical-guide-to-implementing-deepsearch-deepresearch/)
- node-DeepResearch 流程图：初始化 → 检查 token 预算（超出进入 Beast Mode 强制作答）→ 从 gaps 队列取当前问题 → 模型选 answer/reflect/search/visit；answer 若为原问题则评估，“definitive 且有引用”才结束，否则记为 bad attempt 并重置；reflect 产生的子问题去重后入队；search 新 URL 入库、visit 新内容入知识库；某动作无新产出时下一步禁用该动作；示例运行步数 2/3/11/42 — [GitHub jina-ai/node-DeepResearch](https://github.com/jina-ai/node-DeepResearch)
- 第三方 API 描述：plan → search → read → reflect → answer — [TypingMind docs](https://docs.typingmind.com/manage-and-connect-ai-models/jina-deep-research)

**Anthropic 多 agent 研究系统（2025-06-13，[厂商自报]）**
- Opus 4 lead + Sonnet 4 子 agent 的系统在内部研究评测上比单 agent Opus 4 高 **90.2%**；agent 用 ~4× 聊天 token，多 agent ~15×；BrowseComp 上 token 用量解释 80% 方差，加上工具调用次数与模型选择解释 95%；升级到 Sonnet 4 比在 Sonnet 3.7 上把 token 预算翻倍收益更大；并行使复杂查询耗时最多降 90%；上下文超过 200k 被截断，lead 把计划写入 memory；工具描述由 agent 重写后任务完成时间 −40% — [Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system)
- 提示中的 effort scaling 规则：简单事实 1 个 agent、3–10 次工具调用；对比类 2–4 子 agent 各 10–15 次；复杂研究 >10 子 agent 明确分工；lead 并行起 3–5 个子 agent、子 agent 并行用 3+ 工具；搜索策略“短而宽→逐步收窄”；独立 CitationAgent 做引用归属；LLM-as-judge 单次打分 0–1 并给 pass/fail — [Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system)
- 观察到的失败：为简单问题起 50 个子 agent、无休止寻找不存在的来源、子 agent 互相用冗余更新干扰、已足够仍继续搜索、重复劳动、冗长查询、选错工具、偏好 SEO 内容农场 — [Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system)

**OpenAI Deep Research / BrowseComp（[厂商自报]）**
- BrowseComp（2025-04）1,266 题；Deep Research 51.5%（模型针对 BrowseComp 类任务训练）；GPT-4o 加浏览仅从 0.6% 升到 1.9%——“仅有浏览能力不够，还需策略性推理与路径选择” — [OpenAI BrowseComp](https://openai.com/index/browsecomp/)
- 第三方榜单（OpenAI 自报数字）：GPT-5.4 82.7%、GPT-5.2 Pro 77.9%；提醒单次通过率与 best-of-N/重工具系统不可直接比较 — [steel.dev BrowseComp 榜](https://leaderboard.steel.dev/leaderboards/browsecomp)

**RL 训练的搜索 agent**
- Tongyi DeepResearch（阿里，2025-09-17）：30.5B 总参/3.3B 激活，128K 上下文；训练 = 合成数据 + agentic 持续预训练 + SFT + 严格 on-policy GRPO；推理模式 ReAct 与 IterResearch “Heavy”（测试时扩展）；自报 HLE 32.9、BrowseComp 43.4、BrowseComp-ZH 46.7、xbench-DeepSearch 75；WebAgent 家族 18 项工作（WebWalker、WebSailor/V2、WebWatcher、WebWeaver、ReSum、AgentFold 等） — [GitHub Alibaba-NLP/DeepResearch](https://github.com/Alibaba-NLP/DeepResearch)；[The Sequence 解读](https://thesequence.substack.com/p/the-sequence-radar-723-alibabas-agentic)
- Kimi-Researcher（Moonshot，2025-06）：端到端 agentic RL；每任务平均 23 步推理、探索 200+ URL（一处称 74 关键词/206 URL）；HLE 8.6%→26.9% — [Kimi 帮助页](https://www.kimi.com/en/help/deep-research/deep-research-overview)；[Medium 解读](https://ritvik19.medium.com/papers-explained-417-kimi-researcher-baa1c9f4ae68)
- Search-R1（arXiv 2503.09516）：基于 veRL，PPO/GRPO，E5 检索器 + Wikipedia，NQ+HotpotQA 训练 — [GitHub Search-R1](https://github.com/PeterGriffinJin/Search-R1)
- R1-Searcher（2025-03-08，arXiv 2503.05592）：两阶段结果监督 RL（Reinforce++，无冷启动 SFT）：先学“何时调用检索”（格式 + 检索奖励），再学“边搜边答”（F1 奖励）；Qwen-2.5-7B-Base 在域内（HotpotQA/2Wiki）与域外（MuSiQue/Bamboogle）均最佳，Llama-3.1-8B 版超过 GPT-4o-mini 基线；Bamboogle 上接入 Google 优于本地检索 — [GitHub RUCAIBox/R1-Searcher](https://github.com/RUCAIBox/R1-Searcher)
- ZeroSearch（2025-05-08，arXiv 2505.04588）：用 3B/7B/14B “模拟搜索引擎”LLM 训练（推荐 14B），避免真实搜索 API 成本；自称优于 Search-R1 — [GitHub Alibaba-NLP/ZeroSearch](https://github.com/Alibaba-NLP/ZeroSearch)；[DAIR.AI](https://academy.dair.ai/papers/zerosearch)
- BrowseComp-Plus（ACL 2026，arXiv 2508.06600）：固定 ~100K 人工核验文档语料、830 题、检索工具返回 top-5（每篇 ≤512 token）、Qwen3-32B 判官，预置 BM25 与 Qwen3-Embedding 索引，可复现 OpenAI/Anthropic/Gemini/Qwen/GLM/Search-R1/Tongyi 等；示例 gpt-oss-20b 准确率 32.17%、**平均每题 12.6 次搜索调用** — [GitHub texttron/BrowseComp-Plus](https://github.com/texttron/BrowseComp-Plus)
- “Is Grep All You Need”（2026-05）：harness 与交付方式对 agentic 搜索结果的影响与检索器同级（见 KQ2） — [arXiv 2605.15184](https://arxiv.org/abs/2605.15184)

**在内部 KB 上的工具化落地（[官方文档]）**
- Claude Code：MCP 工具定义默认延迟加载（只占用名称与服务器说明的上下文），按需通过 tool search 加载；官方建议把组织已有代码搜索/RAG 索引以 MCP 工具暴露 — [how Claude Code works](https://code.claude.com/docs/en/how-claude-code-works)；[large codebases](https://code.claude.com/docs/en/large-codebases)
- Anthropic 工具设计：工具集小而不重叠（含糊的工具选择对 agent 的伤害与对人一样）；工具描述影响显著；返回分页/过滤/截断并告诉 agent 如何调整；强评测任务可能需要“数十次工具调用” — [Writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)；[Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

### Inferences
- **“RAG 已死、长上下文 + agentic 搜索取代一切”对内部工程知识不成立**：(a) agentic 搜索的每一步仍是检索（grep/向量/SQL），检索质量上限直接决定 agent 上限（BrowseComp-Plus 用固定语料 + 不同检索器就是为了量化这一点；CodeRAG-Bench 与 Anthropic 的 BM25 结果也说明检索器差异显著）；(b) LazyGraphRAG 在 1M 上下文对照下仍胜出、Chroma 上下文腐蚀（KQ6）说明“全塞进去”在质量上也不占优；(c) 成本 15× 与分钟级延迟意味着 DeepSearch 只应用于高价值的复杂问题，简单查询仍走单发 RAG。
- 推荐的 **DeepSearch over internal KB 架构（推断）**：
  1. 路由层：按问题类型分流——单点事实/配置项 → 单发 hybrid RAG（<2 s）；跨系统/多跳/“为什么”/排障 → DeepSearch（预算 10–30 次工具调用、1–3 个子 agent）；
  2. 工具层（MCP）：`lexical_search`（Zoekt/ES，支持 repo/path/时间过滤）、`semantic_search`（Qwen3/voyage 索引，按 namespace）、`kb_sql`（语义层上的 text-to-SQL：实验/特征/发布/拓扑）、`read_file`/`read_doc`（分页、25k token 上限）、`fetch_runbook`（Skill 加载）；
  3. 循环控制：Jina 式 gaps 队列 + 去重 + “无新产出即禁用动作” + 预算耗尽 Beast Mode；Anthropic 式 effort scaling 写进 system prompt；
  4. 验证层：独立 CitationAgent 把每个结论绑定到 path@commit / doc@version / SQL 结果，并做“新鲜度”检查（文档更新时间 vs 代码最近 commit）；
  5. 评测：按 Anthropic 做法先用 ~20 条真实复杂问题做 LLM-as-judge（事实、引用、完整、来源质量、工具效率）再扩大。
- RL 训练搜索 agent（Search-R1/Tongyi）在 2026 的工业意义：若部门有数千条带答案的内部问题与可复现的检索环境（BrowseComp-Plus 式固定语料），可在 7B–30B 开源模型上做 agentic RL 以降低对闭源模型的依赖；但缺乏公开的“内部 KB 场景”RL 收益数据，应视为第二阶段实验。

### Gaps
- Jina 文章全文（URL 排序、snippet 选择、评估器的 definitive/freshness/plurality/completeness/strict 细节、token 预算值）未能打开，仅 README 流程图。
- OpenAI Deep Research 系统卡（工具调用次数、延迟）与 Google Gemini Deep Research / Perplexity 的架构细节未获取（站点屏蔽 + 搜索额度耗尽）。
- Search-R1/R1-Searcher/ZeroSearch/WebSailor 的精确分数表均为图片或论文内，未能读取；ZeroSearch 的成本对比（真实搜索 API vs GPU 模拟）未核实。
- BrowseComp-Plus 论文的核心发现（检索器质量对 agent 准确率的量化影响）未能读取，README 仅有示例文件。
- 没有找到 2025–2026 公开的“企业内部 KB 上 DeepSearch vs 单发 RAG”的量化对照。

---

## KQ6 长上下文 vs 检索：context rot、MRCR、prompt caching 经济学、“把文档塞进 prompt”与混合设计

### Takeaway
长上下文窗口（1M）并没有消除检索：Chroma 的 18 模型实验证明即便简单任务性能也随输入长度下降、干扰项与“连贯的长文档”会加剧退化；MRCR v2 在 1M 下各家差异巨大（Opus 4.6 ~76–78%、GPT-5.4 ~37%、Gemini 3.x Pro ~25%，版本不可比）；Microsoft 在 1M 上下文的 GPT-4.1 对照中结构化检索仍胜出。经济上，Anthropic 缓存读取为 0.1×（新模型 0.025–0.05×）、写入 1.25×/2×，使“固定文档前缀 + 变动问题”成本可降约一个数量级，但只对 <200k token 的稳定语料划算。混合模式（预加载 CLAUDE.md/skills 元数据 → 即时检索 → 命中后整文档/整文件读取）是 2026 的主流设计。

### Cited Findings
**Context rot（Chroma，2025-07，技术报告站点被屏蔽，以下为 GitHub + [二手]）**
- 报告作者 Hong/Troynikov/Huber；三类任务：带语义（非词法）needle 的 NIAH 扩展、LongMemEval、Repeated Words — [GitHub chroma-core/context-rot](https://github.com/chroma-core/context-rot)
- 测试 18 个前沿模型（GPT-4.1、Claude 4、Gemini 2.5、Qwen3 等）：即便简单任务准确率也随输入变长下降；相关信息在开头/结尾优于中部；相似但错误的干扰段落明显伤害准确率，GPT 倾向幻觉、Claude 倾向拒答；**连贯结构良好的文档比随机打乱的 chunk 更难检索**；Repeated Words 从 25 到 10,000 词、1,090 种长度×位置变体 — [Morph 综述](https://www.morphllm.com/context-rot)；[Cobus Greyling](https://cobusgreyling.substack.com/p/llm-context-rot)；[DAIR.AI](https://academy.dair.ai/papers/context-rot)
- Anthropic 官方同样用 “context rot” 描述：上下文是有限注意力预算，token 间关系按 n² 增长 — [Anthropic Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)；Claude Code 文档：“上下文填满后性能下降”，建议 `/clear`、`/compact`，自动压缩先清旧工具输出再摘要 — [Claude Code best practices](https://code.claude.com/docs/en/best-practices)；[how Claude Code works](https://code.claude.com/docs/en/how-claude-code-works)

**MRCR（[二手] 聚合，版本不可比）**
- 2024 Michelangelo 论文：Gemini 1.5 Pro MRCR 从 128K 到 1M 不退化，GPT/Claude 在 128K 处下滑更陡 — [arXiv 2409.12640](https://arxiv.org/pdf/2409.12640)
- 2026-03 第三方汇总 MRCR v2（8-needle）@1M：Claude Opus 4.6 76%，GPT-5.4 36.6%（512K–1M 段），Gemini 3 Pro 24.5%；另一来源 Opus 4.6 78.3%、Sonnet 4.6 65.1%、Gemini 3.1 Pro 25.9% — [yage.ai 2026-03-15](https://yage.ai/share/long-context-benchmark-en-20260315.html)；[benchmarklist MRCR 1M](https://benchmarklist.com/benchmarks/mrcr_1m/)
- HELM Long Context（Stanford CRFM，2025-09-29）：厂商各自使用不同版本的 NIAH/MRCR，“既不全面也不可比” — [HELM Long Context](https://crfm.stanford.edu/2025/09/29/helm-long-context.html)

**RAG vs 长上下文的系统研究（[独立基准]）**
- Self-Route（EMNLP 2024 Industry，arXiv 2407.16833）：资源充足时长上下文平均优于 RAG，但 RAG 便宜得多；用模型自评路由可在接近 LC 质量下大幅降成本 — [arXiv 2407.16833](https://arxiv.org/abs/2407.16833v1)
- LaRA（2025-02，arXiv 2502.09977）“No Silver Bullet”：无普适赢家；模型越弱 RAG 收益越大 — [arXiv 2502.09977](https://arxiv.org/html/2502.09977v1)
- Microsoft BenchmarkQED：向量 RAG 从 8k 扩到 120k 不改善相对表现；GPT-4.1 1M 上下文下 LazyGraphRAG 仍胜（见 KQ4） — [Microsoft Research](https://www.microsoft.com/en-us/research/blog/benchmarkqed-automated-benchmarking-of-rag-systems/)
- Anthropic：<200k token 知识库直接塞 prompt；更大才需要 RAG — [Anthropic](https://www.anthropic.com/news/contextual-retrieval)
- “More Documents, Same Length”（arXiv 2503.04388）：只给支持文档（更短上下文）显著优于混入其他内容；大模型下随机文档增多反而改善，说明“相似但无关”的检索结果最具干扰 — [arXiv 2503.04388](https://arxiv.org/pdf/2503.04388)

**Prompt caching 经济学（Anthropic [官方文档]，2026-10 读取）**
- 5 分钟缓存写入 1.25× 基价、1 小时写入 2×、读取 0.1×（Fable 5.1/Mythos 5.1 为 0.025×，Opus 5.5/Sonnet 5.5 为 0.05×）；最小可缓存长度按模型 512/1024/2048/4096 token；TTL 每次命中免费刷新；示例价格（$/百万 token，基价/5m 写/1h 写/读/输出）：Sonnet 4.6 $3/$3.75/$6/$0.30/$15，Opus 4.6 $5/$6.25/$10/$0.50/$25，Haiku 4.5 $1/$1.25/$2/$0.10/$5，Opus 5.5 $4/$5/$8/$0.20/$20 — [Anthropic prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- Contextual Retrieval 的情境生成正是用缓存把整篇文档缓存一次、逐 chunk 引用，达到 $1.02/百万 token — [Anthropic](https://www.anthropic.com/news/contextual-retrieval)

**“把文档塞进 prompt”的制度化形式**
- CLAUDE.md：每次会话加载；官方建议 **每个文件 <200 行**（更长会消耗上下文并降低遵循度）；`@path` import 也在启动时加载、不省上下文；矛盾指令会被任意取舍；子目录文件按需加载；`claudeMdExcludes` 排除 — [Claude Code memory](https://code.claude.com/docs/en/memory)
- llms.txt（Answer.AI 提案）：站点根目录的 Markdown 索引 + 每页 `.md` 版本；OpenAI/Anthropic/Gemini 为开发者文档发布；Mintlify/GitBook/Yoast/Wix 自动生成；Chrome Lighthouse 审计；**无任何 agent/爬虫实际使用率数据** — [GitHub AnswerDotAI/llms-txt](https://github.com/AnswerDotAI/llms-txt)；Claude Code 文档自身在每页头部提供 llms.txt 索引 — [code.claude.com](https://code.claude.com/docs/en/memory)

### Inferences
- 对部门级 KB（估计远超 200k token），正确模式是 **“检索定位 → 整文档/整文件加载”**：Chroma 发现“连贯长文档更难在其中定位”，但对已命中的单篇文档，整篇读入比碎片 chunk 更利于理解；Claude Code 的 Read（25k token/次，分页）与 LazyGraphRAG 的 chunk→社区→claim 都体现“先粗定位再细读”。
- 缓存经济学的落地点：(1) 稳定的系统提示 + 工具定义 + skills 元数据 + 子系统符号地图作为缓存前缀（每会话重复命中，0.1× 成本）；(2) 批处理类任务（为每个 chunk 生成情境、为每个实验记录做摘要）把文档作为缓存前缀逐项调用；(3) 1 小时 TTL 适合持续 agent 会话。避免把频繁变动的日志/代码放在缓存前缀。
- 不要用 1M 上下文替代索引：即便 Opus 4.6 在 MRCR@1M 达 ~78%，意味着约 1/5 的多针检索失败，且各家差异大、成本高。
- CLAUDE.md 200 行限制意味着“部门知识”绝大多数必须走 skills/rules/检索，而非常驻上下文（见 KQ7）。

### Gaps
- Chroma 报告的精确数字（各模型下降幅度、LongMemEval full vs focused 差距）未能读取。
- OpenAI / Gemini 的缓存折扣与 TTL 在本次搜索中只找到互相矛盾的内容农场页面，未采用；需查官方定价页。
- llms.txt 是否真的被 agent 消费：无证据。

---

## KQ7 Agent 消费的知识格式：Skills / playbooks / pitfalls / memory / AGENTS.md，以及“skill vs chunk vs memory”的划分依据

### Takeaway
2025-10 以来形成了一套清晰的分层：常驻上下文只放 <200 行的 CLAUDE.md/AGENTS.md（命令、约定、架构决策），多步流程与领域参考进 SKILL.md（三级渐进披露：元数据常驻 → 正文按需 → 附件/脚本按需，“可捆绑的上下文实际上无上限”），Claude 自己学到的纠错/偏好进 auto memory（前 200 行/25KB 常驻），其余一切走检索。工业推荐系统的两篇论文把“踩坑库”（RecSys Factory PitfallStore 400 条、半数来自 skill spec、近半来自 changelog）和“系统 wiki（schema + Markdown + 原始来源）”做成一等公民；策划式程序性知识优于原始检索的证据来自 ACE（AppWorld +10.6%、FiNER +8.6%，比 Dynamic Cheatsheet 延迟 −91.5%/成本 −83.6%）、Dynamic Cheatsheet（Game of 24 10%→99%）与 ExpeL（ALFWorld put 83% vs ReAct 46%）。

### Cited Findings
**Agent Skills（Anthropic，2025-10-16；2025-12-18 成为开放标准，[官方]）**
- Skill = 目录 + SKILL.md（YAML frontmatter 必含 name、description）+ 可选脚本/资源；渐进披露三级：(1) 启动时只把所有 skill 的 name/description 放入 system prompt；(2) 相关时读入整个 SKILL.md；(3) 捆绑文件仅在需要时读取；“有文件系统与代码执行的 agent 不必把整个 skill 读入上下文，可捆绑的上下文实际上无上限” — [Anthropic Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- 什么进 skill：模型缺乏的程序性知识与组织上下文；从真实工作中捕获的成功做法与常见错误；确定性或昂贵操作写成脚本（“用 token 生成做排序比运行排序算法贵”）；SKILL.md 过大时拆文件并把很少同时用到的内容放在不同路径；先用代表性任务评测找真实缺口再写 skill；name/description 决定触发 — [Anthropic Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- 安全：恶意 skill 可致数据外泄；只装可信来源，审计脚本/依赖/图片与外联指令 — [Anthropic Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- 二手预算经验（未经官方确认）：每个 skill 元数据约 100 token；正文建议 <5,000 token / ~500 行 — [SwirlAI](https://www.newsletter.swirlai.com/p/agent-skills-progressive-disclosure)；[DZone](https://dzone.com/articles/progressive-disclosure-ai-agents)
- Claude Code 实践：skill 可 `disable-model-invocation: true` 仅手动触发；可用 `paths` glob 按文件模式自动加载；每目录 `.claude/skills/`；skill 过多时“有些 skill 会完全失去描述”，建议描述短且以请求会包含的词开头；用 OpenTelemetry `skill_activated` 事件统计使用率以合并/退役 — [Claude Code large codebases](https://code.claude.com/docs/en/large-codebases)；[best practices](https://code.claude.com/docs/en/best-practices)

**CLAUDE.md / AGENTS.md / auto memory（[官方文档]）**
- CLAUDE.md 与 auto memory 都在每次会话开始加载，被视为“上下文而非强制配置”（要硬性阻止用 PreToolUse hook）；auto memory 由 Claude 根据纠正与偏好自写，按仓库存储、跨 worktree 共享，常驻前 200 行/25KB，含 `type`（如 project）字段 — [Claude Code memory](https://code.claude.com/docs/en/memory)
- CLAUDE.md 内容规则：只放每次会话都该知道的事实（构建命令、约定、布局、“always do X”）；“如果一条是多步流程或只与代码库一部分相关，移到 skill 或 path-scoped rule”；目标 <200 行；include/exclude 表：包含“Claude 猜不到的命令、与默认不同的风格、测试方式、仓库礼仪、架构决策、环境怪癖、非显然的坑”，排除“读代码能推出的、标准约定、详细 API 文档（给链接）、频繁变化的信息、长教程、逐文件描述” — [Claude Code memory](https://code.claude.com/docs/en/memory)；[best practices](https://code.claude.com/docs/en/best-practices)
- 层级：managed（组织）→ user `~/.claude/CLAUDE.md` → project `./CLAUDE.md` → `CLAUDE.local.md`；`.claude/rules/*.md` 可按 `paths:` 作用域加载；import 最多 4 跳；大 monorepo 用 `claudeMdExcludes`；Stop hook 可在会话结束时提议 CLAUDE.md 更新；“大模型换代后重审规则” — [Claude Code memory](https://code.claude.com/docs/en/memory)；[large codebases](https://code.claude.com/docs/en/large-codebases)
- 二手研究引述：ETH Zurich + LogicStar 的研究发现上下文文件只在提供 agent 无法自行发现的信息（命令、特殊约定、比模型新的知识）时有益，重复代码已显示的内容只增加成本；67 个热门仓库的 AGENTS.md 中位数约 5,400 字符 — [mac.install.guide 汇总](https://mac.install.guide/ai/agent-instructions/best-practices)；[HumanLayer](https://www.humanlayer.dev/blog/writing-a-good-claude-md)
- AGENTS.md 最小样例三段：Dev environment tips、Testing instructions、PR instructions — [GitHub agentsmd/agents.md](https://github.com/agentsmd/agents.md)

**工业推荐系统的知识库形态（[论文自述]）**
- RecSys Factory PitfallStore：400 条（v1.0，2026-07-01）、SQLite、严重度分级（7 高/1 低）、来源 skill spec 200 条 + changelog 194 条 + 根级文档，标签 log/data/spark/scheduler/cvr；论文主题是“把 LLM agent 自主性限定在工业推荐生命周期的决策点” — [arXiv 2608.11241](https://arxiv.org/pdf/2608.11241)
- Kuaishou AgentX System KB：schema + Markdown wiki + 原始来源三层，ingest–query–lint 保鲜 — [arXiv 2606.26859](https://arxiv.org/pdf/2606.26859)

**策划式程序性知识 vs 原始检索的证据（[独立论文自评]）**
- ACE（Agentic Context Engineering，ICLR 2026，arXiv 2510.04618）：把上下文当作由 generator/reflector/curator 增量更新的 playbook，而非压缩摘要；agents（AppWorld）+10.6%、finance +8.6%；在线 AppWorld ReAct+ACE 59.5% vs Dynamic Cheatsheet 51.9%；对 DC 在 FiNER 在线设置延迟 −91.5%、token 成本 −83.6%；指出 DC 的两类失败：brevity bias 与 context collapse（一例上下文从 18,282 token 塌缩到 122，准确率 66.7%→57.1%）；用更小开源模型追平 AppWorld 榜首生产级 agent、在 test-challenge 上超过 — [arXiv 2510.04618](https://arxiv.org/pdf/2510.04618v1)；[ICLR 2026](https://iclr.cc/virtual/2026/poster/10008343)；[DAIR.AI](https://academy.dair.ai/papers/agentic-context-engineering-ace)
- Dynamic Cheatsheet（arXiv 2504.07952）：推理时维护“可复用策略/代码片段”记忆；GPT-4o Game of 24 ~10%→99%，Claude 3.5 Sonnet AIME 准确率翻倍以上，Math Equation Balancer ~50%→接近满分，GPQA-Diamond +~9%，MMLU-Pro 工程/物理 +~8%；三种变体 Cumulative / RetrievalSynthesis / CumulativeRetrieval — [GitHub suzgunmirac/dynamic-cheatsheet](https://github.com/suzgunmirac/dynamic-cheatsheet)
- ExpeL（AAAI 2024）：经验池 + 自然语言 insight 抽取 + 按任务/思路相似度检索成功轨迹；ALFWorld “put” 83% vs ReAct 46%、“clean” 73% vs 61%，其余任务收益不均 — [arXiv 2308.10144](https://arxiv.org/html/2308.10144v3)；[GitHub LeapLabTHU/ExpeL](https://github.com/LeapLabTHU/ExpeL)
- Anthropic 的 structured note-taking：agent 把进度/决策写到上下文之外的 NOTES.md 并在压缩后重载，Pokémon 例子跨 1,234 步保持目标 — [Anthropic Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

### Inferences
- **决策树（推断，综合官方规则与论文）**：
  - 每次会话都需要、且 agent 无法自行推出、且稳定 → CLAUDE.md/AGENTS.md（<200 行，按目录分层）；
  - 多步流程、特定子系统的操作手册、排障 runbook、带脚本的检查 → Skill（name/description 精心写，正文 <5k token，细节放 references/，可执行步骤放 scripts/）；
  - 踩坑/教训（“X 配置下 Spark 作业会 OOM”）→ 结构化 PitfallStore（表：触发条件、症状、修复、严重度、标签、来源 changelog/事故），同时以“按任务类型检索 top-k 并注入”的方式使用（ExpeL/ACE 的 retrieval-then-inject），而非塞进 CLAUDE.md；
  - 个人/会话级纠正与偏好 → auto memory；
  - 事实性长文档（设计文档、评审记录、论文）→ 检索 chunk（KQ1）；
  - 结构化事实（实验/特征/发布/拓扑）→ 语义层 + SQL（KQ4）。
- 知识的“生成”应制度化：RecSys Factory 的 400 条中 ~49% 来自 changelog，说明 **changelog/事故复盘/PR 描述是踩坑库最廉价的来源**；可用 Stop hook / 定期 job 从会话转录与 PR 中提议新 pitfall 与 CLAUDE.md 修改（Claude Code 官方建议），再经人审入库（ACE 的 curator 角色）。
- 避免 context collapse：不要让 LLM 周期性“重写/压缩”整个 playbook（DC 的 18,282→122 token 塌缩案例）；采用 ACE 式增量条目 + 去重 + 版本化。
- Skills 数量治理：几十个子系统各自的 skills 会触发“描述被截断”，需要 (a) 按目录放置使其只在相关路径出现，(b) 用 `skill_activated` 指标淘汰，(c) 把共享流程打包成 plugin 命名空间。

### Gaps
- Anthropic 官方没有给出 skill 元数据/正文的 token 预算，上述 100 token / 5k token 为二手经验。
- RecSys Factory 与 AgentX 的 pitfall/KB 检索方式（向量？标签？在哪个决策点注入？）与量化收益未能读取。
- 没有找到“skills vs 文档 chunk 检索”在同一任务上的直接对照实验；ACE/DC/ExpeL 的证据来自通用 agent 基准而非工程知识库。

---

## KQ8 失败模式与缓解：陈旧/重复版本、lost-in-the-middle、过度检索、检索内容注入、agent 循环成本

### Takeaway
2025–2026 的实证把“检索系统最常见的坏结果”归为六类，且都有可操作的缓解：干扰项比缺失更伤（一条高相似干扰段即可明显降准确率，60% 的查询 top-10 中有干扰）；长上下文中部信息被忽视；向量索引对高频变动代码“建成即过期”；检索内容携带指令（分层防御可把攻击成功率从 40.6% 压到 0.2% 且效用几乎不变，其中规则化清洗贡献最大）；多 agent 循环把 token 放大到 ~15× 并出现“50 个子 agent 查简单问题”“无休止找不存在的来源”；上下文文件过长导致规则被忽略、矛盾规则被任意取舍。

### Cited Findings
**过度检索与干扰项（[独立基准]）**
- The Power of Noise：干扰文档越多准确率越低，哪怕只有一条也有明显下降；检索器打分最高但不直接相关的文档对 LLM 有负面影响；加入随机（无关）文档反而最多提升 35% — [Moonlight 综述](https://themoonlight.io/review/the-power-of-noise-redefining-retrieval-for-rag-systems)；[Liner](https://liner.com/review/power-noise-redefining-retrieval-for-rag-systems)
- EMNLP 2025：>60% 的查询在 top-10 检索段落中至少含一条高度干扰段落 — [underline EMNLP 2025](https://underline.io/lecture/131174-do-rag-systems-really-suffer-from-positional-biasquestion)
- The Distracting Effect（arXiv 2505.06914）对无关段落干扰效应的量化 — [arXiv 2505.06914](https://arxiv.org/html/2505.06914v1)
- Anthropic：top-20 优于 top-10，但更多 chunk 可能分散注意力，需按用例测试 — [Anthropic](https://www.anthropic.com/news/contextual-retrieval)
- CodeRAG-Bench：无关上下文可能有害（二手确认） — [Moonlight](https://www.themoonlight.io/review/coderag-bench-can-retrieval-augment-code-generation)

**位置与长度退化**
- Chroma：开头/结尾优于中部；连贯文档更难；干扰项触发幻觉（GPT）或拒答（Claude） — [Morph](https://www.morphllm.com/context-rot)；[DAIR.AI](https://academy.dair.ai/papers/context-rot)
- Claude Code：上下文填满后“忘记早期指令、错误增多”；压缩可能丢失早期详细指令，持久规则应放 CLAUDE.md；单个超大文件/工具输出导致压缩后立即再满时会停止自动压缩并报错 — [how Claude Code works](https://code.claude.com/docs/en/how-claude-code-works)；[best practices](https://code.claude.com/docs/en/best-practices)

**陈旧/重复版本**
- 索引陈旧：评论者指出每小时变动的代码库“索引建好瞬间即过期”；Cursor 用 Merkle tree 做增量同步缓解 [二手] — [jacar.es](https://jacar.es/en/code-agents-without-vector-search/)；[Towards Data Science](https://towardsdatascience.com/how-cursor-actually-indexes-your-codebase/)
- Claude Code 官方：CLAUDE.md 不应包含“频繁变化的信息”；需定期清理过时/矛盾指令（`/doctor prompt-audit`），矛盾指令会被任意取舍；文件被读取后在磁盘变化时会收到提醒 — [Claude Code memory](https://code.claude.com/docs/en/memory)；[how Claude Code works](https://code.claude.com/docs/en/how-claude-code-works)
- AgentX 用 ingest–query–lint 生命周期保持 System KB 新鲜 — [arXiv 2606.26859](https://arxiv.org/pdf/2606.26859)
- Embedding 换代重嵌成本：Gemini Embedding 2 与 001 不兼容需全量重嵌；Voyage 4 系列共享空间可免重嵌 [二手] — [andrew.ooo](https://andrew.ooo/answers/best-embedding-models-2026-ranked/)

**检索内容注入（indirect prompt injection）**
- UCLA 2026 论文：四层防御（提示级防御、规则化清洗、工具使用限制、归因门控）在三个模型上把攻击成功率从 40.6% 降到 0.2%，良性效用 90.6%→90.2%；单层中规则化清洗最强（3.2%），归因门控几乎无效（40.9%） — [eScholarship](https://escholarship.org/uc/item/8zq0952f)
- 分层框架论文：输入过滤器看不到检索文档、输出监控阻止不了恶意载荷进入模型，因此需要检索层防御 — [papers.cool 2606.19660](https://papers.cool/arxiv/2606.19660)
- 被引述的攻击强度：5 篇精心构造文档可在 90% 情况下操纵 RAG 回答（厂商指南引用，未核实原文）；优化过的注入文档可被自然查询召回并影响 agent 行为 — [Maxim 2026 指南](https://www.getmaxim.ai/articles/prompt-injection-defense-for-production-ai-agents-a-complete-2026-guide/)；[promptfoo 漏洞库](https://promptfoo.dev/lm-security-db/vuln/optimized-indirect-prompt-injection-crosses-retrieval-barrier-2b160fcd)
- 产品侧控制：Claude Code 对项目级外部 `@import`/symlink 首次弹窗审批，不跟随网络路径；Skills 安装需审计脚本与外联指令；auto 模式分类器拦截“hostile-content-driven actions” — [Claude Code memory](https://code.claude.com/docs/en/memory)；[Anthropic Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)；[best practices](https://code.claude.com/docs/en/best-practices)

**Agent 循环的成本失控**
- 多 agent ~15× 聊天 token；失败模式包括 50 个子 agent 查简单问题、无休止搜索、冗余更新、已足够仍继续；缓解：prompt 内 effort scaling 规则、检查点恢复、决策模式监控、彩虹部署 — [Anthropic multi-agent](https://www.anthropic.com/engineering/multi-agent-research-system)
- BrowseComp-Plus 示例每题 ~12.6 次搜索；Kimi-Researcher 平均 23 步/200+ URL — [BrowseComp-Plus](https://github.com/texttron/BrowseComp-Plus)；[Kimi](https://www.kimi.com/en/help/deep-research/deep-research-overview)
- Claude Code：“infinite exploration”“kitchen sink session”“correcting over and over（两次纠错后应 /clear）”；工具结果 25k token 上限；子 agent 隔离探索 — [best practices](https://code.claude.com/docs/en/best-practices)
- LocAgent 等图引导定位需要显著更多 LLM 调用 — [arXiv 2503.09089](https://arxiv.org/pdf/2503.09089)
- 完整 GraphRAG 索引成本约为 LazyGraphRAG/向量 RAG 的 1000× — [Microsoft Research](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/)

**工具与 harness 选择错误**
- 含糊/重叠的工具集伤害 agent；工具描述重写可使任务时间 −40%；agent 曾因工具描述问题给查询乱加“2025” — [Writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)；[multi-agent](https://www.anthropic.com/engineering/multi-agent-research-system)
- turbopuffer 评测：recall 取决于 agent 是否知道该用哪个检索工具 — [AI Engineer talk](https://www.ai.engineer/talks/zKk7sDMGDEQ-benchmarking-semantic-code-retrieval-on-claude)

### Inferences
- **缓解清单（按失败类型，推断自上述证据）**：
  1. 干扰项：重排后设相关性阈值而非固定 top-k；按“相似但不同版本/不同子系统”做去重与版本折叠（同一文档保留最新 + 显式版本标签）；把检索结果以“路径 + 摘要 + 置信度”呈现，让 agent 决定是否 Read 整文。
  2. 陈旧：所有知识单元带 `source_commit`/`doc_version`/`last_verified` 元数据；检索时对代码相关文档做“文档时间 vs 引用符号最近变更时间”的新鲜度检查并在答案中标注；向量索引走增量（Merkle/变更事件）而非定期全量；CLAUDE.md/skills 走 PR 审核 + 定期 lint（AgentX lint、Claude `/doctor`）。
  3. 位置退化：把最关键的事实（约束、禁止项）放在上下文开头/结尾；长文档先给目录/摘要再按需展开。
  4. 注入：把检索内容包在数据标记里并做规则化清洗（去指令性句式/隐藏文本/可疑 URL），对写操作与外联工具做人审门控；对第三方可写的来源（wiki 评论、issue）降低权重或隔离索引。
  5. 成本：按问题类型设预算（工具调用数/子 agent 数/时间），子 agent 只返回 1–2k token 摘要，在 25k 工具输出上限内做分页；监控 token/题与“无新信息的连续步数”作为熔断。
  6. 工具选择：工具数量少而正交（lexical / semantic / sql / read），描述里写清适用场景与反例，并用评测验证模型的工具选择率。

### Gaps
- “Lost in the Middle”（Liu et al. 2023）原始数字未在本次会话中检索到（搜索额度耗尽），仅以 Chroma 的位置效应为据。
- 没有找到针对“企业 KB 中重复/陈旧版本对 RAG 准确率影响”的量化研究。
- 检索注入防御论文全文与 OWASP 2025/2026 版本未打开。
- Agentic 循环在内部 KB 场景的真实成本分布（p50/p95 调用数）无公开数据，仅有 BrowseComp-Plus 示例与 Anthropic 的 15× 粗估。
