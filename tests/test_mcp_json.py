import jsonschema

from bundle_facts import (
    MCP_SCHEMA_URL,
    PIN,
    PINNED_PACKAGE,
    REPO_ROOT,
    load_json,
)

mcp = load_json(REPO_ROOT / "mcp.json")
mcp_schema = load_json(REPO_ROOT / "tests/schemas/mcp.schema.json")


def test_mcp_json_conforms_to_published_schema():
    jsonschema.Draft202012Validator.check_schema(mcp_schema)
    errors = sorted(
        jsonschema.Draft202012Validator(mcp_schema).iter_errors(mcp),
        key=lambda e: e.json_path,
    )
    assert not errors, "\n".join(f"{e.json_path}: {e.message}" for e in errors)


def test_exactly_one_stdio_server():
    servers = mcp["mcpServers"]
    assert len(servers) == 1, f"expected exactly one server, got {sorted(servers)}"
    (entry,) = servers.values()
    assert entry["type"] == "stdio"


def test_ships_the_pinned_package_with_no_env_map():
    # IMPLICIT_SPEC invariants 2 and 3: the args pin the exact upstream
    # version, and no env map ships (credentials are host-owned; env values
    # are visible package data per the Agent Plugins spec).
    (entry,) = mcp["mcpServers"].values()
    assert entry["command"] == "npx"
    assert entry["args"] == ["-y", PINNED_PACKAGE], f"args drifted from the pin: {entry['args']}"
    assert "env" not in entry, "shipped mcp.json must not carry an env map"


def test_no_unpinned_package_occurrences_in_guidance_files():
    # IMPLICIT_SPEC invariant 3: every occurrence of the package name across
    # user-facing guidance files carries the exact version suffix. thoughts/
    # records quote upstream verbatim and are evidence, not guidance — they
    # are covered by the leak scan in test_bundle.py instead.
    import re

    from bundle_facts import GUIDANCE_GLOBS, PACKAGE, REPO_ROOT

    offenders = []
    for pattern_glob in GUIDANCE_GLOBS:
        for path in sorted(REPO_ROOT.glob(pattern_glob)):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            for match in re.finditer(re.escape(PACKAGE), text):
                tail = text[match.end(): match.end() + 1]
                if tail != "@":
                    line = text[: match.start()].count("\n") + 1
                    offenders.append(f"{path.relative_to(REPO_ROOT)}:{line} (unpinned occurrence)")
    assert not offenders, "unpinned package references:\n" + "\n".join(offenders)


def test_no_unpinned_older_or_newer_pin_in_mcp_json():
    # Guard the exact pin value itself, independent of PINNED_PACKAGE.
    import json as _json

    raw = _json.loads((REPO_ROOT / "mcp.json").read_text(encoding="utf-8"))
    (entry,) = raw["mcpServers"].values()
    assert f"@{PIN}" in " ".join(entry["args"])


def test_schema_declares_canonical_v1_url():
    assert mcp["$schema"] == MCP_SCHEMA_URL
