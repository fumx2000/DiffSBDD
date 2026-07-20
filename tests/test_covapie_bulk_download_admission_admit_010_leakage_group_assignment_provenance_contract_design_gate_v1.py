from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from dataclasses import FrozenInstanceError, dataclass, fields, replace
from pathlib import Path

import pytest

from covalent_ext import covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate as gate


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/check_covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1.py"
OUTPUT_ROOT = REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT
_DEFAULT_CONTEXT = object()


def valid_contract(**changes: object) -> gate.LeakageGroupAssignmentProvenanceContractV1:
    value = gate.LeakageGroupAssignmentProvenanceContractV1(
        gate.PROVENANCE_CONTRACT_VERSION,
        gate.CANDIDATE_FIELD,
        gate.HISTORICAL_ARTIFACT_FIELD,
        gate.FIELD_MAPPING_RULE,
        gate.ASSIGNMENT_POLICY,
        gate.ASSIGNMENT_POLICY_VERSION,
        gate.ASSIGNMENT_STAGE_KIND,
        "1" * 64,
        "2" * 64,
        "3" * 64,
        "4" * 64,
        "OPAQUE_ASSIGNMENT_RECORD",
        "COVAPIE_LEAKAGE_GROUP_000001",
        "SAMPLE_ALPHA",
        ("SAMPLE_ALPHA",),
        1,
        True,
        False,
        gate.PRE_SPLIT_ASSIGNED_STATUS,
    )
    return replace(value, **changes)


def classify(candidate: object, context: object = _DEFAULT_CONTEXT) -> dict[str, object]:
    return dict(gate.classify_admit_010_leakage_group_assignment_provenance_design(
        candidate, valid_contract() if context is _DEFAULT_CONTEXT else context,
    ))


def test_identity_and_exact19_contract_are_frozen() -> None:
    assert gate.ADMISSION_RULE_ID == "ADMIT_010"
    assert gate.ADMISSION_RULE_NAME == "leakage_group_assignment_before_split"
    assert gate.EVALUATION_PHASE == "pre_final_split"
    assert gate.CANDIDATE_FIELD == "leakage_group_id"
    assert gate.CONTEXT_ITEM == "leakage_group_assignment_provenance_contract"
    assert gate.HISTORICAL_ARTIFACT_FIELD == "final_leakage_group_id"
    assert tuple(field.name for field in fields(gate.LeakageGroupAssignmentProvenanceContractV1)) == gate.EXACT19_FIELD_NAMES
    assert len(gate.EXACT19_FIELD_NAMES) == 19
    assert not hasattr(gate.LeakageGroupAssignmentProvenanceContractV1, "__slots__")
    value = valid_contract()
    with pytest.raises(FrozenInstanceError):
        value.assignment_id = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("value", "outcome", "reason"),
    [
        (None, "invalid", "LEAKAGE_GROUP_ID_TYPE_INVALID"),
        (7, "invalid", "LEAKAGE_GROUP_ID_TYPE_INVALID"),
        ("", "blocked", "leakage_group_unassigned"),
        ("COVAPIE_LEAKAGE_GROUP_00000é", "invalid", "LEAKAGE_GROUP_ID_NON_ASCII"),
        ("covapie_leakage_group_000001", "invalid", "LEAKAGE_GROUP_ID_SYNTAX_INVALID"),
        ("COVAPIE_leakage_GROUP_000001", "invalid", "LEAKAGE_GROUP_ID_SYNTAX_INVALID"),
        ("COVAPIE_LEAKAGE_GROUP_00001", "invalid", "LEAKAGE_GROUP_ID_SYNTAX_INVALID"),
        ("COVAPIE_LEAKAGE_GROUP_0000001", "invalid", "LEAKAGE_GROUP_ID_SYNTAX_INVALID"),
        ("COVAPIE_LEAKAGE_GROUP_00000A", "invalid", "LEAKAGE_GROUP_ID_SYNTAX_INVALID"),
        (" COVAPIE_LEAKAGE_GROUP_000001", "invalid", "LEAKAGE_GROUP_ID_SYNTAX_INVALID"),
        ("COVAPIE_LEAKAGE_GROUP_000001 ", "invalid", "LEAKAGE_GROUP_ID_SYNTAX_INVALID"),
        ("COVAPIE_LEAKAGE_GROUP_00000١", "invalid", "LEAKAGE_GROUP_ID_NON_ASCII"),
        ("COVAPIE_LEAKAGE_GROUP_000001", "passed", ""),
    ],
)
def test_candidate_scalar_grammar_and_precedence(
    value: object, outcome: str, reason: str,
) -> None:
    result = classify(value)
    assert result["outcome"] == outcome
    assert result["reason"] == reason
    assert result["blocks_candidate"] is (outcome != "passed")
    assert result["passed"] is (outcome == "passed")
    if outcome != "passed" and value != "COVAPIE_LEAKAGE_GROUP_000001":
        assert result["canonical_leakage_group_id"] == ""
        assert result["validated_candidate_fields"] == ()
        assert result["consumed_context_items"] == ()


def test_candidate_str_subclass_is_rejected_without_normalization() -> None:
    class StringSubclass(str):
        pass

    candidate = StringSubclass("COVAPIE_LEAKAGE_GROUP_000001")
    result = classify(candidate)
    assert result["reason"] == "LEAKAGE_GROUP_ID_TYPE_INVALID"
    assert result["canonical_leakage_group_id"] == ""


def test_context_requires_exact_committed_design_type() -> None:
    @dataclass(frozen=True)
    class ContractSubclass(gate.LeakageGroupAssignmentProvenanceContractV1):
        pass

    value = valid_contract()
    subclass = ContractSubclass(*(getattr(value, name) for name in gate.EXACT19_FIELD_NAMES))
    for context in (None, {}, subclass):
        result = classify("COVAPIE_LEAKAGE_GROUP_000001", context)
        assert result["outcome"] == "invalid"
        assert result["reason"] == "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_CONTRACT_TYPE_INVALID"
        assert result["canonical_leakage_group_id"] == "COVAPIE_LEAKAGE_GROUP_000001"
        assert result["consumed_context_items"] == (gate.CONTEXT_ITEM,)


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"contract_version": "wrong"}, "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_CONTRACT_VERSION_INVALID"),
        ({"canonical_candidate_field_name": "final_leakage_group_id"}, "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_FIELD_MAPPING_INVALID"),
        ({"historical_artifact_field_name": "leakage_group_id"}, "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_FIELD_MAPPING_INVALID"),
        ({"field_mapping_rule": "renumber"}, "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_FIELD_MAPPING_INVALID"),
        ({"assignment_policy": "other_v1"}, "LEAKAGE_GROUP_ASSIGNMENT_POLICY_INVALID"),
        ({"assignment_policy_version": "v2"}, "LEAKAGE_GROUP_ASSIGNMENT_POLICY_VERSION_INVALID"),
        ({"assignment_stage_kind": "post_split"}, "LEAKAGE_GROUP_ASSIGNMENT_STAGE_KIND_INVALID"),
    ],
)
def test_static_contract_drift_fails_at_frozen_reason(
    changes: dict[str, object], reason: str,
) -> None:
    result = classify("COVAPIE_LEAKAGE_GROUP_000001", valid_contract(**changes))
    assert result["outcome"] == "invalid"
    assert result["reason"] == reason


@pytest.mark.parametrize("hostile_kind", ["plain_object", "str_subclass"])
def test_contract_version_exact_type_gate_precedes_hostile_comparison(
    hostile_kind: str,
) -> None:
    comparisons = {"eq": 0, "ne": 0}

    class ExplosiveComparison:
        def __eq__(self, other: object) -> bool:
            comparisons["eq"] += 1
            raise AssertionError("comparison must not run")

        def __ne__(self, other: object) -> bool:
            comparisons["ne"] += 1
            raise AssertionError("comparison must not run")

    class ExplosiveString(str):
        def __eq__(self, other: object) -> bool:
            comparisons["eq"] += 1
            raise AssertionError("comparison must not run")

        def __ne__(self, other: object) -> bool:
            comparisons["ne"] += 1
            raise AssertionError("comparison must not run")

    hostile: object = (
        ExplosiveComparison()
        if hostile_kind == "plain_object"
        else ExplosiveString(gate.PROVENANCE_CONTRACT_VERSION)
    )
    result = classify(
        "COVAPIE_LEAKAGE_GROUP_000001",
        valid_contract(contract_version=hostile),
    )
    assert comparisons == {"eq": 0, "ne": 0}
    assert result == {
        "outcome": "invalid", "passed": False, "blocks_candidate": True,
        "reason": "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_CONTRACT_VERSION_INVALID",
        "canonical_leakage_group_id": "COVAPIE_LEAKAGE_GROUP_000001",
        "validated_candidate_fields": (("leakage_group_id", "COVAPIE_LEAKAGE_GROUP_000001"),),
        "consumed_candidate_fields": ("leakage_group_id",),
        "consumed_context_items": ("leakage_group_assignment_provenance_contract",),
        "evaluator_io_used": False,
    }


@pytest.mark.parametrize("field_name", [
    "assignment_manifest_sha256", "assignment_artifact_sha256",
    "group_inventory_sha256", "sample_index_sha256",
])
@pytest.mark.parametrize("bad_value", [None, "A" * 64, "1" * 63, "g" * 64, ""])
def test_each_source_sha_field_rejects_invalid_syntax(
    field_name: str, bad_value: object,
) -> None:
    result = classify("COVAPIE_LEAKAGE_GROUP_000001", valid_contract(**{field_name: bad_value}))
    assert result["reason"] == "LEAKAGE_GROUP_ASSIGNMENT_SOURCE_SHA256_INVALID"


def test_sha_str_subclass_is_rejected() -> None:
    class StringSubclass(str):
        pass

    result = classify(
        "COVAPIE_LEAKAGE_GROUP_000001",
        valid_contract(assignment_manifest_sha256=StringSubclass("1" * 64)),
    )
    assert result["reason"] == "LEAKAGE_GROUP_ASSIGNMENT_SOURCE_SHA256_INVALID"


def test_source_sha_is_caller_attestation_not_authenticity_proof() -> None:
    fabricated = valid_contract(
        assignment_manifest_sha256="a" * 64,
        assignment_artifact_sha256="b" * 64,
        group_inventory_sha256="c" * 64,
        sample_index_sha256="d" * 64,
    )
    assert classify("COVAPIE_LEAKAGE_GROUP_000001", fabricated)["outcome"] == "passed"


@pytest.mark.parametrize("value", [None, 7, "", "ASSIGNMENT_é", " ASSIGNMENT", "ASSIGNMENT ", "X" * 257])
def test_assignment_id_is_exact_opaque_identifier(value: object) -> None:
    result = classify("COVAPIE_LEAKAGE_GROUP_000001", valid_contract(assignment_id=value))
    assert result["reason"] == "LEAKAGE_GROUP_ASSIGNMENT_ID_INVALID"


def test_assignment_id_cannot_be_promoted_to_group_id() -> None:
    result = classify("OPAQUE_ASSIGNMENT_RECORD", valid_contract())
    assert result["reason"] == "LEAKAGE_GROUP_ID_SYNTAX_INVALID"


@pytest.mark.parametrize("value", [None, 7, "", "SAMPLE_é", " SAMPLE", "SAMPLE ", "X" * 257])
def test_sample_id_is_exact_opaque_identifier(value: object) -> None:
    result = classify("COVAPIE_LEAKAGE_GROUP_000001", valid_contract(sample_index_row_id=value))
    assert result["reason"] == "LEAKAGE_GROUP_ASSIGNMENT_SAMPLE_ID_INVALID"


@pytest.mark.parametrize("value", [None, 7, "ASSIGNMENT_RECORD", "COVAPIE_LEAKAGE_GROUP_00001"])
def test_historical_group_uses_same_canonical_grammar(value: object) -> None:
    result = classify("COVAPIE_LEAKAGE_GROUP_000001", valid_contract(historical_leakage_group_id=value))
    assert result["reason"] == "LEAKAGE_GROUP_ASSIGNMENT_HISTORICAL_GROUP_ID_INVALID"


@pytest.mark.parametrize(
    "members",
    [
        ["SAMPLE_ALPHA"],
        (),
        (7,),
        ("",),
        ("SAMPLE_é",),
        ("SAMPLE_BETA", "SAMPLE_ALPHA"),
        ("SAMPLE_ALPHA", "SAMPLE_ALPHA"),
    ],
)
def test_membership_container_members_order_and_uniqueness_fail_closed(members: object) -> None:
    count = len(members) if hasattr(members, "__len__") else 1
    result = classify(
        "COVAPIE_LEAKAGE_GROUP_000001",
        valid_contract(member_sample_index_row_ids=members, member_count=count),
    )
    assert result["outcome"] == "invalid"
    assert result["reason"] == "LEAKAGE_GROUP_ASSIGNMENT_MEMBERSHIP_INVALID"


def test_tuple_and_member_subclasses_are_rejected() -> None:
    class TupleSubclass(tuple):
        pass

    class StringSubclass(str):
        pass

    for members in (TupleSubclass(("SAMPLE_ALPHA",)), (StringSubclass("SAMPLE_ALPHA"),)):
        result = classify(
            "COVAPIE_LEAKAGE_GROUP_000001",
            valid_contract(member_sample_index_row_ids=members),
        )
        assert result["reason"] == "LEAKAGE_GROUP_ASSIGNMENT_MEMBERSHIP_INVALID"


@pytest.mark.parametrize("count", [True, False, 1.0, 0, -1, 2])
def test_member_count_requires_exact_positive_int_and_length_equality(count: object) -> None:
    result = classify("COVAPIE_LEAKAGE_GROUP_000001", valid_contract(member_count=count))
    assert result["outcome"] == "invalid"
    assert result["reason"] == "LEAKAGE_GROUP_ASSIGNMENT_MEMBER_COUNT_INVALID"


@pytest.mark.parametrize(
    "changes",
    [
        {"assignment_passed": False},
        {"assignment_passed": 1},
        {"split_assignments_written": True},
        {"split_assignments_written": 0},
        {"pre_split_assignment_status": "leakage_group_assigned"},
        {"historical_leakage_group_id": "COVAPIE_LEAKAGE_GROUP_000002"},
        {"sample_index_row_id": "SAMPLE_BETA"},
    ],
)
def test_incomplete_or_inconsistent_assignment_evidence_is_blocked(
    changes: dict[str, object],
) -> None:
    result = classify("COVAPIE_LEAKAGE_GROUP_000001", valid_contract(**changes))
    assert result == {
        "outcome": "blocked", "passed": False, "blocks_candidate": True,
        "reason": "leakage_group_unassigned",
        "canonical_leakage_group_id": "COVAPIE_LEAKAGE_GROUP_000001",
        "validated_candidate_fields": (("leakage_group_id", "COVAPIE_LEAKAGE_GROUP_000001"),),
        "consumed_candidate_fields": ("leakage_group_id",),
        "consumed_context_items": ("leakage_group_assignment_provenance_contract",),
        "evaluator_io_used": False,
    }


def test_valid_singleton_and_multi_member_assignments_pass() -> None:
    singleton = valid_contract()
    multi = valid_contract(
        sample_index_row_id="SAMPLE_BETA",
        member_sample_index_row_ids=("SAMPLE_ALPHA", "SAMPLE_BETA"),
        member_count=2,
    )
    for context in (singleton, multi):
        result = classify("COVAPIE_LEAKAGE_GROUP_000001", context)
        assert result["outcome"] == "passed"
        assert result["passed"] is True
        assert result["blocks_candidate"] is False
        assert result["reason"] == ""


def test_oracle_is_pure_in_memory(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("I/O attempted")

    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    result = classify("COVAPIE_LEAKAGE_GROUP_000001", valid_contract())
    assert result["outcome"] == "passed"
    assert result["evaluator_io_used"] is False


def test_build_state_row_counts_source_boundary_and_issue_transition() -> None:
    state = gate.build_design_state()
    assert len(state["contract_rows"]) == 32
    assert len(state["mapping_rows"]) == 26
    assert len(state["truth_rows"]) == 71
    assert len(state["source_boundary_rows"]) == 21
    assert len(state["issue_rows"]) == 11
    assert tuple(row["source_relative_path"] for row in state["source_boundary_rows"]) == tuple(
        path.as_posix() for path in gate.SOURCE_PATHS
    )
    blocker = next(row for row in state["issue_rows"] if row["issue_id"] == gate.PRIMARY_BLOCKER)
    coverage = next(row for row in state["issue_rows"] if row["issue_id"] == gate.COVERAGE_ISSUE)
    assert blocker["status"] == "resolved"
    assert blocker["integration_transition"] == "leakage_group_assignment_provenance_contract_frozen_v1"
    assert coverage["affected_rules"].startswith("ADMIT_010|")


def test_materialization_is_byte_deterministic_and_safe(tmp_path: Path) -> None:
    root = tmp_path / "outputs"
    first = gate.run_covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1(root)
    first_bytes = {name: (root / name).read_bytes() for name in gate.OUTPUT_FILES}
    second = gate.run_covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1(root)
    second_bytes = {name: (root / name).read_bytes() for name in gate.OUTPUT_FILES}
    assert first_bytes == second_bytes
    assert first["output_sha256"] == second["output_sha256"]
    assert {entry.name for entry in root.iterdir()} == set(gate.OUTPUT_FILES)
    assert all(stat.S_ISREG(os.lstat(entry).st_mode) and not entry.is_symlink() for entry in root.iterdir())
    assert not list(root.glob("*.tmp"))


@pytest.mark.parametrize("kind", ["extra", "directory", "symlink", "fifo"])
def test_unsafe_existing_inventory_fails_before_partial_write(tmp_path: Path, kind: str) -> None:
    root = tmp_path / "outputs"
    root.mkdir()
    if kind == "extra":
        unsafe = root / "unexpected.txt"
        unsafe.write_text("sentinel", encoding="utf-8")
    elif kind == "directory":
        unsafe = root / gate.CONTRACT_FILENAME
        unsafe.mkdir()
    elif kind == "symlink":
        target = tmp_path / "target"
        target.write_text("sentinel", encoding="utf-8")
        unsafe = root / gate.CONTRACT_FILENAME
        unsafe.symlink_to(target)
    else:
        if not hasattr(os, "mkfifo"):
            pytest.skip("FIFO unsupported")
        unsafe = root / gate.CONTRACT_FILENAME
        os.mkfifo(unsafe)
    before = {entry.name for entry in root.iterdir()}
    with pytest.raises(ValueError):
        gate.run_covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1(root)
    assert {entry.name for entry in root.iterdir()} == before
    assert not any(name in before for name in gate.OUTPUT_FILES if name != unsafe.name)


def test_symlink_output_root_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError):
        gate.run_covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1(link)
    assert not list(target.iterdir())


def test_committed_outputs_are_exact_six_regular_non_symlinks() -> None:
    assert {entry.name for entry in OUTPUT_ROOT.iterdir()} == set(gate.OUTPUT_FILES)
    for entry in OUTPUT_ROOT.iterdir():
        metadata = os.lstat(entry)
        assert stat.S_ISREG(metadata.st_mode)
        assert not stat.S_ISLNK(metadata.st_mode)


def test_checker_accepts_frozen_outputs() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)], cwd=REPO_ROOT,
        text=True, capture_output=True, check=False,
        env={**os.environ, "PYTHONPATH": f"{REPO_ROOT / 'src'}{os.pathsep}{os.environ.get('PYTHONPATH', '')}"},
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    payload = json.loads(completed.stdout)
    assert payload["truth_row_count"] == 71
    assert payload["source_input_count"] == 21


def _load_checker_module() -> object:
    import importlib.util

    spec = importlib.util.spec_from_file_location("admit010_provenance_checker_for_test", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_checker_rejects_semantic_tamper_with_synchronized_manifest_hash(tmp_path: Path) -> None:
    checker = _load_checker_module()
    root = tmp_path / "outputs"
    shutil.copytree(OUTPUT_ROOT, root)
    mapping = root / gate.MAPPING_FILENAME
    rows = list(csv.DictReader(mapping.read_text(encoding="utf-8").splitlines()))
    rows[9]["exact_requirement"] = "renumber_groups"
    with mapping.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=gate.MAPPING_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    manifest_path = root / gate.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["output_sha256"][gate.MAPPING_FILENAME] = hashlib.sha256(mapping.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="mapping semantic mismatch"):
        checker.check_covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1(
            output_root=root, enforce_frozen_hashes=False, exercise_materializer=False,
        )


def _tamper_manifest(manifest: dict[str, object], mutation: str) -> None:
    if mutation == "step":
        manifest["step"] = "changed"
    elif mutation == "precedence_swap":
        precedence = manifest["validation_precedence"]
        assert isinstance(precedence, list)
        precedence[0], precedence[1] = precedence[1], precedence[0]
    elif mutation == "sha_field_count":
        manifest["source_sha256_contract"]["field_count"] = 3  # type: ignore[index]
    elif mutation == "sha_exact_type":
        manifest["source_sha256_contract"]["exact_type"] = "str"  # type: ignore[index]
    elif mutation == "opaque_maximum_length":
        manifest["opaque_identifier_contract"]["maximum_length"] = 255  # type: ignore[index]
    elif mutation == "opaque_whitespace":
        manifest["opaque_identifier_contract"]["surrounding_whitespace_allowed"] = True  # type: ignore[index]
    elif mutation == "membership_unique":
        manifest["membership_contract"]["unique"] = False  # type: ignore[index]
    elif mutation == "membership_order":
        manifest["membership_contract"]["strict_ASCII_ascending"] = False  # type: ignore[index]
    elif mutation == "assignment_passed":
        manifest["pre_split_evidence_contract"]["assignment_passed"] = False  # type: ignore[index]
    elif mutation == "split_written":
        manifest["pre_split_evidence_contract"]["split_assignments_written"] = True  # type: ignore[index]
    elif mutation == "historical_group_count":
        manifest["historical_evidence_boundary"]["historical_group_count"] = 6  # type: ignore[index]
    elif mutation == "split_id_in_exact19":
        manifest["historical_evidence_boundary"]["split_assignment_ids_in_exact19"] = True  # type: ignore[index]
    elif mutation == "materializer_preflight":
        manifest["output_materialization"]["preflight_before_first_write"] = False  # type: ignore[index]
    elif mutation == "materializer_replace":
        manifest["output_materialization"]["os_replace"] = False  # type: ignore[index]
    elif mutation == "stop_boundaries":
        manifest["stop_boundaries"] = list(reversed(manifest["stop_boundaries"]))  # type: ignore[arg-type]
    elif mutation == "nested_unknown":
        manifest["membership_contract"]["unexpected"] = True  # type: ignore[index]
    elif mutation == "top_level_unknown":
        manifest["unexpected_key"] = True
    elif mutation == "readiness_mirror":
        manifest["leakage_group_id_provider_mapping_validated"] = True
    else:
        raise AssertionError(f"unknown mutation: {mutation}")


@pytest.mark.parametrize(
    "mutation",
    [
        "step", "precedence_swap", "sha_field_count", "sha_exact_type",
        "opaque_maximum_length", "opaque_whitespace", "membership_unique",
        "membership_order", "assignment_passed", "split_written",
        "historical_group_count", "split_id_in_exact19", "materializer_preflight",
        "materializer_replace", "stop_boundaries", "nested_unknown",
        "top_level_unknown", "readiness_mirror",
    ],
)
def test_checker_rejects_complete_manifest_semantic_tamper(
    tmp_path: Path, mutation: str,
) -> None:
    checker = _load_checker_module()
    root = tmp_path / mutation
    shutil.copytree(OUTPUT_ROOT, root)
    manifest_path = root / gate.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    _tamper_manifest(manifest, mutation)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(
        ValueError, match="manifest does not equal independent Exact104 expected value",
    ):
        checker.check_covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1(
            output_root=root, enforce_frozen_hashes=False, exercise_materializer=False,
        )


def test_checker_independently_freezes_complete_exact104_manifest() -> None:
    checker = _load_checker_module()
    expected = checker._expected_manifest()
    observed = json.loads((OUTPUT_ROOT / gate.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert type(expected) is dict
    assert len(expected) == 104
    assert observed == expected


def test_checker_rejects_missing_and_symlink_outputs(tmp_path: Path) -> None:
    checker = _load_checker_module()
    missing = tmp_path / "missing"
    shutil.copytree(OUTPUT_ROOT, missing)
    (missing / gate.TRUTH_FILENAME).unlink()
    with pytest.raises(ValueError, match="inventory"):
        checker.check_covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1(
            output_root=missing, enforce_frozen_hashes=False, exercise_materializer=False,
        )
    linked = tmp_path / "linked"
    shutil.copytree(OUTPUT_ROOT, linked)
    path = linked / gate.TRUTH_FILENAME
    target = tmp_path / "truth_target"
    path.rename(target)
    path.symlink_to(target)
    with pytest.raises(ValueError, match="unsafe"):
        checker.check_covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1(
            output_root=linked, enforce_frozen_hashes=False, exercise_materializer=False,
        )


def test_safe_source_boundary_rejects_raw_checkpoint_parent_traversal_and_absolute() -> None:
    assert not gate._safe_relative_path(Path("data/raw/example.csv"))
    assert not gate._safe_relative_path(Path("checkpoints/model.ckpt"))
    assert not gate._safe_relative_path(Path("../escape.csv"))
    assert not gate._safe_relative_path(Path("/tmp/absolute.csv"))


def test_resolved_containment_accepts_normal_nested_regular_file(tmp_path: Path) -> None:
    checker = _load_checker_module()
    repo = tmp_path / "repo"
    nested = repo / "nested"
    nested.mkdir(parents=True)
    (nested / "source.csv").write_text("inside", encoding="utf-8")
    relative = Path("nested/source.csv")
    assert gate._resolved_safe_descendant(relative, repo)
    assert checker._resolved_safe_descendant(relative, repo)


def test_parent_directory_symlink_escape_fails_before_source_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker_module()
    repo = tmp_path / "repo"
    outside = tmp_path / "outside"
    repo.mkdir()
    outside.mkdir()
    external_source = outside / "source.csv"
    external_source.write_text("external sentinel", encoding="utf-8")
    before = external_source.stat()
    (repo / "linked_parent").symlink_to(outside, target_is_directory=True)
    relative = Path("linked_parent/source.csv")
    linked_leaf = repo / relative
    assert linked_leaf.is_file()
    assert not linked_leaf.is_symlink()

    def fake_git(
        arguments: list[str], repo_root: Path, *, text: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        del repo_root, text
        if arguments[0] == "ls-files":
            stdout = relative.as_posix() + "\n"
        elif arguments[0] == "ls-tree":
            stdout = f"100644 blob {'0' * 40}\t{relative.as_posix()}\n"
        else:
            raise AssertionError(f"unexpected git call: {arguments}")
        return subprocess.CompletedProcess(arguments, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(gate, "_git", fake_git)
    assert not gate._resolved_safe_descendant(relative, repo)
    assert not gate._structural_source_check(relative, repo)
    assert not checker._resolved_safe_descendant(relative, repo)
    after = external_source.stat()
    assert (after.st_size, after.st_mtime_ns) == (before.st_size, before.st_mtime_ns)


def test_import_is_silent_and_has_no_output_side_effect(tmp_path: Path) -> None:
    code = (
        "import covalent_ext.covapie_bulk_download_admission_admit_010_"
        "leakage_group_assignment_provenance_contract_design_gate"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code], cwd=tmp_path, text=True,
        capture_output=True, check=False,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == ""
    assert completed.stderr == ""
    assert not list(tmp_path.iterdir())


def test_formal_evaluator_result_adapter_runtime_and_admit011_are_absent() -> None:
    checker = _load_checker_module()
    checker._validate_no_premature_api()
    assert not hasattr(gate, "evaluate_admit_010")
    assert not hasattr(gate, "Admit010EvaluationResult")


def test_manifest_freezes_provider_and_training_boundaries() -> None:
    manifest = json.loads((OUTPUT_ROOT / gate.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert manifest["leakage_group_id_provider_mapping_validated"] is False
    assert manifest["real_provider_leakage_group_id_count_nonzero"] is False
    assert manifest["evaluate_admit_010_implemented"] is False
    assert manifest["Admit010EvaluationResult_implemented"] is False
    assert manifest["admit_010_registered_in_engine"] is False
    assert manifest["unified_dispatch_runtime_with_admit_001_to_010_implemented"] is False
    assert manifest["admit_011_started"] is False
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
