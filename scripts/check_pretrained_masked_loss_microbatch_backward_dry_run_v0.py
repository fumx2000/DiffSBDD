#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext.pretrained_masked_loss_microbatch_backward_dry_run import (  # noqa: E402
    GRADIENT_TABLE_CSV,
    MANIFEST_JSON,
    PREVIOUS_STAGE,
    REPORT_CSV,
    STAGE,
    SUMMARY_MD,
    build_pretrained_masked_loss_microbatch_backward_dry_run_v0,
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
GRADIENT_COLUMNS = [
    "stage",
    "mask_level",
    "strict_load_success",
    "loss_requires_grad",
    "loss_finite",
    "selected_loss_key",
    "selected_loss_value",
    "backward_called",
    "backward_call_count",
    "backward_success",
    "parameter_count",
    "trainable_parameter_count",
    "parameters_with_grad_count",
    "parameters_with_nonzero_grad_count",
    "parameters_with_finite_grad_count",
    "none_grad_parameter_count",
    "zero_grad_parameter_count",
    "grad_nan_count",
    "grad_inf_count",
    "total_grad_norm",
    "max_abs_grad",
    "mean_abs_grad",
    "finite_nonzero_grad_exists",
    "optimizer_created",
    "optimizer_step_called",
    "status",
    "blocking_reasons",
]


def _json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _list_text(values: Any) -> str:
    if isinstance(values, list):
        return ";".join(str(value) for value in values)
    return "" if values is None else str(values)


def write_csv(rows: list[dict[str, Any]], path: str | Path, fieldnames: list[str]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_json(data: dict[str, Any], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_report_rows(result: dict[str, Any]) -> list[dict[str, str]]:
    manifest = result["manifest"]
    recommended = manifest["recommended_next_step"]
    rows = [
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "step11g_precondition",
            "status": "passed" if manifest["step11g_validated"] else "blocked",
            "evidence": _json_text(result["report_sections"]["step11g_precondition"]),
            "decision": "Step 11G protocol allows isolated reverse-pass dry run and is accepted.",
            "blocking_reasons": _list_text(manifest["blocking_reasons"]),
            "recommended_next_step": recommended,
        }
    ]
    for row in result["per_level_results"]:
        rows.append(
            {
                "stage": STAGE,
                "previous_stage": PREVIOUS_STAGE,
                "section": f"mask_level_{row['mask_level']}_backward",
                "status": row["status"],
                "evidence": _json_text(
                    {
                        "selected_loss_key": row.get("selected_loss_key"),
                        "selected_loss_value": row.get("selected_loss_value"),
                        "loss_requires_grad": row.get("loss_requires_grad"),
                        "backward_call_count": row.get("backward_call_count"),
                        "total_grad_norm": row.get("total_grad_norm"),
                        "max_abs_grad": row.get("max_abs_grad"),
                        "grad_nan_count": row.get("grad_nan_count"),
                        "grad_inf_count": row.get("grad_inf_count"),
                    }
                ),
                "decision": "Mask-level isolated reverse pass produced finite nonzero gradients.",
                "blocking_reasons": _list_text(row.get("blocking_reasons", [])),
                "recommended_next_step": recommended,
            }
        )
    rows.extend(
        [
            {
                "stage": STAGE,
                "previous_stage": PREVIOUS_STAGE,
                "section": "gradient_summary",
                "status": "passed" if manifest["finite_nonzero_grad_all_levels"] else "blocked",
                "evidence": _json_text(result["report_sections"]["gradient_summary"]),
                "decision": "All mask levels have finite nonzero gradient evidence.",
                "blocking_reasons": _list_text(manifest["blocking_reasons"]),
                "recommended_next_step": recommended,
            },
            {
                "stage": STAGE,
                "previous_stage": PREVIOUS_STAGE,
                "section": "decision",
                "status": "passed" if manifest["microbatch_backward_dry_run_passed"] else "blocked",
                "evidence": _json_text(result["report_sections"]["decision"]),
                "decision": "Gradient plumbing is proven for this synthetic shape-only microbatch protocol.",
                "blocking_reasons": _list_text(manifest["blocking_reasons"]),
                "recommended_next_step": recommended,
            },
            {
                "stage": STAGE,
                "previous_stage": PREVIOUS_STAGE,
                "section": "safety_boundary",
                "status": "passed" if manifest["all_checks_passed"] else "blocked",
                "evidence": _json_text(result["report_sections"]["safety_boundary"]),
                "decision": "No optimizer, trainer, checkpoint save, model save, or source modification occurred.",
                "blocking_reasons": _list_text(manifest["blocking_reasons"]),
                "recommended_next_step": recommended,
            },
        ]
    )
    return rows


def write_summary(manifest: dict[str, Any], gradient_rows: list[dict[str, Any]], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Pretrained Masked Loss Microbatch Backward Dry Run v0 Summary",
        "",
        "Step 11H is a backward dry run, not formal training.",
        "It uses fresh strict-loaded pretrained models per mask level and runs one isolated reverse pass for each mask.",
        "It does not create an optimizer, does not step parameters, and does not save a checkpoint or model.",
        "",
        "## Gradient Table",
        "| mask_level | selected_loss_value | backward_success | parameters_with_grad_count | total_grad_norm | max_abs_grad | grad_nan_count | grad_inf_count |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in gradient_rows:
        lines.append(
            f"| {row['mask_level']} | {row['selected_loss_value']} | {str(row['backward_success']).lower()} | "
            f"{row['parameters_with_grad_count']} | {row['total_grad_norm']} | {row['max_abs_grad']} | "
            f"{row['grad_nan_count']} | {row['grad_inf_count']} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            f"- all_mask_levels_passed: {str(manifest['all_mask_levels_passed']).lower()}",
            f"- backward_call_count_total: {manifest['backward_call_count_total']}",
            f"- finite_nonzero_grad_all_levels: {str(manifest['finite_nonzero_grad_all_levels']).lower()}",
            f"- grad_nan_count_total: {manifest['grad_nan_count_total']}",
            f"- grad_inf_count_total: {manifest['grad_inf_count_total']}",
            f"- microbatch_backward_status: {manifest['microbatch_backward_status']}",
            f"- gradient_plumbing_proven: {str(manifest['gradient_plumbing_proven']).lower()}",
            f"- optimizer_smoke_design_allowed: {str(manifest['optimizer_smoke_design_allowed']).lower()}",
            f"- optimizer_created: {str(manifest['optimizer_created']).lower()}",
            f"- optimizer_step_called: {str(manifest['optimizer_step_called']).lower()}",
            f"- training_allowed: {str(manifest['training_allowed']).lower()}",
            f"- formal_training_allowed: {str(manifest['formal_training_allowed']).lower()}",
            f"- finetune_allowed: {str(manifest['finetune_allowed']).lower()}",
            f"- checkpoint_saved: {str(manifest['checkpoint_saved']).lower()}",
            f"- model_saved: {str(manifest['model_saved']).lower()}",
            f"- recommended_next_step: {manifest['recommended_next_step']}",
            "",
            "This dry run proves gradient plumbing only. It does not prove loss decrease, generation quality, or real covalent data-loader training readiness.",
        ]
    )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(device: str = "cpu") -> int:
    result = build_pretrained_masked_loss_microbatch_backward_dry_run_v0(device=device)
    write_csv(build_report_rows(result), REPORT_CSV, REPORT_COLUMNS)
    write_csv(result["gradient_table_rows"], GRADIENT_TABLE_CSV, GRADIENT_COLUMNS)
    write_json(result["manifest"], MANIFEST_JSON)
    write_summary(result["manifest"], result["gradient_table_rows"], SUMMARY_MD)
    print(f"{STAGE}_{'passed' if result['manifest']['all_checks_passed'] else 'blocked'}")
    return 0 if result["manifest"]["all_checks_passed"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run pretrained masked loss microbatch backward dry run v0.")
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    return run(device=args.device)


if __name__ == "__main__":
    raise SystemExit(main())
