# Search Strategies by Query Type

Research strategies and example WebSearch queries for each type of user query. Use these as templates -- adapt the specific terms to match what the user is looking for.

## 1. Specific System Queries

**Pattern:** User names a system directly -- "Kafka", "Redis", "Terraform".

**How to handle:**
- Confirm the system: "You want to explore Apache Kafka?"
- Gather basic metadata (language, license, latest version, GitHub stars)
- Suggest proceeding to system-analyzer for a deep dive
- Only search for alternatives if the user asks

**Example searches:**
- `"Apache Kafka" latest version release 2025 2026`
- `"Apache Kafka" GitHub stars contributors`
- `"Apache Kafka" alternatives comparison`

## 2. Category Queries

**Pattern:** User names a software category -- "message queues", "databases", "CI/CD tools".

**How to handle:**
- Start with known leaders in the category from built-in knowledge
- Search for recent entrants and shifts in adoption
- Compare on the dimensions that matter for that category

**Example searches:**
- `best message queue systems 2025 2026 comparison`
- `message queue alternatives to Kafka RabbitMQ`
- `"message broker" open source emerging new`
- `message queue benchmark comparison throughput latency`

**Key dimensions by common categories:**

| Category | Compare on |
|----------|-----------|
| Databases | Query language, consistency model, scaling model, hosted options |
| Message queues | Throughput, latency, ordering guarantees, delivery semantics |
| CI/CD | Pipeline syntax, self-hosted vs cloud, plugin ecosystem, speed |
| Observability | Metrics vs traces vs logs, storage backend, cost model |
| Container orchestration | Complexity, managed options, ecosystem maturity |
| Search engines | Index speed, query features, operational complexity |

## 3. Requirement Queries

**Pattern:** User describes a need -- "I need real-time analytics", "something for container orchestration".

**How to handle:**
1. Extract keywords and map to one or more software categories
2. If the mapping is ambiguous, ask one clarifying question with options
3. Once the category is clear, search as a category query (see above)

**Requirement-to-category mapping examples:**
- "real-time data processing" -> stream processing (Kafka Streams, Flink, Spark Streaming)
- "store user sessions" -> key-value store or cache (Redis, Memcached, DynamoDB)
- "full-text search" -> search engine (Elasticsearch, Meilisearch, Typesense)
- "schedule background jobs" -> task queue (Celery, Sidekiq, BullMQ)
- "deploy microservices" -> container orchestration (Kubernetes, Nomad, ECS)

**Example searches:**
- `real-time stream processing frameworks comparison 2025 2026`
- `best tool for [requirement] open source`
- `[requirement] software comparison production ready`

## 4. Comparison Queries

**Pattern:** User wants a head-to-head -- "Kafka vs RabbitMQ", "PostgreSQL vs MySQL".

**How to handle:**
- Structure as a direct comparison between the named systems
- Search for recent benchmarks and migration stories
- Highlight where each system wins and loses
- Optionally suggest a third alternative the user may not have considered

**Example searches:**
- `"Kafka vs RabbitMQ" comparison 2025 2026`
- `Kafka RabbitMQ benchmark throughput latency`
- `"migrated from RabbitMQ to Kafka" OR "migrated from Kafka to RabbitMQ"`
- `Kafka vs RabbitMQ when to use which`

**Comparison structure:**
- Shared: What both systems do well
- System A wins: Where the first system is clearly better
- System B wins: Where the second system is clearly better
- Decision criteria: What factors should drive the choice

## 5. "Best for X" Queries

**Pattern:** User asks for a recommendation -- "best database for time series", "fastest message queue".

**How to handle:**
1. Identify the use case constraint (time series, fastest, simplest, cheapest)
2. Search for systems optimized for that constraint
3. Present 3-5 options ranked by how well they fit the constraint
4. Note trade-offs -- the "best" for one dimension often sacrifices another

**Example searches:**
- `best time series database comparison 2025 2026`
- `fastest message queue benchmark low latency`
- `"best database for" [use case] production`
- `[use case] database recommendations site:reddit.com OR site:news.ycombinator.com`

**Common "best for" mappings:**

| "Best for..." | Look at |
|---------------|---------|
| Time series | InfluxDB, TimescaleDB, QuestDB, ClickHouse |
| Graph data | Neo4j, Amazon Neptune, ArangoDB, Memgraph |
| Low latency | Redis, Dragonfly, KeyDB, Hazelcast |
| Simplicity | SQLite, DuckDB, Bun SQLite, LiteFS |
| Scale | CockroachDB, ScyllaDB, YugabyteDB, TiDB |
| Cost | Open-source self-hosted options first, then managed tiers |

## 6. Adjacent Category Expansion

**Problem:** Searching only within the user's stated category misses established platforms from broader or sibling categories that have expanded into this space. Example: searching "LLM tracing platforms" misses MLflow (an MLOps platform that added LLM tracing) and Datadog (an APM platform that added LLM monitoring).

**How to handle:**
1. Identify the category hierarchy for the user's query
2. Search broader parent and sibling categories with the target capability
3. Search for known platforms from adjacent spaces that likely added the capability

**Step 1: Map the category hierarchy**

For any target category, identify:
- **Parent category**: The broader space it belongs to (e.g., "LLM tracing" → "ML observability" → "developer platforms")
- **Sibling categories**: Related spaces at the same level (e.g., "LLM tracing" siblings = "ML experiment tracking", "APM/observability", "AI development platforms")

Common hierarchy examples:

| Target Category | Parent | Siblings |
|----------------|--------|----------|
| LLM tracing | ML observability, MLOps | APM tools, AI dev platforms, ML experiment tracking |
| Stream processing | Data infrastructure | ETL tools, message queues, data pipelines |
| Container orchestration | Infrastructure management | PaaS, serverless platforms, VM orchestration |
| CI/CD | Developer tools | Build systems, deployment platforms, GitOps tools |
| Vector database | Database | Search engines, ML feature stores, embedding services |

**Step 2: Search broader categories**

Example searches for "LLM tracing":
- `"MLOps platform" LLM tracing observability 2025 2026`
- `"ML platform" LLM observability features`
- `"APM" OR "application monitoring" LLM tracing support`
- `"developer platform" GenAI observability`

**Step 3: Search for known platforms crossing over**

For each adjacent category, identify 2-3 well-known platforms and check if they've added the target capability:
- `"MLflow" LLM tracing features`
- `"Datadog" LLM monitoring observability`
- `"Weights and Biases" LLM tracing`
- `"New Relic" AI observability`

**Why this matters:** Comparison listicles are written by companies *within* a category and benchmark against direct competitors. They systematically exclude platforms from adjacent categories, even when those platforms have competitive features. This round corrects that source bias.

## 7. Blind Spot Detection

**Problem:** Even after direct and adjacent searches, gaps remain. This round actively hunts for them.

**Strategy 1: Reverse search from top results**
- `"alternatives to [top result]" [year]` -- surfaces competitors clustered differently
- `"[top result] vs" [year]` -- comparison articles name the challenger

**Strategy 2: Community-sourced recommendations**
- `"[category] recommendations site:reddit.com" [year]`
- `"[category] site:news.ycombinator.com" [year]`
- `"what do you use for [capability]" site:reddit.com`

Practitioners on Reddit/HN mention tools they actually use, which often differs from what listicle articles feature. These sources surface tools with strong adoption but low marketing presence.

**Strategy 3: Self-audit question**
After assembling your list, ask: "Is there a well-known, widely-adopted platform in a related space that *probably* has this capability but isn't on my list?" If the answer is yes, search to confirm or exclude. Common examples:
- For any monitoring category: check Datadog, Grafana, New Relic
- For any ML category: check MLflow, W&B, SageMaker
- For any data category: check Databricks, Snowflake, dbt
- For any developer tool category: check JetBrains, VS Code extensions, GitHub-native tools

## General Search Tips

- **Add year filters** (`2025 2026`) to avoid outdated comparisons
- **Check community signals** on Reddit, HackerNews, and GitHub discussions for real-world adoption feedback
- **Look for migration stories** -- "migrated from X to Y" reveals practical trade-offs that benchmarks miss
- **Verify GitHub activity** -- a project with many stars but no recent commits may be abandoned
- **Cross-reference multiple sources** -- no single benchmark or blog post tells the full story
- **Watch for source bias** -- comparison articles from vendors highlight their own competitors and omit platforms from adjacent categories. Always cross-reference with at least one community source (Reddit, HN) and one adjacent-category search
