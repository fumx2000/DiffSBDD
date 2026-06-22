from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_pre_reaction_transform_dry_run_preview import (
    build_markdown,
    build_preview_rows,
    parse_bond_order_restore,
    parse_covalent_bond_remove,
    parse_v2000_sdf,
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


def _write_toy_sdf(path: Path, *, include_restore_bond: bool = True, restore_order: str = "2") -> None:
    bond_lines = [
        "  1  2  1  0",
        f"  2  3  {restore_order}  0",
    ]
    if include_restore_bond:
        bond_lines.append("  3  4  1  0")
    else:
        bond_lines.append("  1  4  1  0")
    path.write_text(
        "\n".join(
            [
                "toy",
                "  test",
                "",
                "  4  3  0  0  0  0            999 V2000",
                "    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0",
                "    1.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0",
                "    2.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0",
                "    3.0000    0.0000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0",
                *bond_lines,
                "M  END",
                "$$$$",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _decision_row(sample_id: str, *, restore: str = "1-2:double") -> dict[str, str]:
    return {
        "sample_id": sample_id,
        "warhead_type": "toy",
        "ligand_reactive_atom_candidate": "2",
        "accepted_warhead_atoms": "1 2 3",
        "unresolved_boundary_atoms": "4",
        "proposed_covalent_bond_to_remove_candidate": "CYS:SG-2",
        "proposed_bond_order_to_restore_candidate": "",
        "proposed_atoms_requiring_charge_check": "2",
        "proposed_atoms_requiring_valence_check": "1 2 3",
        "boundary_resolution_required": "true",
        "manual_covalent_bond_to_remove": "CYS:SG-2",
        "manual_bond_order_to_restore": restore,
        "manual_atoms_requiring_charge_check": "2",
        "manual_atoms_requiring_valence_check": "1 2 3",
        "manual_boundary_resolution": "reviewed_no_boundary_atoms_transferred_to_pre_reaction_transform_rule_candidate",
        "reviewer_decision": "approved",
        "reviewer_note": "manual_write_back_performed_after_explicit_human_approval",
        "review_status": "reviewed",
        "requires_manual_review": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "decision_source": "test",
    }


def _readiness_row(sample_id: str) -> dict[str, str]:
    return {
        "sample_id": sample_id,
        "manual_covalent_bond_to_remove": "CYS:SG-2",
        "manual_bond_order_to_restore": "1-2:double",
        "manual_boundary_resolution": "reviewed_no_boundary_atoms_transferred_to_pre_reaction_transform_rule_candidate",
        "manual_atoms_requiring_charge_check": "2",
        "manual_atoms_requiring_valence_check": "1 2 3",
        "reviewer_decision": "approved",
        "review_status": "reviewed",
        "requires_manual_review": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "post_write_back_check_status": "eligible_for_future_transform_dry_run_only",
        "eligible_for_future_transform_dry_run_only": "true",
        "blocking_reasons": "",
        "recommended_next_action": "build_pre_reaction_transform_dry_run_next",
    }


def test_directive_parsers_and_v2000_parser(tmp_path: Path) -> None:
    sdf_path = tmp_path / "toy_sample_warhead_only_repaired_trial.sdf"
    _write_toy_sdf(sdf_path, restore_order="2")

    assert parse_covalent_bond_remove("CYS:SG-19") == 19
    assert parse_bond_order_restore("18-19:double") == (18, 19, "2")
    atom_count, bonds = parse_v2000_sdf(sdf_path)
    assert atom_count == 4
    assert bonds[(1, 2)] == "2"


def test_preview_passes_when_bond_exists_and_already_target_order(tmp_path: Path) -> None:
    sample_id = "toy_sample"
    sdf_path = tmp_path / f"{sample_id}_warhead_only_repaired_trial.sdf"
    decision_csv = tmp_path / "decision.csv"
    readiness_csv = tmp_path / "readiness.csv"
    output_csv = tmp_path / "report.csv"
    output_md = tmp_path / "summary.md"
    _write_toy_sdf(sdf_path, restore_order="2")
    _write_csv(decision_csv, [_decision_row(sample_id, restore="1-2:double")])
    _write_csv(readiness_csv, [_readiness_row(sample_id)])
    decision_hash = _sha256(decision_csv)
    readiness_hash = _sha256(readiness_csv)
    sdf_hash = _sha256(sdf_path)

    rows = build_preview_rows(decision_csv=decision_csv, readiness_csv=readiness_csv, sdf_paths=[sdf_path])
    write_csv(rows, output_csv)
    write_markdown(build_markdown(rows), output_md)

    row = rows[0]
    assert row["ligand_reactive_atom_present_in_sdf"] == "true"
    assert row["restore_bond_exists_in_repaired_sdf"] == "true"
    assert row["dry_run_preview_status"] == "preview_passed"
    assert row["can_build_future_transform_script"] == "true"
    assert row["current_bond_order_in_repaired_sdf"] == "2"
    assert row["bond_order_dry_run_action"] == "already_target_order_no_change_needed"
    assert row["pre_reaction_sdf_generated"] == "false"
    assert row["training_ready"] == "false"
    assert "Pre-Reaction Transform Dry-Run Preview Summary" in output_md.read_text(encoding="utf-8")
    assert _sha256(decision_csv) == decision_hash
    assert _sha256(readiness_csv) == readiness_hash
    assert _sha256(sdf_path) == sdf_hash
    assert len(list(tmp_path.rglob("*.sdf"))) == 1


def test_preview_reports_would_restore_when_current_order_differs(tmp_path: Path) -> None:
    sample_id = "toy_sample"
    sdf_path = tmp_path / f"{sample_id}_warhead_only_repaired_trial.sdf"
    decision_csv = tmp_path / "decision.csv"
    readiness_csv = tmp_path / "readiness.csv"
    _write_toy_sdf(sdf_path, restore_order="1")
    _write_csv(decision_csv, [_decision_row(sample_id, restore="1-2:double")])
    _write_csv(readiness_csv, [_readiness_row(sample_id)])

    row = build_preview_rows(decision_csv=decision_csv, readiness_csv=readiness_csv, sdf_paths=[sdf_path])[0]

    assert row["current_bond_order_in_repaired_sdf"] == "1"
    assert row["target_bond_order"] == "2"
    assert row["bond_order_dry_run_action"] == "would_restore_bond_order_to_target"
    assert row["dry_run_preview_status"] == "preview_passed"


def test_missing_restore_bond_blocks_preview(tmp_path: Path) -> None:
    sample_id = "toy_sample"
    sdf_path = tmp_path / f"{sample_id}_warhead_only_repaired_trial.sdf"
    decision_csv = tmp_path / "decision.csv"
    readiness_csv = tmp_path / "readiness.csv"
    _write_toy_sdf(sdf_path, include_restore_bond=False)
    _write_csv(decision_csv, [_decision_row(sample_id, restore="2-3:double")])
    _write_csv(readiness_csv, [_readiness_row(sample_id)])

    row = build_preview_rows(decision_csv=decision_csv, readiness_csv=readiness_csv, sdf_paths=[sdf_path])[0]

    assert row["restore_bond_exists_in_repaired_sdf"] == "false"
    assert row["bond_order_dry_run_action"] == "blocked_missing_restore_bond"
    assert row["dry_run_preview_status"] == "blocked"
    assert "restore_bond_missing_in_repaired_sdf" in row["blocking_reasons"]
