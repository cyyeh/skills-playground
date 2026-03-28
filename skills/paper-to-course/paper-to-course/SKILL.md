---
name: paper-to-course
description: "Turn any academic or research paper into a beautiful, interactive single-page HTML course that teaches the paper's ideas to non-experts. Use this skill whenever someone wants to create an interactive course, tutorial, or educational walkthrough from a research paper, academic article, or scientific publication. Also trigger when users mention 'turn this paper into a course,' 'explain this paper interactively,' 'teach this research,' 'interactive tutorial from paper,' 'paper walkthrough,' 'learn from this paper,' 'make a course from this arxiv paper,' 'break down this paper for me,' or 'I want to understand this paper.' This skill produces a stunning, self-contained HTML file with scroll-based navigation, animated visualizations, embedded quizzes, and jargon-to-plain-English side-by-side translations."
license: Apache-2.0
metadata:
  author: cyyeh
---

# Paper-to-Course

Transform any academic or research paper into a stunning, interactive single-page HTML course. The output is a single self-contained HTML file (no dependencies except Google Fonts) that teaches the paper's ideas through scroll-based modules, animated visualizations, embedded quizzes, and plain-English translations of equations and academic jargon.

## First-Run Welcome

When the skill is first triggered and the user hasn't specified a paper yet, introduce yourself and explain what you do:

> **I can turn any research paper into an interactive course that teaches its key ideas — no academic background required.**
>
> Just point me at a paper:
> - **A PDF file** — e.g., "turn ./attention-is-all-you-need.pdf into a course"
> - **An arXiv link** — e.g., "make a course from https://arxiv.org/abs/1706.03762"
> - **A paper title** — e.g., "make a course about the Transformer paper"
> - **A pasted abstract or excerpt** — if you have the text handy
>
> I'll read through the paper, extract the key ideas, and generate a beautiful single-page HTML course with animated diagrams, plain-English equation explanations, and interactive quizzes. The whole thing runs in your browser — no setup needed.

If the user provides an arXiv link, fetch the PDF first. If they provide a local PDF path, read it directly. If they give a paper title, search for it and confirm before proceeding.

## Who This Is For

The target learner is a **curious non-expert** — someone who encountered an interesting paper (shared on social media, referenced in a blog post, cited in a meeting) and wants to actually understand what it says. They might be a product manager trying to evaluate whether a new technique is relevant, a journalist covering a scientific breakthrough, a student encountering a field for the first time, or simply a curious person who refuses to accept "just trust the experts."

**Assume no domain expertise.** Every technical concept — from p-values to attention mechanisms to gene expression — needs to be explained in plain language as if the learner has never encountered it. No jargon without definition. No "as is well-known in the literature." The tone should be like a brilliant friend who happens to have a PhD explaining things over coffee, not a professor lecturing.

**Their goals are practical, not academic:**
- **Understand the core claim** — what did the researchers actually find, and why does it matter?
- **Follow the reasoning** — how did they get from question to answer? What evidence supports the conclusion?
- **Think critically** — what are the limitations? What did the paper NOT prove? Where might the authors be wrong?
- **Join the conversation** — acquire enough vocabulary and understanding to discuss the paper intelligently with experts, write about it, or decide whether it's relevant to their work
- **Build intuition** — develop a mental model of the domain so future papers in the area are less intimidating
- **Spot oversimplifications** — when someone on Twitter says "this paper proves X," know enough to evaluate whether that's actually what it says

**They are NOT trying to become researchers.** They want understanding as a superpower that amplifies what they're already good at. They don't need to reproduce the experiments — they need to *grasp* the ideas, *evaluate* the evidence, and *explain* the significance.

## Why This Approach Works

Academic papers are written for other researchers — dense, jargon-heavy, and structured for peer review, not comprehension. This skill inverts that: instead of starting with methodology and building toward results (the way papers are written), we start with **what the researchers found and why you should care**, then peel back the layers to show how they got there.

The learner already has something traditional students don't — **motivation**. They found this paper because something about it is relevant to their life. The course meets them where they are: "You've heard that [X technique] is changing [Y field]. Here's what's actually going on under the hood."

Every module answers **"why should I care?"** before "how does it work?" The answer is always practical: *because this finding affects how you think about [topic], or because understanding this method helps you evaluate claims in the news, or because this concept shows up everywhere once you know what to look for.*

The single-file constraint is intentional: one HTML file means zero setup, instant sharing, works offline, and forces tight design decisions.

---

## The Process (4 Phases)

### Phase 1: Paper Analysis

Before writing any HTML, deeply understand the paper. Read it carefully, extract the core argument, map the logical structure, and identify what makes it significant. Thoroughness here pays off — the more you understand, the better the course.

**What to extract:**
- The **central claim** — what is the paper arguing or demonstrating? State it in one plain sentence.
- The **motivation** — what problem existed before this paper? Why did the authors care?
- The **key concepts** — the main ideas, techniques, or theories the paper introduces or builds on. These are the "cast of characters" for the course.
- The **methodology** — how did the researchers test their claim? What experiments, proofs, or analyses did they use?
- The **evidence chain** — what results support the claim? Key figures, tables, statistics.
- The **limitations and caveats** — what does the paper NOT prove? What assumptions did the authors make?
- The **significance** — why does this paper matter? What changed because of it? Who cited it and why?
- The **related work** — what came before, and how does this paper build on or differ from prior work?

**Figure out what the paper is about yourself** by reading the abstract, introduction, conclusion, and key figures first (the "three-pass" approach). Don't ask the user to explain the paper — they may not fully understand it either. The course should open by explaining what the paper discovered in plain language (a brief "here's what this research found and why it's exciting") before diving into how it works. The first module should start with a concrete, relatable hook — "Imagine you're trying to translate a sentence from English to French — here's the breakthrough that changed how computers do this."

### Phase 2: Curriculum Design

Structure the course as 5-8 modules. The arc always starts from what the learner already knows (the real-world problem) and moves toward what they don't (the paper's solution and evidence). Think of it as zooming in: start wide with the impact, then progressively peel back layers.

| Module Position | Purpose | Why it matters for a non-expert |
|---|---|---|
| 1 | "Here's what this paper found — and why you should care" | Start with the discovery and its real-world impact. Ground everything in something concrete the learner can relate to. |
| 2 | Meet the key concepts | Know the building blocks so you can follow the argument and recognize these ideas elsewhere |
| 3 | The problem before this paper | Understand what wasn't working so the solution makes sense — and appreciate why this was hard |
| 4 | How they solved it (the method) | Follow the researchers' approach step-by-step, building intuition for what "doing research" looks like |
| 5 | The evidence (results and experiments) | See the proof — learn to read figures, evaluate statistics, and judge whether the evidence is convincing |
| 6 | What it doesn't prove (limitations) | Build critical thinking — every paper has boundaries, assumptions, and open questions |
| 7 | The big picture (impact and future) | See how this fits into the larger field and what it means going forward |

Not every paper needs all 7. A short, focused paper might only need 4-5 modules. A foundational paper with wide impact might need 8. Adapt the arc to the paper's complexity — use your judgment on which modules are worth including based on what would actually help the learner understand and evaluate the work.

**The key principle:** Every module should connect back to a practical skill — understanding claims, evaluating evidence, thinking critically, joining conversations. If a module doesn't help the learner DO something better with this knowledge, cut it or reframe it until it does.

**Each module should contain:**
- 3-6 screens (sub-sections that flow within the module)
- At least one equation/jargon↔English translation (or paper excerpt↔plain English)
- At least one interactive element (quiz, visualization, or animation)
- One or two "insight" callout boxes with transferable thinking skills
- A metaphor that grounds the technical concept in everyday life — but NEVER reuse the same metaphor across modules, and NEVER default to the "factory" or "assembly line" metaphor (it's overused). Pick metaphors that organically fit the specific concept.

**Mandatory interactive elements (every course must include ALL of these):**
- **Expert Roundtable Animation** — at least one across the course. These are chat-style conversations between key concepts personified, or between "researchers" debating the paper's approach. They make abstract ideas feel like a conversation the learner can follow.
- **Research Pipeline / Methodology Flow Animation** — at least one across the course. The step-by-step animation showing how data flows through the research process — from question to data collection to analysis to conclusion. Every paper has a methodology pipeline — animate it.
- **Equation/Jargon ↔ Plain English Translation Blocks** — at least one per module. The left panel shows the actual equation, formula, or dense academic passage. The right panel gives a line-by-line plain English explanation. This is the core teaching tool.
- **Quizzes** — at least one per module (multiple-choice, scenario, drag-and-drop, or "spot the flaw" — any quiz type counts).
- **Glossary Tooltips** — on every technical term, first use per module.

These five element types are the backbone of every course. Other interactive elements (concept maps, layer toggles, comparison cards, etc.) are optional and should be added when they fit. But the five above must ALWAYS be present — no exceptions.

**Do NOT present the curriculum for approval — just build it.** The user wants a course, not a planning document. Design the curriculum internally, then go straight to generating the HTML. If they want changes, they'll tell you after seeing the result.

### Phase 3: Build the Course

Generate a single HTML file with embedded CSS and JavaScript. Read `references/design-system.md` for the complete CSS design tokens, typography, and color system. Read `references/interactive-elements.md` for implementation patterns of every interactive element type.

**Build order (task by task):**

1. **Foundation first** — HTML shell with all module sections (empty), complete CSS design system, navigation bar with progress tracking, scroll-snap behavior, keyboard navigation, and scroll-triggered animations. After this step, you should have a working skeleton you can scroll through.

2. **One module at a time** — Fill in each module's content, translations, and interactive elements. Don't try to write all modules in one pass — the quality drops. Build Module 1, verify it works, then Module 2, etc.

3. **Polish pass** — After all modules are built, do a final pass for transitions, mobile responsiveness, and visual consistency.

**Critical implementation rules:**
- The file must be completely self-contained (only external dependency: Google Fonts CDN)
- Use CSS `scroll-snap-type: y proximity` (NOT `mandatory` — mandatory traps users in long modules)
- Use `min-height: 100dvh` with `100vh` fallback for sections
- Only animate `transform` and `opacity` for GPU performance
- Wrap all JS in an IIFE, use `passive: true` on scroll listeners, throttle with `requestAnimationFrame`
- Include touch support for drag-and-drop, keyboard navigation (arrow keys), and ARIA attributes
- Render equations using HTML/CSS (styled spans with proper symbols) — do NOT depend on MathJax or KaTeX CDNs to keep the file self-contained. For complex equations, use Unicode math symbols and careful CSS positioning.

### Phase 4: Review and Open

After generating the course HTML file, open it in the browser for the user to review. Walk them through what was built and ask for feedback on content, design, and interactivity.

---

## Content Philosophy

These principles are what separate a great course from a generic tutorial. They should guide every content decision:

### Show, Don't Tell — Aggressively Visual
People's eyes glaze over text blocks. The course should feel closer to an infographic than a textbook. Follow these hard rules:

**Text limits:**
- Max **2-3 sentences** per text block. If you're writing a fourth sentence, stop and convert it into a visual instead.
- No text block should ever be wider than the content width AND taller than ~4 lines. If it is, break it up with a visual element.
- Every screen must be **at least 50% visual** (diagrams, equation blocks, cards, animations, badges — anything that isn't a paragraph).

**Convert text to visuals:**
- A list of 3+ items → **cards with icons** (concept cards, finding cards)
- A sequence of steps → **flow diagram with arrows** or **numbered step cards**
- "Concept A relates to Concept B" → **animated relationship flow** or **expert roundtable visualization**
- "This equation means X" → **equation↔English translation block** (not a paragraph *about* the equation)
- Comparing two approaches → **side-by-side columns** with visual contrast
- Experimental results → **animated chart or figure recreation** with annotations explaining what to look at
- Study timeline or process → **methodology pipeline animation**

**Visual breathing room:**
- Use generous spacing between elements (`--space-8` to `--space-12` between sections)
- Alternate between full-width visuals and narrow text blocks to create rhythm
- Every module should have at least one "hero visual" — a diagram, animation, or interactive element that dominates the screen and teaches the core concept at a glance

### Equation/Jargon ↔ Plain English Translations
Every equation, formula, or dense academic passage gets a side-by-side plain English translation. Left panel: the original notation or text with proper formatting. Right panel: line-by-line plain English explaining what each part means and why it matters. This is the single most valuable teaching tool for non-expert learners.

**Critical: Explain the intuition, not just the symbols.** Don't just say "sigma means sum" — say "Add up the following for every single data point in our dataset — like going through a checklist one item at a time." The explanation should build a mental picture.

**Critical: Use the paper's original notation exactly as-is.** Never simplify or alter equations from the paper. The learner should be able to look at the actual paper and recognize the same notation they learned from — that builds confidence. Instead of modifying equations to make them simpler, *choose* the most illustrative equations (the ones that capture the core idea) and explain those deeply, rather than trying to cover every equation in the paper.

### One Concept Per Screen
No walls of text. Each screen within a module teaches exactly one idea. If you need more space, add another screen — don't cram.

### Metaphors First, Then Reality
Introduce every new concept with a metaphor from everyday life. Then immediately ground it: "In the paper, this looks like..." The metaphor builds intuition; the actual notation grounds it in reality.

**Critical: No recycled metaphors.** Do NOT default to "factory" or "assembly line" for everything — those are the #1 crutch. Each concept deserves its own metaphor that feels natural to *that specific idea*. Neural attention is a spotlight in a crowded room. A loss function is a GPS recalculating your route. Gradient descent is rolling a ball downhill in fog. A confidence interval is a fishing net of a certain size. Pick the metaphor that makes the concept click, not the one that's easiest to reach for.

### Learn by Tracing
Follow what actually happens when the method is applied to a concrete example — trace the data through the pipeline end-to-end. "Imagine you feed in this sentence — here's the journey it takes through the model..." This works because the learner can hold onto a specific, tangible example while absorbing the abstract machinery. It's like watching a single package travel through an entire postal system.

### Make It Memorable
Use "insight" callout boxes for transferable thinking skills — ideas that apply beyond this specific paper. Use humor where natural (not forced). Give concepts personality — they're "characters" in a story, not abstract definitions in a glossary.

### Glossary Tooltips — No Term Left Behind
Every technical term gets a dashed-underline tooltip on first use in each module. Hover on desktop or tap on mobile to see a 1-2 sentence plain-English definition. The learner should never have to leave the page to Google a term. This is the difference between a course that *says* it's for non-experts and one that actually *is*.

**Be extremely aggressive with tooltips.** If there is even a 1% chance a non-expert doesn't know a word, tooltip it. This includes:
- Statistical terms (p-value, confidence interval, regression, variance, standard deviation, etc.)
- Domain-specific jargon (whatever field the paper is in)
- Research methodology terms (RCT, cohort study, ablation, hyperparameter, etc.)
- Math notation names (summation, gradient, dot product, etc.)
- Acronyms — ALWAYS tooltip acronyms on first use

**The vocabulary IS the learning.** One of the key goals is for learners to acquire the precise technical vocabulary they need to discuss the paper intelligently. Each tooltip should teach the term in a way that helps the learner USE it in conversation — e.g., "A **p-value** is the probability that you'd see results this extreme if there were actually no real effect. Scientists typically consider p < 0.05 'statistically significant.' When someone says 'the results were significant,' this is what they mean."

**Cursor:** Use `cursor: pointer` on terms (not `cursor: help`). The question-mark cursor feels clinical — a pointer feels clickable and inviting.

**Tooltip overflow fix:** Translation blocks and other containers with `overflow: hidden` will clip tooltips. To fix this, the tooltip JS must use `position: fixed` and calculate coordinates from `getBoundingClientRect()` instead of relying on CSS `position: absolute` within the container. Append tooltips to `document.body` rather than inside the term element. This ensures tooltips are never clipped by any ancestor's overflow.

### Quizzes That Test Understanding, Not Memory

The goal is to build genuine understanding — being able to *think with* what you learned. Quizzes should test whether the learner can reason about new situations using the paper's ideas, not whether they can parrot back a definition.

**What to quiz (in order of value):**
1. **"What would this predict?" scenarios** — Present a new situation the paper didn't cover and ask the learner to apply the paper's framework. e.g., "Based on what you learned about attention mechanisms, what would happen if the input sequence were twice as long?" This is the gold standard.
2. **Critical thinking scenarios** — "A news headline says 'Study proves X.' Based on what you learned about the paper's limitations, what's misleading about this headline?" Tests whether they understood the caveats.
3. **Methodology reasoning** — "The researchers chose method A over method B. Why? What would change if they'd used method B?" Tests whether they understood the reasoning, not just the choice.
4. **Tracing exercises** — "Walk through what happens when [concrete input] goes through the model/process." Tests whether they can follow the pipeline.

**What NOT to quiz:**
- Definitions ("What does RNN stand for?") — that's what the glossary tooltips are for
- Specific numbers ("What was the accuracy on benchmark X?") — nobody memorizes statistics
- Author names or publication details — this isn't a literature exam
- Anything that can be answered by scrolling up and copying

**Quiz tone:**
- Wrong answers get encouraging, non-judgmental explanations ("Not quite — here's why...")
- Correct answers get brief reinforcement of the underlying principle ("Exactly! This works because...")
- Never punitive, never score-focused. The quiz is a thinking exercise, not an exam
- Wrong answer explanations should teach something new, not just say "wrong"

**How many quizzes:** One per module, placed at the end after the learner has seen all the content. 3-5 questions per quiz. Each question should make the learner pause and *think*.

---

## Design Identity

The visual design should feel like a **beautiful scientific journal reimagined for the web** — warm, inviting, intellectually stimulating, but never intimidating. Read `references/design-system.md` for the full token system, but here are the non-negotiable principles:

- **Warm palette**: Off-white backgrounds (like quality paper), warm grays, NO cold whites or blues
- **Bold accent**: One confident accent color (deep teal, scholarly vermillion, or warm amber — NOT neon or purple gradients)
- **Distinctive typography**: Display font with personality for headings (Bricolage Grotesque, or similar bold geometric face — NEVER Inter, Roboto, Arial, or Space Grotesk). Clean sans-serif for body (DM Sans or similar). JetBrains Mono for equations and notation.
- **Generous whitespace**: Modules breathe. Max 3-4 short paragraphs per screen.
- **Alternating backgrounds**: Even/odd modules alternate between two warm background tones for visual rhythm
- **Dark equation/notation blocks**: IDE-style with Catppuccin-inspired highlighting on deep indigo-charcoal (#1E1E2E)
- **Depth without harshness**: Subtle warm shadows, never black drop shadows

---

## Gotchas — Common Failure Points

These are real problems encountered when building courses. Check every one before considering a course complete.

### Tooltip Clipping
Translation blocks use `overflow: hidden` for content wrapping. If tooltips use `position: absolute` inside the term element, they get clipped by the container. **Fix:** Tooltips must use `position: fixed` and be appended to `document.body`. Calculate position from `getBoundingClientRect()`. This is the #1 bug that appears in every build.

### Not Enough Tooltips
The most common failure is under-tooltipping. Non-experts don't know terms like p-value, regression, ablation study, hyperparameter, gradient, epoch, latent space, Bayesian, etc. **Rule of thumb:** if a term wouldn't appear in everyday conversation with a non-technical friend, tooltip it. Err heavily on the side of too many.

### Walls of Text
The course looks like a textbook instead of an infographic. This happens when you write more than 2-3 sentences in a row without a visual break. Every screen must be at least 50% visual. Convert any list of 3+ items into cards, any sequence into step cards or flow diagrams, any equation explanation into an equation↔English translation block.

### Recycled Metaphors
Using "factory" or "assembly line" for everything. Every module needs its own metaphor that feels inevitable for that specific concept. If you catch yourself reaching for the same metaphor twice, stop and find one that fits the concept organically.

### Oversimplification That Distorts
There's a difference between making something accessible and making it wrong. "Neural networks are just like brains" is misleading. "Neural networks are loosely inspired by brains but actually work quite differently — here's how" is accessible AND accurate. Always preserve the core truth, even when simplifying. When in doubt, add a brief caveat ("This is a simplification — the full picture is more nuanced, but this captures the key idea").

### Equation Modifications
Altering, simplifying, or reformatting equations from the paper. The learner should be able to look at the actual paper and see the exact same notation they learned from. Instead of modifying equations, *choose* the most illustrative ones and explain them deeply.

### Quiz Questions That Test Memory
Asking "What does CNN stand for?" or "What accuracy did they achieve?" — those test recall, not understanding. Every quiz question should present a new scenario the learner hasn't seen and ask them to *apply* what they learned.

### Scroll-Snap Mandatory
Using `scroll-snap-type: y mandatory` traps users inside long modules. Always use `proximity`.

### Module Quality Degradation
Trying to write all modules in one pass causes later modules to be thin and rushed. Build one module at a time and verify each before moving on.

### Missing Interactive Elements
A module with only text and equation blocks, no interactivity. Every module needs at least one of: quiz, methodology flow animation, expert roundtable, concept map, drag-and-drop. These aren't decorations — they're how people actually process complex information.

### External Dependencies for Math Rendering
Do NOT link to MathJax or KaTeX CDNs — the course must be fully self-contained. Use Unicode math symbols (summation: ∑, integral: ∫, partial: ∂, etc.), HTML `<sup>` and `<sub>` tags, and CSS styling to render equations. For complex layouts, use CSS grid or flexbox to position numerators, denominators, and fraction bars. The result won't be LaTeX-perfect, but it will be readable, accessible, and work offline.

---

## Reference Files

The `references/` directory contains detailed implementation specs. Read them when you reach the relevant phase:

- **`references/design-system.md`** — Complete CSS custom properties, color palette, typography scale, spacing system, shadows, animations, scrollbar styling. Read this before writing any CSS.
- **`references/interactive-elements.md`** — Implementation patterns for every interactive element: equation↔English translations, multiple-choice quizzes, drag-and-drop matching, expert roundtable animations, methodology flow visualizations, concept maps, comparison cards, callout boxes, and more. Read this before building any interactive elements.
