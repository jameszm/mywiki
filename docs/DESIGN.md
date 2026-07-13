# mywiki — Design Notes

Captured from the design discussion on 2026-07-05.

> **2026-07-13:** the multi-level (semantic-zoom) design is now fully specified in
> [`DESIGN-v2.md`](DESIGN-v2.md) — graph.json v2 schema, pipeline stages, viewer v2,
> validation gates, and the revised milestone plan. This file remains the product-level
> rationale; where the two disagree on mechanism, DESIGN-v2 wins.

## What we're building

A tool that analyzes a GitHub repository and produces an **interactive architecture wiki**: a single HTML page showing a panoramic graph of the system. Clicking any node (component) or edge (relationship) opens a detail panel explaining it, with citations linking to the actual source lines on GitHub.

Reference point: DeepWiki — but differentiated by (a) the interactive graph as the primary artifact instead of markdown pages, and (b) enrichment from online sources, not just code.

## Core principle

**Derive the graph's existence from static analysis; use the LLM for meaning.**

- Static analysis (tree-sitter, import/call graphs, file tree, git history) produces the ground-truth skeleton — nodes and edges that provably exist.
- The LLM then: groups hundreds of files into 10–20 meaningful components, names them in human language, classifies edges ("payment service calls the ledger via the repository pattern"), and writes the click-through explanations.
- This avoids hallucinated edges, which would destroy user trust.

## Pipeline

1. **Ingest** — shallow clone; filter vendored deps, binaries, lockfiles.
2. **Static analysis** — file tree, language breakdown, dependency graph, exported symbols, entry points (no LLM; cheap).
3. **Bottom-up summarization** — file summaries → module summaries → repo summary. Cacheable per file content hash. Use Batch API (50% cost) since not latency-sensitive.
4. **External enrichment** (parallel stage) — GitHub API first (issues/PRs/discussions/releases/milestones — structured, free, 5k req/hr); then web search/fetch for blogs, tutorials, Stack Overflow. Rank issues by engagement, summarize clusters rather than individual items.
5. **Entity linking** — attach external content to graph nodes/edges via (a) explicit file/path references in issues/PRs, (b) issue labels, (c) embedding/LLM matching for vague content.
6. **Grouping/hierarchy** (the make-or-break LLM step) — build the semantic-zoom hierarchy: Level 0 = whiteboard-style panoramic view (8–15 components), Level 1 = internal sub-modules, edges aggregate upward.
7. **Detail payload generation** — one small structured-output call per node and edge, weaving code understanding + linked external content, with citations. Pre-generate levels 0–1 (~150 calls typical).
8. **Render** — inject graph JSON + payloads (markdown pre-converted to HTML) into the prebuilt viewer template → emit one self-contained `.html`.

## Trust & provenance

- Two visually distinct classes of info: **facts from code** (ground truth) vs **claims from the web**.
- Every external snippet carries source URL, date, type. Weight by authority (maintainer > docs > random blog) and freshness (post-latest-release > older).
- Surface conflicts explicitly ("docs say X, but issue #482 suggests this changed in v3").
- Security: web/issue text is untrusted LLM input (prompt-injection risk) — treat as data to summarize, keep instructions in the system prompt.
- Licensing: summarize and link; never republish full content.

## Output format

- **MVP: one self-contained `.html` file** — viewer bundle (React Flow or Cytoscape + ELK layout) + inlined JSON data. Works offline, from `file://`, on GitHub Pages/S3. Low single-digit MB.
- Embed metadata (indexed commit SHA, generation date) visibly on the page.
- URL-hash deep links (`page.html#node=billing-engine`) for sharing.
- Later: static bundle with lazy-loaded payloads (for huge repos), then hosted app with live chat-per-component (same viewer, data served by API — packaging change, not rewrite).

## Incremental updates

- Changed files map to specific nodes/edges → regenerate only those payloads.
- Keep layout stable across updates (users remember where things were).
- External enrichment refreshes on its own cadence (weekly / on release), independent of code re-indexing.

## Cost levers

- Per-file summary cache keyed by content hash (never recompute unchanged files).
- Prompt caching for shared context within a run; Batch API for fan-out stages.
- Model tiering: cheaper model for mechanical file summaries; top model for grouping and page writing.

## MVP milestones

1. HTML viewer against a **hand-written sample `graph.json`** for `examples/requests` — nail the interaction (pan/zoom, click → panel, expand, search) before any pipeline code.
2. Static analysis + grouping for requests → real graph.json.
3. Detail payload generation with citations.
4. GitHub-API enrichment (issues/releases) + entity linking.
5. Web-search enrichment.

## Open questions

- Final viewer library choice: React Flow (better DX, recommended) vs Cytoscape (better at huge graphs).
- graph.json schema design.
- Grouping prompt strategy and evaluation (does Level 0 "tell the right story"?).
- Automatic layout tuning (ELK) so the panoramic view looks deliberate, not hairball.
