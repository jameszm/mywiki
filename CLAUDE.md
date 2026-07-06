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

- `examples/` — test repositories (gitignored clones). Current test subject: `psf/requests` (see `examples/README.md` for why).

## Conventions

- Nothing built yet — tech stack not finalized. Leaning: React Flow + ELK for the viewer; Python for the analysis pipeline; Claude API for LLM steps.
