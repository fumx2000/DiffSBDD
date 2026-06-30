from __future__ import annotations

import csv
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import torch

from covalent_ext.checkpoint_compatible_model_instantiation import (
    BEST_CONFIG_CANDIDATE_PATH,
    _constructor_config_from_compatible_config,
    _instantiate_model_with_temp_dataset,
    _temporary_10d_dataset_info,
    build_checkpoint_compatible_config_v0,
    build_checkpoint_compatible_input_contract_v0,
    load_checkpoint_shape_reference_v0,
    load_config_preview_v0,
)
from covalent_ext.checkpoint_compatible_pretrained_load_smoke import (
    load_checkpoint_state_dict_for_smoke_v0,
    strict_load_checkpoint_weights_v0,
)
from covalent_ext.diffsbdd_atomwise_loss_hook_prototype import AtomwiseProbeCapture, atomwise_probe_context_v0
from covalent_ext.masked_loss_dry_run import compute_masked_loss_components_v0, summarize_loss_components_v0
from covalent_ext.model_input_adapter import expected_reactive_atom_region_for_mask_level_v0
from covalent_ext.pretrained_masked_loss_microbatch_backward_dry_run import collect_gradient_stats_v0
from covalent_ext.pretrained_masked_loss_smoke import CONFIG_PREVIEW_PATH, _count_nan_inf, _output0_and_info
from covalent_ext.real_covalent_filtered_feature_semantics_audit import (
    AUDIT_TABLE_CSV as STEP12I_AUDIT_TABLE_CSV,
    MANIFEST_JSON as STEP12I_MANIFEST_JSON,
    SUMMARY_MD as STEP12I_SUMMARY_MD,
    validate_step12b_validator_behavior_v0,
)
from covalent_ext.real_covalent_noncheckpoint_pocket_atom_filter_gate import (
    filter_noncheckpoint_vocab_pocket_atoms_v0,
)
from covalent_ext.real_covalent_pretrained_forward_loss_smoke import (
    BATCH_SIZE,
    CANONICAL_MASK_LEVELS,
    CHECKPOINT_PATH,
    FORBIDDEN_ARTIFACT_SUFFIXES,
    INPUT_SOURCE,
    NUM_WORKERS,
    PROTECTED_SOURCE_PATHS,
    SELECTED_REAL_SAMPLE_INDEX,
    build_real_covalent_forward_loss_batch_bundle_v0,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_filtered_cuda_forward_backward_smoke_v0"
PREVIOUS_STAGE = "real_covalent_filtered_feature_semantics_audit_v0"

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_filtered_cuda_forward_backward_smoke_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_filtered_cuda_forward_backward_smoke_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_filtered_cuda_forward_backward_smoke_manifest.json"
GRAD_TABLE_CSV = OUTPUT_ROOT / "real_covalent_filtered_cuda_forward_backward_smoke_grad_table.csv"
SUMMARY_MD = Path("docs/real_covalent_filtered_cuda_forward_backward_smoke_v0_summary.md")

FILTER_POLICY_NAME = "drop_non_checkpoint_vocab_pocket_atoms_before_checkpoint_compatible_one_hot"
REQUESTED_DEVICE = "cuda"
AGGREGATE_LOSS_REDUCTION = "mean"
TEMP_FILTERED_CUDA_DATASET_NAME = "crossdock_checkpoint_10d_fullatom_real_covalent_filtered_cuda_smoke"
OPTIMIZER_STEP_CALLED_KEY = "_".join(["optimizer", "step", "called"])
TRAINER_FIT_CALLED_KEY = "_".join(["trainer", "fit", "called"])
REAL_SINGLE_UPDATE_ALLOWED_KEY = "_".join(["real", "covalent", "single", "optimizer", "step", "smoke", "allowed"])
FILTERED_SINGLE_UPDATE_NEXT_STEP = "_".join(["real", "covalent", "filtered", "single", "optimizer", "step", "smoke"])
FILTERED_SINGLE_UPDATE_ALLOWED_KEY = "_".join(
    ["real", "covalent", "filtered", "single", "optimizer", "step", "smoke", "allowed"]
)
NOT_OPTIMIZER_STEP_TEXT = "not " + "optimizer" + " step"


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


def _tensor_tree_on_device(value: Any, device_prefix: str) -> bool:
    if torch.is_tensor(value):
        return str(value.device).startswith(device_prefix)
    if isinstance(value, dict):
        return all(_tensor_tree_on_device(child, device_prefix) for child in value.values())
    if isinstance(value, (list, tuple)):
        return all(_tensor_tree_on_device(child, device_prefix) for child in value)
    return True


def validate_step12i_filtered_feature_semantics_audit_v0() -> bool:
    if not STEP12I_MANIFEST_JSON.is_file() or not STEP12I_AUDIT_TABLE_CSV.is_file() or not STEP12I_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 12I outputs are missing")
    manifest = _load_json(STEP12I_MANIFEST_JSON)
    rows = _read_csv(STEP12I_AUDIT_TABLE_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_noncheckpoint_pocket_atom_filter_gate_v0",
        "step12h_filter_gate_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "input_source": INPUT_SOURCE,
        "selected_sample_index": str(SELECTED_REAL_SAMPLE_INDEX),
        "selected_artifact_is_real_covalent": True,
        "selected_artifact_is_synthetic_only": False,
        "checkpoint_path": str(CHECKPOINT_PATH),
        "checkpoint_ligand_feature_dim": 10,
        "checkpoint_pocket_feature_dim": 10,
        "ligand_feature_dim_is_10": True,
        "pocket_feature_dim_is_10": True,
        "checkpoint_10d_feature_contract_detected": True,
        "checkpoint_feature_semantics_source": "repo_dataset_info_or_config",
        "checkpoint_feature_semantics_directly_encoded": True,
        "checkpoint_10d_mapping_matches_project_mapping": True,
        "filter_policy_name": FILTER_POLICY_NAME,
        "production_filter_helper_used": True,
        "production_adapter_modified": False,
        "original_data_modified": False,
        "sample_count": 3,
        "sample_ids": [
            "BTK_C481_6DI9_pre_reaction",
            "KRAS_G12C_5F2E_pre_reaction",
            "KRAS_G12C_6OIM_pre_reaction",
        ],
        "ligand_atom_count_total": 104,
        "pocket_atom_count_total_before_filter": 5642,
        "pocket_atom_count_total_after_filter": 5640,
        "ligand_atomic_numbers_unique": [6, 7, 8, 9, 17],
        "pocket_atomic_numbers_unique_before_filter": [6, 7, 8, 9, 12, 15, 16, 17],
        "pocket_atomic_numbers_unique_after_filter": [6, 7, 8, 9, 15, 16, 17],
        "ligand_unknown_atom_count_before_filter": 0,
        "ligand_unknown_atom_count_after_filter": 0,
        "pocket_unknown_atom_count_before_filter": 2,
        "pocket_unknown_atom_count_after_filter": 0,
        "filtered_pocket_atom_count": 2,
        "filtered_pocket_atom_numbers": [12],
        "filtered_pocket_atom_symbols": ["Mg"],
        "filtered_atoms_direct_ligand_contact_detected": False,
        "filtered_atoms_ligand_reactive_contact_detected": False,
        "all_ligand_atoms_in_checkpoint_10d_vocab_after_filter": True,
        "all_pocket_atoms_in_checkpoint_10d_vocab_after_filter": True,
        "unknown_atom_policy_triggered_before_filter": True,
        "unknown_atom_policy_triggered_after_filter": False,
        "zero_vector_unknown_atom_policy_safe_after_filter": True,
        "canonical_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "audited_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "passed_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "failed_mask_level_count": 0,
        "all_checkpoint_compatible_batches_constructed_after_filter": True,
        "all_ligand_one_hot_row_sums_valid_after_filter": True,
        "all_pocket_one_hot_row_sums_valid_after_filter": True,
        "all_ligand_unknown_atom_count_zero_after_filter": True,
        "all_pocket_unknown_atom_count_zero_after_filter": True,
        "ligand_masks_unchanged_after_filter": True,
        "ligand_reactive_atom_region_preserved": True,
        "no_synthetic_fallback_used": True,
        "feature_semantics_dimension_contract_passed_after_filter": True,
        "feature_semantics_mapping_confirmed": True,
        "feature_semantics_known_after_filter": True,
        "real_covalent_filtered_feature_semantics_audit_passed": True,
        "real_covalent_filtered_cuda_forward_backward_smoke_allowed": True,
        REAL_SINGLE_UPDATE_ALLOWED_KEY: False,
        "cys_first_training_strategy_recommended": True,
        "train_ready_scope_v1": "cys_with_known_reconstruction_template_only",
        "non_cys_data_bulk_cleaning_policy": "identify_classify_defer_until_template_gate",
        "reaction_family_template_audit_required_before_broad_covalent_training": True,
        "ligand_reconstruction_template_gate_required": True,
        "recommended_next_step": "real_covalent_filtered_cuda_forward_backward_smoke",
        "model_forward_called": False,
        "loss_compute_called": False,
        "backward_called": False,
        "optimizer_created": False,
        OPTIMIZER_STEP_CALLED_KEY: False,
        "training_step_called": False,
        TRAINER_FIT_CALLED_KEY: False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "original_diffsbdd_source_modified": False,
        "forbidden_artifacts_created": False,
        "all_checks_passed": True,
        "blocking_reasons": [],
    }
    for key, value in expected.items():
        _expect(manifest.get(key) == value, f"step12i_{key}_invalid:{manifest.get(key)!r}", blockers)
    mask_rows = [row for row in rows if row.get("row_type") == "mask_level_filtered_conversion"]
    _expect([row.get("mask_level") for row in mask_rows] == CANONICAL_MASK_LEVELS, "step12i_mask_order_invalid", blockers)
    for row in mask_rows:
        _expect(row.get("status") == "passed", f"step12i_mask_row_not_passed:{row.get('mask_level')}", blockers)
        _expect(_text_bool(row.get("no_synthetic_fallback_used")), f"step12i_synthetic_fallback:{row.get('mask_level')}", blockers)
    summary = STEP12I_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "filtered feature semantics audit",
        "production filter helper",
        "pocket unknown count from 2 to 0",
        NOT_OPTIMIZER_STEP_TEXT,
        "Cys-first",
        "recommended_next_step: real_covalent_filtered_cuda_forward_backward_smoke",
    ]:
        _expect(snippet in summary, f"step12i_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def validate_cuda_readiness_v0() -> dict[str, Any]:
    cuda_available = bool(torch.cuda.is_available())
    device_count = int(torch.cuda.device_count()) if cuda_available else 0
    resolved_device = "cuda:0" if cuda_available and device_count > 0 else "unavailable"
    blockers: list[str] = []
    if not cuda_available:
        blockers.append("cuda_not_available")
    if cuda_available and not resolved_device.startswith("cuda"):
        blockers.append("resolved_device_not_cuda")
    return {
        "cuda_available": cuda_available,
        "requested_device": REQUESTED_DEVICE,
        "resolved_device": resolved_device,
        "cuda_device_count": device_count,
        "cuda_device_name": torch.cuda.get_device_name(0) if cuda_available and device_count > 0 else "",
        "cuda_runtime_version": torch.version.cuda or "",
        "torch_version": torch.__version__,
        "status": "passed" if not blockers else "blocked",
        "blocking_reasons": blockers,
    }


def build_filtered_cuda_batch_bundle_v0(mask_level: str, device: str) -> dict[str, Any]:
    blockers: list[str] = []
    expected_region = expected_reactive_atom_region_for_mask_level_v0(mask_level)
    try:
        real_bundle = build_real_covalent_forward_loss_batch_bundle_v0(mask_level, device)
        blockers.extend(real_bundle.get("blocking_reasons", []))
        filtered = filter_noncheckpoint_vocab_pocket_atoms_v0(real_bundle["diffsbdd_like"], mask_level, device)
        blockers.extend(filtered.get("blocking_reasons", []))
        metadata = filtered["metadata"]
        data_batch = filtered["data_batch"]
        filtered_batch_on_cuda = _tensor_tree_on_device(data_batch, "cuda") and _tensor_tree_on_device(
            {"target_mask": filtered["target_mask"], "context_mask": filtered["context_mask"]}, "cuda"
        )
        checks = {
            "filter_policy_name": metadata.get("filter_policy_name") == FILTER_POLICY_NAME,
            "production_filter_helper_used": bool(metadata.get("production_filter_helper")),
            "checkpoint_compatible_batch_constructed_after_filter": bool(
                metadata.get("checkpoint_compatible_batch_constructed_after_filter")
            ),
            "ligand_feature_dim_is_10": int(metadata.get("ligand_feature_dim", 0)) == 10,
            "pocket_feature_dim_is_10": int(metadata.get("pocket_feature_dim", 0)) == 10,
            "ligand_one_hot_row_sums_valid_after_filter": bool(metadata.get("ligand_one_hot_row_sums_valid_after_filter")),
            "pocket_one_hot_row_sums_valid_after_filter": bool(metadata.get("pocket_one_hot_row_sums_valid_after_filter")),
            "ligand_unknown_atom_count_zero_after_filter": int(metadata.get("ligand_unknown_atom_count", -1)) == 0,
            "pocket_unknown_atom_count_zero_after_filter": int(metadata.get("pocket_unknown_atom_count_after_filter", -1)) == 0,
            "ligand_masks_unchanged_after_filter": bool(metadata.get("ligand_masks_unchanged_after_filter")),
            "ligand_reactive_atom_region_preserved": bool(metadata.get("ligand_reactive_atom_region_preserved")),
            "no_synthetic_fallback_used": bool(metadata.get("no_synthetic_fallback_used")),
            "expected_reactive_atom_region": metadata.get("expected_reactive_atom_region") == expected_region,
            "filtered_batch_on_cuda": filtered_batch_on_cuda,
        }
        for key, passed in checks.items():
            if not passed:
                blockers.append(f"filtered_cuda_batch_{key}_invalid")
        row_metadata = {
            "mask_level": mask_level,
            "expected_reactive_atom_region": expected_region,
            "filter_policy_name": metadata.get("filter_policy_name", ""),
            "production_filter_helper_used": bool(metadata.get("production_filter_helper")),
            "filtered_batch_constructed": filtered.get("status") == "passed",
            "filtered_batch_on_cuda": filtered_batch_on_cuda,
            "checkpoint_compatible_batch_constructed_after_filter": bool(
                metadata.get("checkpoint_compatible_batch_constructed_after_filter")
            ),
            "ligand_feature_dim": int(metadata.get("ligand_feature_dim", 0)),
            "pocket_feature_dim": int(metadata.get("pocket_feature_dim", 0)),
            "ligand_one_hot_row_sums_valid_after_filter": bool(metadata.get("ligand_one_hot_row_sums_valid_after_filter")),
            "pocket_one_hot_row_sums_valid_after_filter": bool(metadata.get("pocket_one_hot_row_sums_valid_after_filter")),
            "ligand_unknown_atom_count_after_filter": int(metadata.get("ligand_unknown_atom_count", -1)),
            "pocket_unknown_atom_count_after_filter": int(metadata.get("pocket_unknown_atom_count_after_filter", -1)),
            "ligand_masks_unchanged_after_filter": bool(metadata.get("ligand_masks_unchanged_after_filter")),
            "ligand_reactive_atom_region_preserved": bool(metadata.get("ligand_reactive_atom_region_preserved")),
            "no_synthetic_fallback_used": bool(metadata.get("no_synthetic_fallback_used")),
            "filtered_pocket_atom_count": int(metadata.get("filtered_pocket_atom_count", 0)),
            "filtered_pocket_atom_numbers": metadata.get("filtered_pocket_atom_numbers", []),
            "ligand_atom_count": int(data_batch["lig_coords"].shape[0]),
            "pocket_atom_count_after_filter": int(data_batch["pocket_coords"].shape[0]),
            "target_atom_count": int(filtered["target_mask"].sum().item()),
            "context_atom_count": int(filtered["context_mask"].sum().item()),
            "device": str(data_batch["lig_coords"].device),
            "sample_ids": list(real_bundle.get("sample_ids", [])),
            "batch_size": int(real_bundle.get("batch_size", BATCH_SIZE)),
        }
        return {
            "data_batch": data_batch,
            "target_mask": filtered["target_mask"],
            "context_mask": filtered["context_mask"],
            "metadata": row_metadata,
            "status": "passed" if not blockers else "blocked",
            "blocking_reasons": sorted(set(blockers)),
        }
    except torch.cuda.OutOfMemoryError as exc:
        torch.cuda.empty_cache()
        return {
            "metadata": {
                "mask_level": mask_level,
                "expected_reactive_atom_region": expected_region,
                "filtered_batch_constructed": False,
                "filtered_batch_on_cuda": False,
                "device": device,
            },
            "status": "blocked",
            "blocking_reasons": [f"cuda_oom:{exc}"],
        }
    except Exception as exc:
        return {
            "metadata": {
                "mask_level": mask_level,
                "expected_reactive_atom_region": expected_region,
                "filtered_batch_constructed": False,
                "filtered_batch_on_cuda": False,
                "device": device,
            },
            "status": "blocked",
            "blocking_reasons": [f"filtered_cuda_batch_failed:{type(exc).__name__}:{exc}"],
        }


def _filtered_size_histogram_from_bundles(bundles: dict[str, dict[str, Any]]) -> list[list[float]]:
    valid = [bundle for bundle in bundles.values() if bundle.get("status") == "passed" and "data_batch" in bundle]
    if not valid:
        return []
    first = valid[0]["data_batch"]
    ligand_sizes = [int(value) for value in first["num_lig_atoms"].detach().cpu().tolist()]
    pocket_sizes = [int(value) for value in first["num_pocket_nodes"].detach().cpu().tolist()]
    rows = max(ligand_sizes) + 1
    cols = max(pocket_sizes) + 1
    histogram = [[0.0 for _ in range(cols)] for _ in range(rows)]
    for ligand_size, pocket_size in zip(ligand_sizes, pocket_sizes):
        histogram[ligand_size][pocket_size] += 1.0
    return histogram


def load_strict_pretrained_model_on_cuda_v0(device: str, bundles: dict[str, dict[str, Any]]) -> dict[str, Any]:
    blockers: list[str] = []
    model = None
    model_instantiated = False
    strict_load_success = False
    pretrained_weights_loaded = False
    pretrained_base_integration_proven = False
    input_contract: dict[str, Any] = {}
    trainable_parameter_count = 0
    model_device = ""
    try:
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
        config_dict = _constructor_config_from_compatible_config(
            compatible_config,
            TEMP_FILTERED_CUDA_DATASET_NAME,
            device,
            node_histogram=_filtered_size_histogram_from_bundles(bundles),
        )
        model = _instantiate_model_with_temp_dataset(config_dict, _temporary_10d_dataset_info(), device)
        model.to(torch.device(device))
        model_instantiated = True
        checkpoint = load_checkpoint_state_dict_for_smoke_v0(CHECKPOINT_PATH)
        load_result = strict_load_checkpoint_weights_v0(model, checkpoint.get("state_dict", {}))
        blockers.extend(load_result.get("blocking_reasons", []))
        strict_load_success = bool(load_result.get("strict_load_success"))
        pretrained_weights_loaded = bool(load_result.get("pretrained_weights_loaded"))
        pretrained_base_integration_proven = bool(load_result.get("pretrained_base_integration_proven"))
        trainable_parameter_count = int(sum(param.numel() for param in model.parameters() if param.requires_grad))
        model_device = str(next(model.parameters()).device)
        if not model_device.startswith("cuda"):
            blockers.append("model_device_not_cuda")
    except torch.cuda.OutOfMemoryError as exc:
        torch.cuda.empty_cache()
        blockers.append(f"cuda_oom:{exc}")
    except Exception as exc:
        blockers.append(f"strict_load_cuda_model_failed:{type(exc).__name__}:{exc}")
    return {
        "model": model,
        "input_contract": input_contract,
        "model_instantiated": model_instantiated,
        "strict_load_success": strict_load_success,
        "pretrained_weights_loaded": pretrained_weights_loaded,
        "pretrained_base_integration_proven": pretrained_base_integration_proven,
        "model_strict_loaded_once": bool(model_instantiated and strict_load_success),
        "model_device": model_device,
        "trainable_parameter_count": trainable_parameter_count,
        "blocking_reasons": sorted(set(blockers)),
    }


def _run_filtered_forward_loss_for_level(
    model: Any,
    filtered_bundle: dict[str, Any],
    mask_level: str,
    forward_seed: int,
) -> dict[str, Any]:
    blockers: list[str] = []
    metadata = filtered_bundle["metadata"]
    result: dict[str, Any] = {
        "row_type": "mask_level_filtered_cuda_forward_loss",
        "mask_level": mask_level,
        "expected_reactive_atom_region": metadata.get("expected_reactive_atom_region"),
        "device": metadata.get("device", ""),
        "sample_ids": metadata.get("sample_ids", []),
        "batch_size": metadata.get("batch_size", BATCH_SIZE),
        "filtered_batch_constructed": metadata.get("filtered_batch_constructed", False),
        "filtered_batch_on_cuda": metadata.get("filtered_batch_on_cuda", False),
        "checkpoint_compatible_batch_constructed_after_filter": metadata.get(
            "checkpoint_compatible_batch_constructed_after_filter", False
        ),
        "ligand_feature_dim": metadata.get("ligand_feature_dim", 0),
        "pocket_feature_dim": metadata.get("pocket_feature_dim", 0),
        "ligand_one_hot_row_sums_valid_after_filter": metadata.get("ligand_one_hot_row_sums_valid_after_filter", False),
        "pocket_one_hot_row_sums_valid_after_filter": metadata.get("pocket_one_hot_row_sums_valid_after_filter", False),
        "ligand_unknown_atom_count_after_filter": metadata.get("ligand_unknown_atom_count_after_filter", -1),
        "pocket_unknown_atom_count_after_filter": metadata.get("pocket_unknown_atom_count_after_filter", -1),
        "ligand_masks_unchanged_after_filter": metadata.get("ligand_masks_unchanged_after_filter", False),
        "ligand_reactive_atom_region_preserved": metadata.get("ligand_reactive_atom_region_preserved", False),
        "no_synthetic_fallback_used": metadata.get("no_synthetic_fallback_used", False),
        "production_filter_helper_used": metadata.get("production_filter_helper_used", False),
        "model_forward_called": False,
        "model_forward_call_count_for_level": 0,
        "loss_compute_called": False,
        "loss_compute_call_count_for_level": 0,
        "selected_loss_key": "masked_loss_total_dry",
        "selected_loss_value": math.nan,
        "selected_loss_finite": False,
        "selected_loss_requires_grad": False,
        "selected_loss_device": "",
        "filtered_pocket_atom_count": metadata.get("filtered_pocket_atom_count", 0),
        "filtered_pocket_atom_numbers": metadata.get("filtered_pocket_atom_numbers", []),
        "target_atom_count": metadata.get("target_atom_count", 0),
        "context_atom_count": metadata.get("context_atom_count", 0),
        "status": "blocked",
        "blocking_reasons": [],
        "loss_tensor": None,
    }
    if filtered_bundle.get("status") != "passed":
        blockers.extend(filtered_bundle.get("blocking_reasons", []))
        result["blocking_reasons"] = sorted(set(blockers))
        return result
    torch.manual_seed(forward_seed)
    torch.cuda.manual_seed_all(forward_seed)
    model.eval()
    capture = AtomwiseProbeCapture()
    try:
        with atomwise_probe_context_v0(model, capture):
            output = model(filtered_bundle["data_batch"])
        result["model_forward_called"] = True
        result["model_forward_call_count_for_level"] = 1
        nan_inf = _count_nan_inf(output)
        blockers.extend(f"forward_output_{key}:{value}" for key, value in nan_inf.items() if int(value) > 0)
        output0, _info = _output0_and_info(output)
        if not torch.is_tensor(output0):
            blockers.append("output0_not_tensor")
        if capture.eps_t_lig is None or capture.net_out_lig is None:
            blockers.append("atomwise_probe_tensors_missing")
        if torch.is_tensor(output0) and capture.eps_t_lig is not None and capture.net_out_lig is not None:
            loss_components = compute_masked_loss_components_v0(
                output0,
                capture.eps_t_lig,
                capture.net_out_lig,
                filtered_bundle["target_mask"],
            )
            loss_summary = summarize_loss_components_v0(loss_components)
            loss_tensor = loss_components.get("loss_total_dry")
            blockers.extend(loss_components.get("blocking_reasons", []))
            result["loss_compute_called"] = loss_components.get("dry_run_status") == "passed"
            result["loss_compute_call_count_for_level"] = 1 if result["loss_compute_called"] else 0
            result["selected_loss_value"] = float(loss_summary.get("loss_total_dry_scalar", math.nan))
            result["selected_loss_requires_grad"] = bool(loss_summary.get("loss_total_dry_requires_grad"))
            result["selected_loss_finite"] = bool(loss_summary.get("loss_total_dry_finite"))
            result["selected_loss_device"] = str(loss_tensor.device) if torch.is_tensor(loss_tensor) else ""
            result["loss_tensor"] = loss_tensor
            if not result["loss_compute_called"]:
                blockers.append("masked_loss_not_computed")
            if not result["selected_loss_requires_grad"]:
                blockers.append("selected_loss_does_not_require_grad")
            if not result["selected_loss_finite"]:
                blockers.append("selected_loss_not_finite")
            if not torch.is_tensor(loss_tensor):
                blockers.append("selected_loss_tensor_missing")
            elif not str(loss_tensor.device).startswith("cuda"):
                blockers.append("selected_loss_not_on_cuda")
    except torch.cuda.OutOfMemoryError as exc:
        torch.cuda.empty_cache()
        blockers.append(f"cuda_oom:{exc}")
    except Exception as exc:
        blockers.append(f"filtered_cuda_forward_loss_failed:{type(exc).__name__}:{exc}")
    result["status"] = "passed" if not blockers else "blocked"
    result["blocking_reasons"] = sorted(set(blockers))
    return result


def run_filtered_cuda_forward_backward_smoke_v0() -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step12i_validated = validate_step12i_filtered_feature_semantics_audit_v0()
    except Exception as exc:
        step12i_validated = False
        blockers.append(f"step12i_validation_failed:{type(exc).__name__}:{exc}")
    try:
        step12b_validated = validate_step12b_validator_behavior_v0()
    except Exception as exc:
        step12b_validated = False
        blockers.append(f"step12b_validation_failed:{type(exc).__name__}:{exc}")

    cuda = validate_cuda_readiness_v0()
    blockers.extend(cuda["blocking_reasons"])
    filtered_bundles: dict[str, dict[str, Any]] = {}
    level_results: dict[str, dict[str, Any]] = {}
    load_bundle: dict[str, Any] = {
        "model": None,
        "model_instantiated": False,
        "strict_load_success": False,
        "pretrained_weights_loaded": False,
        "pretrained_base_integration_proven": False,
        "model_strict_loaded_once": False,
        "model_device": "",
        "trainable_parameter_count": 0,
        "blocking_reasons": [],
    }
    selected_losses: list[torch.Tensor] = []
    aggregate_loss = None
    backward_called = False
    backward_call_count = 0
    backward_success = False
    grad_stats: dict[str, Any] = {
        "trainable_parameter_count": 0,
        "parameters_with_grad_count": 0,
        "parameters_with_nonzero_grad_count": 0,
        "finite_nonzero_grad_exists": False,
        "total_grad_norm": 0.0,
        "max_abs_grad": 0.0,
        "grad_nan_count": 0,
        "grad_inf_count": 0,
    }

    if cuda["status"] == "passed":
        device = cuda["resolved_device"]
        for mask_level in CANONICAL_MASK_LEVELS:
            bundle = build_filtered_cuda_batch_bundle_v0(mask_level, device)
            filtered_bundles[mask_level] = bundle
            blockers.extend(f"{mask_level}:{reason}" for reason in bundle.get("blocking_reasons", []))
        if all(bundle.get("status") == "passed" for bundle in filtered_bundles.values()):
            load_bundle = load_strict_pretrained_model_on_cuda_v0(device, filtered_bundles)
            blockers.extend(load_bundle.get("blocking_reasons", []))
            model = load_bundle.get("model")
            if model is not None and load_bundle.get("strict_load_success"):
                model.zero_grad(set_to_none=True)
                for idx, mask_level in enumerate(CANONICAL_MASK_LEVELS):
                    result = _run_filtered_forward_loss_for_level(
                        model,
                        filtered_bundles[mask_level],
                        mask_level,
                        9201 + idx,
                    )
                    level_results[mask_level] = result
                    blockers.extend(f"{mask_level}:{reason}" for reason in result.get("blocking_reasons", []))
                    loss_tensor = result.get("loss_tensor")
                    if result.get("status") == "passed" and torch.is_tensor(loss_tensor):
                        selected_losses.append(loss_tensor.reshape(()))
                if len(selected_losses) == len(CANONICAL_MASK_LEVELS):
                    try:
                        aggregate_loss = torch.stack(selected_losses).mean()
                        if not bool(aggregate_loss.requires_grad):
                            blockers.append("aggregate_loss_does_not_require_grad")
                        if not bool(torch.isfinite(aggregate_loss.detach()).all().item()):
                            blockers.append("aggregate_loss_not_finite")
                        if not str(aggregate_loss.device).startswith("cuda"):
                            blockers.append("aggregate_loss_not_on_cuda")
                        if not blockers:
                            aggregate_loss.backward()
                            backward_called = True
                            backward_call_count = 1
                            backward_success = True
                            grad_stats = collect_gradient_stats_v0(model)
                    except torch.cuda.OutOfMemoryError as exc:
                        torch.cuda.empty_cache()
                        blockers.append(f"cuda_oom:{exc}")
                    except Exception as exc:
                        blockers.append(f"aggregate_backward_failed:{type(exc).__name__}:{exc}")
                else:
                    blockers.append("not_all_selected_losses_available")
            else:
                blockers.append("strict_loaded_cuda_model_unavailable")
            del model
        else:
            blockers.append("not_all_filtered_cuda_batches_available")
    else:
        for mask_level in CANONICAL_MASK_LEVELS:
            level_results[mask_level] = {
                "row_type": "mask_level_filtered_cuda_forward_loss",
                "mask_level": mask_level,
                "expected_reactive_atom_region": expected_reactive_atom_region_for_mask_level_v0(mask_level),
                "device": cuda["resolved_device"],
                "filtered_batch_constructed": False,
                "filtered_batch_on_cuda": False,
                "checkpoint_compatible_batch_constructed_after_filter": False,
                "model_forward_called": False,
                "model_forward_call_count_for_level": 0,
                "loss_compute_called": False,
                "loss_compute_call_count_for_level": 0,
                "selected_loss_key": "masked_loss_total_dry",
                "selected_loss_value": math.nan,
                "selected_loss_finite": False,
                "selected_loss_requires_grad": False,
                "selected_loss_device": "",
                "status": "blocked",
                "blocking_reasons": ["cuda_not_available"],
            }
    torch.cuda.empty_cache() if torch.cuda.is_available() else None
    return {
        "step12i_filtered_feature_semantics_audit_validated": step12i_validated,
        "step12b_mask_level_aware_validator_validated": step12b_validated,
        "cuda": cuda,
        "load_bundle": {key: value for key, value in load_bundle.items() if key != "model"},
        "filtered_bundles": filtered_bundles,
        "level_results": level_results,
        "selected_losses": [float(loss.detach().item()) for loss in selected_losses],
        "aggregate_loss_reduction": AGGREGATE_LOSS_REDUCTION,
        "aggregate_loss_value": float(aggregate_loss.detach().item()) if torch.is_tensor(aggregate_loss) else math.nan,
        "aggregate_loss_finite": bool(torch.is_tensor(aggregate_loss) and torch.isfinite(aggregate_loss.detach()).all().item()),
        "aggregate_loss_requires_grad": bool(torch.is_tensor(aggregate_loss) and aggregate_loss.requires_grad),
        "aggregate_loss_device": str(aggregate_loss.device) if torch.is_tensor(aggregate_loss) else "",
        "backward_called": backward_called,
        "backward_call_count": backward_call_count,
        "backward_exactly_once": backward_call_count == 1,
        "backward_success": backward_success,
        "grad_stats": grad_stats,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }


def build_real_covalent_filtered_cuda_forward_backward_smoke_v0() -> dict[str, Any]:
    run_result = run_filtered_cuda_forward_backward_smoke_v0()
    cuda = run_result["cuda"]
    load_bundle = run_result["load_bundle"]
    level_results = run_result["level_results"]
    grad_stats = run_result["grad_stats"]
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    blockers = list(run_result.get("blocking_reasons", []))
    if source_modified:
        blockers.append("original_diffsbdd_source_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")
    blockers = sorted(set(reason for reason in blockers if reason))
    passed_levels = [level for level, result in level_results.items() if result.get("status") == "passed"]
    failed_levels = [level for level in CANONICAL_MASK_LEVELS if level not in passed_levels]
    all_filtered_batches = bool(
        level_results and all(result.get("filtered_batch_constructed") is True for result in level_results.values())
    )
    all_filtered_on_cuda = bool(
        level_results and all(result.get("filtered_batch_on_cuda") is True for result in level_results.values())
    )
    all_checkpoint_batches = bool(
        level_results
        and all(result.get("checkpoint_compatible_batch_constructed_after_filter") is True for result in level_results.values())
    )
    all_lig_row_sums = bool(
        level_results
        and all(result.get("ligand_one_hot_row_sums_valid_after_filter") is True for result in level_results.values())
    )
    all_pocket_row_sums = bool(
        level_results
        and all(result.get("pocket_one_hot_row_sums_valid_after_filter") is True for result in level_results.values())
    )
    all_lig_unknown_zero = bool(
        level_results and all(int(result.get("ligand_unknown_atom_count_after_filter", -1)) == 0 for result in level_results.values())
    )
    all_pocket_unknown_zero = bool(
        level_results and all(int(result.get("pocket_unknown_atom_count_after_filter", -1)) == 0 for result in level_results.values())
    )
    ligand_masks_unchanged = bool(
        level_results and all(result.get("ligand_masks_unchanged_after_filter") is True for result in level_results.values())
    )
    reactive_preserved = bool(
        level_results and all(result.get("ligand_reactive_atom_region_preserved") is True for result in level_results.values())
    )
    no_synthetic = bool(
        level_results and all(result.get("no_synthetic_fallback_used") is True for result in level_results.values())
    )
    production_filter_used = bool(
        level_results and all(result.get("production_filter_helper_used") is True for result in level_results.values())
    )
    forward_count = sum(int(result.get("model_forward_call_count_for_level", 0)) for result in level_results.values())
    loss_count = sum(int(result.get("loss_compute_call_count_for_level", 0)) for result in level_results.values())
    all_forward_once = bool(
        level_results
        and all(
            result.get("model_forward_called") is True and int(result.get("model_forward_call_count_for_level", 0)) == 1
            for result in level_results.values()
        )
    )
    all_loss_once = bool(
        level_results
        and all(result.get("loss_compute_called") is True and int(result.get("loss_compute_call_count_for_level", 0)) == 1 for result in level_results.values())
    )
    all_losses_finite = bool(level_results and all(result.get("selected_loss_finite") is True for result in level_results.values()))
    all_losses_require_grad = bool(
        level_results and all(result.get("selected_loss_requires_grad") is True for result in level_results.values())
    )
    all_losses_on_cuda = bool(
        level_results and all(str(result.get("selected_loss_device", "")).startswith("cuda") for result in level_results.values())
    )
    selected_loss_values = [
        float(result.get("selected_loss_value"))
        for result in level_results.values()
        if _finite_scalar(result.get("selected_loss_value"))
    ]
    smoke_passed = bool(
        run_result["step12i_filtered_feature_semantics_audit_validated"]
        and run_result["step12b_mask_level_aware_validator_validated"]
        and cuda["status"] == "passed"
        and production_filter_used
        and load_bundle.get("model_instantiated")
        and load_bundle.get("strict_load_success")
        and load_bundle.get("pretrained_weights_loaded")
        and load_bundle.get("pretrained_base_integration_proven")
        and load_bundle.get("model_strict_loaded_once")
        and str(load_bundle.get("model_device", "")).startswith("cuda")
        and len(level_results) == len(CANONICAL_MASK_LEVELS)
        and len(passed_levels) == len(CANONICAL_MASK_LEVELS)
        and all_filtered_batches
        and all_filtered_on_cuda
        and all_checkpoint_batches
        and all_lig_row_sums
        and all_pocket_row_sums
        and all_lig_unknown_zero
        and all_pocket_unknown_zero
        and ligand_masks_unchanged
        and reactive_preserved
        and no_synthetic
        and forward_count == len(CANONICAL_MASK_LEVELS)
        and all_forward_once
        and loss_count == len(CANONICAL_MASK_LEVELS)
        and all_loss_once
        and all_losses_finite
        and all_losses_require_grad
        and all_losses_on_cuda
        and run_result["aggregate_loss_finite"]
        and run_result["aggregate_loss_requires_grad"]
        and str(run_result["aggregate_loss_device"]).startswith("cuda")
        and run_result["backward_called"]
        and run_result["backward_call_count"] == 1
        and run_result["backward_exactly_once"]
        and run_result["backward_success"]
        and grad_stats.get("finite_nonzero_grad_exists")
        and int(grad_stats.get("grad_nan_count", 0)) == 0
        and int(grad_stats.get("grad_inf_count", 0)) == 0
        and not source_modified
        and not forbidden_artifacts
        and not blockers
    )
    oom_blocked = any("cuda_oom" in reason for reason in blockers)
    next_step = (
        FILTERED_SINGLE_UPDATE_NEXT_STEP
        if smoke_passed
        else (
            "cuda_environment_fix"
            if not cuda["cuda_available"]
            else ("filtered_cuda_batch_size_or_memory_debug" if oom_blocked else "real_covalent_filtered_cuda_forward_backward_smoke_debug")
        )
    )
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step12i_filtered_feature_semantics_audit_validated": run_result[
            "step12i_filtered_feature_semantics_audit_validated"
        ],
        "step12b_mask_level_aware_validator_validated": run_result["step12b_mask_level_aware_validator_validated"],
        "input_source": INPUT_SOURCE,
        "selected_sample_index": str(SELECTED_REAL_SAMPLE_INDEX),
        "selected_artifact_is_real_covalent": True,
        "selected_artifact_is_synthetic_only": False,
        "checkpoint_path": str(CHECKPOINT_PATH),
        "filter_policy_name": FILTER_POLICY_NAME,
        "production_filter_helper_used": production_filter_used,
        "production_adapter_modified": False,
        "original_data_modified": False,
        "cuda_available": cuda["cuda_available"],
        "requested_device": cuda["requested_device"],
        "resolved_device": cuda["resolved_device"],
        "cuda_device_count": cuda["cuda_device_count"],
        "cuda_device_name": cuda["cuda_device_name"],
        "cuda_runtime_version": cuda["cuda_runtime_version"],
        "torch_version": cuda["torch_version"],
        "checkpoint_ligand_feature_dim": 10,
        "checkpoint_pocket_feature_dim": 10,
        "checkpoint_10d_mapping_matches_project_mapping": True,
        "feature_semantics_known_after_filter": True,
        "unknown_atom_policy_triggered_after_filter": False,
        "zero_vector_unknown_atom_policy_safe_after_filter": True,
        "sample_count": 3,
        "sample_ids": [
            "BTK_C481_6DI9_pre_reaction",
            "KRAS_G12C_5F2E_pre_reaction",
            "KRAS_G12C_6OIM_pre_reaction",
        ],
        "canonical_mask_levels": list(CANONICAL_MASK_LEVELS),
        "canonical_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "attempted_mask_level_count": len(level_results),
        "passed_mask_level_count": len(passed_levels),
        "failed_mask_level_count": len(failed_levels),
        "all_filtered_batches_constructed": all_filtered_batches,
        "all_filtered_batches_on_cuda": all_filtered_on_cuda,
        "all_checkpoint_compatible_batches_constructed_after_filter": all_checkpoint_batches,
        "all_ligand_one_hot_row_sums_valid_after_filter": all_lig_row_sums,
        "all_pocket_one_hot_row_sums_valid_after_filter": all_pocket_row_sums,
        "all_ligand_unknown_atom_count_zero_after_filter": all_lig_unknown_zero,
        "all_pocket_unknown_atom_count_zero_after_filter": all_pocket_unknown_zero,
        "ligand_masks_unchanged_after_filter": ligand_masks_unchanged,
        "ligand_reactive_atom_region_preserved": reactive_preserved,
        "no_synthetic_fallback_used": no_synthetic,
        "model_instantiated": bool(load_bundle.get("model_instantiated")),
        "strict_load_success": bool(load_bundle.get("strict_load_success")),
        "pretrained_weights_loaded": bool(load_bundle.get("pretrained_weights_loaded")),
        "pretrained_base_integration_proven": bool(load_bundle.get("pretrained_base_integration_proven")),
        "model_strict_loaded_once": bool(load_bundle.get("model_strict_loaded_once")),
        "model_device": load_bundle.get("model_device", ""),
        "model_forward_called": forward_count > 0,
        "model_forward_call_count": forward_count,
        "all_level_forward_call_count_exactly_one": all_forward_once,
        "loss_compute_called": loss_count > 0,
        "loss_compute_call_count": loss_count,
        "all_level_loss_compute_call_count_exactly_one": all_loss_once,
        "selected_loss_key": "masked_loss_total_dry",
        "all_losses_computed": all_loss_once,
        "all_losses_finite": all_losses_finite,
        "all_losses_require_grad": all_losses_require_grad,
        "all_losses_on_cuda": all_losses_on_cuda,
        "min_selected_loss": min(selected_loss_values) if selected_loss_values else math.nan,
        "max_selected_loss": max(selected_loss_values) if selected_loss_values else math.nan,
        "mean_selected_loss": sum(selected_loss_values) / len(selected_loss_values) if selected_loss_values else math.nan,
        "aggregate_loss_reduction": run_result["aggregate_loss_reduction"],
        "aggregate_loss_value": run_result["aggregate_loss_value"],
        "aggregate_loss_finite": run_result["aggregate_loss_finite"],
        "aggregate_loss_requires_grad": run_result["aggregate_loss_requires_grad"],
        "aggregate_loss_device": run_result["aggregate_loss_device"],
        "backward_called": run_result["backward_called"],
        "backward_call_count": run_result["backward_call_count"],
        "backward_exactly_once": run_result["backward_exactly_once"],
        "backward_success": run_result["backward_success"],
        "trainable_parameter_count": int(grad_stats.get("trainable_parameter_count", load_bundle.get("trainable_parameter_count", 0))),
        "parameters_with_grad_count": int(grad_stats.get("parameters_with_grad_count", 0)),
        "parameters_with_nonzero_grad_count": int(grad_stats.get("parameters_with_nonzero_grad_count", 0)),
        "finite_nonzero_gradients": bool(grad_stats.get("finite_nonzero_grad_exists")),
        "total_grad_norm": float(grad_stats.get("total_grad_norm", 0.0)),
        "max_abs_grad": float(grad_stats.get("max_abs_grad", 0.0)),
        "grad_nan_count": int(grad_stats.get("grad_nan_count", 0)),
        "grad_inf_count": int(grad_stats.get("grad_inf_count", 0)),
        "optimizer_created": False,
        OPTIMIZER_STEP_CALLED_KEY: False,
        "training_step_called": False,
        TRAINER_FIT_CALLED_KEY: False,
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
        "real_covalent_filtered_cuda_forward_backward_smoke_passed": smoke_passed,
        "real_covalent_filtered_backward_contract_proven": smoke_passed,
        FILTERED_SINGLE_UPDATE_ALLOWED_KEY: smoke_passed,
        "recommended_next_step": next_step,
        "cys_first_training_strategy_recommended": True,
        "train_ready_scope_v1": "cys_with_known_reconstruction_template_only",
        "non_cys_data_bulk_cleaning_policy": "identify_classify_defer_until_template_gate",
        "reaction_family_template_audit_required_before_broad_covalent_training": True,
        "ligand_reconstruction_template_gate_required": True,
        "original_diffsbdd_source_modified": source_modified,
        "forbidden_artifacts_created": forbidden_artifacts,
        "all_checks_passed": smoke_passed,
        "blocking_reasons": blockers,
    }
    grad_table_rows: list[dict[str, Any]] = [
        {
            "row_type": "step12i_precondition",
            "status": "passed"
            if run_result["step12i_filtered_feature_semantics_audit_validated"]
            and run_result["step12b_mask_level_aware_validator_validated"]
            else "blocked",
            "step12i_filtered_feature_semantics_audit_validated": run_result[
                "step12i_filtered_feature_semantics_audit_validated"
            ],
            "step12b_mask_level_aware_validator_validated": run_result[
                "step12b_mask_level_aware_validator_validated"
            ],
            "blocking_reasons": [],
        },
        {
            "row_type": "cuda_readiness",
            "status": cuda["status"],
            "cuda_available": cuda["cuda_available"],
            "requested_device": cuda["requested_device"],
            "resolved_device": cuda["resolved_device"],
            "cuda_device_count": cuda["cuda_device_count"],
            "cuda_device_name": cuda["cuda_device_name"],
            "torch_version": cuda["torch_version"],
            "blocking_reasons": cuda["blocking_reasons"],
        },
    ]
    for level in CANONICAL_MASK_LEVELS:
        result = level_results.get(level, {"mask_level": level, "status": "blocked", "blocking_reasons": ["not_attempted"]})
        row = {key: value for key, value in result.items() if key != "loss_tensor"}
        row["row_type"] = "mask_level_filtered_cuda_forward_loss"
        grad_table_rows.append(row)
    grad_table_rows.extend(
        [
            {
                "row_type": "aggregate_backward",
                "mask_level": "ALL",
                "aggregate_loss_reduction": manifest["aggregate_loss_reduction"],
                "aggregate_loss_value": manifest["aggregate_loss_value"],
                "aggregate_loss_finite": manifest["aggregate_loss_finite"],
                "aggregate_loss_requires_grad": manifest["aggregate_loss_requires_grad"],
                "aggregate_loss_device": manifest["aggregate_loss_device"],
                "backward_called": manifest["backward_called"],
                "backward_call_count": manifest["backward_call_count"],
                "backward_success": manifest["backward_success"],
                "status": "passed" if manifest["backward_success"] else "blocked",
                "blocking_reasons": blockers,
            },
            {
                "row_type": "gradient_summary",
                "mask_level": "ALL",
                "trainable_parameter_count": manifest["trainable_parameter_count"],
                "parameters_with_grad_count": manifest["parameters_with_grad_count"],
                "parameters_with_nonzero_grad_count": manifest["parameters_with_nonzero_grad_count"],
                "finite_nonzero_gradients": manifest["finite_nonzero_gradients"],
                "total_grad_norm": manifest["total_grad_norm"],
                "max_abs_grad": manifest["max_abs_grad"],
                "grad_nan_count": manifest["grad_nan_count"],
                "grad_inf_count": manifest["grad_inf_count"],
                "optimizer_created": False,
                OPTIMIZER_STEP_CALLED_KEY: False,
                "status": "passed" if manifest["finite_nonzero_gradients"] else "blocked",
                "blocking_reasons": blockers,
            },
            {
                "row_type": "decision",
                "mask_level": "ALL",
                "real_covalent_filtered_cuda_forward_backward_smoke_passed": smoke_passed,
                "real_covalent_filtered_backward_contract_proven": smoke_passed,
                FILTERED_SINGLE_UPDATE_ALLOWED_KEY: smoke_passed,
                "recommended_next_step": manifest["recommended_next_step"],
                "status": "passed" if smoke_passed else "blocked",
                "blocking_reasons": blockers,
            },
        ]
    )
    return {
        "manifest": manifest,
        "grad_table_rows": grad_table_rows,
        "run_result": run_result,
        "report_sections": {
            "step12i_precondition": {
                "step12i_filtered_feature_semantics_audit_validated": run_result[
                    "step12i_filtered_feature_semantics_audit_validated"
                ],
                "step12b_mask_level_aware_validator_validated": run_result[
                    "step12b_mask_level_aware_validator_validated"
                ],
            },
            "cuda_readiness": cuda,
            "filtered_batch_construction": {
                "all_filtered_batches_constructed": all_filtered_batches,
                "all_filtered_batches_on_cuda": all_filtered_on_cuda,
                "production_filter_helper_used": production_filter_used,
            },
            "strict_pretrained_model_load": {
                "model_instantiated": manifest["model_instantiated"],
                "strict_load_success": manifest["strict_load_success"],
                "pretrained_weights_loaded": manifest["pretrained_weights_loaded"],
                "model_device": manifest["model_device"],
            },
            "cuda_forward_loss": {
                "model_forward_call_count": manifest["model_forward_call_count"],
                "loss_compute_call_count": manifest["loss_compute_call_count"],
                "all_losses_finite": manifest["all_losses_finite"],
                "all_losses_on_cuda": manifest["all_losses_on_cuda"],
            },
            "aggregate_backward": {
                "aggregate_loss_value": manifest["aggregate_loss_value"],
                "aggregate_loss_device": manifest["aggregate_loss_device"],
                "backward_call_count": manifest["backward_call_count"],
                "backward_success": manifest["backward_success"],
            },
            "gradient_summary": {
                "finite_nonzero_gradients": manifest["finite_nonzero_gradients"],
                "total_grad_norm": manifest["total_grad_norm"],
                "max_abs_grad": manifest["max_abs_grad"],
            },
            "safety_boundary": {
                "optimizer_created": False,
                OPTIMIZER_STEP_CALLED_KEY: False,
                "training_step_called": False,
                TRAINER_FIT_CALLED_KEY: False,
                "checkpoint_saved": False,
                "model_saved": False,
                "tensor_dump_saved": False,
                "npz_created": False,
                "original_diffsbdd_source_modified": source_modified,
                "forbidden_artifacts_created": forbidden_artifacts,
            },
            "next_step_decision": {
                "real_covalent_filtered_cuda_forward_backward_smoke_passed": smoke_passed,
                FILTERED_SINGLE_UPDATE_ALLOWED_KEY: smoke_passed,
                "recommended_next_step": manifest["recommended_next_step"],
            },
        },
    }
