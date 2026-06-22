from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_generated_pre_reaction_sdf_qa import (
    build_markdown,
    build_report_rows,
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


def _write_sdf(path: Path, *, atom_x: str = "1.0000", bond_order: str = "1", extra_bond_order: str = "1") -> None:
    path.write_text(
        "\n".join(
            [
                "toy",
                "  test",
                "",
                "  3  2  0  0  0  0            999 V2000",
                "    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0",
                f"    {atom_x:>6}    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0",
                "    2.0000    0.0000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0",
                f"  1  2  {bond_order}  0",
                f"  2  3  {extra_bond_order}  0",
                "M  END",
                "$$$$",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_report_and_plan(
    tmp_path: Path,
    *,
    source: Path,
    output: Path,
    operation: str,
    target_order: str = "2",
) -> tuple[Path, Path]:
    write_report_csv = tmp_path / "write_report.csv"
    execution_plan_csv = tmp_path / "execution_plan.csv"
    common = {
        "sample_id": "toy",
        "source_repaired_sdf": str(source),
        "output_pre_reaction_sdf": str(output),
        "planned_bond_order_operation": operation,
        "restore_bond_atom_1": "0",
        "restore_bond_atom_2": "1",
        "target_bond_order": target_order,
    }
    _write_csv(
        write_report_csv,
        [
            {
                **common,
                "mode": "write_sdf",
                "approval_phrase_used": "APPROVE_PRE_REACTION_TRANSFORM_SDF_STEP_8P",
                "override_plan_write_lock_used": "true",
                "source_repaired_sdf_sha256_before": _sha256(source),
                "source_repaired_sdf_sha256_after": _sha256(source),
                "source_repaired_sdf_sha256_matches": "true",
                "planned_output_pre_reaction_sdf": str(output),
                "output_pre_reaction_sdf_sha256": _sha256(output),
                "planned_output_parent": str(output.parent),
                "execution_plan_status": "ready_for_guarded_transform_script_design",
                "original_bond_order_in_source_sdf": "1",
                "final_bond_order_in_output_sdf": target_order,
                "write_sdf_status": "written_after_explicit_human_approval",
                "dry_run_status": "",
                "can_attempt_future_write_sdf_after_explicit_approval": "",
                "write_sdf_attempted": "true",
                "pre_reaction_sdf_generated": "true",
                "ligands_pre_reaction_dir_created": "true",
                "raw_ligand_sdf_modified": "false",
                "repaired_trial_sdf_modified": "false",
                "manifest_modified": "false",
                "pre_reaction_transform_ready": "false",
                "training_ready": "false",
                "blocking_reasons": "",
                "recommended_next_action": "run_pre_reaction_sdf_qa_before_marking_ready",
            }
        ],
    )
    _write_csv(
        execution_plan_csv,
        [
            {
                "sample_id": "toy",
                "planned_bond_order_operation": operation,
            }
        ],
    )
    return write_report_csv, execution_plan_csv


def test_parse_v2000_sdf_reads_atom_and_bond_blocks(tmp_path: Path) -> None:
    sdf_path = tmp_path / "toy.sdf"
    _write_sdf(sdf_path)

    parsed = parse_v2000_sdf(sdf_path)

    assert parsed["atom_count"] == 3
    assert parsed["bond_count"] == 2
    assert len(parsed["atom_block"]) == 3
    assert parsed["bonds"][(0, 1)] == "1"


def test_copy_operation_passes_when_bond_block_unchanged(tmp_path: Path) -> None:
    source = tmp_path / "source.sdf"
    output = tmp_path / "output.sdf"
    _write_sdf(source, bond_order="2")
    _write_sdf(output, bond_order="2")
    source_hash = _sha256(source)
    output_hash = _sha256(output)
    write_report_csv, execution_plan_csv = _write_report_and_plan(
        tmp_path,
        source=source,
        output=output,
        operation="validate_existing_target_bond_order_and_copy_if_future_approved",
    )

    rows = build_report_rows(write_sdf_report_csv=write_report_csv, execution_plan_csv=execution_plan_csv)

    row = rows[0]
    assert row["qa_status"] == "generated_pre_reaction_sdf_qa_passed"
    assert row["atom_count_source"] == row["atom_count_output"]
    assert row["atom_block_identical"] == "true"
    assert row["coordinate_block_identical"] == "true"
    assert row["bond_block_change_count"] == "0"
    assert row["source_restore_bond_order"] == "2"
    assert row["output_restore_bond_order"] == "2"
    assert _sha256(source) == source_hash
    assert _sha256(output) == output_hash


def test_set_operation_passes_when_only_target_bond_order_changes(tmp_path: Path) -> None:
    source = tmp_path / "source.sdf"
    output = tmp_path / "output.sdf"
    _write_sdf(source, bond_order="1")
    _write_sdf(output, bond_order="2")
    write_report_csv, execution_plan_csv = _write_report_and_plan(
        tmp_path,
        source=source,
        output=output,
        operation="set_bond_order_to_target_if_future_approved",
    )
    output_md = tmp_path / "summary.md"
    output_csv = tmp_path / "qa.csv"

    rows = build_report_rows(write_sdf_report_csv=write_report_csv, execution_plan_csv=execution_plan_csv)
    write_csv(rows, output_csv)
    write_markdown(build_markdown(rows), output_md)

    row = rows[0]
    assert row["qa_status"] == "generated_pre_reaction_sdf_qa_passed"
    assert row["bond_block_change_count"] == "1"
    assert row["allowed_bond_order_change_only"] == "true"
    assert row["source_restore_bond_order"] == "1"
    assert row["output_restore_bond_order"] == "2"
    assert "Generated Pre-Reaction SDF QA Summary" in output_md.read_text(encoding="utf-8")


def test_non_target_bond_change_blocks(tmp_path: Path) -> None:
    source = tmp_path / "source.sdf"
    output = tmp_path / "output.sdf"
    _write_sdf(source, bond_order="1", extra_bond_order="1")
    _write_sdf(output, bond_order="2", extra_bond_order="2")
    write_report_csv, execution_plan_csv = _write_report_and_plan(
        tmp_path,
        source=source,
        output=output,
        operation="set_bond_order_to_target_if_future_approved",
    )

    row = build_report_rows(write_sdf_report_csv=write_report_csv, execution_plan_csv=execution_plan_csv)[0]

    assert row["qa_status"] == "blocked"
    assert "bond_block_change_not_limited_to_restore_bond_order" in row["blocking_reasons"]


def test_atom_block_change_blocks(tmp_path: Path) -> None:
    source = tmp_path / "source.sdf"
    output = tmp_path / "output.sdf"
    _write_sdf(source, atom_x="1.0000", bond_order="2")
    _write_sdf(output, atom_x="1.1000", bond_order="2")
    write_report_csv, execution_plan_csv = _write_report_and_plan(
        tmp_path,
        source=source,
        output=output,
        operation="validate_existing_target_bond_order_and_copy_if_future_approved",
    )

    row = build_report_rows(write_sdf_report_csv=write_report_csv, execution_plan_csv=execution_plan_csv)[0]

    assert row["qa_status"] == "blocked"
    assert "atom_block_changed" in row["blocking_reasons"]
    assert "coordinate_block_changed" in row["blocking_reasons"]


def test_output_bond_order_not_target_blocks(tmp_path: Path) -> None:
    source = tmp_path / "source.sdf"
    output = tmp_path / "output.sdf"
    _write_sdf(source, bond_order="1")
    _write_sdf(output, bond_order="1")
    write_report_csv, execution_plan_csv = _write_report_and_plan(
        tmp_path,
        source=source,
        output=output,
        operation="set_bond_order_to_target_if_future_approved",
    )

    row = build_report_rows(write_sdf_report_csv=write_report_csv, execution_plan_csv=execution_plan_csv)[0]

    assert row["qa_status"] == "blocked"
    assert "output_restore_bond_order_not_target" in row["blocking_reasons"]


def test_hash_mismatch_blocks(tmp_path: Path) -> None:
    source = tmp_path / "source.sdf"
    output = tmp_path / "output.sdf"
    _write_sdf(source, bond_order="2")
    _write_sdf(output, bond_order="2")
    write_report_csv, execution_plan_csv = _write_report_and_plan(
        tmp_path,
        source=source,
        output=output,
        operation="validate_existing_target_bond_order_and_copy_if_future_approved",
    )
    rows = list(csv.DictReader(write_report_csv.open("r", encoding="utf-8", newline="")))
    rows[0]["output_pre_reaction_sdf_sha256"] = "bad_hash"
    _write_csv(write_report_csv, rows)

    row = build_report_rows(write_sdf_report_csv=write_report_csv, execution_plan_csv=execution_plan_csv)[0]

    assert row["qa_status"] == "blocked"
    assert "output_pre_reaction_sdf_sha256_mismatch" in row["blocking_reasons"]
