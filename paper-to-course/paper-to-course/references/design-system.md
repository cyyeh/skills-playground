# Design System Reference

Complete CSS design tokens for the course. Copy this entire `:root` block into the course HTML and adapt the accent color to suit the paper's field and personality.

## Table of Contents
1. [Color Palette](#color-palette)
2. [Typography](#typography)
3. [Spacing & Layout](#spacing--layout)
4. [Shadows & Depth](#shadows--depth)
5. [Animations & Transitions](#animations--transitions)
6. [Navigation & Progress](#navigation--progress)
7. [Module Structure](#module-structure)
8. [Responsive Breakpoints](#responsive-breakpoints)
9. [Scrollbar & Background](#scrollbar--background)

---

## Color Palette

```css
:root {
  /* --- BACKGROUNDS --- */
  --color-bg:             #FAF7F2;       /* warm off-white, like quality paper */
  --color-bg-warm:        #F5F0E8;       /* slightly warmer for alternating modules */
  --color-bg-code:        #1E1E2E;       /* deep indigo-charcoal for equation/notation blocks */
  --color-text:           #2C2A28;       /* dark charcoal, easy on eyes */
  --color-text-secondary: #6B6560;       /* warm gray for secondary text */
  --color-text-muted:     #9E9790;       /* muted for timestamps, labels */
  --color-border:         #E5DFD6;       /* subtle warm border */
  --color-border-light:   #EEEBE5;       /* even lighter border */
  --color-surface:        #FFFFFF;       /* card surfaces */
  --color-surface-warm:   #FDF9F3;       /* warm card surface */

  /* --- ACCENT (adapt per paper's field — pick ONE bold color) ---
     Default: deep teal (scholarly, authoritative).
     Alternatives: vermillion (#D94F30) for bold/disruptive papers,
     amber (#D4A843) for historical/foundational, forest (#2D8B55) for
     biology/environmental, coral (#E06B56) for social science.
     Avoid purple gradients and neon colors. */
  --color-accent:         #2A7B9B;
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

  /* --- CONCEPT COLORS (assign to key ideas/actors in the paper) ---
     Each major "character" (concept, variable, component) gets a
     distinct color for chat bubbles, diagrams, and highlights */
  --color-concept-1:      #2A7B9B;       /* teal */
  --color-concept-2:      #D94F30;       /* vermillion */
  --color-concept-3:      #7B6DAA;       /* muted plum */
  --color-concept-4:      #D4A843;       /* golden */
  --color-concept-5:      #2D8B55;       /* forest */
  --color-concept-6:      #E06B56;       /* coral */
}
```

**Rules:**
- Even-numbered modules use `--color-bg`, odd-numbered use `--color-bg-warm` (alternating backgrounds create visual rhythm)
- Concept colors should be visually distinct from each other and from the accent
- Equation/notation blocks always use `--color-bg-code` with light text
- Choose the accent color based on the paper's field and tone

---

## Typography

```css
:root {
  /* --- FONTS ---
     Display: bold, geometric, personality-driven. NOT Inter/Roboto/Arial.
     Body: readable with character. NOT system fonts.
     Mono: clean monospace for equations and notation. */
  --font-display:  'Bricolage Grotesque', Georgia, serif;
  --font-body:     'DM Sans', -apple-system, sans-serif;
  --font-mono:     'JetBrains Mono', 'Fira Code', 'Consolas', monospace;

  /* --- TYPE SCALE (1.25 ratio) --- */
  --text-xs:   0.75rem;    /* 12px — labels, badges */
  --text-sm:   0.875rem;   /* 14px — secondary text, notation */
  --text-base: 1rem;       /* 16px — body text */
  --text-lg:   1.125rem;   /* 18px — lead paragraphs */
  --text-xl:   1.25rem;    /* 20px — screen headings */
  --text-2xl:  1.5rem;     /* 24px — sub-module titles */
  --text-3xl:  1.875rem;   /* 30px — module subtitles */
  --text-4xl:  2.25rem;    /* 36px — module titles */
  --text-5xl:  3rem;       /* 48px — hero text */
  --text-6xl:  3.75rem;    /* 60px — module numbers */

  /* --- LINE HEIGHTS --- */
  --leading-tight:  1.15;  /* headings */
  --leading-snug:   1.3;   /* subheadings */
  --leading-normal: 1.6;   /* body text */
  --leading-loose:  1.8;   /* relaxed reading */
}
```

**Google Fonts link (put in `<head>`):**
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,600;12..96,700;12..96,800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400;1,9..40,500&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
```

**Rules:**
- Module numbers: `--text-6xl`, font-display, weight 800, `--color-accent` with 15% opacity
- Module titles: `--text-4xl`, font-display, weight 700
- Screen headings: `--text-xl` or `--text-2xl`, font-display, weight 600
- Body text: `--text-base` or `--text-lg`, font-body, `--leading-normal`
- Equations/notation: `--text-sm` or `--text-base`, font-mono
- Labels/badges: `--text-xs`, font-mono, uppercase, letter-spacing 0.05em

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

  --content-width:     800px;   /* standard reading width */
  --content-width-wide: 1000px; /* for side-by-side layouts */
  --nav-height:        50px;
  --radius-sm:  8px;
  --radius-md:  12px;
  --radius-lg:  16px;
  --radius-full: 9999px;
}
```

**Module layout:**
```css
.module {
  min-height: 100dvh;       /* fallback: 100vh */
  scroll-snap-align: start;
  padding: var(--space-16) var(--space-6);
  padding-top: calc(var(--nav-height) + var(--space-12));
}
.module-content {
  max-width: var(--content-width);
  margin: 0 auto;
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

Use warm-tinted RGBA (44, 42, 40) — never pure black shadows.

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

**Scroll-triggered reveal pattern:**
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

**Intersection Observer (trigger reveals):**
```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target); // animate only once
    }
  });
}, { rootMargin: '0px 0px -10% 0px', threshold: 0.1 });

document.querySelectorAll('.animate-in').forEach(el => observer.observe(el));
```

---

## Navigation & Progress

**HTML structure:**
```html
<nav class="nav">
  <div class="progress-bar" role="progressbar" aria-valuenow="0"></div>
  <div class="nav-inner">
    <span class="nav-title">Course Title</span>
    <div class="nav-dots">
      <button class="nav-dot" data-target="module-1" data-tooltip="Module 1 Name"
              role="tab" aria-label="Module 1"></button>
      <!-- one per module -->
    </div>
  </div>
</nav>
```

**Progress bar:**
```javascript
function updateProgressBar() {
  const scrollTop = window.scrollY;
  const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
  const progress = (scrollTop / scrollHeight) * 100;
  progressBar.style.width = progress + '%';
}
window.addEventListener('scroll', () => {
  requestAnimationFrame(updateProgressBar);
}, { passive: true });
```

**Nav dot states:**
- Default: `border: 2px solid var(--color-text-muted)`, empty center
- Current: `border-color: var(--color-accent)`, filled center, subtle glow shadow
- Visited: `background: var(--color-accent)`, filled solid

**Keyboard navigation:**
```javascript
document.addEventListener('keydown', (e) => {
  if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) return;
  if (e.key === 'ArrowDown' || e.key === 'ArrowRight') { nextModule(); e.preventDefault(); }
  if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') { prevModule(); e.preventDefault(); }
});
```

---

## Module Structure

**HTML template for each module:**
```html
<section class="module" id="module-N" style="background: var(--color-bg or --color-bg-warm)">
  <div class="module-content">
    <header class="module-header animate-in">
      <span class="module-number">0N</span>
      <h1 class="module-title">Module Title</h1>
      <p class="module-subtitle">One-line description of what this module teaches</p>
    </header>

    <div class="module-body">
      <section class="screen animate-in">
        <h2 class="screen-heading">Screen Title</h2>
        <p>Content...</p>
        <!-- Interactive elements, translations, etc. -->
      </section>

      <section class="screen animate-in">
        <!-- Next screen -->
      </section>
    </div>
  </div>
</section>
```

---

## Responsive Breakpoints

```css
/* Tablet */
@media (max-width: 768px) {
  :root {
    --text-4xl: 1.875rem;
    --text-5xl: 2.25rem;
    --text-6xl: 3rem;
  }
  .translation-block { grid-template-columns: 1fr; } /* stack notation/english */
  .concept-cards { grid-template-columns: 1fr 1fr; }
}

/* Mobile */
@media (max-width: 480px) {
  :root {
    --text-4xl: 1.5rem;
    --text-5xl: 1.875rem;
    --text-6xl: 2.25rem;
  }
  .module { padding: var(--space-8) var(--space-4); }
  .concept-cards { grid-template-columns: 1fr; }
  .flow-steps { flex-direction: column; }
  .flow-arrow { transform: rotate(90deg); }
}
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
}

/* Page scroll setup */
html {
  scroll-snap-type: y proximity;
  scroll-behavior: smooth;
}
```

---

## Equation & Notation Block Globals

All equation/notation blocks in the course must wrap text and never show a horizontal scrollbar. This is a teaching tool, not a LaTeX renderer.

```css
.equation-block, .notation-block {
  white-space: pre-wrap;
  word-break: break-word;
  overflow-x: hidden;
}
/* Hide scrollbars on notation containers */
.translation-notation::-webkit-scrollbar,
.equation-block::-webkit-scrollbar {
  display: none;
}
```

Equations must use the paper's **original notation exactly as-is** — never simplified or reformatted. Use Unicode math symbols and HTML/CSS for rendering. Choose naturally compact, illustrative equations rather than trying to render every formula in the paper.

---

## Self-Contained Math Rendering

Since the course must not depend on external CDNs (MathJax, KaTeX), use these patterns for equations:

**Inline math:** Use `<span class="math-inline">` with Unicode symbols.
```html
<span class="math-inline">y = f(x) + ε</span>
```

**Block equations:** Use CSS grid/flexbox for fractions, summations, etc.
```css
.math-block {
  font-family: var(--font-mono);
  font-size: var(--text-lg);
  text-align: center;
  padding: var(--space-6) var(--space-4);
  background: var(--color-bg-code);
  color: #CDD6F4;
  border-radius: var(--radius-md);
  margin: var(--space-6) 0;
}
.math-fraction {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  vertical-align: middle;
}
.math-fraction .numerator {
  border-bottom: 1.5px solid #CDD6F4;
  padding: 0 var(--space-2) var(--space-1);
}
.math-fraction .denominator {
  padding: var(--space-1) var(--space-2) 0;
}
.math-sum {
  font-size: 1.5em;
  vertical-align: middle;
  line-height: 1;
}
```

**Common Unicode math symbols reference:**
- Summation: ∑  Greek: α β γ δ ε θ λ μ σ φ ω Σ Δ Θ Λ Π
- Operators: × ÷ ± ∓ ≈ ≠ ≤ ≥ ≪ ≫ ∝ ∞
- Calculus: ∂ ∇ ∫ ∬ ∮
- Sets: ∈ ∉ ⊂ ⊃ ∪ ∩ ∅ ∀ ∃
- Arrows: → ← ↔ ⇒ ⇐ ⇔ ↦
- Other: √ ‖ · ∘ ⊗ ⊕ ℝ ℕ ℤ

---

## Syntax Highlighting for Notation Blocks (Catppuccin-inspired)

For notation on the dark `--color-bg-code` background:

```css
.notation-keyword  { color: #CBA6F7; }  /* purple — key terms, operators */
.notation-variable { color: #89B4FA; }  /* blue — variables */
.notation-number   { color: #FAB387; }  /* peach — numbers, constants */
.notation-function { color: #A6E3A1; }  /* green — function names */
.notation-comment  { color: #6C7086; }  /* muted gray — annotations */
.notation-string   { color: #F9E2AF; }  /* yellow — labels, subscripts */
.notation-operator { color: #94E2D5; }  /* teal — =, +, ×, etc. */
.notation-accent   { color: #F38BA8; }  /* pink — emphasis, key results */
```
