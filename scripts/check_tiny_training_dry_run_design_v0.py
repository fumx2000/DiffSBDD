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

from covalent_ext.tiny_training_dry_run_design import (  # noqa: E402
    MANIFEST_JSON,
    PREVIOUS_STAGE,
    PROTOCOL_JSON,
    REPORT_CSV,
    STAGE,
    SUMMARY_MD,
    build_tiny_training_dry_run_design_v0,
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
            "section": "step11j_precondition",
            "status": "passed" if manifest["step11j_validated"] else "blocked",
            "evidence": _json_text(sections["step11j_precondition"]),
            "decision": "Step 11J single optimizer-step smoke evidence is accepted.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "optimizer_evidence",
            "status": "passed" if sections["optimizer_evidence"].get("optimizer_plumbing_proven") else "blocked",
            "evidence": _json_text(sections["optimizer_evidence"]),
            "decision": "Single-step AdamW plumbing and finite parameter delta evidence are available.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "tiny_training_scope",
            "status": "passed" if sections["tiny_training_scope"].get("max_steps") == 3 else "blocked",
            "evidence": _json_text(sections["tiny_training_scope"]),
            "decision": "Scope the next dry run to three A_warhead_only synthetic steps.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "tiny_training_protocol",
            "status": "passed" if sections["tiny_training_protocol"].get("max_steps") == 3 else "blocked",
            "evidence": _json_text(sections["tiny_training_protocol"]),
            "decision": "Next step may run a tiny 3-step loop with scalar-only evidence and no saved artifacts.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "evidence_schema",
            "status": "passed" if "step_table_fields" in sections["evidence_schema"] else "blocked",
            "evidence": _json_text(sections["evidence_schema"]),
            "decision": "The next step evidence schema requires per-step scalar loss, gradient, and parameter delta fields.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "risk_register",
            "status": "passed" if len(sections["risk_register"]) >= 10 else "blocked",
            "evidence": _json_text(sections["risk_register"]),
            "decision": "Risks are explicit and do not block the first tiny synthetic dry run.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "design_decision",
            "status": "passed" if manifest["tiny_training_dry_run_allowed"] else "blocked",
            "evidence": _json_text(sections["design_decision"]),
            "decision": "Allow a tiny training dry run next; this design step itself performs no training action.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "safety_boundary",
            "status": "passed" if manifest["all_checks_passed"] else "blocked",
            "evidence": _json_text(sections["safety_boundary"]),
            "decision": "No backward pass, optimizer creation, optimizer step, trainer, checkpoint save, model save, or tensor dump occurred.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
    ]


def write_summary(manifest: dict[str, Any], protocol_document: dict[str, Any], output_md: str | Path) -> None:
    scope = protocol_document["scope"]
    protocol = protocol_document["protocol"]
    risks = protocol_document["risk_register"]
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Tiny Training Dry Run Design v0 Summary",
        "",
        "Step 11K is a tiny training dry run design step, not training.",
        "Step 11J already proved single optimizer-step plumbing on a strict-loaded pretrained model.",
        "This step only designs the next tiny 3-step synthetic loop and writes evidence.",
        "",
        "## Recommended 11L Boundary",
        f"- proposed_next_stage: {protocol['proposed_next_stage']}",
        f"- input_source: {scope['input_source']}",
        f"- selected_mask_levels: {', '.join(scope['selected_mask_levels'])}",
        f"- max_steps: {scope['max_steps']}",
        f"- batch_size: {scope['batch_size']}",
        f"- optimizer_class: {scope['optimizer_class']}",
        f"- optimizer_lr: {scope['lr']}",
        f"- optimizer_weight_decay: {scope['weight_decay']}",
        f"- reuse_optimizer_across_steps: {str(scope['reuse_optimizer_across_steps']).lower()}",
        f"- checkpoint_save_allowed_next_step: {str(manifest['checkpoint_save_allowed_next_step']).lower()}",
        f"- model_save_allowed_next_step: {str(manifest['model_save_allowed_next_step']).lower()}",
        f"- tensor_dump_allowed_next_step: {str(manifest['tensor_dump_allowed_next_step']).lower()}",
        "",
        "## Loss Trajectory Rule",
        f"- loss_decrease_required: {str(protocol['loss_trajectory_rule']['loss_decrease_required']).lower()}",
        f"- allow_loss_up_down_or_flat: {str(protocol['loss_trajectory_rule']['allow_loss_up_down_or_flat']).lower()}",
        f"- nan_or_inf_loss_fails: {str(protocol['loss_trajectory_rule']['nan_or_inf_loss_fails']).lower()}",
        "",
        "## Non-Claims",
    ]
    lines.extend(f"- {claim}" for claim in protocol["non_claims"])
    lines.extend(["", "## Risks"])
    for risk in risks:
        lines.append(f"- {risk['risk_id']}: {risk['description']} Mitigation: {risk['mitigation']}")
    lines.extend(
        [
            "",
            "## Decision",
            f"- design_status: {manifest['design_status']}",
            f"- tiny_training_dry_run_allowed: {str(manifest['tiny_training_dry_run_allowed']).lower()}",
            f"- this_design_runs_training_loop: {str(manifest['this_design_runs_training_loop']).lower()}",
            f"- this_design_runs_backward: {str(manifest['this_design_runs_backward']).lower()}",
            f"- this_design_creates_optimizer: {str(manifest['this_design_creates_optimizer']).lower()}",
            f"- this_design_runs_optimizer_step: {str(manifest['this_design_runs_optimizer_step']).lower()}",
            f"- training_allowed: {str(manifest['training_allowed']).lower()}",
            f"- formal_training_allowed: {str(manifest['formal_training_allowed']).lower()}",
            f"- finetune_allowed: {str(manifest['finetune_allowed']).lower()}",
            f"- recommended_next_step: {manifest['recommended_next_step']}",
        ]
    )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run() -> int:
    result = build_tiny_training_dry_run_design_v0()
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
