from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from summarize_pre_reaction_transform_readiness import build_markdown, build_summary_rows, write_csv, write_markdown


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _manual_row(sample_id: str, reactive_atom: str, warhead_atoms: str, boundary_atoms: str) -> dict[str, str]:
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


def _dry_row(sample_id: str, reactive_atom: str, warhead_atoms: str, boundary_atoms: str) -> dict[str, str]:
    return {
        "sample_id": sample_id,
        "warhead_type": "toy_michael_acceptor_draft",
        "ligand_reactive_atom_candidate": reactive_atom,
        "accepted_warhead_atoms": warhead_atoms,
        "unresolved_boundary_atoms": boundary_atoms,
        "covalent_bond_to_remove_candidate": "",
        "bond_order_to_restore_candidate": "",
        "atoms_requiring_charge_check_candidate": reactive_atom,
        "atoms_requiring_valence_check_candidate": warhead_atoms,
        "requires_manual_review": "true",
        "review_status": "draft_not_reviewed",
        "reviewer_decision": "",
        "training_ready_candidate": "false",
        "pre_reaction_graph_ready": "false",
        "can_attempt_transform": "false",
        "proposed_action": "blocked_missing_required_transform_rule",
        "dry_run_status": "blocked",
        "blocking_reasons": (
            "requires_manual_review_true;review_status_not_reviewed;reviewer_decision_missing;"
            "covalent_bond_to_remove_candidate_missing;bond_order_to_restore_candidate_missing;"
            "unresolved_boundary_atoms_present"
        ),
        "recommended_next_action": "manual_review_required_before_pre_reaction_transform",
    }


def test_pre_reaction_transform_readiness_summary_blocks_draft_rows(tmp_path: Path) -> None:
    manual_csv = tmp_path / "manual.csv"
    dry_csv = tmp_path / "dry.csv"
    output_csv = tmp_path / "summary.csv"
    output_md = tmp_path / "summary.md"
    samples = [
        ("BTK_C481_6DI9", "19", "17 18 19 32", "13 14 15 28 29"),
        ("KRAS_G12C_5F2E", "29", "8 27 28 29", "7 24 25 26"),
        ("KRAS_G12C_6OIM", "7", "4 5 6 7", "0 1 2 3 8 9"),
    ]
    _write_csv(manual_csv, [_manual_row(*sample) for sample in samples])
    _write_csv(dry_csv, [_dry_row(*sample) for sample in samples])
    manual_hash = _sha256(manual_csv)
    dry_hash = _sha256(dry_csv)

    rows = build_summary_rows(manual_review_csv=manual_csv, dry_run_csv=dry_csv)
    write_csv(rows, output_csv)
    write_markdown(build_markdown(rows), output_md)

    assert {row["sample_id"] for row in rows} == {sample[0] for sample in samples}
    assert {row["pre_reaction_transform_ready"] for row in rows} == {"false"}
    assert {row["training_ready"] for row in rows} == {"false"}
    assert {row["can_attempt_transform"] for row in rows} == {"false"}
    assert {row["dry_run_status"] for row in rows} == {"blocked"}
    for row in rows:
        next_action = row["recommended_next_action"]
        assert "manual_review_required_before_pre_reaction_transform" in next_action
        assert "add_covalent_bond_to_remove_candidate_after_manual_review" in next_action
        assert "add_bond_order_to_restore_candidate_after_manual_review" in next_action
        assert "resolve_boundary_atoms_before_transform" in next_action
    assert _sha256(manual_csv) == manual_hash
    assert _sha256(dry_csv) == dry_hash
    assert not list(tmp_path.rglob("*.sdf"))
