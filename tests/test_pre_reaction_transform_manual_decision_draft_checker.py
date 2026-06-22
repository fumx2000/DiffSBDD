from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_pre_reaction_transform_manual_decision_draft import (
    build_markdown,
    build_report_rows,
    write_csv,
    write_markdown,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _decision_row(**overrides: str) -> dict[str, str]:
    row = {
        "sample_id": "toy",
        "warhead_type": "toy_michael_acceptor_draft",
        "ligand_reactive_atom_candidate": "3",
        "accepted_warhead_atoms": "1 2 3 4",
        "unresolved_boundary_atoms": "5 6",
        "proposed_covalent_bond_to_remove_candidate": "CYS:SG-3",
        "proposed_bond_order_to_restore_candidate": "",
        "proposed_atoms_requiring_charge_check": "3",
        "proposed_atoms_requiring_valence_check": "1 2 3 4",
        "boundary_resolution_required": "true",
        "manual_covalent_bond_to_remove": "",
        "manual_bond_order_to_restore": "",
        "manual_atoms_requiring_charge_check": "",
        "manual_atoms_requiring_valence_check": "",
        "manual_boundary_resolution": "",
        "reviewer_decision": "",
        "reviewer_note": "draft_only_no_transform_performed",
        "review_status": "draft_not_reviewed",
        "requires_manual_review": "true",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "decision_source": "pre_reaction_transform_readiness_summary",
    }
    row.update(overrides)
    return row


def test_current_manual_decision_draft_is_blocked(tmp_path: Path) -> None:
    decision_csv = tmp_path / "decision.csv"
    output_csv = tmp_path / "report.csv"
    output_md = tmp_path / "report.md"
    _write_csv(decision_csv, [_decision_row()])
    input_hash = _sha256(decision_csv)

    rows = build_report_rows(decision_csv)
    write_csv(rows, output_csv)
    write_markdown(build_markdown(rows), output_md)

    row = rows[0]
    assert row["decision_check_status"] == "blocked"
    assert row["can_approve_for_future_transform"] == "false"
    for reason in [
        "requires_manual_review_true",
        "review_status_not_reviewed",
        "reviewer_decision_missing",
        "manual_covalent_bond_to_remove_missing",
        "manual_bond_order_to_restore_missing",
        "manual_boundary_resolution_missing",
        "proposed_bond_order_to_restore_candidate_missing",
    ]:
        assert reason in row["blocking_reasons"]
    assert _sha256(decision_csv) == input_hash
    assert not list(tmp_path.rglob("*.sdf"))


def test_missing_manual_fields_block_approval(tmp_path: Path) -> None:
    decision_csv = tmp_path / "decision.csv"
    _write_csv(
        decision_csv,
        [
            _decision_row(
                requires_manual_review="false",
                review_status="reviewed",
                reviewer_decision="approved",
                proposed_bond_order_to_restore_candidate="1-2:double",
                manual_covalent_bond_to_remove="",
                manual_bond_order_to_restore="",
                manual_boundary_resolution="",
            )
        ],
    )

    row = build_report_rows(decision_csv)[0]

    assert row["decision_check_status"] == "blocked"
    assert "manual_covalent_bond_to_remove_missing" in row["blocking_reasons"]
    assert "manual_bond_order_to_restore_missing" in row["blocking_reasons"]
    assert "manual_boundary_resolution_missing" in row["blocking_reasons"]


def test_fully_reviewed_manual_decision_can_be_approved_for_future_transform(tmp_path: Path) -> None:
    decision_csv = tmp_path / "decision.csv"
    _write_csv(
        decision_csv,
        [
            _decision_row(
                requires_manual_review="false",
                review_status="reviewed",
                reviewer_decision="approved",
                proposed_bond_order_to_restore_candidate="1-2:double",
                manual_covalent_bond_to_remove="CYS:SG-3",
                manual_bond_order_to_restore="1-2:double",
                manual_boundary_resolution="reviewed_no_cross_boundary_transfer",
            )
        ],
    )

    row = build_report_rows(decision_csv)[0]

    assert row["decision_check_status"] == "eligible_for_future_transform_dry_run_only"
    assert row["can_approve_for_future_transform"] == "true"
    assert row["blocking_reasons"] == ""
