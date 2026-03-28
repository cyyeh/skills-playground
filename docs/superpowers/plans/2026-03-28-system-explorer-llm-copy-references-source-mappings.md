# System Explorer: LLM Copy, References & Source Mappings — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add three features to system-explorer generated HTML courses: a per-page "Copy as Markdown" button with LLM-friendly formatting, inline contextual links with per-page reference footers, and source-annotated code blocks with GitHub links.

**Architecture:** Enrich the analysis.md format with new structured fields (references metadata, source annotations, GitHub/Tag metadata). Update system-to-course reference files (page-templates.md, interactive-elements.md, design-system.md) with new HTML/CSS/JS patterns. Update system-analyzer to produce the enriched format. All changes are to skill instruction/reference files — no application code.

**Tech Stack:** Markdown (skill instructions), HTML/CSS/JS (reference templates)

---

## File Map

| Action | File | Responsibility |
|--------|------|---------------|
| Modify | `skills/system-explorer/system-analyzer/references/analysis-template.md` | Add GitHub/Tag metadata fields, per-section references blocks, source annotation docs |
| Modify | `skills/system-explorer/system-analyzer/SKILL.md` | Instruct analyzer to produce references, source annotations, inline links |
| Modify | `skills/system-explorer/system-to-course/references/design-system.md` | Add CSS for copy-markdown button, reference footer, source-annotated code blocks, external links |
| Modify | `skills/system-explorer/system-to-course/references/page-templates.md` | Add copy-markdown button to content page template, reference footer section, page-context metadata |
| Modify | `skills/system-explorer/system-to-course/references/interactive-elements.md` | Add source-annotated code block element, reference footer element, copy-as-markdown element |
| Modify | `skills/system-explorer/system-to-course/SKILL.md` | Instruct course generator to parse new fields and render new elements |

---

### Task 1: Add GitHub/Tag metadata and references to analysis-template.md

**Files:**
- Modify: `skills/system-explorer/system-analyzer/references/analysis-template.md:6-16` (Metadata section)
- Modify: `skills/system-explorer/system-analyzer/references/analysis-template.md:33-34` (after first section, add references docs)

- [ ] **Step 1: Add GitHub and Tag fields to Metadata section**

In `skills/system-explorer/system-analyzer/references/analysis-template.md`, replace the Metadata block (lines 8-16 inside the fenced code block) with:

````markdown
## Metadata
- **Name:** [System Name]
- **Category:** [e.g., Message Queue, Database, Container Orchestrator]
- **Official URL:** [link]
- **GitHub:** [org/repo, e.g., duckdb/duckdb]
- **Tag:** [latest stable tag, e.g., v1.5.1 — used for source code links]
- **License:** [license type]
- **Latest Version:** [version if found]
- **Analysis Date:** [YYYY-MM-DD]
````

- [ ] **Step 2: Add per-section references block documentation**

After the Metadata section closing `---` (line 17), add this new documentation section before `## Overview`:

````markdown
## Per-Section References

Each content section can include an optional references block as an HTML comment, placed immediately after the level tag. References link to authoritative external sources that support or expand on the section's content.

**Format:**
```markdown
## Architecture
<!-- level: intermediate -->
<!-- references:
- [Architecture Deep Dive](https://duckdb.org/docs/internals/overview) | official-docs
- [Push-Based Execution Paper](https://arxiv.org/abs/2106.00505) | paper
- [Storage Format Blog Post](https://duckdb.org/2024/07/storage) | blog
-->
```

**Reference types** (used for icon selection in HTML output):
- `official-docs` — Official documentation pages
- `paper` — Academic or research papers
- `blog` — Blog posts and articles
- `github` — GitHub repositories or specific source files
- `video` — Video content (conference talks, tutorials)
- `tutorial` — Step-by-step tutorial guides
- `community` — Community resources (forums, discussions, wikis)

**Rules:**
- Place the `<!-- references: ... -->` block immediately after the `<!-- level: ... -->` tag
- Each reference is a markdown link followed by `|` and a type label
- Include 2-5 references per section — quality over quantity
- Prefer official/primary sources over third-party summaries
- References are optional — omit the block if no authoritative sources exist for a section

## Inline Contextual Links

Within the content body, include standard markdown links to external sources where they add value:

- Link on **first mention** of a concept that has an authoritative external source
- Link **claims** that benefit from a primary source (benchmarks, design decisions)
- Prefer official documentation over third-party summaries
- Do not over-link — 2-4 inline links per section is typical

Example:
```markdown
DuckDB uses a [push-based execution model](https://duckdb.org/docs/internals/overview)
inspired by the approach described in Leis et al.'s
[Morsel-Driven Parallelism paper](https://db.in.tum.de/~leis/papers/morsels.pdf).
```
````

- [ ] **Step 3: Add source annotation documentation for code blocks**

After the inline links section added in Step 2, add:

````markdown
## Source Code Annotations

Code blocks that represent actual source code from the system's codebase (not tutorial/example code) should include source annotations as comment lines at the top of the block. These annotations are consumed by the HTML course generator to create file path headers and GitHub links.

**Format:**
```cpp
// source: src/parser/parser.cpp:142-168
// github: duckdb/duckdb
// tag: v1.5.1
unique_ptr<SQLStatement> Parser::ParseStatement() {
    auto token = Peek();
    switch (token.type) {
        case TokenType::SELECT:
            return ParseSelectStatement();
    }
}
```

**Annotation fields:**
- `// source: <file-path>:<start-line>-<end-line>` — Required for source-annotated blocks. File path relative to repo root. Line range is optional. A code block without `// source:` is treated as a regular code block (tutorial/example code).
- `// github: <org/repo>` — Optional. Overrides the Metadata-level GitHub field for this block.
- `// tag: <ref>` — Optional. Overrides the Metadata-level Tag field for this block.

**When to annotate:**
- Code extracted or adapted from the system's actual source code
- Configuration files from the system's repository
- NOT for tutorial/getting-started code that users would write themselves
- NOT for shell commands (pip install, docker run, etc.)

**Language-specific comment syntax:**
- C/C++/Java/Go/Rust/JS/TS: `// source: ...`
- Python/Ruby/Shell: `# source: ...`
- SQL: `-- source: ...`
- HTML/XML: `<!-- source: ... -->`
````

- [ ] **Step 4: Commit**

```bash
git add skills/system-explorer/system-analyzer/references/analysis-template.md
git commit -m "feat(system-explorer): add references, source annotations, and GitHub metadata to analysis template"
```

---

### Task 2: Update system-analyzer SKILL.md to produce enriched content

**Files:**
- Modify: `skills/system-explorer/system-analyzer/SKILL.md:78-79` (Phase 2 web research)
- Modify: `skills/system-explorer/system-analyzer/SKILL.md:82-98` (Phase 3 structured analysis)
- Modify: `skills/system-explorer/system-analyzer/SKILL.md:109-119` (Phase 4 review checklist)
- Modify: `skills/system-explorer/system-analyzer/SKILL.md:155-203` (Output Format)

- [ ] **Step 1: Add reference gathering to Phase 2 (Web Research)**

In `skills/system-explorer/system-analyzer/SKILL.md`, after line 79 (`- Comparison articles (X vs Y) for the trade-offs section`), add:

```markdown
- Source code file paths and structure (for source annotation in code blocks)
- Authoritative reference URLs for each section (official docs, papers, blog posts)
```

- [ ] **Step 2: Add enrichment instructions to Phase 3 (Structured Analysis)**

After line 98 (`- **Critical:** Every section MUST have a level comment tag...`), add:

```markdown

**References:** Each section should include a `<!-- references: ... -->` block after the level tag, listing 2-5 authoritative sources relevant to that section. See `references/analysis-template.md` for format and reference types.

**Inline links:** Include standard markdown links within the content body on first mention of concepts with authoritative external sources. Link claims that benefit from a primary source (benchmarks, architectural decisions, papers).

**Source annotations:** When including code blocks that represent actual source code from the system's codebase, annotate them with `// source:`, `// github:`, and `// tag:` metadata lines. See `references/analysis-template.md` for format. The Metadata section's GitHub and Tag fields provide default values.
```

- [ ] **Step 3: Add review items to Phase 4 checklist**

After line 119 (`8. **Section depth** — ...`), add:

```markdown
9. **References** — Does each section with substantial content have a `<!-- references: ... -->` block with 2-5 relevant sources? Are the URLs valid and the types correct?
10. **Source annotations** — Do code blocks showing actual source code have `// source:` annotations with valid file paths? Do the `// github:` and `// tag:` values match the Metadata section or override correctly?
11. **Inline links** — Are key concepts and claims linked to authoritative sources on first mention? Are there 2-4 inline links per section (not over-linked)?
```

- [ ] **Step 4: Update Output Format section with new Metadata fields**

In the Output Format section (around line 158), replace:

```markdown
## Metadata
- **Name:** [System Name]
- **Category:** [e.g., Message Queue, Database, Container Orchestrator]
- **Official URL:** [link]
- **GitHub:** [link if applicable]
- **License:** [license type]
- **Latest Version:** [version if found]
```

with:

```markdown
## Metadata
- **Name:** [System Name]
- **Category:** [e.g., Message Queue, Database, Container Orchestrator]
- **Official URL:** [link]
- **GitHub:** [org/repo, e.g., duckdb/duckdb]
- **Tag:** [latest stable tag, e.g., v1.5.1]
- **License:** [license type]
- **Latest Version:** [version if found]
```

- [ ] **Step 5: Commit**

```bash
git add skills/system-explorer/system-analyzer/SKILL.md
git commit -m "feat(system-explorer): instruct analyzer to produce references, source annotations, and inline links"
```

---

### Task 3: Add CSS styles for new elements to design-system.md

**Files:**
- Modify: `skills/system-explorer/system-to-course/references/design-system.md` (append after Code Block CSS section)

- [ ] **Step 1: Add external link icon CSS**

After the Code Block CSS section's closing `---` (after the copy button JS), add:

````markdown
## External Link Styling

Links to external URLs (used for inline contextual links and reference footers) get a visual indicator and open in new tabs.

```css
/* External link indicator */
a[target="_blank"]::after {
  content: " \2197";  /* ↗ */
  font-size: 0.75em;
  vertical-align: super;
  color: var(--color-text-muted);
  text-decoration: none;
  display: inline;
}
a[target="_blank"] {
  color: var(--color-accent);
  text-decoration: underline;
  text-decoration-color: var(--color-accent-light);
  text-underline-offset: 2px;
  transition: text-decoration-color var(--duration-fast) var(--ease-out);
}
a[target="_blank"]:hover {
  text-decoration-color: var(--color-accent);
}
```
````

- [ ] **Step 2: Add reference footer CSS**

After the external link section added in Step 1, add:

````markdown
## Reference Footer

Per-page reference section rendered above the prev/next navigation. Shows authoritative sources for the page content.

```css
/* Reference footer section */
.references-footer {
  max-width: var(--content-width);
  margin: var(--space-10) auto var(--space-4);
  padding: var(--space-6);
  background: var(--color-bg-warm);
  border-left: 3px solid var(--color-accent);
  border-radius: var(--radius-md);
}
.references-footer h3 {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: var(--space-4);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.references-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.reference-item {
  display: flex;
  align-items: baseline;
  gap: var(--space-3);
}
.reference-type-icon {
  font-size: var(--text-base);
  flex-shrink: 0;
  width: 1.5em;
  text-align: center;
}
.reference-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}
.reference-title {
  font-family: var(--font-body);
  font-size: var(--text-sm);
  font-weight: 600;
}
.reference-title a {
  color: var(--color-accent);
  text-decoration: none;
}
.reference-title a:hover {
  text-decoration: underline;
}
.reference-domain {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}
```
````

- [ ] **Step 3: Add source-annotated code block CSS**

After the reference footer section, add:

````markdown
## Source-Annotated Code Block

Extended code block with a file path header bar and GitHub link. Used for code blocks that have `// source:` annotations.

```css
/* Source-annotated code block */
.code-block-sourced .code-header {
  justify-content: flex-start;
  gap: var(--space-3);
}
.code-source-path {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: #A6ADC8;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.code-source-link {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: #6C7086;
  text-decoration: none;
  padding: 2px var(--space-2);
  border: 1px solid #45475A;
  border-radius: var(--radius-sm);
  white-space: nowrap;
  transition: all var(--duration-fast);
  display: flex;
  align-items: center;
  gap: var(--space-1);
}
.code-source-link:hover {
  color: #CDD6F4;
  border-color: #CDD6F4;
}

/* Source map summary */
.source-map {
  max-width: var(--content-width);
  margin: var(--space-6) auto;
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.source-map-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface);
  cursor: pointer;
  user-select: none;
  transition: background var(--duration-fast);
}
.source-map-header:hover {
  background: var(--color-bg-warm);
}
.source-map-header h3 {
  font-family: var(--font-display);
  font-size: var(--text-base);
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.source-map-toggle {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  transition: transform var(--duration-fast);
}
.source-map.open .source-map-toggle {
  transform: rotate(180deg);
}
.source-map-body {
  max-height: 0;
  overflow: hidden;
  transition: max-height var(--duration-normal) var(--ease-out);
}
.source-map.open .source-map-body {
  max-height: 500px;
}
.source-map-list {
  list-style: none;
  padding: var(--space-3) var(--space-4);
  margin: 0;
  border-top: 1px solid var(--color-border-light);
}
.source-map-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-2) 0;
  font-family: var(--font-mono);
  font-size: var(--text-xs);
}
.source-map-item a {
  color: var(--color-accent);
  text-decoration: none;
}
.source-map-item a:hover {
  text-decoration: underline;
}
.source-map-item .line-range {
  color: var(--color-text-muted);
}
.source-map-repo {
  padding: var(--space-2) var(--space-4) var(--space-3);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  border-top: 1px solid var(--color-border-light);
}
.source-map-repo a {
  color: var(--color-accent);
  text-decoration: none;
}
```
````

- [ ] **Step 4: Add copy-as-markdown button CSS**

After the source-annotated code block section, add:

````markdown
## Copy as Markdown Button

Per-page button in the page header that copies LLM-friendly markdown content of the page. Only appears on content pages (not index.html).

```css
/* Copy as Markdown button */
.copy-markdown-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-family: var(--font-body);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-secondary);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--space-1) var(--space-3);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
  white-space: nowrap;
}
.copy-markdown-btn:hover {
  color: var(--color-accent);
  border-color: var(--color-accent);
  background: var(--color-accent-light);
}
.copy-markdown-btn.copied {
  color: var(--color-success);
  border-color: var(--color-success);
  background: var(--color-success-light);
}
.copy-markdown-btn .btn-icon {
  font-size: var(--text-base);
  line-height: 1;
}
.copy-markdown-btn .btn-label {
  display: inline;
}

/* Mobile: icon only */
@media (max-width: 640px) {
  .copy-markdown-btn .btn-label {
    display: none;
  }
  .copy-markdown-btn {
    padding: var(--space-1) var(--space-2);
  }
}
```

**Placement:** Float right in the `.page-header`, aligned with the level badge and title.

```css
/* Page header layout with copy button */
.page-header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}
.page-header-content {
  flex: 1;
  min-width: 0;
}
```
````

- [ ] **Step 5: Commit**

```bash
git add skills/system-explorer/system-to-course/references/design-system.md
git commit -m "feat(system-explorer): add CSS for copy-markdown button, reference footer, source-annotated code blocks"
```

---

### Task 4: Update page-templates.md with new template elements

**Files:**
- Modify: `skills/system-explorer/system-to-course/references/page-templates.md:294-440` (Content Page Template)

- [ ] **Step 1: Add page-context metadata comment to content page template**

In `page-templates.md`, inside the content page template's `<head>` section (after the closing `</style>` tag, before `</head>`), add:

```html
  <!--
    PAGE CONTEXT METADATA — consumed by Copy as Markdown button.
    Values populated from analysis.md Metadata section.
  -->
  <!-- page-context:
    system: "[SYSTEM_NAME]"
    description: "[ONE_LINE_DESCRIPTION]"
    page: "[PAGE_TITLE]"
    level: "[LEVEL_LABEL]"
  -->
```

- [ ] **Step 2: Add copy-as-markdown button to page header**

Replace the existing page header block (lines 437-440):

```html
  <header class="page-header animate-in">
    <span class="page-level-badge [LEVEL_CLASS]">[LEVEL_LABEL]</span>
    <h1>[PAGE_TITLE]</h1>
  </header>
```

with:

```html
  <!-- ========================================
       PAGE HEADER (with Copy as Markdown button)
       ======================================== -->
  <header class="page-header animate-in">
    <div class="page-header-content">
      <span class="page-level-badge [LEVEL_CLASS]">[LEVEL_LABEL]</span>
      <h1>[PAGE_TITLE]</h1>
    </div>
    <button class="copy-markdown-btn" onclick="copyPageAsMarkdown()">
      <span class="btn-icon">&#x1F4CB;</span>
      <span class="btn-label">Copy as Markdown</span>
    </button>
  </header>
```

- [ ] **Step 3: Add reference footer section above prev/next navigation**

Before the prev/next navigation block (line 542), add:

```html
  <!-- ========================================
       REFERENCES FOOTER
       Only include if the source section had a <!-- references: ... --> block.
       Omit entirely if no references exist for this page.
       ======================================== -->
  <section class="references-footer">
    <h3>&#x1F4DA; References &amp; Resources</h3>
    <ul class="references-list">
      <!--
        Repeat for each reference in the section's references block.
        Map reference type to icon:
          official-docs -> &#x1F4C4;  (📄)
          paper         -> &#x1F4DC;  (📜)
          blog          -> &#x1F4F0;  (📰)
          github        -> &#x1F4BB;  (💻)
          video         -> &#x1F3A5;  (🎥)
          tutorial      -> &#x1F4D6;  (📖)
          community     -> &#x1F4AC;  (💬)
      -->
      <li class="reference-item">
        <span class="reference-type-icon">[TYPE_ICON]</span>
        <div class="reference-content">
          <span class="reference-title">
            <a href="[REFERENCE_URL]" target="_blank" rel="noopener noreferrer">[REFERENCE_TITLE]</a>
          </span>
          <span class="reference-domain">[DOMAIN_HINT]</span>
        </div>
      </li>
    </ul>
  </section>
```

- [ ] **Step 4: Add copy-as-markdown JS to the script block**

In the content page template's inline `<script>` block (line 558-562), add after the existing JS placeholders:

```javascript
    /* ==============================================
       COPY PAGE AS MARKDOWN
       Reads page-context metadata and converts DOM to
       LLM-friendly markdown for clipboard.
       ============================================== */
    function copyPageAsMarkdown() {
      // Read page context from HTML comment
      var html = document.documentElement.innerHTML;
      var ctxMatch = html.match(/<!-- page-context:\s*([\s\S]*?)-->/);
      var ctx = {};
      if (ctxMatch) {
        ctxMatch[1].split('\n').forEach(function(line) {
          var m = line.match(/(\w+):\s*"(.+)"/);
          if (m) ctx[m[1]] = m[2];
        });
      }

      // Build header
      var md = '# ' + (ctx.system || '') + ': ' + (ctx.page || document.title) + '\n';
      md += '> Source: ' + window.location.href + ' | Level: ' + (ctx.level || 'Unknown') + '\n';
      if (ctx.description) {
        md += '> This is the ' + ctx.page + ' section of an interactive course about '
            + ctx.system + ', ' + ctx.description + '.\n';
      }
      md += '\n';

      // Convert content area to markdown
      var content = document.querySelector('.content-area');
      if (content) {
        md += domToMarkdown(content);
      }

      md += '\n---\n*Generated by System Explorer*\n';

      navigator.clipboard.writeText(md).then(function() {
        var btn = document.querySelector('.copy-markdown-btn');
        var label = btn.querySelector('.btn-label');
        var origLabel = label.textContent;
        label.textContent = 'Copied!';
        btn.classList.add('copied');
        setTimeout(function() {
          label.textContent = origLabel;
          btn.classList.remove('copied');
        }, 2000);
      });
    }

    function domToMarkdown(el) {
      var md = '';
      el.childNodes.forEach(function(node) {
        if (node.nodeType === 3) {
          // Text node
          md += node.textContent;
          return;
        }
        if (node.nodeType !== 1) return;

        var tag = node.tagName.toLowerCase();

        // Headings
        if (/^h[1-6]$/.test(tag)) {
          var level = parseInt(tag[1]);
          md += '\n' + '#'.repeat(level) + ' ' + node.textContent.trim() + '\n\n';
          return;
        }

        // Paragraphs
        if (tag === 'p') {
          md += processInline(node) + '\n\n';
          return;
        }

        // Code blocks
        if (tag === 'div' && node.classList.contains('code-block')) {
          var langEl = node.querySelector('.code-lang');
          var lang = langEl ? langEl.textContent.trim().toLowerCase() : '';
          var sourceEl = node.querySelector('.code-source-path');
          var pre = node.querySelector('pre');
          if (sourceEl) {
            md += '*File: ' + sourceEl.textContent.trim() + '*\n';
          }
          md += '```' + lang + '\n' + (pre ? pre.textContent.trim() : '') + '\n```\n\n';
          return;
        }

        // Callout boxes -> blockquotes
        if (tag === 'div' && node.classList.contains('callout')) {
          var type = 'Note';
          if (node.classList.contains('callout-insight')) type = 'Insight';
          if (node.classList.contains('callout-tip')) type = 'Tip';
          if (node.classList.contains('callout-warning')) type = 'Warning';
          var body = node.querySelector('.callout-content');
          md += '> **' + type + ':** ' + (body ? body.textContent.trim() : '') + '\n\n';
          return;
        }

        // Concept cards -> list items
        if (tag === 'div' && node.classList.contains('concept-cards')) {
          node.querySelectorAll('.concept-card').forEach(function(card) {
            var title = card.querySelector('.card-title');
            var desc = card.querySelector('.card-desc');
            var expanded = card.querySelector('.card-expanded');
            md += '- **' + (title ? title.textContent.trim() : '') + '**: ';
            md += (desc ? desc.textContent.trim() : '');
            if (expanded && expanded.textContent.trim()) {
              md += ' ' + expanded.textContent.trim();
            }
            md += '\n';
          });
          md += '\n';
          return;
        }

        // Architecture diagrams -> descriptive list
        if (tag === 'div' && node.classList.contains('arch-diagram')) {
          var title = node.querySelector('.arch-title');
          if (title) md += '**' + title.textContent.trim() + '**\n\n';
          node.querySelectorAll('.arch-component').forEach(function(comp) {
            var label = comp.querySelector('.arch-component-label');
            var brief = comp.querySelector('.arch-component-brief');
            var details = comp.dataset.details || '';
            md += '- **' + (label ? label.textContent.trim() : '') + '** ';
            md += '(' + (brief ? brief.textContent.trim() : '') + ')';
            if (details) md += ': ' + details;
            md += '\n';
          });
          md += '\n';
          return;
        }

        // Performance gauges -> text
        if (tag === 'div' && node.classList.contains('perf-gauges')) {
          node.querySelectorAll('.perf-gauge').forEach(function(gauge) {
            var name = gauge.querySelector('.perf-name');
            var value = gauge.querySelector('.perf-value');
            var fill = gauge.querySelector('.perf-fill');
            var pct = fill ? fill.dataset.width + '%' : '';
            md += '- ' + (name ? name.textContent.trim() : '') + ': ';
            md += (value ? value.textContent.trim() : '') + ' (' + pct + ')\n';
          });
          md += '\n';
          return;
        }

        // Glossary terms -> inline with definition
        if (tag === 'span' && node.classList.contains('glossary-term')) {
          var def = node.dataset.definition;
          md += node.textContent.trim();
          if (def) md += ' (' + def + ')';
          return;
        }

        // Lists
        if (tag === 'ul' || tag === 'ol') {
          var items = node.querySelectorAll(':scope > li');
          items.forEach(function(li, i) {
            var prefix = tag === 'ol' ? (i + 1) + '. ' : '- ';
            md += prefix + li.textContent.trim() + '\n';
          });
          md += '\n';
          return;
        }

        // Accordion (FAQ) -> Q&A format
        if (tag === 'div' && node.classList.contains('accordion-item')) {
          var header = node.querySelector('.accordion-header');
          var body = node.querySelector('.accordion-body');
          md += '**' + (header ? header.textContent.trim() : '') + '**\n\n';
          md += (body ? body.textContent.trim() : '') + '\n\n';
          return;
        }

        // References footer -> markdown links
        if (tag === 'section' && node.classList.contains('references-footer')) {
          md += '### References\n\n';
          node.querySelectorAll('.reference-item').forEach(function(item) {
            var a = item.querySelector('.reference-title a');
            if (a) {
              md += '- [' + a.textContent.trim() + '](' + a.href + ')\n';
            }
          });
          md += '\n';
          return;
        }

        // Skip nav, buttons, scripts
        if (tag === 'nav' || tag === 'button' || tag === 'script') return;

        // Default: recurse into children
        md += domToMarkdown(node);
      });
      return md;
    }

    function processInline(node) {
      var result = '';
      node.childNodes.forEach(function(child) {
        if (child.nodeType === 3) {
          result += child.textContent;
          return;
        }
        if (child.nodeType !== 1) return;
        var tag = child.tagName.toLowerCase();
        if (tag === 'strong' || tag === 'b') {
          result += '**' + child.textContent + '**';
        } else if (tag === 'em' || tag === 'i') {
          result += '*' + child.textContent + '*';
        } else if (tag === 'code') {
          result += '`' + child.textContent + '`';
        } else if (tag === 'a') {
          result += '[' + child.textContent + '](' + child.href + ')';
        } else if (tag === 'span' && child.classList.contains('glossary-term')) {
          result += child.textContent;
          if (child.dataset.definition) {
            result += ' (' + child.dataset.definition + ')';
          }
        } else {
          result += child.textContent;
        }
      });
      return result;
    }
```

- [ ] **Step 5: Commit**

```bash
git add skills/system-explorer/system-to-course/references/page-templates.md
git commit -m "feat(system-explorer): add copy-markdown button, reference footer, and page-context metadata to content page template"
```

---

### Task 5: Add source-annotated code block and reference footer to interactive-elements.md

**Files:**
- Modify: `skills/system-explorer/system-to-course/references/interactive-elements.md` (append after Code Snippet Block section)

- [ ] **Step 1: Add source-annotated code block element**

After the Code Snippet Block section's closing `---`, add:

````markdown
## Source-Annotated Code Block

Extended code block for displaying actual source code from the system's codebase. Includes a file path header bar with a link to the source on GitHub. Used when the analysis.md code block has `// source:` annotation comments.

**When to use:** When a code block in the analysis has `// source:` metadata. Regular tutorial/example code blocks without `// source:` should use the standard Code Snippet Block pattern above.

**HTML:**
```html
<div class="code-block code-block-sourced" id="source-[UNIQUE_ID]">
  <div class="code-header">
    <span class="code-lang">[LANGUAGE]</span>
    <span class="code-source-path">[FILE_PATH]:[LINE_RANGE]</span>
    <a class="code-source-link" href="[GITHUB_URL]" target="_blank" rel="noopener noreferrer">
      View on GitHub &#x2197;
    </a>
    <button class="code-copy" onclick="copyCode(this)">Copy</button>
  </div>
  <pre class="code-pre"><code>[SYNTAX_HIGHLIGHTED_CODE]</code></pre>
</div>
```

**GitHub URL construction:**

```
https://github.com/{github}/blob/{tag || "main"}/{file_path}#L{start_line}-L{end_line}
```

Resolution order for `github` and `tag` values:
1. Code block annotation (`// github:`, `// tag:`) — highest priority
2. Metadata section (`GitHub`, `Tag` fields) — fallback
3. Default (`main` for tag; omit link entirely if no github value at any level)

**Parsing source annotations:**

When converting analysis.md code blocks to HTML, check the first 1-3 lines for metadata comments:
- `// source: src/parser/parser.cpp:142-168` — extract file path and optional line range
- `// github: duckdb/duckdb` — extract org/repo (optional, overrides Metadata)
- `// tag: v1.5.1` — extract git ref (optional, overrides Metadata)

Strip these metadata lines from the displayed code. The code body should show only the actual source code.

**Language-specific comment patterns to match:**
- `// source:` — C, C++, Java, Go, Rust, JavaScript, TypeScript
- `# source:` — Python, Ruby, Shell, YAML
- `-- source:` — SQL, Lua, Haskell
- `<!-- source:` — HTML, XML

Apply the same patterns for `github:` and `tag:` annotations.

**CSS:** Uses `.code-block-sourced` variant from design-system.md. The file path header sits between the language badge and the copy button.

**JS:**
```javascript
function copyCode(btn) {
  var code = btn.closest('.code-block').querySelector('pre').textContent;
  navigator.clipboard.writeText(code).then(function() {
    btn.textContent = 'Copied!';
    btn.classList.add('copied');
    setTimeout(function() {
      btn.textContent = 'Copy';
      btn.classList.remove('copied');
    }, 2000);
  });
}
```

(Same as standard code copy — metadata lines are already stripped from the DOM.)
````

- [ ] **Step 2: Add source map summary element**

After the source-annotated code block section, add:

````markdown
## Source Map

Collapsible summary at the top of pages that contain source-annotated code blocks. Lists all referenced source files with links to both the on-page code block and the GitHub source.

**When to use:** At the top of the Implementation Details page (and How It Works, if it has source-annotated blocks). Only include if the page has at least 2 source-annotated code blocks.

**HTML:**
```html
<div class="source-map" id="source-map">
  <div class="source-map-header" onclick="this.parentElement.classList.toggle('open')">
    <h3>&#x1F5C2; Source Map</h3>
    <span class="source-map-toggle">&#x25BC;</span>
  </div>
  <div class="source-map-body">
    <ul class="source-map-list">
      <!--
        Repeat for each source-annotated code block on this page.
        Link to the on-page anchor and to GitHub.
      -->
      <li class="source-map-item">
        <a href="#source-[UNIQUE_ID]">[FILE_PATH]</a>
        <span class="line-range">Lines [START]-[END]</span>
      </li>
    </ul>
    <div class="source-map-repo">
      Repository: <a href="https://github.com/[GITHUB_ORG_REPO]" target="_blank" rel="noopener noreferrer">[GITHUB_ORG_REPO]</a> @ [TAG]
    </div>
  </div>
</div>
```

**Behavior:**
- Collapsed by default (no `.open` class)
- Click header to toggle `.open` class
- Arrow indicator rotates when open (CSS handles via transform)
- CSS from design-system.md `.source-map` section handles all styling

**Placement:** Insert immediately after the page header, before the first content section.
````

- [ ] **Step 3: Add reference footer element**

After the source map section, add:

````markdown
## Reference Footer

Per-page section listing authoritative sources referenced in the page content. Rendered from the `<!-- references: ... -->` block in the corresponding analysis.md section.

**When to use:** On any content page whose source section in analysis.md has a `<!-- references: ... -->` block. Omit entirely if no references exist for that section.

**HTML:**
```html
<section class="references-footer">
  <h3>&#x1F4DA; References &amp; Resources</h3>
  <ul class="references-list">
    <li class="reference-item">
      <span class="reference-type-icon">[TYPE_ICON]</span>
      <div class="reference-content">
        <span class="reference-title">
          <a href="[URL]" target="_blank" rel="noopener noreferrer">[TITLE]</a>
        </span>
        <span class="reference-domain">[DOMAIN]</span>
      </div>
    </li>
    <!-- Repeat for each reference -->
  </ul>
</section>
```

**Type-to-icon mapping:**

| Type | Icon | Emoji |
|------|------|-------|
| `official-docs` | Document | &#x1F4C4; (📄) |
| `paper` | Scroll | &#x1F4DC; (📜) |
| `blog` | Newspaper | &#x1F4F0; (📰) |
| `github` | Computer | &#x1F4BB; (💻) |
| `video` | Camera | &#x1F3A5; (🎥) |
| `tutorial` | Book | &#x1F4D6; (📖) |
| `community` | Chat | &#x1F4AC; (💬) |

**Domain hint extraction:** Parse the hostname from the URL. For example:
- `https://duckdb.org/docs/internals/overview` → `duckdb.org`
- `https://arxiv.org/abs/2106.00505` → `arxiv.org`
- `https://github.com/duckdb/duckdb` → `github.com`

**Parsing `<!-- references: ... -->` blocks:**

The references block is an HTML comment in analysis.md, placed after the level tag:
```
<!-- references:
- [Title](URL) | type
- [Title](URL) | type
-->
```

Parse each line as: markdown link + pipe + type string. Extract title, URL, and type.

**Placement:** Above the prev/next page navigation, below the last content section.

**CSS:** Uses `.references-footer` styles from design-system.md.
````

- [ ] **Step 4: Commit**

```bash
git add skills/system-explorer/system-to-course/references/interactive-elements.md
git commit -m "feat(system-explorer): add source-annotated code block, source map, and reference footer interactive elements"
```

---

### Task 6: Update system-to-course SKILL.md with parsing and rendering instructions

**Files:**
- Modify: `skills/system-explorer/system-to-course/SKILL.md:48-53` (Phase 1: Parse Analysis)
- Modify: `skills/system-explorer/system-to-course/SKILL.md:75-87` (Phase 2: Generate Foundation)
- Modify: `skills/system-explorer/system-to-course/SKILL.md:89-117` (Phase 3: Generate Content Pages)
- Modify: `skills/system-explorer/system-to-course/SKILL.md:128-140` (Phase 4: Self-Review)

- [ ] **Step 1: Add new parsing targets to Phase 1**

In `SKILL.md`, after line 53 (`- **Content types** — identify code blocks, lists, Q&A pairs...`), add:

```markdown
- **References** — parse `<!-- references: ... -->` blocks from each section. Extract title, URL, and type for each reference entry.
- **Source annotations** — scan code blocks for `// source:`, `// github:`, `// tag:` metadata lines. Extract file paths, line ranges, and repo/tag overrides.
- **GitHub/Tag metadata** — read `GitHub` and `Tag` fields from the Metadata section. These are default values for source-annotated code blocks.
- **Inline links** — preserve markdown links in content. When rendering to HTML, add `target="_blank"` and `rel="noopener noreferrer"` to external URLs.
```

- [ ] **Step 2: Add page-context metadata to Phase 2**

After line 87 (`- Quick-start section pulled from the Overview`), add:

```markdown

**Page context metadata:** Inject a `<!-- page-context: ... -->` HTML comment into each content page's `<head>` section. This metadata is consumed by the Copy as Markdown button. Populate from the Metadata section:
```html
<!-- page-context:
  system: "[System Name]"
  description: "[One-line description from Overview]"
  page: "[Page Title]"
  level: "[Level Label]"
-->
```
```

- [ ] **Step 3: Add new elements to Phase 3 content conversion rules**

After line 117 (`| Technical term (first use) | Glossary Tooltip ...`), add:

```markdown
| Source-annotated code block  | Source-Annotated Code Block (file path header, GitHub link) |
| Section references block     | Reference Footer (per-page, above prev/next nav) |
| Multiple source code blocks  | Source Map (collapsible summary at page top) |
| External URL in content      | External Link (target="_blank", ↗ icon) |
```

Also add to the "Mandatory per page" list:

```markdown
- Copy as Markdown button in the page header (content pages only, not index.html)
- External links open in new tab with ↗ indicator
```

- [ ] **Step 4: Add new review items to Phase 4 checklist**

After line 140 (`10. **Accessibility** — ...`), add:

```markdown
11. **Copy as Markdown** — Does every content page have the copy-markdown button in the header? Click it and verify the output includes the context header and readable markdown.
12. **References footer** — Do pages with `<!-- references: ... -->` blocks in their source section have a references footer? Are type icons correct? Do links open in new tabs?
13. **Source annotations** — Are source-annotated code blocks showing file path headers? Do GitHub links resolve correctly (using tag when available, falling back to main)? Are metadata comment lines stripped from displayed code?
14. **Source map** — Do pages with 2+ source-annotated blocks have a collapsible source map at the top? Does it list all referenced files?
15. **External links** — Do all external links have `target="_blank"`, `rel="noopener noreferrer"`, and the ↗ icon via CSS?
```

- [ ] **Step 5: Commit**

```bash
git add skills/system-explorer/system-to-course/SKILL.md
git commit -m "feat(system-explorer): add parsing and rendering instructions for references, source annotations, and copy-markdown"
```

---

### Task 7: Validate consistency across all modified files

This is a cross-cutting validation pass to verify consistency of names, formats, and cross-references across all modified files.

**Files:**
- Read: All 6 modified files

- [ ] **Step 1: Verify reference type names are consistent**

Check that the reference type list (`official-docs`, `paper`, `blog`, `github`, `video`, `tutorial`, `community`) is identical in:
- `analysis-template.md` (type definitions)
- `interactive-elements.md` (type-to-icon mapping table)
- `page-templates.md` (icon comments in reference footer template)

- [ ] **Step 2: Verify source annotation format is consistent**

Check that the `// source:`, `// github:`, `// tag:` format and parsing rules are identical in:
- `analysis-template.md` (annotation documentation)
- `interactive-elements.md` (parsing instructions)
- `SKILL.md` (system-to-course, Phase 1 parsing)

- [ ] **Step 3: Verify page-context metadata format is consistent**

Check that the `<!-- page-context: ... -->` format matches between:
- `page-templates.md` (template)
- The copy-as-markdown JS (parsing regex)

- [ ] **Step 4: Verify CSS class names match between design-system.md and templates**

Check that every CSS class used in `page-templates.md` and `interactive-elements.md` has corresponding styles in `design-system.md`:
- `.copy-markdown-btn`, `.btn-icon`, `.btn-label`
- `.page-header-content`
- `.references-footer`, `.references-list`, `.reference-item`, `.reference-type-icon`, `.reference-content`, `.reference-title`, `.reference-domain`
- `.code-block-sourced`, `.code-source-path`, `.code-source-link`
- `.source-map`, `.source-map-header`, `.source-map-toggle`, `.source-map-body`, `.source-map-list`, `.source-map-item`, `.source-map-repo`

- [ ] **Step 5: Fix any inconsistencies found, then commit**

If any inconsistencies are found, fix them in the relevant files and commit:

```bash
git add -A
git commit -m "fix(system-explorer): resolve cross-file inconsistencies in new feature references"
```

If no inconsistencies are found, skip this commit.
