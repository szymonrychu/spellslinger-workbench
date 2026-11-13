"""Root conftest: the `template` marker skips template-only tests once the workbench is initialised.

The marker is applied centrally from TEMPLATE_ONLY, so no test file is edited. In the
uninitialised template it skips nothing. A listed id that names no collected test fails
collection, so the list cannot rot.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "init_engine"))

from project_files import is_initialised  # noqa: E402

TEMPLATE_ONLY = [
    "scripts/tests/e2e/test_instantiate.py::test_init_leaves_clean_green_tree",
    "scripts/tests/e2e/test_instantiate.py::test_adopt_existing_repo",
    "scripts/tests/e2e/test_instantiate.py::test_component_add_remove",
    "scripts/tests/e2e/test_instantiate.py::test_new_init_leaves_green_tree",
    "scripts/tests/e2e/test_instantiate.py::test_adopt_leaves_green_tree",
    "scripts/tests/e2e/test_instantiate.py::test_second_component_add_stays_green",
    "scripts/tests/e2e/test_instantiate.py::test_suite_green_on_initialised_copy",
    "scripts/tests/e2e/test_harness_targets.py::test_each_target_roundtrip[copilot]",
    "scripts/tests/e2e/test_harness_targets.py::test_each_target_roundtrip[cursor]",
    "scripts/tests/e2e/test_harness_targets.py::test_each_target_roundtrip[codex]",
    "scripts/tests/e2e/test_harness_targets.py::test_each_target_roundtrip[gemini]",
    "scripts/tests/e2e/test_harness_targets.py::test_each_target_roundtrip[antigravity]",
    "scripts/tests/e2e/test_harness_targets.py::test_generated_hooks_deny[copilot]",
    "scripts/tests/e2e/test_harness_targets.py::test_generated_hooks_deny[cursor]",
    "scripts/tests/e2e/test_harness_targets.py::test_generated_hooks_deny[codex]",
    "scripts/tests/e2e/test_harness_targets.py::test_generated_hooks_deny[gemini]",
    "scripts/tests/e2e/test_harness_targets.py::test_generated_hooks_deny[antigravity]",
    "scripts/tests/e2e/test_harness_targets.py::test_config_dir_migration_roundtrip[copilot]",
    "scripts/tests/e2e/test_harness_targets.py::test_config_dir_migration_roundtrip[cursor]",
    "scripts/tests/e2e/test_harness_targets.py::test_config_dir_migration_roundtrip[codex]",
    "scripts/tests/e2e/test_harness_targets.py::test_config_dir_migration_roundtrip[gemini]",
    "scripts/tests/e2e/test_harness_targets.py::test_config_dir_migration_roundtrip[antigravity]",
    "scripts/tests/e2e/test_harness_targets.py::test_clean_while_active_restores_tree",
    "scripts/tests/e2e/test_harness_targets.py::test_all_targets",
    "scripts/tests/e2e/test_template_update.py::test_init_leaves_no_template_docs",
    "scripts/tests/e2e/test_template_update.py::test_template_update_roundtrip",
    "scripts/tests/init_engine/test_finalize.py::test_marketplace_rename_and_packs",
    "scripts/tests/init_engine/test_finalize.py::test_no_pack_all_false",
    "scripts/tests/init_engine/test_finalize.py::test_template_history_cleared",
    "scripts/tests/init_engine/test_finalize.py::test_adopt_finalizes_and_rerun_is_idempotent",
    "scripts/tests/init_engine/test_finalize.py::test_facts_md_cleared",
    "scripts/tests/init_engine/test_finalize.py::test_license_missing_refuses_on_first_run",
    "scripts/tests/init_engine/test_finalize.py::test_license_options[none]",
    "scripts/tests/init_engine/test_finalize.py::test_license_holder_in_every_plugin",
    "scripts/tests/init_engine/test_finalize.py::test_license_default_holder_fallback",
    "scripts/tests/init_engine/test_finalize.py::test_owned_paths_retired_from_tracked_files",
    "scripts/tests/init_engine/test_project_files.py::test_missing_answers_become_ask_placeholders",
    "scripts/tests/init_engine/test_project_files.py::test_docs_reset",
    "scripts/tests/init_engine/test_refresh.py::test_refresh_refuses_an_uninitialised_workbench",
    "scripts/tests/init_engine/test_update.py::test_update_refuses_uninitialised",
    "scripts/tests/init_engine/test_update.py::test_update_backfills_allow_file",
    "scripts/tests/init_engine/test_update.py::test_update_modify_delete_on_owned_path_keeps_project_side",
    "scripts/tests/init_engine/test_update_conflicts.py::test_template_market_keys_renamed",
    "scripts/tests/init_engine/test_update_unrelated.py::test_base_flag_merges_unrelated_history",
    "scripts/tests/test_agents_md.py::test_block_order",
    "scripts/tests/test_agents_md.py::test_uninitialised_block",
    "scripts/tests/test_agents_md.py::test_template_maintenance",
    "scripts/tests/test_agents_md.py::test_marker_pairs_unique_and_ordered",
    "scripts/tests/test_agents_md.py::test_banner_routes_other_requests",
    "scripts/tests/test_check_personal.py::test_shipped_denylist_is_hashed_only",
    "scripts/tests/test_check_personal.py::test_shipped_tree_is_clean",
    "scripts/tests/test_check_personal.py::test_local_allow_file_only_adds",
    "scripts/tests/test_lint_personal_task.py::test_tracked_tree_passes_personal_lint",
    "scripts/tests/test_marketplace.py::test_marketplace_header",
    "scripts/tests/test_marketplace.py::test_project_settings_exact",
    "scripts/tests/test_root_stubs.py::test_gitmodules_is_not_tracked",
    "scripts/tests/test_root_stubs.py::test_memory_keeps_header_and_import_entry",
    "scripts/tests/test_root_stubs.py::test_architecture_stub_has_components_heading",
    "scripts/tests/test_root_stubs.py::test_license_mit_identical",
    "scripts/tests/test_root_tooling.py::test_task_families_and_markers",
    "scripts/tests/test_secret_scanning.py::test_lint_task_detects_and_tree_is_clean",
    "scripts/tests/test_secret_scanning.py::test_pinned_and_no_allowlist",
    "scripts/tests/test_secret_scanning.py::test_gitleaks_config_extends_default_with_no_allowlist",
]


def stale_ids(collected, listed) -> list[str]:
    """The listed ids that are absent from `collected`."""
    return [i for i in listed if i not in collected]


def pytest_collection_modifyitems(config, items):
    initialised = is_initialised(ROOT)
    listed = set(TEMPLATE_ONLY)
    seen = {i.nodeid for i in items}
    files = {i.nodeid.split("::", 1)[0] for i in items}
    # only ids whose file was collected can be judged: a targeted run collects fewer files
    stale = stale_ids(seen, [i for i in TEMPLATE_ONLY if i.split("::", 1)[0] in files])
    by_id = any("::" in a for a in config.args)
    targeted = config.option.keyword or config.option.markexpr or by_id
    if stale and not targeted:
        raise pytest.UsageError("TEMPLATE_ONLY names no collected test: " + ", ".join(stale))
    reason = "template-only: the workbench is initialised"
    for item in items:
        if item.nodeid in listed:
            item.add_marker(pytest.mark.template)
            item.add_marker(pytest.mark.skipif(initialised, reason=reason))
