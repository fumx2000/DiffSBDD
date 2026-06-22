from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_pre_reaction_transform_dry_run import build_markdown, build_report_rows, write_csv, write_markdown


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _draft_row(**overrides: str) -> dict[str, str]:
    row = {
        "sample_id": "toy",
        "warhead_type": "toy_michael_acceptor_draft",
        "residue_name": "CYS",
        "residue_atom": "SG",
        "ligand_reactive_atom_candidate": "3",
        "accepted_warhead_atoms": "1 2 3 4",
        "unresolved_boundary_atoms": "5 6",
        "covalent_bond_to_remove_candidate": "",
        "bond_order_to_restore_candidate": "",
        "atoms_requiring_charge_check_candidate": "3",
        "atoms_requiring_valence_check_candidate": "1 2 3 4",
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
    row.update(overrides)
    return row


def test_draft_manual_review_rows_are_blocked(tmp_path: Path) -> None:
    manual_csv = tmp_path / "manual.csv"
    output_csv = tmp_path / "dry_run.csv"
    output_md = tmp_path / "dry_run.md"
    _write_csv(manual_csv, [_draft_row()])
    input_hash = _sha256(manual_csv)

    rows = build_report_rows(manual_csv)
    write_csv(rows, output_csv)
    write_markdown(build_markdown(rows), output_md)

    row = rows[0]
    assert row["can_attempt_transform"] == "false"
    assert row["dry_run_status"] == "blocked"
    assert row["proposed_action"] == "blocked_missing_required_transform_rule"
    for reason in [
        "requires_manual_review_true",
        "review_status_not_reviewed",
        "reviewer_decision_missing",
        "covalent_bond_to_remove_candidate_missing",
        "bond_order_to_restore_candidate_missing",
        "unresolved_boundary_atoms_present",
    ]:
        assert reason in row["blocking_reasons"]
    assert _sha256(manual_csv) == input_hash
    assert not list(tmp_path.rglob("*.sdf"))


def test_missing_required_transform_rules_are_blocked(tmp_path: Path) -> None:
    manual_csv = tmp_path / "manual.csv"
    _write_csv(
        manual_csv,
        [
            _draft_row(
                requires_manual_review="false",
                review_status="reviewed",
                reviewer_decision="approved",
                unresolved_boundary_atoms="",
                covalent_bond_to_remove_candidate="",
                bond_order_to_restore_candidate="",
            )
        ],
    )

    row = build_report_rows(manual_csv)[0]

    assert row["can_attempt_transform"] == "false"
    assert row["dry_run_status"] == "blocked"
    assert "covalent_bond_to_remove_candidate_missing" in row["blocking_reasons"]
    assert "bond_order_to_restore_candidate_missing" in row["blocking_reasons"]


def test_fully_reviewed_row_can_attempt_future_transform_check(tmp_path: Path) -> None:
    manual_csv = tmp_path / "manual.csv"
    _write_csv(
        manual_csv,
        [
            _draft_row(
                requires_manual_review="false",
                review_status="reviewed",
                reviewer_decision="approved",
                unresolved_boundary_atoms="",
                covalent_bond_to_remove_candidate="CYS:SG-3",
                bond_order_to_restore_candidate="1-2:double",
            )
        ],
    )

    row = build_report_rows(manual_csv)[0]

    assert row["can_attempt_transform"] == "true"
    assert row["dry_run_status"] == "eligible_for_future_checker_only"
    assert row["proposed_action"] == "dry_run_only_ready_for_future_transform_check"
    assert row["blocking_reasons"] == ""
