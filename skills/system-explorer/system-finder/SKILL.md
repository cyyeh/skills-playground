---
name: system-finder
description: "Discover and compare software systems that match a user's needs. Given a specific system name, software category, or functional requirement, this skill searches for matching systems, validates findings with web research, and presents a structured comparison table so the user can make an informed selection. Trigger this skill when users say 'find systems for', 'what message queues exist', 'compare databases for', 'I need a tool for', 'show me options for', 'what are alternatives to', 'best database for', or 'Kafka vs RabbitMQ'. Also trigger when the user asks about software categories, technology comparisons, tool recommendations, or when they need help choosing between technologies."
license: Apache-2.0
metadata:
  author: cyyeh
---

# System Finder

Discover software systems that match a user's target and present a structured comparison for selection. The target can be a specific system name ("Kafka"), a software category ("message queues"), or a functional requirement ("I need real-time data processing"). The output is a comparison table written to a user-chosen output directory (default: `dist/[system-name]/finder-report.md`).

## First-Run Welcome

When triggered without a specific query, introduce the skill:

> **I can help you find and compare software systems.**
>
> Tell me what you're looking for:
> - **A specific system** -- "Tell me about Kafka" or "What is CockroachDB?"
> - **A category** -- "What message queues exist?" or "Compare CI/CD tools"
> - **A requirement** -- "I need real-time analytics" or "I need a database for time series data"
> - **Alternatives** -- "What are alternatives to Redis?" or "Kafka vs RabbitMQ"
>
> I'll research options, compare them, and help you pick the right one.

## Output Directory

**Always ask the user where to save the finder report before writing any files.** Use AskUserQuestion to prompt:

> Where would you like me to save the finder report?
> Default: `dist/[system-name]/`

Accept the user's chosen path. If they accept the default or say something like "that's fine" or "default", use `dist/[system-name]/`. Store this path as `[output-dir]`.

**Exception:** When called by the system-explorer orchestrator with a pre-determined output directory, use that directory without re-asking.

Create the directory if it does not exist.

## The Process (3 Phases)

### Phase 1: Understand the Target

Parse the user's query to determine the type:

1. **Specific system** -- The user named a system ("Kafka", "Redis", "Terraform"). Confirm the target: "You want to explore Apache Kafka?" Then suggest proceeding directly to system-analyzer. Skip Phase 2 unless the user wants to see alternatives.
2. **Category** -- The user named a software category ("message queues", "databases", "CI/CD tools"). Proceed to Phase 2 to discover systems in that category.
3. **Requirement** -- The user described a need ("I need real-time data processing", "something for container orchestration"). Map the requirement to one or more categories, then proceed to Phase 2.
4. **Comparison** -- The user wants to compare specific systems ("Kafka vs RabbitMQ"). Proceed to Phase 3 with those systems pre-selected.

**If the query is ambiguous, ask ONE clarifying question.** Use the AskUserQuestion tool with multiple-choice options when possible. Do not ask a chain of questions -- get what you need in one round.

Example clarification:
> When you say "database," what's the primary use case?
> 1. Relational / transactional (PostgreSQL, MySQL)
> 2. Document / flexible schema (MongoDB, CouchDB)
> 3. Key-value / caching (Redis, Memcached)
> 4. Time series (InfluxDB, TimescaleDB)
> 5. Something else -- describe it

### Phase 2: Research & Discover

Start with built-in knowledge as a foundation, then validate and expand using web research. Discovery uses three search rounds to minimize blind spots.

**Read `references/search-strategies.md`** for query templates tailored to each query type, including adjacent category and blind spot strategies.

#### Round 1: Direct Category Search

Search within the user's stated category to find the obvious players.

**Use WebSearch to find:**
- Emerging alternatives the model may not know about
- Recent adoption changes, major new releases, or deprecations
- Current GitHub stars and community activity signals
- Recent benchmark comparisons or migration stories

#### Round 2: Adjacent Category Expansion

The user's stated category is often a *subset* of a broader space. Platforms from parent or sibling categories frequently expand into the target area and get missed by direct searches.

**Steps:**
1. **Identify the category hierarchy.** Map the user's query to at least one broader parent category and one sibling category. Example for "LLM tracing": parent = "ML observability" / "MLOps platforms", sibling = "APM tools" / "general observability".
2. **Search the broader categories.** Run WebSearch queries that combine the parent/sibling category with the target capability (e.g., `"MLOps platform" LLM tracing`, `"ML platform" LLM observability`).
3. **Search for established platforms adding the capability.** Well-known platforms often add features without being reclassified. Search for `"[known platform] [target capability]"` for 2-3 likely candidates from adjacent spaces (e.g., `"MLflow tracing"`, `"Datadog LLM observability"`).

#### Round 3: Blind Spot Detection

After Rounds 1-2, actively check for gaps before finalizing.

**Steps:**
1. **Search for "alternatives to" your current top result.** This surfaces competitors that comparison articles may cluster differently (e.g., `"Langfuse alternatives"` will surface platforms that Langfuse-focused articles compare against).
2. **Search community discussions.** Check Reddit, HackerNews, or forums for real-world recommendations: `"[category] recommendations site:reddit.com OR site:news.ycombinator.com"`. Practitioners mention tools that listicles miss.
3. **Cross-check your list.** Ask: "Is there a well-known platform in a related space that likely has this capability but isn't on my list?" If yes, do a targeted search to confirm or exclude it.

**Target: 3-7 matching systems.** Fewer than 3 gives nothing to compare. More than 7 overwhelms. Aim for a mix of:
- Category-native leaders (born in this space)
- Broader platforms that expanded into this space
- Promising newcomers or open-source alternatives

**For each system, gather:**
- Official name and one-line description
- Category or sub-category (note if it originated from an adjacent category)
- Primary language and ecosystem
- 2-3 key strengths
- 2-3 key trade-offs or limitations
- Maturity level: emerging / established / mature
- GitHub stars or adoption signals (if available)

### Phase 3: Compare & Present

Build a structured comparison table and present it to the user.

**Comparison table columns:**
| Name | Category | Language | Strengths | Trade-offs | Maturity |
|------|----------|----------|-----------|------------|----------|

Include GitHub stars or adoption notes in the Maturity column when available.

**After presenting the table:**
1. Offer a brief editorial summary highlighting which systems suit which use cases
2. Let the user pick one or more systems to explore further
3. Write the finder report to `[output-dir]/finder-report.md`

## Phase 4: Self-Review & Fix

Before presenting results to the user, review your own output and fix issues. Iterate until the review passes.

**Review checklist:**
1. **Completeness** — Does the table have 3-7 systems? Are all columns filled for every system?
2. **Accuracy** — Are strengths/trade-offs actually correct and not generic filler? Cross-check against your web research.
3. **Balance** — Are you favoring a system unfairly? Ensure trade-offs are honest for every entry, including popular ones.
4. **Currency** — Is any information stale? Check that maturity levels and adoption signals reflect current state, not 3-year-old data.
5. **Differentiation** — Can the user actually tell the systems apart from the table? If two entries sound identical, sharpen the differences.
6. **Adjacent coverage** — Does the list include at least one platform from a broader/adjacent category? If all results are "category-native," you likely missed established platforms that expanded into this space. Go back to Phase 2 Round 2.
7. **Editorial summary** — Does the summary after the table help the user decide, not just restate the table?

**Fix loop:** If any check fails, fix the issue and re-run the checklist. Only present to the user once all checks pass.

## Output Format

Write the report using this template:

```markdown
# System Finder Report: [User Query]

## Query
[Original user query and any clarifications]

## Comparison

| System | Category | Language | Strengths | Trade-offs | Maturity |
|--------|----------|----------|-----------|------------|----------|
| ...    | ...      | ...      | ...       | ...        | ...      |

## Selected: [System Name]
[Brief rationale for selection]
```

Create `[output-dir]` if it does not exist.

## Integration

**Standalone usage:**
- Write `finder-report.md` to `[output-dir]`
- Suggest running system-analyzer next to do a deep dive on the selected system

**Called by system-explorer orchestrator:**
- Use the output directory provided by the orchestrator (do not re-ask the user)
- Return the comparison table and the user's selection
- The orchestrator will pass the selection to system-analyzer for the next phase

## Reference Files

- **`references/search-strategies.md`** -- Query templates and research strategies for each query type. Read this before starting Phase 2.
