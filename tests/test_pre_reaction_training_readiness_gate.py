from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_pre_reaction_training_readiness_gate import (
    build_gate_rows,
    build_markdown,
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


def _qa_row(tmp_path: Path, sample_id: str) -> dict[str, str]:
    output_path = tmp_path / f"{sample_id}_pre_reaction_artifact"
    output_path.write_text("placeholder derived pre-reaction artifact path\n", encoding="utf-8")
    return {
        "sample_id": sample_id,
        "source_repaired_sdf": f"derived/{sample_id}_source.sdf",
        "output_pre_reaction_sdf": str(output_path),
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
        "source_restore_bond_order": "2",
        "output_restore_bond_order": "2",
        "target_bond_order": "2",
        "planned_bond_order_operation": "validate_existing_target_bond_order_and_copy_if_future_approved",
        "expected_change_description": "source_copied_because_target_bond_order_already_present",
        "qa_status": "generated_pre_reaction_sdf_qa_passed",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "blocking_reasons": "",
        "recommended_next_action": "build_pre_reaction_training_readiness_gate",
    }


def _write_row(sample_id: str) -> dict[str, str]:
    return {
        "sample_id": sample_id,
        "write_sdf_status": "written_after_explicit_human_approval",
        "output_pre_reaction_sdf": f"derived/{sample_id}_pre_reaction.sdf",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
    }


def _execution_row(sample_id: str) -> dict[str, str]:
    return {
        "sample_id": sample_id,
        "execution_plan_status": "ready_for_guarded_transform_script_design",
    }


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    qa_csv = tmp_path / "qa.csv"
    write_csv_path = tmp_path / "write.csv"
    execution_csv = tmp_path / "execution.csv"
    manifest = tmp_path / "manifest_real_small.csv"
    _write_csv(qa_csv, [_qa_row(tmp_path, sample_id) for sample_id in SAMPLES])
    _write_csv(write_csv_path, [_write_row(sample_id) for sample_id in SAMPLES])
    _write_csv(execution_csv, [_execution_row(sample_id) for sample_id in SAMPLES])
    manifest.write_text("sample_id\nexisting\n", encoding="utf-8")
    return qa_csv, write_csv_path, execution_csv, manifest


def _mutate_csv(path: Path, sample_id: str, field: str, value: str) -> None:
    rows = list(csv.DictReader(path.open("r", encoding="utf-8", newline="")))
    for row in rows:
        if row["sample_id"] == sample_id:
            row[field] = value
    _write_csv(path, rows)


def test_training_readiness_gate_passes_three_samples(tmp_path: Path) -> None:
    qa_csv, write_csv_path, execution_csv, manifest = _write_inputs(tmp_path)
    output_csv = tmp_path / "gate.csv"
    output_md = tmp_path / "gate.md"
    qa_hash = _sha256(qa_csv)
    write_hash = _sha256(write_csv_path)
    execution_hash = _sha256(execution_csv)
    manifest_hash = _sha256(manifest)

    rows = build_gate_rows(
        qa_report_csv=qa_csv,
        write_sdf_report_csv=write_csv_path,
        execution_plan_csv=execution_csv,
    )
    write_csv(rows, output_csv)
    write_markdown(build_markdown(rows), output_md)

    assert {row["sample_id"] for row in rows} == set(SAMPLES)
    assert {row["dataset_candidate_gate_status"] for row in rows} == {
        "passed_for_dataset_candidate_not_training"
    }
    assert {row["eligible_for_dataset_assembly_candidate_pool"] for row in rows} == {"true"}
    assert {row["pre_reaction_sdf_qa_passed"] for row in rows} == {"true"}
    assert {row["safe_as_derived_pre_reaction_artifact"] for row in rows} == {"true"}
    assert {row["can_update_manifest_later"] for row in rows} == {"true"}
    assert {row["manifest_updated"] for row in rows} == {"false"}
    assert {row["pre_reaction_transform_ready"] for row in rows} == {"false"}
    assert {row["training_ready"] for row in rows} == {"false"}
    assert "Pre-Reaction Training-Readiness Gate Summary" in output_md.read_text(encoding="utf-8")
    assert _sha256(qa_csv) == qa_hash
    assert _sha256(write_csv_path) == write_hash
    assert _sha256(execution_csv) == execution_hash
    assert _sha256(manifest) == manifest_hash
    assert not list(tmp_path.rglob("*.sdf"))


def test_qa_status_not_passed_blocks(tmp_path: Path) -> None:
    qa_csv, write_csv_path, execution_csv, _ = _write_inputs(tmp_path)
    _mutate_csv(qa_csv, "BTK_C481_6DI9", "qa_status", "blocked")

    row = build_gate_rows(
        qa_report_csv=qa_csv,
        write_sdf_report_csv=write_csv_path,
        execution_plan_csv=execution_csv,
    )[0]

    assert row["dataset_candidate_gate_status"] == "blocked"
    assert row["eligible_for_dataset_assembly_candidate_pool"] == "false"
    assert "qa_status_not_passed" in row["blocking_reasons"]


def test_output_restore_bond_order_mismatch_blocks(tmp_path: Path) -> None:
    qa_csv, write_csv_path, execution_csv, _ = _write_inputs(tmp_path)
    _mutate_csv(qa_csv, "BTK_C481_6DI9", "output_restore_bond_order", "1")

    row = build_gate_rows(
        qa_report_csv=qa_csv,
        write_sdf_report_csv=write_csv_path,
        execution_plan_csv=execution_csv,
    )[0]

    assert row["dataset_candidate_gate_status"] == "blocked"
    assert "output_restore_bond_order_not_target" in row["blocking_reasons"]


def test_atom_block_not_identical_blocks(tmp_path: Path) -> None:
    qa_csv, write_csv_path, execution_csv, _ = _write_inputs(tmp_path)
    _mutate_csv(qa_csv, "BTK_C481_6DI9", "atom_block_identical", "false")

    row = build_gate_rows(
        qa_report_csv=qa_csv,
        write_sdf_report_csv=write_csv_path,
        execution_plan_csv=execution_csv,
    )[0]

    assert row["dataset_candidate_gate_status"] == "blocked"
    assert "atom_block_not_identical" in row["blocking_reasons"]


def test_coordinate_block_not_identical_blocks(tmp_path: Path) -> None:
    qa_csv, write_csv_path, execution_csv, _ = _write_inputs(tmp_path)
    _mutate_csv(qa_csv, "BTK_C481_6DI9", "coordinate_block_identical", "false")

    row = build_gate_rows(
        qa_report_csv=qa_csv,
        write_sdf_report_csv=write_csv_path,
        execution_plan_csv=execution_csv,
    )[0]

    assert row["dataset_candidate_gate_status"] == "blocked"
    assert "coordinate_block_not_identical" in row["blocking_reasons"]


def test_hash_mismatch_blocks(tmp_path: Path) -> None:
    qa_csv, write_csv_path, execution_csv, _ = _write_inputs(tmp_path)
    _mutate_csv(qa_csv, "BTK_C481_6DI9", "output_pre_reaction_sdf_sha256_matches_report", "false")

    row = build_gate_rows(
        qa_report_csv=qa_csv,
        write_sdf_report_csv=write_csv_path,
        execution_plan_csv=execution_csv,
    )[0]

    assert row["dataset_candidate_gate_status"] == "blocked"
    assert "output_pre_reaction_sdf_sha256_mismatch" in row["blocking_reasons"]
