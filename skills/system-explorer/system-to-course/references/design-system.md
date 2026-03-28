# Design System Reference

Complete CSS design tokens for multi-page system courses. Copy the `:root` blocks into every page's inline `<style>` and adapt the accent color to the system's domain.

## Table of Contents
1. [Color Palette](#color-palette)
2. [Typography](#typography)
3. [Spacing & Layout](#spacing--layout)
4. [Shadows & Depth](#shadows--depth)
5. [Navigation CSS](#navigation-css)
6. [Level Selector CSS](#level-selector-css)
7. [Code Block CSS](#code-block-css)
8. [Responsive Breakpoints](#responsive-breakpoints)
9. [Animations & Transitions](#animations--transitions)
10. [Scrollbar & Background](#scrollbar--background)

---

## Color Palette

```css
:root {
  /* --- BACKGROUNDS --- */
  --color-bg:             #FAF7F2;       /* warm off-white */
  --color-bg-warm:        #F5F0E8;       /* alternating sections */
  --color-bg-code:        #1E1E2E;       /* code/notation blocks */
  --color-text:           #2C2A28;       /* primary text */
  --color-text-secondary: #6B6560;
  --color-text-muted:     #9E9790;
  --color-border:         #E5DFD6;
  --color-border-light:   #EEEBE5;
  --color-surface:        #FFFFFF;
  --color-surface-warm:   #FDF9F3;

  /* --- ACCENT (adapt per system domain — pick ONE) --- */
  --color-accent:         #2A7B9B;       /* default: deep teal */
  --color-accent-hover:   #236A86;
  --color-accent-light:   #E4F2F7;
  --color-accent-muted:   #5A9DB5;

  /* --- SEMANTIC --- */
  --color-success:        #2D8B55;
  --color-success-light:  #E8F5EE;
  --color-error:          #C93B3B;
  --color-error-light:    #FDE8E8;
  --color-info:           #2A7B9B;
  --color-info-light:     #E4F2F7;
  --color-warning:        #D4A843;
  --color-warning-light:  #FDF6E4;

  /* --- LEVEL BADGE COLORS --- */
  --color-level-beginner:     #2D8B55;
  --color-level-intermediate: #D4A843;
  --color-level-advanced:     #C93B3B;
}
```

**Accent color by domain:**

| Domain | Color | Hex | CSS override |
|--------|-------|-----|-------------|
| Infrastructure / DevOps | deep teal | #2A7B9B | (default) |
| Databases | amber | #D4A843 | `--color-accent: #D4A843; --color-accent-hover: #BF9738; --color-accent-light: #FDF6E4; --color-accent-muted: #E0C06A;` |
| Message queues / Streaming | coral | #E06B56 | `--color-accent: #E06B56; --color-accent-hover: #C9594A; --color-accent-light: #FDE8E4; --color-accent-muted: #E8917F;` |
| Frontend / UI | plum | #7B6DAA | `--color-accent: #7B6DAA; --color-accent-hover: #695D94; --color-accent-light: #EEEAF5; --color-accent-muted: #9B90BE;` |
| ML / AI | forest | #2D8B55 | `--color-accent: #2D8B55; --color-accent-hover: #257548; --color-accent-light: #E8F5EE; --color-accent-muted: #5AAF7A;` |

**Rules:**
- Even-numbered sections use `--color-bg`, odd-numbered use `--color-bg-warm`
- Code blocks always use `--color-bg-code` with light text
- Level badges use their respective `--color-level-*` tokens, never the accent color

---

## Typography

```css
:root {
  /* --- FONTS --- */
  --font-display:  'Bricolage Grotesque', Georgia, serif;
  --font-body:     'DM Sans', -apple-system, sans-serif;
  --font-mono:     'JetBrains Mono', 'Fira Code', 'Consolas', monospace;

  /* --- TYPE SCALE (1.25 ratio) --- */
  --text-xs:   0.75rem;    /* 12px — labels, badges */
  --text-sm:   0.875rem;   /* 14px — secondary text, code */
  --text-base: 1rem;       /* 16px — body text */
  --text-lg:   1.125rem;   /* 18px — lead paragraphs */
  --text-xl:   1.25rem;    /* 20px — subsection headings (h3) */
  --text-2xl:  1.5rem;     /* 24px — section headings (h2) */
  --text-3xl:  1.875rem;   /* 30px — page subtitle */
  --text-4xl:  2.25rem;    /* 36px — page title (h1) */
  --text-5xl:  3rem;       /* 48px — hero text */
  --text-6xl:  3.75rem;    /* 60px — page numbers */

  /* --- LINE HEIGHTS --- */
  --leading-tight:  1.15;  /* headings */
  --leading-snug:   1.3;   /* subheadings */
  --leading-normal: 1.6;   /* body text */
  --leading-loose:  1.8;   /* relaxed reading */
}
```

**Google Fonts link (put in `<head>` of every page):**
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,600;12..96,700;12..96,800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400;1,9..40,500&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
```

**Multi-page heading rules:**
- `h1` = page title. One per page. `--text-4xl`, font-display, weight 700.
- `h2` = section heading within a page. `--text-2xl`, font-display, weight 600.
- `h3` = subsection heading. `--text-xl`, font-display, weight 600.
- Body text: `--text-base` or `--text-lg`, font-body, `--leading-normal`.
- Code/notation: `--text-sm` or `--text-base`, font-mono.
- Labels/badges: `--text-xs`, font-mono, uppercase, letter-spacing 0.05em.
- Page numbers (decorative): `--text-6xl`, font-display, weight 800, `--color-accent` at 15% opacity.

---

## Spacing & Layout

```css
:root {
  --space-1:  0.25rem;   /* 4px */
  --space-2:  0.5rem;    /* 8px */
  --space-3:  0.75rem;   /* 12px */
  --space-4:  1rem;      /* 16px */
  --space-5:  1.25rem;   /* 20px */
  --space-6:  1.5rem;    /* 24px */
  --space-8:  2rem;      /* 32px */
  --space-10: 2.5rem;    /* 40px */
  --space-12: 3rem;      /* 48px */
  --space-16: 4rem;      /* 64px */
  --space-20: 5rem;      /* 80px */
  --space-24: 6rem;      /* 96px */

  /* --- MULTI-PAGE LAYOUT --- */
  --content-width:      800px;   /* standard reading width */
  --content-width-wide: 1000px;  /* diagrams, side-by-side layouts */
  --nav-height:         60px;    /* taller than paper-to-course for level selector */
  --sidebar-width:      240px;   /* optional sidebar nav on desktop */

  --radius-sm:   8px;
  --radius-md:   12px;
  --radius-lg:   16px;
  --radius-full: 9999px;
}
```

**Page layout:**
```css
.page-body {
  padding: var(--space-16) var(--space-6);
  padding-top: calc(var(--nav-height) + var(--space-12));
  min-height: 100dvh;
}
.page-content {
  max-width: var(--content-width);
  margin: 0 auto;
}
.page-content-wide {
  max-width: var(--content-width-wide);
  margin: 0 auto;
}
```

**Sidebar layout (optional, desktop only):**
```css
.layout-with-sidebar {
  display: grid;
  grid-template-columns: var(--sidebar-width) 1fr;
  gap: var(--space-8);
  max-width: calc(var(--content-width-wide) + var(--sidebar-width) + var(--space-8));
  margin: 0 auto;
  padding-top: calc(var(--nav-height) + var(--space-8));
}
.sidebar-nav {
  position: sticky;
  top: calc(var(--nav-height) + var(--space-8));
  height: fit-content;
  max-height: calc(100dvh - var(--nav-height) - var(--space-16));
  overflow-y: auto;
  padding: var(--space-4);
}
```

---

## Shadows & Depth

```css
:root {
  --shadow-sm:  0 1px 2px rgba(44, 42, 40, 0.05);
  --shadow-md:  0 4px 12px rgba(44, 42, 40, 0.08);
  --shadow-lg:  0 8px 24px rgba(44, 42, 40, 0.1);
  --shadow-xl:  0 16px 48px rgba(44, 42, 40, 0.12);
}
```

Use warm-tinted RGBA (44, 42, 40) -- never pure black shadows.

---

## Navigation CSS

**HTML structure:**
```html
<nav class="site-nav">
  <div class="nav-progress-bar" role="progressbar" aria-valuenow="0"></div>
  <div class="nav-inner">
    <a href="index.html" class="nav-brand">System Name</a>
    <div class="nav-pages" id="navPages">
      <a href="index.html" class="nav-page-link active">Home</a>
      <a href="concepts.html" class="nav-page-link">Concepts</a>
      <a href="architecture.html" class="nav-page-link">Architecture</a>
      <!-- one per page -->
    </div>
    <div class="nav-levels" id="navLevels">
      <button class="level-btn level-btn--beginner active" data-level="beginner">Beginner</button>
      <button class="level-btn level-btn--intermediate active" data-level="intermediate">Intermediate</button>
      <button class="level-btn level-btn--advanced active" data-level="advanced">Advanced</button>
    </div>
    <button class="nav-hamburger" id="navHamburger" aria-label="Toggle navigation">
      <span></span><span></span><span></span>
    </button>
  </div>
</nav>
```

**Navigation bar CSS:**
```css
.site-nav {
  position: sticky;
  top: 0;
  z-index: 1000;
  height: var(--nav-height);
  background: rgba(250, 247, 242, 0.92);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--color-border-light);
}
.nav-inner {
  max-width: var(--content-width-wide);
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: 0 var(--space-6);
}
.nav-brand {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: var(--text-lg);
  color: var(--color-text);
  text-decoration: none;
  white-space: nowrap;
  flex-shrink: 0;
}
.nav-brand:hover {
  color: var(--color-accent);
}
```

**Progress bar:**
```css
.nav-progress-bar {
  position: absolute;
  top: 0;
  left: 0;
  height: 3px;
  width: 0%;
  background: var(--color-accent);
  transition: width 100ms linear;
  z-index: 1;
}
```

**Page links:**
```css
.nav-pages {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  flex: 1;
  overflow-x: auto;
  scrollbar-width: none;
}
.nav-pages::-webkit-scrollbar { display: none; }
.nav-page-link {
  font-family: var(--font-body);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-secondary);
  text-decoration: none;
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  white-space: nowrap;
  transition: color var(--duration-fast) var(--ease-out),
              background var(--duration-fast) var(--ease-out);
}
.nav-page-link:hover {
  color: var(--color-text);
  background: var(--color-border-light);
}
.nav-page-link.active {
  color: var(--color-accent);
  background: var(--color-accent-light);
  font-weight: 600;
}
```

**Progress indicator dots (index page):**
```css
.progress-dots {
  display: flex;
  gap: var(--space-2);
  justify-content: center;
  padding: var(--space-4) 0;
}
.progress-dot {
  width: 10px;
  height: 10px;
  border-radius: var(--radius-full);
  border: 2px solid var(--color-text-muted);
  background: transparent;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}
.progress-dot.visited {
  background: var(--color-accent);
  border-color: var(--color-accent);
}
.progress-dot.current {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px var(--color-accent-light);
}
```

**Hamburger button (mobile only):**
```css
.nav-hamburger {
  display: none;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
  width: 36px;
  height: 36px;
  padding: var(--space-2);
  background: none;
  border: none;
  cursor: pointer;
  flex-shrink: 0;
}
.nav-hamburger span {
  display: block;
  width: 20px;
  height: 2px;
  background: var(--color-text);
  border-radius: 1px;
  transition: transform var(--duration-fast) var(--ease-out),
              opacity var(--duration-fast) var(--ease-out);
}
.nav-hamburger.open span:nth-child(1) {
  transform: translateY(6px) rotate(45deg);
}
.nav-hamburger.open span:nth-child(2) {
  opacity: 0;
}
.nav-hamburger.open span:nth-child(3) {
  transform: translateY(-6px) rotate(-45deg);
}
```

**Previous / Next page footer:**
```css
.page-nav-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-4);
  margin-top: var(--space-16);
  padding-top: var(--space-8);
  border-top: 1px solid var(--color-border);
}
.page-nav-link {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  text-decoration: none;
  padding: var(--space-4);
  border-radius: var(--radius-md);
  transition: background var(--duration-fast) var(--ease-out);
  max-width: 45%;
}
.page-nav-link:hover {
  background: var(--color-surface-warm);
}
.page-nav-link--next {
  text-align: right;
  margin-left: auto;
}
.page-nav-label {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.page-nav-title {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-accent);
}
```

**Progress bar JS:**
```javascript
function updateProgressBar() {
  const scrollTop = window.scrollY;
  const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
  const progress = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0;
  document.querySelector('.nav-progress-bar').style.width = progress + '%';
}
window.addEventListener('scroll', () => {
  requestAnimationFrame(updateProgressBar);
}, { passive: true });
```

**Hamburger toggle JS:**
```javascript
const hamburger = document.getElementById('navHamburger');
const navPages = document.getElementById('navPages');
const navLevels = document.getElementById('navLevels');
hamburger.addEventListener('click', () => {
  hamburger.classList.toggle('open');
  navPages.classList.toggle('mobile-open');
  navLevels.classList.toggle('mobile-open');
});
```

---

## Level Selector CSS

**Toggle buttons:**
```css
.nav-levels {
  display: flex;
  gap: var(--space-1);
  flex-shrink: 0;
}
.level-btn {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  border: 2px solid;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
  background: transparent;
}

/* Beginner */
.level-btn--beginner {
  border-color: var(--color-level-beginner);
  color: var(--color-level-beginner);
}
.level-btn--beginner.active {
  background: var(--color-level-beginner);
  color: #FFFFFF;
}

/* Intermediate */
.level-btn--intermediate {
  border-color: var(--color-level-intermediate);
  color: var(--color-level-intermediate);
}
.level-btn--intermediate.active {
  background: var(--color-level-intermediate);
  color: #FFFFFF;
}

/* Advanced */
.level-btn--advanced {
  border-color: var(--color-level-advanced);
  color: var(--color-level-advanced);
}
.level-btn--advanced.active {
  background: var(--color-level-advanced);
  color: #FFFFFF;
}

/* Hover states (inactive buttons only) */
.level-btn--beginner:not(.active):hover {
  background: rgba(45, 139, 85, 0.1);
}
.level-btn--intermediate:not(.active):hover {
  background: rgba(212, 168, 67, 0.1);
}
.level-btn--advanced:not(.active):hover {
  background: rgba(201, 59, 59, 0.1);
}
```

**Level badge (inline in content):**
```css
.level-badge {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  display: inline-block;
}
.level-badge--beginner {
  background: var(--color-success-light);
  color: var(--color-level-beginner);
}
.level-badge--intermediate {
  background: var(--color-warning-light);
  color: var(--color-level-intermediate);
}
.level-badge--advanced {
  background: var(--color-error-light);
  color: var(--color-level-advanced);
}
```

**Content visibility by level:**
```css
/* Default: all levels visible */
[data-level="beginner"]     { display: block; }
[data-level="intermediate"] { display: block; }
[data-level="advanced"]     { display: block; }

/* Body classes toggle visibility */
body.hide-beginner [data-level="beginner"]         { display: none; }
body.hide-intermediate [data-level="intermediate"] { display: none; }
body.hide-advanced [data-level="advanced"]         { display: none; }
```

**Level selector JS:**
```javascript
(function() {
  const STORAGE_KEY = 'system-explorer-levels';

  function getState() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : { beginner: true, intermediate: true, advanced: true };
    } catch (e) {
      return { beginner: true, intermediate: true, advanced: true };
    }
  }

  function applyState(state) {
    ['beginner', 'intermediate', 'advanced'].forEach(level => {
      document.body.classList.toggle('hide-' + level, !state[level]);
      const btn = document.querySelector('.level-btn[data-level="' + level + '"]');
      if (btn) btn.classList.toggle('active', state[level]);
    });
  }

  function saveState(state) {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch (e) {}
  }

  /* Apply immediately on load to prevent flash of hidden content */
  const initialState = getState();
  applyState(initialState);

  document.addEventListener('DOMContentLoaded', () => {
    applyState(getState());
    document.querySelectorAll('.level-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const level = btn.dataset.level;
        const state = getState();
        state[level] = !state[level];
        /* Prevent hiding ALL levels */
        if (!state.beginner && !state.intermediate && !state.advanced) {
          state[level] = true;
          return;
        }
        saveState(state);
        applyState(state);
      });
    });
  });
})();
```

---

## Code Block CSS

**Container:**
```css
.code-block {
  position: relative;
  background: var(--color-bg-code);
  border-radius: var(--radius-md);
  margin: var(--space-6) 0;
  overflow: hidden;
}
.code-block-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-2) var(--space-4);
  background: rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.code-lang-badge {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  font-weight: 600;
  color: #CDD6F4;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.code-copy-btn {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: #6C7086;
  background: none;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-sm);
  padding: var(--space-1) var(--space-2);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}
.code-copy-btn:hover {
  color: #CDD6F4;
  border-color: rgba(255, 255, 255, 0.25);
  background: rgba(255, 255, 255, 0.05);
}
.code-copy-btn.copied {
  color: #A6E3A1;
  border-color: rgba(166, 227, 161, 0.3);
}
.code-block pre {
  margin: 0;
  padding: var(--space-4);
  overflow-x: auto;
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  line-height: 1.6;
  color: #CDD6F4;
  tab-size: 2;
}
```

**Line numbers (optional):**
```css
.code-block pre.line-numbers {
  counter-reset: line;
  padding-left: calc(var(--space-4) + 3em);
}
.code-block pre.line-numbers .line::before {
  counter-increment: line;
  content: counter(line);
  display: inline-block;
  width: 2.5em;
  margin-left: -3em;
  margin-right: var(--space-2);
  text-align: right;
  color: #45475A;
  user-select: none;
}
```

**Syntax highlighting (Catppuccin-inspired on `--color-bg-code`):**
```css
.code-keyword  { color: #CBA6F7; }  /* purple -- keywords, reserved words */
.code-variable { color: #89B4FA; }  /* blue -- variables, identifiers */
.code-number   { color: #FAB387; }  /* peach -- numbers, constants */
.code-function { color: #A6E3A1; }  /* green -- function/method names */
.code-comment  { color: #6C7086; font-style: italic; }  /* muted -- comments */
.code-string   { color: #F9E2AF; }  /* yellow -- strings */
.code-operator { color: #94E2D5; }  /* teal -- operators */
.code-accent   { color: #F38BA8; }  /* pink -- emphasis, annotations */
.code-type     { color: #89DCEB; }  /* sky -- types, interfaces */
.code-property { color: #F5C2E7; }  /* flamingo -- properties, attributes */
.code-builtin  { color: #FAB387; }  /* peach -- built-in functions */
.code-tag      { color: #CBA6F7; }  /* purple -- HTML/XML tags */
.code-attr     { color: #89B4FA; }  /* blue -- HTML/XML attributes */
```

**Copy button JS:**
```javascript
document.querySelectorAll('.code-copy-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const code = btn.closest('.code-block').querySelector('pre').textContent;
    navigator.clipboard.writeText(code).then(() => {
      btn.textContent = 'Copied!';
      btn.classList.add('copied');
      setTimeout(() => {
        btn.textContent = 'Copy';
        btn.classList.remove('copied');
      }, 2000);
    });
  });
});
```

---

## Responsive Breakpoints

```css
/* Desktop: full nav + optional sidebar */
/* (default styles above) */

/* Tablet */
@media (max-width: 768px) {
  :root {
    --text-4xl: 1.875rem;
    --text-5xl: 2.25rem;
    --text-6xl: 3rem;
    --nav-height: 56px;
  }

  /* Collapse sidebar */
  .layout-with-sidebar {
    grid-template-columns: 1fr;
  }
  .sidebar-nav {
    display: none;
  }

  /* Nav pages stay horizontal but can scroll */
  .nav-pages {
    gap: var(--space-1);
  }
  .nav-page-link {
    font-size: var(--text-xs);
    padding: var(--space-1) var(--space-2);
  }

  /* Level buttons shrink */
  .level-btn {
    padding: var(--space-1) var(--space-2);
    font-size: 0.65rem;
  }

  /* Content adjustments */
  .page-content-wide {
    max-width: 100%;
  }
  .code-block pre {
    font-size: var(--text-xs);
  }
}

/* Mobile */
@media (max-width: 480px) {
  :root {
    --text-4xl: 1.5rem;
    --text-5xl: 1.875rem;
    --text-6xl: 2.25rem;
    --nav-height: 52px;
  }

  /* Show hamburger, hide nav pages and levels by default */
  .nav-hamburger {
    display: flex;
  }
  .nav-pages,
  .nav-levels {
    display: none;
    position: absolute;
    top: var(--nav-height);
    left: 0;
    right: 0;
    background: var(--color-surface);
    border-bottom: 1px solid var(--color-border);
    box-shadow: var(--shadow-md);
    padding: var(--space-4);
  }
  .nav-pages.mobile-open,
  .nav-levels.mobile-open {
    display: flex;
  }
  .nav-pages.mobile-open {
    flex-direction: column;
    gap: var(--space-1);
  }
  .nav-levels.mobile-open {
    top: auto;
    border-top: 1px solid var(--color-border-light);
    justify-content: center;
    gap: var(--space-2);
  }

  /* Stacked layouts */
  .page-body {
    padding: var(--space-8) var(--space-4);
    padding-top: calc(var(--nav-height) + var(--space-8));
  }
  .page-nav-footer {
    flex-direction: column;
    gap: var(--space-4);
  }
  .page-nav-link {
    max-width: 100%;
    text-align: center;
  }
  .page-nav-link--next {
    text-align: center;
    margin-left: 0;
  }
}
```

---

## Animations & Transitions

```css
:root {
  --ease-out:    cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
  --duration-fast:   150ms;
  --duration-normal: 300ms;
  --duration-slow:   500ms;
  --stagger-delay:   120ms;
}
```

**Scroll-triggered reveal:**
```css
.animate-in {
  opacity: 0;
  transform: translateY(20px);
  transition: opacity var(--duration-slow) var(--ease-out),
              transform var(--duration-slow) var(--ease-out);
}
.animate-in.visible {
  opacity: 1;
  transform: translateY(0);
}

/* Stagger children */
.stagger-children > .animate-in {
  transition-delay: calc(var(--stagger-index, 0) * var(--stagger-delay));
}
```

**JS setup for stagger:**
```javascript
document.querySelectorAll('.stagger-children').forEach(parent => {
  Array.from(parent.children).forEach((child, i) => {
    child.style.setProperty('--stagger-index', i);
  });
});
```

**Intersection Observer:**
```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, { rootMargin: '0px 0px -10% 0px', threshold: 0.1 });

document.querySelectorAll('.animate-in').forEach(el => observer.observe(el));
```

---

## Scrollbar & Background

```css
/* Custom scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: var(--radius-full);
}

/* Subtle atmospheric background */
body {
  background: var(--color-bg);
  background-image: radial-gradient(
    ellipse at 20% 50%,
    rgba(42, 123, 155, 0.03) 0%,
    transparent 50%
  );
  font-family: var(--font-body);
  color: var(--color-text);
  line-height: var(--leading-normal);
  margin: 0;
  -webkit-font-smoothing: antialiased;
}

/* No scroll-snap for multi-page site (unlike paper-to-course) */
html {
  scroll-behavior: smooth;
}
```
