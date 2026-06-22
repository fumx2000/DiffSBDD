from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_pre_reaction_transform_execution_plan import (
    APPROVAL_PHRASE,
    build_markdown,
    build_plan_rows,
    planned_output_path,
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


def _write_sdf(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "toy",
                "  test",
                "",
                "  2  1  0  0  0  0            999 V2000",
                "    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0",
                "    1.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0",
                "  1  2  1  0",
                "M  END",
                "$$$$",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _preview_row(sample_id: str, action: str, current_order: str, target_order: str) -> dict[str, str]:
    return {
        "sample_id": sample_id,
        "eligible_for_future_transform_dry_run_only": "true",
        "manual_covalent_bond_to_remove": "CYS:SG-1",
        "covalent_bond_remove_directive_status": "protein_ligand_covalent_bond_removal_directive_present",
        "ligand_reactive_atom": "1",
        "ligand_reactive_atom_present_in_sdf": "true",
        "manual_bond_order_to_restore": "0-1:double",
        "restore_bond_atom_1": "0",
        "restore_bond_atom_2": "1",
        "restore_bond_exists_in_repaired_sdf": "true",
        "current_bond_order_in_repaired_sdf": current_order,
        "target_bond_order": target_order,
        "bond_order_dry_run_action": action,
        "manual_boundary_resolution": "reviewed_no_boundary_atoms_transferred_to_pre_reaction_transform_rule_candidate",
        "manual_atoms_requiring_charge_check": "1",
        "manual_atoms_requiring_valence_check": "0 1",
        "dry_run_preview_status": "preview_passed",
        "can_build_future_transform_script": "true",
        "pre_reaction_sdf_generated": "false",
        "raw_ligand_sdf_modified": "false",
        "repaired_trial_sdf_modified": "false",
        "manifest_modified": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "blocking_reasons": "",
        "recommended_next_action": "design_guarded_pre_reaction_transform_script",
    }


def _decision_row(sample_id: str) -> dict[str, str]:
    return {
        "sample_id": sample_id,
        "warhead_type": "toy",
        "ligand_reactive_atom_candidate": "1",
        "accepted_warhead_atoms": "0 1",
        "unresolved_boundary_atoms": "2",
        "proposed_covalent_bond_to_remove_candidate": "CYS:SG-1",
        "proposed_bond_order_to_restore_candidate": "",
        "proposed_atoms_requiring_charge_check": "1",
        "proposed_atoms_requiring_valence_check": "0 1",
        "boundary_resolution_required": "true",
        "manual_covalent_bond_to_remove": "CYS:SG-1",
        "manual_bond_order_to_restore": "0-1:double",
        "manual_atoms_requiring_charge_check": "1",
        "manual_atoms_requiring_valence_check": "0 1",
        "manual_boundary_resolution": "reviewed_no_boundary_atoms_transferred_to_pre_reaction_transform_rule_candidate",
        "reviewer_decision": "approved",
        "reviewer_note": "manual_write_back_performed_after_explicit_human_approval",
        "review_status": "reviewed",
        "requires_manual_review": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "decision_source": "test",
    }


def test_execution_plan_is_safe_and_does_not_create_pre_reaction_directory(tmp_path: Path) -> None:
    preview_csv = tmp_path / "preview.csv"
    decision_csv = tmp_path / "decision.csv"
    output_csv = tmp_path / "plan.csv"
    output_md = tmp_path / "plan.md"
    samples = [
        ("BTK_C481_6DI9", "already_target_order_no_change_needed", "2", "2"),
        ("KRAS_G12C_5F2E", "already_target_order_no_change_needed", "2", "2"),
        ("KRAS_G12C_6OIM", "would_restore_bond_order_to_target", "1", "2"),
    ]
    sdf_paths: list[Path] = []
    for sample_id, _, _, _ in samples:
        sdf_path = tmp_path / f"{sample_id}_warhead_only_repaired_trial.sdf"
        _write_sdf(sdf_path)
        sdf_paths.append(sdf_path)
    _write_csv(preview_csv, [_preview_row(*sample) for sample in samples])
    _write_csv(decision_csv, [_decision_row(sample[0]) for sample in samples])
    preview_hash = _sha256(preview_csv)
    decision_hash = _sha256(decision_csv)
    sdf_hashes = {path: _sha256(path) for path in sdf_paths}

    rows = build_plan_rows(preview_csv=preview_csv, decision_csv=decision_csv, sdf_paths=sdf_paths)
    write_csv(rows, output_csv)
    write_markdown(build_markdown(rows), output_md)

    by_sample = {row["sample_id"]: row for row in rows}
    assert set(by_sample) == {"BTK_C481_6DI9", "KRAS_G12C_5F2E", "KRAS_G12C_6OIM"}
    assert all(row["source_repaired_sdf_sha256"] for row in rows)
    assert by_sample["BTK_C481_6DI9"]["planned_output_pre_reaction_sdf"] == planned_output_path("BTK_C481_6DI9")
    assert by_sample["KRAS_G12C_5F2E"]["planned_output_pre_reaction_sdf"] == planned_output_path("KRAS_G12C_5F2E")
    assert by_sample["KRAS_G12C_6OIM"]["planned_output_pre_reaction_sdf"] == planned_output_path("KRAS_G12C_6OIM")
    assert {row["execution_plan_status"] for row in rows} == {"ready_for_guarded_transform_script_design"}
    assert {row["write_sdf_allowed_by_plan"] for row in rows} == {"false"}
    assert {row["approval_phrase_required"] for row in rows} == {APPROVAL_PHRASE}
    assert by_sample["BTK_C481_6DI9"]["planned_bond_order_operation"] == (
        "validate_existing_target_bond_order_and_copy_if_future_approved"
    )
    assert by_sample["KRAS_G12C_5F2E"]["planned_bond_order_operation"] == (
        "validate_existing_target_bond_order_and_copy_if_future_approved"
    )
    assert by_sample["KRAS_G12C_6OIM"]["planned_bond_order_operation"] == (
        "set_bond_order_to_target_if_future_approved"
    )
    assert "Pre-Reaction Transform Execution Plan" in output_md.read_text(encoding="utf-8")
    assert _sha256(preview_csv) == preview_hash
    assert _sha256(decision_csv) == decision_hash
    assert {path: _sha256(path) for path in sdf_paths} == sdf_hashes
    assert not (tmp_path / "data" / "derived" / "covalent_small" / "ligands_pre_reaction").exists()
    assert len(list(tmp_path.rglob("*pre_reaction.sdf"))) == 0
