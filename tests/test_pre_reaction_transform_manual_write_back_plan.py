from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_pre_reaction_transform_manual_write_back_plan import (
    APPROVAL_PHRASE,
    PLAN_STATUS,
    build_markdown,
    build_plan_rows,
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


def _proposal_row(sample_id: str, reactive_atom: str, accepted: str, boundary: str, covalent: str, restore: str) -> dict[str, str]:
    bond = restore.split(":")[0]
    return {
        "sample_id": sample_id,
        "ligand_reactive_atom_candidate": reactive_atom,
        "accepted_warhead_atoms": accepted,
        "unresolved_boundary_atoms": boundary,
        "proposed_manual_covalent_bond_to_remove": covalent,
        "selected_bond_order_candidate": bond,
        "proposed_manual_bond_order_to_restore": restore,
        "high_priority_candidate_count": "1",
        "all_candidate_bonds": bond,
        "all_high_priority_candidate_bonds": bond,
        "proposed_manual_boundary_resolution": "reviewed_no_boundary_atoms_transferred_to_pre_reaction_transform_rule_candidate",
        "requires_boundary_manual_confirmation": "true",
        "proposal_status": "proposal_only_not_approved",
        "reviewer_decision": "",
        "reviewer_note": "",
        "review_status": "draft_not_reviewed",
        "requires_manual_review": "true",
        "can_write_back_to_decision_draft": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "decision_source": "test",
    }


def _check_row(sample_id: str, covalent: str, restore: str) -> dict[str, str]:
    return {
        "sample_id": sample_id,
        "proposed_manual_covalent_bond_to_remove": covalent,
        "selected_bond_order_candidate": restore.split(":")[0],
        "proposed_manual_bond_order_to_restore": restore,
        "high_priority_candidate_count": "1",
        "proposal_status": "proposal_only_not_approved",
        "can_write_back_to_decision_draft": "false",
        "requires_manual_review": "true",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "proposal_check_status": "consistent_proposal_only",
        "proposal_consistent_with_decision_draft": "true",
        "proposal_consistent_with_bond_candidate_review": "true",
        "can_consider_manual_write_back": "true",
        "blocking_reasons": "",
        "recommended_next_action": "manual_confirmation_required_before_write_back",
    }


def _decision_row(sample_id: str) -> dict[str, str]:
    return {
        "sample_id": sample_id,
        "warhead_type": "toy",
        "ligand_reactive_atom_candidate": "1",
        "accepted_warhead_atoms": "1 2 3",
        "unresolved_boundary_atoms": "4",
        "proposed_covalent_bond_to_remove_candidate": "CYS:SG-1",
        "proposed_bond_order_to_restore_candidate": "",
        "proposed_atoms_requiring_charge_check": "1",
        "proposed_atoms_requiring_valence_check": "1 2 3",
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


def test_write_back_plan_is_approval_gated_and_does_not_modify_inputs(tmp_path: Path) -> None:
    samples = [
        ("BTK_C481_6DI9", "19", "17 18 19 32", "13 14 15 28 29", "CYS:SG-19", "18-19:double"),
        ("KRAS_G12C_5F2E", "29", "8 27 28 29", "7 24 25 26", "CYS:SG-29", "8-29:double"),
        ("KRAS_G12C_6OIM", "7", "4 5 6 7", "0 1 2 3 8 9", "CYS:SG-7", "6-7:double"),
    ]
    proposal_csv = tmp_path / "proposal.csv"
    check_csv = tmp_path / "check.csv"
    decision_csv = tmp_path / "decision.csv"
    output_csv = tmp_path / "plan.csv"
    output_md = tmp_path / "plan.md"
    _write_csv(proposal_csv, [_proposal_row(*sample) for sample in samples])
    _write_csv(check_csv, [_check_row(sample[0], sample[4], sample[5]) for sample in samples])
    _write_csv(decision_csv, [_decision_row(sample[0]) for sample in samples])
    proposal_hash = _sha256(proposal_csv)
    check_hash = _sha256(check_csv)
    decision_hash = _sha256(decision_csv)

    rows = build_plan_rows(proposal_csv=proposal_csv, proposal_check_csv=check_csv, decision_csv=decision_csv)
    write_csv(rows, output_csv)
    write_markdown(build_markdown(rows), output_md)

    by_sample = {row["sample_id"]: row for row in rows}
    assert set(by_sample) == {"BTK_C481_6DI9", "KRAS_G12C_5F2E", "KRAS_G12C_6OIM"}
    assert by_sample["BTK_C481_6DI9"]["proposed_manual_covalent_bond_to_remove"] == "CYS:SG-19"
    assert by_sample["BTK_C481_6DI9"]["proposed_manual_bond_order_to_restore"] == "18-19:double"
    assert by_sample["KRAS_G12C_5F2E"]["proposed_manual_covalent_bond_to_remove"] == "CYS:SG-29"
    assert by_sample["KRAS_G12C_5F2E"]["proposed_manual_bond_order_to_restore"] == "8-29:double"
    assert by_sample["KRAS_G12C_6OIM"]["proposed_manual_covalent_bond_to_remove"] == "CYS:SG-7"
    assert by_sample["KRAS_G12C_6OIM"]["proposed_manual_bond_order_to_restore"] == "6-7:double"
    assert {row["proposed_manual_boundary_resolution"] for row in rows} == {
        "reviewed_no_boundary_atoms_transferred_to_pre_reaction_transform_rule_candidate"
    }
    assert {row["write_back_allowed_by_script"] for row in rows} == {"false"}
    assert {row["explicit_human_approval_required"] for row in rows} == {"true"}
    assert {row["approval_phrase_required"] for row in rows} == {APPROVAL_PHRASE}
    assert {row["plan_status"] for row in rows} == {PLAN_STATUS}
    assert {row["proposed_pre_reaction_transform_ready"] for row in rows} == {"false"}
    assert {row["proposed_training_ready"] for row in rows} == {"false"}
    assert "Pre-Reaction Transform Manual Write-Back Plan" in output_md.read_text(encoding="utf-8")
    assert _sha256(proposal_csv) == proposal_hash
    assert _sha256(check_csv) == check_hash
    assert _sha256(decision_csv) == decision_hash
    assert not list(tmp_path.rglob("*.sdf"))
