#!/usr/bin/env python3
"""端到端演示: 初始化 -> 同步 v1 -> 评测 -> 回放对话 -> 评分 -> 同步 v2 -> 新鲜度评测 -> 回归 -> 再评分。

所有输出写入 outputs/ (报告为 markdown/json, 数据库 kloop.db 被 .gitignore 忽略)。
"""
from __future__ import annotations

import io
import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from kloop.evaluate import compare_runs, load_golden, mine_golden_candidates, render_regression, run_eval, select_entries, write_jsonl, write_reports  # noqa: E402
from kloop.feedback import replay_scenarios  # noqa: E402
from kloop.index import Index  # noqa: E402
from kloop.llm import get_llm  # noqa: E402
from kloop.scoring import ScoringReport, compute_scores  # noqa: E402
from kloop.store import Store  # noqa: E402
from kloop.sync import sync_source  # noqa: E402

OUT = ROOT / "outputs"
DB = OUT / "kloop.db"
SOURCE = "sample_corpus"
_buf = io.StringIO()


def say(*parts: object) -> None:
    line = " ".join(str(p) for p in parts)
    print(line)
    _buf.write(line + "\n")


def step(n: int, title: str) -> None:
    say(f"\n== 步骤 {n}: {title} " + "=" * max(4, 60 - len(title)))


def metric_table(summary: dict) -> str:
    keys = ["recall@5", "recall@10", "mrr", "ndcg@5", "ndcg@10", "keyword_coverage", "citation_precision", "groundedness", "abstain_ok_rate"]
    head = " | ".join(f"{k:>12}" for k in keys)
    vals = " | ".join(f"{summary.get(k, 0):>12.3f}" for k in keys)
    return f"   {head}\n   {vals}"


def describe_scores(store: Store, rep: ScoringReport, label: str) -> str:
    lines = [f"# 评分报告 {label}", "", f"评分条目 {len(rep.scores)}, 冲突 {len(rep.conflicts)}, 缺口 {len(rep.gaps)}, 开放任务 {len(rep.tasks)}, 本次关闭任务 {rep.resolved_tasks}", ""]
    for title, rows in (("健康度 Top 5", rep.top(5)), ("健康度 Bottom 5", rep.bottom(5))):
        lines += [f"## {title}", "", "| 条目 | 版本 | health | 分量 | 原因 |", "|---|---|---|---|---|"]
        for s in rows:
            it = store.get_item(s.item_id, s.version)
            comp = ", ".join(f"{k}={v}" for k, v in s.components.items())
            lines.append(f"| {it.title if it else s.item_id} ({it.locator if it else '?'}) | v{s.version} | {s.health:.2f} | {comp} | {'; '.join(s.reasons)} |")
        lines.append("")
    lines += ["## 冲突", ""] + [f"- {c['type']} {c.get('path', '')}: {c['detail']}" for c in rep.conflicts] + ["", "## 缺口", ""]
    lines += [f"- [{g.key}] {len(g.turn_ids)} 个对话 (负反馈 {g.negative_feedback}): {' / '.join(g.queries)}" for g in rep.gaps]
    lines += ["", "## 策展队列 (按类型)", ""]
    for ttype, tasks in rep.tasks_by_type().items():
        lines.append(f"### {ttype} ({len(tasks)})")
        for t in tasks:
            lines.append(f"- #{t.id} p={t.priority:.2f} {t.reason} | items={t.item_ids} | evidence={json.dumps(t.evidence, ensure_ascii=False)[:160]}")
        lines.append("")
    return "\n".join(lines) + "\n"


def print_scores(store: Store, rep: ScoringReport) -> None:
    say(f"   评分条目 {len(rep.scores)} (含被替代/墓碑版本), 冲突 {len(rep.conflicts)}, 缺口簇 {len(rep.gaps)}, 开放任务 {len(rep.tasks)}, 本次关闭 {rep.resolved_tasks}")
    say("   健康度 Top 5:")
    for s in rep.top(5):
        it = store.get_item(s.item_id, s.version)
        say(f"     {s.health:.2f} {it.title} ({it.locator} v{s.version}) :: {'; '.join(s.reasons)}")
    say("   健康度 Bottom 5:")
    for s in rep.bottom(5):
        it = store.get_item(s.item_id, s.version)
        say(f"     {s.health:.2f} {it.title} ({it.locator} v{s.version}) :: {'; '.join(s.reasons)}")
    say("   缺口簇:")
    for g in rep.gaps:
        say(f"     [{g.key}] {len(g.turn_ids)} 个对话, 负反馈 {g.negative_feedback}: {' / '.join(q[:28] for q in g.queries)}")
    say("   策展队列 (按类型): " + ", ".join(f"{k}={len(v)}" for k, v in rep.tasks_by_type().items()))
    for ttype, tasks in rep.tasks_by_type().items():
        for t in tasks[:3]:
            say(f"     [{ttype}] #{t.id} p={t.priority:.2f} {t.reason[:90]}")


def main() -> int:
    t0 = time.time()
    OUT.mkdir(exist_ok=True)
    for f in (DB, DB.with_name("kloop.db-wal"), DB.with_name("kloop.db-shm")):
        if f.exists():
            f.unlink()
    llm = get_llm()
    say(f"知识闭环原型演示 (LLM 后端: {llm.name})")

    step(1, "初始化数据库")
    store = Store(DB)
    tables = [r[0] for r in store.conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    say(f"   {DB.relative_to(ROOT)} 已创建, 表: {', '.join(tables)}")

    step(2, "同步语料 v1 (全量首次)")
    index = Index()
    rep1 = sync_source(store, SOURCE, ROOT / "sample_corpus" / "v1", index=index)
    say("   " + rep1.summary())
    kinds = Counter(it.kind for it in store.current_items())
    say("   条目类型分布: " + ", ".join(f"{k}={v}" for k, v in sorted(kinds.items())))
    (OUT / "sync_v1.json").write_text(json.dumps(rep1.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    step(3, "黄金集评测 (expects_version=1)")
    golden = load_golden(ROOT / "golden" / "golden_set.jsonl")
    entries_v1 = select_entries(golden, 1)
    run1 = run_eval(store, index, entries_v1, llm, name="v1", corpus_version=1)
    say(f"   条目 {run1.summary['n']}, 弃答 {run1.summary['abstained']}, 平均步数 {run1.summary['avg_steps']}")
    say(metric_table(run1.summary))
    jp, mp = write_reports(run1, OUT)
    say(f"   报告: {jp.relative_to(ROOT)}, {mp.relative_to(ROOT)}")

    step(4, "回放模拟对话 (search -> answer -> 记录对话与反馈)")
    replay = replay_scenarios(store, index, ROOT / "scenarios" / "conversations.jsonl", llm, corpus_version=1)
    say(f"   对话 {replay.turns} 轮, 用户 {len(replay.users)} 人, 带引用 {replay.cited_turns} 轮 (引用率 {replay.cited_rate:.0%}), 弃答 {replay.abstained}, "
        f"反馈事件 {replay.feedback_events} (改写 {replay.reformulations}, 纠错 {replay.corrections})")
    say(f"   每轮都记录了检索条目 (id@version, rank, 各信号分数) 与引用条目: retrievals={len(store.retrievals())}, citations={len(store.citations())}")
    (OUT / "replay_summary.json").write_text(json.dumps({"turns": replay.turns, "cited_turns": replay.cited_turns, "cited_rate": round(replay.cited_rate, 3),
                                                        "abstained": replay.abstained, "feedback_events": replay.feedback_events, "users": dict(replay.users)},
                                                       ensure_ascii=False, indent=2), encoding="utf-8")

    step(5, "基于日志评分 / 缺口 / 策展队列")
    score1 = compute_scores(store)
    print_scores(store, score1)
    (OUT / "scores_v1.md").write_text(describe_scores(store, score1, "v1 (对话回放后)"), encoding="utf-8")

    step(6, "同步语料 v2 (增量)")
    rep2 = sync_source(store, SOURCE, ROOT / "sample_corpus" / "v2", index=index)
    say("   " + rep2.summary())
    say(f"   只重建了受影响条目: 新增 {rep2.added} + 更新 {rep2.updated} + 墓碑 {rep2.deleted} = {rep2.items_reindexed}; 未变 {rep2.unchanged} 条未触碰 (索引大小 {len(index)} = 当前有效条目 {store.count_items()})")
    say(f"   变更文件: {', '.join(rep2.changed_locators)}; 删除文件: {', '.join(rep2.deleted_locators)}")
    for key in rep2.updated_keys[:3]:
        item_id, ver = key.split("@")
        hist = store.item_history(item_id)
        old = hist[-2]
        say(f"   版本链 {item_id} ({old.title}): v{old.version} valid_to={old.valid_to[:19]} superseded_by={old.superseded_by} status={old.status} -> v{ver} 当前有效")
    for key in rep2.deleted_keys[:1]:
        item_id, ver = key.split("@")
        it = store.get_item(item_id, int(ver))
        say(f"   墓碑示例 {key} ({it.title}, {it.locator}): status={it.status} valid_to={it.valid_to[:19]}")
    (OUT / "sync_v2.json").write_text(json.dumps(rep2.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    step(7, "新鲜度评测 (expects_version=2)")
    entries_fresh = select_entries(golden, 2, freshness_only=True)
    run_fresh = run_eval(store, index, entries_fresh, llm, name="freshness_v2", corpus_version=2)
    say(f"   条目 {run_fresh.summary['n']}, freshness_pass_rate={run_fresh.summary['freshness_pass_rate']:.2f}, 关键词覆盖 {run_fresh.summary['freshness_keyword_coverage']:.2f}")
    for r in run_fresh.per_query:
        say(f"   {'✓' if r['freshness_pass'] else '✗'} {r['id']} {r['query']}: top命中为当前版本={r['top_hit_current']}, 未引用被替代版本={r['no_superseded_cited']}, 关键词覆盖={r['keyword_coverage']:.2f}")
        say(f"       答案: {r['answer_preview'].splitlines()[1][:110] if len(r['answer_preview'].splitlines()) > 1 else r['answer_preview'][:110]}")
    write_reports(run_fresh, OUT)

    step(8, "v2 全量评测 + 与步骤 3 的回归对比")
    entries_v2 = select_entries(golden, 2)
    run2 = run_eval(store, index, entries_v2, llm, name="v2", corpus_version=2)
    say(f"   条目 {run2.summary['n']} (含 {run2.summary.get('freshness_n', 0)} 条新鲜度条目)")
    say(metric_table(run2.summary))
    diff = compare_runs(run1, run2)
    say(f"   回归对比 (共同 query {diff['common']}): " + ", ".join(f"{k} {v:+.3f}" for k, v in diff["summary_delta"].items()))
    say(f"   回归 {len(diff['regressions'])} 条, 改进 {len(diff['improvements'])} 条; 逐条非零差值:")
    for r in diff["per_query"]:
        nz = {k[2:]: v for k, v in r.items() if k.startswith("d_") and abs(v) > 1e-9}
        if nz:
            say(f"     {r['id']} {r['query'][:24]}: " + ", ".join(f"{k} {v:+.2f}" for k, v in nz.items()))
    write_reports(run2, OUT)
    (OUT / "regression_v1_v2.md").write_text(render_regression(diff), encoding="utf-8")
    (OUT / "regression_v1_v2.json").write_text(json.dumps(diff, ensure_ascii=False, indent=2), encoding="utf-8")

    step(9, "再次评分: 陈旧/冲突标记的变化 + 黄金集候选挖掘")
    score2 = compute_scores(store)
    flags1 = Counter(f for s in score1.scores for f in s.staleness_flags)
    flags2 = Counter(f for s in score2.scores for f in s.staleness_flags)
    say(f"   陈旧标记 v1 -> v2: {dict(flags1) or '{}'} -> {dict(flags2)}")
    sig = lambda c: (c["type"], c.get("path", ""), tuple(c["ids"]))  # noqa: E731
    c1, c2 = {sig(c) for c in score1.conflicts}, {sig(c) for c in score2.conflicts}
    for c in score1.conflicts:
        if sig(c) not in c2:
            say(f"   冲突已清除: {c['type']} {c.get('path', '')} {c['detail']}")
    for c in score2.conflicts:
        if sig(c) not in c1:
            say(f"   冲突新出现: {c['type']} {c.get('path', '')} {c['detail']}")
    stale_items = [s for s in score2.scores if "file_changed_since_verified" in s.staleness_flags]
    say(f"   来源文件变更后未复核的条目 {len(stale_items)} 条 (低优先级 verify 任务), 例如: " + "; ".join(store.get_item(s.item_id, s.version).title for s in stale_items[:4]))
    say(f"   被替代版本 (superseded) {flags2.get('superseded', 0)} 条, 墓碑 {flags2.get('tombstoned', 0)} 条 (它们仍在日志中有曝光/引用记录, 健康度降至最低)")
    say(f"   任务变化: 本次关闭 {score2.resolved_tasks} 个不再成立的任务; 开放任务 " + ", ".join(f"{k}={len(v)}" for k, v in score2.tasks_by_type().items()))
    say("   健康度 Bottom 5 (被替代/墓碑版本沉底):")
    for s in score2.bottom(5):
        it = store.get_item(s.item_id, s.version)
        say(f"     {s.health:.2f} {it.title} ({it.locator} v{s.version}) :: {'; '.join(s.reasons)}")
    (OUT / "scores_v2.md").write_text(describe_scores(store, score2, "v2 (增量同步后)"), encoding="utf-8")
    cands = mine_golden_candidates(store)
    write_jsonl(OUT / "golden_candidates.jsonl", cands)
    say(f"   黄金集候选 (显式 +1 且有引用的对话): {len(cands)} 条 -> outputs/golden_candidates.jsonl (不自动合并), 例如: {cands[0]['query'] if cands else '无'} -> {cands[0]['relevant_locators'] if cands else ''}")

    elapsed = time.time() - t0
    say(f"\n全部完成, 总耗时 {elapsed:.1f}s; 输出目录: {OUT.relative_to(ROOT)}/")
    (OUT / "demo_summary.md").write_text("# Demo 输出\n\n```\n" + _buf.getvalue() + "```\n", encoding="utf-8")
    store.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
