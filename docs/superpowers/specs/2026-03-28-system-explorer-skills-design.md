# System Explorer Skills — Design Spec

**Date:** 2026-03-28
**Status:** Draft

## Overview

A suite of 4 skills (3 composable + 1 orchestrator) for discovering, analyzing, and teaching software systems through interactive multi-page static HTML sites. Users can invoke the full pipeline via `system-explorer`, or use individual skills independently.

**Target users:** Engineers evaluating tech, developers learning systems, tech leads/architects making decisions.

**Core idea:** Progressive understanding — users choose their depth level (Beginner / Intermediate / Advanced) and the content adapts.

---

## Skill Architecture

```
skills/system-explorer/
├── system-finder/
│   ├── SKILL.md
│   └── references/
│       └── search-strategies.md
├── system-analyzer/
│   ├── SKILL.md
│   └── references/
│       └── analysis-template.md
├── system-to-course/
│   ├── SKILL.md
│   ├── references/
│   │   ├── design-system.md
│   │   ├── interactive-elements.md
│   │   └── page-templates.md
│   └── evals/
│       └── evals.json
├── system-explorer/
│   ├── SKILL.md
│   └── evals/
│       └── evals.json
└── examples/
    └── (generated example outputs)
```

**Data flow between skills:**
- `system-finder` → writes `dist/[system-name]/finder-report.md`
- `system-analyzer` → reads finder report (or takes direct input), writes `dist/[system-name]/analysis.md`
- `system-to-course` → reads `analysis.md`, generates multi-page HTML in `dist/[system-name]/`
- `system-explorer` → orchestrates all three with user checkpoints

---

## Skill 1: `system-finder`

**Purpose:** Discover software systems matching a user's target and present a structured comparison.

**Trigger phrases:** "find systems for...", "what message queues exist", "compare databases for...", "I need a tool for...", "show me options for..."

### Process

1. **Understand the target** — Ask clarifying questions if the query is ambiguous (e.g., "real-time data" could mean streaming, CDC, or event processing). For specific systems ("tell me about Kafka"), skip discovery and confirm directly.

2. **Research** — Use Claude's built-in knowledge as foundation, then WebSearch to validate and find latest info (new releases, adoption changes, emerging alternatives).

3. **Build comparison table** — Present 3-7 matching systems with structured columns:
   - Name + one-line description
   - Category/type
   - Primary language/ecosystem
   - Key strengths (2-3 bullet points)
   - Key trade-offs (2-3 bullet points)
   - Maturity (emerging / established / mature)
   - GitHub stars / adoption signals (if available via web search)

4. **User selection** — Let user pick one or more systems to deep-dive on.

5. **Write output** — Save `finder-report.md` to `dist/[system-name]/` with the comparison table and user selection.

### Output format (`finder-report.md`)

```markdown
# System Finder Report: [User Query]

## Query
[Original user query and clarifications]

## Comparison

| System | Category | Language | Strengths | Trade-offs | Maturity |
|--------|----------|----------|-----------|------------|----------|
| ...    | ...      | ...      | ...       | ...        | ...      |

## Selected: [System Name]
[Brief rationale for selection]
```

---

## Skill 2: `system-analyzer`

**Purpose:** Deep-dive research on a selected software system. Produces structured analysis markdown.

**Trigger phrases:** "analyze Kafka", "deep dive into Redis", "research how PostgreSQL works"

### Process

1. **Input** — Reads `finder-report.md` from a prior finder run, or takes a system name directly from the user.

2. **Research pipeline** — Layered information gathering:
   - **Claude's knowledge** — core concepts, architecture, design philosophy
   - **WebSearch** — official docs, recent blog posts, changelog/releases, benchmarks
   - **WebFetch** — official architecture pages, getting-started guides, API docs
   - **GitHub** (optional) — README, docs/, key source files if user wants implementation depth

3. **Structured analysis output** — Write `analysis.md` with these sections (skill decides which to include based on system complexity):

| Section | Content | Level |
|---------|---------|-------|
| Overview | What it is, who it's for, core value proposition | Beginner |
| Core Concepts | Key abstractions, mental models, terminology | Beginner |
| Architecture | System design, components, data flow, diagrams (textual) | Intermediate |
| How It Works | Internal mechanisms, algorithms, protocols | Intermediate |
| Implementation Details | Code-level patterns, configuration, deployment | Advanced |
| Use Cases & Case Studies | Real-world applications, when to use/not use | Beginner-Intermediate |
| Ecosystem & Integrations | Related tools, plugins, complementary systems | Intermediate |
| Common Q&A | Frequently asked questions with answers | All levels |
| Trade-offs & Limitations | What it's bad at, common pitfalls, alternatives | Intermediate |

4. **Checkpoint** — Present summary of findings. Let user add/remove sections or request more depth.

### Output format (`analysis.md`)

```markdown
# System Analysis: [System Name]

## Metadata
- **Name:** [System Name]
- **Category:** [e.g., Message Queue, Database, etc.]
- **Official URL:** [link]
- **GitHub:** [link if applicable]
- **License:** [license type]
- **Latest Version:** [version if found]

## Overview
<!-- level: beginner -->
[What it is, who it's for, core value proposition]

## Core Concepts
<!-- level: beginner -->
### [Concept 1]
[Explanation with analogy]
### [Concept 2]
...

## Architecture
<!-- level: intermediate -->
### Components
[Component descriptions]
### Data Flow
[How data moves through the system]
### Design Decisions
[Why the system is designed this way]

## How It Works
<!-- level: intermediate -->
[Internal mechanisms, algorithms, protocols]

## Implementation Details
<!-- level: advanced -->
### Getting Started
[Minimal setup]
### Configuration
[Key configuration patterns]
### Code Patterns
[Common usage patterns with examples]
### Deployment
[Production deployment considerations]

## Use Cases & Case Studies
<!-- level: beginner-intermediate -->
### When to Use
[Ideal scenarios]
### When NOT to Use
[Anti-patterns]
### Real-World Examples
[Companies/projects using it and how]

## Ecosystem & Integrations
<!-- level: intermediate -->
[Related tools, plugins, complementary systems]

## Common Q&A
<!-- level: all -->
### Q: [Question]
A: [Answer]
...

## Trade-offs & Limitations
<!-- level: intermediate -->
### Strengths
[What it excels at]
### Limitations
[What it's bad at]
### Alternatives
[When to consider alternatives and which ones]
```

---

## Skill 3: `system-to-course`

**Purpose:** Transform `analysis.md` into a multi-page static HTML site with level-based content filtering.

**Trigger phrases:** "generate course for...", "build HTML for this analysis", "turn this into a course"

### HTML Output Structure

```
dist/[system-name]/
├── index.html          # Landing page + navigation hub
├── concepts.html       # Core concepts (Beginner)
├── architecture.html   # System architecture (Intermediate)
├── implementation.html # Implementation details (Advanced)
├── use-cases.html      # Case studies & use cases
├── ecosystem.html      # Ecosystem & integrations
├── faq.html            # Common Q&A
├── tradeoffs.html      # Trade-offs & limitations
└── analysis.md         # Source analysis (kept for reference)
```

Pages are generated dynamically — only pages with substantial content from the analysis are created.

### Level Selector

Persistent header bar with three toggles: **Beginner / Intermediate / Advanced**.

- Each content section is tagged with `data-level="beginner|intermediate|advanced"`
- Toggling a level shows/hides relevant sections across the current page
- Default: all levels visible
- State persisted in localStorage so it carries across pages

### Shared Navigation

Consistent across all pages:
- System name + description
- Page list with current page highlighted
- Level selector in header
- Progress indicator (visited pages tracked in localStorage)

### Design System

Adapted from `paper-to-course` with key modifications:
- **Same warm palette** — off-white backgrounds, warm grays, bold accent color
- **Same typography** — Bricolage Grotesque (headings), DM Sans (body), JetBrains Mono (code)
- **Multi-page navigation** instead of scroll-snap single-page modules
- **Software-specific elements** added (see below)
- **Reused elements** — glossary tooltips, callout boxes, concept cards, flow diagrams, quizzes, comparison cards

### Software-Specific Interactive Elements (New)

1. **Architecture Diagram** — CSS/SVG component diagram showing system components and data flow between them. Clickable components that expand with details.

2. **Code Snippet Blocks** — Syntax-highlighted configuration and code examples with copy button. Language-aware highlighting using CSS classes (no external libs).

3. **Decision Tree** — Interactive "should I use this?" flow chart. User answers yes/no questions that lead to a recommendation.

4. **System Comparison Cards** — Side-by-side comparison with alternative systems. Highlight where this system wins vs. where alternatives are better.

5. **Performance Characteristics** — Visual bars/gauges showing throughput, latency, scalability, consistency traits relative to alternatives.

### Implementation Rules

- Each HTML page includes all CSS/JS inline (self-contained per page)
- Only external dependency: Google Fonts CDN
- Pages link to each other via relative URLs
- Responsive: works on desktop and mobile
- Scroll-triggered animations using IntersectionObserver
- Accessible: ARIA attributes, keyboard navigation, proper heading hierarchy

### Build Process

1. Read `analysis.md` and parse sections by heading
2. Determine which pages to generate based on content presence
3. Generate `index.html` first (landing page with links to all pages)
4. Generate each content page with shared nav, level selector, and interactive elements
5. Write all files to `dist/[system-name]/`

---

## Skill 4: `system-explorer` (Orchestrator)

**Purpose:** Single entry point chaining finder → analyzer → course with checkpoints.

**Trigger phrases:** "explore Kafka", "teach me about Redis", "I need to understand message queues", "system explorer"

### Flow

```
User query
    │
    ▼
┌─────────────────────┐
│  1. Clarify target   │  Ask questions if ambiguous
│     (if needed)      │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  2. system-finder    │  Discover matching systems
│     → comparison     │  Present comparison table
│       table          │  User picks system(s)
└──────────┬──────────┘
           ▼  Checkpoint: "Found these. Which to analyze?"
┌─────────────────────┐
│  3. system-analyzer  │  Deep-dive research
│     → analysis.md    │  Present summary of findings
└──────────┬──────────┘
           ▼  Checkpoint: "Here's the analysis. Generate course?"
┌─────────────────────┐
│  4. system-to-course │  Generate multi-page HTML
│     → dist/[name]/   │  Open in browser for review
└──────────┬──────────┘
           ▼
     Done — user reviews HTML
```

### Smart Shortcuts

- **Specific system named** ("explore Kafka") → skip finder, go to analyzer
- **Existing analysis.md provided** → skip to course generation
- **Multiple systems requested** → run analyzer in parallel for each, generate combined comparison site

---

## Integration with Existing Project

- Skills live in `skills/system-explorer/` alongside existing `skills/paper-to-course/`
- HTML output goes to `dist/[system-name]/` alongside existing `dist/` content
- The existing `build.py` will auto-discover these skills via its `skills/**/*/SKILL.md` glob pattern
- GitHub Actions will deploy generated examples to GitHub Pages

---

## Verification Plan

1. **Skill discovery** — Run `build.py` and verify all 4 skills appear in the static website
2. **Individual skill test** — Invoke each skill independently:
   - `/system-finder` with "message queue systems" → verify comparison table output
   - `/system-analyzer` with "Apache Kafka" → verify analysis.md structure and level tags
   - `/system-to-course` with a sample analysis.md → verify multi-page HTML generation
3. **Orchestrator test** — Invoke `/system-explorer` with "I want to understand event-driven architectures" → verify full pipeline
4. **Level selector** — Verify toggling levels shows/hides content correctly in generated HTML
5. **Cross-page navigation** — Verify all page links work and navigation state persists
6. **Mobile responsiveness** — Verify pages work on mobile viewport
7. **Evals** — Run eval cases defined in `evals.json`
