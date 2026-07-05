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

from covalent_ext import real_covalent_confirmed_candidate_diffsbdd_loader_adapter_design_gate as gate  # noqa: E402


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
                "stage": gate.STAGE,
                "previous_stage": gate.PREVIOUS_STAGE,
                "section": section,
                "status": "passed" if manifest["all_checks_passed"] else "blocked",
                "evidence": _json_text(evidence),
                "decision": "DiffSBDD loader adapter design gate passed"
                if manifest["all_checks_passed"]
                else "DiffSBDD loader adapter design gate blocked",
                "blocking_reasons": "" if manifest["all_checks_passed"] else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# Real Covalent Confirmed Candidate DiffSBDD Loader Adapter Design Gate v0 Summary

Step 13AB is DiffSBDD loader adapter design gate only.
It does not implement the adapter.
It does not modify original DiffSBDD dataloader, forward, loss, equivariant_diffusion/, or lightning_modules.py.
It designs an external adapter under covalent_ext to preserve checkpoint compatibility.
It maps current 14 shape items, 5 canonical masks including scaffold_only/B3, and 3 auxiliary labels.
It keeps auxiliary labels out of loss integration for now.
It does not import torch, create tensors, instantiate loader, or train.
It keeps feature semantics audit required before formal training.
It allows adapter implementation smoke next, not training.

diffsbdd_loader_adapter_input_contract_row_count: `{manifest["diffsbdd_loader_adapter_input_contract_row_count"]}`
diffsbdd_loader_adapter_source_discovery_audit_row_count: `{manifest["diffsbdd_loader_adapter_source_discovery_audit_row_count"]}`
diffsbdd_loader_adapter_interface_contract_row_count: `{manifest["diffsbdd_loader_adapter_interface_contract_row_count"]}`
diffsbdd_loader_adapter_shape_mapping_contract_row_count: `{manifest["diffsbdd_loader_adapter_shape_mapping_contract_row_count"]}`
diffsbdd_loader_adapter_mask_mapping_contract_row_count: `{manifest["diffsbdd_loader_adapter_mask_mapping_contract_row_count"]}`
diffsbdd_loader_adapter_auxiliary_label_contract_row_count: `{manifest["diffsbdd_loader_adapter_auxiliary_label_contract_row_count"]}`
diffsbdd_loader_adapter_execution_boundary_contract_row_count: `{manifest["diffsbdd_loader_adapter_execution_boundary_contract_row_count"]}`
diffsbdd_loader_adapter_feature_semantics_boundary_row_count: `{manifest["diffsbdd_loader_adapter_feature_semantics_boundary_row_count"]}`
diffsbdd_loader_adapter_design_gate_passed: `{manifest["diffsbdd_loader_adapter_design_gate_passed"]}`
adapter_implemented: `{manifest["adapter_implemented"]}`
torch_imported: `{manifest["torch_imported"]}`
torch_tensor_created: `{manifest["torch_tensor_created"]}`
ready_for_diffsbdd_loader_adapter_implementation_smoke: `{manifest["ready_for_diffsbdd_loader_adapter_implementation_smoke"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.run_diffsbdd_loader_adapter_design_gate_v0()
    write_csv(result["input_contract_rows"], gate.INPUT_CONTRACT_CSV, gate.INPUT_CONTRACT_COLUMNS)
    write_csv(result["source_discovery_audit_rows"], gate.SOURCE_DISCOVERY_AUDIT_CSV, gate.SOURCE_DISCOVERY_AUDIT_COLUMNS)
    write_csv(result["interface_contract_rows"], gate.INTERFACE_CONTRACT_CSV, gate.INTERFACE_CONTRACT_COLUMNS)
    write_csv(result["shape_mapping_contract_rows"], gate.SHAPE_MAPPING_CONTRACT_CSV, gate.SHAPE_MAPPING_CONTRACT_COLUMNS)
    write_csv(result["mask_mapping_contract_rows"], gate.MASK_MAPPING_CONTRACT_CSV, gate.MASK_MAPPING_CONTRACT_COLUMNS)
    write_csv(result["auxiliary_label_contract_rows"], gate.AUXILIARY_LABEL_CONTRACT_CSV, gate.AUXILIARY_LABEL_CONTRACT_COLUMNS)
    write_csv(result["execution_boundary_contract_rows"], gate.EXECUTION_BOUNDARY_CONTRACT_CSV, gate.EXECUTION_BOUNDARY_CONTRACT_COLUMNS)
    write_csv(result["feature_semantics_boundary_rows"], gate.FEATURE_SEMANTICS_BOUNDARY_CSV, gate.FEATURE_SEMANTICS_BOUNDARY_COLUMNS)
    write_csv(build_report_rows(result), gate.REPORT_CSV, gate.REPORT_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)
    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("real_covalent_confirmed_candidate_diffsbdd_loader_adapter_design_gate_v0_passed")
    else:
        print("real_covalent_confirmed_candidate_diffsbdd_loader_adapter_design_gate_v0_blocked")
    print(f"diffsbdd_loader_adapter_input_contract_row_count={manifest['diffsbdd_loader_adapter_input_contract_row_count']}")
    print(
        "diffsbdd_loader_adapter_source_discovery_audit_row_count="
        f"{manifest['diffsbdd_loader_adapter_source_discovery_audit_row_count']}"
    )
    print(
        "diffsbdd_loader_adapter_interface_contract_row_count="
        f"{manifest['diffsbdd_loader_adapter_interface_contract_row_count']}"
    )
    print(
        "diffsbdd_loader_adapter_shape_mapping_contract_row_count="
        f"{manifest['diffsbdd_loader_adapter_shape_mapping_contract_row_count']}"
    )
    print(
        "diffsbdd_loader_adapter_mask_mapping_contract_row_count="
        f"{manifest['diffsbdd_loader_adapter_mask_mapping_contract_row_count']}"
    )
    print(
        "diffsbdd_loader_adapter_auxiliary_label_contract_row_count="
        f"{manifest['diffsbdd_loader_adapter_auxiliary_label_contract_row_count']}"
    )
    print(
        "diffsbdd_loader_adapter_execution_boundary_contract_row_count="
        f"{manifest['diffsbdd_loader_adapter_execution_boundary_contract_row_count']}"
    )
    print(
        "diffsbdd_loader_adapter_feature_semantics_boundary_row_count="
        f"{manifest['diffsbdd_loader_adapter_feature_semantics_boundary_row_count']}"
    )
    print(f"diffsbdd_loader_adapter_design_gate_passed={manifest['diffsbdd_loader_adapter_design_gate_passed']}")
    print(f"adapter_implemented={manifest['adapter_implemented']}")
    print(f"adapter_instantiated={manifest['adapter_instantiated']}")
    print(f"torch_imported={manifest['torch_imported']}")
    print(f"torch_tensor_created={manifest['torch_tensor_created']}")
    print(
        "ready_for_diffsbdd_loader_adapter_implementation_smoke="
        f"{manifest['ready_for_diffsbdd_loader_adapter_implementation_smoke']}"
    )
    print(f"ready_for_training={manifest['ready_for_training']}")
    print(f"ready_to_train_now={manifest['ready_to_train_now']}")
    print(f"recommended_next_step={manifest['recommended_next_step']}")
    if manifest["blocking_reasons"]:
        print("blocking_reasons=" + ";".join(manifest["blocking_reasons"]))
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
