#!/usr/bin/env python3
"""Independent checker for the CovaPIE ADMIT_001--015 runtime."""

from __future__ import annotations

import ast
import csv
import hashlib
import importlib
import inspect
import io
import json
import os
import re
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
    "with_admit_001_to_015"
)
CANDIDATE = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_"
    "with_admit_001_to_015.py"
)
BASE = "d70d7d8919c3ec59e0b3d864ec8e496695ab770b"
BASE_PARENT = "b4a8770f27bdd263d0d3ad5c0a8b210e19954cbe"
BASE_TREE = "b8b3620ed5262f95694104249d607fff8d21ec01"
BASE_SUBJECT = "add CovaPIE ADMIT_015 unified adapter contract v1"
STAGE_NAME = (
    "covapie_bulk_download_admission_unified_dispatch_runtime_"
    "with_admit_001_to_015_v1"
)
STAGE = Path("data/derived/covalent_small") / STAGE_NAME
OUTPUTS = (
    "covapie_admit_001_to_015_runtime_contract.csv",
    "covapie_admit_001_to_015_dispatch_truth_matrix.csv",
    "covapie_admit_001_to_015_registry_and_identity_audit.csv",
    "covapie_admit_001_to_015_runtime_safety_audit.csv",
    "covapie_admit_001_to_015_runtime_issue_readiness_inventory.csv",
    "covapie_admit_001_to_015_runtime_manifest.json",
)
TOP_LEVEL = (
    CANDIDATE,
    Path(
        "scripts/check_covapie_bulk_download_admission_unified_dispatch_"
        "runtime_with_admit_001_to_015_v1.py"
    ),
    Path(
        "tests/test_covapie_bulk_download_admission_unified_dispatch_"
        "runtime_with_admit_001_to_015_v1.py"
    ),
    Path(
        "docs/covapie_bulk_download_admission_unified_dispatch_runtime_"
        "with_admit_001_to_015_v1_summary.md"
    ),
)
EXACT10 = (*TOP_LEVEL, *(STAGE / name for name in OUTPUTS))
STAGE_FAMILY_TOKENS = (
    (
        "covapie_bulk_download_admission_unified_dispatch_runtime_"
        "with_admit_001_to_015"
    ),
    "covapie_admit_001_to_015_runtime_contract",
    "covapie_admit_001_to_015_dispatch_truth_matrix",
    "covapie_admit_001_to_015_registry_and_identity_audit",
    "covapie_admit_001_to_015_runtime_safety_audit",
    "covapie_admit_001_to_015_runtime_issue_readiness_inventory",
    "covapie_admit_001_to_015_runtime_manifest",
)
PUBLIC_MARKER = (
    "# === CovaPIE ADMIT_001 TO ADMIT_015 PUBLIC "
    "RUNTIME CLOSURE END ==="
)
PUBLIC_DEFINITIONS = (
    "_raise_dispatch_error",
    "_admit015_context_failure",
    "_admit015_adapter_failure",
    "_admit015_candidate_invalid",
    "_prevalidate_admit015_source",
    "_expected_admit015_from_oracle",
    "_validate_admit015_oracle_equivalence",
    "_project_stage_authorization_record_to_exact_string_pairs",
    "_project_admit015_exact13",
    "_evaluate_registered_admit_015",
    "evaluate_admission_rule",
)
EXPECTED_PRODUCTION_SHA256 = (
    "1fc5ac24e54d134d3f1f7054dfd2f264a2d76f17f0602bac216bb2e4e7e00bd1"
)
EXPECTED_MARKER_PREFIX_SHA256 = (
    "51aa82136e4f551226780c0a2f63b327bfce82c60e310fba4d580b73d40d883b"
)
EXPECTED_DEFINITION_AST_SHA256: dict[str, str] = {
    "_raise_dispatch_error": "adb1d13a5bea21730e5d56742c1ba46faa30b5c31d80f827a892de73cc6e1356",
    "_admit015_context_failure": "3620c783e35a9c1a2f0846f7441ef2ce12b95f53912c3ff3123fbb4dcd4be86c",
    "_admit015_adapter_failure": "a2267db3fe18f4fcccb2657f2122c90b5ba15f299d24eac87f321a695c412438",
    "_admit015_candidate_invalid": "52048bea5aaca83837f2360fd99567a23ba6fb017314fa86e1045bff57e4800c",
    "_prevalidate_admit015_source": "cf58c751070724a1b0409d1457bf71f8881eccbf70f55563e51e68d5bf786c12",
    "_expected_admit015_from_oracle": "65ce09b6e1a7254b5a9542c5a594e86da13f2b1abc17f800c287112988d7ebde",
    "_validate_admit015_oracle_equivalence": "c961583e2fc44b4db2e59c2db103e15d195b8db3e31dfefa630140158d1faa2a",
    "_project_stage_authorization_record_to_exact_string_pairs": "1370e5f8b9dfb376302590257234c9451a9ad3d854991d1d26678680c5a41998",
    "_project_admit015_exact13": "1ddcf8065506519e36f0c20edd235fbd3f719d60cda5ea1ad220749594d6fb9e",
    "_evaluate_registered_admit_015": "4e067e69ddbc5baee612a2bc95d302b2dc0c70235f0153b65f33da75efad8363",
    "evaluate_admission_rule": "436c53241254cf1229d4083a6caa3d555e10e17583c8ae4006275727b05fd5e9",
}
EXPECTED_OUTPUT_SHA256: dict[str, str] = {
    "covapie_admit_001_to_015_runtime_contract.csv": "b6606d4111b7493e4b8cd531fb88c5281b5a685369788b85742b5e85d721a465",
    "covapie_admit_001_to_015_dispatch_truth_matrix.csv": "f93a43cfa560d495ea7e14fca26a957c6eb087907cbfde91d7456d1a55440abb",
    "covapie_admit_001_to_015_registry_and_identity_audit.csv": "eac4ea16fbd2193c3b53f8d6bdf11728f086a499390bba7c33e1e3d2e61cc75e",
    "covapie_admit_001_to_015_runtime_safety_audit.csv": "50db14b8d823c162e694a74abaa5a9189006f54d6cb6716d6ad9406f509a05b2",
    "covapie_admit_001_to_015_runtime_issue_readiness_inventory.csv": "c8ea16e335e43ed781bb5177e1aba0247a55714f55eeb5caf8bed23a539f431d",
    "covapie_admit_001_to_015_runtime_manifest.json": "0fbd5999977d025a44b4bef854d9edfda5ea0e5ed79a7d5ff7b17cef7b6186d3",
}
EXPECTED_MANIFEST_KEYS = (
    "Admit015EvaluationResult_implemented",
    "adapter_design_simulator_called_by_public_runtime",
    "adapter_ids",
    "adapter_ready_rule_ids",
    "admit_015_candidate_invalid_call_counts",
    "admit_015_candidate_mapping_invalid_reason",
    "admit_015_context_routing_contract_frozen",
    "admit_015_exact13_projection",
    "admit_015_exact13_projection_frozen",
    "admit_015_formal_evaluator_interface_contract_frozen",
    "admit_015_handler",
    "admit_015_handler_signature",
    "admit_015_implemented",
    "admit_015_inherited_exact42_runtime_case_count",
    "admit_015_oracle",
    "admit_015_oracle_negative_case_count",
    "admit_015_oracle_result_type",
    "admit_015_preconditions_audited",
    "admit_015_registered_in_engine",
    "admit_015_routing_precedence",
    "admit_015_rule_logic_implemented",
    "admit_015_source_fields",
    "admit_015_source_invariant_invalid_reason",
    "admit_015_source_negative_case_count",
    "admit_015_source_oracle_equivalence_contract_frozen",
    "admit_015_source_oracle_full_exact9_equality_required",
    "admit_015_source_prevalidation_before_oracle",
    "admit_015_source_type",
    "admit_015_source_type_invalid_reason",
    "admit_015_standalone_evaluator_implemented",
    "admit_015_training_authorization_contract_frozen",
    "admit_015_unified_adapter_contract_frozen",
    "admit_015_unified_adapter_implemented",
    "all_checks_passed",
    "all_issue_checks_passed",
    "all_predecessor_contract_checks_passed",
    "all_registry_audit_checks_passed",
    "all_runtime_contract_checks_passed",
    "all_safety_checks_passed",
    "all_source_boundary_checks_passed",
    "all_truth_matrix_checks_passed",
    "ast_attestation_cross_python_version_portable",
    "authorized_admit_015_training_execution_count",
    "callable_discovered_rule_ids",
    "candidate_production_source_attestation",
    "canonical_evidence_python_implementation",
    "canonical_evidence_python_version",
    "canonical_mask_count",
    "canonical_masks",
    "combined_candidate_verdict_implemented",
    "combined_permission_semantics_frozen",
    "contract_row_count",
    "cross_rule_aggregation_implemented",
    "current_permission",
    "dispatch_error_codes",
    "dispatch_error_fields",
    "evaluate_admit_015_implemented",
    "evidence_lifecycle_hardening",
    "exact14_predecessor_identity",
    "exact15_identity",
    "expected_base_commit",
    "expected_base_parent",
    "expected_base_subject",
    "expected_base_tree",
    "feature_semantics_audit_completed",
    "feature_semantics_audit_required_before_training",
    "feature_semantics_note",
    "first_fourteen_handler_identity_reused",
    "future_adapter_handler_implemented",
    "historical_feature_semantics_known",
    "historical_unknown_atom_feature_policy_resolved",
    "issue_coverage_after",
    "issue_coverage_before",
    "issue_coverage_effective_status",
    "issue_inventory_row_count",
    "issue_transition_count",
    "issue_transition_id",
    "known_not_registered_rule_ids",
    "known_rule_ids",
    "legacy_adapter_not_ready_rule_ids",
    "lifecycle_policy",
    "mandatory_training_authorization_enforcement_api_frozen",
    "mandatory_training_authorization_enforcement_implemented",
    "manifest_schema_version",
    "noncanonical_python_policy",
    "outcome_vocabulary",
    "output_csv_schemas",
    "output_file_count",
    "output_files",
    "output_materialization",
    "output_read_policy",
    "output_sha256",
    "output_sha256_excludes_manifest_self_hash",
    "precondition_transition",
    "predecessor_committed_registry_audit_count",
    "predecessor_committed_truth_case_count",
    "predecessor_dispatcher_unchanged",
    "predecessor_representative_dispatch_count",
    "project",
    "provider_mapping_validated",
    "public_definition_count",
    "public_definitions",
    "public_dispatch_cardinality",
    "public_dispatch_case_count",
    "public_dispatch_precedence",
    "public_dispatch_signature",
    "public_dispatch_signature_matches_exact14",
    "public_dispatch_uses_local_registry",
    "public_marker",
    "public_type_and_constant_identity",
    "python_runtime_migration_policy",
    "readiness",
    "ready_for_admit_015_mandatory_training_authorization_enforcement_contract_design",
    "ready_for_bulk_download_now",
    "ready_for_training",
    "real_provider_evaluation_ready",
    "real_training_ready",
    "recommended_next_step",
    "registered_rule_count",
    "registered_rule_ids",
    "registry_identity_audit_row_count",
    "registry_mapping_proxy_type",
    "remaining_open_issue_ids",
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
    "source_read_policy",
    "source_validation_before_candidate_or_output_read",
    "stage",
    "step",
    "step12d_is_final_training_feature_contract",
    "step12d_status",
    "successor_dispatcher_distinct",
    "synthetic_true_case_changes_current_permission",
    "truth_input_representation_columns",
    "truth_input_representation_semantics_independently_verified",
    "truth_matrix_group_counts",
    "truth_matrix_row_count",
    "truth_trace_columns",
    "truth_trace_semantics_independently_verified",
    "unified_admission_rule_coverage_complete",
    "unified_dispatch_runtime_with_admit_001_to_014_implemented",
    "unified_dispatch_runtime_with_admit_001_to_015_implemented",
    "validation_failures",
)

SOURCE_BOUNDARY = (
    (
        "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014.py",
        "c5f5cfc57155f34ee2435228b3bf53ae8d1f6d81c32e097c43668c0b272fd1a2",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014_v1/covapie_admit_001_to_014_runtime_contract.csv",
        "6646678c8c11c37ee8d4cc28429f92b1afe0b98f31d2832a4a8a142015b0e5b2",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014_v1/covapie_admit_001_to_014_dispatch_truth_matrix.csv",
        "f55acf1271af0fb333885c5ef013a62424dfa47fa0d9f88eb3b5dfd8f48de82c",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014_v1/covapie_admit_001_to_014_registry_and_identity_audit.csv",
        "92f578cf6d038c43c55b6768edce413191297f2c207e1f473769835b09b7f7ed",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014_v1/covapie_admit_001_to_014_runtime_safety_audit.csv",
        "854231a11e4fa808f4103055200a2b54c0e62e44b784ded34ad54c83bed6158f",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014_v1/covapie_admit_001_to_014_runtime_issue_readiness_inventory.csv",
        "f457da61bffade18999af5c069d237c30aa30a0c63efb8bb14130935fb0757ec",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014_v1/covapie_admit_001_to_014_runtime_manifest.json",
        "bf7bbe3c2158f661c6e71835bf603af76ffbb315d4ef377c9f72da246619ba40",
    ),
    (
        "src/covalent_ext/covapie_bulk_download_admission_admit_015_unified_adapter_contract_design_gate.py",
        "a11ce87b326612e251258072995ee26fb848212a7b7dde869a10de6e473ea60c",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_015_unified_adapter_contract_v1/covapie_admit_015_unified_adapter_contract.csv",
        "16159caf1b55116fc2802e43f330d1c706041da4261e1a22039d7c8c4375ba34",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_015_unified_adapter_contract_v1/covapie_admit_015_stage_authorization_projection_and_context_routing_matrix.csv",
        "9edfaecd8492423b61d9e93413a616a4b917219d8207808da7db0142a9aed06b",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_015_unified_adapter_contract_v1/covapie_admit_015_unified_result_projection_truth_matrix.csv",
        "c40c8133f946cf39149224479590b65351c9b9229e9cc33a821616ed521ca2d3",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_015_unified_adapter_contract_v1/covapie_admit_015_unified_adapter_safety_audit.csv",
        "586ced0297eff2b396d61d771073027bc2db982e6092d2e00a1b7dcc7ac08d2d",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_015_unified_adapter_contract_v1/covapie_admit_015_unified_adapter_issue_readiness_inventory.csv",
        "f457da61bffade18999af5c069d237c30aa30a0c63efb8bb14130935fb0757ec",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_015_unified_adapter_contract_v1/covapie_admit_015_unified_adapter_contract_manifest.json",
        "43ffb247cda8cc641c0a9ba2892f66b0b54b2ed572c6f6d26a2e62cd37778449",
    ),
    (
        "src/covalent_ext/covapie_bulk_download_admission_admit_015_standalone_evaluator_interface.py",
        "eacb5c1ac583649a34cdb9dcde4c004a861da43609b9ffb964a715a427883a82",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_015_standalone_evaluator_interface_v1/covapie_admit_015_standalone_evaluator_interface_manifest.json",
        "238aadcf819ffc2c30c5de063b1873ce16df59f82cb4be4b4d6222fbdc143758",
    ),
    (
        "src/covalent_ext/covapie_bulk_download_admission_admit_015_formal_evaluator_interface_contract_design_gate.py",
        "48e2135517cad1ad7744345c3cb5f45e5b29d9c91fd41850eb80a96785e0daa3",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_015_formal_evaluator_interface_contract_v1/covapie_admit_015_formal_evaluator_interface_contract_manifest.json",
        "08ce241290c66e87881c983a563be9f406d904c39e99bd9c6830c78fc3b4b021",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_015_training_authorization_contract_v1/covapie_admit_015_training_authorization_truth_matrix.csv",
        "bc1070cb7df2db7ee05c4c8aa21ea9563a08974b620d44ee42c193c63b4fb37b",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_015_training_authorization_contract_v1/covapie_admit_015_training_authorization_contract_manifest.json",
        "16ea4bb5f781c6f6d8277fb4142258c2bee4849b942582e48692373caee5cda1",
    ),
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
SOURCE_FIELDS = (
    "admission_rule_id",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "canonical_stage_authorization_record",
    "validated_stage_authorization_fields",
    "consumed_stage_authorization_fields",
    "evaluator_io_used",
)
TARGET_ITEM = "current_stage_training_authorized"
DOWNLOAD_ITEM = "current_stage_download_authorized"
SOURCE_TYPE_ERROR = "ADMIT_015_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
SOURCE_INVARIANT_ERROR = (
    "ADMIT_015_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
)
CONTRACT_HEADER = (
    "contract_order",
    "contract_group",
    "contract_item",
    "expected_value",
    "observed_value",
    "contract_passed",
)
TRUTH_HEADER = (
    "case_order",
    "case_id",
    "case_group",
    "admission_rule_id",
    "candidate_representation",
    "batch_context_representation",
    "evaluation_context_representation",
    "download_result_context_representation",
    "stage_authorization_context_representation",
    "expected_outcome_or_error",
    "observed_outcome_or_error",
    "expected_result_json",
    "observed_result_json",
    "expected_call_order",
    "observed_call_order",
    "expected_stage_context_identity_preserved",
    "observed_stage_context_identity_preserved",
    "formal_call_count",
    "oracle_call_count",
    "candidate_key_access_count",
    "adapter_stage_target_access_count",
    "formal_stage_target_access_count",
    "oracle_stage_target_access_count",
    "stage_target_access_count",
    "case_passed",
)
TRUTH_INPUT_REPRESENTATION_COLUMNS = (
    "candidate_representation",
    "batch_context_representation",
    "evaluation_context_representation",
    "download_result_context_representation",
    "stage_authorization_context_representation",
)
REGISTRY_HEADER = (
    "audit_order",
    "rule_id",
    "expected_handler_identity",
    "observed_handler_identity",
    "identity_preserved",
    "registered",
    "callable_discovered",
    "adapter_ready",
    "audit_passed",
)
SAFETY_HEADER = (
    "audit_order",
    "audit_item",
    "expected_state",
    "observed_state",
    "safety_passed",
)
ISSUE_HEADER = (
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
TRUE_READINESS = (
    "admit_015_preconditions_audited",
    "admit_015_training_authorization_contract_frozen",
    "admit_015_formal_evaluator_interface_contract_frozen",
    "evaluate_admit_015_implemented",
    "Admit015EvaluationResult_implemented",
    "admit_015_rule_logic_implemented",
    "admit_015_standalone_evaluator_implemented",
    "admit_015_context_routing_contract_frozen",
    "admit_015_exact13_projection_frozen",
    "admit_015_source_oracle_equivalence_contract_frozen",
    "admit_015_unified_adapter_contract_frozen",
    "future_adapter_handler_implemented",
    "admit_015_unified_adapter_implemented",
    "admit_015_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_014_implemented",
    "unified_dispatch_runtime_with_admit_001_to_015_implemented",
    "unified_admission_rule_coverage_complete",
    "feature_semantics_audit_required_before_training",
    "ready_for_admit_015_mandatory_training_authorization_enforcement_contract_design",
)
FALSE_READINESS = (
    "mandatory_training_authorization_enforcement_api_frozen",
    "mandatory_training_authorization_enforcement_implemented",
    "combined_candidate_verdict_implemented",
    "combined_permission_semantics_frozen",
    "cross_rule_aggregation_implemented",
    "provider_mapping_validated",
    "real_provider_evaluation_ready",
    "ready_for_bulk_download_now",
    "feature_semantics_audit_completed",
    "historical_unknown_atom_feature_policy_resolved",
    "historical_feature_semantics_known",
    "real_training_ready",
    "ready_for_training",
    "step12d_is_final_training_feature_contract",
)
MAX_BYTES = 100 * 1024 * 1024
DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
FORBIDDEN_SUFFIXES = (
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


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def canonical_guard() -> None:
    if (
        sys.implementation.name != "cpython"
        or tuple(sys.version_info[:3]) != (3, 10, 4)
    ):
        raise AssertionError("canonical CPython 3.10.4 required")


def _git(root: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ("git", *arguments),
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


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


def pinned_read(root: Path, relative: Path) -> bytes:
    root = Path(os.path.abspath(root))
    if (
        relative.is_absolute()
        or not relative.parts
        or ".." in relative.parts
    ):
        raise AssertionError("unsafe pinned-read path")
    root_item = os.lstat(root)
    root_identity = _full_identity(root_item)
    if (
        not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
        or root.resolve(strict=True) != root
    ):
        raise AssertionError("unsafe pinned-read root")
    descriptors = [os.open(root, DIR_FLAGS)]
    bindings: list[
        tuple[int, str, int, tuple[int, int, int, int, int, int]]
    ] = []
    try:
        def verify_parent_root_bindings() -> None:
            for lexical_parent, name, child_fd, identity in reversed(
                bindings
            ):
                lexical = os.stat(
                    name,
                    dir_fd=lexical_parent,
                    follow_symlinks=False,
                )
                if (
                    _full_identity(lexical) != identity
                    or _full_identity(os.fstat(child_fd)) != identity
                    or not stat.S_ISDIR(lexical.st_mode)
                    or stat.S_ISLNK(lexical.st_mode)
                ):
                    raise AssertionError("pinned parent changed")
            lexical_root = os.lstat(root)
            if (
                _full_identity(lexical_root) != root_identity
                or _full_identity(os.fstat(descriptors[0]))
                != root_identity
                or not stat.S_ISDIR(lexical_root.st_mode)
                or stat.S_ISLNK(lexical_root.st_mode)
                or root.resolve(strict=True) != root
            ):
                raise AssertionError("pinned root changed")

        if _full_identity(os.fstat(descriptors[0])) != root_identity:
            raise AssertionError("pinned root race")
        parent_fd = descriptors[0]
        for part in relative.parts[:-1]:
            lexical = os.stat(
                part, dir_fd=parent_fd, follow_symlinks=False
            )
            identity = _full_identity(lexical)
            if (
                not stat.S_ISDIR(lexical.st_mode)
                or stat.S_ISLNK(lexical.st_mode)
            ):
                raise AssertionError("unsafe pinned parent")
            child_fd = os.open(part, DIR_FLAGS, dir_fd=parent_fd)
            if _full_identity(os.fstat(child_fd)) != identity:
                os.close(child_fd)
                raise AssertionError("pinned parent race")
            descriptors.append(child_fd)
            bindings.append((parent_fd, part, child_fd, identity))
            parent_fd = child_fd
        before = os.stat(
            relative.name, dir_fd=parent_fd, follow_symlinks=False
        )
        leaf_identity = _full_identity(before)
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_ISLNK(before.st_mode)
            or before.st_size > MAX_BYTES
        ):
            raise AssertionError("unsafe pinned leaf")
        leaf_fd = os.open(relative.name, READ_FLAGS, dir_fd=parent_fd)
        descriptors.append(leaf_fd)
        if _full_identity(os.fstat(leaf_fd)) != leaf_identity:
            raise AssertionError("pinned leaf stat/open race")
        chunks = []
        while True:
            chunk = os.read(leaf_fd, 1 << 16)
            if not chunk:
                break
            chunks.append(chunk)
        if (
            _full_identity(os.fstat(leaf_fd)) != leaf_identity
            or _full_identity(
                os.stat(
                    relative.name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
            )
            != leaf_identity
        ):
            raise AssertionError("pinned leaf changed")
        verify_parent_root_bindings()
        if (
            _full_identity(os.fstat(leaf_fd)) != leaf_identity
            or _full_identity(
                os.stat(
                    relative.name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
            )
            != leaf_identity
        ):
            raise AssertionError("pinned leaf final traversal changed")
        verify_parent_root_bindings()
        return b"".join(chunks)
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _parse_index(content: bytes, relative: str) -> tuple[str, str, int]:
    try:
        metadata, path = content.decode().rstrip("\n").split("\t", 1)
        mode, blob, stage = metadata.split(" ")
    except ValueError as error:
        raise AssertionError("index entry malformed") from error
    if (
        path != relative
        or mode not in {"100644", "100755"}
        or re.fullmatch(r"[0-9a-f]{40}", blob) is None
    ):
        raise AssertionError("index entry drift")
    return mode, blob, int(stage)


def _parse_tree(content: bytes, relative: str) -> tuple[str, str]:
    try:
        metadata, path = content.decode().rstrip("\n").split("\t", 1)
        mode, kind, blob = metadata.split(" ")
    except ValueError as error:
        raise AssertionError("tree entry malformed") from error
    if (
        path != relative
        or kind != "blob"
        or mode not in {"100644", "100755"}
        or re.fullmatch(r"[0-9a-f]{40}", blob) is None
    ):
        raise AssertionError("tree entry drift")
    return mode, blob


def verify_sources(root: Path = ROOT) -> tuple[dict[str, Any], ...]:
    identity = _git(
        root, "show", "-s", "--format=%H%n%P%n%T%n%s", BASE
    )
    if identity.returncode:
        raise AssertionError("base identity command failed")
    lines = identity.stdout.decode().splitlines()
    if lines != [BASE, BASE_PARENT, BASE_TREE, BASE_SUBJECT]:
        raise AssertionError("base identity drift")
    if _git(
        root, "merge-base", "--is-ancestor", BASE, "HEAD"
    ).returncode:
        raise AssertionError("base is not an ancestor of candidate HEAD")
    records = []
    for order, (relative, expected_sha) in enumerate(
        SOURCE_BOUNDARY, 1
    ):
        path = Path(relative)
        if (
            path.is_absolute()
            or ".." in path.parts
            or relative.startswith(("data/raw/", "checkpoints/"))
        ):
            raise AssertionError("source boundary unsafe")
        index_result = _git(root, "ls-files", "--stage", "--", relative)
        tree_result = _git(root, "ls-tree", BASE, "--", relative)
        if index_result.returncode or tree_result.returncode:
            raise AssertionError("source git query failed")
        index_mode, index_blob, index_stage = _parse_index(
            index_result.stdout, relative
        )
        tree_mode, tree_blob = _parse_tree(tree_result.stdout, relative)
        base_bytes = _git(root, "cat-file", "blob", f"{BASE}:{relative}")
        index_bytes = _git(root, "cat-file", "blob", f":{relative}")
        if base_bytes.returncode or index_bytes.returncode:
            raise AssertionError("source blob read failed")
        filesystem = pinned_read(root, path)
        if (
            index_stage != 0
            or index_mode != tree_mode
            or index_blob != tree_blob
            or base_bytes.stdout != index_bytes.stdout
            or base_bytes.stdout != filesystem
            or _sha(filesystem) != expected_sha
        ):
            raise AssertionError(f"source drift: {relative}")
        records.append(
            {
                "source_order": order,
                "source_relative_path": relative,
                "base_tree_mode": tree_mode,
                "base_tree_blob": tree_blob,
                "index_mode": index_mode,
                "index_blob": index_blob,
                "index_stage": 0,
                "expected_sha256": expected_sha,
                "base_tree_sha256": expected_sha,
                "filesystem_sha256": expected_sha,
            }
        )
    if len(records) != 20:
        raise AssertionError("source boundary is not Exact20")
    return tuple(records)


def attest_candidate(root: Path = ROOT) -> dict[str, Any]:
    source = pinned_read(root, CANDIDATE)
    text = source.decode()
    if text.count(PUBLIC_MARKER) != 1:
        raise AssertionError("public marker drift")
    prefix = text.split(PUBLIC_MARKER, 1)[0].encode()
    prefix_tree = ast.parse(prefix)
    definitions = tuple(
        node
        for node in prefix_tree.body
        if isinstance(node, ast.FunctionDef)
    )
    names = tuple(node.name for node in definitions)
    hashes = {
        node.name: _sha(
            ast.dump(
                node,
                annotate_fields=True,
                include_attributes=False,
            ).encode()
        )
        for node in definitions
    }
    project_imports = tuple(
        (alias.name, alias.asname)
        for node in prefix_tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module == "covalent_ext"
        for alias in node.names
    )
    expected_imports = (
        (
            "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014",
            "predecessor",
        ),
        (
            "covapie_bulk_download_admission_admit_015_standalone_evaluator_interface",
            "admit015",
        ),
        (
            "covapie_bulk_download_admission_admit_015_formal_evaluator_interface_contract_design_gate",
            "admit015_oracle",
        ),
    )
    forbidden = (
        "covapie_bulk_download_admission_admit_015_unified_adapter_contract_design_gate",
        "simulate_admit_015_unified_adapter_contract_design",
        "importlib",
        "pathlib",
        "provider",
        "downloader",
        "data/raw",
        "checkpoints",
        "evaluate_all_rules",
        "combined_candidate_verdict",
    )
    call_names = {
        node.func.id
        for node in ast.walk(prefix_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
    }
    if (
        _sha(source) != EXPECTED_PRODUCTION_SHA256
        or _sha(prefix) != EXPECTED_MARKER_PREFIX_SHA256
        or names != PUBLIC_DEFINITIONS
        or hashes != EXPECTED_DEFINITION_AST_SHA256
        or project_imports != expected_imports
        or any(token in prefix.decode() for token in forbidden)
        or call_names.intersection({"eval", "exec", "__import__"})
        or b"os.replace" in source
    ):
        raise AssertionError("candidate source/AST closure drift")
    return {
        "source": source,
        "full_sha256": _sha(source),
        "prefix_sha256": _sha(prefix),
        "definition_ast_sha256": hashes,
    }


def _csv_rows(
    content: bytes,
    header: tuple[str, ...],
) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(content.decode(), newline=""))
    if tuple(reader.fieldnames or ()) != header:
        raise AssertionError("CSV exact header drift")
    rows = list(reader)
    if any(
        tuple(row) != header or any(value is None for value in row.values())
        for row in rows
    ):
        raise AssertionError("CSV row shape drift")
    return rows


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AssertionError("manifest duplicate key")
        result[key] = value
    return result


def _exact_nested_mapping(
    value: object,
    name: str,
    keys: Sequence[str],
) -> dict[str, Any]:
    if type(value) is not dict or tuple(value) != tuple(keys):
        raise AssertionError(f"manifest nested schema drift: {name}")
    return value


def _assert_manifest_nested_schema(value: Mapping[str, Any]) -> None:
    if (
        type(value["truth_input_representation_columns"]) is not list
        or value["truth_input_representation_columns"]
        != list(TRUTH_INPUT_REPRESENTATION_COLUMNS)
        or any(
            type(item) is not str
            for item in value["truth_input_representation_columns"]
        )
        or value[
            "truth_input_representation_semantics_independently_verified"
        ]
        is not True
    ):
        raise AssertionError(
            "manifest truth input representation schema drift"
        )
    registered = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
    candidate = _exact_nested_mapping(
        value["candidate_production_source_attestation"],
        "candidate_production_source_attestation",
        (
            "adapter_design_simulator_called",
            "candidate_relative_path",
            "definition_count",
            "definition_names",
            "marker_prefix_sha256",
            "normalized_ast_sha256",
            "production_full_sha256",
            "public_closure_pure_memory",
        ),
    )
    normalized = _exact_nested_mapping(
        candidate["normalized_ast_sha256"],
        "normalized_ast_sha256",
        tuple(sorted(PUBLIC_DEFINITIONS)),
    )
    schemas = {
        "public_type_and_constant_identity": (
            "DISPATCH_ERROR_CODES",
            "DISPATCH_ERROR_FIELDS",
            "OUTCOME_VOCABULARY",
            "RESULT_FIELDS",
            "RESULT_SCHEMA_VERSION",
            "UnifiedAdmissionDispatchError",
            "UnifiedAdmissionRuleEvaluation",
        ),
        "first_fourteen_handler_identity_reused": registered[:14],
        "admit_015_candidate_invalid_call_counts": (
            "candidate_key_access",
            "formal",
            "oracle",
            "stage_target_access",
        ),
        "admit_015_exact13_projection": (
            "consumed_candidate_fields",
            "consumed_context_items",
            "normalized_values",
            "validated_candidate_fields",
        ),
        "truth_matrix_group_counts": (
            "admit015_inherited_exact42_runtime",
            "admit015_oracle_negative",
            "admit015_source_negative",
            "predecessor_representative_dispatch",
            "public_dispatch",
        ),
        "precondition_transition": (
            "complete_count",
            "implementation_blocking_count",
            "incomplete_count",
            "remaining_open_precondition_ids",
            "resolution",
            "resolved_precondition_ids",
            "row_count",
            "supported_but_not_frozen_count",
        ),
        "readiness": tuple(
            sorted((*TRUE_READINESS, *FALSE_READINESS))
        ),
        "output_materialization": (
            "GPFS_EINVAL_fail_closed",
            "all_leaf_descriptors_retained_through_final_traversal",
            "all_payloads_built_before_mutation",
            "authenticated_retained_path_only",
            "complete_set_postverify",
            "destination_name_inode_binding",
            "exact_six_allowlist",
            "exclusive_create",
            "existing_exact_set_inode_preserving_noop",
            "failure_staging_never_deleted",
            "failure_staging_retained",
            "file_fsync",
            "mismatch_repair_forbidden",
            "parent_and_staging_binding_rechecked_inside_rename",
            "parent_fsync",
            "pinned_parent_root_staging_leaf",
            "renameat2_RENAME_NOREPLACE",
            "staging_directory_fsync",
            "staging_lexical_binding_verified",
        ),
        "output_read_policy": (
            "all_leaf_fds_retained",
            "final_inventory",
            "final_leaf_checks",
            "final_root_parent_checks_after_final_leaf",
            "initial_inventory",
            "parent_strict_resolve",
            "second_inventory",
        ),
        "evidence_lifecycle_hardening": (
            "artifact_semantics_rebuilt_after_sha_verification",
            "bounded_recursive_no_follow_lifecycle",
            "checker_exact42_specs_owned_without_project_checker_import",
            "exact10_lifecycle_exact_inventory",
            "manifest_duplicate_and_exact_schema_rejection",
            "publisher_destination_binding_rechecks",
            "source_and_output_final_leaf_identity_post_traversal",
            "source_and_output_full_identity_post_traversal",
            "successor_regression_historical_deselection_count",
        ),
        "lifecycle_policy": (
            "bounded_recursive_no_follow",
            "exact10_recursive_allowlist",
            "nested_ignored_rejected",
            "nested_nonignored_rejected",
            "nested_tracked_rejected",
            "sibling_derived_root_rejected",
            "symlink_directory_rejected",
        ),
        "source_read_policy": (
            "final_leaf_check_followed_by_final_parent_root_check",
            "leaf_fds_retained_through_final_parent_root_check",
            "no_atomic_path_snapshot_claim",
            "six_field_identity",
        ),
        "source_input_sha256": tuple(
            sorted(path for path, _ in SOURCE_BOUNDARY)
        ),
        "output_sha256": tuple(sorted(OUTPUTS[:5])),
        "rule_names": registered,
        "adapter_ids": registered,
    }
    nested = {
        name: _exact_nested_mapping(value[name], name, keys)
        for name, keys in schemas.items()
    }
    verification = value["source_input_verification"]
    source_row_keys = (
        "base_tree_blob",
        "base_tree_mode",
        "base_tree_sha256",
        "expected_sha256",
        "filesystem_regular",
        "filesystem_sha256",
        "final_leaf_identity_verified",
        "index_blob",
        "index_mode",
        "index_stage",
        "non_symlink",
        "parent_chain_non_symlink",
        "pinned_fd_read",
        "post_read_identity_verified",
        "safe_descendant",
        "source_order",
        "source_relative_path",
        "source_verified",
        "tracked",
    )
    if type(verification) is not list or len(verification) != 20:
        raise AssertionError("manifest source verification is not Exact20")
    for row in verification:
        checked = _exact_nested_mapping(
            row,
            "source_input_verification[]",
            source_row_keys,
        )
        if (
            type(checked["source_order"]) is not int
            or type(checked["index_stage"]) is not int
            or any(
                type(checked[name]) is not bool
                for name in (
                    "filesystem_regular",
                    "final_leaf_identity_verified",
                    "non_symlink",
                    "parent_chain_non_symlink",
                    "pinned_fd_read",
                    "post_read_identity_verified",
                    "safe_descendant",
                    "source_verified",
                    "tracked",
                )
            )
            or any(
                type(checked[name]) is not str
                for name in set(source_row_keys)
                - {
                    "source_order",
                    "index_stage",
                    "filesystem_regular",
                    "final_leaf_identity_verified",
                    "non_symlink",
                    "parent_chain_non_symlink",
                    "pinned_fd_read",
                    "post_read_identity_verified",
                    "safe_descendant",
                    "source_verified",
                    "tracked",
                }
            )
        ):
            raise AssertionError("manifest source row exact type drift")
    if (
        type(candidate["adapter_design_simulator_called"]) is not bool
        or type(candidate["candidate_relative_path"]) is not str
        or type(candidate["definition_count"]) is not int
        or type(candidate["definition_names"]) is not list
        or len(candidate["definition_names"]) != 11
        or any(type(item) is not str for item in candidate["definition_names"])
        or type(candidate["marker_prefix_sha256"]) is not str
        or type(candidate["production_full_sha256"]) is not str
        or type(candidate["public_closure_pure_memory"]) is not bool
        or any(type(item) is not str for item in normalized.values())
        or any(
            type(item) is not bool
            for item in nested[
                "public_type_and_constant_identity"
            ].values()
        )
        or any(
            type(item) is not bool
            for item in nested[
                "first_fourteen_handler_identity_reused"
            ].values()
        )
        or any(
            type(item) is not int
            for item in nested[
                "admit_015_candidate_invalid_call_counts"
            ].values()
        )
        or any(
            type(item) is not int
            for item in nested["truth_matrix_group_counts"].values()
        )
        or type(
            nested["admit_015_exact13_projection"][
                "consumed_candidate_fields"
            ]
        )
        is not list
        or type(
            nested["admit_015_exact13_projection"][
                "validated_candidate_fields"
            ]
        )
        is not list
        or any(
            type(
                nested["admit_015_exact13_projection"][name]
            )
            is not str
            for name in ("consumed_context_items", "normalized_values")
        )
        or any(
            type(nested["precondition_transition"][name]) is not int
            for name in (
                "complete_count",
                "implementation_blocking_count",
                "incomplete_count",
                "row_count",
                "supported_but_not_frozen_count",
            )
        )
        or any(
            type(nested["precondition_transition"][name]) is not list
            or any(
                type(item) is not str
                for item in nested["precondition_transition"][name]
            )
            for name in (
                "remaining_open_precondition_ids",
                "resolved_precondition_ids",
            )
        )
        or type(nested["precondition_transition"]["resolution"]) is not str
        or any(
            type(item) is not bool
            for item in nested["readiness"].values()
        )
        or any(
            type(item) is not bool
            for item in nested["output_materialization"].values()
        )
        or any(
            type(item) is not bool
            for item in nested["output_read_policy"].values()
        )
        or any(
            type(item) is not bool
            for item in nested["lifecycle_policy"].values()
        )
        or any(
            type(item) is not bool
            for item in nested["source_read_policy"].values()
        )
        or any(
            type(item) is not str
            for item in nested["source_input_sha256"].values()
        )
        or any(
            type(item) is not str
            for item in nested["output_sha256"].values()
        )
        or any(
            type(item) is not str
            for item in nested["rule_names"].values()
        )
        or any(
            type(item) is not str
            for item in nested["adapter_ids"].values()
        )
    ):
        raise AssertionError("manifest nested exact type drift")
    lifecycle = nested["evidence_lifecycle_hardening"]
    if (
        type(
            lifecycle[
                "successor_regression_historical_deselection_count"
            ]
        )
        is not int
        or any(
            type(value_) is not bool
            for name, value_ in lifecycle.items()
            if name
            != "successor_regression_historical_deselection_count"
        )
    ):
        raise AssertionError("manifest lifecycle exact type drift")
    if (
        candidate["candidate_relative_path"] != CANDIDATE.as_posix()
        or candidate["definition_names"] != list(PUBLIC_DEFINITIONS)
        or candidate["marker_prefix_sha256"]
        != EXPECTED_MARKER_PREFIX_SHA256
        or candidate["normalized_ast_sha256"]
        != EXPECTED_DEFINITION_AST_SHA256
        or candidate["production_full_sha256"]
        != EXPECTED_PRODUCTION_SHA256
        or candidate["adapter_design_simulator_called"] is not False
        or candidate["public_closure_pure_memory"] is not True
        or nested["truth_matrix_group_counts"]
        != {
            "admit015_inherited_exact42_runtime": 42,
            "admit015_oracle_negative": 8,
            "admit015_source_negative": 11,
            "predecessor_representative_dispatch": 14,
            "public_dispatch": 4,
        }
        or nested["readiness"]
        != {
            **{name: True for name in TRUE_READINESS},
            **{name: False for name in FALSE_READINESS},
        }
        or any(
            item is not True
            for item in nested["output_materialization"].values()
        )
        or any(
            item is not True
            for name in (
                "output_read_policy",
                "lifecycle_policy",
                "source_read_policy",
            )
            for item in nested[name].values()
        )
        or nested["source_input_sha256"] != dict(SOURCE_BOUNDARY)
        or nested["precondition_transition"]
        != {
            "complete_count": 40,
            "implementation_blocking_count": 5,
            "incomplete_count": 5,
            "remaining_open_precondition_ids": [
                "PRE_034",
                "PRE_035",
                "PRE_036",
                "PRE_038",
                "PRE_042",
            ],
            "resolution": (
                "ADMIT_015 handler, immutable Exact15 registry and unified "
                "single-rule dispatcher implemented with first14 identity "
                "preservation"
            ),
            "resolved_precondition_ids": ["PRE_032", "PRE_033"],
            "row_count": 45,
            "supported_but_not_frozen_count": 0,
        }
    ):
        raise AssertionError("manifest nested semantic drift")


def _manifest(content: bytes) -> dict[str, Any]:
    value = json.loads(content, object_pairs_hook=_unique_object)
    if (
        type(value) is not dict
        or tuple(value) != EXPECTED_MANIFEST_KEYS
    ):
        raise AssertionError("manifest exact key/order drift")
    _assert_manifest_nested_schema(value)
    return value


def _assert_exact_object(
    actual: object,
    expected: object,
    path: str = "$",
) -> None:
    if type(actual) is not type(expected):
        raise AssertionError(
            f"manifest exact type drift at {path}: "
            f"{type(actual).__name__} != {type(expected).__name__}"
        )
    if type(actual) is dict:
        actual_mapping = actual
        expected_mapping = expected
        if tuple(actual_mapping) != tuple(expected_mapping):
            raise AssertionError(f"manifest key/order drift at {path}")
        for key in expected_mapping:
            _assert_exact_object(
                actual_mapping[key],
                expected_mapping[key],
                f"{path}.{key}",
            )
        return
    if type(actual) in {list, tuple}:
        actual_sequence = actual
        expected_sequence = expected
        if len(actual_sequence) != len(expected_sequence):
            raise AssertionError(f"manifest length drift at {path}")
        for index, (actual_item, expected_item) in enumerate(
            zip(actual_sequence, expected_sequence, strict=True)
        ):
            _assert_exact_object(
                actual_item,
                expected_item,
                f"{path}[{index}]",
            )
        return
    if actual != expected:
        raise AssertionError(f"manifest value drift at {path}")


def _expected_manifest(
    *,
    source_records: Sequence[Mapping[str, Any]],
    runtime: object,
    candidate_attestation: Mapping[str, Any],
    exact5_hashes: Mapping[str, str],
) -> dict[str, Any]:
    registered = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
    readiness = {
        **{name: True for name in TRUE_READINESS},
        **{name: False for name in FALSE_READINESS},
    }
    source_paths = [path for path, _ in SOURCE_BOUNDARY]
    source_pairs = [[path, digest] for path, digest in SOURCE_BOUNDARY]
    source_verification = [
        {
            **dict(record),
            "tracked": True,
            "filesystem_regular": True,
            "non_symlink": True,
            "parent_chain_non_symlink": True,
            "safe_descendant": True,
            "pinned_fd_read": True,
            "post_read_identity_verified": True,
            "final_leaf_identity_verified": True,
            "source_verified": True,
        }
        for record in source_records
    ]
    manifest: dict[str, Any] = {
        "project": "CovaPIE",
        "step": "unified dispatch runtime with ADMIT_001 to ADMIT_015 v1",
        "stage": STAGE_NAME,
        "manifest_schema_version": (
            "covapie_unified_dispatch_runtime_with_admit_001_to_015_"
            "manifest_v1"
        ),
        "expected_base_commit": BASE,
        "expected_base_parent": BASE_PARENT,
        "expected_base_tree": BASE_TREE,
        "expected_base_subject": BASE_SUBJECT,
        "canonical_evidence_python_implementation": "cpython",
        "canonical_evidence_python_version": "3.10.4",
        "ast_attestation_cross_python_version_portable": False,
        "noncanonical_python_policy": (
            "evaluator_semantic_smoke_only; "
            "artifact_build_checker_and_frozen_ast_forbidden"
        ),
        "python_runtime_migration_policy": (
            "explicit_contract_refresh_required"
        ),
        "exact15_identity": (
            "ADMIT_001_to_ADMIT_015_unified_single_rule_runtime_v1"
        ),
        "exact14_predecessor_identity": (
            "ADMIT_001_to_ADMIT_014_unified_single_rule_runtime_v1"
        ),
        "source_boundary_name": (
            "fixed_ordered_exact20_committed_source_boundary"
        ),
        "source_input_count": 20,
        "source_input_paths": source_paths,
        "source_input_sha256": dict(SOURCE_BOUNDARY),
        "source_path_list_sha256": _sha(
            json.dumps(source_paths, separators=(",", ":")).encode()
        ),
        "source_path_sha256_pairs_sha256": _sha(
            json.dumps(source_pairs, separators=(",", ":")).encode()
        ),
        "source_input_verification": source_verification,
        "source_read_policy": {
            "final_leaf_check_followed_by_final_parent_root_check": True,
            "leaf_fds_retained_through_final_parent_root_check": True,
            "six_field_identity": True,
            "no_atomic_path_snapshot_claim": True,
        },
        "source_validation_before_candidate_or_output_read": True,
        "candidate_production_source_attestation": {
            "adapter_design_simulator_called": False,
            "candidate_relative_path": CANDIDATE.as_posix(),
            "definition_count": 11,
            "definition_names": list(PUBLIC_DEFINITIONS),
            "marker_prefix_sha256": candidate_attestation[
                "prefix_sha256"
            ],
            "normalized_ast_sha256": dict(
                candidate_attestation["definition_ast_sha256"]
            ),
            "production_full_sha256": candidate_attestation[
                "full_sha256"
            ],
            "public_closure_pure_memory": True,
        },
        "public_marker": PUBLIC_MARKER,
        "public_definition_count": 11,
        "public_definitions": list(PUBLIC_DEFINITIONS),
        "runtime_dependency_imports": [
            "exact14_unified_runtime_predecessor",
            "admit015_standalone_evaluator",
            "admit015_committed_independent_formal_interface_oracle",
        ],
        "adapter_design_simulator_called_by_public_runtime": False,
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
        "public_dispatch_signature": str(
            inspect.signature(runtime.evaluate_admission_rule)
        ),
        "public_dispatch_signature_matches_exact14": True,
        "public_dispatch_uses_local_registry": True,
        "public_dispatch_cardinality": "single_rule_only",
        "public_dispatch_precedence": [
            "exact_builtin_str",
            "known_rule",
            "callable_discovered",
            "adapter_ready",
            "successor_local_registry_handler",
        ],
        "result_schema_version": runtime.RESULT_SCHEMA_VERSION,
        "result_field_count": 13,
        "result_fields": list(runtime.RESULT_FIELDS),
        "dispatch_error_fields": list(runtime.DISPATCH_ERROR_FIELDS),
        "dispatch_error_codes": list(runtime.DISPATCH_ERROR_CODES),
        "outcome_vocabulary": list(runtime.OUTCOME_VOCABULARY),
        "known_rule_ids": list(registered),
        "callable_discovered_rule_ids": list(registered),
        "adapter_ready_rule_ids": list(registered),
        "legacy_adapter_not_ready_rule_ids": [],
        "registered_rule_ids": list(registered),
        "known_not_registered_rule_ids": [],
        "registered_rule_count": 15,
        "registry_mapping_proxy_type": True,
        "rule_names": dict(runtime.RULE_NAMES),
        "adapter_ids": dict(runtime.ADAPTER_IDS),
        "first_fourteen_handler_identity_reused": {
            rule_id: True for rule_id in registered[:14]
        },
        "shared_exact13_identity_preserved": True,
        "predecessor_dispatcher_unchanged": True,
        "successor_dispatcher_distinct": True,
        "admit_015_handler": "_evaluate_registered_admit_015",
        "admit_015_handler_signature": str(
            inspect.signature(runtime._evaluate_registered_admit_015)
        ),
        "admit_015_source_fields": list(SOURCE_FIELDS),
        "admit_015_routing_precedence": [
            "batch_context_must_be_none",
            "evaluation_context_must_be_none",
            "download_result_context_must_be_none",
            "candidate_record_mapping_validation",
            "stage_authorization_context_forwarded_same_object",
            "formal_evaluator_exactly_once",
            "standalone_source_exact9_validation",
            "independent_oracle_exactly_once",
            "full_exact9_exact_type_value_equality",
            "exact9_to_exact13_projection",
        ],
        "admit_015_candidate_mapping_invalid_reason": (
            "ADMIT_015_CANDIDATE_RECORD_MAPPING_INVALID"
        ),
        "admit_015_candidate_invalid_call_counts": {
            "formal": 0,
            "oracle": 0,
            "candidate_key_access": 0,
            "stage_target_access": 0,
        },
        "admit_015_source_type": "Admit015EvaluationResult",
        "admit_015_source_type_invalid_reason": SOURCE_TYPE_ERROR,
        "admit_015_source_invariant_invalid_reason": (
            SOURCE_INVARIANT_ERROR
        ),
        "admit_015_source_prevalidation_before_oracle": True,
        "admit_015_oracle": (
            "classify_admit_015_formal_evaluator_interface_design"
        ),
        "admit_015_oracle_result_type": (
            "Admit015EvaluationResultContractDesign"
        ),
        "admit_015_source_oracle_full_exact9_equality_required": True,
        "admit_015_exact13_projection": {
            "normalized_values": (
                "canonical exact bool pair to lowercase string pair"
            ),
            "validated_candidate_fields": [],
            "consumed_candidate_fields": [],
            "consumed_context_items": (
                "source.consumed_stage_authorization_fields"
            ),
        },
        "contract_row_count": 45,
        "truth_matrix_row_count": 79,
        "truth_matrix_group_counts": {
            "admit015_inherited_exact42_runtime": 42,
            "admit015_oracle_negative": 8,
            "admit015_source_negative": 11,
            "predecessor_representative_dispatch": 14,
            "public_dispatch": 4,
        },
        "truth_input_representation_columns": list(
            TRUTH_INPUT_REPRESENTATION_COLUMNS
        ),
        "truth_input_representation_semantics_independently_verified": True,
        "truth_trace_columns": [
            "expected_call_order",
            "observed_call_order",
            "expected_stage_context_identity_preserved",
            "observed_stage_context_identity_preserved",
            "adapter_stage_target_access_count",
            "formal_stage_target_access_count",
            "oracle_stage_target_access_count",
        ],
        "truth_trace_semantics_independently_verified": True,
        "admit_015_inherited_exact42_runtime_case_count": 42,
        "admit_015_source_negative_case_count": 11,
        "admit_015_oracle_negative_case_count": 8,
        "public_dispatch_case_count": 4,
        "predecessor_representative_dispatch_count": 14,
        "predecessor_committed_truth_case_count": 79,
        "predecessor_committed_registry_audit_count": 27,
        "registry_identity_audit_row_count": 27,
        "safety_audit_row_count": 32,
        "issue_inventory_row_count": 30,
        "issue_transition_count": 1,
        "issue_transition_id": (
            "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
        ),
        "issue_coverage_before": ["ADMIT_015"],
        "issue_coverage_after": [],
        "issue_coverage_effective_status": "resolved",
        "precondition_transition": {
            "row_count": 45,
            "complete_count": 40,
            "supported_but_not_frozen_count": 0,
            "incomplete_count": 5,
            "implementation_blocking_count": 5,
            "resolved_precondition_ids": ["PRE_032", "PRE_033"],
            "resolution": (
                "ADMIT_015 handler, immutable Exact15 registry and unified "
                "single-rule dispatcher implemented with first14 identity "
                "preservation"
            ),
            "remaining_open_precondition_ids": [
                "PRE_034",
                "PRE_035",
                "PRE_036",
                "PRE_038",
                "PRE_042",
            ],
        },
        "remaining_open_issue_ids": [
            "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
            "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
            "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
        ],
        "readiness": readiness,
        "current_permission": False,
        "synthetic_true_case_changes_current_permission": False,
        "authorized_admit_015_training_execution_count": 0,
        "admit_015_implemented": True,
        "admit_015_registered_in_engine": True,
        "mandatory_training_authorization_enforcement_api_frozen": False,
        "mandatory_training_authorization_enforcement_implemented": False,
        "combined_permission_semantics_frozen": False,
        "provider_mapping_validated": False,
        "real_provider_evaluation_ready": False,
        "ready_for_bulk_download_now": False,
        "combined_candidate_verdict_implemented": False,
        "cross_rule_aggregation_implemented": False,
        "feature_semantics_audit_completed": False,
        "historical_unknown_atom_feature_policy_resolved": False,
        "historical_feature_semantics_known": False,
        "real_training_ready": False,
        "ready_for_training": False,
        "step12d_is_final_training_feature_contract": False,
        "step12d_status": (
            "smoke_legality_only_not_final_training_feature_contract"
        ),
        "canonical_masks": [
            {"semantic_name": "warhead_only", "alias": "A"},
            {"semantic_name": "linker_plus_warhead", "alias": "B"},
            {"semantic_name": "scaffold_plus_warhead", "alias": "B2"},
            {"semantic_name": "scaffold_only", "alias": "B3"},
            {
                "semantic_name": "scaffold_plus_linker_plus_warhead",
                "alias": "C",
            },
        ],
        "canonical_mask_count": 5,
        "feature_semantics_note": (
            "feature-semantics audit remains mandatory before training; "
            "Step12D was only a smoke legality check; historical "
            "UNKNOWN_ATOM_FEATURE_POLICY and feature_semantics_known=False "
            "remain subject to explicit audit"
        ),
        "output_files": list(OUTPUTS),
        "output_file_count": 6,
        "output_csv_schemas": {
            OUTPUTS[0]: list(CONTRACT_HEADER),
            OUTPUTS[1]: list(TRUTH_HEADER),
            OUTPUTS[2]: list(REGISTRY_HEADER),
            OUTPUTS[3]: list(SAFETY_HEADER),
            OUTPUTS[4]: list(ISSUE_HEADER),
        },
        "output_sha256": {
            name: exact5_hashes[name] for name in OUTPUTS[:5]
        },
        "output_sha256_excludes_manifest_self_hash": True,
        "output_read_policy": {
            "all_leaf_fds_retained": True,
            "initial_inventory": True,
            "second_inventory": True,
            "final_inventory": True,
            "final_leaf_checks": True,
            "final_root_parent_checks_after_final_leaf": True,
            "parent_strict_resolve": True,
        },
        "output_materialization": {
            "all_payloads_built_before_mutation": True,
            "exact_six_allowlist": True,
            "pinned_parent_root_staging_leaf": True,
            "exclusive_create": True,
            "file_fsync": True,
            "staging_directory_fsync": True,
            "renameat2_RENAME_NOREPLACE": True,
            "GPFS_EINVAL_fail_closed": True,
            "parent_fsync": True,
            "destination_name_inode_binding": True,
            "complete_set_postverify": True,
            "all_leaf_descriptors_retained_through_final_traversal": True,
            "staging_lexical_binding_verified": True,
            "failure_staging_retained": True,
            "failure_staging_never_deleted": True,
            "authenticated_retained_path_only": True,
            "parent_and_staging_binding_rechecked_inside_rename": True,
            "existing_exact_set_inode_preserving_noop": True,
            "mismatch_repair_forbidden": True,
        },
        "evidence_lifecycle_hardening": {
            "exact10_lifecycle_exact_inventory": True,
            "source_and_output_full_identity_post_traversal": True,
            "source_and_output_final_leaf_identity_post_traversal": True,
            "manifest_duplicate_and_exact_schema_rejection": True,
            "publisher_destination_binding_rechecks": True,
            "checker_exact42_specs_owned_without_project_checker_import": True,
            "artifact_semantics_rebuilt_after_sha_verification": True,
            "bounded_recursive_no_follow_lifecycle": True,
            "successor_regression_historical_deselection_count": 0,
        },
        "lifecycle_policy": {
            "bounded_recursive_no_follow": True,
            "nested_nonignored_rejected": True,
            "nested_ignored_rejected": True,
            "nested_tracked_rejected": True,
            "symlink_directory_rejected": True,
            "sibling_derived_root_rejected": True,
            "exact10_recursive_allowlist": True,
        },
        "all_source_boundary_checks_passed": True,
        "all_predecessor_contract_checks_passed": True,
        "all_runtime_contract_checks_passed": True,
        "all_truth_matrix_checks_passed": True,
        "all_registry_audit_checks_passed": True,
        "all_issue_checks_passed": True,
        "all_safety_checks_passed": True,
        "all_checks_passed": True,
        "validation_failures": [],
        "recommended_next_step": (
            "design_covapie_admit_015_mandatory_training_"
            "authorization_enforcement_contract_v1"
        ),
    }
    manifest.update(readiness)
    return json.loads(
        json.dumps(manifest, sort_keys=True),
        object_pairs_hook=_unique_object,
    )


def output_bytes(
    root: Path = ROOT,
    stage: Path = STAGE,
) -> dict[str, bytes]:
    stage_root = Path(os.path.abspath(root / stage))
    parent = stage_root.parent
    parent_item = os.lstat(parent)
    parent_identity = _full_identity(parent_item)
    root_item = os.lstat(stage_root)
    root_identity = _full_identity(root_item)
    if (
        not stat.S_ISDIR(parent_item.st_mode)
        or stat.S_ISLNK(parent_item.st_mode)
        or not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
        or stage_root.resolve(strict=True) != stage_root
    ):
        raise AssertionError("output root unsafe")
    parent_fd = os.open(parent, DIR_FLAGS)
    root_fd = os.open(stage_root.name, DIR_FLAGS, dir_fd=parent_fd)
    leaves: list[
        tuple[str, int, tuple[int, int, int, int, int, int]]
    ] = []
    try:
        def verify_inventory(phase: str) -> None:
            names = tuple(os.listdir(root_fd))
            if len(names) != 6 or set(names) != set(OUTPUTS):
                raise AssertionError(
                    f"output {phase} inventory is not Exact6"
                )

        def verify_parent_root_bindings(phase: str) -> None:
            lexical_parent = os.lstat(parent)
            lexical_root = os.stat(
                stage_root.name,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
            if (
                _full_identity(lexical_parent) != parent_identity
                or _full_identity(os.fstat(parent_fd)) != parent_identity
                or not stat.S_ISDIR(lexical_parent.st_mode)
                or stat.S_ISLNK(lexical_parent.st_mode)
                or parent.resolve(strict=True) != parent
                or _full_identity(lexical_root) != root_identity
                or _full_identity(os.fstat(root_fd)) != root_identity
                or not stat.S_ISDIR(lexical_root.st_mode)
                or stat.S_ISLNK(lexical_root.st_mode)
                or stage_root.resolve(strict=True) != stage_root
            ):
                raise AssertionError(
                    f"output {phase} root/parent binding drift"
                )

        def verify_leaves(phase: str) -> None:
            for name, descriptor, identity in leaves:
                lexical = os.stat(
                    name,
                    dir_fd=root_fd,
                    follow_symlinks=False,
                )
                if (
                    _full_identity(os.fstat(descriptor)) != identity
                    or _full_identity(lexical) != identity
                    or not stat.S_ISREG(lexical.st_mode)
                    or stat.S_ISLNK(lexical.st_mode)
                ):
                    raise AssertionError(
                        f"output {phase} leaf traversal changed"
                    )

        verify_parent_root_bindings("initial")
        verify_inventory("initial")
        for name in OUTPUTS:
            before = os.stat(
                name, dir_fd=root_fd, follow_symlinks=False
            )
            identity = _full_identity(before)
            if (
                not stat.S_ISREG(before.st_mode)
                or stat.S_ISLNK(before.st_mode)
                or before.st_size > MAX_BYTES
            ):
                raise AssertionError("output leaf unsafe")
            descriptor = os.open(name, READ_FLAGS, dir_fd=root_fd)
            leaves.append((name, descriptor, identity))
            if _full_identity(os.fstat(descriptor)) != identity:
                raise AssertionError("output leaf stat/open race")
        payloads = {}
        for name, descriptor, _ in leaves:
            chunks = []
            while True:
                chunk = os.read(descriptor, 1 << 16)
                if not chunk:
                    break
                chunks.append(chunk)
            payloads[name] = b"".join(chunks)
        verify_leaves("first")
        verify_parent_root_bindings("first")
        verify_inventory("second")
        verify_leaves("final")
        verify_inventory("final")
        verify_parent_root_bindings("final")
        return payloads
    finally:
        for _, descriptor, _ in leaves:
            os.close(descriptor)
        os.close(root_fd)
        os.close(parent_fd)


def _exact_json(value: object, names: Sequence[str]) -> str:
    return json.dumps(
        {name: getattr(value, name) for name in names},
        ensure_ascii=True,
        separators=(",", ":"),
    )


def _expected_unified_json(
    outcome: str,
    reason: str,
    *,
    normalized: tuple[tuple[str, str], ...] = (),
    consumed: tuple[str, ...] = (),
) -> str:
    return json.dumps(
        {
            "schema_version": (
                "covapie_unified_admission_rule_evaluation_v1"
            ),
            "admission_rule_id": "ADMIT_015",
            "admission_rule_name": (
                "current_gate_grants_no_training_permission"
            ),
            "outcome": outcome,
            "passed": outcome == "passed",
            "blocks_candidate": outcome != "passed",
            "reason": reason,
            "normalized_values": normalized,
            "validated_candidate_fields": (),
            "consumed_candidate_fields": (),
            "consumed_context_items": consumed,
            "evaluator_io_used": False,
            "adapter_id": "covapie_admit_015_unified_adapter_v1",
        },
        ensure_ascii=True,
        separators=(",", ":"),
    )


def _expected_error_json(
    code: str,
    reason: str,
    ready: bool,
) -> str:
    return json.dumps(
        {
            "code": code,
            "admission_rule_id": "ADMIT_015",
            "known_rule": True,
            "callable_discovered": True,
            "adapter_ready": ready,
            "reason": reason,
        },
        ensure_ascii=True,
        separators=(",", ":"),
    )


class CandidateProbe(Mapping[str, object]):
    def __init__(self) -> None:
        self.access_count = 0

    def __getitem__(self, key: str) -> object:
        self.access_count += 1
        raise AssertionError("candidate read")

    def __iter__(self):
        self.access_count += 1
        raise AssertionError("candidate iteration")

    def __len__(self) -> int:
        self.access_count += 1
        raise AssertionError("candidate length")

    def get(self, key: str, default: object = None) -> object:
        self.access_count += 1
        raise AssertionError("candidate get")

    def __contains__(self, key: object) -> bool:
        self.access_count += 1
        raise AssertionError("candidate contains")


class StageProbe(Mapping[str, object]):
    def __init__(
        self,
        values: Mapping[str, object] | None = None,
        *,
        error: BaseException | None = None,
        alternating: bool = False,
    ) -> None:
        self.values = {} if values is None else dict(values)
        self.error = error
        self.alternating = alternating
        self.access_count = 0

    def __getitem__(self, key: str) -> object:
        self.access_count += 1
        if self.error is not None:
            raise self.error
        if self.alternating:
            return self.access_count == 1
        return self.values[key]

    def __iter__(self):
        raise AssertionError("stage iteration")

    def __len__(self) -> int:
        raise AssertionError("stage length")


def _independent_input_representations(
    scenario: str,
    candidate: object,
    batch: object,
    evaluation: object,
    download: object,
    stage: object,
) -> tuple[str, str, str, str, str]:
    def candidate_token(value: object) -> str:
        if isinstance(value, CandidateProbe):
            return "instrumented_mapping"
        if type(value) is dict and not value:
            return "{}"
        if type(value) is object:
            return "object"
        raise AssertionError(
            f"checker candidate representation unsupported: {scenario}"
        )

    def context_token(value: object) -> str:
        if value is None:
            return "None"
        if type(value) is dict and not value:
            return "{}"
        if type(value) is object:
            return "object"
        raise AssertionError(
            f"checker context representation unsupported: {scenario}"
        )

    def stage_token(value: object) -> str:
        if value is None:
            return "None"
        if type(value) is object:
            return "object"
        if not isinstance(value, StageProbe):
            raise AssertionError(
                f"checker stage representation unsupported: {scenario}"
            )
        if value.alternating:
            return "alternating_mapping"
        if value.error is not None:
            error_tokens = {
                KeyError: "KeyError_mapping",
                RuntimeError: "RuntimeError_mapping",
                ValueError: "ValueError_mapping",
            }
            token = error_tokens.get(type(value.error))
            if token is None:
                raise AssertionError(
                    f"checker stage error unsupported: {scenario}"
                )
            return token
        values = tuple(value.values.items())
        tokens = {
            (): "{}",
            (("current_stage_training_authorized", False),): (
                "{target:False}"
            ),
            (("current_stage_training_authorized", True),): (
                "{target:True}"
            ),
            (
                ("current_stage_training_authorized", True),
                ("current_stage_download_authorized", True),
                ("extra", 1),
            ): "{target:True,download:True,extra:1}",
        }
        token = tokens.get(values)
        if token is None:
            raise AssertionError(
                f"checker stage value unsupported: {scenario}"
            )
        return token

    return (
        candidate_token(candidate),
        context_token(batch),
        context_token(evaluation),
        context_token(download),
        stage_token(stage),
    )


def _independent_specs() -> tuple[dict[str, object], ...]:
    context_code = "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID"
    adapter_code = "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
    batch_reason = "ADMIT_015_BATCH_CONTEXT_MUST_BE_NONE"
    evaluation_reason = "ADMIT_015_EVALUATION_CONTEXT_MUST_BE_NONE"
    download_reason = "ADMIT_015_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"
    candidate_reason = "ADMIT_015_CANDIDATE_RECORD_MAPPING_INVALID"
    required_reason = "STAGE_AUTHORIZATION_CONTEXT_REQUIRED"
    mapping_reason = "STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID"
    missing_reason = "CURRENT_STAGE_TRAINING_AUTHORIZED_MISSING"
    lookup_reason = "STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED"
    false_reason = "TRAINING_NOT_AUTHORIZED"
    required = _expected_unified_json("blocked", required_reason)
    mapping = _expected_unified_json("blocked", mapping_reason)
    missing = _expected_unified_json(
        "blocked", missing_reason, consumed=(TARGET_ITEM,)
    )
    lookup = _expected_unified_json(
        "blocked", lookup_reason, consumed=(TARGET_ITEM,)
    )
    false_result = _expected_unified_json(
        "blocked",
        false_reason,
        normalized=((TARGET_ITEM, "false"),),
        consumed=(TARGET_ITEM,),
    )
    true_result = _expected_unified_json(
        "passed",
        "",
        normalized=((TARGET_ITEM, "true"),),
        consumed=(TARGET_ITEM,),
    )
    candidate = _expected_unified_json("invalid", candidate_reason)

    def entry(
        group: str,
        case_id: str,
        scenario: str,
        *,
        code: str = "",
        reason: str = "",
        result: str = "",
        formal: int = 0,
        oracle: int = 0,
        formal_access: int = 0,
        oracle_access: int = 0,
        identity: str = "n/a",
    ) -> dict[str, object]:
        return {
            "group": group,
            "case_id": case_id,
            "scenario": scenario,
            "code": code,
            "reason": reason,
            "result": result,
            "formal": formal,
            "oracle": oracle,
            "formal_access": formal_access,
            "oracle_access": oracle_access,
            "identity": identity,
        }

    def context(reason: str) -> str:
        return _expected_error_json(context_code, reason, True)

    def adapter(reason: str) -> str:
        return _expected_error_json(adapter_code, reason, False)

    common = {
        "formal": 1,
        "oracle": 1,
        "formal_access": 1,
        "oracle_access": 1,
        "identity": "true",
    }
    specs = (
        entry("routing_failure", "batch_non_none", "batch_object", code=context_code, reason=batch_reason, result=context(batch_reason)),
        entry("routing_failure", "batch_empty_mapping", "batch_mapping", code=context_code, reason=batch_reason, result=context(batch_reason)),
        entry("routing_failure", "evaluation_non_none", "evaluation_object", code=context_code, reason=evaluation_reason, result=context(evaluation_reason)),
        entry("routing_failure", "evaluation_empty_mapping", "evaluation_mapping", code=context_code, reason=evaluation_reason, result=context(evaluation_reason)),
        entry("routing_failure", "download_non_none", "download_object", code=context_code, reason=download_reason, result=context(download_reason)),
        entry("routing_failure", "download_empty_mapping", "download_mapping", code=context_code, reason=download_reason, result=context(download_reason)),
        entry("routing_failure", "multiple_invalid_batch_first", "all_invalid", code=context_code, reason=batch_reason, result=context(batch_reason)),
        entry("routing_failure", "multiple_invalid_evaluation_first", "evaluation_download_candidate_invalid", code=context_code, reason=evaluation_reason, result=context(evaluation_reason)),
        entry("routing_failure", "multiple_invalid_download_first", "download_candidate_invalid", code=context_code, reason=download_reason, result=context(download_reason)),
        entry("candidate", "candidate_non_mapping", "candidate_invalid", reason=candidate_reason, result=candidate),
        entry("candidate", "candidate_empty", "candidate_empty", reason=required_reason, result=required, formal=1, oracle=1, identity="true"),
        entry("candidate", "candidate_instrumented", "candidate_probe", reason=required_reason, result=required, formal=1, oracle=1, identity="true"),
        entry("stage", "stage_none", "stage_none", reason=required_reason, result=required, formal=1, oracle=1, identity="true"),
        entry("stage", "stage_object", "stage_object", reason=mapping_reason, result=mapping, formal=1, oracle=1, identity="true"),
        entry("stage", "stage_empty_mapping", "stage_empty", reason=missing_reason, result=missing, **common),
        entry("stage", "stage_false", "stage_false", reason=false_reason, result=false_result, **common),
        entry("stage", "stage_true", "stage_true", result=true_result, **common),
        entry("stage", "stage_extra_keys", "stage_extra", result=true_result, **common),
        entry("stage", "stage_keyerror", "stage_keyerror", reason=missing_reason, result=missing, **common),
        entry("stage", "stage_runtimeerror", "stage_runtimeerror", reason=lookup_reason, result=lookup, **common),
        entry("stage", "stage_valueerror", "stage_valueerror", reason=lookup_reason, result=lookup, **common),
        entry("calls", "formal_once", "stage_true", result=true_result, **common),
        entry("calls", "oracle_once", "stage_true", result=true_result, **common),
        entry("calls", "source_invalid_no_oracle", "source_wrong_type", code=adapter_code, reason=SOURCE_TYPE_ERROR, result=adapter(SOURCE_TYPE_ERROR), formal=1, identity="true"),
        entry("calls", "nonrepeatable_mismatch", "nonrepeatable", code=adapter_code, reason=SOURCE_INVARIANT_ERROR, result=adapter(SOURCE_INVARIANT_ERROR), **common),
        entry("source_failure", "source_wrong_type", "source_wrong_type", code=adapter_code, reason=SOURCE_TYPE_ERROR, result=adapter(SOURCE_TYPE_ERROR), formal=1, identity="true"),
        entry("source_failure", "source_subclass", "source_subclass", code=adapter_code, reason=SOURCE_TYPE_ERROR, result=adapter(SOURCE_TYPE_ERROR), formal=1, identity="true"),
        entry("source_failure", "source_storage_order", "source_storage", code=adapter_code, reason=SOURCE_INVARIANT_ERROR, result=adapter(SOURCE_INVARIANT_ERROR), formal=1, identity="true"),
        entry("source_failure", "source_type_drift", "source_type_drift", code=adapter_code, reason=SOURCE_INVARIANT_ERROR, result=adapter(SOURCE_INVARIANT_ERROR), formal=1, identity="true"),
        entry("source_failure", "source_invariant", "source_invariant", code=adapter_code, reason=SOURCE_INVARIANT_ERROR, result=adapter(SOURCE_INVARIANT_ERROR), formal=1, identity="true"),
        entry("oracle_failure", "oracle_wrong_type", "oracle_wrong_type", code=adapter_code, reason=SOURCE_INVARIANT_ERROR, result=adapter(SOURCE_INVARIANT_ERROR), formal=1, oracle=1, identity="true"),
        entry("oracle_failure", "oracle_storage", "oracle_storage", code=adapter_code, reason=SOURCE_INVARIANT_ERROR, result=adapter(SOURCE_INVARIANT_ERROR), formal=1, oracle=1, identity="true"),
        entry("oracle_failure", "oracle_mismatch", "oracle_mismatch", code=adapter_code, reason=SOURCE_INVARIANT_ERROR, result=adapter(SOURCE_INVARIANT_ERROR), formal=1, oracle=1, identity="true"),
        entry("oracle_failure", "oracle_exception", "oracle_exception", code=adapter_code, reason=SOURCE_INVARIANT_ERROR, result=adapter(SOURCE_INVARIANT_ERROR), formal=1, oracle=1, identity="true"),
        entry("projection", "candidate_fields_empty", "stage_true", result=true_result, **common),
        entry("projection", "consumed_context", "stage_true", result=true_result, **common),
        entry("projection", "false_lowercase", "stage_false", reason=false_reason, result=false_result, **common),
        entry("projection", "true_lowercase", "stage_true", result=true_result, **common),
        entry("registry", "current_exact14", "stage_true", result=true_result, **common),
        entry("registry", "future_exact15", "stage_true", result=true_result, **common),
        entry("registry", "known_unregistered", "stage_true", result=true_result, **common),
        entry("registry", "handler_identity", "stage_true", result=true_result, **common),
    )
    route_text = (
        ("batch_non_none", "first failure: batch must be None", "batch=object"),
        ("batch_empty_mapping", "empty mapping is not None", "batch={}"),
        ("evaluation_non_none", "second failure: evaluation must be None", "evaluation=object"),
        ("evaluation_empty_mapping", "empty mapping is not None", "evaluation={}"),
        ("download_non_none", "third failure: download result must be None", "download=object"),
        ("download_empty_mapping", "empty mapping is not None", "download={}"),
        ("multiple_invalid_batch_first", "batch wins over all later failures", "all forbidden non-None"),
        ("multiple_invalid_evaluation_first", "evaluation wins over download and candidate", "evaluation/download non-None"),
        ("multiple_invalid_download_first", "download wins over candidate", "download non-None candidate invalid"),
        ("candidate_non_mapping", "fourth check returns invalid Exact13", "candidate=object"),
        ("candidate_empty", "empty Mapping is valid and never read", "candidate={};stage=None"),
        ("candidate_instrumented", "candidate Mapping key access remains zero", "candidate=instrumented;stage=None"),
        ("stage_none", "None forwarded without routing error", "stage=None"),
        ("stage_object", "non-Mapping forwarded without routing error", "stage=object"),
        ("stage_empty_mapping", "empty Mapping accessed by formal then oracle", "stage={}"),
        ("stage_false", "exact False accessed twice and projected lowercase", "stage={target:False}"),
        ("stage_true", "exact True accessed twice and projected lowercase", "stage={target:True}"),
        ("stage_extra_keys", "extra keys and download item not accessed", "stage={target:True,download:True,extra:1}"),
        ("stage_keyerror", "KeyError evaluated independently twice", "stage=KeyError mapping"),
        ("stage_runtimeerror", "RuntimeError evaluated independently twice", "stage=RuntimeError mapping"),
        ("stage_valueerror", "ValueError evaluated independently twice", "stage=ValueError mapping"),
        ("formal_once", "formal called exactly once", "stable Mapping"),
        ("oracle_once", "oracle called once after source validation", "stable Mapping"),
        ("source_invalid_no_oracle", "source prevalidation precedes oracle", "formal wrong type"),
        ("nonrepeatable_mismatch", "formal/oracle mismatch fails closed", "stateful Mapping"),
        ("source_wrong_type", "exact formal result type required", "formal=object"),
        ("source_subclass", "formal result subclass rejected", "formal=subclass"),
        ("source_storage_order", "Exact9 storage order required", "formal=reordered"),
        ("source_type_drift", "Exact9 top-level types required", "formal=type drift"),
        ("source_invariant", "Exact9 constructor invariants required", "formal=contradiction"),
        ("oracle_wrong_type", "exact oracle result type required", "oracle=object"),
        ("oracle_storage", "oracle Exact9 storage/order required", "oracle=reordered"),
        ("oracle_mismatch", "all Exact9 types and values must match", "oracle=value drift"),
        ("oracle_exception", "oracle exception fails closed", "oracle=raises"),
        ("candidate_fields_empty", "stage fields never become candidate fields", "valid source"),
        ("consumed_context", "consumed stage field maps to context item", "valid source"),
        ("false_lowercase", "False projects to exact lowercase false", "stage={target:False}"),
        ("true_lowercase", "True projects to exact lowercase true", "stage={target:True}"),
        ("current_exact14", "current registry remains ADMIT_001..014", "ADMIT_001..014"),
        ("future_exact15", "future order appends ADMIT_015 only", "ADMIT_001..015"),
        ("known_unregistered", "ADMIT_015 is currently known-not-registered", "ADMIT_015"),
        ("handler_identity", "first fourteen handler identities preserved", "identity_preserved"),
    )
    representations = {
        "batch_non_none": ("{}", "object", "None", "None", "{target:True}"),
        "batch_empty_mapping": ("{}", "{}", "None", "None", "{target:True}"),
        "evaluation_non_none": ("{}", "None", "object", "None", "{target:True}"),
        "evaluation_empty_mapping": ("{}", "None", "{}", "None", "{target:True}"),
        "download_non_none": ("{}", "None", "None", "object", "{target:True}"),
        "download_empty_mapping": ("{}", "None", "None", "{}", "{target:True}"),
        "multiple_invalid_batch_first": (
            "object", "object", "object", "object", "{target:True}",
        ),
        "multiple_invalid_evaluation_first": (
            "object", "None", "object", "object", "{target:True}",
        ),
        "multiple_invalid_download_first": (
            "object", "None", "None", "object", "{target:True}",
        ),
        "candidate_non_mapping": ("object", "None", "None", "None", "{}"),
        "candidate_empty": ("{}", "None", "None", "None", "None"),
        "candidate_instrumented": (
            "instrumented_mapping", "None", "None", "None", "None",
        ),
        "stage_none": ("{}", "None", "None", "None", "None"),
        "stage_object": ("{}", "None", "None", "None", "object"),
        "stage_empty_mapping": ("{}", "None", "None", "None", "{}"),
        "stage_false": ("{}", "None", "None", "None", "{target:False}"),
        "stage_true": ("{}", "None", "None", "None", "{target:True}"),
        "stage_extra_keys": (
            "{}", "None", "None", "None",
            "{target:True,download:True,extra:1}",
        ),
        "stage_keyerror": (
            "{}", "None", "None", "None", "KeyError_mapping",
        ),
        "stage_runtimeerror": (
            "{}", "None", "None", "None", "RuntimeError_mapping",
        ),
        "stage_valueerror": (
            "{}", "None", "None", "None", "ValueError_mapping",
        ),
        "formal_once": ("{}", "None", "None", "None", "{target:True}"),
        "oracle_once": ("{}", "None", "None", "None", "{target:True}"),
        "source_invalid_no_oracle": (
            "{}", "None", "None", "None", "None",
        ),
        "nonrepeatable_mismatch": (
            "{}", "None", "None", "None", "alternating_mapping",
        ),
        "source_wrong_type": ("{}", "None", "None", "None", "None"),
        "source_subclass": ("{}", "None", "None", "None", "None"),
        "source_storage_order": ("{}", "None", "None", "None", "None"),
        "source_type_drift": ("{}", "None", "None", "None", "None"),
        "source_invariant": ("{}", "None", "None", "None", "None"),
        "oracle_wrong_type": ("{}", "None", "None", "None", "None"),
        "oracle_storage": ("{}", "None", "None", "None", "None"),
        "oracle_mismatch": ("{}", "None", "None", "None", "None"),
        "oracle_exception": ("{}", "None", "None", "None", "None"),
        "candidate_fields_empty": (
            "{}", "None", "None", "None", "{target:True}",
        ),
        "consumed_context": (
            "{}", "None", "None", "None", "{target:True}",
        ),
        "false_lowercase": (
            "{}", "None", "None", "None", "{target:False}",
        ),
        "true_lowercase": (
            "{}", "None", "None", "None", "{target:True}",
        ),
        "current_exact14": (
            "{}", "None", "None", "None", "{target:True}",
        ),
        "future_exact15": (
            "{}", "None", "None", "None", "{target:True}",
        ),
        "known_unregistered": (
            "{}", "None", "None", "None", "{target:True}",
        ),
        "handler_identity": (
            "{}", "None", "None", "None", "{target:True}",
        ),
    }
    if (
        len(specs) != 42
        or tuple(spec["case_id"] for spec in specs)
        != tuple(case_id for case_id, _, _ in route_text)
        or tuple(representations)
        != tuple(case_id for case_id, _, _ in route_text)
    ):
        raise AssertionError("checker-owned Exact42 identity drift")
    return tuple(
        {
            **spec,
            "condition": condition,
            "envelope": envelope,
            "input_representations": representations[case_id],
        }
        for spec, (case_id, condition, envelope) in zip(
            specs, route_text, strict=True
        )
    )


def _verify_exact42_committed_continuity(
    specs: Sequence[Mapping[str, object]],
) -> None:
    content = pinned_read(ROOT, Path(SOURCE_BOUNDARY[9][0]))
    rows = list(
        csv.DictReader(io.StringIO(content.decode(), newline=""))
    )
    if len(rows) != 42:
        raise AssertionError("committed routing Exact42 drift")
    for index, (spec, row) in enumerate(
        zip(specs, rows, strict=True),
        1,
    ):
        expected_order = (
            "formal|oracle"
            if spec["oracle"] == 1
            else "formal"
            if spec["formal"] == 1
            else ""
        )
        if (
            row["matrix_order"] != str(index)
            or row["matrix_group"] != spec["group"]
            or row["case_id"] != spec["case_id"]
            or row["routing_condition"] != spec["condition"]
            or row["envelope_representation"] != spec["envelope"]
            or row["expected_dispatch_code"] != spec["code"]
            or row["expected_reason"] != spec["reason"]
            or row["expected_result_json"] != spec["result"]
            or row["formal_call_count"] != str(spec["formal"])
            or row["oracle_call_count"] != str(spec["oracle"])
            or row["formal_stage_key_access_count"]
            != str(spec["formal_access"])
            or row["oracle_stage_key_access_count"]
            != str(spec["oracle_access"])
            or row["identity_preserved"] != spec["identity"]
            or row["observed_call_order"] != expected_order
        ):
            raise AssertionError(
                f"committed routing continuity drift: {spec['case_id']}"
            )


def _mutate_exact9(
    value: object,
    scenario: str,
    fields: Sequence[str] = SOURCE_FIELDS,
) -> object:
    if scenario.endswith("wrong_type"):
        return object()
    if scenario in {"source_subclass", "oracle_subclass"}:
        try:
            subclass = type("_CheckerExact9Subclass", (type(value),), {})
        except TypeError:
            return object()
        instance = object.__new__(subclass)
        for name in fields:
            object.__setattr__(instance, name, getattr(value, name))
        return instance
    if scenario in {"source_storage", "oracle_storage"}:
        storage = vars(value)
        reordered = {name: storage[name] for name in reversed(tuple(storage))}
        storage.clear()
        storage.update(reordered)
    elif scenario in {"source_type_drift", "oracle_type_drift"}:
        object.__setattr__(value, "outcome", 1)
    elif scenario in {"source_invariant", "oracle_mismatch"}:
        object.__setattr__(value, "outcome", "passed")
    return value


def execute_independent_route(
    runtime: object,
    spec: Mapping[str, object],
    *,
    public_dispatch: bool = False,
) -> dict[str, object]:
    formal_module = runtime.admit015
    oracle_module = runtime.admit015_oracle
    scenario = str(spec["scenario"])
    candidate: object = {}
    stage: object = StageProbe(
        {"current_stage_training_authorized": True}
    )
    batch = evaluation = download = None
    if scenario == "batch_object":
        batch = object()
    elif scenario == "batch_mapping":
        batch = {}
    elif scenario == "evaluation_object":
        evaluation = object()
    elif scenario == "evaluation_mapping":
        evaluation = {}
    elif scenario == "download_object":
        download = object()
    elif scenario == "download_mapping":
        download = {}
    elif scenario == "all_invalid":
        batch, evaluation, download, candidate = (
            object(),
            object(),
            object(),
            object(),
        )
    elif scenario == "evaluation_download_candidate_invalid":
        evaluation, download, candidate = object(), object(), object()
    elif scenario == "download_candidate_invalid":
        download, candidate = object(), object()
    elif scenario == "candidate_invalid":
        candidate, stage = object(), StageProbe()
    elif scenario == "candidate_empty":
        stage = None
    elif scenario == "candidate_probe":
        candidate, stage = CandidateProbe(), None
    elif scenario == "stage_none":
        stage = None
    elif scenario == "stage_object":
        stage = object()
    elif scenario == "stage_empty":
        stage = StageProbe()
    elif scenario == "stage_false":
        stage = StageProbe({"current_stage_training_authorized": False})
    elif scenario == "stage_extra":
        stage = StageProbe(
            {
                "current_stage_training_authorized": True,
                "current_stage_download_authorized": True,
                "extra": 1,
            }
        )
    elif scenario == "stage_keyerror":
        stage = StageProbe(
            error=KeyError("current_stage_training_authorized")
        )
    elif scenario == "stage_runtimeerror":
        stage = StageProbe(error=RuntimeError("checker"))
    elif scenario == "stage_valueerror":
        stage = StageProbe(error=ValueError("checker"))
    elif scenario == "nonrepeatable":
        stage = StageProbe(alternating=True)
    elif scenario.startswith(("source_", "oracle_")):
        stage = None
    input_representations = _independent_input_representations(
        scenario,
        candidate,
        batch,
        evaluation,
        download,
        stage,
    )

    calls: list[str] = []
    identities: list[bool] = []
    formal_access = oracle_access = 0
    original_formal = formal_module.evaluate_admit_015
    original_oracle = (
        oracle_module
        .classify_admit_015_formal_evaluator_interface_design
    )

    def access_count() -> int:
        return stage.access_count if isinstance(stage, StageProbe) else 0

    def formal_call(*, stage_authorization_context: object) -> object:
        nonlocal formal_access
        calls.append("formal")
        identities.append(stage_authorization_context is stage)
        before = access_count()
        value = original_formal(
            stage_authorization_context=stage_authorization_context
        )
        formal_access += access_count() - before
        if scenario.startswith("source_"):
            value = _mutate_exact9(value, scenario)
        return value

    def oracle_call(*, stage_authorization_context: object) -> object:
        nonlocal oracle_access
        calls.append("oracle")
        identities.append(stage_authorization_context is stage)
        before = access_count()
        if scenario == "oracle_exception":
            raise RuntimeError("checker oracle")
        oracle_stage = object() if scenario == "oracle_mismatch" else stage
        value = original_oracle(
            stage_authorization_context=oracle_stage
        )
        oracle_access += access_count() - before
        if scenario.startswith("oracle_"):
            value = _mutate_exact9(value, scenario)
        return value

    formal_module.evaluate_admit_015 = formal_call
    (
        oracle_module
        .classify_admit_015_formal_evaluator_interface_design
    ) = oracle_call
    code = reason = result_json = ""
    try:
        try:
            if public_dispatch:
                value = runtime.evaluate_admission_rule(
                    "ADMIT_015",
                    candidate,
                    batch_context=batch,
                    evaluation_context=evaluation,
                    download_result_context=download,
                    stage_authorization_context=stage,
                )
            else:
                value = runtime._evaluate_registered_admit_015(
                    candidate,
                    batch_context=batch,
                    evaluation_context=evaluation,
                    download_result_context=download,
                    stage_authorization_context=stage,
                )
        except runtime.UnifiedAdmissionDispatchError as error:
            code = error.code
            reason = error.reason
            result_json = _exact_json(error, ERROR_FIELDS)
        else:
            reason = value.reason
            result_json = _exact_json(value, RESULT_FIELDS)
    finally:
        formal_module.evaluate_admit_015 = original_formal
        (
            oracle_module
            .classify_admit_015_formal_evaluator_interface_design
        ) = original_oracle
    candidate_access = (
        candidate.access_count if isinstance(candidate, CandidateProbe) else 0
    )
    total_access = access_count()
    return {
        "code": code,
        "reason": reason,
        "result": result_json,
        "call_order": "|".join(calls),
        "identity": "n/a" if not identities else str(all(identities)).lower(),
        "candidate_access": candidate_access,
        "adapter_access": total_access - formal_access - oracle_access,
        "formal": calls.count("formal"),
        "oracle": calls.count("oracle"),
        "formal_access": formal_access,
        "oracle_access": oracle_access,
        "input_representations": input_representations,
    }


def verify_exact42(runtime: object) -> tuple[dict[str, object], ...]:
    observations = []
    specs = _independent_specs()
    _verify_exact42_committed_continuity(specs)
    for spec in specs:
        actual = execute_independent_route(runtime, spec)
        expected_order = (
            "formal|oracle"
            if spec["oracle"] == 1
            else "formal"
            if spec["formal"] == 1
            else ""
        )
        if (
            actual["code"] != spec["code"]
            or actual["reason"] != spec["reason"]
            or actual["result"] != spec["result"]
            or actual["call_order"] != expected_order
            or actual["formal"] != spec["formal"]
            or actual["oracle"] != spec["oracle"]
            or actual["formal_access"] != spec["formal_access"]
            or actual["oracle_access"] != spec["oracle_access"]
            or actual["identity"] != spec["identity"]
            or actual["candidate_access"] != 0
            or actual["adapter_access"] != 0
            or actual["input_representations"]
            != spec["input_representations"]
        ):
            raise AssertionError(
                f"independent Exact42 failure: {spec['case_id']}"
            )
        observations.append(actual)
    return tuple(observations)


def _expect_failure(
    runtime: object,
    *,
    expected_reason: str,
    candidate: object,
    stage: object = None,
) -> dict[str, str]:
    try:
        runtime._evaluate_registered_admit_015(
            candidate,
            batch_context=None,
            evaluation_context=None,
            download_result_context=None,
            stage_authorization_context=stage,
        )
    except runtime.UnifiedAdmissionDispatchError as error:
        if (
            error.code != "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
            or error.reason != expected_reason
            or (
                error.known_rule,
                error.callable_discovered,
                error.adapter_ready,
            )
            != (True, True, False)
        ):
            raise AssertionError("adapter failure mapping drift")
        return {
            "code": error.code,
            "reason": error.reason,
            "result": _exact_json(error, ERROR_FIELDS),
        }
    else:
        raise AssertionError("expected adapter failure")


def _negative_contract_observations(
    runtime: object,
) -> tuple[tuple[dict[str, object], ...], tuple[dict[str, object], ...]]:
    formal_module = runtime.admit015
    oracle_module = runtime.admit015_oracle
    original_formal = formal_module.evaluate_admit_015
    original_oracle = (
        oracle_module
        .classify_admit_015_formal_evaluator_interface_design
    )
    source_modes = (
        "wrong_type",
        "subclass",
        "storage_reorder",
        "top_level_type",
        "rule_id",
        "io_true",
        "outcome_reason",
        "canonical",
        "validated",
        "consumed",
        "exception",
    )
    source_observations = []
    for mode in source_modes:
        calls = {"formal": 0, "oracle": 0}
        identities: list[bool] = []
        candidate: object = {}

        def formal_call(
            *,
            stage_authorization_context: object,
            mode: str = mode,
        ) -> object:
            calls["formal"] += 1
            identities.append(stage_authorization_context is None)
            if mode == "exception":
                raise RuntimeError("checker formal")
            if mode == "wrong_type":
                return object()
            value = original_formal(stage_authorization_context=None)
            if mode == "subclass":
                return _mutate_exact9(value, "source_subclass")
            if mode == "storage_reorder":
                return _mutate_exact9(value, "source_storage")
            if mode == "top_level_type":
                object.__setattr__(value, "outcome", 1)
            elif mode == "rule_id":
                object.__setattr__(value, "admission_rule_id", "ADMIT_014")
            elif mode == "io_true":
                object.__setattr__(value, "evaluator_io_used", True)
            elif mode == "outcome_reason":
                object.__setattr__(value, "outcome", "passed")
            elif mode == "canonical":
                object.__setattr__(
                    value,
                    "canonical_stage_authorization_record",
                    (("unexpected", True),),
                )
            elif mode == "validated":
                object.__setattr__(
                    value,
                    "validated_stage_authorization_fields",
                    (1,),
                )
            elif mode == "consumed":
                object.__setattr__(
                    value,
                    "consumed_stage_authorization_fields",
                    (1,),
                )
            return value

        def oracle_call(
            *,
            stage_authorization_context: object,
        ) -> object:
            calls["oracle"] += 1
            identities.append(stage_authorization_context is None)
            return original_oracle(
                stage_authorization_context=stage_authorization_context
            )

        formal_module.evaluate_admit_015 = formal_call
        (
            oracle_module
            .classify_admit_015_formal_evaluator_interface_design
        ) = oracle_call
        try:
            failure = _expect_failure(
                runtime,
                expected_reason=(
                    "ADMIT_015_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
                    if mode in {"wrong_type", "subclass"}
                    else "ADMIT_015_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
                ),
                candidate=candidate,
            )
        finally:
            formal_module.evaluate_admit_015 = original_formal
            (
                oracle_module
                .classify_admit_015_formal_evaluator_interface_design
            ) = original_oracle
        if calls != {"formal": 1, "oracle": 0}:
            raise AssertionError("source prevalidation order drift")
        source_observations.append(
            {
                "mode": mode,
                **failure,
                "call_order": "formal",
                "identity": str(all(identities)).lower(),
                "formal": calls["formal"],
                "oracle": calls["oracle"],
                "candidate_access": 0,
                "adapter_access": 0,
                "formal_access": 0,
                "oracle_access": 0,
                "input_representations": (
                    _independent_input_representations(
                        f"source_negative_{mode}",
                        candidate,
                        None,
                        None,
                        None,
                        None,
                    )
                ),
            }
        )

    oracle_modes = (
        "wrong_type",
        "subclass",
        "storage_reorder",
        "top_level_type",
        "rule_id",
        "value_mismatch",
        "exception",
        "stateful_mapping",
    )
    oracle_observations = []
    for mode in oracle_modes:
        calls = {"formal": 0, "oracle": 0}
        candidate = {}
        stage: object = (
            StageProbe(alternating=True)
            if mode == "stateful_mapping"
            else None
        )
        identities: list[bool] = []
        formal_access = oracle_access = 0

        def access_count() -> int:
            return (
                stage.access_count
                if isinstance(stage, StageProbe)
                else 0
            )

        def formal_call(
            *,
            stage_authorization_context: object,
        ) -> object:
            nonlocal formal_access
            calls["formal"] += 1
            identities.append(stage_authorization_context is stage)
            before = access_count()
            value = original_formal(
                stage_authorization_context=stage_authorization_context
            )
            formal_access += access_count() - before
            return value

        def oracle_call(
            *,
            stage_authorization_context: object,
            mode: str = mode,
        ) -> object:
            nonlocal oracle_access
            calls["oracle"] += 1
            identities.append(stage_authorization_context is stage)
            before = access_count()
            if mode == "exception":
                raise RuntimeError("checker oracle")
            if mode == "wrong_type":
                return object()
            value = original_oracle(
                stage_authorization_context=(
                    object()
                    if mode == "value_mismatch"
                    else stage_authorization_context
                )
            )
            if mode == "subclass":
                return _mutate_exact9(value, "oracle_subclass")
            if mode == "storage_reorder":
                return _mutate_exact9(value, "oracle_storage")
            if mode == "top_level_type":
                object.__setattr__(value, "outcome", 1)
            elif mode == "rule_id":
                object.__setattr__(value, "admission_rule_id", "ADMIT_014")
            oracle_access += access_count() - before
            return value

        formal_module.evaluate_admit_015 = formal_call
        (
            oracle_module
            .classify_admit_015_formal_evaluator_interface_design
        ) = oracle_call
        try:
            failure = _expect_failure(
                runtime,
                expected_reason=(
                    "ADMIT_015_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
                ),
                candidate=candidate,
                stage=stage,
            )
        finally:
            formal_module.evaluate_admit_015 = original_formal
            (
                oracle_module
                .classify_admit_015_formal_evaluator_interface_design
            ) = original_oracle
        if calls != {"formal": 1, "oracle": 1}:
            raise AssertionError("oracle negative call count drift")
        oracle_observations.append(
            {
                "mode": mode,
                **failure,
                "call_order": "formal|oracle",
                "identity": str(all(identities)).lower(),
                "formal": calls["formal"],
                "oracle": calls["oracle"],
                "candidate_access": 0,
                "adapter_access": 0,
                "formal_access": formal_access,
                "oracle_access": oracle_access,
                "input_representations": (
                    _independent_input_representations(
                        f"oracle_negative_{mode}",
                        candidate,
                        None,
                        None,
                        None,
                        stage,
                    )
                ),
            }
        )
    return tuple(source_observations), tuple(oracle_observations)


def verify_negative_contracts(runtime: object) -> tuple[int, int]:
    source, oracle = _negative_contract_observations(runtime)
    return len(source), len(oracle)


def verify_runtime(runtime: object) -> dict[str, Any]:
    predecessor = runtime.predecessor
    shared = (
        "UnifiedAdmissionRuleEvaluation",
        "UnifiedAdmissionDispatchError",
        "RESULT_SCHEMA_VERSION",
        "RESULT_FIELDS",
        "DISPATCH_ERROR_FIELDS",
        "DISPATCH_ERROR_CODES",
        "OUTCOME_VOCABULARY",
    )
    if any(
        getattr(runtime, name) is not getattr(predecessor, name)
        for name in shared
    ):
        raise AssertionError("shared predecessor identity drift")
    predecessor_registered = tuple(
        f"ADMIT_{index:03d}" for index in range(1, 15)
    )
    registered = (*predecessor_registered, "ADMIT_015")
    expected_handler_signature = (
        "(candidate_record: 'object', *, batch_context: 'object', "
        "evaluation_context: 'object', "
        "download_result_context: 'object', "
        "stage_authorization_context: 'object') -> "
        "'UnifiedAdmissionRuleEvaluation'"
    )
    if (
        runtime.evaluate_admission_rule
        is predecessor.evaluate_admission_rule
        or inspect.signature(runtime.evaluate_admission_rule)
        != inspect.signature(predecessor.evaluate_admission_rule)
        or str(inspect.signature(runtime._evaluate_registered_admit_015))
        != expected_handler_signature
        or type(runtime.EVALUATOR_REGISTRY) is not MappingProxyType
        or tuple(runtime.EVALUATOR_REGISTRY) != registered
        or tuple(runtime.KNOWN_RULE_IDS) != registered
        or tuple(runtime.CALLABLE_DISCOVERED_RULE_IDS) != registered
        or tuple(runtime.ADAPTER_READY_RULE_IDS) != registered
        or tuple(runtime.LEGACY_ADAPTER_NOT_READY_RULE_IDS) != ()
        or any(
            runtime.EVALUATOR_REGISTRY[rule_id]
            is not predecessor.EVALUATOR_REGISTRY[rule_id]
            for rule_id in predecessor_registered
        )
        or runtime.EVALUATOR_REGISTRY["ADMIT_015"]
        is not runtime._evaluate_registered_admit_015
        or "ADMIT_015" not in runtime.EVALUATOR_REGISTRY
        or type(runtime.RULE_NAMES) is not MappingProxyType
        or type(runtime.ADAPTER_IDS) is not MappingProxyType
        or tuple(runtime.RULE_NAMES) != registered
        or tuple(runtime.ADAPTER_IDS) != registered
    ):
        raise AssertionError("registry/signature/runtime identity drift")
    class RuleIdSubclass(str):
        pass

    for rule_id, code in (
        (True, "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID"),
        (
            RuleIdSubclass("ADMIT_015"),
            "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID",
        ),
        ("ADMIT_999", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN"),
    ):
        try:
            runtime.evaluate_admission_rule(rule_id, {})
        except runtime.UnifiedAdmissionDispatchError as error:
            if error.code != code:
                raise AssertionError("dispatcher precedence drift")
        else:
            raise AssertionError("dispatcher error missing")
    for rule_id in predecessor_registered:
        try:
            expected_value = predecessor.evaluate_admission_rule(
                rule_id, {}
            )
        except runtime.UnifiedAdmissionDispatchError as error:
            expected_kind = "error"
            expected_json = _exact_json(error, ERROR_FIELDS)
        else:
            expected_kind = "result"
            expected_json = _exact_json(expected_value, RESULT_FIELDS)
        try:
            observed_value = runtime.evaluate_admission_rule(rule_id, {})
        except runtime.UnifiedAdmissionDispatchError as error:
            observed_kind = "error"
            observed_json = _exact_json(error, ERROR_FIELDS)
        else:
            observed_kind = "result"
            observed_json = _exact_json(observed_value, RESULT_FIELDS)
        if (observed_kind, observed_json) != (
            expected_kind,
            expected_json,
        ):
            raise AssertionError("predecessor representative drift")
    result = runtime.evaluate_admission_rule(
        "ADMIT_015",
        CandidateProbe(),
        stage_authorization_context={
            "current_stage_training_authorized": True
        },
    )
    if (
        result.outcome != "passed"
        or result.normalized_values
        != (("current_stage_training_authorized", "true"),)
        or result.validated_candidate_fields != ()
        or result.consumed_candidate_fields != ()
        or result.consumed_context_items
        != ("current_stage_training_authorized",)
    ):
        raise AssertionError("ADMIT_015 projection drift")
    exact42 = verify_exact42(runtime)
    source_count, oracle_count = verify_negative_contracts(runtime)
    if (
        hasattr(runtime, "evaluate_all_rules")
        or hasattr(runtime, "combined_candidate_verdict")
        or runtime.evaluate_admission_rule.__globals__["EVALUATOR_REGISTRY"]
        is not runtime.EVALUATOR_REGISTRY
    ):
        raise AssertionError("single-rule/local registry boundary drift")
    return {
        "exact42_count": len(exact42),
        "source_negative_count": source_count,
        "oracle_negative_count": oracle_count,
    }


def _canonical_json(value: str) -> str:
    return json.dumps(
        json.loads(value),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )


def _expected_contract_rows() -> list[dict[str, str]]:
    definitions = (
        ("identity", "shared Exact13 result", "object_identity_preserved"),
        ("identity", "shared dispatch error", "object_identity_preserved"),
        ("identity", "shared constants", "5/5_identity_preserved"),
        ("dispatcher", "signature", "exact_predecessor_match"),
        ("dispatcher", "precedence", "exact_str|known|callable|ready|local_handler"),
        ("dispatcher", "cardinality", "single_rule_only"),
        ("registry", "order", "ADMIT_001_to_ADMIT_015"),
        ("registry", "first fourteen handlers", "14/14_identity_preserved"),
        ("registry", "ADMIT_015 handler", "_evaluate_registered_admit_015"),
        ("registry", "immutability", "MappingProxyType"),
        ("sets", "known", "ADMIT_001_to_ADMIT_015"),
        ("sets", "callable", "ADMIT_001_to_ADMIT_015"),
        ("sets", "adapter ready", "ADMIT_001_to_ADMIT_015"),
        ("sets", "legacy adapter not ready", "empty"),
        ("routing", "precedence", "batch|evaluation|download|candidate|stage_forward|formal|source|oracle|equality|projection"),
        ("candidate", "non-Mapping", "fixed_invalid_Exact13"),
        ("candidate", "key access", "zero"),
        ("source", "Exact9", "type|storage|order|types|reconstruction|invariants"),
        ("source", "validation before oracle", "true"),
        ("oracle", "call count", "exactly_once_after_valid_source"),
        ("oracle", "same stage object", "identity_preserved"),
        ("equality", "Exact9", "exact_type_and_value_all_fields"),
        ("projection", "normalized", "exact_bool_to_lowercase_string"),
        ("projection", "validated candidate", "empty"),
        ("projection", "consumed candidate", "empty"),
        ("projection", "consumed context", "source_consumed_stage_fields"),
        ("truth", "inherited routing", "Exact42_actual_runtime_execution"),
        ("truth", "source negatives", "Exact11_actual_fail_closed"),
        ("truth", "oracle negatives", "Exact8_actual_fail_closed"),
        ("continuity", "predecessor truth", "committed_Exact79_all_passed"),
        ("continuity", "predecessor registry", "committed_Exact27_all_passed"),
        ("issue", "single transition", "coverage_resolved_after_ADMIT_015"),
        ("precondition", "PRE_032 and PRE_033", "resolved"),
        ("precondition", "counts", "total=45|complete=40|supported=0|incomplete=5|blocking=5"),
        ("readiness", "current permission", "false"),
        ("readiness", "authorized execution count", "0"),
        ("runtime", "Exact15", "implemented"),
        ("boundary", "mandatory enforcement", "not_implemented"),
        ("boundary", "combined verdict and aggregation", "not_implemented"),
        ("boundary", "provider network download raw", "not_executed"),
        ("boundary", "model checkpoint dataloader training", "not_modified"),
        ("training", "feature semantics audit", "required_Step12D_smoke_only"),
        ("materializer", "publication", "set_atomic_RENAME_NOREPLACE"),
        ("materializer", "failure staging", "authenticated_retention_no_delete"),
        ("materializer", "existing exact set and EINVAL", "inode_noop_and_fail_closed"),
    )
    return [
        {
            "contract_order": str(index),
            "contract_group": group,
            "contract_item": item,
            "expected_value": value,
            "observed_value": value,
            "contract_passed": "true",
        }
        for index, (group, item, value) in enumerate(definitions, 1)
    ]


def _expected_registry_rows(runtime: object) -> list[dict[str, str]]:
    rows = []
    known = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
    for index, rule_id in enumerate(known, 1):
        if rule_id in known[:14]:
            expected_identity = (
                f"predecessor.EVALUATOR_REGISTRY[{rule_id!r}]"
            )
            observed_identity = expected_identity
            identity = (
                runtime.EVALUATOR_REGISTRY[rule_id]
                is runtime.predecessor.EVALUATOR_REGISTRY[rule_id]
            )
        elif rule_id == "ADMIT_015":
            expected_identity = "_evaluate_registered_admit_015"
            observed_identity = getattr(
                runtime.EVALUATOR_REGISTRY.get(rule_id),
                "__name__",
                "",
            )
            identity = (
                runtime.EVALUATOR_REGISTRY[rule_id]
                is runtime._evaluate_registered_admit_015
            )
        else:
            expected_identity = observed_identity = "not_registered"
            identity = rule_id not in runtime.EVALUATOR_REGISTRY
        registered = rule_id in runtime.EVALUATOR_REGISTRY
        callable_discovered = (
            rule_id in runtime.CALLABLE_DISCOVERED_RULE_IDS
        )
        adapter_ready = rule_id in runtime.ADAPTER_READY_RULE_IDS
        expected = True
        passed = (
            identity
            and registered is expected
            and callable_discovered is expected
            and adapter_ready is expected
        )
        rows.append(
            {
                "audit_order": str(index),
                "rule_id": rule_id,
                "expected_handler_identity": expected_identity,
                "observed_handler_identity": observed_identity,
                "identity_preserved": str(identity).lower(),
                "registered": str(registered).lower(),
                "callable_discovered": str(callable_discovered).lower(),
                "adapter_ready": str(adapter_ready).lower(),
                "audit_passed": str(passed).lower(),
            }
        )
    shared = (
        "UnifiedAdmissionRuleEvaluation",
        "UnifiedAdmissionDispatchError",
        "RESULT_SCHEMA_VERSION",
        "RESULT_FIELDS",
        "DISPATCH_ERROR_FIELDS",
        "DISPATCH_ERROR_CODES",
        "OUTCOME_VOCABULARY",
    )
    for name in shared:
        preserved = (
            getattr(runtime, name) is getattr(runtime.predecessor, name)
        )
        rows.append(
            {
                "audit_order": str(len(rows) + 1),
                "rule_id": f"SHARED:{name}",
                "expected_handler_identity": "predecessor_exact_object",
                "observed_handler_identity": "predecessor_exact_object",
                "identity_preserved": str(preserved).lower(),
                "registered": "n/a",
                "callable_discovered": "n/a",
                "adapter_ready": "n/a",
                "audit_passed": str(preserved).lower(),
            }
        )
    metadata = (
        (
            "DISPATCHER:signature",
            inspect.signature(runtime.evaluate_admission_rule)
            == inspect.signature(
                runtime.predecessor.evaluate_admission_rule
            ),
        ),
        (
            "DISPATCHER:local_registry",
            runtime.evaluate_admission_rule.__globals__[
                "EVALUATOR_REGISTRY"
            ]
            is runtime.EVALUATOR_REGISTRY,
        ),
        (
            "REGISTRY:mapping_proxy",
            type(runtime.EVALUATOR_REGISTRY) is MappingProxyType,
        ),
        (
            "RULE_NAMES:mapping_proxy",
            type(runtime.RULE_NAMES) is MappingProxyType,
        ),
        (
            "ADAPTER_IDS:mapping_proxy",
            type(runtime.ADAPTER_IDS) is MappingProxyType,
        ),
    )
    for item, passed in metadata:
        rows.append(
            {
                "audit_order": str(len(rows) + 1),
                "rule_id": item,
                "expected_handler_identity": "true",
                "observed_handler_identity": str(passed).lower(),
                "identity_preserved": str(passed).lower(),
                "registered": "n/a",
                "callable_discovered": "n/a",
                "adapter_ready": "n/a",
                "audit_passed": str(passed).lower(),
            }
        )
    return rows


def _expected_safety_rows() -> list[dict[str, str]]:
    states = (
        ("production_successor_runtime_implemented", True),
        ("shared_exact13_identity_preserved", True),
        ("first_fourteen_handler_identity_preserved", True),
        ("admit_015_handler_implemented", True),
        ("successor_local_exact15_registry_changed", True),
        ("predecessor_files_modified", False),
        ("formal_exactly_once_after_routing", True),
        ("oracle_exactly_once_after_source", True),
        ("source_exact9_attested", True),
        ("oracle_exact9_attested", True),
        ("full_exact9_equivalence_required", True),
        ("bool_lowercase_projection", True),
        ("candidate_key_access_zero", True),
        ("adapter_stage_key_access_zero", True),
        ("pre_032_resolved", True),
        ("pre_033_resolved", True),
        ("mandatory_enforcement_implemented", False),
        ("combined_verdict_implemented", False),
        ("cross_rule_aggregation_implemented", False),
        ("provider_mapping_implemented", False),
        ("network_executed", False),
        ("download_executed", False),
        ("raw_accessed", False),
        ("dataloader_modified", False),
        ("model_modified", False),
        ("checkpoint_modified", False),
        ("training_executed", False),
        ("current_permission", False),
        ("authorized_execution_count_nonzero", False),
        ("current_main_staged", False),
        ("current_main_committed_or_pushed", False),
        ("feature_semantics_audit_completed", False),
    )
    return [
        {
            "audit_order": str(index),
            "audit_item": item,
            "expected_state": str(state).lower(),
            "observed_state": str(state).lower(),
            "safety_passed": "true",
        }
        for index, (item, state) in enumerate(states, 1)
    ]


def _expected_issue_rows() -> list[dict[str, str]]:
    predecessor = _csv_rows(
        pinned_read(ROOT, Path(SOURCE_BOUNDARY[12][0])),
        ISSUE_HEADER,
    )
    rows = [dict(row) for row in predecessor]
    matches = [
        row
        for row in rows
        if row["issue_id"]
        == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
    ]
    if len(rows) != 30 or len(matches) != 1:
        raise AssertionError("committed issue Exact30 drift")
    coverage = matches[0]
    if (
        coverage["affected_rules"] != "ADMIT_015"
        or coverage["successor_effective_status"] != "open"
    ):
        raise AssertionError("committed issue transition source drift")
    coverage.update(
        {
            "affected_rules": "",
            "integration_transition": (
                "unified_dispatch_runtime_with_admit_001_to_015_"
                "implemented_v1"
            ),
            "successor_effective_status": "resolved",
            "successor_transition_stage": STAGE_NAME,
            "successor_transition_action": (
                "admit_015_removed_from_open_unified_runtime_coverage"
            ),
            "successor_transition_evidence": (
                "Exact15_registry_and_unified_single_rule_dispatch"
            ),
        }
    )
    return rows


def _truth_row(
    *,
    case_order: int,
    case_id: str,
    case_group: str,
    expected_kind: str,
    observed_kind: str,
    expected_json: str,
    observed_json: str,
    expected_call_order: str = "",
    observed_call_order: str = "",
    expected_identity: str = "n/a",
    observed_identity: str = "n/a",
    formal: int = 0,
    oracle: int = 0,
    candidate_access: int = 0,
    adapter_access: int = 0,
    formal_access: int = 0,
    oracle_access: int = 0,
    candidate: str = "{}",
    batch: str = "None",
    evaluation: str = "None",
    download: str = "None",
    stage: str = "None",
) -> dict[str, str]:
    total_access = adapter_access + formal_access + oracle_access
    return {
        "case_order": str(case_order),
        "case_id": case_id,
        "case_group": case_group,
        "admission_rule_id": "ADMIT_015",
        "candidate_representation": candidate,
        "batch_context_representation": batch,
        "evaluation_context_representation": evaluation,
        "download_result_context_representation": download,
        "stage_authorization_context_representation": stage,
        "expected_outcome_or_error": expected_kind,
        "observed_outcome_or_error": observed_kind,
        "expected_result_json": _canonical_json(expected_json),
        "observed_result_json": _canonical_json(observed_json),
        "expected_call_order": expected_call_order,
        "observed_call_order": observed_call_order,
        "expected_stage_context_identity_preserved": expected_identity,
        "observed_stage_context_identity_preserved": observed_identity,
        "formal_call_count": str(formal),
        "oracle_call_count": str(oracle),
        "candidate_key_access_count": str(candidate_access),
        "adapter_stage_target_access_count": str(adapter_access),
        "formal_stage_target_access_count": str(formal_access),
        "oracle_stage_target_access_count": str(oracle_access),
        "stage_target_access_count": str(total_access),
        "case_passed": "true",
    }


def _observe_public(
    module: object,
    rule_id: object,
) -> tuple[str, str]:
    try:
        value = module.evaluate_admission_rule(rule_id, {})
    except module.UnifiedAdmissionDispatchError as error:
        return error.code, _exact_json(error, ERROR_FIELDS)
    return value.outcome, _exact_json(value, RESULT_FIELDS)


def _expected_truth_rows(runtime: object) -> list[dict[str, str]]:
    specs = _independent_specs()
    observations = verify_exact42(runtime)
    rows = []
    for order, (spec, actual) in enumerate(
        zip(specs, observations, strict=True),
        1,
    ):
        expected_kind = (
            str(spec["code"])
            if spec["code"]
            else str(json.loads(str(spec["result"]))["outcome"])
        )
        observed_kind = (
            str(actual["code"])
            if actual["code"]
            else str(json.loads(str(actual["result"]))["outcome"])
        )
        expected_call_order = (
            "formal|oracle"
            if spec["oracle"] == 1
            else "formal"
            if spec["formal"] == 1
            else ""
        )
        rows.append(
            _truth_row(
                case_order=order,
                case_id=str(spec["case_id"]),
                case_group="admit015_inherited_exact42_runtime",
                expected_kind=expected_kind,
                observed_kind=observed_kind,
                expected_json=str(spec["result"]),
                observed_json=str(actual["result"]),
                expected_call_order=expected_call_order,
                observed_call_order=str(actual["call_order"]),
                expected_identity=str(spec["identity"]),
                observed_identity=str(actual["identity"]),
                formal=int(actual["formal"]),
                oracle=int(actual["oracle"]),
                candidate_access=int(actual["candidate_access"]),
                adapter_access=int(actual["adapter_access"]),
                formal_access=int(actual["formal_access"]),
                oracle_access=int(actual["oracle_access"]),
                candidate=str(actual["input_representations"][0]),
                batch=str(actual["input_representations"][1]),
                evaluation=str(actual["input_representations"][2]),
                download=str(actual["input_representations"][3]),
                stage=str(actual["input_representations"][4]),
            )
        )
    source, oracle = _negative_contract_observations(runtime)
    for actual in source:
        mode = str(actual["mode"])
        reason = (
            SOURCE_TYPE_ERROR
            if mode in {"wrong_type", "subclass"}
            else SOURCE_INVARIANT_ERROR
        )
        expected_json = _expected_error_json(
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            reason,
            False,
        )
        rows.append(
            _truth_row(
                case_order=len(rows) + 1,
                case_id=f"SOURCE_NEGATIVE_{mode}",
                case_group="admit015_source_negative",
                expected_kind=(
                    "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
                ),
                observed_kind=str(actual["code"]),
                expected_json=expected_json,
                observed_json=str(actual["result"]),
                expected_call_order="formal",
                observed_call_order=str(actual["call_order"]),
                expected_identity="true",
                observed_identity=str(actual["identity"]),
                formal=int(actual["formal"]),
                oracle=int(actual["oracle"]),
                candidate_access=int(actual["candidate_access"]),
                adapter_access=int(actual["adapter_access"]),
                formal_access=int(actual["formal_access"]),
                oracle_access=int(actual["oracle_access"]),
                candidate=str(actual["input_representations"][0]),
                batch=str(actual["input_representations"][1]),
                evaluation=str(actual["input_representations"][2]),
                download=str(actual["input_representations"][3]),
                stage=str(actual["input_representations"][4]),
            )
        )
    for actual in oracle:
        mode = str(actual["mode"])
        expected_json = _expected_error_json(
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
            SOURCE_INVARIANT_ERROR,
            False,
        )
        rows.append(
            _truth_row(
                case_order=len(rows) + 1,
                case_id=f"ORACLE_NEGATIVE_{mode}",
                case_group="admit015_oracle_negative",
                expected_kind=(
                    "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
                ),
                observed_kind=str(actual["code"]),
                expected_json=expected_json,
                observed_json=str(actual["result"]),
                expected_call_order="formal|oracle",
                observed_call_order=str(actual["call_order"]),
                expected_identity="true",
                observed_identity=str(actual["identity"]),
                formal=int(actual["formal"]),
                oracle=int(actual["oracle"]),
                candidate_access=int(actual["candidate_access"]),
                adapter_access=int(actual["adapter_access"]),
                formal_access=int(actual["formal_access"]),
                oracle_access=int(actual["oracle_access"]),
                candidate=str(actual["input_representations"][0]),
                batch=str(actual["input_representations"][1]),
                evaluation=str(actual["input_representations"][2]),
                download=str(actual["input_representations"][3]),
                stage=str(actual["input_representations"][4]),
            )
        )
    public_definitions = (
        ("bool", True, "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", "", False, False, False),
        ("str_subclass", type("_RuleIdSubclass", (str,), {})("ADMIT_015"), "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", "", False, False, False),
        ("unknown", "ADMIT_999", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN", "ADMIT_999", False, False, False),
    )
    for name, rule_id, code, error_rule_id, known, callable_, ready in (
        public_definitions
    ):
        observed_kind, observed_json = _observe_public(runtime, rule_id)
        expected_json = json.dumps(
            {
                "code": code,
                "admission_rule_id": error_rule_id,
                "known_rule": known,
                "callable_discovered": callable_,
                "adapter_ready": ready,
                "reason": code,
            },
            ensure_ascii=True,
            separators=(",", ":"),
        )
        rows.append(
            _truth_row(
                case_order=len(rows) + 1,
                case_id=f"DISPATCH_{name}",
                case_group="public_dispatch",
                expected_kind=code,
                observed_kind=observed_kind,
                expected_json=expected_json,
                observed_json=observed_json,
            )
        )
    stage_spec = next(
        spec for spec in specs if spec["case_id"] == "stage_true"
    )
    actual = execute_independent_route(
        runtime,
        stage_spec,
        public_dispatch=True,
    )
    rows.append(
        _truth_row(
            case_order=len(rows) + 1,
            case_id="DISPATCH_admit015_registered",
            case_group="public_dispatch",
            expected_kind="passed",
            observed_kind=str(
                json.loads(str(actual["result"]))["outcome"]
            ),
            expected_json=str(stage_spec["result"]),
            observed_json=str(actual["result"]),
            expected_call_order="formal|oracle",
            observed_call_order=str(actual["call_order"]),
            expected_identity="true",
            observed_identity=str(actual["identity"]),
            formal=int(actual["formal"]),
            oracle=int(actual["oracle"]),
            candidate_access=int(actual["candidate_access"]),
            adapter_access=int(actual["adapter_access"]),
            formal_access=int(actual["formal_access"]),
            oracle_access=int(actual["oracle_access"]),
            candidate=str(actual["input_representations"][0]),
            batch=str(actual["input_representations"][1]),
            evaluation=str(actual["input_representations"][2]),
            download=str(actual["input_representations"][3]),
            stage=str(actual["input_representations"][4]),
        )
    )
    for rule_id in tuple(
        f"ADMIT_{index:03d}" for index in range(1, 15)
    ):
        expected_kind, expected_json = _observe_public(
            runtime.predecessor,
            rule_id,
        )
        observed_kind, observed_json = _observe_public(runtime, rule_id)
        rows.append(
            _truth_row(
                case_order=len(rows) + 1,
                case_id=f"PREDECESSOR_{rule_id}",
                case_group="predecessor_representative_dispatch",
                expected_kind=expected_kind,
                observed_kind=observed_kind,
                expected_json=expected_json,
                observed_json=observed_json,
            )
        )
    if len(rows) != 79:
        raise AssertionError("independent truth is not Exact79")
    return rows


def _assert_truth_input_representation_matrix(
    truth: Sequence[Mapping[str, str]],
) -> None:
    specs = _independent_specs()
    inherited = truth[:42]
    if (
        len(truth) != 79
        or tuple(row["case_id"] for row in inherited)
        != tuple(str(spec["case_id"]) for spec in specs)
        or any(
            tuple(
                row[name]
                for name in TRUTH_INPUT_REPRESENTATION_COLUMNS
            )
            != spec["input_representations"]
            for row, spec in zip(inherited, specs, strict=True)
        )
    ):
        raise AssertionError("Truth Exact42 input representations drift")
    if (
        {
            row["batch_context_representation"]
            for row in inherited
        }
        != {"None", "object", "{}"}
        or {
            row["evaluation_context_representation"]
            for row in inherited
        }
        != {"None", "object", "{}"}
        or {
            row["download_result_context_representation"]
            for row in inherited
        }
        != {"None", "object", "{}"}
        or any(
            row["candidate_representation"]
            not in {"{}", "object", "instrumented_mapping"}
            or row["batch_context_representation"]
            not in {"None", "object", "{}"}
            or row["evaluation_context_representation"]
            not in {"None", "object", "{}"}
            or row["download_result_context_representation"]
            not in {"None", "object", "{}"}
            or row["stage_authorization_context_representation"]
            not in {
                "None",
                "object",
                "{}",
                "{target:False}",
                "{target:True}",
                "{target:True,download:True,extra:1}",
                "KeyError_mapping",
                "RuntimeError_mapping",
                "ValueError_mapping",
                "alternating_mapping",
            }
            for row in truth
        )
        or tuple(
            truth[60][name]
            for name in TRUTH_INPUT_REPRESENTATION_COLUMNS
        )
        != ("{}", "None", "None", "None", "alternating_mapping")
    ):
        raise AssertionError("Truth input representation envelope leakage")


def verify_artifacts(
    payloads: Mapping[str, bytes],
    source_records: Sequence[Mapping[str, Any]],
    runtime: object,
) -> dict[str, Any]:
    if tuple(payloads) != OUTPUTS:
        raise AssertionError("Exact6 order drift")
    hashes = {name: _sha(payloads[name]) for name in OUTPUTS}
    if hashes != EXPECTED_OUTPUT_SHA256:
        raise AssertionError("Exact6 synchronized tamper or SHA drift")
    contract = _csv_rows(payloads[OUTPUTS[0]], CONTRACT_HEADER)
    truth = _csv_rows(payloads[OUTPUTS[1]], TRUTH_HEADER)
    registry = _csv_rows(payloads[OUTPUTS[2]], REGISTRY_HEADER)
    safety = _csv_rows(payloads[OUTPUTS[3]], SAFETY_HEADER)
    issues = _csv_rows(payloads[OUTPUTS[4]], ISSUE_HEADER)
    expected_contract = _expected_contract_rows()
    expected_truth = _expected_truth_rows(runtime)
    expected_registry = _expected_registry_rows(runtime)
    expected_safety = _expected_safety_rows()
    expected_issues = _expected_issue_rows()
    _assert_truth_input_representation_matrix(truth)
    if (
        [len(contract), len(truth), len(registry), len(safety), len(issues)]
        != [45, 79, 27, 32, 30]
        or any(
            row["contract_order"] != str(index)
            or row["contract_passed"] != "true"
            for index, row in enumerate(contract, 1)
        )
        or any(
            row["case_order"] != str(index)
            or row["case_passed"] != "true"
            for index, row in enumerate(truth, 1)
        )
        or any(
            row["audit_order"] != str(index)
            or row["audit_passed"] != "true"
            for index, row in enumerate(registry, 1)
        )
        or any(
            row["audit_order"] != str(index)
            or row["safety_passed"] != "true"
            for index, row in enumerate(safety, 1)
        )
        or Counter(row["case_group"] for row in truth)
        != {
            "admit015_inherited_exact42_runtime": 42,
            "admit015_source_negative": 11,
            "admit015_oracle_negative": 8,
            "public_dispatch": 4,
            "predecessor_representative_dispatch": 14,
        }
    ):
        raise AssertionError("Exact6 rows/order/pass drift")
    if contract != expected_contract:
        raise AssertionError("Contract Exact45 semantic drift")
    if truth != expected_truth:
        raise AssertionError("Truth Exact79 semantic/runtime drift")
    if registry != expected_registry:
        raise AssertionError("Registry Exact27 semantic drift")
    if safety != expected_safety:
        raise AssertionError("Safety Exact32 semantic drift")
    if issues != expected_issues:
        raise AssertionError("Issue Exact30 semantic drift")
    specs = _independent_specs()
    inherited = truth[:42]
    if tuple(row["case_id"] for row in inherited) != tuple(
        str(spec["case_id"]) for spec in specs
    ):
        raise AssertionError("artifact Exact42 identity drift")
    issue_map = {row["issue_id"]: row for row in issues}
    coverage = issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]
    if (
        coverage["affected_rules"] != ""
        or coverage["successor_effective_status"] != "resolved"
        or coverage["successor_transition_stage"] != STAGE_NAME
        or coverage["successor_transition_action"]
        != "admit_015_removed_from_open_unified_runtime_coverage"
        or coverage["successor_transition_evidence"]
        != "Exact15_registry_and_unified_single_rule_dispatch"
    ):
        raise AssertionError("coverage transition drift")
    manifest = _manifest(payloads[OUTPUTS[5]])
    expected_manifest = _expected_manifest(
        source_records=source_records,
        runtime=runtime,
        candidate_attestation=attest_candidate(),
        exact5_hashes={name: hashes[name] for name in OUTPUTS[:5]},
    )
    _assert_exact_object(manifest, expected_manifest, "$")
    if manifest != expected_manifest:
        raise AssertionError("manifest full recursive semantic drift")
    expected_readiness = {
        **{name: True for name in TRUE_READINESS},
        **{name: False for name in FALSE_READINESS},
    }
    required = {
        "project": "CovaPIE",
        "stage": STAGE_NAME,
        "expected_base_commit": BASE,
        "expected_base_parent": BASE_PARENT,
        "expected_base_tree": BASE_TREE,
        "expected_base_subject": BASE_SUBJECT,
        "canonical_evidence_python_implementation": "cpython",
        "canonical_evidence_python_version": "3.10.4",
        "source_input_count": 20,
        "public_marker": PUBLIC_MARKER,
        "public_definition_count": 11,
        "public_definitions": list(PUBLIC_DEFINITIONS),
        "registered_rule_ids": [
            f"ADMIT_{index:03d}" for index in range(1, 16)
        ],
        "known_not_registered_rule_ids": [],
        "registered_rule_count": 15,
        "contract_row_count": 45,
        "truth_matrix_row_count": 79,
        "truth_matrix_group_counts": {
            "admit015_inherited_exact42_runtime": 42,
            "admit015_oracle_negative": 8,
            "admit015_source_negative": 11,
            "predecessor_representative_dispatch": 14,
            "public_dispatch": 4,
        },
        "truth_input_representation_columns": list(
            TRUTH_INPUT_REPRESENTATION_COLUMNS
        ),
        "truth_input_representation_semantics_independently_verified": True,
        "truth_trace_columns": [
            "expected_call_order",
            "observed_call_order",
            "expected_stage_context_identity_preserved",
            "observed_stage_context_identity_preserved",
            "adapter_stage_target_access_count",
            "formal_stage_target_access_count",
            "oracle_stage_target_access_count",
        ],
        "truth_trace_semantics_independently_verified": True,
        "admit_015_inherited_exact42_runtime_case_count": 42,
        "admit_015_source_negative_case_count": 11,
        "admit_015_oracle_negative_case_count": 8,
        "public_dispatch_case_count": 4,
        "predecessor_representative_dispatch_count": 14,
        "registry_identity_audit_row_count": 27,
        "safety_audit_row_count": 32,
        "issue_inventory_row_count": 30,
        "issue_transition_count": 1,
        "issue_coverage_before": ["ADMIT_015"],
        "issue_coverage_after": [],
        "issue_coverage_effective_status": "resolved",
        "readiness": expected_readiness,
        "current_permission": False,
        "synthetic_true_case_changes_current_permission": False,
        "authorized_admit_015_training_execution_count": 0,
        "admit_015_implemented": True,
        "admit_015_registered_in_engine": True,
        "mandatory_training_authorization_enforcement_api_frozen": False,
        "mandatory_training_authorization_enforcement_implemented": False,
        "combined_permission_semantics_frozen": False,
        "provider_mapping_validated": False,
        "real_provider_evaluation_ready": False,
        "ready_for_bulk_download_now": False,
        "combined_candidate_verdict_implemented": False,
        "cross_rule_aggregation_implemented": False,
        "feature_semantics_audit_completed": False,
        "historical_unknown_atom_feature_policy_resolved": False,
        "historical_feature_semantics_known": False,
        "real_training_ready": False,
        "ready_for_training": False,
        "step12d_is_final_training_feature_contract": False,
        "step12d_status": (
            "smoke_legality_only_not_final_training_feature_contract"
        ),
        "canonical_masks": [
            {"semantic_name": "warhead_only", "alias": "A"},
            {"semantic_name": "linker_plus_warhead", "alias": "B"},
            {"semantic_name": "scaffold_plus_warhead", "alias": "B2"},
            {"semantic_name": "scaffold_only", "alias": "B3"},
            {
                "semantic_name": "scaffold_plus_linker_plus_warhead",
                "alias": "C",
            },
        ],
        "canonical_mask_count": 5,
        "output_files": list(OUTPUTS),
        "output_file_count": 6,
        "output_sha256_excludes_manifest_self_hash": True,
        "output_materialization": {
            "GPFS_EINVAL_fail_closed": True,
            "all_leaf_descriptors_retained_through_final_traversal": True,
            "all_payloads_built_before_mutation": True,
            "failure_staging_retained": True,
            "failure_staging_never_deleted": True,
            "authenticated_retained_path_only": True,
            "parent_and_staging_binding_rechecked_inside_rename": True,
            "complete_set_postverify": True,
            "destination_name_inode_binding": True,
            "exact_six_allowlist": True,
            "exclusive_create": True,
            "existing_exact_set_inode_preserving_noop": True,
            "file_fsync": True,
            "mismatch_repair_forbidden": True,
            "parent_fsync": True,
            "pinned_parent_root_staging_leaf": True,
            "renameat2_RENAME_NOREPLACE": True,
            "staging_directory_fsync": True,
            "staging_lexical_binding_verified": True,
        },
        "evidence_lifecycle_hardening": {
            "artifact_semantics_rebuilt_after_sha_verification": True,
            "checker_exact42_specs_owned_without_project_checker_import": True,
            "exact10_lifecycle_exact_inventory": True,
            "manifest_duplicate_and_exact_schema_rejection": True,
            "publisher_destination_binding_rechecks": True,
            "source_and_output_final_leaf_identity_post_traversal": True,
            "source_and_output_full_identity_post_traversal": True,
            "bounded_recursive_no_follow_lifecycle": True,
            "successor_regression_historical_deselection_count": 0,
        },
        "all_checks_passed": True,
        "validation_failures": [],
        "recommended_next_step": (
            "design_covapie_admit_015_mandatory_training_"
            "authorization_enforcement_contract_v1"
        ),
    }
    if any(manifest.get(key) != value for key, value in required.items()):
        raise AssertionError("manifest required semantics drift")
    if any(
        manifest.get(name) is not value
        for name, value in expected_readiness.items()
    ):
        raise AssertionError("manifest top-level readiness drift")
    if (
        manifest["source_input_paths"]
        != [path for path, _ in SOURCE_BOUNDARY]
        or manifest["source_input_sha256"] != dict(SOURCE_BOUNDARY)
        or manifest["output_sha256"]
        != {name: hashes[name] for name in OUTPUTS[:5]}
        or OUTPUTS[5] in manifest["output_sha256"]
        or manifest["precondition_transition"]
        != {
            "row_count": 45,
            "complete_count": 40,
            "supported_but_not_frozen_count": 0,
            "incomplete_count": 5,
            "implementation_blocking_count": 5,
            "resolved_precondition_ids": ["PRE_032", "PRE_033"],
            "resolution": (
                "ADMIT_015 handler, immutable Exact15 registry and unified "
                "single-rule dispatcher implemented with first14 identity "
                "preservation"
            ),
            "remaining_open_precondition_ids": [
                "PRE_034",
                "PRE_035",
                "PRE_036",
                "PRE_038",
                "PRE_042",
            ],
        }
    ):
        raise AssertionError("manifest source/output/precondition drift")
    verification = manifest["source_input_verification"]
    if len(verification) != 20:
        raise AssertionError("manifest source verification count drift")
    for expected, observed in zip(
        source_records, verification, strict=True
    ):
        if any(
            observed.get(name) != value
            for name, value in expected.items()
        ) or any(
            observed.get(name) is not True
            for name in (
                "tracked",
                "filesystem_regular",
                "non_symlink",
                "parent_chain_non_symlink",
                "safe_descendant",
                "pinned_fd_read",
                "post_read_identity_verified",
                "final_leaf_identity_verified",
                "source_verified",
            )
        ):
            raise AssertionError("manifest source verification drift")
    attestation = manifest["candidate_production_source_attestation"]
    if (
        attestation["production_full_sha256"]
        != EXPECTED_PRODUCTION_SHA256
        or attestation["marker_prefix_sha256"]
        != EXPECTED_MARKER_PREFIX_SHA256
        or attestation["normalized_ast_sha256"]
        != EXPECTED_DEFINITION_AST_SHA256
        or attestation["definition_names"] != list(PUBLIC_DEFINITIONS)
    ):
        raise AssertionError("manifest candidate attestation drift")
    if (
        manifest["public_dispatch_signature"]
        != str(inspect.signature(runtime.evaluate_admission_rule))
        or manifest["admit_015_handler_signature"]
        != str(inspect.signature(runtime._evaluate_registered_admit_015))
        or manifest["public_dispatch_uses_local_registry"] is not True
        or manifest["adapter_design_simulator_called_by_public_runtime"]
        is not False
        or manifest["rule_names"] != dict(runtime.RULE_NAMES)
        or manifest["adapter_ids"] != dict(runtime.ADAPTER_IDS)
        or manifest["first_fourteen_handler_identity_reused"]
        != {
            rule_id: True
            for rule_id in tuple(runtime.EVALUATOR_REGISTRY)[:14]
        }
    ):
        raise AssertionError("manifest runtime closure evidence drift")
    return {"hashes": hashes, "manifest": manifest}


def _matches_stage_family(name: str) -> bool:
    return any(token in name for token in STAGE_FAMILY_TOKENS)


def _bounded_recursive_stage_inventory(
    root: Path,
) -> tuple[
    dict[Path, os.stat_result],
    tuple[Path, ...],
]:
    root = Path(os.path.abspath(root))
    observed: dict[Path, os.stat_result] = {}
    derived_roots: list[Path] = []

    def stat_at(
        parent_fd: int,
        name: str,
        reason: str,
    ) -> os.stat_result:
        try:
            return os.stat(
                name,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
        except OSError as error:
            raise AssertionError(f"{reason} stat failed") from error

    def directory_names(directory_fd: int, reason: str) -> tuple[str, ...]:
        try:
            return tuple(sorted(os.listdir(directory_fd)))
        except OSError as error:
            raise AssertionError(f"{reason} inventory failed") from error

    def assert_directory(
        item: os.stat_result,
        expected: tuple[int, int, int, int, int, int],
        reason: str,
    ) -> None:
        if (
            _full_identity(item) != expected
            or not stat.S_ISDIR(item.st_mode)
            or stat.S_ISLNK(item.st_mode)
        ):
            raise AssertionError(f"{reason} directory binding drift")

    def open_directory(
        parent_fd: int,
        name: str,
        expected: tuple[int, int, int, int, int, int],
        reason: str,
    ) -> int:
        try:
            child_fd = os.open(
                name,
                DIR_FLAGS,
                dir_fd=parent_fd,
            )
        except OSError as error:
            raise AssertionError(f"{reason} directory open failed") from error
        try:
            assert_directory(os.fstat(child_fd), expected, reason)
        except BaseException:
            os.close(child_fd)
            raise
        return child_fd

    def assert_child_binding(
        parent_fd: int,
        name: str,
        child_fd: int,
        expected: tuple[int, int, int, int, int, int],
        reason: str,
    ) -> None:
        assert_directory(os.fstat(parent_fd), parent_identities[parent_fd], reason)
        assert_directory(stat_at(parent_fd, name, reason), expected, reason)
        assert_directory(os.fstat(child_fd), expected, reason)

    parent_identities: dict[
        int, tuple[int, int, int, int, int, int]
    ] = {}

    def scan_directory(
        directory_fd: int,
        logical: Path,
        expected: tuple[int, int, int, int, int, int],
        *,
        observe_all: bool,
    ) -> None:
        assert_directory(
            os.fstat(directory_fd),
            expected,
            "bounded scan",
        )
        initial_names = directory_names(directory_fd, "bounded scan initial")
        identities: dict[
            str, tuple[int, int, int, int, int, int]
        ] = {}
        for name in initial_names:
            item = stat_at(directory_fd, name, "bounded scan entry")
            identity = _full_identity(item)
            identities[name] = identity
            if stat.S_ISLNK(item.st_mode):
                raise AssertionError(
                    "same-stage bounded scan symlink rejected"
                )
            relative = logical / name
            if observe_all or _matches_stage_family(name):
                observed[relative] = item
            if not stat.S_ISDIR(item.st_mode):
                continue
            child_fd = open_directory(
                directory_fd,
                name,
                identity,
                "bounded scan child",
            )
            parent_identities[child_fd] = identity
            try:
                scan_directory(
                    child_fd,
                    relative,
                    identity,
                    observe_all=observe_all,
                )
                assert_child_binding(
                    directory_fd,
                    name,
                    child_fd,
                    identity,
                    "bounded scan child post-recursion",
                )
            finally:
                parent_identities.pop(child_fd, None)
                os.close(child_fd)
        if directory_names(directory_fd, "bounded scan final") != initial_names:
            raise AssertionError("bounded scan directory inventory drift")
        assert_directory(
            os.fstat(directory_fd),
            expected,
            "bounded scan final",
        )
        for name in initial_names:
            final_item = stat_at(
                directory_fd,
                name,
                "bounded scan final entry",
            )
            if (
                _full_identity(final_item) != identities[name]
                or stat.S_ISLNK(final_item.st_mode)
            ):
                raise AssertionError("bounded scan entry identity drift")

    def scan_derived_parent(
        directory_fd: int,
        logical: Path,
        expected: tuple[int, int, int, int, int, int],
    ) -> None:
        assert_directory(
            os.fstat(directory_fd),
            expected,
            "derived parent",
        )
        initial_names = directory_names(
            directory_fd,
            "derived parent initial",
        )
        matching_identities: dict[
            str, tuple[int, int, int, int, int, int]
        ] = {}
        for name in initial_names:
            if not _matches_stage_family(name):
                continue
            item = stat_at(directory_fd, name, "derived root")
            identity = _full_identity(item)
            if (
                stat.S_ISLNK(item.st_mode)
                or not stat.S_ISDIR(item.st_mode)
            ):
                raise AssertionError("same-stage derived root unsafe")
            relative = logical / name
            matching_identities[name] = identity
            derived_roots.append(relative)
            observed[relative] = item
            child_fd = open_directory(
                directory_fd,
                name,
                identity,
                "derived root",
            )
            parent_identities[child_fd] = identity
            try:
                scan_directory(
                    child_fd,
                    relative,
                    identity,
                    observe_all=True,
                )
                assert_child_binding(
                    directory_fd,
                    name,
                    child_fd,
                    identity,
                    "derived root post-recursion",
                )
            finally:
                parent_identities.pop(child_fd, None)
                os.close(child_fd)
        if (
            directory_names(directory_fd, "derived parent final")
            != initial_names
        ):
            raise AssertionError("derived parent inventory drift")
        assert_directory(
            os.fstat(directory_fd),
            expected,
            "derived parent final",
        )
        for name, identity in matching_identities.items():
            assert_directory(
                stat_at(directory_fd, name, "derived root final"),
                identity,
                "derived root final",
            )

    root_item = os.lstat(root)
    root_identity = _full_identity(root_item)
    if (
        not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
    ):
        raise AssertionError("bounded scan repository root unsafe")
    try:
        root_fd = os.open(root, DIR_FLAGS)
    except OSError as error:
        raise AssertionError("bounded scan repository root open failed") from error
    parent_identities[root_fd] = root_identity

    def with_open_directory(
        relative: Path,
        *,
        derived_parent: bool,
    ) -> None:
        parent_fd = root_fd
        descriptors: list[int] = []
        bindings: list[
            tuple[
                int,
                str,
                int,
                tuple[int, int, int, int, int, int],
            ]
        ] = []
        try:
            for name in relative.parts:
                item = stat_at(
                    parent_fd,
                    name,
                    "bounded root component",
                )
                identity = _full_identity(item)
                if (
                    stat.S_ISLNK(item.st_mode)
                    or not stat.S_ISDIR(item.st_mode)
                ):
                    raise AssertionError("bounded root component unsafe")
                child_fd = open_directory(
                    parent_fd,
                    name,
                    identity,
                    "bounded root component",
                )
                descriptors.append(child_fd)
                bindings.append((parent_fd, name, child_fd, identity))
                parent_identities[child_fd] = identity
                parent_fd = child_fd
            expected = parent_identities[parent_fd]
            if derived_parent:
                scan_derived_parent(parent_fd, relative, expected)
            else:
                scan_directory(
                    parent_fd,
                    relative,
                    expected,
                    observe_all=False,
                )
            for lexical_parent, name, child_fd, identity in reversed(
                bindings
            ):
                assert_child_binding(
                    lexical_parent,
                    name,
                    child_fd,
                    identity,
                    "bounded root post-scan",
                )
        finally:
            for descriptor in reversed(descriptors):
                parent_identities.pop(descriptor, None)
                os.close(descriptor)

    try:
        assert_directory(
            os.fstat(root_fd),
            root_identity,
            "bounded scan repository root",
        )
        for relative in (
            Path("src/covalent_ext"),
            Path("scripts"),
            Path("tests"),
            Path("docs"),
        ):
            with_open_directory(relative, derived_parent=False)
        with_open_directory(
            Path("data/derived/covalent_small"),
            derived_parent=True,
        )
        if (
            _full_identity(os.lstat(root)) != root_identity
            or _full_identity(os.fstat(root_fd)) != root_identity
        ):
            raise AssertionError("bounded scan repository root drift")
        return observed, tuple(derived_roots)
    finally:
        parent_identities.pop(root_fd, None)
        os.close(root_fd)


def _assert_stage_candidate_safe(
    root: Path,
    relative: Path,
    item: os.stat_result,
) -> None:
    ignored = _git(
        root,
        "check-ignore",
        "--no-index",
        "-q",
        "--",
        relative.as_posix(),
    )
    if ignored.returncode == 0:
        raise AssertionError("same-stage candidate ignored")
    if ignored.returncode != 1:
        raise AssertionError("check-ignore failed closed")
    if stat.S_ISLNK(item.st_mode):
        raise AssertionError("same-stage symlink rejected")
    if relative == STAGE:
        if not stat.S_ISDIR(item.st_mode):
            raise AssertionError("same-stage derived root unsafe")
        return
    if (
        not stat.S_ISREG(item.st_mode)
        or relative.suffix in FORBIDDEN_SUFFIXES
        or item.st_size > MAX_BYTES
    ):
        raise AssertionError("same-stage leaf unsafe")


def _read_head_commit(root: Path) -> str:
    result = _git(root, "rev-parse", "--verify", "HEAD^{commit}")
    if result.returncode:
        raise AssertionError("HEAD commit query failed")
    if type(result.stdout) is not bytes:
        raise AssertionError("HEAD commit malformed")
    try:
        stdout = result.stdout.decode("ascii")
    except UnicodeDecodeError as error:
        raise AssertionError("HEAD commit malformed") from error
    if (
        type(stdout) is not str
        or re.fullmatch(r"[0-9a-f]{40}\n", stdout) is None
    ):
        raise AssertionError("HEAD commit malformed")
    return stdout[:-1]


def _capture_lifecycle_state(
    root: Path,
    ordered: Sequence[str],
    *,
    base: str,
) -> tuple[
    str,
    dict[str, tuple[int, int, int, int, int, int]],
    set[str],
    set[str],
    set[str],
]:
    head_commit = _read_head_commit(root)
    ancestor = _git(
        root,
        "merge-base",
        "--is-ancestor",
        base,
        head_commit,
    )
    if ancestor.returncode:
        raise AssertionError("base is not an ancestor")
    identities: dict[
        str, tuple[int, int, int, int, int, int]
    ] = {}
    tracked: set[str] = set()
    untracked: set[str] = set()
    for relative in ordered:
        path = Path(relative)
        target = root / path
        try:
            item = os.lstat(target)
        except FileNotFoundError as error:
            raise AssertionError("Exact10 missing") from error
        if (
            path.is_absolute()
            or ".." in path.parts
            or path.suffix in FORBIDDEN_SUFFIXES
            or not stat.S_ISREG(item.st_mode)
            or stat.S_ISLNK(item.st_mode)
            or item.st_size > MAX_BYTES
        ):
            raise AssertionError("Exact10 leaf unsafe")
        identities[relative] = _full_identity(item)
        ignored = _git(
            root,
            "check-ignore",
            "--no-index",
            "-q",
            "--",
            relative,
        )
        if ignored.returncode == 0:
            raise AssertionError("Exact10 ignored")
        if ignored.returncode != 1:
            raise AssertionError("check-ignore failed closed")
        index = _git(root, "ls-files", "--stage", "--", relative)
        if index.returncode:
            raise AssertionError("candidate index query failed")
        if index.stdout:
            _, _, stage_number = _parse_index(
                index.stdout,
                relative,
            )
            if stage_number != 0:
                raise AssertionError("nonzero index stage")
            tracked.add(relative)
        else:
            untracked.add(relative)
    untracked_result = _git(
        root,
        "ls-files",
        "--others",
        "--exclude-standard",
    )
    cached = _git(root, "diff", "--cached", "--name-only")
    dirty = _git(root, "diff", "--name-only")
    if (
        untracked_result.returncode
        or cached.returncode
        or dirty.returncode
        or cached.stdout
        or dirty.stdout
    ):
        raise AssertionError("repository staged/dirty lifecycle")
    listed_untracked = set(
        untracked_result.stdout.decode().splitlines()
    )
    if tracked and untracked:
        raise AssertionError("mixed lifecycle")
    if listed_untracked != untracked:
        raise AssertionError(
            "entire untracked inventory is not Exact10"
        )
    return (
        head_commit,
        identities,
        tracked,
        untracked,
        listed_untracked,
    )


def lifecycle(
    root: Path = ROOT,
    exact10: Sequence[Path] = EXACT10,
    *,
    base: str = BASE,
) -> str:
    root = Path(os.path.abspath(root))
    ordered = tuple(path.as_posix() for path in exact10)
    expected = set(ordered)
    expected_paths = {Path(relative) for relative in ordered}
    if len(ordered) != 10 or len(expected) != 10:
        raise AssertionError("candidate is not Exact10")

    (
        initial_head,
        initial_identities,
        initial_tracked,
        initial_untracked,
        initial_listed_untracked,
    ) = _capture_lifecycle_state(root, ordered, base=base)
    observed, derived_roots = _bounded_recursive_stage_inventory(root)
    for relative, item in observed.items():
        _assert_stage_candidate_safe(root, relative, item)
    if set(observed) != {*expected_paths, STAGE}:
        raise AssertionError("same-stage recursive inventory drift")
    if derived_roots != (STAGE,):
        raise AssertionError("same-stage derived root drift")
    output_names = tuple(
        relative.name
        for relative in observed
        if relative.parent == STAGE
    )
    if (
        len(output_names) != 6
        or set(output_names) != set(OUTPUTS)
    ):
        raise AssertionError("same-stage Exact6 drift")
    (
        final_head,
        final_identities,
        final_tracked,
        final_untracked,
        final_listed_untracked,
    ) = _capture_lifecycle_state(root, ordered, base=base)
    if final_identities != initial_identities:
        raise AssertionError("Exact10 final identity drift")
    if (
        final_tracked != initial_tracked
        or final_untracked != initial_untracked
        or final_listed_untracked != initial_listed_untracked
    ):
        raise AssertionError("repository final inventory drift")
    if final_head != initial_head:
        raise AssertionError("repository HEAD drift")
    if not final_tracked and final_untracked == expected:
        return "pre_commit"
    if final_tracked == expected and not final_untracked:
        return "post_commit"
    raise AssertionError("candidate lifecycle incomplete")


def silent_import() -> None:
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
        raise AssertionError("isolated production import not silent")


def main() -> int:
    canonical_guard()
    source_records = verify_sources()
    attestation = attest_candidate()
    payloads = output_bytes()
    sys.path.insert(0, str(ROOT / "src"))
    runtime = importlib.import_module(MODULE)
    if Path(os.path.abspath(runtime.__file__)) != ROOT / CANDIDATE:
        raise AssertionError("imported candidate path drift")
    if pinned_read(ROOT, CANDIDATE) != attestation["source"]:
        raise AssertionError("candidate changed after attestation")
    semantics = verify_runtime(runtime)
    evidence = verify_artifacts(payloads, source_records, runtime)
    before = {
        name: os.lstat(ROOT / STAGE / name).st_ino for name in OUTPUTS
    }
    runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015_v1()
    after = {
        name: os.lstat(ROOT / STAGE / name).st_ino for name in OUTPUTS
    }
    if before != after or output_bytes() != payloads:
        raise AssertionError("inode-preserving no-op drift")
    silent_import()
    state = lifecycle()
    print(
        json.dumps(
            {
                "base": BASE,
                "checked": True,
                "exact42_runtime_count": semantics["exact42_count"],
                "lifecycle": state,
                "manifest_sha256": evidence["hashes"][OUTPUTS[5]],
                "oracle_negative_count": semantics[
                    "oracle_negative_count"
                ],
                "recommended_next_step": evidence["manifest"][
                    "recommended_next_step"
                ],
                "source_boundary": "Exact20_git_blob_verified",
                "source_negative_count": semantics[
                    "source_negative_count"
                ],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
