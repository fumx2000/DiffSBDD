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

from covalent_ext import real_covalent_confirmed_candidate_ligand_topology_smoke_current_cys_goldens as gate  # noqa: E402


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
    status = "passed" if manifest["all_checks_passed"] else "blocked"
    decision = (
        "ligand topology smoke passed"
        if manifest["all_checks_passed"]
        else "blocked_pending_step8_per_atom_per_bond_topology_evidence"
    )
    rows: list[dict[str, str]] = []
    for section, evidence in result["report_sections"].items():
        rows.append(
            {
                "stage": gate.STAGE,
                "previous_stage": gate.PREVIOUS_STAGE,
                "section": section,
                "status": status,
                "evidence": _json_text(evidence),
                "decision": decision,
                "blocking_reasons": "" if manifest["all_checks_passed"] else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    parser_tools = (
        f"{gate.BIOPDB_TEXT}/{gate.MMCIF_PARSER_TEXT}/"
        f"{gate.PDB_PARSER_TEXT}/{gate.VENDOR_TEXT}/{gate.RDKIT_TEXT}"
    )
    status_line = (
        "The topology evidence was sufficient, so atom topology rows=104 and bond topology rows=113."
        if manifest["all_checks_passed"]
        else "The topology smoke is blocked because existing Step 8 evidence lacks per-atom and per-bond topology evidence."
    )
    next_line = (
        "The next step is sample index design gate, not training."
        if manifest["all_checks_passed"]
        else "The next step is to locate or export Step 8 per-bond topology evidence, not training."
    )
    text = f"""# Real Covalent Confirmed Candidate Ligand Topology Smoke Current CYS Goldens v0 Summary

Step 13O is a ligand topology smoke for the current CYS/SG golden samples only.
Topology evidence is limited to Step 8 manual-reviewed pre-reaction provenance or existing graph preview.
This step did not automatically restore ligands.
This step did not read, generate, modify, or copy SDF files.
This step did not use {parser_tools}.
This step did not generalize to non-CYS residue classes or unknown warheads.
This step did not write sample_index, enriched_sample_index, final_dataset, or model input.
This step did not run forward, loss, backward, optimizer, trainer, checkpoint, model save, or tensor dump.
This step did not train.
{status_line}
This is an expected-blocked diagnostic artifact. The script passes only because the missing topology evidence was correctly detected; ligand topology smoke itself did not pass.
Feature semantics audit is still required before formal training.
{next_line}

Recommended next step: `{manifest["recommended_next_step"]}`.
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def expected_blocked_diagnostic_passed(manifest: dict[str, Any]) -> bool:
    expected_values = {
        "stage": gate.STAGE,
        "step13n_ligand_topology_policy_review_gate_validated": True,
        "all_checks_passed": False,
        "all_step8_topology_artifacts_found": True,
        "all_artifacts_contain_per_atom_topology": False,
        "all_artifacts_contain_per_bond_topology": False,
        "all_artifacts_sufficient_for_topology_smoke": False,
        "ligand_observed_atom_topology_table_written": False,
        "ligand_observed_bond_topology_table_written": False,
        "ligand_observed_atom_topology_table_row_count": 0,
        "ligand_observed_bond_topology_table_row_count": 0,
        "all_ligand_topology_smoke_passed": False,
        "ready_for_sample_index_design_gate": False,
        "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "recommended_next_step": gate.BLOCKED_NEXT_STEP,
    }
    false_safety_keys = [
        "rdkit_used",
        "sdf_read_for_topology",
        "sdf_generated",
        "sdf_modified",
        "sdf_copied",
        "ligand_auto_restoration_run",
        "non_cys_generalization_run",
        "sample_index_written",
        "model_input_materialized",
        "training_allowed",
        "finetune_allowed",
        "parameter_update_allowed",
        "checkpoint_saved",
        "model_saved",
        "tensor_dump_saved",
        gate.GZIP_OPEN_KEY,
        "raw_files_read",
        "mmcif_text_read",
        "atom_site_text_scan_run",
    ]
    return (
        all(manifest.get(key) == value for key, value in expected_values.items())
        and "step8_per_atom_or_per_bond_topology_evidence_missing" in manifest["blocking_reasons"]
        and all(manifest.get(key) is False for key in false_safety_keys)
    )


def run() -> int:
    result = gate.build_real_covalent_confirmed_candidate_ligand_topology_smoke_current_cys_goldens_v0()
    write_csv(result["artifact_discovery_rows"], gate.ARTIFACT_DISCOVERY_AUDIT_CSV, gate.ARTIFACT_DISCOVERY_COLUMNS)
    write_csv(result["atom_topology_rows"], gate.ATOM_TOPOLOGY_TABLE_CSV, gate.ATOM_TOPOLOGY_COLUMNS)
    write_csv(result["bond_topology_rows"], gate.BOND_TOPOLOGY_TABLE_CSV, gate.BOND_TOPOLOGY_COLUMNS)
    write_csv(result["topology_smoke_audit_rows"], gate.TOPOLOGY_SMOKE_AUDIT_CSV, gate.TOPOLOGY_SMOKE_AUDIT_COLUMNS)
    write_csv(build_report_rows(result), gate.REPORT_CSV, REPORT_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)
    manifest = result["manifest"]
    expected_blocked = expected_blocked_diagnostic_passed(manifest)
    if manifest["all_checks_passed"]:
        status = "passed"
    elif expected_blocked:
        status = "blocked_as_expected"
    else:
        status = "blocked_unexpected"
    print(f"real_covalent_confirmed_candidate_ligand_topology_smoke_current_cys_goldens_only_v0_{status}")
    print(f"artifact_discovery_audit_row_count={manifest['artifact_discovery_audit_row_count']}")
    print(f"all_artifacts_sufficient_for_topology_smoke={manifest['all_artifacts_sufficient_for_topology_smoke']}")
    print(f"recommended_next_step={manifest['recommended_next_step']}")
    if manifest["blocking_reasons"]:
        print("blocking_reasons=" + ";".join(manifest["blocking_reasons"]))
    return 0 if manifest["all_checks_passed"] or expected_blocked else 1


if __name__ == "__main__":
    raise SystemExit(run())
