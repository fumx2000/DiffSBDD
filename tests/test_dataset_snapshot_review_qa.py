import argparse
import ast
import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from apply_dataset_snapshot_review import APPROVAL_TOKEN, SNAPSHOT_ROOT, TARGETS, run as apply_snapshot_review  # noqa: E402
from check_dataset_snapshot_review_qa import run as run_qa  # noqa: E402


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


def _apply_args(paths):
    return argparse.Namespace(
        snapshot_review_gate_plan_csv=paths["snapshot_gate_plan"],
        snapshot_review_gate_report_csv=paths["snapshot_gate_report"],
        loader_dry_run_qa_report_csv=paths["loader_qa"],
        loader_dry_run_report_csv=paths["loader_report"],
        actual_dataset_index_qa_report_csv=paths["index_qa"],
        index_csv=paths["index"],
        dataset_manifest_json=paths["dataset_manifest"],
        manifest_csv=paths["raw_manifest"],
        package_root=paths["package_root"],
        output_snapshot_manifest_json=paths["snapshot_manifest"],
        output_file_list_csv=paths["snapshot_file_list"],
        output_report_csv=paths["snapshot_report"],
        output_md=paths["snapshot_summary"],
        approval_token=APPROVAL_TOKEN,
    )


def _qa_args(paths):
    return argparse.Namespace(
        snapshot_manifest_json=paths["snapshot_manifest"],
        snapshot_file_list_csv=paths["snapshot_file_list"],
        snapshot_review_report_csv=paths["snapshot_report"],
        snapshot_review_gate_plan_csv=paths["snapshot_gate_plan"],
        snapshot_review_gate_report_csv=paths["snapshot_gate_report"],
        loader_dry_run_qa_report_csv=paths["loader_qa"],
        loader_dry_run_report_csv=paths["loader_report"],
        actual_dataset_index_qa_report_csv=paths["index_qa"],
        index_csv=paths["index"],
        dataset_manifest_json=paths["dataset_manifest"],
        manifest_csv=paths["raw_manifest"],
        package_root=paths["package_root"],
        output_report_csv=paths["qa_report"],
        output_md=paths["qa_summary"],
    )


def _make_fixture(tmp_path):
    shutil.rmtree(tmp_path / "data" / "derived" / "covalent_small", ignore_errors=True)
    paths = {
        "snapshot_gate_plan": tmp_path / "loader" / "dataset_snapshot_review_gate_plan.csv",
        "snapshot_gate_report": tmp_path / "loader" / "dataset_snapshot_review_gate_report.csv",
        "loader_qa": tmp_path / "loader" / "read_only_dataset_loader_dry_run_qa_report.csv",
        "loader_report": tmp_path / "loader" / "read_only_dataset_loader_dry_run_report.csv",
        "index_qa": tmp_path / "pre" / "actual_dataset_index_qa_report.csv",
        "index": tmp_path / "index" / "index.csv",
        "dataset_manifest": tmp_path / "index" / "manifest.json",
        "raw_manifest": tmp_path / "raw" / "manifest_real_small.csv",
        "package_root": tmp_path / "package",
        "snapshot_manifest": Path(SNAPSHOT_ROOT) / "dataset_snapshot_review_manifest.json",
        "snapshot_file_list": Path(SNAPSHOT_ROOT) / "dataset_snapshot_review_file_list.csv",
        "snapshot_report": Path(SNAPSHOT_ROOT) / "dataset_snapshot_review_report.csv",
        "snapshot_summary": tmp_path / "docs" / "dataset_snapshot_review_summary.md",
        "qa_report": Path(SNAPSHOT_ROOT) / "dataset_snapshot_review_qa_report.csv",
        "qa_summary": tmp_path / "docs" / "dataset_snapshot_review_qa_summary.md",
    }
    gate_plan_rows = []
    gate_report_rows = []
    loader_qa_rows = []
    loader_report_rows = []
    index_qa_rows = []
    index_rows = []
    raw_manifest_rows = []
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
        index_rows.append(
            {
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
        )
        gate_plan_rows.append({"snapshot_review_gate_plan_id": candidate_id})
        gate_report_rows.append(
            {
                "candidate_id": candidate_id,
                "dataset_snapshot_review_gate_status": "dataset_snapshot_review_gate_passed",
                "explicit_approval_required_before_snapshot_review": "true",
                "ready_for_dataset_snapshot_review_after_approval": "true",
                "snapshot_review_executed": "false",
                "files_copied": "false",
                "archive_created": "false",
                "torch_imported": "false",
                "checkpoint_loaded": "false",
                "model_initialized": "false",
                "dataloader_tensor_generated": "false",
                "real_training_tensor_generated": "false",
                "real_dataset_generated": "false",
                "pre_reaction_transform_ready": "false",
                "training_ready": "false",
            }
        )
        loader_qa_rows.append({"candidate_id": candidate_id, "read_only_dataset_loader_dry_run_qa_status": "read_only_dataset_loader_dry_run_qa_passed"})
        loader_report_rows.append({"candidate_id": candidate_id, "read_only_dataset_loader_dry_run_status": "read_only_dataset_loader_dry_run_passed"})
        index_qa_rows.append({"candidate_id": candidate_id, "actual_dataset_index_qa_status": "actual_dataset_index_qa_passed"})
        raw_manifest_rows.append({"sample_id": source_id, "protein_pdb_path": str(source_protein), "ligand_sdf_path": str(source_base_ligand)})
        raw_manifest_rows.append({"sample_id": candidate_id, "protein_pdb_path": str(source_protein), "ligand_sdf_path": str(source_ligand)})
        sha["packaged_proteins"][candidate_id] = _sha(packaged_protein)
        sha["packaged_ligands"][candidate_id] = _sha(packaged_ligand)
        sha["packaged_metadata"][candidate_id] = _sha(packaged_metadata)
    _write_csv(paths["snapshot_gate_plan"], gate_plan_rows)
    _write_csv(paths["snapshot_gate_report"], gate_report_rows)
    _write_csv(paths["loader_qa"], loader_qa_rows)
    _write_csv(paths["loader_report"], loader_report_rows)
    _write_csv(paths["index_qa"], index_qa_rows)
    _write_csv(paths["index"], index_rows)
    _write_csv(paths["raw_manifest"], raw_manifest_rows)
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
    file_list, report, snapshot_manifest, code = apply_snapshot_review(_apply_args(paths))
    assert code == 0
    assert len(file_list) == 23
    assert len(report) == 3
    assert snapshot_manifest["row_count"] == 3
    return paths


def _run_qa(paths):
    return run_qa(_qa_args(paths))


def _assert_blocked(paths, reason):
    rows, code = _run_qa(paths)
    assert code == 1
    assert len(rows) == 3
    assert any(reason in row["blocking_reasons"] for row in rows)
    assert any(row["dataset_snapshot_review_qa_status"] == "blocked" for row in rows)


def test_success_outputs_three_passed_rows(tmp_path):
    paths = _make_fixture(tmp_path)
    original_hashes = {key: _sha(paths[key]) for key in ["snapshot_manifest", "snapshot_file_list", "snapshot_report", "index", "dataset_manifest", "raw_manifest"]}
    rows, code = _run_qa(paths)
    assert code == 0
    assert len(rows) == 3
    assert len(_read_csv(paths["qa_report"])) == 3
    assert all(row["dataset_snapshot_review_qa_status"] == "dataset_snapshot_review_qa_passed" for row in rows)
    assert all(row["snapshot_manifest_valid"] == "true" for row in rows)
    assert all(row["candidate_file_rows_valid"] == "true" for row in rows)
    assert all(row["candidate_file_hashes_match_current_files"] == "true" for row in rows)
    assert all(row["global_artifact_rows_valid"] == "true" for row in rows)
    assert all(row["only_allowed_snapshot_files_created"] == "true" for row in rows)
    assert all(row["training_ready"] == "false" for row in rows)
    assert "Dataset Snapshot Review QA Summary" in paths["qa_summary"].read_text(encoding="utf-8")
    for key, before in original_hashes.items():
        assert _sha(paths[key]) == before


def test_manifest_missing_invalid_or_bad_row_count_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    paths["snapshot_manifest"].unlink()
    _assert_blocked(paths, "snapshot_manifest_parseable")
    paths = _make_fixture(tmp_path)
    paths["snapshot_manifest"].write_text("{bad", encoding="utf-8")
    _assert_blocked(paths, "snapshot_manifest_parseable")
    paths = _make_fixture(tmp_path)
    manifest = json.loads(paths["snapshot_manifest"].read_text(encoding="utf-8"))
    manifest["row_count"] = 4
    paths["snapshot_manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    _assert_blocked(paths, "snapshot_manifest_valid")


def test_file_list_count_candidate_roles_hash_and_flags_block(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["snapshot_file_list"])
    _write_csv(paths["snapshot_file_list"], rows[:22], list(rows[0]))
    _assert_blocked(paths, "snapshot_file_list_row_count_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["snapshot_file_list"])
    rows[0]["file_role"] = "wrong"
    _write_csv(paths["snapshot_file_list"], rows, list(rows[0]))
    _assert_blocked(paths, "candidate_file_rows_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["snapshot_file_list"])
    rows[0]["sha256"] = "bad"
    _write_csv(paths["snapshot_file_list"], rows, list(rows[0]))
    _assert_blocked(paths, "candidate_file_hashes_match_current_files")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["snapshot_file_list"])
    rows[0]["copied_to_snapshot"] = "true"
    _write_csv(paths["snapshot_file_list"], rows, list(rows[0]))
    _assert_blocked(paths, "candidate_file_reference_only_flags_valid")


def test_global_artifact_rows_and_hashes_block(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["snapshot_file_list"])
    rows = [row for row in rows if row["row_type"] != "global_artifact"]
    _write_csv(paths["snapshot_file_list"], rows, list(rows[0]))
    _assert_blocked(paths, "global_artifact_rows_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["snapshot_file_list"])
    for row in rows:
        if row["row_type"] == "global_artifact":
            row["sha256"] = "bad"
            break
    _write_csv(paths["snapshot_file_list"], rows, list(rows[0]))
    _assert_blocked(paths, "global_artifact_hashes_match_current_files")


def test_snapshot_report_and_upstream_status_blockers(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["snapshot_report"])
    _write_csv(paths["snapshot_report"], rows[:2], list(rows[0]))
    _assert_blocked(paths, "snapshot_review_report_row_found_once")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["snapshot_report"])
    rows[0]["dataset_snapshot_review_status"] = "blocked"
    _write_csv(paths["snapshot_report"], rows, list(rows[0]))
    _assert_blocked(paths, "snapshot_review_status_passed")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["snapshot_gate_report"])
    rows[0]["dataset_snapshot_review_gate_status"] = "blocked"
    _write_csv(paths["snapshot_gate_report"], rows, list(rows[0]))
    _assert_blocked(paths, "upstream_gate_status_still_passed")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["loader_qa"])
    rows[0]["read_only_dataset_loader_dry_run_qa_status"] = "blocked"
    _write_csv(paths["loader_qa"], rows, list(rows[0]))
    _assert_blocked(paths, "loader_dry_run_qa_status_still_passed")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["loader_report"])
    rows[0]["read_only_dataset_loader_dry_run_status"] = "blocked"
    _write_csv(paths["loader_report"], rows, list(rows[0]))
    _assert_blocked(paths, "loader_dry_run_status_still_passed")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index_qa"])
    rows[0]["actual_dataset_index_qa_status"] = "blocked"
    _write_csv(paths["index_qa"], rows, list(rows[0]))
    _assert_blocked(paths, "actual_dataset_index_qa_status_still_passed")


def test_snapshot_forbidden_files_and_global_forbidden_outputs_block(tmp_path):
    paths = _make_fixture(tmp_path)
    (Path(SNAPSHOT_ROOT) / "bad.pdb").write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "only_allowed_snapshot_files_created")
    paths = _make_fixture(tmp_path)
    (Path(SNAPSHOT_ROOT) / "bad.pt").write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "only_allowed_snapshot_files_created")
    paths = _make_fixture(tmp_path)
    tensor = tmp_path / "data" / "derived" / "covalent_small" / "bad.pt"
    tensor.parent.mkdir(parents=True, exist_ok=True)
    tensor.write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "no_training_tensors_created")
    tensor.unlink()
    paths = _make_fixture(tmp_path)
    archive = tmp_path / "data" / "derived" / "covalent_small" / "bad.zip"
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_text("bad", encoding="utf-8")
    _assert_blocked(paths, "no_archive_created")


def test_index_package_hash_and_raw_manifest_blockers(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    _write_csv(paths["index"], rows[:2], list(rows[0]))
    _assert_blocked(paths, "index_and_manifest_still_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    Path(rows[0]["packaged_ligand_sdf_path"]).write_text("changed\n$$$$\n", encoding="utf-8")
    _assert_blocked(paths, "packaged_hashes_still_match_index_and_manifest")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["raw_manifest"])
    rows[1]["ligand_sdf_path"] = "wrong.sdf"
    _write_csv(paths["raw_manifest"], rows, list(rows[0]))
    _assert_blocked(paths, "manifest_paths_match_index_sources")


def test_script_has_no_torch_import_checkpoint_model_or_training_calls():
    source = Path(__file__).resolve().parents[1] / "scripts" / "check_dataset_snapshot_review_qa.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    assert "torch" not in imported
    text = source.read_text(encoding="utf-8").lower()
    assert "load_checkpoint(" not in text
    assert "initialize_model(" not in text
    assert "dataloader(" not in text
    assert "train(" not in text
