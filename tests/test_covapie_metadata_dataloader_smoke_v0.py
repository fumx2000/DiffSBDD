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

from covalent_ext import covapie_legacy_pipeline_retirement_policy as retirement
from covalent_ext import covapie_metadata_dataloader_smoke as smoke


S1_ROOT = Path(
    "data/derived/covalent_small/covapie_dataloader_smoke_design_gate_v0"
)
S2_ROOT = Path(
    "data/derived/covalent_small/covapie_metadata_dataloader_smoke_v0"
)
S3_ROOT = Path(
    "data/derived/covalent_small/covapie_metadata_dataloader_smoke_qa_gate_v0"
)
STEP14AR_ROOT = Path(
    "data/derived/covalent_small/covapie_final_dataset_materialization_smoke_v0"
)
MODULE_PATH = Path("src/covalent_ext/covapie_metadata_dataloader_smoke.py")
CHECK_PATH = Path("scripts/check_covapie_metadata_dataloader_smoke_v0.py")
EXPECTED_GUARDS = (
    "build_precondition_rows",
    "build_preview_rows",
    "build_len_getitem_rows",
    "build_key_coverage_rows",
    "build_mask_distribution_rows",
    "build_blocker_runtime_rows",
    "build_safety_rows",
    "build_git_safety_rows",
    "run_covapie_metadata_dataloader_smoke_v0",
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
    assert smoke.LEGACY_STAGE == "covapie_metadata_dataloader_smoke_v0"
    assert smoke.STAGE == smoke.LEGACY_STAGE


def test_policy_matches_registry() -> None:
    assert smoke.build_retirement_policy() == (
        retirement.build_legacy_stage_retirement_policy(smoke.LEGACY_STAGE)
    )


def test_guarded_entrypoints_are_explicit_and_unique() -> None:
    assert smoke.GUARDED_ENTRYPOINTS == EXPECTED_GUARDS
    assert len(smoke.GUARDED_ENTRYPOINTS) == len(set(smoke.GUARDED_ENTRYPOINTS))


def test_guarded_class_methods_are_exact() -> None:
    assert smoke.GUARDED_CLASS_METHODS == (
        "CovapieMetadataDatasetSmoke.__init__",
    )


def test_policy_is_retired_and_non_executable() -> None:
    policy = smoke.build_retirement_policy()
    assert policy.legacy_stage_retired is True
    assert policy.legacy_stage_executable is False


def test_successor_is_absent_and_redesign_is_pending() -> None:
    policy = smoke.build_retirement_policy()
    assert policy.superseded_by_stage is None
    assert policy.superseded_by_manifest_path is None
    assert policy.successor_availability == "redesign_pending"


def test_blockers_and_next_step_are_exact() -> None:
    policy = smoke.build_retirement_policy()
    assert policy.blocking_reasons == EXPECTED_BLOCKERS
    assert policy.recommended_next_step == "covapie_final_dataset_qa_gate_v1"


def test_training_boundary_is_exact() -> None:
    policy = smoke.build_retirement_policy()
    assert policy.historical_artifacts_read_only is True
    assert policy.legacy_artifact_regeneration_forbidden is True
    assert policy.ready_for_training is False
    assert policy.ready_to_train_now is False
    assert policy.feature_semantics_audit_required_before_training is True


def test_main_run_fails_closed() -> None:
    with pytest.raises(retirement.LegacyStageRetiredError):
        smoke.run_covapie_metadata_dataloader_smoke_v0()


@pytest.mark.parametrize("name", EXPECTED_GUARDS)
def test_all_artifact_and_admission_entrypoints_fail_closed(name: str) -> None:
    with pytest.raises(retirement.LegacyStageRetiredError) as caught:
        _invoke_with_required_arguments(getattr(smoke, name))
    assert caught.value.stage == smoke.LEGACY_STAGE


def test_constructor_fails_closed() -> None:
    with pytest.raises(retirement.LegacyStageRetiredError) as caught:
        smoke.CovapieMetadataDatasetSmoke("interface.csv", "final.csv")
    assert caught.value.stage == smoke.LEGACY_STAGE


def test_constructor_guard_is_first_executable_statement() -> None:
    _assert_first_statement_is_guard(_function_node("__init__"))


@pytest.mark.parametrize("name", EXPECTED_GUARDS)
def test_entrypoint_guard_is_first_executable_statement(name: str) -> None:
    _assert_first_statement_is_guard(_function_node(name))


def test_constructor_guard_precedes_path_and_csv_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("I/O occurred before retirement guard")

    monkeypatch.setattr(smoke, "_csv_rows", forbidden)
    monkeypatch.setattr(Path, "exists", forbidden)
    monkeypatch.setattr(Path, "open", forbidden)
    with pytest.raises(retirement.LegacyStageRetiredError):
        smoke.CovapieMetadataDatasetSmoke("interface.csv", "final.csv")


def test_constructor_has_no_bypass_or_alternate_mode() -> None:
    parameters = tuple(
        inspect.signature(smoke.CovapieMetadataDatasetSmoke.__init__).parameters
    )
    assert parameters == (
        "self",
        "interface_preview_csv_path",
        "final_dataset_preview_csv_path",
    )
    assert not any(
        token in MODULE_PATH.read_text(encoding="utf-8")
        for token in ("bypass_guard", "in_memory_mode", "RETIREMENT_BYPASS")
    )


def test_class_is_not_torch_dataset() -> None:
    assert all(
        base.__module__.split(".")[0] != "torch"
        for base in smoke.CovapieMetadataDatasetSmoke.__mro__
    )


def test_module_does_not_import_torch() -> None:
    for node in ast.walk(_module_tree()):
        if isinstance(node, ast.Import):
            assert all(alias.name.split(".")[0] != "torch" for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] != "torch"


def test_len_and_getitem_symbols_are_preserved() -> None:
    assert callable(smoke.CovapieMetadataDatasetSmoke.__len__)
    assert callable(smoke.CovapieMetadataDatasetSmoke.__getitem__)


def test_module_reload_performs_no_artifact_io(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("artifact I/O during module import")

    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(Path, "exists", forbidden)
    monkeypatch.setattr(Path, "is_file", forbidden)
    importlib.reload(smoke)


def test_s3_import_surface_remains_compatible() -> None:
    from covalent_ext import covapie_metadata_dataloader_smoke_qa_gate as qa

    assert qa.step13bu is smoke
    assert qa.PREVIOUS_STAGE == smoke.STAGE
    assert qa.CANONICAL_MASK_TASK_NAMES == smoke.CANONICAL_MASK_TASK_NAMES


def test_s3_import_does_not_instantiate_s2(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from covalent_ext import covapie_metadata_dataloader_smoke_qa_gate as qa

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("S2 constructor executed during S3 import")

    monkeypatch.setattr(smoke.CovapieMetadataDatasetSmoke, "__init__", forbidden)
    importlib.reload(qa)


def test_check_script_is_policy_only() -> None:
    text = CHECK_PATH.read_text(encoding="utf-8")
    for forbidden in (
        "run_covapie_metadata_dataloader_smoke_v0(",
        "CovapieMetadataDatasetSmoke(",
        "write_text",
        "write_bytes",
        "open(",
        "mkdir",
        "subprocess",
    ):
        assert forbidden not in text


def test_check_script_does_not_hardcode_registry_count() -> None:
    text = CHECK_PATH.read_text(encoding="utf-8")
    assert re.search(r"len\(policies\)\s*==", text) is None
    assert "validation.registry_count_passed is True" in text


def test_check_script_reports_retirement_success_without_artifact_changes() -> None:
    before = _tree_hash(S2_ROOT)
    result = subprocess.run(
        [sys.executable, str(CHECK_PATH)],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "covapie_metadata_dataloader_smoke_v0_retirement_policy_passed" in result.stdout
    assert "successor_availability=redesign_pending" in result.stdout
    assert before == _tree_hash(S2_ROOT)


def test_historical_s2_root_hash_is_frozen() -> None:
    assert _tree_hash(S2_ROOT) == (
        "23b3a807d0915d21bdbd73ecc7c357e5df5e514b7d7a80f98bc903910f5e191c"
    )


def test_s1_and_s3_root_hashes_are_frozen() -> None:
    assert _tree_hash(S1_ROOT) == (
        "a9d23c3da97f38ad028f17c4b8ab62ac0a0c328b471fb8a1ec7d6c82cf93276e"
    )
    assert _tree_hash(S3_ROOT) == (
        "894e64576bfa983115a0418207a455499e331fad27dc00fa8c8be0b5cf807acf"
    )


def test_step14ar_manifest_hash_is_frozen() -> None:
    manifest = STEP14AR_ROOT / "covapie_final_dataset_materialization_smoke_manifest.json"
    assert hashlib.sha256(manifest.read_bytes()).hexdigest() == (
        "6f25c8976b295749f3af6407c3bb8ce17cfbda9f18cb967df5fe9b47b480c433"
    )


def test_canonical_qa_v1_is_not_materialized() -> None:
    assert not Path("src/covalent_ext/covapie_final_dataset_qa_gate_v1.py").exists()
    assert not Path(
        "data/derived/covalent_small/covapie_final_dataset_qa_gate_v1"
    ).exists()


def test_raw_files_remain_untracked_and_unstaged() -> None:
    raw = "data/raw/covalent_sources"
    assert _git_lines("ls-files", raw) == []
    assert _git_lines("diff", "--cached", "--name-only", "--", raw) == []


def test_retirement_policy_is_deterministic() -> None:
    assert smoke.build_retirement_policy() == smoke.build_retirement_policy()


def test_step14z_independent_stages_remain_outside_registry() -> None:
    stages = set(retirement.LEGACY_STAGE_ORDER)
    assert "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0" not in stages
    assert "covapie_independent_group_expansion_struct_conn_crosscheck_smoke_v0" not in stages


def test_historical_roots_have_no_tracked_diff() -> None:
    assert _git_lines("diff", "--name-only", "--", str(S1_ROOT), str(S2_ROOT), str(S3_ROOT)) == []
