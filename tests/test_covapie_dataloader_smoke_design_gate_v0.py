from __future__ import annotations

import ast
import hashlib
import importlib
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

from covalent_ext import covapie_dataloader_smoke_design_gate as legacy
from covalent_ext import covapie_legacy_pipeline_retirement_policy as retirement


LEGACY_ROOT = Path(
    "data/derived/covalent_small/covapie_dataloader_smoke_design_gate_v0"
)
S2_ROOT = Path(
    "data/derived/covalent_small/covapie_metadata_dataloader_smoke_v0"
)
CHECK_SCRIPT = Path(
    "scripts/check_covapie_dataloader_smoke_design_gate_v0.py"
)
MODULE_PATH = Path(
    "src/covalent_ext/covapie_dataloader_smoke_design_gate.py"
)
RAW_ROOT = Path("data/raw/covalent_sources")
QA_V1_MODULE = Path("src/covalent_ext/covapie_final_dataset_qa_gate_v1.py")
QA_V1_ROOT = Path(
    "data/derived/covalent_small/covapie_final_dataset_qa_gate_v1"
)
STEP14AR_FILES = (
    Path(
        "data/derived/covalent_small/"
        "covapie_final_dataset_materialization_smoke_v0"
    ),
    Path("docs/covapie_final_dataset_materialization_smoke_v0_summary.md"),
    Path("scripts/check_covapie_final_dataset_materialization_smoke_v0.py"),
    Path("src/covalent_ext/covapie_final_dataset_materialization_smoke.py"),
    Path("tests/test_covapie_final_dataset_materialization_smoke_v0.py"),
)

EXPECTED_STAGE = "covapie_dataloader_smoke_design_gate_v0"
EXPECTED_NEXT_STEP = "covapie_final_dataset_qa_gate_v1"
EXPECTED_AVAILABILITY = "redesign_pending"
EXPECTED_BLOCKERS = (
    "legacy_stage_superseded",
    "dataloader_interface_redesign_pending",
)
EXPECTED_GUARDS = (
    "build_precondition_rows",
    "build_getitem_output_mapping_rows",
    "build_safety_rows",
    "run_covapie_dataloader_smoke_design_gate_v0",
)
EXPECTED_SUCCESS_LINE = (
    "covapie_dataloader_smoke_design_gate_v0_retirement_policy_passed"
)
OLD_SUCCESS_LINE = "covapie_dataloader_smoke_design_gate_v0_passed"
EXPECTED_ERROR_MESSAGE = (
    f"legacy_stage_retired:{EXPECTED_STAGE}:superseded_by=None:"
    f"recommended_next_step={EXPECTED_NEXT_STEP}"
)
EXPECTED_S1_ROOT_HASH = (
    "a9d23c3da97f38ad028f17c4b8ab62ac0a0c328b471fb8a1ec7d6c82cf93276e"
)
EXPECTED_S2_ROOT_HASH = (
    "23b3a807d0915d21bdbd73ecc7c357e5df5e514b7d7a80f98bc903910f5e191c"
)
INDEPENDENT_MODULES = (
    "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke",
    "covapie_independent_group_expansion_struct_conn_crosscheck_smoke",
)


def _tree_hash(paths: tuple[Path, ...]) -> str:
    digest = hashlib.sha256()
    for relative in paths:
        absolute = REPO_ROOT / relative
        if not absolute.exists():
            continue
        candidates = (
            [absolute] if absolute.is_file() else sorted(absolute.rglob("*"))
        )
        for path in candidates:
            if path.is_file():
                digest.update(path.relative_to(REPO_ROOT).as_posix().encode())
                digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def _snapshot_path(relative: Path) -> dict[str, object]:
    path = REPO_ROOT / relative
    if not path.exists():
        return {"state": "missing"}
    if path.is_file():
        return {"state": "file", "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    return {
        "state": "directory",
        "files": {
            child.relative_to(path).as_posix(): hashlib.sha256(child.read_bytes()).hexdigest()
            for child in sorted(path.rglob("*"))
            if child.is_file()
        },
    }


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
    function()


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


def test_stage_alias_guards_and_import_surface_are_exact() -> None:
    assert legacy.LEGACY_STAGE == EXPECTED_STAGE
    assert legacy.STAGE == EXPECTED_STAGE
    assert legacy.GUARDED_ENTRYPOINTS == EXPECTED_GUARDS
    assert len(legacy.GUARDED_ENTRYPOINTS) == len(
        set(legacy.GUARDED_ENTRYPOINTS)
    )
    for symbol in (
        "PREVIOUS_STAGE",
        "OUTPUT_ROOT",
        "MANIFEST_JSON",
        "PRECONDITION_COLUMNS",
        "RUNTIME_BOUNDARY_COLUMNS",
        "METADATA_DATASET_API_COLUMNS",
        "GETITEM_OUTPUT_MAPPING_COLUMNS",
        "TENSORIZATION_BLOCKER_COLUMNS",
        "BATCH_COLLATE_DESIGN_COLUMNS",
        "CHECKPOINT_RUNTIME_RISK_COLUMNS",
        "METADATA_DATALOADER_SMOKE_PLAN_COLUMNS",
        "SAFETY_AUDIT_COLUMNS",
        "CANONICAL_MASK_TASK_NAMES",
        "CANONICAL_MASK_TASK_ALIASES",
        "step13bd",
        "step13bm",
        "step13bo",
        "step13bq",
        "step13br",
        "step13bs",
    ):
        assert hasattr(legacy, symbol), symbol


def test_historical_contract_builders_remain_import_compatible_only() -> None:
    for symbol in (
        "build_runtime_boundary_rows",
        "build_metadata_dataset_api_rows",
        "build_tensorization_blocker_rows",
        "build_batch_collate_rows",
        "build_checkpoint_runtime_risk_rows",
        "build_metadata_smoke_plan_rows",
    ):
        assert callable(getattr(legacy, symbol))
    assert legacy.build_retirement_policy().legacy_stage_executable is False


def test_policy_matches_registry_and_redesign_contract() -> None:
    item = legacy.build_retirement_policy()
    assert item == retirement.build_legacy_stage_retirement_policy(
        EXPECTED_STAGE
    )
    assert item.legacy_stage_retired is True
    assert item.legacy_stage_executable is False
    assert item.superseded_by_stage is None
    assert item.superseded_by_manifest_path is None
    assert item.successor_availability == EXPECTED_AVAILABILITY
    assert item.recommended_next_step == EXPECTED_NEXT_STEP
    assert item.blocking_reasons == EXPECTED_BLOCKERS


def test_training_and_historical_boundaries_are_exact() -> None:
    item = legacy.build_retirement_policy()
    assert item.historical_artifacts_read_only is True
    assert item.legacy_artifact_regeneration_forbidden is True
    assert item.ready_for_training is False
    assert item.ready_to_train_now is False
    assert item.feature_semantics_audit_required_before_training is True


def test_main_run_fails_closed() -> None:
    with pytest.raises(retirement.LegacyStageRetiredError):
        legacy.run_covapie_dataloader_smoke_design_gate_v0()


@pytest.mark.parametrize("entrypoint", EXPECTED_GUARDS)
def test_all_guarded_entrypoints_fail_closed(entrypoint: str) -> None:
    with pytest.raises(retirement.LegacyStageRetiredError):
        _invoke(entrypoint)


def test_exception_attributes_and_message_are_deterministic() -> None:
    messages = []
    for _ in range(2):
        with pytest.raises(retirement.LegacyStageRetiredError) as caught:
            legacy.run_covapie_dataloader_smoke_design_gate_v0()
        error = caught.value
        assert error.stage == EXPECTED_STAGE
        assert error.superseded_by_stage is None
        assert error.successor_availability == EXPECTED_AVAILABILITY
        assert error.recommended_next_step == EXPECTED_NEXT_STEP
        assert error.blocking_reasons == EXPECTED_BLOCKERS
        messages.append(str(error))
    assert messages == [EXPECTED_ERROR_MESSAGE, EXPECTED_ERROR_MESSAGE]


def test_guards_are_first_executable_statements() -> None:
    tree = ast.parse((REPO_ROOT / MODULE_PATH).read_text(encoding="utf-8"))
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }
    for name in EXPECTED_GUARDS:
        first = functions[name].body[0]
        assert isinstance(first, ast.Expr)
        assert isinstance(first.value, ast.Call)
        assert isinstance(first.value.func, ast.Name)
        assert first.value.func.id == "raise_legacy_stage_retired"
        assert len(first.value.args) == 1
        assert isinstance(first.value.args[0], ast.Name)
        assert first.value.args[0].id == "LEGACY_STAGE"


def test_guards_precede_filesystem_admission_and_readiness(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected(*args: object, **kwargs: object) -> object:
        raise AssertionError("legacy filesystem/admission path reached")

    for name in (
        "_csv_rows",
        "_load_json",
        "_run_git",
        "_metadata_hash",
        "_raw_files_tracked",
        "_raw_files_staged",
        "_forbidden_suffix_exists",
        "_forbidden_named_artifact_exists",
    ):
        monkeypatch.setattr(legacy, name, unexpected)
    monkeypatch.setattr(Path, "exists", unexpected)
    monkeypatch.setattr(Path, "is_file", unexpected)
    for entrypoint in EXPECTED_GUARDS:
        with pytest.raises(retirement.LegacyStageRetiredError):
            _invoke(entrypoint)


def test_s2_import_surface_is_compatible() -> None:
    from covalent_ext import covapie_metadata_dataloader_smoke as s2

    assert s2.step13bt is legacy
    for symbol in (
        "STAGE",
        "OUTPUT_ROOT",
        "MANIFEST_JSON",
        "CANONICAL_MASK_TASK_NAMES",
        "CANONICAL_MASK_TASK_ALIASES",
        "METADATA_CSV_SHA256",
        "step13bd",
        "step13bm",
        "step13bo",
        "step13bq",
        "step13br",
        "step13bs",
    ):
        assert hasattr(s2.step13bt, symbol), symbol


def test_s2_import_does_not_call_s1_producer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected() -> object:
        raise AssertionError("S1 producer called during S2 import")

    monkeypatch.setattr(
        legacy,
        "run_covapie_dataloader_smoke_design_gate_v0",
        unexpected,
    )
    module = importlib.import_module(
        "covalent_ext.covapie_metadata_dataloader_smoke"
    )
    importlib.reload(module)


def test_module_import_has_zero_artifact_io() -> None:
    guarded = (LEGACY_ROOT, S2_ROOT, QA_V1_ROOT, *STEP14AR_FILES)
    before = _tree_hash(guarded)
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(SRC_ROOT), environment.get("PYTHONPATH", "")]
    )
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import covalent_ext.covapie_dataloader_smoke_design_gate",
        ],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert before == _tree_hash(guarded)


def test_check_exits_zero_and_reports_exact_retirement_contract() -> None:
    result = _run_check()
    assert result.returncode == 0, result.stdout + result.stderr
    for line in (
        f"legacy_stage={EXPECTED_STAGE}",
        "legacy_stage_retired=true",
        "legacy_stage_executable=false",
        "successor_stage_is_none=true",
        "successor_availability=redesign_pending",
        "successor_manifest_path_is_none=true",
        "dataloader_interface_redesign_pending=true",
        "historical_artifacts_read_only=true",
        "legacy_artifact_regeneration_forbidden=true",
        "ready_for_training=false",
        "ready_to_train_now=false",
        "feature_semantics_audit_required_before_training=true",
        f"recommended_next_step={EXPECTED_NEXT_STEP}",
        EXPECTED_SUCCESS_LINE,
    ):
        assert line in result.stdout


def test_check_is_policy_only_and_does_not_report_old_success() -> None:
    text = (REPO_ROOT / CHECK_SCRIPT).read_text(encoding="utf-8")
    assert "run_covapie_dataloader_smoke_design_gate_v0" not in text
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
    result = _run_check()
    assert result.returncode == 0, result.stdout + result.stderr
    assert OLD_SUCCESS_LINE not in result.stdout
    assert "ready_for_covapie_metadata_dataloader_smoke" not in result.stdout
    assert "qa v1 passed" not in result.stdout.lower()


def test_historical_s1_root_hash_is_frozen() -> None:
    assert _tree_hash((LEGACY_ROOT,)) == EXPECTED_S1_ROOT_HASH


def test_s2_root_hash_is_frozen() -> None:
    assert _tree_hash((S2_ROOT,)) == EXPECTED_S2_ROOT_HASH


def test_check_preserves_s1_s2_and_step14ar() -> None:
    guarded = (LEGACY_ROOT, S2_ROOT, *STEP14AR_FILES)
    before = _tree_hash(guarded)
    result = _run_check()
    assert result.returncode == 0, result.stdout + result.stderr
    assert before == _tree_hash(guarded)


def test_qa_v1_root_is_unchanged_by_legacy_check() -> None:
    module_before = _snapshot_path(QA_V1_MODULE)
    root_before = _snapshot_path(QA_V1_ROOT)
    result = _run_check()
    assert result.returncode == 0, result.stdout + result.stderr
    assert _snapshot_path(QA_V1_MODULE) == module_before
    assert _snapshot_path(QA_V1_ROOT) == root_before


def test_raw_git_state_remains_empty() -> None:
    assert _raw_git_state() == ("", "")
    result = _run_check()
    assert result.returncode == 0, result.stdout + result.stderr
    assert _raw_git_state() == ("", "")


def test_two_independent_modules_are_not_retired() -> None:
    registered = set(retirement.LEGACY_STAGE_ORDER)
    for module_name in INDEPENDENT_MODULES:
        module = importlib.import_module(f"covalent_ext.{module_name}")
        assert module.STAGE not in registered


def test_two_check_runs_are_deterministic() -> None:
    first = _run_check()
    second = _run_check()
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout
    assert first.stderr == second.stderr
