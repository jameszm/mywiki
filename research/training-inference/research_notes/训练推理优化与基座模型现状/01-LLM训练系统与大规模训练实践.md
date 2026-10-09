# 01 · LLM / 多模态预训练的系统层现状与大规模训练实践（2025 年中 – 2026 年 10 月）

> 调研日期：2026-10-09。读者：TikTok 推荐系统训练/推理优化工程师。只用公开信息。
>
> **权威度标注**：A = 论文/技术报告全文或官方仓库文档原文（本次多数来自 `git clone` 的官方仓库与报告 PDF，含从 `deepseek-ai/DeepSeek-V3` 历史提交恢复的 `DeepSeek_V3.pdf`，以及 MLCommons 官方结果仓库的原始日志）；**A(摘要)** = arXiv 论文摘要原文（经 GitHub 镜像仓库 `CSQianDong/Awesome-arXiv-Daily-Reporter` 获取，未读全文，数字为作者自述）；B = 第三方转述/复现笔记；C = 搜索摘要、媒体二手报道。**B/C 的数字一律视为"未核实"。**
>
> **取证限制**：arXiv、HuggingFace、NVIDIA 官方博客/文档站、Meta/OpenAI/xAI 官网均不可达；凡"仅摘要"的论文，正文细节未读。相关缺口列在各节 Gaps。
>
> **MFU 口径提醒**：NVIDIA 官方表只给 "Model TFLOP/s/GPU"，不给 MFU；本文把它除以 NVIDIA 自己公布的"非稀疏峰值"（H100 BF16 989 / FP8 1979；GB200 BF16 2450 / FP8 4900 / NVFP4 9800；GB300 FP8 4900 / NVFP4 14700；B200 FP8 4500）得到的百分比是**本文推算**，并同时给出"相对 BF16 峰值"的口径，便于与各家报告（多数按 BF16 峰值算 MFU）比较。

---

## 关键问题 1：主流训练框架与栈的现状、2025–2026 关键更新与工业选型趋势

### Takeaway
Megatron-Core（+ Transformer Engine + Megatron-Bridge）已成为 NVIDIA 生态和国内工业界（阿里 PAI、华为昇腾 MindSpeed、AMD Primus 均以 Megatron 为骨架）事实上的大规模预训练标准，2025-12 起全部开发转到 GitHub 公开进行；torchtitan（FSDP2 + DTensor）在 PyTorch 原生路线上快速补齐 MoE/EP、MXFP8/NVFP4 与前沿模型定义（DeepSeek V4、Kimi K3、Qwen3.8），并被 AMD Primus、NVIDIA DGX Cloud 基准等作为第二后端；DeepSpeed 的 2025–2026 工作重心转向 offload/超芯片/编译优化与 Muon 支持，不再是前沿预训练主栈；字节的公开栈由 veScale(-FSDP)、VeOmni、Flux/COMET、Triton-distributed 组成，但 MegaScale 本体未开源。

### Cited Findings

**Megatron-LM / Megatron-Core（NVIDIA）**
- 2026-05：`dev` 分支已含 DeepSeek-V4 初始实现，Megatron-Bridge 提供 DeepSeek-V4 的转换/推理/预训练 recipe；2026-04：通过新库 Emerging-Optimizers 支持 Muon 等新优化器；2026-03：发布技术报告《Scalable Training of Mixture-of-Experts Models with Megatron Core》(arXiv 2603.07685)；2026-01：Dynamic Context Parallelism，变长序列训练最高 1.48× 加速；**2025-12：Megatron Core 开发与 CI 全部迁到 GitHub 公开进行**；2025-10：Megatron Bridge（HF↔Megatron 双向转换 + 生产 recipe）；2025-08：MoE 2025 Q3–Q4 路线图（DeepSeek-V3、Qwen3、FP8、Blackwell）；2025-06：Megatron MoE Model Zoo（DeepSeek-V3/Mixtral/Qwen3 最佳配置） — [NVIDIA/Megatron-LM README](https://github.com/NVIDIA/Megatron-LM/blob/main/README.md)（仓库提交 2026-10-08；官方 README；A）
- README 自述：Megatron Core 提供 TP/PP/DP/EP/CP 并行、FP16/BF16/FP8/**FP4** 混合精度；在 H100 集群上训练 2B–462B 模型可达 **47% MFU**；6,144 张 H100 上完成 462B 模型基准；弱扩展时 MFU 从 41%（最小模型）升至 47–48%（最大模型），原因是大 GEMM 算术强度更高；强扩展实验：GPT-3 175B 从 96 张 H100 扩到 4,608 张（batch 固定 1,152 序列），MFU 由 47% 降到 42% — [同上](https://github.com/NVIDIA/Megatron-LM/blob/main/README.md)（A）
- 文档中的并行推荐配置：DeepSeek-V3 671B → 1024 GPU，TP2 / PP16 / CP1 / EP64；Mixtral 8x22B → 256 GPU，TP4 / PP4 / EP8；"TP 与 EP 同时使用时必须开 Sequence Parallel" — [docs/user-guide/parallelism-guide.md](https://github.com/NVIDIA/Megatron-LM/blob/main/docs/user-guide/parallelism-guide.md)（A）
- Megatron-FSDP：NVIDIA 用原生 PyTorch 实现的 FSDP 库（PyPI `megatron-fsdp`），支持 HSDP 与 Hybrid-FSDP（优化器状态在节点内/外 DP rank 间进一步分片）、与 TP/CP/EP 组合、TE 的 MXFP8/NVFP4 recipe、NCCL User Buffer Registration、把 FSDP 集合通信 offload 到交换机的 SHARP；可插入 HF Transformers 与 TorchTitan — [docs/user-guide/features/megatron_fsdp.md](https://github.com/NVIDIA/Megatron-LM/blob/main/docs/user-guide/features/megatron_fsdp.md)（A）
- 其他 2025–2026 新特性：自定义流水线层布局 `--pipeline-model-parallel-layout`（例：DeepSeek-V3 61 层 + MTP 在 PP16/VPP2 下的非对称切分）；细粒度激活 offload（与小红书 RedNote 合作贡献，按子模块 `core_attn/attn_proj/expert_fc1/...` 粒度异步卸载到 CPU）；三种 CUDA Graph 实现（`local / transformer_engine / full_iteration`）；优化器 CPU offload — [pipeline_parallel_layout.md](https://github.com/NVIDIA/Megatron-LM/blob/main/docs/user-guide/features/pipeline_parallel_layout.md)、[fine_grained_activation_offloading.md](https://github.com/NVIDIA/Megatron-LM/blob/main/docs/user-guide/features/fine_grained_activation_offloading.md)、[cuda_graph.md](https://github.com/NVIDIA/Megatron-LM/blob/main/docs/user-guide/features/cuda_graph.md)（A）
- 2025-05：Megatron Core v0.11.0 支持跨数据中心（multi-data center）LLM 训练 — [docs/discussions/README.md](https://github.com/NVIDIA/Megatron-LM/blob/main/docs/discussions/README.md)（A）
- Megatron-Bridge 官方性能页（26.08.01 容器）的 MoE 结果，见关键问题 7 — [NVIDIA-NeMo/Megatron-Bridge docs/performance-summary.md](https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/main/docs/performance-summary.md)（仓库提交 2026-10-08；A）

**PyTorch torchtitan / FSDP2**
- 功能清单（README，提交 2026-10-09）：FSDP2（per-parameter sharding）、TP（含 async TP）、PP（含 zero-bubble）、CP（1M 序列）、分布式 checkpoint（DCP，含异步）、torch.compile、**MXFP8 与 NVFP4 低精度训练**（kernel 由 torchao 提供）、TorchFT 集成、可 checkpoint 的数据加载、MFU/TFLOPs 指标；核心模型含 Llama 3、Qwen3 / 3.5 / 3.8、DeepSeek V3 / V4、GPT-OSS、Kimi K2.7 / K3、Muse Glimmer、Flux；性能报告覆盖至 512 GPU；发布节奏跟随 PyTorch 次版本（示例 torchtitan 0.3.0 ↔ PyTorch 2.14） — [pytorch/torchtitan README](https://github.com/pytorch/torchtitan/blob/main/README.md)、[docs/release.md](https://github.com/pytorch/torchtitan/blob/main/docs/release.md)（A）
- FSDP2 vs FSDP1：Llama-7B 8×H100 上 FSDP2 MFU 更高且峰值内存低 7%，loss 曲线一致 — [docs/fsdp.md](https://github.com/pytorch/torchtitan/blob/main/docs/fsdp.md)（A）
- Async TP 基准（2025-06）：Llama3 70B，256 H100，FSDP=32/TP=8：BF16 597.3→652.4 tokens/s（1.09×），float8 tensorwise 809.8→942.4（1.16×）；Llama3 8B 64 H100：BF16 4378→4809（1.10×） — [benchmarks/asyncTP_llama3_h100_2025-06_torchtitan.md](https://github.com/pytorch/torchtitan/blob/main/benchmarks/asyncTP_llama3_h100_2025-06_torchtitan.md)（A）
- 2024-12 基准（背景）：Llama 3.1 8B 1D 训练在 8/128 张 H100 上 33–39% MFU（测试机为低 TDP 的 HBM2e H100，按 SXM 峰值算因此偏低）；开启 Float8 时作者认为 MFU 定义不清故不报 — [benchmarks/llama3_h100_202412_torchtitan.md](https://github.com/pytorch/torchtitan/blob/main/benchmarks/llama3_h100_202412_torchtitan.md)（A）
- NVIDIA DGX Cloud 基准把 **TorchTitan 列为 DeepSeek V3 671B 的第二框架**（GB200/B200 256 GPU FP8/BF16；H100 512 GPU BF16，容器 25.12） — [NVIDIA/dgxc-benchmarking README](https://github.com/NVIDIA/dgxc-benchmarking/blob/main/README.md)（提交 2026-10-02；A）
- AMD Primus 以 Megatron-LM、TorchTitan、JAX MaxText、Megatron-Bridge 为可切换后端；TorchTitan 后端支持 LLaMA3.x/4、DeepSeek-V3（16B–671B）、Qwen3 0.6B–32B — [AMD-AGI/Primus README](https://github.com/AMD-AGI/Primus/blob/main/README.md)（提交 2026-10-09；A）

**DeepSpeed**
- 2025–2026 更新时间线（README）：2025-03 AutoTP（HF 模型自动 TP 训练）；2025-04 DeepCompile（编译器优化分布式训练，对 ZeRO-3 最高 1.5× 加速，GPU 受限需 offload 场景最高 7×）；2025-06 DeepNVMe、ALST（Arctic Long Sequence Training，多百万 token 序列）；2025-08 ZenFlow（无停顿 offload 引擎，较 ZeRO-Offload 最高 5× 端到端加速、较 ZeRO-Infinity 6.3×，GPU 停顿减少 >85%）；2025-10 SuperOffload（GH200 单卡全参微调 GPT-OSS-20B/Qwen3-14B 达 600 TFLOPS，4×GH200 训 Llama3-70B，较 ZeRO-Offload 最高 4×；ASPLOS 2026 最佳论文荣誉提名）；**2025-11 LinkedIn 用 DeepSpeed ZeRO++ 做推荐系统 LLM 大规模蒸馏训练（EMNLP 2025 industry）**；2025-12 Core API 更新（PyTorch 风格 backward、低精度 master states）；2026-05 Muon 优化器支持、AMD GPU 上 SDMA 卸载 ZeRO-3 集合通信 — [deepspeedai/DeepSpeed README](https://github.com/deepspeedai/DeepSpeed/blob/master/README.md)、[blogs/deepcompile](https://github.com/deepspeedai/DeepSpeed/blob/master/blogs/deepcompile/README.md)、[blogs/deepspeed-zenflow](https://github.com/deepspeedai/DeepSpeed/blob/master/blogs/deepspeed-zenflow/README.md)、[blogs/deepspeed-superoffload](https://github.com/deepspeedai/DeepSpeed/blob/master/blogs/deepspeed-superoffload/README.md)（提交 2026-10-09；A）

**NVIDIA Transformer Engine（TE）**
- 2026-09：TE v2.19 增加 **Rubin 支持、混合量化、MXFP8 EP 通信**、更广的 FP8 attention；2026-06：JAX/MaxText 上 NVFP4 训练博客、Nemotron 3 Ultra 技术报告；2026-04：端到端 FP8 RL 训练；2026-02：NVFP4 训练博客；2025-12：Nemotron 3 "trained with NVFP4 on Transformer Engine"；2025-09：《Pretraining LLMs with NVFP4》、Ling 2.0 FP8 训练方案开源；2025-08：DeepL 用 FP8 训练/推理下一代 LLM；2025-03：GTC "Stable and Scalable FP8 Training on Blackwell" — [TransformerEngine docs/project_updates.rst](https://github.com/NVIDIA/TransformerEngine/blob/main/docs/project_updates.rst)（提交 2026-10-09；A）
- 代码中的 recipe 类：`DelayedScaling`、`Float8CurrentScaling`、`MXFP8BlockScaling`、`Float8BlockScaling`（DeepSeek 式）、`NVFP4BlockScaling`、`CustomRecipe` — [transformer_engine/common/recipe/__init__.py](https://github.com/NVIDIA/TransformerEngine/blob/main/transformer_engine/common/recipe/__init__.py)（A）

**字节跳动公开栈**
- veScale 仓库（volcengine/veScale，提交 2026-03-03）：README 声明"旧 veScale 已移入 legacy/，新 veScale 即将到来"，自述为"内部 PyTorch Distributed 库，支撑 LLM 与 RL 的超大规模训练，仅开源一小部分"；公开内容为 RaggedShard DTensor 与 quick-start；论文：veScale-FSDP（arXiv 2602.22437，MLSys'26）与 veScale（arXiv 2509.07003，eager-mode SPMD） — [volcengine/veScale README](https://github.com/volcengine/veScale/blob/main/README.md)（A）
- veScale-FSDP 摘要：现有 FSDP 固定的 element/row-wise 分片格式与 block-wise 量化训练、非逐元素优化器（Shampoo、Muon，"Gemini、Kimi K2 等前沿模型在用"）冲突；veScale-FSDP 用 RaggedShard 分片格式 + 结构感知规划，吞吐高 5–66%、内存低 16–30%，可扩展到数万 GPU — [arXiv 2602.22437](https://arxiv.org/abs/2602.22437)（2026-02；A(摘要)）
- VeOmni（ByteDance-Seed/VeOmni，提交 2026-10-09）：全模态训练框架，FSDP2 后端、Ulysses 序列并行（同步/异步）、EP（Qwen3-MoE 等）、Torch Distributed Checkpoint、动态 batching；论文 OmniScale 被 AAAI 2026 接收（arXiv 2508.02317）；模型表含 DeepSeek-V4（DSA/mHC 默认 eager，可选 SM90+ TileLang/TileKernels 后端）、Qwen2-3 Omni；路线图含与 VeRL 的全模态 RL — [VeOmni README](https://github.com/ByteDance-Seed/VeOmni/blob/main/README.md)（A）
- Flux（bytedance/flux，提交 2025-08-28）：dense/MoE 的计算-通信重叠 kernel 库，2025-03-10 发布 COMET；Triton-distributed（ByteDance-Seed，提交 2026-09-18）：基于 OpenAI Triton 的分布式编译器（TileLink，MLSys 2025），2026 年连续发布 FlashComm（EP 重叠、跨节点多 NIC EP、固定 buffer 分块 EP、**MXFP8 打包 FP8 的 EP dispatch**）、CuTeDSL 融合 dispatch/combine（Hopper/Blackwell）、Ascend RDMA 支持、AMD MORI 后端 — [flux README](https://github.com/bytedance/flux/blob/main/README.md)、[Triton-distributed README](https://github.com/ByteDance-Seed/Triton-distributed/blob/main/README.md)（A）

**华为昇腾 MindSpeed / 阿里 PAI / AMD**
- MindSpeed-LLM（GitHub 镜像 Ascend/MindSpeed-LLM，提交 2026-10-08；主站 gitcode）：基于 Megatron-Core（v26.0.0 分支支持 core_v0.12.1）；时间线：2025-03 DeepSeek-V3-671B 全家桶、2025-05 Qwen3 首发、2025-07 GLM-4.5-Air、2025-09 Qwen3-Next、2025-12 GPT-OSS；**2026-02 FSDP2 训练后端上线**（Qwen3-Next）、GLM5、Step-3.5-Flash；2026-04 MiniMax M2.7、**DeepSeekV4-Flash 定长预训练支持**；2026-06 GLM5.2 预训练支持（均标 beta） — [Ascend/MindSpeed-LLM README](https://github.com/Ascend/MindSpeed-LLM/blob/master/README.md)（A）
- Pai-Megatron-Patch（alibaba，提交 2025-12-15）：Megatron-Core 之上的模型补丁，2025 年支持 DeepSeek-V3 671B 预训练（2025-02）、Qwen3、Qwen3-Next-80B-A3B 预训练（2025-09，实验性）、Qwen3-VL、Qwen3-Omni SFT（2025-11），以及通过 ChatLearn/verl 的 GRPO RL；分布式 checkpoint 转换工具 — [alibaba/Pai-Megatron-Patch README](https://github.com/alibaba/Pai-Megatron-Patch/blob/main/README.md)（A）
- AMD Primus：多后端（Megatron-LM/TorchTitan/MaxText/Megatron-Bridge）、ROCm 优化（Primus-Turbo kernel、DeepEP、MegaMoE 把专家 all-to-all 折叠进 grouped GEMM 并支持 FP4 grouped GEMM，2026-07）、FP8/MXFP8/MXFP4 recipe、训练前 Projection 估算并行与显存；2026-09 v26.7 镜像（ROCm 10.0，DeepSeek-V4 128k 上下文并行）；自述"在数百 GPU 规模上验证" — [AMD-AGI/Primus README](https://github.com/AMD-AGI/Primus/blob/main/README.md)（A）

### Inferences
- "Megatron-Core 是否成为事实标准"：从依赖关系看答案是肯定的——MindSpeed（昇腾）、Pai-Megatron-Patch（阿里）、Primus（AMD）、Megatron-Bridge/NeMo（NVIDIA）、MLPerf v6.0 的 NVIDIA/CoreWeave/Azure/Google 提交（NeMo 容器）都建立在 Megatron-Core 之上；DeepSeek（HAI-LLM）、Moonshot、Meta、Google 等头部自研栈不在其列，但其公开的并行设计（PP+EP+ZeRO-1）与 Megatron 的 MoE 配置空间一致。
- torchtitan 的工业采用仍以"研究/中等规模/第二后端"为主（≤512 GPU 的公开基准、DGX Cloud 的 DeepSeek V3 第二框架、Primus 后端），但它是 FSDP2/DTensor/Float8/MXFP8/NVFP4 的参考实现，PyTorch 原生路线的 MoE/EP 能力在 2025–2026 明显追上。
- DeepSpeed 2025–2026 的公开成果集中在 offload、GH200/GB200 超芯片、编译和 RL/微调场景，预训练主栈地位已让位于 Megatron-Core 与 torchtitan；但其 ZeRO++ 在 LinkedIn 推荐系统蒸馏中的生产应用对推荐团队有直接参考价值。
- 字节的训练基础设施呈"论文开源、核心闭源"：MegaScale 系列（MegaScale-MoE、MegaScale-Data/OVERLORD、ByteRobust、ByteScale）只有论文，开源的是外围组件（veScale-FSDP、VeOmni、Flux/COMET、Triton-distributed、StragglerAnalysis 工件）。

### Gaps
- NeMo 2.x/Megatron-Bridge 的 release notes 与性能页在 docs.nvidia.com（不可达），仅从仓库文档获取；NeMo 本体仓库未克隆。
- veScale "新版本"内容与发布时间未知（README 仅说"coming"）。
- 华为 MindSpeed 的性能数据（MFU、吞吐）未在 GitHub README 中给出；gitcode 站点不可达。

---

## 关键问题 2：并行策略组合与头部模型技术报告中的训练系统信息

### Takeaway
万卡级 MoE 训练的主流配方是"**PP（多为 16 路，带虚拟流水/非对称切分）× 大 EP（16–64 路，跨 8 节点）× ZeRO-1 DP，TP=1 或极小**"，再用 DualPipe/交错 1F1B + 延后权重梯度计算来把 EP all-to-all 与 PP 通信完全藏进计算；DeepSeek-V3（2048 H800、FP8、DualPipe、2.788M GPU 小时/557.6 万美元）是唯一同时公开规模、并行、精度与成本的样本；Kimi K2（1T MoE、Muon）公开了并行与显存设计但不公开集群规模，并**明确拒绝 DualPipe、不用 FP8 计算**；Qwen3、GLM-4.5、gpt-oss、Gemma 3、Hunyuan 的报告几乎不披露系统细节。

### Cited Findings

**DeepSeek-V3（2024-12，背景但为 2025–2026 所有 MoE 系统设计的基准）**
- 集群：2048 张 NVIDIA H800，节点内 8 卡 NVLink/NVSwitch，节点间 InfiniBand；NVLink 160 GB/s ≈ IB 50 GB/s 的 3.2 倍 — [DeepSeek-V3 Technical Report §3.1/§3.2.2](https://arxiv.org/abs/2412.19437)（PDF 从 deepseek-ai/DeepSeek-V3 仓库历史提交 4c2fdb8 恢复；2024-12-27；A）
- 框架 HAI-LLM（自研）；并行：**16 路 PP、64 路 EP（跨 8 节点）、ZeRO-1 DP，不用 TP**；DualPipe 双向流水：气泡 (PP/2−1)(F&B+B−3W)，参数内存 2×，激活 PP+1；要求 PP 级数与 micro-batch 数可被 2 整除 — [同上 §3.2](https://arxiv.org/abs/2412.19437)、[deepseek-ai/DualPipe README](https://github.com/deepseek-ai/DualPipe)（A）
- 跨节点 all-to-all：每 token 最多发往 4 个节点（node-limited routing），先经 IB 送到目标节点同序号 GPU，再经 NVLink 转发；**仅 20 个 SM 即可打满 IB+NVLink**（warp specialization，10 个通信 channel，定制 PTX、自动调通信块大小以减少 L2 干扰）；每节点平均可选 3.2 个专家，最多可扩到 13 个专家而不增通信成本 — [同上 §3.2.2](https://arxiv.org/abs/2412.19437)（A）
- 显存：重计算 RMSNorm 与 MLA 上投影；EMA 参数放 CPU 异步更新；MTP 与主模型共享 embedding/输出头（放同一 PP rank） — [同上 §3.2.3](https://arxiv.org/abs/2412.19437)（A）
- 训练稳定性：全程"没有不可恢复的 loss spike、没有回滚"；aux-loss-free 负载均衡（专家 bias 按过载/欠载 ±γ 调整，只用于路由不进 gating 值）+ 序列级辅助损失防极端失衡；不丢 token — [同上 §2.1.2/§4](https://arxiv.org/abs/2412.19437)（A）
- 超参：14.8T token，4K 序列预训练，batch 从 3072 渐增到 15360，梯度裁剪 1.0；两阶段上下文扩展 32K→128K（YaRN） — [同上 §4.2/§4.3](https://arxiv.org/abs/2412.19437)（A）
- 成本：预训练 2664K H800 GPU 小时（每万亿 token 180K GPU 小时 = 2048 卡 3.7 天，"不到两个月"），上下文扩展 119K，后训练 5K，合计 2.788M GPU 小时；按 2 美元/GPU 小时计 557.6 万美元；**不含前期研究与消融** — [同上 Table 1](https://arxiv.org/abs/2412.19437)（A）
- 公开的训练 profile：DualPipe 一对前/后向 chunk 的重叠 trace，EP64/TP1/4K 序列（不含 PP 通信） — [deepseek-ai/profile-data](https://github.com/deepseek-ai/profile-data)（2025-03；A）
- 对硬件的建议：把通信 offload 给专用协处理器、统一 IB(scale-out) 与 NVLink(scale-up) 编程接口、Tensor Core 提高 FP8 累加精度（H800 累加仅约 14 bit） — [同上 §3.5](https://arxiv.org/abs/2412.19437)（A）
- DeepSeek-V3.2-Exp（2025-09-29）：引入 DeepSeek Sparse Attention（DSA），从 V3.1-Terminus 继续训练，长上下文训练/推理效率显著提升；成本图按 H800 2 美元/GPU 小时估算 — [DeepSeek_V3_2.pdf](https://github.com/deepseek-ai/DeepSeek-V3.2-Exp/blob/main/DeepSeek_V3_2.pdf)（A）

**Kimi K2（Moonshot，2025-07）**
- 1T 总参/32B 激活、384 专家每 token 激活 8 个、MLA、64 注意力头（DeepSeek-V3 为 128）；15.5T token，**零 loss spike**；MuonClip = Muon + weight decay + 一致 RMS + QK-Clip（τ=100，按需缩放 Wq/Wk，训练到约 30% 步后基本不再触发） — [Kimi K2 tech_report.pdf §2.1](https://github.com/MoonshotAI/Kimi-K2/blob/main/tech_report.pdf)（arXiv 2507.20534；A）
- 集群：H800，节点 2 TB 内存 + 8 卡 NVLink/NVSwitch，**节点间 8×400 Gbps RoCE**（非 IB）；集群总规模未披露 — [同上 §2.4.1](https://github.com/MoonshotAI/Kimi-K2/blob/main/tech_report.pdf)（A）
- 并行：16 路 PP（虚拟流水）× 16 路 EP × ZeRO-1 DP；任意"32 节点整数倍"的规模都可用同一并行配置；BF16 参数 + FP32 梯度累积缓冲约 6 TB，分布在 256 GPU 的模型并行组上，每卡约 30 GB 存全部状态；节点少（如 32 节点）时把部分优化器状态 offload 到 CPU — [同上 §2.4.2](https://github.com/MoonshotAI/Kimi-K2/blob/main/tech_report.pdf)（A）
- **拒绝 DualPipe**："DualPipe 使参数与梯度内存翻倍，需要更多并行来补偿；增 PP 加气泡，增 EP 加开销，对 1T 模型代价过高"；改用交错 1F1B，增加 warm-up micro-batch 来重叠 EP all-to-all，并把权重梯度计算从 micro-batch 的 backward 解耦，与 PP 通信并行，除 warm-up 外所有 PP 通信都被隐藏；**EP 取最小可行值 16**，因为 K2 注意力计算时间更短，需压缩 EP 操作时间；小 EP 组也放松了专家均衡约束 — [同上 §2.4.2](https://github.com/MoonshotAI/Kimi-K2/blob/main/tech_report.pdf)（A）
- 激活：选择性重计算 LayerNorm、SwiGLU、MLA 上投影、MoE 下投影（防早期专家失衡导致 OOM）；MoE 上投影输入与 SwiGLU 输入用 **FP8-E4M3 1×128 tile + FP32 scale 存储**，小规模实验无 loss 变化；**"由于预研中观察到性能退化风险，不在计算中使用 FP8"**；其余激活全部 offload 到 CPU RAM，用 copy engine 流式卸载/预取并与计算、通信重叠，PCIe 拥塞下 EP 通信仍完全重叠 — [同上 §2.4.3](https://github.com/MoonshotAI/Kimi-K2/blob/main/tech_report.pdf)（A）
- 训练配方：4096 上下文，WSD 调度，前 10T 常数 lr 2e-4、后 5.5T 余弦衰减至 2e-5，weight decay 0.1，**全局 batch 恒为 67M token**；退火 400B token（4K）+ 60B token（32K），YaRN 扩到 128K — [同上 §2.5](https://github.com/MoonshotAI/Kimi-K2/blob/main/tech_report.pdf)（A）
- Muon 可扩展性（Moonlight，2025-02）：加 weight decay 与逐参数更新尺度调整后 Muon "开箱即用"，scaling law 实验约 **2× 计算效率**（≈52% 训练 FLOPs 达到 AdamW 同等性能）；开源 ZeRO-1 风格的分布式 Muon 实现；Moonlight 16B-A3B 用 5.7T token 训练 — [Moonlight.pdf](https://github.com/MoonshotAI/Moonlight)（A）
- Kimi K3（2026-07）：2.8T 参数、104B 激活、Kimi Delta Attention + Attention Residuals、Stable LatentMoE（896 路由专家中激活 16 个）、1M 上下文；自述基础设施进展包括"**完美均衡的专家并行训练与高效内存管理**"、KDA 的算法-系统协同设计、百万 token agentic RL；相对 K2 约 2.5× 整体 scaling 效率 — [arXiv 2607.24653](https://arxiv.org/abs/2607.24653)（A(摘要)）
- Moonshot 开源 MoonEP（动态冗余专家在线规划），DeepEP v2.5 为其提供 `lb_prefetch_weights/lb_reduce_grads`（NVLink 内预取冗余专家权重并回收 FP32 梯度） — [DeepEP README](https://github.com/deepseek-ai/DeepEP/blob/main/README.md)（提交 2026-09-30；A）

**其他头部模型报告中的系统信息**
- Qwen3（2025-05）：36T token、119 语言；技术报告**未披露 GPU 类型/数量、并行或 MFU**（全文 grep 无相关内容） — [Qwen3_Technical_Report.pdf](https://github.com/QwenLM/Qwen3/blob/main/Qwen3_Technical_Report.pdf)（A）
- Llama 4（2025-04）：Scout 17B×16E 预训练约 40T token、5.0M H100-80GB GPU 小时；Maverick 17B×128E 约 22T token、2.38M GPU 小时；合计 7.38M GPU 小时（700W TDP，1,999 tCO2eq 地点口径）；"自研训练库、Meta 自建 GPU 集群与生产基础设施"；128K 上下文；Maverick 发布 FP8 权重 — [meta-llama/llama-models MODEL_CARD.md](https://github.com/meta-llama/llama-models/blob/main/models/llama4/MODEL_CARD.md)（A）
- Llama 4 Behemoth：Meta 发布博文称预训练用 **FP8、32K GPU，达到 390 TFLOPs/GPU**，数据 >30T token — [dasroot.net 技术分析](https://dasroot.net/posts/2025/12/technical-analysis-llama-4-scout-maverick-behemoth/)、[LessWrong 转述](https://lesswrong.com/posts/Wnv739iQjkBrLbZnr/meta-releases-llama-4-herd-of-models)（2025；C，**未核实**，原文在 ai.meta.com 不可达）
- Meta NCCLX：为 >100,000 GPU 集群设计的集合通信框架，覆盖训练到推理，在 Llama4 上验证 — [arXiv 2510.20171 "Collective Communication for 100k+ GPUs"](https://arxiv.org/abs/2510.20171)（2025-10；A(摘要)）
- GLM-4.5（2025-08）：355B-A32B，23T token 多阶段训练；摘要与仓库均无集群/并行信息；GLM-5（2026-02）采用 DSA 显著降低训练与推理成本，并用"生成与训练解耦的异步 RL 基础设施" — [arXiv 2508.06471](https://arxiv.org/abs/2508.06471)、[arXiv 2602.15763](https://arxiv.org/abs/2602.15763)（A(摘要)）；[zai-org/GLM-4.5 README](https://github.com/zai-org/GLM-4.5)（A）
- MiniMax-M1（2025-06）：在 MiniMax-Text-01 上继续预训练 7.5T token；**RL 阶段 512 张 H800、3 周、租金约 53 万美元**；发现训练/推理 kernel 精度不匹配，把 LM 输出头改为 FP32 后修复 — [MiniMax_M1_tech_report.pdf](https://github.com/MiniMax-AI/MiniMax-M1/blob/main/MiniMax_M1_tech_report.pdf)（A）；MiniMax-01（2025-01，背景）：H800 集群规模**动态在 1500–2500 卡之间变化**，varlen ring attention，EP-ETP 重叠策略 — [MiniMax-01.pdf](https://github.com/MiniMax-AI/MiniMax-01/blob/main/MiniMax-01.pdf)（A）；MiniMax-M2 系列（2026-05）：229.9B 总参/9.8B 激活，Forge agent-native RL 系统，训练-推理-agent 解耦 — [arXiv 2605.26494](https://arxiv.org/abs/2605.26494)（A(摘要)）
- gpt-oss（2025-08）：模型卡摘要只说 MoE + 大规模蒸馏与 RL，未披露训练算力；Megatron Core 为其集成 YaRN、attention sinks、自定义激活 — [arXiv 2508.10925](https://arxiv.org/abs/2508.10925)（A(摘要)）；[Megatron-LM README](https://github.com/NVIDIA/Megatron-LM/blob/main/README.md)（A）
- Gemma 3（2025-03）：27B 用 14T token 训练，用 JAX + ML Pathways（单 Python 进程编排整个训练） — [Gemma 3 model card](https://ai.google.dev/gemma/docs/core/model_card_3)（B，经搜索摘要；TPU 型号/数量未核实）
- Seed-OSS-36B（字节，2025-08）：原生 512K 上下文训练；README/模型卡无集群信息 — [ByteDance-Seed/Seed-OSS README](https://github.com/ByteDance-Seed/Seed-OSS)（A）
- Seed1.5-VL（字节，2025-05）：预训练约 3T 多模态 token、**1.3M GPU 小时**；视觉编码器与 MLP 适配器用 ZeRO DP，LLM 用 4D 并行（EP + 交错 PP + ZeRO-1 DP + 上下文扩展用 CP）；优化项含 workload balancing、并行感知数据加载、鲁棒训练、CP 高性能 attention kernel、选择性激活 checkpoint/offload、kernel 融合、细粒度通信重叠 — [arXiv 2505.07062](https://arxiv.org/abs/2505.07062)（B，经搜索摘要转述正文；数字**未核实**）
- Hunyuan-A13B（腾讯，2025-06）：80B-A13B，20T token，基础阶段固定 4096 上下文，退火 300B token 8192 上下文，再分两阶段扩到 32K→256K（NTK-aware）；**未披露 GPU/MFU** — [Hunyuan_A13B_Technical_Report.pdf](https://github.com/Tencent-Hunyuan/Hunyuan-A13B/blob/main/report/Hunyuan_A13B_Technical_Report.pdf)（A）
- LongCat-Flash（美团，2025-09）：560B MoE（零计算专家，平均激活 27B）、Shortcut-connected MoE 扩大计算-通信重叠窗口；超参迁移 + 模型增长初始化 + 稳定性套件 + **确定性计算**；**>20T token 在 30 天内训完**（集群规模未披露） — [arXiv 2509.01322](https://arxiv.org/abs/2509.01322)（A(摘要)）
- NVIDIA Nemotron 3（2025-12 / 2026-04 / 2026-06）：混合 Mamba-Transformer MoE；Nano 30B-A3B 25T token；**Super 120B-A12B 是家族首个 NVFP4 预训练模型，25T token**；**Ultra 550B-A55B 20T token，NVFP4 预训练，1M 上下文**，全部开源数据与配方 — [arXiv 2512.20856](https://arxiv.org/abs/2512.20856)、[arXiv 2604.12374](https://arxiv.org/abs/2604.12374)、[arXiv 2606.15007](https://arxiv.org/abs/2606.15007)（A(摘要)）
- ERNIE 4.5（百度，2025-06）：异构混合并行 + 分层负载均衡，节点内 EP、显存高效流水调度、FP8 混合精度、细粒度重计算；**最大模型预训练 47% MFU**（PaddlePaddle） — [PaddlePaddle/ERNIE README](https://github.com/PaddlePaddle/ERNIE/blob/develop/README.md)（A，峰值口径未说明）；ERNIE 5.0（2026-02）：万亿级统一多模态 MoE，"弹性训练"——一次预训练得到不同深度/专家容量/路由稀疏度的子模型族 — [arXiv 2602.04705](https://arxiv.org/abs/2602.04705)（A(摘要)）
- Ling（蚂蚁）：Ling-Plus 290B-A28.8B 在"非高端 GPU"上训练（2025-03）；Ling 2.0 **全程 FP8 混合精度训练**，>1T token 实验 loss 与 BF16 几乎一致，并开源 FP8 方案（tile/blockwise 缩放 + FP8 优化器 + FP8 按需转置权重 + FP8 padding routing map）；Ling-mini-2.0 1/32 稀疏 + MTP，8×80G GPU 上 109.5K tok/s（Llama 3.1 8B 基线 81.2K） — [arXiv 2503.05139](https://arxiv.org/abs/2503.05139)（A(摘要)）、[inclusionAI/Ling-V2 README](https://github.com/inclusionAI/Ling-V2)（A）；Ling/Ring 2.6（2026-06）：万亿参数规模，通过"架构迁移预训练"从 Ling-2.0 升级，混合 Lightning Attention + MLA — [arXiv 2606.15079](https://arxiv.org/abs/2606.15079)（A(摘要)）
- Step-3（阶跃，2025-07）：321B VLM，MFA 注意力 + Attention-FFN Disaggregation（推理系统） — [arXiv 2507.19427](https://arxiv.org/abs/2507.19427)（A(摘要)）
- MiMo-V2-Flash（小米，2026-01）：309B-A15B，SWA/全局 5:1 混合注意力，27T token，原生 32k 后扩 256k — [arXiv 2601.02780](https://arxiv.org/abs/2601.02780)（A(摘要)）

**昇腾（Ascend）上的大模型训练**
- Pangu Ultra（2025-04）：135B dense，13.2T token，**8,192 张 Ascend NPU**，depth-scaled sandwich norm 消除 loss spike — [arXiv 2504.07866](https://arxiv.org/abs/2504.07866)（A(摘要)）
- Pangu Ultra MoE（2025-05）：718B MoE，用仿真选模型配置，优化 EP 通信与设备内显存，**6K Ascend NPU 上 30.0% MFU**，性能对标 DeepSeek R1 — [arXiv 2505.04519](https://arxiv.org/abs/2505.04519)（A(摘要)）
- SLAI T-Rex（2026-07）：在 Ascend NPU SuperPOD 上对 DeepSeek-V4 家族做全参后训练，分层优化（模型级并行、计算-通信编排、kernel），**34.22% MFU，较开源基线配方 2.93×** — [arXiv 2607.20145](https://arxiv.org/abs/2607.20145)（A(摘要)）
- HiFloat4（2026-04）：华为 FP4 格式，在 Ascend 集群上 dense（Pangu/LLaMA 式）与 MoE 的线性层与专家 GEMM 全部 FP4，稳定技术使相对误差 <1% — [arXiv 2604.08826](https://arxiv.org/abs/2604.08826)（A(摘要)）
- DeepEP 已有 Ascend 版本（"同 API、在 HUAWEI Ascend 950 上全性能"） — [DeepEP README](https://github.com/deepseek-ai/DeepEP/blob/main/README.md)（A）
- 媒体报道称 DeepSeek-V4-Pro（1.6T）在华为 Ascend 910C 集群完成全部训练、MFU >30%（2026-08） — [borncity.com](https://borncity.com/news/deepseek-v4-pro-16-billionen-modell-auf-huawei-hardware-trainiert/)（C，**未核实**；DeepSeek-V4 GitHub 仓库不可克隆）
- MindSpeed RL（2025-07）：Ascend 上的分布式 RL 数据流系统（transfer dock、allgather-swap 重分片） — [arXiv 2507.19017](https://arxiv.org/abs/2507.19017)（A(摘要)）；MindVL（2025-09）：Mindspeed-MLLM 多模态训练框架，部分算子等价替换以保精度 — [arXiv 2509.11662](https://arxiv.org/abs/2509.11662)（A(摘要)）

**NVIDIA 参考并行配置（DGX Cloud 基准 recipe，2026-10）**
- DeepSeek V3 671B：GB200 128 GPU → TP1/PP4/EP32/VP4（NVFP4/FP8/BF16）；256–512 GPU → TP1/PP2/EP32/VP8（NVFP4/FP8）或 PP4/EP64（BF16）；B200：TP1/PP8/EP8/VP2；**H100 1024 GPU：TP2/PP8/EP64/VP2**，GBS 16384 — [dgxc-benchmarking deepseek_v3 README](https://github.com/NVIDIA/dgxc-benchmarking/blob/main/deepseek_v3/pretrain/megatron_bridge/README.md)（A）
- Kimi-K2 1T：GB200/GB300 256–512 GPU → TP1/PP4/EP64/VP4；H100/B200 → **TP1/PP16/EP16**（与 Moonshot 自述配置一致） — [dgxc-benchmarking kimi-k2 README](https://github.com/NVIDIA/dgxc-benchmarking/blob/main/kimi-k2/README.md)（A）
- Qwen3-235B：GB200 PP4/EP32/VP12（FP8）；B200 PP8/EP8 或 EP32；H100 PP8/EP8（BF16）；Qwen3-30B：EP8 纯 DP 扩展 — [dgxc-benchmarking qwen3 README](https://github.com/NVIDIA/dgxc-benchmarking/blob/main/qwen3/pretrain/README.md)（A）
- GPT-OSS 120B：GB200 EP64 / B200 与 H100 EP8，TP1 PP1，BF16 — [dgxc-benchmarking gpt-oss README](https://github.com/NVIDIA/dgxc-benchmarking/blob/main/gpt-oss/pretrain/megatron_bridge/README.md)（A）

### Inferences
- DeepSeek-V3 实际训练吞吐可反推：14.8T token / 2.664M GPU 小时 ≈ **1,540 token/s/GPU**；按 6×37B FLOPs/token 估模型算力 ≈ 343 TFLOPS/GPU，相当于 H800 FP8 密集峰值（1979）的 17%、BF16 峰值（989）的 35%（本文推算，未计 attention 与 MTP）。这与 NVIDIA 在 GB200 上的 DeepSeek-V3 MXFP8 结果（1292 TFLOPS，FP8 峰值的 26%）处在同一量级，说明 MoE 的 MFU 天花板比 dense 低得多。
- Kimi K2 与 DeepSeek-V3 的对比给出两条 MoE 系统路线：DeepSeek 用大 EP（64）+ DualPipe + FP8 计算换极致重叠；Moonshot 用小 EP（16）+ 交错 1F1B + CPU 激活卸载 + 仅 FP8 存储，换取 1T 规模下的显存与研究迭代一致性。NVIDIA 的 Kimi-K2 recipe 在 NVL72 上回到 EP64/PP4，说明"小 EP"主要是 8 卡 NVLink 域 + RoCE 的约束产物。
- Qwen3/GLM-4.5/gpt-oss/Gemma 3/Hunyuan 不披露系统细节，意味着对国内团队而言 DeepSeek、Kimi、ERNIE、LongCat、Pangu 的报告是仅有的"生产实践并公开数据"样本。

### Gaps
- DeepSeek V3.1/V4 的训练系统细节（集群、精度、成本）：V4 仓库不可克隆，媒体关于 Ascend 910C 的说法未核实。
- Kimi K2/K3、LongCat-Flash、GLM 的集群规模与 GPU 小时未公开。
- Gemma 3 报告正文中的 TPU 配置（型号、芯片数、Pathways 细节）未读到。
- Seed1.5-VL 训练基础设施节的 MFU 数字未获取。

---

## 关键问题 3：万卡/十万卡集群工程——故障、checkpoint、straggler、网络与有效训练时间

### Takeaway
2025–2026 的公开数据把"有效训练时间"量化了：字节 ByteRobust 在 9,600 GPU、3 个月任务上做到 **97% ETTR**（平台 >200,000 GPU）；O(100K) GPU 同步训练的有效时间可低至 44%，FT-HSDP（以 DP 副本为容错单元）把故障恢复停顿从 10 分钟降到 3 分钟、有效时间提到 80%；straggler 治理（字节 OSDI'25 的 what-if 分析、Guard 的在线监控 + 离线节点扫查，MFU 最高 +1.7×、step 方差 20%→1%）与多级 checkpoint（TierCheck <10 s、NVRx 本地/异步 checkpoint、DeepSeek 3FS 6.6 TiB/s）成为标配；网络侧 RoCE（Kimi 8×400G）与 IB（DeepSeek）并存，NVL72/CloudMatrix384 的 scale-up 域正在改写 EP 通信库。

### Cited Findings

**字节跳动（MegaScale 系列与后续）**
- ByteRobust（SOSP'25）：面向 LLM 训练的大规模 GPU 基础设施管理系统，把故障检测与恢复作为常规流程，利用并行性做高容量容错、快速故障定界与数据驱动的定位；**部署在 >200,000 GPU 的生产平台，9,600 GPU 的三个月训练任务达到 97% ETTR（有效训练时间比）** — [arXiv 2509.16293](https://arxiv.org/abs/2509.16293)（2025-09；A(摘要)）；[LLMSys-PaperList 标注 SOSP'25](https://github.com/AmberLJC/LLMSys-PaperList)（B）
- Understanding Stragglers in Large Model Training Using What-if Analysis（OSDI'25，NYU + ByteDance Seed）：基于字节 LLM 训练集群 **5 个月 trace**，用"无 straggler 的模拟运行"做 what-if 分析，回答 straggler 频率/影响、时空模式、根因；结论之一是"straggler 并不总由硬件故障引起"；开源工件含模拟器与三类样本 trace（序列长度不均 SE、流水阶段切分不均 ST、单 worker 人工减速 AR） — [USENIX OSDI'25 页面](https://www.usenix.org/conference/osdi25/presentation/lin-jinkun)（B，经搜索）、[ByteDance-Seed/StragglerAnalysis](https://github.com/ByteDance-Seed/StragglerAnalysis)（A，仅工件说明，定量结论未读到）
- RobustRL（2025-12）：RL 后训练的角色级容错（trainer/rollout 分别恢复、rollout 热备、UCX 点对点动态重连），"不再像 ByteRobust 那样整任务重启" — [arXiv 2512.22492](https://arxiv.org/abs/2512.22492)（A(摘要)）
- MegaScale-MoE（EuroSys'26）：按注意力/FFN 分别定制并行策略，算子间与算子内两级通信-计算重叠，通信压缩到低精度；**352B MoE 在 1,440 张 Hopper GPU 上 1.41M tokens/s，效率为 Megatron-LM 的 1.88×** — [arXiv 2505.11432](https://arxiv.org/abs/2505.11432)（2025-05；B，经搜索摘要；**未核实**）
- ByteScale（2025-02）：Hybrid Data Parallelism（动态 mesh 统一 DP 与 CP），7B–141B 模型、**256K–2048K 上下文、>12,000 GPU 生产集群** — [arXiv 2502.21231](https://arxiv.org/abs/2502.21231)（A(摘要)）
- MegaScale-Data / OVERLORD（EuroSys'26）：工业级分布式数据加载架构——集中式声明式 data plane（长短上下文、多模态、课程学习编排）、按角色拆分的 Source Loader/Data Constructor 自动扩缩、**Shadow Loader + 差分 checkpoint 实现不中断的故障恢复**；部署在数千 GPU 生产集群 — [arXiv 2504.09844](https://arxiv.org/abs/2504.09844)（A(摘要)，加速倍数被截断）
- COMET（MLSys'25）：MoE 层通信可占模型执行时间 47%；细粒度重叠使单 MoE 层 1.96×、端到端平均 1.71×；**已在万卡级生产集群采用，节省数百万 GPU 小时** — [arXiv 2502.19811](https://arxiv.org/abs/2502.19811)（A(摘要)）
- （背景，2024）MegaScale（NSDI'24）为字节万卡训练系统的起点；本次未能取得全文，数字不列 — [LLMSys-PaperList](https://github.com/AmberLJC/LLMSys-PaperList)（B）

**Meta / 十万卡级**
- FT-HSDP（2026-02）：在 O(100K) GPU 上同步训练因频繁故障与长恢复导致低效率；以 DP 副本为容错单元，只下线含故障 GPU 的副本；Fault Tolerant All Reduce（CPU 驱动控制逻辑、GPU 传数据）+ 非阻塞追赶协议；**故障恢复停顿 10 分钟→3 分钟，有效训练时间 44%→80%**，精度无退化 — [arXiv 2602.00277](https://arxiv.org/abs/2602.00277)（A(摘要)；作者单位未在摘要中出现）
- NCCLX（Meta）：面向 >100,000 GPU 的集合通信框架，Llama4 上验证 — [arXiv 2510.20171](https://arxiv.org/abs/2510.20171)（A(摘要)）
- Llama 4 Scout/Maverick 合计 7.38M H100 GPU 小时（见问题 2） — [MODEL_CARD.md](https://github.com/meta-llama/llama-models/blob/main/models/llama4/MODEL_CARD.md)（A）

**xAI / Microsoft–OpenAI / Google / Anthropic 集群（规模口径）**
- xAI：Musk 称 Colossus 1 有 230k GPU（含 30k GB200）在训 Grok，Colossus 2 首批 550k GB200/GB300；2026-01 Series E 公告称 Grok 5 在 Colossus 2 训练；后续扩建"至少 220,000 GB300、>400 MW" — [TweakTown](https://www.tweaktown.com/news/106571/elon-musk-230k-ai-gpus-train-grok-at-colossus-1-550k-gb200-gb300s-at-colossus-2-coming-soon/index.html)、[Introl](https://introl.com/ar/blog/xai-colossus-2-gigawatt-expansion-555k-gpus-january-2026)（C，**未核实**）
- Microsoft：Fairwater（威斯康星）"数十万 GB200/GB300、单一扁平网络、AI WAN 跨站互联"，2026 初投运；2025-10 为 OpenAI 部署 4,608 张 GB300（64 台 NVL72，Quantum-X800 IB） — [ConvergeDigest](https://convergedigest.com/microsoft-unveils-fairwater-ai-data-center-in-wisconsin/)、[3dtested](https://www.3dtested.com/tech-industry/artificial-intelligence/microsoft-deploys-worlds-first-supercomputer-scale-gb300-nvl72-azure-cluster-4-608-gb300-gpus-linked-together-to-form-a-single-unified-accelerator-capable-of-1-44-pflops-of-inference)（C，**未核实**）
- Google TPU：Ironwood（2025-11-06 宣布数周内 GA）单 superpod **9,216 芯片、ICI 9.6 Tb/s、1.77 PB 共享 HBM**，"跨 pod 扩展到数十万 TPU 的集群"，OCS 光路交换动态绕过故障；TPU 8t（2026-04-22）**原生 FP4、12.6 PFLOPs、216 GB HBM/6.5 TB/s、单 superpod 9,600 芯片 3D torus、Virgo 网络 >134,000 芯片 47 Pb/s、"单训练集群 >100 万 TPU"、较 Ironwood 2.7× 性能/美元**，TPUDirect Storage + Managed Lustre 10T 存储访问较 Ironwood 快 10× — [Google Cloud Blog: Ironwood GA](https://cloud.google.com/blog/products/compute/ironwood-tpus-and-new-axion-based-vms-for-your-ai-workloads)、[Google Cloud Blog: TPU 8t/8i](https://cloud.google.com/blog/products/compute/tpu-8t-and-tpu-8i-technical-deep-dive)（A，厂商自述）
- Google Cloud 训练可靠性工具（2025-04）：Cluster Director 提供 AI Health Predictor、Straggler Detection、端到端健康检查、多级 checkpoint；Pathways 支持故障时自动缩容、恢复后扩容的弹性训练（无量化数据） — [What's new with AI Hypercomputer](https://cloud.google.com/blog/products/compute/whats-new-with-ai-hypercomputer)（A）
- MaxText 自述：单一训练任务跨 **50,944 颗 TPU v5e** 近线性扩展 — [maxtext docs architecture_overview.md](https://github.com/AI-Hypercomputer/maxtext/blob/main/docs/reference/architecture/architecture_overview.md)（A）
- Anthropic（2025-10-23）：计划使用最多 100 万颗 TPU，2026 年新增"远超 1 GW"算力，三平台策略（TPU、Trainium、NVIDIA GPU） — [Anthropic news](https://www.anthropic.com/news/expanding-our-use-of-google-cloud-tpus-and-services)（A）

**故障恢复、checkpoint、straggler 的系统工作（2025-09 至 2026-07）**
- FlashRecovery（2025-09）：秒级主动故障检测、与集群规模无关的任务重启（正常/故障节点分别处理 + 通信组重建协议）、**一步内无 checkpoint 恢复** — [arXiv 2509.03047](https://arxiv.org/abs/2509.03047)（A(摘要)）
- ReCoVer（2026-05）：保持"每迭代 micro-batch 数恒定"的不变量，使梯度与无故障运行随机等价；容错集合通信 + 步内细粒度恢复 + 幸存者间动态重分配 micro-batch；与 3D 并行和 HSDP 都可组合；512 GPU 实验中累计丢失 256 GPU 仍保持训练轨迹，较 checkpoint-restart **2.23× 有效吞吐** — [arXiv 2605.11215](https://arxiv.org/abs/2605.11215)（A(摘要)）
- Guard（2026-05，MLSys'26）：在线性能监控 + 离线节点扫查（node-sweep）捕捉 fail-slow；部署于大规模基础模型预训练，**平均 FLOPs 利用率最高 +1.7×，run-to-run step 方差 20%→1%，MTTF 提升** — [arXiv 2605.17879](https://arxiv.org/abs/2605.17879)（A(摘要)）
- TierCheck（2026-05）：三级 checkpoint（本地/对端内存差分 checkpoint + 异步远端全量），端到端 checkpoint 时间 <10 s，支持高频 checkpoint（40B 模型实验） — [arXiv 2605.17821](https://arxiv.org/abs/2605.17821)（A(摘要)）；DataStates-LLM（2026-06）：利用前/后向期间参数不变做惰性非阻塞异步快照 — [arXiv 2601.16956](https://arxiv.org/abs/2601.16956)（A(摘要)）
- NVIDIA Resiliency Extension（NVRx）v0.7（2026-10）：in-job 重启（不重新分配 Slurm 节点）、热备节点、barrier rendezvous、调度器节点健康排除、**NVLink 重放/恢复计数器健康检查**、持久化异步 checkpoint worker、本地 checkpoint、straggler 检测、故障归因服务（Attribution/Restart Agent，可接 MCP/Slack）；in-process restart 已弃用；要求 PyTorch ≥2.8、TE ≥2.5 — [nvidia-resiliency-ext README](https://github.com/NVIDIA/nvidia-resiliency-ext/blob/main/README.md)、[docs/source/release-notes.md](https://github.com/NVIDIA/nvidia-resiliency-ext/blob/main/docs/source/release-notes.md)（A）
- torchtitan 集成 TorchFT；OVERLORD 的 Shadow Loader 差分 checkpoint（见上）；DeepSeek 3FS 支持高吞吐并行 checkpoint（见问题 6） — [torchtitan README](https://github.com/pytorch/torchtitan/blob/main/README.md)、[3FS README](https://github.com/deepseek-ai/3FS)（A）
- 其他：Mycroft（SOSP'25，追踪集合通信依赖以提升可靠性）、Sailor（SOSP'25，动态/异构/跨地域集群）、Zeppelin（EuroSys'26，DP 变长负载均衡）、HybridEP（2025-10，跨数据中心 EP：专家迁移与数据传输混合）、Megatron Core v0.11 的跨数据中心训练 — [LLMSys-PaperList](https://github.com/AmberLJC/LLMSys-PaperList)（B）、[arXiv 2510.19470](https://arxiv.org/abs/2510.19470)（A(摘要)）

**网络**
- DeepSeek-V3：节点间 IB（50 GB/s/卡）、节点内 NVLink 160 GB/s；Kimi K2：**8×400 Gbps RoCE**；两家都用 8 卡 NVLink/NVSwitch 节点 — [DeepSeek-V3 §3](https://arxiv.org/abs/2412.19437)、[Kimi K2 §2.4.1](https://github.com/MoonshotAI/Kimi-K2/blob/main/tech_report.pdf)（A）
- NVL72：MLPerf v6.0 中 NVIDIA/Azure/CoreWeave/Google 的 GB200/GB300 系统均为"4 GPU/节点 + NVLink Gen5 1800 GB/s + NVSwitch Gen5"的 NVL72 机架（128×NVL72 = 8,192 GPU） — [mlcommons/training_results_v6.0 系统描述 JSON](https://github.com/mlcommons/training_results_v6.0)（A）
- UBEP（2026-07）：面向 NVL72/576 与华为 CloudMatrix384 超节点的 EP 通信库，解决 BSP 串行化、同步开销与距离无关调度的负载不均，all-to-all 延迟最高 −52.4% — [arXiv 2607.06202](https://arxiv.org/abs/2607.06202)（A(摘要)）
- Megatron-FSDP 用 SHARP 把 FSDP 集合通信卸载到 IB 交换机 — [megatron_fsdp.md](https://github.com/NVIDIA/Megatron-LM/blob/main/docs/user-guide/features/megatron_fsdp.md)（A）
- Spectrum-X 以太网在训练集群中的实测：本次未找到 A/B 级来源（见 Gaps）。

### Inferences
- "有效训练时间/ETTR/goodput" 已成为可对标的 KPI：万卡级（9.6K）成熟平台 97%，十万卡级同步训练未做副本级容错时可低至 44%——规模每上一个数量级，容错架构必须从"checkpoint-restart"换成"副本/角色级隔离 + 步内恢复"。
- 字节公开论文的叙事一致：故障（ByteRobust/RobustRL）、straggler（OSDI'25）、数据加载（OVERLORD）、通信重叠（COMET/Flux/Triton-distributed）、分片格式（veScale-FSDP）各有一篇，覆盖了万卡训练的全部非算力瓶颈；推荐团队可以把这套分层视作内部平台能力清单。
- NVL72 把 EP 通信的主战场从"8 卡 NVLink + RDMA"转到"72 卡 NVLink 域 + 跨机架 RDMA"，DeepEP v2（NCCL Gin 后端）、NCCL EP、HybridEP 后端、TE MXFP8 EP 通信、UBEP 都是对此的回应。

### Gaps
- MTBF/故障率的原始数据（如每千卡每天故障次数）：2025–2026 的公开论文只给 ETTR/停顿时间，未取得具体故障率表（Llama 3 2024 年报告中的故障统计属于背景，此次未重新取证）。
- ByteDance straggler 论文的定量结论（受影响任务比例、损失时间）未读到全文。
- Spectrum-X vs IB/RoCE 在训练中的公开对比数据缺失；阿里 HPN、腾讯星脉等网络论文此次未取证。
- 快手公开的 LLM 集群实践仅见 SlimPipe（长上下文流水并行，见问题 6）。

---

## 关键问题 4：低精度训练——FP8 配方、Blackwell 上的 MXFP8/NVFP4 与 FP4 的生产化程度

### Takeaway
FP8 已是 Hopper/H800 时代的生产默认（DeepSeek 分块缩放、Ling 2.0 全程 FP8、Megatron "tensorwise 最快稳定"配方），但仍有头部团队（Kimi K2）因风险只用 FP8 存储不用 FP8 计算；Blackwell 上 **MXFP8 成为 NVIDIA 官方基准的默认精度**（1×32 块、E8M0 scale，MoE 等价收敛）；**NVFP4 预训练在 2026 年出现了真正的生产案例——NVIDIA Nemotron 3 Super（120B-A12B，25T token）与 Ultra（550B-A55B，20T token）**，MLPerf v5.1 起 NVIDIA 用 NVFP4 提交，Llama 405B 在 GB300 上 NVFP4 较 FP8 再快 1.35×；但 Megatron/torchtitan 文档都把 NVFP4 标为"持续演进/实验性"，需保留首尾层 BF16、末期切回高精度等缓解。

### Cited Findings

**FP8（Hopper 时代配方）**
- DeepSeek-V3 FP8 框架：Fprop/Dgrad/Wgrad 三个 GEMM 均 FP8，激活 1×128 tile、权重 128×128 block 分组缩放，缩放因子沿 GEMM 内维按组，**每 128 元素（N_C=128）把部分和提升到 CUDA Core 做 FP32 累加**（H800 Tensor Core 累加仅约 14 bit，否则最大相对误差近 2%）；MoE 激活以 FP8 缓存与分发，低精度优化器状态用 BF16；master weight/权重梯度/优化器状态保持高精度；两个模型（≈V2-Lite、V2）约 1T token 验证，**相对 loss 误差 <0.25%**；块状缩放激活（与权重同法）会导致不稳定（附录 B.2） — [DeepSeek-V3 §3.3](https://arxiv.org/abs/2412.19437)（A）
- Megatron-Core 低精度指南（2026）：recipe 表——`delayed`（历史默认，唯一支持优化器 CPU offload）、`tensorwise`（当前缩放，无 amax 历史，"Hopper/H100 最快稳定 FP8"推荐，生产 RL/SFT 用）、`mxfp8`（仅 Blackwell，"B200/GB200 最快 FP8"，需 `--reuse-grad-buf-for-mxfp8-param-ag`）、`blockwise`（1×128/128×128，DeepSeek 式，"复现/微调 DeepSeek 配方或需要更大离群值裕度"）、`nvfp4`（仅 Blackwell，TE ≥2.7.0.dev0）；稳定性旋钮：首尾 N 层 BF16（FP4 建议 2–4 层）、`--fp8-margin`、Wgrad 保持高精度、amax 规约限制在 TP/CP 域；内存旋钮：FP8/FP4 参数 all-gather、优化器状态 exp_avg/exp_avg_sq 可存 FP8 — [low_precision_training.md](https://github.com/NVIDIA/Megatron-LM/blob/main/docs/user-guide/features/low_precision_training.md)（A）
- Kimi K2：FP8-E4M3 仅用于激活存储，**明确不在计算中用 FP8** — [Kimi K2 §2.4.3](https://github.com/MoonshotAI/Kimi-K2/blob/main/tech_report.pdf)（A）
- Ling 2.0：全程 FP8 混合精度，>1T token 与 BF16 loss 几乎一致，开源 FP8 方案（见问题 2） — [Ling-V2 README](https://github.com/inclusionAI/Ling-V2)（A）
- Llama 4：Maverick 发布 FP8 权重；Behemoth FP8 预训练 390 TFLOPs/GPU（C，未核实） — 见问题 2
- FP8 在 RL 中：FP8-RL（veRL，blockwise FP8 W8A8 rollout + FP8 KV cache，2026-01）；NVIDIA "端到端 FP8 RL"（2026-04）；lmsys FP8 RL（2025-11） — [arXiv 2601.18150](https://arxiv.org/abs/2601.18150)（A(摘要)）、[TE project_updates](https://github.com/NVIDIA/TransformerEngine/blob/main/docs/project_updates.rst)（A）
- FP8-Flow-MoE（MLSys'26）：免 cast 的 MoE FP8 配方，避免双重量化误差 — [LLMSys-PaperList](https://github.com/AmberLJC/LLMSys-PaperList)（B，仅标题）
- torchtitan Float8（tensorwise/rowwise）+ async TP 在 256 H100 上 Llama3 70B：float8 tensorwise 942 vs BF16 652 tokens/s/GPU（1.44×） — [asyncTP 基准](https://github.com/pytorch/torchtitan/blob/main/benchmarks/asyncTP_llama3_h100_2025-06_torchtitan.md)（A）
- MXFP4 激活 + FP8 计算用于 Hopper 上的 MoE（2026-03）：直接 FP8↔FP4 量化/反量化与缩放感知的行列转换，FP4 激活与 EP 通信压缩，**671B 规模下吞吐 1157→1302 token/GPU/s（+12.5%），峰值激活内存 −14.8%（11.8 GB）**，收敛不变 — [arXiv 2603.02731](https://arxiv.org/abs/2603.02731)（A(摘要)）

**MXFP8（Blackwell）**
- NVIDIA《Recipes for Pre-training LLMs with MXFP8》（2025-06）：OCP 规范建议的舍入模式会导致预训练发散，改用 round-to-infinity 计算 scale 后 **8B 模型 15T token MXFP8 预训练成功** — [arXiv 2506.08027](https://arxiv.org/abs/2506.08027)（A(摘要)）
- torchtitan MXFP8（torchao kernel）：1×32 块、数据 float8_e4m3fn、scale float8_e8m0；FSDP all-gather 后 hook 把 BF16 权重量化为 32×32 方块 scale（FPROP/DGRAD 共用）；B200 单机 Llama 3 8B：mxfp8 +20.0%，float8 tensorwise +25.4%；**512 GPU GB200 集群 Llama4 Scout（FSDP256+EP16）：6169→7401 tokens/s（+20.3%），3,000 步收敛与 BF16 等价（最终 loss 略低）**；Llama 3 8B 在 4×GB300 上 3,000 步确定性对比与 BF16 紧贴；"2K+ GPU Crusoe B200 集群预训练最高 1.28× 加速"案例 — [torchtitan/quantization/mxfp8/README.md](https://github.com/pytorch/torchtitan/blob/main/torchtitan/quantization/mxfp8/README.md)（A）
- NVIDIA Megatron-Bridge 26.08.01 官方表：**所有 GB300/GB200 MoE 基准默认 MXFP8**（DeepSeekV3、DeepSeekV4 Flash、GPT-OSS、Qwen3）；MoE 基准"强制均衡专家 token 分布且无丢 token" — [performance-summary.md](https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/main/docs/performance-summary.md)（A）
- 同一表中 Llama 3.1 405B 在 GB300 上 FP8（tensorwise/delayed）2646 TFLOPS 高于 MXFP8 2403；Llama3 70B 同样 FP8 略高于 MXFP8 — [performance-summary-archive.md 26.06](https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/main/docs/performance-summary-archive.md)（A）
- TE v2.19（2026-09）增加 **MXFP8 EP 通信**；Triton-distributed FlashComm（2026-09）支持 MXFP8 打包的 EP dispatch — [TE project_updates](https://github.com/NVIDIA/TransformerEngine/blob/main/docs/project_updates.rst)、[Triton-distributed README](https://github.com/ByteDance-Seed/Triton-distributed/blob/main/README.md)（A）

**NVFP4 / FP4（Blackwell、Ascend、TPU）**
- NVFP4 配方（TE `NVFP4BlockScaling`）：两级缩放——每 16 个连续值共享 E4M3 scale + 每张量 FP32 全局 scale；权重用 16×16 二维块共享 scale；梯度量化用随机舍入；输入与梯度做 16×16 随机 Hadamard 变换平滑离群值；因行/列方向量化后不等价，前后向都从高精度源量化；`4over6` 自适应块缩放当前面向 RL/后训练，预训练路径尚未与 RHT 组合 — [TE recipe/__init__.py](https://github.com/NVIDIA/TransformerEngine/blob/main/transformer_engine/common/recipe/__init__.py)（A）
- 《Pretraining LLMs with NVFP4》（2025-09）：RHT + 二维量化 + 随机舍入 + 选择性高精度层；**12B 模型训练 10T token，"迄今最长的 4-bit 公开训练"** — [arXiv 2509.25149](https://arxiv.org/abs/2509.25149)（A(摘要)）
- **生产案例**：Nemotron 3 Super（120B-A12B）"家族首个 NVFP4 预训练模型"，25T token（2026-04）；Nemotron 3 Ultra（550B-A55B）NVFP4 预训练 20T token + 1M 上下文（2026-06）；Nemotron 3 白皮书（2025-12）称 Super 与 Ultra 用 NVFP4 训练 — [arXiv 2604.12374](https://arxiv.org/abs/2604.12374)、[arXiv 2606.15007](https://arxiv.org/abs/2606.15007)、[arXiv 2512.20856](https://arxiv.org/abs/2512.20856)（A(摘要)）；Megatron-Bridge 官方表给出 Nemotron 3 Ultra 在 256×GB300 上 NVFP4 3744 tok/s/GPU、1348 TFLOPS/GPU，Super 64×GB300 NVFP4 839 TFLOPS（略高于 MXFP8 817） — [performance-summary.md](https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/main/docs/performance-summary.md)（A）
- NVIDIA 官方基准（26.06）：Llama 3.1 405B 256×GB300 **NVFP4 3575 TFLOPS/GPU（1413 tok/s/GPU）vs FP8 2646（1048）**，即 1.35×；GB200：NVFP4 2944 vs FP8 2129（1.38×） — [performance-summary-archive.md](https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/main/docs/performance-summary-archive.md)（A）
- MLPerf Training v5.1（2025-11）：NVIDIA 称 NVFP4 训练配方使同一 GB200 NVL72 架构较上一轮 FP8 提交最高 1.4× — [NVIDIA 博客](https://blogs.nvidia.com/blog/mlperf-training-benchmark-blackwell-ultra/)（C，**未核实**）；DGX Cloud 基准中 Llama 3.1 8B（MLPerf）在 GB200 上以 NVFP4 运行 — [dgxc-benchmarking README](https://github.com/NVIDIA/dgxc-benchmarking/blob/main/README.md)（A）
- torchtitan NVFP4（实验性，依赖 torchao 原型）：保留末尾约 15% decoder 层与 LM head 为 BF16，GEMM 局部维度需 128 整除；Llama 3 8B 200M token：NVFP4 30,040 tok/s/GPU、110.95 GiB vs MXFP8 28,084 / 179.94 GiB vs BF16 21,919 / 174.49 GiB，loss 相当；Qwen3 8B：NVFP4 较 BF16 +28% 吞吐、内存 −34%；建议在 lr 衰减前切回高精度（论文附录 D：仅把前向 GEMM 切 BF16 可把相对 loss 误差从 ~1.5% 降到 ~0.5%，仅增加 ~6% 高精度计算，但 torchtitan 暂不支持只切前向） — [torchtitan/quantization/nvfp4/README.md](https://github.com/pytorch/torchtitan/blob/main/torchtitan/quantization/nvfp4/README.md)（A）
- Megatron-Core：NVFP4 "actively evolving"，PP 支持为 partial，推理 partial，不支持优化器 CPU offload；B200 FP4 cookbook 要求首尾各 2 层 BF16；2026 Q2 路线图含 NVFP4 param gather、MXFP8/NVFP4 混合精度 — [low_precision_training.md](https://github.com/NVIDIA/Megatron-LM/blob/main/docs/user-guide/features/low_precision_training.md)（A）
- 稳定性研究（2025-11 至 2026-07）：TetraJet-v2（振荡抑制与离群控制）、Four Over Six（自适应块缩放，已进 TE）、Dissecting Outlier Dynamics（NVFP4 预训练中离群值从早期瞬态尖峰演化为少数持久"热通道"，Softmax/门控/SwiGLU 为来源，提出 HCP/CHON）、Stable FP4 via Transposition-Invariant 2D Block Quantization（1D 块缩放因转置导致前后向 scale 不一致是不稳定根源；Q/K 投影用 MXFP8）、UFP4（E2M1 非均匀格点的"收缩偏差"随层累积并被 RHT 放大，主张 E1M2/INT4 均匀格点）、《Practical FP4 for MoE on Hopper》 — [arXiv 2510.27527](https://arxiv.org/abs/2510.27527)、[2512.02010](https://arxiv.org/abs/2512.02010)、[2602.02047](https://arxiv.org/abs/2602.02047)、[2607.24953](https://arxiv.org/abs/2607.24953)、[2606.20381](https://arxiv.org/abs/2606.20381)（A(摘要)）
- 非 NVIDIA 平台：华为 HiFloat4（Ascend 上 dense/MoE 全 FP4 GEMM，相对误差 <1%）；Google TPU 8t 原生 FP4（12.6 PFLOPs）面向预训练；AMD Primus 支持 MXFP4 recipe 与 FP4 grouped GEMM（MegaMoE） — [arXiv 2604.08826](https://arxiv.org/abs/2604.08826)（A(摘要)）、[TPU 8t 博客](https://cloud.google.com/blog/products/compute/tpu-8t-and-tpu-8i-technical-deep-dive)、[Primus README](https://github.com/AMD-AGI/Primus/blob/main/README.md)（A）
- 峰值口径：NVIDIA 基准仓库给出 NVFP4 非稀疏峰值 GB300 14,700 / GB200 9,800 / B300 13,500 / B200 9,000 TFLOPS，H100 不支持 — [dgxc-benchmarking README](https://github.com/NVIDIA/dgxc-benchmarking/blob/main/README.md)（A）

### Inferences
- "2026 年是否出现 FP4 训练的生产案例"：**是，但仅限 NVIDIA 自家 Nemotron 3 Super/Ultra**（开源权重与配方，20–25T token），以及 MLPerf 提交与 NVIDIA/Google 的基准；中国头部实验室公开报告（DeepSeek、Kimi、Qwen、GLM、MiniMax）在 2026-10 前没有 FP4 预训练生产案例，Kimi 甚至不用 FP8 计算。对 H800/H20 用户，可落地的是"FP8 计算 + MXFP4 激活/EP 通信压缩"（2603.02731）这类无需 FP4 Tensor Core 的方案。
- NVFP4 相对 FP8 的实测增益（1.35–1.38×）远低于峰值比（2–3×），且 MoE 上更小（Nemotron Super NVFP4 仅比 MXFP8 快 ~3%），说明 FP4 的收益集中在大 GEMM 的 dense 模型；MoE 的瓶颈在通信与小 GEMM。
- "相对 BF16 峰值"口径下 GB300 上 Llama 405B FP8 的 MFU 已 >100%，各家报告 MFU 时若不说明峰值基准，跨平台比较没有意义；推荐团队内部对标应固定按"所用精度的非稀疏峰值"。

### Gaps
- NVIDIA 关于 NVFP4 在 Nemotron 3 Ultra 上的收敛/精度对比细节（报告 PDF 在 research.nvidia.com，不可达）。
- MLPerf v5.1/v6.0 各提交使用的精度（NVFP4 vs FP8）在结果仓库日志中需逐条解析，本次未做。
- FP8 训练在推荐/排序稠密塔上的公开案例未找到。

---

## 关键问题 5：MoE 训练——专家并行、负载均衡、通信优化与 MoE/dense 的 MFU 对比

### Takeaway
MoE 训练系统的三条主线在 2025–2026 收敛：(1) 通信——从 NCCL all-to-all 走向 GPU 发起的 RDMA 分发库（DeepEP v2/v2.5、NCCL EP、HybridEP、UBEP、Triton-distributed FlashComm），并把 EP 通信与 1F1B 流水/延后 wgrad 重叠；(2) 负载均衡——aux-loss-free 的专家 bias（DeepSeek）成为 Megatron 内置选项，Kimi 用小 EP 放松均衡约束，K3 宣称"完美均衡的 EP 训练"，推理/后训练则出现动态冗余专家（MoonEP/DeepEP lb API、LLEP）；(3) 效率——官方基准显示 **MoE 的 Model TFLOPS/GPU 只有同平台 dense 的 40–60%**（GB300：DeepSeek-V3 1648 vs Llama 405B FP8 2646；H100：Qwen3-30B-A3B 203 vs Llama 405B 822），细粒度专家数越多（Kimi K2 384 专家 1099 TFLOPS、Qwen3-235B 128 专家 1335）越低。

### Cited Findings

**专家并行与通信库**
- DeepEP（2026-09-30 提交）：V2 全面重构 EP，支持更大 scale-up/scale-out 域，**轻量 NCCL Gin 后端（可复用 NCCL communicator）**，JIT 编译 kernel（DeepJIT），高吞吐与低延迟 API 统一为 `EPBuffer`，SM/QP 数量解析式计算（无需 auto-tune）；V2.5 增加 Engram、PP、bucket 集合通信（all-gather/reduce-scatter/all-reduce，供 CP/DP 用）、动态冗余专家 API，**完全移除 V1 与 NVSHMEM 依赖**；要求 Hopper+、节点内 NVLink、节点间 RDMA；"EP dispatch/combine 需要 GPU SM，不支持零 SM 的 RDMA EP"；另有 Ascend 950 版本 — [DeepEP README](https://github.com/deepseek-ai/DeepEP/blob/main/README.md)（A）
- Megatron-Core MoE：Flex Dispatcher 可选 DeepEP 后端（去除跨节点冗余 token，节点内/间通信融合为单 kernel）或 **HybridEP 后端（NVIDIA 优化，TMA + IBGDA，更少 SM，原生 MNNVL，面向 GB200 NVL72）**；批级重叠隐藏 EP A2A（`--overlap-moe-expert-parallel-comm --delay-wgrad-compute`）；GroupedGEMM 含 FP8/MXFP8；FP8 权重 + BF16 优化器状态；CUDA Graph 细粒度作用域；DeepSeek-V3/V3.2、Qwen3-Next、GPT-OSS、Kimi 支持；"对 DeepSeek-V3 这类超大 MoE，EP 通信可能超过 NVLink 带宽，此时用 1F1B A2A Overlap" — [moe/README.md](https://github.com/NVIDIA/Megatron-LM/blob/main/megatron/core/transformer/moe/README.md)（A）
- NCCL EP（2026-03）：完全基于 NCCL Device API 的 MoE 通信库，统一 `ncclEpDispatch/ncclEpCombine`，LL 模式（1–128 token，直接 all-to-all RDMA+NVLink 网格，双缓冲重叠）与 HT 模式（≥4096 token，NVLink 域内先聚合再跨节点 RDMA）；H100 集群评估并集成 vLLM — [arXiv 2603.13606](https://arxiv.org/abs/2603.13606)（A(摘要)）
- COMET/Flux（字节）：MoE 层通信占比可达 47%，细粒度重叠 1.96×/1.71×，万卡生产采用（见问题 3）；MegaScale-MoE 1.88× vs Megatron-LM（B，未核实）；Triton-distributed FlashComm 系列（2026-06 至 09）：Hopper/Blackwell 上融合 dispatch+FC1 / FC2+combine、跨节点多 NIC EP、固定 buffer 分块 EP（峰值 EP 内存不随最坏 token 数增长）、MXFP8 打包 EP — [Triton-distributed README](https://github.com/ByteDance-Seed/Triton-distributed/blob/main/README.md)（A）
- DisagMoE（2026-05）：注意力与 FFN 分到不同 GPU 组，单向多对多多级流水，roofline 模型分配 GPU 与网络带宽，Megatron-LM 上 16 节点×8 H800 最高 1.8× — [arXiv 2605.11005](https://arxiv.org/abs/2605.11005)（A(摘要)）
- MoEBlaze（MLSys'26）：消除 token 路由缓冲与中间张量物化，协同设计 kernel 与智能激活 checkpoint，**>4× 加速、>50% 内存节省** — [arXiv 2601.05296](https://arxiv.org/abs/2601.05296)（A(摘要)）
- Piper（2026-05）：MoE 在 HPC 平台的资源建模 + 流水化混合并行，较 X-MoE 等 2–3.5× MFU，新 all-to-all 算法较厂商实现 1.2–9× 带宽 — [arXiv 2605.05049](https://arxiv.org/abs/2605.05049)（A(摘要)）
- AMD MegaMoE（2026-07）：把专家 all-to-all 折叠进 grouped GEMM，FP4 grouped GEMM — [Primus README](https://github.com/AMD-AGI/Primus/blob/main/README.md)（A）
- TE v2.19 MXFP8 EP 通信；NVIDIA "Boosting MoE Training Throughput with Advanced Fusion Kernels"（2026-06）、"Accelerating Dropless MoE Training in JAX with TE"（2026-09） — [TE project_updates](https://github.com/NVIDIA/TransformerEngine/blob/main/docs/project_updates.rst)（A，博客正文不可达）

**负载均衡**
- Megatron-Core 内置策略：`aux_loss`（micro-batch 级）、`seq_aux_loss`、`global_aux_loss`（全局 batch 跨 rank）、`sinkhorn`、**aux loss free（`--moe-router-enable-expert-bias --moe-router-bias-update-rate 1e-3`）**、`none`；默认示例 top-2/8 专家 aux_loss 系数 1e-2 — [moe/README.md](https://github.com/NVIDIA/Megatron-LM/blob/main/megatron/core/transformer/moe/README.md)（A）
- DeepSeek-V3：aux-loss-free bias + 序列级辅助损失兜底 + node-limited routing（≤4 节点）+ 不丢 token — [DeepSeek-V3 §2.1.2](https://arxiv.org/abs/2412.19437)（A）
- Kimi K2：EP=16 "放松了专家均衡约束，无需额外调优即可接近最优速度"；早期专家失衡可能导致 OOM，故重计算 MoE 下投影 — [Kimi K2 §2.4](https://github.com/MoonshotAI/Kimi-K2/blob/main/tech_report.pdf)（A）
- MiniMax-M1：降低 MoE 辅助损失系数并调整并行训练配置（继续预训练阶段） — [MiniMax_M1_tech_report.pdf](https://github.com/MiniMax-AI/MiniMax-M1/blob/main/MiniMax_M1_tech_report.pdf)（A）
- Least-Loaded EP（2026-01）：训练良好的 MoE 仍显著失衡且"可能是合理的"（领域知识集中），后训练/推理无法加显式均衡时，LLEP 动态把过载设备的多余 token 与专家参数迁到空闲设备 — [arXiv 2601.17111](https://arxiv.org/abs/2601.17111)（A(摘要)）
- 动态冗余专家：DeepEP v2.5 `lb_prefetch_weights/lb_reduce_grads` + MoonEP 在线规划（训练侧，NVLink 域内集合操作） — [DeepEP README](https://github.com/deepseek-ai/DeepEP/blob/main/README.md)（A）
- NVIDIA 官方 MoE 基准"强制均衡 token 分布"——即官方 TFLOPS 是均衡上限，真实训练的失衡会进一步拉低 — [performance-summary.md 脚注](https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/main/docs/performance-summary.md)（A）
- MaxText/Trillium 案例：Mixtral 式 700B MoE 把 capacity factor 从 1.0 提到 1.5（为路由不均留缓冲）后 MFU 从 49.8% 降到 38.1%（1 pod）/35.3%（4 pod） — [maxtext custom_model.md](https://github.com/AI-Hypercomputer/maxtext/blob/main/docs/guides/optimization/custom_model.md)（A）

**超大/细粒度专家与共享专家**
- DeepSeek-V3 256 路由专家 + 共享专家（DeepSeekMoE）；Kimi K2 384 专家激活 8（稀疏度 48，"更高稀疏度收益伴随基础设施复杂度上升，折中取 48"）；Kimi K3 896 路由专家激活 16（Stable LatentMoE）；Ling-mini-2.0 1/32 稀疏；Nemotron 3 LatentMoE；LongCat-Flash 零计算专家 + 快捷连接 MoE；ERNIE 5.0 弹性路由稀疏度 — [DeepSeek-V3](https://arxiv.org/abs/2412.19437)、[Kimi K2 §2.3](https://github.com/MoonshotAI/Kimi-K2/blob/main/tech_report.pdf)（A）；[arXiv 2607.24653](https://arxiv.org/abs/2607.24653)、[2509.01322](https://arxiv.org/abs/2509.01322)、[2602.04705](https://arxiv.org/abs/2602.04705)（A(摘要)）
- Megatron-Core 支持共享专家重叠执行、dense→MoE upcycling（含运行时 upcycling、任意 EP 下加载 dense checkpoint） — [moe/README.md](https://github.com/NVIDIA/Megatron-LM/blob/main/megatron/core/transformer/moe/README.md)（A）
- 2026-08 综述把现代 MoE 组织为专家粒度/拓扑/路由自由度/均衡范围/执行结构五维，并按"专家拓扑、路由、均衡、专家并行"四个控制面分析 — [arXiv 2608.08650](https://arxiv.org/abs/2608.08650)（A(摘要)）

**MoE 与 dense 的效率对比（官方基准）**
- Megatron-Bridge 26.06 容器（Model TFLOP/s/GPU；括号为本文推算的"相对所用精度非稀疏峰值"）：
  - GB300 ×256：Llama 3.1 405B FP8 **2646（54%）**；DeepSeek-V3 MXFP8 1648（34%）；Qwen3-235B-A22B 1335（27%）；Kimi-K2 1T 1099（22%）；GPT-OSS-120B（×64）1081（22%）；Llama3-70B（×32）FP8 2083（43%）
  - GB200 ×256：Llama 405B FP8 2129（43%）；DeepSeek-V3 1292（26%）；Qwen3-235B 1092（22%）
  - H100：Llama 405B ×1024 FP8 **822（42%）**；Llama3-70B ×32 FP8 710（36%）；Qwen3-30B-A3B ×16 FP8 203（10%）；Nemotron 3 Nano ×16 FP8 328（17%）
  — [performance-summary-archive.md](https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/main/docs/performance-summary-archive.md)（A；百分比为推算）
- Megatron-Core MoE 技术报告（2026-03）：GB300/GB200 上 DeepSeek-V3-685B **1,233/1,048 TFLOPS/GPU**，Qwen3-235B 974/919；"Parallel Folding" 灵活多维并行；FP8 与 NVFP4；已用于数十亿到数万亿参数、数千 GPU 的训练 — [arXiv 2603.07685](https://arxiv.org/abs/2603.07685)（A(摘要)）
- MaxText/Trillium：dense 915B 定制模型 39.8% MFU（1 pod）；700B MoE 43.1–49.8%（capacity 1.0）/38.1%（1.5）；10T 参数稀疏度 32 的 MoE 34.5%（1 pod）/26.2%（16 pod，需跨 DCN 的流水并行） — [maxtext custom_model.md](https://github.com/AI-Hypercomputer/maxtext/blob/main/docs/guides/optimization/custom_model.md)（A）
- 国产平台：Pangu Ultra MoE 718B 6K NPU 30.0% MFU；DeepSeek-V4 后训练 Ascend SuperPOD 34.22%；ERNIE 4.5 47%（口径未明） — 见问题 2

### Inferences
- 官方基准里 dense（Llama 405B）与 MoE（DeepSeek-V3）在同一 GB300 平台的 TFLOPS 差 1.6×，在 H100 上 Qwen3-30B-A3B 与 Llama 405B 差 4×；MoE 的"每 token 激活参数少 → GEMM 小 → 算术强度低 + all-to-all"是结构性损失，不会被单点 kernel 优化抹平，所以 2025–2026 的工程重点才会集中在重叠（COMET/DualPipe/1F1B A2A）与分发库（DeepEP/NCCL EP/HybridEP）。
- 训练期负载均衡的工业共识是"aux-loss-free bias 为主 + 轻量序列级辅助损失兜底 + 拓扑感知路由（节点/NVL 域限制）"，而推理/后训练期转向动态冗余专家与 token 重路由；两者在 DeepEP v2.5 中首次合流到同一通信库。

### Gaps
- MegaScale-MoE 全文（并行策略细节、1,440 GPU 的网络拓扑）未读；Tutel 2025–2026 的更新未取证。
- DeepSeek-V3 报告之外，没有头部团队公开"均衡 vs 真实失衡"条件下的 MFU 差值。
- Kimi K3 "完美均衡的 EP 训练"的实现未公开（仅摘要）。

---

## 关键问题 6：训练数据流水线、存储与长上下文训练

### Takeaway
数据与存储侧的公开样本仍少：DeepSeek 3FS（180 存储节点、6.6 TiB/s 聚合读、FoundationDB 元数据、CRAQ 强一致，用于 dataloader 随机访问、并行 checkpoint 与 KVCache）与字节 OVERLORD（集中式 data plane、按源拆分的 loader 角色、Shadow Loader 差分 checkpoint）是 2025 年仅有的两篇生产级公开；长上下文训练已形成"CP（含动态/变长 CP）+ 混合 DP/CP 动态 mesh（ByteScale 2048K/12K GPU）+ 序列切片流水（SlimPipe）+ 稀疏注意力（DSA/MTraining）+ 分阶段 YaRN/NTK 扩展"的工具箱，1M 上下文已进入 Nemotron 3 Ultra、Kimi K3 的发布规格。

### Cited Findings

**数据流水线与存储**
- DeepSeek 3FS：利用 SSD 与 RDMA 的分布式文件系统；解耦架构聚合数千 SSD 与数百存储节点带宽；CRAQ 强一致；无状态元数据服务基于事务 KV 存储（FoundationDB）；用途：dataloader（跨计算节点随机访问样本，无需预取/shuffle）、大规模训练的高吞吐并行 checkpoint、推理 KVCache；**180 存储节点（每节点 2×200 Gbps IB、16×14 TiB NVMe）+ 500+ 客户端节点压测，带训练背景流量下聚合读约 6.6 TiB/s**；KVCache 读峰值 40 GiB/s — [deepseek-ai/3FS README](https://github.com/deepseek-ai/3FS/blob/main/README.md)（提交 2026-05-07；A）
- OVERLORD/MegaScale-Data（字节，EuroSys'26）：DP 范式 dataloader 因 attention 二次复杂度下样本分布不均导致 loader 负载失衡，且多源数据共置超出 pod 内存；解法为集中式声明式 data plane、Source Loader/Data Constructor 角色拆分与自动扩缩、Shadow Loader 差分 checkpoint；多千卡生产集群部署 — [arXiv 2504.09844](https://arxiv.org/abs/2504.09844)（A(摘要)）
- Seed1.5-VL：并行感知的数据加载、多模态工作负载均衡 — [arXiv 2505.07062](https://arxiv.org/abs/2505.07062)（B，经搜索）
- Megatron-Core：Megatron Energon 多模态数据加载、数据准备/加载指南、Multi-Storage Client（MSC）集成 — [docs/user-guide 列表](https://github.com/NVIDIA/Megatron-LM/tree/main/docs/user-guide)（A，仅目录）
- torchtitan：可 checkpoint 的数据加载（C4 预配置），DCP 异步 checkpoint，HF↔DCP 转换 — [torchtitan README](https://github.com/pytorch/torchtitan/blob/main/README.md)（A）
- Google：TPU 8t 的 TPUDirect RDMA/Storage 绕过主机 CPU，配合 Managed Lustre 10T 存储访问较 Ironwood 快 10×；Rapid Storage 随机读较区域桶快 20×；Hyperdisk Exapools EB 级块存储 — [TPU 8t 博客](https://cloud.google.com/blog/products/compute/tpu-8t-and-tpu-8i-technical-deep-dive)、[AI Hypercomputer 更新](https://cloud.google.com/blog/products/compute/whats-new-with-ai-hypercomputer)（A）
- DeepSpeed DeepNVMe（2025-06）："可负担的 I/O 扩展" — [DeepSpeed README](https://github.com/deepspeedai/DeepSpeed/blob/master/README.md)（A）
- 数据混合/数据平面研究：Mixtera（ETH，基础模型训练的 data plane）、Olmix（Stanford，数据混合框架） — [LLMSys-PaperList](https://github.com/AmberLJC/LLMSys-PaperList)（B）

**长上下文训练**
- Megatron-Core CP：按序列维切分输入与所有激活，attention 处交换 KV（类 Ring Attention），与 TP/PP/DP 组合；全激活重计算约 30% 开销，CP 可同时降低每卡计算、通信与激活；**Dynamic Context Parallelism（2026-01）对变长序列最高 1.48×**；CP 已支持 MTP 与 MLA — [context_parallel.md](https://github.com/NVIDIA/Megatron-LM/blob/main/docs/user-guide/features/context_parallel.md)、[Megatron-LM README](https://github.com/NVIDIA/Megatron-LM/blob/main/README.md)（A）
- ByteScale：HDP 动态 mesh 统一 DP/CP，数据感知分片消除短序列冗余通信、选择性 offload 压缩长序列通信、并行感知数据分配做负载均衡；**256K–2048K 上下文、>12,000 GPU** — [arXiv 2502.21231](https://arxiv.org/abs/2502.21231)（A(摘要)）
- WLB-LLM（OSDI'25）：PP 级变长文档打包 + CP 级按文档细粒度分片，内部框架平均 1.23× — [arXiv 2503.17924](https://arxiv.org/abs/2503.17924)（A(摘要)）
- SlimPipe（快手，2025-04）：均匀序列切片 + 1F1B，多 micro-batch 累积激活降为一个，重分配因果注意力的不均负载；Llama 70B 512K 上下文 MFU 最高 1.57×，2048K 仍可训 — [arXiv 2504.14519](https://arxiv.org/abs/2504.14519)（A(摘要)）
- DCP（SOSP'25，动态 CP 应对输入动态性）、BurstEngine（>1M token 序列）、FlexSP（ASPLOS'25）、AutoSP（ICLR'26，编译器序列并行）、Core Attention Disaggregation（MLSys'26）、Fully Connected Pipeline CP（MLSys'26）、FlexTrain（MLSys'26） — [LLMSys-PaperList](https://github.com/AmberLJC/LLMSys-PaperList)（B，仅标题）
- MTraining（2025-10）：动态稀疏注意力 + 均衡/分层稀疏 ring attention，Qwen2.5-3B 在 32 张 A100 上从 32K 扩到 512K — [arXiv 2510.18830](https://arxiv.org/abs/2510.18830)（A(摘要)）
- DeepSpeed ALST（2025-06）：多百万 token 序列训练 — [DeepSpeed README](https://github.com/deepspeedai/DeepSpeed/blob/master/README.md)（A）；torchtitan CP 1M 序列 — [torchtitan README](https://github.com/pytorch/torchtitan/blob/main/README.md)（A）
- 模型侧做法：DeepSeek-V3 两阶段 YaRN 4K→32K→128K（119K GPU 小时）；Kimi K2 退火末期 60B token 用 32K，YaRN 到 128K；Hunyuan-A13B 退火 8192 后两阶段 NTK-aware 到 32K→256K；MiMo-V2-Flash 原生 32k 扩 256k；Nemotron 3 Ultra 20T 后扩 1M；Kimi K3 原生 1M；Seed-OSS 原生 512K；DeepSeek-V3.2 DSA 与 GLM-5 DSA 用稀疏注意力降低长上下文训练成本；MiniMax-01 varlen ring attention 支持 1M+ — 见问题 2 各来源（A / A(摘要)）

### Inferences
- 对推荐团队最可迁移的是"数据加载的 DP 失衡与多源内存爆炸"问题（OVERLORD）与"随机访问样本 + 并行 checkpoint 共用一套高吞吐存储"（3FS）：推荐训练的样本流同样是多源、变长（用户历史序列）且 checkpoint 巨大。
- 长上下文训练的系统能力已从"能不能训 128K"变为"变长混合数据下 CP/DP 的动态调度效率"（Dynamic CP、ByteScale、WLB-LLM、Zeppelin），这与推荐中"用户序列长度高度不均"的负载均衡问题同构。

### Gaps
- 3FS 在真实训练任务中的 dataloader 吞吐与 checkpoint 时间未公开；OVERLORD 的加速倍数在摘要中被截断。
- 各家长上下文训练阶段的 GPU 小时（除 DeepSeek-V3 的 119K）未公开。

---

## 关键问题 7：公开的 MFU/吞吐基准与训练成本；GB200/GB300 NVL72 的 MLPerf 实测；H100 vs Blackwell 性价比

### Takeaway
官方可复现数据（NVIDIA Megatron-Bridge 性能页 + MLCommons 结果仓库原始日志）给出 2026 年的刻度：Llama 3.1 405B FP8 每 GPU 吞吐 **H100 326 → GB200 843 → GB300 1048 tok/s（2.6× / 3.2×）**；MLPerf Training v6.0（2026-06）新增 DeepSeek-V3 671B 预训练项，**8,192 GB300 1.96 分钟、8,192 GB200 3.19 分钟**（GB300 快 1.63×），Llama 405B 在 8,192 GB200 上 6.6–7.2 分钟；公开训练成本样本仅 DeepSeek-V3（2.788M H800 小时 / 557.6 万美元）、Llama 4（7.38M H100 小时）、MiniMax-M1 RL（512 H800×3 周 / 53 万美元）、Seed1.5-VL（1.3M GPU 小时，B）。

### Cited Findings

**官方训练吞吐表（NVIDIA Megatron-Bridge，GBS/序列见原表）**
- 26.08.01 容器：DeepSeekV3 256×GB300 MXFP8 **6288 tok/s/GPU、1636 TFLOPS**（PP2/EP32/VP8）；256×GB200 4912/1277（PP4/EP64）；DeepSeekV4 Flash 128×GB300 9184/834、GB200 7968/725（EP32）；GPT-OSS-120B 64×GB300 33024/1077；Qwen3-30B-A3B 8×GB300 44544/1023；Qwen3-235B 256×GB300 8832/1306；Nemotron 3.5 Lightning 8×GB300 34816/973；Nemotron 3 Super 64×GB300 NVFP4 10240/871；Nemotron 3 Ultra 256×GB300 NVFP4 3744/1348 — [performance-summary.md](https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/main/docs/performance-summary.md)（A）
- 26.06 容器（含 H100）：Llama 3.1 405B（8192 序列、GBS 1536）：GB300 FP8 1048 tok/s/GPU（2646 TFLOPS，TP4/PP8/VP4）、NVFP4 1413（3575）；GB200 FP8 843（2129，TP4/PP16）、NVFP4 1166（2944）；**H100 ×1024 FP8 326（822，TP8/PP8/CP2/VP8）**；Kimi K2 256×GB300 MXFP8 5372/1099；Llama3-70B 32×GB300 FP8 4819/2083 vs 32×H100 1638/710 — [performance-summary-archive.md](https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/main/docs/performance-summary-archive.md)（A）
- DGX Cloud 基准仓库：峰值表（见问题 4）；H100 DeepSeek V3 需 1024 GPU、Qwen3-235B H100 仅 BF16（EP16 的 EFA 跨节点 EP 通信问题 Megatron-Bridge #3343） — [dgxc-benchmarking README](https://github.com/NVIDIA/dgxc-benchmarking/blob/main/README.md)（A）

**MLPerf Training（官方结果仓库日志，时间 = run_stop − run_start）**
- v6.0（2026-06）NVIDIA 提交：deepseekv3_671b——**8,192 GB200（128×NVL72，"Tyche-hsg"）3.19/3.23 分钟**；4,096 GB200 4.83/4.85；2,048 GB200 7.84/8.15；512 GB300（8×NVL72，"Theia"）17.5；256 GB300 33.4–34.1；llama31_405b——2,048 GB300 17.66/18.51 分钟；512 GB300 58–62；5,120 GB200 9.99/10.67（25.09 容器）；2,560 GB200 18.79；gpt_oss_20b 512 GB300 7.2–7.7 分钟；llama31_8b 512 GB300 4.5–4.8 — [mlcommons/training_results_v6.0 NVIDIA/results](https://github.com/mlcommons/training_results_v6.0)（A，本文从日志计算）
- v6.0 CoreWeave：**8,192 GB300（2048 节点×4）deepseekv3_671b 1.96 分钟**；4,096 GB300 2.98/3.03；2,048 GB300 5.46/5.54（PyTorch NVIDIA Release 26.04） — [training_results_v6.0 CoreWeave](https://github.com/mlcommons/training_results_v6.0)（A）；CoreWeave 新闻稿称"约两分钟、本轮最快" — [BusinessWire](https://www.businesswire.com/news/home/20260616994797/en/CoreWeave-Sets-New-AI-Training-Records-in-MLPerf%C2%AE-Training-v6.0-Training-DeepSeek-V3-in-Approximately-Two-Minutes/)（C）
- v6.0 Azure：**8,192 GB200（128×NVL72）llama31_405b 6.64/7.21 分钟**（NeMo 25.09）；Google：256 GB200（64 节点，4 个 NVLink 域）deepseekv3_671b 49.4 分钟；AMD：8×MI355X llama31_8b 86.3 分钟、llama2_70b_lora 7.9 分钟（Primus 0.2.0），8×MI350X 107.2 / 9.8 分钟 — [training_results_v6.0](https://github.com/mlcommons/training_results_v6.0)（A）
- v5.1（2025-11）NVIDIA 系统列表：GB200 1,152 / 2,560 / 5,120 GPU（"hsg"）与 GB300 8–512（"theia"）；NVIDIA 称 2,560 GPU Llama 405B 18.79 分钟较上轮 2,496 GPU 快 45%、NVFP4 带来最高 1.4×、5,000+ Blackwell GPU 10 分钟纪录、GB300 较 Hopper 同 GPU 数 >4× — [training_results_v5.1](https://github.com/mlcommons/training_results_v5.1)（A，系统清单）、[NVIDIA 博客](https://blogs.nvidia.com/blog/mlperf-training-benchmark-blackwell-ultra/)（C，倍数**未核实**）
- v6.0 提交者含 Azure、CoreWeave、Google、Nebius、Oracle、Lambda、SCITIX、vultr、tinycorp 等 25 家 — [training_results_v6.0 根目录](https://github.com/mlcommons/training_results_v6.0)（A）

**TPU / GPU 云基准**
- Google gpu-recipes：A4（B200）MaxText Llama 3.1 405B 预训练 **1520 TFLOP/s/device**（文档按 BF16 峰值 2237 计 eMFU 67.96%）、70B 1507；A3 Ultra（H200）405B 日志 508 TFLOP/s/device（文档公式自相矛盾：写 903/989=0.514=91.3%） — [gpu-recipes a4 llama3-1-405b README](https://github.com/AI-Hypercomputer/gpu-recipes/blob/main/training/a4/llama3-1-405b/maxtext-pretraining-gke/README.md)、[a3ultra README](https://github.com/AI-Hypercomputer/gpu-recipes/blob/main/training/a3ultra/llama3-1-405b/maxtext-pretraining-gke/README.md)（A，数字口径存疑）
- MaxText 公开：Llama2-70B v5p-128 65% MFU，Mixtral 8x7B 54.89%；Trillium 定制模型 26–50%（见问题 5） — [maxtext docs](https://github.com/AI-Hypercomputer/maxtext/blob/main/docs/reference/architecture/architecture_overview.md)（A）
- TPU 8t 较 Ironwood 2.7× 性能/美元（训练），2× 性能/瓦 — [TPU 8t 博客](https://cloud.google.com/blog/products/compute/tpu-8t-and-tpu-8i-technical-deep-dive)（A，厂商自述）

**公开训练成本**
- DeepSeek-V3：2.788M H800 小时、557.6 万美元（2 美元/小时），不含研究与消融 — [DeepSeek-V3 Table 1](https://arxiv.org/abs/2412.19437)（A）；媒体转述 Hassabis 称成本"被低报且有误导"、SemiAnalysis 估硬件支出 >5 亿美元 — [36kr 英文](https://eu.36kr.com/en/p/3780728378776838)（C，**未核实**）
- Llama 4：Scout 5.0M + Maverick 2.38M = 7.38M H100 小时 — [MODEL_CARD.md](https://github.com/meta-llama/llama-models/blob/main/models/llama4/MODEL_CARD.md)（A）
- MiniMax-M1：RL 512 H800 × 3 周 ≈ 53 万美元 — [MiniMax_M1_tech_report.pdf](https://github.com/MiniMax-AI/MiniMax-M1/blob/main/MiniMax_M1_tech_report.pdf)（A）
- Seed1.5-VL：预训练 1.3M GPU 小时 — [arXiv 2505.07062](https://arxiv.org/abs/2505.07062)（B，**未核实**）
- COMET 在字节"节省数百万 GPU 小时" — [arXiv 2502.19811](https://arxiv.org/abs/2502.19811)（A(摘要)）
- ReCoVer：234 GPU 小时内较 checkpoint-restart 多处理 74.9% token — [arXiv 2605.11215](https://arxiv.org/abs/2605.11215)（A(摘要)）

### Inferences
- **H100 vs Blackwell 性价比（本文推算）**：Llama 405B FP8 每 GPU 吞吐 GB200/H100 = 2.59×、GB300/H100 = 3.22×；若 GB200 每 GPU 小时租金低于 H100 的 2.6 倍，则 Blackwell 的单位 token 成本更低。NVFP4 再给 dense 模型 1.35–1.38×，使 GB300 NVFP4 对 H100 FP8 达 ~4.3× 每 GPU（与 NVIDIA 宣称的 ">4×" 一致）。MoE 的代际增益更小：DeepSeek-V3 在 GB300 上 6338 tok/s/GPU，而 DeepSeek 自家 H800 实测约 1,540（推算），约 4.1×，但两者的并行/batch/精度不可比。
- MLPerf v6.0 扩展效率（推算）：DeepSeek-V3 在 GB200 上 2,048→8,192 GPU 加速 2.46×（61%），4,096→8,192 为 1.51×（76%）；Llama 405B 2,560→5,120 GB200 1.88×，5,120→8,192 约 1.5×（94%，跨容器/提交者，仅供参考）。万卡级的"扩展损失"仍有 25–40%，与 Megatron 的 175B 强扩展（47%→42% MFU）一致。
- 公开成本只覆盖"官方训练"且多按 2 美元/H800 小时折算，无法推出各家真实 TCO；对内部对标，更可靠的是 tok/s/GPU 与 ETTR。

### Gaps
- MLPerf 日志中各提交的精度（NVFP4/FP8）与并行配置未逐条解析；Nebius/Oracle/Lambda 等 GB300/B300 结果未计算。
- NVIDIA 官方 MFU 的峰值口径（是否按稀疏/密集）在仓库文档中未说明，本文按"非稀疏"表推算。
- 各云厂商 GB200/H100 租金未取证，性价比结论止于吞吐比。
- Megatron-Bridge 的 DeepSeekV3 H100 行在归档中未找到（只有 B200/GB 系列）。

---

## 关键问题 8：对推荐/排序模型训练可迁移的经验（简要）

### Takeaway
LLM 训练系统 2025–2026 的成果中，与推荐/排序训练直接同构的有五类：ETTR/goodput 作为平台 KPI 与副本级容错；straggler 的"what-if 归因 + 节点扫查"；多源变长数据的集中式 data plane；EP/all-to-all 通信库对 embedding/多专家塔的复用；MXFP8/FP8 与 Muon 的分片格式要求（RaggedShard）。

### Cited Findings
- LinkedIn 用 DeepSpeed ZeRO++ 做推荐系统 LLM 的大规模蒸馏训练（EMNLP 2025 industry） — [DeepSpeed README 2025-11 条目](https://github.com/deepspeedai/DeepSpeed/blob/master/README.md)（A，仅条目）
- Google 公开"Scalable ML Training Infrastructure for Online Ads Recommendation and Auction Scoring Modeling at Google"（2025-01） — [arXiv 2501.10546](https://arxiv.org/abs/2501.10546)（A(标题)，摘要未读）
- MLPerf v5.1/v6.0 中 NVIDIA 仍以 HugeCTR 提交推荐基准（tyche/theia `hugectr` 系统，GB200/GB300 8–64 GPU） — [training_results_v5.1 / v6.0 系统列表](https://github.com/mlcommons/training_results_v6.0)（A）
- TPU 8t 保留 SparseCore 用于 embedding lookup，并用 VPU 重叠量化/softmax/layernorm — [TPU 8t 博客](https://cloud.google.com/blog/products/compute/tpu-8t-and-tpu-8i-technical-deep-dive)（A）
- veScale-FSDP 的 RaggedShard 面向 block-wise 量化与 Muon/Shampoo 这类非逐元素优化器 — [arXiv 2602.22437](https://arxiv.org/abs/2602.22437)（A(摘要)）
- OVERLORD 直接针对"DP 范式 dataloader 的负载失衡与多源内存"问题 — [arXiv 2504.09844](https://arxiv.org/abs/2504.09844)（A(摘要)）
- DeepEP v2.5 把 all-gather/reduce-scatter/all-reduce bucket 集合通信与 EP 分发统一在一个 GPU 发起的通信库中 — [DeepEP README](https://github.com/deepseek-ai/DeepEP/blob/main/README.md)（A）

### Inferences
- 推荐训练的 embedding all-to-all 与 MoE 的 dispatch/combine 在通信模式上同构（稀疏、按键路由、跨节点），DeepEP/NCCL EP/HybridEP 的"NVLink 域内聚合 + 跨节点 RDMA + 少量 SM"设计可直接借鉴到 NVL72 上的大 embedding 表训练。
- ByteRobust 的 97% ETTR 与 FT-HSDP 的"副本即容错单元"提示：推荐模型多为纯 DP/HSDP，天然适合副本级隔离恢复而非全任务 checkpoint-restart。
- Guard/OSDI'25 的 straggler 方法论（无 straggler 模拟 + 在线监控 + 离线扫查）对推荐训练中常见的"数据/参数服务器侧 fail-slow"同样适用。
- MXFP8（1×32 块、E8M0）对排序模型的稠密 MLP/attention 塔是低风险选项，但 embedding/交叉特征的离群值分布需要单独验证（NVFP4 的热通道研究提示离群值在特定算子集中）。

### Gaps
- 推荐专用训练系统（TorchRec、HugeCTR、字节 Monolith 后续等）的 2025–2026 更新由另一份笔记覆盖；本笔记未取证。

---

## 关键问题 9：未来 12 个月（至 2027-10）的判断

### Takeaway
基于上述证据的判断：NVFP4 预训练会从"NVIDIA 自家 Nemotron 3"扩展到少数 Blackwell/Rubin 用户，但 FP8（Hopper blockwise/tensorwise、Blackwell MXFP8）仍是全球多数生产训练的精度；Megatron-Core 的事实标准地位进一步巩固（公开开发、Megatron-Bridge、昇腾/AMD/阿里下游），torchtitan 作为 PyTorch 原生参考实现与 RL/后训练后端继续扩张；EP 通信收敛到 NCCL 原生（NCCL EP、DeepEP Gin 后端、TE MXFP8 EP）与 NVL72/超节点感知库；容错范式从 checkpoint-restart 转向副本/角色级隔离与步内恢复，ETTR 成为公开指标；Muon 类优化器与 1M 上下文成为新模型的默认项。

### Cited Findings（支撑判断的已发生事实）
- TE v2.19 已加入 Rubin 支持（2026-09）；Megatron NVFP4 2026 Q2 路线图在推进 param gather 与 MXFP8/NVFP4 混合精度 — [TE project_updates](https://github.com/NVIDIA/TransformerEngine/blob/main/docs/project_updates.rst)、[low_precision_training.md](https://github.com/NVIDIA/Megatron-LM/blob/main/docs/user-guide/features/low_precision_training.md)（A）
- TPU 8t 原生 FP4、>100 万 TPU 单集群；Anthropic 2026 年 >1 GW TPU 容量 — [TPU 8t 博客](https://cloud.google.com/blog/products/compute/tpu-8t-and-tpu-8i-technical-deep-dive)、[Anthropic](https://www.anthropic.com/news/expanding-our-use-of-google-cloud-tpus-and-services)（A）
- Muon 支持已进入 Megatron（Emerging-Optimizers，2026-04）、DeepSpeed（2026-05）、veScale-FSDP（RaggedShard）；Kimi K2/K3 用 MuonClip — 见问题 1/2（A）
- MindSpeed-LLM 对 DeepSeekV4-Flash/GLM5.2 的预训练支持（2026-04/06）、DeepEP-Ascend、SLAI T-Rex 34.22% MFU、HiFloat4 — 见问题 2（A / A(摘要)）
- 1M 上下文：Nemotron 3 全系、Kimi K3、Qwen3.5-Omni 256k、Seed-OSS 512K — 见问题 2/6
- MLPerf v6.0 新增 DeepSeek-V3 671B 与 GPT-OSS-20B 预训练项，8,192 GPU 提交成为常态（NVIDIA、Azure、CoreWeave） — [training_results_v6.0](https://github.com/mlcommons/training_results_v6.0)（A）

### Inferences（判断）
1. **精度**：到 2027-10，Blackwell/Rubin 集群上的 dense 预训练将以 NVFP4（首尾层 BF16 + 末期高精度）为常见选项，MoE 预训练主体仍为 MXFP8 + FP4 激活/通信压缩；H800/H20/昇腾上的国内团队继续 FP8 blockwise（昇腾走 HiFloat4 试点）。
2. **框架**：Megatron-Core + TE + Megatron-Bridge 为工业默认；torchtitan 在 RL/后训练与研究侧扩张（已承载 DeepSeek V4/Kimi K3 定义）；DeepSpeed 保持 offload/超芯片/微调生态位；字节继续"论文开源 + 组件开源"，veScale 新版本可能发布。
3. **并行**："PP16 × EP16–64 × ZeRO-1，TP≤2" 仍是 1T 级 MoE 的主配方；NVL72 上 EP 域扩到 64–72，HybridEP/NCCL EP/UBEP 取代 NVSHMEM 系方案；DualPipe 不会成为主流（显存翻倍），交错 1F1B + 延后 wgrad + 细粒度 offload 更常见。
4. **稳定性与 goodput**：十万卡级作业把 FT-HSDP/ReCoVer 式副本或步内恢复作为必需能力，NVRx 的 in-job restart/热备进入 NeMo 默认；ETTR ≥95% 成为万卡级平台的公开对标线。
5. **硬件**：MLPerf v7.0（2026-11）很可能出现 Rubin 与 TPU 8t/Ironwood 训练提交；GB300 NVL72 成为 2027 年前沿训练主力，H100 转向后训练/推理。
6. **风险**：FP4 的稳定性研究（收缩偏差、热通道、转置不一致）尚未收敛，若多家在 10T+ token 规模上报告 loss gap，NVFP4 预训练的普及会推迟到 Rubin 代。

### Gaps
- 以上判断缺少 OpenAI/Anthropic/Google/Meta 自研栈的直接证据（官网不可达，仅摘要与厂商博客）。
- DeepSeek V4 的训练精度与平台（NVIDIA vs 昇腾）未核实，这是判断"国产卡前沿训练"的关键缺口。

---

## 附：本次取证的主要本地资料路径（供复核）
- 技术报告 PDF→文本：`/tmp/claude-0/-home-user-mywiki/68839d70-3d19-558b-8f15-a53d47531007/scratchpad/txt/`（DeepSeek_V3、tech_report(Kimi K2)、Qwen3_Technical_Report、MiniMax_M1、MiniMax-01、Moonlight、DeepSeek_V3_2、Hunyuan_A13B）
- 官方仓库克隆：`/home/user/<org>/<repo>`（NVIDIA/Megatron-LM、NVIDIA/TransformerEngine、NVIDIA/dgxc-benchmarking、NVIDIA-NeMo/Megatron-Bridge、NVIDIA/nvidia-resiliency-ext、pytorch/torchtitan、deepspeedai/DeepSpeed、deepseek-ai/{DeepSeek-V3,DualPipe,DeepEP,3FS,profile-data,DeepGEMM,DeepSeek-V3.2-Exp}、MoonshotAI/{Kimi-K2,Moonlight,MoonEP}、volcengine/veScale、ByteDance-Seed/{VeOmni,Triton-distributed,StragglerAnalysis,Seed-OSS}、bytedance/flux、Ascend/MindSpeed-LLM、AMD-AGI/Primus、alibaba/Pai-Megatron-Patch、PaddlePaddle/ERNIE、inclusionAI/Ling-V2、Tencent-Hunyuan/Hunyuan-A13B、meta-llama/llama-models、AI-Hypercomputer/{maxtext,gpu-recipes}、AmberLJC/LLMSys-PaperList、CSQianDong/Awesome-arXiv-Daily-Reporter）
- MLPerf 结果仓库（无 checkout 克隆，按需读取日志）：`.../scratchpad/mlc/training_results_v5.1`、`training_results_v6.0`
- arXiv 摘要抽取：`.../scratchpad/papers.jsonl`、`titles.txt`（脚本 `scripts/extract_papers.py`、`dump_abs2.py`，均以 `python3 -I` 运行）
