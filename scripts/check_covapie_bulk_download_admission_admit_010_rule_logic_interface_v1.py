#!/usr/bin/env python3
"""Fail-closed independent checker for ADMIT_010 standalone evaluator v1."""

from __future__ import annotations

import ast
import csv
import hashlib
import inspect
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate
    as committed_oracle,
)
from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_010_rule_logic_interface as interface,
)


EXPECTED_BASE_COMMIT = "c78f15a1bf57f6372e48098629f3cce33f21e7fc"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_010 leakage group provenance contract v1"
CHECKER_RULE_ID = "ADMIT_010"
CHECKER_CANDIDATE_FIELD = "leakage_group_id"
CHECKER_CONTEXT_ITEM = "leakage_group_assignment_provenance_contract"
CHECKER_HISTORICAL_FIELD = "final_leakage_group_id"
CHECKER_REGEX = r"^COVAPIE_LEAKAGE_GROUP_[0-9]{6}$"
CHECKER_VERSION = "covapie_leakage_group_assignment_provenance_contract_v1"
CHECKER_MAPPING = "exact_value_identity_after_provider_field_rename_only"
CHECKER_POLICY = "conservative_union_of_ligand_graph_scaffold_and_protein_accession_sequence_clusters_v1"
CHECKER_POLICY_VERSION = "v1"
CHECKER_STAGE = "pre_final_split_leakage_group_assignment"
CHECKER_STATUS = "leakage_group_assigned_before_final_split"
CHECKER_BLOCK_REASON = "leakage_group_unassigned"
CHECKER_RESULT_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_leakage_group_id", "validated_candidate_fields",
    "consumed_candidate_fields", "consumed_context_items", "evaluator_io_used",
)
CHECKER_PRECEDENCE = (
    "leakage_group_id_exact_builtin_str", "empty_assignment_state", "ASCII",
    "canonical_grammar", "provenance_exact_committed_design_type",
    "contract_version", "candidate_and_historical_field_names",
    "field_mapping_rule", "assignment_policy", "assignment_policy_version",
    "assignment_stage_kind", "four_source_SHA256_fields", "assignment_id",
    "historical_leakage_group_id_grammar", "sample_index_row_id",
    "member_sample_index_row_ids", "member_count", "assignment_evidence_consistency",
    "candidate_historical_id_exact_equality", "sample_membership", "passed",
)
CHECKER_REASONS = (
    "LEAKAGE_GROUP_ID_TYPE_INVALID", CHECKER_BLOCK_REASON,
    "LEAKAGE_GROUP_ID_NON_ASCII", "LEAKAGE_GROUP_ID_SYNTAX_INVALID",
    "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_CONTRACT_TYPE_INVALID",
    "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_CONTRACT_VERSION_INVALID",
    "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_FIELD_MAPPING_INVALID",
    "LEAKAGE_GROUP_ASSIGNMENT_POLICY_INVALID",
    "LEAKAGE_GROUP_ASSIGNMENT_POLICY_VERSION_INVALID",
    "LEAKAGE_GROUP_ASSIGNMENT_STAGE_KIND_INVALID",
    "LEAKAGE_GROUP_ASSIGNMENT_SOURCE_SHA256_INVALID",
    "LEAKAGE_GROUP_ASSIGNMENT_ID_INVALID",
    "LEAKAGE_GROUP_ASSIGNMENT_HISTORICAL_GROUP_ID_INVALID",
    "LEAKAGE_GROUP_ASSIGNMENT_SAMPLE_ID_INVALID",
    "LEAKAGE_GROUP_ASSIGNMENT_MEMBERSHIP_INVALID",
    "LEAKAGE_GROUP_ASSIGNMENT_MEMBER_COUNT_INVALID",
)

CONTRACT_FILENAME = "covapie_admit_010_rule_logic_interface_contract.csv"
TRUTH_FILENAME = "covapie_admit_010_rule_logic_interface_truth_matrix.csv"
SOURCE_FILENAME = "covapie_admit_010_rule_logic_interface_source_boundary_audit.csv"
SAFETY_FILENAME = "covapie_admit_010_rule_logic_interface_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_010_rule_logic_interface_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_010_rule_logic_interface_manifest.json"
CSV_OUTPUTS = (CONTRACT_FILENAME, TRUTH_FILENAME, SOURCE_FILENAME, SAFETY_FILENAME, ISSUE_FILENAME)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)
OUTPUT_ROOT = REPO_ROOT / "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_rule_logic_interface_v1"

EXPECTED_SOURCE_PATHS = (
    "src/covalent_ext/covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1/covapie_admit_010_leakage_group_assignment_provenance_contract_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1/covapie_admit_010_leakage_group_assignment_provenance_contract.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1/covapie_admit_010_leakage_group_id_field_mapping_and_grammar_contract.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1/covapie_admit_010_provenance_validation_truth_matrix.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1/covapie_admit_010_provenance_contract_source_boundary_audit.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1/covapie_admit_010_provenance_contract_issue_readiness_inventory.csv",
    "src/covalent_ext/covapie_bulk_download_admission_admit_010_formal_evaluator_interface_preconditions_audit.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_010_formal_evaluator_preconditions_manifest.json",
    "src/covalent_ext/covapie_bulk_download_admission_admit_009_rule_logic_interface.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_rule_logic_interface_v1/covapie_admit_009_rule_logic_interface_contract.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_rule_logic_interface_v1/covapie_admit_009_rule_logic_interface_manifest.json",
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009.py",
)
EXPECTED_SOURCE_SHA256 = {
    "src/covalent_ext/covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate.py": "cbff1bd3fe4e6d65c9be33a5efee4d80ea1f9310cb7cb73e45dc4e1055a2de05",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1/covapie_admit_010_leakage_group_assignment_provenance_contract_manifest.json": "33fb0d6f35b49dbf98e61e2c16fafece4b01cdfcce629ff7f1ac5afb1e7e5af2",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1/covapie_admit_010_leakage_group_assignment_provenance_contract.csv": "6daea490d7a355015f9b9f0da134d0c4e58ae48dfb7e38ed0337efdcfbe8a4a6",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1/covapie_admit_010_leakage_group_id_field_mapping_and_grammar_contract.csv": "9de1347f94498f1e79f95b48bc4e943fe6b311715bebeb1acd730110907fb3ba",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1/covapie_admit_010_provenance_validation_truth_matrix.csv": "1a40d6e7ef0cbccf9408f9fca2524ab260f3291dd1fe4f1838d3e0a73b8a3ee7",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1/covapie_admit_010_provenance_contract_source_boundary_audit.csv": "607660277c3f2ee4931cfc4601017ed57b8953eb738a3535f5580a21591107f6",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1/covapie_admit_010_provenance_contract_issue_readiness_inventory.csv": "779932531b630072ff33721e689a2865defdad477df8335a9950c8e4537476bd",
    "src/covalent_ext/covapie_bulk_download_admission_admit_010_formal_evaluator_interface_preconditions_audit.py": "229945a3edad28ee7770172cb931e05ac463db56b0dd1abe57a8053bb4d7e5b1",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_010_formal_evaluator_preconditions_manifest.json": "29df6cdf3b1eb7c1a690610d9fad88055797caba58f27f01f0b7da0d488d4c43",
    "src/covalent_ext/covapie_bulk_download_admission_admit_009_rule_logic_interface.py": "3649971eec020c5981a3ba8bfddeb604797f8557fb6036efd6094a2b0d6ab4e4",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_rule_logic_interface_v1/covapie_admit_009_rule_logic_interface_contract.csv": "ea02293b7a43ee22c34c029192bdce4e3356fe9c69688bb66169a939b39eda67",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_rule_logic_interface_v1/covapie_admit_009_rule_logic_interface_manifest.json": "b69941408b6f6098e926f7cf3f60cf526811e78a71cb07000c332511b19d5447",
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009.py": "80bdc66d2b0b2a1d761b0a1eb07f644f47535516598c3869f75a92cddafbdb39",
}
EXPECTED_OUTPUT_SHA256 = {
    CONTRACT_FILENAME: "809a591cca7bd5f94920100105dbc6d643d8e73f38dc7692933f244de954d774",
    TRUTH_FILENAME: "c5caa0f398f7d8592b2ef8ab14e4af4c47e9bfd7a06e476f617de55e6c627284",
    SOURCE_FILENAME: "8695ed6089fd576581ef1a50e7c48b07cac12a7aa6450f19a384bfbfabcef84d",
    SAFETY_FILENAME: "85dbd9f38e39a5620c41081d6134774893250a43d67023b69cae94775224d2ab",
    ISSUE_FILENAME: "779932531b630072ff33721e689a2865defdad477df8335a9950c8e4537476bd",
    MANIFEST_FILENAME: "5769c583bc5ade6dbeb81190b20e1774120f7b38dbf53d540f97b50dbf594d54",
}

EXPECTED_GROUP_COUNTS = {
    "candidate_scalar": 14, "context_type": 4, "static_fields": 7,
    "sha256": 6, "assignment_id": 5, "historical_group": 3,
    "sample_id": 5, "membership": 12, "member_count": 6,
    "assignment_semantics": 9,
}

CHECKER_CONTRACT_IDS = (
    "API_001", "API_002", "API_003", "RESULT_001", "RESULT_002", "RESULT_003",
    "RESULT_004", "RESULT_005", "RESULT_006", "RESULT_007", "RESULT_008",
    "RESULT_009", "RESULT_010", "TUPLE_001", "TUPLE_002", "TUPLE_003",
    "IDENTITY_001", "IDENTITY_002", "PRECEDENCE_001", "PRECEDENCE_002",
    "GRAMMAR_001", "GRAMMAR_002", "SHA_001", "OPAQUE_001", "MEMBER_001",
    "MEMBER_002", "EVIDENCE_001", "ORACLE_001", "ORACLE_002", "ORACLE_003",
    "SOURCE_001", "SOURCE_002", "ISSUE_001", "PROVIDER_001", "BOUNDARY_001",
    "BOUNDARY_002", "BOUNDARY_003", "BOUNDARY_004", "OUTPUT_001", "OUTPUT_002",
    "OUTPUT_003",
)
CHECKER_EXECUTED_SAFETY_ITEMS = (
    "formal_evaluator_implementation", "exact10_result_class",
    "exact71_full_equivalence", "result_invariant_enforcement",
    "pure_in_memory_call_graph", "no_input_mutation", "hostile_comparison_blocked",
    "exact_type_first", "deterministic_materialization", "source_verification",
    "issue_byte_preservation", "materializer_preflight_and_atomic_replace",
)
CHECKER_NOT_EXECUTED_SAFETY_ITEMS = (
    "provider_mapping", "real_candidate_evaluation", "unified_adapter_design",
    "unified_adapter_implementation", "admit_010_registration", "exact10_runtime",
    "admit_011", "evaluate_all_rules", "combined_candidate_verdict", "grouping",
    "split", "reassignment", "raw_read", "network", "bulk_download", "checkpoint",
    "model_forward_loss", "training_fine_tune", "parameter_update", "stage", "commit",
    "push", "gh",
)
CHECKER_TRUE_READINESS = (
    "leakage_group_assignment_provenance_contract_frozen",
    "leakage_group_id_final_grammar_frozen",
    "leakage_group_id_historical_field_mapping_rule_frozen",
    "admit_010_design_oracle_implemented", "admit_010_standalone_evaluator_implemented",
    "evaluate_admit_010_implemented", "Admit010EvaluationResult_implemented",
    "admit_010_exact10_result_contract_frozen",
    "admit_010_result_class_exact_type_enforced",
    "admit_010_result_cross_field_invariants_enforced",
    "admit_010_validation_precedence_runtime_enforced",
    "admit_010_design_oracle_independence_preserved",
    "admit_010_formal_exact71_equivalence_enforced",
    "admit_010_provider_mapping_boundary_preserved",
    "ready_for_admit_010_unified_adapter_contract_design",
    "feature_semantics_audit_required_before_training",
)
CHECKER_FALSE_READINESS = (
    "leakage_group_id_provider_mapping_validated",
    "real_provider_leakage_group_id_count_nonzero",
    "admit_010_unified_adapter_contract_frozen", "admit_010_unified_adapter_implemented",
    "admit_010_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_010_implemented",
    "admit_011_started", "evaluate_all_rules_implemented",
    "combined_candidate_verdict_contract_frozen", "combined_candidate_verdict_implemented",
    "cross_rule_precedence_frozen", "real_candidate_evaluation",
    "ready_for_bulk_download_now", "ready_for_training", "ready_to_train_now",
)
CHECKER_READINESS = {
    **{name: True for name in CHECKER_TRUE_READINESS},
    **{name: False for name in CHECKER_FALSE_READINESS},
}
CHECKER_OUTPUT_MATERIALIZATION = {
    "preflight_before_first_write": True, "real_directory_non_symlink": True,
    "existing_inventory_allowlist_exact": True, "existing_entries_regular_non_symlink": True,
    "atomic_same_directory_mkstemp": True, "temporary_suffix": ".tmp",
    "fdopen_mode": "wb", "flush_and_fsync": True, "os_replace": True,
    "finally_cleanup": True, "postwrite_exact_inventory_reverified": True,
}
CHECKER_STOP_BOUNDARIES = [
    "no_provider_mapping", "no_unified_adapter_design_or_implementation",
    "no_admit_010_registration", "no_exact10_runtime", "no_admit_011",
    "no_evaluate_all_rules", "no_combined_candidate_verdict",
    "no_real_candidate_evaluation", "no_split_or_reassignment",
    "no_raw_network_download_checkpoint_model_training",
]
CORE_MANIFEST_KEYS = {
    "admission_rule_id", "admission_rule_name", "all_checks_passed",
    "all_issue_checks_passed", "all_predecessor_contract_checks_passed",
    "all_result_contract_checks_passed", "all_safety_checks_passed",
    "all_semantic_checks_passed", "all_source_boundary_checks_passed",
    "all_truth_matrix_checks_passed", "artifact_reference_paths_not_recursively_opened",
    "candidate_field", "context_item", "contract_pass_count", "contract_row_count",
    "coverage_issue_affected_rules", "coverage_issue_status", "evaluation_phase",
    "expected_base_commit", "expected_base_subject", "formal_design_exact10_parity",
    "historical_artifact_field", "issue_inventory_preserved_exactly",
    "issue_inventory_row_count", "issue_inventory_sha256", "issue_transition",
    "leakage_group_prefix", "leakage_group_regex", "manifest_schema_version",
    "metadata_design_oracle_parity_only", "outcome_vocabulary", "output_file_count",
    "output_files", "output_materialization", "output_sha256",
    "output_sha256_excludes_manifest_self_hash", "production_design_oracle_import_or_call",
    "project", "provenance_type", "provenance_type_direct_committed_identity",
    "public_api", "public_signature_parameters",
    "public_signature_required_positional_or_keyword", "readiness",
    "real_provider_leakage_group_id_count", "reason_vocabulary", "recommended_next_step",
    "result_exact_type_required", "result_field_count", "result_fields", "result_type",
    "safety_pass_count", "safety_row_count", "source_audit_pass_count",
    "source_audit_row_count", "source_boundary_name",
    "source_documents_parsed_only_from_frozen_snapshot_bytes", "source_input_count",
    "source_input_paths", "source_input_sha256", "source_input_verification",
    "source_structural_checks_before_first_explicit_content_read", "stage", "step",
    "stop_boundaries", "truth_group_counts", "truth_matrix_contract", "truth_pass_count",
    "truth_row_count", "validation_failures", "validation_precedence",
}
EXPECTED_MANIFEST_KEYS = CORE_MANIFEST_KEYS | set(CHECKER_READINESS)

CHECKER_CONTRACT_COLUMNS = (
    "contract_id", "contract_kind", "contract_subject", "contract_value",
    "contract_status",
)
CHECKER_TRUTH_COLUMNS = (
    "truth_order", "truth_group", "case_id", "input_summary",
    *CHECKER_RESULT_FIELDS, "design_oracle_full_result",
    "exact10_equal_field_count", "formal_design_exact10_parity",
    "expected_precedence", "truth_passed",
)
CHECKER_SOURCE_COLUMNS = (
    "source_order", "source_relative_path", "source_kind", "boundary_necessity",
    "tracked", "base_tree_blob", "filesystem_regular", "non_symlink",
    "safe_descendant", "expected_sha256", "base_tree_sha256",
    "filesystem_sha256", "source_boundary_passed",
)
CHECKER_SAFETY_COLUMNS = (
    "safety_item", "expected_executed", "observed_executed", "safety_passed",
)
CHECKER_ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity",
    "status", "blocking_scope", "blocking_reason", "issue_origin",
    "integration_transition", "issue_count",
)


def _expected_contract_rows() -> tuple[dict[str, str], ...]:
    """Return the checker-owned complete Exact41 contract, without production builders."""
    values = (
        ("API_001", "public_api", "signature", "evaluate_admit_010(leakage_group_id, leakage_group_assignment_provenance_contract)"),
        ("API_002", "public_api", "parameters", "two_required_positional_or_keyword_no_defaults_no_extras"),
        ("API_003", "public_api", "execution", "pure_in_memory_deterministic_no_input_mutation"),
        ("RESULT_001", "result", "type", "exact_frozen_dataclass_no_slots_no_subclasses"),
        ("RESULT_002", "result", "field_count", "10"),
        ("RESULT_003", "result", "field_order", "|".join(CHECKER_RESULT_FIELDS)),
        ("RESULT_004", "result", "exact_types_first", "str|bool|tuple|string_pair_no_subclasses"),
        ("RESULT_005", "result", "outcomes", "passed|blocked|invalid"),
        ("RESULT_006", "result", "state", "passed_iff_passed;blocks_iff_nonpassed"),
        ("RESULT_007", "result", "reason", "passed_empty;nonpassed_frozen;blocked_lowercase_only"),
        ("RESULT_008", "result", "scalar_short", "empty_canonical_validated_context"),
        ("RESULT_009", "result", "retained", "canonical_pair_and_context_singleton"),
        ("RESULT_010", "result", "io", "exact_false"),
        ("TUPLE_001", "tuple", "consumed_candidate_fields", CHECKER_CANDIDATE_FIELD),
        ("TUPLE_002", "tuple", "consumed_context_items", "empty_or_context_singleton"),
        ("TUPLE_003", "tuple", "validated_candidate_fields", "empty_or_exact_single_canonical_pair"),
        ("IDENTITY_001", "reuse", "Exact19", "direct_committed_class_identity"),
        ("IDENTITY_002", "reuse", "constants", "direct_committed_design_identity"),
        ("PRECEDENCE_001", "validation", "Exact21", "|".join(CHECKER_PRECEDENCE)),
        ("PRECEDENCE_002", "validation", "short_circuit", "exact_type_first_no_hostile_dunder"),
        ("GRAMMAR_001", "scalar", "regex", CHECKER_REGEX),
        ("GRAMMAR_002", "scalar", "canonical", "input_byte_identity_no_normalization"),
        ("SHA_001", "provenance", "four_sha", "exact_lowercase_hex_str_length_64_syntax_only"),
        ("OPAQUE_001", "provenance", "identifiers", "exact_ascii_str_1_to_256_trim_identity"),
        ("MEMBER_001", "provenance", "membership", "exact_nonempty_tuple_strict_ascending_unique"),
        ("MEMBER_002", "provenance", "member_count", "exact_int_positive_equals_length_bool_rejected"),
        ("EVIDENCE_001", "provenance", "pre_split", "true_false_exact_status_then_equality_then_membership"),
        ("ORACLE_001", "oracle", "production", "formal_call_graph_does_not_import_or_call_design_classifier"),
        ("ORACLE_002", "oracle", "parity", "committed_Exact71_all_10_fields"),
        ("ORACLE_003", "oracle", "role", "design_classifier_tests_checker_metadata_only"),
        ("SOURCE_001", "source", "boundary", "fixed_ordered_Exact13_base_tree_and_filesystem_SHA"),
        ("SOURCE_002", "source", "structure", "all_structure_before_first_source_byte_read"),
        ("ISSUE_001", "issue", "inventory", "authoritative_bytes_preserved_no_transition"),
        ("PROVIDER_001", "boundary", "provider_mapping", "unvalidated_zero_real_provider_ids"),
        ("BOUNDARY_001", "boundary", "integration", "no_adapter_registration_Exact10_runtime_ADMIT_011"),
        ("BOUNDARY_002", "boundary", "aggregation", "no_evaluate_all_rules_or_combined_verdict"),
        ("BOUNDARY_003", "boundary", "operations", "no_raw_network_download_checkpoint_split_reassignment"),
        ("BOUNDARY_004", "boundary", "training", "feature_semantics_audit_required_Step12D_smoke_only"),
        ("OUTPUT_001", "materializer", "preflight", "complete_before_first_write_exact_six_safe_entries"),
        ("OUTPUT_002", "materializer", "atomic", "same_directory_tmp_fdopen_flush_fsync_replace_cleanup"),
        ("OUTPUT_003", "materializer", "postwrite", "exact_six_regular_non_symlink"),
    )
    rows = tuple({
        "contract_id": identifier, "contract_kind": kind,
        "contract_subject": subject, "contract_value": value,
        "contract_status": "frozen",
    } for identifier, kind, subject, value in values)
    _assert(len(rows) == 41 and tuple(row["contract_id"] for row in rows) == CHECKER_CONTRACT_IDS, "checker Exact41 construction")
    return rows


def _expected_manifest() -> dict[str, object]:
    """Return the checker-owned complete Exact102 manifest contract."""
    readiness = dict(CHECKER_READINESS)
    csv_hashes = {name: EXPECTED_OUTPUT_SHA256[name] for name in CSV_OUTPUTS}
    expected: dict[str, object] = {
        "project": "CovaPIE",
        "step": "ADMIT_010 standalone evaluator interface v1",
        "stage": "covapie_bulk_download_admission_admit_010_rule_logic_interface_v1",
        "manifest_schema_version": "covapie_admit_010_rule_logic_interface_manifest_v1",
        "expected_base_commit": EXPECTED_BASE_COMMIT,
        "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "admission_rule_id": CHECKER_RULE_ID,
        "admission_rule_name": "leakage_group_assignment_before_split",
        "evaluation_phase": "pre_final_split",
        "candidate_field": CHECKER_CANDIDATE_FIELD,
        "context_item": CHECKER_CONTEXT_ITEM,
        "historical_artifact_field": CHECKER_HISTORICAL_FIELD,
        "public_api": "evaluate_admit_010(leakage_group_id, leakage_group_assignment_provenance_contract)",
        "public_signature_parameters": [
            "leakage_group_id", "leakage_group_assignment_provenance_contract",
        ],
        "public_signature_required_positional_or_keyword": True,
        "result_type": "Admit010EvaluationResult",
        "result_field_count": 10,
        "result_fields": list(CHECKER_RESULT_FIELDS),
        "result_exact_type_required": True,
        "outcome_vocabulary": ["passed", "blocked", "invalid"],
        "reason_vocabulary": ["", *CHECKER_REASONS],
        "leakage_group_prefix": "COVAPIE_LEAKAGE_GROUP_",
        "leakage_group_regex": CHECKER_REGEX,
        "validation_precedence": list(CHECKER_PRECEDENCE),
        "provenance_type": "LeakageGroupAssignmentProvenanceContractV1",
        "provenance_type_direct_committed_identity": True,
        "production_design_oracle_import_or_call": False,
        "metadata_design_oracle_parity_only": True,
        "formal_design_exact10_parity": True,
        "truth_matrix_contract": "Exact71",
        "truth_row_count": 71,
        "truth_pass_count": 71,
        "truth_group_counts": dict(EXPECTED_GROUP_COUNTS),
        "contract_row_count": 41,
        "contract_pass_count": 41,
        "source_boundary_name": "fixed_ordered_exact13_committed_source_boundary",
        "source_input_count": 13,
        "source_input_paths": list(EXPECTED_SOURCE_PATHS),
        "source_input_sha256": dict(EXPECTED_SOURCE_SHA256),
        "source_input_verification": [{
            "source_order": index,
            "source_relative_path": relative,
            "tracked": True,
            "base_tree_blob": True,
            "filesystem_regular": True,
            "non_symlink": True,
            "safe_descendant": True,
            "expected_sha256": EXPECTED_SOURCE_SHA256[relative],
            "base_tree_sha256": EXPECTED_SOURCE_SHA256[relative],
            "filesystem_sha256": EXPECTED_SOURCE_SHA256[relative],
            "source_verified": True,
        } for index, relative in enumerate(EXPECTED_SOURCE_PATHS, 1)],
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "source_audit_row_count": 13,
        "source_audit_pass_count": 13,
        "issue_inventory_row_count": 11,
        "issue_inventory_preserved_exactly": True,
        "issue_inventory_sha256": "779932531b630072ff33721e689a2865defdad477df8335a9950c8e4537476bd",
        "issue_transition": "none",
        "coverage_issue_status": "open",
        "coverage_issue_affected_rules": "ADMIT_010–ADMIT_015",
        "real_provider_leakage_group_id_count": 0,
        "leakage_group_id_provider_mapping_validated": False,
        "safety_row_count": 35,
        "safety_pass_count": 35,
        "output_files": list(OUTPUT_FILES),
        "output_file_count": 6,
        "output_sha256": csv_hashes,
        "output_sha256_excludes_manifest_self_hash": True,
        "output_materialization": dict(CHECKER_OUTPUT_MATERIALIZATION),
        "readiness": readiness,
        **readiness,
        "all_source_boundary_checks_passed": True,
        "all_predecessor_contract_checks_passed": True,
        "all_result_contract_checks_passed": True,
        "all_semantic_checks_passed": True,
        "all_truth_matrix_checks_passed": True,
        "all_issue_checks_passed": True,
        "all_safety_checks_passed": True,
        "all_checks_passed": True,
        "stop_boundaries": list(CHECKER_STOP_BOUNDARIES),
        "recommended_next_step": "design_covapie_admit_010_unified_adapter_contract_v1",
        "validation_failures": [],
    }
    _assert(type(expected) is dict and len(expected) == 102, "checker Exact102 construction")
    _assert(set(expected) == EXPECTED_MANIFEST_KEYS, "checker Exact102 keys")
    return expected


@dataclass(frozen=True)
class CheckerExpectedResult:
    admission_rule_id: str
    outcome: str
    passed: bool
    blocks_candidate: bool
    reason: str
    canonical_leakage_group_id: str
    validated_candidate_fields: tuple[tuple[str, str], ...]
    consumed_candidate_fields: tuple[str, ...]
    consumed_context_items: tuple[str, ...]
    evaluator_io_used: bool


class Hostile:
    comparisons = 0

    def _hit(self, *_: object) -> bool:
        type(self).comparisons += 1
        raise AssertionError("hostile comparison executed")

    __eq__ = __ne__ = __lt__ = __le__ = __gt__ = __ge__ = _hit

    def __len__(self) -> int:
        return int(self._hit())

    def __iter__(self) -> object:
        self._hit()
        return iter(())


def _assert(condition: bool, message: str) -> None:
    if condition is not True:
        raise AssertionError(message)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _checker_resolved_output_target_is_authorized(
    root: Path,
    repo_root: Path,
    *,
    output_root_was_relative: bool,
) -> bool:
    """Checker-owned containment logic; never calls the production helper."""
    try:
        repo_metadata = os.lstat(repo_root)
        if not stat.S_ISDIR(repo_metadata.st_mode) or stat.S_ISLNK(repo_metadata.st_mode):
            return False
        resolved_repo = repo_root.resolve(strict=True)
        parent_metadata = os.lstat(root.parent)
        if not stat.S_ISDIR(parent_metadata.st_mode) or stat.S_ISLNK(parent_metadata.st_mode):
            return False
        resolved_parent = root.parent.resolve(strict=True)
        if Path(os.path.abspath(root.parent)) != resolved_parent:
            return False
        root_metadata = os.lstat(root)
        if not stat.S_ISDIR(root_metadata.st_mode) or stat.S_ISLNK(root_metadata.st_mode):
            return False
        resolved_target = root.resolve(strict=True)
        if Path(os.path.abspath(root)) != resolved_target:
            return False
        if output_root_was_relative:
            resolved_target.relative_to(resolved_repo)
    except (OSError, RuntimeError, ValueError):
        return False
    return True


def _csv(path: Path, columns: tuple[str, ...]) -> tuple[dict[str, str], ...]:
    reader = csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"), newline=""))
    _assert(tuple(reader.fieldnames or ()) == columns, f"CSV schema: {path.name}")
    rows = tuple(dict(row) for row in reader)
    _assert(all(tuple(row) == columns and all(value is not None for value in row.values()) for row in rows), f"CSV rows: {path.name}")
    return rows


def _checker_result(outcome: str, reason: str, canonical: str) -> CheckerExpectedResult:
    return CheckerExpectedResult(
        CHECKER_RULE_ID, outcome, outcome == "passed", outcome != "passed", reason,
        canonical, ((CHECKER_CANDIDATE_FIELD, canonical),) if canonical else (),
        (CHECKER_CANDIDATE_FIELD,), (CHECKER_CONTEXT_ITEM,) if canonical else (), False,
    )


def _valid_group(value: object) -> bool:
    return type(value) is str and value.isascii() and re.fullmatch(CHECKER_REGEX, value, flags=re.ASCII) is not None


def _valid_opaque(value: object) -> bool:
    return type(value) is str and 1 <= len(value) <= 256 and value.isascii() and value == value.strip()


def _checker_expected(candidate: object, context: object) -> CheckerExpectedResult:
    if type(candidate) is not str:
        return _checker_result("invalid", CHECKER_REASONS[0], "")
    if candidate == "":
        return _checker_result("blocked", CHECKER_BLOCK_REASON, "")
    if not candidate.isascii():
        return _checker_result("invalid", CHECKER_REASONS[2], "")
    if not _valid_group(candidate):
        return _checker_result("invalid", CHECKER_REASONS[3], "")
    bad = lambda reason: _checker_result("invalid", reason, candidate)
    if type(context) is not committed_oracle.LeakageGroupAssignmentProvenanceContractV1:
        return bad(CHECKER_REASONS[4])
    value = context
    if type(value.contract_version) is not str or value.contract_version != CHECKER_VERSION:
        return bad(CHECKER_REASONS[5])
    if type(value.canonical_candidate_field_name) is not str or value.canonical_candidate_field_name != CHECKER_CANDIDATE_FIELD:
        return bad(CHECKER_REASONS[6])
    if type(value.historical_artifact_field_name) is not str or value.historical_artifact_field_name != CHECKER_HISTORICAL_FIELD:
        return bad(CHECKER_REASONS[6])
    if type(value.field_mapping_rule) is not str or value.field_mapping_rule != CHECKER_MAPPING:
        return bad(CHECKER_REASONS[6])
    if type(value.assignment_policy) is not str or value.assignment_policy != CHECKER_POLICY:
        return bad(CHECKER_REASONS[7])
    if type(value.assignment_policy_version) is not str or value.assignment_policy_version != CHECKER_POLICY_VERSION:
        return bad(CHECKER_REASONS[8])
    if type(value.assignment_stage_kind) is not str or value.assignment_stage_kind != CHECKER_STAGE:
        return bad(CHECKER_REASONS[9])
    shas = (value.assignment_manifest_sha256, value.assignment_artifact_sha256, value.group_inventory_sha256, value.sample_index_sha256)
    if any(type(item) is not str for item in shas) or any(re.fullmatch(r"[0-9a-f]{64}", item, flags=re.ASCII) is None for item in shas):
        return bad(CHECKER_REASONS[10])
    if not _valid_opaque(value.assignment_id):
        return bad(CHECKER_REASONS[11])
    if not _valid_group(value.historical_leakage_group_id):
        return bad(CHECKER_REASONS[12])
    if not _valid_opaque(value.sample_index_row_id):
        return bad(CHECKER_REASONS[13])
    members = value.member_sample_index_row_ids
    if type(members) is not tuple or not members or any(type(member) is not str for member in members):
        return bad(CHECKER_REASONS[14])
    if any(not _valid_opaque(member) for member in members) or any(a >= b for a, b in zip(members, members[1:])):
        return bad(CHECKER_REASONS[14])
    if type(value.member_count) is not int or value.member_count <= 0 or value.member_count != len(members):
        return bad(CHECKER_REASONS[15])
    if type(value.assignment_passed) is not bool or type(value.split_assignments_written) is not bool or type(value.pre_split_assignment_status) is not str:
        return _checker_result("blocked", CHECKER_BLOCK_REASON, candidate)
    if value.assignment_passed is not True or value.split_assignments_written is not False or value.pre_split_assignment_status != CHECKER_STATUS:
        return _checker_result("blocked", CHECKER_BLOCK_REASON, candidate)
    if candidate != value.historical_leakage_group_id or value.sample_index_row_id not in members:
        return _checker_result("blocked", CHECKER_BLOCK_REASON, candidate)
    return _checker_result("passed", "", candidate)


def _as_dict(value: object) -> dict[str, object]:
    return {name: getattr(value, name) for name in CHECKER_RESULT_FIELDS}


def _oracle_dict(candidate: object, context: object) -> dict[str, object]:
    return {
        "admission_rule_id": CHECKER_RULE_ID,
        **dict(committed_oracle.classify_admit_010_leakage_group_assignment_provenance_design(candidate, context)),
    }


def _check_exact71_runtime_parity() -> None:
    cases = interface._natural_cases()
    _assert(len(cases) == 71, "Exact71 case count")
    groups = {group: sum(case[0] == group for case in cases) for group in EXPECTED_GROUP_COUNTS}
    _assert(groups == EXPECTED_GROUP_COUNTS, "Exact71 group counts")
    for group, case_id, candidate, context, _precedence in cases:
        formal = interface.evaluate_admit_010(candidate, context)
        expected = _checker_expected(candidate, context)
        oracle = _oracle_dict(candidate, context)
        _assert(type(formal) is interface.Admit010EvaluationResult, f"exact result {case_id}")
        _assert(_as_dict(formal) == _as_dict(expected) == oracle, f"Exact10 parity {group}/{case_id}")


def _invalid_result(
    values: dict[str, object],
    expected: tuple[type[Exception], ...] = (TypeError, ValueError),
) -> None:
    try:
        interface.Admit010EvaluationResult(**values)
    except expected:
        return
    raise AssertionError("invalid result construction accepted")


def _valid_result_values() -> dict[str, object]:
    candidate = "COVAPIE_LEAKAGE_GROUP_000001"
    return {
        "admission_rule_id": CHECKER_RULE_ID, "outcome": "passed", "passed": True,
        "blocks_candidate": False, "reason": "", "canonical_leakage_group_id": candidate,
        "validated_candidate_fields": ((CHECKER_CANDIDATE_FIELD, candidate),),
        "consumed_candidate_fields": (CHECKER_CANDIDATE_FIELD,),
        "consumed_context_items": (CHECKER_CONTEXT_ITEM,), "evaluator_io_used": False,
    }


def _check_result_hostility() -> None:
    class Text(str):
        pass

    class TupleSubclass(tuple):
        pass

    Hostile.comparisons = 0
    cases = (
        ("admission_rule_id", Hostile()), ("admission_rule_id", Text(CHECKER_RULE_ID)),
        ("outcome", Text("passed")), ("passed", 1), ("blocks_candidate", 0),
        ("reason", Text("")), ("canonical_leakage_group_id", Text("COVAPIE_LEAKAGE_GROUP_000001")),
        ("validated_candidate_fields", []),
        ("validated_candidate_fields", TupleSubclass(((CHECKER_CANDIDATE_FIELD, "COVAPIE_LEAKAGE_GROUP_000001"),))),
        ("validated_candidate_fields", (TupleSubclass((CHECKER_CANDIDATE_FIELD, "COVAPIE_LEAKAGE_GROUP_000001")),)),
        ("validated_candidate_fields", ((Text(CHECKER_CANDIDATE_FIELD), "COVAPIE_LEAKAGE_GROUP_000001"),)),
        ("validated_candidate_fields", ((CHECKER_CANDIDATE_FIELD, Text("COVAPIE_LEAKAGE_GROUP_000001")),)),
        ("consumed_candidate_fields", TupleSubclass((CHECKER_CANDIDATE_FIELD,))),
        ("consumed_context_items", TupleSubclass((CHECKER_CONTEXT_ITEM,))),
        ("evaluator_io_used", 0),
    )
    for name, replacement in cases:
        values = _valid_result_values()
        values[name] = replacement
        _invalid_result(values)
    conflicts = (
        {"passed": False}, {"blocks_candidate": True},
        {"reason": CHECKER_BLOCK_REASON},
        {"outcome": "blocked", "passed": False, "blocks_candidate": True, "reason": ""},
        {"outcome": "invalid", "passed": False, "blocks_candidate": True, "reason": CHECKER_BLOCK_REASON},
        {"outcome": "invalid", "passed": False, "blocks_candidate": True, "reason": "LEAKAGE_GROUP_ID_TYPE_INVALID"},
        {"canonical_leakage_group_id": ""},
        {"validated_candidate_fields": ((CHECKER_CANDIDATE_FIELD, "COVAPIE_LEAKAGE_GROUP_000002"),)},
        {"consumed_context_items": ()}, {"reason": "UNKNOWN_REASON"},
    )
    for override in conflicts:
        values = _valid_result_values()
        values.update(override)
        _invalid_result(values)
    _assert(Hostile.comparisons == 0, "hostile result comparator executed")


def _called_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                names.add(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                names.add(child.func.attr)
    return names


def _check_call_graph() -> None:
    path = REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_010_rule_logic_interface.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    pending = ["evaluate_admit_010"]
    closure: set[str] = set()
    banned = {
        "classify_admit_010_leakage_group_assignment_provenance_design",
        "build_interface_state", "build_frozen_source_snapshot", "read_bytes",
        "read_text", "open", "run", "write", "system", "Popen", "provider",
    }
    while pending:
        name = pending.pop()
        if name in closure:
            continue
        closure.add(name)
        calls = _called_names(functions[name])
        _assert(not calls.intersection(banned), f"banned evaluator call: {calls.intersection(banned)}")
        pending.extend(call for call in calls if call in functions)
    _assert(closure == {
        "evaluate_admit_010", "_formal_result", "_valid_sha256",
        "_valid_opaque_id", "_is_canonical_group_id",
    }, "formal evaluator closure")
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module and node.module.endswith("provenance_contract_design_gate"):
            _assert(all(alias.name != "classify_admit_010_leakage_group_assignment_provenance_design" for alias in node.names), "production classifier import")


def _check_public_contract() -> None:
    signature = inspect.signature(interface.evaluate_admit_010)
    parameters = tuple(signature.parameters.values())
    _assert(tuple(parameter.name for parameter in parameters) == ("leakage_group_id", "leakage_group_assignment_provenance_contract"), "signature names")
    _assert(all(parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD and parameter.default is inspect.Parameter.empty for parameter in parameters), "signature kinds/defaults")
    _assert(signature.return_annotation == "Admit010EvaluationResult", "return annotation")
    _assert(tuple(field.name for field in fields(interface.Admit010EvaluationResult)) == CHECKER_RESULT_FIELDS, "Exact10 field order")
    _assert(interface.LeakageGroupAssignmentProvenanceContractV1 is committed_oracle.LeakageGroupAssignmentProvenanceContractV1, "Exact19 identity")
    _assert(interface.VALIDATION_PRECEDENCE == CHECKER_PRECEDENCE, "Exact21 precedence")
    _assert(interface.REASONS == CHECKER_REASONS, "reason vocabulary")
    _assert(interface.LEAKAGE_GROUP_REGEX == CHECKER_REGEX, "grammar")
    result = interface.evaluate_admit_010("", object())
    _assert(type(result) is interface.Admit010EvaluationResult and tuple(vars(result)) == CHECKER_RESULT_FIELDS, "exact result/storage")


def _read_verified_sources() -> dict[str, bytes]:
    _assert(tuple(EXPECTED_SOURCE_SHA256) == EXPECTED_SOURCE_PATHS and len(EXPECTED_SOURCE_PATHS) == 13, "Exact13 checker boundary")
    for relative in EXPECTED_SOURCE_PATHS:
        path = REPO_ROOT / relative
        metadata = os.lstat(path)
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", "--", relative], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
        tree = subprocess.run(["git", "ls-tree", EXPECTED_BASE_COMMIT, "--", relative], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
        header = tree.stdout.split("\t", 1)[0].split() if tree.returncode == 0 else []
        _assert(tracked.returncode == 0 and len(header) == 3 and header[1] == "blob", f"tracked/base blob {relative}")
        _assert(stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode), f"regular source {relative}")
        _assert(relative.split("/", 2)[:2] != ["data", "raw"] and not relative.startswith("checkpoints/"), f"forbidden source {relative}")
        path.resolve(strict=True).relative_to(REPO_ROOT.resolve(strict=True))
    sources: dict[str, bytes] = {}
    for relative in EXPECTED_SOURCE_PATHS:
        filesystem = (REPO_ROOT / relative).read_bytes()
        base = subprocess.run(["git", "show", f"{EXPECTED_BASE_COMMIT}:{relative}"], cwd=REPO_ROOT, capture_output=True, check=False).stdout
        expected = EXPECTED_SOURCE_SHA256[relative]
        _assert(hashlib.sha256(filesystem).hexdigest() == hashlib.sha256(base).hexdigest() == expected, f"source SHA {relative}")
        sources[relative] = filesystem
    return sources


def _truth_expected_from_design(source_bytes: bytes) -> tuple[dict[str, str], ...]:
    reader = csv.DictReader(io.StringIO(source_bytes.decode("utf-8"), newline=""))
    rows = tuple(dict(row) for row in reader)
    _assert(len(rows) == 71, "committed Exact71")
    return rows


def _validate_truth(rows: tuple[dict[str, str], ...], design: tuple[dict[str, str], ...]) -> None:
    _assert(len(rows) == len(design) == 71, "truth count")
    groups = {group: sum(row["truth_group"] == group for row in rows) for group in EXPECTED_GROUP_COUNTS}
    _assert(groups == EXPECTED_GROUP_COUNTS, "truth groups")
    for observed, frozen in zip(rows, design, strict=True):
        _assert(observed["truth_order"] == frozen["truth_order"], "truth order")
        _assert(observed["truth_group"] == frozen["truth_group"], "truth group")
        _assert(observed["case_id"] == frozen["case_id"], "case id")
        _assert(observed["input_summary"] == frozen["input_summary"], "input summary")
        _assert(observed["expected_precedence"] == frozen["expected_precedence"], "precedence")
        _assert(observed["admission_rule_id"] == CHECKER_RULE_ID, "rule id")
        for name in (
            "outcome", "passed", "blocks_candidate", "reason",
            "canonical_leakage_group_id", "validated_candidate_fields",
            "consumed_candidate_fields", "consumed_context_items", "evaluator_io_used",
        ):
            _assert(observed[name] == frozen[name], f"design projection {frozen['case_id']}/{name}")
        design_result = json.loads(observed["design_oracle_full_result"])
        expected_design = {
            "admission_rule_id": CHECKER_RULE_ID,
            "outcome": frozen["outcome"], "passed": frozen["passed"] == "true",
            "blocks_candidate": frozen["blocks_candidate"] == "true", "reason": frozen["reason"],
            "canonical_leakage_group_id": frozen["canonical_leakage_group_id"],
            "validated_candidate_fields": json.loads(frozen["validated_candidate_fields"]),
            "consumed_candidate_fields": json.loads(frozen["consumed_candidate_fields"]),
            "consumed_context_items": json.loads(frozen["consumed_context_items"]),
            "evaluator_io_used": frozen["evaluator_io_used"] == "true",
        }
        _assert(design_result == expected_design, f"design Exact10 {frozen['case_id']}")
        _assert(observed["exact10_equal_field_count"] == "10" and observed["formal_design_exact10_parity"] == observed["truth_passed"] == "true", "Exact10 parity marker")


def _validate_output_tree(root: Path, *, enforce_frozen_hashes: bool = True) -> dict[str, Any]:
    output_root_was_relative = not root.is_absolute()
    resolved_root = REPO_ROOT / root if output_root_was_relative else root
    _assert(_checker_resolved_output_target_is_authorized(
        resolved_root, REPO_ROOT, output_root_was_relative=output_root_was_relative,
    ), "output resolved containment")
    entries = tuple(resolved_root.iterdir())
    _assert({entry.name for entry in entries} == set(OUTPUT_FILES), "output exact six")
    _assert(all(
        stat.S_ISREG(os.lstat(entry).st_mode) and not stat.S_ISLNK(os.lstat(entry).st_mode)
        for entry in entries
    ), "output entries regular")
    sources = _read_verified_sources()
    contracts = _csv(resolved_root / CONTRACT_FILENAME, CHECKER_CONTRACT_COLUMNS)
    truth = _csv(resolved_root / TRUTH_FILENAME, CHECKER_TRUTH_COLUMNS)
    source_rows = _csv(resolved_root / SOURCE_FILENAME, CHECKER_SOURCE_COLUMNS)
    safety = _csv(resolved_root / SAFETY_FILENAME, CHECKER_SAFETY_COLUMNS)
    issues = _csv(resolved_root / ISSUE_FILENAME, CHECKER_ISSUE_COLUMNS)
    _assert(contracts == _expected_contract_rows(), "complete Exact41 contract equality")
    _validate_truth(truth, _truth_expected_from_design(sources[EXPECTED_SOURCE_PATHS[4]]))
    _assert(len(source_rows) == 13, "source rows")
    for index, row in enumerate(source_rows):
        relative = EXPECTED_SOURCE_PATHS[index]
        expected = EXPECTED_SOURCE_SHA256[relative]
        _assert(row["source_order"] == str(index + 1) and row["source_relative_path"] == relative, "source order/path")
        _assert(row["expected_sha256"] == row["base_tree_sha256"] == row["filesystem_sha256"] == expected, "source output SHA")
        _assert(all(row[name] == "true" for name in ("tracked", "base_tree_blob", "filesystem_regular", "non_symlink", "safe_descendant", "source_boundary_passed")), "source booleans")
    expected_safety_names = (*CHECKER_EXECUTED_SAFETY_ITEMS, *CHECKER_NOT_EXECUTED_SAFETY_ITEMS)
    _assert(tuple(row["safety_item"] for row in safety) == expected_safety_names and len(safety) == 35, "safety identity")
    for index, row in enumerate(safety):
        expected = "true" if index < len(CHECKER_EXECUTED_SAFETY_ITEMS) else "false"
        _assert(row["expected_executed"] == row["observed_executed"] == expected and row["safety_passed"] == "true", "safety row")
    _assert((resolved_root / ISSUE_FILENAME).read_bytes() == sources[EXPECTED_SOURCE_PATHS[6]], "issue byte identity")
    _assert(len(issues) == 11, "issue count")
    issue_map = {row["issue_id"]: row for row in issues}
    _assert(issue_map["LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_UNRESOLVED"]["status"] == "resolved", "provenance issue")
    coverage = issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]
    _assert(coverage["status"] == "open" and coverage["affected_rules"] == "ADMIT_010|ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015", "coverage issue")
    manifest = json.loads((resolved_root / MANIFEST_FILENAME).read_text(encoding="utf-8"))
    expected_manifest = _expected_manifest()
    _assert(type(manifest) is dict and len(manifest) == 102, "manifest Exact102 type/count")
    _assert(manifest == expected_manifest, "complete Exact102 manifest equality")
    if enforce_frozen_hashes:
        _assert({name: _sha(resolved_root / name) for name in OUTPUT_FILES} == EXPECTED_OUTPUT_SHA256, "frozen output SHA")
    return manifest


def _negative_checks(root: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="covapie-admit010-checker-") as temporary:
        base = Path(temporary)
        for mutation in ("missing", "extra", "symlink", "truth_rehash", "issue_rehash", "provider", "adapter", "registration", "runtime", "admit011", "readiness", "unknown"):
            victim = base / mutation
            shutil.copytree(root, victim)
            if mutation == "missing":
                (victim / CONTRACT_FILENAME).unlink()
            elif mutation == "extra":
                (victim / "extra.txt").write_text("extra", encoding="utf-8")
            elif mutation == "symlink":
                outside = base / "outside"
                outside.write_text("outside", encoding="utf-8")
                (victim / CONTRACT_FILENAME).unlink()
                (victim / CONTRACT_FILENAME).symlink_to(outside)
            elif mutation in ("truth_rehash", "issue_rehash"):
                name = TRUTH_FILENAME if mutation == "truth_rehash" else ISSUE_FILENAME
                path = victim / name
                original = path.read_text(encoding="utf-8")
                changed = original.replace("ADMIT_010", "ADMIT_099", 1)
                path.write_text(changed, encoding="utf-8")
                manifest_path = victim / MANIFEST_FILENAME
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["output_sha256"][name] = _sha(path)
                manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            else:
                path = victim / MANIFEST_FILENAME
                manifest = json.loads(path.read_text(encoding="utf-8"))
                if mutation == "provider":
                    manifest["leakage_group_id_provider_mapping_validated"] = True
                elif mutation == "adapter":
                    manifest["admit_010_unified_adapter_implemented"] = manifest["readiness"]["admit_010_unified_adapter_implemented"] = True
                elif mutation == "registration":
                    manifest["admit_010_registered_in_engine"] = manifest["readiness"]["admit_010_registered_in_engine"] = True
                elif mutation == "runtime":
                    manifest["unified_dispatch_runtime_with_admit_001_to_010_implemented"] = manifest["readiness"]["unified_dispatch_runtime_with_admit_001_to_010_implemented"] = True
                elif mutation == "admit011":
                    manifest["admit_011_started"] = manifest["readiness"]["admit_011_started"] = True
                elif mutation == "readiness":
                    manifest["ready_for_training"] = manifest["readiness"]["ready_for_training"] = True
                else:
                    manifest["unknown_manifest_key"] = True
                path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            try:
                _validate_output_tree(victim, enforce_frozen_hashes=False)
            except (AssertionError, OSError, ValueError, json.JSONDecodeError):
                continue
            raise AssertionError(f"negative mutation accepted: {mutation}")


def _silent_imports() -> None:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(SRC_ROOT)
    commands = (
        "import covalent_ext.covapie_bulk_download_admission_admit_010_rule_logic_interface",
        "import importlib.util,sys;p='scripts/check_covapie_bulk_download_admission_admit_010_rule_logic_interface_v1.py';s=importlib.util.spec_from_file_location('admit010_checker',p);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)",
    )
    for command in commands:
        result = subprocess.run([sys.executable, "-c", command], cwd=REPO_ROOT, env=environment, capture_output=True, text=True)
        _assert(result.returncode == 0 and result.stdout == result.stderr == "", "silent import")


def main() -> int:
    _check_public_contract()
    _check_result_hostility()
    _check_exact71_runtime_parity()
    _check_call_graph()
    first = interface.run_covapie_bulk_download_admission_admit_010_rule_logic_interface_v1(OUTPUT_ROOT)
    first_bytes = {name: (OUTPUT_ROOT / name).read_bytes() for name in OUTPUT_FILES}
    second = interface.run_covapie_bulk_download_admission_admit_010_rule_logic_interface_v1(OUTPUT_ROOT)
    second_bytes = {name: (OUTPUT_ROOT / name).read_bytes() for name in OUTPUT_FILES}
    _assert(first["manifest"] == second["manifest"] and first_bytes == second_bytes, "double materialization")
    manifest = _validate_output_tree(OUTPUT_ROOT)
    _negative_checks(OUTPUT_ROOT)
    _silent_imports()
    print("admit_010_truth_matrix=71/71")
    print("admit_010_exact10_parity=71/71")
    print("admit_010_contract=41/41")
    print("source_boundary=13/13")
    print("safety_audit=35/35")
    print("exact11_issue_inventory=11/11")
    print(f"manifest_key_count={len(manifest)}")
    print(f"readiness_count={len(manifest['readiness'])}")
    print("real_provider_leakage_group_id_count=0")
    print("leakage_group_id_provider_mapping_validated=false")
    for name in OUTPUT_FILES:
        print(f"sha256 {name} {_sha(OUTPUT_ROOT / name)}")
    print("ADMIT_010_STANDALONE_EVALUATOR_INTERFACE_CHECK=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
