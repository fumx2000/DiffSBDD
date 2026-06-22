from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_pre_reaction_transform_manual_write_back_readiness import (
    ELIGIBLE_STATUS,
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


def _decision_row(
    sample_id: str,
    covalent: str,
    restore: str,
    charge: str,
    valence: str,
    **overrides: str,
) -> dict[str, str]:
    row = {
        "sample_id": sample_id,
        "warhead_type": "toy",
        "ligand_reactive_atom_candidate": charge,
        "accepted_warhead_atoms": valence,
        "unresolved_boundary_atoms": "boundary",
        "proposed_covalent_bond_to_remove_candidate": covalent,
        "proposed_bond_order_to_restore_candidate": "",
        "proposed_atoms_requiring_charge_check": charge,
        "proposed_atoms_requiring_valence_check": valence,
        "boundary_resolution_required": "true",
        "manual_covalent_bond_to_remove": covalent,
        "manual_bond_order_to_restore": restore,
        "manual_atoms_requiring_charge_check": charge,
        "manual_atoms_requiring_valence_check": valence,
        "manual_boundary_resolution": "reviewed_no_boundary_atoms_transferred_to_pre_reaction_transform_rule_candidate",
        "reviewer_decision": "approved",
        "reviewer_note": "manual_write_back_performed_after_explicit_human_approval",
        "review_status": "reviewed",
        "requires_manual_review": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "decision_source": "test",
    }
    row.update(overrides)
    return row


def test_post_write_back_readiness_accepts_manual_fields_without_proposed_restore(tmp_path: Path) -> None:
    decision_csv = tmp_path / "decision.csv"
    output_csv = tmp_path / "report.csv"
    output_md = tmp_path / "summary.md"
    _write_csv(
        decision_csv,
        [
            _decision_row("BTK_C481_6DI9", "CYS:SG-19", "18-19:double", "19", "17 18 19 32"),
            _decision_row("KRAS_G12C_5F2E", "CYS:SG-29", "8-29:double", "29", "8 27 28 29"),
            _decision_row("KRAS_G12C_6OIM", "CYS:SG-7", "6-7:double", "7", "4 5 6 7"),
        ],
    )
    decision_hash = _sha256(decision_csv)

    rows = build_report_rows(decision_csv)
    write_csv(rows, output_csv)
    write_markdown(build_markdown(rows), output_md)

    assert len(rows) == 3
    assert {row["post_write_back_check_status"] for row in rows} == {ELIGIBLE_STATUS}
    assert {row["eligible_for_future_transform_dry_run_only"] for row in rows} == {"true"}
    assert {row["pre_reaction_transform_ready"] for row in rows} == {"false"}
    assert {row["training_ready"] for row in rows} == {"false"}
    assert {row["blocking_reasons"] for row in rows} == {""}
    assert {row["recommended_next_action"] for row in rows} == {"build_pre_reaction_transform_dry_run_next"}
    assert "Pre-Reaction Transform Manual Write-Back Readiness Summary" in output_md.read_text(encoding="utf-8")
    assert _sha256(decision_csv) == decision_hash
    assert not list(tmp_path.rglob("*.sdf"))


def test_missing_manual_bond_order_blocks_readiness(tmp_path: Path) -> None:
    decision_csv = tmp_path / "decision.csv"
    _write_csv(
        decision_csv,
        [_decision_row("toy", "CYS:SG-3", "", "3", "1 2 3")],
    )

    row = build_report_rows(decision_csv)[0]

    assert row["post_write_back_check_status"] == "blocked"
    assert row["eligible_for_future_transform_dry_run_only"] == "false"
    assert "manual_bond_order_to_restore_missing" in row["blocking_reasons"]


def test_non_approved_reviewer_decision_blocks_readiness(tmp_path: Path) -> None:
    decision_csv = tmp_path / "decision.csv"
    _write_csv(
        decision_csv,
        [_decision_row("toy", "CYS:SG-3", "1-2:double", "3", "1 2 3", reviewer_decision="pending")],
    )

    row = build_report_rows(decision_csv)[0]

    assert row["post_write_back_check_status"] == "blocked"
    assert row["eligible_for_future_transform_dry_run_only"] == "false"
    assert "reviewer_decision_not_approved" in row["blocking_reasons"]
