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

from covalent_ext.optimizer_smoke_design import (  # noqa: E402
    MANIFEST_JSON,
    PREVIOUS_STAGE,
    PROTOCOL_JSON,
    REPORT_CSV,
    STAGE,
    SUMMARY_MD,
    build_optimizer_smoke_design_v0,
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


def build_report_rows(result: dict[str, Any]) -> list[dict[str, str]]:
    manifest = result["manifest"]
    sections = result["report_sections"]
    recommended = manifest["recommended_next_step"]
    blockers = _list_text(manifest["blocking_reasons"])
    return [
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "step11h_precondition",
            "status": "passed" if manifest["step11h_validated"] else "blocked",
            "evidence": _json_text(sections["step11h_precondition"]),
            "decision": "Step 11H pretrained microbatch backward evidence is accepted.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "gradient_evidence",
            "status": "passed" if sections["gradient_evidence"].get("all_have_nonzero_grad") else "blocked",
            "evidence": _json_text(sections["gradient_evidence"]),
            "decision": "Finite nonzero gradient evidence exists for A/B/B2/C; gradient size is not a quality claim.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "optimizer_input_policy",
            "status": "passed" if sections["optimizer_input_policy"].get("selected_initial_mask_level") == "A_warhead_only" else "blocked",
            "evidence": _json_text(sections["optimizer_input_policy"]),
            "decision": "Use A_warhead_only as the first and most conservative single-step optimizer smoke level.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "optimizer_config",
            "status": "passed" if sections["optimizer_config"].get("lr") == 1e-6 else "blocked",
            "evidence": _json_text(sections["optimizer_config"]),
            "decision": "Recommend AdamW with lr=1e-6 and weight_decay=0 for plumbing-only parameter delta evidence.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "optimizer_protocol",
            "status": "passed" if sections["optimizer_protocol"].get("optimizer_step_call_count_next_step") == 1 else "blocked",
            "evidence": _json_text(sections["optimizer_protocol"]),
            "decision": "Next step may create one optimizer and call one step exactly once, without saving artifacts.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "design_decision",
            "status": "passed" if manifest["optimizer_step_smoke_allowed"] else "blocked",
            "evidence": _json_text(sections["design_decision"]),
            "decision": "Allow a single optimizer-step smoke next; this design step itself runs no optimizer or backward.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "safety_boundary",
            "status": "passed" if manifest["all_checks_passed"] else "blocked",
            "evidence": _json_text(sections["safety_boundary"]),
            "decision": "No backward pass, optimizer creation, optimizer step, training, checkpoint save, or model save occurred.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
    ]


def write_summary(manifest: dict[str, Any], protocol_document: dict[str, Any], output_md: str | Path) -> None:
    protocol = protocol_document["protocol"]
    optimizer_config = protocol_document["optimizer_config"]
    risks = protocol_document["risk_register"]
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Optimizer Smoke Design v0 Summary",
        "",
        "Step 11I is an optimizer smoke design step, not training.",
        "Step 11H already proved pretrained masked-loss gradient plumbing over A/B/B2/C.",
        "This step only designs the next single optimizer-step smoke and writes evidence.",
        "",
        "## Recommended 11J Boundary",
        f"- proposed_next_stage: {protocol['proposed_next_stage']}",
        f"- selected_initial_mask_level: {protocol['selected_mask_level']}",
        f"- input_source: {protocol['input_source']}",
        f"- model_policy: {protocol['model_policy']}",
        f"- optimizer_policy: {protocol['optimizer_policy']}",
        f"- optimizer_class: {optimizer_config['optimizer_class']}",
        f"- optimizer_import_path_next_step: {optimizer_config['optimizer_import_path_next_step']}",
        f"- optimizer_lr_recommended: {optimizer_config['lr']}",
        f"- optimizer_weight_decay_recommended: {optimizer_config['weight_decay']}",
        f"- optimizer_step_policy: {protocol['optimizer_step_policy']}",
        f"- optimizer_step_call_count_next_step: {protocol['optimizer_step_call_count_next_step']}",
        f"- checkpoint_save_allowed_next_step: {str(manifest['checkpoint_save_allowed_next_step']).lower()}",
        f"- model_save_allowed_next_step: {str(manifest['model_save_allowed_next_step']).lower()}",
        "",
        "## Pass Conditions",
    ]
    lines.extend(f"- {condition}" for condition in protocol["pass_conditions"])
    lines.extend(
        [
            "",
            "## Non-Claims",
        ]
    )
    lines.extend(f"- {claim}" for claim in protocol["non_claims"])
    lines.extend(["", "## Risks"])
    for risk in risks:
        lines.append(f"- {risk['risk_id']}: {risk['description']} Mitigation: {risk['mitigation']}")
    lines.extend(
        [
            "",
            "## Decision",
            f"- design_status: {manifest['design_status']}",
            f"- optimizer_step_smoke_allowed: {str(manifest['optimizer_step_smoke_allowed']).lower()}",
            f"- this_design_creates_optimizer: {str(manifest['this_design_creates_optimizer']).lower()}",
            f"- this_design_runs_optimizer_step: {str(manifest['this_design_runs_optimizer_step']).lower()}",
            f"- this_design_runs_backward: {str(manifest['this_design_runs_backward']).lower()}",
            f"- training_allowed: {str(manifest['training_allowed']).lower()}",
            f"- formal_training_allowed: {str(manifest['formal_training_allowed']).lower()}",
            f"- finetune_allowed: {str(manifest['finetune_allowed']).lower()}",
            f"- checkpoint_saved: {str(manifest['checkpoint_saved']).lower()}",
            f"- model_saved: {str(manifest['model_saved']).lower()}",
            f"- recommended_next_step: {manifest['recommended_next_step']}",
        ]
    )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run() -> int:
    result = build_optimizer_smoke_design_v0()
    write_csv(build_report_rows(result), REPORT_CSV, REPORT_COLUMNS)
    write_json(result["manifest"], MANIFEST_JSON)
    write_json(result["protocol_document"], PROTOCOL_JSON)
    write_summary(result["manifest"], result["protocol_document"], SUMMARY_MD)
    print(f"{STAGE}_{'passed' if result['manifest']['all_checks_passed'] else 'blocked'}")
    return 0 if result["manifest"]["all_checks_passed"] else 1


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
