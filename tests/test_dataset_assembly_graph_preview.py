import csv
import hashlib
import sys
from pathlib import Path

import pytest
from rdkit import Chem


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_dataset_assembly_graph_preview import (  # noqa: E402
    PREVIEW_CANDIDATE_COLUMNS,
    REPORT_COLUMNS,
    TARGETS,
    build_markdown,
    build_preview,
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


def _write_toy_sdf(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    mol = Chem.MolFromSmiles("CCCCCCCC")
    writer = Chem.SDWriter(str(path))
    writer.write(mol)
    writer.close()


def _atom_line(serial, atom_name, resname="CYS", chain="A", residue_id=12, element="C"):
    return (
        f"ATOM  {serial:5d} {atom_name:<4} {resname:>3} {chain}{residue_id:4d}"
        f"    {serial:8.3f}{0.0:8.3f}{0.0:8.3f}  1.00 20.00          {element:>2}\n"
    )


def _write_toy_pdb(path, chain="A", residue_id=12, resname="CYS", include_sg=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        _atom_line(1, "N", resname=resname, chain=chain, residue_id=residue_id, element="N"),
        _atom_line(2, "CA", resname=resname, chain=chain, residue_id=residue_id, element="C"),
    ]
    if include_sg:
        lines.append(_atom_line(3, "SG", resname=resname, chain=chain, residue_id=residue_id, element="S"))
    path.write_text("".join(lines) + "END\n", encoding="utf-8")


def _paths(tmp_path):
    return {
        "locked": tmp_path / "hash_locked.csv",
        "hash_report": tmp_path / "hash_report.csv",
        "preview": tmp_path / "out" / "preview.csv",
        "report": tmp_path / "out" / "report.csv",
        "summary": tmp_path / "out" / "summary.md",
    }


def _make_fixture(tmp_path):
    paths = _paths(tmp_path)
    locked_rows = []
    report_rows = []
    for candidate_id, source_id in TARGETS.items():
        residue_id = "481" if source_id == "BTK_C481_6DI9" else "12"
        protein_path = Path(f"data/raw/covalent_small/proteins/{source_id}.pdb")
        ligand_path = Path(f"data/derived/covalent_small/ligands_pre_reaction/{candidate_id}.sdf")
        _write_toy_pdb(protein_path, residue_id=int(residue_id))
        _write_toy_sdf(ligand_path)
        locked_rows.append(
            {
                "hash_locked_candidate_id": candidate_id,
                "source_sample_id": source_id,
                "pre_reaction_sample_id": candidate_id,
                "protein_pdb_path": str(protein_path),
                "protein_pdb_size_bytes": str(protein_path.stat().st_size),
                "protein_pdb_sha256": _sha(protein_path),
                "ligand_sdf_path": str(ligand_path),
                "ligand_sdf_size_bytes": str(ligand_path.stat().st_size),
                "ligand_sdf_sha256": _sha(ligand_path),
                "reactive_residue_chain": "A",
                "reactive_residue_id": residue_id,
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
                "file_hash_gate_stage": "file_existence_and_hash_locked_candidate_only_not_training",
                "training_ready": "false",
            }
        )
        report_rows.append(
            {
                "candidate_id": candidate_id,
                "file_existence_and_hash_gate_status": "file_existence_and_hash_gate_passed",
                "hash_locked_candidate_written": "true",
                "real_dataset_generated": "false",
                "training_ready": "false",
            }
        )
    _write_csv(paths["locked"], locked_rows, list(locked_rows[0]))
    _write_csv(paths["hash_report"], report_rows, list(report_rows[0]))
    return paths, locked_rows, report_rows


def _run_preview(paths):
    return build_preview(
        hash_locked_candidates_csv=paths["locked"],
        file_hash_report_csv=paths["hash_report"],
    )


def _report_for(reports, candidate_id):
    return next(row for row in reports if row["candidate_id"] == candidate_id)


def test_graph_preview_success_writes_three_candidates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, locked_rows, _ = _make_fixture(tmp_path)
    input_hashes = {row["ligand_sdf_path"]: _sha(Path(row["ligand_sdf_path"])) for row in locked_rows}

    reports, preview_candidates = _run_preview(paths)
    write_csv(preview_candidates, paths["preview"], PREVIEW_CANDIDATE_COLUMNS)
    write_csv(reports, paths["report"], REPORT_COLUMNS)
    write_markdown(build_markdown(reports, preview_candidates), paths["summary"])

    assert len(preview_candidates) == 3
    assert len(_read_csv(paths["preview"])) == 3
    assert len(_read_csv(paths["report"])) == 3
    assert "Dataset Assembly Graph Preview Summary" in paths["summary"].read_text(encoding="utf-8")
    for row in reports:
        assert row["graph_preview_status"] == "dataset_assembly_graph_preview_passed"
        assert row["graph_preview_candidate_written"] == "true"
        assert int(row["ligand_atom_count"]) > 0
        assert int(row["ligand_heavy_atom_count"]) > 0
        assert int(row["ligand_bond_count"]) > 0
        assert int(row["protein_atom_count"]) > 0
        assert int(row["protein_residue_count"]) > 0
        assert row["reactive_residue_found"] == "true"
        assert row["reactive_atom_found"] == "true"
        assert row["protein_pdb_sha256_matches_hash_locked"] == "true"
        assert row["ligand_sdf_sha256_matches_hash_locked"] == "true"
        assert row["training_ready"] == "false"
        assert row["real_dataset_generated"] == "false"
    for path_value, before_hash in input_hashes.items():
        assert _sha(Path(path_value)) == before_hash
    assert not list(tmp_path.rglob("*.pt"))
    assert not list(tmp_path.rglob("*.pkl"))
    assert not list(tmp_path.rglob("*.npz"))
    assert not list(tmp_path.rglob("*.lmdb"))


def test_candidate_missing_or_duplicate_blocks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, locked_rows, _ = _make_fixture(tmp_path)
    missing_id = "KRAS_G12C_5F2E_pre_reaction"
    _write_csv(paths["locked"], [row for row in locked_rows if row["hash_locked_candidate_id"] != missing_id], list(locked_rows[0]))
    reports, preview_candidates = _run_preview(paths)
    assert _report_for(reports, missing_id)["graph_preview_status"] == "blocked"
    assert "candidate_row_not_found_once" in _report_for(reports, missing_id)["blocking_reasons"]
    assert missing_id not in {row["graph_preview_candidate_id"] for row in preview_candidates}

    paths, locked_rows, _ = _make_fixture(tmp_path)
    duplicate = locked_rows[0].copy()
    _write_csv(paths["locked"], locked_rows + [duplicate], list(locked_rows[0]))
    reports, _ = _run_preview(paths)
    assert "candidate_row_not_found_once" in _report_for(reports, duplicate["hash_locked_candidate_id"])["blocking_reasons"]


def test_file_hash_report_not_passed_blocks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, _, report_rows = _make_fixture(tmp_path)
    report_rows[0]["file_existence_and_hash_gate_status"] = "blocked"
    _write_csv(paths["hash_report"], report_rows, list(report_rows[0]))

    reports, _ = _run_preview(paths)

    assert "file_hash_gate_not_passed" in _report_for(reports, report_rows[0]["candidate_id"])["blocking_reasons"]


def test_protein_and_ligand_hash_mismatch_blocks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, locked_rows, _ = _make_fixture(tmp_path)
    locked_rows[0]["protein_pdb_sha256"] = "bad"
    locked_rows[1]["ligand_sdf_sha256"] = "bad"
    _write_csv(paths["locked"], locked_rows, list(locked_rows[0]))

    reports, _ = _run_preview(paths)

    assert "protein_pdb_sha256_mismatch" in _report_for(reports, locked_rows[0]["hash_locked_candidate_id"])["blocking_reasons"]
    assert "ligand_sdf_sha256_mismatch" in _report_for(reports, locked_rows[1]["hash_locked_candidate_id"])["blocking_reasons"]


def test_ligand_parse_failure_blocks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, locked_rows, _ = _make_fixture(tmp_path)
    ligand_path = Path(locked_rows[0]["ligand_sdf_path"])
    ligand_path.write_text("not an sdf\n", encoding="utf-8")
    locked_rows[0]["ligand_sdf_size_bytes"] = str(ligand_path.stat().st_size)
    locked_rows[0]["ligand_sdf_sha256"] = _sha(ligand_path)
    _write_csv(paths["locked"], locked_rows, list(locked_rows[0]))

    reports, _ = _run_preview(paths)

    report = _report_for(reports, locked_rows[0]["hash_locked_candidate_id"])
    assert report["ligand_rdkit_parseable"] == "false"
    assert "ligand_rdkit_not_parseable" in report["blocking_reasons"]


@pytest.mark.parametrize(
    "field,value,expected_reason",
    [
        ("scaffold_atoms", "0 X", "scaffold_atoms_not_parseable"),
        ("linker_atoms", "1 2", "atom_groups_overlap"),
        ("warhead_atoms", "99", "atom_index_out_of_ligand_range"),
        ("warhead_atoms", "3 6", "warhead_missing_ligand_reactive_atom"),
        ("ligand_reactive_atom_id", "bad", "ligand_reactive_atom_id_not_integer"),
        ("ligand_reactive_atom_id", "99", "ligand_reactive_atom_out_of_range"),
    ],
)
def test_atom_group_blockers(tmp_path, monkeypatch, field, value, expected_reason):
    monkeypatch.chdir(tmp_path)
    paths, locked_rows, _ = _make_fixture(tmp_path)
    locked_rows[0][field] = value
    _write_csv(paths["locked"], locked_rows, list(locked_rows[0]))

    reports, _ = _run_preview(paths)

    assert expected_reason in _report_for(reports, locked_rows[0]["hash_locked_candidate_id"])["blocking_reasons"]


def test_missing_reactive_residue_or_atom_blocks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, locked_rows, _ = _make_fixture(tmp_path)
    _write_toy_pdb(Path(locked_rows[0]["protein_pdb_path"]), residue_id=999)
    locked_rows[0]["protein_pdb_size_bytes"] = str(Path(locked_rows[0]["protein_pdb_path"]).stat().st_size)
    locked_rows[0]["protein_pdb_sha256"] = _sha(Path(locked_rows[0]["protein_pdb_path"]))
    _write_toy_pdb(Path(locked_rows[1]["protein_pdb_path"]), residue_id=12, include_sg=False)
    locked_rows[1]["protein_pdb_size_bytes"] = str(Path(locked_rows[1]["protein_pdb_path"]).stat().st_size)
    locked_rows[1]["protein_pdb_sha256"] = _sha(Path(locked_rows[1]["protein_pdb_path"]))
    _write_csv(paths["locked"], locked_rows, list(locked_rows[0]))

    reports, _ = _run_preview(paths)

    assert "reactive_residue_not_found" in _report_for(reports, locked_rows[0]["hash_locked_candidate_id"])["blocking_reasons"]
    assert "reactive_atom_not_found" in _report_for(reports, locked_rows[1]["hash_locked_candidate_id"])["blocking_reasons"]
