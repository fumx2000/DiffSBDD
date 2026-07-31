#!/usr/bin/env python3
"""Check the in-memory Current11 unified-authority precedence design."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

from covalent_ext import (
    covapie_current11_multi_boundary_authority_materialization_and_unified_precedence_design_v1
    as subject,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_ingestion_contract_design_v1
    as multi_design,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_ingestion_execution_bundle_v1
    as multi_execution,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_ingestion_interface_v1
    as public_interface,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_submission_adapter_v1
    as adapter,
)
from covalent_ext import (
    covapie_current11_multi_boundary_human_review_submission_bundle_compiler_v1
    as compiler,
)


def _load_execution_checker(repo_root: Path):
    path = (
        repo_root
        / "scripts/check_covapie_current11_multi_boundary_"
        "human_review_ingestion_execution_bundle_v1.py"
    )
    specification = importlib.util.spec_from_file_location(
        "multi_execution_checker_for_precedence_checker", path,
    )
    if specification is None or specification.loader is None:
        raise AssertionError("execution checker unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _synthetic_inputs(repo_root: Path) -> tuple[bytes, bytes, bytes]:
    checker = _load_execution_checker(repo_root)
    multi_submission, adapter_response, v1_submission, v1_execution = (
        checker._synthetic_case(repo_root)
    )
    multi_execution_payload = (
        multi_execution
        .build_covapie_current11_multi_boundary_human_review_ingestion_execution_bundle_v1(
            adapter_response_payload=adapter_response,
            source_multi_boundary_submission_bundle=multi_submission,
            source_v1_submission_bundle=v1_submission,
            source_v1_ingestion_execution_bundle=v1_execution,
            repo_root=repo_root,
        )
    )
    return v1_submission, v1_execution, multi_execution_payload


def _evaluate(
    repo_root: Path,
    inputs: tuple[bytes, bytes, bytes],
) -> dict[str, Any]:
    return (
        subject
        ._reference_design_covapie_current11_unified_authority_precedence_v1(
            source_v1_submission_bundle=inputs[0],
            source_v1_ingestion_execution_bundle=inputs[1],
            source_multi_boundary_ingestion_execution_bundle=inputs[2],
            repo_root=repo_root,
        )
    )


def _short_sample(sample: str) -> str:
    return sample.rsplit("_", 1)[-1]


def _check(repo_root: Path) -> dict[str, object]:
    # Synthetic construction is deliberately outside all evaluator call budgets.
    inputs = _synthetic_inputs(repo_root)
    input_snapshots = tuple(bytes(value) for value in inputs)
    source_authority_snapshots = (
        json.loads(inputs[1])["new_authority_records"],
        json.loads(inputs[2])["new_authority_records"],
    )
    calls = {
        "compiler": 0,
        "adapter": 0,
        "public_ingestion_interface": 0,
        "private_ingestion_evaluator": 0,
        "writes": 0,
    }
    originals = {
        "compiler":
            compiler
            .compile_covapie_current11_multi_boundary_human_review_submission_bundle_v1,
        "adapter":
            adapter
            .adapt_covapie_current11_multi_boundary_human_review_submission_bundle_v1,
        "public_ingestion_interface":
            public_interface
            .evaluate_covapie_current11_multi_boundary_human_review_ingestion_v1,
        "private_ingestion_evaluator":
            multi_design
            ._reference_evaluate_covapie_current11_multi_boundary_ingestion_v1,
    }
    path_writes = {
        name: getattr(Path, name)
        for name in ("write_bytes", "write_text", "touch", "mkdir")
    }

    def forbidden(name: str):
        def fail(*_arguments, **_keywords):
            calls[name] += 1
            raise AssertionError(f"forbidden evaluator call: {name}")

        return fail

    try:
        compiler.compile_covapie_current11_multi_boundary_human_review_submission_bundle_v1 = forbidden(
            "compiler"
        )
        adapter.adapt_covapie_current11_multi_boundary_human_review_submission_bundle_v1 = forbidden(
            "adapter"
        )
        public_interface.evaluate_covapie_current11_multi_boundary_human_review_ingestion_v1 = forbidden(
            "public_ingestion_interface"
        )
        multi_design._reference_evaluate_covapie_current11_multi_boundary_ingestion_v1 = forbidden(
            "private_ingestion_evaluator"
        )
        for name in path_writes:
            setattr(Path, name, forbidden("writes"))
        responses = (_evaluate(repo_root, inputs), _evaluate(repo_root, inputs))
    finally:
        compiler.compile_covapie_current11_multi_boundary_human_review_submission_bundle_v1 = originals[
            "compiler"
        ]
        adapter.adapt_covapie_current11_multi_boundary_human_review_submission_bundle_v1 = originals[
            "adapter"
        ]
        public_interface.evaluate_covapie_current11_multi_boundary_human_review_ingestion_v1 = originals[
            "public_ingestion_interface"
        ]
        multi_design._reference_evaluate_covapie_current11_multi_boundary_ingestion_v1 = originals[
            "private_ingestion_evaluator"
        ]
        for name, method in path_writes.items():
            setattr(Path, name, method)

    response = responses[1]
    records = response["resolution_records"]
    inputs_unchanged = input_snapshots == inputs
    source_authority_objects_unchanged = source_authority_snapshots == (
        json.loads(inputs[1])["new_authority_records"],
        json.loads(inputs[2])["new_authority_records"],
    )
    legacy_selected = tuple(
        _short_sample(record["sample_index_row_id"])
        for record in records
        if record["effective_authority_namespace"]
        == subject._LEGACY_NAMESPACE
    )
    multi_selected = tuple(
        _short_sample(record["sample_index_row_id"])
        for record in records
        if record["effective_authority_namespace"]
        == subject._MULTI_NAMESPACE
    )
    record_shas = tuple(
        record["unified_precedence_resolution_record_sha256"]
        for record in records
    )
    record_digests_valid = all(
        record["unified_precedence_resolution_record_sha256"]
        == subject._record_sha256(
            record,
            subject._RESOLUTION_FIELDS,
            "unified_precedence_resolution_record_sha256",
        )
        for record in records
    )
    response_digest_valid = response[
        "unified_authority_precedence_design_response_sha256"
    ] == subject._record_sha256(
        response,
        subject._RESPONSE_FIELDS,
        "unified_authority_precedence_design_response_sha256",
    )
    assertions: dict[str, object] = {
        "resolution_record_count": len(records),
        "effective_legacy_exact_one_count":
            response["effective_legacy_exact_one_count"],
        "effective_multi_boundary_exact_two_count":
            response["effective_multi_boundary_exact_two_count"],
        "legacy_selected_samples": ",".join(legacy_selected),
        "multi_boundary_selected_samples": ",".join(multi_selected),
        "source_v1_execution_filesystem_sha256":
            response[
                "source_v1_ingestion_execution_bundle_filesystem_sha256"
            ],
        "source_v1_execution_internal_sha256":
            response["source_v1_ingestion_execution_bundle_sha256"],
        "source_multi_boundary_execution_filesystem_sha256":
            response[
                "source_multi_boundary_ingestion_execution_bundle_filesystem_sha256"
            ],
        "source_multi_boundary_execution_internal_sha256":
            response[
                "source_multi_boundary_ingestion_execution_bundle_sha256"
            ],
        "ready_for_authority_and_unified_view_implementation":
            response[
                "ready_for_authority_and_unified_view_implementation"
            ],
        "deterministic": responses[0] == responses[1],
        "inputs_unchanged": inputs_unchanged,
        "source_authority_objects_unchanged":
            source_authority_objects_unchanged,
        "compiler_calls": calls["compiler"],
        "adapter_calls": calls["adapter"],
        "public_ingestion_interface_calls":
            calls["public_ingestion_interface"],
        "private_ingestion_evaluator_calls":
            calls["private_ingestion_evaluator"],
        "files_written": calls["writes"] != 0,
        "authority_bundle_created": False,
        "unified_gold_created": False,
        "v1_authority_modified": not source_authority_objects_unchanged,
        "resolution_record_sha256s": ",".join(record_shas),
        "design_response_sha256":
            response[
                "unified_authority_precedence_design_response_sha256"
            ],
    }
    expected = {
        "resolution_record_count": 11,
        "effective_legacy_exact_one_count": 6,
        "effective_multi_boundary_exact_two_count": 5,
        "legacy_selected_samples":
            "000001,000002,000003,000004,000005,000011",
        "multi_boundary_selected_samples":
            "000006,000007,000008,000009,000010",
        "ready_for_authority_and_unified_view_implementation": True,
        "deterministic": True,
        "inputs_unchanged": True,
        "source_authority_objects_unchanged": True,
        "compiler_calls": 0,
        "adapter_calls": 0,
        "public_ingestion_interface_calls": 0,
        "private_ingestion_evaluator_calls": 0,
        "files_written": False,
        "authority_bundle_created": False,
        "unified_gold_created": False,
        "v1_authority_modified": False,
    }
    if (
        any(assertions[key] != value for key, value in expected.items())
        or not record_digests_valid
        or not response_digest_valid
        or tuple(record["sample_index_row_id"] for record in records)
        != subject._EXPECTED_SAMPLES
        or tuple(response) != subject._RESPONSE_FIELDS
        or any(tuple(record) != subject._RESOLUTION_FIELDS for record in records)
    ):
        raise AssertionError("unified authority precedence design check failed")
    return assertions


def main() -> int:
    assertions = _check(Path(__file__).resolve().parents[1])
    for key, value in assertions.items():
        if type(value) is bool:
            rendered = str(value).lower()
        else:
            rendered = str(value)
        print(f"{key}={rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
