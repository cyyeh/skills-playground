# How It Works Section Template

Self-contained template for the How It Works section. Level: **intermediate**.

```markdown
## How It Works
<!-- level: intermediate -->
<!-- references:
- [Title](URL) | official-docs
- [Title](URL) | paper
- [Title](URL) | blog
-->
<!-- Internal mechanisms: algorithms, protocols, clever tricks. Deeper than Architecture. -->

### [Mechanism 1: e.g., Storage Engine]
<!-- How data is stored, indexed, retrieved. File formats, data structures. -->

### [Mechanism 2: e.g., Replication Protocol]
<!-- Durability/consistency/availability mechanisms. Failure handling. -->

### [Mechanism 3: e.g., Consensus / Coordination]
<!-- Distributed agreement: leader election, quorum decisions. -->

### Performance Characteristics
<!-- Where it's fast, where it's slow, and why. Include numbers when available.
     Cite benchmarks with sources. -->
```

## Content Guidance

- This section goes deeper than Architecture — it explains the algorithms and protocols behind the components
- Name mechanisms based on what the system actually does (storage, replication, scheduling, parsing, etc.)
- Include 2-4 mechanisms; more only if the system is truly complex
- "Performance Characteristics" should include concrete numbers where available, with citations
- Include source code snippets with `// source:` annotations when they illuminate a mechanism
- Include inline links to papers, design docs, and benchmark results
