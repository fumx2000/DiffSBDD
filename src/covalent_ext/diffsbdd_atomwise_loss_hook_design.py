from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


DEFAULT_ROOT = Path("data/derived/covalent_small/training_tensor_materialized_v0")
STAGE = "diffsbdd_atomwise_loss_hook_design_without_behavior_change_v0"
PREVIOUS_STAGE = "masked_loss_adapter_design_without_diffsbdd_modification_v0"
MASK_LEVELS = [
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "C_scaffold_linker_warhead",
]
SOURCE_FILES = [
    "equivariant_diffusion/en_diffusion.py",
    "equivariant_diffusion/conditional_model.py",
    "equivariant_diffusion/dynamics.py",
    "lightning_modules.py",
    "src/covalent_ext/masked_loss_adapter_design.py",
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
    "archive_created",
]


def _rows_from_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _bool_text(value: Any) -> str:
    return str(value).strip().lower()


def _require_manifest_value(manifest: dict[str, Any], key: str, expected: Any) -> None:
    actual = manifest.get(key)
    if actual != expected:
        raise ValueError(f"Step 10I manifest invalid for {key}: {actual!r}")


def validate_step10i_outputs_v0(
    report_csv: str | Path = DEFAULT_ROOT / "masked_loss_adapter_design_report.csv",
    manifest_json: str | Path = DEFAULT_ROOT / "masked_loss_adapter_design_preview_manifest.json",
) -> bool:
    report_path = Path(report_csv)
    manifest_path = Path(manifest_json)
    if not report_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("Step 10I masked loss adapter design outputs are missing")

    rows = _rows_from_csv(report_path)
    if len(rows) != 1:
        raise ValueError(f"Step 10I report must contain exactly one row, found {len(rows)}")
    row = rows[0]
    expected_row_values = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "diffsbdd_backward_smoke_without_checkpoint_v0",
        "step10h_backward_smoke_passed": "true",
        "source_inspection_status": "passed",
        "design_status": "ready",
        "atomwise_loss_exposed_by_current_forward": "false",
        "nodewise_noise_exposed_by_current_forward": "false",
        "can_build_masked_loss_from_current_output_only": "false",
        "current_forward_is_mask_aware": "false",
        "current_forward_is_full_ligand_objective": "true",
        "must_modify_loss_for_masked_training": "true",
        "recommended_next_step": "diffsbdd_atomwise_loss_hook_design_without_behavior_change",
    }
    for key, expected in expected_row_values.items():
        if row.get(key) != expected:
            raise ValueError(f"Step 10I report invalid for {key}: {row.get(key)!r}")
    for field in SAFETY_FALSE_FIELDS:
        if _bool_text(row.get(field, "")) != "false":
            raise ValueError(f"Step 10I report safety flag is not false: {field}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_manifest_values = {
        "stage": PREVIOUS_STAGE,
        "previous_stage": "diffsbdd_backward_smoke_without_checkpoint_v0",
        "step10h_backward_smoke_passed": True,
        "design_status": "ready",
        "atomwise_loss_exposed_by_current_forward": False,
        "nodewise_noise_exposed_by_current_forward": False,
        "can_build_masked_loss_from_current_output_only": False,
        "current_forward_is_mask_aware": False,
        "current_forward_is_full_ligand_objective": True,
        "must_modify_loss_for_masked_training": True,
        "recommended_next_step": "diffsbdd_atomwise_loss_hook_design_without_behavior_change",
        "all_checks_passed": True,
    }
    for key, expected in expected_manifest_values.items():
        _require_manifest_value(manifest, key, expected)
    for field in SAFETY_FALSE_FIELDS:
        _require_manifest_value(manifest, field, False)
    return True


def _source_matches(rel_path: str, patterns: list[str]) -> list[str]:
    path = REPO_ROOT / rel_path
    if not path.is_file():
        return []
    matches: list[str] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if any(pattern in stripped for pattern in patterns):
            matches.append(f"{rel_path}:{number}:{stripped}")
    return matches


def _all_source_matches(patterns: list[str]) -> list[str]:
    matches: list[str] = []
    for rel_path in SOURCE_FILES:
        matches.extend(_source_matches(rel_path, patterns))
    return matches


def inspect_atomwise_hook_candidate_sources_v0() -> dict[str, Any]:
    inspected_source_files = [rel_path for rel_path in SOURCE_FILES if (REPO_ROOT / rel_path).is_file()]
    eps_t_lig_locations = _all_source_matches(["eps_t_lig"])
    net_out_lig_locations = _all_source_matches(["net_out_lig"])
    squared_error_locations = _all_source_matches(["squared_error", "(eps_t_lig - net_out_lig) ** 2"])
    error_t_lig_locations = _all_source_matches(["error_t_lig"])
    reduction_locations = _all_source_matches(
        ["sum_except_batch", "scatter_add", "scatter_mean", ".mean()", "loss = nll.mean"]
    )
    coordinate_channel_locations = _all_source_matches(
        ["net_out_lig[:, :self.n_dims]", "eps_hat_lig_x", "eps_lig_x", "residual_x"]
    )
    feature_channel_locations = _all_source_matches(
        ["net_out_lig[:, self.n_dims:]", "eps_hat_lig_h", "log_ph_given_z0", "residual_h"]
    )
    ligand_mask_locations = _all_source_matches(["ligand['mask']", "lig_mask", "ligand_target_mask_flat"])

    candidate_hook_points = [
        "A. EnVariationalDiffusion.forward / ConditionalDDPM.forward expose ligand node-wise residual before sum_except_batch.",
        "B. EnVariationalDiffusion.forward / ConditionalDDPM.forward expose eps_t_lig and net_out_lig immediately after dynamics.",
        "C. LigandPocketDDPM.forward wrapper captures internal tensors with a probe context.",
        "D. covalent_ext forward-probe copy for dry-run inspection only.",
    ]
    preferred_hook_point = (
        "B. Expose eps_t_lig and net_out_lig after dynamics through an optional no-behavior-change probe path"
    )
    hook_point_rankings = [
        {
            "rank": 1,
            "hook_point": "B",
            "reason": "Raw predicted and target noise are the most general atom-wise signals; covalent_ext can compute coordinate and feature residuals without changing default loss.",
        },
        {
            "rank": 2,
            "hook_point": "A",
            "reason": "Unreduced squared residual is close to the masked objective but less flexible for feature/coordinate weighting.",
        },
        {
            "rank": 3,
            "hook_point": "C",
            "reason": "A wrapper probe avoids return-value changes but is more brittle because it depends on internal call structure.",
        },
        {
            "rank": 4,
            "hook_point": "D",
            "reason": "A copied dry-run probe avoids model edits but risks semantic drift from DiffSBDD forward.",
        },
    ]
    hook_point_risks = {
        "A": "May couple the adapter to the current residual formula and miss raw noise diagnostics.",
        "B": "Requires a minimal optional probe/return side channel inside diffusion forward code.",
        "C": "Monkeypatch or context capture can be fragile across refactors.",
        "D": "Duplicated forward logic can silently diverge from the original implementation.",
    }
    tensors_needed_for_masked_loss = [
        "eps_t_lig",
        "net_out_lig",
        "ligand_mask_flat",
        "ligand_target_mask_flat",
        "ligand_context_mask_flat",
        "generation_mask_flat",
        "optional xh_t_lig",
        "optional alpha_t",
        "optional sigma_t",
        "optional gamma_t",
        "optional t_int",
        "optional ligand_size",
    ]
    tensor_shape_contract = {
        "eps_t_lig": "[N_lig_total, n_dims + lig_feature_dim]",
        "net_out_lig": "[N_lig_total, n_dims + lig_feature_dim]",
        "coordinate_residual": "[N_lig_total, 3]",
        "feature_residual": "[N_lig_total, lig_feature_dim]",
        "ligand_target_mask_flat": "[N_lig_total]",
        "ligand_context_mask_flat": "[N_lig_total]",
        "generation_mask_flat": "[N_lig_total]",
        "batch_index_mask": "[N_lig_total]",
    }
    no_behavior_change_requirements = [
        "Default forward return value remains unchanged.",
        "Original per-sample nll and diagnostics remain bit-for-bit equivalent when probe is disabled.",
        "No default training_step behavior changes.",
        "No checkpoint key or module parameter changes.",
        "Atom-wise tensors are exposed only under an explicit probe flag or context.",
    ]
    notes = [
        "eps_t_lig is produced by noised_representation before the dynamics call.",
        "net_out_lig is produced by the dynamics network from z_t_lig and pocket context.",
        "Node-wise squared residual exists before sum_except_batch in conditional_model.py and can be recomputed in en_diffusion.py from eps_t_lig and net_out_lig.",
        "Current info outputs are reduced diagnostics and are not sufficient for target-atom masked losses.",
    ]
    return {
        "inspected_source_files": inspected_source_files,
        "eps_t_lig_locations": eps_t_lig_locations,
        "net_out_lig_locations": net_out_lig_locations,
        "squared_error_locations": squared_error_locations,
        "error_t_lig_locations": error_t_lig_locations,
        "reduction_locations": reduction_locations,
        "coordinate_channel_locations": coordinate_channel_locations,
        "feature_channel_locations": feature_channel_locations,
        "ligand_mask_locations": ligand_mask_locations,
        "candidate_hook_points": candidate_hook_points,
        "preferred_hook_point": preferred_hook_point,
        "hook_point_rankings": hook_point_rankings,
        "hook_point_risks": hook_point_risks,
        "tensors_needed_for_masked_loss": tensors_needed_for_masked_loss,
        "tensor_shape_contract": tensor_shape_contract,
        "no_behavior_change_requirements": no_behavior_change_requirements,
        "whether_original_forward_return_should_change": False,
        "whether_checkpoint_compatibility_should_be_affected": False,
        "notes": notes,
    }


def build_atomwise_loss_hook_design_v0(source_info: dict[str, Any]) -> dict[str, Any]:
    found_required_sources = all(
        [
            source_info["eps_t_lig_locations"],
            source_info["net_out_lig_locations"],
            source_info["error_t_lig_locations"] or source_info["squared_error_locations"],
            source_info["reduction_locations"],
        ]
    )
    design_status = "ready" if found_required_sources else "blocked"
    blocking_reasons = [] if found_required_sources else ["required atom-wise residual source locations were not all found"]
    recommended_next_step = (
        "atomwise_loss_hook_prototype_without_behavior_change"
        if design_status == "ready"
        else "manual_atomwise_hook_review"
    )
    captured_tensor_contract = {
        "required": ["eps_t_lig", "net_out_lig", "ligand_mask_flat"],
        "adapter_supplied": [
            "ligand_target_mask_flat",
            "ligand_context_mask_flat",
            "generation_mask_flat",
            "sample_id",
            "mask_level",
        ],
        "optional": ["xh_t_lig", "alpha_t", "sigma_t", "gamma_t", "t_int", "ligand_size", "batch_size"],
    }
    tensor_alignment_contract = [
        "eps_t_lig, net_out_lig, ligand_mask_flat, and covalent target masks must share the same flattened ligand atom order.",
        "residual = eps_t_lig - net_out_lig",
        "residual_x = residual[:, :3]",
        "residual_h = residual[:, 3:]",
        "loss_masked_x = mean(sum(residual_x[target_mask] ** 2, dim=-1))",
        "loss_masked_h = mean(sum(residual_h[target_mask] ** 2, dim=-1))",
        "target_mask must contain at least one atom; empty target masks should block or use an explicit fallback.",
    ]
    behavior_preservation_contract = [
        "When atomwise probe is disabled, forward returns exactly the original tuple.",
        "When atomwise probe is disabled, original loss and diagnostics are unchanged.",
        "Probe tensors are detached only if the caller requests diagnostic-only mode; masked-loss mode keeps graph connectivity.",
        "No optimizer, trainer, or training loop behavior is introduced by the hook design.",
    ]
    checkpoint_compatibility_contract = [
        "No new parameters, buffers, or renamed modules.",
        "No checkpoint load/save path is introduced.",
        "Optional probe metadata is runtime-only and absent from state_dict.",
    ]
    hook_interface_contract = {
        "preferred_api": "with covalent_ext atomwise probe context or explicit return_atomwise=True on a wrapper path",
        "default": "return_atomwise=False",
        "default_forward_return_changes": False,
        "probe_payload": captured_tensor_contract,
    }
    return {
        "design_status": design_status,
        "recommended_hook_strategy": "optional_no_behavior_change_atomwise_probe_for_eps_t_lig_and_net_out_lig",
        "preferred_hook_point": source_info["preferred_hook_point"],
        "hook_interface_contract": hook_interface_contract,
        "captured_tensor_contract": captured_tensor_contract,
        "tensor_alignment_contract": tensor_alignment_contract,
        "behavior_preservation_contract": behavior_preservation_contract,
        "checkpoint_compatibility_contract": checkpoint_compatibility_contract,
        "masked_loss_readiness_after_hook": {
            "can_capture_atomwise_noise_after_hook": design_status == "ready",
            "can_compute_masked_x_loss_after_hook": design_status == "ready",
            "can_compute_masked_h_loss_after_hook": design_status == "ready",
        },
        "implementation_phases": [
            "Hook design report only",
            "No-behavior-change hook prototype in covalent_ext or optional return path",
            "Hook shape smoke",
            "Masked loss dry run without backward",
            "Masked loss backward smoke",
            "Only then optimizer smoke",
        ],
        "recommended_next_step": recommended_next_step,
        "blocking_reasons": blocking_reasons,
        "risks": [
            "Hooking raw internal tensors is close to the model core and must be guarded by tests that compare default outputs.",
            "Feature residual semantics may require confirming categorical channel scaling.",
            "A/B/B2/C masks must be aligned to flattened ligand order from the adapter.",
            "A context-manager probe is convenient but can be brittle if the internal forward flow changes.",
        ],
    }
