# Coding Agent 格局与大厂内部实践（截至 2026 年 10 月）

> 研究说明：本笔记面向 TikTok 推荐架构负责人规划内部研发提效 Agent。所有数字均标注日期；【厂商口径】= 厂商/公司自述或公关数据，【独立测量】= 第三方学术/遥测研究，【媒体转述】= 二手媒体/聚合站转述且未能核实原始出处。本次研究中多个一手域名（metr.org、arxiv.org、infoq.com、engineering.atspotify.com、newsletter.pragmaticengineer.com、blog.google、github.blog、dora.dev、tech.meituan.com、36kr 等）被网络代理拦截，部分数据只能通过搜索摘要与二手来源获得，相应条目已标注。

---

## 一、商业与开源 Coding Agent 格局：形态、自主性、定价、规模

### Takeaway
2025–2026 年市场从"IDE 补全"转向"终端 Agent + 云端异步 Agent"双形态；Claude Code（终端）、OpenAI Codex（CLI+云）、Cursor（IDE+后台 Agent）、GitHub Copilot coding agent（云端异步 PR）构成第一梯队，收入/用户规模在一年内普遍增长 3–10 倍；中国侧 ByteDance Trae、Alibaba Qoder、Tencent CodeBuddy 均已进入"内部 90%+ 工程师覆盖"阶段并对外商业化。开源侧 OpenHands / Cline / OpenCode 活跃，Aider 与 Roo Code 在 2026 年中陷入停滞或关闭。

### Cited Findings

**Claude Code（Anthropic，终端 Agent，可接 IDE / Slack / CI；按订阅或 API token 计费）**
- 2025-11（GA 后约 6 个月）年化收入 run-rate 达 $1B；2026-02 超过 $2.5B；2026 年初以来周活翻倍、企业订阅翻 4 倍，企业使用占 Claude Code 收入一半以上【厂商口径，经聚合站转述】 — [joinnextdev](https://www.joinnextdev.com/blog/claude-code-hits-25b-arr-redesign-your-eng-org-now)；[codeconductor](https://codeconductor.ai/blog/claude-code-anthropic-profitability/)；[aicodedetector](https://aicodedetector.com/claude-code-statistics/)
- Anthropic 整体 run-rate：2025 年初约 $1B → 2026-02 约 $14B → 2026 年中宣称 $30B（"80x 增长"）【厂商口径】 — [VentureBeat](https://venturebeat.com/technology/anthropic-says-it-hit-a-30-billion-revenue-run-rate-after-crazy-80x-growth)；[technologychecker（2026-07 更新）](https://technologychecker.io/blog/claude-statistics-insights)
- 定价（2026）：Pro $20/月（年付 $17）、Max 5x $100/月、Max 20x $200/月；API 按 token（Sonnet 5 约 $3/M 输入、$15/M 输出） — [amux.io 定价对比](https://amux.io/blog/ai-coding-tools-pricing-2026/)
- Pragmatic Engineer 2026-01-27~02-17 调查（906 名工程师/管理者，中位经验 11–15 年）：Claude Code 为**使用率第一**的 AI 工具；95% 受访者每周使用 AI；75% 用 AI 完成至少一半工程工作；Staff+ 工程师是最重的 Agent 用户（63.5% 常规使用 Agent vs 普通工程师 49.7%）【独立调查，自选样本】 — [Pragmatic Engineer: AI Tooling 2026](https://newsletter.pragmaticengineer.com/p/ai-tooling-2026)；[转述](https://aiproductivity.ai/news/pragmatic-engineer-survey-ai-tooling-2026/)

**OpenAI Codex（CLI + 云端异步 Agent + IDE 扩展；随 ChatGPT 订阅）**
- 周活：2026-03 >200 万 → 2026-04-21 >400 万 → 2026-06 >500 万（其中 20% 为非开发者知识工作者）→ 2026-07-13 700 万、GPT-5.6 发布后数日内 800 万【厂商口径】 — [Constellation Research](https://www.constellationr.com/insights/news/openai-touts-broadening-codex-usage-5-million-weekly-active-users)；[digitalapplied](https://www.digitalapplied.com/blog/openai-codex-4m-weekly-developers-growth-data)；[gradually.ai 汇总](https://www.gradually.ai/en/codex-statistics/)
- 2026-08 OpenAI 的 Tibo Sottiaux 称 "2000 万活跃用户"，但未给出日/周/月口径；2026-07-09 起 Codex 与 ChatGPT Work 合并入同一桌面应用并共享用量池，官方"1000 万合并用户"口径与单品指标不可直接比较【口径警告】 — [gradually.ai](https://www.gradually.ai/en/codex-statistics/)；[unite.ai](https://www.unite.ai/openai-says-codex-and-chatgpt-work-hit-10-million-users/)
- 定价：Plus $20/月、Pro $200/月；Terminal-Bench 2.0 得分 77.3%【厂商口径】 — [amux.io](https://amux.io/blog/ai-coding-tools-pricing-2026/)
- Pragmatic Engineer 2026 调查：Codex 在上一轮调查（9 个月前）尚不存在，本轮使用量已达 Cursor 的 60% — [aiproductivity 转述](https://aiproductivity.ai/news/pragmatic-engineer-survey-ai-tooling-2026/)

**Cursor（Anysphere，AI IDE + Background Agents + 自研模型 Composer）**
- ARR：2025-01 $100M → 2025-06 $500M → 2025-11 $1B → 2026-02 $2B → 2026-06 约 $4B【媒体/聚合站转述】 — [Clink ARR leaderboard](https://clinkbill.com/arr-leaderboard/cursor)；[getlatka](https://getlatka.com/companies/cursor.com)
- 维基百科条目称 2026-04 SpaceX（经 xAI）同意以 $600 亿收购 Anysphere【媒体转述，本次未能核实一手来源，需复核】 — [Wikipedia: Cursor (company)](https://en.wikipedia.org/wiki/Cursor_(company))
- 产品：Composer 2 模型 2026-03 发布（基于 Moonshot Kimi 2.5 开源权重），Composer 2.5 2026-05-18；Cursor 3 定位"与 Agent 协作的统一工作区"；Background Agents 可并行派发任务 — [getpanto 汇总](https://www.getpanto.ai/blog/cursor-ai-statistics)；[programming-helper](https://www.programming-helper.com/tech/cursor-2026-ai-first-ide-composer-agents-python)
- 企业渗透：Cursor 自称 64% 的 Fortune 500 使用、5 万+企业、每日 1 亿+行企业代码；2026 Gartner Enterprise AI Coding Agents 魔力象限 Leader【厂商口径】 — [Cursor 博客](https://cursor.com/blog/cursor-leads-gartner-mq-2026)；[beri.net](https://www.beri.net/article/cursor-benchmark-partners-enterprise-ai-coding-deployment-gap-adoption-stack-2026)
- 定价：Pro $20（含 $20 用量）、Pro+ $60（含 $70）、Ultra $200（含 $400）、Teams $40/人/月 — [amux.io](https://amux.io/blog/ai-coding-tools-pricing-2026/)

**GitHub Copilot coding agent（云端异步：从 Issue 直接产出 PR）**
- Octoverse 2025：coding agent 从 demo 到 GA，2025-05 至 2025-09 创建 100 万+ PR；Agent 活动偏向 star 多、规模大、历史久的仓库（而非一次性项目）；80% 的 GitHub 新开发者第一周即使用 Copilot【厂商口径】 — [GitHub Octoverse 2025](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/)
- 微软 FY2026 Q3：Copilot 企业客户近 14 万家（同比 3 倍）；付费订阅 470 万+（同比 +75%）；90% Fortune 100 使用【厂商口径】 — [index.dev 汇总](https://www.index.dev/blog/ai-pair-programming-statistics)；[Wikipedia: GitHub Copilot](https://en.wikipedia.org/wiki/GitHub_Copilot)

**Cognition（Devin + Windsurf → Devin Desktop）**
- 2025-07-14 收购 Windsurf：当时 Windsurf ARR $82M、350+ 企业客户、210 人 — [TechCrunch](https://techcrunch.com/2025/07/14/cognition-maker-of-the-ai-coding-agent-devin-acquires-windsurf/)
- 2026-05 完成 $1B+ 融资，估值约 $250–260 亿，ARR 约 $492M（收购后 7 个月翻倍）【媒体转述】 — [idlen.io](https://www.idlen.io/news/cognition-devin-25-billion-valuation-windsurf-vibe-coding-april-2026/)；[valueaddvc](https://valueaddvc.com/company/cognition)
- 2026-06-02 Windsurf 通过 OTA 更新更名为 Devin Desktop，windsurf.com 跳转 devin.ai — [digitalapplied](https://www.digitalapplied.com/blog/windsurf-becomes-devin-desktop-ide-migration-2026)
- 定价：2026-04 从 $500/月企业门槛降至 $20/月 + $2.25/ACU；典型 bug fix 2–3 ACU（$4.5–6.75） — [amux.io](https://amux.io/blog/ai-coding-tools-pricing-2026/)

**Google（Antigravity / Gemini CLI / Jules）**
- 2025-11 发布 Antigravity IDE（VS Code 风格、Agent-first）；2026-05-18~19 I/O 发布 Antigravity 2.0：桌面应用（多 Agent 编排）、Antigravity CLI（Go 实现，支持异步后台多 Agent）、Antigravity SDK — [TNW](https://thenextweb.com/news/google-antigravity-2-desktop-cli-sdk-io-2026)；[dev.to](https://dev.to/turingsoracle/antigravity-is-dead-long-live-antigravity-186m)
- Gemini CLI 并入 Antigravity CLI；2026-06-18 起 Gemini CLI 与 Gemini Code Assist IDE 扩展停止为免费/AI Pro/Ultra 个人用户服务，企业（Code Assist Standard/Enterprise、Google Cloud）不受影响 — [Google Developers Blog](https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/)；[Virtualization Review](https://virtualizationreview.com/articles/2026/05/19/google-moves-gemini-cli-into-antigravity-cli-as-agent-platform-expands.aspx)

**Amazon（Q Developer → Kiro）**
- Kiro 2025-07 发布（spec-driven 的 Agentic IDE）；2025-12 re:Invent 预览 Kiro Autonomous Agent（可独立工作数日，分配 Jira ticket → 返回时得到 PR）；2026-05 作为 Q Developer 正式继任者国际发布；前 3 个月 25 万用户【厂商口径/媒体转述】 — [Constellation](https://www.constellationr.com/insights/news/aws-kiro-launches-autonomous-agents-individual-developers)；[aiwiki](https://aiwiki.ai/wiki/kiro)
- Kiro Crew（多 Agent"自主工程团队"）内部 6 个月内被 3.9 万 Amazon builder 采用；内部政策要求 80% 开发者每周使用 Kiro（2026-03 仍有效）【媒体转述】 — [InfoWorld](https://www.infoworld.com/article/4204961/awss-kiro-crew-aims-to-turn-ai-coding-agents-into-autonomous-engineering-teams.html)；[agentmarketcap](https://agentmarketcap.ai/blog/2026/04/11/amazon-q-developer-vs-kiro-dual-track-coding-agent-strategy-2026)
- 2026-09 AWS 新闻稿：越南券商 TCBS 全员 460 人部署 Kiro，产品上市提速 25%【厂商口径】 — [Amazon Press](https://press.aboutamazon.com/aws/2026/9/tcbs-goes-all-in-with-kiro-amazon-web-services-agentic-coding-environment)

**ByteDance Trae / TRAE SOLO**
- 2025-01 发布 AI-native IDE（"The Real AI Engineer"）；2025 年报：MAU 超 160 万，累计注册 600 万+，覆盖近 200 国，全年生成近 1000 亿行代码【厂商口径】 — [AIbase](https://news.aibase.com/news/24099)；[知乎：一年 200 次更新](https://zhuanlan.zhihu.com/p/1989338477536502661)
- 2026-03-31 发布 SOLO 独立版（桌面 + Web），含 Code 与 MTC（More Than Coding）两种模式，双 Agent 从规划到编码端到端；SOLO 模式渗透率国际版 44%、国内版 3/10 开发者使用【厂商口径】 — [Pandaily](https://pandaily.com/byte-dance-launches-standalone-version-of-ai-coding-tool-trae-solo)
- 开源 Trae Agent 仓库自 2026-02 起无提交 — [pinggy](https://pinggy.io/blog/best_open_source_cli_coding_agents/)

**Alibaba Qoder / Tongyi Lingma（通义灵码）**
- 2026-05-20 通义灵码更名 Qoder CN；Qoder 产品族含 Qoder Desktop、QoderWork、QoderWake、Qoder CLI、Cloud Agents — [Baidu 百科](https://baike.baidu.com/en/item/Qoder/1427525)；[Alibaba Cloud 文档](https://www.alibabacloud.com/help/en/lingma/product-overview/billing-description)
- 2026 年中全球用户 500 万+；2026-08-27 达 600 万用户、10 万+ 企业客户；某份 2026 报告称 Qoder 市场份额 47.6% 居首（超过智谱、商汤、腾讯、百度之和）【厂商口径/媒体转述，原始报告机构未核实】 — [网易：47.6%](https://www.163.com/dy/article/L1VB4RB40511N33R.html)；[雷锋网](https://m.leiphone.com/category/industrynews/kMp6GgBN9B7luNaO.html)
- 2026 Gartner Enterprise AI Coding Agents 魔力象限：全球 12 家入围，阿里云连续三年 Challenger，为该象限唯一中国公司 — [新浪财经 2026-07-17](https://finance.sina.com.cn/wm/2026-07-17/doc-iniiatfe4206270.shtml)

**Tencent CodeBuddy**
- 2025-09 发布 CodeBuddy CLI 并开放 CodeBuddy IDE 公测 — [量子位](https://www.qbitai.com/2025/09/329704.html)
- 2026-03 推出面向泛知识工作者的 WorkBuddy（对应 Claude Cowork 定位） — [深圳新闻网](https://www.sznews.com/news/content/2026-03/09/content_31970172.htm)

**开源阵营（2026 年中状态）**
- GitHub star：OpenCode ~202k、OpenHands ~85k、Cline ~67k、Aider ~48k；OpenHands SWE-bench Verified 72%（开源自主 Agent 最高），2026-06 完成 $18.8M A 轮 — [pinggy](https://pinggy.io/blog/best_open_source_cli_coding_agents/)；[OpenHands 博客](https://www.openhands.dev/blog/open-source-ai-coding-agents)
- Aider 自 2026-05-22 起无提交；Roo Code 2026-05-15 关闭扩展，仓库引导用户转向社区 fork ZooCode 或 Cline — [pinggy](https://pinggy.io/blog/best_open_source_cli_coding_agents/)
- Cline：VS Code 内全文件/终端/MCP 工具访问、按动作粒度审批、多模型支持；Roo Code 为 Cline 衍生 fork（多模式、自定义 mode、默认更激进） — [PkgPulse](https://www.pkgpulse.com/guides/cline-vs-roo-code-vs-aider-open-source-ai-coding-agents-2026)
- Block Goose：2025-01-28 开源（Apache 2.0），~27k star、350+ 贡献者；2025-12-09 与 MCP、AGENTS.md 一同捐入 Linux Foundation 新设的 Agentic AI Foundation（AAIF） — [Block 官方](https://block.xyz/inside/block-open-source-introduces-codename-goose)；[AAIF 新闻稿](https://aaif.io/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation-aaif-anchored-by-new-project-contributions-including-model-context-protocol-mcp-goose-and-agents-md/)

### Inferences
- 收入指标口径差异极大（run-rate、ARR、"活跃用户"无时间窗），横向比较应只用同一来源同一时间点；厂商公布的 Fortune 500 渗透率往往以"至少一个席位"计，不代表深度使用。
- 形态上，所有头部厂商都在 2026 年同时覆盖三种形态（IDE、终端、云端异步），差异点转向：(1) 自研模型 vs 多模型路由（Cursor Composer、Google Gemini 绑定 vs Claude Code/Codex 单模型）；(2) 任务入口（Slack/Issue/Jira 触发 vs 编辑器内）；(3) 企业治理能力（SSO、审计、沙箱）。
- 对内部平台团队而言，开源 harness（Goose、OpenHands、Cline）与 Claude Agent SDK / Codex SDK 等"可嵌入 harness"是构建内部 Agent 的两条主路径——Stripe 选 Goose、Spotify 选 Claude Agent SDK（见第三节）。

### Gaps
- Google Jules 2026 年的独立状态（是否并入 Antigravity）未找到可靠来源。
- JetBrains 2026-08《AI Coding Agents: Adoption Trends》原文被拦截，未能提取数字。
- Cursor 被 SpaceX/xAI 收购的说法仅见于维基百科摘要，未核实。
- Tencent CodeBuddy、Alibaba Qoder 的对外定价与收入数据未找到。

---

## 二、测量到的生产力影响：严谨研究 vs 厂商声明

### Takeaway
独立测量的共识是：个人产出（PR 数、任务数）普遍提升 20–25%（Microsoft 2024 RCT +26% PR；Microsoft 2026 内部遥测 +24% 合并 PR；Jellyfish 0→100% 采纳 PR/人 +113%），但 METR 的 RCT 显示对高熟练度开发者在熟悉代码库上的"任务时长"效应不确定（2025：+19% 变慢；2026 复测：−18%/−4% 但置信区间跨零）；组织层面的瓶颈转移到代码评审（Faros：评审时长 +91%，高采纳团队中位评审时长 +441%）与交付稳定性（DORA 2025：吞吐↑同时不稳定性↑）。

### Cited Findings

**METR（独立 RCT）**
- 2025 年原研究：16 名有经验开源开发者，在自己熟悉的仓库上使用 AI（主要 Cursor + Claude 3.5/3.7）完成任务时间**增加 19%**；开发者事前预期快 24%、事后仍自认快 20% — [particula 转述](https://particula.tech/blog/ai-coding-tools-developer-productivity-paradox)；[andrewwegner 评论](https://andrewwegner.com/metr-ai-productivity-study-update.html)
- 2026-02-24 更新（数据采集自 2025-08 起）：57 名开发者（10 名来自原研究 + 47 名新招募）、143 个仓库、800+ 任务。原班 10 人：**−18% 时间**（95% CI −38% ~ +9%）；新招 47 人：**−4%**（CI −15% ~ +9%）。两组置信区间均包含零，"既未证实加速也未证实减速" — [METR 官方博文](https://metr.org/blog/2026-02-24-uplift-update/)；[devs-group 解读](https://devs-group.ch/en/blog/ai-productivity-studies-2026/)
- 关键偏差：30–50% 的开发者表示有些任务因"不想不用 AI 做"而选择不提交 → 选择偏差，METR 因此宣布改变实验设计，并在原研究页面加注"历史结果不再反映 AI 对开源开发者生产力的当前影响" — [METR 官方博文](https://metr.org/blog/2026-02-24-uplift-update/)；[ingenire 转述](https://ingenire.com/blog/metr-2026-developer-productivity-study)
- METR 2026-02-17 另发布"分析 coding agent transcript 以估计时间节省上界"的笔记；2026-05-11 发布"早期 2026 AI 对技术工作者生产力的自报影响"调查 — [METR notes](https://metr.org/notes/2026-02-17-exploratory-transcript-analysis-for-estimating-time-savings-from-coding-agents/)；[METR survey](https://metr.org/blog/2026-05-11-ai-usage-survey/)

**Microsoft 内部大规模遥测（独立于厂商产品团队的研究者，2026-07）**
- arXiv 2607.01418（Murphy-Hill, Butler, Savelieva）：微软 2026 年初向数万名工程师推出 Claude Code 与 GitHub Copilot CLI，4 个月观察窗口；采纳者合并的 PR 比反事实**多约 24%**，效应在 4 个月内持续；首次使用主要通过社交网络（同事可见使用）传播；留存与编码活跃度相关而非人口统计特征；结论：组织应把"可见的同伴使用"作为推广核心 — [arXiv 2607.01418](https://arxiv.org/abs/2607.01418)；[Developers Digest 解读](https://www.developersdigest.tech/blog/microsoft-cli-coding-agents-study-2026)

**Microsoft / Accenture / 匿名 Fortune 100 RCT（2024，Cui, Demirer, Jaffe, Musolff 等）**
- 三项现场实验、5000+ 开发者：Copilot 使完成任务（以 PR 计）**+26%**；微软实验中 PR、commit、build 均上升但仅 PR 显著；经验较少开发者获益更多 — [MIT 论文 PDF](https://economics.mit.edu/sites/default/files/inline-files/draft_copilot_experiments.pdf)；[DX 解读](https://newsletter.getdx.com/p/copilot-impact-on-productivity)

**DORA（Google Cloud）**
- 2025 报告（近 5000 名受访者）：90% 开发者每日使用 AI；AI 采纳与**更高交付吞吐**相关，同时与**更高不稳定性**相关；核心结论"AI 是放大器"；59% 称代码质量提升，10% 称变差，30% 不确定/不信任；提出 7 项放大 AI 效果的基础能力 — [Google Cloud 博客](https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report)；[dora.dev](https://dora.dev/dora-report-2025/)；[scrum.org 摘要](https://www.scrum.org/resources/blog/dora-report-2025-summary-state-ai-assisted-software-development)
- 2026.01《ROI of AI-Assisted Software Development》：以 500 人工程组织、全成本 $176k/人为例，首年回报约 $11.6M vs 投入 $8.4M，ROI 39%，回收期约 8 个月；提出"J 曲线"（先降后升）；强调评审等待与大 PR 无上下文审批会吞掉 AI 创造的价值 — [InfoQ 2026-05](https://www.infoq.com/news/2026/05/dora-roi-ai-assisted-dev-report/)；[kodus 解读](https://kodus.io/en/dora-accelerate-state-of-devops/)

**Stack Overflow Developer Survey**
- 2025：84% 使用或计划使用 AI；对 AI 输出准确性的信任 29%（2024 为 40%），"高度信任"仅 3%；不信任（46%）> 信任（33%）；资深开发者高信任率 2.6%、强不信任 20%；66% 首要抱怨"几乎正确但不完全正确"；45% 称调试 AI 代码比手写更耗时 — [byteiota](https://byteiota.com/stack-overflow-dev-survey-2026-ai-at-84-trust-at-3/)；[AI Economy substack](https://theaieconomy.substack.com/p/stack-overflow-2025-ai-trust-gap)
- 2026：65% 开发者使用 coding agent，但 Stack Overflow 官方称"其中六成实际上会回避使用 AI"（表述含糊，原始题项未核实） — [Stack Overflow 官方 X](https://x.com/StackOverflow/status/2107144120305115389)；[ADTmag 2026-01](https://adtmag.com/blogs/watersworks/2026/01/stack-overflow-survey.aspx)

**Faros AI《AI Productivity Paradox》（2025-07，遥测，1 万+ 开发者 / 1255 团队）**
- 高 AI 采纳团队：完成任务 +21%、合并 PR +98%，但 PR 评审时间 +91%；每开发者 bug +54%；每 PR 导致生产事故概率 >3 倍；无评审直达生产的代码 +31% — [Faros 报告页](https://www.faros.ai/blog/ai-software-engineering)；[报告 PDF](https://243608892.fs1.hubspotusercontent-na2.net/hubfs/243608892/AI_Engineering_Impact_Report_July_2025_Faros_AI.pdf)
- 高采纳下：完成编码任务 +210%，但首次评审等待中位 +156.6%、评审平均时长 +199.6%、评审中位时长 +441.5% — [Faros：评审负担](https://www.faros.ai/blog/ai-code-quality-senior-engineer-review-burden)

**Jellyfish（遥测）**
- 2025-06：AI 使用同比 +260%（基于 200 万+ PR）；平均 PR 周期 95.5h → 83.8h — [Jellyfish 2025-06](https://jellyfish.co/blog/ai-impact-data-june-2025/)
- 2025 年度回顾：采纳率 0→100% 时，中位周期时间 16.7h → 12.7h（−24%）；每工程师 PR 数 1.36 → 2.9（+113%）；高采纳公司 bug-fix PR 占比 9.5% vs 低采纳 7.5%（更多修 bug） — [Jellyfish 2025 回顾](https://jellyfish.co/blog/2025-ai-metrics-in-review/)
- 与 OpenAI 联合发布的研究涵盖 coding assistant 与 code review agent 的按工具采纳数据 — [Jellyfish 新闻稿](https://jellyfish.co/newsroom/jellyfish-reveals-ais-real-impact-on-engineering-teams/)

**Anthropic Economic Index（厂商研究，但方法学公开）**
- 2025-04-06~13 数据、50 万次交互：Claude Code **79% 自动化 / 21% 增强**（Claude.ai 为 49/51）；Claude Code 中"指令式"43.8%、"反馈循环"35.8%；语言：JS/TS 31%、HTML/CSS 28%、Python 14%、SQL 6%；初创公司占 Claude Code 对话 32.9%、企业 23.8%；**排除 Team/Enterprise/API 用量，未测量实际生产力或代码质量** — [Anthropic: impact-software-development](https://anthropic.com/research/impact-software-development)
- 2025-09 报告：Claude.ai 上单轮"指令式"自动化占比从 2024-12 的 27% 升至 2025-09 的 39% — [Anthropic 2025-09 报告](https://www.anthropic.com/research/anthropic-economic-index-september-2025-report)
- 2026-06《Cadences》报告：Claude Code 会话 54% 由 Opus 服务（聊天/Cowork 仅 10%），自主度高于聊天 — [Anthropic 2026-06 报告](https://www.anthropic.com/research/economic-index-june-2026-report)

**Google 自述（厂商口径）**
- AI 生成代码占新代码比例：2024 年初约 25% → 2025 年秋 50% → 2026-04 Cloud Next 宣布 **75%**（"AI 生成并经工程师批准"）；Pichai 称更重要的指标是"工程速度"；一项复杂代码迁移由 Agent+工程师协作完成，比一年前快 6 倍 — [Fast Company](https://www.fastcompany.com/91531519/google-ceo-says-75-of-the-companys-code-is-ai-generated)；[DevOps.com](https://devops.com/google-ceo-says-75-of-new-code-is-ai-generated/)；[Google 官方博客 Cloud Next 2026](https://blog.google/innovation-and-ai/infrastructure-and-cloud/google-cloud/cloud-next-2026-sundar-pichai/)
- Google FSE 2025 工业论文《Migrating Code At Scale With LLMs At Google》（Ziftci 等）：3 名开发者 12 个月完成 39 项迁移，提交 595 个变更 / 93,574 处编辑，**74.45% 的变更、69.46% 的编辑由 LLM 生成**，开发者工作量减半；int32→int64 迁移从历史上 2 年缩短一半【公司研究，经同行评审】 — [arXiv 2504.09691](https://arxiv.org/abs/2504.09691)；[DX 摘要](https://getdx.com/research/migrating-code-at-scale-with-llms-at-google/)

### Inferences
- "产出 +20~25%"是跨 RCT 与遥测最稳健的数字，但它衡量的是 PR/任务计数，不是业务交付；METR 的"时长"指标对高熟练度、高上下文任务最不利，提示内部 Agent 应优先部署在**上下文已结构化、验证自动化**的任务（迁移、测试、修 lint）而非资深工程师的核心架构工作。
- Faros/DORA/Spotify（第三节）三方独立指向同一结论：**评审能力是 2026 年的硬瓶颈**，任何内部 Agent 规划若不同时投资 AI 评审与自动合并策略，吞吐增益会被评审队列吞掉并带来稳定性退化。
- 自报数据（SO、Pragmatic Engineer）与遥测数据的错位（开发者"感觉"更快、信任却下降）说明必须以遥测与事故率作为内部 KPI，而非满意度。

### Gaps
- 任务中提到的 Google "约 10% 工程速度提升"数字，本次未找到可引用的原始来源（Pichai 在 Lex Fridman 访谈的原话无法核实），仅找到"工程速度是重要指标"的表述。
- DORA 2026 年度主报告（通常 9–10 月发布）截至本研究未见；仅有 2026.01 ROI 报告。
- JetBrains 2026-08 调查、Stack Overflow 2026 完整题项数据未获取。

---

## 三、大厂内部 Agent 平台案例

### Takeaway
成功案例共享三个结构特征：(1) **Agent 入口贴近源码控制与 CI 而非编辑器**（Meta DevMate、Spotify Honk、Stripe Minions、Shopify River）；(2) **沿用人类同一套 lint/CI/规则文件作为验证闭环**，并用确定性步骤包裹 LLM（Airbnb 状态机、Stripe blueprints、Uber Lang Effect）；(3) **先在"迁移/测试/评审"等高重复、强验证任务上拿到规模数字**（Amazon 4500 开发者年、Airbnb 18 个月→6 周、Uber 21,000 小时、Spotify 1000 PR/10 天）。中国厂商（ByteDance 92%、Tencent 90%+、Meituan 90%+）以"工程师覆盖率 + AI 代码占比"为主要公开指标，组织推力明显强于欧美。

### Cited Findings

**Google**
- 见第二节：75% 新代码 AI 生成（2026-04）；FSE 2025 迁移论文（LLM 生成 74% 变更）；Agent+工程师迁移 6 倍提速。— [Fast Company](https://www.fastcompany.com/91531519/google-ceo-says-75-of-the-companys-code-is-ai-generated)；[arXiv 2504.09691](https://arxiv.org/abs/2504.09691)
- 对外产品化为 Antigravity 2.0 / Antigravity CLI（见第一节）。

**Meta**
- DevMate：Dev Infra（约 1000 人，服务 4 万工程师）在 James Everingham 领导下建设的内部 Agent 平台，工程师可在一个界面发现、fork、构建连接源码控制的 Agent；平台内 200–300 个 Agent 运行，**Agent 提交的 diff 约占 Meta 全部 diff 的 50%**；核心转变是"把 Agent 行为从编辑器移到源码控制层"（"Agent control plane"）【前负责人口述，经 Guild.ai/LinearB 转述，Everingham 现为 Guild.ai CEO，存在利益相关】 — [Guild: DevMate 起源](https://www.guild.ai/blog/news/james-everingham-devmate-origin-story-theory-ventures)；[LinearB](https://linearb.io/blog/meta-ai-control-plane-james-everingham-guildai)；[Tunguz Office Hours](https://tomtunguz.com/office-hours-jim-everingham-developer-infrastructure/)
- 2025-04 Meta 工程师公开提及 Devmate bot 会查看测试失败、诊断并提交修复 diff — [Hasnain Lakhani X](https://x.com/mhlakhani/status/1914905942652539154)
- ACH（Automated Compliance Hardening，变异测试引导的 LLM 测试生成）：应用于 7 个平台 10,795 个 Android Kotlin 类，生成 9,095 个 mutant 与 571 个隐私加固测试；Messenger/WhatsApp test-a-thon 中工程师接受 73% 的测试、判定 36% 与隐私相关；571 个测试中 277 个若只看行覆盖会被丢弃；mutant kill rate 12–15% vs 覆盖导向的 TestGen-LLM 仅 2.0–2.4%；等价 mutant 检测 precision 0.79 / recall 0.47（预处理后 0.95/0.96）【公司研究论文】 — [arXiv 2501.12862](https://arxiv.org/html/2501.12862v1)；[Meta Engineering 2025-09-30](https://engineering.fb.com/2025/09/30/security/llms-are-the-key-to-mutation-testing-and-better-compliance/)；[InfoQ 2026-01](https://www.infoq.com/news/2026/01/meta-llm-mutation-testing)
- 媒体报道 Meta 要求部分团队到 2026 年中 75% 以上提交代码由 AI 生成，并推行内部工具 MetaCode / Metamate【媒体转述，未核实】 — [blockchain-council](https://www.blockchain-council.org/news/meta-ai-asking-engineers-75-percent-code-ai-tools/)；[TechFlow](https://www.techflowpost.com/en-US/newsletter/130852)

**Uber（约 5000 工程师，数亿行代码 monorepo）**
- uReview（AI 代码评审）：四阶段 prompt-chaining（生成评论 → 过滤 → 验证 → 去重）；分析 Uber 每周约 65,000 个 diff 的 90% 以上；工程师"有用"评价 75%，65% 的评论被处理【厂商口径，Uber 博客 2025-08】 — [Uber 博客 uReview](https://www.uber.com/ng/en/blog/ureview/)；[Uber Eng X 2025-08](https://x.com/UberEng/status/1955300802366787946)
- AutoCover（测试生成）：与业界 agentic 工具相比 2–3 倍覆盖率、一半时间；将 developer platform 覆盖率提高 10%，折合约 21,000 开发者小时；每月生成数千测试 — [ZenML LLMOps DB](https://www.zenml.io/llmops-database/ai-powered-developer-tools-for-code-quality-and-test-generation)
- Validator（IDE 内最佳实践/安全违规标记，LangGraph agent）、Fixrleak（Java 资源泄漏修复：构建 + 全量测试 + SonarQube 复检）、Genie（Picasso 工作流助手）；统一在自研 "Lang Effect" 框架（封装 LangGraph/LangChain 以对接内部系统）之上 — [ZenML: LangGraph at Uber](https://www.zenml.io/llmops-database/building-ai-developer-tools-using-langgraph-for-large-scale-software-development)；[Uber 博客 Fixrleak](https://www.uber.com/us/en/blog/fixrleak-fixing-java-resource-leaks-with-genai/)
- Pragmatic Engineer 2025 深度报道：92% 工程师每月使用 Agent【媒体转述】 — [Pragmatic Engineer](https://newsletter.pragmaticengineer.com/p/how-uber-uses-ai-for-development)；[aiproductivity 转述](https://aiproductivity.ai/news/uber-ai-development-inside-look/)
- 二手来源称 Uber 2025-12 向约 5000 工程师开放 Claude Code，2026-02 用量翻倍，2026-03 84% 开发者被归为 agentic coding 用户，**2026-04 耗尽全年 AI 预算**【低质量来源，未核实，仅供提示成本风险】 — [kunalganglani 博客](https://www.kunalganglani.com/blog/ai-agent-cost-per-task-2026)

**Airbnb（2025-03）**
- 约 3,500 个 React 测试文件 Enzyme → React Testing Library：人工预估 18 个月，LLM 流水线 6 周完成；状态机式逐文件流转（Enzyme 重构 → Jest 修复 → lint 修复 → TS 检查），每阶段通过才前进，配可配置重试循环与长尾文件的富上下文 prompt；首轮批量 4 小时内完成 75% 文件，约 900 个卡住；最终 97% 自动化，3% 以 LLM 产出为基线人工完成【公司博客】 — [InfoQ 2025-03](https://www.infoq.com/news/2025/03/airbnb-llm-test-migration/)；[ByteByteGo 解读](https://blog.bytebytego.com/p/inside-airbnbs-ai-powered-pipeline)

**Amazon（2024-08，Q Developer Java 升级）**
- 30,000 个生产应用 Java 8/11 → 17；节省约 4,500 开发者年；每年 $260M 性能/安全收益；单应用升级从约 50 开发者日降至数小时；79% 自动生成的代码评审无需修改直接发布；6 个月内升级超 50% 生产 Java 系统【厂商口径，Jassy 公开信】 — [AWS DevOps 博客](https://aws.amazon.com/blogs/devops/amazon-q-developer-just-reached-a-260-million-dollar-milestone)；[Digiday](https://digiday.com/media/how-amazons-genai-tool-for-developers-is-saving-4500-years-of-work-260-million-annually/)；[The Register 批评](https://www.theregister.com/2024/09/05/amazon_q_developer_gartner/)
- 2025-12 Kiro 相关事故：据 FT 报道，工程师用 Kiro 对线上系统做基础设施变更，Agent 判断"最快路径是删除整个环境重建"，导致 AWS Cost Explorer（中国区）13 小时中断；Amazon 2026-02-20 声明称系"用户错误、权限配置过宽，而非 AI"；多名员工称这是数月内至少第二次 AI 工具引发的服务中断；此后 Amazon 对所有生产变更强制同行评审【媒体报道 + 公司声明】 — [AI Incident Database #1442](https://incidentdatabase.ai/cite/1442/)；[BigGo 2026-02](https://finance.biggo.com/news/202602202120_Amazon_AI_Kiro_AWS_Outage_User_Error)

**Stripe Minions（2026-03 公开）**
- 内部"一次性端到端" coding agent：每周产出 **1,300+ 个 PR，零人工编写代码**，全部经人工评审；入口为 Slack 表情反应 / 工单；5 个 Agent 各自在 <10 秒内拉起隔离云机器，读取文档、写代码、跑 lint、推 CI、准备 PR；基于 Block 的 Goose harness；通过 MCP 暴露近 500 个内部工具（文档、工单、构建状态、代码搜索等）；采用 "blueprints"（确定性节点 + agentic 节点的混合图）而非纯 agent loop；与人类共用同一套 linter、CI 与规则文件【公司在 Lenny's 播客/InfoQ 的自述】 — [InfoQ 2026-03](https://infoq.com/news/2026/03/stripe-autonomous-coding-agents/)；[Lenny's Newsletter](https://www.lennysnewsletter.com/p/how-stripe-built-minionsai-coding)；[ByteByteGo](https://blog.bytebytego.com/p/how-stripes-minions-ship-1300-prs)

**Spotify Honk（后台 coding agent，2025-11 起系列博客）**
- Part 1（2025-11）：数百名开发者使用，1,500+ PR 合并；可从 Slack/GitHub/任意 MCP 工具触发；每月合并 650+ Agent PR【公司博客】 — [Spotify Eng Part 1](https://engineering.atspotify.com/2025/11/spotifys-background-coding-agent-part-1)；[everydev 转述](https://www.everydev.ai/p/blog-spotify-built-an-ai-coding-agent-honk)
- QCon London 2026-03：Honk 现在每 10 天合并 1,000 个 PR（6 个月前为 3 个月 1,000 个）；Honk 用 Claude Agent SDK 运行 Claude，封装在 Spotify 自有 harness 中，部署为 Kubernetes pod；与 Fleet Management 的 Fleetshift 集成（人管编排：选目标、排期、追踪进度；Honk 做实际代码修改）；Spotify 自 Fleet Management 以来已合并 250 万+ 自动维护 PR，绝大多数无人工介入自动合并，2024 年中以来约一半 PR 为自动化产生；结果是**待人工评审的 PR 多了 76%**，评审成为新约束【公司演讲，InfoQ 转述】 — [InfoQ QCon London 2026](https://www.infoq.com/news/2026/03/spotify-honk-rewrite/)；[QCon 议程](https://qconlondon.com/presentation/mar2026/rewriting-all-spotifys-code-base-all-time)
- Part 4（2026-04）：用后台 Agent 做下游消费者数据集迁移——用自然语言描述变更，Agent 决定如何应用，而非为每个变换写脚本 — [Spotify Eng Part 4](https://engineering.atspotify.com/2026/4/background-coding-agents-dataset-migrations-honk-part-4)
- 2026-06《Coding Is No Longer the Constraint》：把开发者体验从"面向个人"扩展到"面向团队与 Agent" — [Spotify Eng 2026-06](https://engineering.atspotify.com/2026/6/code-with-claude-coding-is-no-longer-the-constraint)
- Spotify 实验平台团队另撰文讨论"AI 写代码时，谁决定上线"（实验/发布门禁） — [Confidence by Spotify](https://confidence.spotify.com/blog/when-ai-writes-the-code)

**Shopify（2026）**
- River：住在公司 Slack 的 Agent，上线数月后 **Shopify 全部合并 PR 的 1/8 由其共同署名**；只在公开频道运行以保证可见性；运行在内部 Agent 平台 Aquifer 上（提供 session、harness、sandbox、gateway、持久事件日志、凭证代理、可观测流水线）【公司博客】 — [Shopify Eng: Under the River](https://shopify.engineering/under-the-river)；[MindStudio 解读](https://www.mindstudio.ai/blog/how-to-make-ai-work-visible-shopify-river)
- 集中式 LLM proxy：Claude Code、Copilot 等所有 AI 请求经同一网关到达模型供应商（统一计费/审计/路由）；Quick：面向 AI 时代的内部托管平台 — [Shopify Eng: Quick](https://shopify.engineering/quick)；[Bessemer: Shopify AI-first 策略 PDF](https://www.bvp.com/assets/uploads/2026/04/Shopifys-strategy-for-AI-first-engineering-1.pdf)

**Block（Goose）**
- 约 1.2 万员工中 60% 每周使用 Goose，覆盖 15 种岗位（工程、销售、设计、产品、客服）；使用 Agent 的任务上开发时间节省 50–75%【厂商口径】 — [Anthropic 客户案例](https://www.anthropic.com/customers/block)；[the-agent-report](https://the-agent-report.com/2026/05/block-goose-ai-agent-recipe-runner-scaled-60-percent/)

**Salesforce（2026）**
- 预计 2026 年在 Anthropic token 上花费近 $300M，大部分用于编码 Agent；以"工程团队生产力提升 30%+"为由自 2025 年起冻结工程师招聘并延续至 2026；约 1.5 万工程师与 Claude、Codex、Cursor 协作；销售人员同期 +20%【媒体转述 Benioff 公开言论】 — [Fortune 2026-05-28](https://fortune.com/2026/05/28/ai-slashes-white-collar-jobs-salesforce-ceo-marc-benioff-one-department-still-hiring-sales/)；[Enterprise DNA](https://enterprisedna.co/resources/news/salesforce-300m-anthropic-tokens-engineer-hiring-freeze-2026/)

**Netflix**
- 3,000+ 开发者；2025-11 与 Anthropic 联合网络研讨会披露基于 Claude Sonnet 4.5 的内部 Agent 规模化经验（集中化上下文基础设施、配置管理、评估框架）；招聘 JD 显示方向为智能构建/测试选择、自动代码评审、triage 自动化、Agent Platform【厂商活动/招聘信息】 — [Anthropic 网络研讨会](https://www.anthropic.com/webinars/scaling-ai-agent-development-at-netflix)；[Netflix JD](https://netflix.wd108.myworkdayjobs.com/Netflix/job/USA---Remote/Software-Engineer-5---Agent-Platform--AI-Platform_JR41100)

**Pinterest（2024，早于时间窗，供参考）**
- Querybook 内 Text-to-SQL：两版架构，第二版加入 RAG 表选择（离线向量索引、NLP 表搜索、表再选、查询摘要）；通过低基数列唯一值注入、schema 裁剪应对上下文窗口 — [Pinterest Eng Medium](https://medium.com/pinterest-engineering/how-we-built-text-to-sql-at-pinterest-30bad30dabff)

**ByteDance（Trae 内部化）**
- 2025-12-18 公告：字节内部 **92%+ 工程师**使用 TRAE 辅助开发（此前口径为 80%）；抖音直播服务团队将 TRAE 接入 DevOps 全链路后 **AI 代码贡献率 43%**；同期推出 TRAE CN 企业版【厂商口径】 — [品玩](https://www.pingwest.com/a/309943)；[知乎转载](https://zhuanlan.zhihu.com/p/1985005077287675436)
- 字节研发负责人与 TRAE 合作的首个开源项目称 AI 写了 85% 代码【厂商口径】 — [知乎](https://zhuanlan.zhihu.com/p/1919342853500434148)
- 甲子光年报道 TRAE 百万月活与开发者生态战略（2025） — [澎湃/甲子光年](https://www.thepaper.cn/newsDetail_forward_31004647)

**Alibaba**
- 知识引擎上线后：用户代码保留率 +11%、输入 token 消耗 −40%、对话轮次 −33%【厂商口径】；2026 届校招 AI 相关岗位占比超六成，阿里云/钉钉 AI 岗位 80% — [雷锋网](https://m.leiphone.com/category/industrynews/kMp6GgBN9B7luNaO.html)；[网易](https://www.163.com/dy/article/L1VB4RB40511N33R.html)

**Tencent**
- 截至 2025 年底：CodeBuddy 覆盖腾讯 90%+ 工程师，多数团队 90%+ 代码由 AI 生成（另一口径：AI 代码占比 >50%），编码时间平均缩短 40%+，研发整体效率提升 16%+【厂商口径，两处占比口径不一致】 — [腾讯云开发者社区](https://cloud.tencent.com/developer/article/2677102)；[36kr 英文](https://eu.36kr.com/en/p/3878580738158852)

**Meituan**
- 自研工具 CatPaw；NoCode 负责人程达通称每周约 50% 新代码由 AI 生成，90%+ 工程团队成员使用 AI 编码工具；有内部中层称 2026 年初起技术部门 95%+ 代码工作依赖 CatPaw【媒体转述】 — [CBNData](https://www.cbndata.com/information/295471)
- 2026-05-07 美团技术团队博客《用 Agent 评测思路管理 AI Coding——31 万行代码 AI 重构的实践》：AI 生成代码占比 90%+，提出以 Agent 评测（而非人工逐行）管理 AI 产出的范式【公司博客，原文被拦截，细节未核实】 — [美团技术团队](https://tech.meituan.com/2026/05/07/Agent-AI-Coding.html)；[转述](https://aitoolly.com/zh/ai-news/article/2026-06-22-managing-ai-coding-with-agent-evaluation-meituans-practice-in-refactoring-310000-lines-of-code)

### Inferences
- 对 TikTok 推荐架构团队最可迁移的模式是 **Spotify Fleetshift + Honk** 与 **Google 迁移论文**：推荐系统有大量"同构变更扩散到数百服务/数据集"的工作（特征口径升级、SDK 版本、数据集下游迁移），Agent 在"人管编排、Agent 做修改、CI 做验证"的三层结构下已被证明可达每 10 天 1000 PR 的吞吐。
- Meta DevMate 的"50% diff"与 Shopify River 的"1/8 PR"差异提示：Agent 产出占比高度依赖是否把**自动化维护类 PR**计入；内部 KPI 需区分"Agent 独立提交"与"Agent 辅助提交"。
- Stripe 与 Uber 都选择**自建 harness 并用确定性步骤包裹 LLM**（blueprints / Lang Effect / prompt-chaining），而非直接采购商业 Agent；这对拥有内部工具链（TCE、Argos、Metrics 等）的组织更现实，MCP 成为暴露内部工具的事实标准（Stripe 近 500 个 MCP 工具）。
- Amazon Kiro 事故说明：对基础设施/线上环境的 Agent 操作必须有独立于 Agent 的权限边界，不能依赖 Agent 的"判断"。

### Gaps
- Meta DevMate 的 "50% diffs" 仅来自前负责人（现竞品 CEO）口述，Meta 官方未发布；Meta 官方工程博客仅确认 ACH/TestGen-LLM 等测试工作。
- Uber "耗尽 2026 AI 预算"、Microsoft "取消内部 Claude Code 许可"均来自低质量来源，未能核实，不建议引用为事实。
- Spotify "开发者自 12 月起不再手写代码"的说法仅见于二手博客标题，未核实。
- LinkedIn、Netflix 的内部 Agent 具体量化结果未找到公开数据；Pinterest 无 2025–2026 新披露。
- ByteDance Doubao coding 模型在内部 Trae 中的使用比例、字节内部"AI coding 7 条反常识结论"原文细节未获取。

---

## 四、有效的组织模式：评审、仓库卫生、平台团队、推广、权限与成本治理

### Takeaway
2026 年的共识实践是"**先修评审与验证，再放量生成**"：AI 评审前置（Uber uReview 覆盖 90% diff）、仓库级 Agent 上下文文件（AGENTS.md 已被 6 万+ 项目采用）、集中 LLM 网关与沙箱（Shopify Aquifer/LLM proxy、Stripe 隔离云机）、以"同伴可见使用"而非行政命令驱动采纳（Microsoft 研究），同时用按人/仓库/工作流的 token 计量对冲成本失控风险。

### Cited Findings
- **AI-first 评审**：Uber uReview 四阶段架构覆盖 90%+ 周 diff、75% 有用率、65% 评论被处理 — [Uber 博客](https://www.uber.com/ng/en/blog/ureview/)；DORA 2026 ROI 报告将评审等待与大 PR 无上下文审批列为 AI 价值流失的两大点 — [InfoQ](https://www.infoq.com/news/2026/05/dora-roi-ai-assisted-dev-report/)；Faros 数据显示高采纳下评审中位时长 +441% — [Faros](https://www.faros.ai/blog/ai-code-quality-senior-engineer-review-burden)
- **仓库卫生 / Agent 上下文文件**：AGENTS.md 自 2025-08 发布后被 6 万+ 开源项目采用，Amp、Codex、Cursor、Devin、Factory、Gemini CLI、Copilot、Jules、VS Code 等支持；内容为构建/测试命令、代码风格、架构决策；无 schema、纯 Markdown — [AAIF 新闻稿](https://aaif.io/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation-aaif-anchored-by-new-project-contributions-including-model-context-protocol-mcp-goose-and-agents-md/)；[codersera 指南](https://codersera.com/blog/agents-md-complete-guide-2026/)
- **开放标准治理**：2025-12-09 Linux Foundation 成立 AAIF，托管 MCP、Goose、AGENTS.md；2026-04 成员 170+，MCP 月下载 1.1 亿+ — [intuitionlabs](https://intuitionlabs.ai/articles/agentic-ai-foundation-open-standards)；[OpenAI 公告](https://openai.com/index/agentic-ai-foundation/)
- **同一套验证闭环**：Stripe Minions 与人类共用 linter/CI/规则文件 — [InfoQ](https://infoq.com/news/2026/03/stripe-autonomous-coding-agents/)；Airbnb 用确定性状态机 + 重试包裹 LLM — [InfoQ](https://www.infoq.com/news/2025/03/airbnb-llm-test-migration/)；Uber Fixrleak 以构建 + 全量测试 + SonarQube 复检作为接受条件 — [Uber 博客](https://www.uber.com/us/en/blog/fixrleak-fixing-java-resource-leaks-with-genai/)
- **专职平台团队与"Agent control plane"**：Meta Dev Infra 约 1000 人服务 4 万工程师，DevMate 让工程师发现/fork/构建 Agent — [LinearB](https://linearb.io/blog/meta-ai-control-plane-james-everingham-guildai)；Shopify Aquifer 提供 session/harness/sandbox/gateway/事件日志/凭证代理/可观测 — [Shopify Eng](https://shopify.engineering/under-the-river)；Spotify 将 Honk 放入 Fleet Management 既有编排 — [InfoQ](https://www.infoq.com/news/2026/03/spotify-honk-rewrite/)
- **采纳曲线与推广机制**：Microsoft 研究发现首次使用主要经社交网络传播，留存与编码活跃度相关，建议把"可见的同伴使用"作为推广核心 — [arXiv 2607.01418](https://arxiv.org/abs/2607.01418)；Microsoft/Accenture RCT 显示经验较少者受益更多 — [MIT PDF](https://economics.mit.edu/sites/default/files/inline-files/draft_copilot_experiments.pdf)
- **自上而下的使用指标/强制**：ByteDance 92% 工程师覆盖（2025-12） — [品玩](https://www.pingwest.com/a/309943)；Amazon 要求 80% 开发者每周使用 Kiro — [agentmarketcap](https://agentmarketcap.ai/blog/2026/04/11/amazon-q-developer-vs-kiro-dual-track-coding-agent-strategy-2026)；Meta 被报道设定 75% AI 代码目标【未核实】 — [blockchain-council](https://www.blockchain-council.org/news/meta-ai-asking-engineers-75-percent-code-ai-tools/)
- **可见性作为治理手段**：Shopify River 仅在公开 Slack 频道运行，"所有对话发生在全公司可见处" — [Shopify Eng](https://shopify.engineering/under-the-river)
- **企业级安全/权限控制清单**（行业实践总结）：SSO、接入 SIEM 的审计日志、Agent PR 的密钥扫描、PR 策略门禁、许可证治理、Agent 执行沙箱隔离（建议 microVM 级）、事故响应 runbook — [Northflank](https://northflank.com/blog/enterprise-ai-coding-agent-deployment)
- **成本治理**：2026 年中每任务 Agent 成本约 $0.03–0.13（随模型/工具变化），多数团队无可见性；需按用户/仓库/项目/工作流追踪 — [kunalganglani](https://www.kunalganglani.com/blog/ai-agent-cost-per-task-2026)；arXiv 2609.28919《Control the Harness, Control the Cost》讨论在企业内通过 harness 层做模型路由与治理 — [arXiv 2609.28919](https://arxiv.org/html/2609.28919v1)；Shopify 以集中 LLM proxy 统一所有 AI 请求 — [weaverse 解读](https://weaverse.io/blogs/shopify-ai-engineering-playbook-hydrogen-2026)；Salesforce 2026 年 Anthropic token 预算近 $300M — [Enterprise DNA](https://enterprisedna.co/resources/news/salesforce-300m-anthropic-tokens-engineer-hiring-freeze-2026/)
- **事故后的流程修正**：Kiro 事故后 Amazon 对所有生产变更强制同行评审 — [BigGo](https://finance.biggo.com/news/202602202120_Amazon_AI_Kiro_AWS_Outage_User_Error)
- **Agent 评测替代人工逐行审查**：美团以 Agent 评测思路管理 31 万行 AI 重构 — [美团技术团队](https://tech.meituan.com/2026/05/07/Agent-AI-Coding.html)
- **DORA 7 项基础能力**（放大 AI 正向效果）：报告指出回报主要来自内部平台质量、工作流清晰度与团队对齐，而非工具本身 — [Google Cloud 博客](https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report)

### Inferences
- 对大型 monorepo 组织，最高杠杆的三件事依次是：(1) 为 Agent 补齐可机读的仓库上下文与一键构建/测试入口（AGENTS.md + hermetic 测试）；(2) 把 AI 评审放到 PR 首道关卡并给出"可自动合并"的变更类别白名单；(3) 建一个集中网关做身份、审计、路由与按团队计量，否则成本与安全问题会在采纳曲线陡升期同时爆发。
- "行政覆盖率指标"（90%+ 工程师使用）在中国厂商普遍，但独立研究显示留存由实际编码活跃度与同伴示范驱动；覆盖率 KPI 若不配合遥测质量指标（事故率、回滚率、评审时长）容易导致"打开即算使用"。

### Gaps
- 未找到任何公司公开其内部 Agent 的**权限模型细节**（如对内部代码/数据的分级访问、Agent 身份与人类身份的分离）；Shopify Aquifer 的"凭证代理"是唯一提到的机制。
- 未找到公开的内部 Agent **成本/收益对账**（token 支出 vs 节省工时）案例，Amazon $260M 为唯一量化但为 2024 年数据。

---

## 五、Coding Agent 在大型代码库中仍然失败的地方

### Takeaway
2026 年的失败模式集中在：长时程任务的质量衰减（SlopCodeBench）、仓库级"工作集"超出上下文导致的连贯性债务、跨仓库调用链不可见、整仓迁移通过率低（8 个前沿模型 520 次运行仅 28 次全部通过验证）、以及"验证债务"——评审队列膨胀、"几乎正确"代码进入生产、事故概率上升。Amazon Kiro 事故与 METR 的选择偏差则提示运维与测量层面的新风险。

### Cited Findings
- **长时程退化**：SlopCodeBench（arXiv 2603.24755，2026-03）专门度量 coding agent 在长时程迭代任务中的质量退化 — [arXiv 2603.24755](https://arxiv.org/pdf/2603.24755)
- **工作集 / 连贯性债务**：arXiv 2608.16630（2026-08）提出仓库级任务中 Agent 的"工作集"概念与 coherence debt — [arXiv 2608.16630](https://arxiv.org/pdf/2608.16630)
- **整仓迁移**：8 个前沿模型 520 次运行中仅 28 次通过全部验证阶段；20 个任务中 13 个没有任何被接受的解；通过迁移检查的运行中 58% 达到 99% 的修复检查，但仅 26% 达到 100%【个人博客实验，2026-08-25，未经同行评审】 — [Ken Ashe](https://kenashe.ai/blog/2026-08-25-coding-agents-still-struggle-with-whole-repo-migrations)
- **跨仓库盲区**：各仓库单独索引导致 Agent 看不到服务间调用链；变更涉及多仓库时 Agent "既不知道也不会问"；隐藏技术债（覆盖、自定义装饰器、兄弟微服务）对 Agent 不可见 — [Supermemory 2026-06](https://supermemory.ai/blog/memory-bottleneck-large-repo-coding-agents/)；[Augment Code](https://www.augmentcode.com/tools/ai-coding-assistants-for-large-codebases-a-complete-guide)
- **验证债务 / 评审瓶颈**：Faros：高采纳下评审中位时长 +441.5%、无评审进入生产的代码 +31%、每 PR 事故概率 >3 倍 — [Faros](https://www.faros.ai/blog/ai-code-quality-senior-engineer-review-burden)；Spotify：待评审 PR +76% — [InfoQ](https://www.infoq.com/news/2026/03/spotify-honk-rewrite/)；Stack Overflow：66% 抱怨"几乎正确"，45% 称调试 AI 代码更耗时 — [byteiota](https://byteiota.com/stack-overflow-dev-survey-2026-ai-at-84-trust-at-3/)
- **稳定性**：DORA 2025 发现 AI 采纳与交付不稳定性正相关 — [dora.dev](https://dora.dev/dora-report-2025/)
- **长尾文件**：Airbnb 首轮 4 小时完成 75%，剩余约 900 个文件需富上下文重试，最后 3% 仍需人工 — [InfoQ](https://www.infoq.com/news/2025/03/airbnb-llm-test-migration/)
- **运维边界**：Kiro 为完成任务选择删除并重建整个环境，导致 13 小时中断（Amazon 归因为权限配置过宽） — [AI Incident Database](https://incidentdatabase.ai/cite/1442/)
- **测量本身的失败**：METR 2026 复测中 30–50% 开发者因不愿在无 AI 条件下做任务而不提交，导致 RCT 不再可靠 — [METR](https://metr.org/blog/2026-02-24-uplift-update/)
- **架构判断类任务**：Agent 在不熟悉的代码库、遗留系统的复杂多文件变更、需要架构判断的任务上仍表现差 — [Faros 2026 评测](https://www.faros.ai/blog/best-ai-coding-agents-2026)；[mikemason.ca](https://mikemason.ca/writing/ai-coding-agents-jan-2026/)
- **开源 Agent 生态脆弱性**：Aider 停更、Roo Code 关闭（2026-05）说明依赖单一开源 harness 的供应风险 — [pinggy](https://pinggy.io/blog/best_open_source_cli_coding_agents/)

### Inferences
- 推荐系统代码库的典型特征（多语言、特征/模型/服务跨仓库、重度依赖线上数据与 A/B 门禁）恰好落在当前 Agent 最弱的区域（跨仓库调用链、需要线上验证的变更）；可行的切入点是把"跨仓库"问题转化为"单仓库 + 显式契约"（如 schema/proto 变更由 Agent 在各仓库独立应用并由 CI 契约测试验证），并把线上验证交给既有实验平台门禁（Spotify Confidence 的做法）。
- "验证债务"是真正的约束：如果没有可信的自动验证（hermetic 测试、契约测试、变异测试级别的覆盖），放量生成只会把工作从"写"搬到"审"，Faros 的 +441% 评审时长就是这一点的量化。

### Gaps
- 未找到针对 **ML/推荐系统代码**（特征流水线、训练代码、在线服务）的 coding agent 专项评测或大厂案例。
- 整仓迁移通过率数据来自个人博客实验，缺乏同行评审的大规模基准（SlopCodeBench、arXiv 2608.16630 原文被拦截，未能核对数字）。
- 未找到关于"复现构建环境/flaky test 对 Agent 影响"的量化研究。
