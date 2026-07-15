#!/usr/bin/env python3
"""Verify deterministic Step14AU-C2 candidate record ID overlay outputs."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import covapie_bulk_download_admission_candidate_record_id_semantics_integration_gate as gate  # noqa: E402


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _validate_exact_output_files(root: Path) -> None:
    expected = {*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME}
    actual = {path.name for path in root.iterdir()}
    assert actual == expected
    assert all((root / name).is_file() and not (root / name).is_symlink() for name in expected)


def _validate_manifest_and_outputs(
    manifest: dict[str, object], root: Path, first_hashes: dict[str, str],
) -> None:
    """Validate current disk evidence independently of manifest declarations."""
    _validate_exact_output_files(root)
    current_hashes = {
        name: _hash(root / name) for name in (*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME)
    }
    assert current_hashes == first_hashes
    source = gate._load_source()
    source_rows = gate._source_boundary_rows()
    assert gate._validate_source_rows(source_rows)
    assert gate._validate_source_semantics(source)
    assert {row["source_relative_path"]: row["sha256_observed"] for row in source_rows} == gate.SOURCE_SHA256
    assert gate._validate_c1_helpers()

    assert manifest["stage"] == gate.STAGE
    assert manifest["step_label"] == "Step14AU-C2"
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["manifest_schema_version"] == gate.MANIFEST_SCHEMA_VERSION
    assert manifest["previous_stages"] == list(gate.PREVIOUS_STAGES)
    assert manifest["source_read_boundary"] == (
        "only_step14au_b2_and_step14au_c1_12_committed_metadata_outputs"
    )
    assert manifest["source_input_count"] == 12
    assert manifest["source_input_sha256"] == gate.SOURCE_SHA256
    assert manifest["output_files"] == [*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME]
    assert manifest["output_file_count"] == 6
    assert manifest["non_manifest_output_count"] == 5
    assert manifest["output_sha256"] == {
        name: current_hashes[name] for name in gate.CSV_OUTPUTS
    }
    assert gate.MANIFEST_FILENAME not in manifest["output_sha256"]
    assert manifest["blocking_reasons"] == list(gate.REMAINING_ISSUE_IDS)
    assert manifest["canonical_mask_pairs"] == [list(pair) for pair in gate.CANONICAL_MASK_PAIRS]
    assert manifest["canonical_mask_task_count"] == 5
    assert ["scaffold_only", "B3"] in manifest["canonical_mask_pairs"]
    assert all(manifest[key] is True for key in (
        "artifact_reference_paths_not_recursively_opened",
        "all_source_boundary_checks_passed",
        "all_integration_lineage_checks_passed",
        "all_integrated_rule_checks_passed",
        "all_integrated_field_checks_passed",
        "all_integrated_context_checks_passed",
        "all_issue_transition_checks_passed",
        "all_safety_checks_passed",
        "all_checks_passed",
        "candidate_record_id_semantics_integrated",
        "admit_001_rule_logic_ready",
        "pdb_identifier_semantics_integrated",
        "ready_for_admission_evaluator_interface_implementation",
        "feature_semantics_audit_required_before_training",
    ))
    assert all(manifest[key] is False for key in (
        "ready_for_admission_evaluator_rule_logic_implementation",
        "ready_for_real_candidate_evaluation",
        "ready_for_bulk_download_now",
        "ready_for_training",
        "ready_to_train_now",
        "candidate_records_materialized_current_step",
        "download_queue_materialized_current_step",
        "raw_structure_read_current_step",
        "network_access_used_current_step",
    ))
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP
    assert manifest["changed_rule_ids"] == ["ADMIT_001"]
    assert manifest["changed_field_names"] == ["candidate_record_id"]
    assert manifest["changed_context_items"] == ["candidate_record_id_contract"]
    assert manifest["removed_issue_ids"] == [gate.REMOVED_ISSUE_ID]
    assert manifest["remaining_issue_count"] == 11
    assert manifest["rule_dependency_contract_passed_count"] == 15
    assert (manifest["integrated_rule_count"], manifest["semantics_complete_rule_count"],
            manifest["semantics_incomplete_rule_count"]) == (15, 4, 11)
    assert (manifest["integrated_field_count"], manifest["semantics_complete_field_count"],
            manifest["semantics_incomplete_field_count"]) == (17, 2, 15)
    assert (
        manifest["integrated_context_count"],
        manifest["deterministic_now_context_count"],
        manifest["deterministic_after_contract_freeze_context_count"],
        manifest["ready_evaluation_context_count"],
    ) == (18, 7, 18, 7)

    rules = _csv(root / gate.CSV_OUTPUTS[0])
    fields = _csv(root / gate.CSV_OUTPUTS[1])
    contexts = _csv(root / gate.CSV_OUTPUTS[2])
    safety = _csv(root / gate.CSV_OUTPUTS[3])
    issues = _csv(root / gate.CSV_OUTPUTS[4])
    assert gate._validate_lineage_rows(rules, fields, contexts)
    assert gate._validate_integrated_rule_rows(rules, source["rule_rows"])
    assert gate._validate_integrated_field_rows(fields, source["field_rows"])
    assert gate._validate_integrated_context_rows(contexts, source["context_rows"])
    assert gate._validate_issue_transition_rows(issues, source["issue_rows"])
    assert gate._validate_safety_rows(safety)
    assert tuple(row["admission_rule_id"] for row in rules if row["semantics_complete"] == "true") == gate.COMPLETE_RULE_IDS
    assert tuple(
        row["field_name"] for row in fields if row["implementation_semantics_complete"] == "true"
    ) == gate.COMPLETE_FIELD_NAMES
    assert tuple(row["context_item"] for row in contexts if row["implementation_ready"] == "true") == gate.READY_CONTEXT_ITEMS
    assert [row["issue_id"] for row in issues] == list(gate.REMAINING_ISSUE_IDS)
    assert len(safety) == 16

    serialized = json.dumps(manifest, sort_keys=True)
    assert "timestamp" not in serialized.lower()
    assert "/home/" not in serialized
    assert [path.as_posix() for path in gate._source_paths()] == list(gate.SOURCE_SHA256)


def main() -> int:
    root = REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT
    first = gate.run_covapie_bulk_download_admission_candidate_record_id_semantics_integration_gate_v1(root)
    _validate_exact_output_files(root)
    first_hashes = {
        name: _hash(root / name) for name in (*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME)
    }
    second = gate.run_covapie_bulk_download_admission_candidate_record_id_semantics_integration_gate_v1(root)
    _validate_exact_output_files(root)
    second_hashes = {
        name: _hash(root / name) for name in (*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME)
    }
    assert first == second and first_hashes == second_hashes
    manifest = json.loads((root / gate.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert manifest == second
    _validate_manifest_and_outputs(manifest, root, first_hashes)
    print(f"stage={gate.STAGE}")
    print("all_checks_passed=true")
    print("candidate_record_id_semantics_integrated=true")
    print("admit_001_rule_logic_ready=true")
    print("remaining_issue_count=11")
    print("ready_for_admission_evaluator_rule_logic_implementation=false")
    print("ready_for_real_candidate_evaluation=false")
    print("ready_for_bulk_download_now=false")
    print("ready_for_training=false")
    print("ready_to_train_now=false")
    print("candidate_record_id_semantics_integration_outputs_byte_identical=true")
    print("covapie_bulk_download_admission_candidate_record_id_semantics_integration_gate_v1_passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
