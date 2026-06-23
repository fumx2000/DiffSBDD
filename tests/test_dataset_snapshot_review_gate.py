import argparse
import ast
import csv
import hashlib
import json
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_dataset_snapshot_review_gate import PLANNED_SNAPSHOT_ROOT, TARGETS, run  # noqa: E402


@pytest.fixture(autouse=True)
def _chdir_tmp_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _write_csv(path, rows, fieldnames=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _args(paths):
    return argparse.Namespace(
        loader_dry_run_qa_report_csv=paths["loader_qa"],
        loader_dry_run_report_csv=paths["loader_report"],
        loader_dry_run_gate_plan_csv=paths["loader_gate_plan"],
        loader_dry_run_gate_report_csv=paths["loader_gate_report"],
        actual_dataset_index_qa_report_csv=paths["index_qa"],
        index_csv=paths["index"],
        dataset_manifest_json=paths["dataset_manifest"],
        manifest_csv=paths["raw_manifest"],
        package_root=paths["package_root"],
        output_gate_plan_csv=paths["snapshot_gate_plan"],
        output_report_csv=paths["snapshot_gate_report"],
        output_md=paths["summary"],
    )


def _make_fixture(tmp_path):
    paths = {
        "loader_qa": tmp_path / "loader" / "read_only_dataset_loader_dry_run_qa_report.csv",
        "loader_report": tmp_path / "loader" / "read_only_dataset_loader_dry_run_report.csv",
        "loader_gate_plan": tmp_path / "pre" / "read_only_dataset_loader_dry_run_gate_plan.csv",
        "loader_gate_report": tmp_path / "pre" / "read_only_dataset_loader_dry_run_gate_report.csv",
        "index_qa": tmp_path / "pre" / "actual_dataset_index_qa_report.csv",
        "index": tmp_path / "index" / "index.csv",
        "dataset_manifest": tmp_path / "index" / "manifest.json",
        "raw_manifest": tmp_path / "raw" / "manifest_real_small.csv",
        "package_root": tmp_path / "package",
        "snapshot_gate_plan": tmp_path / "loader" / "dataset_snapshot_review_gate_plan.csv",
        "snapshot_gate_report": tmp_path / "loader" / "dataset_snapshot_review_gate_report.csv",
        "summary": tmp_path / "docs" / "dataset_snapshot_review_gate_summary.md",
    }
    loader_qa = []
    loader_report = []
    loader_gate_plan = []
    loader_gate_report = []
    index_qa = []
    index_rows = []
    raw_manifest = []
    sha = {"packaged_proteins": {}, "packaged_ligands": {}, "packaged_metadata": {}}
    for candidate_id, source_id in TARGETS.items():
        source_protein = tmp_path / "raw" / "proteins" / f"{source_id}.pdb"
        source_ligand = tmp_path / "raw" / "ligands" / f"{candidate_id}.sdf"
        source_base_ligand = tmp_path / "raw" / "ligands" / f"{source_id}.sdf"
        packaged_protein = paths["package_root"] / "proteins" / f"{source_id}.pdb"
        packaged_ligand = paths["package_root"] / "ligands_pre_reaction" / f"{candidate_id}.sdf"
        packaged_metadata = paths["package_root"] / "metadata" / f"{candidate_id}.json"
        for file_path in [source_protein, source_ligand, source_base_ligand, packaged_protein, packaged_ligand, packaged_metadata]:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        source_protein.write_text(f"HEADER {source_id}\nATOM 1 SG CYS A 12\n", encoding="utf-8")
        source_ligand.write_text(f"{candidate_id}\n$$$$\n", encoding="utf-8")
        source_base_ligand.write_text(f"{source_id}\n$$$$\n", encoding="utf-8")
        packaged_protein.write_bytes(source_protein.read_bytes())
        packaged_ligand.write_bytes(source_ligand.read_bytes())
        packaged_metadata.write_text(json.dumps({"sample_id": candidate_id}), encoding="utf-8")
        common_index = {
            "sample_id": candidate_id,
            "source_sample_id": source_id,
            "pre_reaction_sample_id": candidate_id,
            "dataset_name": "covalent_small_pre_reaction_review_only",
            "dataset_role": "smoke_test_pre_reaction_packaged_artifact",
            "split": "smoke_test",
            "schema_version": "dataset_index_v0_review_only",
            "package_root": str(paths["package_root"]),
            "packaged_protein_path": str(packaged_protein),
            "packaged_ligand_sdf_path": str(packaged_ligand),
            "packaged_metadata_json_path": str(packaged_metadata),
            "source_protein_path": str(source_protein),
            "source_ligand_sdf_path": str(source_ligand),
            "packaged_protein_sha256": _sha(packaged_protein),
            "packaged_ligand_sha256": _sha(packaged_ligand),
            "packaged_metadata_sha256": _sha(packaged_metadata),
            "ligand_atom_count": "4",
            "ligand_heavy_atom_count": "4",
            "ligand_bond_count": "3",
            "protein_atom_count": "8",
            "protein_residue_count": "1",
            "scaffold_atom_count": "1",
            "linker_atom_count": "1",
            "warhead_atom_count": "2",
            "supported_mask_levels": "A_warhead_only;B_linker_warhead;B2_scaffold_warhead;C_scaffold_linker_warhead",
            "required_auxiliary_labels": "warhead_type;ligand_reactive_atom_id;protein_reactive_residue;pre_reaction_geometry_label",
            "real_dataset_generated": "false",
            "pre_reaction_transform_ready": "false",
            "training_ready": "false",
        }
        index_rows.append(common_index)
        loader_qa.append(
            {
                "candidate_id": candidate_id,
                "read_only_dataset_loader_dry_run_qa_status": "read_only_dataset_loader_dry_run_qa_passed",
                "dry_run_status_passed": "true",
                "dry_run_readability_fields_valid": "true",
                "dry_run_record_fields_valid": "true",
                "packaged_hashes_still_match_index_and_manifest": "true",
                "torch_imported": "false",
                "checkpoint_loaded": "false",
                "model_initialized": "false",
                "dataloader_tensor_generated": "false",
                "files_copied": "false",
                "package_archive_created": "false",
                "real_training_tensor_generated": "false",
                "real_dataset_generated": "false",
                "pre_reaction_transform_ready": "false",
                "training_ready": "false",
            }
        )
        loader_report.append(
            {
                "candidate_id": candidate_id,
                "read_only_dataset_loader_dry_run_status": "read_only_dataset_loader_dry_run_passed",
                "loader_dry_run_executed": "true",
                "torch_imported": "false",
                "dataloader_tensor_generated": "false",
            }
        )
        loader_gate_plan.append({"loader_dry_run_gate_plan_id": candidate_id})
        loader_gate_report.append({"candidate_id": candidate_id, "read_only_dataset_loader_dry_run_gate_status": "read_only_dataset_loader_dry_run_gate_passed"})
        index_qa.append({"candidate_id": candidate_id, "actual_dataset_index_qa_status": "actual_dataset_index_qa_passed"})
        raw_manifest.append({"sample_id": source_id, "protein_pdb_path": str(source_protein), "ligand_sdf_path": str(source_base_ligand)})
        raw_manifest.append({"sample_id": candidate_id, "protein_pdb_path": str(source_protein), "ligand_sdf_path": str(source_ligand)})
        sha["packaged_proteins"][candidate_id] = _sha(packaged_protein)
        sha["packaged_ligands"][candidate_id] = _sha(packaged_ligand)
        sha["packaged_metadata"][candidate_id] = _sha(packaged_metadata)
    _write_csv(paths["loader_qa"], loader_qa)
    _write_csv(paths["loader_report"], loader_report)
    _write_csv(paths["loader_gate_plan"], loader_gate_plan)
    _write_csv(paths["loader_gate_report"], loader_gate_report)
    _write_csv(paths["index_qa"], index_qa)
    _write_csv(paths["index"], index_rows)
    _write_csv(paths["raw_manifest"], raw_manifest)
    manifest = {
        "row_count": 3,
        "sample_ids": list(TARGETS),
        "safety_flags": {
            "source_manifest_modified": False,
            "source_pdb_modified": False,
            "source_sdf_modified": False,
            "packaged_pdb_sdf_json_modified": False,
            "files_copied": False,
            "package_archive_created": False,
            "real_training_tensor_generated": False,
            "real_dataset_generated": False,
            "pre_reaction_transform_ready": False,
            "training_ready": False,
        },
        "sha256": sha,
    }
    paths["dataset_manifest"].parent.mkdir(parents=True, exist_ok=True)
    paths["dataset_manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    return paths


def _run(paths):
    return run(_args(paths))


def _assert_blocked(paths, reason):
    plan, report, code = _run(paths)
    assert code == 1
    assert any(row["dataset_snapshot_review_gate_status"] == "blocked" for row in report)
    assert any(reason in row["blocking_reasons"] for row in report)
    assert len(plan) < 3


def test_success_outputs_three_passed_rows(tmp_path):
    paths = _make_fixture(tmp_path)
    plan, report, code = _run(paths)
    assert code == 0
    assert len(plan) == 3
    assert len(_read_csv(paths["snapshot_gate_plan"])) == 3
    assert len(_read_csv(paths["snapshot_gate_report"])) == 3
    assert all(row["dataset_snapshot_review_gate_status"] == "dataset_snapshot_review_gate_passed" for row in report)
    assert all(row["explicit_approval_required_before_snapshot_review"] == "true" for row in report)
    assert all(row["snapshot_review_executed"] == "false" for row in report)
    assert all(row["files_copied"] == "false" for row in report)
    assert all(row["archive_created"] == "false" for row in report)
    assert all(row["training_ready"] == "false" for row in report)
    assert not Path(PLANNED_SNAPSHOT_ROOT).exists()
    assert "Dataset Snapshot Review Gate Summary" in paths["summary"].read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("file_key", "reason"),
    [
        ("loader_qa", "loader_dry_run_qa_row_found_once"),
        ("loader_report", "loader_dry_run_report_row_found_once"),
    ],
)
def test_missing_required_reports_block(tmp_path, file_key, reason):
    paths = _make_fixture(tmp_path)
    paths[file_key].unlink()
    _assert_blocked(paths, reason)


def test_loader_qa_row_missing_or_bad_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["loader_qa"])
    _write_csv(paths["loader_qa"], rows[:2], list(rows[0]))
    _assert_blocked(paths, "loader_dry_run_qa_row_found_once")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["loader_qa"])
    rows[0]["read_only_dataset_loader_dry_run_qa_status"] = "blocked"
    _write_csv(paths["loader_qa"], rows, list(rows[0]))
    _assert_blocked(paths, "loader_dry_run_qa_status_passed")


def test_loader_report_row_missing_or_bad_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["loader_report"])
    _write_csv(paths["loader_report"], rows[:2], list(rows[0]))
    _assert_blocked(paths, "loader_dry_run_report_row_found_once")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["loader_report"])
    rows[0]["read_only_dataset_loader_dry_run_status"] = "blocked"
    _write_csv(paths["loader_report"], rows, list(rows[0]))
    _assert_blocked(paths, "loader_dry_run_status_passed")


def test_gate_report_and_index_qa_blockers(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["loader_gate_report"])
    _write_csv(paths["loader_gate_report"], rows[:2], list(rows[0]))
    _assert_blocked(paths, "loader_dry_run_gate_report_row_found_once")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index_qa"])
    rows[0]["actual_dataset_index_qa_status"] = "blocked"
    _write_csv(paths["index_qa"], rows, list(rows[0]))
    _assert_blocked(paths, "actual_dataset_index_qa_status_passed")


def test_index_row_and_hash_and_manifest_blockers(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    _write_csv(paths["index"], rows[:2], list(rows[0]))
    _assert_blocked(paths, "index_row_found_once")
    paths = _make_fixture(tmp_path)
    next(paths["package_root"].glob("ligands_pre_reaction/*.sdf")).write_text("changed\n", encoding="utf-8")
    _assert_blocked(paths, "packaged_hashes_match_index_and_manifest")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["raw_manifest"])
    rows[1]["ligand_sdf_path"] = "wrong.sdf"
    _write_csv(paths["raw_manifest"], rows, list(rows[0]))
    _assert_blocked(paths, "manifest_paths_match_index_sources")


def test_label_count_snapshot_and_forbidden_output_blockers(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    rows[0]["supported_mask_levels"] = "A_warhead_only"
    _write_csv(paths["index"], rows, list(rows[0]))
    _assert_blocked(paths, "mask_levels_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    rows[0]["required_auxiliary_labels"] = "warhead_type"
    _write_csv(paths["index"], rows, list(rows[0]))
    _assert_blocked(paths, "auxiliary_labels_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    rows[0]["ligand_atom_count"] = "0"
    _write_csv(paths["index"], rows, list(rows[0]))
    _assert_blocked(paths, "graph_counts_positive")
    paths = _make_fixture(tmp_path)
    Path(PLANNED_SNAPSHOT_ROOT).mkdir(parents=True)
    _assert_blocked(paths, "planned_snapshot_outputs_absent_before_gate")


def test_tensor_archive_blockers(tmp_path):
    paths = _make_fixture(tmp_path)
    bad = tmp_path / "data" / "derived" / "covalent_small" / "bad.pt"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_bytes(b"x")
    _assert_blocked(paths, "forbidden_training_tensors_absent")
    paths = _make_fixture(tmp_path)
    bad = tmp_path / "data" / "derived" / "covalent_small" / "bad.zip"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_bytes(b"x")
    _assert_blocked(paths, "forbidden_archives_absent")


def test_script_has_no_disallowed_module_imports():
    script = Path(__file__).resolve().parents[1] / "scripts" / "build_dataset_snapshot_review_gate.py"
    tree = ast.parse(script.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert "torch" not in imported
