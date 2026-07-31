#!/usr/bin/env python3
"""Check the in-memory Current11 unified effective authority view."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

from covalent_ext import (
    covapie_current11_multi_boundary_authority_bundle_v1
    as multi_authority_bundle,
)
from covalent_ext import (
    covapie_current11_multi_boundary_authority_materialization_and_unified_precedence_design_v1
    as precedence_design,
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
from covalent_ext import (
    covapie_current11_unified_effective_authority_view_v1 as subject,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_gate_design_v1
    as legacy_design,
)


def _load_precedence_checker(repo_root: Path):
    path = (
        repo_root
        / "scripts/check_covapie_current11_multi_boundary_authority_"
        "materialization_and_unified_precedence_design_v1.py"
    )
    specification = importlib.util.spec_from_file_location(
        "precedence_checker_for_unified_view_checker", path,
    )
    if specification is None or specification.loader is None:
        raise AssertionError("precedence checker unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _synthetic_inputs(
    repo_root: Path,
) -> tuple[bytes, bytes, bytes, bytes]:
    inputs = _load_precedence_checker(repo_root)._synthetic_inputs(repo_root)
    authority_bundle = (
        multi_authority_bundle
        .build_covapie_current11_multi_boundary_authority_bundle_v1(
            source_v1_submission_bundle=inputs[0],
            source_v1_ingestion_execution_bundle=inputs[1],
            source_multi_boundary_ingestion_execution_bundle=inputs[2],
            repo_root=repo_root,
        )
    )
    return (*inputs, authority_bundle)


def _build(
    repo_root: Path,
    inputs: tuple[bytes, bytes, bytes, bytes],
) -> bytes:
    return subject.build_covapie_current11_unified_effective_authority_view_v1(
        source_v1_submission_bundle=inputs[0],
        source_v1_ingestion_execution_bundle=inputs[1],
        source_multi_boundary_ingestion_execution_bundle=inputs[2],
        source_multi_boundary_authority_bundle=inputs[3],
        repo_root=repo_root,
    )


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _check(repo_root: Path) -> dict[str, object]:
    # All synthetic construction and expected design work precedes call budgets.
    inputs = _synthetic_inputs(repo_root)
    expected_design = (
        precedence_design
        ._reference_design_covapie_current11_unified_authority_precedence_v1(
            source_v1_submission_bundle=inputs[0],
            source_v1_ingestion_execution_bundle=inputs[1],
            source_multi_boundary_ingestion_execution_bundle=inputs[2],
            repo_root=repo_root,
        )
    )
    input_snapshots = tuple(bytes(value) for value in inputs)
    legacy_execution = json.loads(inputs[1])
    multi_execution_value = json.loads(inputs[2])
    authority_bundle = json.loads(inputs[3])
    legacy_authorities = legacy_execution["new_authority_records"]
    multi_authorities = multi_execution_value["new_authority_records"]
    authority_bundle_records = authority_bundle["authority_records"]
    legacy_snapshot = copy.deepcopy(legacy_authorities)
    multi_snapshot = copy.deepcopy(multi_authorities)
    authority_bundle_snapshot = copy.deepcopy(authority_bundle_records)

    calls = {
        "precedence_design": 0,
        "legacy_validation": 0,
        "multi_validation": 0,
        "authority_bundle_builder": 0,
        "compiler": 0,
        "adapter": 0,
        "public_ingestion_interface": 0,
        "private_ingestion_evaluator": 0,
        "execution_builder": 0,
        "writes": 0,
    }
    originals = {
        "precedence_design": precedence_design
        ._reference_design_covapie_current11_unified_authority_precedence_v1,
        "legacy_validation": precedence_design._validate_legacy_execution,
        "multi_validation": precedence_design._validate_multi_execution,
        "authority_bundle_builder": multi_authority_bundle
        .build_covapie_current11_multi_boundary_authority_bundle_v1,
        "compiler": compiler
        .compile_covapie_current11_multi_boundary_human_review_submission_bundle_v1,
        "adapter": adapter
        .adapt_covapie_current11_multi_boundary_human_review_submission_bundle_v1,
        "public_ingestion_interface": public_interface
        .evaluate_covapie_current11_multi_boundary_human_review_ingestion_v1,
        "private_ingestion_evaluator": multi_design
        ._reference_evaluate_covapie_current11_multi_boundary_ingestion_v1,
        "execution_builder": multi_execution
        .build_covapie_current11_multi_boundary_human_review_ingestion_execution_bundle_v1,
    }
    path_writes = {
        name: getattr(Path, name)
        for name in ("write_bytes", "write_text", "touch", "mkdir")
    }

    def counted(name: str):
        def call(*arguments, **keywords):
            calls[name] += 1
            return originals[name](*arguments, **keywords)

        return call

    def forbidden(name: str):
        def fail(*_arguments, **_keywords):
            calls[name] += 1
            raise AssertionError(f"forbidden call: {name}")

        return fail

    try:
        precedence_design._reference_design_covapie_current11_unified_authority_precedence_v1 = counted(
            "precedence_design"
        )
        precedence_design._validate_legacy_execution = counted(
            "legacy_validation"
        )
        precedence_design._validate_multi_execution = counted(
            "multi_validation"
        )
        multi_authority_bundle.build_covapie_current11_multi_boundary_authority_bundle_v1 = forbidden(
            "authority_bundle_builder"
        )
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
        multi_execution.build_covapie_current11_multi_boundary_human_review_ingestion_execution_bundle_v1 = forbidden(
            "execution_builder"
        )
        for name in path_writes:
            setattr(Path, name, forbidden("writes"))

        first = _build(repo_root, inputs)
        mutated_first = json.loads(first)
        pristine_first = copy.deepcopy(mutated_first)
        mutated_first["effective_authority_records"][0][
            "effective_authority_record"
        ]["reviewed_warhead_atom_ids"].append("MUTATION")
        second = _build(repo_root, inputs)
    finally:
        precedence_design._reference_design_covapie_current11_unified_authority_precedence_v1 = originals[
            "precedence_design"
        ]
        precedence_design._validate_legacy_execution = originals[
            "legacy_validation"
        ]
        precedence_design._validate_multi_execution = originals[
            "multi_validation"
        ]
        multi_authority_bundle.build_covapie_current11_multi_boundary_authority_bundle_v1 = originals[
            "authority_bundle_builder"
        ]
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
        multi_execution.build_covapie_current11_multi_boundary_human_review_ingestion_execution_bundle_v1 = originals[
            "execution_builder"
        ]
        for name, method in path_writes.items():
            setattr(Path, name, method)

    view = subject._strict_json_object(second)
    records = view["effective_authority_records"]
    resolutions = expected_design["resolution_records"]
    legacy_selected = tuple(
        record["sample_index_row_id"] for record in records
        if record["effective_authority_namespace"]
        == subject._LEGACY_NAMESPACE
    )
    multi_selected = tuple(
        record["sample_index_row_id"] for record in records
        if record["effective_authority_namespace"] == subject._MULTI_NAMESPACE
    )
    for record in records:
        authority = record["effective_authority_record"]
        if record["effective_authority_namespace"] == subject._LEGACY_NAMESPACE:
            legacy_design.validate_authority_record(authority)
        else:
            multi_design._validate_authority_record(authority)
    record_sha256s = tuple(
        record["unified_effective_authority_record_sha256"]
        for record in records
    )
    authority_sha256s = tuple(
        record["source_authority_record_sha256"] for record in records
    )
    exact_records_valid = all(
        tuple(record) == subject.EXACT10_EFFECTIVE_RECORD_FIELDS
        and record["unified_effective_authority_record_version"]
        == subject.EFFECTIVE_RECORD_VERSION
        and record["unified_effective_authority_record_sha256"]
        == subject._record_sha256(
            record,
            subject.EXACT10_EFFECTIVE_RECORD_FIELDS,
            "unified_effective_authority_record_sha256",
        )
        and record["sample_index_row_id"]
        == resolution["sample_index_row_id"]
        and record["source_resolution_record_sha256"]
        == resolution["unified_precedence_resolution_record_sha256"]
        and record["source_authority_record_sha256"]
        == resolution["effective_authority_record_sha256"]
        and (
            record["effective_authority_namespace"],
            record["effective_boundary_cardinality"],
            record["precedence_reason"],
        ) == (
            resolution["effective_authority_namespace"],
            resolution["effective_boundary_cardinality"],
            resolution["precedence_reason"],
        )
        for record, resolution in zip(records, resolutions)
    )
    round_trip_valid = (
        tuple(view) == subject.EXACT16_VIEW_FIELDS
        and tuple(record["sample_index_row_id"] for record in records)
        == subject._EXPECTED_SAMPLES
        and exact_records_valid
        and view["unified_effective_authority_view_sha256"]
        == subject._record_sha256(
            view,
            subject.EXACT16_VIEW_FIELDS,
            "unified_effective_authority_view_sha256",
        )
        and not second.startswith(b"\xef\xbb\xbf")
        and b"\x00" not in second
        and b"\n" not in second
        and len(second) < 2 * 1024 * 1024
    )
    inputs_unchanged = input_snapshots == inputs
    legacy_unchanged = (
        legacy_snapshot == legacy_authorities
        and legacy_snapshot
        == json.loads(inputs[1])["new_authority_records"]
    )
    multi_unchanged = (
        multi_snapshot == multi_authorities
        and multi_snapshot
        == json.loads(inputs[2])["new_authority_records"]
    )
    bundle_unchanged = (
        authority_bundle_snapshot == authority_bundle_records
        and authority_bundle_snapshot
        == json.loads(inputs[3])["authority_records"]
    )
    responses_isolated = (
        pristine_first == json.loads(second)
        and mutated_first != json.loads(second)
        and legacy_unchanged
        and multi_unchanged
        and bundle_unchanged
    )
    build_count = 2
    assertions: dict[str, object] = {
        "view_version": view[
            "unified_effective_authority_view_version"
        ],
        "view_field_count": len(view),
        "effective_record_version": records[0][
            "unified_effective_authority_record_version"
        ],
        "effective_record_count": view[
            "effective_authority_record_count"
        ],
        "effective_legacy_exact_one_count": view[
            "effective_legacy_exact_one_count"
        ],
        "effective_multi_boundary_exact_two_count": view[
            "effective_multi_boundary_exact_two_count"
        ],
        "legacy_selected_samples": ",".join(
            sample.rsplit("_", 1)[-1] for sample in legacy_selected
        ),
        "multi_boundary_selected_samples": ",".join(
            sample.rsplit("_", 1)[-1] for sample in multi_selected
        ),
        "sample_order": ",".join(view["sample_order"]),
        "source_v1_submission_filesystem_sha256": view[
            "source_v1_submission_bundle_filesystem_sha256"
        ],
        "source_v1_execution_filesystem_sha256": view[
            "source_v1_ingestion_execution_bundle_filesystem_sha256"
        ],
        "source_v1_execution_internal_sha256": view[
            "source_v1_ingestion_execution_bundle_sha256"
        ],
        "source_multi_execution_filesystem_sha256": view[
            "source_multi_boundary_ingestion_execution_bundle_filesystem_sha256"
        ],
        "source_multi_execution_internal_sha256": view[
            "source_multi_boundary_ingestion_execution_bundle_sha256"
        ],
        "source_multi_authority_bundle_filesystem_sha256": view[
            "source_multi_boundary_authority_bundle_filesystem_sha256"
        ],
        "source_multi_authority_bundle_internal_sha256": view[
            "source_multi_boundary_authority_bundle_sha256"
        ],
        "source_precedence_design_version": view[
            "source_unified_precedence_design_version"
        ],
        "source_precedence_design_response_sha256": view[
            "source_unified_precedence_design_response_sha256"
        ],
        "effective_record_sha256s": ",".join(record_sha256s),
        "effective_source_authority_sha256s": ",".join(
            authority_sha256s
        ),
        "view_sha256": view[
            "unified_effective_authority_view_sha256"
        ],
        "transport_sha256": _sha256(second),
        "transport_size": len(second),
        "deterministic": first == second,
        "round_trip_valid": round_trip_valid,
        "inputs_unchanged": inputs_unchanged,
        "legacy_source_authorities_unchanged": legacy_unchanged,
        "multi_source_authorities_unchanged": multi_unchanged,
        "authority_bundle_records_unchanged": bundle_unchanged,
        "responses_isolated": responses_isolated,
        "precedence_design_calls_per_build":
            calls["precedence_design"] // build_count,
        "legacy_validation_calls_per_build":
            calls["legacy_validation"] // build_count,
        "multi_validation_calls_per_build":
            calls["multi_validation"] // build_count,
        "authority_bundle_builder_calls_per_build":
            calls["authority_bundle_builder"] // build_count,
        "compiler_calls_per_build": calls["compiler"] // build_count,
        "adapter_calls_per_build": calls["adapter"] // build_count,
        "public_ingestion_interface_calls_per_build":
            calls["public_ingestion_interface"] // build_count,
        "private_ingestion_evaluator_calls_per_build":
            calls["private_ingestion_evaluator"] // build_count,
        "execution_builder_calls_per_build":
            calls["execution_builder"] // build_count,
        "files_written": calls["writes"] != 0,
        "formal_view_file_created": False,
        "unified_gold_created": False,
        "v1_authority_modified": not legacy_unchanged,
    }
    expected = {
        "view_version": subject.UNIFIED_EFFECTIVE_VIEW_VERSION,
        "view_field_count": 16,
        "effective_record_version": subject.EFFECTIVE_RECORD_VERSION,
        "effective_record_count": 11,
        "effective_legacy_exact_one_count": 6,
        "effective_multi_boundary_exact_two_count": 5,
        "legacy_selected_samples": "000001,000002,000003,000004,000005,000011",
        "multi_boundary_selected_samples": "000006,000007,000008,000009,000010",
        "sample_order": ",".join(subject._EXPECTED_SAMPLES),
        "deterministic": True,
        "round_trip_valid": True,
        "inputs_unchanged": True,
        "legacy_source_authorities_unchanged": True,
        "multi_source_authorities_unchanged": True,
        "authority_bundle_records_unchanged": True,
        "responses_isolated": True,
        "precedence_design_calls_per_build": 1,
        "legacy_validation_calls_per_build": 1,
        "multi_validation_calls_per_build": 1,
        "authority_bundle_builder_calls_per_build": 0,
        "compiler_calls_per_build": 0,
        "adapter_calls_per_build": 0,
        "public_ingestion_interface_calls_per_build": 0,
        "private_ingestion_evaluator_calls_per_build": 0,
        "execution_builder_calls_per_build": 0,
        "files_written": False,
        "formal_view_file_created": False,
        "unified_gold_created": False,
        "v1_authority_modified": False,
    }
    if (
        any(assertions[key] != value for key, value in expected.items())
        or any(
            calls[key] != build_count
            for key in (
                "precedence_design",
                "legacy_validation",
                "multi_validation",
            )
        )
        or any(
            calls[key] != 0
            for key in (
                "authority_bundle_builder",
                "compiler",
                "adapter",
                "public_ingestion_interface",
                "private_ingestion_evaluator",
                "execution_builder",
                "writes",
            )
        )
        or authority_bundle_records != multi_authorities
    ):
        raise AssertionError("unified effective authority view check failed")
    return assertions


def main() -> int:
    assertions = _check(Path(__file__).resolve().parents[1])
    for key, value in assertions.items():
        rendered = str(value).lower() if type(value) is bool else str(value)
        print(f"{key}={rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
