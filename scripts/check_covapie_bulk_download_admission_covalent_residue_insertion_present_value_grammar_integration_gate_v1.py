#!/usr/bin/env python3
"""Fail-closed direct checker for the Step14AU-E1-D integration outputs."""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_covalent_residue_insertion_present_value_grammar_integration_gate as gate,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv(path: Path, columns: Sequence[str]) -> list[dict[str, str]]:
    assert path.is_file() and not path.is_symlink()
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert tuple(reader.fieldnames or ()) == tuple(columns)
        rows = [dict(row) for row in reader]
    assert all(tuple(row) == tuple(columns) and all(value is not None for value in row.values()) for row in rows)
    return rows


def _standard_library_only(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    allowed = {
        "__future__", "ast", "csv", "hashlib", "io", "json", "os", "stat",
        "subprocess", "sys", "tempfile", "dataclasses", "pathlib", "typing",
        "covalent_ext",
    }
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots <= allowed


def _direct_predecessor_and_overlay_checks(
    snapshot: gate.FrozenSourceSnapshot,
    state: Mapping[str, Any],
) -> None:
    e1b = gate._validate_e1b(snapshot)
    e1c = gate._validate_e1c(snapshot)
    assert len(e1b["rules"]) == 15 and len(e1b["fields"]) == 22
    assert len(e1b["contexts"]) == 18 and len(e1b["issues"]) == 10
    assert sum(row["semantics_complete"] == "true" for row in e1b["rules"]) == 6
    assert sum(row["implementation_semantics_complete"] == "true" for row in e1b["fields"]) == 11
    assert sum(row["implementation_ready"] == "true" for row in e1b["contexts"]) == 8
    assert len(e1c["contract"]) == 31 and all(row["contract_passed"] == "true" for row in e1c["contract"])
    assert len(e1c["examples"]) == 64 and all(row["example_passed"] == "true" for row in e1c["examples"])
    assert [sum(row["row_kind"] == kind for row in e1c["examples"]) for kind in (
        "present_valid_example", "present_invalid_example", "state_value_truth",
    )] == [35, 15, 14]
    assert len(e1c["issues"]) == 10 and all(row["status"] == "open" for row in e1c["issues"])
    assert gate._validate_exact11_invariant(e1b, e1c)

    rules, fields, contexts, issues = (
        state["rule_rows"], state["field_rows"], state["context_rows"], state["issue_rows"],
    )
    rule_allowed = {
        "semantics_complete", "deterministic_evaluation_possible_now",
        "deterministic_evaluation_possible_after_contract_freeze", "implementation_disposition",
        "blocking_reasons", "integration_source_stage", "integration_applied", "integration_reason",
    }
    field_allowed = {
        "source_value_contract", "allowed_values_defined", "normalization_defined",
        "exact_validation_defined", "implementation_semantics_complete", "semantics_evidence",
        "blocking_reasons", "integration_source_stage", "integration_applied", "integration_reason",
    }
    context_allowed = {
        "deterministic_now", "deterministic_after_contract_freeze", "exact_contract_defined",
        "implementation_ready", "blocking_reasons", "integration_source_stage",
        "integration_applied", "integration_reason",
    }
    assert gate._unchanged_except(rules, e1b["rules"], "admission_rule_id", "ADMIT_004", rule_allowed)
    assert gate._unchanged_except(fields, e1b["fields"], "field_name", "covalent_residue_insertion_code", field_allowed)
    assert gate._unchanged_except(contexts, e1b["contexts"], "context_item", "covalent_residue_identity_contract", context_allowed)
    rule_map = {row["admission_rule_id"]: row for row in rules}
    field_map = {row["field_name"]: row for row in fields}
    e1b_field_map = {row["field_name"]: row for row in e1b["fields"]}
    context_map = {row["context_item"]: row for row in contexts}
    admit_004 = rule_map["ADMIT_004"]
    insertion = field_map["covalent_residue_insertion_code"]
    identity = context_map["covalent_residue_identity_contract"]
    assert admit_004["semantics_complete"] == admit_004["deterministic_evaluation_possible_now"] == "true"
    assert admit_004["implementation_disposition"] == "rule_logic_ready" and admit_004["blocking_reasons"] == ""
    assert insertion["source_value_contract"] == gate.INSERTION_SOURCE_VALUE_CONTRACT
    assert insertion["normalization_defined"] == insertion["exact_validation_defined"] == "true"
    assert insertion["implementation_semantics_complete"] == "true" and insertion["blocking_reasons"] == ""
    assert identity["deterministic_now"] == identity["exact_contract_defined"] == identity["implementation_ready"] == "true"
    assert identity["blocking_reasons"] == ""
    for name in (
        "covalent_residue_locator_namespace", "covalent_residue_insertion_code_state",
        "covalent_residue_locator_provenance_source_id", "covalent_residue_locator_provenance_sha256",
    ):
        assert field_map[name] == e1b_field_map[name]
    expected_issue_ids = [row["issue_id"] for row in e1c["issues"] if row["issue_id"] != gate.IDENTITY_ISSUE]
    assert [row["issue_id"] for row in issues] == expected_issue_ids
    issue_map = {row["issue_id"]: row for row in issues}
    e1c_issue_map = {row["issue_id"]: row for row in e1c["issues"]}
    assert gate.IDENTITY_ISSUE not in issue_map
    assert all(issue_map[item] == e1c_issue_map[item] for item in expected_issue_ids)
    provider = issue_map[gate.PROVIDER_ISSUE]
    assert provider["status"] == "open" and provider["severity"] == "blocking" and provider["issue_count"] == "11"


def check(output_root: Path = gate.DEFAULT_OUTPUT_ROOT) -> dict[str, Any]:
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    assert root.is_dir() and not root.is_symlink()
    assert {path.name for path in root.iterdir()} == set(gate.OUTPUT_FILES)
    assert all(path.is_file() and not path.is_symlink() for path in root.iterdir())
    assert not any(path.name.endswith((".tmp", ".part")) for path in root.iterdir())

    snapshot = gate.build_frozen_source_snapshot(REPO_ROOT)
    assert gate.validate_frozen_source_snapshot(snapshot)
    assert tuple(record.relative_path for record in snapshot.records) == gate.SOURCE_PATHS
    assert all(
        record.expected_sha256 == record.base_tree_sha256 == record.filesystem_sha256
        == gate.SOURCE_SHA256[record.relative_path]
        for record in snapshot.records
    )
    state = gate.build_integration_state(snapshot)
    assert state["source_ok"] is state["e1b_ok"] is state["e1c_ok"] is True
    assert state["all_checks_passed"] is True and state["validation_failures"] == []
    assert (
        state["integrated_rule_count"], state["integrated_field_count"],
        state["integrated_context_count"], state["active_issue_count"],
    ) == (15, 22, 18, 9)
    assert (
        state["semantics_complete_rule_count"],
        state["implementation_semantics_complete_field_count"],
        state["implementation_ready_context_count"],
    ) == (7, 12, 9)
    _direct_predecessor_and_overlay_checks(snapshot, state)

    output_specs = (
        (gate.RULE_FILENAME, gate.RULE_COLUMNS, state["rule_rows"]),
        (gate.FIELD_FILENAME, gate.FIELD_COLUMNS, state["field_rows"]),
        (gate.CONTEXT_FILENAME, gate.CONTEXT_COLUMNS, state["context_rows"]),
        (gate.SAFETY_FILENAME, gate.SAFETY_COLUMNS, state["safety_rows"]),
        (gate.ISSUE_FILENAME, gate.ISSUE_COLUMNS, state["issue_rows"]),
    )
    for filename, columns, expected_rows in output_specs:
        assert _csv(root / filename, columns) == list(expected_rows)
    csv_hashes = {filename: _sha256(root / filename) for filename in gate.CSV_OUTPUTS}
    manifest_path = root / gate.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert type(manifest) is dict and manifest == gate._manifest_payload(state, csv_hashes)
    assert not any(key in manifest for key in ("timestamp", "hostname", "host", "manifest_sha256"))
    assert gate.MANIFEST_FILENAME not in manifest["output_sha256"]
    assert manifest["source_input_paths"] == [path.as_posix() for path in gate.SOURCE_PATHS]
    assert manifest["source_input_sha256"] == {path.as_posix(): gate.SOURCE_SHA256[path] for path in gate.SOURCE_PATHS}
    assert manifest["resolved_issue_ids"] == [gate.IDENTITY_ISSUE]
    assert manifest["provider_blocking_issue_count"] == 11
    assert manifest["exact11_count"] == manifest["exact11_insertion_unknown_count"] == 11
    assert manifest["exact11_insertion_value_empty_count"] == manifest["exact11_insertion_blocked_count"] == 11
    assert manifest["exact11_effective_blocked_count"] == 11 and manifest["exact11_reason"] == gate.UNKNOWN_REASON
    assert manifest["exact11_auth_label_conflict_count"] == 3 and manifest["exact11_auth_label_no_conflict_count"] == 8
    true_keys = (
        "insertion_present_value_grammar_integrated_into_effective_schema",
        "residue_identity_semantics_integrated_into_effective_schema",
        "covalent_residue_identity_contract_fully_integrated", "admit_004_rule_logic_ready",
        "ready_for_admit_004_rule_logic_implementation", "admit_005_rule_logic_ready",
        "invalid_state_value_outcomes_fail_closed",
        "agreement_requires_struct_conn_atom_site_candidate_and_provenance_exact_equality",
        "feature_semantics_audit_required_before_training", "all_checks_passed",
    )
    false_keys = (
        "admit_004_evaluator_implemented", "parser_quote_class_roundtrip_verified",
        "real_provider_present_value_roundtrip_ready", "real_provider_export_blocking_rows_resolved",
        "candidate_records_materialized", "ready_for_real_candidate_evaluation",
        "ready_for_bulk_download_now", "ready_for_training", "ready_to_train_now",
    )
    assert all(manifest[key] is True for key in true_keys)
    assert all(manifest[key] is False for key in false_keys)
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP
    safety = _csv(root / gate.SAFETY_FILENAME, gate.SAFETY_COLUMNS)
    assert safety == gate._safety_rows() and all(row["safety_passed"] == "true" for row in safety)

    production_path = REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_covalent_residue_insertion_present_value_grammar_integration_gate.py"
    assert _standard_library_only(production_path)
    assert _standard_library_only(Path(__file__))

    with tempfile.TemporaryDirectory(prefix="covapie_e1d_check_a_") as first_name, tempfile.TemporaryDirectory(prefix="covapie_e1d_check_b_") as second_name:
        first, second = Path(first_name), Path(second_name)
        gate.run_covapie_bulk_download_admission_covalent_residue_insertion_present_value_grammar_integration_gate_v1(first)
        gate.run_covapie_bulk_download_admission_covalent_residue_insertion_present_value_grammar_integration_gate_v1(second)
        assert all(
            (first / filename).read_bytes() == (second / filename).read_bytes() == (root / filename).read_bytes()
            for filename in gate.OUTPUT_FILES
        )
        assert not any(
            path.name.endswith((".tmp", ".part"))
            for directory in (first, second) for path in directory.iterdir()
        )

    return {
        "source_count": 12, "integrated_counts": "15/22/18/9",
        "complete_ready_counts": "7/12/9", "exact11_blocked": "11/11",
        "provider_blocking_count": 11, "quote_class_roundtrip_ready": False,
        "bulk_download_ready": False, "training_ready": False,
        "output_sha256": {filename: _sha256(root / filename) for filename in gate.OUTPUT_FILES},
        "all_checks_passed": True,
    }


def main() -> int:
    result = check()
    assert result["source_count"] == 12
    print("source_count=12")
    assert result["integrated_counts"] == "15/22/18/9"
    print("integrated_counts=15/22/18/9")
    assert result["complete_ready_counts"] == "7/12/9"
    print("complete_ready_counts=7/12/9")
    assert result["exact11_blocked"] == "11/11"
    print("exact11_blocked=11/11")
    assert result["provider_blocking_count"] == 11
    print("provider_blocking_count=11")
    assert result["quote_class_roundtrip_ready"] is False
    print("quote_class_roundtrip_ready=false")
    assert result["bulk_download_ready"] is False
    print("ready_for_bulk_download_now=false")
    assert result["training_ready"] is False
    print("ready_for_training=false")
    for filename, digest in result["output_sha256"].items():
        assert len(digest) == 64
        print(f"sha256[{filename}]={digest}")
    assert result["all_checks_passed"] is True
    print("all_checks_passed=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
