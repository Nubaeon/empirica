# The Empirica Ecosystem — How Everything Connects

**Date:** 2026-04-23
**For:** Philipp (overview), investors (architecture), new team members (onboarding), partners (integration points)

---

## The Stack at a Glance

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER INTERFACES                              │
│                                                                  │
│  📱 Phone (ntfy)    💻 Extension (Chrome)    ⌨️ CLI (Claude Code) │
│  └─ notifications   └─ preview + paste       └─ development      │
│  └─ ✅🔄❌ buttons  └─ goal sidebar          └─ epistemic tx     │
│                      └─ engagement dash                          │
├──────────────────────────────────────────────────────────────────┤
│                     PROTOCOL LAYER                               │
│                                                                  │
│  ENP (Epistemic Network Protocol)                                │
│  └─ ntfy: real-time signals (pub/sub, phone + desktop)          │
│  └─ git notes: permanent knowledge (signed, versioned)          │
│  └─ Universal Governance: ✅ Accept | 🔄 Reclassify | ❌ Archive │
├──────────────────────────────────────────────────────────────────┤
│                     INTELLIGENCE LAYER                           │
│                                                                  │
│  Cortex (commercial)                                             │
│  └─ Qdrant: semantic search across all artifacts                │
│  └─ Prediction engine: pre-loads context for next session       │
│  └─ L0-L5 composable lessons: knowledge that compounds          │
│  └─ Bus: dispatches events between AI instances                 │
│  └─ Multi-tenant: org/user scoping                              │
├──────────────────────────────────────────────────────────────────┤
│                     PRODUCT LAYER                                │
│                                                                  │
│  Outreach          Autonomy           Epistemic Candor           │
│  └─ prosodic voice └─ earned trust    └─ claim-level gating     │
│  └─ platform adapt └─ graduated       └─ domain risk profiles   │
│  └─ engagement loop  sentinel         └─ PROCEED/HEDGE/HALT    │
│  └─ Zernio dispatch└─ multi-backend   └─ audit trail            │
│                    └─ training data                              │
├──────────────────────────────────────────────────────────────────┤
│                     MEASUREMENT LAYER                            │
│                                                                  │
│  Empirica Core (MIT)                                             │
│  └─ 13 epistemic vectors                                        │
│  └─ Brier-scored dual calibration                               │
│  └─ Sentinel gating (noetic → praxic)                           │
│  └─ 4-layer persistence (SQLite, git notes, Qdrant, auto-memory)│
│  └─ Sycophancy + confabulation detection                        │
│  └─ Transaction lifecycle (PREFLIGHT → CHECK → POSTFLIGHT)      │
├──────────────────────────────────────────────────────────────────┤
│                     RENDERING                                    │
│                                                                  │
│  mdview                                                          │
│  └─ Markdown → HTML with ASCII art diagram rendering            │
│  └─ DiagramSpec → SVG conversion                                │
│  └─ Article preview in extension                                │
│  └─ Calibration report visualization                            │
└──────────────────────────────────────────────────────────────────┘
```

---

## Each Product — What It Does and How It Connects

### Empirica Core (MIT)

**What:** The measurement infrastructure. Everything else builds on this.

**Repo:** `empirica` | **License:** MIT | **Status:** Mature (1,944 commits)

| Component | What It Does | Connected To |
|-----------|-------------|-------------|
| 13 epistemic vectors | Measure AI knowledge state per transaction | Cortex (stores), Autonomy (trust input), Candor (claim confidence) |
| Sentinel | Gates praxic actions on demonstrated knowledge | All products (enforces discipline) |
| Dual calibration | Compares self-assessment vs deterministic evidence | Cortex (stores calibration history), ENP (convergence data) |
| Transaction lifecycle | PREFLIGHT → CHECK → POSTFLIGHT | All products (measurement wrapper) |
| 4-layer persistence | SQLite + git notes + Qdrant + auto-memory | Cortex (Qdrant shared), ENP (git notes = transport) |
| Sycophancy/confabulation detection | Flags when AI agrees without grounding | Candor (claim-level), Outreach (voice quality) |

**The foundation rule:** If it's not measured by Core, it doesn't exist in the ecosystem.

---

### Epistemic Cortex (Commercial)

**What:** The intelligence layer. Stores, serves, and compounds knowledge.

**Repo:** `empirica-cortex` | **Status:** Live (cortex.getempirica.com)

| Component | What It Does | Connected To |
|-----------|-------------|-------------|
| Qdrant collections | Semantic search across findings, decisions, unknowns, goals, lessons | Core (artifact source), Outreach (voice samples), ENP (pattern search) |
| Prediction engine | Pre-loads context for next session based on patterns | Core (calibration data), Extension (proactive suggestions) |
| L0-L5 composable lessons | Knowledge that abstracts from personal → project → domain → cross-org → network | ENP (sharing transport), ECO (governs visibility) |
| MCP bus | Dispatches events between Claude instances | ENP (Accept/Archive callbacks), Outreach (publish pipeline), Autonomy (task dispatch) |
| Multi-tenant | Org/user scoping with API keys | All products (data isolation) |
| Email ingestion | IMAP + LLM classifier for incoming knowledge | Outreach (audience signals) |
| Session init | Loads user context on every new session | Extension (auto-loads voice profile), Core (calibration history) |

**The intelligence rule:** If it's not in Cortex, the AI can't find it next session.

---

### Empirica Outreach (Commercial)

**What:** Content intelligence. Voice-aware multi-platform publishing.

**Repo:** `empirica-outreach` | **Status:** Shipped (500+ tests)

| Component | What It Does | Connected To |
|-----------|-------------|-------------|
| Prosodic memory | Voice modeling: creator profile + 569 samples across 3 registers | Cortex (Qdrant storage), Drafter (voice injection), ENP (voice YAML export) |
| Platform configs | 10 platform YAML files with cultural norms, limits, tone | Drafter (adaptation rules), ENP (platform-specific actions) |
| adapt_for_platforms() | One source → N platform-adapted versions via Ollama | ENP (Accept triggers), Extension (preview panel), Zernio (dispatch) |
| Engagement analyzer | Detects patterns in what content performs | Prosodic memory (feedback loop), Cortex (findings) |
| Drafter agent | Generates content with 3-layer brief injection | Core (epistemic transaction), Cortex (voice context) |
| Scout agent | Detects outreach opportunities in platform feeds | Core (epistemic measurement), Outreach DB (opportunities) |
| Obsei bridge | Multi-platform listening (Reddit, Twitter) | Prosodic memory (audience voice ingestion) |
| getLate/Zernio bridge | Multi-channel publishing dispatch | ENP (Accept pipeline), Platform configs (adaptation) |

**The outreach rule:** Every piece of content sounds like you, adapted for where it's going, informed by what worked before.

---

### Empirica Autonomy (BSL)

**What:** Earned autonomy for AI agents. Trust through calibration.

**Repo:** `empirica-autonomy` | **Status:** Alpha (Phase 2, 83%)

| Component | What It Does | Connected To |
|-----------|-------------|-------------|
| Graduated Sentinel | CONTROLLER → OBSERVER → ADVISORY → AUTONOMOUS | Core (calibration input), ECO (trust management), ENP (Universal Governance Pattern) |
| Trust Calculator | 40% calibration + 40% suggestions + 20% mistakes | Core (Brier scores), Cortex (history) |
| Orchestrator | Polling loop, task dispatch, state machine | Cortex (task source), Core (epistemic transactions per task) |
| Training collector | JSONL training data from measured agent runs | Core (vectors), Cortex (lessons) |
| Grounded verifier | Objective evidence collection post-execution | Core (dual calibration), Cortex (calibration history) |
| Multi-backend runners | Claude Code + Ollama (+ Gemini, Codex planned) | ENP (model-agnostic instruction bus) |

**The autonomy rule:** Trust is earned through demonstrated calibration, never granted by configuration.

---

### Epistemic Candor (MIT)

**What:** Claim-level confabulation gating.

**Repo:** `epistemic-candor` | **Status:** Alpha (v0.1.0)

| Component | What It Does | Connected To |
|-----------|-------------|-------------|
| Claim extraction | Identifies individual factual claims in AI output | Core (sycophancy detection), Outreach (content quality) |
| Per-claim gating | PROCEED / HEDGE / HALT per claim based on confidence | ENP (Universal Governance Pattern — same three states) |
| Domain risk profiles | Legal, medical, financial, technical, academic | Cortex (domain patterns), ECO (domain-specific rules) |
| Calibration tracking | Per-claim accuracy over time | Core (Brier scoring), Cortex (calibration history) |
| MCP server | Claude Desktop/CLI integration | Cortex (session context) |

**The candor rule:** Every claim carries its confidence. High-risk claims are gated before reaching the user.

---

### empirica-extension (Chrome)

**What:** Desktop face of the epistemic network.

**Repo:** `empirica-extension` | **Status:** In development

| Component | What It Does | Connected To |
|-----------|-------------|-------------|
| ntfy SSE subscription | Real-time notifications in browser | ENP (same topics as phone) |
| Goal management sidebar | Active goals + pending notifications | Cortex (goal queries), Core (transaction state) |
| Context-aware paste | Detects platform, offers adapted content | Outreach (adapt_for_platforms output), ENP (Accept pipeline) |
| Pre-publish preview | Renders adapted content before publishing | mdview (rendering), Outreach (platform versions) |
| Engagement dashboard | Badge showing content performance | Outreach (engagement analyzer), Cortex (patterns) |
| Artifact extraction | Scrape + ingest any webpage | Cortex (knowledge ingestion) |

**The extension rule:** Whatever the phone can do, the desktop does with richer context.

---

### mdview

**What:** Markdown rendering with ASCII art diagram support.

| Component | What It Does | Connected To |
|-----------|-------------|-------------|
| Markdown → HTML | Themed rendering with syntax highlighting | Extension (article preview), Outreach (content rendering) |
| DiagramSpec → SVG | Converts ASCII art blocks to vector graphics | Extension (diagram preview), Outreach (cover images) |
| CLI rendering | Render markdown files from terminal | Core (calibration reports), Outreach (article drafts) |

**The rendering rule:** If it's markdown, mdview makes it visual.

---

## How They Connect for Notifications + Epistemic Management

### The Notification Flow

```
Something changes (git push, goal completed, calibration alert)
        ↓
ENP watcher detects (cron, 5 min)
        ↓
Ollama generates TL;DR (qwen3.5:4b, 2s)
        ↓
ntfy pushes to phone + extension:
  Body: TL;DR (tap to view full content)
  ✅ Accept | 🔄 Reclassify | ❌ Archive
        ↓
User taps button
        ↓
Cortex /enp/ack receives callback
        ↓
Cortex dispatches bus event
        ↓
Active Claude session (CLI or Desktop) picks up
        ↓
Claude executes based on action:
  Accept → adapt_for_platforms → Zernio/ntfy
  Reclassify → AI re-evaluates → follow-up notification
  Archive → AI classifies → routes to correct folder
        ↓
Decision logged as epistemic artifact
        ↓
Calibration data feeds back (convergence)
```

### The Epistemic Management Flow

```
AI works on a task
        ↓
Core measures: 13 vectors at PREFLIGHT
        ↓
Sentinel gates: investigation before action
        ↓
AI investigates → logs findings, unknowns, dead-ends
        ↓
CHECK: readiness assessed
        ↓
AI acts → code, content, decisions
        ↓
POSTFLIGHT: compare self-assessment vs evidence
        ↓
Cortex stores: calibration data, artifacts, patterns
        ↓
Prediction engine: pre-loads for next session
        ↓
Composable lessons: patterns abstract L0 → L5
        ↓
ECO governs: what crosses boundaries, who sees what
        ↓
ENP transports: notifications, lessons, skills across network
        ↓
Autonomy adjusts: trust level earned from calibration
        ↓
Next task starts better calibrated
```

### The Publishing Flow

```
Content drafted (any Claude, any session)
        ↓
Core measures the drafting transaction
        ↓
ENP detects new content → TL;DR → notification
        ↓
ECO reviews: ✅ Accept | 🔄 Reclassify | ❌ Archive
        ↓
Accept → Cortex bus → Claude session
        ↓
Outreach: adapt_for_platforms (prosodic voice + platform config)
        ↓
Extension: preview adapted versions (mdview rendering)
        ↓
Zernio: dispatch to connected platforms
        ↓
Engagement data returns → Outreach analyzer
        ↓
Prosodic memory updated → next draft is better
        ↓
Cortex stores patterns → network intelligence compounds
```

---

## The Universal Governance Pattern Across Products

Every product implements the same three-state model:

| Product | ✅ Accept (Proceed) | 🔄 Reclassify (Ask) | ❌ Archive (Deny) |
|---------|--------------------|--------------------|------------------|
| **ENP** | Publish content | Re-evaluate classification | Route to storage |
| **Autonomy** | AI acts (ADVISORY) | AI proposes (OBSERVER) | AI reads only (CONTROLLER) |
| **ECO** | Allow sharing | Review context | Block sharing |
| **Candor** | State claim directly | Hedge with caveat | Halt — verify first |
| **Sentinel** | Proceed to praxic | Keep investigating | Block action |

One pattern. Three states. Every product. Convergence in every domain.

---

## Product Dependencies

```
empirica-core (MIT) ← foundation, everything depends on this
    ↓
epistemic-cortex (commercial) ← intelligence, most products connect here
    ↓
┌───────────────┬──────────────────┬──────────────────┐
↓               ↓                  ↓                  ↓
outreach        autonomy           candor             extension
(content)       (earned trust)     (claim gating)     (desktop UI)
    ↓                                                     ↓
zernio/getLate                                        mdview
(multi-channel)                                    (rendering)
```

**Build order:** Core → Cortex → {Outreach, Autonomy, Candor, Extension} in parallel → integrate via ENP + bus

**Deploy order:** Core (pip install) → Cortex (Hetzner) → Products (per client need)

---

## Roles in the Ecosystem

| Role | What They Touch | Primary Interface |
|------|----------------|-------------------|
| **Developer** | Core + Cortex | CLI (Claude Code) |
| **Content creator** | Outreach + Extension | Extension + phone |
| **ECO** | Cortex + ENP + all products | Phone (ntfy) + dashboard |
| **Client admin** | Cortex (tenant) + Autonomy (trust) | Dashboard |
| **End user** | Candor (transparent AI) | Desktop (Claude Desktop) |

---

*All roads lead back to Empirica. Plugins in, knowledge out. Measured, governed, earned.*
