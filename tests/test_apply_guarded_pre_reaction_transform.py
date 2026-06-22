from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from apply_guarded_pre_reaction_transform import (
    APPROVAL_PHRASE,
    build_dry_run_rows,
    get_source_bond_order,
    run,
    write_csv,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_sdf(path: Path, bond_order: str = "1") -> None:
    path.write_text(
        "\n".join(
            [
                "toy",
                "  test",
                "",
                "  2  1  0  0  0  0            999 V2000",
                "    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0",
                "    1.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0",
                f"  1  2  {bond_order}  0",
                "M  END",
                "$$$$",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _plan_row(sample_id: str, sdf_path: Path, sha256: str, operation: str) -> dict[str, str]:
    return {
        "sample_id": sample_id,
        "source_repaired_sdf": str(sdf_path),
        "source_repaired_sdf_sha256": sha256,
        "planned_output_pre_reaction_sdf": f"data/derived/covalent_small/ligands_pre_reaction/{sample_id}_pre_reaction.sdf",
        "dry_run_preview_status": "preview_passed",
        "can_build_future_transform_script": "true",
        "manual_covalent_bond_to_remove": "CYS:SG-1",
        "ligand_reactive_atom": "1",
        "covalent_bond_removal_operation": "protein_ligand_covalent_bond_removal_directive_recorded_not_applied_to_ligand_only_sdf",
        "manual_bond_order_to_restore": "0-1:double",
        "restore_bond_atom_1": "0",
        "restore_bond_atom_2": "1",
        "current_bond_order_in_repaired_sdf": "1",
        "target_bond_order": "2",
        "planned_bond_order_operation": operation,
        "manual_atoms_requiring_charge_check": "1",
        "manual_atoms_requiring_valence_check": "0 1",
        "manual_boundary_resolution": "reviewed_no_boundary_atoms_transferred_to_pre_reaction_transform_rule_candidate",
        "execution_plan_status": "ready_for_guarded_transform_script_design",
        "write_sdf_allowed_by_plan": "false",
        "explicit_human_approval_required_for_sdf_generation": "true",
        "approval_phrase_required": APPROVAL_PHRASE,
        "pre_reaction_sdf_generated": "false",
        "raw_ligand_sdf_modified": "false",
        "repaired_trial_sdf_modified": "false",
        "manifest_modified": "false",
        "pre_reaction_transform_ready": "false",
        "training_ready": "false",
        "blocking_reasons": "",
        "recommended_next_action": "implement_guarded_transform_script_but_do_not_run_write_mode",
    }


def _write_plan(tmp_path: Path) -> tuple[Path, list[Path]]:
    sdf_paths: list[Path] = []
    rows: list[dict[str, str]] = []
    samples = [
        ("BTK_C481_6DI9", "validate_existing_target_bond_order_and_copy_if_future_approved"),
        ("KRAS_G12C_5F2E", "validate_existing_target_bond_order_and_copy_if_future_approved"),
        ("KRAS_G12C_6OIM", "set_bond_order_to_target_if_future_approved"),
    ]
    for sample_id, operation in samples:
        sdf_path = tmp_path / f"{sample_id}_warhead_only_repaired_trial.sdf"
        _write_sdf(sdf_path)
        sdf_paths.append(sdf_path)
        rows.append(_plan_row(sample_id, sdf_path, _sha256(sdf_path), operation))
    plan_csv = tmp_path / "execution_plan.csv"
    _write_csv(plan_csv, rows)
    return plan_csv, sdf_paths


def _write_success_plan(tmp_path: Path) -> tuple[Path, list[Path]]:
    sdf_paths: list[Path] = []
    rows: list[dict[str, str]] = []
    samples = [
        ("BTK_C481_6DI9", "validate_existing_target_bond_order_and_copy_if_future_approved", "2"),
        ("KRAS_G12C_5F2E", "validate_existing_target_bond_order_and_copy_if_future_approved", "2"),
        ("KRAS_G12C_6OIM", "set_bond_order_to_target_if_future_approved", "1"),
    ]
    for sample_id, operation, bond_order in samples:
        sdf_path = tmp_path / f"{sample_id}_warhead_only_repaired_trial.sdf"
        _write_sdf(sdf_path, bond_order=bond_order)
        sdf_paths.append(sdf_path)
        rows.append(_plan_row(sample_id, sdf_path, _sha256(sdf_path), operation))
    plan_csv = tmp_path / "execution_plan.csv"
    _write_csv(plan_csv, rows)
    return plan_csv, sdf_paths


def test_dry_run_passes_without_writing_files_or_creating_directory(tmp_path: Path) -> None:
    plan_csv, sdf_paths = _write_plan(tmp_path)
    output_csv = tmp_path / "dry_run_report.csv"
    output_md = tmp_path / "dry_run.md"
    plan_hash = _sha256(plan_csv)
    sdf_hashes = {path: _sha256(path) for path in sdf_paths}

    rows = run(
        execution_plan_csv=plan_csv,
        mode="dry_run",
        output_report_csv=output_csv,
        output_md=output_md,
    )

    assert len(rows) == 3
    assert {row["dry_run_status"] for row in rows} == {"dry_run_passed_no_files_written"}
    assert {row["source_repaired_sdf_sha256_matches"] for row in rows} == {"true"}
    assert {row["can_attempt_future_write_sdf_after_explicit_approval"] for row in rows} == {"true"}
    assert {row["write_sdf_attempted"] for row in rows} == {"false"}
    assert {row["pre_reaction_sdf_generated"] for row in rows} == {"false"}
    assert {row["ligands_pre_reaction_dir_created"] for row in rows} == {"false"}
    assert output_csv.exists()
    assert output_md.exists()
    assert "Guarded Pre-Reaction Transform Dry-Run Summary" in output_md.read_text(encoding="utf-8")
    assert _sha256(plan_csv) == plan_hash
    assert {path: _sha256(path) for path in sdf_paths} == sdf_hashes
    assert not (tmp_path / "data" / "derived" / "covalent_small" / "ligands_pre_reaction").exists()
    assert len(list(tmp_path.rglob("*pre_reaction.sdf"))) == 0


def test_wrong_hash_blocks_dry_run(tmp_path: Path) -> None:
    plan_csv, _ = _write_plan(tmp_path)
    rows = list(csv.DictReader(plan_csv.open("r", encoding="utf-8", newline="")))
    rows[0]["source_repaired_sdf_sha256"] = "bad_hash"
    _write_csv(plan_csv, rows)

    report_rows = build_dry_run_rows(plan_csv)
    row = next(report for report in report_rows if report["sample_id"] == "BTK_C481_6DI9")

    assert row["dry_run_status"] == "blocked"
    assert row["source_repaired_sdf_sha256_matches"] == "false"
    assert "source_repaired_sdf_sha256_mismatch" in row["blocking_reasons"]


def test_write_sdf_mode_without_approval_fails_without_creating_directory(tmp_path: Path) -> None:
    plan_csv, sdf_paths = _write_plan(tmp_path)
    output_csv = tmp_path / "report.csv"
    output_md = tmp_path / "summary.md"
    plan_hash = _sha256(plan_csv)
    sdf_hashes = {path: _sha256(path) for path in sdf_paths}

    with pytest.raises(ValueError):
        run(
            execution_plan_csv=plan_csv,
            mode="write_sdf",
            output_report_csv=output_csv,
            output_md=output_md,
            approval_phrase="",
        )

    assert not output_csv.exists()
    assert not output_md.exists()
    assert _sha256(plan_csv) == plan_hash
    assert {path: _sha256(path) for path in sdf_paths} == sdf_hashes
    assert not (tmp_path / "data" / "derived" / "covalent_small" / "ligands_pre_reaction").exists()
    assert len(list(tmp_path.rglob("*pre_reaction.sdf"))) == 0


def test_write_sdf_mode_with_wrong_approval_fails_without_creating_directory(tmp_path: Path) -> None:
    plan_csv, _ = _write_plan(tmp_path)

    with pytest.raises(ValueError):
        run(
            execution_plan_csv=plan_csv,
            mode="write_sdf",
            output_report_csv=tmp_path / "report.csv",
            output_md=tmp_path / "summary.md",
            approval_phrase="WRONG",
        )

    assert not (tmp_path / "data" / "derived" / "covalent_small" / "ligands_pre_reaction").exists()


def test_write_sdf_mode_without_override_fails_without_creating_directory(tmp_path: Path) -> None:
    plan_csv, _ = _write_plan(tmp_path)

    with pytest.raises(ValueError):
        run(
            execution_plan_csv=plan_csv,
            mode="write_sdf",
            output_report_csv=tmp_path / "report.csv",
            output_md=tmp_path / "summary.md",
            approval_phrase=APPROVAL_PHRASE,
        )

    assert not (tmp_path / "data" / "derived" / "covalent_small" / "ligands_pre_reaction").exists()


def test_write_sdf_mode_with_hash_mismatch_fails_without_creating_directory(tmp_path: Path) -> None:
    plan_csv, sdf_paths = _write_plan(tmp_path)
    rows = list(csv.DictReader(plan_csv.open("r", encoding="utf-8", newline="")))
    rows[0]["source_repaired_sdf_sha256"] = "bad_hash"
    _write_csv(plan_csv, rows)
    plan_hash = _sha256(plan_csv)
    sdf_hashes = {path: _sha256(path) for path in sdf_paths}

    with pytest.raises(ValueError):
        run(
            execution_plan_csv=plan_csv,
            mode="write_sdf",
            output_report_csv=tmp_path / "report.csv",
            output_md=tmp_path / "summary.md",
            approval_phrase=APPROVAL_PHRASE,
            override_plan_write_lock=True,
        )

    assert _sha256(plan_csv) == plan_hash
    assert {path: _sha256(path) for path in sdf_paths} == sdf_hashes
    assert not (tmp_path / "data" / "derived" / "covalent_small" / "ligands_pre_reaction").exists()
    assert len(list(tmp_path.rglob("*pre_reaction.sdf"))) == 0


def test_write_sdf_mode_with_bad_output_parent_fails_without_creating_directory(tmp_path: Path) -> None:
    plan_csv, _ = _write_plan(tmp_path)
    rows = list(csv.DictReader(plan_csv.open("r", encoding="utf-8", newline="")))
    rows[0]["planned_output_pre_reaction_sdf"] = "bad_parent/toy_pre_reaction.sdf"
    _write_csv(plan_csv, rows)

    with pytest.raises(ValueError):
        run(
            execution_plan_csv=plan_csv,
            mode="write_sdf",
            output_report_csv=tmp_path / "report.csv",
            output_md=tmp_path / "summary.md",
            approval_phrase=APPROVAL_PHRASE,
            override_plan_write_lock=True,
        )

    assert not (tmp_path / "data" / "derived" / "covalent_small" / "ligands_pre_reaction").exists()


def test_write_sdf_mode_success_generates_only_derived_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    plan_csv, sdf_paths = _write_success_plan(tmp_path)
    output_csv = tmp_path / "write_report.csv"
    output_md = tmp_path / "write_summary.md"
    plan_hash = _sha256(plan_csv)
    sdf_hashes = {path: _sha256(path) for path in sdf_paths}

    rows = run(
        execution_plan_csv=plan_csv,
        mode="write_sdf",
        output_report_csv=output_csv,
        output_md=output_md,
        approval_phrase=APPROVAL_PHRASE,
        override_plan_write_lock=True,
    )

    output_dir = tmp_path / "data" / "derived" / "covalent_small" / "ligands_pre_reaction"
    outputs = sorted(output_dir.glob("*.sdf"))
    assert len(outputs) == 3
    by_sample = {row["sample_id"]: row for row in rows}
    assert by_sample["BTK_C481_6DI9"]["final_bond_order_in_output_sdf"] == "2"
    assert by_sample["KRAS_G12C_5F2E"]["final_bond_order_in_output_sdf"] == "2"
    assert by_sample["KRAS_G12C_6OIM"]["final_bond_order_in_output_sdf"] == "2"
    assert get_source_bond_order({**by_sample["KRAS_G12C_6OIM"], "source_repaired_sdf": by_sample["KRAS_G12C_6OIM"]["output_pre_reaction_sdf"]}) == "2"
    assert {row["write_sdf_status"] for row in rows} == {"written_after_explicit_human_approval"}
    assert {row["pre_reaction_sdf_generated"] for row in rows} == {"true"}
    assert {row["raw_ligand_sdf_modified"] for row in rows} == {"false"}
    assert {row["repaired_trial_sdf_modified"] for row in rows} == {"false"}
    assert {row["manifest_modified"] for row in rows} == {"false"}
    assert {row["training_ready"] for row in rows} == {"false"}
    assert output_csv.exists()
    assert output_md.exists()
    assert "Guarded Pre-Reaction Transform Write-SDF Summary" in output_md.read_text(encoding="utf-8")
    assert _sha256(plan_csv) == plan_hash
    assert {path: _sha256(path) for path in sdf_paths} == sdf_hashes
