# Advanced Topics

<!-- level:beginner -->
## What Makes Advanced Usage "Advanced"?

The Agent SDK is designed to be simple for basic tasks but supports sophisticated patterns for production systems. Advanced topics include:

- **Streaming input** for interactive, multi-turn applications
- **Custom process spawning** for running agents in containers or remote machines
- **Hook orchestration** for building complex guardrail systems
- **File checkpointing** for reverting agent-made changes
- **The V2 interface** for simplified session management

Most developers start with the basic `query()` pattern and add advanced features as their requirements grow.

<!-- level:intermediate -->
## Streaming Input Mode

For applications where the user sends multiple messages in a single session (chat UIs, REPLs), use an async iterable as the prompt:

```typescript
import { query, SDKUserMessage } from "@anthropic-ai/claude-agent-sdk";

// Create a controllable input stream
class MessageQueue {
  private resolvers: ((msg: SDKUserMessage) => void)[] = [];
  private messages: SDKUserMessage[] = [];
  private done = false;

  push(text: string) {
    const msg: SDKUserMessage = {
      type: "user",
      session_id: "",
      message: { role: "user", content: [{ type: "text", text }] },
      parent_tool_use_id: null
    };

    if (this.resolvers.length > 0) {
      this.resolvers.shift()!(msg);
    } else {
      this.messages.push(msg);
    }
  }

  close() { this.done = true; }

  async *[Symbol.asyncIterator](): AsyncIterator<SDKUserMessage> {
    while (!this.done) {
      if (this.messages.length > 0) {
        yield this.messages.shift()!;
      } else {
        yield await new Promise<SDKUserMessage>((resolve) => {
          this.resolvers.push(resolve);
        });
      }
    }
  }
}

const queue = new MessageQueue();

// Start the query with the streaming input
const q = query({
  prompt: queue,
  options: {
    allowedTools: ["Read", "Edit", "Glob", "Grep"],
    permissionMode: "acceptEdits"
  }
});

// Consume output in background
(async () => {
  for await (const message of q) {
    if (message.type === "assistant") {
      for (const block of message.message.content) {
        if (block.type === "text") process.stdout.write(block.text);
      }
    }
  }
})();

// Send messages whenever you want
queue.push("Read the authentication module");
// ... wait for response ...
queue.push("Now find all security issues");
// ... wait for response ...
queue.push("Fix the most critical one");
// ... when done ...
queue.close();
```

## The V2 Interface Deep Dive

The V2 interface (`unstable_v2_*`) provides a cleaner abstraction for multi-turn sessions:

### Session with All Options

```typescript
import { unstable_v2_createSession } from "@anthropic-ai/claude-agent-sdk";

await using session = unstable_v2_createSession({
  model: "claude-opus-4-6",
  // All standard options are available
  allowedTools: ["Read", "Edit", "Glob", "Grep"],
  permissionMode: "acceptEdits",
  systemPrompt: "You are a TypeScript expert.",
  maxTurns: 20,
  maxBudgetUsd: 1.0
});

// Each send/stream cycle is a turn
await session.send("What patterns does this codebase use?");
for await (const msg of session.stream()) {
  // Process messages
}

// Follow-up turns maintain context automatically
await session.send("Refactor the weakest pattern you found");
for await (const msg of session.stream()) {
  // Process messages
}
```

### Session Resume Across Processes

```typescript
import {
  unstable_v2_createSession,
  unstable_v2_resumeSession
} from "@anthropic-ai/claude-agent-sdk";

// Process 1: Create session and save ID
const session = unstable_v2_createSession({ model: "claude-opus-4-6" });
await session.send("Analyze the codebase");

let sessionId: string | undefined;
for await (const msg of session.stream()) {
  sessionId = msg.session_id;
}
session.close();

// Save sessionId to database, file, or pass to another process
console.log("Session ID:", sessionId);

// Process 2 (or later): Resume
await using resumed = unstable_v2_resumeSession(sessionId!, {
  model: "claude-opus-4-6"
});
await resumed.send("What did you find?");
for await (const msg of resumed.stream()) {
  // Full context from the original session is available
}
```

## File Checkpointing

Track and revert all file changes made by the agent:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

const q = query({
  prompt: "Refactor the entire auth module to use async/await",
  options: {
    allowedTools: ["Read", "Edit", "Glob", "Grep"],
    permissionMode: "acceptEdits",
    enableFileCheckpointing: true
  }
});

const checkpoints: string[] = [];

for await (const message of q) {
  // Track user message IDs as potential rewind points
  if (message.type === "user" && message.uuid) {
    checkpoints.push(message.uuid);
  }

  // If something goes wrong, revert to a checkpoint
  if (message.type === "result" && message.subtype !== "success") {
    if (checkpoints.length > 0) {
      // Preview what would change
      const preview = await q.rewindFiles(checkpoints[0], { dryRun: true });
      console.log("Would revert:", preview);

      // Actually revert
      const result = await q.rewindFiles(checkpoints[0]);
      console.log("Reverted:", result);
    }
  }
}
```

## Skills and Slash Commands

### Loading Skills

Skills are Markdown-defined capabilities in `.claude/skills/`:

```typescript
options: {
  settingSources: ["project"],  // Required to load skills
  systemPrompt: { type: "preset", preset: "claude_code" },
  // Skills from .claude/skills/*/SKILL.md are auto-loaded
}
```

### Subagents with Skills

```typescript
options: {
  agents: {
    "frontend-expert": {
      description: "Frontend development specialist",
      prompt: "You are a React and CSS expert.",
      tools: ["Read", "Edit", "Glob"],
      skills: ["react-patterns", "css-best-practices"]  // Load specific skills
    }
  }
}
```

<!-- level:advanced -->
## Hook Orchestration Patterns

### Permission Request Interception

The `PermissionRequest` hook lets you implement custom approval UI:

```typescript
import { query, HookCallback } from "@anthropic-ai/claude-agent-sdk";

const permissionHandler: HookCallback = async (input) => {
  if (input.hook_event_name !== "PermissionRequest") return {};

  const permInput = input as any;
  const toolName = permInput.tool_name;
  const toolInput = permInput.tool_input;

  // Implement custom approval logic
  // This could call an external API, prompt a Slack channel, etc.
  const approved = await customApprovalService.requestApproval({
    tool: toolName,
    input: toolInput,
    sessionId: input.session_id
  });

  return {
    hookSpecificOutput: {
      hookEventName: "PermissionRequest",
      decision: approved
        ? { behavior: "allow" }
        : { behavior: "deny", message: "Rejected by approval system" }
    }
  };
};

for await (const message of query({
  prompt: "Deploy to production",
  options: {
    allowedTools: ["Bash", "Read", "Glob"],
    hooks: {
      PermissionRequest: [{ hooks: [permissionHandler] }]
    }
  }
})) {
  // ...
}
```

### Session Lifecycle Hooks (TypeScript-only)

These hooks are exclusive to the TypeScript SDK:

```typescript
import { query, HookCallback } from "@anthropic-ai/claude-agent-sdk";

const sessionStart: HookCallback = async (input) => {
  if (input.hook_event_name !== "SessionStart") return {};
  const startInput = input as any;

  console.log(`Session started: ${input.session_id}`);
  console.log(`  Source: ${startInput.source}`);  // "startup" | "resume" | "clear" | "compact"
  console.log(`  Model: ${startInput.model}`);

  // Initialize telemetry, logging, etc.
  await telemetry.startSession(input.session_id);

  return {};
};

const sessionEnd: HookCallback = async (input) => {
  if (input.hook_event_name !== "SessionEnd") return {};
  const endInput = input as any;

  console.log(`Session ended: ${input.session_id}, reason: ${endInput.reason}`);

  // Cleanup resources
  await telemetry.endSession(input.session_id);

  return {};
};

const taskCompleted: HookCallback = async (input) => {
  if (input.hook_event_name !== "TaskCompleted") return {};
  const taskInput = input as any;

  console.log(`Task completed: ${taskInput.task_id}`);
  console.log(`  Subject: ${taskInput.task_subject}`);
  console.log(`  Team: ${taskInput.team_name}`);

  return {};
};

for await (const message of query({
  prompt: "Complex analysis task",
  options: {
    hooks: {
      SessionStart: [{ hooks: [sessionStart] }],
      SessionEnd: [{ hooks: [sessionEnd] }],
      TaskCompleted: [{ hooks: [taskCompleted] }]
    }
  }
})) {
  // ...
}
```

### Worktree Isolation for Subagents

Run subagents in isolated git worktrees:

```typescript
options: {
  agents: {
    "risky-refactor": {
      description: "Performs risky refactoring in an isolated worktree",
      prompt: "Refactor aggressively. This runs in an isolated worktree so changes can be discarded.",
      tools: ["Read", "Edit", "Write", "Bash", "Glob", "Grep"]
      // The Agent tool input supports isolation: "worktree"
    }
  }
}
```

When invoked, the agent tool supports the `isolation` parameter:

```typescript
// The AgentInput type supports worktree isolation
type AgentInput = {
  description: string;
  prompt: string;
  subagent_type: string;
  isolation?: "worktree";  // Run in a separate git worktree
  run_in_background?: boolean;
  max_turns?: number;
  // ...
};
```

### Background Tasks

Subagents can run in the background while the main agent continues:

```typescript
// The AgentInput supports background execution
type AgentInput = {
  // ...
  run_in_background?: boolean;  // Don't wait for completion
  // ...
};
```

Monitor and manage background tasks:

```typescript
for await (const message of q) {
  // Background task started
  if (message.type === "task_started") {
    console.log(`Background task: ${(message as any).task_id}`);
  }

  // Background task progress
  if (message.type === "task_progress") {
    console.log(`Task progress: ${(message as any).task_id}`);
  }

  // Background task notification
  if (message.type === "task_notification") {
    const taskMsg = message as any;
    console.log(`Task ${taskMsg.task_id}: ${taskMsg.message}`);
  }
}

// Stop a background task
await q.stopTask("task-uuid");
```

### Advanced Subagent Configuration

```typescript
import { query, AgentDefinition } from "@anthropic-ai/claude-agent-sdk";

const agents: Record<string, AgentDefinition> = {
  "security-scanner": {
    description: "Deep security analysis with access to vulnerability databases",
    prompt: `You are a security expert with deep knowledge of OWASP Top 10, CVE databases, and security best practices.

For each vulnerability found, provide:
1. CVE reference if applicable
2. CVSS score estimate
3. Reproduction steps
4. Remediation code`,
    tools: ["Read", "Grep", "Glob"],
    model: "opus",  // Most capable model for security analysis
    maxTurns: 30,   // Allow thorough analysis
    mcpServers: [
      // Reference parent's MCP servers by name
      "vulnerability-db",
      // Or define inline MCP servers
      {
        "cve-lookup": {
          command: "npx",
          args: ["-y", "cve-mcp-server"],
          env: { CVE_API_KEY: process.env.CVE_API_KEY! }
        }
      }
    ],
    disallowedTools: ["Bash", "Write", "Edit"],  // Read-only
    criticalSystemReminder_EXPERIMENTAL: "NEVER suggest disabling security features as a fix."
  }
};

for await (const message of query({
  prompt: "Run a comprehensive security audit of the entire codebase",
  options: {
    allowedTools: ["Read", "Glob", "Grep", "Agent"],
    agents,
    mcpServers: {
      "vulnerability-db": {
        type: "http",
        url: "https://vuln-db.internal/mcp"
      }
    }
  }
})) {
  if ("result" in message) console.log(message.result);
}
```

### Prompt Suggestions

Enable the SDK to suggest what the user might want to ask next:

```typescript
for await (const message of query({
  prompt: "Analyze the project structure",
  options: {
    allowedTools: ["Read", "Glob", "Grep"],
    promptSuggestions: true  // Enable suggestion generation
  }
})) {
  if (message.type === "prompt_suggestion") {
    // The SDK predicts what the user might ask next
    console.log("Suggested next prompt:", (message as any).suggestion);
  }
}
```

### Error Recovery Patterns

Handle different failure modes gracefully:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

async function runWithRetry(
  prompt: string,
  options: any,
  maxRetries = 3
): Promise<string> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      for await (const message of query({ prompt, options })) {
        if (message.type === "result") {
          switch (message.subtype) {
            case "success":
              return message.result;

            case "error_max_turns":
              // Agent ran out of turns -- increase limit and retry
              if (attempt < maxRetries) {
                options.maxTurns = (options.maxTurns ?? 20) * 1.5;
                console.log(`Retrying with maxTurns=${options.maxTurns}`);
                break;
              }
              throw new Error(`Max turns exceeded after ${maxRetries} attempts`);

            case "error_max_budget_usd":
              // Budget exceeded -- no point retrying
              throw new Error("Budget exceeded");

            case "error_during_execution":
              // Runtime error -- retry with fresh session
              if (attempt < maxRetries) {
                console.log(`Execution error, retrying (attempt ${attempt + 1})`);
                break;
              }
              throw new Error(`Execution failed: ${message.errors?.join(", ")}`);
          }
        }
      }
    } catch (error) {
      if (attempt === maxRetries) throw error;
      console.log(`Attempt ${attempt} failed, retrying...`);
    }
  }
  throw new Error("All retries exhausted");
}
```

### TypeScript vs. Python SDK Differences

The TypeScript SDK has several features not available in the Python version:

| Feature | TypeScript | Python |
|---------|-----------|--------|
| `SessionStart` hook callback | Yes | Shell commands only |
| `SessionEnd` hook callback | Yes | Shell commands only |
| `Setup` hook | Yes | No |
| `TeammateIdle` hook | Yes | No |
| `TaskCompleted` hook | Yes | No |
| `ConfigChange` hook | Yes | No |
| `WorktreeCreate` hook | Yes | No |
| `WorktreeRemove` hook | Yes | No |
| `dontAsk` permission mode | Yes | No |
| V2 interface (preview) | Yes | No |
| `await using` cleanup | Yes (TS 5.2+) | `async with` |

The Python SDK uses `snake_case` for all options (`allowed_tools`, `permission_mode`, `system_prompt`) while TypeScript uses `camelCase` (`allowedTools`, `permissionMode`, `systemPrompt`). The underlying functionality is identical.
