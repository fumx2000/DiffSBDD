import csv
import hashlib
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_dataset_index_build_gate import (  # noqa: E402
    INTENDED_DATASET_NAME,
    INTENDED_DATASET_ROLE,
    INTENDED_SPLIT,
    PLAN_COLUMNS,
    PLANNED_DATASET_INDEX_PATH,
    PLANNED_DATASET_MANIFEST_PATH,
    PLANNED_INDEX_ROOT,
    REPORT_COLUMNS,
    SCHEMA_VERSION,
    TARGETS,
    build_gate,
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
        "design_plan": base / "dataset_index_design_review_plan.csv",
        "design_report": base / "dataset_index_design_review_report.csv",
        "qa": base / "real_packaging_execution_qa_report.csv",
        "manifest": tmp_path / "data" / "raw" / "covalent_small" / "manifests" / "manifest_real_small.csv",
        "output_plan": base / "dataset_index_build_gate_plan.csv",
        "output_report": base / "dataset_index_build_gate_report.csv",
        "summary": tmp_path / "docs" / "dataset_index_build_gate_summary.md",
        "package_root": tmp_path / PACKAGE_ROOT,
    }


def _make_fixture(tmp_path):
    paths = _paths(tmp_path)
    design_plan = []
    design_report = []
    qa = []
    manifest = []
    for candidate_id, source_id in TARGETS.items():
        residue_id = "481" if source_id == "BTK_C481_6DI9" else "12"
        source_protein = tmp_path / "data" / "raw" / "covalent_small" / "proteins" / f"{source_id}.pdb"
        source_ligand = tmp_path / "data" / "derived" / "covalent_small" / "ligands_pre_reaction" / f"{candidate_id}.sdf"
        packaged_protein = tmp_path / PACKAGE_ROOT / "proteins" / f"{source_id}.pdb"
        packaged_ligand = tmp_path / PACKAGE_ROOT / "ligands_pre_reaction" / f"{candidate_id}.sdf"
        packaged_metadata = tmp_path / PACKAGE_ROOT / "metadata" / f"{candidate_id}.json"
        for path in [source_protein, source_ligand, packaged_protein, packaged_ligand, packaged_metadata]:
            path.parent.mkdir(parents=True, exist_ok=True)
        source_protein.write_text(f"HEADER {source_id}\n", encoding="utf-8")
        source_ligand.write_text(f"{candidate_id}\n", encoding="utf-8")
        packaged_protein.write_bytes(source_protein.read_bytes())
        packaged_ligand.write_bytes(source_ligand.read_bytes())
        packaged_metadata.write_text(f'{{"sample_id":"{candidate_id}"}}\n', encoding="utf-8")
        common = {
            "source_sample_id": source_id,
            "pre_reaction_sample_id": candidate_id,
            "intended_dataset_name": INTENDED_DATASET_NAME,
            "intended_dataset_role": INTENDED_DATASET_ROLE,
            "intended_split": INTENDED_SPLIT,
            "planned_index_schema_version": SCHEMA_VERSION,
            "packaged_protein_path": str(PACKAGE_ROOT / "proteins" / f"{source_id}.pdb"),
            "packaged_ligand_sdf_path": str(PACKAGE_ROOT / "ligands_pre_reaction" / f"{candidate_id}.sdf"),
            "packaged_metadata_json_path": str(PACKAGE_ROOT / "metadata" / f"{candidate_id}.json"),
            "source_protein_path": str(source_protein),
            "source_ligand_sdf_path": str(source_ligand),
            "packaged_protein_sha256": _sha(packaged_protein),
            "packaged_ligand_sha256": _sha(packaged_ligand),
            "packaged_metadata_sha256": _sha(packaged_metadata),
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
            "supported_mask_levels": "A_warhead_only;B_linker_warhead;B2_scaffold_warhead;C_scaffold_linker_warhead",
            "required_auxiliary_labels": "warhead_type;ligand_reactive_atom_id;protein_reactive_residue;pre_reaction_geometry_label",
            "actual_dataset_index_written": "false",
            "real_dataset_generated": "false",
            "pre_reaction_transform_ready": "false",
            "training_ready": "false",
        }
        design_plan.append(
            {
                "dataset_index_design_plan_id": candidate_id,
                "package_root": str(PACKAGE_ROOT),
                **common,
                "ready_for_dataset_index_build_gate": "true",
            }
        )
        design_report.append(
            {
                "candidate_id": candidate_id,
                **common,
                "dataset_index_design_review_status": "dataset_index_design_review_passed",
                "design_plan_row_written": "true",
                "recommended_next_action": "prepare_dataset_index_build_gate_not_training",
            }
        )
        qa.append(
            {
                "candidate_id": candidate_id,
                "source_sample_id": source_id,
                "pre_reaction_sample_id": candidate_id,
                "real_packaging_execution_qa_status": "real_packaging_execution_qa_passed",
                "real_dataset_generated": "false",
                "training_ready": "false",
            }
        )
        manifest.append({"sample_id": source_id, "protein_pdb_path": str(source_protein), "ligand_sdf_path": f"raw/{source_id}.sdf"})
        manifest.append({"sample_id": candidate_id, "protein_pdb_path": str(source_protein), "ligand_sdf_path": str(source_ligand)})
    _write_csv(paths["design_plan"], design_plan, list(design_plan[0]))
    _write_csv(paths["design_report"], design_report, list(design_report[0]))
    _write_csv(paths["qa"], qa, list(qa[0]))
    _write_csv(paths["manifest"], manifest, list(manifest[0]))
    return paths, design_plan, design_report, qa, manifest


def _run(paths):
    return build_gate(
        dataset_index_design_plan_csv=paths["design_plan"],
        dataset_index_design_report_csv=paths["design_report"],
        packaging_qa_report_csv=paths["qa"],
        manifest_csv=paths["manifest"],
        package_root=paths["package_root"],
    )


def _hashes(paths):
    return {path: _sha(path) for path in paths}


def test_dataset_index_build_gate_success(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, design_plan, _, _, _ = _make_fixture(tmp_path)
    protected = [paths["design_plan"], paths["design_report"], paths["qa"], paths["manifest"]]
    protected.extend(path for path in paths["package_root"].rglob("*") if path.is_file())
    before = _hashes(protected)

    reports, gate_plan = _run(paths)
    write_csv(gate_plan, paths["output_plan"], PLAN_COLUMNS)
    write_csv(reports, paths["output_report"], REPORT_COLUMNS)
    write_markdown(build_markdown(reports, gate_plan), paths["summary"])

    assert len(gate_plan) == 3
    assert len(_read_csv(paths["output_plan"])) == 3
    assert len(_read_csv(paths["output_report"])) == 3
    assert "Dataset Index Build Gate Summary" in paths["summary"].read_text(encoding="utf-8")
    for row in reports:
        assert row["dataset_index_build_gate_status"] == "dataset_index_build_gate_passed"
        assert row["build_gate_plan_row_written"] == "true"
        assert row["explicit_approval_required_before_index_write"] == "true"
        assert row["ready_for_actual_dataset_index_build_after_approval"] == "true"
        assert row["actual_dataset_index_written"] == "false"
        assert row["dataset_manifest_written"] == "false"
        assert row["real_dataset_generated"] == "false"
        assert row["training_ready"] == "false"
    for row in gate_plan:
        assert row["planned_index_root"] == PLANNED_INDEX_ROOT
        assert row["planned_dataset_index_path"] == PLANNED_DATASET_INDEX_PATH
        assert row["planned_dataset_manifest_path"] == PLANNED_DATASET_MANIFEST_PATH
        assert row["explicit_approval_required_before_index_write"] == "true"
        assert row["actual_dataset_index_written"] == "false"
        assert row["dataset_manifest_written"] == "false"
    assert _hashes(protected) == before
    assert not Path(PLANNED_DATASET_INDEX_PATH).exists()
    assert not Path(PLANNED_DATASET_MANIFEST_PATH).exists()
    assert not list(tmp_path.rglob("*.pt"))
    assert not list(tmp_path.rglob("*.pkl"))
    assert not list(tmp_path.rglob("*.npz"))
    assert not list(tmp_path.rglob("*.lmdb"))
    assert not list(tmp_path.rglob("*.tar"))
    assert not list(tmp_path.rglob("*.zip"))
    assert not list(tmp_path.rglob("*.tgz"))
    assert {row["dataset_index_build_gate_plan_id"] for row in gate_plan} == {
        row["dataset_index_design_plan_id"] for row in design_plan
    }


@pytest.mark.parametrize(
    "mutator,field,reason",
    [
        (lambda paths, plan, report, qa, manifest: __import__("shutil").rmtree(paths["package_root"]), "package_root_exists", "package_root_missing"),
        (lambda paths, plan, report, qa, manifest: (paths["package_root"] / "proteins" / "extra.pdb").write_text("x\n", encoding="utf-8"), "package_file_counts_valid", "package_file_counts_invalid"),
        (lambda paths, plan, report, qa, manifest: plan.pop(), "design_plan_row_found_once", "design_plan_row_not_found_once"),
        (lambda paths, plan, report, qa, manifest: report.pop(), "design_report_row_found_once", "design_report_row_not_found_once"),
        (lambda paths, plan, report, qa, manifest: qa.pop(), "packaging_qa_report_row_found_once", "packaging_qa_report_row_not_found_once"),
        (lambda paths, plan, report, qa, manifest: report.__setitem__(0, {**report[0], "dataset_index_design_review_status": "blocked"}), "design_review_status_passed", "design_review_status_not_passed"),
        (lambda paths, plan, report, qa, manifest: plan.__setitem__(0, {**plan[0], "ready_for_dataset_index_build_gate": "false"}), "design_plan_ready_for_build_gate", "design_plan_not_ready_for_build_gate"),
        (lambda paths, plan, report, qa, manifest: qa.__setitem__(0, {**qa[0], "real_packaging_execution_qa_status": "blocked"}), "packaging_qa_status_passed", "packaging_qa_status_not_passed"),
        (lambda paths, plan, report, qa, manifest: Path(plan[0]["packaged_protein_path"]).unlink(), "packaged_paths_exist", "packaged_paths_missing"),
        (lambda paths, plan, report, qa, manifest: plan.__setitem__(0, {**plan[0], "packaged_ligand_sha256": "bad"}), "packaged_hashes_match_design_plan", "packaged_hashes_mismatch_design_plan"),
        (lambda paths, plan, report, qa, manifest: plan.__setitem__(0, {**plan[0], "intended_dataset_name": "wrong"}), "planned_dataset_identity_valid", "planned_dataset_identity_invalid"),
        (lambda paths, plan, report, qa, manifest: plan.__setitem__(0, {**plan[0], "intended_dataset_role": "wrong"}), "planned_dataset_identity_valid", "planned_dataset_identity_invalid"),
        (lambda paths, plan, report, qa, manifest: plan.__setitem__(0, {**plan[0], "intended_split": "train"}), "planned_dataset_identity_valid", "planned_dataset_identity_invalid"),
        (lambda paths, plan, report, qa, manifest: plan.__setitem__(0, {**plan[0], "planned_index_schema_version": "wrong"}), "planned_dataset_identity_valid", "planned_dataset_identity_invalid"),
        (lambda paths, plan, report, qa, manifest: plan.__setitem__(0, {**plan[0], "supported_mask_levels": "A_warhead_only"}), "mask_levels_valid", "mask_levels_invalid"),
        (lambda paths, plan, report, qa, manifest: plan.__setitem__(0, {**plan[0], "required_auxiliary_labels": "warhead_type"}), "auxiliary_labels_valid", "auxiliary_labels_invalid"),
        (lambda paths, plan, report, qa, manifest: plan.__setitem__(0, {**plan[0], "protein_atom_count": "0"}), "graph_counts_positive", "graph_counts_not_positive"),
        (lambda paths, plan, report, qa, manifest: Path(PLANNED_DATASET_INDEX_PATH).parent.mkdir(parents=True, exist_ok=True) or Path(PLANNED_DATASET_INDEX_PATH).write_text("index\n", encoding="utf-8"), "actual_index_absent_before_gate", "actual_index_already_exists"),
        (lambda paths, plan, report, qa, manifest: Path(PLANNED_DATASET_MANIFEST_PATH).parent.mkdir(parents=True, exist_ok=True) or Path(PLANNED_DATASET_MANIFEST_PATH).write_text("{}\n", encoding="utf-8"), "dataset_manifest_absent_before_gate", "dataset_manifest_already_exists"),
        (lambda paths, plan, report, qa, manifest: (paths["package_root"] / "bad.pt").write_text("x\n", encoding="utf-8"), "forbidden_training_tensors_absent", "forbidden_training_tensors_present"),
        (lambda paths, plan, report, qa, manifest: (paths["package_root"] / "bad.tar").write_text("x\n", encoding="utf-8"), "forbidden_archives_absent", "forbidden_archives_present"),
    ],
)
def test_dataset_index_build_gate_blockers(tmp_path, monkeypatch, mutator, field, reason):
    monkeypatch.chdir(tmp_path)
    paths, design_plan, design_report, qa, manifest = _make_fixture(tmp_path)
    mutator(paths, design_plan, design_report, qa, manifest)
    _write_csv(paths["design_plan"], design_plan, list(design_plan[0]) if design_plan else ["dataset_index_design_plan_id"])
    _write_csv(paths["design_report"], design_report, list(design_report[0]) if design_report else ["candidate_id"])
    _write_csv(paths["qa"], qa, list(qa[0]) if qa else ["candidate_id"])
    _write_csv(paths["manifest"], manifest, ["sample_id", "protein_pdb_path", "ligand_sdf_path"])

    reports, gate_plan = _run(paths)

    assert any(row[field] == "false" for row in reports)
    assert any(reason in row["blocking_reasons"] for row in reports)
    assert any(row["dataset_index_build_gate_status"] == "blocked" for row in reports)
    assert all(row["training_ready"] == "false" for row in reports)
    assert len(gate_plan) < 3


def test_dataset_index_build_gate_does_not_write_outputs_by_itself(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, _, _, _, _ = _make_fixture(tmp_path)
    protected = [paths["design_plan"], paths["design_report"], paths["qa"], paths["manifest"]]
    protected.extend(path for path in paths["package_root"].rglob("*") if path.is_file())
    before = _hashes(protected)

    reports, gate_plan = _run(paths)

    assert len(reports) == 3
    assert len(gate_plan) == 3
    assert _hashes(protected) == before
    assert not paths["output_plan"].exists()
    assert not paths["output_report"].exists()
    assert not paths["summary"].exists()
    assert not Path(PLANNED_DATASET_INDEX_PATH).exists()
    assert not Path(PLANNED_DATASET_MANIFEST_PATH).exists()
