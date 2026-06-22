import csv
import hashlib
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_dataset_assembly_file_existence_and_hash_gate import (  # noqa: E402
    HASH_LOCKED_COLUMNS,
    REPORT_COLUMNS,
    TARGETS,
    build_gate,
    build_markdown,
    write_csv,
    write_markdown,
)


def _write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _base_paths(tmp_path):
    return {
        "candidates": tmp_path / "candidates.csv",
        "schema_report": tmp_path / "schema_report.csv",
        "manifest": tmp_path / "manifest.csv",
        "locked": tmp_path / "out" / "locked.csv",
        "report": tmp_path / "out" / "report.csv",
        "summary": tmp_path / "out" / "summary.md",
    }


def _make_fixture(tmp_path):
    paths = _base_paths(tmp_path)
    candidate_rows = []
    schema_rows = []
    manifest_rows = []
    for candidate_id, target in TARGETS.items():
        source_id = target["source"]
        protein_path = Path(f"data/raw/covalent_small/proteins/{source_id}.pdb")
        ligand_path = Path(target["ligand"])
        protein_path.parent.mkdir(parents=True, exist_ok=True)
        ligand_path.parent.mkdir(parents=True, exist_ok=True)
        protein_path.write_text(f"HEADER {source_id}\n", encoding="utf-8")
        ligand_path.write_text(f"{candidate_id}\n  test\n\n", encoding="utf-8")
        row = {
            "schema_valid_candidate_id": candidate_id,
            "source_sample_id": source_id,
            "pre_reaction_sample_id": candidate_id,
            "protein_pdb_path": str(protein_path),
            "ligand_sdf_path": str(ligand_path),
            "reactive_residue_chain": "A",
            "reactive_residue_id": "12",
            "reactive_residue_type": "CYS",
            "reactive_atom_name": "SG",
            "ligand_reactive_atom_id": "7",
            "warhead_type": "test_warhead",
            "scaffold_atoms": "0 1",
            "linker_atoms": "2",
            "warhead_atoms": "3 7",
            "scaffold_atom_count": "2",
            "linker_atom_count": "1",
            "warhead_atom_count": "2",
            "candidate_type": "derived_pre_reaction_ligand_candidate",
            "dataset_assembly_stage": "dry_run_candidate_only_not_training",
            "schema_validation_stage": "schema_validated_candidate_only_not_training",
            "training_ready": "false",
        }
        candidate_rows.append(row)
        schema_rows.append(
            {
                "candidate_id": candidate_id,
                "schema_validation_status": "dataset_assembly_schema_validation_passed",
                "schema_valid_candidate_written": "true",
                "real_dataset_generated": "false",
                "training_ready": "false",
            }
        )
        manifest_rows.append(
            {
                "sample_id": source_id,
                "protein_pdb_path": str(protein_path),
                "ligand_sdf_path": f"data/raw/covalent_small/ligands/{source_id}.sdf",
            }
        )
        manifest_rows.append(
            {
                "sample_id": candidate_id,
                "protein_pdb_path": str(protein_path),
                "ligand_sdf_path": str(ligand_path),
            }
        )

    _write_csv(paths["candidates"], candidate_rows, list(candidate_rows[0]))
    _write_csv(paths["schema_report"], schema_rows, list(schema_rows[0]))
    _write_csv(paths["manifest"], manifest_rows, list(manifest_rows[0]))
    return paths, candidate_rows, schema_rows, manifest_rows


def _run_gate(paths):
    return build_gate(
        schema_valid_candidates_csv=paths["candidates"],
        schema_validation_report_csv=paths["schema_report"],
        manifest_csv=paths["manifest"],
    )


def _report_for(reports, candidate_id):
    return next(row for row in reports if row["candidate_id"] == candidate_id)


def test_file_existence_and_hash_gate_writes_three_hash_locked_candidates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, _, _, _ = _make_fixture(tmp_path)
    manifest_before = hashlib.sha256(paths["manifest"].read_bytes()).hexdigest()

    reports, locked = _run_gate(paths)
    write_csv(locked, paths["locked"], HASH_LOCKED_COLUMNS)
    write_csv(reports, paths["report"], REPORT_COLUMNS)
    write_markdown(build_markdown(reports, locked), paths["summary"])

    assert len(locked) == 3
    assert len(_read_csv(paths["locked"])) == 3
    assert len(_read_csv(paths["report"])) == 3
    assert "Dataset Assembly File Existence and Hash Gate Summary" in paths["summary"].read_text(encoding="utf-8")
    assert hashlib.sha256(paths["manifest"].read_bytes()).hexdigest() == manifest_before
    for row in reports:
        assert row["file_existence_and_hash_gate_status"] == "file_existence_and_hash_gate_passed"
        assert row["hash_locked_candidate_written"] == "true"
        assert row["protein_pdb_nonempty"] == "true"
        assert row["ligand_sdf_nonempty"] == "true"
        assert row["protein_pdb_sha256"]
        assert row["ligand_sdf_sha256"]
        assert row["manifest_candidate_row_found_once"] == "true"
        assert row["manifest_source_row_found_once"] == "true"
        assert row["manifest_candidate_paths_match_candidate_csv"] == "true"
        assert row["training_ready"] == "false"
    for row in locked:
        assert row["file_hash_gate_stage"] == "file_existence_and_hash_locked_candidate_only_not_training"
        assert row["training_ready"] == "false"
        assert not row["ligand_sdf_path"].endswith((".pt", ".pkl", ".npz", ".lmdb"))


def test_missing_candidate_row_blocks_candidate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, candidate_rows, _, _ = _make_fixture(tmp_path)
    missing_id = "KRAS_G12C_5F2E_pre_reaction"
    _write_csv(paths["candidates"], [row for row in candidate_rows if row["schema_valid_candidate_id"] != missing_id], list(candidate_rows[0]))

    reports, locked = _run_gate(paths)

    report = _report_for(reports, missing_id)
    assert report["file_existence_and_hash_gate_status"] == "blocked"
    assert "candidate_row_not_found_once" in report["blocking_reasons"]
    assert missing_id not in {row["hash_locked_candidate_id"] for row in locked}


def test_duplicate_candidate_row_blocks_candidate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, candidate_rows, _, _ = _make_fixture(tmp_path)
    duplicate_id = "BTK_C481_6DI9_pre_reaction"
    duplicate = next(row for row in candidate_rows if row["schema_valid_candidate_id"] == duplicate_id).copy()
    _write_csv(paths["candidates"], candidate_rows + [duplicate], list(candidate_rows[0]))

    reports, _ = _run_gate(paths)

    report = _report_for(reports, duplicate_id)
    assert report["file_existence_and_hash_gate_status"] == "blocked"
    assert "candidate_row_not_found_once" in report["blocking_reasons"]


def test_wrong_source_mapping_blocks_candidate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, candidate_rows, _, _ = _make_fixture(tmp_path)
    candidate_rows[0]["source_sample_id"] = "wrong_source"
    _write_csv(paths["candidates"], candidate_rows, list(candidate_rows[0]))

    reports, _ = _run_gate(paths)

    report = _report_for(reports, candidate_rows[0]["schema_valid_candidate_id"])
    assert report["source_mapping_valid"] == "false"
    assert "source_mapping_invalid" in report["blocking_reasons"]


def test_missing_empty_or_wrong_suffix_files_block_candidate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, candidate_rows, _, _ = _make_fixture(tmp_path)
    candidate_rows[0]["protein_pdb_path"] = "data/raw/covalent_small/proteins/missing.txt"
    candidate_rows[1]["ligand_sdf_path"] = TARGETS[candidate_rows[1]["schema_valid_candidate_id"]]["ligand"].replace(".sdf", ".mol2")
    Path(candidate_rows[2]["ligand_sdf_path"]).write_text("", encoding="utf-8")
    _write_csv(paths["candidates"], candidate_rows, list(candidate_rows[0]))

    reports, _ = _run_gate(paths)

    first = _report_for(reports, candidate_rows[0]["schema_valid_candidate_id"])
    second = _report_for(reports, candidate_rows[1]["schema_valid_candidate_id"])
    third = _report_for(reports, candidate_rows[2]["schema_valid_candidate_id"])
    assert "protein_pdb_path_suffix_not_pdb" in first["blocking_reasons"]
    assert "protein_pdb_missing" in first["blocking_reasons"]
    assert "ligand_sdf_path_not_expected" in second["blocking_reasons"]
    assert "ligand_sdf_path_suffix_not_sdf" in second["blocking_reasons"]
    assert "ligand_sdf_empty" in third["blocking_reasons"]


def test_schema_report_blockers_are_reported(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, _, schema_rows, _ = _make_fixture(tmp_path)
    schema_rows[0]["schema_validation_status"] = "blocked"
    schema_rows[1]["real_dataset_generated"] = "true"
    schema_rows[2]["training_ready"] = "true"
    _write_csv(paths["schema_report"], schema_rows, list(schema_rows[0]))

    reports, _ = _run_gate(paths)

    first = _report_for(reports, schema_rows[0]["candidate_id"])
    second = _report_for(reports, schema_rows[1]["candidate_id"])
    third = _report_for(reports, schema_rows[2]["candidate_id"])
    assert "schema_validation_status_not_passed" in first["blocking_reasons"]
    assert "schema_validation_real_dataset_generated_not_false" in second["blocking_reasons"]
    assert "schema_validation_training_ready_not_false" in third["blocking_reasons"]


def test_manifest_blockers_are_reported(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, _, _, manifest_rows = _make_fixture(tmp_path)
    candidate_id = "KRAS_G12C_6OIM_pre_reaction"
    source_id = TARGETS[candidate_id]["source"]
    for row in manifest_rows:
        if row["sample_id"] == candidate_id:
            row["ligand_sdf_path"] = "wrong.sdf"
    manifest_rows = [row for row in manifest_rows if row["sample_id"] != source_id]
    _write_csv(paths["manifest"], manifest_rows, list(manifest_rows[0]))

    reports, _ = _run_gate(paths)

    report = _report_for(reports, candidate_id)
    assert report["manifest_source_row_found_once"] == "false"
    assert report["manifest_candidate_paths_match_candidate_csv"] == "false"
    assert "manifest_source_row_not_found_once" in report["blocking_reasons"]
    assert "manifest_candidate_paths_mismatch_candidate_csv" in report["blocking_reasons"]
