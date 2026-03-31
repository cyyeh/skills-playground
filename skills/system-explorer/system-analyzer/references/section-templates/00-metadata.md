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
- **Additional Repos:** [optional — for multi-repo systems, list secondary repos with brief role descriptions]
- **License:** [license type]
- **Latest Version:** [version if found]
- **Analysis Date:** [YYYY-MM-DD]
```

### Multi-Repo Example

Some systems span multiple repositories. List the primary repo in `GitHub` and secondary repos in `Additional Repos`:

```markdown
- **GitHub:** NVIDIA/NemoClaw
- **Tag:** latest
- **Additional Repos:** NVIDIA/OpenShell (sandbox runtime, Rust), openclaw/openclaw (agent framework, TypeScript)
```

Source-annotated code blocks default to the `GitHub` and `Tag` values. For code from secondary repos, override with per-block `// github:` and `// tag:` annotations.

## Field Notes

- **GitHub** and **Tag** are used as defaults for source-annotated code blocks throughout all section files. Every section file can reference these values.
- **Tag** should be the latest stable release tag, not `main` or `HEAD`. Used in `// tag:` annotations and raw GitHub URLs.
- **Additional Repos** is optional. Include it when core concepts are implemented across multiple repositories. Each entry should include the org/repo and a brief description of what that repo contains. During Phase 2 Source Code Research, all listed repos should be explored.
- **Analysis Date** is the date the analysis was generated, in ISO 8601 format.
- **Category** helps the section selection heuristic — simple tools/libraries get fewer sections than complex distributed systems.
