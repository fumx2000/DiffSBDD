#!/usr/bin/env python3
"""Run the CovaPIE Cys-SG V1 review or approved-materialization pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from covalent_ext.covapie_cys_sg_dataset_expansion_pipeline_v1 import (  # noqa: E402
    MATERIALIZE_APPROVED,
    REVIEW_ONLY,
    atomic_write_review_only_report_v1,
    load_candidate_batch_v1,
    load_cumulative_expansion_leakage_registry_v1,
    load_current_non_exact16_candidates_v1,
    load_reusable_authority_registry_v1,
    pipeline_output_sha256_v1,
    run_covapie_cys_sg_dataset_expansion_pipeline_v1,
)


def _approval_records(path: Path | None) -> dict[str, dict[str, object]]:
    if path is None:
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    records = value if type(value) is list else value.get("approval_records") if type(value) is dict else None
    if type(records) is not list:
        raise ValueError("APPROVAL_RECORDS_JSON_MUST_BE_LIST")
    result: dict[str, dict[str, object]] = {}
    for record in records:
        if type(record) is not dict or type(record.get("candidate_identity")) is not str:
            raise ValueError("APPROVAL_RECORD_INVALID")
        if record.get("review_status") in (None, "", "NOT_REVIEWED"):
            continue
        identity = record["candidate_identity"]
        if identity in result:
            raise ValueError("DUPLICATE_APPROVAL_RECORD_IDENTITY")
        result[identity] = record
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--approval-records-json", type=Path)
    parser.add_argument("--candidate-batch-json", type=Path)
    parser.add_argument("--reusable-authority-registry-json", type=Path)
    parser.add_argument("--cumulative-leakage-registry-json", type=Path)
    parser.add_argument(
        "--mode", choices=(REVIEW_ONLY, MATERIALIZE_APPROVED),
        default=REVIEW_ONLY,
    )
    parser.add_argument("--materialization-output-root", type=Path)
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Optional non-authoritative review-only report path.",
    )
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    approvals = _approval_records(args.approval_records_json)
    candidates = (
        load_candidate_batch_v1(args.candidate_batch_json.resolve())
        if args.candidate_batch_json is not None
        else load_current_non_exact16_candidates_v1(repo_root)
    )
    authorities = (
        load_reusable_authority_registry_v1(
            args.reusable_authority_registry_json.resolve()
        )
        if args.reusable_authority_registry_json is not None else ()
    )
    cumulative_registry_path = (
        args.cumulative_leakage_registry_json.resolve()
        if args.cumulative_leakage_registry_json is not None else None
    )
    cumulative_registry = (
        load_cumulative_expansion_leakage_registry_v1(
            cumulative_registry_path, repo_root=repo_root,
        )
        if cumulative_registry_path is not None else None
    )
    materialization_root = args.materialization_output_root
    if materialization_root is not None and not materialization_root.is_absolute():
        materialization_root = (repo_root / materialization_root).resolve()
    run = run_covapie_cys_sg_dataset_expansion_pipeline_v1(
        candidates,
        reusable_authorities=authorities,
        approval_records=approvals,
        execution_mode=args.mode,
        output_root=materialization_root,
        cumulative_leakage_registry=cumulative_registry,
        cumulative_leakage_registry_source_path=cumulative_registry_path,
    )
    if args.output_json is not None:
        if args.mode != REVIEW_ONLY:
            raise ValueError("OUTPUT_JSON_IS_REVIEW_ONLY;USE_MATERIALIZATION_OUTPUT_ROOT")
        output = args.output_json
        if not output.is_absolute():
            output = repo_root / output
        atomic_write_review_only_report_v1(output, run)
    print(json.dumps({
        "aggregate": dict(run.aggregate),
        "dry_run": run.dry_run,
        "execution_mode": run.execution_mode,
        "materialization_performed_count": sum(
            item.materialization_performed for item in run.outcomes
        ),
        "output_sha256": pipeline_output_sha256_v1(run),
        "pipeline_version": run.pipeline_version,
        "review_queue_identities": list(run.review_queue_identities),
        "tensorization_performed_count": sum(
            item.tensorization_performed for item in run.outcomes
        ),
        "successor_policy_id": run.successor_policy_id,
    }, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
