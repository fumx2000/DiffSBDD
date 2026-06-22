from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from validate_dataset_assembly_candidate_schema import (
    REPORT_COLUMNS,
    TARGETS,
    VALID_CANDIDATE_COLUMNS,
    build_markdown,
    build_validation,
    write_csv,
    write_markdown,
)


REACTIVE = {
    "BTK_C481_6DI9_pre_reaction": "19",
    "KRAS_G12C_5F2E_pre_reaction": "29",
    "KRAS_G12C_6OIM_pre_reaction": "7",
}
WARHEAD = {
    "BTK_C481_6DI9_pre_reaction": "17 18 19 32",
    "KRAS_G12C_5F2E_pre_reaction": "8 27 28 29",
    "KRAS_G12C_6OIM_pre_reaction": "4 5 6 7",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _candidate_row(candidate_id: str) -> dict[str, str]:
    source_id = TARGETS[candidate_id]["source"]
    protein = f"data/raw/covalent_small/proteins/{source_id}.pdb"
    ligand = TARGETS[candidate_id]["ligand"]
    Path(protein).parent.mkdir(parents=True, exist_ok=True)
    Path(ligand).parent.mkdir(parents=True, exist_ok=True)
    Path(protein).write_text("toy pdb\n", encoding="utf-8")
    Path(ligand).write_text("toy sdf\n", encoding="utf-8")
    return {
        "candidate_id": candidate_id,
        "source_sample_id": source_id,
        "pre_reaction_sample_id": candidate_id,
        "protein_pdb_path": protein,
        "ligand_sdf_path": ligand,
        "reactive_residue_chain": "A",
        "reactive_residue_id": "1",
        "reactive_residue_type": "CYS",
        "reactive_atom_name": "SG",
        "ligand_reactive_atom_id": REACTIVE[candidate_id],
        "warhead_type": "toy",
        "scaffold_atoms": "0 1",
        "linker_atoms": "3",
        "warhead_atoms": WARHEAD[candidate_id],
        "candidate_type": "derived_pre_reaction_ligand_candidate",
        "dataset_assembly_stage": "dry_run_candidate_only_not_training",
        "training_ready": "false",
    }


def _manifest_row(sample_id: str, source_for_pre: str | None = None) -> dict[str, str]:
    pre = sample_id in TARGETS
    source_id = source_for_pre or TARGETS[sample_id]["source"] if pre else sample_id
    protein = f"data/raw/covalent_small/proteins/{source_id}.pdb"
    ligand = TARGETS[sample_id]["ligand"] if pre else f"data/raw/covalent_small/ligands/{sample_id}.sdf"
    return {
        "sample_id": sample_id,
        "protein_pdb_path": protein,
        "ligand_sdf_path": ligand,
        "reactive_residue_chain": "A",
        "reactive_residue_id": "1",
        "reactive_residue_type": "CYS",
        "reactive_atom_name": "SG",
        "ligand_reactive_atom_id": REACTIVE.get(sample_id, "1"),
        "warhead_type": "toy",
        "scaffold_atoms": "0 1",
        "linker_atoms": "3",
        "warhead_atoms": WARHEAD.get(sample_id, "2"),
    }


def _write_inputs(tmp_path: Path) -> dict[str, Path]:
    candidates = tmp_path / "candidates.csv"
    dry_run = tmp_path / "dry_run.csv"
    manifest = tmp_path / "manifest.csv"
    report = tmp_path / "report.csv"
    valid = tmp_path / "valid.csv"
    summary = tmp_path / "summary.md"
    candidate_rows = [_candidate_row(candidate_id) for candidate_id in sorted(TARGETS)]
    dry_rows = [
        {
            "pre_reaction_sample_id": candidate_id,
            "candidate_written_to_dry_run_list": "true",
            "dataset_assembly_dry_run_status": "post_manifest_dataset_assembly_dry_run_passed",
            "real_dataset_generated": "false",
            "training_ready": "false",
        }
        for candidate_id in sorted(TARGETS)
    ]
    manifest_rows = []
    for candidate_id in sorted(TARGETS):
        manifest_rows.append(_manifest_row(TARGETS[candidate_id]["source"]))
    for candidate_id in sorted(TARGETS):
        manifest_rows.append(_manifest_row(candidate_id))
    _write_csv(candidates, candidate_rows)
    _write_csv(dry_run, dry_rows)
    _write_csv(manifest, manifest_rows)
    return {
        "candidates": candidates,
        "dry_run": dry_run,
        "manifest": manifest,
        "report": report,
        "valid": valid,
        "summary": summary,
    }


def _run(paths: dict[str, Path]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    return build_validation(
        candidates_csv=paths["candidates"],
        dry_run_report_csv=paths["dry_run"],
        manifest_csv=paths["manifest"],
    )


def _mutate_csv(path: Path, key_field: str, key_value: str, field: str, value: str) -> None:
    rows = _read_csv(path)
    for row in rows:
        if row.get(key_field) == key_value:
            row[field] = value
    _write_csv(path, rows)


def test_schema_validation_passes_three_candidates(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    manifest_hash = _sha256(paths["manifest"])

    reports, valid = _run(paths)
    write_csv(valid, paths["valid"], VALID_CANDIDATE_COLUMNS)
    write_csv(reports, paths["report"], REPORT_COLUMNS)
    write_markdown(build_markdown(reports, valid), paths["summary"])

    assert len(valid) == 3
    assert len(_read_csv(paths["valid"])) == 3
    assert {row["schema_validation_status"] for row in reports} == {"dataset_assembly_schema_validation_passed"}
    assert {row["schema_valid_candidate_id"] for row in valid} == set(TARGETS)
    assert all(row["schema_valid_candidate_id"] == row["pre_reaction_sample_id"] for row in valid)
    assert {row["training_ready"] for row in valid} == {"false"}
    counts = {row["schema_valid_candidate_id"]: (row["scaffold_atom_count"], row["linker_atom_count"], row["warhead_atom_count"]) for row in valid}
    assert counts["BTK_C481_6DI9_pre_reaction"] == ("2", "1", "4")
    assert counts["KRAS_G12C_5F2E_pre_reaction"] == ("2", "1", "4")
    assert counts["KRAS_G12C_6OIM_pre_reaction"] == ("2", "1", "4")
    assert _sha256(paths["manifest"]) == manifest_hash
    assert "Dataset Assembly Schema Validation Summary" in paths["summary"].read_text(encoding="utf-8")
    assert not list(tmp_path.rglob("*.pt"))
    assert not list(tmp_path.rglob("*.pkl"))
    assert not list(tmp_path.rglob("*.npz"))
    assert not list(tmp_path.rglob("*.lmdb"))


def test_missing_required_candidate_column_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    rows = _read_csv(paths["candidates"])
    fieldnames = [field for field in rows[0] if field != "warhead_atoms"]
    rows = [{key: value for key, value in row.items() if key in fieldnames} for row in rows]
    _write_csv(paths["candidates"], rows, fieldnames)

    reports, valid = _run(paths)

    assert valid == []
    assert {row["schema_validation_status"] for row in reports} == {"blocked"}
    assert all("required_candidate_columns_missing" in row["blocking_reasons"] for row in reports)


def test_candidate_row_missing_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    rows = [row for row in _read_csv(paths["candidates"]) if row["candidate_id"] != "BTK_C481_6DI9_pre_reaction"]
    _write_csv(paths["candidates"], rows)

    reports, _ = _run(paths)

    row = next(row for row in reports if row["candidate_id"] == "BTK_C481_6DI9_pre_reaction")
    assert row["schema_validation_status"] == "blocked"
    assert "candidate_row_not_found_once" in row["blocking_reasons"]


def test_duplicate_candidate_row_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    rows = _read_csv(paths["candidates"])
    rows.append(rows[0])
    _write_csv(paths["candidates"], rows)

    reports, _ = _run(paths)

    row = next(row for row in reports if row["candidate_id"] == rows[0]["candidate_id"])
    assert row["schema_validation_status"] == "blocked"
    assert "candidate_row_not_found_once" in row["blocking_reasons"]


def test_source_mapping_wrong_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    _mutate_csv(paths["candidates"], "candidate_id", "BTK_C481_6DI9_pre_reaction", "source_sample_id", "wrong")

    reports, _ = _run(paths)

    row = next(row for row in reports if row["candidate_id"] == "BTK_C481_6DI9_pre_reaction")
    assert "source_mapping_invalid" in row["blocking_reasons"]


def test_candidate_type_or_stage_wrong_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    _mutate_csv(paths["candidates"], "candidate_id", "BTK_C481_6DI9_pre_reaction", "candidate_type", "wrong")
    _mutate_csv(paths["candidates"], "candidate_id", "KRAS_G12C_5F2E_pre_reaction", "dataset_assembly_stage", "wrong")

    reports, _ = _run(paths)

    assert any("candidate_type_invalid" in row["blocking_reasons"] for row in reports)
    assert any("dataset_assembly_stage_invalid" in row["blocking_reasons"] for row in reports)


def test_ligand_path_or_missing_file_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    Path(TARGETS["BTK_C481_6DI9_pre_reaction"]["ligand"]).unlink()
    _mutate_csv(paths["candidates"], "candidate_id", "KRAS_G12C_5F2E_pre_reaction", "ligand_sdf_path", "wrong.sdf")

    reports, _ = _run(paths)

    assert any("ligand_sdf_path_empty_or_missing" in row["blocking_reasons"] for row in reports)
    assert any("ligand_sdf_path_not_expected" in row["blocking_reasons"] for row in reports)


def test_protein_pdb_missing_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    Path(_read_csv(paths["candidates"])[0]["protein_pdb_path"]).unlink()

    reports, _ = _run(paths)

    assert any("protein_pdb_path_empty_or_missing" in row["blocking_reasons"] for row in reports)


def test_non_integer_ids_block(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    _mutate_csv(paths["candidates"], "candidate_id", "BTK_C481_6DI9_pre_reaction", "reactive_residue_id", "bad")
    _mutate_csv(paths["candidates"], "candidate_id", "KRAS_G12C_5F2E_pre_reaction", "ligand_reactive_atom_id", "bad")

    reports, _ = _run(paths)

    assert any("reactive_residue_id_not_integer" in row["blocking_reasons"] for row in reports)
    assert any("ligand_reactive_atom_id_not_integer" in row["blocking_reasons"] for row in reports)


def test_atom_list_overlap_and_missing_reactive_atom_block(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    _mutate_csv(paths["candidates"], "candidate_id", "BTK_C481_6DI9_pre_reaction", "scaffold_atoms", "0 bad")
    _mutate_csv(paths["candidates"], "candidate_id", "KRAS_G12C_5F2E_pre_reaction", "linker_atoms", "8")
    _mutate_csv(paths["candidates"], "candidate_id", "KRAS_G12C_6OIM_pre_reaction", "warhead_atoms", "4 5 6")

    reports, _ = _run(paths)

    assert any("scaffold_atoms_not_parseable" in row["blocking_reasons"] for row in reports)
    assert any("atom_groups_overlap" in row["blocking_reasons"] for row in reports)
    assert any("warhead_missing_ligand_reactive_atom" in row["blocking_reasons"] for row in reports)


def test_dry_run_report_blockers(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    _mutate_csv(paths["dry_run"], "pre_reaction_sample_id", "BTK_C481_6DI9_pre_reaction", "dataset_assembly_dry_run_status", "blocked")
    _mutate_csv(paths["dry_run"], "pre_reaction_sample_id", "KRAS_G12C_5F2E_pre_reaction", "real_dataset_generated", "true")

    reports, _ = _run(paths)

    assert any("dry_run_status_not_passed" in row["blocking_reasons"] for row in reports)
    assert any("dry_run_real_dataset_generated_not_false" in row["blocking_reasons"] for row in reports)


def test_manifest_missing_candidate_or_source_blocks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    paths = _write_inputs(tmp_path)
    rows = [
        row
        for row in _read_csv(paths["manifest"])
        if row["sample_id"] not in {"BTK_C481_6DI9_pre_reaction", "KRAS_G12C_5F2E"}
    ]
    _write_csv(paths["manifest"], rows)

    reports, _ = _run(paths)

    assert any("manifest_candidate_row_not_found_once" in row["blocking_reasons"] for row in reports)
    assert any("manifest_source_row_not_found_once" in row["blocking_reasons"] for row in reports)
