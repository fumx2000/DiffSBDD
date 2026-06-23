import argparse
import ast
import csv
import hashlib
import json
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from apply_training_dataset_design_review import (  # noqa: E402
    APPROVAL_TOKEN,
    DESIGN_ROOT,
    PLANNED_TRAINING_RECORD_FIELDS,
    run,
)
from test_training_dataset_design_gate import _make_fixture as _make_gate_fixture, _read_csv, _run as _run_gate, _write_csv  # noqa: E402


@pytest.fixture(autouse=True)
def _chdir_tmp_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _args(paths, approval_token=APPROVAL_TOKEN):
    return argparse.Namespace(
        training_dataset_design_gate_plan_csv=paths["training_gate_plan"],
        training_dataset_design_gate_report_csv=paths["training_gate_report"],
        snapshot_review_qa_report_csv=paths["qa_report"],
        snapshot_manifest_json=paths["snapshot_manifest"],
        snapshot_file_list_csv=paths["snapshot_file_list"],
        snapshot_review_report_csv=paths["snapshot_report"],
        index_csv=paths["index"],
        dataset_manifest_json=paths["dataset_manifest"],
        manifest_csv=paths["raw_manifest"],
        package_root=paths["package_root"],
        output_design_manifest_json=Path(DESIGN_ROOT) / "training_dataset_design_manifest.json",
        output_schema_report_csv=Path(DESIGN_ROOT) / "training_dataset_design_schema_report.csv",
        output_split_plan_csv=Path(DESIGN_ROOT) / "training_dataset_design_split_plan.csv",
        output_design_report_csv=Path(DESIGN_ROOT) / "training_dataset_design_report.csv",
        output_md=paths["training_gate_summary"].parent / "training_dataset_design_review_summary.md",
        approval_token=approval_token,
    )


def _make_fixture(tmp_path):
    paths = _make_gate_fixture(tmp_path)
    plan, report, code = _run_gate(paths)
    assert code == 0
    assert len(plan) == 3
    assert len(report) == 3
    paths["design_manifest"] = Path(DESIGN_ROOT) / "training_dataset_design_manifest.json"
    paths["schema_report"] = Path(DESIGN_ROOT) / "training_dataset_design_schema_report.csv"
    paths["split_plan"] = Path(DESIGN_ROOT) / "training_dataset_design_split_plan.csv"
    paths["design_report"] = Path(DESIGN_ROOT) / "training_dataset_design_report.csv"
    paths["design_summary"] = paths["training_gate_summary"].parent / "training_dataset_design_review_summary.md"
    return paths


def _run(paths, approval_token=APPROVAL_TOKEN):
    return run(_args(paths, approval_token))


def _assert_blocked_without_design_dir(paths, reason=None):
    schema, split, report, manifest, code = _run(paths)
    assert code == 1
    assert schema == []
    assert split == []
    assert report == []
    assert manifest == {}
    assert not Path(DESIGN_ROOT).exists()


def test_wrong_approval_token_blocks_without_design_dir(tmp_path):
    paths = _make_fixture(tmp_path)
    schema, split, report, manifest, code = _run(paths, "WRONG")
    assert code == 1
    assert schema == []
    assert split == []
    assert report == []
    assert manifest == {}
    assert not Path(DESIGN_ROOT).exists()


def test_success_writes_design_manifest_schema_split_and_report(tmp_path):
    paths = _make_fixture(tmp_path)
    input_hashes = {
        key: _sha(paths[key])
        for key in [
            "training_gate_plan",
            "training_gate_report",
            "qa_report",
            "snapshot_manifest",
            "snapshot_file_list",
            "snapshot_report",
            "index",
            "dataset_manifest",
            "raw_manifest",
        ]
    }
    schema, split, report, manifest, code = _run(paths)
    assert code == 0
    assert len(schema) >= len(PLANNED_TRAINING_RECORD_FIELDS)
    assert {row["field_name"] for row in _read_csv(paths["schema_report"])}.issuperset(PLANNED_TRAINING_RECORD_FIELDS)
    assert len(split) == 3
    assert len(_read_csv(paths["split_plan"])) == 3
    assert len(report) == 3
    assert len(_read_csv(paths["design_report"])) == 3
    parsed = json.loads(paths["design_manifest"].read_text(encoding="utf-8"))
    assert parsed["design_stage"] == "training_dataset_design_review_only_not_training"
    assert parsed["row_count"] == 3
    assert manifest["target_dataset_name"] == "covalent_small_pre_reaction_training_candidate_design"
    assert all(row["training_dataset_design_status"] == "training_dataset_design_passed" for row in report)
    assert all(row["planned_schema_fields_present"] == "true" for row in report)
    assert all(row["planned_mask_levels_present"] == "true" for row in report)
    assert all(row["planned_auxiliary_labels_present"] == "true" for row in report)
    assert all(row["split_plan_row_written"] == "true" for row in report)
    assert all(row["only_allowed_design_files_created"] == "true" for row in report)
    assert all(row["training_dataset_design_executed"] == "true" for row in report)
    assert all(row["real_training_tensor_generated"] == "false" for row in report)
    assert all(row["real_dataset_generated"] == "false" for row in report)
    assert all(row["dataloader_tensor_generated"] == "false" for row in report)
    assert all(row["torch_imported"] == "false" for row in report)
    assert all(row["checkpoint_loaded"] == "false" for row in report)
    assert all(row["model_initialized"] == "false" for row in report)
    assert all(row["training_ready"] == "false" for row in report)
    assert "Training Dataset Design Review Summary" in paths["design_summary"].read_text(encoding="utf-8")
    for key, before in input_hashes.items():
        assert _sha(paths[key]) == before


def test_design_dir_contains_only_four_review_files(tmp_path):
    paths = _make_fixture(tmp_path)
    _run(paths)
    files = sorted(path.name for path in Path(DESIGN_ROOT).rglob("*") if path.is_file())
    assert files == [
        "training_dataset_design_manifest.json",
        "training_dataset_design_report.csv",
        "training_dataset_design_schema_report.csv",
        "training_dataset_design_split_plan.csv",
    ]
    assert not list(Path(DESIGN_ROOT).rglob("*.pdb"))
    assert not list(Path(DESIGN_ROOT).rglob("*.sdf"))
    assert not list(Path(DESIGN_ROOT).rglob("*.cif"))
    assert not list(Path(DESIGN_ROOT).rglob("*.pt"))
    assert not list(Path(DESIGN_ROOT).rglob("*.pkl"))
    assert not list(Path(DESIGN_ROOT).rglob("*.npz"))
    assert not list(Path(DESIGN_ROOT).rglob("*.lmdb"))
    assert not list(Path(DESIGN_ROOT).rglob("*.tar"))
    assert not list(Path(DESIGN_ROOT).rglob("*.zip"))
    assert not list(Path(DESIGN_ROOT).rglob("*.tgz"))


def test_gate_snapshot_and_hash_blockers_do_not_create_design_dir(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["training_gate_report"])
    _write_csv(paths["training_gate_report"], rows[:2], list(rows[0]))
    _assert_blocked_without_design_dir(paths, "training_dataset_design_gate_report_row_found_once")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["training_gate_report"])
    rows[0]["training_dataset_design_gate_status"] = "blocked"
    _write_csv(paths["training_gate_report"], rows, list(rows[0]))
    _assert_blocked_without_design_dir(paths, "training_dataset_design_gate_status_passed")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["qa_report"])
    rows[0]["dataset_snapshot_review_qa_status"] = "blocked"
    _write_csv(paths["qa_report"], rows, list(rows[0]))
    _assert_blocked_without_design_dir(paths, "snapshot_review_qa_status_passed")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["snapshot_report"])
    rows[0]["dataset_snapshot_review_status"] = "blocked"
    _write_csv(paths["snapshot_report"], rows, list(rows[0]))
    _assert_blocked_without_design_dir(paths, "snapshot_review_status_passed")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    Path(rows[0]["packaged_ligand_sdf_path"]).write_text("changed\n$$$$\n", encoding="utf-8")
    _assert_blocked_without_design_dir(paths, "packaged_hashes_match_index_and_manifest")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["raw_manifest"])
    rows[1]["ligand_sdf_path"] = "wrong.sdf"
    _write_csv(paths["raw_manifest"], rows, list(rows[0]))
    _assert_blocked_without_design_dir(paths, "manifest_paths_match_index_sources")


def test_label_count_and_existing_output_blockers_do_not_create_design_dir(tmp_path):
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    rows[0]["supported_mask_levels"] = "A_warhead_only"
    _write_csv(paths["index"], rows, list(rows[0]))
    _assert_blocked_without_design_dir(paths, "mask_levels_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    rows[0]["required_auxiliary_labels"] = "warhead_type"
    _write_csv(paths["index"], rows, list(rows[0]))
    _assert_blocked_without_design_dir(paths, "auxiliary_labels_valid")
    paths = _make_fixture(tmp_path)
    rows = _read_csv(paths["index"])
    rows[0]["ligand_atom_count"] = "0"
    _write_csv(paths["index"], rows, list(rows[0]))
    _assert_blocked_without_design_dir(paths, "graph_counts_positive")
    paths = _make_fixture(tmp_path)
    Path(DESIGN_ROOT).mkdir(parents=True)
    schema, split, report, manifest, code = _run(paths)
    assert code == 1
    assert schema == []
    assert split == []
    assert report == []
    assert manifest == {}
    assert not paths["design_manifest"].exists()
    assert not paths["schema_report"].exists()
    assert not paths["split_plan"].exists()
    assert not paths["design_report"].exists()


def test_script_has_no_torch_import_checkpoint_model_or_training_calls():
    source = Path(__file__).resolve().parents[1] / "scripts" / "apply_training_dataset_design_review.py"
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
