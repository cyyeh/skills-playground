# Graphify — System Analysis

## Overview

<!-- level:beginner -->

**Graphify** is an AI coding assistant skill that turns any folder of code, documents, papers, and images into a queryable knowledge graph. You type `/graphify .` in Claude Code (or Codex, OpenCode, OpenClaw, Factory Droid), and it reads your files, builds a persistent knowledge graph, and gives you back structure you didn't know was there.

**The problem it solves:** AI coding assistants have no persistent memory of your codebase. Every session, they re-read raw files to re-establish context. This is expensive in tokens and loses structural understanding — the AI sees text, not architecture. Graphify changes this by creating a compact, structured representation that persists across sessions.

**The origin story:** On April 2, 2026, Andrej Karpathy posted about his `raw/` folder workflow — dropping papers, code, screenshots, and notes into a folder for LLM consumption — and issued a public challenge: "I think there is room here for an incredible new product." Safi Shamsi (safishamsi) built Graphify within 48 hours.

**Key numbers:**
- **71.5x fewer tokens per query** vs reading raw files (on a 52-file mixed corpus)
- **19 programming languages** supported via tree-sitter AST parsing
- **Multimodal:** code, PDFs, markdown, screenshots, diagrams, whiteboard photos
- **Zero infrastructure:** no database, no Docker, no config files — just `pip install graphifyy`

**What you get:**
- `graph.html` — interactive visualization (click nodes, search, filter by community)
- `GRAPH_REPORT.md` — god nodes, surprising connections, suggested questions
- `graph.json` — persistent graph for querying weeks later without re-reading files
- `cache/` — SHA256 cache so re-runs only process changed files

<!-- level:intermediate -->

**How it compares to alternatives:**

| Tool | Approach | Key Difference from Graphify |
|------|----------|------------------------------|
| Microsoft GraphRAG | Fully LLM-driven extraction on text corpora | Designed for enterprise documents, not codebases; requires vector DB |
| code-review-graph | Tree-sitter + SQLite, focused on code review | Narrower scope — optimizes review file sets, not general understanding |
| Understand-Anything | Multi-agent pipeline with web dashboard | Less transparency — no EXTRACTED/INFERRED/AMBIGUOUS confidence tiers |
| FalkorDB CodeGraph | GraphRAG-SDK with Neo4j backend | Heavy infrastructure; Graphify deliberately avoids external databases |

**Key architectural insight:** Graphify splits extraction into two passes. Pass 1 is deterministic AST parsing (tree-sitter) for code — free, fast, reproducible. Pass 2 uses LLM subagents for docs/papers/images — probabilistic but honest about it via confidence tiers. This hybrid approach means you only pay LLM costs for unstructured content.

---

## Concepts

### The Knowledge Graph Model

<!-- level:beginner -->

A knowledge graph is a network of **nodes** (things) connected by **edges** (relationships). In Graphify:

- **Nodes** represent code entities (functions, classes, modules), concepts from documents, and rationale fragments (design decisions extracted from comments)
- **Edges** represent relationships: `calls`, `imports`, `contains`, `inherits`, `semantically_similar_to`, `rationale_for`
- **Communities** are clusters of densely-connected nodes discovered automatically

Think of it like a map of your codebase where connected things are grouped together, and you can see which concepts bridge different areas.

### Confidence Tiers

<!-- level:beginner -->

Every relationship in the graph is tagged with a confidence level:

| Label | Meaning | Example |
|-------|---------|---------|
| **EXTRACTED** | Found directly in source code | An `import` statement, a direct function call |
| **INFERRED** | Reasonable deduction from context | Two functions that likely call each other based on name matching |
| **AMBIGUOUS** | Uncertain — flagged for human review | A possible relationship that could go either way |

This is Graphify's honesty mechanism. You always know what was found vs. what was guessed.

<!-- level:intermediate -->

EXTRACTED edges always have confidence score 1.0. INFERRED edges carry a score between 0.0 and 1.0 reflecting how confident the model was. AMBIGUOUS edges are explicitly flagged for review in the GRAPH_REPORT.md output.

The confidence tiers directly influence:
- **Report sorting:** AMBIGUOUS connections surface first in "surprising connections"
- **Question generation:** The system generates questions about ambiguous relationships
- **Surprise scoring:** Lower confidence + cross-file-type = higher surprise score

### Node Types

<!-- level:intermediate -->

Graphify creates several types of nodes:

| Node Type | Source | `file_type` | How Created |
|-----------|--------|-------------|-------------|
| Function | Code files | `code` | Tree-sitter AST parsing |
| Class | Code files | `code` | Tree-sitter AST parsing |
| Import/Module | Code files | `code` | Tree-sitter AST parsing |
| Concept | Docs/papers | `document` or `paper` | Claude semantic extraction |
| Visual concept | Images | `image` | Claude vision extraction |
| Rationale | Code comments | `rationale` | Comment pattern matching (`# WHY:`, `# NOTE:`, `# HACK:`) |

### Communities (Clustering)

<!-- level:beginner -->

Graphify automatically groups related nodes into **communities** using the Leiden algorithm. Communities emerge from graph topology — nodes that are densely connected end up grouped together.

For example, in a web application, you might see:
- Community 0: Authentication (login, session, tokens)
- Community 1: Database layer (models, queries, migrations)
- Community 2: API endpoints (routes, handlers, middleware)

<!-- level:intermediate -->

The clustering is **topology-based, not embedding-based**. There is no separate vector database or embedding step. Semantic similarity edges that Claude extracts (`semantically_similar_to`) are already in the graph as INFERRED edges, so they influence community detection directly.

**Why Leiden over Louvain?** Leiden guarantees well-connected communities and runs faster. If graspologic (which provides Leiden) is not installed, Graphify falls back to NetworkX's built-in Louvain with tuned parameters (`max_level=10`, `threshold=1e-4`) to prevent hangs on large sparse graphs.

<!-- level:advanced -->

**Oversized community splitting:** If a community contains more than 25% of graph nodes (and at least 10 nodes), Graphify recursively extracts its subgraph and re-runs Leiden. This prevents one giant cluster from dominating the analysis.

**Cohesion scoring:** Each community gets a cohesion score — the ratio of actual intra-community edges to maximum possible edges (0.0–1.0). Low-cohesion communities (< 0.15) are flagged in the suggested questions as candidates for splitting.

### God Nodes

<!-- level:beginner -->

**God nodes** are the highest-degree concepts — what everything connects through. They're the architectural pillars of your codebase. If you remove a god node, large parts of the graph would disconnect.

<!-- level:intermediate -->

God nodes are computed by sorting nodes by degree (number of edges) and filtering out:
- File-level hubs (label matches source filename — these are just containers)
- Method stubs (`.method_name()` — too granular)
- Isolated functions (degree ≤ 1 — not actually well-connected)
- Concept nodes (empty `source_file` — manually injected, not structural)

### Surprising Connections

<!-- level:intermediate -->

These are edges ranked by a **surprise score** — a multi-factor composition:

```
score = 0
+ confidence_bonus (AMBIGUOUS +3, INFERRED +2, EXTRACTED +1)
+ 2 if crosses file types (code ↔ paper/image)
+ 2 if different top-level directories (cross-repo)
+ 1 if cross-community
× 1.5 if semantically_similar_to relation
+ 1 if peripheral-to-hub (low-degree node reaching god node)
```

The weighting ensures diverse surprise signals. A confident but cross-repo connection ranks higher than an uncertain same-file edge.

### Hyperedges

<!-- level:advanced -->

Some relationships connect 3+ nodes and can't be expressed as pairwise edges. Examples: all classes implementing a shared protocol, all functions in an authentication flow, all concepts from a paper section forming one idea.

Hyperedges are stored as metadata on the graph object (`G.graph["hyperedges"]`) and rendered as shaded convex hulls in the HTML visualization.

---

## Architecture

### Pipeline Overview

<!-- level:beginner -->

Graphify runs a sequential pipeline where each stage feeds into the next:

```
detect() → extract() → build_graph() → cluster() → analyze() → report() → export()
```

Each stage is a single function in its own module. They communicate through plain Python dicts and NetworkX graphs — no shared state, no side effects outside `graphify-out/`.

<!-- level:intermediate -->

### Module Map

| Module | Function | Input → Output |
|--------|----------|----------------|
| `detect.py` | `collect_files(root)` | directory → filtered file list with classification |
| `extract.py` | `extract(path)` | file path → `{nodes, edges}` dict |
| `build.py` | `build_graph(extractions)` | list of extraction dicts → `nx.Graph` |
| `cluster.py` | `cluster(G)` | graph → graph with `community` attr on each node |
| `analyze.py` | `analyze(G)` | graph → analysis dict (god nodes, surprises, questions) |
| `report.py` | `render_report(G, analysis)` | graph + analysis → GRAPH_REPORT.md string |
| `export.py` | `export(G, out_dir, ...)` | graph → JSON, HTML, Obsidian vault, SVG, GraphML, Cypher |

Supporting modules:
| Module | Purpose |
|--------|---------|
| `cache.py` | SHA256-based extraction caching for fast `--update` runs |
| `validate.py` | Schema validation for extraction output |
| `security.py` | URL validation, path traversal prevention, label sanitization |
| `ingest.py` | Fetch URLs (tweets, papers, webpages) and save as annotated markdown |
| `serve.py` | MCP stdio server for agent-queryable graph |
| `watch.py` | File system monitoring for auto-rebuild |
| `hooks.py` | Git hook installation (post-commit, post-checkout) |
| `benchmark.py` | Token reduction measurement |
| `wiki.py` | Wikipedia-style markdown export per community |

### Data Flow

<!-- level:intermediate -->

**Main pipeline (when you run `/graphify .`):**

```
User: /graphify ./raw
         │
         ▼
    detect(root)
         │ files: {code: [...], doc: [...], paper: [...], image: [...]}
         ▼
    extract(code_files)          ← Pass 1: deterministic AST (free, fast)
         │ extraction_code: {nodes, edges}
         ▼
    [parallel subagents]         ← Pass 2: Claude semantic extraction (costs tokens)
    extract_semantic(docs/papers/images)
         │ extraction_semantic: {nodes, edges}
         ▼
    build([code_extraction, semantic_extraction])
         │ G: nx.Graph (merged)
         ▼
    cluster(G)
         │ communities: {0: [nodes], 1: [nodes], ...}
         ▼
    analyze(G, communities)
         │ god_nodes, surprising_connections, suggested_questions
         ▼
    report(G, analysis) → GRAPH_REPORT.md
         │
         ▼
    export(G, communities) → graph.json, graph.html, ...
```

**Incremental update (`--update` mode):**

```
detect_incremental(root) → only new/modified files (via manifest mtime comparison)
         │
    reprocess only new files
         │
    load existing graph.json → merge with new extractions → re-cluster → re-export
```

<!-- level:advanced -->

### Design Principles

**No shared state, pure composition:** Each module consumes dicts/graphs and produces dicts/graphs. No globals, no hidden dependencies. This enables unit testing with fixtures, parallel subagent dispatch, and intermediate output inspection.

**Lazy imports for skill bootstrap:** `__init__.py` uses `__getattr__` to defer imports until needed. Reason: `graphify install` must work before heavy dependencies (tree-sitter, NetworkX, graspologic) are installed.

**Extraction schema is language-agnostic:** A single `LanguageConfig` dataclass template supports all 19 languages. Customization points include AST node type names, field names, import handlers, and language-specific post-processing functions. Adding a new language means defining a new `LanguageConfig` instance.

---

## Implementation Details

### File Detection (`detect.py`)

<!-- level:intermediate -->

The detection module classifies files into four types using a `FileType` enum: CODE, DOCUMENT, PAPER, IMAGE.

**Paper detection heuristic:** PDFs are classified as PAPER if the first 3000 characters contain 3+ signals from: arXiv ID patterns, "doi:", "abstract", citation patterns, "we propose", "literature". This avoids treating every PDF as an academic paper.

**Security filtering:** `_is_sensitive()` blocks files matching patterns for `.env`, `.pem`, `.key`, credentials, AWS/GCP service accounts.

**Performance:** Uses in-place directory pruning (`dirnames[:] = [...]`) during `os.walk` to skip `.git`, `node_modules`, virtual environments, and `.graphifyignore` patterns.

**Corpus health warnings:** Flags if corpus < 50K words ("may not need graph") or > 500K words / > 200 files ("expensive token cost").

### AST Extraction (`extract.py`)

<!-- level:intermediate -->

The extraction module is the heart of Pass 1. It uses tree-sitter to parse source files into concrete syntax trees, then walks the tree to extract nodes and edges.

**The `LanguageConfig` dataclass:**

```python
class LanguageConfig:
    ts_module: str                    # e.g., "tree_sitter_python"
    class_types: frozenset            # AST node types that represent classes
    function_types: frozenset         # AST node types that represent functions
    call_types: frozenset             # AST node types that represent function calls
    import_types: frozenset           # AST node types that represent imports
    name_field: str                   # Field name for extracting identifiers
    body_field: str                   # Field containing function/class body
    call_function_field: str          # Field on call nodes for the callee
    call_accessor_node_types: frozenset  # Member access nodes (e.g., attribute)
    resolve_function_name_fn: Callable   # Language-specific name resolution
    extra_walk_fn: Callable              # Post-processing (JS arrow functions, C# namespaces)
```

All 19 languages are defined as instances of this template.

<!-- level:advanced -->

**Two-pass call graph inference:** First pass builds basic AST structure. Second pass walks function bodies to find call sites, building a "call name" by concatenating the callee expression (e.g., `self.helper()` → `self_helper`). Then tries to match against known function IDs. Matches become INFERRED "calls" edges.

**Node deduplication (three layers):**
1. Within file: `seen_ids` set tracks emitted node IDs
2. Between files: NetworkX `add_node()` is idempotent; semantic nodes overwrite AST nodes (intentional)
3. Pre-build merge: Skill deduplicates cached and new semantic extractions

**Rationale extraction:** Captures inline comments with markers: `# WHY:`, `# NOTE:`, `# IMPORTANT:`, `# HACK:`. These become separate `rationale_for` nodes, linking back to the source entity via edges.

**Language-specific subtleties:**
- Python: decorators, class inheritance, `__init__` methods, module-level functions
- JavaScript: arrow functions via `extra_walk` (not in standard body field), CommonJS vs ES6
- C/C++: function names inside declarators (extra indirection), header includes as imports
- C#: namespaces as containers, using statements
- Kotlin: data classes, extension functions
- Swift: initializers, extensions, protocol conformance

### Graph Building (`build.py`)

<!-- level:intermediate -->

The build module merges extraction results into a unified NetworkX graph.

- Validates each extraction against schema (required fields, confidence values)
- Dangling edges (referencing stdlib/external nodes) are silently dropped
- Preserves original edge direction via `_src` and `_tgt` attributes (the graph is undirected but directional metadata is kept)
- Hyperedges stored as `G.graph["hyperedges"]` list

### Community Detection (`cluster.py`)

<!-- level:advanced -->

**Algorithm priority:**
1. Leiden (graspologic) — preferred, better quality communities
2. Louvain (NetworkX) — fallback, with `max_level=10, threshold=1e-4` to prevent hangs

**Post-processing:**
- Isolate nodes (degree 0) → single-node communities
- Oversized communities (>25% of graph, min 10 nodes) → recursive splitting via subgraph extraction + re-run Leiden
- Communities sorted by size descending, re-indexed (community 0 = largest)

**Cohesion score:** `actual_intra_edges / max_possible_edges` for each community. Used in analysis to flag poorly-defined clusters.

### Analysis (`analyze.py`)

<!-- level:advanced -->

**God nodes algorithm:** Sort by degree, filter file-level hubs, method stubs, isolates, concept nodes. Return top N.

**Surprise score algorithm (for multi-file corpora):**

```python
score = 0
score += {AMBIGUOUS: 3, INFERRED: 2, EXTRACTED: 1}[confidence]
if crosses_file_types: score += 2
if different_top_directories: score += 2
if cross_community: score += 1
if semantically_similar_to: score *= 1.5
if peripheral_to_hub: score += 1
```

**Suggested questions (7 types):**
1. AMBIGUOUS edges — "What is the exact relationship between X and Y?"
2. Bridge nodes (betweenness centrality) — "Why does X connect communities A and B?"
3. God nodes with INFERRED edges — "Are these inferred relationships correct?"
4. Isolated nodes — "What connects X, Y, Z to the rest?"
5. Low-cohesion communities — "Should community C be split?"
6. Graph diff (if update mode) — "What changed?"
7. Fallback — generic questions if above don't apply

### Caching (`cache.py`)

<!-- level:intermediate -->

Cache key is SHA256 of file contents + resolved path. Identical files in different locations share one cache entry. Cache files are stored in `graphify-out/cache/{hash}.json` with atomic writes (write to `.tmp`, then rename).

`check_semantic_cache()` splits file lists into (cached, uncached) so the LLM only processes changed files. This is what makes `--update` fast — unchanged files hit the cache, only new/modified files go through extraction.

### Security (`security.py`)

<!-- level:intermediate -->

Defense-in-depth approach to all external input:

| Function | Threat Mitigated |
|----------|-----------------|
| `validate_url(url)` | SSRF — blocks `file://`, private IPs (127.x, 10.x, 169.254.x), cloud metadata endpoints |
| `safe_fetch(url, max_bytes)` | DoS — streaming download with 50MB cap |
| `validate_graph_path(path, base)` | Path traversal — must resolve inside `graphify-out/` |
| `sanitize_label(text)` | XSS + prompt injection — strips control chars, HTML-escapes, caps at 256 chars |

<!-- level:advanced -->

**Redirect safety:** `_NoFileRedirectHandler` intercepts HTTP redirects and blocks any that resolve to `file://` schemes (open redirect → SSRF).

**YAML injection:** `_yaml_str()` in `ingest.py` escapes quotes and newlines in frontmatter values to prevent YAML injection via fetched webpage titles.

**Cypher injection:** Node labels are sanitized before generating Neo4j Cypher statements, preventing injection via crafted node names.

### Export Formats (`export.py`)

<!-- level:intermediate -->

| Format | File | Purpose |
|--------|------|---------|
| JSON | `graph.json` | NetworkX node-link format; portable, queryable |
| HTML | `graph.html` | Interactive vis.js force-directed layout with sidebar search, community legend, node info panels |
| SVG | `graph.svg` | Static diagram for presentations |
| GraphML | `graph.graphml` | Import into Gephi or yEd |
| Cypher | `cypher.txt` | Neo4j `CREATE` statements |
| Obsidian | `vault/` | One markdown file per community + god node with backlinks |
| Wiki | `wiki/` | Wikipedia-style articles per community with `index.md` entry point |

### MCP Server (`serve.py`)

<!-- level:advanced -->

Graphify can run as a Model Context Protocol (MCP) stdio server, making the graph queryable by any MCP-compatible agent.

**Query functions:**
- `_score_nodes(G, terms)` — keyword search, scoring by term matches in label and source_file
- `_bfs(G, start, depth)` — breadth-first traversal from starting nodes
- `_dfs(G, start, depth)` — depth-first traversal for path tracing
- `_subgraph_to_text(G, nodes, edges, budget)` — render subgraph as plain text within a token budget (~3 chars/token)

### Watch Mode & Git Hooks

<!-- level:intermediate -->

**Watch mode** (`--watch`): Uses watchdog to monitor the directory. Code file changes trigger instant AST rebuild (no LLM). Doc/image changes write a flag file and notify the user to run `--update` (LLM needed).

**Git hooks** (`graphify hook install`): Installs `post-commit` and `post-checkout` hooks that rebuild the graph after every commit and branch switch. Hooks use start/end markers for idempotent installation.

---

## Use Cases

<!-- level:beginner -->

### 1. Onboarding to a New Codebase

Drop into a new project, run `/graphify .`, and immediately see:
- Which modules are the architectural pillars (god nodes)
- How the codebase clusters into logical areas (communities)
- Surprising connections you'd miss reading files linearly

### 2. Research Paper + Code Integration

If you're working with academic papers alongside code (common in ML), graphify connects concepts across both:
- Paper concepts link to code implementations via `semantically_similar_to` edges
- You can query "what connects attention to the optimizer?" and get a traversal through both paper and code nodes

### 3. Architecture Documentation

The GRAPH_REPORT.md is an auto-generated architecture document that stays current with your code. The always-on hook means your AI assistant reads this report before answering architecture questions.

### 4. Code Review Context

Before reviewing a PR, query the graph to understand the blast radius: which god nodes and communities are affected by the changed files.

<!-- level:intermediate -->

### 5. Incremental Knowledge Building

Use `--update` mode and `--watch` to keep the graph current as your codebase evolves. The SHA256 cache means only changed files are re-processed. Git hooks can automate this entirely.

### 6. Multi-Format Export for Teams

Export to Obsidian for team-wide knowledge base navigation, Neo4j for complex graph queries, or the wiki format for agent-crawlable documentation.

### 7. Token Cost Management

The benchmark tool (`graphify benchmark`) quantifies token savings. On a 52-file mixed corpus: 123K tokens (naive read) → 1.7K per query (graph traversal) = 71.5x reduction. The savings compound over time as queries accumulate.

---

## Tech Stack

<!-- level:beginner -->

| Technology | Role |
|------------|------|
| **Python 3.10+** | Core language |
| **NetworkX** | In-memory graph data structure and algorithms |
| **tree-sitter** | AST parsing for 19 languages (deterministic, no LLM) |
| **vis.js** | Interactive graph visualization in HTML |
| **Leiden (graspologic)** | Community detection algorithm |
| **Claude / GPT-4** | Semantic extraction for docs, papers, images |

<!-- level:intermediate -->

**Optional dependencies:**

| Extra | Package | Purpose |
|-------|---------|---------|
| `[mcp]` | mcp | MCP stdio server |
| `[neo4j]` | neo4j | Direct Neo4j push |
| `[pdf]` | pypdf, html2text | PDF text extraction |
| `[watch]` | watchdog | File system monitoring |
| `[leiden]` | graspologic | Leiden community detection |
| `[office]` | python-docx, openpyxl | .docx and .xlsx support |
| `[all]` | all of above | Everything |

---

## Platform Integration

<!-- level:beginner -->

Graphify works as a skill across multiple AI coding platforms:

| Platform | Skill Trigger | Always-On Mechanism |
|----------|--------------|---------------------|
| Claude Code | `/graphify` | `CLAUDE.md` + PreToolUse hook in `settings.json` |
| Codex | `$graphify` | `AGENTS.md` |
| OpenCode | `/graphify` | `AGENTS.md` |
| OpenClaw | `/graphify` | `AGENTS.md` |
| Factory Droid | `/graphify` | `AGENTS.md` |

<!-- level:intermediate -->

**Claude Code integration (deepest):** The PreToolUse hook fires before every Glob and Grep call. If a knowledge graph exists, Claude sees: "graphify: Knowledge graph exists. Read GRAPH_REPORT.md for god nodes and community structure before searching raw files." This means Claude navigates via the graph instead of grepping through every file.

**The difference between always-on and explicit commands:** The always-on hook surfaces `GRAPH_REPORT.md` — a one-page summary. The `/graphify query`, `/graphify path`, and `/graphify explain` commands go deeper: they traverse `graph.json` hop by hop, trace exact paths, and surface edge-level detail (relation type, confidence score, source location).

Think of it this way: the always-on hook gives your assistant a map. The `/graphify` commands let it navigate the map precisely.

---

## Extending Graphify

<!-- level:advanced -->

### Adding a New Language

1. Define a `LanguageConfig` instance with the language's AST node types
2. Add a `_import_<lang>()` function for language-specific import handling
3. Register the file suffix in `extract()` dispatch and `collect_files()`
4. Add the suffix to `CODE_EXTENSIONS` in `detect.py` and `_WATCHED_EXTENSIONS` in `watch.py`
5. Add the tree-sitter package to `pyproject.toml` dependencies
6. Add a fixture file to `tests/fixtures/` and tests to `tests/test_languages.py`

### Adding a New Export Format

1. Implement the export function in `export.py`
2. Call it from the skill with appropriate flags
3. Add tests in `tests/test_export.py`

### Programmatic Usage

The library can be used standalone (without the skill):

```python
from graphify.detect import detect
from graphify.extract import extract
from graphify.build import build_from_json
from graphify.cluster import cluster
from graphify.analyze import god_nodes, surprising_connections

files = detect("./my-project")
extractions = extract(files["files"]["code"])
G = build_from_json(extractions)
communities = cluster(G)
gods = god_nodes(G)
```

---

## Testing

<!-- level:intermediate -->

All tests are pure unit tests — no network calls, no file system side effects outside `tmp_path`. Test files map 1:1 to modules:

| Test File | Covers |
|-----------|--------|
| `test_detect.py` | File classification, `.graphifyignore`, symlink safety |
| `test_extract.py` | AST extraction for all 19 languages |
| `test_build.py` | Graph assembly, deduplication, hyperedges |
| `test_cluster.py` | Community detection, cohesion scoring, splitting |
| `test_analyze.py` | God nodes, surprising connections, graph diff |
| `test_validate.py` | Schema validation, error messages |
| `test_cache.py` | Hash caching, incremental detection |
| `test_security.py` | URL validation, path traversal, label sanitization |
| `test_report.py` | Report generation, markdown formatting |
| `test_export.py` | JSON, HTML, Obsidian export |
| `test_hooks.py` | Git hook install/uninstall |
| `test_watch.py` | Auto-rebuild logic |
| `test_benchmark.py` | Token reduction calculation |
| `test_ingest.py` | URL fetching, annotation |
| `test_languages.py` | Multi-language extraction |
| `test_hypergraph.py` | Hyperedge support |

CI runs on Python 3.10 and 3.12 via GitHub Actions.

---

## Known Limitations & Considerations

<!-- level:intermediate -->

1. **Graph drift on incremental updates:** When merging new files with `--update`, stale relationships from earlier indexing runs can persist. Recommendation: full re-index after major structural changes.

2. **Token reduction scales with size:** Small projects (~6 files) see ~1x reduction — they fit in a context window anyway. The 71.5x figure is on a 52-file mixed corpus. Value is proportional to project scale.

3. **Semantic extraction is probabilistic:** Claude/GPT-4 extraction varies by model version and temperature. Confidence scores mitigate this but don't eliminate it.

4. **PyPI name:** Package is `graphifyy` (the `graphify` name is being reclaimed). The CLI and skill command are still `graphify`.

5. **Louvain fallback performance:** On large sparse graphs, Louvain can hang without the tuned parameters added in v0.3.10 (`max_level=10, threshold=1e-4`).
