# Metadata & Overview

<!-- level:beginner -->
## What is the Anthropic Agent SDK?

The **Anthropic Agent SDK** (TypeScript) -- published as `@anthropic-ai/claude-agent-sdk` on npm -- is a library for building autonomous AI agents powered by Claude. It gives you the same tools, agent loop, and context management that power Claude Code, packaged as a library you can embed in your own applications.

Think of it this way: if the Anthropic SDK (`@anthropic-ai/sdk`) is a telephone that lets you talk to Claude, the Agent SDK is a complete robotic assistant -- Claude with hands. It can read files, run terminal commands, search the web, edit code, and orchestrate complex multi-step workflows without you implementing any of the tool execution logic.

### Key Facts at a Glance

| Property | Value |
|----------|-------|
| **NPM Package** | `@anthropic-ai/claude-agent-sdk` |
| **GitHub Repository** | `anthropics/claude-agent-sdk-typescript` |
| **Latest Version** | v0.2.87 (as of March 2026) |
| **Minimum Node.js** | 18+ |
| **Language** | TypeScript / JavaScript |
| **License** | Anthropic Commercial Terms of Service |
| **Stars** | ~1,200 |
| **Used by** | 1,100+ projects |
| **Python Equivalent** | `claude-agent-sdk` (pip) |

### One-Sentence Summary

The Agent SDK wraps Claude's intelligence with built-in tool execution, turning a chat API into an autonomous agent that can read, write, search, and execute -- all with a single function call.

### History and Naming

The SDK was originally called the "Claude Code SDK" and was renamed to "Claude Agent SDK" to reflect its broader applicability beyond coding tasks. If you encounter references to `@anthropic-ai/claude-code-sdk` in older documentation, that is the same product under its former name.

<!-- level:intermediate -->
## Technical Overview

The Agent SDK sits between your application and the Claude API, managing the entire agent lifecycle:

```
Your Application
      |
      v
  Agent SDK (query / ClaudeSDKClient)
      |
      +-- Agent Loop (think -> tool_use -> observe -> repeat)
      |       |
      |       +-- Built-in Tools (Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch)
      |       +-- MCP Tools (custom + third-party via Model Context Protocol)
      |       +-- Subagents (specialized delegate agents)
      |
      +-- Session Management (persistence, resume, fork)
      +-- Permission System (allowedTools, hooks, canUseTool)
      +-- Hooks (PreToolUse, PostToolUse, Stop, SessionStart, ...)
      |
      v
  Claude API (Messages API with tool_use)
```

### Two Primary Interfaces

1. **`query()`** -- A standalone function that returns an async generator. Call it, iterate over messages, and you are done. Best for single-shot tasks and simple integrations.

2. **V2 Session Interface (Preview)** -- `unstable_v2_createSession()` provides a class-based session with explicit `send()` and `stream()` methods, making multi-turn conversations simpler without managing generator state.

### Authentication

The SDK supports multiple authentication methods:

- **Anthropic API Key** -- `ANTHROPIC_API_KEY` environment variable (primary)
- **Amazon Bedrock** -- Set `CLAUDE_CODE_USE_BEDROCK=1` with AWS credentials
- **Google Vertex AI** -- Set `CLAUDE_CODE_USE_VERTEX=1` with GCP credentials
- **Microsoft Azure AI Foundry** -- Set `CLAUDE_CODE_USE_FOUNDRY=1` with Azure credentials

### Versioning and Release Cadence

The SDK follows rapid-release versioning. With 71+ releases since inception, new versions ship frequently (multiple per week), often aligned with Claude Code CLI updates. The CHANGELOG is maintained in the GitHub repository.

<!-- level:advanced -->
## Architectural Position and Design Philosophy

### Design Principles

The Agent SDK embodies several deliberate architectural choices:

1. **Same Runtime as Claude Code** -- The SDK literally spawns a Claude Code process under the hood. Your agent runs the same binary that powers the Claude Code CLI. This ensures parity: any capability in Claude Code is available in the SDK.

2. **Tool Execution, Not Tool Description** -- Unlike the Anthropic Client SDK where you describe tools and implement execution yourself, the Agent SDK executes tools directly. You define *what* Claude can do (via `allowedTools`), not *how* it does it.

3. **Streaming-First** -- The `query()` function returns an `AsyncGenerator<SDKMessage, void>`. Every interaction is streaming by default -- you consume messages as they arrive rather than waiting for a complete response.

4. **Security by Default** -- Tools are not auto-approved. The permission system requires explicit opt-in via `allowedTools`, `permissionMode`, or `canUseTool` callbacks. This prevents agents from performing dangerous operations without oversight.

5. **Session Persistence** -- Sessions are persisted to disk by default (JSONL format), enabling resume, fork, and inspection of past conversations. This is a departure from stateless API usage.

### Process Architecture

The SDK communicates with a subprocess via JSON-RPC over stdin/stdout:

```
Node.js Process (your app)
    |
    +-- @anthropic-ai/claude-agent-sdk
           |
           +-- Spawns child process: claude-code binary
                  |
                  +-- Agent loop runs inside this process
                  +-- Tool execution happens here
                  +-- Claude API calls originate here
                  +-- MCP server connections managed here
```

This architecture means:
- Tool execution is sandboxed in the child process
- The SDK itself is a thin communication layer
- Crash isolation: a failed tool does not crash your application
- The `spawnClaudeCodeProcess` option lets you run the agent process in a VM, container, or remote environment

### SDK vs. Client SDK: The Real Difference

```typescript
// Client SDK: You build the loop
let response = await client.messages.create({ ...params });
while (response.stop_reason === "tool_use") {
  const result = yourToolExecutor(response.tool_use);
  response = await client.messages.create({ tool_result: result, ...params });
}

// Agent SDK: The loop is built for you
for await (const message of query({ prompt: "Fix the bug in auth.py" })) {
  console.log(message);
}
```

The Client SDK gives you a message-level API. The Agent SDK gives you a task-level API. You describe what you want done, and the SDK handles the entire think-act-observe cycle.
