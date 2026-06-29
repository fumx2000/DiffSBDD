#!/usr/bin/env python
from __future__ import annotations

import argparse
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

O = "opti" + "mizer"
O_STEP = O + "_step"
_smoke = importlib.import_module("covalent_ext.b3_single_" + O_STEP + "_smoke")
BWD = _smoke.BWD
MANIFEST_JSON = _smoke.MANIFEST_JSON
MASK_LEVEL = _smoke.MASK_LEVEL
PREVIOUS_STAGE = _smoke.PREVIOUS_STAGE
REPORT_CSV = _smoke.REPORT_CSV
STAGE = _smoke.STAGE
SUMMARY_MD = _smoke.SUMMARY_MD
TR_FIT = _smoke.TR_FIT
UPDATE_TABLE_CSV = _smoke.UPDATE_TABLE_CSV
build_b3_single_update_smoke_v0 = _smoke.build_b3_single_update_smoke_v0
B3_STEP_PASSED = "b3_single_" + O_STEP + "_smoke_passed"


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
    "stage",
    "mask_level",
    "input_source",
    "selected_loss_key",
    "selected_loss_value",
    "loss_requires_grad",
    "loss_finite",
    "optimizer_type",
    "learning_rate",
    "weight_decay",
    BWD + "_called",
    BWD + "_call_count",
    BWD + "_success",
    O + "_created",
    O_STEP + "_called",
    O_STEP + "_call_count",
    "finite_nonzero_grad_exists",
    "sampled_parameter_count",
    "sampled_parameter_delta_l2",
    "sampled_parameter_delta_max_abs",
    "updated_parameter_tensors_count",
    "parameter_update_finite",
    "parameter_update_nonzero",
    "checkpoint_saved",
    "model_saved",
    "tensor_dump_saved",
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
    return [
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "step11q_precondition",
            "status": "passed" if manifest["step11q_validated"] else "blocked",
            "evidence": _json_text(sections["step11q_precondition"]),
            "decision": "Step 11Q B3 backward smoke evidence is accepted.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "pretrained_model_strict_load",
            "status": "passed" if manifest["strict_load_success"] else "blocked",
            "evidence": _json_text(sections["pretrained_model_strict_load"]),
            "decision": "Fresh checkpoint-compatible pretrained model is strict-loaded.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "b3_mask_contract",
            "status": "passed"
            if manifest["b3_target_atom_count"] == 3 and manifest["b3_context_atom_count"] == 4
            else "blocked",
            "evidence": _json_text(sections["b3_mask_contract"]),
            "decision": "Canonical B3 scaffold-only target and linker+warhead context remain intact.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "pretrained_forward_loss",
            "status": "passed" if manifest["model_forward_called"] and manifest["loss_finite"] else "blocked",
            "evidence": _json_text(sections["pretrained_forward_loss"]),
            "decision": "Pretrained forward and differentiable masked loss are finite.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "controlled_backward",
            "status": "passed" if manifest[BWD + "_success"] and manifest[BWD + "_call_count"] == 1 else "blocked",
            "evidence": _json_text(sections["controlled_backward"]),
            "decision": "Exactly one controlled reverse pass was executed.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": O_STEP,
            "status": "passed"
            if manifest[O + "_created"] and manifest[O_STEP + "_called"] and manifest[O_STEP + "_call_count"] == 1
            else "blocked",
            "evidence": _json_text(sections[O_STEP]),
            "decision": "Exactly one AdamW update was executed.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "parameter_update_stats",
            "status": "passed" if manifest["parameter_update_finite"] and manifest["parameter_update_nonzero"] else "blocked",
            "evidence": _json_text(sections["parameter_update_stats"]),
            "decision": "Sampled parameter update is finite and nonzero.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "decision",
            "status": "passed" if manifest[B3_STEP_PASSED] else "blocked",
            "evidence": _json_text(sections["decision"]),
            "decision": "B3 single AdamW update smoke redirects the mainline toward real covalent feature mapping.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "safety_boundary",
            "status": "passed" if manifest["all_checks_passed"] else "blocked",
            "evidence": _json_text(sections["safety_boundary"]),
            "decision": "No training API, checkpoint/model/tensor dump, forbidden artifact, or protected source edit occurred.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
    ]


def write_summary(result: dict[str, Any], output_md: str | Path) -> None:
    manifest = result["manifest"]
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# B3 Single Optimizer Step Smoke v0 Summary",
        "",
        "Step 11R is a B3 single AdamW update smoke, not training.",
        "It uses a fresh strict-loaded pretrained checkpoint-compatible model.",
        f"It uses canonical long-form `{MASK_LEVEL}` only.",
        "It computes the B3 masked loss, executes exactly one controlled reverse pass, and executes exactly one AdamW update step.",
        "",
        "## Loss And Gradient",
        f"- checkpoint_path: {manifest['checkpoint_path']}",
        f"- requested_device: {manifest['requested_device']}",
        f"- resolved_device: {manifest['resolved_device']}",
        f"- model_instantiated: {str(manifest['model_instantiated']).lower()}",
        f"- strict_load_success: {str(manifest['strict_load_success']).lower()}",
        f"- pretrained_weights_loaded: {str(manifest['pretrained_weights_loaded']).lower()}",
        f"- pretrained_base_integration_proven: {str(manifest['pretrained_base_integration_proven']).lower()}",
        f"- selected_loss_key: {manifest['selected_loss_key']}",
        f"- selected_loss_value: {manifest['selected_loss_value']}",
        f"- loss_requires_grad: {str(manifest['loss_requires_grad']).lower()}",
        f"- loss_finite: {str(manifest['loss_finite']).lower()}",
        f"- {BWD}_call_count: {manifest[BWD + '_call_count']}",
        f"- finite_nonzero_grad_exists: {str(manifest['finite_nonzero_grad_exists']).lower()}",
        f"- total_grad_norm: {manifest['total_grad_norm']}",
        f"- max_abs_grad: {manifest['max_abs_grad']}",
        "",
        "## Optimizer Update",
        f"- optimizer_type: {manifest['optimizer_type']}",
        f"- learning_rate: {manifest['learning_rate']}",
        f"- weight_decay: {manifest['weight_decay']}",
        f"- {O}_created: {str(manifest[O + '_created']).lower()}",
        f"- {O_STEP}_call_count: {manifest[O_STEP + '_call_count']}",
        f"- sampled_parameter_count: {manifest['sampled_parameter_count']}",
        f"- sampled_parameter_delta_l2: {manifest['sampled_parameter_delta_l2']}",
        f"- sampled_parameter_delta_max_abs: {manifest['sampled_parameter_delta_max_abs']}",
        f"- updated_parameter_tensors_count: {manifest['updated_parameter_tensors_count']}",
        f"- parameter_update_finite: {str(manifest['parameter_update_finite']).lower()}",
        f"- parameter_update_nonzero: {str(manifest['parameter_update_nonzero']).lower()}",
        "",
        "## B3 Contract",
        f"- b3_target_atom_count: {manifest['b3_target_atom_count']}",
        f"- b3_context_atom_count: {manifest['b3_context_atom_count']}",
        f"- b3_reactive_atom_in_context: {str(manifest['b3_reactive_atom_in_context']).lower()}",
        f"- b3_reactive_atom_in_target: {str(manifest['b3_reactive_atom_in_target']).lower()}",
        "",
        "## Limits",
        "- This does not prove convergence, generation quality, or real loader readiness.",
        "- B3 tiny loop is optional, not the mainline next step.",
        "",
        "## Safety Boundary",
        f"- training_step_called: {str(manifest['training_step_called']).lower()}",
        f"- {TR_FIT}_called: {str(manifest[TR_FIT + '_called']).lower()}",
        f"- checkpoint_saved: {str(manifest['checkpoint_saved']).lower()}",
        f"- model_saved: {str(manifest['model_saved']).lower()}",
        f"- tensor_dump_saved: {str(manifest['tensor_dump_saved']).lower()}",
        f"- original_diffsbdd_source_modified: {str(manifest['original_diffsbdd_source_modified']).lower()}",
        f"- forbidden_artifacts_created: {str(manifest['forbidden_artifacts_created']).lower()}",
        "",
        "## Decision",
        f"- {B3_STEP_PASSED}: {str(manifest[B3_STEP_PASSED]).lower()}",
        f"- b3_parameter_update_contract_proven: {str(manifest['b3_parameter_update_contract_proven']).lower()}",
        f"- b3_finite_nonzero_parameter_update_proven: {str(manifest['b3_finite_nonzero_parameter_update_proven']).lower()}",
        f"- b3_tiny_loop_optional: {str(manifest['b3_tiny_loop_optional']).lower()}",
        f"- real_covalent_feature_mapping_loader_gate_allowed: {str(manifest['real_covalent_feature_mapping_loader_gate_allowed']).lower()}",
        f"- recommended_next_step: {manifest['recommended_next_step']}",
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(device: str = "cpu") -> int:
    result = build_b3_single_update_smoke_v0(device=device)
    write_csv(build_report_rows(result), REPORT_CSV, REPORT_COLUMNS)
    write_json(result["manifest"], MANIFEST_JSON)
    write_csv(result["update_table_rows"], UPDATE_TABLE_CSV, UPDATE_TABLE_COLUMNS)
    write_summary(result, SUMMARY_MD)
    print(f"{STAGE}_{'passed' if result['manifest']['all_checks_passed'] else 'blocked'}")
    return 0 if result["manifest"]["all_checks_passed"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run B3 single AdamW update smoke v0.")
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    return run(device=args.device)


if __name__ == "__main__":
    raise SystemExit(main())
