# Analysis Template Reference

Definitive template for `analysis.md` output. Sections are optional based on complexity, but order, level tags, and sub-section structure must be preserved.

```markdown
# System Analysis: [System Name]

## Metadata
- **Name:** [System Name]
- **Category:** [e.g., Message Queue, Database, Container Orchestrator]
- **Official URL:** [link]
- **GitHub:** [org/repo, e.g., duckdb/duckdb]
- **Tag:** [latest stable tag, e.g., v1.5.1 — used for source code links]
- **License:** [license type]
- **Latest Version:** [version if found]
- **Analysis Date:** [YYYY-MM-DD]

---

## Overview
<!-- level: beginner -->
<!-- 2-3 paragraphs. Lead with core value proposition, then expand. -->

### What It Is
<!-- One clear sentence + real-world analogy. E.g.: "Kafka is a distributed event
     streaming platform — like a city-wide postal system where every letter is stored
     permanently, delivered in order, and read by multiple recipients independently." -->

### Who It's For
<!-- Target audience: what kind of engineer/team/company benefits most? -->

### The One-Sentence Pitch
<!-- Explain this system to a CTO in an elevator. -->

---

## Core Concepts
<!-- level: beginner -->
<!-- The "vocabulary lesson." Every concept needs: definition, analogy, why it matters. -->

### [Concept 1 Name]
<!-- Pattern: Definition -> Analogy -> Why it matters. E.g.: "A **Topic** is a named
     stream of records — like a labeled conveyor belt. Topics decouple producers
     from consumers." Aim for 4-8 core concepts. -->

### [Concept 2 Name]

### [Concept N Name]

### How They Fit Together
<!-- Brief narrative showing how the concepts relate to each other. -->

---

## Architecture
<!-- level: intermediate -->
<!-- System design and components. Always explain WHY each component exists. -->

### High-Level Design
<!-- 10,000-foot view. Major components and their interactions. -->

### Key Components
<!-- Each component: what it does, why it exists, what problem it solves. E.g.:
     "**Controller Node** — Manages partition assignments. Exists because distributed
     systems need a single source of truth for cluster state." -->

### Data Flow
<!-- Trace a request/message through the system end-to-end, step by step. -->

### Design Decisions
<!-- Interesting architectural choices and their rationale. -->

---

## How It Works
<!-- level: intermediate -->
<!-- Internal mechanisms: algorithms, protocols, clever tricks. Deeper than Architecture. -->

### [Mechanism 1: e.g., Storage Engine]
<!-- How data is stored, indexed, retrieved. File formats, data structures. -->

### [Mechanism 2: e.g., Replication Protocol]
<!-- Durability/consistency/availability mechanisms. Failure handling. -->

### [Mechanism 3: e.g., Consensus / Coordination]
<!-- Distributed agreement: leader election, quorum decisions. -->

### Performance Characteristics
<!-- Where it's fast, where it's slow, and why. Include numbers when available. -->

---

## Implementation Details
<!-- level: advanced -->
<!-- Hands-on: code snippets, config files, deployment patterns. -->

### Getting Started
<!-- Fastest path from zero to "hello world." Docker/brew/equivalent. -->

### Configuration Essentials
<!-- 5-10 most important config knobs. What each controls, default, when to change. -->

### Code Patterns
<!-- Common usage patterns with short code snippets (10-20 lines). -->

### Deployment Considerations
<!-- Production checklist: sizing, monitoring, backup, upgrade path. -->

---

## Use Cases & Case Studies
<!-- level: beginner-intermediate -->
<!-- When to use AND when NOT to use. Real examples + anti-patterns. -->

### When to Use It
<!-- 3-5 specific scenarios. E.g.: "100K+ events/sec with ordering guarantees." -->

### When NOT to Use It
<!-- Anti-patterns. E.g.: "Don't use Kafka for point lookups or request-response RPC." -->

### Real-World Examples
<!-- 2-3 known production deployments with brief descriptions. -->

---

## Ecosystem & Integrations
<!-- level: intermediate -->

### Official Tools & Extensions
<!-- Tools built by the same team or organization. -->

### Community Ecosystem
<!-- Popular third-party tools, libraries, frameworks. -->

### Common Integration Patterns
<!-- How this connects with other systems. E.g.: "Kafka + Flink for stream processing,
     Kafka + Elasticsearch for search indexing." -->

---

## Common Q&A
<!-- level: all -->
<!-- Real questions a senior engineer would ask when evaluating or operating the system.
     Not basics — hard, practical questions. Aim for 5-8 questions. -->

### Q: [Hard practical question]
<!-- E.g.: "What happens to in-flight messages if a broker crashes mid-replication?" -->

### Q: [Operational question]
<!-- E.g.: "How do I handle schema evolution without breaking consumers?" -->

### Q: [Comparison question]
<!-- E.g.: "When should I choose X over Y?" -->

### Q: [Scaling question]
<!-- E.g.: "What are the practical limits of this architecture?" -->

### Q: [Debugging question]
<!-- E.g.: "Consumer lag is increasing — what's the diagnostic playbook?" -->

---

## Trade-offs & Limitations
<!-- level: intermediate -->
<!-- Honest assessment. Every system has weaknesses — name them. -->

### Strengths
<!-- 3-5 genuine technical strengths that matter in production. -->

### Limitations
<!-- 3-5 real limitations. Be specific. E.g.: "No built-in exactly-once delivery
     across system boundaries — only within the Kafka ecosystem." -->

### Alternatives Comparison
<!-- 2-3 alternatives. For each: what it does better, worse, when to choose it. -->

### The Honest Take
<!-- 2-3 sentences. When would you recommend this system? When would you not? -->
```

---

## Per-Section References

Each content section can include an optional references block as an HTML comment, placed immediately after the level tag. References link to authoritative external sources that support or expand on the section's content.

**Format:**
```markdown
## Architecture
<!-- level: intermediate -->
<!-- references:
- [Architecture Deep Dive](https://duckdb.org/docs/internals/overview) | official-docs
- [Push-Based Execution Paper](https://arxiv.org/abs/2106.00505) | paper
- [Storage Format Blog Post](https://duckdb.org/2024/07/storage) | blog
-->
```

**Reference types** (used for icon selection in HTML output):
- `official-docs` — Official documentation pages
- `paper` — Academic or research papers
- `blog` — Blog posts and articles
- `github` — GitHub repositories or specific source files
- `video` — Video content (conference talks, tutorials)
- `tutorial` — Step-by-step tutorial guides
- `community` — Community resources (forums, discussions, wikis)

**Rules:**
- Place the `<!-- references: ... -->` block immediately after the `<!-- level: ... -->` tag
- Each reference is a markdown link followed by `|` and a type label
- Include 2-5 references per section — quality over quantity
- Prefer official/primary sources over third-party summaries
- References are optional — omit the block if no authoritative sources exist for a section

## Inline Contextual Links

Within the content body, include standard markdown links to external sources where they add value:

- Link on **first mention** of a concept that has an authoritative external source
- Link **claims** that benefit from a primary source (benchmarks, design decisions)
- Prefer official documentation over third-party summaries
- Do not over-link — 2-4 inline links per section is typical

Example:
```markdown
DuckDB uses a [push-based execution model](https://duckdb.org/docs/internals/overview)
inspired by the approach described in Leis et al.'s
[Morsel-Driven Parallelism paper](https://db.in.tum.de/~leis/papers/morsels.pdf).
```

## Source Code Annotations

Code blocks that represent actual source code from the system's codebase (not tutorial/example code) should include source annotations as comment lines at the top of the block. These annotations are consumed by the HTML course generator to create file path headers and GitHub links.

**Format:**
```cpp
// source: src/parser/parser.cpp:142-168
// github: duckdb/duckdb
// tag: v1.5.1
unique_ptr<SQLStatement> Parser::ParseStatement() {
    auto token = Peek();
    switch (token.type) {
        case TokenType::SELECT:
            return ParseSelectStatement();
    }
}
```

**Annotation fields:**
- `// source: <file-path>:<start-line>-<end-line>` — Required for source-annotated blocks. File path relative to repo root. Line range is optional. A code block without `// source:` is treated as a regular code block (tutorial/example code).
- `// github: <org/repo>` — Optional. Overrides the Metadata-level GitHub field for this block.
- `// tag: <ref>` — Optional. Overrides the Metadata-level Tag field for this block.

**When to annotate:**
- Code extracted or adapted from the system's actual source code
- Configuration files from the system's repository
- NOT for tutorial/getting-started code that users would write themselves
- NOT for shell commands (pip install, docker run, etc.)

**Language-specific comment syntax:**
- C/C++/Java/Go/Rust/JS/TS: `// source: ...`
- Python/Ruby/Shell/YAML: `# source: ...`
- SQL/Lua/Haskell: `-- source: ...`
- HTML/XML: `<!-- source: ... -->`

---

## Section Selection Guide

| System Complexity | Sections | Examples |
|---|---|---|
| Simple tool / library | Overview, Core Concepts, Implementation, Use Cases, Q&A | jq, curl, lodash |
| Mid-complexity | All except Ecosystem or How It Works | Redis, Nginx, SQLite |
| Complex distributed system | All 9 sections | Kafka, Kubernetes, Cassandra |

## Level Tag Rules

Every section MUST have exactly one level tag as an HTML comment immediately after the heading:

- `<!-- level: beginner -->` — No prior knowledge required
- `<!-- level: intermediate -->` — Assumes familiarity with core concepts
- `<!-- level: advanced -->` — Assumes hands-on experience
- `<!-- level: beginner-intermediate -->` — Starts accessible, gets technical
- `<!-- level: all -->` — Useful at every level

Tags are consumed by the HTML course generator. Missing or malformed tags break the pipeline.
