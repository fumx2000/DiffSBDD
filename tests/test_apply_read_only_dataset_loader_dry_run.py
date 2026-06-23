import argparse
import ast
import csv
import hashlib
import json
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from apply_read_only_dataset_loader_dry_run import APPROVAL_TOKEN, TARGETS, run  # noqa: E402


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


def _args(paths, token=APPROVAL_TOKEN):
    return argparse.Namespace(
        loader_dry_run_gate_plan_csv=paths["gate_plan"],
        loader_dry_run_gate_report_csv=paths["gate_report"],
        actual_dataset_index_qa_report_csv=paths["qa_report"],
        index_csv=paths["index"],
        dataset_manifest_json=paths["dataset_manifest"],
        manifest_csv=paths["raw_manifest"],
        package_root=paths["package_root"],
        output_report_csv=paths["output_report"],
        output_md=paths["summary"],
        approval_token=token,
    )


def _make_fixture(tmp_path):
    paths = {
        "gate_plan": tmp_path / "pre_reaction_graph" / "read_only_dataset_loader_dry_run_gate_plan.csv",
        "gate_report": tmp_path / "pre_reaction_graph" / "read_only_dataset_loader_dry_run_gate_report.csv",
        "qa_report": tmp_path / "pre_reaction_graph" / "actual_dataset_index_qa_report.csv",
        "index": tmp_path / "dataset_index_review_only" / "index.csv",
        "dataset_manifest": tmp_path / "dataset_index_review_only" / "manifest.json",
        "raw_manifest": tmp_path / "raw" / "manifest_real_small.csv",
        "package_root": tmp_path / "packaging_real_review_only",
        "output_report": tmp_path
        / "data"
        / "derived"
        / "covalent_small"
        / "loader_dry_run_review_only"
        / "read_only_dataset_loader_dry_run_report.csv",
        "summary": tmp_path / "docs" / "read_only_dataset_loader_dry_run_summary.md",
    }
    gate_plan_rows = []
    gate_report_rows = []
    qa_rows = []
    index_rows = []
    manifest_rows = []
    sha_section = {
        "packaged_proteins": {},
        "packaged_ligands": {},
        "packaged_metadata": {},
    }
    for candidate_id, source_id in TARGETS.items():
        source_protein = tmp_path / "raw" / "proteins" / f"{source_id}.pdb"
        source_ligand = tmp_path / "raw" / "ligands" / f"{candidate_id}.sdf"
        source_base_ligand = tmp_path / "raw" / "ligands" / f"{source_id}.sdf"
        packaged_protein = paths["package_root"] / "proteins" / f"{source_id}.pdb"
        packaged_ligand = paths["package_root"] / "ligands_pre_reaction" / f"{candidate_id}.sdf"
        packaged_metadata = paths["package_root"] / "metadata" / f"{candidate_id}.json"
        for file_path in [source_protein, source_ligand, source_base_ligand, packaged_protein, packaged_ligand, packaged_metadata]:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        source_protein.write_text(f"HEADER {source_id}\nATOM      1  SG  CYS A  12\n", encoding="utf-8")
        source_ligand.write_text(f"{candidate_id}\n  CDK\n\n$$$$\n", encoding="utf-8")
        source_base_ligand.write_text(f"{source_id}\n  CDK\n\n$$$$\n", encoding="utf-8")
        packaged_protein.write_bytes(source_protein.read_bytes())
        packaged_ligand.write_bytes(source_ligand.read_bytes())
        packaged_metadata.write_text(json.dumps({"sample_id": candidate_id, "source_sample_id": source_id}), encoding="utf-8")

        common = {
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
            "reactive_residue_chain": "A",
            "reactive_residue_id": "12",
            "reactive_atom_name": "SG",
            "ligand_reactive_atom_id": "1",
            "scaffold_atoms": "0",
            "linker_atoms": "2",
            "warhead_atoms": "1 3",
            "scaffold_atom_count": "1",
            "linker_atom_count": "1",
            "warhead_atom_count": "2",
            "supported_mask_levels": "A_warhead_only;B_linker_warhead;B2_scaffold_warhead;C_scaffold_linker_warhead",
            "required_auxiliary_labels": "warhead_type;ligand_reactive_atom_id;protein_reactive_residue;pre_reaction_geometry_label",
            "real_dataset_generated": "false",
            "pre_reaction_transform_ready": "false",
            "training_ready": "false",
        }
        gate_plan_rows.append({"loader_dry_run_gate_plan_id": candidate_id, **common})
        gate_report_rows.append(
            {
                "candidate_id": candidate_id,
                "read_only_dataset_loader_dry_run_gate_status": "read_only_dataset_loader_dry_run_gate_passed",
                "explicit_approval_required_before_loader_dry_run": "true",
                "ready_for_read_only_loader_dry_run_after_approval": "true",
                "loader_dry_run_executed": "false",
                "torch_imported": "false",
                "checkpoint_loaded": "false",
                "model_initialized": "false",
                "dataloader_tensor_generated": "false",
                "real_dataset_generated": "false",
                "pre_reaction_transform_ready": "false",
                "training_ready": "false",
            }
        )
        qa_rows.append(
            {
                "candidate_id": candidate_id,
                "actual_dataset_index_qa_status": "actual_dataset_index_qa_passed",
                "index_csv_modified_by_qa": "false",
                "dataset_manifest_modified_by_qa": "false",
                "package_files_modified_by_qa": "false",
                "source_files_modified_by_qa": "false",
                "raw_manifest_modified_by_qa": "false",
                "files_copied_by_qa": "false",
                "real_dataset_generated": "false",
                "pre_reaction_transform_ready": "false",
                "training_ready": "false",
            }
        )
        index_rows.append({"sample_id": candidate_id, **common})
        manifest_rows.append(
            {"sample_id": source_id, "protein_pdb_path": str(source_protein), "ligand_sdf_path": str(source_base_ligand)}
        )
        manifest_rows.append(
            {"sample_id": candidate_id, "protein_pdb_path": str(source_protein), "ligand_sdf_path": str(source_ligand)}
        )
        sha_section["packaged_proteins"][candidate_id] = _sha(packaged_protein)
        sha_section["packaged_ligands"][candidate_id] = _sha(packaged_ligand)
        sha_section["packaged_metadata"][candidate_id] = _sha(packaged_metadata)

    _write_csv(paths["gate_plan"], gate_plan_rows)
    _write_csv(paths["gate_report"], gate_report_rows)
    _write_csv(paths["qa_report"], qa_rows)
    _write_csv(paths["index"], index_rows)
    _write_csv(paths["raw_manifest"], manifest_rows)
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
        "sha256": sha_section,
    }
    paths["dataset_manifest"].parent.mkdir(parents=True, exist_ok=True)
    paths["dataset_manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    return paths


def _protected_files(paths):
    protected = [
        paths["gate_plan"],
        paths["gate_report"],
        paths["qa_report"],
        paths["index"],
        paths["dataset_manifest"],
        paths["raw_manifest"],
    ]
    protected.extend(path for path in paths["package_root"].rglob("*") if path.is_file())
    protected.extend(path for path in paths["raw_manifest"].parent.rglob("*") if path.is_file())
    return sorted(set(protected))


def _hashes(paths):
    return {str(path): _sha(path) for path in paths}


def _run(paths, token=APPROVAL_TOKEN):
    return run(_args(paths, token=token))


def _assert_blocked_for(paths, expected_blocker):
    rows, exit_code = _run(paths)
    assert exit_code == 1
    assert any(row["read_only_dataset_loader_dry_run_status"] == "blocked" for row in rows)
    assert any(expected_blocker in row["blocking_reasons"] for row in rows)


def test_invalid_approval_token_blocks_without_output_directory(tmp_path):
    paths = _make_fixture(tmp_path)
    rows, exit_code = _run(paths, token="wrong")
    assert rows == []
    assert exit_code == 1
    assert not paths["output_report"].parent.exists()


def test_success_outputs_three_passed_rows_and_does_not_mutate_inputs(tmp_path):
    paths = _make_fixture(tmp_path)
    before = _hashes(_protected_files(paths))
    rows, exit_code = _run(paths)

    assert exit_code == 0
    assert len(rows) == 3
    assert len(_read_csv(paths["output_report"])) == 3
    assert all(row["read_only_dataset_loader_dry_run_status"] == "read_only_dataset_loader_dry_run_passed" for row in rows)
    assert all(row["approval_token_valid"] == "true" for row in rows)
    assert all(row["packaged_metadata_json_parseable"] == "true" for row in rows)
    assert all(row["packaged_protein_readable"] == "true" for row in rows)
    assert all(row["packaged_ligand_sdf_readable"] == "true" for row in rows)
    assert all(row["dry_run_record_constructed"] == "true" for row in rows)
    assert all(row["dry_run_record_fields_valid"] == "true" for row in rows)
    assert all(row["loader_dry_run_executed"] == "true" for row in rows)
    assert all(row["torch_imported"] == "false" for row in rows)
    assert all(row["checkpoint_loaded"] == "false" for row in rows)
    assert all(row["model_initialized"] == "false" for row in rows)
    assert all(row["dataloader_tensor_generated"] == "false" for row in rows)
    assert all(row["training_ready"] == "false" for row in rows)
    assert before == _hashes(_protected_files(paths))
    assert "Read-only Dataset Loader Dry-run Summary" in paths["summary"].read_text(encoding="utf-8")
    assert not list(tmp_path.rglob("*.pt"))
    assert not list(tmp_path.rglob("*.tar"))


def test_gate_plan_row_missing_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["gate_plan"])
    _write_csv(paths["gate_plan"], rows[:2], list(rows[0]))
    _assert_blocked_for(paths, "gate_plan_row_found_once")


def test_gate_report_row_missing_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["gate_report"])
    _write_csv(paths["gate_report"], rows[:2], list(rows[0]))
    _assert_blocked_for(paths, "gate_report_row_found_once")


def test_gate_status_not_passed_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["gate_report"])
    rows[0]["read_only_dataset_loader_dry_run_gate_status"] = "blocked"
    _write_csv(paths["gate_report"], rows, list(rows[0]))
    _assert_blocked_for(paths, "gate_status_passed")


def test_qa_row_missing_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["qa_report"])
    _write_csv(paths["qa_report"], rows[:2], list(rows[0]))
    _assert_blocked_for(paths, "actual_dataset_index_qa_row_found_once")


def test_qa_status_not_passed_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["qa_report"])
    rows[0]["actual_dataset_index_qa_status"] = "blocked"
    _write_csv(paths["qa_report"], rows, list(rows[0]))
    _assert_blocked_for(paths, "qa_status_passed")


def test_index_row_missing_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    _write_csv(paths["index"], rows[:2], list(rows[0]))
    _assert_blocked_for(paths, "index_row_found_once")


def test_metadata_json_unparseable_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    next(paths["package_root"].glob("metadata/*.json")).write_text("{", encoding="utf-8")
    _assert_blocked_for(paths, "packaged_metadata_json_parseable")


def test_packaged_pdb_missing_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    next(paths["package_root"].glob("proteins/*.pdb")).unlink()
    _assert_blocked_for(paths, "packaged_paths_exist")
    _assert_blocked_for(paths, "packaged_protein_readable")


def test_packaged_sdf_missing_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    next(paths["package_root"].glob("ligands_pre_reaction/*.sdf")).unlink()
    _assert_blocked_for(paths, "packaged_paths_exist")
    _assert_blocked_for(paths, "packaged_ligand_sdf_readable")


def test_packaged_hash_mismatch_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    rows[0]["packaged_ligand_sha256"] = "bad"
    _write_csv(paths["index"], rows, list(rows[0]))
    _assert_blocked_for(paths, "packaged_hashes_match_index_and_manifest")


def test_raw_manifest_source_path_mismatch_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["raw_manifest"])
    rows[1]["ligand_sdf_path"] = "wrong.sdf"
    _write_csv(paths["raw_manifest"], rows, list(rows[0]))
    _assert_blocked_for(paths, "manifest_paths_match_index_sources")


def test_missing_mask_level_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    rows[0]["supported_mask_levels"] = "A_warhead_only"
    _write_csv(paths["index"], rows, list(rows[0]))
    _assert_blocked_for(paths, "mask_levels_valid")


def test_missing_auxiliary_label_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    rows[0]["required_auxiliary_labels"] = "warhead_type"
    _write_csv(paths["index"], rows, list(rows[0]))
    _assert_blocked_for(paths, "auxiliary_labels_valid")


def test_zero_graph_count_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    rows[0]["ligand_atom_count"] = "0"
    _write_csv(paths["index"], rows, list(rows[0]))
    _assert_blocked_for(paths, "graph_counts_positive")


def test_training_tensor_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    bad_file = tmp_path / "data" / "derived" / "covalent_small" / "bad.pt"
    bad_file.parent.mkdir(parents=True, exist_ok=True)
    bad_file.write_bytes(b"no tensor")
    _assert_blocked_for(paths, "forbidden_training_tensors_absent")


def test_archive_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    bad_file = tmp_path / "data" / "derived" / "covalent_small" / "bad.zip"
    bad_file.parent.mkdir(parents=True, exist_ok=True)
    bad_file.write_bytes(b"no archive")
    _assert_blocked_for(paths, "forbidden_archives_absent")


def test_script_has_no_disallowed_module_imports():
    script = Path(__file__).resolve().parents[1] / "scripts" / "apply_read_only_dataset_loader_dry_run.py"
    tree = ast.parse(script.read_text(encoding="utf-8"))
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
    assert "torch" not in imported_roots
