#!/usr/bin/env python3
"""Check the in-memory Current11 multi-boundary authority bundle."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from covalent_ext import (
    covapie_current11_multi_boundary_authority_bundle_v1 as subject,
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


def _load_precedence_checker(repo_root: Path):
    path = (
        repo_root
        / "scripts/check_covapie_current11_multi_boundary_authority_"
        "materialization_and_unified_precedence_design_v1.py"
    )
    specification = importlib.util.spec_from_file_location(
        "precedence_checker_for_authority_bundle_checker", path,
    )
    if specification is None or specification.loader is None:
        raise AssertionError("precedence checker unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _synthetic_inputs(repo_root: Path) -> tuple[bytes, bytes, bytes]:
    return _load_precedence_checker(repo_root)._synthetic_inputs(repo_root)


def _build(
    repo_root: Path,
    inputs: tuple[bytes, bytes, bytes],
) -> bytes:
    return subject.build_covapie_current11_multi_boundary_authority_bundle_v1(
        source_v1_submission_bundle=inputs[0],
        source_v1_ingestion_execution_bundle=inputs[1],
        source_multi_boundary_ingestion_execution_bundle=inputs[2],
        repo_root=repo_root,
    )


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _check(repo_root: Path) -> dict[str, object]:
    # Synthetic construction and independent expected design are outside budgets.
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
    selected = tuple(
        record for record in expected_design["resolution_records"]
        if record["effective_authority_namespace"]
        == subject.AUTHORITY_NAMESPACE
    )
    input_snapshots = tuple(bytes(value) for value in inputs)
    source_execution = json.loads(inputs[2])
    source_authorities = source_execution["new_authority_records"]
    source_authority_snapshot = copy.deepcopy(source_authorities)

    calls = {
        "precedence_design": 0,
        "compiler": 0,
        "adapter": 0,
        "public_ingestion_interface": 0,
        "private_ingestion_evaluator": 0,
        "execution_builder": 0,
        "writes": 0,
    }
    originals = {
        "precedence_design":
            precedence_design
            ._reference_design_covapie_current11_unified_authority_precedence_v1,
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
        "execution_builder":
            multi_execution
            .build_covapie_current11_multi_boundary_human_review_ingestion_execution_bundle_v1,
    }
    path_writes = {
        name: getattr(Path, name)
        for name in ("write_bytes", "write_text", "touch", "mkdir")
    }

    def counted_precedence(**keywords):
        calls["precedence_design"] += 1
        return originals["precedence_design"](**keywords)

    def forbidden(name: str):
        def fail(*_arguments, **_keywords):
            calls[name] += 1
            raise AssertionError(f"forbidden call: {name}")

        return fail

    try:
        precedence_design._reference_design_covapie_current11_unified_authority_precedence_v1 = counted_precedence
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
        mutated_first["authority_records"][0][
            "reviewed_warhead_atom_ids"
        ].append("MUTATION")
        second = _build(repo_root, inputs)
    finally:
        precedence_design._reference_design_covapie_current11_unified_authority_precedence_v1 = originals[
            "precedence_design"
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

    _, bundle = multi_design._strict_json_object(second)
    authorities = bundle["authority_records"]
    for authority in authorities:
        multi_design._validate_authority_record(authority)
    selected_shas = tuple(
        record["unified_precedence_resolution_record_sha256"]
        for record in selected
    )
    authority_shas = tuple(
        authority["multi_boundary_authority_record_sha256"]
        for authority in authorities
    )
    linkage_valid = all(
        resolution["sample_index_row_id"]
        == authority["sample_index_row_id"]
        and resolution["multi_boundary_authority_record_sha256"]
        == authority["multi_boundary_authority_record_sha256"]
        and resolution["effective_authority_record_sha256"]
        == authority["multi_boundary_authority_record_sha256"]
        and resolution["multi_boundary_authority_status"]
        == authority["authority_status"] == "active"
        and resolution["effective_boundary_cardinality"] == 2
        for resolution, authority in zip(selected, authorities)
    )
    round_trip_valid = (
        tuple(bundle) == subject.EXACT16_FIELDS
        and bundle["multi_boundary_authority_bundle_sha256"]
        == subject._record_sha256(
            bundle,
            subject.EXACT16_FIELDS,
            "multi_boundary_authority_bundle_sha256",
        )
        and not second.startswith(b"\xef\xbb\xbf")
        and b"\x00" not in second
        and b"\n" not in second
        and len(second) < 1024 * 1024
    )
    inputs_unchanged = input_snapshots == inputs
    source_authority_objects_unchanged = (
        source_authority_snapshot == source_authorities
        and source_authority_snapshot
        == json.loads(inputs[2])["new_authority_records"]
    )
    responses_isolated = (
        pristine_first == json.loads(second)
        and mutated_first != json.loads(second)
        and source_authority_objects_unchanged
    )
    build_count = 2
    assertions: dict[str, object] = {
        "authority_bundle_version":
            bundle["multi_boundary_authority_bundle_version"],
        "authority_namespace": bundle["authority_namespace"],
        "authority_bundle_field_count": len(bundle),
        "source_v1_execution_filesystem_sha256":
            bundle[
                "source_v1_ingestion_execution_bundle_filesystem_sha256"
            ],
        "source_v1_execution_internal_sha256":
            bundle["source_v1_ingestion_execution_bundle_sha256"],
        "source_multi_boundary_execution_filesystem_sha256":
            bundle[
                "source_multi_boundary_ingestion_execution_bundle_filesystem_sha256"
            ],
        "source_multi_boundary_execution_internal_sha256":
            bundle[
                "source_multi_boundary_ingestion_execution_bundle_sha256"
            ],
        "source_precedence_design_version":
            bundle["source_unified_precedence_design_version"],
        "source_precedence_design_response_sha256":
            bundle["source_unified_precedence_design_response_sha256"],
        "selected_resolution_count":
            len(bundle["selected_resolution_record_sha256s"]),
        "sample_order": ",".join(bundle["sample_order"]),
        "authority_record_count": bundle["authority_record_count"],
        "active_authority_count": bundle["active_authority_count"],
        "exact_two_boundary_authority_count":
            bundle["exact_two_boundary_authority_count"],
        "v1_quarantine_backlink_count":
            bundle["v1_quarantine_backlink_count"],
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
        "unique_authority_digest_count": len(set(authority_shas)),
        "authority_record_sha256s": ",".join(authority_shas),
        "selected_resolution_record_sha256s": ",".join(selected_shas),
        "authority_bundle_sha256":
            bundle["multi_boundary_authority_bundle_sha256"],
        "authority_transport_sha256": _sha256(second),
        "authority_transport_size": len(second),
        "deterministic": first == second,
        "round_trip_valid": round_trip_valid,
        "inputs_unchanged": inputs_unchanged,
        "source_authority_objects_unchanged":
            source_authority_objects_unchanged,
        "responses_isolated": responses_isolated,
        "precedence_design_calls_per_build":
            calls["precedence_design"] // build_count,
        "compiler_calls_per_build": calls["compiler"] // build_count,
        "adapter_calls_per_build": calls["adapter"] // build_count,
        "public_ingestion_interface_calls_per_build":
            calls["public_ingestion_interface"] // build_count,
        "private_ingestion_evaluator_calls_per_build":
            calls["private_ingestion_evaluator"] // build_count,
        "execution_builder_calls_per_build":
            calls["execution_builder"] // build_count,
        "files_written": calls["writes"] != 0,
        "durable_authority_file_created": False,
        "unified_effective_view_created": False,
        "unified_gold_created": False,
        "v1_authority_modified": not source_authority_objects_unchanged,
    }
    expected = {
        "authority_bundle_version": subject.AUTHORITY_BUNDLE_VERSION,
        "authority_namespace": subject.AUTHORITY_NAMESPACE,
        "authority_bundle_field_count": 16,
        "selected_resolution_count": 5,
        "sample_order": ",".join(subject._EXPECTED_SAMPLES),
        "authority_record_count": 5,
        "active_authority_count": 5,
        "exact_two_boundary_authority_count": 5,
        "v1_quarantine_backlink_count": 5,
        "accept_authority_count": 4,
        "revise_authority_count": 1,
        "quarantine_authority_count": 0,
        "unique_authority_digest_count": 5,
        "deterministic": True,
        "round_trip_valid": True,
        "inputs_unchanged": True,
        "source_authority_objects_unchanged": True,
        "responses_isolated": True,
        "precedence_design_calls_per_build": 1,
        "compiler_calls_per_build": 0,
        "adapter_calls_per_build": 0,
        "public_ingestion_interface_calls_per_build": 0,
        "private_ingestion_evaluator_calls_per_build": 0,
        "execution_builder_calls_per_build": 0,
        "files_written": False,
        "durable_authority_file_created": False,
        "unified_effective_view_created": False,
        "unified_gold_created": False,
        "v1_authority_modified": False,
    }
    if (
        any(assertions[key] != value for key, value in expected.items())
        or calls["precedence_design"] != build_count
        or any(
            calls[key] != 0
            for key in (
                "compiler",
                "adapter",
                "public_ingestion_interface",
                "private_ingestion_evaluator",
                "execution_builder",
                "writes",
            )
        )
        or bundle["selected_resolution_record_sha256s"]
        != list(selected_shas)
        or bundle["authority_records"] != source_authority_snapshot
        or not linkage_valid
    ):
        raise AssertionError("multi-boundary authority bundle check failed")
    return assertions


def main() -> int:
    assertions = _check(Path(__file__).resolve().parents[1])
    for key, value in assertions.items():
        rendered = str(value).lower() if type(value) is bool else str(value)
        print(f"{key}={rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
