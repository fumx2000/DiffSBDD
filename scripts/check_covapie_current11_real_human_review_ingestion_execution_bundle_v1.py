#!/usr/bin/env python3
"""Check the Current11 real-human-review ingestion execution bundle v1."""

from __future__ import annotations

import csv
import importlib.util
import io
import json
import sys
from pathlib import Path
from typing import Sequence

from covalent_ext import (
    covapie_current11_real_human_review_ingestion_execution_bundle_v1
    as execution,
)
from covalent_ext import (
    covapie_current11_real_human_review_submission_bundle_compiler_v1
    as compiler,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1
    as ingestion_interface,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_submission_adapter_v1
    as public_adapter,
)


def _load_preparer(repo_root: Path):
    path = repo_root / (
        "scripts/"
        "prepare_covapie_current11_warhead_atom_set_and_attachment_boundary_"
        "human_review_workspace_v1.py"
    )
    specification = importlib.util.spec_from_file_location(
        "covapie_current11_workspace_preparer_for_execution_checker",
        path,
    )
    if specification is None or specification.loader is None:
        raise ValueError("workspace preparer import specification unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _csv_rows(payload: bytes) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with io.StringIO(payload.decode("utf-8"), newline="") as handle:
        reader = csv.DictReader(handle)
        return tuple(reader.fieldnames or ()), list(reader)


def _csv_bytes(
    fields: Sequence[str],
    rows: Sequence[dict[str, str]],
) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=fields,
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def _synthetic_completed_submission(repo_root: Path) -> bytes:
    preparer = _load_preparer(repo_root)
    workspace = preparer.build_workspace_payloads(repo_root)
    fields, rows = _csv_rows(workspace["review_worklist.csv"])
    _, options = _csv_rows(workspace["eligible_candidate_options.csv"])
    first_option_by_sample: dict[str, dict[str, str]] = {}
    for option in options:
        first_option_by_sample.setdefault(
            option["sample_index_row_id"],
            option,
        )
    for position, row in enumerate(rows):
        row.update(
            {
                "reviewer_id": "checker-human-reviewer",
                "review_rationale": f"Checker human rationale {position}.",
                "review_notes": f"Checker preserved note {position}.",
                "reviewer_provenance_attested": "true",
                "reviewer_provenance_attestor_id": "checker-human-attestor",
                "submission_source_label": "execution-bundle-checker",
                "review_completed": "true",
            }
        )
        if 5 <= position <= 9:
            row.update(
                {
                    "review_decision": "quarantine",
                    "selected_bridge_candidate_index_0based": "",
                    "selected_bridge_candidate_record_sha256": "",
                    "reviewed_warhead_atom_ids_json": "[]",
                    "reviewed_warhead_attachment_atom_id": "",
                    "reviewed_nonwarhead_boundary_atom_id": "",
                    "reviewed_attachment_boundary_bond_order": "",
                    "reviewed_boundary_bond_id": "",
                }
            )
            continue
        option = first_option_by_sample[row["sample_index_row_id"]]
        row.update(
            {
                "review_decision": "select_admitted_candidate",
                "selected_bridge_candidate_index_0based":
                    option["source_bridge_candidate_index_0based"],
                "selected_bridge_candidate_record_sha256":
                    option["source_bridge_candidate_record_sha256"],
                "reviewed_warhead_atom_ids_json":
                    option["warhead_side_atom_ids"],
                "reviewed_warhead_attachment_atom_id":
                    option["warhead_attachment_atom_id"],
                "reviewed_nonwarhead_boundary_atom_id":
                    option["nonwarhead_boundary_atom_id"],
                "reviewed_attachment_boundary_bond_order":
                    option["boundary_bond_order"],
                "reviewed_boundary_bond_id": option["boundary_bond_id"],
            }
        )
    package_root = repo_root / preparer.PACKAGE_ROOT
    return compiler.compile_covapie_current11_real_human_review_submission_bundle_v1(
        review_worklist_csv=_csv_bytes(fields, rows),
        eligible_candidate_options_csv=
            workspace["eligible_candidate_options.csv"],
        package_index_csv=(package_root / preparer.INDEX_FILE).read_bytes(),
        package_candidate_options_csv=
            (package_root / preparer.OPTIONS_FILE).read_bytes(),
        review_record_templates_csv=
            (package_root / preparer.TEMPLATES_FILE).read_bytes(),
        submission_batch_id=
            "covapie_current11_execution_bundle_checker_batch_v1",
    )


def _check(repo_root: Path) -> dict[str, object]:
    submission = _synthetic_completed_submission(repo_root)
    adapter_calls = 0
    context_calls = 0
    evaluator_calls = 0
    observed_existing: list[object] = []
    observed_submissions: list[object] = []
    original_adapter = (
        public_adapter
        .adapt_current11_warhead_boundary_review_submission_bundle_v1
    )
    original_context = (
        ingestion_interface
        .build_current11_warhead_boundary_review_ingestion_authority_context_v1
    )
    original_evaluator = (
        ingestion_interface
        .evaluate_current11_warhead_boundary_review_ingestion_v1
    )

    def counted_adapter(*, source_payload: bytes):
        nonlocal adapter_calls
        adapter_calls += 1
        response = original_adapter(source_payload=source_payload)
        observed_submissions.append(response["adapted_submissions"])
        return response

    def counted_context(root: Path):
        nonlocal context_calls
        context_calls += 1
        return original_context(root)

    def counted_evaluator(**arguments):
        nonlocal evaluator_calls
        evaluator_calls += 1
        observed_existing.append(arguments["existing_authorities"])
        return original_evaluator(**arguments)

    public_adapter.adapt_current11_warhead_boundary_review_submission_bundle_v1 = (
        counted_adapter
    )
    ingestion_interface.build_current11_warhead_boundary_review_ingestion_authority_context_v1 = (
        counted_context
    )
    ingestion_interface.evaluate_current11_warhead_boundary_review_ingestion_v1 = (
        counted_evaluator
    )
    try:
        first = (
            execution
            .build_covapie_current11_real_human_review_ingestion_execution_bundle_v1(
                source_submission_bundle=submission,
                repo_root=repo_root,
            )
        )
        second = (
            execution
            .build_covapie_current11_real_human_review_ingestion_execution_bundle_v1(
                source_submission_bundle=submission,
                repo_root=repo_root,
            )
        )
    finally:
        public_adapter.adapt_current11_warhead_boundary_review_submission_bundle_v1 = (
            original_adapter
        )
        ingestion_interface.build_current11_warhead_boundary_review_ingestion_authority_context_v1 = (
            original_context
        )
        ingestion_interface.evaluate_current11_warhead_boundary_review_ingestion_v1 = (
            original_evaluator
        )
    if (
        adapter_calls != 2
        or context_calls != 2
        or evaluator_calls != 2
        or observed_existing != [(), ()]
        or len(observed_submissions) != 2
        or observed_submissions[0] != observed_submissions[1]
        or first != second
    ):
        raise ValueError("public call-count or deterministic contract failed")
    bundle = json.loads(first)
    authorities = bundle["new_authority_records"]
    active = sum(
        authority["authority_status"] == "active"
        for authority in authorities
    )
    quarantined = sum(
        authority["authority_status"] == "quarantined"
        for authority in authorities
    )
    active_samples = {
        f"CYS_SG_SAMPLE_INDEX_{number:06d}"
        for number in (*range(1, 6), 11)
    }
    direct_fields = (
        "sample_index_row_id",
        "review_decision",
        "reviewed_warhead_atom_ids",
        "reviewed_warhead_attachment_atom_id",
        "reviewed_nonwarhead_boundary_atom_id",
        "reviewed_attachment_boundary_bond_order",
        "reviewed_boundary_bond_id",
        "reviewer_id",
    )
    linkage_valid = True
    decision_profile_valid = True
    for authority, submission_pair in zip(
        authorities,
        observed_submissions[0],
    ):
        review, envelope = submission_pair
        sample = authority["sample_index_row_id"]
        expected_decision = (
            "select_admitted_candidate"
            if sample in active_samples
            else "quarantine"
        )
        decision_profile_valid = decision_profile_valid and (
            authority["review_decision"] == expected_decision
            and review["review_decision"] == expected_decision
        )
        linkage_valid = linkage_valid and (
            all(authority[field] == review[field] for field in direct_fields)
            and authority["source_review_record_sha256"]
            == review["review_record_sha256"]
            and authority["source_ingestion_envelope_sha256"]
            == envelope["ingestion_envelope_sha256"]
        )
        if expected_decision == "quarantine":
            linkage_valid = linkage_valid and (
                authority["reviewed_warhead_atom_ids"] == []
                and review["reviewed_warhead_atom_ids"] == []
                and all(
                    authority[field] == review[field] == ""
                    for field in (
                        "reviewed_warhead_attachment_atom_id",
                        "reviewed_nonwarhead_boundary_atom_id",
                        "reviewed_attachment_boundary_bond_order",
                        "reviewed_boundary_bond_id",
                    )
                )
            )
    if (
        bundle["batch_passed"] is not True
        or len(bundle["ingestion_result_records"]) != 11
        or len(authorities) != 11
        or active != 6
        or quarantined != 5
        or decision_profile_valid is not True
        or linkage_valid is not True
    ):
        raise ValueError("execution bundle semantic contract failed")
    return {
        "execution_bundle_checked": True,
        "adapter_calls_per_build": 1,
        "context_calls_per_build": 1,
        "evaluator_calls_per_build": 1,
        "existing_authorities_empty": True,
        "result_count": 11,
        "authority_count": 11,
        "active_authority_count": 6,
        "quarantined_authority_count": 5,
        "decision_profile_valid": True,
        "authority_review_linkage_valid": True,
        "batch_passed": True,
        "deterministic": True,
        "files_written": False,
    }


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    try:
        result = _check(repo_root)
    except (OSError, TypeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    if not all((
        result["execution_bundle_checked"] is True,
        result["existing_authorities_empty"] is True,
        result["decision_profile_valid"] is True,
        result["authority_review_linkage_valid"] is True,
        result["batch_passed"] is True,
        result["deterministic"] is True,
        result["files_written"] is False,
    )):
        print("error: checker readiness assertion failed", file=sys.stderr)
        return 1
    for field in (
        "execution_bundle_checked",
        "adapter_calls_per_build",
        "context_calls_per_build",
        "evaluator_calls_per_build",
        "existing_authorities_empty",
        "result_count",
        "authority_count",
        "active_authority_count",
        "quarantined_authority_count",
        "decision_profile_valid",
        "authority_review_linkage_valid",
        "batch_passed",
        "deterministic",
        "files_written",
    ):
        value = result[field]
        rendered = str(value).lower() if type(value) is bool else str(value)
        print(f"{field}={rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
