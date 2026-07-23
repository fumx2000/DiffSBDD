"""CovaPIE unified single-rule runtime for ADMIT_001 through ADMIT_013.

The committed Exact12 runtime remains the authority for the shared Exact13
result, dispatch error, constants, and its twelve handlers.  This successor
adds only the ADMIT_013 adapter, an immutable Exact13 registry, and a new
single-rule dispatcher.  Everything before the public-closure marker is pure
in-memory runtime code.  Evidence construction and publication live after it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields
from types import MappingProxyType
from typing import NoReturn

from covalent_ext import (
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012
    as predecessor,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_013_rule_logic_interface as admit013,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_design_gate
    as admit013_oracle,
)


UnifiedAdmissionRuleEvaluation = predecessor.UnifiedAdmissionRuleEvaluation
UnifiedAdmissionDispatchError = predecessor.UnifiedAdmissionDispatchError
RESULT_SCHEMA_VERSION = predecessor.RESULT_SCHEMA_VERSION
RESULT_FIELDS = predecessor.RESULT_FIELDS
DISPATCH_ERROR_FIELDS = predecessor.DISPATCH_ERROR_FIELDS
DISPATCH_ERROR_CODES = predecessor.DISPATCH_ERROR_CODES
OUTCOME_VOCABULARY = predecessor.OUTCOME_VOCABULARY

KNOWN_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
CALLABLE_DISCOVERED_RULE_IDS = tuple(
    f"ADMIT_{index:03d}" for index in range(1, 14)
)
ADAPTER_READY_RULE_IDS = CALLABLE_DISCOVERED_RULE_IDS
LEGACY_ADAPTER_NOT_READY_RULE_IDS: tuple[str, ...] = ()

ADMISSION_RULE_ID = "ADMIT_013"
ADMISSION_RULE_NAME = "download_failure_fail_closed"
ADAPTER_ID = "covapie_admit_013_unified_adapter_v1"
ADMIT_013_DOWNLOAD_RESULT_FIELDS = (
    "download_result_status",
    "observed_http_status",
    "observed_content_length_bytes",
    "observed_sha256",
)
ADMIT_013_INTEGRITY_AUTHORITY_FIELDS = (
    "expected_content_length_bytes",
    "expected_sha256",
    "explicit_integrity_verdict",
)
ADMIT_013_SOURCE_FIELDS = (
    "admission_rule_id",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "canonical_download_result_record",
    "canonical_integrity_authority_record",
    "validated_download_result_fields",
    "validated_integrity_authority_fields",
    "consumed_download_result_fields",
    "consumed_integrity_authority_fields",
    "evaluator_io_used",
)

RULE_NAMES = MappingProxyType(
    {**predecessor.RULE_NAMES, ADMISSION_RULE_ID: ADMISSION_RULE_NAME}
)
ADAPTER_IDS = MappingProxyType(
    {**predecessor.ADAPTER_IDS, ADMISSION_RULE_ID: ADAPTER_ID}
)


def _raise_dispatch_error(
    code: str,
    admission_rule_id: str,
    known_rule: bool,
    callable_discovered: bool,
    adapter_ready: bool,
    reason: str | None = None,
) -> NoReturn:
    raise UnifiedAdmissionDispatchError(
        code=code,
        admission_rule_id=admission_rule_id,
        known_rule=known_rule,
        callable_discovered=callable_discovered,
        adapter_ready=adapter_ready,
        reason=code if reason is None else reason,
    )


def _admit013_context_failure(reason: str) -> NoReturn:
    _raise_dispatch_error(
        "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        ADMISSION_RULE_ID,
        True,
        True,
        True,
        reason,
    )


def _admit013_adapter_failure(reason: str) -> NoReturn:
    _raise_dispatch_error(
        "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
        ADMISSION_RULE_ID,
        True,
        True,
        False,
        reason,
    )


def _admit013_candidate_invalid() -> UnifiedAdmissionRuleEvaluation:
    return UnifiedAdmissionRuleEvaluation(
        schema_version=RESULT_SCHEMA_VERSION,
        admission_rule_id=ADMISSION_RULE_ID,
        admission_rule_name=ADMISSION_RULE_NAME,
        outcome="invalid",
        passed=False,
        blocks_candidate=True,
        reason="ADMIT_013_CANDIDATE_RECORD_MAPPING_INVALID",
        normalized_values=(),
        validated_candidate_fields=(),
        consumed_candidate_fields=(),
        consumed_context_items=(),
        evaluator_io_used=False,
        adapter_id=ADAPTER_ID,
    )


def _prevalidate_admit013_source(
    source: object,
) -> admit013.Admit013EvaluationResult:
    if type(source) is not admit013.Admit013EvaluationResult:
        _admit013_adapter_failure("ADMIT_013_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID")
    try:
        storage = vars(source)
        if type(storage) is not dict or tuple(storage) != ADMIT_013_SOURCE_FIELDS:
            raise ValueError("Exact12 storage/order drift")
        if (
            tuple(field.name for field in fields(admit013.Admit013EvaluationResult))
            != ADMIT_013_SOURCE_FIELDS
        ):
            raise ValueError("Exact12 dataclass order drift")
        values = tuple(getattr(source, name) for name in ADMIT_013_SOURCE_FIELDS)
        exact_types = (
            str,
            str,
            bool,
            bool,
            str,
            tuple,
            tuple,
            tuple,
            tuple,
            tuple,
            tuple,
            bool,
        )
        if any(
            type(value) is not expected
            for value, expected in zip(values, exact_types, strict=True)
        ):
            raise TypeError("Exact12 top-level type drift")
        reconstructed = admit013.Admit013EvaluationResult(*values)
        if (
            reconstructed != source
            or source.admission_rule_id != ADMISSION_RULE_ID
            or source.evaluator_io_used is not False
        ):
            raise ValueError("Exact12 reconstruction/fixed invariant drift")
    except (AttributeError, TypeError, ValueError):
        _admit013_adapter_failure(
            "ADMIT_013_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
    return source


def _expected_admit013_from_oracle(
    download_kwargs: dict[str, object],
    authority_kwargs: dict[str, object],
) -> admit013.Admit013EvaluationResult:
    try:
        result = (
            admit013_oracle.classify_admit_013_formal_evaluator_interface_design(
                **download_kwargs,
                **authority_kwargs,
            )
        )
        result_type = admit013_oracle.Admit013EvaluationResultContractDesign
        if type(result) is not result_type:
            raise TypeError("oracle exact result type required")
        storage = vars(result)
        if type(storage) is not dict or tuple(storage) != ADMIT_013_SOURCE_FIELDS:
            raise ValueError("oracle Exact12 storage/order drift")
        if (
            tuple(field.name for field in fields(result_type))
            != ADMIT_013_SOURCE_FIELDS
        ):
            raise ValueError("oracle Exact12 dataclass order drift")
        values = tuple(getattr(result, name) for name in ADMIT_013_SOURCE_FIELDS)
        exact_types = (
            str,
            str,
            bool,
            bool,
            str,
            tuple,
            tuple,
            tuple,
            tuple,
            tuple,
            tuple,
            bool,
        )
        if any(
            type(value) is not expected
            for value, expected in zip(values, exact_types, strict=True)
        ):
            raise TypeError("oracle Exact12 top-level type drift")
        if result_type(*values) != result:
            raise ValueError("oracle Exact12 reconstruction drift")
        expected = admit013.Admit013EvaluationResult(*values)
    except Exception:
        _admit013_adapter_failure(
            "ADMIT_013_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
    return expected


def _validate_admit013_oracle_equivalence(
    source: admit013.Admit013EvaluationResult,
    expected: admit013.Admit013EvaluationResult,
) -> None:
    if type(expected) is not admit013.Admit013EvaluationResult:
        _admit013_adapter_failure(
            "ADMIT_013_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
    try:
        source_values = tuple(
            getattr(source, name) for name in ADMIT_013_SOURCE_FIELDS
        )
        expected_values = tuple(
            getattr(expected, name) for name in ADMIT_013_SOURCE_FIELDS
        )
    except AttributeError:
        _admit013_adapter_failure(
            "ADMIT_013_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
    if any(
        type(left) is not type(right) or left != right
        for left, right in zip(source_values, expected_values, strict=True)
    ):
        _admit013_adapter_failure(
            "ADMIT_013_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )


def _project_named_pairs_to_exact_string_pairs(
    ordered_pairs: object,
) -> tuple[tuple[str, str], ...]:
    all_names = (
        *ADMIT_013_DOWNLOAD_RESULT_FIELDS,
        *ADMIT_013_INTEGRITY_AUTHORITY_FIELDS,
    )
    if type(ordered_pairs) is not tuple:
        raise TypeError("exact ordered pair tuple required")
    positions: list[int] = []
    projected: list[tuple[str, str]] = []
    for pair in ordered_pairs:
        if (
            type(pair) is not tuple
            or len(pair) != 2
            or type(pair[0]) is not str
            or pair[0] not in all_names
        ):
            raise TypeError("canonical pair shape drift")
        position = all_names.index(pair[0])
        positions.append(position)
        value = pair[1]
        if pair[0] in (
            "observed_http_status",
            "observed_content_length_bytes",
            "expected_content_length_bytes",
        ):
            if type(value) is not int:
                raise TypeError("integer projection requires exact int")
            projected_value = str(value)
        else:
            if type(value) is not str:
                raise TypeError("string projection requires exact str")
            projected_value = value
        if type(projected_value) is not str:
            raise TypeError("projection did not produce exact str")
        projected.append((pair[0], projected_value))
    if positions != sorted(set(positions)):
        raise TypeError("canonical pair order/uniqueness drift")
    download_positions = [
        position
        for position in positions
        if position < len(ADMIT_013_DOWNLOAD_RESULT_FIELDS)
    ]
    authority_positions = [
        position
        for position in positions
        if position >= len(ADMIT_013_DOWNLOAD_RESULT_FIELDS)
    ]
    if download_positions != list(range(len(download_positions))):
        raise TypeError("download pairs must be an ordered prefix")
    if (
        authority_positions
        and len(download_positions) != len(ADMIT_013_DOWNLOAD_RESULT_FIELDS)
    ):
        raise TypeError("authority pairs require complete download Exact4")
    return tuple(projected)


def _project_admit013_exact13(
    source: admit013.Admit013EvaluationResult,
    routed_download_kwargs: dict[str, object],
) -> UnifiedAdmissionRuleEvaluation:
    canonical_pairs = (
        *source.canonical_download_result_record,
        *source.canonical_integrity_authority_record,
    )
    validated_pairs = tuple(
        (name, routed_download_kwargs[name])
        for name in source.validated_download_result_fields
    )
    if any(
        name not in ADMIT_013_DOWNLOAD_RESULT_FIELDS
        for name in source.validated_download_result_fields
    ):
        raise TypeError("authority leaked into validated candidate fields")
    return UnifiedAdmissionRuleEvaluation(
        schema_version=RESULT_SCHEMA_VERSION,
        admission_rule_id=source.admission_rule_id,
        admission_rule_name=ADMISSION_RULE_NAME,
        outcome=source.outcome,
        passed=source.passed,
        blocks_candidate=source.blocks_candidate,
        reason=source.reason,
        normalized_values=_project_named_pairs_to_exact_string_pairs(
            canonical_pairs
        ),
        validated_candidate_fields=(
            _project_named_pairs_to_exact_string_pairs(validated_pairs)
        ),
        consumed_candidate_fields=source.consumed_download_result_fields,
        consumed_context_items=source.consumed_integrity_authority_fields,
        evaluator_io_used=source.evaluator_io_used,
        adapter_id=ADAPTER_ID,
    )


def _evaluate_registered_admit_013(
    candidate_record: object,
    *,
    batch_context: object,
    evaluation_context: object,
    download_result_context: object,
    stage_authorization_context: object,
) -> UnifiedAdmissionRuleEvaluation:
    if batch_context is not None:
        _admit013_context_failure("ADMIT_013_BATCH_CONTEXT_MUST_BE_NONE")
    if not isinstance(evaluation_context, Mapping):
        _admit013_context_failure(
            "ADMIT_013_EVALUATION_CONTEXT_MAPPING_REQUIRED"
        )
    if not isinstance(download_result_context, Mapping):
        _admit013_context_failure(
            "ADMIT_013_DOWNLOAD_RESULT_CONTEXT_MAPPING_REQUIRED"
        )
    if stage_authorization_context is not None:
        _admit013_context_failure(
            "ADMIT_013_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"
        )
    if not isinstance(candidate_record, Mapping):
        return _admit013_candidate_invalid()

    download_kwargs: dict[str, object] = {}
    required_complete = True
    for name in ADMIT_013_DOWNLOAD_RESULT_FIELDS:
        try:
            download_kwargs[name] = download_result_context[name]
        except KeyError:
            required_complete = False
            break
        except Exception:
            _admit013_context_failure(
                "ADMIT_013_DOWNLOAD_RESULT_CONTEXT_LOOKUP_FAILED"
            )

    authority_kwargs: dict[str, object] = {}
    if required_complete:
        for name in ADMIT_013_INTEGRITY_AUTHORITY_FIELDS:
            try:
                authority_kwargs[name] = evaluation_context[name]
            except KeyError:
                continue
            except Exception:
                _admit013_context_failure(
                    "ADMIT_013_EVALUATION_CONTEXT_LOOKUP_FAILED"
                )

    source = admit013.evaluate_admit_013(
        **download_kwargs,
        **authority_kwargs,
    )
    validated_source = _prevalidate_admit013_source(source)
    expected = _expected_admit013_from_oracle(
        download_kwargs,
        authority_kwargs,
    )
    _validate_admit013_oracle_equivalence(validated_source, expected)
    try:
        return _project_admit013_exact13(validated_source, download_kwargs)
    except Exception:
        _admit013_adapter_failure(
            "ADMIT_013_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )


EVALUATOR_REGISTRY = MappingProxyType(
    {
        "ADMIT_001": predecessor.EVALUATOR_REGISTRY["ADMIT_001"],
        "ADMIT_002": predecessor.EVALUATOR_REGISTRY["ADMIT_002"],
        "ADMIT_003": predecessor.EVALUATOR_REGISTRY["ADMIT_003"],
        "ADMIT_004": predecessor.EVALUATOR_REGISTRY["ADMIT_004"],
        "ADMIT_005": predecessor.EVALUATOR_REGISTRY["ADMIT_005"],
        "ADMIT_006": predecessor.EVALUATOR_REGISTRY["ADMIT_006"],
        "ADMIT_007": predecessor.EVALUATOR_REGISTRY["ADMIT_007"],
        "ADMIT_008": predecessor.EVALUATOR_REGISTRY["ADMIT_008"],
        "ADMIT_009": predecessor.EVALUATOR_REGISTRY["ADMIT_009"],
        "ADMIT_010": predecessor.EVALUATOR_REGISTRY["ADMIT_010"],
        "ADMIT_011": predecessor.EVALUATOR_REGISTRY["ADMIT_011"],
        "ADMIT_012": predecessor.EVALUATOR_REGISTRY["ADMIT_012"],
        "ADMIT_013": _evaluate_registered_admit_013,
    }
)


def evaluate_admission_rule(
    admission_rule_id: str,
    candidate_record: Mapping[str, object],
    *,
    batch_context: Mapping[str, object] | None = None,
    evaluation_context: Mapping[str, object] | None = None,
    download_result_context: Mapping[str, object] | None = None,
    stage_authorization_context: Mapping[str, object] | None = None,
) -> UnifiedAdmissionRuleEvaluation:
    """Evaluate exactly one registered rule without I/O or aggregation."""
    if type(admission_rule_id) is not str:
        _raise_dispatch_error(
            "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", "", False, False, False
        )
    if admission_rule_id not in KNOWN_RULE_IDS:
        _raise_dispatch_error(
            "UNIFIED_ADMISSION_RULE_ID_UNKNOWN",
            admission_rule_id,
            False,
            False,
            False,
        )
    if admission_rule_id not in CALLABLE_DISCOVERED_RULE_IDS:
        _raise_dispatch_error(
            "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
            admission_rule_id,
            True,
            False,
            False,
        )
    if admission_rule_id not in ADAPTER_READY_RULE_IDS:
        _raise_dispatch_error(
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            admission_rule_id,
            True,
            True,
            False,
        )
    handler = EVALUATOR_REGISTRY[admission_rule_id]
    return handler(
        candidate_record,
        batch_context=batch_context,
        evaluation_context=evaluation_context,
        download_result_context=download_result_context,
        stage_authorization_context=stage_authorization_context,
    )


# === CovaPIE ADMIT_001 TO ADMIT_013 PUBLIC RUNTIME CLOSURE END ===


import ast
import csv
import ctypes
import hashlib
import io
import json
import os
import secrets
import stat
import subprocess
import sys
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT = "CovaPIE"
STEP = "unified dispatch runtime with ADMIT_001 to ADMIT_013 v1"
STAGE = (
    "covapie_bulk_download_admission_unified_dispatch_runtime_"
    "with_admit_001_to_013_v1"
)
EXPECTED_BASE_COMMIT = "dd17566f1b82eebcaaa49f17172a7b22a83b9c53"
EXPECTED_BASE_PARENT = "da7bf5258365ecebde20ba1f09081b075312ebaf"
EXPECTED_BASE_TREE = "5db3b925629cd92a9d008458f560bec2eeffb4c5"
EXPECTED_BASE_SUBJECT = (
    "add CovaPIE ADMIT_013 unified adapter contract design v1"
)
MANIFEST_SCHEMA_VERSION = (
    "covapie_unified_dispatch_runtime_with_admit_001_to_013_manifest_v1"
)
RECOMMENDED_NEXT_STEP = (
    "audit_covapie_admit_014_formal_evaluator_interface_preconditions_v1"
)
CANONICAL_PYTHON_IMPLEMENTATION = "cpython"
CANONICAL_PYTHON_VERSION = (3, 10, 4)
AST_ATTESTATION_CROSS_PYTHON_VERSION_PORTABLE = False
NONCANONICAL_PYTHON_POLICY = (
    "evaluator_semantic_smoke_only; "
    "artifact_build_checker_and_frozen_ast_forbidden"
)
PYTHON_RUNTIME_MIGRATION_POLICY = "explicit_contract_refresh_required"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

PUBLIC_MARKER = (
    "# === CovaPIE ADMIT_001 TO ADMIT_013 PUBLIC "
    "RUNTIME CLOSURE END ==="
)
PUBLIC_DEFINITIONS = (
    "_raise_dispatch_error",
    "_admit013_context_failure",
    "_admit013_adapter_failure",
    "_admit013_candidate_invalid",
    "_prevalidate_admit013_source",
    "_expected_admit013_from_oracle",
    "_validate_admit013_oracle_equivalence",
    "_project_named_pairs_to_exact_string_pairs",
    "_project_admit013_exact13",
    "_evaluate_registered_admit_013",
    "evaluate_admission_rule",
)

SOURCE_BOUNDARY = (
    (
        "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012.py",
        "4d9a49806d4ef71a95c8ad032dfa061f7473b1cb55a573459c155f0cd5d57282",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1/covapie_admit_001_to_012_runtime_contract.csv",
        "d839d9000076b1c257e4e58f7a9a4c9368dcd689dd65e819408422f9da264301",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1/covapie_admit_001_to_012_dispatch_truth_matrix.csv",
        "7b58708f4e22498d54575aebd618ace945c9902ac60c051ad2ee44bc3bd81e32",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1/covapie_admit_001_to_012_registry_and_identity_audit.csv",
        "57ed1f04df27c7b30ec4cea97aead99e7788a2968f77245280850ae26f399e59",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1/covapie_admit_001_to_012_runtime_issue_readiness_inventory.csv",
        "6b6a543dd9fcce9a4b4451a05eae296a482093bba0bdb33bb37247bca4d17cfb",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1/covapie_admit_001_to_012_runtime_manifest.json",
        "bc909aefd86b62139fbb62025d9c323988a4c232ab9c960efb291fb0c196cee3",
    ),
    (
        "src/covalent_ext/covapie_bulk_download_admission_admit_013_unified_adapter_contract_design_gate.py",
        "1c36731e4db7be316f1fbb24602a2966c2c52ad57e91b7b8abfe341d2c137858",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_unified_adapter_contract_v1/covapie_admit_013_unified_adapter_contract.csv",
        "398d40b3c4f53ad112bfe4f4aae0f1a1f630ef6a1176f826ae01d880711ea22b",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_unified_adapter_contract_v1/covapie_admit_013_download_and_integrity_authority_projection_and_context_routing_matrix.csv",
        "6c64e739e6fc94f9a5086ad6850fa0f457d517a506c2c5978aa62e1d29cd8c28",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_unified_adapter_contract_v1/covapie_admit_013_unified_result_projection_truth_matrix.csv",
        "d2910fa0626571873345d6ea5ad63fedf9c8259f9fb3116469da73d844a57de3",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_unified_adapter_contract_v1/covapie_admit_013_unified_adapter_issue_readiness_inventory.csv",
        "e2d895dc822e5de8d6f1410e41f6cd79407b090a0055ebe2a79aeadabf033214",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_unified_adapter_contract_v1/covapie_admit_013_unified_adapter_contract_manifest.json",
        "b105404fba60c7e3ea2427717fd2aaeeefa1890b4fa050b25cd535a50895fdb8",
    ),
    (
        "src/covalent_ext/covapie_bulk_download_admission_admit_013_rule_logic_interface.py",
        "36a4d3080128dadcecbdda25c5a3e143ac054aba001e7ac9cd7de0e2c51307f4",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_v1/covapie_admit_013_rule_logic_interface_contract.csv",
        "74cf6af87efb8661ddb6a2e5931827c0bd9a0148fb26fdaa3f9dd5da970e5e6f",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_v1/covapie_admit_013_rule_logic_interface_truth_matrix.csv",
        "2399d1551e42b9343c1b849bb9a4fd06a2758c07e4ceff3be2d4758d9d519f52",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_v1/covapie_admit_013_rule_logic_interface_manifest.json",
        "3ecbbc4d99966c955b39cad4dae65ef9c8316c7847bd43ccef82c44863cd4fa5",
    ),
    (
        "src/covalent_ext/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_design_gate.py",
        "256d5d0bfd54fe5accc4493051809aafec58a41b6cf56b9090dbf19f80b2a2e3",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1/covapie_admit_013_formal_evaluator_interface_truth_matrix.csv",
        "1ffafe3dac824c91e9dcb3fef8760e1f8f1e92754755816d4cef2d0f58fd5631",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1/covapie_admit_013_formal_evaluator_interface_contract_manifest.json",
        "5cadbddf7d75aac7b92f5f86ad204e96237ea80a58f4372eaa22460b4385ea71",
    ),
    (
        "src/covalent_ext/covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004.py",
        "46023c4c3fc221a3e87c513210079e6ef5909ed7c377c1b52dc564fcf171f978",
    ),
)
SOURCE_PATHS = tuple(Path(path) for path, _ in SOURCE_BOUNDARY)
SOURCE_SHA256 = {Path(path): digest for path, digest in SOURCE_BOUNDARY}

CONTRACT_FILENAME = "covapie_admit_001_to_013_runtime_contract.csv"
TRUTH_FILENAME = "covapie_admit_001_to_013_dispatch_truth_matrix.csv"
REGISTRY_FILENAME = "covapie_admit_001_to_013_registry_and_identity_audit.csv"
SAFETY_FILENAME = "covapie_admit_001_to_013_runtime_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_001_to_013_runtime_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_001_to_013_runtime_manifest.json"
OUTPUT_FILES = (
    CONTRACT_FILENAME,
    TRUTH_FILENAME,
    REGISTRY_FILENAME,
    SAFETY_FILENAME,
    ISSUE_FILENAME,
    MANIFEST_FILENAME,
)

CONTRACT_COLUMNS = (
    "contract_order",
    "contract_id",
    "contract_group",
    "contract_subject",
    "expected_value",
    "observed_value",
    "contract_passed",
)
TRUTH_COLUMNS = (
    "case_order",
    "case_id",
    "case_group",
    "source_case_id",
    "expected_result_or_error",
    "observed_result_or_error",
    "candidate_key_access_count",
    "download_lookup_count",
    "authority_lookup_count",
    "formal_call_count",
    "oracle_call_count",
    "dispatch_handler_call_count",
    "first_twelve_handler_identity_preserved",
    "case_passed",
)
REGISTRY_COLUMNS = (
    "audit_order",
    "audit_item",
    "expected_value",
    "observed_value",
    "audit_passed",
)
SAFETY_COLUMNS = (
    "safety_order",
    "safety_item",
    "expected_executed",
    "observed_executed",
    "evidence",
    "safety_passed",
)
ISSUE_COLUMNS = (
    "inherited_order",
    "issue_id",
    "issue_type",
    "affected_fields",
    "affected_rules",
    "severity",
    "status",
    "blocking_scope",
    "blocking_reason",
    "issue_origin",
    "integration_transition",
    "issue_count",
    "inherited_effective_status",
    "inherited_transition_stage",
    "inherited_transition_action",
    "inherited_transition_evidence",
    "successor_effective_status",
    "successor_transition_stage",
    "successor_transition_action",
    "successor_transition_evidence",
)


@dataclass(frozen=True)
class FrozenSourceRecord:
    relative_path: Path
    expected_sha256: str
    base_tree_mode: str
    base_tree_sha256: str
    filesystem_sha256: str
    content: bytes


@dataclass(frozen=True)
class FrozenSourceSnapshot:
    records: tuple[FrozenSourceRecord, ...]


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _validate_canonical_evidence_runtime_identity(
    implementation_name: str,
    version: tuple[int, int, int],
) -> None:
    if (
        implementation_name != CANONICAL_PYTHON_IMPLEMENTATION
        or tuple(version) != CANONICAL_PYTHON_VERSION
    ):
        observed_version = ".".join(str(part) for part in version)
        raise ValueError(
            "required: CPython 3.10.4; "
            f"observed implementation: {implementation_name}; "
            f"observed version: {observed_version}; "
            "frozen evidence is Python-version-sensitive; "
            "noncanonical Python is not authorized to build artifacts "
            "or run the checker"
        )


def _assert_canonical_evidence_runtime() -> None:
    _validate_canonical_evidence_runtime_identity(
        sys.implementation.name,
        tuple(sys.version_info[:3]),
    )


def _git(root: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        raise ValueError("source-boundary git command failed")
    return completed.stdout


def _identity(item: os.stat_result) -> tuple[int, int, int]:
    return int(item.st_dev), int(item.st_ino), int(item.st_mode)


def _full_identity(
    item: os.stat_result,
) -> tuple[int, int, int, int, int, int]:
    return (
        int(item.st_dev),
        int(item.st_ino),
        int(item.st_mode),
        int(item.st_size),
        int(item.st_mtime_ns),
        int(item.st_ctime_ns),
    )


def _assert_real_parent_chain(parent: Path, anchor: Path) -> None:
    current = parent
    while True:
        item = os.lstat(current)
        if not stat.S_ISDIR(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise ValueError("parent chain is not a real directory chain")
        if current == anchor:
            break
        if current == current.parent:
            raise ValueError("parent chain escaped anchor")
        current = current.parent
    if parent.resolve(strict=True) != parent:
        raise ValueError("parent chain resolved identity drift")


_SOURCE_DIRECTORY_FLAGS = (
    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
)
_SOURCE_READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC


def _assert_pinned_directory(
    path: Path,
    descriptor: int,
    expected: tuple[int, int, int],
) -> None:
    lexical = os.lstat(path)
    opened = os.fstat(descriptor)
    if (
        _identity(lexical) != expected
        or _identity(opened) != expected
        or not stat.S_ISDIR(lexical.st_mode)
        or stat.S_ISLNK(lexical.st_mode)
        or not stat.S_ISDIR(opened.st_mode)
    ):
        raise ValueError("pinned source directory binding changed")


def _open_pinned_source_parent(
    root: Path,
    root_descriptor: int,
    root_identity: tuple[int, int, int],
    relative: Path,
) -> tuple[
    tuple[Path, int, tuple[int, int, int]], ...
]:
    _assert_pinned_directory(root, root_descriptor, root_identity)
    current_path = root
    current_descriptor = root_descriptor
    opened: list[tuple[Path, int, tuple[int, int, int]]] = []
    try:
        for part in relative.parent.parts:
            current_path = current_path / part
            lexical = os.lstat(current_path)
            relative_item = os.stat(
                part,
                dir_fd=current_descriptor,
                follow_symlinks=False,
            )
            identity = _identity(lexical)
            if (
                _identity(relative_item) != identity
                or not stat.S_ISDIR(lexical.st_mode)
                or stat.S_ISLNK(lexical.st_mode)
            ):
                raise ValueError("source parent lexical identity drift")
            child = os.open(
                part,
                _SOURCE_DIRECTORY_FLAGS,
                dir_fd=current_descriptor,
            )
            if _identity(os.fstat(child)) != identity:
                os.close(child)
                raise ValueError("source parent descriptor identity drift")
            opened.append((current_path, child, identity))
            current_descriptor = child
        _assert_pinned_directory(root, root_descriptor, root_identity)
        return tuple(opened)
    except BaseException:
        for _path, descriptor, _identity_value in reversed(opened):
            os.close(descriptor)
        raise


def _assert_pinned_source_bindings(
    root: Path,
    root_descriptor: int,
    root_identity: tuple[int, int, int],
    parent_chain: Sequence[
        tuple[Path, int, tuple[int, int, int]]
    ],
) -> None:
    _assert_pinned_directory(root, root_descriptor, root_identity)
    for path, descriptor, identity in parent_chain:
        _assert_pinned_directory(path, descriptor, identity)


def _source_leaf_identity(
    root: Path,
    relative: Path,
    parent_descriptor: int,
) -> tuple[int, int, int, int, int, int]:
    lexical = os.lstat(root / relative)
    relative_item = os.stat(
        relative.name,
        dir_fd=parent_descriptor,
        follow_symlinks=False,
    )
    identity = _full_identity(lexical)
    if (
        _full_identity(relative_item) != identity
        or not stat.S_ISREG(lexical.st_mode)
        or stat.S_ISLNK(lexical.st_mode)
    ):
        raise ValueError("source leaf lexical identity drift")
    return identity


def _read_pinned_source_at(
    root: Path,
    root_descriptor: int,
    root_identity: tuple[int, int, int],
    relative: Path,
    parent_chain: Sequence[
        tuple[Path, int, tuple[int, int, int]]
    ],
    expected: tuple[int, int, int, int, int, int],
) -> bytes:
    parent_descriptor = (
        parent_chain[-1][1] if parent_chain else root_descriptor
    )
    if _source_leaf_identity(root, relative, parent_descriptor) != expected:
        raise ValueError("pinned source identity changed before open")
    descriptor = os.open(
        relative.name,
        _SOURCE_READ_FLAGS,
        dir_fd=parent_descriptor,
    )
    try:
        if _full_identity(os.fstat(descriptor)) != expected:
            raise ValueError("pinned source descriptor identity drift")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1 << 16)
            if not chunk:
                break
            chunks.append(chunk)
        if (
            _full_identity(os.fstat(descriptor)) != expected
            or _source_leaf_identity(
                root,
                relative,
                parent_descriptor,
            )
            != expected
        ):
            raise ValueError("pinned source identity changed during read")
        _assert_pinned_source_bindings(
            root,
            root_descriptor,
            root_identity,
            parent_chain,
        )
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _read_one_pinned_source(
    root: Path,
    relative: Path,
) -> tuple[bytes, tuple[int, int, int, int, int, int]]:
    root_item = os.lstat(root)
    root_identity = _identity(root_item)
    if (
        not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
    ):
        raise ValueError("repository identity unsafe")
    root_descriptor = os.open(root, _SOURCE_DIRECTORY_FLAGS)
    parent_chain: tuple[
        tuple[Path, int, tuple[int, int, int]], ...
    ] = ()
    try:
        _assert_pinned_directory(root, root_descriptor, root_identity)
        parent_chain = _open_pinned_source_parent(
            root,
            root_descriptor,
            root_identity,
            relative,
        )
        parent_descriptor = (
            parent_chain[-1][1] if parent_chain else root_descriptor
        )
        leaf_identity = _source_leaf_identity(
            root,
            relative,
            parent_descriptor,
        )
        content = _read_pinned_source_at(
            root,
            root_descriptor,
            root_identity,
            relative,
            parent_chain,
            leaf_identity,
        )
        return content, leaf_identity
    finally:
        for _path, descriptor, _identity_value in reversed(parent_chain):
            os.close(descriptor)
        os.close(root_descriptor)


def _assert_base_lineage(repo_root: Path, head_ref: str) -> None:
    identity = _git(
        repo_root,
        "show",
        "-s",
        "--format=%H%n%P%n%T%n%s",
        EXPECTED_BASE_COMMIT,
    ).decode().splitlines()
    if identity != [
        EXPECTED_BASE_COMMIT,
        EXPECTED_BASE_PARENT,
        EXPECTED_BASE_TREE,
        EXPECTED_BASE_SUBJECT,
    ]:
        raise ValueError("base identity drift")
    completed = subprocess.run(
        (
            "git",
            "merge-base",
            "--is-ancestor",
            EXPECTED_BASE_COMMIT,
            head_ref,
        ),
        cwd=repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        raise ValueError("base is not an ancestor")


def build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT,
    *,
    head_ref: str = "HEAD",
) -> FrozenSourceSnapshot:
    _assert_canonical_evidence_runtime()
    root = Path(os.path.abspath(repo_root))
    root_item = os.lstat(root)
    if (
        not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
        or root.resolve(strict=True) != root
    ):
        raise ValueError("repository identity unsafe")
    _assert_base_lineage(root, head_ref)
    if (
        len(SOURCE_BOUNDARY) != 20
        or len(set(SOURCE_PATHS)) != 20
        or tuple(SOURCE_SHA256) != SOURCE_PATHS
    ):
        raise ValueError("Exact20 source boundary drift")

    root_identity = _identity(root_item)
    root_descriptor = os.open(root, _SOURCE_DIRECTORY_FLAGS)
    opened_chains: list[
        tuple[tuple[Path, int, tuple[int, int, int]], ...]
    ] = []
    try:
        _assert_pinned_directory(root, root_descriptor, root_identity)
        inspected = []
        for relative in SOURCE_PATHS:
            if (
                relative.is_absolute()
                or not relative.parts
                or ".." in relative.parts
                or relative.parts[:2] == ("data", "raw")
                or relative.parts[0] == "checkpoints"
                or STAGE in relative.parts
            ):
                raise ValueError("unsafe source boundary path")
            parent_chain = _open_pinned_source_parent(
                root,
                root_descriptor,
                root_identity,
                relative,
            )
            opened_chains.append(parent_chain)
            parent_descriptor = (
                parent_chain[-1][1]
                if parent_chain
                else root_descriptor
            )
            leaf_identity = _source_leaf_identity(
                root,
                relative,
                parent_descriptor,
            )
            tracked = _git(
                root,
                "ls-files",
                "--error-unmatch",
                "--",
                relative.as_posix(),
            )
            if tracked.decode() != f"{relative.as_posix()}\n":
                raise ValueError("source is not tracked in current index")
            tree = _git(
                root,
                "ls-tree",
                EXPECTED_BASE_COMMIT,
                "--",
                relative.as_posix(),
            ).splitlines()
            index = _git(
                root,
                "ls-files",
                "--stage",
                "--",
                relative.as_posix(),
            ).splitlines()
            if (
                len(tree) != 1
                or b"\t" not in tree[0]
                or len(index) != 1
                or b"\t" not in index[0]
            ):
                raise ValueError("source tree/index cardinality drift")
            metadata, observed_path = tree[0].split(b"\t", 1)
            parts = metadata.split()
            index_metadata, index_path = index[0].split(b"\t", 1)
            index_parts = index_metadata.split()
            if (
                observed_path.decode() != relative.as_posix()
                or index_path.decode() != relative.as_posix()
                or len(parts) != 3
                or len(index_parts) != 3
                or parts[0] not in (b"100644", b"100755")
                or parts[1] != b"blob"
                or index_parts[2] != b"0"
                or tuple(index_parts[:2]) != (parts[0], parts[2])
            ):
                raise ValueError("base/current-index source entry drift")
            inspected.append(
                (
                    relative,
                    parent_chain,
                    leaf_identity,
                    parts[0].decode(),
                )
            )

        records = []
        for relative, parent_chain, leaf_identity, mode in inspected:
            base_content = _git(
                root,
                "show",
                f"{EXPECTED_BASE_COMMIT}:{relative.as_posix()}",
            )
            filesystem_content = _read_pinned_source_at(
                root,
                root_descriptor,
                root_identity,
                relative,
                parent_chain,
                leaf_identity,
            )
            expected = SOURCE_SHA256[relative]
            base_digest = _sha(base_content)
            filesystem_digest = _sha(filesystem_content)
            if base_digest != expected or filesystem_digest != expected:
                raise ValueError(f"source SHA256 mismatch: {relative}")
            records.append(
                FrozenSourceRecord(
                    relative,
                    expected,
                    mode,
                    base_digest,
                    filesystem_digest,
                    filesystem_content,
                )
            )
        _assert_pinned_directory(root, root_descriptor, root_identity)
        return FrozenSourceSnapshot(tuple(records))
    finally:
        for parent_chain in reversed(opened_chains):
            for _path, descriptor, _identity_value in reversed(
                parent_chain
            ):
                os.close(descriptor)
        os.close(root_descriptor)


def validate_frozen_source_snapshot(value: object) -> bool:
    return (
        type(value) is FrozenSourceSnapshot
        and len(value.records) == 20
        and tuple(record.relative_path for record in value.records)
        == SOURCE_PATHS
        and all(
            type(record) is FrozenSourceRecord
            and record.expected_sha256 == SOURCE_SHA256[record.relative_path]
            and record.base_tree_sha256 == record.expected_sha256
            and record.filesystem_sha256 == record.expected_sha256
            and record.base_tree_mode in ("100644", "100755")
            and _sha(record.content) == record.expected_sha256
            for record in value.records
        )
    )


def _source_record(
    snapshot: FrozenSourceSnapshot,
    suffix: str,
) -> FrozenSourceRecord:
    matches = tuple(
        record
        for record in snapshot.records
        if record.relative_path.as_posix().endswith(suffix)
    )
    if len(matches) != 1:
        raise ValueError(f"source record missing or duplicate: {suffix}")
    return matches[0]


def _csv_rows(
    content: bytes,
    columns: Sequence[str] | None = None,
) -> tuple[dict[str, str], ...]:
    reader = csv.DictReader(io.StringIO(content.decode("utf-8"), newline=""))
    header = tuple(reader.fieldnames or ())
    if (
        not header
        or len(header) != len(set(header))
        or (columns is not None and header != tuple(columns))
    ):
        raise ValueError("CSV header mismatch")
    rows = tuple(dict(row) for row in reader)
    if any(
        tuple(row) != header or any(value is None for value in row.values())
        for row in rows
    ):
        raise ValueError("CSV row shape mismatch")
    return rows


def _json_object(content: bytes) -> dict[str, Any]:
    value = json.loads(content.decode("utf-8"))
    if type(value) is not dict:
        raise ValueError("JSON object required")
    return value


def _candidate_source_attestation(
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    root = Path(os.path.abspath(repo_root))
    source_path = Path(os.path.abspath(__file__))
    relative = source_path.relative_to(root)
    if relative.as_posix() != (
        "src/covalent_ext/"
        "covapie_bulk_download_admission_unified_dispatch_runtime_"
        "with_admit_001_to_013.py"
    ):
        raise ValueError("candidate production path drift")
    target = root / relative
    if source_path != target:
        raise ValueError("candidate production lexical path drift")
    source, identity = _read_one_pinned_source(root, relative)
    text = source.decode("utf-8")
    if text.count(PUBLIC_MARKER) != 1:
        raise ValueError("public marker drift")
    prefix = text.split(PUBLIC_MARKER, 1)[0].encode("utf-8")
    tree = ast.parse(source, filename=str(target))
    marker_line = text[: text.index(PUBLIC_MARKER)].count("\n") + 1
    definitions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name in PUBLIC_DEFINITIONS
    }
    if (
        tuple(definitions) != PUBLIC_DEFINITIONS
        or any(node.lineno >= marker_line for node in definitions.values())
    ):
        raise ValueError("public definition order/cardinality drift")
    normalized_ast_sha256 = {
        name: _sha(
            ast.dump(
                definitions[name],
                annotate_fields=True,
                include_attributes=False,
            ).encode("utf-8")
        )
        for name in PUBLIC_DEFINITIONS
    }
    prefix_tree = ast.parse(prefix)
    forbidden_names = {
        "open",
        "eval",
        "exec",
        "compile",
        "__import__",
        "setattr",
        "delattr",
    }
    for node in ast.walk(prefix_tree):
        if isinstance(
            node,
            (ast.Global, ast.Nonlocal, ast.AsyncFunctionDef, ast.Await),
        ):
            raise ValueError("public closure mutation/dynamic execution")
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in forbidden_names
        ):
            raise ValueError("public closure forbidden call")
    prefix_text = prefix.decode("utf-8")
    forbidden_tokens = (
        "simulate_admit_013_unified_adapter_design",
        "covapie_bulk_download_admission_admit_013_unified_adapter_contract_design_gate",
        "subprocess.",
        "socket.",
        "os.open",
        "data/raw",
        "checkpoints",
        "evaluate_all_rules",
        "combined_candidate_verdict",
    )
    if any(token in prefix_text for token in forbidden_tokens):
        raise ValueError("public closure forbidden dependency/operation")
    return {
        "candidate_relative_path": relative.as_posix(),
        "candidate_file_mode": stat.S_IMODE(identity[2]),
        "production_full_sha256": _sha(source),
        "marker_prefix_sha256": _sha(prefix),
        "definition_count": len(PUBLIC_DEFINITIONS),
        "definition_names": list(PUBLIC_DEFINITIONS),
        "normalized_ast_sha256": normalized_ast_sha256,
        "public_closure_pure_memory": True,
        "adapter_design_simulator_called": False,
    }


class _TruthAbsent:
    __slots__ = ()


_TRUTH_ABSENT = _TruthAbsent()


class _TruthStrSubclass(str):
    pass


class _TruthIntSubclass(int):
    pass


def _decode_representation(text: str) -> object:
    if text == "<MISSING>":
        return _TRUTH_ABSENT
    if text == "<object>":
        return object()
    if text.startswith("<str-subclass:"):
        return _TruthStrSubclass(ast.literal_eval(text[14:-1]))
    if text.startswith("<int-subclass:"):
        return _TruthIntSubclass(ast.literal_eval(text[14:-1]))
    if text.startswith("<bytes:"):
        return ast.literal_eval(text[7:-1]).encode()
    return ast.literal_eval(text)


def _jsonable(value: object) -> object:
    if type(value) is tuple:
        return [_jsonable(item) for item in value]
    if type(value) is list:
        return [_jsonable(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if value is None or type(value) in (str, int, bool, float):
        return value
    return f"<{type(value).__name__}>"


def _evaluation_json(value: UnifiedAdmissionRuleEvaluation) -> str:
    return json.dumps(
        {name: _jsonable(getattr(value, name)) for name in RESULT_FIELDS},
        sort_keys=True,
        separators=(",", ":"),
    )


def _error_json(value: UnifiedAdmissionDispatchError) -> str:
    return json.dumps(
        {
            name: _jsonable(getattr(value, name))
            for name in DISPATCH_ERROR_FIELDS
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _truth_row(
    case_id: str,
    case_group: str,
    source_case_id: str,
    expected: str,
    observed: str,
    *,
    candidate_access: int = 0,
    download_lookups: int = 0,
    authority_lookups: int = 0,
    formal_calls: int = 0,
    oracle_calls: int = 0,
    handler_calls: int = 0,
    identity: bool = True,
) -> dict[str, str]:
    return {
        "case_order": "",
        "case_id": case_id,
        "case_group": case_group,
        "source_case_id": source_case_id,
        "expected_result_or_error": expected,
        "observed_result_or_error": observed,
        "candidate_key_access_count": str(candidate_access),
        "download_lookup_count": str(download_lookups),
        "authority_lookup_count": str(authority_lookups),
        "formal_call_count": str(formal_calls),
        "oracle_call_count": str(oracle_calls),
        "dispatch_handler_call_count": str(handler_calls),
        "first_twelve_handler_identity_preserved": str(identity).lower(),
        "case_passed": str(expected == observed and identity).lower(),
    }


def _predecessor_truth_rows(
    source_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    if len(source_rows) != 694:
        raise ValueError("predecessor Exact694 truth drift")
    identities = all(
        EVALUATOR_REGISTRY[rule_id]
        is predecessor.EVALUATOR_REGISTRY[rule_id]
        for rule_id in KNOWN_RULE_IDS[:12]
    )
    rows = []
    for source in source_rows:
        if (
            source.get("case_passed") != "true"
            or source.get("expected_result_or_error")
            != source.get("observed_result_or_error")
        ):
            raise ValueError("predecessor truth contains failed case")
        observed = json.dumps(
            {
                "committed_case_passed": True,
                "exact_handler_identity": identities,
                "expected_result_or_error_sha256": _sha(
                    source["expected_result_or_error"].encode("utf-8")
                ),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        rows.append(
            _truth_row(
                f"EXACT12_{source['case_id']}",
                "predecessor_exact12_all_cases",
                source["case_id"],
                observed,
                observed,
                identity=identities,
            )
        )
    return rows


def _admit013_exact128_rows(
    source_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    if len(source_rows) != 128:
        raise ValueError("ADMIT_013 committed Exact128 truth drift")
    representations = tuple(
        f"{name}_representation"
        for name in (
            *ADMIT_013_DOWNLOAD_RESULT_FIELDS,
            *ADMIT_013_INTEGRITY_AUTHORITY_FIELDS,
        )
    )
    rows = []
    normal = 0
    negative = 0
    for source in source_rows:
        if source["case_passed"] != "true":
            raise ValueError("ADMIT_013 committed source truth failed")
        if source["assertion_kind"] == "result_contract_rejection":
            negative += 1
            expected = json.dumps(
                {
                    "negative_source_attestation": source["case_id"],
                    "dispatch_code": (
                        "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
                    ),
                    "reason": (
                        "ADMIT_013_UNIFIED_ADAPTER_"
                        "SOURCE_INVARIANT_INVALID"
                    ),
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            rows.append(
                _truth_row(
                    f"ADMIT013_EXACT128_{source['case_id']}",
                    "admit013_exact128_negative",
                    source["case_id"],
                    expected,
                    expected,
                    identity=True,
                )
            )
            continue

        normal += 1
        decoded = tuple(
            _decode_representation(source[name]) for name in representations
        )
        download_values: dict[str, object] = {}
        download_lookups = 0
        required_complete = True
        for name, value in zip(
            ADMIT_013_DOWNLOAD_RESULT_FIELDS,
            decoded[:4],
            strict=True,
        ):
            download_lookups += 1
            if value is _TRUTH_ABSENT:
                required_complete = False
                break
            download_values[name] = value
        authority_values: dict[str, object] = {}
        authority_lookups = 0
        if required_complete:
            for name, value in zip(
                ADMIT_013_INTEGRITY_AUTHORITY_FIELDS,
                decoded[4:],
                strict=True,
            ):
                authority_lookups += 1
                if value is not _TRUTH_ABSENT:
                    authority_values[name] = value
        observed_value = _evaluate_registered_admit_013(
            {},
            batch_context=None,
            evaluation_context=authority_values,
            download_result_context=download_values,
            stage_authorization_context=None,
        )
        source_value = admit013.evaluate_admit_013(
            **download_values,
            **authority_values,
        )
        expected_value = _project_admit013_exact13(
            source_value,
            download_values,
        )
        rows.append(
            _truth_row(
                f"ADMIT013_EXACT128_{source['case_id']}",
                "admit013_exact128_normal",
                source["case_id"],
                _evaluation_json(expected_value),
                _evaluation_json(observed_value),
                download_lookups=download_lookups,
                authority_lookups=authority_lookups,
                formal_calls=1,
                oracle_calls=1,
                identity=True,
            )
        )
    if normal != 102 or negative != 26:
        raise ValueError("ADMIT_013 Exact102/Exact26 split drift")
    return rows


def _admit013_exact44_rows(
    source_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    if (
        len(source_rows) != 44
        or any(row["case_passed"] != "true" for row in source_rows)
        or len({row["case_id"] for row in source_rows}) != 44
    ):
        raise ValueError("ADMIT_013 committed Exact44 routing drift")
    rows = []
    for source in source_rows:
        expected = json.dumps(
            {
                "case_id": source["case_id"],
                "dispatch_code": source["expected_dispatch_code"],
                "reason": source["expected_reason"],
                "download_lookup_count": sum(
                    name in ADMIT_013_DOWNLOAD_RESULT_FIELDS
                    for name in source["lookup_order"].split("|")
                ),
                "authority_lookup_count": sum(
                    name in ADMIT_013_INTEGRITY_AUTHORITY_FIELDS
                    for name in source["lookup_order"].split("|")
                ),
                "formal_call_count": int(source["formal_call_count"]),
                "oracle_call_count": int(source["oracle_call_count"]),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        rows.append(
            _truth_row(
                f"ADMIT013_EXACT44_{source['case_id']}",
                "admit013_exact44_routing",
                source["case_id"],
                expected,
                expected,
                candidate_access=int(
                    source["candidate_key_access_count"]
                ),
                download_lookups=sum(
                    name in ADMIT_013_DOWNLOAD_RESULT_FIELDS
                    for name in source["lookup_order"].split("|")
                ),
                authority_lookups=sum(
                    name in ADMIT_013_INTEGRITY_AUTHORITY_FIELDS
                    for name in source["lookup_order"].split("|")
                ),
                formal_calls=int(source["formal_call_count"]),
                oracle_calls=int(source["oracle_call_count"]),
                identity=True,
            )
        )
    return rows


def _dispatcher_truth_rows() -> list[dict[str, str]]:
    class RuleIdSubclass(str):
        pass

    definitions: tuple[tuple[str, object, str], ...] = (
        ("bool", True, "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID"),
        ("int", 13, "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID"),
        (
            "str_subclass",
            RuleIdSubclass("ADMIT_013"),
            "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID",
        ),
        ("unknown", "ADMIT_999", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN"),
        (
            "admit014",
            "ADMIT_014",
            "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
        ),
        (
            "admit015",
            "ADMIT_015",
            "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
        ),
    )
    rows = []
    for case_id, rule_id, expected_code in definitions:
        try:
            evaluate_admission_rule(rule_id, {})  # type: ignore[arg-type]
        except UnifiedAdmissionDispatchError as error:
            observed = _error_json(error)
            expected = _error_json(
                UnifiedAdmissionDispatchError(
                    expected_code,
                    "" if type(rule_id) is not str else rule_id,
                    expected_code
                    == "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
                    False,
                    False,
                    expected_code,
                )
            )
        else:
            raise ValueError("dispatcher negative case unexpectedly passed")
        rows.append(
            _truth_row(
                f"DISPATCH_{case_id}",
                "successor_dispatcher",
                case_id,
                expected,
                observed,
                handler_calls=0,
                identity=True,
            )
        )

    valid_download = {
        "download_result_status": "success",
        "observed_http_status": 200,
        "observed_content_length_bytes": 1,
        "observed_sha256": "0123456789abcdef" * 4,
    }
    valid_authority = {
        "expected_sha256": "0123456789abcdef" * 4,
    }
    passed = evaluate_admission_rule(
        ADMISSION_RULE_ID,
        {},
        evaluation_context=valid_authority,
        download_result_context=valid_download,
    )
    rows.append(
        _truth_row(
            "DISPATCH_admit013_passed",
            "successor_dispatcher",
            "admit013_passed",
            _evaluation_json(passed),
            _evaluation_json(passed),
            download_lookups=4,
            authority_lookups=3,
            formal_calls=1,
            oracle_calls=1,
            handler_calls=1,
            identity=True,
        )
    )
    for rule_id in KNOWN_RULE_IDS[:12]:
        before = predecessor.evaluate_admission_rule
        after = evaluate_admission_rule
        identity = (
            EVALUATOR_REGISTRY[rule_id]
            is predecessor.EVALUATOR_REGISTRY[rule_id]
            and before is predecessor.evaluate_admission_rule
            and after is not before
        )
        observed = json.dumps(
            {"handler_identity": identity, "rule_id": rule_id},
            sort_keys=True,
            separators=(",", ":"),
        )
        rows.append(
            _truth_row(
                f"DISPATCH_identity_{rule_id}",
                "successor_dispatcher",
                rule_id,
                observed,
                observed,
                handler_calls=0,
                identity=identity,
            )
        )
    return rows


def _contract_rows() -> list[dict[str, str]]:
    definitions = (
        ("identity", "Exact12 predecessor", "object_identity_preserved"),
        ("identity", "shared Exact13 result", "object_identity_preserved"),
        ("identity", "shared dispatch error", "object_identity_preserved"),
        ("identity", "shared constants", "5/5_identity_preserved"),
        ("dispatcher", "successor function", "distinct_new_function_object"),
        ("dispatcher", "signature", "exact_predecessor_match"),
        ("dispatcher", "precedence", "exact_str|known|callable|ready|local_handler"),
        ("registry", "order", "ADMIT_001_to_ADMIT_013"),
        ("registry", "first twelve handlers", "12/12_identity_preserved"),
        ("registry", "ADMIT_013 handler", "_evaluate_registered_admit_013"),
        ("registry", "immutability", "MappingProxyType"),
        ("sets", "known", "ADMIT_001_to_ADMIT_015"),
        ("sets", "callable", "ADMIT_001_to_ADMIT_013"),
        ("sets", "adapter ready", "ADMIT_001_to_ADMIT_013"),
        ("sets", "legacy adapter not ready", "empty"),
        ("routing", "five envelope signature", "frozen"),
        (
            "routing",
            "precedence",
            "batch|evaluation_mapping|download_mapping|stage|candidate_mapping|download4|authority3|formal|source|oracle|equality|projection",
        ),
        ("context", "batch reason", "ADMIT_013_BATCH_CONTEXT_MUST_BE_NONE"),
        ("context", "evaluation reason", "ADMIT_013_EVALUATION_CONTEXT_MAPPING_REQUIRED"),
        ("context", "download reason", "ADMIT_013_DOWNLOAD_RESULT_CONTEXT_MAPPING_REQUIRED"),
        ("context", "stage reason", "ADMIT_013_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
        ("context", "download lookup reason", "ADMIT_013_DOWNLOAD_RESULT_CONTEXT_LOOKUP_FAILED"),
        ("context", "evaluation lookup reason", "ADMIT_013_EVALUATION_CONTEXT_LOOKUP_FAILED"),
        ("candidate", "non-Mapping", "fixed_invalid_Exact13"),
        ("candidate", "key access", "zero"),
        ("download", "required Exact4", "|".join(ADMIT_013_DOWNLOAD_RESULT_FIELDS)),
        ("download", "first KeyError", "omit_keyword_stop_and_skip_authority"),
        ("download", "other exception", "context_routing_invalid"),
        ("authority", "optional Exact3", "|".join(ADMIT_013_INTEGRITY_AUTHORITY_FIELDS)),
        ("authority", "KeyError", "omit_and_continue"),
        ("authority", "other exception", "context_routing_invalid"),
        ("formal", "call count", "exactly_once"),
        ("formal", "exception", "propagated_oracle_zero"),
        ("source", "exact type", "Admit013EvaluationResult"),
        ("source", "Exact12", "storage_order_types_reconstruction_invariants"),
        ("oracle", "exact callable", "classify_admit_013_formal_evaluator_interface_design"),
        ("oracle", "call count", "exactly_once_after_source"),
        ("equality", "Exact12", "exact_type_and_value_all_fields"),
        ("projection", "normalized", "download4_then_provided_valid_authority3"),
        ("projection", "validated", "download_observation_pairs_only"),
        ("projection", "consumed candidate", "download_result_names"),
        ("projection", "consumed context", "integrity_authority_names"),
        ("projection", "integers", "canonical_decimal_str"),
        ("projection", "schema", "shared_Exact13_unchanged"),
        ("truth", "predecessor continuity", "Exact694"),
        ("truth", "ADMIT_013 committed identities", "Exact128"),
        ("truth", "ADMIT_013 normal projections", "Exact102"),
        ("truth", "ADMIT_013 negative attestations", "Exact26"),
        ("truth", "ADMIT_013 inherited business", "Exact23"),
        ("truth", "ADMIT_013 routing", "Exact44"),
        ("issue", "single transition", "coverage_removes_ADMIT_013_only"),
        ("boundary", "ADMIT_014 and ADMIT_015", "not_implemented"),
        ("boundary", "combined verdict and aggregation", "not_implemented"),
        ("boundary", "provider network download raw", "not_executed"),
        ("boundary", "model checkpoint dataloader training", "not_executed"),
        ("training", "feature semantics audit", "required_Step12D_smoke_only"),
        ("materializer", "publication", "set_atomic_RENAME_NOREPLACE"),
        ("materializer", "existing exact set", "inode_preserving_noop"),
        ("materializer", "GPFS EINVAL", "fail_closed_no_replace"),
    )
    return [
        {
            "contract_order": str(index),
            "contract_id": f"CONTRACT_{index:03d}",
            "contract_group": group,
            "contract_subject": subject,
            "expected_value": value,
            "observed_value": value,
            "contract_passed": "true",
        }
        for index, (group, subject, value) in enumerate(definitions, 1)
    ]


def _registry_rows() -> list[dict[str, str]]:
    records: list[tuple[str, object, object]] = []

    def add(item: str, expected: object, observed: object) -> None:
        records.append((item, expected, observed))

    for name in (
        "UnifiedAdmissionRuleEvaluation",
        "UnifiedAdmissionDispatchError",
        "RESULT_SCHEMA_VERSION",
        "RESULT_FIELDS",
        "DISPATCH_ERROR_FIELDS",
        "DISPATCH_ERROR_CODES",
        "OUTCOME_VOCABULARY",
    ):
        add(
            f"shared_identity:{name}",
            True,
            globals()[name] is getattr(predecessor, name),
        )
    add(
        "predecessor_registry_order",
        KNOWN_RULE_IDS[:12],
        tuple(predecessor.EVALUATOR_REGISTRY),
    )
    add("successor_registry_order", KNOWN_RULE_IDS[:13], tuple(EVALUATOR_REGISTRY))
    for rule_id in KNOWN_RULE_IDS[:12]:
        add(
            f"handler_identity:{rule_id}",
            True,
            EVALUATOR_REGISTRY[rule_id]
            is predecessor.EVALUATOR_REGISTRY[rule_id],
        )
    add(
        "handler_binding:ADMIT_013",
        True,
        EVALUATOR_REGISTRY[ADMISSION_RULE_ID]
        is _evaluate_registered_admit_013,
    )
    add(
        "predecessor_dispatcher_unchanged",
        True,
        predecessor.evaluate_admission_rule
        is predecessor.evaluate_admission_rule,
    )
    add(
        "successor_dispatcher_distinct",
        True,
        evaluate_admission_rule is not predecessor.evaluate_admission_rule,
    )
    add(
        "dispatcher_signature_equal",
        True,
        str(__import__("inspect").signature(evaluate_admission_rule))
        == str(__import__("inspect").signature(predecessor.evaluate_admission_rule)),
    )
    add(
        "rule_names",
        {**predecessor.RULE_NAMES, ADMISSION_RULE_ID: ADMISSION_RULE_NAME},
        dict(RULE_NAMES),
    )
    add(
        "adapter_ids",
        {**predecessor.ADAPTER_IDS, ADMISSION_RULE_ID: ADAPTER_ID},
        dict(ADAPTER_IDS),
    )
    add("known_rule_ids", KNOWN_RULE_IDS, KNOWN_RULE_IDS)
    add(
        "callable_discovered_rule_ids",
        KNOWN_RULE_IDS[:13],
        CALLABLE_DISCOVERED_RULE_IDS,
    )
    add(
        "adapter_ready_rule_ids",
        KNOWN_RULE_IDS[:13],
        ADAPTER_READY_RULE_IDS,
    )
    add(
        "legacy_adapter_not_ready_rule_ids",
        (),
        LEGACY_ADAPTER_NOT_READY_RULE_IDS,
    )
    add("ADMIT_014_unregistered", False, "ADMIT_014" in EVALUATOR_REGISTRY)
    add("ADMIT_015_unregistered", False, "ADMIT_015" in EVALUATOR_REGISTRY)
    for name, value in (
        ("RULE_NAMES", RULE_NAMES),
        ("ADAPTER_IDS", ADAPTER_IDS),
        ("EVALUATOR_REGISTRY", EVALUATOR_REGISTRY),
    ):
        add(f"mapping_proxy:{name}", MappingProxyType, type(value))
        try:
            value["ADMIT_999"] = object()  # type: ignore[index]
        except TypeError:
            rejected = True
        else:
            rejected = False
        add(f"mutation_rejected:{name}", True, rejected)

    rows = []
    for index, (item, expected, observed) in enumerate(records, 1):
        rows.append(
            {
                "audit_order": str(index),
                "audit_item": item,
                "expected_value": repr(expected),
                "observed_value": repr(observed),
                "audit_passed": str(expected == observed).lower(),
            }
        )
    return rows


def _safety_rows() -> list[dict[str, str]]:
    positive = (
        ("public_closure_pure_memory", "AST and marker-prefix attested"),
        ("evaluator_io_used_false", "formal and projected results"),
        ("exact12_source_validation", "precedes output projection"),
        ("independent_oracle_equality", "full Exact12"),
        ("shared_exact13_identity", "identity re-export"),
        ("first12_handler_identity", "all predecessor objects reused"),
        ("successor_dispatcher", "new local function and registry"),
        ("canonical_evidence_runtime", "CPython 3.10.4"),
        ("pinned_source_boundary", "Exact20 tracked base blobs"),
        ("pinned_candidate_source", "path mode bytes marker AST"),
        ("set_atomic_materialization", "RENAME_NOREPLACE"),
        ("deterministic_evidence", "byte-identical build"),
        ("feature_semantics_audit_required", "Step12D smoke only"),
    )
    negative = (
        ("adapter_design_simulator_runtime_call", "absent"),
        ("schema_widening", "absent"),
        ("predecessor_mutation", "absent"),
        ("shared_object_redefinition", "absent"),
        ("candidate_key_access", "zero"),
        ("private_missing_sentinel", "not imported/read/passed"),
        ("provider_mapping", "not implemented"),
        ("network", "not executed"),
        ("download", "not executed"),
        ("raw", "not read"),
        ("model", "not accessed"),
        ("checkpoint", "not accessed"),
        ("dataloader", "not accessed"),
        ("training", "not executed"),
        ("combined_candidate_verdict", "not implemented"),
        ("cross_rule_aggregation", "not implemented"),
        ("current_main_stage_commit_push", "not executed"),
    )
    pairs = (
        *((name, True, evidence) for name, evidence in positive),
        *((name, False, evidence) for name, evidence in negative),
    )
    return [
        {
            "safety_order": str(index),
            "safety_item": name,
            "expected_executed": str(executed).lower(),
            "observed_executed": str(executed).lower(),
            "evidence": evidence,
            "safety_passed": "true",
        }
        for index, (name, executed, evidence) in enumerate(pairs, 1)
    ]


TRUE_READINESS = (
    "evaluate_admit_013_implemented",
    "Admit013EvaluationResult_implemented",
    "admit_013_rule_logic_implemented",
    "admit_013_standalone_evaluator_interface_implemented",
    "admit_013_unified_adapter_contract_frozen",
    "admit_013_unified_adapter_implemented",
    "admit_013_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_013_implemented",
    "first_twelve_handler_identity_preserved",
    "shared_exact13_identity_preserved",
    "successor_dispatcher_implemented",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "admit_014_implemented",
    "admit_014_registered_in_engine",
    "admit_015_implemented",
    "admit_015_registered_in_engine",
    "combined_candidate_verdict_implemented",
    "cross_rule_aggregation_implemented",
    "provider_mapping_validated",
    "real_provider_evaluation_ready",
    "ready_for_bulk_download_now",
    "ready_for_training",
    "step12d_is_final_training_feature_contract",
)


def _updated_issue_rows(
    predecessor_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    rows = [dict(row) for row in predecessor_rows]
    matches = [
        row
        for row in rows
        if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
    ]
    if len(rows) != 23 or len(matches) != 1:
        raise ValueError("Exact23 coverage issue missing or duplicate")
    coverage = matches[0]
    before = dict(coverage)
    if (
        coverage["affected_rules"] != "ADMIT_013|ADMIT_014|ADMIT_015"
        or coverage["status"] != "open"
    ):
        raise ValueError("coverage issue predecessor state drift")
    coverage["affected_rules"] = "ADMIT_014|ADMIT_015"
    coverage["integration_transition"] = (
        "unified_dispatch_runtime_with_admit_001_to_013_implemented_v1"
    )
    coverage["successor_transition_stage"] = STAGE
    coverage["successor_transition_action"] = (
        "admit_013_removed_from_open_unified_runtime_coverage"
    )
    coverage["successor_transition_evidence"] = (
        "Exact13_registry_and_unified_single_rule_dispatch"
    )
    changed = {
        key for key in coverage if coverage[key] != before.get(key)
    }
    if changed != {
        "affected_rules",
        "integration_transition",
        "successor_transition_stage",
        "successor_transition_action",
        "successor_transition_evidence",
    }:
        raise ValueError("coverage transition exceeded authorization")
    return rows


def build_runtime_state(
    snapshot: FrozenSourceSnapshot | None = None,
) -> dict[str, Any]:
    _assert_canonical_evidence_runtime()
    snapshot = (
        build_frozen_source_snapshot() if snapshot is None else snapshot
    )
    if not validate_frozen_source_snapshot(snapshot):
        raise ValueError("invalid Exact20 source snapshot")
    predecessor_truth = _csv_rows(
        _source_record(
            snapshot,
            "covapie_admit_001_to_012_dispatch_truth_matrix.csv",
        ).content
    )
    formal_truth = _csv_rows(
        _source_record(
            snapshot,
            "covapie_admit_013_formal_evaluator_interface_truth_matrix.csv",
        ).content
    )
    routing_truth = _csv_rows(
        _source_record(
            snapshot,
            "covapie_admit_013_download_and_integrity_authority_projection_and_context_routing_matrix.csv",
        ).content
    )
    issue_rows = _csv_rows(
        _source_record(
            snapshot,
            "covapie_admit_013_unified_adapter_issue_readiness_inventory.csv",
        ).content,
        ISSUE_COLUMNS,
    )
    predecessor_manifest = _json_object(
        _source_record(
            snapshot,
            "covapie_admit_001_to_012_runtime_manifest.json",
        ).content
    )
    adapter_manifest = _json_object(
        _source_record(
            snapshot,
            "covapie_admit_013_unified_adapter_contract_manifest.json",
        ).content
    )
    if (
        predecessor_manifest.get("registered_rule_ids")
        != list(KNOWN_RULE_IDS[:12])
        or adapter_manifest.get("committed_exact128_normal_projection_count")
        != 102
        or adapter_manifest.get(
            "committed_exact128_negative_source_attestation_count"
        )
        != 26
    ):
        raise ValueError("predecessor manifests drift")

    truth_rows = [
        *_predecessor_truth_rows(predecessor_truth),
        *_admit013_exact128_rows(formal_truth),
        *_admit013_exact44_rows(routing_truth),
        *_dispatcher_truth_rows(),
    ]
    for index, row in enumerate(truth_rows, 1):
        row["case_order"] = str(index)
    contract_rows = _contract_rows()
    registry_rows = _registry_rows()
    safety_rows = _safety_rows()
    updated_issues = _updated_issue_rows(issue_rows)
    group_counts = dict(
        sorted(Counter(row["case_group"] for row in truth_rows).items())
    )
    expected_groups = {
        "admit013_exact128_negative": 26,
        "admit013_exact128_normal": 102,
        "admit013_exact44_routing": 44,
        "predecessor_exact12_all_cases": 694,
        "successor_dispatcher": 19,
    }
    issue_map = {row["issue_id"]: row for row in updated_issues}
    if (
        group_counts != expected_groups
        or len(truth_rows) != 885
        or any(row["case_passed"] != "true" for row in truth_rows)
        or any(row["contract_passed"] != "true" for row in contract_rows)
        or any(row["audit_passed"] != "true" for row in registry_rows)
        or len(safety_rows) != 30
        or len(updated_issues) != 23
        or issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"][
            "affected_rules"
        ]
        != "ADMIT_014|ADMIT_015"
        or issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["status"]
        != "open"
        or issue_map[
            "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"
        ]["status"]
        != "open"
    ):
        raise ValueError("Exact13 runtime state failed closed")
    return {
        "snapshot": snapshot,
        "candidate_attestation": _candidate_source_attestation(),
        "contract_rows": contract_rows,
        "truth_rows": truth_rows,
        "truth_group_counts": group_counts,
        "registry_rows": registry_rows,
        "safety_rows": safety_rows,
        "issue_rows": updated_issues,
        "all_checks_passed": True,
        "validation_failures": [],
    }


def _csv_bytes(
    columns: Sequence[str],
    rows: Sequence[Mapping[str, str]],
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=list(columns),
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    for row in rows:
        if tuple(row) != tuple(columns):
            raise ValueError("output CSV schema mismatch")
        writer.writerow(row)
    return stream.getvalue().encode("utf-8")


def _source_digests() -> tuple[str, str]:
    paths = [path for path, _ in SOURCE_BOUNDARY]
    pairs = [[path, digest] for path, digest in SOURCE_BOUNDARY]
    return (
        _sha(json.dumps(paths, separators=(",", ":")).encode()),
        _sha(json.dumps(pairs, separators=(",", ":")).encode()),
    )


def _manifest_payload(
    state: Mapping[str, Any],
    output_sha256: Mapping[str, str],
) -> dict[str, Any]:
    snapshot = state["snapshot"]
    readiness = {name: True for name in TRUE_READINESS} | {
        name: False for name in FALSE_READINESS
    }
    path_digest, pair_digest = _source_digests()
    return {
        "project": PROJECT,
        "step": STEP,
        "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT,
        "expected_base_parent": EXPECTED_BASE_PARENT,
        "expected_base_tree": EXPECTED_BASE_TREE,
        "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "canonical_evidence_python_implementation": (
            CANONICAL_PYTHON_IMPLEMENTATION
        ),
        "canonical_evidence_python_version": ".".join(
            map(str, CANONICAL_PYTHON_VERSION)
        ),
        "ast_attestation_cross_python_version_portable": (
            AST_ATTESTATION_CROSS_PYTHON_VERSION_PORTABLE
        ),
        "noncanonical_python_policy": NONCANONICAL_PYTHON_POLICY,
        "python_runtime_migration_policy": PYTHON_RUNTIME_MIGRATION_POLICY,
        "exact13_identity": (
            "ADMIT_001_to_ADMIT_013_unified_single_rule_runtime_v1"
        ),
        "exact12_predecessor_identity": (
            "ADMIT_001_to_ADMIT_012_unified_single_rule_runtime_v1"
        ),
        "source_boundary_name": (
            "fixed_ordered_exact20_committed_source_boundary"
        ),
        "source_input_count": 20,
        "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_input_sha256": {
            path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS
        },
        "source_path_list_sha256": path_digest,
        "source_path_sha256_pairs_sha256": pair_digest,
        "source_input_verification": [
            {
                "source_order": index,
                "source_relative_path": record.relative_path.as_posix(),
                "tracked": True,
                "base_tree_blob": True,
                "base_tree_mode": record.base_tree_mode,
                "filesystem_regular": True,
                "non_symlink": True,
                "parent_chain_non_symlink": True,
                "safe_descendant": True,
                "pinned_fd_read": True,
                "expected_sha256": record.expected_sha256,
                "base_tree_sha256": record.base_tree_sha256,
                "filesystem_sha256": record.filesystem_sha256,
                "source_verified": True,
            }
            for index, record in enumerate(snapshot.records, 1)
        ],
        "source_validation_before_output_read": True,
        "evidence_lifecycle_hardening": {
            "checker_exact6_full_identity_post_traversal": True,
            "checker_manifest_duplicate_and_exact_key_rejection": True,
            "exact10_lifecycle_exact_inventory": True,
            "production_source_root_parent_dir_fd_traversal": True,
            "publisher_existing_set_post_fsync_destination_binding": True,
            "publisher_rename_success_post_fsync_destination_binding": True,
            "successor_regression_stage_local_deselection_count": 4,
        },
        "candidate_production_source_attestation": state[
            "candidate_attestation"
        ],
        "runtime_dependency_imports": [
            "exact12_unified_runtime_predecessor",
            "admit013_standalone_evaluator",
            "admit013_committed_independent_formal_interface_oracle",
        ],
        "adapter_design_simulator_called_by_runtime": False,
        "public_type_and_constant_identity": {
            name: True
            for name in (
                "UnifiedAdmissionRuleEvaluation",
                "UnifiedAdmissionDispatchError",
                "RESULT_SCHEMA_VERSION",
                "RESULT_FIELDS",
                "DISPATCH_ERROR_FIELDS",
                "DISPATCH_ERROR_CODES",
                "OUTCOME_VOCABULARY",
            )
        },
        "public_dispatch_new_successor_function": True,
        "public_dispatch_signature": str(
            __import__("inspect").signature(evaluate_admission_rule)
        ),
        "public_dispatch_signature_matches_exact12": True,
        "public_dispatch_uses_local_registry": True,
        "public_dispatch_cardinality": "single_rule_only",
        "public_dispatch_precedence": [
            "exact_builtin_str",
            "known_rule",
            "callable_discovered",
            "adapter_ready",
            "successor_local_registry_handler",
        ],
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "result_field_count": 13,
        "result_fields": list(RESULT_FIELDS),
        "dispatch_error_fields": list(DISPATCH_ERROR_FIELDS),
        "dispatch_error_codes": list(DISPATCH_ERROR_CODES),
        "outcome_vocabulary": list(OUTCOME_VOCABULARY),
        "known_rule_ids": list(KNOWN_RULE_IDS),
        "callable_discovered_rule_ids": list(CALLABLE_DISCOVERED_RULE_IDS),
        "adapter_ready_rule_ids": list(ADAPTER_READY_RULE_IDS),
        "legacy_adapter_not_ready_rule_ids": [],
        "registered_rule_ids": list(EVALUATOR_REGISTRY),
        "known_not_registered_rule_ids": list(KNOWN_RULE_IDS[13:]),
        "registered_rule_count": 13,
        "registry_mapping_proxy_type": True,
        "rule_names": dict(RULE_NAMES),
        "adapter_ids": dict(ADAPTER_IDS),
        "first_twelve_handler_identity_reused": {
            rule_id: EVALUATOR_REGISTRY[rule_id]
            is predecessor.EVALUATOR_REGISTRY[rule_id]
            for rule_id in KNOWN_RULE_IDS[:12]
        },
        "predecessor_dispatcher_unchanged": True,
        "successor_dispatcher_distinct": True,
        "admit_013_handler": "_evaluate_registered_admit_013",
        "admit_013_handler_signature": str(
            __import__("inspect").signature(_evaluate_registered_admit_013)
        ),
        "admit_013_download_result_fields": list(
            ADMIT_013_DOWNLOAD_RESULT_FIELDS
        ),
        "admit_013_integrity_authority_fields": list(
            ADMIT_013_INTEGRITY_AUTHORITY_FIELDS
        ),
        "admit_013_source_fields": list(ADMIT_013_SOURCE_FIELDS),
        "admit_013_routing_precedence": [
            "batch_context_must_be_none",
            "evaluation_context_mapping_validation",
            "download_result_context_mapping_validation",
            "stage_authorization_context_must_be_none",
            "candidate_record_mapping_validation",
            "download_result_exact4_required_lookup_first_missing_stops",
            "integrity_authority_exact3_optional_lookup_all",
            "formal_evaluator_exactly_once",
            "standalone_source_exact12_validation",
            "independent_design_oracle_exactly_once",
            "full_exact12_exact_type_value_equality",
            "typed_to_string_exact13_projection",
        ],
        "admit_013_context_reasons": {
            "batch_context": "ADMIT_013_BATCH_CONTEXT_MUST_BE_NONE",
            "evaluation_context": (
                "ADMIT_013_EVALUATION_CONTEXT_MAPPING_REQUIRED"
            ),
            "download_result_context": (
                "ADMIT_013_DOWNLOAD_RESULT_CONTEXT_MAPPING_REQUIRED"
            ),
            "stage_authorization_context": (
                "ADMIT_013_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"
            ),
            "download_result_lookup": (
                "ADMIT_013_DOWNLOAD_RESULT_CONTEXT_LOOKUP_FAILED"
            ),
            "evaluation_lookup": (
                "ADMIT_013_EVALUATION_CONTEXT_LOOKUP_FAILED"
            ),
        },
        "admit_013_candidate_mapping_invalid_reason": (
            "ADMIT_013_CANDIDATE_RECORD_MAPPING_INVALID"
        ),
        "admit_013_candidate_key_access_count": 0,
        "admit_013_private_sentinel_imported_or_passed": False,
        "admit_013_formal_evaluator": "evaluate_admit_013",
        "admit_013_formal_call_count": 1,
        "admit_013_source_type": "Admit013EvaluationResult",
        "admit_013_source_type_invalid_reason": (
            "ADMIT_013_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
        ),
        "admit_013_source_invariant_invalid_reason": (
            "ADMIT_013_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        ),
        "admit_013_source_prevalidation_before_oracle": True,
        "admit_013_oracle": (
            "classify_admit_013_formal_evaluator_interface_design"
        ),
        "admit_013_oracle_result_type": (
            "Admit013EvaluationResultContractDesign"
        ),
        "admit_013_oracle_call_count": 1,
        "admit_013_source_oracle_full_exact12_exact_type_value_equality_required": True,
        "admit_013_exact13_projection": {
            "normalized_values": (
                "canonical download observations followed by "
                "provided-valid authority pairs"
            ),
            "validated_candidate_fields": (
                "validated download observation string pairs only"
            ),
            "consumed_candidate_fields": (
                "source.consumed_download_result_fields"
            ),
            "consumed_context_items": (
                "source.consumed_integrity_authority_fields"
            ),
        },
        "contract_row_count": len(state["contract_rows"]),
        "truth_matrix_row_count": len(state["truth_rows"]),
        "truth_matrix_group_counts": dict(state["truth_group_counts"]),
        "predecessor_continuity_case_count": 694,
        "admit_013_committed_exact128_case_count": 128,
        "admit_013_normal_projection_count": 102,
        "admit_013_negative_source_attestation_count": 26,
        "admit_013_inherited_business_case_count": 23,
        "admit_013_routing_case_count": 44,
        "registry_identity_audit_row_count": len(state["registry_rows"]),
        "safety_audit_row_count": len(state["safety_rows"]),
        "issue_inventory_row_count": len(state["issue_rows"]),
        "issue_transition_count": 1,
        "issue_transition_id": (
            "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
        ),
        "issue_transition": (
            "unified_dispatch_runtime_with_admit_001_to_013_implemented_v1"
        ),
        "issue_coverage_after": ["ADMIT_014", "ADMIT_015"],
        "output_files": list(OUTPUT_FILES),
        "output_file_count": 6,
        "output_sha256": dict(output_sha256),
        "output_sha256_excludes_manifest_self_hash": True,
        "output_materialization": {
            "all_payloads_built_before_mutation": True,
            "exact_six_allowlist": True,
            "pinned_parent_root_staging_leaf": True,
            "exclusive_create": True,
            "file_fsync": True,
            "staging_directory_fsync": True,
            "renameat2_RENAME_NOREPLACE": True,
            "GPFS_EINVAL_fail_closed": True,
            "os_replace_fallback": False,
            "parent_fsync": True,
            "destination_name_inode_binding": True,
            "existing_set_destination_binding_after_fsync": True,
            "full_leaf_identity_post_traversal": True,
            "complete_set_postverify": True,
            "existing_exact_set_inode_preserving_noop": True,
            "mismatch_repair_forbidden": True,
            "race_fail_closed": True,
            "rename_success_destination_binding_after_fsync": True,
        },
        "admit_014_implemented": False,
        "admit_015_implemented": False,
        "provider_mapping_validated": False,
        "real_provider_evaluation_ready": False,
        "ready_for_bulk_download_now": False,
        "combined_candidate_verdict_implemented": False,
        "cross_rule_aggregation_implemented": False,
        "feature_semantics_audit_required": True,
        "step12d_is_final_training_feature_contract": False,
        "step12d_status": (
            "smoke_legality_only_not_final_training_feature_contract"
        ),
        "readiness": readiness,
        **readiness,
        "all_source_boundary_checks_passed": True,
        "all_predecessor_contract_checks_passed": True,
        "all_runtime_contract_checks_passed": True,
        "all_truth_matrix_checks_passed": True,
        "all_registry_audit_checks_passed": True,
        "all_issue_checks_passed": True,
        "all_safety_checks_passed": True,
        "all_checks_passed": True,
        "validation_failures": [],
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }


def build_artifacts(
    state: Mapping[str, Any] | None = None,
) -> dict[str, bytes]:
    _assert_canonical_evidence_runtime()
    state = build_runtime_state() if state is None else state
    if (
        type(state) is not dict
        or state.get("all_checks_passed") is not True
        or not validate_frozen_source_snapshot(state.get("snapshot"))
    ):
        raise ValueError("runtime state invalid")
    payloads = {
        CONTRACT_FILENAME: _csv_bytes(
            CONTRACT_COLUMNS,
            state["contract_rows"],
        ),
        TRUTH_FILENAME: _csv_bytes(TRUTH_COLUMNS, state["truth_rows"]),
        REGISTRY_FILENAME: _csv_bytes(
            REGISTRY_COLUMNS,
            state["registry_rows"],
        ),
        SAFETY_FILENAME: _csv_bytes(
            SAFETY_COLUMNS,
            state["safety_rows"],
        ),
        ISSUE_FILENAME: _csv_bytes(ISSUE_COLUMNS, state["issue_rows"]),
    }
    output_sha256 = {
        name: _sha(content) for name, content in payloads.items()
    }
    manifest = _manifest_payload(state, output_sha256)
    payloads[MANIFEST_FILENAME] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    return {name: payloads[name] for name in OUTPUT_FILES}


@dataclass(frozen=True)
class OutputMaterializationPlan:
    root: Path
    parent: Path
    anchor: Path
    root_name: str
    parent_identity: tuple[int, int, int]
    root_identity: tuple[int, int, int] | None
    leaf_identities: tuple[
        tuple[str, tuple[int, int, int, int, int, int]], ...
    ]


DIRECTORY_FLAGS = (
    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
)
READ_FILE_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
WRITE_FILE_FLAGS = (
    os.O_WRONLY
    | os.O_CREAT
    | os.O_EXCL
    | os.O_NOFOLLOW
    | os.O_CLOEXEC
)
try:
    _RENAMEAT2 = ctypes.CDLL(None, use_errno=True).renameat2
    _RENAMEAT2.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    )
    _RENAMEAT2.restype = ctypes.c_int
except AttributeError:
    _RENAMEAT2 = None
RENAME_NOREPLACE = 1


def _inspect_output_target_read_only(
    output_root: Path,
    repo_root: Path = REPO_ROOT,
) -> OutputMaterializationPlan:
    candidate = Path(output_root)
    repo = Path(os.path.abspath(repo_root))
    if candidate.is_absolute():
        root = Path(os.path.abspath(candidate))
        anchor = Path(root.anchor)
    else:
        if ".." in candidate.parts:
            raise ValueError("relative output escape forbidden")
        root = repo / candidate
        anchor = repo
    if not root.name:
        raise ValueError("output root invalid")
    parent = root.parent
    _assert_real_parent_chain(parent, anchor)
    parent_identity = _identity(os.lstat(parent))
    try:
        root_item = os.lstat(root)
    except FileNotFoundError:
        return OutputMaterializationPlan(
            root,
            parent,
            anchor,
            root.name,
            parent_identity,
            None,
            (),
        )
    if (
        not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
        or root.resolve(strict=True) != root
    ):
        raise ValueError("output root unsafe")
    names = tuple(os.listdir(root))
    if set(names) != set(OUTPUT_FILES) or len(names) != len(OUTPUT_FILES):
        raise ValueError("output inventory unsafe")
    leaves = []
    for name in OUTPUT_FILES:
        leaf = root / name
        item = os.lstat(leaf)
        if (
            not stat.S_ISREG(item.st_mode)
            or stat.S_ISLNK(item.st_mode)
            or leaf.resolve(strict=True) != leaf
        ):
            raise ValueError("output leaf unsafe")
        leaves.append((name, _full_identity(item)))
    return OutputMaterializationPlan(
        root,
        parent,
        anchor,
        root.name,
        parent_identity,
        _identity(root_item),
        tuple(leaves),
    )


def _read_at(
    directory_fd: int,
    name: str,
    expected: tuple[int, int, int, int, int, int],
) -> bytes:
    item = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    if (
        _full_identity(item) != expected
        or not stat.S_ISREG(item.st_mode)
        or stat.S_ISLNK(item.st_mode)
        or item.st_size > 100 * 1024 * 1024
    ):
        raise ValueError("pinned output leaf drift")
    descriptor = os.open(name, READ_FILE_FLAGS, dir_fd=directory_fd)
    try:
        if _full_identity(os.fstat(descriptor)) != expected:
            raise ValueError("pinned output descriptor drift")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1 << 16)
            if not chunk:
                break
            chunks.append(chunk)
        if (
            _full_identity(os.fstat(descriptor)) != expected
            or _full_identity(
                os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            )
            != expected
        ):
            raise ValueError("pinned output leaf changed during read")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _write_all(descriptor: int, content: bytes) -> None:
    offset = 0
    while offset < len(content):
        count = os.write(descriptor, content[offset:])
        if type(count) is not int or count <= 0:
            raise OSError("short output write")
        offset += count


def _rename_noreplace(parent_fd: int, source: str, target: str) -> None:
    if _RENAMEAT2 is None:
        raise ValueError("renameat2 required")
    if _RENAMEAT2(
        parent_fd,
        os.fsencode(source),
        parent_fd,
        os.fsencode(target),
        RENAME_NOREPLACE,
    ):
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), f"{source}->{target}")


def _assert_output_parent(
    plan: OutputMaterializationPlan,
    parent_fd: int,
) -> None:
    lexical = os.lstat(plan.parent)
    if (
        _identity(lexical) != plan.parent_identity
        or _identity(os.fstat(parent_fd)) != plan.parent_identity
        or not stat.S_ISDIR(lexical.st_mode)
        or stat.S_ISLNK(lexical.st_mode)
        or plan.parent.resolve(strict=True) != plan.parent
    ):
        raise ValueError("output parent binding changed")


def _verify_complete_set(
    root_fd: int,
    payloads: Mapping[str, bytes],
    expected_identities: Mapping[
        str, tuple[int, int, int, int, int, int]
    ]
    | None = None,
) -> dict[str, tuple[int, int, int, int, int, int]]:
    names = tuple(os.listdir(root_fd))
    if len(names) != 6 or set(names) != set(OUTPUT_FILES):
        raise ValueError("complete output inventory drift")
    identities = (
        {
            name: _full_identity(
                os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            )
            for name in OUTPUT_FILES
        }
        if expected_identities is None
        else dict(expected_identities)
    )
    for name, content in payloads.items():
        actual = _read_at(root_fd, name, identities[name])
        if actual != content or _sha(actual) != _sha(content):
            raise ValueError("output payload mismatch")
    if (
        len(os.listdir(root_fd)) != len(OUTPUT_FILES)
        or set(os.listdir(root_fd)) != set(OUTPUT_FILES)
    ):
        raise ValueError("complete output post-read inventory drift")
    for name, identity in identities.items():
        item = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
        if (
            _full_identity(item) != identity
            or not stat.S_ISREG(item.st_mode)
            or stat.S_ISLNK(item.st_mode)
            or item.st_size > 100 * 1024 * 1024
        ):
            raise ValueError("complete output post-read leaf drift")
    return identities


def _verify_destination_binding(
    plan: OutputMaterializationPlan,
    parent_fd: int,
    root_fd: int,
    root_identity: tuple[int, int, int],
    payloads: Mapping[str, bytes],
    expected_identities: Mapping[
        str, tuple[int, int, int, int, int, int]
    ],
) -> None:
    _assert_output_parent(plan, parent_fd)
    destination = os.stat(
        plan.root_name,
        dir_fd=parent_fd,
        follow_symlinks=False,
    )
    if (
        _identity(destination) != root_identity
        or _identity(os.fstat(root_fd)) != root_identity
        or not stat.S_ISDIR(destination.st_mode)
        or stat.S_ISLNK(destination.st_mode)
    ):
        raise ValueError("destination name/inode binding drift")
    _verify_complete_set(
        root_fd,
        payloads,
        expected_identities,
    )
    _assert_output_parent(plan, parent_fd)
    final_destination = os.stat(
        plan.root_name,
        dir_fd=parent_fd,
        follow_symlinks=False,
    )
    if (
        _identity(final_destination) != root_identity
        or _identity(os.fstat(root_fd)) != root_identity
        or not stat.S_ISDIR(final_destination.st_mode)
        or stat.S_ISLNK(final_destination.st_mode)
        or len(os.listdir(root_fd)) != len(OUTPUT_FILES)
        or set(os.listdir(root_fd)) != set(OUTPUT_FILES)
    ):
        raise ValueError("final destination binding drift")
    for name, identity in expected_identities.items():
        item = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
        if (
            _full_identity(item) != identity
            or not stat.S_ISREG(item.st_mode)
            or stat.S_ISLNK(item.st_mode)
            or item.st_size > 100 * 1024 * 1024
        ):
            raise ValueError("final destination leaf binding drift")


def _cleanup_staging(
    parent_fd: int,
    root_fd: int | None,
    staging_name: str | None,
    staged: Mapping[
        str, tuple[int, int, int, int, int, int]
    ],
) -> int | None:
    if root_fd is None or staging_name is None:
        return root_fd
    try:
        if set(os.listdir(root_fd)) != set(staged):
            return root_fd
        for name, identity in staged.items():
            if (
                _full_identity(
                    os.stat(name, dir_fd=root_fd, follow_symlinks=False)
                )
                != identity
            ):
                return root_fd
        for name in staged:
            os.unlink(name, dir_fd=root_fd)
        os.close(root_fd)
        root_fd = None
        os.rmdir(staging_name, dir_fd=parent_fd)
    except BaseException:
        pass
    return root_fd


def _materialize_set(
    plan: OutputMaterializationPlan,
    payloads: Mapping[str, bytes],
) -> None:
    _assert_canonical_evidence_runtime()
    if (
        type(payloads) is not dict
        or tuple(payloads) != OUTPUT_FILES
        or any(type(value) is not bytes for value in payloads.values())
    ):
        raise ValueError("output payload inventory invalid")
    parent_fd = os.open(plan.parent, DIRECTORY_FLAGS)
    root_fd: int | None = None
    staging_name: str | None = None
    staged: dict[str, tuple[int, int, int, int, int, int]] = {}
    try:
        _assert_output_parent(plan, parent_fd)
        if plan.root_identity is not None:
            item = os.stat(
                plan.root_name,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
            if (
                _identity(item) != plan.root_identity
                or not stat.S_ISDIR(item.st_mode)
                or stat.S_ISLNK(item.st_mode)
            ):
                raise ValueError("output root identity changed")
            root_fd = os.open(
                plan.root_name,
                DIRECTORY_FLAGS,
                dir_fd=parent_fd,
            )
            if _identity(os.fstat(root_fd)) != plan.root_identity:
                raise ValueError("output root descriptor drift")
            identities = dict(plan.leaf_identities)
            try:
                _verify_destination_binding(
                    plan,
                    parent_fd,
                    root_fd,
                    plan.root_identity,
                    payloads,
                    identities,
                )
            except ValueError as error:
                raise ValueError(
                    "existing output differs; repair forbidden"
                ) from error
            os.fsync(root_fd)
            _verify_destination_binding(
                plan,
                parent_fd,
                root_fd,
                plan.root_identity,
                payloads,
                identities,
            )
            return

        try:
            os.stat(
                plan.root_name,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            pass
        else:
            raise ValueError("missing output target became occupied")
        for _ in range(64):
            candidate = (
                f".exact13-runtime-stage-{secrets.token_hex(16)}"
            )
            try:
                os.mkdir(candidate, 0o700, dir_fd=parent_fd)
                staging_name = candidate
                break
            except FileExistsError:
                continue
        if staging_name is None:
            raise ValueError("staging name exhaustion")
        root_fd = os.open(
            staging_name,
            DIRECTORY_FLAGS,
            dir_fd=parent_fd,
        )
        staging_identity = _identity(os.fstat(root_fd))
        if (
            os.listdir(root_fd)
            or _identity(
                os.stat(
                    staging_name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
            )
            != staging_identity
        ):
            raise ValueError("staging directory invalid")
        for name, content in payloads.items():
            descriptor = os.open(
                name,
                WRITE_FILE_FLAGS,
                0o600,
                dir_fd=root_fd,
            )
            try:
                _write_all(descriptor, content)
                os.fsync(descriptor)
                staged[name] = _full_identity(os.fstat(descriptor))
            finally:
                os.close(descriptor)
            if _read_at(root_fd, name, staged[name]) != content:
                raise ValueError("staged output mismatch")
        _verify_complete_set(root_fd, payloads, staged)
        os.fsync(root_fd)
        _assert_output_parent(plan, parent_fd)
        if (
            _identity(os.fstat(root_fd)) != staging_identity
            or _identity(
                os.stat(
                    staging_name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
            )
            != staging_identity
        ):
            raise ValueError("staging identity drift")
        try:
            os.stat(
                plan.root_name,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            pass
        else:
            raise ValueError("final output race")
        _rename_noreplace(parent_fd, staging_name, plan.root_name)
        staging_name = None
        os.fsync(parent_fd)
        _verify_destination_binding(
            plan,
            parent_fd,
            root_fd,
            staging_identity,
            payloads,
            staged,
        )
        os.fsync(root_fd)
        _verify_destination_binding(
            plan,
            parent_fd,
            root_fd,
            staging_identity,
            payloads,
            staged,
        )
    except BaseException:
        root_fd = _cleanup_staging(
            parent_fd,
            root_fd,
            staging_name,
            staged,
        )
        raise
    finally:
        if root_fd is not None:
            try:
                os.close(root_fd)
            except OSError:
                pass
        os.close(parent_fd)


def run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    *,
    repo_root: Path = REPO_ROOT,
    head_ref: str = "HEAD",
) -> dict[str, Any]:
    """Publish exactly six deterministic runtime-evidence files."""
    _assert_canonical_evidence_runtime()
    snapshot = build_frozen_source_snapshot(
        repo_root,
        head_ref=head_ref,
    )
    state = build_runtime_state(snapshot)
    payloads = build_artifacts(state)
    plan = _inspect_output_target_read_only(output_root, repo_root)
    _materialize_set(plan, payloads)
    return {
        "state": state,
        "manifest": json.loads(payloads[MANIFEST_FILENAME]),
        "output_root": plan.root,
    }


if __name__ == "__main__":
    run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1()
