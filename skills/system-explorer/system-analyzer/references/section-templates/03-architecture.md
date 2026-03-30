# Architecture Section Template

Self-contained template for the Architecture section. Level: **intermediate**.

```markdown
## Architecture
<!-- level: intermediate -->
<!-- references:
- [Title](URL) | official-docs
- [Title](URL) | paper
- [Title](URL) | blog
-->
<!-- System design and components. Always explain WHY each component exists. -->

### High-Level Design
<!-- 10,000-foot view. Major components and their interactions.
     Consider an ASCII diagram showing component relationships. -->

### Key Components
<!-- Each component: what it does, why it exists, what problem it solves. E.g.:
     "**Controller Node** — Manages partition assignments. Exists because distributed
     systems need a single source of truth for cluster state." -->

### Data Flow
<!-- Trace a request/message through the system end-to-end, step by step.
     Number the steps. Show the path data takes from input to output. -->

### Design Decisions
<!-- Interesting architectural choices and their rationale.
     Why did the authors choose X over Y? What constraints drove the design? -->
```

## Content Guidance

- Don't just describe components — explain WHY they exist and what problem they solve (checked in self-review)
- "High-Level Design" benefits from an ASCII or text diagram
- "Data Flow" should be a numbered walkthrough a reader can follow step-by-step
- "Design Decisions" is where the analysis gets interesting — show the trade-offs the designers considered
- Include inline links to architecture documentation and design papers
- Component names here will be cross-referenced by Implementation Details' Source Code Walkthrough
