# Use Cases & Adoption

<!-- level:beginner -->
## Who Uses the Agent SDK?

The Anthropic Agent SDK is used by 1,100+ projects as of March 2026. It targets developers building AI-powered automation in several domains:

### Primary Use Cases

#### 1. CI/CD Pipeline Automation
Integrate Claude into your continuous integration to automatically review code, fix linting errors, update tests, and generate changelogs.

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

// CI pipeline step: auto-fix linting and type errors
for await (const message of query({
  prompt: `Run 'npm run lint' and 'npx tsc --noEmit'. Fix any errors found.
Do not change test files. Commit fixes with a descriptive message.`,
  options: {
    allowedTools: ["Read", "Edit", "Bash", "Glob", "Grep"],
    permissionMode: "bypassPermissions",
    allowDangerouslySkipPermissions: true,
    maxBudgetUsd: 1.0,
    maxTurns: 20
  }
})) {
  if (message.type === "result") {
    if (message.subtype === "success") {
      console.log("CI fix completed:", message.result);
      process.exit(0);
    } else {
      console.error("CI fix failed:", message.subtype);
      process.exit(1);
    }
  }
}
```

#### 2. Code Review Automation
Automatically review pull requests for quality, security, and style:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: `Review the changes in the current git diff (git diff main...HEAD).
Categorize findings as: CRITICAL, WARNING, SUGGESTION.
Focus on security, correctness, and maintainability.`,
  options: {
    allowedTools: ["Read", "Bash", "Glob", "Grep"],
    systemPrompt: "You are a senior code reviewer. Be thorough but constructive."
  }
})) {
  if (message.type === "result" && message.subtype === "success") {
    // Post review to GitHub PR
    console.log(message.result);
  }
}
```

#### 3. Documentation Generation
Generate or update documentation from code:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: `Analyze all public functions in src/ and generate API documentation.
Create a docs/api-reference.md file with function signatures, descriptions,
parameter types, return types, and usage examples.`,
  options: {
    allowedTools: ["Read", "Write", "Glob", "Grep"],
    permissionMode: "acceptEdits"
  }
})) {
  if ("result" in message) console.log(message.result);
}
```

#### 4. Research and Analysis
Build agents that gather and synthesize information:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: `Research the top 5 alternatives to Redis for caching in Node.js applications.
Compare them on: performance, ease of use, clustering support, and community size.
Write a summary to research-results.md.`,
  options: {
    allowedTools: ["WebSearch", "WebFetch", "Write"],
    permissionMode: "acceptEdits"
  }
})) {
  if ("result" in message) console.log(message.result);
}
```

#### 5. Data Processing Pipelines
Automate data transformation and analysis tasks:

```typescript
import { tool, createSdkMcpServer, query } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";

const queryDB = tool(
  "query_database",
  "Run a read-only SQL query",
  { sql: z.string() },
  async (args) => {
    const results = await pool.query(args.sql);
    return { content: [{ type: "text", text: JSON.stringify(results.rows) }] };
  },
  { annotations: { readOnlyHint: true } }
);

const dbServer = createSdkMcpServer({ name: "db", tools: [queryDB] });

for await (const message of query({
  prompt: "Analyze user signup trends over the past 30 days. Break down by source, device, and geography. Write a summary.",
  options: {
    mcpServers: { db: dbServer },
    allowedTools: ["mcp__db__query_database", "Write"],
    permissionMode: "acceptEdits"
  }
})) {
  if ("result" in message) console.log(message.result);
}
```

<!-- level:intermediate -->
## Real-World Patterns

### Pattern: PR Bot with GitHub MCP

Build a GitHub-integrated PR review bot:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

async function reviewPR(prNumber: number, repo: string) {
  for await (const message of query({
    prompt: `Review PR #${prNumber} in ${repo}.
Fetch the diff using the GitHub MCP server.
For each file changed, check for:
1. Security vulnerabilities
2. Performance regressions
3. Missing error handling
4. Test coverage gaps
Format as a structured review with file-by-file comments.`,
    options: {
      mcpServers: {
        github: {
          command: "npx",
          args: ["-y", "@modelcontextprotocol/server-github"],
          env: { GITHUB_TOKEN: process.env.GITHUB_TOKEN }
        }
      },
      allowedTools: [
        "mcp__github__*",
        "Read", "Grep", "Glob"
      ],
      systemPrompt: `You are a thorough code reviewer.
Always explain WHY something is a problem, not just WHAT the problem is.
Suggest specific fixes with code examples.`
    }
  })) {
    if (message.type === "result" && message.subtype === "success") {
      return message.result;
    }
  }
}
```

### Pattern: Database Migration Assistant

An agent that generates and validates database migrations:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: `I need to add a "last_login_at" timestamp column to the users table.
1. Read the existing migration files to understand the pattern
2. Generate a new migration following the same conventions
3. Generate a rollback migration
4. Verify both migrations are syntactically valid by dry-running them`,
  options: {
    allowedTools: ["Read", "Write", "Bash", "Glob", "Grep"],
    permissionMode: "acceptEdits",
    agents: {
      "migration-validator": {
        description: "Validates SQL migrations for correctness and safety",
        prompt: `You validate SQL migrations. Check for:
- Backward compatibility (no destructive changes without fallback)
- Index creation on large tables (use CONCURRENTLY)
- Data migration safety
- Rollback correctness`,
        tools: ["Read", "Bash", "Grep"]
      }
    }
  }
})) {
  if ("result" in message) console.log(message.result);
}
```

### Pattern: Email/Report Generator

Build an agent that collects data and generates formatted reports:

```typescript
import { tool, createSdkMcpServer, query } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";

const sendEmail = tool(
  "send_email",
  "Send an email via the company email service",
  {
    to: z.string().email(),
    subject: z.string(),
    body: z.string().describe("HTML email body")
  },
  async (args) => {
    await emailService.send(args.to, args.subject, args.body);
    return { content: [{ type: "text", text: "Email sent successfully" }] };
  }
);

const getMetrics = tool(
  "get_metrics",
  "Fetch application metrics for a time range",
  {
    metric: z.enum(["requests", "errors", "latency", "signups"]),
    period: z.enum(["1h", "24h", "7d", "30d"])
  },
  async (args) => {
    const data = await metricsService.query(args.metric, args.period);
    return { content: [{ type: "text", text: JSON.stringify(data) }] };
  },
  { annotations: { readOnlyHint: true } }
);

const reportServer = createSdkMcpServer({
  name: "reports",
  tools: [sendEmail, getMetrics]
});

for await (const message of query({
  prompt: `Generate a weekly status report:
1. Get request volume, error rate, and latency for the past 7 days
2. Get signup numbers for the past 7 days
3. Format as an HTML email with charts described in text
4. Send to team@company.com with subject "Weekly Status Report"`,
  options: {
    mcpServers: { reports: reportServer },
    allowedTools: ["mcp__reports__*"]
  }
})) {
  if ("result" in message) console.log(message.result);
}
```

### Pattern: Deployment Agent

An agent that handles deployments with safety checks:

```typescript
import { query, HookCallback, PreToolUseHookInput } from "@anthropic-ai/claude-agent-sdk";

const deployGuard: HookCallback = async (input) => {
  if (input.hook_event_name !== "PreToolUse") return {};
  const preInput = input as PreToolUseHookInput;
  if (preInput.tool_name !== "Bash") return {};

  const cmd = (preInput.tool_input as any)?.command as string;

  // Block production deployments on Friday afternoons
  const now = new Date();
  if (now.getDay() === 5 && now.getHours() >= 14) {
    if (cmd.includes("deploy") && cmd.includes("production")) {
      return {
        systemMessage: "Production deployments are blocked on Friday afternoons.",
        hookSpecificOutput: {
          hookEventName: "PreToolUse",
          permissionDecision: "deny",
          permissionDecisionReason: "No Friday afternoon production deploys"
        }
      };
    }
  }

  return {};
};

for await (const message of query({
  prompt: `Deploy the staging branch to production:
1. Run the full test suite
2. Build the production bundle
3. Deploy to staging first and run smoke tests
4. If staging passes, deploy to production
5. Verify production health checks`,
  options: {
    allowedTools: ["Bash", "Read", "Glob"],
    permissionMode: "acceptEdits",
    hooks: {
      PreToolUse: [{ matcher: "Bash", hooks: [deployGuard] }]
    }
  }
})) {
  if ("result" in message) console.log(message.result);
}
```

<!-- level:advanced -->
## Enterprise Adoption Patterns

### Multi-Tenant Agent Platform

Build a platform where multiple users run agents with isolated contexts:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

interface TenantConfig {
  id: string;
  allowedPaths: string[];
  maxBudget: number;
  allowedTools: string[];
}

async function runTenantAgent(tenant: TenantConfig, prompt: string) {
  const pathGuard = async (input: any) => {
    if (input.hook_event_name !== "PreToolUse") return {};
    const filePath = (input.tool_input as any)?.file_path as string;
    if (filePath && !tenant.allowedPaths.some(p => filePath.startsWith(p))) {
      return {
        hookSpecificOutput: {
          hookEventName: "PreToolUse",
          permissionDecision: "deny" as const,
          permissionDecisionReason: `Tenant ${tenant.id} cannot access ${filePath}`
        }
      };
    }
    return {};
  };

  for await (const message of query({
    prompt,
    options: {
      cwd: `/tenants/${tenant.id}/workspace`,
      allowedTools: tenant.allowedTools,
      maxBudgetUsd: tenant.maxBudget,
      maxTurns: 25,
      permissionMode: "dontAsk",
      hooks: {
        PreToolUse: [{ hooks: [pathGuard] }]
      },
      env: {
        ...process.env,
        CLAUDE_AGENT_SDK_CLIENT_APP: `tenant-platform-${tenant.id}`
      }
    }
  })) {
    if (message.type === "result") {
      await logTenantUsage(tenant.id, message);
      return message;
    }
  }
}
```

### Agent-as-a-Service Architecture

Deploy agents as HTTP endpoints:

```typescript
import express from "express";
import { query } from "@anthropic-ai/claude-agent-sdk";

const app = express();
app.use(express.json());

app.post("/api/agent/analyze", async (req, res) => {
  const { prompt, projectPath } = req.body;

  try {
    const results: any[] = [];

    for await (const message of query({
      prompt,
      options: {
        cwd: projectPath,
        allowedTools: ["Read", "Glob", "Grep"],
        maxTurns: 15,
        maxBudgetUsd: 0.25,
        persistSession: false  // Don't persist -- API is stateless
      }
    })) {
      if (message.type === "result" && message.subtype === "success") {
        return res.json({
          success: true,
          result: message.result,
          cost: message.total_cost_usd,
          turns: message.num_turns
        });
      }
    }

    res.status(500).json({ success: false, error: "No result" });
  } catch (error) {
    res.status(500).json({ success: false, error: String(error) });
  }
});

app.listen(3000);
```

### Cost-Aware Agent Orchestrator

Implement budget management across multiple agent runs:

```typescript
import { query, SDKMessage } from "@anthropic-ai/claude-agent-sdk";

class AgentOrchestrator {
  private totalSpent = 0;
  private readonly globalBudget: number;

  constructor(budgetUsd: number) {
    this.globalBudget = budgetUsd;
  }

  async runTask(
    prompt: string,
    tools: string[],
    taskBudget?: number
  ): Promise<{ result: string; cost: number }> {
    const remaining = this.globalBudget - this.totalSpent;
    if (remaining <= 0) {
      throw new Error(`Global budget exhausted. Spent: $${this.totalSpent.toFixed(4)}`);
    }

    const budget = Math.min(taskBudget ?? remaining, remaining);

    for await (const message of query({
      prompt,
      options: {
        allowedTools: tools,
        maxBudgetUsd: budget,
        maxTurns: 20
      }
    })) {
      if (message.type === "result") {
        const cost = message.total_cost_usd;
        this.totalSpent += cost;

        if (message.subtype === "success") {
          return { result: message.result, cost };
        } else {
          throw new Error(`Task failed: ${message.subtype}`);
        }
      }
    }

    throw new Error("No result received");
  }

  get spent(): number { return this.totalSpent; }
  get remaining(): number { return this.globalBudget - this.totalSpent; }
}

// Usage
const orchestrator = new AgentOrchestrator(5.0);  // $5 global budget

const review = await orchestrator.runTask(
  "Review src/ for code quality", ["Read", "Glob", "Grep"], 1.0
);
console.log(`Review cost: $${review.cost.toFixed(4)}, remaining: $${orchestrator.remaining.toFixed(4)}`);

const fix = await orchestrator.runTask(
  "Fix the top 3 issues found", ["Read", "Edit", "Glob"], 2.0
);
console.log(`Fix cost: $${fix.cost.toFixed(4)}, remaining: $${orchestrator.remaining.toFixed(4)}`);
```
