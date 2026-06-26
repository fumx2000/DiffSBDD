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

from covalent_ext.pretrained_checkpoint_load_smoke import (  # noqa: E402
    CHECKPOINT_PATH,
    MANIFEST_JSON,
    PREVIOUS_STAGE,
    REPORT_CSV,
    STAGE,
    SUMMARY_MD,
    build_pretrained_checkpoint_load_smoke_v0,
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


def write_csv(rows: list[dict[str, str]], path: str | Path, fieldnames: list[str]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(data: dict[str, Any], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_report_rows(result: dict[str, Any]) -> list[dict[str, str]]:
    manifest = result["manifest"]
    sections = result["sections"]
    recommended = manifest["recommended_next_step"]
    return [
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "step10x_review_precondition",
            "status": "passed" if sections["step10x"]["step10x_review_passed"] else "blocked",
            "evidence": _json_text(sections["step10x"]),
            "decision": "Step 10X review evidence accepted as precondition.",
            "blocking_reasons": _list_text(sections["step10x"]["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "pretrained_checkpoint_location",
            "status": sections["location"]["status"],
            "evidence": _json_text(sections["location"]),
            "decision": "Use existing local pretrained checkpoint only.",
            "blocking_reasons": _list_text(sections["location"]["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "checkpoint_payload_inspection",
            "status": "passed" if manifest["checkpoint_loaded"] and manifest["state_dict_key_count"] > 0 else "blocked",
            "evidence": _json_text(
                {
                    "checkpoint_payload_type": manifest["checkpoint_payload_type"],
                    "checkpoint_top_level_keys": manifest["checkpoint_top_level_keys"],
                    "has_state_dict": manifest["has_state_dict"],
                    "state_dict_key_count": manifest["state_dict_key_count"],
                }
            ),
            "decision": "Checkpoint payload can be inspected and state_dict can be extracted.",
            "blocking_reasons": _list_text(sections["payload"].get("blocking_reasons", [])),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "state_dict_key_normalization",
            "status": "passed" if manifest["candidate_variant_count"] > 0 else "blocked",
            "evidence": _json_text(sections["normalization"]),
            "decision": "Evaluate conservative prefix-stripping variants without changing tensor values.",
            "blocking_reasons": "",
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "model_instantiation",
            "status": "passed" if manifest["model_instantiated"] else "blocked",
            "evidence": _json_text(
                {
                    "model_class": manifest["model_class"],
                    "requested_device": manifest["requested_device"],
                    "resolved_device": manifest["resolved_device"],
                    "cuda_available": manifest["cuda_available"],
                    "cuda_device_name": manifest["cuda_device_name"],
                }
            ),
            "decision": "Fresh in-memory DiffSBDD model instantiated for load compatibility smoke.",
            "blocking_reasons": _list_text(sections["instantiation"].get("blocking_reasons", [])),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "pretrained_state_dict_load",
            "status": "passed" if manifest["pretrained_partial_shape_load_success"] else "blocked",
            "evidence": _json_text(
                {
                    "best_variant_name": manifest["best_variant_name"],
                    "strict_load_success": manifest["strict_load_success"],
                    "nonstrict_load_success": manifest["nonstrict_load_success"],
                    "matched_key_count": manifest["matched_key_count"],
                    "shape_matched_key_count": manifest["shape_matched_key_count"],
                    "shape_matched_ratio": manifest["shape_matched_ratio"],
                    "missing_key_count": manifest["missing_key_count"],
                    "unexpected_key_count": manifest["unexpected_key_count"],
                    "incompatible_shape_count": manifest["incompatible_shape_count"],
                    "pretrained_partial_shape_load_success": manifest["pretrained_partial_shape_load_success"],
                    "pretrained_full_architecture_compatible": manifest["pretrained_full_architecture_compatible"],
                    "shape_mismatch_detected": manifest["shape_mismatch_detected"],
                    "architecture_config_mismatch_suspected": manifest[
                        "architecture_config_mismatch_suspected"
                    ],
                    "pretrained_weights_loaded": manifest["pretrained_weights_loaded"],
                }
            ),
            "decision": (
                "Checkpoint is readable and partially loadable, but architecture/config mismatch prevents "
                "claiming pretrained base model integration."
            ),
            "blocking_reasons": _list_text(sections["load"]["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "no_grad_forward_smoke",
            "status": "passed" if manifest["forward_smoke_success"] else "blocked",
            "evidence": _json_text(
                {
                    "forward_smoke_attempted": manifest["forward_smoke_attempted"],
                    "forward_smoke_success": manifest["forward_smoke_success"],
                    "output_shape_summary": manifest["output_shape_summary"],
                    "output_finite": manifest["output_finite"],
                    "nan_count": manifest["nan_count"],
                    "inf_count": manifest["inf_count"],
                }
            ),
            "decision": "No-grad eval forward smoke validates finite output after pretrained load.",
            "blocking_reasons": _list_text(sections["forward"]["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "safety_boundary",
            "status": "passed" if manifest["all_checks_passed"] else "blocked",
            "evidence": _json_text(
                {
                    "backward_called": manifest["backward_called"],
                    "optimizer_created": manifest["optimizer_created"],
                    "optimizer_step_called": manifest["optimizer_step_called"],
                    "training_step_called": manifest["training_step_called"],
                    "trainer_fit_called": manifest["trainer_fit_called"],
                    "checkpoint_saved": manifest["checkpoint_saved"],
                    "model_saved": manifest["model_saved"],
                    "formal_training_executed": manifest["formal_training_executed"],
                    "real_finetune_executed": manifest["real_finetune_executed"],
                    "original_source_files_modified": manifest["original_source_files_modified"],
                    "forbidden_artifacts_created": manifest["forbidden_artifacts_created"],
                    "pretrained_partial_shape_load_success": manifest["pretrained_partial_shape_load_success"],
                    "pretrained_full_architecture_compatible": manifest[
                        "pretrained_full_architecture_compatible"
                    ],
                    "pretrained_weights_loaded": manifest["pretrained_weights_loaded"],
                }
            ),
            "decision": "Smoke stayed inside load/forward-only boundary.",
            "blocking_reasons": _list_text(manifest["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
    ]


def write_summary(manifest: dict[str, Any], output_md: str | Path) -> None:
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Pretrained Checkpoint Load Smoke v0 Summary",
        "",
        "Step 11A is a pretrained DiffSBDD checkpoint load compatibility smoke, not training.",
        f"It reads checkpoint: `{manifest['pretrained_checkpoint_path']}`.",
        f"Checkpoint present: {manifest['pretrained_checkpoint_present']}",
        f"Checkpoint sha256: `{manifest['pretrained_checkpoint_sha256']}`",
        f"Checkpoint size bytes: {manifest['pretrained_checkpoint_size_bytes']}",
        "",
        "## Payload Inspection",
        f"- payload type: {manifest['checkpoint_payload_type']}",
        f"- top-level keys: {', '.join(manifest['checkpoint_top_level_keys'])}",
        f"- has_state_dict: {manifest['has_state_dict']}",
        f"- state_dict_key_count: {manifest['state_dict_key_count']}",
        f"- pretrained_checkpoint_readable: {manifest['pretrained_checkpoint_readable']}",
        f"- pretrained_state_dict_extracted: {manifest['pretrained_state_dict_extracted']}",
        "",
        "## Load Compatibility",
        f"- model_class: {manifest['model_class']}",
        f"- requested_device: {manifest['requested_device']}",
        f"- resolved_device: {manifest['resolved_device']}",
        f"- cuda_available: {manifest['cuda_available']}",
        f"- cuda_device_name: {manifest['cuda_device_name']}",
        f"- best_variant_name: {manifest['best_variant_name']}",
        f"- strict_load_success: {manifest['strict_load_success']}",
        f"- nonstrict_load_success: {manifest['nonstrict_load_success']} only for compatible tensors",
        f"- matched_key_count: {manifest['matched_key_count']}",
        f"- shape_matched_key_count: {manifest['shape_matched_key_count']}",
        f"- shape_matched_ratio: {manifest['shape_matched_ratio']}",
        f"- missing_key_count: {manifest['missing_key_count']}",
        f"- unexpected_key_count: {manifest['unexpected_key_count']}",
        f"- incompatible_shape_count: {manifest['incompatible_shape_count']}",
        f"- pretrained_partial_shape_load_success: {manifest['pretrained_partial_shape_load_success']}",
        f"- pretrained_full_architecture_compatible: {manifest['pretrained_full_architecture_compatible']}",
        f"- pretrained_effective_load_status: {manifest['pretrained_effective_load_status']}",
        f"- pretrained_weights_loaded: {manifest['pretrained_weights_loaded']}",
        f"- shape_mismatch_detected: {manifest['shape_mismatch_detected']}",
        f"- architecture_config_mismatch_suspected: {manifest['architecture_config_mismatch_suspected']}",
        "",
        "Conclusion: the current model configuration and checkpoint architecture are clearly mismatched.",
        "This cannot be claimed as successful pretrained base model integration.",
        "Do not proceed to pretrained masked loss smoke from this result.",
        "The next step must reconcile the checkpoint architecture/configuration.",
        "",
        "## No-Grad Forward Smoke",
        f"- forward_smoke_attempted: {manifest['forward_smoke_attempted']}",
        f"- forward_smoke_success: {manifest['forward_smoke_success']}",
        f"- output_finite: {manifest['output_finite']}",
        f"- output_shape_summary: {json.dumps(manifest['output_shape_summary'], sort_keys=True)}",
        "",
        "## Safety",
        f"- backward_called: {manifest['backward_called']}",
        f"- optimizer_created: {manifest['optimizer_created']}",
        f"- optimizer_step_called: {manifest['optimizer_step_called']}",
        f"- training_step_called: {manifest['training_step_called']}",
        f"- trainer_fit_called: {manifest['trainer_fit_called']}",
        f"- checkpoint_saved: {manifest['checkpoint_saved']}",
        f"- model_saved: {manifest['model_saved']}",
        f"- formal_training_executed: {manifest['formal_training_executed']}",
        f"- real_finetune_executed: {manifest['real_finetune_executed']}",
        f"- original_source_files_modified: {manifest['original_source_files_modified']}",
        f"- forbidden_artifacts_created: {manifest['forbidden_artifacts_created']}",
        "",
        "This step does not prove generation quality or loss improvement.",
        f"all_checks_passed_meaning: {manifest['all_checks_passed_meaning']}",
        "",
        "## Recommendation",
        f"- {manifest['recommended_next_step']}",
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check pretrained DiffSBDD checkpoint load compatibility.")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--checkpoint-path", default=str(CHECKPOINT_PATH))
    return parser.parse_args()


def run(device: str = "auto", checkpoint_path: str | Path = CHECKPOINT_PATH) -> int:
    result = build_pretrained_checkpoint_load_smoke_v0(device=device, checkpoint_path=checkpoint_path)
    manifest = result["manifest"]
    write_csv(build_report_rows(result), REPORT_CSV, REPORT_COLUMNS)
    write_json(manifest, MANIFEST_JSON)
    write_summary(manifest, SUMMARY_MD)
    return 0 if manifest["all_checks_passed"] else 1


def main() -> int:
    args = parse_args()
    code = run(device=args.device, checkpoint_path=args.checkpoint_path)
    print("pretrained_checkpoint_load_smoke_v0_passed" if code == 0 else "pretrained_checkpoint_load_smoke_v0_blocked")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
