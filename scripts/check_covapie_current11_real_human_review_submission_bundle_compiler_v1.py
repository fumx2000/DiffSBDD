#!/usr/bin/env python3
"""Check the Current11 real-human-review submission bundle compiler v1."""

from __future__ import annotations

import csv
import importlib.util
import inspect
import io
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Sequence

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
        "covapie_current11_workspace_preparer_for_compiler_checker",
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


def _completed_worklist(
    worklist: bytes,
    eligible: bytes,
) -> bytes:
    fields, rows = _csv_rows(worklist)
    _, option_rows = _csv_rows(eligible)
    first_option_by_sample: dict[str, dict[str, str]] = {}
    for option in option_rows:
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
                "submission_source_label": "compiler-checker",
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
    return _csv_bytes(fields, rows)


def _check(repo_root: Path) -> dict[str, object]:
    function = (
        compiler
        .compile_covapie_current11_real_human_review_submission_bundle_v1
    )
    if compiler.__all__ != (
        "compile_covapie_current11_real_human_review_submission_bundle_v1",
    ):
        raise ValueError("compiler __all__ contract mismatch")
    signature = inspect.signature(function)
    if tuple(signature.parameters) != (
        "review_worklist_csv",
        "eligible_candidate_options_csv",
        "package_index_csv",
        "package_candidate_options_csv",
        "review_record_templates_csv",
        "submission_batch_id",
    ) or any(
        parameter.kind is not inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    ):
        raise ValueError("compiler public signature mismatch")

    preparer = _load_preparer(repo_root)
    workspace = preparer.build_workspace_payloads(repo_root)
    worklist = _completed_worklist(
        workspace["review_worklist.csv"],
        workspace["eligible_candidate_options.csv"],
    )
    package_root = repo_root / preparer.PACKAGE_ROOT
    keyword_arguments = {
        "review_worklist_csv": worklist,
        "eligible_candidate_options_csv":
            workspace["eligible_candidate_options.csv"],
        "package_index_csv":
            (package_root / preparer.INDEX_FILE).read_bytes(),
        "package_candidate_options_csv":
            (package_root / preparer.OPTIONS_FILE).read_bytes(),
        "review_record_templates_csv":
            (package_root / preparer.TEMPLATES_FILE).read_bytes(),
        "submission_batch_id":
            "covapie_current11_submission_compiler_checker_batch_v1",
    }

    adapter_calls = 0
    ingestion_calls = 0
    original_adapter = (
        public_adapter
        .adapt_current11_warhead_boundary_review_submission_bundle_v1
    )
    original_ingestion = (
        ingestion_interface
        .evaluate_current11_warhead_boundary_review_ingestion_v1
    )

    def counted_adapter(*, source_payload: bytes):
        nonlocal adapter_calls
        adapter_calls += 1
        return original_adapter(source_payload=source_payload)

    def forbidden_ingestion(**_arguments):
        nonlocal ingestion_calls
        ingestion_calls += 1
        raise ValueError("compiler called forbidden ingestion interface")

    public_adapter.adapt_current11_warhead_boundary_review_submission_bundle_v1 = (
        counted_adapter
    )
    ingestion_interface.evaluate_current11_warhead_boundary_review_ingestion_v1 = (
        forbidden_ingestion
    )
    try:
        first = function(**keyword_arguments)
        if adapter_calls != 1:
            raise ValueError("public adapter was not called exactly once")
        second = function(**keyword_arguments)
        if adapter_calls != 2:
            raise ValueError(
                "public adapter was not called exactly once per compilation"
            )
    finally:
        public_adapter.adapt_current11_warhead_boundary_review_submission_bundle_v1 = (
            original_adapter
        )
        ingestion_interface.evaluate_current11_warhead_boundary_review_ingestion_v1 = (
            original_ingestion
        )
    if ingestion_calls:
        raise ValueError("ingestion interface was executed")
    if first != second:
        raise ValueError("compiler output is not byte deterministic")
    bundle = json.loads(first)
    items = bundle["submission_items"]
    decisions = Counter(
        item["review_record_payload"]["review_decision"] for item in items
    )
    if (
        len(items) != 11
        or decisions
        != {
            "select_admitted_candidate": 6,
            "quarantine": 5,
        }
        or any(
            item["review_record_payload"]["review_decision"] != "quarantine"
            for item in items[5:10]
        )
    ):
        raise ValueError("compiler checker decision/order contract mismatch")
    return {
        "compiler_checked": True,
        "adapter_passed": True,
        "item_count": 11,
        "selected_count": 6,
        "quarantine_count": 5,
        "deterministic": True,
        "ingestion_executed": False,
    }


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    try:
        result = _check(repo_root)
    except (OSError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not (
        result["compiler_checked"] is True
        and result["adapter_passed"] is True
        and result["deterministic"] is True
        and result["ingestion_executed"] is False
    ):
        print("error: checker readiness assertion failed", file=sys.stderr)
        return 1
    print("compiler_checked=true")
    print("adapter_passed=true")
    print("item_count=11")
    print("selected_count=6")
    print("quarantine_count=5")
    print("deterministic=true")
    print("ingestion_executed=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
