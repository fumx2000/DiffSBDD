import csv
import hashlib
import json
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from apply_real_packaging_execution import (  # noqa: E402
    APPROVAL_TOKEN,
    PACKAGE_ROOT,
    REPORT_COLUMNS,
    TARGETS,
    apply_real_packaging_execution,
)


PLAN_COLUMNS = [
    "execution_gate_plan_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "planned_package_root",
    "planned_protein_relative_path",
    "planned_ligand_relative_path",
    "planned_metadata_relative_path",
    "planned_protein_destination_path",
    "planned_ligand_destination_path",
    "planned_metadata_destination_path",
    "protein_pdb_path",
    "protein_pdb_sha256",
    "ligand_sdf_path",
    "ligand_sdf_sha256",
    "ligand_atom_count",
    "ligand_heavy_atom_count",
    "ligand_bond_count",
    "protein_atom_count",
    "protein_residue_count",
    "reactive_residue_chain",
    "reactive_residue_id",
    "reactive_residue_type",
    "reactive_atom_name",
    "ligand_reactive_atom_id",
    "scaffold_atoms",
    "linker_atoms",
    "warhead_atoms",
    "scaffold_atom_count",
    "linker_atom_count",
    "warhead_atom_count",
    "execution_gate_stage",
    "explicit_approval_required_before_copy",
    "ready_for_real_packaging_execution_after_approval",
    "directories_created",
    "files_copied",
    "metadata_written",
    "package_archive_created",
    "real_dataset_generated",
    "training_ready",
]

GATE_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "execution_gate_plan_row_written",
    "execution_gate_status",
    "explicit_approval_required_before_copy",
    "ready_for_real_packaging_execution_after_approval",
    "directories_created",
    "files_copied",
    "metadata_written",
    "package_archive_created",
    "real_dataset_generated",
    "pre_reaction_transform_ready",
    "training_ready",
]


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
        "plan": base / "real_packaging_execution_gate_plan.csv",
        "gate": base / "real_packaging_execution_gate_report.csv",
        "manifest": tmp_path / "data" / "raw" / "covalent_small" / "manifests" / "manifest_real_small.csv",
        "report": base / "real_packaging_execution_report.csv",
        "summary": tmp_path / "docs" / "real_packaging_execution_summary.md",
    }


def _make_fixture(tmp_path):
    paths = _paths(tmp_path)
    plan_rows = []
    gate_rows = []
    manifest_rows = []
    for candidate_id, source_id in TARGETS.items():
        residue_id = "481" if source_id == "BTK_C481_6DI9" else "12"
        protein = tmp_path / "data" / "raw" / "covalent_small" / "proteins" / f"{source_id}.pdb"
        ligand = tmp_path / "data" / "derived" / "covalent_small" / "ligands_pre_reaction" / f"{candidate_id}.sdf"
        protein.parent.mkdir(parents=True, exist_ok=True)
        ligand.parent.mkdir(parents=True, exist_ok=True)
        protein.write_text(f"HEADER {source_id}\nATOM      1  SG  CYS A{residue_id:>4}\n", encoding="utf-8")
        ligand.write_text(f"{candidate_id}\n  RDKit\n\n", encoding="utf-8")
        protein_rel = f"proteins/{source_id}.pdb"
        ligand_rel = f"ligands_pre_reaction/{candidate_id}.sdf"
        metadata_rel = f"metadata/{candidate_id}.json"
        plan_rows.append(
            {
                "execution_gate_plan_id": candidate_id,
                "source_sample_id": source_id,
                "pre_reaction_sample_id": candidate_id,
                "planned_package_root": PACKAGE_ROOT,
                "planned_protein_relative_path": protein_rel,
                "planned_ligand_relative_path": ligand_rel,
                "planned_metadata_relative_path": metadata_rel,
                "planned_protein_destination_path": f"{PACKAGE_ROOT}/{protein_rel}",
                "planned_ligand_destination_path": f"{PACKAGE_ROOT}/{ligand_rel}",
                "planned_metadata_destination_path": f"{PACKAGE_ROOT}/{metadata_rel}",
                "protein_pdb_path": str(protein),
                "protein_pdb_sha256": _sha(protein),
                "ligand_sdf_path": str(ligand),
                "ligand_sdf_sha256": _sha(ligand),
                "ligand_atom_count": "8",
                "ligand_heavy_atom_count": "8",
                "ligand_bond_count": "7",
                "protein_atom_count": "3",
                "protein_residue_count": "1",
                "reactive_residue_chain": "A",
                "reactive_residue_id": residue_id,
                "reactive_residue_type": "CYS",
                "reactive_atom_name": "SG",
                "ligand_reactive_atom_id": "7",
                "scaffold_atoms": "0 1",
                "linker_atoms": "2",
                "warhead_atoms": "3 7",
                "scaffold_atom_count": "2",
                "linker_atom_count": "1",
                "warhead_atom_count": "2",
                "execution_gate_stage": "real_packaging_execution_gate_only_not_training",
                "explicit_approval_required_before_copy": "true",
                "ready_for_real_packaging_execution_after_approval": "true",
                "directories_created": "false",
                "files_copied": "false",
                "metadata_written": "false",
                "package_archive_created": "false",
                "real_dataset_generated": "false",
                "training_ready": "false",
            }
        )
        gate_rows.append(
            {
                "candidate_id": candidate_id,
                "source_sample_id": source_id,
                "pre_reaction_sample_id": candidate_id,
                "execution_gate_plan_row_written": "true",
                "execution_gate_status": "real_packaging_execution_gate_passed",
                "explicit_approval_required_before_copy": "true",
                "ready_for_real_packaging_execution_after_approval": "true",
                "directories_created": "false",
                "files_copied": "false",
                "metadata_written": "false",
                "package_archive_created": "false",
                "real_dataset_generated": "false",
                "pre_reaction_transform_ready": "false",
                "training_ready": "false",
            }
        )
        manifest_rows.append({"sample_id": source_id, "protein_pdb_path": str(protein), "ligand_sdf_path": f"raw/{source_id}.sdf"})
        manifest_rows.append({"sample_id": candidate_id, "protein_pdb_path": str(protein), "ligand_sdf_path": str(ligand)})
    _write_csv(paths["plan"], plan_rows, PLAN_COLUMNS)
    _write_csv(paths["gate"], gate_rows, GATE_COLUMNS)
    _write_csv(paths["manifest"], manifest_rows, ["sample_id", "protein_pdb_path", "ligand_sdf_path"])
    return paths, plan_rows, gate_rows, manifest_rows


def _run(paths, token=APPROVAL_TOKEN):
    return apply_real_packaging_execution(
        execution_gate_plan_csv=paths["plan"],
        execution_gate_report_csv=paths["gate"],
        manifest_csv=paths["manifest"],
        output_report_csv=paths["report"],
        output_md=paths["summary"],
        approval_token=token,
    )


def _report_for(rows, candidate_id):
    return next(row for row in rows if row["candidate_id"] == candidate_id)


def test_invalid_approval_token_blocks_without_packaging(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, _, _, _ = _make_fixture(tmp_path)
    manifest_hash = _sha(paths["manifest"])

    reports, exit_code = _run(paths, token="wrong")

    assert exit_code == 1
    assert len(reports) == 3
    assert all(row["approval_token_valid"] == "false" for row in reports)
    assert all(row["real_packaging_execution_status"] == "blocked" for row in reports)
    assert not Path(PACKAGE_ROOT).exists()
    assert _sha(paths["manifest"]) == manifest_hash
    assert len(_read_csv(paths["report"])) == 3


def test_real_packaging_execution_success(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, plan_rows, _, _ = _make_fixture(tmp_path)
    manifest_hash = _sha(paths["manifest"])
    source_hashes = {}
    for row in plan_rows:
        source_hashes[row["protein_pdb_path"]] = _sha(Path(row["protein_pdb_path"]))
        source_hashes[row["ligand_sdf_path"]] = _sha(Path(row["ligand_sdf_path"]))

    reports, exit_code = _run(paths)

    assert exit_code == 0
    assert len(reports) == 3
    assert len(_read_csv(paths["report"])) == 3
    assert "Real Packaging Execution Summary" in paths["summary"].read_text(encoding="utf-8")
    assert _sha(paths["manifest"]) == manifest_hash
    for source_path, digest in source_hashes.items():
        assert _sha(Path(source_path)) == digest
    assert len(list((Path(PACKAGE_ROOT) / "proteins").glob("*.pdb"))) == 3
    assert len(list((Path(PACKAGE_ROOT) / "ligands_pre_reaction").glob("*.sdf"))) == 3
    assert len(list((Path(PACKAGE_ROOT) / "metadata").glob("*.json"))) == 3
    for row in reports:
        assert row["real_packaging_execution_status"] == "real_packaging_execution_passed"
        assert row["protein_copied"] == "true"
        assert row["ligand_copied"] == "true"
        assert row["metadata_written"] == "true"
        assert row["packaged_protein_hash_matches_source"] == "true"
        assert row["packaged_ligand_hash_matches_source"] == "true"
        assert row["metadata_hashes_match_packaged_files"] == "true"
        assert row["manifest_modified"] == "false"
        assert row["source_pdb_modified"] == "false"
        assert row["source_sdf_modified"] == "false"
        assert row["package_archive_created"] == "false"
        assert row["real_training_tensor_generated"] == "false"
        assert row["real_dataset_generated"] == "false"
        assert row["pre_reaction_transform_ready"] == "false"
        assert row["training_ready"] == "false"
    for plan in plan_rows:
        metadata = json.loads(Path(plan["planned_metadata_destination_path"]).read_text(encoding="utf-8"))
        assert metadata["sample_id"] == plan["pre_reaction_sample_id"]
        assert metadata["source_sample_id"] == plan["source_sample_id"]
        assert metadata["protein"]["sha256"] == plan["protein_pdb_sha256"]
        assert metadata["ligand"]["sha256"] == plan["ligand_sdf_sha256"]
        assert metadata["safety_flags"]["training_ready"] is False
    assert not list(Path(PACKAGE_ROOT).rglob("*.pt"))
    assert not list(Path(PACKAGE_ROOT).rglob("*.pkl"))
    assert not list(Path(PACKAGE_ROOT).rglob("*.npz"))
    assert not list(Path(PACKAGE_ROOT).rglob("*.lmdb"))
    assert not list(Path(PACKAGE_ROOT).rglob("*.tar"))
    assert not list(Path(PACKAGE_ROOT).rglob("*.zip"))
    assert not list(Path(PACKAGE_ROOT).rglob("*.tgz"))


@pytest.mark.parametrize(
    "mutator,reason",
    [
        (lambda plan, gate, manifest: plan.pop(), "execution_gate_plan_row_found_once"),
        (lambda plan, gate, manifest: gate.pop(), "execution_gate_report_row_found_once"),
        (lambda plan, gate, manifest: gate.__setitem__(0, {**gate[0], "execution_gate_status": "blocked"}), "execution_gate_status_passed"),
        (lambda plan, gate, manifest: plan.__setitem__(0, {**plan[0], "source_sample_id": "wrong"}), "source_mapping_valid"),
        (lambda plan, gate, manifest: plan.__setitem__(0, {**plan[0], "planned_package_root": "wrong"}), "planned_layout_valid"),
        (lambda plan, gate, manifest: plan.__setitem__(0, {**plan[0], "ligand_atom_count": "0"}), "graph_counts_positive"),
        (lambda plan, gate, manifest: manifest.__setitem__(1, {**manifest[1], "ligand_sdf_path": "wrong.sdf"}), "manifest_candidate_paths_match_plan"),
    ],
)
def test_preflight_blockers_do_not_copy(tmp_path, monkeypatch, mutator, reason):
    monkeypatch.chdir(tmp_path)
    paths, plan_rows, gate_rows, manifest_rows = _make_fixture(tmp_path)
    mutator(plan_rows, gate_rows, manifest_rows)
    _write_csv(paths["plan"], plan_rows, PLAN_COLUMNS)
    _write_csv(paths["gate"], gate_rows, GATE_COLUMNS)
    _write_csv(paths["manifest"], manifest_rows, ["sample_id", "protein_pdb_path", "ligand_sdf_path"])

    reports, exit_code = _run(paths)

    assert exit_code == 1
    assert any(row[reason] == "false" for row in reports)
    assert all(row["real_packaging_execution_status"] == "blocked" for row in reports)
    assert not Path(PACKAGE_ROOT).exists()


def test_source_hash_mismatch_blocks_without_copy(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, plan_rows, _, _ = _make_fixture(tmp_path)
    Path(plan_rows[0]["protein_pdb_path"]).write_text("changed\n", encoding="utf-8")
    Path(plan_rows[1]["ligand_sdf_path"]).write_text("changed\n", encoding="utf-8")

    reports, exit_code = _run(paths)

    assert exit_code == 1
    assert _report_for(reports, plan_rows[0]["execution_gate_plan_id"])["source_protein_hash_matches_plan"] == "false"
    assert _report_for(reports, plan_rows[1]["execution_gate_plan_id"])["source_ligand_hash_matches_plan"] == "false"
    assert not Path(PACKAGE_ROOT).exists()
