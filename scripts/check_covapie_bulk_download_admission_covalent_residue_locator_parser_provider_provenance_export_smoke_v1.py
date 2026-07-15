#!/usr/bin/env python3
"""Validate deterministic Step14AU-E0-P5-B synthetic smoke outputs."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_smoke
    as gate,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _serialized_rows(
    rows: list[dict[str, Any]], columns: tuple[str, ...]
) -> list[dict[str, str]]:
    return [
        {column: str(gate._csv_value(row[column])) for column in columns}
        for row in rows
    ]


def _output_hashes(root: Path) -> dict[str, str]:
    return {name: _sha256(root / name) for name in gate.OUTPUT_FILES}


def _validate_exact_output_set(root: Path) -> None:
    assert root.is_dir() and not root.is_symlink()
    assert tuple(sorted(path.name for path in root.iterdir())) == tuple(
        sorted(gate.OUTPUT_FILES)
    )
    assert all(
        (root / name).is_file() and not (root / name).is_symlink()
        for name in gate.OUTPUT_FILES
    )


def validate_materialized_outputs(
    root: Path, expected_hashes: dict[str, str] | None = None
) -> dict[str, Any]:
    """Validate full rows and manifest without rewriting the output root."""
    _validate_exact_output_set(root)
    current_hashes = _output_hashes(root)
    if expected_hashes is not None:
        assert current_hashes == expected_hashes

    state = gate.build_smoke_state()
    contract = _csv_rows(root / gate.CONTRACT_FILENAME)
    cases = _csv_rows(root / gate.CASE_FILENAME)
    sources = _csv_rows(root / gate.SOURCE_FILENAME)
    safety = _csv_rows(root / gate.SAFETY_FILENAME)
    issues = _csv_rows(root / gate.ISSUE_FILENAME)
    manifest = json.loads((root / gate.MANIFEST_FILENAME).read_text(encoding="utf-8"))

    assert contract == _serialized_rows(state["contract_rows"], gate.CONTRACT_COLUMNS)
    assert cases == _serialized_rows(state["case_rows"], gate.CASE_COLUMNS)
    assert sources == _serialized_rows(state["source_rows"], gate.SOURCE_COLUMNS)
    assert safety == _serialized_rows(state["safety_rows"], gate.SAFETY_COLUMNS)
    assert issues == _serialized_rows(state["issue_rows"], gate.ISSUE_COLUMNS)
    assert len(contract) == 42
    assert len(cases) == 16 and len(gate.CASE_COLUMNS) == 33
    assert len(sources) == 9
    assert len(safety) == 20
    assert len(issues) == 2

    assert tuple(row["smoke_case_id"] for row in cases) == gate.CASE_IDS
    counts = Counter(row["provider_export_status"] for row in cases)
    assert counts == Counter(exported_pass=5, exported_blocking=5, rejected=6)
    for row in cases:
        fields = [row[field] for field in gate.P3_FIELDS]
        if row["provider_export_status"] == "rejected":
            assert fields == ["", "", "", "", ""]
        else:
            assert fields[0] and fields[1] and fields[3]
            assert len(fields[4]) == 64 and fields[4] == fields[4].lower()
    for case_id in gate.CASE_IDS[3:8]:
        row = next(item for item in cases if item["smoke_case_id"] == case_id)
        assert row["provider_export_status"] == "exported_blocking"
        assert row["covalent_residue_insertion_code_state"] == "unknown"
        assert row["covalent_residue_insertion_code"] == ""
    for case_id in (
        gate.CASE_IDS[8],
        gate.CASE_IDS[11],
        gate.CASE_IDS[12],
        gate.CASE_IDS[13],
        gate.CASE_IDS[14],
    ):
        row = next(item for item in cases if item["smoke_case_id"] == case_id)
        assert [
            row["resolved_insertion_state"],
            row["resolved_insertion_value"],
            row["insertion_evidence_agreement"],
            row["insertion_blocks_admit_004"],
            row["insertion_blocking_reason"],
        ] == ["", "", "", "", ""]
        assert row["provider_export_status"] == "rejected"
        assert row["provider_export_blocking_reason"]
    case16 = next(item for item in cases if item["smoke_case_id"] == gate.CASE_IDS[15])
    assert case16["resolved_insertion_state"] == "present"
    assert case16["resolved_insertion_value"] == "A"
    assert case16["insertion_evidence_agreement"] == "true"
    assert case16["insertion_blocks_admit_004"] == "false"
    assert case16["insertion_blocking_reason"] == ""
    assert case16["provider_export_status"] == "rejected"
    assert case16["provider_export_blocking_reason"] == (
        "PROVENANCE_SOURCE_ID_COMPONENT_INVALID"
    )
    assert {cases[0]["residue_partner_side"], cases[1]["residue_partner_side"]} == {
        "ptnr1",
        "ptnr2",
    }
    token_classes = {
        cases[index]["atom_site_token_class"] for index in (2, 3, 4, 5)
    }
    assert token_classes == {
        "dot_not_applicable",
        "question_unknown",
        "tag_missing",
        "parsed_empty",
    }

    expected_manifest = gate._manifest_payload(
        state, {name: current_hashes[name] for name in gate.CSV_OUTPUTS}
    )
    assert manifest == expected_manifest
    assert manifest["source_input_count"] == 9
    assert manifest["source_input_sha256"] == gate.SOURCE_SHA256
    assert manifest["output_files"] == list(gate.OUTPUT_FILES)
    assert manifest["output_file_count"] == 6
    assert manifest["non_manifest_output_count"] == 5
    assert manifest["canonical_mask_pairs"] == [
        list(pair) for pair in gate.CANONICAL_MASK_PAIRS
    ]
    assert ["scaffold_only", "B3"] in manifest["canonical_mask_pairs"]
    assert manifest["canonical_mask_task_count"] == 5
    assert manifest["all_checks_passed"] is True
    assert manifest["historical_compatibility_view_verified"] is True
    assert manifest["synthetic_case_count"] == 16
    assert manifest["synthetic_sidecar_column_count"] == 33
    assert manifest["exported_pass_case_count"] == 5
    assert manifest["exported_blocking_case_count"] == 5
    assert manifest["rejected_case_count"] == 6
    assert manifest["real_parser_pipeline_integration_implemented"] is False
    assert manifest["real_provider_pipeline_integration_implemented"] is False
    assert manifest["existing_real_sample_count"] == 11
    assert manifest["real_insertion_unknown_sample_count"] == 11
    assert manifest["real_insertion_absence_proven_sample_count"] == 0
    assert manifest["admit_004_rule_logic_ready"] is False
    assert manifest["ready_for_e1_residue_identity_semantics_design"] is False
    assert manifest["ready_for_real_candidate_evaluation"] is False
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["ready_for_real_parser_provider_pipeline_integration_design"] is True
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP
    assert manifest["validation_failures"] == []
    return manifest


def main() -> None:
    root = REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT
    source_hashes_before = {
        path.as_posix(): _sha256(REPO_ROOT / path) for path in gate.SOURCE_PATHS
    }
    first = gate.run_covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_smoke_v1()
    first_hashes = _output_hashes(root)
    first_manifest = validate_materialized_outputs(root, first_hashes)
    second = gate.run_covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_smoke_v1()
    second_manifest = validate_materialized_outputs(root, first_hashes)
    assert first["manifest"] == first_manifest == second["manifest"] == second_manifest
    assert _output_hashes(root) == first_hashes
    assert {
        path.as_posix(): _sha256(REPO_ROOT / path) for path in gate.SOURCE_PATHS
    } == source_hashes_before

    print(f"stage={gate.STAGE}")
    print("all_checks_passed=true")
    print("additive_raw_preserving_parser_adapter_implemented=true")
    print("historical_compatibility_view_verified=true")
    print("synthetic_case_count=16")
    print("synthetic_sidecar_column_count=33")
    print("exported_pass_case_count=5")
    print("exported_blocking_case_count=5")
    print("rejected_case_count=6")
    print("real_parser_pipeline_integration_implemented=false")
    print("real_provider_pipeline_integration_implemented=false")
    print("existing_real_sample_count=11")
    print("real_insertion_unknown_sample_count=11")
    print("real_insertion_absence_proven_sample_count=0")
    print("ready_for_real_parser_provider_pipeline_integration_design=true")
    print("admit_004_rule_logic_ready=false")
    print("ready_for_e1_residue_identity_semantics_design=false")
    print("ready_for_real_candidate_evaluation=false")
    print("ready_for_bulk_download_now=false")
    print("ready_for_training=false")
    print("ready_to_train_now=false")
    print("parser_provider_provenance_export_smoke_outputs_byte_identical=true")
    print(
        "covapie_bulk_download_admission_covalent_residue_locator_parser_provider_"
        "provenance_export_smoke_v1_passed"
    )


if __name__ == "__main__":
    main()
