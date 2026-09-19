---
name: kuma-status-digest
description: >
  Produce a fleet-wide uptime digest from Uptime Kuma: overall posture from
  the monitor summary, problems ranked by severity, scheduled maintenance that
  explains expected downtime, and a short "nothing else moving" tail. Use for
  daily/weekly check-ins, "how are my services doing", or post-change reviews.
---

# Uptime Kuma status digest

Goal: a paste-ready digest of everything the instance knows — in one read,
not a monitor-by-monitor crawl.

> **Read-first:** these workflows use read tools by default; the only writes they may ever perform are pause, resume, and maintenance windows — and only after you explicitly confirm the specific action.

## Workflow

1. **One summary read first.** `getMonitorSummary` aggregates the fleet: up / down / paused / pending counts and the problem list. This is the digest's backbone — resist per-monitor reads until this says they're needed.
2. **Check scheduled work.** `getMaintenanceWindows` tells you which downtime is expected. Annotate, don't alarm: "down" monitors inside a maintenance window belong in a separate "expected" line.
3. **Structure the digest:**
   - **Posture** — one line: N up, M down, K paused, of T monitors.
   - **Problems** — down/flapping monitors, worst first, each with time-in-state from the summary.
   - **Expected** — maintenance-covered downtime, with window ends.
   - **Quiet tail** — "everything else up" one-liner so silence is explicit.
4. **Compare if the user asks.** For "what changed since yesterday", rely on what the summary/heartbeats expose — do not page through every monitor's history; offer the incident-review skill for anything suspicious.
5. Keep it under ~15 lines so it can be pasted into a channel as-is.

See the kuma-setup skill if the connection itself is failing.

> If the instance rate-limits or errors repeatedly, stop and batch — the digest must come from aggregate reads, not a per-monitor loop.

## When MCP is unavailable

- Ask the user to paste the Kuma dashboard state (monitor names + statuses, or the status page export) and apply the same four-section structure.
- Build the digest from what was pasted and mark the source as user-provided.
- Say plainly that live reads are unavailable; never invent uptime numbers.
