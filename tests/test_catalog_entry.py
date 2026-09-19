"""Catalog-entry template validated by the vendored upstream checker.

The real catalog validator requires a 40-hex sha, which can only exist after
the release tag. So the test substitutes a synthetic sha into a tempdir copy
and runs the vendored checker — everything else is validated exactly as the
catalog CI will (IMPLICIT_SPEC invariant 15).
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from bundle_facts import REPO_ROOT

TEMPLATE = REPO_ROOT / "docs/catalog-entry.yaml.template"
VENDORED_CHECKER = REPO_ROOT / "tests/vendor/validate_plugin_catalog.py"
SYNTHETIC_SHA = "a" * 40  # shape-valid; only the shape is checked offline


def test_catalog_template_passes_upstream_validator():
    template_text = TEMPLATE.read_text(encoding="utf-8")
    assert "fill before PR" in template_text, "template lost its fill-me guidance"
    with tempfile.TemporaryDirectory() as tmp:
        catalog_dir = Path(tmp) / "plugin-catalog"
        catalog_dir.mkdir()
        entry = template_text.replace(
            "<40-hex commit SHA of the release tag — fill before PR>", SYNTHETIC_SHA
        )
        assert SYNTHETIC_SHA in entry, "sha substitution failed — template placeholder changed?"
        (catalog_dir / "hermes-kuma.yaml").write_text(entry, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(VENDORED_CHECKER), str(catalog_dir)],
            capture_output=True,
            text=True,
            timeout=60,
        )
    assert result.returncode == 0, (
        f"upstream validator rejected the entry:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
