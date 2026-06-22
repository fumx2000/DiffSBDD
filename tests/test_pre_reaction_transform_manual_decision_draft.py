from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from init_pre_reaction_transform_manual_decision_draft import (
    DECISION_COLUMNS,
    build_decision_rows,
    write_decision_rows,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _readiness_row(sample_id: str) -> dict[str, str]:
    return {
        "sample_id": sample_id,
        "warhead_type": "toy_michael_acceptor_draft",
        "ligand_reactive_atom_candidate": "0",
        "accepted_warhead_atoms": "0 1 2",
        "unresolved_boundary_atoms": "3",
        "requires_manual_review": "true",
        "review_status": "draft_not_reviewed",
        "reviewer_decision": "",
        "covalent_bond_to_remove_candidate_present": "false",
        "bond_order_to_restore_candidate_present": "false",
        "can_attempt_transform": "false",
        "dry_run_status": "blocked",
        "blocking_reasons": "requires_manual_review_true",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "recommended_next_action": "manual_review_required_before_pre_reaction_transform",
    }


def _manual_row(
    sample_id: str,
    reactive_atom: str,
    warhead_atoms: str,
    boundary_atoms: str,
) -> dict[str, str]:
    return {
        "sample_id": sample_id,
        "warhead_type": "toy_michael_acceptor_draft",
        "residue_name": "CYS",
        "residue_atom": "SG",
        "ligand_reactive_atom_candidate": reactive_atom,
        "accepted_warhead_atoms": warhead_atoms,
        "unresolved_boundary_atoms": boundary_atoms,
        "covalent_bond_to_remove_candidate": "",
        "bond_order_to_restore_candidate": "",
        "atoms_requiring_charge_check_candidate": reactive_atom,
        "atoms_requiring_valence_check_candidate": warhead_atoms,
        "protonation_note": "requires_manual_review",
        "geometry_note": "post_covalent_bound_pose_coordinates_do_not_claim_free_ligand_conformer",
        "confidence_level": "draft",
        "requires_manual_review": "true",
        "review_status": "draft_not_reviewed",
        "reviewer_decision": "",
        "reviewer_note": "template_only_no_transform_performed",
        "training_ready_candidate": "false",
        "pre_reaction_graph_ready": "false",
        "rule_source": "pre_reaction_graph_design_plan",
    }


def test_pre_reaction_transform_manual_decision_draft(tmp_path: Path) -> None:
    readiness_csv = tmp_path / "readiness.csv"
    manual_csv = tmp_path / "manual.csv"
    output_csv = tmp_path / "decision.csv"
    samples = [
        ("BTK_C481_6DI9", "19", "17 18 19 32", "13 14 15 28 29", "CYS:SG-19"),
        ("KRAS_G12C_5F2E", "29", "8 27 28 29", "7 24 25 26", "CYS:SG-29"),
        ("KRAS_G12C_6OIM", "7", "4 5 6 7", "0 1 2 3 8 9", "CYS:SG-7"),
    ]
    _write_csv(readiness_csv, [_readiness_row(sample[0]) for sample in samples])
    _write_csv(manual_csv, [_manual_row(*sample[:4]) for sample in samples])
    readiness_hash = _sha256(readiness_csv)
    manual_hash = _sha256(manual_csv)

    rows = build_decision_rows(readiness_csv=readiness_csv, manual_review_csv=manual_csv)
    write_decision_rows(rows, output_csv)

    written_rows = list(csv.DictReader(output_csv.open(newline="", encoding="utf-8")))
    assert list(written_rows[0]) == DECISION_COLUMNS
    by_sample = {row["sample_id"]: row for row in written_rows}
    assert set(by_sample) == {sample[0] for sample in samples}
    for sample_id, _, _, _, expected_bond in samples:
        row = by_sample[sample_id]
        assert row["proposed_covalent_bond_to_remove_candidate"] == expected_bond
        assert row["proposed_bond_order_to_restore_candidate"] == ""
        assert row["boundary_resolution_required"] == "true"
        assert row["review_status"] == "draft_not_reviewed"
        assert row["requires_manual_review"] == "true"
        assert row["pre_reaction_transform_ready"] == "false"
        assert row["training_ready"] == "false"
        assert "no_pre_reaction_sdf_generated" in row["reviewer_note"]
        assert "not_training_ready" in row["reviewer_note"]
    assert _sha256(readiness_csv) == readiness_hash
    assert _sha256(manual_csv) == manual_hash
    assert not list(tmp_path.rglob("*.sdf"))
