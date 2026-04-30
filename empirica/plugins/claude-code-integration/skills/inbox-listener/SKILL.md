---
name: inbox-listener
description: "Use when arming an event listener registered with `empirica listener` — when the user says 'arm this listener', 'subscribe to ntfy topic', 'wake me when X arrives', or when responding to a system-reminder from the listener-install-pickup hook. Listeners are sister concept to cron loops but event-driven: hold a curl -N connection against a topic, arm Monitor with persistent:true, wake on event arrival. Idle cost is zero (no PREFLIGHT/CHECK/POSTFLIGHT cycles for empty polls); wake latency is network round-trip. Without this wiring, listener registration is a no-op — registry has metadata but nothing is actually listening."
version: 1.0.0
---

# Inbox-Listener Wiring

Empirica's loop-cron skill wires periodic background work into the
registry. This skill does the same for **event-driven** background work:
held HTTP connection (ntfy/SSE), Monitor wake on event, wake handler
runs, listener stays armed.

The CLI surface (`empirica listener register / pause / resume / list /
status / unregister`) handles registry, pause flags, and runtime
metadata. This skill is the **prompt template for the listener body**
— what runs inside the owning Claude session to actually arm the
listener.

---

## When to Use

You see a system-reminder from `listener-install-pickup` saying a
listener is queued for installation in this instance. The reminder
contains the substituted prompt template — follow it.

Or: you want to manually arm a listener that was registered but is
currently disarmed (no `~/.empirica/listener_active_*.json` file).

If you're scheduling **periodic** work (cron-mode loop), use
`/loop-cron` instead. This skill is for "wake when something arrives,"
not "wake every 15 minutes."

---

## Architecture

Three components, none of which involve cron:

```
                     ┌────────────────────────────┐
                     │ external publisher         │
                     │ (Cortex, ntfy emitter, ...)│
                     └──────────────┬─────────────┘
                                    │ HTTP POST
                                    ▼
                     ┌────────────────────────────┐
                     │  ntfy server               │
                     │  topic: <role>-claude-inbox│
                     └──────────────┬─────────────┘
                                    │ held HTTP connection
                                    ▼
   Background Bash (run_in_background: true):
     curl -N -u $NTFY_USER:$NTFY_PASSWORD https://$NTFY_SERVER/<topic>/json
                                    │ emits JSON line per published message
                                    ▼
   Claude Code Monitor (persistent: true, watches the curl task):
                                    │ matches a line → wakes parent CC
                                    ▼
                     <task-notification> arrives
                                    │
                                    ▼
                     wake handler runs (on_wake_template)
                                    │
                                    ▼
                     `empirica listener record-wake NAME`
                                    │
                                    └── Monitor stays armed for next event
```

**Idle cost:** zero. The curl holds the connection. No PREFLIGHT cycles
fire for empty polls. CC tokens consumed only on wake.

**Wake latency:** sub-second from publish to wake handler (network
round-trip + Monitor poll cycle).

---

## Arming Sequence

Variables you need (provided in the install-request system-reminder):

- `{NAME}` — listener name (e.g. `outreach-inbox`)
- `{TOPIC}` — URL scheme + rest (e.g. `ntfy:outreach-claude-inbox`)
- `{ON_WAKE}` — what to do on each wake (the registered prompt template)
- `{INSTANCE}` — your instance_id (resolve via `empirica instance current`
  or session-resolver; usually available as env var `EMPIRICA_INSTANCE_ID`)

### Step 1: launch the held connection

For `ntfy:` topics, parse the rest as the channel name. Server +
auth from env (`NTFY_SERVER`, `NTFY_USER`, `NTFY_PASSWORD`) — if the
user hasn't configured them, fall back to the public ntfy.sh and warn.

```
# Background Bash (run_in_background: true) — capture the task_id
curl -N -u "$NTFY_USER:$NTFY_PASSWORD" \
  "https://$NTFY_SERVER/{TOPIC_REST}/json"
```

The Bash tool returns `task_id` for the running task. Capture it as
`$CURL_TASK_ID`. The OS PID for the curl process is harder to get
directly from CC; for V1 record `null` for `curl_pid` and rely on
`TaskStop($CURL_TASK_ID)` for cleanup. (Future: a wrapper script
could echo `$$` first then exec curl.)

### Step 2: arm the Monitor

```
# Monitor with persistent: true, until pattern matches a JSON event line
Monitor(
  task_id=$CURL_TASK_ID,
  pattern="^\\{",          # JSON event line
  persistent=true,
  stream="stdout",
  pollIntervalMs=500
)
```

The Monitor returns `monitor_task_id` and stays armed across multiple
matches. Capture as `$MONITOR_TASK_ID`.

### Step 3: write the runtime metadata

```bash
cat > "$HOME/.empirica/listener_active_{INSTANCE}_{NAME}.json" << EOF
{
  "monitor_task_id": "$MONITOR_TASK_ID",
  "curl_task_id": "$CURL_TASK_ID",
  "curl_pid": null,
  "armed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
```

(`curl_task_id` is the CC task; `curl_pid` is the OS PID. Both are
recorded so future tooling can kill via either path. V1: TaskStop the
curl task is the supported teardown.)

### Step 4: wake handler

Each time Monitor matches a JSON event line, you wake with a
`<task-notification>` containing the matched line. On each wake:

```
1. Check pause flag — exit silently if paused:
     if [ -f "$HOME/.empirica/listener_paused_{INSTANCE}_{NAME}" ]; then
       # The body backstop. Stop processing wakes; the
       # listener-uninstall-pickup hook should also have queued a
       # TaskStop request. Either way: don't continue.
       return
     fi

2. Run the on-wake handler:
     {ON_WAKE}

3. Record the wake:
     empirica listener record-wake {NAME} \
       --message "<short summary of what happened>"

4. Loop back — Monitor stays armed for the next event.
```

The Monitor `persistent: true` flag means the same Monitor task
delivers multiple wakes. You don't need to re-arm between events.

---

## Pausing and Resuming

From any terminal, on any machine that shares `~/.empirica/`:

```
empirica listener pause  {NAME} --instance {INSTANCE}
empirica listener resume {NAME} --instance {INSTANCE}
empirica listener status {NAME} --instance {INSTANCE}
empirica listener list   --instance {INSTANCE}
empirica listener unregister {NAME} --instance {INSTANCE}
```

`pause` writes the pause sidecar AND, when the active runtime file
shows the listener is armed (Monitor task id present), writes a
`listener_uninstall_pending_{INSTANCE}_{NAME}.json` file. The
`listener-uninstall-pickup` hook surfaces it on this instance's next
prompt as a system-reminder asking you to:

1. `TaskStop($MONITOR_TASK_ID)` to disarm the Monitor
2. `TaskStop($CURL_TASK_ID)` (or kill the PID if recorded) to drop
   the held connection
3. Delete `~/.empirica/listener_active_{INSTANCE}_{NAME}.json`

The body's pause check (step 1 of the wake handler above) is the
backstop — if you don't run TaskStop in time, the next wake exits
silently anyway.

`resume` clears the pause flag. To re-arm after resume, re-issue via
`empirica listener install-request --instance {INSTANCE} --name {NAME}
--topic {TOPIC}` from any terminal — the install-pickup hook will
surface a fresh install request.

---

## State Files

| Path | Purpose | Owner |
|---|---|---|
| `~/.empirica/listeners_<instance>.json` | Declarative registry (name, topic, on_wake, history) | empirica CLI |
| `~/.empirica/listener_paused_<instance>_<name>` | Pause flag (empty file == paused) | empirica CLI |
| `~/.empirica/listener_active_<instance>_<name>.json` | Runtime metadata (Monitor + curl task ids, armed_at) | listener body (this skill) |
| `~/.empirica/listener_install_pending_<instance>_<name>.json` | Bootstrap install request | empirica CLI → listener-install-pickup hook |
| `~/.empirica/listener_uninstall_pending_<instance>_<name>.json` | Bootstrap uninstall request | empirica CLI → listener-uninstall-pickup hook |

The active file is yours to maintain. Write it after arming, delete
it on uninstall. Status output (`empirica listener status`) reads it
to surface "armed since X" alongside the registry's wake history.

---

## Concrete Example

Cortex publishes orchestration messages to ntfy when the outreach
inbox gets new mail. The outreach Claude wants to wake on those
messages and process them.

```
# Cockpit registers + queues install-request:
empirica listener install-request \
  --instance tmux_outreach \
  --name outreach-inbox \
  --topic ntfy:outreach-claude-inbox \
  --description "Cortex orchestration inbox" \
  --on-wake "Read empirica/outreach inbox, summarize unread, capture findings."

# Outreach Claude's UserPromptSubmit hook surfaces the system-reminder
# on next prompt. Outreach Claude runs /inbox-listener with the
# substituted template. After arming:

#   ~/.empirica/listener_active_tmux_outreach_outreach-inbox.json
#     {monitor_task_id: "tk_a1b2", curl_task_id: "tk_c3d4", armed_at: "..."}

# Now: every time Cortex publishes to outreach-claude-inbox, ntfy
# delivers it via the held connection within milliseconds. Monitor
# wakes outreach Claude. Outreach Claude reads the inbox, processes
# unread, calls record-wake. Stays armed.

# Pause from another terminal:
empirica listener pause outreach-inbox --instance tmux_outreach
# → reads active file, writes uninstall_pending. Outreach Claude
# sees the system-reminder on its next prompt, runs TaskStop on both
# the Monitor and the curl, deletes the active file. Listener is OFF.
```

---

## Visibility

Once armed, the listener appears in:

```
empirica status              # current instance
empirica status --all        # every Claude across every terminal
empirica listener list       # listener-only view
```

(Cockpit listener panel — item 5 of PROPOSAL_EVENT_LISTENER — is a
follow-up; for now `empirica listener list` is the canonical view.)

---

## Related

- `empirica listener` CLI — registry + pause/resume verbs
- `/loop-cron` — sister skill for periodic (not event-driven) work
- `docs/architecture/PROPOSAL_EVENT_LISTENER.md` — full design + rationale
- `docs/architecture/COCKPIT.md` — state-file layout + discovery rules
