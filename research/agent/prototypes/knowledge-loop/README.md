# 知识闭环 (Knowledge Loop) 参考实现

> 推荐架构团队“系统迭代 AI 助手”的设计验证原型: 异构工程知识接入 → 版本化知识库 → 增量同步 → DeepSearch 式迭代检索与带引用回答 → 全量对话/引用日志 → 基于日志的知识评分与策展 → 检索/答案/新鲜度/回归评测。
>
> **只依赖 Python 3.13 标准库**, 无网络、无 API Key 即可完整运行 (`python3 run_demo.py` 约 0.5s, `bash run_tests.sh` 46 个用例)。它是设计方案的参考实现, 不是产品。

## 1. 目标

验证以下设计判断在工程上是否成立, 并给出可运行的最小实现:

1. **知识可版本化、可增量更新**: 文档/代码/配置/日志能统一切成带稳定 id 的知识条目; 来源变化时只重建受影响条目, 旧版本可追溯 (valid_to / superseded_by / 墓碑)。
2. **检索可解释、可迭代**: 不依赖向量模型也能做多步检索 (BM25 + 字符 3-gram + RRF + 伪相关反馈), 每条命中给出 why; 证据不足时弃答而不是编造。
3. **每一轮对话都是可回放的数据**: 记录 query、检索到的条目 (精确到版本)、引用的条目、答案、反馈 (显式/隐式/纠错), 评分可以随时从日志重算。
4. **知识质量可度量、可策展**: 曝光/引用/反馈份额/陈旧/冲突/缺口 → 健康度与策展任务; 策展**从不静默修改知识**, 只产生带证据的任务。
5. **系统可评测、可回归**: 黄金集 + 检索指标 + 答案指标 + 新鲜度测试 + 两次评测的逐条回归对比 + 从正反馈对话挖掘黄金集候选。

## 2. 架构

```mermaid
flowchart LR
    subgraph Sources[知识来源 sample_corpus/v1 → v2]
        D[Markdown 文档] ; C[Python 代码] ; F[YAML/JSON 配置] ; L[日志]
    end
    subgraph Ingest[接入与同步]
        CN[connectors/*<br/>heading-aware / ast / yaml 子集 / Drain 模板]
        CH[chunking<br/>稳定 id · 上下文头 · 大小限制]
        SY[sync<br/>sha256 对比 → 新增/新版本/墓碑<br/>只重建受影响条目]
    end
    subgraph KB[版本化知识库 store.py (SQLite, WAL)]
        IT[(items 版本链)] ; SF[(source_files)] ; SR[(sync_runs)]
    end
    subgraph Serve[检索与问答]
        IX[index<br/>BM25 + 3-gram cosine + RRF<br/>kind/acl/as_of 过滤]
        DS[search<br/>DeepSearch 循环: 计划→检索→读取→覆盖率→PRF 扩展]
        AN[answer<br/>抽取式答案 + K-id 引用 / 弃答]
        LLM[llm<br/>HeuristicLLM 默认 / AnthropicLLM 可选]
    end
    subgraph Logs[对话与反馈日志]
        TU[(turns / retrievals / citations / feedback)]
    end
    subgraph Loop[闭环]
        SC[scoring<br/>曝光·引用·反馈份额·陈旧·冲突·缺口 → health → 策展任务]
        CQ[(curation_queue<br/>verify/update/deprecate/merge/fill_gap/promote_candidate)]
        EV[evaluate<br/>recall/MRR/nDCG · 关键词覆盖/引用精度/groundedness · 新鲜度 · 回归 · 黄金集挖掘]
    end
    Sources --> CN --> CH --> SY --> KB
    KB --> IX --> DS --> AN
    LLM -.-> DS & AN
    AN --> TU
    TU --> SC --> CQ
    KB --> SC
    TU --> EV
    KB --> EV
    CQ -. 人工确认 promote .-> KB
```

## 3. 数据模型 (`kloop/models.py` + `kloop/store.py`)

| 表 | 关键列 | 说明 |
|---|---|---|
| `sources` | id, root, last_sync_at, **sync_count** (=语料版本) | 一个 source 对应一个语料根目录, 跨版本同步按 locator 对齐 |
| `source_files` | (source_id, locator) PK, sha256, mtime, kind, first_seen_at, **last_changed_at**, deleted_at | 文件级指纹, 增量同步跳过未变文件; 陈旧判定用 last_changed_at |
| `items` | (**id**, **version**) PK, source_id, locator, kind∈{doc,code,config,log,lesson}, title, text, context_header, content_hash, valid_from, **valid_to**, **superseded_by**, metadata(json), acl(json), last_verified_at, heading_path, **status**∈{active,superseded,deleted} | 版本化知识条目; `valid_to IS NULL` 即当前有效; status=deleted 的关闭行即墓碑。索引: (source_id, locator), kind, valid_to |
| `sync_runs` | source_id, root, started_at, added, updated, unchanged, deleted, items_reindexed, details(json) | 每次同步的报告 |
| `turns` | id, session_id, user_id, query, answer, created_at, max_score, abstained, trace(json), metadata(json) | 一轮对话; trace 为 DeepSearch 轨迹 |
| `retrievals` | turn_id, **item_id, item_version**, rank, score, signals(json: rrf/bm25/bm25_norm/cosine/ranks/queries) | 该轮检索到的条目 (精确到版本) |
| `citations` | turn_id, item_id, item_version, position | 答案实际引用的条目 |
| `feedback` | turn_id, kind∈{explicit,reformulated,applied_action,task_success,correction}, value, text | 显式 ±1; 隐式 −0.5/+0.5/+0.5; 纠错文本 |
| `item_scores` | (item_id, version), exposures, citations, citation_rate, helpfulness, staleness_flags, conflict_flags, health, components, reasons | 可重算的评分快照 |
| `curation_queue` | task_type, item_ids, priority, reason, evidence(json), status∈{open,resolved,done}, **fingerprint UNIQUE** | 策展任务; fingerprint 保证重算幂等 |
| `eval_runs` | id, name, summary(json), per_query(json), corpus_version | 评测结果, 供回归对比 |

**稳定 id**: `sha1(source|locator|kind|heading_path)[:12]` (`chunking.stable_id`), 与内容无关; markdown 的 heading_path 是标题路径 (`A > B`), 代码是限定名 (`module.Class.method`), 配置是顶层 key, 日志是 `LEVEL 模板`。**物理键** `id@version` 用于索引与日志, 保证“哪一版被检索/引用”可追溯。**上下文头** `来源 | 路径 | 章节 | 版本` 作为条目文本前缀进入索引与证据。

## 4. 核心算法

### 4.1 接入 (`kloop/connectors/`)
- `markdown_docs`: 按标题层级切章节 (忽略代码块内的 `#`), 支持 front matter `acl:`; 超长章节按段落切块 (`#1/#2` 进入 heading_path); 同一文件内重复的 heading_path (两个同名章节) 自动加 `(2)`/`(3)` 后缀, 稳定 id 不碰撞。
- `python_code`: `ast` 解析, 产出模块 docstring (+ 顶层名与常量)、类 (签名 + docstring + 方法列表)、函数/方法 (装饰器 + 签名 + docstring + 前 12 行函数体摘录)。
- `config_files`: JSON 用 `json`; YAML 用自写子集解析器 (映射/列表/标量/行内列表/引号/注释, 无 PyYAML)。每个顶层 section 一条, 文本为 `key.path = value  # 注释`, `metadata.kv` 保存扁平键值对供冲突检测。
- `log_files`: Drain 风格模板挖掘: 解析时间戳/级别 → 屏蔽 `<TS> <DATE> <IP> <HEX> <PATH> <ID> <NUM>` → 按 (级别, token 数) 分桶 → 与桶内模板按位置相似度 ≥ 0.6 合并 (差异位写 `<*>`)。每模板一条: 次数/首末次出现/3 条样例/级别/关键词; 按关键词重叠把模板关联到 runbook 章节 (`metadata.related_docs`)。

### 4.2 增量同步 (`kloop/sync.py`)
```
语料目录不存在 → 直接报错 (否则会把该 source 的全部条目写成墓碑)
扫描全部文件 → 对每个 locator 比较 sha256 (source_files)
  未变  → 整个文件跳过 (不抽取、不重建索引), 其条目计 unchanged
  变化/新增 → 抽取草稿, 按稳定 id 与当前版本对比 content_hash:
      相同   → unchanged (acl、日志 related_docs 等元数据就地更新, 不产生新版本)
      不同   → 新版本 version+1; 旧版本 valid_to=now, superseded_by=id@new, status=superseded
      新 id  → 插入 (若曾有墓碑则版本号继续递增)
      消失   → 旧版本 valid_to=now, status=deleted (墓碑)
扫描不到的 locator → 其全部当前条目写墓碑, source_files.deleted_at
记录 sync_run; 若传入 Index: remove(旧键) + add(新条目) —— items_reindexed = 索引 remove/add 操作数 = 新增 + 2×更新 (移除旧版本 + 加入新版本) + 墓碑
```
演示中 v1→v2: 16 个文件只有 6 个变化 + 1 新增 + 1 删除; 条目新增 5 / 更新 9 / 墓碑 3 (索引 remove/add 共 26 次), 89 个条目未触碰, 同步后当前有效 103 条。

### 4.3 索引 (`kloop/index.py`)
- 分词: 英文/标识符 (保留整体 + `snake_case`/`CamelCase`/`key.path` 子词) + 中文二元组 (剔除停用字/停用二元组), 无需分词器。
- **BM25**: `score = Σ_t idf(t)·tf·(k1+1)/(tf + k1·(1−b+b·|d|/avgdl))`, `idf = ln(1+(N−df+0.5)/(df+0.5))`, k1=1.5, b=0.75; `bm25_norm = score / Σ_t idf(t)(k1+1)` ∈ [0,1) 作为相关度代理。
- **字符 3-gram TF-IDF 余弦**: `w = (1+ln tf)·idf`, `idf = ln((N+1)/(df+1))+1`, 文档范数在变更后惰性重算。
- **RRF**: `score(d) = Σ_r 1/(60 + rank_r(d))` 融合两路排序 (各取前 50)。
- 过滤: `kinds`, `acl` (条目 acl 含 `all` 或与用户组相交), 默认只取 `valid_to IS NULL`; 传 `as_of` 时取该时刻有效的版本。
- 每个 `Hit` 带 bm25 / bm25_norm / cosine / 两路名次 / `why` (如 `BM25 18.00 (命中: 告警, 处理, featurefetchtimeout) · 3-gram余弦 0.24 · RRF 0.0318`)。
- 支持 `add_items` / `remove_items` 增量更新。

### 4.4 DeepSearch 循环 (`kloop/search.py`)
```
plan: 原查询 + 按 和/与/and/then/，/; 切分的子句 + 标识符 (snake_case, CamelCase, key.path, 错误码, --flag)
loop (最多 4 步, 预算 40 条命中):
    取下一条待检索查询 → index.search(top_k=8) → 合并证据 (按键去重, 累加 RRF 分)
    coverage = |需求词 ∩ 前 5 条证据的词| / |需求词|   (需求词 = 查询内容词 + 标识符)
    coverage ≥ 0.8 → 停 (coverage_reached); 预算耗尽 → 停; 无待检索查询 → 伪相关反馈:
        取前 2 条证据中 idf 最高且不在查询中的 3 个词, 追加到原查询形成新查询
停止原因 ∈ {coverage_reached, budget_exhausted, no_more_queries, max_steps}
最终排序: Σ 各子查询的 RRF 分 (多跳证据被多个子查询命中会上浮)
SearchTrace 记录每步 query / 命中键 / 新证据数 / coverage / 扩展词
```
`identifier_known`: 查询中的英文标识符若**全部**不在索引词表中 (如问 Kafka 而语料无 Kafka), 视为知识库无相关内容 → 弃答 + 缺口信号。

### 4.5 答案与引用 (`kloop/answer.py`, `kloop/llm.py`)
- 证据 = 前 5 条命中。弃答条件: 无证据 / 最高 `bm25_norm` < 0.12 / 标识符全部未知。弃答答案不带引用, 但记录最接近的条目供缺口分析。
- `HeuristicLLM.compose_answer`: 把证据切句 (跳过 markdown 标题), 按“与查询词重叠率 + 标识符命中 0.3 + 文本类型偏好 (doc/lesson 0.1, config 0.05)”打分, 每条证据最多 2 句、共 6 句, 按证据名次与句序输出, 每句尾部 `[K-<id>]`; 末尾列出参考来源 `(v版本)`。答案一定至少带一条引用。
- `Answer(text, cited_item_ids, evidence_ids, versions, abstained, max_relevance)`。

### 4.6 对话与反馈 (`kloop/feedback.py`)
- `log_turn`: turns + retrievals (前 10 条, 含各信号) + citations + trace。
- `log_feedback`: explicit ±1; reformulated −0.5 (回放时由 `reformulation_of` 自动记到**上一轮**); applied_action +0.5; task_success +0.5; correction (文本)。
- 纠错文本命中 `不对|其实|应该是|实际上|错了|已经改成|现在是|…` → `curation_queue(promote_candidate)`, 证据含对话 id、当时引用的条目、候选 lesson 文本。`promote_candidate(store, task_id)` 是显式人工动作 (CLI `promote`), 才会写入 kind=lesson 的条目。

### 4.7 评分 (`kloop/scoring.py`, 幂等, 全部从日志重算)
对每个 `id@version` (当前条目 ∪ 日志中出现过的版本):
- `exposures` = 出现在检索前 10 的对话数; `citations` = 引用它的对话数; `citation_rate = citations/exposures`。
- **helpfulness** (反馈份额): 对话 t 的反馈值 `v_t = clip(显式之和 + 隐式之和, −1.5, 1.5)`; 若 t 引用了 n 条, 第 p 位的权重 `w_p = (1/p)/Σ_{j≤n}(1/j)`; `helpfulness(i) = mean_{t 引用 i} w_{pos(i,t)}·v_t`。
- **staleness_flags**: `superseded` / `tombstoned` (该版本已被替代/删除但日志里仍有它), `file_changed_since_verified` (来源文件 `last_changed_at` > 条目 `last_verified_at`, 即文件变了但该章节未变)。
- **conflict_flags**: `near_duplicate` (当前条目两两 3-token shingle Jaccard ≥ 0.6, 不同 locator 且归一化文本不同, 用倒排 shingle 剪枝); `value_mismatch` (文档中“`key.path` 默认 X”的陈述与配置取值不一致; 或不同配置文件同一 key-path 取值不同)。
- **gap**: 弃答 / `max_score` < 0.2 / 负反馈且无引用 的对话 → 按共享英文标识符或 ≥2 个共享非泛化中文词聚类 (并查集) → 缺口簇 (优先级 = 0.4 + 0.1·对话数 + 0.2·有负反馈; 标签取簇内频次最高的标识符, 同频按字典序, 保证跨进程确定)。
- **health** = `0.4·helpful + 0.3·freshness + 0.2·consistency + 0.1·usage`, 其中 `helpful = (clip(helpfulness,−1,1)+1)/2` (无反馈 0.5; 曝光≥3 但从未被引用 0.45), `freshness ∈ {1, 0.5 (file_changed), 0 (superseded/tombstoned)}`, `consistency = max(0, 1 − 0.5·冲突数)`, `usage = min(1, citations/3)`。`components` 与 `reasons` 解释每一项。
- **策展任务** (fingerprint 去重; 重算时仍成立的 open 任务刷新优先级/理由/证据, 不再成立的自动 `resolved`, 再次成立时重开):

| 类型 | 触发条件 | 优先级 |
|---|---|---|
| deprecate | 引用 ≥2 次且 helpfulness ≤ −0.5; 或条目自称“废弃/deprecated”却仍被检索到 | 0.7+ / 0.5 |
| verify | 引用后反馈偏负 (helpfulness < −0.2); 曝光 ≥3 次从未被引用; 来源文件变更后该章节未复核 | 0.6 / 0.4+ / 0.3+ |
| update | 文档与配置取值冲突 | 0.9 |
| merge | 近重复内容 | 0.7 |
| fill_gap | 缺口簇 | 0.6–1.0 |
| promote_candidate | 用户纠错抽取的候选经验 (由 feedback 产生) | 0.8 |

### 4.8 评测 (`kloop/evaluate.py`)
- 黄金集 `golden/golden_set.jsonl`: `{id, query, relevant_locators, relevant_keywords, kind, expects_version, notes[, valid_until_version]}` (缺失或 null 的字段按默认值处理); `relevant_locators=[]` 表示期望弃答; `expects_version=2` 是新鲜度条目; `valid_until_version=1` 表示该条期望在 v2 失效 (如“学习率默认 0.001”), 新鲜度子集同样遵守。
- 检索: `recall@k` (命中的相关 locator / 相关 locator 数), `MRR`, `nDCG@k` (locator 首次出现位置计 binary 增益, IDCG 按相关数), k=5,10。
- 答案: `keyword_coverage` (关键词在答案中出现的比例), `citation_precision` (引用中 locator 相关的比例), `groundedness` (答案句子与某引用条目 token 重叠 ≥ 0.5 的比例; 弃答没有断言句, 记 1.0), `abstain_ok` (弃答与期望一致)。
- 新鲜度 (expects_version ≥ 2): `top_hit_current` (以存储为准: top 命中是该 id 的最新版本且 `valid_to IS NULL`, 索引副本的状态不作数) ∧ `no_superseded_cited` (引用的每个 (id, version) 都 `valid_to IS NULL`) → `freshness_pass`。
- 回归: `compare_runs(base, new)` 只看共同 query: 汇总 Δ = 共同 query 上各指标均值之差 (两次黄金集不同时不混入条目构成的变化); 逐条 recall@10 / MRR / nDCG@10 / 关键词覆盖 任一 Δ < −0.1 标为回归、> +0.1 标为改进。
- 黄金集挖掘: 显式 +1 且 ≥1 条引用的对话 → `outputs/golden_candidates.jsonl` (不自动合并)。

## 5. 如何运行

```bash
cd research/agent/prototypes/knowledge-loop
python3 run_demo.py        # 端到端演示, < 1s, 退出码 0, 输出写入 outputs/
bash run_tests.sh          # python3 -m unittest discover -s tests -v (46 个用例)

# CLI (默认 outputs/kloop.db)
python3 -m kloop.cli init
python3 -m kloop.cli sync sample_corpus/v1
python3 -m kloop.cli search "FeatureFetchTimeout 告警怎么处理" --top-k 5 [--kinds doc,log] [--as-of 2026-10-16T00:00:00]
python3 -m kloop.cli ask "学习率默认值是多少" --user erin          # 记录对话, 打印 turn id
python3 -m kloop.cli feedback t00001 -1 --correction "不对，其实现在已经改成 0.0005 了"
python3 -m kloop.cli score && python3 -m kloop.cli curate        # 重算评分 / 查看策展队列
python3 -m kloop.cli promote 1                                    # 人工确认候选经验入库 (lesson)
python3 -m kloop.cli sync sample_corpus/v2                        # 增量同步
python3 -m kloop.cli eval golden/golden_set.jsonl --name v2 [--freshness] [--compare <run_id>]
python3 -m kloop.cli report
```
可选真实模型: `KLOOP_LLM=anthropic` + 安装 `anthropic` 包 + `ANTHROPIC_API_KEY`; 模型 id 取 `KLOOP_MODEL` (默认 `claude-opus-5-5`)。缺任一条件时自动回退 HeuristicLLM 并在 stderr 提示。

## 6. Demo 输出怎么读 (`outputs/demo_summary.md`)

| 步骤 | 看什么 | 本次结果 |
|---|---|---|
| 1 初始化 | 建表 | 12 张表 |
| 2 同步 v1 | SyncReport: 16 文件 → 101 条目 (doc 38 / code 40 / config 12 / log 11), 全部重建索引 | `outputs/sync_v1.json` |
| 3 评测 v1 | 26 条 (含 3 条期望弃答): recall@10 0.95, MRR 0.95, nDCG@10 0.89, 关键词覆盖 0.96, 引用精度 0.75, groundedness 1.00, abstain_ok 1.00 | `outputs/eval_v1.md` 逐条表 |
| 4 回放对话 | 38 轮 / 8 用户; 31 轮带引用 (82%), 7 轮弃答 (Kafka/GPU/warmup/Redis 等语料没有的内容); 50 条反馈 (3 次改写, 3 条纠错); retrievals=330, citations=131 —— 每轮都有精确到版本的检索/引用记录 | `outputs/replay_summary.json` |
| 5 评分 | Top-5 为被引用且正反馈的条目 (在线取数、OOM 处理…); Bottom-5 为反馈偏负或多次曝光未引用的代码条目; 缺口簇 gpu / kafka / warmup / connection; 冲突 1 (废弃文档与上线流程近重复, Jaccard 0.615); 队列: deprecate 1, fill_gap 4, merge 1, promote_candidate 3, verify 8 | `outputs/scores_v1.md` |
| 6 同步 v2 | 只有 17 条受影响 (新增 5 / 更新 9 / 墓碑 3, 索引 remove/add 26 次), 89 条跳过; 打印版本链 (v1 `valid_to`/`superseded_by`→v2) 与墓碑示例 | `outputs/sync_v2.json` |
| 7 新鲜度 | 7 条 expects_version=2 全部通过: top 命中为当前版本、未引用被替代版本、答案含新值 (0.0005 / user_click_count_7d / 灰度五阶段 / RedisConnectionReset 16 次 / warmup_steps 1000 / `_cnt_` 废弃) | `outputs/eval_freshness_v2.md` |
| 8 全量评测 + 回归 | 29 条; 与步骤 3 共同的 22 条逐项差值, 汇总 Δ 也只按这 22 条算 (recall@5 +0.023, 其余 |Δ| ≤ 0.01, 多为引用精度小幅波动, 无 >0.1 的回归); g04 因 v2 新增代码注释而召回提升 | `outputs/eval_v2.md`, `outputs/regression_v1_v2.md` |
| 9 再评分 | 陈旧标记从 {} 变为 superseded 9 / tombstoned 3 / file_changed_since_verified 21; 近重复冲突随废弃文档删除而**清除**, SOP 文档“learning_rate 默认 0.001” vs 配置 0.0005 的取值冲突**新出现** (update 任务); 3 个不再成立的任务自动 resolved; 25 条黄金集候选 | `outputs/scores_v2.md`, `outputs/golden_candidates.jsonl` |

时间戳随运行时间变化, 其余数值 (计数、指标、排序) 在同一语料与场景下是确定性的。

## 7. 与设计方案的对应

| 设计方案模块 | 本原型 | 验证了什么 |
|---|---|---|
| 知识接入层 (多源异构) | `connectors/` + `chunking.py` | 四类来源可统一为带上下文头、稳定 id 的条目; 日志可挖成模板并关联 runbook |
| 知识库 (版本化存储) | `store.py` items 版本链 + 墓碑 + as_of | 旧版本可追溯、可按时间点回看; 引用精确到版本 |
| 更新机制 (增量同步) | `sync.py` + `source_files` | 文件指纹 + 条目 content_hash 两级比对, 只重建受影响条目 |
| 检索与问答 (DeepSearch) | `index.py` + `search.py` + `answer.py` | 多路召回 + RRF + 多步循环 + 覆盖率停止 + 弃答, 全部可解释 |
| 对话日志与反馈 | `feedback.py` + turns/retrievals/citations/feedback 表 | 评分与评测完全可从日志重算; 纠错可转化为候选知识 |
| 知识评估与策展 | `scoring.py` + `curation_queue` | 曝光/引用/反馈份额/陈旧/冲突/缺口 → 健康度 → 带证据的任务; 幂等、不静默改知识 |
| 评测体系 | `evaluate.py` + `golden/` | 检索/答案/新鲜度/回归四类指标; 黄金集可从正反馈对话增量挖掘 |
| 模型层 (可替换) | `llm.py` LLMClient 协议 | 启发式与真实模型同接口, 离线也能跑完整闭环 |

## 8. 如何接入真实 LLM / 向量模型

- **LLM**: 实现 `LLMClient` 协议 (`plan_queries` / `compose_answer` / `judge_relevance`) 即可; `AnthropicLLM` 是现成实现 (`client.messages.create(model, max_tokens, system, messages)`, 处理 `stop_reason == "refusal"`, 输出校验引用标记后才采用, 否则回退启发式)。`get_llm()` 按 `KLOOP_LLM` 选择。
- **Embedding**: 在 `index.py` 中把 `TrigramIndex` 替换/补充为向量索引 (保持 `add/remove/score(query, candidates) -> {key: sim}` 接口), `Index.search` 的 RRF 融合无需改动; 条目文本仍用 `KnowledgeItem.indexed_text()` (含上下文头)。
- **判别器 / 重排**: `judge_relevance` 可用于证据重排或弃答判定 (当前仅用于接口完整性); `search.coverage_of` 可替换为 LLM 判定的“信息是否足够”。
- **真实来源**: 新增 connector 只需实现 `scan(root)` 与 `extract(raw, source_id)`, 并注册到 `default_connectors()`; 稳定 id 规则保持不变即可享受增量同步。

## 9. 局限与下一步

- **无真实 embedding**: 字符 3-gram 余弦只能捕捉表面相似, 同义改写召回有限; 中文用二元组而非分词。
- **启发式判别**: 覆盖率、弃答阈值 (0.12)、缺口阈值 (0.2)、冲突 Jaccard (0.6) 都是在 toy 语料上调的常数; 抽取式答案只能拼接原句, 不能综合。
- **toy 语料**: 16 个文件 / ~100 条目 / 38 轮模拟对话, 指标数值不代表真实效果, 只用于验证机制; 黄金集的 `relevant_locators` 是文件级而非条目级。
- **冲突检测范围窄**: 只覆盖近重复与“文档默认值 vs 配置值”; 标识符重命名 (如 `user_click_cnt_7d`) 导致的过期引用未检测 (可基于 `metadata.kv` 与标识符索引扩展)。
- **ACL** 只有组级过滤, 无行级审计; **索引不持久化** (CLI 每次从 store 重建, 服务化时应常驻 + 按 sync 报告增量更新)。
- **下一步**: 接入真实向量模型与 LLM 判别; 条目级黄金集与标注工具; 策展任务的处理流程 (认领/驳回/回写来源); 日志模板 → 告警 → runbook 的自动关联评测; 多 source 与权限模型; 把评测跑进 CI 作为知识库变更的门禁。

## 10. 文件清单

```
knowledge-loop/
  README.md  run_demo.py  run_tests.sh
  kloop/      __init__ models store chunking sync index search answer llm feedback scoring evaluate cli
  kloop/connectors/  __init__ markdown_docs python_code config_files log_files
  sample_corpus/v1  docs(7) code(4) configs(3) logs(2, 230 行)   sample_corpus/v2  同结构 (6 改 / 1 增 / 1 删 / 新日志模板)
  golden/golden_set.jsonl (33 条)   scenarios/conversations.jsonl (38 轮, 8 用户)
  tests/  test_connectors test_sync test_index test_scoring test_evaluate (+helpers)
  outputs/  demo 生成的 json/md 报告 (*.db 已 .gitignore)
```
