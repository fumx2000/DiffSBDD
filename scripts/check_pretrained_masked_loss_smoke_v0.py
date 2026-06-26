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

from covalent_ext.pretrained_masked_loss_smoke import (  # noqa: E402
    CHECKPOINT_PATH,
    CONFIG_PREVIEW_PATH,
    LOSS_TABLE_CSV,
    MANIFEST_JSON,
    PREVIOUS_STAGE,
    REPORT_CSV,
    STAGE,
    SUMMARY_MD,
    build_pretrained_masked_loss_smoke_v0,
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
LOSS_TABLE_COLUMNS = [
    "stage",
    "mask_level",
    "candidate_inputs_built",
    "forward_success",
    "loss_hook_success",
    "finite_loss",
    "selected_primary_loss_key",
    "selected_primary_loss_value",
    "nan_count",
    "inf_count",
    "synthetic_mask_loss_adapter_used",
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
    sections = result["report_sections"]
    recommended = manifest["recommended_next_step"]
    rows = [
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "step11e_precondition",
            "status": "passed" if manifest["step11e_validated"] else "blocked",
            "evidence": _json_text(sections["step11e_precondition"]),
            "decision": "Step 11E strict-load pretrained base evidence is accepted.",
            "blocking_reasons": _list_text(manifest["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "pretrained_model_load",
            "status": "passed" if manifest["strict_load_success"] else "blocked",
            "evidence": _json_text(sections["pretrained_model_load"]),
            "decision": "Checkpoint-compatible pretrained model is strict-loaded in memory for smoke only.",
            "blocking_reasons": _list_text(manifest["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "synthetic_input_contract",
            "status": "passed" if manifest["synthetic_shape_smoke_only"] else "blocked",
            "evidence": _json_text(sections["synthetic_input_contract"]),
            "decision": "Inputs use a synthetic 10D shape contract; this is not training data or a quality claim.",
            "blocking_reasons": _list_text(manifest["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
    ]
    for item in result["per_level_results"]:
        rows.append(
            {
                "stage": STAGE,
                "previous_stage": PREVIOUS_STAGE,
                "section": f"mask_level_{item['mask_level']}",
                "status": item["status"],
                "evidence": _json_text(
                    {
                        "candidate_inputs_built": item["candidate_inputs_built"],
                        "forward_success": item["forward_success"],
                        "loss_hook_success": item["loss_hook_success"],
                        "finite_loss": item["finite_loss"],
                        "selected_primary_loss_key": item["selected_primary_loss_key"],
                        "selected_primary_loss_value": item["selected_primary_loss_value"],
                        "mask_tensor_summary": item["mask_tensor_summary"],
                    }
                ),
                "decision": "Mask-level pretrained no-grad masked loss smoke is finite.",
                "blocking_reasons": _list_text(item["blocking_reasons"]),
                "recommended_next_step": recommended,
            }
        )
    rows.extend(
        [
            {
                "stage": STAGE,
                "previous_stage": PREVIOUS_STAGE,
                "section": "decision",
                "status": "passed" if manifest["pretrained_masked_loss_smoke_passed"] else "blocked",
                "evidence": _json_text(sections["decision"]),
                "decision": "Microbatch dry run design is allowed only when all four mask levels pass finite smoke.",
                "blocking_reasons": _list_text(manifest["blocking_reasons"]),
                "recommended_next_step": recommended,
            },
            {
                "stage": STAGE,
                "previous_stage": PREVIOUS_STAGE,
                "section": "safety_boundary",
                "status": "passed" if manifest["all_checks_passed"] else "blocked",
                "evidence": _json_text(sections["safety_boundary"]),
                "decision": "No parameter update, trainer call, checkpoint save, model save, or source modification occurred.",
                "blocking_reasons": _list_text(manifest["blocking_reasons"]),
                "recommended_next_step": recommended,
            },
        ]
    )
    return rows


def write_summary(manifest: dict[str, Any], loss_rows: list[dict[str, Any]], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Pretrained Masked Loss Smoke v0 Summary",
        "",
        "Step 11F is a pretrained masked loss smoke, not training.",
        "It strict-loads the checkpoint-compatible pretrained model and runs no-grad masked loss smoke over A/B/B2/C.",
        "It uses a synthetic 10D shape-only contract, so it does not prove generation quality or loss decrease.",
        "",
        "## Pretrained Base",
        f"- checkpoint_sha256: {manifest['checkpoint_sha256']}",
        f"- pretrained_weights_loaded: {str(manifest['pretrained_weights_loaded']).lower()}",
        f"- pretrained_base_integration_proven: {str(manifest['pretrained_base_integration_proven']).lower()}",
        f"- strict_load_success: {str(manifest['strict_load_success']).lower()}",
        "",
        "## Mask Levels",
        "| mask_level | selected_primary_loss_key | selected_primary_loss_value | finite_loss | status |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for row in loss_rows:
        lines.append(
            f"| {row['mask_level']} | {row['selected_primary_loss_key']} | "
            f"{row['selected_primary_loss_value']} | {str(row['finite_loss']).lower()} | {row['status']} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            f"- synthetic_shape_smoke_only: {str(manifest['synthetic_shape_smoke_only']).lower()}",
            f"- feature_semantics_known: {str(manifest['feature_semantics_known']).lower()}",
            f"- synthetic_mask_loss_adapter_used: {str(manifest['synthetic_mask_loss_adapter_used']).lower()}",
            f"- all_mask_levels_passed: {str(manifest['all_mask_levels_passed']).lower()}",
            f"- pretrained_masked_loss_smoke_passed: {str(manifest['pretrained_masked_loss_smoke_passed']).lower()}",
            f"- microbatch_dry_run_allowed: {str(manifest['microbatch_dry_run_allowed']).lower()}",
            f"- training_allowed: {str(manifest['training_allowed']).lower()}",
            f"- formal_training_allowed: {str(manifest['formal_training_allowed']).lower()}",
            f"- finetune_allowed: {str(manifest['finetune_allowed']).lower()}",
            f"- optimizer_allowed: {str(manifest['optimizer_allowed']).lower()}",
            f"- checkpoint_saved: {str(manifest['checkpoint_saved']).lower()}",
            f"- model_saved: {str(manifest['model_saved']).lower()}",
            f"- recommended_next_step: {manifest['recommended_next_step']}",
        ]
    )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(
    device: str = "cpu",
    checkpoint_path: str | Path = CHECKPOINT_PATH,
    config_preview_path: str | Path = CONFIG_PREVIEW_PATH,
) -> int:
    result = build_pretrained_masked_loss_smoke_v0(
        device=device,
        checkpoint_path=checkpoint_path,
        config_preview_path=config_preview_path,
    )
    write_csv(build_report_rows(result), REPORT_CSV, REPORT_COLUMNS)
    write_csv(result["loss_table_rows"], LOSS_TABLE_CSV, LOSS_TABLE_COLUMNS)
    write_json(result["manifest"], MANIFEST_JSON)
    write_summary(result["manifest"], result["loss_table_rows"], SUMMARY_MD)
    print(f"{STAGE}_{'passed' if result['manifest']['all_checks_passed'] else 'blocked'}")
    return 0 if result["manifest"]["all_checks_passed"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run pretrained masked loss smoke v0.")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--checkpoint-path", default=str(CHECKPOINT_PATH))
    parser.add_argument("--config-preview-path", default=str(CONFIG_PREVIEW_PATH))
    args = parser.parse_args()
    return run(args.device, args.checkpoint_path, args.config_preview_path)


if __name__ == "__main__":
    raise SystemExit(main())
