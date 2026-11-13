"""Pins the root config: ignore entries, local-only pre-commit hooks, workbench.json keys."""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIRS = [".claude", ".github", ".cursor", ".codex", ".gemini", ".agents"]
RUNTIME = [
    "scheduled_tasks.lock",
    "scheduled_tasks.json",
    "routines/.state/",
    "checkpoints/",
    "mailbox/",
    "agent-registry.json",
    "agent-memory-local",
    "first-run",
    "assistant-daemon-state.json",
]
ACCEPTED_KEYS = {"refRunners", "suites", "deploy", "overlapIgnore"}


def _ignore() -> set[str]:
    lines = (ROOT / ".gitignore").read_text().splitlines()
    return {x.strip() for x in lines if x.strip() and not x.startswith("#")}


def _tracked(path: str) -> bool:
    out = subprocess.run(
        ["git", "ls-files", path], cwd=ROOT, capture_output=True, text=True, check=True
    )
    return bool(out.stdout.strip())


def test_gitignore_base_entries():
    entries = _ignore()
    for e in [
        "__pycache__/", "*.pyc", ".pytest_cache/", ".ruff_cache/", ".venv/",
        "node_modules/", ".DS_Store", ".env", ".env.*", "!.env.example", ".logs/", ".scratchpad/",
        ".worktrees/", "**/.claude/settings.local.json", "docs/plans/index.json",
        "docs/plans/facts.md", "docs/research/", "docs/handoffs/",
    ]:  # fmt: skip
        assert e in entries, e


def test_gitignore_per_config_dir_and_runtime():
    entries = _ignore()
    for d in CONFIG_DIRS:
        assert f"{d}/worktrees/" in entries
        assert f"{d}/settings.local.json" in entries
        assert f"{d}/harness.json" in entries or f"{d}/.harness-owned.json" in entries
    for r in RUNTIME:
        assert f".claude/{r}" in entries, r


def test_gitignore_has_no_superpowers_and_plugin_gitignore_retired():
    assert not any("superpowers" in e for e in _ignore())
    assert not _tracked("plugins/workbench/.gitignore")


def test_precommit_is_local_only():
    # Stdlib only (the template ships no PyYAML): every hook is a one-line flow mapping.
    text = (ROOT / ".pre-commit-config.yaml").read_text()
    repos = re.findall(r"^\s*-\s*repo:\s*(\S+)", text, re.M)
    assert repos and all(r == "local" for r in repos), repos
    hooks = re.findall(r"^\s*-\s*\{(.*)\}\s*$", text, re.M)
    assert hooks
    ids = set()
    for h in hooks:
        fields = dict(re.findall(r"(\w+):\s*([^,]+?)\s*(?:,|$)", h))
        assert fields.get("language") == "system", h
        ids.add(fields["id"])
    for want in [
        "trailing-whitespace", "end-of-file-fixer", "check-yaml", "check-json",
        "check-toml", "check-merge-conflict", "check-added-large-files",
        "ruff", "ruff-format", "shellcheck",
    ]:  # fmt: skip
        assert want in ids, want


def test_shellcheckrc():
    assert "disable=SC1090,SC1091" in (ROOT / ".shellcheckrc").read_text()


def test_workbench_config_keys():
    cfg = json.loads((ROOT / ".claude/workbench.json").read_text())
    assert set(cfg) <= ACCEPTED_KEYS
    assert "harness" not in cfg
    # refRunners stays a live key (init writes it); the node workflow tests it mapped are gone
    assert cfg.get("refRunners") == {}
    assert not _tracked("plugins/workbench/.claude/workbench.json")


def test_gitignore_entries():
    test_gitignore_base_entries()
    test_gitignore_per_config_dir_and_runtime()
    test_gitignore_has_no_superpowers_and_plugin_gitignore_retired()
    assert "uv.lock" not in _ignore()


def _conftest():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "tests_conftest", ROOT / "scripts/tests/conftest.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_template_marker_registered_and_noop_in_template(request):
    markers = request.config.getini("markers")
    assert any(m.startswith("template") for m in markers)
    conf = _conftest()
    tagged = [i for i in request.session.items if i.get_closest_marker("template")]
    assert all(i.nodeid in conf.TEMPLATE_ONLY for i in tagged)
    skipped = [i for i in tagged if any(m.args[0] for m in i.iter_markers("skipif"))]
    if conf.is_initialised(ROOT):
        assert len(skipped) == len(tagged)
    else:
        assert not skipped  # the marker never skips anything in the uninitialised template


def test_template_only_ids_all_exist():
    conf = _conftest()
    out = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.splitlines()  # fmt: skip
    collected = {x for x in out if "::" in x}
    assert conf.stale_ids(collected, conf.TEMPLATE_ONLY) == []
    assert conf.stale_ids(collected, ["scripts/tests/test_root_config.py::nope"]) == [
        "scripts/tests/test_root_config.py::nope"
    ]


def test_slow_marker_registered_and_deselected_by_default(request):
    markers = request.config.getini("markers")
    assert any(m.startswith("slow") for m in markers)
    body = (ROOT / "mise-tasks/test/scripts").read_text()
    assert 'pytest scripts/tests -m "not slow"' in body
