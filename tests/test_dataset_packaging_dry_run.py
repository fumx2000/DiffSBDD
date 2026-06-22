import csv
import hashlib
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_dataset_packaging_dry_run import (  # noqa: E402
    PLAN_COLUMNS,
    REPORT_COLUMNS,
    TARGETS,
    build_markdown,
    build_packaging_dry_run,
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
        "candidates": base / "final_candidates.csv",
        "report": base / "final_report.csv",
        "manifest": tmp_path / "data" / "raw" / "covalent_small" / "manifests" / "manifest_real_small.csv",
        "plan": tmp_path / "out" / "plan.csv",
        "dry_report": tmp_path / "out" / "dry_report.csv",
        "summary": tmp_path / "out" / "summary.md",
    }


def _make_fixture(tmp_path):
    paths = _paths(tmp_path)
    candidates = []
    reports = []
    manifest = []
    for candidate_id, source_id in TARGETS.items():
        residue_id = "481" if source_id == "BTK_C481_6DI9" else "12"
        protein = Path(f"data/raw/covalent_small/proteins/{source_id}.pdb")
        ligand = Path(f"data/derived/covalent_small/ligands_pre_reaction/{candidate_id}.sdf")
        protein.parent.mkdir(parents=True, exist_ok=True)
        ligand.parent.mkdir(parents=True, exist_ok=True)
        protein.write_text(f"HEADER {source_id}\n", encoding="utf-8")
        ligand.write_text(f"{candidate_id}\n", encoding="utf-8")
        candidates.append(
            {
                "final_readiness_candidate_id": candidate_id,
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
                "ready_for_packaging_dry_run": "true",
                "training_ready": "false",
            }
        )
        reports.append(
            {
                "candidate_id": candidate_id,
                "final_readiness_status": "dataset_assembly_final_readiness_passed",
                "final_readiness_candidate_written": "true",
                "ready_for_packaging_dry_run": "true",
                "real_dataset_generated": "false",
                "training_ready": "false",
            }
        )
        manifest.append({"sample_id": source_id, "protein_pdb_path": str(protein), "ligand_sdf_path": f"raw/{source_id}.sdf"})
        manifest.append({"sample_id": candidate_id, "protein_pdb_path": str(protein), "ligand_sdf_path": str(ligand)})
    _write_csv(paths["candidates"], candidates, list(candidates[0]))
    _write_csv(paths["report"], reports, list(reports[0]))
    _write_csv(paths["manifest"], manifest, list(manifest[0]))
    return paths, candidates, reports, manifest


def _run(paths):
    return build_packaging_dry_run(
        final_readiness_candidates_csv=paths["candidates"],
        final_readiness_report_csv=paths["report"],
        manifest_csv=paths["manifest"],
    )


def _report_for(reports, candidate_id):
    return next(row for row in reports if row["candidate_id"] == candidate_id)


def test_packaging_dry_run_success_writes_three_plan_rows(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, candidates, _, _ = _make_fixture(tmp_path)
    manifest_hash = _sha(paths["manifest"])
    input_hashes = {row["protein_pdb_path"]: _sha(Path(row["protein_pdb_path"])) for row in candidates}
    input_hashes.update({row["ligand_sdf_path"]: _sha(Path(row["ligand_sdf_path"])) for row in candidates})

    reports, plan = _run(paths)
    write_csv(plan, paths["plan"], PLAN_COLUMNS)
    write_csv(reports, paths["dry_report"], REPORT_COLUMNS)
    write_markdown(build_markdown(reports, plan), paths["summary"])

    assert len(plan) == 3
    assert len(_read_csv(paths["plan"])) == 3
    assert len(_read_csv(paths["dry_report"])) == 3
    assert "Dataset Packaging Dry-Run Summary" in paths["summary"].read_text(encoding="utf-8")
    assert _sha(paths["manifest"]) == manifest_hash
    for row in reports:
        assert row["packaging_dry_run_status"] == "dataset_packaging_dry_run_passed"
        assert row["packaging_plan_row_written"] == "true"
        assert row["real_dataset_generated"] == "false"
        assert row["training_ready"] == "false"
        assert row["files_copied"] == "false"
        assert row["package_archive_created"] == "false"
    for row in plan:
        assert row["ready_for_real_packaging_later"] == "true"
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


def test_missing_or_duplicate_candidate_blocks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, candidates, _, _ = _make_fixture(tmp_path)
    candidate_id = "KRAS_G12C_5F2E_pre_reaction"
    _write_csv(paths["candidates"], [row for row in candidates if row["final_readiness_candidate_id"] != candidate_id], list(candidates[0]))

    reports, plan = _run(paths)

    assert "final_readiness_candidate_not_found_once" in _report_for(reports, candidate_id)["blocking_reasons"]
    assert candidate_id not in {row["packaging_plan_id"] for row in plan}

    paths, candidates, _, _ = _make_fixture(tmp_path)
    candidates.append(candidates[0].copy())
    _write_csv(paths["candidates"], candidates, list(candidates[0]))
    reports, _ = _run(paths)
    assert "final_readiness_candidate_not_found_once" in _report_for(reports, candidates[0]["final_readiness_candidate_id"])["blocking_reasons"]


@pytest.mark.parametrize(
    "mutator,reason",
    [
        (lambda rows, reports: reports.__setitem__(0, {**reports[0], "final_readiness_status": "blocked"}), "final_readiness_status_not_passed"),
        (lambda rows, reports: rows.__setitem__(0, {**rows[0], "ready_for_packaging_dry_run": "false"}), "ready_for_packaging_dry_run_not_true"),
        (lambda rows, reports: rows.__setitem__(0, {**rows[0], "ligand_atom_count": "0"}), "ligand_atom_count_not_positive"),
        (lambda rows, reports: rows.__setitem__(0, {**rows[0], "protein_atom_count": "0"}), "protein_atom_count_not_positive"),
        (lambda rows, reports: rows.__setitem__(0, {**rows[0], "reactive_residue_found": "false"}), "reactive_residue_not_found"),
        (lambda rows, reports: rows.__setitem__(0, {**rows[0], "reactive_atom_found": "false"}), "reactive_atom_not_found"),
    ],
)
def test_status_and_count_blockers(tmp_path, monkeypatch, mutator, reason):
    monkeypatch.chdir(tmp_path)
    paths, candidates, reports, _ = _make_fixture(tmp_path)
    mutator(candidates, reports)
    _write_csv(paths["candidates"], candidates, list(candidates[0]))
    _write_csv(paths["report"], reports, list(reports[0]))

    output_reports, _ = _run(paths)

    assert reason in _report_for(output_reports, candidates[0]["final_readiness_candidate_id"])["blocking_reasons"]


def test_current_hash_mismatch_blocks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, candidates, _, _ = _make_fixture(tmp_path)
    Path(candidates[0]["protein_pdb_path"]).write_text("changed\n", encoding="utf-8")
    Path(candidates[1]["ligand_sdf_path"]).write_text("changed\n", encoding="utf-8")

    reports, _ = _run(paths)

    assert "protein_pdb_sha256_mismatch" in _report_for(reports, candidates[0]["final_readiness_candidate_id"])["blocking_reasons"]
    assert "ligand_sdf_sha256_mismatch" in _report_for(reports, candidates[1]["final_readiness_candidate_id"])["blocking_reasons"]


def test_manifest_blockers(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, candidates, _, manifest = _make_fixture(tmp_path)
    candidate_id = "BTK_C481_6DI9_pre_reaction"
    source_id = TARGETS[candidate_id]
    for row in manifest:
        if row["sample_id"] == candidate_id:
            row["ligand_sdf_path"] = "wrong.sdf"
    manifest = [row for row in manifest if row["sample_id"] != source_id]
    _write_csv(paths["manifest"], manifest, ["sample_id", "protein_pdb_path", "ligand_sdf_path"])

    reports, _ = _run(paths)

    report = _report_for(reports, candidate_id)
    assert "manifest_source_row_not_found_once" in report["blocking_reasons"]
    assert "manifest_candidate_paths_mismatch_final_candidate" in report["blocking_reasons"]
