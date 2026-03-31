# Interactive Elements Reference

Implementation patterns for every interactive element type used in system courses. Reuses shared patterns from paper-to-course (callout boxes, glossary tooltips, concept cards) and adds software-specific elements (architecture diagrams, code snippets, decision trees, performance gauges).

## Table of Contents
1. [Architecture Diagram](#architecture-diagram)
2. [Code Snippet Block](#code-snippet-block)
3. [Source-Annotated Code Block](#source-annotated-code-block)
4. [Source Map](#source-map)
5. [Reference Footer](#reference-footer)
6. [Decision Tree](#decision-tree)
7. [System Comparison Cards](#system-comparison-cards)
8. [Performance Gauge](#performance-gauge)
9. [Flow Diagram](#flow-diagram)
10. [Concept Cards](#concept-cards)
11. [Expandable Accordion](#expandable-accordion)
12. [Callout Boxes](#callout-boxes)
13. [Glossary Tooltips](#glossary-tooltips)
14. [Level Badge](#level-badge)

---

## Architecture Diagram

CSS/SVG component diagram showing system components and data flow. Each component is a clickable box that expands with details. Color-coded by component type.

**HTML:**
```html
<div class="arch-diagram">
  <h3 class="arch-title">System Architecture</h3>
  <div class="arch-canvas">
    <!-- Row 1: Client layer -->
    <div class="arch-row">
      <div class="arch-component" data-type="network" data-details="Handles HTTP requests, TLS termination, rate limiting, and routes traffic to backend services.">
        <div class="arch-component-icon">&#x1F310;</div>
        <div class="arch-component-label">Load Balancer</div>
        <div class="arch-component-brief">Traffic routing</div>
        <div class="arch-component-details"></div>
      </div>
    </div>

    <div class="arch-arrow-down">
      <svg width="24" height="32" viewBox="0 0 24 32"><path d="M12 0 L12 24 M6 18 L12 28 L18 18" stroke="currentColor" stroke-width="2" fill="none"/></svg>
    </div>

    <!-- Row 2: Compute layer -->
    <div class="arch-row">
      <div class="arch-component" data-type="compute" data-details="Stateless application servers running the core business logic. Horizontally scalable behind the load balancer.">
        <div class="arch-component-icon">&#x2699;&#xFE0F;</div>
        <div class="arch-component-label">API Server</div>
        <div class="arch-component-brief">Business logic</div>
        <div class="arch-component-details"></div>
      </div>

      <div class="arch-arrow-right">
        <svg width="40" height="24" viewBox="0 0 40 24"><path d="M0 12 L32 12 M26 6 L36 12 L26 18" stroke="currentColor" stroke-width="2" fill="none"/></svg>
      </div>

      <div class="arch-component" data-type="compute" data-details="Processes background jobs: email delivery, report generation, data pipelines. Decoupled via message queue.">
        <div class="arch-component-icon">&#x1F504;</div>
        <div class="arch-component-label">Worker</div>
        <div class="arch-component-brief">Async processing</div>
        <div class="arch-component-details"></div>
      </div>
    </div>

    <div class="arch-arrow-down">
      <svg width="24" height="32" viewBox="0 0 24 32"><path d="M12 0 L12 24 M6 18 L12 28 L18 18" stroke="currentColor" stroke-width="2" fill="none"/></svg>
    </div>

    <!-- Row 3: Storage layer -->
    <div class="arch-row">
      <div class="arch-component" data-type="storage" data-details="Primary data store. Handles ACID transactions, relational queries, and persistent state.">
        <div class="arch-component-icon">&#x1F4BE;</div>
        <div class="arch-component-label">Database</div>
        <div class="arch-component-brief">Persistent state</div>
        <div class="arch-component-details"></div>
      </div>

      <div class="arch-arrow-right">
        <svg width="40" height="24" viewBox="0 0 40 24"><path d="M0 12 L32 12 M26 6 L36 12 L26 18" stroke="currentColor" stroke-width="2" fill="none"/></svg>
      </div>

      <div class="arch-component" data-type="storage" data-details="In-memory cache layer. Reduces database load for hot reads. TTL-based expiration.">
        <div class="arch-component-icon">&#x26A1;</div>
        <div class="arch-component-label">Cache</div>
        <div class="arch-component-brief">Fast reads</div>
        <div class="arch-component-details"></div>
      </div>

      <div class="arch-arrow-right">
        <svg width="40" height="24" viewBox="0 0 40 24"><path d="M0 12 L32 12 M26 6 L36 12 L26 18" stroke="currentColor" stroke-width="2" fill="none"/></svg>
      </div>

      <div class="arch-component" data-type="queue" data-details="Message broker for async communication between services. Provides durability and ordering guarantees.">
        <div class="arch-component-icon">&#x1F4E8;</div>
        <div class="arch-component-label">Message Queue</div>
        <div class="arch-component-brief">Async messaging</div>
        <div class="arch-component-details"></div>
      </div>
    </div>
  </div>
</div>
```

**CSS:**
```css
.arch-diagram {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--shadow-md);
  margin: var(--space-8) 0;
  overflow-x: auto;
}
.arch-title {
  font-family: var(--font-display);
  font-weight: 700;
  margin-bottom: var(--space-5);
  text-align: center;
}
.arch-canvas {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
}
.arch-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}
.arch-component {
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  min-width: 140px;
  max-width: 200px;
  text-align: center;
  cursor: pointer;
  transition: border-color var(--duration-fast), box-shadow var(--duration-fast), transform var(--duration-fast);
  position: relative;
}
.arch-component:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}
.arch-component.expanded {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px var(--color-accent-light);
}

/* Component type colors */
.arch-component[data-type="compute"] { border-left: 4px solid #2A7B9B; }
.arch-component[data-type="storage"] { border-left: 4px solid #2D8B55; }
.arch-component[data-type="network"] { border-left: 4px solid #D4A843; }
.arch-component[data-type="queue"]   { border-left: 4px solid #7B6DAA; }
.arch-component[data-type="cache"]   { border-left: 4px solid #E06B56; }

.arch-component-icon { font-size: 1.5rem; margin-bottom: var(--space-1); }
.arch-component-label {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: var(--text-sm);
}
.arch-component-brief {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-top: var(--space-1);
}
.arch-component-details {
  max-height: 0;
  overflow: hidden;
  opacity: 0;
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  line-height: var(--leading-normal);
  transition: max-height var(--duration-normal), opacity var(--duration-normal), margin var(--duration-normal);
}
.arch-component.expanded .arch-component-details {
  max-height: 150px;
  opacity: 1;
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border-light);
}

/* Arrows */
.arch-arrow-down, .arch-arrow-right {
  color: var(--color-text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/* Responsive: stack vertically on mobile */
@media (max-width: 768px) {
  .arch-row { flex-direction: column; }
  .arch-arrow-right {
    transform: rotate(90deg);
  }
}
```

**JS:**
```javascript
document.querySelectorAll('.arch-component').forEach(comp => {
  comp.addEventListener('click', () => {
    const details = comp.querySelector('.arch-component-details');
    const wasExpanded = comp.classList.contains('expanded');

    // Collapse all others
    document.querySelectorAll('.arch-component.expanded').forEach(other => {
      other.classList.remove('expanded');
      other.querySelector('.arch-component-details').textContent = '';
    });

    // Toggle clicked component
    if (!wasExpanded) {
      comp.classList.add('expanded');
      details.textContent = comp.dataset.details;
    }
  });
});
```

**Usage:** Adapt the rows, component types, and data-details to match the system being documented. Add/remove rows and arrows as needed for the actual architecture.

---

## Code Snippet Block

Syntax-highlighted code with copy button and language label. Dark background with Catppuccin-inspired colors.

**HTML:**
```html
<div class="code-block">
  <div class="code-header">
    <span class="code-lang">Python</span>
    <button class="code-copy" onclick="copyCode(this)">Copy</button>
  </div>
  <pre class="code-pre"><code><span class="code-keyword">import</span> <span class="code-variable">redis</span>

<span class="code-comment"># Connect to the cache layer</span>
<span class="code-variable">client</span> = <span class="code-variable">redis</span>.<span class="code-function">Redis</span>(<span class="code-variable">host</span>=<span class="code-string">'localhost'</span>, <span class="code-variable">port</span>=<span class="code-number">6379</span>)

<span class="code-keyword">def</span> <span class="code-function">get_user</span>(<span class="code-variable">user_id</span>):
    <span class="code-comment"># Check cache first</span>
    <span class="code-variable">cached</span> = <span class="code-variable">client</span>.<span class="code-function">get</span>(<span class="code-string">f'user:</span><span class="code-string">{user_id}'</span>)
    <span class="code-keyword">if</span> <span class="code-variable">cached</span>:
        <span class="code-keyword">return</span> <span class="code-variable">json</span>.<span class="code-function">loads</span>(<span class="code-variable">cached</span>)
    <span class="code-comment"># Fall through to database</span>
    <span class="code-variable">user</span> = <span class="code-variable">db</span>.<span class="code-function">query</span>(<span class="code-string">'SELECT * FROM users WHERE id = %s'</span>, <span class="code-variable">user_id</span>)
    <span class="code-variable">client</span>.<span class="code-function">setex</span>(<span class="code-string">f'user:</span><span class="code-string">{user_id}'</span>, <span class="code-number">300</span>, <span class="code-variable">json</span>.<span class="code-function">dumps</span>(<span class="code-variable">user</span>))
    <span class="code-keyword">return</span> <span class="code-variable">user</span></code></pre>
</div>
```

**CSS:**
```css
.code-block {
  background: #1E1E2E;
  border-radius: var(--radius-md);
  overflow: hidden;
  margin: var(--space-6) 0;
  box-shadow: var(--shadow-md);
}
.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-2) var(--space-4);
  background: #181825;
  border-bottom: 1px solid #313244;
}
.code-lang {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: #CDD6F4;
  background: #313244;
  padding: 2px var(--space-2);
  border-radius: var(--radius-sm);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.code-copy {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: #A6ADC8;
  background: none;
  border: 1px solid #45475A;
  border-radius: var(--radius-sm);
  padding: 2px var(--space-3);
  cursor: pointer;
  transition: all var(--duration-fast);
}
.code-copy:hover {
  color: #CDD6F4;
  border-color: #CDD6F4;
}
.code-copy.copied {
  color: #A6E3A1;
  border-color: #A6E3A1;
}
.code-pre {
  padding: var(--space-4) var(--space-5);
  margin: 0;
  overflow-x: auto;
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  line-height: 1.7;
  color: #CDD6F4;
  -webkit-overflow-scrolling: touch;
}

/* Optional line numbers via CSS counter */
.code-pre.line-numbers {
  counter-reset: line;
}
.code-pre.line-numbers code {
  display: block;
}
.code-pre.line-numbers code > span.line::before {
  counter-increment: line;
  content: counter(line);
  display: inline-block;
  width: 2.5em;
  margin-right: var(--space-3);
  text-align: right;
  color: #45475A;
  border-right: 1px solid #313244;
  padding-right: var(--space-2);
  user-select: none;
}

/* Catppuccin Mocha-inspired syntax colors */
.code-keyword  { color: #CBA6F7; }  /* purple — keywords, control flow */
.code-string   { color: #F9E2AF; }  /* yellow — string literals */
.code-comment  { color: #6C7086; font-style: italic; }  /* gray — comments */
.code-function { color: #A6E3A1; }  /* green — function names */
.code-number   { color: #FAB387; }  /* peach — numeric literals */
.code-variable { color: #89B4FA; }  /* blue — variables, identifiers */
```

**JS:**
```javascript
function copyCode(btn) {
  const pre = btn.closest('.code-block').querySelector('.code-pre');
  const text = pre.textContent;
  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = 'Copied!';
    btn.classList.add('copied');
    setTimeout(() => {
      btn.textContent = 'Copy';
      btn.classList.remove('copied');
    }, 2000);
  });
}
```

**Usage:** Wrap language keywords, strings, comments, functions, numbers, and variables in the appropriate `<span>` classes. Set the `.code-lang` text to the language name. For line numbers, add the `line-numbers` class to `.code-pre` and wrap each line in `<span class="line">`.

---

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

---

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

---

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

---

## Decision Tree

Interactive "should I use this?" flow chart. Data-driven: each step has a question and yes/no branches leading to another step or a final recommendation.

**HTML:**
```html
<div class="decision-tree" id="dt-1">
  <h3 class="dt-title">Should You Use This System?</h3>
  <div class="dt-breadcrumb" id="dt-1-breadcrumb"></div>
  <div class="dt-step active" data-step="start">
    <p class="dt-question">Do you need to handle more than 10,000 requests per second?</p>
    <div class="dt-actions">
      <button class="dt-btn dt-yes" onclick="dtNavigate('dt-1', 'high-scale')">Yes</button>
      <button class="dt-btn dt-no" onclick="dtNavigate('dt-1', 'low-scale')">No</button>
    </div>
  </div>
  <div class="dt-step" data-step="high-scale">
    <p class="dt-question">Is strong consistency more important than availability?</p>
    <div class="dt-actions">
      <button class="dt-btn dt-yes" onclick="dtNavigate('dt-1', 'rec-a')">Yes</button>
      <button class="dt-btn dt-no" onclick="dtNavigate('dt-1', 'rec-b')">No</button>
    </div>
  </div>
  <div class="dt-step" data-step="low-scale">
    <p class="dt-question">Do you need complex relational queries (JOINs, aggregations)?</p>
    <div class="dt-actions">
      <button class="dt-btn dt-yes" onclick="dtNavigate('dt-1', 'rec-c')">Yes</button>
      <button class="dt-btn dt-no" onclick="dtNavigate('dt-1', 'rec-d')">No</button>
    </div>
  </div>
  <!-- Final recommendations -->
  <div class="dt-step" data-step="rec-a">
    <div class="dt-recommendation good">
      <strong>Use this system.</strong> It excels at high-throughput workloads with strong consistency guarantees.
    </div>
  </div>
  <div class="dt-step" data-step="rec-b">
    <div class="dt-recommendation alt">
      <strong>Consider an alternative.</strong> For high availability at scale, an eventually-consistent system like Cassandra may be a better fit.
    </div>
  </div>
  <div class="dt-step" data-step="rec-c">
    <div class="dt-recommendation alt">
      <strong>Consider PostgreSQL instead.</strong> For complex relational queries at moderate scale, a traditional RDBMS is likely simpler and more capable.
    </div>
  </div>
  <div class="dt-step" data-step="rec-d">
    <div class="dt-recommendation good">
      <strong>This system is a good fit.</strong> Simpler data access patterns at moderate scale are its sweet spot.
    </div>
  </div>
  <button class="dt-reset" onclick="dtReset('dt-1')">Start Over</button>
</div>
```

**CSS:**
```css
.decision-tree {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--shadow-md);
  margin: var(--space-8) 0;
}
.dt-title {
  font-family: var(--font-display);
  font-weight: 700;
  margin-bottom: var(--space-4);
}
.dt-breadcrumb {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
  min-height: 28px;
}
.dt-crumb {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  background: var(--color-accent-light);
  color: var(--color-accent);
  padding: 2px var(--space-2);
  border-radius: var(--radius-sm);
}
.dt-crumb.yes { background: var(--color-success-light); color: var(--color-success); }
.dt-crumb.no  { background: var(--color-error-light); color: var(--color-error); }
.dt-step {
  display: none;
  animation: dtFadeIn var(--duration-normal) var(--ease-out);
}
.dt-step.active { display: block; }
@keyframes dtFadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.dt-question {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 600;
  margin-bottom: var(--space-4);
}
.dt-actions {
  display: flex;
  gap: var(--space-3);
}
.dt-btn {
  padding: var(--space-3) var(--space-6);
  border-radius: var(--radius-sm);
  border: 2px solid;
  font-family: var(--font-body);
  font-size: var(--text-base);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--duration-fast);
}
.dt-yes {
  border-color: var(--color-success);
  color: var(--color-success);
  background: var(--color-success-light);
}
.dt-yes:hover { background: var(--color-success); color: white; }
.dt-no {
  border-color: var(--color-error);
  color: var(--color-error);
  background: var(--color-error-light);
}
.dt-no:hover { background: var(--color-error); color: white; }
.dt-recommendation {
  padding: var(--space-5);
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  line-height: var(--leading-normal);
}
.dt-recommendation.good {
  background: var(--color-success-light);
  border-left: 4px solid var(--color-success);
}
.dt-recommendation.alt {
  background: var(--color-warning-light);
  border-left: 4px solid var(--color-warning);
}
.dt-reset {
  margin-top: var(--space-4);
  padding: var(--space-2) var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  font-family: var(--font-body);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--duration-fast);
}
.dt-reset:hover { border-color: var(--color-accent); color: var(--color-accent); }
```

**JS:**
```javascript
(function() {
  // Track history per tree for breadcrumbs
  const treeHistory = {};

  window.dtNavigate = function(treeId, targetStep) {
    const tree = document.getElementById(treeId);
    const current = tree.querySelector('.dt-step.active');
    const questionText = current.querySelector('.dt-question')?.textContent || '';
    const isYes = event.target.classList.contains('dt-yes');

    // Record breadcrumb
    if (!treeHistory[treeId]) treeHistory[treeId] = [];
    treeHistory[treeId].push({ question: questionText, answer: isYes ? 'Yes' : 'No' });
    renderBreadcrumbs(treeId);

    // Transition
    current.classList.remove('active');
    const next = tree.querySelector(`[data-step="${targetStep}"]`);
    next.classList.add('active');
  };

  window.dtReset = function(treeId) {
    const tree = document.getElementById(treeId);
    tree.querySelectorAll('.dt-step').forEach(s => s.classList.remove('active'));
    tree.querySelector('[data-step="start"]').classList.add('active');
    treeHistory[treeId] = [];
    renderBreadcrumbs(treeId);
  };

  function renderBreadcrumbs(treeId) {
    const container = document.getElementById(treeId + '-breadcrumb');
    const history = treeHistory[treeId] || [];
    container.innerHTML = history.map(h => {
      const cls = h.answer === 'Yes' ? 'yes' : 'no';
      // Shorten question for breadcrumb
      const short = h.question.length > 40 ? h.question.substring(0, 37) + '...' : h.question;
      return `<span class="dt-crumb ${cls}">${short} &rarr; ${h.answer}</span>`;
    }).join('');
  }
})();
```

**Usage:** Define each step with `data-step`. The `start` step is shown initially. Yes/No buttons call `dtNavigate` with the target step ID. Terminal nodes use `.dt-recommendation` instead of a question.

---

## System Comparison Cards

Side-by-side comparison with alternative systems. Each card shows strengths, weaknesses, and best-for summary.

**HTML:**
```html
<div class="sys-comparison">
  <div class="sys-comparison-header">
    <h3>How Does It Compare?</h3>
    <div class="sys-comparison-toggles">
      <label class="sys-toggle"><input type="checkbox" checked data-dim="strengths" onchange="toggleDimension(this)"> Strengths</label>
      <label class="sys-toggle"><input type="checkbox" checked data-dim="weaknesses" onchange="toggleDimension(this)"> Weaknesses</label>
      <label class="sys-toggle"><input type="checkbox" checked data-dim="best-for" onchange="toggleDimension(this)"> Best For</label>
    </div>
  </div>
  <div class="sys-cards">
    <div class="sys-card current">
      <div class="sys-card-badge">This System</div>
      <h4 class="sys-card-name">Redis</h4>
      <div class="sys-card-section" data-dim="strengths">
        <h5 class="sys-section-label strengths-label">Strengths</h5>
        <ul>
          <li class="sys-highlight">Sub-millisecond latency</li>
          <li>Rich data structures</li>
          <li class="sys-highlight">Built-in pub/sub</li>
        </ul>
      </div>
      <div class="sys-card-section" data-dim="weaknesses">
        <h5 class="sys-section-label weaknesses-label">Weaknesses</h5>
        <ul>
          <li>Dataset must fit in memory</li>
          <li>Limited query capabilities</li>
        </ul>
      </div>
      <div class="sys-card-section" data-dim="best-for">
        <h5 class="sys-section-label bestfor-label">Best For</h5>
        <p>Caching, session storage, real-time leaderboards, rate limiting</p>
      </div>
    </div>

    <div class="sys-card">
      <h4 class="sys-card-name">Memcached</h4>
      <div class="sys-card-section" data-dim="strengths">
        <h5 class="sys-section-label strengths-label">Strengths</h5>
        <ul>
          <li>Simple and predictable</li>
          <li>Multi-threaded</li>
        </ul>
      </div>
      <div class="sys-card-section" data-dim="weaknesses">
        <h5 class="sys-section-label weaknesses-label">Weaknesses</h5>
        <ul>
          <li>Only string key-value</li>
          <li>No persistence</li>
          <li>No pub/sub</li>
        </ul>
      </div>
      <div class="sys-card-section" data-dim="best-for">
        <h5 class="sys-section-label bestfor-label">Best For</h5>
        <p>Simple caching with predictable memory usage</p>
      </div>
    </div>

    <div class="sys-card">
      <h4 class="sys-card-name">DynamoDB</h4>
      <div class="sys-card-section" data-dim="strengths">
        <h5 class="sys-section-label strengths-label">Strengths</h5>
        <ul>
          <li>Fully managed, serverless</li>
          <li>Scales to any size</li>
        </ul>
      </div>
      <div class="sys-card-section" data-dim="weaknesses">
        <h5 class="sys-section-label weaknesses-label">Weaknesses</h5>
        <ul>
          <li>Higher latency (~5-10ms)</li>
          <li>Vendor lock-in</li>
          <li>Cost at high throughput</li>
        </ul>
      </div>
      <div class="sys-card-section" data-dim="best-for">
        <h5 class="sys-section-label bestfor-label">Best For</h5>
        <p>Serverless apps, variable workloads, zero-ops requirement</p>
      </div>
    </div>
  </div>
</div>
```

**CSS:**
```css
.sys-comparison {
  margin: var(--space-8) 0;
}
.sys-comparison-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}
.sys-comparison-header h3 {
  font-family: var(--font-display);
  font-weight: 700;
}
.sys-comparison-toggles {
  display: flex;
  gap: var(--space-3);
}
.sys-toggle {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--color-text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: var(--space-1);
}
.sys-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--space-4);
}
.sys-card {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: var(--space-5);
  box-shadow: var(--shadow-sm);
  border-top: 3px solid var(--color-border);
  transition: box-shadow var(--duration-fast);
}
.sys-card.current {
  border-top-color: var(--color-accent);
  box-shadow: var(--shadow-md);
}
.sys-card-badge {
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-accent);
  margin-bottom: var(--space-2);
}
.sys-card-name {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: var(--text-lg);
  margin-bottom: var(--space-4);
}
.sys-card-section {
  margin-bottom: var(--space-3);
  transition: max-height var(--duration-normal), opacity var(--duration-normal);
  overflow: hidden;
}
.sys-card-section.hidden {
  max-height: 0;
  opacity: 0;
  margin-bottom: 0;
}
.sys-section-label {
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-2);
}
.strengths-label  { color: var(--color-success); }
.weaknesses-label { color: var(--color-error); }
.bestfor-label    { color: var(--color-info); }
.sys-card ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
.sys-card li {
  font-size: var(--text-sm);
  padding: var(--space-1) 0;
  color: var(--color-text-secondary);
}
.sys-card li.sys-highlight {
  color: var(--color-text);
  font-weight: 600;
}
.sys-card .sys-card-section[data-dim="best-for"] p {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}
@media (max-width: 768px) {
  .sys-cards { grid-template-columns: 1fr; }
}
```

**JS:**
```javascript
function toggleDimension(checkbox) {
  const dim = checkbox.dataset.dim;
  const sections = document.querySelectorAll(`.sys-card-section[data-dim="${dim}"]`);
  sections.forEach(s => {
    s.classList.toggle('hidden', !checkbox.checked);
  });
}
```

**Usage:** Add 2-3 cards. Mark the system being taught with the `.current` class. Use `.sys-highlight` on list items where the current system has a clear advantage.

---

## Performance Gauge

Horizontal bars showing throughput, latency, scalability, and other performance traits. Animated fill on scroll into view.

**HTML:**
```html
<div class="perf-gauges" id="perf-1">
  <h3 class="perf-title">Performance Profile</h3>
  <div class="perf-gauge">
    <div class="perf-label">
      <span class="perf-name">Read Latency</span>
      <span class="perf-value">~0.5ms</span>
    </div>
    <div class="perf-bar">
      <div class="perf-fill perf-green" data-width="95"></div>
    </div>
    <span class="perf-note">Sub-millisecond for cached reads</span>
  </div>
  <div class="perf-gauge">
    <div class="perf-label">
      <span class="perf-name">Write Throughput</span>
      <span class="perf-value">~100K ops/s</span>
    </div>
    <div class="perf-bar">
      <div class="perf-fill perf-green" data-width="80"></div>
    </div>
    <span class="perf-note">Single node, pipelined</span>
  </div>
  <div class="perf-gauge">
    <div class="perf-label">
      <span class="perf-name">Horizontal Scalability</span>
      <span class="perf-value">Moderate</span>
    </div>
    <div class="perf-bar">
      <div class="perf-fill perf-yellow" data-width="55"></div>
    </div>
    <span class="perf-note">Cluster mode available but adds complexity</span>
  </div>
  <div class="perf-gauge">
    <div class="perf-label">
      <span class="perf-name">Durability</span>
      <span class="perf-value">Configurable</span>
    </div>
    <div class="perf-bar">
      <div class="perf-fill perf-yellow" data-width="50"></div>
    </div>
    <span class="perf-note">AOF/RDB persistence, risk of data loss on crash</span>
  </div>
  <div class="perf-gauge">
    <div class="perf-label">
      <span class="perf-name">Memory Efficiency</span>
      <span class="perf-value">Low</span>
    </div>
    <div class="perf-bar">
      <div class="perf-fill perf-red" data-width="30"></div>
    </div>
    <span class="perf-note">All data must fit in RAM</span>
  </div>
</div>
```

**CSS:**
```css
.perf-gauges {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--shadow-md);
  margin: var(--space-8) 0;
}
.perf-title {
  font-family: var(--font-display);
  font-weight: 700;
  margin-bottom: var(--space-5);
}
.perf-gauge {
  margin-bottom: var(--space-4);
}
.perf-label {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: var(--space-1);
}
.perf-name {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: var(--text-sm);
}
.perf-value {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}
.perf-bar {
  height: 10px;
  background: var(--color-border-light);
  border-radius: var(--radius-full);
  overflow: hidden;
}
.perf-fill {
  height: 100%;
  border-radius: var(--radius-full);
  width: 0;
  transition: width 1s var(--ease-out);
}
.perf-fill.animated {
  /* width set by JS from data-width */
}
.perf-green  { background: var(--color-success); }
.perf-yellow { background: var(--color-warning); }
.perf-red    { background: var(--color-error); }
.perf-note {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-top: var(--space-1);
  display: block;
}
```

**JS:**
```javascript
(function() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const fills = entry.target.querySelectorAll('.perf-fill');
        fills.forEach((fill, i) => {
          setTimeout(() => {
            fill.style.width = fill.dataset.width + '%';
            fill.classList.add('animated');
          }, i * 150);
        });
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.3 });

  document.querySelectorAll('.perf-gauges').forEach(g => observer.observe(g));
})();
```

**Usage:** Set `data-width` (0-100) on each `.perf-fill` to control bar length. Use `perf-green` for strengths (70-100), `perf-yellow` for moderate (40-69), `perf-red` for weaknesses (0-39). Add `.perf-note` for context.

---

## Flow Diagram

Numbered step cards with arrows showing process or data flow. Horizontal on desktop, vertical on mobile. Steps revealed sequentially on scroll.

**HTML:**
```html
<div class="flow-diagram" id="flow-1">
  <div class="flow-step animate-in" style="--step-delay: 0">
    <div class="flow-step-num">1</div>
    <div class="flow-step-content">
      <strong>Client Request</strong>
      <p>User sends an HTTP request to the API endpoint</p>
    </div>
  </div>
  <div class="flow-arrow animate-in" style="--step-delay: 1">&rarr;</div>
  <div class="flow-step animate-in" style="--step-delay: 2">
    <div class="flow-step-num">2</div>
    <div class="flow-step-content">
      <strong>Load Balancer</strong>
      <p>Routes request to a healthy backend instance</p>
    </div>
  </div>
  <div class="flow-arrow animate-in" style="--step-delay: 3">&rarr;</div>
  <div class="flow-step animate-in" style="--step-delay: 4">
    <div class="flow-step-num">3</div>
    <div class="flow-step-content">
      <strong>Cache Check</strong>
      <p>Look up the key in Redis. Cache hit? Return immediately.</p>
    </div>
  </div>
  <div class="flow-arrow animate-in" style="--step-delay: 5">&rarr;</div>
  <div class="flow-step animate-in" style="--step-delay: 6">
    <div class="flow-step-num">4</div>
    <div class="flow-step-content">
      <strong>Database Query</strong>
      <p>Cache miss: query the primary database, populate cache, return</p>
    </div>
  </div>
</div>
```

**CSS:**
```css
.flow-diagram {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin: var(--space-8) 0;
  overflow-x: auto;
  padding: var(--space-4) 0;
  -webkit-overflow-scrolling: touch;
}
.flow-step {
  display: flex;
  gap: var(--space-3);
  align-items: flex-start;
  background: var(--color-surface);
  padding: var(--space-4) var(--space-5);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  min-width: 180px;
  max-width: 240px;
  flex-shrink: 0;
  opacity: 0;
  transform: translateY(12px);
  transition: opacity var(--duration-normal) var(--ease-out), transform var(--duration-normal) var(--ease-out);
  transition-delay: calc(var(--step-delay) * 0.15s);
}
.flow-step.visible {
  opacity: 1;
  transform: translateY(0);
}
.flow-step-num {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-accent);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display);
  font-weight: 700;
  flex-shrink: 0;
}
.flow-step-content strong {
  font-family: var(--font-display);
  font-size: var(--text-sm);
  display: block;
  margin-bottom: var(--space-1);
}
.flow-step-content p {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  margin: 0;
}
.flow-arrow {
  font-size: var(--text-xl);
  color: var(--color-accent);
  flex-shrink: 0;
  opacity: 0;
  transition: opacity var(--duration-normal);
  transition-delay: calc(var(--step-delay) * 0.15s);
}
.flow-arrow.visible { opacity: 1; }

/* Responsive: vertical on mobile */
@media (max-width: 768px) {
  .flow-diagram {
    flex-direction: column;
    align-items: stretch;
    overflow-x: visible;
  }
  .flow-step {
    min-width: auto;
    max-width: none;
  }
  .flow-arrow {
    text-align: center;
    transform: rotate(90deg);
  }
}
```

**JS:**
```javascript
(function() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const items = entry.target.querySelectorAll('.animate-in');
        items.forEach(item => item.classList.add('visible'));
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.2 });

  document.querySelectorAll('.flow-diagram').forEach(d => observer.observe(d));
})();
```

**Usage:** Each `.flow-step` and `.flow-arrow` gets a `--step-delay` CSS variable (0, 1, 2, ...) for staggered reveal. The IntersectionObserver triggers the animation when the diagram scrolls into view.

---

## Concept Cards

Card grid for key concepts with icon, title, and brief description. Optional "Learn more" expand.

**HTML:**
```html
<div class="concept-cards stagger-children">
  <div class="concept-card animate-in" style="--card-color: var(--color-concept-1)">
    <div class="card-icon">&#x1F511;</div>
    <h4 class="card-title">Key-Value Store</h4>
    <p class="card-desc">Data is stored and retrieved using a unique key. Think of it like a dictionary: look up the word, get the definition.</p>
    <button class="card-expand-btn" onclick="toggleCardExpand(this)">Learn more</button>
    <div class="card-expanded">
      <p>Unlike relational databases where data lives in tables with rows and columns, key-value stores treat each entry as an opaque blob associated with a key. This simplicity enables extremely fast lookups but limits query flexibility.</p>
    </div>
  </div>
  <div class="concept-card animate-in" style="--card-color: var(--color-concept-2)">
    <div class="card-icon">&#x1F4A8;</div>
    <h4 class="card-title">In-Memory Storage</h4>
    <p class="card-desc">All data is kept in RAM, not on disk. Blazing fast reads and writes, but limited by available memory.</p>
  </div>
  <div class="concept-card animate-in" style="--card-color: var(--color-concept-3)">
    <div class="card-icon">&#x1F4E1;</div>
    <h4 class="card-title">Pub/Sub</h4>
    <p class="card-desc">Publish/Subscribe messaging: senders broadcast messages to channels, receivers listen on channels they care about.</p>
  </div>
</div>
```

**CSS:**
```css
.concept-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--space-4);
  margin: var(--space-6) 0;
}
.concept-card {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: var(--space-5);
  border-top: 3px solid var(--card-color);
  box-shadow: var(--shadow-sm);
  transition: transform var(--duration-fast), box-shadow var(--duration-fast);
}
.concept-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}
.card-icon { font-size: 1.5rem; margin-bottom: var(--space-2); }
.card-title {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: var(--text-base);
  margin-bottom: var(--space-2);
}
.card-desc {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  line-height: var(--leading-normal);
}
.card-expand-btn {
  margin-top: var(--space-3);
  background: none;
  border: none;
  font-family: var(--font-body);
  font-size: var(--text-xs);
  color: var(--color-accent);
  cursor: pointer;
  padding: 0;
  text-decoration: underline;
  text-underline-offset: 2px;
}
.card-expand-btn:hover { color: var(--color-accent-hover); }
.card-expanded {
  max-height: 0;
  overflow: hidden;
  opacity: 0;
  transition: max-height var(--duration-normal), opacity var(--duration-normal);
}
.card-expanded.open {
  max-height: 300px;
  opacity: 1;
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border-light);
}
.card-expanded p {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  line-height: var(--leading-normal);
}

@media (max-width: 768px) {
  .concept-cards { grid-template-columns: 1fr; }
}
```

**JS:**
```javascript
function toggleCardExpand(btn) {
  const expanded = btn.nextElementSibling;
  const isOpen = expanded.classList.contains('open');
  expanded.classList.toggle('open');
  btn.textContent = isOpen ? 'Learn more' : 'Show less';
}
```

**Usage:** Use 2-3 columns on desktop. Each card gets a `--card-color` for the top border accent. The "Learn more" button and `.card-expanded` block are optional -- omit both for simple cards.

---

## Expandable Accordion

For Q&A sections, FAQs, and long content that should be collapsed by default.

**HTML:**
```html
<div class="accordion" id="acc-1">
  <div class="accordion-item">
    <button class="accordion-header" onclick="toggleAccordion(this)">
      <span>When should I use this system instead of a relational database?</span>
      <span class="accordion-icon">+</span>
    </button>
    <div class="accordion-body">
      <p>Use it when you need sub-millisecond reads for frequently accessed data, and your data model fits a key-value pattern. If you need complex JOINs, aggregations, or ACID transactions across multiple records, stick with a relational database.</p>
    </div>
  </div>
  <div class="accordion-item">
    <button class="accordion-header" onclick="toggleAccordion(this)">
      <span>What happens when the server crashes? Is data lost?</span>
      <span class="accordion-icon">+</span>
    </button>
    <div class="accordion-body">
      <p>It depends on your persistence configuration. With AOF (Append Only File) set to <code>everysec</code>, you lose at most 1 second of writes. With RDB snapshots only, you could lose several minutes. With no persistence, everything is lost on restart.</p>
    </div>
  </div>
  <div class="accordion-item">
    <button class="accordion-header" onclick="toggleAccordion(this)">
      <span>How much memory do I need?</span>
      <span class="accordion-icon">+</span>
    </button>
    <div class="accordion-body">
      <p>Plan for your dataset size plus ~30-50% overhead for internal data structures. A dataset of 1 GB of raw data typically requires ~1.3-1.5 GB of RAM. Monitor usage and set a <code>maxmemory</code> policy to prevent OOM crashes.</p>
    </div>
  </div>
</div>
```

**CSS:**
```css
.accordion {
  margin: var(--space-6) 0;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.accordion-item {
  border-bottom: 1px solid var(--color-border-light);
}
.accordion-item:last-child { border-bottom: none; }
.accordion-header {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4) var(--space-5);
  background: var(--color-surface);
  border: none;
  cursor: pointer;
  font-family: var(--font-display);
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text);
  text-align: left;
  transition: background var(--duration-fast);
}
.accordion-header:hover { background: var(--color-surface-warm); }
.accordion-header.active { background: var(--color-surface-warm); }
.accordion-icon {
  font-size: var(--text-xl);
  font-weight: 300;
  color: var(--color-accent);
  transition: transform var(--duration-fast);
  flex-shrink: 0;
  margin-left: var(--space-3);
}
.accordion-header.active .accordion-icon {
  transform: rotate(45deg);
}
.accordion-body {
  max-height: 0;
  overflow: hidden;
  transition: max-height var(--duration-normal) var(--ease-out);
}
.accordion-body p, .accordion-body ul {
  padding: 0 var(--space-5) var(--space-5);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  line-height: var(--leading-normal);
}
.accordion-body code {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  background: var(--color-border-light);
  padding: 1px var(--space-1);
  border-radius: 3px;
}
```

**JS:**
```javascript
function toggleAccordion(header) {
  const item = header.parentElement;
  const body = item.querySelector('.accordion-body');
  const isActive = header.classList.contains('active');

  // Optional: close all others (single-open mode)
  const accordion = item.closest('.accordion');
  accordion.querySelectorAll('.accordion-header.active').forEach(other => {
    if (other !== header) {
      other.classList.remove('active');
      other.parentElement.querySelector('.accordion-body').style.maxHeight = null;
    }
  });

  // Toggle current
  if (isActive) {
    header.classList.remove('active');
    body.style.maxHeight = null;
  } else {
    header.classList.add('active');
    body.style.maxHeight = body.scrollHeight + 'px';
  }
}
```

**Usage:** For multi-open mode, remove the "close all others" block in the JS. The `+` icon rotates 45 degrees to become an `x` when open.

---

## Callout Boxes

Colored callouts for tips, warnings, insights, and informational notes. Left border colored by type.

**HTML:**
```html
<!-- Tip callout -->
<div class="callout callout-tip">
  <div class="callout-icon">&#x1F4A1;</div>
  <div class="callout-content">
    <strong>Tip:</strong> Set <code>maxmemory-policy allkeys-lru</code> in production. Without it, the server returns errors when memory is full instead of evicting old keys.
  </div>
</div>

<!-- Warning callout -->
<div class="callout callout-warning">
  <div class="callout-icon">&#x26A0;&#xFE0F;</div>
  <div class="callout-content">
    <strong>Warning:</strong> Never expose this service directly to the internet without authentication. By default, it accepts connections from any client on the bound interface.
  </div>
</div>

<!-- Info callout -->
<div class="callout callout-info">
  <div class="callout-icon">&#x2139;&#xFE0F;</div>
  <div class="callout-content">
    <strong>Note:</strong> The benchmarks in this section were measured on a single node with 32 GB RAM. Cluster mode introduces additional latency from cross-slot redirects.
  </div>
</div>

<!-- Insight callout -->
<div class="callout callout-insight">
  <div class="callout-icon">&#x1F52D;</div>
  <div class="callout-content">
    <strong>Architecture insight:</strong> The single-threaded event loop is a deliberate design choice, not a limitation. It eliminates lock contention and makes the codebase simpler. The trade-off: one slow command blocks everything.
  </div>
</div>
```

**CSS:**
```css
.callout {
  display: flex;
  gap: var(--space-4);
  padding: var(--space-5);
  border-radius: var(--radius-md);
  margin: var(--space-6) 0;
  border-left: 4px solid;
}
.callout-tip {
  background: var(--color-success-light);
  border-color: var(--color-success);
}
.callout-warning {
  background: var(--color-warning-light);
  border-color: var(--color-warning);
}
.callout-info {
  background: var(--color-info-light);
  border-color: var(--color-info);
}
.callout-insight {
  background: #F3EFF8;
  border-color: #7B6DAA;
}
.callout-icon {
  font-size: 1.3rem;
  flex-shrink: 0;
}
.callout-content {
  font-size: var(--text-sm);
  line-height: var(--leading-normal);
}
.callout-content code {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  background: rgba(0,0,0,0.06);
  padding: 1px var(--space-1);
  border-radius: 3px;
}
```

**Usage:** Four types: `callout-tip` (green, operational advice), `callout-warning` (yellow, pitfalls and dangers), `callout-info` (blue, context and neutral facts), `callout-insight` (purple, architectural or design insights). Every page should have at least one callout.

---

## Glossary Tooltips

Technical term definitions on hover (desktop) or tap (mobile). Uses `position: fixed` appended to `document.body` to avoid clipping by overflow containers.

**HTML:**
```html
<p>The system uses a
  <span class="glossary-term" data-definition="A concurrency model where a single thread runs an event loop that dispatches I/O operations asynchronously. No context switching or lock contention, but one slow operation blocks everything.">single-threaded event loop</span>
  to handle all client connections, achieving high throughput without the overhead of
  <span class="glossary-term" data-definition="When multiple threads or processes compete for the same lock or resource, causing them to wait. Eliminated in single-threaded architectures.">lock contention</span>.
</p>
```

**CSS:**
```css
.glossary-term {
  border-bottom: 2px dashed var(--color-accent-muted);
  cursor: pointer;
}
.glossary-tooltip {
  position: fixed;
  background: var(--color-text);
  color: white;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  max-width: 300px;
  z-index: 10000;
  box-shadow: var(--shadow-lg);
  line-height: var(--leading-normal);
  pointer-events: none;
  opacity: 0;
  transition: opacity var(--duration-fast);
}
.glossary-tooltip.visible { opacity: 1; }
.glossary-tooltip::before {
  content: '';
  position: absolute;
  bottom: 100%;
  left: 20px;
  border: 6px solid transparent;
  border-bottom-color: var(--color-text);
}
```

**JS:**
```javascript
(function() {
  let tooltip = null;

  function showTooltip(term) {
    if (tooltip) tooltip.remove();
    tooltip = document.createElement('div');
    tooltip.className = 'glossary-tooltip';
    tooltip.textContent = term.dataset.definition;
    document.body.appendChild(tooltip);

    const rect = term.getBoundingClientRect();
    const tipRect = tooltip.getBoundingClientRect();

    let left = rect.left + rect.width / 2 - tipRect.width / 2;
    let top = rect.bottom + 8;

    // Keep within viewport
    if (left < 8) left = 8;
    if (left + tipRect.width > window.innerWidth - 8) left = window.innerWidth - tipRect.width - 8;
    if (top + tipRect.height > window.innerHeight - 8) top = rect.top - tipRect.height - 8;

    tooltip.style.left = left + 'px';
    tooltip.style.top = top + 'px';
    requestAnimationFrame(() => tooltip.classList.add('visible'));
  }

  function hideTooltip() {
    if (tooltip) { tooltip.remove(); tooltip = null; }
  }

  // Desktop: hover
  document.addEventListener('mouseover', (e) => {
    const term = e.target.closest('.glossary-term');
    if (term) showTooltip(term);
  });
  document.addEventListener('mouseout', (e) => {
    if (e.target.closest('.glossary-term')) hideTooltip();
  });

  // Mobile: tap
  document.addEventListener('click', (e) => {
    const term = e.target.closest('.glossary-term');
    if (term) { e.preventDefault(); showTooltip(term); }
    else hideTooltip();
  });
})();
```

**Usage:** Add `data-definition` to every technical term on first use per page. Definitions should explain what the term means in context, not just a dictionary definition. Use `position: fixed` and `document.body.appendChild` -- never `position: absolute` inside a container (causes clipping).

---

## Level Badge

Small colored pill badge showing content difficulty level. Used in navigation headers and section titles.

**HTML:**
```html
<!-- Inline with heading -->
<h2>Core Architecture <span class="level-badge level-intermediate">Intermediate</span></h2>

<!-- In navigation -->
<nav class="page-nav">
  <a href="concepts.html">Core Concepts <span class="level-badge level-beginner">Beginner</span></a>
  <a href="architecture.html">Architecture <span class="level-badge level-intermediate">Intermediate</span></a>
  <a href="implementation.html">Implementation <span class="level-badge level-advanced">Advanced</span></a>
</nav>

<!-- Standalone -->
<span class="level-badge level-beginner">Beginner</span>
<span class="level-badge level-intermediate">Intermediate</span>
<span class="level-badge level-advanced">Advanced</span>
```

**CSS:**
```css
.level-badge {
  display: inline-block;
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  font-weight: 600;
  padding: 2px var(--space-2);
  border-radius: var(--radius-full);
  text-transform: uppercase;
  letter-spacing: 0.03em;
  vertical-align: middle;
  line-height: 1.4;
}
.level-beginner {
  background: var(--color-success-light);
  color: var(--color-success);
}
.level-intermediate {
  background: var(--color-warning-light);
  color: #B8860B;
}
.level-advanced {
  background: var(--color-error-light);
  color: var(--color-error);
}
```

**Usage:** Place inline with headings or navigation links. The badge is purely informational -- level filtering is handled by `data-level` attributes on content sections, not by the badge itself.
