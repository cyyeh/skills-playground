# Common Q&A Section Template

Self-contained template for the Common Q&A section. Level: **all**.

```markdown
## Common Q&A
<!-- level: all -->
<!-- references:
- [Title](URL) | official-docs
- [Title](URL) | community
-->
<!-- Real questions a senior engineer would ask when evaluating or operating the system.
     Not basics — hard, practical questions. Aim for 5-8 questions. -->

### Q: [Hard practical question]
<!-- E.g.: "What happens to in-flight messages if a broker crashes mid-replication?" -->

### Q: [Operational question]
<!-- E.g.: "How do I handle schema evolution without breaking consumers?" -->

### Q: [Comparison question]
<!-- E.g.: "When should I choose X over Y?" -->

### Q: [Scaling question]
<!-- E.g.: "What are the practical limits of this architecture?" -->

### Q: [Debugging question]
<!-- E.g.: "Consumer lag is increasing — what's the diagnostic playbook?" -->
```

## Content Guidance

- Questions should be what a senior engineer would ask when EVALUATING or OPERATING this system
- NOT "What is X?" questions — those belong in Core Concepts
- Each answer should be substantive (3-8 sentences), not one-liners
- Include concrete numbers, commands, or config examples in answers where relevant
- Aim for 5-8 questions covering: failure modes, operational concerns, scaling limits, comparisons, debugging
- Include inline links to relevant documentation in answers
