"""命令行入口: python -m kloop.cli <子命令>。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .answer import compose_answer
from .evaluate import compare_runs, load_golden, mine_golden_candidates, render_regression, run_eval, select_entries, write_jsonl, write_reports
from .feedback import log_feedback, log_turn, promote_candidate
from .index import Index
from .llm import get_llm
from .scoring import compute_scores
from .search import deep_search
from .store import Store
from .sync import sync_source

DEFAULT_DB = str(Path(__file__).resolve().parent.parent / "outputs" / "kloop.db")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="kloop", description="知识闭环原型 CLI")
    p.add_argument("--db", default=DEFAULT_DB, help="SQLite 路径 (默认 outputs/kloop.db)")
    p.add_argument("--source", default="sample_corpus", help="source id")
    p.add_argument("--llm", default=None, help="heuristic | anthropic (默认取 KLOOP_LLM)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", help="初始化数据库")
    s = sub.add_parser("sync", help="增量同步语料目录"); s.add_argument("corpus_dir")
    s = sub.add_parser("search", help="检索"); s.add_argument("query"); s.add_argument("--kinds", default=None); s.add_argument("--top-k", type=int, default=8); s.add_argument("--as-of", default=None)
    s = sub.add_parser("ask", help="提问 (检索 + 回答 + 记录对话)"); s.add_argument("query"); s.add_argument("--user", default="cli"); s.add_argument("--session", default="cli")
    s = sub.add_parser("feedback", help="反馈"); s.add_argument("turn_id"); s.add_argument("value", choices=["+1", "-1"]); s.add_argument("--correction", default=None)
    sub.add_parser("score", help="从日志重算评分、缺口与策展任务")
    s = sub.add_parser("curate", help="查看策展队列"); s.add_argument("--status", default="open")
    s = sub.add_parser("promote", help="人工确认候选知识入库"); s.add_argument("task_id", type=int)
    s = sub.add_parser("eval", help="黄金集评测"); s.add_argument("golden"); s.add_argument("--name", default="cli"); s.add_argument("--freshness", action="store_true"); s.add_argument("--compare", default=None, help="与某个 eval run id 做回归对比"); s.add_argument("--out", default=None)
    sub.add_parser("report", help="总览报告")
    return p


def _corpus_version(store: Store, source: str) -> int:
    src = store.get_source(source)
    return src.sync_count if src else 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    store = Store(args.db)
    llm = get_llm(args.llm)
    try:
        if args.cmd == "init":
            print(f"已初始化数据库 {args.db}")
        elif args.cmd == "sync":
            idx = Index.from_store(store)
            rep = sync_source(store, args.source, args.corpus_dir, index=idx)
            print(rep.summary())
        elif args.cmd == "search":
            idx = Index.from_store(store, as_of=args.as_of)
            res = deep_search(idx, args.query, llm=llm, top_k=args.top_k, kinds=tuple(args.kinds.split(",")) if args.kinds else None, as_of=args.as_of)
            print(f"子查询: {res.trace.queries}; 步数 {len(res.trace.steps)}; 停止原因 {res.trace.stop_reason}; 覆盖率 {res.trace.coverage:.2f}")
            for i, h in enumerate(res.hits[:args.top_k], 1):
                print(f"{i:2d}. [{h.item.kind}] {h.item.title} — {h.item.locator} (v{h.item.version})\n    {h.why}")
        elif args.cmd == "ask":
            idx = Index.from_store(store)
            res = deep_search(idx, args.query, llm=llm)
            ans = compose_answer(args.query, res, llm)
            turn = log_turn(store, args.query, args.user, args.session, res, ans, llm.name, metadata={"corpus_version": _corpus_version(store, args.source)})
            print(ans.text)
            print(f"\n[turn {turn.id}] 引用 {len(ans.cited_item_ids)} 条, 检索 {len(res.hits)} 条, 弃答={ans.abstained}")
        elif args.cmd == "feedback":
            fb = log_feedback(store, args.turn_id, "explicit", 1 if args.value == "+1" else -1)
            print(f"已记录显式反馈 #{fb.id}")
            if args.correction:
                log_feedback(store, args.turn_id, "correction", text=args.correction)
                print("已记录纠错文本, 候选知识进入策展队列 (promote_candidate)")
        elif args.cmd == "score":
            rep = compute_scores(store)
            print(f"评分条目 {len(rep.scores)}, 缺口 {len(rep.gaps)}, 冲突 {len(rep.conflicts)}, 开放任务 {len(rep.tasks)}, 本次关闭 {rep.resolved_tasks}")
            for s in rep.top(5):
                it = store.get_item(s.item_id, s.version)
                print(f"  TOP  {s.health:.2f} {it.title if it else s.key} :: {'; '.join(s.reasons)}")
            for s in rep.bottom(5):
                it = store.get_item(s.item_id, s.version)
                print(f"  LOW  {s.health:.2f} {it.title if it else s.key} :: {'; '.join(s.reasons)}")
            for ttype, tasks in rep.tasks_by_type().items():
                print(f"  任务 {ttype}: {len(tasks)}")
        elif args.cmd == "curate":
            for t in store.curation_tasks(args.status):
                print(f"#{t.id} [{t.task_type}] p={t.priority:.2f} {t.reason} | items={t.item_ids} | evidence={json.dumps(t.evidence, ensure_ascii=False)[:200]}")
        elif args.cmd == "promote":
            item = promote_candidate(store, args.task_id)
            print(f"已入库 lesson 条目 {item.key}: {item.title}")
        elif args.cmd == "eval":
            golden = load_golden(args.golden)
            cv = _corpus_version(store, args.source)
            entries = select_entries(golden, cv, freshness_only=args.freshness)
            idx = Index.from_store(store)
            run = run_eval(store, idx, entries, llm, name=args.name, corpus_version=cv)
            out = Path(args.out or Path(args.db).parent)
            jp, mp = write_reports(run, out)
            print(json.dumps(run.summary, ensure_ascii=False, indent=2))
            print(f"报告: {jp}, {mp}")
            if args.compare:
                base = store.get_eval_run(args.compare)
                if base is None:
                    print(f"找不到 eval run {args.compare}")
                else:
                    diff = compare_runs(base, run)
                    print(render_regression(diff))
            cands = mine_golden_candidates(store)
            if cands:
                write_jsonl(out / "golden_candidates.jsonl", cands)
                print(f"黄金集候选 {len(cands)} 条 -> {out / 'golden_candidates.jsonl'}")
        elif args.cmd == "report":
            for src in store.list_sources():
                print(f"source {src.id}: root={src.root} 同步 {src.sync_count} 次, 最近 {src.last_sync_at}")
            print(f"当前条目 {store.count_items()} / 历史总数 {store.count_items(False)}; 对话 {store.count_turns()}; 反馈 {len(store.feedback())}")
            for run in store.list_eval_runs():
                print(f"eval {run.id}: " + ", ".join(f"{k}={v}" for k, v in run.summary.items() if isinstance(v, (int, float))))
            tasks = store.curation_tasks("open")
            print(f"开放策展任务 {len(tasks)}: " + ", ".join(f"{t.task_type}#{t.id}" for t in tasks[:12]))
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # 管道被 head 等提前关闭时静默退出
        sys.exit(0)
