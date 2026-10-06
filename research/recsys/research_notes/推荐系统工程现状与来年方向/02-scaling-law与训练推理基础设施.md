# 推荐系统的 Scaling Law 证据与训练/推理基础设施、算力经济学（2025 年中 – 2026 年 10 月）

> 调研方法与来源说明（2026-10-06）
> - 本环境的网络出口封锁了 arxiv.org、engineering.fb.com、about.fb.com、pytorch.org、huggingface.co、medium.com、usenix.org 等绝大多数站点；WebSearch 的会话配额在第三轮后耗尽。因此：(1) **论文全文**通过 GitHub 上的公开论文镜像仓库（`guyulongcs/Deep-Learning-for-Search-Recommendation-Advertisements`，raw.githubusercontent.com 可达）下载 PDF 并用 pdftotext 提取后逐篇核对，引用时给出**论文的 arXiv 正式链接**；(2) **开源仓库 README/benchmark**（NVIDIA recsys-examples、TorchRec、HugeCTR、Monolith）直接读取；(3) 公司博客、财报电话会、芯片新闻等只拿到**搜索引擎摘要**，无法读全文，相应条目标注"（搜索摘要，未读全文）"，权威度相应下调。
> - 权威度标注：**A** = 公司一手论文/官方仓库/官方博客（已读全文）；**B** = 一手来源但只读到摘要；**C** = 二手解读/媒体转述。
> - 所有"未核实"的说法都放在各节 Gaps 中，不写入正文结论。

---

## 1. Scaling law 在推荐里的公开证据：谁在涨、谁在饱和

### Takeaway
2025 年中至 2026 年，Meta、字节、快手、阿里、腾讯、美团、Pinterest、Google 都公开了"效果随参数/FLOPs/序列长度呈幂律提升"的工业证据，但几乎所有论文同时承认**前提是架构必须先"GPU 友好化"**（老架构 MFU 只有 3–15%，堆参数会先撞上延迟/成本墙）；真正"持续上涨"的轴是**用户行为序列长度**与**算力（FLOPs/样本）**，而**纯 dense 参数**在 1B–2B 以上普遍出现边际收益递减（OneRec-V2 2B→4B 仅降损 0.03；TokenMixer-Large 1B 以上必须宽深平衡扩展；RankMixer 承认 100M 以下仅有限收益）。

### Cited Findings

**背景（2024 年，Meta）**
- Wukong（Meta，ICML 2024）：用堆叠 FM 建立推荐侧 scaling law，在内部数据上跨两个数量级模型复杂度、超过 100 GFLOP/example 仍保持幂律；对照组 DLRM/DCNv2/AutoInt 在约 31 GFLOP/example 后质量饱和；参数扩展到 6370 亿以上仍有稳定改善；内部数据上 0.02% 相对 LogLoss 视为显著 — [arXiv 2403.02545](https://arxiv.org/abs/2403.02545)（论文，2024-03/06，权威度 A）。搜索摘要另给出"每 4 倍算力约 0.1% LogLoss 提升"的数字（[themoonlight 解读](https://www.themoonlight.io/en/review/wukong-towards-a-scaling-law-for-large-scale-recommendation)，权威度 C，未在全文核对）。
- HSTU / Generative Recommenders（Meta，ICML 2024）：1.5 万亿参数模型线上 A/B +12.4%，质量随训练算力跨三个数量级呈幂律 — [arXiv 2402.17152](https://arxiv.org/abs/2402.17152)（论文，2024-02，权威度 A；本次仅核对 NVIDIA recsys-examples README 中的转述）。搜索摘要称"判别式模型约在 2000 亿参数处停滞"（权威度 C，未核实）。

**Meta（2025 年中 – 2026 年）**
- HyperCast / Foundation–Expert 范式（2025-08）：中心 FM 在跨 surface、终身、多模态用户数据上流式训练，通过 target-aware embedding 传给各 surface 的轻量 expert；FM→expert 的指标迁移率 0.64–1.0；线上服务每日数百亿请求；FM 变体 HSTU-0.5B（推理 30 GFLOPs）与 HSTU-1B（推理 80 GFLOPs）分别用 160 与 512 张 H100 训练；"0.5B/1B 只算 dense 参数，加上 sparse embedding 是万亿参数量级"；内部 NE 改善 0.05% 即显著 — [arXiv 2508.02929](https://arxiv.org/abs/2508.02929)（论文，2025-08，A）。
- ExFM（2025-02，v7 2025-07）：广告排序的"外部大基础模型"，FM 参数 0.8T–3.2T，算力 30×–1800×（1X = 6000 万训练 FLOPs），下游 VM（真正服务的模型）仅 30×；FM 给各阶段 VM 带来 0.11%–0.25% 的额外 NE 增益；内部数据集 740 亿样本；内部 0.02% NE 视为显著；CTR 标签延迟 5–90 分钟、CVR 1 天 — [arXiv 2502.17494](https://arxiv.org/abs/2502.17494)（论文，A）。
- LLaTTE（2026-01，AI at Meta）：广告序列建模"遵循类 LLM 的可预测幂律"；语义/内容特征会"弯曲"scaling 曲线（是继续 scaling 的前提）；宽度需≥256 深度扩展才有效；128 张 H100 上训 30B 样本/229K steps；上游模型 92 GFLOPs/样本，序列 FLOPs 是在线主排序模型的 >45 倍，上游→下游迁移率≈50%；两阶段部署在旗舰广告排序上 NE −0.25%，对应 Facebook Feed/Reels **转化 +4.3%，"年收入影响数亿美元量级"**，P99 延迟无可测变化 — [arXiv 2601.20083](https://arxiv.org/abs/2601.20083)（论文，A）。
- ULTRA-HSTU "Bending the Scaling Law Curve"（2026-02，Meta Recommendation Systems）：把 scaling efficiency 定义为"效果–算力拟合直线的斜率"；半局部稀疏注意力 + FP8 GEMM + INT4 embedding 量化 + 定制 kernel，相对原始 HSTU **训练 scaling 效率 5.3×、推理 21.4×**；系统优化带来训练吞吐 +70%、推理 +50%；生产部署 18 层注意力、16k 用户序列，训练用"数百张 H100"，线上消费/互动指标 +4%–8%，topline +0.217% — [arXiv 2602.16986](https://arxiv.org/abs/2602.16986)（论文，A）。
- Kunlun（2026-02，Meta）：指出现有模型"仅 3–15% MFU"，统一架构后在 **B200 上 MFU 从 17% 提升到 37%**，相对 SOTA 2× scaling 效率；在 Meta Ads 主要模型上 topline +1.2%；内部数据 700 亿+样本；对比在 6/60/180 GFLOPs 三档：相对 Wukong 的 NE 增益 0.31%/0.66%/0.79%，差距随算力扩大；滑窗注意力 QPS +31.1%、FLOPs −29.5% — [arXiv 2602.10016](https://arxiv.org/abs/2602.10016)（论文，A）。
- WHALE（2026-07，Meta）：Wukong（非序列特征交叉）+ HSTU（序列）逐层融合；B200 上实验，800 亿训练样本；序列长度 3k→6k→10k→15k 持续有 NE 增益，深度到 8 层、宽度 64→512 仍有增益；线上 14 天 A/B 正向，代价是 5% 推理 QPS 回退；训练吞吐优化 +30%、推理 +22%，AOTInductor 省 1–5 ms、QPS +15% — [arXiv 2607.17017](https://arxiv.org/abs/2607.17017)（论文，A）。
- Meta Lattice（2025-12，KDD 2026）：多域多目标模型空间重设计（跨域共享、数据整合、蒸馏、FP8），部署后 **收入 topline +10%、满意度 +11.5%、转化 +6%，同时节省 20% 容量**；在 1024 GPU 上验证硬件效率；teacher:student GPU 比≈1:100；把选定模型扩到 30–40 GFLOPs/样本 — [arXiv 2512.09200](https://arxiv.org/abs/2512.09200)（论文，A）。
- GEM（Generative Ads Recommendation Model，Meta 工程博客 2025-11-10）：称为"业界最大的推荐基础模型"、LLM 规模、在数千 GPU 上训练，Instagram 广告转化 +5% — [engineering.fb.com](https://engineering.fb.com/2025/11/10/ml-applications/metas-generative-ads-model-gem-the-central-brain-accelerating-ads-recommendation-ai-innovation/)（官方博客，B：搜索摘要，未读全文）。Meta 2025Q4 财报电话会（2026-01-28）：Q4 把训练 GEM 的 GPU 数量翻倍，2026 年将"有意义地"继续扩大集群；GEM + 新序列学习架构在 Q4 带来 Facebook 广告点击 +3.5%、Instagram 转化 >1% — [Fool 转录](https://www.fool.com/earnings/call-transcripts/2026/01/28/meta-meta-q4-2025-earnings-call-transcript/)（B，搜索摘要）。

**字节跳动 / TikTok（公开论文）**
- RankMixer（CIKM 2025）：抖音 Feed 排序 dense 部分 16M → 1B（≈70×），**MFU 4.5% → 45%**，推理延迟 14.5 ms → 14.3 ms 不变；活跃天数 +0.3%、停留时长 +1.08%；低活用户活跃天数 +1.74%；offline AUC +0.7%；承认"扩到 1 亿参数以内收益有限"；DTSI-MoE（稠密训练/稀疏推理）在 AUC 几乎无损下把 FLOPs/footprint 降 >8×、吞吐 +50% — [arXiv 2507.15551](https://arxiv.org/abs/2507.15551)（论文，A）。
- TokenMixer-Large（2026-02，ByteDance AML）：RankMixer 后继，线上部署 **7B（广告）/4B（电商）/2B（直播）**，离线验证到 15B/7B/4B；"纯模型"去掉碎片算子后广告骨干 MFU 60%；FP8 E4M3 推理 PTQ 带来 1.7× 加速且无精度损失；4 路 token 并行（全局 batch 320）吞吐 +29.2%；关键发现：**1B 以上任何单一维度（宽/深/scaling factor）都会遇瓶颈，需要宽深平衡扩展；更大模型需要更多数据收敛——30M→90M 只需 14 天样本，500M→2B 需要 60 天样本**；线上电商订单 +1.66%、人均预览支付 GMV +2.98%，广告 ADSS +2.0%，直播收入 +1.4% — [arXiv 2602.06563](https://arxiv.org/abs/2602.06563)（论文，A）。
- MixFormer（2026-02）：把序列建模与特征交叉合进单一 Transformer 以"共同 scaling"；user–item 解耦减少约 36% FLOPs、服务加速 >30%；序列长度扫描 {512, 2048, 8192, 10000}；抖音/抖音极速版 A/B 正向，基线是 >1B 参数的 STCA→RankMixer 堆叠 — [arXiv 2602.14110](https://arxiv.org/abs/2602.14110)（论文，A）。
- Zenith（2026-01，TikTok Live）：Prime Token + Token Fusion/Boost；DCN-V2 扩到 100M 有中等收益、继续扩展无效；Zenith 在各规模比 DCN-V2/Wukong/DHEN 低 0.42%–0.63% LogLoss；Zenith++ 用 tokenwise sparse MoE（920M 激活 / 1822M 总参）；TikTok Live 线上 CTR AUC +1.05%、Logloss −1.10%，Quality Watch Session/User +9.93%、Duration/User +8.11% — [arXiv 2601.21285](https://arxiv.org/abs/2601.21285)（论文，A）。
- LONGER（RecSys 2025）：端到端长序列（L≥2000）；AUC 随参数呈幂律（R²=0.987）、随 FLOPs 幂律（R²=0.967）；在字节广告与电商"数十个场景全量部署"；48×A100 实验集群，5.2B 样本/130 天 — [arXiv 2505.04421](https://arxiv.org/abs/2505.04421)（论文，A）。
- STCA "Make It Long, Keep It Fast"（2025-11）：抖音端到端 **10k 序列**全量上线；"随历史长度与模型容量扩展出现可预测、单调的收益，镜像 LLM scaling law"；L=10k 时 STCA 序列 FLOPs 1.06→21.06 GFLOPs（19.9×）；训练 ~2k 外推到 10k；线上一个月 A/B 正向（finish AUC +0.17%）— [arXiv 2511.06077](https://arxiv.org/abs/2511.06077)（论文，A）。
- OneTrans（2025-10）：单一 Transformer 统一特征交叉+序列；线上人均 GMV +5.68%；16×H100 数据并行训练 — [arXiv 2510.26104](https://arxiv.org/abs/2510.26104)（论文，A）。
- Rec-Distill（2026-05，ByteDance AML）：工业蒸馏流水线，**teacher 扩到 24B dense 参数、20K 行为序列**（TokenMixer-Large + LONGER）；训练数据约 70 亿样本/天；参数 scaling 的增益可迁移 73%，序列 scaling 迁移 61%；teacher 固定 7B 时 student 从 1B 缩到 376M/184M 迁移率继续下降；线上订单 +0.68%、GMV +0.62%、礼物收入 +0.78% — [arXiv 2605.29755](https://arxiv.org/abs/2605.29755)（论文，A）。
- TM20K（2026-08）：电商广告序列扩到 20K，ADSS +1.036%，服务延迟仅 +5.6%；对照：朴素把 5K 扩到 20K 训练时间 3.5×、显存 +49 GB、延迟 6.3×；最近 10% token 贡献约一半注意力 — [arXiv 2608.07055](https://arxiv.org/abs/2608.07055)（论文，A）。
- HLLM（2024-09，背景）：Item/User 双 LLM 各 7B 仍有增益；对照 SASRec-1B/HSTU-1B 等 ID 模型"充分收敛后增参收益极小" — [arXiv 2409.12740](https://arxiv.org/abs/2409.12740)（论文，A）。

**快手**
- OneRec Technical Report（2025-06）：端到端生成式；模型系列 0.015B/0.121B/0.935B(MoE)/2.633B(MoE)；0.935B 约 1000 亿样本收敛（3000 亿 token）；loss 在前约 100 亿样本内快速下降、1000 亿后仍缓慢下降；快手主站+极速版承接 25% QPS，App 停留时长 +0.54%/+1.24%，LT7 +0.05%/+0.08%（平台上 0.1% 停留时长、0.01% LT7 即显著）；本地生活场景 GMV +21.01%、订单 +17.89% 后接管 100% QPS — [arXiv 2506.13695](https://arxiv.org/abs/2506.13695)（论文，A）。
- OneRec-V2（2025-08）：encoder 占 97.66% FLOPs 而 decoder 仅 2.34%；Lazy Decoder-Only 减少 94% 计算、90% 实际训练资源，同算力下参数 16×（0.5B→8B）；0.1B→8B 收敛 loss 3.57→3.19，其中 0.1B→1B 降 0.3，**4B 比 2B 仅再降 0.03（"2B 以上 scaling 仍具挑战"）**，4B-MoE（0.5B 激活）loss 3.22；线上用 1B、序列长度≈3000；4 亿 DAU；停留时长 +0.467%/+0.741% — [arXiv 2508.20900](https://arxiv.org/abs/2508.20900)（论文，A）。
- UniMixer（2026-04，快手）：统一 attention/TokenMixer/FM 三类 scaling 模块；拟合 ΔAUC = 0.002718·Params^0.116（RankMixer）、0.003032·Params^0.132（UniMixer）、0.003767·Params^0.142（UniMixer-Lite），深度扩展优于宽度；40 GPU 混合分布式训练，0.7B 样本 — [arXiv 2604.00590](https://arxiv.org/abs/2604.00590)（论文，A）。
- GR4AD（2026-02，快手广告）：生成式广告推荐全量上线（4 亿用户），相对 DLRM 栈 **广告收入最高 +4.2%**，"模型 scaling 与推理时 scaling 都带来一致增益"；中小广告主投放 +17.5% — [arXiv 2602.22732](https://arxiv.org/abs/2602.22732)（论文，A）。

**阿里 / 腾讯 / 美团 / Pinterest / Google**
- LUM（阿里，2025-02）：生成式预训练→判别式服务的三步范式，扩到 7B 仍有提升；对比端到端 GR（HSTU）要在 24 小时内完成训练"需要 12×–98× 的 GPU"；Group Query 推理加速 78% — [arXiv 2502.08309](https://arxiv.org/abs/2502.08309)（论文，A）。搜索摘要称淘宝赞助搜索 CTR +2.9%、RPM +1.2%（C，未在全文核对）。
- GPSD（阿里，KDD 2025）：判别式 CTR 大模型"越大越过拟合"，用生成式预训练初始化 + 稀疏参数冻结后，dense 13K→0.3B 遵循幂律；5B 样本 CTR-XL 数据集 — [ACM DOI 10.1145/3711896.3737117](https://dl.acm.org/doi/10.1145/3711896.3737117)（论文，A）。
- EST（阿里淘天，2026-02）：全统一 token 序列建模，"稳定高效的幂律 scaling"；淘宝展示广告 RPM +3.27%、CTR +1.22% — [arXiv 2602.10811](https://arxiv.org/abs/2602.10811)（论文，A）。
- RankUp（腾讯广告，2026-04）：每场景模型 10M→100M（一个量级），batch 300 ≈ 70 GFLOPs，MFU 23%；视频号/公众号/朋友圈 GMV +3.41%/+4.81%/+2.21%（20% 流量 14 天）— [arXiv 2604.17878](https://arxiv.org/abs/2604.17878)（论文，A）。
- GPR（腾讯视频号广告，2025-11）：one-model 生成式广告；dense 0.02B–2B scaling，sparse 约 80B；首次全量 GMV +2.11%，后续 HEPO 等迭代累计再 +0.7%/+0.58%/+0.58% — [arXiv 2511.10138](https://arxiv.org/abs/2511.10138)（论文，A）。
- MTGR（美团，2025-05）：HSTU 架构但保留交叉特征（"放弃交叉特征的生成式方案，scaling 也补不回来"）；单样本前向 **65× FLOPs**，训练成本与 DLRM 持平、推理成本 −12%；订单 +1.22%、CTR +1.31%；效果–算力呈幂律 — [arXiv 2505.18654](https://arxiv.org/abs/2505.18654)（论文，A）。
- PinFM（Pinterest，2025-07）：20B+ 参数用户序列基础模型，序列上限 16,000，两年历史；transformer 参数不到总参数 0.2%（其余为 embedding）— [arXiv 2507.12704](https://arxiv.org/abs/2507.12704)（论文，A）。
- PLUM（Google/YouTube，2025-10）：Semantic ID + 预训练 LM 做生成式召回；LEM（大 embedding 模型）的神经网络仅占 0.4% 参数；PLUM dense 参数 100× 但因收敛快训练总成本相当；MoE 从 110M→370M→900M 激活参数（4.2B 总）持续改善；loss 与 iso-FLOPs 呈幂律；YouTube 多核心 surface 生产部署 — [arXiv 2510.07784](https://arxiv.org/abs/2510.07784)（论文，A）。搜索摘要：Shorts Panel CTR +4.96%（[tullie.ai 解读](https://tullie.ai/blog/youtube-semantic-ids-ctr-lift)，C）。

### Inferences
- "持续上涨"的证据集中在三类：(a) 用户序列长度（Meta 4K→64K 仍有 >5% NE 累计增益；字节 10k/20K；WHALE 15k）；(b) 上游大 FM + 下游小模型的两段式（ExFM 3.2T、LLaTTE 45×、HyperCast、Rec-Distill 24B）；(c) 生成式架构的训练 loss（OneRec-V2 到 8B、PLUM 到 4.2B）。"很快饱和"的证据集中在：在线服务的 dense 排序模型 1B–2B 以上、老架构（DCN-V2 100M、Wukong 以外的基线 31 GFLOP/example）、以及 ID-only 的序列模型。
- 各家报告的 scaling 指数很小（UniMixer 拟合指数 0.12–0.14），意味着 10× 参数只换约 1.3–1.4× 的 ΔAUC 增量；这解释了为何所有团队把重心放在"每 FLOP 的效果"（scaling efficiency）而不是裸参数量。
- 对 TikTok 工程师的直接含义：字节公开路线是 RankMixer→TokenMixer-Large（线上 7B）+ LONGER/STCA/TM20K（10k–20K 序列）+ Rec-Distill（24B teacher 蒸馏），与 Meta 的 Foundation–Expert 思路同构。

### Gaps
- Wukong "每 4× 算力 0.1% LogLoss" 来自二手摘要，未在全文核对具体数字。
- HSTU 2024 论文"判别式模型约 2000 亿参数停滞"的说法来自搜索摘要，未核实原文措辞。
- GEM 博客正文（架构、MFU 提升倍数、并行策略）无法读取；Meta 财报原话也仅有转录摘要。
- 未找到腾讯广告排序整体 scaling law 的系统性论文（RankUp/GPR 是单模型报告）；未找到 Netflix、LinkedIn（360Brew）、小红书的 2025–2026 scaling 数据（搜索未执行/被阻断）。

---

## 2. 训练基础设施：集群、框架、并行、在线学习与样本流水线

### Takeaway
公开的训练规模从"几十张 A100/H100 的实验集群"到"数百至数千张 H100/B200 的生产集群"（Meta HyperCast 512×H100、LLaTTE 128×H100、ULTRA-HSTU 数百 H100、Lattice 1024 GPU、GEM"数千 GPU"；快手 OneRec 720 张旗舰 GPU；字节整体"数万 GPU + 千万 CPU 核 + 7 EB 数据"），MFU 从 4–11% 提升到 23–60%；核心手段是 embedding 全 GPU 化（SKAI/Primus/DynamicEmb/TorchRec 2D 并行）、请求级/用户级样本压缩、混合精度 FP8 和**把样本流水线/特征存储当作一等公民**（Meta 发现超长序列下数据基础设施开销会超过 GPU 训练开销）。

### Cited Findings

**Meta**
- HyperCast 训练：HSTU-0.5B 用 160 张 H100，HSTU-1B 用 512 张 H100；FM 与 expert 的流式训练作业彼此独立；数据到 trainer 平均延迟约 30 分钟，模型新鲜度分钟级 — [arXiv 2508.02929](https://arxiv.org/abs/2508.02929)（A）。
- Lattice 训练栈：TorchRec 做 embedding 分片 + FSDP 同步 dense 参数 + DDP 处理小参数；FP8/BF16/FP32 混合训练、FP8 推理；FBGEMM 的 tensor-wise/row-wise 缩放；1024 GPU 上验证硬件效率 — [arXiv 2512.09200](https://arxiv.org/abs/2512.09200)（A）。
- ULTRA-HSTU：BF16 为主、GEMM 走 FP8、INT4 embedding 量化减少推理通信；定制 FlashAttention-V3 风格 SLA kernel 同时适配 **NVIDIA H100 与 AMD MI300**（两平台均比 FlashAttention-V2 快 2×）；每层 HBM 占用 7 GB→2.3 GB（d=512、batch 256、3k 序列、BF16）；全 jagged tensor 训练；训练序列经 LBSL 约 4,400、推理 16,384 — [arXiv 2602.16986](https://arxiv.org/abs/2602.16986)（A）。
- Kunlun：NVIDIA H100/B200/GB200 上训练，B200 上 MFU 17%→37%；移除 GDPA 会把 MFU 从 37.0% 降到 34.0% 并损失 8% QPS — [arXiv 2602.10016](https://arxiv.org/abs/2602.10016)（A）。
- **Versioned Late Materialization（2026-04，Meta）—— 样本流水线/特征存储瓶颈的直接证据**：工业界为保证 Online-to-Offline 一致性而把用户历史（UIH）物理预物化进每条样本（"Fat Row"），同一用户一天 K 个请求就复制 K 份；定义"Fat Row Wall"= 数据支撑服务资源/GPU 训练功耗之比超过 0.75，**Meta 生产环境在约 4K 序列处撞墙**，并指出超长序列会使"数据基础设施用量超过 GPU 训练部署"；改为带版本的训练时延迟物化（不可变 UIH 存储 + 多租户序列投影下推 + 解耦的数据预处理 DPP + 流水线预取 + 数据亲和分片）后：主训练数据写带宽 −46.2%、读带宽 −47.7% 到 −70.3%，不可变存储每单位主机资源读吞吐 3.4×，批训练序列查找带宽再降约 60%，Model B/C 的 per-batch 数据加载延迟 −26.4%/−36.2%（Model A +9.7% 由弹性 DPP 吸收）；效果上 Platform A 从 4K 扩到 64K 再得 1.2% NE（累计 >5%），Platform B 4K→10K +0.65%（"1% NE 即算成功"）；被描述为 HSTU 与万亿参数序列模型的基础设施 — [arXiv 2604.24806](https://arxiv.org/abs/2604.24806)（论文，A）。
- DV365（Instagram，KDD 2025）：端到端序列被"特征存储、抽取"卡在约 2k，注意力模型只能处理约 500；改走离线用户 embedding（最长 70,000、平均 40,000 条历史），单一上游模型产出 30 亿用户 embedding 供 15 个生产模型使用，发布时 4-bit 量化；关键模型使用在线训练保证新鲜度 — [arXiv 2506.00450](https://arxiv.org/abs/2506.00450)（论文，A）。
- TorchRec 官方 README：提供 data-parallel/table-wise/row-wise/table-wise-row-wise/column-wise 等分片、自动 planner、流水线化训练（dataloader→input_dist→forward/backward 重叠）、FBGEMM kernel、量化训练/推理与 C++ 推理导出 — [GitHub meta-pytorch/torchrec](https://github.com/meta-pytorch/torchrec)（官方仓库，A）。PyTorch 博客"2D sparse parallelism"称通过 DMPCollection API 把推荐训练扩到数千 GPU — [pytorch.org](https://pytorch.org/blog/scaling-recommendation-2d-sparse-parallelism/)（B，搜索摘要，未读全文）。
- Meta 2025Q4 财报电话会：Q4 训练 GEM 的 GPU 数翻倍，2026 年继续扩大 — [Fool 转录](https://www.fool.com/earnings/call-transcripts/2026/01/28/meta-meta-q4-2025-earnings-call-transcript/)（B，搜索摘要）。

**字节跳动 / TikTok**
- Primus（USENIX ATC 2025）：字节统一 DLRM 训练系统；"截至 2025 年，字节 DLRM 训练使用超过 1000 万 CPU 虚拟核、数万 GPU、7 EB 训练数据"，服务抖音/西瓜/头条 — [usenix.org PDF](https://www.usenix.org/system/files/atc25-shan-jixi.pdf)（论文，B：搜索摘要，全文被阻断）。
- LONGER：训练框架是"面向大规模稀疏模型的全同步系统，dense 与 sparse 参数统一在 GPU 上更新"；BF16/FP16 混合精度 + 激活重计算带来吞吐 +18%、训练时间 −16%、显存 −18%（dense 部分最高 −28%）— [arXiv 2505.04421](https://arxiv.org/abs/2505.04421)（A）。
- STCA 的 Request Level Batching：同一用户多个 target 共享用户侧编码，单 GPU 训练吞吐 2.2×（叠加优化 kernel 后 5.1×），同显存下最大可训序列长度≈8×，**参数服务器 CPU 使用 −50%** — [arXiv 2511.06077](https://arxiv.org/abs/2511.06077)（A）。
- TokenMixer-Large：实验在 64 GPU（电商）/256 GPU（Feed-Ads）的混合分布式框架上；token 并行（4 路）吞吐 +29.2%；MoEPermute/GroupedFFN 算子优化 — [arXiv 2602.06563](https://arxiv.org/abs/2602.06563)（A）。
- Rec-Distill：广告场景训练数据约 70 亿样本/天 — [arXiv 2605.29755](https://arxiv.org/abs/2605.29755)（A）。
- LMN（Large Memory Network，2025-02）：Memory Parameter Server 把记忆值分片存放在多 GPU HBM 上，已在抖音电商全量 — [arXiv 2502.05558](https://arxiv.org/abs/2502.05558)（B，搜索摘要）。
- Streaming VQ 召回（KDD 2025）：抖音十亿级物料下 HNSW 建索引需 1.5–2 小时、DR 的 M-step 1 小时，流式 VQ 索引随训练实时更新；为让复杂 VQ 模型 ROI 转正"花了近半年优化 GPU 效率（算子放置、fp16 等）"；HNSW/DR/VQ 双塔/VQ 复杂版成本分别为 22K/20K/17K/30K 核（GPU 折算为 CPU 核）— [GitHub 镜像 PDF](https://github.com/guyulongcs/Deep-Learning-for-Search-Recommendation-Advertisements/blob/master/02_Matching/2025%20%28Bytedance%29%20%28KDD%29%20%5BVQ%5D%20Real-time%20Indexing%20for%20Large-scale%20Recommendation%20by%20Streaming%20Vector%20Quantization%20Retriever.pdf)（论文，A）。
- Monolith（2022，背景）：字节开源的无碰撞 embedding 表 + 在线学习训练框架 — [GitHub bytedance/monolith](https://github.com/bytedance/monolith)（官方仓库，A；2022 年背景）。

**快手**
- OneRec 训练集群：**90 台服务器 × 8 张"旗舰 GPU" + 2 CPU**（=720 GPU，型号未公开）；embedding 用快手 **SKAI** GPU 参数服务器（跨 GPU 统一 embedding 表、GPU 缓存、预取流水线）；并行策略 = 数据并行 + ZeRO-1 + 梯度累积（dense 参数可放进单卡）；BF16 部分 MLP、注意力编译优化；训练 MFU 从 4.6% 提升到 23.7%；日处理约 180 亿样本（540 亿 token）；流式曝光数据在线训练 — [arXiv 2506.13695](https://arxiv.org/abs/2506.13695)（A）。腾讯云开发者文章称 SKAI 解决"单样本需训练 1000 万以上 embedding 参数"的问题并实现 embedding 训练全流程在 GPU 完成 — [cloud.tencent.com](https://cloud.tencent.com/developer/article/2594097)（C，二手解读）。
- OneRec-V2：Lazy decoder 省 90% 实际训练资源；RL 用流式曝光数据在线训练 — [arXiv 2508.20900](https://arxiv.org/abs/2508.20900)（A）。
- GR4AD：闭环系统（实时服务、实时索引、在线学习模块持续 VSL/RL 更新、奖励系统）— [arXiv 2602.22732](https://arxiv.org/abs/2602.22732)（A）。

**阿里 / 美团 / 腾讯 / Pinterest / Google / NVIDIA**
- MTGR 训练：DLRM 每 GPU batch 2400 用 8×A100，MTGR batch 96 用 16×A100；用户级压缩（多条样本合一）+ 框架优化后训练吞吐 1.6×–2.4×，>100 GPU 扩展良好；65× FLOPs 下训练成本基本不变 — [arXiv 2505.18654](https://arxiv.org/abs/2505.18654)（A）。
- LUM：128 GPU 上 0.5B–14B 模型；要求 24 小时内完成持续训练，端到端 GR 需 12×–98× GPU 才能匹配 LUM 吞吐 — [arXiv 2502.08309](https://arxiv.org/abs/2502.08309)（A）。
- EST：在 32 个 **PPU（阿里自研 GPU 架构）** 上训练、128 PPU 做 scaling 实验，每 PPU batch 1000 — [arXiv 2602.10811](https://arxiv.org/abs/2602.10811)（A）。TBGRecall：部署于 **PPU 810E，算力约为 NVIDIA A100 的 60%**；训练"10B 级稀疏 + 十亿级 dense 参数、万亿级样本"，数据准备卸载后 GPU 利用率 >90% — [arXiv 2508.11977](https://arxiv.org/abs/2508.11977)（A）。
- 腾讯 GPU 检索：在线实时训练 batch 4000，FTRL 稀疏 + Adam dense — [arXiv 2511.22460](https://arxiv.org/abs/2511.22460)（A）。
- Pinterest：基础排序模型约 99% 参数在 embedding 表；初次多机训练第二台机器反而慢 5×，启用 AWS EFA 后 2/4 节点仅 1.13×/1.21×（3× GPU 换 21% 吞吐）——后续优化到"近线性" — [Pinterest 工程博客](https://medium.com/pinterest-engineering/achieving-near-linear-training-scalability-for-pinterests-foundation-models-14d4f59fe6f6)（B，搜索摘要）。PinFM：DCAT 去重交叉注意力使服务吞吐 +600%、训练 +200%；TorchRec 分片 embedding — [arXiv 2507.12704](https://arxiv.org/abs/2507.12704)（A）。
- Google PLUM：scaling 实验用 **1024 片 TPU v6e（每片 32 GB HBM，4 个 trainer × 256 TPU）**，iso-FLOPs 1e22；900M MoE 每天只训约 2.5 亿样本（LEM 每天数十亿），训练 FLOPs <0.55× LEM；生产用恒定学习率以支持持续训练 — [arXiv 2510.07784](https://arxiv.org/abs/2510.07784)（A）。
- NVIDIA recsys-examples HSTU 端到端训练 benchmark（2×8 H100-SXM5，batch 32/GPU，4096 序列）：逐步启用负载均衡 shuffler、CUTLASS attention、DynamicEmb 缓存、hash-roundrobin 分片、预取流水线后，**平均吞吐 75.6 → 310.6 TFLOPS/GPU（峰值 338.1）**；按 989 TFLOPS BF16 峰值折算约 7.6% → 31.4% MFU（折算为本笔记推导）；NCCL 暴露时间仅约 2–3% — [GitHub E2E_BENCHMARK.md](https://github.com/NVIDIA/recsys-examples/blob/main/examples/hstu/training/benchmark/E2E_BENCHMARK.md)（官方仓库，A）。

### Inferences
- 三条共性工程路径：(1) sparse 全 GPU 化（SKAI、Primus、DynamicEmb、TorchRec/HugeCTR 系）；(2) 样本层压缩（MTGR 用户级压缩、STCA RLB、LLaTTE/HyperCast 的离线用户 embedding），本质是把"每请求重复的用户侧计算与存储"摊薄；(3) 低精度（BF16 训练 + FP8 GEMM + INT4/INT8 embedding）。
- Meta 的 Versioned Late Materialization 是本轮调研中**唯一量化了"样本流水线成为瓶颈"的一手证据**：4K 序列即撞"Fat Row Wall"，超长序列的瓶颈不在 GPU 而在训练数据的写/读带宽与预处理；这对 TikTok 这类已经 10k–20K 序列的系统是最直接的对照。
- 在线学习在 GPU 时代的公开形态是"流式 + 分钟级数据延迟（Meta 30 分钟）+ 独立的 FM/expert 训练作业"，以及快手/腾讯广告的实时 RL/在线学习闭环；没有公司公开声称放弃在线学习。

### Gaps
- 未拿到 Primus 论文全文（吞吐、PS/GPU 混合架构细节）；字节的 GPU 总量只有"数万"的数量级描述。
- 快手"旗舰 GPU"具体型号、720 卡集群的 MFU 口径（是否含 embedding 算力）未公开。
- Meta 2D sparse parallelism 博客、GEM 博客的具体并行与 MFU 数字无法读取。
- 未找到各家公开的**端到端样本吞吐（samples/s）与 feature store 读带宽**的绝对数值（Meta 只给相对百分比）。

---

## 3. 推理与服务：GPU 落地、延迟预算、KV cache、量化/MoE、生成式 beam search

### Takeaway
2025–2026 年的公开系统把排序/召回推理几乎全部放到 GPU（Meta H100/B200、快手 L20、字节 FP8 GPU、腾讯 T4、阿里 PPU），用三类手段守住延迟预算：**用户侧计算复用**（跨候选/跨请求 KV cache：LONGER 把吞吐退化从 −40% 压到 −6.8%、NVIDIA HSTU KV 命中 2.2–5.9×）、**低精度**（FP16/FP8 推理 1.7–2×、INT4/INT8 embedding）、**稀疏/两段式**（DTSI-MoE、Foundation–Expert、蒸馏）；生成式推荐的 beam search 成本靠 LazyAR（约 2× QPS）、动态 beam（512-512-512→128-256-512）、多 token 生成（约 10× 延迟下降）来控制。

### Cited Findings
- 快手 OneRec 推理：**NVIDIA L20 GPU，每台 4 GPU + 2 CPU，PCIe 互连**，部署在快手 UniPredict 预测平台；Float16；对 MoE/Attention/BeamSearch 等核心算子 kernel 融合；配合 batching 与 MPS 吞吐 5×，推理 MFU 11.2% → 28.8%（结论章写 28.6%，原文前后不一致）；beam size 512（二手文章）；传统级联系统 >50% 服务资源用于通信与存储而非计算；快手整体 QPS >400k、延迟要求 <500 ms；OPEX 为传统流水线的 10.6% — [arXiv 2506.13695](https://arxiv.org/abs/2506.13695)（A）；beam 512 来自 [腾讯云文章](https://cloud.tencent.com/developer/article/2594097)（C）。
- 快手 GR4AD 推理：**<100 ms 延迟、每张 L20 500+ QPS**；LazyAR（9 层 decoder、前 6 层跨 beam 共享）性能微降但 QPS 近 2×；Dynamic Beam Serving：逐层 beam 由 512-512-512 改为 128-256-512 不损收入，低峰期 beam +60% 提收入；Beam-Shared KV caching；FP32→FP8；SID 索引秒级更新（embedding 索引重建通常分钟级）；注：GR 模型"通常跑在更强 GPU 上且利用率更高"，与 DLRM 多模型共服务的 QPS 不可直接比 — [arXiv 2602.22732](https://arxiv.org/abs/2602.22732)（A）。
- 字节 RankMixer 线上部署（表 6）：基线 15.8M 参数、107 GFLOPs、MFU 4.47%、fp32、14.5 ms；RankMixer-1B 1.1B 参数、2106 GFLOPs、**MFU 44.57%、fp16、14.3 ms**；70× 参数仅 20.7× FLOPs（FLOPs/参数 −3.6×）+ MFU 10× + fp16 2× 抵消；DTSI-MoE 吞吐 +50% — [arXiv 2507.15551](https://arxiv.org/abs/2507.15551)（A）。TokenMixer-Large：FP8 E4M3 推理 PTQ 1.7× 加速、训练保持 BF16；"稀疏训练、稀疏推理"的 per-token MoE — [arXiv 2602.06563](https://arxiv.org/abs/2602.06563)（A）。
- 字节 LONGER KV cache 服务：把用户行为 token 与候选相关计算解耦，多候选打分时吞吐退化从 −40% 降到 −6.8% — [arXiv 2505.04421](https://arxiv.org/abs/2505.04421)（A）。OneTrans：跨候选、跨请求 KV cache 把会话复杂度从 O(C) 降到 O(1) — [arXiv 2510.26104](https://arxiv.org/abs/2510.26104)（A）。MixFormer：user–item 解耦服务加速 >30% — [arXiv 2602.14110](https://arxiv.org/abs/2602.14110)（A）。TM20K：20K 序列下服务延迟仅 +5.6% — [arXiv 2608.07055](https://arxiv.org/abs/2608.07055)（A）。
- Meta 推理：HyperCast 三层推理服务（在线 FM 为数百候选出 embedding；离线 FM logging 只需在线 FM 1/3 主机；在线 expert），端到端延迟与 CPU 持平 — [arXiv 2508.02929](https://arxiv.org/abs/2508.02929)（A）。LLaTTE：上游用户模型不按请求算，而由高价值事件（主要是转化）触发，在专用 H100 集群上做高吞吐推理，写入 feature store，下游排序读 dense 特征；"Meta 最大的用户模型部署"；P99 无可测变化 — [arXiv 2601.20083](https://arxiv.org/abs/2601.20083)（A）。WHALE：torch.compile + AOTInductor 省 1–5 ms、QPS +15% — [arXiv 2607.17017](https://arxiv.org/abs/2607.17017)（A）。ULTRA-HSTU：INT4 embedding 量化减少推理通信；推理 scaling 效率 21.4× — [arXiv 2602.16986](https://arxiv.org/abs/2602.16986)（A）。
- NVIDIA 官方 HSTU 推理栈（recsys-examples，截至 v26.08/2026-09）：paged GPU KV cache + 异步 host 卸载（FlexKV 多层：GPU/CPU/SSD）+ CUDA graph + Triton + AOTInductor C++；L20 上 batch 1–8 KV cache+CUDA graph 整体 1.3–2.6×，4096 token 中 3968 已缓存时 HSTU block 加速 3–20×（无候选）/3–8×（256 候选），B200（Blackwell CuteDSL kernel）3.3–7.7×；AOTI C++ 相对 Python 运行时 1.44–1.90×（L20 6.03→3.71 ms/请求）；Triton AOTI 后端 KV 命中 3 层/8 层模型 2.20×/2.38×，batch 8 时 4.47×；HSTU attention 支持 FP8 — [GitHub NVIDIA/recsys-examples](https://github.com/NVIDIA/recsys-examples)（官方仓库，A）。NVIDIA 博客称 RTX PRO 6000 上 Dynamo-Triton + AOTI 对 8 层 HSTU 最高 5.93× — [developer.nvidia.com](https://developer.nvidia.com/blog/deploying-an-hstu-generative-recommender-with-nvidia-dynamo-triton)（B，搜索摘要）。
- NVIDIA SID-GR 推理（生成式检索 beam search 服务）：工作负载是"长上下文 + 短解码 + 大 beam（128/256）"，与聊天 LLM 不同；vLLM 无稳定生产 beam search 路径、SGLang 大 beam 支持仍在未合并 PR；NVIDIA 用 ContextKV/BeamKV/BeamPath + 连续批处理 + CUDA graph，离线性能"一致快于 SGLang beam-search 分支" — [GitHub sid-gr-inference README](https://github.com/NVIDIA/recsys-examples/blob/main/examples/sid-gr-inference/README.md)（官方仓库，A）。
- KV cache 复用用户序列（学术/工业系统，2026）：RelayGR 预推理长期行为前缀并在多阶段流水线中跨阶段复用 per-layer KV（HBM 内接力）— [arXiv 2601.01712](https://arxiv.org/abs/2601.01712)；MTServe 用 host RAM 虚拟化 GPU KV 存储应对跨请求复用导致的存储爆炸 — [arXiv 2604.22881](https://arxiv.org/abs/2604.22881)；"When KV Meets Embeddings" 动态分配 GPU 显存给 KV 与 embedding — [arXiv 2605.04450](https://arxiv.org/abs/2605.04450)；写感知 KV 策略把 KV 放到高带宽 Flash — [arXiv 2609.07175](https://arxiv.org/abs/2609.07175)（以上均 B，搜索摘要，作者单位未核实）。
- 美团 MTGR：65× FLOPs 下推理成本 −12% — [arXiv 2505.18654](https://arxiv.org/abs/2505.18654)（A）。阿里 LUM：Group Query 推理 +78%、packing +82%，30 ms 延迟约束下评估最大序列 — [arXiv 2502.08309](https://arxiv.org/abs/2502.08309)（A）。
- 腾讯 GPU 召回：在双塔召回里实现 Wide&Deep 特征交叉，自研压缩倒排 HitMatch 算子相对 cuSPARSE QPS +590%，在 **T4** 上运行；朋友圈消耗 +0.37%、GMV +1.58% — [arXiv 2511.22460](https://arxiv.org/abs/2511.22460)（A）。
- Pinterest：PinFM 用 FBGEMM n-bit min-max PTQ，int4 把 embedding 表压到 31.25%，主机成本按比例下降，embedding IO 降低使基础设施延迟 −7%；int8 离线无损，int4 save 指标 −0.06% 但 A/B 可接受 — [arXiv 2507.12704](https://arxiv.org/abs/2507.12704)（A）。PinRec 生成式召回：每步生成 16 个 embedding 的多 token 生成比逐 token 延迟约 −10×，6 步（1 prefill + 5 decode），INT8 嵌入 — [arXiv 2504.10507](https://arxiv.org/abs/2504.10507)（A）。TransActV2：特征存储 O(L)、网络 O(NL) 是终身序列的主成本，改为端上最近邻检索并只记录 NN 特征，把日志存储从 O(L) 降到 O(1)，PinSage embedding int8 — [arXiv 2506.02267](https://arxiv.org/abs/2506.02267)（A）。Pinterest 称 GPU 服务使"100× 更大的架构在不增成本与延迟下上线"、现有 14,000 张 NVIDIA GPU、VLM 服务栈基于 Blackwell + Dynamo — [Pinterest 博客](https://medium.com/pinterest-engineering/a-decade-of-ai-platform-at-pinterest-4e3b37c0f758)、[NVIDIA 案例](https://www.nvidia.com/en-us/case-studies/pinterest/)（B，搜索摘要）。
- HugeCTR 官方 README：自 25.03 起只提供 Dockerfile 源码、用户自行构建；最近论文为 2024 EMBark；NVIDIA 的新投入集中在 recsys-examples（DynamicEmb/HSTU/SID-GR）— [GitHub NVIDIA-Merlin/HugeCTR](https://github.com/NVIDIA-Merlin/HugeCTR)（官方仓库，A）。

### Inferences
- CPU vs GPU 的公开"成本对比"几乎都以相对量给出：快手 OPEX 10.6%、美团推理 −12%、字节"70× 参数延迟不变"、Pinterest"100× 架构成本不变"、LUM"端到端 GR 需 12–98× GPU"。没有公司公开每请求的绝对美元成本。
- 生成式推荐的服务成本结构与 LLM 不同（短解码、大 beam、长上下文），现有 LLM 引擎（vLLM/SGLang）不直接适配，头部公司（快手 UniPredict、NVIDIA SID-GR、字节自研）都在做专用 beam 引擎；推理时 scaling（更大 beam）已被 GR4AD 当作"低峰期换收入"的旋钮。
- 字节的公开线上延迟锚点是排序模型约 14 ms（RankMixer），快手生成式广告 <100 ms、主站 <500 ms。

### Gaps
- 未找到 Meta MTIA 与 GPU 推理在排序模型上的直接性能/成本对比数据（ISCA'25 论文被阻断）。
- 字节 DPIFrame（CTR 推理双层并行框架，arXiv 2606.21101）与 SilverTorch（arXiv 2511.14881）只在搜索结果中出现，作者单位与数据未核实。
- OneRec beam size 512 仅来自二手文章，正文未核对；OneRec 推理 MFU 原文存在 28.8%/28.6% 两个数字。

---

## 4. 硬件与专用芯片：MTIA、TPU SparseCore、自研 GPU、AMD

### Takeaway
公开信息显示头部公司推荐推理/训练硬件正在多元化：Meta 的 MTIA 已大规模服务广告推荐并宣布 2 年内 4 代芯片（300 已用于推荐训练、450/500 面向 2027 年推理），同时在推荐模型上同时适配 NVIDIA H100/B200/GB200 与 AMD MI300；Google 以 TPU（Ironwood 第三代 SparseCore、v6e）承载推荐；阿里用自研 PPU（约 A100 60% 算力）训练与部署推荐模型；快手/腾讯在推理侧使用性价比 GPU（L20、T4）。架构设计上的共同影响是：模型被改造成"大 GEMM、少碎片算子、低精度友好"以提高任何加速器上的 MFU。

### Cited Findings
- Meta 官方（2026-03）"Expanding Meta's Custom Silicon"：MTIA 已在数据中心规模部署、主要服务广告负载，"相对供应商芯片带来巨大效率收益"；MTIA 2i 已大规模部署服务数十亿用户；两年内推出 4 代新芯片，**MTIA 300 已投产用于排序与推荐训练，400 实验室测试中，450 与 500 面向推理、分别计划 2027 年初与 2027 年晚些时候大规模部署**，六个月一代 — [about.fb.com](https://about.fb.com/news/2026/03/expanding-metas-custom-silicon-to-power-our-ai-workloads/)（官方新闻，B，搜索摘要）；[Tom's Hardware 报道](https://www.tomshardware.com/tech-industry/semiconductors/meta-reveals-four-new-mtia-chips-built-for-ai-inference)（C）。
- Meta 第二代 MTIA 论文"Model-Chip Co-Design and Productionization Experiences"（ISCA 2025）— [ACM DOI 10.1145/3695053.3731409](https://dl.acm.org/doi/10.1145/3695053.3731409)（论文，B：仅有标题，全文被阻断）。
- Meta 的 GPU 侧：Kunlun 在 H100/B200/GB200 上训练、以 B200 为基准；WHALE 全部在 B200 上实验；ULTRA-HSTU 同时为 NVIDIA H100 和 **AMD MI300** 调优 SLA kernel（"异构 GPU 架构"）— 见第 1、2 节论文（A）。
- Google：Ironwood（TPU v7）每芯片 2 个 TensorCore + 4 个 SparseCore，第三代 SparseCore 起源于 v5p、Trillium 增强，面向"数百 GB 到数 TB 的超大 embedding 表"的随机 gather/scatter — [blog.google Ironwood](https://blog.google/innovation-and-ai/infrastructure-and-cloud/google-cloud/ironwood-tpu-age-of-inference/)、[The Next Platform](https://www.nextplatform.com/2025/04/09/with-ironwood-tpu-google-pushes-the-ai-accelerator-to-the-floor/)（B/C，搜索摘要）。YouTube PLUM 的 scaling 实验在 1024 片 TPU v6e 上完成 — [arXiv 2510.07784](https://arxiv.org/abs/2510.07784)（A）。
- 阿里：EST 在 32/128 个自研 PPU 上训练；TBGRecall 在 PPU 810E 上部署，"算力约为 NVIDIA A100 的 60%" — [arXiv 2602.10811](https://arxiv.org/abs/2602.10811)、[arXiv 2508.11977](https://arxiv.org/abs/2508.11977)（A）。
- 快手：OneRec 推理用 NVIDIA L20（4 卡/机，PCIe），GR4AD 以"每 L20 500+ QPS"报告 — [arXiv 2506.13695](https://arxiv.org/abs/2506.13695)、[arXiv 2602.22732](https://arxiv.org/abs/2602.22732)（A）。腾讯 GPU 召回在 T4 上 — [arXiv 2511.22460](https://arxiv.org/abs/2511.22460)（A）。
- NVIDIA 为推荐专门维护 Blackwell（sm_100）HSTU attention、FP8 attention、GB200 MFU 热图（按 2500 TFLOPS/GB200、989 TFLOPS/H100 峰值）— [GitHub recsys-examples](https://github.com/NVIDIA/recsys-examples)（A）。

### Inferences
- 对架构设计的影响已经体现在论文里：Kunlun/TokenMixer-Large/RankMixer 都把"去掉碎片化内存受限算子、用大 GEMM"作为设计原则，Lattice 专门做了"低精度友好架构"（SwishRN、归一化）以支持 FP8；这些设计同时服务于 GPU 与自研 ASIC。
- 专用芯片（MTIA、TPU SparseCore、PPU）集中解决的是 embedding gather/scatter 与推理性价比，而非 dense 算力峰值；这与第 5 节 embedding 系统 GPU/HBM 常驻趋势一致。

### Gaps
- MTIA 300/400/450/500 的峰值算力、HBM、perf/W、与 GPU 的 TCO 对比均未公开（或被阻断）；MTIA 是否已承载 GEM 级别的大模型推理未知。
- Google 推荐在 TPU 上的 MFU/成本数据未公开；SparseCore 对比 GPU 的量化数据缺失。
- 字节/快手/腾讯是否使用自研或定制推理芯片无可靠公开信息（搜索未执行）。

---

## 5. Embedding 系统：GPU/HBM 常驻、动态哈希表、量化、Semantic ID

### Takeaway
公开方案一致从"CPU 参数服务器"转向"GPU 哈希表 + 多级（HBM/host/SSD）存储"（NVIDIA DynamicEmb、快手 SKAI、字节 LMN/Primus、TorchRec 分片），用 INT8/INT4 PTQ（PinFM 表体积 31.25%、DV365 4-bit、ULTRA-HSTU INT4）压缩；同时 Semantic ID 正在替代/补充 item ID（OneRec、GR4AD、GPR、PLUM、TIGER 系），其工程价值是解耦参数量与物料规模、秒级索引更新与冷启动，而非单纯省显存。

### Cited Findings
- NVIDIA DynamicEmb（recsys-examples）：模型并行动态 embedding 表，GPU 优化的带分数哈希表后端，同时使用 GPU HBM 与主机内存；支持 TorchRec EmbeddingBagCollection/EmbeddingCollection、admission（阻止稀有/噪声 ID 占用参数与优化器状态，2025-12 v25.11）、按 TIMESTAMP/STEP/LFU 及复合 (TIMESTAMP, LFU) 自定义评分驱逐、缓存/预取、增量 dump 与 `replay_increment()` 把训练更新同步到服务副本而不重载全量 checkpoint（2026-09 v26.08）、按 fp32/fp16/bf16 原生精度存 checkpoint；8×H100 NVSwitch 节点上有与 TorchRec 原生表的查表耗时对比 — [GitHub DynamicEmb README](https://github.com/NVIDIA/recsys-examples/blob/main/corelib/dynamicemb/README.md)（官方仓库，A）。
- 快手 SKAI：GPU 参数服务器，跨 GPU 统一 embedding 表 + GPU 缓存 + 预取流水线 — [arXiv 2506.13695](https://arxiv.org/abs/2506.13695)（A）。
- 字节 LMN：记忆参数服务器把记忆值 GPU 分片存于多 GPU HBM — [arXiv 2502.05558](https://arxiv.org/abs/2502.05558)（B，搜索摘要）。字节 Monolith（2022）无碰撞哈希 embedding 表 — [GitHub](https://github.com/bytedance/monolith)（A，背景）。
- Pinterest PinFM：item id 通过 8 个子表（各 8000 万行 × 32 维 fp16）拼成 256 维以缓解哈希碰撞，embedding 共 200 亿可训参数；int4 PTQ 后每向量 512 bit→160 bit，表体积 31.25% — [arXiv 2507.12704](https://arxiv.org/abs/2507.12704)（A）。
- Meta：ExFM 的 FM 0.8T–3.2T 参数；HyperCast 含 sparse 为万亿参数；ULTRA-HSTU 用 INT4 embedding 量化减少推理通信；DV365 用户 embedding 4-bit 发布 — 见上（A）。
- Semantic ID 工业落地：
  - 快手 OneRec：RQ-Kmeans（而非 RQ-VAE）做 3 层 8,192 码本的残差量化，码本利用率三层均为 1.0、重构更好；扩到 32,768 码本有增益；每个视频 3 个 SID — [arXiv 2506.13695](https://arxiv.org/abs/2506.13695)（A）。
  - 快手 GR4AD：UA-SID 统一广告语义 ID，减少碰撞、提高码本利用；SID 索引"秒级更新"对比 embedding 索引"分钟级重建" — [arXiv 2602.22732](https://arxiv.org/abs/2602.22732)（A）。
  - 腾讯 GPR：广告与自然内容映射到共享多级 SID 空间，RQ-KMeans+ 对比 RQ-VAE（易出现 dead code）— [arXiv 2511.10138](https://arxiv.org/abs/2511.10138)（A）。
  - Google PLUM：多分辨率码本的 SID（2048/2^(level-1)），多模态视频 embedding 量化；SID 输入"绕过 LEM 的 scaling 瓶颈" — [arXiv 2510.07784](https://arxiv.org/abs/2510.07784)（A）。
  - Meta Ads："Enhancing Embedding Representation Stability in Recommendation Systems with Semantic ID"，摘要称 A/A 预测方差下降 43% — [ResearchGate 页面](https://www.researchgate.net/publication/395337315_Enhancing_Embedding_Representation_Stability_in_Recommendation_Systems_with_Semantic_ID)（B，搜索摘要）；EmergentMind 综述称 SID 使 embedding 参数量减少 75–99%（音乐）、3× 内存（广告）— [emergentmind](https://www.emergentmind.com/topics/semantic-ids)（C）。
- 字节 Streaming VQ：流式向量量化把召回索引随训练实时更新，替代定期重建的 HNSW（1.5–2 h）— 见第 2 节（A）。

### Inferences
- "参数服务器 vs GPU HBM 常驻"的答案在 2025–2026 年公开方案里是**分层**：热 embedding 在 HBM（缓存/哈希表），全量在 host 内存甚至 SSD（FlexKV/DynamicEmb），并用 admission/eviction 控制表增长；NVIDIA 的增量 dump/replay 表明"训练到服务的 embedding 增量同步"已成标准需求（对应在线学习）。
- Semantic ID 的主要工程红利在生成式召回/排序的索引与冷启动，而 PinFM/DV365 等仍以 ID embedding + 量化为主，说明两条路线并行。

### Gaps
- 未找到 2025–2026 年各公司**embedding 表总规模（TB 级）与压缩后节省的绝对数字**（只有 PinFM 的 200 亿参数、Meta 万亿级）。
- Meta Semantic ID 稳定性论文与 EmergentMind 的百分比未在原文核对。

---

## 6. 算力经济学：用多少算力换多少收益

### Takeaway
公开的"X 倍算力换 Y% 收益"案例均来自论文而非财报：美团 65× FLOPs 换订单 +1.22%/CTR +1.31%（训练成本不变、推理 −12%）；字节 70× 参数/20.7× FLOPs 换抖音时长 +1.08%（延迟不变）；Meta 上游 45× 序列算力换转化 +4.3%（"年收入数亿美元"）、Lattice 在省 20% 容量的同时 topline +10%；快手 OneRec 以 10.6% 的 OPEX 承接 25% QPS 并提升停留时长 0.54–1.24%；Meta 财报层面只披露"GEM 训练 GPU 翻倍"。GPU 投入量级的可靠公开数字只有 Pinterest 14,000 张、字节"数万"、快手 OneRec 训练 720 张。

### Cited Findings
- 快手 OneRec：OPEX 为传统方案 10.6%（级联系统 >50% 服务资源花在通信与存储）；训练 90×8 GPU；日 180 亿样本 — [arXiv 2506.13695](https://arxiv.org/abs/2506.13695)（A）。OneRec-V2：同算力 16× 参数 — [arXiv 2508.20900](https://arxiv.org/abs/2508.20900)（A）。GR4AD：广告收入 +4.2%、每 L20 500+ QPS — [arXiv 2602.22732](https://arxiv.org/abs/2602.22732)（A）。
- 美团 MTGR：65× FLOPs/样本，训练成本持平、推理成本 −12%，订单 +1.22% — [arXiv 2505.18654](https://arxiv.org/abs/2505.18654)（A）。
- 字节 RankMixer：1B 模型（70× 参数、20.7× FLOPs）线上延迟不变，时长 +1.08%、活跃天数 +0.3% — [arXiv 2507.15551](https://arxiv.org/abs/2507.15551)（A）。TokenMixer-Large 7B 线上：广告 ADSS +2.0%、电商 GMV +2.98% — [arXiv 2602.06563](https://arxiv.org/abs/2602.06563)（A）。Rec-Distill：24B teacher 的 73%/61% 增益可迁移到 1B student — [arXiv 2605.29755](https://arxiv.org/abs/2605.29755)（A）。Streaming VQ：复杂召回模型成本 30K 核 vs 双塔 17K 核，"按 ROI 只对部分目标部署复杂版" — [KDD 2025 论文镜像](https://github.com/guyulongcs/Deep-Learning-for-Search-Recommendation-Advertisements/blob/master/02_Matching/2025%20%28Bytedance%29%20%28KDD%29%20%5BVQ%5D%20Real-time%20Indexing%20for%20Large-scale%20Recommendation%20by%20Streaming%20Vector%20Quantization%20Retriever.pdf)（A）。
- Meta：LLaTTE 上游 >45× 序列 FLOPs（92 GFLOPs/样本）换旗舰广告排序 NE −0.25% ≈ 转化 +4.3%，"年收入数亿美元量级" — [arXiv 2601.20083](https://arxiv.org/abs/2601.20083)（A）。Lattice：topline +10%、转化 +6%、容量 −20%；teacher:student GPU ≈ 1:100 — [arXiv 2512.09200](https://arxiv.org/abs/2512.09200)（A）。ExFM：30×–1800× FM（0.8T–3.2T）换各阶段 VM NE +0.11%–0.25%，且 FM 成本由多个 VM 分摊 — [arXiv 2502.17494](https://arxiv.org/abs/2502.17494)（A）。ULTRA-HSTU：数百 H100 训练的 18 层/16k 模型换 topline +0.217% 与 4–8% 消费/互动 — [arXiv 2602.16986](https://arxiv.org/abs/2602.16986)（A）。Kunlun：Ads topline +1.2% — [arXiv 2602.10016](https://arxiv.org/abs/2602.10016)（A）。Versioned Late Materialization："1% NE 即成功"，数据基础设施在 4K 序列后成本超过 GPU — [arXiv 2604.24806](https://arxiv.org/abs/2604.24806)（A）。
- Meta 财报（2025Q4）：GEM 训练 GPU 翻倍、2026 继续扩大；Zuckerberg："更大的模型有从更多算力受益的空间" — [Fool 转录](https://www.fool.com/earnings/call-transcripts/2026/01/28/meta-meta-q4-2025-earnings-call-transcript/)、[Yahoo Q3 转录](https://finance.yahoo.com/news/meta-platforms-meta-q3-2025-233942466.html)（B，搜索摘要）。
- Google PLUM：100× dense 参数但训练总成本与 LEM 相当（样本效率高、<0.55× FLOPs）— [arXiv 2510.07784](https://arxiv.org/abs/2510.07784)（A）。
- 阿里 LUM：端到端 GR 需 12–98× GPU 才能在 24 h 内完成训练 — [arXiv 2502.08309](https://arxiv.org/abs/2502.08309)（A）。
- Pinterest：14,000 张 NVIDIA GPU；推理交易成本"低于同类闭源模型 8%"（指 VLM） — [smbtech 报道](https://smbtech.au/news/pinterest-deploys-14000-nvidia-gpus-to-drive-multimodal-ai-across-its-platform/)、[NVIDIA 案例](https://www.nvidia.com/en-us/case-studies/pinterest/)（C/B，搜索摘要）。
- 字节 Primus："数万 GPU、1000 万+ CPU 虚拟核、7 EB" — [usenix](https://www.usenix.org/system/files/atc25-shan-jixi.pdf)（B）。

### Inferences
- 把"算力倍数→效果"换算成同一尺度：排序 dense 侧约每 10× FLOPs 换 0.3–1% 的核心业务指标（RankMixer、MTGR、Kunlun 的 6→180 GFLOPs 换 NE 0.31→0.79%）；序列侧 4K→16K/64K 换 >1% NE；上游 FM 的"每 FLOP 收益"更高是因为成本被多个下游模型分摊（ExFM、Lattice 1:100）。
- 各家宣称"成本不变"的前提都是 MFU 翻 5–10 倍与低精度，即**第一笔算力红利来自利用率而非扩容**；TokenMixer-Large 已到 60% MFU，意味着下一步只能真扩容——这与 Meta 财报"GEM GPU 翻倍"一致。
- 头部公司的推荐 GPU 投入没有可靠公开数字（Meta 1.3M GPU 的口径是全公司 AI），任何"推荐占比"估计都应标为未核实。

### Gaps
- 没有任何公司公开每请求/每千次请求的绝对推理成本或推荐训练的美元成本；也没有公开推荐专用 GPU 数量（Meta/字节/快手）。
- Meta 2026 年资本开支指引与推荐占比、快手财报中 OneRec 相关算力表述均未能核实（搜索配额耗尽）。
- SemiAnalysis 等行业分析关于推荐算力的内容未能获取。

---

## 7. 工程组织层面的变化："推荐 infra 对齐 LLM infra"

### Takeaway
2025–2026 年的一手论文把组织变化写进了正文：Meta 用"中心 FM + 各 surface expert"（HyperCast/GEM/ExFM/DV365）把训练算力集中到少数基础模型团队、下游以 embedding/蒸馏接入，并强调"开发者速度"；快手 OneRec 明确把端到端架构视为"团队协作机制"的重构；多家在技术栈上直接复用 LLM 组件（DeepSeek-V2/V3 的 MLA、无辅助损失负载均衡、GRPO/PPO、ZeRO、FSDP、FP8、KV cache、SGLang/vLLM 对标）。

### Cited Findings
- HyperCast："在改善线上指标的同时提高开发者速度并保持基础设施效率"；FM 与 expert 训练解耦、各自独立迭代；三层推理服务各自优化 — [arXiv 2508.02929](https://arxiv.org/abs/2508.02929)（A）。
- Meta GEM 被官方称为广告推荐 AI 创新的"central brain"，并通过 post-training/知识迁移服务其他广告模型 — [engineering.fb.com](https://engineering.fb.com/2025/11/10/ml-applications/metas-generative-ads-model-gem-the-central-brain-accelerating-ads-recommendation-ai-innovation/)（B，搜索摘要）。DV365：单一上游模型服务 Instagram/Threads 的 15 个模型 — [arXiv 2506.00450](https://arxiv.org/abs/2506.00450)（A）。Lattice：跨域数据整合与模型统一来对抗"产品/政策碎片化与基础设施成本上升" — [arXiv 2512.09200](https://arxiv.org/abs/2512.09200)（A）。
- 快手 OneRec 结论："建立了全新架构，为技术演进、商业价值优化**和团队协作**引入变革性框架……以此为基础方法系统性推进算法创新并完善团队协作机制" — [arXiv 2506.13695](https://arxiv.org/abs/2506.13695)（A）。
- LLM 组件复用：OneRec-V2 采用 DeepSeek-V3 的无辅助损失 MoE 负载均衡 — [arXiv 2508.20900](https://arxiv.org/abs/2508.20900)；ULTRA-HSTU"受 DeepSeek-V2 启发"、FlashAttention-V3 思路 — [arXiv 2602.16986](https://arxiv.org/abs/2602.16986)；LLaTTE 使用 MLA、结尾称"站在推荐系统 LLM 规模时代的门口"，并计划探索 RL、可扩展基础设施与 scaling 上限 — [arXiv 2601.20083](https://arxiv.org/abs/2601.20083)；Lattice 用 TorchRec+FSDP；OneRec 用 ZeRO-1；NVIDIA 把 SID-GR 推理与 vLLM/SGLang 对标，并提供"SGLang 兼容的权重热更新用于 slime 风格 RL 工作流" — [GitHub recsys-examples](https://github.com/NVIDIA/recsys-examples)（均 A）。
- NVIDIA v26.08 新增 Talos：由 Claude Code/Codex 等编码 agent 自动做 profiling-rewrite-verify 循环的性能优化工具，在 DIN/DIEN/HSTU/OneRec 工作负载上 2.22×–3.29× 加速 — [GitHub recsys-examples README](https://github.com/NVIDIA/recsys-examples)（A）。
- 字节论文作者单位出现"ByteDance AML"（TokenMixer-Large、Rec-Distill、Zenith）与业务团队并列署名，TikTok 与 ByteDance 联合署名（Zenith）— 见对应论文（A）。

### Inferences
- 组织上的"对齐 LLM infra"体现在三点：集中式基础模型团队 + 统一训练栈（TorchRec/FSDP/Megatron-Core/FP8）+ 推理引擎复用 LLM 生态（paged KV、连续批处理、CUDA graph、AOTI）；NVIDIA recsys-examples 的目录结构（TorchRec + Megatron-Core + DynamicEmb + KV cache manager + SID-GR 推理）就是这一趋势的产品化。
- 对 TikTok 而言，公开路线暗示"排序大模型（AML）+ 业务线 expert/student（Rec-Distill）"的分工已经成型。

### Gaps
- 没有公开的组织架构图或团队规模数据；"推荐 infra 对齐 LLM infra"的说法主要来自论文措辞与技术栈选择的推断。

---

## 8. 未来 12 个月的判断（2026-10 → 2027-10）

### Takeaway
基于一手证据，接下来的瓶颈不在 dense 算力本身，而在（1）超长序列的**数据基础设施**（Meta 已证明 4K 以上数据成本超过 GPU）；（2）**在线学习下的 KV/embedding 增量同步**与多级缓存容量；（3）生成式推荐的**beam 服务引擎**；（4）**低精度（FP8/INT4）与定制芯片**的推理性价比。能成为分水岭的基础设施能力是：用户级复用（RLB/KV cache/上游 FM）、训练时延迟物化的样本系统、GPU 哈希表 embedding 的增量同步、以及把 MFU 做到 40–60% 的"纯模型"架构纪律。

### Cited Findings（支撑判断的已引用事实）
- 数据侧墙：Fat Row Wall ≈ 4K 序列，数据基础设施用量超过 GPU 训练 — [arXiv 2604.24806](https://arxiv.org/abs/2604.24806)（A）。
- 序列长度仍是最可靠的增益轴：Meta 64K、字节 10k–20K、WHALE 15k 均未饱和 — 第 1 节（A）。
- MFU 天花板将至：TokenMixer-Large 60%、RankMixer 45%、Kunlun 37%（B200）、OneRec 23.7%/28.8%，LLM 训练约 40%（OneRec 引述）— 第 1、2 节（A）。
- 生成式服务工作负载特殊性（长上下文+短解码+大 beam）与现有 LLM 引擎的不匹配 — [NVIDIA SID-GR README](https://github.com/NVIDIA/recsys-examples/blob/main/examples/sid-gr-inference/README.md)（A）；动态 beam 已被当作收入旋钮 — [arXiv 2602.22732](https://arxiv.org/abs/2602.22732)（A）。
- 硬件：MTIA 450/500 推理芯片 2027 年部署；Meta 推荐模型同时适配 AMD MI300 — 第 4 节（B/A）。
- 增量同步成为标配：DynamicEmb `incremental_dump()` / `replay_increment()`（2026-07/09）— [GitHub](https://github.com/NVIDIA/recsys-examples)（A）。
- 推理时 scaling 尚未兑现：OneRec 明确"推理阶段 step scaling 尚不明显、缺乏推理能力" — [arXiv 2506.13695](https://arxiv.org/abs/2506.13695)（A）；GR4AD 则报告推理时 scaling 有一致增益 — [arXiv 2602.22732](https://arxiv.org/abs/2602.22732)（A）（两者口径不同：前者指多步推理，后者指 beam 规模）。

### Inferences
- 12 个月内最可能的分水岭：(a) 谁能把 10k–64K 序列的样本流水线做成"GPU-bound"（而非存储/带宽-bound）；(b) 谁的在线学习能在 GPU 哈希表 embedding + KV cache 下保持分钟级新鲜度；(c) 谁能把 dense 排序模型从 1–2B 推向 7B+ 而不靠新增 GPU（需要蒸馏/两段式 + FP8）；(d) 生成式召回/排序的专用 beam 引擎与动态 beam 调度。
- 算力瓶颈的主体会从训练转向**推理与数据**：训练侧有 FM 分摊（1:100）、推理侧则每请求都要付费，且 SID/生成式路线把推理从"查表 + MLP"变成"长上下文 + beam"。

### Gaps
- 以上判断是基于 2025 年中–2026 年 8 月论文与仓库的推断，没有任何公司公开 2027 年推荐算力规划的数字。
- 未能获取行业分析（SemiAnalysis 等）与各公司 2026 年资本开支中推荐相关的表述。
