"""基于日志的知识条目评分 (幂等, 可随时从日志重算)。

每个条目 (id@version):
- exposures: 出现在检索结果 (rank<=10) 的对话数; citations: 被引用的对话数; citation_rate = citations/exposures。
- helpfulness: 引用它的每个对话的反馈值 (显式 ±1 + 隐式: 改写 -0.5, 采纳/任务成功 +0.5) 按引用位次权重
  w_i = (1/i)/Σ(1/j) 分摊后, 对该条目取平均。
- staleness: superseded / tombstoned / file_changed_since_verified (来源文件在 last_verified_at 之后变化)。
- conflict: near_duplicate (3-token shingle Jaccard >= 0.6 且归一化文本不同, 不同 locator);
  value_mismatch (文档中出现的 key.path 取值与配置不一致, 或不同配置文件同一 key-path 取值不同)。
- gap: max_score 低于阈值 / 弃答 / 负反馈且无引用 的对话, 按共享标识符聚类。
- health = 0.4*helpful + 0.3*freshness + 0.2*consistency + 0.1*usage (各分量见 components)。
- 策展任务: verify / update / deprecate / merge / fill_gap (promote_candidate 由 feedback 产生), 带优先级与证据。
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .index import tokenize
from .models import CurationTask, ItemScore, KnowledgeItem, utc_now
from .search import extract_identifiers
from .store import Store

GAP_SCORE_THRESHOLD = 0.2
NEAR_DUP_JACCARD = 0.6
KEYPATH_RE = re.compile(  # 文档中“key.path 默认 <值>”的陈述 (只认默认值表述, 避免把“把 x 设为 true”的操作指令当作冲突)
    r"`?(?<![\w.])([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+)`?\s*(?:的)?(?:默认值为|默认值是|默认为|默认是|默认值|默认|缺省为|缺省值|缺省|defaults? to|default)\s*[:：=]?\s*`?"
    r"([-+]?\d[\d.e+-]*%?|true|false|[A-Za-z_][\w./-]*)`?"
)
GENERIC_TOKENS = {"在哪", "哪里", "配置", "设置", "什么", "错误", "处理", "申请", "使用", "需要", "怎样", "如何", "方法", "问题",
                  "里配", "置文", "文件", "是什", "么配", "么意", "意思", "怎么", "多少", "出现"}
DEPRECATED_RE = re.compile(r"废弃|deprecated|obsolete|已下线", re.I)
RECOMPUTED_TYPES = ("verify", "update", "deprecate", "merge", "fill_gap")


def _ranked(counter: Counter) -> list[str]:
    """按频次降序、同频按字典序 (不依赖 set/Counter 的插入顺序, 否则 hash 随机化会让缺口标签与 fingerprint 每次运行不同)。"""
    return [t for t, _ in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))]


def rank_weights(n: int) -> list[float]:
    raw = [1.0 / i for i in range(1, n + 1)]
    total = sum(raw) or 1.0
    return [r / total for r in raw]


def shingles(text: str, n: int = 3) -> set[str]:
    toks = tokenize(text)
    return {" ".join(toks[i:i + n]) for i in range(len(toks) - n + 1)}


def _norm_value(v: str) -> str:
    s = v.strip().strip("`'\"").lower()
    try:
        return repr(float(s))
    except ValueError:
        return s


@dataclass
class GapCluster:
    key: str
    identifiers: list[str]
    turn_ids: list[str]
    queries: list[str]
    priority: float
    negative_feedback: int = 0


@dataclass
class ScoringReport:
    scores: list[ItemScore]
    gaps: list[GapCluster]
    tasks: list[CurationTask]
    resolved_tasks: int
    computed_at: str
    conflicts: list[dict] = field(default_factory=list)

    def tasks_by_type(self) -> dict[str, list[CurationTask]]:
        out: dict[str, list[CurationTask]] = defaultdict(list)
        for t in self.tasks:
            out[t.task_type].append(t)
        return dict(sorted(out.items()))

    def top(self, n: int = 5) -> list[ItemScore]:
        return sorted(self.scores, key=lambda s: (-s.health, -s.citations, s.key))[:n]

    def bottom(self, n: int = 5) -> list[ItemScore]:
        return sorted(self.scores, key=lambda s: (s.health, -s.exposures, s.key))[:n]


def detect_near_duplicates(items: list[KnowledgeItem], threshold: float = NEAR_DUP_JACCARD) -> list[tuple[str, str, float]]:
    """返回 (key_a, key_b, jaccard) 冲突对; 仅比较不同 locator、归一化文本不同的当前条目。"""
    sh = {it.key: shingles(it.text) for it in items if len(it.text) >= 40}
    sh = {k: v for k, v in sh.items() if len(v) >= 8}
    postings: dict[str, list[str]] = defaultdict(list)
    for key, s in sh.items():
        for g in s:
            postings[g].append(key)
    shared: Counter = Counter()
    for g, keys in postings.items():
        if len(keys) > 30:
            continue
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                shared[(min(keys[i], keys[j]), max(keys[i], keys[j]))] += 1
    by_key = {it.key: it for it in items}
    out = []
    for (a, b), n in shared.items():
        sa, sb = sh[a], sh[b]
        if n < threshold * max(len(sa), len(sb)):
            continue
        ia, ib = by_key[a], by_key[b]
        if ia.locator == ib.locator:
            continue
        if re.sub(r"\s+", " ", ia.text).strip() == re.sub(r"\s+", " ", ib.text).strip():
            continue
        j = n / len(sa | sb)
        if j >= threshold:
            out.append((a, b, round(j, 3)))
    return sorted(out)


def detect_value_conflicts(items: list[KnowledgeItem]) -> list[dict]:
    """文档中的 key.path 取值 vs 配置取值; 不同配置文件之间同一 key-path 取值不同。"""
    out: list[dict] = []
    cfg: dict[str, list[tuple[str, KnowledgeItem]]] = defaultdict(list)
    for it in items:
        if it.kind == "config":
            for kp, val in (it.metadata.get("kv") or {}).items():
                cfg[kp].append((val, it))
    for kp, entries in sorted(cfg.items()):
        vals = {_norm_value(v) for v, _ in entries}
        if len(vals) > 1:
            out.append({"type": "value_mismatch", "path": kp, "keys": sorted({e.key for _, e in entries}),
                        "detail": "; ".join(f"{e.locator}={v}" for v, e in entries)})
    short: dict[str, list[str]] = defaultdict(list)
    for kp in cfg:
        short[kp.rsplit(".", 1)[-1]].append(kp)
    for it in items:
        if it.kind not in ("doc", "lesson"):
            continue
        for m in KEYPATH_RE.finditer(it.text):
            path, val = m.group(1), m.group(2)
            target = path if path in cfg else None
            if target is None:
                cands = short.get(path.rsplit(".", 1)[-1], [])
                target = cands[0] if len(cands) == 1 and cands[0].endswith(path) else None
            if target is None:
                continue
            for cval, citem in cfg[target]:
                if _norm_value(cval) != _norm_value(val):
                    out.append({"type": "value_mismatch", "path": target, "keys": [it.key, citem.key],
                                "detail": f"文档 {it.locator} 写 {val}, 配置 {citem.locator} 为 {cval}"})
    return out


def detect_gaps(store: Store, turns, fb_by_turn, cites_by_turn, threshold: float = GAP_SCORE_THRESHOLD) -> list[GapCluster]:
    cands = []
    for t in turns:
        fbs = fb_by_turn.get(t.id, [])
        neg = any(f.kind == "explicit" and f.value < 0 for f in fbs)
        if t.abstained or t.max_score < threshold or (neg and not cites_by_turn.get(t.id)):
            cands.append((t, neg))
    if not cands:
        return []
    feats = []
    for t, _ in cands:
        toks = {x for x in tokenize(t.query) if len(x) > 1 and x not in GENERIC_TOKENS}
        latin = {x for x in toks if x.isascii() and len(x) >= 3}
        idents = {i.lower() for i in extract_identifiers(t.query)} | latin
        feats.append((idents, toks - latin))
    parent = list(range(len(cands)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(len(cands)):
        for j in range(i + 1, len(cands)):
            if feats[i][0] & feats[j][0] or len(feats[i][1] & feats[j][1]) >= 2:
                parent[find(i)] = find(j)
    groups: dict[int, list[int]] = defaultdict(list)
    for i in range(len(cands)):
        groups[find(i)].append(i)
    clusters = []
    for members in groups.values():
        idents = Counter(x for i in members for x in feats[i][0])
        toks = Counter(x for i in members for x in feats[i][1])
        label = _ranked(idents)[0] if idents else "+".join(_ranked(toks)[:2])
        neg = sum(1 for i in members if cands[i][1])
        clusters.append(GapCluster(key=label, identifiers=sorted(idents), turn_ids=[cands[i][0].id for i in members],
                                   queries=[cands[i][0].query for i in members],
                                   priority=round(min(1.0, 0.4 + 0.1 * len(members) + 0.2 * (neg > 0)), 2), negative_feedback=neg))
    return sorted(clusters, key=lambda c: (-c.priority, c.key))


def compute_scores(store: Store, now: str | None = None) -> ScoringReport:
    now = now or utc_now()
    all_items = store.all_items()
    by_key = {it.key: it for it in all_items}
    turns = store.turns()
    retrievals, citations, feedback = store.retrievals(), store.citations(), store.feedback()
    cites_by_turn: dict[str, list] = defaultdict(list)
    for c in citations:
        cites_by_turn[c.turn_id].append(c)
    fb_by_turn: dict[str, list] = defaultdict(list)
    for f in feedback:
        fb_by_turn[f.turn_id].append(f)

    exposure_turns: dict[str, set[str]] = defaultdict(set)
    for r in retrievals:
        if r.rank <= 10:
            exposure_turns[f"{r.item_id}@{r.item_version}"].add(r.turn_id)
    cited_turns: dict[str, list[str]] = defaultdict(list)
    contrib: dict[str, float] = defaultdict(float)
    explicit_share: dict[str, float] = defaultdict(float)
    for turn_id, cites in cites_by_turn.items():
        fbs = fb_by_turn.get(turn_id, [])
        explicit = sum(f.value for f in fbs if f.kind == "explicit")
        implicit = sum(f.value for f in fbs if f.kind != "explicit")
        turn_value = max(-1.5, min(1.5, explicit + implicit))
        weights = rank_weights(len(cites))
        for c, w in zip(sorted(cites, key=lambda c: c.position), weights):
            key = f"{c.item_id}@{c.item_version}"
            cited_turns[key].append(turn_id)
            contrib[key] += w * turn_value
            explicit_share[key] += w * explicit

    current = [it for it in all_items if it.valid_to is None]
    dups = detect_near_duplicates(current)
    conflicts = [{"type": "near_duplicate", "keys": [a, b], "jaccard": j, "detail": f"{by_key[a].locator} ↔ {by_key[b].locator}"} for a, b, j in dups]
    conflicts += detect_value_conflicts(current)
    for c in conflicts:  # 逻辑 id (不含版本), 便于跨同步比较冲突是否仍然存在
        c["ids"] = sorted(k.split("@")[0] for k in c["keys"])
    conflict_flags: dict[str, list[str]] = defaultdict(list)
    for c in conflicts:
        for k in c["keys"]:
            other = [x for x in c["keys"] if x != k]
            conflict_flags[k].append(f"{c['type']}:{c.get('path') or other[0]}")

    files_by_source: dict[str, dict] = {}
    scored_keys = sorted({it.key for it in current} | set(exposure_turns) | set(cited_turns))
    scores: list[ItemScore] = []
    for key in scored_keys:
        it = by_key.get(key)
        if it is None:
            continue
        exposures = len(exposure_turns.get(key, ()))
        ncited = len(cited_turns.get(key, ()))
        helpfulness = contrib[key] / ncited if ncited else 0.0
        stale: list[str] = []
        if it.status == "superseded":
            stale.append("superseded")
        elif it.status == "deleted":
            stale.append("tombstoned")
        else:
            files = files_by_source.setdefault(it.source_id, store.source_files(it.source_id, include_deleted=True))
            f = files.get(it.locator)
            if f and f["last_changed_at"] > it.last_verified_at:
                stale.append("file_changed_since_verified")
        cflags = sorted(conflict_flags.get(key, []))
        usage = min(1.0, ncited / 3)
        helpful = (max(-1.0, min(1.0, helpfulness)) + 1) / 2  # 无反馈时 0.5 (中性)
        if ncited == 0 and exposures >= 3:
            helpful = 0.45  # 多次检索到但从未被引用: 轻微扣分
        freshness = 0.0 if ("superseded" in stale or "tombstoned" in stale) else (0.5 if stale else 1.0)
        consistency = max(0.0, 1 - 0.5 * len(cflags))
        health = round(0.4 * helpful + 0.3 * freshness + 0.2 * consistency + 0.1 * usage, 4)
        reasons = [f"曝光 {exposures} 次, 引用 {ncited} 次 (引用率 {ncited / exposures:.0%})" if exposures else "未被检索到"]
        if ncited:
            reasons.append(f"反馈份额 {helpfulness:+.2f} (显式 {explicit_share[key] / ncited:+.2f})")
        reasons += [f"陈旧: {s}" for s in stale] + [f"冲突: {c}" for c in cflags]
        scores.append(ItemScore(it.id, it.version, exposures, ncited, round(ncited / exposures, 3) if exposures else 0.0,
                                round(helpfulness, 4), stale, cflags, health,
                                {"helpful": round(helpful, 3), "freshness": freshness, "consistency": consistency, "usage": round(usage, 3)},
                                reasons, now))
    store.upsert_item_scores(scores)

    gaps = detect_gaps(store, turns, fb_by_turn, cites_by_turn)
    tasks = _emit_tasks(store, scores, by_key, conflicts, gaps, cited_turns, fb_by_turn, now)
    keep = {t.fingerprint for t in tasks}
    resolved = store.resolve_tasks_not_in(RECOMPUTED_TYPES, keep, now)
    open_tasks = store.curation_tasks("open")
    return ScoringReport(scores=scores, gaps=gaps, tasks=open_tasks, resolved_tasks=resolved, computed_at=now, conflicts=conflicts)


def _emit_tasks(store: Store, scores: list[ItemScore], by_key: dict[str, KnowledgeItem], conflicts: list[dict],
                gaps: list[GapCluster], cited_turns: dict[str, list[str]], fb_by_turn: dict, now: str) -> list[CurationTask]:
    tasks: list[CurationTask] = []

    def add(task_type: str, item_ids: list[str], priority: float, reason: str, evidence: dict, fp_extra: str = "") -> None:
        fp = f"{task_type}:{','.join(sorted(item_ids))}:{fp_extra}"
        tasks.append(CurationTask(None, task_type, sorted(item_ids), round(min(1.0, priority), 2), reason, evidence, "open", now, fp))

    for s in scores:
        it = by_key[s.key]
        if it.valid_to is not None:
            continue
        turn_ids = cited_turns.get(s.key, [])
        neg_turns = [t for t in turn_ids if any(f.kind == "explicit" and f.value < 0 for f in fb_by_turn.get(t, []))]
        if s.helpfulness <= -0.5 and len(turn_ids) >= 2:
            add("deprecate", [s.key], 0.7 + 0.05 * len(neg_turns), f"多次被引用但反馈持续为负 (helpfulness {s.helpfulness:+.2f})",
                {"turn_ids": turn_ids, "negative_turns": neg_turns})
        elif DEPRECATED_RE.search(it.title + " " + it.text[:200]) and s.exposures >= 1:
            add("deprecate", [s.key], 0.5, "条目自称废弃/deprecated 但仍被检索到", {"turn_ids": sorted(set(turn_ids))})
        elif s.helpfulness < -0.2 and turn_ids:
            add("verify", [s.key], 0.6, f"引用后反馈偏负 (helpfulness {s.helpfulness:+.2f}), 需人工核对", {"turn_ids": turn_ids, "negative_turns": neg_turns})
        elif s.exposures >= 3 and s.citations == 0:
            add("verify", [s.key], 0.4 + 0.02 * s.exposures, f"被检索 {s.exposures} 次但从未被引用, 可能标题/内容与问题不匹配", {"exposures": s.exposures})
        if "file_changed_since_verified" in s.staleness_flags:
            add("verify", [s.key], 0.3 + 0.1 * min(3, s.citations), "来源文件在上次核验后已变化, 该章节未变但需复核上下文是否仍一致",
                {"locator": it.locator, "last_verified_at": it.last_verified_at}, fp_extra="file_changed")
    for c in conflicts:
        if c["type"] == "near_duplicate":
            add("merge", c["keys"], 0.7, f"近重复内容 (Jaccard {c['jaccard']}): {c['detail']}", {"jaccard": c["jaccard"], "locators": [by_key[k].locator for k in c["keys"]]})
        else:
            docs = [k for k in c["keys"] if by_key[k].kind != "config"] or c["keys"]
            add("update", docs, 0.9, f"取值冲突 {c['path']}: {c['detail']}", {"path": c["path"], "keys": c["keys"]}, fp_extra=c["path"])
    for g in gaps:
        add("fill_gap", [], g.priority, f"知识缺口 [{g.key}]: {len(g.turn_ids)} 个对话没有可靠依据" + (f", {g.negative_feedback} 个负反馈" if g.negative_feedback else ""),
            {"turn_ids": g.turn_ids, "queries": g.queries, "identifiers": g.identifiers}, fp_extra=g.key)
    return [store.add_curation_task(t) for t in tasks]
