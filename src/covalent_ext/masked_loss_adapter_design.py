from __future__ import annotations

import csv
import inspect
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


DEFAULT_ROOT = Path("data/derived/covalent_small/training_tensor_materialized_v0")
STAGE = "masked_loss_adapter_design_without_diffsbdd_modification_v0"
PREVIOUS_STAGE = "diffsbdd_backward_smoke_without_checkpoint_v0"
MASK_LEVELS = [
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "C_scaffold_linker_warhead",
]
SOURCE_FILES = [
    "lightning_modules.py",
    "equivariant_diffusion/en_diffusion.py",
    "equivariant_diffusion/dynamics.py",
    "equivariant_diffusion/conditional_model.py",
    "src/covalent_ext/diffsbdd_loss_semantics.py",
    "src/covalent_ext/diffsbdd_backward_smoke.py",
]
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
]


def _rows_from_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_step10h_outputs_v0(
    report_csv: str | Path = DEFAULT_ROOT / "diffsbdd_backward_smoke_report.csv",
    manifest_json: str | Path = DEFAULT_ROOT / "diffsbdd_backward_smoke_preview_manifest.json",
) -> bool:
    report_path = Path(report_csv)
    manifest_path = Path(manifest_json)
    if not report_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("Step 10H backward smoke outputs are missing")
    rows = _rows_from_csv(report_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if len(rows) != 1 or rows[0].get("smoke_status") != "passed":
        raise ValueError("Step 10H report is not passed")
    expected = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "diffsbdd_forward_loss_semantics_review_without_backward_v0",
        "step10g_loss_semantics_passed": True,
        "model_initialized": True,
        "forward_success": True,
        "loss_reduction": "mean",
        "scalar_loss_finite": True,
        "backward_called": True,
        "backward_success": True,
        "finite_gradients": True,
        "nonzero_gradients": True,
        "grad_nan_count": 0,
        "grad_inf_count": 0,
        "checkpoint_loaded": False,
        "checkpoint_saved": False,
        "training_step_called": False,
        "optimizer_step_executed": False,
        "trainer_fit_called": False,
        "training_executed": False,
        "real_finetune_executed": False,
        "checkpoint_written": False,
        "recommended_next_step": "masked_loss_adapter_design_without_diffsbdd_modification",
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise ValueError(f"Step 10H manifest invalid for {key}: {manifest.get(key)!r}")
    return True


def _source_matches(rel_path: str, patterns: list[str]) -> list[str]:
    path = REPO_ROOT / rel_path
    matches: list[str] = []
    if not path.is_file():
        return matches
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if any(pattern in stripped for pattern in patterns):
            matches.append(f"{rel_path}:{number}:{stripped}")
    return matches


def inspect_masked_loss_candidate_sources_v0() -> dict[str, Any]:
    from equivariant_diffusion.conditional_model import ConditionalDDPM
    from equivariant_diffusion.en_diffusion import EnVariationalDiffusion
    from lightning_modules import LigandPocketDDPM

    inspected_source_files = [rel_path for rel_path in SOURCE_FILES if (REPO_ROOT / rel_path).is_file()]
    output_info_keys = {
        "eps_hat_lig_x",
        "eps_hat_lig_h",
        "error_t_lig",
        "error_t_pocket",
        "SNR_weight",
        "loss_0",
        "kl_prior",
        "delta_log_px",
        "neg_log_const_0",
        "log_pN",
    }
    available_forward_outputs = {
        "output0": "per-sample nll vector returned by LigandPocketDDPM.forward",
        "output1": sorted(output_info_keys),
    }
    minimal_hooks = [
        "Expose or recompute ligand node-wise squared error before sum_except_batch in EnVariationalDiffusion.forward / ConditionalDDPM.forward.",
        "Expose net_out_lig and eps_t_lig or their coordinate/feature residuals before scatter_add reduction.",
        "Thread ligand_target_mask_flat/generation_mask_flat through a wrapper-side data contract without changing original forward behavior.",
        "Keep original nll.mean() available as loss_original and add masked losses in covalent_ext wrapper code.",
    ]
    return {
        "inspected_source_files": inspected_source_files,
        "loss_construction_locations": _source_matches(
            "lightning_modules.py",
            ["loss_t =", "loss_0 =", "nll =", "return nll", "loss = nll.mean"],
        ),
        "ligand_error_locations": _source_matches(
            "equivariant_diffusion/en_diffusion.py",
            ["error_t_lig =", "(eps_t_lig - net_out_lig) ** 2", "sum_except_batch"],
        )
        + _source_matches(
            "equivariant_diffusion/conditional_model.py",
            ["error_t_lig =", "squared_error = (eps_t_lig - net_out_lig) ** 2", "sum_except_batch"],
        ),
        "feature_error_locations": _source_matches(
            "equivariant_diffusion/en_diffusion.py",
            ["eps_hat_lig_h", "net_out_lig[:, self.n_dims:]", "log_ph_given_z0"],
        )
        + _source_matches(
            "equivariant_diffusion/conditional_model.py",
            ["eps_hat_lig_h", "net_out_lig[:, self.n_dims:]", "log_ph_given_z0"],
        ),
        "coordinate_error_locations": _source_matches(
            "equivariant_diffusion/en_diffusion.py",
            ["eps_hat_lig_x", "net_out_lig[:, :self.n_dims]", "eps_lig_x - net_lig_x"],
        )
        + _source_matches(
            "equivariant_diffusion/conditional_model.py",
            ["eps_hat_lig_x", "net_out_lig[:, :self.n_dims]", "squared_error"],
        ),
        "reduction_locations": _source_matches(
            "equivariant_diffusion/en_diffusion.py",
            ["sum_except_batch", "scatter_mean", ".mean()"],
        )
        + _source_matches(
            "lightning_modules.py",
            ["info['error_t_lig'] = error_t_lig.mean", "loss = nll.mean"],
        ),
        "available_forward_outputs": available_forward_outputs,
        "atomwise_loss_exposed_by_current_forward": False,
        "nodewise_noise_exposed_by_current_forward": False,
        "can_build_masked_loss_from_current_output_only": False,
        "minimal_required_hook_points": minimal_hooks,
        "no_diffsbdd_modification_feasible": "uncertain",
        "current_forward_is_mask_aware": False,
        "current_forward_is_full_ligand_objective": True,
        "must_modify_loss_for_masked_training": True,
        "function_signatures": {
            "LigandPocketDDPM.forward": str(inspect.signature(LigandPocketDDPM.forward)),
            "EnVariationalDiffusion.forward": str(inspect.signature(EnVariationalDiffusion.forward)),
            "ConditionalDDPM.forward": str(inspect.signature(ConditionalDDPM.forward)),
        },
        "notes": [
            "Current output0 is per-sample nll, not atom-wise.",
            "Current output1 values are scalar diagnostics after reductions.",
            "Node-wise signals exist internally as eps_t_lig/net_out_lig/squared_error before sum_except_batch, but current forward does not expose them.",
        ],
    }


def build_masked_loss_adapter_design_v0(source_info: dict[str, Any]) -> dict[str, Any]:
    proposed_components = [
        "loss_original = nll.mean()",
        "loss_masked_x = masked coordinate denoising loss over ligand target atoms",
        "loss_masked_h = masked feature denoising loss over ligand target atoms",
        "loss_warhead_type = optional warhead type classification auxiliary",
        "loss_reactive_pair = optional ligand reactive atom / residue atom pair auxiliary",
        "loss_geometry = optional covalent-ready geometry auxiliary",
    ]
    mask_policy = {
        "A_warhead_only": {
            "target": "warhead atoms",
            "context": "scaffold + linker",
            "focus": "warhead geometry/reactivity",
        },
        "B_linker_warhead": {
            "target": "linker + warhead",
            "context": "scaffold",
            "focus": "linker trajectory + warhead placement",
        },
        "B2_scaffold_warhead": {
            "target": "scaffold + warhead",
            "context": "linker",
            "focus": "scaffold variation with warhead constraints",
        },
        "C_scaffold_linker_warhead": {
            "target": "all ligand atoms",
            "context": "none",
            "focus": "full ligand generation with covalent labels",
        },
    }
    adapter_input_contract = [
        "model output raw loss-like tensor",
        "optional raw atomwise predicted noise / target noise if exposed later",
        "ligand_target_mask_flat",
        "ligand_context_mask_flat",
        "generation_mask_flat",
        "ligand_mask_flat",
        "sample_id",
        "mask_level",
        "ligand_reactive_atom_index",
        "residue reactive atom info",
        "warhead_type_label",
        "optional geometry labels",
    ]
    adapter_output_contract = [
        "loss_total",
        "loss_original",
        "loss_masked_x",
        "loss_masked_h",
        "loss_aux",
        "diagnostics",
        "safety_flags",
    ]
    current_output_only = source_info["can_build_masked_loss_from_current_output_only"]
    if current_output_only is False:
        design_status = "ready"
        recommended_next_step = "diffsbdd_atomwise_loss_hook_design_without_behavior_change"
        recommended_path = (
            "Implement a no-behavior-change hook/probe to expose ligand atom-wise denoising residuals, "
            "then run masked loss dry run before any optimizer smoke."
        )
    else:
        design_status = "uncertain"
        recommended_next_step = "manual_masked_loss_adapter_review"
        recommended_path = "Manually verify current outputs before masked loss dry run."
    return {
        "design_status": design_status,
        "current_output_limitation": "output0 is per-sample nll and output1 is scalar diagnostics; current output cannot support atom-level masked loss directly",
        "required_model_signals": [
            "ligand atom-wise predicted noise for coordinates",
            "ligand atom-wise target noise for coordinates",
            "ligand atom-wise predicted feature/noise logits or residuals",
            "ligand target/context/generation masks aligned to flattened ligand atoms",
            "optional xh_lig_hat for geometry auxiliary terms",
        ],
        "proposed_loss_components": proposed_components,
        "proposed_loss_formula_text": (
            "loss_total = 1.0*loss_original + 1.0*loss_masked_x + 0.2*loss_masked_h "
            "+ 0.1*loss_warhead_type + 0.1*loss_reactive_pair + 0.1*loss_geometry"
        ),
        "initial_weights": {
            "w_original": 1.0,
            "w_x": 1.0,
            "w_h": 0.2,
            "w_warhead_type": 0.1,
            "w_reactive_pair": 0.1,
            "w_geometry": 0.1,
        },
        "mask_level_loss_policy": mask_policy,
        "adapter_input_contract": adapter_input_contract,
        "adapter_output_contract": adapter_output_contract,
        "no_modification_path": (
            "Current committed outputs are insufficient for true masked atom-wise loss. "
            "A wrapper can define contracts and combine loss_original, but cannot compute loss_masked_x/h without extra internal signals."
        ),
        "minimal_modification_path": (
            "Add a no-behavior-change hook or optional return path around EnVariationalDiffusion.forward / ConditionalDDPM.forward "
            "to expose eps_t_lig, net_out_lig, ligand mask, and unreduced squared residuals."
        ),
        "recommended_path": recommended_path,
        "risks": [
            "Using per-sample nll alone would not enforce warhead/linker/scaffold target masks.",
            "Hooking internal tensors must preserve original DiffSBDD behavior and checkpoint compatibility.",
            "Feature denoising semantics need careful separation of coordinate and categorical channels.",
            "C mode has no context atoms and may behave like full ligand generation.",
        ],
        "recommended_next_step": recommended_next_step,
        "blocking_reasons": [],
    }
