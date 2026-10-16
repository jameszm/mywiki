"""评测: 黄金集加载、检索/答案指标、新鲜度测试、回归对比、黄金集挖掘、报告输出。

指标:
- recall@k = 命中的相关 locator 数 / 相关 locator 数; MRR = 1/首个相关命中的名次;
  nDCG@k 以 locator 首次出现位置计增益 (binary), IDCG 按相关 locator 数计算。
- keyword_coverage = 答案覆盖的 relevant_keywords 比例; citation_precision = 引用中相关的比例;
  groundedness = 答案句子中与某引用条目 token 重叠 >= 0.5 的比例; abstain_ok = 弃答与期望一致。
- freshness (expects_version>=2): top hit 为当前版本 且 引用中无被替代版本。
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any

from .answer import compose_answer
from .index import Index, tokenize
from .llm import CITE_RE, HeuristicLLM, LLMClient, split_sentences
from .models import EvalRun, utc_now
from .search import deep_search, extract_identifiers
from .store import Store

METRICS = ("recall@5", "recall@10", "mrr", "ndcg@5", "ndcg@10", "keyword_coverage", "citation_precision", "groundedness")


@dataclass
class GoldenEntry:
    id: str
    query: str
    relevant_locators: list[str]
    relevant_keywords: list[str]
    kind: str = "doc"
    expects_version: int = 1
    notes: str = ""
    valid_until_version: int | None = None
    acl: list[str] | None = None

    @property
    def expects_abstain(self) -> bool:
        return not self.relevant_locators


def load_golden(path: str | Path) -> list[GoldenEntry]:
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            d = json.loads(line)
            out.append(GoldenEntry(d["id"], d["query"], d.get("relevant_locators", []), d.get("relevant_keywords", []),
                                   d.get("kind", "doc"), int(d.get("expects_version", 1)), d.get("notes", ""),
                                   d.get("valid_until_version"), d.get("acl")))
    return out


def select_entries(entries: list[GoldenEntry], corpus_version: int, freshness_only: bool = False) -> list[GoldenEntry]:
    if freshness_only:
        return [e for e in entries if 2 <= e.expects_version <= corpus_version]
    return [e for e in entries if e.expects_version <= corpus_version and (e.valid_until_version is None or e.valid_until_version >= corpus_version)]


# ----------------------------------------------------------------- metrics
def recall_at_k(ranked_locators: list[str], relevant: list[str], k: int) -> float:
    if not relevant:
        return 1.0
    return len(set(ranked_locators[:k]) & set(relevant)) / len(set(relevant))


def mrr(ranked_locators: list[str], relevant: list[str]) -> float:
    rel = set(relevant)
    for i, loc in enumerate(ranked_locators, 1):
        if loc in rel:
            return 1.0 / i
    return 0.0 if relevant else 1.0


def ndcg_at_k(ranked_locators: list[str], relevant: list[str], k: int) -> float:
    rel = set(relevant)
    if not rel:
        return 1.0
    seen, dcg = set(), 0.0
    for i, loc in enumerate(ranked_locators[:k], 1):
        if loc in rel and loc not in seen:
            seen.add(loc)
            dcg += 1.0 / math.log2(i + 1)
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, min(len(rel), k) + 1))
    return dcg / idcg if idcg else 0.0


def keyword_coverage(answer_text: str, keywords: list[str]) -> float:
    if not keywords:
        return 1.0
    low = answer_text.lower()
    return sum(1 for kw in keywords if kw.lower() in low) / len(keywords)


def citation_precision(cited_locators: list[str], relevant: list[str]) -> float:
    if not cited_locators:
        return 1.0 if not relevant else 0.0
    rel = set(relevant)
    return sum(1 for loc in cited_locators if loc in rel) / len(cited_locators)


def groundedness(answer_text: str, cited_texts: list[str], threshold: float = 0.5) -> float:
    body = answer_text.split("参考来源:")[0]
    sents = [CITE_RE.sub("", s).strip("- ") for s in split_sentences(body)]
    sents = [s for s in sents if len(set(tokenize(s))) >= 2 and not s.startswith("根据知识库")]
    if not sents or not cited_texts:
        return 0.0 if sents else 1.0
    token_sets = [set(tokenize(t)) for t in cited_texts]
    ok = 0
    for s in sents:
        toks = set(tokenize(s))
        if any(len(toks & ts) / len(toks) >= threshold for ts in token_sets):
            ok += 1
    return ok / len(sents)


# --------------------------------------------------------------- evaluate
def evaluate_entry(store: Store, index: Index, entry: GoldenEntry, llm: LLMClient, latest: dict[str, int]) -> dict[str, Any]:
    result = deep_search(index, entry.query, llm=llm, acl=entry.acl)
    ans = compose_answer(entry.query, result, llm)
    ranked = [h.item.locator for h in result.hits]
    rel = entry.relevant_locators
    cited_items = [store.get_item(i, v) for i, v in ans.citations]
    cited_locs = [it.locator for it in cited_items if it]
    rec: dict[str, Any] = {
        "id": entry.id, "query": entry.query, "kind": entry.kind, "expects_version": entry.expects_version,
        "recall@5": recall_at_k(ranked, rel, 5), "recall@10": recall_at_k(ranked, rel, 10), "mrr": mrr(ranked, rel),
        "ndcg@5": ndcg_at_k(ranked, rel, 5), "ndcg@10": ndcg_at_k(ranked, rel, 10),
        "keyword_coverage": keyword_coverage(ans.text, entry.relevant_keywords),
        "citation_precision": citation_precision(cited_locs, rel),
        "groundedness": groundedness(ans.text, [it.text for it in cited_items if it]),
        "abstained": ans.abstained, "expected_abstain": entry.expects_abstain, "abstain_ok": ans.abstained == entry.expects_abstain,
        "max_relevance": round(result.max_relevance, 3), "steps": len(result.trace.steps), "stop_reason": result.trace.stop_reason,
        "top_locators": list(dict.fromkeys(ranked[:5])), "cited": [f"{i}@{v}" for i, v in ans.citations],
        "answer_preview": ans.text.split("\n\n参考来源")[0][:220],
    }
    if entry.expects_version >= 2:
        top = result.hits[0].item if result.hits else None
        rec["top_hit_current"] = bool(top and top.valid_to is None and latest.get(top.id) == top.version)
        rec["no_superseded_cited"] = all(it is not None and it.valid_to is None for it in cited_items)
        rec["freshness_pass"] = rec["top_hit_current"] and rec["no_superseded_cited"]
    return rec


def run_eval(store: Store, index: Index, entries: list[GoldenEntry], llm: LLMClient | None = None, name: str = "eval",
             corpus_version: int = 0, run_id: str | None = None) -> EvalRun:
    llm = llm or HeuristicLLM()
    latest = store.latest_versions()
    per_query = [evaluate_entry(store, index, e, llm, latest) for e in entries]
    summary: dict[str, Any] = {"n": len(per_query), "corpus_version": corpus_version}
    for m in METRICS:
        summary[m] = round(mean(r[m] for r in per_query), 4) if per_query else 0.0
    summary["abstain_ok_rate"] = round(mean(r["abstain_ok"] for r in per_query), 4) if per_query else 0.0
    summary["abstained"] = sum(r["abstained"] for r in per_query)
    summary["avg_steps"] = round(mean(r["steps"] for r in per_query), 2) if per_query else 0.0
    fresh = [r for r in per_query if "freshness_pass" in r]
    if fresh:
        summary["freshness_n"] = len(fresh)
        summary["freshness_pass_rate"] = round(mean(r["freshness_pass"] for r in fresh), 4)
        summary["freshness_keyword_coverage"] = round(mean(r["keyword_coverage"] for r in fresh), 4)
    run = EvalRun(run_id or f"{name}-{store.count_turns()}-{len(store.list_eval_runs()) + 1}", name, utc_now(), summary, per_query, corpus_version)
    store.save_eval_run(run)
    return run


def compare_runs(base: EvalRun, new: EvalRun, tol: float = 0.1) -> dict[str, Any]:
    """回归对比: 共同 query 的逐项指标差值, 标出回归 / 改进。"""
    base_by = {r["id"]: r for r in base.per_query}
    rows, regressions, improvements = [], [], []
    for r in new.per_query:
        b = base_by.get(r["id"])
        if not b:
            continue
        deltas = {m: round(r[m] - b[m], 4) for m in METRICS}
        row = {"id": r["id"], "query": r["query"], **{f"d_{m}": v for m, v in deltas.items()}}
        rows.append(row)
        key_metrics = ("recall@10", "mrr", "ndcg@10", "keyword_coverage")
        if any(deltas[m] < -tol for m in key_metrics):
            regressions.append(row)
        elif any(deltas[m] > tol for m in key_metrics):
            improvements.append(row)
    summary_delta = {m: round(new.summary.get(m, 0) - base.summary.get(m, 0), 4) for m in METRICS}
    return {"base": base.id, "new": new.id, "common": len(rows), "summary_delta": summary_delta, "per_query": rows,
            "regressions": regressions, "improvements": improvements}


def mine_golden_candidates(store: Store) -> list[dict[str, Any]]:
    """显式 +1 且至少一条引用的对话 -> 候选黄金条目 (不自动合并)。"""
    out = []
    for t in store.turns():
        fbs = store.feedback(t.id)
        if not any(f.kind == "explicit" and f.value > 0 for f in fbs):
            continue
        cites = store.citations(t.id)
        if not cites:
            continue
        locs = sorted({it.locator for it in (store.get_item(c.item_id, c.item_version) for c in cites) if it})
        kws = extract_identifiers(t.query) or [x for x in tokenize(t.query) if len(x) > 1][:3]
        out.append({"id": f"cand-{t.id}", "query": t.query, "relevant_locators": locs, "relevant_keywords": kws, "kind": "mined",
                    "expects_version": t.metadata.get("corpus_version", 1), "notes": f"mined from {t.id} user={t.user_id}, 需人工审核"})
    return out


# ---------------------------------------------------------------- reports
def write_jsonl(path: str | Path, rows: list[dict]) -> None:
    Path(path).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def render_markdown(run: EvalRun) -> str:
    s = run.summary
    lines = [f"# 评测报告 {run.id}", "", f"- 名称: {run.name}  语料版本: v{run.corpus_version}  条目数: {s['n']}  时间: {run.created_at}", "",
             "| 指标 | 值 |", "|---|---|"]
    for m in METRICS:
        lines.append(f"| {m} | {s[m]:.3f} |")
    lines.append(f"| abstain_ok_rate | {s['abstain_ok_rate']:.3f} |")
    if "freshness_pass_rate" in s:
        lines.append(f"| freshness_pass_rate (n={s['freshness_n']}) | {s['freshness_pass_rate']:.3f} |")
    lines += ["", "## 逐条结果", "", "| id | query | R@5 | R@10 | MRR | nDCG@10 | kw | cite_p | grounded | abstain_ok | fresh | 步数/停止 |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in run.per_query:
        fresh = "✓" if r.get("freshness_pass") else ("✗" if "freshness_pass" in r else "-")
        lines.append(f"| {r['id']} | {r['query']} | {r['recall@5']:.2f} | {r['recall@10']:.2f} | {r['mrr']:.2f} | {r['ndcg@10']:.2f} | "
                     f"{r['keyword_coverage']:.2f} | {r['citation_precision']:.2f} | {r['groundedness']:.2f} | {'✓' if r['abstain_ok'] else '✗'} | {fresh} | {r['steps']}/{r['stop_reason']} |")
    return "\n".join(lines) + "\n"


def render_regression(diff: dict[str, Any]) -> str:
    lines = [f"# 回归对比 {diff['base']} → {diff['new']}", "", f"共同 query: {diff['common']}; 回归 {len(diff['regressions'])}, 改进 {len(diff['improvements'])}", "",
             "| 指标 | Δ |", "|---|---|"] + [f"| {m} | {v:+.3f} |" for m, v in diff["summary_delta"].items()]
    lines += ["", "## 逐条差值", "", "| id | query | ΔR@10 | ΔMRR | ΔnDCG@10 | Δkw | Δcite_p |", "|---|---|---|---|---|---|---|"]
    for r in diff["per_query"]:
        lines.append(f"| {r['id']} | {r['query']} | {r['d_recall@10']:+.2f} | {r['d_mrr']:+.2f} | {r['d_ndcg@10']:+.2f} | {r['d_keyword_coverage']:+.2f} | {r['d_citation_precision']:+.2f} |")
    return "\n".join(lines) + "\n"


def write_reports(run: EvalRun, outputs_dir: str | Path) -> tuple[Path, Path]:
    out = Path(outputs_dir)
    out.mkdir(parents=True, exist_ok=True)
    jp, mp = out / f"eval_{run.name}.json", out / f"eval_{run.name}.md"
    jp.write_text(json.dumps({"id": run.id, "name": run.name, "created_at": run.created_at, "corpus_version": run.corpus_version,
                              "summary": run.summary, "per_query": run.per_query}, ensure_ascii=False, indent=2), encoding="utf-8")
    mp.write_text(render_markdown(run), encoding="utf-8")
    return jp, mp
