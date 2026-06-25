from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

import torch
from torch.utils.data import DataLoader


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from covalent_ext.batch_adapter import adapt_covalent_batch_for_model_v0
from covalent_ext.diffsbdd_forward_shape_smoke import (
    DEFAULT_ROOT,
    _instantiate_model_for_forward,
    build_forward_candidate_inputs_v0,
    move_diffsbdd_batch_to_device_v0,
    resolve_diffsbdd_forward_device_v0,
)
from covalent_ext.diffsbdd_input_adapter import build_diffsbdd_like_input_from_covalent_v0
from covalent_ext.diffsbdd_shape_smoke import build_diffsbdd_batch_fields_v0, build_ligand_pocket_dicts_for_diffsbdd_v0
from covalent_ext.model_input_adapter import build_covalent_model_input_v0
from covalent_ext.npz_dataset import CovalentNPZDataset, covalent_npz_collate_fn


STAGE = "diffsbdd_backward_smoke_without_checkpoint_v0"
PREVIOUS_STAGE = "diffsbdd_forward_loss_semantics_review_without_backward_v0"
SAFETY_FALSE_FIELDS = [
    "checkpoint_loaded",
    "checkpoint_saved",
    "training_step_called",
    "optimizer_step_executed",
    "trainer_fit_called",
    "training_executed",
    "real_finetune_executed",
    "checkpoint_written",
]


def _rows_from_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_step10g_outputs_v0(
    report_csv: str | Path = DEFAULT_ROOT / "diffsbdd_forward_loss_semantics_report.csv",
    manifest_json: str | Path = DEFAULT_ROOT / "diffsbdd_forward_loss_semantics_preview_manifest.json",
) -> bool:
    report_path = Path(report_csv)
    manifest_path = Path(manifest_json)
    if not report_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("Step 10G forward loss semantics outputs are missing")
    rows = _rows_from_csv(report_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if len(rows) != 1 or rows[0].get("forward_loss_semantics_status") != "ready":
        raise ValueError("Step 10G report is not ready")
    expected = {
        "stage": PREVIOUS_STAGE,
        "output0_is_loss_like": True,
        "output0_is_per_sample_vector": True,
        "recommended_loss_reduction": "mean",
        "training_step_uses_forward_output0": True,
        "training_step_reduction_semantics": "nll.mean(0)",
        "can_do_backward_smoke_next": True,
        "checkpoint_loaded": False,
        "checkpoint_saved": False,
        "training_step_called": False,
        "backward_called": False,
        "optimizer_step_executed": False,
        "training_executed": False,
        "recommended_next_step": "real_diffsbdd_backward_smoke_without_checkpoint_then_masked_loss_adapter_design",
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise ValueError(f"Step 10G manifest invalid for {key}: {manifest.get(key)!r}")
    return True


def zero_model_grads_v0(model: torch.nn.Module) -> None:
    for parameter in model.parameters():
        parameter.grad = None


def collect_gradient_summary_v0(model: torch.nn.Module) -> dict[str, Any]:
    parameter_count = 0
    trainable_parameter_count = 0
    parameters_with_grad = 0
    trainable_parameters_with_grad = 0
    parameters_without_grad_count = 0
    grad_nan_count = 0
    grad_inf_count = 0
    total_norm_sq = 0.0
    max_grad_abs = 0.0
    finite_gradients = True
    nonzero_gradients = False
    top_grad_modules: list[dict[str, Any]] = []
    for name, parameter in model.named_parameters():
        parameter_count += int(parameter.numel())
        if parameter.requires_grad:
            trainable_parameter_count += int(parameter.numel())
        grad = parameter.grad
        if grad is None:
            parameters_without_grad_count += 1
            continue
        parameters_with_grad += 1
        if parameter.requires_grad:
            trainable_parameters_with_grad += 1
        detached = grad.detach()
        nan_count = int(torch.isnan(detached).sum().item())
        inf_count = int(torch.isinf(detached).sum().item())
        grad_nan_count += nan_count
        grad_inf_count += inf_count
        finite_gradients = finite_gradients and nan_count == 0 and inf_count == 0
        grad_norm = float(torch.linalg.vector_norm(detached).item())
        grad_abs = float(detached.abs().max().item()) if detached.numel() else 0.0
        total_norm_sq += grad_norm * grad_norm
        max_grad_abs = max(max_grad_abs, grad_abs)
        nonzero = grad_abs > 0.0
        nonzero_gradients = nonzero_gradients or nonzero
        top_grad_modules.append(
            {
                "name": name,
                "grad_norm": grad_norm,
                "max_grad_abs": grad_abs,
                "nonzero": nonzero,
            }
        )
    top_grad_modules = sorted(top_grad_modules, key=lambda item: item["grad_norm"], reverse=True)[:10]
    total_grad_norm = math.sqrt(total_norm_sq)
    return {
        "parameter_count": parameter_count,
        "trainable_parameter_count": trainable_parameter_count,
        "parameters_with_grad": parameters_with_grad,
        "trainable_parameters_with_grad": trainable_parameters_with_grad,
        "total_grad_norm": total_grad_norm,
        "max_grad_abs": max_grad_abs,
        "finite_gradients": bool(finite_gradients),
        "nonzero_gradients": bool(nonzero_gradients),
        "grad_nan_count": grad_nan_count,
        "grad_inf_count": grad_inf_count,
        "top_grad_modules": top_grad_modules,
        "parameters_without_grad_count": parameters_without_grad_count,
    }


def _build_candidate_inputs(mask_level: str) -> dict[str, Any]:
    dataset = CovalentNPZDataset(DEFAULT_ROOT / "sample_index.csv")
    loader = DataLoader(dataset, batch_size=3, shuffle=False, collate_fn=covalent_npz_collate_fn)
    batch = next(iter(loader))
    adapted = adapt_covalent_batch_for_model_v0(batch, mask_level=mask_level)
    model_input = build_covalent_model_input_v0(adapted)
    diffsbdd_like = build_diffsbdd_like_input_from_covalent_v0(model_input)
    batch_fields = build_diffsbdd_batch_fields_v0(diffsbdd_like)
    shape_smoke = build_ligand_pocket_dicts_for_diffsbdd_v0(batch_fields)
    return build_forward_candidate_inputs_v0(shape_smoke)


def _base_result(device_info: dict[str, Any], mask_level: str) -> dict[str, Any]:
    result = {
        **device_info,
        "mask_level": mask_level,
        "batch_size": 0,
        "model_class_name": "LigandPocketDDPM",
        "model_initialized": False,
        "model_mode": "train",
        "parameter_count": 0,
        "trainable_parameter_count": 0,
        "forward_called": False,
        "forward_success": False,
        "output0_shape": [],
        "output0_is_loss_like": True,
        "loss_reduction": "mean",
        "scalar_loss": "",
        "scalar_loss_finite": False,
        "backward_called": False,
        "backward_success": False,
        "parameters_with_grad": 0,
        "trainable_parameters_with_grad": 0,
        "total_grad_norm": 0.0,
        "max_grad_abs": 0.0,
        "finite_gradients": False,
        "nonzero_gradients": False,
        "grad_nan_count": 0,
        "grad_inf_count": 0,
        "top_grad_modules": [],
        "parameters_without_grad_count": 0,
        "backward_exception_type": "",
        "backward_exception_message": "",
        "smoke_status": "blocked",
        "blocking_reasons": [],
    }
    for key in SAFETY_FALSE_FIELDS:
        result[key] = False
    return result


def run_real_diffsbdd_backward_smoke_v0(device: str = "auto", mask_level: str = "A_warhead_only") -> dict[str, Any]:
    device_info = resolve_diffsbdd_forward_device_v0(device)
    result = _base_result(device_info, mask_level)
    try:
        validate_step10g_outputs_v0()
        torch.manual_seed(2301)
        if device_info["resolved_device"].startswith("cuda") and torch.cuda.is_available():
            torch.cuda.manual_seed_all(2301)
        candidate_inputs = _build_candidate_inputs(mask_level)
        result["batch_size"] = int(candidate_inputs["metadata"]["batch_size"])
        model, counts, reasons = _instantiate_model_for_forward(device_info, candidate_inputs)
        result.update(counts)
        if model is None:
            result["blocking_reasons"].extend(reasons)
            return result
        model.train()
        result["model_mode"] = "train"
        data_batch = move_diffsbdd_batch_to_device_v0(candidate_inputs["data_batch"], torch.device(device_info["resolved_device"]))
        zero_model_grads_v0(model)
        result["forward_called"] = True
        output = model(data_batch)
        result["forward_success"] = True
        output0 = output[0] if isinstance(output, tuple) and output else output
        if not torch.is_tensor(output0):
            result["blocking_reasons"].append("output0_not_tensor")
            return result
        result["output0_shape"] = [int(dim) for dim in output0.shape]
        scalar_loss = output0.mean()
        result["scalar_loss"] = float(scalar_loss.detach().item())
        result["scalar_loss_finite"] = bool(torch.isfinite(scalar_loss.detach()).item())
        if not result["scalar_loss_finite"]:
            result["blocking_reasons"].append("scalar_loss_not_finite")
            return result
        result["backward_called"] = True
        scalar_loss.backward()
        result["backward_success"] = True
        gradient_summary = collect_gradient_summary_v0(model)
        result.update(gradient_summary)
        blockers = []
        if result["parameters_with_grad"] <= 0:
            blockers.append("parameters_with_grad_zero")
        if result["trainable_parameters_with_grad"] <= 0:
            blockers.append("trainable_parameters_with_grad_zero")
        if not result["finite_gradients"]:
            blockers.append("gradients_not_finite")
        if not result["nonzero_gradients"]:
            blockers.append("gradients_all_zero")
        if result["total_grad_norm"] <= 0:
            blockers.append("total_grad_norm_not_positive")
        if result["max_grad_abs"] <= 0:
            blockers.append("max_grad_abs_not_positive")
        if result["grad_nan_count"] != 0:
            blockers.append("grad_nan_count_nonzero")
        if result["grad_inf_count"] != 0:
            blockers.append("grad_inf_count_nonzero")
        if any(result[key] is not False for key in SAFETY_FALSE_FIELDS):
            blockers.append("safety_flag_not_false")
        result["blocking_reasons"] = blockers
        result["smoke_status"] = "passed" if not blockers else "blocked"
    except Exception as exc:
        result["backward_exception_type"] = type(exc).__name__
        result["backward_exception_message"] = str(exc)
        result["blocking_reasons"].append(f"backward_smoke_failed:{type(exc).__name__}")
    finally:
        if device_info["resolved_device"].startswith("cuda") and torch.cuda.is_available():
            torch.cuda.empty_cache()
    return result
