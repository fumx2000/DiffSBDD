from __future__ import annotations

import ast
import ctypes
import errno
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_bulk_download_admission_admit_015_mandatory_training_authorization_enforcement_contract_design_gate
    as gate,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / (
    "scripts/"
    "check_covapie_bulk_download_admission_admit_015_mandatory_"
    "training_authorization_enforcement_contract_v1.py"
)
SPEC = importlib.util.spec_from_file_location(
    "admit015_mandatory_enforcement_checker", CHECKER_PATH
)
assert SPEC is not None and SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


@pytest.fixture(scope="module")
def snapshot():
    return gate.build_frozen_source_snapshot()


@pytest.fixture(scope="module")
def payloads(snapshot):
    return gate.build_artifacts(snapshot)


def _canonical_result():
    return gate.exact15_runtime.evaluate_admission_rule(
        gate.ADMISSION_RULE_ID,
        {},
        batch_context=None,
        evaluation_context=None,
        download_result_context=None,
        stage_authorization_context={gate.AUTHORIZATION_ITEM: True},
    )


def _returning(value):
    def dispatch(*_args, **_kwargs):
        return value

    return dispatch


def _write_exact6(root: Path, payloads, *, replacement: bool = False):
    root.mkdir(parents=True)
    for name in checker.OUTPUT_FILES:
        content = payloads[name]
        if replacement:
            content = b"replacement:" + name.encode()
        (root / name).write_bytes(content)


def _git(root: Path, *arguments: str) -> str:
    return subprocess.check_output(
        ["git", *arguments],
        cwd=root,
        text=True,
    ).strip()


def _make_lifecycle_repo(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "repo"
    for relative in (
        Path("src/covalent_ext"),
        Path("scripts"),
        Path("tests"),
        Path("docs"),
        Path("data/derived/covalent_small"),
    ):
        (root / relative).mkdir(parents=True, exist_ok=True)
    for relative in (
        Path("src/covalent_ext/baseline.py"),
        Path("scripts/baseline.py"),
        Path("tests/baseline.py"),
        Path("docs/baseline.md"),
        Path("data/derived/covalent_small/baseline.txt"),
    ):
        (root / relative).write_text("baseline\n")
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "tests@example.invalid")
    _git(root, "config", "user.name", "CovaPIE tests")
    _git(root, "add", "--", *(
        relative.as_posix()
        for relative in (
            Path("src/covalent_ext/baseline.py"),
            Path("scripts/baseline.py"),
            Path("tests/baseline.py"),
            Path("docs/baseline.md"),
            Path("data/derived/covalent_small/baseline.txt"),
        )
    ))
    _git(root, "commit", "-q", "-m", "baseline")
    base = _git(root, "rev-parse", "HEAD")
    for index, relative in enumerate(checker.EXACT10, 1):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"candidate {index}\n")
    return root, base


def _manifest_bytes(manifest, *, sort_keys: bool = True) -> bytes:
    return (
        json.dumps(manifest, indent=2, sort_keys=sort_keys) + "\n"
    ).encode()


def _synchronized_tamper(payloads, category: str, monkeypatch):
    altered = dict(payloads)
    manifest = json.loads(altered[checker.MANIFEST_FILENAME])
    sort_keys = True
    if category == "api":
        forged_name = "forged_admit_015_training_authorization"
        forged_signature = checker.FUTURE_PUBLIC_SIGNATURE.replace(
            checker.FUTURE_PUBLIC_FUNCTION,
            forged_name,
        )
        rows = checker._csv_rows(
            altered[checker.API_FILENAME],
            checker.API_COLUMNS,
        )
        rows[0]["frozen_value"] = forged_name
        rows[1]["frozen_value"] = forged_signature
        altered[checker.API_FILENAME] = checker._csv_bytes(
            checker.API_COLUMNS,
            rows,
        )
        manifest["future_api_contract"]["public_function_name"] = forged_name
        manifest["future_api_contract"]["exact_signature"] = forged_signature
        monkeypatch.setattr(gate, "FUTURE_PUBLIC_FUNCTION", forged_name)
        monkeypatch.setattr(gate, "FUTURE_PUBLIC_SIGNATURE", forged_signature)
    elif category == "error_code":
        forged = "ADMIT_015_FORGED_DENIAL"
        codes = list(gate.FUTURE_ERROR_CODES)
        codes[2] = forged
        monkeypatch.setattr(gate, "FUTURE_ERROR_CODES", tuple(codes))
        manifest["future_api_contract"]["error_codes"][2] = forged
        rows = checker._csv_rows(
            altered[checker.TRUTH_FILENAME],
            checker.TRUTH_COLUMNS,
        )
        for row in rows:
            if row["expected_error_code"] == checker.FUTURE_ERROR_CODES[2]:
                row["expected_error_code"] = forged
                row["observed_error_code"] = forged
        altered[checker.TRUTH_FILENAME] = checker._csv_bytes(
            checker.TRUTH_COLUMNS,
            rows,
        )
    elif category == "protected":
        actions = list(gate.PROTECTED_ACTIONS)
        actions[0] = (actions[0][0], "forged loader action")
        monkeypatch.setattr(gate, "PROTECTED_ACTIONS", tuple(actions))
        rows = checker._csv_rows(
            altered[checker.PROTECTED_FILENAME],
            checker.PROTECTED_COLUMNS,
        )
        rows[0]["action_semantic_name"] = "forged loader action"
        altered[checker.PROTECTED_FILENAME] = checker._csv_bytes(
            checker.PROTECTED_COLUMNS,
            rows,
        )
        manifest["protected_actions"][0][
            "semantic_name"
        ] = "forged loader action"
    elif category == "mask":
        masks = list(gate.CANONICAL_MASKS)
        masks[3] = ("replacement_mask", "B4")
        monkeypatch.setattr(gate, "CANONICAL_MASKS", tuple(masks))
        manifest["canonical_masks"][3] = {
            "semantic_name": "replacement_mask",
            "alias": "B4",
        }
    elif category == "readiness_type":
        manifest["readiness"]["ready_for_training"] = 0
        manifest["ready_for_training"] = 0
    elif category == "pre_ids":
        manifest["precondition_transition"][
            "remaining_open_precondition_ids"
        ] = ["PRE_035", "PRE_036", "PRE_038"]
    elif category == "source_digest":
        path = checker.SOURCE_PATHS[0].as_posix()
        forged = "0" * 64
        source_sha = dict(gate.SOURCE_SHA256)
        source_sha[gate.SOURCE_PATHS[0]] = forged
        monkeypatch.setattr(gate, "SOURCE_SHA256", source_sha)
        manifest["source_sha256"][path] = forged
        manifest["source_verification"][0]["filesystem_sha256"] = forged
    elif category == "nested_missing":
        manifest["future_api_contract"].pop("exception_on_denial")
    elif category == "nested_extra":
        manifest["pass_invariants"]["unexpected"] = False
    elif category == "nested_reorder":
        nested = manifest["issue_continuity"]
        manifest["issue_continuity"] = dict(reversed(tuple(nested.items())))
        sort_keys = False
    elif category == "safety":
        rows = checker._csv_rows(
            altered[checker.SAFETY_FILENAME],
            checker.SAFETY_COLUMNS,
        )
        rows[0]["observed_state"] = "true"
        rows[0]["safety_passed"] = "true"
        altered[checker.SAFETY_FILENAME] = checker._csv_bytes(
            checker.SAFETY_COLUMNS,
            rows,
        )
        monkeypatch.setattr(gate, "_safety_rows", lambda: rows)
    elif category == "truth":
        rows = checker._csv_rows(
            altered[checker.TRUTH_FILENAME],
            checker.TRUTH_COLUMNS,
        )
        rows[0]["case_id"] = "forged_case"
        rows[0]["case_group"] = "forged_group"
        rows[0]["case_passed"] = "true"
        altered[checker.TRUTH_FILENAME] = checker._csv_bytes(
            checker.TRUTH_COLUMNS,
            rows,
        )
        monkeypatch.setattr(gate, "_truth_rows", lambda: rows)
    else:
        raise AssertionError("unknown tamper category")
    for name in checker.OUTPUT_FILES[:-1]:
        manifest["output_sha256"][name] = checker._sha(altered[name])
    altered[checker.MANIFEST_FILENAME] = _manifest_bytes(
        manifest,
        sort_keys=sort_keys,
    )
    monkeypatch.setattr(
        gate,
        "build_artifacts",
        lambda *_args, **_kwargs: altered,
    )
    return altered


def test_base_identity_and_canonical_runtime():
    assert gate.BASE_COMMIT == "4a3e813912cf704a1c6508ab21cd198e911b6b3c"
    assert gate.BASE_PARENT == "d70d7d8919c3ec59e0b3d864ec8e496695ab770b"
    assert gate.BASE_TREE == "a9c634a60c989838dd9334a0d037de62f9d0ee75"
    assert sys.implementation.name == "cpython"
    assert tuple(sys.version_info[:3]) == (3, 10, 4)


def test_exact_future_api_metadata_and_signature():
    assert (
        gate.FUTURE_PUBLIC_FUNCTION
        == "require_admit_015_training_authorization"
    )
    assert gate.FUTURE_PUBLIC_SIGNATURE == (
        "require_admit_015_training_authorization("
        "candidate_record: Mapping[str, object], *, "
        "stage_authorization_context: Mapping[str, object] | None"
        ") -> UnifiedAdmissionRuleEvaluation"
    )
    assert gate.FUTURE_ERROR_FIELDS == (
        "schema_version",
        "error_code",
        "admission_rule_id",
        "reason",
    )
    assert gate.FUTURE_ERROR_FIELD_TYPES == ("str", "str", "str", "str")
    assert gate.FUTURE_ERROR_SIGNATURE == (
        "Admit015TrainingAuthorizationEnforcementError("
        "schema_version: str, error_code: str, admission_rule_id: str, "
        "reason: str)"
    )


def test_future_guard_is_not_implemented():
    assert not hasattr(gate, gate.FUTURE_PUBLIC_FUNCTION)
    source = Path(gate.__file__).read_text()
    tree = ast.parse(source)
    assert gate.FUTURE_PUBLIC_FUNCTION not in {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }


def test_exact34_source_boundary(snapshot):
    assert len(snapshot) == 34
    assert tuple(item.relative_path for item in snapshot) == gate.SOURCE_PATHS
    assert all(item.index_stage == 0 for item in snapshot)
    assert all(item.index_mode == item.base_tree_mode for item in snapshot)
    assert all(item.index_blob == item.base_tree_blob for item in snapshot)


def test_source_sha_and_bytes_are_frozen(snapshot):
    assert all(
        gate._sha(item.content) == gate.SOURCE_SHA256[item.relative_path]
        == item.filesystem_sha256
        for item in snapshot
    )


def test_artifacts_are_byte_deterministic(snapshot, payloads):
    assert gate.build_artifacts(snapshot) == payloads
    assert tuple(payloads) == gate.OUTPUT_FILES


def test_api_contract_exact_rows(payloads):
    rows = gate._csv_rows(payloads[gate.API_FILENAME], gate.API_COLUMNS)
    assert len(rows) == 44
    assert rows[0]["frozen_value"] == gate.FUTURE_PUBLIC_FUNCTION
    assert rows[1]["frozen_value"] == gate.FUTURE_PUBLIC_SIGNATURE
    assert all(row["contract_passed"] == "true" for row in rows)


def test_exact11_protected_action_boundary(payloads):
    rows = gate._csv_rows(
        payloads[gate.PROTECTED_FILENAME], gate.PROTECTED_COLUMNS
    )
    assert len(rows) == 11
    assert tuple(
        (row["action_id"], row["action_semantic_name"]) for row in rows
    ) == gate.PROTECTED_ACTIONS
    assert all(row["blocked_count_expected"] == "0" for row in rows)
    assert all(row["design_pass_executes_action"] == "false" for row in rows)


def test_canonical_pass_exactly_once_and_exact_routing():
    context = {gate.AUTHORIZATION_ITEM: True}
    observed = []

    def dispatch(rule_id, candidate, **kwargs):
        observed.append((rule_id, candidate, kwargs))
        return _canonical_result()

    decision = gate.simulate_admit_015_mandatory_enforcement_design(
        {},
        stage_authorization_context=context,
        dispatcher=dispatch,
    )
    assert decision.released_future_in_memory_continuation is True
    assert decision.error_code == ""
    assert decision.runtime_call_count == 1
    assert decision.selected_rule_id == "ADMIT_015"
    assert observed[0][2] == {
        "batch_context": None,
        "evaluation_context": None,
        "download_result_context": None,
        "stage_authorization_context": context,
    }
    assert observed[0][2]["stage_authorization_context"] is context


@pytest.mark.parametrize(
    ("candidate", "context"),
    [
        ({}, {gate.AUTHORIZATION_ITEM: False}),
        (object(), {gate.AUTHORIZATION_ITEM: True}),
        ({}, None),
        ({}, {}),
    ],
)
def test_every_business_nonpass_fails_closed(candidate, context):
    decision = gate.simulate_admit_015_mandatory_enforcement_design(
        candidate, stage_authorization_context=context
    )
    assert decision.released_future_in_memory_continuation is False
    assert decision.error_code == gate.FUTURE_ERROR_CODES[2]
    assert decision.runtime_call_count == 1


def test_dispatcher_error_fails_closed():
    def fail(*_args, **_kwargs):
        raise RuntimeError("failure")

    decision = gate.simulate_admit_015_mandatory_enforcement_design(
        {},
        stage_authorization_context={gate.AUTHORIZATION_ITEM: True},
        dispatcher=fail,
    )
    assert decision.error_code == gate.FUTURE_ERROR_CODES[0]
    assert decision.runtime_call_count == 1


def test_wrong_result_type_fails_closed():
    decision = gate.simulate_admit_015_mandatory_enforcement_design(
        {},
        stage_authorization_context={gate.AUTHORIZATION_ITEM: True},
        dispatcher=_returning(object()),
    )
    assert decision.error_code == gate.FUTURE_ERROR_CODES[1]
    assert decision.released_future_in_memory_continuation is False


def test_result_subclass_fails_closed():
    canonical = _canonical_result()

    class Subclass(gate.exact15_runtime.UnifiedAdmissionRuleEvaluation):
        pass

    value = Subclass(
        *(getattr(canonical, name) for name in gate.RESULT_FIELDS)
    )
    decision = gate.simulate_admit_015_mandatory_enforcement_design(
        {},
        stage_authorization_context={gate.AUTHORIZATION_ITEM: True},
        dispatcher=_returning(value),
    )
    assert decision.error_code == gate.FUTURE_ERROR_CODES[1]


@pytest.mark.parametrize(
    "updates",
    [
        {"schema_version": "wrong"},
        {"admission_rule_id": "ADMIT_014"},
        {"outcome": "blocked"},
        {"passed": False},
        {"blocks_candidate": True},
        {"reason": "drift"},
        {"reason": 1},
        {"normalized_values": ()},
        {"normalized_values": []},
        {
            "normalized_values": (
                (gate.AUTHORIZATION_ITEM, "false"),
            )
        },
        {"validated_candidate_fields": ("x",)},
        {"consumed_candidate_fields": ("x",)},
        {"consumed_context_items": ()},
        {"evaluator_io_used": True},
        {"adapter_id": "wrong"},
    ],
)
def test_every_exact13_pass_invariant_drift_fails_closed(updates):
    value = gate._mutated_result(**updates)
    decision = gate.simulate_admit_015_mandatory_enforcement_design(
        {},
        stage_authorization_context={gate.AUTHORIZATION_ITEM: True},
        dispatcher=_returning(value),
    )
    assert decision.released_future_in_memory_continuation is False
    assert decision.error_code == gate.FUTURE_ERROR_CODES[2]


def test_repeated_runtime_call_attempt_fails_without_call():
    decision = gate.simulate_admit_015_mandatory_enforcement_design(
        {},
        stage_authorization_context={gate.AUTHORIZATION_ITEM: True},
        attempted_repeated_runtime_call=True,
    )
    assert decision.error_code == gate.FUTURE_ERROR_CODES[4]
    assert decision.runtime_call_count == 0


def test_precomputed_result_replay_is_forbidden():
    decision = gate.simulate_admit_015_mandatory_enforcement_design(
        {},
        stage_authorization_context={gate.AUTHORIZATION_ITEM: True},
        attempted_precomputed_result=_canonical_result(),
    )
    assert decision.error_code == gate.FUTURE_ERROR_CODES[3]
    assert decision.runtime_call_count == 0


@pytest.mark.parametrize(
    "attempt",
    ["combined", "admit014"],
)
def test_combined_and_admit014_true_cannot_authorize_training(attempt):
    kwargs = (
        {"attempted_combined_verdict": True}
        if attempt == "combined"
        else {"attempted_admit_014_permission": True}
    )
    decision = gate.simulate_admit_015_mandatory_enforcement_design(
        {},
        stage_authorization_context={gate.AUTHORIZATION_ITEM: False},
        **kwargs,
    )
    assert decision.error_code == gate.FUTURE_ERROR_CODES[5]
    assert decision.runtime_call_count == 0


@pytest.mark.parametrize("authorized", [False, True])
def test_all_protected_action_counts_remain_zero(authorized):
    decision = gate.simulate_admit_015_mandatory_enforcement_design(
        {},
        stage_authorization_context={
            gate.AUTHORIZATION_ITEM: authorized
        },
    )
    assert decision.protected_action_counts == gate.ZERO_PROTECTED_ACTION_COUNTS
    assert decision.real_training_executed is False


def test_truth_matrix_exact29_groups_and_cases(payloads):
    rows = gate._csv_rows(payloads[gate.TRUTH_FILENAME], gate.TRUTH_COLUMNS)
    assert len(rows) == 29
    assert len({row["case_group"] for row in rows}) == 23
    required = {
        "canonical_admit_015_pass",
        "dispatcher_failure",
        "result_subclass",
        "result_field_order_drift",
        "result_field_type_drift",
        "repeated_runtime_call_attempt",
        "precomputed_result_replay",
        "admit_014_true_cannot_authorize_training",
        "combined_true_cannot_override_blocked",
        "blocked_protected_counts_zero",
        "pass_releases_future_in_memory_only",
    }
    assert required <= {row["case_id"] for row in rows}
    assert all(row["case_passed"] == "true" for row in rows)


def test_safety_exact28_and_training_boundaries(payloads):
    rows = gate._csv_rows(payloads[gate.SAFETY_FILENAME], gate.SAFETY_COLUMNS)
    assert len(rows) == 28
    states = {row["audit_item"]: row["observed_state"] for row in rows}
    for item in (
        "torch_imported",
        "dataloader_instantiated",
        "checkpoint_loaded",
        "model_forward_executed",
        "loss_computed",
        "backward_executed",
        "optimizer_created",
        "scheduler_created",
        "parameter_updated",
        "checkpoint_written",
        "training_result_materialized",
        "network_executed",
        "provider_executed",
        "download_executed",
        "raw_accessed",
    ):
        assert states[item] == "false"


def test_precondition_only_resolves_pre034(payloads):
    manifest = json.loads(payloads[gate.MANIFEST_FILENAME])
    transition = manifest["precondition_transition"]
    assert transition == {
        "row_count": 45,
        "resolved_precondition_ids": ["PRE_034"],
        "remaining_open_precondition_ids": [
            "PRE_035",
            "PRE_036",
            "PRE_038",
            "PRE_042",
        ],
        "complete_count": 41,
        "supported_but_not_frozen_count": 0,
        "incomplete_count": 4,
        "implementation_blocking_count": 4,
    }


def test_exact30_is_byte_identical(payloads, snapshot):
    source = gate._source(
        snapshot,
        "covapie_admit_001_to_015_runtime_issue_readiness_inventory.csv",
    ).content
    assert payloads[gate.ISSUE_FILENAME] == source
    manifest = json.loads(payloads[gate.MANIFEST_FILENAME])
    assert manifest["issue_continuity"]["transition_count"] == 0


def test_readiness_current_permission_and_execution_count(payloads):
    manifest = json.loads(payloads[gate.MANIFEST_FILENAME])
    readiness = manifest["readiness"]
    assert readiness[
        "mandatory_training_authorization_enforcement_api_frozen"
    ] is True
    assert readiness[
        "ready_for_admit_015_mandatory_training_authorization_enforcement_implementation"
    ] is True
    assert readiness[
        "mandatory_training_authorization_enforcement_implemented"
    ] is False
    assert readiness["combined_permission_semantics_frozen"] is False
    assert readiness["combined_candidate_verdict_implemented"] is False
    assert readiness["cross_rule_aggregation_implemented"] is False
    assert readiness["feature_semantics_audit_completed"] is False
    assert readiness["real_training_ready"] is False
    assert readiness["ready_for_training"] is False
    assert manifest["current_permission"] is False
    assert manifest["authorized_admit_015_training_execution_count"] == 0


def test_five_masks_include_scaffold_only_b3(payloads):
    manifest = json.loads(payloads[gate.MANIFEST_FILENAME])
    assert manifest["canonical_masks"] == [
        {"semantic_name": "warhead_only", "alias": "A"},
        {"semantic_name": "linker_plus_warhead", "alias": "B"},
        {"semantic_name": "scaffold_plus_warhead", "alias": "B2"},
        {"semantic_name": "scaffold_only", "alias": "B3"},
        {
            "semantic_name": "scaffold_plus_linker_plus_warhead",
            "alias": "C",
        },
    ]


def test_step12d_and_feature_semantics_remain_blocking(payloads):
    manifest = json.loads(payloads[gate.MANIFEST_FILENAME])
    assert (
        manifest["step12d_status"]
        == "smoke_legality_only_not_final_training_feature_contract"
    )
    assert "UNKNOWN_ATOM_FEATURE_POLICY" in manifest["feature_semantics_note"]
    assert "feature_semantics_known=False" in manifest[
        "feature_semantics_note"
    ]


def test_production_has_no_forbidden_import_or_training_call():
    checker._verify_candidate_surface()


def test_materializer_new_publish_and_inode_preserving_noop(
    tmp_path, payloads
):
    root = tmp_path / "evidence"
    plan = gate._inspect_output_target_read_only(root)
    gate._materialize_set(plan, payloads)
    before = {
        name: gate._identity(os.lstat(root / name))
        for name in gate.OUTPUT_FILES
    }
    second = gate._inspect_output_target_read_only(root)
    gate._materialize_set(second, payloads)
    after = {
        name: gate._identity(os.lstat(root / name))
        for name in gate.OUTPUT_FILES
    }
    assert before == after


def test_materializer_mismatch_fails_without_repair(tmp_path, payloads):
    root = tmp_path / "evidence"
    gate._materialize_set(
        gate._inspect_output_target_read_only(root), payloads
    )
    target = root / gate.API_FILENAME
    target.write_bytes(b"tamper")
    before = target.read_bytes()
    with pytest.raises(ValueError):
        gate._materialize_set(
            gate._inspect_output_target_read_only(root), payloads
        )
    assert target.read_bytes() == before


def test_gpfs_einval_fails_closed_and_retains_authenticated_staging(
    tmp_path, payloads, monkeypatch
):
    def fail_rename(*_args):
        ctypes.set_errno(errno.EINVAL)
        return -1

    monkeypatch.setattr(gate, "_RENAMEAT2", fail_rename)
    root = tmp_path / "evidence"
    with pytest.raises(gate.MaterializationRetentionError) as caught:
        gate._materialize_set(
            gate._inspect_output_target_read_only(root), payloads
        )
    assert caught.value.binding_authenticated is True
    retained = caught.value.authenticated_retained_path
    assert retained is not None and retained.is_dir()
    assert not root.exists()


def test_materializer_rejects_symlink_output(tmp_path):
    target = tmp_path / "real"
    target.mkdir()
    link = tmp_path / "evidence"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError):
        gate._inspect_output_target_read_only(link)


def test_checker_rejects_manifest_duplicate():
    with pytest.raises(AssertionError, match="duplicate"):
        checker._strict_json(b'{"a":1,"a":1}')


def test_checker_local_full_row_and_manifest_reconstruction():
    local_snapshot = checker._build_local_source_snapshot()
    row_sets = (
        (
            checker.API_FILENAME,
            checker.API_COLUMNS,
            checker._expected_api_rows(),
            44,
        ),
        (
            checker.PROTECTED_FILENAME,
            checker.PROTECTED_COLUMNS,
            checker._expected_protected_rows(),
            11,
        ),
        (
            checker.TRUTH_FILENAME,
            checker.TRUTH_COLUMNS,
            checker._expected_truth_rows(),
            29,
        ),
        (
            checker.SAFETY_FILENAME,
            checker.SAFETY_COLUMNS,
            checker._expected_safety_rows(),
            28,
        ),
    )
    for filename, columns, rows, count in row_sets:
        assert len(rows) == count
        assert (
            checker._sha(checker._csv_bytes(columns, rows))
            == checker.EXPECTED_OUTPUT_SHA256[filename]
        )
    manifest = checker._expected_manifest(local_snapshot)
    assert len(manifest) == 64
    assert tuple(manifest) == tuple(sorted(manifest))


@pytest.mark.parametrize(
    "mutation",
    [
        "nested_missing",
        "nested_extra",
        "nested_reorder",
        "bool_to_int",
    ],
)
def test_recursive_manifest_comparator_is_exact(mutation):
    expected = checker._expected_manifest(
        checker._build_local_source_snapshot()
    )
    actual = json.loads(json.dumps(expected))
    if mutation == "nested_missing":
        actual["future_api_contract"].pop("exception_on_denial")
    elif mutation == "nested_extra":
        actual["pass_invariants"]["unexpected"] = False
    elif mutation == "nested_reorder":
        nested = actual["issue_continuity"]
        actual["issue_continuity"] = dict(reversed(tuple(nested.items())))
    else:
        actual["readiness"]["ready_for_training"] = 0
    with pytest.raises(AssertionError):
        checker._assert_recursive_exact(actual, expected)


@pytest.mark.parametrize(
    "category",
    [
        "api",
        "error_code",
        "protected",
        "mask",
        "readiness_type",
        "pre_ids",
        "source_digest",
        "nested_missing",
        "nested_extra",
        "nested_reorder",
        "safety",
        "truth",
    ],
)
def test_checker_rejects_synchronized_candidate_and_artifact_tamper(
    payloads,
    monkeypatch,
    category,
):
    altered = _synchronized_tamper(payloads, category, monkeypatch)
    assert gate.build_artifacts() is altered
    with pytest.raises(AssertionError):
        checker._verify_semantics(altered)


def test_checker_never_calls_candidate_artifact_builder(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("candidate builder must not be called")

    monkeypatch.setattr(gate, "build_artifacts", forbidden)
    assert checker.verify_artifacts()["all_checks_passed"] is True


def test_exact6_reader_normal_binding(tmp_path, payloads, monkeypatch):
    root = tmp_path / "derived" / checker.STAGE_NAME
    _write_exact6(root, payloads)
    monkeypatch.setattr(checker, "DERIVED_ROOT", root)
    assert checker._read_exact_outputs() == payloads


@pytest.mark.parametrize(
    "race",
    [
        "root_replacement",
        "parent_replacement",
        "seventh_file",
        "missing_leaf",
        "same_byte_replaced_leaf",
    ],
)
def test_exact6_reader_rejects_final_leaf_races(
    tmp_path,
    payloads,
    monkeypatch,
    race,
):
    parent = tmp_path / "derived"
    root = parent / checker.STAGE_NAME
    _write_exact6(root, payloads)
    monkeypatch.setattr(checker, "DERIVED_ROOT", root)
    original_stat = checker.os.stat
    watched = checker.OUTPUT_FILES[0]
    calls = 0
    triggered = False

    def racing_stat(path, *args, **kwargs):
        nonlocal calls, triggered
        if (
            path == watched
            and kwargs.get("dir_fd") is not None
            and kwargs.get("follow_symlinks") is False
        ):
            calls += 1
            if calls == 3:
                triggered = True
                if race == "root_replacement":
                    old = parent / "held-old-root"
                    root.rename(old)
                    _write_exact6(root, payloads, replacement=True)
                elif race == "parent_replacement":
                    old = tmp_path / "held-old-parent"
                    parent.rename(old)
                    _write_exact6(root, payloads, replacement=True)
                elif race == "seventh_file":
                    (root / "seventh.txt").write_bytes(b"seventh")
                elif race == "missing_leaf":
                    (root / checker.OUTPUT_FILES[-1]).unlink()
                else:
                    target = root / watched
                    replacement = root / "same-byte-replacement"
                    replacement.write_bytes(target.read_bytes())
                    replacement.replace(target)
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(checker.os, "stat", racing_stat)
    with pytest.raises(AssertionError):
        checker._read_exact_outputs()
    assert triggered is True


def test_checker_accepts_current_exact6():
    manifest = checker.verify_artifacts()
    assert manifest["all_checks_passed"] is True


def test_lifecycle_matches_pre_or_post_commit_state():
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    expected = "pre_commit" if head == gate.BASE_COMMIT else "post_commit"
    assert checker.verify_lifecycle() == expected


def test_lifecycle_normal_pre_commit(tmp_path):
    root, base = _make_lifecycle_repo(tmp_path)
    assert (
        checker.verify_lifecycle(root, checker.EXACT10, base=base)
        == "pre_commit"
    )


def test_lifecycle_normal_post_commit(tmp_path):
    root, base = _make_lifecycle_repo(tmp_path)
    _git(root, "add", "--", *(path.as_posix() for path in checker.EXACT10))
    _git(root, "commit", "-q", "-m", "candidate")
    assert (
        checker.verify_lifecycle(root, checker.EXACT10, base=base)
        == "post_commit"
    )


def test_lifecycle_rejects_allow_empty_head_drift(tmp_path):
    root, base = _make_lifecycle_repo(tmp_path)
    _git(root, "add", "--", *(path.as_posix() for path in checker.EXACT10))
    _git(root, "commit", "-q", "-m", "candidate")
    _git(root, "commit", "--allow-empty", "-q", "-m", "empty drift")
    with pytest.raises(AssertionError, match="allow-empty"):
        checker.verify_lifecycle(root, checker.EXACT10, base=base)


def test_lifecycle_rejects_head_change_between_snapshots(
    tmp_path,
    monkeypatch,
):
    root, base = _make_lifecycle_repo(tmp_path)
    original = checker._assert_recursive_inventory

    def drift_during_scan(scan_root, exact10):
        original(scan_root, exact10)
        _git(root, "commit", "--allow-empty", "-q", "-m", "mid-scan drift")

    monkeypatch.setattr(
        checker,
        "_assert_recursive_inventory",
        drift_during_scan,
    )
    with pytest.raises(AssertionError, match="final HEAD"):
        checker.verify_lifecycle(root, checker.EXACT10, base=base)


@pytest.mark.parametrize(
    "bounded_root",
    [
        Path("src/covalent_ext"),
        Path("scripts"),
        Path("tests"),
        Path("docs"),
    ],
)
def test_tracked_nested_stage_family_file_rejected(
    tmp_path,
    bounded_root,
):
    root, base = _make_lifecycle_repo(tmp_path)
    nested = (
        root
        / bounded_root
        / "nested"
        / f"{checker.STAGE_TOKEN}_hidden.txt"
    )
    nested.parent.mkdir()
    nested.write_text("tracked hidden stage residue\n")
    _git(root, "add", "--", nested.relative_to(root).as_posix())
    _git(root, "commit", "-q", "-m", "tracked hidden residue")
    base = _git(root, "rev-parse", "HEAD")
    with pytest.raises(AssertionError, match="recursive inventory"):
        checker.verify_lifecycle(root, checker.EXACT10, base=base)


@pytest.mark.parametrize("ignored", [False, True])
def test_generic_symlink_rejected_before_filter_without_external_open(
    tmp_path,
    monkeypatch,
    ignored,
):
    root, _ = _make_lifecycle_repo(tmp_path)
    external = tmp_path / "external-target"
    external.mkdir()
    sentinel = external / "sentinel.txt"
    sentinel.write_text("do not touch\n")
    target_identity = checker._identity(os.lstat(external))
    sentinel_identity = checker._identity(os.lstat(sentinel))
    link = root / "docs/generic_link"
    link.symlink_to(external, target_is_directory=True)
    if ignored:
        (root / ".gitignore").write_text("docs/generic_link\n")
        _git(root, "add", "--", ".gitignore")
    else:
        _git(root, "add", "--", "docs/generic_link")
    _git(root, "commit", "-q", "-m", "generic symlink fixture")
    base = _git(root, "rev-parse", "HEAD")
    original_open = checker.os.open
    opened_link = False

    def recording_open(path, *args, **kwargs):
        nonlocal opened_link
        if path == "generic_link":
            opened_link = True
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(checker.os, "open", recording_open)
    with pytest.raises(AssertionError, match="generic symlink"):
        checker.verify_lifecycle(root, checker.EXACT10, base=base)
    assert opened_link is False
    assert checker._identity(os.lstat(external)) == target_identity
    assert checker._identity(os.lstat(sentinel)) == sentinel_identity
    assert sentinel.read_text() == "do not touch\n"


@pytest.mark.parametrize("timing", ["pre_open", "post_open"])
def test_top_directory_replacement_rejected(
    tmp_path,
    monkeypatch,
    timing,
):
    root, _ = _make_lifecycle_repo(tmp_path)
    original_open = checker.os.open
    triggered = False

    def replacing_open(path, *args, **kwargs):
        nonlocal triggered
        if path == "docs" and kwargs.get("dir_fd") is not None and not triggered:
            triggered = True
            old = root / "docs-held-old"
            if timing == "pre_open":
                (root / "docs").rename(old)
                (root / "docs").mkdir()
                return original_open(path, *args, **kwargs)
            descriptor = original_open(path, *args, **kwargs)
            (root / "docs").rename(old)
            (root / "docs").mkdir()
            return descriptor
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(checker.os, "open", replacing_open)
    with pytest.raises(AssertionError, match="binding|inventory"):
        checker._bounded_recursive_stage_inventory(root)
    assert triggered is True


def test_ignored_nested_same_stage_path_rejected(tmp_path):
    root, _ = _make_lifecycle_repo(tmp_path)
    ignored_dir = root / "docs/ignored"
    ignored_dir.mkdir()
    nested = ignored_dir / f"{checker.STAGE_TOKEN}_hidden.md"
    nested.write_text("ignored hidden stage residue\n")
    (root / ".gitignore").write_text("docs/ignored/\n")
    _git(root, "add", "--", ".gitignore")
    _git(root, "commit", "-q", "-m", "ignore fixture")
    base = _git(root, "rev-parse", "HEAD")
    with pytest.raises(AssertionError, match="ignored"):
        checker.verify_lifecycle(root, checker.EXACT10, base=base)


def test_sibling_derived_stage_root_rejected(tmp_path):
    root, _ = _make_lifecycle_repo(tmp_path)
    sibling = (
        root
        / "data/derived/covalent_small"
        / f"{checker.STAGE_NAME}_sibling"
    )
    sibling.mkdir()
    (sibling / "payload.txt").write_text("sibling\n")
    with pytest.raises(
        AssertionError,
        match="recursive inventory|derived root|same-stage leaf",
    ):
        checker._assert_recursive_inventory(root, checker.EXACT10)


def test_matching_derived_root_symlink_rejected_without_follow(
    tmp_path,
    monkeypatch,
):
    root, _ = _make_lifecycle_repo(tmp_path)
    external = tmp_path / "external-derived-target"
    external.mkdir()
    sentinel = external / "sentinel"
    sentinel.write_text("unread\n")
    target_identity = checker._identity(os.lstat(external))
    stage_root = root / checker.STAGE
    for child in stage_root.iterdir():
        child.unlink()
    stage_root.rmdir()
    stage_root.symlink_to(external, target_is_directory=True)
    original_open = checker.os.open
    followed = False

    def recording_open(path, *args, **kwargs):
        nonlocal followed
        if path == checker.STAGE_NAME:
            followed = True
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(checker.os, "open", recording_open)
    with pytest.raises(AssertionError, match="derived root unsafe"):
        checker._bounded_recursive_stage_inventory(root)
    assert followed is False
    assert checker._identity(os.lstat(external)) == target_identity
    assert sentinel.read_text() == "unread\n"


def test_exact10_inventory_is_regular_safe_and_matches_lifecycle():
    identities = checker._exact10_identities()
    assert len(identities) == 10
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    untracked = {
        item
        for item in subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=ROOT,
            text=True,
        ).splitlines()
    }
    expected = {path.as_posix() for path in checker.EXACT10}
    if head == gate.BASE_COMMIT:
        assert untracked == expected
    else:
        assert untracked == set()
        tracked = {
            item
            for item in subprocess.check_output(
                ["git", "ls-files", "--", *sorted(expected)],
                cwd=ROOT,
                text=True,
            ).splitlines()
        }
        assert tracked == expected


def test_no_protected_source_diff_and_no_forbidden_candidate_suffix():
    protected = (
        "equivariant_diffusion",
        "lightning_modules.py",
        "dataset.py",
        "data/prepare_crossdocked.py",
        "checkpoints",
        "data/raw",
    )
    changed = subprocess.check_output(
        ["git", "diff", "--name-only"], cwd=ROOT, text=True
    ).splitlines()
    assert not any(
        path == item or path.startswith(item + "/")
        for path in changed
        for item in protected
    )
    assert not any(
        path.suffix.lower() in checker.FORBIDDEN_SUFFIXES
        for path in checker.EXACT10
    )


@pytest.mark.parametrize(
    "relative",
    [
        gate.__file__,
        CHECKER_PATH,
    ],
)
def test_isolated_import_is_silent(relative, tmp_path):
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
                (
                    "import importlib.util,sys;"
                    f"s=importlib.util.spec_from_file_location('x',{str(relative)!r});"
                    "m=importlib.util.module_from_spec(s);"
                    "sys.modules['x']=m;"
                    "s.loader.exec_module(m)"
                ),
        ],
        cwd=tmp_path,
        env={
            **os.environ,
            "PYTHONPATH": str(ROOT / "src"),
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == b""
    assert completed.stderr == b""
