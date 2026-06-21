from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from summarize_warhead_only_repair_readiness import build_readiness_rows, build_markdown, write_csv, write_markdown


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _qa_rows(status: str = "passed") -> list[dict[str, str]]:
    return [
        {
            "sample_id": "toy",
            "output_sdf_path": "derived.sdf",
            "source_ligand_sdf_path": "raw.sdf",
            "bond_endpoint_a": "0",
            "bond_endpoint_b": "1",
            "action_applied": "transferred",
            "expected_old_bond_type": "single",
            "expected_new_bond_type": "double",
            "raw_current_bond_type": "single",
            "repaired_current_bond_type": "double",
            "bond_change_matches_action": "true",
            "coordinate_hash_same": "true",
            "raw_sdf_hash_same": "true",
            "touched_unresolved_boundary": "false",
            "qa_status": status,
            "qa_error": "",
        },
        {
            "sample_id": "toy",
            "output_sdf_path": "derived.sdf",
            "source_ligand_sdf_path": "raw.sdf",
            "bond_endpoint_a": "1",
            "bond_endpoint_b": "2",
            "action_applied": "blocked",
            "expected_old_bond_type": "single",
            "expected_new_bond_type": "single",
            "raw_current_bond_type": "single",
            "repaired_current_bond_type": "single",
            "bond_change_matches_action": "true",
            "coordinate_hash_same": "true",
            "raw_sdf_hash_same": "true",
            "touched_unresolved_boundary": "true",
            "qa_status": "passed",
            "qa_error": "",
        },
    ]


def _manual_summary_rows(has_unresolved_boundary: str = "true") -> list[dict[str, str]]:
    return [
        {
            "sample_id": "toy",
            "rows": "2",
            "accept_candidate_count": "1",
            "unresolved_count": "1" if has_unresolved_boundary == "true" else "0",
            "replace_candidate_count": "0",
            "exclude_sample_count": "0",
            "reviewed_count": "1",
            "needs_followup_count": "1" if has_unresolved_boundary == "true" else "0",
            "excluded_count": "0",
            "reactive_atom_rows": "1",
            "warhead_rows": "1",
            "linker_or_boundary_rows": "1",
            "accepted_warhead_rows": "1",
            "unresolved_boundary_rows": "1" if has_unresolved_boundary == "true" else "0",
            "has_empty_manual_decision": "false",
            "all_warhead_atoms_accepted": "true",
            "has_unresolved_boundary": has_unresolved_boundary,
            "local_bond_order_transfer_ready": "false",
            "recommended_next_action": "strictly_warhead_only_trial_or_manual_boundary_review_before_transfer",
        }
    ]


def test_readiness_safe_but_not_training_ready_with_unresolved_boundary(tmp_path: Path) -> None:
    qa_csv = tmp_path / "qa.csv"
    manual_csv = tmp_path / "manual.csv"
    output_csv = tmp_path / "readiness.csv"
    output_md = tmp_path / "readiness.md"
    _write_csv(qa_csv, _qa_rows())
    _write_csv(manual_csv, _manual_summary_rows())
    qa_hash = _sha256(qa_csv)
    manual_hash = _sha256(manual_csv)

    rows = build_readiness_rows(qa_csv=qa_csv, manual_decision_summary_csv=manual_csv)
    write_csv(rows, output_csv)
    write_markdown(build_markdown(rows), output_md)

    row = rows[0]
    assert row["derived_trial_safe"] == "true"
    assert row["training_ready"] == "false"
    assert row["pre_reaction_graph_ready"] == "false"
    assert row["has_unresolved_boundary"] == "true"
    assert row["recommended_next_action"] == "manual_boundary_review_or_pre_reaction_graph_design_before_training_ready"
    assert _sha256(qa_csv) == qa_hash
    assert _sha256(manual_csv) == manual_hash


def test_readiness_failed_qa_not_safe(tmp_path: Path) -> None:
    qa_csv = tmp_path / "qa.csv"
    manual_csv = tmp_path / "manual.csv"
    rows = _qa_rows(status="failed")
    _write_csv(qa_csv, rows)
    _write_csv(manual_csv, _manual_summary_rows())

    readiness = build_readiness_rows(qa_csv=qa_csv, manual_decision_summary_csv=manual_csv)

    assert readiness[0]["qa_failed_rows"] == "1"
    assert readiness[0]["derived_trial_safe"] == "false"
    assert readiness[0]["training_ready"] == "false"


def test_readiness_defaults_pre_reaction_graph_not_ready_even_without_boundary(tmp_path: Path) -> None:
    qa_csv = tmp_path / "qa.csv"
    manual_csv = tmp_path / "manual.csv"
    _write_csv(qa_csv, _qa_rows())
    _write_csv(manual_csv, _manual_summary_rows(has_unresolved_boundary="false"))

    readiness = build_readiness_rows(qa_csv=qa_csv, manual_decision_summary_csv=manual_csv)

    assert readiness[0]["derived_trial_safe"] == "true"
    assert readiness[0]["cross_boundary_transfer_ready"] == "true"
    assert readiness[0]["pre_reaction_graph_ready"] == "false"
    assert readiness[0]["training_ready"] == "false"
