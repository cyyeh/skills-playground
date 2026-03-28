# Skills Playground

## Installation

### Claude Code (Marketplace)

Add the marketplace and install plugins:

```
/plugin marketplace add cyyeh/skills-playground
/plugin install paper-to-course@skills-playground
/plugin install system-explorer@skills-playground
```

### Codex (Skill Installer)

Inside a Codex session, use `$skill-installer` to install from GitHub:

```
$skill-installer install https://github.com/cyyeh/skills-playground/tree/main/skills/paper-to-course/paper-to-course
$skill-installer install https://github.com/cyyeh/skills-playground/tree/main/skills/system-explorer/system-explorer
$skill-installer install https://github.com/cyyeh/skills-playground/tree/main/skills/system-explorer/system-analyzer
$skill-installer install https://github.com/cyyeh/skills-playground/tree/main/skills/system-explorer/system-finder
$skill-installer install https://github.com/cyyeh/skills-playground/tree/main/skills/system-explorer/system-to-course
```

Restart Codex after installation.

## Skills

- paper-to-course: idea originated from [Codebase to Course](https://github.com/zarazhangrui/codebase-to-course)
- system-explorer: explore and learn about any software system through a full pipeline — discover matching systems, deep-dive research, and generate an interactive HTML course

## License

[LICENSE](./LICENSE)