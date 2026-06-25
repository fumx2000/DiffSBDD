from __future__ import annotations

import csv
import json
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

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


STAGE = "diffsbdd_atomwise_loss_hook_prototype_without_behavior_change_v0"
PREVIOUS_STAGE = "diffsbdd_atomwise_loss_hook_design_without_behavior_change_v0"
SAFETY_FALSE_FIELDS = [
    "checkpoint_loaded",
    "checkpoint_saved",
    "training_step_called",
    "backward_called",
    "optimizer_step_executed",
    "trainer_fit_called",
    "training_executed",
    "real_finetune_executed",
    "checkpoint_written",
    "archive_created",
]
PROTECTED_SOURCE_FILES = [
    "equivariant_diffusion/en_diffusion.py",
    "equivariant_diffusion/conditional_model.py",
    "equivariant_diffusion/dynamics.py",
    "lightning_modules.py",
]


@dataclass
class AtomwiseProbeCapture:
    eps_t_lig: torch.Tensor | None = None
    net_out_lig: torch.Tensor | None = None
    ligand_mask_flat: torch.Tensor | None = None
    capture_events: list[str] = field(default_factory=list)
    capture_success: bool = False
    original_methods_restored: bool = False
    blocking_reasons: list[str] = field(default_factory=list)


def _rows_from_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _text_bool(value: Any) -> str:
    return str(value).strip().lower()


def validate_step10j_outputs_v0(
    report_csv: str | Path = DEFAULT_ROOT / "diffsbdd_atomwise_loss_hook_design_report.csv",
    manifest_json: str | Path = DEFAULT_ROOT / "diffsbdd_atomwise_loss_hook_design_preview_manifest.json",
) -> bool:
    report_path = Path(report_csv)
    manifest_path = Path(manifest_json)
    if not report_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("Step 10J atomwise hook design outputs are missing")
    rows = _rows_from_csv(report_path)
    if len(rows) != 1:
        raise ValueError(f"Step 10J report must contain exactly one row, found {len(rows)}")
    row = rows[0]
    expected_row_values = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "masked_loss_adapter_design_without_diffsbdd_modification_v0",
        "step10i_masked_loss_design_passed": "true",
        "source_inspection_status": "passed",
        "design_status": "ready",
        "recommended_hook_strategy": "optional_no_behavior_change_atomwise_probe_for_eps_t_lig_and_net_out_lig",
        "original_forward_return_should_change": "false",
        "checkpoint_compatibility_affected": "false",
        "can_preserve_default_behavior": "true",
        "can_capture_atomwise_noise_after_hook": "true",
        "can_compute_masked_x_loss_after_hook": "true",
        "can_compute_masked_h_loss_after_hook": "true",
        "recommended_next_step": "atomwise_loss_hook_prototype_without_behavior_change",
    }
    for key, expected in expected_row_values.items():
        if row.get(key) != expected:
            raise ValueError(f"Step 10J report invalid for {key}: {row.get(key)!r}")
    preferred = row.get("preferred_hook_point", "")
    if "eps_t_lig" not in preferred or "net_out_lig" not in preferred:
        raise ValueError("Step 10J preferred hook point does not include eps_t_lig and net_out_lig")
    for field_name in SAFETY_FALSE_FIELDS:
        if _text_bool(row.get(field_name, "")) != "false":
            raise ValueError(f"Step 10J report safety flag is not false: {field_name}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_manifest_values = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "masked_loss_adapter_design_without_diffsbdd_modification_v0",
        "step10i_masked_loss_design_passed": True,
        "design_status": "ready",
        "recommended_hook_strategy": "optional_no_behavior_change_atomwise_probe_for_eps_t_lig_and_net_out_lig",
        "original_forward_return_should_change": False,
        "checkpoint_compatibility_affected": False,
        "can_preserve_default_behavior": True,
        "can_capture_atomwise_noise_after_hook": True,
        "can_compute_masked_x_loss_after_hook": True,
        "can_compute_masked_h_loss_after_hook": True,
        "all_checks_passed": True,
        "recommended_next_step": "atomwise_loss_hook_prototype_without_behavior_change",
    }
    for key, expected in expected_manifest_values.items():
        if manifest.get(key) != expected:
            raise ValueError(f"Step 10J manifest invalid for {key}: {manifest.get(key)!r}")
    preferred_manifest = manifest.get("preferred_hook_point", "")
    if "eps_t_lig" not in preferred_manifest or "net_out_lig" not in preferred_manifest:
        raise ValueError("Step 10J manifest preferred hook point does not include required tensors")
    for field_name in SAFETY_FALSE_FIELDS:
        if manifest.get(field_name) is not False:
            raise ValueError(f"Step 10J manifest safety flag is not false: {field_name}")
    return True


@contextmanager
def atomwise_probe_context_v0(model: Any, capture: AtomwiseProbeCapture) -> Iterator[AtomwiseProbeCapture]:
    ddpm = getattr(model, "ddpm", None)
    if ddpm is None or not hasattr(ddpm, "noised_representation") or not hasattr(ddpm, "dynamics"):
        capture.blocking_reasons.append("model_ddpm_probe_targets_missing")
        yield capture
        return

    dynamics = ddpm.dynamics
    had_noised_attr = "noised_representation" in ddpm.__dict__
    old_noised_attr = ddpm.__dict__.get("noised_representation")
    old_noised_callable = ddpm.noised_representation
    had_forward_attr = "forward" in dynamics.__dict__
    old_forward_attr = dynamics.__dict__.get("forward")
    old_forward_callable = dynamics.forward

    def wrapped_noised_representation(*args: Any, **kwargs: Any) -> Any:
        output = old_noised_callable(*args, **kwargs)
        if len(args) >= 3 and torch.is_tensor(args[2]):
            capture.ligand_mask_flat = args[2]
            capture.capture_events.append("ligand_mask_flat_captured")
        if isinstance(output, tuple) and len(output) >= 3 and torch.is_tensor(output[2]):
            capture.eps_t_lig = output[2]
            capture.capture_events.append("eps_t_lig_captured")
        else:
            capture.blocking_reasons.append("eps_t_lig_not_found_in_noised_representation_output")
        return output

    def wrapped_dynamics_forward(*args: Any, **kwargs: Any) -> Any:
        output = old_forward_callable(*args, **kwargs)
        if isinstance(output, tuple) and output and torch.is_tensor(output[0]):
            capture.net_out_lig = output[0]
            capture.capture_events.append("net_out_lig_captured")
        elif torch.is_tensor(output):
            capture.net_out_lig = output
            capture.capture_events.append("net_out_lig_captured")
        else:
            capture.blocking_reasons.append("net_out_lig_not_found_in_dynamics_output")
        return output

    ddpm.noised_representation = wrapped_noised_representation
    dynamics.forward = wrapped_dynamics_forward
    try:
        yield capture
    finally:
        if had_noised_attr:
            ddpm.noised_representation = old_noised_attr
        elif "noised_representation" in ddpm.__dict__:
            delattr(ddpm, "noised_representation")
        if had_forward_attr:
            dynamics.forward = old_forward_attr
        elif "forward" in dynamics.__dict__:
            delattr(dynamics, "forward")
        restored_noised = had_noised_attr and ddpm.__dict__.get("noised_representation") is old_noised_attr
        restored_noised = restored_noised or (not had_noised_attr and "noised_representation" not in ddpm.__dict__)
        restored_forward = had_forward_attr and dynamics.__dict__.get("forward") is old_forward_attr
        restored_forward = restored_forward or (not had_forward_attr and "forward" not in dynamics.__dict__)
        capture.original_methods_restored = bool(restored_noised and restored_forward)
        capture.capture_success = bool(
            capture.eps_t_lig is not None
            and capture.net_out_lig is not None
            and capture.ligand_mask_flat is not None
        )


def _shape(value: torch.Tensor | None) -> list[int]:
    if value is None:
        return []
    return [int(dim) for dim in value.shape]


def _set_forward_seed(seed: int, device_info: dict[str, Any]) -> None:
    torch.manual_seed(seed)
    if device_info["resolved_device"].startswith("cuda") and torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def compare_forward_outputs_v0(output_a: Any, output_b: Any, rtol: float = 1e-5, atol: float = 1e-6) -> dict[str, Any]:
    output_type_equal = type(output_a).__name__ == type(output_b).__name__
    output0_a = output_a[0] if isinstance(output_a, tuple) and output_a else output_a
    output0_b = output_b[0] if isinstance(output_b, tuple) and output_b else output_b
    output0_shape_equal = bool(
        torch.is_tensor(output0_a)
        and torch.is_tensor(output0_b)
        and tuple(output0_a.shape) == tuple(output0_b.shape)
    )
    output0_allclose = bool(
        output0_shape_equal and torch.allclose(output0_a.detach(), output0_b.detach(), rtol=rtol, atol=atol)
    )
    info_a = output_a[1] if isinstance(output_a, tuple) and len(output_a) > 1 and isinstance(output_a[1], dict) else {}
    info_b = output_b[1] if isinstance(output_b, tuple) and len(output_b) > 1 and isinstance(output_b[1], dict) else {}
    output1_keys_equal = set(info_a) == set(info_b)
    output1_scalar_allclose = output1_keys_equal
    for key in sorted(set(info_a) & set(info_b)):
        value_a = info_a[key]
        value_b = info_b[key]
        if torch.is_tensor(value_a) and torch.is_tensor(value_b):
            output1_scalar_allclose = output1_scalar_allclose and bool(
                tuple(value_a.shape) == tuple(value_b.shape)
                and torch.allclose(value_a.detach(), value_b.detach(), rtol=rtol, atol=atol)
            )
        else:
            output1_scalar_allclose = output1_scalar_allclose and value_a == value_b
    return {
        "output_type_equal": output_type_equal,
        "output0_shape_equal": output0_shape_equal,
        "output0_allclose": output0_allclose,
        "output1_keys_equal": output1_keys_equal,
        "output1_scalar_allclose": bool(output1_scalar_allclose),
        "default_behavior_preserved": bool(
            output_type_equal and output0_shape_equal and output0_allclose and output1_keys_equal and output1_scalar_allclose
        ),
    }


def summarize_captured_atomwise_tensors_v0(capture: AtomwiseProbeCapture, metadata: dict[str, Any]) -> dict[str, Any]:
    eps = capture.eps_t_lig
    net = capture.net_out_lig
    ligand_mask = capture.ligand_mask_flat
    target_mask = metadata.get("ligand_target_mask_flat")
    if torch.is_tensor(target_mask) and eps is not None:
        target_mask = target_mask.to(device=eps.device, dtype=torch.bool)

    eps_captured = torch.is_tensor(eps)
    net_captured = torch.is_tensor(net)
    mask_available = torch.is_tensor(ligand_mask)
    target_available = torch.is_tensor(target_mask)
    residual = None
    residual_x = None
    residual_h = None
    if eps_captured and net_captured and eps.shape == net.shape:
        residual = eps - net
        residual_x = residual[:, :3]
        residual_h = residual[:, 3:]

    ligand_atom_count = int(ligand_mask.shape[0]) if mask_available else 0
    target_mask_shape = _shape(target_mask) if target_available else []
    target_mask_nonempty = bool(target_available and int(target_mask.sum().item()) > 0)
    target_mask_matches_ligand_atoms = bool(target_available and target_mask.shape == (ligand_atom_count,))
    tensor_first_dim_matches_ligand_atoms = bool(
        eps_captured
        and net_captured
        and mask_available
        and int(eps.shape[0]) == ligand_atom_count
        and int(net.shape[0]) == ligand_atom_count
    )
    residual_x_finite = bool(residual_x is not None and torch.isfinite(residual_x).all().item())
    residual_h_finite = bool(residual_h is not None and torch.isfinite(residual_h).all().item())
    return {
        "eps_t_lig_captured": bool(eps_captured),
        "net_out_lig_captured": bool(net_captured),
        "ligand_mask_flat_available": bool(mask_available),
        "eps_t_lig_shape": _shape(eps),
        "net_out_lig_shape": _shape(net),
        "ligand_mask_flat_shape": _shape(ligand_mask),
        "eps_t_lig_finite": bool(eps_captured and torch.isfinite(eps).all().item()),
        "net_out_lig_finite": bool(net_captured and torch.isfinite(net).all().item()),
        "net_out_lig_requires_grad": bool(net_captured and net.requires_grad),
        "eps_t_lig_requires_grad": bool(eps_captured and eps.requires_grad),
        "tensor_first_dim_matches_ligand_atoms": tensor_first_dim_matches_ligand_atoms,
        "target_mask_shape": target_mask_shape,
        "target_mask_nonempty": target_mask_nonempty,
        "target_mask_matches_ligand_atoms": target_mask_matches_ligand_atoms,
        "residual_shape": _shape(residual),
        "residual_x_shape": _shape(residual_x),
        "residual_h_shape": _shape(residual_h),
        "residual_x_finite": residual_x_finite,
        "residual_h_finite": residual_h_finite,
        "can_compute_masked_x_loss_later": bool(
            residual_x is not None
            and residual_x.shape[1] == 3
            and residual_x_finite
            and target_mask_nonempty
            and target_mask_matches_ligand_atoms
        ),
        "can_compute_masked_h_loss_later": bool(
            residual_h is not None
            and residual_h.ndim == 2
            and residual_h.shape[1] > 0
            and residual_h_finite
            and target_mask_nonempty
            and target_mask_matches_ligand_atoms
        ),
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


def _source_snapshots() -> dict[str, str]:
    return {
        rel_path: (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        for rel_path in PROTECTED_SOURCE_FILES
        if (REPO_ROOT / rel_path).is_file()
    }


def _sources_modified(before: dict[str, str]) -> bool:
    return any((REPO_ROOT / rel_path).read_text(encoding="utf-8") != text for rel_path, text in before.items())


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
        "forward_no_probe_called": False,
        "forward_probe_called": False,
        "forward_no_probe_success": False,
        "forward_probe_success": False,
        "default_behavior_preserved": False,
        "output_type_equal": False,
        "output0_shape_equal": False,
        "output0_allclose": False,
        "output1_keys_equal": False,
        "output1_scalar_allclose": False,
        "eps_t_lig_captured": False,
        "net_out_lig_captured": False,
        "ligand_mask_flat_available": False,
        "eps_t_lig_shape": [],
        "net_out_lig_shape": [],
        "ligand_mask_flat_shape": [],
        "eps_t_lig_finite": False,
        "net_out_lig_finite": False,
        "net_out_lig_requires_grad": False,
        "eps_t_lig_requires_grad": False,
        "tensor_first_dim_matches_ligand_atoms": False,
        "target_mask_shape": [],
        "target_mask_nonempty": False,
        "target_mask_matches_ligand_atoms": False,
        "residual_shape": [],
        "residual_x_shape": [],
        "residual_h_shape": [],
        "residual_x_finite": False,
        "residual_h_finite": False,
        "can_compute_masked_x_loss_later": False,
        "can_compute_masked_h_loss_later": False,
        "original_methods_restored": False,
        "original_source_files_modified": False,
        "smoke_status": "blocked",
        "forward_exception_type": "",
        "forward_exception_message": "",
        "blocking_reasons": [],
    }
    for key in SAFETY_FALSE_FIELDS:
        result[key] = False
    return result


def run_atomwise_loss_hook_prototype_v0(device: str = "auto", mask_level: str = "A_warhead_only") -> dict[str, Any]:
    device_info = resolve_diffsbdd_forward_device_v0(device)
    result = _base_result(device_info, mask_level)
    snapshots = _source_snapshots()
    try:
        validate_step10j_outputs_v0()
        candidate_inputs = _build_candidate_inputs(mask_level)
        result["batch_size"] = int(candidate_inputs["metadata"]["batch_size"])
        model, counts, reasons = _instantiate_model_for_forward(device_info, candidate_inputs)
        result.update(counts)
        if model is None:
            result["blocking_reasons"].extend(reasons)
            return result
        model.train()
        result["model_mode"] = "train"
        data_batch = move_diffsbdd_batch_to_device_v0(
            candidate_inputs["data_batch"], torch.device(device_info["resolved_device"])
        )
        metadata = candidate_inputs["metadata"]
        _set_forward_seed(3101, device_info)
        result["forward_no_probe_called"] = True
        output_no_probe = model(data_batch)
        result["forward_no_probe_success"] = True

        capture = AtomwiseProbeCapture()
        _set_forward_seed(3101, device_info)
        result["forward_probe_called"] = True
        with atomwise_probe_context_v0(model, capture):
            output_probe = model(data_batch)
        result["forward_probe_success"] = True
        result["original_methods_restored"] = capture.original_methods_restored

        result.update(compare_forward_outputs_v0(output_no_probe, output_probe))
        result.update(summarize_captured_atomwise_tensors_v0(capture, metadata))
        result["blocking_reasons"].extend(capture.blocking_reasons)

        blockers: list[str] = []
        required_true = [
            "forward_no_probe_success",
            "forward_probe_success",
            "default_behavior_preserved",
            "output0_allclose",
            "output1_scalar_allclose",
            "eps_t_lig_captured",
            "net_out_lig_captured",
            "ligand_mask_flat_available",
            "net_out_lig_requires_grad",
            "tensor_first_dim_matches_ligand_atoms",
            "target_mask_nonempty",
            "target_mask_matches_ligand_atoms",
            "residual_x_finite",
            "residual_h_finite",
            "can_compute_masked_x_loss_later",
            "can_compute_masked_h_loss_later",
            "original_methods_restored",
        ]
        for field_name in required_true:
            if result.get(field_name) is not True:
                blockers.append(f"{field_name}_not_true")
        if any(result[key] is not False for key in SAFETY_FALSE_FIELDS):
            blockers.append("safety_flag_not_false")
        result["original_source_files_modified"] = _sources_modified(snapshots)
        if result["original_source_files_modified"]:
            blockers.append("original_source_files_modified")
        result["blocking_reasons"].extend(blockers)
        result["blocking_reasons"] = sorted(set(result["blocking_reasons"]))
        result["smoke_status"] = "passed" if not result["blocking_reasons"] else "blocked"
    except Exception as exc:
        result["forward_exception_type"] = type(exc).__name__
        result["forward_exception_message"] = str(exc)
        result["blocking_reasons"].append(f"prototype_failed:{type(exc).__name__}")
        result["original_source_files_modified"] = _sources_modified(snapshots)
    finally:
        if device_info["resolved_device"].startswith("cuda") and torch.cuda.is_available():
            torch.cuda.empty_cache()
    return result
