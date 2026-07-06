# mywiki

A product that analyzes GitHub repositories and generates an **interactive architecture wiki**.

## Product decisions (agreed 2026-07-05)

- The output is a **single interactive HTML page**, not multi-page markdown docs.
- The page shows a **panoramic architecture graph** on open (8–15 top-level components); users click any node or edge to see details in a side panel; nodes expand for deeper levels (semantic zoom).
- Graph **structure comes from static analysis** (ground truth: imports, calls, file tree via tree-sitter); the **LLM adds meaning**: grouping files into components, naming them, classifying edges, writing detail explanations with source citations.
- Data is enriched from **online sources** too, not just code: GitHub issues/PRs/releases (first priority), official docs and blog posts, Stack Overflow. External claims are kept visually separate from code-derived facts, with provenance (source URL, date, authority weighting).
- Delivery: self-contained `.html` file (viewer JS + graph JSON + pre-generated detail payloads inlined). No backend for the MVP. Deep links via URL hash.
- MVP path: CLI takes a repo URL → emits one HTML file. First milestone: build the HTML viewer against a hand-written sample `graph.json` before writing the analysis pipeline.

See `docs/DESIGN.md` for the full architecture discussion.

## Repo layout

- `viewer/template.html` — the reusable interactive viewer (vanilla JS + SVG, zero deps) with a `__GRAPH_DATA__` placeholder.
- `tools/build.py` — injects a graph JSON into the template → one self-contained HTML file. Run: `python3 tools/build.py [graph.json output.html]` (no args = requests example).
- `examples/` — test repositories (gitignored clones) + graph data. Current test subject: `psf/requests`.
  - `requests.graph.json` — hand-written sample graph (milestone 1 artifact; to be replaced by pipeline output).
  - `requests-wiki.html` — built demo output.

## Status (2026-07-06)

- Milestone 1 done: viewer works (pan/zoom, click → detail panel, neighbor highlighting, search, URL-hash deep links) against the hand-written requests graph. User approved the demo.
- Next milestone: real pipeline — static analysis of `examples/requests` → LLM grouping → generated graph.json.

## Conventions

- Viewer is deliberately vanilla JS (no build step, output must work from `file://`). Python for the pipeline; Claude API for LLM steps.
