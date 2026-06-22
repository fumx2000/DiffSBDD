import csv
import hashlib
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_dataset_packaging_dry_run_qa import (  # noqa: E402
    REPORT_COLUMNS,
    TARGETS,
    build_markdown,
    build_qa,
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
        "plan": base / "plan.csv",
        "packaging_report": base / "packaging_report.csv",
        "final": base / "final.csv",
        "manifest": tmp_path / "data" / "raw" / "covalent_small" / "manifests" / "manifest_real_small.csv",
        "qa_report": tmp_path / "out" / "qa_report.csv",
        "summary": tmp_path / "out" / "summary.md",
    }


def _make_fixture(tmp_path):
    paths = _paths(tmp_path)
    plan = []
    packaging_report = []
    final = []
    manifest = []
    for candidate_id, source_id in TARGETS.items():
        residue_id = "481" if source_id == "BTK_C481_6DI9" else "12"
        protein = Path(f"data/raw/covalent_small/proteins/{source_id}.pdb")
        ligand = Path(f"data/derived/covalent_small/ligands_pre_reaction/{candidate_id}.sdf")
        protein.parent.mkdir(parents=True, exist_ok=True)
        ligand.parent.mkdir(parents=True, exist_ok=True)
        protein.write_text(f"HEADER {source_id}\n", encoding="utf-8")
        ligand.write_text(f"{candidate_id}\n", encoding="utf-8")
        common = {
            "source_sample_id": source_id,
            "pre_reaction_sample_id": candidate_id,
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
            "reactive_residue_found": "true",
            "reactive_atom_found": "true",
            "ligand_reactive_atom_id": "7",
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
            "graph_preview_stage": "graph_preview_candidate_only_not_training",
            "final_readiness_stage": "final_readiness_passed_candidate_only_not_training",
            "training_ready": "false",
        }
        plan.append(
            {
                "packaging_plan_id": candidate_id,
                **common,
                "packaging_dry_run_stage": "packaging_dry_run_plan_only_not_training",
                "ready_for_real_packaging_later": "true",
                "real_dataset_generated": "false",
            }
        )
        final.append({"final_readiness_candidate_id": candidate_id, **common, "ready_for_packaging_dry_run": "true"})
        packaging_report.append(
            {
                "candidate_id": candidate_id,
                "packaging_dry_run_status": "dataset_packaging_dry_run_passed",
                "packaging_plan_row_written": "true",
                "files_copied": "false",
                "package_archive_created": "false",
                "manifest_modified": "false",
                "sdf_modified": "false",
                "sdf_generated": "false",
                "real_dataset_generated": "false",
                "training_ready": "false",
            }
        )
        manifest.append({"sample_id": source_id, "protein_pdb_path": str(protein), "ligand_sdf_path": f"raw/{source_id}.sdf"})
        manifest.append({"sample_id": candidate_id, "protein_pdb_path": str(protein), "ligand_sdf_path": str(ligand)})
    _write_csv(paths["plan"], plan, list(plan[0]))
    _write_csv(paths["packaging_report"], packaging_report, list(packaging_report[0]))
    _write_csv(paths["final"], final, list(final[0]))
    _write_csv(paths["manifest"], manifest, list(manifest[0]))
    return paths, plan, packaging_report, final, manifest


def _run(paths):
    return build_qa(
        packaging_plan_csv=paths["plan"],
        packaging_report_csv=paths["packaging_report"],
        final_readiness_candidates_csv=paths["final"],
        manifest_csv=paths["manifest"],
    )


def _report_for(rows, candidate_id):
    return next(row for row in rows if row["candidate_id"] == candidate_id)


def test_packaging_dry_run_qa_success(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, plan, _, _, _ = _make_fixture(tmp_path)
    manifest_hash = _sha(paths["manifest"])
    input_hashes = {row["protein_pdb_path"]: _sha(Path(row["protein_pdb_path"])) for row in plan}
    input_hashes.update({row["ligand_sdf_path"]: _sha(Path(row["ligand_sdf_path"])) for row in plan})

    reports = _run(paths)
    write_csv(reports, paths["qa_report"], REPORT_COLUMNS)
    write_markdown(build_markdown(reports), paths["summary"])

    assert len(reports) == 3
    assert len(_read_csv(paths["qa_report"])) == 3
    assert "Dataset Packaging Dry-Run QA Summary" in paths["summary"].read_text(encoding="utf-8")
    assert _sha(paths["manifest"]) == manifest_hash
    for row in reports:
        assert row["packaging_dry_run_qa_status"] == "dataset_packaging_dry_run_qa_passed"
        assert row["ready_for_real_packaging_planning_later"] == "true"
        assert row["real_dataset_generated_false"] == "true"
        assert row["training_ready"] == "false"
        assert row["files_copied_false"] == "true"
        assert row["package_archive_created_false"] == "true"
    for path_value, digest in input_hashes.items():
        assert _sha(Path(path_value)) == digest
    assert not list(tmp_path.rglob("*.pt"))
    assert not list(tmp_path.rglob("*.pkl"))
    assert not list(tmp_path.rglob("*.npz"))
    assert not list(tmp_path.rglob("*.lmdb"))
    assert not list(tmp_path.rglob("*.tar"))
    assert not list(tmp_path.rglob("*.zip"))
    assert not list(tmp_path.rglob("*.tgz"))


def test_missing_or_duplicate_plan_row_blocks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, plan, _, _, _ = _make_fixture(tmp_path)
    candidate_id = "KRAS_G12C_5F2E_pre_reaction"
    _write_csv(paths["plan"], [row for row in plan if row["packaging_plan_id"] != candidate_id], list(plan[0]))
    reports = _run(paths)
    assert "packaging_plan_row_not_found_once" in _report_for(reports, candidate_id)["blocking_reasons"]

    paths, plan, _, _, _ = _make_fixture(tmp_path)
    plan.append(plan[0].copy())
    _write_csv(paths["plan"], plan, list(plan[0]))
    reports = _run(paths)
    assert "packaging_plan_row_not_found_once" in _report_for(reports, plan[0]["packaging_plan_id"])["blocking_reasons"]


@pytest.mark.parametrize(
    "table_name,path_key,id_key,reason",
    [
        ("packaging_report", "packaging_report", "candidate_id", "packaging_report_row_not_found_once"),
        ("final", "final", "final_readiness_candidate_id", "final_readiness_candidate_not_found_once"),
    ],
)
def test_missing_required_upstream_rows_block(tmp_path, monkeypatch, table_name, path_key, id_key, reason):
    monkeypatch.chdir(tmp_path)
    paths, plan, packaging_report, final, _ = _make_fixture(tmp_path)
    rows = packaging_report if table_name == "packaging_report" else final
    candidate_id = "BTK_C481_6DI9_pre_reaction"
    rows = [row for row in rows if row[id_key] != candidate_id]
    _write_csv(paths[path_key], rows, list((packaging_report if table_name == "packaging_report" else final)[0]))

    reports = _run(paths)

    assert reason in _report_for(reports, candidate_id)["blocking_reasons"]


@pytest.mark.parametrize(
    "mutator,reason",
    [
        (lambda plan, report, final: plan.__setitem__(0, {**plan[0], "source_sample_id": "wrong"}), "source_mapping_invalid"),
        (lambda plan, report, final: plan.__setitem__(0, {**plan[0], "protein_pdb_path": "wrong.pdb"}), "path_consistency_failed"),
        (lambda plan, report, final: plan.__setitem__(0, {**plan[0], "protein_pdb_sha256": "bad"}), "hash_consistency_failed"),
        (lambda plan, report, final: report.__setitem__(0, {**report[0], "packaging_dry_run_status": "blocked"}), "packaging_dry_run_status_not_passed"),
        (lambda plan, report, final: report.__setitem__(0, {**report[0], "files_copied": "true"}), "files_copied_not_false"),
        (lambda plan, report, final: report.__setitem__(0, {**report[0], "package_archive_created": "true"}), "package_archive_created_not_false"),
        (lambda plan, report, final: report.__setitem__(0, {**report[0], "real_dataset_generated": "true"}), "report_real_dataset_generated_not_false"),
        (lambda plan, report, final: report.__setitem__(0, {**report[0], "training_ready": "true"}), "report_training_ready_not_false"),
        (lambda plan, report, final: plan.__setitem__(0, {**plan[0], "ligand_atom_count": "0"}), "graph_counts_not_positive"),
        (lambda plan, report, final: plan.__setitem__(0, {**plan[0], "reactive_residue_found": "false"}), "reactive_residue_not_found"),
        (lambda plan, report, final: plan.__setitem__(0, {**plan[0], "reactive_atom_found": "false"}), "reactive_atom_not_found"),
    ],
)
def test_qa_blockers(tmp_path, monkeypatch, mutator, reason):
    monkeypatch.chdir(tmp_path)
    paths, plan, packaging_report, final, _ = _make_fixture(tmp_path)
    mutator(plan, packaging_report, final)
    _write_csv(paths["plan"], plan, list(plan[0]))
    _write_csv(paths["packaging_report"], packaging_report, list(packaging_report[0]))
    _write_csv(paths["final"], final, list(final[0]))

    reports = _run(paths)

    assert reason in _report_for(reports, plan[0]["packaging_plan_id"])["blocking_reasons"]


def test_current_hash_mismatch_blocks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, plan, _, _, _ = _make_fixture(tmp_path)
    Path(plan[0]["protein_pdb_path"]).write_text("changed\n", encoding="utf-8")
    Path(plan[1]["ligand_sdf_path"]).write_text("changed\n", encoding="utf-8")

    reports = _run(paths)

    assert "current_protein_hash_mismatch_plan" in _report_for(reports, plan[0]["packaging_plan_id"])["blocking_reasons"]
    assert "current_ligand_hash_mismatch_plan" in _report_for(reports, plan[1]["packaging_plan_id"])["blocking_reasons"]


def test_manifest_path_and_source_blockers(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, _, _, _, manifest = _make_fixture(tmp_path)
    candidate_id = "KRAS_G12C_6OIM_pre_reaction"
    source_id = TARGETS[candidate_id]
    for row in manifest:
        if row["sample_id"] == candidate_id:
            row["ligand_sdf_path"] = "wrong.sdf"
    manifest = [row for row in manifest if row["sample_id"] != source_id]
    _write_csv(paths["manifest"], manifest, ["sample_id", "protein_pdb_path", "ligand_sdf_path"])

    reports = _run(paths)

    report = _report_for(reports, candidate_id)
    assert "manifest_source_row_not_found_once" in report["blocking_reasons"]
    assert "manifest_candidate_paths_mismatch_plan" in report["blocking_reasons"]
