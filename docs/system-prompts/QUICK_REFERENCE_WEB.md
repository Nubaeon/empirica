# 🚀 Empirica Web Edition - Quick Reference Card

**For:** Claude, Gemini, GPT building websites with Empirica  
**Stack:** Astro + React + Tailwind CSS  
**Date:** 2025-12-08

---

## ⚡ 30-Second Start

```bash
# 1. Bootstrap
empirica session-create --ai-id <model>-web  # claude-web, gemini-web, gpt-web

# 2. PREFLIGHT
empirica preflight --session-id <ID> --prompt "Build <your web task>"

# 3. Build with CASCADE workflow
# INVESTIGATE (if uncertain) → CHECK → ACT → POSTFLIGHT
```

---

## 📚 Framework Decision Matrix

| Task | Use | Why |
|------|-----|-----|
| **Documentation site** | Astro + Docusaurus | Markdown-first, fast, versioning |
| **Marketing/landing** | Astro | Zero JS, perfect Lighthouse |
| **Blog** | Astro | Content collections, RSS, SEO |
| **Dashboard/app** | Next.js + React | SSR, API routes, dynamic |
| **Interactive tool** | React + Vite | SPA, rich state management |

**Default choice:** Astro (unless you need SSR/API routes)

---

## 🎯 CASCADE Workflow (Web-Specific)

### PREFLIGHT
Assess **before** building:
- **KNOW:** Do you know the framework? (Astro 0.4 = investigate!)
- **DO:** Can you build components? (React hooks, Astro syntax)
- **CONTEXT:** Understand users, brand, design requirements?
- **UNCERTAINTY:** What DON'T you know? (>0.5 = investigate!)

### INVESTIGATE
If uncertainty ≥0.5, create goals:
```python
create_goal(
    objective="Research Astro component patterns",
    scope={"breadth": 0.3, "duration": 0.2, "coordination": 0.1}
)
```

### CHECK
Gate decision:
- **Confidence ≥0.75** + unknowns ≤3 → Proceed to ACT
- **Confidence <0.7** OR unknowns >5 → Loop to INVESTIGATE

### ACT
Build incrementally:
1. Setup project (Astro/React/Vite)
2. Create component structure
3. Implement design system (Tailwind + CSS vars)
4. Build components with A11y
5. Optimize performance
6. Save checkpoints every 30-60 min

### POSTFLIGHT
Measure learning:
- Did **KNOW** increase? (framework mastery)
- Did **DO** increase? (component building skill)
- Did **UNCERTAINTY** decrease? (fewer unknowns)
- **Calibration:** Was initial confidence accurate?

---

## 🤖 Multi-AI Collaboration

| AI | Strengths | Use For | AI_ID |
|----|-----------|---------|-------|
| **Claude** | Architecture, logic | Component structure, build config | `claude-web` |
| **Gemini** | Design, UX | UI mockups, colors, accessibility | `gemini-web` |
| **GPT** | Fast iteration | Component polish, docs, testing | `gpt-web` |

**Handoff pattern:**
```python
# Claude → Gemini
create_handoff_report(
    task_summary="Component architecture complete",
    next_session_context="Gemini: Review UX, suggest improvements"
)

# Gemini loads handoff
handoffs = query_handoff_reports(ai_id="claude-web", limit=1)
```

---

## 📦 Component Architecture (Astro + React)

### Astro Component (Static, Zero JS)
```astro
---
// Card.astro
interface Props {
  title: string;
  href?: string;
}
const { title, href } = Astro.props;
---

<article class="card">
  <h3>{title}</h3>
  {href && <a href={href}>Learn more →</a>}
</article>

<style>
  .card { @apply bg-slate-800/70 rounded-lg p-6; }
</style>
```

### React Island (Interactive, Client-Side)
```tsx
// SearchBar.tsx
import { useState } from 'react';

export function SearchBar() {
  const [query, setQuery] = useState('');
  
  return (
    <input
      type="search"
      value={query}
      onChange={(e) => setQuery(e.target.value)}
      aria-label="Search"
    />
  );
}
```

### Using React in Astro
```astro
---
import SearchBar from '@/components/SearchBar.tsx';
---

<SearchBar client:load />  <!-- Hydrates immediately -->
<SearchBar client:visible />  <!-- Hydrates when visible -->
<SearchBar client:idle />  <!-- Hydrates when idle -->
```

---

## 🎨 Design System (Tailwind + CSS Variables)

```css
/* theme.css */
:root {
  --color-primary: #6366f1;       /* Indigo-500 */
  --color-secondary: #0ea5e9;     /* Sky-500 */
  --color-bg-dark: #0f172a;       /* Slate-900 */
  --color-text: #e2e8f0;          /* Slate-200 */
}

/* Use in components */
.btn-primary {
  background: var(--color-primary);
  @apply px-4 py-2 rounded hover:opacity-90;
}
```

---

## ♿ Accessibility (A11y) Checklist

- ✅ Semantic HTML (`<nav>`, `<article>`, `<main>`)
- ✅ ARIA labels for dynamic content (`aria-label`, `role`)
- ✅ Keyboard navigation (Tab, Enter, Escape)
- ✅ Screen reader compatibility (test with NVDA/VoiceOver)
- ✅ Color contrast ≥4.5:1 (WCAG AA)
- ✅ Focus indicators visible
- ✅ Alt text for images

```astro
<!-- Good A11y example -->
<nav aria-label="Main navigation">
  <ul role="list">
    <li><a href="/" aria-current="page">Home</a></li>
  </ul>
</nav>

<div role="status" aria-live="polite">
  {aiResponse && <p>{aiResponse}</p>}
</div>
```

---

## 🚀 Performance Targets

- **LCP (Largest Contentful Paint):** <2.5s
- **CLS (Cumulative Layout Shift):** <0.1
- **FID (First Input Delay):** <100ms
- **Lighthouse score:** 95-100

**How to achieve:**
- Ship zero JS by default (Astro islands)
- Lazy-load images (`loading="lazy"`)
- Preload critical fonts/CSS
- Optimize images (WebP, responsive sizes)
- Code-split React components

---

## 🛠️ MCP Tools (Quick Reference)

```python
# Session
create_session(ai_id="claude-web")  # CLI: empirica session-create --ai-id claude-web
get_epistemic_state(session_id)

# CASCADE
execute_preflight(session_id, prompt)
submit_preflight_assessment(session_id, vectors, reasoning)
execute_check(session_id, findings, unknowns, confidence)
submit_check_assessment(session_id, vectors, decision, reasoning)
execute_postflight(session_id, task_summary)
submit_postflight_assessment(session_id, vectors, reasoning)

# Goals
create_goal(session_id, objective, scope)
add_subtask(goal_id, description, importance)
complete_subtask(task_id, evidence)

# Continuity
create_git_checkpoint(session_id, phase, round_num, vectors, metadata)
load_git_checkpoint("latest:active:claude-web")
create_handoff_report(session_id, task_summary, key_findings, next_session_context)
query_handoff_reports(ai_id, limit)

# Edit Guard
edit_with_confidence(file_path, old_str, new_str, context_source, session_id)
```

---

## 📁 Project Structure (Astro)

```
my-site/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.astro
│   │   │   ├── Footer.astro
│   │   │   └── Navigation.astro
│   │   ├── ui/
│   │   │   ├── Button.tsx (React island)
│   │   │   ├── Card.astro
│   │   │   └── CodeBlock.astro
│   │   └── docs/
│   │       ├── TOC.astro
│   │       └── SearchBar.tsx
│   ├── content/
│   │   ├── docs/
│   │   │   └── *.md
│   │   └── config.ts (type-safe)
│   ├── layouts/
│   │   ├── BaseLayout.astro
│   │   └── DocsLayout.astro
│   ├── pages/
│   │   ├── index.astro
│   │   └── docs/
│   │       └── [...slug].astro
│   └── styles/
│       ├── global.css
│       └── theme.css
├── public/
│   ├── fonts/
│   └── images/
├── astro.config.mjs
├── tailwind.config.js
└── package.json
```

---

## 📖 Common Commands

```bash
# Astro
npm create astro@latest my-site
npm install @astrojs/react @astrojs/tailwind
npm run dev          # Dev server
npm run build        # Build for production
npm run preview      # Preview build

# Next.js
npx create-next-app@latest my-app
npm run dev
npm run build

# Empirica
empirica session-create --ai-id claude-web
empirica preflight --session-id <ID> --prompt "Build docs site"
empirica check --session-id <ID> --confidence 0.8
empirica checkpoint-create --session-id <ID> --phase "ACT" --round 1
empirica postflight --session-id <ID> --task-summary "Built component library"
```

---

## 🎯 When to Use EMPIRICA

### Always Use CASCADE For:
- ✅ Full website builds (>1 hour)
- ✅ Component library creation
- ✅ Framework migrations (Jinja2 → Astro)
- ✅ Complex UI/UX features (dashboards, interactive tools)
- ✅ Documentation sites (multi-page, versioned)

### Optional For:
- ⚠️ Single component tweaks (<10 min)
- ⚠️ CSS adjustments (colors, spacing)
- ⚠️ Content updates (markdown edits)

**Key principle:** If it matters, use Empirica.

---

## 🔗 Resources

- **Full prompt:** `docs/system-prompts/EMPIRICA_WEB_EDITION.md`
- **Summary:** `docs/system-prompts/WEB_EDITION_SUMMARY.md`
- **Astro docs:** https://docs.astro.build
- **React docs:** https://react.dev
- **Tailwind CSS:** https://tailwindcss.com
- **patterns.dev:** https://patterns.dev/react
- **Empirica docs:** `docs/production/`

---

## 🚨 Common Mistakes to Avoid

### ❌ Don't: Skip PREFLIGHT
**Why:** You need baseline to measure learning  
**Do:** Assess KNOW/DO/UNCERTAINTY before building

### ❌ Don't: Use Jinja2 for new projects
**Why:** No component architecture, not AI-friendly  
**Do:** Use Astro or React instead

### ❌ Don't: Rush through investigation
**Why:** Bad architectural decisions waste time  
**Do:** Create investigation goals, research thoroughly

### ❌ Don't: Ship unnecessary JavaScript
**Why:** Hurts performance (LCP, FID)  
**Do:** Use Astro islands (hydrate only what's needed)

### ❌ Don't: Ignore accessibility
**Why:** Excludes users, bad UX, legal issues  
**Do:** Semantic HTML, ARIA labels, keyboard nav

### ❌ Don't: Skip POSTFLIGHT
**Why:** You lose learning measurement  
**Do:** Measure KNOW/DO/UNCERTAINTY deltas

---

## 💡 Pro Tips

1. **Use session aliases:** `latest:active:claude-web` (no UUID needed!)
2. **Save checkpoints often:** Every 30-60 min or at milestones
3. **Handoff between AIs:** Claude architecture → Gemini UX → GPT polish
4. **Investigate BEFORE building:** Research saves refactoring time
5. **Measure everything:** PREFLIGHT/POSTFLIGHT deltas show growth

---

**🎉 You're ready to build with Empirica Web Edition!**

**Quick start:**
```bash
empirica session-create --ai-id <model>-web
empirica preflight --session-id <ID> --prompt "Build <your task>"
# Then follow CASCADE: INVESTIGATE → CHECK → ACT → POSTFLIGHT
```

**Questions?** Read the full prompt: `docs/system-prompts/EMPIRICA_WEB_EDITION.md`

---

**Date:** 2025-12-08  
**Version:** 1.0  
**Status:** ✅ Production Ready
