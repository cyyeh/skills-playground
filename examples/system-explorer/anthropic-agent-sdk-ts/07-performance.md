# Performance & Optimization

<!-- level:beginner -->
## Understanding Costs

Every agent interaction has costs in three dimensions:

### 1. API Token Cost
Claude charges per input and output token. The Agent SDK adds overhead because:
- Each tool call adds tokens for the tool definition + call + result
- Multi-turn conversations accumulate context
- Subagents run separate API calls

### 2. Time
Agent tasks take time because:
- Each API call has latency (typically 2-15 seconds depending on complexity)
- Tool execution adds time (file reads, web requests, bash commands)
- Multi-turn loops multiply these delays

### 3. Compute
The agent process consumes local CPU and memory for:
- Tool execution (bash commands, file operations)
- MCP server processes
- Session persistence (disk I/O)

### Quick Cost Controls

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Analyze this codebase",
  options: {
    // Budget: stop if cost exceeds $0.50
    maxBudgetUsd: 0.50,

    // Turns: limit to 15 round-trips
    maxTurns: 15,

    // Model: use a cheaper model for simple tasks
    model: "claude-haiku-4-20250514",

    // Effort: lower effort = fewer thinking tokens
    effort: "medium",

    allowedTools: ["Read", "Glob", "Grep"]
  }
})) {
  if (message.type === "result") {
    if (message.subtype === "success") {
      console.log(`Cost: $${message.total_cost_usd.toFixed(4)}`);
      console.log(`Turns: ${message.num_turns}`);
      console.log(`Time: ${message.duration_ms}ms`);
    } else if (message.subtype === "error_max_budget_usd") {
      console.log("Budget exceeded");
    } else if (message.subtype === "error_max_turns") {
      console.log("Turn limit reached");
    }
  }
}
```

### Model Selection for Cost Optimization

| Model | Speed | Cost | Best For |
|-------|-------|------|----------|
| **Haiku** | Fastest | Lowest | Simple tasks, classification, formatting |
| **Sonnet** | Medium | Medium | Most development tasks, code review |
| **Opus** | Slowest | Highest | Complex reasoning, security audits, architecture |

```typescript
// Use the fallback model when primary is unavailable or rate-limited
options: {
  model: "claude-sonnet-4-20250514",
  fallbackModel: "claude-haiku-4-20250514"
}
```

<!-- level:intermediate -->
## Optimization Strategies

### Strategy 1: Minimize Tool Calls

Each tool call is an API round-trip. Reduce them by:

**Giving precise prompts:**
```typescript
// Bad: vague prompt leads to many exploratory tool calls
prompt: "Check the code for issues"

// Good: specific prompt reduces exploration
prompt: "Check src/auth/login.ts for SQL injection vulnerabilities in the query functions"
```

**Providing context in the system prompt:**
```typescript
options: {
  systemPrompt: `Project structure:
- src/server/ -- Express.js backend
- src/client/ -- React frontend
- src/shared/ -- Shared types
- Tests are co-located as *.test.ts
Use Glob before Read to find files efficiently.`
}
```

### Strategy 2: Limit Tool Access

Only allow tools the agent actually needs:

```typescript
// Read-only analysis -- no Write, Edit, or Bash
options: { allowedTools: ["Read", "Glob", "Grep"] }

// Editing tasks -- add Edit but not Bash
options: { allowedTools: ["Read", "Edit", "Glob", "Grep"] }

// Full automation -- include Bash only when necessary
options: { allowedTools: ["Read", "Edit", "Write", "Bash", "Glob", "Grep"] }
```

Fewer available tools means fewer tokens spent on tool definitions in the context window.

### Strategy 3: Use Subagents for Context Efficiency

Subagents have fresh context windows. A main agent analyzing 50 files will accumulate all that content in its context. Delegating to subagents keeps each context focused:

```typescript
options: {
  allowedTools: ["Agent", "Read", "Glob"],
  agents: {
    "file-analyzer": {
      description: "Analyze a single file or small set of files",
      prompt: "Analyze the given files. Return a concise summary.",
      tools: ["Read", "Grep"],
      model: "haiku"  // Cheaper model for individual file analysis
    }
  }
}
```

### Strategy 4: Control Thinking Depth

```typescript
// For simple tasks: minimal thinking
options: {
  effort: "low",
  thinking: { type: "disabled" }
}

// For complex tasks: full thinking
options: {
  effort: "max",
  thinking: { type: "adaptive" }
}

// For budget-sensitive tasks: capped thinking
options: {
  thinking: { type: "enabled", budget_tokens: 2000 }
}
```

### Strategy 5: Disable Session Persistence

For one-off tasks where you do not need to resume:

```typescript
options: {
  persistSession: false  // Skip disk I/O for session storage
}
```

### Strategy 6: Use Structured Output

When you need data, not prose, use structured output to avoid wasted tokens on formatting:

```typescript
options: {
  outputFormat: {
    type: "json_schema",
    schema: {
      type: "object",
      properties: {
        issues: {
          type: "array",
          items: {
            type: "object",
            properties: {
              file: { type: "string" },
              line: { type: "number" },
              severity: { type: "string" },
              description: { type: "string" }
            }
          }
        }
      }
    }
  }
}
```

<!-- level:advanced -->
## Advanced Performance Tuning

### Monitoring Cost and Usage

Extract detailed usage metrics from result messages:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({ prompt: "...", options })) {
  if (message.type === "result" && message.subtype === "success") {
    // Overall metrics
    console.log(`Total cost: $${message.total_cost_usd.toFixed(4)}`);
    console.log(`Total turns: ${message.num_turns}`);
    console.log(`Wall time: ${message.duration_ms}ms`);
    console.log(`API time: ${message.duration_api_ms}ms`);
    console.log(`Overhead: ${message.duration_ms - message.duration_api_ms}ms`);

    // Per-model breakdown
    for (const [model, usage] of Object.entries(message.modelUsage)) {
      console.log(`Model ${model}:`);
      console.log(`  Input tokens: ${usage.input_tokens}`);
      console.log(`  Output tokens: ${usage.output_tokens}`);
      console.log(`  Cache read: ${usage.cache_read_input_tokens}`);
      console.log(`  Cache write: ${usage.cache_creation_input_tokens}`);
    }

    // Token usage
    console.log(`Total input: ${message.usage.input_tokens}`);
    console.log(`Total output: ${message.usage.output_tokens}`);

    // Permission denials (may indicate misconfiguration)
    if (message.permission_denials.length > 0) {
      console.log("Permission denials:", message.permission_denials);
    }
  }
}
```

### Rate Limit Handling

The SDK emits rate limit events that you can monitor:

```typescript
for await (const message of query({ prompt: "...", options })) {
  if (message.type === "rate_limit") {
    // SDK handles retry automatically, but you can log it
    console.warn("Rate limited -- SDK will retry");
  }
}
```

### Context Window Management

The SDK automatically compacts conversations when they approach the context limit. You can hook into this process:

```typescript
import { query, HookCallback } from "@anthropic-ai/claude-agent-sdk";

const preCompactHook: HookCallback = async (input) => {
  if (input.hook_event_name !== "PreCompact") return {};

  const compactInput = input as any;
  console.log(`Context compaction triggered:`);
  console.log(`  Trigger: ${compactInput.trigger}`);  // "auto" or "manual"
  console.log(`  Pre-tokens: ${compactInput.compact_metadata?.pre_tokens}`);

  // You could archive the full transcript here before compaction
  // await archiveTranscript(input.transcript_path);

  return {};
};

for await (const message of query({
  prompt: "Do a comprehensive analysis (may require many tool calls)",
  options: {
    allowedTools: ["Read", "Glob", "Grep"],
    hooks: {
      PreCompact: [{ hooks: [preCompactHook] }]
    }
  }
})) {
  // Monitor compaction boundaries in the message stream
  if (message.type === "system" && (message as any).subtype === "compact_boundary") {
    const compact = message as any;
    console.log(`Compacted at ${compact.compact_metadata.pre_tokens} tokens`);
  }
}
```

### 1M Context Window

For tasks requiring very large context (reading entire codebases):

```typescript
options: {
  betas: ["context-1m-2025-08-07"],  // Enable 1M token context
  model: "claude-sonnet-4-20250514"   // Must be Sonnet 4 or 4.5
}
```

### Parallel Tool Execution

Mark custom tools as read-only to enable parallel execution:

```typescript
const readOnlyTool = tool(
  "check_endpoint",
  "Check if an API endpoint is responding",
  { url: z.string().url() },
  async (args) => {
    const start = Date.now();
    const resp = await fetch(args.url);
    return {
      content: [{
        type: "text",
        text: `${args.url}: ${resp.status} (${Date.now() - start}ms)`
      }]
    };
  },
  { annotations: { readOnlyHint: true } }  // Enables parallel execution
);
```

When Claude calls multiple read-only tools in a single turn, they execute concurrently rather than sequentially.

### Tool Search for Large Tool Sets

When you have dozens of MCP tools, the SDK uses tool search to avoid context window bloat:

```typescript
// With many tools, tool search is enabled automatically
options: {
  mcpServers: {
    crm: crmServer,         // 15 tools
    analytics: analyticsServer,  // 12 tools
    email: emailServer,     // 8 tools
    calendar: calendarServer // 6 tools
    // 41 tools total -- tool search kicks in
  },
  allowedTools: [
    "mcp__crm__*",
    "mcp__analytics__*",
    "mcp__email__*",
    "mcp__calendar__*"
  ]
}
// Claude uses ToolSearch to discover tools on-demand
// instead of loading all 41 tool definitions upfront
```

### Cancellation and Cleanup

Use AbortController for timeout management and graceful cancellation:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

const controller = new AbortController();

// Hard timeout
const timeout = setTimeout(() => {
  controller.abort();
  console.log("Agent timed out after 60 seconds");
}, 60_000);

try {
  for await (const message of query({
    prompt: "Analyze the codebase",
    options: {
      abortController: controller,
      allowedTools: ["Read", "Glob", "Grep"]
    }
  })) {
    if (message.type === "result") {
      clearTimeout(timeout);
      console.log("Completed within time limit");
    }
  }
} catch (error) {
  if (controller.signal.aborted) {
    console.log("Cancelled by timeout");
  }
} finally {
  clearTimeout(timeout);
}
```

### Benchmark: Turns vs. Cost

Empirical observations for common task types:

| Task Type | Typical Turns | Typical Cost (Sonnet) | Typical Time |
|-----------|--------------|----------------------|-------------|
| Read and summarize 1 file | 2-3 | $0.01-0.03 | 5-10s |
| Find and fix a single bug | 4-8 | $0.05-0.15 | 15-30s |
| Code review (10 files) | 10-20 | $0.10-0.30 | 30-90s |
| Refactor a module | 8-15 | $0.10-0.40 | 30-60s |
| Full codebase analysis | 20-40 | $0.30-1.00 | 2-5min |
| Multi-agent review pipeline | 15-30 | $0.20-0.80 | 1-3min |

These numbers vary significantly based on project size, complexity, model choice, and effort level. Use `maxBudgetUsd` and `maxTurns` to set hard limits.
