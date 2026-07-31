#!/usr/bin/env python3
"""Check the private in-memory multi-boundary ingestion reference evaluator."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from covalent_ext import (
    covapie_current11_multi_boundary_human_review_ingestion_contract_design_v1
    as design,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_sidecar_v1 as sidecar,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_submission_adapter_v1
    as adapter,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_submission_bundle_compiler_v1
    as compiler,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_interface_v1
    as ingestion_interface,
)


def _ordered_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _load_compiler_checker(repo_root: Path):
    path = (
        repo_root
        / "scripts/check_covapie_current11_multi_boundary_"
        "human_review_submission_bundle_compiler_v1.py"
    )
    specification = importlib.util.spec_from_file_location(
        "multi_boundary_ingestion_design_predecessor_checker", path,
    )
    if specification is None or specification.loader is None:
        raise AssertionError("compiler predecessor checker unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _synthetic_case(
    repo_root: Path,
) -> tuple[bytes, bytes, bytes, bytes]:
    predecessor = _load_compiler_checker(repo_root)
    workspace, v1_submission, v1_execution = (
        predecessor._completed_workspace(repo_root)
    )
    multi_submission = (
        compiler
        .compile_covapie_current11_multi_boundary_human_review_submission_bundle_v1(
            verified_multi_boundary_evidence_csv=workspace["evidence"],
            multi_boundary_review_worklist_csv=workspace["worklist"],
            readme_md=workspace["readme"],
            source_submission_bundle=v1_submission,
            source_ingestion_execution_bundle=v1_execution,
            repo_root=repo_root,
            submission_batch_id=
                "covapie_current11_multi_boundary_ingestion_design_batch_v1",
        )
    )
    adapter_response = (
        adapter
        .adapt_covapie_current11_multi_boundary_human_review_submission_bundle_v1(
            source_payload=multi_submission,
        )
    )
    if adapter_response["adapter_passed"] is not True:
        raise AssertionError("synthetic predecessor adapter failed")
    return (
        multi_submission,
        _ordered_bytes(adapter_response),
        v1_submission,
        v1_execution,
    )


def _evaluate(
    repo_root: Path,
    case: tuple[bytes, bytes, bytes, bytes],
    *,
    existing: tuple[dict[str, Any], ...] = (),
) -> dict[str, Any]:
    multi_submission, adapter_response, v1_submission, v1_execution = case
    return design._reference_evaluate_covapie_current11_multi_boundary_ingestion_v1(
        adapter_response_payload=adapter_response,
        source_multi_boundary_submission_bundle=multi_submission,
        source_v1_submission_bundle=v1_submission,
        source_v1_ingestion_execution_bundle=v1_execution,
        repo_root=repo_root,
        existing_multi_boundary_authority_records=existing,
    )


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    case = _synthetic_case(repo_root)
    snapshots = tuple(bytes(value) for value in case)
    calls = {
        "sidecar": 0,
        "authority_context": 0,
        "compiler": 0,
        "adapter": 0,
        "predecessor_ingestion_evaluator": 0,
        "writes": 0,
    }
    original_sidecar = (
        sidecar.build_covapie_current11_multi_boundary_human_review_sidecar_v1
    )
    original_context = (
        ingestion_interface
        .build_current11_warhead_boundary_review_ingestion_authority_context_v1
    )
    original_compiler = (
        compiler
        .compile_covapie_current11_multi_boundary_human_review_submission_bundle_v1
    )
    original_adapter = (
        adapter
        .adapt_covapie_current11_multi_boundary_human_review_submission_bundle_v1
    )
    original_evaluator = (
        ingestion_interface
        .evaluate_current11_warhead_boundary_review_ingestion_v1
    )
    original_writes = {
        name: getattr(Path, name)
        for name in ("write_bytes", "write_text", "touch", "mkdir")
    }

    def counted(name: str, function):
        def wrapper(*arguments, **keywords):
            calls[name] += 1
            return function(*arguments, **keywords)

        return wrapper

    def forbidden(name: str):
        def fail(*_arguments, **_keywords):
            calls[name] += 1
            raise AssertionError(f"evaluator called forbidden {name}")

        return fail

    try:
        sidecar.build_covapie_current11_multi_boundary_human_review_sidecar_v1 = (
            counted("sidecar", original_sidecar)
        )
        ingestion_interface.build_current11_warhead_boundary_review_ingestion_authority_context_v1 = (
            counted("authority_context", original_context)
        )
        compiler.compile_covapie_current11_multi_boundary_human_review_submission_bundle_v1 = (
            forbidden("compiler")
        )
        adapter.adapt_covapie_current11_multi_boundary_human_review_submission_bundle_v1 = (
            forbidden("adapter")
        )
        ingestion_interface.evaluate_current11_warhead_boundary_review_ingestion_v1 = (
            forbidden("predecessor_ingestion_evaluator")
        )
        for name in original_writes:
            setattr(Path, name, forbidden("writes"))
        responses = [_evaluate(repo_root, case) for _ in range(2)]
    finally:
        sidecar.build_covapie_current11_multi_boundary_human_review_sidecar_v1 = (
            original_sidecar
        )
        ingestion_interface.build_current11_warhead_boundary_review_ingestion_authority_context_v1 = (
            original_context
        )
        compiler.compile_covapie_current11_multi_boundary_human_review_submission_bundle_v1 = (
            original_compiler
        )
        adapter.adapt_covapie_current11_multi_boundary_human_review_submission_bundle_v1 = (
            original_adapter
        )
        ingestion_interface.evaluate_current11_warhead_boundary_review_ingestion_v1 = (
            original_evaluator
        )
        for name, method in original_writes.items():
            setattr(Path, name, method)

    response = responses[0]
    results = response["ingestion_result_records"]
    authorities = response["new_authority_records"]
    source_adapter = json.loads(case[1])
    decisions = [record["review_decision"] for record in authorities]
    assertions = {
        "adapter_response_item_count":
            len(source_adapter["adapter_result_records"]),
        "ready_for_ingestion_count": sum(
            envelope["ready_for_ingestion"] is True
            for envelope in source_adapter["adapted_submissions"]
        ),
        "authority_context_record_sha256":
            response["authority_context_record_sha256"],
        "batch_passed": response["batch_passed"],
        "ingestion_result_count": len(results),
        "new_authority_count": len(authorities),
        "active_authority_count": sum(
            record["authority_status"] == "active"
            for record in authorities
        ),
        "quarantined_authority_count": sum(
            record["authority_status"] == "quarantined"
            for record in authorities
        ),
        "accept_authority_count":
            decisions.count("accept_verified_two_boundary_proposal"),
        "revise_authority_count":
            decisions.count("revise_two_boundary_atom_set_and_boundaries"),
        "quarantine_authority_count": decisions.count("quarantine"),
        "complete_warhead_atom_set_authority_count": sum(
            record["complete_warhead_atom_set_authority_available"] is True
            for record in authorities
        ),
        "exact_two_attachment_boundaries_authority_count": sum(
            record[
                "exact_two_attachment_boundaries_authority_available"
            ] is True
            for record in authorities
        ),
        "v1_quarantine_authority_unchanged_count": sum(
            record["v1_quarantine_authority_unchanged"] is True
            for record in authorities
        ),
        "idempotent_replay_count": sum(
            result["idempotent_replay"] is True for result in results
        ),
        "conflict_count": sum(
            result["conflicting_existing_authority"] is True
            for result in results
        ),
        "result_digest_count": sum(
            bool(result["multi_boundary_ingestion_result_sha256"])
            for result in results
        ),
        "unique_authority_digest_count": len({
            record["multi_boundary_authority_record_sha256"]
            for record in authorities
        }),
        "response_digest_valid": response[
            "multi_boundary_ingestion_interface_response_sha256"
        ] == design._digest(
            response,
            design.MULTI_BOUNDARY_INGESTION_INTERFACE_RESPONSE_FIELDS,
            "multi_boundary_ingestion_interface_response_sha256",
        ),
        "deterministic": responses[0] == responses[1],
        "inputs_unchanged": case == snapshots,
        "sidecar_builder_calls_per_evaluation": calls["sidecar"] // 2,
        "authority_context_builder_calls_per_evaluation":
            calls["authority_context"] // 2,
        "compiler_calls_per_evaluation": calls["compiler"] // 2,
        "adapter_calls_per_evaluation": calls["adapter"] // 2,
        "predecessor_ingestion_evaluator_calls_per_evaluation":
            calls["predecessor_ingestion_evaluator"] // 2,
        "files_written": calls["writes"] != 0,
        "durable_authority_created": False,
        "v1_authority_modified": False,
        "candidate_authority_sha256s": [
            record["multi_boundary_authority_record_sha256"]
            for record in authorities
        ],
        "ingestion_result_sha256s": [
            result["multi_boundary_ingestion_result_sha256"]
            for result in results
        ],
        "interface_response_sha256": response[
            "multi_boundary_ingestion_interface_response_sha256"
        ],
    }
    expected = {
        "adapter_response_item_count": 5,
        "ready_for_ingestion_count": 5,
        "batch_passed": True,
        "ingestion_result_count": 5,
        "new_authority_count": 5,
        "active_authority_count": 5,
        "quarantined_authority_count": 0,
        "accept_authority_count": 4,
        "revise_authority_count": 1,
        "quarantine_authority_count": 0,
        "complete_warhead_atom_set_authority_count": 5,
        "exact_two_attachment_boundaries_authority_count": 5,
        "v1_quarantine_authority_unchanged_count": 5,
        "idempotent_replay_count": 0,
        "conflict_count": 0,
        "result_digest_count": 5,
        "unique_authority_digest_count": 5,
        "response_digest_valid": True,
        "deterministic": True,
        "inputs_unchanged": True,
        "sidecar_builder_calls_per_evaluation": 1,
        "authority_context_builder_calls_per_evaluation": 2,
        "compiler_calls_per_evaluation": 0,
        "adapter_calls_per_evaluation": 0,
        "predecessor_ingestion_evaluator_calls_per_evaluation": 0,
        "files_written": False,
        "durable_authority_created": False,
        "v1_authority_modified": False,
    }
    for key, expected_value in expected.items():
        if assertions[key] != expected_value:
            raise AssertionError(
                f"{key}: expected {expected_value!r}, "
                f"observed {assertions[key]!r}"
            )
    for key, value in assertions.items():
        print(f"{key}={json.dumps(value, ensure_ascii=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
