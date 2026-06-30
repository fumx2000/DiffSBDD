from __future__ import annotations

import csv
import importlib
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import torch

from covalent_ext.checkpoint_compatible_model_instantiation import (
    BEST_CONFIG_CANDIDATE_PATH,
    build_checkpoint_compatible_config_v0,
    build_checkpoint_compatible_input_contract_v0,
    load_checkpoint_shape_reference_v0,
    load_config_preview_v0,
)
from covalent_ext.model_input_adapter import expected_reactive_atom_region_for_mask_level_v0
from covalent_ext.npz_dataset import CovalentNPZDataset
from covalent_ext.real_covalent_backward_smoke import (
    GRAD_TABLE_CSV as STEP12E_GRAD_TABLE_CSV,
    MANIFEST_JSON as STEP12E_MANIFEST_JSON,
    SUMMARY_MD as STEP12E_SUMMARY_MD,
    validate_step12b_validator_behavior_v0,
)
from covalent_ext.real_covalent_pretrained_forward_loss_smoke import (
    CANONICAL_MASK_LEVELS,
    CHECKPOINT_PATH,
    FORBIDDEN_ARTIFACT_SUFFIXES,
    INPUT_SOURCE,
    PROTECTED_SOURCE_PATHS,
    SELECTED_REAL_SAMPLE_INDEX,
    UNKNOWN_ATOM_FEATURE_POLICY,
    build_checkpoint_compatible_real_model_batch_v0,
    build_real_covalent_forward_loss_batch_bundle_v0,
)
from covalent_ext.pretrained_masked_loss_smoke import CONFIG_PREVIEW_PATH


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STAGE = "real_covalent_feature_semantics_audit_v0"
PREVIOUS_STAGE = "real_covalent_backward_smoke_v0"

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_feature_semantics_audit_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_feature_semantics_audit_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_feature_semantics_audit_manifest.json"
AUDIT_TABLE_CSV = OUTPUT_ROOT / "real_covalent_feature_semantics_audit_table.csv"
SUMMARY_MD = Path("docs/real_covalent_feature_semantics_audit_v0_summary.md")

CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX = {
    6: 0,
    7: 1,
    8: 2,
    16: 3,
    5: 4,
    35: 5,
    17: 6,
    15: 7,
    53: 8,
    9: 9,
}

CHECKPOINT_10D_INDEX_TO_ATOM_SYMBOL = {
    0: "C",
    1: "N",
    2: "O",
    3: "S",
    4: "B",
    5: "Br",
    6: "Cl",
    7: "P",
    8: "I",
    9: "F",
}

ATOMIC_NUMBER_TO_SYMBOL = {
    5: "B",
    6: "C",
    7: "N",
    8: "O",
    9: "F",
    15: "P",
    16: "S",
    17: "Cl",
    35: "Br",
    53: "I",
}


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _expect(condition: bool, message: str, blockers: list[str]) -> None:
    if not condition:
        blockers.append(message)


def _text_bool(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def _finite_scalar(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _source_diff_exists(paths: list[str] = PROTECTED_SOURCE_PATHS) -> bool:
    unstaged = subprocess.run(
        ["git", "diff", "--quiet", "--", *paths],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    staged = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", *paths],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return unstaged.returncode != 0 or staged.returncode != 0


def _forbidden_artifacts_created(root: str | Path = OUTPUT_ROOT) -> bool:
    root_path = Path(root)
    if not root_path.exists():
        return False
    return any(path.is_file() and path.suffix in FORBIDDEN_ARTIFACT_SUFFIXES for path in root_path.rglob("*"))


def _mapping_as_jsonable(mapping: dict[int, Any]) -> dict[str, Any]:
    return {str(key): value for key, value in sorted(mapping.items())}


def _symbol_counts(counter: Counter[int]) -> dict[str, int]:
    result: dict[str, int] = {}
    for atomic_number, count in sorted(counter.items()):
        result[ATOMIC_NUMBER_TO_SYMBOL.get(int(atomic_number), f"Z{int(atomic_number)}")] = int(count)
    return result


def _canonical_project_atom_encoder() -> dict[str, int]:
    return {CHECKPOINT_10D_INDEX_TO_ATOM_SYMBOL[index]: index for index in sorted(CHECKPOINT_10D_INDEX_TO_ATOM_SYMBOL)}


def validate_step12e_outputs_v0() -> bool:
    if not STEP12E_MANIFEST_JSON.is_file() or not STEP12E_GRAD_TABLE_CSV.is_file() or not STEP12E_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 12E outputs are missing")
    manifest = _load_json(STEP12E_MANIFEST_JSON)
    rows = _read_csv(STEP12E_GRAD_TABLE_CSV)
    blockers: list[str] = []
    expected_manifest = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_pretrained_forward_loss_smoke_v0",
        "step12d_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "input_source": INPUT_SOURCE,
        "selected_sample_index": str(SELECTED_REAL_SAMPLE_INDEX),
        "selected_artifact_is_real_covalent": True,
        "selected_artifact_is_synthetic_only": False,
        "checkpoint_path": str(CHECKPOINT_PATH),
        "requested_device": "cpu",
        "resolved_device": "cpu",
        "batch_size": 2,
        "num_workers": 0,
        "canonical_mask_levels": CANONICAL_MASK_LEVELS,
        "canonical_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "attempted_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "passed_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "failed_mask_level_count": 0,
        "model_instantiated": True,
        "strict_load_success": True,
        "pretrained_weights_loaded": True,
        "pretrained_base_integration_proven": True,
        "model_strict_loaded_once": True,
        "model_forward_called": True,
        "model_forward_call_count": len(CANONICAL_MASK_LEVELS),
        "all_level_forward_call_count_exactly_one": True,
        "all_adapted_batches_valid": True,
        "all_model_inputs_valid": True,
        "all_diffsbdd_like_inputs_valid": True,
        "all_checkpoint_compatible_real_batches_constructed": True,
        "no_synthetic_fallback_used": True,
        "all_losses_computed": True,
        "all_losses_finite": True,
        "all_losses_require_grad": True,
        "selected_loss_key": "masked_loss_total_dry",
        "aggregate_loss_reduction": "mean",
        "aggregate_loss_finite": True,
        "aggregate_loss_requires_grad": True,
        "backward_called": True,
        "backward_call_count": 1,
        "backward_exactly_once": True,
        "backward_success": True,
        "finite_nonzero_gradients": True,
        "grad_nan_count": 0,
        "grad_inf_count": 0,
        "real_covalent_backward_smoke_passed": True,
        "real_covalent_backward_contract_proven": True,
        "real_covalent_single_optimizer_step_smoke_allowed": True,
        "recommended_next_step": "real_covalent_single_optimizer_step_smoke",
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "original_diffsbdd_source_modified": False,
        "forbidden_artifacts_created": False,
        "all_checks_passed": True,
        "blocking_reasons": [],
    }
    for key, expected in expected_manifest.items():
        _expect(manifest.get(key) == expected, f"step12e_{key}_invalid:{manifest.get(key)!r}", blockers)
    _expect(_finite_scalar(manifest.get("aggregate_loss_value")), "step12e_aggregate_loss_value_not_finite", blockers)
    _expect(len(rows) == 6, f"step12e_grad_table_row_count_invalid:{len(rows)}", blockers)
    loss_rows = [row for row in rows if row.get("row_type") == "mask_level_loss"]
    aggregate_rows = [row for row in rows if row.get("row_type") == "aggregate_backward"]
    _expect(len(loss_rows) == len(CANONICAL_MASK_LEVELS), f"step12e_loss_row_count_invalid:{len(loss_rows)}", blockers)
    _expect(len(aggregate_rows) == 1, f"step12e_aggregate_row_count_invalid:{len(aggregate_rows)}", blockers)
    _expect([row.get("mask_level") for row in loss_rows] == CANONICAL_MASK_LEVELS, "step12e_loss_mask_order_invalid", blockers)
    for row in loss_rows:
        mask_level = row.get("mask_level", "")
        expected_region = "context" if mask_level == "B3_scaffold_only" else "target"
        checks = {
            "expected_reactive_atom_region": expected_region,
            "status": "passed",
            "forward_call_count": "1",
            "loss_computed": "True",
            "loss_finite": "True",
            "loss_requires_grad": "True",
            "selected_loss_key": "masked_loss_total_dry",
            "no_synthetic_fallback_used": "True",
        }
        for key, expected in checks.items():
            _expect(row.get(key) == expected, f"step12e_loss_{mask_level}_{key}_invalid:{row.get(key)!r}", blockers)
    if aggregate_rows:
        row = aggregate_rows[0]
        checks = {
            "mask_level": "ALL",
            "aggregate_loss_reduction": "mean",
            "aggregate_loss_finite": "True",
            "aggregate_loss_requires_grad": "True",
            "backward_called": "True",
            "backward_call_count": "1",
            "backward_success": "True",
            "finite_nonzero_gradients": "True",
            "grad_nan_count": "0",
            "grad_inf_count": "0",
        }
        for key, expected in checks.items():
            _expect(row.get(key) == expected, f"step12e_aggregate_{key}_invalid:{row.get(key)!r}", blockers)
    summary = STEP12E_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "real covalent backward smoke, not training",
        "feature semantics audit",
        "recommended_next_step: real_covalent_single_optimizer_step_smoke",
    ]:
        _expect(snippet in summary, f"step12e_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def audit_checkpoint_feature_contract_v0() -> dict[str, Any]:
    blockers: list[str] = []
    checkpoint_reference = load_checkpoint_shape_reference_v0(CHECKPOINT_PATH)
    preview_result = load_config_preview_v0(CONFIG_PREVIEW_PATH)
    preview = preview_result.get("preview", {})
    compatible_config = (
        build_checkpoint_compatible_config_v0(preview, BEST_CONFIG_CANDIDATE_PATH)
        if preview
        else {"compatible_config_built": False, "blocking_reasons": ["config_preview_missing"]}
    )
    input_contract = (
        build_checkpoint_compatible_input_contract_v0(checkpoint_reference, preview, compatible_config)
        if compatible_config.get("compatible_config_built")
        else {"input_contract_built": False, "blocking_reasons": ["compatible_config_not_built"]}
    )
    blockers.extend(checkpoint_reference.get("blocking_reasons", []))
    blockers.extend(preview_result.get("blocking_reasons", []))
    blockers.extend(compatible_config.get("blocking_reasons", []))
    blockers.extend(input_contract.get("blocking_reasons", []))
    ligand_dim = int(input_contract.get("target_ligand_feature_dim", 0))
    pocket_dim = int(input_contract.get("target_pocket_feature_dim", 0))
    constants = importlib.import_module("constants")
    repo_encoder = dict(constants.dataset_params.get("crossdock", {}).get("atom_encoder", {}))
    repo_decoder = list(constants.dataset_params.get("crossdock", {}).get("atom_decoder", []))
    project_encoder = _canonical_project_atom_encoder()
    repo_mapping_matches = repo_encoder == project_encoder and repo_decoder == [
        CHECKPOINT_10D_INDEX_TO_ATOM_SYMBOL[index] for index in range(10)
    ]
    if not repo_mapping_matches:
        blockers.append("repo_crossdock_10d_mapping_mismatch")
    if ligand_dim != 10:
        blockers.append("checkpoint_ligand_feature_dim_not_10")
    if pocket_dim != 10:
        blockers.append("checkpoint_pocket_feature_dim_not_10")
    semantics_source = "repo_dataset_info_or_config" if repo_mapping_matches else "dimension_only_plus_project_constant_mapping"
    directly_encoded = bool(repo_mapping_matches)
    return {
        "checkpoint_path": str(CHECKPOINT_PATH),
        "checkpoint_ligand_feature_dim": ligand_dim,
        "checkpoint_pocket_feature_dim": pocket_dim,
        "ligand_feature_dim_is_10": ligand_dim == 10,
        "pocket_feature_dim_is_10": pocket_dim == 10,
        "checkpoint_10d_feature_contract_detected": ligand_dim == 10 and pocket_dim == 10,
        "checkpoint_feature_semantics_source": semantics_source,
        "checkpoint_feature_semantics_directly_encoded": directly_encoded,
        "checkpoint_10d_mapping_project": _mapping_as_jsonable(CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX),
        "checkpoint_10d_index_to_atom_symbol": _mapping_as_jsonable(CHECKPOINT_10D_INDEX_TO_ATOM_SYMBOL),
        "repo_crossdock_atom_encoder": repo_encoder,
        "repo_crossdock_atom_decoder": repo_decoder,
        "checkpoint_10d_mapping_matches_project_mapping": repo_mapping_matches,
        "input_contract": input_contract,
        "status": "passed" if not blockers else "blocked",
        "blocking_reasons": sorted(set(blockers)),
    }


def audit_real_covalent_atom_vocabulary_v0() -> dict[str, Any]:
    blockers: list[str] = []
    dataset = CovalentNPZDataset(SELECTED_REAL_SAMPLE_INDEX)
    sample_ids: list[str] = []
    ligand_counts: Counter[int] = Counter()
    protein_counts: Counter[int] = Counter()
    for sample in dataset:
        sample_ids.append(str(sample["sample_id"]))
        ligand_counts.update(int(value) for value in sample["ligand_atomic_numbers"].detach().cpu().tolist())
        protein_counts.update(int(value) for value in sample["protein_atomic_numbers"].detach().cpu().tolist())
    vocab = set(CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX)
    ligand_unique = sorted(ligand_counts)
    protein_unique = sorted(protein_counts)
    ligand_unknown_numbers = [value for value in ligand_unique if value not in vocab]
    protein_unknown_numbers = [value for value in protein_unique if value not in vocab]
    ligand_unknown_count = sum(ligand_counts[value] for value in ligand_unknown_numbers)
    protein_unknown_count = sum(protein_counts[value] for value in protein_unknown_numbers)
    if ligand_unknown_count:
        blockers.append("ligand_unknown_atoms_present")
    if protein_unknown_count:
        blockers.append("protein_unknown_atoms_present")
    return {
        "sample_count": len(dataset),
        "sample_ids": sample_ids,
        "ligand_atom_count_total": int(sum(ligand_counts.values())),
        "protein_atom_count_total": int(sum(protein_counts.values())),
        "ligand_atomic_numbers_unique": ligand_unique,
        "protein_atomic_numbers_unique": protein_unique,
        "ligand_atom_symbol_counts": _symbol_counts(ligand_counts),
        "protein_atom_symbol_counts": _symbol_counts(protein_counts),
        "ligand_unknown_atom_numbers": ligand_unknown_numbers,
        "protein_unknown_atom_numbers": protein_unknown_numbers,
        "ligand_unknown_atom_count": int(ligand_unknown_count),
        "protein_unknown_atom_count": int(protein_unknown_count),
        "all_ligand_atoms_in_checkpoint_10d_vocab": ligand_unknown_count == 0,
        "all_protein_atoms_in_checkpoint_10d_vocab": protein_unknown_count == 0,
        "unknown_atom_policy_name": UNKNOWN_ATOM_FEATURE_POLICY,
        "unknown_atom_policy_would_trigger": ligand_unknown_count > 0 or protein_unknown_count > 0,
        "unknown_atom_policy_triggered": ligand_unknown_count > 0 or protein_unknown_count > 0,
        "zero_vector_unknown_atom_policy_safe": ligand_unknown_count == 0 and protein_unknown_count == 0,
        "status": "passed" if not blockers else "blocked",
        "blocking_reasons": sorted(set(blockers)),
    }


def _row_sums_valid(one_hot: torch.Tensor) -> bool:
    if one_hot.ndim != 2 or one_hot.shape[0] == 0:
        return False
    row_sums = one_hot.detach().cpu().sum(dim=1)
    return bool(torch.allclose(row_sums, torch.ones_like(row_sums)))


def audit_checkpoint_compatible_conversion_semantics_v0(input_contract: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    for mask_level in CANONICAL_MASK_LEVELS:
        level_blockers: list[str] = []
        expected_region = expected_reactive_atom_region_for_mask_level_v0(mask_level)
        try:
            bundle = build_real_covalent_forward_loss_batch_bundle_v0(mask_level, "cpu")
            checkpoint_batch = build_checkpoint_compatible_real_model_batch_v0(
                bundle["diffsbdd_like"],
                input_contract,
                mask_level,
                "cpu",
            )
            metadata = checkpoint_batch["metadata"]
            data_batch = checkpoint_batch["data_batch"]
            ligand_one_hot = data_batch["lig_one_hot"]
            pocket_one_hot = data_batch["pocket_one_hot"]
            ligand_row_sums_valid = _row_sums_valid(ligand_one_hot)
            pocket_row_sums_valid = _row_sums_valid(pocket_one_hot)
            ligand_feature_dim = int(ligand_one_hot.shape[1])
            pocket_feature_dim = int(pocket_one_hot.shape[1])
            ligand_rows_equal_coords = int(ligand_one_hot.shape[0]) == int(data_batch["lig_coords"].shape[0])
            pocket_rows_equal_coords = int(pocket_one_hot.shape[0]) == int(data_batch["pocket_coords"].shape[0])
            if checkpoint_batch["status"] != "passed":
                level_blockers.extend(checkpoint_batch.get("blocking_reasons", []))
            if ligand_feature_dim != 10:
                level_blockers.append("ligand_feature_dim_not_10")
            if pocket_feature_dim != 10:
                level_blockers.append("pocket_feature_dim_not_10")
            if not ligand_rows_equal_coords:
                level_blockers.append("ligand_one_hot_row_count_mismatch")
            if not pocket_rows_equal_coords:
                level_blockers.append("pocket_one_hot_row_count_mismatch")
            if not ligand_row_sums_valid:
                level_blockers.append("ligand_one_hot_row_sums_invalid")
            if not pocket_row_sums_valid:
                level_blockers.append("pocket_one_hot_row_sums_invalid")
            if int(metadata["ligand_unknown_atom_count"]) != 0:
                level_blockers.append("ligand_unknown_atom_count_nonzero")
            if int(metadata["pocket_unknown_atom_count"]) != 0:
                level_blockers.append("pocket_unknown_atom_count_nonzero")
            if metadata["expected_reactive_atom_region"] != expected_region:
                level_blockers.append("expected_reactive_atom_region_invalid")
            if not metadata["no_synthetic_fallback_used"]:
                level_blockers.append("synthetic_fallback_used")
            row = {
                "row_type": "mask_level_conversion",
                "mask_level": mask_level,
                "expected_reactive_atom_region": expected_region,
                "checkpoint_compatible_batch_constructed": bool(metadata["checkpoint_compatible_batch_constructed"]),
                "ligand_feature_dim": ligand_feature_dim,
                "pocket_feature_dim": pocket_feature_dim,
                "ligand_one_hot_rows_equal_ligand_coords_rows": ligand_rows_equal_coords,
                "pocket_one_hot_rows_equal_pocket_coords_rows": pocket_rows_equal_coords,
                "ligand_one_hot_row_sums_valid": ligand_row_sums_valid,
                "pocket_one_hot_row_sums_valid": pocket_row_sums_valid,
                "ligand_unknown_atom_count": int(metadata["ligand_unknown_atom_count"]),
                "pocket_unknown_atom_count": int(metadata["pocket_unknown_atom_count"]),
                "no_synthetic_fallback_used": bool(metadata["no_synthetic_fallback_used"]),
                "status": "passed" if not level_blockers else "blocked",
                "blocking_reasons": sorted(set(level_blockers)),
            }
        except Exception as exc:
            level_blockers.append(f"conversion_audit_failed:{type(exc).__name__}:{exc}")
            row = {
                "row_type": "mask_level_conversion",
                "mask_level": mask_level,
                "expected_reactive_atom_region": expected_region,
                "checkpoint_compatible_batch_constructed": False,
                "ligand_feature_dim": 0,
                "pocket_feature_dim": 0,
                "ligand_one_hot_rows_equal_ligand_coords_rows": False,
                "pocket_one_hot_rows_equal_pocket_coords_rows": False,
                "ligand_one_hot_row_sums_valid": False,
                "pocket_one_hot_row_sums_valid": False,
                "ligand_unknown_atom_count": -1,
                "pocket_unknown_atom_count": -1,
                "no_synthetic_fallback_used": False,
                "status": "blocked",
                "blocking_reasons": sorted(set(level_blockers)),
            }
        rows.append(row)
        blockers.extend(f"{mask_level}:{reason}" for reason in row["blocking_reasons"])
    return {
        "rows": rows,
        "audited_mask_level_count": len(rows),
        "passed_mask_level_count": sum(1 for row in rows if row["status"] == "passed"),
        "failed_mask_level_count": sum(1 for row in rows if row["status"] != "passed"),
        "all_checkpoint_compatible_batches_constructed": all(row["checkpoint_compatible_batch_constructed"] for row in rows),
        "all_ligand_one_hot_row_sums_valid": all(row["ligand_one_hot_row_sums_valid"] for row in rows),
        "all_pocket_one_hot_row_sums_valid": all(row["pocket_one_hot_row_sums_valid"] for row in rows),
        "all_ligand_unknown_atom_count_zero": all(row["ligand_unknown_atom_count"] == 0 for row in rows),
        "all_pocket_unknown_atom_count_zero": all(row["pocket_unknown_atom_count"] == 0 for row in rows),
        "no_synthetic_fallback_used": all(row["no_synthetic_fallback_used"] for row in rows),
        "status": "passed" if not blockers else "blocked",
        "blocking_reasons": sorted(set(blockers)),
    }


def build_real_covalent_feature_semantics_audit_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step12e_validated = validate_step12e_outputs_v0()
    except Exception as exc:
        step12e_validated = False
        blockers.append(f"step12e_validation_failed:{type(exc).__name__}:{exc}")
    try:
        step12b_validated = validate_step12b_validator_behavior_v0()
    except Exception as exc:
        step12b_validated = False
        blockers.append(f"step12b_validation_failed:{type(exc).__name__}:{exc}")

    checkpoint_contract = audit_checkpoint_feature_contract_v0()
    real_vocab = audit_real_covalent_atom_vocabulary_v0()
    conversion = audit_checkpoint_compatible_conversion_semantics_v0(checkpoint_contract["input_contract"])
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    blockers.extend(checkpoint_contract.get("blocking_reasons", []))
    blockers.extend(real_vocab.get("blocking_reasons", []))
    blockers.extend(conversion.get("blocking_reasons", []))
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")
    blockers = sorted(set(reason for reason in blockers if reason))

    dimension_contract_passed = bool(
        checkpoint_contract["ligand_feature_dim_is_10"]
        and checkpoint_contract["pocket_feature_dim_is_10"]
        and checkpoint_contract["checkpoint_10d_feature_contract_detected"]
        and conversion["all_checkpoint_compatible_batches_constructed"]
        and conversion["all_ligand_one_hot_row_sums_valid"]
        and conversion["all_pocket_one_hot_row_sums_valid"]
    )
    mapping_confirmed = bool(
        checkpoint_contract["checkpoint_feature_semantics_directly_encoded"]
        and checkpoint_contract["checkpoint_10d_mapping_matches_project_mapping"]
    )
    unknown_policy_triggered = bool(real_vocab["unknown_atom_policy_triggered"])
    hard_pass = bool(
        step12e_validated
        and step12b_validated
        and dimension_contract_passed
        and mapping_confirmed
        and real_vocab["all_ligand_atoms_in_checkpoint_10d_vocab"]
        and real_vocab["all_protein_atoms_in_checkpoint_10d_vocab"]
        and not unknown_policy_triggered
        and real_vocab["zero_vector_unknown_atom_policy_safe"]
        and conversion["audited_mask_level_count"] == len(CANONICAL_MASK_LEVELS)
        and conversion["passed_mask_level_count"] == len(CANONICAL_MASK_LEVELS)
        and conversion["all_ligand_unknown_atom_count_zero"]
        and conversion["all_pocket_unknown_atom_count_zero"]
        and conversion["no_synthetic_fallback_used"]
        and not source_modified
        and not forbidden_artifacts
        and not blockers
    )
    soft_pass = bool(
        step12e_validated
        and step12b_validated
        and dimension_contract_passed
        and not mapping_confirmed
        and real_vocab["all_ligand_atoms_in_checkpoint_10d_vocab"]
        and real_vocab["all_protein_atoms_in_checkpoint_10d_vocab"]
        and not unknown_policy_triggered
        and conversion["passed_mask_level_count"] == len(CANONICAL_MASK_LEVELS)
        and not source_modified
        and not forbidden_artifacts
        and not blockers
    )
    audit_passed = hard_pass or soft_pass
    mapping_source_needs_confirmation = bool(audit_passed and not mapping_confirmed)
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step12e_validated": step12e_validated,
        "step12b_mask_level_aware_validator_validated": step12b_validated,
        "input_source": INPUT_SOURCE,
        "selected_sample_index": str(SELECTED_REAL_SAMPLE_INDEX),
        "selected_artifact_is_real_covalent": True,
        "selected_artifact_is_synthetic_only": False,
        "checkpoint_path": str(CHECKPOINT_PATH),
        "checkpoint_ligand_feature_dim": checkpoint_contract["checkpoint_ligand_feature_dim"],
        "checkpoint_pocket_feature_dim": checkpoint_contract["checkpoint_pocket_feature_dim"],
        "ligand_feature_dim_is_10": checkpoint_contract["ligand_feature_dim_is_10"],
        "pocket_feature_dim_is_10": checkpoint_contract["pocket_feature_dim_is_10"],
        "checkpoint_10d_feature_contract_detected": checkpoint_contract["checkpoint_10d_feature_contract_detected"],
        "checkpoint_feature_semantics_source": checkpoint_contract["checkpoint_feature_semantics_source"],
        "checkpoint_feature_semantics_directly_encoded": checkpoint_contract[
            "checkpoint_feature_semantics_directly_encoded"
        ],
        "checkpoint_10d_mapping_project": checkpoint_contract["checkpoint_10d_mapping_project"],
        "checkpoint_10d_mapping_matches_project_mapping": checkpoint_contract[
            "checkpoint_10d_mapping_matches_project_mapping"
        ],
        "sample_count": real_vocab["sample_count"],
        "sample_ids": real_vocab["sample_ids"],
        "ligand_atom_count_total": real_vocab["ligand_atom_count_total"],
        "protein_atom_count_total": real_vocab["protein_atom_count_total"],
        "ligand_atomic_numbers_unique": real_vocab["ligand_atomic_numbers_unique"],
        "protein_atomic_numbers_unique": real_vocab["protein_atomic_numbers_unique"],
        "ligand_unknown_atom_numbers": real_vocab["ligand_unknown_atom_numbers"],
        "protein_unknown_atom_numbers": real_vocab["protein_unknown_atom_numbers"],
        "ligand_unknown_atom_count": real_vocab["ligand_unknown_atom_count"],
        "protein_unknown_atom_count": real_vocab["protein_unknown_atom_count"],
        "all_ligand_atoms_in_checkpoint_10d_vocab": real_vocab["all_ligand_atoms_in_checkpoint_10d_vocab"],
        "all_protein_atoms_in_checkpoint_10d_vocab": real_vocab["all_protein_atoms_in_checkpoint_10d_vocab"],
        "unknown_atom_policy_name": real_vocab["unknown_atom_policy_name"],
        "unknown_atom_policy_triggered": unknown_policy_triggered,
        "zero_vector_unknown_atom_policy_safe": real_vocab["zero_vector_unknown_atom_policy_safe"],
        "canonical_mask_levels": list(CANONICAL_MASK_LEVELS),
        "canonical_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "audited_mask_level_count": conversion["audited_mask_level_count"],
        "passed_mask_level_count": conversion["passed_mask_level_count"],
        "failed_mask_level_count": conversion["failed_mask_level_count"],
        "all_checkpoint_compatible_batches_constructed": conversion["all_checkpoint_compatible_batches_constructed"],
        "all_ligand_one_hot_row_sums_valid": conversion["all_ligand_one_hot_row_sums_valid"],
        "all_pocket_one_hot_row_sums_valid": conversion["all_pocket_one_hot_row_sums_valid"],
        "all_ligand_unknown_atom_count_zero": conversion["all_ligand_unknown_atom_count_zero"],
        "all_pocket_unknown_atom_count_zero": conversion["all_pocket_unknown_atom_count_zero"],
        "no_synthetic_fallback_used": conversion["no_synthetic_fallback_used"],
        "feature_semantics_dimension_contract_passed": dimension_contract_passed,
        "feature_semantics_mapping_confirmed": mapping_confirmed,
        "feature_semantics_known_after_audit": hard_pass,
        "feature_semantics_mapping_source_needs_confirmation": mapping_source_needs_confirmation,
        "real_covalent_feature_semantics_audit_passed": audit_passed,
        "real_covalent_cuda_forward_backward_smoke_allowed": soft_pass,
        "real_covalent_single_optimizer_step_smoke_allowed": hard_pass,
        "recommended_next_step": "real_covalent_single_optimizer_step_smoke"
        if hard_pass
        else (
            "real_covalent_feature_semantics_mapping_confirmation"
            if soft_pass
            else "real_covalent_feature_semantics_audit_debug"
        ),
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "quality_claim_allowed": False,
        "parameter_update_allowed": False,
        "checkpoint_save_allowed": False,
        "model_save_allowed": False,
        "original_diffsbdd_source_modified": source_modified,
        "forbidden_artifacts_created": forbidden_artifacts,
        "all_checks_passed": audit_passed,
        "blocking_reasons": blockers,
    }
    audit_table_rows = [
        {
            "row_type": "checkpoint_feature_contract",
            "mask_level": "",
            "checkpoint_ligand_feature_dim": checkpoint_contract["checkpoint_ligand_feature_dim"],
            "checkpoint_pocket_feature_dim": checkpoint_contract["checkpoint_pocket_feature_dim"],
            "checkpoint_feature_semantics_source": checkpoint_contract["checkpoint_feature_semantics_source"],
            "checkpoint_feature_semantics_directly_encoded": checkpoint_contract[
                "checkpoint_feature_semantics_directly_encoded"
            ],
            "checkpoint_10d_mapping_project": checkpoint_contract["checkpoint_10d_mapping_project"],
            "checkpoint_10d_mapping_matches_project_mapping": checkpoint_contract[
                "checkpoint_10d_mapping_matches_project_mapping"
            ],
            "status": checkpoint_contract["status"],
            "blocking_reasons": checkpoint_contract["blocking_reasons"],
        },
        {
            "row_type": "real_atom_vocabulary",
            "mask_level": "",
            "sample_count": real_vocab["sample_count"],
            "ligand_atomic_numbers_unique": real_vocab["ligand_atomic_numbers_unique"],
            "protein_atomic_numbers_unique": real_vocab["protein_atomic_numbers_unique"],
            "ligand_unknown_atom_count": real_vocab["ligand_unknown_atom_count"],
            "protein_unknown_atom_count": real_vocab["protein_unknown_atom_count"],
            "unknown_atom_policy_triggered": real_vocab["unknown_atom_policy_triggered"],
            "zero_vector_unknown_atom_policy_safe": real_vocab["zero_vector_unknown_atom_policy_safe"],
            "status": real_vocab["status"],
            "blocking_reasons": real_vocab["blocking_reasons"],
        },
    ]
    audit_table_rows.extend(conversion["rows"])
    audit_table_rows.append(
        {
            "row_type": "decision",
            "mask_level": "",
            "feature_semantics_dimension_contract_passed": dimension_contract_passed,
            "feature_semantics_mapping_confirmed": mapping_confirmed,
            "feature_semantics_known_after_audit": hard_pass,
            "real_covalent_single_optimizer_step_smoke_allowed": hard_pass,
            "recommended_next_step": manifest["recommended_next_step"],
            "status": "passed" if audit_passed else "blocked",
            "blocking_reasons": blockers,
        }
    )
    return {
        "manifest": manifest,
        "audit_table_rows": audit_table_rows,
        "report_sections": {
            "step12e_precondition": {
                "step12e_validated": step12e_validated,
                "step12b_mask_level_aware_validator_validated": step12b_validated,
            },
            "checkpoint_feature_contract": {
                "checkpoint_ligand_feature_dim": checkpoint_contract["checkpoint_ligand_feature_dim"],
                "checkpoint_pocket_feature_dim": checkpoint_contract["checkpoint_pocket_feature_dim"],
                "checkpoint_feature_semantics_source": checkpoint_contract["checkpoint_feature_semantics_source"],
                "checkpoint_10d_mapping_matches_project_mapping": checkpoint_contract[
                    "checkpoint_10d_mapping_matches_project_mapping"
                ],
            },
            "real_atom_vocabulary": {
                "sample_count": real_vocab["sample_count"],
                "ligand_atomic_numbers_unique": real_vocab["ligand_atomic_numbers_unique"],
                "protein_atomic_numbers_unique": real_vocab["protein_atomic_numbers_unique"],
                "ligand_unknown_atom_count": real_vocab["ligand_unknown_atom_count"],
                "protein_unknown_atom_count": real_vocab["protein_unknown_atom_count"],
            },
            "mask_level_conversion_semantics": {
                "audited_mask_level_count": conversion["audited_mask_level_count"],
                "passed_mask_level_count": conversion["passed_mask_level_count"],
                "all_ligand_one_hot_row_sums_valid": conversion["all_ligand_one_hot_row_sums_valid"],
                "all_pocket_one_hot_row_sums_valid": conversion["all_pocket_one_hot_row_sums_valid"],
            },
            "unknown_atom_policy": {
                "unknown_atom_policy_name": real_vocab["unknown_atom_policy_name"],
                "unknown_atom_policy_triggered": real_vocab["unknown_atom_policy_triggered"],
                "zero_vector_unknown_atom_policy_safe": real_vocab["zero_vector_unknown_atom_policy_safe"],
            },
            "feature_semantics_decision": {
                "feature_semantics_dimension_contract_passed": dimension_contract_passed,
                "feature_semantics_mapping_confirmed": mapping_confirmed,
                "feature_semantics_known_after_audit": hard_pass,
            },
            "safety_boundary": {
                "model_forward_called": False,
                "loss_compute_called": False,
                "backward_called": False,
                "optimizer_created": False,
                "optimizer_step_called": False,
                "training_step_called": False,
                "trainer_fit_called": False,
                "checkpoint_saved": False,
                "model_saved": False,
                "tensor_dump_saved": False,
                "npz_created": False,
                "original_diffsbdd_source_modified": source_modified,
                "forbidden_artifacts_created": forbidden_artifacts,
            },
            "next_step_decision": {
                "real_covalent_feature_semantics_audit_passed": audit_passed,
                "real_covalent_single_optimizer_step_smoke_allowed": hard_pass,
                "real_covalent_cuda_forward_backward_smoke_allowed": soft_pass,
                "recommended_next_step": manifest["recommended_next_step"],
            },
        },
    }
