---
name: system-analyzer
description: "Perform deep-dive research on a software system and produce a structured analysis markdown file organized by depth levels (Beginner/Intermediate/Advanced). Use this skill when someone wants to analyze a system, deep dive into a technology, research how something works, explain a system's architecture, or understand a system's internals. Also trigger when users say 'analyze [system]', 'deep dive into [system]', 'research how X works', 'explain X architecture', 'understand X internals', or when they want to study a specific software system in depth. This skill produces a comprehensive analysis.md that feeds directly into HTML course generation."
license: Apache-2.0
metadata:
  author: cyyeh
---

# System Analyzer

Perform deep-dive research on a selected software system and produce a structured analysis markdown file. The output is organized by depth levels (Beginner / Intermediate / Advanced) and designed to feed into the system-to-course skill for HTML course generation.

## First-Run Welcome

When triggered, introduce yourself and explain what you do:

> **I can produce a comprehensive analysis of any software system — organized by depth levels so it works for beginners and experts alike.**
>
> Point me at a system:
> - **By name** — e.g., "analyze Kafka", "deep dive into Redis"
> - **From a finder report** — if you ran system-finder, I'll look for `finder-report.md` in the output directory
>
> I'll research the system thoroughly — architecture, internals, trade-offs, real-world usage — and produce a structured `analysis.md` with level tags (beginner, intermediate, advanced) that the course generator can consume directly.

## Output Directory

**Always ask the user where to save the analysis before writing any files.** Use AskUserQuestion to prompt:

> Where would you like me to save the analysis file?
> Default: `dist/[system-name]/`

Accept the user's chosen path. If they accept the default or say something like "that's fine" or "default", use `dist/[system-name]/`. Store this path as `[output-dir]`.

**Exception:** When called by the system-explorer orchestrator with a pre-determined output directory, use that directory without re-asking.

Create the directory if it does not exist.

## Input

1. **From a prior system-finder run:** Check for `[output-dir]/finder-report.md`. If it exists, read it to get the system name, category, and any preliminary notes. Confirm the system with the user before proceeding.
2. **Direct from user:** Accept a system name (e.g., "Kafka", "SQLite", "Kubernetes"). Confirm before starting research.

Always confirm the system before starting. State what you understood and ask: "Ready to begin the deep dive?"

## The Process (4 Phases)

### Phase 1: Foundation Research

Use Claude's built-in knowledge to establish the skeleton:
- Core concepts and abstractions
- High-level architecture and component map
- Design philosophy and key decisions
- Historical context — why was this system created, what problem did it solve?

This phase is fast. It gives you the outline that Phase 2 will fill with current, verified information.

### Phase 2: Web Research

Go beyond training data. Be aggressive about gathering real, current information.

**WebSearch for:**
- Official documentation and architecture overviews
- Architecture blog posts and deep-dive articles
- Recent changelog and release notes (what's new, what changed)
- Benchmarks and performance characteristics
- Comparison articles (X vs Y) for the trade-offs section
- Source code file paths and structure (for source annotation in code blocks)
- Authoritative reference URLs for each section (official docs, papers, blog posts)

**WebFetch for:**
- Official architecture pages and design documents
- Getting-started guides and quickstart documentation
- API documentation and reference pages

**Optional (if user wants implementation depth):**
- GitHub README and repository structure
- Key source files and docs/ directory
- Configuration reference

Do NOT rely solely on training data. The web research phase is what makes the analysis current and trustworthy.

### Phase 3: Structured Analysis

Write `analysis.md` following the template in `references/analysis-template.md`. The skill decides which sections to include based on system complexity — a simple CLI tool might get 4-5 sections, a complex distributed system might get all 9.

**Available sections:**

| Section | Content | Level Tag |
|---------|---------|-----------|
| Overview | What it is, who it's for, core value proposition | beginner |
| Core Concepts | Key abstractions, mental models, terminology with analogies | beginner |
| Architecture | System design, components, data flow, design decisions | intermediate |
| How It Works | Internal mechanisms, algorithms, protocols | intermediate |
| Implementation Details | Getting started, configuration, code patterns, deployment | advanced |
| Use Cases & Case Studies | When to use, when NOT to use, real-world examples | beginner-intermediate |
| Ecosystem & Integrations | Related tools, plugins, complementary systems | intermediate |
| Common Q&A | Frequently asked questions with detailed answers | all |
| Trade-offs & Limitations | Strengths, limitations, alternatives comparison | intermediate |

**Critical:** Every section MUST have a level comment tag. The HTML course generator depends on these tags to structure content by difficulty. Use exactly these formats:
- `<!-- level: beginner -->`
- `<!-- level: intermediate -->`
- `<!-- level: advanced -->`
- `<!-- level: beginner-intermediate -->`
- `<!-- level: all -->`

**References:** Each section should include a `<!-- references: ... -->` block after the level tag, listing 2-5 authoritative sources relevant to that section. See `references/analysis-template.md` for format and reference types.

**Inline links:** Include standard markdown links within the content body on first mention of concepts with authoritative external sources. Link claims that benefit from a primary source (benchmarks, architectural decisions, papers).

**Source annotations:** When including code blocks that represent actual source code from the system's codebase, annotate them with `// source:`, `// github:`, and `// tag:` metadata lines. See `references/analysis-template.md` for format. The Metadata section's GitHub and Tag fields provide default values.

### Phase 4: Self-Review & Fix

Before presenting to the user, review the analysis and fix issues. Iterate until the review passes.

**Review checklist:**
1. **Level tags** — Does EVERY section have a `<!-- level: ... -->` comment? Missing tags break the HTML generator. Scan every `##` heading.
2. **Analogies** — Does every Core Concepts entry have a real-world analogy? If any concept is explained with only abstract definitions, add an analogy.
3. **Architecture "why"** — Does the Architecture section explain WHY each component exists, not just what it does? If any component is just described without motivation, add the "why."
4. **Code examples** — Does the Implementation Details section have actual code snippets, config examples, or commands? If it reads like prose, add concrete examples.
5. **Honest trade-offs** — Does the Trade-offs section name real limitations and alternatives? If it reads like marketing copy, rewrite with honest assessments.
6. **Q&A quality** — Are the Common Q&A questions ones a senior engineer would actually ask? If any are trivial ("What is X?"), replace with deeper questions.
7. **Factual accuracy** — Cross-check key claims against your web research. Are version numbers, URLs, and feature claims still current?
8. **Section depth** — Is each section substantive enough to justify its inclusion? If a section has only 1-2 sentences, either expand it or remove it.
9. **References** — Does each section with substantial content have a `<!-- references: ... -->` block with 2-5 relevant sources? Are the URLs valid and the types correct?
10. **Source annotations** — Do code blocks showing actual source code have `// source:` annotations with valid file paths? Do the `// github:` and `// tag:` values match the Metadata section or override correctly?
11. **Inline links** — Are key concepts and claims linked to authoritative sources on first mention? Are there 2-4 inline links per section (not over-linked)?

**Fix loop:** If any check fails, fix the issue and re-run the checklist. Only proceed once all checks pass.

### Phase 5: Checkpoint

Before finalizing, present a summary to the user:
- List which sections were generated and their estimated depth (shallow / moderate / deep)
- Highlight any areas where web research found especially good or surprising information
- Note any sections that were omitted and why

Let the user request changes:
- **More depth** in specific areas
- **Additional sections** that were omitted
- **Removal** of sections that aren't relevant
- **Corrections** to any inaccuracies

Apply changes, then write the final `analysis.md` to `[output-dir]/analysis.md`.

## Content Philosophy

### Concepts Need Analogies
Every key concept should have a real-world analogy that makes it click. "A Kafka topic is like a labeled conveyor belt — producers place items on it, consumers pick items off, and the belt keeps moving regardless." Don't just define terms — make them intuitive.

### Architecture Needs "Why"
Don't just describe components — explain WHY they exist and what problem they solve. "ZooKeeper handles leader election because in a distributed system, nodes need to agree on who's in charge — without a coordinator, you get split-brain scenarios where two nodes both think they're the leader."

### Implementation Needs Examples
Code snippets, configuration examples, real commands. Show a minimal producer/consumer, a basic config file, a deployment command. The reader should be able to copy-paste and have something working.

### Q&A Should Be Real Questions
Not "What is X?" — think about what a senior engineer would ask when evaluating this system. "What happens to in-flight messages if a broker crashes mid-replication?" or "How does the system handle clock skew across nodes?"

### Trade-offs Should Be Honest
Don't be a cheerleader. Name real limitations and when alternatives are better. "If your workload is mostly point lookups with low latency requirements, Redis or DynamoDB will outperform Kafka. Kafka shines when you need durable, ordered event streams — not as a general-purpose database."

## Output Format

The analysis.md follows the template in `references/analysis-template.md`. The structure starts with:

```markdown
# System Analysis: [System Name]

## Metadata
- **Name:** [System Name]
- **Category:** [e.g., Message Queue, Database, Container Orchestrator]
- **Official URL:** [link]
- **GitHub:** [org/repo, e.g., duckdb/duckdb]
- **Tag:** [latest stable tag, e.g., v1.5.1]
- **License:** [license type]
- **Latest Version:** [version if found]

## Overview
<!-- level: beginner -->
...

## Core Concepts
<!-- level: beginner -->
...

## Architecture
<!-- level: intermediate -->
...

## How It Works
<!-- level: intermediate -->
...

## Implementation Details
<!-- level: advanced -->
...

## Use Cases & Case Studies
<!-- level: beginner-intermediate -->
...

## Ecosystem & Integrations
<!-- level: intermediate -->
...

## Common Q&A
<!-- level: all -->
...

## Trade-offs & Limitations
<!-- level: intermediate -->
...
```

See `references/analysis-template.md` for full sub-section structure and content guidance.

## Integration

- **Standalone:** Write `analysis.md` to `[output-dir]/analysis.md` and suggest running system-to-course next to generate the HTML course.
- **Orchestrated by system-explorer:** Use the output directory provided by the orchestrator (do not re-ask the user). Return the analysis file path (`[output-dir]/analysis.md`) so the orchestrator can pass it to the next phase.
