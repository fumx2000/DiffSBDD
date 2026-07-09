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

from covalent_ext import covapie_cys_sg_ligand_covale_annotation_alignment_gate as gate  # noqa: E402


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
    text = f"""# CovaPIE CYS/SG Ligand Covale Annotation Alignment Gate v0 Summary

Step 14J aligns the Step 14I ligand covale candidates against the local CovPDB manual metadata CSV.
It does not use network access, download files, read raw CIF content, create ready candidates, create sample/final/split/leakage artifacts, instantiate a dataloader, or train.

input_ligand_covale_candidate_count: `{manifest["input_ligand_covale_candidate_count"]}`
annotation_alignment_candidate_count: `{manifest["annotation_alignment_candidate_count"]}`
metadata_pdb_match_count: `{manifest["metadata_pdb_match_count"]}`
metadata_ligand_or_het_alignment_count: `{manifest["metadata_ligand_or_het_alignment_count"]}`
metadata_event_annotation_gap_count: `{manifest["metadata_event_annotation_gap_count"]}`
metadata_conflict_count: `{manifest["metadata_conflict_count"]}`
all_annotation_alignment_candidates_pending_manual_review: `{manifest["all_annotation_alignment_candidates_pending_manual_review"]}`
ready_for_covapie_cys_sg_targeted_metadata_expansion_gate_after_alignment_if_below_20: `{manifest["ready_for_covapie_cys_sg_targeted_metadata_expansion_gate_after_alignment_if_below_20"]}`
ready_for_training: `{manifest["ready_for_training"]}`
recommended_next_step: `{manifest["recommended_next_step"]}`

PDB ID and CovPDB ligand IDs remain context fields, not event identity. Formal training, fine-tuning, or real parameter updates still require a separate feature semantics audit and leakage/split design gate.
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.run_covapie_cys_sg_ligand_covale_annotation_alignment_gate_v0()
    write_csv(result["precondition_rows"], gate.PRECONDITION_AUDIT_CSV, gate.PRECONDITION_COLUMNS)
    write_csv(result["metadata_schema_rows"], gate.METADATA_SCHEMA_AUDIT_CSV, gate.METADATA_SCHEMA_COLUMNS)
    write_csv(result["candidate_input_rows"], gate.CANDIDATE_INPUT_AUDIT_CSV, gate.CANDIDATE_INPUT_COLUMNS)
    write_csv(result["policy_rows"], gate.POLICY_CONTRACT_CSV, gate.POLICY_COLUMNS)
    write_csv(result["alignment_rows"], gate.ALIGNMENT_CANDIDATES_CSV, gate.ALIGNMENT_COLUMNS)
    write_json(result["alignment_rows"], gate.ALIGNMENT_CANDIDATES_JSON)
    write_csv(result["gap_rows"], gate.GAP_AUDIT_CSV, gate.GAP_COLUMNS)
    write_csv(result["downstream_rows"], gate.DOWNSTREAM_READINESS_CONTRACT_CSV, gate.DOWNSTREAM_COLUMNS)
    write_csv(result["safety_rows"], gate.SAFETY_AUDIT_CSV, gate.SAFETY_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)

    manifest = result["manifest"]
    print("covapie_cys_sg_ligand_covale_annotation_alignment_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_cys_sg_ligand_covale_annotation_alignment_gate_v0_blocked")
    for key in [
        "input_ligand_covale_candidate_count",
        "annotation_alignment_candidate_count",
        "metadata_pdb_match_count",
        "metadata_ligand_or_het_alignment_count",
        "metadata_event_annotation_gap_count",
        "metadata_conflict_count",
        "all_annotation_alignment_candidates_pending_manual_review",
        "ready_candidate_count_current_step",
        "ready_for_covapie_cys_sg_targeted_metadata_expansion_gate_after_alignment_if_below_20",
        "ready_for_training",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
