from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_pre_reaction_transform_manual_decision_proposal import (
    PROPOSAL_STATUS,
    build_markdown,
    build_proposal_rows,
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


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_manual_decision_proposal_selects_single_high_priority_candidate(tmp_path: Path) -> None:
    decision_csv = tmp_path / "decision.csv"
    candidate_csv = tmp_path / "candidates.csv"
    output_csv = tmp_path / "proposal.csv"
    output_md = tmp_path / "proposal.md"
    _write_csv(
        decision_csv,
        [
            {
                "sample_id": "BTK_C481_6DI9",
                "warhead_type": "toy",
                "ligand_reactive_atom_candidate": "19",
                "accepted_warhead_atoms": "17 18 19 32",
                "unresolved_boundary_atoms": "13 14 15 28 29",
                "proposed_covalent_bond_to_remove_candidate": "CYS:SG-19",
                "proposed_bond_order_to_restore_candidate": "",
                "proposed_atoms_requiring_charge_check": "19",
                "proposed_atoms_requiring_valence_check": "17 18 19 32",
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
            },
            {
                "sample_id": "KRAS_G12C_5F2E",
                "warhead_type": "toy",
                "ligand_reactive_atom_candidate": "29",
                "accepted_warhead_atoms": "8 27 28 29",
                "unresolved_boundary_atoms": "7 24 25 26",
                "proposed_covalent_bond_to_remove_candidate": "CYS:SG-29",
                "proposed_bond_order_to_restore_candidate": "",
                "proposed_atoms_requiring_charge_check": "29",
                "proposed_atoms_requiring_valence_check": "8 27 28 29",
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
            },
            {
                "sample_id": "KRAS_G12C_6OIM",
                "warhead_type": "toy",
                "ligand_reactive_atom_candidate": "7",
                "accepted_warhead_atoms": "4 5 6 7",
                "unresolved_boundary_atoms": "0 1 2 3 8 9",
                "proposed_covalent_bond_to_remove_candidate": "CYS:SG-7",
                "proposed_bond_order_to_restore_candidate": "",
                "proposed_atoms_requiring_charge_check": "7",
                "proposed_atoms_requiring_valence_check": "4 5 6 7",
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
            },
        ],
    )
    _write_csv(
        candidate_csv,
        [
            {
                "sample_id": "BTK_C481_6DI9",
                "ligand_reactive_atom_candidate": "19",
                "accepted_warhead_atoms": "17 18 19 32",
                "candidate_bond_atom_1": "17",
                "candidate_bond_atom_2": "18",
                "candidate_bond": "17-18",
                "current_bond_order_in_repaired_sdf": "1",
                "proposed_restore_bond_order": "double_candidate",
                "candidate_reason": "adjacent_warhead_internal_bond_candidate",
                "candidate_priority": "medium",
                "requires_manual_review": "true",
                "reviewer_decision": "",
                "reviewer_note": "",
                "review_status": "draft_not_reviewed",
                "decision_source": "test",
            },
            {
                "sample_id": "BTK_C481_6DI9",
                "ligand_reactive_atom_candidate": "19",
                "accepted_warhead_atoms": "17 18 19 32",
                "candidate_bond_atom_1": "18",
                "candidate_bond_atom_2": "19",
                "candidate_bond": "18-19",
                "current_bond_order_in_repaired_sdf": "2",
                "proposed_restore_bond_order": "double_candidate",
                "candidate_reason": "touches_ligand_reactive_atom_candidate",
                "candidate_priority": "high",
                "requires_manual_review": "true",
                "reviewer_decision": "",
                "reviewer_note": "",
                "review_status": "draft_not_reviewed",
                "decision_source": "test",
            },
            {
                "sample_id": "KRAS_G12C_5F2E",
                "ligand_reactive_atom_candidate": "29",
                "accepted_warhead_atoms": "8 27 28 29",
                "candidate_bond_atom_1": "8",
                "candidate_bond_atom_2": "29",
                "candidate_bond": "8-29",
                "current_bond_order_in_repaired_sdf": "2",
                "proposed_restore_bond_order": "double_candidate",
                "candidate_reason": "touches_ligand_reactive_atom_candidate",
                "candidate_priority": "high",
                "requires_manual_review": "true",
                "reviewer_decision": "",
                "reviewer_note": "",
                "review_status": "draft_not_reviewed",
                "decision_source": "test",
            },
            {
                "sample_id": "KRAS_G12C_6OIM",
                "ligand_reactive_atom_candidate": "7",
                "accepted_warhead_atoms": "4 5 6 7",
                "candidate_bond_atom_1": "6",
                "candidate_bond_atom_2": "7",
                "candidate_bond": "6-7",
                "current_bond_order_in_repaired_sdf": "1",
                "proposed_restore_bond_order": "double_candidate",
                "candidate_reason": "touches_ligand_reactive_atom_candidate",
                "candidate_priority": "high",
                "requires_manual_review": "true",
                "reviewer_decision": "",
                "reviewer_note": "",
                "review_status": "draft_not_reviewed",
                "decision_source": "test",
            },
        ],
    )
    decision_hash = _sha256(decision_csv)
    candidate_hash = _sha256(candidate_csv)

    rows = build_proposal_rows(decision_csv=decision_csv, bond_candidate_csv=candidate_csv)
    write_csv(rows, output_csv)
    write_markdown(build_markdown(rows), output_md)

    by_sample = {row["sample_id"]: row for row in rows}
    assert set(by_sample) == {"BTK_C481_6DI9", "KRAS_G12C_5F2E", "KRAS_G12C_6OIM"}
    assert by_sample["BTK_C481_6DI9"]["selected_bond_order_candidate"] == "18-19"
    assert by_sample["BTK_C481_6DI9"]["proposed_manual_bond_order_to_restore"] == "18-19:double"
    assert by_sample["BTK_C481_6DI9"]["proposed_manual_covalent_bond_to_remove"] == "CYS:SG-19"
    assert by_sample["KRAS_G12C_5F2E"]["selected_bond_order_candidate"] == "8-29"
    assert by_sample["KRAS_G12C_5F2E"]["proposed_manual_bond_order_to_restore"] == "8-29:double"
    assert by_sample["KRAS_G12C_5F2E"]["proposed_manual_covalent_bond_to_remove"] == "CYS:SG-29"
    assert by_sample["KRAS_G12C_6OIM"]["selected_bond_order_candidate"] == "6-7"
    assert by_sample["KRAS_G12C_6OIM"]["proposed_manual_bond_order_to_restore"] == "6-7:double"
    assert by_sample["KRAS_G12C_6OIM"]["proposed_manual_covalent_bond_to_remove"] == "CYS:SG-7"
    assert {row["high_priority_candidate_count"] for row in rows} == {"1"}
    assert {row["proposal_status"] for row in rows} == {PROPOSAL_STATUS}
    assert {row["can_write_back_to_decision_draft"] for row in rows} == {"false"}
    assert {row["requires_manual_review"] for row in rows} == {"true"}
    assert {row["pre_reaction_transform_ready"] for row in rows} == {"false"}
    assert {row["training_ready"] for row in rows} == {"false"}
    assert {row["reviewer_decision"] for row in rows} == {""}
    assert len(_read_csv(output_csv)) == 3
    assert "Pre-Reaction Transform Manual Decision Proposal" in output_md.read_text(encoding="utf-8")
    assert _sha256(decision_csv) == decision_hash
    assert _sha256(candidate_csv) == candidate_hash
    assert not list(tmp_path.glob("*pre*reaction*.sdf"))
