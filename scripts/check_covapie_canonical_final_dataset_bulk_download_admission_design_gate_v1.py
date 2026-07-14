#!/usr/bin/env python3
"""Materialize and verify the deterministic CovaPIE admission-design gate."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext.covapie_canonical_final_dataset_bulk_download_admission_design_gate import (  # noqa: E402
    CSV_OUTPUTS,
    DEFAULT_OUTPUT_ROOT,
    MANIFEST_FILENAME,
    STAGE,
    run_covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    output_root = REPO_ROOT / DEFAULT_OUTPUT_ROOT
    first = run_covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1(output_root)
    first_hashes = {name: _sha256(output_root / name) for name in (*CSV_OUTPUTS, MANIFEST_FILENAME)}
    second = run_covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1(output_root)
    second_hashes = {name: _sha256(output_root / name) for name in (*CSV_OUTPUTS, MANIFEST_FILENAME)}
    manifest = json.loads((output_root / MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert first["all_checks_passed"] is True
    assert second["all_checks_passed"] is True
    assert first_hashes == second_hashes
    assert manifest["all_checks_passed"] is True
    assert manifest["output_file_count"] == 6
    assert manifest["admission_schema_field_count"] == 17
    assert manifest["expected_admission_schema_field_count"] == 17
    assert manifest["admission_rule_count"] == 15
    assert manifest["expected_admission_rule_count"] == 15
    assert manifest["pre_download_required_field_count"] == 12
    assert manifest["pre_final_split_required_field_count"] == 1
    assert manifest["post_download_required_field_count"] == 4
    assert manifest["blocking_reasons"] == []
    assert manifest["all_source_boundary_checks_passed"] is True
    assert manifest["all_admission_schema_contract_checks_passed"] is True
    assert manifest["all_admission_rule_contract_checks_passed"] is True
    assert manifest["all_safety_checks_passed"] is True
    assert manifest["ready_for_bulk_download_admission_implementation"] is True
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["output_sha256"] == {name: first_hashes[name] for name in CSV_OUTPUTS}
    print(f"stage={STAGE}")
    print(f"source_input_count={manifest['source_input_count']}")
    print(f"admission_schema_field_count={manifest['admission_schema_field_count']}")
    print(f"expected_admission_schema_field_count={manifest['expected_admission_schema_field_count']}")
    print(f"admission_rule_count={manifest['admission_rule_count']}")
    print(f"expected_admission_rule_count={manifest['expected_admission_rule_count']}")
    print(f"pre_download_required_field_count={manifest['pre_download_required_field_count']}")
    print(f"pre_final_split_required_field_count={manifest['pre_final_split_required_field_count']}")
    print(f"post_download_required_field_count={manifest['post_download_required_field_count']}")
    print("all_source_boundary_checks_passed=true")
    print("all_admission_schema_contract_checks_passed=true")
    print("all_admission_rule_contract_checks_passed=true")
    print("all_safety_checks_passed=true")
    print("ready_for_bulk_download_admission_implementation=true")
    print("ready_for_bulk_download_now=false")
    print("ready_for_training=false")
    print("ready_to_train_now=false")
    print("feature_semantics_audit_required_before_training=true")
    print("admission_design_output_hashes_byte_identical=true")
    print("covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1_passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
