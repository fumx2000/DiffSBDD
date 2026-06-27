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

from covalent_ext.pretrained_masked_loss_microbatch_design import (  # noqa: E402
    MANIFEST_JSON,
    PREVIOUS_STAGE,
    PROTOCOL_JSON,
    REPORT_CSV,
    STAGE,
    SUMMARY_MD,
    build_pretrained_masked_loss_microbatch_design_v0,
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
    return [
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "step11f_precondition",
            "status": "passed" if manifest["step11f_validated"] else "blocked",
            "evidence": _json_text(sections["step11f_precondition"]),
            "decision": "Step 11F pretrained masked loss smoke evidence is accepted.",
            "blocking_reasons": _list_text(manifest["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "step11f_loss_evidence",
            "status": "passed" if sections["step11f_loss_evidence"].get("finite_loss_count") == 4 else "blocked",
            "evidence": _json_text(sections["step11f_loss_evidence"]),
            "decision": "Four finite Step 11F loss values are available for protocol design; loss size is not a quality claim.",
            "blocking_reasons": _list_text(manifest["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "microbatch_data_source_inspection",
            "status": "passed" if sections["microbatch_data_source_inspection"].get("synthetic_10d_contract_available") else "blocked",
            "evidence": _json_text(sections["microbatch_data_source_inspection"]),
            "decision": "Use the synthetic 10D shape contract for the first pretrained microbatch backward dry run.",
            "blocking_reasons": _list_text(manifest["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "microbatch_protocol",
            "status": "passed" if sections["microbatch_protocol"].get("fresh_model_per_mask_level") else "blocked",
            "evidence": _json_text(sections["microbatch_protocol"]),
            "decision": "Next step should use isolated fresh-model reverse-pass dry runs for A/B/B2/C, with no optimizer.",
            "blocking_reasons": _list_text(manifest["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "risk_register",
            "status": "passed" if len(sections["risk_register"]) >= 6 else "blocked",
            "evidence": _json_text(sections["risk_register"]),
            "decision": "Risks are explicit and do not block the first backward-only microbatch dry run.",
            "blocking_reasons": _list_text(manifest["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "design_decision",
            "status": "passed" if manifest["microbatch_backward_dry_run_allowed"] else "blocked",
            "evidence": _json_text(sections["design_decision"]),
            "decision": "Allow Step 11H as a backward-only microbatch dry run; still no optimizer step or checkpoint save.",
            "blocking_reasons": _list_text(manifest["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "safety_boundary",
            "status": "passed" if manifest["all_checks_passed"] else "blocked",
            "evidence": _json_text(sections["safety_boundary"]),
            "decision": "This design step did not run a reverse pass, create an optimizer, train, or save model artifacts.",
            "blocking_reasons": _list_text(manifest["blocking_reasons"]),
            "recommended_next_step": recommended,
        },
    ]


def write_summary(manifest: dict[str, Any], protocol_document: dict[str, Any], output_md: str | Path) -> None:
    protocol = protocol_document["protocol"]
    data_sources = protocol_document["data_source_evidence"]
    risks = protocol_document["risk_register"]
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Pretrained Masked Loss Microbatch Design v0 Summary",
        "",
        "Step 11G is a microbatch dry-run design step, not training.",
        "Step 11F already proved checkpoint-compatible pretrained masked loss smoke over A/B/B2/C.",
        "This step only designs the next backward-only microbatch dry run and writes evidence.",
        "",
        "## 11H Boundary",
        f"- proposed_next_stage: {protocol['proposed_next_stage']}",
        f"- microbatch_backward_policy: {protocol['microbatch_backward_policy']}",
        f"- mask_levels_for_backward_dry_run: {', '.join(protocol['mask_levels_for_backward_dry_run'])}",
        f"- fresh_model_per_mask_level: {str(protocol['fresh_model_per_mask_level']).lower()}",
        f"- backward_allowed_next_step: {str(protocol['backward_allowed_next_step']).lower()}",
        f"- optimizer_allowed_next_step: {str(protocol['optimizer_allowed_next_step']).lower()}",
        f"- optimizer_step_allowed_next_step: {str(protocol['optimizer_step_allowed_next_step']).lower()}",
        f"- checkpoint_save_allowed_next_step: {str(protocol['checkpoint_save_allowed_next_step']).lower()}",
        f"- model_save_allowed_next_step: {str(protocol['model_save_allowed_next_step']).lower()}",
        "",
        "## Input Source",
        f"- recommended_microbatch_input_source: {data_sources['recommended_microbatch_input_source']}",
        f"- real_covalent_sample_available: {str(data_sources['real_covalent_sample_available']).lower()}",
        f"- synthetic_10d_contract_available: {str(data_sources['synthetic_10d_contract_available']).lower()}",
        "- rationale: real covalent artifacts exist, but the checkpoint-compatible pretrained model still uses a synthetic 10D shape contract.",
        "",
        "## Risks",
    ]
    for risk in risks:
        lines.append(f"- {risk['risk_id']}: {risk['description']} Mitigation: {risk['mitigation']}")
    lines.extend(
        [
            "",
            "## Decision",
            f"- design_status: {manifest['design_status']}",
            f"- microbatch_backward_dry_run_allowed: {str(manifest['microbatch_backward_dry_run_allowed']).lower()}",
            f"- this_design_executes_backward: {str(manifest['this_design_executes_backward']).lower()}",
            f"- this_design_creates_optimizer: {str(manifest['this_design_creates_optimizer']).lower()}",
            f"- training_allowed: {str(manifest['training_allowed']).lower()}",
            f"- formal_training_allowed: {str(manifest['formal_training_allowed']).lower()}",
            f"- finetune_allowed: {str(manifest['finetune_allowed']).lower()}",
            f"- optimizer_step_allowed: {str(manifest['optimizer_step_allowed']).lower()}",
            f"- checkpoint_saved: {str(manifest['checkpoint_saved']).lower()}",
            f"- model_saved: {str(manifest['model_saved']).lower()}",
            f"- recommended_next_step: {manifest['recommended_next_step']}",
        ]
    )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run() -> int:
    result = build_pretrained_masked_loss_microbatch_design_v0()
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
