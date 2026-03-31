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

**Source Code Research (when GitHub repo is available):**

This is NOT optional — when the system has a public GitHub repository, always perform source code research to feed the Implementation Details section's Source Code Walkthrough. For systems spanning multiple repositories (listed in the `Additional Repos` metadata field), repeat these steps for each repo.

**Step 1 — Build a concept checklist.** Take every core concept from Phase 1 (typically 4-8 concepts) and every key architectural component. Write them down as a checklist. Every concept MUST be mapped to source code by the end of this phase.

**Step 2 — Explore the repo structure.** Fetch the repository file tree using WebFetch on `https://api.github.com/repos/{org}/{repo}/git/trees/{tag}?recursive=1`. For large repos where the tree is truncated, browse key directories individually via the GitHub API: `https://api.github.com/repos/{org}/{repo}/contents/{path}?ref={tag}`.

**Step 3 — Map each concept to source files using a concept-driven search.** For EACH concept on the checklist:
1. Search the file tree for directories and files whose names match the concept (e.g., `hnsw_index/` for "HNSW Index", `artifact/` or `artifact_repo.py` for "Artifacts", `vector_storage/` for "Vectors")
2. Fetch the most likely candidate files using raw GitHub URLs: `https://raw.githubusercontent.com/{org}/{repo}/{tag}/{filepath}`
3. Identify the key type definition — the struct, class, trait, interface, or enum that IS the concept (e.g., `struct GraphLayers` for HNSW, `class Experiment` for Experiments, `enum Distance` for Distance Metrics)
4. Identify key functions/methods that operate on that type (e.g., `create_experiment()`, `search_on_level()`, `apply()`)
5. Extract a representative code excerpt (20-60 lines) that reveals the concept's implementation. Prefer code that shows design decisions over boilerplate.

**Step 4 — Track coverage.** After searching, review the checklist. Every core concept should have at least one source mapping. If a concept has no mapping, try alternative search strategies:
- Search for the concept name as a type/function name in different casings (CamelCase, snake_case, UPPER_CASE)
- Browse the top-level `src/` or `lib/` directories for module names related to the concept
- Check the project's README or ARCHITECTURE.md for pointers to key source files
- For multi-repo systems, the concept may live in a different repo than the main one

**Step 5 — Extract and annotate.** For each mapped concept, extract the code excerpt with precise line ranges. For complex implementations, extract multiple consecutive excerpts from the same file to support multi-block sequences. Flag concepts that will need multi-block sequences or the focus + context pattern.

Record the final mapping as a working table for Phase 3:
```
| Concept | File | Lines | Key Types/Functions | Repo (if multi-repo) |
```

If the GitHub API rate-limits you, fall back to raw.githubusercontent.com URLs directly. If the system is closed-source, skip this step and note the limitation in the Implementation Details section.

Do NOT rely solely on training data. The web research and source code research phases are what make the analysis current and trustworthy.

### Phase 3: Structured Analysis

Write the analysis as **multiple files** — one per section — instead of a single monolithic `analysis.md`. This allows each section to use the full context budget for depth and detail.

**Step 1: Write the manifest.** Create `analysis.json` in `[output-dir]` following the format in `references/section-templates/manifest-template.json`. List only the sections you plan to include.

**Step 2: Write each section file.** For each section in the manifest, write a separate numbered markdown file to `[output-dir]` using the corresponding template from `references/section-templates/`. The skill decides which sections to include based on system complexity — a simple CLI tool might get 4-5 sections, a complex distributed system might get all 9. Omitted sections skip their number.

**Available sections and their files:**

| File | Section | Content | Level Tag |
|------|---------|---------|-----------|
| `00-metadata.md` | Metadata | System name, URLs, license, GitHub, tag | — |
| `01-overview.md` | Overview | What it is, who it's for, core value proposition | beginner |
| `02-core-concepts.md` | Core Concepts | Key abstractions, mental models, terminology with analogies | beginner |
| `03-architecture.md` | Architecture | System design, components, data flow, design decisions | intermediate |
| `04-how-it-works.md` | How It Works | Internal mechanisms, algorithms, protocols | intermediate |
| `05-implementation-details.md` | Implementation Details | Getting started, configuration, code patterns, source code walkthrough, deployment | advanced |
| `06-use-cases.md` | Use Cases & Case Studies | When to use, when NOT to use, real-world examples | beginner-intermediate |
| `07-ecosystem.md` | Ecosystem & Integrations | Related tools, plugins, complementary systems | intermediate |
| `08-common-qa.md` | Common Q&A | Frequently asked questions with detailed answers | all |
| `09-tradeoffs.md` | Trade-offs & Limitations | Strengths, limitations, alternatives comparison | intermediate |

**Critical:** Every section file MUST have a level comment tag. The HTML course generator depends on these tags to structure content by difficulty. Use exactly these formats:
- `<!-- level: beginner -->`
- `<!-- level: intermediate -->`
- `<!-- level: advanced -->`
- `<!-- level: beginner-intermediate -->`
- `<!-- level: all -->`

**References:** Each section file should include a `<!-- references: ... -->` block after the level tag, listing 2-5 authoritative sources relevant to that section. See `references/analysis-template.md` for format and reference types.

**Inline links:** Include standard markdown links within the content body on first mention of concepts with authoritative external sources. Link claims that benefit from a primary source (benchmarks, architectural decisions, papers).

**Source annotations:** When including code blocks that represent actual source code from the system's codebase, annotate them with `// source:`, `// github:`, and `// tag:` metadata lines. See `references/analysis-template.md` for format. The Metadata section's GitHub and Tag fields (from `00-metadata.md`) provide default values.

**Implementation Details — Source Code Walkthrough (MANDATORY for open-source systems):** When the system has a public GitHub repository and source code was gathered in Phase 2, the `05-implementation-details.md` file MUST include a `### Source Code Walkthrough` sub-section with actual annotated source code — not just a directory listing or prose description of the codebase structure. A "Source Code Structure" section that only lists directory paths is NOT a substitute.

Use the concept-to-source mapping table from Phase 2's Source Code Research. For EACH core concept (from `02-core-concepts.md`), include the actual source code that implements it. Cross-reference explicitly: "This implements the [Concept Name] concept from Core Concepts." The mapping table tells you which file, lines, and key types to use — transcribe those excerpts into annotated code blocks with `// source:`, `// github:`, and `// tag:` annotations. Aim for 5-12 annotated source blocks. For complex concepts, use multi-block sequences (2-4 blocks chained with bridging commentary) or the focus + context pattern (critical excerpt in full, surrounding code summarized in prose with a GitHub permalink). See `references/section-templates/05-implementation-details.md` for the detailed template.

For multi-repo systems, include source blocks from all relevant repositories. Use the `// github:` annotation to override the default repo for blocks from secondary repos.

If Phase 2's Source Code Research failed to fetch source files (rate limiting, repo not found), document the failure and retry with alternative URLs before falling back to a behavioral analysis. The absence of a Source Code Walkthrough for an open-source system is a review failure in Phase 4.

### Phase 4: Self-Review & Fix

Before presenting to the user, review the analysis and fix issues. Iterate until the review passes.

**Review checklist:**
1. **Manifest completeness** — Does `analysis.json` list all generated section files? Do the `file`, `title`, `level`, and `order` fields match the actual files?
2. **Level tags** — Does EVERY section file have a `<!-- level: ... -->` comment? Missing tags break the HTML generator. Scan every `##` heading in each file.
3. **Analogies** — Does every Core Concepts entry (in `02-core-concepts.md`) have a real-world analogy? If any concept is explained with only abstract definitions, add an analogy.
4. **Architecture "why"** — Does `03-architecture.md` explain WHY each component exists, not just what it does? If any component is just described without motivation, add the "why."
5. **Code examples** — Does `05-implementation-details.md` have actual code snippets, config examples, or commands? If it reads like prose, add concrete examples.
6. **Source code coverage (HARD FAIL for open-source systems)** — If the system has a public GitHub repository, verify ALL of the following:
   - Does `05-implementation-details.md` include a `### Source Code Walkthrough` sub-section (not `### Source Code Structure` or similar)?
   - Does it contain at least 5 annotated source code blocks with actual code excerpts from the system's repository (not just directory listings, not synthetic/illustrative code)?
   - Does each block have `// source:`, `// github:`, and `// tag:` annotations?
   - **Concept coverage check:** List every core concept from `02-core-concepts.md`. For EACH concept, verify there is at least one annotated source block in the walkthrough that implements it. Missing concepts = go back to Phase 2 and fetch their source.
   - Do the `// source:` paths correspond to real files discovered in Phase 2?
   - For multi-repo systems: are source blocks included from all relevant repositories (not just the primary one)?
   - Are multi-block sequences or focus + context patterns used for complex concepts?
   If ANY of these checks fail for an open-source system, this is a BLOCKING failure — go back to Phase 2 to fetch source code and rewrite the section before proceeding. (Skip this check only if the system is genuinely closed-source with no public repository.)
7. **Honest trade-offs** — Does `09-tradeoffs.md` name real limitations and alternatives? If it reads like marketing copy, rewrite with honest assessments.
8. **Q&A quality** — Are the questions in `08-common-qa.md` ones a senior engineer would actually ask? If any are trivial ("What is X?"), replace with deeper questions.
9. **Factual accuracy** — Cross-check key claims against your web research. Are version numbers, URLs, and feature claims still current?
10. **Section depth** — Is each section file substantive enough to justify its inclusion? If a section has only 1-2 sentences, either expand it or remove the file (and its manifest entry).
11. **References** — Does each section file with substantial content have a `<!-- references: ... -->` block with 2-5 relevant sources? Are the URLs valid and the types correct?
12. **Source annotations** — Do code blocks showing actual source code have `// source:` annotations with valid file paths? Do the `// github:` and `// tag:` values match `00-metadata.md` or override correctly?
13. **Inline links** — Are key concepts and claims linked to authoritative sources on first mention? Are there 2-4 inline links per section file (not over-linked)?

**Fix loop:** If any check fails, fix the issue in the relevant file and re-run the checklist. Only proceed once all checks pass.

### Phase 5: Checkpoint

Before finalizing, present a summary to the user:
- List which section files were generated and their estimated depth (shallow / moderate / deep)
- Highlight any areas where web research found especially good or surprising information
- Note any sections that were omitted and why
- For the Source Code Walkthrough, list how many annotated source blocks were included and which concepts they cover

Let the user request changes:
- **More depth** in specific areas (re-generate individual section files)
- **Additional sections** that were omitted (add new section files and update `analysis.json`)
- **Removal** of sections that aren't relevant (delete section files and update `analysis.json`)
- **Corrections** to any inaccuracies (edit the specific section file)

Apply changes to the relevant section files, update `analysis.json` if the section list changed, then confirm completion.

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

The analysis is written as multiple files in `[output-dir]`, with a JSON manifest as the entry point:

```
[output-dir]/
  analysis.json              # manifest — entry point for downstream consumers
  00-metadata.md             # system name, URLs, license, GitHub, tag
  01-overview.md             # what it is, who it's for (beginner)
  02-core-concepts.md        # key abstractions with analogies (beginner)
  03-architecture.md         # components, data flow, design decisions (intermediate)
  04-how-it-works.md         # algorithms, protocols, internals (intermediate)
  05-implementation-details.md  # getting started, code patterns, source walkthrough (advanced)
  06-use-cases.md            # when to use, when not to, real-world examples (beginner-intermediate)
  07-ecosystem.md            # tools, integrations, community (intermediate)
  08-common-qa.md            # senior-engineer Q&A (all)
  09-tradeoffs.md            # strengths, limitations, alternatives (intermediate)
```

Not all section files are required. The manifest (`analysis.json`) lists only the sections that were generated. Omitted sections skip their number. See `references/section-templates/manifest-template.json` for the manifest format and `references/section-templates/` for per-section templates.

Each section file is self-contained with its own `## Heading`, `<!-- level: ... -->` tag, `<!-- references: ... -->` block, and sub-sections. See `references/analysis-template.md` for the full structural reference.

## Integration

- **Standalone:** Write analysis files to `[output-dir]/` (manifest + section files) and suggest running system-to-course next to generate the HTML course.
- **Orchestrated by system-explorer:** Use the output directory provided by the orchestrator (do not re-ask the user). Return the output directory path so the orchestrator can pass it to the next phase. The downstream system-to-course skill detects the multi-file format via `analysis.json`.
