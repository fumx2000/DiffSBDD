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

from covalent_ext import covapie_cys_sg_discovery_support_review_gate as gate  # noqa: E402


def _csv_value(value: Any) -> Any:
    if isinstance(value, (list, dict, set)):
        return json.dumps(sorted(value) if isinstance(value, set) else value, sort_keys=True)
    return value


def write_csv(rows: list[dict[str, Any]], path: str | Path, fieldnames: list[str]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key, "")) for key in fieldnames})


def write_json(data: Any, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    text = f"""# CovaPIE CYS/SG Discovery Support Review Gate v0 Summary

Step 14I reads the Step 14H CYS/SG discovery proposals and separates disulfide or SG--SG protein-protein rows from ligand covale candidates.
It does not download, read raw CIF content, create ready candidates, create sample/final/split/leakage artifacts, instantiate a dataloader, or train.

input_support_proposal_count: `{manifest["input_support_proposal_count"]}`
disulfide_excluded_count: `{manifest["disulfide_excluded_count"]}`
other_excluded_or_triage_count: `{manifest["other_excluded_or_triage_count"]}`
ligand_covale_candidate_count: `{manifest["ligand_covale_candidate_count"]}`
unique_ligand_covale_pdb_count: `{manifest["unique_ligand_covale_pdb_count"]}`
all_ligand_covale_candidates_pending_manual_review: `{manifest["all_ligand_covale_candidates_pending_manual_review"]}`
ready_for_covapie_cys_sg_ligand_covale_annotation_alignment_gate: `{manifest["ready_for_covapie_cys_sg_ligand_covale_annotation_alignment_gate"]}`
ready_for_training: `{manifest["ready_for_training"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`

The retained ligand covale rows are still pending CovPDB annotation alignment and manual review. Formal training, fine-tuning, or real parameter updates still require a separate feature semantics audit and leakage/split design gate.
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.run_covapie_cys_sg_discovery_support_review_gate_v0()
    write_csv(result["precondition_rows"], gate.PRECONDITION_AUDIT_CSV, gate.PRECONDITION_COLUMNS)
    write_csv(result["input_rows"], gate.INPUT_PROPOSAL_AUDIT_CSV, gate.INPUT_AUDIT_COLUMNS)
    write_csv(result["policy_rows"], gate.POLICY_CONTRACT_CSV, gate.POLICY_COLUMNS)
    write_csv(result["disulfide_rows"], gate.DISULFIDE_EXCLUSION_AUDIT_CSV, gate.DISULFIDE_AUDIT_COLUMNS)
    write_csv(result["candidates"], gate.LIGAND_COVALE_CANDIDATES_CSV, gate.LIGAND_COVALE_COLUMNS)
    write_json(result["candidates"], gate.LIGAND_COVALE_CANDIDATES_JSON)
    write_csv(result["decision_rows"], gate.DECISION_AUDIT_CSV, gate.DECISION_COLUMNS)
    write_csv(result["downstream_rows"], gate.DOWNSTREAM_READINESS_CONTRACT_CSV, gate.DOWNSTREAM_COLUMNS)
    write_csv(result["safety_rows"], gate.SAFETY_AUDIT_CSV, gate.SAFETY_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_cys_sg_discovery_support_review_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_cys_sg_discovery_support_review_gate_v0_blocked")
    for key in [
        "input_support_proposal_count",
        "disulfide_excluded_count",
        "other_excluded_or_triage_count",
        "ligand_covale_candidate_count",
        "unique_ligand_covale_pdb_count",
        "ligand_covale_candidates_csv_json_consistent",
        "all_ligand_covale_candidates_pending_manual_review",
        "ready_candidate_count_current_step",
        "ready_for_covapie_cys_sg_ligand_covale_annotation_alignment_gate",
        "ready_for_training",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
