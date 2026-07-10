from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import covapie_sample_index_materialization_smoke as smoke
from covalent_ext import covapie_sample_index_design_gate as design


ROOT = Path("data/derived/covalent_small/covapie_sample_index_materialization_smoke_v0")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    return json.loads((ROOT / "covapie_sample_index_materialization_smoke_manifest.json").read_text())


def _imports_name(path: Path, name: str) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(alias.name.split(".")[0] == name for alias in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == name:
            return True
    return False


def test_step14ac_precondition_and_materialization_outputs() -> None:
    prior = json.loads(design.MANIFEST_JSON.read_text())
    manifest = _manifest()
    assert prior["stage"] == design.STAGE
    assert prior["all_checks_passed"] is True
    assert prior["ready_for_covapie_sample_index_materialization_smoke"] is True
    assert manifest["stage"] == smoke.STAGE
    assert manifest["step_label"] == "Step 14AD"
    assert manifest["previous_stage"] == design.STAGE
    assert manifest["sample_index_written_current_step"] is True
    assert manifest["sample_index_csv_written"] is True
    assert manifest["sample_index_json_written"] is True


def test_sample_index_schema_identity_and_json_consistency() -> None:
    with (ROOT / "sample_index.csv").open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == smoke.SAMPLE_INDEX_FIELDS
        csv_rows = list(reader)
    json_rows = json.loads((ROOT / "sample_index.json").read_text())
    assert len(csv_rows) == len(json_rows) == 3
    assert [row["sample_index_row_id"] for row in csv_rows] == [
        "CYS_SG_SAMPLE_INDEX_000001", "CYS_SG_SAMPLE_INDEX_000002", "CYS_SG_SAMPLE_INDEX_000003",
    ]
    assert [f"{row['pdb_id']}/{row['expected_het_id']}" for row in csv_rows] == ["6BV6/JUG", "6BV8/JUG", "6BV5/JUG"]
    for csv_row, json_row in zip(csv_rows, json_rows):
        assert list(json_row) == smoke.SAMPLE_INDEX_FIELDS
        for field in smoke.SAMPLE_INDEX_FIELDS:
            if field in smoke.BOOL_FIELDS:
                assert (csv_row[field] == "True") is json_row[field]
            elif field in smoke.COUNT_FIELDS:
                assert int(csv_row[field]) == json_row[field]
            elif field == "bond_distance_angstrom":
                assert float(csv_row[field]) == json_row[field]
            else:
                assert csv_row[field] == json_row[field]


def test_rows_trace_to_derived_sources_and_preserve_boundaries() -> None:
    rows = _csv_rows(ROOT / "sample_index.csv")
    for row in rows:
        for field in smoke.PATH_FIELDS:
            assert Path(row[field]).is_file()
        assert int(row["protein_atom_count"]) > 0
        assert int(row["ligand_atom_count"]) > 0
        assert int(row["pocket_atom_count"]) > 0
        assert row["covalent_event_count"] == row["ligand_residue_atom_pair_count"] == "1"
        assert (row["covalent_residue_name"], row["covalent_residue_atom_name"]) == ("CYS", "SG")
        assert (row["ligand_comp_id"], row["ligand_covalent_atom_name"]) == ("JUG", "CAG")
        assert row["covalent_bond_atom_pair"] == "SG--CAG"
        assert row["conn_type_id"] == "covale"
        assert float(row["bond_distance_angstrom"]) > 0
        assert row["sample_index_status"] == "sample_index_materialized_from_qa_passed_sample"
        assert row["eligible_for_final_dataset_design"] == "False"
        assert row["ready_for_training_current_step"] == "False"
        assert row["feature_semantics_audit_required_before_training"] == "True"
        assert row["leakage_split_design_required_before_training"] == "True"


def test_schema_traceability_and_issue_audits_pass() -> None:
    schema = _csv_rows(ROOT / "covapie_sample_index_schema_validation_audit.csv")
    trace = _csv_rows(ROOT / "covapie_sample_index_row_traceability_audit.csv")
    issues = _csv_rows(ROOT / "covapie_sample_index_materialization_issue_inventory.csv")
    assert len(schema) == 33
    assert {row["schema_validation_status"] for row in schema} == {"passed"}
    assert len(trace) == 3
    assert {row["row_traceability_status"] for row in trace} == {"passed"}
    assert issues == [{
        "issue_id": "NO_SAMPLE_INDEX_MATERIALIZATION_ISSUES", "issue_scope": "all_rows",
        "sample_index_row_id": "", "pdb_id": "", "expected_het_id": "", "issue_severity": "none",
        "issue_type": "no_issues", "issue_description": "No sample index materialization issues detected.",
        "issue_status": "passed",
    }]


def test_manifest_readiness_masks_and_training_boundary() -> None:
    manifest = _manifest()
    assert manifest["all_checks_passed"] is True
    assert manifest["blocking_reasons"] == []
    assert manifest["sample_index_row_count"] == 3
    assert manifest["sample_index_schema_field_count"] == 33
    assert manifest["schema_validation_passed_count"] == 33
    assert manifest["row_traceability_passed_count"] == 3
    assert manifest["materialization_issue_count"] == 0
    assert manifest["accepted_pdb_het_pairs"] == ["6BV6/JUG", "6BV8/JUG", "6BV5/JUG"]
    assert manifest["ready_for_covapie_sample_index_qa_gate"] is True
    assert manifest["ready_for_covapie_final_dataset_design_gate"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_known_for_training"] is False
    assert manifest["unknown_atom_feature_policy_finalized_for_training"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["canonical_mask_task_names"] == smoke.CANONICAL_MASK_TASK_NAMES
    assert manifest["canonical_mask_task_aliases"] == ["A", "B", "B2", "B3", "C"]
    assert manifest["b3_scaffold_only_included"] is True
    assert manifest["no_extra_mask_tasks_added"] is True
    assert manifest["recommended_next_step"] == "covapie_sample_index_qa_gate"


def test_no_forbidden_artifacts_or_forbidden_imports() -> None:
    assert not smoke._forbidden_output_artifacts_absent() is False
    assert not any(path.is_file() and (path.name in smoke.FORBIDDEN_NAMES or path.suffix.lower() in smoke.FORBIDDEN_SUFFIXES) for path in ROOT.rglob("*"))
    for path in [
        Path("src/covalent_ext/covapie_sample_index_materialization_smoke.py"),
        Path("scripts/check_covapie_sample_index_materialization_smoke_v0.py"),
    ]:
        for name in ["torch", "numpy", "rdkit", "Bio", "gemmi", "requests", "urllib", "selenium", "playwright", "bs4"]:
            assert not _imports_name(path, name), (path, name)


def test_metadata_raw_and_protected_source_guards() -> None:
    metadata = Path("data/derived/covalent_small/external_metadata_index/covpdb/covpdb_complexes_metadata_manual.csv")
    assert hashlib.sha256(metadata.read_bytes()).hexdigest() == design.METADATA_CSV_SHA256
    raw_root = Path("data/raw/covalent_sources/covpdb/future_struct_conn_crosscheck_raw_v0")
    assert not subprocess.run(["git", "ls-files", str(raw_root)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
    assert not subprocess.run(["git", "diff", "--cached", "--name-only", "--", str(raw_root)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
    assert not smoke._path_diff_exists([design.OUTPUT_ROOT.as_posix()])
    assert not smoke._path_diff_exists([design.STEP14AB_ROOT.as_posix(), design.STEP14AA_ROOT.as_posix()])
    assert not smoke._path_diff_exists(["equivariant_diffusion/", "lightning_modules.py", "dataset.py", "data/prepare_crossdocked.py"])

