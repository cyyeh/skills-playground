# Release Script Design

Build/release/update cycle for publishing skills to Claude Code plugin marketplace and Codex skill marketplace.

## Overview

A single `release.sh` script handles both platforms. A GitHub Actions workflow creates releases on tag push. Each skill group is versioned independently.

## Skill Group Structure

Each skill group has a `version.json` at its root as the single source of truth:

```
skills/
  paper-to-course/
    version.json          # {"version": "0.1.0", "name": "paper-to-course", "description": "..."}
    paper-to-course/      # the actual skill (SKILL.md, evals/, references/)
  system-explorer/
    version.json          # {"version": "0.1.0", "name": "system-explorer", "description": "..."}
    system-explorer/      # main skill
    system-analyzer/      # sub-skill
    system-finder/        # sub-skill
    system-to-course/     # sub-skill
```

## Script Commands

### `./release.sh build <skill-group>`

- Validates skill structure (every sub-skill directory has a `SKILL.md`)
- Generates/updates `marketplace.json` at repo root for Claude Code plugin registration
- Validates Codex compatibility (directory layout matches expected structure)
- Reports issues; exits non-zero on validation failure
- Idempotent: running twice produces the same output

### `./release.sh bump <skill-group> <major|minor|patch>`

- Reads `skills/<skill-group>/version.json`, bumps the specified semver component
- Regenerates `marketplace.json` with the new version
- Commits the version changes (does NOT tag or push)

### `./release.sh release <skill-group>`

- Runs `build` to validate first
- Creates a git tag: `<skill-group>/v<version>` (e.g., `paper-to-course/v0.1.0`)
- Pushes the tag to origin
- Prints summary of what CI will do

## Marketplace Outputs

### Claude Code: `marketplace.json` (repo root)

Generated/updated by the `build` command. Registers each skill group as a plugin:

```json
{
  "name": "skills-playground",
  "owner": {
    "name": "cyyeh"
  },
  "metadata": {
    "description": "Custom skills for Claude Code and Codex"
  },
  "plugins": [
    {
      "name": "paper-to-course",
      "description": "Turn research papers into interactive HTML courses",
      "version": "0.1.0",
      "source": "./skills/paper-to-course/",
      "strict": false,
      "skills": [
        "./skills/paper-to-course/paper-to-course"
      ]
    },
    {
      "name": "system-explorer",
      "description": "Explore and learn about software systems",
      "version": "0.1.0",
      "source": "./skills/system-explorer/",
      "strict": false,
      "skills": [
        "./skills/system-explorer/system-explorer",
        "./skills/system-explorer/system-analyzer",
        "./skills/system-explorer/system-finder",
        "./skills/system-explorer/system-to-course"
      ]
    }
  ]
}
```

Users install via:
```
/plugin marketplace add cyyeh/skills-playground
/plugin install paper-to-course@skills-playground
```

### Codex

No extra packaging needed. The existing `skills/<group>/<skill>/SKILL.md` layout is already Codex-compatible. Users install via:
```
$skill-installer install https://github.com/cyyeh/skills-playground/tree/main/skills/paper-to-course/paper-to-course
```

## GitHub Actions: `.github/workflows/release.yml`

Triggers on skill group tags:

```yaml
on:
  push:
    tags:
      - '*/v*'
```

Steps:
1. Parse tag to extract skill group name and version
2. Run `./release.sh build <skill-group>` to validate
3. Create a GitHub Release titled `<skill-group> v<version>` with auto-generated release notes from commits since the previous tag for that skill group

## Version Policy

- Both skill groups start at `0.1.0`
- Each skill group is versioned independently
- Semver: major (breaking), minor (new features), patch (fixes)
- Tags follow the pattern `<skill-group>/v<version>`
