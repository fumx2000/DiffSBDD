#!/usr/bin/env python
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext.real_covalent_backward_smoke import (  # noqa: E402
    CANONICAL_MASK_LEVELS,
    GRAD_TABLE_CSV,
    MANIFEST_JSON,
    PREVIOUS_STAGE,
    REPORT_CSV,
    STAGE,
    SUMMARY_MD,
    build_real_covalent_backward_smoke_v0,
)


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

GRAD_TABLE_COLUMNS = [
    "row_type",
    "mask_level",
    "expected_reactive_atom_region",
    "sample_ids",
    "batch_size",
    "adapted_valid",
    "model_input_valid",
    "diffsbdd_like_valid",
    "checkpoint_compatible_real_batch_constructed",
    "no_synthetic_fallback_used",
    "model_forward_called",
    "forward_call_count",
    "loss_computed",
    "selected_loss_key",
    "selected_loss_value",
    "loss_requires_grad",
    "loss_finite",
    "target_atom_count",
    "context_atom_count",
    "aggregate_loss_reduction",
    "aggregate_loss_value",
    "aggregate_loss_requires_grad",
    "aggregate_loss_finite",
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
    "status",
    "blocking_reasons",
]


def _json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _list_text(value: Any) -> str:
    if isinstance(value, list):
        return ";".join(str(item) for item in value)
    return "" if value is None else str(value)


def _csv_value(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True)
    return value


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
    sections = result["report_sections"]
    blockers = _list_text(manifest["blocking_reasons"])
    recommended = manifest["recommended_next_step"]
    rows = []
    specs = [
        (
            "step12d_precondition",
            manifest["step12d_validated"] and manifest["step12b_mask_level_aware_validator_validated"],
            "Step 12D forward/loss evidence and Step 12B validator behavior are accepted.",
        ),
        (
            "real_batch_loading",
            manifest["selected_artifact_is_real_covalent"] and not manifest["selected_artifact_is_synthetic_only"],
            "Read-only real covalent Dataset/DataLoader supplies the backward smoke batch.",
        ),
        (
            "mask_level_aware_model_input",
            manifest["all_model_inputs_valid"],
            "A/B/B2/B3/C model inputs validate with mask-level-aware reactive atom rules.",
        ),
        (
            "checkpoint_compatible_real_batch",
            manifest["all_checkpoint_compatible_real_batches_constructed"] and manifest["no_synthetic_fallback_used"],
            "Real covalent batches are converted to checkpoint-compatible model inputs without synthetic fallback.",
        ),
        (
            "pretrained_strict_load",
            manifest["strict_load_success"] and manifest["pretrained_weights_loaded"],
            "A fresh checkpoint-compatible pretrained model is strict-loaded once.",
        ),
        (
            "forward_loss_by_mask_level",
            manifest["all_losses_finite"] and manifest["all_losses_require_grad"],
            "Each canonical mask level runs exactly one forward and differentiable selected loss.",
        ),
        (
            "aggregate_backward",
            manifest["backward_success"] and manifest["backward_call_count"] == 1,
            "The mean aggregate selected loss executes exactly one reverse pass.",
        ),
        (
            "safety_boundary",
            not any(
                manifest[key]
                for key in [
                    "optimizer_created",
                    "optimizer_step_called",
                    "training_step_called",
                    "trainer_fit_called",
                    "checkpoint_saved",
                    "model_saved",
                    "tensor_dump_saved",
                    "npz_created",
                    "original_diffsbdd_source_modified",
                    "forbidden_artifacts_created",
                ]
            ),
            "No optimizer, training API, persistence, forbidden artifact, or protected source edit occurred.",
        ),
        (
            "next_step_decision",
            manifest["real_covalent_single_optimizer_step_smoke_allowed"],
            "The next allowed stage is real covalent single optimizer step smoke if all checks pass.",
        ),
    ]
    for section, passed, decision in specs:
        rows.append(
            {
                "stage": STAGE,
                "previous_stage": PREVIOUS_STAGE,
                "section": section,
                "status": "passed" if passed else "blocked",
                "evidence": _json_text(sections[section]),
                "decision": decision,
                "blocking_reasons": blockers,
                "recommended_next_step": recommended,
            }
        )
    return rows


def write_summary(result: dict[str, Any], path: str | Path) -> None:
    manifest = result["manifest"]
    rows = result["grad_table_rows"]
    by_level = {row["mask_level"]: row for row in rows if row["row_type"] == "mask_level_loss"}
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Real Covalent Backward Smoke v0 Summary",
        "",
        "Step 12E is a real covalent backward smoke, not training.",
        "It uses the real covalent sample_index and does not use synthetic fallback.",
        "It runs one forward/loss pass per canonical mask level, then one aggregate reverse pass.",
        "It does not create an optimizer, call training_step, call trainer.fit, or save checkpoint/model/tensor dump.",
        "Formal training still requires a separate feature semantics audit before optimizer or checkpointed training stages.",
        "",
        "## Inputs",
        f"- input_source: {manifest['input_source']}",
        f"- selected_sample_index: {manifest['selected_sample_index']}",
        f"- checkpoint_path: {manifest['checkpoint_path']}",
        f"- requested_device: {manifest['requested_device']}",
        f"- resolved_device: {manifest['resolved_device']}",
        f"- batch_size: {manifest['batch_size']}",
        f"- num_workers: {manifest['num_workers']}",
        "",
        "## Mask Levels",
        f"- canonical_mask_levels: {', '.join(CANONICAL_MASK_LEVELS)}",
        "- A_warhead_only expected reactive atom region: target",
        "- B_linker_warhead expected reactive atom region: target",
        "- B2_scaffold_warhead expected reactive atom region: target",
        "- B3_scaffold_only expected reactive atom region: context",
        "- C_scaffold_linker_warhead expected reactive atom region: target",
        "",
        "## Pretrained Model",
        f"- model_instantiated: {str(manifest['model_instantiated']).lower()}",
        f"- strict_load_success: {str(manifest['strict_load_success']).lower()}",
        f"- pretrained_weights_loaded: {str(manifest['pretrained_weights_loaded']).lower()}",
        f"- pretrained_base_integration_proven: {str(manifest['pretrained_base_integration_proven']).lower()}",
        f"- model_strict_loaded_once: {str(manifest['model_strict_loaded_once']).lower()}",
        "",
        "## Forward/Loss Results",
        f"- model_forward_called: {str(manifest['model_forward_called']).lower()}",
        f"- model_forward_call_count: {manifest['model_forward_call_count']}",
        f"- all_level_forward_call_count_exactly_one: {str(manifest['all_level_forward_call_count_exactly_one']).lower()}",
        f"- all_losses_computed: {str(manifest['all_losses_computed']).lower()}",
        f"- all_losses_finite: {str(manifest['all_losses_finite']).lower()}",
        f"- all_losses_require_grad: {str(manifest['all_losses_require_grad']).lower()}",
        f"- selected_loss_key: {manifest['selected_loss_key']}",
        "",
        "## Per-Level Loss Table",
        "| mask_level | selected_loss_value | loss_finite | loss_requires_grad |",
        "| --- | ---: | --- | --- |",
    ]
    for level in CANONICAL_MASK_LEVELS:
        row = by_level[level]
        lines.append(
            f"| {level} | {row['selected_loss_value']} | {str(row['loss_finite']).lower()} | "
            f"{str(row['loss_requires_grad']).lower()} |"
        )
    lines.extend(
        [
            "",
            "## Aggregate Backward",
            f"- aggregate_loss_reduction: {manifest['aggregate_loss_reduction']}",
            f"- aggregate_loss_value: {manifest['aggregate_loss_value']}",
            f"- aggregate_loss_finite: {str(manifest['aggregate_loss_finite']).lower()}",
            f"- aggregate_loss_requires_grad: {str(manifest['aggregate_loss_requires_grad']).lower()}",
            f"- backward_called: {str(manifest['backward_called']).lower()}",
            f"- backward_call_count: {manifest['backward_call_count']}",
            f"- backward_exactly_once: {str(manifest['backward_exactly_once']).lower()}",
            f"- backward_success: {str(manifest['backward_success']).lower()}",
            f"- trainable_parameter_count: {manifest['trainable_parameter_count']}",
            f"- parameters_with_grad_count: {manifest['parameters_with_grad_count']}",
            f"- parameters_with_nonzero_grad_count: {manifest['parameters_with_nonzero_grad_count']}",
            f"- finite_nonzero_gradients: {str(manifest['finite_nonzero_gradients']).lower()}",
            f"- total_grad_norm: {manifest['total_grad_norm']}",
            f"- max_abs_grad: {manifest['max_abs_grad']}",
            f"- grad_nan_count: {manifest['grad_nan_count']}",
            f"- grad_inf_count: {manifest['grad_inf_count']}",
            "",
            "## Safety Boundary",
            f"- optimizer_created: {str(manifest['optimizer_created']).lower()}",
            f"- optimizer_step_called: {str(manifest['optimizer_step_called']).lower()}",
            f"- training_step_called: {str(manifest['training_step_called']).lower()}",
            f"- trainer_fit_called: {str(manifest['trainer_fit_called']).lower()}",
            f"- checkpoint_saved: {str(manifest['checkpoint_saved']).lower()}",
            f"- model_saved: {str(manifest['model_saved']).lower()}",
            f"- tensor_dump_saved: {str(manifest['tensor_dump_saved']).lower()}",
            f"- npz_created: {str(manifest['npz_created']).lower()}",
            f"- original_diffsbdd_source_modified: {str(manifest['original_diffsbdd_source_modified']).lower()}",
            f"- forbidden_artifacts_created: {str(manifest['forbidden_artifacts_created']).lower()}",
            "",
            "## Decision",
            f"- real_covalent_backward_smoke_passed: {str(manifest['real_covalent_backward_smoke_passed']).lower()}",
            f"- real_covalent_backward_contract_proven: {str(manifest['real_covalent_backward_contract_proven']).lower()}",
            "- real_covalent_single_optimizer_step_smoke_allowed: "
            f"{str(manifest['real_covalent_single_optimizer_step_smoke_allowed']).lower()}",
            f"- all_checks_passed: {str(manifest['all_checks_passed']).lower()}",
            f"- recommended_next_step: {manifest['recommended_next_step']}",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def run(device: str = "cpu") -> int:
    result = build_real_covalent_backward_smoke_v0(device=device)
    write_json(result["manifest"], MANIFEST_JSON)
    write_csv(result["grad_table_rows"], GRAD_TABLE_CSV, GRAD_TABLE_COLUMNS)
    write_csv(build_report_rows(result), REPORT_CSV, REPORT_COLUMNS)
    write_summary(result, SUMMARY_MD)
    if result["manifest"]["all_checks_passed"]:
        print("real_covalent_backward_smoke_v0_passed")
        return 0
    print("real_covalent_backward_smoke_v0_blocked")
    print(json.dumps(result["manifest"]["blocking_reasons"], indent=2, sort_keys=True))
    return 1


if __name__ == "__main__":
    raise SystemExit(run())
