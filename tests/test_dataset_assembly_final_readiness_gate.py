import csv
import hashlib
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_dataset_assembly_final_readiness_gate import (  # noqa: E402
    FINAL_CANDIDATE_COLUMNS,
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


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _paths(tmp_path):
    base = tmp_path / "data" / "derived" / "covalent_small" / "pre_reaction_graph"
    return {
        "dry_candidates": base / "dry_candidates.csv",
        "dry_report": base / "dry_report.csv",
        "schema_candidates": base / "schema_candidates.csv",
        "schema_report": base / "schema_report.csv",
        "hash_candidates": base / "hash_candidates.csv",
        "hash_report": base / "hash_report.csv",
        "graph_candidates": base / "graph_candidates.csv",
        "graph_report": base / "graph_report.csv",
        "manifest": tmp_path / "data" / "raw" / "covalent_small" / "manifests" / "manifest_real_small.csv",
        "final": tmp_path / "out" / "final.csv",
        "report": tmp_path / "out" / "report.csv",
        "summary": tmp_path / "out" / "summary.md",
    }


def _make_fixture(tmp_path):
    paths = _paths(tmp_path)
    rows = {name: [] for name in ["dry", "dry_report", "schema", "schema_report", "hash", "hash_report", "graph", "graph_report", "manifest"]}
    for candidate_id, source_id in TARGETS.items():
        residue_id = "481" if source_id == "BTK_C481_6DI9" else "12"
        protein = Path(f"data/raw/covalent_small/proteins/{source_id}.pdb")
        ligand = Path(f"data/derived/covalent_small/ligands_pre_reaction/{candidate_id}.sdf")
        protein.parent.mkdir(parents=True, exist_ok=True)
        ligand.parent.mkdir(parents=True, exist_ok=True)
        protein.write_text(f"HEADER {source_id}\nATOM      1  SG  CYS A{int(residue_id):4d}      0.0 0.0 0.0\n", encoding="utf-8")
        ligand.write_text(f"{candidate_id}\n", encoding="utf-8")
        common = {
            "source_sample_id": source_id,
            "pre_reaction_sample_id": candidate_id,
            "protein_pdb_path": str(protein),
            "ligand_sdf_path": str(ligand),
            "reactive_residue_chain": "A",
            "reactive_residue_id": residue_id,
            "reactive_residue_type": "CYS",
            "reactive_atom_name": "SG",
            "ligand_reactive_atom_id": "7",
            "warhead_type": "test_warhead",
            "scaffold_atoms": "0 1",
            "linker_atoms": "2",
            "warhead_atoms": "3 7",
            "candidate_type": "derived_pre_reaction_ligand_candidate",
            "dataset_assembly_stage": "dry_run_candidate_only_not_training",
            "training_ready": "false",
        }
        rows["dry"].append({"candidate_id": candidate_id, **common})
        rows["dry_report"].append(
            {
                "pre_reaction_sample_id": candidate_id,
                "source_sample_id": source_id,
                "candidate_written_to_dry_run_list": "true",
                "dataset_assembly_dry_run_status": "post_manifest_dataset_assembly_dry_run_passed",
                "real_dataset_generated": "false",
                "training_ready": "false",
            }
        )
        schema_common = {
            "schema_valid_candidate_id": candidate_id,
            **common,
            "scaffold_atom_count": "2",
            "linker_atom_count": "1",
            "warhead_atom_count": "2",
            "schema_validation_stage": "schema_validated_candidate_only_not_training",
        }
        rows["schema"].append(schema_common)
        rows["schema_report"].append(
            {
                "candidate_id": candidate_id,
                "schema_validation_status": "dataset_assembly_schema_validation_passed",
                "schema_valid_candidate_written": "true",
                "real_dataset_generated": "false",
                "training_ready": "false",
            }
        )
        rows["hash"].append(
            {
                "hash_locked_candidate_id": candidate_id,
                **schema_common,
                "protein_pdb_size_bytes": str(protein.stat().st_size),
                "protein_pdb_sha256": _sha(protein),
                "ligand_sdf_size_bytes": str(ligand.stat().st_size),
                "ligand_sdf_sha256": _sha(ligand),
                "file_hash_gate_stage": "file_existence_and_hash_locked_candidate_only_not_training",
            }
        )
        rows["hash_report"].append(
            {
                "candidate_id": candidate_id,
                "file_existence_and_hash_gate_status": "file_existence_and_hash_gate_passed",
                "hash_locked_candidate_written": "true",
                "real_dataset_generated": "false",
                "training_ready": "false",
            }
        )
        rows["graph"].append(
            {
                "graph_preview_candidate_id": candidate_id,
                **schema_common,
                "protein_pdb_sha256": _sha(protein),
                "ligand_sdf_sha256": _sha(ligand),
                "ligand_atom_count": "8",
                "ligand_heavy_atom_count": "8",
                "ligand_bond_count": "7",
                "protein_atom_count": "3",
                "protein_residue_count": "1",
                "reactive_residue_found": "true",
                "reactive_atom_found": "true",
                "file_hash_gate_stage": "file_existence_and_hash_locked_candidate_only_not_training",
                "graph_preview_stage": "graph_preview_candidate_only_not_training",
            }
        )
        rows["graph_report"].append(
            {
                "candidate_id": candidate_id,
                "graph_preview_status": "dataset_assembly_graph_preview_passed",
                "graph_preview_candidate_written": "true",
                "real_dataset_generated": "false",
                "training_ready": "false",
            }
        )
        rows["manifest"].append({"sample_id": source_id, "protein_pdb_path": str(protein), "ligand_sdf_path": f"raw/{source_id}.sdf"})
        rows["manifest"].append({"sample_id": candidate_id, "protein_pdb_path": str(protein), "ligand_sdf_path": str(ligand)})

    _write_csv(paths["dry_candidates"], rows["dry"], list(rows["dry"][0]))
    _write_csv(paths["dry_report"], rows["dry_report"], list(rows["dry_report"][0]))
    _write_csv(paths["schema_candidates"], rows["schema"], list(rows["schema"][0]))
    _write_csv(paths["schema_report"], rows["schema_report"], list(rows["schema_report"][0]))
    _write_csv(paths["hash_candidates"], rows["hash"], list(rows["hash"][0]))
    _write_csv(paths["hash_report"], rows["hash_report"], list(rows["hash_report"][0]))
    _write_csv(paths["graph_candidates"], rows["graph"], list(rows["graph"][0]))
    _write_csv(paths["graph_report"], rows["graph_report"], list(rows["graph_report"][0]))
    _write_csv(paths["manifest"], rows["manifest"], list(rows["manifest"][0]))
    return paths, rows


def _run(paths):
    return build_gate(
        dry_run_candidates_csv=paths["dry_candidates"],
        dry_run_report_csv=paths["dry_report"],
        schema_valid_candidates_csv=paths["schema_candidates"],
        schema_validation_report_csv=paths["schema_report"],
        hash_locked_candidates_csv=paths["hash_candidates"],
        file_hash_report_csv=paths["hash_report"],
        graph_preview_candidates_csv=paths["graph_candidates"],
        graph_preview_report_csv=paths["graph_report"],
        manifest_csv=paths["manifest"],
    )


def _report_for(reports, candidate_id):
    return next(row for row in reports if row["candidate_id"] == candidate_id)


def test_final_readiness_success_writes_three_candidates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, rows = _make_fixture(tmp_path)
    manifest_hash = _sha(paths["manifest"])

    reports, final_candidates = _run(paths)
    write_csv(final_candidates, paths["final"], FINAL_CANDIDATE_COLUMNS)
    write_csv(reports, paths["report"], REPORT_COLUMNS)
    write_markdown(build_markdown(reports, final_candidates), paths["summary"])

    assert len(final_candidates) == 3
    assert len(_read_csv(paths["final"])) == 3
    assert len(_read_csv(paths["report"])) == 3
    assert "Dataset Assembly Final Readiness Gate Summary" in paths["summary"].read_text(encoding="utf-8")
    assert _sha(paths["manifest"]) == manifest_hash
    for row in reports:
        assert row["final_readiness_status"] == "dataset_assembly_final_readiness_passed"
        assert row["ready_for_packaging_dry_run"] == "true"
        assert row["training_ready"] == "false"
        assert row["pre_reaction_transform_ready"] == "false"
        assert row["current_protein_pdb_sha256_matches_record"] == "true"
        assert row["current_ligand_sdf_sha256_matches_record"] == "true"
    for row in final_candidates:
        assert row["ready_for_packaging_dry_run"] == "true"
        assert row["training_ready"] == "false"
    assert not list(tmp_path.rglob("*.pt"))
    assert not list(tmp_path.rglob("*.pkl"))
    assert not list(tmp_path.rglob("*.npz"))
    assert not list(tmp_path.rglob("*.lmdb"))


@pytest.mark.parametrize(
    "table,path_key,id_key,reason",
    [
        ("dry", "dry_candidates", "candidate_id", "dry_run_candidate_not_found_once"),
        ("schema", "schema_candidates", "schema_valid_candidate_id", "schema_valid_candidate_not_found_once"),
        ("hash", "hash_candidates", "hash_locked_candidate_id", "hash_locked_candidate_not_found_once"),
        ("graph", "graph_candidates", "graph_preview_candidate_id", "graph_preview_candidate_not_found_once"),
    ],
)
def test_missing_stage_candidate_blocks(tmp_path, monkeypatch, table, path_key, id_key, reason):
    monkeypatch.chdir(tmp_path)
    paths, rows = _make_fixture(tmp_path)
    candidate_id = "KRAS_G12C_5F2E_pre_reaction"
    rows[table] = [row for row in rows[table] if row[id_key] != candidate_id]
    _write_csv(paths[path_key], rows[table], list(rows[table][0]))

    reports, final_candidates = _run(paths)

    assert reason in _report_for(reports, candidate_id)["blocking_reasons"]
    assert candidate_id not in {row["final_readiness_candidate_id"] for row in final_candidates}


def test_duplicate_stage_candidate_blocks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, rows = _make_fixture(tmp_path)
    duplicate = rows["graph"][0].copy()
    rows["graph"].append(duplicate)
    _write_csv(paths["graph_candidates"], rows["graph"], list(rows["graph"][0]))

    reports, _ = _run(paths)

    assert "graph_preview_candidate_not_found_once" in _report_for(reports, duplicate["graph_preview_candidate_id"])["blocking_reasons"]


@pytest.mark.parametrize(
    "mutator,reason",
    [
        (lambda rows: rows["schema"].__setitem__(0, {**rows["schema"][0], "source_sample_id": "wrong"}), "source_mapping_inconsistent"),
        (lambda rows: rows["schema"].__setitem__(0, {**rows["schema"][0], "protein_pdb_path": "wrong.pdb"}), "protein_pdb_path_inconsistent"),
        (lambda rows: rows["schema"].__setitem__(0, {**rows["schema"][0], "ligand_sdf_path": "wrong.sdf"}), "ligand_sdf_path_inconsistent"),
        (lambda rows: rows["dry_report"].__setitem__(0, {**rows["dry_report"][0], "dataset_assembly_dry_run_status": "blocked"}), "dry_run_status_not_passed"),
        (lambda rows: rows["schema_report"].__setitem__(0, {**rows["schema_report"][0], "schema_validation_status": "blocked"}), "schema_validation_status_not_passed"),
        (lambda rows: rows["hash_report"].__setitem__(0, {**rows["hash_report"][0], "file_existence_and_hash_gate_status": "blocked"}), "file_hash_gate_not_passed"),
        (lambda rows: rows["graph_report"].__setitem__(0, {**rows["graph_report"][0], "graph_preview_status": "blocked"}), "graph_preview_status_not_passed"),
        (lambda rows: rows["graph"].__setitem__(0, {**rows["graph"][0], "ligand_atom_count": "0"}), "ligand_atom_count_not_positive"),
        (lambda rows: rows["graph"].__setitem__(0, {**rows["graph"][0], "reactive_residue_found": "false"}), "reactive_residue_not_found"),
        (lambda rows: rows["graph"].__setitem__(0, {**rows["graph"][0], "reactive_atom_found": "false"}), "reactive_atom_not_found"),
    ],
)
def test_consistency_and_status_blockers(tmp_path, monkeypatch, mutator, reason):
    monkeypatch.chdir(tmp_path)
    paths, rows = _make_fixture(tmp_path)
    mutator(rows)
    _write_csv(paths["schema_candidates"], rows["schema"], list(rows["schema"][0]))
    _write_csv(paths["dry_report"], rows["dry_report"], list(rows["dry_report"][0]))
    _write_csv(paths["schema_report"], rows["schema_report"], list(rows["schema_report"][0]))
    _write_csv(paths["hash_report"], rows["hash_report"], list(rows["hash_report"][0]))
    _write_csv(paths["graph_candidates"], rows["graph"], list(rows["graph"][0]))
    _write_csv(paths["graph_report"], rows["graph_report"], list(rows["graph_report"][0]))

    reports, _ = _run(paths)

    assert reason in _report_for(reports, rows["dry"][0]["candidate_id"])["blocking_reasons"]


def test_current_hash_mismatch_blocks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, rows = _make_fixture(tmp_path)
    Path(rows["graph"][0]["protein_pdb_path"]).write_text("changed\n", encoding="utf-8")
    Path(rows["graph"][1]["ligand_sdf_path"]).write_text("changed\n", encoding="utf-8")

    reports, _ = _run(paths)

    assert "current_protein_pdb_sha256_mismatch" in _report_for(reports, rows["graph"][0]["graph_preview_candidate_id"])["blocking_reasons"]
    assert "current_ligand_sdf_sha256_mismatch" in _report_for(reports, rows["graph"][1]["graph_preview_candidate_id"])["blocking_reasons"]


def test_manifest_missing_rows_block(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, rows = _make_fixture(tmp_path)
    candidate_id = "BTK_C481_6DI9_pre_reaction"
    source_id = TARGETS[candidate_id]
    rows["manifest"] = [row for row in rows["manifest"] if row["sample_id"] not in {candidate_id, source_id}]
    _write_csv(paths["manifest"], rows["manifest"], ["sample_id", "protein_pdb_path", "ligand_sdf_path"])

    reports, _ = _run(paths)

    report = _report_for(reports, candidate_id)
    assert "manifest_candidate_row_not_found_once" in report["blocking_reasons"]
    assert "manifest_source_row_not_found_once" in report["blocking_reasons"]
