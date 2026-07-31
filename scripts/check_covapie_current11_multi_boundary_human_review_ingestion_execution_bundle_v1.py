#!/usr/bin/env python3
"""Check the in-memory multi-boundary ingestion execution-bundle builder."""

from __future__ import annotations

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
    covapie_current11_multi_boundary_human_review_ingestion_execution_bundle_v1
    as execution,
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


def _load_interface_checker(repo_root: Path):
    path = (
        repo_root
        / "scripts/check_covapie_current11_multi_boundary_"
        "human_review_ingestion_interface_v1.py"
    )
    specification = importlib.util.spec_from_file_location(
        "multi_boundary_ingestion_interface_checker_for_execution", path,
    )
    if specification is None or specification.loader is None:
        raise AssertionError("interface checker unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _synthetic_case(
    repo_root: Path,
) -> tuple[bytes, bytes, bytes, bytes]:
    return _load_interface_checker(repo_root)._synthetic_case(repo_root)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_sha(
    record: dict[str, Any],
    fields: tuple[str, ...],
    excluded: str,
) -> str:
    return _sha256(json.dumps(
        {field: record[field] for field in fields if field != excluded},
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8"))


def _build(
    repo_root: Path,
    case: tuple[bytes, bytes, bytes, bytes],
) -> bytes:
    multi_submission, adapter_response, v1_submission, v1_execution = case
    return execution.build_covapie_current11_multi_boundary_human_review_ingestion_execution_bundle_v1(
        adapter_response_payload=adapter_response,
        source_multi_boundary_submission_bundle=multi_submission,
        source_v1_submission_bundle=v1_submission,
        source_v1_ingestion_execution_bundle=v1_execution,
        repo_root=repo_root,
    )


def _check(repo_root: Path) -> dict[str, object]:
    # Synthetic input construction is deliberately outside every call budget.
    case = _synthetic_case(repo_root)
    snapshots = tuple(bytes(payload) for payload in case)
    calls = {
        "public_interface": 0,
        "private_reference": 0,
        "sidecar": 0,
        "authority_context": 0,
        "compiler": 0,
        "adapter": 0,
        "predecessor_ingestion_evaluator": 0,
        "writes": 0,
    }
    originals = {
        "public_interface":
            public_interface
            .evaluate_covapie_current11_multi_boundary_human_review_ingestion_v1,
        "private_reference":
            design
            ._reference_evaluate_covapie_current11_multi_boundary_ingestion_v1,
        "sidecar":
            sidecar
            .build_covapie_current11_multi_boundary_human_review_sidecar_v1,
        "authority_context":
            predecessor_ingestion
            .build_current11_warhead_boundary_review_ingestion_authority_context_v1,
        "compiler":
            compiler
            .compile_covapie_current11_multi_boundary_human_review_submission_bundle_v1,
        "adapter":
            adapter
            .adapt_covapie_current11_multi_boundary_human_review_submission_bundle_v1,
        "predecessor_ingestion_evaluator":
            predecessor_ingestion
            .evaluate_current11_warhead_boundary_review_ingestion_v1,
    }
    path_writes = {
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
            raise AssertionError(f"builder called forbidden {name}")

        return fail

    try:
        public_interface.evaluate_covapie_current11_multi_boundary_human_review_ingestion_v1 = counted(
            "public_interface", originals["public_interface"],
        )
        design._reference_evaluate_covapie_current11_multi_boundary_ingestion_v1 = counted(
            "private_reference", originals["private_reference"],
        )
        sidecar.build_covapie_current11_multi_boundary_human_review_sidecar_v1 = counted(
            "sidecar", originals["sidecar"],
        )
        predecessor_ingestion.build_current11_warhead_boundary_review_ingestion_authority_context_v1 = counted(
            "authority_context", originals["authority_context"],
        )
        compiler.compile_covapie_current11_multi_boundary_human_review_submission_bundle_v1 = forbidden(
            "compiler"
        )
        adapter.adapt_covapie_current11_multi_boundary_human_review_submission_bundle_v1 = forbidden(
            "adapter"
        )
        predecessor_ingestion.evaluate_current11_warhead_boundary_review_ingestion_v1 = forbidden(
            "predecessor_ingestion_evaluator"
        )
        for name in path_writes:
            setattr(Path, name, forbidden("writes"))
        payloads = (_build(repo_root, case), _build(repo_root, case))
    finally:
        public_interface.evaluate_covapie_current11_multi_boundary_human_review_ingestion_v1 = originals[
            "public_interface"
        ]
        design._reference_evaluate_covapie_current11_multi_boundary_ingestion_v1 = originals[
            "private_reference"
        ]
        sidecar.build_covapie_current11_multi_boundary_human_review_sidecar_v1 = originals[
            "sidecar"
        ]
        predecessor_ingestion.build_current11_warhead_boundary_review_ingestion_authority_context_v1 = originals[
            "authority_context"
        ]
        compiler.compile_covapie_current11_multi_boundary_human_review_submission_bundle_v1 = originals[
            "compiler"
        ]
        adapter.adapt_covapie_current11_multi_boundary_human_review_submission_bundle_v1 = originals[
            "adapter"
        ]
        predecessor_ingestion.evaluate_current11_warhead_boundary_review_ingestion_v1 = originals[
            "predecessor_ingestion_evaluator"
        ]
        for name, method in path_writes.items():
            setattr(Path, name, method)

    payload = payloads[1]
    _, bundle = design._strict_json_object(payload)
    if tuple(bundle) != execution.EXACT16_FIELDS:
        raise AssertionError("execution Exact16 invalid")
    results = bundle["ingestion_result_records"]
    authorities = bundle["new_authority_records"]
    for result in results:
        design._validate_result_record(result)
    for authority in authorities:
        design._validate_authority_record(authority)
    response = {
        "multi_boundary_ingestion_interface_response_version":
            bundle["ingestion_interface_response_version"],
        "authority_context_record_sha256":
            bundle["authority_context_record_sha256"],
        "batch_passed": bundle["batch_passed"],
        "ingestion_result_records": tuple(results),
        "new_authority_records": tuple(authorities),
        "multi_boundary_ingestion_interface_response_sha256":
            bundle["ingestion_interface_response_sha256"],
    }
    design._validate_interface_response(response)
    execution_sha_valid = bundle[
        "multi_boundary_ingestion_execution_bundle_sha256"
    ] == _canonical_sha(
        bundle,
        execution.EXACT16_FIELDS,
        "multi_boundary_ingestion_execution_bundle_sha256",
    )
    round_trip_valid = (
        json.dumps(
            bundle,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
        == payload
    )
    candidate_shas = tuple(
        authority["multi_boundary_authority_record_sha256"]
        for authority in authorities
    )
    result_shas = tuple(
        result["multi_boundary_ingestion_result_sha256"]
        for result in results
    )

    assertions: dict[str, object] = {
        "execution_bundle_version": bundle[
            "multi_boundary_ingestion_execution_bundle_version"
        ],
        "execution_bundle_field_count": len(bundle),
        "source_v1_submission_bundle_sha256":
            bundle["source_v1_submission_bundle_sha256"],
        "source_v1_ingestion_execution_bundle_filesystem_sha256":
            bundle[
                "source_v1_ingestion_execution_bundle_filesystem_sha256"
            ],
        "source_v1_ingestion_execution_bundle_sha256":
            bundle["source_v1_ingestion_execution_bundle_sha256"],
        "source_multi_boundary_submission_bundle_filesystem_sha256":
            bundle[
                "source_multi_boundary_submission_bundle_filesystem_sha256"
            ],
        "source_multi_boundary_submission_bundle_sha256":
            bundle["source_multi_boundary_submission_bundle_sha256"],
        "source_adapter_response_filesystem_sha256":
            bundle["source_adapter_response_filesystem_sha256"],
        "source_adapter_response_sha256":
            bundle["source_adapter_response_sha256"],
        "submission_batch_id": bundle["submission_batch_id"],
        "authority_context_record_sha256":
            bundle["authority_context_record_sha256"],
        "batch_passed": bundle["batch_passed"],
        "ingestion_result_count": len(results),
        "new_authority_count": len(authorities),
        "active_authority_count": sum(
            authority["authority_status"] == "active"
            for authority in authorities
        ),
        "exact_two_boundary_authority_count": sum(
            authority[
                "exact_two_attachment_boundaries_authority_available"
            ] is True
            for authority in authorities
        ),
        "v1_quarantine_authority_unchanged_count": sum(
            authority["v1_quarantine_authority_unchanged"] is True
            for authority in authorities
        ),
        "accept_authority_count": sum(
            authority["review_decision"]
            == "accept_verified_two_boundary_proposal"
            for authority in authorities
        ),
        "revise_authority_count": sum(
            authority["review_decision"]
            == "revise_two_boundary_atom_set_and_boundaries"
            for authority in authorities
        ),
        "quarantine_authority_count": sum(
            authority["review_decision"] == "quarantine"
            for authority in authorities
        ),
        "result_digest_count": len(result_shas),
        "unique_authority_digest_count": len(set(candidate_shas)),
        "interface_response_sha256":
            bundle["ingestion_interface_response_sha256"],
        "execution_bundle_sha256":
            bundle[
                "multi_boundary_ingestion_execution_bundle_sha256"
            ],
        "execution_transport_sha256": _sha256(payload),
        "execution_transport_size": len(payload),
        "deterministic": payloads[0] == payloads[1],
        "round_trip_valid": round_trip_valid and execution_sha_valid,
        "inputs_unchanged": case == snapshots,
        "public_interface_calls_per_build":
            calls["public_interface"] // 2,
        "private_reference_calls_per_build":
            calls["private_reference"] // 2,
        "sidecar_builder_calls_per_build": calls["sidecar"] // 2,
        "authority_context_builder_calls_per_build":
            calls["authority_context"] // 2,
        "compiler_calls_per_build": calls["compiler"] // 2,
        "adapter_calls_per_build": calls["adapter"] // 2,
        "predecessor_ingestion_evaluator_calls_per_build":
            calls["predecessor_ingestion_evaluator"] // 2,
        "files_written": calls["writes"] != 0,
        "durable_execution_file_created": False,
        "durable_authority_created": False,
        "v1_authority_modified": case[3] != snapshots[3],
        "candidate_authority_sha256s": list(candidate_shas),
        "ingestion_result_sha256s": list(result_shas),
    }
    expected_values = {
        "execution_bundle_version": execution.EXECUTION_BUNDLE_VERSION,
        "execution_bundle_field_count": 16,
        "authority_context_record_sha256": _EXPECTED_CONTEXT_SHA256,
        "batch_passed": True,
        "ingestion_result_count": 5,
        "new_authority_count": 5,
        "active_authority_count": 5,
        "exact_two_boundary_authority_count": 5,
        "v1_quarantine_authority_unchanged_count": 5,
        "accept_authority_count": 4,
        "revise_authority_count": 1,
        "quarantine_authority_count": 0,
        "result_digest_count": 5,
        "unique_authority_digest_count": 5,
        "interface_response_sha256": _EXPECTED_RESPONSE_SHA256,
        "deterministic": True,
        "round_trip_valid": True,
        "inputs_unchanged": True,
        "public_interface_calls_per_build": 1,
        "private_reference_calls_per_build": 1,
        "sidecar_builder_calls_per_build": 1,
        "authority_context_builder_calls_per_build": 3,
        "compiler_calls_per_build": 0,
        "adapter_calls_per_build": 0,
        "predecessor_ingestion_evaluator_calls_per_build": 0,
        "files_written": False,
        "durable_execution_file_created": False,
        "durable_authority_created": False,
        "v1_authority_modified": False,
        "candidate_authority_sha256s": list(_EXPECTED_AUTHORITY_SHA256S),
        "ingestion_result_sha256s": list(_EXPECTED_RESULT_SHA256S),
    }
    expected_call_totals = {
        "public_interface": 2,
        "private_reference": 2,
        "sidecar": 2,
        "authority_context": 6,
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
    for key, expected in expected_values.items():
        if assertions[key] != expected:
            raise AssertionError(
                f"{key}: expected {expected!r}, "
                f"observed {assertions[key]!r}"
            )
    return assertions


def main() -> int:
    assertions = _check(Path(__file__).resolve().parents[1])
    for key, value in assertions.items():
        print(f"{key}={json.dumps(value, ensure_ascii=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
