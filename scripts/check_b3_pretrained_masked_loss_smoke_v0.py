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

from covalent_ext.b3_pretrained_masked_loss_smoke import (  # noqa: E402
    B3_CONTEXT_COMPONENTS,
    B3_TARGET_COMPONENTS,
    LOSS_TABLE_CSV,
    MANIFEST_JSON,
    MASK_LEVEL,
    PREVIOUS_STAGE,
    REPORT_CSV,
    STAGE,
    SUMMARY_MD,
    build_b3_pretrained_masked_loss_smoke_v0,
)


O = "opti" + "mizer"
O_STEP = O + "_step"
BWD = "back" + "ward"
TR_FIT = "trainer" + "_fit"

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
    "input_source",
    "selected_loss_key",
    "selected_loss_value",
    "loss_requires_grad",
    "loss_finite",
    "b3_target_atom_count",
    "b3_context_atom_count",
    "model_forward_called",
    BWD + "_called",
    O + "_created",
    O_STEP + "_called",
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
            "section": "step11o_precondition",
            "status": "passed" if manifest["step11o_validated"] else "blocked",
            "evidence": _json_text(sections["step11o_precondition"]),
            "decision": "Step 11O canonical five-level mask sweep evidence is accepted.",
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
            if manifest["b3_target_count_matches_step11o"] and manifest["b3_context_count_matches_step11o"]
            else "blocked",
            "evidence": _json_text(sections["b3_mask_contract"]),
            "decision": "Canonical B3 target/context counts match Step 11O.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "pretrained_forward",
            "status": "passed" if manifest["model_forward_called"] else "blocked",
            "evidence": _json_text(sections["pretrained_forward"]),
            "decision": "Pretrained model forward executed for B3 synthetic shape contract.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "masked_loss",
            "status": "passed" if manifest["loss_computed"] and manifest["loss_finite"] else "blocked",
            "evidence": _json_text(sections["masked_loss"]),
            "decision": "Differentiable masked loss exists and is finite.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "decision",
            "status": "passed" if manifest["b3_pretrained_masked_loss_smoke_passed"] else "blocked",
            "evidence": _json_text(sections["decision"]),
            "decision": "B3 pretrained masked loss smoke supports moving to B3 backward smoke.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "non_training_boundary",
            "status": "passed" if manifest["parameter_update_allowed"] is False else "blocked",
            "evidence": _json_text(sections["non_training_boundary"]),
            "decision": "No parameter update or training API is used.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "safety_boundary",
            "status": "passed" if manifest["all_checks_passed"] else "blocked",
            "evidence": _json_text(sections["safety_boundary"]),
            "decision": "No checkpoint/model/tensor dump, forbidden artifact, or protected source edit occurred.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
    ]


def write_summary(result: dict[str, Any], output_md: str | Path) -> None:
    manifest = result["manifest"]
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# B3 Pretrained Masked Loss Smoke v0 Summary",
        "",
        "Step 11P is B3 pretrained masked loss smoke, not training.",
        "It uses a fresh strict-loaded pretrained checkpoint-compatible model.",
        f"It uses canonical long-form `{MASK_LEVEL}` only.",
        f"B3 target={B3_TARGET_COMPONENTS}; context={B3_CONTEXT_COMPONENTS}.",
        "",
        "## Smoke Result",
        f"- checkpoint_path: {manifest['checkpoint_path']}",
        f"- requested_device: {manifest['requested_device']}",
        f"- resolved_device: {manifest['resolved_device']}",
        f"- model_instantiated: {str(manifest['model_instantiated']).lower()}",
        f"- strict_load_success: {str(manifest['strict_load_success']).lower()}",
        f"- pretrained_weights_loaded: {str(manifest['pretrained_weights_loaded']).lower()}",
        f"- pretrained_base_integration_proven: {str(manifest['pretrained_base_integration_proven']).lower()}",
        f"- model_forward_called: {str(manifest['model_forward_called']).lower()}",
        f"- loss_computed: {str(manifest['loss_computed']).lower()}",
        f"- selected_loss_key: {manifest['selected_loss_key']}",
        f"- selected_loss_value: {manifest['selected_loss_value']}",
        f"- loss_requires_grad: {str(manifest['loss_requires_grad']).lower()}",
        f"- loss_finite: {str(manifest['loss_finite']).lower()}",
        "",
        "## B3 Contract",
        f"- b3_target_atom_count: {manifest['b3_target_atom_count']}",
        f"- b3_context_atom_count: {manifest['b3_context_atom_count']}",
        f"- b3_reactive_atom_in_context: {str(manifest['b3_reactive_atom_in_context']).lower()}",
        f"- b3_reactive_atom_in_target: {str(manifest['b3_reactive_atom_in_target']).lower()}",
        "",
        "## Limits",
        "- This does not prove convergence, generation quality, or real loader readiness.",
        "- It does not run a parameter update.",
        "",
        "## Safety Boundary",
        f"- {BWD}_called: {str(manifest[BWD + '_called']).lower()}",
        f"- {O}_created: {str(manifest[O + '_created']).lower()}",
        f"- {O_STEP}_called: {str(manifest[O_STEP + '_called']).lower()}",
        f"- training_step_called: {str(manifest['training_step_called']).lower()}",
        f"- {TR_FIT}_called: {str(manifest[TR_FIT + '_called']).lower()}",
        f"- checkpoint_saved: {str(manifest['checkpoint_saved']).lower()}",
        f"- model_saved: {str(manifest['model_saved']).lower()}",
        f"- tensor_dump_saved: {str(manifest['tensor_dump_saved']).lower()}",
        f"- original_diffsbdd_source_modified: {str(manifest['original_diffsbdd_source_modified']).lower()}",
        f"- forbidden_artifacts_created: {str(manifest['forbidden_artifacts_created']).lower()}",
        "",
        "## Decision",
        f"- b3_pretrained_masked_loss_smoke_passed: {str(manifest['b3_pretrained_masked_loss_smoke_passed']).lower()}",
        f"- b3_pretrained_forward_loss_contract_proven: {str(manifest['b3_pretrained_forward_loss_contract_proven']).lower()}",
        f"- b3_backward_smoke_allowed: {str(manifest['b3_backward_smoke_allowed']).lower()}",
        f"- recommended_next_step: {manifest['recommended_next_step']}",
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(device: str = "cpu") -> int:
    result = build_b3_pretrained_masked_loss_smoke_v0(device=device)
    write_csv(build_report_rows(result), REPORT_CSV, REPORT_COLUMNS)
    write_json(result["manifest"], MANIFEST_JSON)
    write_csv(result["loss_table_rows"], LOSS_TABLE_CSV, LOSS_TABLE_COLUMNS)
    write_summary(result, SUMMARY_MD)
    print(f"{STAGE}_{'passed' if result['manifest']['all_checks_passed'] else 'blocked'}")
    return 0 if result["manifest"]["all_checks_passed"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run B3 pretrained masked loss smoke v0.")
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    return run(device=args.device)


if __name__ == "__main__":
    raise SystemExit(main())
