import csv
import hashlib
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_real_packaging_execution_gate import (  # noqa: E402
    PLAN_COLUMNS,
    PLANNED_PACKAGE_ROOT,
    REPORT_COLUMNS,
    TARGETS,
    build_execution_gate,
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
        "design_plan": base / "design_plan.csv",
        "design_report": base / "design_report.csv",
        "qa": base / "qa.csv",
        "manifest": tmp_path / "data" / "raw" / "covalent_small" / "manifests" / "manifest_real_small.csv",
        "execution_plan": tmp_path / "out" / "execution_plan.csv",
        "report": tmp_path / "out" / "report.csv",
        "summary": tmp_path / "out" / "summary.md",
    }


def _make_fixture(tmp_path):
    paths = _paths(tmp_path)
    design_plan = []
    design_report = []
    qa = []
    manifest = []
    for candidate_id, source_id in TARGETS.items():
        residue_id = "481" if source_id == "BTK_C481_6DI9" else "12"
        protein = Path(f"data/raw/covalent_small/proteins/{source_id}.pdb")
        ligand = Path(f"data/derived/covalent_small/ligands_pre_reaction/{candidate_id}.sdf")
        protein.parent.mkdir(parents=True, exist_ok=True)
        ligand.parent.mkdir(parents=True, exist_ok=True)
        protein.write_text(f"HEADER {source_id}\n", encoding="utf-8")
        ligand.write_text(f"{candidate_id}\n", encoding="utf-8")
        protein_rel = f"proteins/{source_id}.pdb"
        ligand_rel = f"ligands_pre_reaction/{candidate_id}.sdf"
        metadata_rel = f"metadata/{candidate_id}.json"
        design_plan.append(
            {
                "design_review_plan_id": candidate_id,
                "source_sample_id": source_id,
                "pre_reaction_sample_id": candidate_id,
                "planned_package_root": PLANNED_PACKAGE_ROOT,
                "planned_protein_relative_path": protein_rel,
                "planned_ligand_relative_path": ligand_rel,
                "planned_metadata_relative_path": metadata_rel,
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
            }
        )
        design_report.append(
            {
                "candidate_id": candidate_id,
                "design_review_status": "real_packaging_design_review_passed",
                "design_plan_row_written": "true",
                "ready_for_real_packaging_design_review": "true",
                "files_copied": "false",
                "package_archive_created": "false",
                "real_dataset_generated": "false",
                "training_ready": "false",
            }
        )
        qa.append(
            {
                "candidate_id": candidate_id,
                "packaging_dry_run_qa_status": "dataset_packaging_dry_run_qa_passed",
                "ready_for_real_packaging_planning_later": "true",
                "real_dataset_generated_false": "true",
                "training_ready": "false",
            }
        )
        manifest.append({"sample_id": source_id, "protein_pdb_path": str(protein), "ligand_sdf_path": f"raw/{source_id}.sdf"})
        manifest.append({"sample_id": candidate_id, "protein_pdb_path": str(protein), "ligand_sdf_path": str(ligand)})
    _write_csv(paths["design_plan"], design_plan, list(design_plan[0]))
    _write_csv(paths["design_report"], design_report, list(design_report[0]))
    _write_csv(paths["qa"], qa, list(qa[0]))
    _write_csv(paths["manifest"], manifest, list(manifest[0]))
    return paths, design_plan, design_report, qa, manifest


def _run(paths):
    return build_execution_gate(
        design_review_plan_csv=paths["design_plan"],
        design_review_report_csv=paths["design_report"],
        packaging_qa_report_csv=paths["qa"],
        manifest_csv=paths["manifest"],
    )


def _report_for(rows, candidate_id):
    return next(row for row in rows if row["candidate_id"] == candidate_id)


def test_real_packaging_execution_gate_success(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, design_plan, _, _, _ = _make_fixture(tmp_path)
    manifest_hash = _sha(paths["manifest"])
    input_hashes = {row["protein_pdb_path"]: _sha(Path(row["protein_pdb_path"])) for row in design_plan}
    input_hashes.update({row["ligand_sdf_path"]: _sha(Path(row["ligand_sdf_path"])) for row in design_plan})

    reports, execution_plan = _run(paths)
    write_csv(execution_plan, paths["execution_plan"], PLAN_COLUMNS)
    write_csv(reports, paths["report"], REPORT_COLUMNS)
    write_markdown(build_markdown(reports, execution_plan), paths["summary"])

    assert len(execution_plan) == 3
    assert len(_read_csv(paths["execution_plan"])) == 3
    assert len(_read_csv(paths["report"])) == 3
    assert "Real Packaging Execution Gate Summary" in paths["summary"].read_text(encoding="utf-8")
    assert _sha(paths["manifest"]) == manifest_hash
    for row in reports:
        assert row["execution_gate_status"] == "real_packaging_execution_gate_passed"
        assert row["explicit_approval_required_before_copy"] == "true"
        assert row["ready_for_real_packaging_execution_after_approval"] == "true"
        assert row["directories_created"] == "false"
        assert row["files_copied"] == "false"
        assert row["metadata_written"] == "false"
        assert row["package_archive_created"] == "false"
        assert row["real_dataset_generated"] == "false"
        assert row["training_ready"] == "false"
    for row in execution_plan:
        assert row["planned_protein_destination_path"] == f"{PLANNED_PACKAGE_ROOT}/{row['planned_protein_relative_path']}"
        assert row["planned_ligand_destination_path"] == f"{PLANNED_PACKAGE_ROOT}/{row['planned_ligand_relative_path']}"
        assert row["planned_metadata_destination_path"] == f"{PLANNED_PACKAGE_ROOT}/{row['planned_metadata_relative_path']}"
        assert row["explicit_approval_required_before_copy"] == "true"
        assert row["directories_created"] == "false"
        assert row["files_copied"] == "false"
        assert row["metadata_written"] == "false"
        assert row["package_archive_created"] == "false"
        assert row["real_dataset_generated"] == "false"
        assert row["training_ready"] == "false"
    for path_value, digest in input_hashes.items():
        assert _sha(Path(path_value)) == digest
    assert not Path(PLANNED_PACKAGE_ROOT).exists()
    assert not list(tmp_path.rglob("*.json"))
    assert not list(tmp_path.rglob("*.pt"))
    assert not list(tmp_path.rglob("*.pkl"))
    assert not list(tmp_path.rglob("*.npz"))
    assert not list(tmp_path.rglob("*.lmdb"))
    assert not list(tmp_path.rglob("*.tar"))
    assert not list(tmp_path.rglob("*.zip"))
    assert not list(tmp_path.rglob("*.tgz"))


@pytest.mark.parametrize(
    "table,path_key,id_key,reason",
    [
        ("design_plan", "design_plan", "design_review_plan_id", "design_plan_row_not_found_once"),
        ("design_report", "design_report", "candidate_id", "design_report_row_not_found_once"),
        ("qa", "qa", "candidate_id", "packaging_qa_report_row_not_found_once"),
    ],
)
def test_missing_upstream_rows_block(tmp_path, monkeypatch, table, path_key, id_key, reason):
    monkeypatch.chdir(tmp_path)
    paths, design_plan, design_report, qa, _ = _make_fixture(tmp_path)
    rows_by_name = {"design_plan": design_plan, "design_report": design_report, "qa": qa}
    candidate_id = "KRAS_G12C_5F2E_pre_reaction"
    rows = [row for row in rows_by_name[table] if row[id_key] != candidate_id]
    _write_csv(paths[path_key], rows, list(rows_by_name[table][0]))

    reports, execution_plan = _run(paths)

    assert reason in _report_for(reports, candidate_id)["blocking_reasons"]
    assert candidate_id not in {row["execution_gate_plan_id"] for row in execution_plan}


@pytest.mark.parametrize(
    "mutator,reason",
    [
        (lambda plan, report, qa: report.__setitem__(0, {**report[0], "design_review_status": "blocked"}), "design_review_status_not_passed"),
        (lambda plan, report, qa: report.__setitem__(0, {**report[0], "ready_for_real_packaging_design_review": "false"}), "ready_for_real_packaging_design_review_not_true"),
        (lambda plan, report, qa: qa.__setitem__(0, {**qa[0], "packaging_dry_run_qa_status": "blocked"}), "packaging_qa_status_not_passed"),
        (lambda plan, report, qa: plan.__setitem__(0, {**plan[0], "planned_package_root": "wrong"}), "planned_layout_invalid"),
        (lambda plan, report, qa: plan.__setitem__(0, {**plan[0], "source_sample_id": "wrong"}), "source_mapping_invalid"),
        (lambda plan, report, qa: plan.__setitem__(0, {**plan[0], "ligand_atom_count": "0"}), "graph_counts_not_positive"),
    ],
)
def test_execution_gate_blockers(tmp_path, monkeypatch, mutator, reason):
    monkeypatch.chdir(tmp_path)
    paths, design_plan, design_report, qa, _ = _make_fixture(tmp_path)
    mutator(design_plan, design_report, qa)
    _write_csv(paths["design_plan"], design_plan, list(design_plan[0]))
    _write_csv(paths["design_report"], design_report, list(design_report[0]))
    _write_csv(paths["qa"], qa, list(qa[0]))

    reports, _ = _run(paths)

    assert reason in _report_for(reports, design_plan[0]["design_review_plan_id"])["blocking_reasons"]


def test_current_hash_mismatch_blocks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, design_plan, _, _, _ = _make_fixture(tmp_path)
    Path(design_plan[0]["protein_pdb_path"]).write_text("changed\n", encoding="utf-8")
    Path(design_plan[1]["ligand_sdf_path"]).write_text("changed\n", encoding="utf-8")

    reports, _ = _run(paths)

    assert "current_protein_hash_mismatch_design_plan" in _report_for(reports, design_plan[0]["design_review_plan_id"])["blocking_reasons"]
    assert "current_ligand_hash_mismatch_design_plan" in _report_for(reports, design_plan[1]["design_review_plan_id"])["blocking_reasons"]


def test_manifest_candidate_path_mismatch_blocks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, _, _, _, manifest = _make_fixture(tmp_path)
    candidate_id = "BTK_C481_6DI9_pre_reaction"
    for row in manifest:
        if row["sample_id"] == candidate_id:
            row["ligand_sdf_path"] = "wrong.sdf"
    _write_csv(paths["manifest"], manifest, ["sample_id", "protein_pdb_path", "ligand_sdf_path"])

    reports, _ = _run(paths)

    assert "manifest_candidate_paths_mismatch_design_plan" in _report_for(reports, candidate_id)["blocking_reasons"]
