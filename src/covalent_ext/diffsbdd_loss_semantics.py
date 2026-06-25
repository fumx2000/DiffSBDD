from __future__ import annotations

import ast
import csv
import inspect
import json
import sys
import textwrap
from pathlib import Path
from typing import Any

import torch
from torch.utils.data import DataLoader


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from covalent_ext.batch_adapter import adapt_covalent_batch_for_model_v0
from covalent_ext.diffsbdd_forward_mask_sweep import MASK_LEVELS
from covalent_ext.diffsbdd_forward_shape_smoke import (
    DEFAULT_ROOT,
    SAFETY_FALSE_FIELDS,
    _instantiate_model_for_forward,
    _inspect_forward_output,
    build_forward_candidate_inputs_v0,
    inspect_real_diffsbdd_forward_signature_v0,
    move_diffsbdd_batch_to_device_v0,
    resolve_diffsbdd_forward_device_v0,
)
from covalent_ext.diffsbdd_input_adapter import build_diffsbdd_like_input_from_covalent_v0
from covalent_ext.diffsbdd_shape_smoke import build_diffsbdd_batch_fields_v0, build_ligand_pocket_dicts_for_diffsbdd_v0
from covalent_ext.model_input_adapter import build_covalent_model_input_v0
from covalent_ext.npz_dataset import CovalentNPZDataset, covalent_npz_collate_fn


STAGE = "diffsbdd_forward_loss_semantics_review_without_backward_v0"
PREVIOUS_STAGE = "diffsbdd_forward_mask_level_sweep_without_checkpoint_v0"
SOURCE_FILES = [
    "lightning_modules.py",
    "equivariant_diffusion/en_diffusion.py",
    "equivariant_diffusion/dynamics.py",
    "equivariant_diffusion/conditional_model.py",
    "dataset.py",
    "train.py",
    "generate_ligands.py",
    "optimize.py",
    "src/covalent_ext/diffsbdd_forward_shape_smoke.py",
    "src/covalent_ext/diffsbdd_forward_mask_sweep.py",
]
MASK_IDENTIFIERS = [
    "lig_fixed",
    "generation_mask_flat",
    "ligand_target_mask_flat",
    "ligand_context_mask_flat",
    "lig_fixed.bool",
    "inpaint",
]


def _rows_from_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_step10f_outputs_v0(
    report_csv: str | Path = DEFAULT_ROOT / "diffsbdd_forward_mask_level_sweep_report.csv",
    manifest_json: str | Path = DEFAULT_ROOT / "diffsbdd_forward_mask_level_sweep_preview_manifest.json",
) -> bool:
    report_path = Path(report_csv)
    manifest_path = Path(manifest_json)
    if not report_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("Step 10F forward mask-level sweep outputs are missing")
    rows = _rows_from_csv(report_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if len(rows) != 4 or any(row.get("smoke_status") != "passed" for row in rows):
        raise ValueError("Step 10F report is not four passed rows")
    expected_false = {
        "checkpoint_loaded",
        "checkpoint_saved",
        "training_step_called",
        "backward_called",
        "optimizer_step_executed",
        "trainer_fit_called",
        "training_executed",
        "real_finetune_executed",
    }
    if manifest.get("stage") != PREVIOUS_STAGE:
        raise ValueError("Step 10F manifest stage is invalid")
    if manifest.get("all_mask_levels_passed") is not True or manifest.get("all_checks_passed") is not True:
        raise ValueError("Step 10F manifest did not pass all checks")
    for key in expected_false:
        if manifest.get(key) is not False:
            raise ValueError(f"Step 10F manifest invalid for {key}: {manifest.get(key)!r}")
    if manifest.get("recommended_next_step") != "diffsbdd_forward_loss_semantics_review_without_backward":
        raise ValueError("Step 10F recommended next step is not loss semantics review")
    return True


def _function_node(source: str, function_name: str) -> ast.FunctionDef | None:
    try:
        module = ast.parse(textwrap.dedent(source))
    except SyntaxError:
        return None
    for node in ast.walk(module):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return node
    return None


def _contains_name(node: ast.AST | None, names: set[str]) -> bool:
    if node is None:
        return False
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and child.id in names:
            return True
        if isinstance(child, ast.Constant) and isinstance(child.value, str) and child.value in names:
            return True
    return False


def _source_lines_for_function(obj: Any, patterns: list[str]) -> list[str]:
    lines, start = inspect.getsourcelines(obj)
    matches: list[str] = []
    for offset, line in enumerate(lines):
        stripped = line.strip()
        if any(pattern in stripped for pattern in patterns):
            matches.append(f"{inspect.getsourcefile(obj)}:{start + offset}:{stripped}")
    return matches


def _identifier_locations() -> dict[str, list[str]]:
    locations: dict[str, list[str]] = {identifier: [] for identifier in MASK_IDENTIFIERS}
    for rel_path in SOURCE_FILES:
        path = REPO_ROOT / rel_path
        if not path.is_file():
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for identifier in MASK_IDENTIFIERS:
                if identifier in line:
                    locations[identifier].append(f"{rel_path}:{number}:{line.strip()}")
    return locations


def inspect_diffsbdd_loss_semantics_sources_v0() -> dict[str, Any]:
    from equivariant_diffusion.conditional_model import ConditionalDDPM
    from equivariant_diffusion.en_diffusion import EnVariationalDiffusion
    from lightning_modules import LigandPocketDDPM

    inspected_source_files = [rel_path for rel_path in SOURCE_FILES if (REPO_ROOT / rel_path).is_file()]
    lightning_source = (REPO_ROOT / "lightning_modules.py").read_text(encoding="utf-8")
    en_source = (REPO_ROOT / "equivariant_diffusion" / "en_diffusion.py").read_text(encoding="utf-8")
    conditional_source = (REPO_ROOT / "equivariant_diffusion" / "conditional_model.py").read_text(encoding="utf-8")
    forward_node = _function_node(inspect.getsource(LigandPocketDDPM.forward), "forward")
    training_node = _function_node(inspect.getsource(LigandPocketDDPM.training_step), "training_step")
    en_forward_node = _function_node(inspect.getsource(EnVariationalDiffusion.forward), "forward")
    conditional_forward_node = _function_node(inspect.getsource(ConditionalDDPM.forward), "forward")
    identifier_locations = _identifier_locations()

    forward_mask_names = {"lig_fixed", "generation_mask_flat", "ligand_target_mask_flat", "ligand_context_mask_flat"}
    training_mask_names = set(forward_mask_names)
    sampling_locations = {
        key: values
        for key, values in identifier_locations.items()
        if key == "lig_fixed" and any(("inpaint" in value or "conditional_model.py" in value or "en_diffusion.py" in value) for value in values)
    }
    output1_semantics = {
        "error_t_lig": "per-sample ligand denoising squared error, reduced to scalar diagnostic in LigandPocketDDPM.forward",
        "error_t_pocket": "per-sample pocket denoising squared error, reduced to scalar diagnostic in LigandPocketDDPM.forward",
        "SNR_weight": "signal-to-noise weighting term used for the VLB/evaluation loss_t term",
        "loss_0": "mean zero-timestep reconstruction contribution assembled from x/h and constants",
        "kl_prior": "mean KL-to-prior contribution",
        "delta_log_px": "mean normalization log-volume correction",
        "neg_log_const_0": "mean negative Gaussian normalization constant for p(x|z0)",
        "log_pN": "mean ligand/pocket size prior log probability",
        "eps_hat_lig_x": "mean absolute predicted ligand coordinate noise diagnostic",
        "eps_hat_lig_h": "mean absolute predicted ligand feature noise diagnostic",
    }
    return {
        "inspected_source_files": inspected_source_files,
        "forward_signature": str(inspect.signature(LigandPocketDDPM.forward)),
        "training_step_signature": str(inspect.signature(LigandPocketDDPM.training_step)),
        "en_diffusion_forward_signature": str(inspect.signature(EnVariationalDiffusion.forward)),
        "conditional_forward_signature": str(inspect.signature(ConditionalDDPM.forward)),
        "located_forward_return_lines": _source_lines_for_function(
            LigandPocketDDPM.forward,
            ["self.ddpm", "nll =", "info['", "return nll"],
        ),
        "located_training_step_loss_lines": _source_lines_for_function(
            LigandPocketDDPM.training_step,
            ["self.forward", "loss = nll.mean", "info['loss']", "return info"],
        ),
        "located_en_diffusion_loss_lines": _source_lines_for_function(
            EnVariationalDiffusion.forward,
            ["Computes the loss", "error_t_lig", "loss_0", "kl_prior", "log_pN", "loss_terms", "return"],
        ),
        "located_conditional_loss_lines": _source_lines_for_function(
            ConditionalDDPM.forward,
            ["Computes the loss", "error_t_lig", "loss_0", "kl_prior", "log_pN", "loss_terms", "return"],
        ),
        "output0_semantics_candidate": "LigandPocketDDPM.forward returns nll as output.0; training_step reduces it with nll.mean(0) as loss.",
        "output1_key_semantics_candidates": output1_semantics,
        "mask_related_identifiers_found": identifier_locations,
        "mask_related_identifiers_consumed_by_forward": {
            "LigandPocketDDPM.forward": _contains_name(forward_node, forward_mask_names),
            "EnVariationalDiffusion.forward": _contains_name(en_forward_node, forward_mask_names),
            "ConditionalDDPM.forward": _contains_name(conditional_forward_node, forward_mask_names),
        },
        "mask_related_identifiers_consumed_by_training_step": {
            "LigandPocketDDPM.training_step": _contains_name(training_node, training_mask_names),
        },
        "mask_related_identifiers_consumed_by_sampling_or_inpainting": sampling_locations,
        "lig_fixed_consumed_by_forward_ast": _contains_name(forward_node, {"lig_fixed"}),
        "generation_mask_consumed_by_forward_ast": _contains_name(forward_node, {"generation_mask_flat"}),
        "target_mask_consumed_by_forward_ast": _contains_name(forward_node, {"ligand_target_mask_flat"}),
        "context_mask_consumed_by_forward_ast": _contains_name(forward_node, {"ligand_context_mask_flat"}),
        "forward_source_mentions_lig_fixed": "lig_fixed" in inspect.getsource(LigandPocketDDPM.forward),
        "training_step_uses_forward_output0": "nll, info = self.forward(data)" in inspect.getsource(LigandPocketDDPM.training_step)
        and "loss = nll.mean(0)" in inspect.getsource(LigandPocketDDPM.training_step),
        "training_step_reduction_semantics": "nll.mean(0)",
        "notes": [
            "LigandPocketDDPM.get_ligand_and_pocket builds ligand/pocket dicts from coords, one_hot, size, and mask only.",
            "The covalent adapter passes lig_fixed in data_batch, but LigandPocketDDPM.forward does not request it from data.",
            "Original inpainting paths consume lig_fixed; training forward does not appear mask-aware.",
        ],
    }


def _tensor_stats(tensor: torch.Tensor) -> dict[str, Any]:
    detached = tensor.detach()
    finite = bool(torch.isfinite(detached).all().item()) if (torch.is_floating_point(detached) or torch.is_complex(detached)) else True
    stats: dict[str, Any] = {
        "shape": [int(dim) for dim in detached.shape],
        "dtype": str(detached.dtype),
        "finite": finite,
    }
    if detached.numel() and torch.is_floating_point(detached):
        stats.update(
            {
                "mean": float(detached.mean().item()),
                "min": float(detached.min().item()),
                "max": float(detached.max().item()),
            }
        )
    return stats


def _collect_output_probe(value: Any) -> dict[str, Any]:
    output_info = _inspect_forward_output(value)
    output0 = value[0] if isinstance(value, tuple) and value else None
    output1 = value[1] if isinstance(value, tuple) and len(value) > 1 and isinstance(value[1], dict) else {}
    output1_stats: dict[str, dict[str, Any]] = {}
    output1_scalar_values: dict[str, float] = {}
    for key, item in output1.items():
        if torch.is_tensor(item):
            stats = _tensor_stats(item)
            output1_stats[str(key)] = stats
            if item.detach().numel() == 1 and torch.is_floating_point(item.detach()) and stats["finite"]:
                output1_scalar_values[str(key)] = float(item.detach().item())
    return {
        "output_type": output_info["output_type"],
        "output0": _tensor_stats(output0) if torch.is_tensor(output0) else {},
        "output1_keys": sorted(str(key) for key in output1.keys()),
        "output1_shapes": {key: stats["shape"] for key, stats in output1_stats.items()},
        "output1_finite_by_key": {key: stats["finite"] for key, stats in output1_stats.items()},
        "output1_scalar_values_if_safe": output1_scalar_values,
        "tensor_output_shapes": output_info["tensor_output_shapes"],
        "finite_tensor_outputs": output_info["finite_tensor_outputs"],
        "scalar_loss_like_output_finite": output_info["scalar_loss_like_output_finite"],
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


def run_forward_output_semantics_probe_v0(device: str = "auto") -> dict[str, Any]:
    step10f_passed = validate_step10f_outputs_v0()
    device_info = resolve_diffsbdd_forward_device_v0(device)
    rows: list[dict[str, Any]] = []
    for index, mask_level in enumerate(MASK_LEVELS):
        row: dict[str, Any] = {
            **device_info,
            "mask_level": mask_level,
            "forward_success": False,
            "forward_exception_type": "",
            "forward_exception_message": "",
            "checkpoint_loaded": False,
            "checkpoint_saved": False,
            "training_step_called": False,
            "backward_called": False,
            "optimizer_step_executed": False,
            "trainer_fit_called": False,
            "training_executed": False,
            "real_finetune_executed": False,
        }
        try:
            torch.manual_seed(1701 + index)
            if device_info["resolved_device"].startswith("cuda") and torch.cuda.is_available():
                torch.cuda.manual_seed_all(1701 + index)
            candidate_inputs = _build_candidate_inputs(mask_level)
            data_batch = candidate_inputs["data_batch"]
            metadata = candidate_inputs["metadata"]
            row["batch_size"] = int(metadata["batch_size"])
            row["target_atom_count"] = int(metadata["ligand_target_mask_flat"].sum().item())
            row["context_atom_count"] = int(metadata["ligand_context_mask_flat"].sum().item())
            model, counts, reasons = _instantiate_model_for_forward(device_info, candidate_inputs)
            row.update(counts)
            row["blocking_reasons"] = reasons
            if model is None:
                rows.append(row)
                continue
            row.update(inspect_real_diffsbdd_forward_signature_v0(model))
            moved_data_batch = move_diffsbdd_batch_to_device_v0(data_batch, torch.device(device_info["resolved_device"]))
            with torch.no_grad():
                output = model(moved_data_batch)
            probe = _collect_output_probe(output)
            row.update(probe)
            row["output0_shape"] = probe["output0"].get("shape", [])
            row["output0_dtype"] = probe["output0"].get("dtype", "")
            row["output0_finite"] = bool(probe["output0"].get("finite", False))
            row["output0_mean"] = probe["output0"].get("mean")
            row["output0_min"] = probe["output0"].get("min")
            row["output0_max"] = probe["output0"].get("max")
            row["forward_success"] = True
            row["blocking_reasons"] = []
        except Exception as exc:
            row["forward_exception_type"] = type(exc).__name__
            row["forward_exception_message"] = str(exc)
            row["blocking_reasons"] = [f"forward_probe_failed:{type(exc).__name__}"]
        finally:
            if device_info["resolved_device"].startswith("cuda") and torch.cuda.is_available():
                torch.cuda.empty_cache()
        rows.append(row)
    return {
        "stage": STAGE,
        "previous_stage": PREVIOUS_STAGE,
        "step10f_forward_sweep_passed": step10f_passed,
        "requested_device": device_info["requested_device"],
        "resolved_device": device_info["resolved_device"],
        "cuda_available": device_info["cuda_available"],
        "cuda_device_count": device_info["cuda_device_count"],
        "cuda_device_name": device_info["cuda_device_name"],
        "mask_levels_checked": len(rows),
        "rows": rows,
        "probe_status": "passed" if len(rows) == len(MASK_LEVELS) and all(row["forward_success"] for row in rows) else "blocked",
        "output0_shape_by_mask_level": {row["mask_level"]: row.get("output0_shape", []) for row in rows},
        "output0_finite_by_mask_level": {row["mask_level"]: row.get("output0_finite", False) for row in rows},
        "output0_mean_by_mask_level": {row["mask_level"]: row.get("output0_mean") for row in rows},
        "output1_keys_by_mask_level": {row["mask_level"]: row.get("output1_keys", []) for row in rows},
        "output1_finite_by_mask_level": {row["mask_level"]: row.get("output1_finite_by_key", {}) for row in rows},
        "output1_scalar_values_by_mask_level": {row["mask_level"]: row.get("output1_scalar_values_if_safe", {}) for row in rows},
        "tensor_output_shapes_by_mask_level": {row["mask_level"]: row.get("tensor_output_shapes", {}) for row in rows},
        "checkpoint_loaded": False,
        "checkpoint_saved": False,
        "training_step_called": False,
        "backward_called": False,
        "optimizer_step_executed": False,
        "trainer_fit_called": False,
        "training_executed": False,
        "real_finetune_executed": False,
        "archive_created": False,
    }


def _all_output1_finite(probe_info: dict[str, Any]) -> bool:
    for finite_by_key in probe_info["output1_finite_by_mask_level"].values():
        if not finite_by_key or not all(bool(value) for value in finite_by_key.values()):
            return False
    return True


def assess_forward_loss_training_readiness_v0(source_info: dict[str, Any], probe_info: dict[str, Any]) -> dict[str, Any]:
    output0_shapes = probe_info["output0_shape_by_mask_level"]
    output0_finite = probe_info["output0_finite_by_mask_level"]
    output0_is_per_sample_vector = all(shape == [3] for shape in output0_shapes.values())
    output0_is_loss_like = bool(source_info["training_step_uses_forward_output0"] and output0_is_per_sample_vector)
    output1_keys = sorted(set().union(*(set(keys) for keys in probe_info["output1_keys_by_mask_level"].values())))
    output1_all_finite = _all_output1_finite(probe_info)
    output1_is_diagnostics = bool(output1_keys and output1_all_finite)
    lig_fixed_forward = bool(source_info["lig_fixed_consumed_by_forward_ast"])
    generation_forward = bool(source_info["generation_mask_consumed_by_forward_ast"])
    target_forward = bool(source_info["target_mask_consumed_by_forward_ast"])
    context_forward = bool(source_info["context_mask_consumed_by_forward_ast"])
    any_mask_forward = lig_fixed_forward or generation_forward or target_forward or context_forward
    sampling_has_lig_fixed = bool(source_info["mask_related_identifiers_consumed_by_sampling_or_inpainting"].get("lig_fixed"))
    if any_mask_forward:
        mask_status = "consumed_by_forward"
    elif sampling_has_lig_fixed:
        mask_status = "consumed_by_sampling_only"
    else:
        mask_status = "not_consumed"
    blockers: list[str] = []
    if not output0_is_loss_like:
        blockers.append("output0_loss_semantics_unclear")
    if not all(output0_finite.values()):
        blockers.append("output0_not_finite")
    can_do_backward = output0_is_loss_like and all(output0_finite.values()) and probe_info["probe_status"] == "passed"
    must_modify = not any_mask_forward
    if output0_is_loss_like:
        status = "ready"
    else:
        status = "uncertain"
    if can_do_backward and must_modify:
        next_step = "real_diffsbdd_backward_smoke_without_checkpoint_then_masked_loss_adapter_design"
    elif can_do_backward:
        next_step = "real_diffsbdd_backward_smoke_without_checkpoint"
    else:
        next_step = "manual_loss_semantics_review"
    return {
        "forward_loss_semantics_status": status,
        "output0_is_loss_like": output0_is_loss_like,
        "output0_is_per_sample_vector": output0_is_per_sample_vector,
        "recommended_loss_reduction": "mean" if output0_is_loss_like else "uncertain",
        "training_step_uses_forward_output0": bool(source_info["training_step_uses_forward_output0"]),
        "training_step_reduction_semantics": source_info["training_step_reduction_semantics"],
        "output1_is_diagnostics": output1_is_diagnostics,
        "output1_keys": output1_keys,
        "mask_consumption_status": mask_status,
        "lig_fixed_consumed_by_forward": lig_fixed_forward,
        "generation_mask_consumed_by_forward": generation_forward,
        "target_mask_consumed_by_forward": target_forward,
        "context_mask_consumed_by_forward": context_forward,
        "current_forward_is_mask_aware": any_mask_forward,
        "current_forward_is_full_ligand_objective": not any_mask_forward,
        "can_do_backward_smoke_next": can_do_backward,
        "must_modify_loss_for_masked_training": must_modify,
        "recommended_next_step": next_step,
        "blocking_reasons": blockers,
        "notes": [
            "Backward smoke can validate the original DiffSBDD loss pathway, but it will not prove masked covalent loss semantics.",
            "A masked loss adapter/design is still needed before claiming target-mask-aware covalent training.",
        ],
    }
