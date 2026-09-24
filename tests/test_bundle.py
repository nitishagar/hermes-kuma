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
    # The hash length is host-dependent: 8 chars in Hermes (current source:
    # `agent_plugin_<name>_<8hex>__<server>`, hermes-agent
    # tests/tools/test_mcp_tool.py; also the snyk README observation
    # `mcp__agent_plugin_snyk_8cb0f11d__sn__<tool>`); OpenClaw exposes the
    # short `server__tool` form (docs.openclaw.ai/plugins/bundles "Tool
    # naming"; no hash, no budget pressure), so 12 chars stays as pure
    # conservatism on the Hermes leg only.
    name = plugin["name"]
    server_key = next(iter(mcp["mcpServers"]))
    longest = tools["longest_tool_name"]
    for hash_len in (8, 12):
        tool_id = f"mcp__agent_plugin_{name}_{'0' * hash_len}__{server_key}__{longest}"
        assert len(tool_id) <= 63, (
            f"tool-ID budget blown at hash_len={hash_len}: {len(tool_id)} > 63 "
            f"(the invariant requires margin below the 64 cap; {tool_id!r})"
        )


def test_http_sidecar_mentions_carry_the_warning():
    # IMPLICIT_SPEC invariant 12: any shipped file that mentions the
    # streamable-HTTP sidecar must carry the MCP_AUTH_TOKEN warning — the
    # upstream default (no token) exposes full read/write including deletes.
    import re

    from bundle_facts import GUIDANCE_GLOBS, REPO_ROOT, SIDECAR_MENTION_PATTERN

    sidecar_rx = re.compile(SIDECAR_MENTION_PATTERN, re.IGNORECASE)
    offenders = []
    for pattern_glob in GUIDANCE_GLOBS:
        for path in sorted(REPO_ROOT.glob(pattern_glob)):
            if not path.is_file() or path.suffix == ".json":
                continue
            text = path.read_text(encoding="utf-8")
            if sidecar_rx.search(text) and "MCP_AUTH_TOKEN" not in text:
                offenders.append(str(path.relative_to(REPO_ROOT)))
    assert not offenders, "sidecar mentions without the auth warning:\n" + "\n".join(offenders)


def test_no_runtime_code_shipped():
    # IMPLICIT_SPEC invariant 16: the plugin ships no executable code — only
    # manifests, skills (Markdown), docs, and validation tooling in tests/CI.
    executable_dirs = {"tests", ".github"}
    skip_dirs = {".venv", ".git", ".pytest_cache", "__pycache__", "thoughts"}
    executable_exts = {".py", ".sh", ".bash", ".js", ".ts", ".mjs", ".cjs", ".exe", ".bat", ".cmd", ".ps1"}
    offenders = []
    for path in sorted(REPO_ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(REPO_ROOT)
        if set(rel.parts) & skip_dirs:
            continue
        if rel.parts[0] in executable_dirs:
            continue
        if path.suffix.lower() in executable_exts:
            offenders.append(str(rel))
    assert not offenders, "executable files shipped outside tests/CI:\n" + "\n".join(offenders)


def test_catalog_template_capabilities_are_empty():
    # IMPLICIT_SPEC invariant 15: bundle MCP tools are namespaced, never
    # declared — the upstream validator accepts filled lists, so this is
    # checked here (review round 1).
    import yaml

    text = (REPO_ROOT / "docs/catalog-entry.yaml.template").read_text(encoding="utf-8")
    entry = yaml.safe_load(text.replace("<40-hex commit SHA of the release tag — fill before PR>", "a" * 40))
    capabilities = entry["capabilities"]
    assert set(capabilities) == {"provides_tools", "provides_hooks", "provides_middleware", "requires_env"}
    assert all(capabilities[k] == [] for k in capabilities), f"capabilities must all be empty: {capabilities}"


def test_no_secret_values_in_guidance_files():
    # IMPLICIT_SPEC invariant 2: secret env-var NAMES are mandated setup
    # content; their VALUES must be <placeholder> tokens or ${env:VAR}
    # references — never literals (advisor round 1: names != values).
    import re

    from bundle_facts import GUIDANCE_GLOBS, REPO_ROOT

    offenders = []
    # An occurrence is acceptable iff the value is a <placeholder> or a
    # ${env:VAR} reference — bare or quoted. A quoted plain literal (e.g.
    # "hunter2") is NOT acceptable: only env-ref indirection belongs in
    # guidance (plan: values must be placeholder tokens; review round 1).
    name_alt = "|".join(SECRET_ENV_VARS)
    occurrence_rx = re.compile(r"(?:" + name_alt + r")\s*[:=]\s*\S")
    env_ref = r"\$\{env:[^}\n]*\}"
    accept_rx = re.compile(
        r"(?:" + name_alt + r")\s*[:=]\s*("
        r'"(?:\$\{env:[^}\n]*\}|<[^>\n]*>)"'     # quoted env-ref or quoted <placeholder>
        r"|<[^>\n]*>"                            # bare <placeholder>
        r"|" + env_ref +                         # bare ${env:VAR}
        r")"
    )
    for pattern_glob in GUIDANCE_GLOBS:
        for path in sorted(REPO_ROOT.glob(pattern_glob)):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            for m in occurrence_rx.finditer(text):
                if accept_rx.match(text, m.start()):
                    continue
                line = text[: m.start()].count("\n") + 1
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{line}: {text[m.start():m.end()]}")
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
