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

from covalent_ext import covapie_independent_group_expansion_candidate_review_gate as gate


def write_csv(rows: list[dict], path: Path, fields: list[str]) -> None:
    output = ROOT / path
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])


def main() -> int:
    result = gate.run_covapie_independent_group_expansion_candidate_review_gate_v0()
    for rows, path, fields in [
        (result["preconditions"], gate.PRECONDITION_AUDIT, gate.PRE_COLUMNS), (result["reviews"], gate.REVIEW_REGISTRY, gate.REVIEW_COLUMNS), (result["diversity"], gate.DIVERSITY_REVIEW, gate.DIVERSITY_COLUMNS), (result["preflight"], gate.PREFLIGHT_PLAN, gate.PREFLIGHT_COLUMNS), (result["decisions"], gate.DECISION_REGISTRY, gate.DECISION_COLUMNS), (result["issues"], gate.ISSUE_INVENTORY, gate.ISSUE_COLUMNS), (result["evidence"], gate.EVIDENCE_CONTRACT, gate.EVIDENCE_COLUMNS), (result["readiness"], gate.READINESS_CONTRACT, gate.READINESS_COLUMNS), (result["safety"], gate.SAFETY_AUDIT, gate.SAFETY_COLUMNS),
    ]:
        write_csv(rows, path, fields)
    (ROOT / gate.MANIFEST).write_text(json.dumps(result["manifest"], indent=2) + "\n", encoding="utf-8")
    manifest = result["manifest"]
    (ROOT / gate.SUMMARY).write_text(
        "# CovaPIE Independent Group Expansion Candidate Review Gate v0\n\n"
        "Step 14AJ approves eight candidates for controlled acquisition preflight only. It does not authorize acquisition execution, networking, downloads, raw reads, independence confirmation, split materialization, final-dataset materialization, or training.\n\n"
        f"- candidate_review_approved_for_preflight_count: `{manifest['candidate_review_approved_for_preflight_count']}`\n"
        f"- candidate_review_approved_for_execution_count: `{manifest['candidate_review_approved_for_execution_count']}`\n"
        f"- confirmed_new_independent_group_count_current_step: `{manifest['confirmed_new_independent_group_count_current_step']}`\n"
        f"- recommended_next_step: `{manifest['recommended_next_step']}`\n",
        encoding="utf-8",
    )
    label = "covapie_independent_group_expansion_candidate_review_gate_v0_passed" if manifest["all_checks_passed"] else "covapie_independent_group_expansion_candidate_review_gate_v0_blocked"
    print(label)
    print(f"candidate_review_count={manifest['candidate_review_count']}")
    print(f"candidate_review_approved_for_preflight_count={manifest['candidate_review_approved_for_preflight_count']}")
    print(f"recommended_next_step={manifest['recommended_next_step']}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
