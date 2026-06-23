import csv
import hashlib
import json
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from apply_actual_dataset_index_build import (  # noqa: E402
    APPROVAL_TOKEN,
    INDEX_COLUMNS,
    PLANNED_INDEX_PATH,
    PLANNED_INDEX_ROOT,
    PLANNED_MANIFEST_PATH,
    REPORT_COLUMNS,
    TARGETS,
    apply_actual_dataset_index_build,
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
        "gate_plan": base / "dataset_index_build_gate_plan.csv",
        "gate_report": base / "dataset_index_build_gate_report.csv",
        "design_plan": base / "dataset_index_design_review_plan.csv",
        "design_report": base / "dataset_index_design_review_report.csv",
        "qa": base / "real_packaging_execution_qa_report.csv",
        "manifest": tmp_path / "data" / "raw" / "covalent_small" / "manifests" / "manifest_real_small.csv",
        "package_root": tmp_path / PACKAGE_ROOT,
        "output_index": Path(PLANNED_INDEX_PATH),
        "output_dataset_manifest": Path(PLANNED_MANIFEST_PATH),
        "output_report": base / "actual_dataset_index_build_report.csv",
        "summary": tmp_path / "docs" / "actual_dataset_index_build_summary.md",
    }


def _make_fixture(tmp_path):
    paths = _paths(tmp_path)
    gate_plan = []
    gate_report = []
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
            "intended_dataset_name": "covalent_small_pre_reaction_review_only",
            "intended_dataset_role": "smoke_test_pre_reaction_packaged_artifact",
            "intended_split": "smoke_test",
            "planned_index_schema_version": "dataset_index_v0_review_only",
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
            "real_dataset_generated": "false",
            "pre_reaction_transform_ready": "false",
            "training_ready": "false",
        }
        gate_plan.append(
            {
                "dataset_index_build_gate_plan_id": candidate_id,
                **common,
                "planned_index_root": PLANNED_INDEX_ROOT,
                "planned_dataset_index_path": PLANNED_INDEX_PATH,
                "planned_dataset_manifest_path": PLANNED_MANIFEST_PATH,
                "build_gate_stage": "dataset_index_build_gate_only_not_training",
                "explicit_approval_required_before_index_write": "true",
                "ready_for_actual_dataset_index_build_after_approval": "true",
                "actual_dataset_index_written": "false",
                "dataset_manifest_written": "false",
            }
        )
        gate_report.append(
            {
                "candidate_id": candidate_id,
                "source_sample_id": source_id,
                "pre_reaction_sample_id": candidate_id,
                "dataset_index_build_gate_status": "dataset_index_build_gate_passed",
                "build_gate_plan_row_written": "true",
                "explicit_approval_required_before_index_write": "true",
                "ready_for_actual_dataset_index_build_after_approval": "true",
                "actual_dataset_index_written": "false",
                "dataset_manifest_written": "false",
                "real_dataset_generated": "false",
                "training_ready": "false",
            }
        )
        design_plan.append({"dataset_index_design_plan_id": candidate_id, **common})
        design_report.append(
            {
                "candidate_id": candidate_id,
                "dataset_index_design_review_status": "dataset_index_design_review_passed",
                "actual_dataset_index_written": "false",
                "real_dataset_generated": "false",
                "training_ready": "false",
            }
        )
        qa.append(
            {
                "candidate_id": candidate_id,
                "real_packaging_execution_qa_status": "real_packaging_execution_qa_passed",
                "real_dataset_generated": "false",
                "training_ready": "false",
            }
        )
        manifest.append({"sample_id": source_id, "protein_pdb_path": str(source_protein), "ligand_sdf_path": f"raw/{source_id}.sdf"})
        manifest.append({"sample_id": candidate_id, "protein_pdb_path": str(source_protein), "ligand_sdf_path": str(source_ligand)})
    _write_csv(paths["gate_plan"], gate_plan, list(gate_plan[0]))
    _write_csv(paths["gate_report"], gate_report, list(gate_report[0]))
    _write_csv(paths["design_plan"], design_plan, list(design_plan[0]))
    _write_csv(paths["design_report"], design_report, list(design_report[0]))
    _write_csv(paths["qa"], qa, list(qa[0]))
    _write_csv(paths["manifest"], manifest, list(manifest[0]))
    return paths, gate_plan, gate_report, design_plan, design_report, qa, manifest


def _run(paths, token=APPROVAL_TOKEN):
    return apply_actual_dataset_index_build(
        dataset_index_build_gate_plan_csv=paths["gate_plan"],
        dataset_index_build_gate_report_csv=paths["gate_report"],
        dataset_index_design_plan_csv=paths["design_plan"],
        dataset_index_design_report_csv=paths["design_report"],
        packaging_qa_report_csv=paths["qa"],
        manifest_csv=paths["manifest"],
        package_root=paths["package_root"],
        output_index_csv=paths["output_index"],
        output_dataset_manifest_json=paths["output_dataset_manifest"],
        output_report_csv=paths["output_report"],
        output_md=paths["summary"],
        approval_token=token,
    )


def _hashes(paths):
    return {path: _sha(path) for path in paths}


def _protected(paths):
    values = [paths["manifest"], paths["gate_plan"], paths["gate_report"], paths["design_plan"], paths["design_report"], paths["qa"]]
    values.extend(path for path in paths["package_root"].rglob("*") if path.is_file())
    source_parent = paths["manifest"].parents[2]
    values.extend(path for path in source_parent.rglob("*") if path.is_file())
    return sorted(set(values))


def test_invalid_approval_token_blocks_without_index_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, *_ = _make_fixture(tmp_path)
    before = _hashes(_protected(paths))

    reports, exit_code = _run(paths, token="wrong")

    assert exit_code == 1
    assert len(reports) == 3
    assert all(row["approval_token_valid"] == "false" for row in reports)
    assert all(row["actual_dataset_index_build_status"] == "blocked" for row in reports)
    assert not paths["output_index"].exists()
    assert not paths["output_dataset_manifest"].exists()
    assert not paths["output_index"].parent.exists()
    assert _hashes(_protected(paths)) == before


def test_actual_dataset_index_build_success(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, gate_plan, *_ = _make_fixture(tmp_path)
    before = _hashes(_protected(paths))

    reports, exit_code = _run(paths)

    assert exit_code == 0
    assert len(reports) == 3
    assert paths["output_index"].exists()
    assert paths["output_dataset_manifest"].exists()
    assert len(_read_csv(paths["output_index"])) == 3
    assert len(_read_csv(paths["output_report"])) == 3
    manifest = json.loads(paths["output_dataset_manifest"].read_text(encoding="utf-8"))
    assert manifest["row_count"] == 3
    assert set(manifest["sample_ids"]) == {row["pre_reaction_sample_id"] for row in gate_plan}
    assert manifest["safety_flags"]["training_ready"] is False
    assert "Actual Dataset Index Build Summary" in paths["summary"].read_text(encoding="utf-8")
    for row in reports:
        assert row["actual_dataset_index_build_status"] == "actual_dataset_index_build_passed"
        assert row["index_csv_written"] == "true"
        assert row["dataset_manifest_written"] == "true"
        assert row["index_row_found_once"] == "true"
        assert row["index_row_fields_match_gate_plan"] == "true"
        assert row["index_row_hashes_match_files"] == "true"
        assert row["index_row_safety_flags_valid"] == "true"
        assert row["source_manifest_modified"] == "false"
        assert row["source_pdb_modified"] == "false"
        assert row["source_sdf_modified"] == "false"
        assert row["packaged_files_modified"] == "false"
        assert row["files_copied"] == "false"
        assert row["package_archive_created"] == "false"
        assert row["real_training_tensor_generated"] == "false"
        assert row["real_dataset_generated"] == "false"
        assert row["pre_reaction_transform_ready"] == "false"
        assert row["training_ready"] == "false"
    assert _hashes(_protected(paths)) == before
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
        (lambda paths, gp, gr, dp, dr, qa, manifest: gp.pop(), "build_gate_plan_row_found_once", "build_gate_plan_row_not_found_once"),
        (lambda paths, gp, gr, dp, dr, qa, manifest: gr.pop(), "build_gate_report_row_found_once", "build_gate_report_row_not_found_once"),
        (lambda paths, gp, gr, dp, dr, qa, manifest: gr.__setitem__(0, {**gr[0], "dataset_index_build_gate_status": "blocked"}), "build_gate_status_passed", "build_gate_status_not_passed"),
        (lambda paths, gp, gr, dp, dr, qa, manifest: gp.__setitem__(0, {**gp[0], "explicit_approval_required_before_index_write": "false"}), "explicit_approval_confirmed", "explicit_approval_not_confirmed"),
        (lambda paths, gp, gr, dp, dr, qa, manifest: Path(gp[0]["packaged_protein_path"]).unlink(), "packaged_paths_exist", "packaged_paths_missing"),
        (lambda paths, gp, gr, dp, dr, qa, manifest: gp.__setitem__(0, {**gp[0], "packaged_ligand_sha256": "bad"}), "packaged_hashes_match_gate_plan", "packaged_hashes_mismatch_gate_plan"),
        (lambda paths, gp, gr, dp, dr, qa, manifest: gp.__setitem__(0, {**gp[0], "supported_mask_levels": "A_warhead_only"}), "mask_levels_valid", "mask_levels_invalid"),
        (lambda paths, gp, gr, dp, dr, qa, manifest: gp.__setitem__(0, {**gp[0], "required_auxiliary_labels": "warhead_type"}), "auxiliary_labels_valid", "auxiliary_labels_invalid"),
        (lambda paths, gp, gr, dp, dr, qa, manifest: gp.__setitem__(0, {**gp[0], "ligand_atom_count": "0"}), "graph_counts_positive", "graph_counts_not_positive"),
        (lambda paths, gp, gr, dp, dr, qa, manifest: (paths["package_root"] / "bad.pt").write_text("x\n", encoding="utf-8"), "real_training_tensor_generated", "real_training_tensor_generated"),
        (lambda paths, gp, gr, dp, dr, qa, manifest: (paths["package_root"] / "bad.tar").write_text("x\n", encoding="utf-8"), "package_archive_created", "package_archive_created"),
    ],
)
def test_actual_dataset_index_build_blockers(tmp_path, monkeypatch, mutator, field, reason):
    monkeypatch.chdir(tmp_path)
    paths, gate_plan, gate_report, design_plan, design_report, qa, manifest = _make_fixture(tmp_path)
    mutator(paths, gate_plan, gate_report, design_plan, design_report, qa, manifest)
    _write_csv(paths["gate_plan"], gate_plan, list(gate_plan[0]) if gate_plan else ["dataset_index_build_gate_plan_id"])
    _write_csv(paths["gate_report"], gate_report, list(gate_report[0]) if gate_report else ["candidate_id"])
    _write_csv(paths["design_plan"], design_plan, list(design_plan[0]))
    _write_csv(paths["design_report"], design_report, list(design_report[0]))
    _write_csv(paths["qa"], qa, list(qa[0]))
    _write_csv(paths["manifest"], manifest, ["sample_id", "protein_pdb_path", "ligand_sdf_path"])

    reports, exit_code = _run(paths)

    assert exit_code == 1
    assert any(row[field] == "false" or row[field] == "true" and field in {"real_training_tensor_generated", "package_archive_created"} for row in reports)
    assert any(reason in row["blocking_reasons"] for row in reports)
    assert all(row["actual_dataset_index_build_status"] == "blocked" for row in reports)
    assert not paths["output_index"].exists()
    assert not paths["output_dataset_manifest"].exists()


def test_manifest_path_mismatch_blocks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, gate_plan, gate_report, design_plan, design_report, qa, manifest = _make_fixture(tmp_path)
    manifest[1]["ligand_sdf_path"] = "wrong.sdf"
    _write_csv(paths["manifest"], manifest, ["sample_id", "protein_pdb_path", "ligand_sdf_path"])

    reports, exit_code = _run(paths)

    assert exit_code == 1
    assert any("manifest_paths_mismatch_sources" in row["blocking_reasons"] for row in reports)
    assert not paths["output_index"].exists()
