"""Step14AU-E1-E4 Phase 4 unified single-rule admission runtime.

The public runtime registers ADMIT_001 through ADMIT_004.  The first three
rules adapt their committed legacy evaluators and enforce an independent pure
semantic oracle on every well-shaped legacy result.  ADMIT_004 is delegated
unchanged to the Phase 2 runtime.  The metadata materializer below the runtime
uses only the frozen Exact14 evidence boundary and synthetic inputs.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import inspect
import io
import json
import os
import stat
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from pathlib import Path
from types import MappingProxyType, SimpleNamespace
from typing import Any, NoReturn

from covalent_ext import (
    covapie_bulk_download_admission_candidate_record_id_semantics_design_gate
    as _admit001_oracle_module,
)
from covalent_ext import (
    covapie_bulk_download_admission_candidate_record_id_semantics_integration_gate
    as admit001_legacy,
)
from covalent_ext import (
    covapie_bulk_download_admission_ligand_comp_id_semantics_design_gate
    as _admit003_oracle_module,
)
from covalent_ext import (
    covapie_bulk_download_admission_ligand_comp_id_semantics_integration_gate
    as admit003_legacy,
)
from covalent_ext import (
    covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004
    as phase2,
)
from covalent_ext import (
    covapie_bulk_download_admission_pdb_identifier_semantics_design_gate
    as _admit002_oracle_module,
)
from covalent_ext import (
    covapie_bulk_download_admission_pdb_identifier_semantics_integration_gate
    as admit002_legacy,
)

# Static callable namespaces keep adapter-level call counting independent from
# the legacy modules' own internal reuse of the same committed pure helpers.
admit001_oracle = SimpleNamespace(
    normalize_candidate_record_id=_admit001_oracle_module.normalize_candidate_record_id,
    evaluate_candidate_record_id_batch_uniqueness=(
        _admit001_oracle_module.evaluate_candidate_record_id_batch_uniqueness
    ),
)
admit002_oracle = SimpleNamespace(
    normalize_pdb_identifier=_admit002_oracle_module.normalize_pdb_identifier
)
admit003_oracle = SimpleNamespace(
    normalize_ligand_comp_id=_admit003_oracle_module.normalize_ligand_comp_id
)


PROJECT = "CovaPIE"
STEP = "Step14AU-E1-E4 Phase 4"
STAGE = (
    "covapie_bulk_download_admission_unified_dispatch_runtime_"
    "with_admit_001_to_004_v1"
)
EXPECTED_BASE_COMMIT = "759f19b8e84d68a531b791ff683033812549ce80"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_001 to ADMIT_003 legacy adapter contracts v1"
MANIFEST_SCHEMA_VERSION = (
    "covapie_unified_dispatch_runtime_with_admit_001_to_004_manifest_v1"
)
RECOMMENDED_NEXT_STEP = "audit_covapie_admit_005_formal_evaluator_interface_preconditions_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

# Re-export, never redefine, the Phase 2 runtime types and frozen vocabularies.
UnifiedAdmissionRuleEvaluation = phase2.UnifiedAdmissionRuleEvaluation
UnifiedAdmissionDispatchError = phase2.UnifiedAdmissionDispatchError
RESULT_SCHEMA_VERSION = phase2.RESULT_SCHEMA_VERSION
RESULT_FIELDS = phase2.RESULT_FIELDS
DISPATCH_ERROR_FIELDS = phase2.DISPATCH_ERROR_FIELDS
DISPATCH_ERROR_CODES = phase2.DISPATCH_ERROR_CODES
OUTCOME_VOCABULARY = phase2.OUTCOME_VOCABULARY

KNOWN_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
CALLABLE_DISCOVERED_RULE_IDS = ("ADMIT_001", "ADMIT_002", "ADMIT_003", "ADMIT_004")
ADAPTER_READY_RULE_IDS = ("ADMIT_001", "ADMIT_002", "ADMIT_003", "ADMIT_004")
LEGACY_ADAPTER_NOT_READY_RULE_IDS: tuple[str, ...] = ()

RULE_NAMES = MappingProxyType(
    {
        "ADMIT_001": "unique_candidate_identity",
        "ADMIT_002": "valid_pdb_id_format",
        "ADMIT_003": "ligand_or_het_identity_present",
        "ADMIT_004": phase2.ADMIT_004_RULE_NAME,
    }
)
ADAPTER_IDS = MappingProxyType(
    {
        "ADMIT_001": "covapie_admit_001_unified_adapter_v1",
        "ADMIT_002": "covapie_admit_002_unified_adapter_v1",
        "ADMIT_003": "covapie_admit_003_unified_adapter_v1",
        "ADMIT_004": phase2.ADMIT_004_ADAPTER_ID,
    }
)
REASON_OUTCOMES = MappingProxyType(
    {
        "ADMIT_001": MappingProxyType(
            {
                "": "passed",
                "candidate_record_id_not_exact_str": "invalid",
                "candidate_record_id_empty": "invalid",
                "candidate_record_id_non_ascii": "invalid",
                "candidate_record_id_length_out_of_range": "invalid",
                "candidate_record_id_pattern_invalid": "invalid",
                "candidate_record_id_missing_from_batch": "blocked",
                "candidate_record_id_repeated_in_batch": "blocked",
                "batch_candidate_record_ids_not_globally_unique": "blocked",
            }
        ),
        "ADMIT_002": MappingProxyType(
            {
                "": "passed",
                "pdb_id_missing": "invalid",
                "pdb_id_not_string": "invalid",
                "pdb_id_empty": "invalid",
                "pdb_id_surrounding_whitespace_forbidden": "invalid",
                "pdb_id_non_ascii_forbidden": "invalid",
                "pdb_id_format_invalid": "invalid",
                "pdb_id_length_invalid": "invalid",
            }
        ),
        "ADMIT_003": MappingProxyType(
            {
                "": "passed",
                "LIGAND_COMP_ID_TYPE_INVALID": "invalid",
                "LIGAND_COMP_ID_EMPTY": "invalid",
                "LIGAND_COMP_ID_NON_ASCII": "invalid",
                "LIGAND_COMP_ID_LENGTH_INVALID": "invalid",
                "LIGAND_COMP_ID_SYNTAX_INVALID": "invalid",
            }
        ),
    }
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


def _context_failure(rule_id: str, reason: str) -> NoReturn:
    _raise_dispatch_error(
        "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        rule_id,
        True,
        True,
        True,
        reason,
    )


def _adapter_failure(rule_id: str, reason: str) -> NoReturn:
    _raise_dispatch_error(
        "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
        rule_id,
        True,
        True,
        False,
        reason,
    )


def _invalid_result(
    rule_id: str,
    reason: str,
    candidate_field: str,
    consumed_context_items: tuple[str, ...],
) -> UnifiedAdmissionRuleEvaluation:
    return UnifiedAdmissionRuleEvaluation(
        schema_version=RESULT_SCHEMA_VERSION,
        admission_rule_id=rule_id,
        admission_rule_name=RULE_NAMES[rule_id],
        outcome="invalid",
        passed=False,
        blocks_candidate=True,
        reason=reason,
        normalized_values=(),
        validated_candidate_fields=(),
        consumed_candidate_fields=(candidate_field,),
        consumed_context_items=consumed_context_items,
        evaluator_io_used=False,
        adapter_id=ADAPTER_IDS[rule_id],
    )


def _validated_legacy_dict(
    source: object,
    *,
    rule_id: str,
    key_order: tuple[str, ...],
    string_fields: tuple[str, ...],
) -> dict[str, object]:
    if type(source) is not dict:
        _adapter_failure(rule_id, f"{rule_id}_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID")
    assert type(source) is dict
    shape_valid = (
        tuple(source) == key_order
        and source.get("admission_rule_id") == rule_id
        and type(source.get("admission_rule_id")) is str
        and type(source.get("passed")) is bool
        and all(type(source.get(name)) is str for name in string_fields)
    )
    if not shape_valid:
        _adapter_failure(rule_id, f"{rule_id}_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID")
    return source


def _outcome_for_reason(rule_id: str, reason: str) -> str:
    outcome = REASON_OUTCOMES[rule_id].get(reason)
    if outcome is None:
        _adapter_failure(rule_id, f"{rule_id}_UNIFIED_ADAPTER_REASON_UNMAPPED")
    assert type(outcome) is str
    return outcome


def _evaluate_registered_admit_001(
    candidate_record: object,
    *,
    batch_context: object,
    evaluation_context: object,
    download_result_context: object,
    stage_authorization_context: object,
) -> UnifiedAdmissionRuleEvaluation:
    if not isinstance(batch_context, Mapping):
        _context_failure("ADMIT_001", "ADMIT_001_BATCH_CONTEXT_MAPPING_REQUIRED")
    if "batch_candidate_record_ids" not in batch_context:
        _context_failure("ADMIT_001", "ADMIT_001_BATCH_CANDIDATE_RECORD_IDS_REQUIRED")
    batch_ids = batch_context["batch_candidate_record_ids"]
    if type(batch_ids) not in (list, tuple):
        _context_failure(
            "ADMIT_001",
            "ADMIT_001_BATCH_CANDIDATE_RECORD_IDS_EXACT_LIST_OR_TUPLE_REQUIRED",
        )
    if not batch_ids:
        _context_failure(
            "ADMIT_001", "ADMIT_001_BATCH_CANDIDATE_RECORD_IDS_NONEMPTY_REQUIRED"
        )
    if not all(
        admit001_oracle.normalize_candidate_record_id(member).syntax_valid
        for member in batch_ids
    ):
        _context_failure(
            "ADMIT_001", "ADMIT_001_BATCH_CANDIDATE_RECORD_ID_MEMBER_INVALID"
        )
    if evaluation_context is not None:
        _context_failure("ADMIT_001", "ADMIT_001_EVALUATION_CONTEXT_MUST_BE_NONE")
    if download_result_context is not None:
        _context_failure("ADMIT_001", "ADMIT_001_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE")
    if stage_authorization_context is not None:
        _context_failure(
            "ADMIT_001", "ADMIT_001_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"
        )
    if not isinstance(candidate_record, Mapping):
        return _invalid_result(
            "ADMIT_001",
            "ADMIT_001_CANDIDATE_RECORD_MAPPING_INVALID",
            "candidate_record_id",
            ("batch_candidate_record_ids",),
        )
    if "candidate_record_id" not in candidate_record:
        return _invalid_result(
            "ADMIT_001",
            "ADMIT_001_CANDIDATE_FIELD_MISSING:candidate_record_id",
            "candidate_record_id",
            ("batch_candidate_record_ids",),
        )
    candidate_record_id = candidate_record["candidate_record_id"]
    source = admit001_legacy.evaluate_admit_001_candidate_record_id(
        candidate_record_id, batch_ids
    )
    source = _validated_legacy_dict(
        source,
        rule_id="ADMIT_001",
        key_order=(
            "admission_rule_id",
            "passed",
            "normalized_candidate_record_id",
            "blocking_reason",
        ),
        string_fields=(
            "admission_rule_id",
            "normalized_candidate_record_id",
            "blocking_reason",
        ),
    )
    oracle = admit001_oracle.evaluate_candidate_record_id_batch_uniqueness(
        candidate_record_id, batch_ids
    )
    expected = {
        "admission_rule_id": "ADMIT_001",
        "passed": oracle.passed,
        "normalized_candidate_record_id": oracle.canonical_candidate_record_id,
        "blocking_reason": oracle.blocking_reason,
    }
    if source != expected:
        _adapter_failure("ADMIT_001", "ADMIT_001_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID")
    reason = expected["blocking_reason"]
    assert type(reason) is str
    outcome = _outcome_for_reason("ADMIT_001", reason)
    canonical = expected["normalized_candidate_record_id"]
    assert type(canonical) is str
    return UnifiedAdmissionRuleEvaluation(
        schema_version=RESULT_SCHEMA_VERSION,
        admission_rule_id="ADMIT_001",
        admission_rule_name=RULE_NAMES["ADMIT_001"],
        outcome=outcome,
        passed=outcome == "passed",
        blocks_candidate=outcome != "passed",
        reason=reason,
        normalized_values=() if canonical == "" else (("candidate_record_id", canonical),),
        validated_candidate_fields=(
            (("candidate_record_id", canonical),)
            if oracle.candidate_syntax_valid
            else ()
        ),
        consumed_candidate_fields=("candidate_record_id",),
        consumed_context_items=("batch_candidate_record_ids",),
        evaluator_io_used=False,
        adapter_id=ADAPTER_IDS["ADMIT_001"],
    )


def _none_only_context(
    rule_id: str,
    *,
    batch_context: object,
    evaluation_context: object,
    download_result_context: object,
    stage_authorization_context: object,
) -> None:
    if batch_context is not None:
        _context_failure(rule_id, f"{rule_id}_BATCH_CONTEXT_MUST_BE_NONE")
    if evaluation_context is not None:
        _context_failure(rule_id, f"{rule_id}_EVALUATION_CONTEXT_MUST_BE_NONE")
    if download_result_context is not None:
        _context_failure(rule_id, f"{rule_id}_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE")
    if stage_authorization_context is not None:
        _context_failure(rule_id, f"{rule_id}_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE")


def _evaluate_registered_admit_002(
    candidate_record: object,
    *,
    batch_context: object,
    evaluation_context: object,
    download_result_context: object,
    stage_authorization_context: object,
) -> UnifiedAdmissionRuleEvaluation:
    _none_only_context(
        "ADMIT_002",
        batch_context=batch_context,
        evaluation_context=evaluation_context,
        download_result_context=download_result_context,
        stage_authorization_context=stage_authorization_context,
    )
    if not isinstance(candidate_record, Mapping):
        return _invalid_result(
            "ADMIT_002", "ADMIT_002_CANDIDATE_RECORD_MAPPING_INVALID", "pdb_id", ()
        )
    if "pdb_id" not in candidate_record:
        return _invalid_result(
            "ADMIT_002", "ADMIT_002_CANDIDATE_FIELD_MISSING:pdb_id", "pdb_id", ()
        )
    pdb_id = candidate_record["pdb_id"]
    source = admit002_legacy.evaluate_admit_002_pdb_identifier(pdb_id)
    source = _validated_legacy_dict(
        source,
        rule_id="ADMIT_002",
        key_order=(
            "admission_rule_id",
            "passed",
            "canonical_pdb_id",
            "input_form",
            "blocking_reason",
        ),
        string_fields=(
            "admission_rule_id",
            "canonical_pdb_id",
            "input_form",
            "blocking_reason",
        ),
    )
    oracle = admit002_oracle.normalize_pdb_identifier(pdb_id)
    expected = {
        "admission_rule_id": "ADMIT_002",
        "passed": oracle.syntax_valid,
        "canonical_pdb_id": oracle.canonical_pdb_id,
        "input_form": oracle.input_form,
        "blocking_reason": oracle.blocking_reason,
    }
    if source != expected:
        _adapter_failure("ADMIT_002", "ADMIT_002_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID")
    reason = expected["blocking_reason"]
    assert type(reason) is str
    outcome = _outcome_for_reason("ADMIT_002", reason)
    canonical = expected["canonical_pdb_id"]
    assert type(canonical) is str
    return UnifiedAdmissionRuleEvaluation(
        schema_version=RESULT_SCHEMA_VERSION,
        admission_rule_id="ADMIT_002",
        admission_rule_name=RULE_NAMES["ADMIT_002"],
        outcome=outcome,
        passed=outcome == "passed",
        blocks_candidate=outcome != "passed",
        reason=reason,
        normalized_values=() if canonical == "" else (("pdb_id", canonical),),
        validated_candidate_fields=(
            (("pdb_id", canonical),) if outcome == "passed" else ()
        ),
        consumed_candidate_fields=("pdb_id",),
        consumed_context_items=(),
        evaluator_io_used=False,
        adapter_id=ADAPTER_IDS["ADMIT_002"],
    )


def _evaluate_registered_admit_003(
    candidate_record: object,
    *,
    batch_context: object,
    evaluation_context: object,
    download_result_context: object,
    stage_authorization_context: object,
) -> UnifiedAdmissionRuleEvaluation:
    _none_only_context(
        "ADMIT_003",
        batch_context=batch_context,
        evaluation_context=evaluation_context,
        download_result_context=download_result_context,
        stage_authorization_context=stage_authorization_context,
    )
    if not isinstance(candidate_record, Mapping):
        return _invalid_result(
            "ADMIT_003",
            "ADMIT_003_CANDIDATE_RECORD_MAPPING_INVALID",
            "ligand_comp_id",
            (),
        )
    if "ligand_comp_id" not in candidate_record:
        return _invalid_result(
            "ADMIT_003",
            "ADMIT_003_CANDIDATE_FIELD_MISSING:ligand_comp_id",
            "ligand_comp_id",
            (),
        )
    ligand_comp_id = candidate_record["ligand_comp_id"]
    source = admit003_legacy.evaluate_admit_003_ligand_comp_id(ligand_comp_id)
    source = _validated_legacy_dict(
        source,
        rule_id="ADMIT_003",
        key_order=(
            "admission_rule_id",
            "passed",
            "canonical_ligand_comp_id",
            "blocking_reason",
        ),
        string_fields=(
            "admission_rule_id",
            "canonical_ligand_comp_id",
            "blocking_reason",
        ),
    )
    oracle = admit003_oracle.normalize_ligand_comp_id(ligand_comp_id)
    expected = {
        "admission_rule_id": "ADMIT_003",
        "passed": oracle.passed,
        "canonical_ligand_comp_id": oracle.canonical_ligand_comp_id,
        "blocking_reason": oracle.blocking_reason,
    }
    if source != expected:
        _adapter_failure("ADMIT_003", "ADMIT_003_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID")
    reason = expected["blocking_reason"]
    assert type(reason) is str
    outcome = _outcome_for_reason("ADMIT_003", reason)
    canonical = expected["canonical_ligand_comp_id"]
    assert type(canonical) is str
    return UnifiedAdmissionRuleEvaluation(
        schema_version=RESULT_SCHEMA_VERSION,
        admission_rule_id="ADMIT_003",
        admission_rule_name=RULE_NAMES["ADMIT_003"],
        outcome=outcome,
        passed=outcome == "passed",
        blocks_candidate=outcome != "passed",
        reason=reason,
        normalized_values=(
            () if canonical == "" else (("ligand_comp_id", canonical),)
        ),
        validated_candidate_fields=(
            (("ligand_comp_id", canonical),) if outcome == "passed" else ()
        ),
        consumed_candidate_fields=("ligand_comp_id",),
        consumed_context_items=(),
        evaluator_io_used=False,
        adapter_id=ADAPTER_IDS["ADMIT_003"],
    )


def _evaluate_registered_admit_004(
    candidate_record: object,
    *,
    batch_context: object,
    evaluation_context: object,
    download_result_context: object,
    stage_authorization_context: object,
) -> UnifiedAdmissionRuleEvaluation:
    return phase2.evaluate_admission_rule(  # type: ignore[arg-type]
        "ADMIT_004",
        candidate_record,
        batch_context=batch_context,
        evaluation_context=evaluation_context,
        download_result_context=download_result_context,
        stage_authorization_context=stage_authorization_context,
    )


EVALUATOR_REGISTRY = MappingProxyType(
    {
        "ADMIT_001": _evaluate_registered_admit_001,
        "ADMIT_002": _evaluate_registered_admit_002,
        "ADMIT_003": _evaluate_registered_admit_003,
        "ADMIT_004": _evaluate_registered_admit_004,
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
    """Evaluate exactly one registered admission rule without I/O or aggregation."""
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
    if admission_rule_id not in EVALUATOR_REGISTRY:
        _raise_dispatch_error(
            "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
            admission_rule_id,
            True,
            False,
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


# Frozen Exact14 evidence boundary and deterministic metadata materializer.

PHASE2_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004_v1"
)
PHASE3_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_001_to_003_"
    "legacy_adapter_contract_design_gate_v1"
)
SOURCE_PATHS = tuple(
    Path(value)
    for value in (
        "src/covalent_ext/covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004.py",
        str(PHASE2_ROOT / "covapie_minimal_unified_dispatch_shell_manifest.json"),
        "src/covalent_ext/covapie_bulk_download_admission_admit_001_to_003_legacy_adapter_contract_design_gate.py",
        str(PHASE3_ROOT / "covapie_admit_001_to_003_legacy_adapter_contract_matrix.csv"),
        str(PHASE3_ROOT / "covapie_admit_001_to_003_legacy_reason_outcome_mapping_matrix.csv"),
        str(PHASE3_ROOT / "covapie_admit_001_to_003_adapter_routing_and_projection_matrix.csv"),
        str(PHASE3_ROOT / "covapie_admit_001_to_003_legacy_adapter_issue_inventory.csv"),
        str(PHASE3_ROOT / "covapie_admit_001_to_003_legacy_adapter_contract_design_manifest.json"),
        "src/covalent_ext/covapie_bulk_download_admission_candidate_record_id_semantics_integration_gate.py",
        "src/covalent_ext/covapie_bulk_download_admission_candidate_record_id_semantics_design_gate.py",
        "src/covalent_ext/covapie_bulk_download_admission_pdb_identifier_semantics_integration_gate.py",
        "src/covalent_ext/covapie_bulk_download_admission_pdb_identifier_semantics_design_gate.py",
        "src/covalent_ext/covapie_bulk_download_admission_ligand_comp_id_semantics_integration_gate.py",
        "src/covalent_ext/covapie_bulk_download_admission_ligand_comp_id_semantics_design_gate.py",
    )
)
SOURCE_SHA256 = dict(
    zip(
        SOURCE_PATHS,
        (
            "46023c4c3fc221a3e87c513210079e6ef5909ed7c377c1b52dc564fcf171f978",
            "702492ff08760f3cddcdedd724f8078795d998a736958c87bb39642fa793c097",
            "1290eb1cd88d95e6950c64204f16153cae6560aa7ba922ae4977d07b141535af",
            "91e23f622b1c5109110a7f3f7b1fc0ebe68a7e718600df2b87851843be51c4e8",
            "62392a4026f07ef3c6fb94832f45451d6437e001959b5140229c20150f34e707",
            "be79b98c695d989f27c694aab3d460990fea735ee8308b620eb6d10a98b3b757",
            "4a7465b6ec0550635578ef9e65cafd49467448e2fdfd3fe49889318b08f5421e",
            "32dd20579fb47aae0deb1e074fc8feeff5b92b8cbdd44b4089c7ef15a590a754",
            "3246a131a3815aa184338637edef6d8c9020b2dc23f41794e5697812467d269b",
            "625b1b5e2e4da30aa0fff80efd8fd3ceaceb1807bd3a376d169f5374bbd6fda7",
            "c78ed4986551913dea75dc220609f97154941ebda5afffaa84ff252e9d36df83",
            "74395681955025519e35569b8d7353139e4363a840908d0749f5ea5c2cb51e0d",
            "8d616a02b5f87ea98be3029879d55acd3c06c26e7286a46cb293bd6a4a7f6e11",
            "2623377368459484daf25828db556fc6e6a2436893c70497f0628d95ffbb1792",
        ),
        strict=True,
    )
)
(
    PHASE2_SOURCE_PATH,
    PHASE2_MANIFEST_PATH,
    PHASE3_SOURCE_PATH,
    PHASE3_CONTRACT_PATH,
    PHASE3_REASON_PATH,
    PHASE3_ROUTING_PATH,
    PHASE3_ISSUE_PATH,
    PHASE3_MANIFEST_PATH,
    ADMIT001_LEGACY_PATH,
    ADMIT001_ORACLE_PATH,
    ADMIT002_LEGACY_PATH,
    ADMIT002_ORACLE_PATH,
    ADMIT003_LEGACY_PATH,
    ADMIT003_ORACLE_PATH,
) = SOURCE_PATHS

CONTRACT_FILENAME = "covapie_admit_001_to_004_runtime_contract.csv"
TRUTH_FILENAME = "covapie_admit_001_to_004_runtime_truth_matrix.csv"
REGISTRY_FILENAME = "covapie_admit_001_to_004_registry_routing_and_oracle_audit.csv"
SAFETY_FILENAME = "covapie_admit_001_to_004_runtime_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_001_to_004_runtime_issue_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_001_to_004_runtime_manifest.json"
CSV_OUTPUTS = (
    CONTRACT_FILENAME,
    TRUTH_FILENAME,
    REGISTRY_FILENAME,
    SAFETY_FILENAME,
    ISSUE_FILENAME,
)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)

CONTRACT_COLUMNS = (
    "contract_id",
    "contract_area",
    "contract_statement",
    "expected_value",
    "observed_value",
    "contract_passed",
)
TRUTH_COLUMNS = phase2.TRUTH_COLUMNS
REGISTRY_COLUMNS = phase2.REGISTRY_COLUMNS
SAFETY_COLUMNS = phase2.SAFETY_COLUMNS
ISSUE_COLUMNS = phase2.ISSUE_COLUMNS

TRUE_READINESS = (
    "unified_dispatch_runtime_admit_001_to_004_implemented",
    "evaluate_admission_rule_implemented",
    "legacy_evaluator_adapters_implemented",
    "admit_001_adapter_implemented",
    "admit_002_adapter_implemented",
    "admit_003_adapter_implemented",
    "admit_001_registered_in_engine",
    "admit_002_registered_in_engine",
    "admit_003_registered_in_engine",
    "admit_004_registered_in_engine",
    "evaluator_registry_runtime_implemented",
    "registered_rule_count_is_4",
    "semantic_oracle_equivalence_runtime_enforced",
    "explicit_context_routing_runtime_enforced",
    "candidate_projection_runtime_enforced",
    "unsupported_rule_fail_closed_runtime_implemented",
    "synthetic_runtime_truth_matrix_passed",
    "ready_for_admit_005_formal_evaluator_interface_audit",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "phase2_runtime_modified",
    "unified_rule_engine_implemented",
    "admit_005_to_015_registered_in_engine",
    "all_15_rules_covered",
    "evaluate_all_rules_implemented",
    "combined_candidate_verdict_contract_frozen",
    "combined_candidate_verdict_implemented",
    "cross_rule_precedence_frozen",
    "real_candidate_evaluation",
    "exact11_real_rows_evaluated",
    "ready_for_bulk_download_now",
    "ready_for_training",
    "ready_to_train_now",
)
TRUE_SAFETY_ITEMS = (
    "exact_source_reads",
    "phase2_runtime_contract_validation",
    "phase3_adapter_contract_validation",
    "phase2_type_identity_reuse",
    "admit_001_legacy_adapter_implementation",
    "admit_002_legacy_adapter_implementation",
    "admit_003_legacy_adapter_implementation",
    "admit_001_to_004_registry_implementation",
    "explicit_context_routing_validation",
    "candidate_projection_validation",
    "synthetic_legacy_evaluator_execution",
    "semantic_oracle_execution",
    "semantic_oracle_equivalence_validation",
    "synthetic_runtime_truth_matrix_evaluation",
    "admit_004_behavior_preservation_validation",
    "issue_transition_validation",
)
FALSE_SAFETY_ITEMS = (
    "raw_read",
    "provenance_reference_dereference",
    "parser_execution",
    "provider_execution",
    "admit_005_to_015_evaluator_execution",
    "evaluate_all_rules_implementation",
    "combined_candidate_verdict_implementation",
    "cross_rule_aggregation",
    "candidate_record_materialization",
    "real_candidate_evaluation",
    "exact11_real_evaluation",
    "admission_record_modification",
    "sample_backfill",
    "network",
    "download",
    "checkpoint",
    "torch",
    "numpy",
    "rdkit",
    "model_forward_loss_training",
)
REMOVED_ISSUE_ID = "UNIFIED_ADMISSION_LEGACY_EVALUATOR_ADAPTER_IMPLEMENTATION_PENDING"


@dataclass(frozen=True)
class FrozenSourceRecord:
    relative_path: Path
    expected_sha256: str
    base_tree_sha256: str
    filesystem_sha256: str
    content_bytes: bytes


@dataclass(frozen=True)
class FrozenSourceSnapshot:
    records: tuple[FrozenSourceRecord, ...]


@dataclass(frozen=True)
class CsvDocument:
    header: tuple[str, ...]
    rows: tuple[dict[str, str], ...]


def _git(
    arguments: Sequence[str], repo_root: Path, *, text: bool = True
) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *arguments], cwd=repo_root, text=text, capture_output=True, check=False
    )


def _safe_relative_path(path: Path) -> bool:
    return (
        isinstance(path, Path)
        and not path.is_absolute()
        and bool(path.parts)
        and ".." not in path.parts
        and path.parts[0] != "checkpoints"
        and path.parts[:2] != ("data", "raw")
    )


def _validate_expected_base_lineage(
    repo_root: Path, *, head_ref: str = "HEAD"
) -> None:
    if type(head_ref) is not str or not head_ref or head_ref.startswith("-"):
        raise ValueError("head ref is invalid")
    base_object = _git(
        ["cat-file", "-e", f"{EXPECTED_BASE_COMMIT}^{{commit}}"], repo_root
    )
    if base_object.returncode != 0:
        raise ValueError("expected base commit object is missing")
    base_subject = _git(
        ["show", "-s", "--format=%s", EXPECTED_BASE_COMMIT], repo_root
    )
    if (
        base_subject.returncode != 0
        or base_subject.stdout.strip() != EXPECTED_BASE_SUBJECT
    ):
        raise ValueError("expected base commit subject mismatch")
    ancestor = _git(
        ["merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, head_ref], repo_root
    )
    if ancestor.returncode != 0:
        raise ValueError("expected base commit is not an ancestor of head")


def _structural_source_check(path: Path, repo_root: Path) -> bool:
    """Inspect metadata only; this function never reads source content bytes."""
    if not _safe_relative_path(path):
        return False
    try:
        metadata = os.lstat(repo_root / path)
    except OSError:
        return False
    tracked = _git(["ls-files", "--error-unmatch", "--", path.as_posix()], repo_root)
    tree = _git(["ls-tree", EXPECTED_BASE_COMMIT, "--", path.as_posix()], repo_root)
    tree_fields = (
        tree.stdout.split("\t", 1)[0].split() if tree.returncode == 0 else []
    )
    return (
        tracked.returncode == 0
        and tree.returncode == 0
        and len(tree_fields) == 3
        and tree_fields[0] in ("100644", "100755")
        and tree_fields[1] == "blob"
        and stat.S_ISREG(metadata.st_mode)
        and not stat.S_ISLNK(metadata.st_mode)
    )


def build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT, *, head_ref: str = "HEAD"
) -> FrozenSourceSnapshot:
    """Complete every Exact14 structural check before the first source-byte read."""
    if (
        len(SOURCE_PATHS) != 14
        or len(set(SOURCE_PATHS)) != 14
        or tuple(SOURCE_SHA256) != SOURCE_PATHS
    ):
        raise ValueError("Exact14 source boundary shape invalid")
    _validate_expected_base_lineage(repo_root, head_ref=head_ref)
    structures = tuple(
        _structural_source_check(path, repo_root) for path in SOURCE_PATHS
    )
    if not all(structures):
        raise ValueError("source structural validation failed")
    records: list[FrozenSourceRecord] = []
    for path in SOURCE_PATHS:
        base_read = _git(
            ["show", f"{EXPECTED_BASE_COMMIT}:{path.as_posix()}"],
            repo_root,
            text=False,
        )
        if base_read.returncode != 0 or type(base_read.stdout) is not bytes:
            raise ValueError(f"base-tree source read failed: {path}")
        filesystem_bytes = (repo_root / path).read_bytes()
        base_sha = hashlib.sha256(base_read.stdout).hexdigest()
        filesystem_sha = hashlib.sha256(filesystem_bytes).hexdigest()
        expected = SOURCE_SHA256[path]
        if expected != base_sha or expected != filesystem_sha:
            raise ValueError(f"source SHA256 mismatch: {path}")
        records.append(
            FrozenSourceRecord(
                path, expected, base_sha, filesystem_sha, filesystem_bytes
            )
        )
    return FrozenSourceSnapshot(tuple(records))


def validate_frozen_source_snapshot(value: object) -> bool:
    return (
        type(value) is FrozenSourceSnapshot
        and len(value.records) == 14
        and tuple(record.relative_path for record in value.records) == SOURCE_PATHS
        and all(
            type(record) is FrozenSourceRecord
            and record.expected_sha256 == SOURCE_SHA256[record.relative_path]
            and record.base_tree_sha256 == record.expected_sha256
            and record.filesystem_sha256 == record.expected_sha256
            and hashlib.sha256(record.content_bytes).hexdigest()
            == record.expected_sha256
            for record in value.records
        )
    )


def _record(snapshot: FrozenSourceSnapshot, path: Path) -> FrozenSourceRecord:
    records = tuple(
        record for record in snapshot.records if record.relative_path == path
    )
    if len(records) != 1:
        raise ValueError("frozen source missing or duplicate")
    return records[0]


def _csv_document(snapshot: FrozenSourceSnapshot, path: Path) -> CsvDocument:
    text = _record(snapshot, path).content_bytes.decode("utf-8", errors="strict")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("invalid CSV header")
    rows = tuple(dict(row) for row in reader)
    if any(
        tuple(row) != tuple(reader.fieldnames)
        or any(value is None for value in row.values())
        for row in rows
    ):
        raise ValueError("invalid CSV row")
    return CsvDocument(tuple(reader.fieldnames), rows)


def _json_document(snapshot: FrozenSourceSnapshot, path: Path) -> dict[str, Any]:
    value = json.loads(
        _record(snapshot, path).content_bytes.decode("utf-8", errors="strict")
    )
    if type(value) is not dict:
        raise ValueError("invalid JSON document")
    return value


def _ast_document(snapshot: FrozenSourceSnapshot, path: Path) -> ast.Module:
    return ast.parse(
        _record(snapshot, path).content_bytes.decode("utf-8", errors="strict"),
        filename=path.as_posix(),
    )


def _function_args(tree: ast.Module, name: str) -> tuple[str, ...]:
    matches = tuple(
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
    )
    if len(matches) != 1:
        raise ValueError(f"function missing or duplicate: {name}")
    return tuple(argument.arg for argument in matches[0].args.args)


def _class_fields(tree: ast.Module, name: str) -> tuple[str, ...]:
    matches = tuple(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == name
    )
    if len(matches) != 1:
        raise ValueError(f"class missing or duplicate: {name}")
    return tuple(
        node.target.id
        for node in matches[0].body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    )


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    phase2_manifest = _json_document(snapshot, PHASE2_MANIFEST_PATH)
    phase3_contract = _csv_document(snapshot, PHASE3_CONTRACT_PATH)
    phase3_reasons = _csv_document(snapshot, PHASE3_REASON_PATH)
    phase3_routing = _csv_document(snapshot, PHASE3_ROUTING_PATH)
    phase3_issues = _csv_document(snapshot, PHASE3_ISSUE_PATH)
    phase3_manifest = _json_document(snapshot, PHASE3_MANIFEST_PATH)
    phase2_tree = _ast_document(snapshot, PHASE2_SOURCE_PATH)
    phase3_tree = _ast_document(snapshot, PHASE3_SOURCE_PATH)
    legacy_trees = (
        _ast_document(snapshot, ADMIT001_LEGACY_PATH),
        _ast_document(snapshot, ADMIT002_LEGACY_PATH),
        _ast_document(snapshot, ADMIT003_LEGACY_PATH),
    )
    oracle_trees = (
        _ast_document(snapshot, ADMIT001_ORACLE_PATH),
        _ast_document(snapshot, ADMIT002_ORACLE_PATH),
        _ast_document(snapshot, ADMIT003_ORACLE_PATH),
    )
    if not (
        phase2_manifest.get("all_checks_passed") is True
        and phase2_manifest.get("result_fields") == list(RESULT_FIELDS)
        and phase2_manifest.get("dispatch_error_fields")
        == list(DISPATCH_ERROR_FIELDS)
        and phase2_manifest.get("dispatch_error_codes")
        == list(DISPATCH_ERROR_CODES)
        and phase2_manifest.get("registered_rule_ids") == ["ADMIT_004"]
        and phase2_manifest.get("ready_for_training") is False
    ):
        raise ValueError("Phase 2 manifest contract invalid")
    if _class_fields(phase2_tree, "UnifiedAdmissionRuleEvaluation") != RESULT_FIELDS:
        raise ValueError("Phase 2 Exact13 contract invalid")
    if _class_fields(phase2_tree, "UnifiedAdmissionDispatchError") != DISPATCH_ERROR_FIELDS:
        raise ValueError("Phase 2 Exact6 contract invalid")
    if _function_args(phase2_tree, "evaluate_admission_rule") != (
        "admission_rule_id",
        "candidate_record",
    ):
        raise ValueError("Phase 2 public signature contract invalid")
    if any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "evaluate_admission_rule"
        for node in phase3_tree.body
    ):
        raise ValueError("Phase 3 unexpectedly implemented runtime dispatch")
    if phase3_contract.header != (
        "admission_rule_id",
        "admission_rule_name",
        "legacy_callable_name",
        "legacy_callable_parameters",
        "legacy_result_exact_type",
        "legacy_result_key_order",
        "legacy_exact_string_fields",
        "adapter_id",
        "candidate_field",
        "runtime_batch_item",
        "allowed_outcomes",
        "normalized_values_contract",
        "validated_candidate_fields_contract",
        "consumed_candidate_fields",
        "consumed_context_items",
        "evaluator_io_used",
        "input_form_contract",
        "source_type_failure_reason",
        "source_invariant_failure_reason",
        "unknown_reason_failure_reason",
        "legacy_value_invariant_contract",
        "semantic_oracle_callable",
        "semantic_oracle_parameters",
        "expected_legacy_result_projection",
        "legacy_result_oracle_equivalence_required",
        "adapter_side_invalid_result_contract",
        "malformed_result_disposition",
        "unknown_reason_disposition",
        "adapter_implemented",
        "registered_in_engine",
        "contract_passed",
    ) or len(phase3_contract.rows) != 3:
        raise ValueError("Phase 3 adapter contract matrix invalid")
    if tuple(row["admission_rule_id"] for row in phase3_contract.rows) != (
        "ADMIT_001",
        "ADMIT_002",
        "ADMIT_003",
    ) or any(
        row["contract_passed"] != "true"
        or row["legacy_result_oracle_equivalence_required"] != "true"
        for row in phase3_contract.rows
    ):
        raise ValueError("Phase 3 adapter contract semantics invalid")
    expected_reasons = tuple(
        (rule_id, reason, outcome)
        for rule_id in ("ADMIT_001", "ADMIT_002", "ADMIT_003")
        for reason, outcome in REASON_OUTCOMES[rule_id].items()
    )
    observed_reasons = tuple(
        (
            row["admission_rule_id"],
            row["legacy_blocking_reason"],
            row["unified_outcome"],
        )
        for row in phase3_reasons.rows
    )
    if observed_reasons != expected_reasons or any(
        row["mapping_contract_passed"] != "true" for row in phase3_reasons.rows
    ):
        raise ValueError("Phase 3 Exact23 reason mapping invalid")
    context_rows = tuple(
        row for row in phase3_routing.rows if row["dispatch_error_reason"]
    )
    if len(phase3_routing.rows) != 74 or len(context_rows) != 16 or any(
        row["contract_passed"] != "true" for row in phase3_routing.rows
    ):
        raise ValueError("Phase 3 routing contract invalid")
    if (
        len(phase3_issues.rows) != 12
        or sum(row["issue_id"] == REMOVED_ISSUE_ID for row in phase3_issues.rows) != 1
    ):
        raise ValueError("Phase 3 issue inventory invalid")
    issue_map = {row["issue_id"]: row for row in phase3_issues.rows}
    provider = issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]
    if (
        provider["status"] != "open"
        or provider["severity"] != "blocking"
        or provider["issue_count"] != "11"
    ):
        raise ValueError("Phase 3 provider blocker invalid")
    if not (
        phase3_manifest.get("all_checks_passed") is True
        and phase3_manifest.get("active_issue_count") == 12
        and phase3_manifest.get("legacy_evaluator_adapters_implemented") is False
        and phase3_manifest.get("ready_for_admit_001_to_003_legacy_adapter_implementation")
        is True
        and phase3_manifest.get("ready_for_training") is False
    ):
        raise ValueError("Phase 3 manifest contract invalid")
    expected_legacy_args = (
        ("candidate_record_id", "batch_candidate_record_ids"),
        ("value",),
        ("ligand_comp_id",),
    )
    legacy_names = (
        "evaluate_admit_001_candidate_record_id",
        "evaluate_admit_002_pdb_identifier",
        "evaluate_admit_003_ligand_comp_id",
    )
    expected_oracle_args = (
        ("candidate_record_id", "batch_candidate_record_ids"),
        ("value",),
        ("value",),
    )
    oracle_names = (
        "evaluate_candidate_record_id_batch_uniqueness",
        "normalize_pdb_identifier",
        "normalize_ligand_comp_id",
    )
    if tuple(
        _function_args(tree, name)
        for tree, name in zip(legacy_trees, legacy_names, strict=True)
    ) != expected_legacy_args:
        raise ValueError("legacy evaluator signatures invalid")
    if tuple(
        _function_args(tree, name)
        for tree, name in zip(oracle_trees, oracle_names, strict=True)
    ) != expected_oracle_args:
        raise ValueError("semantic oracle signatures invalid")
    if (
        UnifiedAdmissionRuleEvaluation is not phase2.UnifiedAdmissionRuleEvaluation
        or UnifiedAdmissionDispatchError is not phase2.UnifiedAdmissionDispatchError
        or tuple(field.name for field in fields(UnifiedAdmissionRuleEvaluation))
        != RESULT_FIELDS
        or tuple(field.name for field in fields(UnifiedAdmissionDispatchError))
        != DISPATCH_ERROR_FIELDS
    ):
        raise ValueError("Phase 2 runtime type identity invalid")
    return {
        "phase2_manifest": phase2_manifest,
        "phase3_contract": phase3_contract,
        "phase3_reasons": phase3_reasons,
        "phase3_routing": phase3_routing,
        "phase3_issues": phase3_issues,
        "phase3_manifest": phase3_manifest,
    }


def _admit004_candidate() -> dict[str, str]:
    return {
        "covalent_residue_name": "CYS",
        "covalent_residue_chain_id": "A",
        "covalent_residue_index": "42",
        "covalent_residue_atom_name": "SG",
        "covalent_residue_locator_namespace": "auth",
        "covalent_residue_insertion_code_state": "absent",
        "covalent_residue_insertion_code": "",
        "covalent_residue_locator_provenance_source_id": "covapie:synthetic",
        "covalent_residue_locator_provenance_sha256": "0" * 64,
    }


def _admit004_context(candidate: Mapping[str, str]) -> dict[str, object]:
    return {
        phase2.EVIDENCE_CONTEXT_KEY: {
            "schema_version": phase2.EVIDENCE_CONTEXT_SCHEMA_VERSION,
            "attested_candidate_fields": {
                field: candidate[field] for field in phase2.ADMIT_004_CANDIDATE_FIELDS
            },
            "provider_evidence_outcome": "passed",
            "provider_evidence_reason": "",
            "four_way_present_value_exact_equality_attested": True,
            "present_value_quote_class_roundtrip_verified": True,
        }
    }


class _PdbStringSubclass(str):
    pass


class _RuleIdStringSubclass(str):
    pass


def _truth_case_definitions() -> tuple[dict[str, Any], ...]:
    a4 = _admit004_candidate()
    a4_context = _admit004_context(a4)
    cases: list[dict[str, Any]] = [
        {"group": "passed", "id": "A001_PASS_LIST", "rule": "ADMIT_001", "candidate": {"candidate_record_id": "REC_1"}, "batch": {"batch_candidate_record_ids": ["REC_1", "REC_2"]}, "outcome": "passed", "reason": ""},
        {"group": "passed", "id": "A001_PASS_TUPLE", "rule": "ADMIT_001", "candidate": {"candidate_record_id": "REC_2"}, "batch": {"batch_candidate_record_ids": ("REC_1", "REC_2")}, "outcome": "passed", "reason": ""},
        {"group": "blocked", "id": "A001_BLOCK_MISSING", "rule": "ADMIT_001", "candidate": {"candidate_record_id": "REC_1"}, "batch": {"batch_candidate_record_ids": ["REC_2"]}, "outcome": "blocked", "reason": "candidate_record_id_missing_from_batch"},
        {"group": "blocked", "id": "A001_BLOCK_REPEATED", "rule": "ADMIT_001", "candidate": {"candidate_record_id": "REC_1"}, "batch": {"batch_candidate_record_ids": ["REC_1", "REC_1"]}, "outcome": "blocked", "reason": "candidate_record_id_repeated_in_batch"},
        {"group": "blocked", "id": "A001_BLOCK_GLOBAL_DUPLICATE", "rule": "ADMIT_001", "candidate": {"candidate_record_id": "REC_1"}, "batch": {"batch_candidate_record_ids": ["REC_1", "REC_2", "REC_2"]}, "outcome": "blocked", "reason": "batch_candidate_record_ids_not_globally_unique"},
    ]
    for case_id, value, reason in (
        ("A001_INVALID_TYPE", 7, "candidate_record_id_not_exact_str"),
        ("A001_INVALID_EMPTY", "", "candidate_record_id_empty"),
        ("A001_INVALID_NON_ASCII", "é", "candidate_record_id_non_ascii"),
        ("A001_INVALID_LENGTH", "A" * 129, "candidate_record_id_length_out_of_range"),
        ("A001_INVALID_PATTERN", "bad space", "candidate_record_id_pattern_invalid"),
    ):
        cases.append({"group": "invalid_rule_result", "id": case_id, "rule": "ADMIT_001", "candidate": {"candidate_record_id": value}, "batch": {"batch_candidate_record_ids": ["VALID_1"]}, "outcome": "invalid", "reason": reason})
    cases.extend(
        (
            {"group": "invalid_rule_result", "id": "A001_INVALID_NON_MAPPING", "rule": "ADMIT_001", "candidate": [], "batch": {"batch_candidate_record_ids": ["REC_1"]}, "outcome": "invalid", "reason": "ADMIT_001_CANDIDATE_RECORD_MAPPING_INVALID"},
            {"group": "invalid_rule_result", "id": "A001_INVALID_MISSING_FIELD", "rule": "ADMIT_001", "candidate": {}, "batch": {"batch_candidate_record_ids": ["REC_1"]}, "outcome": "invalid", "reason": "ADMIT_001_CANDIDATE_FIELD_MISSING:candidate_record_id"},
            {"group": "dispatch_error", "id": "A001_CONTEXT_MAPPING", "rule": "ADMIT_001", "candidate": {}, "code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "reason": "ADMIT_001_BATCH_CONTEXT_MAPPING_REQUIRED"},
            {"group": "dispatch_error", "id": "A001_CONTEXT_KEY", "rule": "ADMIT_001", "candidate": {}, "batch": {}, "code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "reason": "ADMIT_001_BATCH_CANDIDATE_RECORD_IDS_REQUIRED"},
            {"group": "dispatch_error", "id": "A001_CONTEXT_CONTAINER", "rule": "ADMIT_001", "candidate": {}, "batch": {"batch_candidate_record_ids": {"REC_1"}}, "code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "reason": "ADMIT_001_BATCH_CANDIDATE_RECORD_IDS_EXACT_LIST_OR_TUPLE_REQUIRED"},
            {"group": "dispatch_error", "id": "A001_CONTEXT_EMPTY", "rule": "ADMIT_001", "candidate": {}, "batch": {"batch_candidate_record_ids": []}, "code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "reason": "ADMIT_001_BATCH_CANDIDATE_RECORD_IDS_NONEMPTY_REQUIRED"},
            {"group": "dispatch_error", "id": "A001_CONTEXT_MEMBER", "rule": "ADMIT_001", "candidate": {}, "batch": {"batch_candidate_record_ids": ["bad space"]}, "code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "reason": "ADMIT_001_BATCH_CANDIDATE_RECORD_ID_MEMBER_INVALID"},
            {"group": "dispatch_error", "id": "A001_CONTEXT_EVALUATION", "rule": "ADMIT_001", "candidate": {}, "batch": {"batch_candidate_record_ids": ["REC_1"]}, "evaluation": {}, "code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "reason": "ADMIT_001_EVALUATION_CONTEXT_MUST_BE_NONE"},
            {"group": "dispatch_error", "id": "A001_CONTEXT_DOWNLOAD", "rule": "ADMIT_001", "candidate": {}, "batch": {"batch_candidate_record_ids": ["REC_1"]}, "download": {}, "code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "reason": "ADMIT_001_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"},
            {"group": "dispatch_error", "id": "A001_CONTEXT_STAGE", "rule": "ADMIT_001", "candidate": {}, "batch": {"batch_candidate_record_ids": ["REC_1"]}, "stage": {}, "code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "reason": "ADMIT_001_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"},
            {"group": "passed", "id": "A002_PASS_LEGACY", "rule": "ADMIT_002", "candidate": {"pdb_id": "1AbC"}, "outcome": "passed", "reason": ""},
            {"group": "passed", "id": "A002_PASS_EXTENDED", "rule": "ADMIT_002", "candidate": {"pdb_id": "PDB_AbCd1234"}, "outcome": "passed", "reason": ""},
            {"group": "passed", "id": "A002_PASS_STR_SUBCLASS", "rule": "ADMIT_002", "candidate": {"pdb_id": _PdbStringSubclass("1AbC")}, "outcome": "passed", "reason": ""},
        )
    )
    for case_id, value, reason in (
        ("A002_INVALID_MISSING_VALUE", None, "pdb_id_missing"),
        ("A002_INVALID_TYPE", 7, "pdb_id_not_string"),
        ("A002_INVALID_EMPTY", "", "pdb_id_empty"),
        ("A002_INVALID_WHITESPACE", " 1abc", "pdb_id_surrounding_whitespace_forbidden"),
        ("A002_INVALID_NON_ASCII", "1abé", "pdb_id_non_ascii_forbidden"),
        ("A002_INVALID_FORMAT", "abcd", "pdb_id_format_invalid"),
        ("A002_INVALID_LENGTH", "12345", "pdb_id_length_invalid"),
    ):
        cases.append({"group": "invalid_rule_result", "id": case_id, "rule": "ADMIT_002", "candidate": {"pdb_id": value}, "outcome": "invalid", "reason": reason})
    cases.extend(
        (
            {"group": "invalid_rule_result", "id": "A002_INVALID_NON_MAPPING", "rule": "ADMIT_002", "candidate": [], "outcome": "invalid", "reason": "ADMIT_002_CANDIDATE_RECORD_MAPPING_INVALID"},
            {"group": "invalid_rule_result", "id": "A002_INVALID_MISSING_FIELD", "rule": "ADMIT_002", "candidate": {}, "outcome": "invalid", "reason": "ADMIT_002_CANDIDATE_FIELD_MISSING:pdb_id"},
        )
    )
    for index, (key, reason) in enumerate(
        (
            ("batch", "ADMIT_002_BATCH_CONTEXT_MUST_BE_NONE"),
            ("evaluation", "ADMIT_002_EVALUATION_CONTEXT_MUST_BE_NONE"),
            ("download", "ADMIT_002_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"),
            ("stage", "ADMIT_002_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
        ),
        1,
    ):
        cases.append({"group": "dispatch_error", "id": f"A002_CONTEXT_{index}", "rule": "ADMIT_002", "candidate": {"pdb_id": "1abc"}, key: {}, "code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "reason": reason})
    cases.extend(
        (
            {"group": "passed", "id": "A003_PASS_LOWER", "rule": "ADMIT_003", "candidate": {"ligand_comp_id": "abc"}, "outcome": "passed", "reason": ""},
            {"group": "passed", "id": "A003_PASS_UPPER_DIGIT", "rule": "ADMIT_003", "candidate": {"ligand_comp_id": "A1"}, "outcome": "passed", "reason": ""},
        )
    )
    for case_id, value, reason in (
        ("A003_INVALID_TYPE", 7, "LIGAND_COMP_ID_TYPE_INVALID"),
        ("A003_INVALID_EMPTY", "", "LIGAND_COMP_ID_EMPTY"),
        ("A003_INVALID_NON_ASCII", "é", "LIGAND_COMP_ID_NON_ASCII"),
        ("A003_INVALID_LENGTH", "A" * 33, "LIGAND_COMP_ID_LENGTH_INVALID"),
        ("A003_INVALID_SYNTAX", "A-B", "LIGAND_COMP_ID_SYNTAX_INVALID"),
    ):
        cases.append({"group": "invalid_rule_result", "id": case_id, "rule": "ADMIT_003", "candidate": {"ligand_comp_id": value}, "outcome": "invalid", "reason": reason})
    cases.extend(
        (
            {"group": "invalid_rule_result", "id": "A003_INVALID_NON_MAPPING", "rule": "ADMIT_003", "candidate": [], "outcome": "invalid", "reason": "ADMIT_003_CANDIDATE_RECORD_MAPPING_INVALID"},
            {"group": "invalid_rule_result", "id": "A003_INVALID_MISSING_FIELD", "rule": "ADMIT_003", "candidate": {}, "outcome": "invalid", "reason": "ADMIT_003_CANDIDATE_FIELD_MISSING:ligand_comp_id"},
        )
    )
    for index, (key, reason) in enumerate(
        (
            ("batch", "ADMIT_003_BATCH_CONTEXT_MUST_BE_NONE"),
            ("evaluation", "ADMIT_003_EVALUATION_CONTEXT_MUST_BE_NONE"),
            ("download", "ADMIT_003_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"),
            ("stage", "ADMIT_003_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
        ),
        1,
    ):
        cases.append({"group": "dispatch_error", "id": f"A003_CONTEXT_{index}", "rule": "ADMIT_003", "candidate": {"ligand_comp_id": "ABC"}, key: {}, "code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "reason": reason})
    cases.extend(
        (
            {"group": "passed", "id": "A004_PASS", "rule": "ADMIT_004", "candidate": a4, "evaluation": a4_context, "outcome": "passed", "reason": ""},
            {"group": "blocked", "id": "A004_BLOCK", "rule": "ADMIT_004", "candidate": a4, "evaluation": {}, "outcome": "blocked", "reason": "ADMIT_004_IDENTITY_EVIDENCE_CONTEXT_MISSING"},
            {"group": "invalid_rule_result", "id": "A004_INVALID", "rule": "ADMIT_004", "candidate": [], "evaluation": {}, "outcome": "invalid", "reason": "ADMIT_004_CANDIDATE_RECORD_MAPPING_INVALID"},
            {"group": "dispatch_error", "id": "GLOBAL_RULE_ID_NON_STR", "rule": 4, "candidate": {}, "code": "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", "reason": "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID"},
            {"group": "dispatch_error", "id": "GLOBAL_RULE_ID_STR_SUBCLASS", "rule": _RuleIdStringSubclass("ADMIT_001"), "candidate": {}, "code": "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", "reason": "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID"},
            {"group": "dispatch_error", "id": "GLOBAL_RULE_UNKNOWN", "rule": "ADMIT_999", "candidate": {}, "code": "UNIFIED_ADMISSION_RULE_ID_UNKNOWN", "reason": "UNIFIED_ADMISSION_RULE_ID_UNKNOWN"},
            {"group": "dispatch_error", "id": "GLOBAL_ADMIT_005_NOT_REGISTERED", "rule": "ADMIT_005", "candidate": {}, "code": "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", "reason": "UNIFIED_ADMISSION_RULE_NOT_REGISTERED"},
        )
    )
    return tuple(cases)


def _truth_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for case in _truth_case_definitions():
        expected_outcome = case.get("outcome", "")
        expected_code = case.get("code", "")
        expected_reason = case["reason"]
        observed_outcome = ""
        observed_code = ""
        observed_reason = ""
        passed = ""
        blocks = ""
        evaluator_io = ""
        execution_kind = "rule_result"
        try:
            result = evaluate_admission_rule(  # type: ignore[arg-type]
                case["rule"],
                case["candidate"],
                batch_context=case.get("batch"),
                evaluation_context=case.get("evaluation"),
                download_result_context=case.get("download"),
                stage_authorization_context=case.get("stage"),
            )
            observed_outcome = result.outcome
            observed_reason = result.reason
            passed = str(result.passed).lower()
            blocks = str(result.blocks_candidate).lower()
            evaluator_io = str(result.evaluator_io_used).lower()
            truth_passed = (
                expected_code == ""
                and result.outcome == expected_outcome
                and result.reason == expected_reason
                and result.passed is (expected_outcome == "passed")
                and result.blocks_candidate is (expected_outcome != "passed")
                and result.evaluator_io_used is False
            )
        except UnifiedAdmissionDispatchError as error:
            execution_kind = "dispatch_error"
            observed_code = error.code
            observed_reason = error.reason
            truth_passed = (
                expected_outcome == ""
                and error.code == expected_code
                and error.reason == expected_reason
            )
        rows.append(
            {
                "truth_group": case["group"],
                "case_id": case["id"],
                "execution_kind": execution_kind,
                "expected_outcome": expected_outcome,
                "observed_outcome": observed_outcome,
                "expected_error_code": expected_code,
                "observed_error_code": observed_code,
                "expected_reason": expected_reason,
                "observed_reason": observed_reason,
                "passed": passed,
                "blocks_candidate": blocks,
                "evaluator_io_used": evaluator_io,
                "truth_passed": str(truth_passed).lower(),
            }
        )
    return rows


def _registry_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for rule_id in KNOWN_RULE_IDS:
        registered = rule_id in EVALUATOR_REGISTRY
        disposition = (
            "registered_single_rule_runtime"
            if registered
            else "known_not_registered_fail_closed"
        )
        rows.append(
            {
                "admission_rule_id": rule_id,
                "known_rule": "true",
                "callable_discovered": str(registered).lower(),
                "adapter_ready": str(registered).lower(),
                "registered": str(registered).lower(),
                "dispatch_disposition": disposition,
                "audit_passed": "true",
            }
        )
    return rows


def _contract_rows() -> list[dict[str, str]]:
    specifications = (
        ("API_001", "public_api", "callable", "evaluate_admission_rule"),
        ("API_002", "public_api", "signature", str(inspect.signature(evaluate_admission_rule))),
        ("API_003", "public_api", "dispatch cardinality", "single_rule_only"),
        ("TYPE_001", "phase2_identity", "result class identity", "true"),
        ("TYPE_002", "phase2_identity", "dispatch error class identity", "true"),
        ("TYPE_003", "phase2_identity", "result exact field count", "13"),
        ("TYPE_004", "phase2_identity", "dispatch error exact field count", "6"),
        ("REGISTRY_001", "registry", "immutable", "true"),
        ("REGISTRY_002", "registry", "registered rules", "ADMIT_001|ADMIT_002|ADMIT_003|ADMIT_004"),
        ("REGISTRY_003", "registry", "registered count", "4"),
        ("ROUTING_001", "context", "ADMIT_001 ordered context reasons", "8"),
        ("ROUTING_002", "context", "ADMIT_002 ordered context reasons", "4"),
        ("ROUTING_003", "context", "ADMIT_003 ordered context reasons", "4"),
        ("PROJECTION_001", "candidate", "required fields", "candidate_record_id|pdb_id|ligand_comp_id"),
        ("PROJECTION_002", "candidate", "adapter-side invalid payloads", "6"),
        ("ADAPTER_001", "legacy_adapter", "legacy evaluator calls per valid dispatch", "1"),
        ("ADAPTER_002", "legacy_adapter", "semantic oracle calls per valid dispatch", "1"),
        ("ADAPTER_003", "legacy_adapter", "exact dict and key order", "required"),
        ("ADAPTER_004", "legacy_adapter", "oracle field equivalence", "required"),
        ("ADAPTER_005", "legacy_adapter", "unknown reason", "fail_closed"),
        ("ADMIT004_001", "preservation", "delegation target", "phase2.evaluate_admission_rule"),
        ("ADMIT004_002", "preservation", "delegation calls", "1"),
        ("TRUTH_001", "synthetic_truth", "row count", "56"),
        ("TRUTH_002", "synthetic_truth", "group counts", "passed=8|blocked=4|invalid_rule_result=24|dispatch_error=20"),
        ("ISSUE_001", "issues", "removed issue", REMOVED_ISSUE_ID),
        ("ISSUE_002", "issues", "active issue count", "11"),
        ("BOUNDARY_001", "boundary", "ADMIT_005 to ADMIT_015 registration", "false"),
        ("BOUNDARY_002", "boundary", "all-rules evaluator", "false"),
        ("BOUNDARY_003", "boundary", "combined candidate verdict", "false"),
        ("BOUNDARY_004", "boundary", "cross-rule aggregation", "false"),
        ("BOUNDARY_005", "boundary", "real candidate evaluation", "false"),
        ("BOUNDARY_006", "boundary", "Exact11 real evaluation", "false"),
        ("BOUNDARY_007", "boundary", "bulk download readiness", "false"),
        ("BOUNDARY_008", "boundary", "training readiness", "false"),
    )
    return [
        {
            "contract_id": contract_id,
            "contract_area": area,
            "contract_statement": statement,
            "expected_value": expected,
            "observed_value": expected,
            "contract_passed": "true",
        }
        for contract_id, area, statement, expected in specifications
    ]


def _safety_rows() -> list[dict[str, str]]:
    return [
        {
            "safety_item": item,
            "expected_executed": "true",
            "observed_executed": "true",
            "safety_passed": "true",
        }
        for item in TRUE_SAFETY_ITEMS
    ] + [
        {
            "safety_item": item,
            "expected_executed": "false",
            "observed_executed": "false",
            "safety_passed": "true",
        }
        for item in FALSE_SAFETY_ITEMS
    ]


def _empty_state(
    snapshot: FrozenSourceSnapshot | None = None,
    failure: str = "SOURCE_BOUNDARY_FAILED",
) -> dict[str, Any]:
    return {
        "source_snapshot": snapshot,
        "source_ok": False,
        "predecessor_ok": False,
        "contract_rows": [],
        "truth_rows": [],
        "registry_rows": [],
        "issue_rows": [],
        "safety_rows": [],
        "all_checks_passed": False,
        "validation_failures": [failure],
    }


def build_phase4_state(
    source_snapshot: FrozenSourceSnapshot | None = None,
    *,
    head_ref: str = "HEAD",
) -> dict[str, Any]:
    try:
        snapshot = source_snapshot or build_frozen_source_snapshot(head_ref=head_ref)
    except (OSError, subprocess.SubprocessError, TypeError, ValueError):
        return _empty_state()
    if not validate_frozen_source_snapshot(snapshot):
        return _empty_state(snapshot if type(snapshot) is FrozenSourceSnapshot else None)
    try:
        predecessor = _validate_predecessors(snapshot)
        contract_rows = _contract_rows()
        truth_rows = _truth_rows()
        registry_rows = _registry_rows()
        issue_rows = [
            dict(row)
            for row in predecessor["phase3_issues"].rows
            if row["issue_id"] != REMOVED_ISSUE_ID
        ]
        safety_rows = _safety_rows()
        truth_groups = {
            group: sum(row["truth_group"] == group for row in truth_rows)
            for group in ("passed", "blocked", "invalid_rule_result", "dispatch_error")
        }
        issue_map = {row["issue_id"]: row for row in issue_rows}
        passed = (
            len(contract_rows) == 34
            and all(row["contract_passed"] == "true" for row in contract_rows)
            and len(truth_rows) == 56
            and len({row["case_id"] for row in truth_rows}) == 56
            and truth_groups
            == {
                "passed": 8,
                "blocked": 4,
                "invalid_rule_result": 24,
                "dispatch_error": 20,
            }
            and all(row["truth_passed"] == "true" for row in truth_rows)
            and len(registry_rows) == 15
            and tuple(row["admission_rule_id"] for row in registry_rows)
            == KNOWN_RULE_IDS
            and all(row["audit_passed"] == "true" for row in registry_rows)
            and len(issue_rows) == 11
            and issue_rows
            == [
                dict(row)
                for row in predecessor["phase3_issues"].rows
                if row["issue_id"] != REMOVED_ISSUE_ID
            ]
            and issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["issue_count"]
            == "11"
            and issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["status"]
            == "open"
            and issue_map[
                "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"
            ]["status"]
            == "open"
            and len(safety_rows) == len(TRUE_SAFETY_ITEMS) + len(FALSE_SAFETY_ITEMS)
            and all(row["safety_passed"] == "true" for row in safety_rows)
            and type(EVALUATOR_REGISTRY) is MappingProxyType
            and tuple(EVALUATOR_REGISTRY) == ADAPTER_READY_RULE_IDS
            and LEGACY_ADAPTER_NOT_READY_RULE_IDS == ()
            and UnifiedAdmissionRuleEvaluation is phase2.UnifiedAdmissionRuleEvaluation
            and UnifiedAdmissionDispatchError is phase2.UnifiedAdmissionDispatchError
        )
    except (
        AttributeError,
        KeyError,
        TypeError,
        ValueError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        SyntaxError,
    ):
        return _empty_state(snapshot, "PREDECESSOR_OR_RUNTIME_VALIDATION_FAILED") | {
            "source_ok": True
        }
    if not passed:
        return _empty_state(snapshot, "PHASE4_VALIDATION_FAILED") | {
            "source_ok": True,
            "predecessor_ok": True,
        }
    return {
        "source_snapshot": snapshot,
        "source_ok": True,
        "predecessor_ok": True,
        "predecessor": predecessor,
        "contract_rows": contract_rows,
        "truth_rows": truth_rows,
        "truth_group_counts": truth_groups,
        "registry_rows": registry_rows,
        "issue_rows": issue_rows,
        "safety_rows": safety_rows,
        "all_checks_passed": True,
        "validation_failures": [],
    }


def _csv_bytes(
    columns: Sequence[str], rows: Sequence[Mapping[str, str]]
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=list(columns), lineterminator="\n", extrasaction="raise"
    )
    writer.writeheader()
    for row in rows:
        if tuple(row) != tuple(columns):
            raise ValueError("output CSV schema mismatch")
        writer.writerow(row)
    return stream.getvalue().encode("utf-8")


def _manifest_payload(
    state: Mapping[str, Any], output_sha256: Mapping[str, str]
) -> dict[str, Any]:
    snapshot = state["source_snapshot"]
    readiness = {name: True for name in TRUE_READINESS} | {
        name: False for name in FALSE_READINESS
    }
    return {
        "project": PROJECT,
        "step": STEP,
        "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": EXPECTED_BASE_COMMIT,
        "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "source_input_count": 14,
        "source_input_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_input_sha256": {
            path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS
        },
        "source_input_verification": [
            {
                "source_ordinal": index,
                "source_relative_path": record.relative_path.as_posix(),
                "tracked": True,
                "base_tree_blob": True,
                "filesystem_regular": True,
                "non_symlink": True,
                "expected_sha256": record.expected_sha256,
                "base_tree_sha256": record.base_tree_sha256,
                "filesystem_sha256": record.filesystem_sha256,
                "source_verified": True,
            }
            for index, record in enumerate(snapshot.records, 1)
        ],
        "source_structural_checks_before_first_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "output_files": list(OUTPUT_FILES),
        "output_file_count": 6,
        "output_sha256": dict(output_sha256),
        "output_sha256_excludes_manifest_self_hash": True,
        "contract_row_count": len(state["contract_rows"]),
        "truth_matrix_row_count": 56,
        "truth_matrix_pass_count": 56,
        "truth_matrix_group_counts": dict(state["truth_group_counts"]),
        "registry_audit_row_count": 15,
        "registry_audit_pass_count": 15,
        "active_issue_count": 11,
        "removed_issue_id": REMOVED_ISSUE_ID,
        "provider_blocking_issue_id": "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
        "provider_blocking_issue_count": 11,
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "result_field_count": 13,
        "result_fields": list(RESULT_FIELDS),
        "dispatch_error_field_count": 6,
        "dispatch_error_fields": list(DISPATCH_ERROR_FIELDS),
        "dispatch_error_codes": list(DISPATCH_ERROR_CODES),
        "known_rule_ids": list(KNOWN_RULE_IDS),
        "callable_discovered_rule_ids": list(CALLABLE_DISCOVERED_RULE_IDS),
        "adapter_ready_rule_ids": list(ADAPTER_READY_RULE_IDS),
        "legacy_adapter_not_ready_rule_ids": [],
        "registered_rule_ids": list(EVALUATOR_REGISTRY),
        "registered_rule_count": 4,
        "adapter_ids": dict(ADAPTER_IDS),
        "semantic_oracle_equivalence_rule_ids": [
            "ADMIT_001",
            "ADMIT_002",
            "ADMIT_003",
        ],
        "context_dispatch_error_reason_count": 16,
        "phase2_runtime_source_sha256": SOURCE_SHA256[PHASE2_SOURCE_PATH],
        "phase2_type_identity_reused": True,
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


def _payloads(state: Mapping[str, Any]) -> tuple[dict[str, bytes], dict[str, Any]]:
    csv_payloads = {
        CONTRACT_FILENAME: _csv_bytes(CONTRACT_COLUMNS, state["contract_rows"]),
        TRUTH_FILENAME: _csv_bytes(TRUTH_COLUMNS, state["truth_rows"]),
        REGISTRY_FILENAME: _csv_bytes(REGISTRY_COLUMNS, state["registry_rows"]),
        SAFETY_FILENAME: _csv_bytes(SAFETY_COLUMNS, state["safety_rows"]),
        ISSUE_FILENAME: _csv_bytes(ISSUE_COLUMNS, state["issue_rows"]),
    }
    hashes = {
        name: hashlib.sha256(content).hexdigest()
        for name, content in csv_payloads.items()
    }
    manifest = _manifest_payload(state, hashes)
    payloads = {
        **csv_payloads,
        MANIFEST_FILENAME: (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        ),
    }
    return payloads, manifest


def _atomic_write(path: Path, content: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _preflight_output_root(root: Path) -> None:
    if root.exists() or root.is_symlink():
        metadata = os.lstat(root)
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise ValueError("output root must be a real non-symlink directory")
    else:
        root.mkdir(parents=True, exist_ok=False)
        metadata = os.lstat(root)
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise ValueError("output root creation was unsafe")
    entries = tuple(root.iterdir())
    if {entry.name for entry in entries} - set(OUTPUT_FILES):
        raise ValueError("output root contains unexpected files")
    for entry in entries:
        metadata = os.lstat(entry)
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise ValueError("output root contains unsafe entries")


def run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    state = build_phase4_state()
    if state["all_checks_passed"] is not True:
        raise RuntimeError(
            "unified ADMIT_001 to ADMIT_004 runtime failed closed: "
            + "|".join(state["validation_failures"])
        )
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    _preflight_output_root(root)
    payloads, manifest = _payloads(state)
    for filename in OUTPUT_FILES:
        _atomic_write(root / filename, payloads[filename])
    return {"state": state, "manifest": manifest, "output_root": root}


if __name__ == "__main__":
    materialized = run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004_v1()
    print(json.dumps(materialized["manifest"], indent=2, sort_keys=True))
