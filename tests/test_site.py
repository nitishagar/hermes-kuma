"""Static docs-site checks (site/ -> GitHub Pages at kuma.applair.in).

The site is dependency-free static HTML+CSS (no JS: the no-runtime-code
invariant forbids .js outside tests/CI). These checks run in the offline
suite and gate the pages deploy: required files, CNAME, internal-link and
anchor integrity, and a no-secret-values sweep of site content.
"""

import re
from html.parser import HTMLParser
from pathlib import Path

from bundle_facts import REPO_ROOT, SECRET_ENV_VARS

SITE = REPO_ROOT / "site"
REQUIRED_PAGES = ["index.html", "install.html", "credentials.html", "skills.html"]
EXPECTED_CNAME = "kuma.applair.in"


class _LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if attrs.get("id"):
            self.ids.add(attrs["id"])


def _parse(page: Path):
    collector = _LinkCollector()
    collector.feed(page.read_text(encoding="utf-8"))
    return collector


def test_site_pages_and_assets_exist():
    for name in REQUIRED_PAGES:
        assert (SITE / name).is_file(), f"site/{name} missing"
    assert (SITE / "assets" / "style.css").is_file(), "site/assets/style.css missing"
    assert (SITE / "CNAME").read_text(encoding="utf-8").strip() == EXPECTED_CNAME


def test_site_has_no_executable_content():
    # The no-runtime-code invariant (test_no_runtime_code_shipped) already
    # forbids .js repo-wide; this pins the site to the static subset and
    # guards against inline <script> regressing the deploy shape.
    for path in sorted(SITE.rglob("*")):
        if path.is_file():
            assert path.suffix.lower() in {".html", ".css", ""}, f"unexpected site file: {path.name}"
            if path.suffix.lower() == ".html":
                assert "<script" not in path.read_text(encoding="utf-8").lower(), f"inline script in {path.name}"


def test_site_internal_links_and_anchors_resolve():
    parsed = {name: _parse(SITE / name) for name in REQUIRED_PAGES}
    for name, collector in parsed.items():
        for href in collector.links:
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            target, _, fragment = href.partition("#")
            target_page = SITE / (target or name)
            assert target_page.is_file(), f"{name}: dead link to {href}"
            if fragment and target_page.suffix == ".html":
                key = target or name
                assert fragment in parsed[key].ids, f"{name}: dead anchor #{fragment}"


def test_site_pages_share_nav_and_titles():
    for name in REQUIRED_PAGES:
        text = (SITE / name).read_text(encoding="utf-8")
        for nav in REQUIRED_PAGES:
            assert f'href="{nav}"' in text, f"{name}: nav missing link to {nav}"
        assert re.search(r"<title>[^<]{8,}</title>", text), f"{name}: missing/empty <title>"
        assert '<meta name="viewport"' in text, f"{name}: missing viewport meta"


def test_site_has_no_secret_values():
    # Secret env-var NAMES are documented setup content; VALUES must never
    # appear. Placeholders (<...>, ${env:...}, ..., example hostnames) pass.
    offenders = []
    for page in [SITE / name for name in REQUIRED_PAGES]:
        for lineno, line in enumerate(page.read_text(encoding="utf-8").splitlines(), 1):
            for var in SECRET_ENV_VARS:
                for match in re.finditer(rf"{var}\s*[:=]\s*(\S+)", line):
                    value = match.group(1).strip("\"'")
                    if value and not value.startswith(("<", "${", "...", "http")) and value != "...":
                        offenders.append(f"{page.name}:{lineno}: {var}={value}")
    assert not offenders, "literal secret values in site:\n" + "\n".join(offenders)
