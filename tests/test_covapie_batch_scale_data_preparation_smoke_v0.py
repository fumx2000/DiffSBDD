from __future__ import annotations

import ast
import csv
import json
import subprocess
import sys
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import covapie_batch_scale_data_preparation_smoke as smoke


def _ensure_outputs() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/check_covapie_batch_scale_data_preparation_smoke_v0.py"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _manifest() -> dict:
    if not smoke.MANIFEST_JSON.is_file():
        _ensure_outputs()
    return json.loads(smoke.MANIFEST_JSON.read_text(encoding="utf-8"))


def _imports_name(path: Path, name: str) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] == name for alias in node.names):
                return True
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == name:
            return True
    return False


def _write_allowlist(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=smoke.ALLOWLIST_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _valid_allowlist_rows(count: int = 10) -> list[dict[str, str]]:
    rows = []
    for index in range(count):
        rows.append(
            {
                "candidate_id": f"COVAPIE_CAND_{index + 1:04d}",
                "source_dataset_name": "synthetic_unit_test_source",
                "source_dataset_version": "v0",
                "source_file_relative_path": f"synthetic/pdb_{index + 1:04d}.cif",
                "pdb_id": f"T{index + 1:03d}",
                "ligand_id": f"L{index + 1:03d}",
                "chain_id": "A",
                "residue_name": "CYS",
                "residue_index": str(100 + index),
                "residue_atom_name": "SG",
                "covalent_bond_atom_pair": "CYS:SG-LIG:C1",
                "restoration_policy_id": "known_restoration_template",
                "manual_review_status": "reviewed_pass" if index % 2 == 0 else "approved_for_smoke",
                "include_in_smoke": "true",
                "exclusion_reason": "",
            }
        )
    return rows


def test_check_script_passes_missing_allowlist_preflight() -> None:
    result = _ensure_outputs()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "covapie_batch_scale_data_preparation_smoke_v0_preflight_passed" in result.stdout
    manifest = _manifest()
    assert manifest["stage"] == smoke.STAGE
    assert manifest["previous_stage"] == smoke.PREVIOUS_STAGE
    assert manifest["project_name"] == "CovaPIE"
    assert manifest["step13ae_batch_scale_design_gate_validated"] is True
    assert manifest["naming_convention_validated"] is True
    assert manifest["all_checks_passed"] is True


def test_no_runtime_or_raw_parsing_imports() -> None:
    module_path = Path("src/covalent_ext/covapie_batch_scale_data_preparation_smoke.py")
    script_path = Path("scripts/check_covapie_batch_scale_data_preparation_smoke_v0.py")
    for name in ["torch", "rdkit", "gzip", "gemmi", "Bio"]:
        assert not _imports_name(module_path, name)
        assert not _imports_name(script_path, name)


def test_missing_allowlist_manifest_boundary() -> None:
    manifest = _manifest()
    assert manifest["allowlist_path"] == str(smoke.ALLOWLIST_PATH)
    assert manifest["allowlist_exists"] is False
    assert manifest["allowlist_read"] is False
    assert manifest["allowlist_row_count"] == 0
    assert manifest["included_candidate_count"] == 0
    assert manifest["allowlist_schema_validated"] is False
    assert manifest["candidate_selection_validated"] is False
    assert manifest["shard_plan_created"] is False
    assert manifest["shard_count"] == 0
    assert manifest["smoke_status"] == "blocked_due_to_missing_allowlist"
    assert manifest["batch_scale_smoke_preflight_passed"] is True
    assert manifest["covapie_batch_scale_data_preparation_smoke_passed"] is False
    assert manifest["ready_for_covapie_candidate_allowlist_creation_gate"] is True
    assert manifest["ready_for_covapie_batch_scale_raw_read_smoke"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert manifest["leakage_split_design_required_before_training"] is True
    assert manifest["recommended_next_step"] == "covapie_candidate_allowlist_creation_gate"
    assert manifest["blocking_reasons"] == ["missing_explicit_candidate_allowlist"]


def test_missing_allowlist_output_row_counts() -> None:
    manifest = _manifest()
    assert manifest["covapie_batch_smoke_precondition_audit_row_count"] == len(_csv_rows(smoke.PRECONDITION_AUDIT_CSV)) == 6
    assert manifest["covapie_batch_smoke_allowlist_discovery_audit_row_count"] == len(_csv_rows(smoke.ALLOWLIST_DISCOVERY_AUDIT_CSV)) == 1
    assert manifest["covapie_batch_smoke_allowlist_schema_audit_row_count"] == len(_csv_rows(smoke.ALLOWLIST_SCHEMA_AUDIT_CSV)) == 15
    assert manifest["covapie_batch_smoke_candidate_selection_audit_row_count"] == len(_csv_rows(smoke.CANDIDATE_SELECTION_AUDIT_CSV)) == 12
    assert manifest["covapie_batch_smoke_shard_plan_audit_row_count"] == len(_csv_rows(smoke.SHARD_PLAN_AUDIT_CSV)) == 1
    assert manifest["covapie_batch_smoke_provenance_audit_row_count"] == len(_csv_rows(smoke.PROVENANCE_AUDIT_CSV)) == 14
    assert manifest["covapie_batch_smoke_failure_audit_row_count"] == len(_csv_rows(smoke.FAILURE_AUDIT_CSV)) >= 1
    assert manifest["covapie_batch_smoke_execution_boundary_audit_row_count"] == len(_csv_rows(smoke.EXECUTION_BOUNDARY_AUDIT_CSV)) == 24
    assert manifest["covapie_batch_smoke_git_safety_audit_row_count"] == len(_csv_rows(smoke.GIT_SAFETY_AUDIT_CSV)) == 10
    assert manifest["covapie_batch_smoke_mask_scope_audit_row_count"] == len(_csv_rows(smoke.MASK_SCOPE_AUDIT_CSV)) == 5
    assert manifest["covapie_batch_smoke_feature_semantics_audit_row_count"] == len(_csv_rows(smoke.FEATURE_SEMANTICS_AUDIT_CSV)) == 12
    assert manifest["covapie_batch_smoke_leakage_split_audit_row_count"] == len(_csv_rows(smoke.LEAKAGE_SPLIT_AUDIT_CSV)) == 12


def test_missing_allowlist_audits_are_intentionally_blocked() -> None:
    discovery = _csv_rows(smoke.ALLOWLIST_DISCOVERY_AUDIT_CSV)[0]
    assert discovery["allowlist_exists"] == "False"
    assert discovery["allowlist_read"] == "False"
    assert discovery["smoke_status"] == "blocked_due_to_missing_allowlist"
    assert discovery["discovery_audit_passed"] == "True"
    assert discovery["blocking_reasons"] == "missing_explicit_candidate_allowlist"

    schema = _csv_rows(smoke.ALLOWLIST_SCHEMA_AUDIT_CSV)
    assert [row["allowlist_column"] for row in schema] == smoke.ALLOWLIST_COLUMNS
    assert {row["column_present"] for row in schema} == {"False"}
    assert {row["schema_audit_status"] for row in schema} == {"not_applicable_missing_allowlist"}
    assert {row["schema_audit_passed"] for row in schema} == {"True"}

    selection = _csv_rows(smoke.CANDIDATE_SELECTION_AUDIT_CSV)
    assert {row["current_status"] for row in selection} == {"not_evaluated_missing_allowlist"}
    assert {row["selection_audit_passed"] for row in selection} == {"True"}

    shard = _csv_rows(smoke.SHARD_PLAN_AUDIT_CSV)[0]
    assert shard["shard_plan_created"] == "False"
    assert shard["shard_size"] == "5"
    assert shard["candidate_count"] == "0"
    assert shard["sharding_status"] == "blocked_missing_allowlist"

    failure = _csv_rows(smoke.FAILURE_AUDIT_CSV)[0]
    assert failure["failure_code"] == "missing_candidate_allowlist"
    assert failure["severity"] == "blocking_for_smoke_not_training"
    assert failure["skip_or_block"] == "block_smoke"


def test_canonical_masks_feature_semantics_and_leakage_boundaries() -> None:
    mask = _csv_rows(smoke.MASK_SCOPE_AUDIT_CSV)
    assert [row["canonical_mask_task_name"] for row in mask] == smoke.CANONICAL_MASK_TASK_NAMES
    assert [row["display_alias"] for row in mask] == smoke.CANONICAL_MASK_TASK_ALIASES
    assert smoke.CANONICAL_MASK_TASK_NAMES[3] == "scaffold_only"
    assert smoke.CANONICAL_MASK_TASK_ALIASES[3] == "B3"
    assert {row["source_of_truth_status"] for row in mask} == {"long_semantic_name_source_of_truth"}
    assert {row["alias_status"] for row in mask} == {"display_only"}
    assert {row["mask_scope_status"] for row in mask} == {"preserved_from_step13ae"}
    assert {row["no_extra_mask_tasks_added"] for row in mask} == {"True"}
    assert {row["mask_scope_audit_passed"] for row in mask} == {"True"}

    feature = _csv_rows(smoke.FEATURE_SEMANTICS_AUDIT_CSV)
    assert {row["audit_required_before_training"] for row in feature} == {"True"}
    assert {row["fully_audited_claimed"] for row in feature} == {"False"}
    assert {row["blocking_for_batch_smoke"] for row in feature} == {"False"}
    assert {row["training_ready"] for row in feature} == {"False"}
    assert all(row["recommended_audit_step"] for row in feature)

    leakage = _csv_rows(smoke.LEAKAGE_SPLIT_AUDIT_CSV)
    assert {row["current_step_status"] for row in leakage} == {"placeholder_only_no_split_written"}
    assert {row["future_required_gate"] for row in leakage} == {"covapie_leakage_split_design_gate_before_training"}
    assert {row["blocking_for_training"] for row in leakage} == {"True"}
    assert {row["leakage_split_audit_passed"] for row in leakage} == {"True"}


def test_execution_git_and_manifest_safety_boundaries() -> None:
    boundary = {row["boundary_item"]: row for row in _csv_rows(smoke.EXECUTION_BOUNDARY_AUDIT_CSV)}
    assert boundary["batch_scale_smoke_preflight"]["current_step_status"] == "executed_preflight_only"
    for item in smoke.EXECUTION_BOUNDARY_ITEMS[1:]:
        assert boundary[item]["current_step_status"] == "not_executed_or_not_allowed"
        assert boundary[item]["boundary_audit_passed"] == "True"

    git_rows = {row["git_safety_item"]: row for row in _csv_rows(smoke.GIT_SAFETY_AUDIT_CSV)}
    assert ".pt" in git_rows["forbidden_suffix_check"]["command_or_check"]
    assert ".ckpt" in git_rows["forbidden_suffix_check"]["command_or_check"]
    assert ".npz" in git_rows["forbidden_suffix_check"]["command_or_check"]
    assert ".sdf" in git_rows["forbidden_suffix_check"]["command_or_check"]
    assert git_rows["raw_directory_not_staged"]["required_status"] == "empty"
    assert git_rows["raw_directory_not_tracked"]["required_status"] == "empty"
    assert {row["git_safety_audit_passed"] for row in git_rows.values()} == {"True"}

    manifest = _manifest()
    for key in [
        "batch_scale_smoke_executed",
        "raw_data_read",
        "raw_file_copied",
        "sdf_read",
        "sdf_generated",
        "sdf_modified",
        "sdf_copied",
        "pdb_read",
        "pdb_generated",
        "mmcif_text_read",
        "gzip_open_used",
        "rdkit_used",
        "biopdb_parser_used",
        "gemmi_used",
        "atom_site_text_scan_run",
        "candidate_materialized",
        "sample_index_written",
        "final_dataset_written",
        "split_assignments_written",
        "leakage_matrix_written",
        "adapter_instantiated",
        "torch_imported",
        "torch_tensor_created",
        "tensor_artifact_written",
        "npz_created",
        "pt_created",
        "checkpoint_loaded",
        "model_forward_called",
        "loss_compute_called",
        "backward_called",
        "optimizer_created",
        "trainer_fit_called",
        "training_allowed",
    ]:
        assert manifest[key] is False
    assert manifest["batch_scale_preflight_executed"] is True


def test_synthetic_valid_allowlist_preflight_only(tmp_path: Path) -> None:
    allowlist = tmp_path / "covapie_batch_smoke_candidate_allowlist.csv"
    _write_allowlist(allowlist, _valid_allowlist_rows(10))
    result = smoke.run_covapie_batch_scale_data_preparation_smoke_v0(allowlist)
    manifest = result["manifest"]
    assert manifest["allowlist_exists"] is True
    assert manifest["allowlist_read"] is True
    assert manifest["allowlist_row_count"] == 10
    assert manifest["included_candidate_count"] == 10
    assert manifest["allowlist_schema_validated"] is True
    assert manifest["candidate_selection_validated"] is True
    assert manifest["shard_plan_created"] is True
    assert manifest["shard_count"] == 2
    assert manifest["smoke_status"] == "allowlist_validated_preflight_only"
    assert manifest["covapie_batch_scale_data_preparation_smoke_passed"] is True
    assert manifest["ready_for_covapie_batch_scale_raw_read_smoke"] is True
    assert manifest["ready_for_training"] is False
    assert result["shard_rows"][0]["candidate_count"] == 5
    assert result["shard_rows"][1]["candidate_count"] == 5
    assert result["shard_rows"][0]["shard_candidate_ids"].startswith("COVAPIE_CAND_0001")


def test_synthetic_invalid_allowlist_validation_only(tmp_path: Path) -> None:
    rows = _valid_allowlist_rows(10)
    rows[0]["candidate_id"] = rows[1]["candidate_id"]
    rows[2]["residue_name"] = "SER"
    rows[3]["source_file_relative_path"] = "../unsafe.cif"
    allowlist = tmp_path / "bad_allowlist.csv"
    _write_allowlist(allowlist, rows)
    result = smoke.run_covapie_batch_scale_data_preparation_smoke_v0(allowlist)
    manifest = result["manifest"]
    assert manifest["allowlist_exists"] is True
    assert manifest["allowlist_read"] is True
    assert manifest["smoke_status"] == "blocked_due_to_invalid_allowlist"
    assert manifest["covapie_batch_scale_data_preparation_smoke_passed"] is False
    assert manifest["ready_for_covapie_candidate_allowlist_creation_gate"] is True
    reasons = set(result["validation"]["blocking_reasons"])
    assert {"duplicate_candidate_id", "non_cys_included", "unsafe_source_file_relative_path"} <= reasons


def test_no_forbidden_artifacts_or_protected_diffs() -> None:
    forbidden_suffixes = set(smoke.FORBIDDEN_COMMITTABLE_SUFFIXES)
    assert not [
        path
        for path in smoke.OUTPUT_ROOT.rglob("*")
        if path.is_file() and path.suffix in forbidden_suffixes
    ]
    assert subprocess.run(["git", "diff", "--quiet", "--", "equivariant_diffusion/", "lightning_modules.py"]).returncode == 0
    assert subprocess.run(["git", "diff", "--quiet", "--", "dataset.py", "data/prepare_crossdocked.py"]).returncode == 0
    assert subprocess.run(["git", "diff", "--cached", "--quiet", "--", "data/raw/covalent_sources"]).returncode == 0
    assert subprocess.run(["git", "ls-files", "data/raw/covalent_sources"], stdout=subprocess.PIPE, text=True).stdout.strip() == ""
