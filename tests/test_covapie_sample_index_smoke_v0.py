from __future__ import annotations

import ast
import csv
import hashlib
import json
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
from covalent_ext import covapie_sample_index_smoke as smoke


LEGACY_ROOT = Path("data/derived/covalent_small/covapie_sample_index_smoke_v0")
SUCCESSOR_ROOT = Path(
    "data/derived/covalent_small/covapie_sample_index_materialization_smoke_v0"
)
SUCCESSOR_MANIFEST = (
    SUCCESSOR_ROOT / "covapie_sample_index_materialization_smoke_manifest.json"
)
STEP14AR_FILES = (
    Path("data/derived/covalent_small/covapie_final_dataset_materialization_smoke_v0"),
    Path("docs/covapie_final_dataset_materialization_smoke_v0_summary.md"),
    Path("scripts/check_covapie_final_dataset_materialization_smoke_v0.py"),
    Path("src/covalent_ext/covapie_final_dataset_materialization_smoke.py"),
    Path("tests/test_covapie_final_dataset_materialization_smoke_v0.py"),
)
RAW_ROOT = Path("data/raw/covalent_sources")
CHECK_SCRIPT = Path("scripts/check_covapie_sample_index_smoke_v0.py")
MODULE_PATH = Path("src/covalent_ext/covapie_sample_index_smoke.py")

EXPECTED_STAGE = "covapie_sample_index_smoke_v0"
EXPECTED_SUCCESSOR_STAGE = "covapie_sample_index_materialization_smoke_v0"
EXPECTED_SUCCESSOR_MANIFEST = SUCCESSOR_MANIFEST.as_posix()
EXPECTED_NEXT_STEP = "covapie_sample_index_materialization_smoke"
EXPECTED_ERROR_MESSAGE = (
    "legacy_stage_retired:covapie_sample_index_smoke_v0:"
    "superseded_by=covapie_sample_index_materialization_smoke_v0:"
    "recommended_next_step=covapie_sample_index_materialization_smoke"
)
GUARDED_ENTRYPOINTS = (
    "build_precondition_rows",
    "build_sample_index_rows",
    "build_row_qa_rows",
    "build_mask_distribution_rows",
    "build_source_traceability_rows",
    "build_boundary_rows",
    "build_git_safety_rows",
    "build_training_blocker_rows",
    "run_covapie_sample_index_smoke_v0",
)


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


def _git_paths(path: Path, *, cached: bool = False) -> tuple[str, ...]:
    command = ["git", "diff"]
    if cached:
        command.append("--cached")
    command.extend(["--name-only", "--", path.as_posix()])
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return tuple(line for line in result.stdout.splitlines() if line)


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
    function: Callable[..., object] = getattr(smoke, name)
    if name in {
        "build_row_qa_rows",
        "build_mask_distribution_rows",
        "build_source_traceability_rows",
    }:
        function([])
    else:
        function()


def test_legacy_stage_is_exact() -> None:
    assert smoke.LEGACY_STAGE == EXPECTED_STAGE


def test_historical_stage_alias_is_preserved() -> None:
    assert smoke.STAGE == smoke.LEGACY_STAGE


def test_build_retirement_policy_matches_registry() -> None:
    built = smoke.build_retirement_policy()
    registered = retirement.build_legacy_stage_retirement_policy(EXPECTED_STAGE)
    assert built == registered


def test_stage_is_retired() -> None:
    assert smoke.build_retirement_policy().legacy_stage_retired is True


def test_stage_is_not_executable() -> None:
    assert smoke.build_retirement_policy().legacy_stage_executable is False


def test_successor_stage_is_exact() -> None:
    assert (
        smoke.build_retirement_policy().superseded_by_stage
        == EXPECTED_SUCCESSOR_STAGE
    )


def test_successor_availability_is_tracked() -> None:
    assert smoke.build_retirement_policy().successor_availability == "tracked"


def test_successor_manifest_path_is_exact() -> None:
    assert (
        smoke.build_retirement_policy().superseded_by_manifest_path
        == EXPECTED_SUCCESSOR_MANIFEST
    )


def test_recommended_next_step_is_exact() -> None:
    assert smoke.build_retirement_policy().recommended_next_step == EXPECTED_NEXT_STEP


def test_training_readiness_is_false() -> None:
    policy = smoke.build_retirement_policy()
    assert policy.ready_for_training is False
    assert policy.ready_to_train_now is False


def test_feature_semantics_audit_remains_required() -> None:
    assert (
        smoke.build_retirement_policy().feature_semantics_audit_required_before_training
        is True
    )


def test_historical_artifacts_are_read_only() -> None:
    assert smoke.build_retirement_policy().historical_artifacts_read_only is True


def test_legacy_artifact_regeneration_is_forbidden() -> None:
    assert (
        smoke.build_retirement_policy().legacy_artifact_regeneration_forbidden
        is True
    )


def test_blocking_reason_is_exact() -> None:
    assert smoke.build_retirement_policy().blocking_reasons == (
        "legacy_stage_superseded",
    )


def test_main_legacy_producer_fails_closed() -> None:
    with pytest.raises(retirement.LegacyStageRetiredError):
        smoke.run_covapie_sample_index_smoke_v0()


@pytest.mark.parametrize("entrypoint", GUARDED_ENTRYPOINTS)
def test_every_public_legacy_entrypoint_fails_closed(entrypoint: str) -> None:
    with pytest.raises(retirement.LegacyStageRetiredError):
        _invoke(entrypoint)


def test_guard_exception_attributes_are_exact() -> None:
    with pytest.raises(retirement.LegacyStageRetiredError) as caught:
        smoke.run_covapie_sample_index_smoke_v0()
    error = caught.value
    assert error.stage == EXPECTED_STAGE
    assert error.superseded_by_stage == EXPECTED_SUCCESSOR_STAGE
    assert error.successor_availability == "tracked"
    assert error.recommended_next_step == EXPECTED_NEXT_STEP
    assert error.blocking_reasons == ("legacy_stage_superseded",)


def test_guard_exception_message_is_deterministic() -> None:
    messages = []
    for _ in range(2):
        with pytest.raises(retirement.LegacyStageRetiredError) as caught:
            smoke.run_covapie_sample_index_smoke_v0()
        messages.append(str(caught.value))
    assert messages == [EXPECTED_ERROR_MESSAGE, EXPECTED_ERROR_MESSAGE]


def test_guards_are_first_executable_statements() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert set(GUARDED_ENTRYPOINTS).issubset(functions)
    for name in GUARDED_ENTRYPOINTS:
        first = functions[name].body[0]
        assert isinstance(first, ast.Expr), name
        assert isinstance(first.value, ast.Call), name
        assert isinstance(first.value.func, ast.Name), name
        assert first.value.func.id == "raise_legacy_stage_retired", name
        assert len(first.value.args) == 1
        assert isinstance(first.value.args[0], ast.Name)
        assert first.value.args[0].id == "LEGACY_STAGE"


def test_guard_precedes_all_legacy_filesystem_reads(
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
        monkeypatch.setattr(smoke, name, unexpected)
    for entrypoint in GUARDED_ENTRYPOINTS:
        with pytest.raises(retirement.LegacyStageRetiredError):
            _invoke(entrypoint)


def test_guard_and_check_precede_all_legacy_filesystem_writes() -> None:
    script_text = CHECK_SCRIPT.read_text(encoding="utf-8")
    for forbidden in (
        "write_text",
        "write_bytes",
        "open(",
        "mkdir",
        "csv.DictWriter",
        "json.dump",
    ):
        assert forbidden not in script_text
    with pytest.raises(retirement.LegacyStageRetiredError):
        smoke.run_covapie_sample_index_smoke_v0()


def test_module_import_does_not_modify_artifacts() -> None:
    guarded = (LEGACY_ROOT, SUCCESSOR_ROOT, *STEP14AR_FILES)
    before = _tree_hash(guarded)
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(SRC_ROOT), environment.get("PYTHONPATH", "")]
    )
    result = subprocess.run(
        [sys.executable, "-c", "import covalent_ext.covapie_sample_index_smoke"],
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
    assert "covapie_sample_index_smoke_v0_retirement_policy_passed" in result.stdout


def test_retirement_check_reports_exact_contract() -> None:
    result = _run_check()
    assert result.returncode == 0, result.stdout + result.stderr
    expected_lines = {
        "legacy_stage=covapie_sample_index_smoke_v0",
        "legacy_stage_retired=true",
        "legacy_stage_executable=false",
        "successor_stage=covapie_sample_index_materialization_smoke_v0",
        "successor_availability=tracked",
        "successor_manifest_path_validation_passed=true",
        "historical_artifacts_read_only=true",
        "legacy_artifact_regeneration_forbidden=true",
        "ready_for_training=false",
        "ready_to_train_now=false",
        "feature_semantics_audit_required_before_training=true",
        "recommended_next_step=covapie_sample_index_materialization_smoke",
    }
    assert expected_lines.issubset(set(result.stdout.splitlines()))


def test_retirement_check_does_not_call_old_producer() -> None:
    text = CHECK_SCRIPT.read_text(encoding="utf-8")
    assert "run_covapie_sample_index_smoke_v0" not in text


def test_retirement_check_contains_no_write_mkdir_or_subprocess() -> None:
    text = CHECK_SCRIPT.read_text(encoding="utf-8")
    for forbidden in ("write_text", "write_bytes", "open(", "mkdir", "subprocess"):
        assert forbidden not in text


def test_retirement_check_does_not_report_old_success_line() -> None:
    result = _run_check()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "covapie_sample_index_smoke_v0_passed" not in result.stdout


def test_historical_sample_index_evidence_is_preserved_but_not_canonical() -> None:
    csv_path = LEGACY_ROOT / "covapie_sample_index_smoke.csv"
    manifest_path = LEGACY_ROOT / "covapie_sample_index_smoke_manifest.json"
    with (REPO_ROOT / csv_path).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    manifest = json.loads((REPO_ROOT / manifest_path).read_text(encoding="utf-8"))
    assert len(rows) == 20
    assert len(rows[0]) == 31
    assert manifest["stage"] == EXPECTED_STAGE
    assert smoke.build_retirement_policy().legacy_stage_executable is False
    assert smoke.build_retirement_policy().superseded_by_stage == EXPECTED_SUCCESSOR_STAGE


def test_historical_root_hash_is_unchanged_by_check() -> None:
    before = _tree_hash((LEGACY_ROOT,))
    result = _run_check()
    after = _tree_hash((LEGACY_ROOT,))
    assert result.returncode == 0, result.stdout + result.stderr
    assert before == after


def test_successor_manifest_exists_as_regular_non_symlink() -> None:
    path = REPO_ROOT / SUCCESSOR_MANIFEST
    assert path.exists()
    assert path.is_file()
    assert not path.is_symlink()


def test_canonical_materialization_outputs_are_unchanged_by_check() -> None:
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


def test_raw_paths_are_not_accessed_by_legacy_execution() -> None:
    before_hash = _tree_hash((RAW_ROOT,))
    before_diff = (_git_paths(RAW_ROOT), _git_paths(RAW_ROOT, cached=True))
    with pytest.raises(retirement.LegacyStageRetiredError):
        smoke.run_covapie_sample_index_smoke_v0()
    after_hash = _tree_hash((RAW_ROOT,))
    after_diff = (_git_paths(RAW_ROOT), _git_paths(RAW_ROOT, cached=True))
    assert before_hash == after_hash
    assert before_diff == after_diff


def test_two_retirement_checks_are_deterministic() -> None:
    first = _run_check()
    second = _run_check()
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout
    assert first.stderr == second.stderr
