#!/usr/bin/env python3
"""Direct checker for the Step14AU-E1-C design gate outputs."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_covalent_residue_insertion_present_value_grammar_design_gate as gate,
)


def _csv(path: Path, expected_header: Sequence[str]) -> list[dict[str, str]]:
    if path.is_symlink() or not path.is_file():
        raise AssertionError(f"missing, non-regular, or symlink output: {path.name}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert tuple(reader.fieldnames or ()) == tuple(expected_header)
        rows = [dict(row) for row in reader]
    assert all(tuple(row) == tuple(expected_header) and all(value is not None for value in row.values()) for row in rows)
    return rows


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(output_root: Path = gate.DEFAULT_OUTPUT_ROOT) -> dict[str, Any]:
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    assert root.is_dir() and not root.is_symlink()
    assert {path.name for path in root.iterdir()} == set(gate.OUTPUT_FILES)
    assert not any(path.is_symlink() for path in root.iterdir())
    assert not any(path.name.endswith((".tmp", ".part")) for path in root.iterdir())

    snapshot = gate.build_frozen_source_snapshot(REPO_ROOT)
    assert gate.validate_frozen_source_snapshot(snapshot)
    assert len(snapshot.records) == 39
    assert tuple(record.relative_path for record in snapshot.records) == gate.SOURCE_PATHS
    assert all(record.expected_sha256 == record.observed_sha256 == gate.SOURCE_SHA256[record.relative_path] for record in snapshot.records)

    assert gate.NORMATIVE_DICTIONARY_NAME == "PDBx/mmCIF V5"
    assert gate.NORMATIVE_ITEM == "_atom_site.pdbx_PDB_ins_code"
    assert gate.NORMATIVE_REFERENCE_ROLE == "_struct_conn.pdbx_ptnr1/2_PDB_ins_code references atom_site insertion code"
    assert gate.WWPDB_DICTIONARY_CODE_PATTERN == r"[][_,.;:\"&<>()/\{}'`~!@#$%A-Za-z0-9*|+-]*"
    assert gate.INSERTION_PRESENT_VALUE_PATTERN == r"[][_,.;:\"&<>()/\{}'`~!@#$%A-Za-z0-9*|+-]+"
    assert len(gate.ALLOWED_PUNCTUATION) == 28
    for character in gate.ALLOWED_PUNCTUATION:
        result = gate.validate_covalent_residue_insertion_present_value(f"A{character}B")
        assert result["valid"] is True and result["canonical_value"] == f"A{character}B"
    for value in ("", ".", "?", "A B", "A\tB", " A", "A ", "A\nB", "A\rB", "A=B", "A\\B", "é"):
        assert gate.validate_covalent_residue_insertion_present_value(value)["valid"] is False
    assert gate.validate_covalent_residue_insertion_present_value("A.B")["valid"] is True
    assert gate.validate_covalent_residue_insertion_present_value("A" * 4096)["valid"] is True

    invalid_state_values = (
        (1, ""), ("other", ""), ("absent", None), ("absent", "A"),
        ("unknown", None), ("unknown", "A"), ("present", None),
        ("present", ""), ("present", "."), ("present", "?"),
        ("present", "A B"), ("present", "é"), ("present", "A=B"),
    )
    for state_value in invalid_state_values:
        result = gate.validate_covalent_residue_insertion_state_value(*state_value)
        assert result["outcome"] == "invalid" and result["blocks_admit_004"] is True
    unknown = gate.validate_covalent_residue_insertion_state_value("unknown", "")
    absent = gate.validate_covalent_residue_insertion_state_value("absent", "")
    present = gate.validate_covalent_residue_insertion_state_value("present", "A.B")
    assert unknown["outcome"] == "blocked" and unknown["blocks_admit_004"] is True
    assert absent["outcome"] == "passed" and absent["blocks_admit_004"] is False
    assert present["outcome"] == "passed" and present["blocks_admit_004"] is False

    agreement = gate.validate_struct_conn_atom_site_insertion_agreement(True, "A.B", True, "A.B", "A.B", "A.B")
    assert agreement["valid"] is True and agreement["outcome"] == "passed" and agreement["canonical_value"] == "A.B"
    candidate_conflict = gate.validate_struct_conn_atom_site_insertion_agreement(True, "A.B", True, "A.B", "A", "A.B")
    provenance_conflict = gate.validate_struct_conn_atom_site_insertion_agreement(True, "A.B", True, "A.B", "A.B", "A")
    invalid_candidate = gate.validate_struct_conn_atom_site_insertion_agreement(True, "A.B", True, "A.B", 1, "A.B")
    invalid_provenance = gate.validate_struct_conn_atom_site_insertion_agreement(True, "A.B", True, "A.B", "A.B", 1)
    assert candidate_conflict["reason"] == provenance_conflict["reason"] == gate.SOURCE_CONFLICT_REASON
    assert invalid_candidate["reason"] == invalid_provenance["reason"] == gate.EVIDENCE_INVALID_REASON

    contract = _csv(root / gate.CONTRACT_FILENAME, gate.CONTRACT_COLUMNS)
    examples = _csv(root / gate.EXAMPLES_FILENAME, gate.EXAMPLE_COLUMNS)
    sources = _csv(root / gate.SOURCE_FILENAME, gate.SOURCE_COLUMNS)
    safety = _csv(root / gate.SAFETY_FILENAME, gate.SAFETY_COLUMNS)
    issues = _csv(root / gate.ISSUE_FILENAME, gate.ISSUE_COLUMNS)
    assert len(contract) == 31 and all(row["contract_passed"] == "true" for row in contract)
    fail_closed_contract = next(
        row for row in contract
        if row["contract_statement"] == "all invalid state/value outcomes block ADMIT_004 fail closed"
    )
    assert fail_closed_contract["contract_area"] == "state_value"
    assert fail_closed_contract["expected_value"] == fail_closed_contract["observed_value"] == "true"
    assert fail_closed_contract["contract_passed"] == "true"
    assert len(examples) == 64 and all(row["example_passed"] == "true" for row in examples)
    assert [sum(row["row_kind"] == kind for row in examples) for kind in ("present_valid_example", "present_invalid_example", "state_value_truth")] == [35, 15, 14]
    assert len(sources) == 39
    assert [row["source_relative_path"] for row in sources] == [path.as_posix() for path in gate.SOURCE_PATHS]
    assert all(row["source_verified"] == "true" and row["sha256_expected"] == row["sha256_observed"] for row in sources)
    assert len(safety) == len(gate.TRUE_SAFETY_ITEMS) + len(gate.FALSE_SAFETY_ITEMS)
    assert all(row["safety_passed"] == "true" for row in safety)
    assert len(issues) == 10 and all(row["status"] == "open" for row in issues)
    identity = next(row for row in issues if row["issue_id"] == "COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED")
    assert identity["affected_fields"] == "covalent_residue_insertion_code"
    assert identity["affected_rules"] == "ADMIT_004" and identity["issue_count"] == "1"
    assert identity["integration_transition"] == "insertion_present_value_grammar_design_frozen_pending_successor_integration"
    provider = next(row for row in issues if row["issue_id"] == "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT")
    assert provider["severity"] == "blocking" and provider["status"] == "open" and provider["issue_count"] == "11"

    manifest_path = root / gate.MANIFEST_FILENAME
    assert manifest_path.is_file() and not manifest_path.is_symlink()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert type(manifest) is dict
    assert not any(key in manifest for key in ("timestamp", "hostname", "host", "manifest_sha256"))
    assert gate.MANIFEST_FILENAME not in manifest["output_sha256"]
    assert manifest["source_input_count"] == 39 and manifest["examples_and_state_value_truth_row_count"] == 64
    assert manifest["allowed_punctuation_count"] == 28
    assert manifest["exact11_count"] == manifest["exact11_unknown_count"] == manifest["exact11_blocked_count"] == 11
    assert manifest["exact11_auth_label_conflict_count"] == 3 and manifest["exact11_auth_label_no_conflict_count"] == 8
    true_keys = (
        "insertion_present_value_grammar_design_frozen", "state_value_combination_contract_frozen",
        "exact_preserve_policy_frozen", "struct_conn_atom_site_agreement_design_frozen",
        "ready_for_insertion_present_value_grammar_successor_integration",
        "candidate_value_grammar_design_not_blocked_by_quote_class_gap",
        "invalid_state_value_outcomes_fail_closed",
        "agreement_requires_struct_conn_atom_site_candidate_and_provenance_exact_equality",
        "feature_semantics_audit_required_before_training", "all_source_boundary_checks_passed", "all_checks_passed",
    )
    false_keys = (
        "insertion_present_value_grammar_integrated_into_effective_schema",
        "covalent_residue_identity_contract_fully_integrated", "admit_004_rule_logic_ready",
        "ready_for_admit_004_rule_logic_implementation", "admit_004_evaluator_implemented",
        "parser_quote_class_roundtrip_verified", "real_provider_present_value_roundtrip_ready",
        "candidate_records_materialized", "ready_for_real_candidate_evaluation",
        "ready_for_bulk_download_now", "ready_for_training", "ready_to_train_now",
    )
    assert all(manifest[key] is True for key in true_keys)
    assert all(manifest[key] is False for key in false_keys)
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP
    for filename in gate.CSV_OUTPUTS:
        assert manifest["output_sha256"][filename] == _sha(root / filename)

    with tempfile.TemporaryDirectory(prefix="covapie_e1c_check_") as first_name, tempfile.TemporaryDirectory(prefix="covapie_e1c_check_") as second_name:
        first, second = Path(first_name), Path(second_name)
        gate.run_covapie_bulk_download_admission_covalent_residue_insertion_present_value_grammar_design_gate_v1(first)
        gate.run_covapie_bulk_download_admission_covalent_residue_insertion_present_value_grammar_design_gate_v1(second)
        assert all((first / filename).read_bytes() == (second / filename).read_bytes() == (root / filename).read_bytes() for filename in gate.OUTPUT_FILES)
        assert not any(path.name.endswith((".tmp", ".part")) for directory in (first, second) for path in directory.iterdir())

    return {
        "source_count": len(sources), "contract_count": len(contract), "matrix_count": len(examples),
        "punctuation_count": len(gate.ALLOWED_PUNCTUATION), "issue_count": len(issues),
        "exact11_blocked_count": manifest["exact11_blocked_count"],
        "invalid_outcomes_fail_closed": True, "four_way_agreement_contract": True,
        "output_sha256": {filename: _sha(root / filename) for filename in gate.OUTPUT_FILES},
        "all_checks_passed": True,
    }


def main() -> None:
    result = check()
    assert result["source_count"] == 39
    print(f"source_count={result['source_count']}")
    assert result["matrix_count"] == 64
    print(f"matrix_count={result['matrix_count']}")
    assert result["punctuation_count"] == 28
    print(f"punctuation_count={result['punctuation_count']}")
    assert result["exact11_blocked_count"] == 11
    print(f"exact11_blocked_count={result['exact11_blocked_count']}")
    assert result["invalid_outcomes_fail_closed"] is True
    print("invalid_outcomes_fail_closed=true")
    assert result["four_way_agreement_contract"] is True
    print("four_way_agreement_contract=true")
    for filename, digest in result["output_sha256"].items():
        assert len(digest) == 64
        print(f"sha256[{filename}]={digest}")
    assert result["all_checks_passed"] is True
    print("all_checks_passed=true")


if __name__ == "__main__":
    main()
