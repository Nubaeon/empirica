# Empirica Chat — Overnight Autonomous Build Plan (FINAL)

> **Status:** FINAL. David's framing: "I don't need you to compress or
> go fast — we do things right, just expand it. If you're still going
> when I wake up, that will be a result."
>
> **Mode:** Autonomous after approval — full Sentinel discipline, no
> shortcuts. Going long, not fast.
>
> **Branch:** `develop` (empirica), `build/v1-plugin` (ecodex).

---

## The framing

I am NOT optimizing for time. I AM optimizing for:
1. Right code (tested, committed, spec'd)
2. Maximum scope coverage in priority order
3. Honest reporting

Time estimates are removed because they're poor models for my pace. The
plan ships in priority order. Whatever I'm working on when David wakes
up = where I got. Skip-on-2-fail per phase still applies.

---

## Per-phase discipline (every phase)

Five acceptance criteria:
1. **Code committed** to `develop` (empirica) or `build/v1-plugin` (ecodex)
2. **Imports verify** (programmatic `python3 -c "import …"`)
3. **Programmatic smoke** of new behavior (live verification where possible)
4. **Pytest test added** (not just smoke — actual test cases for the new module)
5. **Spec entry** in CHAT.md updated to "shipped" with commit hash + LOC

Artifact discipline:
- 1+ findings logged per phase
- decisions for any non-trivial design call
- mistakes logged immediately with prevention rules
- assumptions captured for unverified bets
- dead-ends logged when an approach is abandoned

Sentinel discipline:
- Every phase = full PREFLIGHT → CHECK → work → commit → POSTFLIGHT cycle
- No `--no-verify`, no sentinel pause, no shortcuts
- 2-fail skip rule: if a phase fails its build/test cycle twice, skip
  and document why

---

## What's currently shipped (baseline)

empirica chat v0 — all on `develop`, head commit `05441794d`:

| Phase | Status | Commit | LOC |
|---|---|---|---|
| 0 | spec + skeleton | `7fb414b53` | ~50 |
| 1 | conversation render + jsonl persistence | `d50254bfb` | ~400 |
| 2a | direct translator dispatch | `77d7ef164` | ~250 |
| 4 | artifact cards (v0 demo) | `0f6604456` | ~440 |
| 6 | basic statusline (4 modes) | `7e8920352` | ~180 |
| T40 | multi-provider selector | `1cae6324c` | ~520 |

ecodex translator — `build/v1-plugin`:
- 21/21 unit tests, mock smoke test, live-tested against DeepSeek + empirica-server.

---

## Priority-ordered phase list

Each phase ships when its 5 acceptance criteria pass. I work down the
list until I'm out of time, context, or hit a real blocker requiring
David's input.

### TIER 1 — Foundational (do first; everything else builds on them)

1. **Phase 8** — system prompt + epistemic discipline integration (`b910b609`)
   - `empirica/core/chat/system_prompt.py` with autonomy-mode-aware rendering
   - Wire into ChatApp.on_mount as turn 0
   - Tests: prompt rendering for all 3 autonomy modes
2. **Phase 6b** — full CC statusline extraction (`9c7e6abd`)
   - Extract `statusline_empirica.py` → `empirica/core/statusline/`
   - Drop context-window field
   - Cockpit also adopts the shared module
   - Tests: renderer modes + edge cases
3. **Phase 16** — slash command refinement (`0c36aef5`)
   - `/plan` shows open goals + transactions
   - `/autonomy MODE` switches modes
   - `/help` minimal default; `/help debug` shows everything
   - Tests: slash parsing + dispatch

### TIER 2 — Visible signals (the conversational-layer differentiators)

4. **Phase 13** — phase indicator badge (🔍 INVESTIGATE / ▶ ACT) (`3d82a10a`)
5. **Phase 14** — intuition vs search transparency badge (`9c11964c`)
6. **Phase 15** — natural-language workflow narration (`3d7303af`)
   - `empirica/core/chat/narration.py`
   - Subscribes to translator event tap + local empirica session DB
   - Renders as muted SystemTurn
   - Golden-snapshot tests for the per-event verbiage

### TIER 3 — Convenience features

7. **Phase 12** — arrow-key model selector (`30fb4a25`)
8. **Phase 4b** — wire artifact-card buttons → real CLI invocations
9. **Phase 9** — token tracking + per-model context window (`544a6000`)
   - tiktoken (OpenAI family) + transformers AutoTokenizer (HF) + char/4 fallback chain
   - Per-model max-token registry
   - Token bar UI strip
   - Auto-warn at 80%, auto-suggest /compact at 90%
10. **Phase 10** — pre/post compact lifecycle hooks (`ed7bdef6`)
    - Save/restore via `~/.empirica/chat_breadcrumbs/{session_id}.yaml`
    - `/compact` slash command + auto-trigger at 90%
11. **Phase 11** — batch artifact operations (`fa433410`)
    - `/batch /resolve-batch /delete-batch` slash wrappers

### TIER 4 — Polish & integration

12. **Phase 7** — replay mode (`--replay <session-id>`)
13. **T53** — ecodex wrapper auto-spawn translator + base_url rewriting
14. **T55** — live smoke test harness (reusable `live_test.sh`)

### TIER 5 — Architecture (previously deferred — now in scope)

15. **Phase 5** — knowledge graph side panel
    - Click artifact card → side panel with edges + Qdrant neighbors + related goals
    - Toggle Ctrl+G
16. **Phase 2b** — codex-app-server WebSocket dispatch
    - JSON-RPC over WS to codex-app-server
    - Full agent loop awareness
    - Reads app-server-protocol/schema/json/ fixtures, builds Python WS client

### TIER 6 — Bonus polish

17. **Translator concurrent request handling** — switch tiny_http loop to threaded or async
18. **ecodex cosmetic fixes**
    - `ecodex --version` shows actual version (not "codex-cli 0.0.0")
    - Help title says "ecodex" (not "Codex CLI")
19. **Empirica lint scoping bug fix** (T35 finding)
    - `empirica/empirica/config/service_registry.py:324` — skip lint when no Python files changed
20. **Documentation pass**
    - CHANGELOG entry for the chat phases
    - User guide section for empirica chat
    - Update CHAT.md final summary
    - README links

### TIER 7 — Cross-cutting tests

21. **Integration test suite** — `empirica/tests/test_chat_integration.py`
    - End-to-end: spawn translator + run chat → live empirica-server → assert turns persist correctly
    - Multi-provider switch test
    - Slash command full coverage
22. **Translator integration tests** — `codex-empirica-translator/tests_integration/`
    - Live-against-empirica-server test (using existing harness)
    - Anthropic adapter against real Anthropic API (skip if no key)
    - Concurrent-request test (validates Tier 6 work)

### TIER 8 — Provider expansion

23. **Vertex AI provider config** — Anthropic on GCP, just config + docs
24. **Bedrock provider config** — Anthropic on AWS, just config + docs
25. **Groq provider config** — fast inference, free tier
26. **Cerebras provider config** — wafer-scale fast inference
27. **Together AI provider config**
28. **OpenRouter provider config** — single key for many models
   - All as additions to `builtin_providers()` registry + docs entries

### TIER 9 — Cockpit integration

29. **Cockpit adopts shared statusline** (Phase 6b dependency)
30. **Cockpit surfaces empirica chat sessions** in instance table
31. **Cockpit launches chat from instance row** (action button → spawn `empirica chat` in new tmux pane)

### TIER 10 — Distribution

32. **Empirica chat as installable** — confirm `pip install -e .` exposes `empirica chat` correctly; document
33. **Codex plugin registration of chat** — chat as an `app` in the codex empirica plugin manifest, so `codex` users can launch it
34. **Cross-platform paths** — verify chat works on macOS (path differences, Textual rendering)

### TIER 11 — Web UI prototype

35. **Read-only HTML renderer** — `empirica chat-render <session.jsonl>` outputs HTML
    - Useful for sharing conversations
    - No interactive backend needed
    - Renders artifact cards + statusline + autonomy badge as static HTML

### TIER 12 — If still running

36. **Brier-score widget in chat** — surface session calibration trajectory live
37. **Performance instrumentation** — `empirica chat --profile` outputs per-turn timing breakdown
38. **Empirica `--autonomous` mode** — chat in full earned autonomy mode (the third autonomy badge), with session-end summary
39. **GitHub Actions CI** — for both repos: smoke test runs on PR
40. **Translator metrics export** — Prometheus/OpenTelemetry endpoint

---

## Source repos for porting (read this BEFORE each phase)

Most phases lift code or patterns from existing places. Don't rediscover.

| Phase | Source pattern | Source location |
|---|---|---|
| 8 (system prompt) | `empirica-system-prompt.md` for CC | `~/.claude/empirica-system-prompt.md` |
| 6b (full statusline) | `statusline_empirica.py` (225 LOC) | `~/.claude/plugins/local/empirica/scripts/statusline_empirica.py` |
| 10 (compact hooks) | pre-compact + post-compact hook patterns | `~/.claude/plugins/local/empirica/hooks/pre-compact.py` + `post-compact.py` |
| 5 (KG side panel) | Candence prediction-triage card pattern + IntelligencePanel | `/home/yogapad/empirical-ai/empirica-workspace/empirica_workspace/dashboard/widgets.py` (line 7958 + line 8761) |
| 11 (batch artifacts) | `log_artifacts -` / `resolve_artifacts -` / `delete_artifacts -` CLI shapes | `empirica` CLI (wrap, don't reimplement) |
| 13/14 (signals) | event signaling helpers | `empirica/empirica/core/signaling.py` |
| 15 (narration) | event tap JSONL + empirica session DB | translator `--event-log` + `empirica.data.session_database` |
| 9 (tokenizers) | tiktoken + transformers AutoTokenizer | external pip packages, lazy-import |
| 2b (app-server WS) | JSON-RPC schemas | `/home/yogapad/empirical-ai/ecodex/codex-rs/app-server-protocol/schema/json/` |
| Cockpit integration | existing `cockpit_app.py` (884 LOC) | `/home/yogapad/empirical-ai/empirica/empirica/cli/tui/cockpit_app.py` |

Key project paths:
- `/home/yogapad/empirical-ai/empirica/` — empirica package (branch `develop`)
- `/home/yogapad/empirical-ai/empirica-workspace/` — Candence (patterns only)
- `/home/yogapad/empirical-ai/ecodex/` — translator + ecodex (branch `build/v1-plugin`)
- `~/.claude/plugins/local/empirica/` — CC plugin (statusline + hooks)

---

## What I WON'T do (explicit out of scope)

- Anything requiring David's input (architectural forks, scope changes)
- Live tests requiring keys we don't have (DeepSeek balance, etc.)
- Marketplace publishing or external announcements
- Scope creep — only what's listed above
- Major refactors of shipped code unless a phase requires it
- Force-push or rewrite shared git history

---

## Risk management (unchanged)

- **Per-phase 2-fail rule:** skip + document if a phase's PREFLIGHT-to-commit cycle fails twice
- **Commit before POSTFLIGHT** every phase
- **No interactive prompts** — document and skip if a CLI subprocess hangs
- **Spec discipline** — every shipped phase updates CHAT.md
- **Honest reporting** — POSTFLIGHT artifacts (calibration_status, evidence_count, mistakes) tell the real story
- **Sentinel discipline** — no `--no-verify`, no sentinel pause

---

## When you wake up

1. **Read** `CHAT.md` — every shipped phase has commit hash + LOC marker
2. **Read** new `CHANGELOG.md` entry — human-readable summary
3. **Run** `git log --oneline develop -100` — chronological commits (yes 100, going long)
4. **Check** `empirica goals-list` — completed vs remaining
5. **Test** `empirica chat` — try the new commands, see new badges, narration
6. **Issues?** Each transaction has a POSTFLIGHT with confidence + any mistakes logged

---

## Approval

Suggested approval forms:
- "go" — full plan, all tiers, work down the list until interrupted
- "go but cap at Tier N" — explicit scope ceiling
- "go but add X / skip Y" — explicit modifications
