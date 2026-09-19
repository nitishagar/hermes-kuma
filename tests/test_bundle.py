from bundle_facts import (
    MCP_SCHEMA_URL,
    PLUGIN_SCHEMA_URL,
    REPO_ROOT,
    SECRET_ENV_VARS,
    SHIPPED_GLOBS,
    load_json,
    load_tools,
)

plugin = load_json(REPO_ROOT / "plugin.json")
mcp = load_json(REPO_ROOT / "mcp.json")
tools = load_tools()


def test_vendored_schemas_keep_canonical_ids():
    # Provenance check on the vendored copies (tests/schemas/README.md): a
    # mislabeled or hand-edited vendored file is caught here.
    for path, canonical in [
        (REPO_ROOT / "tests/schemas/plugin.schema.json", PLUGIN_SCHEMA_URL),
        (REPO_ROOT / "tests/schemas/mcp.schema.json", MCP_SCHEMA_URL),
    ]:
        vendored = load_json(path)
        assert vendored.get("$id") == canonical, (
            f"{path.relative_to(REPO_ROOT)}: $id {vendored.get('$id')!r} != canonical {canonical}"
        )


def test_cross_file_schema_versions_match():
    # Agent Plugins spec §10.1: a version mismatch silently disables the MCP
    # surface while skills keep loading.
    plugin_version = plugin["$schema"].rsplit("/", 2)[-2]
    mcp_version = mcp["$schema"].rsplit("/", 2)[-2]
    assert plugin_version == mcp_version, (
        f"plugin.json targets {plugin_version}, mcp.json targets {mcp_version}"
    )


def test_vendored_tool_inventory_is_wellformed():
    # The fixture the budget and discipline tests read from must itself be
    # sane: 31 tools, unique names, exactly the three classes, and the
    # recorded longest name must actually be the longest.
    names = [t["name"] for t in tools["tools"]]
    assert len(names) == 31, f"expected 31 tools, got {len(names)}"
    assert len(set(names)) == 31, "duplicate tool names in the vendored inventory"
    assert {t["class"] for t in tools["tools"]} == {"read", "write", "destructive"}
    longest = max(names, key=len)
    assert tools["longest_tool_name"] == longest, (
        f"recorded longest {tools['longest_tool_name']!r} != actual {longest!r}"
    )


def test_tool_id_namespace_budget():
    # IMPLICIT_SPEC invariant 4. Hosts register agent-plugin MCP tools as:
    #   mcp__agent_plugin_<name>_<hash>__<server>__<tool>   (<= 64 chars)
    # The hash length is host-dependent: 8 chars observed in Hermes (snyk
    # README, `mcp__agent_plugin_snyk_8cb0f11d__sn__<tool>`); OpenClaw's
    # exposed-name format is unevidenced, so 12 chars is pure conservatism.
    name = plugin["name"]
    server_key = next(iter(mcp["mcpServers"]))
    longest = tools["longest_tool_name"]
    for hash_len in (8, 12):
        tool_id = f"mcp__agent_plugin_{name}_{'0' * hash_len}__{server_key}__{longest}"
        assert len(tool_id) <= 63, (
            f"tool-ID budget blown at hash_len={hash_len}: {len(tool_id)} > 63 "
            f"(the invariant requires margin below the 64 cap; {tool_id!r})"
        )


def test_no_secret_values_in_guidance_files():
    # IMPLICIT_SPEC invariant 2: secret env-var NAMES are mandated setup
    # content; their VALUES must be <placeholder> tokens or ${env:VAR}
    # references — never literals (advisor round 1: names != values).
    import re

    from bundle_facts import GUIDANCE_GLOBS, REPO_ROOT

    offenders = []
    value_rx = re.compile(
        r"(?P<name>" + "|".join(SECRET_ENV_VARS) + r")(?P<eq>\s*[:=]\s*)(?P<value>\S+)"
    )
    for pattern_glob in GUIDANCE_GLOBS:
        for path in sorted(REPO_ROOT.glob(pattern_glob)):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            for m in value_rx.finditer(text):
                value = m.group("value").strip("'\"")
                is_placeholder = re.fullmatch(r"<[^>]+>", value)
                is_env_ref = value.startswith("${env:") and value.endswith("}")
                if not (is_placeholder or is_env_ref):
                    line = text[: m.start()].count("\n") + 1
                    offenders.append(
                        f"{path.relative_to(REPO_ROOT)}:{line}: {m.group('name')}={m.group('value')}"
                    )
    assert not offenders, "literal secret values found:\n" + "\n".join(offenders)


def test_no_real_token_shaped_leaks_anywhere():
    # Defense in depth over ALL committed files including thoughts/ evidence
    # records: JWT-shaped strings (the credential type this stack uses) must
    # not appear anywhere. Upstream README's example env values quoted in
    # thoughts/ are not JWT-shaped and stay out of the way.
    import re

    jwt_rx = re.compile(r"eyJ[A-Za-z0-9_-]{20,}")
    offenders = []
    for path in sorted(REPO_ROOT.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".json", ".yml", ".yaml", ".toml"}:
            continue
        rel = path.relative_to(REPO_ROOT)
        if set(rel.parts) & {".venv", ".git", ".pytest_cache", "__pycache__"}:
            continue
        if jwt_rx.search(path.read_text(encoding="utf-8")):
            offenders.append(str(rel))
    assert not offenders, "JWT-shaped strings found:\n" + "\n".join(offenders)
