# Skills Playground

## Installation

Each skill lives under `skills/[skill_name]/[skill_name]/`.

### Claude Code

Copy the skill folder(s) into your Claude Code skills directory:

```bash
# paper-to-course
cp -r skills/paper-to-course/paper-to-course ~/.claude/skills/paper-to-course

# system-explorer (includes sub-skills: system-analyzer, system-finder, system-to-course)
cp -r skills/system-explorer/system-explorer ~/.claude/skills/system-explorer
cp -r skills/system-explorer/system-analyzer ~/.claude/skills/system-analyzer
cp -r skills/system-explorer/system-finder ~/.claude/skills/system-finder
cp -r skills/system-explorer/system-to-course ~/.claude/skills/system-to-course
```

### Codex

Copy the skill folder(s) into your Codex skills directory:

```bash
# paper-to-course
cp -r skills/paper-to-course/paper-to-course ~/.agents/skills/paper-to-course

# system-explorer (includes sub-skills: system-analyzer, system-finder, system-to-course)
cp -r skills/system-explorer/system-explorer ~/.agents/skills/system-explorer
cp -r skills/system-explorer/system-analyzer ~/.agents/skills/system-analyzer
cp -r skills/system-explorer/system-finder ~/.agents/skills/system-finder
cp -r skills/system-explorer/system-to-course ~/.agents/skills/system-to-course
```

## Skills

- paper-to-course: idea originated from [Codebase to Course](https://github.com/zarazhangrui/codebase-to-course)
- system-explorer: explore and learn about any software system through a full pipeline — discover matching systems, deep-dive research, and generate an interactive HTML course

## License

[LICENSE](./LICENSE)