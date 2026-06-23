import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_actual_dataset_index_qa import TARGETS, run  # noqa: E402


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
        index_csv=paths["index"],
        dataset_manifest_json=paths["dataset_manifest"],
        actual_dataset_index_build_report_csv=paths["build_report"],
        dataset_index_build_gate_plan_csv=paths["gate_plan"],
        dataset_index_build_gate_report_csv=paths["gate_report"],
        packaging_qa_report_csv=paths["packaging_qa"],
        manifest_csv=paths["raw_manifest"],
        package_root=paths["package_root"],
        output_report_csv=paths["qa_report"],
        output_md=paths["summary"],
    )


def _make_fixture(tmp_path):
    paths = {
        "index": tmp_path / "dataset_index_review_only" / "index.csv",
        "dataset_manifest": tmp_path / "dataset_index_review_only" / "manifest.json",
        "build_report": tmp_path / "pre_reaction_graph" / "actual_dataset_index_build_report.csv",
        "gate_plan": tmp_path / "pre_reaction_graph" / "dataset_index_build_gate_plan.csv",
        "gate_report": tmp_path / "pre_reaction_graph" / "dataset_index_build_gate_report.csv",
        "packaging_qa": tmp_path / "pre_reaction_graph" / "real_packaging_execution_qa_report.csv",
        "raw_manifest": tmp_path / "raw" / "manifest_real_small.csv",
        "package_root": tmp_path / "packaging_real_review_only",
        "qa_report": tmp_path / "pre_reaction_graph" / "actual_dataset_index_qa_report.csv",
        "summary": tmp_path / "docs" / "actual_dataset_index_qa_summary.md",
    }
    index_rows = []
    gate_plan_rows = []
    build_report_rows = []
    gate_report_rows = []
    packaging_qa_rows = []
    raw_manifest_rows = []
    sha_section = {
        "dataset_index_csv": "",
        "packaged_proteins": {},
        "packaged_ligands": {},
        "packaged_metadata": {},
    }

    for candidate_id, source_id in TARGETS.items():
        source_protein = tmp_path / "raw" / "proteins" / f"{source_id}.pdb"
        source_ligand = tmp_path / "raw" / "ligands" / f"{candidate_id}.sdf"
        source_extra_ligand = tmp_path / "raw" / "ligands" / f"{source_id}.sdf"
        packaged_protein = paths["package_root"] / "proteins" / f"{source_id}.pdb"
        packaged_ligand = paths["package_root"] / "ligands_pre_reaction" / f"{candidate_id}.sdf"
        packaged_metadata = paths["package_root"] / "metadata" / f"{candidate_id}.json"
        for file_path in [source_protein, source_ligand, source_extra_ligand, packaged_protein, packaged_ligand, packaged_metadata]:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        source_protein.write_text(f"HEADER {source_id}\n", encoding="utf-8")
        source_ligand.write_text(f"{candidate_id}\n", encoding="utf-8")
        source_extra_ligand.write_text(f"{source_id}\n", encoding="utf-8")
        packaged_protein.write_bytes(source_protein.read_bytes())
        packaged_ligand.write_bytes(source_ligand.read_bytes())
        packaged_metadata.write_text(json.dumps({"sample_id": candidate_id}) + "\n", encoding="utf-8")

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
            "ligand_atom_count": "4",
            "ligand_heavy_atom_count": "4",
            "ligand_bond_count": "3",
            "protein_atom_count": "8",
            "protein_residue_count": "1",
            "reactive_residue_chain": "A",
            "reactive_residue_id": "12",
            "reactive_residue_type": "CYS",
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
        index_rows.append(
            {
                "sample_id": candidate_id,
                **common,
                "dataset_name": "covalent_small_pre_reaction_review_only",
                "dataset_role": "smoke_test_pre_reaction_packaged_artifact",
                "split": "smoke_test",
                "schema_version": "dataset_index_v0_review_only",
                "package_root": str(paths["package_root"]),
                "index_stage": "actual_dataset_index_build_review_only_not_training",
            }
        )
        gate_plan_rows.append(
            {
                "dataset_index_build_gate_plan_id": candidate_id,
                **common,
                "intended_dataset_name": "covalent_small_pre_reaction_review_only",
                "intended_dataset_role": "smoke_test_pre_reaction_packaged_artifact",
                "intended_split": "smoke_test",
                "planned_index_schema_version": "dataset_index_v0_review_only",
            }
        )
        build_report_rows.append(
            {
                "candidate_id": candidate_id,
                "source_sample_id": source_id,
                "pre_reaction_sample_id": candidate_id,
                "index_csv_written": "true",
                "dataset_manifest_written": "true",
                "index_row_found_once": "true",
                "index_row_fields_match_gate_plan": "true",
                "index_row_hashes_match_files": "true",
                "index_row_safety_flags_valid": "true",
                "dataset_manifest_parseable": "true",
                "dataset_manifest_row_count_valid": "true",
                "dataset_manifest_sample_ids_valid": "true",
                "dataset_manifest_safety_flags_valid": "true",
                "files_copied": "false",
                "real_training_tensor_generated": "false",
                "real_dataset_generated": "false",
                "pre_reaction_transform_ready": "false",
                "training_ready": "false",
                "actual_dataset_index_build_status": "actual_dataset_index_build_passed",
            }
        )
        gate_report_rows.append(
            {
                "candidate_id": candidate_id,
                "dataset_index_build_gate_status": "dataset_index_build_gate_passed",
            }
        )
        packaging_qa_rows.append(
            {
                "candidate_id": candidate_id,
                "real_packaging_execution_qa_status": "real_packaging_execution_qa_passed",
            }
        )
        raw_manifest_rows.append(
            {"sample_id": source_id, "protein_pdb_path": str(source_protein), "ligand_sdf_path": str(source_extra_ligand)}
        )
        raw_manifest_rows.append(
            {"sample_id": candidate_id, "protein_pdb_path": str(source_protein), "ligand_sdf_path": str(source_ligand)}
        )
        sha_section["packaged_proteins"][candidate_id] = _sha(packaged_protein)
        sha_section["packaged_ligands"][candidate_id] = _sha(packaged_ligand)
        sha_section["packaged_metadata"][candidate_id] = _sha(packaged_metadata)

    _write_csv(paths["index"], index_rows)
    sha_section["dataset_index_csv"] = _sha(paths["index"])
    dataset_manifest = {
        "dataset_name": "covalent_small_pre_reaction_review_only",
        "schema_version": "dataset_index_v0_review_only",
        "split": "smoke_test",
        "row_count": 3,
        "sample_ids": list(TARGETS),
        "source_sample_ids": list(TARGETS.values()),
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
    paths["dataset_manifest"].write_text(json.dumps(dataset_manifest, indent=2), encoding="utf-8")
    _write_csv(paths["build_report"], build_report_rows)
    _write_csv(paths["gate_plan"], gate_plan_rows)
    _write_csv(paths["gate_report"], gate_report_rows)
    _write_csv(paths["packaging_qa"], packaging_qa_rows)
    _write_csv(paths["raw_manifest"], raw_manifest_rows)
    return paths


def _protected_files(paths):
    protected = [
        paths["index"],
        paths["dataset_manifest"],
        paths["raw_manifest"],
        paths["build_report"],
        paths["gate_plan"],
        paths["gate_report"],
        paths["packaging_qa"],
    ]
    protected.extend(path for path in paths["package_root"].rglob("*") if path.is_file())
    protected.extend(path for path in paths["raw_manifest"].parent.rglob("*") if path.is_file())
    return sorted(set(protected))


def _hashes(paths):
    return {str(path): _sha(path) for path in paths}


def _run(paths):
    return run(_args(paths))


def _assert_blocked_for(paths, expected_blocker):
    rows = _run(paths)
    assert any(row["actual_dataset_index_qa_status"] == "blocked" for row in rows)
    assert any(expected_blocker in row["blocking_reasons"] for row in rows)


def test_success_outputs_three_passed_rows_and_summary_without_mutating_inputs(tmp_path):
    paths = _make_fixture(tmp_path)
    before = _hashes(_protected_files(paths))

    rows = _run(paths)

    assert len(rows) == 3
    assert all(row["actual_dataset_index_qa_status"] == "actual_dataset_index_qa_passed" for row in rows)
    assert all(row["index_csv_modified_by_qa"] == "false" for row in rows)
    assert all(row["dataset_manifest_modified_by_qa"] == "false" for row in rows)
    assert all(row["raw_manifest_modified_by_qa"] == "false" for row in rows)
    assert all(row["package_files_modified_by_qa"] == "false" for row in rows)
    assert all(row["source_files_modified_by_qa"] == "false" for row in rows)
    assert all(row["files_copied_by_qa"] == "false" for row in rows)
    assert all(row["real_dataset_generated"] == "false" for row in rows)
    assert all(row["training_ready"] == "false" for row in rows)
    assert len(_read_csv(paths["qa_report"])) == 3
    assert "Actual Dataset Index QA Summary" in paths["summary"].read_text(encoding="utf-8")
    assert before == _hashes(_protected_files(paths))
    assert not list(tmp_path.rglob("*.pt"))
    assert not list(tmp_path.rglob("*.tar"))


def test_missing_index_csv_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    paths["index"].unlink()
    _assert_blocked_for(paths, "index_csv_exists")


def test_missing_dataset_manifest_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    paths["dataset_manifest"].unlink()
    _assert_blocked_for(paths, "dataset_manifest_exists")


def test_index_row_count_not_three_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    _write_csv(paths["index"], rows[:2], list(rows[0]))
    _assert_blocked_for(paths, "index_row_count_valid")


def test_unparseable_manifest_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    paths["dataset_manifest"].write_text("{", encoding="utf-8")
    _assert_blocked_for(paths, "dataset_manifest_parseable")


def test_manifest_row_count_mismatch_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    data = json.loads(paths["dataset_manifest"].read_text(encoding="utf-8"))
    data["row_count"] = 2
    paths["dataset_manifest"].write_text(json.dumps(data), encoding="utf-8")
    _assert_blocked_for(paths, "dataset_manifest_row_count_valid")


def test_manifest_sample_ids_mismatch_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    data = json.loads(paths["dataset_manifest"].read_text(encoding="utf-8"))
    data["sample_ids"] = ["wrong"]
    paths["dataset_manifest"].write_text(json.dumps(data), encoding="utf-8")
    _assert_blocked_for(paths, "dataset_manifest_sample_ids_valid")


def test_manifest_safety_flags_mismatch_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    data = json.loads(paths["dataset_manifest"].read_text(encoding="utf-8"))
    data["safety_flags"]["training_ready"] = True
    paths["dataset_manifest"].write_text(json.dumps(data), encoding="utf-8")
    _assert_blocked_for(paths, "dataset_manifest_safety_flags_valid")


def test_index_row_missing_or_duplicate_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    rows.append(rows[0].copy())
    _write_csv(paths["index"], rows, list(rows[0]))
    _assert_blocked_for(paths, "index_row_count_valid")
    _assert_blocked_for(paths, "index_row_found_once")


def test_build_report_row_missing_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["build_report"])
    _write_csv(paths["build_report"], rows[:2], list(rows[0]))
    _assert_blocked_for(paths, "build_report_row_found_once")


def test_gate_plan_row_missing_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["gate_plan"])
    _write_csv(paths["gate_plan"], rows[:2], list(rows[0]))
    _assert_blocked_for(paths, "build_gate_plan_row_found_once")


def test_build_report_status_not_passed_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["build_report"])
    rows[0]["actual_dataset_index_build_status"] = "blocked"
    _write_csv(paths["build_report"], rows, list(rows[0]))
    _assert_blocked_for(paths, "build_report_status_passed")


def test_index_fields_mismatch_gate_plan_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    rows[0]["dataset_name"] = "wrong"
    _write_csv(paths["index"], rows, list(rows[0]))
    _assert_blocked_for(paths, "index_row_fields_match_gate_plan")


def test_index_hash_mismatch_current_file_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    rows[0]["packaged_ligand_sha256"] = "bad"
    _write_csv(paths["index"], rows, list(rows[0]))
    _assert_blocked_for(paths, "index_row_hashes_match_current_files")


def test_dataset_manifest_hash_mismatch_current_file_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    data = json.loads(paths["dataset_manifest"].read_text(encoding="utf-8"))
    data["sha256"]["packaged_ligands"]["BTK_C481_6DI9_pre_reaction"] = "bad"
    paths["dataset_manifest"].write_text(json.dumps(data), encoding="utf-8")
    _assert_blocked_for(paths, "dataset_manifest_hashes_match_current_files")


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


def test_training_tensor_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    bad_file = tmp_path / "data" / "derived" / "covalent_small" / "bad.pt"
    bad_file.parent.mkdir(parents=True, exist_ok=True)
    bad_file.write_bytes(b"not a tensor")
    _assert_blocked_for(paths, "forbidden_training_tensors_absent")


def test_archive_blocks(tmp_path):
    paths = _make_fixture(tmp_path)
    bad_file = tmp_path / "data" / "derived" / "covalent_small" / "bad.zip"
    bad_file.parent.mkdir(parents=True, exist_ok=True)
    bad_file.write_bytes(b"not an archive")
    _assert_blocked_for(paths, "forbidden_archives_absent")
