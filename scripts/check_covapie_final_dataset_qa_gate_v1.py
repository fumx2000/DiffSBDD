#!/usr/bin/env python3
"""Materialize and verify the deterministic CovaPIE final-dataset QA v1 gate."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext.covapie_final_dataset_qa_gate_v1 import (  # noqa: E402
    CSV_OUTPUTS,
    DEFAULT_OUTPUT_ROOT,
    MANIFEST_FILENAME,
    SOURCE_STEP14AQ_MANIFEST_SHA256,
    SOURCE_STEP14AR_MANIFEST_SHA256,
    STAGE,
    run_covapie_final_dataset_qa_gate_v1,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    output_root = REPO_ROOT / DEFAULT_OUTPUT_ROOT
    first = run_covapie_final_dataset_qa_gate_v1(output_root)
    first_hashes = {name: sha256(output_root / name) for name in (*CSV_OUTPUTS, MANIFEST_FILENAME)}
    second = run_covapie_final_dataset_qa_gate_v1(output_root)
    second_hashes = {name: sha256(output_root / name) for name in (*CSV_OUTPUTS, MANIFEST_FILENAME)}
    manifest = json.loads((output_root / MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert first["all_checks_passed"] is True
    assert second["all_checks_passed"] is True
    assert manifest["all_checks_passed"] is True
    assert first_hashes == second_hashes
    assert manifest["output_file_count"] == 8
    assert manifest["source_step14ar_manifest_sha256"] == SOURCE_STEP14AR_MANIFEST_SHA256
    assert manifest["source_step14aq_manifest_sha256"] == SOURCE_STEP14AQ_MANIFEST_SHA256
    assert all(
        sha256(REPO_ROOT / relative_path) == expected_hash
        for relative_path, expected_hash in manifest["source_input_sha256"].items()
    )
    assert {name: first_hashes[name] for name in CSV_OUTPUTS} == manifest["output_sha256"]
    assert manifest["ready_for_covapie_canonical_final_dataset_bulk_download_admission_design_gate"] is True
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    print(f"stage={STAGE}")
    print(f"source_step14ar_manifest_sha256={SOURCE_STEP14AR_MANIFEST_SHA256}")
    print(f"source_step14aq_manifest_sha256={SOURCE_STEP14AQ_MANIFEST_SHA256}")
    print(f"source_input_count={manifest['source_input_count']}")
    print(f"output_file_count={manifest['output_file_count']}")
    print(f"final_dataset_row_count={manifest['final_dataset_row_count']}")
    print(f"canonical_schema_field_count={manifest['canonical_schema_field_count']}")
    print(f"canonical_mask_task_count={manifest['canonical_mask_task_count']}")
    print(f"qa_issue_count={manifest['qa_issue_count']}")
    print(f"all_checks_passed={str(manifest['all_checks_passed']).lower()}")
    print("ready_for_covapie_canonical_final_dataset_bulk_download_admission_design_gate=true")
    print("ready_for_bulk_download_now=false")
    print("ready_for_training=false")
    print("ready_to_train_now=false")
    print("feature_semantics_audit_required_before_training=true")
    print(f"recommended_next_step={manifest['recommended_next_step']}")
    print("qa_v1_output_hashes_byte_identical=true")
    print("covapie_final_dataset_qa_gate_v1_passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
