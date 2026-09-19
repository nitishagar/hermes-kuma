"""Skill conformance + content tests (IMPLICIT_SPEC invariants 6-11, 13, 14)."""

import re
from pathlib import Path

import pytest

from bundle_facts import (
    ALERTING_LINE,
    ENV_FLOW_LINE,
    HTTP_WARNING_LINE,
    MAINTENANCE_SKILL,
    MCP_UNAVAILABLE_HEADING,
    NO_DESTRUCTIVE_LINE,
    READ_FIRST_LINE,
    REPO_ROOT,
    SETUP_SKILL,
    TROUBLESHOOT_HEADING,
    V2_LINE,
    WRITE_CONFIRM_LINE,
    load_skill_frontmatter,
    load_tools,
)

SKILLS_DIR = REPO_ROOT / "skills"
SKILL_NAMES = sorted(p.name for p in SKILLS_DIR.iterdir() if p.is_dir())

tools = load_tools()
WRITE_TOOLS = sorted(t["name"] for t in tools["tools"] if t["class"] == "write")
DESTRUCTIVE_TOOLS = sorted(t["name"] for t in tools["tools"] if t["class"] == "destructive")
# The only write tools any skill may instruct (IMPLICIT_SPEC invariant 7).
SANCTIONED_WRITES = {"pauseMonitor", "resumeMonitor", "createMaintenance"}


def _skill_text(name: str) -> str:
    return (SKILLS_DIR / name / "SKILL.md").read_text(encoding="utf-8")


def test_expected_skill_set_is_present():
    # The plan pins four skills; a missing or surprise skill is a plan mismatch.
    assert SKILL_NAMES == ["kuma-incident-review", "kuma-maintenance", "kuma-setup", "kuma-status-digest"]


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_frontmatter_name_matches_directory(name: str):
    fm = load_skill_frontmatter(SKILLS_DIR / name / "SKILL.md")
    assert fm.get("name") == name, f"frontmatter name {fm.get('name')!r} != directory {name!r}"


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_frontmatter_name_shape(name: str):
    fm = load_skill_frontmatter(SKILLS_DIR / name / "SKILL.md")
    skill_name = fm.get("name", "")
    assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", skill_name or "") and len(skill_name) <= 64, (
        f"{name}: frontmatter name {skill_name!r} must be lowercase-alnum hyphen-separated, <=64 chars"
    )


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_frontmatter_description_required_and_bounded(name: str):
    fm = load_skill_frontmatter(SKILLS_DIR / name / "SKILL.md")
    description = fm.get("description")
    assert isinstance(description, str) and description.strip(), (
        f"{name}: description is missing or empty (agentskills requires 1..1024 chars)"
    )
    assert len(description) <= 1024, f"{name}: description is {len(description)} chars (> 1024)"


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_frontmatter_has_no_unknown_keys(name: str):
    fm = load_skill_frontmatter(SKILLS_DIR / name / "SKILL.md")
    unknown = set(fm) - {"name", "description"} - {"license", "allowed-tools", "metadata"}
    assert not unknown, f"{name}: unknown frontmatter keys {sorted(unknown)}"


# --- Per-role pinned strings (PLAN.md "Approach": roles, not one-size) ---


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_read_first_line(name: str):
    # Invariant 7: read-first discipline stated everywhere.
    assert READ_FIRST_LINE in _skill_text(name), f"{name}: missing pinned read-first line"


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_degradation_section(name: str):
    # Invariant 13: skills stay useful without the MCP surface.
    text = _skill_text(name)
    assert MCP_UNAVAILABLE_HEADING in text, f"{name}: missing {MCP_UNAVAILABLE_HEADING!r}"
    after = text.split(MCP_UNAVAILABLE_HEADING, 1)[1]
    body = after.split("\n## ", 1)[0]
    guidance = [line for line in body.splitlines() if line.strip().startswith(("-", "1.", "2.", "3."))]
    assert len(guidance) >= 3, f"{name}: degradation section needs >=3 guidance bullets, got {len(guidance)}"


def test_setup_only_content():
    # Invariants 8, 9, 11, 12, 14: the heavy guidance lives in kuma-setup.
    text = _skill_text(SETUP_SKILL)
    for pinned in (NO_DESTRUCTIVE_LINE, ENV_FLOW_LINE, HTTP_WARNING_LINE, V2_LINE, ALERTING_LINE):
        assert pinned in text, f"{SETUP_SKILL}: missing pinned line: {pinned[:60]}..."
    assert TROUBLESHOOT_HEADING in text, f"{SETUP_SKILL}: missing {TROUBLESHOOT_HEADING!r}"
    ladder = text.split(TROUBLESHOOT_HEADING, 1)[1].split("\n## ", 1)[0]
    steps = [line for line in ladder.splitlines() if line.strip().startswith(("1.", "2.", "3.", "4.", "5."))]
    assert len(steps) >= 4, f"{SETUP_SKILL}: troubleshooting ladder needs >=4 numbered steps, got {len(steps)}"
    # Invariant 10: the ladder must distinguish the failure modes, not just
    # have steps — each step names a different root cause (review round 1).
    lowered = ladder.lower()
    for term in ("node", "npx", "uptime_kuma_url", "authinvalidtoken"):
        assert term in lowered, f"{SETUP_SKILL}: troubleshooting ladder omits failure mode {term!r}"
    for other in (n for n in SKILL_NAMES if n != SETUP_SKILL):
        other_text = _skill_text(other)
        for pinned in (NO_DESTRUCTIVE_LINE, ENV_FLOW_LINE, HTTP_WARNING_LINE):
            assert pinned not in other_text, f"{other}: duplicates setup-only content"


def test_write_confirm_line_in_maintenance_only():
    # Invariant 7: the confirmation gate is the maintenance skill's core rule.
    assert WRITE_CONFIRM_LINE in _skill_text(MAINTENANCE_SKILL), (
        f"{MAINTENANCE_SKILL}: missing pinned write-confirm line"
    )


# --- Tool discipline (invariants 7 and 8), driven by the vendored inventory ---


def test_destructive_tools_named_only_in_setup_prohibition():
    # Invariant 8: the 5 delete tools appear only inside kuma-setup's
    # prohibition line — named as forbidden, never instructed.
    for tool in DESTRUCTIVE_TOOLS:
        for name in SKILL_NAMES:
            text = _skill_text(name)
            occurrences = text.count(tool)
            if name == SETUP_SKILL:
                assert occurrences == 1 and tool in NO_DESTRUCTIVE_LINE, (
                    f"{SETUP_SKILL}: {tool} must appear exactly once, inside the prohibition line"
                )
            else:
                assert occurrences == 0, f"{name}: names destructive tool {tool}"


def test_unsanctioned_write_tools_never_appear():
    # Invariant 8: the 10 non-sanctioned write tools are out of scope for all
    # skills; routing to the Kuma UI is the correct answer for those.
    for tool in WRITE_TOOLS:
        if tool in SANCTIONED_WRITES:
            continue
        for name in SKILL_NAMES:
            assert tool not in _skill_text(name), f"{name}: names out-of-scope write tool {tool}"


def test_sanctioned_writes_instructed_only_in_maintenance():
    # Invariant 7: the three sanctioned write tool names are instructed only
    # by kuma-maintenance (setup mentions them as prose, not tool calls).
    for tool in sorted(SANCTIONED_WRITES):
        for name in SKILL_NAMES:
            count = _skill_text(name).count(tool)
            if name == MAINTENANCE_SKILL:
                assert count >= 1, f"{MAINTENANCE_SKILL}: never explains {tool}"
            else:
                assert count == 0, f"{name}: instructs sanctioned write {tool}"
