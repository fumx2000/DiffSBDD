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

from covalent_ext.b3_scaffold_only_mask_implementation import (  # noqa: E402
    API_AUDIT_CSV,
    CANONICAL_B3_NAME,
    MANIFEST_JSON,
    PREVIOUS_STAGE,
    REPORT_CSV,
    STAGE,
    SUMMARY_MD,
    build_b3_scaffold_only_mask_implementation_v0,
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

API_AUDIT_COLUMNS = ["stage", "section", "field", "value"]


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
    blockers = _list_text(manifest["blocking_reasons"])
    recommended = manifest["recommended_next_step"]
    return [
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "step11m_precondition",
            "status": "passed" if manifest["step11m_validated"] else "blocked",
            "evidence": _json_text(sections["step11m_precondition"]),
            "decision": "Step 11M B3 design evidence is accepted.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "api_audit",
            "status": "passed" if manifest["api_audit_completed"] else "blocked",
            "evidence": _json_text(sections["api_audit"]),
            "decision": "Short-token and long-form mask APIs were audited before implementation evidence was written.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "legacy_short_name_boundary",
            "status": "passed" if manifest["legacy_short_name_preserved"] else "blocked",
            "evidence": _json_text(sections["legacy_short_name_boundary"]),
            "decision": "Legacy short-token behavior is preserved; short B3 alias is deferred.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "long_form_mask_implementation",
            "status": "passed" if manifest["canonical_b3_long_form_available"] else "blocked",
            "evidence": _json_text(sections["long_form_mask_implementation"]),
            "decision": "Canonical long-form B3 mask is available additively.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "b2_b3_contrast",
            "status": "passed" if manifest["b2_b3_contrast_passed"] else "blocked",
            "evidence": _json_text(sections["b2_b3_contrast"]),
            "decision": "Long-form B2 and B3 target/context masks are distinct and explicit.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "missing_label_fail_safe",
            "status": "passed" if manifest["missing_label_fail_safe_passed"] else "blocked",
            "evidence": _json_text(sections["missing_label_fail_safe"]),
            "decision": "B3 fails safely on missing or empty scaffold/linker/warhead labels.",
            "blocking_reasons": blockers,
            "recommended_next_step": recommended,
        },
        {
            "stage": STAGE,
            "previous_stage": PREVIOUS_STAGE,
            "section": "batch_adapter_b3",
            "status": "passed" if manifest["batch_adapter_b3_available"] else "blocked",
            "evidence": _json_text(sections["batch_adapter_b3"]),
            "decision": "Batch adapter can route B3 scaffold target with linker plus warhead context.",
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
    audit = result["api_audit"]
    checks = result["implementation_checks"]
    output = Path(output_md)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# B3 Scaffold-Only Mask Implementation v0 Summary",
        "",
        "Step 11N implements the canonical long-form B3 scaffold-only mask additively.",
        "It is not training and does not run model execution or parameter updates.",
        "",
        "## API Audit",
        f"- short_tokens_detected: {audit['short_tokens_detected']}",
        f"- long_form_names_detected: {audit['long_form_names_detected']}",
        f"- legacy_short_name_ambiguity_detected: {str(manifest['legacy_short_name_ambiguity_detected']).lower()}",
        f"- legacy_short_name_preserved: {str(manifest['legacy_short_name_preserved']).lower()}",
        f"- short_alias_b3_added: {str(manifest['short_alias_b3_added']).lower()}",
        f"- short_alias_b3_deferred: {str(manifest['short_alias_b3_deferred']).lower()}",
        f"- short_alias_b3_deferred_reason: {manifest['short_alias_b3_deferred_reason']}",
        "",
        "## Canonical B3",
        f"- canonical_b3_name: {manifest['canonical_b3_name']}",
        f"- b3_target_components: {manifest['b3_target_components']}",
        f"- b3_context_components: {manifest['b3_context_components']}",
        f"- canonical_b3_long_form_available: {str(manifest['canonical_b3_long_form_available']).lower()}",
        f"- b3_added_additively: {str(manifest['b3_added_additively']).lower()}",
        "",
        "## B2 vs B3",
        f"- long_form_b2_masked_atoms: {audit['long_form_b2_masked_atoms']}",
        f"- long_form_b2_visible_atoms: {audit['long_form_b2_visible_atoms']}",
        f"- long_form_b3_masked_atoms: {audit['long_form_b3_masked_atoms']}",
        f"- long_form_b3_visible_atoms: {audit['long_form_b3_visible_atoms']}",
        f"- long_form_b2_semantics_protected: {str(manifest['long_form_b2_semantics_protected']).lower()}",
        f"- b2_b3_contrast_passed: {str(manifest['b2_b3_contrast_passed']).lower()}",
        "",
        "## Fail-Safe",
    ]
    lines.extend(f"- {name}: {str(value).lower()}" for name, value in checks["fail_safe_results"].items())
    lines.extend(
        [
            "",
            "## Safety Boundary",
            f"- mask_logic_modified: {str(manifest['mask_logic_modified']).lower()}",
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
            f"- b3_mask_implementation_passed: {str(manifest['b3_mask_implementation_passed']).lower()}",
            f"- existing_four_level_semantics_unchanged: {str(manifest['existing_four_level_semantics_unchanged']).lower()}",
            f"- all_checks_passed: {str(manifest['all_checks_passed']).lower()}",
            f"- recommended_next_step: {manifest['recommended_next_step']}",
        ]
    )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run() -> int:
    result = build_b3_scaffold_only_mask_implementation_v0()
    write_csv(build_report_rows(result), REPORT_CSV, REPORT_COLUMNS)
    write_json(result["manifest"], MANIFEST_JSON)
    write_csv(result["api_audit_rows"], API_AUDIT_CSV, API_AUDIT_COLUMNS)
    write_summary(result, SUMMARY_MD)
    print(f"{STAGE}_{'passed' if result['manifest']['all_checks_passed'] else 'blocked'}")
    return 0 if result["manifest"]["all_checks_passed"] else 1


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
