# Skills Static Website — Design Spec

## Goal
A static website hosted on GitHub Pages that lets users browse skills from the `skills/` folder. Single-page app with sidebar navigation, full dark mode, full SKILL.md content rendered as readable HTML.

## Architecture

```
skills-playground/
  build.py                    # Python build script
  dist/                       # Generated output (gitignored)
    index.html                # The SPA (self-contained)
    examples/                 # Copied example HTML files
  .github/workflows/
    deploy.yml                # Auto-build + deploy on push
```

## Build Script (`build.py`)

**Input:** `skills/` directory
**Output:** `dist/` directory

Process:
1. Scan `skills/` recursively for directories containing a `SKILL.md` (pattern: `skills/**/*/SKILL.md`)
2. For each skill found:
   - Parse YAML frontmatter (`name`, `description`) and markdown body from SKILL.md
   - Collect reference markdown files from sibling `references/` directory
   - Collect example HTML files from sibling `examples/` directory (or parent)
3. Convert all markdown to HTML using Python `markdown` library with extensions: `tables`, `fenced_code`, `codehilite`, `toc`
4. Generate a single `index.html` with all skill content embedded as data (JSON in a script tag or inline HTML sections)
5. Copy example HTML files to `dist/examples/<skill-name>/`

**Dependencies:** `markdown`, `pyyaml` (pip installable)

## SPA Layout

### Sidebar (~250px, fixed left)
- Header: "Skills" title
- List of skill names (from frontmatter `name` field)
- Active skill highlighted with emerald accent (`#34d399`)
- Click to switch content in main area (no page reload)
- Collapsible to hamburger on mobile (< 768px)

### Main Content Area
For each skill, render in order:
1. **Header:** Skill name (h1) + description (subtitle)
2. **Body:** Full SKILL.md markdown rendered as styled HTML
3. **References:** Collapsible sections for each reference doc (click to expand/collapse)
4. **Examples:** Links to example HTML files (open in new tab)

### Navigation
- URL hash routing (`#skill-name`) for direct linking
- First skill selected by default on load
- Sidebar items update the hash and swap the main content

## Dark Mode Palette

| Element | Color |
|---------|-------|
| Page background | `#0f172a` (slate-900) |
| Sidebar background | `#111827` (gray-900) |
| Sidebar active item bg | `rgba(52, 211, 153, 0.1)` |
| Sidebar active item text | `#34d399` (emerald-400) |
| Sidebar inactive text | `#9ca3af` (gray-400) |
| Main text | `#e2e8f0` (slate-200) |
| Headings | `#f1f5f9` (slate-50) |
| Code block background | `#1e293b` (slate-800) |
| Code text | `#e2e8f0` |
| Links | `#34d399` |
| Table borders | `#334155` (slate-700) |
| Horizontal rules | `#334155` |
| Blockquote border | `#34d399` |
| Blockquote background | `rgba(52, 211, 153, 0.05)` |

## Typography

- Body: system-ui, -apple-system, sans-serif
- Code: 'JetBrains Mono', 'Fira Code', monospace
- Headings: Bold, slight letter-spacing
- Base font size: 16px, line-height: 1.7

## Responsive Behavior

- **Desktop (>768px):** Sidebar fixed left, main content scrolls
- **Mobile (<768px):** Sidebar hidden, hamburger menu toggles sidebar as overlay

## GitHub Action (`.github/workflows/deploy.yml`)

- **Trigger:** Push to `main` branch
- **Path filter:** `skills/**`, `build.py`
- **Steps:**
  1. Checkout repo
  2. Setup Python 3.x
  3. Install dependencies (`pip install markdown pyyaml`)
  4. Run `python build.py`
  5. Upload `dist/` as artifact
  6. Deploy to GitHub Pages using `actions/deploy-pages`
- **Permissions:** `pages: write`, `id-token: write`, `contents: read`

## Content Handling

### Markdown Features Supported
- Headings (h1-h6)
- Bold, italic, strikethrough
- Ordered/unordered lists
- Tables (with styled borders)
- Fenced code blocks (with syntax highlighting via codehilite)
- Blockquotes
- Horizontal rules
- Links (external open in new tab)
- Images (if any)

### YAML Frontmatter
```yaml
---
name: skill-name
description: "Short description"
---
```

### Skill Discovery
The build script walks `skills/` looking for any `SKILL.md` file. The directory structure for paper-to-course is:
```
skills/paper-to-course/
  examples/                    # Example HTML outputs
  paper-to-course/
    SKILL.md                   # Skill definition
    references/                # Reference docs
    evals/                     # Eval data (not rendered)
```

The build script handles this nested structure — it finds `SKILL.md` wherever it lives, then looks for `references/` as a sibling and `examples/` in the parent tree.
