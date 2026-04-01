# Architecture & Internals

<!-- level:beginner -->
## High-Level Architecture

The Anthropic Agent SDK has a layered architecture with three main components:

### 1. Your Application Layer
This is your TypeScript/JavaScript code. You call `query()` or create a session, provide a prompt and options, and consume the streamed messages.

### 2. The SDK Layer
The `@anthropic-ai/claude-agent-sdk` npm package. It manages:
- Spawning and communicating with the agent process
- Serializing/deserializing messages
- Session persistence
- Hook execution
- Permission evaluation

### 3. The Agent Process
A separate Node.js process running the Claude Code binary. This is where the real work happens:
- The agent loop (think-act-observe cycle)
- Tool execution (file operations, bash commands, web requests)
- Claude API calls
- MCP server connections

```
+-------------------+
| Your Application  |  <-- You write this
+-------------------+
        |
        | query() / createSession()
        v
+-------------------+
|   SDK Library     |  <-- @anthropic-ai/claude-agent-sdk
| - Message routing |
| - Hook dispatch   |
| - Permission eval |
| - Session mgmt    |
+-------------------+
        |
        | JSON-RPC over stdin/stdout
        v
+-------------------+
| Agent Process     |  <-- Claude Code binary (child process)
| - Agent loop      |
| - Tool execution  |
| - API calls       |
| - MCP connections |
+-------------------+
        |
        | HTTPS
        v
+-------------------+
| Claude API        |  <-- Anthropic's servers
+-------------------+
```

### Why a Separate Process?

The agent runs in a child process for several reasons:
- **Isolation**: A crashed tool does not crash your application
- **Security**: Tool execution is sandboxed
- **Portability**: The same binary works across CLI and SDK
- **Flexibility**: You can run the agent process in a VM, container, or remote machine

## Message Flow

When you call `query({ prompt: "Fix the bug" })`, here is what happens:

1. SDK spawns the Claude Code child process
2. SDK sends your prompt to the child process
3. Child process calls Claude API with the prompt and available tools
4. Claude responds with a `tool_use` block (e.g., "I want to read auth.py")
5. Child process executes the tool and feeds the result back to Claude
6. Claude sees the file contents, thinks, and may call another tool
7. Steps 4-6 repeat until Claude is done
8. Each step produces `SDKMessage` objects that stream back to your `for await` loop
9. A `result` message signals the task is complete

<!-- level:intermediate -->
## The Agent Loop in Detail

### Loop States

The agent loop inside the child process follows this state machine:

```
                    +----------------+
                    |   INITIALIZE   |
                    | - Load config  |
                    | - Connect MCP  |
                    | - Emit init msg|
                    +-------+--------+
                            |
                            v
                    +----------------+
             +----->|   API CALL     |
             |      | - Send context |
             |      | - Stream resp  |
             |      +-------+--------+
             |              |
             |              v
             |      +----------------+
             |      | PROCESS RESP   |
             |      | - Text? Emit   |
             |      | - tool_use?    |
             |      +--+-----+------+
             |         |     |
             |    (text)|    |(tool_use)
             |         |    v
             |         | +-----------+
             |         | | EXECUTE   |
             |         | | TOOL      |
             |         | | - Hooks   |
             |         | | - Perms   |
             |         | | - Run     |
             |         | +-----+-----+
             |         |       |
             |         |       v
             |         | +-----------+
             |         | | OBSERVE   |
             |         | | - Feed    |
             |         | |   result  |
             |         | +-----+-----+
             |         |       |
             |         +---+---+
             |             |
             +-------------+ (more work needed)
                           |
                           v (stop_reason = end_turn)
                    +----------------+
                    |    RESULT      |
                    | - Emit result  |
                    | - Cleanup      |
                    +----------------+
```

### Tool Execution Pipeline

When Claude wants to use a tool, the following pipeline executes:

1. **PreToolUse Hooks** -- Your hook callbacks run first. They can approve, deny, or modify the tool input.
2. **Permission Check** -- `disallowedTools` -> `allowedTools` -> `permissionMode` -> `canUseTool`
3. **Tool Execution** -- The built-in tool or MCP tool handler runs
4. **PostToolUse Hooks** -- Your hooks run with the tool result, can add context
5. **Result Injection** -- The tool result is added to the conversation for Claude to observe

### MCP Server Architecture

MCP (Model Context Protocol) servers extend the agent with external tools. The SDK supports four transport types:

```typescript
type McpServerConfig =
  | McpStdioServerConfig          // Local process via stdin/stdout
  | McpSSEServerConfig            // Server-Sent Events (streaming)
  | McpHttpServerConfig           // HTTP (request-response)
  | McpSdkServerConfigWithInstance; // In-process (same Node.js process)
```

**Stdio servers** spawn a child process and communicate via stdin/stdout:
```typescript
mcpServers: {
  github: {
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-github"],
    env: { GITHUB_TOKEN: process.env.GITHUB_TOKEN }
  }
}
```

**In-process SDK servers** run inside your application -- no subprocess needed:
```typescript
import { tool, createSdkMcpServer } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";

const myTool = tool(
  "lookup_user",
  "Look up a user by email",
  { email: z.string().email() },
  async (args) => {
    const user = await db.users.findByEmail(args.email);
    return { content: [{ type: "text", text: JSON.stringify(user) }] };
  }
);

const myServer = createSdkMcpServer({
  name: "my-app",
  tools: [myTool]
});
```

### Subagent Architecture

Subagents are nested agent loops with their own context windows:

```
Main Agent Context
  |
  +-- [Read, Grep, Glob, Agent] (available tools)
  |
  +-- Claude decides to delegate to "code-reviewer"
  |
  +-- Agent Tool Call:
        |
        +-- Spawns subagent "code-reviewer"
        |     |
        |     +-- Fresh context window
        |     +-- Own system prompt
        |     +-- Restricted tools: [Read, Grep, Glob]
        |     +-- Runs its own agent loop
        |     +-- Returns final message
        |
        +-- Subagent result becomes tool_result in main context
```

Key architectural details:
- Subagents **cannot** spawn their own subagents (no recursive nesting)
- Subagent transcripts are stored in separate files
- The parent only sees the subagent's final message, not intermediate steps
- Multiple subagents can run concurrently for parallel workloads

<!-- level:advanced -->
## Inter-Process Communication Protocol

The SDK communicates with the agent process using a JSON-RPC-like protocol over stdin/stdout of the child process:

### Outbound Messages (SDK to Agent Process)

```typescript
// Initialize the agent
{ type: "control", action: "initialize", options: { ... } }

// Send a prompt
{ type: "user", message: { role: "user", content: [...] } }

// Control commands
{ type: "control", action: "interrupt" }
{ type: "control", action: "set_permission_mode", mode: "acceptEdits" }
{ type: "control", action: "set_model", model: "claude-opus-4-6" }
{ type: "control", action: "set_mcp_servers", servers: { ... } }
```

### Inbound Messages (Agent Process to SDK)

Each line of stdout is a JSON-encoded `SDKMessage`. The SDK parses these and yields them through the async generator.

### Custom Process Spawning

For advanced deployment scenarios, you can override how the agent process is spawned:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Analyze the codebase",
  options: {
    spawnClaudeCodeProcess: (options) => {
      // Run Claude Code in a Docker container
      const proc = spawn("docker", [
        "run", "--rm", "-i",
        "-v", `${process.cwd()}:/workspace`,
        "claude-code:latest",
        ...options.args
      ]);
      return {
        stdin: proc.stdin,
        stdout: proc.stdout,
        stderr: proc.stderr,
        on: proc.on.bind(proc),
        kill: proc.kill.bind(proc)
      };
    }
  }
})) {
  console.log(message);
}
```

## Hook Execution Architecture

Hooks are executed synchronously in the agent loop, meaning the agent pauses while hooks run:

```
Agent Loop Step
  |
  v
Fire PreToolUse Event
  |
  +-- Collect registered hooks for this event
  |     |
  |     +-- Filter by matcher (regex against tool name)
  |     +-- Execute hooks in array order
  |     +-- Merge results (deny > ask > allow)
  |
  v
If denied: skip tool execution, return denial to Claude
If allowed: execute tool
  |
  v
Fire PostToolUse Event
  |
  +-- Execute PostToolUse hooks (same filtering process)
  |
  v
Continue agent loop
```

### Hook Input/Output Contract

All hooks receive a `BaseHookInput` with common fields:

```typescript
type BaseHookInput = {
  session_id: string;
  transcript_path: string;
  cwd: string;
  permission_mode?: string;
  agent_id?: string;
  agent_type?: string;
};
```

Hooks return a `HookJSONOutput` that can be synchronous or asynchronous:

```typescript
// Synchronous: agent waits for result
{ continue?: boolean; suppressOutput?: boolean; decision?: "approve" | "block";
  systemMessage?: string; hookSpecificOutput?: { ... } }

// Asynchronous: agent continues immediately (for side effects only)
{ async: true; asyncTimeout?: 30000 }
```

### Permission System Implementation

The permission evaluation is a pipeline with short-circuit logic:

```typescript
// Pseudocode of internal permission evaluation
function evaluatePermission(toolName, input, options) {
  // 1. Disallow list (always first, always wins)
  if (options.disallowedTools?.some(pattern => matches(toolName, pattern))) {
    return { behavior: "deny" };
  }

  // 2. Allow list
  if (options.allowedTools?.some(pattern => matches(toolName, pattern))) {
    return { behavior: "allow" };
  }

  // 3. Permission mode
  switch (options.permissionMode) {
    case "bypassPermissions":
      return { behavior: "allow" };
    case "acceptEdits":
      if (isFileEditTool(toolName)) return { behavior: "allow" };
      break;
    case "dontAsk":
      return { behavior: "deny", message: "Not pre-approved" };
    case "plan":
      return { behavior: "deny", message: "Plan mode" };
  }

  // 4. Custom callback
  if (options.canUseTool) {
    return options.canUseTool(toolName, input, { signal, ... });
  }

  // 5. Default: deny
  return { behavior: "deny", message: "No permission rule matched" };
}
```

### Session Storage Format

Sessions are stored as JSONL (JSON Lines) files in `~/.claude/sessions/`:

```
~/.claude/
  sessions/
    <project-hash>/
      <session-uuid>.jsonl
```

Each line is a complete message object. The SDK's `listSessions()`, `getSessionMessages()`, and related functions read these files directly.

Session metadata (title, tag, branch, last modified time) is derived from the JSONL content and file system attributes, making sessions lightweight and inspectable with standard Unix tools.

### Tool Search Architecture

When many MCP tools are configured, loading all tool definitions into the context window wastes tokens. The SDK implements a tool search mechanism:

1. Tool definitions are withheld from the initial context
2. Claude is given a `ToolSearch` meta-tool instead
3. When Claude needs a specific capability, it calls `ToolSearch` with a query
4. The SDK returns matching tool definitions
5. Claude can then call the discovered tools

This lazy-loading approach scales to hundreds of MCP tools without context window pressure. Tool search is enabled by default for large tool sets.
