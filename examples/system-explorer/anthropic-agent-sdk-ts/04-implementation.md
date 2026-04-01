# Implementation Patterns

<!-- level:beginner -->
## Common Agent Patterns

### Pattern 1: Read-Only Analyzer

The simplest pattern -- an agent that examines code without modifying it:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

async function analyzeCode(prompt: string): Promise<string> {
  for await (const message of query({
    prompt,
    options: {
      allowedTools: ["Read", "Glob", "Grep"],  // Read-only tools only
      maxTurns: 10
    }
  })) {
    if (message.type === "result" && message.subtype === "success") {
      return message.result;
    }
  }
  throw new Error("Analysis failed");
}

// Usage
const analysis = await analyzeCode("Find all TODO comments and prioritize them");
console.log(analysis);
```

### Pattern 2: Code Modifier

An agent that can both analyze and change code:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

async function fixCode(prompt: string): Promise<{ result: string; cost: number }> {
  for await (const message of query({
    prompt,
    options: {
      allowedTools: ["Read", "Edit", "Glob", "Grep"],
      permissionMode: "acceptEdits",  // Auto-approve file changes
      maxBudgetUsd: 0.50
    }
  })) {
    if (message.type === "result" && message.subtype === "success") {
      return { result: message.result, cost: message.total_cost_usd };
    }
  }
  throw new Error("Fix failed");
}

const outcome = await fixCode("Add error handling to all async functions in src/");
console.log(`Result: ${outcome.result}`);
console.log(`Cost: $${outcome.cost.toFixed(4)}`);
```

### Pattern 3: Full Automation Agent

An agent with complete access for CI/CD pipelines:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Run the test suite, fix any failures, and commit the fixes",
  options: {
    allowedTools: ["Read", "Edit", "Write", "Bash", "Glob", "Grep"],
    permissionMode: "bypassPermissions",  // Only in trusted/sandboxed environments
    allowDangerouslySkipPermissions: true,
    maxTurns: 30,
    maxBudgetUsd: 2.0
  }
})) {
  if (message.type === "result") {
    if (message.subtype === "success") {
      console.log("Pipeline completed:", message.result);
    } else {
      console.error("Pipeline failed:", message.subtype);
    }
  }
}
```

### Pattern 4: Web Research Agent

An agent that searches the internet for information:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Research the latest TypeScript 5.6 features and write a summary",
  options: {
    allowedTools: ["WebSearch", "WebFetch", "Write"],
    permissionMode: "acceptEdits"
  }
})) {
  if (message.type === "result" && message.subtype === "success") {
    console.log(message.result);
  }
}
```

<!-- level:intermediate -->
## Custom Tool Implementation

### Creating an In-Process MCP Server

Define tools that Claude can call, using Zod for type-safe schemas:

```typescript
import { tool, createSdkMcpServer, query } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";

// Define a database query tool
const queryDatabase = tool(
  "query_database",
  "Execute a read-only SQL query against the application database",
  {
    sql: z.string().describe("SQL SELECT query to execute"),
    limit: z.number().int().min(1).max(100).default(10).describe("Maximum rows to return")
  },
  async (args) => {
    try {
      const results = await db.query(args.sql, { limit: args.limit });
      return {
        content: [{
          type: "text",
          text: JSON.stringify(results, null, 2)
        }]
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: `Query failed: ${error}` }],
        isError: true  // Tells Claude the tool failed -- agent loop continues
      };
    }
  },
  { annotations: { readOnlyHint: true } }  // Enables parallel execution
);

// Define a notification tool
const sendNotification = tool(
  "send_notification",
  "Send a notification to a Slack channel",
  {
    channel: z.string().describe("Slack channel name"),
    message: z.string().describe("Message to send")
  },
  async (args) => {
    await slackClient.postMessage(args.channel, args.message);
    return {
      content: [{ type: "text", text: `Sent to #${args.channel}` }]
    };
  }
);

// Bundle tools into an MCP server
const appServer = createSdkMcpServer({
  name: "my-app",
  version: "1.0.0",
  tools: [queryDatabase, sendNotification]
});

// Use the tools in an agent
for await (const message of query({
  prompt: "Check how many users signed up this week and post the count to #metrics",
  options: {
    mcpServers: { "my-app": appServer },
    allowedTools: [
      "mcp__my-app__query_database",
      "mcp__my-app__send_notification"
    ]
  }
})) {
  if (message.type === "result" && message.subtype === "success") {
    console.log(message.result);
  }
}
```

### Hook-Based Audit Trail

Implement comprehensive logging with hooks:

```typescript
import { query, HookCallback, PreToolUseHookInput, PostToolUseHookInput }
  from "@anthropic-ai/claude-agent-sdk";
import { appendFile } from "fs/promises";

const auditLog: HookCallback = async (input, toolUseID, { signal }) => {
  const timestamp = new Date().toISOString();

  if (input.hook_event_name === "PreToolUse") {
    const preInput = input as PreToolUseHookInput;
    await appendFile("audit.log",
      `${timestamp} [PRE] ${preInput.tool_name} input=${JSON.stringify(preInput.tool_input)}\n`
    );
  }

  if (input.hook_event_name === "PostToolUse") {
    const postInput = input as PostToolUseHookInput;
    await appendFile("audit.log",
      `${timestamp} [POST] ${postInput.tool_name} result=${JSON.stringify(postInput.tool_response).slice(0, 200)}\n`
    );
  }

  return {};  // Allow the operation to proceed
};

for await (const message of query({
  prompt: "Refactor the auth module",
  options: {
    allowedTools: ["Read", "Edit", "Glob", "Grep"],
    permissionMode: "acceptEdits",
    hooks: {
      PreToolUse: [{ hooks: [auditLog] }],
      PostToolUse: [{ hooks: [auditLog] }]
    }
  }
})) {
  // ...
}
```

### Multi-Agent Code Review Pipeline

Use subagents for parallel, specialized reviews:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: `Perform a comprehensive code review of the src/ directory.
Use the security-reviewer for security issues,
the performance-reviewer for performance concerns,
and the style-reviewer for code style.
Synthesize all findings into a final report.`,
  options: {
    allowedTools: ["Read", "Glob", "Grep", "Agent"],
    agents: {
      "security-reviewer": {
        description: "Security vulnerability scanner. Use for OWASP, injection, auth issues.",
        prompt: `You are a security expert. Review code for:
- SQL injection, XSS, CSRF
- Authentication/authorization flaws
- Secrets in code
- Input validation gaps
Rate each finding: CRITICAL, HIGH, MEDIUM, LOW.`,
        tools: ["Read", "Grep", "Glob"],
        model: "opus"
      },
      "performance-reviewer": {
        description: "Performance optimization expert. Use for N+1 queries, memory leaks, bottlenecks.",
        prompt: `You are a performance engineer. Review code for:
- N+1 database queries
- Memory leaks and unbounded growth
- Unnecessary recomputation
- Missing caching opportunities
Estimate impact: HIGH, MEDIUM, LOW.`,
        tools: ["Read", "Grep", "Glob"],
        model: "sonnet"
      },
      "style-reviewer": {
        description: "Code style and convention checker. Use for naming, structure, readability.",
        prompt: `You are a code style expert. Review for:
- Naming conventions
- Function length and complexity
- Dead code
- Missing documentation
Follow TypeScript best practices.`,
        tools: ["Read", "Grep", "Glob"],
        model: "haiku"
      }
    }
  }
})) {
  if ("result" in message) console.log(message.result);
}
```

### Session-Based Interactive Assistant

Build a multi-turn assistant that maintains context:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";
import * as readline from "readline";

const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

function askQuestion(prompt: string): Promise<string> {
  return new Promise((resolve) => rl.question(prompt, resolve));
}

let sessionId: string | undefined;

while (true) {
  const userInput = await askQuestion("\nYou: ");
  if (userInput === "exit") break;

  const options: any = {
    allowedTools: ["Read", "Edit", "Glob", "Grep", "Bash"],
    permissionMode: "acceptEdits"
  };

  // Resume session if we have one
  if (sessionId) {
    options.resume = sessionId;
  }

  process.stdout.write("\nClaude: ");

  for await (const message of query({ prompt: userInput, options })) {
    if (message.type === "system" && message.subtype === "init") {
      sessionId = message.session_id;
    }

    if (message.type === "assistant") {
      for (const block of message.message.content) {
        if (block.type === "text") {
          process.stdout.write(block.text);
        }
      }
    }
  }

  console.log();
}

rl.close();
```

<!-- level:advanced -->
## Production Patterns

### Guardrail System with Chained Hooks

Implement a comprehensive safety system using multiple hook layers:

```typescript
import { query, HookCallback, PreToolUseHookInput } from "@anthropic-ai/claude-agent-sdk";

// Layer 1: Rate limiter
const toolCallCounts = new Map<string, number>();
const rateLimiter: HookCallback = async (input) => {
  if (input.hook_event_name !== "PreToolUse") return {};
  const preInput = input as PreToolUseHookInput;

  const count = (toolCallCounts.get(preInput.tool_name) ?? 0) + 1;
  toolCallCounts.set(preInput.tool_name, count);

  if (count > 50) {
    return {
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: `Rate limit: ${preInput.tool_name} called ${count} times`
      }
    };
  }
  return {};
};

// Layer 2: Path-based security
const pathGuard: HookCallback = async (input) => {
  if (input.hook_event_name !== "PreToolUse") return {};
  const preInput = input as PreToolUseHookInput;
  const toolInput = preInput.tool_input as Record<string, unknown>;
  const filePath = (toolInput?.file_path as string) ?? "";

  const blockedPatterns = [/\.env/, /credentials/, /secrets/, /\.ssh/, /node_modules/];
  if (blockedPatterns.some(p => p.test(filePath))) {
    return {
      systemMessage: "This file is protected and cannot be accessed.",
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: `Protected path: ${filePath}`
      }
    };
  }
  return {};
};

// Layer 3: Command sanitizer
const commandSanitizer: HookCallback = async (input) => {
  if (input.hook_event_name !== "PreToolUse") return {};
  const preInput = input as PreToolUseHookInput;
  if (preInput.tool_name !== "Bash") return {};

  const toolInput = preInput.tool_input as Record<string, unknown>;
  const command = toolInput?.command as string;
  const dangerous = ["rm -rf", "sudo", "chmod 777", "mkfs", "dd if=", "> /dev/"];

  if (dangerous.some(d => command.includes(d))) {
    return {
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: `Blocked dangerous command: ${command}`
      }
    };
  }
  return {};
};

// Layer 4: Async telemetry (non-blocking)
const telemetry: HookCallback = async (input) => {
  // Fire and forget -- don't block the agent
  fetch("https://telemetry.internal/events", {
    method: "POST",
    body: JSON.stringify({
      event: input.hook_event_name,
      tool: (input as any).tool_name,
      timestamp: Date.now()
    })
  }).catch(() => {});

  return { async: true, asyncTimeout: 5000 };  // Don't wait for this
};

for await (const message of query({
  prompt: "Analyze and optimize the database queries in src/db/",
  options: {
    allowedTools: ["Read", "Edit", "Glob", "Grep", "Bash"],
    permissionMode: "acceptEdits",
    hooks: {
      PreToolUse: [
        { hooks: [rateLimiter] },           // Check rate limits first
        { hooks: [pathGuard] },             // Then check file paths
        { matcher: "Bash", hooks: [commandSanitizer] },  // Bash-specific guard
        { hooks: [telemetry] }              // Non-blocking telemetry
      ]
    }
  }
})) {
  // ...
}
```

### Dynamic Agent Factory

Create agents dynamically based on runtime context:

```typescript
import { query, AgentDefinition } from "@anthropic-ai/claude-agent-sdk";

interface ReviewConfig {
  language: string;
  strictness: "relaxed" | "standard" | "strict";
  focusAreas: string[];
}

function createReviewAgent(config: ReviewConfig): AgentDefinition {
  const strictnessPrompts = {
    relaxed: "Focus only on critical issues.",
    standard: "Report medium and high severity issues.",
    strict: "Report all issues including minor style concerns."
  };

  return {
    description: `Code reviewer for ${config.language} projects (${config.strictness} mode)`,
    prompt: `You are a ${config.language} code review expert.
${strictnessPrompts[config.strictness]}
Focus areas: ${config.focusAreas.join(", ")}
Provide actionable, specific feedback with line references.`,
    tools: ["Read", "Grep", "Glob"],
    model: config.strictness === "strict" ? "opus" : "sonnet"
  };
}

// Build agents from a config file or database
const projectConfig: ReviewConfig = {
  language: "TypeScript",
  strictness: "strict",
  focusAreas: ["type safety", "error handling", "test coverage"]
};

for await (const message of query({
  prompt: "Review the pull request changes",
  options: {
    allowedTools: ["Read", "Glob", "Grep", "Bash", "Agent"],
    agents: {
      reviewer: createReviewAgent(projectConfig)
    }
  }
})) {
  if ("result" in message) console.log(message.result);
}
```

### Parallel Task Execution with Background Agents

Run multiple agents concurrently for faster results:

```typescript
import { query, SDKMessage } from "@anthropic-ai/claude-agent-sdk";

async function runAgent(
  prompt: string,
  tools: string[]
): Promise<{ result: string; cost: number }> {
  for await (const message of query({
    prompt,
    options: { allowedTools: tools, maxTurns: 15, maxBudgetUsd: 0.50 }
  })) {
    if (message.type === "result" && message.subtype === "success") {
      return { result: message.result, cost: message.total_cost_usd };
    }
  }
  throw new Error("Agent failed");
}

// Run multiple analyses in parallel
const [security, performance, documentation] = await Promise.all([
  runAgent(
    "Analyze src/ for security vulnerabilities",
    ["Read", "Grep", "Glob"]
  ),
  runAgent(
    "Profile the hot paths in src/ and suggest optimizations",
    ["Read", "Grep", "Glob", "Bash"]
  ),
  runAgent(
    "Check documentation coverage for all public APIs in src/",
    ["Read", "Grep", "Glob"]
  )
]);

console.log("Security:", security.result);
console.log("Performance:", performance.result);
console.log("Documentation:", documentation.result);
console.log(`Total cost: $${(security.cost + performance.cost + documentation.cost).toFixed(4)}`);
```

### Input Transformation via Hooks

Modify tool inputs before execution -- useful for sandboxing and path rewriting:

```typescript
import { query, HookCallback, PreToolUseHookInput } from "@anthropic-ai/claude-agent-sdk";

const sandboxPaths: HookCallback = async (input) => {
  if (input.hook_event_name !== "PreToolUse") return {};
  const preInput = input as PreToolUseHookInput;
  const toolInput = preInput.tool_input as Record<string, unknown>;

  // Rewrite file paths to sandbox directory
  if (toolInput?.file_path) {
    const originalPath = toolInput.file_path as string;
    if (!originalPath.startsWith("/sandbox")) {
      return {
        hookSpecificOutput: {
          hookEventName: "PreToolUse",
          permissionDecision: "allow",
          updatedInput: {
            ...toolInput,
            file_path: `/sandbox${originalPath}`
          }
        }
      };
    }
  }

  // Rewrite Bash commands to run in sandbox
  if (preInput.tool_name === "Bash" && toolInput?.command) {
    return {
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "allow",
        updatedInput: {
          ...toolInput,
          command: `cd /sandbox && ${toolInput.command}`
        }
      }
    };
  }

  return {};
};

for await (const message of query({
  prompt: "Install dependencies and run the test suite",
  options: {
    allowedTools: ["Read", "Edit", "Bash", "Glob"],
    permissionMode: "acceptEdits",
    hooks: {
      PreToolUse: [{ hooks: [sandboxPaths] }]
    }
  }
})) {
  // All file operations are redirected to /sandbox/
}
```

### Streaming Partial Messages for Real-Time UIs

Enable token-by-token streaming for responsive user interfaces:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Explain the architecture of this codebase",
  options: {
    allowedTools: ["Read", "Glob", "Grep"],
    includePartialMessages: true  // Enable streaming deltas
  }
})) {
  if (message.type === "stream_event") {
    // Raw Anthropic API stream events
    const event = message.event;
    if (event.type === "content_block_delta" && event.delta.type === "text_delta") {
      process.stdout.write(event.delta.text);  // Token-by-token output
    }
  }
}
```
