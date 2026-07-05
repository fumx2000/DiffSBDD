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

from covalent_ext import (  # noqa: E402
    real_covalent_confirmed_candidate_diffsbdd_loader_adapter_implementation_smoke as smoke,
)


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
                "stage": smoke.STAGE,
                "previous_stage": smoke.PREVIOUS_STAGE,
                "section": section,
                "status": "passed" if manifest["all_checks_passed"] else "blocked",
                "evidence": _json_text(evidence),
                "decision": "DiffSBDD loader adapter implementation smoke passed"
                if manifest["all_checks_passed"]
                else "DiffSBDD loader adapter implementation smoke blocked",
                "blocking_reasons": "" if manifest["all_checks_passed"] else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# Real Covalent Confirmed Candidate DiffSBDD Loader Adapter Implementation Smoke v0 Summary

Step 13AC is DiffSBDD loader adapter implementation smoke.
It implements only a minimal external adapter under src/covalent_ext/.
It does not modify original DiffSBDD dataloader, forward, loss, equivariant_diffusion/, or lightning_modules.py.
It creates transient in-memory tensors only for adapter shape inspection.
It does not persist tensors and does not create PT or NPZ artifacts.
It does not load checkpoints, call model forward, compute loss, backward, optimizer, trainer.fit, or training.
It preserves five canonical mask tasks, including scaffold_only/B3.
It carries 3 auxiliary labels but does not integrate them into loss.
It does not claim training readiness or final DiffSBDD compatibility.
It keeps feature semantics audit required before formal training.
It allows adapter implementation QA gate next, not training.

diffsbdd_loader_adapter_input_audit_row_count: `{manifest["diffsbdd_loader_adapter_input_audit_row_count"]}`
diffsbdd_loader_adapter_sample_dict_audit_row_count: `{manifest["diffsbdd_loader_adapter_sample_dict_audit_row_count"]}`
diffsbdd_loader_adapter_field_shape_observation_row_count: `{manifest["diffsbdd_loader_adapter_field_shape_observation_row_count"]}`
diffsbdd_loader_adapter_single_sample_batch_audit_row_count: `{manifest["diffsbdd_loader_adapter_single_sample_batch_audit_row_count"]}`
diffsbdd_loader_adapter_mask_mapping_audit_row_count: `{manifest["diffsbdd_loader_adapter_mask_mapping_audit_row_count"]}`
diffsbdd_loader_adapter_auxiliary_label_audit_row_count: `{manifest["diffsbdd_loader_adapter_auxiliary_label_audit_row_count"]}`
diffsbdd_loader_adapter_execution_boundary_audit_row_count: `{manifest["diffsbdd_loader_adapter_execution_boundary_audit_row_count"]}`
diffsbdd_loader_adapter_feature_semantics_audit_row_count: `{manifest["diffsbdd_loader_adapter_feature_semantics_audit_row_count"]}`
diffsbdd_loader_adapter_dependency_audit_row_count: `{manifest["diffsbdd_loader_adapter_dependency_audit_row_count"]}`
adapter_implemented: `{manifest["adapter_implemented"]}`
adapter_instantiated: `{manifest["adapter_instantiated"]}`
torch_imported: `{manifest["torch_imported"]}`
torch_tensor_created: `{manifest["torch_tensor_created"]}`
tensor_artifact_written: `{manifest["tensor_artifact_written"]}`
npz_created: `{manifest["npz_created"]}`
pt_created: `{manifest["pt_created"]}`
diffsbdd_loader_adapter_implementation_smoke_passed: `{manifest["diffsbdd_loader_adapter_implementation_smoke_passed"]}`
ready_for_diffsbdd_loader_adapter_implementation_qa_gate: `{manifest["ready_for_diffsbdd_loader_adapter_implementation_qa_gate"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = smoke.run_diffsbdd_loader_adapter_implementation_smoke_v0()
    write_csv(result["input_audit_rows"], smoke.INPUT_AUDIT_CSV, smoke.INPUT_AUDIT_COLUMNS)
    write_csv(result["sample_dict_audit_rows"], smoke.SAMPLE_DICT_AUDIT_CSV, smoke.SAMPLE_DICT_AUDIT_COLUMNS)
    write_csv(
        result["field_shape_observation_rows"],
        smoke.FIELD_SHAPE_OBSERVATION_CSV,
        smoke.FIELD_SHAPE_OBSERVATION_COLUMNS,
    )
    write_csv(
        result["single_sample_batch_audit_rows"],
        smoke.SINGLE_SAMPLE_BATCH_AUDIT_CSV,
        smoke.SINGLE_SAMPLE_BATCH_AUDIT_COLUMNS,
    )
    write_csv(result["mask_mapping_audit_rows"], smoke.MASK_MAPPING_AUDIT_CSV, smoke.MASK_MAPPING_AUDIT_COLUMNS)
    write_csv(
        result["auxiliary_label_audit_rows"],
        smoke.AUXILIARY_LABEL_AUDIT_CSV,
        smoke.AUXILIARY_LABEL_AUDIT_COLUMNS,
    )
    write_csv(
        result["execution_boundary_audit_rows"],
        smoke.EXECUTION_BOUNDARY_AUDIT_CSV,
        smoke.EXECUTION_BOUNDARY_AUDIT_COLUMNS,
    )
    write_csv(
        result["feature_semantics_audit_rows"],
        smoke.FEATURE_SEMANTICS_AUDIT_CSV,
        smoke.FEATURE_SEMANTICS_AUDIT_COLUMNS,
    )
    write_csv(result["dependency_audit_rows"], smoke.DEPENDENCY_AUDIT_CSV, smoke.DEPENDENCY_AUDIT_COLUMNS)
    write_csv(build_report_rows(result), smoke.REPORT_CSV, smoke.REPORT_COLUMNS)
    write_json(result["manifest"], smoke.MANIFEST_JSON)
    write_summary(result["manifest"], smoke.SUMMARY_MD)
    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("real_covalent_confirmed_candidate_diffsbdd_loader_adapter_implementation_smoke_v0_passed")
    else:
        print("real_covalent_confirmed_candidate_diffsbdd_loader_adapter_implementation_smoke_v0_blocked")
    print(f"diffsbdd_loader_adapter_input_audit_row_count={manifest['diffsbdd_loader_adapter_input_audit_row_count']}")
    print(
        "diffsbdd_loader_adapter_sample_dict_audit_row_count="
        f"{manifest['diffsbdd_loader_adapter_sample_dict_audit_row_count']}"
    )
    print(
        "diffsbdd_loader_adapter_field_shape_observation_row_count="
        f"{manifest['diffsbdd_loader_adapter_field_shape_observation_row_count']}"
    )
    print(
        "diffsbdd_loader_adapter_single_sample_batch_audit_row_count="
        f"{manifest['diffsbdd_loader_adapter_single_sample_batch_audit_row_count']}"
    )
    print(f"diffsbdd_loader_adapter_mask_mapping_audit_row_count={manifest['diffsbdd_loader_adapter_mask_mapping_audit_row_count']}")
    print(
        "diffsbdd_loader_adapter_auxiliary_label_audit_row_count="
        f"{manifest['diffsbdd_loader_adapter_auxiliary_label_audit_row_count']}"
    )
    print(
        "diffsbdd_loader_adapter_execution_boundary_audit_row_count="
        f"{manifest['diffsbdd_loader_adapter_execution_boundary_audit_row_count']}"
    )
    print(
        "diffsbdd_loader_adapter_feature_semantics_audit_row_count="
        f"{manifest['diffsbdd_loader_adapter_feature_semantics_audit_row_count']}"
    )
    print(f"diffsbdd_loader_adapter_dependency_audit_row_count={manifest['diffsbdd_loader_adapter_dependency_audit_row_count']}")
    print(f"adapter_implemented={manifest['adapter_implemented']}")
    print(f"adapter_instantiated={manifest['adapter_instantiated']}")
    print(f"adapter_sample_count={manifest['adapter_sample_count']}")
    print(f"adapter_output_field_count={manifest['adapter_output_field_count']}")
    print(f"adapter_single_sample_batch_count={manifest['adapter_single_sample_batch_count']}")
    print(f"torch_imported={manifest['torch_imported']}")
    print(f"torch_tensor_created={manifest['torch_tensor_created']}")
    print(
        "diffsbdd_loader_adapter_implementation_smoke_passed="
        f"{manifest['diffsbdd_loader_adapter_implementation_smoke_passed']}"
    )
    print(
        "ready_for_diffsbdd_loader_adapter_implementation_qa_gate="
        f"{manifest['ready_for_diffsbdd_loader_adapter_implementation_qa_gate']}"
    )
    print(f"ready_for_training={manifest['ready_for_training']}")
    print(f"ready_to_train_now={manifest['ready_to_train_now']}")
    print(f"recommended_next_step={manifest['recommended_next_step']}")
    if manifest["blocking_reasons"]:
        print("blocking_reasons=" + ";".join(manifest["blocking_reasons"]))
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
