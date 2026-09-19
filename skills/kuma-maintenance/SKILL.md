---
name: kuma-maintenance
description: >
  Handle Uptime Kuma maintenance with confirmation-gated writes: read existing
  maintenance windows, pause or resume a monitor, or schedule a maintenance
  window — each only after the user explicitly confirms the exact action. Use
  when the user asks to pause/resume monitoring or schedule downtime for
  planned work.
---

# Uptime Kuma maintenance

Goal: apply exactly the maintenance action the user confirmed — nothing more.

> **Read-first:** these workflows use read tools by default; the only writes they may ever perform are pause, resume, and maintenance windows — and only after you explicitly confirm the specific action.

> Before any write, restate the exact action (for example "pause monitor <name>") and wait for the user's explicit yes — never write on a suggestion alone.

## Reading state (no confirmation needed)

- `getMaintenanceWindows` — list scheduled windows before proposing a new one (avoid duplicates), and during digests to annotate expected downtime.
- The summary/heartbeat reads from the other skills establish what's paused or failing before any state change.

## Sanctioned writes (confirmation required, every time)

1. **Pause a monitor** (`pauseMonitor`) — for planned work or noise suppression. Restate: which monitor, paused from when. Remind the user a paused monitor stops alerting entirely — Kuma's own notification channels go quiet too.
2. **Resume a monitor** (`resumeMonitor`) — restate: which monitor. Watch the first heartbeat afterwards and report whether it's actually back.
3. **Schedule a maintenance window** (`createMaintenance`) — restate: which monitor(s), start, duration/strategy, and title. If an existing window already covers the ask, say so instead of creating a new one.

**Hard limits:** these three are the entire write surface of this skill. Never call the delete tools (the five permanent, ungated ones named in the kuma-setup skill) — and never create/update monitors, notifications, tags, docker hosts, or status pages from this skill; routing the user to the Kuma UI for those is the correct answer.

> Alert delivery belongs to Uptime Kuma's own notification channels (90+ services, configured in its UI) — this bundle reviews and maintains; it does not page you.

## After a write

- Re-read the affected state (`getMonitorSummary` or `getMaintenanceWindows`) and confirm the change took effect before reporting success.
- Report the change in one line: action, target, result.

See the kuma-setup skill if the connection itself is failing.

## When MCP is unavailable

- Writes are impossible without the connection — do not simulate them; say so and collect the exact actions the user wants so they can apply them in the Kuma UI (or re-run this skill once the connection is back).
- The read steps still work as guides against pasted UI state (window lists, monitor statuses).
- Queue confirmed-but-unapplied actions explicitly: action, target, parameters — nothing applied, nothing guessed.
