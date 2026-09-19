# Vendored oracles

- `plugin.schema.json`, `mcp.schema.json` — the published Agent Plugins v1.0.0
  JSON Schemas, fetched 2026-09-19 from their canonical URLs
  (`https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`,
  `https://agent-plugins.org/schemas/1.0.0/mcp.schema.json`). Vendored so the
  suite runs offline; each copy keeps its canonical `$id`, asserted by
  `tests/test_bundle.py`. The v1.0.0 spec is frozen; re-vendor deliberately
  if a v2 ever appears.
- `../vendor/validate_plugin_catalog.py` — the catalog-entry checker from
  `NousResearch/hermes-agent` (`scripts/validate_plugin_catalog.py`, MIT),
  with its own provenance note.
- `../fixtures/tools.json` — the pinned upstream server's tool inventory with
  provenance.
