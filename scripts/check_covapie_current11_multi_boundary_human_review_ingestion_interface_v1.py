#!/usr/bin/env python3
"""Check the public in-memory multi-boundary ingestion interface."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from typing import Any

from covalent_ext import (
    covapie_current11_multi_boundary_human_review_ingestion_contract_design_v1
    as design,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_ingestion_interface_v1
    as public_interface,
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
    as predecessor_ingestion,
)


_EXPECTED_CONTEXT_SHA256 = (
    "20103755725ec8f5e8e8b0131f21b23da8942eb5e23503e23f58ec08fcaf4aee"
)
_EXPECTED_AUTHORITY_SHA256S = (
    "64baf4bff6a66531d8a7f1a55f03329ce305fcc31ac3d42f48b0ca5b68f35198",
    "ed3bac34805ec92ba0318495b8ea33b918d62c5c57af498c2fd1b473fb6d2d30",
    "c41bf5d8bd6a0fa7bd4cf02953fad2279524ecc230778a1f84c1f522b56d957d",
    "f393ec80ce6695abc53752185ee73bff553653f4b36b847fd3f477870d4ff871",
    "20ae0941391bad1535d1f31d996aa828f677326ea34fbee75dbf3aa12d5e7d96",
)
_EXPECTED_RESULT_SHA256S = (
    "8bd390c3afe99f7b384160c765935faa41ed84888191433107d15d245f36aba9",
    "4a5f3e55ea5b9f57496704a63c45efdcdd0614d73f5a00f2a8433c02c3980921",
    "f5138a955a8b7a6c9dea6e57e82a2f1a506a6848b12c460f893fc0c0271b1f1a",
    "81b3a9bc66bfe11c44c6ed75fe7ab4bcdfe90ad8fb1426df9836131d688466a7",
    "ab2df326d2143a973409c363d691257d89c18371eeed4a83fe2cace02c77dd9d",
)
_EXPECTED_RESPONSE_SHA256 = (
    "129f9354470da06c987fe7712751bd05e7aa2dbec0c704db4dfec8d870c62267"
)


def _load_design_checker(repo_root: Path):
    path = (
        repo_root
        / "scripts/check_covapie_current11_multi_boundary_"
        "human_review_ingestion_contract_design_v1.py"
    )
    specification = importlib.util.spec_from_file_location(
        "multi_boundary_ingestion_interface_design_checker", path,
    )
    if specification is None or specification.loader is None:
        raise AssertionError("design checker unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _synthetic_case(
    repo_root: Path,
) -> tuple[bytes, bytes, bytes, bytes]:
    return _load_design_checker(repo_root)._synthetic_case(repo_root)


def _private_evaluate(
    repo_root: Path,
    case: tuple[bytes, bytes, bytes, bytes],
) -> dict[str, Any]:
    multi_submission, adapter_response, v1_submission, v1_execution = case
    return design._reference_evaluate_covapie_current11_multi_boundary_ingestion_v1(
        adapter_response_payload=adapter_response,
        source_multi_boundary_submission_bundle=multi_submission,
        source_v1_submission_bundle=v1_submission,
        source_v1_ingestion_execution_bundle=v1_execution,
        repo_root=repo_root,
    )


def _public_evaluate(
    repo_root: Path,
    case: tuple[bytes, bytes, bytes, bytes],
    *,
    existing: Any = (),
) -> dict[str, Any]:
    multi_submission, adapter_response, v1_submission, v1_execution = case
    return (
        public_interface
        .evaluate_covapie_current11_multi_boundary_human_review_ingestion_v1(
            adapter_response_payload=adapter_response,
            source_multi_boundary_submission_bundle=multi_submission,
            source_v1_submission_bundle=v1_submission,
            source_v1_ingestion_execution_bundle=v1_execution,
            repo_root=repo_root,
            existing_multi_boundary_authority_records=existing,
        )
    )


def _mutable_object_ids(value: Any) -> set[int]:
    identities: set[int] = set()
    visited: set[int] = set()

    def visit(item: Any) -> None:
        identity = id(item)
        if identity in visited:
            return
        visited.add(identity)
        if type(item) is dict:
            identities.add(identity)
            for key, nested in item.items():
                visit(key)
                visit(nested)
        elif type(item) is list:
            identities.add(identity)
            for nested in item:
                visit(nested)
        elif type(item) is set:
            identities.add(identity)
            for nested in item:
                visit(nested)
        elif type(item) is tuple:
            for nested in item:
                visit(nested)

    visit(value)
    return identities


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]

    # Synthetic construction and the private expected value are outside the
    # public-interface call budget.
    case = _synthetic_case(repo_root)
    input_snapshots = tuple(bytes(value) for value in case)
    expected = _private_evaluate(repo_root, case)
    expected_snapshot = copy.deepcopy(expected)
    design._validate_interface_response(expected)

    calls = {
        "private_reference": 0,
        "sidecar": 0,
        "authority_context": 0,
        "compiler": 0,
        "adapter": 0,
        "predecessor_ingestion_evaluator": 0,
        "writes": 0,
    }
    original_private = (
        design._reference_evaluate_covapie_current11_multi_boundary_ingestion_v1
    )
    original_sidecar = (
        sidecar.build_covapie_current11_multi_boundary_human_review_sidecar_v1
    )
    original_context = (
        predecessor_ingestion
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
    original_predecessor_evaluator = (
        predecessor_ingestion
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
            raise AssertionError(f"public interface called forbidden {name}")

        return fail

    try:
        design._reference_evaluate_covapie_current11_multi_boundary_ingestion_v1 = (
            counted("private_reference", original_private)
        )
        sidecar.build_covapie_current11_multi_boundary_human_review_sidecar_v1 = (
            counted("sidecar", original_sidecar)
        )
        predecessor_ingestion.build_current11_warhead_boundary_review_ingestion_authority_context_v1 = (
            counted("authority_context", original_context)
        )
        compiler.compile_covapie_current11_multi_boundary_human_review_submission_bundle_v1 = (
            forbidden("compiler")
        )
        adapter.adapt_covapie_current11_multi_boundary_human_review_submission_bundle_v1 = (
            forbidden("adapter")
        )
        predecessor_ingestion.evaluate_current11_warhead_boundary_review_ingestion_v1 = (
            forbidden("predecessor_ingestion_evaluator")
        )
        for name in original_writes:
            setattr(Path, name, forbidden("writes"))
        responses = [_public_evaluate(repo_root, case) for _ in range(2)]
    finally:
        design._reference_evaluate_covapie_current11_multi_boundary_ingestion_v1 = (
            original_private
        )
        sidecar.build_covapie_current11_multi_boundary_human_review_sidecar_v1 = (
            original_sidecar
        )
        predecessor_ingestion.build_current11_warhead_boundary_review_ingestion_authority_context_v1 = (
            original_context
        )
        compiler.compile_covapie_current11_multi_boundary_human_review_submission_bundle_v1 = (
            original_compiler
        )
        adapter.adapt_covapie_current11_multi_boundary_human_review_submission_bundle_v1 = (
            original_adapter
        )
        predecessor_ingestion.evaluate_current11_warhead_boundary_review_ingestion_v1 = (
            original_predecessor_evaluator
        )
        for name, method in original_writes.items():
            setattr(Path, name, method)

    for response in responses:
        design._validate_interface_response(response)
    parity = responses[0] == expected and responses[1] == expected
    deterministic = responses[0] == responses[1]
    isolated_identities = (
        not (
            _mutable_object_ids(responses[0])
            & _mutable_object_ids(expected)
        )
        and not (
            _mutable_object_ids(responses[1])
            & _mutable_object_ids(expected)
        )
        and not (
            _mutable_object_ids(responses[0])
            & _mutable_object_ids(responses[1])
        )
    )
    response = responses[1]
    results = response["ingestion_result_records"]
    authorities = response["new_authority_records"]
    source_adapter = json.loads(case[1])
    candidate_sha256s = tuple(
        record["multi_boundary_authority_record_sha256"]
        for record in authorities
    )
    result_sha256s = tuple(
        result["multi_boundary_ingestion_result_sha256"]
        for result in results
    )
    response_digest_valid = response[
        "multi_boundary_ingestion_interface_response_sha256"
    ] == design._digest(
        response,
        design.MULTI_BOUNDARY_INGESTION_INTERFACE_RESPONSE_FIELDS,
        "multi_boundary_ingestion_interface_response_sha256",
    )

    responses[0]["new_authority_records"][0][
        "reviewed_warhead_atom_ids"
    ].append("__response_isolation_probe__")
    response_isolated = (
        isolated_identities
        and expected == expected_snapshot
        and responses[1] == expected_snapshot
        and responses[0] != responses[1]
    )

    assertions = {
        "public_private_fresh_parity": parity,
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
        "accept_authority_count": sum(
            record["review_decision"]
            == "accept_verified_two_boundary_proposal"
            for record in authorities
        ),
        "revise_authority_count": sum(
            record["review_decision"]
            == "revise_two_boundary_atom_set_and_boundaries"
            for record in authorities
        ),
        "quarantine_authority_count": sum(
            record["review_decision"] == "quarantine"
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
        "result_digest_count": len({
            result["multi_boundary_ingestion_result_sha256"]
            for result in results
        }),
        "unique_authority_digest_count": len(set(candidate_sha256s)),
        "response_digest_valid": response_digest_valid,
        "deterministic": deterministic,
        "inputs_unchanged": case == input_snapshots,
        "response_isolated": response_isolated,
        "private_reference_calls_per_public_evaluation":
            calls["private_reference"] // 2,
        "sidecar_builder_calls_per_public_evaluation":
            calls["sidecar"] // 2,
        "authority_context_builder_calls_per_public_evaluation":
            calls["authority_context"] // 2,
        "compiler_calls_per_public_evaluation": calls["compiler"] // 2,
        "adapter_calls_per_public_evaluation": calls["adapter"] // 2,
        "predecessor_ingestion_evaluator_calls_per_public_evaluation":
            calls["predecessor_ingestion_evaluator"] // 2,
        "files_written": calls["writes"] != 0,
        "durable_authority_created": calls["writes"] != 0,
        "v1_authority_modified": case[3] != input_snapshots[3],
        "candidate_authority_sha256s": list(candidate_sha256s),
        "ingestion_result_sha256s": list(result_sha256s),
        "interface_response_sha256": response[
            "multi_boundary_ingestion_interface_response_sha256"
        ],
    }
    expected_values = {
        "public_private_fresh_parity": True,
        "adapter_response_item_count": 5,
        "ready_for_ingestion_count": 5,
        "authority_context_record_sha256": _EXPECTED_CONTEXT_SHA256,
        "batch_passed": True,
        "ingestion_result_count": 5,
        "new_authority_count": 5,
        "active_authority_count": 5,
        "quarantined_authority_count": 0,
        "accept_authority_count": 4,
        "revise_authority_count": 1,
        "quarantine_authority_count": 0,
        "exact_two_attachment_boundaries_authority_count": 5,
        "v1_quarantine_authority_unchanged_count": 5,
        "idempotent_replay_count": 0,
        "conflict_count": 0,
        "result_digest_count": 5,
        "unique_authority_digest_count": 5,
        "response_digest_valid": True,
        "deterministic": True,
        "inputs_unchanged": True,
        "response_isolated": True,
        "private_reference_calls_per_public_evaluation": 1,
        "sidecar_builder_calls_per_public_evaluation": 1,
        "authority_context_builder_calls_per_public_evaluation": 2,
        "compiler_calls_per_public_evaluation": 0,
        "adapter_calls_per_public_evaluation": 0,
        "predecessor_ingestion_evaluator_calls_per_public_evaluation": 0,
        "files_written": False,
        "durable_authority_created": False,
        "v1_authority_modified": False,
        "candidate_authority_sha256s": list(_EXPECTED_AUTHORITY_SHA256S),
        "ingestion_result_sha256s": list(_EXPECTED_RESULT_SHA256S),
        "interface_response_sha256": _EXPECTED_RESPONSE_SHA256,
    }
    expected_call_totals = {
        "private_reference": 2,
        "sidecar": 2,
        "authority_context": 4,
        "compiler": 0,
        "adapter": 0,
        "predecessor_ingestion_evaluator": 0,
        "writes": 0,
    }
    if calls != expected_call_totals:
        raise AssertionError(
            f"call totals: expected {expected_call_totals!r}, "
            f"observed {calls!r}"
        )
    for key, expected_value in expected_values.items():
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
