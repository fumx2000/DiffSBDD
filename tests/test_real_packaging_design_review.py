import csv
import hashlib
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_real_packaging_design_review import (  # noqa: E402
    PLAN_COLUMNS,
    PLANNED_PACKAGE_ROOT,
    REPORT_COLUMNS,
    TARGETS,
    build_design_review,
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
        "qa": base / "qa.csv",
        "plan": base / "packaging_plan.csv",
        "final": base / "final.csv",
        "manifest": tmp_path / "data" / "raw" / "covalent_small" / "manifests" / "manifest_real_small.csv",
        "design_plan": tmp_path / "out" / "design_plan.csv",
        "report": tmp_path / "out" / "report.csv",
        "summary": tmp_path / "out" / "summary.md",
    }


def _make_fixture(tmp_path):
    paths = _paths(tmp_path)
    qa_rows = []
    plan_rows = []
    final_rows = []
    manifest_rows = []
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
            "training_ready": "false",
        }
        qa_rows.append(
            {
                "candidate_id": candidate_id,
                "packaging_dry_run_qa_status": "dataset_packaging_dry_run_qa_passed",
                "ready_for_real_packaging_planning_later": "true",
                "real_dataset_generated_false": "true",
                "training_ready": "false",
                "files_copied_false": "true",
                "package_archive_created_false": "true",
            }
        )
        plan_rows.append(
            {
                "packaging_plan_id": candidate_id,
                **common,
                "packaging_dry_run_stage": "packaging_dry_run_plan_only_not_training",
                "ready_for_real_packaging_later": "true",
                "real_dataset_generated": "false",
            }
        )
        final_rows.append(
            {
                "final_readiness_candidate_id": candidate_id,
                **common,
            }
        )
        manifest_rows.append({"sample_id": source_id, "protein_pdb_path": str(protein), "ligand_sdf_path": f"raw/{source_id}.sdf"})
        manifest_rows.append({"sample_id": candidate_id, "protein_pdb_path": str(protein), "ligand_sdf_path": str(ligand)})
    _write_csv(paths["qa"], qa_rows, list(qa_rows[0]))
    _write_csv(paths["plan"], plan_rows, list(plan_rows[0]))
    _write_csv(paths["final"], final_rows, list(final_rows[0]))
    _write_csv(paths["manifest"], manifest_rows, list(manifest_rows[0]))
    return paths, qa_rows, plan_rows, final_rows, manifest_rows


def _run(paths):
    return build_design_review(
        packaging_qa_report_csv=paths["qa"],
        packaging_plan_csv=paths["plan"],
        final_readiness_candidates_csv=paths["final"],
        manifest_csv=paths["manifest"],
    )


def _report_for(rows, candidate_id):
    return next(row for row in rows if row["candidate_id"] == candidate_id)


def test_real_packaging_design_review_success(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, _, plan_rows, _, _ = _make_fixture(tmp_path)
    manifest_hash = _sha(paths["manifest"])
    input_hashes = {row["protein_pdb_path"]: _sha(Path(row["protein_pdb_path"])) for row in plan_rows}
    input_hashes.update({row["ligand_sdf_path"]: _sha(Path(row["ligand_sdf_path"])) for row in plan_rows})

    reports, design_plan = _run(paths)
    write_csv(design_plan, paths["design_plan"], PLAN_COLUMNS)
    write_csv(reports, paths["report"], REPORT_COLUMNS)
    write_markdown(build_markdown(reports, design_plan), paths["summary"])

    assert len(design_plan) == 3
    assert len(_read_csv(paths["design_plan"])) == 3
    assert len(_read_csv(paths["report"])) == 3
    assert "Real Packaging Design Review Summary" in paths["summary"].read_text(encoding="utf-8")
    assert _sha(paths["manifest"]) == manifest_hash
    for row in reports:
        assert row["design_review_status"] == "real_packaging_design_review_passed"
        assert row["ready_for_real_packaging_design_review"] == "true"
        assert row["files_copied"] == "false"
        assert row["package_archive_created"] == "false"
        assert row["real_dataset_generated"] == "false"
        assert row["training_ready"] == "false"
    for row in design_plan:
        assert row["planned_package_root"] == PLANNED_PACKAGE_ROOT
        assert row["planned_protein_relative_path"] == f"proteins/{row['source_sample_id']}.pdb"
        assert row["planned_ligand_relative_path"] == f"ligands_pre_reaction/{row['pre_reaction_sample_id']}.sdf"
        assert row["planned_metadata_relative_path"] == f"metadata/{row['pre_reaction_sample_id']}.json"
        assert row["ready_for_real_packaging_design_review"] == "true"
        assert row["files_copied"] == "false"
        assert row["package_archive_created"] == "false"
        assert row["real_dataset_generated"] == "false"
        assert row["training_ready"] == "false"
    for path_value, digest in input_hashes.items():
        assert _sha(Path(path_value)) == digest
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
        ("qa", "qa", "candidate_id", "qa_report_row_not_found_once"),
        ("plan", "plan", "packaging_plan_id", "packaging_plan_row_not_found_once"),
        ("final", "final", "final_readiness_candidate_id", "final_readiness_candidate_not_found_once"),
    ],
)
def test_missing_upstream_rows_block(tmp_path, monkeypatch, table, path_key, id_key, reason):
    monkeypatch.chdir(tmp_path)
    paths, qa_rows, plan_rows, final_rows, _ = _make_fixture(tmp_path)
    rows_by_name = {"qa": qa_rows, "plan": plan_rows, "final": final_rows}
    candidate_id = "KRAS_G12C_5F2E_pre_reaction"
    rows = [row for row in rows_by_name[table] if row[id_key] != candidate_id]
    _write_csv(paths[path_key], rows, list(rows_by_name[table][0]))

    reports, design_plan = _run(paths)

    assert reason in _report_for(reports, candidate_id)["blocking_reasons"]
    assert candidate_id not in {row["design_review_plan_id"] for row in design_plan}


@pytest.mark.parametrize(
    "mutator,reason",
    [
        (lambda qa, plan, final: qa.__setitem__(0, {**qa[0], "packaging_dry_run_qa_status": "blocked"}), "qa_status_not_passed"),
        (lambda qa, plan, final: qa.__setitem__(0, {**qa[0], "ready_for_real_packaging_planning_later": "false"}), "ready_for_real_packaging_planning_later_not_true"),
        (lambda qa, plan, final: plan.__setitem__(0, {**plan[0], "source_sample_id": "wrong"}), "source_mapping_invalid"),
        (lambda qa, plan, final: plan.__setitem__(0, {**plan[0], "protein_pdb_path": "wrong.pdb"}), "path_consistency_failed"),
        (lambda qa, plan, final: plan.__setitem__(0, {**plan[0], "protein_pdb_sha256": "bad"}), "hash_consistency_failed"),
        (lambda qa, plan, final: plan.__setitem__(0, {**plan[0], "ligand_atom_count": "0"}), "graph_counts_not_positive"),
        (lambda qa, plan, final: plan.__setitem__(0, {**plan[0], "reactive_residue_found": "false"}), "reactive_residue_not_found"),
        (lambda qa, plan, final: plan.__setitem__(0, {**plan[0], "reactive_atom_found": "false"}), "reactive_atom_not_found"),
    ],
)
def test_design_review_blockers(tmp_path, monkeypatch, mutator, reason):
    monkeypatch.chdir(tmp_path)
    paths, qa_rows, plan_rows, final_rows, _ = _make_fixture(tmp_path)
    mutator(qa_rows, plan_rows, final_rows)
    _write_csv(paths["qa"], qa_rows, list(qa_rows[0]))
    _write_csv(paths["plan"], plan_rows, list(plan_rows[0]))
    _write_csv(paths["final"], final_rows, list(final_rows[0]))

    reports, _ = _run(paths)

    assert reason in _report_for(reports, plan_rows[0]["packaging_plan_id"])["blocking_reasons"]


def test_current_hash_mismatch_blocks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, _, plan_rows, _, _ = _make_fixture(tmp_path)
    Path(plan_rows[0]["protein_pdb_path"]).write_text("changed\n", encoding="utf-8")
    Path(plan_rows[1]["ligand_sdf_path"]).write_text("changed\n", encoding="utf-8")

    reports, _ = _run(paths)

    assert "current_protein_hash_mismatch_plan" in _report_for(reports, plan_rows[0]["packaging_plan_id"])["blocking_reasons"]
    assert "current_ligand_hash_mismatch_plan" in _report_for(reports, plan_rows[1]["packaging_plan_id"])["blocking_reasons"]


def test_manifest_candidate_path_mismatch_blocks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, _, _, _, manifest_rows = _make_fixture(tmp_path)
    candidate_id = "BTK_C481_6DI9_pre_reaction"
    source_id = TARGETS[candidate_id]
    for row in manifest_rows:
        if row["sample_id"] == candidate_id:
            row["ligand_sdf_path"] = "wrong.sdf"
    manifest_rows = [row for row in manifest_rows if row["sample_id"] != source_id]
    _write_csv(paths["manifest"], manifest_rows, ["sample_id", "protein_pdb_path", "ligand_sdf_path"])

    reports, _ = _run(paths)

    report = _report_for(reports, candidate_id)
    assert "manifest_source_row_not_found_once" in report["blocking_reasons"]
    assert "path_consistency_failed" in report["blocking_reasons"]
