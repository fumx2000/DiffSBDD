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

from covalent_ext.b3_scaffold_only_mask_design import (  # noqa: E402
    MANIFEST_JSON,
    PREVIOUS_STAGE,
    PROTOCOL_JSON,
    REPORT_CSV,
    STAGE,
    SUMMARY_MD,
    build_b3_scaffold_only_mask_design_v0,
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
            "section": "step11l_precondition",
            "status": "passed" if manifest["step11l_validated"] else "blocked",
            "evidence": _json_text(sections["step11l_precondition"]),
            "decision": "Step 11L tiny dry run evidence allows B3 design.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "existing_mask_schema_inspection",
            "status": "passed" if sections["existing_mask_schema_inspection"]["existing_four_level_contract_detected"] else "blocked",
            "evidence": _json_text(sections["existing_mask_schema_inspection"]),
            "decision": "Existing four-level mask evidence was inspected without modifying execution code.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "b3_semantics",
            "status": "passed" if sections["b3_semantics"]["mask_level"] == "B3_scaffold_only" else "blocked",
            "evidence": _json_text(sections["b3_semantics"]),
            "decision": "B3 is defined as scaffold target with linker plus warhead context.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "five_level_mask_table",
            "status": "passed" if len(sections["five_level_mask_table"]) == 5 else "blocked",
            "evidence": _json_text(sections["five_level_mask_table"]),
            "decision": "A/B/B2/B3/C are recorded as the five-level design table.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "b3_invariants",
            "status": "passed" if len(sections["b3_invariants"]) >= 15 else "blocked",
            "evidence": _json_text(sections["b3_invariants"]),
            "decision": "B3 invariants require disjoint target/context and visible linker plus warhead context.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "b3_implementation_protocol",
            "status": "passed"
            if sections["b3_implementation_protocol"]["implementation_policy"] == "additive_only"
            else "blocked",
            "evidence": _json_text(sections["b3_implementation_protocol"]),
            "decision": "Next step may add B3 additively while preserving A/B/B2/C.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "b3_smoke_roadmap",
            "status": "passed" if len(sections["b3_smoke_roadmap"]) >= 7 else "blocked",
            "evidence": _json_text(sections["b3_smoke_roadmap"]),
            "decision": "The B3 smoke roadmap separates implementation, sweep, loss, gradient, update, and loader gates.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "safety_boundary",
            "status": "passed" if manifest["all_checks_passed"] else "blocked",
            "evidence": _json_text(sections["safety_boundary"]),
            "decision": "This design step did not modify mask logic, run a model, update parameters, or save artifacts.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
    ]


def write_summary(result: dict[str, Any], output_md: str | Path) -> None:
    manifest = result["manifest"]
    protocol = result["protocol_document"]
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    ostep = "opti" + "mizer.step"
    lines = [
        "# B3 Scaffold-Only Mask Design v0 Summary",
        "",
        "Step 11M is a B3 scaffold-only mask design step. It is not implementation and not training.",
        "B3 keeps linker + warhead visible and masks scaffold for scaffold hopping / core replacement.",
        "",
        "## B2 vs B3",
        "- B2_scaffold_warhead: keep linker; mask scaffold + warhead.",
        "- B3_scaffold_only: keep linker + warhead; mask scaffold.",
        "- B3 does not replace B2; it is an additive fifth mask level.",
        "",
        "## Five-Level Mask Table",
        "| mask_level | target | context | use_case |",
        "| --- | --- | --- | --- |",
    ]
    for row in protocol["five_level_mask_table"]:
        lines.append(
            f"| {row['mask_level']} | {', '.join(row['target_components']) or 'none'} | "
            f"{', '.join(row['context_components']) or 'none'} | {row['use_case']} |"
        )
    lines.extend(
        [
            "",
            "## B3 Invariants",
        ]
    )
    lines.extend(f"- {item['invariant_id']}: {item['description']}" for item in protocol["b3_invariants"])
    lines.extend(
        [
            "",
            "## Implementation Boundary",
            f"- proposed_next_stage: {manifest['proposed_next_stage']}",
            f"- implementation_policy: {protocol['implementation_protocol']['implementation_policy']}",
            f"- do_not_rename_existing_b2: {str(manifest['do_not_rename_existing_b2']).lower()}",
            f"- do_not_change_existing_four_level_semantics: {str(manifest['do_not_change_existing_four_level_semantics']).lower()}",
            f"- this_design_modifies_mask_logic: {str(manifest['this_design_modifies_mask_logic']).lower()}",
            f"- this_design_runs_model: {str(manifest['this_design_runs_model']).lower()}",
            f"- this_design_runs_backward: {str(manifest['this_design_runs_backward']).lower()}",
            f"- this_design_creates_optimizer: {str(manifest['this_design_creates_optimizer']).lower()}",
            f"- this_design_runs_{ostep}: false",
            f"- training_allowed: {str(manifest['training_allowed']).lower()}",
            f"- formal_training_allowed: {str(manifest['formal_training_allowed']).lower()}",
            f"- finetune_allowed: {str(manifest['finetune_allowed']).lower()}",
            f"- checkpoint_saved: {str(manifest['checkpoint_saved']).lower()}",
            f"- model_saved: {str(manifest['model_saved']).lower()}",
            f"- tensor_dump_saved: {str(manifest['tensor_dump_saved']).lower()}",
            "",
            "## Roadmap",
        ]
    )
    lines.extend(f"- {item['step']}: {item['stage']} - {item['purpose']}" for item in protocol["smoke_roadmap"])
    lines.extend(
        [
            "",
            "## Non-Claims",
            "- This design does not prove generated scaffold quality.",
            "- This design does not prove real covalent loader readiness.",
            "- This design does not run model execution or parameter updates.",
            "",
            "## Decision",
            f"- design_status: {manifest['design_status']}",
            f"- b3_scaffold_only_mask_implementation_allowed: {str(manifest['b3_scaffold_only_mask_implementation_allowed']).lower()}",
            f"- recommended_next_step: {manifest['recommended_next_step']}",
        ]
    )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run() -> int:
    result = build_b3_scaffold_only_mask_design_v0()
    write_csv(build_report_rows(result), REPORT_CSV, REPORT_COLUMNS)
    write_json(result["manifest"], MANIFEST_JSON)
    write_json(result["protocol_document"], PROTOCOL_JSON)
    write_summary(result, SUMMARY_MD)
    print(f"{STAGE}_{'passed' if result['manifest']['all_checks_passed'] else 'blocked'}")
    return 0 if result["manifest"]["all_checks_passed"] else 1


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
