---
name: learning-platform
description: "Create structured interactive learning platforms for any field or subject. Use this skill whenever the user wants to build a learning site, educational course collection, study guide platform, or knowledge base about ANY topic — psychology, physics, history, cooking, music theory, programming, medicine, etc. Also use when the user wants to add topics to an existing learning platform, propose new topics, or generate educational content in the structured 6-content-per-topic format. Trigger on phrases like 'create a course about', 'build a learning platform', 'teach me about [broad field]', 'make an educational site', 'add a topic about', 'what topics should I learn next', or any request to generate structured educational material for a broad field."
license: Apache-2.0
metadata:
  author: cyyeh
---

# Learning Platform Generator

Create structured, interactive learning platforms for any field — modeled after the [business-101](https://github.com/cyyeh/business-101) architecture: a single-page app (SPA) that dynamically renders markdown content and interactive HTML tools, with no build step required.

## How the Platform Works

The platform is a static site powered by a single `index.html` SPA. The `README.md` acts as the database — the SPA parses it at runtime to discover all topics and their content files. Each topic gets a folder under `src/` with exactly **6 content files** covering different learning angles. The only external dependency is [marked.js](https://github.com/markedjs/marked) for markdown rendering.

```
<cwd>/
└── platform-name/          # New directory created inside CWD
    ├── index.html          # SPA shell (from template)
    ├── README.md           # Topic registry — the SPA parses this
├── Makefile            # Local preview (make serve)
├── .nojekyll           # For GitHub Pages
└── src/
    ├── learning-roadmap.md       # Suggested learning order
    ├── glossary.md               # Key terms table
    ├── <topic-folder>/           # One folder per topic
    │   ├── <topic>_analysis.md       # In-depth professional analysis
    │   ├── <topic>_guide.md          # Beginner-friendly plain language guide
    │   ├── <topic>_cases.md          # Real-world case studies
    │   ├── <topic>_interactive.html  # Self-contained interactive HTML tool
    │   ├── <topic>_quiz.md           # Practice questions & self-assessment
    │   └── <topic>_resources.md      # Further learning resources
    └── cross-topic/              # Cross-topic integration analyses
        └── <case-name>.md
```

The SPA provides: hash-based routing, tabbed content viewer per topic, full-text search across all markdown, glossary with search integration, responsive card grid, and iframe embedding for interactive HTML tools.

## Two Modes

**Auto-detect**: If no learning platform directory (containing `index.html` + `README.md` with topic structure) exists in the current working directory → **Create mode**. If one exists and the user's request targets it → **Expand mode**.

---

## Create Mode

### Step 1: Gather Requirements

Ask the user (skip what's already clear from their request):

1. **Field/subject**: What field? (e.g., "psychology", "classical physics", "wine tasting")
2. **Language**: What language for content? (default: English)
3. **Audience level**: Target audience? (beginners, intermediate, advanced, mixed)
4. **External sources**: Any specific materials (URLs, papers, textbooks) to incorporate? Or all from general knowledge?
5. **Scope**: How many initial topics? (suggest 5-8 for a solid start)
6. **Project name**: Platform directory name — a kebab-case slug derived from the subject (e.g., "psychology-101", "wine-tasting-guide"). This becomes the new directory created inside the current working directory to hold all platform content.

### Step 2: Present Curriculum Plan for Approval

Before generating any content, present a structured plan:

```markdown
## Proposed Curriculum: [Platform Name]

### Learning Roadmap
Suggested order with brief rationale for the sequence.

### Initial Topics (N topics)
For each topic:
- **Topic Name** — 1-sentence scope description
- **Interactive Tool Idea** — What the HTML interactive will do

### Cross-Topic Analyses (2-3)
- **Case Name** — Which topics it connects

### Glossary Scope
Estimated number of terms, categories.

### Color Scheme
Proposed colors that match the field's aesthetic.
```

Wait for approval. Iterate until the user is satisfied. Only then proceed to generation.

### Step 3: Generate Platform

Once the plan is approved, create a new directory named after the project (e.g., `psychology-101/`) inside the current working directory. **All generated files go inside this directory.** Then generate in this order:

1. **index.html** — Read the SPA template from `assets/index-template.html` in this skill's directory. Customize the `CONFIG` object and all `__PLACEHOLDER__` strings:
   - Platform title, subtitle, favicon SVG
   - Color scheme (warm for humanities, cool for sciences, earthy for nature topics, etc.)
   - All language strings (tab labels, search placeholder, loading text, error text, disclaimer, badges)
   - Content type detection keywords in `CONFIG.keywords` matching the language
   - Footer links
   - Section headers matching what you'll use in README.md

2. **Makefile**:
   ```makefile
   .PHONY: serve
   serve:
   	python3 -m http.server 8000
   ```

3. **.nojekyll** — Empty file

4. **README.md** — Exact format the SPA parser expects:
   ```markdown
   # platform-name

   > Disclaimer about AI-generated content...

   Description.

   ## Topics

   ### Topic Name

   - [Topic - In-Depth Analysis](src/topic-name/topic-name_analysis.md) — Professional analysis covering...
   - [Topic - Beginner Guide](src/topic-name/topic-name_guide.md) — Plain language explanation...
   - [Topic - Interactive Tools](src/topic-name/topic-name_interactive.html) — Interactive visualization...
   - [Topic - Case Studies](src/topic-name/topic-name_cases.md) — Real-world cases...
   - [Topic - Practice Quiz](src/topic-name/topic-name_quiz.md) — Self-assessment...
   - [Topic - Further Resources](src/topic-name/topic-name_resources.md) — Books, courses...

   ## Cross-Topic Analysis

   ### Case Name
   - [Case Analysis](src/cross-topic/case-name.md) — Description...
   ```

5. **src/learning-roadmap.md** — Structured learning path with suggested order and connections

6. **src/glossary.md** — Terms table by category:
   ```markdown
   # Glossary
   ## Category
   | Term | English | Definition |
   |------|---------|------------|
   ```

7. **Topic content** — For each topic, generate all 6 files. Read `references/content-guidelines.md` for detailed instructions on each content type.

8. **Cross-topic analyses** — Markdown files synthesizing insights across multiple topics

### Generation Pace

Generate topics one at a time, completing all 6 files before moving to the next. After 2-3 topics, check with the user that the style and depth match expectations before continuing.

---

## Expand Mode

### Detect Existing Platform

Read `README.md` and `index.html` to understand: existing topics, language, naming conventions, content style.

### Three Expand Actions

**1. Add specific topic(s)** — User says "add a topic about X"
- Generate the topic folder with all 6 content files
- Append to README.md with the new topic entry (matching existing format exactly)
- Update glossary.md with relevant new terms
- Optionally update learning-roadmap.md to place the new topic

**2. Propose topics** — User says "what should I learn next?" or "suggest more topics"
- Analyze existing topics to understand coverage and gaps
- Identify natural next steps, complementary areas, and missing foundations
- Present 5-10 suggested topics with brief descriptions and rationale for each
- Let the user pick which ones to generate

**3. Add cross-topic analysis** — User wants a case spanning multiple existing topics
- Generate cross-topic markdown
- Append to README.md cross-topic section

### Updating README.md

Append entries in the exact format the SPA parser expects. Match whatever section headers and keyword conventions the existing platform uses. The parser relies on:
- `##` headers as section markers
- `###` headers as topic names
- `- [Link Text](path) — description` as content links
- Content type detection via keywords in link text/URL (or `.html` extension for interactive)

---

## Key Principles

### Content Quality
- **Analysis**: Genuinely teaches — frameworks, models, expert perspectives, nuanced discussion. Not Wikipedia summaries.
- **Guide**: Vivid everyday analogies. Makes concepts click for someone with zero background.
- **Cases**: Real events with dates, names, numbers, source references. For fields without traditional cases, use historical discoveries, famous experiments, or worked examples.
- **Interactive**: Genuinely useful tools, not decorative. Read `references/content-guidelines.md` for patterns.
- **Quiz**: Mixed question types with detailed answer explanations.
- **Resources**: Real, currently available books/courses/podcasts with difficulty ratings.

### Interactive HTML — Must Be Self-Contained
- All CSS in `<style>`, all JS in `<script>`, all data in JS variables
- No external dependencies unless truly necessary
- Works inside an iframe, responsive design
- 3-5 interactive tools per page using tab navigation
- Include hints/tooltips for discoverability

### Adapting to the Field

| Field Type | Analysis Focus | Guide Approach | Interactive Ideas |
|-----------|---------------|----------------|-------------------|
| Sciences | Theories, formulas, experiments | Analogies, visualizations | Simulators, calculators |
| Humanities | Schools of thought, debates | Stories, relatable scenarios | Timelines, concept maps |
| Practical | Techniques, best practices | Step-by-step walkthroughs | Builders, planners |
| Arts | History, theory, criticism | Sensory descriptions | Visual/audio explorers |

### File Naming
- Topic folders: `kebab-case` (e.g., `cognitive-biases/`)
- Files: `topic-name_analysis.md`, `topic-name_guide.md`, `topic-name_cases.md`, `topic-name_interactive.html`, `topic-name_quiz.md`, `topic-name_resources.md`
- Cross-topic: `case-name.md`
- For non-English platforms, you may use localized folder/file names if the user prefers — just ensure the README links match exactly
