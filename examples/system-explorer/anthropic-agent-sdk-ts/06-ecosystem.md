# Ecosystem & Integrations

<!-- level:beginner -->
## The MCP Ecosystem

The Agent SDK's primary extension mechanism is the **Model Context Protocol (MCP)**. MCP is an open standard created by Anthropic for connecting AI agents to external tools and data sources. Think of it as USB for AI -- a universal connector that lets your agent plug into databases, APIs, browsers, and more.

### What MCP Servers Are Available?

The MCP ecosystem includes hundreds of servers. Here are the most popular categories:

| Category | Example Servers | What They Enable |
|----------|----------------|------------------|
| **Version Control** | GitHub, GitLab | PR reviews, issue management, repo search |
| **Databases** | PostgreSQL, SQLite, MySQL | Natural language database queries |
| **Cloud Platforms** | AWS, GCP, Azure | Cloud resource management |
| **Communication** | Slack, Discord, Email | Sending notifications and messages |
| **Browsers** | Playwright, Puppeteer | Web automation, scraping, testing |
| **File Systems** | Filesystem, S3 | File management beyond local disk |
| **Search** | Brave Search, Google | Web search capabilities |
| **Documentation** | Notion, Confluence | Reading and writing documentation |
| **Monitoring** | Datadog, PagerDuty | Checking metrics and alerts |

### Connecting an MCP Server

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

// Connect the Playwright MCP server for browser automation
for await (const message of query({
  prompt: "Open example.com and describe what you see",
  options: {
    mcpServers: {
      playwright: {
        command: "npx",
        args: ["@playwright/mcp@latest"]
      }
    },
    allowedTools: ["mcp__playwright__*"]
  }
})) {
  if (message.type === "result" && message.subtype === "success") {
    console.log(message.result);
  }
}
```

## Cloud Provider Support

The Agent SDK works with multiple cloud AI providers, not just Anthropic's direct API:

### Amazon Bedrock

```bash
export CLAUDE_CODE_USE_BEDROCK=1
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
```

### Google Vertex AI

```bash
export CLAUDE_CODE_USE_VERTEX=1
export GOOGLE_CLOUD_PROJECT=your-project
export GOOGLE_CLOUD_REGION=us-central1
```

### Microsoft Azure AI Foundry

```bash
export CLAUDE_CODE_USE_FOUNDRY=1
# Configure Azure credentials
```

This means you can use the Agent SDK in environments where direct Anthropic API access is not available, routing through your existing cloud provider instead.

## Related Anthropic Tools

| Tool | Relationship to Agent SDK |
|------|--------------------------|
| **Claude Code CLI** | Same capabilities, interactive terminal interface. The SDK is the programmatic version of the CLI. |
| **Anthropic SDK** (`@anthropic-ai/sdk`) | Lower-level API client. Agent SDK builds on top of this. |
| **Claude.ai** | Web interface for Claude. Different product, same underlying model. |

<!-- level:intermediate -->
## Integration Patterns

### GitHub Integration

The GitHub MCP server is one of the most commonly used integrations:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

// Full GitHub integration with issue creation
for await (const message of query({
  prompt: `Review the codebase for security issues.
For each issue found:
1. Create a GitHub issue with the label "security"
2. Include the file path, line numbers, and suggested fix
3. Assign severity: critical, high, medium, or low`,
  options: {
    mcpServers: {
      github: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-github"],
        env: { GITHUB_TOKEN: process.env.GITHUB_TOKEN }
      }
    },
    allowedTools: [
      "Read", "Grep", "Glob",
      "mcp__github__list_issues",
      "mcp__github__create_issue",
      "mcp__github__search_code"
    ]
  }
})) {
  if ("result" in message) console.log(message.result);
}
```

### Database Integration

Connect to databases for natural language querying:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "How many users signed up last week? Break down by day and source.",
  options: {
    mcpServers: {
      postgres: {
        command: "npx",
        args: [
          "-y",
          "@modelcontextprotocol/server-postgres",
          process.env.DATABASE_URL!
        ]
      }
    },
    allowedTools: ["mcp__postgres__query"]  // Read-only -- no write access
  }
})) {
  if (message.type === "result" && message.subtype === "success") {
    console.log(message.result);
  }
}
```

### Slack Notifications via Hooks

Integrate Slack notifications without a full MCP server:

```typescript
import { query, HookCallback, NotificationHookInput } from "@anthropic-ai/claude-agent-sdk";

const slackNotifier: HookCallback = async (input, toolUseID, { signal }) => {
  const notification = input as NotificationHookInput;

  try {
    await fetch(process.env.SLACK_WEBHOOK_URL!, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: `Agent update: ${notification.message}`
      }),
      signal
    });
  } catch (error) {
    // Don't block the agent if Slack is down
  }

  return {};
};

for await (const message of query({
  prompt: "Run the deployment pipeline",
  options: {
    allowedTools: ["Bash", "Read", "Glob"],
    hooks: {
      Notification: [{ hooks: [slackNotifier] }]
    }
  }
})) {
  // ...
}
```

### Plugin System

The SDK supports plugins for extending functionality:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Use the custom linter to check code quality",
  options: {
    plugins: [
      { type: "local", path: "./plugins/custom-linter" },
      { type: "local", path: "/shared/plugins/team-tools" }
    ]
  }
})) {
  // Plugins add custom commands, agents, and MCP servers
}
```

### .mcp.json Configuration File

For project-wide MCP server configuration that is version-controlled:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", "${DATABASE_URL}"]
    },
    "docs": {
      "type": "http",
      "url": "https://docs.mycompany.com/mcp"
    }
  }
}
```

Place this in your project root and the SDK loads it automatically.

### CLAUDE.md for Project Context

Create a `CLAUDE.md` or `.claude/CLAUDE.md` file to give agents project-specific knowledge:

```markdown
# Project: MyApp

## Architecture
- Express.js backend in src/server/
- React frontend in src/client/
- PostgreSQL database, migrations in db/migrations/

## Coding Standards
- Use TypeScript strict mode
- All functions must have JSDoc comments
- Error handling: use Result<T, E> pattern
- Tests: co-locate with source files as *.test.ts

## Common Commands
- `npm test` -- run all tests
- `npm run lint` -- lint with ESLint
- `npm run build` -- production build
```

To load this, use the `claude_code` preset and project settings:

```typescript
options: {
  systemPrompt: { type: "preset", preset: "claude_code" },
  settingSources: ["project"]
}
```

<!-- level:advanced -->
## Building Custom MCP Servers

### In-Process Server with Multiple Tools

```typescript
import { tool, createSdkMcpServer, query } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";

// Tool 1: Customer lookup
const lookupCustomer = tool(
  "lookup_customer",
  "Look up a customer by email or ID",
  {
    query: z.string().describe("Email address or customer ID"),
    type: z.enum(["email", "id"]).default("email")
  },
  async (args) => {
    const customer = args.type === "email"
      ? await db.customers.findByEmail(args.query)
      : await db.customers.findById(args.query);

    if (!customer) {
      return { content: [{ type: "text", text: "Customer not found" }], isError: true };
    }
    return { content: [{ type: "text", text: JSON.stringify(customer, null, 2) }] };
  },
  { annotations: { readOnlyHint: true } }
);

// Tool 2: Create support ticket
const createTicket = tool(
  "create_ticket",
  "Create a support ticket in the ticketing system",
  {
    customerId: z.string(),
    title: z.string().max(200),
    description: z.string(),
    priority: z.enum(["low", "medium", "high", "urgent"]),
    category: z.enum(["billing", "technical", "account", "other"])
  },
  async (args) => {
    const ticket = await ticketingSystem.create({
      customer_id: args.customerId,
      title: args.title,
      description: args.description,
      priority: args.priority,
      category: args.category
    });
    return {
      content: [{
        type: "text",
        text: `Ticket created: ${ticket.id} (${ticket.url})`
      }]
    };
  }
);

// Tool 3: Image analysis (returning non-text content)
const fetchScreenshot = tool(
  "fetch_screenshot",
  "Capture a screenshot of a URL for visual analysis",
  { url: z.string().url() },
  async (args) => {
    const buffer = await screenshotService.capture(args.url);
    return {
      content: [{
        type: "image",
        data: buffer.toString("base64"),
        mimeType: "image/png"
      }]
    };
  },
  { annotations: { readOnlyHint: true, openWorldHint: true } }
);

// Bundle into a server
const supportServer = createSdkMcpServer({
  name: "support",
  version: "2.0.0",
  tools: [lookupCustomer, createTicket, fetchScreenshot]
});
```

### Connecting to External MCP Servers with Authentication

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

// OAuth2 flow completed externally
const accessToken = await oauthClient.getAccessToken();

for await (const message of query({
  prompt: "List my recent Jira tickets and summarize their status",
  options: {
    mcpServers: {
      // HTTP transport with OAuth bearer token
      jira: {
        type: "http",
        url: "https://jira.company.com/mcp",
        headers: {
          Authorization: `Bearer ${accessToken}`
        }
      },
      // SSE transport for streaming updates
      monitoring: {
        type: "sse",
        url: "https://monitoring.internal/mcp/sse",
        headers: {
          "X-API-Key": process.env.MONITORING_API_KEY!
        }
      }
    },
    allowedTools: ["mcp__jira__*", "mcp__monitoring__*"]
  }
})) {
  // ...
}
```

### Dynamic MCP Server Management

Add and remove MCP servers at runtime:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

async function* inputStream() {
  yield { type: "user" as const, session_id: "", message: {
    role: "user" as const,
    content: [{ type: "text" as const, text: "Start analyzing" }]
  }, parent_tool_use_id: null };
}

const q = query({
  prompt: inputStream(),
  options: { allowedTools: ["Read", "Glob"] }
});

// Start consuming messages
const iterator = q[Symbol.asyncIterator]();

// After initialization, dynamically add an MCP server
const result = await q.setMcpServers({
  github: {
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-github"],
    env: { GITHUB_TOKEN: process.env.GITHUB_TOKEN! }
  }
});
console.log("Added servers:", result);

// Check MCP server status
const status = await q.mcpServerStatus();
for (const server of status) {
  console.log(`${server.name}: ${server.status}`);
}

// Reconnect a failing server
await q.reconnectMcpServer("github");

// Toggle a server on/off
await q.toggleMcpServer("github", false);  // Disable
await q.toggleMcpServer("github", true);   // Re-enable
```

### Settings Sources and Configuration Hierarchy

The SDK can load filesystem-based settings at multiple levels:

```typescript
options: {
  settingSources: ["user", "project", "local"]
  //               ^        ^          ^
  //               |        |          +-- .claude/settings.local.json (gitignored)
  //               |        +-- .claude/settings.json (version controlled)
  //               +-- ~/.claude/settings.json (global user prefs)
}
```

Precedence (highest to lowest):
1. Programmatic options (always win)
2. Local settings
3. Project settings
4. User settings

For CI/CD, use only project settings for consistency:

```typescript
options: {
  settingSources: ["project"]  // Only team-shared config
}
```

For SDK-only applications, skip all filesystem settings:

```typescript
options: {
  // settingSources defaults to [] -- no filesystem dependency
  // Define everything programmatically
}
```
