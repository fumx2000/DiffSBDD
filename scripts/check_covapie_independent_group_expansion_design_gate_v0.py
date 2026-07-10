#!/usr/bin/env python
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import covapie_independent_group_expansion_design_gate as gate


def write_csv(rows: list[dict], path: Path, fieldnames: list[str]) -> None:
    output = ROOT / path
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fieldnames} for row in rows])


def main() -> int:
    result = gate.run_covapie_independent_group_expansion_design_gate_v0()
    for rows, path, fields in [
        (result["preconditions"], gate.PRECONDITION_AUDIT, gate.PRE_COLUMNS),
        (result["source"], gate.SOURCE_AUDIT, gate.SOURCE_COLUMNS),
        (result["exclusions"], gate.EXCLUSION_AUDIT, gate.EXCLUSION_COLUMNS),
        (result["evidence"], gate.EVIDENCE_CONTRACT, gate.EVIDENCE_COLUMNS),
        (result["shortlist"], gate.SHORTLIST_CSV, gate.SHORTLIST_COLUMNS),
        (result["plans"], gate.ACQUISITION_PLAN, gate.PLAN_COLUMNS),
        (result["policy"], gate.POLICY_CONTRACT, gate.POLICY_COLUMNS),
        (result["safety"], gate.SAFETY_AUDIT, gate.SAFETY_COLUMNS),
    ]:
        write_csv(rows, path, fields)
    (ROOT / gate.SHORTLIST_JSON).write_text(json.dumps(result["shortlist"], indent=2) + "\n", encoding="utf-8")
    (ROOT / gate.MANIFEST).write_text(json.dumps(result["manifest"], indent=2) + "\n", encoding="utf-8")
    summary = result["manifest"]
    (ROOT / gate.SUMMARY).write_text(
        "# CovaPIE Independent Group Expansion Design Gate v0\n\n"
        "Step 14AI uses the committed Step 14O controlled candidate pool and Step 14P status as read-only inputs. "
        "Its shortlist is for manual review and a future controlled raw mmCIF struct_conn crosscheck only. "
        "Different HET IDs provide provisional acquisition diversification, not confirmed leakage-group independence.\n\n"
        f"- shortlist_candidate_count: `{summary['shortlist_candidate_count']}`\n"
        f"- shortlist_distinct_non_jug_het_id_count: `{summary['shortlist_distinct_non_jug_het_id_count']}`\n"
        f"- confirmed_new_independent_group_count_current_step: `{summary['confirmed_new_independent_group_count_current_step']}`\n"
        f"- recommended_next_step: `{summary['recommended_next_step']}`\n",
        encoding="utf-8",
    )
    label = "covapie_independent_group_expansion_design_gate_v0_passed" if summary["all_checks_passed"] else "covapie_independent_group_expansion_design_gate_v0_blocked"
    print(label)
    print(f"candidate_source_record_count={summary['candidate_source_record_count']}")
    print(f"shortlist_candidate_count={summary['shortlist_candidate_count']}")
    print(f"shortlist_distinct_non_jug_het_id_count={summary['shortlist_distinct_non_jug_het_id_count']}")
    print(f"recommended_next_step={summary['recommended_next_step']}")
    return 0 if summary["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
