#!/usr/bin/env python3
"""Verify deterministic Step14AU-E0-P4 design-gate outputs."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_design_gate
    as gate,
)


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _output_hashes(root: Path) -> dict[str, str]:
    return {
        name: _hash(root / name)
        for name in (*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME)
    }


def _validate_exact_outputs(root: Path) -> None:
    expected = {*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME}
    assert root.is_dir() and not root.is_symlink()
    assert {path.name for path in root.iterdir()} == expected
    assert all((root / name).is_file() and not (root / name).is_symlink() for name in expected)


def _validate_manifest_and_outputs(
    manifest: dict[str, object], root: Path, first_hashes: dict[str, str],
) -> None:
    _validate_exact_outputs(root)
    current_hashes = _output_hashes(root)
    assert current_hashes == first_hashes
    contracts = _csv(root / gate.CSV_OUTPUTS[0])
    resolution = _csv(root / gate.CSV_OUTPUTS[1])
    sources = _csv(root / gate.CSV_OUTPUTS[2])
    safety = _csv(root / gate.CSV_OUTPUTS[3])
    issues = _csv(root / gate.CSV_OUTPUTS[4])
    assert len(contracts) == 48 and gate._validate_contract_rows(contracts)
    assert len(resolution) == 12 and gate._validate_resolution_rows(resolution)
    assert len(sources) == 10 and gate._validate_source_boundary_rows(sources)
    assert len(safety) == 20 and gate._validate_safety_rows(safety)
    assert len(issues) == 2 and gate._validate_issue_rows(issues)
    assert gate._validate_p3_predecessor(gate._load_p3_source())
    expected_manifest = gate._manifest_payload(
        gate._build_materialization(),
        {name: current_hashes[name] for name in gate.CSV_OUTPUTS},
    )
    assert manifest == expected_manifest
    assert manifest["stage"] == gate.STAGE
    assert manifest["step_label"] == gate.STEP_LABEL
    assert manifest["project_name"] == gate.PROJECT_NAME
    assert manifest["manifest_schema_version"] == gate.MANIFEST_SCHEMA_VERSION
    assert manifest["previous_stage"] == gate.PREVIOUS_STAGE
    assert manifest["source_read_boundary"] == gate.SOURCE_READ_BOUNDARY
    assert manifest["source_input_count"] == 10
    assert manifest["source_input_sha256"] == gate.SOURCE_SHA256
    assert manifest["output_files"] == [*gate.CSV_OUTPUTS, gate.MANIFEST_FILENAME]
    assert manifest["output_file_count"] == 6
    assert manifest["non_manifest_output_count"] == 5
    assert manifest["output_sha256"] == {
        name: current_hashes[name] for name in gate.CSV_OUTPUTS
    }
    assert manifest["canonical_mask_pairs"] == [list(pair) for pair in gate.CANONICAL_MASK_PAIRS]
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["predecessor_field_count"] == 22
    assert manifest["predecessor_rule_count"] == 15
    assert manifest["predecessor_context_count"] == 18
    assert manifest["predecessor_remaining_domain_issue_count"] == 10
    assert tuple(manifest["parser_insertion_source_tags"]) == gate.PARSER_INSERTION_SOURCE_TAGS
    assert tuple(manifest["raw_token_classes"]) == gate.RAW_TOKEN_CLASSES
    assert manifest["raw_token_class_count"] == 6
    assert manifest["resolution_matrix_case_count"] == 12
    by_id = {row["resolution_case_id"]: row for row in resolution}
    assert by_id["RESOLVE_001"]["observed_resolved_state"] == "present"
    assert by_id["RESOLVE_001"]["observed_resolved_value"] == "A"
    assert by_id["RESOLVE_006"]["observed_resolved_state"] == "absent"
    for case_id in ("RESOLVE_007", "RESOLVE_008", "RESOLVE_009"):
        assert by_id[case_id]["observed_resolved_state"] == "unknown"
    for case_id in ("RESOLVE_003", "RESOLVE_004", "RESOLVE_005"):
        assert by_id[case_id]["observed_blocking_reason"] == (
            "COVALENT_RESIDUE_INSERTION_CODE_SOURCE_CONFLICT"
        )
    assert gate.build_locator_provenance_source_id(
        "SPREP_000001", "covale1", "ptnr1"
    ) == "covapie:residue-locator:SPREP_000001:covale1:ptnr1"
    payload = gate._sample_payload()
    assert tuple(payload) == gate.CANONICAL_PAYLOAD_KEYS
    assert gate.canonical_locator_provenance_payload_bytes(payload) == json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    assert len(gate.sha256_canonical_locator_provenance_payload(payload)) == 64
    assert manifest["all_checks_passed"] is True
    assert manifest["parser_provider_provenance_export_design_frozen"] is True
    assert manifest["parser_provider_provenance_export_implemented"] is False
    assert manifest["parser_insertion_tag_registry_ready"] is True
    assert manifest["raw_token_classifier_contract_ready"] is True
    assert manifest["insertion_state_resolution_contract_ready"] is True
    assert manifest["provider_five_field_mapping_contract_ready"] is True
    assert manifest["provenance_source_id_template_ready"] is True
    assert manifest["canonical_provenance_payload_contract_ready"] is True
    assert manifest["provenance_sha256_contract_ready"] is True
    assert manifest["canonical_provenance_payload_key_count"] == 20
    assert manifest["namespace_evidence_binding_contract_ready"] is True
    assert manifest["provider_recomputes_namespace_evidence"] is True
    assert manifest["provider_recomputes_insertion_evidence"] is True
    assert manifest["atom_site_row_binding_contract_ready"] is True
    assert manifest["insertion_code_present_value_grammar_fully_frozen"] is False
    assert manifest["existing_sample_count"] == 11
    assert manifest["insertion_unknown_sample_count"] == 11
    assert manifest["insertion_absence_proven_sample_count"] == 0
    assert manifest["fully_provable_pre_download_sample_count"] == 0
    assert manifest["samples_admissible_current_step"] == 0
    assert manifest["ready_for_parser_provider_provenance_export_smoke_implementation"] is True
    assert manifest["insertion_code_provenance_export_ready"] is False
    assert manifest["admit_004_rule_logic_ready"] is False
    assert manifest["ready_for_e1_residue_identity_semantics_design"] is False
    assert manifest["ready_for_real_candidate_evaluation"] is False
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["candidate_records_materialized_current_step"] is False
    assert manifest["provider_payloads_materialized_current_step"] is False
    assert manifest["download_queue_materialized_current_step"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["current_domain_blocking_reasons"] == list(gate.DOMAIN_BLOCKING_REASONS)
    assert manifest["design_followup_issue_ids"] == list(gate.DESIGN_FOLLOWUP_ISSUE_IDS)
    assert manifest["validation_failures"] == []
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP
    assert ["scaffold_only", "B3"] in manifest["canonical_mask_pairs"]
    assert manifest["canonical_mask_task_count"] == 5
    assert all(manifest[key] is True for key in (
        "all_source_boundary_checks_passed", "all_p3_predecessor_checks_passed",
        "all_contract_checks_passed", "all_resolution_matrix_checks_passed",
        "all_issue_inventory_checks_passed", "all_safety_checks_passed",
    ))


def _validate_manifest(manifest: dict[str, object], root: Path) -> None:
    """Compatibility wrapper used by focused tests."""
    _validate_manifest_and_outputs(manifest, root, _output_hashes(root))


def main() -> None:
    root = REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT
    before_sources = {path.as_posix(): _hash(REPO_ROOT / path) for path in gate.SOURCE_PATHS}
    first = gate.run_covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_design_gate_v1()
    first_hashes = _output_hashes(root)
    _validate_manifest_and_outputs(first, root, first_hashes)
    second = gate.run_covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_design_gate_v1()
    _validate_manifest_and_outputs(second, root, first_hashes)
    assert second == first
    assert _output_hashes(root) == first_hashes
    assert {path.as_posix(): _hash(REPO_ROOT / path) for path in gate.SOURCE_PATHS} == before_sources

    print(f"stage={gate.STAGE}")
    print("all_checks_passed=true")
    print("parser_provider_provenance_export_design_frozen=true")
    print("parser_provider_provenance_export_implemented=false")
    print("predecessor_field_count=22")
    print("parser_insertion_source_tag_count=3")
    print("raw_token_class_count=6")
    print("resolution_matrix_case_count=12")
    print("existing_sample_count=11")
    print("insertion_unknown_sample_count=11")
    print("insertion_absence_proven_sample_count=0")
    print("ready_for_parser_provider_provenance_export_smoke_implementation=true")
    print("insertion_code_provenance_export_ready=false")
    print("admit_004_rule_logic_ready=false")
    print("ready_for_e1_residue_identity_semantics_design=false")
    print("ready_for_real_candidate_evaluation=false")
    print("ready_for_bulk_download_now=false")
    print("ready_for_training=false")
    print("ready_to_train_now=false")
    print("parser_provider_provenance_export_design_outputs_byte_identical=true")
    print(
        "covapie_bulk_download_admission_covalent_residue_locator_parser_provider_"
        "provenance_export_design_gate_v1_passed"
    )


if __name__ == "__main__":
    main()
