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
<!-- For each core concept and architectural component, include the actual source code
     from the system's repository that implements it. Group by concept.

     Structure:

     #### [Concept/Component Name] — Implementation
     Brief explanation of what this code does, how it relates to the concept defined
     in Core Concepts or the component described in Architecture, and why this
     particular code is interesting or revealing.

     ```language
     // source: path/to/file.ext:start-end
     // github: org/repo
     // tag: vX.Y.Z
     [actual source code excerpt, 20-60 lines]
     ```

     Guidelines:
     - Aim for 5-8 annotated source blocks covering the most important concepts
     - Each block MUST have // source:, // github:, and // tag: annotations
     - Prefer code that reveals design decisions over boilerplate
     - Include brief commentary before each block explaining what to look for
     - Cross-reference concept names from 02-core-concepts.md and component names
       from 03-architecture.md
     - If source code is unavailable (closed-source system), note this and provide
       behavioral analysis instead -->

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
