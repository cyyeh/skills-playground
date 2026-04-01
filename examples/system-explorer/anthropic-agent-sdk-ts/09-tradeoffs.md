# Tradeoffs & Alternatives

<!-- level:beginner -->
## When Should You Use the Agent SDK?

### Use the Agent SDK When:

- You want **built-in tool execution** (files, shell, web) without implementing it yourself
- You are building **Claude-powered automation** (CI/CD, code review, deployment)
- You need the **same capabilities as Claude Code** but in a programmatic form
- You want **session persistence** with resume and fork capabilities
- Your use case involves **code understanding and modification**
- You need **MCP integration** for connecting to external services

### Consider Alternatives When:

- You need to use **multiple AI providers** (OpenAI, Google, etc.) interchangeably
- You need a **framework-level abstraction** with built-in RAG, memory, and routing
- You want a **model-agnostic** agent framework
- You need **visual workflow builders** or low-code solutions
- Your agents do not need file/shell/web tools -- just conversation

### The Agent SDK vs. the Anthropic Client SDK

| Feature | Client SDK (`@anthropic-ai/sdk`) | Agent SDK (`@anthropic-ai/claude-agent-sdk`) |
|---------|----------------------------------|----------------------------------------------|
| Tool execution | You implement it | Built-in |
| Agent loop | You build it | Built-in |
| File operations | Not included | Read, Write, Edit, Glob, Grep |
| Shell commands | Not included | Bash tool |
| Web access | Not included | WebSearch, WebFetch |
| Session management | Not included | Built-in persistence/resume |
| MCP support | Not included | Built-in |
| Subagents | Not included | Built-in |
| Hooks/guardrails | Not included | Built-in |
| Control level | Maximum | Abstracted |
| Overhead | Minimal | Spawns child process |
| Cost | Pay per API call | Pay per API call + tool overhead |

**Rule of thumb:** If you need Claude to **do things** (read files, run commands, edit code), use the Agent SDK. If you need Claude to **answer questions** or you want full control over every API call, use the Client SDK.

## Comparison with Major Alternatives

### vs. LangChain / LangGraph

| Aspect | Agent SDK | LangChain / LangGraph |
|--------|-----------|----------------------|
| **Model support** | Claude only | Multi-model (OpenAI, Claude, Llama, etc.) |
| **Language** | TypeScript + Python | Python + JavaScript/TypeScript |
| **Philosophy** | Opinionated, batteries-included | Flexible, composable |
| **Built-in tools** | Yes (file, shell, web, MCP) | Minimal -- you add your own |
| **Agent loop** | Managed automatically | You compose with LangGraph |
| **Complexity** | Lower | Higher (more concepts to learn) |
| **RAG support** | Via MCP servers | Built-in with vector stores |
| **Community** | Growing (1.1K+ users) | Large (70K+ GitHub stars) |
| **Maturity** | Newer (2025) | Established (2023+) |

**Choose LangChain/LangGraph when:** You need multi-model support, complex graph-based workflows, built-in RAG, or you are already invested in the LangChain ecosystem.

**Choose Agent SDK when:** You are committed to Claude, want built-in tool execution, need Claude Code parity, or want simpler setup for file/code/shell tasks.

### vs. CrewAI

| Aspect | Agent SDK | CrewAI |
|--------|-----------|--------|
| **Multi-agent pattern** | Subagents (parent delegates) | Crews (role-based teams) |
| **Agent definition** | Programmatic (`AgentDefinition`) | Role, goal, backstory |
| **Task routing** | Claude decides via description | Explicit task assignment |
| **Model support** | Claude only | Multi-model |
| **Built-in tools** | Yes (comprehensive) | Minimal |
| **Complexity** | Lower | Medium |
| **Best for** | Code/automation tasks | Business process automation |

**Choose CrewAI when:** You want role-based multi-agent teams, multi-model support, or business-process-style orchestration.

**Choose Agent SDK when:** You want tight Claude integration, built-in code tools, or simpler subagent delegation.

### vs. Microsoft AutoGen

| Aspect | Agent SDK | AutoGen |
|--------|-----------|---------|
| **Architecture** | Parent-subagent tree | Conversable agent network |
| **Communication** | Tool calls (parent -> child) | Multi-agent chat |
| **Human-in-loop** | Hooks, canUseTool, AskUserQuestion | Built-in human proxy |
| **Model support** | Claude only | Multi-model |
| **Concurrency** | Event-driven, async | Async, multi-agent |
| **Code execution** | Built-in (sandboxed) | Docker-based sandbox |
| **Best for** | Autonomous coding/ops | Research, complex multi-agent |

**Choose AutoGen when:** You need complex multi-agent conversation patterns, research-grade flexibility, or multi-model agent networks.

**Choose Agent SDK when:** You want production-ready tool execution, session management, and a simpler mental model.

<!-- level:intermediate -->
## Detailed Tradeoff Analysis

### Tradeoff: Claude Lock-In

**Pro:** Deep integration means you get the best possible Claude experience. The SDK uses the same binary as Claude Code, so you get immediate access to every new Claude capability.

**Con:** You cannot switch to a different model provider without rewriting your agent logic. If Claude's API has downtime, your agents are down.

**Mitigation:**
- Use the `fallbackModel` option for within-Claude resilience
- The Bedrock/Vertex/Azure providers give you alternative infrastructure
- Keep your business logic separate from agent invocations

### Tradeoff: Child Process Architecture

**Pro:** Isolation means tool crashes do not crash your app. The agent process can be containerized or run remotely.

**Con:** There is overhead in spawning a process, and communication adds latency. You cannot directly call into the agent process's runtime -- it is a separate binary.

**Mitigation:**
- The process is reused within a session
- The V2 interface reduces per-turn overhead
- In-process MCP servers (`createSdkMcpServer`) avoid extra processes for custom tools

### Tradeoff: Opinionated Tool Set

**Pro:** Built-in tools (Read, Write, Edit, Bash, Glob, Grep) work immediately without configuration. They are battle-tested from Claude Code.

**Con:** You cannot customize the behavior of built-in tools (e.g., changing how `Read` works). You can only add new tools via MCP, not replace built-in ones.

**Mitigation:**
- Use `disallowedTools` to block built-in tools you do not want
- Use `tools` to control which built-ins are in context
- PreToolUse hooks can modify tool inputs before execution
- Custom MCP tools can wrap built-in tools with different behavior

### Tradeoff: Session Persistence

**Pro:** Sessions persist to disk automatically, enabling resume, fork, and audit trails.

**Con:** Disk I/O for every message, JSONL files can grow large, and sessions accumulate over time.

**Mitigation:**
- Set `persistSession: false` for one-off tasks
- Sessions auto-cleanup after `cleanupPeriodDays` (default 30 days)
- Use `listSessions()` to manage old sessions

### Tradeoff: Permission System Complexity

**Pro:** Layered permissions (disallowedTools -> allowedTools -> permissionMode -> canUseTool -> hooks) provide defense in depth.

**Con:** The evaluation order can be confusing. It is easy to misconfigure and either over-permit or over-deny.

**Mitigation:**
- Start with `dontAsk` mode (deny by default) and add allowedTools explicitly
- Use the `permission_denials` field in result messages to debug
- Test permission configurations with non-destructive prompts first

### Tradeoff: Rapid Release Cadence

**Pro:** New features and bug fixes ship quickly (71+ releases). You get improvements fast.

**Con:** APIs may change between versions. The V2 interface is explicitly marked `unstable`. Migration effort can accumulate.

**Mitigation:**
- Pin specific versions in package.json
- Read the CHANGELOG before upgrading
- The migration guide documents breaking changes

<!-- level:advanced -->
## Architectural Comparison

### Agent Loop Architectures

```
Agent SDK (Linear Agent Loop):
  User Prompt -> Think -> Act -> Observe -> Think -> Act -> ... -> Result

LangGraph (Graph-Based):
  Start -> Node A -> [Condition] -> Node B -> Node C -> End
                        |
                        +-> Node D -> Node E -> End

CrewAI (Role-Based Crews):
  Manager -> Researcher -> Writer -> Editor -> (sequential or parallel)

AutoGen (Multi-Agent Chat):
  Agent A <-> Agent B <-> Agent C <-> Human (conversational)
```

### Tool Execution Models

```
Agent SDK:
  Claude -> tool_use block -> SDK executes tool -> tool_result -> Claude
  (tools run in agent subprocess, managed by SDK)

LangChain:
  LLM -> tool call -> Your code executes tool -> result -> LLM
  (you implement the tool executor)

CrewAI:
  Agent -> tool call -> CrewAI executes tool -> result -> Agent
  (tools are Python functions or LangChain tools)

AutoGen:
  Agent -> code block -> Code executor runs in Docker -> result -> Agent
  (code-centric execution model)
```

### When Framework Maturity Matters

| Framework | First Release | GitHub Stars | NPM/PyPI Downloads | Production Users |
|-----------|--------------|-------------|-------------------|-----------------|
| LangChain | Oct 2022 | ~100K | Very high | Widespread |
| AutoGen | Sep 2023 | ~40K | High | Growing |
| CrewAI | Dec 2023 | ~25K | Medium | Growing |
| Agent SDK | Oct 2025 | ~1.2K | Growing | 1.1K+ projects |

The Agent SDK is the newest entrant but benefits from being built by the same team that builds Claude. It is not a wrapper around an API -- it is an extension of the Claude Code product.

### Cost Comparison

| Framework | LLM Costs | Infrastructure | Additional Costs |
|-----------|-----------|---------------|-----------------|
| Agent SDK | Claude API tokens | Node.js process | None (no orchestration fees) |
| LangChain | Varies by provider | Python/Node process | LangSmith (optional, paid) |
| CrewAI | Varies by provider | Python process | CrewAI Enterprise (optional) |
| AutoGen | Varies by provider | Python process + Docker | AutoGen Studio (free) |

All frameworks charge based on the underlying LLM's token pricing. The Agent SDK has no additional orchestration fees -- you pay only for Claude API usage.

### Decision Matrix

| Your Priority | Best Choice | Why |
|---------------|------------|-----|
| Fastest time to working agent | **Agent SDK** | Built-in tools, no setup needed |
| Multi-model flexibility | **LangChain/LangGraph** | Broad provider support |
| Role-based team patterns | **CrewAI** | Natural crew metaphor |
| Research/academic agents | **AutoGen** | Flexible conversation patterns |
| Code-centric automation | **Agent SDK** | Claude Code parity |
| Enterprise RAG pipeline | **LangChain** | Mature RAG ecosystem |
| TypeScript-first | **Agent SDK** or **Mastra** | Native TS support |
| Python-first complex graphs | **LangGraph** | Mature graph framework |
| Minimal abstraction | **Anthropic Client SDK** | Direct API, full control |

### Future Trajectory

The Agent SDK is on a rapid development trajectory. Key signals:

1. **V2 Interface** -- Simpler session management is being developed
2. **MCP Ecosystem Growth** -- Hundreds of MCP servers available, with the ecosystem growing
3. **Multi-Cloud Support** -- Bedrock, Vertex, and Azure integration
4. **Plugin System** -- Extensibility beyond MCP
5. **Background Tasks** -- Concurrent subagent execution
6. **Tool Search** -- Scaling to hundreds of tools efficiently

The main risk is vendor lock-in to Claude. The main advantage is that no other framework gives you this level of tool execution out of the box with this little configuration.
