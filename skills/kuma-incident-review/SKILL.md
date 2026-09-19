---
name: kuma-incident-review
description: >
  Investigate an Uptime Kuma incident: start from the monitor summary, drill
  into the affected monitor's heartbeats to build a timeline, and draft an
  incident summary for the user to paste wherever they report incidents. Use
  when something is down, flapping, or just recovered, or the user asks "what
  happened to X".
---

# Uptime Kuma incident review

Goal: turn "something is down" into a dated, factual timeline and a draft
summary — without writing anything to the instance.

> **Read-first:** these workflows use read tools by default; the only writes they may ever perform are pause, resume, and maintenance windows — and only after you explicitly confirm the specific action.

## Workflow

1. **Start from the summary, not the list.** One `getMonitorSummary` call gives the aggregated state — identify the affected monitor(s) (down or flapping) before any per-monitor read. If the user named the monitor, confirm it exists via the summary rather than listing everything.
2. **Drill into the affected monitor only.** Pull `getHeartbeats` for that monitor and read the recent status transitions. Heartbeat messages may include credential-scrubbed detail — quote them as-is, do not guess at redacted content.
3. **Build the timeline.** For each recent transition: time, old state → new state, and the reported message. Mark the still-open edge (currently down since T, or recovered at T after N minutes).
4. **Draft the incident summary** for the user to paste: what is affected, when it started, current state, observed pattern (single failure vs flapping vs sustained), and what changed around that time if the heartbeats suggest it.
5. **Suggest next reads, not actions.** If the pattern looks like a maintenance window collision, point at the maintenance skill. If a monitor should stop alerting during a known change, the user may want a pause — that is a confirmed write, routed to the maintenance skill.

See the kuma-setup skill if the connection itself is failing.

> If the instance rate-limits or errors repeatedly, stop and batch — re-reading the same heartbeats in a loop fixes nothing.

## When MCP is unavailable

- Ask the user to paste the monitor's recent heartbeat rows (or a screenshot transcript) from the Kuma UI and apply the same timeline structure.
- Produce the same summary shape: affected monitor, start time, transitions, current state, pattern.
- Say plainly that live reads are unavailable; never invent states or timestamps.
