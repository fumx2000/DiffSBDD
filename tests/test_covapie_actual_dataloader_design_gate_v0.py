from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
import re
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import covapie_actual_dataloader_design_gate as design
from covalent_ext import covapie_legacy_pipeline_retirement_policy as retirement


S3_ROOT = Path(
    "data/derived/covalent_small/covapie_metadata_dataloader_smoke_qa_gate_v0"
)
S4_ROOT = Path(
    "data/derived/covalent_small/covapie_actual_dataloader_design_gate_v0"
)
S5_ROOT = Path(
    "data/derived/covalent_small/covapie_feature_semantics_tensorization_audit_gate_v0"
)
STEP14AR_ROOT = Path(
    "data/derived/covalent_small/covapie_final_dataset_materialization_smoke_v0"
)
QA_V1_MODULE = Path("src/covalent_ext/covapie_final_dataset_qa_gate_v1.py")
QA_V1_ROOT = Path("data/derived/covalent_small/covapie_final_dataset_qa_gate_v1")
MODULE_PATH = Path("src/covalent_ext/covapie_actual_dataloader_design_gate.py")
CHECK_PATH = Path("scripts/check_covapie_actual_dataloader_design_gate_v0.py")
S5_MODULE = "covalent_ext.covapie_feature_semantics_tensorization_audit_gate"
EXPECTED_GUARDS = (
    "build_precondition_rows",
    "build_static_reference_rows",
    "build_safety_rows",
    "run_covapie_actual_dataloader_design_gate_v0",
)
EXPECTED_PURE_BUILDERS = (
    "build_adapter_design_rows",
    "build_tensorization_input_rows",
    "build_batch_collate_rows",
    "build_checkpoint_compatibility_rows",
    "build_feature_semantics_blocker_rows",
    "build_future_smoke_plan_rows",
)
EXPECTED_BLOCKERS = (
    "legacy_stage_superseded",
    "dataloader_interface_redesign_pending",
)


def _tree_hash(relative: Path) -> str:
    digest = hashlib.sha256()
    root = REPO_ROOT / relative
    for path in sorted(root.rglob("*")):
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


def _module_tree() -> ast.Module:
    return ast.parse(MODULE_PATH.read_text(encoding="utf-8"))


def _function_node(name: str) -> ast.FunctionDef:
    for node in ast.walk(_module_tree()):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"missing function: {name}")


def _assert_first_statement_is_guard(node: ast.FunctionDef) -> None:
    first = node.body[0]
    assert isinstance(first, ast.Expr)
    assert isinstance(first.value, ast.Call)
    assert isinstance(first.value.func, ast.Name)
    assert first.value.func.id == "raise_legacy_stage_retired"
    assert len(first.value.args) == 1
    assert isinstance(first.value.args[0], ast.Name)
    assert first.value.args[0].id == "LEGACY_STAGE"


def _invoke_with_required_arguments(function: object) -> None:
    signature = inspect.signature(function)
    args: list[object] = []
    kwargs: dict[str, object] = {}
    for parameter in signature.parameters.values():
        if parameter.default is not inspect.Parameter.empty:
            continue
        if parameter.kind is inspect.Parameter.KEYWORD_ONLY:
            kwargs[parameter.name] = None
        elif parameter.kind not in {
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        }:
            args.append(None)
    function(*args, **kwargs)  # type: ignore[operator]


def _git_lines(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        check=False,
    )
    return result.stdout.strip().splitlines()


def test_stage_identity_is_exact() -> None:
    assert design.LEGACY_STAGE == "covapie_actual_dataloader_design_gate_v0"
    assert design.STAGE == design.LEGACY_STAGE


def test_policy_matches_registry() -> None:
    assert design.build_retirement_policy() == (
        retirement.build_legacy_stage_retirement_policy(design.LEGACY_STAGE)
    )


def test_guarded_entrypoints_are_explicit_and_unique() -> None:
    assert design.GUARDED_ENTRYPOINTS == EXPECTED_GUARDS
    assert len(design.GUARDED_ENTRYPOINTS) == len(set(design.GUARDED_ENTRYPOINTS))


def test_pure_historical_contract_builders_are_explicit_and_unique() -> None:
    assert design.PURE_HISTORICAL_CONTRACT_BUILDERS == EXPECTED_PURE_BUILDERS
    assert len(EXPECTED_PURE_BUILDERS) == len(set(EXPECTED_PURE_BUILDERS))
    assert set(EXPECTED_PURE_BUILDERS).isdisjoint(EXPECTED_GUARDS)


def test_policy_is_retired_and_non_executable() -> None:
    policy = design.build_retirement_policy()
    assert policy.legacy_stage_retired is True
    assert policy.legacy_stage_executable is False


def test_successor_is_absent_and_redesign_is_pending() -> None:
    policy = design.build_retirement_policy()
    assert policy.superseded_by_stage is None
    assert policy.superseded_by_manifest_path is None
    assert policy.successor_availability == "redesign_pending"


def test_blockers_and_next_step_are_exact() -> None:
    policy = design.build_retirement_policy()
    assert policy.blocking_reasons == EXPECTED_BLOCKERS
    assert policy.recommended_next_step == "covapie_final_dataset_qa_gate_v1"


def test_training_and_feature_audit_boundary_is_exact() -> None:
    policy = design.build_retirement_policy()
    assert policy.historical_artifacts_read_only is True
    assert policy.legacy_artifact_regeneration_forbidden is True
    assert policy.ready_for_training is False
    assert policy.ready_to_train_now is False
    assert policy.feature_semantics_audit_required_before_training is True


def test_main_run_fails_closed() -> None:
    with pytest.raises(retirement.LegacyStageRetiredError):
        design.run_covapie_actual_dataloader_design_gate_v0()


@pytest.mark.parametrize("name", EXPECTED_GUARDS)
def test_all_artifact_and_admission_entrypoints_fail_closed(name: str) -> None:
    with pytest.raises(retirement.LegacyStageRetiredError) as caught:
        _invoke_with_required_arguments(getattr(design, name))
    assert caught.value.stage == design.LEGACY_STAGE


def test_exception_attributes_and_message_are_deterministic() -> None:
    expected_message = (
        "legacy_stage_retired:covapie_actual_dataloader_design_gate_v0:"
        "superseded_by=None:"
        "recommended_next_step=covapie_final_dataset_qa_gate_v1"
    )
    messages = []
    for _ in range(2):
        with pytest.raises(retirement.LegacyStageRetiredError) as caught:
            design.run_covapie_actual_dataloader_design_gate_v0()
        error = caught.value
        assert error.stage == design.LEGACY_STAGE
        assert error.superseded_by_stage is None
        assert error.successor_availability == "redesign_pending"
        assert error.blocking_reasons == EXPECTED_BLOCKERS
        messages.append(str(error))
    assert messages == [expected_message, expected_message]


@pytest.mark.parametrize("name", EXPECTED_GUARDS)
def test_each_guard_is_first_executable_statement(name: str) -> None:
    _assert_first_statement_is_guard(_function_node(name))


@pytest.mark.parametrize("name", EXPECTED_GUARDS)
def test_guard_precedes_artifact_static_source_and_git_access(
    name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("I/O occurred before retirement guard")

    for helper in (
        "_csv_rows",
        "_load_json",
        "_run_git",
        "_path_diff_exists",
        "_metadata_hash",
        "_raw_files_tracked",
        "_raw_files_staged",
        "_static_read_status",
    ):
        monkeypatch.setattr(design, helper, forbidden)
    monkeypatch.setattr(Path, "exists", forbidden)
    monkeypatch.setattr(Path, "is_file", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    with pytest.raises(retirement.LegacyStageRetiredError):
        _invoke_with_required_arguments(getattr(design, name))


@pytest.mark.parametrize("name", EXPECTED_PURE_BUILDERS)
def test_pure_contract_builders_remain_import_compatible(name: str) -> None:
    rows = getattr(design, name)()
    assert isinstance(rows, list)
    assert rows


@pytest.mark.parametrize("name", EXPECTED_PURE_BUILDERS)
def test_pure_contract_builders_perform_no_io_or_readiness_admission(
    name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("pure historical builder performed I/O")

    for helper in (
        "_csv_rows",
        "_load_json",
        "_run_git",
        "_path_diff_exists",
        "_metadata_hash",
        "_raw_files_tracked",
        "_raw_files_staged",
        "_static_read_status",
    ):
        monkeypatch.setattr(design, helper, forbidden)
    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    before = tuple(Path(".").glob("definitely-no-match-*"))
    rows = getattr(design, name)()
    after = tuple(Path(".").glob("definitely-no-match-*"))
    assert rows
    assert before == after == ()
    assert design.build_retirement_policy().legacy_stage_executable is False


def test_module_reload_performs_no_artifact_or_static_source_io(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("I/O during module import")

    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(Path, "exists", forbidden)
    monkeypatch.setattr(Path, "is_file", forbidden)
    importlib.reload(design)


def test_s5_import_surface_remains_compatible() -> None:
    s5 = importlib.import_module(S5_MODULE)
    assert s5.step13bw is design
    assert s5.PREVIOUS_STAGE == design.STAGE
    assert s5.CANONICAL_MASK_TASK_NAMES == design.CANONICAL_MASK_TASK_NAMES


def test_s5_import_does_not_execute_s4_producer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    s5 = importlib.import_module(S5_MODULE)

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("S4 producer executed during S5 import")

    monkeypatch.setattr(design, "run_covapie_actual_dataloader_design_gate_v0", forbidden)
    for name in EXPECTED_GUARDS[:-1]:
        monkeypatch.setattr(design, name, forbidden)
    importlib.reload(s5)


def test_s5_ast_has_no_calls_into_s4() -> None:
    tree = ast.parse(
        Path(
            "src/covalent_ext/covapie_feature_semantics_tensorization_audit_gate.py"
        ).read_text(encoding="utf-8")
    )
    calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        owner = node.func.value
        if isinstance(owner, ast.Name) and owner.id == "step13bw":
            calls.append(node.func.attr)
    assert calls == []


def test_check_script_is_policy_only() -> None:
    text = CHECK_PATH.read_text(encoding="utf-8")
    for forbidden in (
        "run_covapie_actual_dataloader_design_gate_v0(",
        "build_precondition_rows(",
        "build_static_reference_rows(",
        "build_safety_rows(",
        "write_text",
        "write_bytes",
        "open(",
        "mkdir",
        "subprocess",
        "dataset.py",
        "lightning_modules.py",
    ):
        assert forbidden not in text


def test_check_script_does_not_hardcode_registry_count() -> None:
    text = CHECK_PATH.read_text(encoding="utf-8")
    assert re.search(r"len\(policies\)\s*==", text) is None
    assert "validation.registry_count_passed is True" in text


def test_check_script_reports_retirement_success_without_artifact_changes() -> None:
    before = _tree_hash(S4_ROOT)
    result = subprocess.run(
        [sys.executable, str(CHECK_PATH)],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "covapie_actual_dataloader_design_gate_v0_retirement_policy_passed" in result.stdout
    assert "successor_availability=redesign_pending" in result.stdout
    assert before == _tree_hash(S4_ROOT)


def test_historical_s4_root_and_manifest_hashes_are_frozen() -> None:
    assert _tree_hash(S4_ROOT) == (
        "37d10ef6b1d56b59e01a0433c8ecae33c9724cc81a87a4625f776160e9ab99ce"
    )
    manifest = S4_ROOT / "covapie_actual_dataloader_design_gate_manifest.json"
    assert hashlib.sha256(manifest.read_bytes()).hexdigest() == (
        "25935bea5f89637c9eebfa404fb0dcb865b4aca0958a90eebe2e2d4e2d8d03d8"
    )


def test_s3_and_s5_root_hashes_are_frozen() -> None:
    assert _tree_hash(S3_ROOT) == (
        "894e64576bfa983115a0418207a455499e331fad27dc00fa8c8be0b5cf807acf"
    )
    assert _tree_hash(S5_ROOT) == (
        "d738a52df0d4aad3b29adb5654f50a4ff2fc9aeb129968e5e08d7bdd18870675"
    )
    manifest = S5_ROOT / "covapie_feature_semantics_tensorization_audit_gate_manifest.json"
    assert hashlib.sha256(manifest.read_bytes()).hexdigest() == (
        "c89ebb3981be29c4180d477838d7eb3c9fbf3bc93aa52f4d07b9360c77d9bd91"
    )


def test_step14ar_manifest_hash_is_frozen() -> None:
    manifest = STEP14AR_ROOT / "covapie_final_dataset_materialization_smoke_manifest.json"
    assert hashlib.sha256(manifest.read_bytes()).hexdigest() == (
        "6f25c8976b295749f3af6407c3bb8ce17cfbda9f18cb967df5fe9b47b480c433"
    )


def test_canonical_qa_v1_is_unchanged_by_legacy_check() -> None:
    module_before = _snapshot_path(QA_V1_MODULE)
    root_before = _snapshot_path(QA_V1_ROOT)
    result = subprocess.run(
        [sys.executable, CHECK_PATH.as_posix()],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert _snapshot_path(QA_V1_MODULE) == module_before
    assert _snapshot_path(QA_V1_ROOT) == root_before


def test_raw_files_remain_untracked_and_unstaged() -> None:
    raw = "data/raw/covalent_sources"
    assert _git_lines("ls-files", raw) == []
    assert _git_lines("diff", "--cached", "--name-only", "--", raw) == []


def test_policy_is_deterministic() -> None:
    assert design.build_retirement_policy() == design.build_retirement_policy()


def test_step14z_independent_stages_remain_outside_registry() -> None:
    stages = set(retirement.LEGACY_STAGE_ORDER)
    assert "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0" not in stages
    assert "covapie_independent_group_expansion_struct_conn_crosscheck_smoke_v0" not in stages


def test_historical_roots_have_no_tracked_diff() -> None:
    assert _git_lines("diff", "--name-only", "--", str(S3_ROOT), str(S4_ROOT), str(S5_ROOT)) == []
