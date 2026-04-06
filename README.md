# Skills Playground

## Installation

### Claude Code (Marketplace)

Add the marketplace and install plugins:

```
/plugin marketplace add cyyeh/skills-playground
/plugin install paper-to-course@skills-playground
/plugin install system-explorer@skills-playground
/plugin install learning-platform@skills-playground
```

### Codex (Skill Installer)

Inside a Codex session, use `$skill-installer` to install from GitHub:

```
$skill-installer install https://github.com/cyyeh/skills-playground/tree/main/skills/paper-to-course/paper-to-course
$skill-installer install https://github.com/cyyeh/skills-playground/tree/main/skills/system-explorer/system-explorer
$skill-installer install https://github.com/cyyeh/skills-playground/tree/main/skills/system-explorer/system-analyzer
$skill-installer install https://github.com/cyyeh/skills-playground/tree/main/skills/system-explorer/system-finder
$skill-installer install https://github.com/cyyeh/skills-playground/tree/main/skills/system-explorer/system-to-course
$skill-installer install https://github.com/cyyeh/skills-playground/tree/main/skills/learning-platform/learning-platform
```

Restart Codex after installation.

## Skills

- paper-to-course: idea originated from [Codebase to Course](https://github.com/zarazhangrui/codebase-to-course)
- system-explorer: explore and learn about any software system through a full pipeline — discover matching systems, deep-dive research, and generate an interactive HTML course
- learning-platform: create structured interactive learning platforms for any field or subject

## Releasing a Plugin

Each skill group (e.g. `paper-to-course`, `system-explorer`) is versioned independently via `skills/<group>/version.json`. The `release.sh` script manages the full lifecycle:

```bash
# 1. Bump the version (commits automatically)
./release.sh bump <skill-group> <major|minor|patch>

# 2. Create a git tag and validate the build
./release.sh release <skill-group>

# 3. Push the tag to trigger the GitHub Actions release workflow
git push origin <skill-group>/v<version>
```

Pushing a tag matching `*/v*` triggers the [release workflow](.github/workflows/release.yml), which validates the build and creates a GitHub Release with auto-generated release notes.

You can also run `./release.sh build <skill-group>` independently to validate skills and regenerate `.claude-plugin/marketplace.json`.

## License

[LICENSE](./LICENSE)