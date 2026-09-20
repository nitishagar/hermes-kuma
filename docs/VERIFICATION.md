# Manual verification gate (human)

The offline suite cannot observe five things (research doc Verification Surface
Gaps 1–5). Run these on a machine with Hermes Agent installed, with a real
Uptime Kuma v2 instance you control.

## 1. Real Hermes load path

```bash
cd /path/to/hermes-kuma
hermes plugins validate --install-deps .   # documented on the developer-guide page + used by the plugin-catalog CI; absent from the CLI reference page — if your build lacks it, the doctor gate below is the exit-0 criterion
hermes plugins doctor . --ci        # must exit 0
hermes plugins install . --no-enable
hermes plugins enable kuma
```

Expected: `validate` reports no `dangerous` findings and no capability drift;
`doctor --ci` exits 0; after enabling, tools appear under the
`mcp__agent_plugin_kuma_…` namespace and the four `kuma-*` skills appear in
`skills_list`.

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

## 3. Ambient-env behavior (per host)

On OpenClaw: install the bundle, export the `UPTIME_KUMA_*` variables on the
gateway process, enable, and check whether the bundled server (no host config)
connects. Record what happens for **both** hosts — this is the evidence the
research doc marks unknown (bounding assumption A1), and it feeds the README.

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

## 5. Record the OpenClaw exposed-name format

If you inspect OpenClaw's tool names for this bundle
(`mcp__agent_plugin_…`), note the hash length — the name-budget test assumes
12 chars conservatively from a single Hermes observation (8); a second data
point tightens or relaxes that margin.
