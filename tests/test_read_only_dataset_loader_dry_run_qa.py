import argparse
import ast
import csv
import hashlib
import json
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_read_only_dataset_loader_dry_run_qa import TARGETS, run  # noqa: E402


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
        loader_dry_run_report_csv=paths["dry_report"],
        loader_dry_run_gate_plan_csv=paths["gate_plan"],
        loader_dry_run_gate_report_csv=paths["gate_report"],
        actual_dataset_index_qa_report_csv=paths["index_qa"],
        index_csv=paths["index"],
        dataset_manifest_json=paths["dataset_manifest"],
        manifest_csv=paths["raw_manifest"],
        package_root=paths["package_root"],
        output_report_csv=paths["qa_report"],
        output_md=paths["summary"],
    )


def _make_fixture(tmp_path):
    paths = {
        "dry_report": tmp_path / "loader_dry_run_review_only" / "read_only_dataset_loader_dry_run_report.csv",
        "gate_plan": tmp_path / "pre_reaction_graph" / "read_only_dataset_loader_dry_run_gate_plan.csv",
        "gate_report": tmp_path / "pre_reaction_graph" / "read_only_dataset_loader_dry_run_gate_report.csv",
        "index_qa": tmp_path / "pre_reaction_graph" / "actual_dataset_index_qa_report.csv",
        "index": tmp_path / "dataset_index_review_only" / "index.csv",
        "dataset_manifest": tmp_path / "dataset_index_review_only" / "manifest.json",
        "raw_manifest": tmp_path / "raw" / "manifest_real_small.csv",
        "package_root": tmp_path / "packaging_real_review_only",
        "qa_report": tmp_path / "loader_dry_run_review_only" / "read_only_dataset_loader_dry_run_qa_report.csv",
        "summary": tmp_path / "docs" / "read_only_dataset_loader_dry_run_qa_summary.md",
    }
    dry_rows = []
    gate_plan_rows = []
    gate_report_rows = []
    index_qa_rows = []
    index_rows = []
    manifest_rows = []
    sha_section = {"packaged_proteins": {}, "packaged_ligands": {}, "packaged_metadata": {}}
    for candidate_id, source_id in TARGETS.items():
        source_protein = tmp_path / "raw" / "proteins" / f"{source_id}.pdb"
        source_ligand = tmp_path / "raw" / "ligands" / f"{candidate_id}.sdf"
        source_base_ligand = tmp_path / "raw" / "ligands" / f"{source_id}.sdf"
        packaged_protein = paths["package_root"] / "proteins" / f"{source_id}.pdb"
        packaged_ligand = paths["package_root"] / "ligands_pre_reaction" / f"{candidate_id}.sdf"
        packaged_metadata = paths["package_root"] / "metadata" / f"{candidate_id}.json"
        for file_path in [source_protein, source_ligand, source_base_ligand, packaged_protein, packaged_ligand, packaged_metadata]:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        source_protein.write_text(f"HEADER {source_id}\nATOM      1 SG CYS A 12\n", encoding="utf-8")
        source_ligand.write_text(f"{candidate_id}\n  CDK\n\n$$$$\n", encoding="utf-8")
        source_base_ligand.write_text(f"{source_id}\n  CDK\n\n$$$$\n", encoding="utf-8")
        packaged_protein.write_bytes(source_protein.read_bytes())
        packaged_ligand.write_bytes(source_ligand.read_bytes())
        packaged_metadata.write_text(json.dumps({"sample_id": candidate_id}), encoding="utf-8")
        common = {
            "source_sample_id": source_id,
            "pre_reaction_sample_id": candidate_id,
            "packaged_protein_path": str(packaged_protein),
            "packaged_ligand_sdf_path": str(packaged_ligand),
            "packaged_metadata_json_path": str(packaged_metadata),
            "source_protein_path": str(source_protein),
            "source_ligand_sdf_path": str(source_ligand),
            "packaged_protein_sha256": _sha(packaged_protein),
            "packaged_ligand_sha256": _sha(packaged_ligand),
            "packaged_metadata_sha256": _sha(packaged_metadata),
            "supported_mask_levels": "A_warhead_only;B_linker_warhead;B2_scaffold_warhead;C_scaffold_linker_warhead",
            "required_auxiliary_labels": "warhead_type;ligand_reactive_atom_id;protein_reactive_residue;pre_reaction_geometry_label",
        }
        dry_rows.append(
            {
                "candidate_id": candidate_id,
                "source_sample_id": source_id,
                "pre_reaction_sample_id": candidate_id,
                "approval_token_valid": "true",
                "gate_plan_row_found_once": "true",
                "gate_report_row_found_once": "true",
                "actual_dataset_index_qa_row_found_once": "true",
                "index_row_found_once": "true",
                "manifest_candidate_row_found_once": "true",
                "manifest_source_row_found_once": "true",
                "gate_status_passed": "true",
                "qa_status_passed": "true",
                "source_mapping_valid": "true",
                "packaged_paths_exist": "true",
                "source_paths_exist": "true",
                "packaged_hashes_match_index_and_manifest": "true",
                "manifest_paths_match_index_sources": "true",
                "mask_levels_valid": "true",
                "auxiliary_labels_valid": "true",
                "graph_counts_positive": "true",
                "packaged_metadata_json_parseable": "true",
                "packaged_protein_readable": "true",
                "packaged_ligand_sdf_readable": "true",
                "packaged_protein_file_size_bytes": str(packaged_protein.stat().st_size),
                "packaged_ligand_file_size_bytes": str(packaged_ligand.stat().st_size),
                "packaged_metadata_file_size_bytes": str(packaged_metadata.stat().st_size),
                "packaged_protein_line_count": "2",
                "packaged_ligand_sdf_line_count": "4",
                "packaged_protein_atom_like_line_count": "1",
                "packaged_ligand_sdf_record_marker_present": "true",
                "dry_run_record_constructed": "true",
                "dry_run_record_fields_valid": "true",
                "loader_dry_run_executed": "true",
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
                "read_only_dataset_loader_dry_run_status": "read_only_dataset_loader_dry_run_passed",
                "blocking_reasons": "",
                "recommended_next_action": "build_read_only_dataset_loader_dry_run_qa_not_training",
            }
        )
        gate_plan_rows.append({"loader_dry_run_gate_plan_id": candidate_id})
        gate_report_rows.append({"candidate_id": candidate_id, "read_only_dataset_loader_dry_run_gate_status": "read_only_dataset_loader_dry_run_gate_passed"})
        index_qa_rows.append({"candidate_id": candidate_id, "actual_dataset_index_qa_status": "actual_dataset_index_qa_passed"})
        index_rows.append({"sample_id": candidate_id, **common})
        manifest_rows.append({"sample_id": source_id, "protein_pdb_path": str(source_protein), "ligand_sdf_path": str(source_base_ligand)})
        manifest_rows.append({"sample_id": candidate_id, "protein_pdb_path": str(source_protein), "ligand_sdf_path": str(source_ligand)})
        sha_section["packaged_proteins"][candidate_id] = _sha(packaged_protein)
        sha_section["packaged_ligands"][candidate_id] = _sha(packaged_ligand)
        sha_section["packaged_metadata"][candidate_id] = _sha(packaged_metadata)
    _write_csv(paths["dry_report"], dry_rows)
    _write_csv(paths["gate_plan"], gate_plan_rows)
    _write_csv(paths["gate_report"], gate_report_rows)
    _write_csv(paths["index_qa"], index_qa_rows)
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


def _protected(paths):
    files = [paths["dry_report"], paths["gate_plan"], paths["gate_report"], paths["index_qa"], paths["index"], paths["dataset_manifest"], paths["raw_manifest"]]
    files.extend(path for path in paths["package_root"].rglob("*") if path.is_file())
    files.extend(path for path in paths["raw_manifest"].parent.rglob("*") if path.is_file())
    return sorted(set(files))


def _hashes(paths):
    return {str(path): _sha(path) for path in paths}


def _run(paths):
    return run(_args(paths))


def _assert_blocked(paths, reason):
    rows, exit_code = _run(paths)
    assert exit_code == 1
    assert any(row["read_only_dataset_loader_dry_run_qa_status"] == "blocked" for row in rows)
    assert any(reason in row["blocking_reasons"] for row in rows)


def test_success_outputs_three_passed_rows_and_preserves_inputs(tmp_path):
    paths = _make_fixture(tmp_path)
    before = _hashes(_protected(paths))
    rows, exit_code = _run(paths)
    assert exit_code == 0
    assert len(rows) == 3
    assert len(_read_csv(paths["qa_report"])) == 3
    assert all(row["read_only_dataset_loader_dry_run_qa_status"] == "read_only_dataset_loader_dry_run_qa_passed" for row in rows)
    assert all(row["dry_run_status_passed"] == "true" for row in rows)
    assert all(row["dry_run_readability_fields_valid"] == "true" for row in rows)
    assert all(row["dry_run_record_fields_valid"] == "true" for row in rows)
    assert all(row["packaged_hashes_still_match_index_and_manifest"] == "true" for row in rows)
    assert all(row["torch_imported"] == "false" for row in rows)
    assert all(row["dataloader_tensor_generated"] == "false" for row in rows)
    assert before == _hashes(_protected(paths))
    assert "Read-only Dataset Loader Dry-run QA Summary" in paths["summary"].read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("read_only_dataset_loader_dry_run_status", "blocked", "dry_run_status_passed"),
        ("loader_dry_run_executed", "false", "dry_run_safety_flags_valid"),
        ("torch_imported", "true", "dry_run_safety_flags_valid"),
        ("checkpoint_loaded", "true", "dry_run_safety_flags_valid"),
        ("model_initialized", "true", "dry_run_safety_flags_valid"),
        ("dataloader_tensor_generated", "true", "dry_run_safety_flags_valid"),
        ("files_copied", "true", "dry_run_safety_flags_valid"),
        ("real_training_tensor_generated", "true", "dry_run_safety_flags_valid"),
        ("training_ready", "true", "dry_run_safety_flags_valid"),
        ("packaged_protein_file_size_bytes", "0", "dry_run_readability_fields_valid"),
        ("packaged_ligand_sdf_record_marker_present", "false", "dry_run_readability_fields_valid"),
        ("dry_run_record_fields_valid", "false", "dry_run_record_fields_valid"),
    ],
)
def test_bad_dry_run_fields_block(tmp_path, field, value, reason):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["dry_report"])
    rows[0][field] = value
    _write_csv(paths["dry_report"], rows, list(rows[0]))
    _assert_blocked(paths, reason)


def test_dry_run_report_missing_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    paths["dry_report"].unlink()
    _assert_blocked(paths, "loader_dry_run_report_row_found_once")


def test_dry_run_report_duplicate_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["dry_report"])
    rows.append(rows[0].copy())
    _write_csv(paths["dry_report"], rows, list(rows[0]))
    _assert_blocked(paths, "loader_dry_run_report_row_found_once")


def test_gate_report_missing_or_bad_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["gate_report"])
    _write_csv(paths["gate_report"], rows[:2], list(rows[0]))
    _assert_blocked(paths, "gate_report_row_found_once")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["gate_report"])
    rows[0]["read_only_dataset_loader_dry_run_gate_status"] = "blocked"
    _write_csv(paths["gate_report"], rows, list(rows[0]))
    _assert_blocked(paths, "gate_status_still_passed")


def test_index_qa_missing_or_bad_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index_qa"])
    _write_csv(paths["index_qa"], rows[:2], list(rows[0]))
    _assert_blocked(paths, "actual_dataset_index_qa_row_found_once")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index_qa"])
    rows[0]["actual_dataset_index_qa_status"] = "blocked"
    _write_csv(paths["index_qa"], rows, list(rows[0]))
    _assert_blocked(paths, "actual_dataset_index_qa_status_still_passed")


def test_index_row_missing_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    _write_csv(paths["index"], rows[:2], list(rows[0]))
    _assert_blocked(paths, "index_row_found_once")


def test_current_packaged_hash_mismatch_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    next(paths["package_root"].glob("ligands_pre_reaction/*.sdf")).write_text("changed\n$$$$\n", encoding="utf-8")
    _assert_blocked(paths, "packaged_hashes_still_match_index_and_manifest")


def test_raw_manifest_source_path_mismatch_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["raw_manifest"])
    rows[1]["ligand_sdf_path"] = "wrong.sdf"
    _write_csv(paths["raw_manifest"], rows, list(rows[0]))
    _assert_blocked(paths, "manifest_paths_match_index_sources")


def test_forbidden_tensor_and_archive_block(tmp_path):
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
    script = Path(__file__).resolve().parents[1] / "scripts" / "check_read_only_dataset_loader_dry_run_qa.py"
    tree = ast.parse(script.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert "torch" not in imported
