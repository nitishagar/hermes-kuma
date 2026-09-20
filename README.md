# hermes-kuma

[Uptime Kuma](https://github.com/louislam/uptime-kuma) monitoring for AI
agents — a portable [Agent Plugins v1](https://agent-plugins.org) bundle
wrapping the community MCP server for **Uptime Kuma v2** (pinned), with
curated workflow skills. No runtime code.

Works in **Hermes Agent and OpenClaw from day one** (both load Agent Plugins
bundles natively), plus any MCP-capable host.

The bundle's value is the safety and workflow layer on top of a read-write
upstream: the server exposes 31 tools including 5 permanent, ungated deletes —
the skills enforce summary-first reads, never instruct the delete tools, and
gate the only sanctioned writes (pause / resume / maintenance windows) behind
your explicit confirmation. **Alerting stays with Uptime Kuma's own
notification channels (90+ services)** — this bundle reviews and maintains;
it does not page you.

## What's inside

```
plugin.json                          Agent Plugins v1.0.0 manifest (name: kuma)
mcp.json                             one stdio server: @davidfuchs/mcp-uptime-kuma@0.11.18 (pinned)
skills/kuma-setup/SKILL.md           credential tiers, troubleshooting, hard limits
skills/kuma-incident-review/SKILL.md summary → heartbeat timeline → draft incident summary
skills/kuma-status-digest/SKILL.md   fleet digest from one summary read
skills/kuma-maintenance/SKILL.md     confirmation-gated pause/resume/maintenance windows
```

## Requirements

- **Uptime Kuma v2** (stable 2.5.x; the upstream server does not support v1).
- **Node.js ≥ 22 on `PATH`** (the server is launched with `npx -y`; npx only
  *warns* about the engines requirement, so an old Node fails confusingly).

## Install

### Hermes Agent

```bash
hermes plugins install nitishagar/hermes-kuma --no-enable
hermes plugins enable kuma
```

### OpenClaw

OpenClaw installs Agent Plugins bundles natively:

```bash
openclaw plugins install git:github.com/nitishagar/hermes-kuma
```

### Any MCP-capable host

Point your host's MCP client at the stdio command in `mcp.json`
(`npx -y @davidfuchs/mcp-uptime-kuma@0.11.18`) and load the `skills/`
directories as agent skills.

## Credentials (three tiers)

The server reads `UPTIME_KUMA_URL` plus (when your instance has auth enabled)
`UPTIME_KUMA_USERNAME`/`UPTIME_KUMA_PASSWORD`, or a JWT. The bundle ships no
secrets and no `env` map — pick a tier:

1. **Guaranteed: your host's own MCP configuration** (pinning the same
   version). Hermes: a `mcp_servers` entry in `config.yaml` whose `env` can
   reference secrets via `${env:VAR}` (resolved from `~/.hermes/.env`).
   OpenClaw: `openclaw mcp add --env`. Full examples in
   `skills/kuma-setup/SKILL.md`.
2. **Best-effort: ambient environment.** Hosts that pass their own
   environment to spawned MCP servers need nothing extra — export the
   `UPTIME_KUMA_*` variables before starting the host and verify with a cheap
   read. (OpenClaw's docs imply this behavior; Hermes does not document it —
   don't rely on it unverified.)
3. **HTTP sidecar** (VPS/remote agents): the server's documented Docker form
   with `-t streamable-http`. **Warning: with `MCP_AUTH_TOKEN` unset there is
   no authentication, `ALLOWED_ORIGIN` defaults to `*`, and the endpoint has
   full read/write control including deleting monitors** — always set a token
   and a narrow origin, and never expose the raw endpoint off-host
   unencrypted (terminate TLS in front or keep it loopback/host-internal).

> Trust note: the upstream server is a single-maintainer community npm package. The exact version pin blocks silent drift, but no integrity digest is possible in this manifest shape — review what you enable.

**2FA users:** use the JWT helper (`npx -p @davidfuchs/mcp-uptime-kuma@0.11.18
mcp-uptime-kuma-get-jwt <url> <user> <pass>`) and supply
`UPTIME_KUMA_JWT_TOKEN`. Kuma's API keys do **not** work here — they
authenticate only the `/metrics` endpoint.

## Muse (Meta) status

No Muse compatibility is claimed. Meta's Muse assistant opened its
[Connector Platform](https://muse.ai/platform) with no public SDK, and public
reporting on whether Muse consumes MCP server URLs conflicts. A laptop-local
stdio server would be unreachable from Meta's cloud in any case; the
reachable shape is the tier-3 HTTP sidecar — which carries the security
warning above.

Muse Code (Meta's terminal coding agent) is a separate product that documents its own MCP support (dev.meta.ai/docs/muse-code) — this note covers only the Muse assistant's Connector Platform.

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install pytest jsonschema pyyaml
.venv/bin/python -m pytest -q          # offline: schemas, skills, catalog template
```

The suite validates the manifests against the published v1.0.0 schemas
(vendored, with `$id` provenance), the skill frontmatter and per-role pinned
safety content, the tool-discipline rules against a vendored 31-tool
inventory, the version pin across all guidance files, and the catalog entry
template against the upstream checker vendored from `NousResearch/hermes-agent`.

## Publishing checklist (maintainer)

1. Merge to `main`, tag a release (`git tag v0.1.0 && git push --tags`).
2. Confirm the pin still exists: `npm view @davidfuchs/mcp-uptime-kuma@0.11.18 version`.
3. Fill `docs/catalog-entry.yaml.template` (replace the `sha` placeholder with
   the tagged commit's 40-hex SHA; rename to `hermes-kuma.yaml`).
4. Verify on a machine with Hermes installed (see `docs/VERIFICATION.md`).
5. Open a PR adding the YAML to `NousResearch/hermes-agent` under
   `plugin-catalog/` (owner-submitted; the catalog CI does the rest).

## License

MIT — see [LICENSE](LICENSE).
