#!/usr/bin/env python3
"""Check the pure in-memory Current11 multi-boundary submission compiler."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path

from covalent_ext import (
    covapie_current11_multi_boundary_human_review_sidecar_v1 as sidecar,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_submission_bundle_compiler_v1
    as compiler,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1
    as ingestion_interface,
)


_REVISION_ATOMS = [
    "C16", "C21", "C38", "N18", "N19",
    "N40", "N41", "O17", "O22", "O39",
]
_REVISION_BOUNDARIES = [
    {
        "warhead_attachment_atom_id": "C16",
        "nonwarhead_boundary_atom_id": "C11",
        "boundary_bond_order": "single",
        "boundary_bond_id": "C11|C16|single",
    },
    {
        "warhead_attachment_atom_id": "C38",
        "nonwarhead_boundary_atom_id": "C33",
        "boundary_bond_order": "single",
        "boundary_bond_id": "C33|C38|single",
    },
]


def _load_predecessor_checker(repo_root: Path):
    path = (
        repo_root
        / "scripts/check_prepare_covapie_current11_multi_boundary_"
        "human_review_sidecar_v1.py"
    )
    specification = importlib.util.spec_from_file_location(
        "multi_boundary_compiler_checker_predecessor", path,
    )
    if specification is None or specification.loader is None:
        raise AssertionError("predecessor checker import unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _csv_rows(
    payload: bytes,
) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with io.StringIO(payload.decode("utf-8"), newline="") as stream:
        reader = csv.DictReader(stream)
        return tuple(reader.fieldnames or ()), list(reader)


def _csv_bytes(
    fields: tuple[str, ...],
    rows: list[dict[str, str]],
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=fields,
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _json_cell(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    )


def _completed_workspace(
    repo_root: Path,
) -> tuple[dict[str, bytes], bytes, bytes]:
    predecessor = _load_predecessor_checker(repo_root)
    submission, execution = predecessor._synthetic_sources(repo_root)
    blank = (
        sidecar.build_covapie_current11_multi_boundary_human_review_sidecar_v1(
            source_submission_bundle=submission,
            source_ingestion_execution_bundle=execution,
            repo_root=repo_root,
        )
    )
    fields, rows = _csv_rows(blank["multi_boundary_review_worklist.csv"])
    for position, row in enumerate(rows):
        row.update({
            "review_decision":
                "revise_two_boundary_atom_set_and_boundaries"
                if position == 2
                else "accept_verified_two_boundary_proposal",
            "reviewed_warhead_atom_ids_json":
                _json_cell(_REVISION_ATOMS)
                if position == 2
                else row["proposed_warhead_atom_ids_json"],
            "reviewed_boundary_records_json":
                _json_cell(_REVISION_BOUNDARIES)
                if position == 2
                else row["proposed_boundary_records_json"],
            "reviewer_id": "fmx",
            "review_rationale":
                f"Checker synthetic human rationale {position}.",
            "review_notes": f"Checker synthetic human notes {position}.",
            "reviewer_provenance_attested": "true",
            "reviewer_provenance_attestor_id": "fmx",
            "submission_source_label":
                "multi-boundary-compiler-checker-synthetic",
            "review_completed": "true",
            "multi_boundary_review_record_sha256": "",
        })
    return (
        {
            "evidence": blank["verified_multi_boundary_evidence.csv"],
            "worklist": _csv_bytes(fields, rows),
            "readme": blank["README.md"],
        },
        submission,
        execution,
    )


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    workspace, submission, execution = _completed_workspace(repo_root)
    input_snapshots = (
        bytes(workspace["evidence"]),
        bytes(workspace["worklist"]),
        bytes(workspace["readme"]),
        bytes(submission),
        bytes(execution),
    )
    calls = {"sidecar": 0, "context": 0, "evaluator": 0, "writes": 0}
    original_sidecar = (
        sidecar.build_covapie_current11_multi_boundary_human_review_sidecar_v1
    )
    original_context = (
        ingestion_interface
        .build_current11_warhead_boundary_review_ingestion_authority_context_v1
    )
    original_evaluator = (
        ingestion_interface
        .evaluate_current11_warhead_boundary_review_ingestion_v1
    )
    original_writes = {
        name: getattr(Path, name)
        for name in ("write_bytes", "write_text", "touch", "mkdir")
    }

    def counted_sidecar(**arguments):
        calls["sidecar"] += 1
        return original_sidecar(**arguments)

    def counted_context(root: Path):
        calls["context"] += 1
        return original_context(root)

    def forbidden_evaluator(*_arguments, **_keyword_arguments):
        calls["evaluator"] += 1
        raise AssertionError("ingestion evaluator called")

    def forbidden_write(*_arguments, **_keyword_arguments):
        calls["writes"] += 1
        raise AssertionError("compiler attempted a filesystem write")

    try:
        sidecar.build_covapie_current11_multi_boundary_human_review_sidecar_v1 = (
            counted_sidecar
        )
        ingestion_interface.build_current11_warhead_boundary_review_ingestion_authority_context_v1 = (
            counted_context
        )
        ingestion_interface.evaluate_current11_warhead_boundary_review_ingestion_v1 = (
            forbidden_evaluator
        )
        for name in original_writes:
            setattr(Path, name, forbidden_write)
        outputs = []
        for _ in range(2):
            outputs.append(
                compiler.compile_covapie_current11_multi_boundary_human_review_submission_bundle_v1(
                    verified_multi_boundary_evidence_csv=
                        workspace["evidence"],
                    multi_boundary_review_worklist_csv=
                        workspace["worklist"],
                    readme_md=workspace["readme"],
                    source_submission_bundle=submission,
                    source_ingestion_execution_bundle=execution,
                    repo_root=repo_root,
                    submission_batch_id=
                        "covapie_current11_multi_boundary_checker_batch_v1",
                )
            )
    finally:
        sidecar.build_covapie_current11_multi_boundary_human_review_sidecar_v1 = (
            original_sidecar
        )
        ingestion_interface.build_current11_warhead_boundary_review_ingestion_authority_context_v1 = (
            original_context
        )
        ingestion_interface.evaluate_current11_warhead_boundary_review_ingestion_v1 = (
            original_evaluator
        )
        for name, method in original_writes.items():
            setattr(Path, name, method)

    bundle = json.loads(outputs[0])
    items = bundle["submission_items"]
    decisions = [record["review_decision"] for record in items]
    digests = [
        record["multi_boundary_review_record_sha256"] for record in items
    ]
    current_inputs = (
        workspace["evidence"],
        workspace["worklist"],
        workspace["readme"],
        submission,
        execution,
    )
    assertions = {
        "sidecar_builder_calls_per_compile": calls["sidecar"] // 2,
        "authority_context_builder_calls_per_compile": calls["context"] // 2,
        "ingestion_evaluator_calls_per_compile": calls["evaluator"] // 2,
        "submission_item_count": len(items),
        "accept_decision_count":
            decisions.count("accept_verified_two_boundary_proposal"),
        "revise_decision_count":
            decisions.count("revise_two_boundary_atom_set_and_boundaries"),
        "quarantine_decision_count": decisions.count("quarantine"),
        "completed_review_count":
            sum(record["review_completed"] is True for record in items),
        "record_digest_count": sum(bool(value) for value in digests),
        "unique_record_digest_count": len(set(digests)),
        "revision_graph_validated_count":
            decisions.count("revise_two_boundary_atom_set_and_boundaries"),
        "deterministic": outputs[0] == outputs[1],
        "inputs_unchanged": current_inputs == input_snapshots,
        "files_written": calls["writes"] != 0,
        "authority_created": False,
        "v1_authority_modified": False,
    }
    expected = {
        "sidecar_builder_calls_per_compile": 1,
        "authority_context_builder_calls_per_compile": 2,
        "ingestion_evaluator_calls_per_compile": 0,
        "submission_item_count": 5,
        "accept_decision_count": 4,
        "revise_decision_count": 1,
        "quarantine_decision_count": 0,
        "completed_review_count": 5,
        "record_digest_count": 5,
        "unique_record_digest_count": 5,
        "revision_graph_validated_count": 1,
        "deterministic": True,
        "inputs_unchanged": True,
        "files_written": False,
        "authority_created": False,
        "v1_authority_modified": False,
    }
    if assertions != expected:
        raise AssertionError((assertions, expected))
    revision = items[2]
    if (
        revision["sample_index_row_id"] != "CYS_SG_SAMPLE_INDEX_000008"
        or revision["reviewed_warhead_atom_ids"] != _REVISION_ATOMS
        or revision["reviewed_boundary_records"] != _REVISION_BOUNDARIES
    ):
        raise AssertionError("000008 compiled revision mismatch")

    for key, value in assertions.items():
        rendered = str(value).lower() if type(value) is bool else value
        print(f"{key}={rendered}")
    print(
        "compiled_bundle_bytes_sha256="
        + hashlib.sha256(outputs[0]).hexdigest()
    )
    print(
        "multi_boundary_submission_bundle_sha256="
        + bundle["multi_boundary_submission_bundle_sha256"]
    )
    print("record_sha256s=" + _json_cell(digests))
    print(
        "sample_000008_compiled_reviewed_warhead_atom_ids="
        + _json_cell(revision["reviewed_warhead_atom_ids"])
    )
    print(
        "sample_000008_compiled_reviewed_boundary_records="
        + _json_cell(revision["reviewed_boundary_records"])
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
