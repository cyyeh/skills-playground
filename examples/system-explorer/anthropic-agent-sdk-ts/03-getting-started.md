# Getting Started

<!-- level:beginner -->
## Installation

### Prerequisites

- **Node.js 18+** (check with `node --version`)
- An **Anthropic API key** from [platform.claude.com](https://platform.claude.com)

### Step 1: Install the Package

```bash
npm install @anthropic-ai/claude-agent-sdk
```

Or with your preferred package manager:

```bash
# yarn
yarn add @anthropic-ai/claude-agent-sdk

# pnpm
pnpm add @anthropic-ai/claude-agent-sdk
```

### Step 2: Set Your API Key

Create a `.env` file in your project root:

```bash
ANTHROPIC_API_KEY=your-api-key-here
```

Or set it as an environment variable:

```bash
export ANTHROPIC_API_KEY=your-api-key-here
```

### Step 3: Write Your First Agent

Create a file called `agent.ts`:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

// The simplest possible agent
for await (const message of query({
  prompt: "What files are in this directory? List them with brief descriptions.",
  options: {
    allowedTools: ["Glob", "Read"]
  }
})) {
  if ("result" in message) {
    console.log(message.result);
  }
}
```

### Step 4: Run It

```bash
npx tsx agent.ts
```

That is it. Claude will use the `Glob` tool to find files, the `Read` tool to examine them, and return a summary.

## Your First Real Agent: Bug Fixer

Let us build something more practical -- an agent that finds and fixes bugs:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Review utils.py for bugs that would cause crashes. Fix any issues you find.",
  options: {
    allowedTools: ["Read", "Edit", "Glob"],
    permissionMode: "acceptEdits"  // Auto-approve file changes
  }
})) {
  // Show Claude's reasoning and actions
  if (message.type === "assistant" && message.message?.content) {
    for (const block of message.message.content) {
      if ("text" in block) {
        console.log(block.text);
      } else if ("name" in block) {
        console.log(`Tool: ${block.name}`);
      }
    }
  } else if (message.type === "result") {
    console.log(`Done: ${message.subtype}`);
  }
}
```

### What Happens When This Runs

1. Claude receives your prompt and the list of available tools
2. It decides to read `utils.py` using the `Read` tool
3. It analyzes the code and identifies bugs (e.g., division by zero, null handling)
4. It uses the `Edit` tool to fix each bug with precise string replacements
5. It reports what it found and fixed
6. You see each step streamed in real time

## Understanding the Output

The `for await` loop yields different message types. Here is a practical way to handle them:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Add type hints to all functions in src/utils.ts",
  options: {
    allowedTools: ["Read", "Edit", "Glob", "Grep"],
    permissionMode: "acceptEdits"
  }
})) {
  switch (message.type) {
    case "system":
      // Session started -- you can capture the session_id here
      console.log(`Session: ${message.session_id}`);
      console.log(`Model: ${(message as any).model}`);
      break;

    case "assistant":
      // Claude is working -- show what it's doing
      for (const block of message.message.content) {
        if (block.type === "text") {
          process.stdout.write(block.text);
        } else if (block.type === "tool_use") {
          console.log(`\n[Using ${block.name}]`);
        }
      }
      break;

    case "result":
      // Task complete
      if (message.subtype === "success") {
        console.log(`\n\nDone! Cost: $${message.total_cost_usd.toFixed(4)}`);
        console.log(`Turns: ${message.num_turns}, Time: ${message.duration_ms}ms`);
      } else {
        console.error(`Failed: ${message.subtype}`);
      }
      break;
  }
}
```

<!-- level:intermediate -->
## Configuration Deep Dive

### The Options Object

The `options` parameter controls nearly every aspect of agent behavior. Here are the most commonly used fields:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Refactor the authentication module",
  options: {
    // What tools Claude can use
    allowedTools: ["Read", "Edit", "Glob", "Grep", "Bash"],
    disallowedTools: ["Write"],  // Block creating new files

    // Permission behavior
    permissionMode: "acceptEdits",

    // Model selection
    model: "claude-sonnet-4-20250514",
    fallbackModel: "claude-haiku-4-20250514",

    // Budget controls
    maxTurns: 20,
    maxBudgetUsd: 1.0,

    // Thinking behavior
    effort: "high",
    thinking: { type: "adaptive" },

    // System prompt
    systemPrompt: "You are a senior TypeScript developer. Follow project conventions.",

    // Working directory
    cwd: "/path/to/project",

    // Debug output
    debug: true,
    debugFile: "./agent-debug.log"
  }
})) {
  // ...
}
```

### Adding Custom System Prompts

You have two options for system prompts:

**Custom string prompt:**
```typescript
options: {
  systemPrompt: "You are a security auditor. Only report high-severity issues."
}
```

**Claude Code preset with additions:**
```typescript
options: {
  systemPrompt: {
    type: "preset",
    preset: "claude_code",
    append: "Always follow our team's coding standards in CLAUDE.md"
  },
  settingSources: ["project"]  // Required to load CLAUDE.md
}
```

### Working with Multiple Directories

```typescript
options: {
  cwd: "/main/project",
  additionalDirectories: [
    "/shared/libraries",
    "/config/templates"
  ]
}
```

### Structured Output

Force Claude to return results in a specific JSON schema:

```typescript
for await (const message of query({
  prompt: "Analyze this codebase and categorize all functions",
  options: {
    allowedTools: ["Read", "Glob", "Grep"],
    outputFormat: {
      type: "json_schema",
      schema: {
        type: "object",
        properties: {
          functions: {
            type: "array",
            items: {
              type: "object",
              properties: {
                name: { type: "string" },
                file: { type: "string" },
                category: { type: "string", enum: ["utility", "handler", "middleware", "model"] },
                complexity: { type: "string", enum: ["low", "medium", "high"] }
              },
              required: ["name", "file", "category", "complexity"]
            }
          }
        },
        required: ["functions"]
      }
    }
  }
})) {
  if (message.type === "result" && message.subtype === "success") {
    const analysis = message.structured_output;
    console.log(JSON.stringify(analysis, null, 2));
  }
}
```

### AbortController for Cancellation

```typescript
const controller = new AbortController();

// Cancel after 30 seconds
setTimeout(() => controller.abort(), 30_000);

for await (const message of query({
  prompt: "Do a comprehensive code review",
  options: {
    abortController: controller,
    allowedTools: ["Read", "Glob", "Grep"]
  }
})) {
  if ("result" in message) console.log(message.result);
}
```

## The V2 Interface (Preview)

The V2 interface simplifies multi-turn conversations by replacing the async generator pattern with explicit `send()` and `stream()` calls:

```typescript
import { unstable_v2_createSession } from "@anthropic-ai/claude-agent-sdk";

// Create a session (auto-cleaned up with `await using`)
await using session = unstable_v2_createSession({
  model: "claude-opus-4-6"
});

// Turn 1
await session.send("What is 5 + 3?");
for await (const msg of session.stream()) {
  if (msg.type === "assistant") {
    const text = msg.message.content
      .filter((b) => b.type === "text")
      .map((b) => b.text)
      .join("");
    console.log(text);
  }
}

// Turn 2 -- Claude remembers the previous answer
await session.send("Multiply that by 2");
for await (const msg of session.stream()) {
  if (msg.type === "assistant") {
    const text = msg.message.content
      .filter((b) => b.type === "text")
      .map((b) => b.text)
      .join("");
    console.log(text);
  }
}
```

### V2 One-Shot Convenience

For simple single-turn queries without session management:

```typescript
import { unstable_v2_prompt } from "@anthropic-ai/claude-agent-sdk";

const result = await unstable_v2_prompt("What is 2 + 2?", {
  model: "claude-opus-4-6"
});

if (result.subtype === "success") {
  console.log(result.result);  // "4"
}
```

<!-- level:advanced -->
## Advanced Initialization Patterns

### Streaming Input Mode for Interactive Applications

For interactive applications (chat UIs, REPLs), use an async iterable as the prompt to enable multi-turn conversations within a single `query()` call:

```typescript
import { query, SDKUserMessage } from "@anthropic-ai/claude-agent-sdk";

// Create a message queue for the input stream
async function* createInputStream(): AsyncIterable<SDKUserMessage> {
  // In a real app, this would read from stdin, a WebSocket, etc.
  const messages = [
    "Read the authentication module",
    "Now find all security vulnerabilities",
    "Fix the most critical one"
  ];

  for (const text of messages) {
    yield {
      type: "user",
      session_id: "",
      message: { role: "user", content: [{ type: "text", text }] },
      parent_tool_use_id: null
    };
  }
}

const q = query({
  prompt: createInputStream(),
  options: {
    allowedTools: ["Read", "Edit", "Glob", "Grep"],
    permissionMode: "acceptEdits"
  }
});

for await (const message of q) {
  if (message.type === "assistant") {
    const text = message.message.content
      .filter((b: any) => b.type === "text")
      .map((b: any) => b.text)
      .join("");
    if (text) console.log(text);
  }
}
```

### Runtime Reconfiguration

The `Query` object supports changing configuration mid-session:

```typescript
const q = query({
  prompt: createInputStream(),
  options: { allowedTools: ["Read", "Glob"] }
});

// After initialization, upgrade to a more capable model
const init = await q.initializationResult();
console.log("Started with model:", init.models[0]);

// Dynamically switch model
await q.setModel("claude-opus-4-6");

// Add MCP servers at runtime
await q.setMcpServers({
  github: {
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-github"],
    env: { GITHUB_TOKEN: process.env.GITHUB_TOKEN! }
  }
});

// Change permission mode
await q.setPermissionMode("acceptEdits");
```

### File Checkpointing and Rewind

Enable file checkpointing to track and revert file changes:

```typescript
const q = query({
  prompt: "Refactor the entire codebase to use TypeScript strict mode",
  options: {
    allowedTools: ["Read", "Edit", "Glob", "Grep"],
    permissionMode: "acceptEdits",
    enableFileCheckpointing: true  // Track all file changes
  }
});

let lastUserMessageId: string | undefined;

for await (const message of q) {
  if (message.type === "user") {
    lastUserMessageId = message.uuid;
  }

  if (message.type === "result" && message.subtype === "success") {
    // Preview what would be reverted
    const preview = await q.rewindFiles(lastUserMessageId!, { dryRun: true });
    console.log("Would revert:", preview);

    // Actually revert if something went wrong
    // const result = await q.rewindFiles(lastUserMessageId!);
  }
}
```

### Custom Process Spawning for Remote Execution

Run the agent process inside a Docker container, VM, or remote machine:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";
import { spawn } from "child_process";

for await (const message of query({
  prompt: "Analyze the project",
  options: {
    spawnClaudeCodeProcess: (spawnOptions) => {
      const proc = spawn("ssh", [
        "build-server",
        "claude-code", ...spawnOptions.args
      ], {
        stdio: ["pipe", "pipe", "pipe"],
        env: { ...process.env, ...spawnOptions.env }
      });

      return {
        stdin: proc.stdin!,
        stdout: proc.stdout!,
        stderr: proc.stderr!,
        on: proc.on.bind(proc),
        kill: proc.kill.bind(proc)
      };
    }
  }
})) {
  // Messages stream from the remote agent
}
```

### Sandbox Configuration

Control the sandbox behavior programmatically:

```typescript
options: {
  sandbox: {
    // Configure how the agent process is sandboxed
    // Platform-specific options
    type: "docker",
    image: "node:20-slim",
    volumes: ["/workspace:/workspace"]
  }
}
```

### Beta Features

Enable experimental features:

```typescript
options: {
  betas: ["context-1m-2025-08-07"]  // 1M token context on Sonnet 4/4.5
}
```

### Environment Variable Configuration

Pass custom environment variables to the agent process:

```typescript
options: {
  env: {
    ...process.env,
    CLAUDE_AGENT_SDK_CLIENT_APP: "my-ci-pipeline",  // Identifies your app in User-Agent
    DATABASE_URL: "postgres://...",
    API_KEY: process.env.INTERNAL_API_KEY
  }
}
```
