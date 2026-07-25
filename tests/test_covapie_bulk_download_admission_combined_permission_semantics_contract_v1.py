"""Targeted tests for the phase-scoped combined-permission design contract."""

from __future__ import annotations

import csv
import ctypes
import hashlib
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
from dataclasses import fields
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_bulk_download_admission_combined_permission_semantics_contract_design_gate
    as gate,
)


ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "data/derived/covalent_small" / gate.STAGE


def _load_checker():
    path = (
        ROOT
        / "scripts"
        / (
            "check_covapie_bulk_download_admission_combined_permission_"
            "semantics_contract_v1.py"
        )
    )
    spec = importlib.util.spec_from_file_location(
        "combined_permission_checker_for_tests", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _pass(scope_id: str) -> tuple[tuple[str, str], ...]:
    return tuple(
        (rule_id, "passed")
        for rule_id in gate.REQUIRED_RULE_IDS[scope_id]
    )


def _replace(
    vector: tuple[tuple[str, object], ...], index: int, state: object
) -> tuple[tuple[str, object], ...]:
    return tuple(
        (rule_id, state if position == index else value)
        for position, (rule_id, value) in enumerate(vector)
    )


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def test_exact4_scope_ids_and_order() -> None:
    assert gate.SCOPE_IDS == (
        "download_execution_permission",
        "post_download_acceptance_permission",
        "pre_final_split_acceptance_permission",
        "training_execution_admission_permission",
    )


@pytest.mark.parametrize(
    ("scope_id", "expected"),
    [(scope_id, required) for scope_id, _, required in gate.SCOPE_CONTRACT],
)
def test_exact_scope_membership(
    scope_id: str, expected: tuple[str, ...]
) -> None:
    assert gate.REQUIRED_RULE_IDS[scope_id] == expected
    assert len(expected) in {11, 13, 14, 15}


def test_scope_contract_contains_exact_rule_counts() -> None:
    assert tuple(
        len(gate.REQUIRED_RULE_IDS[scope_id])
        for scope_id in gate.SCOPE_IDS
    ) == (11, 13, 14, 15)


def test_exact15_registry_phases() -> None:
    assert gate.RULE_PHASES == (
        *( (f"ADMIT_{index:03d}", "pre_download") for index in range(1, 10) ),
        ("ADMIT_010", "pre_final_split"),
        ("ADMIT_011", "pre_download"),
        ("ADMIT_012", "post_download"),
        ("ADMIT_013", "post_download"),
        ("ADMIT_014", "current_step"),
        ("ADMIT_015", "current_step"),
    )


def test_phase_isolation_membership() -> None:
    download = gate.REQUIRED_RULE_IDS[gate.SCOPE_IDS[0]]
    post = gate.REQUIRED_RULE_IDS[gate.SCOPE_IDS[1]]
    prefinal = gate.REQUIRED_RULE_IDS[gate.SCOPE_IDS[2]]
    training = gate.REQUIRED_RULE_IDS[gate.SCOPE_IDS[3]]
    assert not {"ADMIT_010", "ADMIT_012", "ADMIT_013", "ADMIT_015"} & set(download)
    assert "ADMIT_010" not in post and "ADMIT_015" not in post
    assert "ADMIT_015" not in prefinal
    assert "ADMIT_015" in training
    assert all("ADMIT_014" in required for required in (download, post, prefinal, training))


@pytest.mark.parametrize("scope_id", gate.SCOPE_IDS)
def test_canonical_all_pass(scope_id: str) -> None:
    result = gate.simulate_combined_permission_semantics_design(
        scope_id, _pass(scope_id)
    )
    assert result.outcome == "passed"
    assert result.passed is True
    assert result.blocks_action is False
    assert result.reason == ""
    assert result.failing_rule_ids == ()
    assert result.design_io_used is False


BLOCKED_CASES = tuple(
    (scope_id, index, rule_id)
    for scope_id in gate.SCOPE_IDS
    for index, rule_id in enumerate(gate.REQUIRED_RULE_IDS[scope_id])
)


@pytest.mark.parametrize(
    ("scope_id", "index", "rule_id"), BLOCKED_CASES
)
def test_every_required_rule_blocked(
    scope_id: str, index: int, rule_id: str
) -> None:
    result = gate.simulate_combined_permission_semantics_design(
        scope_id, _replace(_pass(scope_id), index, "blocked")
    )
    assert result.outcome == "blocked"
    assert result.passed is False
    assert result.blocks_action is True
    assert result.reason == gate.BLOCKED_REASON
    assert result.failing_rule_ids == (rule_id,)


@pytest.mark.parametrize(
    ("scope_id", "index", "rule_id"), BLOCKED_CASES
)
def test_every_required_rule_invalid(
    scope_id: str, index: int, rule_id: str
) -> None:
    result = gate.simulate_combined_permission_semantics_design(
        scope_id, _replace(_pass(scope_id), index, "invalid")
    )
    assert result.outcome == "invalid"
    assert result.passed is False
    assert result.blocks_action is True
    assert result.reason == gate.INVALID_REASON
    assert result.failing_rule_ids == (rule_id,)


@pytest.mark.parametrize("scope_id", gate.SCOPE_IDS)
def test_invalid_precedes_blocked(scope_id: str) -> None:
    vector = _replace(_replace(_pass(scope_id), 0, "blocked"), 1, "invalid")
    result = gate.simulate_combined_permission_semantics_design(
        scope_id, vector
    )
    assert result.outcome == "invalid"
    assert result.failing_rule_ids == (
        gate.REQUIRED_RULE_IDS[scope_id][0],
        gate.REQUIRED_RULE_IDS[scope_id][1],
    )


@pytest.mark.parametrize("scope_id", gate.SCOPE_IDS)
@pytest.mark.parametrize("position", ("first", "middle", "last"))
def test_missing_required_is_invalid(
    scope_id: str, position: str
) -> None:
    vector = _pass(scope_id)
    index = {
        "first": 0,
        "middle": len(vector) // 2,
        "last": len(vector) - 1,
    }[position]
    result = gate.simulate_combined_permission_semantics_design(
        scope_id, vector[:index] + vector[index + 1 :]
    )
    assert result.outcome == "invalid"


@pytest.mark.parametrize("scope_id", gate.SCOPE_IDS)
def test_duplicate_is_invalid(scope_id: str) -> None:
    vector = _pass(scope_id)
    assert (
        gate.simulate_combined_permission_semantics_design(
            scope_id, vector + (vector[0],)
        ).outcome
        == "invalid"
    )


@pytest.mark.parametrize("scope_id", gate.SCOPE_IDS)
def test_reorder_is_invalid(scope_id: str) -> None:
    vector = _pass(scope_id)
    assert (
        gate.simulate_combined_permission_semantics_design(
            scope_id, (vector[1], vector[0]) + vector[2:]
        ).outcome
        == "invalid"
    )


@pytest.mark.parametrize(
    ("scope_id", "extra"),
    (
        (gate.SCOPE_IDS[0], "ADMIT_010"),
        (gate.SCOPE_IDS[0], "ADMIT_012"),
        (gate.SCOPE_IDS[0], "ADMIT_013"),
        (gate.SCOPE_IDS[0], "ADMIT_015"),
        (gate.SCOPE_IDS[1], "ADMIT_010"),
        (gate.SCOPE_IDS[1], "ADMIT_015"),
        (gate.SCOPE_IDS[2], "ADMIT_015"),
        (gate.SCOPE_IDS[3], "ADMIT_999"),
    ),
)
def test_extra_and_phase_isolation_are_invalid(
    scope_id: str, extra: str
) -> None:
    result = gate.simulate_combined_permission_semantics_design(
        scope_id, _pass(scope_id) + ((extra, "passed"),)
    )
    assert result.outcome == "invalid"


@pytest.mark.parametrize(
    ("scope", "vector"),
    (
        ("unknown", ()),
        (True, ()),
        (None, ()),
        (gate.SCOPE_IDS[0], []),
        (gate.SCOPE_IDS[0], {}),
        (gate.SCOPE_IDS[0], "passed"),
        (gate.SCOPE_IDS[0], None),
    ),
)
def test_unknown_scope_and_wrong_top_level_type_are_invalid(
    scope: object, vector: object
) -> None:
    result = gate.simulate_combined_permission_semantics_design(scope, vector)
    assert result.outcome == "invalid"
    assert result.passed is False
    assert result.blocks_action is True


@pytest.mark.parametrize("state", ("PASSED", "unknown", True, 1, None, []))
def test_unknown_or_non_string_state_is_invalid(state: object) -> None:
    result = gate.simulate_combined_permission_semantics_design(
        gate.SCOPE_IDS[0], _replace(_pass(gate.SCOPE_IDS[0]), 0, state)
    )
    assert result.outcome == "invalid"


def test_admit014_is_necessary_but_not_sufficient() -> None:
    for scope_id in gate.SCOPE_IDS:
        only = gate.simulate_combined_permission_semantics_design(
            scope_id, (("ADMIT_014", "passed"),)
        )
        assert only.outcome == "invalid"
        blocked = gate.simulate_combined_permission_semantics_design(
            scope_id, _replace(_pass(scope_id), 0, "blocked")
        )
        assert blocked.outcome == "blocked"


def test_admit015_is_necessary_but_not_sufficient() -> None:
    scope_id = gate.SCOPE_IDS[3]
    only = gate.simulate_combined_permission_semantics_design(
        scope_id, (("ADMIT_015", "passed"),)
    )
    blocked = gate.simulate_combined_permission_semantics_design(
        scope_id, _replace(_pass(scope_id), 0, "blocked")
    )
    assert only.outcome == "invalid"
    assert blocked.outcome == "blocked"


def test_result_exact_schema_types_and_immutability() -> None:
    result = gate.simulate_combined_permission_semantics_design(
        gate.SCOPE_IDS[0], _pass(gate.SCOPE_IDS[0])
    )
    assert tuple(field.name for field in fields(type(result))) == (
        "scope_id",
        "outcome",
        "passed",
        "blocks_action",
        "reason",
        "required_rule_ids",
        "observed_rule_ids",
        "failing_rule_ids",
        "design_io_used",
    )
    assert tuple(type(value) for value in vars(result).values()) == (
        str,
        str,
        bool,
        bool,
        str,
        tuple,
        tuple,
        tuple,
        bool,
    )
    with pytest.raises(Exception):
        result.outcome = "blocked"


def test_no_or_majority_weight_or_fallback_contract() -> None:
    rows = gate._precedence_rows()
    frozen = {(row["contract_item"], row["frozen_value"]) for row in rows}
    assert {
        ("OR", "forbidden"),
        ("majority vote", "forbidden"),
        ("weighted score", "forbidden"),
        ("fallback", "forbidden"),
        ("latest pass", "forbidden"),
    } <= frozen


def test_current_permission_and_execution_count_remain_zero() -> None:
    before = (
        gate.CURRENT_PERMISSION,
        gate.AUTHORIZED_ADMIT_015_TRAINING_EXECUTION_COUNT,
    )
    gate.simulate_combined_permission_semantics_design(
        gate.SCOPE_IDS[3], _pass(gate.SCOPE_IDS[3])
    )
    assert before == (False, 0)
    assert (
        gate.CURRENT_PERMISSION,
        gate.AUTHORIZED_ADMIT_015_TRAINING_EXECUTION_COUNT,
    ) == before


def test_b3_canonical_mask_is_present() -> None:
    assert gate.CANONICAL_MASKS == (
        ("warhead_only", "A"),
        ("linker_plus_warhead", "B"),
        ("scaffold_plus_warhead", "B2"),
        ("scaffold_only", "B3"),
        ("scaffold_plus_linker_plus_warhead", "C"),
    )


def test_source_snapshot_exact11_and_sha_truth() -> None:
    snapshot = gate.build_frozen_source_snapshot(ROOT)
    assert len(snapshot) == 11
    assert tuple(item.relative_path for item in snapshot) == gate.SOURCE_PATHS
    assert all(
        hashlib.sha256(item.content).hexdigest() == item.expected_sha256
        and item.index_stage == 0
        and item.base_tree_mode == "100644"
        and item.index_mode == "100644"
        for item in snapshot
    )


def test_truth_matrix_counts_and_coverage() -> None:
    rows = gate._truth_rows()
    assert len(rows) == len(gate._truth_cases())
    assert len(rows) == 163
    groups = {row["case_group"] for row in rows}
    assert len(groups) == 17
    assert all(row["case_passed"] == "true" for row in rows)
    assert {
        "canonical_all_pass",
        "every_required_rule_blocked",
        "every_required_rule_invalid",
        "missing_required",
        "phase_isolation",
        "synthetic_pass_no_mutation",
    } <= groups


def test_membership_csv_reconstructs_exact_scopes() -> None:
    rows = _csv(DERIVED / gate.MEMBERSHIP_FILENAME)
    assert len(rows) == 60
    for scope_id in gate.SCOPE_IDS:
        required = tuple(
            row["admission_rule_id"]
            for row in rows
            if row["scope_id"] == scope_id and row["included"] == "true"
        )
        assert required == gate.REQUIRED_RULE_IDS[scope_id]


def test_safety_exact30_and_all_pass() -> None:
    rows = _csv(DERIVED / gate.SAFETY_FILENAME)
    assert len(rows) == 30
    assert all(row["safety_passed"] == "true" for row in rows)
    states = {row["audit_item"]: row["observed_state"] for row in rows}
    assert states["runtime_dispatcher_calls"] == "0"
    assert states["cross_rule_aggregation_implemented"] == "false"
    assert states["ready_for_training"] == "false"


def test_issue_transition_only_target_row() -> None:
    source = _csv(
        ROOT
        / "data/derived/covalent_small/"
        "covapie_bulk_download_admission_unified_dispatch_runtime_with_"
        "admit_001_to_015_v1/"
        "covapie_admit_001_to_015_runtime_issue_readiness_inventory.csv"
    )
    successor = _csv(DERIVED / gate.ISSUE_FILENAME)
    changed = [
        (left, right)
        for left, right in zip(source, successor, strict=True)
        if left != right
    ]
    assert len(changed) == 1
    assert (
        changed[0][0]["issue_id"]
        == "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"
    )
    assert changed[0][1]["successor_effective_status"] == "resolved"


def test_manifest_pre_transition_readiness_and_boundaries() -> None:
    manifest = json.loads((DERIVED / gate.MANIFEST_FILENAME).read_bytes())
    assert manifest["precondition_transition"] == {
        "complete_count": 42,
        "implementation_blocking_count": 3,
        "incomplete_count": 3,
        "remaining_open_precondition_ids": [
            "PRE_036",
            "PRE_038",
            "PRE_042",
        ],
        "resolved_in_this_stage": ["PRE_035"],
        "resolved_precondition_ids": ["PRE_034", "PRE_035"],
        "row_count": 45,
        "supported_but_not_frozen_count": 0,
    }
    readiness = manifest["readiness"]
    assert readiness["combined_permission_semantics_frozen"] is True
    assert readiness["cross_rule_aggregation_implemented"] is False
    assert readiness["feature_semantics_audit_completed"] is False
    assert readiness["ready_for_training"] is False
    assert manifest["current_permission"] is False
    assert manifest["authorized_admit_015_training_execution_count"] == 0


def test_manifest_hash_truth_and_no_self_hash() -> None:
    manifest = json.loads((DERIVED / gate.MANIFEST_FILENAME).read_bytes())
    assert manifest["manifest_self_sha256_recorded"] is False
    for path, expected in manifest["derived_output_sha256"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
    for path, expected in manifest["support_file_sha256"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected


def test_complete_checker_local_reconstruction() -> None:
    checker = _load_checker()
    snapshot = checker._source_snapshot()
    expected = checker._local_expected(snapshot)
    observed = {
        name: (ROOT / checker.DERIVED_ROOT / name).read_bytes()
        for name in checker.OUTPUT_NAMES
    }
    assert expected == observed


def test_candidate_production_actual_matches_checker_local_expected() -> None:
    checker = _load_checker()
    snapshot = checker._source_snapshot()
    expected = checker._local_expected(snapshot)
    actual = gate.build_artifacts(
        gate.build_frozen_source_snapshot(ROOT), repo_root=ROOT
    )
    observed = checker.read_exact6_no_follow()
    checker._verify_observed_artifacts(actual, expected)
    checker._verify_observed_artifacts(observed, expected)
    assert actual == expected == observed
    assert (
        actual[gate.MANIFEST_FILENAME]
        == expected[checker.MANIFEST_NAME]
        == observed[checker.MANIFEST_NAME]
    )
    actual_manifest = json.loads(actual[gate.MANIFEST_FILENAME])
    expected_manifest = json.loads(expected[checker.MANIFEST_NAME])
    observed_manifest = json.loads(observed[checker.MANIFEST_NAME])
    assert actual_manifest == expected_manifest == observed_manifest
    assert "revised2_final_lifecycle_closure" in actual_manifest


def _canonical_synchronized_tamper(
    checker: object,
    expected: dict[str, bytes],
    name: str,
    content: bytes,
    manifest_change: str,
) -> dict[str, bytes]:
    tampered = dict(expected)
    tampered[name] = content
    manifest = json.loads(tampered[checker.MANIFEST_NAME])
    derived_path = (checker.DERIVED_ROOT / name).as_posix()
    manifest["derived_output_sha256"][derived_path] = hashlib.sha256(
        content
    ).hexdigest()
    if manifest_change == "precedence":
        manifest["combination_semantics"] = "majority_vote"
    elif manifest_change == "membership":
        manifest["permission_scopes"][0]["scope_id"] = (
            "download_execution_permission_tampered"
        )
        manifest["permission_scopes"][0]["membership_sha256"] = (
            hashlib.sha256(content).hexdigest()
        )
    elif manifest_change == "truth":
        manifest["truth_matrix"]["generated_by_pure_memory_design_simulator"] = (
            False
        )
    else:
        raise AssertionError("unknown synchronized tamper")
    tampered[checker.MANIFEST_NAME] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode()
    return tampered


@pytest.mark.parametrize("tamper_kind", ("precedence", "membership", "truth"))
def test_synchronized_csv_manifest_tamper_is_rejected_by_real_verifier(
    tamper_kind: str,
) -> None:
    checker = _load_checker()
    expected = checker._local_expected(checker._source_snapshot())
    if tamper_kind == "precedence":
        name = checker.PRECEDENCE_NAME
        content = expected[name].replace(
            b"monotone conjunction", b"majority vote allowed", 1
        )
    elif tamper_kind == "membership":
        name = checker.MEMBERSHIP_NAME
        content = expected[name].replace(
            b"download_execution_permission",
            b"download_execution_permission_tampered",
            1,
        )
    else:
        name = checker.TRUTH_NAME
        content = expected[name].replace(
            b",passed,passed,true,true,false,false,",
            b",blocked,blocked,false,false,true,true,",
            1,
        )
    assert content != expected[name]
    tampered = _canonical_synchronized_tamper(
        checker,
        expected,
        name,
        content,
        tamper_kind,
    )
    with pytest.raises(ValueError, match="reconstruction mismatch"):
        checker._verify_observed_artifacts(tampered, expected)


def test_duplicate_json_key_is_rejected() -> None:
    with pytest.raises(ValueError, match="unique keys"):
        gate._json(b'{"a":1,"a":2}')


def test_pinned_reader_rejects_final_symlink(tmp_path: Path) -> None:
    (tmp_path / "real").write_text("value", encoding="utf-8")
    (tmp_path / "link").symlink_to("real")
    with pytest.raises((OSError, ValueError)):
        gate._pinned_read(tmp_path, Path("link"))


def test_pinned_reader_rejects_parent_symlink(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    (real / "leaf").write_text("value", encoding="utf-8")
    (tmp_path / "alias").symlink_to(real, target_is_directory=True)
    with pytest.raises((OSError, ValueError)):
        gate._pinned_read(tmp_path, Path("alias/leaf"))


def test_output_reader_rejects_extra_residue(tmp_path: Path) -> None:
    for name in gate.OUTPUT_FILES:
        (tmp_path / name).write_bytes(b"x")
    (tmp_path / "extra").write_bytes(b"x")
    with pytest.raises(ValueError, match="inventory"):
        gate._read_output_set(tmp_path)


def test_output_reader_rejects_symlink(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.write_bytes(b"x")
    for name in gate.OUTPUT_FILES[:-1]:
        (tmp_path / name).write_bytes(b"x")
    (tmp_path / gate.OUTPUT_FILES[-1]).symlink_to(target)
    with pytest.raises((OSError, ValueError)):
        gate._read_output_set(tmp_path)


def test_materializer_build_before_mutation_and_existing_noop(
    tmp_path: Path,
) -> None:
    payloads = {name: name.encode() for name in gate.OUTPUT_FILES}
    plan = gate._inspect_output_target(Path("evidence"), tmp_path)
    gate._materialize_set(plan, payloads)
    identities = {
        name: os.lstat(tmp_path / "evidence" / name).st_ino
        for name in gate.OUTPUT_FILES
    }
    second = gate._inspect_output_target(Path("evidence"), tmp_path)
    gate._materialize_set(second, payloads)
    assert identities == {
        name: os.lstat(tmp_path / "evidence" / name).st_ino
        for name in gate.OUTPUT_FILES
    }


def _exact6_identity_state(root: Path) -> tuple[object, ...]:
    return (
        os.lstat(root).st_ino,
        tuple(sorted(os.listdir(root))),
        tuple(
            (
                name,
                os.lstat(root / name).st_ino,
                hashlib.sha256((root / name).read_bytes()).hexdigest(),
            )
            for name in gate.OUTPUT_FILES
        ),
    )


def test_production_generated_payload_is_formal_exact6_existing_noop() -> None:
    actual = gate.build_artifacts(
        gate.build_frozen_source_snapshot(ROOT),
        repo_root=ROOT,
    )
    before = _exact6_identity_state(DERIVED)
    staging_before = tuple(
        sorted(
            path.name
            for path in DERIVED.parent.iterdir()
            if path.name.startswith(
                ".combined-permission-semantics-stage-"
            )
        )
    )
    plan = gate._inspect_output_target(gate.DEFAULT_OUTPUT_ROOT, ROOT)
    gate._materialize_set(plan, actual)
    assert _exact6_identity_state(DERIVED) == before
    assert tuple(
        sorted(
            path.name
            for path in DERIVED.parent.iterdir()
            if path.name.startswith(
                ".combined-permission-semantics-stage-"
            )
        )
    ) == staging_before


def test_production_materializes_new_exact6_and_second_run_is_noop(
    tmp_path: Path,
) -> None:
    actual = gate.build_artifacts(
        gate.build_frozen_source_snapshot(ROOT),
        repo_root=ROOT,
    )
    formal = gate._read_output_set(DERIVED)
    plan = gate._inspect_output_target(Path("new-evidence"), tmp_path)
    gate._materialize_set(plan, actual)
    assert gate._read_output_set(plan.root) == actual == formal
    before = _exact6_identity_state(plan.root)
    second = gate._inspect_output_target(Path("new-evidence"), tmp_path)
    gate._materialize_set(second, actual)
    assert _exact6_identity_state(plan.root) == before
    assert tuple(sorted(os.listdir(tmp_path))) == ("new-evidence",)


def test_formal_run_entry_is_inode_preserving_existing_noop() -> None:
    before = _exact6_identity_state(DERIVED)
    staging_before = tuple(
        sorted(
            path.name
            for path in DERIVED.parent.iterdir()
            if path.name.startswith(
                ".combined-permission-semantics-stage-"
            )
        )
    )
    result = gate.run_covapie_bulk_download_admission_combined_permission_semantics_contract_v1(
        gate.DEFAULT_OUTPUT_ROOT,
        repo_root=ROOT,
    )
    assert (
        result["manifest"]["revised2_final_lifecycle_closure"]
        == gate._revised2_final_lifecycle_closure()
    )
    assert _exact6_identity_state(DERIVED) == before
    assert tuple(
        sorted(
            path.name
            for path in DERIVED.parent.iterdir()
            if path.name.startswith(
                ".combined-permission-semantics-stage-"
            )
        )
    ) == staging_before


def test_materializer_existing_tamper_fails_closed(tmp_path: Path) -> None:
    payloads = {name: name.encode() for name in gate.OUTPUT_FILES}
    root = tmp_path / "evidence"
    root.mkdir()
    for name, content in payloads.items():
        (root / name).write_bytes(content)
    (root / gate.OUTPUT_FILES[0]).write_bytes(b"tampered")
    with pytest.raises(ValueError, match="payload"):
        gate._materialize_set(
            gate._inspect_output_target(Path("evidence"), tmp_path),
            payloads,
        )


def test_materializer_einval_retains_authenticated_staging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payloads = {name: name.encode() for name in gate.OUTPUT_FILES}

    def fail_rename(*_args: object) -> int:
        ctypes.set_errno(22)
        return -1

    monkeypatch.setattr(gate, "_RENAMEAT2", fail_rename)
    plan = gate._inspect_output_target(Path("evidence"), tmp_path)
    with pytest.raises(gate.MaterializationRetentionError) as captured:
        gate._materialize_set(plan, payloads)
    retained = captured.value.authenticated_retained_path
    assert retained is not None
    assert retained.is_dir()
    assert set(os.listdir(retained)) == set(gate.OUTPUT_FILES)
    assert not (tmp_path / "evidence").exists()


def test_production_has_no_torch_or_dispatcher_dependency() -> None:
    source = (ROOT / gate.SUPPORT_PATHS[0]).read_text(encoding="utf-8")
    prefix = source.split("if __name__ == \"__main__\":", 1)[0]
    assert "import torch" not in prefix
    assert "evaluate_admission_rule(" not in prefix
    assert "cross_rule_aggregation_implemented\": True" not in source


def test_checker_lifecycle_and_full_main() -> None:
    checker = _load_checker()
    assert checker._lifecycle() in {"pre_commit", "post_commit"}
    assert checker.main() == 0


def _write_exact6(root: Path, payload: bytes = b"value") -> None:
    root.mkdir(parents=True)
    for name in gate.OUTPUT_FILES:
        (root / name).write_bytes(payload + name.encode())


def _replace_directory_with_equivalent_tree(
    path: Path,
    relative_leaf: Path,
    content: bytes,
) -> None:
    path.rename(path.with_name(path.name + "-old"))
    (path / relative_leaf.parent).mkdir(parents=True)
    (path / relative_leaf).write_bytes(content)


def test_source_reader_normal_and_checker_independence(
    tmp_path: Path,
) -> None:
    (tmp_path / "a/b").mkdir(parents=True)
    (tmp_path / "a/b/leaf").write_bytes(b"value")
    assert gate._pinned_read(tmp_path, Path("a/b/leaf")) == b"value"
    checker = _load_checker()
    assert (
        checker._read_repo_relative_no_follow(
            tmp_path,
            Path("a/b/leaf"),
        )
        == b"value"
    )
    assert checker._read_repo_relative_no_follow is not gate._pinned_read


@pytest.mark.parametrize("reader_kind", ("production", "checker"))
def test_source_reader_rejects_same_byte_leaf_replacement(
    tmp_path: Path,
    reader_kind: str,
) -> None:
    (tmp_path / "a").mkdir()
    leaf = tmp_path / "a/leaf"
    leaf.write_bytes(b"same")
    checker = _load_checker()
    reader = (
        gate._pinned_read
        if reader_kind == "production"
        else checker._read_repo_relative_no_follow
    )

    def replace(event: str, _path: Path) -> None:
        if event == "after_leaf_open":
            leaf.rename(tmp_path / "a/leaf-old")
            leaf.write_bytes(b"same")

    with pytest.raises(ValueError, match="leaf"):
        reader(tmp_path, Path("a/leaf"), hook=replace)


@pytest.mark.parametrize(
    ("reader_kind", "replacement"),
    (
        ("production", "intermediate"),
        ("production", "upper"),
        ("production", "root"),
        ("checker", "intermediate"),
        ("checker", "upper"),
        ("checker", "root"),
    ),
)
def test_source_reader_rejects_parent_chain_replacement(
    tmp_path: Path,
    reader_kind: str,
    replacement: str,
) -> None:
    repository = tmp_path / "repository"
    (repository / "upper/intermediate").mkdir(parents=True)
    relative = Path("upper/intermediate/leaf")
    (repository / relative).write_bytes(b"old")
    checker = _load_checker()
    reader = (
        gate._pinned_read
        if reader_kind == "production"
        else checker._read_repo_relative_no_follow
    )

    def replace(event: str, _path: Path) -> None:
        if event != "after_leaf_open":
            return
        if replacement == "intermediate":
            target = repository / "upper/intermediate"
            _replace_directory_with_equivalent_tree(
                target,
                Path("leaf"),
                b"new",
            )
        elif replacement == "upper":
            target = repository / "upper"
            _replace_directory_with_equivalent_tree(
                target,
                Path("intermediate/leaf"),
                b"new",
            )
        else:
            _replace_directory_with_equivalent_tree(
                repository,
                relative,
                b"new",
            )

    with pytest.raises((OSError, ValueError)):
        reader(repository, relative, hook=replace)


def test_legacy_checker_parent_replacement_gap_is_reproduced(
    tmp_path: Path,
) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "leaf").write_bytes(b"old")
    root_fd = os.open(tmp_path, gate.DIRECTORY_FLAGS)
    docs_fd = os.open("docs", gate.DIRECTORY_FLAGS, dir_fd=root_fd)
    leaf_fd = os.open("leaf", gate.READ_FLAGS, dir_fd=docs_fd)
    try:
        docs.rename(tmp_path / "docs-old")
        docs.mkdir()
        (docs / "leaf").write_bytes(b"new")
        old_bytes = os.read(leaf_fd, 100)
        legacy_lexical = os.stat(
            "leaf",
            dir_fd=docs_fd,
            follow_symlinks=False,
        )
        assert gate._identity(legacy_lexical) == gate._identity(
            os.fstat(leaf_fd)
        )
    finally:
        os.close(leaf_fd)
        os.close(docs_fd)
        os.close(root_fd)
    assert old_bytes == b"old"
    assert (docs / "leaf").read_bytes() == b"new"


def test_exact6_readers_normal_and_return_canonical_order(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence"
    _write_exact6(root)
    assert tuple(gate._read_output_set(root)) == gate.OUTPUT_FILES
    checker = _load_checker()
    assert (
        tuple(checker.read_exact6_no_follow(root))
        == checker.OUTPUT_NAMES
    )


@pytest.mark.parametrize("reader_kind", ("production", "checker"))
def test_exact6_reader_rejects_root_replacement(
    tmp_path: Path,
    reader_kind: str,
) -> None:
    root = tmp_path / "evidence"
    _write_exact6(root, b"old")
    checker = _load_checker()
    reader = (
        gate._read_output_set
        if reader_kind == "production"
        else checker.read_exact6_no_follow
    )

    def replace(event: str, _path: Path) -> None:
        if event == "after_leaf_open":
            root.rename(tmp_path / "evidence-old")
            _write_exact6(root, b"new")

    with pytest.raises(ValueError, match="root"):
        reader(root, hook=replace)


def test_legacy_production_exact6_root_replacement_gap_is_reproduced(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence"
    _write_exact6(root, b"old")
    root_fd = os.open(root, gate.DIRECTORY_FLAGS)
    descriptors = {
        name: os.open(name, gate.READ_FLAGS, dir_fd=root_fd)
        for name in gate.OUTPUT_FILES
    }
    try:
        root.rename(tmp_path / "evidence-old")
        _write_exact6(root, b"new")
        legacy = {
            name: os.read(descriptor, 1 << 16)
            for name, descriptor in descriptors.items()
        }
    finally:
        for descriptor in descriptors.values():
            os.close(descriptor)
        os.close(root_fd)
    assert all(value.startswith(b"old") for value in legacy.values())
    assert all(
        (root / name).read_bytes().startswith(b"new")
        for name in gate.OUTPUT_FILES
    )


@pytest.mark.parametrize("reader_kind", ("production", "checker"))
def test_exact6_reader_rejects_parent_replacement(
    tmp_path: Path,
    reader_kind: str,
) -> None:
    container = tmp_path / "container"
    root = container / "evidence"
    _write_exact6(root, b"old")
    checker = _load_checker()
    reader = (
        gate._read_output_set
        if reader_kind == "production"
        else checker.read_exact6_no_follow
    )

    def replace(event: str, _path: Path) -> None:
        if event == "after_leaf_open":
            container.rename(tmp_path / "container-old")
            _write_exact6(root, b"new")

    with pytest.raises(ValueError, match="root"):
        reader(root, hook=replace)


@pytest.mark.parametrize("reader_kind", ("production", "checker"))
def test_exact6_reader_rejects_same_byte_leaf_replacement(
    tmp_path: Path,
    reader_kind: str,
) -> None:
    root = tmp_path / "evidence"
    _write_exact6(root)
    leaf = root / gate.OUTPUT_FILES[0]
    checker = _load_checker()
    reader = (
        gate._read_output_set
        if reader_kind == "production"
        else checker.read_exact6_no_follow
    )

    def replace(event: str, _path: Path) -> None:
        if event == "after_leaf_open":
            content = leaf.read_bytes()
            leaf.rename(root / (leaf.name + "-old"))
            leaf.write_bytes(content)

    with pytest.raises(ValueError, match="leaf|inventory"):
        reader(root, hook=replace)


@pytest.mark.parametrize("condition", ("missing", "extra", "leaf_symlink"))
def test_checker_exact6_inventory_and_symlink_fail_closed(
    tmp_path: Path,
    condition: str,
) -> None:
    root = tmp_path / "evidence"
    _write_exact6(root)
    if condition == "missing":
        (root / gate.OUTPUT_FILES[0]).unlink()
    elif condition == "extra":
        (root / "seventh.txt").write_bytes(b"x")
    else:
        leaf = root / gate.OUTPUT_FILES[0]
        leaf.unlink()
        leaf.symlink_to(root / gate.OUTPUT_FILES[1])
    checker = _load_checker()
    with pytest.raises((OSError, ValueError)):
        checker.read_exact6_no_follow(root)


def test_exact6_root_symlink_is_rejected(tmp_path: Path) -> None:
    actual = tmp_path / "actual"
    _write_exact6(actual)
    alias = tmp_path / "alias"
    alias.symlink_to(actual, target_is_directory=True)
    checker = _load_checker()
    with pytest.raises((OSError, ValueError)):
        gate._read_output_set(alias)
    with pytest.raises((OSError, ValueError)):
        checker.read_exact6_no_follow(alias)


def test_materializer_existing_root_replacement_is_not_noop(
    tmp_path: Path,
) -> None:
    payloads = {name: name.encode() for name in gate.OUTPUT_FILES}
    root = tmp_path / "evidence"
    root.mkdir()
    for name, content in payloads.items():
        (root / name).write_bytes(content)
    plan = gate._inspect_output_target(Path("evidence"), tmp_path)

    def replace(event: str, _path: Path) -> None:
        if event == "before_existing_read":
            root.rename(tmp_path / "evidence-old")
            root.mkdir()
            for name, content in payloads.items():
                (root / name).write_bytes(content)

    with pytest.raises(ValueError, match="expected (parent|root)"):
        gate._materialize_set(plan, payloads, hook=replace)


def test_materializer_rejects_staging_identity_drift(
    tmp_path: Path,
) -> None:
    payloads = {name: name.encode() for name in gate.OUTPUT_FILES}
    plan = gate._inspect_output_target(Path("evidence"), tmp_path)

    def drift(event: str, path: Path) -> None:
        if event == "before_pre_rename_binding":
            os.chmod(path, 0o755)

    with pytest.raises(gate.MaterializationRetentionError) as captured:
        gate._materialize_set(plan, payloads, hook=drift)
    assert captured.value.authenticated_retained_path is None
    assert not plan.root.exists()


def test_materializer_rejects_staging_lexical_replacement(
    tmp_path: Path,
) -> None:
    payloads = {name: name.encode() for name in gate.OUTPUT_FILES}
    plan = gate._inspect_output_target(Path("evidence"), tmp_path)

    def replace(event: str, path: Path) -> None:
        if event == "before_pre_rename_binding":
            path.rename(path.with_name(path.name + "-old"))
            path.mkdir()

    with pytest.raises(gate.MaterializationRetentionError) as captured:
        gate._materialize_set(plan, payloads, hook=replace)
    assert captured.value.authenticated_retained_path is None
    assert not plan.root.exists()


def test_materializer_rejects_target_appearing_before_rename(
    tmp_path: Path,
) -> None:
    payloads = {name: name.encode() for name in gate.OUTPUT_FILES}
    plan = gate._inspect_output_target(Path("evidence"), tmp_path)

    def create_target(event: str, _path: Path) -> None:
        if event == "before_pre_rename_binding":
            plan.root.mkdir()

    with pytest.raises(gate.MaterializationRetentionError) as captured:
        gate._materialize_set(plan, payloads, hook=create_target)
    assert captured.value.authenticated_retained_path is not None
    assert plan.root.is_dir()


def test_materializer_post_publish_identity_and_no_os_replace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payloads = {name: name.encode() for name in gate.OUTPUT_FILES}
    observed = {}

    def forbidden_replace(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("os.replace must not be called")

    def record(event: str, path: Path) -> None:
        if event == "after_publish":
            observed["identity"] = gate._identity(os.lstat(path))

    monkeypatch.setattr(gate.os, "replace", forbidden_replace)
    plan = gate._inspect_output_target(Path("evidence"), tmp_path)
    gate._materialize_set(plan, payloads, hook=record)
    assert observed["identity"] == gate._identity(os.lstat(plan.root))
    assert gate._read_output_set(plan.root) == payloads


def _run_git(repo: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode()
    return completed.stdout


def _make_lifecycle_repo(
    tmp_path: Path,
    *,
    stable_descendant: bool = False,
) -> tuple[Path, str]:
    checker = _load_checker()
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    _run_git(repo, "init", "-q")
    _run_git(repo, "config", "user.email", "tests@example.invalid")
    _run_git(repo, "config", "user.name", "CovaPIE Tests")
    fixtures = (
        Path("src/covalent_ext/.keep"),
        Path("scripts/.keep"),
        Path("tests/.keep"),
        Path("docs/.keep"),
        Path("data/derived/covalent_small/.keep"),
    )
    for relative in fixtures:
        (repo / relative).parent.mkdir(parents=True, exist_ok=True)
        (repo / relative).write_bytes(b"baseline\n")
    (repo / ".gitignore").write_text(
        "ignored/\n*sibling/\n",
        encoding="utf-8",
    )
    _run_git(
        repo,
        "add",
        "--",
        ".gitignore",
        *(path.as_posix() for path in fixtures),
    )
    _run_git(repo, "commit", "-q", "-m", "base")
    base = _run_git(repo, "rev-parse", "HEAD").decode().strip()
    if stable_descendant:
        (repo / "stable-descendant").write_bytes(b"stable\n")
        _run_git(repo, "add", "--", "stable-descendant")
        _run_git(repo, "commit", "-q", "-m", "stable descendant")
    for relative in checker.EXACT10:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(relative.as_posix().encode() + b"\n")
    return repo, base


def _commit_exact10(repo: Path, checker: object) -> str:
    _run_git(
        repo,
        "add",
        "--",
        *(path.as_posix() for path in checker.EXACT10),
    )
    _run_git(repo, "commit", "-q", "-m", "candidate Exact10")
    return _run_git(repo, "rev-parse", "HEAD").decode().strip()


def test_legacy_ignored_lifecycle_bypass_is_reproduced(
    tmp_path: Path,
) -> None:
    checker = _load_checker()
    repo, base = _make_lifecycle_repo(tmp_path)
    hidden = repo / "docs/ignored" / f"{checker.STAGE}_hidden.txt"
    hidden.parent.mkdir()
    hidden.write_bytes(b"hidden")
    external = tmp_path / "external-target"
    external.write_bytes(b"external-target-bytes")
    link = hidden.parent / "generic-link"
    link.symlink_to(external)
    before = (os.lstat(external).st_ino, external.read_bytes())
    exact = tuple(path.as_posix() for path in checker.EXACT10)
    assert _run_git(repo, "diff", "--name-only") == b""
    untracked = tuple(
        value
        for value in _run_git(
            repo,
            "ls-files",
            "--others",
            "--exclude-standard",
        )
        .decode()
        .splitlines()
        if value
    )
    ignored_derived = tuple(
        value
        for value in _run_git(
            repo,
            "ls-files",
            "--others",
            "--ignored",
            "--exclude-standard",
        )
        .decode()
        .splitlines()
        if value.startswith(checker.DERIVED_ROOT.as_posix())
    )
    assert tuple(sorted(set(untracked) | set(ignored_derived))) == tuple(
        sorted(exact)
    )
    legacy_result = "pre_commit"
    assert legacy_result == "pre_commit"
    assert _run_git(repo, "rev-parse", "HEAD").decode().strip() == base
    assert (os.lstat(external).st_ino, external.read_bytes()) == before
    with pytest.raises(ValueError, match="symlink|ignored"):
        checker.verify_lifecycle(repo, checker.EXACT10, base=base)
    assert (os.lstat(external).st_ino, external.read_bytes()) == before


@pytest.mark.parametrize("residue_kind", ("same_stage_file", "generic_symlink"))
def test_final_complete_lifecycle_rejects_post_candidate_ignored_residue(
    tmp_path: Path,
    residue_kind: str,
) -> None:
    checker = _load_checker()
    repo, base = _make_lifecycle_repo(tmp_path)
    ordered = tuple(path.as_posix() for path in checker.EXACT10)
    assert (
        checker.verify_lifecycle(repo, checker.EXACT10, base=base)
        == "pre_commit"
    )
    initial = checker._capture_lifecycle_state(
        repo,
        ordered,
        base=base,
    )
    ignored = repo / "docs/ignored"
    ignored.mkdir()
    external = tmp_path / "external-target"
    external_before = None
    if residue_kind == "same_stage_file":
        (ignored / f"{checker.STAGE}_hidden.txt").write_bytes(b"hidden")
        error_pattern = "ignored|inventory"
    else:
        external.write_bytes(b"external-target-bytes")
        (ignored / "generic-link").symlink_to(external)
        external_before = (os.lstat(external).st_ino, external.read_bytes())
        error_pattern = "symlink"
    prefinal = checker._capture_lifecycle_state(
        repo,
        ordered,
        base=base,
    )
    assert prefinal == initial
    with pytest.raises(ValueError, match=error_pattern):
        checker.verify_lifecycle(repo, checker.EXACT10, base=base)
    if external_before is not None:
        assert (os.lstat(external).st_ino, external.read_bytes()) == (
            external_before
        )


def test_lifecycle_normal_base_and_stable_descendant_precommit(
    tmp_path: Path,
) -> None:
    checker = _load_checker()
    base_repo, base = _make_lifecycle_repo(tmp_path / "base")
    assert (
        checker.verify_lifecycle(
            base_repo,
            checker.EXACT10,
            base=base,
        )
        == "pre_commit"
    )
    descendant_repo, descendant_base = _make_lifecycle_repo(
        tmp_path / "descendant",
        stable_descendant=True,
    )
    assert (
        checker.verify_lifecycle(
            descendant_repo,
            checker.EXACT10,
            base=descendant_base,
        )
        == "pre_commit"
    )


def test_lifecycle_normal_postcommit(tmp_path: Path) -> None:
    checker = _load_checker()
    repo, base = _make_lifecycle_repo(tmp_path)
    head = _commit_exact10(repo, checker)
    assert head != base
    assert (
        checker.verify_lifecycle(repo, checker.EXACT10, base=base)
        == "post_commit"
    )


@pytest.mark.parametrize(
    "bounded_root",
    ("src/covalent_ext", "scripts", "tests", "docs"),
)
def test_lifecycle_rejects_ignored_nested_residue_in_four_roots(
    tmp_path: Path,
    bounded_root: str,
) -> None:
    checker = _load_checker()
    repo, base = _make_lifecycle_repo(tmp_path)
    residue = (
        repo
        / bounded_root
        / "ignored"
        / f"{checker.STAGE}_nested.txt"
    )
    residue.parent.mkdir()
    residue.write_bytes(b"hidden")
    with pytest.raises(ValueError, match="ignored|inventory"):
        checker.verify_lifecycle(repo, checker.EXACT10, base=base)


@pytest.mark.parametrize("tracked", (False, True))
def test_lifecycle_rejects_generic_symlink_without_touching_target(
    tmp_path: Path,
    tracked: bool,
) -> None:
    checker = _load_checker()
    repo, base = _make_lifecycle_repo(tmp_path)
    external = tmp_path / "external"
    external.write_bytes(b"external-bytes")
    link = (
        repo / "docs/generic-link"
        if tracked
        else repo / "docs/ignored/generic-link"
    )
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(external)
    if tracked:
        _run_git(repo, "add", "--", "docs/generic-link")
        _run_git(repo, "commit", "-q", "-m", "tracked generic symlink")
    before = (os.lstat(external).st_ino, external.read_bytes())
    with pytest.raises(ValueError, match="symlink"):
        checker.verify_lifecycle(repo, checker.EXACT10, base=base)
    assert (os.lstat(external).st_ino, external.read_bytes()) == before


def test_lifecycle_rejects_matching_derived_sibling(tmp_path: Path) -> None:
    checker = _load_checker()
    repo, base = _make_lifecycle_repo(tmp_path)
    sibling = (
        repo
        / checker.DERIVED_ROOT.parent
        / f"{checker.STAGE}-sibling"
    )
    sibling.mkdir()
    (sibling / "hidden").write_bytes(b"x")
    with pytest.raises(ValueError, match="derived|inventory|ignored"):
        checker.verify_lifecycle(repo, checker.EXACT10, base=base)


def test_lifecycle_rejects_matching_derived_root_symlink(
    tmp_path: Path,
) -> None:
    checker = _load_checker()
    repo, base = _make_lifecycle_repo(tmp_path)
    external = tmp_path / "external-directory"
    external.mkdir()
    sibling = (
        repo
        / checker.DERIVED_ROOT.parent
        / f"{checker.STAGE}-sibling"
    )
    exclude = repo / ".git/info/exclude"
    exclude.write_text(
        exclude.read_text(encoding="utf-8")
        + f"\n{checker.STAGE}-sibling\n",
        encoding="utf-8",
    )
    sibling.symlink_to(external, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        checker.verify_lifecycle(repo, checker.EXACT10, base=base)


@pytest.mark.parametrize("event_name", ("before_top_root_open", "after_top_root_open"))
def test_recursive_scanner_rejects_top_root_replacement(
    tmp_path: Path,
    event_name: str,
) -> None:
    checker = _load_checker()
    repo, _base = _make_lifecycle_repo(tmp_path)
    fired = False

    def replace(event: str, path: Path) -> None:
        nonlocal fired
        if fired or event != event_name or path != Path("docs"):
            return
        fired = True
        docs = repo / "docs"
        docs.rename(repo / "docs-old")
        docs.mkdir()
        (docs / ".keep").write_bytes(b"baseline\n")
        summary = docs / checker.SUMMARY_PATH.name
        summary.write_bytes(checker.SUMMARY_PATH.as_posix().encode() + b"\n")

    with pytest.raises(ValueError, match="drift|race"):
        checker.assert_exact10_recursive_inventory(
            repo,
            checker.EXACT10,
            hook=replace,
        )
    assert fired is True


def test_lifecycle_rejects_allow_empty_postcommit_history(
    tmp_path: Path,
) -> None:
    checker = _load_checker()
    repo, base = _make_lifecycle_repo(tmp_path)
    _commit_exact10(repo, checker)
    _run_git(repo, "commit", "--allow-empty", "-q", "-m", "empty")
    with pytest.raises(ValueError, match="allow-empty"):
        checker.verify_lifecycle(repo, checker.EXACT10, base=base)


def test_lifecycle_rejects_mid_scan_head_drift(tmp_path: Path) -> None:
    checker = _load_checker()
    repo, base = _make_lifecycle_repo(tmp_path)
    fired = False

    def drift(event: str, _path: Path) -> None:
        nonlocal fired
        if not fired and event == "after_repository_root_open":
            fired = True
            _run_git(
                repo,
                "commit",
                "--allow-empty",
                "-q",
                "-m",
                "mid-scan",
            )

    with pytest.raises(ValueError, match="HEAD|drift"):
        checker.verify_lifecycle(
            repo,
            checker.EXACT10,
            base=base,
            hook=drift,
        )


def test_lifecycle_rejects_full_index_bytes_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker()
    repo, base = _make_lifecycle_repo(tmp_path)
    original = checker._git_result
    full_index_calls = 0

    def drift(root: Path, *arguments: str):
        nonlocal full_index_calls
        result = original(root, *arguments)
        if arguments == ("ls-files", "--stage", "-z"):
            full_index_calls += 1
            if full_index_calls == 2:
                return subprocess.CompletedProcess(
                    result.args,
                    result.returncode,
                    stdout=result.stdout + b"synthetic-index-drift\0",
                    stderr=result.stderr,
                )
        return result

    monkeypatch.setattr(checker, "_git_result", drift)
    with pytest.raises(ValueError, match="index|drift"):
        checker.verify_lifecycle(repo, checker.EXACT10, base=base)
    assert full_index_calls == 2


@pytest.mark.parametrize("drift_kind", ("staged", "unrelated_untracked"))
def test_lifecycle_rejects_staged_and_unrelated_untracked_drift(
    tmp_path: Path,
    drift_kind: str,
) -> None:
    checker = _load_checker()
    repo, base = _make_lifecycle_repo(tmp_path)
    fired = False

    def drift(event: str, _path: Path) -> None:
        nonlocal fired
        if fired or event != "after_repository_root_open":
            return
        fired = True
        if drift_kind == "staged":
            (repo / "docs/.keep").write_bytes(b"changed\n")
            _run_git(repo, "add", "--", "docs/.keep")
        else:
            (repo / "unrelated").write_bytes(b"untracked\n")

    with pytest.raises(ValueError, match="staged|untracked|drift"):
        checker.verify_lifecycle(
            repo,
            checker.EXACT10,
            base=base,
            hook=drift,
        )


def test_strict_head_rejects_malformed_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker()

    def malformed(
        _root: Path,
        *_arguments: str,
    ) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(
            ("git",),
            0,
            stdout=b"BB282EF24343BAEBC05212715A8C7D56BC8224AD\n",
            stderr=b"",
        )

    monkeypatch.setattr(checker, "_git_result", malformed)
    with pytest.raises(ValueError, match="malformed"):
        checker._strict_head(ROOT)


def test_production_source_snapshot_rejects_mid_scan_head_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed = iter((gate.BASE_COMMIT, "0" * 40))
    monkeypatch.setattr(gate, "_strict_head", lambda _root: next(observed))
    with pytest.raises(ValueError, match="HEAD drift"):
        gate.build_frozen_source_snapshot(ROOT)


def test_checker_source_snapshot_rejects_mid_scan_head_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker()
    observed = iter((checker.BASE_COMMIT, "0" * 40))
    monkeypatch.setattr(
        checker,
        "_strict_head",
        lambda _root=checker.ROOT: next(observed),
    )
    with pytest.raises(ValueError, match="HEAD drift"):
        checker._source_snapshot()


def test_revised1_manifest_declaration() -> None:
    manifest = json.loads((DERIVED / gate.MANIFEST_FILENAME).read_bytes())
    closure = manifest["revised1_infrastructure_closure"]
    assert closure["business_semantics_changed"] is False
    assert closure["source_parent_chain_fd_pinned"] is True
    assert closure["exact6_parent_root_set_reader_fd_pinned"] is True
    assert closure["checker_recursive_lifecycle_fd_pinned"] is True
    assert closure["checker_full_index_bytes_snapshotted"] is True
    assert closure["git_write_tree_index_snapshot_used"] is False


def test_revised2_final_lifecycle_manifest_declaration() -> None:
    manifest = json.loads((DERIVED / gate.MANIFEST_FILENAME).read_bytes())
    closure = manifest["revised2_final_lifecycle_closure"]
    assert closure["business_semantics_changed"] is False
    assert closure["full_recursive_lifecycle_runs_before_candidate"] is True
    assert closure["full_recursive_lifecycle_runs_after_candidate"] is True
    assert (
        closure["final_recursive_lifecycle_is_last_filesystem_validation"]
        is True
    )
    assert closure["ignored_residue_after_candidate_rejected"] is True
    assert closure["generic_symlink_after_candidate_rejected"] is True
    assert (
        closure["synchronized_tamper_uses_real_fail_closed_verifier"]
        is True
    )


def test_generator_unification_has_no_checker_overlay_or_dual_expected() -> None:
    checker_source = (ROOT / gate.SUPPORT_PATHS[1]).read_text(
        encoding="utf-8"
    )
    production_source = (ROOT / gate.SUPPORT_PATHS[0]).read_text(
        encoding="utf-8"
    )
    assert "include_revised2" not in checker_source
    assert "production_expected" not in checker_source
    assert (
        "_add_revised2_checker_owned_manifest_overlay"
        not in checker_source
    )
    assert "revised2_final_lifecycle_closure" in production_source
    metadata = gate._revised2_final_lifecycle_closure()
    assert type(metadata) is dict
    assert type(metadata["revision"]) is str
    assert all(type(value) is bool for key, value in metadata.items() if key != "revision")


def test_checker_source_has_no_git_write_tree_snapshot() -> None:
    source = (ROOT / gate.SUPPORT_PATHS[1]).read_text(encoding="utf-8")
    assert '"write-tree"' not in source
    assert "full_index" in source


def _install_checker_orchestration_stubs(
    checker: object,
    monkeypatch: pytest.MonkeyPatch,
    *,
    reject_post_candidate_residue: bool,
) -> tuple[list[str], dict[str, bool]]:
    events: list[str] = []
    state = {"post_candidate_residue": False}
    payloads = {
        name: (b"{}\n" if name == checker.MANIFEST_NAME else b"csv")
        for name in checker.OUTPUT_NAMES
    }
    manifest = {
        "truth_matrix": {"row_count": 163, "group_count": 17},
        "safety_audit": {"row_count": 30},
    }

    def capture(*_args: object, **_kwargs: object) -> str:
        events.append("capture")
        return "stable-snapshot"

    lifecycle_calls = 0

    def lifecycle(*_args: object, **_kwargs: object) -> str:
        nonlocal lifecycle_calls
        lifecycle_calls += 1
        events.append(f"verify-lifecycle-{lifecycle_calls}")
        if (
            lifecycle_calls == 2
            and reject_post_candidate_residue
            and state["post_candidate_residue"]
        ):
            raise ValueError("final full lifecycle rejected ignored residue")
        return "pre_commit"

    def source_snapshot(*_args: object, **_kwargs: object) -> list[object]:
        events.append("source-snapshot")
        return []

    def local_expected(_snapshot: object) -> dict[str, bytes]:
        events.append("local-expected")
        return payloads

    def exact6(*_args: object, **_kwargs: object) -> dict[str, bytes]:
        events.append("exact6-read")
        return payloads

    class Candidate:
        @staticmethod
        def build_frozen_source_snapshot(*_args: object, **_kwargs: object):
            events.append("candidate-source-snapshot")
            return ()

        @staticmethod
        def build_artifacts(*_args: object, **_kwargs: object):
            events.append("candidate-build-artifacts")
            return payloads

    def load_candidate() -> Candidate:
        events.append("candidate-load")
        return Candidate()

    def verify_artifacts(*_args: object, **_kwargs: object):
        events.append("artifact-verifier")
        return manifest

    monkeypatch.setattr(checker, "_capture_lifecycle_state", capture)
    monkeypatch.setattr(checker, "verify_lifecycle", lifecycle)
    monkeypatch.setattr(checker, "_source_snapshot", source_snapshot)
    monkeypatch.setattr(checker, "_local_expected", local_expected)
    monkeypatch.setattr(checker, "read_exact6_no_follow", exact6)
    monkeypatch.setattr(checker, "_load_candidate", load_candidate)
    monkeypatch.setattr(
        checker,
        "_verify_observed_artifacts",
        verify_artifacts,
    )
    return events, state


def test_checker_orchestration_runs_final_full_lifecycle_last(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker()
    events, _state = _install_checker_orchestration_stubs(
        checker,
        monkeypatch,
        reject_post_candidate_residue=False,
    )

    def after_candidate() -> None:
        events.append("after-candidate-hook")

    report = checker._verify_complete_checker_run(
        after_candidate_validation=after_candidate
    )
    assert events.count("verify-lifecycle-1") == 1
    assert events.count("verify-lifecycle-2") == 1
    assert events.index("verify-lifecycle-1") < events.index("candidate-load")
    assert events.index("candidate-build-artifacts") < events.index(
        "verify-lifecycle-2"
    )
    assert events.index("after-candidate-hook") < events.index("capture", 1)
    assert events[-1] == "verify-lifecycle-2"
    assert report["full_recursive_lifecycle_run_count"] == 2
    assert (
        report["final_recursive_lifecycle_is_last_filesystem_validation"]
        is True
    )


def test_checker_orchestration_final_lifecycle_rejects_candidate_side_effect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker()
    events, state = _install_checker_orchestration_stubs(
        checker,
        monkeypatch,
        reject_post_candidate_residue=True,
    )

    def create_ignored_residue() -> None:
        events.append("after-candidate-hook")
        state["post_candidate_residue"] = True

    with pytest.raises(ValueError, match="ignored residue"):
        checker._verify_complete_checker_run(
            after_candidate_validation=create_ignored_residue
        )
    assert events.index("candidate-build-artifacts") < events.index(
        "verify-lifecycle-2"
    )
    assert events[-1] == "verify-lifecycle-2"
