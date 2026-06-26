from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from covalent_ext.checkpoint_compatible_pretrained_load_smoke import (  # noqa: E402
    instantiate_model_for_pretrained_load_v0,
    load_checkpoint_state_dict_for_smoke_v0,
    strict_load_checkpoint_weights_v0,
)
from covalent_ext.diffsbdd_atomwise_loss_hook_prototype import (  # noqa: E402
    AtomwiseProbeCapture,
    atomwise_probe_context_v0,
)
from covalent_ext.masked_loss_dry_run import (  # noqa: E402
    compute_masked_loss_components_v0,
    summarize_loss_components_v0,
)


STAGE = "pretrained_masked_loss_smoke_v0"
PREVIOUS_STAGE = "checkpoint_compatible_pretrained_load_smoke_v0"
CHECKPOINT_PATH = Path("checkpoints/crossdocked_fullatom_cond.ckpt")
CONFIG_PREVIEW_PATH = Path(
    "data/derived/covalent_small/checkpoint_original_config_instantiation_design_v0/checkpoint_original_config_preview.json"
)
STEP11E_MANIFEST_JSON = Path(
    "data/derived/covalent_small/checkpoint_compatible_pretrained_load_smoke_v0/"
    "checkpoint_compatible_pretrained_load_smoke_manifest.json"
)
STEP11E_SUMMARY_MD = Path("docs/checkpoint_compatible_pretrained_load_smoke_v0_summary.md")
OUTPUT_ROOT = Path("data/derived/covalent_small/pretrained_masked_loss_smoke_v0")
REPORT_CSV = OUTPUT_ROOT / "pretrained_masked_loss_smoke_report.csv"
MANIFEST_JSON = OUTPUT_ROOT / "pretrained_masked_loss_smoke_manifest.json"
LOSS_TABLE_CSV = OUTPUT_ROOT / "pretrained_masked_loss_smoke_loss_table.csv"
SUMMARY_MD = Path("docs/pretrained_masked_loss_smoke_v0_summary.md")
MASK_LEVELS = [
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "C_scaffold_linker_warhead",
]
FORBIDDEN_ARTIFACT_SUFFIXES = {".pt", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".ckpt", ".pth"}
PROTECTED_SOURCE_PATHS = ["equivariant_diffusion/", "lightning_modules.py"]
SAFETY_FALSE_FIELDS = [
    "training_allowed",
    "formal_training_allowed",
    "finetune_allowed",
    "optimizer_allowed",
    "quality_claim_allowed",
    "loss_decrease_required",
    "backward_called",
    "optimizer_created",
    "optimizer_step_called",
    "training_step_called",
    "trainer_fit_called",
    "checkpoint_saved",
    "model_saved",
]


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_diff_exists() -> bool:
    unstaged = subprocess.run(
        ["git", "diff", "--quiet", "--", *PROTECTED_SOURCE_PATHS],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    staged = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", *PROTECTED_SOURCE_PATHS],
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


def _shape(value: Any) -> list[int]:
    return [int(dim) for dim in value.shape] if torch.is_tensor(value) else []


def _finite_tensor(value: Any) -> bool:
    return bool(torch.is_tensor(value) and torch.isfinite(value.detach()).all().item())


def _scalar(value: Any) -> float | str:
    if not torch.is_tensor(value):
        return ""
    detached = value.detach()
    return float(detached.mean().item()) if detached.numel() else ""


def _count_nan_inf(value: Any) -> dict[str, int]:
    tensors: list[torch.Tensor] = []

    def collect(child: Any) -> None:
        if torch.is_tensor(child):
            tensors.append(child)
        elif isinstance(child, dict):
            for item in child.values():
                collect(item)
        elif isinstance(child, (list, tuple)):
            for item in child:
                collect(item)

    collect(value)
    nan_count = 0
    inf_count = 0
    for tensor in tensors:
        if torch.is_floating_point(tensor) or torch.is_complex(tensor):
            nan_count += int(torch.isnan(tensor.detach()).sum().item())
            inf_count += int(torch.isinf(tensor.detach()).sum().item())
    return {"nan_count": nan_count, "inf_count": inf_count}


def validate_step11e_outputs_v0() -> bool:
    if not STEP11E_MANIFEST_JSON.is_file() or not STEP11E_SUMMARY_MD.is_file():
        raise FileNotFoundError("Step 11E outputs are missing")
    manifest = _load_json(STEP11E_MANIFEST_JSON)
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "checkpoint_compatible_instantiation_wrapper_v0",
        "step11d_validated": True,
        "checkpoint_loaded": True,
        "checkpoint_state_dict_key_count": 122,
        "model_instantiated": True,
        "model_class": "LigandPocketDDPM",
        "model_state_dict_key_count": 122,
        "pre_load_shape_matched_key_count": 122,
        "pre_load_shape_matched_ratio": 1.0,
        "pre_load_incompatible_shape_count": 0,
        "strict_load_attempted": True,
        "strict_load_success": True,
        "missing_keys_count": 0,
        "unexpected_keys_count": 0,
        "incompatible_shape_count": 0,
        "loaded_parameter_key_count": 122,
        "loaded_parameter_numel_total": 1006560,
        "pretrained_weights_loaded": True,
        "pretrained_base_integration_proven": True,
        "forward_smoke_attempted": True,
        "forward_smoke_success": True,
        "output_finite": True,
        "nan_count": 0,
        "inf_count": 0,
        "load_smoke_status": "checkpoint_compatible_pretrained_load_proven",
        "pretrained_masked_loss_smoke_allowed": True,
        "masked_loss_smoke_allowed": False,
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "original_source_files_modified": False,
        "forbidden_artifacts_created": False,
        "all_checks_passed": True,
        "recommended_next_step": "pretrained_masked_loss_smoke_on_checkpoint_compatible_model",
    }
    blockers = [f"step11e_{key}_invalid:{manifest.get(key)!r}" for key, value in expected.items() if manifest.get(key) != value]
    summary_text = STEP11E_SUMMARY_MD.read_text(encoding="utf-8")
    if "strict_load_success: true" not in summary_text:
        blockers.append("step11e_summary_strict_load_success_missing")
    if "pretrained_masked_loss_smoke_allowed: true" not in summary_text:
        blockers.append("step11e_summary_masked_loss_permission_missing")
    if blockers:
        raise ValueError(";".join(blockers))
    return True


def build_strict_loaded_checkpoint_compatible_model_for_masked_loss_v0(
    device: str = "cpu",
    checkpoint_path: str | Path = CHECKPOINT_PATH,
    config_preview_path: str | Path = CONFIG_PREVIEW_PATH,
) -> dict[str, Any]:
    checkpoint = load_checkpoint_state_dict_for_smoke_v0(checkpoint_path)
    model_result = instantiate_model_for_pretrained_load_v0(device, checkpoint_path, config_preview_path)
    load_result: dict[str, Any] = {
        "strict_load_success": False,
        "pretrained_weights_loaded": False,
        "pretrained_base_integration_proven": False,
        "blocking_reasons": ["model_or_state_dict_unavailable"],
    }
    if model_result.get("model_instantiated") and checkpoint.get("state_dict"):
        load_result = strict_load_checkpoint_weights_v0(model_result["model"], checkpoint["state_dict"])
    return {
        "model": model_result.get("model"),
        "input_contract": model_result.get("input_contract", {}),
        "checkpoint": checkpoint,
        "model_result": model_result,
        "load_result": load_result,
        "requested_device": model_result.get("requested_device", device),
        "resolved_device": model_result.get("resolved_device", "cpu"),
        "model_instantiated": bool(model_result.get("model_instantiated")),
        "strict_load_success": bool(load_result.get("strict_load_success")),
        "pretrained_weights_loaded": bool(load_result.get("pretrained_weights_loaded")),
        "pretrained_base_integration_proven": bool(load_result.get("pretrained_base_integration_proven")),
    }


def _mask_tensors_for_level(mask_level: str, device: torch.device) -> dict[str, torch.Tensor]:
    scaffold = torch.tensor([1, 0, 0, 0], dtype=torch.bool, device=device)
    linker = torch.tensor([0, 1, 0, 0], dtype=torch.bool, device=device)
    warhead = torch.tensor([0, 0, 1, 1], dtype=torch.bool, device=device)
    if mask_level == "A_warhead_only":
        target = warhead
    elif mask_level == "B_linker_warhead":
        target = linker | warhead
    elif mask_level == "B2_scaffold_warhead":
        target = scaffold | warhead
    elif mask_level == "C_scaffold_linker_warhead":
        target = scaffold | linker | warhead
    else:
        raise ValueError(f"unknown mask level: {mask_level}")
    context = ~target
    return {
        "scaffold_mask": scaffold,
        "linker_mask": linker,
        "warhead_mask": warhead,
        "target_mask": target,
        "context_mask": context,
    }


def build_pretrained_masked_loss_candidate_inputs_v0(
    mask_level: str,
    input_contract: dict[str, Any],
    device: str = "cpu",
) -> dict[str, Any]:
    if mask_level not in MASK_LEVELS:
        raise ValueError(f"Unsupported mask level: {mask_level}")
    torch_device = torch.device(device)
    ligand_count = 4
    pocket_count = 5
    ligand_dim = int(input_contract.get("target_ligand_feature_dim", 10))
    pocket_dim = int(input_contract.get("target_pocket_feature_dim", 10))
    ligand_one_hot = torch.zeros(ligand_count, ligand_dim, device=torch_device)
    pocket_one_hot = torch.zeros(pocket_count, pocket_dim, device=torch_device)
    ligand_one_hot[torch.arange(ligand_count, device=torch_device), torch.arange(ligand_count, device=torch_device)] = 1.0
    pocket_one_hot[torch.arange(pocket_count, device=torch_device), torch.arange(pocket_count, device=torch_device)] = 1.0
    masks = _mask_tensors_for_level(mask_level, torch_device)
    target_mask = masks["target_mask"]
    context_mask = masks["context_mask"]
    data_batch = {
        "lig_coords": torch.tensor(
            [[-0.3, 0.0, 0.1], [0.2, -0.2, 0.3], [0.4, 0.1, -0.1], [0.8, 0.2, 0.2]],
            dtype=torch.float32,
            device=torch_device,
        ),
        "lig_one_hot": ligand_one_hot,
        "lig_mask": torch.zeros(ligand_count, dtype=torch.long, device=torch_device),
        "pocket_coords": torch.tensor(
            [
                [-1.0, 0.0, 0.0],
                [-0.5, 0.5, 0.2],
                [0.0, -0.7, 0.3],
                [0.6, 0.2, -0.4],
                [1.0, -0.1, 0.1],
            ],
            dtype=torch.float32,
            device=torch_device,
        ),
        "pocket_one_hot": pocket_one_hot,
        "pocket_mask": torch.zeros(pocket_count, dtype=torch.long, device=torch_device),
        "num_lig_atoms": torch.tensor([ligand_count], dtype=torch.long, device=torch_device),
        "num_pocket_nodes": torch.tensor([pocket_count], dtype=torch.long, device=torch_device),
        "lig_fixed": context_mask.to(dtype=torch.bool),
        "covalent_mask_level": mask_level,
        "scaffold_atom_mask": masks["scaffold_mask"],
        "linker_atom_mask": masks["linker_mask"],
        "warhead_atom_mask": masks["warhead_mask"],
        "ligand_target_mask_flat": target_mask,
        "ligand_context_mask_flat": context_mask,
        "generation_mask_flat": target_mask,
        "ligand_reactive_atom_index": torch.tensor([2], dtype=torch.long, device=torch_device),
        "reactive_residue_index": torch.tensor([0], dtype=torch.long, device=torch_device),
    }
    metadata = {
        "mask_level": mask_level,
        "batch_size": 1,
        "ligand_atom_count": ligand_count,
        "pocket_atom_count": pocket_count,
        "target_atom_count": int(target_mask.sum().item()),
        "context_atom_count": int(context_mask.sum().item()),
        "feature_semantics_known": False,
        "synthetic_shape_smoke_only": True,
        "not_training_data": True,
        "synthetic_mask_loss_adapter_used": True,
        "target_mask": target_mask,
        "context_mask": context_mask,
    }
    return {"data_batch": data_batch, "metadata": metadata}


def _output0_and_info(output: Any) -> tuple[Any, dict[str, Any]]:
    if isinstance(output, tuple) and output:
        output0 = output[0]
        info = output[1] if len(output) > 1 and isinstance(output[1], dict) else {}
        return output0, info
    return output, {}


def _loss_scalar_candidates(output0: Any, info: dict[str, Any], loss_summary: dict[str, Any]) -> dict[str, float]:
    candidates: dict[str, float] = {}
    if loss_summary.get("loss_total_dry_finite"):
        candidates["masked_loss_total_dry"] = float(loss_summary["loss_total_dry_scalar"])
    for key in ["error_t_lig", "loss_0", "kl_prior"]:
        value = info.get(key)
        if torch.is_tensor(value) and torch.isfinite(value.detach()).all().item():
            candidates[key] = float(value.detach().mean().item())
    if torch.is_tensor(output0) and torch.isfinite(output0.detach()).all().item():
        candidates["output0_mean"] = float(output0.detach().mean().item())
    return candidates


def run_pretrained_masked_loss_smoke_for_level_v0(
    model: Any,
    mask_level: str,
    input_contract: dict[str, Any],
    device: str = "cpu",
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "mask_level": mask_level,
        "candidate_inputs_built": False,
        "forward_attempted": False,
        "forward_success": False,
        "loss_hook_attempted": False,
        "loss_hook_success": False,
        "finite_loss": False,
        "finite_outputs": False,
        "loss_scalar_keys": [],
        "loss_scalar_values": {},
        "selected_primary_loss_key": "",
        "selected_primary_loss_value": "",
        "nan_count": 0,
        "inf_count": 0,
        "mask_tensor_summary": {},
        "synthetic_mask_loss_adapter_used": True,
        "status": "blocked",
        "blocking_reasons": [],
    }
    try:
        candidate = build_pretrained_masked_loss_candidate_inputs_v0(mask_level, input_contract, device)
        result["candidate_inputs_built"] = True
        metadata = candidate["metadata"]
        target_mask = metadata["target_mask"]
        result["mask_tensor_summary"] = {
            "ligand_atom_count": metadata["ligand_atom_count"],
            "pocket_atom_count": metadata["pocket_atom_count"],
            "target_atom_count": metadata["target_atom_count"],
            "context_atom_count": metadata["context_atom_count"],
            "target_mask_shape": _shape(target_mask),
        }
        model.eval()
        capture = AtomwiseProbeCapture()
        result["forward_attempted"] = True
        with torch.no_grad():
            with atomwise_probe_context_v0(model, capture):
                output = model(candidate["data_batch"])
        result["forward_success"] = True
        nan_inf = _count_nan_inf(output)
        result.update(nan_inf)
        result["finite_outputs"] = nan_inf["nan_count"] == 0 and nan_inf["inf_count"] == 0
        output0, info = _output0_and_info(output)
        if not torch.is_tensor(output0):
            result["blocking_reasons"].append("output0_not_tensor")
        if not (capture.eps_t_lig is not None and capture.net_out_lig is not None):
            result["blocking_reasons"].append("atomwise_probe_tensors_missing")
        if capture.eps_t_lig is not None and capture.net_out_lig is not None and torch.is_tensor(output0):
            result["loss_hook_attempted"] = True
            loss_components = compute_masked_loss_components_v0(
                output0,
                capture.eps_t_lig,
                capture.net_out_lig,
                target_mask,
            )
            loss_summary = summarize_loss_components_v0(loss_components)
            result["blocking_reasons"].extend(loss_components.get("blocking_reasons", []))
            result["loss_hook_success"] = loss_components.get("dry_run_status") == "passed"
            result["finite_loss"] = bool(loss_summary.get("loss_total_dry_finite"))
            candidates = _loss_scalar_candidates(output0, info, loss_summary)
            result["loss_scalar_keys"] = list(candidates.keys())
            result["loss_scalar_values"] = candidates
            for key in ["masked_loss_total_dry", "error_t_lig", "loss_0", "kl_prior", "output0_mean"]:
                if key in candidates:
                    result["selected_primary_loss_key"] = key
                    result["selected_primary_loss_value"] = candidates[key]
                    break
            result["mask_tensor_summary"].update(
                {
                    "eps_t_lig_shape": _shape(capture.eps_t_lig),
                    "net_out_lig_shape": _shape(capture.net_out_lig),
                    "ligand_mask_flat_shape": _shape(capture.ligand_mask_flat),
                    "target_mask_matches_ligand_atoms": bool(target_mask.shape[0] == capture.eps_t_lig.shape[0]),
                }
            )
        required_true = [
            "candidate_inputs_built",
            "forward_success",
            "loss_hook_success",
            "finite_loss",
            "finite_outputs",
        ]
        for field_name in required_true:
            if result.get(field_name) is not True:
                result["blocking_reasons"].append(f"{field_name}_not_true")
        if not result["selected_primary_loss_key"]:
            result["blocking_reasons"].append("primary_loss_not_selected")
        result["blocking_reasons"] = sorted(set(reason for reason in result["blocking_reasons"] if reason))
        result["status"] = "passed" if not result["blocking_reasons"] else "blocked"
    except Exception as exc:
        result["blocking_reasons"].append(f"masked_loss_smoke_failed:{type(exc).__name__}:{exc}")
        result["status"] = "blocked"
    return result


def run_pretrained_masked_loss_smoke_all_levels_v0(
    model: Any,
    input_contract: dict[str, Any],
    device: str = "cpu",
) -> dict[str, Any]:
    per_level_results = [
        run_pretrained_masked_loss_smoke_for_level_v0(model, mask_level, input_contract, device)
        for mask_level in MASK_LEVELS
    ]
    mask_levels_passed = [row["mask_level"] for row in per_level_results if row["status"] == "passed"]
    failed_mask_levels = [row["mask_level"] for row in per_level_results if row["status"] != "passed"]
    loss_table_rows = [
        {
            "stage": STAGE,
            "mask_level": row["mask_level"],
            "candidate_inputs_built": row["candidate_inputs_built"],
            "forward_success": row["forward_success"],
            "loss_hook_success": row["loss_hook_success"],
            "finite_loss": row["finite_loss"],
            "selected_primary_loss_key": row["selected_primary_loss_key"],
            "selected_primary_loss_value": row["selected_primary_loss_value"],
            "nan_count": row["nan_count"],
            "inf_count": row["inf_count"],
            "synthetic_mask_loss_adapter_used": row["synthetic_mask_loss_adapter_used"],
            "status": row["status"],
            "blocking_reasons": ";".join(row["blocking_reasons"]),
        }
        for row in per_level_results
    ]
    return {
        "per_level_results": per_level_results,
        "mask_levels_attempted": MASK_LEVELS,
        "mask_levels_passed": mask_levels_passed,
        "all_mask_levels_passed": len(mask_levels_passed) == len(MASK_LEVELS),
        "finite_loss_level_count": sum(1 for row in per_level_results if row["finite_loss"]),
        "failed_mask_levels": failed_mask_levels,
        "loss_table_rows": loss_table_rows,
    }


def build_pretrained_masked_loss_smoke_decision_v0(
    load_evidence: dict[str, Any],
    all_level_results: dict[str, Any],
) -> dict[str, Any]:
    pretrained_loaded = bool(
        load_evidence.get("strict_load_success")
        and load_evidence.get("pretrained_weights_loaded")
        and load_evidence.get("pretrained_base_integration_proven")
    )
    if pretrained_loaded and all_level_results.get("all_mask_levels_passed"):
        return {
            "masked_loss_smoke_status": "pretrained_masked_loss_smoke_passed",
            "pretrained_masked_loss_smoke_passed": True,
            "pretrained_model_mask_hook_integration_proven": True,
            "recommended_next_step": "pretrained_masked_loss_microbatch_dry_run_design",
            "microbatch_dry_run_allowed": True,
            "training_allowed": False,
            "formal_training_allowed": False,
            "finetune_allowed": False,
            "optimizer_allowed": False,
            "quality_claim_allowed": False,
            "loss_decrease_required": False,
        }
    if pretrained_loaded:
        return {
            "masked_loss_smoke_status": "pretrained_masked_loss_partial",
            "pretrained_masked_loss_smoke_passed": False,
            "pretrained_model_mask_hook_integration_proven": False,
            "recommended_next_step": "pretrained_masked_loss_failed_level_debug",
            "microbatch_dry_run_allowed": False,
            "training_allowed": False,
            "formal_training_allowed": False,
            "finetune_allowed": False,
            "optimizer_allowed": False,
            "quality_claim_allowed": False,
            "loss_decrease_required": False,
        }
    return {
        "masked_loss_smoke_status": "pretrained_model_unavailable",
        "pretrained_masked_loss_smoke_passed": False,
        "pretrained_model_mask_hook_integration_proven": False,
        "recommended_next_step": "checkpoint_compatible_pretrained_load_smoke_debug",
        "microbatch_dry_run_allowed": False,
        "training_allowed": False,
        "formal_training_allowed": False,
        "finetune_allowed": False,
        "optimizer_allowed": False,
        "quality_claim_allowed": False,
        "loss_decrease_required": False,
    }


def build_pretrained_masked_loss_smoke_v0(
    device: str = "cpu",
    checkpoint_path: str | Path = CHECKPOINT_PATH,
    config_preview_path: str | Path = CONFIG_PREVIEW_PATH,
) -> dict[str, Any]:
    blockers: list[str] = []
    try:
        step11e_validated = validate_step11e_outputs_v0()
    except Exception as exc:
        step11e_validated = False
        blockers.append(f"step11e_validation_failed:{type(exc).__name__}:{exc}")
    load_bundle = build_strict_loaded_checkpoint_compatible_model_for_masked_loss_v0(device, checkpoint_path, config_preview_path)
    checkpoint = load_bundle["checkpoint"]
    load_result = load_bundle["load_result"]
    blockers.extend(checkpoint.get("blocking_reasons", []))
    blockers.extend(load_bundle["model_result"].get("blocking_reasons", []))
    blockers.extend(load_result.get("blocking_reasons", []))
    all_level_results = {
        "per_level_results": [],
        "mask_levels_attempted": MASK_LEVELS,
        "mask_levels_passed": [],
        "all_mask_levels_passed": False,
        "finite_loss_level_count": 0,
        "failed_mask_levels": MASK_LEVELS,
        "loss_table_rows": [],
    }
    if step11e_validated and load_bundle["strict_load_success"] and load_bundle["model"] is not None:
        all_level_results = run_pretrained_masked_loss_smoke_all_levels_v0(
            load_bundle["model"],
            load_bundle["input_contract"],
            load_bundle["resolved_device"],
        )
    decision = build_pretrained_masked_loss_smoke_decision_v0(load_bundle, all_level_results)
    for row in all_level_results["per_level_results"]:
        blockers.extend(row.get("blocking_reasons", []))
    source_modified = _source_diff_exists()
    forbidden_artifacts = _forbidden_artifacts_created()
    if source_modified:
        blockers.append("original_source_files_modified")
    if forbidden_artifacts:
        blockers.append("forbidden_artifacts_created")
    blockers = sorted(set(reason for reason in blockers if reason))
    all_checks_passed = bool(
        step11e_validated
        and load_bundle["strict_load_success"]
        and load_bundle["pretrained_weights_loaded"]
        and all_level_results["all_mask_levels_passed"]
        and decision["pretrained_masked_loss_smoke_passed"]
        and not source_modified
        and not forbidden_artifacts
    )
    loss_by_level = {
        row["mask_level"]: row["selected_primary_loss_value"]
        for row in all_level_results["per_level_results"]
    }
    manifest = {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step11e_validated": step11e_validated,
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_sha256": _sha256(checkpoint_path) if Path(checkpoint_path).is_file() else "",
        "pretrained_weights_loaded": load_bundle["pretrained_weights_loaded"],
        "pretrained_base_integration_proven": load_bundle["pretrained_base_integration_proven"],
        "model_instantiated": load_bundle["model_instantiated"],
        "strict_load_success": load_bundle["strict_load_success"],
        "requested_device": load_bundle["requested_device"],
        "resolved_device": load_bundle["resolved_device"],
        "mask_levels_attempted": all_level_results["mask_levels_attempted"],
        "mask_levels_passed": all_level_results["mask_levels_passed"],
        "all_mask_levels_passed": all_level_results["all_mask_levels_passed"],
        "finite_loss_level_count": all_level_results["finite_loss_level_count"],
        "failed_mask_levels": all_level_results["failed_mask_levels"],
        "selected_primary_loss_value_by_mask_level": loss_by_level,
        "pretrained_masked_loss_smoke_passed": decision["pretrained_masked_loss_smoke_passed"],
        "pretrained_model_mask_hook_integration_proven": decision["pretrained_model_mask_hook_integration_proven"],
        "synthetic_shape_smoke_only": True,
        "feature_semantics_known": False,
        "synthetic_mask_loss_adapter_used": True,
        **decision,
        "masked_loss_smoke_allowed": True,
        "backward_called": False,
        "optimizer_created": False,
        "optimizer_step_called": False,
        "training_step_called": False,
        "trainer_fit_called": False,
        "checkpoint_saved": False,
        "model_saved": False,
        "original_source_files_modified": source_modified,
        "forbidden_artifacts_created": forbidden_artifacts,
        "all_checks_passed": all_checks_passed,
        "blocking_reasons": blockers,
    }
    return {
        "manifest": manifest,
        "loss_table_rows": all_level_results["loss_table_rows"],
        "per_level_results": all_level_results["per_level_results"],
        "report_sections": {
            "step11e_precondition": {"step11e_validated": step11e_validated},
            "pretrained_model_load": {
                "model_instantiated": load_bundle["model_instantiated"],
                "strict_load_success": load_bundle["strict_load_success"],
                "pretrained_weights_loaded": load_bundle["pretrained_weights_loaded"],
                "pretrained_base_integration_proven": load_bundle["pretrained_base_integration_proven"],
                "checkpoint_sha256": checkpoint.get("checkpoint_sha256", ""),
                "checkpoint_size_bytes": checkpoint.get("checkpoint_size_bytes", 0),
                "loaded_parameter_key_count": load_result.get("loaded_parameter_key_count", 0),
                "loaded_parameter_numel_total": load_result.get("loaded_parameter_numel_total", 0),
            },
            "synthetic_input_contract": {
                "synthetic_shape_smoke_only": True,
                "feature_semantics_known": False,
                "synthetic_mask_loss_adapter_used": True,
                "input_contract": load_bundle["input_contract"],
            },
            "mask_levels": all_level_results["per_level_results"],
            "decision": decision,
            "safety_boundary": {
                "backward_called": False,
                "optimizer_created": False,
                "optimizer_step_called": False,
                "training_step_called": False,
                "trainer_fit_called": False,
                "checkpoint_saved": False,
                "model_saved": False,
                "original_source_files_modified": source_modified,
                "forbidden_artifacts_created": forbidden_artifacts,
            },
        },
    }
