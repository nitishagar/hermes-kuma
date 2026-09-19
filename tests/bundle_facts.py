"""Shared facts and helpers for the offline bundle-validation suite."""

import json
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]

# Canonical published schema URLs (Agent Plugins v1.0.0, frozen spec).
PLUGIN_SCHEMA_URL = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
MCP_SCHEMA_URL = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"

# Pinned upstream server (npm registry verified 2026-09-19).
PACKAGE = "@davidfuchs/mcp-uptime-kuma"
PIN = "0.11.18"
PINNED_PACKAGE = f"{PACKAGE}@{PIN}"

# Pinned literal strings the skills must carry (PLAN.md "Approach").
READ_FIRST_LINE = (
    "> **Read-first:** these workflows use read tools by default; the only "
    "writes they may ever perform are pause, resume, and maintenance windows "
    "— and only after you explicitly confirm the specific action."
)
NO_DESTRUCTIVE_LINE = (
    "> Never call the delete tools — deleteMonitor, deleteNotification, "
    "deleteDockerHost, deleteTag, deleteStatusPage — they are permanent and "
    "have no upstream confirmation gate; this bundle's workflows do not use "
    "them."
)
WRITE_CONFIRM_LINE = (
    '> Before any write, restate the exact action (for example "pause monitor '
    '<name>") and wait for the user\'s explicit yes — never write on a '
    "suggestion alone."
)
ENV_FLOW_LINE = (
    "The guaranteed credential path is your host's own MCP configuration, "
    f"pinning the same version (`{PINNED_PACKAGE}`): Hermes — a `mcp_servers` "
    "entry in `config.yaml` whose `env` can reference secrets via "
    "`${env:VAR}` (resolved from `~/.hermes/.env`); OpenClaw — "
    "`openclaw mcp add --env`. The bundled server itself picks up credentials "
    "only where your host passes its own environment through."
)
HTTP_WARNING_LINE = (
    "> HTTP sidecar warning: with MCP_AUTH_TOKEN unset there is no "
    "authentication, ALLOWED_ORIGIN defaults to *, and the endpoint has full "
    "read/write control including deleting monitors — always set a token and "
    "a narrow origin."
)
V2_LINE = (
    "> Requires Uptime Kuma v2 (stable 2.5.x); v1 is untested and unsupported "
    "by the upstream server."
)
ALERTING_LINE = (
    "> Alert delivery belongs to Uptime Kuma's own notification channels "
    "(90+ services, configured in its UI) — this bundle reviews and "
    "maintains; it does not page you."
)
MCP_UNAVAILABLE_HEADING = "## When MCP is unavailable"
TROUBLESHOOT_HEADING = "## Troubleshooting the connection"

SETUP_SKILL = "kuma-setup"
MAINTENANCE_SKILL = "kuma-maintenance"
SKILL_NAMES = ["kuma-setup", "kuma-incident-review", "kuma-status-digest", "kuma-maintenance"]

# Secret env vars whose values must never appear as literals; the names
# themselves are mandated setup content (advisor round 1: names != values).
SECRET_ENV_VARS = ["UPTIME_KUMA_PASSWORD", "UPTIME_KUMA_JWT_TOKEN", "UPTIME_KUMA_2FA_TOKEN"]

# A file "mentions the sidecar" iff it matches this (advisor round 1: pinned
# trigger terms so the HTTP-warning co-occurrence scan cannot silently
# under-match).
SIDECAR_MENTION_PATTERN = r"streamable.http|HTTP sidecar"

# Guidance files: the pin and secret-value rules govern what users are told
# to copy-paste. thoughts/ records quote upstream verbatim (including its
# unpinned JWT-helper command and example env values), so they are evidence,
# not guidance — they get a real-leak scan only (JWT shape), not the pin or
# placeholder rules.
GUIDANCE_GLOBS = [
    "plugin.json",
    "mcp.json",
    "skills/**/*.md",
    "README.md",
    "docs/**",
    ".github/**/*.y*ml",
]
THOUGHTS_GLOB = "thoughts/**/*.md"

SHIPPED_GLOBS = GUIDANCE_GLOBS + [THOUGHTS_GLOB]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_tools() -> dict:
    return load_json(REPO_ROOT / "tests/fixtures/tools.json")


def load_skill_frontmatter(path: Path) -> dict:
    """Parse the YAML frontmatter block of a SKILL.md file."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise AssertionError(f"{path.name}: missing '---' frontmatter opener")
    end = text.find("\n---", 3)
    if end == -1:
        raise AssertionError(f"{path.name}: missing '---' frontmatter closer")
    return yaml.safe_load(text[3:end])
