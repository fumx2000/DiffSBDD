#!/usr/bin/env python3
"""Independent checker for the ADMIT_007 evaluator-precondition audit v1."""

from __future__ import annotations

import csv
import hashlib
import importlib
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_007_formal_evaluator_interface_preconditions_audit as gate,
)

# checker-owned expectations
EXPECTED_RULE_ID = "ADMIT_007"
EXPECTED_RULE_NAME = "distance_only_inference_forbidden"
EXPECTED_FIELD = "covalent_event_evidence_source"
EXPECTED_CONTEXT_ITEM = "allowed_covalent_evidence_classes"
EXPECTED_ENUM = (
    "explicit_structure_bond_record",
    "explicit_curated_covalent_annotation",
    "distance_only_inference",
)
EXPECTED_CONTEXT = EXPECTED_ENUM[:2]
EXPECTED_SCALAR_REASONS = (
    "COVALENT_EVENT_EVIDENCE_SOURCE_TYPE_INVALID",
    "COVALENT_EVENT_EVIDENCE_SOURCE_EMPTY",
    "COVALENT_EVENT_EVIDENCE_SOURCE_NON_ASCII",
    "COVALENT_EVENT_EVIDENCE_SOURCE_SYNTAX_INVALID",
    "COVALENT_EVENT_EVIDENCE_SOURCE_UNKNOWN",
)
EXPECTED_CONTEXT_REASONS = (
    "ALLOWED_COVALENT_EVIDENCE_CLASSES_TYPE_INVALID",
    "ALLOWED_COVALENT_EVIDENCE_CLASSES_CONTENT_INVALID",
)
EXPECTED_BLOCKED_REASON = "DISTANCE_ONLY_INFERENCE_NOT_ADMISSIBLE"
EXPECTED_HISTORICAL_REASON = "distance_only_inference_not_admissible"
EXPECTED_ORACLE = "classify_admit_006_admit_007_evidence_design"
EXPECTED_FILES = (
    "covapie_admit_007_evaluator_precondition_matrix.csv",
    "covapie_admit_007_field_occurrence_inventory.csv",
    "covapie_admit_007_observed_evidence_value_inventory.csv",
    "covapie_admit_007_source_boundary_audit.csv",
    "covapie_admit_007_issue_readiness_inventory.csv",
    "covapie_admit_007_formal_evaluator_preconditions_manifest.json",
)
EXPECTED_OUTPUT_SHA256 = {
    "covapie_admit_007_evaluator_precondition_matrix.csv": "a6c1b8a84e1dd112b0b26ed0a0d87e235f117df3368f14b056048358ed7fb29c",
    "covapie_admit_007_field_occurrence_inventory.csv": "655271d518a25472350ac8cafb90e0d030c3dedccd130a977eba6fef74a8e6ad",
    "covapie_admit_007_observed_evidence_value_inventory.csv": "1bb5c224dbfe8b1d2c19a44331cc91a8b18ad1afe8abd985e5a6f6b01606c4cf",
    "covapie_admit_007_source_boundary_audit.csv": "9bfd3b9815b044416cec8aece37556347a7da1cde574de8df05bf6e8872a176a",
    "covapie_admit_007_issue_readiness_inventory.csv": "e63c1b83fe245031ecdefa6b3387086b2aba8d72ef50189be17b9874e8f18196",
    "covapie_admit_007_formal_evaluator_preconditions_manifest.json": "8459b898d543c50f36e625faff2bba7ba0491bce130c488c32ae91b3c3ef0d2a",
}
EXPECTED_SOURCE_PATHS = tuple(path.as_posix() for path in gate.SOURCE_PATHS)
EXPECTED_SOURCE_SHA256 = {path.as_posix(): digest for path, digest in gate.SOURCE_SHA256.items()}
EXPECTED_ISSUE_SHA256 = "e63c1b83fe245031ecdefa6b3387086b2aba8d72ef50189be17b9874e8f18196"
EXPECTED_MATCH_TERMS = {
    "ADMIT_007", "distance_only_inference_forbidden", EXPECTED_HISTORICAL_REASON,
    EXPECTED_BLOCKED_REASON, EXPECTED_FIELD, EXPECTED_CONTEXT_ITEM,
    *EXPECTED_ENUM, EXPECTED_ORACLE,
}
TRUE_READINESS = {
    "admit_007_candidate_field_contract_available",
    "admit_007_scalar_validation_contract_available",
    "admit_007_context_contract_available",
    "admit_007_enum_contract_available",
    "admit_007_reason_outcome_contract_available",
    "admit_007_canonical_state_contract_available",
    "admit_007_independent_semantic_oracle_available",
    "admit_007_shared_enum_dependency_resolved",
    "admit_007_standalone_evaluator_preconditions_complete",
    "ready_for_admit_007_standalone_evaluator_interface_implementation",
    "feature_semantics_audit_required_before_training",
}
FALSE_READINESS = {
    "admit_007_standalone_evaluator_implemented",
    "admit_007_unified_adapter_contract_frozen", "admit_007_unified_adapter_implemented",
    "admit_007_registered_in_engine", "current_exact6_runtime_modified",
    "admit_008_standalone_evaluator_implemented", "admit_008_to_015_registered_in_engine",
    "all_15_rules_covered", "evaluate_all_rules_implemented",
    "combined_candidate_verdict_contract_frozen", "combined_candidate_verdict_implemented",
    "cross_rule_precedence_frozen", "real_provider_enum_mapping_validated",
    "real_candidate_evaluation", "exact11_real_rows_evaluated",
    "ready_for_bulk_download_now", "ready_for_training", "ready_to_train_now",
}

PRECONDITION_HEADER = (
    "precondition_id", "semantic_area", "required_contract", "observed_contract",
    "source_evidence", "semantics_complete", "blocker_id",
    "implementation_disposition", "precondition_passed",
)
OCCURRENCE_HEADER = (
    "occurrence_order", "source_relative_path", "source_sha256", "source_kind",
    "symbol_or_row_id", "matched_term", "field_role", "rule_scope",
    "semantic_statement", "contains_concrete_value", "concrete_value",
    "authoritative_for_runtime_semantics", "occurrence_passed",
)
VALUE_HEADER = (
    "value_order", "observed_value", "source_relative_path", "source_row_or_symbol",
    "source_role", "exact_string", "occurrence_count", "evidence_interpretation",
    "real_provider_value", "enum_membership_frozen", "safe_for_admit_007_pass",
    "value_inventory_passed",
)
SOURCE_HEADER = (
    "source_order", "source_relative_path", "source_kind", "boundary_necessity",
    "tracked", "base_tree_blob", "filesystem_regular", "non_symlink",
    "expected_sha256", "base_tree_sha256", "filesystem_sha256", "source_boundary_passed",
)
ISSUE_HEADER = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status",
    "blocking_scope", "blocking_reason", "issue_origin", "integration_transition", "issue_count",
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv(path: Path, header: tuple[str, ...]) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"), newline=""))
    assert tuple(reader.fieldnames or ()) == header
    rows = [dict(row) for row in reader]
    assert all(tuple(row) == header and all(value is not None for value in row.values()) for row in rows)
    return rows


def _one(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str]:
    matches = [row for row in rows if row.get(key) == value]
    assert len(matches) == 1
    return matches[0]


def _validate_entries(root: Path) -> None:
    metadata = os.lstat(root)
    assert stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
    assert tuple(sorted(path.name for path in root.iterdir())) == tuple(sorted(EXPECTED_FILES))
    for name in EXPECTED_FILES:
        item = root / name
        metadata = os.lstat(item)
        assert stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)


def _validate_checker_owned_expectations(root: Path) -> dict[str, Any]:
    preconditions = _csv(root / EXPECTED_FILES[0], PRECONDITION_HEADER)
    occurrences = _csv(root / EXPECTED_FILES[1], OCCURRENCE_HEADER)
    values = _csv(root / EXPECTED_FILES[2], VALUE_HEADER)
    sources = _csv(root / EXPECTED_FILES[3], SOURCE_HEADER)
    issues = _csv(root / EXPECTED_FILES[4], ISSUE_HEADER)
    manifest = json.loads((root / EXPECTED_FILES[5]).read_text(encoding="utf-8"))
    assert type(manifest) is dict

    assert [row["precondition_id"] for row in preconditions] == [f"PRE_{index:03d}" for index in range(1, 20)]
    assert all(row["precondition_passed"] == "true" for row in preconditions)
    assert [row["semantics_complete"] for row in preconditions] == ["true"] * 15 + ["false"] * 4
    assert all(row["implementation_disposition"] == "frozen_or_implementable" for row in preconditions[:15])
    assert preconditions[15]["implementation_disposition"] == "future_provider_validation_not_required_for_interface"
    assert preconditions[16]["implementation_disposition"] == "blocked_by_current_scope"
    assert preconditions[17]["blocker_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
    assert preconditions[18]["blocker_id"] == "FEATURE_SEMANTICS_AUDIT_REQUIRED"
    assert EXPECTED_ENUM[2] + "=blocked" in preconditions[7]["observed_contract"]
    assert "ADMIT_007=" + EXPECTED_BLOCKED_REASON in preconditions[8]["observed_contract"]
    assert "explicit=passed" in preconditions[9]["observed_contract"]
    assert set((*EXPECTED_SCALAR_REASONS, *EXPECTED_CONTEXT_REASONS, EXPECTED_BLOCKED_REASON)).issubset(set(preconditions[10]["observed_contract"].split("|")))
    assert "context invalid retains canonical/pair" in preconditions[11]["required_contract"]
    assert EXPECTED_ORACLE == preconditions[13]["required_contract"]

    assert occurrences and [row["occurrence_order"] for row in occurrences] == [str(index) for index in range(1, len(occurrences) + 1)]
    assert {row["matched_term"] for row in occurrences} == EXPECTED_MATCH_TERMS
    assert all(row["occurrence_passed"] == "true" for row in occurrences)
    assert all(row["source_relative_path"] in EXPECTED_SOURCE_PATHS for row in occurrences)
    assert all(row["source_sha256"] == EXPECTED_SOURCE_SHA256[row["source_relative_path"]] for row in occurrences)
    historical = [row for row in occurrences if row["matched_term"] == EXPECTED_HISTORICAL_REASON and row["source_relative_path"].endswith("rule_registry.csv")]
    assert len(historical) == 1 and "historical lowercase" in historical[0]["semantic_statement"]
    assert values == []

    assert len(sources) == 14
    assert [row["source_relative_path"] for row in sources] == list(EXPECTED_SOURCE_PATHS)
    assert all(row["expected_sha256"] == EXPECTED_SOURCE_SHA256[row["source_relative_path"]] for row in sources)
    assert all(row["base_tree_sha256"] == row["expected_sha256"] == row["filesystem_sha256"] for row in sources)
    assert all(row["tracked"] == row["base_tree_blob"] == row["filesystem_regular"] == row["non_symlink"] == row["source_boundary_passed"] == "true" for row in sources)

    assert len(issues) == 11 and _sha(root / EXPECTED_FILES[4]) == EXPECTED_ISSUE_SHA256
    assert _one(issues, "issue_id", "COVALENT_EVIDENCE_ENUM_UNRESOLVED")["status"] == "resolved"
    coverage = _one(issues, "issue_id", "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    assert coverage["status"] == "open"
    assert coverage["affected_rules"] == "|".join(f"ADMIT_{index:03d}" for index in range(7, 16))
    assert _one(issues, "issue_id", "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED")["status"] == "open"
    assert _one(issues, "issue_id", "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT")["issue_count"] == "11"

    assert manifest["admission_rule_id"] == EXPECTED_RULE_ID
    assert manifest["admission_rule_name"] == EXPECTED_RULE_NAME
    assert manifest["candidate_scalar_field"] == EXPECTED_FIELD
    assert manifest["evaluation_context_item"] == EXPECTED_CONTEXT_ITEM
    assert tuple(manifest["canonical_enum_members"]) == EXPECTED_ENUM
    assert tuple(manifest["allowed_covalent_evidence_classes"]) == EXPECTED_CONTEXT
    assert tuple(manifest["scalar_reasons"]) == EXPECTED_SCALAR_REASONS
    assert tuple(manifest["context_reasons"]) == EXPECTED_CONTEXT_REASONS
    assert manifest["historical_registry_blocking_reason"] == EXPECTED_HISTORICAL_REASON
    assert manifest["formal_evaluator_blocked_reason"] == EXPECTED_BLOCKED_REASON
    assert manifest["historical_registry_blocking_reason"] != manifest["formal_evaluator_blocked_reason"]
    assert manifest["outcome_vocabulary"] == ["passed", "blocked", "invalid"]
    assert manifest["explicit_member_outcome"] == "passed"
    assert manifest["distance_only_outcome"] == "blocked"
    assert manifest["invalid_input_outcome"] == "invalid"
    assert manifest["standalone_missing_reason_included"] is False
    assert manifest["independent_semantic_oracle"] == EXPECTED_ORACLE
    assert manifest["independent_oracle_called_by_audit_production"] is False
    assert manifest["future_production_evaluator_may_call_oracle"] is False
    assert manifest["precondition_row_count"] == manifest["precondition_passed_count"] == 19
    assert manifest["semantics_complete_precondition_count"] == 15
    assert manifest["field_occurrence_row_count"] == len(occurrences)
    assert manifest["observed_evidence_value_row_count"] == 0
    assert manifest["issue_inventory_byte_identical_to_authoritative_predecessor"] is True
    assert manifest["source_boundary_count"] == 14
    assert manifest["source_paths"] == list(EXPECTED_SOURCE_PATHS)
    assert manifest["source_sha256"] == EXPECTED_SOURCE_SHA256
    assert manifest["output_files"] == list(EXPECTED_FILES)
    assert manifest["output_file_count"] == 6
    assert manifest["output_sha256_excludes_manifest_self_hash"] is True
    assert set(manifest["output_sha256"]) == set(EXPECTED_FILES[:-1])
    assert all(manifest["output_sha256"][name] == _sha(root / name) for name in EXPECTED_FILES[:-1])
    for key in TRUE_READINESS:
        assert manifest[key] is True and manifest["readiness"][key] is True
    for key in FALSE_READINESS:
        assert manifest[key] is False and manifest["readiness"][key] is False
    assert manifest["recommended_next_step"] == "implement_covapie_admit_007_standalone_evaluator_interface_v1"
    assert manifest["all_checks_passed"] is True
    serialized = json.dumps(manifest, sort_keys=True)
    assert "timestamp" not in serialized.lower() and "/home/" not in serialized
    return manifest


def _validate_committed_normative_contracts() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    assert len(snapshot.records) == 14 and gate.validate_frozen_source_snapshot(snapshot)
    state = gate._validate_predecessors(snapshot)
    assert state["enum_truth_row_count"] == 37
    assert hashlib.sha256(state["runtime_issue_bytes"]).hexdigest() == EXPECTED_ISSUE_SHA256


def _validate_production_state(root: Path) -> None:
    state = gate.build_audit_state()
    expected = {
        gate.PRECONDITION_FILENAME: gate._csv_bytes(gate.PRECONDITION_COLUMNS, state["precondition_rows"]),
        gate.OCCURRENCE_FILENAME: gate._csv_bytes(gate.OCCURRENCE_COLUMNS, state["occurrence_rows"]),
        gate.VALUE_FILENAME: gate._csv_bytes(gate.VALUE_COLUMNS, state["value_rows"]),
        gate.SOURCE_BOUNDARY_FILENAME: gate._csv_bytes(gate.SOURCE_BOUNDARY_COLUMNS, state["source_rows"]),
        gate.ISSUE_FILENAME: state["issue_bytes"],
    }
    assert all((root / name).read_bytes() == content for name, content in expected.items())


def _validate_disk(root: Path, *, enforce_frozen_hashes: bool = True) -> dict[str, Any]:
    _validate_entries(root)
    manifest = _validate_checker_owned_expectations(root)
    _validate_committed_normative_contracts()
    _validate_production_state(root)
    if enforce_frozen_hashes:
        assert EXPECTED_OUTPUT_SHA256
        assert {name: _sha(root / name) for name in EXPECTED_FILES} == EXPECTED_OUTPUT_SHA256
    return manifest


def _raises(function: Any, *args: Any, **kwargs: Any) -> None:
    try:
        function(*args, **kwargs)
    except (AssertionError, ValueError):
        return
    raise AssertionError("expected fail-closed rejection")


def _negative_checks(root: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="covapie_admit007_checker_") as temporary:
        temp = Path(temporary)
        tampered = temp / "tampered"
        shutil.copytree(root, tampered)
        matrix_path = tampered / EXPECTED_FILES[0]
        text = matrix_path.read_text(encoding="utf-8").replace(
            "distance_only_inference=blocked", "distance_only_inference=invalid", 1
        )
        matrix_path.write_text(text, encoding="utf-8")
        manifest_path = tampered / EXPECTED_FILES[5]
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["output_sha256"][EXPECTED_FILES[0]] = _sha(matrix_path)
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _raises(_validate_disk, tampered, enforce_frozen_hashes=False)

        overclaim = temp / "overclaim"
        shutil.copytree(root, overclaim)
        manifest_path = overclaim / EXPECTED_FILES[5]
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["admit_007_registered_in_engine"] = True
        manifest["readiness"]["admit_007_registered_in_engine"] = True
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _raises(_validate_disk, overclaim, enforce_frozen_hashes=False)

        extra = temp / "extra"
        shutil.copytree(root, extra)
        (extra / "unexpected.txt").write_text("unexpected", encoding="utf-8")
        _raises(_validate_disk, extra, enforce_frozen_hashes=False)

        unsafe = temp / "unsafe"
        unsafe.mkdir()
        victim = temp / "victim"
        victim.write_text("unchanged", encoding="utf-8")
        (unsafe / gate.SOURCE_BOUNDARY_FILENAME).symlink_to(victim)
        _raises(
            gate.run_covapie_bulk_download_admission_admit_007_formal_evaluator_interface_preconditions_audit_v1,
            unsafe,
        )
        assert victim.read_text(encoding="utf-8") == "unchanged"


def main() -> int:
    root = REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT
    first = gate.run_covapie_bulk_download_admission_admit_007_formal_evaluator_interface_preconditions_audit_v1(root)
    first_hashes = {name: _sha(root / name) for name in EXPECTED_FILES}
    second = gate.run_covapie_bulk_download_admission_admit_007_formal_evaluator_interface_preconditions_audit_v1(root)
    second_hashes = {name: _sha(root / name) for name in EXPECTED_FILES}
    assert first["manifest"] == second["manifest"] and first_hashes == second_hashes
    manifest = _validate_disk(root)
    _negative_checks(root)
    print(f"stage={gate.STAGE}")
    print("all_checks_passed=true")
    print("source_boundary_exact14=true")
    print("precondition_exact19_passed=true")
    print(f"field_occurrence_row_count={manifest['field_occurrence_row_count']}")
    print("observed_evidence_value_row_count=0")
    print("issue_inventory_exact11_byte_identical=true")
    print("ready_for_admit_007_standalone_evaluator_interface_implementation=true")
    print(f"recommended_next_step={gate.RECOMMENDED_NEXT_STEP}")
    print("outputs_byte_identical=true")
    print("covapie_admit_007_formal_evaluator_interface_preconditions_audit_v1_passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
