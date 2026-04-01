# Core Concepts

<!-- level:beginner -->
## The Agent Loop

The most fundamental concept in the Agent SDK is the **agent loop**. When you give Claude a task, it does not simply generate text. It enters a cycle:

1. **Think** -- Claude analyzes the task and decides what to do
2. **Act** -- Claude calls a tool (read a file, run a command, etc.)
3. **Observe** -- Claude examines the tool's output
4. **Repeat** -- Claude decides whether more work is needed or the task is complete

This loop continues until Claude determines the task is finished, encounters an error, or hits a configured limit (like `maxTurns` or `maxBudgetUsd`).

```
    +--------+
    | Think  |<---------+
    +--------+          |
        |               |
        v               |
    +--------+          |
    |  Act   |   (tool  |
    +--------+   result)|
        |               |
        v               |
    +--------+          |
    |Observe |---------+
    +--------+
        |
        v (when done)
    +--------+
    | Result |
    +--------+
```

### A Simple Example

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "What files are in this directory?",
  options: { allowedTools: ["Bash", "Glob"] }
})) {
  if ("result" in message) console.log(message.result);
}
```

In this example:
- You provide a prompt ("What files are in this directory?")
- You allow two tools: `Bash` and `Glob`
- Claude thinks about the task, decides to use `Glob`, executes it, reads the result, and returns a summary
- You receive messages as they stream in via the `for await` loop

## Tools

Tools are the capabilities you give your agent. Without tools, Claude can only think and respond with text. With tools, Claude can interact with the world.

### Built-in Tools

| Tool | What It Does | Example |
|------|-------------|---------|
| **Read** | Read any file | Reading source code, config files, PDFs, images |
| **Write** | Create new files | Generating scripts, configs, reports |
| **Edit** | Modify existing files with precise replacements | Fixing bugs, updating settings |
| **Bash** | Run terminal commands | `git status`, `npm test`, `ls -la` |
| **Glob** | Find files by pattern | `**/*.ts`, `src/**/*.py` |
| **Grep** | Search file contents with regex | Finding function definitions, TODOs |
| **WebSearch** | Search the internet | Looking up documentation, current events |
| **WebFetch** | Fetch and parse web pages | Reading API docs, downloading data |
| **Agent** | Spawn a subagent | Delegating subtasks to specialized agents |
| **AskUserQuestion** | Ask the user a question | Clarifying requirements |

### Tool Safety

Tools are not automatically approved. You control access through:
- **`allowedTools`**: Pre-approve specific tools
- **`disallowedTools`**: Explicitly block specific tools
- **`permissionMode`**: Set broad permission policies
- **`canUseTool`**: Custom callback for fine-grained control

## Messages

When you iterate over `query()`, each iteration yields an `SDKMessage`. These come in several types:

- **`system`** (subtype `init`) -- First message, contains session info
- **`assistant`** -- Claude's thinking and tool calls
- **`user`** -- Tool results fed back to Claude
- **`result`** -- Final outcome of the task (success or error)

```typescript
for await (const message of query({ prompt: "...", options })) {
  switch (message.type) {
    case "system":
      // Session initialized
      break;
    case "assistant":
      // Claude is thinking or calling a tool
      break;
    case "result":
      // Task is complete
      if (message.subtype === "success") {
        console.log(message.result);
      }
      break;
  }
}
```

<!-- level:intermediate -->
## Permissions Deep Dive

The permission system is layered and follows a strict evaluation order:

### Permission Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| `default` | Falls through to `canUseTool` callback | Custom approval flows |
| `acceptEdits` | Auto-approves file edits, asks for everything else | Trusted dev workflows |
| `dontAsk` | Denies anything not in `allowedTools` (TS only) | Locked-down headless agents |
| `bypassPermissions` | Approves everything without prompts | Sandboxed CI environments |
| `plan` | Planning mode, no tool execution | Reviewing what an agent would do |

### Evaluation Order

```
1. disallowedTools  -->  DENY (always checked first, overrides everything)
2. allowedTools     -->  ALLOW (if tool matches)
3. permissionMode   -->  Mode-specific logic
4. canUseTool       -->  Custom callback (if permissionMode is "default")
```

### The `canUseTool` Callback

For maximum control, implement a custom permission function:

```typescript
import { query, PermissionResult } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Refactor the codebase",
  options: {
    canUseTool: async (
      toolName: string,
      input: Record<string, unknown>,
      options
    ): Promise<PermissionResult> => {
      // Allow all read operations
      if (["Read", "Glob", "Grep"].includes(toolName)) {
        return { behavior: "allow" };
      }

      // Block dangerous commands
      if (toolName === "Bash") {
        const cmd = input.command as string;
        if (cmd.includes("rm -rf") || cmd.includes("sudo")) {
          return { behavior: "deny", message: "Dangerous command blocked" };
        }
      }

      // Allow everything else
      return { behavior: "allow" };
    }
  }
})) {
  // ...
}
```

## Sessions

Sessions give your agent persistent memory across multiple interactions.

### Session Lifecycle

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

let sessionId: string | undefined;

// First interaction: capture session ID
for await (const message of query({
  prompt: "Read the authentication module",
  options: { allowedTools: ["Read", "Glob"] }
})) {
  if (message.type === "system" && message.subtype === "init") {
    sessionId = message.session_id;
  }
}

// Second interaction: resume with full context
for await (const message of query({
  prompt: "Now find all places that call it",
  options: { resume: sessionId }
})) {
  if ("result" in message) console.log(message.result);
}
```

### Session Operations

| Function | Purpose |
|----------|---------|
| `listSessions()` | List past sessions with metadata |
| `getSessionMessages()` | Read the transcript of a session |
| `getSessionInfo()` | Get metadata for a single session |
| `renameSession()` | Set a custom title |
| `tagSession()` | Tag or untag a session |

### Session Persistence

Sessions are stored as JSONL files on disk by default. You can:
- **Disable persistence**: `persistSession: false`
- **Fork a session**: `forkSession: true` with `resume: sessionId`
- **Resume at a specific point**: `resumeSessionAt: messageUUID`

## Subagents

Subagents are specialized agent instances your main agent can spawn for focused subtasks. They provide:

- **Context Isolation** -- Subagent conversations do not pollute the main context
- **Parallelization** -- Multiple subagents can run concurrently
- **Specialized Instructions** -- Each subagent has its own system prompt and tools
- **Tool Restrictions** -- Limit what each subagent can do

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Review this codebase for security and style issues",
  options: {
    allowedTools: ["Read", "Glob", "Grep", "Agent"],
    agents: {
      "security-reviewer": {
        description: "Security vulnerability scanner",
        prompt: "You are a security expert. Find vulnerabilities.",
        tools: ["Read", "Grep", "Glob"],
        model: "opus"
      },
      "style-checker": {
        description: "Code style and convention checker",
        prompt: "You are a style expert. Check coding conventions.",
        tools: ["Read", "Grep", "Glob"],
        model: "sonnet"
      }
    }
  }
})) {
  if ("result" in message) console.log(message.result);
}
```

<!-- level:advanced -->
## The Message Type System

The SDK defines a rich union type for messages. Understanding this is critical for building robust integrations:

```typescript
type SDKMessage =
  | SDKAssistantMessage      // Claude's thinking and tool calls
  | SDKUserMessage           // Tool results and user input
  | SDKUserMessageReplay     // Replayed messages during session resume
  | SDKResultMessage         // Final task outcome
  | SDKSystemMessage         // Session init info
  | SDKPartialAssistantMessage  // Streaming deltas (opt-in)
  | SDKCompactBoundaryMessage   // Context compaction markers
  | SDKStatusMessage         // Status updates
  | SDKLocalCommandOutputMessage // Slash command output
  | SDKHookStartedMessage    // Hook execution started
  | SDKHookProgressMessage   // Hook progress updates
  | SDKHookResponseMessage   // Hook execution results
  | SDKToolProgressMessage   // Tool execution progress
  | SDKAuthStatusMessage     // Authentication status
  | SDKTaskNotificationMessage  // Background task notifications
  | SDKTaskStartedMessage    // Background task started
  | SDKTaskProgressMessage   // Background task progress
  | SDKFilesPersistedEvent   // File checkpoint events
  | SDKToolUseSummaryMessage // Tool usage summary
  | SDKRateLimitEvent        // Rate limit notifications
  | SDKPromptSuggestionMessage; // Suggested next prompts
```

### SDKResultMessage Subtypes

The result message indicates how the agent loop terminated:

```typescript
type SDKResultMessage =
  | { subtype: "success"; result: string; total_cost_usd: number; usage: NonNullableUsage; ... }
  | { subtype: "error_max_turns"; errors: string[]; ... }
  | { subtype: "error_during_execution"; errors: string[]; ... }
  | { subtype: "error_max_budget_usd"; errors: string[]; ... }
  | { subtype: "error_max_structured_output_retries"; errors: string[]; ... };
```

Success results include `total_cost_usd`, `num_turns`, `duration_ms`, `duration_api_ms`, and per-model usage breakdowns via `modelUsage`.

### Query Object Methods

The `Query` object returned by `query()` is more than an async generator. It exposes control methods:

```typescript
interface Query extends AsyncGenerator<SDKMessage, void> {
  // Lifecycle control
  interrupt(): Promise<void>;           // Interrupt current operation
  close(): void;                        // Terminate and cleanup

  // Runtime reconfiguration
  setPermissionMode(mode: PermissionMode): Promise<void>;
  setModel(model?: string): Promise<void>;
  setMcpServers(servers: Record<string, McpServerConfig>): Promise<McpSetServersResult>;

  // Introspection
  initializationResult(): Promise<SDKControlInitializeResponse>;
  supportedCommands(): Promise<SlashCommand[]>;
  supportedModels(): Promise<ModelInfo[]>;
  supportedAgents(): Promise<AgentInfo[]>;
  mcpServerStatus(): Promise<McpServerStatus[]>;
  accountInfo(): Promise<AccountInfo>;

  // File management
  rewindFiles(userMessageId: string, options?: { dryRun?: boolean }): Promise<RewindFilesResult>;

  // Multi-turn
  streamInput(stream: AsyncIterable<SDKUserMessage>): Promise<void>;

  // Background tasks
  stopTask(taskId: string): Promise<void>;
}
```

### Context Compaction

When conversations grow long, the SDK automatically compacts the context to fit within the model's context window. This is signaled via `SDKCompactBoundaryMessage`:

```typescript
type SDKCompactBoundaryMessage = {
  type: "system";
  subtype: "compact_boundary";
  compact_metadata: {
    trigger: "manual" | "auto";
    pre_tokens: number;
  };
};
```

You can hook into this process via `PreCompact` hooks to archive the full transcript or inject custom compaction instructions.

### Thinking Configuration

Control Claude's extended thinking behavior:

```typescript
type ThinkingConfig =
  | { type: "disabled" }                    // No extended thinking
  | { type: "enabled"; budget_tokens: number }  // Fixed token budget
  | { type: "adaptive" };                   // SDK manages budget (default for supported models)
```

The `effort` option (`low` | `medium` | `high` | `max`) works with adaptive thinking to guide depth. Higher effort means Claude will think longer before acting.
