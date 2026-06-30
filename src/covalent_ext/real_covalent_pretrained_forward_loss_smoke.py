from __future__ import annotations

import csv
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import torch
from torch.utils.data import DataLoader

from covalent_ext.batch_adapter import adapt_covalent_batch_for_model_v0, validate_adapted_covalent_batch_v0
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
from covalent_ext.diffsbdd_input_adapter import (
    build_diffsbdd_like_input_from_covalent_v0,
    validate_diffsbdd_like_input_v0,
)
from covalent_ext.masked_loss_dry_run import compute_masked_loss_components_v0, summarize_loss_components_v0
from covalent_ext.model_input_adapter import (
    build_covalent_model_input_v0,
    expected_reactive_atom_region_for_mask_level_v0,
    validate_covalent_model_input_v0,
)
from covalent_ext.npz_dataset import CovalentNPZDataset, covalent_npz_collate_fn
from covalent_ext.pretrained_masked_loss_smoke import CONFIG_PREVIEW_PATH, _count_nan_inf, _output0_and_info


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE = "real_covalent_pretrained_forward_loss_smoke_v0"
PREVIOUS_STAGE = "real_covalent_pretraining_smoke_design_v0"

STEP12C_MANIFEST_JSON = Path(
    "data/derived/covalent_small/real_covalent_pretraining_smoke_design_v0/"
    "real_covalent_pretraining_smoke_design_manifest.json"
)
STEP12C_PLAN_TABLE_CSV = Path(
    "data/derived/covalent_small/real_covalent_pretraining_smoke_design_v0/"
    "real_covalent_pretraining_smoke_design_plan_table.csv"
)
STEP12C_SUMMARY_MD = Path("docs/real_covalent_pretraining_smoke_design_v0_summary.md")

OUTPUT_ROOT = Path("data/derived/covalent_small/real_covalent_pretrained_forward_loss_smoke_v0")
REPORT_CSV = OUTPUT_ROOT / "real_covalent_pretrained_forward_loss_smoke_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "real_covalent_pretrained_forward_loss_smoke_manifest.json"
LOSS_TABLE_CSV = OUTPUT_ROOT / "real_covalent_pretrained_forward_loss_smoke_loss_table.csv"
SUMMARY_MD = Path("docs/real_covalent_pretrained_forward_loss_smoke_v0_summary.md")

CHECKPOINT_PATH = Path("checkpoints/crossdocked_fullatom_cond.ckpt")
SELECTED_REAL_SAMPLE_INDEX = Path("data/derived/covalent_small/training_tensor_materialized_v0/sample_index.csv")
INPUT_SOURCE = "real_covalent_training_tensor_materialized_v0"
REQUESTED_DEVICE = "cpu"
RESOLVED_DEVICE = "cpu"
BATCH_SIZE = 2
NUM_WORKERS = 0

CANONICAL_MASK_LEVELS = [
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "B3_scaffold_only",
    "C_scaffold_linker_warhead",
]

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
UNKNOWN_ATOM_FEATURE_POLICY = "zero_vector_for_atoms_outside_checkpoint_10d_vocab"
TEMP_REAL_DATASET_NAME = "crossdock_checkpoint_10d_fullatom_real_covalent_smoke"
FORBIDDEN_ARTIFACT_SUFFIXES = {".pt", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".ckpt", ".pth", ".npz"}
PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _expect(condition: bool, message: str, blockers: list[str]) -> None:
    if not condition:
        blockers.append(message)


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


def _to_device(value: Any, device: str) -> Any:
    if torch.is_tensor(value):
        return value.to(torch.device(device))
    if isinstance(value, dict):
        return {key: _to_device(child, device) for key, child in value.items()}
    return value


def _shape(value: Any) -> list[int]:
    return [int(dim) for dim in value.shape] if torch.is_tensor(value) else []


def validate_step12c_outputs_v0() -> bool:
    if not STEP12C_MANIFEST_JSON.is_file() or not STEP12C_PLAN_TABLE_CSV.is_file() or not STEP12C_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 12C outputs are missing")
    manifest = _load_json(STEP12C_MANIFEST_JSON)
    rows = _read_csv(STEP12C_PLAN_TABLE_CSV)
    blockers: list[str] = []
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "real_covalent_feature_mapping_loader_gate_v0",
        "step12a_validated": True,
        "step12b_mask_level_aware_validator_validated": True,
        "selected_real_data_root": "data/derived/covalent_small/training_tensor_materialized_v0",
        "selected_sample_index": str(SELECTED_REAL_SAMPLE_INDEX),
        "selected_artifact_is_real_covalent": True,
        "selected_artifact_is_synthetic_only": False,
        "planned_next_stage": STAGE,
        "planned_checkpoint_path": str(CHECKPOINT_PATH),
        "planned_batch_size": BATCH_SIZE,
        "planned_num_workers": NUM_WORKERS,
        "planned_mask_levels": CANONICAL_MASK_LEVELS,
        "planned_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "planned_use_mask_level_aware_validator": True,
        "planned_use_synthetic_fallback": False,
        "planned_allow_model_forward": True,
        "planned_allow_loss_compute": True,
        "planned_allow_backward": False,
        "planned_allow_optimizer": False,
        "planned_allow_optimizer_step": False,
        "planned_allow_training_step": False,
        "planned_allow_trainer_fit": False,
        "planned_allow_checkpoint_save": False,
        "planned_allow_model_save": False,
        "planned_allow_tensor_dump": False,
        "real_covalent_pretraining_smoke_design_passed": True,
        "real_covalent_forward_loss_smoke_plan_ready": True,
        "real_covalent_forward_loss_smoke_allowed": True,
        "recommended_next_step": "real_covalent_pretrained_forward_loss_smoke",
        "model_forward_called": False,
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "tensor_dump_saved": False,
        "npz_created": False,
        "all_checks_passed": True,
    }
    for key, expected_value in expected.items():
        _expect(manifest.get(key) == expected_value, f"step12c_{key}_invalid:{manifest.get(key)!r}", blockers)
    _expect(len(rows) == len(CANONICAL_MASK_LEVELS), f"step12c_plan_row_count_invalid:{len(rows)}", blockers)
    _expect([row.get("mask_level") for row in rows] == CANONICAL_MASK_LEVELS, "step12c_plan_mask_order_invalid", blockers)
    for row in rows:
        mask_level = row.get("mask_level", "")
        expected_region = "context" if mask_level == "B3_scaffold_only" else "target"
        _expect(
            row.get("expected_reactive_atom_region") == expected_region,
            f"step12c_plan_region_invalid:{mask_level}:{row.get('expected_reactive_atom_region')!r}",
            blockers,
        )
        _expect(row.get("planned_use_synthetic_fallback") == "False", f"step12c_plan_synthetic_fallback:{mask_level}", blockers)
    expected_regions = {
        "A_warhead_only": "target",
        "B_linker_warhead": "target",
        "B2_scaffold_warhead": "target",
        "B3_scaffold_only": "context",
        "C_scaffold_linker_warhead": "target",
    }
    for mask_level, expected_region in expected_regions.items():
        _expect(
            expected_reactive_atom_region_for_mask_level_v0(mask_level) == expected_region,
            f"step12b_region_invalid:{mask_level}",
            blockers,
        )
    try:
        expected_reactive_atom_region_for_mask_level_v0("B3")
    except ValueError:
        short_b3_rejected = True
    else:
        short_b3_rejected = False
    _expect(short_b3_rejected, "step12b_short_alias_b3_accepted", blockers)
    summary = STEP12C_SUMMARY_MD.read_text(encoding="utf-8")
    for snippet in [
        "design only, not training",
        "recommended_next_step: real_covalent_pretrained_forward_loss_smoke",
    ]:
        _expect(snippet in summary, f"step12c_summary_missing:{snippet}", blockers)
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def _checkpoint_compatible_one_hot_from_atomic_numbers(atomic_numbers: torch.Tensor) -> tuple[torch.Tensor, dict[str, Any]]:
    flat_numbers = atomic_numbers.detach().cpu().to(dtype=torch.long).view(-1).tolist()
    one_hot = torch.zeros((len(flat_numbers), len(CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX)), dtype=torch.float32)
    unknown_numbers: list[int] = []
    for row_idx, value in enumerate(flat_numbers):
        feature_idx = CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX.get(int(value))
        if feature_idx is None:
            unknown_numbers.append(int(value))
        else:
            one_hot[row_idx, feature_idx] = 1.0
    return one_hot.to(device=atomic_numbers.device), {
        "unknown_atom_numbers": sorted(set(unknown_numbers)),
        "unknown_atom_count": len(unknown_numbers),
        "unknown_atom_feature_policy": UNKNOWN_ATOM_FEATURE_POLICY,
    }


def build_real_covalent_forward_loss_batch_bundle_v0(mask_level: str, device: str = REQUESTED_DEVICE) -> dict[str, Any]:
    if mask_level not in CANONICAL_MASK_LEVELS:
        raise ValueError(f"unsupported_mask_level:{mask_level}")
    blockers: list[str] = []
    dataset = CovalentNPZDataset(SELECTED_REAL_SAMPLE_INDEX)
    dataloader = DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
        collate_fn=covalent_npz_collate_fn,
    )
    batch = next(iter(dataloader))
    adapted = adapt_covalent_batch_for_model_v0(batch, mask_level=mask_level)
    adapted_valid, adapted_reasons = validate_adapted_covalent_batch_v0(adapted)
    model_input = build_covalent_model_input_v0(adapted)
    model_input_valid, model_input_reasons = validate_covalent_model_input_v0(model_input, mask_level=mask_level)
    diffsbdd_like = build_diffsbdd_like_input_from_covalent_v0(model_input)
    diffsbdd_like_valid, diffsbdd_like_reasons = validate_diffsbdd_like_input_v0(diffsbdd_like)
    if not adapted_valid:
        blockers.append("adapted_batch_invalid")
    if not model_input_valid:
        blockers.append("model_input_invalid")
    if not diffsbdd_like_valid:
        blockers.append("diffsbdd_like_input_invalid")
    expected_region = expected_reactive_atom_region_for_mask_level_v0(mask_level)
    reactive_valid = model_input_valid and not model_input_reasons
    bundle = {
        "mask_level": mask_level,
        "dataset_created": True,
        "dataloader_created": True,
        "dataset_len": len(dataset),
        "batch_size": int(model_input["batch_size"]),
        "num_workers": NUM_WORKERS,
        "sample_ids": list(model_input["sample_id"]),
        "expected_reactive_atom_region": expected_region,
        "adapted_valid": adapted_valid,
        "adapted_reasons": adapted_reasons,
        "model_input_valid": model_input_valid,
        "model_input_reasons": model_input_reasons,
        "diffsbdd_like_valid": diffsbdd_like_valid,
        "diffsbdd_like_reasons": diffsbdd_like_reasons,
        "ligand_feature_dim": int(diffsbdd_like["ligand"]["one_hot"].shape[1]),
        "pocket_feature_dim": int(diffsbdd_like["pocket"]["one_hot"].shape[1]),
        "target_atom_count": int(model_input["ligand_target_mask"].sum().item()),
        "context_atom_count": int(model_input["ligand_context_mask"].sum().item()),
        "ligand_atom_count": int(model_input["ligand_mask"].sum().item()),
        "protein_atom_count": int(model_input["protein_mask"].sum().item()),
        "reactive_atom_region_valid": bool(reactive_valid),
        "input_source": INPUT_SOURCE,
        "synthetic_fallback_used": False,
        "model_input": _to_device(model_input, device),
        "diffsbdd_like": _to_device(diffsbdd_like, device),
        "status": "passed" if not blockers else "blocked",
        "blocking_reasons": sorted(set(blockers)),
    }
    return bundle


def build_checkpoint_compatible_real_model_batch_v0(
    diffsbdd_like: dict[str, Any],
    input_contract: dict[str, Any],
    mask_level: str,
    device: str = REQUESTED_DEVICE,
) -> dict[str, Any]:
    blockers: list[str] = []
    if mask_level not in CANONICAL_MASK_LEVELS:
        blockers.append(f"unsupported_mask_level:{mask_level}")
    target_ligand_dim = int(input_contract.get("target_ligand_feature_dim", 0))
    target_pocket_dim = int(input_contract.get("target_pocket_feature_dim", 0))
    if target_ligand_dim != 10 or target_pocket_dim != 10:
        blockers.append("input_contract_not_checkpoint_10d")
    ligand_mask = diffsbdd_like["ligand_mask"].to(dtype=torch.bool)
    protein_mask = diffsbdd_like["protein_mask"].to(dtype=torch.bool)
    ligand_atomic = diffsbdd_like["ligand_h"][ligand_mask].to(dtype=torch.long)
    protein_atomic = diffsbdd_like["protein_h"][protein_mask].to(dtype=torch.long)
    ligand_one_hot, ligand_unknown = _checkpoint_compatible_one_hot_from_atomic_numbers(ligand_atomic)
    pocket_one_hot, pocket_unknown = _checkpoint_compatible_one_hot_from_atomic_numbers(protein_atomic)
    ligand_one_hot = ligand_one_hot.to(device=torch.device(device))
    pocket_one_hot = pocket_one_hot.to(device=torch.device(device))
    target_mask = diffsbdd_like["ligand_target_mask_flat"].to(device=torch.device(device), dtype=torch.bool)
    context_mask = diffsbdd_like["ligand_context_mask_flat"].to(device=torch.device(device), dtype=torch.bool)
    expected_region = expected_reactive_atom_region_for_mask_level_v0(mask_level)
    reactive_valid = True
    reactive = diffsbdd_like["ligand_reactive_atom_index"]
    for idx in range(int(diffsbdd_like["batch_size"])):
        atom_idx = int(reactive[idx].item())
        in_target = bool(diffsbdd_like["ligand_target_mask"][idx, atom_idx].item())
        in_context = bool(diffsbdd_like["ligand_context_mask"][idx, atom_idx].item())
        if expected_region == "target":
            reactive_valid = reactive_valid and in_target and not in_context
        else:
            reactive_valid = reactive_valid and in_context and not in_target
    data_batch = {
        "lig_coords": diffsbdd_like["lig_coords"].to(device=torch.device(device), dtype=torch.float32),
        "lig_one_hot": ligand_one_hot,
        "lig_mask": diffsbdd_like["lig_mask"].to(device=torch.device(device), dtype=torch.long),
        "pocket_coords": diffsbdd_like["pocket_coords"].to(device=torch.device(device), dtype=torch.float32),
        "pocket_one_hot": pocket_one_hot,
        "pocket_mask": diffsbdd_like["pocket_mask"].to(device=torch.device(device), dtype=torch.long),
        "num_lig_atoms": diffsbdd_like["num_lig_atoms"].to(device=torch.device(device), dtype=torch.long),
        "num_pocket_nodes": diffsbdd_like["num_pocket_nodes"].to(device=torch.device(device), dtype=torch.long),
        "lig_fixed": diffsbdd_like["lig_fixed"].to(device=torch.device(device), dtype=torch.bool).view(-1),
    }
    if data_batch["lig_one_hot"].shape[1] != target_ligand_dim:
        blockers.append("ligand_one_hot_checkpoint_dim_invalid")
    if data_batch["pocket_one_hot"].shape[1] != target_pocket_dim:
        blockers.append("pocket_one_hot_checkpoint_dim_invalid")
    if data_batch["lig_coords"].shape[0] != data_batch["lig_one_hot"].shape[0]:
        blockers.append("ligand_feature_count_mismatch")
    if data_batch["pocket_coords"].shape[0] != data_batch["pocket_one_hot"].shape[0]:
        blockers.append("pocket_feature_count_mismatch")
    if not reactive_valid:
        blockers.append("reactive_atom_region_invalid")
    constructed = not blockers
    metadata = {
        "mask_level": mask_level,
        "input_source": INPUT_SOURCE,
        "real_sample_ids": list(diffsbdd_like["sample_id"]),
        "ligand_atom_count": int(data_batch["lig_coords"].shape[0]),
        "protein_atom_count": int(data_batch["pocket_coords"].shape[0]),
        "target_atom_count": int(target_mask.sum().item()),
        "context_atom_count": int(context_mask.sum().item()),
        "expected_reactive_atom_region": expected_region,
        "reactive_atom_region_valid": bool(reactive_valid),
        "checkpoint_compatible_batch_constructed": constructed,
        "no_synthetic_fallback_used": True,
        "feature_semantics_known": False,
        "checkpoint_ligand_feature_dim": int(data_batch["lig_one_hot"].shape[1]),
        "checkpoint_pocket_feature_dim": int(data_batch["pocket_one_hot"].shape[1]),
        "ligand_unknown_atom_numbers": ligand_unknown["unknown_atom_numbers"],
        "ligand_unknown_atom_count": ligand_unknown["unknown_atom_count"],
        "pocket_unknown_atom_numbers": pocket_unknown["unknown_atom_numbers"],
        "pocket_unknown_atom_count": pocket_unknown["unknown_atom_count"],
        "unknown_atom_feature_policy": UNKNOWN_ATOM_FEATURE_POLICY,
        "blocking_reasons": sorted(set(blockers)),
    }
    return {
        "data_batch": data_batch,
        "target_mask": target_mask,
        "context_mask": context_mask,
        "metadata": metadata,
        "status": "passed" if constructed else "blocked",
        "blocking_reasons": sorted(set(blockers)),
    }


def _real_size_histogram_from_bundles(bundles: dict[str, dict[str, Any]]) -> list[list[float]]:
    first = next(iter(bundles.values()))
    sizes = first["diffsbdd_like"]
    ligand_sizes = [int(value) for value in sizes["num_lig_atoms"].detach().cpu().tolist()]
    pocket_sizes = [int(value) for value in sizes["num_pocket_nodes"].detach().cpu().tolist()]
    rows = max(ligand_sizes) + 1
    cols = max(pocket_sizes) + 1
    histogram = [[0.0 for _ in range(cols)] for _ in range(rows)]
    for ligand_size, pocket_size in zip(ligand_sizes, pocket_sizes):
        histogram[ligand_size][pocket_size] += 1.0
    return histogram


def build_strict_loaded_real_size_checkpoint_compatible_model_v0(
    bundles: dict[str, dict[str, Any]],
    device: str = REQUESTED_DEVICE,
    checkpoint_path: str | Path = CHECKPOINT_PATH,
    config_preview_path: str | Path = CONFIG_PREVIEW_PATH,
) -> dict[str, Any]:
    blockers: list[str] = []
    requested_device = device
    resolved_device = RESOLVED_DEVICE
    checkpoint_reference = load_checkpoint_shape_reference_v0(checkpoint_path)
    preview_result = load_config_preview_v0(config_preview_path)
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
    model = None
    model_instantiated = False
    strict_load_success = False
    pretrained_weights_loaded = False
    pretrained_base_integration_proven = False
    node_histogram = _real_size_histogram_from_bundles(bundles) if bundles else []
    try:
        config_dict = _constructor_config_from_compatible_config(
            compatible_config,
            TEMP_REAL_DATASET_NAME,
            resolved_device,
            node_histogram=node_histogram,
        )
        model = _instantiate_model_with_temp_dataset(config_dict, _temporary_10d_dataset_info(), resolved_device)
        model_instantiated = True
        checkpoint = load_checkpoint_state_dict_for_smoke_v0(checkpoint_path)
        load_result = strict_load_checkpoint_weights_v0(model, checkpoint.get("state_dict", {}))
        blockers.extend(load_result.get("blocking_reasons", []))
        strict_load_success = bool(load_result.get("strict_load_success"))
        pretrained_weights_loaded = bool(load_result.get("pretrained_weights_loaded"))
        pretrained_base_integration_proven = bool(load_result.get("pretrained_base_integration_proven"))
    except Exception as exc:
        blockers.append(f"strict_loaded_real_size_model_failed:{type(exc).__name__}:{exc}")
        checkpoint = {"blocking_reasons": ["checkpoint_not_loaded_after_exception"]}
        load_result = {"blocking_reasons": ["load_not_attempted_after_exception"]}
    return {
        "model": model,
        "input_contract": input_contract,
        "checkpoint": checkpoint,
        "load_result": load_result,
        "requested_device": requested_device,
        "resolved_device": resolved_device,
        "model_instantiated": model_instantiated,
        "strict_load_success": strict_load_success,
        "pretrained_weights_loaded": pretrained_weights_loaded,
        "pretrained_base_integration_proven": pretrained_base_integration_proven,
        "model_strict_loaded_once": bool(model_instantiated and strict_load_success),
        "node_histogram_ligand_axis": len(node_histogram),
        "node_histogram_pocket_axis": len(node_histogram[0]) if node_histogram else 0,
        "blocking_reasons": sorted(set(blockers)),
    }


def _run_forward_loss_for_level(
    model: Any,
    checkpoint_batch: dict[str, Any],
    mask_level: str,
    forward_seed: int,
) -> dict[str, Any]:
    blockers: list[str] = []
    metadata = checkpoint_batch["metadata"]
    result: dict[str, Any] = {
        "mask_level": mask_level,
        "expected_reactive_atom_region": metadata["expected_reactive_atom_region"],
        "sample_ids": list(metadata["real_sample_ids"]),
        "batch_size": BATCH_SIZE,
        "adapted_valid": True,
        "model_input_valid": True,
        "diffsbdd_like_valid": True,
        "checkpoint_compatible_real_batch_constructed": metadata["checkpoint_compatible_batch_constructed"],
        "no_synthetic_fallback_used": metadata["no_synthetic_fallback_used"],
        "model_forward_called": False,
        "forward_call_count": 0,
        "loss_computed": False,
        "selected_loss_key": "masked_loss_total_dry",
        "selected_loss_value": math.nan,
        "loss_requires_grad": False,
        "loss_finite": False,
        "target_atom_count": metadata["target_atom_count"],
        "context_atom_count": metadata["context_atom_count"],
        "ligand_feature_dim": metadata["checkpoint_ligand_feature_dim"],
        "pocket_feature_dim": metadata["checkpoint_pocket_feature_dim"],
        "ligand_unknown_atom_count": metadata["ligand_unknown_atom_count"],
        "pocket_unknown_atom_count": metadata["pocket_unknown_atom_count"],
        "status": "blocked",
        "blocking_reasons": [],
    }
    if not metadata["checkpoint_compatible_batch_constructed"]:
        blockers.extend(metadata.get("blocking_reasons", []))
        blockers.append("checkpoint_compatible_real_model_batch_unavailable")
        result["blocking_reasons"] = sorted(set(blockers))
        return result
    torch.manual_seed(forward_seed)
    model.eval()
    capture = AtomwiseProbeCapture()
    try:
        with atomwise_probe_context_v0(model, capture):
            output = model(checkpoint_batch["data_batch"])
        result["model_forward_called"] = True
        result["forward_call_count"] = 1
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
                checkpoint_batch["target_mask"],
            )
            loss_summary = summarize_loss_components_v0(loss_components)
            blockers.extend(loss_components.get("blocking_reasons", []))
            result["loss_computed"] = loss_components.get("dry_run_status") == "passed"
            result["selected_loss_value"] = float(loss_summary.get("loss_total_dry_scalar", math.nan))
            result["loss_requires_grad"] = bool(loss_summary.get("loss_total_dry_requires_grad"))
            result["loss_finite"] = bool(loss_summary.get("loss_total_dry_finite"))
            if not result["loss_computed"]:
                blockers.append("masked_loss_not_computed")
            if not result["loss_requires_grad"]:
                blockers.append("selected_loss_does_not_require_grad")
            if not result["loss_finite"]:
                blockers.append("selected_loss_not_finite")
        del output
        del capture
    except Exception as exc:
        blockers.append(f"forward_loss_failed:{type(exc).__name__}:{exc}")
    result["status"] = "passed" if not blockers else "blocked"
    result["blocking_reasons"] = sorted(set(blockers))
    return result


def run_real_covalent_pretrained_forward_loss_smoke_v0(device: str = REQUESTED_DEVICE) -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step12c_validated = validate_step12c_outputs_v0()
        step12b_validated = True
    except Exception as exc:
        step12c_validated = False
        step12b_validated = False
        blockers.append(f"step12c_or_step12b_validation_failed:{type(exc).__name__}:{exc}")
    bundles: dict[str, dict[str, Any]] = {}
    for mask_level in CANONICAL_MASK_LEVELS:
        try:
            bundle = build_real_covalent_forward_loss_batch_bundle_v0(mask_level, device)
        except Exception as exc:
            bundle = {
                "mask_level": mask_level,
                "status": "blocked",
                "blocking_reasons": [f"real_batch_bundle_failed:{type(exc).__name__}:{exc}"],
            }
        bundles[mask_level] = bundle
        blockers.extend(f"{mask_level}:{reason}" for reason in bundle.get("blocking_reasons", []))
    load_bundle = build_strict_loaded_real_size_checkpoint_compatible_model_v0(bundles, device)
    blockers.extend(load_bundle.get("blocking_reasons", []))
    model = load_bundle.get("model")
    checkpoint_batches: dict[str, dict[str, Any]] = {}
    level_results: dict[str, dict[str, Any]] = {}
    if model is not None and load_bundle.get("strict_load_success"):
        for idx, mask_level in enumerate(CANONICAL_MASK_LEVELS):
            bundle = bundles[mask_level]
            if bundle.get("status") != "passed":
                level_results[mask_level] = {
                    "mask_level": mask_level,
                    "status": "blocked",
                    "blocking_reasons": bundle.get("blocking_reasons", []),
                    "model_forward_called": False,
                    "forward_call_count": 0,
                    "loss_computed": False,
                    "loss_finite": False,
                    "loss_requires_grad": False,
                }
                continue
            checkpoint_batch = build_checkpoint_compatible_real_model_batch_v0(
                bundle["diffsbdd_like"],
                load_bundle["input_contract"],
                mask_level,
                load_bundle["resolved_device"],
            )
            checkpoint_batches[mask_level] = checkpoint_batch
            result = _run_forward_loss_for_level(model, checkpoint_batch, mask_level, 6201 + idx)
            result["adapted_valid"] = bundle["adapted_valid"]
            result["model_input_valid"] = bundle["model_input_valid"]
            result["diffsbdd_like_valid"] = bundle["diffsbdd_like_valid"]
            level_results[mask_level] = result
            blockers.extend(f"{mask_level}:{reason}" for reason in result.get("blocking_reasons", []))
    else:
        blockers.append("strict_loaded_model_unavailable")
    del model
    return {
        "step12c_validated": step12c_validated,
        "step12b_mask_level_aware_validator_validated": step12b_validated,
        "load_bundle": {key: value for key, value in load_bundle.items() if key != "model"},
        "bundles": bundles,
        "checkpoint_batches": checkpoint_batches,
        "level_results": level_results,
        "blocking_reasons": sorted(set(reason for reason in blockers if reason)),
    }


def build_real_covalent_pretrained_forward_loss_smoke_v0(device: str = REQUESTED_DEVICE) -> dict[str, Any]:
    run_result = run_real_covalent_pretrained_forward_loss_smoke_v0(device)
    level_results = run_result["level_results"]
    loss_values = [
        float(result["selected_loss_value"])
        for result in level_results.values()
        if _finite_scalar(result.get("selected_loss_value"))
    ]
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
    all_adapted = bool(level_results and all(result.get("adapted_valid") is True for result in level_results.values()))
    all_model_inputs = bool(level_results and all(result.get("model_input_valid") is True for result in level_results.values()))
    all_diffsbdd = bool(level_results and all(result.get("diffsbdd_like_valid") is True for result in level_results.values()))
    all_checkpoint_batches = bool(
        level_results
        and all(result.get("checkpoint_compatible_real_batch_constructed") is True for result in level_results.values())
    )
    all_forward_once = bool(
        level_results
        and all(result.get("model_forward_called") is True and result.get("forward_call_count") == 1 for result in level_results.values())
    )
    all_losses_computed = bool(level_results and all(result.get("loss_computed") is True for result in level_results.values()))
    all_losses_finite = bool(level_results and all(result.get("loss_finite") is True for result in level_results.values()))
    all_losses_require_grad = bool(level_results and all(result.get("loss_requires_grad") is True for result in level_results.values()))
    no_synthetic_fallback = bool(
        level_results and all(result.get("no_synthetic_fallback_used") is True for result in level_results.values())
    )
    load_bundle = run_result["load_bundle"]
    model_forward_count = sum(int(result.get("forward_call_count", 0)) for result in level_results.values())
    smoke_passed = bool(
        run_result["step12c_validated"]
        and run_result["step12b_mask_level_aware_validator_validated"]
        and load_bundle.get("model_instantiated")
        and load_bundle.get("strict_load_success")
        and load_bundle.get("pretrained_weights_loaded")
        and load_bundle.get("pretrained_base_integration_proven")
        and len(level_results) == len(CANONICAL_MASK_LEVELS)
        and len(passed_levels) == len(CANONICAL_MASK_LEVELS)
        and all_adapted
        and all_model_inputs
        and all_diffsbdd
        and all_checkpoint_batches
        and no_synthetic_fallback
        and model_forward_count == len(CANONICAL_MASK_LEVELS)
        and all_forward_once
        and all_losses_computed
        and all_losses_finite
        and all_losses_require_grad
        and not source_modified
        and not forbidden_artifacts
        and not blockers
    )
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step12c_validated": run_result["step12c_validated"],
        "step12b_mask_level_aware_validator_validated": run_result["step12b_mask_level_aware_validator_validated"],
        "input_source": INPUT_SOURCE,
        "selected_sample_index": str(SELECTED_REAL_SAMPLE_INDEX),
        "selected_artifact_is_real_covalent": True,
        "selected_artifact_is_synthetic_only": False,
        "checkpoint_path": str(CHECKPOINT_PATH),
        "requested_device": device,
        "resolved_device": RESOLVED_DEVICE,
        "batch_size": BATCH_SIZE,
        "num_workers": NUM_WORKERS,
        "canonical_mask_levels": list(CANONICAL_MASK_LEVELS),
        "canonical_mask_level_count": len(CANONICAL_MASK_LEVELS),
        "attempted_mask_level_count": len(level_results),
        "passed_mask_level_count": len(passed_levels),
        "failed_mask_level_count": len(failed_levels),
        "model_instantiated": bool(load_bundle.get("model_instantiated")),
        "strict_load_success": bool(load_bundle.get("strict_load_success")),
        "pretrained_weights_loaded": bool(load_bundle.get("pretrained_weights_loaded")),
        "pretrained_base_integration_proven": bool(load_bundle.get("pretrained_base_integration_proven")),
        "model_strict_loaded_once": bool(load_bundle.get("model_strict_loaded_once")),
        "model_forward_called": model_forward_count > 0,
        "model_forward_call_count": model_forward_count,
        "all_level_forward_call_count_exactly_one": all_forward_once,
        "all_adapted_batches_valid": all_adapted,
        "all_model_inputs_valid": all_model_inputs,
        "all_diffsbdd_like_inputs_valid": all_diffsbdd,
        "all_checkpoint_compatible_real_batches_constructed": all_checkpoint_batches,
        "no_synthetic_fallback_used": no_synthetic_fallback,
        "all_losses_computed": all_losses_computed,
        "all_losses_finite": all_losses_finite,
        "all_losses_require_grad": all_losses_require_grad,
        "selected_loss_key": "masked_loss_total_dry",
        "min_selected_loss_value": min(loss_values) if loss_values else math.nan,
        "max_selected_loss_value": max(loss_values) if loss_values else math.nan,
        "mean_selected_loss_value": sum(loss_values) / len(loss_values) if loss_values else math.nan,
        "real_covalent_pretrained_forward_loss_smoke_passed": smoke_passed,
        "real_covalent_forward_loss_contract_proven": smoke_passed,
        "real_covalent_all_mask_levels_forward_loss_proven": smoke_passed,
        "real_covalent_backward_smoke_allowed": smoke_passed,
        "recommended_next_step": "real_covalent_backward_smoke"
        if smoke_passed
        else "real_covalent_pretrained_forward_loss_smoke_debug",
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
        "all_checks_passed": smoke_passed,
        "blocking_reasons": blockers,
    }
    loss_table_rows = []
    for level in CANONICAL_MASK_LEVELS:
        result = level_results.get(level, {"mask_level": level, "status": "blocked", "blocking_reasons": ["not_attempted"]})
        loss_table_rows.append(
            {
                "mask_level": level,
                "expected_reactive_atom_region": result.get(
                    "expected_reactive_atom_region", expected_reactive_atom_region_for_mask_level_v0(level)
                ),
                "sample_ids": result.get("sample_ids", []),
                "batch_size": result.get("batch_size", BATCH_SIZE),
                "adapted_valid": result.get("adapted_valid", False),
                "model_input_valid": result.get("model_input_valid", False),
                "diffsbdd_like_valid": result.get("diffsbdd_like_valid", False),
                "checkpoint_compatible_real_batch_constructed": result.get(
                    "checkpoint_compatible_real_batch_constructed", False
                ),
                "no_synthetic_fallback_used": result.get("no_synthetic_fallback_used", False),
                "model_forward_called": result.get("model_forward_called", False),
                "forward_call_count": result.get("forward_call_count", 0),
                "loss_computed": result.get("loss_computed", False),
                "selected_loss_key": result.get("selected_loss_key", "masked_loss_total_dry"),
                "selected_loss_value": result.get("selected_loss_value", ""),
                "loss_requires_grad": result.get("loss_requires_grad", False),
                "loss_finite": result.get("loss_finite", False),
                "target_atom_count": result.get("target_atom_count", 0),
                "context_atom_count": result.get("context_atom_count", 0),
                "ligand_feature_dim": result.get("ligand_feature_dim", 0),
                "pocket_feature_dim": result.get("pocket_feature_dim", 0),
                "status": result.get("status", "blocked"),
                "blocking_reasons": result.get("blocking_reasons", []),
            }
        )
    return {
        "manifest": manifest,
        "loss_table_rows": loss_table_rows,
        "run_result": run_result,
        "report_sections": {
            "step12c_precondition": {
                "step12c_validated": run_result["step12c_validated"],
                "step12b_mask_level_aware_validator_validated": run_result[
                    "step12b_mask_level_aware_validator_validated"
                ],
            },
            "real_batch_loading": {
                "input_source": INPUT_SOURCE,
                "selected_sample_index": str(SELECTED_REAL_SAMPLE_INDEX),
                "batch_size": BATCH_SIZE,
                "num_workers": NUM_WORKERS,
            },
            "mask_level_aware_model_input": {
                "all_model_inputs_valid": all_model_inputs,
                "canonical_mask_levels": list(CANONICAL_MASK_LEVELS),
            },
            "checkpoint_compatible_real_batch": {
                "all_checkpoint_compatible_real_batches_constructed": all_checkpoint_batches,
                "no_synthetic_fallback_used": no_synthetic_fallback,
                "unknown_atom_feature_policy": UNKNOWN_ATOM_FEATURE_POLICY,
            },
            "pretrained_strict_load": {
                "model_instantiated": manifest["model_instantiated"],
                "strict_load_success": manifest["strict_load_success"],
                "pretrained_weights_loaded": manifest["pretrained_weights_loaded"],
                "pretrained_base_integration_proven": manifest["pretrained_base_integration_proven"],
                "model_strict_loaded_once": manifest["model_strict_loaded_once"],
            },
            "forward_loss_by_mask_level": {
                "model_forward_call_count": model_forward_count,
                "all_level_forward_call_count_exactly_one": all_forward_once,
                "all_losses_computed": all_losses_computed,
                "all_losses_finite": all_losses_finite,
                "all_losses_require_grad": all_losses_require_grad,
            },
            "aggregate_loss_decision": {
                "selected_loss_key": manifest["selected_loss_key"],
                "min_selected_loss_value": manifest["min_selected_loss_value"],
                "max_selected_loss_value": manifest["max_selected_loss_value"],
                "mean_selected_loss_value": manifest["mean_selected_loss_value"],
            },
            "safety_boundary": {
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
                "real_covalent_pretrained_forward_loss_smoke_passed": smoke_passed,
                "real_covalent_backward_smoke_allowed": smoke_passed,
                "recommended_next_step": manifest["recommended_next_step"],
            },
        },
    }
