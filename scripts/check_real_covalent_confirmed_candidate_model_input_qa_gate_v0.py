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

from covalent_ext import real_covalent_confirmed_candidate_model_input_qa_gate as qa  # noqa: E402


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
                "stage": qa.STAGE,
                "previous_stage": qa.PREVIOUS_STAGE,
                "section": section,
                "status": "passed" if manifest["all_checks_passed"] else "blocked",
                "evidence": _json_text(evidence),
                "decision": "model_input QA gate passed"
                if manifest["all_checks_passed"]
                else "model_input QA gate blocked",
                "blocking_reasons": "" if manifest["all_checks_passed"] else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# Real Covalent Confirmed Candidate Model Input QA Gate v0 Summary

Step 13X is a model_input QA gate only.
It reads but does not modify the Step 13W CSV/JSON smoke artifacts.
It validates row identity, CYS/SG scope, sample contract consistency, sample_index consistency, ligand counts, endpoint counts, pocket dependencies, ligand topology dependencies, five canonical mask tasks including scaffold_only/B3, feature semantics audit status, tensor status, and loader/training boundaries.

This step does not generate tensor, NPZ, or PT artifacts.
It does not modify dataloader, forward, loss, or DiffSBDD main model code.
It does not run loader shape dry run.
It does not run forward, loss, backward, optimizer, training step, trainer fit, checkpoint save, model save, or tensor dump.
It allows the loader shape dry run design gate next.
It does not allow training.
Feature semantics audit remains required before formal training.

model_input_smoke_row_qa_audit_row_count: `{manifest["model_input_smoke_row_qa_audit_row_count"]}`
model_input_smoke_dependency_qa_audit_row_count: `{manifest["model_input_smoke_dependency_qa_audit_row_count"]}`
model_input_smoke_feature_qa_audit_row_count: `{manifest["model_input_smoke_feature_qa_audit_row_count"]}`
model_input_smoke_mask_qa_audit_row_count: `{manifest["model_input_smoke_mask_qa_audit_row_count"]}`
model_input_qa_passed: `{manifest["model_input_qa_passed"]}`
model_input_smoke_modified: `{manifest["model_input_smoke_modified"]}`
model_input_materialized: `{manifest["model_input_materialized"]}`
tensor_artifact_written: `{manifest["tensor_artifact_written"]}`
ready_for_loader_shape_dry_run: `{manifest["ready_for_loader_shape_dry_run"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = qa.build_real_covalent_confirmed_candidate_model_input_qa_gate_v0()
    write_csv(result["row_qa_rows"], qa.ROW_QA_AUDIT_CSV, qa.ROW_QA_COLUMNS)
    write_csv(result["dependency_qa_rows"], qa.DEPENDENCY_QA_AUDIT_CSV, qa.DEPENDENCY_QA_COLUMNS)
    write_csv(result["feature_qa_rows"], qa.FEATURE_QA_AUDIT_CSV, qa.FEATURE_QA_COLUMNS)
    write_csv(result["mask_qa_rows"], qa.MASK_QA_AUDIT_CSV, qa.MASK_QA_COLUMNS)
    write_csv(build_report_rows(result), qa.REPORT_CSV, qa.REPORT_COLUMNS)
    write_json(result["manifest"], qa.MANIFEST_JSON)
    write_summary(result["manifest"], qa.SUMMARY_MD)
    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("real_covalent_confirmed_candidate_model_input_qa_gate_v0_passed")
    else:
        print("real_covalent_confirmed_candidate_model_input_qa_gate_v0_blocked")
    print(f"model_input_smoke_row_qa_audit_row_count={manifest['model_input_smoke_row_qa_audit_row_count']}")
    print(f"model_input_smoke_dependency_qa_audit_row_count={manifest['model_input_smoke_dependency_qa_audit_row_count']}")
    print(f"model_input_smoke_feature_qa_audit_row_count={manifest['model_input_smoke_feature_qa_audit_row_count']}")
    print(f"model_input_smoke_mask_qa_audit_row_count={manifest['model_input_smoke_mask_qa_audit_row_count']}")
    print(f"model_input_qa_passed={manifest['model_input_qa_passed']}")
    print(f"ready_for_loader_shape_dry_run={manifest['ready_for_loader_shape_dry_run']}")
    print(f"ready_for_training={manifest['ready_for_training']}")
    print(f"ready_to_train_now={manifest['ready_to_train_now']}")
    print(f"recommended_next_step={manifest['recommended_next_step']}")
    if manifest["blocking_reasons"]:
        print("blocking_reasons=" + ";".join(manifest["blocking_reasons"]))
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
