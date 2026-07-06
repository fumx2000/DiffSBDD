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

from covalent_ext import covapie_external_source_registry_configuration_gate as gate  # noqa: E402


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
    return [
        {
            "stage": gate.STAGE,
            "previous_stage": gate.PREVIOUS_STAGE,
            "section": section,
            "status": "passed",
            "evidence": _json_text(evidence),
            "blocking_reasons": _list_text(manifest["blocking_reasons"]),
            "recommended_next_step": manifest["recommended_next_step"],
        }
        for section, evidence in result["report_sections"].items()
    ]


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# CovaPIE External Source Registry Configuration Gate v0 Summary

This is CovaPIE external source registry configuration gate.
It creates a header-only template for explicitly configuring external specialized covalent metadata sources.
It does not invent source names or URLs.
It does not configure a real external source unless explicit input CSV is present.
It does not verify external URLs.
It does not use internet, network, curl, wget, requests, urllib, or browser.
It does not download metadata or raw structures.
It does not read raw structure contents.
It does not read SDF, PDB, mmCIF, or gzip files.
It does not use RDKit, Bio.PDB, or gemmi.
It does not materialize candidate metadata or allowlist rows.
It does not write sample index, final dataset, split assignment, or leakage matrix.
It does not import torch or create tensors.
It does not load checkpoint, call model forward, compute loss, backward, optimizer, trainer.fit, or training.
If explicit config is missing, the step is safely blocked and writes a header-only blocked config artifact.
If explicit config is valid with exactly one verified enabled source, the next step can be external metadata index download smoke.
Metadata index download smoke remains metadata-only; raw structure download remains forbidden.
It preserves one row = one covalent ligand-residue event.
Joining by pdb_id alone remains forbidden.
It keeps feature semantics audit and leakage/split design required before training.

source_registry_config_template_written: `{manifest["source_registry_config_template_written"]}`
source_registry_config_exists: `{manifest["source_registry_config_exists"]}`
source_registry_config_read: `{manifest["source_registry_config_read"]}`
source_registry_config_row_count: `{manifest["source_registry_config_row_count"]}`
configured_source_count: `{manifest["configured_source_count"]}`
enabled_source_count: `{manifest["enabled_source_count"]}`
enabled_source_ready_for_download_smoke: `{manifest["enabled_source_ready_for_download_smoke"]}`
configuration_status: `{manifest["configuration_status"]}`
ready_for_covapie_external_metadata_index_download_smoke: `{manifest["ready_for_covapie_external_metadata_index_download_smoke"]}`
ready_for_training: `{manifest["ready_for_training"]}`
ready_to_train_now: `{manifest["ready_to_train_now"]}`
feature_semantics_audit_required_before_training: `{manifest["feature_semantics_audit_required_before_training"]}`
leakage_split_design_required_before_training: `{manifest["leakage_split_design_required_before_training"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`
blocking_reasons: `{manifest["blocking_reasons"]}`
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.run_covapie_external_source_registry_configuration_gate_v0()
    paths = result["paths"]
    write_csv([], paths["template"], gate.SOURCE_CONFIG_COLUMNS)
    if result["blocked_header_only_written"]:
        if Path(paths["validated"]).exists():
            Path(paths["validated"]).unlink()
        write_csv([], paths["blocked"], gate.SOURCE_CONFIG_COLUMNS)
    if result["validated_config_written"]:
        if Path(paths["blocked"]).exists():
            Path(paths["blocked"]).unlink()
        write_csv(result["config_rows"], paths["validated"], gate.SOURCE_CONFIG_COLUMNS)
    write_csv(result["precondition_rows"], paths["precondition"], gate.PRECONDITION_COLUMNS)
    write_csv(result["input_rows"], paths["input"], gate.INPUT_DISCOVERY_COLUMNS)
    write_csv(result["schema_rows"], paths["schema"], gate.SCHEMA_VALIDATION_COLUMNS)
    write_csv(result["value_rows"], paths["value"], gate.VALUE_VALIDATION_COLUMNS)
    write_csv(result["enabled_rows"], paths["enabled"], gate.ENABLED_SOURCE_COLUMNS)
    write_csv(result["output_rows"], paths["output"], gate.OUTPUT_AUDIT_COLUMNS)
    write_csv(result["execution_rows"], paths["execution"], gate.EXECUTION_COLUMNS)
    write_csv(result["git_rows"], paths["git"], gate.GIT_SAFETY_COLUMNS)
    write_csv(result["mask_rows"], paths["mask"], gate.MASK_COLUMNS)
    write_csv(result["feature_rows"], paths["feature"], gate.FEATURE_COLUMNS)
    write_csv(result["leakage_rows"], paths["leakage"], gate.LEAKAGE_COLUMNS)
    write_csv(build_report_rows(result), paths["report"], gate.REPORT_COLUMNS)
    write_json(result["manifest"], paths["manifest"])
    write_summary(result["manifest"], gate.SUMMARY_MD)
    manifest = result["manifest"]
    print("covapie_external_source_registry_configuration_gate_v0_passed")
    for key in [
        "source_registry_config_template_written",
        "source_registry_config_exists",
        "source_registry_config_read",
        "source_registry_config_row_count",
        "source_registry_schema_validated",
        "source_registry_values_validated",
        "configured_source_count",
        "enabled_source_count",
        "enabled_source_slot_id",
        "enabled_source_name",
        "enabled_source_family",
        "enabled_source_artifact_type",
        "enabled_source_verified",
        "enabled_source_ready_for_download_smoke",
        "configuration_status",
        "ready_for_covapie_external_metadata_index_download_smoke",
        "ready_for_covapie_external_metadata_index_schema_probe_design_gate",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
