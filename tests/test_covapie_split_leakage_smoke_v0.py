from __future__ import annotations

import ast
import hashlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import covapie_legacy_pipeline_retirement_policy as retirement
from covalent_ext import covapie_split_leakage_smoke as legacy


LEGACY_ROOT = Path("data/derived/covalent_small/covapie_split_leakage_smoke_v0")
SUCCESSOR_ROOT = Path("data/derived/covalent_small/covapie_unified_leakage_split_materialization_smoke_v0")
SUCCESSOR_MANIFEST = SUCCESSOR_ROOT / "covapie_unified_leakage_split_materialization_smoke_manifest.json"
CHECK_SCRIPT = Path("scripts/check_covapie_split_leakage_smoke_v0.py")
MODULE_PATH = Path("src/covalent_ext/covapie_split_leakage_smoke.py")
RAW_ROOT = Path("data/raw/covalent_sources")
STEP14AR_FILES = (
    Path("data/derived/covalent_small/covapie_final_dataset_materialization_smoke_v0"),
    Path("docs/covapie_final_dataset_materialization_smoke_v0_summary.md"),
    Path("scripts/check_covapie_final_dataset_materialization_smoke_v0.py"),
    Path("src/covalent_ext/covapie_final_dataset_materialization_smoke.py"),
    Path("tests/test_covapie_final_dataset_materialization_smoke_v0.py"),
)

EXPECTED_STAGE = "covapie_split_leakage_smoke_v0"
EXPECTED_SUCCESSOR_STAGE = "covapie_unified_leakage_split_materialization_smoke_v0"
EXPECTED_SUCCESSOR_MANIFEST = SUCCESSOR_MANIFEST.as_posix()
EXPECTED_NEXT_STEP = "covapie_unified_leakage_split_materialization_smoke"
EXPECTED_SUCCESS_LINE = "covapie_split_leakage_smoke_v0_retirement_policy_passed"
OLD_SUCCESS_LINE = "covapie_split_leakage_smoke_v0_passed"
EXPECTED_ERROR_MESSAGE = (
    f"legacy_stage_retired:{EXPECTED_STAGE}:"
    f"superseded_by={EXPECTED_SUCCESSOR_STAGE}:"
    f"recommended_next_step={EXPECTED_NEXT_STEP}"
)
ENTRYPOINT_ARGS: dict[str, tuple[object, ...]] = {
    "build_parent_event_group_integrity_rows": ([],),
    "build_candidate_metadata_group_integrity_rows": ([],),
}


def _tree_hash(paths: tuple[Path, ...]) -> str:
    digest = hashlib.sha256()
    for relative in paths:
        absolute = REPO_ROOT / relative
        candidates = [absolute] if absolute.is_file() else sorted(absolute.rglob("*"))
        for path in candidates:
            if path.is_file():
                digest.update(path.relative_to(REPO_ROOT).as_posix().encode())
                digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def _run_check() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, CHECK_SCRIPT.as_posix()],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _invoke(name: str) -> None:
    function: Callable[..., object] = getattr(legacy, name)
    function(*ENTRYPOINT_ARGS.get(name, ()))


def _raw_git_state() -> tuple[str, str]:
    tracked = subprocess.run(
        ["git", "ls-files", RAW_ROOT.as_posix()],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        check=False,
    ).stdout
    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", RAW_ROOT.as_posix()],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        check=False,
    ).stdout
    return tracked, staged


def test_legacy_stage_and_stage_alias_are_exact() -> None:
    assert legacy.LEGACY_STAGE == EXPECTED_STAGE
    assert legacy.STAGE == EXPECTED_STAGE


def test_guarded_entrypoint_inventory_is_explicit_and_complete() -> None:
    assert legacy.GUARDED_ENTRYPOINTS
    assert legacy.GUARDED_ENTRYPOINTS[-1] == "run_covapie_split_leakage_smoke_v0"
    assert len(legacy.GUARDED_ENTRYPOINTS) == len(set(legacy.GUARDED_ENTRYPOINTS))


def test_retirement_policy_matches_registry() -> None:
    assert legacy.build_retirement_policy() == (
        retirement.build_legacy_stage_retirement_policy(EXPECTED_STAGE)
    )


def test_retirement_and_execution_flags_are_exact() -> None:
    policy = legacy.build_retirement_policy()
    assert policy.legacy_stage_retired is True
    assert policy.legacy_stage_executable is False


def test_successor_contract_is_exact() -> None:
    policy = legacy.build_retirement_policy()
    assert policy.superseded_by_stage == EXPECTED_SUCCESSOR_STAGE
    assert policy.successor_availability == "tracked"
    assert policy.superseded_by_manifest_path == EXPECTED_SUCCESSOR_MANIFEST
    assert policy.recommended_next_step == EXPECTED_NEXT_STEP


def test_training_boundary_is_closed() -> None:
    policy = legacy.build_retirement_policy()
    assert policy.ready_for_training is False
    assert policy.ready_to_train_now is False
    assert policy.feature_semantics_audit_required_before_training is True


def test_historical_artifact_contract_is_read_only() -> None:
    policy = legacy.build_retirement_policy()
    assert policy.historical_artifacts_read_only is True
    assert policy.legacy_artifact_regeneration_forbidden is True
    assert policy.blocking_reasons == ("legacy_stage_superseded",)


def test_main_legacy_producer_fails_closed() -> None:
    with pytest.raises(retirement.LegacyStageRetiredError):
        _invoke("run_covapie_split_leakage_smoke_v0")


@pytest.mark.parametrize("entrypoint", legacy.GUARDED_ENTRYPOINTS)
def test_all_guarded_entrypoints_fail_closed(entrypoint: str) -> None:
    with pytest.raises(retirement.LegacyStageRetiredError):
        _invoke(entrypoint)


def test_guard_exception_attributes_and_message_are_exact() -> None:
    with pytest.raises(retirement.LegacyStageRetiredError) as caught:
        _invoke("run_covapie_split_leakage_smoke_v0")
    error = caught.value
    assert error.stage == EXPECTED_STAGE
    assert error.superseded_by_stage == EXPECTED_SUCCESSOR_STAGE
    assert error.successor_availability == "tracked"
    assert error.recommended_next_step == EXPECTED_NEXT_STEP
    assert error.blocking_reasons == ("legacy_stage_superseded",)
    assert str(error) == EXPECTED_ERROR_MESSAGE


def test_guard_message_is_deterministic() -> None:
    messages = []
    for _ in range(2):
        with pytest.raises(retirement.LegacyStageRetiredError) as caught:
            _invoke("run_covapie_split_leakage_smoke_v0")
        messages.append(str(caught.value))
    assert messages == [EXPECTED_ERROR_MESSAGE, EXPECTED_ERROR_MESSAGE]


def test_guards_are_first_executable_statements() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for name in legacy.GUARDED_ENTRYPOINTS:
        first = functions[name].body[0]
        assert isinstance(first, ast.Expr), name
        assert isinstance(first.value, ast.Call), name
        assert isinstance(first.value.func, ast.Name), name
        assert first.value.func.id == "raise_legacy_stage_retired", name
        assert isinstance(first.value.args[0], ast.Name), name
        assert first.value.args[0].id == "LEGACY_STAGE", name


def test_guards_precede_all_filesystem_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected(*args: object, **kwargs: object) -> object:
        raise AssertionError("legacy filesystem read reached")

    for name in (
        "_csv_rows",
        "_load_json",
        "_metadata_hash",
        "_raw_files_tracked",
        "_raw_files_staged",
        "_path_diff_exists",
    ):
        monkeypatch.setattr(legacy, name, unexpected)
    for entrypoint in legacy.GUARDED_ENTRYPOINTS:
        with pytest.raises(retirement.LegacyStageRetiredError):
            _invoke(entrypoint)


def test_guards_and_check_precede_all_filesystem_writes() -> None:
    text = CHECK_SCRIPT.read_text(encoding="utf-8")
    for forbidden in (
        "write_text",
        "write_bytes",
        "open(",
        "mkdir",
        "csv.DictWriter",
        "json.dump",
    ):
        assert forbidden not in text
    with pytest.raises(retirement.LegacyStageRetiredError):
        _invoke("run_covapie_split_leakage_smoke_v0")


def test_module_import_has_no_artifact_io() -> None:
    guarded = (LEGACY_ROOT, SUCCESSOR_ROOT, *STEP14AR_FILES)
    before = _tree_hash(guarded)
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(SRC_ROOT), environment.get("PYTHONPATH", "")]
    )
    result = subprocess.run(
        [sys.executable, "-c", "import covalent_ext.covapie_split_leakage_smoke"],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    after = _tree_hash(guarded)
    assert result.returncode == 0, result.stdout + result.stderr
    assert before == after


def test_retirement_check_exits_zero_and_reports_success() -> None:
    result = _run_check()
    assert result.returncode == 0, result.stdout + result.stderr
    assert EXPECTED_SUCCESS_LINE in result.stdout
    assert f"legacy_stage={EXPECTED_STAGE}" in result.stdout
    assert f"successor_stage={EXPECTED_SUCCESSOR_STAGE}" in result.stdout
    assert "successor_manifest_path_validation_passed=true" in result.stdout
    assert "ready_for_training=false" in result.stdout
    assert "feature_semantics_audit_required_before_training=true" in result.stdout


def test_check_does_not_call_old_producer_or_report_old_success() -> None:
    text = CHECK_SCRIPT.read_text(encoding="utf-8")
    assert "run_covapie_split_leakage_smoke_v0" not in text
    result = _run_check()
    assert result.returncode == 0, result.stdout + result.stderr
    assert OLD_SUCCESS_LINE not in result.stdout


def test_check_contains_no_write_mkdir_or_subprocess() -> None:
    text = CHECK_SCRIPT.read_text(encoding="utf-8")
    for forbidden in ("write_text", "write_bytes", "open(", "mkdir", "subprocess"):
        assert forbidden not in text


def test_historical_root_is_evidence_only_and_unchanged() -> None:
    manifest_path = LEGACY_ROOT / legacy.MANIFEST_JSON.name
    historical = __import__("json").loads(
        (REPO_ROOT / manifest_path).read_text(encoding="utf-8")
    )
    before = _tree_hash((LEGACY_ROOT,))
    result = _run_check()
    after = _tree_hash((LEGACY_ROOT,))
    assert result.returncode == 0, result.stdout + result.stderr
    assert historical["stage"] == EXPECTED_STAGE
    assert legacy.build_retirement_policy().legacy_stage_executable is False
    assert before == after


def test_successor_manifest_exists_regular_and_non_symlink() -> None:
    path = REPO_ROOT / SUCCESSOR_MANIFEST
    assert path.exists()
    assert path.is_file()
    assert not path.is_symlink()


def test_successor_root_is_unchanged_by_check() -> None:
    before = _tree_hash((SUCCESSOR_ROOT,))
    result = _run_check()
    after = _tree_hash((SUCCESSOR_ROOT,))
    assert result.returncode == 0, result.stdout + result.stderr
    assert before == after


def test_step14ar_files_are_unchanged_by_check() -> None:
    before = _tree_hash(STEP14AR_FILES)
    result = _run_check()
    after = _tree_hash(STEP14AR_FILES)
    assert result.returncode == 0, result.stdout + result.stderr
    assert before == after


def test_raw_state_is_unchanged_and_check_has_no_raw_access() -> None:
    before = _raw_git_state()
    result = _run_check()
    after = _raw_git_state()
    assert result.returncode == 0, result.stdout + result.stderr
    assert before == after == ("", "")
    assert "data/raw" not in CHECK_SCRIPT.read_text(encoding="utf-8")


def test_two_check_runs_are_deterministic() -> None:
    first = _run_check()
    second = _run_check()
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout
    assert first.stderr == second.stderr


def test_shared_step14aq_successor_path_is_exact() -> None:
    policies = {
        item.stage: item
        for item in retirement.build_all_legacy_stage_retirement_policies()
    }
    assert (
        policies["covapie_split_leakage_smoke_v0"].superseded_by_manifest_path
        == policies["covapie_split_leakage_qa_gate_v0"].superseded_by_manifest_path
        == EXPECTED_SUCCESSOR_MANIFEST
    )


def test_shared_step14aq_stage_set_is_exact() -> None:
    assert retirement.EXPECTED_SHARED_SUCCESSOR_MANIFEST_REFERENCES == {
        EXPECTED_SUCCESSOR_MANIFEST: (
            "covapie_split_leakage_smoke_v0",
            "covapie_split_leakage_qa_gate_v0",
        )
    }


def test_registry_allows_only_one_shared_manifest_group() -> None:
    policies = retirement.build_all_legacy_stage_retirement_policies()
    grouped: dict[str, list[str]] = {}
    for item in policies:
        if item.successor_availability == "tracked":
            grouped.setdefault(str(item.superseded_by_manifest_path), []).append(item.stage)
    shared = {path: tuple(stages) for path, stages in grouped.items() if len(stages) > 1}
    assert shared == retirement.EXPECTED_SHARED_SUCCESSOR_MANIFEST_REFERENCES


def test_check_does_not_copy_or_generate_step14aq_manifest() -> None:
    before = _tree_hash((SUCCESSOR_ROOT,))
    before_manifests = tuple(
        sorted(SUCCESSOR_ROOT.glob("*materialization_smoke_manifest.json"))
    )
    result = _run_check()
    after = _tree_hash((SUCCESSOR_ROOT,))
    after_manifests = tuple(
        sorted(SUCCESSOR_ROOT.glob("*materialization_smoke_manifest.json"))
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert before == after
    assert before_manifests == after_manifests == (SUCCESSOR_MANIFEST,)
    assert "shared_step14aq_successor_manifest_contract_passed=true" in result.stdout
