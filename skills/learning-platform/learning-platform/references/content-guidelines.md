# Content Guidelines

Detailed guidelines for generating each of the 6 content types per topic.

---

## 1. In-Depth Analysis (`_analysis.md`)

Professional, comprehensive treatment. The core reference material.

### Structure

```markdown
# [Topic]: In-Depth Analysis

## Introduction
What this covers and why it matters.

---

## Part 1: [Core Concept Area]

### [Subtopic]
Deep explanation with frameworks, models, data.

### [Subtopic]
...

---

## Part 2: [Another Area]
...

---

## Summary & Key Takeaways
Numbered list of the most important points.
```

### Guidelines
- 2000-3000 words
- Proper heading hierarchy (H1 title, H2 parts, H3 subtopics)
- Tables for comparisons, blockquotes for key definitions
- Bold key terms on first use
- Cite real researchers, frameworks, theories by name
- Horizontal rules between major sections

---

## 2. Beginner-Friendly Guide (`_guide.md`)

Plain language — accessible to anyone with zero background.

### Structure

```markdown
# [Topic]: A Beginner's Guide

## What Is [Topic]?
Imagine you're [vivid everyday scenario]...

---

## Part 1: The Basics

### [Concept] in Plain Terms
**[Term]** is basically like [analogy]...

#### Example: [Real-Life Situation]
Concrete walkthrough.

---

## Quick Reference
Summary table or checklist.
```

### Guidelines
- 1500-2000 words
- Start with a relatable scenario
- Everyday analogies throughout
- Define jargon immediately when used
- Short paragraphs, bullet points
- Friendly, conversational, encouraging tone

---

## 3. Case Studies (`_cases.md`)

Real-world events/examples illustrating the topic in action.

### Structure

```markdown
# [Topic]: Case Studies

> Real-world cases related to [topic]. Each describes background, events, and relevance.

---

### Case 1: [Event/Name] — [Year]

**Background**
Context with dates, names, numbers.

**What Happened**
Chronological narrative.

**Relevance to [Topic]**
Which concepts this illustrates.

**References**
- [Source](URL)
```

### Guidelines
- 3-5 cases per topic
- Real events with verifiable facts
- Specific dates, numbers, names
- Explain connection to topic concepts
- Real source URLs
- For abstract fields (math, philosophy): use historical discoveries, thought experiments, famous debates

---

## 4. Interactive HTML (`_interactive.html`)

Self-contained HTML pages embedded via iframe. Genuinely useful learning tools.

### Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[Topic] Interactive Tools</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: #f1f5f9; min-height: 100vh; padding: 24px;
  }
  .container { max-width: 920px; margin: 0 auto; }
  h1 { text-align: center; font-size: 26px; color: #1e293b; margin-bottom: 4px; }
  .subtitle { text-align: center; font-size: 14px; color: #94a3b8; margin-bottom: 18px; }
  .tabs { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; margin-bottom: 18px; }
  .tab-btn {
    padding: 8px 20px; border-radius: 20px; border: 1px solid #cbd5e1;
    background: #fff; color: #64748b; font-size: 14px; cursor: pointer; transition: all .2s;
  }
  .tab-btn:hover { border-color: #94a3b8; }
  .tab-btn.active { background: #1e293b; color: #fff; border-color: #1e293b; }
  .tab-content { display: none; }
  .tab-content.active { display: block; }
  .panel {
    background: #fff; border-radius: 14px; border: 1px solid #e2e8f0;
    box-shadow: 0 1px 4px rgba(0,0,0,.06); padding: 24px; margin-bottom: 16px;
  }
  @media (max-width: 640px) {
    body { padding: 12px; }
    .tab-btn { padding: 6px 14px; font-size: 13px; }
  }
</style>
</head>
<body>
<div class="container">
  <h1>[Title]</h1>
  <p class="subtitle">[Description]</p>
  <div class="tabs">
    <button class="tab-btn active" onclick="switchTab(0)">Tool 1</button>
    <button class="tab-btn" onclick="switchTab(1)">Tool 2</button>
  </div>
  <div class="tab-content active" id="tab-0"><!-- Tool 1 --></div>
  <div class="tab-content" id="tab-1"><!-- Tool 2 --></div>
</div>
<script>
function switchTab(idx) {
  document.querySelectorAll('.tab-btn').forEach((b,i) => b.classList.toggle('active', i===idx));
  document.querySelectorAll('.tab-content').forEach((c,i) => c.classList.toggle('active', i===idx));
}
</script>
</body>
</html>
```

### Interactive Ideas by Domain

| Domain | Tool Ideas |
|--------|-----------|
| Sciences | Formula calculators, simulations, animated diagrams, periodic table |
| Humanities | Timeline explorers, concept maps, debate comparisons, historical maps |
| Practical | Step-by-step builders, checklists, decision trees, comparison matrices |
| Arts | Visual galleries, audio explorers, style comparisons |
| Business | Financial calculators, org charts, process flows, dashboards |

### Common Patterns

- **Relationship diagram**: SVG nodes + connections, filter by category, click for detail panel
- **Calculator**: Input fields → computed outputs, optionally with charts
- **Explorer**: Filterable cards/list with detail view on click
- **Process flow**: Step-by-step animation with play/pause
- **Matrix/Grid**: 2D grid with clickable cells (e.g., risk matrix, comparison grid)

### Requirements
- All CSS/JS/data self-contained — no external deps unless essential
- Works in iframe, responsive (test at 320px and 920px)
- 3-5 tools per page via tab navigation
- Include hints/tooltips for discoverability
- Use CSS transitions for polish

---

## 5. Practice Quiz (`_quiz.md`)

Self-assessment with varied question types and detailed explanations.

### Structure

```markdown
# [Topic]: Practice & Self-Assessment

> Complete these after reading the analysis and guide. Answers at each section's end.

---

## Section 1: True or False (10 questions)
**1. [Statement]**
...

### Answers
1. **True/False** — Explanation...

---

## Section 2: Multiple Choice (5-8 questions)
**1. [Question]**
A. [Option]  B. [Option]  C. [Option]  D. [Option]
...

### Answers
1. **C** — Explanation...

---

## Section 3: Scenario Analysis (2-3)
**Scenario 1:** [Situation description]
1. [Question]
2. [Question]

### Analysis
...

---

## Section 4: Reflection Questions
1. [Open-ended thought question]
```

### Guidelines
- 20-30 questions total across sections
- True/False: target common misconceptions
- Multiple Choice: plausible distractors
- Every answer includes detailed explanation referencing concepts
- Reflection questions encourage deeper thinking

---

## 6. Further Resources (`_resources.md`)

Curated recommendations for continued learning.

### Structure

```markdown
# [Topic]: Further Learning Resources

[Brief intro]

---

## Books
**[Title - Author](URL)**
- Description. Difficulty: Beginner/Intermediate/Advanced

---

## Online Courses
**[Course (Platform)](URL)**
- Description. Difficulty: ...

---

## Podcasts
**[Name](URL)**
- Description. Difficulty: ...

---

## Videos & YouTube
**[Channel/Video](URL)**
- Description.

---

## Websites & Tools
**[Name](URL)**
- Description.
```

### Guidelines
- 3-5 items per category
- Real, currently available resources with working URLs
- Difficulty ratings on each
- Range from beginner to advanced
- Diverse media types
