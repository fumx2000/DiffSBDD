#!/usr/bin/env python3
"""Check the pure in-memory Current11 Exact5 multi-boundary sidecar."""

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
    covapie_current11_real_human_review_ingestion_execution_bundle_v1
    as execution_builder,
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


_EXPECTED = (
    (
        "CYS_SG_SAMPLE_INDEX_000006",
        ["C19", "C21", "C22", "C42", "N18", "N41", "O23"],
        ["C16|N18|single", "C39|N41|single"],
    ),
    (
        "CYS_SG_SAMPLE_INDEX_000007",
        ["C15", "C16", "C17", "C18", "N14", "N23", "O42"],
        ["C13|N14|single", "C24|N23|single"],
    ),
    (
        "CYS_SG_SAMPLE_INDEX_000008",
        ["C21", "N18", "N19", "N40", "N41", "O22"],
        ["C16|N18|single", "C38|N40|single"],
    ),
    (
        "CYS_SG_SAMPLE_INDEX_000009",
        [
            "C17", "C20", "C21", "C42", "CH'", "N19", "NJ'", "NK'",
            "O22", "OI'", "S18",
        ],
        ["C11|C17|single", "CB'|CH'|single"],
    ),
    (
        "CYS_SG_SAMPLE_INDEX_000010",
        [
            "C17", "C21", "CH'", "N19", "N20", "NJ'", "NK'", "O18",
            "O22", "OI'",
        ],
        ["C11|C17|single", "CB'|CH'|single"],
    ),
)


def _load_preparer(repo_root: Path):
    path = (
        repo_root
        / "scripts/"
        "prepare_covapie_current11_warhead_atom_set_and_attachment_boundary_"
        "human_review_workspace_v1.py"
    )
    specification = importlib.util.spec_from_file_location(
        "sidecar_checker_predecessor_preparer", path,
    )
    if specification is None or specification.loader is None:
        raise AssertionError("predecessor preparer import unavailable")
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


def _synthetic_sources(repo_root: Path) -> tuple[bytes, bytes]:
    preparer = _load_preparer(repo_root)
    workspace = preparer.build_workspace_payloads(repo_root)
    fields, worklist = _csv_rows(workspace["review_worklist.csv"])
    _, options = _csv_rows(workspace["eligible_candidate_options.csv"])
    first_option: dict[str, dict[str, str]] = {}
    for option in options:
        first_option.setdefault(option["sample_index_row_id"], option)
    expected_by_sample = {
        sample: (atoms, boundaries)
        for sample, atoms, boundaries in _EXPECTED
    }
    for position, row in enumerate(worklist):
        sample = row["sample_index_row_id"]
        notes = f"Checker preserved human review note {position}."
        if sample in expected_by_sample:
            atoms, boundaries = expected_by_sample[sample]
            notes = (
                "Exact audited proposed atom IDs "
                + json.dumps(atoms, separators=(",", ":"))
                + "; exact canonical boundary IDs "
                + ", ".join(boundaries)
                + "."
            )
        row.update({
            "reviewer_id": "checker-human-reviewer",
            "review_rationale": f"Checker human rationale {position}.",
            "review_notes": notes,
            "reviewer_provenance_attested": "true",
            "reviewer_provenance_attestor_id": "checker-human-attestor",
            "submission_source_label": "sidecar-checker-synthetic",
            "review_completed": "true",
        })
        if 5 <= position <= 9:
            row.update({
                "review_decision": "quarantine",
                "selected_bridge_candidate_index_0based": "",
                "selected_bridge_candidate_record_sha256": "",
                "reviewed_warhead_atom_ids_json": "[]",
                "reviewed_warhead_attachment_atom_id": "",
                "reviewed_nonwarhead_boundary_atom_id": "",
                "reviewed_attachment_boundary_bond_order": "",
                "reviewed_boundary_bond_id": "",
            })
        else:
            option = first_option[sample]
            row.update({
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
            })
    package_root = repo_root / preparer.PACKAGE_ROOT
    submission = compiler.compile_covapie_current11_real_human_review_submission_bundle_v1(
        review_worklist_csv=_csv_bytes(fields, worklist),
        eligible_candidate_options_csv=
            workspace["eligible_candidate_options.csv"],
        package_index_csv=
            (package_root / preparer.INDEX_FILE).read_bytes(),
        package_candidate_options_csv=
            (package_root / preparer.OPTIONS_FILE).read_bytes(),
        review_record_templates_csv=
            (package_root / preparer.TEMPLATES_FILE).read_bytes(),
        submission_batch_id="covapie_current11_sidecar_checker_batch_v1",
    )
    execution = execution_builder.build_covapie_current11_real_human_review_ingestion_execution_bundle_v1(
        source_submission_bundle=submission,
        repo_root=repo_root,
    )
    return submission, execution


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    submission, execution = _synthetic_sources(repo_root)
    submission_snapshot = bytes(submission)
    execution_snapshot = bytes(execution)
    calls = {"adapter": 0, "context": 0, "evaluator": 0}
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
    original_writes = {
        name: getattr(Path, name)
        for name in ("write_bytes", "write_text", "touch", "mkdir")
    }

    def counted_adapter(*, source_payload: bytes):
        calls["adapter"] += 1
        return original_adapter(source_payload=source_payload)

    def counted_context(root: Path):
        calls["context"] += 1
        return original_context(root)

    def forbidden_evaluator(*_arguments, **_keyword_arguments):
        calls["evaluator"] += 1
        raise AssertionError("ingestion evaluator was called")

    def forbidden_write(*_arguments, **_keyword_arguments):
        raise AssertionError("sidecar builder attempted a file write")

    try:
        public_adapter.adapt_current11_warhead_boundary_review_submission_bundle_v1 = (
            counted_adapter
        )
        ingestion_interface.build_current11_warhead_boundary_review_ingestion_authority_context_v1 = (
            counted_context
        )
        ingestion_interface.evaluate_current11_warhead_boundary_review_ingestion_v1 = (
            forbidden_evaluator
        )
        for name in original_writes:
            setattr(Path, name, forbidden_write)
        first = sidecar.build_covapie_current11_multi_boundary_human_review_sidecar_v1(
            source_submission_bundle=submission,
            source_ingestion_execution_bundle=execution,
            repo_root=repo_root,
        )
        second = sidecar.build_covapie_current11_multi_boundary_human_review_sidecar_v1(
            source_submission_bundle=submission,
            source_ingestion_execution_bundle=execution,
            repo_root=repo_root,
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
        for name, method in original_writes.items():
            setattr(Path, name, method)
    _, evidence = _csv_rows(first["verified_multi_boundary_evidence.csv"])
    _, worklist = _csv_rows(first["multi_boundary_review_worklist.csv"])
    if calls != {"adapter": 2, "context": 2, "evaluator": 0}:
        raise AssertionError(f"public call counts invalid: {calls}")
    if len(evidence) != 5 or len(worklist) != 5:
        raise AssertionError("Exact5 output count invalid")
    for position, (sample, atoms, boundary_ids) in enumerate(_EXPECTED):
        evidence_row = evidence[position]
        observed_boundaries = json.loads(
            evidence_row["proposed_boundary_records_json"]
        )
        if (
            evidence_row["sample_index_row_id"] != sample
            or json.loads(
                evidence_row["proposed_warhead_atom_ids_json"]
            ) != atoms
            or [
                record["boundary_bond_id"]
                for record in observed_boundaries
            ] != boundary_ids
            or evidence_row["exact_two_boundaries_verified"] != "true"
        ):
            raise AssertionError(f"proposal mismatch: {sample}")
    exact_two = sum(
        row["exact_two_boundaries_verified"] == "true"
        for row in evidence
    )
    pending = sum(
        row["review_decision"] == "not_reviewed"
        and row["review_completed"] == "false"
        for row in worklist
    )
    parsed_execution = json.loads(execution)
    quarantined = [
        record
        for record in parsed_execution["new_authority_records"]
        if record["sample_index_row_id"] in {
            sample for sample, _, _ in _EXPECTED
        }
    ]
    if (
        len(quarantined) != 5
        or any(
            record["authority_status"] != "quarantined"
            or record["sample_quarantined"] is not True
            for record in quarantined
        )
        or submission != submission_snapshot
        or execution != execution_snapshot
    ):
        raise AssertionError("V1 source authority or input changed")
    summary = {
        "adapter_calls_per_build": calls["adapter"] // 2,
        "authority_context_calls_per_build": calls["context"] // 2,
        "ingestion_evaluator_calls_per_build": calls["evaluator"] // 2,
        "evidence_count": len(evidence),
        "worklist_count": len(worklist),
        "exact_two_boundary_verified_count": exact_two,
        "pending_human_review_count": pending,
        "v1_authority_modified": False,
        "multi_boundary_authority_created": False,
        "deterministic": first == second,
        "files_written": False,
        "evidence_sha256": hashlib.sha256(
            first["verified_multi_boundary_evidence.csv"]
        ).hexdigest(),
        "worklist_sha256": hashlib.sha256(
            first["multi_boundary_review_worklist.csv"]
        ).hexdigest(),
        "readme_sha256": hashlib.sha256(first["README.md"]).hexdigest(),
    }
    expected_summary = {
        "adapter_calls_per_build": 1,
        "authority_context_calls_per_build": 1,
        "ingestion_evaluator_calls_per_build": 0,
        "evidence_count": 5,
        "worklist_count": 5,
        "exact_two_boundary_verified_count": 5,
        "pending_human_review_count": 5,
        "v1_authority_modified": False,
        "multi_boundary_authority_created": False,
        "deterministic": True,
        "files_written": False,
    }
    if any(summary[key] != value for key, value in expected_summary.items()):
        raise AssertionError("checker summary invariant invalid")
    for key, value in summary.items():
        if type(value) is bool:
            value = "true" if value else "false"
        print(f"{key}={value}")
    for sample, atoms, boundary_ids in _EXPECTED:
        print(
            f"proposal_{sample}="
            + json.dumps(
                {"atom_ids": atoms, "boundary_ids": boundary_ids},
                separators=(",", ":"),
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
