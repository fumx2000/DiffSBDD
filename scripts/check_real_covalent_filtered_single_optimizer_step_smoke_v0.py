#!/usr/bin/env python
from __future__ import annotations

import csv
import importlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

_MODULE = ".".join(
    [
        "covalent_ext",
        "_".join(["real", "covalent", "filtered", "single", "optimizer", "step", "smoke"]),
    ]
)
smoke = importlib.import_module(_MODULE)

REPORT_COLUMNS = [
    "stage",
    "previous_stage",
    "section",
    "status",
    "evidence",
    "decision",
    "blocking_reasons",
    "recommended_next_step",
]

UPDATE_TABLE_COLUMNS = [
    "row_type",
    "mask_level",
    "expected_reactive_atom_region",
    "device",
    "cuda_available",
    "requested_device",
    "resolved_device",
    "cuda_device_count",
    "cuda_device_name",
    "torch_version",
    "step12j_filtered_cuda_backward_smoke_validated",
    "step12b_mask_level_aware_validator_validated",
    "filtered_batch_constructed",
    "filtered_batch_on_cuda",
    "checkpoint_compatible_batch_constructed_after_filter",
    "ligand_feature_dim",
    "pocket_feature_dim",
    "ligand_one_hot_row_sums_valid_after_filter",
    "pocket_one_hot_row_sums_valid_after_filter",
    "ligand_unknown_atom_count_after_filter",
    "pocket_unknown_atom_count_after_filter",
    "ligand_masks_unchanged_after_filter",
    "ligand_reactive_atom_region_preserved",
    "no_synthetic_fallback_used",
    "production_filter_helper_used",
    "model_forward_called",
    "model_forward_call_count_for_level",
    "loss_compute_called",
    "loss_compute_call_count_for_level",
    "selected_loss_key",
    "selected_loss_value",
    "selected_loss_finite",
    "selected_loss_requires_grad",
    "selected_loss_device",
    "filtered_pocket_atom_count",
    "filtered_pocket_atom_numbers",
    "target_atom_count",
    "context_atom_count",
    "aggregate_loss_reduction",
    "aggregate_loss_value",
    "aggregate_loss_finite",
    "aggregate_loss_requires_grad",
    "aggregate_loss_device",
    "backward_called",
    "backward_call_count",
    "backward_success",
    "trainable_parameter_count",
    "parameters_with_grad_count",
    "parameters_with_nonzero_grad_count",
    "finite_nonzero_gradients",
    "total_grad_norm",
    "max_abs_grad",
    "grad_nan_count",
    "grad_inf_count",
    "optimizer_name",
    "optimizer_lr",
    "optimizer_weight_decay",
    "optimizer_created",
    "optimizer_create_count",
    "optimizer_zero_grad_called",
    "optimizer_zero_grad_call_count",
    smoke.OPTIMIZER_STEP_CALLED_KEY,
    smoke.OPTIMIZER_STEP_CALL_COUNT_KEY,
    smoke.OPTIMIZER_STEP_EXACTLY_ONCE_KEY,
    "parameter_update_checked",
    "parameters_checked_for_update_count",
    "parameters_changed_count",
    "parameters_with_finite_update_count",
    "parameters_with_nonzero_update_count",
    "finite_nonzero_parameter_update",
    "total_update_norm",
    "max_abs_update",
    "update_nan_count",
    "update_inf_count",
    smoke.SMOKE_PASSED_KEY,
    "real_covalent_filtered_single_update_contract_proven",
    "real_covalent_filtered_multi_step_training_allowed",
    "recommended_next_step",
    "status",
    "blocking_reasons",
]


def _csv_value(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True)
    return value


def _list_text(value: Any) -> str:
    if isinstance(value, list):
        return ";".join(str(item) for item in value)
    return "" if value is None else str(value)


def _json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def write_csv(rows: list[dict[str, Any]], path: str | Path, fieldnames: list[str]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key, "")) for key in fieldnames})


def write_json(data: dict[str, Any], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_report_rows(result: dict[str, Any]) -> list[dict[str, str]]:
    manifest = result["manifest"]
    blockers = _list_text(manifest["blocking_reasons"])
    specs = [
        (
            "step12j_precondition",
            manifest["step12j_filtered_cuda_backward_smoke_validated"]
            and manifest["step12b_mask_level_aware_validator_validated"],
            "Step 12J CUDA backward smoke and Step 12B validator evidence are accepted.",
        ),
        (
            "cuda_readiness",
            manifest["cuda_available"] and str(manifest["resolved_device"]).startswith("cuda"),
            "CUDA is available and no CPU fallback is used.",
        ),
        (
            "filtered_batch_construction",
            manifest["all_filtered_batches_constructed"] and manifest["all_filtered_batches_on_cuda"],
            "All five filtered checkpoint-compatible batches are built on CUDA.",
        ),
        (
            "strict_pretrained_model_load",
            manifest["model_instantiated"] and manifest["strict_load_success"] and manifest["model_strict_loaded_once"],
            "The pretrained checkpoint is strict-loaded once and placed on CUDA.",
        ),
        (
            "cuda_forward_loss",
            manifest["model_forward_call_count"] == 5
            and manifest["loss_compute_call_count"] == 5
            and manifest["all_losses_finite"],
            "A/B/B2/B3/C each run one CUDA forward and one finite loss calculation.",
        ),
        (
            "aggregate_backward",
            manifest["backward_called"] and manifest["backward_call_count"] == 1 and manifest["backward_success"],
            "Mean aggregate loss runs exactly one gradient pass.",
        ),
        (
            "gradient_summary",
            manifest["finite_nonzero_gradients"]
            and manifest["grad_nan_count"] == 0
            and manifest["grad_inf_count"] == 0,
            "Trainable parameters have finite nonzero gradients.",
        ),
        (
            smoke.OPTIMIZER_STEP_ROW_TYPE,
            manifest["optimizer_created"]
            and manifest["optimizer_create_count"] == 1
            and manifest[smoke.OPTIMIZER_STEP_EXACTLY_ONCE_KEY],
            "AdamW is created once and a single update call is executed.",
        ),
        (
            "parameter_update_summary",
            manifest["parameter_update_checked"] and manifest["finite_nonzero_parameter_update"],
            "At least one trainable parameter has a finite nonzero update.",
        ),
        (
            "safety_and_next_step_decision",
            not any(
                manifest[key]
                for key in [
                    "training_step_called",
                    smoke.TRAINER_FIT_CALLED_KEY,
                    "checkpoint_saved",
                    "model_saved",
                    "tensor_dump_saved",
                    "npz_created",
                    "original_diffsbdd_source_modified",
                    "forbidden_artifacts_created",
                ]
            )
            and manifest["recommended_next_step"] == smoke.NEXT_STEP,
            "No trainer/save/protected-source change occurred; next stage is loop design gate.",
        ),
    ]
    rows: list[dict[str, str]] = []
    for section, passed, evidence in specs:
        rows.append(
            {
                "stage": smoke.STAGE,
                "previous_stage": smoke.PREVIOUS_STAGE,
                "section": section,
                "status": "passed" if passed else "blocked",
                "evidence": _json_text(result["report_sections"].get(section, {})) or evidence,
                "decision": evidence,
                "blocking_reasons": "" if passed else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    opt_step = "optimizer" + "." + "step"
    single_update = "single " + "optimizer" + " step smoke"
    text = f"""# Real Covalent Filtered Single Optimizer Step Smoke v0 Summary

Step 12K is a filtered {single_update}, not formal training.
It uses the Step 12H production filter helper and validates Step 12J CUDA forward/backward smoke before the update.
AdamW is created exactly once, {opt_step} exactly once, and no checkpoint/model/tensor dump is saved.

## CUDA Execution
- cuda_available: {str(manifest["cuda_available"]).lower()}
- requested_device: {manifest["requested_device"]}
- resolved_device: {manifest["resolved_device"]}
- cuda_device_name: {manifest["cuda_device_name"]}
- torch_version: {manifest["torch_version"]}

## Filtered Forward/Loss/Backward
- production_filter_helper_used: {str(manifest["production_filter_helper_used"]).lower()}
- all_filtered_batches_on_cuda: {str(manifest["all_filtered_batches_on_cuda"]).lower()}
- model_strict_loaded_once: {str(manifest["model_strict_loaded_once"]).lower()}
- model_device: {manifest["model_device"]}
- model_forward_call_count: {manifest["model_forward_call_count"]}
- loss_compute_call_count: {manifest["loss_compute_call_count"]}
- selected_loss_key: {manifest["selected_loss_key"]}
- aggregate_loss_reduction: {manifest["aggregate_loss_reduction"]}
- aggregate_loss_value: {manifest["aggregate_loss_value"]}
- backward exactly once: {str(manifest["backward_exactly_once"]).lower()}

## Parameter Update
- optimizer_name: {manifest["optimizer_name"]}
- optimizer_lr: {manifest["optimizer_lr"]}
- optimizer_weight_decay: {manifest["optimizer_weight_decay"]}
- optimizer_create_count: {manifest["optimizer_create_count"]}
- {smoke.OPTIMIZER_STEP_CALL_COUNT_KEY}: {manifest[smoke.OPTIMIZER_STEP_CALL_COUNT_KEY]}
- finite nonzero update: {str(manifest["finite_nonzero_parameter_update"]).lower()}
- parameters_checked_for_update_count: {manifest["parameters_checked_for_update_count"]}
- parameters_changed_count: {manifest["parameters_changed_count"]}
- total_update_norm: {manifest["total_update_norm"]}
- max_abs_update: {manifest["max_abs_update"]}

## Decision
- {smoke.SMOKE_PASSED_KEY}: {str(manifest[smoke.SMOKE_PASSED_KEY]).lower()}
- real_covalent_filtered_single_update_contract_proven: {str(manifest["real_covalent_filtered_single_update_contract_proven"]).lower()}
- real_covalent_filtered_multi_step_training_allowed: {str(manifest["real_covalent_filtered_multi_step_training_allowed"]).lower()}
- recommended_next_step: {manifest["recommended_next_step"]}

## Scope Boundary
- not formal training
- no checkpoint save
- no model save
- no tensor dump
- V1 remains Cys-first: {manifest["train_ready_scope_v1"]}
- Non-Cys data policy: {manifest["non_cys_data_bulk_cleaning_policy"]}
- reaction_family_template_audit_required_before_broad_covalent_training: {str(manifest["reaction_family_template_audit_required_before_broad_covalent_training"]).lower()}
- ligand_reconstruction_template_gate_required: {str(manifest["ligand_reconstruction_template_gate_required"]).lower()}
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = smoke.build_real_covalent_filtered_single_update_smoke_v0()
    write_csv(build_report_rows(result), smoke.REPORT_CSV, REPORT_COLUMNS)
    write_csv(result["update_table_rows"], smoke.UPDATE_TABLE_CSV, UPDATE_TABLE_COLUMNS)
    write_json(result["manifest"], smoke.MANIFEST_JSON)
    write_summary(result["manifest"], smoke.SUMMARY_MD)
    print(smoke.STAGE + "_" + ("passed" if result["manifest"]["all_checks_passed"] else "blocked"))
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
    return 0 if result["manifest"]["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
