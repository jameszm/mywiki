# AgentX 论文精读（arXiv 2606.26859，快手）

> **检索状况声明（必读）**：本次研究所在沙箱的出网代理封锁了 arxiv.org / export.arxiv.org / r.jina.ai / alphaxiv.org / huggingface.co / semanticscholar.org / papers.cool / emergentmind.com / gptget.net / paper-archivist.com / besthub.dev / themoonlight.io / pith.science / franklineh.com / catalyzex.com / chatpaper.com / zhuanlan.zhihu.com / m.sohu.com / news.qq.com（全部返回 EGRESS_BLOCKED 或 CONNECT 403）。**论文全文未能直接取回。** 唯一可用通道是 WebSearch（搜索引擎对 arXiv HTML v2、alphaxiv overview、知乎/机器之心转载的索引摘录）以及 github.com（可达）。因此下文每条事实都标注了出处；标注为 "[arXiv HTML 摘录]" 的内容是搜索引擎从 https://arxiv.org/html/2606.26859v2 索引出的原文片段（多为英文原句的转述/引用），而非我逐段阅读全文后的归纳。凡搜索摘录未覆盖的问题，一律列入 Gaps，不做臆测。
>
> 实际尝试过的 URL 及结果：
> - 被封锁：https://arxiv.org/abs/2606.26859 、https://arxiv.org/html/2606.26859v2 、https://arxiv.org/pdf/2606.26859 、https://export.arxiv.org/api/query?id_list=2606.26859 、https://r.jina.ai/https://arxiv.org/html/2606.26859v2 、https://www.alphaxiv.org/abs/2606.26859 、https://www.alphaxiv.org/zh/overview/2606.26859 、https://huggingface.co/papers/2606.26859 、https://api.semanticscholar.org/graph/v1/paper/arXiv:2606.26859 、https://papers.cool/arxiv/2606.26859 、https://www.emergentmind.com/papers/2606.26859 、https://gptget.net/papers/2606.26859 、https://pith.science/paper/2606.26859 、https://www.themoonlight.io/zh/review/agentx-... 、https://zhuanlan.zhihu.com/p/2054229279240611073 、https://zhuanlan.zhihu.com/p/2055238872141920128 、https://m.sohu.com/a/1044094449_129720 、https://news.qq.com/rain/a/20260701A03IQG00 、https://chatpaper.com/chatpaper/paper/303863 、https://www.catalyzex.com/author/Kangzhi%20Zhao 、arxiv.gg / arxiv.tips / aminer.cn / scholar.archive.org / paperswithcode.com（curl 000）。
> - 可达：https://github.com/jjakimoto/research-issues/issues/1749 （对后续论文 2609.30001 的批评）、https://github.com/HaFred/awesome-generative-recsys （前 10 万字符内未收录 AgentX）。

---

## 一、论文元信息：作者 / 团队 / 版本日期 / 发表场所 / 开源

### Takeaway
论文《AgentX: Towards Agent-Driven Self-Iteration of Industrial Recommender Systems》由快手 "AgentX Team" 署名（可确认的作者包括 Kangzhi Zhao、Changxin Lao、Fei Pan、Guozhuang Ma、Wenhao Li、Wentao Xie 等），v1 于 2026-06-25 提交、v2 于 2026-06-26 更新；未发现任何会议/期刊录用信息，也未发现官方代码、demo 或项目主页。

### Cited Findings
- 标题 "AgentX: Towards Agent-Driven Self-Iteration of Industrial Recommender Systems"，arXiv 编号 2606.26859 — [arXiv abs 列表（搜索索引）](https://arxiv.org/abs/2606.26859)
- "The paper (arXiv:2606.26859) was submitted on June 25, 2026, with a revised version on June 26, 2026." — [WebSearch 对 arXiv 页面的摘录](https://arxiv.org/abs/2606.26859)
- 知乎解读给出的作者署名为 "AgentX Team"，链接指向 v1："论文作者：AgentX Team" — [知乎《快手-AgentX：推荐系统研发自迭代（推荐算法离失业还有多久？）》](https://zhuanlan.zhihu.com/p/2054229279240611073)
- "Kangzhi Zhao is one of the authors of this work, along with Changxin Lao, Fei Pan, Guozhuang Ma, and many other researchers." — [搜索摘录自 arXiv HTML v2 / alphaxiv 作者页](https://arxiv.org/html/2606.26859v2)；alphaxiv 作者页 "Wenhao Li"、"Fei PAN" 与 catalyzex 作者页 "Wentao Xie"、"Kangzhi Zhao" 均关联到本文 — [alphaxiv @wenhao-li-5](https://www.alphaxiv.org/@wenhao-li-5)、[alphaxiv @fei-pan-2](https://www.alphaxiv.org/@fei-pan-2)、[catalyzex Wentao Xie](https://www.catalyzex.com/author/Wentao%20Xie)、[catalyzex Kangzhi Zhao](https://www.catalyzex.com/author/Kangzhi%20Zhao)
- catalyzex 将作者 Fei Pan 的机构标为 "Kuaishou Technology" — [catalyzex Fei Pan](https://www.catalyzex.com/author/Fei%20Pan)
- 同系列后续论文 RobustSGPO（2609.09646）"was conducted by Kuaishou Technology in Beijing, China, building upon the AgentX framework" — [RobustSGPO arXiv](https://arxiv.org/html/2609.09646)
- 后续论文 "Advancing Model Research in AgentX: Long-Horizon Autonomy for Industrial Recommender Systems"（arXiv 2609.30001，2026-09-24 提交）作者：Shuang Yang, Zijie Zhuang, Changxin Lao, Pengbo Xu, Hanwen Xu, Yusheng Huang, Han Gao, Guanchen Wang, Tianbao Ma, Linxun Chen, Peilin Song, Xuming Wang, Chen Li, Fan Wu, Tao Wang, Zibo Zhao, Xiangyu Wu, An Liu, Fei Pan, Peng Jiang, Chen Yang, Zhaojie Liu, Wenwu Ou — [arXiv 2609.30001](https://arxiv.org/abs/2609.30001)
- 中文媒体首发：机器之心 2026-07-01 报道《快手AgentX：推荐系统开始自我迭代》（腾讯新闻、搜狐转载），称 "快手 AgentX 团队发布了技术报告" — [腾讯新闻转载](https://news.qq.com/rain/a/20260701A03IQG00)、[搜狐转载](https://m.sohu.com/a/1044094449_129720)
- 智东西（Chinazhidx）英文推文："#Kuaishou AgentX releases a report on agent-driven R&D loops for recommender systems … 3 AgentX workers turned 374 ideas into 10 deployable results—8× throughput, 3.7× productivity, +¥100M annualized revenue" — [X 推文](https://x.com/Chinazhidx/status/2072995747864465756)
- 开源情况：一条搜索综合结论称 "the search results don't provide specific GitHub repository details for the official Kuaishou AgentX recommender system code"；搜索到的 GitHub 上名为 AgentX 的仓库（OpenAgentX/AgentX、WindriderQc/AgentX、lucky-aeon/AgentX、Webioinfo01/agentx-hub）与本文**无关** — [OpenAgentX/AgentX](https://github.com/OpenAgentX/AgentX)、[WindriderQc/AgentX](https://github.com/WindriderQc/AgentX)

### Inferences
- 署名 "AgentX Team" + 后续论文的通讯作者阵容（Peng Jiang、Zhaojie Liu、Wenwu Ou 等为快手推荐/商业化方向的资深负责人）暗示这是快手推荐算法团队与商业化（生活服务）团队联合的工程项目，而非单一研究组产出。
- 从 2609.30001 把 "AgentX-Model" 作为独立框架、RobustSGPO 把 "AgentX brainstorming workflow" 作为评测床来看，AgentX 在快手内部是一个持续演进的平台品牌，2606.26859 只是第一篇"策略侧/特征工程侧"报告。

### Gaps
- 完整作者名单及各自所属的快手具体团队（主站推荐 / 商业化 / 基础模型）未能确认——arXiv 页面与 alphaxiv 均被封锁。
- 未发现任何会议投稿或录用信息（RecSys 2026 / KDD 2026 / NeurIPS 2026 均无搜索结果）。
- 未发现官方代码仓库、demo 或项目主页；也未发现论文中关于"是否开源"的声明。
- v1 与 v2 之间的修改内容未知。

---

## 二、整体架构：四阶段闭环、Data Layer、Monitoring Platform、使用的 LLM

### Takeaway
AgentX 是一个多 Agent（而非单循环 Agent）系统，把一次推荐迭代拆成 Brainstorm Agent → Developing Agent → Evaluation Agent 三个执行阶段加一个离线的 Harness Evolution（SGPO）元层；三类 Agent 共享一个 Data Layer（Knowledge Base + Agent Data Management）并被一个 Monitoring Platform 观测。论文公开部分**未披露**底座 LLM 的具体型号。

### Cited Findings
- 摘要原句："AgentX … orchestrates four tightly coupled stages in a closed loop: a Brainstorm Agent synthesizes evidence from historical experiments, system architecture, data analysis, and external research into ranked, executable proposals; a Developing Agent translates each proposal into production-ready code through repository-grounded generation and multi-dimensional reliability verification; an Evaluation Agent conducts safe online rollout with guardrail-vetted A/B judgment, converting both successes and failures into structured knowledge assets; and a Harness Evolution layer (SGPO) distills execution trajectories into semantic-gradient updates that continuously sharpen the agents themselves -- making the system not merely automated, but self-improving." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 系统定位："AgentX is designed to turn vague business intent into evidence-grounded proposals, translate each proposal into repository-consistent code, validate changes through safe online rollout with guardrail veto, and feed both positive and negative trajectories back into the system so that the loop itself improves over time." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 数据层与监控平台："A shared Data Layer encompasses a Knowledge Base of current experience in practice together with Agent Data Management records of experiment reports, while the Monitoring Platform continuously observes system health through dashboards, metrics, tracing, alerts, audit, and visualization." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 另一处表述："The agents are supported by a Shared Data Layer—containing knowledge bases for experiments and system code—and a Monitoring Platform that observes system health." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 问题背景（引言）："Recommendation algorithm iteration is moving from an artisanal, engineer-bound process toward an industrialized research loop, but the idea-to-launch cycle still depends on human engineers to generate hypotheses, modify production code, launch A/B experiments, and attribute online results." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 中文概括（知乎）："AgentX 将一次完整的推荐实验拆解为 Brainstorm Agent、Developing Agent、Evaluation Agent 和 Harness Evolution。前三个阶段负责把一个想法推到真实线上结果，第四个阶段负责让 Agent 系统从历史轨迹中变得更强。" — [知乎《AgentX：快手让推荐系统自己迭代自己…》](https://zhuanlan.zhihu.com/p/2055238872141920128)
- 机器之心概括："让 Agent 不只是辅助写代码，而是成为推荐迭代的执行主体，持续生成方案、实现代码、上线实验、读取反馈，并把每一次轨迹沉淀为下一轮进化的燃料 … 成功实验成为后续方案的 playbook，失败实验沉淀为反例、约束和剪枝规则。" — [腾讯新闻转载机器之心](https://news.qq.com/rain/a/20260701A03IQG00)
- 第三方（腾讯 RecSys Factory 论文）对 AgentX 的刻画："AgentX (Kuaishou Team, 2026) is a 4-stage closed-loop production agent for Kuaishou App feature engineering, with a Monitoring Platform for engineers and a runtime playbook accumulated online." — [RecSys Factory arXiv 2608.11241](https://arxiv.org/html/2608.11241v1)
- 关于底座模型：Harness Evolution 描述中仅说 "During evolution runs, the foundation model, tool interface, top-level orchestration, and other subagents remain fixed, with only the target subagent's instructions, validation rules, output contract, and tool-use discipline being edited."；一条专门搜索的综合结论是 "The specific LLM model backbone used in AgentX … is not explicitly disclosed in the publicly available paper abstracts and summaries" — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 模型侧延伸："Beyond online strategy iteration, the same closed-loop principle extends to model-side research, enabling autonomous paper reproduction, module ablation, and cross-paper architectural composition." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)

### Inferences
- "feature engineering"（RecSys Factory 的刻画）+ Developing Agent 失败模式全是特征 schema / ranking DSL / factory 注册（见第四节）→ 2606.26859 中的线上实验主体很可能是**排序侧特征与策略（DSL 层）改动**，而非训练新模型结构；模型结构侧的工作被拆到了 2609.30001（AgentX-Model）。
- 架构是"编排的多子 Agent + 元优化层"，每个子 Agent 有独立的 instructions / validation rules / output contract / tool-use discipline，这正是 SGPO 能"只改一个子 Agent 规范"的前提（见第六节）。
- 底座 LLM 未披露；考虑快手同期发布 KAT-Coder / KAT-Coder-V2.5（2607.05471）等自研代码模型，**不能排除**使用自研模型，但这只是推测，论文公开片段没有任何证据。

### Gaps
- 底座 LLM（Claude / GPT / Qwen / DeepSeek / 自研 KAT）完全未知。
- Agent 调用的具体工具清单（代码仓库 API、特征平台、训练平台、实验平台 API 等）未在可见片段中出现；只知道存在 "tool interface" 与 "tool-use discipline"。
- 三个 Agent 之间的编排器（orchestrator）实现、状态机、任务队列等细节未知。
- "worker" 的精确定义（一个 worker = 一套三 Agent 流水线实例？）未明确。

---

## 三、Proposal 阶段（Brainstorm Agent）：想法来源、生成、筛选

### Takeaway
Brainstorm Agent 把"欠规范的用户意图"转成"少量、排序过、可执行"的实验提案，机制是 bounded exploration（分批探索、按成熟度分类）+ evidence-weighted generation（证据来自 Experiment Knowledge Base、System Knowledge Base、数据分析、外部论文）。374 个 idea 的具体去重/排序算法未见披露。

### Cited Findings
- "The Brainstorm Agent converts an under-specified user intent into a small, ranked set of executable experiment proposals via bounded exploration and evidence-weighted generation." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- Bounded exploration 的理由："The agent explores proposals in batches rather than through a single free-form response, since production ideas differ by mechanism and maturity—some are ready to implement, some require data or source probes, and some are strategically interesting but depend on future platform or model capability." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 证据来源："an evidence-weighted generation process drawing from an Experiment Knowledge Base of historical launch reviews, System Knowledge Base with structured information on current model architecture and features, along with data analysis and external research." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 中文转述："Brainstorm Agent 整合历史实验、系统架构、数据分析和外部论文，将目标收敛为少量有优先级、有证据、边界清晰的候选方案" — [知乎](https://zhuanlan.zhihu.com/p/2054229279240611073)
- 后续论文 RobustSGPO 把 "AgentX brainstorming workflow" 作为评测床："evaluates these techniques in the AgentX brainstorming workflow using 120 tasks, 95 runs, and 7,350 candidate attempts" — [RobustSGPO 2609.09646](https://arxiv.org/pdf/2609.09646)
- Monitoring Platform 把 "idea pass" 作为闭环第一个状态节点记录（见第七节），且三周内 "the idea pass rate tripled (from 15% to 45%)" — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)

### Inferences
- 存在一个显式的 "idea pass" 门禁（通过率 15%→45%），说明 374 个 idea 中大部分在进入 Developing 前就被筛掉；这个门禁可能是 Brainstorm Agent 内部的证据加权排序 + 人工/规则审核，但谁来判定（人还是 Agent）未见说明。
- 把 idea 按成熟度分成"可直接实现 / 需数据或源码探查 / 依赖未来平台能力"三类，相当于一个粗粒度的可行性路由，可减少 Developing Agent 在不可实现想法上的浪费。

### Gaps
- 374 个 idea 的生成节奏（是一次性 brainstorm 还是每周滚动）、去重方法、排序评分公式均未见。
- "用户意图"（user intent）由谁给出——业务方工程师输入一句目标？还是系统自动从指标看板触发？未知。
- 外部论文检索的来源与方式（arXiv 爬取？内部论文库？）未知。

---

## 四、Implementation 阶段（Developing Agent）：改哪部分代码、如何验证、训练如何等待

### Takeaway
Developing Agent 以"repository-grounded generation + 面向验证的实现循环"把提案变成生产可审查代码，验证维度包括语法、与仓库约定的语义一致性、单元测试覆盖、性能回归、安全护栏；论文明确列出了推荐代码库特有的静默失败（特征名幻觉、DSL 误用、漏注册工厂、未加开关的默认开启），并提到 "dryrun-template" 随时间成熟。训练时长与等待机制未见披露。

### Cited Findings
- "The Developing Agent translates each selected proposal into production-ready code through repository-grounded generation and a verification-oriented implementation loop." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- "The Developing Agent manages the transformation of approved proposals into executable production code and handles offline training tasks. The Developing Agent owns code realization and repository-level verification." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 验证维度："The verification dimensions include syntax, semantic alignment with repository conventions, unit-test coverage, performance regression checks, and safety guardrails." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 工业代码库的静默失败风险（原文）："Both recommendation tracks face the fundamental risk that promising ideas degrade into silent failures at the implementation stage. Online, the target repository is large, internal conventions are partially undocumented, and many errors evade compile-time checks: incorrect feature names compile but read meaningless data, missing factory registrations disable strategies without notification, and unguarded default-on changes can impact live traffic prior to review." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 两类典型幻觉："Attribute hallucination arises when the agent invents fields in the user feature schema, the context feature schema, or the item feature schema. DSL misuse arises when it guesses ranking DSL operator names or argument contracts." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 中文转述："Developing Agent 将提案转为生产可审查代码或离线模型实验" — [知乎](https://zhuanlan.zhihu.com/p/2054229279240611073)
- 自进化三要素之一是 "dryrun-template maturation"（与 skill consolidation、pitfalls accumulation 并列） — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)

### Inferences
- 失败模式全部围绕 user/context/item 特征 schema 与 "ranking DSL"，说明本文线上实验的代码落点主要是**排序层的特征配置与策略 DSL**（可能还包括召回/重排策略的 factory 注册），而非训练框架或 serving 内核。
- "dryrun" 模板的存在说明实现循环中有一个在真实流量前的"空跑/影子运行"环节，用于捕获上述编译期无法发现的错误；模板随经验积累被 Harness Evolution 固化。
- "handles offline training tasks" 表明 Developing Agent 能触发离线训练/评估，但等待与轮询机制未知。

### Gaps
- 单次训练/离线评估的耗时、Agent 如何等待（轮询、回调、挂起恢复）未知。
- 代码审查（code review）是人审还是 Agent 审、合入分支策略、是否需要人工 approve 才能部署，均未见。
- 单元测试是 Agent 自己写的还是既有的；性能回归如何测量；"safety guardrails" 在代码层指什么，未见。
- 每个 idea 的 token / GPU 成本未见任何数字。

---

## 五、Guarded Online A/B（Evaluation Agent）：护栏、判定、launchable rollout 定义

### Takeaway
Evaluation Agent 负责流量分配、上线、A/B 判定与"负结果资产化"；护栏不是单指标一票否决，而是把多个业务目标加权成一个聚合的 LT（lifetime-value）exchange score；只有主指标同时过"最小效应阈值 + 统计显著"且护栏确认无不可接受的跨域损害才能 KEEP；输出是 KEEP / EXTEND / DISCARD 结构化判决。"launchable rollout/result" = Monitoring Platform 记录的 "positive evaluation"，即达到可全量（full rollout）条件的实验。

### Cited Findings
- "The Evaluation Agent manages rollout and traffic assignment, judges A/B results with guardrail veto, and assetizes online outcomes into reusable reward signals and failure memory." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- "The Evaluation Agent closes the production loop of AgentX: it determines whether a code change materialized by the Developing Agent should be kept, rolled back, or fed back as a negative lesson for the next round of iteration." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 其任务本质："convert noisy, delayed, and partially observable online traffic into a trustworthy reward signal that the rest of the system can act upon." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 护栏设计："Guardrails use composite economic-exchange metrics rather than single-indicator vetoes. Instead of blocking on any individual metric crossing a hard line, the system computes an aggregated lifetime-value (LT) exchange score that weights several business objectives into a unified summary." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- KEEP 条件："A candidate is eligible for KEEP only when the primary objective clears both a minimum effect threshold and statistical significance, and when guardrail assessments confirm no unacceptable cross-domain damage." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 另一表述："A decision to 'KEEP' a change is only made if the primary objective reaches significance and no 'guardrail' metrics (e.g., system stability or long-term user experience) are negatively impacted." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 判决输出格式："The output of the analysis stage is a structured verdict: KEEP, EXTEND, or DISCARD, together with the primary effect, guardrail status, statistical method, observation window, and caveats." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 负结果处理："Online A/B results decide which changes survive, but negative results decide which future branches should be pruned or probed more carefully. … the agent must convert negative results into reusable memory." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 中文转述："Evaluation Agent 负责安全上线、流量分配、A/B 判定和负结果资产化 … 使用基于业务指标综合经济置换分数的 Guardrail Veto 机制做决策" — [知乎](https://zhuanlan.zhihu.com/p/2054229279240611073)
- launchable result 的定义："a positive evaluation denotes an experiment that qualifies for full rollout, i.e., a launchable result." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 人工干预在质量评分中的地位："Manual intervention is treated as a hard binary gate in quality scoring." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)

### Inferences
- "EXTEND" 判决意味着存在"延长观察窗口/扩大流量"的中间态，这是对噪声大、延迟高的线上指标的常见处理，也暗示流量是分阶段放大的，但具体阶梯（如 1%→5%→全量）未见。
- "LT exchange score"（置换分数）即快手内部用"以 X 换 Y 是否划算"的经济换算（如用部分商业化收入换时长），说明护栏是业务方预先设定权重的加权分，而非 Agent 自行决定。
- "launchable"（可全量）与"已全量"不是同一回事：10 个是"达到全量条件"的实验，最终是否由人拍板全量、以及实际全量了几个，论文可见片段未说。

### Gaps
- 具体护栏指标清单、流量上限、实验最短/最长时长、自动回滚触发条件、人工审批节点均未见。
- 谁有最终 launch 决定权（Agent 自动 or 人）未知；"Manual intervention … hard binary gate" 暗示人工干预会被记录并影响质量评分，但干预率未见数字。
- 统计方法（t-test / CUPED / 序贯检验等）未见。

---

## 六、Harness Evolution（SGPO）：存什么、如何更新、如何防回归

### Takeaway
SGPO（Semantic-Gradient-based Prompt Optimization）是**离线**的 harness 进化方法：Harness Evaluate Agent 从采样轨迹中诊断失败，产出结构化"语义梯度"（缺失需求、步骤顺序错误、工具使用违规、输出契约破坏）；Harness Refine Agent 据此生成候选 harness；Harness Exp Agent 用 **paired replay**（新旧 harness 在相同任务上并行重放）验证，只有正向证据才接纳进生产。每次只改一个子 Agent 的规范，底座模型、工具接口、编排与其他子 Agent 保持固定。

### Cited Findings
- 定义："SGPO is an offline harness-evolution method that turns accumulated execution traces into local subagent prompt updates and admits them solely through paired replay. SGPO treats natural-language diagnoses of trace failures as semantic gradients that revise a single subagent specification while the rest of AgentX remains fixed." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 三步流程：(1) "Loss Calculation … The Harness Evaluate Agent analyzes failures within sampled traces against the current Target Harness, yielding a structured Semantic Gradient which explicitly maps execution flaws such as missing requirements, incorrect step orders, tool-use violations, or broken output contracts." (2) "Harness Refinement: The Harness Refine Agent leverages this gradient to propose an updated Candidate Harness." (3) "Paired Replay: The Harness Exp Agent conducts a Paired Replay evaluation by executing both the current harness and the candidate harness over identical user tasks. If the replay yields positive evidence, the candidate harness is formally Accepted into production." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 固定范围："During evolution runs, the foundation model, tool interface, top-level orchestration, and other subagents remain fixed, with only the target subagent's instructions, validation rules, output contract, and tool-use discipline being edited." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 优化对象（第三方综述）："a second optimization layer over execution trajectories targeting not the recommendation strategy itself, but the harness controlling how each subagent reasons, asks questions, validates evidence, hands off work, and recovers from failure." — [搜索摘录（emergentmind 页面索引）](https://www.emergentmind.com/papers/2606.26859)
- 中文转述："Harness Evolution 使用 SGPO 从执行轨迹中提取语义梯度，更新单个子 agent 的指令、验证规则、输出契约和工具使用纪律" — [知乎](https://zhuanlan.zhihu.com/p/2054229279240611073)
- 自进化的三个载体："per-worker concurrent throughput roughly doubled each week as the system self-evolved through skill consolidation, pitfalls accumulation, and dryrun-template maturation." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 第三方刻画："AgentX's SGPO harness provides closed-loop online playbook accumulation"；"A team pushing candidate-scoring quality under a shared 24/7 monitoring surface benefits most from AgentX's SGPO harness." — [RecSys Factory 2608.11241](https://arxiv.org/html/2608.11241v1)
- 后续工作 RobustSGPO（快手，2609.09646）在 SGPO 基础上加入 "search-space control"："specifying the requested edit, constructing and checking the patch, and continuing search from either the incumbent or retained snapshots"，在 AgentX brainstorming workflow 上用 120 tasks / 95 runs / 7,350 candidate attempts 评测 — [RobustSGPO](https://arxiv.org/pdf/2609.09646)

### Inferences
- "runtime playbook" 的实体 = skills（技能/模板的固化）+ pitfalls（踩坑清单）+ dryrun templates（空跑模板），再加上各子 Agent 被 SGPO 改写的 prompt 规范；这与腾讯 RecSys Factory 的 "PitfallStore" 思路同源。
- 防回归机制 = 局部更新（一次只改一个子 Agent）+ paired replay 门禁（只接受正向证据）；RobustSGPO 的出现（强调 search-space control、从 incumbent 或 retained snapshot 继续搜索）暗示原版 SGPO 在搜索空间失控/回退方面存在不足，这是作者团队自己承认的改进方向。
- 关于 reward hacking：可见片段中没有专门讨论；paired replay 的评价指标如果是 Agent 自评，理论上存在被利用的空间，但论文是否讨论了这一点无法确认。

### Gaps
- paired replay 的评分标准（是否人审、用什么指标判"positive evidence"）未见。
- SGPO 的运行频率（每日/每周）、每轮采样多少条轨迹、接纳率未见。
- 轨迹存储格式、Knowledge Base 的检索方式（RAG？结构化表？）未见。
- 是否有显式的 reward hacking / Goodhart 防护讨论未知。

---

## 七、Monitoring Platform 与人的角色

### Takeaway
Monitoring Platform 提供 dashboards、metrics、tracing、alerts、audit、visualization，并把闭环的每个节点（idea pass、code-and-launch、positive evaluation）记为显式状态转移；人工干预被当作质量评分里的"硬二值门"。工程师的具体职责与干预率未见数字。

### Cited Findings
- "the Monitoring Platform continuously observes system health through dashboards, metrics, tracing, alerts, audit, and visualization." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- "The monitoring platform logs every node of the loop—idea pass, code-and-launch, and positive evaluation—as an explicit state transition, where a positive evaluation denotes an experiment that qualifies for full rollout, i.e., a launchable result." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- "Manual intervention is treated as a hard binary gate in quality scoring." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 第三方刻画："a Monitoring Platform for engineers and a runtime playbook accumulated online" — [RecSys Factory](https://arxiv.org/html/2608.11241v1)

### Inferences
- "audit" 功能 + "manual intervention 作为二值门"说明系统会记录每条轨迹是否被人碰过，被人碰过的轨迹在统计"Agent 自主产出"时可能被单独计或扣分——这对 TikTok 复现时定义"自主率"指标有参考价值。
- 三个状态节点（idea pass → code-and-launch → positive evaluation）正是论文漏斗数字（374 → ? → 10）的度量基础。

### Gaps
- 人工干预率、人工审批节点位置、工程师在 Monitoring Platform 上的典型操作均未见。
- 中间节点 "code-and-launch" 的数量（即 374 个 idea 中有多少进入线上实验）未见。

---

## 八、实验设置与全部报告数字

### Takeaway
部署设定：3 个 AgentX worker、3 周、快手 App 两个场景（主站推荐 main feed、生活服务商业化 life-service commercialization）并发跑 idea-to-rollout 闭环；374 idea → 10 launchable results；每 worker-week 并发 12 个实验 vs 工程师 1.5（8×）；每 worker-week 1.1 个 launchable result vs 工程师 0.08（13.8×）；单位人力业务价值 3.7×；idea 通过率 15%→45%；周 launchable 数翻倍以上；主站 App 时长累计 +0.561%；生活服务年化收入 >1 亿元。

### Cited Findings
- 摘要总句："In a three-week Kuaishou App deployment across main-feed and life-service recommendation, three AgentX workers turned 374 ideas into 10 launchable rollouts—per-worker throughput doubled weekly via self-evolution, delivering 8× concurrency and 3.7× business value over a manual engineer, a 0.561% user app-time gain, and over RMB 100M annualized revenue." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 场景设定："three AgentX workers ran idea-to-rollout loops concurrently across two production scenarios on the Kuaishou App: main feed recommendation and life-service commercialization." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 并发与产出（worker-week 粒度）："AgentX achieved 1.1 LR (launchable results) Count per worker-week compared to 0.08 for an engineer—a 13.8× increase, and 12 concurrent experiments per worker-week compared to 1.5 for an engineer—an 8× increase." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 自进化曲线："Over the three-week period, the idea pass rate tripled (from 15% to 45%) and the weekly launchable results more than doubled" — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 业务指标拆分（中文）："在快手 App 三周线上部署中用 3 个 worker 将 374 个想法转成 10 个可全量发布结果，带来 0.561% 用户 App 时长增益和超 1 亿元年化收入 … 与单个算法工程师对比，AgentX 的单位人力业务价值提升 3.7 倍" — [知乎](https://zhuanlan.zhihu.com/p/2054229279240611073)
- 场景归属（中文）："achieving a 0.561% increase in main feed app duration and over 100 million yuan in annual revenue for life services"（搜索引擎对知乎文的英文摘录） — [知乎](https://zhuanlan.zhihu.com/p/2055238872141920128)
- "a cumulative gain of 0.561% in user app consumption time on Kuaishou App and over RMB 100 million in annualized revenue for the Kuaishou platform." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 机器之心："3 个 AgentX worker 在主站推荐与生活服务商业化场景中，将 374 个实验想法推进为 10 个可发布结果 … 相较传统人工迭代，单 worker 并发实验数提升 8 倍，单位人力业务价值提升 3.7 倍。" — [腾讯新闻转载](https://news.qq.com/rain/a/20260701A03IQG00)
- 知乎列表式转述："三周 374 个 idea → 10 个可全量上线结果；每 worker 并发实验 12 个（工程师 1.5 个，8×）；用户 App 时长 +0.561%，年化收入超 1 亿元。" — [知乎](https://zhuanlan.zhihu.com/p/2055238872141920128)

### Inferences
- 0.561% 是**累计**（cumulative）口径，即 10 个（或其中主站的那部分）launchable 实验收益的加总，而非单个实验；"+0.561% 主站时长" 与 "生活服务 >1 亿元年化" 分属两个场景，这一拆分来自知乎解读与论文片段的一致表述，但论文原文是否逐一列出每个实验的贡献未知。
- 工程师基线（1.5 并发、0.08 LR/周）应为快手内部历史统计或估算；3.7× "业务价值"与 13.8× "LR 数量"的差距暗示 Agent 产出的单个 launchable 实验平均价值约为工程师产出的 27%（3.7/13.8），即 Agent 更擅长高吞吐的小收益实验——这是我的推算，论文是否如此解释未知。
- "3 workers × 3 weeks = 9 worker-weeks"，10 LR / 9 ≈ 1.1 LR/worker-week，与报告一致，验证了口径。

### Gaps
- 374 → code-and-launch → 10 的中间漏斗数字未见。
- 工程师基线的来源（多少位工程师、哪个时间窗、哪个场景）未见。
- "3.7× 业务价值"的分母定义（人均？worker 与工程师的成本是否折算）未见。
- 任何成本数字（token、GPU 小时、每 idea 成本）均未见。
- 10 个 launchable 中有多少属于主站、多少属于生活服务；有多少最终真正全量，未见。

---

## 九、失败分析、成功案例、消融

### Takeaway
可见片段中的"失败分析"主要是定性的实现层失败模式（特征名幻觉、DSL 误用、漏注册、默认开启），**未见**失败原因的数量分布，也**未见**10 个成功 rollout 的具体内容；"消融"方面只看到 idea 通过率 15%→45% 与周 LR 翻倍这类随时间的自进化证据，未见移除 SGPO / Knowledge Base 的对照实验。

### Cited Findings
- 实现层失败模式（见第四节引文）："incorrect feature names compile but read meaningless data, missing factory registrations disable strategies without notification, and unguarded default-on changes can impact live traffic prior to review"；"Attribute hallucination … DSL misuse …" — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 自进化证据："idea pass rate tripled (from 15% to 45%) and the weekly launchable results more than doubled, suggesting that the system was successfully learning from its trajectories." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 模型侧探索的方法论："The model research exploration follows a systematic loop of reproduction, module ablation, and cross-paper composition, whose execution and self-evolution are described in the paper." — [arXiv HTML 摘录](https://arxiv.org/html/2606.26859v2)
- 后续论文 2609.30001 的模型侧结果（**非本文**，供对照）："the five latest online A/B evaluations across different business settings reported gains including 10–15% in acquisition efficiency, 15–20% in target-segment advertising spend, and 0.3–0.8% in watch time"；采用 "Research Agent + Model Agent" 双 Agent 架构 — [arXiv 2609.30001](https://arxiv.org/abs/2609.30001)
- 对 2609.30001 的第三方批评（**非本文**）：声称 "560 of 636 completed experiments above their business AUC baseline" 的阈值是 ΔAUC > 1e-6（"three orders of magnitude below noise"），作者自己也说明 "are not experiment success rates: many Follow-up and Composition experiments inherit implementations"；473 节点重放消融中 "Uniform Random matched or beat every LLM scheduling policy in two of four settings" — [GitHub research-issues #1749](https://github.com/jjakimoto/research-issues/issues/1749)

### Inferences
- 本文（2606.26859）的"消融"更接近"纵向自进化曲线"，不是严格的组件消融；对 TikTok 复现者而言，这意味着 SGPO 的独立贡献无法从本文数据中分离出来。
- 对后续论文的批评（阈值过松、LLM 调度不优于随机）虽不直接针对本文，但提示在评估本文 "idea pass rate 15%→45%" 等自评指标时，应追问门禁标准是否也在同步放松。

### Gaps
- 失败原因的数量分布（编译失败 / 训练失败 / 离线无收益 / 线上护栏否决）未见。
- 10 个 launchable rollout 的具体改动内容（特征？策略？模型？）未见任何案例描述。
- 是否有 "w/o SGPO"、"w/o Knowledge Base" 等对照未见。

---

## 十、局限性、未来工作、安全/伦理讨论

### Takeaway
可见片段中**没有**抓取到论文 Limitations / Future Work / Ethics 章节的任何原文；只能从同团队后续论文（RobustSGPO 补搜索空间控制、AgentX-Model 补模型侧长程自主）反推作者认为的不足。

### Cited Findings
- 后续工作 RobustSGPO："introduces search-space control for agent harness evolution … continuing search from either the incumbent or retained snapshots"，在 AgentX brainstorming workflow 上评测 — [RobustSGPO 2609.09646](https://arxiv.org/pdf/2609.09646)
- 后续工作 AgentX-Model："a model research framework that connects proposal development and model experimentation within sandboxes defined by business inputs and prediction tasks … dual-agent architecture comprising a Research Agent and a Model Agent" — [arXiv 2609.30001](https://arxiv.org/abs/2609.30001)
- 同行对比视角（腾讯）："The design principle is autonomy at decision points, not over pipelines"；RecSys Factory 用 "29-file skill ecosystem (8,971 lines of SKILL.md) whose per-skill pitfall tables mechanically compile into a 400-entry PitfallStore, confining autonomy to bounded typed decision surfaces inside pre-committed pipelines"，并以 Table 2.1 在五个设计轴上与 AgentX、NOVA 对比 — [RecSys Factory 2608.11241](https://arxiv.org/html/2608.11241v1)
- 知乎解读标题本身即提出的社会性问题："推荐算法离失业还有多久？" — [知乎](https://zhuanlan.zhihu.com/p/2054229279240611073)

### Inferences
- 从后续两篇论文的切入点推断，作者自认的局限至少包括：(a) SGPO 的 prompt 搜索空间缺乏控制、易漂移（→RobustSGPO）；(b) 本文只覆盖线上策略/特征迭代，模型结构研究需要更长时程的自主性（→AgentX-Model）。
- 腾讯 RecSys Factory 把自己定位为"决策点有界自主"，隐含地把 AgentX 归为"全流水线自主"一侧，这是复现时需要权衡的核心设计轴：AgentX 式端到端闭环 vs. 把 Agent 自主权限定在少数决策点。

### Gaps
- 论文明文的 Limitations、Future Work、Ethics/Safety 章节内容完全未知。
- 是否讨论了 Agent 自主改线上代码的安全边界、权限模型、事故案例，未知。

---

## 十一、来源清单与可靠性分级

- **一级（论文原文片段，经搜索引擎索引）**：https://arxiv.org/html/2606.26859v2 、https://arxiv.org/abs/2606.26859 、https://arxiv.org/pdf/2606.26859 ——所有标注 "[arXiv HTML 摘录]" 的引文均来自搜索引擎对这些页面的摘录，未经本人直接通读全文核对。
- **一级（同团队/同行论文，经搜索索引）**：https://arxiv.org/abs/2609.30001 （AgentX-Model）、https://arxiv.org/pdf/2609.09646 （RobustSGPO）、https://arxiv.org/html/2608.11241v1 （腾讯 RecSys Factory）、https://arxiv.org/html/2607.29241v1 （RecHarness，仅引用 AgentX）。
- **二级（中文媒体/解读）**：机器之心 2026-07-01（转载：https://news.qq.com/rain/a/20260701A03IQG00 、https://m.sohu.com/a/1044094449_129720 ）；知乎 https://zhuanlan.zhihu.com/p/2054229279240611073 、https://zhuanlan.zhihu.com/p/2055238872141920128 ；智东西推文 https://x.com/Chinazhidx/status/2072995747864465756 。
- **二级（英文聚合/解读页，仅标题与片段可见）**：https://www.alphaxiv.org/overview/2606.26859 、https://www.emergentmind.com/papers/2606.26859 、https://www.besthub.dev/articles/how-kuaishou-s-agentx-enables-self-iterating-industrial-recommender-systems-70bd1a0f6215 、https://www.paper-archivist.com/reading/2026/agentx-towards-agent-driven-self-iteration-of-industrial-rec/ 、https://www.themoonlight.io/zh/review/agentx-towards-agent-driven-self-iteration-of-industrial-recommender-systems 、https://pith.science/paper/2606.26859 。
- **三级（第三方批评，针对后续论文）**：https://github.com/jjakimoto/research-issues/issues/1749 。
- 未找到：官方 GitHub、项目主页、会议录用信息、底座 LLM 型号、成本数据。
