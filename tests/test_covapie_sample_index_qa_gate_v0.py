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

from covalent_ext import covapie_sample_index_qa_gate as qa
from covalent_ext import covapie_sample_index_materialization_smoke as material

ROOT = Path("data/derived/covalent_small/covapie_sample_index_qa_gate_v0")


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    return json.loads((ROOT / "covapie_sample_index_qa_gate_manifest.json").read_text())


def _imports(path: Path, name: str) -> bool:
    tree = ast.parse(path.read_text())
    return any((isinstance(node, ast.Import) and any(alias.name.split(".")[0] == name for alias in node.names)) or (isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == name) for node in ast.walk(tree))


def test_step14ad_precondition_and_independent_qa_outputs() -> None:
    prior = json.loads(material.MANIFEST_JSON.read_text())
    manifest = _manifest()
    assert prior["stage"] == material.STAGE
    assert prior["all_checks_passed"] is True
    assert prior["ready_for_covapie_sample_index_qa_gate"] is True
    assert manifest["stage"] == qa.STAGE
    assert manifest["step_label"] == "Step 14AE"
    assert manifest["previous_stage"] == material.STAGE
    assert manifest["all_checks_passed"] is True


def test_row_qa_and_source_traceability_are_independently_passed() -> None:
    row_qa = _rows(ROOT / "covapie_sample_index_row_qa.csv")
    trace = _rows(ROOT / "covapie_sample_index_source_traceability_qa.csv")
    assert len(row_qa) == len(trace) == 3
    assert [r["sample_index_row_id"] for r in row_qa] == ["CYS_SG_SAMPLE_INDEX_000001", "CYS_SG_SAMPLE_INDEX_000002", "CYS_SG_SAMPLE_INDEX_000003"]
    assert [f"{r['pdb_id']}/{r['expected_het_id']}" for r in row_qa] == ["6BV6/JUG", "6BV8/JUG", "6BV5/JUG"]
    for key in ["csv_json_semantically_consistent", "sample_index_row_id_unique", "pdb_het_pair_unique", "identity_fields_nonempty", "all_six_artifact_paths_exist", "count_fields_valid", "covalent_event_identity_valid", "bond_distance_smoke_sanity_passed", "sample_index_status_valid", "boundary_flags_valid", "source_traceability_passed", "approved_for_final_dataset_design_by_qa"]:
        assert {r[key] for r in row_qa} == {"True"}
    assert {r["row_qa_status"] for r in row_qa} == {"passed"}
    assert {r["source_traceability_qa_status"] for r in trace} == {"passed"}


def test_schema_fingerprints_and_issue_inventory_pass() -> None:
    schema = _rows(ROOT / "covapie_sample_index_schema_qa.csv")
    fingerprints = _rows(ROOT / "covapie_sample_index_fingerprint_audit.csv")
    issues = _rows(ROOT / "covapie_sample_index_qa_issue_inventory.csv")
    assert len(schema) == 33
    assert {r["schema_qa_status"] for r in schema} == {"passed"}
    assert len(fingerprints) == 2
    assert {r["fingerprint_status"] for r in fingerprints} == {"recorded_and_verified"}
    for row in fingerprints:
        assert hashlib.sha256(Path(row["artifact_path"]).read_bytes()).hexdigest() == row["sha256"]
    assert issues[0]["issue_id"] == "NO_SAMPLE_INDEX_QA_ISSUES"


def test_approval_is_not_training_readiness_and_preserves_source_flag() -> None:
    source = _rows(material.SAMPLE_INDEX_CSV)
    manifest = _manifest()
    assert {r["eligible_for_final_dataset_design"] for r in source} == {"False"}
    assert manifest["qa_approved_for_final_dataset_design_count"] == 3
    assert manifest["source_eligible_for_final_dataset_design_true_count"] == 0
    assert manifest["ready_for_covapie_final_dataset_design_gate"] is True
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_known_for_training"] is False
    assert manifest["unknown_atom_feature_policy_finalized_for_training"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["recommended_next_step"] == "covapie_final_dataset_design_gate"


def test_safety_masks_and_no_forbidden_imports_or_outputs() -> None:
    safety = _rows(ROOT / "covapie_sample_index_qa_safety_audit.csv")
    manifest = _manifest()
    assert {r["safety_passed"] for r in safety} == {"True"}
    assert manifest["canonical_mask_task_names"] == ["warhead_only", "linker_plus_warhead", "scaffold_plus_warhead", "scaffold_only", "scaffold_plus_linker_plus_warhead"]
    assert manifest["canonical_mask_task_aliases"] == ["A", "B", "B2", "B3", "C"]
    assert manifest["b3_scaffold_only_included"] is True
    assert not any(p.is_file() and (p.name in qa.FORBIDDEN_NAMES or p.suffix.lower() in qa.FORBIDDEN_SUFFIXES) for p in ROOT.rglob("*"))
    for path in [Path("src/covalent_ext/covapie_sample_index_qa_gate.py"), Path("scripts/check_covapie_sample_index_qa_gate_v0.py")]:
        for name in ["torch", "numpy", "rdkit", "Bio", "gemmi", "requests", "urllib", "selenium", "playwright", "bs4"]:
            assert not _imports(path, name), (path, name)


def test_metadata_raw_sample_index_and_protected_diff_guards() -> None:
    assert hashlib.sha256(material.design.METADATA_CSV.read_bytes()).hexdigest() == material.design.METADATA_CSV_SHA256
    raw = material.design.RAW_ROOT
    assert not subprocess.run(["git", "ls-files", str(raw)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
    assert not subprocess.run(["git", "diff", "--cached", "--name-only", "--", str(raw)], text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
    assert not qa._path_diff_exists([material.SAMPLE_INDEX_CSV.as_posix(), material.SAMPLE_INDEX_JSON.as_posix()])
    assert not qa._path_diff_exists([material.OUTPUT_ROOT.as_posix(), material.design.OUTPUT_ROOT.as_posix(), material.design.STEP14AB_ROOT.as_posix(), material.design.STEP14AA_ROOT.as_posix()])
    assert not qa._path_diff_exists(["equivariant_diffusion/", "lightning_modules.py", "dataset.py", "data/prepare_crossdocked.py"])
