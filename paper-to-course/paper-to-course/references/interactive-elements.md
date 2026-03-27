# Interactive Elements Reference

Implementation patterns for every interactive element type used in paper courses. Pick the elements that best serve each module's teaching goal.

## Table of Contents
1. [Equation/Jargon ↔ English Translation Blocks](#equationjargon--english-translation-blocks)
2. [Multiple-Choice Quizzes](#multiple-choice-quizzes)
3. [Drag-and-Drop Matching](#drag-and-drop-matching)
4. [Expert Roundtable Animation](#expert-roundtable-animation)
5. [Research Pipeline / Methodology Flow Animation](#research-pipeline--methodology-flow-animation)
6. [Interactive Concept Map](#interactive-concept-map)
7. [Layer Toggle Demo](#layer-toggle-demo)
8. ["Spot the Flaw" Challenge](#spot-the-flaw-challenge)
9. [Scenario Quiz](#scenario-quiz)
10. [Callout Boxes](#callout-boxes)
11. [Concept/Finding Cards](#conceptfinding-cards)
12. [Flow Diagrams](#flow-diagrams)
13. [Comparison Cards](#comparison-cards)
14. [Glossary Tooltips](#glossary-tooltips)
15. [Figure Annotation Overlay](#figure-annotation-overlay)
16. [Evidence Strength Meter](#evidence-strength-meter)
17. [Numbered Step Cards](#numbered-step-cards)

---

## Equation/Jargon ↔ English Translation Blocks

The most important teaching element. Shows the original equation, formula, or dense academic passage on the left and a plain English translation on the right, element by element.

**HTML:**
```html
<div class="translation-block animate-in">
  <div class="translation-notation">
    <span class="translation-label">FROM THE PAPER</span>
    <div class="notation-content">
      <div class="math-block">
        <span class="notation-function">Attention</span>(<span class="notation-variable">Q</span>, <span class="notation-variable">K</span>, <span class="notation-variable">V</span>) = <span class="notation-function">softmax</span>(
        <span class="math-fraction">
          <span class="numerator"><span class="notation-variable">Q</span><span class="notation-variable">K</span><sup>T</sup></span>
          <span class="denominator">√<span class="notation-variable">d<sub>k</sub></span></span>
        </span>
        )<span class="notation-variable">V</span>
      </div>
    </div>
  </div>
  <div class="translation-english">
    <span class="translation-label">PLAIN ENGLISH</span>
    <div class="translation-lines">
      <p class="tl"><strong>Attention</strong> is a way to figure out which parts of the input to focus on...</p>
      <p class="tl"><strong>Q, K, V</strong> are three different "views" of the same data — like looking at a painting from three angles...</p>
      <p class="tl"><strong>QK<sup>T</sup></strong> measures how much each piece of input "cares about" every other piece...</p>
      <p class="tl"><strong>÷ √d<sub>k</sub></strong> keeps the numbers from getting too big (a scaling trick)...</p>
      <p class="tl"><strong>softmax</strong> turns the scores into percentages that add up to 100%...</p>
      <p class="tl"><strong>× V</strong> uses those percentages to create a weighted blend of the original information.</p>
    </div>
  </div>
</div>
```

**CSS:**
```css
.translation-block {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: var(--shadow-md);
  margin: var(--space-8) 0;
}
.translation-notation {
  background: var(--color-bg-code);
  color: #CDD6F4;
  padding: var(--space-6);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  line-height: 1.7;
  position: relative;
  overflow-x: hidden;
}
.translation-notation .notation-content {
  white-space: pre-wrap;
  word-break: break-word;
  overflow-x: hidden;
}
.translation-english {
  background: var(--color-surface-warm);
  padding: var(--space-6);
  font-size: var(--text-sm);
  line-height: 1.7;
  border-left: 3px solid var(--color-accent);
}
.translation-label {
  position: absolute;
  top: var(--space-2);
  right: var(--space-3);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  opacity: 0.5;
}
.translation-english .translation-label {
  color: var(--color-text-muted);
}
@media (max-width: 768px) {
  .translation-block { grid-template-columns: 1fr; }
  .translation-english { border-left: none; border-top: 3px solid var(--color-accent); }
}
```

**Rules:**
- Each English line should correspond to one symbol, term, or operation in the equation
- Explain the *intuition*, not just the symbol names — "measures how much each piece cares about every other piece" not "computes the dot product of Q and K transpose"
- Bold the notation element being explained on each line so the reader can track left-to-right
- For dense text passages (not equations), use the same layout but with the original academic text on the left

---

## Multiple-Choice Quizzes

For testing understanding with instant feedback. Each question has options, one correct answer, and per-question explanations.

**HTML:**
```html
<div class="quiz-container">
  <div class="quiz-question-block" data-question="q1" data-correct="option-b">
    <h3 class="quiz-question">A startup claims their model "uses attention just like the paper describes." But their model only looks at the 5 words before each word, not the entire sentence. What's wrong with their claim?</h3>
    <div class="quiz-options">
      <button class="quiz-option" data-value="option-a" onclick="selectOption(this)">
        <div class="quiz-option-radio"></div>
        <span>Nothing — 5 words is enough context</span>
      </button>
      <button class="quiz-option" data-value="option-b" onclick="selectOption(this)">
        <div class="quiz-option-radio"></div>
        <span>The whole point of attention is looking at ALL positions, not just nearby ones</span>
      </button>
      <button class="quiz-option" data-value="option-c" onclick="selectOption(this)">
        <div class="quiz-option-radio"></div>
        <span>They should use more attention heads</span>
      </button>
    </div>
    <div class="quiz-feedback" id="q1-feedback"></div>
  </div>

  <button class="quiz-check-btn" onclick="checkQuiz('section-id')">Check Answers</button>
  <button class="quiz-reset-btn" onclick="resetQuiz('section-id')">Try Again</button>
  <div class="quiz-overall-feedback" id="section-overall"></div>
</div>
```

**JS pattern:**
```javascript
window.selectOption = function(btn) {
  const block = btn.closest('.quiz-question-block');
  block.querySelectorAll('.quiz-option').forEach(o => o.classList.remove('selected'));
  btn.classList.add('selected');
};

window.checkQuiz = function(sectionId) {
  const container = document.querySelector(`#${sectionId} .quiz-container`);
  const questions = container.querySelectorAll('.quiz-question-block');
  let correct = 0;

  questions.forEach(q => {
    const selected = q.querySelector('.quiz-option.selected');
    const feedback = q.querySelector('.quiz-feedback');
    const correctValue = q.dataset.correct;

    if (!selected) {
      feedback.textContent = 'Pick an answer first!';
      feedback.className = 'quiz-feedback show warning';
      return;
    }

    if (selected.dataset.value === correctValue) {
      correct++;
      selected.classList.add('correct');
      feedback.innerHTML = '<strong>Exactly!</strong> ' + getExplanation(q, true);
      feedback.className = 'quiz-feedback show success';
    } else {
      selected.classList.add('incorrect');
      q.querySelector(`[data-value="${correctValue}"]`).classList.add('correct');
      feedback.innerHTML = '<strong>Not quite.</strong> ' + getExplanation(q, false);
      feedback.className = 'quiz-feedback show error';
    }

    q.querySelectorAll('.quiz-option').forEach(o => o.disabled = true);
  });
};
```

**CSS for quiz states:**
```css
.quiz-option {
  display: flex; align-items: center; gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  cursor: pointer; width: 100%;
  transition: border-color var(--duration-fast), background var(--duration-fast);
}
.quiz-option:hover { border-color: var(--color-accent-muted); }
.quiz-option.selected { border-color: var(--color-accent); background: var(--color-accent-light); }
.quiz-option.correct { border-color: var(--color-success); background: var(--color-success-light); }
.quiz-option.incorrect { border-color: var(--color-error); background: var(--color-error-light); }
.quiz-option-radio {
  width: 18px; height: 18px; border-radius: 50%;
  border: 2px solid var(--color-border);
  transition: all var(--duration-fast);
}
.quiz-option.selected .quiz-option-radio {
  border-color: var(--color-accent);
  background: var(--color-accent);
  box-shadow: inset 0 0 0 3px white;
}
.quiz-feedback {
  max-height: 0; overflow: hidden; opacity: 0;
  transition: max-height var(--duration-normal), opacity var(--duration-normal);
}
.quiz-feedback.show { max-height: 200px; opacity: 1; padding: var(--space-3); margin-top: var(--space-2); border-radius: var(--radius-sm); }
.quiz-feedback.success { background: var(--color-success-light); color: var(--color-success); }
.quiz-feedback.error { background: var(--color-error-light); color: var(--color-error); }
```

---

## Drag-and-Drop Matching

For matching concepts to descriptions, terms to definitions, or causes to effects. Supports both mouse (HTML5 Drag API) and touch.

**HTML:**
```html
<div class="dnd-container">
  <div class="dnd-chips">
    <div class="dnd-chip" draggable="true" data-answer="concept-a">Concept A</div>
    <div class="dnd-chip" draggable="true" data-answer="concept-b">Concept B</div>
    <div class="dnd-chip" draggable="true" data-answer="concept-c">Concept C</div>
  </div>
  <div class="dnd-zones">
    <div class="dnd-zone" data-correct="concept-a">
      <p class="dnd-zone-label">Description of Concept A in plain English</p>
      <div class="dnd-zone-target">Drop here</div>
    </div>
    <!-- more zones -->
  </div>
  <button onclick="checkDnD()">Check Matches</button>
  <button onclick="resetDnD()">Reset</button>
</div>
```

**JS (mouse + touch):**
```javascript
// MOUSE: HTML5 Drag API
chips.forEach(chip => {
  chip.addEventListener('dragstart', (e) => {
    e.dataTransfer.setData('text/plain', chip.dataset.answer);
    chip.classList.add('dragging');
  });
  chip.addEventListener('dragend', () => chip.classList.remove('dragging'));
});

zones.forEach(zone => {
  const target = zone.querySelector('.dnd-zone-target');
  target.addEventListener('dragover', (e) => { e.preventDefault(); target.classList.add('drag-over'); });
  target.addEventListener('dragleave', () => target.classList.remove('drag-over'));
  target.addEventListener('drop', (e) => {
    e.preventDefault();
    target.classList.remove('drag-over');
    const answer = e.dataTransfer.getData('text/plain');
    const chip = document.querySelector(`[data-answer="${answer}"]`);
    target.textContent = chip.textContent;
    target.dataset.placed = answer;
    chip.classList.add('placed');
  });
});

// TOUCH: Custom implementation
chips.forEach(chip => {
  chip.addEventListener('touchstart', (e) => {
    e.preventDefault();
    const touch = e.touches[0];
    const clone = chip.cloneNode(true);
    clone.classList.add('touch-ghost');
    clone.style.cssText = `position:fixed; z-index:1000; pointer-events:none;
      left:${touch.clientX - 40}px; top:${touch.clientY - 20}px;`;
    document.body.appendChild(clone);
    chip._ghost = clone;
    chip._answer = chip.dataset.answer;
  }, { passive: false });

  chip.addEventListener('touchmove', (e) => {
    e.preventDefault();
    const touch = e.touches[0];
    if (chip._ghost) {
      chip._ghost.style.left = (touch.clientX - 40) + 'px';
      chip._ghost.style.top = (touch.clientY - 20) + 'px';
    }
  }, { passive: false });
});
```

---

## Expert Roundtable Animation

iMessage/chat-style conversation between personified concepts, researchers, or perspectives from the paper. These make abstract ideas feel like an overheard conversation the learner can follow.

**HTML:**
```html
<div class="roundtable-container" id="roundtable-1">
  <div class="roundtable-header">
    <h3>The Concepts Discuss: Why Self-Attention?</h3>
    <button class="roundtable-play" onclick="playRoundtable('roundtable-1')">Watch the discussion</button>
  </div>
  <div class="roundtable-messages">
    <!-- Messages appear one by one with typing indicator -->
    <div class="rt-message" data-speaker="RNN" data-delay="0" style="--speaker-color: var(--color-concept-1)">
      <div class="rt-avatar">RNN</div>
      <div class="rt-bubble">
        <div class="rt-name">Recurrent Neural Network</div>
        <p>I process words one at a time, left to right. It's how I was built.</p>
      </div>
    </div>
    <div class="rt-message right" data-speaker="Attention" data-delay="1" style="--speaker-color: var(--color-concept-2)">
      <div class="rt-bubble">
        <div class="rt-name">Self-Attention</div>
        <p>But that means by the time you reach the end of a long sentence, you've half-forgotten the beginning!</p>
      </div>
      <div class="rt-avatar">ATT</div>
    </div>
    <div class="rt-message" data-speaker="RNN" data-delay="2" style="--speaker-color: var(--color-concept-1)">
      <div class="rt-avatar">RNN</div>
      <div class="rt-bubble">
        <div class="rt-name">Recurrent Neural Network</div>
        <p>Fair point. And I can't process words in parallel — each one has to wait for the last.</p>
      </div>
    </div>
    <div class="rt-message right" data-speaker="Attention" data-delay="3" style="--speaker-color: var(--color-concept-2)">
      <div class="rt-bubble">
        <div class="rt-name">Self-Attention</div>
        <p>I look at ALL words simultaneously. Every word gets to "attend" to every other word. No forgetting, no waiting.</p>
      </div>
      <div class="rt-avatar">ATT</div>
    </div>
  </div>
</div>
```

**CSS:**
```css
.roundtable-container {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--shadow-md);
  margin: var(--space-8) 0;
}
.roundtable-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: var(--space-4);
}
.roundtable-play {
  background: var(--color-accent); color: white;
  border: none; border-radius: var(--radius-full);
  padding: var(--space-2) var(--space-5);
  font-family: var(--font-body); font-size: var(--text-sm);
  cursor: pointer; transition: background var(--duration-fast);
}
.roundtable-play:hover { background: var(--color-accent-hover); }
.rt-message {
  display: flex; gap: var(--space-3); align-items: flex-start;
  margin-bottom: var(--space-4);
  opacity: 0; transform: translateY(10px);
  transition: opacity var(--duration-normal), transform var(--duration-normal);
}
.rt-message.visible { opacity: 1; transform: translateY(0); }
.rt-message.right { flex-direction: row-reverse; }
.rt-avatar {
  width: 40px; height: 40px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-mono); font-size: var(--text-xs);
  font-weight: 600; color: white; flex-shrink: 0;
  background: var(--speaker-color);
}
.rt-bubble {
  background: var(--color-surface-warm);
  border-radius: var(--radius-md);
  padding: var(--space-3) var(--space-4);
  max-width: 75%;
  border: 1px solid var(--color-border-light);
}
.rt-message.right .rt-bubble {
  background: color-mix(in srgb, var(--speaker-color) 8%, white);
}
.rt-name {
  font-size: var(--text-xs); font-weight: 600;
  color: var(--speaker-color);
  margin-bottom: var(--space-1);
}
.rt-typing {
  display: flex; gap: 4px; padding: var(--space-2) var(--space-3);
}
.rt-typing span {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--color-text-muted);
  animation: typingBounce 1.4s infinite;
}
.rt-typing span:nth-child(2) { animation-delay: 0.2s; }
.rt-typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes typingBounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-5px); }
}
```

**JS:**
```javascript
function playRoundtable(id) {
  const container = document.getElementById(id);
  const messages = container.querySelectorAll('.rt-message');
  const btn = container.querySelector('.roundtable-play');
  btn.disabled = true; btn.textContent = 'Playing...';

  messages.forEach((msg, i) => {
    // Show typing indicator first
    setTimeout(() => {
      const typing = document.createElement('div');
      typing.className = 'rt-typing';
      typing.innerHTML = '<span></span><span></span><span></span>';
      msg.querySelector('.rt-bubble').prepend(typing);
      msg.style.opacity = '1'; msg.style.transform = 'translateY(0)';

      // Replace typing with actual message after brief delay
      setTimeout(() => { typing.remove(); msg.classList.add('visible'); }, 800);
    }, i * 2000);
  });

  setTimeout(() => {
    btn.textContent = 'Replay';
    btn.disabled = false;
    btn.onclick = () => {
      messages.forEach(m => { m.classList.remove('visible'); m.style.opacity = '0'; m.style.transform = 'translateY(10px)'; });
      playRoundtable(id);
    };
  }, messages.length * 2000 + 1000);
}
```

**Rules:**
- Give each speaker a distinct personality that matches their concept
- Keep messages short (1-2 sentences) and conversational
- The conversation should build understanding — each message adds a new insight
- End with a "punchline" that captures the key takeaway
- Ideal for: explaining trade-offs, comparing approaches, showing why one method was chosen over another

---

## Research Pipeline / Methodology Flow Animation

Step-by-step animation showing how data flows through the research process. Each step highlights, shows a brief description, then passes to the next.

**HTML:**
```html
<div class="pipeline-container" id="pipeline-1">
  <button class="pipeline-play" onclick="playPipeline('pipeline-1')">Trace the process</button>
  <div class="pipeline-steps">
    <div class="pipeline-step" data-step="1" style="--step-color: var(--color-concept-1)">
      <div class="pipeline-icon">📝</div>
      <div class="pipeline-label">Research Question</div>
      <div class="pipeline-detail">"Can machines translate without processing words one-by-one?"</div>
    </div>
    <div class="pipeline-arrow">→</div>
    <div class="pipeline-step" data-step="2" style="--step-color: var(--color-concept-2)">
      <div class="pipeline-icon">📊</div>
      <div class="pipeline-label">Data Collection</div>
      <div class="pipeline-detail">4.5 million sentence pairs in English-German</div>
    </div>
    <div class="pipeline-arrow">→</div>
    <div class="pipeline-step" data-step="3" style="--step-color: var(--color-concept-3)">
      <div class="pipeline-icon">⚙️</div>
      <div class="pipeline-label">Model Design</div>
      <div class="pipeline-detail">Replace RNNs entirely with self-attention</div>
    </div>
    <div class="pipeline-arrow">→</div>
    <div class="pipeline-step" data-step="4" style="--step-color: var(--color-concept-4)">
      <div class="pipeline-icon">🧪</div>
      <div class="pipeline-label">Experiments</div>
      <div class="pipeline-detail">Train on 8 GPUs for 3.5 days, test on standard benchmarks</div>
    </div>
    <div class="pipeline-arrow">→</div>
    <div class="pipeline-step" data-step="5" style="--step-color: var(--color-concept-5)">
      <div class="pipeline-icon">📈</div>
      <div class="pipeline-label">Results</div>
      <div class="pipeline-detail">New state-of-the-art BLEU score, trained 10× faster</div>
    </div>
  </div>
  <div class="pipeline-packet" id="pipeline-1-packet"></div>
</div>
```

**CSS:**
```css
.pipeline-container {
  position: relative;
  padding: var(--space-8) var(--space-4);
  margin: var(--space-8) 0;
}
.pipeline-steps {
  display: flex; align-items: center; justify-content: center;
  flex-wrap: wrap; gap: var(--space-3);
}
.pipeline-step {
  display: flex; flex-direction: column; align-items: center;
  padding: var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  min-width: 120px; max-width: 160px;
  transition: all var(--duration-normal) var(--ease-out);
  text-align: center;
}
.pipeline-step.active {
  border-color: var(--step-color);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--step-color) 15%, transparent);
  transform: scale(1.05);
}
.pipeline-icon { font-size: 1.5rem; margin-bottom: var(--space-2); }
.pipeline-label {
  font-family: var(--font-display); font-weight: 600;
  font-size: var(--text-sm);
}
.pipeline-detail {
  font-size: var(--text-xs); color: var(--color-text-secondary);
  margin-top: var(--space-1);
  max-height: 0; overflow: hidden; opacity: 0;
  transition: all var(--duration-normal);
}
.pipeline-step.active .pipeline-detail {
  max-height: 100px; opacity: 1;
  margin-top: var(--space-2);
}
.pipeline-arrow {
  font-size: var(--text-xl); color: var(--color-text-muted);
  transition: color var(--duration-fast);
}
.pipeline-arrow.active { color: var(--color-accent); }
```

**JS:**
```javascript
function playPipeline(id) {
  const container = document.getElementById(id);
  const steps = container.querySelectorAll('.pipeline-step');
  const arrows = container.querySelectorAll('.pipeline-arrow');

  // Reset
  steps.forEach(s => s.classList.remove('active'));
  arrows.forEach(a => a.classList.remove('active'));

  steps.forEach((step, i) => {
    setTimeout(() => {
      if (i > 0) steps[i-1].classList.remove('active');
      step.classList.add('active');
      if (i > 0) arrows[i-1].classList.add('active');
    }, i * 1500);
  });
}
```

**Rules:**
- Use for ANY sequential process: data collection → processing → analysis → results
- Keep step labels short (2-3 words), details brief (1 sentence)
- The animation should be slow enough to read each step (~1.5s per step)
- Works for: experimental methodology, data processing pipelines, proof structures, study designs

---

## Interactive Concept Map

Shows relationships between the paper's key concepts. Nodes are clickable — clicking one highlights its connections and shows a brief description.

**HTML:**
```html
<div class="concept-map" id="concept-map-1">
  <svg class="concept-lines" viewBox="0 0 800 400">
    <!-- Lines drawn between nodes via JS -->
  </svg>
  <div class="concept-nodes">
    <div class="concept-node" data-id="attention" data-connects="query,key,value"
         style="left: 50%; top: 20%; --node-color: var(--color-concept-1)">
      <div class="concept-node-inner">Self-Attention</div>
      <div class="concept-desc">The core mechanism — lets every word look at every other word</div>
    </div>
    <div class="concept-node" data-id="query" data-connects="attention"
         style="left: 25%; top: 60%; --node-color: var(--color-concept-2)">
      <div class="concept-node-inner">Query (Q)</div>
      <div class="concept-desc">"What am I looking for?"</div>
    </div>
    <!-- more nodes -->
  </div>
</div>
```

**CSS:**
```css
.concept-map {
  position: relative; min-height: 400px;
  margin: var(--space-8) 0;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--shadow-md);
}
.concept-lines { position: absolute; inset: 0; pointer-events: none; }
.concept-lines line {
  stroke: var(--color-border); stroke-width: 2;
  transition: stroke var(--duration-fast);
}
.concept-lines line.highlighted { stroke: var(--color-accent); stroke-width: 3; }
.concept-node {
  position: absolute; transform: translate(-50%, -50%);
  cursor: pointer; text-align: center;
  transition: transform var(--duration-fast);
}
.concept-node:hover { transform: translate(-50%, -50%) scale(1.05); }
.concept-node-inner {
  background: var(--node-color); color: white;
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-full);
  font-family: var(--font-display); font-weight: 600;
  font-size: var(--text-sm); white-space: nowrap;
}
.concept-desc {
  font-size: var(--text-xs); color: var(--color-text-secondary);
  max-width: 150px; margin: var(--space-2) auto 0;
  opacity: 0; transition: opacity var(--duration-fast);
}
.concept-node.active .concept-desc { opacity: 1; }
```

---

## Layer Toggle Demo

Shows different "layers" of understanding for the same concept. Toggle between simplified view, standard view, and full technical detail.

**HTML:**
```html
<div class="layer-toggle">
  <div class="layer-tabs">
    <button class="layer-tab active" data-layer="simple" onclick="switchLayer(this)">Simple</button>
    <button class="layer-tab" data-layer="standard" onclick="switchLayer(this)">Standard</button>
    <button class="layer-tab" data-layer="technical" onclick="switchLayer(this)">Full Detail</button>
  </div>
  <div class="layer-content" data-layer="simple" style="display: block;">
    <p>Attention is like a spotlight — it helps the model focus on the most relevant parts of the input.</p>
  </div>
  <div class="layer-content" data-layer="standard" style="display: none;">
    <p>Self-attention computes a weighted sum of all input positions, where the weights are determined by how "compatible" each pair of positions is. This lets the model capture long-range dependencies without sequential processing.</p>
  </div>
  <div class="layer-content" data-layer="technical" style="display: none;">
    <div class="math-block">Attention(Q, K, V) = softmax(QK<sup>T</sup> / √d<sub>k</sub>)V</div>
    <p>The compatibility function is a scaled dot product. Scaling by √d<sub>k</sub> prevents the dot products from growing too large in magnitude, which would push softmax into regions with extremely small gradients.</p>
  </div>
</div>
```

**CSS:**
```css
.layer-toggle {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  overflow: hidden; margin: var(--space-6) 0;
}
.layer-tabs {
  display: flex; background: var(--color-border-light);
}
.layer-tab {
  flex: 1; padding: var(--space-3);
  border: none; background: none; cursor: pointer;
  font-family: var(--font-body); font-size: var(--text-sm);
  color: var(--color-text-secondary);
  transition: all var(--duration-fast);
}
.layer-tab.active {
  background: var(--color-surface);
  color: var(--color-accent); font-weight: 600;
}
.layer-content { padding: var(--space-6); }
```

---

## "Spot the Flaw" Challenge

Present a claim, headline, or interpretation of the paper's findings and ask the learner to identify what's wrong or misleading about it. Builds critical thinking.

**HTML:**
```html
<div class="flaw-challenge">
  <h3 class="flaw-header">Spot the Flaw</h3>
  <div class="flaw-claim">
    <span class="flaw-source">News headline:</span>
    <p class="flaw-text">"AI Can Now Perfectly Translate Any Language Thanks to New Attention Mechanism"</p>
  </div>
  <div class="flaw-options">
    <button class="flaw-option" data-correct="false" onclick="checkFlaw(this)">
      The headline is accurate — the paper shows perfect translation
    </button>
    <button class="flaw-option" data-correct="true" onclick="checkFlaw(this)">
      "Perfectly" is wrong — the model improved BLEU scores but translation is far from perfect
    </button>
    <button class="flaw-option" data-correct="false" onclick="checkFlaw(this)">
      The flaw is that attention isn't new — RNNs already used it
    </button>
  </div>
  <div class="flaw-explanation"></div>
</div>
```

**CSS:**
```css
.flaw-challenge {
  background: var(--color-warning-light);
  border: 2px solid var(--color-warning);
  border-radius: var(--radius-md);
  padding: var(--space-6); margin: var(--space-8) 0;
}
.flaw-header {
  font-family: var(--font-display); font-weight: 700;
  color: var(--color-warning);
}
.flaw-claim {
  background: var(--color-surface);
  border-radius: var(--radius-sm);
  padding: var(--space-4); margin: var(--space-4) 0;
}
.flaw-source {
  font-size: var(--text-xs); color: var(--color-text-muted);
  text-transform: uppercase;
}
.flaw-text {
  font-family: var(--font-display); font-size: var(--text-lg);
  font-weight: 600; font-style: italic;
}
```

**Rules:**
- Use real-world-style claims (news headlines, tweets, blog summaries)
- The flaw should be about misinterpreting or exaggerating the paper's findings
- Explanation should teach *why* the claim is wrong and what the paper actually shows
- Great for building "BS detector" skills

---

## Scenario Quiz

Present a realistic scenario where the learner must apply what they learned from the paper.

```html
<div class="scenario-quiz">
  <div class="scenario-setup">
    <span class="scenario-badge">SCENARIO</span>
    <p>You're a product manager at a startup building a chatbot. Your engineer says: "We should use the Transformer architecture from this paper instead of our current RNN-based model." Your CEO asks you: "What's the practical benefit?"</p>
  </div>
  <div class="scenario-options">
    <button class="scenario-option" data-correct="false" onclick="checkScenario(this)">
      "It's newer technology, so it must be better"
    </button>
    <button class="scenario-option" data-correct="true" onclick="checkScenario(this)">
      "It can process all words in parallel instead of one-by-one, so training is much faster and it handles long conversations better"
    </button>
    <button class="scenario-option" data-correct="false" onclick="checkScenario(this)">
      "It uses less memory because it doesn't need to remember previous words"
    </button>
  </div>
  <div class="scenario-feedback"></div>
</div>
```

---

## Callout Boxes

For transferable insights, important caveats, and "aha!" moments.

**HTML:**
```html
<!-- Insight callout (transferable thinking skill) -->
<div class="callout callout-insight">
  <div class="callout-icon">💡</div>
  <div class="callout-content">
    <strong>Transferable insight:</strong> When someone claims a model "understands" language, ask: what does it actually compute? The gap between human-like behavior and human-like understanding is where most AI hype lives.
  </div>
</div>

<!-- Caveat callout (important limitation) -->
<div class="callout callout-caveat">
  <div class="callout-icon">⚠️</div>
  <div class="callout-content">
    <strong>Important caveat:</strong> The paper tested on English-German and English-French. Whether attention works as well for languages with very different structures (like Japanese or Arabic) required further research.
  </div>
</div>

<!-- Context callout (historical/field context) -->
<div class="callout callout-context">
  <div class="callout-icon">📚</div>
  <div class="callout-content">
    <strong>Field context:</strong> In 2017, RNNs were the dominant approach for sequence tasks. Saying "we don't need RNNs at all" was a bold claim — like suggesting cars don't need engines.
  </div>
</div>
```

**CSS:**
```css
.callout {
  display: flex; gap: var(--space-4);
  padding: var(--space-5);
  border-radius: var(--radius-md);
  margin: var(--space-6) 0;
  border-left: 4px solid;
}
.callout-insight {
  background: var(--color-accent-light);
  border-color: var(--color-accent);
}
.callout-caveat {
  background: var(--color-warning-light);
  border-color: var(--color-warning);
}
.callout-context {
  background: var(--color-info-light);
  border-color: var(--color-info);
}
.callout-icon { font-size: 1.5rem; flex-shrink: 0; }
.callout-content { font-size: var(--text-sm); line-height: var(--leading-normal); }
```

---

## Concept/Finding Cards

For presenting multiple related concepts or findings as a visual grid instead of a bullet list.

**HTML:**
```html
<div class="concept-cards stagger-children">
  <div class="concept-card animate-in" style="--card-color: var(--color-concept-1)">
    <div class="card-icon">🔍</div>
    <h4 class="card-title">Self-Attention</h4>
    <p class="card-desc">Every word looks at every other word to decide what's important</p>
  </div>
  <div class="concept-card animate-in" style="--card-color: var(--color-concept-2)">
    <div class="card-icon">🔀</div>
    <h4 class="card-title">Multi-Head</h4>
    <p class="card-desc">Run attention 8 times in parallel, each looking for different patterns</p>
  </div>
  <div class="concept-card animate-in" style="--card-color: var(--color-concept-3)">
    <div class="card-icon">📍</div>
    <h4 class="card-title">Positional Encoding</h4>
    <p class="card-desc">Since there's no sequence, inject word order info using sine waves</p>
  </div>
</div>
```

**CSS:**
```css
.concept-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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
.concept-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
.card-icon { font-size: 1.5rem; margin-bottom: var(--space-2); }
.card-title {
  font-family: var(--font-display); font-weight: 600;
  font-size: var(--text-base); margin-bottom: var(--space-2);
}
.card-desc { font-size: var(--text-sm); color: var(--color-text-secondary); }
```

---

## Flow Diagrams

For showing causal chains, argument structures, or any directional process.

**HTML:**
```html
<div class="flow-diagram stagger-children">
  <div class="flow-step animate-in">
    <div class="flow-step-num">1</div>
    <div class="flow-step-content">
      <strong>Problem</strong>
      <p>RNNs process sequentially — slow and forgetful</p>
    </div>
  </div>
  <div class="flow-arrow animate-in">↓</div>
  <div class="flow-step animate-in">
    <div class="flow-step-num">2</div>
    <div class="flow-step-content">
      <strong>Hypothesis</strong>
      <p>Attention alone can replace recurrence entirely</p>
    </div>
  </div>
  <div class="flow-arrow animate-in">↓</div>
  <div class="flow-step animate-in">
    <div class="flow-step-num">3</div>
    <div class="flow-step-content">
      <strong>Evidence</strong>
      <p>New SOTA on translation benchmarks, 10× faster training</p>
    </div>
  </div>
</div>
```

**CSS:**
```css
.flow-diagram { display: flex; flex-direction: column; align-items: center; gap: var(--space-2); margin: var(--space-6) 0; }
.flow-step {
  display: flex; gap: var(--space-4); align-items: center;
  background: var(--color-surface); padding: var(--space-4) var(--space-5);
  border-radius: var(--radius-md); box-shadow: var(--shadow-sm);
  max-width: var(--content-width); width: 100%;
}
.flow-step-num {
  width: 32px; height: 32px; border-radius: 50%;
  background: var(--color-accent); color: white;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-display); font-weight: 700; flex-shrink: 0;
}
.flow-arrow { font-size: var(--text-xl); color: var(--color-accent); }
```

---

## Comparison Cards

Side-by-side comparison of approaches, methods, or before/after states. Great for showing what changed with this paper's contribution.

**HTML:**
```html
<div class="comparison">
  <div class="comparison-card before">
    <span class="comparison-badge">BEFORE THIS PAPER</span>
    <h4>RNN-based Translation</h4>
    <ul>
      <li>Process words one at a time</li>
      <li>Slow to train (sequential)</li>
      <li>Struggles with long sentences</li>
      <li>BLEU score: 25.8</li>
    </ul>
  </div>
  <div class="comparison-vs">vs</div>
  <div class="comparison-card after">
    <span class="comparison-badge">THIS PAPER</span>
    <h4>Transformer (Attention Only)</h4>
    <ul>
      <li>Process all words simultaneously</li>
      <li>10× faster training (parallel)</li>
      <li>Handles long-range dependencies</li>
      <li>BLEU score: 28.4</li>
    </ul>
  </div>
</div>
```

**CSS:**
```css
.comparison {
  display: grid; grid-template-columns: 1fr auto 1fr;
  gap: var(--space-4); align-items: stretch;
  margin: var(--space-8) 0;
}
.comparison-card {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: var(--space-5);
  box-shadow: var(--shadow-sm);
}
.comparison-card.before { border-top: 3px solid var(--color-text-muted); }
.comparison-card.after { border-top: 3px solid var(--color-accent); }
.comparison-badge {
  font-size: var(--text-xs); font-family: var(--font-mono);
  text-transform: uppercase; letter-spacing: 0.05em;
  color: var(--color-text-muted);
}
.comparison-vs {
  display: flex; align-items: center;
  font-family: var(--font-display); font-weight: 800;
  font-size: var(--text-2xl); color: var(--color-text-muted);
}
@media (max-width: 768px) {
  .comparison { grid-template-columns: 1fr; }
  .comparison-vs { justify-content: center; }
}
```

---

## Glossary Tooltips

Dashed-underline terms with hover/tap definitions. The learner should never have to Google a term.

**HTML:**
```html
<span class="glossary-term" data-definition="A score that measures how similar a machine translation is to a human translation. Higher is better. A BLEU score of 28.4 means the model's output overlaps ~28% with professional human translations.">
  BLEU score
</span>
```

**CSS:**
```css
.glossary-term {
  border-bottom: 2px dashed var(--color-accent-muted);
  cursor: pointer;
  position: relative;
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

**JS (position: fixed — prevents clipping):**
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

**Rules:**
- Use `position: fixed` with `getBoundingClientRect()` — NEVER `position: absolute` (clipping)
- Append to `document.body`, not inside the term element
- Tooltip every technical term, acronym, or domain-specific word on first use per module
- Definitions should help the learner USE the term, not just define it

---

## Figure Annotation Overlay

For annotating key figures or charts from the paper. Shows the figure with clickable hotspots that explain what to look at.

**HTML:**
```html
<div class="figure-annotated">
  <div class="figure-title">Figure 3 from the paper: Attention head visualization</div>
  <div class="figure-container">
    <!-- Recreated figure using HTML/CSS, or a description if image not available -->
    <div class="figure-recreation">
      <!-- Simplified recreation of the figure -->
    </div>
    <div class="figure-hotspot" style="left: 30%; top: 40%;" data-annotation="Notice how the word 'it' strongly attends to 'animal' — the model learned that 'it' refers to 'animal' without being explicitly taught grammar.">
      <div class="hotspot-dot"></div>
    </div>
    <div class="figure-hotspot" style="left: 70%; top: 20%;" data-annotation="The diagonal pattern shows each word paying some attention to itself — a sanity check that the model is working as expected.">
      <div class="hotspot-dot"></div>
    </div>
  </div>
  <div class="figure-annotation-display"></div>
</div>
```

**CSS:**
```css
.figure-annotated {
  margin: var(--space-8) 0;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--shadow-md);
}
.figure-title {
  font-size: var(--text-xs); color: var(--color-text-muted);
  text-transform: uppercase; letter-spacing: 0.05em;
  margin-bottom: var(--space-4);
}
.figure-container { position: relative; }
.figure-hotspot {
  position: absolute; transform: translate(-50%, -50%);
  cursor: pointer; z-index: 2;
}
.hotspot-dot {
  width: 24px; height: 24px; border-radius: 50%;
  background: var(--color-accent);
  border: 3px solid white;
  box-shadow: var(--shadow-md);
  animation: hotspotPulse 2s infinite;
}
@keyframes hotspotPulse {
  0%, 100% { box-shadow: var(--shadow-md), 0 0 0 0 rgba(42, 123, 155, 0.3); }
  50% { box-shadow: var(--shadow-md), 0 0 0 8px rgba(42, 123, 155, 0); }
}
.figure-annotation-display {
  margin-top: var(--space-4);
  padding: var(--space-4);
  background: var(--color-accent-light);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  display: none;
}
.figure-annotation-display.visible { display: block; }
```

---

## Evidence Strength Meter

Visual indicator of how strong the evidence is for a particular claim. Teaches the learner to evaluate evidence quality.

**HTML:**
```html
<div class="evidence-meter">
  <div class="evidence-claim">Claim: "Attention is all you need for sequence transduction"</div>
  <div class="evidence-bar">
    <div class="evidence-fill" style="width: 75%"></div>
    <div class="evidence-markers">
      <span style="left: 25%">Weak</span>
      <span style="left: 50%">Moderate</span>
      <span style="left: 75%">Strong</span>
      <span style="left: 95%">Definitive</span>
    </div>
  </div>
  <div class="evidence-details">
    <div class="evidence-for">
      <strong>Supporting:</strong> New SOTA on 2 translation benchmarks, faster training, successful on parsing task
    </div>
    <div class="evidence-against">
      <strong>Caveats:</strong> Only tested on translation + parsing, not all sequence tasks. "All you need" may overstate — later work showed some tasks still benefit from recurrence.
    </div>
  </div>
</div>
```

**CSS:**
```css
.evidence-meter {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: var(--space-5);
  margin: var(--space-6) 0;
  box-shadow: var(--shadow-sm);
}
.evidence-claim {
  font-family: var(--font-display); font-weight: 600;
  margin-bottom: var(--space-4);
}
.evidence-bar {
  position: relative; height: 12px;
  background: var(--color-border-light);
  border-radius: var(--radius-full);
  margin-bottom: var(--space-6);
}
.evidence-fill {
  height: 100%; border-radius: var(--radius-full);
  background: linear-gradient(90deg, var(--color-warning), var(--color-success));
  transition: width 1s var(--ease-out);
}
.evidence-markers {
  position: relative; margin-top: var(--space-2);
}
.evidence-markers span {
  position: absolute; transform: translateX(-50%);
  font-size: var(--text-xs); color: var(--color-text-muted);
}
.evidence-for, .evidence-against {
  font-size: var(--text-sm); margin-top: var(--space-3);
  padding: var(--space-3);
  border-radius: var(--radius-sm);
}
.evidence-for { background: var(--color-success-light); }
.evidence-against { background: var(--color-warning-light); }
```

---

## Numbered Step Cards

For breaking down a complex process into clear, numbered steps.

**HTML:**
```html
<div class="step-cards stagger-children">
  <div class="step-card animate-in">
    <div class="step-num">1</div>
    <div class="step-content">
      <h4>Embed the input</h4>
      <p>Convert each word into a vector of numbers that captures its meaning</p>
    </div>
  </div>
  <div class="step-card animate-in">
    <div class="step-num">2</div>
    <div class="step-content">
      <h4>Add position info</h4>
      <p>Since we process all words at once, we need to tell the model their order using sine waves</p>
    </div>
  </div>
  <div class="step-card animate-in">
    <div class="step-num">3</div>
    <div class="step-content">
      <h4>Run self-attention</h4>
      <p>Let every word "look at" every other word to figure out context</p>
    </div>
  </div>
</div>
```

**CSS:**
```css
.step-cards { display: flex; flex-direction: column; gap: var(--space-3); margin: var(--space-6) 0; }
.step-card {
  display: flex; gap: var(--space-4); align-items: flex-start;
  background: var(--color-surface);
  padding: var(--space-4) var(--space-5);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
}
.step-num {
  width: 36px; height: 36px; border-radius: 50%;
  background: var(--color-accent); color: white;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-display); font-weight: 700;
  font-size: var(--text-lg); flex-shrink: 0;
}
.step-content h4 {
  font-family: var(--font-display); font-weight: 600;
  margin-bottom: var(--space-1);
}
.step-content p { font-size: var(--text-sm); color: var(--color-text-secondary); }
```
