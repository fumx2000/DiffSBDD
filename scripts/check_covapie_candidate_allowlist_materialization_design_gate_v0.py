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

from covalent_ext import covapie_candidate_allowlist_materialization_design_gate as design_gate  # noqa: E402


def _csv_value(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True)
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


def write_summary(manifest: dict[str, Any], preview_rows: list[dict[str, Any]], path: str | Path) -> None:
    ids = "\n".join(f"- `{row['allowlist_entry_id_preview']}`" for row in preview_rows)
    text = f"""# CovaPIE Candidate Allowlist Materialization Design Gate v0 Summary

Step 13BA is a design gate for future candidate allowlist materialization.
It defines the future allowlist schema, candidate preview, unresolved exclusion policy, materialization plan, boundary safety, git safety, and training blockers.
It does not write a materialized candidate allowlist CSV or JSON.
It does not write sample_index, final_dataset, split assignments, or leakage matrix.
It does not use network access, raw downloads, raw text reads, RDKit/Bio.PDB/gemmi/gzip/torch, model calls, loss, optimizer, trainer.fit, or training.
The preview is design-only and limited to the four Step 13AZ-validated candidate metadata rows.

Preview allowlist entry IDs:
{ids}

allowlist_schema_field_count: `{manifest["allowlist_schema_field_count"]}`
allowlist_candidate_preview_row_count: `{manifest["allowlist_candidate_preview_row_count"]}`
allowlist_entry_id_preview_unique_count: `{manifest["allowlist_entry_id_preview_unique_count"]}`
candidate_allowlist_materialized: `{manifest["candidate_allowlist_materialized"]}`
candidate_allowlist_materialized_current_step: `{manifest["candidate_allowlist_materialized_current_step"]}`
ready_for_covapie_candidate_allowlist_materialization_smoke: `{manifest["ready_for_covapie_candidate_allowlist_materialization_smoke"]}`
ready_for_covapie_batch_scale_raw_read_design_gate: `{manifest["ready_for_covapie_batch_scale_raw_read_design_gate"]}`
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
    result = design_gate.run_covapie_candidate_allowlist_materialization_design_gate_v0()
    write_csv(result["precondition_rows"], design_gate.PRECONDITION_AUDIT_CSV, design_gate.PRECONDITION_COLUMNS)
    write_csv(result["schema_rows"], design_gate.SCHEMA_CONTRACT_CSV, design_gate.SCHEMA_COLUMNS)
    write_csv(result["preview_rows"], design_gate.CANDIDATE_PREVIEW_CSV, design_gate.PREVIEW_COLUMNS)
    write_csv(result["exclusion_rows"], design_gate.EXCLUSION_POLICY_CSV, design_gate.EXCLUSION_COLUMNS)
    write_csv(result["plan_rows"], design_gate.MATERIALIZATION_PLAN_CSV, design_gate.PLAN_COLUMNS)
    write_csv(result["boundary_rows"], design_gate.BOUNDARY_SAFETY_CSV, design_gate.BOUNDARY_COLUMNS)
    write_csv(result["git_safety_rows"], design_gate.GIT_SAFETY_CSV, design_gate.GIT_SAFETY_COLUMNS)
    write_csv(result["training_blocker_rows"], design_gate.TRAINING_BLOCKERS_CSV, design_gate.TRAINING_BLOCKERS_COLUMNS)
    write_json(result["manifest"], design_gate.MANIFEST_JSON)
    write_summary(result["manifest"], result["preview_rows"], design_gate.SUMMARY_MD)

    manifest = result["manifest"]
    if manifest["all_checks_passed"]:
        print("covapie_candidate_allowlist_materialization_design_gate_v0_passed")
    else:
        print("covapie_candidate_allowlist_materialization_design_gate_v0_blocked")
    for key in [
        "allowlist_schema_field_count",
        "allowlist_candidate_preview_row_count",
        "allowlist_entry_id_preview_unique_count",
        "candidate_allowlist_materialized",
        "candidate_allowlist_materialized_current_step",
        "ready_for_covapie_candidate_allowlist_materialization_smoke",
        "ready_for_covapie_batch_scale_raw_read_design_gate",
        "ready_for_training",
        "ready_to_train_now",
        "recommended_next_step",
        "blocking_reasons",
    ]:
        print(f"{key}={manifest[key]}")
    return 0 if manifest["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
