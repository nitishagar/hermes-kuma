# Manual verification gate (human)

The offline suite cannot observe five things (research doc Verification Surface
Gaps 1–5). Run these on a machine with Hermes Agent installed, with a real
Uptime Kuma v2 instance you control.

## 1. Real Hermes load path — EXECUTED 2026-09-24 (Hermes Agent v0.21.5)

```bash
cd /path/to/hermes-kuma
hermes plugins validate --install-deps .   # documented on the developer-guide page + used by the plugin-catalog CI; absent from the CLI reference page — if your build lacks it, the doctor gate below is the exit-0 criterion
hermes plugins doctor . --ci        # must exit 0
hermes plugins install <git-url-or-owner/repo> --no-enable   # NOTE: a local path (`.`) is rejected — install takes a catalog name, Git URL, or owner/repo; push first
hermes plugins enable kuma
```

Observed 2026-09-24: `validate` passed ("portable manifest", "manifest
fields", "security scan — safe"); `doctor --ci` exited 0; install from a Git
URL + `enable kuma` + `plugins show kuma` (v0.1.0, enabled) all green. After
enabling, tools appear under the `mcp__agent_plugin_kuma_<8hex>__ku__<tool>`
namespace (8-char hash confirmed in current hermes-agent source) and the four
`kuma-*` skills load as agent skills.

## 2. The guaranteed credential tier (Hermes)

Add to `config.yaml` (secrets in `~/.hermes/.env`):

```yaml
mcp_servers:
  kuma:
    command: "npx"
    args: ["-y", "@davidfuchs/mcp-uptime-kuma@0.11.18"]
    env:
      UPTIME_KUMA_URL: "http://your-kuma-host:3001"
      UPTIME_KUMA_USERNAME: "<your username>"
      UPTIME_KUMA_PASSWORD: "${env:UPTIME_KUMA_PASSWORD}"
```

Then confirm a summary read works. This tier is the plan's "guaranteed" path —
if it fails, the tier structure needs revisiting (open an issue with the
Hermes version).

## 3. Ambient-env behavior (per host) — RESOLVED 2026-09-24, no live probe needed

Source-verified (no host behavior left unknown): Hermes builds stdio env via
`_build_safe_env` (safe-baseline allowlist + secret-source vars + the server
entry's own `env`; ambient `UPTIME_KUMA_*` do not pass), and OpenClaw inherits
only `HOME/LOGNAME/PATH/SHELL/TERM/USER` for MCP stdio servers
(`DEFAULT_INHERITED_ENV_VARS`). Tier 2 therefore does not work on either
host — Tier 1 (host-managed MCP config with `env`) is the only credential
path. The README and kuma-setup Tier-2 wording say this; bounding assumption
A1 is closed.

## 4. Skill quality + confirmation discipline (Hard Core B)

Against the live instance, run each skill once:

- `kuma-status-digest` — does the digest match the dashboard, and did it avoid
  per-monitor crawls?
- `kuma-incident-review` — is the drafted timeline accurate against a real
  incident (or a manually paused monitor)?
- `kuma-maintenance` — confirm the agent restates the exact action and waits
  for your explicit yes before any write; confirm it refuses out-of-scope
  writes (e.g. "create a monitor" should route you to the Kuma UI).
- `kuma-setup` — hand it to a colleague: can they connect without asking you
  anything?

Edit SKILL.md files for anything that reads wrong; the pinned invariant lines
must survive edits — `pytest -q` tells you if an edit broke one.

## 5. OpenClaw exposed-name format — RECORDED 2026-09-24

OpenClaw registers bundle MCP tools as `server__tool` (docs.openclaw.ai
"Plugin bundles" → Tool naming; verified mapping surface on OpenClaw
2026.9.6: `openclaw plugins inspect kuma` reports Format `bundle`, Bundle
format `agent (Agent Plugins)`, capabilities `skills, mcpServers`, MCP server
`ku`; all four skills `ready`). No hash, no Hermes-style namespace — no
budget pressure on this host. The name-budget test keeps its conservative
12-char Hermes leg (Hermes' own 8-char hash confirmed in current hermes-agent
source); nothing to tighten.
