# Implementation Details Section Template

Self-contained template for the Implementation Details section. Level: **advanced**.

```markdown
## Implementation Details
<!-- level: advanced -->
<!-- references:
- [Title](URL) | official-docs
- [Title](URL) | github
- [Title](URL) | tutorial
-->
<!-- Hands-on: code snippets, config files, deployment patterns, and source code walkthrough. -->

### Getting Started
<!-- Fastest path from zero to "hello world." Docker/brew/equivalent.
     Include actual shell commands the reader can copy-paste. -->

### Configuration Essentials
<!-- 5-10 most important config knobs. What each controls, default, when to change.
     Include a config file snippet if applicable. -->

### Code Patterns
<!-- Common usage patterns with short code snippets (10-20 lines).
     These are USER-WRITTEN code examples (not source code from the system's repo). -->

### Source Code Walkthrough
<!-- MANDATORY for open-source systems with a public GitHub repository.
     This section MUST contain actual annotated source code excerpts — NOT just a
     directory listing or "Source Code Structure" overview. A section that only lists
     file paths like "mlflow/tracking/ -- Client-side tracking API" is NOT a walkthrough.

     For each core concept (from 02-core-concepts.md) and architectural component
     (from 03-architecture.md), include the actual source code from the system's
     repository that implements it. Group by concept.

     Structure:

     #### [Concept/Component Name] — Implementation
     Brief explanation of what this code does, how it relates to the concept defined
     in Core Concepts or the component described in Architecture, and why this
     particular code is interesting or revealing.

     ```language
     // source: path/to/file.ext:start-end
     // github: org/repo
     // tag: vX.Y.Z
     [actual source code excerpt, 20-60 lines per block]
     ```

     For complex concepts that span more code, use MULTI-BLOCK SEQUENCES —
     chain 2-4 blocks for a single concept with bridging commentary:

     #### [Concept Name] — Phase 1: [Phase Description]
     Explain what this phase does and what to look for...

     ```language
     // source: path/to/file.ext:start-end
     // github: org/repo
     // tag: vX.Y.Z
     [excerpt 1, 20-60 lines]
     ```

     #### [Concept Name] — Phase 2: [Phase Description]
     How this connects to Phase 1...

     ```language
     // source: path/to/file.ext:start-end
     // github: org/repo
     // tag: vX.Y.Z
     [excerpt 2, 20-60 lines]
     ```

     For large implementations where even multi-block sequences can't cover
     everything, use the FOCUS + CONTEXT pattern — show the critical excerpt
     in full and summarize the surrounding code in prose:

     The full `ClassName.method()` is ~200 lines (file.ext:340-540).
     The core logic is in the following section:

     ```language
     // source: path/to/file.ext:410-455
     // github: org/repo
     // tag: vX.Y.Z
     [key excerpt, 20-60 lines]
     ```

     Lines 340-409 handle [brief summary of preceding code].
     Lines 456-540 handle [brief summary of following code].

     > Full implementation: [file.ext:340-540](https://github.com/org/repo/blob/tag/path/to/file.ext#L340-L540)

     Guidelines:
     - Aim for 5-12 annotated source blocks covering the most important concepts
     - Keep each individual block at 20-60 lines for readability (one screenful)
     - Use multi-block sequences (2-4 blocks) for concepts that span more code
     - Use the focus + context pattern for very large implementations (100+ lines)
     - Each block MUST have // source:, // github:, and // tag: annotations
     - Prefer code that reveals design decisions over boilerplate
     - Include brief commentary before each block explaining what to look for
     - Cross-reference concept names from 02-core-concepts.md and component names
       from 03-architecture.md
     - If source code is unavailable (closed-source system), note this and provide
       behavioral analysis instead
     - If the system is open-source but you only have a directory listing, this section
       is INCOMPLETE — go back to Phase 2 and fetch actual source files -->

### Deployment Considerations
<!-- Production checklist: sizing, monitoring, backup, upgrade path. -->
```

## Content Guidance

- "Getting Started" should be copy-paste ready — a reader should go from zero to running in minutes
- "Code Patterns" shows how USERS write code against the system (producer/consumer, queries, etc.)
- "Source Code Walkthrough" shows the system's OWN source code that implements each concept — this is the key differentiator of this section
- Source annotations use language-appropriate comment syntax:
  - C/C++/Java/Go/Rust/JS/TS: `// source: ...`
  - Python/Ruby/Shell/YAML: `# source: ...`
  - SQL/Lua/Haskell: `-- source: ...`
  - HTML/XML: `<!-- source: ... -->`
- The `// github:` and `// tag:` values default to the Metadata section's GitHub and Tag fields but can be overridden per block
- "Deployment Considerations" is for production readiness, not getting-started
