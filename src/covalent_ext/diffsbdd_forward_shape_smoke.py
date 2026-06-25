from __future__ import annotations

import inspect
import importlib
import json
import sys
from pathlib import Path
from typing import Any

import torch
from torch.utils.data import DataLoader


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from covalent_ext.batch_adapter import adapt_covalent_batch_for_model_v0
from covalent_ext.diffsbdd_input_adapter import build_diffsbdd_like_input_from_covalent_v0
from covalent_ext.diffsbdd_model_instantiation import (
    MODEL_CLASS_NAME,
    MODEL_MODULE_NAME,
    _constructor_kwargs,
    build_minimal_diffsbdd_instantiation_config_v0,
)
from covalent_ext.diffsbdd_shape_smoke import build_diffsbdd_batch_fields_v0, build_ligand_pocket_dicts_for_diffsbdd_v0
from covalent_ext.model_input_adapter import build_covalent_model_input_v0
from covalent_ext.npz_dataset import CovalentNPZDataset, covalent_npz_collate_fn


DEFAULT_ROOT = Path("data/derived/covalent_small/training_tensor_materialized_v0")
SAFETY_FALSE_FIELDS = [
    "checkpoint_loaded",
    "checkpoint_saved",
    "training_step_called",
    "backward_called",
    "optimizer_step_executed",
    "trainer_fit_called",
    "training_executed",
    "real_finetune_executed",
]


def resolve_diffsbdd_forward_device_v0(device: str = "auto") -> dict[str, Any]:
    cuda_available = bool(torch.cuda.is_available())
    cuda_device_count = int(torch.cuda.device_count()) if cuda_available else 0
    cuda_device_name = torch.cuda.get_device_name(0) if cuda_available and cuda_device_count > 0 else ""
    fallback_reason = ""
    if device == "auto":
        resolved = "cuda:0" if cuda_available else "cpu"
        if not cuda_available:
            fallback_reason = "cuda_unavailable"
    elif device.startswith("cuda"):
        if cuda_available:
            resolved = device if ":" in device else "cuda:0"
        else:
            resolved = "cpu"
            fallback_reason = "requested_cuda_but_cuda_unavailable"
    elif device == "cpu":
        resolved = "cpu"
    else:
        resolved = "cpu"
        fallback_reason = f"unsupported_device:{device}"
    return {
        "requested_device": device,
        "resolved_device": resolved,
        "cuda_available": cuda_available,
        "cuda_device_count": cuda_device_count,
        "cuda_device_name": cuda_device_name,
        "device_fallback_reason": fallback_reason,
    }


def move_diffsbdd_batch_to_device_v0(batch_like: Any, device: torch.device) -> Any:
    if torch.is_tensor(batch_like):
        return batch_like.to(device)
    if isinstance(batch_like, dict):
        return {key: move_diffsbdd_batch_to_device_v0(value, device) for key, value in batch_like.items()}
    if isinstance(batch_like, list):
        return [move_diffsbdd_batch_to_device_v0(value, device) for value in batch_like]
    if isinstance(batch_like, tuple):
        return tuple(move_diffsbdd_batch_to_device_v0(value, device) for value in batch_like)
    return batch_like


def build_forward_candidate_inputs_v0(shape_smoke: dict[str, Any]) -> dict[str, Any]:
    ligand = shape_smoke["ligand"]
    pocket = shape_smoke["pocket"]
    data_batch = {
        "lig_coords": ligand["x"],
        "lig_one_hot": ligand["one_hot"],
        "lig_mask": ligand["mask"],
        "pocket_coords": pocket["x"],
        "pocket_one_hot": pocket["one_hot"],
        "pocket_mask": pocket["mask"],
        "num_lig_atoms": ligand["size"],
        "num_pocket_nodes": pocket["size"],
        "lig_fixed": shape_smoke["lig_fixed"],
    }
    return {
        "data_batch": data_batch,
        "ligand": {
            "x": ligand["x"],
            "one_hot": ligand["one_hot"],
            "size": ligand["size"],
            "mask": ligand["mask"],
        },
        "pocket": {
            "x": pocket["x"],
            "one_hot": pocket["one_hot"],
            "size": pocket["size"],
            "mask": pocket["mask"],
        },
        "metadata": {
            "sample_id": list(shape_smoke["sample_id"]),
            "mask_level": shape_smoke["mask_level"],
            "batch_size": int(shape_smoke["batch_size"]),
            "generation_mask_flat": shape_smoke["generation_mask_flat"],
            "ligand_context_mask_flat": shape_smoke["ligand_context_mask_flat"],
            "ligand_target_mask_flat": shape_smoke["ligand_target_mask_flat"],
        },
    }


def inspect_real_diffsbdd_forward_signature_v0(model: Any) -> dict[str, Any]:
    forward_signature = str(inspect.signature(model.forward))
    get_ligand_signature = str(inspect.signature(model.get_ligand_and_pocket))
    selected = "LigandPocketDDPM.forward(data_batch)"
    notes = [
        "LigandPocketDDPM.forward accepts a single data argument and internally calls get_ligand_and_pocket.",
        "The selected call style passes ProcessedLigandPocketDataset-like flattened batch fields.",
    ]
    return {
        "forward_signature": forward_signature,
        "get_ligand_and_pocket_signature": get_ligand_signature,
        "selected_forward_call_style": selected,
        "notes": notes,
    }


def _validate_step10d_outputs() -> bool:
    report = DEFAULT_ROOT / "diffsbdd_model_instantiation_dry_run_report.csv"
    manifest = DEFAULT_ROOT / "diffsbdd_model_instantiation_dry_run_preview_manifest.json"
    if not report.is_file() or not manifest.is_file():
        raise FileNotFoundError("Step 10D model instantiation dry-run outputs are missing")
    import csv

    with report.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if len(rows) != 1 or rows[0].get("smoke_status") != "passed":
        raise ValueError("Step 10D report is not passed")
    required = {
        "model_initialized": True,
        "checkpoint_loaded": False,
        "checkpoint_saved": False,
        "forward_called": False,
        "training_step_called": False,
        "training_executed": False,
    }
    for key, expected in required.items():
        if data.get(key) is not expected:
            raise ValueError(f"Step 10D manifest invalid for {key}: {data.get(key)!r}")
    if data.get("recommended_next_step") != "diffsbdd_single_batch_forward_shape_smoke_without_checkpoint":
        raise ValueError("Step 10D recommended next step is not forward shape smoke")
    return True


def _histogram_for_forward_sizes(num_lig_atoms: torch.Tensor, num_pocket_nodes: torch.Tensor) -> list[list[float]]:
    max_lig = int(num_lig_atoms.max().item())
    max_pocket = int(num_pocket_nodes.max().item())
    histogram = [[0.0 for _ in range(max_pocket + 1)] for _ in range(max_lig + 1)]
    for lig, pocket in zip(num_lig_atoms.detach().cpu().tolist(), num_pocket_nodes.detach().cpu().tolist()):
        histogram[int(lig)][int(pocket)] = 1.0
    return histogram


def _instantiate_model_for_forward(device_info: dict[str, Any], candidate_inputs: dict[str, Any]) -> tuple[Any | None, dict[str, Any], list[str]]:
    config = build_minimal_diffsbdd_instantiation_config_v0()
    reasons = list(config["blocking_reasons"])
    if config["config_status"] != "ready":
        return None, {"parameter_count": 0, "trainable_parameter_count": 0, "model_initialized": False}, reasons or ["config_not_ready"]
    config_dict = dict(config["config_dict"])
    config_dict["egnn_params"] = dict(config_dict["egnn_params"], device=device_info["resolved_device"])
    data_batch = candidate_inputs["data_batch"]
    config_dict["node_histogram"] = _histogram_for_forward_sizes(data_batch["num_lig_atoms"], data_batch["num_pocket_nodes"])
    try:
        module = importlib.import_module(MODEL_MODULE_NAME)
        model_class = getattr(module, MODEL_CLASS_NAME)
        model = model_class(**_constructor_kwargs(config_dict))
        model = model.to(torch.device(device_info["resolved_device"]))
        model.eval()
        counts = {
            "model_initialized": True,
            "parameter_count": int(sum(parameter.numel() for parameter in model.parameters())),
            "trainable_parameter_count": int(sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)),
        }
        return model, counts, []
    except Exception as exc:
        return None, {"parameter_count": 0, "trainable_parameter_count": 0, "model_initialized": False}, [f"model_initialization_failed:{type(exc).__name__}:{exc}"]


def _shape(value: torch.Tensor) -> list[int]:
    return [int(dim) for dim in value.shape]


def _collect_tensors(value: Any, prefix: str = "output") -> dict[str, torch.Tensor]:
    if torch.is_tensor(value):
        return {prefix: value}
    if isinstance(value, dict):
        tensors: dict[str, torch.Tensor] = {}
        for key, child in value.items():
            tensors.update(_collect_tensors(child, f"{prefix}.{key}"))
        return tensors
    if isinstance(value, (list, tuple)):
        tensors = {}
        for index, child in enumerate(value):
            tensors.update(_collect_tensors(child, f"{prefix}.{index}"))
        return tensors
    return {}


def _output_keys(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [str(key) for key in value.keys()]
    if isinstance(value, (list, tuple)):
        return [str(index) for index in range(len(value))]
    return []


def _inspect_forward_output(value: Any) -> dict[str, Any]:
    tensors = _collect_tensors(value)
    finite = True
    shapes: dict[str, list[int]] = {}
    for name, tensor in tensors.items():
        shapes[name] = _shape(tensor)
        if torch.is_floating_point(tensor) or torch.is_complex(tensor):
            finite = finite and bool(torch.isfinite(tensor).all().item())
    first_tensor = next(iter(tensors.values()), None)
    scalar_loss_like_finite = True
    if first_tensor is not None and (torch.is_floating_point(first_tensor) or torch.is_complex(first_tensor)):
        scalar_loss_like_finite = bool(torch.isfinite(first_tensor).all().item())
    return {
        "output_type": type(value).__name__,
        "output_keys": _output_keys(value),
        "tensor_output_shapes": shapes,
        "finite_tensor_outputs": finite,
        "scalar_loss_like_output_finite": scalar_loss_like_finite,
    }


def _base_result(device_info: dict[str, Any], mask_level: str) -> dict[str, Any]:
    result = {
        **device_info,
        "mask_level": mask_level,
        "batch_size": 0,
        "model_class_name": MODEL_CLASS_NAME,
        "model_initialized": False,
        "parameter_count": 0,
        "trainable_parameter_count": 0,
        "forward_signature": "",
        "get_ligand_and_pocket_signature": "",
        "selected_forward_call_style": "",
        "ligand_x_shape": [],
        "ligand_one_hot_shape": [],
        "pocket_x_shape": [],
        "pocket_one_hot_shape": [],
        "ligand_mask_shape": [],
        "pocket_mask_shape": [],
        "target_atom_count": 0,
        "context_atom_count": 0,
        "forward_called": False,
        "forward_success": False,
        "output_type": "",
        "output_keys": [],
        "tensor_output_shapes": {},
        "finite_tensor_outputs": False,
        "scalar_loss_like_output_finite": False,
        "forward_exception_type": "",
        "forward_exception_message": "",
        "smoke_status": "blocked",
        "blocking_reasons": [],
    }
    for key in SAFETY_FALSE_FIELDS:
        result[key] = False
    return result


def run_diffsbdd_single_batch_forward_shape_smoke_v0(device: str = "auto", mask_level: str = "A_warhead_only") -> dict[str, Any]:
    device_info = resolve_diffsbdd_forward_device_v0(device)
    result = _base_result(device_info, mask_level)
    try:
        _validate_step10d_outputs()
        dataset = CovalentNPZDataset(DEFAULT_ROOT / "sample_index.csv")
        loader = DataLoader(dataset, batch_size=3, shuffle=False, collate_fn=covalent_npz_collate_fn)
        batch = next(iter(loader))
        adapted = adapt_covalent_batch_for_model_v0(batch, mask_level=mask_level)
        model_input = build_covalent_model_input_v0(adapted)
        diffsbdd_like = build_diffsbdd_like_input_from_covalent_v0(model_input)
        batch_fields = build_diffsbdd_batch_fields_v0(diffsbdd_like)
        shape_smoke = build_ligand_pocket_dicts_for_diffsbdd_v0(batch_fields)
        candidate_inputs = build_forward_candidate_inputs_v0(shape_smoke)
        data_batch = candidate_inputs["data_batch"]
        ligand = candidate_inputs["ligand"]
        pocket = candidate_inputs["pocket"]
        metadata = candidate_inputs["metadata"]
        result.update(
            {
                "batch_size": int(metadata["batch_size"]),
                "ligand_x_shape": _shape(ligand["x"]),
                "ligand_one_hot_shape": _shape(ligand["one_hot"]),
                "pocket_x_shape": _shape(pocket["x"]),
                "pocket_one_hot_shape": _shape(pocket["one_hot"]),
                "ligand_mask_shape": _shape(ligand["mask"]),
                "pocket_mask_shape": _shape(pocket["mask"]),
                "target_atom_count": int(metadata["ligand_target_mask_flat"].sum().item()),
                "context_atom_count": int(metadata["ligand_context_mask_flat"].sum().item()),
            }
        )
        model, counts, model_reasons = _instantiate_model_for_forward(device_info, candidate_inputs)
        result.update(counts)
        if model is None:
            result["blocking_reasons"].extend(model_reasons)
            return result
        signature_info = inspect_real_diffsbdd_forward_signature_v0(model)
        result.update(signature_info)
        moved_data_batch = move_diffsbdd_batch_to_device_v0(data_batch, torch.device(device_info["resolved_device"]))
        try:
            with torch.no_grad():
                result["forward_called"] = True
                output = model(moved_data_batch)
            output_info = _inspect_forward_output(output)
            result.update(output_info)
            result["forward_success"] = True
        except Exception as exc:
            result["forward_called"] = True
            result["forward_success"] = False
            result["forward_exception_type"] = type(exc).__name__
            result["forward_exception_message"] = str(exc)
            result["blocking_reasons"].append(f"forward_failed:{type(exc).__name__}")
        finally:
            if device_info["resolved_device"].startswith("cuda") and torch.cuda.is_available():
                torch.cuda.empty_cache()
        if (
            result["model_initialized"]
            and result["forward_called"]
            and result["forward_success"]
            and result["finite_tensor_outputs"]
            and all(result[key] is False for key in SAFETY_FALSE_FIELDS)
        ):
            result["smoke_status"] = "passed"
            result["blocking_reasons"] = []
        elif not result["blocking_reasons"]:
            result["blocking_reasons"].append("forward_shape_smoke_checks_failed")
    except Exception as exc:
        result["forward_exception_type"] = type(exc).__name__
        result["forward_exception_message"] = str(exc)
        result["blocking_reasons"].append(f"setup_failed:{type(exc).__name__}")
    return result
