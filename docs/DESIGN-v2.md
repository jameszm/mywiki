# mywiki — Design v2: the multi-level architecture wiki

Synthesized 2026-07-13 from three independent design passes (data model / pipeline / viewer)
plus two adversarial reviews (consistency & integration; cost, scale & trust). Supersedes the
single-level portions of `DESIGN.md`; the product principles there still hold.

## 0. User requirements and locked decisions (2026-07-13)

The product: a **user-facing, interactive, web-page architecture wiki** containing *all*
knowledge about a repo — from the code itself, git commit history, GitHub issue/PR
discussions, and external web sources. Users first see the complete panoramic architecture
diagram, then click modules to drill into details, layer by layer.

Locked decisions:

1. **Granularity: function/class level.** Every class, function, and method is summarized
   and reachable in the UI. Methods are full graph nodes (children of classes) — their
   summaries come from the same per-file LLM pass, so node-hood is essentially free; their
   *detail* payloads are budget-gated (public or >10 LOC get LLM detail, the rest get
   deterministic facts-only panels).
2. **Delivery: one self-contained HTML file.** Everything pre-generated and inlined; works
   from `file://`; zero-dep vanilla JS + SVG viewer. "Dynamic" = in-page interactivity.
3. **Depth: unlimited drill-down** (component → [submodule] → file → class/function →
   method). Because of (2), "on-demand" means on-demand **rendering** of pre-generated,
   inlined data — never on-demand generation. Depth is adaptive per repo: requests needs no
   submodule level; a monorepo inserts them.
4. **Order of work: pure code graph first** (milestone 2b), then GitHub API enrichment
   (commits/issues/PRs/releases), then web search. The schema carries the external-knowledge
   envelope NOW (fields exist, arrays empty) so enrichment is additive.

Non-negotiable core principle (unchanged from v1): **graph structure comes from static
analysis only; the LLM adds meaning.** Every node groups real files/symbols; every edge is
traceable to real imports (later: calls). The LLM groups, names, labels, and explains — it can
never add, remove, or hide provable structure.

## 1. Architecture overview

```
数据层 (sources)          分析层 (pipeline, Python + Claude API)         展示层 (viewer)
────────────────          ─────────────────────────────────────         ───────────────
code (shallow clone)  →   analyze.py    skeleton.json   (no LLM)
                          summarize.py  summaries.json  (LLM: per-file, per-symbol; Batch; cached)
                          group.py      hierarchy.json  (LLM: component tree; 1 call, Opus)
                          aggregate.py  graphcore.json  (NO LLM: lifted edges + provenance)
                          details.py    details.json    (LLM: edge labels + node/edge prose; Batch)
                          assemble.py   graph.json      (NO LLM: layout, sanitize, citations)
git log ─────────────→    (milestone 3: knowledge envelope, kind:"code", type:"commit")
GitHub API ──────────→    (milestone 3: issues/PRs/releases → entity linking)
web search ──────────→    (milestone 4: docs/blogs/SO → entity linking)
                          build.py      wiki.html       (inject into viewer template)
```

Every intermediate artifact carries `meta: {stage, generated, prompt_version, input_hashes}` —
any stage re-runs in isolation; staleness is detectable; a crashed run resumes from cache.

## 2. graph.json v2 schema

### 2.1 Top-level shape

```json
{
  "meta": {
    "schemaVersion": 2,
    "title": "Requests — Architecture",
    "repo": "psf/requests", "repoUrl": "https://github.com/psf/requests",
    "commit": "<full sha — REQUIRED; v1's \"main\" breaks citation pinning>",
    "generated": "2026-07-13", "lang": "en",
    "pipeline": { "prompt_version": "2b.1", "models": { "...": "..." } },
    "limitations": ["nested functions not indexed", "import edges only (no call graph yet)"],
    "idAliases": { "sessions": "c/session-engine", "sessions-adapters": "E/c/session-engine~c/transport-adapters" }
  },
  "nodes":   [ /* FLAT array; hierarchy via parent field */ ],
  "edges":   [ /* base (leaf) edges only, with evidence */ ],
  "edgeAgg": { /* "E/<src>~<dst>" -> aggregated-pair record (all levels) */ },
  "details": { /* id -> {detail, citations, knowledge} — the lazy-load seam */ }
}
```

Key structural choices (each resolved against alternatives in review):

- **Flat `nodes` with `parent`** (not recursive nesting). The viewer builds parent/children
  indexes in one pass; edges and details are flat/keyed anyway; v1 files load as "all nodes
  with `parent: null`".
- **`edges` = base edges only** (file→file imports today; symbol→symbol calls later). The
  viewer computes the visible edge set at runtime by lifting base edges onto the currently
  visible frontier (§5.2) — pre-computing edges per expansion state is exponential and was
  rejected.
- **`edgeAgg`** is the pipeline's deterministic enumeration of *every lifted pair the viewer
  can ever produce* (§4.1), keyed by pair id, carrying weight/provenance/display and — for the
  curated subset — LLM label/summary. Viewer bucket-key lookup: hit → pipeline label; miss →
  impossible (validated at build time, gate V11).
- **`details`** is a separate id-keyed map holding panel-only payloads. Inlined in the MVP;
  for huge repos it shards into fetched chunks (packaging change only — the schema seam
  exists now). `details["repo"]` holds the repo overview shown when nothing is selected.

### 2.2 IDs and deep links

| prefix | pattern | example | stability |
|---|---|---|---|
| `c/` | `c/<slug>` | `c/session-engine` | LLM-invented; protocol-stabilized (below) |
| `f/` | `f/<repo-relative-path>` | `f/src/requests/sessions.py` | stable by code identity |
| `s/` | `s/<path>:<qualname>` | `s/src/requests/sessions.py:Session.request` | stable by code identity |
| `x/` | `x/<package>` | `x/urllib3` | stable |
| `E/` | `E/<srcId>~<dstId>` | `E/c/session-engine~c/models` | inherits endpoint stability |

Paths are percent-encoded for `#`, `%`, whitespace **and `~`** (reserved as the edge
separator) at id-generation time. The viewer never parses ids — ancestor chains come from the
parent index.

URL hashes keep v1 parameter names: `#node=<id>`, `#edge=<id>`. On navigation the viewer
resolves via the flat index, falls back to `meta.idAliases` (which carries v1→v2 mappings for
both nodes and edges), auto-expands the target's ancestor chain, focuses, selects.
`&open=<id>,<id>` is reserved (not MVP) for sharing curated multi-expansion views.

**Slug stability across regenerations:** the grouping prompt receives the previous run's
`{slug, label, member files}` and must reuse a slug when ≥50% of its files are retained;
Python enforces uniqueness; renames land in `idAliases`. (Deferred past 2b — first run seeds
aliases from the hand-written v1 ids. Recorded as an open integration item: `group.py --prev`.)

### 2.3 Nodes

```json
{ "id": "s/src/requests/sessions.py:Session", "parent": "f/src/requests/sessions.py",
  "kind": "class", "label": "Session", "sublabel": "class · line 395 · 19 methods",
  "x": 20, "y": 20,
  "summary": "Holds cross-request state (headers, cookies, adapters); request()/send() live here.",
  "facts": { "symKind": "class", "line": 395, "endLine": 903, "methodCount": 19 } }
```

- `kind`: `component | support | external` (LLM-assigned, grouping levels) ∪
  `submodule | file | class | function | method` (structural, from skeleton). Viewer CSS keys
  off it as in v1.
- `x, y` are **local to the parent's content frame** (root = v1 world coordinates). All child
  layouts are precomputed by the pipeline; the viewer does no layout math except make-room
  shifts (§5.3).
- `facts` is **static-analysis-only, never LLM-written** — the deterministic trust anchor
  rendered as chips (file: `{loc, doc, role}`; symbol: `{symKind, line, endLine, methodCount?}`;
  grouping: `{fileCount, loc}`).
- `summary` (LLM) is always inline (search/tooltips), ≤200 chars for symbols. `detail` lives
  in `details[id]`.
- Build-time invariant: every in-scope source file appears exactly once as an `f/` node; every
  skeleton class/function/method appears exactly once under its file. The LLM only *assigns*
  files to components and writes text.

### 2.4 Edges, aggregation, provenance

**Base edges** (in `edges`) carry evidence — machine-checkable pointers into source:

```json
{ "id": "E/f/src/requests/sessions.py~f/src/requests/adapters.py",
  "source": "f/src/requests/sessions.py", "target": "f/src/requests/adapters.py",
  "kind": "import", "label": "imports HTTPAdapter, BaseAdapter", "weight": 2,
  "evidence": [
    { "kind": "import", "path": "src/requests/sessions.py", "line": 23, "symbol": "HTTPAdapter",
      "url": "https://github.com/psf/requests/blob/<sha>/src/requests/sessions.py#L23" } ] }
```

**Aggregated pair records** (in `edgeAgg`, keyed by pair id) for every ancestor cross-pair:

```json
"E/c/session-engine~c/transport-adapters": {
  "kind": "import", "weight": 2, "display": "primary",
  "label": "send(PreparedRequest)", "category": "uses",
  "summary": "Session.send() picks an adapter by URL prefix and dispatches.",
  "aggregates": ["E/f/src/requests/sessions.py~f/src/requests/adapters.py"] }
```

- Provenance chain: **aggregated pair → `aggregates` → base edge → `evidence` →
  file:line:symbol → commit-pinned GitHub URL.** The panel renders this as an "Evidence" list;
  every hop is machine-checkable.
- `weight` = number of imported symbols (min 1) — one definition everywhere (stroke width,
  demotion tie-breaks, scorer).
- Two classification fields, two dimensions: `kind` is structural from analysis (`import` now,
  `call` when the call-graph pass exists); `category` is an LLM chip on curated pairs only.
  Until call evidence exists, `category` is restricted to non-runtime-claiming values
  (`uses | extends | configures | re-exports`) — `calls`/`creates`/`data-flow` are reserved.
- **Label vocabulary constraint (trust):** any symbol name appearing in an LLM edge label or
  summary must be ∈ that edge's imported-symbol set (mechanical check). The panel marks labels
  as "LLM interpretation — evidence below." This prevents smuggling call-level claims on
  import-level evidence, and prevents benchmark-matching from rewarding over-claiming.
- File-level edges get mechanical labels (`imports X, Y`); no LLM.
- External deps: `external_imports` becomes per-edge records in the skeleton; file→package
  edges lift like any other (this yields `adapters → urllib3` at L0 mechanically).

### 2.5 Details and the knowledge envelope

```json
"details": {
  "c/session-engine": {
    "detail": "<p>… sanitized HTML with <a href='…#L500'>sessions.py:500</a> citations …</p>",
    "citations": [ { "path": "src/requests/sessions.py", "line": 500, "endLine": 587,
                     "url": "…/blob/<sha>/src/requests/sessions.py#L500-L587",
                     "note": "request(): merge → prepare → send" } ],
    "knowledge": [] } }
```

Knowledge item envelope (fields fixed now, populated by milestones 3–4):
`{ kind: "code"|"external", type: issue|pr|release|commit|discussion|docs|blog|stackoverflow,
title, url, date, retrieved, authority: maintainer|official|community, body (sanitized HTML),
linkedBy: path-ref|label|semantic, conflicts_with?: [ids] }`.

- `kind:"code", type:"commit"` covers git-history enrichment; `authority` is an enum (renders
  as a badge; a float invites false precision); `conflicts_with` surfaces "docs say X, issue
  #482 says Y" per DESIGN.md.
- **Per-node knowledge cap: top-K≈5 items** by authority×engagement — part of the schema
  contract now, because knowledge volume scales with repo *popularity*, not repo size.
- Viewer renders external items in a visually distinct "From the web" section (tinted block,
  source pill, date badge, `FROM THE WEB` chip) — never mixed with code-fact styling.

## 3. Static analyzer amendments (prerequisite, gates everything)

One amendment list for `tools/analyze.py` (union of all three designs' needs):

1. Edges carry `[{symbol, line}]` per import, not bare `names`.
2. `end_lineno` captured for classes and functions (citation gate needs symbol spans).
3. Methods get `line` (+`end_lineno`).
4. `external_imports` becomes per-edge records `{source, target: pkg, names: [{symbol, line}]}`
   (otherwise `adapters→urllib3` has no evidence chain).
5. `meta` gains `commit` (`git rev-parse HEAD`) and `remote_url` when the repo is a checkout.
6. Fix the `role` heuristic: `docs/**` currently classifies as "source".

Known blind spots (documented in `meta.limitations`, accepted): nested functions, dynamic
imports.

**Graph scope predicate** (applied once, at pipeline input): graph files = the files handed to
grouping = the repo's importable source (for requests: the 19 `src/requests/**` files; tests
and `docs/` excluded; `setup.py` excluded from the graph — packaging facts can live in meta).
Leaf edges = core→core (73 for requests) + file→external. External nodes = top external
packages by fan-in (mechanical; for requests: urllib3, charset_normalizer, idna, certifi).

## 4. Deterministic core (no LLM)

### 4.1 Edge lifting (`aggregate.py`)

Full ancestor cross-product with containment filtering (NOT index-paired zip, which silently
drops pairs when chains have different depths):

```python
agg = {}   # (a_id, b_id) -> {weight, symbols, aggregates[]}
for e in leaf_edges:
    for a in ancestors(e.source):        # [file, (submodule), component]
        for b in ancestors(e.target):
            if a == b or is_ancestor(a, b) or is_ancestor(b, a):
                continue                 # containment, not an edge
            bump(agg[(a.id, b.id)], e)
```

O(E × depth²) — trivial. This enumeration is exactly the set of buckets the viewer's runtime
lift can produce; a unit test asserts equality against a reference implementation of the
viewer's `lift()` over all expansion states of a fixture (gate V11 checks coverage at build
time).

### 4.2 Panorama curation (the hairball problem — measured, not hoped away)

Lifting the 73 requests core edges onto the hand-written 10-component grouping yields **31 L0
pairs**; the approved demo draws 12. Fan-in concentrates on `models` (8, kind=component!),
`utils` (6), `cookies` (5) — a support-only demotion rule provably cannot reach 12. Merged
mechanism:

1. **Deterministic demotion (generalized):** for any target with primary in-degree > K (K≈4),
   keep top-K incoming by weight, demote the rest to `secondary` — regardless of node kind.
   Tie-break: weight, symbol count, source id.
2. **`__init__.py` re-export edges** are `secondary` by rule (detectable from the skeleton).
3. **LLM curation is demote-only:** the edge-label pass may demote `primary → secondary`,
   never promote, never hide, never add/delete. Schema-validated.
4. **Hard validator cap:** primary edges ≤ 1.5 × component count.
5. Every provable edge stays in the JSON with full provenance; secondary renders faint/on-hover
   and always appears in Connections panels. The scorer counts primary only and reports the
   primary *count* (the "tells its story in ~12 edges" property is regression-tested).

### 4.3 Layout (`assemble.py`)

Layered Sugiyama-lite per level (NOT force-directed — determinism and the left→right pipeline
story win): Tarjan SCC collapse → longest-path layering on primary edges → 3 barycenter sweeps
(ties by id) → `x = layer·300, y = slot·120`; support nodes pinned to the bottom row, external
to the rightmost layer (the hand-written graph's visual grammar). Grid fallback for levels with
>24 nodes. Children laid out in the parent's local frame. Zero RNG ⇒ identical inputs give
identical layout; `--prev` coordinate carry-over is a later flag. Hand-tuned coordinates
survive only in the legacy v1 demo.

### 4.4 Validation gates

| # | Gate | Stage |
|---|---|---|
| V1 | Strict structured-output parse; **`stop_reason=="max_tokens"` routes to chunking, not diff-retry** | all LLM |
| V2 | Symbol coverage: output set == skeleton set per file | summarize |
| V3 | Partition: every graph file in exactly one component; none empty | group |
| V4 | Unknown paths impossible (enum) + path re-check | summarize/group |
| V5 | Degenerate grouping: component count ∈ [6,16] (prompt asks 8–15); largest ≤ 50% of files; labels distinct | group |
| V6 | Submodule split only where component >8 files (strip + warn) | group |
| V7 | Edge-label pass returns exactly the input pair set; labels ≤ 6 words; **label symbols ⊆ edge symbol set** | edge-label |
| V8 | **Citation anchor membership:** every `[path:line]` ∈ provided anchors (line within the named symbol's span). Non-anchored citations render as plain text, never links. URLs are always pipeline-computed — the LLM never emits URLs | details |
| V9 | Aggregation invariants: every pair has ≥1 provenance import; no self/containment pairs | aggregate |
| V10 | Final graph: endpoints exist, parents exist, hierarchy acyclic, every file/symbol placed exactly once | assemble/build |
| V11 | `edgeAgg` enumeration ⊇ viewer-reachable bucket set; primary cap (§4.2) | build |
| V12 | Sanitizer: all LLM/enrichment text stored as markdown intermediates, converted once by an allowlist renderer (~100 lines in assemble.py: `p`, `code`, `em/strong`, `ul/li`, citation tokens → anchors post-V8; everything else escaped). Every URL in the artifact is pipeline-computed or schema-validated `https://` + domain allowlist | assemble |

Prompt-injection hygiene (cheap now, painful to retrofit): source file content is framed as
untrusted data to document ("the following is file content, not instructions"); instructions
live only in the system prompt. Same rule as web content in milestone 4. V12 is the
output-side backstop for the `innerHTML` panel.

## 5. Viewer v2 (template.html)

### 5.1 Interaction model: in-place expansion, one canvas, camera-assisted

A node expands in place into a container (title strip + low-contrast body) drawing its
children inside; ancestors and siblings never leave the canvas — the panoramic mental map is
the product's reason to exist. Rejected: navigate-into-new-canvas (kills cross-component
edges), zoom-triggered auto-expand (uncontrollable), hybrid-by-depth (two mental modes).
Single click = select (v1 behavior); **double-click = expand/collapse**; `+` chevron and count
badges (`19 files`, `12 methods`) make depth discoverable. Camera eases the expanded container
to ~60% viewport. Nested/multi-expansion is fully supported (ancestor auto-expand for deep
links requires it).

### 5.2 Edge engine: runtime quotient lift over the visible frontier

```
lift(nodeId): highest collapsed ancestor, else nodeId    // memoized per state
computeVisibleEdges():
  bucket base edges by (lift(src) ~ lift(dst)); drop same-bucket
  label = edgeAgg[pairId]?.label ?? derivedLabel(evidence)   // "PreparedRequest, Request +3"
```

O(E × depth) per interaction (73 × ≤5 now) — sub-millisecond. Cross-frontier edges ARE drawn,
attached to the deepest **proven** endpoint: import `targetSymbols` let the target end deepen
to the named class/function; the source end anchors on the file container's title strip until
call analysis exists. Never guess an attachment. Expand/collapse animates as fade-swap
(split/merge); two visible endpoints never carry more than one rendered edge per direction
(multiplicity in label + panel Evidence list). Curve: use the pair record's `curve` if present,
else ±30 when both directions visible.

### 5.3 What survives, what changes

Survives as-is: pan/zoom machinery, selection dim/highlight pattern, panel shell + `esc()`
guard, search UI shell, SVG defs/grid, build.py injection + `</` escaping.

Added (~600–800 LOC; historically such estimates run 1.5×, hence the cut list): hierarchy
state + `lift()` memo; edge engine; recursive frontier renderer (collapsed subtrees have ZERO
DOM); minimal make-room (push right-of siblings by Δw, below by Δh, propagate to root —
deterministic, order-preserving); camera assist; search v2; hash v2; panel v2; container CSS.

**Deferred past 2b** (not needed at requests scale — ~2,200–2,600 SVG elements fully expanded,
well under budget): pushState history, `&open=` param, touch pinch, LOD culling, LRU
auto-collapse, animation polish (pulse rings, breadcrumb accent decay). One rule kept for
later: when navigating to a child suppressed by a future "top 50 + N more" cap, force-render
its ancestors' capped lists — otherwise deep links silently no-op on big repos.

### 5.4 Search, deep links, panel

- **Search:** flat all-depth index built at load (`{id, label, kind, qualifiedPath}`,
  ~330 entries); ranking exact > prefix > substring, leaf symbols boosted on exact hits.
  Result rows show kind chip + dim qualified path (`Session Engine › sessions.py › Session ›
  request()`). Jump = expand ancestor chain → make-room → camera frame → select.
- **Deep links:** `#node=`/`#edge=` + `idAliases` fallback + ancestor auto-expand (§2.2).
- **Panel v2**, top to bottom: header (kind chip, title, clickable breadcrumb) → **code
  facts** (`FROM CODE` chip; LLM prose with `sessions.py:500` citation links pinned to
  `meta.commit`) → **structure** (deterministic: LOC, child counts, clickable children,
  in/out connections — always renders even if payload generation failed) → **external
  knowledge** (empty-state one-liner in 2b; full renderer in milestone 3) → edge panels add
  **Evidence**: each base edge as `sessions.py → models.py · imports PreparedRequest, Request`
  with its line link. Header count line shows L0 nodes / primary L0 edges.

## 6. LLM stages

### 6.1 `summarize.py` — per-file, per-symbol (stage A)

One call per graph file (whole file + skeleton symbol checklist; whole-file beats slices
because symbol meaning depends on module context). Strict structured output; `name` fields are
enum-constrained to the skeleton's symbol list; exact-set coverage is a Python validator with
diff-message retry (≤2). `max_tokens=16000` (measured: `utils.py`-class files exceed 8K; a
max_tokens truncation must route to per-symbol chunking, not retry — V1). Prompt asks what each
symbol is *for*, one-line summaries + 2–4 sentence details for classes/nontrivial functions;
"if the docstring and the body disagree, describe the body's behavior."

Batch API, one request per cache miss. Cache key
`sha256(model + prompt_version + schema_version + lang + file_bytes)`; layout
`.mywiki-cache/summaries/ab/<hash>.json`. Unchanged-repo re-run = $0.

### 6.2 `group.py` — the make-or-break call (stage B)

Single call (requests input ≈7.5K tokens; grouping quality needs all files + all edges in one
context). Input: file cards (path, loc, role, docstring, top symbol names w/ stage-A one-liners)
+ edge list + external imports. Prompt core: "group into 8–15 components — the boxes a
maintainer would draw on a whiteboard; a component is a responsibility, not a directory; every
file in exactly one component; do not describe relationships." Output schema: components
`{slug, label, kind: component|support, summary, files (enum-constrained)}` + optional
submodules. Partition enforcement in Python (V3) with diff retry; deterministic fallback:
assign stragglers by import affinity, stamped `assignedBy: "fallback"`.

Model: `claude-opus-4-8`, direct (not batch — interactive retry loop), effort high.
Escalation path documented (map/reduce grouping) with trigger at ~300–400 files or first
observed quality drop — quality degrades long before the context limit does.

### 6.3 Edge-label pass (stage C2) and details (stage D)

- **C2:** ONE call for all curated pairs (primary L0 + submodule-level): receives endpoints'
  labels/summaries, symbols, weight, top provenance lines; returns `{pairId (enum), label,
  category, summary, display (demote-only)}`. One call ⇒ stylistically consistent labels.
- **D:** LLM prose ONLY for: repo overview (1), component nodes (~8–12), external nodes (~4),
  primary L0 edges (~12–16) ≈ **~30 batched calls**. File/class/function/method payloads are
  **assembled from stage A output** — zero extra calls for the deepest, most numerous levels.
  Each call gets a **facts list of citable anchors** `(path, line..endLine, symbol)`; citations
  validated by V8 anchor membership. Uncited component labels/summaries render without the
  `FROM CODE` chip.

### 6.4 Cost (requests, function/class granularity, verified pricing)

| Stage | Calls | Model / mode | Cost |
|---|---|---|---|
| A. Symbol summaries | ~19 (batch) | Haiku 4.5 batch | $0.12 |
| B. Grouping | 1 (+≤2 retries) | Opus 4.8 direct, effort high | $0.08 |
| C2. Edge labels | 1 | Opus 4.8 direct | $0.08 |
| D. Details | ~30 (batch) | Opus 4.8 batch | $0.53 |
| **Total** | **~52** | | **≈ $0.80/run** |

Re-run on unchanged repo ≈ $0 (cache). ~Linear in LOC (A) and node count (D); a 100-file repo
lands ~$5–8. Wall-clock: typically 1–2 h (two sequential batches; 24 h worst case each —
pipeline is resumable, don't promise same-hour turnaround). Every LLM script preflights
credentials (construct client + try a `count_tokens` call — `ANTHROPIC_API_KEY` may be absent
on this machine); `--dry-run` prints call counts + cost estimate keylessly.

## 7. Size & scale

Requests at full depth with the merged payload economics (method nodes; LLM prose only where
§6.3 says): ≈ 250–350 KB single HTML. Honest full-depth ceiling ≈ 800–1,000 source files.
Escape hatches, in order: (1) detail-depth budget — structure stays complete, LLM details only
to files + top-K central symbols, facts-only panels below (no schema change); (2) gzip+base64
via `DecompressionStream` (net ~3–3.8×, works from `file://`); (3) bundle variant — `details`
shards fetched per component (packaging change; drops `file://`). The enrichment byte-budget
(knowledge cap, §2.5) is part of this table, not an afterthought — knowledge scales with
popularity, not size.

Viewer budget: ~2,200–2,600 SVG elements fully expanded (requests); collapsed subtrees have
zero DOM, so a 10× repo opens with the same ~10-element panorama. Deferred LOD/LRU guards kick
in only past ~6K live elements.

## 8. Quality benchmark (`score.py`)

Score generated L0 against hand-written `examples/requests.graph.json` on every prompt change:

1. **Node alignment:** greedy best-match by Jaccard over file sets — computed over
   benchmark-covered files only, after extending the hand-written reference to place the 8
   files it currently ignores (10-minute task, do first).
2. **Edge recovery:** map hand-written edges through the alignment; hit iff a primary pair
   exists in the same direction. Include external nodes (`adapters→urllib3` comes from
   external-import lifting). Bar: **≥10/12 recovered**; report primary count (~12–18 target)
   alongside — recall alone can pass while the panorama hairballs.
3. **Labels:** side-by-side eyeball table (no auto-score; hand-written labels are call-level
   stories — a naive label-match objective would train over-claiming, see §2.4).

Pass bar for 2b sign-off: mean Jaccard ≥ 0.6, ≥8/10 nodes at J ≥ 0.5, edge recovery ≥10/12,
primary count ≤ 1.5× components, plus a sampled human spot-check of 10 symbol summaries.

## 9. Milestone plan (revised)

- **2b-0 (prereq, ~1 h):** analyzer amendments (§3) + scope predicate. Re-run on requests.
- **2b-1 (LLM-free end-to-end — the integration artifact):** schema v2 + `aggregate.py` +
  `assemble.py` + `build.py` v2 validation + **`--grouping trivial` mode** (deterministic
  file-based grouping, mechanical labels, facts-only panels, zero API calls). Produces a real
  v2 graph.json from the existing skeleton immediately: the viewer's dev fixture, the keyless
  CI path, and the no-API-key degraded product mode, all in one.
- **2b-2 (viewer v2):** develop against the trivial fixture (§5, with the cut list).
- **2b-3 (LLM stages):** `summarize.py` → `group.py` + `score.py` (iterate grouping prompts
  against the benchmark HERE — this is the risk concentrator) → C2/D → full run on requests →
  benchmark sign-off. Extend the hand-written reference first (§8.1).
- **3 (GitHub enrichment):** commits + issues/PRs/releases → entity linking → knowledge
  envelopes (schema already shipped). **4 (web search enrichment).** Unchanged from DESIGN.md.

Open items (decided defaults, flagged to user): output language `--lang zh|en` (in cache keys
and `meta`; default zh for the user's own runs — confirm); method-node granularity confirmed
as full nodes per locked decision 1; slug-stability protocol deferred past 2b (§2.2).

## 10. CLI contracts

| Script | LLM | Contract |
|---|---|---|
| `analyze.py` | no | repo → skeleton.json (amended per §3) |
| `summarize.py` | batch | skeleton + repo → summaries.json (`--model --cache-dir --no-batch --lang --dry-run`) |
| `group.py` | direct ×1–3 | skeleton + summaries → hierarchy.json (`--grouping trivial\|llm`, `--retries`, later `--prev`) |
| `aggregate.py` | **no** | skeleton + hierarchy → graphcore.json (nodes all levels, edgeAgg, curation, external nodes) |
| `details.py` | direct ×1 + batch | graphcore + summaries → details.json |
| `assemble.py` | no | graphcore + details + summaries → graph.json (layout, sanitize, citation URLs) |
| `score.py` | no | generated + reference → report (CI on prompt changes) |
| `pipeline.py` | orchestrates | repo path/URL → wiki.html; ingest = `git clone --depth 1` + `rev-parse HEAD` + `remote get-url origin`; credential preflight before any LLM stage; `--dry-run`, `--from-stage` |
| `build.py` | no | graph.json → html (v2 validation: V10/V11) |

All: Python 3 stdlib + `anthropic` SDK only; idempotent; non-zero exit with the printed diff on
any hard validation failure.
