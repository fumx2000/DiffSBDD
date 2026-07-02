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

from covalent_ext import real_covalent_struct_conn_candidate_human_review_table as gate  # noqa: E402


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
            writer.writerow({key: _csv_value(row[key]) for key in fieldnames})


def write_json(data: dict[str, Any], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_report_rows(result: dict[str, Any]) -> list[dict[str, str]]:
    manifest = result["manifest"]
    blockers = _list_text(manifest["blocking_reasons"])
    sections = [
        ("step13a_precondition", manifest["step13a_struct_conn_candidate_adapter_merge_smoke_validated"]),
        ("human_review_table_execution", manifest["struct_conn_candidate_human_review_table_executed"]),
        ("priority_sorting", manifest["high_priority_rows_first"]),
        ("manual_review_columns", manifest["all_manual_review_columns_blank"]),
        ("candidate_status_preservation", manifest["all_rows_preserve_candidate_status"]),
        ("no_inference_no_training_boundary", manifest["all_inference_flags_false"]),
        ("output_artifact_policy", manifest["output_limited_to_csv_json_md"]),
        ("next_step_decision", manifest["real_covalent_struct_conn_candidate_human_review_table_passed"]),
    ]
    rows: list[dict[str, str]] = []
    for section, passed in sections:
        rows.append(
            {
                "stage": gate.STAGE,
                "previous_stage": gate.PREVIOUS_STAGE,
                "section": section,
                "status": "passed" if passed else "blocked",
                "evidence": _json_text(result["report_sections"][section]),
                "decision": "human review table contract satisfied" if passed else "human review table blocked",
                "blocking_reasons": "" if passed else blockers,
                "recommended_next_step": manifest["recommended_next_step"],
            }
        )
    return rows


def write_summary(manifest: dict[str, Any], path: str | Path) -> None:
    no_parser_tools = f"{gate.BIOPDB_TEXT}/{gate.MMCIF_PARSER_TEXT}/{gate.PDB_PARSER_TEXT}/{gate.VENDOR_TEXT}/{gate.RDKIT_TEXT}"
    manual_columns = "\n".join(f"- {column}" for column in gate.MANUAL_REVIEW_COLUMNS)
    text = f"""# Real Covalent Struct Conn Candidate Human Review Table v0 Summary

Step 13B is an actual struct_conn candidate human review table.

This step read the Step 13A candidate-enriched stub CSV.
It did not read raw `.cif.gz`, did not decompress raw files, and did not parse mmCIF.
It did not use {no_parser_tools}.
It did not run coordinate geometry, distance calculation, UniProt/CD-HIT, NPZ reads, or training.

The step generated a human-reviewable candidate table.
- human_review_table_row_count: {manifest["human_review_table_row_count"]}
- candidate_like_review_row_count: {manifest["candidate_like_review_row_count"]}
- high_priority_review_row_count: {manifest["high_priority_review_row_count"]}
- audit_review_row_count: {manifest["audit_review_row_count"]}

Candidate-like rows are sorted first. The table preserves ptnr1/ptnr2 atom identifiers, conn_type_id, pdbx_dist_value, and pdbx_role.

Manual review blank columns:
{manual_columns}

This step did not fill manual review decision.
It did not infer ligand/residue role, did not infer warhead_type, and did not claim covalent_bond_atom_pair is chemically verified.
All rows have human_review_required=true and training_ready=false.
This step did not write enriched sample_index and did not write final dataset.

Next step is manual fill of the human review table, not training.
"""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def run() -> int:
    result = gate.build_real_covalent_struct_conn_candidate_human_review_table_v0()
    write_csv(build_report_rows(result), gate.REPORT_CSV, REPORT_COLUMNS)
    write_csv(result["review_rows"], gate.HUMAN_REVIEW_TABLE_CSV, gate.HUMAN_REVIEW_COLUMNS)
    write_json(result["manifest"], gate.MANIFEST_JSON)
    write_summary(result["manifest"], gate.SUMMARY_MD)
    print(
        "real_covalent_struct_conn_candidate_human_review_table_v0_"
        + ("passed" if result["manifest"]["all_checks_passed"] else "blocked")
    )
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
    return 0 if result["manifest"]["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
