#!/usr/bin/env python3
"""Independent fail-closed checker for the ADMIT_001-to-007 runtime."""

from __future__ import annotations

import ast
import csv
import hashlib
import inspect
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import MappingProxyType
from typing import Any
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007
    as runtime,
)


CHECKER_EXPECTED_BASE_COMMIT = "ea6678caef867bf2c4c0901bc4066f4d5e4f7520"
CHECKER_EXPECTED_BASE_SUBJECT = (
    "add CovaPIE ADMIT_007 unified adapter contract design v1"
)
CHECKER_PROJECT = "CovaPIE"
CHECKER_STEP = "unified dispatch runtime with ADMIT_001 to ADMIT_007 v1"
CHECKER_STAGE = (
    "covapie_bulk_download_admission_unified_dispatch_runtime_"
    "with_admit_001_to_007_v1"
)
CHECKER_MANIFEST_SCHEMA_VERSION = (
    "covapie_unified_dispatch_runtime_with_admit_001_to_007_manifest_v1"
)
CHECKER_RECOMMENDED_NEXT_STEP = (
    "audit_covapie_admit_008_formal_evaluator_interface_preconditions_v1"
)
CHECKER_SOURCE_BOUNDARY_NAME = (
    "fixed_ordered_minimal_exact18_committed_source_boundary"
)
CHECKER_SOURCE_BOUNDARY = (
    (
        Path("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006.py"),
        "fe00e617cfc99bf40eb44b13b66e4c14f08f2c764dd32820f03fd162f9049896",
    ),
    (
        Path("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006_v1/covapie_admit_001_to_006_runtime_manifest.json"),
        "359c666541602458b3ea6a023be95ea06205f8580ff71d371c25306715f558d6",
    ),
    (
        Path("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006_v1/covapie_admit_001_to_006_runtime_contract.csv"),
        "f9fa70076bb7cee1cd4ef6af7ad8bec76d0ef9a95a8d3305da55d96d5a259bcb",
    ),
    (
        Path("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006_v1/covapie_admit_001_to_006_runtime_truth_matrix.csv"),
        "bba064d245f88b274821d52617b7725a22b063d28afdf99d094c5d6dfec348ca",
    ),
    (
        Path("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006_v1/covapie_admit_001_to_006_registry_routing_and_oracle_audit.csv"),
        "beba9b44b65e1459d406506d05e31786174ddec786ffe31586e0d7188ff0f3a6",
    ),
    (
        Path("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006_v1/covapie_admit_001_to_006_runtime_safety_audit.csv"),
        "8b4eec9656a0c34dfc4e9fa480841543f14ab722e7bacfb4e4f1a895d5a7b636",
    ),
    (
        Path("src/covalent_ext/covapie_bulk_download_admission_admit_007_rule_logic_interface.py"),
        "ce5cbf09765e8b12db162458ca9518d71d431b175f3225e5558a8b57fdd133f6",
    ),
    (
        Path("data/derived/covalent_small/covapie_bulk_download_admission_admit_007_rule_logic_interface_v1/covapie_admit_007_rule_logic_interface_manifest.json"),
        "f5212100bf458372dd908a234557ee34858cf24cf2360e39b1e61cba8a562958",
    ),
    (
        Path("src/covalent_ext/covapie_bulk_download_admission_admit_007_unified_adapter_contract_design_gate.py"),
        "5c3171fb19efdafecad5258ce4d6c0185b731ab93dece947232d80ef089b4a88",
    ),
    (
        Path("data/derived/covalent_small/covapie_bulk_download_admission_admit_007_unified_adapter_contract_design_gate_v1/covapie_admit_007_unified_adapter_contract_manifest.json"),
        "9cb470520b666624ecbde992354c05587dd38c3006f1f21db4a2dfe3733a4eb4",
    ),
    (
        Path("data/derived/covalent_small/covapie_bulk_download_admission_admit_007_unified_adapter_contract_design_gate_v1/covapie_admit_007_unified_adapter_contract.csv"),
        "9c155462b7ffe83a172eb16dccde0da0c8c6be03fff93aa1a405aa9ca7b14537",
    ),
    (
        Path("data/derived/covalent_small/covapie_bulk_download_admission_admit_007_unified_adapter_contract_design_gate_v1/covapie_admit_007_candidate_projection_and_context_routing_matrix.csv"),
        "5cca82bac1f9e971b238735a9c8aad3c06f5876e32dad535f639645453720c59",
    ),
    (
        Path("data/derived/covalent_small/covapie_bulk_download_admission_admit_007_unified_adapter_contract_design_gate_v1/covapie_admit_007_unified_result_projection_truth_matrix.csv"),
        "0423420e0442f9d6ea7cf8b1befe319f0b6bc6527d1038a0a4f95883d982cddd",
    ),
    (
        Path("data/derived/covalent_small/covapie_bulk_download_admission_admit_007_unified_adapter_contract_design_gate_v1/covapie_admit_007_unified_adapter_safety_audit.csv"),
        "4641829cb8912cfbd9a84689feed03b2780baee199d13070cd0b97c8e90c9992",
    ),
    (
        Path("data/derived/covalent_small/covapie_bulk_download_admission_admit_007_unified_adapter_contract_design_gate_v1/covapie_admit_007_unified_adapter_issue_readiness_inventory.csv"),
        "e63c1b83fe245031ecdefa6b3387086b2aba8d72ef50189be17b9874e8f18196",
    ),
    (
        Path("src/covalent_ext/covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate.py"),
        "92267891cb8a51d2a919d6a6eaca6e6320de288f41ac75692a1c1e6fde2ceb76",
    ),
    (
        Path("data/derived/covalent_small/covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1/covapie_unified_admission_result_schema_and_outcome_contract.csv"),
        "b09d1bc265cae80296450390c3486a942a9ac16fbd689331770e74024f33bbfa",
    ),
    (
        Path("data/derived/covalent_small/covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1/covapie_unified_admission_evaluator_and_context_routing_matrix.csv"),
        "2d09f6ab5aa9c64419e7e7c4a90f6562a2883007f9b3ef82258a69b9df181b05",
    ),
)
CHECKER_DESIGN_ISSUE_PATH = CHECKER_SOURCE_BOUNDARY[14][0]
CHECKER_DESIGN_ISSUE_SHA256 = CHECKER_SOURCE_BOUNDARY[14][1]
CHECKER_CONTRACT_FILENAME = "covapie_admit_001_to_007_runtime_contract.csv"
CHECKER_TRUTH_FILENAME = "covapie_admit_001_to_007_runtime_truth_matrix.csv"
CHECKER_REGISTRY_FILENAME = (
    "covapie_admit_001_to_007_registry_routing_and_oracle_audit.csv"
)
CHECKER_SAFETY_FILENAME = "covapie_admit_001_to_007_runtime_safety_audit.csv"
CHECKER_ISSUE_FILENAME = "covapie_admit_001_to_007_runtime_issue_inventory.csv"
CHECKER_MANIFEST_FILENAME = "covapie_admit_001_to_007_runtime_manifest.json"
CHECKER_CSV_OUTPUTS = (
    CHECKER_CONTRACT_FILENAME,
    CHECKER_TRUTH_FILENAME,
    CHECKER_REGISTRY_FILENAME,
    CHECKER_SAFETY_FILENAME,
    CHECKER_ISSUE_FILENAME,
)
CHECKER_OUTPUT_FILES = (*CHECKER_CSV_OUTPUTS, CHECKER_MANIFEST_FILENAME)
CHECKER_RUNTIME_DEPENDENCY_IMPORTS = (
    "exact6_unified_runtime_predecessor",
    "admit007_standalone_evaluator",
    "admit007_committed_independent_enum_oracle",
)
CHECKER_RUNTIME_DEPENDENCY_MODULES = (
    "covalent_ext.covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006",
    "covalent_ext.covapie_bulk_download_admission_admit_007_rule_logic_interface",
    "covalent_ext.covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate",
)
CHECKER_CONTRACT_HEADER = (
    "contract_id",
    "contract_area",
    "contract_statement",
    "expected_value",
    "observed_value",
    "contract_passed",
)
CHECKER_TRUTH_HEADER = (
    "case_id",
    "case_group",
    "admission_rule_id",
    "behavior",
    "expected_result_or_error",
    "observed_result_or_error",
    "expected_reason",
    "observed_reason",
    "formal_call_count",
    "oracle_call_count",
    "candidate_access_status",
    "predecessor_handler_identity_status",
    "case_passed",
)
CHECKER_REGISTRY_HEADER = (
    "admission_rule_id",
    "admission_rule_name",
    "adapter_id",
    "known_rule",
    "callable_discovered",
    "adapter_ready",
    "registered",
    "predecessor_handler_identity_reused",
    "successor_handler_implemented",
    "expected_dispatch_behavior",
    "audit_passed",
)
CHECKER_SAFETY_HEADER = (
    "safety_item",
    "expected_executed",
    "observed_executed",
    "safety_passed",
)
CHECKER_ISSUE_HEADER = (
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
)


EXPECTED_OUTPUT_SHA256 = {
    "covapie_admit_001_to_007_runtime_contract.csv": "d3a1ad40803ceb25f30e106bbab44ab11cfcc26717b7c244266ab1ce1378f29d",
    "covapie_admit_001_to_007_runtime_truth_matrix.csv": "149b838e9fe8254df7ba7a610ae64377cb7c7a41da8010cedee4722dcea081b5",
    "covapie_admit_001_to_007_registry_routing_and_oracle_audit.csv": "1dbb5453277a93dff5d7612715c5fdd5edfde0d63cf114802220f962e22118f3",
    "covapie_admit_001_to_007_runtime_safety_audit.csv": "97fba54037625b78a82b17753b77870366f8c3fa492ee506923ed3ca369c9f88",
    "covapie_admit_001_to_007_runtime_issue_inventory.csv": "47de07417697808b044d30260f153ec7e5d46fb7c5b0e2c1f41187bcb09b89a0",
    "covapie_admit_001_to_007_runtime_manifest.json": "0a4cb44812ff5398ffba9a077f1217db3da3624d870922eec87848b60091c96e",
}
CHECKER_MANIFEST_OUTPUT_SHA256 = {
    name: EXPECTED_OUTPUT_SHA256[name] for name in CHECKER_CSV_OUTPUTS
}
KNOWN_RULE_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
REGISTERED_RULE_IDS = KNOWN_RULE_IDS[:7]
CANDIDATE_FIELD = "covalent_event_evidence_source"
CONTEXT_ITEM = "allowed_covalent_evidence_classes"
ENUM_MEMBERS = (
    "explicit_structure_bond_record",
    "explicit_curated_covalent_annotation",
    "distance_only_inference",
)
ALLOWED_CLASSES = ENUM_MEMBERS[:2]
SCALAR_REASONS = (
    "COVALENT_EVENT_EVIDENCE_SOURCE_TYPE_INVALID",
    "COVALENT_EVENT_EVIDENCE_SOURCE_EMPTY",
    "COVALENT_EVENT_EVIDENCE_SOURCE_NON_ASCII",
    "COVALENT_EVENT_EVIDENCE_SOURCE_SYNTAX_INVALID",
    "COVALENT_EVENT_EVIDENCE_SOURCE_UNKNOWN",
)
CONTEXT_REASONS = (
    "ALLOWED_COVALENT_EVIDENCE_CLASSES_TYPE_INVALID",
    "ALLOWED_COVALENT_EVIDENCE_CLASSES_CONTENT_INVALID",
)
BLOCKED_REASON = "DISTANCE_ONLY_INFERENCE_NOT_ADMISSIBLE"
RESULT_FIELDS = (
    "schema_version",
    "admission_rule_id",
    "admission_rule_name",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "normalized_values",
    "validated_candidate_fields",
    "consumed_candidate_fields",
    "consumed_context_items",
    "evaluator_io_used",
    "adapter_id",
)
ERROR_FIELDS = (
    "code",
    "admission_rule_id",
    "known_rule",
    "callable_discovered",
    "adapter_ready",
    "reason",
)
DISPATCH_ERROR_CODES = (
    "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID",
    "UNIFIED_ADMISSION_RULE_ID_UNKNOWN",
    "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
    "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
    "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
)
OUTCOME_VOCABULARY = ("passed", "blocked", "invalid", "rejected")
RESULT_SCHEMA_VERSION = "covapie_unified_admission_rule_evaluation_v1"
TRUTH_GROUP_COUNTS = {
    "global_dispatch": 5,
    "predecessor_identity_and_behavior": 14,
    "context_routing": 7,
    "candidate_envelope": 12,
    "standalone_semantics": 37,
    "source_fail_closed": 15,
    "projection_semantics": 7,
    "unsupported_boundary": 10,
}
RULE_NAMES = {
    "ADMIT_001": "unique_candidate_identity",
    "ADMIT_002": "valid_pdb_id_format",
    "ADMIT_003": "ligand_or_het_identity_present",
    "ADMIT_004": "covalent_residue_identity_present",
    "ADMIT_005": "cys_sg_scope_only_v1",
    "ADMIT_006": "explicit_covalent_event_evidence",
    "ADMIT_007": "distance_only_inference_forbidden",
}
ADAPTER_IDS = {
    rule_id: f"covapie_admit_{index:03d}_unified_adapter_v1"
    for index, rule_id in enumerate(REGISTERED_RULE_IDS, 1)
}
CHECKER_TRUE_READINESS = frozenset(
    {
        "unified_dispatch_runtime_admit_001_to_007_implemented",
        "evaluate_admission_rule_implemented",
        "evaluator_registry_runtime_implemented",
        "registered_rule_count_is_7",
        "callable_discovered_rule_count_is_7",
        "adapter_ready_rule_count_is_7",
        "first_six_handler_identity_reused",
        "admit_007_adapter_implemented",
        "admit_007_registered_in_engine",
        "admit_007_candidate_projection_runtime_enforced",
        "admit_007_context_routing_runtime_enforced",
        "admit_007_missing_field_value_runtime_enforced",
        "admit_007_source_prevalidation_before_oracle_runtime_enforced",
        "admit_007_semantic_oracle_equivalence_runtime_enforced",
        "admit_007_blocked_passthrough_runtime_enforced",
        "admit_007_context_invalid_partial_canonical_projection_runtime_enforced",
        "unsupported_rule_fail_closed_runtime_implemented",
        "synthetic_runtime_truth_matrix_passed",
        "ready_for_admit_008_formal_evaluator_interface_preconditions_audit",
        "feature_semantics_audit_required_before_training",
    }
)
CHECKER_FALSE_READINESS = frozenset(
    {
        "predecessor_exact6_runtime_modified",
        "admit_008_standalone_evaluator_implemented",
        "admit_008_unified_adapter_contract_frozen",
        "admit_008_unified_adapter_implemented",
        "admit_008_registered_in_engine",
        "admit_008_to_015_registered_in_engine",
        "all_15_rules_covered",
        "evaluate_all_rules_implemented",
        "combined_candidate_verdict_contract_frozen",
        "combined_candidate_verdict_implemented",
        "cross_rule_precedence_frozen",
        "real_provider_enum_mapping_validated",
        "real_candidate_evaluation",
        "exact11_real_rows_evaluated",
        "ready_for_bulk_download_now",
        "ready_for_training",
        "ready_to_train_now",
    }
)


class _StringSubclass(str):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    reader = csv.DictReader(
        io.StringIO(path.read_text(encoding="utf-8"), newline="")
    )
    if reader.fieldnames is None:
        raise AssertionError(f"CSV header missing: {path.name}")
    rows = [dict(row) for row in reader]
    if any(tuple(row) != tuple(reader.fieldnames) for row in rows):
        raise AssertionError(f"CSV row shape mismatch: {path.name}")
    return tuple(reader.fieldnames), rows


def _expected_source_boundary() -> tuple[tuple[Path, str], ...]:
    return CHECKER_SOURCE_BOUNDARY


def _expected_output_filenames() -> tuple[str, ...]:
    return CHECKER_OUTPUT_FILES


def _expected_headers() -> dict[str, tuple[str, ...]]:
    return {
        CHECKER_CONTRACT_FILENAME: CHECKER_CONTRACT_HEADER,
        CHECKER_TRUTH_FILENAME: CHECKER_TRUTH_HEADER,
        CHECKER_REGISTRY_FILENAME: CHECKER_REGISTRY_HEADER,
        CHECKER_SAFETY_FILENAME: CHECKER_SAFETY_HEADER,
        CHECKER_ISSUE_FILENAME: CHECKER_ISSUE_HEADER,
    }


def _expected_readiness() -> dict[str, bool]:
    return {name: True for name in sorted(CHECKER_TRUE_READINESS)} | {
        name: False for name in sorted(CHECKER_FALSE_READINESS)
    }


def _expected_manifest() -> dict[str, object]:
    boundary = _expected_source_boundary()
    paths = [path.as_posix() for path, _ in boundary]
    source_sha = {path.as_posix(): digest for path, digest in boundary}
    readiness = _expected_readiness()
    return {
        "project": CHECKER_PROJECT,
        "step": CHECKER_STEP,
        "stage": CHECKER_STAGE,
        "manifest_schema_version": CHECKER_MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": CHECKER_EXPECTED_BASE_COMMIT,
        "expected_base_subject": CHECKER_EXPECTED_BASE_SUBJECT,
        "source_boundary_name": CHECKER_SOURCE_BOUNDARY_NAME,
        "source_input_count": 18,
        "source_input_paths": paths,
        "source_input_sha256": source_sha,
        "source_input_verification": [
            {
                "source_ordinal": ordinal,
                "source_relative_path": path.as_posix(),
                "tracked": True,
                "base_tree_blob": True,
                "filesystem_regular": True,
                "non_symlink": True,
                "expected_sha256": digest,
                "base_tree_sha256": digest,
                "filesystem_sha256": digest,
                "source_verified": True,
            }
            for ordinal, (path, digest) in enumerate(boundary, 1)
        ],
        "runtime_dependency_imports_authorized": True,
        "runtime_dependency_imports": list(CHECKER_RUNTIME_DEPENDENCY_IMPORTS),
        "adapter_design_gate_imported_by_runtime": False,
        "frozen_source_snapshot_explicit_byte_reads_preflighted": True,
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "output_files": list(_expected_output_filenames()),
        "output_file_count": 6,
        "output_sha256": dict(CHECKER_MANIFEST_OUTPUT_SHA256),
        "output_sha256_excludes_manifest_self_hash": True,
        "checker_freezes_all_six_output_sha256": True,
        "contract_row_count": 56,
        "truth_matrix_row_count": 107,
        "truth_matrix_pass_count": 107,
        "truth_matrix_group_counts": dict(TRUTH_GROUP_COUNTS),
        "registry_audit_row_count": 15,
        "registry_audit_pass_count": 15,
        "safety_audit_row_count": 36,
        "active_issue_count": 11,
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "result_field_count": 13,
        "result_fields": list(RESULT_FIELDS),
        "dispatch_error_field_count": 6,
        "dispatch_error_fields": list(ERROR_FIELDS),
        "dispatch_error_codes": list(DISPATCH_ERROR_CODES),
        "outcome_vocabulary": list(OUTCOME_VOCABULARY),
        "known_rule_ids": list(KNOWN_RULE_IDS),
        "callable_discovered_rule_ids": list(REGISTERED_RULE_IDS),
        "adapter_ready_rule_ids": list(REGISTERED_RULE_IDS),
        "legacy_adapter_not_ready_rule_ids": [],
        "registered_rule_count": 7,
        "registered_rule_ids": list(REGISTERED_RULE_IDS),
        "adapter_ids": dict(ADAPTER_IDS),
        "predecessor_exact6_runtime_modified": False,
        "predecessor_handlers_reused_by_identity": True,
        "admit_007_implemented": True,
        "admit_007_registered": True,
        "admit_008_to_015_registered": False,
        "feature_semantics_audit_required": True,
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
        "recommended_next_step": CHECKER_RECOMMENDED_NEXT_STEP,
    }


def _expected_contract_rows() -> list[dict[str, str]]:
    signature = (
        "(admission_rule_id: 'str', candidate_record: 'Mapping[str, object]', *, "
        "batch_context: 'Mapping[str, object] | None' = None, evaluation_context: "
        "'Mapping[str, object] | None' = None, download_result_context: "
        "'Mapping[str, object] | None' = None, stage_authorization_context: "
        "'Mapping[str, object] | None' = None) -> 'UnifiedAdmissionRuleEvaluation'"
    )
    definitions = (
        ("TYPE_001", "type_identity", "result type identity", "true"),
        ("TYPE_002", "type_identity", "dispatch error type identity", "true"),
        ("TYPE_003", "type_identity", "Exact13 fields", "|".join(RESULT_FIELDS)),
        ("TYPE_004", "type_identity", "Exact6 fields", "|".join(ERROR_FIELDS)),
        ("TYPE_005", "type_identity", "result schema", "covapie_unified_admission_rule_evaluation_v1"),
        ("TYPE_006", "type_identity", "outcome vocabulary", "passed|blocked|invalid|rejected"),
        ("API_001", "public_api", "signature", signature),
        ("API_002", "public_api", "dispatch cardinality", "single_rule_only"),
        ("API_003", "public_api", "combined verdict", "excluded"),
        ("DISPATCH_001", "global_dispatch", "precedence", "exact_str|known|registered|handler"),
        ("REGISTRY_001", "registry", "immutable registry", "true"),
        ("REGISTRY_002", "registry", "registered IDs", "|".join(REGISTERED_RULE_IDS)),
        ("REGISTRY_003", "registry", "registered count", "7"),
        ("REGISTRY_004", "registry", "callable discovered count", "7"),
        ("REGISTRY_005", "registry", "adapter ready count", "7"),
        ("REUSE_001", "predecessor_reuse", "first six handler identity", "true"),
        ("REUSE_002", "predecessor_reuse", "first six names and adapters", "true"),
        ("A007_001", "admit007_identity", "rule name", "distance_only_inference_forbidden"),
        ("A007_002", "admit007_identity", "adapter ID", "covapie_admit_007_unified_adapter_v1"),
        ("CONTEXT_001", "context_routing", "precedence", "batch|evaluation_mapping|evaluation_key|download_result|stage_authorization"),
        ("CONTEXT_002", "context_routing", "evaluation Mapping subclass", "accepted"),
        ("CONTEXT_003", "context_routing", "evaluation extra keys", "ignored"),
        ("CONTEXT_004", "context_routing", "required value", "original_identity_single_lookup_no_prevalidation"),
        ("CONTEXT_005", "context_routing", "candidate access before routing", "false"),
        ("CANDIDATE_001", "candidate_projection", "field", CANDIDATE_FIELD),
        ("CANDIDATE_002", "candidate_projection", "Mapping subclasses", "accepted"),
        ("CANDIDATE_003", "candidate_projection", "extra fields", "ignored"),
        ("CANDIDATE_004", "candidate_projection", "non Mapping reason", "ADMIT_007_CANDIDATE_RECORD_MAPPING_INVALID"),
        ("CANDIDATE_005", "candidate_projection", "consumed context retained", "true"),
        ("MISSING_001", "missing", "missing key", "covalent_event_evidence_missing"),
        ("MISSING_002", "missing", "exact None", "covalent_event_evidence_missing"),
        ("MISSING_003", "missing", "exact built-in empty str", "covalent_event_evidence_missing"),
        ("MISSING_004", "missing", "empty str subclass", "not_missing"),
        ("FORMAL_001", "formal_evaluator", "positional original objects", "single_candidate_lookup_single_context_lookup_exact_positional_call"),
        ("FORMAL_002", "formal_evaluator", "normalization", "none"),
        ("FORMAL_003", "formal_evaluator", "I/O", "false"),
        ("SOURCE_001", "source_prevalidation", "exact source type", "required"),
        ("SOURCE_002", "source_prevalidation", "source subclass", "rejected"),
        ("SOURCE_003", "source_prevalidation", "Exact10 reconstruction", "exact_storage_keys_and_reconstruction_before_oracle"),
        ("SOURCE_004", "source_prevalidation", "failure adapter readiness", "false"),
        ("ORACLE_001", "semantic_oracle", "identity", "classify_admit_006_admit_007_evidence_design"),
        ("ORACLE_002", "semantic_oracle", "original objects", "exact_once"),
        ("ORACLE_003", "semantic_oracle", "complete Exact10 equality", "required"),
        ("PROJECTION_001", "exact13", "normalized from validated", "true"),
        ("PROJECTION_002", "exact13", "blocked passthrough", "true"),
        ("PROJECTION_003", "exact13", "context invalid canonical retained", "true"),
        ("PROJECTION_004", "exact13", "partial result on failure", "false"),
        ("SAFETY_001", "runtime_safety", "candidate mutation", "false"),
        ("SAFETY_002", "runtime_safety", "evaluation context mutation", "false"),
        ("SAFETY_003", "runtime_safety", "public runtime metadata I/O", "false"),
        ("SAFETY_004", "runtime_safety", "real evaluation/download/training", "false"),
        ("BOUNDARY_001", "boundary", "ADMIT_008 to ADMIT_015 registered", "false"),
        ("BOUNDARY_002", "boundary", "evaluate_all_rules", "excluded"),
        ("BOUNDARY_003", "boundary", "combined verdict", "excluded"),
        ("BOUNDARY_004", "boundary", "provider mapping and real evaluation", "excluded"),
        ("BOUNDARY_005", "boundary", "download and training", "excluded"),
    )
    return [
        {
            "contract_id": identifier,
            "contract_area": area,
            "contract_statement": statement,
            "expected_value": value,
            "observed_value": value,
            "contract_passed": "true",
        }
        for identifier, area, statement, value in definitions
    ]


def _truth_row(
    case_id: str,
    group: str,
    rule_id: str,
    behavior: str,
    value: str,
    reason: str,
    *,
    formal: int = 0,
    oracle: int = 0,
    access: str = "not_applicable",
    identity: str = "not_applicable",
) -> dict[str, str]:
    return {
        "case_id": case_id,
        "case_group": group,
        "admission_rule_id": rule_id,
        "behavior": behavior,
        "expected_result_or_error": value,
        "observed_result_or_error": value,
        "expected_reason": reason,
        "observed_reason": reason,
        "formal_call_count": str(formal),
        "oracle_call_count": str(oracle),
        "candidate_access_status": access,
        "predecessor_handler_identity_status": identity,
        "case_passed": "true",
    }


def _classify(scalar: object, context: object) -> tuple[str, str]:
    import re

    if type(scalar) is not str:
        return "invalid", SCALAR_REASONS[0]
    if scalar == "":
        return "invalid", SCALAR_REASONS[1]
    if not scalar.isascii():
        return "invalid", SCALAR_REASONS[2]
    if re.fullmatch(r"[a-z][a-z0-9_]{0,63}", scalar, re.ASCII) is None:
        return "invalid", SCALAR_REASONS[3]
    if scalar not in ENUM_MEMBERS:
        return "invalid", SCALAR_REASONS[4]
    if type(context) is not tuple:
        return "invalid", CONTEXT_REASONS[0]
    if any(type(member) is not str for member in context) or context != ALLOWED_CLASSES:
        return "invalid", CONTEXT_REASONS[1]
    if scalar == ENUM_MEMBERS[2]:
        return "blocked", BLOCKED_REASON
    return "passed", ""


def _exact37_definitions() -> tuple[tuple[str, object, object], ...]:
    scalar_cases: tuple[tuple[str, object], ...] = (
        ("canonical_structure_bond", ENUM_MEMBERS[0]),
        ("canonical_curated_annotation", ENUM_MEMBERS[1]),
        ("canonical_distance_only", ENUM_MEMBERS[2]),
        ("type_none", None),
        ("type_int", 7),
        ("type_bool", True),
        ("type_str_subclass", _StringSubclass(ENUM_MEMBERS[0])),
        ("type_list", [ENUM_MEMBERS[0]]),
        ("type_mapping", {"value": ENUM_MEMBERS[0]}),
        ("empty", ""),
        ("whitespace_only", " "),
        ("leading_whitespace", " explicit_structure_bond_record"),
        ("trailing_whitespace", "explicit_structure_bond_record "),
        ("uppercase", "Explicit_structure_bond_record"),
        ("hyphen", "explicit-structure-bond-record"),
        ("dot", "explicit.structure"),
        ("slash", "explicit/structure"),
        ("non_ascii", "explicit_évidence"),
        ("over_length", "a" * 65),
        ("leading_digit", "1explicit"),
        ("unknown_valid", "unregistered_value"),
        ("unknown_explicit_looking", "explicit_database_bond"),
        ("unknown_manual_review", "manual_review"),
        ("unknown_other", "other"),
        ("unknown_unknown", "unknown"),
    )
    context_cases: tuple[tuple[str, object], ...] = (
        ("context_exact_tuple", ALLOWED_CLASSES),
        ("context_none", None),
        ("context_list", list(ALLOWED_CLASSES)),
        ("context_set", set(ALLOWED_CLASSES)),
        ("context_frozenset", frozenset(ALLOWED_CLASSES)),
        ("context_wrong_order", tuple(reversed(ALLOWED_CLASSES))),
        ("context_missing_member", ALLOWED_CLASSES[:1]),
        ("context_duplicate", (ALLOWED_CLASSES[0], ALLOWED_CLASSES[0])),
        ("context_distance_only", (*ALLOWED_CLASSES, ENUM_MEMBERS[2])),
        ("context_unknown", (*ALLOWED_CLASSES, "unknown")),
        ("context_str_subclass", (_StringSubclass(ALLOWED_CLASSES[0]), ALLOWED_CLASSES[1])),
        ("context_extra_member", (*ALLOWED_CLASSES, "explicit_database_bond")),
    )
    values = [(name, scalar, ALLOWED_CLASSES) for name, scalar in scalar_cases]
    values.extend((name, ENUM_MEMBERS[0], context) for name, context in context_cases)
    return tuple(values)


def _expected_truth_rows() -> list[dict[str, str]]:
    rows = [
        _truth_row("GLOBAL_NON_STR", "global_dispatch", "6", "global_precedence", "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID"),
        _truth_row("GLOBAL_STR_SUBCLASS", "global_dispatch", "ADMIT_007", "global_precedence", "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID"),
        _truth_row("GLOBAL_UNKNOWN", "global_dispatch", "ADMIT_999", "global_precedence", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN"),
        _truth_row("GLOBAL_KNOWN_UNREGISTERED", "global_dispatch", "ADMIT_008", "global_precedence", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED"),
        _truth_row("GLOBAL_PRECEDENCE", "global_dispatch", "ADMIT_999", "global_precedence", "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID"),
    ]
    for rule_id in KNOWN_RULE_IDS[:6]:
        rows.append(
            _truth_row(
                f"PRED_IDENTITY_{rule_id}",
                "predecessor_identity_and_behavior",
                rule_id,
                "handler_identity",
                "identity_reused",
                "",
                identity="true",
            )
        )
    for case_id, rule_id, value, reason in (
        ("PRED_BEHAVIOR_P4_A001_PASS", "ADMIT_001", "passed", ""),
        ("PRED_BEHAVIOR_P4_A002_PASS", "ADMIT_002", "passed", ""),
        ("PRED_BEHAVIOR_P4_A003_PASS", "ADMIT_003", "passed", ""),
        ("PRED_BEHAVIOR_P4_A004_PASS", "ADMIT_004", "passed", ""),
        ("PRED_BEHAVIOR_P5_A005_PASS", "ADMIT_005", "passed", ""),
        ("PRED_BEHAVIOR_P5_A005_REJECT", "ADMIT_005", "rejected", "ADMIT_005_CYS_SG_SCOPE_REJECTED"),
        ("PRED_BEHAVIOR_P6_A006_EXPLICIT_PASS", "ADMIT_006", "passed", ""),
        ("PRED_BEHAVIOR_P6_A006_DISTANCE_BLOCKED", "ADMIT_006", "blocked", "COVALENT_EVENT_EVIDENCE_NOT_EXPLICIT"),
    ):
        rows.append(
            _truth_row(
                case_id,
                "predecessor_identity_and_behavior",
                rule_id,
                "representative_parity",
                value,
                reason,
                identity="true",
            )
        )
    for case_id, reason in (
        ("A007_CONTEXT_BATCH", "ADMIT_007_BATCH_CONTEXT_MUST_BE_NONE"),
        ("A007_CONTEXT_EVALUATION", "ADMIT_007_EVALUATION_CONTEXT_MAPPING_REQUIRED"),
        ("A007_CONTEXT_KEY", "ADMIT_007_ALLOWED_COVALENT_EVIDENCE_CLASSES_REQUIRED"),
        ("A007_CONTEXT_DOWNLOAD", "ADMIT_007_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"),
        ("A007_CONTEXT_STAGE", "ADMIT_007_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
        ("A007_CONTEXT_MULTI_PRECEDENCE", "ADMIT_007_BATCH_CONTEXT_MUST_BE_NONE"),
    ):
        rows.append(
            _truth_row(
                case_id,
                "context_routing",
                "ADMIT_007",
                "ordered_context_failure",
                "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
                reason,
                access="not_accessed",
            )
        )
    rows.append(
        _truth_row(
            "A007_CONTEXT_CANDIDATE_BOMB",
            "context_routing",
            "ADMIT_007",
            "candidate_not_accessed",
            "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
            "ADMIT_007_BATCH_CONTEXT_MUST_BE_NONE",
            access="not_accessed",
        )
    )
    for case_id, value, reason, formal, oracle, access in (
        ("A007_CANDIDATE_NON_MAPPING", "invalid", "ADMIT_007_CANDIDATE_RECORD_MAPPING_INVALID", 0, 0, "envelope_checked"),
        ("A007_CANDIDATE_KEY_MISSING", "invalid", "covalent_event_evidence_missing", 0, 0, "value_read_once"),
        ("A007_CANDIDATE_NONE", "invalid", "covalent_event_evidence_missing", 0, 0, "value_read_once"),
        ("A007_CANDIDATE_EMPTY", "invalid", "covalent_event_evidence_missing", 0, 0, "value_read_once"),
        ("A007_CANDIDATE_EMPTY_SUBCLASS", "invalid", SCALAR_REASONS[0], 1, 1, "value_read_once"),
        ("A007_CANDIDATE_WHITESPACE", "invalid", SCALAR_REASONS[3], 1, 1, "value_read_once"),
        ("A007_CANDIDATE_MALFORMED", "invalid", SCALAR_REASONS[0], 1, 1, "value_read_once"),
        ("A007_CANDIDATE_DISTANCE", "blocked", BLOCKED_REASON, 1, 1, "value_read_once"),
        ("A007_CANDIDATE_MAPPING_SUBCLASS", "passed", "", 1, 1, "value_read_once"),
        ("A007_CANDIDATE_EXTRA_FIELDS", "passed", "", 1, 1, "value_read_once"),
        ("A007_CANDIDATE_NO_MUTATION", "passed", "", 1, 1, "value_read_once"),
        ("A007_CANDIDATE_IDENTITY", "invalid", SCALAR_REASONS[0], 1, 1, "value_read_once"),
    ):
        rows.append(
            _truth_row(
                case_id,
                "candidate_envelope",
                "ADMIT_007",
                "candidate_projection_and_missing",
                value,
                reason,
                formal=formal,
                oracle=oracle,
                access=access,
            )
        )
    for index, (name, scalar, context) in enumerate(_exact37_definitions(), 1):
        if scalar is None or (type(scalar) is str and scalar == ""):
            value, reason, formal, oracle = "invalid", "covalent_event_evidence_missing", 0, 0
        else:
            value, reason = _classify(scalar, context)
            formal = oracle = 1
        rows.append(
            _truth_row(
                f"A007_EXACT37_{index:03d}_{name}",
                "standalone_semantics",
                "ADMIT_007",
                "runtime_exact37_path",
                value,
                reason,
                formal=formal,
                oracle=oracle,
                access="value_read_once",
            )
        )
    for suffix, reason in (
        ("SOURCE_WRONG_TYPE", "ADMIT_007_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"),
        ("SOURCE_SUBCLASS", "ADMIT_007_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"),
        ("SOURCE_MISSING_SHAPE", "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        ("SOURCE_EXTRA_SHAPE", "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        ("SOURCE_RULE_ID", "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        ("SOURCE_OUTCOME", "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        ("SOURCE_PASSED", "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        ("SOURCE_BLOCKS", "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        ("SOURCE_REASON", "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        ("SOURCE_CANONICAL", "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        ("SOURCE_VALIDATED", "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        ("SOURCE_CONSUMED_CANDIDATE", "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        ("SOURCE_CONSUMED_CONTEXT", "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        ("SOURCE_IO", "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
    ):
        rows.append(
            _truth_row(
                f"A007_{suffix}",
                "source_fail_closed",
                "ADMIT_007",
                "source_prevalidation_before_oracle",
                "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
                reason,
                formal=1,
                access="value_read_once",
            )
        )
    rows.append(
        _truth_row(
            "A007_SOURCE_ORACLE_MISMATCH",
            "source_fail_closed",
            "ADMIT_007",
            "complete_exact10_mismatch_no_projection",
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
            formal=1,
            oracle=1,
            access="value_read_once",
        )
    )
    for case_id, behavior, value, reason, formal, oracle, access in (
        ("PROJECTION_EXPLICIT_STRUCTURE", "exact10_to_exact13", "passed", "", 1, 1, "value_read_once"),
        ("PROJECTION_EXPLICIT_CURATED", "exact10_to_exact13", "passed", "", 1, 1, "value_read_once"),
        ("PROJECTION_DISTANCE_BLOCKED", "exact10_to_exact13", "blocked", BLOCKED_REASON, 1, 1, "value_read_once"),
        ("PROJECTION_SCALAR_INVALID", "exact10_to_exact13", "invalid", SCALAR_REASONS[4], 1, 1, "value_read_once"),
        ("PROJECTION_CONTEXT_INVALID_CANONICAL", "exact10_to_exact13", "invalid", CONTEXT_REASONS[0], 1, 1, "value_read_once"),
        ("PROJECTION_MISSING", "adapter_generated_exact13", "invalid", "covalent_event_evidence_missing", 0, 0, "envelope_checked"),
        ("PROJECTION_NON_MAPPING", "adapter_generated_exact13", "invalid", "ADMIT_007_CANDIDATE_RECORD_MAPPING_INVALID", 0, 0, "envelope_checked"),
    ):
        rows.append(
            _truth_row(
                case_id,
                "projection_semantics",
                "ADMIT_007",
                behavior,
                value,
                reason,
                formal=formal,
                oracle=oracle,
                access=access,
            )
        )
    for rule_id in KNOWN_RULE_IDS[7:]:
        rows.append(
            _truth_row(
                f"UNSUPPORTED_{rule_id}",
                "unsupported_boundary",
                rule_id,
                "known_not_registered_fail_closed",
                "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
                "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
            )
        )
    rows.extend(
        (
            _truth_row("UNSUPPORTED_NO_EVALUATE_ALL", "unsupported_boundary", "", "public_boundary_absent", "absent", ""),
            _truth_row("UNSUPPORTED_NO_COMBINED_VERDICT", "unsupported_boundary", "", "public_boundary_absent", "absent", ""),
        )
    )
    if Counter(row["case_group"] for row in rows) != TRUTH_GROUP_COUNTS:
        raise AssertionError("checker truth group construction failed")
    return rows


def _expected_registry_rows() -> list[dict[str, str]]:
    rows = []
    for rule_id in KNOWN_RULE_IDS:
        registered = rule_id in REGISTERED_RULE_IDS
        rows.append(
            {
                "admission_rule_id": rule_id,
                "admission_rule_name": RULE_NAMES.get(rule_id, ""),
                "adapter_id": ADAPTER_IDS.get(rule_id, ""),
                "known_rule": "true",
                "callable_discovered": str(registered).lower(),
                "adapter_ready": str(registered).lower(),
                "registered": str(registered).lower(),
                "predecessor_handler_identity_reused": str(rule_id in KNOWN_RULE_IDS[:6]).lower(),
                "successor_handler_implemented": str(rule_id == "ADMIT_007").lower(),
                "expected_dispatch_behavior": "registered_single_rule_runtime" if registered else "known_not_registered_fail_closed",
                "audit_passed": "true",
            }
        )
    return rows


def _expected_issue_rows(
    authoritative_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    rows = [dict(row) for row in authoritative_rows]
    matches = [
        row
        for row in rows
        if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
    ]
    if len(rows) != 11 or len(matches) != 1:
        raise AssertionError("authoritative Exact11 issue shape mismatch")
    coverage = matches[0]
    coverage["status"] = "open"
    coverage["affected_rules"] = "|".join(KNOWN_RULE_IDS[7:])
    coverage["integration_transition"] = (
        "admit_007_implemented_and_removed_from_open_coverage_scope"
    )
    coverage["issue_count"] = "1"
    return rows


def _expected_safety_rows() -> list[dict[str, str]]:
    positive = (
        "exact18_source_verification",
        "predecessor_exact6_handler_identity_reuse",
        "successor_exact7_registry_construction",
        "admit_007_adapter_implementation",
        "candidate_projection",
        "context_routing",
        "missing_field_value_classification",
        "formal_source_prevalidation",
        "independent_oracle_equivalence",
        "exact13_construction",
        "blocked_passthrough",
        "context_invalid_partial_canonical_projection",
        "synthetic_runtime_truth",
        "coverage_issue_update",
    )
    negative = (
        "predecessor_exact6_runtime_modification",
        "standalone_source_modification",
        "adapter_design_source_modification",
        "enum_design_source_modification",
        "admit_008_implementation",
        "admit_008_registration",
        "admit_008_to_015_registration",
        "evaluate_all_rules",
        "combined_candidate_verdict",
        "cross_rule_aggregation",
        "provider_mapping",
        "real_candidate_evaluation",
        "exact11_real_evaluation",
        "raw_read",
        "structure_parser",
        "network",
        "bulk_download",
        "checkpoint",
        "torch_numpy_rdkit",
        "model_forward_loss_training",
        "fine_tune",
        "parameter_update",
    )
    return [
        {
            "safety_item": item,
            "expected_executed": expected,
            "observed_executed": expected,
            "safety_passed": "true",
        }
        for item, expected in (
            *((item, "true") for item in positive),
            *((item, "false") for item in negative),
        )
    ]


PROTECTED_BUILDERS = {
    "_expected_source_boundary",
    "_expected_output_filenames",
    "_expected_headers",
    "_expected_readiness",
    "_expected_manifest",
    "_expected_issue_rows",
    "_expected_contract_rows",
    "_classify",
    "_exact37_definitions",
    "_expected_truth_rows",
    "_expected_registry_rows",
    "_expected_safety_rows",
}


def _assert_checker_independent_ast(source_text: str | None = None) -> None:
    tree = ast.parse(
        Path(__file__).read_text(encoding="utf-8")
        if source_text is None
        else source_text
    )
    forbidden_roots = {
        "runtime",
        "predecessor",
        "admit007",
        "admit007_oracle",
        "design_gate",
    }
    forbidden_attributes = {
        "_contract_rows",
        "_truth_rows",
        "_registry_rows",
        "_safety_rows",
        "EVALUATOR_REGISTRY",
        "evaluate_admit_007",
        "classify_admit_006_admit_007_evidence_design",
        "build_design_state",
        "SOURCE_PATHS",
        "SOURCE_SHA256",
        "CONTRACT_COLUMNS",
        "TRUTH_COLUMNS",
        "REGISTRY_COLUMNS",
        "SAFETY_COLUMNS",
        "ISSUE_COLUMNS",
        "OUTPUT_FILES",
        "CSV_OUTPUTS",
        "DESIGN_ISSUE_PATH",
        "TRUE_READINESS",
        "FALSE_READINESS",
        "ADAPTER_IDS",
        "DISPATCH_ERROR_CODES",
        "RESULT_FIELDS",
        "_manifest_payload",
    }
    seen: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in PROTECTED_BUILDERS:
            seen.add(node.name)
            names = {
                child.id for child in ast.walk(node) if isinstance(child, ast.Name)
            }
            attributes = {
                child.attr
                for child in ast.walk(node)
                if isinstance(child, ast.Attribute)
            }
            if names & forbidden_roots or attributes & forbidden_attributes:
                raise AssertionError(
                    f"checker semantic builder depends on production: {node.name}"
                )
    if source_text is None and seen != PROTECTED_BUILDERS:
        raise AssertionError("checker protected builder inventory changed")


def _check_production_constant_alignment(
    expected_manifest: Mapping[str, object] | None = None,
) -> None:
    expected = (
        _expected_manifest()
        if expected_manifest is None
        else expected_manifest
    )
    identity = {
        "project": runtime.PROJECT,
        "step": runtime.STEP,
        "stage": runtime.STAGE,
        "manifest_schema_version": runtime.MANIFEST_SCHEMA_VERSION,
        "expected_base_commit": runtime.EXPECTED_BASE_COMMIT,
        "expected_base_subject": runtime.EXPECTED_BASE_SUBJECT,
        "recommended_next_step": runtime.RECOMMENDED_NEXT_STEP,
    }
    if any(identity[key] != expected[key] for key in identity):
        raise AssertionError("production manifest identity constants changed")
    boundary = _expected_source_boundary()
    expected_paths = tuple(path for path, _ in boundary)
    expected_sha = {path: digest for path, digest in boundary}
    if runtime.SOURCE_PATHS != expected_paths:
        raise AssertionError("production source paths differ from checker Exact18")
    if runtime.SOURCE_SHA256 != expected_sha:
        raise AssertionError("production source SHA differs from checker Exact18")
    if hasattr(runtime, "EXACT6_ISSUE_PATH"):
        raise AssertionError("obsolete Exact6 issue alias remains")
    if runtime.DESIGN_ISSUE_PATH != CHECKER_DESIGN_ISSUE_PATH:
        raise AssertionError("authoritative design issue path changed")
    if runtime.OUTPUT_FILES != _expected_output_filenames():
        raise AssertionError("production output filenames changed")
    if runtime.CSV_OUTPUTS != CHECKER_CSV_OUTPUTS:
        raise AssertionError("production CSV output filenames changed")
    if (
        runtime.RESULT_SCHEMA_VERSION != expected["result_schema_version"]
        or list(runtime.RESULT_FIELDS) != expected["result_fields"]
        or list(runtime.DISPATCH_ERROR_FIELDS)
        != expected["dispatch_error_fields"]
        or list(runtime.DISPATCH_ERROR_CODES)
        != expected["dispatch_error_codes"]
        or list(runtime.OUTCOME_VOCABULARY)
        != expected["outcome_vocabulary"]
    ):
        raise AssertionError("production result or dispatch contract changed")
    if (
        list(runtime.KNOWN_RULE_IDS) != expected["known_rule_ids"]
        or list(runtime.CALLABLE_DISCOVERED_RULE_IDS)
        != expected["callable_discovered_rule_ids"]
        or list(runtime.ADAPTER_READY_RULE_IDS)
        != expected["adapter_ready_rule_ids"]
        or list(runtime.LEGACY_ADAPTER_NOT_READY_RULE_IDS)
        != expected["legacy_adapter_not_ready_rule_ids"]
        or list(runtime.EVALUATOR_REGISTRY)
        != expected["registered_rule_ids"]
        or dict(runtime.ADAPTER_IDS) != expected["adapter_ids"]
    ):
        raise AssertionError("production rule or adapter state changed")
    production_readiness = {
        name: True for name in runtime.TRUE_READINESS
    } | {name: False for name in runtime.FALSE_READINESS}
    if (
        set(runtime.TRUE_READINESS) != CHECKER_TRUE_READINESS
        or set(runtime.FALSE_READINESS) != CHECKER_FALSE_READINESS
        or production_readiness != expected["readiness"]
    ):
        raise AssertionError("production readiness constants changed")
    dependency_modules = (
        runtime.predecessor.__name__,
        runtime.admit007.__name__,
        runtime.admit007_oracle.__name__,
    )
    if dependency_modules != CHECKER_RUNTIME_DEPENDENCY_MODULES:
        raise AssertionError("production runtime dependency imports changed")
    expected_headers = _expected_headers()
    observed_headers = {
        runtime.CONTRACT_FILENAME: runtime.CONTRACT_COLUMNS,
        runtime.TRUTH_FILENAME: runtime.TRUTH_COLUMNS,
        runtime.REGISTRY_FILENAME: runtime.REGISTRY_COLUMNS,
        runtime.SAFETY_FILENAME: runtime.SAFETY_COLUMNS,
        runtime.ISSUE_FILENAME: runtime.ISSUE_COLUMNS,
    }
    if observed_headers != expected_headers:
        raise AssertionError("production CSV headers changed")
    observed_filenames = (
        runtime.CONTRACT_FILENAME,
        runtime.TRUTH_FILENAME,
        runtime.REGISTRY_FILENAME,
        runtime.SAFETY_FILENAME,
        runtime.ISSUE_FILENAME,
        runtime.MANIFEST_FILENAME,
    )
    if observed_filenames != _expected_output_filenames():
        raise AssertionError("production output filename constants changed")


def _assert_error(
    call: Any,
    code: str,
    reason: str,
) -> runtime.UnifiedAdmissionDispatchError:
    try:
        call()
    except runtime.UnifiedAdmissionDispatchError as error:
        if error.code != code or error.reason != reason:
            raise AssertionError("dispatch error mismatch")
        return error
    raise AssertionError("dispatch did not fail closed")


def _check_runtime_directly() -> None:
    if runtime.UnifiedAdmissionRuleEvaluation is not runtime.predecessor.UnifiedAdmissionRuleEvaluation:
        raise AssertionError("result type identity changed")
    if runtime.UnifiedAdmissionDispatchError is not runtime.predecessor.UnifiedAdmissionDispatchError:
        raise AssertionError("dispatch type identity changed")
    for name in (
        "RESULT_SCHEMA_VERSION",
        "RESULT_FIELDS",
        "DISPATCH_ERROR_FIELDS",
        "DISPATCH_ERROR_CODES",
        "OUTCOME_VOCABULARY",
    ):
        if getattr(runtime, name) is not getattr(runtime.predecessor, name):
            raise AssertionError(f"identity changed: {name}")
    if inspect.signature(runtime.evaluate_admission_rule) != inspect.signature(
        runtime.predecessor.evaluate_admission_rule
    ):
        raise AssertionError("public signature changed")
    if type(runtime.EVALUATOR_REGISTRY) is not MappingProxyType:
        raise AssertionError("registry is mutable")
    if tuple(runtime.EVALUATOR_REGISTRY) != REGISTERED_RULE_IDS:
        raise AssertionError("registry order changed")
    for rule_id in KNOWN_RULE_IDS[:6]:
        if runtime.EVALUATOR_REGISTRY[rule_id] is not runtime.predecessor.EVALUATOR_REGISTRY[rule_id]:
            raise AssertionError(f"predecessor handler wrapped: {rule_id}")
        if runtime.RULE_NAMES[rule_id] != RULE_NAMES[rule_id]:
            raise AssertionError(f"rule name changed: {rule_id}")
        if runtime.ADAPTER_IDS[rule_id] != ADAPTER_IDS[rule_id]:
            raise AssertionError(f"adapter ID changed: {rule_id}")
    if runtime.EVALUATOR_REGISTRY["ADMIT_007"] is not runtime._evaluate_registered_admit_007:
        raise AssertionError("ADMIT_007 handler not registered")
    if hasattr(runtime, "evaluate_all_rules") or hasattr(runtime, "combined_candidate_verdict"):
        raise AssertionError("aggregation boundary expanded")

    class Text(str):
        pass

    error = _assert_error(
        lambda: runtime.evaluate_admission_rule(Text("ADMIT_007"), {}),
        "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID",
        "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID",
    )
    if (error.known_rule, error.callable_discovered, error.adapter_ready) != (
        False,
        False,
        False,
    ):
        raise AssertionError("str subclass flags")
    for rule_id in KNOWN_RULE_IDS[7:]:
        error = _assert_error(
            lambda rule_id=rule_id: runtime.evaluate_admission_rule(rule_id, {}),
            "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
            "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
        )
        if (error.known_rule, error.callable_discovered, error.adapter_ready) != (
            True,
            False,
            False,
        ):
            raise AssertionError("known-not-registered flags")

    class BombCandidate(Mapping[str, object]):
        def __init__(self) -> None:
            self.accesses = 0

        def __getitem__(self, key: str) -> object:
            self.accesses += 1
            raise AssertionError("candidate accessed")

        def __iter__(self):
            self.accesses += 1
            raise AssertionError("candidate accessed")

        def __len__(self) -> int:
            self.accesses += 1
            raise AssertionError("candidate accessed")

    bomb = BombCandidate()
    counts: Counter[str] = Counter()
    with (
        patch.object(runtime.admit007, "evaluate_admit_007", lambda *args: counts.update(["formal"])),
        patch.object(runtime.admit007_oracle, "classify_admit_006_admit_007_evidence_design", lambda *args: counts.update(["oracle"])),
    ):
        error = _assert_error(
            lambda: runtime.evaluate_admission_rule(
                "ADMIT_007",
                bomb,
                batch_context={},
                evaluation_context={},
                download_result_context={},
                stage_authorization_context={},
            ),
            "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
            "ADMIT_007_BATCH_CONTEXT_MUST_BE_NONE",
        )
    if error.adapter_ready is not True or counts or bomb.accesses:
        raise AssertionError("context routing accessed later state")

    class SingleLookupMapping(Mapping[str, object]):
        def __init__(
            self, key: str, value: object, *, present: bool = True
        ) -> None:
            self.key = key
            self.value = value
            self.present = present
            self.lookups = 0

        def __getitem__(self, key: str) -> object:
            if key != self.key:
                raise KeyError(key)
            self.lookups += 1
            if self.lookups > 1:
                raise AssertionError("required value read twice")
            if not self.present:
                raise KeyError(key)
            return self.value

        def __iter__(self):
            raise AssertionError("Mapping iterated")

        def __len__(self) -> int:
            raise AssertionError("Mapping sized")

    lookup_scalar = ENUM_MEMBERS[0]
    lookup_context_value = ALLOWED_CLASSES
    lookup_candidate = SingleLookupMapping(CANDIDATE_FIELD, lookup_scalar)
    lookup_context = SingleLookupMapping(CONTEXT_ITEM, lookup_context_value)
    lookup_result = runtime.evaluate_admission_rule(
        "ADMIT_007",
        lookup_candidate,
        evaluation_context=lookup_context,
    )
    if lookup_result.outcome != "passed" or (
        lookup_candidate.lookups,
        lookup_context.lookups,
    ) != (1, 1):
        raise AssertionError("required Mapping lookup count changed")

    missing_candidate = SingleLookupMapping(
        CANDIDATE_FIELD, object(), present=False
    )
    missing_result = runtime.evaluate_admission_rule(
        "ADMIT_007",
        missing_candidate,
        evaluation_context={CONTEXT_ITEM: ALLOWED_CLASSES},
    )
    if (
        missing_result.reason != "covalent_event_evidence_missing"
        or missing_candidate.lookups != 1
    ):
        raise AssertionError("missing candidate lookup count changed")

    missing_context = SingleLookupMapping(CONTEXT_ITEM, object(), present=False)
    error = _assert_error(
        lambda: runtime.evaluate_admission_rule(
            "ADMIT_007", {}, evaluation_context=missing_context
        ),
        "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        "ADMIT_007_ALLOWED_COVALENT_EVIDENCE_CLASSES_REQUIRED",
    )
    if error.adapter_ready is not True or missing_context.lookups != 1:
        raise AssertionError("missing context lookup count changed")

    scalar = object()
    context = object()
    candidate = {CANDIDATE_FIELD: scalar, "extra": object()}
    evaluation = {CONTEXT_ITEM: context, "extra": object()}
    candidate_before = dict(candidate)
    evaluation_before = dict(evaluation)
    source = runtime.admit007.evaluate_admit_007(ENUM_MEMBERS[0], ALLOWED_CLASSES)
    classification = runtime.admit007_oracle.classify_admit_006_admit_007_evidence_design(
        ENUM_MEMBERS[0], ALLOWED_CLASSES
    )
    calls: dict[str, list[tuple[object, object]]] = {"formal": [], "oracle": []}
    with (
        patch.object(runtime.admit007, "evaluate_admit_007", lambda left, right: calls["formal"].append((left, right)) or source),
        patch.object(runtime.admit007_oracle, "classify_admit_006_admit_007_evidence_design", lambda left, right: calls["oracle"].append((left, right)) or classification),
    ):
        result = runtime.evaluate_admission_rule(
            "ADMIT_007", candidate, evaluation_context=evaluation
        )
    if result.outcome != "passed":
        raise AssertionError("identity projection failed")
    if calls != {"formal": [(scalar, context)], "oracle": [(scalar, context)]}:
        raise AssertionError("original object identity lost")
    if candidate != candidate_before or evaluation != evaluation_before:
        raise AssertionError("input mapping mutated")

    for candidate_value in ({}, {CANDIDATE_FIELD: None}, {CANDIDATE_FIELD: ""}):
        with (
            patch.object(runtime.admit007, "evaluate_admit_007", side_effect=AssertionError("formal called")),
            patch.object(runtime.admit007_oracle, "classify_admit_006_admit_007_evidence_design", side_effect=AssertionError("oracle called")),
        ):
            missing = runtime.evaluate_admission_rule(
                "ADMIT_007",
                candidate_value,
                evaluation_context={CONTEXT_ITEM: ALLOWED_CLASSES},
            )
        if missing.reason != "covalent_event_evidence_missing":
            raise AssertionError("missing policy changed")

    for storage_mode in ("missing", "extra"):
        corrupt = runtime.admit007.evaluate_admit_007(
            ENUM_MEMBERS[0], ALLOWED_CLASSES
        )
        if storage_mode == "missing":
            object.__delattr__(corrupt, runtime.admit007.RESULT_FIELDS[-1])
        else:
            object.__setattr__(corrupt, "extra", True)
        counts.clear()
        with (
            patch.object(
                runtime.admit007,
                "evaluate_admit_007",
                lambda *args, corrupt=corrupt: counts.update(["formal"])
                or corrupt,
            ),
            patch.object(
                runtime.admit007_oracle,
                "classify_admit_006_admit_007_evidence_design",
                side_effect=AssertionError("oracle called"),
            ),
            patch.object(
                runtime,
                "_project_admit007_exact13",
                side_effect=AssertionError("projected"),
            ),
        ):
            error = _assert_error(
                lambda: runtime.evaluate_admission_rule(
                    "ADMIT_007",
                    {CANDIDATE_FIELD: ENUM_MEMBERS[0]},
                    evaluation_context={CONTEXT_ITEM: ALLOWED_CLASSES},
                ),
                "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
                "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
            )
        if error.adapter_ready is not False or counts != {"formal": 1}:
            raise AssertionError(f"{storage_mode} storage shape did not fail early")

    bad = runtime.admit007.evaluate_admit_007(ENUM_MEMBERS[0], ALLOWED_CLASSES)
    object.__setattr__(bad, "evaluator_io_used", True)
    counts.clear()
    with (
        patch.object(runtime.admit007, "evaluate_admit_007", lambda *args: counts.update(["formal"]) or bad),
        patch.object(runtime.admit007_oracle, "classify_admit_006_admit_007_evidence_design", lambda *args: counts.update(["oracle"])),
    ):
        error = _assert_error(
            lambda: runtime.evaluate_admission_rule(
                "ADMIT_007",
                {CANDIDATE_FIELD: ENUM_MEMBERS[0]},
                evaluation_context={CONTEXT_ITEM: ALLOWED_CLASSES},
            ),
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        )
    if error.adapter_ready is not False or counts != {"formal": 1}:
        raise AssertionError("source failure did not precede oracle")

    valid = runtime.admit007.evaluate_admit_007(ENUM_MEMBERS[0], ALLOWED_CLASSES)
    mismatch = runtime.admit007_oracle.classify_admit_006_admit_007_evidence_design(
        ENUM_MEMBERS[1], ALLOWED_CLASSES
    )
    counts.clear()
    with (
        patch.object(runtime.admit007, "evaluate_admit_007", lambda *args: counts.update(["formal"]) or valid),
        patch.object(runtime.admit007_oracle, "classify_admit_006_admit_007_evidence_design", lambda *args: counts.update(["oracle"]) or mismatch),
        patch.object(runtime, "_project_admit007_exact13", side_effect=AssertionError("projected")),
    ):
        _assert_error(
            lambda: runtime.evaluate_admission_rule(
                "ADMIT_007",
                {CANDIDATE_FIELD: ENUM_MEMBERS[0]},
                evaluation_context={CONTEXT_ITEM: ALLOWED_CLASSES},
            ),
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            "ADMIT_007_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        )
    if counts != {"formal": 1, "oracle": 1}:
        raise AssertionError("oracle mismatch call counts")

    blocked = runtime.evaluate_admission_rule(
        "ADMIT_007",
        {CANDIDATE_FIELD: ENUM_MEMBERS[2]},
        evaluation_context={CONTEXT_ITEM: ALLOWED_CLASSES},
    )
    retained = runtime.evaluate_admission_rule(
        "ADMIT_007",
        {CANDIDATE_FIELD: ENUM_MEMBERS[0]},
        evaluation_context={CONTEXT_ITEM: None},
    )
    if blocked.outcome != "blocked" or blocked.reason != BLOCKED_REASON:
        raise AssertionError("blocked passthrough changed")
    expected_pair = ((CANDIDATE_FIELD, ENUM_MEMBERS[0]),)
    if retained.outcome != "invalid" or retained.normalized_values != expected_pair or retained.validated_candidate_fields != expected_pair:
        raise AssertionError("context-invalid canonical state lost")


def _called_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                names.add(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                names.add(child.func.attr)
    return names


def _check_public_call_graph() -> None:
    path = REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    banned = {
        "build_runtime_state",
        "build_frozen_source_snapshot",
        "run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1",
        "_git",
        "open",
        "read",
        "read_bytes",
        "read_text",
        "write",
        "write_bytes",
        "write_text",
        "run",
        "Popen",
        "system",
        "urlopen",
    }
    # Registry dispatch is indirect in the AST, so seed the registered handler
    # explicitly and audit both public roots as one closure.
    pending = ["evaluate_admission_rule", "_evaluate_registered_admit_007"]
    closure: set[str] = set()
    while pending:
        name = pending.pop()
        if name in closure:
            continue
        closure.add(name)
        calls = _called_names(functions[name])
        if calls & banned:
            raise AssertionError(f"public runtime reaches metadata I/O: {calls & banned}")
        pending.extend(call for call in calls if call in functions)
    required = {
        "evaluate_admission_rule",
        "_raise_dispatch_error",
        "_evaluate_registered_admit_007",
        "_admit007_context_failure",
        "_admit007_candidate_invalid",
        "_prevalidate_admit007_source",
        "_expected_admit007_from_oracle",
        "_validate_admit007_oracle_equivalence",
        "_project_admit007_exact13",
        "_admit007_adapter_failure",
    }
    if not required <= closure:
        raise AssertionError("public runtime closure incomplete")
    import_section = path.read_text(encoding="utf-8").split("PROJECT =", 1)[0]
    if "admit_007_unified_adapter_contract_design_gate" in import_section:
        raise AssertionError("design gate imported into runtime")
    for dependency in ("torch", "numpy", "rdkit"):
        if dependency in import_section:
            raise AssertionError(f"disallowed runtime import: {dependency}")

    standalone_tree = ast.parse(
        (REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_007_rule_logic_interface.py").read_text(encoding="utf-8")
    )
    standalone_functions = {
        node.name: node
        for node in standalone_tree.body
        if isinstance(node, ast.FunctionDef)
    }
    if "classify_admit_006_admit_007_evidence_design" in _called_names(
        standalone_functions["evaluate_admit_007"]
    ):
        raise AssertionError("standalone evaluator calls design oracle")


def _validate_issue_rows(rows: Sequence[Mapping[str, str]]) -> None:
    _check_production_constant_alignment()
    predecessor_path = REPO_ROOT / CHECKER_DESIGN_ISSUE_PATH
    if _sha256(predecessor_path) != CHECKER_DESIGN_ISSUE_SHA256:
        raise AssertionError("authoritative design issue SHA mismatch")
    predecessor_header, predecessor_rows = _csv(predecessor_path)
    if (
        predecessor_header != CHECKER_ISSUE_HEADER
        or len(rows) != len(predecessor_rows) != 11
    ):
        raise AssertionError("Exact11 issue shape mismatch")
    if [dict(row) for row in rows] != _expected_issue_rows(predecessor_rows):
        raise AssertionError("Exact11 issue semantics mismatch")
    issue_map = {row["issue_id"]: row for row in rows}
    if issue_map["COVALENT_EVIDENCE_ENUM_UNRESOLVED"]["status"] != "resolved":
        raise AssertionError("enum issue reopened")
    if issue_map["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["status"] != "open":
        raise AssertionError("cross-rule issue closed")
    provider = issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]
    if provider["status"] != "open" or provider["issue_count"] != "11":
        raise AssertionError("provider blocker changed")


def _validate_manifest(
    manifest: object,
    root: Path,
    expected_manifest: Mapping[str, object] | None = None,
) -> None:
    expected = (
        _expected_manifest()
        if expected_manifest is None
        else expected_manifest
    )
    if type(manifest) is not dict:
        raise AssertionError("manifest must be an exact dict")
    if set(manifest) != set(expected):
        missing = sorted(set(expected) - set(manifest))
        extra = sorted(set(manifest) - set(expected))
        raise AssertionError(
            f"manifest key set mismatch: missing={missing}, extra={extra}"
        )
    if manifest != expected:
        mismatched = sorted(
            key for key in expected if manifest[key] != expected[key]
        )
        raise AssertionError(
            f"manifest semantic mismatch: {mismatched}"
        )
    expected_readiness = expected["readiness"]
    if type(expected_readiness) is not dict:
        raise AssertionError("checker readiness contract is not an exact dict")
    for key, value in expected_readiness.items():
        if manifest[key] is not value or manifest["readiness"][key] is not value:
            raise AssertionError(f"manifest readiness mirror mismatch: {key}")
    _check_production_constant_alignment(expected)
    output_sha256 = expected["output_sha256"]
    if type(output_sha256) is not dict:
        raise AssertionError("checker output SHA contract is not an exact dict")
    for name, claimed in output_sha256.items():
        if _sha256(root / name) != claimed:
            raise AssertionError(f"manifest output hash mismatch: {name}")


def _validate_output_root(
    root: Path,
    *,
    enforce_frozen_hashes: bool = True,
) -> dict[str, int]:
    expected_manifest = _expected_manifest()
    if not root.is_dir() or root.is_symlink():
        raise AssertionError("unsafe output root")
    if {path.name for path in root.iterdir()} != set(
        _expected_output_filenames()
    ):
        raise AssertionError("output set mismatch")
    for name in _expected_output_filenames():
        path = root / name
        if not path.is_file() or path.is_symlink():
            raise AssertionError(f"unsafe output entry: {name}")
    manifest = json.loads(
        (root / CHECKER_MANIFEST_FILENAME).read_text(encoding="utf-8")
    )
    _validate_manifest(manifest, root, expected_manifest)
    if enforce_frozen_hashes:
        for name, expected_sha in EXPECTED_OUTPUT_SHA256.items():
            if _sha256(root / name) != expected_sha:
                raise AssertionError(f"frozen output SHA256 mismatch: {name}")

    contract_header, contract_rows = _csv(root / CHECKER_CONTRACT_FILENAME)
    truth_header, truth_rows = _csv(root / CHECKER_TRUTH_FILENAME)
    registry_header, registry_rows = _csv(root / CHECKER_REGISTRY_FILENAME)
    safety_header, safety_rows = _csv(root / CHECKER_SAFETY_FILENAME)
    issue_header, issue_rows = _csv(root / CHECKER_ISSUE_FILENAME)
    headers = _expected_headers()
    if contract_header != headers[CHECKER_CONTRACT_FILENAME] or contract_rows != _expected_contract_rows():
        raise AssertionError("Exact66 contract semantics mismatch")
    if truth_header != headers[CHECKER_TRUTH_FILENAME] or truth_rows != _expected_truth_rows():
        raise AssertionError("Exact107 truth semantics mismatch")
    if registry_header != headers[CHECKER_REGISTRY_FILENAME] or registry_rows != _expected_registry_rows():
        raise AssertionError("Exact15 registry semantics mismatch")
    if safety_header != headers[CHECKER_SAFETY_FILENAME] or safety_rows != _expected_safety_rows():
        raise AssertionError("Exact36 safety semantics mismatch")
    if issue_header != headers[CHECKER_ISSUE_FILENAME]:
        raise AssertionError("Exact11 issue header mismatch")
    _validate_issue_rows(issue_rows)
    return {
        "contract_rows": len(contract_rows),
        "truth_rows": len(truth_rows),
        "registry_rows": len(registry_rows),
        "safety_rows": len(safety_rows),
        "issue_rows": len(issue_rows),
    }


def _check_source_boundary() -> runtime.FrozenSourceSnapshot:
    _check_production_constant_alignment()
    boundary = _expected_source_boundary()
    if len(boundary) != 18 or len({path for path, _ in boundary}) != 18:
        raise AssertionError("checker Exact18 source boundary shape")
    subject = subprocess.run(
        [
            "git",
            "show",
            "-s",
            "--format=%s",
            CHECKER_EXPECTED_BASE_COMMIT,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    ancestor = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            CHECKER_EXPECTED_BASE_COMMIT,
            "HEAD",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    if (
        subject.returncode != 0
        or subject.stdout.strip() != CHECKER_EXPECTED_BASE_SUBJECT
        or ancestor.returncode != 0
    ):
        raise AssertionError("checker base lineage mismatch")
    for path, expected_sha in boundary:
        absolute = REPO_ROOT / path
        metadata = os.lstat(absolute)
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", path.as_posix()],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
        base = subprocess.run(
            [
                "git",
                "show",
                f"{CHECKER_EXPECTED_BASE_COMMIT}:{path.as_posix()}",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
        if (
            tracked.returncode != 0
            or base.returncode != 0
            or not stat.S_ISREG(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or hashlib.sha256(base.stdout).hexdigest() != expected_sha
            or _sha256(absolute) != expected_sha
        ):
            raise AssertionError(f"checker source mismatch: {path}")
    snapshot = runtime.build_frozen_source_snapshot()
    if not runtime.validate_frozen_source_snapshot(snapshot):
        raise AssertionError("Exact18 source snapshot invalid")
    if len(snapshot.records) != 18:
        raise AssertionError("Exact18 source snapshot count changed")
    for (path, expected_sha), record in zip(
        boundary, snapshot.records, strict=True
    ):
        if not (
            record.relative_path == path
            and record.expected_sha256 == expected_sha
            == record.base_tree_sha256
            == record.filesystem_sha256
            == hashlib.sha256(record.content_bytes).hexdigest()
        ):
            raise AssertionError(f"source SHA mismatch: {record.relative_path}")
    return snapshot


def _check_materialization() -> None:
    with tempfile.TemporaryDirectory(prefix="covapie-exact7-check-") as temporary:
        first_root = Path(temporary) / "first"
        second_root = Path(temporary) / "second"
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1(first_root)
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1(second_root)
        for name in _expected_output_filenames():
            if (first_root / name).read_bytes() != (second_root / name).read_bytes():
                raise AssertionError(f"double materialization differs: {name}")
            if (first_root / name).read_bytes() != (REPO_ROOT / runtime.DEFAULT_OUTPUT_ROOT / name).read_bytes():
                raise AssertionError(f"committed output differs: {name}")
        _validate_output_root(first_root)

        tampered = Path(temporary) / "tampered"
        shutil.copytree(first_root, tampered)
        contract_path = tampered / CHECKER_CONTRACT_FILENAME
        header, rows = _csv(contract_path)
        rows[0]["observed_value"] = "false"
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        contract_path.write_text(stream.getvalue(), encoding="utf-8")
        manifest_path = tampered / CHECKER_MANIFEST_FILENAME
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["output_sha256"][CHECKER_CONTRACT_FILENAME] = _sha256(contract_path)
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        try:
            _validate_output_root(tampered, enforce_frozen_hashes=False)
        except AssertionError:
            pass
        else:
            raise AssertionError("synchronized output tamper accepted")

        for mode in ("missing", "extra", "symlink"):
            candidate = Path(temporary) / mode
            shutil.copytree(first_root, candidate)
            if mode == "missing":
                (candidate / CHECKER_CONTRACT_FILENAME).unlink()
            elif mode == "extra":
                (candidate / "unexpected.txt").write_text("x", encoding="utf-8")
            else:
                victim = candidate / CHECKER_CONTRACT_FILENAME
                victim.unlink()
                victim.symlink_to(first_root / CHECKER_CONTRACT_FILENAME)
            try:
                _validate_output_root(candidate)
            except AssertionError:
                continue
            raise AssertionError(f"unsafe output accepted: {mode}")

        unsafe_root = Path(temporary) / "unsafe"
        unsafe_root.mkdir()
        outside = Path(temporary) / "outside"
        outside.write_text("unchanged", encoding="utf-8")
        (unsafe_root / CHECKER_CONTRACT_FILENAME).symlink_to(outside)
        try:
            runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1(unsafe_root)
        except ValueError:
            pass
        else:
            raise AssertionError("materializer accepted symlink output")
        if outside.read_text(encoding="utf-8") != "unchanged":
            raise AssertionError("symlink victim modified")


def _silent_import(command_text: str) -> None:
    completed = subprocess.run(
        [sys.executable, "-c", command_text],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(SRC_ROOT)},
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError("silent import failed")
    if completed.stdout or completed.stderr:
        raise AssertionError("silent import emitted output")


def main() -> int:
    _assert_checker_independent_ast()
    _check_source_boundary()
    _check_public_call_graph()
    _check_runtime_directly()
    state = runtime.build_runtime_state()
    if state["all_checks_passed"] is not True or state["validation_failures"]:
        raise AssertionError("runtime state failed closed")
    root = REPO_ROOT / runtime.DEFAULT_OUTPUT_ROOT
    counts = _validate_output_root(root)
    _check_materialization()
    _silent_import(
        "import covalent_ext.covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007"
    )
    checker_path = Path(__file__)
    _silent_import(
        "import importlib.util;"
        f"s=importlib.util.spec_from_file_location('exact7_checker',{str(checker_path)!r});"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m)"
    )

    print("all_checks_passed=true")
    print("exact18_source_sha=18/18")
    print("registered_rule_count=7")
    print("predecessor_handler_identity_reused=6/6")
    print(f"contract_rows={counts['contract_rows']}")
    print(f"truth_rows={counts['truth_rows']}")
    print("truth_groups=" + json.dumps(TRUTH_GROUP_COUNTS, sort_keys=True, separators=(",", ":")))
    print(f"registry_rows={counts['registry_rows']}")
    print(f"safety_rows={counts['safety_rows']}")
    print(f"issue_rows={counts['issue_rows']}")
    print("frozen_output_sha=6/6")
    print("ready_for_bulk_download_now=false")
    print("ready_for_training=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
