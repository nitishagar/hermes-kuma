import jsonschema

from bundle_facts import PLUGIN_SCHEMA_URL, REPO_ROOT, load_json

plugin = load_json(REPO_ROOT / "plugin.json")
plugin_schema = load_json(REPO_ROOT / "tests/schemas/plugin.schema.json")


def test_plugin_json_conforms_to_published_schema():
    jsonschema.Draft202012Validator.check_schema(plugin_schema)
    errors = sorted(
        jsonschema.Draft202012Validator(plugin_schema).iter_errors(plugin),
        key=lambda e: e.json_path,
    )
    assert not errors, "\n".join(f"{e.json_path}: {e.message}" for e in errors)


def test_plugin_json_stays_inside_the_closed_property_set():
    # IMPLICIT_SPEC invariant 1: requires_env and friends are schema-illegal
    # for bundles; the closed schema enforces it, this names it for humans.
    allowed = {
        "$schema", "name", "version", "description", "author",
        "homepage", "repository", "license", "keywords", "extensions",
    }
    unknown = set(plugin) - allowed
    assert not unknown, f"properties outside the closed v1.0.0 set: {sorted(unknown)}"


def test_name_fits_manifest_rules():
    import re

    name = plugin["name"]
    assert 1 <= len(name) <= 64, f"manifest name length {len(name)} outside 1..64"
    assert re.fullmatch(r"[a-z0-9-.]+", name), f"manifest name {name!r} has illegal characters"
    assert "--" not in name and ".." not in name, f"manifest name {name!r} contains '--' or '..'"


def test_license_is_mit():
    assert plugin.get("license") == "MIT"


def test_repository_points_at_nitishagar_hermes_kuma():
    assert plugin.get("repository", "").rstrip("/") == "https://github.com/nitishagar/hermes-kuma"


def test_schema_declares_canonical_v1_url():
    assert plugin["$schema"] == PLUGIN_SCHEMA_URL
