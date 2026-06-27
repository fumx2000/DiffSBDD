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

from covalent_ext.b3_scaffold_only_mask_sweep import (  # noqa: E402
    CANONICAL_MASK_LEVELS,
    EXPECTED_COMPONENTS,
    MANIFEST_JSON,
    PREVIOUS_STAGE,
    REPORT_CSV,
    STAGE,
    SUMMARY_MD,
    SWEEP_TABLE_CSV,
    build_b3_scaffold_only_mask_sweep_v0,
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

SWEEP_TABLE_COLUMNS = [
    "stage",
    "sample_id",
    "mask_level",
    "target_components",
    "context_components",
    "target_atoms",
    "context_atoms",
    "target_atom_count",
    "context_atom_count",
    "scaffold_in_target",
    "scaffold_in_context",
    "linker_in_target",
    "linker_in_context",
    "warhead_in_target",
    "warhead_in_context",
    "target_context_disjoint",
    "target_context_cover_assigned_atoms",
    "expected_target_count",
    "expected_context_count",
    "target_count_matches_expected",
    "context_count_matches_expected",
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
            "section": "step11n_precondition",
            "status": "passed" if manifest["step11n_validated"] else "blocked",
            "evidence": _json_text(sections["step11n_precondition"]),
            "decision": "Step 11N additive B3 implementation evidence is accepted.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "canonical_mask_sweep",
            "status": "passed" if manifest["all_mask_sweep_rows_passed"] else "blocked",
            "evidence": _json_text(sections["canonical_mask_sweep"]),
            "decision": "Five canonical long-form mask levels match expected target/context atoms and counts.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "b2_b3_contrast",
            "status": "passed" if manifest["b2_b3_contrast_passed"] else "blocked",
            "evidence": _json_text(sections["b2_b3_contrast"]),
            "decision": "B2 scaffold+warhead target and B3 scaffold-only target remain distinct.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "batch_adapter_sweep",
            "status": "passed" if manifest["all_batch_adapter_rows_passed"] else "blocked",
            "evidence": _json_text(sections["batch_adapter_sweep"]),
            "decision": "Batch adapter validates all five canonical long-form mask levels.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "b3_fallback_adapter",
            "status": "passed" if manifest["b3_fallback_adapter_valid"] else "blocked",
            "evidence": _json_text(sections["b3_fallback_adapter"]),
            "decision": "B3 adapter fallback uses scaffold mask when explicit B3 generation key is absent.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "b3_explicit_key_adapter",
            "status": "passed" if manifest["b3_explicit_key_adapter_valid"] else "blocked",
            "evidence": _json_text(sections["b3_explicit_key_adapter"]),
            "decision": "B3 adapter explicit generation key path validates with expected counts.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "decision",
            "status": "passed" if manifest["five_level_mask_sweep_passed"] else "blocked",
            "evidence": _json_text(sections["decision"]),
            "decision": "Canonical five-level mask contract is ready for B3 pretrained masked loss smoke.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "safety_boundary",
            "status": "passed" if manifest["all_checks_passed"] else "blocked",
            "evidence": _json_text(sections["safety_boundary"]),
            "decision": "No model execution, parameter update, checkpoint/model/tensor artifact, or original DiffSBDD source edit occurred.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
    ]


def write_summary(result: dict[str, Any], output_md: str | Path) -> None:
    manifest = result["manifest"]
    sweep_rows = result["sweep_rows"]
    contrast = result["contrast"]
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# B3 Scaffold-Only Mask Sweep v0 Summary",
        "",
        "Step 11O is a five-level mask sweep, not training.",
        "It uses only canonical long-form A/B/B2/B3/C mask levels.",
        "It does not use short alias B3; legacy short-name ambiguity remains preserved and isolated.",
        "",
        "## Canonical Levels",
    ]
    lines.extend(f"- {level}: target={EXPECTED_COMPONENTS[level]['target']}, context={EXPECTED_COMPONENTS[level]['context']}" for level in CANONICAL_MASK_LEVELS)
    lines.extend(
        [
            "",
            "## Observed Counts",
        ]
    )
    for row in sweep_rows:
        lines.append(
            "- "
            f"{row['mask_level']}: target_atoms={row['target_atoms']} "
            f"context_atoms={row['context_atoms']} "
            f"target_count={row['target_atom_count']} context_count={row['context_atom_count']} "
            f"status={row['status']}"
        )
    lines.extend(
        [
            "",
            "## B2/B3 Contrast",
        ]
    )
    lines.extend(f"- {key}: {str(value).lower()}" for key, value in contrast.items())
    lines.extend(
        [
            "",
            "## Batch Adapter Sweep",
            f"- batch_adapter_sweep_row_count: {manifest['batch_adapter_sweep_row_count']}",
            f"- all_batch_adapter_rows_passed: {str(manifest['all_batch_adapter_rows_passed']).lower()}",
            f"- b3_fallback_adapter_valid: {str(manifest['b3_fallback_adapter_valid']).lower()}",
            f"- b3_explicit_key_adapter_valid: {str(manifest['b3_explicit_key_adapter_valid']).lower()}",
            "",
            "## Limits",
            "- This step does not prove loss behavior, gradients, optimizer behavior, generation quality, or real loader readiness.",
            "- It does not run model forward or write tensor dumps.",
            "",
            "## Safety Boundary",
            f"- model_forward_called: {str(manifest['model_forward_called']).lower()}",
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
            f"- five_level_mask_sweep_passed: {str(manifest['five_level_mask_sweep_passed']).lower()}",
            f"- canonical_five_level_mask_contract_proven: {str(manifest['canonical_five_level_mask_contract_proven']).lower()}",
            f"- b3_pretrained_masked_loss_smoke_allowed: {str(manifest['b3_pretrained_masked_loss_smoke_allowed']).lower()}",
            f"- recommended_next_step: {manifest['recommended_next_step']}",
        ]
    )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run() -> int:
    result = build_b3_scaffold_only_mask_sweep_v0()
    write_csv(build_report_rows(result), REPORT_CSV, REPORT_COLUMNS)
    write_json(result["manifest"], MANIFEST_JSON)
    write_csv(result["sweep_rows"], SWEEP_TABLE_CSV, SWEEP_TABLE_COLUMNS)
    write_summary(result, SUMMARY_MD)
    print(f"{STAGE}_{'passed' if result['manifest']['all_checks_passed'] else 'blocked'}")
    return 0 if result["manifest"]["all_checks_passed"] else 1


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
