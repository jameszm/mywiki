# mywiki

A product that analyzes GitHub repositories and generates an **interactive architecture wiki**.

## Product decisions (agreed 2026-07-05)

- The output is a **single interactive HTML page**, not multi-page markdown docs.
- The page shows a **panoramic architecture graph** on open (8–15 top-level components); users click any node or edge to see details in a side panel; nodes expand for deeper levels (semantic zoom).
- Graph **structure comes from static analysis** (ground truth: imports, calls, file tree via tree-sitter); the **LLM adds meaning**: grouping files into components, naming them, classifying edges, writing detail explanations with source citations.
- Data is enriched from **online sources** too, not just code: GitHub issues/PRs/releases (first priority), official docs and blog posts, Stack Overflow. External claims are kept visually separate from code-derived facts, with provenance (source URL, date, authority weighting).
- Delivery: self-contained `.html` file (viewer JS + graph JSON + pre-generated detail payloads inlined). No backend for the MVP. Deep links via URL hash.
- MVP path: CLI takes a repo URL → emits one HTML file. First milestone: build the HTML viewer against a hand-written sample `graph.json` before writing the analysis pipeline.

## Product decisions (locked 2026-07-13)

- **Granularity: function/class level** — every class/function/method gets summarized; methods are full graph nodes (details budget-gated: facts-only panels for private/small symbols).
- **Delivery: self-contained single HTML** (reconfirmed). "Dynamic" = in-page interactivity, no backend.
- **Depth: unlimited drill-down** (component → [submodule] → file → class/function → method), realized as on-demand *rendering* of pre-generated, inlined data — never on-demand generation.
- **Order: pure code graph first (milestone 2b), then GitHub API enrichment (commits/issues/PRs/releases), then web search** — but the external-knowledge schema envelope (provenance, authority, conflicts) ships in the schema now, arrays empty.

See `docs/DESIGN.md` for the v1 architecture discussion and **`docs/DESIGN-v2.md` for the full
multi-level design** (graph.json v2 schema, pipeline stages, viewer v2, validation gates,
benchmark, revised milestone plan).

## Repo layout

- `viewer/template.html` — the reusable interactive viewer (vanilla JS + SVG, zero deps) with a `__GRAPH_DATA__` placeholder.
- `tools/build.py` — injects a graph JSON into the template → one self-contained HTML file. Run: `python3 tools/build.py [graph.json output.html]` (no args = requests example).
- `examples/` — test repositories (gitignored clones) + graph data. Current test subject: `psf/requests`.
  - `requests.graph.json` — hand-written sample graph (milestone 1 artifact; to be replaced by pipeline output).
  - `requests-wiki.html` — built demo output.

## Status (2026-07-13)

- Milestone 1 done: viewer works (pan/zoom, click → detail panel, neighbor highlighting, search, URL-hash deep links) against the hand-written requests graph. User approved the demo.
- Milestone 2a done: `tools/analyze.py` extracts ground-truth skeletons (ast-based import graph). Validated on requests: all 12 hand-written edges confirmed by real imports; 65 raw core edges show why LLM aggregation is needed.
- **Design v2 done (2026-07-13):** multi-level schema + pipeline + viewer designed via 3 independent design passes + 2 adversarial reviews; all conflicts resolved in `docs/DESIGN-v2.md`. Estimated pipeline cost for requests: ~$0.80/run.
- **Next: implement milestone 2b**, in this order (per DESIGN-v2 §9):
  1. **2b-0** — analyzer amendments (import lines on edges, symbol end_lineno, method lines, per-edge external imports, commit SHA, role-heuristic fix).
  2. **2b-1** — LLM-free end-to-end: schema v2 + `aggregate.py` + `assemble.py` + `--grouping trivial` → real v2 graph.json from the existing skeleton with zero API calls (viewer fixture + keyless CI path).
  3. **2b-2** — viewer v2 (in-place expansion, runtime quotient edge lift, search/deep-links across depths).
  4. **2b-3** — LLM stages (`summarize.py` → `group.py` iterated against `score.py` → details) → benchmark sign-off (≥10/12 edges recovered, mean Jaccard ≥ 0.6, primary edge count ≤ 1.5× components).
- API access: `ANTHROPIC_API_KEY` goes in `~/.bashrc` (user has a key; may not be set up on every machine — verify before running LLM steps; scripts must preflight + support `--dry-run`). `api.anthropic.com` is NOT intercepted by the SealSuite gateway; direct TLS works.

## Conventions

- Viewer is deliberately vanilla JS (no build step, output must work from `file://`). Python for the pipeline; Claude API for LLM steps.
