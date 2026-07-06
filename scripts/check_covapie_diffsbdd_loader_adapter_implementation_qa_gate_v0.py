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

from covalent_ext import covapie_diffsbdd_loader_adapter_implementation_qa_gate as qa  # noqa: E402


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
                "decision": "CovaPIE DiffSBDD loader adapter implementation QA gate passed"
                if manifest["all_checks_passed"]
                else "CovaPIE DiffSBDD loader adapter implementation QA gate blocked",
                "blocking_reasons": "" if manifest["all_checks_passed"] else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# CovaPIE DiffSBDD Loader Adapter Implementation QA Gate v0 Summary

This is a CovaPIE QA gate.
It reviews Step 13AC external DiffSBDD loader adapter implementation smoke.
It does not implement or instantiate the adapter.
It does not import torch or create tensors.
It does not modify original DiffSBDD dataloader, forward, loss, equivariant_diffusion/, or lightning_modules.py.
It validates 3 CYS/SG golden samples, 14 adapter fields, 42 field shape observations, 5 canonical mask tasks including scaffold_only/B3, and 3 auxiliary labels.
It confirms auxiliary labels are carried but not integrated into loss.
It confirms no PT/NPZ/tensor artifacts, no checkpoint load/save, no model forward/loss/backward/optimizer/trainer.fit/training.
It confirms feature semantics audit remains required before formal training.
It allows CovaPIE batch-scale data preparation design gate next, not training.
Historical artifact paths are retained while new reports and docs use CovaPIE.

project_name: `{manifest["project_name"]}`
naming_convention_validated: `{manifest["naming_convention_validated"]}`
covapie_adapter_input_qa_audit_row_count: `{manifest["covapie_adapter_input_qa_audit_row_count"]}`
covapie_adapter_sample_dict_qa_audit_row_count: `{manifest["covapie_adapter_sample_dict_qa_audit_row_count"]}`
covapie_adapter_field_shape_qa_audit_row_count: `{manifest["covapie_adapter_field_shape_qa_audit_row_count"]}`
covapie_adapter_single_sample_batch_qa_audit_row_count: `{manifest["covapie_adapter_single_sample_batch_qa_audit_row_count"]}`
covapie_adapter_mask_mapping_qa_audit_row_count: `{manifest["covapie_adapter_mask_mapping_qa_audit_row_count"]}`
covapie_adapter_auxiliary_label_qa_audit_row_count: `{manifest["covapie_adapter_auxiliary_label_qa_audit_row_count"]}`
covapie_adapter_execution_boundary_qa_audit_row_count: `{manifest["covapie_adapter_execution_boundary_qa_audit_row_count"]}`
covapie_adapter_feature_semantics_qa_audit_row_count: `{manifest["covapie_adapter_feature_semantics_qa_audit_row_count"]}`
covapie_adapter_dependency_qa_audit_row_count: `{manifest["covapie_adapter_dependency_qa_audit_row_count"]}`
covapie_adapter_source_ast_safety_qa_audit_row_count: `{manifest["covapie_adapter_source_ast_safety_qa_audit_row_count"]}`
adapter_implemented_in_step13ac: `{manifest["adapter_implemented_in_step13ac"]}`
torch_imported_in_step13ac: `{manifest["torch_imported_in_step13ac"]}`
adapter_implemented: `{manifest["adapter_implemented"]}`
torch_imported: `{manifest["torch_imported"]}`
torch_tensor_created: `{manifest["torch_tensor_created"]}`
tensor_artifact_written: `{manifest["tensor_artifact_written"]}`
covapie_adapter_implementation_qa_gate_passed: `{manifest["covapie_adapter_implementation_qa_gate_passed"]}`
ready_for_covapie_batch_scale_data_preparation_design_gate: `{manifest["ready_for_covapie_batch_scale_data_preparation_design_gate"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = qa.run_covapie_adapter_implementation_qa_gate_v0()
    write_csv(result["input_qa_rows"], qa.INPUT_QA_AUDIT_CSV, qa.INPUT_QA_COLUMNS)
    write_csv(result["sample_dict_qa_rows"], qa.SAMPLE_DICT_QA_AUDIT_CSV, qa.SAMPLE_DICT_QA_COLUMNS)
    write_csv(result["field_shape_qa_rows"], qa.FIELD_SHAPE_QA_AUDIT_CSV, qa.FIELD_SHAPE_QA_COLUMNS)
    write_csv(result["batch_qa_rows"], qa.SINGLE_SAMPLE_BATCH_QA_AUDIT_CSV, qa.SINGLE_SAMPLE_BATCH_QA_COLUMNS)
    write_csv(result["mask_mapping_qa_rows"], qa.MASK_MAPPING_QA_AUDIT_CSV, qa.MASK_MAPPING_QA_COLUMNS)
    write_csv(result["auxiliary_label_qa_rows"], qa.AUXILIARY_LABEL_QA_AUDIT_CSV, qa.AUXILIARY_LABEL_QA_COLUMNS)
    write_csv(result["execution_boundary_qa_rows"], qa.EXECUTION_BOUNDARY_QA_AUDIT_CSV, qa.EXECUTION_BOUNDARY_QA_COLUMNS)
    write_csv(result["feature_semantics_qa_rows"], qa.FEATURE_SEMANTICS_QA_AUDIT_CSV, qa.FEATURE_SEMANTICS_QA_COLUMNS)
    write_csv(result["dependency_qa_rows"], qa.DEPENDENCY_QA_AUDIT_CSV, qa.DEPENDENCY_QA_COLUMNS)
    write_csv(result["source_ast_safety_qa_rows"], qa.SOURCE_AST_SAFETY_QA_AUDIT_CSV, qa.SOURCE_AST_SAFETY_QA_COLUMNS)
    write_csv(build_report_rows(result), qa.REPORT_CSV, qa.REPORT_COLUMNS)
    write_json(result["manifest"], qa.MANIFEST_JSON)
    write_summary(result["manifest"], qa.SUMMARY_MD)
    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("covapie_diffsbdd_loader_adapter_implementation_qa_gate_v0_passed")
    else:
        print("covapie_diffsbdd_loader_adapter_implementation_qa_gate_v0_blocked")
    for key in [
        "covapie_adapter_input_qa_audit_row_count",
        "covapie_adapter_sample_dict_qa_audit_row_count",
        "covapie_adapter_field_shape_qa_audit_row_count",
        "covapie_adapter_single_sample_batch_qa_audit_row_count",
        "covapie_adapter_mask_mapping_qa_audit_row_count",
        "covapie_adapter_auxiliary_label_qa_audit_row_count",
        "covapie_adapter_execution_boundary_qa_audit_row_count",
        "covapie_adapter_feature_semantics_qa_audit_row_count",
        "covapie_adapter_dependency_qa_audit_row_count",
        "covapie_adapter_source_ast_safety_qa_audit_row_count",
        "naming_convention_validated",
        "adapter_implemented_in_step13ac",
        "torch_imported_in_step13ac",
        "adapter_implemented",
        "torch_imported",
        "torch_tensor_created",
        "covapie_adapter_implementation_qa_gate_passed",
        "ready_for_covapie_batch_scale_data_preparation_design_gate",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
    ]:
        print(f"{key}={manifest[key]}")
    if manifest["blocking_reasons"]:
        print("blocking_reasons=" + ";".join(manifest["blocking_reasons"]))
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
