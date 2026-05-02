# Empirica Chat

> Single-instance collaborative epistemic workspace.
>
> **Status:** Spec (T33). Implementation pending.
> **Sister:** [`COCKPIT.md`](COCKPIT.md) (multi-instance orchestration — complementary, not replaced)
> **Related:** [`EWM.md`](EWM.md), [`EPISTEMIC_PROMPT_ENGINE.md`](EPISTEMIC_PROMPT_ENGINE.md),
>   ecodex translator + event tap (`ecodex/codex-rs/codex-empirica-translator/`)

---

## What it is

A focused single-instance Python Textual TUI (`empirica chat`) that hosts the
AI ↔ human collaborative loop. Both parties contribute to the epistemic
state — the chat renders the conversation **and** the epistemic
artifacts as first-class elements, not as buried tool-call output.

| Surface | Purpose |
|---|---|
| `empirica chat` (this spec) | Single-instance conversation + epistemic workspace |
| `empirica tui` ([COCKPIT.md](COCKPIT.md)) | Multi-instance orchestration view — sister tool |
| `ecodex` (codex's TUI) | Standard codex experience — full mode for power users |

These are complementary. Common pattern is to run `empirica chat` and
`empirica tui` in tmux panes side-by-side: chat for the active
conversation, cockpit for "what are my other agents doing." On a phone:
pick whichever fits the moment.

---

## Principle

**The epistemic state is the work.** A conversation that renders only
prose is incomplete — findings, decisions, unknowns, dead-ends, goals,
and transactions are not byproducts of the conversation, they *are* the
conversation. Render them as first-class turn elements with the same
weight as text.

Corollary: **the human is a peer in the epistemic loop, not an
audience.** The chat affords human participation in artifact creation
(👍 a finding to confirm it, 👎 to challenge, "tell me more" to deepen,
"resolve" to close an unknown). Both parties shape the epistemic map.

---

## Three autonomy modes

The chat renders differently based on the AI's current operating mode.
Mode is set per-session and surfaced as a header badge.

| Mode | Badge | Rendering |
|---|---|---|
| **Conversational** | `🤖 conversational` | Every AI turn is interactive. User sees each step. Default for exploration, design, learning. |
| **Multi-agentic loop** | `🌀 multi-agentic` | AI is in a cooperative loop with other agents. Chat shows loop progress against an epistemic map. User can intervene but doesn't drive each turn. |
| **Full earned autonomy** | `🦅 autonomous` | AI works against plan/transactions independently. Chat becomes ambient — surfaces only escalations, milestone artifacts, and human-required decisions. Foreground noise drops; epistemic delta foregrounds. |

Mode is a property of the empirica-autonomy integration layer (separate
spec), not of chat itself. Chat consumes the current mode via the same
`~/.empirica/` state files cockpit reads.

---

## Layout

Vertical Textual layout. Targets ~80×24 minimum, scales up. Phone
landscape works; phone portrait acceptable but optimized for tmux pane
or laptop terminal first (chat is a focused-attention surface, not a
glance-and-go like cockpit).

```
┌─ Header           (mode badge · model · instance label · clock)
│  Statusline       (k:.. c:.. conf:.. phase:noetic|praxic — ctx:N%)
│
│  Conversation     (scroll, takes most of the screen)
│    ├─ Turn (user) — plain
│    ├─ Turn (agent) — text + inline artifact cards
│    │   ┌─ Finding card    (impact, subject, confirm/reject)
│    │   ├─ Decision card   (rationale, reversibility, evidence links)
│    │   ├─ Unknown card    (resolve / convert-to-finding)
│    │   ├─ Goal card       (subtasks, completion %)
│    │   └─ Transaction card (PREFLIGHT/CHECK/POSTFLIGHT vectors)
│    └─ Tool call (collapsed by default — Ctrl-O to expand all)
│
│  Input            (multi-line, paste-friendly, autocomplete commands)
└─ Footer           (key bindings + active autonomy notice)
```

Tool calls and code diffs are **collapsed by default** in conversational
mode and hidden in autonomous mode. `Ctrl-O` reveals everything
(matches codex's existing convention).

---

## Conversation rendering — turn types

Every turn is one of:

| Type | Rendered as | Source |
|---|---|---|
| `user` | Plain text bubble (right-aligned or distinct background) | User input |
| `agent_text` | Plain text (left-aligned, agent style) | Translator event tap `text_delta` events accumulated → agent turn |
| `agent_reasoning` | Collapsed thinking-block (chevron to expand) | Translator `reasoning_delta` (Anthropic + future o-series providers) |
| `tool_call` | Collapsed strip (`▶ Read foo.py`) — expand to see full | App-server agent-loop notification |
| `tool_result` | Collapsed by default unless error — show inline if surfaces something user-relevant | App-server notification |
| `epistemic_action` | **First-class card** — see "Artifact cards" below | Empirica MCP / CLI traffic intercepted via translator event tap or app-server hook events |
| `system` | Italic muted text (compaction markers, mode transitions, sentinel pauses) | Various |

Each turn carries a stable `turn_id` so artifact cards can resolve into
the user's interactions without losing identity across re-renders.

---

## Artifact cards (the differentiator)

When the AI logs a finding, decision, unknown, mistake, dead-end,
assumption, goal, or transaction, the chat renders a **structured card
inline in the conversation flow**, not a wall of JSON in a tool-call
expand.

Pattern lifted directly from `empirica_workspace`'s
`CandenceChatScreen` + `IntelligencePanel` (see
`empirica_workspace/dashboard/CANDENCE_API.md`):

```
┌─ 🔎 Finding · impact 0.85 ──────────────────────────────────┐
│ codex-app-server WebSocket transport is multi-client +      │
│ JSON-RPC. Means Cockpit Option C is fully viable.           │
│                                                              │
│ subject: codex-app-server  · session 26942c05               │
│ [👍 confirm]  [👎 challenge]  [💬 discuss]  [📌 pin]          │
└──────────────────────────────────────────────────────────────┘
```

Per-artifact-type quick actions:

| Artifact | Actions |
|---|---|
| `finding` | confirm · challenge · discuss · pin |
| `decision` | acknowledge · reverse · discuss · cite-as-precedent |
| `unknown` | resolve (with finding) · escalate · discuss · de-prioritize |
| `mistake` | acknowledge · add-prevention · discuss |
| `dead_end` | acknowledge · discuss |
| `assumption` | confirm (→ finding) · falsify (→ decision) · discuss |
| `goal` | view-subtasks · complete · split · re-scope |
| `transaction` | view-vectors · view-deltas · view-grounded-calibration |
| `source` | open-link · view-citations · discuss |

Action invocations either:
1. **Direct CLI write** — clear cases like `confirm finding` →
   `empirica finding-log` with same content + link as confirmed
2. **Send to AI via chat** — like `discuss` → injects a system message
   into the next turn ("user discusses finding X: ...")
3. **Open modal** — like `view-vectors` for a transaction

The card is the **action surface**, not just a render. This is what
makes the chat a *workspace* and not a transcript.

---

## Knowledge graph linkage

Every artifact card carries its UUID. Clicking a card opens a side
panel (or modal in narrow layouts) showing:

- The artifact's full content (untruncated)
- Edges into/out of the artifact (evidence, caused-by, prevents,
  resolves, sourced-from, attached-to)
- Related artifacts via Qdrant semantic search
- Related goals (where applicable)
- Related sources

This is the **knowledge graph spelunking** view — the chat is the
read/write surface; the side panel is the navigate surface. Same data
as `empirica project-search` + `empirica project-bootstrap`, rendered
for direct interaction.

Pattern parallels Candence's "click card → discuss with EPE" flow but
generalized to all artifact types.

---

## Statusline integration

The header includes a 1-line condensed statusline. Pressing `s` (or
clicking it) expands the full statusline modes from
`statusline_empirica.py` (basic | default | learning | full):

```
┌─ Statusline ─────────────────────────────────────────────────────┐
│ Mode: [basic] [default*] [learning] [full]                        │
│                                                                   │
│ Phase: 🟡 praxic     · transaction 944a20f2 · age 4m              │
│ Vectors:                                                          │
│   know: ████████░░ 0.85    uncertainty: ██░░░░░░░░ 0.18           │
│   context: █████████░ 0.92   completion: ███░░░░░░░ 0.30          │
│   ...                                                             │
│ Open: 3 goals (1 in-scope) · 2 unknowns (1 blocking)              │
│ Calibration trajectory: ↗ Brier improving (0.142 → 0.115)         │
└───────────────────────────────────────────────────────────────────┘
```

Renderer is the same `format_vectors_compact` from
`empirica.core.signaling` plus the count queries from
`statusline_empirica.py:get_open_counts`. Cockpit shows a 1-line
version; chat shows full when expanded. **Same renderer, different
fidelity** — no duplication.

---

## Data flow / subscriptions

Chat subscribes to **two streams** (per the architecture decided in T29 + T30):

```
                 ┌───────────────────────────────┐
                 │  empirica chat (Python+Textual)│
                 │  ┌────────────────────────────┐│
                 │  │ Turn aggregator            ││
                 │  │ (merges both streams into  ││
                 │  │  ordered turn timeline)    ││
                 │  └─────▲──────────▲───────────┘│
                 └────────┼──────────┼────────────┘
                          │          │
       ┌──────────────────┘          └──────────────────────┐
       │                                                    │
┌──────▼─────────────────────┐         ┌────────────────────▼──────────┐
│ codex-app-server           │         │ ecodex translator event tap   │
│ ws://localhost:NNNN        │         │ ~/.empirica/translator-events │
│ JSON-RPC (ClientRequest /  │         │   .jsonl  (tail -F)           │
│ ServerNotification)        │         │                               │
│ → agent-loop semantics:    │         │ → raw model events:           │
│   user prompts in,         │         │   text_delta, tool_call_delta,│
│   tool_call notifications, │         │   reasoning_delta, completed, │
│   thread state changes     │         │   request_started/completed   │
└──────┬─────────────────────┘         └────────────────────┬──────────┘
       │                                                    │
       └────────► codex agent loop ◄────► provider (DS/Q/G/K/Anth)
                  ▲
                  │ (translator interposes for chat-completions providers)
```

**App-server stream** = "what the agent loop is doing." Authoritative
for: turn boundaries, tool calls, thread state, mode transitions,
epistemic actions emitted by the empirica plugin's hook handlers.

**Translator stream** = "what the model is producing." Authoritative
for: token-level deltas, latency, finish reasons, raw error classes.

Chat aggregates both into the turn timeline. The two streams arrive
out of order; chat reconciles by matching `request_id` (translator) ↔
`turn_id` (app-server) — the empirica plugin's hook captures both at
turn boundary and writes the mapping to a session file.

---

## State files

All under `~/.empirica/`. Chat reads (mostly) and writes only its own
session-scoped files.

| File | Owner | Purpose |
|---|---|---|
| `chat_sessions/{session_id}.jsonl` | chat | Full turn history (append-only). One JSON line per turn (or sub-turn). Replayable. |
| `chat_layout_{session_id}.json` | chat | Layout state — collapsed/expanded artifact cards, side panel state |
| `chat_pinned_{session_id}.json` | chat | User-pinned artifacts for quick access |
| `instance_projects/{instance_id}.json` | session-init hook | (read) project lookup |
| `active_transaction_{instance_id}.json` | workflow_commands | (read) current transaction for statusline |
| `hook_counters_{instance_id}.json` | hooks | (read) phase derivation |
| `translator_request_to_turn_{session_id}.json` | empirica plugin | (read) request_id ↔ turn_id mapping for stream reconciliation |

`chat_sessions/*.jsonl` is the source of truth for replay + analysis.
Chat is reconstructable purely from this file. Layout/pinned files are
ephemeral UX state and can be deleted without losing the conversation.

---

## Subscriptions to the existing primitives

Don't reinvent — **subscribe**. Each primitive already exists in
empirica core; chat is a renderer + interaction surface for them.

| Primitive | Source | Used for |
|---|---|---|
| `aggregate_all()` | `empirica.core.cockpit.instance_state` | Header instance label, project context |
| `statusline_summary()` + `format_vectors_compact()` | `empirica.core.cockpit` + `empirica.core.signaling` | Statusline header + expanded view |
| `get_open_counts()` | `~/.claude/plugins/local/empirica/scripts/statusline_empirica.py` (extract to `empirica.core.statusline`) | Goals/unknowns counts in statusline |
| `EpistemicPromptEngine` | `empirica_workspace.engine` | (Optional) for "discuss finding X" flow if available |
| `SessionDatabase` | `empirica.data.session_database` | Artifact lookup for card content + edge resolution |
| Sentinel pause/loops/listeners | `empirica.core.cockpit.*` | (Optional) chat may surface that the instance is paused |

The CLI subprocess pattern is ALSO available: chat can shell out to
`empirica finding-log`, `empirica unknown-resolve`, etc. for action
invocations. Subprocess is cheaper to maintain than direct module
imports — no internal API churn risk.

---

## Wiring summary (planned files)

```
empirica/cli/parsers/chat_parsers.py           # `empirica chat` argparse
empirica/cli/command_handlers/chat_commands.py # handler dispatching to TUI
empirica/cli/tui/chat_app.py                   # Textual app entry
empirica/cli/tui/chat/                         # widget package
    __init__.py
    conversation.py     # ConversationScroll widget — turn list
    turn.py             # Turn widgets (UserTurn, AgentTurn, SystemTurn)
    artifact_card.py    # ArtifactCard with type-specific actions
    statusline.py       # Header statusline (delegates to core renderer)
    side_panel.py       # Knowledge-graph side panel
    input.py            # Multi-line input with command autocomplete
    aggregator.py       # Two-stream merger (app-server + translator)
empirica/core/chat/                            # business logic
    __init__.py
    session.py          # ChatSession state + jsonl persistence
    appserver_client.py # Python websockets + JSON-RPC client
    tap_subscriber.py   # tail -F on translator-events.jsonl
    actions.py          # CLI invocation for artifact actions
empirica/core/statusline.py                    # extracted from CC plugin
                                                # script for shared use
```

Estimated: ~1200 LOC chat package + ~200 LOC statusline extraction +
~150 LOC tests. Total fresh code ~1500 LOC. Reuses existing cockpit
core (~100KB) + statusline renderer + signaling module + session DB.

---

## Bindings

| Key | Action |
|---|---|
| `Enter` | Send input (Shift+Enter for newline) |
| `Ctrl-O` | Toggle full-stream view (reveal all tool calls + diffs) |
| `Ctrl-K` | Quick artifact search modal |
| `Ctrl-G` | Knowledge-graph side panel toggle |
| `s` | Expand/collapse statusline |
| `m` | Cycle autonomy mode (only available if user has authority) |
| `r` | Refresh statusline + counts |
| `?` | Help overlay |
| `q` | Quit (confirm if mid-stream) |

Card-specific actions are buttons inside the card body — keyboard
focus walks card → button → next card.

---

## What's deliberately out of scope

Same discipline as cockpit — write a separate proposal first.

- **Multi-instance chat** — chat is single-instance by design; multi-
  instance orchestration is cockpit's job. If you want to chat with
  agent A while observing agents B/C, run cockpit alongside.
- **Voice / audio I/O** — text-first. Voice integration belongs in
  `empirica voice` skill (separate).
- **Embedded code editing** — chat is a workspace surface, not an
  editor. Edits go through the AI; for direct edits use `$EDITOR` or
  the codex TUI.
- **Knowledge graph EDITING via chat UI** — read/navigate yes, edit
  no. Artifact creation happens through AI tool calls or CLI.
  Editing-via-chat-UI invites entropy.
- **Ambassador / external agent dispatch** — that's the
  `AMBASSADOR_ARCHITECTURE.md` territory; chat may surface
  ambassadorial events but doesn't drive them.
- **Web UI / Chrome panel** — terminal first. JSON schemas in
  `chat_sessions/*.jsonl` make a future web renderer trivial; build
  that proposal separately when the watch-recipe analog ("read the
  jsonl file in your browser") surfaces ≥3 documented gaps from real
  use.

---

## Build phases

Sized for incremental shipping. Each phase ends with a working binary
+ tests + commit.

| Phase | Deliverable | LOC est. |
|---|---|---|
| **0** | Spec (this doc) + `empirica chat --help` skeleton subcommand | ~50 |
| **1** | Conversation rendering: ChatSession state + jsonl persistence + UserTurn/AgentTurn widgets + Input widget + manual feed via CLI flag (`--feed sample.jsonl`) | ~400 |
| **2** | App-server WebSocket client + bidirectional flow (user input → agent loop → agent text rendered) | ~250 |
| **3** | Translator event tap subscriber + stream reconciliation (request_id ↔ turn_id) | ~200 |
| **4** | Artifact cards (Finding, Decision, Unknown first; rest follow) + actions (CLI subprocess) | ~300 |
| **5** | Knowledge graph side panel + Qdrant lookups | ~150 |
| **6** | Statusline integration + autonomy mode badge + bindings | ~150 |
| **7** | Replay mode (open old session jsonl) + tests | ~150 |

Total ~1650 LOC. Phase 1 is buildable standalone (no app-server
dependency) — useful for reviewing the conversation render UX before
wiring the rest.

---

## Prior art credits

Lifting design patterns from:

- **`empirica_workspace.dashboard.CandenceChatScreen`** — card-as-chat-
  element with Authorize/Queue/Deny actions, lifecycle states, worker-
  thread async generation, message bubbling. Direct inspiration for
  artifact-card pattern.
- **`empirica_workspace.dashboard.IntelligencePanel`** — sidebar
  showing predictions/gaps/drafts/activity/media. Direct inspiration
  for knowledge-graph side panel.
- **`empirica.cli.tui.cockpit_app`** — Textual app structure, bindings
  pattern, refresh loop. Sister tool by design.
- **Toad (Will McGugan, Textual creator, private dev)** —
  architectural validation: Python+Textual front-end + JSON-protocol
  back-end subprocess. Confirmed our codex-app-server design is sound.
- **Elia (`darrenburns/elia`, Apache-2.0)** — keyboard-centric UX
  idioms, scroll patterns. Design reference, not code base.
- **GPTUI (`happyapplehorse/gptui`)** — multi-AI conversation
  rendering for the multi-agentic-loop autonomy mode.

No code lifted from any of the above. Patterns + UX decisions only.
The artifact-card flow is the genuinely new piece — Candence does it
for predictions, we generalize to all eight Empirica artifact types
plus goals + transactions.
