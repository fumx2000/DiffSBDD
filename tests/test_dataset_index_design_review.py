import csv
import hashlib
import json
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_dataset_index_design_review import (  # noqa: E402
    PLAN_COLUMNS,
    REPORT_COLUMNS,
    TARGETS,
    build_design_review,
    build_markdown,
    write_csv,
    write_markdown,
)


PACKAGE_ROOT = Path("data/derived/covalent_small/packaging_real_review_only")


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
        "qa": base / "real_packaging_execution_qa_report.csv",
        "execution": base / "real_packaging_execution_report.csv",
        "plan": base / "real_packaging_execution_gate_plan.csv",
        "manifest": tmp_path / "data" / "raw" / "covalent_small" / "manifests" / "manifest_real_small.csv",
        "output_plan": base / "dataset_index_design_review_plan.csv",
        "output_report": base / "dataset_index_design_review_report.csv",
        "summary": tmp_path / "docs" / "dataset_index_design_review_summary.md",
        "package_root": tmp_path / PACKAGE_ROOT,
    }


def _metadata(plan):
    return {
        "sample_id": plan["pre_reaction_sample_id"],
        "source_sample_id": plan["source_sample_id"],
        "pre_reaction_sample_id": plan["pre_reaction_sample_id"],
        "protein": {
            "source_path": plan["protein_pdb_path"],
            "packaged_path": plan["planned_protein_destination_path"],
            "sha256": plan["protein_pdb_sha256"],
        },
        "ligand": {
            "source_path": plan["ligand_sdf_path"],
            "packaged_path": plan["planned_ligand_destination_path"],
            "sha256": plan["ligand_sdf_sha256"],
        },
        "safety_flags": {
            "manifest_modified": False,
            "source_sdf_modified": False,
            "source_pdb_modified": False,
            "package_archive_created": False,
            "real_training_tensor_generated": False,
            "real_dataset_generated": False,
            "training_ready": False,
        },
    }


def _make_fixture(tmp_path):
    paths = _paths(tmp_path)
    qa_rows = []
    execution_rows = []
    plan_rows = []
    manifest_rows = []
    for candidate_id, source_id in TARGETS.items():
        residue_id = "481" if source_id == "BTK_C481_6DI9" else "12"
        source_protein = tmp_path / "data" / "raw" / "covalent_small" / "proteins" / f"{source_id}.pdb"
        source_ligand = tmp_path / "data" / "derived" / "covalent_small" / "ligands_pre_reaction" / f"{candidate_id}.sdf"
        source_protein.parent.mkdir(parents=True, exist_ok=True)
        source_ligand.parent.mkdir(parents=True, exist_ok=True)
        source_protein.write_text(f"HEADER {source_id}\n", encoding="utf-8")
        source_ligand.write_text(f"{candidate_id}\n", encoding="utf-8")
        protein_rel = f"proteins/{source_id}.pdb"
        ligand_rel = f"ligands_pre_reaction/{candidate_id}.sdf"
        metadata_rel = f"metadata/{candidate_id}.json"
        packaged_protein = tmp_path / PACKAGE_ROOT / protein_rel
        packaged_ligand = tmp_path / PACKAGE_ROOT / ligand_rel
        packaged_metadata = tmp_path / PACKAGE_ROOT / metadata_rel
        packaged_protein.parent.mkdir(parents=True, exist_ok=True)
        packaged_ligand.parent.mkdir(parents=True, exist_ok=True)
        packaged_metadata.parent.mkdir(parents=True, exist_ok=True)
        packaged_protein.write_bytes(source_protein.read_bytes())
        packaged_ligand.write_bytes(source_ligand.read_bytes())
        plan = {
            "execution_gate_plan_id": candidate_id,
            "source_sample_id": source_id,
            "pre_reaction_sample_id": candidate_id,
            "planned_package_root": str(PACKAGE_ROOT),
            "planned_protein_relative_path": protein_rel,
            "planned_ligand_relative_path": ligand_rel,
            "planned_metadata_relative_path": metadata_rel,
            "planned_protein_destination_path": str(PACKAGE_ROOT / protein_rel),
            "planned_ligand_destination_path": str(PACKAGE_ROOT / ligand_rel),
            "planned_metadata_destination_path": str(PACKAGE_ROOT / metadata_rel),
            "protein_pdb_path": str(source_protein),
            "protein_pdb_sha256": _sha(source_protein),
            "ligand_sdf_path": str(source_ligand),
            "ligand_sdf_sha256": _sha(source_ligand),
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
        }
        packaged_metadata.write_text(json.dumps(_metadata(plan), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        plan_rows.append(plan)
        execution_rows.append(
            {
                "candidate_id": candidate_id,
                "source_sample_id": source_id,
                "pre_reaction_sample_id": candidate_id,
                "real_packaging_execution_status": "real_packaging_execution_passed",
                "real_dataset_generated": "false",
                "training_ready": "false",
            }
        )
        qa_rows.append(
            {
                "candidate_id": candidate_id,
                "source_sample_id": source_id,
                "pre_reaction_sample_id": candidate_id,
                "real_packaging_execution_qa_status": "real_packaging_execution_qa_passed",
                "protein_hash_chain_valid": "true",
                "ligand_hash_chain_valid": "true",
                "metadata_ids_valid": "true",
                "metadata_paths_valid": "true",
                "metadata_hashes_valid": "true",
                "metadata_provenance_valid": "true",
                "metadata_safety_flags_valid": "true",
                "forbidden_training_tensors_absent": "true",
                "forbidden_archives_absent": "true",
                "files_copied_by_qa": "false",
                "metadata_written_by_qa": "false",
                "manifest_modified_by_qa": "false",
                "source_files_modified_by_qa": "false",
                "real_dataset_generated": "false",
                "training_ready": "false",
            }
        )
        manifest_rows.append({"sample_id": source_id, "protein_pdb_path": str(source_protein), "ligand_sdf_path": f"raw/{source_id}.sdf"})
        manifest_rows.append({"sample_id": candidate_id, "protein_pdb_path": str(source_protein), "ligand_sdf_path": str(source_ligand)})
    _write_csv(paths["qa"], qa_rows, list(qa_rows[0]))
    _write_csv(paths["execution"], execution_rows, list(execution_rows[0]))
    _write_csv(paths["plan"], plan_rows, list(plan_rows[0]))
    _write_csv(paths["manifest"], manifest_rows, list(manifest_rows[0]))
    return paths, qa_rows, execution_rows, plan_rows, manifest_rows


def _run(paths):
    return build_design_review(
        packaging_qa_report_csv=paths["qa"],
        packaging_execution_report_csv=paths["execution"],
        execution_gate_plan_csv=paths["plan"],
        manifest_csv=paths["manifest"],
        package_root=paths["package_root"],
    )


def _report_for(rows, candidate_id):
    return next(row for row in rows if row["candidate_id"] == candidate_id)


def _hashes(paths):
    return {path: _sha(path) for path in paths}


def test_dataset_index_design_review_success(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, _, _, plan_rows, _ = _make_fixture(tmp_path)
    protected = [paths["qa"], paths["execution"], paths["plan"], paths["manifest"]]
    protected.extend(path for path in paths["package_root"].rglob("*") if path.is_file())
    before = _hashes(protected)

    reports, design_plan = _run(paths)
    write_csv(design_plan, paths["output_plan"], PLAN_COLUMNS)
    write_csv(reports, paths["output_report"], REPORT_COLUMNS)
    write_markdown(build_markdown(reports, design_plan, paths["package_root"]), paths["summary"])

    assert len(design_plan) == 3
    assert len(_read_csv(paths["output_plan"])) == 3
    assert len(_read_csv(paths["output_report"])) == 3
    assert "Dataset Index Design Review Summary" in paths["summary"].read_text(encoding="utf-8")
    for row in reports:
        assert row["dataset_index_design_review_status"] == "dataset_index_design_review_passed"
        assert row["design_plan_row_written"] == "true"
        assert row["actual_dataset_index_written"] == "false"
        assert row["real_dataset_generated"] == "false"
        assert row["training_ready"] == "false"
    for row in design_plan:
        assert row["intended_dataset_name"] == "covalent_small_pre_reaction_review_only"
        assert row["actual_dataset_index_written"] == "false"
        assert row["real_dataset_generated"] == "false"
        assert row["training_ready"] == "false"
        original = next(plan for plan in plan_rows if plan["execution_gate_plan_id"] == row["dataset_index_design_plan_id"])
        assert row["packaged_protein_sha256"] == _sha(Path(original["planned_protein_destination_path"]))
        assert row["packaged_ligand_sha256"] == _sha(Path(original["planned_ligand_destination_path"]))
    assert _hashes(protected) == before
    assert not list(tmp_path.rglob("*.pt"))
    assert not list(tmp_path.rglob("*.pkl"))
    assert not list(tmp_path.rglob("*.npz"))
    assert not list(tmp_path.rglob("*.lmdb"))
    assert not list(tmp_path.rglob("*.tar"))
    assert not list(tmp_path.rglob("*.zip"))
    assert not list(tmp_path.rglob("*.tgz"))


@pytest.mark.parametrize(
    "mutator,field,reason",
    [
        (lambda paths, qa, exe, plan, manifest: __import__("shutil").rmtree(paths["package_root"]), "package_root_exists", "package_root_missing"),
        (lambda paths, qa, exe, plan, manifest: (paths["package_root"] / "proteins" / "extra.pdb").write_text("x\n", encoding="utf-8"), "package_file_counts_valid", "package_file_counts_invalid"),
        (lambda paths, qa, exe, plan, manifest: qa.pop(), "packaging_qa_report_row_found_once", "packaging_qa_report_row_not_found_once"),
        (lambda paths, qa, exe, plan, manifest: exe.pop(), "packaging_execution_report_row_found_once", "packaging_execution_report_row_not_found_once"),
        (lambda paths, qa, exe, plan, manifest: plan.pop(), "execution_gate_plan_row_found_once", "execution_gate_plan_row_not_found_once"),
        (lambda paths, qa, exe, plan, manifest: qa.__setitem__(0, {**qa[0], "real_packaging_execution_qa_status": "blocked"}), "packaging_qa_status_passed", "packaging_qa_status_not_passed"),
        (lambda paths, qa, exe, plan, manifest: qa.__setitem__(0, {**qa[0], "training_ready": "true"}), "packaging_qa_flags_passed", "packaging_qa_flags_not_passed"),
        (lambda paths, qa, exe, plan, manifest: exe.__setitem__(0, {**exe[0], "real_packaging_execution_status": "blocked"}), "packaging_execution_status_passed", "packaging_execution_status_not_passed"),
        (lambda paths, qa, exe, plan, manifest: Path(plan[0]["planned_protein_destination_path"]).unlink(), "packaged_files_exist", "packaged_files_missing"),
        (lambda paths, qa, exe, plan, manifest: Path(plan[0]["planned_ligand_destination_path"]).unlink(), "packaged_files_exist", "packaged_files_missing"),
        (lambda paths, qa, exe, plan, manifest: Path(plan[0]["planned_metadata_destination_path"]).unlink(), "packaged_files_exist", "packaged_files_missing"),
        (lambda paths, qa, exe, plan, manifest: Path(plan[0]["planned_metadata_destination_path"]).write_text("{bad json", encoding="utf-8"), "metadata_json_parseable", "metadata_json_not_parseable"),
        (lambda paths, qa, exe, plan, manifest: _mutate_metadata(plan[0], {"sample_id": "wrong"}), "metadata_ids_valid", "metadata_ids_invalid"),
        (lambda paths, qa, exe, plan, manifest: _mutate_metadata(plan[0], {"protein": {"source_path": "wrong"}}), "metadata_paths_valid", "metadata_paths_invalid"),
        (lambda paths, qa, exe, plan, manifest: _mutate_metadata(plan[0], {"ligand": {"sha256": "wrong"}}), "metadata_hashes_valid", "metadata_hashes_invalid"),
        (lambda paths, qa, exe, plan, manifest: _mutate_metadata(plan[0], {"safety_flags": {"training_ready": True}}), "metadata_safety_flags_valid", "metadata_safety_flags_invalid"),
        (lambda paths, qa, exe, plan, manifest: manifest.__setitem__(1, {**manifest[1], "ligand_sdf_path": "wrong.sdf"}), "manifest_paths_match_sources", "manifest_paths_mismatch_sources"),
        (lambda paths, qa, exe, plan, manifest: plan.__setitem__(0, {**plan[0], "ligand_atom_count": "0"}), "graph_counts_positive", "graph_counts_not_positive"),
        (lambda paths, qa, exe, plan, manifest: plan.__setitem__(0, {**plan[0], "warhead_atoms": ""}), "mask_label_fields_present", "mask_label_fields_missing"),
        (lambda paths, qa, exe, plan, manifest: (paths["package_root"] / "bad.pt").write_text("x\n", encoding="utf-8"), "forbidden_training_tensors_absent", "forbidden_training_tensors_present"),
        (lambda paths, qa, exe, plan, manifest: (paths["package_root"] / "bad.tgz").write_text("x\n", encoding="utf-8"), "forbidden_archives_absent", "forbidden_archives_present"),
    ],
)
def test_dataset_index_design_review_blockers(tmp_path, monkeypatch, mutator, field, reason):
    monkeypatch.chdir(tmp_path)
    paths, qa, execution, plan, manifest = _make_fixture(tmp_path)
    mutator(paths, qa, execution, plan, manifest)
    _write_csv(paths["qa"], qa, list(qa[0]) if qa else ["candidate_id"])
    _write_csv(paths["execution"], execution, list(execution[0]) if execution else ["candidate_id"])
    _write_csv(paths["plan"], plan, list(plan[0]) if plan else ["execution_gate_plan_id"])
    _write_csv(paths["manifest"], manifest, ["sample_id", "protein_pdb_path", "ligand_sdf_path"])

    reports, design_plan = _run(paths)

    assert any(row[field] == "false" for row in reports)
    assert any(reason in row["blocking_reasons"] for row in reports)
    assert any(row["dataset_index_design_review_status"] == "blocked" for row in reports)
    assert all(row["training_ready"] == "false" for row in reports)
    assert len(design_plan) < 3


def _mutate_metadata(plan, patch):
    path = Path(plan["planned_metadata_destination_path"])
    data = json.loads(path.read_text(encoding="utf-8"))
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(data.get(key), dict):
            data[key].update(value)
        else:
            data[key] = value
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_dataset_index_design_review_does_not_write_outputs_by_itself(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, _, _, _, _ = _make_fixture(tmp_path)
    protected = [paths["qa"], paths["execution"], paths["plan"], paths["manifest"]]
    protected.extend(path for path in paths["package_root"].rglob("*") if path.is_file())
    before = _hashes(protected)

    reports, design_plan = _run(paths)

    assert len(reports) == 3
    assert len(design_plan) == 3
    assert _hashes(protected) == before
    assert not paths["output_plan"].exists()
    assert not paths["output_report"].exists()
    assert not paths["summary"].exists()
