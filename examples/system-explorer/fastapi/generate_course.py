#!/usr/bin/env python3
"""Generate the FastAPI interactive course HTML pages from markdown source files."""

import json
import re
import html as html_module
from pathlib import Path

BASE_DIR = Path("/home/cyyeh/skills-playground/examples/system-explorer/fastapi")

# Page definitions: (filename, source_md, title, short_title)
PAGES = [
    ("index.html", "00-metadata.md", "FastAPI Course", "Home"),
    ("concepts.html", "01-concepts.md", "Core Concepts", "Concepts"),
    ("architecture.html", "02-architecture.md", "Architecture & Internals", "Architecture"),
    ("getting-started.html", "03-getting-started.md", "Getting Started", "Getting Started"),
    ("implementation.html", "04-implementation.md", "Implementation Patterns", "Implementation"),
    ("use-cases.html", "05-use-cases.md", "Use Cases & Adoption", "Use Cases"),
    ("ecosystem.html", "06-ecosystem.md", "Ecosystem & Integrations", "Ecosystem"),
    ("performance.html", "07-performance.md", "Performance & Optimization", "Performance"),
    ("advanced.html", "08-advanced.md", "Advanced Topics", "Advanced"),
    ("tradeoffs.html", "09-tradeoffs.md", "Tradeoffs & Alternatives", "Tradeoffs"),
]

NAV_ICONS = [
    "&#9733;",  # star - Home
    "&#9670;",  # diamond - Concepts
    "&#9881;",  # gear - Architecture
    "&#9654;",  # play - Getting Started
    "&#9998;",  # pencil - Implementation
    "&#9992;",  # airplane - Use Cases
    "&#9741;",  # puzzle - Ecosystem
    "&#9889;",  # lightning - Performance
    "&#9733;",  # star - Advanced
    "&#9878;",  # scales - Tradeoffs
]


def escape_html(text):
    return html_module.escape(text)


def convert_inline_markdown(text):
    """Convert inline markdown (bold, italic, code, links) to HTML."""
    # Inline code (backticks) - must come before bold/italic
    text = re.sub(r'`([^`]+)`', r'<code class="inline-code">\1</code>', text)
    # Bold + italic
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    # Em dash
    text = text.replace(' -- ', ' &mdash; ')
    return text


def slugify(text):
    """Create a URL-friendly slug from text."""
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[\s_]+', '-', text)
    return text.strip('-')


def detect_code_language(code_block, lang_hint=""):
    """Detect the language for syntax highlighting."""
    lang = lang_hint.strip().lower()
    if lang in ("python", "py"):
        return "python"
    if lang in ("bash", "shell", "sh"):
        return "bash"
    if lang in ("yaml", "yml"):
        return "yaml"
    if lang in ("dockerfile",):
        return "dockerfile"
    if lang in ("nginx",):
        return "nginx"
    if lang in ("javascript", "js"):
        return "javascript"
    if lang in ("sql",):
        return "sql"
    # Auto-detect from content
    if "import " in code_block or "def " in code_block or "class " in code_block or "from " in code_block:
        return "python"
    if code_block.strip().startswith(("$", "#", "pip ", "uvicorn ", "gunicorn ", "alembic ", "curl ", "python ", "fastapi ")):
        return "bash"
    if "apiVersion:" in code_block or "kind:" in code_block:
        return "yaml"
    if "FROM " in code_block and ("RUN " in code_block or "CMD " in code_block):
        return "dockerfile"
    if "server {" in code_block or "location " in code_block:
        return "nginx"
    return "text"


def tokenize_and_highlight(code, lang):
    """Token-based syntax highlighting that avoids nested span issues.

    Works by scanning through the code character-by-character, identifying tokens,
    and wrapping them in spans. This avoids the problem of regex-on-HTML that causes
    nested/broken spans.
    """
    if lang == "text":
        return escape_html(code)

    PY_KEYWORDS = {
        'from', 'import', 'class', 'def', 'async', 'await', 'return', 'yield',
        'if', 'else', 'elif', 'for', 'while', 'try', 'except', 'finally',
        'with', 'as', 'in', 'not', 'and', 'or', 'is', 'None', 'True', 'False',
        'raise', 'global', 'lambda', 'pass', 'break', 'continue', 'del',
    }
    PY_BUILTINS = {
        'print', 'len', 'range', 'list', 'dict', 'set', 'tuple', 'int', 'str',
        'float', 'bool', 'type', 'isinstance', 'getattr', 'setattr', 'hasattr',
        'super', 'property', 'staticmethod', 'classmethod', 'enumerate', 'zip',
        'map', 'filter', 'sorted', 'reversed', 'any', 'all', 'min', 'max',
        'abs', 'round', 'open', 'id', 'hex', 'oct', 'bin', 'repr',
    }
    BASH_KEYWORDS = {
        'if', 'then', 'else', 'fi', 'for', 'do', 'done', 'while', 'case', 'esac',
        'function', 'return', 'export', 'source', 'echo', 'cd', 'ls', 'mkdir',
        'rm', 'cp', 'mv', 'grep', 'sed', 'awk', 'find', 'cat', 'head', 'tail',
    }

    is_python = lang == "python"
    is_bash = lang in ("bash", "shell")
    is_yaml = lang in ("yaml", "dockerfile", "nginx")
    is_js = lang == "javascript"

    tokens = []  # list of (text, css_class_or_None)
    i = 0
    n = len(code)

    while i < n:
        ch = code[i]

        # === Triple-quoted strings (Python) ===
        if is_python and i + 2 < n and code[i:i+3] in ('"""', "'''"):
            quote = code[i:i+3]
            j = code.find(quote, i + 3)
            if j == -1:
                j = n
            else:
                j += 3
            tokens.append((code[i:j], "hl-str"))
            i = j
            continue

        # === Strings (single/double quote) ===
        if ch in ('"', "'") and (is_python or is_bash or is_yaml or is_js):
            # Check for f-string prefix
            prefix = ""
            if is_python and i > 0 and code[i-1] in ('f', 'r', 'b') and (i < 2 or not code[i-2].isalnum()):
                # Already emitted the prefix as part of an identifier; pop it
                if tokens and tokens[-1][1] is None and tokens[-1][0] in ('f', 'r', 'b'):
                    prefix = tokens.pop()[0]
            quote_char = ch
            j = i + 1
            while j < n:
                if code[j] == '\\' and j + 1 < n:
                    j += 2
                    continue
                if code[j] == quote_char:
                    j += 1
                    break
                j += 1
            tokens.append((prefix + code[i:j], "hl-str"))
            i = j
            continue

        # === Comments ===
        if ch == '#' and (is_python or is_bash or is_yaml):
            j = code.find('\n', i)
            if j == -1:
                j = n
            tokens.append((code[i:j], "hl-cmt"))
            i = j
            continue

        # JS comments
        if is_js and ch == '/' and i + 1 < n and code[i+1] == '/':
            j = code.find('\n', i)
            if j == -1:
                j = n
            tokens.append((code[i:j], "hl-cmt"))
            i = j
            continue

        # === Decorators (Python) ===
        if is_python and ch == '@' and (i == 0 or code[i-1] in (' ', '\n', '\t')):
            j = i + 1
            while j < n and (code[j].isalnum() or code[j] in '_.'):
                j += 1
            tokens.append((code[i:j], "hl-dec"))
            i = j
            continue

        # === Numbers ===
        if ch.isdigit() and (i == 0 or not code[i-1].isalnum()):
            j = i
            while j < n and (code[j].isdigit() or code[j] == '.'):
                j += 1
            tokens.append((code[i:j], "hl-num"))
            i = j
            continue

        # === Identifiers and keywords ===
        if ch.isalpha() or ch == '_':
            j = i
            while j < n and (code[j].isalnum() or code[j] == '_'):
                j += 1
            word = code[i:j]

            if is_python:
                if word in PY_KEYWORDS:
                    tokens.append((word, "hl-kw"))
                elif word in PY_BUILTINS:
                    tokens.append((word, "hl-fn"))
                else:
                    tokens.append((word, None))
            elif is_bash:
                if word in BASH_KEYWORDS:
                    tokens.append((word, "hl-kw"))
                else:
                    tokens.append((word, None))
            elif is_yaml:
                # YAML keys are handled differently - check if followed by colon
                if j < n and code[j] == ':':
                    tokens.append((word, "hl-kw"))
                else:
                    tokens.append((word, None))
            elif is_js:
                js_kws = {'const', 'let', 'var', 'function', 'return', 'if', 'else', 'for', 'while', 'new', 'this', 'async', 'await', 'import', 'from', 'export', 'default', 'class', 'extends', 'true', 'false', 'null', 'undefined'}
                if word in js_kws:
                    tokens.append((word, "hl-kw"))
                else:
                    tokens.append((word, None))
            else:
                tokens.append((word, None))
            i = j
            continue

        # === Everything else (operators, whitespace, punctuation) ===
        tokens.append((ch, None))
        i += 1

    # Build the HTML from tokens
    parts = []
    for text, cls in tokens:
        escaped = escape_html(text)
        if cls:
            parts.append(f'<span class="{cls}">{escaped}</span>')
        else:
            parts.append(escaped)
    return ''.join(parts)


def highlight_code(code, lang):
    """Apply syntax highlighting based on language."""
    return tokenize_and_highlight(code, lang)


def parse_markdown_to_html(md_content):
    """Convert markdown content to structured HTML with level markers."""
    lines = md_content.split('\n')
    html_parts = []
    current_level = None
    in_code_block = False
    code_lang = ""
    code_lines = []
    in_table = False
    table_rows = []
    table_is_header = True
    in_list = False
    list_items = []
    list_type = "ul"
    in_paragraph = False
    para_lines = []

    def flush_paragraph():
        nonlocal in_paragraph, para_lines
        if in_paragraph and para_lines:
            text = ' '.join(para_lines)
            text = convert_inline_markdown(text)
            html_parts.append(f'<p>{text}</p>')
            para_lines = []
            in_paragraph = False

    def flush_list():
        nonlocal in_list, list_items, list_type
        if in_list and list_items:
            items_html = '\n'.join(f'<li>{convert_inline_markdown(item)}</li>' for item in list_items)
            html_parts.append(f'<{list_type} class="content-list">\n{items_html}\n</{list_type}>')
            list_items = []
            in_list = False

    def flush_table():
        nonlocal in_table, table_rows, table_is_header
        if in_table and table_rows:
            thead = ""
            tbody_rows = []
            for i, row in enumerate(table_rows):
                cells = [c.strip() for c in row.split('|')[1:-1]]
                if not cells:
                    cells = [c.strip() for c in row.split('|') if c.strip()]
                if i == 0:
                    thead_cells = ''.join(f'<th>{convert_inline_markdown(c)}</th>' for c in cells)
                    thead = f'<thead><tr>{thead_cells}</tr></thead>'
                elif i == 1:
                    continue  # separator row
                else:
                    row_cells = ''.join(f'<td>{convert_inline_markdown(c)}</td>' for c in cells)
                    tbody_rows.append(f'<tr>{row_cells}</tr>')
            tbody = f'<tbody>{"".join(tbody_rows)}</tbody>'
            html_parts.append(f'<div class="table-wrapper"><table>{thead}{tbody}</table></div>')
            table_rows = []
            in_table = False
            table_is_header = True

    i = 0
    while i < len(lines):
        line = lines[i]

        # Code block detection
        if line.strip().startswith('```'):
            if not in_code_block:
                flush_paragraph()
                flush_list()
                flush_table()
                in_code_block = True
                code_lang = line.strip()[3:].strip()
                code_lines = []
                i += 1
                continue
            else:
                # End of code block
                code_content = '\n'.join(code_lines)
                lang = detect_code_language(code_content, code_lang)
                highlighted = highlight_code(code_content, lang)
                code_id = f"code-{abs(hash(code_content)) % 100000}"
                html_parts.append(f'''<div class="code-block-wrapper">
<div class="code-header">
<span class="code-lang">{lang}</span>
<button class="copy-btn" onclick="copyCode('{code_id}')" title="Copy to clipboard">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
Copy
</button>
</div>
<pre><code id="{code_id}" class="language-{lang}">{highlighted}</code></pre>
</div>''')
                in_code_block = False
                code_lang = ""
                code_lines = []
                i += 1
                continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        stripped = line.strip()

        # Level markers
        if stripped.startswith('<!-- level:'):
            flush_paragraph()
            flush_list()
            flush_table()
            level_match = re.match(r'<!-- level:(\w+) -->', stripped)
            if level_match:
                if current_level:
                    html_parts.append('</div>')  # close previous level
                current_level = level_match.group(1)
                level_labels = {
                    'beginner': 'Beginner',
                    'intermediate': 'Intermediate',
                    'advanced': 'Advanced'
                }
                label = level_labels.get(current_level, current_level.title())
                html_parts.append(f'<div class="level-section" data-level="{current_level}">')
                html_parts.append(f'<div class="level-badge level-badge-{current_level}">{label}</div>')
            i += 1
            continue

        # Empty line
        if not stripped:
            flush_paragraph()
            flush_list()
            if in_table:
                flush_table()
            i += 1
            continue

        # Headers
        header_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if header_match:
            flush_paragraph()
            flush_list()
            flush_table()
            level = len(header_match.group(1))
            text = header_match.group(2)
            slug = slugify(text)
            text_html = convert_inline_markdown(text)
            # Skip the first H1 as it becomes the page title
            if level == 1:
                i += 1
                continue
            html_parts.append(f'<h{level} id="{slug}" class="section-header">'
                            f'<a href="#{slug}" class="header-anchor" aria-label="Link to {escape_html(text)}">#</a>'
                            f'{text_html}</h{level}>')
            i += 1
            continue

        # Table
        if '|' in stripped and not stripped.startswith('```'):
            flush_paragraph()
            flush_list()
            if not in_table:
                in_table = True
                table_rows = []
            table_rows.append(stripped)
            i += 1
            continue
        elif in_table:
            flush_table()

        # List items
        list_match = re.match(r'^(\s*)[-*]\s+(.+)$', stripped)
        num_list_match = re.match(r'^(\s*)\d+\.\s+(.+)$', stripped)
        if list_match or num_list_match:
            flush_paragraph()
            flush_table()
            if not in_list:
                in_list = True
                list_items = []
                list_type = "ol" if num_list_match else "ul"
            match = list_match or num_list_match
            list_items.append(match.group(2))
            i += 1
            continue
        elif in_list:
            flush_list()

        # Paragraph text (plain ASCII diagram blocks)
        if stripped.startswith('+--') or stripped.startswith('|') and not in_table:
            flush_paragraph()
            # Collect the whole diagram
            diagram_lines = []
            while i < len(lines):
                s = lines[i].strip() if i < len(lines) else ""
                if s.startswith('+') or s.startswith('|') or s.startswith(' '):
                    if not s:
                        break
                    diagram_lines.append(lines[i])
                    i += 1
                else:
                    break
            if diagram_lines:
                diagram_text = escape_html('\n'.join(diagram_lines))
                html_parts.append(f'<pre class="diagram">{diagram_text}</pre>')
            continue

        # Regular paragraph
        if not in_paragraph:
            in_paragraph = True
            para_lines = []
        para_lines.append(stripped)
        i += 1

    # Flush remaining
    flush_paragraph()
    flush_list()
    flush_table()
    if current_level:
        html_parts.append('</div>')  # close last level

    return '\n'.join(html_parts)


def get_shared_css():
    return '''
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
      --primary: #009688;
      --primary-dark: #00796b;
      --primary-light: #4db6ac;
      --primary-bg: #e0f2f1;
      --accent: #00bcd4;
      --accent-dark: #0097a7;

      --bg: #fafbfc;
      --bg-card: #ffffff;
      --bg-code: #1e1e2e;
      --bg-sidebar: #0d1117;

      --text: #1a1a2e;
      --text-secondary: #4a5568;
      --text-muted: #718096;
      --text-light: #a0aec0;
      --text-on-dark: #e2e8f0;

      --border: #e2e8f0;
      --border-light: #edf2f7;

      --beginner: #4caf50;
      --beginner-bg: #e8f5e9;
      --intermediate: #ff9800;
      --intermediate-bg: #fff3e0;
      --advanced: #f44336;
      --advanced-bg: #ffebee;

      --shadow-sm: 0 1px 3px rgba(0,0,0,0.08);
      --shadow-md: 0 4px 12px rgba(0,0,0,0.1);
      --shadow-lg: 0 8px 30px rgba(0,0,0,0.12);

      --radius-sm: 6px;
      --radius-md: 10px;
      --radius-lg: 16px;

      --transition: 0.2s ease;
    }

    * { margin: 0; padding: 0; box-sizing: border-box; }

    html {
      scroll-behavior: smooth;
      font-size: 16px;
    }

    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.7;
      min-height: 100vh;
    }

    /* ===== LAYOUT ===== */
    .page-layout {
      display: flex;
      min-height: 100vh;
    }

    /* ===== SIDEBAR ===== */
    .sidebar {
      width: 280px;
      background: var(--bg-sidebar);
      color: var(--text-on-dark);
      position: fixed;
      top: 0;
      left: 0;
      bottom: 0;
      overflow-y: auto;
      z-index: 100;
      transition: transform 0.3s ease;
      display: flex;
      flex-direction: column;
    }

    .sidebar-header {
      padding: 24px 20px 16px;
      border-bottom: 1px solid rgba(255,255,255,0.08);
    }

    .sidebar-logo {
      display: flex;
      align-items: center;
      gap: 10px;
      text-decoration: none;
      color: inherit;
    }

    .sidebar-logo-icon {
      width: 36px;
      height: 36px;
      background: var(--primary);
      border-radius: var(--radius-sm);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      font-weight: 700;
      color: white;
    }

    .sidebar-logo-text {
      font-size: 18px;
      font-weight: 700;
      color: white;
    }

    .sidebar-logo-sub {
      font-size: 11px;
      color: var(--text-light);
      text-transform: uppercase;
      letter-spacing: 1.5px;
      margin-top: 2px;
    }

    .sidebar-nav {
      padding: 12px 0;
      flex: 1;
    }

    .nav-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 20px;
      color: var(--text-light);
      text-decoration: none;
      font-size: 14px;
      font-weight: 400;
      transition: all var(--transition);
      border-left: 3px solid transparent;
      position: relative;
    }

    .nav-item:hover {
      background: rgba(255,255,255,0.05);
      color: white;
    }

    .nav-item.active {
      background: rgba(0,150,136,0.15);
      color: var(--primary-light);
      border-left-color: var(--primary);
      font-weight: 500;
    }

    .nav-icon {
      width: 20px;
      text-align: center;
      font-size: 14px;
      opacity: 0.7;
    }

    .nav-item.active .nav-icon { opacity: 1; }

    .nav-visited::after {
      content: '';
      position: absolute;
      right: 16px;
      width: 6px;
      height: 6px;
      background: var(--primary);
      border-radius: 50%;
    }

    .sidebar-footer {
      padding: 16px 20px;
      border-top: 1px solid rgba(255,255,255,0.08);
      font-size: 12px;
      color: var(--text-muted);
    }

    .progress-bar-container {
      background: rgba(255,255,255,0.1);
      border-radius: 10px;
      height: 6px;
      margin-top: 8px;
      overflow: hidden;
    }

    .progress-bar {
      height: 100%;
      background: var(--primary);
      border-radius: 10px;
      transition: width 0.5s ease;
    }

    /* ===== MAIN CONTENT ===== */
    .main-content {
      margin-left: 280px;
      flex: 1;
      min-width: 0;
    }

    /* ===== TOP BAR ===== */
    .top-bar {
      position: sticky;
      top: 0;
      z-index: 50;
      background: rgba(255,255,255,0.92);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      padding: 12px 40px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }

    .page-title-bar {
      font-size: 16px;
      font-weight: 600;
      color: var(--text);
    }

    .level-selector {
      display: flex;
      background: var(--bg);
      border-radius: var(--radius-md);
      padding: 3px;
      gap: 2px;
      border: 1px solid var(--border);
    }

    .level-btn {
      padding: 6px 16px;
      border: none;
      background: transparent;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      transition: all var(--transition);
      color: var(--text-secondary);
      font-family: inherit;
    }

    .level-btn:hover { background: rgba(0,0,0,0.04); }

    .level-btn.active {
      background: white;
      color: var(--text);
      box-shadow: var(--shadow-sm);
    }

    .level-btn[data-level="beginner"].active { color: var(--beginner); }
    .level-btn[data-level="intermediate"].active { color: var(--intermediate); }
    .level-btn[data-level="advanced"].active { color: var(--advanced); }

    .mobile-menu-btn {
      display: none;
      background: none;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 6px 10px;
      cursor: pointer;
      font-size: 20px;
      color: var(--text);
    }

    /* ===== CONTENT AREA ===== */
    .content-area {
      max-width: 900px;
      margin: 0 auto;
      padding: 40px 40px 80px;
    }

    .page-header {
      margin-bottom: 40px;
      padding-bottom: 24px;
      border-bottom: 2px solid var(--primary-bg);
    }

    .page-header h1 {
      font-size: 2.2rem;
      font-weight: 700;
      color: var(--text);
      letter-spacing: -0.02em;
      margin-bottom: 8px;
    }

    .page-header .subtitle {
      font-size: 1.1rem;
      color: var(--text-secondary);
      font-weight: 400;
    }

    /* ===== LEVEL SECTIONS ===== */
    .level-section {
      margin-bottom: 32px;
      animation: fadeIn 0.3s ease;
    }

    .level-section[data-level].hidden {
      display: none;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .level-badge {
      display: inline-block;
      padding: 4px 14px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      margin-bottom: 20px;
    }

    .level-badge-beginner { background: var(--beginner-bg); color: var(--beginner); }
    .level-badge-intermediate { background: var(--intermediate-bg); color: var(--intermediate); }
    .level-badge-advanced { background: var(--advanced-bg); color: var(--advanced); }

    /* ===== TYPOGRAPHY ===== */
    .section-header {
      margin-top: 2rem;
      margin-bottom: 1rem;
      position: relative;
      padding-left: 0;
    }

    h2.section-header {
      font-size: 1.65rem;
      font-weight: 700;
      color: var(--text);
      padding-bottom: 8px;
      border-bottom: 1px solid var(--border-light);
    }

    h3.section-header {
      font-size: 1.3rem;
      font-weight: 600;
      color: var(--text);
    }

    h4.section-header {
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--text-secondary);
    }

    .header-anchor {
      position: absolute;
      left: -24px;
      color: var(--primary);
      text-decoration: none;
      opacity: 0;
      transition: opacity var(--transition);
      font-weight: 400;
    }

    .section-header:hover .header-anchor { opacity: 1; }

    p {
      margin-bottom: 1rem;
      color: var(--text);
      line-height: 1.8;
    }

    .content-list {
      margin: 0 0 1.2rem 1.5rem;
      line-height: 1.9;
    }

    .content-list li {
      margin-bottom: 4px;
      color: var(--text);
    }

    .content-list li::marker {
      color: var(--primary);
    }

    .inline-code {
      background: var(--primary-bg);
      color: var(--primary-dark);
      padding: 2px 7px;
      border-radius: 4px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.88em;
      font-weight: 500;
    }

    a {
      color: var(--primary);
      text-decoration: none;
      border-bottom: 1px solid transparent;
      transition: border-color var(--transition);
    }

    a:hover {
      border-bottom-color: var(--primary);
    }

    strong { font-weight: 600; }

    /* ===== CODE BLOCKS ===== */
    .code-block-wrapper {
      margin: 1.2rem 0 1.5rem;
      border-radius: var(--radius-md);
      overflow: hidden;
      box-shadow: var(--shadow-md);
      border: 1px solid rgba(0,0,0,0.1);
    }

    .code-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #181825;
      padding: 8px 16px;
      border-bottom: 1px solid rgba(255,255,255,0.06);
    }

    .code-lang {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      color: var(--text-light);
      text-transform: uppercase;
      letter-spacing: 1px;
    }

    .copy-btn {
      display: flex;
      align-items: center;
      gap: 6px;
      background: rgba(255,255,255,0.08);
      border: 1px solid rgba(255,255,255,0.1);
      color: var(--text-light);
      border-radius: var(--radius-sm);
      padding: 4px 12px;
      font-size: 12px;
      font-family: inherit;
      cursor: pointer;
      transition: all var(--transition);
    }

    .copy-btn:hover {
      background: rgba(255,255,255,0.15);
      color: white;
    }

    .copy-btn.copied {
      background: var(--primary);
      color: white;
      border-color: var(--primary);
    }

    pre {
      background: var(--bg-code);
      color: #cdd6f4;
      padding: 20px;
      overflow-x: auto;
      font-family: 'JetBrains Mono', monospace;
      font-size: 13.5px;
      line-height: 1.65;
      tab-size: 4;
    }

    pre.diagram {
      background: var(--bg);
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 20px;
      margin: 1rem 0 1.5rem;
      font-size: 13px;
    }

    code {
      font-family: 'JetBrains Mono', monospace;
    }

    /* Syntax highlighting */
    .hl-kw { color: #cba6f7; }  /* purple - keywords */
    .hl-str { color: #a6e3a1; } /* green - strings */
    .hl-cmt { color: #6c7086; font-style: italic; } /* gray - comments */
    .hl-num { color: #fab387; } /* peach - numbers */
    .hl-fn { color: #89b4fa; }  /* blue - functions */
    .hl-dec { color: #f9e2af; } /* yellow - decorators */

    /* ===== TABLES ===== */
    .table-wrapper {
      overflow-x: auto;
      margin: 1rem 0 1.5rem;
      border-radius: var(--radius-md);
      border: 1px solid var(--border);
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }

    thead {
      background: var(--primary-bg);
    }

    th {
      padding: 12px 16px;
      text-align: left;
      font-weight: 600;
      color: var(--primary-dark);
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    td {
      padding: 10px 16px;
      border-top: 1px solid var(--border-light);
      color: var(--text);
    }

    tbody tr:hover {
      background: rgba(0,150,136,0.03);
    }

    /* ===== NAV FOOTER ===== */
    .page-nav {
      display: flex;
      justify-content: space-between;
      align-items: stretch;
      gap: 16px;
      margin-top: 60px;
      padding-top: 32px;
      border-top: 2px solid var(--border-light);
    }

    .page-nav-link {
      flex: 1;
      display: flex;
      flex-direction: column;
      padding: 20px;
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      text-decoration: none;
      color: var(--text);
      transition: all var(--transition);
    }

    .page-nav-link:hover {
      border-color: var(--primary);
      box-shadow: var(--shadow-md);
      transform: translateY(-2px);
    }

    .page-nav-label {
      font-size: 12px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 4px;
    }

    .page-nav-title {
      font-size: 16px;
      font-weight: 600;
      color: var(--primary-dark);
    }

    .page-nav-link.next { text-align: right; }

    .page-nav-placeholder { flex: 1; }

    /* ===== INDEX PAGE ===== */
    .hero {
      text-align: center;
      padding: 60px 20px 50px;
      background: linear-gradient(135deg, var(--primary-bg) 0%, #b2dfdb 50%, #e0f7fa 100%);
      border-radius: var(--radius-lg);
      margin-bottom: 48px;
      position: relative;
      overflow: hidden;
    }

    .hero::before {
      content: '';
      position: absolute;
      top: -50%;
      left: -50%;
      width: 200%;
      height: 200%;
      background: radial-gradient(circle at 30% 50%, rgba(0,150,136,0.08) 0%, transparent 50%);
    }

    .hero h1 {
      font-size: 3rem;
      font-weight: 800;
      color: var(--primary-dark);
      letter-spacing: -0.03em;
      margin-bottom: 12px;
      position: relative;
    }

    .hero .tagline {
      font-size: 1.2rem;
      color: var(--text-secondary);
      max-width: 600px;
      margin: 0 auto 24px;
      position: relative;
    }

    .hero-stats {
      display: flex;
      justify-content: center;
      gap: 40px;
      margin-top: 30px;
      position: relative;
    }

    .hero-stat {
      text-align: center;
    }

    .hero-stat-value {
      font-size: 1.8rem;
      font-weight: 700;
      color: var(--primary-dark);
    }

    .hero-stat-label {
      font-size: 12px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 1px;
    }

    .section-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 20px;
      margin: 32px 0;
    }

    .section-card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 24px;
      text-decoration: none;
      color: var(--text);
      transition: all 0.25s ease;
      display: flex;
      flex-direction: column;
      gap: 8px;
      position: relative;
      overflow: hidden;
    }

    .section-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: var(--primary);
      transform: scaleX(0);
      transition: transform 0.25s ease;
    }

    .section-card:hover {
      border-color: var(--primary-light);
      box-shadow: var(--shadow-md);
      transform: translateY(-3px);
    }

    .section-card:hover::before {
      transform: scaleX(1);
    }

    .section-card-num {
      font-size: 32px;
      font-weight: 800;
      color: var(--primary-bg);
      line-height: 1;
    }

    .section-card-title {
      font-size: 17px;
      font-weight: 600;
      color: var(--text);
    }

    .section-card-desc {
      font-size: 14px;
      color: var(--text-secondary);
      line-height: 1.6;
    }

    /* ===== COLLAPSIBLE ===== */
    .collapsible-trigger {
      display: flex;
      align-items: center;
      gap: 8px;
      width: 100%;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 12px 16px;
      cursor: pointer;
      font-family: inherit;
      font-size: 15px;
      font-weight: 500;
      color: var(--text);
      text-align: left;
      transition: all var(--transition);
      margin: 1rem 0 0.5rem;
    }

    .collapsible-trigger:hover {
      background: var(--primary-bg);
      border-color: var(--primary-light);
    }

    .collapsible-trigger .arrow {
      transition: transform 0.2s ease;
      font-size: 12px;
    }

    .collapsible-trigger.open .arrow {
      transform: rotate(90deg);
    }

    .collapsible-content {
      display: none;
      padding: 0 16px 16px;
      animation: fadeIn 0.2s ease;
    }

    .collapsible-content.open { display: block; }

    /* ===== QUIZ ===== */
    .quiz-container {
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 24px;
      margin: 2rem 0;
    }

    .quiz-title {
      font-size: 16px;
      font-weight: 600;
      color: var(--text);
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .quiz-question {
      font-size: 15px;
      margin-bottom: 12px;
      color: var(--text);
    }

    .quiz-option {
      display: block;
      width: 100%;
      text-align: left;
      padding: 10px 16px;
      margin: 6px 0;
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      cursor: pointer;
      font-family: inherit;
      font-size: 14px;
      color: var(--text);
      transition: all var(--transition);
    }

    .quiz-option:hover:not(.selected) {
      border-color: var(--primary-light);
      background: var(--primary-bg);
    }

    .quiz-option.correct {
      background: var(--beginner-bg);
      border-color: var(--beginner);
      color: #2e7d32;
    }

    .quiz-option.incorrect {
      background: var(--advanced-bg);
      border-color: var(--advanced);
      color: #c62828;
    }

    .quiz-feedback {
      margin-top: 12px;
      padding: 12px;
      border-radius: var(--radius-sm);
      font-size: 14px;
      display: none;
    }

    .quiz-feedback.show { display: block; }

    .quiz-feedback.correct {
      background: var(--beginner-bg);
      color: #2e7d32;
    }

    .quiz-feedback.incorrect {
      background: var(--advanced-bg);
      color: #c62828;
    }

    /* ===== TOOLTIP ===== */
    .tooltip-wrapper {
      position: relative;
      display: inline;
      cursor: help;
      border-bottom: 1px dashed var(--primary);
    }

    .tooltip-text {
      visibility: hidden;
      opacity: 0;
      position: absolute;
      bottom: calc(100% + 8px);
      left: 50%;
      transform: translateX(-50%);
      background: var(--bg-sidebar);
      color: var(--text-on-dark);
      padding: 8px 14px;
      border-radius: var(--radius-sm);
      font-size: 13px;
      white-space: nowrap;
      z-index: 200;
      box-shadow: var(--shadow-lg);
      transition: all 0.15s ease;
      pointer-events: none;
    }

    .tooltip-wrapper:hover .tooltip-text {
      visibility: visible;
      opacity: 1;
    }

    /* ===== RESPONSIVE ===== */
    .sidebar-overlay {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.5);
      z-index: 90;
    }

    @media (max-width: 1024px) {
      .sidebar {
        transform: translateX(-100%);
      }
      .sidebar.open {
        transform: translateX(0);
      }
      .sidebar-overlay.open {
        display: block;
      }
      .main-content {
        margin-left: 0;
      }
      .mobile-menu-btn {
        display: block;
      }
      .content-area {
        padding: 24px 20px 60px;
      }
      .top-bar {
        padding: 10px 16px;
      }
      .hero h1 { font-size: 2rem; }
      .hero-stats { gap: 20px; flex-wrap: wrap; }
      .section-grid { grid-template-columns: 1fr; }
      .page-nav { flex-direction: column; }
    }

    @media (max-width: 600px) {
      .level-selector {
        flex-wrap: wrap;
      }
      .level-btn { padding: 5px 10px; font-size: 12px; }
      .page-header h1 { font-size: 1.6rem; }
    }
    '''


def get_shared_js():
    return '''
    // ===== LEVEL SELECTOR =====
    function initLevelSelector() {
      const stored = localStorage.getItem('fastapi-course-level');
      const buttons = document.querySelectorAll('.level-btn');
      const sections = document.querySelectorAll('.level-section');

      function showLevel(level) {
        localStorage.setItem('fastapi-course-level', level);
        buttons.forEach(b => b.classList.toggle('active', b.dataset.level === level));
        sections.forEach(s => {
          if (level === 'all') {
            s.classList.remove('hidden');
          } else {
            const sectionLevel = s.dataset.level;
            const levels = ['beginner', 'intermediate', 'advanced'];
            const selectedIdx = levels.indexOf(level);
            const sectionIdx = levels.indexOf(sectionLevel);
            s.classList.toggle('hidden', sectionIdx > selectedIdx);
          }
        });
      }

      buttons.forEach(btn => {
        btn.addEventListener('click', () => showLevel(btn.dataset.level));
      });

      showLevel(stored || 'all');
    }

    // ===== COPY CODE =====
    function copyCode(id) {
      const codeEl = document.getElementById(id);
      if (!codeEl) return;
      const text = codeEl.textContent;
      navigator.clipboard.writeText(text).then(() => {
        const btn = codeEl.closest('.code-block-wrapper').querySelector('.copy-btn');
        btn.classList.add('copied');
        btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> Copied!';
        setTimeout(() => {
          btn.classList.remove('copied');
          btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy';
        }, 2000);
      });
    }

    // ===== PROGRESS TRACKING =====
    function trackProgress() {
      const page = window.location.pathname.split('/').pop() || 'index.html';
      let visited = JSON.parse(localStorage.getItem('fastapi-course-visited') || '[]');
      if (!visited.includes(page)) {
        visited.push(page);
        localStorage.setItem('fastapi-course-visited', JSON.stringify(visited));
      }
      // Update nav items
      document.querySelectorAll('.nav-item').forEach(item => {
        const href = item.getAttribute('href');
        if (visited.includes(href)) {
          item.classList.add('nav-visited');
        }
      });
      // Update progress bar
      const total = document.querySelectorAll('.nav-item').length;
      const visitedCount = visited.length;
      const pct = Math.round((visitedCount / total) * 100);
      const bar = document.querySelector('.progress-bar');
      const label = document.querySelector('.progress-label');
      if (bar) bar.style.width = pct + '%';
      if (label) label.textContent = pct + '% complete (' + visitedCount + '/' + total + ' sections)';
    }

    // ===== MOBILE MENU =====
    function initMobileMenu() {
      const btn = document.querySelector('.mobile-menu-btn');
      const sidebar = document.querySelector('.sidebar');
      const overlay = document.querySelector('.sidebar-overlay');
      if (!btn) return;

      function toggle() {
        sidebar.classList.toggle('open');
        overlay.classList.toggle('open');
      }

      btn.addEventListener('click', toggle);
      overlay.addEventListener('click', toggle);
    }

    // ===== COLLAPSIBLES =====
    function initCollapsibles() {
      document.querySelectorAll('.collapsible-trigger').forEach(trigger => {
        trigger.addEventListener('click', () => {
          trigger.classList.toggle('open');
          const content = trigger.nextElementSibling;
          if (content) content.classList.toggle('open');
        });
      });
    }

    // ===== QUIZ =====
    function initQuiz(quizId, correctIdx) {
      const container = document.getElementById(quizId);
      if (!container) return;
      const options = container.querySelectorAll('.quiz-option');
      const feedback = container.querySelector('.quiz-feedback');
      let answered = false;

      options.forEach((opt, idx) => {
        opt.addEventListener('click', () => {
          if (answered) return;
          answered = true;
          opt.classList.add('selected');
          if (idx === correctIdx) {
            opt.classList.add('correct');
            feedback.className = 'quiz-feedback show correct';
            feedback.textContent = 'Correct! Well done.';
          } else {
            opt.classList.add('incorrect');
            options[correctIdx].classList.add('correct');
            feedback.className = 'quiz-feedback show incorrect';
            feedback.textContent = 'Not quite. The correct answer is highlighted above.';
          }
        });
      });
    }

    // ===== INIT =====
    document.addEventListener('DOMContentLoaded', () => {
      initLevelSelector();
      trackProgress();
      initMobileMenu();
      initCollapsibles();
    });
    '''


QUIZZES = {
    "index.html": {
        "id": "quiz-home",
        "question": "What two libraries form the foundation of FastAPI?",
        "options": [
            "Django and Celery",
            "Flask and Marshmallow",
            "Starlette and Pydantic",
            "Tornado and SQLAlchemy"
        ],
        "correct": 2,
        "explanation": ""
    },
    "concepts.html": {
        "id": "quiz-concepts",
        "question": "What happens when a client sends an invalid type for a path parameter in FastAPI?",
        "options": [
            "The server crashes with a 500 error",
            "The invalid value is silently converted to None",
            "FastAPI returns a 422 Unprocessable Entity with a clear error message",
            "The request is forwarded to the handler with the raw string"
        ],
        "correct": 2,
    },
    "architecture.html": {
        "id": "quiz-arch",
        "question": "What is ASGI?",
        "options": [
            "A Python testing framework",
            "An Asynchronous Server Gateway Interface for async web apps",
            "A database connection protocol",
            "A JSON serialization format"
        ],
        "correct": 1,
    },
    "getting-started.html": {
        "id": "quiz-start",
        "question": "Which command starts a FastAPI app in development mode with auto-reload?",
        "options": [
            "python main.py",
            "flask run",
            "fastapi dev main.py",
            "django-admin runserver"
        ],
        "correct": 2,
    },
    "implementation.html": {
        "id": "quiz-impl",
        "question": "What does model_dump(exclude_unset=True) do in a PATCH endpoint?",
        "options": [
            "Deletes the model from the database",
            "Returns only the fields the client explicitly sent, ignoring defaults",
            "Validates all fields are present",
            "Converts the model to a YAML string"
        ],
        "correct": 1,
    },
    "use-cases.html": {
        "id": "quiz-use",
        "question": "Which industry has FastAPI become the de facto standard framework for model serving?",
        "options": [
            "Game development",
            "Desktop applications",
            "Machine Learning / AI",
            "Embedded systems"
        ],
        "correct": 2,
    },
    "ecosystem.html": {
        "id": "quiz-eco",
        "question": "What is SQLModel?",
        "options": [
            "A NoSQL database",
            "A library combining SQLAlchemy and Pydantic by the same author as FastAPI",
            "A JavaScript ORM",
            "A database migration tool"
        ],
        "correct": 1,
    },
    "performance.html": {
        "id": "quiz-perf",
        "question": "What makes Pydantic V2 significantly faster than V1?",
        "options": [
            "It uses fewer Python features",
            "Its core validation engine is written in Rust (pydantic-core)",
            "It skips validation entirely",
            "It only works with async code"
        ],
        "correct": 1,
    },
    "advanced.html": {
        "id": "quiz-adv",
        "question": "What is the modern replacement for startup/shutdown event handlers in FastAPI?",
        "options": [
            "on_event decorators",
            "Signal handlers",
            "Lifespan context managers",
            "Middleware hooks"
        ],
        "correct": 2,
    },
    "tradeoffs.html": {
        "id": "quiz-trade",
        "question": "When should you choose Django over FastAPI?",
        "options": [
            "When building a pure REST API microservice",
            "When you need a full-stack web app with admin panel, ORM, and migrations built-in",
            "When maximum API performance is the top priority",
            "When serving ML models"
        ],
        "correct": 1,
    },
}

SECTION_DESCRIPTIONS = {
    "index.html": "Welcome to the FastAPI Interactive Course",
    "concepts.html": "Type hints, Pydantic models, dependency injection, and the core ideas that drive FastAPI.",
    "architecture.html": "How FastAPI builds on Starlette and Pydantic, the ASGI protocol, and request lifecycle.",
    "getting-started.html": "Installation, your first API, project structure, testing, and deployment.",
    "implementation.html": "CRUD operations, authentication, pagination, rate limiting, and production patterns.",
    "use-cases.html": "REST APIs, microservices, ML model serving, and real-world adoption stories.",
    "ecosystem.html": "Database integrations, task queues, caching, monitoring, and the broader library ecosystem.",
    "performance.html": "Benchmark numbers, optimization techniques, profiling, and understanding the speed stack.",
    "advanced.html": "WebSockets, SSE, background tasks, lifespan events, and expert-level patterns.",
    "tradeoffs.html": "FastAPI vs Django vs Flask vs Litestar, migration strategies, and architectural decisions.",
}


def build_quiz_html(page_file):
    quiz = QUIZZES.get(page_file)
    if not quiz:
        return ""
    opts = ""
    for opt_text in quiz["options"]:
        opts += f'<button class="quiz-option">{escape_html(opt_text)}</button>\n'
    return f'''
    <div class="quiz-container" id="{quiz["id"]}">
      <div class="quiz-title">&#128218; Quick Check</div>
      <div class="quiz-question">{escape_html(quiz["question"])}</div>
      {opts}
      <div class="quiz-feedback"></div>
    </div>
    <script>
      document.addEventListener('DOMContentLoaded', function() {{
        initQuiz('{quiz["id"]}', {quiz["correct"]});
      }});
    </script>
    '''


def build_sidebar(active_page):
    items = []
    for idx, (fname, _, title, short) in enumerate(PAGES):
        active = "active" if fname == active_page else ""
        icon = NAV_ICONS[idx]
        items.append(f'<a href="{fname}" class="nav-item {active}" title="{escape_html(title)}"><span class="nav-icon">{icon}</span>{escape_html(short)}</a>')
    return '\n'.join(items)


def build_page_nav(page_idx):
    prev_html = ""
    next_html = ""
    if page_idx > 0:
        pf, _, pt, ps = PAGES[page_idx - 1]
        prev_html = f'<a href="{pf}" class="page-nav-link prev"><span class="page-nav-label">&larr; Previous</span><span class="page-nav-title">{escape_html(pt)}</span></a>'
    else:
        prev_html = '<div class="page-nav-placeholder"></div>'
    if page_idx < len(PAGES) - 1:
        nf, _, nt, ns = PAGES[page_idx + 1]
        next_html = f'<a href="{nf}" class="page-nav-link next"><span class="page-nav-label">Next &rarr;</span><span class="page-nav-title">{escape_html(nt)}</span></a>'
    else:
        next_html = '<div class="page-nav-placeholder"></div>'
    return f'<nav class="page-nav">{prev_html}{next_html}</nav>'


def build_index_content():
    """Build the special index page content."""
    cards = []
    for idx, (fname, _, title, short) in enumerate(PAGES[1:], 1):
        desc = SECTION_DESCRIPTIONS.get(fname, "")
        cards.append(f'''<a href="{fname}" class="section-card">
          <div class="section-card-num">{idx:02d}</div>
          <div class="section-card-title">{escape_html(title)}</div>
          <div class="section-card-desc">{escape_html(desc)}</div>
        </a>''')
    return f'''
    <div class="hero">
      <h1>FastAPI</h1>
      <p class="tagline">A modern, high-performance Python web framework for building APIs. Master it from beginner to advanced with this interactive course.</p>
      <div class="hero-stats">
        <div class="hero-stat"><div class="hero-stat-value">~97k</div><div class="hero-stat-label">GitHub Stars</div></div>
        <div class="hero-stat"><div class="hero-stat-value">4M+</div><div class="hero-stat-label">Weekly Downloads</div></div>
        <div class="hero-stat"><div class="hero-stat-value">MIT</div><div class="hero-stat-label">License</div></div>
        <div class="hero-stat"><div class="hero-stat-value">10</div><div class="hero-stat-label">Course Sections</div></div>
      </div>
    </div>

    <h2 class="section-header" style="margin-top: 0;">Course Sections</h2>
    <p>Click any section to begin learning. Your progress is tracked automatically.</p>
    <div class="section-grid">
      {''.join(cards)}
    </div>
    '''


def build_full_page(page_idx, body_content):
    fname, src, title, short = PAGES[page_idx]
    is_index = (page_idx == 0)

    sidebar = build_sidebar(fname)
    page_nav = build_page_nav(page_idx)
    quiz_html = build_quiz_html(fname)
    css = get_shared_css()
    js = get_shared_js()
    desc = SECTION_DESCRIPTIONS.get(fname, title)

    page_header = ""
    if not is_index:
        page_header = f'''<div class="page-header">
        <h1>{escape_html(title)}</h1>
        <p class="subtitle">{escape_html(desc)}</p>
      </div>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape_html(title)} | FastAPI Interactive Course</title>
  <meta name="description" content="{escape_html(desc)}">
  <style>{css}</style>
</head>
<body>
  <div class="sidebar-overlay"></div>

  <div class="page-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <a href="index.html" class="sidebar-logo">
          <div class="sidebar-logo-icon">F</div>
          <div>
            <div class="sidebar-logo-text">FastAPI</div>
            <div class="sidebar-logo-sub">Interactive Course</div>
          </div>
        </a>
      </div>
      <nav class="sidebar-nav">
        {sidebar}
      </nav>
      <div class="sidebar-footer">
        <div class="progress-label">0% complete</div>
        <div class="progress-bar-container">
          <div class="progress-bar" style="width: 0%"></div>
        </div>
      </div>
    </aside>

    <main class="main-content">
      <div class="top-bar">
        <button class="mobile-menu-btn">&#9776;</button>
        <div class="page-title-bar">{escape_html(short if not is_index else "Home")}</div>
        <div class="level-selector">
          <button class="level-btn active" data-level="all">All</button>
          <button class="level-btn" data-level="beginner">Beginner</button>
          <button class="level-btn" data-level="intermediate">Intermediate</button>
          <button class="level-btn" data-level="advanced">Advanced</button>
        </div>
      </div>

      <div class="content-area">
        {page_header}
        {body_content}
        {quiz_html}
        {page_nav}
      </div>
    </main>
  </div>

  <script>{js}</script>
</body>
</html>'''


def main():
    # Generate each page
    for idx, (fname, src_md, title, short) in enumerate(PAGES):
        src_path = BASE_DIR / src_md
        md_content = src_path.read_text(encoding='utf-8')

        if fname == "index.html":
            # Index gets special treatment: markdown content + section grid
            md_html = parse_markdown_to_html(md_content)
            body = build_index_content() + '\n' + md_html
        else:
            body = parse_markdown_to_html(md_content)

        full_html = build_full_page(idx, body)
        out_path = BASE_DIR / fname
        out_path.write_text(full_html, encoding='utf-8')
        print(f"Generated: {out_path}")

    print("\nAll pages generated successfully.")


if __name__ == "__main__":
    main()
