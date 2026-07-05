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

from covalent_ext import real_covalent_confirmed_candidate_model_input_design_gate as design  # noqa: E402


def _csv_value(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True)
    return value


def _json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _list_text(value: Any) -> str:
    if isinstance(value, list):
        return ";".join(str(item) for item in value)
    return "" if value is None else str(value)


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
    blockers = _list_text(manifest["blocking_reasons"])
    rows: list[dict[str, str]] = []
    for section, evidence in result["report_sections"].items():
        rows.append(
            {
                "stage": design.STAGE,
                "previous_stage": design.PREVIOUS_STAGE,
                "section": section,
                "status": "passed" if manifest["all_checks_passed"] else "blocked",
                "evidence": _json_text(evidence),
                "decision": "model_input design gate passed"
                if manifest["all_checks_passed"]
                else "model_input design gate blocked",
                "blocking_reasons": "" if manifest["all_checks_passed"] else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# Real Covalent Confirmed Candidate Model Input Design Gate v0 Summary

Step 13V is a model_input design gate only.
It designs how the current sample_index smoke could map to DiffSBDD-compatible model input.
It does not materialize model input, tensors, NPZ, PT, split assignments, leakage matrix, or final_dataset.
It does not modify dataloader, forward, loss, or DiffSBDD main model code.

The five canonical mask tasks remain preserved, including scaffold_only/B3.
Long semantic mask names remain the source of truth and aliases remain display-only.
This gate explicitly records feature semantics audit requirements.
Step 12D was smoke legality only, not final feature semantics audit.
This gate allows model_input materialization smoke next.
It does not allow loader shape dry run and does not allow training.
Feature semantics audit remains required before formal training.

schema_contract_row_count: `{manifest["schema_contract_row_count"]}`
dependency_contract_row_count: `{manifest["dependency_contract_row_count"]}`
sample_contract_row_count: `{manifest["sample_contract_row_count"]}`
mask_contract_row_count: `{manifest["mask_contract_row_count"]}`
feature_semantics_contract_row_count: `{manifest["feature_semantics_contract_row_count"]}`
ready_for_model_input_materialization_smoke: `{manifest["ready_for_model_input_materialization_smoke"]}`
ready_for_loader_shape_dry_run: `{manifest["ready_for_loader_shape_dry_run"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = design.build_real_covalent_confirmed_candidate_model_input_design_gate_v0()
    write_csv(result["schema_rows"], design.SCHEMA_CONTRACT_CSV, design.SCHEMA_COLUMNS)
    write_csv(result["dependency_rows"], design.DEPENDENCY_CONTRACT_CSV, design.DEPENDENCY_COLUMNS)
    write_csv(result["sample_rows"], design.SAMPLE_CONTRACT_CSV, design.SAMPLE_COLUMNS)
    write_csv(result["mask_rows"], design.MASK_CONTRACT_CSV, design.MASK_COLUMNS)
    write_csv(result["feature_rows"], design.FEATURE_SEMANTICS_CONTRACT_CSV, design.FEATURE_SEMANTICS_COLUMNS)
    write_csv(build_report_rows(result), design.REPORT_CSV, design.REPORT_COLUMNS)
    write_json(result["manifest"], design.MANIFEST_JSON)
    write_summary(result["manifest"], design.SUMMARY_MD)
    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("real_covalent_confirmed_candidate_model_input_design_gate_v0_passed")
    else:
        print("real_covalent_confirmed_candidate_model_input_design_gate_v0_blocked")
    print(f"schema_contract_row_count={manifest['schema_contract_row_count']}")
    print(f"dependency_contract_row_count={manifest['dependency_contract_row_count']}")
    print(f"sample_contract_row_count={manifest['sample_contract_row_count']}")
    print(f"mask_contract_row_count={manifest['mask_contract_row_count']}")
    print(f"feature_semantics_contract_row_count={manifest['feature_semantics_contract_row_count']}")
    print(f"model_input_design_gate_passed={manifest['model_input_design_gate_passed']}")
    print(f"ready_for_model_input_materialization_smoke={manifest['ready_for_model_input_materialization_smoke']}")
    print(f"ready_for_loader_shape_dry_run={manifest['ready_for_loader_shape_dry_run']}")
    print(f"ready_for_training={manifest['ready_for_training']}")
    print(f"ready_to_train_now={manifest['ready_to_train_now']}")
    print(f"recommended_next_step={manifest['recommended_next_step']}")
    if manifest["blocking_reasons"]:
        print("blocking_reasons=" + ";".join(manifest["blocking_reasons"]))
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
