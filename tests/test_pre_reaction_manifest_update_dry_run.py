from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_pre_reaction_manifest_update_dry_run import (
    build_dry_run,
    build_markdown,
    write_markdown,
    write_proposed_rows,
    write_report,
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


def _manifest_row(sample_id: str, ligand_path: str | None = None) -> dict[str, str]:
    return {
        "sample_id": sample_id,
        "protein_pdb_path": f"protein/{sample_id}.pdb",
        "ligand_sdf_path": ligand_path or f"ligand/{sample_id}.sdf",
        "reactive_residue_chain": "A",
        "reactive_residue_id": "1",
        "reactive_residue_type": "CYS",
        "reactive_atom_name": "SG",
        "ligand_reactive_atom_id": "1",
        "warhead_type": "toy",
        "scaffold_atoms": "0",
        "linker_atoms": "1",
        "warhead_atoms": "2",
    }


def _staging_row(tmp_path: Path, sample_id: str) -> dict[str, str]:
    proposed_id = f"{sample_id}_pre_reaction"
    proposed_path = str(tmp_path / "pre_reaction_outputs" / f"{proposed_id}.sdf")
    return {
        "sample_id": sample_id,
        "proposed_manifest_sample_id": proposed_id,
        "source_sample_id": sample_id,
        "source_repaired_sdf": f"derived/{sample_id}_source.sdf",
        "output_pre_reaction_sdf": proposed_path,
        "proposed_ligand_sdf_path": proposed_path,
        "dataset_candidate_gate_status": "passed_for_dataset_candidate_not_training",
        "eligible_for_dataset_assembly_candidate_pool": "true",
        "qa_status": "generated_pre_reaction_sdf_qa_passed",
        "write_sdf_status": "written_after_explicit_human_approval",
        "execution_plan_status": "ready_for_guarded_transform_script_design",
        "planned_bond_order_operation": "validate_existing_target_bond_order_and_copy_if_future_approved",
        "source_restore_bond_order": "2",
        "output_restore_bond_order": "2",
        "target_bond_order": "2",
        "covalent_bond_removed_in_ligand_only_sdf": "true",
        "pre_reaction_ligand_graph_ready": "true",
        "can_stage_manifest_row": "true",
        "manifest_row_should_be_added_later": "true",
        "manifest_updated": "false",
        "current_manifest_contains_source_sample": "true",
        "current_manifest_contains_proposed_sample": "false",
        "proposed_manifest_record_type": "derived_pre_reaction_ligand_candidate",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "blocking_reasons": "",
        "recommended_next_action": "build_manifest_update_dry_run_not_training",
    }


def _write_inputs(
    tmp_path: Path,
    *,
    include_proposed: bool = False,
    missing_source: bool = False,
    missing_ligand_column: bool = False,
) -> tuple[Path, Path]:
    staging_csv = tmp_path / "staging.csv"
    manifest_csv = tmp_path / "manifest_real_small.csv"
    _write_csv(staging_csv, [_staging_row(tmp_path, sample_id) for sample_id in SAMPLES])
    manifest_rows = [] if missing_source else [_manifest_row(sample_id) for sample_id in SAMPLES]
    if include_proposed:
        manifest_rows.append(_manifest_row("BTK_C481_6DI9_pre_reaction"))
    if missing_ligand_column:
        manifest_rows = [
            {key: value for key, value in row.items() if key != "ligand_sdf_path"}
            for row in manifest_rows
        ]
    _write_csv(manifest_csv, manifest_rows or [_manifest_row("placeholder")])
    if missing_source:
        _write_csv(manifest_csv, [_manifest_row("unrelated")])
    return staging_csv, manifest_csv


def _mutate_csv(path: Path, sample_id: str, field: str, value: str) -> None:
    rows = list(csv.DictReader(path.open("r", encoding="utf-8", newline="")))
    for row in rows:
        if row["sample_id"] == sample_id:
            row[field] = value
    _write_csv(path, rows)


def test_manifest_update_dry_run_writes_three_proposed_rows(tmp_path: Path) -> None:
    staging_csv, manifest_csv = _write_inputs(tmp_path)
    output_report = tmp_path / "report.csv"
    output_proposed = tmp_path / "proposed_rows.csv"
    output_md = tmp_path / "summary.md"
    manifest_hash = _sha256(manifest_csv)

    rows, proposed_rows, fieldnames = build_dry_run(
        staging_plan_csv=staging_csv,
        current_manifest_csv=manifest_csv,
    )
    write_report(rows, output_report)
    write_proposed_rows(proposed_rows, fieldnames, output_proposed)
    write_markdown(build_markdown(rows), output_md)

    proposed_csv_rows = list(csv.DictReader(output_proposed.open("r", encoding="utf-8", newline="")))
    manifest_fieldnames = csv.DictReader(manifest_csv.open("r", encoding="utf-8", newline="")).fieldnames
    assert len(rows) == 3
    assert len(proposed_rows) == 3
    assert len(proposed_csv_rows) == 3
    assert fieldnames == manifest_fieldnames
    assert csv.DictReader(output_proposed.open("r", encoding="utf-8", newline="")).fieldnames == manifest_fieldnames
    assert {row["manifest_update_dry_run_status"] for row in rows} == {
        "passed_manifest_update_dry_run_not_written"
    }
    assert {row["would_add_manifest_row_later"] for row in rows} == {"true"}
    assert {row["manifest_updated"] for row in rows} == {"false"}
    assert {row["new_manifest_created"] for row in rows} == {"false"}
    assert {row["training_ready"] for row in rows} == {"false"}
    for report_row, proposed_row in zip(rows, proposed_rows):
        assert proposed_row["sample_id"] == report_row["proposed_manifest_sample_id"]
        assert proposed_row["ligand_sdf_path"] == report_row["proposed_ligand_sdf_path"]
    assert _sha256(manifest_csv) == manifest_hash
    assert "Pre-Reaction Manifest Update Dry-Run Summary" in output_md.read_text(encoding="utf-8")
    assert not (tmp_path / "new_manifest.csv").exists()
    assert not list(tmp_path.rglob("*.sdf"))


def test_existing_proposed_sample_blocks(tmp_path: Path) -> None:
    staging_csv, manifest_csv = _write_inputs(tmp_path, include_proposed=True)

    rows, proposed_rows, _ = build_dry_run(
        staging_plan_csv=staging_csv,
        current_manifest_csv=manifest_csv,
    )

    row = rows[0]
    assert row["sample_id"] == "BTK_C481_6DI9"
    assert row["manifest_update_dry_run_status"] == "blocked"
    assert row["would_add_manifest_row_later"] == "false"
    assert "current_manifest_already_contains_proposed_sample" in row["blocking_reasons"]
    assert len(proposed_rows) == 2


def test_missing_source_sample_blocks(tmp_path: Path) -> None:
    staging_csv, manifest_csv = _write_inputs(tmp_path, missing_source=True)

    rows, proposed_rows, _ = build_dry_run(
        staging_plan_csv=staging_csv,
        current_manifest_csv=manifest_csv,
    )

    assert {row["manifest_update_dry_run_status"] for row in rows} == {"blocked"}
    assert all("source_manifest_row_missing" in row["blocking_reasons"] for row in rows)
    assert proposed_rows == []


def test_missing_ligand_path_column_blocks(tmp_path: Path) -> None:
    staging_csv, manifest_csv = _write_inputs(tmp_path, missing_ligand_column=True)

    rows, proposed_rows, _ = build_dry_run(
        staging_plan_csv=staging_csv,
        current_manifest_csv=manifest_csv,
    )

    assert {row["manifest_update_dry_run_status"] for row in rows} == {"blocked"}
    assert all("manifest_ligand_path_column_missing" in row["blocking_reasons"] for row in rows)
    assert proposed_rows == []


def test_staging_not_ready_blocks(tmp_path: Path) -> None:
    staging_csv, manifest_csv = _write_inputs(tmp_path)
    _mutate_csv(staging_csv, "BTK_C481_6DI9", "can_stage_manifest_row", "false")

    rows, proposed_rows, _ = build_dry_run(
        staging_plan_csv=staging_csv,
        current_manifest_csv=manifest_csv,
    )

    row = rows[0]
    assert row["sample_id"] == "BTK_C481_6DI9"
    assert row["manifest_update_dry_run_status"] == "blocked"
    assert "can_stage_manifest_row_not_true" in row["blocking_reasons"]
    assert len(proposed_rows) == 2
