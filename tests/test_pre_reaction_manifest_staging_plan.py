from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_pre_reaction_manifest_staging_plan import (
    build_markdown,
    build_staging_rows,
    write_csv,
    write_markdown,
)


SAMPLES = ["BTK_C481_6DI9", "KRAS_G12C_5F2E", "KRAS_G12C_6OIM"]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _artifact_path(tmp_path: Path, sample_id: str) -> str:
    path = tmp_path / "artifacts" / f"{sample_id}_pre_reaction_artifact"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("derived artifact placeholder\n", encoding="utf-8")
    return str(path)


def _gate_row(tmp_path: Path, sample_id: str) -> dict[str, str]:
    output_path = _artifact_path(tmp_path, sample_id)
    return {
        "sample_id": sample_id,
        "output_pre_reaction_sdf": output_path,
        "qa_status": "generated_pre_reaction_sdf_qa_passed",
        "source_restore_bond_order": "2",
        "output_restore_bond_order": "2",
        "target_bond_order": "2",
        "bond_block_change_count": "0",
        "allowed_bond_order_change_only": "true",
        "atom_block_identical": "true",
        "coordinate_block_identical": "true",
        "source_repaired_sdf_sha256_matches_report": "true",
        "output_pre_reaction_sdf_sha256_matches_report": "true",
        "write_sdf_status": "written_after_explicit_human_approval",
        "execution_plan_status": "ready_for_guarded_transform_script_design",
        "dataset_candidate_gate_status": "passed_for_dataset_candidate_not_training",
        "eligible_for_dataset_assembly_candidate_pool": "true",
        "pre_reaction_sdf_qa_passed": "true",
        "safe_as_derived_pre_reaction_artifact": "true",
        "can_update_manifest_later": "true",
        "manifest_updated": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "blocking_reasons": "",
        "recommended_next_action": "build_manifest_staging_plan_not_training",
    }


def _qa_row(gate: dict[str, str]) -> dict[str, str]:
    return {
        "sample_id": gate["sample_id"],
        "source_repaired_sdf": f"derived/{gate['sample_id']}_source.sdf",
        "output_pre_reaction_sdf": gate["output_pre_reaction_sdf"],
        "source_repaired_sdf_exists": "true",
        "output_pre_reaction_sdf_exists": "true",
        "source_repaired_sdf_sha256_matches_report": "true",
        "output_pre_reaction_sdf_sha256_matches_report": "true",
        "atom_count_source": "3",
        "atom_count_output": "3",
        "bond_count_source": "2",
        "bond_count_output": "2",
        "atom_block_identical": "true",
        "coordinate_block_identical": "true",
        "bond_block_change_count": "0",
        "allowed_bond_order_change_only": "true",
        "restore_bond_atom_1": "0",
        "restore_bond_atom_2": "1",
        "source_restore_bond_order": gate["source_restore_bond_order"],
        "output_restore_bond_order": gate["output_restore_bond_order"],
        "target_bond_order": gate["target_bond_order"],
        "planned_bond_order_operation": "validate_existing_target_bond_order_and_copy_if_future_approved",
        "expected_change_description": "source_copied_because_target_bond_order_already_present",
        "qa_status": gate["qa_status"],
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "blocking_reasons": "",
        "recommended_next_action": "build_pre_reaction_training_readiness_gate",
    }


def _write_row(sample_id: str, output_path: str) -> dict[str, str]:
    return {
        "sample_id": sample_id,
        "source_repaired_sdf": f"derived/{sample_id}_source.sdf",
        "output_pre_reaction_sdf": output_path,
        "write_sdf_status": "written_after_explicit_human_approval",
    }


def _execution_row(sample_id: str) -> dict[str, str]:
    return {
        "sample_id": sample_id,
        "execution_plan_status": "ready_for_guarded_transform_script_design",
        "planned_bond_order_operation": "validate_existing_target_bond_order_and_copy_if_future_approved",
    }


def _manifest_row(sample_id: str) -> dict[str, str]:
    return {
        "sample_id": sample_id,
        "protein_pdb_path": f"protein/{sample_id}.pdb",
        "ligand_sdf_path": f"ligand/{sample_id}.sdf",
    }


def _write_inputs(tmp_path: Path, *, include_proposed: bool = False) -> tuple[Path, Path, Path, Path, Path]:
    gate_rows = [_gate_row(tmp_path, sample_id) for sample_id in SAMPLES]
    qa_rows = [_qa_row(row) for row in gate_rows]
    write_rows = [_write_row(row["sample_id"], row["output_pre_reaction_sdf"]) for row in gate_rows]
    execution_rows = [_execution_row(sample_id) for sample_id in SAMPLES]
    manifest_rows = [_manifest_row(sample_id) for sample_id in SAMPLES]
    if include_proposed:
        manifest_rows.append(_manifest_row("BTK_C481_6DI9_pre_reaction"))
    gate_csv = tmp_path / "gate.csv"
    qa_csv = tmp_path / "qa.csv"
    write_csv_path = tmp_path / "write.csv"
    execution_csv = tmp_path / "execution.csv"
    manifest_csv = tmp_path / "manifest_real_small.csv"
    _write_csv(gate_csv, gate_rows)
    _write_csv(qa_csv, qa_rows)
    _write_csv(write_csv_path, write_rows)
    _write_csv(execution_csv, execution_rows)
    _write_csv(manifest_csv, manifest_rows)
    return gate_csv, qa_csv, write_csv_path, execution_csv, manifest_csv


def _mutate_csv(path: Path, sample_id: str, field: str, value: str) -> None:
    rows = list(csv.DictReader(path.open("r", encoding="utf-8", newline="")))
    for row in rows:
        if row["sample_id"] == sample_id:
            row[field] = value
    _write_csv(path, rows)


def test_manifest_staging_plan_passes_three_samples(tmp_path: Path) -> None:
    gate_csv, qa_csv, write_csv_path, execution_csv, manifest_csv = _write_inputs(tmp_path)
    output_csv = tmp_path / "staging.csv"
    output_md = tmp_path / "staging.md"
    manifest_hash = _sha256(manifest_csv)

    rows = build_staging_rows(
        gate_report_csv=gate_csv,
        qa_report_csv=qa_csv,
        write_sdf_report_csv=write_csv_path,
        execution_plan_csv=execution_csv,
        current_manifest_csv=manifest_csv,
    )
    write_csv(rows, output_csv)
    write_markdown(build_markdown(rows), output_md)

    assert {row["sample_id"] for row in rows} == set(SAMPLES)
    assert {row["proposed_manifest_sample_id"] for row in rows} == {
        "BTK_C481_6DI9_pre_reaction",
        "KRAS_G12C_5F2E_pre_reaction",
        "KRAS_G12C_6OIM_pre_reaction",
    }
    assert all(row["proposed_ligand_sdf_path"] == row["output_pre_reaction_sdf"] for row in rows)
    assert {row["can_stage_manifest_row"] for row in rows} == {"true"}
    assert {row["manifest_row_should_be_added_later"] for row in rows} == {"true"}
    assert {row["manifest_updated"] for row in rows} == {"false"}
    assert {row["training_ready"] for row in rows} == {"false"}
    assert {row["current_manifest_contains_proposed_sample"] for row in rows} == {"false"}
    assert "Pre-Reaction Manifest Staging Plan" in output_md.read_text(encoding="utf-8")
    assert _sha256(manifest_csv) == manifest_hash
    assert not (tmp_path / "new_manifest.csv").exists()
    assert not list(tmp_path.rglob("*.sdf"))


def test_existing_proposed_manifest_sample_blocks(tmp_path: Path) -> None:
    gate_csv, qa_csv, write_csv_path, execution_csv, manifest_csv = _write_inputs(
        tmp_path, include_proposed=True
    )

    row = build_staging_rows(
        gate_report_csv=gate_csv,
        qa_report_csv=qa_csv,
        write_sdf_report_csv=write_csv_path,
        execution_plan_csv=execution_csv,
        current_manifest_csv=manifest_csv,
    )[0]

    assert row["sample_id"] == "BTK_C481_6DI9"
    assert row["can_stage_manifest_row"] == "false"
    assert row["current_manifest_contains_proposed_sample"] == "true"
    assert "current_manifest_already_contains_proposed_sample" in row["blocking_reasons"]


def test_gate_status_not_passed_blocks(tmp_path: Path) -> None:
    gate_csv, qa_csv, write_csv_path, execution_csv, manifest_csv = _write_inputs(tmp_path)
    _mutate_csv(gate_csv, "BTK_C481_6DI9", "dataset_candidate_gate_status", "blocked")

    row = build_staging_rows(
        gate_report_csv=gate_csv,
        qa_report_csv=qa_csv,
        write_sdf_report_csv=write_csv_path,
        execution_plan_csv=execution_csv,
        current_manifest_csv=manifest_csv,
    )[0]

    assert row["can_stage_manifest_row"] == "false"
    assert "dataset_candidate_gate_status_not_passed" in row["blocking_reasons"]


def test_missing_output_path_blocks(tmp_path: Path) -> None:
    gate_csv, qa_csv, write_csv_path, execution_csv, manifest_csv = _write_inputs(tmp_path)
    _mutate_csv(gate_csv, "BTK_C481_6DI9", "output_pre_reaction_sdf", "")

    row = build_staging_rows(
        gate_report_csv=gate_csv,
        qa_report_csv=qa_csv,
        write_sdf_report_csv=write_csv_path,
        execution_plan_csv=execution_csv,
        current_manifest_csv=manifest_csv,
    )[0]

    assert row["can_stage_manifest_row"] == "false"
    assert "output_pre_reaction_sdf_missing_or_empty" in row["blocking_reasons"]


def test_restore_bond_order_mismatch_blocks(tmp_path: Path) -> None:
    gate_csv, qa_csv, write_csv_path, execution_csv, manifest_csv = _write_inputs(tmp_path)
    _mutate_csv(qa_csv, "BTK_C481_6DI9", "output_restore_bond_order", "1")

    row = build_staging_rows(
        gate_report_csv=gate_csv,
        qa_report_csv=qa_csv,
        write_sdf_report_csv=write_csv_path,
        execution_plan_csv=execution_csv,
        current_manifest_csv=manifest_csv,
    )[0]

    assert row["can_stage_manifest_row"] == "false"
    assert "output_restore_bond_order_not_target" in row["blocking_reasons"]
