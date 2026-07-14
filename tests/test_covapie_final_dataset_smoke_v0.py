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

from covalent_ext import covapie_final_dataset_smoke as legacy
from covalent_ext import covapie_legacy_pipeline_retirement_policy as retirement


LEGACY_ROOT = Path("data/derived/covalent_small/covapie_final_dataset_smoke_v0")
SUCCESSOR_MANIFEST = Path("data/derived/covalent_small/covapie_final_dataset_materialization_smoke_v0/covapie_final_dataset_materialization_smoke_manifest.json")
CHECK_SCRIPT = Path("scripts/check_covapie_final_dataset_smoke_v0.py")
MODULE_PATH = Path("src/covalent_ext/covapie_final_dataset_smoke.py")
RAW_ROOT = Path("data/raw/covalent_sources")
STEP14AR_FILES = (
    Path("data/derived/covalent_small/covapie_final_dataset_materialization_smoke_v0"),
    Path("docs/covapie_final_dataset_materialization_smoke_v0_summary.md"),
    Path("scripts/check_covapie_final_dataset_materialization_smoke_v0.py"),
    Path("src/covalent_ext/covapie_final_dataset_materialization_smoke.py"),
    Path("tests/test_covapie_final_dataset_materialization_smoke_v0.py"),
)

EXPECTED_STAGE = "covapie_final_dataset_smoke_v0"
EXPECTED_SUCCESSOR_STAGE = "covapie_final_dataset_materialization_smoke_v0"
EXPECTED_SUCCESSOR_MANIFEST = "data/derived/covalent_small/covapie_final_dataset_materialization_smoke_v0/covapie_final_dataset_materialization_smoke_manifest.json"
EXPECTED_NEXT_STEP = "covapie_final_dataset_materialization_smoke"
EXPECTED_AVAILABILITY = "tracked"
EXPECTED_BLOCKERS = ("legacy_stage_superseded",)
EXPECTED_SUCCESS_LINE = "covapie_final_dataset_smoke_v0_retirement_policy_passed"
OLD_SUCCESS_LINE = "covapie_final_dataset_smoke_v0_passed"
EXPECTED_STEP14AR_MANIFEST_SHA256 = (
    "6f25c8976b295749f3af6407c3bb8ce17cfbda9f18cb967df5fe9b47b480c433"
)
EXPECTED_ERROR_MESSAGE = (
    f"legacy_stage_retired:{EXPECTED_STAGE}:"
    f"superseded_by={EXPECTED_SUCCESSOR_STAGE}:"
    f"recommended_next_step={EXPECTED_NEXT_STEP}"
)
ENTRYPOINT_ARGS: dict[str, tuple[object, ...]] = {
    "build_schema_order_rows": ([], []),
    "build_row_lineage_rows": ([],),
    "build_mask_distribution_rows": ([],),
    "build_feature_blocker_rows": ([],),
}


def _tree_hash(paths: tuple[Path, ...]) -> str:
    digest = hashlib.sha256()
    for relative in paths:
        absolute = REPO_ROOT / relative
        if not absolute.exists():
            continue
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


def test_legacy_stage_and_alias_are_exact() -> None:
    assert legacy.LEGACY_STAGE == EXPECTED_STAGE
    assert legacy.STAGE == EXPECTED_STAGE


def test_guarded_entrypoints_are_explicit_unique_and_complete() -> None:
    assert legacy.GUARDED_ENTRYPOINTS
    assert legacy.GUARDED_ENTRYPOINTS[-1] == "run_covapie_final_dataset_smoke_v0"
    assert len(legacy.GUARDED_ENTRYPOINTS) == len(set(legacy.GUARDED_ENTRYPOINTS))


def test_policy_matches_registry() -> None:
    assert legacy.build_retirement_policy() == (
        retirement.build_legacy_stage_retirement_policy(EXPECTED_STAGE)
    )


def test_retirement_and_successor_contract_is_exact() -> None:
    policy = legacy.build_retirement_policy()
    assert policy.legacy_stage_retired is True
    assert policy.legacy_stage_executable is False
    assert policy.superseded_by_stage == EXPECTED_SUCCESSOR_STAGE
    assert policy.successor_availability == EXPECTED_AVAILABILITY
    assert policy.superseded_by_manifest_path == EXPECTED_SUCCESSOR_MANIFEST
    assert policy.recommended_next_step == EXPECTED_NEXT_STEP


def test_training_and_historical_boundaries_are_exact() -> None:
    policy = legacy.build_retirement_policy()
    assert policy.ready_for_training is False
    assert policy.ready_to_train_now is False
    assert policy.feature_semantics_audit_required_before_training is True
    assert policy.historical_artifacts_read_only is True
    assert policy.legacy_artifact_regeneration_forbidden is True
    assert policy.blocking_reasons == EXPECTED_BLOCKERS


def test_main_producer_fails_closed() -> None:
    with pytest.raises(retirement.LegacyStageRetiredError):
        _invoke("run_covapie_final_dataset_smoke_v0")


@pytest.mark.parametrize("entrypoint", legacy.GUARDED_ENTRYPOINTS)
def test_all_guarded_entrypoints_fail_closed(entrypoint: str) -> None:
    with pytest.raises(retirement.LegacyStageRetiredError):
        _invoke(entrypoint)


def test_exception_attributes_and_deterministic_message() -> None:
    messages = []
    for _ in range(2):
        with pytest.raises(retirement.LegacyStageRetiredError) as caught:
            _invoke("run_covapie_final_dataset_smoke_v0")
        error = caught.value
        assert error.stage == EXPECTED_STAGE
        assert error.superseded_by_stage == EXPECTED_SUCCESSOR_STAGE
        assert error.successor_availability == EXPECTED_AVAILABILITY
        assert error.recommended_next_step == EXPECTED_NEXT_STEP
        assert error.blocking_reasons == EXPECTED_BLOCKERS
        messages.append(str(error))
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


def test_check_and_guards_precede_filesystem_writes() -> None:
    text = CHECK_SCRIPT.read_text(encoding="utf-8")
    for forbidden in (
        "write_text",
        "write_bytes",
        "open(",
        "mkdir",
        "csv.DictWriter",
        "json.dump",
        "subprocess",
    ):
        assert forbidden not in text
    with pytest.raises(retirement.LegacyStageRetiredError):
        _invoke("run_covapie_final_dataset_smoke_v0")


def test_module_import_has_zero_artifact_io() -> None:
    guarded = (LEGACY_ROOT, *STEP14AR_FILES)
    before = _tree_hash(guarded)
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(SRC_ROOT), environment.get("PYTHONPATH", "")]
    )
    result = subprocess.run(
        [sys.executable, "-c", "import covalent_ext.covapie_final_dataset_smoke"],
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


def test_check_exits_zero_and_reports_retirement_contract() -> None:
    result = _run_check()
    assert result.returncode == 0, result.stdout + result.stderr
    assert EXPECTED_SUCCESS_LINE in result.stdout
    assert f"legacy_stage={EXPECTED_STAGE}" in result.stdout
    assert f"successor_stage={EXPECTED_SUCCESSOR_STAGE}" in result.stdout
    assert f"successor_availability={EXPECTED_AVAILABILITY}" in result.stdout
    assert f"successor_manifest_path={EXPECTED_SUCCESSOR_MANIFEST}" in result.stdout
    assert "successor_manifest_path_contract_passed=true" in result.stdout
    assert "successor_manifest_filesystem_check_deferred=false" in result.stdout
    assert "historical_artifacts_read_only=true" in result.stdout
    assert "legacy_artifact_regeneration_forbidden=true" in result.stdout
    assert "ready_for_training=false" in result.stdout
    assert "ready_to_train_now=false" in result.stdout
    assert "feature_semantics_audit_required_before_training=true" in result.stdout
    assert f"recommended_next_step={EXPECTED_NEXT_STEP}" in result.stdout


def test_check_does_not_call_old_producer_or_report_old_success() -> None:
    text = CHECK_SCRIPT.read_text(encoding="utf-8")
    assert "run_covapie_final_dataset_smoke_v0" not in text
    result = _run_check()
    assert result.returncode == 0, result.stdout + result.stderr
    assert OLD_SUCCESS_LINE not in result.stdout


def test_historical_root_is_noncanonical_evidence_and_unchanged() -> None:
    before = _tree_hash((LEGACY_ROOT,))
    result = _run_check()
    after = _tree_hash((LEGACY_ROOT,))
    assert result.returncode == 0, result.stdout + result.stderr
    assert legacy.build_retirement_policy().legacy_stage_executable is False
    assert before == after


def test_step14ar_sixteen_files_are_unchanged() -> None:
    before = _tree_hash(STEP14AR_FILES)
    result = _run_check()
    after = _tree_hash(STEP14AR_FILES)
    assert result.returncode == 0, result.stdout + result.stderr
    assert before == after


def test_raw_state_is_unchanged() -> None:
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


def test_tracked_successor_contract_is_exact() -> None:
    policy = legacy.build_retirement_policy()
    assert policy.successor_availability == "tracked"
    assert policy.superseded_by_manifest_path == EXPECTED_SUCCESSOR_MANIFEST
    assert policy.blocking_reasons == ("legacy_stage_superseded",)


def test_check_validates_tracked_successor_filesystem() -> None:
    result = _run_check()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "successor_manifest_filesystem_check_deferred=false" in result.stdout
    path_validation = retirement.validate_tracked_successor_manifest_paths(
        retirement.build_all_legacy_stage_retirement_policies(),
        repo_root=REPO_ROOT,
    )
    assert path_validation["tracked_successor_paths_passed"] is True


def test_tracked_successor_exists_and_is_git_tracked() -> None:
    manifest = REPO_ROOT / SUCCESSOR_MANIFEST
    assert manifest.exists()
    assert manifest.is_file()
    assert not manifest.is_symlink()
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", SUCCESSOR_MANIFEST.as_posix()],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert tracked.returncode == 0, tracked.stdout + tracked.stderr
    assert tracked.stdout.strip() == EXPECTED_SUCCESSOR_MANIFEST
    policy = legacy.build_retirement_policy()
    assert policy.superseded_by_manifest_path == EXPECTED_SUCCESSOR_MANIFEST
    tracked_policies = tuple(
        policy
        for policy in retirement.build_all_legacy_stage_retirement_policies()
        if policy.successor_availability == "tracked"
    )
    assert len(tracked_policies) == retirement.EXPECTED_TRACKED_SUCCESSOR_REFERENCE_COUNT
    for tracked_policy in tracked_policies:
        assert tracked_policy.superseded_by_manifest_path is not None
        tracked_successor = subprocess.run(
            [
                "git",
                "ls-files",
                "--error-unmatch",
                tracked_policy.superseded_by_manifest_path,
            ],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        assert tracked_successor.returncode == 0, (
            tracked_successor.stdout + tracked_successor.stderr
        )
        assert (
            tracked_successor.stdout.strip()
            == tracked_policy.superseded_by_manifest_path
        )
    result = retirement.validate_tracked_successor_manifest_paths(
        tracked_policies,
        repo_root=REPO_ROOT,
    )
    assert result["tracked_successor_paths_passed"] is True
    assert (
        result["tracked_successor_reference_count"]
        == retirement.EXPECTED_TRACKED_SUCCESSOR_REFERENCE_COUNT
    )
    assert (
        result["validated_reference_count"]
        == retirement.EXPECTED_TRACKED_SUCCESSOR_REFERENCE_COUNT
    )
    assert (
        result["unique_manifest_path_count"]
        == retirement.EXPECTED_UNIQUE_TRACKED_SUCCESSOR_MANIFEST_COUNT
    )
    assert (
        result["unique_regular_file_count"]
        == retirement.EXPECTED_UNIQUE_TRACKED_SUCCESSOR_MANIFEST_COUNT
    )
    assert result["shared_manifest_reference_count"] == len(
        retirement.EXPECTED_SHARED_SUCCESSOR_MANIFEST_REFERENCES
    )


def test_tracked_step14ar_is_retirement_reproducibility_input() -> None:
    manifest = REPO_ROOT / SUCCESSOR_MANIFEST
    before_manifest_hash = hashlib.sha256(manifest.read_bytes()).hexdigest()
    before_step14ar_root = _tree_hash((STEP14AR_FILES[0],))
    before_legacy_root = _tree_hash((LEGACY_ROOT,))
    before_raw_state = _raw_git_state()

    result = _run_check()

    after_manifest_hash = hashlib.sha256(manifest.read_bytes()).hexdigest()
    after_step14ar_root = _tree_hash((STEP14AR_FILES[0],))
    after_legacy_root = _tree_hash((LEGACY_ROOT,))
    after_raw_state = _raw_git_state()
    assert result.returncode == 0, result.stdout + result.stderr
    assert before_manifest_hash == EXPECTED_STEP14AR_MANIFEST_SHA256
    assert after_manifest_hash == EXPECTED_STEP14AR_MANIFEST_SHA256
    assert before_manifest_hash == after_manifest_hash
    assert before_step14ar_root == after_step14ar_root
    assert before_legacy_root == after_legacy_root
    assert before_raw_state == after_raw_state == ("", "")
