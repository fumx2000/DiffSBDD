import csv
import hashlib
import json
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_real_packaging_execution_qa import (  # noqa: E402
    APPROVAL_TOKEN,
    REPORT_COLUMNS,
    TARGETS,
    build_markdown,
    build_qa,
    write_csv,
    write_markdown,
)


PACKAGE_ROOT = Path("data/derived/covalent_small/packaging_real_review_only")


PLAN_COLUMNS = [
    "execution_gate_plan_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "planned_package_root",
    "planned_protein_relative_path",
    "planned_ligand_relative_path",
    "planned_metadata_relative_path",
    "planned_protein_destination_path",
    "planned_ligand_destination_path",
    "planned_metadata_destination_path",
    "protein_pdb_path",
    "protein_pdb_sha256",
    "ligand_sdf_path",
    "ligand_sdf_sha256",
    "ligand_atom_count",
    "ligand_heavy_atom_count",
    "ligand_bond_count",
    "protein_atom_count",
    "protein_residue_count",
    "reactive_residue_chain",
    "reactive_residue_id",
    "reactive_residue_type",
    "reactive_atom_name",
    "ligand_reactive_atom_id",
    "scaffold_atoms",
    "linker_atoms",
    "warhead_atoms",
    "scaffold_atom_count",
    "linker_atom_count",
    "warhead_atom_count",
    "execution_gate_stage",
    "explicit_approval_required_before_copy",
    "ready_for_real_packaging_execution_after_approval",
    "directories_created",
    "files_copied",
    "metadata_written",
    "package_archive_created",
    "real_dataset_generated",
    "training_ready",
]

EXECUTION_REPORT_COLUMNS = [
    "candidate_id",
    "source_sample_id",
    "pre_reaction_sample_id",
    "approval_token_valid",
    "execution_gate_plan_row_found_once",
    "execution_gate_report_row_found_once",
    "manifest_candidate_row_found_once",
    "manifest_source_row_found_once",
    "execution_gate_status_passed",
    "source_mapping_valid",
    "planned_layout_valid",
    "source_protein_exists",
    "source_ligand_exists",
    "source_protein_hash_matches_plan",
    "source_ligand_hash_matches_plan",
    "manifest_candidate_paths_match_plan",
    "graph_counts_positive",
    "directories_created",
    "protein_copied",
    "ligand_copied",
    "metadata_written",
    "packaged_protein_exists",
    "packaged_ligand_exists",
    "packaged_metadata_exists",
    "packaged_protein_hash_matches_source",
    "packaged_ligand_hash_matches_source",
    "metadata_hashes_match_packaged_files",
    "manifest_modified",
    "source_pdb_modified",
    "source_sdf_modified",
    "package_archive_created",
    "real_training_tensor_generated",
    "real_dataset_generated",
    "pre_reaction_transform_ready",
    "training_ready",
    "real_packaging_execution_status",
    "blocking_reasons",
    "recommended_next_action",
]


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
        "plan": base / "real_packaging_execution_gate_plan.csv",
        "execution_report": base / "real_packaging_execution_report.csv",
        "manifest": tmp_path / "data" / "raw" / "covalent_small" / "manifests" / "manifest_real_small.csv",
        "qa_report": base / "real_packaging_execution_qa_report.csv",
        "summary": tmp_path / "docs" / "real_packaging_execution_qa_summary.md",
        "package_root": tmp_path / PACKAGE_ROOT,
    }


def _metadata(plan):
    return {
        "sample_id": plan["pre_reaction_sample_id"],
        "source_sample_id": plan["source_sample_id"],
        "pre_reaction_sample_id": plan["pre_reaction_sample_id"],
        "protein": {
            "source_path": plan["protein_pdb_path"],
            "packaged_relative_path": plan["planned_protein_relative_path"],
            "packaged_path": plan["planned_protein_destination_path"],
            "sha256": plan["protein_pdb_sha256"],
            "atom_count": plan["protein_atom_count"],
            "residue_count": plan["protein_residue_count"],
        },
        "ligand": {
            "source_path": plan["ligand_sdf_path"],
            "packaged_relative_path": plan["planned_ligand_relative_path"],
            "packaged_path": plan["planned_ligand_destination_path"],
            "sha256": plan["ligand_sdf_sha256"],
            "atom_count": plan["ligand_atom_count"],
            "heavy_atom_count": plan["ligand_heavy_atom_count"],
            "bond_count": plan["ligand_bond_count"],
            "ligand_reactive_atom_id": plan["ligand_reactive_atom_id"],
        },
        "provenance": {
            "source_manifest": "manifest.csv",
            "execution_gate_plan_csv": "plan.csv",
            "execution_gate_report_csv": "report.csv",
            "approval_token": APPROVAL_TOKEN,
            "packaging_stage": "real_packaging_execution_step_8ag",
        },
        "safety_flags": {
            "manifest_modified": False,
            "source_sdf_modified": False,
            "source_pdb_modified": False,
            "package_archive_created": False,
            "real_training_tensor_generated": False,
            "real_dataset_generated": False,
            "training_ready": False,
        },
    }


def _make_fixture(tmp_path):
    paths = _paths(tmp_path)
    plan_rows = []
    report_rows = []
    manifest_rows = []
    for candidate_id, source_id in TARGETS.items():
        residue_id = "481" if source_id == "BTK_C481_6DI9" else "12"
        source_protein = tmp_path / "data" / "raw" / "covalent_small" / "proteins" / f"{source_id}.pdb"
        source_ligand = tmp_path / "data" / "derived" / "covalent_small" / "ligands_pre_reaction" / f"{candidate_id}.sdf"
        source_protein.parent.mkdir(parents=True, exist_ok=True)
        source_ligand.parent.mkdir(parents=True, exist_ok=True)
        source_protein.write_text(f"HEADER {source_id}\nATOM      1  SG  CYS A{residue_id:>4}\n", encoding="utf-8")
        source_ligand.write_text(f"{candidate_id}\n  RDKit\n\n", encoding="utf-8")
        protein_rel = f"proteins/{source_id}.pdb"
        ligand_rel = f"ligands_pre_reaction/{candidate_id}.sdf"
        metadata_rel = f"metadata/{candidate_id}.json"
        packaged_protein = tmp_path / PACKAGE_ROOT / protein_rel
        packaged_ligand = tmp_path / PACKAGE_ROOT / ligand_rel
        packaged_metadata = tmp_path / PACKAGE_ROOT / metadata_rel
        packaged_protein.parent.mkdir(parents=True, exist_ok=True)
        packaged_ligand.parent.mkdir(parents=True, exist_ok=True)
        packaged_metadata.parent.mkdir(parents=True, exist_ok=True)
        packaged_protein.write_bytes(source_protein.read_bytes())
        packaged_ligand.write_bytes(source_ligand.read_bytes())
        plan = {
            "execution_gate_plan_id": candidate_id,
            "source_sample_id": source_id,
            "pre_reaction_sample_id": candidate_id,
            "planned_package_root": str(PACKAGE_ROOT),
            "planned_protein_relative_path": protein_rel,
            "planned_ligand_relative_path": ligand_rel,
            "planned_metadata_relative_path": metadata_rel,
            "planned_protein_destination_path": str(PACKAGE_ROOT / protein_rel),
            "planned_ligand_destination_path": str(PACKAGE_ROOT / ligand_rel),
            "planned_metadata_destination_path": str(PACKAGE_ROOT / metadata_rel),
            "protein_pdb_path": str(source_protein),
            "protein_pdb_sha256": _sha(source_protein),
            "ligand_sdf_path": str(source_ligand),
            "ligand_sdf_sha256": _sha(source_ligand),
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
            "execution_gate_stage": "real_packaging_execution_gate_only_not_training",
            "explicit_approval_required_before_copy": "true",
            "ready_for_real_packaging_execution_after_approval": "true",
            "directories_created": "false",
            "files_copied": "false",
            "metadata_written": "false",
            "package_archive_created": "false",
            "real_dataset_generated": "false",
            "training_ready": "false",
        }
        packaged_metadata.write_text(json.dumps(_metadata(plan), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        plan_rows.append(plan)
        report_rows.append(
            {
                "candidate_id": candidate_id,
                "source_sample_id": source_id,
                "pre_reaction_sample_id": candidate_id,
                "approval_token_valid": "true",
                "execution_gate_plan_row_found_once": "true",
                "execution_gate_report_row_found_once": "true",
                "manifest_candidate_row_found_once": "true",
                "manifest_source_row_found_once": "true",
                "execution_gate_status_passed": "true",
                "source_mapping_valid": "true",
                "planned_layout_valid": "true",
                "source_protein_exists": "true",
                "source_ligand_exists": "true",
                "source_protein_hash_matches_plan": "true",
                "source_ligand_hash_matches_plan": "true",
                "manifest_candidate_paths_match_plan": "true",
                "graph_counts_positive": "true",
                "directories_created": "true",
                "protein_copied": "true",
                "ligand_copied": "true",
                "metadata_written": "true",
                "packaged_protein_exists": "true",
                "packaged_ligand_exists": "true",
                "packaged_metadata_exists": "true",
                "packaged_protein_hash_matches_source": "true",
                "packaged_ligand_hash_matches_source": "true",
                "metadata_hashes_match_packaged_files": "true",
                "manifest_modified": "false",
                "source_pdb_modified": "false",
                "source_sdf_modified": "false",
                "package_archive_created": "false",
                "real_training_tensor_generated": "false",
                "real_dataset_generated": "false",
                "pre_reaction_transform_ready": "false",
                "training_ready": "false",
                "real_packaging_execution_status": "real_packaging_execution_passed",
                "blocking_reasons": "",
                "recommended_next_action": "build_real_packaging_execution_qa_not_training",
            }
        )
        manifest_rows.append({"sample_id": source_id, "protein_pdb_path": str(source_protein), "ligand_sdf_path": f"raw/{source_id}.sdf"})
        manifest_rows.append({"sample_id": candidate_id, "protein_pdb_path": str(source_protein), "ligand_sdf_path": str(source_ligand)})
    _write_csv(paths["plan"], plan_rows, PLAN_COLUMNS)
    _write_csv(paths["execution_report"], report_rows, EXECUTION_REPORT_COLUMNS)
    _write_csv(paths["manifest"], manifest_rows, ["sample_id", "protein_pdb_path", "ligand_sdf_path"])
    return paths, plan_rows, report_rows, manifest_rows


def _run(paths):
    return build_qa(
        execution_report_csv=paths["execution_report"],
        execution_gate_plan_csv=paths["plan"],
        manifest_csv=paths["manifest"],
        package_root=paths["package_root"],
    )


def _report_for(rows, candidate_id):
    return next(row for row in rows if row["candidate_id"] == candidate_id)


def _all_tracked_files(tmp_path):
    return sorted(path for path in tmp_path.rglob("*") if path.is_file())


def _hashes(paths):
    return {path: _sha(path) for path in paths}


def test_real_packaging_execution_qa_success(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, _, _, _ = _make_fixture(tmp_path)
    before_files = _all_tracked_files(tmp_path)
    before_hashes = _hashes(before_files)

    rows = _run(paths)
    write_csv(rows, paths["qa_report"], REPORT_COLUMNS)
    write_markdown(build_markdown(rows, paths["package_root"]), paths["summary"])

    assert len(rows) == 3
    assert len(_read_csv(paths["qa_report"])) == 3
    assert "Real Packaging Execution QA Summary" in paths["summary"].read_text(encoding="utf-8")
    for row in rows:
        assert row["real_packaging_execution_qa_status"] == "real_packaging_execution_qa_passed"
        assert row["protein_hash_chain_valid"] == "true"
        assert row["ligand_hash_chain_valid"] == "true"
        assert row["metadata_ids_valid"] == "true"
        assert row["metadata_paths_valid"] == "true"
        assert row["metadata_hashes_valid"] == "true"
        assert row["metadata_provenance_valid"] == "true"
        assert row["metadata_safety_flags_valid"] == "true"
        assert row["files_copied_by_qa"] == "false"
        assert row["metadata_written_by_qa"] == "false"
        assert row["manifest_modified_by_qa"] == "false"
        assert row["source_files_modified_by_qa"] == "false"
        assert row["real_dataset_generated"] == "false"
        assert row["training_ready"] == "false"
    for path, digest in before_hashes.items():
        assert _sha(path) == digest
    assert sorted(path for path in _all_tracked_files(tmp_path) if path not in before_files) == [paths["qa_report"], paths["summary"]]


@pytest.mark.parametrize(
    "mutator,field,reason",
    [
        (lambda paths, plan, report, manifest: __import__("shutil").rmtree(paths["package_root"]), "package_root_exists", "package_root_missing"),
        (lambda paths, plan, report, manifest: __import__("shutil").rmtree(paths["package_root"] / "proteins"), "package_subdirs_exist", "package_subdirs_missing"),
        (lambda paths, plan, report, manifest: (paths["package_root"] / "proteins" / "extra.pdb").write_text("x\n", encoding="utf-8"), "packaged_file_counts_valid", "packaged_file_counts_invalid"),
        (lambda paths, plan, report, manifest: report.pop(), "execution_report_row_found_once", "execution_report_row_not_found_once"),
        (lambda paths, plan, report, manifest: plan.pop(), "execution_gate_plan_row_found_once", "execution_gate_plan_row_not_found_once"),
        (lambda paths, plan, report, manifest: report.__setitem__(0, {**report[0], "real_packaging_execution_status": "blocked"}), "execution_report_status_passed", "execution_report_status_not_passed"),
        (lambda paths, plan, report, manifest: report.__setitem__(0, {**report[0], "training_ready": "true"}), "execution_report_flags_passed", "execution_report_flags_not_passed"),
        (lambda paths, plan, report, manifest: Path(plan[0]["planned_protein_destination_path"]).unlink(), "packaged_protein_exists", "packaged_protein_missing"),
        (lambda paths, plan, report, manifest: Path(plan[0]["planned_ligand_destination_path"]).unlink(), "packaged_ligand_exists", "packaged_ligand_missing"),
        (lambda paths, plan, report, manifest: Path(plan[0]["planned_metadata_destination_path"]).unlink(), "packaged_metadata_exists", "packaged_metadata_missing"),
        (lambda paths, plan, report, manifest: Path(plan[0]["planned_metadata_destination_path"]).write_text("{bad json", encoding="utf-8"), "metadata_json_parseable", "metadata_json_not_parseable"),
        (lambda paths, plan, report, manifest: _mutate_metadata(plan[0], {"sample_id": "wrong"}), "metadata_ids_valid", "metadata_ids_invalid"),
        (lambda paths, plan, report, manifest: _mutate_metadata(plan[0], {"protein": {"source_path": "wrong"}}), "metadata_paths_valid", "metadata_paths_invalid"),
        (lambda paths, plan, report, manifest: _mutate_metadata(plan[0], {"protein": {"sha256": "wrong"}}), "metadata_hashes_valid", "metadata_hashes_invalid"),
        (lambda paths, plan, report, manifest: _mutate_metadata(plan[0], {"provenance": {"approval_token": "wrong"}}), "metadata_provenance_valid", "metadata_provenance_invalid"),
        (lambda paths, plan, report, manifest: _mutate_metadata(plan[0], {"safety_flags": {"training_ready": True}}), "metadata_safety_flags_valid", "metadata_safety_flags_invalid"),
        (lambda paths, plan, report, manifest: Path(plan[0]["protein_pdb_path"]).write_text("changed\n", encoding="utf-8"), "protein_hash_chain_valid", "protein_hash_chain_invalid"),
        (lambda paths, plan, report, manifest: Path(plan[0]["ligand_sdf_path"]).write_text("changed\n", encoding="utf-8"), "ligand_hash_chain_valid", "ligand_hash_chain_invalid"),
        (lambda paths, plan, report, manifest: (paths["package_root"] / "bad.pt").write_text("x\n", encoding="utf-8"), "forbidden_training_tensors_absent", "forbidden_training_tensors_present"),
        (lambda paths, plan, report, manifest: (paths["package_root"] / "bad.zip").write_text("x\n", encoding="utf-8"), "forbidden_archives_absent", "forbidden_archives_present"),
    ],
)
def test_real_packaging_execution_qa_blocks_invalid_inputs(tmp_path, monkeypatch, mutator, field, reason):
    monkeypatch.chdir(tmp_path)
    paths, plan, report, manifest = _make_fixture(tmp_path)
    mutator(paths, plan, report, manifest)
    _write_csv(paths["plan"], plan, PLAN_COLUMNS)
    _write_csv(paths["execution_report"], report, EXECUTION_REPORT_COLUMNS)
    _write_csv(paths["manifest"], manifest, ["sample_id", "protein_pdb_path", "ligand_sdf_path"])

    rows = _run(paths)

    assert any(row[field] == "false" for row in rows)
    assert any(reason in row["blocking_reasons"] for row in rows)
    assert any(row["real_packaging_execution_qa_status"] == "blocked" for row in rows)
    assert all(row["training_ready"] == "false" for row in rows)


def _mutate_metadata(plan, patch):
    path = Path(plan["planned_metadata_destination_path"])
    data = json.loads(path.read_text(encoding="utf-8"))
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(data.get(key), dict):
            data[key].update(value)
        else:
            data[key] = value
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_manifest_path_mismatch_blocks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, plan, report, manifest = _make_fixture(tmp_path)
    manifest[1]["ligand_sdf_path"] = "wrong.sdf"
    _write_csv(paths["manifest"], manifest, ["sample_id", "protein_pdb_path", "ligand_sdf_path"])

    rows = _run(paths)

    assert "manifest_paths_mismatch_sources" in _report_for(rows, plan[0]["execution_gate_plan_id"])["blocking_reasons"]


def test_qa_does_not_write_package_or_inputs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths, _, _, _ = _make_fixture(tmp_path)
    protected = [
        *paths["package_root"].rglob("*"),
        paths["manifest"],
        paths["plan"],
        paths["execution_report"],
    ]
    protected = sorted(path for path in protected if path.is_file())
    before = _hashes(protected)

    rows = _run(paths)

    assert len(rows) == 3
    assert _hashes(protected) == before
    assert not paths["qa_report"].exists()
    assert not paths["summary"].exists()
