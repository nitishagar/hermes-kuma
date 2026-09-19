---
name: kuma-setup
description: >
  Set up the kuma plugin: connect the agent to a self-hosted Uptime Kuma v2
  instance through the pinned community MCP server, choose a credential tier
  (host-native config, ambient environment, or an HTTP sidecar), and
  troubleshoot connection failures. Use when the user asks to connect,
  configure, authenticate, or debug Uptime Kuma access.
---

# Uptime Kuma setup for the `kuma` plugin

This plugin bundles the community MCP server for [Uptime Kuma](https://github.com/louislam/uptime-kuma)
(pinned: `@davidfuchs/mcp-uptime-kuma@0.11.18`, stdio) plus workflow skills —
incident review, status digest, and confirmation-gated maintenance. No runtime
code ships in the bundle.

> Requires Uptime Kuma v2 (stable 2.5.x); v1 is untested and unsupported by the upstream server.

> Alert delivery belongs to Uptime Kuma's own notification channels (90+ services, configured in its UI) — this bundle reviews and maintains; it does not page you.

## Credential tiers (pick one)

The server reads its connection settings from environment variables:
`UPTIME_KUMA_URL` (always required), and — when your instance has auth
enabled — `UPTIME_KUMA_USERNAME` + `UPTIME_KUMA_PASSWORD`, or a JWT.

**Tier 1 — guaranteed: your host's own MCP configuration.**
The guaranteed credential path is your host's own MCP configuration, pinning the same version (`@davidfuchs/mcp-uptime-kuma@0.11.18`): Hermes — a `mcp_servers` entry in `config.yaml` whose `env` can reference secrets via `${env:VAR}` (resolved from `~/.hermes/.env`); OpenClaw — `openclaw mcp add --env`. The bundled server itself picks up credentials only where your host passes its own environment through.

Hermes example (credentials live in `~/.hermes/.env`, never in `config.yaml`):

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

OpenClaw example: `openclaw mcp add kuma --command npx --arg -y --arg @davidfuchs/mcp-uptime-kuma@0.11.18 --env UPTIME_KUMA_URL=http://your-kuma-host:3001 --env UPTIME_KUMA_USERNAME=<your username> --env UPTIME_KUMA_PASSWORD=<your password>` (OpenClaw's stdio env safety filter blocks interpreter/loader keys; the `UPTIME_KUMA_*` names pass).

**Tier 2 — best-effort: ambient environment.** If your host passes its own
environment to spawned MCP servers (OpenClaw's docs imply this; Hermes does
not document it), exporting `UPTIME_KUMA_URL` / `UPTIME_KUMA_USERNAME` /
`UPTIME_KUMA_PASSWORD` before starting the host is enough — the bundled
server needs no extra configuration. Verify with a cheap read (Tier 3 check
below) before relying on it.

**Tier 3 — HTTP sidecar (VPS/remote agents).** Run the server's documented
Docker form with `-t streamable-http` and point your host's MCP config at
`http://<host>:3000/mcp`.

> HTTP sidecar warning: with MCP_AUTH_TOKEN unset there is no authentication, ALLOWED_ORIGIN defaults to *, and the endpoint has full read/write control including deleting monitors — always set a token and a narrow origin.

Never expose the raw HTTP endpoint off-host unencrypted: the bearer token grants that full delete-capable surface and would cross the wire in cleartext — terminate TLS in front (reverse proxy) or keep the sidecar loopback/host-internal.

When a command example would put a real secret on the command line (the OpenClaw inline `--env` form, the JWT helper's positional password), prefer the env-reference form (`${env:VAR}` from `~/.hermes/.env`) or set it via your host's secret mechanism instead — command-line secrets land in shell history and process lists.

**2FA users:** prefer a JWT — `npx -p @davidfuchs/mcp-uptime-kuma@0.11.18 mcp-uptime-kuma-get-jwt <kuma-url> <username> <password>` — and supply `UPTIME_KUMA_JWT_TOKEN` instead of username/password. Kuma's API keys will NOT work here: they authenticate only Kuma's `/metrics` endpoint, not this server's socket.io login.

## First connection check

1. Enable the plugin (Hermes: `hermes plugins enable kuma`).
2. Ask for a monitor summary (the incident-review skill starts with one).
3. If tools appear but error, go to Troubleshooting. If no `kuma`/`ku` tools appear at all, the plugin may not be enabled or the host blocked the spawn.

## What the agent may and may not do

> **Read-first:** these workflows use read tools by default; the only writes they may ever perform are pause, resume, and maintenance windows — and only after you explicitly confirm the specific action.

> Never call the delete tools — deleteMonitor, deleteNotification, deleteDockerHost, deleteTag, deleteStatusPage — they are permanent and have no upstream confirmation gate; this bundle's workflows do not use them.

## Troubleshooting the connection

Work down the ladder; each step distinguishes one failure from the next:

1. **Node too old** — the server needs Node ≥ 22; `npx` only *warns* about the `engines` requirement and then crashes on modern syntax. Check `node --version`.
2. **Spawn failed / offline cold cache** — the first `npx` run downloads the package; on an offline host it fails outright. Pre-warm with `npx -y @davidfuchs/mcp-uptime-kuma@0.11.18 --help` once online.
3. **Missing env vars** — the server exits complaining about `UPTIME_KUMA_URL` (always required) or credentials (required when the instance has auth). With auth disabled on the instance, the URL alone suffices.
4. **Wrong credentials** — the server surfaces Kuma's opaque `authInvalidToken` for a bad token (Kuma API keys fail this way — use a real JWT), or a login failure for bad username/password/2FA.
5. **Instance unreachable** — a plain `curl` to `UPTIME_KUMA_URL` from the same machine tells you whether it's the network or the credentials.

## When MCP is unavailable

- The workflow skills double as guides: follow their steps against the Kuma web UI (or a pasted status page) and produce the same structured output.
- Ask the user for what the workflow needs (monitor names, statuses, last-change times) instead of guessing workspace state.
- Say plainly that live reads are unavailable; never invent monitor states.
