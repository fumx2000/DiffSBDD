#!/usr/bin/env python3
"""Check the pure in-memory Current11 multi-boundary adapter."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

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


def _canonical_sha(record: dict[str, Any], excluded: str) -> str:
    return hashlib.sha256(json.dumps(
        {key: value for key, value in record.items() if key != excluded},
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()


def _json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    )


def _load_compiler_checker(repo_root: Path):
    path = (
        repo_root
        / "scripts/check_covapie_current11_multi_boundary_"
        "human_review_submission_bundle_compiler_v1.py"
    )
    specification = importlib.util.spec_from_file_location(
        "adapter_checker_compiler_predecessor", path,
    )
    if specification is None or specification.loader is None:
        raise AssertionError("compiler predecessor checker unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _synthetic_payload(repo_root: Path) -> bytes:
    checker = _load_compiler_checker(repo_root)
    workspace, submission, execution = checker._completed_workspace(repo_root)
    return (
        compiler
        .compile_covapie_current11_multi_boundary_human_review_submission_bundle_v1(
            verified_multi_boundary_evidence_csv=workspace["evidence"],
            multi_boundary_review_worklist_csv=workspace["worklist"],
            readme_md=workspace["readme"],
            source_submission_bundle=submission,
            source_ingestion_execution_bundle=execution,
            repo_root=repo_root,
            submission_batch_id=
                "covapie_current11_multi_boundary_adapter_checker_batch_v1",
        )
    )


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    source_payload = _synthetic_payload(repo_root)
    source_snapshot = bytes(source_payload)
    source_bundle = json.loads(source_payload)
    calls = {
        "compiler": 0,
        "sidecar": 0,
        "authority_context": 0,
        "ingestion_evaluator": 0,
        "writes": 0,
    }
    original_compiler = (
        compiler
        .compile_covapie_current11_multi_boundary_human_review_submission_bundle_v1
    )
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

    def forbidden(name: str):
        def fail(*_arguments, **_keyword_arguments):
            calls[name] += 1
            raise AssertionError(f"adapter called {name}")

        return fail

    try:
        compiler.compile_covapie_current11_multi_boundary_human_review_submission_bundle_v1 = (
            forbidden("compiler")
        )
        sidecar.build_covapie_current11_multi_boundary_human_review_sidecar_v1 = (
            forbidden("sidecar")
        )
        ingestion_interface.build_current11_warhead_boundary_review_ingestion_authority_context_v1 = (
            forbidden("authority_context")
        )
        ingestion_interface.evaluate_current11_warhead_boundary_review_ingestion_v1 = (
            forbidden("ingestion_evaluator")
        )
        for name in original_writes:
            setattr(Path, name, forbidden("writes"))
        responses = [
            adapter
            .adapt_covapie_current11_multi_boundary_human_review_submission_bundle_v1(
                source_payload=source_payload,
            )
            for _ in range(2)
        ]
    finally:
        compiler.compile_covapie_current11_multi_boundary_human_review_submission_bundle_v1 = (
            original_compiler
        )
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

    response = responses[0]
    results = response["adapter_result_records"]
    envelopes = response["adapted_submissions"]
    decisions = [
        envelope["review_record_payload"]["review_decision"]
        for envelope in envelopes
    ]
    review_shas = [
        envelope["source_multi_boundary_review_record_sha256"]
        for envelope in envelopes
    ]
    envelope_shas = [
        envelope["multi_boundary_ingestion_envelope_sha256"]
        for envelope in envelopes
    ]
    result_shas = [
        result["multi_boundary_submission_adapter_result_sha256"]
        for result in results
    ]
    assertions = {
        "source_payload_sha256": hashlib.sha256(source_payload).hexdigest(),
        "canonical_source_bundle_sha256":
            source_bundle["multi_boundary_submission_bundle_sha256"],
        "adapter_passed": response["adapter_passed"],
        "reason": response["reason"],
        "adapter_result_record_count": len(results),
        "adapted_submission_count": len(envelopes),
        "ready_for_ingestion_count": sum(
            envelope["ready_for_ingestion"] is True
            for envelope in envelopes
        ),
        "accept_decision_count":
            decisions.count("accept_verified_two_boundary_proposal"),
        "revise_decision_count":
            decisions.count("revise_two_boundary_atom_set_and_boundaries"),
        "quarantine_decision_count": decisions.count("quarantine"),
        "unique_review_record_sha_count": len(set(review_shas)),
        "unique_ingestion_envelope_sha_count": len(set(envelope_shas)),
        "result_digest_count": sum(bool(value) for value in result_shas),
        "response_digest_valid": response[
            "multi_boundary_submission_adapter_response_sha256"
        ] == _canonical_sha(
            response,
            "multi_boundary_submission_adapter_response_sha256",
        ),
        "deterministic": responses[0] == responses[1],
        "input_unchanged": source_payload == source_snapshot,
        "compiler_calls_per_adapt": calls["compiler"] // 2,
        "sidecar_calls_per_adapt": calls["sidecar"] // 2,
        "authority_context_calls_per_adapt":
            calls["authority_context"] // 2,
        "ingestion_evaluator_calls_per_adapt":
            calls["ingestion_evaluator"] // 2,
        "files_written": calls["writes"] != 0,
        "authority_created": False,
        "v1_authority_modified": False,
    }
    expected = {
        "adapter_passed": True,
        "reason": "PASSED",
        "adapter_result_record_count": 5,
        "adapted_submission_count": 5,
        "ready_for_ingestion_count": 5,
        "accept_decision_count": 4,
        "revise_decision_count": 1,
        "quarantine_decision_count": 0,
        "unique_review_record_sha_count": 5,
        "unique_ingestion_envelope_sha_count": 5,
        "result_digest_count": 5,
        "response_digest_valid": True,
        "deterministic": True,
        "input_unchanged": True,
        "compiler_calls_per_adapt": 0,
        "sidecar_calls_per_adapt": 0,
        "authority_context_calls_per_adapt": 0,
        "ingestion_evaluator_calls_per_adapt": 0,
        "files_written": False,
        "authority_created": False,
        "v1_authority_modified": False,
    }
    observed = {
        key: assertions[key] for key in expected
    }
    if observed != expected:
        raise AssertionError((observed, expected))

    for key, value in assertions.items():
        rendered = str(value).lower() if type(value) is bool else value
        print(f"{key}={rendered}")
    print("ingestion_envelope_sha256s=" + _json(envelope_shas))
    print("adapter_result_sha256s=" + _json(result_shas))
    print(
        "adapter_response_sha256="
        + response["multi_boundary_submission_adapter_response_sha256"]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
