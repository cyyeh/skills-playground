---
name: system-explorer
description: "The main entry point for exploring and learning about any software system. This skill orchestrates a full pipeline: discover matching systems, deep-dive research, and generate an interactive HTML course -- all with user checkpoints between phases. Trigger when users say 'explore [system]', 'teach me about [system]', 'I want to understand [technology]', 'system explorer', 'help me learn [system]', 'what is [system] and how does it work', 'I need to understand [category] systems', or any general request to learn about, explore, compare, or understand software systems, infrastructure tools, or distributed systems."
license: Apache-2.0
metadata:
  author: cyyeh
---

# System Explorer

Single entry point that orchestrates three sub-skills into a complete learning pipeline: discover systems, analyze in depth, and generate an interactive course -- with user checkpoints between each phase.

## First-Run Welcome

When triggered, greet the user and explain the pipeline:

> **I can help you explore and learn any software system -- from discovery to a full interactive course.**
>
> Here's how it works:
> 1. **Discover** -- Find and compare systems that match what you're looking for
> 2. **Analyze** -- Deep-dive research with layered depth (beginner to advanced)
> 3. **Generate** -- Build an interactive multi-page HTML course you can browse
>
> Just tell me what you want to explore:
> - A specific system -- "Explore Kafka"
> - A category -- "I want to understand message queues"
> - A requirement -- "Help me find a database for time-series data"

## Flow

```
User query
    |
    v
+---------------------+
|  1. Clarify target   |  Ask questions if ambiguous
+----------+----------+
           v
+---------------------+
|  2. Ask output dir   |  User chooses where artifacts go
+----------+----------+
           v
+---------------------+
|  3. system-finder    |  Discover & compare systems
|     -> comparison    |  User picks system(s)
+----------+----------+
           v  Checkpoint
+---------------------+
|  4. system-analyzer  |  Deep-dive research
|     -> analysis.md   |  User reviews findings
+----------+----------+
           v  Checkpoint
+---------------------+
|  5. system-to-course |  Generate HTML site
|     -> [output-dir]  |  User reviews output
+----------+----------+
           v
     Done
```

## Smart Shortcuts

Skip phases when they are not needed:

- **Specific system named** ("explore Kafka") -- Skip finder and go directly to analyzer. Confirm with user: "You want to explore Apache Kafka. Shall I start the deep-dive analysis, or would you prefer to see alternatives first?"
- **Existing finder-report.md** -- If `[output-dir]/finder-report.md` exists, offer to skip finder: "I found an existing finder report. Want to use it, or start fresh?"
- **Existing analysis.md** -- If `[output-dir]/analysis.md` exists, offer to skip to course generation: "There's already an analysis on file. Jump to course generation, or redo the analysis?"
- **Multiple systems** -- If the user wants to compare multiple systems, run analyzer for each (potentially in parallel using the Agent tool), then generate a combined or separate course site per system.

## Phase 1: Clarify Target

Parse the user's query to determine intent:

- **Clear target** (specific system or well-defined category) -- Proceed immediately.
- **Ambiguous query** -- Ask ONE clarifying question. Do not chain multiple questions. Use multiple-choice options when possible.

Examples of clear targets: "Explore Kafka", "Message queue systems", "I need a time-series database."
Examples of ambiguous queries: "I want to learn about data stuff", "Help me with streaming."

## Phase 2: Ask Output Directory

**Always ask the user where to save generated artifacts before starting any sub-skill.** Use AskUserQuestion to prompt:

> Where would you like me to save the output files (finder report, analysis, HTML course)?
> Default: `dist/[system-name]/`

Accept the user's chosen path. If they accept the default or say something like "that's fine" or "default", use `dist/[system-name]/`. Store this path as `[output-dir]` and pass it to all sub-skills.

Create the directory if it does not exist.

## Phase 3: Discovery (system-finder)

Invoke the system-finder skill process, passing `[output-dir]` as the output directory:

1. Research matching systems using Claude knowledge + WebSearch
2. Present a structured comparison table (3-7 systems)
3. User picks a system
4. Write `finder-report.md` to `[output-dir]`

**Checkpoint:** "I found these systems. Here's the comparison. Which would you like to analyze in depth?"

Wait for user selection before proceeding.

## Phase 4: Analysis (system-analyzer)

Invoke the system-analyzer skill process, passing `[output-dir]` as the output directory:

1. Layered research: Claude knowledge, then WebSearch, then WebFetch for primary sources
2. Write structured `analysis.md` with level tags (beginner / intermediate / advanced)
3. Write `analysis.md` to `[output-dir]`

**Checkpoint:** Present a summary of what was found -- list the sections and their depth levels. Ask: "Analysis complete. Here's what I covered: [section list]. Ready to generate the interactive course, or want to adjust anything?"

Wait for user confirmation before proceeding.

## Phase 5: Course Generation (system-to-course)

Invoke the system-to-course skill process, passing `[output-dir]` as the output directory:

1. Read `analysis.md` from `[output-dir]`
2. Generate multi-page HTML with level selector (Beginner / Intermediate / Advanced)
3. Write all HTML files to `[output-dir]`
4. Open `index.html` in the browser for review

**Checkpoint:** "The course is ready. I've opened it in your browser. Take a look and let me know if you'd like any changes."

## Phase 6: Final Review & Fix

After the course is generated, perform a final end-to-end review of the complete output. This reviews the overall pipeline result, not just individual phases.

**Review checklist:**
1. **Finder → Analyzer consistency** — Does the analysis match what the finder report said? If the finder highlighted specific strengths/trade-offs, are they reflected in the analysis?
2. **Analyzer → Course consistency** — Does the HTML course cover all sections from analysis.md? Are any sections missing or empty in the HTML?
3. **Level selector** — Do all pages have proper `data-level` tags? Does toggling levels actually hide/show content?
4. **Navigation** — Do all cross-page links work? Is the current page highlighted in the nav?
5. **Content quality** — Read through each page in the browser. Are there walls of text that should be interactive elements? Missing analogies? Generic filler?
6. **Interactive elements** — Does each page have at least one interactive element (diagram, quiz, decision tree, code snippet)?

**Fix loop:** If any check fails, fix the source (analysis.md or HTML) and re-run the check. Iterate until all checks pass. Then present the final result to the user.

## Output

The final output is a multi-page static HTML site in the user-chosen `[output-dir]` containing:

- `index.html` -- Landing page with navigation
- Individual content pages (`concepts.html`, `architecture.html`, etc.)
- Level-based content filtering (Beginner / Intermediate / Advanced)
- `analysis.md` -- Source reference from Phase 4
- `finder-report.md` -- Discovery report from Phase 3 (if finder was run)

## Error Handling

- If a sub-skill fails or produces incomplete output, report the issue to the user and offer to retry that phase.
- If the user wants to skip ahead at any checkpoint, honor the request.
- If the user wants to go back and redo a phase, re-run that sub-skill from scratch.
