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

from covalent_ext.checkpoint_compatible_pretrained_load_smoke import (  # noqa: E402
    CHECKPOINT_PATH,
    CONFIG_PREVIEW_PATH,
    DIAGNOSTICS_JSON,
    MANIFEST_JSON,
    PREVIOUS_STAGE,
    REPORT_CSV,
    STAGE,
    SUMMARY_MD,
    build_checkpoint_compatible_pretrained_load_smoke_v0,
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


def _checkpoint_evidence(section: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_sha256": section["checkpoint_sha256"],
        "checkpoint_size_bytes": section["checkpoint_size_bytes"],
        "checkpoint_loaded": section["checkpoint_loaded"],
        "has_state_dict": section["has_state_dict"],
        "has_hyper_parameters": section["has_hyper_parameters"],
        "state_dict_key_count": section["state_dict_key_count"],
        "checkpoint_target_fields": section["checkpoint_target_fields"],
    }


def _model_evidence(section: dict[str, Any]) -> dict[str, Any]:
    return {
        "model_instantiated": section["model_instantiated"],
        "model_class": section["model_class"],
        "requested_device": section["requested_device"],
        "resolved_device": section["resolved_device"],
        "model_state_dict_key_count": section["model_state_dict_key_count"],
        "trainable_parameter_count": section["trainable_parameter_count"],
        "shape_match_ratio_vs_checkpoint": section["shape_match_ratio_vs_checkpoint"],
    }


def build_report_rows(result: dict[str, Any]) -> list[dict[str, str]]:
    manifest = result["manifest"]
    sections = result["report_sections"]
    recommended = manifest["recommended_next_step"]
    blockers = manifest["blocking_reasons"]
    checkpoint = sections["checkpoint_state_dict"]
    model = sections["model_instantiation"]
    pre_load = sections["pre_load_shape_match"]
    strict_load = sections["strict_load"]
    forward = sections["loaded_model_forward_smoke"]
    decision = sections["decision"]
    safety = sections["safety_boundary"]
    return [
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "step11d_precondition",
            "status": "passed" if manifest["step11d_validated"] else "blocked",
            "evidence": _json_text(sections["step11d"]),
            "decision": "Step 11D checkpoint-compatible wrapper outputs are accepted.",
            "blocking_reasons": "",
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "checkpoint_state_dict",
            "status": "passed" if checkpoint["has_state_dict"] else "blocked",
            "evidence": _json_text(_checkpoint_evidence(checkpoint)),
            "decision": "Checkpoint payload and state_dict are readable.",
            "blocking_reasons": _list_text(checkpoint["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "checkpoint_compatible_model_instantiation",
            "status": "passed" if model["model_instantiated"] else "blocked",
            "evidence": _json_text(_model_evidence(model)),
            "decision": "Checkpoint-compatible model is instantiated in memory.",
            "blocking_reasons": _list_text(model["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "pre_load_shape_match",
            "status": "passed" if pre_load.get("pre_load_shape_matched_ratio") == 1.0 else "blocked",
            "evidence": _json_text(pre_load),
            "decision": "Model and checkpoint state_dict shapes match before strict load.",
            "blocking_reasons": _list_text(blockers),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "strict_load",
            "status": "passed" if strict_load["strict_load_success"] else "blocked",
            "evidence": _json_text(
                {
                    "strict_load_attempted": strict_load["strict_load_attempted"],
                    "strict_load_success": strict_load["strict_load_success"],
                    "missing_keys_count": strict_load["missing_keys_count"],
                    "unexpected_keys_count": strict_load["unexpected_keys_count"],
                    "incompatible_shape_count": strict_load["incompatible_shape_count"],
                    "loaded_parameter_key_count": strict_load["loaded_parameter_key_count"],
                    "loaded_parameter_numel_total": strict_load["loaded_parameter_numel_total"],
                }
            ),
            "decision": "Strict load proves checkpoint tensor compatibility when all counts are zero.",
            "blocking_reasons": _list_text(strict_load["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "loaded_model_forward_smoke",
            "status": "passed" if forward["forward_smoke_success"] else "blocked",
            "evidence": _json_text(forward),
            "decision": "Loaded model no-grad forward smoke must be finite before next masked-loss smoke.",
            "blocking_reasons": _list_text(forward["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "decision",
            "status": "passed" if manifest["all_checks_passed"] else "blocked",
            "evidence": _json_text(decision),
            "decision": "Pretrained masked loss smoke is allowed next, but this step does not execute it.",
            "blocking_reasons": _list_text(blockers),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "safety_boundary",
            "status": "passed" if manifest["all_checks_passed"] else "blocked",
            "evidence": _json_text(safety),
            "decision": "No training, optimizer, model save, checkpoint save, or source modification occurred.",
            "blocking_reasons": _list_text(blockers),
            "recommended_next_step": recommended,
        },
    ]


def write_summary(manifest: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Checkpoint-Compatible Pretrained Load Smoke v0 Summary",
        "",
        "Step 11E is a checkpoint-compatible pretrained load smoke, not training.",
        "It strict-loads the pretrained state_dict into the checkpoint-compatible in-memory model and runs a no-grad forward smoke.",
        "It does not run masked loss smoke, optimizer steps, formal training, or fine-tuning.",
        "",
        "## Strict Load",
        f"- checkpoint_sha256: {manifest['checkpoint_sha256']}",
        f"- checkpoint_size_bytes: {manifest['checkpoint_size_bytes']}",
        f"- checkpoint_state_dict_key_count: {manifest['checkpoint_state_dict_key_count']}",
        f"- model_state_dict_key_count: {manifest['model_state_dict_key_count']}",
        f"- pre_load_shape_matched_ratio: {manifest['pre_load_shape_matched_ratio']}",
        f"- strict_load_attempted: {str(manifest['strict_load_attempted']).lower()}",
        f"- strict_load_success: {str(manifest['strict_load_success']).lower()}",
        f"- missing_keys_count: {manifest['missing_keys_count']}",
        f"- unexpected_keys_count: {manifest['unexpected_keys_count']}",
        f"- incompatible_shape_count: {manifest['incompatible_shape_count']}",
        f"- pretrained_weights_loaded: {str(manifest['pretrained_weights_loaded']).lower()}",
        f"- pretrained_base_integration_proven: {str(manifest['pretrained_base_integration_proven']).lower()}",
        "",
        "## Forward Smoke",
        f"- forward_smoke_attempted: {str(manifest['forward_smoke_attempted']).lower()}",
        f"- forward_smoke_success: {str(manifest['forward_smoke_success']).lower()}",
        f"- output_finite: {str(manifest['output_finite']).lower()}",
        f"- nan_count: {manifest['nan_count']}",
        f"- inf_count: {manifest['inf_count']}",
        "",
        "## Boundary",
        f"- pretrained_masked_loss_smoke_allowed: {str(manifest['pretrained_masked_loss_smoke_allowed']).lower()}",
        f"- masked_loss_smoke_allowed_this_step: {str(manifest['masked_loss_smoke_allowed']).lower()}",
        f"- training_allowed: {str(manifest['training_allowed']).lower()}",
        f"- formal_training_allowed: {str(manifest['formal_training_allowed']).lower()}",
        f"- finetune_allowed: {str(manifest['finetune_allowed']).lower()}",
        f"- checkpoint_saved: {str(manifest['checkpoint_saved']).lower()}",
        f"- model_saved: {str(manifest['model_saved']).lower()}",
        f"- recommended_next_step: {manifest['recommended_next_step']}",
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(device: str = "cpu", checkpoint_path: str | Path = CHECKPOINT_PATH, config_preview_path: str | Path = CONFIG_PREVIEW_PATH) -> int:
    result = build_checkpoint_compatible_pretrained_load_smoke_v0(
        device=device,
        checkpoint_path=checkpoint_path,
        config_preview_path=config_preview_path,
    )
    write_csv(build_report_rows(result), REPORT_CSV, REPORT_COLUMNS)
    write_json(result["manifest"], MANIFEST_JSON)
    write_json(result["diagnostics"], DIAGNOSTICS_JSON)
    write_summary(result["manifest"], SUMMARY_MD)
    print(f"{STAGE}_{'passed' if result['manifest']['all_checks_passed'] else 'blocked'}")
    return 0 if result["manifest"]["all_checks_passed"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run checkpoint-compatible pretrained load smoke v0.")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--checkpoint-path", default=str(CHECKPOINT_PATH))
    parser.add_argument("--config-preview-path", default=str(CONFIG_PREVIEW_PATH))
    args = parser.parse_args()
    return run(args.device, args.checkpoint_path, args.config_preview_path)


if __name__ == "__main__":
    raise SystemExit(main())
