#!/usr/bin/env python3
"""Independent fail-closed checker for the CovaPIE Exact13 runtime."""

from __future__ import annotations

import ast
import csv
import hashlib
import importlib
import inspect
import io
import json
import os
import stat
import subprocess
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import MappingProxyType
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = (
    "covalent_ext."
    "covapie_bulk_download_admission_unified_dispatch_runtime_"
    "with_admit_001_to_013"
)
SOURCE_RELATIVE_PATH = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_"
    "with_admit_001_to_013.py"
)
BASE = "dd17566f1b82eebcaaa49f17172a7b22a83b9c53"
BASE_PARENT = "da7bf5258365ecebde20ba1f09081b075312ebaf"
BASE_TREE = "5db3b925629cd92a9d008458f560bec2eeffb4c5"
BASE_SUBJECT = "add CovaPIE ADMIT_013 unified adapter contract design v1"
STAGE = (
    "covapie_bulk_download_admission_unified_dispatch_runtime_"
    "with_admit_001_to_013_v1"
)
OUTPUT_ROOT = ROOT / "data/derived/covalent_small" / STAGE
MARKER = (
    "# === CovaPIE ADMIT_001 TO ADMIT_013 PUBLIC "
    "RUNTIME CLOSURE END ==="
)
EXPECTED_SOURCE_SHA256 = (
    "79f95b6e178044ff5b4f5abbd6445b6cd848e81ba1a8a16cacdf831b05b9b892"
)
EXPECTED_MARKER_PREFIX_SHA256 = (
    "099a7aa4ae4369eda3262ab0c4f4345cfbe198cfa03fc13c37034d705cf1a74a"
)
EXPECTED_AST_SHA256 = {
    "_raise_dispatch_error": "adb1d13a5bea21730e5d56742c1ba46faa30b5c31d80f827a892de73cc6e1356",
    "_admit013_context_failure": "89e17e9e1db5c31fdebd8345170a53928ba6539daa2e0bf506bf5d00a3ca5f1f",
    "_admit013_adapter_failure": "d1c327d0cc67bcb4422ba7e11a8dd1cc372e951db8e0007d31069466adfafe7d",
    "_admit013_candidate_invalid": "7abea048b39749e455c2a98294f894a82447813a85abd9b7729c7225b625b94c",
    "_prevalidate_admit013_source": "69bc48a6bf9dbcf4818da671782b4733a8ea35f038607bc9be2929dee926d4cf",
    "_expected_admit013_from_oracle": "9e9059a56aa9e16a820067b298fefbc89f4c96887e7b8b15eba324c872eb884a",
    "_validate_admit013_oracle_equivalence": "b2647bb3e3adddaad37b43284e7f20cd52443adc1bb740e127788263c7fa4625",
    "_project_named_pairs_to_exact_string_pairs": "bf9e1e47d5b52e2010ecc7257e8f88ce23cf67774fb6b622dea093a2088fe34d",
    "_project_admit013_exact13": "2ed133f6641108d1148ddcecc4cc7aebeedbc83b5f716071acfaeb507931d1a9",
    "_evaluate_registered_admit_013": "96f9e081f8988a2613fdbe591155d84f447bbb8a1504b551b1fb8901d61b75b8",
    "evaluate_admission_rule": "436c53241254cf1229d4083a6caa3d555e10e17583c8ae4006275727b05fd5e9",
}
EXPECTED_AST_AGGREGATE_SHA256 = (
    "de3a8b82a56b463f456ac8aa46dcddfc30c24fcee61dfc76fe25483c74689b3c"
)

RULE_ID = "ADMIT_013"
RULE_NAME = "download_failure_fail_closed"
ADAPTER_ID = "covapie_admit_013_unified_adapter_v1"
KNOWN_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
REGISTERED_IDS = KNOWN_IDS[:13]
DOWNLOAD_FIELDS = (
    "download_result_status",
    "observed_http_status",
    "observed_content_length_bytes",
    "observed_sha256",
)
AUTHORITY_FIELDS = (
    "expected_content_length_bytes",
    "expected_sha256",
    "explicit_integrity_verdict",
)
SOURCE_FIELDS = (
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

OUTPUTS = (
    "covapie_admit_001_to_013_runtime_contract.csv",
    "covapie_admit_001_to_013_dispatch_truth_matrix.csv",
    "covapie_admit_001_to_013_registry_and_identity_audit.csv",
    "covapie_admit_001_to_013_runtime_safety_audit.csv",
    "covapie_admit_001_to_013_runtime_issue_readiness_inventory.csv",
    "covapie_admit_001_to_013_runtime_manifest.json",
)
FROZEN_OUTPUT_SHA256 = {
    "covapie_admit_001_to_013_runtime_contract.csv": "035effd65ca65ed1442bb7a29c03986390209f6d129d2ae078e223101c6a6144",
    "covapie_admit_001_to_013_dispatch_truth_matrix.csv": "78e04c469fe5a6102ec07293b1b2e59e04848b54f251abe28e2d21ba1cbd05bb",
    "covapie_admit_001_to_013_registry_and_identity_audit.csv": "6700c9360f1447f79a5180d74e1b00d5098547aca3534b5192eab2b8bdb93295",
    "covapie_admit_001_to_013_runtime_safety_audit.csv": "4b0c11cb59193bdfea9b7011e63ad4262cbbff2c1d57fd276de064997c28d8b4",
    "covapie_admit_001_to_013_runtime_issue_readiness_inventory.csv": "477b4192579d3f64dac5bd0cc61c1a378b2f28c3355251e344b79999801a5d69",
    "covapie_admit_001_to_013_runtime_manifest.json": "2940e6cc02a92b4919cdece3b1fa7c2f5e27d844f2962bb18757197266c23f79",
}

EXACT10 = (
    SOURCE_RELATIVE_PATH.as_posix(),
    (
        "scripts/check_covapie_bulk_download_admission_unified_dispatch_"
        "runtime_with_admit_001_to_013_v1.py"
    ),
    (
        "tests/test_covapie_bulk_download_admission_unified_dispatch_"
        "runtime_with_admit_001_to_013_v1.py"
    ),
    (
        "docs/covapie_bulk_download_admission_unified_dispatch_"
        "runtime_with_admit_001_to_013_v1_summary.md"
    ),
    *(f"data/derived/covalent_small/{STAGE}/{name}" for name in OUTPUTS),
)
STAGE_LOCAL_DESELECTIONS = (
    (
        "tests/test_covapie_bulk_download_admission_unified_dispatch_"
        "runtime_with_admit_001_to_012_v1.py::"
        "test_exact_ten_authorized_files_and_no_forbidden_artifacts"
    ),
    (
        "tests/test_covapie_bulk_download_admission_admit_012_formal_"
        "evaluator_interface_contract_v1.py::"
        "test_no_forbidden_stage_artifacts_or_unexpected_changes"
    ),
    (
        "tests/test_covapie_bulk_download_admission_admit_012_unified_"
        "adapter_contract_v1.py::"
        "test_exactly_ten_authorized_candidate_files_and_no_forbidden_"
        "artifact"
    ),
    (
        "tests/test_covapie_bulk_download_admission_admit_013_formal_"
        "evaluator_interface_contract_v1.py::"
        "test_no_formal_evaluator_result_adapter_registry_or_exact13_"
        "runtime"
    ),
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

MANIFEST_TOP_LEVEL_KEYS = (
    "Admit013EvaluationResult_implemented",
    "adapter_design_simulator_called_by_runtime",
    "adapter_ids",
    "adapter_ready_rule_ids",
    "admit_013_candidate_key_access_count",
    "admit_013_candidate_mapping_invalid_reason",
    "admit_013_committed_exact128_case_count",
    "admit_013_context_reasons",
    "admit_013_download_result_fields",
    "admit_013_exact13_projection",
    "admit_013_formal_call_count",
    "admit_013_formal_evaluator",
    "admit_013_handler",
    "admit_013_handler_signature",
    "admit_013_inherited_business_case_count",
    "admit_013_integrity_authority_fields",
    "admit_013_negative_source_attestation_count",
    "admit_013_normal_projection_count",
    "admit_013_oracle",
    "admit_013_oracle_call_count",
    "admit_013_oracle_result_type",
    "admit_013_private_sentinel_imported_or_passed",
    "admit_013_registered_in_engine",
    "admit_013_routing_case_count",
    "admit_013_routing_precedence",
    "admit_013_rule_logic_implemented",
    "admit_013_source_fields",
    "admit_013_source_invariant_invalid_reason",
    "admit_013_source_oracle_full_exact12_exact_type_value_equality_required",
    "admit_013_source_prevalidation_before_oracle",
    "admit_013_source_type",
    "admit_013_source_type_invalid_reason",
    "admit_013_standalone_evaluator_interface_implemented",
    "admit_013_unified_adapter_contract_frozen",
    "admit_013_unified_adapter_implemented",
    "admit_014_implemented",
    "admit_014_registered_in_engine",
    "admit_015_implemented",
    "admit_015_registered_in_engine",
    "all_checks_passed",
    "all_issue_checks_passed",
    "all_predecessor_contract_checks_passed",
    "all_registry_audit_checks_passed",
    "all_runtime_contract_checks_passed",
    "all_safety_checks_passed",
    "all_source_boundary_checks_passed",
    "all_truth_matrix_checks_passed",
    "ast_attestation_cross_python_version_portable",
    "callable_discovered_rule_ids",
    "candidate_production_source_attestation",
    "canonical_evidence_python_implementation",
    "canonical_evidence_python_version",
    "combined_candidate_verdict_implemented",
    "contract_row_count",
    "cross_rule_aggregation_implemented",
    "dispatch_error_codes",
    "dispatch_error_fields",
    "evaluate_admit_013_implemented",
    "evidence_lifecycle_hardening",
    "exact12_predecessor_identity",
    "exact13_identity",
    "expected_base_commit",
    "expected_base_parent",
    "expected_base_subject",
    "expected_base_tree",
    "feature_semantics_audit_required",
    "feature_semantics_audit_required_before_training",
    "first_twelve_handler_identity_preserved",
    "first_twelve_handler_identity_reused",
    "issue_coverage_after",
    "issue_inventory_row_count",
    "issue_transition",
    "issue_transition_count",
    "issue_transition_id",
    "known_not_registered_rule_ids",
    "known_rule_ids",
    "legacy_adapter_not_ready_rule_ids",
    "manifest_schema_version",
    "noncanonical_python_policy",
    "outcome_vocabulary",
    "output_file_count",
    "output_files",
    "output_materialization",
    "output_sha256",
    "output_sha256_excludes_manifest_self_hash",
    "predecessor_continuity_case_count",
    "predecessor_dispatcher_unchanged",
    "project",
    "provider_mapping_validated",
    "public_dispatch_cardinality",
    "public_dispatch_new_successor_function",
    "public_dispatch_precedence",
    "public_dispatch_signature",
    "public_dispatch_signature_matches_exact12",
    "public_dispatch_uses_local_registry",
    "public_type_and_constant_identity",
    "python_runtime_migration_policy",
    "readiness",
    "ready_for_bulk_download_now",
    "ready_for_training",
    "real_provider_evaluation_ready",
    "recommended_next_step",
    "registered_rule_count",
    "registered_rule_ids",
    "registry_identity_audit_row_count",
    "registry_mapping_proxy_type",
    "result_field_count",
    "result_fields",
    "result_schema_version",
    "rule_names",
    "runtime_dependency_imports",
    "safety_audit_row_count",
    "shared_exact13_identity_preserved",
    "source_boundary_name",
    "source_input_count",
    "source_input_paths",
    "source_input_sha256",
    "source_input_verification",
    "source_path_list_sha256",
    "source_path_sha256_pairs_sha256",
    "source_validation_before_output_read",
    "stage",
    "step",
    "step12d_is_final_training_feature_contract",
    "step12d_status",
    "successor_dispatcher_distinct",
    "successor_dispatcher_implemented",
    "truth_matrix_group_counts",
    "truth_matrix_row_count",
    "unified_dispatch_runtime_with_admit_001_to_013_implemented",
    "validation_failures",
)
MANIFEST_READINESS_KEYS = (
    "Admit013EvaluationResult_implemented",
    "admit_013_registered_in_engine",
    "admit_013_rule_logic_implemented",
    "admit_013_standalone_evaluator_interface_implemented",
    "admit_013_unified_adapter_contract_frozen",
    "admit_013_unified_adapter_implemented",
    "admit_014_implemented",
    "admit_014_registered_in_engine",
    "admit_015_implemented",
    "admit_015_registered_in_engine",
    "combined_candidate_verdict_implemented",
    "cross_rule_aggregation_implemented",
    "evaluate_admit_013_implemented",
    "feature_semantics_audit_required_before_training",
    "first_twelve_handler_identity_preserved",
    "provider_mapping_validated",
    "ready_for_bulk_download_now",
    "ready_for_training",
    "real_provider_evaluation_ready",
    "shared_exact13_identity_preserved",
    "step12d_is_final_training_feature_contract",
    "successor_dispatcher_implemented",
    "unified_dispatch_runtime_with_admit_001_to_013_implemented",
)
MANIFEST_OUTPUT_SHA256_KEYS = (
    "covapie_admit_001_to_013_dispatch_truth_matrix.csv",
    "covapie_admit_001_to_013_registry_and_identity_audit.csv",
    "covapie_admit_001_to_013_runtime_contract.csv",
    "covapie_admit_001_to_013_runtime_issue_readiness_inventory.csv",
    "covapie_admit_001_to_013_runtime_safety_audit.csv",
)
MANIFEST_CANDIDATE_ATTESTATION_KEYS = (
    "adapter_design_simulator_called",
    "candidate_file_mode",
    "candidate_relative_path",
    "definition_count",
    "definition_names",
    "marker_prefix_sha256",
    "normalized_ast_sha256",
    "production_full_sha256",
    "public_closure_pure_memory",
)
MANIFEST_EVIDENCE_HARDENING_KEYS = (
    "checker_exact6_full_identity_post_traversal",
    "checker_manifest_duplicate_and_exact_key_rejection",
    "exact10_lifecycle_exact_inventory",
    "production_source_root_parent_dir_fd_traversal",
    "publisher_existing_set_post_fsync_destination_binding",
    "publisher_rename_success_post_fsync_destination_binding",
    "successor_regression_stage_local_deselection_count",
)


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _canonical_guard() -> None:
    implementation = sys.implementation.name
    version = tuple(sys.version_info[:3])
    if implementation != "cpython" or version != (3, 10, 4):
        observed = ".".join(map(str, version))
        raise AssertionError(
            "required: CPython 3.10.4; "
            f"observed implementation: {implementation}; "
            f"observed version: {observed}; "
            "frozen evidence is Python-version-sensitive; "
            "noncanonical Python is not authorized to build artifacts "
            "or run the checker"
        )


def _git(*arguments: str) -> bytes:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        raise AssertionError(f"git command failed: {arguments}")
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


def _parent_chain(parent: Path, anchor: Path) -> None:
    current = parent
    while True:
        item = os.lstat(current)
        if not stat.S_ISDIR(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise AssertionError("parent chain unsafe")
        if current == anchor:
            break
        if current == current.parent:
            raise AssertionError("parent chain escaped")
        current = current.parent
    if parent.resolve(strict=True) != parent:
        raise AssertionError("parent chain resolved drift")


DIRECTORY_FLAGS = (
    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
)
READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
MAX_CANDIDATE_BYTES = 100 * 1024 * 1024


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
        raise AssertionError("pinned directory binding drift")


def _open_pinned_parent(
    root: Path,
    root_descriptor: int,
    root_identity: tuple[int, int, int],
    relative: Path,
) -> tuple[tuple[Path, int, tuple[int, int, int]], ...]:
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
                raise AssertionError("source parent lexical identity drift")
            child = os.open(
                part,
                DIRECTORY_FLAGS,
                dir_fd=current_descriptor,
            )
            if _identity(os.fstat(child)) != identity:
                os.close(child)
                raise AssertionError(
                    "source parent descriptor identity drift"
                )
            opened.append((current_path, child, identity))
            current_descriptor = child
        _assert_pinned_directory(root, root_descriptor, root_identity)
        return tuple(opened)
    except BaseException:
        for _path, descriptor, _expected in reversed(opened):
            os.close(descriptor)
        raise


def _assert_source_bindings(
    root: Path,
    root_descriptor: int,
    root_identity: tuple[int, int, int],
    parent_descriptors: Sequence[
        tuple[Path, int, tuple[int, int, int]]
    ],
) -> None:
    _assert_pinned_directory(root, root_descriptor, root_identity)
    for path, descriptor, identity in parent_descriptors:
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
        or lexical.st_size > MAX_CANDIDATE_BYTES
    ):
        raise AssertionError("source leaf lexical identity drift")
    return identity


def _read_pinned_source_at(
    root: Path,
    root_descriptor: int,
    root_identity: tuple[int, int, int],
    relative: Path,
    parent_descriptors: Sequence[
        tuple[Path, int, tuple[int, int, int]]
    ],
    expected: tuple[int, int, int, int, int, int],
) -> bytes:
    parent_descriptor = (
        parent_descriptors[-1][1]
        if parent_descriptors
        else root_descriptor
    )
    if (
        _source_leaf_identity(root, relative, parent_descriptor)
        != expected
    ):
        raise AssertionError("pinned source changed before open")
    descriptor = os.open(
        relative.name,
        READ_FLAGS,
        dir_fd=parent_descriptor,
    )
    try:
        if _full_identity(os.fstat(descriptor)) != expected:
            raise AssertionError("pinned descriptor identity drift")
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
            raise AssertionError("pinned source changed during read")
        _assert_source_bindings(
            root,
            root_descriptor,
            root_identity,
            parent_descriptors,
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
        raise AssertionError("source root unsafe")
    root_descriptor = os.open(root, DIRECTORY_FLAGS)
    parent_descriptors: tuple[
        tuple[Path, int, tuple[int, int, int]], ...
    ] = ()
    try:
        _assert_pinned_directory(root, root_descriptor, root_identity)
        parent_descriptors = _open_pinned_parent(
            root,
            root_descriptor,
            root_identity,
            relative,
        )
        parent_descriptor = (
            parent_descriptors[-1][1]
            if parent_descriptors
            else root_descriptor
        )
        leaf_identity = _source_leaf_identity(
            root,
            relative,
            parent_descriptor,
        )
        return (
            _read_pinned_source_at(
                root,
                root_descriptor,
                root_identity,
                relative,
                parent_descriptors,
                leaf_identity,
            ),
            leaf_identity,
        )
    finally:
        for _path, descriptor, _expected in reversed(
            parent_descriptors
        ):
            os.close(descriptor)
        os.close(root_descriptor)


def _verify_base_and_sources() -> tuple[dict[str, Any], ...]:
    identity = _git(
        "show",
        "-s",
        "--format=%H%n%P%n%T%n%s",
        BASE,
    ).decode().splitlines()
    if identity != [BASE, BASE_PARENT, BASE_TREE, BASE_SUBJECT]:
        raise AssertionError("base identity drift")
    _git("merge-base", "--is-ancestor", BASE, "HEAD")
    if len(SOURCE_BOUNDARY) != 20:
        raise AssertionError("Exact20 source boundary drift")
    root_item = os.lstat(ROOT)
    root_identity = _identity(root_item)
    if (
        not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
        or ROOT.resolve(strict=True) != ROOT
    ):
        raise AssertionError("repository identity unsafe")
    root_descriptor = os.open(ROOT, DIRECTORY_FLAGS)
    opened_chains: list[
        tuple[tuple[Path, int, tuple[int, int, int]], ...]
    ] = []
    try:
        _assert_pinned_directory(ROOT, root_descriptor, root_identity)
        inspected = []
        for order, (raw_path, expected) in enumerate(
            SOURCE_BOUNDARY,
            1,
        ):
            relative = Path(raw_path)
            if (
                relative.is_absolute()
                or not relative.parts
                or ".." in relative.parts
                or relative.parts[:2] == ("data", "raw")
                or relative.parts[0] == "checkpoints"
                or STAGE in relative.parts
            ):
                raise AssertionError("unsafe source path")
            parent_descriptors = _open_pinned_parent(
                ROOT,
                root_descriptor,
                root_identity,
                relative,
            )
            opened_chains.append(parent_descriptors)
            parent_descriptor = (
                parent_descriptors[-1][1]
                if parent_descriptors
                else root_descriptor
            )
            leaf_identity = _source_leaf_identity(
                ROOT,
                relative,
                parent_descriptor,
            )
            if (
                _git(
                    "ls-files",
                    "--error-unmatch",
                    "--",
                    raw_path,
                ).decode()
                != f"{raw_path}\n"
            ):
                raise AssertionError("source not tracked")
            tree = _git("ls-tree", BASE, "--", raw_path).splitlines()
            index = _git(
                "ls-files",
                "--stage",
                "--",
                raw_path,
            ).splitlines()
            if (
                len(tree) != 1
                or b"\t" not in tree[0]
                or len(index) != 1
                or b"\t" not in index[0]
            ):
                raise AssertionError("base/index source cardinality")
            metadata, observed_path = tree[0].split(b"\t", 1)
            mode, kind, blob = metadata.split()
            index_metadata, index_path = index[0].split(b"\t", 1)
            index_mode, index_blob, index_stage = (
                index_metadata.split()
            )
            if (
                observed_path.decode() != raw_path
                or index_path.decode() != raw_path
                or mode not in (b"100644", b"100755")
                or kind != b"blob"
                or (index_mode, index_blob, index_stage)
                != (mode, blob, b"0")
            ):
                raise AssertionError("base/current-index source identity")
            inspected.append(
                (
                    order,
                    raw_path,
                    expected,
                    relative,
                    parent_descriptors,
                    leaf_identity,
                    mode,
                )
            )
        records = []
        for (
            order,
            raw_path,
            expected,
            relative,
            parent_descriptors,
            leaf_identity,
            mode,
        ) in inspected:
            filesystem = _read_pinned_source_at(
                ROOT,
                root_descriptor,
                root_identity,
                relative,
                parent_descriptors,
                leaf_identity,
            )
            base = _git("show", f"{BASE}:{raw_path}")
            if _sha(filesystem) != expected or _sha(base) != expected:
                raise AssertionError(f"source SHA drift: {raw_path}")
            records.append(
                {
                    "source_order": order,
                    "source_relative_path": raw_path,
                    "expected_sha256": expected,
                    "base_tree_mode": mode.decode(),
                    "content": filesystem,
                }
            )
        _assert_pinned_directory(ROOT, root_descriptor, root_identity)
        return tuple(records)
    finally:
        for parent_descriptors in reversed(opened_chains):
            for _path, descriptor, _expected in reversed(
                parent_descriptors
            ):
                os.close(descriptor)
        os.close(root_descriptor)


def _attest_candidate() -> dict[str, Any]:
    target = ROOT / SOURCE_RELATIVE_PATH
    content, identity = _read_one_pinned_source(
        ROOT,
        SOURCE_RELATIVE_PATH,
    )
    if EXPECTED_SOURCE_SHA256 and _sha(content) != EXPECTED_SOURCE_SHA256:
        raise AssertionError("candidate production SHA drift")
    text = content.decode("utf-8")
    if text.count(MARKER) != 1:
        raise AssertionError("candidate public marker drift")
    prefix = text.split(MARKER, 1)[0].encode("utf-8")
    if (
        EXPECTED_MARKER_PREFIX_SHA256
        and _sha(prefix) != EXPECTED_MARKER_PREFIX_SHA256
    ):
        raise AssertionError("candidate marker-prefix SHA drift")
    tree = ast.parse(content, filename=str(target))
    marker_line = text[: text.index(MARKER)].count("\n") + 1
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
        raise AssertionError("public definition order/cardinality drift")
    hashes = {
        name: _sha(
            ast.dump(
                definitions[name],
                annotate_fields=True,
                include_attributes=False,
            ).encode()
        )
        for name in PUBLIC_DEFINITIONS
    }
    if EXPECTED_AST_SHA256 and hashes != EXPECTED_AST_SHA256:
        raise AssertionError("public normalized AST SHA drift")
    aggregate = _sha(
        json.dumps(
            hashes,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    )
    if aggregate != EXPECTED_AST_AGGREGATE_SHA256:
        raise AssertionError("public normalized AST aggregate SHA drift")
    prefix_text = prefix.decode()
    forbidden = (
        "simulate_admit_013_unified_adapter_design",
        "covapie_bulk_download_admission_admit_013_unified_adapter_contract_design_gate",
        "os.open",
        "subprocess.",
        "socket.",
        "data/raw",
        "checkpoints",
        "evaluate_all_rules",
        "combined_candidate_verdict",
    )
    if any(token in prefix_text for token in forbidden):
        raise AssertionError("forbidden public closure dependency/operation")
    project_imports = []
    for node in ast.parse(prefix).body:
        if isinstance(node, ast.ImportFrom) and node.module == "covalent_ext":
            project_imports.extend(
                (alias.name, alias.asname) for alias in node.names
            )
    if project_imports != [
        (
            "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012",
            "predecessor",
        ),
        (
            "covapie_bulk_download_admission_admit_013_rule_logic_interface",
            "admit013",
        ),
        (
            "covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_design_gate",
            "admit013_oracle",
        ),
    ]:
        raise AssertionError("public import provenance drift")
    return {
        "content": content,
        "sha256": _sha(content),
        "marker_prefix_sha256": _sha(prefix),
        "ast_sha256": hashes,
        "identity": identity,
        "path": target,
    }


def _assert_candidate_unchanged(attested: Mapping[str, Any]) -> None:
    target = attested["path"]
    if _full_identity(os.lstat(target)) != attested["identity"]:
        raise AssertionError("attested candidate identity changed")
    content, identity = _read_one_pinned_source(
        ROOT,
        SOURCE_RELATIVE_PATH,
    )
    if (
        identity != attested["identity"]
        or content != attested["content"]
    ):
        raise AssertionError("attested candidate bytes changed")


def _csv(
    content: bytes,
    columns: Sequence[str],
) -> tuple[dict[str, str], ...]:
    reader = csv.DictReader(io.StringIO(content.decode(), newline=""))
    if tuple(reader.fieldnames or ()) != tuple(columns):
        raise AssertionError("CSV header drift")
    rows = tuple(dict(row) for row in reader)
    if any(
        tuple(row) != tuple(columns)
        or any(value is None for value in row.values())
        for row in rows
    ):
        raise AssertionError("CSV row shape drift")
    return rows


def _unique_json_object(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AssertionError(f"duplicate manifest key: {key}")
        result[key] = value
    return result


def _manifest_object(content: bytes) -> dict[str, Any]:
    try:
        manifest = json.loads(
            content.decode("utf-8"),
            object_pairs_hook=_unique_json_object,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AssertionError("manifest JSON invalid") from error
    if type(manifest) is not dict:
        raise AssertionError("manifest object required")
    if tuple(manifest) != MANIFEST_TOP_LEVEL_KEYS:
        raise AssertionError("manifest exact top-level keys/order drift")
    exact_nested = (
        ("readiness", MANIFEST_READINESS_KEYS),
        ("output_sha256", MANIFEST_OUTPUT_SHA256_KEYS),
        (
            "candidate_production_source_attestation",
            MANIFEST_CANDIDATE_ATTESTATION_KEYS,
        ),
        (
            "evidence_lifecycle_hardening",
            MANIFEST_EVIDENCE_HARDENING_KEYS,
        ),
    )
    for name, expected_keys in exact_nested:
        value = manifest[name]
        if type(value) is not dict or tuple(value) != expected_keys:
            raise AssertionError(
                f"manifest exact nested keys/order drift: {name}"
            )
    return manifest


def _assert_output_snapshot(
    root: Path,
    parent_descriptor: int,
    parent_identity: tuple[int, int, int, int, int, int],
    root_descriptor: int,
    root_identity: tuple[int, int, int, int, int, int],
    leaf_identities: Mapping[
        str, tuple[int, int, int, int, int, int]
    ],
) -> None:
    parent_lexical = os.lstat(root.parent)
    root_lexical = os.lstat(root)
    root_relative = os.stat(
        root.name,
        dir_fd=parent_descriptor,
        follow_symlinks=False,
    )
    if (
        _full_identity(parent_lexical) != parent_identity
        or _full_identity(os.fstat(parent_descriptor)) != parent_identity
        or not stat.S_ISDIR(parent_lexical.st_mode)
        or stat.S_ISLNK(parent_lexical.st_mode)
        or _full_identity(root_lexical) != root_identity
        or _full_identity(root_relative) != root_identity
        or _full_identity(os.fstat(root_descriptor)) != root_identity
        or not stat.S_ISDIR(root_lexical.st_mode)
        or stat.S_ISLNK(root_lexical.st_mode)
    ):
        raise AssertionError("output parent/root binding drift")
    names = tuple(os.listdir(root_descriptor))
    if len(names) != len(OUTPUTS) or set(names) != set(OUTPUTS):
        raise AssertionError("Exact6 post-traversal inventory drift")
    for name, expected in leaf_identities.items():
        lexical = os.lstat(root / name)
        relative = os.stat(
            name,
            dir_fd=root_descriptor,
            follow_symlinks=False,
        )
        if (
            _full_identity(lexical) != expected
            or _full_identity(relative) != expected
            or not stat.S_ISREG(lexical.st_mode)
            or stat.S_ISLNK(lexical.st_mode)
            or lexical.st_size > MAX_CANDIDATE_BYTES
        ):
            raise AssertionError("output post-traversal leaf drift")


def _read_output_leaf(
    root: Path,
    root_descriptor: int,
    name: str,
    expected: tuple[int, int, int, int, int, int],
) -> bytes:
    lexical = os.lstat(root / name)
    relative = os.stat(
        name,
        dir_fd=root_descriptor,
        follow_symlinks=False,
    )
    if (
        _full_identity(lexical) != expected
        or _full_identity(relative) != expected
        or not stat.S_ISREG(lexical.st_mode)
        or stat.S_ISLNK(lexical.st_mode)
        or lexical.st_size > MAX_CANDIDATE_BYTES
    ):
        raise AssertionError("output leaf changed before read")
    descriptor = os.open(
        name,
        READ_FLAGS,
        dir_fd=root_descriptor,
    )
    try:
        if _full_identity(os.fstat(descriptor)) != expected:
            raise AssertionError("output stat/open race")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1 << 16)
            if not chunk:
                break
            chunks.append(chunk)
        if (
            _full_identity(os.fstat(descriptor)) != expected
            or _full_identity(os.lstat(root / name)) != expected
            or _full_identity(
                os.stat(
                    name,
                    dir_fd=root_descriptor,
                    follow_symlinks=False,
                )
            )
            != expected
        ):
            raise AssertionError("output leaf changed during read")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _output_bytes(output_root: Path = OUTPUT_ROOT) -> dict[str, bytes]:
    root = Path(os.path.abspath(output_root))
    _parent_chain(root.parent, Path(root.anchor))
    parent_item = os.lstat(root.parent)
    parent_identity = _full_identity(parent_item)
    if (
        not stat.S_ISDIR(parent_item.st_mode)
        or stat.S_ISLNK(parent_item.st_mode)
    ):
        raise AssertionError("output parent unsafe")
    parent_descriptor = os.open(root.parent, DIRECTORY_FLAGS)
    root_descriptor: int | None = None
    try:
        if _full_identity(os.fstat(parent_descriptor)) != parent_identity:
            raise AssertionError("output parent descriptor drift")
        root_item = os.lstat(root)
        root_relative = os.stat(
            root.name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
        root_identity = _full_identity(root_item)
        if (
            _full_identity(root_relative) != root_identity
            or not stat.S_ISDIR(root_item.st_mode)
            or stat.S_ISLNK(root_item.st_mode)
            or root.resolve(strict=True) != root
        ):
            raise AssertionError("output root unsafe")
        names = tuple(os.listdir(root))
        if len(names) != len(OUTPUTS) or set(names) != set(OUTPUTS):
            raise AssertionError("Exact6 inventory drift")
        root_descriptor = os.open(
            root.name,
            DIRECTORY_FLAGS,
            dir_fd=parent_descriptor,
        )
        if _full_identity(os.fstat(root_descriptor)) != root_identity:
            raise AssertionError("output root descriptor drift")
        identities = {}
        for name in OUTPUTS:
            lexical = os.lstat(root / name)
            relative = os.stat(
                name,
                dir_fd=root_descriptor,
                follow_symlinks=False,
            )
            identity = _full_identity(lexical)
            if (
                _full_identity(relative) != identity
                or not stat.S_ISREG(lexical.st_mode)
                or stat.S_ISLNK(lexical.st_mode)
                or lexical.st_size > MAX_CANDIDATE_BYTES
            ):
                raise AssertionError("output leaf unsafe")
            identities[name] = identity
        contents = {
            name: _read_output_leaf(
                root,
                root_descriptor,
                name,
                identities[name],
            )
            for name in OUTPUTS
        }
        _assert_output_snapshot(
            root,
            parent_descriptor,
            parent_identity,
            root_descriptor,
            root_identity,
            identities,
        )
        return contents
    finally:
        if root_descriptor is not None:
            os.close(root_descriptor)
        os.close(parent_descriptor)


def _verify_output_tree(
    source_records: Sequence[Mapping[str, Any]],
) -> dict[str, str]:
    contents = _output_bytes()
    hashes = {name: _sha(content) for name, content in contents.items()}
    if FROZEN_OUTPUT_SHA256 and hashes != FROZEN_OUTPUT_SHA256:
        raise AssertionError("frozen Exact6 SHA drift")
    contract = _csv(contents[OUTPUTS[0]], CONTRACT_COLUMNS)
    truth = _csv(contents[OUTPUTS[1]], TRUTH_COLUMNS)
    registry = _csv(contents[OUTPUTS[2]], REGISTRY_COLUMNS)
    safety = _csv(contents[OUTPUTS[3]], SAFETY_COLUMNS)
    issues = _csv(contents[OUTPUTS[4]], ISSUE_COLUMNS)
    manifest = _manifest_object(contents[OUTPUTS[5]])
    if (
        len(contract) != 59
        or len(truth) != 885
        or len(registry) != 39
        or len(safety) != 30
        or len(issues) != 23
    ):
        raise AssertionError("Exact6 row-count drift")
    if any(
        row["contract_passed"] != "true"
        or row["expected_value"] != row["observed_value"]
        for row in contract
    ):
        raise AssertionError("contract status drift")
    groups = Counter(row["case_group"] for row in truth)
    if groups != {
        "predecessor_exact12_all_cases": 694,
        "admit013_exact128_normal": 102,
        "admit013_exact128_negative": 26,
        "admit013_exact44_routing": 44,
        "successor_dispatcher": 19,
    }:
        raise AssertionError("truth group-count drift")
    if (
        tuple(row["case_order"] for row in truth)
        != tuple(str(index) for index in range(1, 886))
        or len({row["case_id"] for row in truth}) != 885
        or any(
            row["case_passed"] != "true"
            or row["expected_result_or_error"]
            != row["observed_result_or_error"]
            or row["first_twelve_handler_identity_preserved"] != "true"
            for row in truth
        )
    ):
        raise AssertionError("truth status/order/identity drift")
    predecessor_truth = _csv(
        source_records[2]["content"],
        (
            "case_order",
            "case_id",
            "case_group",
            "entrypoint",
            "rule_id_representation",
            "candidate_record_representation",
            "batch_context_representation",
            "evaluation_context_representation",
            "download_result_context_representation",
            "stage_authorization_context_representation",
            "lookup_order",
            "evaluation_lookup_count",
            "download_lookup_count",
            "candidate_key_access_count",
            "formal_call_count",
            "oracle_call_count",
            "expected_result_or_error",
            "observed_result_or_error",
            "old_handler_identity_preserved",
            "case_passed",
        ),
    )
    if tuple(row["source_case_id"] for row in truth[:694]) != tuple(
        row["case_id"] for row in predecessor_truth
    ):
        raise AssertionError("predecessor Exact694 lineage drift")
    formal_truth = _csv(
        source_records[17]["content"],
        tuple(
            next(
                csv.reader(
                    io.StringIO(source_records[17]["content"].decode())
                )
            )
        ),
    )
    if tuple(
        row["source_case_id"] for row in truth[694 : 694 + 128]
    ) != tuple(row["case_id"] for row in formal_truth):
        raise AssertionError("ADMIT_013 Exact128 identity drift")
    if Counter(row["assertion_kind"] for row in formal_truth) != {
        "formal_interface_projection": 102,
        "result_contract_rejection": 26,
    }:
        raise AssertionError("ADMIT_013 Exact102/Exact26 source split")
    if (
        sum(
            row["case_group"] == "inherited_exact7_business_projection"
            for row in formal_truth
        )
        != 23
    ):
        raise AssertionError("ADMIT_013 inherited Exact23 business drift")
    routing = _csv(
        source_records[8]["content"],
        tuple(
            next(
                csv.reader(
                    io.StringIO(source_records[8]["content"].decode())
                )
            )
        ),
    )
    if tuple(
        row["source_case_id"]
        for row in truth[694 + 128 : 694 + 128 + 44]
    ) != tuple(row["case_id"] for row in routing):
        raise AssertionError("ADMIT_013 Exact44 routing lineage drift")
    if any(
        row["audit_passed"] != "true"
        or row["expected_value"] != row["observed_value"]
        for row in registry
    ):
        raise AssertionError("registry audit drift")
    required_registry = {
        "predecessor_registry_order",
        "successor_registry_order",
        "handler_binding:ADMIT_013",
        "successor_dispatcher_distinct",
        "dispatcher_signature_equal",
        *(f"handler_identity:{rule_id}" for rule_id in KNOWN_IDS[:12]),
        "ADMIT_014_unregistered",
        "ADMIT_015_unregistered",
    }
    if not required_registry <= {row["audit_item"] for row in registry}:
        raise AssertionError("registry audit coverage drift")
    if any(
        row["safety_passed"] != "true"
        or row["expected_executed"] != row["observed_executed"]
        for row in safety
    ):
        raise AssertionError("safety audit drift")
    source_issues = _csv(source_records[10]["content"], ISSUE_COLUMNS)
    changed = [
        (
            source["issue_id"],
            {
                key
                for key in ISSUE_COLUMNS
                if source[key] != successor[key]
            },
        )
        for source, successor in zip(source_issues, issues, strict=True)
        if source != successor
    ]
    if len(changed) != 1 or changed[0][0] != (
        "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
    ):
        raise AssertionError("issue transition cardinality/identity drift")
    issue_map = {row["issue_id"]: row for row in issues}
    coverage = issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]
    if (
        coverage["affected_rules"] != "ADMIT_014|ADMIT_015"
        or coverage["status"] != "open"
        or coverage["integration_transition"]
        != "unified_dispatch_runtime_with_admit_001_to_013_implemented_v1"
        or issue_map[
            "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"
        ]["status"]
        != "open"
    ):
        raise AssertionError("issue transition semantics drift")
    required_manifest = {
        "project": "CovaPIE",
        "stage": STAGE,
        "expected_base_commit": BASE,
        "expected_base_parent": BASE_PARENT,
        "expected_base_tree": BASE_TREE,
        "expected_base_subject": BASE_SUBJECT,
        "source_input_count": 20,
        "registered_rule_ids": list(REGISTERED_IDS),
        "known_not_registered_rule_ids": ["ADMIT_014", "ADMIT_015"],
        "registered_rule_count": 13,
        "contract_row_count": 59,
        "truth_matrix_row_count": 885,
        "predecessor_continuity_case_count": 694,
        "admit_013_committed_exact128_case_count": 128,
        "admit_013_normal_projection_count": 102,
        "admit_013_negative_source_attestation_count": 26,
        "admit_013_inherited_business_case_count": 23,
        "admit_013_routing_case_count": 44,
        "registry_identity_audit_row_count": 39,
        "safety_audit_row_count": 30,
        "issue_inventory_row_count": 23,
        "issue_transition_count": 1,
        "combined_candidate_verdict_implemented": False,
        "cross_rule_aggregation_implemented": False,
        "provider_mapping_validated": False,
        "ready_for_training": False,
        "recommended_next_step": (
            "audit_covapie_admit_014_formal_evaluator_interface_"
            "preconditions_v1"
        ),
        "all_checks_passed": True,
    }
    if any(
        manifest.get(key) != value
        for key, value in required_manifest.items()
    ):
        raise AssertionError("manifest required semantics drift")
    readiness = {name: True for name in TRUE_READINESS} | {
        name: False for name in FALSE_READINESS
    }
    if manifest.get("readiness") != readiness or any(
        manifest.get(name) is not value
        for name, value in readiness.items()
    ):
        raise AssertionError("manifest readiness drift")
    if (
        manifest.get("source_input_paths")
        != [path for path, _ in SOURCE_BOUNDARY]
        or manifest.get("source_input_sha256") != dict(SOURCE_BOUNDARY)
        or manifest.get("output_files") != list(OUTPUTS)
        or manifest.get("output_sha256")
        != {name: hashes[name] for name in OUTPUTS[:5]}
    ):
        raise AssertionError("manifest source/output/order drift")
    attestation = manifest.get("candidate_production_source_attestation")
    if (
        type(attestation) is not dict
        or attestation.get("production_full_sha256")
        != EXPECTED_SOURCE_SHA256
        or attestation.get("marker_prefix_sha256")
        != EXPECTED_MARKER_PREFIX_SHA256
        or attestation.get("normalized_ast_sha256")
        != EXPECTED_AST_SHA256
        or attestation.get("definition_names")
        != list(PUBLIC_DEFINITIONS)
    ):
        raise AssertionError("manifest candidate source attestation drift")
    hardening = manifest["evidence_lifecycle_hardening"]
    if hardening != {
        "checker_exact6_full_identity_post_traversal": True,
        "checker_manifest_duplicate_and_exact_key_rejection": True,
        "exact10_lifecycle_exact_inventory": True,
        "production_source_root_parent_dir_fd_traversal": True,
        "publisher_existing_set_post_fsync_destination_binding": True,
        "publisher_rename_success_post_fsync_destination_binding": True,
        "successor_regression_stage_local_deselection_count": 4,
    }:
        raise AssertionError("manifest evidence hardening drift")
    return hashes


class CountingMapping(Mapping[str, object]):
    def __init__(
        self,
        values: Mapping[str, object],
        *,
        error_key: str | None = None,
        error: Exception | None = None,
    ) -> None:
        self.values = dict(values)
        self.error_key = error_key
        self.error = error
        self.calls: list[str] = []
        self.iterated = False
        self.sized = False
        self.get_called = False
        self.contains_called = False

    def __getitem__(self, key: str) -> object:
        self.calls.append(key)
        if key == self.error_key and self.error is not None:
            raise self.error
        return self.values[key]

    def __iter__(self):
        self.iterated = True
        return iter(self.values)

    def __len__(self) -> int:
        self.sized = True
        return len(self.values)

    def get(self, key: str, default: object = None) -> object:
        self.get_called = True
        return super().get(key, default)

    def __contains__(self, key: object) -> bool:
        self.contains_called = True
        return super().__contains__(key)


class CandidateBomb(Mapping[str, object]):
    def __init__(self) -> None:
        self.accesses = 0

    def __getitem__(self, key: str) -> object:
        self.accesses += 1
        raise AssertionError("candidate key accessed")

    def __iter__(self):
        raise AssertionError("candidate iterated")

    def __len__(self) -> int:
        raise AssertionError("candidate sized")


def _runtime_tuple(value: object, names: Sequence[str]) -> tuple[object, ...]:
    return tuple(getattr(value, name) for name in names)


def _verify_runtime(runtime: Any) -> None:
    predecessor = runtime.predecessor
    original = importlib.import_module(
        "covalent_ext."
        "covapie_bulk_download_admission_minimal_unified_dispatch_"
        "shell_with_admit_004"
    )
    for name in (
        "UnifiedAdmissionRuleEvaluation",
        "UnifiedAdmissionDispatchError",
        "RESULT_SCHEMA_VERSION",
        "RESULT_FIELDS",
        "DISPATCH_ERROR_FIELDS",
        "DISPATCH_ERROR_CODES",
        "OUTCOME_VOCABULARY",
    ):
        if (
            getattr(runtime, name) is not getattr(predecessor, name)
            or getattr(runtime, name) is not getattr(original, name)
        ):
            raise AssertionError(f"shared identity drift: {name}")
    if (
        runtime.evaluate_admission_rule
        is predecessor.evaluate_admission_rule
        or inspect.signature(runtime.evaluate_admission_rule)
        != inspect.signature(predecessor.evaluate_admission_rule)
    ):
        raise AssertionError("successor dispatcher identity/signature drift")
    expected_handler_signature = (
        "(candidate_record: 'object', *, batch_context: 'object', "
        "evaluation_context: 'object', download_result_context: 'object', "
        "stage_authorization_context: 'object') -> "
        "'UnifiedAdmissionRuleEvaluation'"
    )
    if (
        str(inspect.signature(runtime._evaluate_registered_admit_013))
        != expected_handler_signature
    ):
        raise AssertionError("ADMIT_013 handler signature drift")
    if (
        type(runtime.EVALUATOR_REGISTRY) is not MappingProxyType
        or tuple(runtime.EVALUATOR_REGISTRY) != REGISTERED_IDS
        or any(
            runtime.EVALUATOR_REGISTRY[rule_id]
            is not predecessor.EVALUATOR_REGISTRY[rule_id]
            for rule_id in KNOWN_IDS[:12]
        )
        or runtime.EVALUATOR_REGISTRY[RULE_ID]
        is not runtime._evaluate_registered_admit_013
    ):
        raise AssertionError("Exact13 registry/identity drift")
    if (
        tuple(runtime.KNOWN_RULE_IDS) != KNOWN_IDS
        or tuple(runtime.CALLABLE_DISCOVERED_RULE_IDS) != REGISTERED_IDS
        or tuple(runtime.ADAPTER_READY_RULE_IDS) != REGISTERED_IDS
        or tuple(runtime.LEGACY_ADAPTER_NOT_READY_RULE_IDS) != ()
    ):
        raise AssertionError("known/callable/ready sets drift")
    valid_download = {
        "download_result_status": "success",
        "observed_http_status": 200,
        "observed_content_length_bytes": 7,
        "observed_sha256": "0123456789abcdef" * 4,
    }
    valid_authority = {
        "expected_content_length_bytes": 7,
        "expected_sha256": "0123456789abcdef" * 4,
        "explicit_integrity_verdict": "verified",
    }
    candidate = CandidateBomb()
    download = CountingMapping(valid_download)
    authority = CountingMapping(valid_authority)
    result = runtime._evaluate_registered_admit_013(
        candidate,
        batch_context=None,
        evaluation_context=authority,
        download_result_context=download,
        stage_authorization_context=None,
    )
    if (
        result.outcome != "passed"
        or candidate.accesses != 0
        or download.calls != list(DOWNLOAD_FIELDS)
        or authority.calls != list(AUTHORITY_FIELDS)
        or any(
            (
                download.iterated,
                download.sized,
                download.get_called,
                download.contains_called,
                authority.iterated,
                authority.sized,
                authority.get_called,
                authority.contains_called,
            )
        )
        or result.normalized_values[1][1] != "200"
        or result.normalized_values[2][1] != "7"
        or result.normalized_values[4][1] != "7"
        or any(
            name in AUTHORITY_FIELDS
            for name, _ in result.validated_candidate_fields
        )
    ):
        raise AssertionError("ADMIT_013 success routing/projection drift")
    for index in range(4):
        download = CountingMapping(
            {
                name: valid_download[name]
                for name in DOWNLOAD_FIELDS[:index]
            }
        )
        authority = CountingMapping(valid_authority)
        value = runtime._evaluate_registered_admit_013(
            CandidateBomb(),
            batch_context=None,
            evaluation_context=authority,
            download_result_context=download,
            stage_authorization_context=None,
        )
        if (
            download.calls != list(DOWNLOAD_FIELDS[: index + 1])
            or authority.calls
            or value.reason != runtime.admit013.MISSING_REASONS[index]
        ):
            raise AssertionError("required Exact4 first-missing drift")
    for index in range(3):
        authority_values = dict(valid_authority)
        authority_values.pop(AUTHORITY_FIELDS[index])
        authority = CountingMapping(authority_values)
        runtime._evaluate_registered_admit_013(
            CandidateBomb(),
            batch_context=None,
            evaluation_context=authority,
            download_result_context=valid_download,
            stage_authorization_context=None,
        )
        if authority.calls != list(AUTHORITY_FIELDS):
            raise AssertionError("optional Exact3 continue drift")
    invalid = runtime._evaluate_registered_admit_013(
        object(),
        batch_context=None,
        evaluation_context={},
        download_result_context={},
        stage_authorization_context=None,
    )
    if _runtime_tuple(invalid, RESULT_FIELDS) != (
        runtime.RESULT_SCHEMA_VERSION,
        RULE_ID,
        RULE_NAME,
        "invalid",
        False,
        True,
        "ADMIT_013_CANDIDATE_RECORD_MAPPING_INVALID",
        (),
        (),
        (),
        (),
        False,
        ADAPTER_ID,
    ):
        raise AssertionError("candidate invalid Exact13 drift")
    context_cases = (
        (
            {"batch_context": object()},
            "ADMIT_013_BATCH_CONTEXT_MUST_BE_NONE",
        ),
        (
            {"evaluation_context": object()},
            "ADMIT_013_EVALUATION_CONTEXT_MAPPING_REQUIRED",
        ),
        (
            {"download_result_context": object()},
            "ADMIT_013_DOWNLOAD_RESULT_CONTEXT_MAPPING_REQUIRED",
        ),
        (
            {"stage_authorization_context": object()},
            "ADMIT_013_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
        ),
    )
    for overrides, reason in context_cases:
        kwargs = {
            "batch_context": None,
            "evaluation_context": {},
            "download_result_context": {},
            "stage_authorization_context": None,
            **overrides,
        }
        try:
            runtime._evaluate_registered_admit_013(
                CandidateBomb(),
                **kwargs,
            )
        except runtime.UnifiedAdmissionDispatchError as error:
            if _runtime_tuple(error, ERROR_FIELDS) != (
                "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
                RULE_ID,
                True,
                True,
                True,
                reason,
            ):
                raise AssertionError("context dispatch semantics drift")
        else:
            raise AssertionError("context routing failure missing")
    for rule_id, code in (
        (True, "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID"),
        (13, "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID"),
        ("ADMIT_999", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN"),
        ("ADMIT_014", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED"),
        ("ADMIT_015", "UNIFIED_ADMISSION_RULE_NOT_REGISTERED"),
    ):
        try:
            runtime.evaluate_admission_rule(rule_id, {})
        except runtime.UnifiedAdmissionDispatchError as error:
            if error.code != code:
                raise AssertionError("dispatcher precedence drift")
        else:
            raise AssertionError("dispatcher error missing")
    if (
        hasattr(runtime, "evaluate_all_rules")
        or hasattr(runtime, "combined_candidate_verdict")
    ):
        raise AssertionError("aggregation public API leaked")


def _git_at(root: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        raise AssertionError(f"git command failed: {arguments}")
    return completed.stdout


def _verify_lifecycle(
    root: Path = ROOT,
    exact10: Sequence[str] = EXACT10,
    *,
    base_commit: str = BASE,
) -> str:
    candidate_root = Path(os.path.abspath(root))
    expected_order = tuple(exact10)
    expected = set(expected_order)
    forbidden = (
        ".pt",
        ".ckpt",
        ".pth",
        ".pkl",
        ".lmdb",
        ".tar",
        ".zip",
        ".tgz",
        ".npz",
        ".tmp",
        ".part",
    )
    if len(expected_order) != 10 or len(expected) != 10:
        raise AssertionError("candidate Exact10 cardinality drift")
    if any(
        Path(path).is_absolute()
        or not Path(path).parts
        or ".." in Path(path).parts
        or path.endswith(forbidden)
        for path in expected_order
    ):
        raise AssertionError("candidate Exact10 path unsafe")
    for path in expected_order:
        target = candidate_root / path
        try:
            item = os.lstat(target)
        except FileNotFoundError as error:
            raise AssertionError("candidate Exact10 missing") from error
        if (
            not stat.S_ISREG(item.st_mode)
            or stat.S_ISLNK(item.st_mode)
            or item.st_size > MAX_CANDIDATE_BYTES
        ):
            raise AssertionError("candidate Exact10 leaf unsafe")
        ignored = subprocess.run(
            (
                "git",
                "check-ignore",
                "--no-index",
                "-q",
                "--",
                path,
            ),
            cwd=candidate_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if ignored.returncode == 0:
            raise AssertionError("candidate Exact10 ignored")
        if ignored.returncode != 1:
            raise AssertionError("candidate ignore inspection failed")

    stage_token = "unified_dispatch_runtime_with_admit_001_to_013"
    expected_top = set(expected_order[:4])
    observed_top: set[str] = set()
    for relative_directory in (
        Path("src/covalent_ext"),
        Path("scripts"),
        Path("tests"),
        Path("docs"),
    ):
        directory = candidate_root / relative_directory
        for child in directory.iterdir():
            if stage_token in child.name:
                observed_top.add(
                    (relative_directory / child.name).as_posix()
                )
    if observed_top != expected_top:
        raise AssertionError("same-stage top-level inventory drift")
    output_parents = {Path(path).parent for path in expected_order[4:]}
    if len(output_parents) != 1:
        raise AssertionError("candidate Exact6 parent drift")
    output_parent = candidate_root / next(iter(output_parents))
    expected_outputs = {
        Path(path).name for path in expected_order[4:]
    }
    observed_outputs = {child.name for child in output_parent.iterdir()}
    if observed_outputs != expected_outputs:
        raise AssertionError("candidate Exact6 inventory drift")

    ancestor = subprocess.run(
        ("git", "merge-base", "--is-ancestor", base_commit, "HEAD"),
        cwd=candidate_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if ancestor.returncode:
        raise AssertionError("candidate base is not an ancestor")
    tracked = {
        path
        for path in expected_order
        if subprocess.run(
            ("git", "ls-files", "--error-unmatch", "--", path),
            cwd=candidate_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        ).returncode
        == 0
    }
    untracked = set(
        _git_at(
            candidate_root,
            "ls-files",
            "--others",
            "--exclude-standard",
            "--",
            *expected_order,
        )
        .decode()
        .splitlines()
    )
    staged = set(
        _git_at(
            candidate_root,
            "diff",
            "--cached",
            "--name-only",
            "--",
            *expected_order,
        )
        .decode()
        .splitlines()
    )
    dirty = set(
        _git_at(
            candidate_root,
            "diff",
            "--name-only",
            "--",
            *expected_order,
        )
        .decode()
        .splitlines()
    )
    if staged or dirty:
        raise AssertionError("candidate lifecycle staged or dirty")
    if tracked == set() and untracked == expected:
        return "pre_commit"
    if tracked == expected and untracked == set():
        return "post_commit"
    raise AssertionError("candidate lifecycle mixed or incomplete")


def _silent_import(attested: Mapping[str, Any]) -> None:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        (
            sys.executable,
            "-B",
            "-c",
            f"import importlib; importlib.import_module({MODULE!r})",
        ),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
        check=False,
    )
    if completed.returncode or completed.stdout or completed.stderr:
        raise AssertionError("production isolated import not silent")
    _assert_candidate_unchanged(attested)


def main() -> int:
    _canonical_guard()
    source_records = _verify_base_and_sources()
    attested = _attest_candidate()
    before = _output_bytes()
    sys.path.insert(0, str(ROOT / "src"))
    runtime = importlib.import_module(MODULE)
    if Path(os.path.abspath(runtime.__file__)) != attested["path"]:
        raise AssertionError("imported candidate path drift")
    _assert_candidate_unchanged(attested)
    _verify_runtime(runtime)
    _silent_import(attested)
    if _output_bytes() != before:
        raise AssertionError("runtime import caused output side effect")
    hashes = _verify_output_tree(source_records)
    lifecycle = _verify_lifecycle()
    print(
        json.dumps(
            {
                "checked": True,
                "lifecycle": lifecycle,
                "output_sha256": hashes,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
