from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_pre_reaction_transform_manual_decision_proposal import (
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


def _proposal_row(sample_id: str, reactive_atom: str, accepted: str, boundary: str, covalent: str, bond: str) -> dict[str, str]:
    return {
        "sample_id": sample_id,
        "ligand_reactive_atom_candidate": reactive_atom,
        "accepted_warhead_atoms": accepted,
        "unresolved_boundary_atoms": boundary,
        "proposed_manual_covalent_bond_to_remove": covalent,
        "selected_bond_order_candidate": bond,
        "proposed_manual_bond_order_to_restore": f"{bond}:double",
        "high_priority_candidate_count": "1",
        "all_candidate_bonds": bond,
        "all_high_priority_candidate_bonds": bond,
        "proposed_manual_boundary_resolution": "reviewed_no_boundary_atoms_transferred_to_pre_reaction_transform_rule_candidate",
        "requires_boundary_manual_confirmation": "true",
        "proposal_status": "proposal_only_not_approved",
        "reviewer_decision": "",
        "reviewer_note": "proposal_only_no_decision_written",
        "review_status": "draft_not_reviewed",
        "requires_manual_review": "true",
        "can_write_back_to_decision_draft": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "decision_source": "test",
    }


def _decision_row(sample_id: str, reactive_atom: str, accepted: str, boundary: str, covalent: str) -> dict[str, str]:
    return {
        "sample_id": sample_id,
        "warhead_type": "toy",
        "ligand_reactive_atom_candidate": reactive_atom,
        "accepted_warhead_atoms": accepted,
        "unresolved_boundary_atoms": boundary,
        "proposed_covalent_bond_to_remove_candidate": covalent,
        "proposed_bond_order_to_restore_candidate": "",
        "proposed_atoms_requiring_charge_check": reactive_atom,
        "proposed_atoms_requiring_valence_check": accepted,
        "boundary_resolution_required": "true",
        "manual_covalent_bond_to_remove": "",
        "manual_bond_order_to_restore": "",
        "manual_atoms_requiring_charge_check": "",
        "manual_atoms_requiring_valence_check": "",
        "manual_boundary_resolution": "",
        "reviewer_decision": "",
        "reviewer_note": "",
        "review_status": "draft_not_reviewed",
        "requires_manual_review": "true",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "decision_source": "test",
    }


def _candidate_row(sample_id: str, reactive_atom: str, accepted: str, bond: str) -> dict[str, str]:
    atom_a, atom_b = bond.split("-")
    return {
        "sample_id": sample_id,
        "ligand_reactive_atom_candidate": reactive_atom,
        "accepted_warhead_atoms": accepted,
        "candidate_bond_atom_1": atom_a,
        "candidate_bond_atom_2": atom_b,
        "candidate_bond": bond,
        "current_bond_order_in_repaired_sdf": "1",
        "proposed_restore_bond_order": "double_candidate",
        "candidate_reason": "touches_ligand_reactive_atom_candidate",
        "candidate_priority": "high",
        "requires_manual_review": "true",
        "reviewer_decision": "",
        "reviewer_note": "",
        "review_status": "draft_not_reviewed",
        "decision_source": "test",
    }


def _toy_tables(tmp_path: Path) -> tuple[Path, Path, Path]:
    samples = [
        ("BTK_C481_6DI9", "19", "17 18 19 32", "13 14 15 28 29", "CYS:SG-19", "18-19"),
        ("KRAS_G12C_5F2E", "29", "8 27 28 29", "7 24 25 26", "CYS:SG-29", "8-29"),
        ("KRAS_G12C_6OIM", "7", "4 5 6 7", "0 1 2 3 8 9", "CYS:SG-7", "6-7"),
    ]
    proposal_csv = tmp_path / "proposal.csv"
    decision_csv = tmp_path / "decision.csv"
    candidate_csv = tmp_path / "candidate.csv"
    _write_csv(proposal_csv, [_proposal_row(*sample) for sample in samples])
    _write_csv(decision_csv, [_decision_row(*sample[:-1]) for sample in samples])
    _write_csv(candidate_csv, [_candidate_row(sample[0], sample[1], sample[2], sample[5]) for sample in samples])
    return proposal_csv, decision_csv, candidate_csv


def test_consistent_proposal_can_be_considered_for_manual_write_back(tmp_path: Path) -> None:
    proposal_csv, decision_csv, candidate_csv = _toy_tables(tmp_path)
    output_csv = tmp_path / "report.csv"
    output_md = tmp_path / "report.md"
    proposal_hash = _sha256(proposal_csv)
    decision_hash = _sha256(decision_csv)
    candidate_hash = _sha256(candidate_csv)

    rows = build_report_rows(
        proposal_csv=proposal_csv,
        decision_csv=decision_csv,
        bond_candidate_csv=candidate_csv,
    )
    write_csv(rows, output_csv)
    write_markdown(build_markdown(rows), output_md)

    assert len(rows) == 3
    assert {row["proposal_check_status"] for row in rows} == {"consistent_proposal_only"}
    assert {row["proposal_consistent_with_decision_draft"] for row in rows} == {"true"}
    assert {row["proposal_consistent_with_bond_candidate_review"] for row in rows} == {"true"}
    assert {row["can_consider_manual_write_back"] for row in rows} == {"true"}
    assert {row["proposal_status"] for row in rows} == {"proposal_only_not_approved"}
    assert {row["can_write_back_to_decision_draft"] for row in rows} == {"false"}
    assert {row["pre_reaction_transform_ready"] for row in rows} == {"false"}
    assert {row["training_ready"] for row in rows} == {"false"}
    assert "Pre-Reaction Transform Manual Decision Proposal Check Summary" in output_md.read_text(encoding="utf-8")
    assert _sha256(proposal_csv) == proposal_hash
    assert _sha256(decision_csv) == decision_hash
    assert _sha256(candidate_csv) == candidate_hash
    assert not list(tmp_path.rglob("*.sdf"))


def test_mismatch_proposal_is_blocked_with_reasons(tmp_path: Path) -> None:
    proposal_csv, decision_csv, candidate_csv = _toy_tables(tmp_path)
    rows = list(csv.DictReader(proposal_csv.open("r", encoding="utf-8", newline="")))
    rows[0]["proposed_manual_covalent_bond_to_remove"] = "CYS:SG-999"
    rows[0]["selected_bond_order_candidate"] = "17-32"
    rows[0]["proposed_manual_bond_order_to_restore"] = "17-32:double"
    _write_csv(proposal_csv, rows)
    proposal_hash = _sha256(proposal_csv)

    report_rows = build_report_rows(
        proposal_csv=proposal_csv,
        decision_csv=decision_csv,
        bond_candidate_csv=candidate_csv,
    )
    row = next(report for report in report_rows if report["sample_id"] == "BTK_C481_6DI9")

    assert row["proposal_check_status"] == "blocked"
    assert row["proposal_consistent_with_decision_draft"] == "false"
    assert row["proposal_consistent_with_bond_candidate_review"] == "false"
    assert row["can_consider_manual_write_back"] == "false"
    assert "proposal_decision_draft_mismatch" in row["blocking_reasons"]
    assert "selected_bond_order_candidate_not_found" in row["blocking_reasons"]
    assert _sha256(proposal_csv) == proposal_hash
