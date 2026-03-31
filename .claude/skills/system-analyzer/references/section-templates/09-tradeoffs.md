# Trade-offs & Limitations Section Template

Self-contained template for the Trade-offs & Limitations section. Level: **intermediate**.

```markdown
## Trade-offs & Limitations
<!-- level: intermediate -->
<!-- references:
- [Title](URL) | blog
- [Title](URL) | official-docs
-->
<!-- Honest assessment. Every system has weaknesses — name them. -->

### Strengths
<!-- 3-5 genuine technical strengths that matter in production.
     Be specific — not "fast" but "sub-millisecond point lookups at 99th percentile." -->

### Limitations
<!-- 3-5 real limitations. Be specific. E.g.: "No built-in exactly-once delivery
     across system boundaries — only within the Kafka ecosystem." -->

### Alternatives Comparison
<!-- 2-3 alternatives. For each: what it does better, worse, when to choose it.
     Consider a comparison table for clarity. -->

### The Honest Take
<!-- 2-3 sentences. When would you recommend this system? When would you not?
     This should read like advice from a trusted senior engineer, not marketing. -->
```

## Content Guidance

- This section must be HONEST, not promotional (checked in self-review)
- "Strengths" should cite evidence (benchmarks, architectural properties) not just claims
- "Limitations" should be real engineering limitations, not "it could be better documented"
- "Alternatives Comparison" should be fair — name what alternatives genuinely do better
- "The Honest Take" is the most important sub-section — distill your assessment into advice
- Include inline links to benchmark results and comparison articles
