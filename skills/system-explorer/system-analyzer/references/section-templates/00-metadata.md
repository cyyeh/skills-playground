# Metadata Section Template

This file is self-contained. It provides the metadata block that appears at the top of every analysis.

```markdown
# System Analysis: [System Name]

## Metadata
- **Name:** [System Name]
- **Category:** [e.g., Message Queue, Database, Container Orchestrator]
- **Official URL:** [link]
- **GitHub:** [org/repo, e.g., duckdb/duckdb]
- **Tag:** [latest stable tag, e.g., v1.5.1 — used for source code links]
- **License:** [license type]
- **Latest Version:** [version if found]
- **Analysis Date:** [YYYY-MM-DD]
```

## Field Notes

- **GitHub** and **Tag** are used as defaults for source-annotated code blocks throughout all section files. Every section file can reference these values.
- **Tag** should be the latest stable release tag, not `main` or `HEAD`. Used in `// tag:` annotations and raw GitHub URLs.
- **Analysis Date** is the date the analysis was generated, in ISO 8601 format.
- **Category** helps the section selection heuristic — simple tools/libraries get fewer sections than complex distributed systems.
