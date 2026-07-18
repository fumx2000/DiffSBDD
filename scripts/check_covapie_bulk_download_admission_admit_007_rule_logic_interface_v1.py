#!/usr/bin/env python3
"""Fail-closed checker for the ADMIT_007 standalone evaluator interface v1."""

from __future__ import annotations

import ast
import csv
import hashlib
import importlib.util
import inspect
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import FrozenInstanceError, dataclass, fields, replace
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_007_rule_logic_interface as interface,
)
from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate
    as committed_oracle,
)


EXPECTED_OUTPUT_SHA256 = {
    interface.CONTRACT_FILENAME: "d6183b2f6dba1c50f6131e28d14519c29d6645b879f954fed7668e776bb0f425",
    interface.TRUTH_FILENAME: "e0ac129e65333e7d1808b8d165391e9188a22c61e8f96ce5e0def8895a34b30c",
    interface.SOURCE_AUDIT_FILENAME: "512308ffeeafbe0f80729883f68b074828915b3ebbc8a7afeb37231399fd9bd4",
    interface.SAFETY_FILENAME: "74c0e0f2825b265e8beb6251d392258454c4824f9b8777ebe794201b4051038a",
    interface.ISSUE_FILENAME: "e63c1b83fe245031ecdefa6b3387086b2aba8d72ef50189be17b9874e8f18196",
    interface.MANIFEST_FILENAME: "f5212100bf458372dd908a234557ee34858cf24cf2360e39b1e61cba8a562958",
}


EXPECTED_MANIFEST = json.loads(r"""
{
  "admission_rule_id": "ADMIT_007",
  "admission_rule_name": "distance_only_inference_forbidden",
  "admit_007_context_semantics_implemented": true,
  "admit_007_formal_result_contract_frozen": true,
  "admit_007_independent_semantic_oracle_attested": true,
  "admit_007_reason_outcome_contract_implemented": true,
  "admit_007_registered_in_engine": false,
  "admit_007_scalar_semantics_implemented": true,
  "admit_007_standalone_evaluator_implemented": true,
  "admit_007_synthetic_truth_matrix_passed": true,
  "admit_007_unified_adapter_contract_frozen": false,
  "admit_007_unified_adapter_implemented": false,
  "admit_008_standalone_evaluator_implemented": false,
  "admit_008_to_015_registered_in_engine": false,
  "all_15_rules_covered": false,
  "all_checks_passed": true,
  "all_issue_checks_passed": true,
  "all_predecessor_contract_checks_passed": true,
  "all_result_contract_checks_passed": true,
  "all_safety_checks_passed": true,
  "all_semantic_checks_passed": true,
  "all_source_boundary_checks_passed": true,
  "all_truth_matrix_checks_passed": true,
  "allowed_covalent_evidence_classes": [
    "explicit_structure_bond_record",
    "explicit_curated_covalent_annotation"
  ],
  "artifact_reference_paths_not_recursively_opened": true,
  "canonical_enum_members": [
    "explicit_structure_bond_record",
    "explicit_curated_covalent_annotation",
    "distance_only_inference"
  ],
  "combined_candidate_verdict_contract_frozen": false,
  "combined_candidate_verdict_implemented": false,
  "context_validation_precedence": [
    "exact_tuple",
    "exact_content"
  ],
  "contract_pass_count": 28,
  "contract_row_count": 28,
  "cross_rule_precedence_frozen": false,
  "current_exact6_runtime_modified": false,
  "evaluate_all_rules_implemented": false,
  "evaluator_call_graph_pure_in_memory": true,
  "evaluator_precedence": [
    "scalar_failure",
    "context_failure",
    "canonical_member_classification"
  ],
  "exact11_real_rows_evaluated": false,
  "expected_base_commit": "801d6edee9b2424f97d0c359bd5249aabc385611",
  "expected_base_subject": "add CovaPIE ADMIT_007 evaluator preconditions audit v1",
  "feature_semantics_audit_required_before_training": true,
  "formal_blocked_reason": "DISTANCE_ONLY_INFERENCE_NOT_ADMISSIBLE",
  "historical_lowercase_reason_source_evidence_only": "distance_only_inference_not_admissible",
  "historical_missing_reason_used_by_standalone_evaluator": false,
  "independent_semantic_oracle": "classify_admit_006_admit_007_evidence_design",
  "independent_semantic_oracle_attested": true,
  "issue_inventory_preserved_exactly": true,
  "issue_inventory_row_count": 11,
  "issue_inventory_sha256": "e63c1b83fe245031ecdefa6b3387086b2aba8d72ef50189be17b9874e8f18196",
  "manifest_schema_version": "covapie_admit_007_rule_logic_interface_manifest_v1",
  "normalization_applied": false,
  "outcome_vocabulary": [
    "passed",
    "blocked",
    "invalid"
  ],
  "output_file_count": 6,
  "output_files": [
    "covapie_admit_007_rule_logic_interface_contract.csv",
    "covapie_admit_007_rule_logic_interface_truth_matrix.csv",
    "covapie_admit_007_rule_logic_interface_source_boundary_audit.csv",
    "covapie_admit_007_rule_logic_interface_safety_audit.csv",
    "covapie_admit_007_rule_logic_interface_issue_readiness_inventory.csv",
    "covapie_admit_007_rule_logic_interface_manifest.json"
  ],
  "output_sha256": {
    "covapie_admit_007_rule_logic_interface_contract.csv": "d6183b2f6dba1c50f6131e28d14519c29d6645b879f954fed7668e776bb0f425",
    "covapie_admit_007_rule_logic_interface_issue_readiness_inventory.csv": "e63c1b83fe245031ecdefa6b3387086b2aba8d72ef50189be17b9874e8f18196",
    "covapie_admit_007_rule_logic_interface_safety_audit.csv": "74c0e0f2825b265e8beb6251d392258454c4824f9b8777ebe794201b4051038a",
    "covapie_admit_007_rule_logic_interface_source_boundary_audit.csv": "512308ffeeafbe0f80729883f68b074828915b3ebbc8a7afeb37231399fd9bd4",
    "covapie_admit_007_rule_logic_interface_truth_matrix.csv": "e0ac129e65333e7d1808b8d165391e9188a22c61e8f96ce5e0def8895a34b30c"
  },
  "output_sha256_excludes_manifest_self_hash": true,
  "predecessor_contract_independently_checked": true,
  "production_oracle_call": false,
  "project": "CovaPIE",
  "public_api": "evaluate_admit_007(covalent_event_evidence_source, allowed_covalent_evidence_classes)",
  "readiness": {
    "admit_007_context_semantics_implemented": true,
    "admit_007_formal_result_contract_frozen": true,
    "admit_007_independent_semantic_oracle_attested": true,
    "admit_007_reason_outcome_contract_implemented": true,
    "admit_007_registered_in_engine": false,
    "admit_007_scalar_semantics_implemented": true,
    "admit_007_standalone_evaluator_implemented": true,
    "admit_007_synthetic_truth_matrix_passed": true,
    "admit_007_unified_adapter_contract_frozen": false,
    "admit_007_unified_adapter_implemented": false,
    "admit_008_standalone_evaluator_implemented": false,
    "admit_008_to_015_registered_in_engine": false,
    "all_15_rules_covered": false,
    "combined_candidate_verdict_contract_frozen": false,
    "combined_candidate_verdict_implemented": false,
    "cross_rule_precedence_frozen": false,
    "current_exact6_runtime_modified": false,
    "evaluate_all_rules_implemented": false,
    "evaluator_call_graph_pure_in_memory": true,
    "exact11_real_rows_evaluated": false,
    "feature_semantics_audit_required_before_training": true,
    "ready_for_admit_007_unified_adapter_contract_design": true,
    "ready_for_bulk_download_now": false,
    "ready_for_training": false,
    "ready_to_train_now": false,
    "real_candidate_evaluation": false,
    "real_provider_enum_mapping_validated": false
  },
  "ready_for_admit_007_unified_adapter_contract_design": true,
  "ready_for_bulk_download_now": false,
  "ready_for_training": false,
  "ready_to_train_now": false,
  "real_candidate_evaluation": false,
  "real_provider_enum_mapping_validated": false,
  "reason_vocabulary": [
    "",
    "COVALENT_EVENT_EVIDENCE_SOURCE_TYPE_INVALID",
    "COVALENT_EVENT_EVIDENCE_SOURCE_EMPTY",
    "COVALENT_EVENT_EVIDENCE_SOURCE_NON_ASCII",
    "COVALENT_EVENT_EVIDENCE_SOURCE_SYNTAX_INVALID",
    "COVALENT_EVENT_EVIDENCE_SOURCE_UNKNOWN",
    "ALLOWED_COVALENT_EVIDENCE_CLASSES_TYPE_INVALID",
    "ALLOWED_COVALENT_EVIDENCE_CLASSES_CONTENT_INVALID",
    "DISTANCE_ONLY_INFERENCE_NOT_ADMISSIBLE"
  ],
  "recommended_next_step": "design_covapie_admit_007_unified_adapter_contract_v1",
  "result_field_count": 10,
  "result_fields": [
    "admission_rule_id",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "canonical_covalent_event_evidence_source",
    "validated_candidate_fields",
    "consumed_candidate_fields",
    "consumed_context_items",
    "evaluator_io_used"
  ],
  "result_type": "Admit007EvaluationResult",
  "safety_pass_count": 20,
  "safety_row_count": 20,
  "scalar_validation_precedence": [
    "exact_builtin_str",
    "nonempty",
    "ascii",
    "syntax",
    "exact3_membership"
  ],
  "source_audit_pass_count": 10,
  "source_audit_row_count": 10,
  "source_boundary_name": "fixed_ordered_minimal_committed_source_boundary",
  "source_documents_parsed_only_from_frozen_snapshot_bytes": true,
  "source_input_count": 10,
  "source_input_paths": [
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_007_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_007_formal_evaluator_preconditions_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_007_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_007_evaluator_precondition_matrix.csv",
    "src/covalent_ext/covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1/covapie_covalent_event_evidence_source_enum_contract_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1/covapie_covalent_event_evidence_source_enum_validation_truth_matrix.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1/covapie_admit_006_admit_007_evidence_responsibility_matrix.csv",
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006_v1/covapie_admit_001_to_006_runtime_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006_v1/covapie_admit_001_to_006_runtime_issue_inventory.csv",
    "src/covalent_ext/covapie_bulk_download_admission_admit_006_rule_logic_interface.py"
  ],
  "source_input_sha256": {
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_007_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_007_evaluator_precondition_matrix.csv": "a6c1b8a84e1dd112b0b26ed0a0d87e235f117df3368f14b056048358ed7fb29c",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_007_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_007_formal_evaluator_preconditions_manifest.json": "8459b898d543c50f36e625faff2bba7ba0491bce130c488c32ae91b3c3ef0d2a",
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1/covapie_admit_006_admit_007_evidence_responsibility_matrix.csv": "41f7b53ccee575d098379ff6722639a53583c6b4097be7708483ed9f651ae284",
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1/covapie_covalent_event_evidence_source_enum_contract_manifest.json": "91b98e2a10a20a8f8b07708ec77af947c29e94c33ce73bcf7528f1d8a8abbf20",
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1/covapie_covalent_event_evidence_source_enum_validation_truth_matrix.csv": "d332ca526fd0ec05be5ab2edee87daa6d93adcd51515bacec1f1caee814f7507",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006_v1/covapie_admit_001_to_006_runtime_issue_inventory.csv": "e63c1b83fe245031ecdefa6b3387086b2aba8d72ef50189be17b9874e8f18196",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006_v1/covapie_admit_001_to_006_runtime_manifest.json": "359c666541602458b3ea6a023be95ea06205f8580ff71d371c25306715f558d6",
    "src/covalent_ext/covapie_bulk_download_admission_admit_006_rule_logic_interface.py": "6fd3727234b4b3f637fa5812c78421ec944238518702bc7f9d0d57a654d9a46d",
    "src/covalent_ext/covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate.py": "92267891cb8a51d2a919d6a6eaca6e6320de288f41ac75692a1c1e6fde2ceb76",
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006.py": "fe00e617cfc99bf40eb44b13b66e4c14f08f2c764dd32820f03fd162f9049896"
  },
  "source_input_verification": [
    {
      "base_tree_sha256": "8459b898d543c50f36e625faff2bba7ba0491bce130c488c32ae91b3c3ef0d2a",
      "expected_sha256": "8459b898d543c50f36e625faff2bba7ba0491bce130c488c32ae91b3c3ef0d2a",
      "filesystem_sha256": "8459b898d543c50f36e625faff2bba7ba0491bce130c488c32ae91b3c3ef0d2a",
      "source_order": 1,
      "source_relative_path": "data/derived/covalent_small/covapie_bulk_download_admission_admit_007_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_007_formal_evaluator_preconditions_manifest.json",
      "source_verified": true
    },
    {
      "base_tree_sha256": "a6c1b8a84e1dd112b0b26ed0a0d87e235f117df3368f14b056048358ed7fb29c",
      "expected_sha256": "a6c1b8a84e1dd112b0b26ed0a0d87e235f117df3368f14b056048358ed7fb29c",
      "filesystem_sha256": "a6c1b8a84e1dd112b0b26ed0a0d87e235f117df3368f14b056048358ed7fb29c",
      "source_order": 2,
      "source_relative_path": "data/derived/covalent_small/covapie_bulk_download_admission_admit_007_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_007_evaluator_precondition_matrix.csv",
      "source_verified": true
    },
    {
      "base_tree_sha256": "92267891cb8a51d2a919d6a6eaca6e6320de288f41ac75692a1c1e6fde2ceb76",
      "expected_sha256": "92267891cb8a51d2a919d6a6eaca6e6320de288f41ac75692a1c1e6fde2ceb76",
      "filesystem_sha256": "92267891cb8a51d2a919d6a6eaca6e6320de288f41ac75692a1c1e6fde2ceb76",
      "source_order": 3,
      "source_relative_path": "src/covalent_ext/covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate.py",
      "source_verified": true
    },
    {
      "base_tree_sha256": "91b98e2a10a20a8f8b07708ec77af947c29e94c33ce73bcf7528f1d8a8abbf20",
      "expected_sha256": "91b98e2a10a20a8f8b07708ec77af947c29e94c33ce73bcf7528f1d8a8abbf20",
      "filesystem_sha256": "91b98e2a10a20a8f8b07708ec77af947c29e94c33ce73bcf7528f1d8a8abbf20",
      "source_order": 4,
      "source_relative_path": "data/derived/covalent_small/covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1/covapie_covalent_event_evidence_source_enum_contract_manifest.json",
      "source_verified": true
    },
    {
      "base_tree_sha256": "d332ca526fd0ec05be5ab2edee87daa6d93adcd51515bacec1f1caee814f7507",
      "expected_sha256": "d332ca526fd0ec05be5ab2edee87daa6d93adcd51515bacec1f1caee814f7507",
      "filesystem_sha256": "d332ca526fd0ec05be5ab2edee87daa6d93adcd51515bacec1f1caee814f7507",
      "source_order": 5,
      "source_relative_path": "data/derived/covalent_small/covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1/covapie_covalent_event_evidence_source_enum_validation_truth_matrix.csv",
      "source_verified": true
    },
    {
      "base_tree_sha256": "41f7b53ccee575d098379ff6722639a53583c6b4097be7708483ed9f651ae284",
      "expected_sha256": "41f7b53ccee575d098379ff6722639a53583c6b4097be7708483ed9f651ae284",
      "filesystem_sha256": "41f7b53ccee575d098379ff6722639a53583c6b4097be7708483ed9f651ae284",
      "source_order": 6,
      "source_relative_path": "data/derived/covalent_small/covapie_bulk_download_admission_covalent_event_evidence_source_enum_contract_design_gate_v1/covapie_admit_006_admit_007_evidence_responsibility_matrix.csv",
      "source_verified": true
    },
    {
      "base_tree_sha256": "fe00e617cfc99bf40eb44b13b66e4c14f08f2c764dd32820f03fd162f9049896",
      "expected_sha256": "fe00e617cfc99bf40eb44b13b66e4c14f08f2c764dd32820f03fd162f9049896",
      "filesystem_sha256": "fe00e617cfc99bf40eb44b13b66e4c14f08f2c764dd32820f03fd162f9049896",
      "source_order": 7,
      "source_relative_path": "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006.py",
      "source_verified": true
    },
    {
      "base_tree_sha256": "359c666541602458b3ea6a023be95ea06205f8580ff71d371c25306715f558d6",
      "expected_sha256": "359c666541602458b3ea6a023be95ea06205f8580ff71d371c25306715f558d6",
      "filesystem_sha256": "359c666541602458b3ea6a023be95ea06205f8580ff71d371c25306715f558d6",
      "source_order": 8,
      "source_relative_path": "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006_v1/covapie_admit_001_to_006_runtime_manifest.json",
      "source_verified": true
    },
    {
      "base_tree_sha256": "e63c1b83fe245031ecdefa6b3387086b2aba8d72ef50189be17b9874e8f18196",
      "expected_sha256": "e63c1b83fe245031ecdefa6b3387086b2aba8d72ef50189be17b9874e8f18196",
      "filesystem_sha256": "e63c1b83fe245031ecdefa6b3387086b2aba8d72ef50189be17b9874e8f18196",
      "source_order": 9,
      "source_relative_path": "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006_v1/covapie_admit_001_to_006_runtime_issue_inventory.csv",
      "source_verified": true
    },
    {
      "base_tree_sha256": "6fd3727234b4b3f637fa5812c78421ec944238518702bc7f9d0d57a654d9a46d",
      "expected_sha256": "6fd3727234b4b3f637fa5812c78421ec944238518702bc7f9d0d57a654d9a46d",
      "filesystem_sha256": "6fd3727234b4b3f637fa5812c78421ec944238518702bc7f9d0d57a654d9a46d",
      "source_order": 10,
      "source_relative_path": "src/covalent_ext/covapie_bulk_download_admission_admit_006_rule_logic_interface.py",
      "source_verified": true
    }
  ],
  "source_structural_checks_before_first_explicit_content_read": true,
  "stage": "covapie_bulk_download_admission_admit_007_rule_logic_interface_v1",
  "step": "ADMIT_007 standalone evaluator interface v1",
  "stop_boundaries": [
    "no_unified_adapter",
    "no_runtime_modification",
    "no_admit_007_registration",
    "no_admit_008",
    "no_provider_mapping",
    "no_real_candidate_evaluation",
    "no_raw_network_download",
    "no_model_forward_loss_training"
  ],
  "truth_matrix_group_counts": {
    "canonical": 3,
    "context": 12,
    "empty_syntax": 11,
    "scalar_type": 6,
    "unknown": 5
  },
  "truth_matrix_pass_count": 37,
  "truth_matrix_row_count": 37,
  "unified_engine_coverage_issue_still_includes_admit_007": true,
  "validation_failures": []
}
""")



CHECKER_ENUM_MEMBERS = (
    "explicit_structure_bond_record",
    "explicit_curated_covalent_annotation",
    "distance_only_inference",
)
CHECKER_ALLOWED_CONTEXT = (
    "explicit_structure_bond_record",
    "explicit_curated_covalent_annotation",
)
CHECKER_SCALAR_SYNTAX = r"[a-z][a-z0-9_]{0,63}"
CHECKER_SCALAR_REASONS = (
    "COVALENT_EVENT_EVIDENCE_SOURCE_TYPE_INVALID",
    "COVALENT_EVENT_EVIDENCE_SOURCE_EMPTY",
    "COVALENT_EVENT_EVIDENCE_SOURCE_NON_ASCII",
    "COVALENT_EVENT_EVIDENCE_SOURCE_SYNTAX_INVALID",
    "COVALENT_EVENT_EVIDENCE_SOURCE_UNKNOWN",
)
CHECKER_CONTEXT_REASONS = (
    "ALLOWED_COVALENT_EVIDENCE_CLASSES_TYPE_INVALID",
    "ALLOWED_COVALENT_EVIDENCE_CLASSES_CONTENT_INVALID",
)
CHECKER_BLOCKED_REASON = "DISTANCE_ONLY_INFERENCE_NOT_ADMISSIBLE"
CHECKER_CANDIDATE_FIELDS = ("covalent_event_evidence_source",)
CHECKER_CONTEXT_ITEMS = ("allowed_covalent_evidence_classes",)
CHECKER_RESULT_FIELDS = (
    "admission_rule_id",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "canonical_covalent_event_evidence_source",
    "validated_candidate_fields",
    "consumed_candidate_fields",
    "consumed_context_items",
    "evaluator_io_used",
)
CHECKER_TRUTH_COLUMNS = (
    "case_id", "case_group", "scalar_input_kind", "scalar_input_display",
    "context_input_kind", "context_input_display", "expected_outcome", "expected_reason",
    "observed_outcome", "observed_reason", "expected_canonical_evidence_source",
    "observed_canonical_evidence_source", "expected_validated_candidate_fields",
    "observed_validated_candidate_fields", "consumed_candidate_fields",
    "consumed_context_items", "evaluator_io_used", "expected_full_result",
    "observed_full_result", "independent_oracle_full_result", "case_passed",
)
CHECKER_GROUP_COUNTS = {
    "canonical": 3,
    "scalar_type": 6,
    "empty_syntax": 11,
    "unknown": 5,
    "context": 12,
}


@dataclass(frozen=True)
class CheckerExpectedResult:
    admission_rule_id: str
    outcome: str
    passed: bool
    blocks_candidate: bool
    reason: str
    canonical_covalent_event_evidence_source: str
    validated_candidate_fields: tuple[tuple[str, str], ...]
    consumed_candidate_fields: tuple[str, ...]
    consumed_context_items: tuple[str, ...]
    evaluator_io_used: bool


class _StringSubclass(str):
    """Checker-owned exact-str-subclass negative."""


def _assert(condition: bool, message: str) -> None:
    if condition is not True:
        raise AssertionError(message)


def _result_tuple(result: interface.Admit007EvaluationResult) -> tuple[Any, ...]:
    return tuple(getattr(result, field.name) for field in fields(result))


def _checker_bool(value: bool) -> str:
    return "true" if value else "false"


def _checker_scalar_state(scalar: object) -> tuple[str, str, str]:
    if type(scalar) is not str:
        return "invalid", "", CHECKER_SCALAR_REASONS[0]
    elif len(scalar) == 0:
        return "invalid", "", CHECKER_SCALAR_REASONS[1]
    elif not all(ord(character) < 128 for character in scalar):
        return "invalid", "", CHECKER_SCALAR_REASONS[2]
    elif re.fullmatch(CHECKER_SCALAR_SYNTAX, scalar, flags=re.ASCII) is None:
        return "invalid", "", CHECKER_SCALAR_REASONS[3]
    elif scalar not in CHECKER_ENUM_MEMBERS:
        return "unknown", "", CHECKER_SCALAR_REASONS[4]
    return "canonical", scalar, ""


def _checker_context_state(context: object) -> tuple[bool, str]:
    if type(context) is not tuple:
        return False, CHECKER_CONTEXT_REASONS[0]
    if (
        len(context) != 2
        or type(context[0]) is not str
        or type(context[1]) is not str
        or context != CHECKER_ALLOWED_CONTEXT
    ):
        return False, CHECKER_CONTEXT_REASONS[1]
    return True, ""


def _checker_oracle(scalar: object, context: object) -> CheckerExpectedResult:
    scalar_classification, canonical, scalar_reason = _checker_scalar_state(scalar)
    context_valid, context_reason = _checker_context_state(context)
    if scalar_classification != "canonical":
        outcome, reason = "invalid", scalar_reason
    elif not context_valid:
        outcome, reason = "invalid", context_reason
    elif canonical == "distance_only_inference":
        outcome, reason = "blocked", CHECKER_BLOCKED_REASON
    else:
        outcome, reason = "passed", ""
    validated = () if canonical == "" else ((CHECKER_CANDIDATE_FIELDS[0], canonical),)
    return CheckerExpectedResult(
        "ADMIT_007", outcome, outcome == "passed", outcome != "passed", reason,
        canonical, validated, CHECKER_CANDIDATE_FIELDS, CHECKER_CONTEXT_ITEMS, False,
    )


def _committed_oracle_result(scalar: object, context: object) -> CheckerExpectedResult:
    classification = committed_oracle.classify_admit_006_admit_007_evidence_design(
        scalar, context
    )
    canonical = (
        classification.scalar.canonical_value
        if classification.scalar.classification == "canonical"
        else ""
    )
    validated = () if canonical == "" else ((CHECKER_CANDIDATE_FIELDS[0], canonical),)
    outcome = classification.admit_007
    return CheckerExpectedResult(
        "ADMIT_007", outcome.outcome, outcome.passed, outcome.blocks_candidate,
        outcome.reason, canonical, validated, CHECKER_CANDIDATE_FIELDS,
        CHECKER_CONTEXT_ITEMS, False,
    )


def _checker_result_dict(result: CheckerExpectedResult) -> dict[str, Any]:
    return {name: getattr(result, name) for name in CHECKER_RESULT_FIELDS}


def _checker_display(value: object) -> str:
    if type(value) is str:
        return json.dumps(value, ensure_ascii=True)
    if isinstance(value, _StringSubclass):
        return f"str_subclass:{json.dumps(str(value))}"
    if type(value) in (tuple, list):
        return f"{type(value).__name__}:{json.dumps(list(value), ensure_ascii=True)}"
    if type(value) in (set, frozenset):
        return f"{type(value).__name__}:{json.dumps(sorted(value), ensure_ascii=True)}"
    if type(value) is dict:
        return f"dict:{json.dumps(value, ensure_ascii=True, sort_keys=True)}"
    return f"{type(value).__name__}:{repr(value)}"


def _checker_predecessor_display(value: object) -> str:
    if type(value) is str:
        return json.dumps(value, ensure_ascii=True)
    if isinstance(value, _StringSubclass):
        return f"str_subclass:{json.dumps(str(value))}"
    return f"{type(value).__name__}:{repr(value)}"


def _checker_truth_definitions() -> tuple[tuple[str, str, object, str, object], ...]:
    exact = CHECKER_ALLOWED_CONTEXT
    scalar_cases: tuple[tuple[str, str, object], ...] = (
        ("canonical_structure_bond", "canonical", CHECKER_ENUM_MEMBERS[0]),
        ("canonical_curated_annotation", "canonical", CHECKER_ENUM_MEMBERS[1]),
        ("canonical_distance_only", "canonical", CHECKER_ENUM_MEMBERS[2]),
        ("type_none", "scalar_type", None), ("type_int", "scalar_type", 7),
        ("type_bool", "scalar_type", True),
        ("type_str_subclass", "scalar_type", _StringSubclass(CHECKER_ENUM_MEMBERS[0])),
        ("type_list", "scalar_type", [CHECKER_ENUM_MEMBERS[0]]),
        ("type_mapping", "scalar_type", {"value": CHECKER_ENUM_MEMBERS[0]}),
        ("empty", "empty_syntax", ""), ("whitespace_only", "empty_syntax", " "),
        ("leading_whitespace", "empty_syntax", " explicit_structure_bond_record"),
        ("trailing_whitespace", "empty_syntax", "explicit_structure_bond_record "),
        ("uppercase", "empty_syntax", "Explicit_structure_bond_record"),
        ("hyphen", "empty_syntax", "explicit-structure-bond-record"),
        ("dot", "empty_syntax", "explicit.structure"),
        ("slash", "empty_syntax", "explicit/structure"),
        ("non_ascii", "empty_syntax", "explicit_évidence"),
        ("over_length", "empty_syntax", "a" * 65),
        ("leading_digit", "empty_syntax", "1explicit"),
        ("unknown_valid", "unknown", "unregistered_value"),
        ("unknown_explicit_looking", "unknown", "explicit_database_bond"),
        ("unknown_manual_review", "unknown", "manual_review"),
        ("unknown_other", "unknown", "other"),
        ("unknown_unknown", "unknown", "unknown"),
    )
    context_cases: tuple[tuple[str, object], ...] = (
        ("context_exact_tuple", exact), ("context_none", None),
        ("context_list", list(exact)), ("context_set", set(exact)),
        ("context_frozenset", frozenset(exact)),
        ("context_wrong_order", tuple(reversed(exact))),
        ("context_missing_member", exact[:1]),
        ("context_duplicate", (exact[0], exact[0])),
        ("context_distance_only", (*exact, CHECKER_ENUM_MEMBERS[2])),
        ("context_unknown", (*exact, "unknown")),
        ("context_str_subclass", (_StringSubclass(exact[0]), exact[1])),
        ("context_extra_member", (*exact, "explicit_database_bond")),
    )
    definitions = [
        (case_id, group, scalar, "exact_tuple", exact)
        for case_id, group, scalar in scalar_cases
    ]
    definitions.extend(
        (case_id, "context", CHECKER_ENUM_MEMBERS[0], case_id.removeprefix("context_"), context)
        for case_id, context in context_cases
    )
    return tuple(definitions)


def _checker_expected_disk_rows() -> tuple[dict[str, str], ...]:
    rows = []
    for index, (name, group, scalar, context_kind, context) in enumerate(
        _checker_truth_definitions(), 1
    ):
        result = _checker_oracle(scalar, context)
        full_json = json.dumps(_checker_result_dict(result), separators=(",", ":"))
        validated_json = json.dumps(result.validated_candidate_fields, separators=(",", ":"))
        rows.append({
            "case_id": f"CASE_{index:03d}_{name}",
            "case_group": group,
            "scalar_input_kind": type(scalar).__name__,
            "scalar_input_display": _checker_display(scalar),
            "context_input_kind": context_kind,
            "context_input_display": _checker_display(context),
            "expected_outcome": result.outcome,
            "expected_reason": result.reason,
            "observed_outcome": result.outcome,
            "observed_reason": result.reason,
            "expected_canonical_evidence_source": result.canonical_covalent_event_evidence_source,
            "observed_canonical_evidence_source": result.canonical_covalent_event_evidence_source,
            "expected_validated_candidate_fields": validated_json,
            "observed_validated_candidate_fields": validated_json,
            "consumed_candidate_fields": "|".join(result.consumed_candidate_fields),
            "consumed_context_items": "|".join(result.consumed_context_items),
            "evaluator_io_used": _checker_bool(result.evaluator_io_used),
            "expected_full_result": full_json,
            "observed_full_result": full_json,
            "independent_oracle_full_result": full_json,
            "case_passed": "true",
        })
    return tuple(rows)


def _checker_expected_predecessor_rows() -> tuple[dict[str, str], ...]:
    rows = []
    for index, (name, group, scalar, context_kind, context) in enumerate(
        _checker_truth_definitions(), 1
    ):
        scalar_classification, canonical, scalar_reason = _checker_scalar_state(scalar)
        context_valid, context_reason = _checker_context_state(context)
        result = _checker_oracle(scalar, context)
        rows.append({
            "case_id": f"CASE_{index:03d}_{name}",
            "case_group": group,
            "scalar_input_kind": type(scalar).__name__,
            "scalar_input_display": _checker_predecessor_display(scalar),
            "context_input_kind": context_kind,
            "expected_scalar_classification": scalar_classification,
            "expected_canonical_value": canonical,
            "expected_scalar_reason": scalar_reason,
            "expected_context_valid": _checker_bool(context_valid),
            "expected_context_reason": context_reason,
            "expected_admit_007_outcome": result.outcome,
            "expected_admit_007_reason": result.reason,
            "normative_not_observed": "true",
            "case_passed": "true",
        })
    return tuple(rows)


def _result_values(
    outcome: str, reason: str, canonical: str,
    validated: tuple[tuple[str, str], ...] | None = None,
) -> dict[str, Any]:
    expected = () if canonical == "" else ((interface.CANDIDATE_FIELDS[0], canonical),)
    return {
        "admission_rule_id": "ADMIT_007",
        "outcome": outcome,
        "passed": outcome == "passed",
        "blocks_candidate": outcome != "passed",
        "reason": reason,
        "canonical_covalent_event_evidence_source": canonical,
        "validated_candidate_fields": expected if validated is None else validated,
        "consumed_candidate_fields": interface.CANDIDATE_FIELDS,
        "consumed_context_items": interface.CONTEXT_ITEMS,
        "evaluator_io_used": False,
    }


def _check_public_contract() -> int:
    signature = inspect.signature(interface.evaluate_admit_007)
    parameters = tuple(signature.parameters.values())
    _assert(
        tuple(parameter.name for parameter in parameters)
        == ("covalent_event_evidence_source", "allowed_covalent_evidence_classes"),
        "public parameter names",
    )
    _assert(all(parameter.default is inspect.Parameter.empty for parameter in parameters), "defaults forbidden")
    _assert(
        all(parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD for parameter in parameters),
        "parameter kinds",
    )
    _assert(signature.return_annotation == "Admit007EvaluationResult", "return annotation")
    _assert(tuple(field.name for field in fields(interface.Admit007EvaluationResult)) == CHECKER_RESULT_FIELDS, "Exact10 result fields")
    _assert(interface.OUTCOME_VOCABULARY == ("passed", "blocked", "invalid"), "outcome vocabulary")
    _assert(interface.CANONICAL_ENUM_MEMBERS == CHECKER_ENUM_MEMBERS, "Exact3 enum")
    _assert(interface.ALLOWED_COVALENT_EVIDENCE_CLASSES == CHECKER_ALLOWED_CONTEXT, "Exact2 context")
    _assert(interface.SCALAR_REASONS == CHECKER_SCALAR_REASONS, "scalar reasons")
    _assert(interface.CONTEXT_REASONS == CHECKER_CONTEXT_REASONS, "context reasons")
    _assert(interface.BLOCKED_REASON == CHECKER_BLOCKED_REASON, "blocked reason")
    _assert("COVALENT_EVENT_EVIDENCE_NOT_EXPLICIT" not in interface.REASON_VOCABULARY, "ADMIT_006 reason leaked")
    _assert("distance_only_inference_not_admissible" not in interface.REASON_VOCABULARY, "historical reason leaked")
    _assert(interface.CANDIDATE_FIELDS == CHECKER_CANDIDATE_FIELDS, "candidate fields")
    _assert(interface.CONTEXT_ITEMS == CHECKER_CONTEXT_ITEMS, "context items")
    _assert(interface.TRUTH_COLUMNS == CHECKER_TRUTH_COLUMNS, "truth columns")

    result = interface.evaluate_admit_007(
        interface.CANONICAL_ENUM_MEMBERS[0], interface.ALLOWED_COVALENT_EVIDENCE_CLASSES
    )
    try:
        result.reason = "changed"  # type: ignore[misc]
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("result dataclass is mutable")

    conflicts = (
        _result_values("passed", "", "distance_only_inference"),
        _result_values("blocked", interface.BLOCKED_REASON, "explicit_structure_bond_record"),
        _result_values("invalid", interface.SCALAR_REASONS[0], "explicit_structure_bond_record"),
        _result_values("invalid", interface.CONTEXT_REASONS[0], ""),
        _result_values("invalid", interface.CONTEXT_REASONS[1], "explicit_structure_bond_record", ()),
        _result_values("invalid", interface.SCALAR_REASONS[4], "", (("covalent_event_evidence_source", "unknown"),)),
        _result_values("invalid", "", ""),
        _result_values("blocked", "", "distance_only_inference"),
    )
    for values in conflicts:
        try:
            interface.Admit007EvaluationResult(**values)
        except (TypeError, ValueError):
            continue
        raise AssertionError("semantic result conflict accepted")
    return len(conflicts)


def _check_exact37_semantics() -> None:
    definitions = _checker_truth_definitions()
    _assert(len(definitions) == 37, "Exact37 definition count")
    counts = {group: sum(case[1] == group for case in definitions) for group in (
        "canonical", "scalar_type", "empty_syntax", "unknown", "context"
    )}
    _assert(counts == CHECKER_GROUP_COUNTS, "Exact37 groups")
    for _, _, scalar, _, context in definitions:
        before = (repr(scalar), repr(context))
        first = interface.evaluate_admit_007(scalar, context)
        second = interface.evaluate_admit_007(scalar, context)
        _assert(first == second, "evaluator not deterministic")
        _assert((repr(scalar), repr(context)) == before, "input mutation")
        expected = _checker_oracle(scalar, context)
        oracle_expected = _committed_oracle_result(scalar, context)
        expected_tuple = tuple(getattr(expected, name) for name in CHECKER_RESULT_FIELDS)
        _assert(_result_tuple(first) == expected_tuple, "independent oracle mismatch")
        _assert(
            tuple(getattr(oracle_expected, name) for name in CHECKER_RESULT_FIELDS)
            == expected_tuple,
            "committed oracle mismatch",
        )
    precedence = interface.evaluate_admit_007("UNKNOWN", None)
    _assert(precedence.reason == CHECKER_SCALAR_REASONS[3], "scalar/context precedence")
    distance = interface.evaluate_admit_007("distance_only_inference", CHECKER_ALLOWED_CONTEXT)
    _assert(distance.outcome == "blocked" and distance.reason == CHECKER_BLOCKED_REASON, "distance-only classification")
    for explicit in CHECKER_ALLOWED_CONTEXT:
        observed = interface.evaluate_admit_007(explicit, CHECKER_ALLOWED_CONTEXT)
        _assert(observed.outcome == "passed" and observed.reason == "", "explicit classification")


def _check_scalar_short_circuit() -> None:
    original = interface._validate_context

    def forbidden(_: object) -> str:
        raise AssertionError("context validator reached after scalar failure")

    interface._validate_context = forbidden
    try:
        observed = interface.evaluate_admit_007(None, object())
    finally:
        interface._validate_context = original
    _assert(observed.reason == CHECKER_SCALAR_REASONS[0], "scalar short-circuit reason")


def _verify_exact37_views(
    predecessor_rows: tuple[dict[str, str], ...],
    disk_rows: tuple[dict[str, str], ...],
) -> None:
    definitions = _checker_truth_definitions()
    expected_predecessor = _checker_expected_predecessor_rows()
    expected_disk = _checker_expected_disk_rows()
    _assert(len(definitions) == len(expected_predecessor) == len(expected_disk) == 37, "independent Exact37 shape")
    _assert(len(predecessor_rows) == 37, "committed predecessor Exact37 shape")
    _assert(len(disk_rows) == 37, "materialized disk Exact37 shape")
    for index, (definition, expected_result_row, expected_prior, prior, disk) in enumerate(
        zip(definitions, expected_disk, expected_predecessor, predecessor_rows, disk_rows, strict=True), 1
    ):
        _assert(
            all(prior.get(key) == value for key, value in expected_prior.items()),
            f"committed predecessor mismatch at row {index}",
        )
        _assert(tuple(disk) == CHECKER_TRUTH_COLUMNS, f"disk truth columns at row {index}")
        _assert(disk == expected_result_row, f"materialized disk mismatch at row {index}")
        _, _, scalar, _, context = definition
        observed = interface.evaluate_admit_007(scalar, context)
        expected = _checker_oracle(scalar, context)
        oracle_expected = _committed_oracle_result(scalar, context)
        _assert(
            _result_tuple(observed)
            == tuple(getattr(expected, name) for name in CHECKER_RESULT_FIELDS),
            f"production evaluator mismatch at row {index}",
        )
        _assert(
            tuple(getattr(oracle_expected, name) for name in CHECKER_RESULT_FIELDS)
            == tuple(getattr(expected, name) for name in CHECKER_RESULT_FIELDS),
            f"committed oracle mismatch at row {index}",
        )


def _verify_issue_inventory_preservation(
    observed_rows: list[dict[str, str]],
    predecessor_rows: tuple[dict[str, str], ...],
) -> None:
    _assert(len(observed_rows) == len(predecessor_rows) == 11, "Exact11 issue shape")
    _assert(observed_rows == [dict(row) for row in predecessor_rows], "issue inventory not preserved")
    coverage = [
        row for row in observed_rows
        if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
    ]
    _assert(len(coverage) == 1, "unified coverage issue identity")
    _assert(coverage[0]["status"] == "open", "unified coverage issue status")
    _assert(coverage[0]["blocking_scope"] == "unified_admission_engine", "unified coverage issue scope")
    _assert(
        coverage[0]["affected_rules"]
        == "ADMIT_007|ADMIT_008|ADMIT_009|ADMIT_010|ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015",
        "unified coverage issue rules",
    )
    _assert(
        coverage[0]["integration_transition"]
        == "admit_006_implemented_and_removed_from_open_coverage_scope",
        "unified coverage predecessor transition",
    )


def _called_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                names.add(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                names.add(child.func.attr)
    return names


def _pure_closure(tree: ast.Module, root: str) -> set[str]:
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    banned = {
        "classify_admit_006_admit_007_evidence_design", "build_interface_state",
        "run_covapie_bulk_download_admission_admit_007_rule_logic_interface_v1",
        "build_frozen_source_snapshot", "_git", "open", "read", "read_bytes", "read_text",
        "write", "write_bytes", "write_text", "run", "Popen", "system", "urlopen", "request",
        "evaluate_rule", "register", "provider",
    }
    pending = [root]
    closure: set[str] = set()
    while pending:
        name = pending.pop()
        if name in closure:
            continue
        _assert(name in functions, f"missing call-graph node: {name}")
        closure.add(name)
        calls = _called_names(functions[name])
        _assert(not calls.intersection(banned), f"banned evaluator call: {calls.intersection(banned)}")
        pending.extend(call for call in calls if call in functions)
    return closure


CHECKER_INDEPENDENT_FUNCTIONS = (
    "_checker_bool",
    "_checker_scalar_state",
    "_checker_context_state",
    "_checker_oracle",
    "_checker_result_dict",
    "_checker_display",
    "_checker_predecessor_display",
    "_checker_truth_definitions",
    "_checker_expected_disk_rows",
    "_checker_expected_predecessor_rows",
)


def _assert_checker_independent_ast(tree: ast.Module) -> None:
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    banned_names = {
        "interface",
        "_truth_definitions",
        "_independent_expected",
        "_truth_rows",
        "classify_admit_006_admit_007_evidence_design",
    }
    for name in CHECKER_INDEPENDENT_FUNCTIONS:
        _assert(name in functions, f"missing checker-independent function: {name}")
        for node in ast.walk(functions[name]):
            if isinstance(node, ast.Name):
                _assert(node.id not in banned_names, f"checker-independent name leak in {name}: {node.id}")
            if isinstance(node, ast.Attribute):
                _assert(node.attr not in banned_names, f"checker-independent attribute leak in {name}: {node.attr}")
                root = node.value
                while isinstance(root, ast.Attribute):
                    root = root.value
                _assert(
                    not isinstance(root, ast.Name) or root.id != "interface",
                    f"checker-independent interface reference in {name}",
                )


def _check_checker_independent_ast() -> None:
    checker_tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    _assert_checker_independent_ast(checker_tree)


def _check_evaluator_call_graph() -> None:
    production_path = REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_007_rule_logic_interface.py"
    tree = ast.parse(production_path.read_text(encoding="utf-8"))
    closure = _pure_closure(tree, "evaluate_admit_007")
    _assert(closure == {"evaluate_admit_007", "_validate_scalar", "_validate_context", "_result"}, "unexpected evaluator closure")
    imports = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module.split(".")[0])
    standard = set(getattr(sys, "stdlib_module_names", ())) | {"__future__"}
    _assert(all(name in standard for name in imports), "non-stdlib production import")
    for bad in (
        "classify_admit_006_admit_007_evidence_design(x)", "read_bytes(x)", "build_interface_state()"
    ):
        synthetic = ast.parse(f"def evaluate_admit_007(x):\n    return helper(x)\ndef helper(x):\n    return {bad}\n")
        try:
            _pure_closure(synthetic, "evaluate_admit_007")
        except AssertionError:
            continue
        raise AssertionError("call-graph negative accepted")


def _check_snapshot_and_state() -> dict[str, Any]:
    original_git = interface._git
    structural_count = 0
    first_content_read_after = -1

    def observed_git(arguments: Any, repo_root: Path, *, text: bool = True) -> Any:
        nonlocal structural_count, first_content_read_after
        if tuple(arguments[:2]) == ("ls-files", "--error-unmatch"):
            structural_count += 1
        if arguments[0] == "show" and len(arguments) == 2 and ":" in arguments[1] and first_content_read_after == -1:
            first_content_read_after = structural_count
        return original_git(arguments, repo_root, text=text)

    interface._git = observed_git
    try:
        snapshot = interface.build_frozen_source_snapshot()
    finally:
        interface._git = original_git
    _assert(structural_count == first_content_read_after == len(interface.SOURCE_PATHS), "structural checks did not precede bytes")
    _assert(interface.validate_frozen_source_snapshot(snapshot), "source snapshot invalid")

    first = snapshot.records[0]
    bad_record = replace(first, content_bytes=first.content_bytes + b"tamper")
    bad_snapshot = interface.FrozenSourceSnapshot((bad_record, *snapshot.records[1:]))
    _assert(not interface.validate_frozen_source_snapshot(bad_snapshot), "source SHA mismatch accepted")

    def non_descendant(arguments: Any, repo_root: Path, *, text: bool = True) -> Any:
        if tuple(arguments[:2]) == ("merge-base", "--is-ancestor"):
            empty = "" if text else b""
            return subprocess.CompletedProcess(arguments, 1, empty, empty)
        return original_git(arguments, repo_root, text=text)

    interface._git = non_descendant
    try:
        try:
            interface.build_frozen_source_snapshot()
        except ValueError as error:
            _assert("not an ancestor" in str(error), "wrong non-descendant failure")
        else:
            raise AssertionError("non-descendant base accepted")
    finally:
        interface._git = original_git

    state = interface.build_interface_state(snapshot)
    predecessor_record = next(
        record for record in snapshot.records
        if record.relative_path == interface.PREDECESSOR_TRUTH_PATH
    )
    predecessor_reader = csv.DictReader(
        io.StringIO(predecessor_record.content_bytes.decode("utf-8"), newline="")
    )
    predecessor_rows = tuple(dict(row) for row in predecessor_reader)
    disk_reader = csv.DictReader(
        io.StringIO(
            (REPO_ROOT / interface.DEFAULT_OUTPUT_ROOT / interface.TRUTH_FILENAME).read_text(),
            newline="",
        )
    )
    disk_rows = tuple(dict(row) for row in disk_reader)
    _verify_exact37_views(predecessor_rows, disk_rows)
    _assert(tuple(state["truth_rows"]) == _checker_expected_disk_rows(), "production materialized truth drift")
    _assert(len(state["contract_rows"]) == 28, "contract count")
    _assert(len(state["truth_rows"]) == 37 and all(row["case_passed"] == "true" for row in state["truth_rows"]), "truth rows")
    _assert(len(state["source_audit_rows"]) == len(interface.SOURCE_PATHS), "source audit count")
    _assert(
        state["source_audit_rows"][8]["boundary_necessity"]
        == "ordered Exact11 issue inventory preservation baseline",
        "source boundary row 9 preservation wording",
    )
    _assert(len(state["issue_rows"]) == 11, "Exact11 issue count")
    coverage = [row for row in state["issue_rows"] if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]
    enum_issue = [row for row in state["issue_rows"] if row["issue_id"] == "COVALENT_EVIDENCE_ENUM_UNRESOLVED"]
    predecessor_issues = interface._validate_predecessors(snapshot)["issue_rows"]
    _verify_issue_inventory_preservation(state["issue_rows"], predecessor_issues)
    _assert(len(coverage) == 1, "coverage issue identity")
    _assert(len(enum_issue) == 1 and enum_issue[0]["status"] == "resolved", "enum issue changed")
    _assert(state["readiness"] == interface.READINESS, "readiness mismatch")
    _assert(state["readiness"]["ready_for_training"] is False, "training overclaim")
    return state


def _validate_output_tree(
    root: Path,
    expected: dict[str, bytes],
    *,
    enforce_frozen_hashes: bool = True,
) -> None:
    _assert(root.exists() and root.is_dir() and not root.is_symlink(), "unsafe output root")
    entries = tuple(root.iterdir())
    _assert({entry.name for entry in entries} == set(interface.OUTPUT_FILES), "output set mismatch")
    _assert(all(entry.is_file() and not entry.is_symlink() for entry in entries), "unsafe output entry")
    for name, payload in expected.items():
        _assert((root / name).read_bytes() == payload, f"output mismatch: {name}")
    manifest = json.loads((root / interface.MANIFEST_FILENAME).read_text())
    _assert(type(manifest) is dict, "manifest type")
    _assert(set(manifest) == set(EXPECTED_MANIFEST), "exact manifest key set")
    _assert(manifest == EXPECTED_MANIFEST, "full expected manifest mismatch")
    _assert(manifest["output_files"] == list(interface.OUTPUT_FILES), "manifest output set")
    _assert(manifest["output_file_count"] == 6, "manifest output count")
    _assert(manifest["readiness"] == interface.READINESS, "manifest readiness")
    _assert(manifest["all_checks_passed"] is True, "manifest overclaim")
    _assert(interface.MANIFEST_FILENAME not in manifest["output_sha256"], "manifest self hash")
    for name in interface.CSV_OUTPUTS:
        digest = hashlib.sha256((root / name).read_bytes()).hexdigest()
        _assert(manifest["output_sha256"].get(name) == digest, f"manifest hash: {name}")
    if enforce_frozen_hashes:
        hashes = {
            name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in interface.OUTPUT_FILES
        }
        _assert(hashes == EXPECTED_OUTPUT_SHA256, "frozen output hashes")


def _expect_invalid_output(root: Path, expected: dict[str, bytes]) -> None:
    try:
        _validate_output_tree(root, expected, enforce_frozen_hashes=False)
    except (AssertionError, OSError, ValueError, json.JSONDecodeError):
        return
    raise AssertionError("mutated output accepted")


def _check_materialization(state: dict[str, Any]) -> dict[str, str]:
    expected, _ = interface._payloads(state)
    output_root = REPO_ROOT / interface.DEFAULT_OUTPUT_ROOT
    _validate_output_tree(output_root, expected)
    with tempfile.TemporaryDirectory(prefix="covapie-admit007-check-") as temporary:
        temporary_root = Path(temporary)
        root = temporary_root / "outputs"
        interface.run_covapie_bulk_download_admission_admit_007_rule_logic_interface_v1(root)
        first = {name: (root / name).read_bytes() for name in interface.OUTPUT_FILES}
        interface.run_covapie_bulk_download_admission_admit_007_rule_logic_interface_v1(root)
        second = {name: (root / name).read_bytes() for name in interface.OUTPUT_FILES}
        _assert(first == second == expected, "double materialization differs")
        for mutation in ("missing", "extra", "tamper", "overclaim", "truth_rehash"):
            victim = temporary_root / mutation
            shutil.copytree(root, victim)
            if mutation == "missing":
                (victim / interface.CONTRACT_FILENAME).unlink()
            elif mutation == "extra":
                (victim / "extra.txt").write_text("extra")
            elif mutation == "tamper":
                (victim / interface.TRUTH_FILENAME).write_bytes(b"tampered\n")
            elif mutation == "overclaim":
                path = victim / interface.MANIFEST_FILENAME
                manifest = json.loads(path.read_text())
                manifest["readiness"]["ready_for_training"] = True
                path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
            else:
                truth_path = victim / interface.TRUTH_FILENAME
                rows = list(csv.DictReader(io.StringIO(truth_path.read_text(), newline="")))
                rows[0]["observed_outcome"] = "blocked"
                stream = io.StringIO(newline="")
                writer = csv.DictWriter(stream, fieldnames=interface.TRUTH_COLUMNS, lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
                truth_path.write_text(stream.getvalue())
                manifest_path = victim / interface.MANIFEST_FILENAME
                manifest = json.loads(manifest_path.read_text())
                manifest["output_sha256"][interface.TRUTH_FILENAME] = hashlib.sha256(truth_path.read_bytes()).hexdigest()
                manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
            _expect_invalid_output(victim, expected)

        unsafe = temporary_root / "symlink"
        unsafe.mkdir()
        outside = temporary_root / "outside"
        outside.write_text("unchanged")
        (unsafe / interface.CONTRACT_FILENAME).symlink_to(outside)
        try:
            interface.run_covapie_bulk_download_admission_admit_007_rule_logic_interface_v1(unsafe)
        except ValueError:
            pass
        else:
            raise AssertionError("symlink output accepted")
        _assert(outside.read_text() == "unchanged", "symlink victim modified")
    _assert(not tuple(output_root.glob("*.tmp")) and not tuple(output_root.glob("*.part")), "temporary residue")
    hashes = {
        name: hashlib.sha256((output_root / name).read_bytes()).hexdigest()
        for name in interface.OUTPUT_FILES
    }
    _assert(hashes == EXPECTED_OUTPUT_SHA256, "frozen output SHA256 mismatch")
    return hashes


def _check_generated_preservation_wording(state: dict[str, Any]) -> None:
    expected = "ordered Exact11 issue inventory preservation baseline"
    stale = "one-row coverage transition"
    _assert(state["source_audit_rows"][8]["boundary_necessity"] == expected, "row 9 wording")
    output_root = REPO_ROOT / interface.DEFAULT_OUTPUT_ROOT
    paths = tuple(output_root / name for name in interface.OUTPUT_FILES) + (
        REPO_ROOT / "docs/covapie_bulk_download_admission_admit_007_rule_logic_interface_v1_summary.md",
    )
    _assert(all(stale not in path.read_text() for path in paths), "stale transition wording remains")


def _silent_import(command_text: str) -> None:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(SRC_ROOT)
    completed = subprocess.run(
        [sys.executable, "-c", command_text], cwd=REPO_ROOT, env=environment,
        capture_output=True, text=True, check=False,
    )
    _assert(completed.returncode == 0, "import failed")
    _assert(completed.stdout == "" and completed.stderr == "", "import emitted output")


def _check_silent_imports() -> None:
    _silent_import("import covalent_ext.covapie_bulk_download_admission_admit_007_rule_logic_interface")
    checker = REPO_ROOT / "scripts/check_covapie_bulk_download_admission_admit_007_rule_logic_interface_v1.py"
    command = (
        "import importlib.util,sys;"
        f"s=importlib.util.spec_from_file_location('admit007_checker',{str(checker)!r});"
        "m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)"
    )
    _silent_import(command)


def main() -> int:
    invariant_count = _check_public_contract()
    _check_exact37_semantics()
    _check_scalar_short_circuit()
    _check_checker_independent_ast()
    _check_evaluator_call_graph()
    state = _check_snapshot_and_state()
    output_hashes = _check_materialization(state)
    _check_generated_preservation_wording(state)
    _check_silent_imports()

    _assert(len(state["truth_rows"]) == 37, "stdout truth assertion")
    print("admit_007_truth_matrix=37/37")
    print("admit_007_truth_groups=canonical:3,scalar_type:6,empty_syntax:11,unknown:5,context:12")
    _assert(len(state["contract_rows"]) == 28, "stdout contract assertion")
    print("admit_007_contract=28/28")
    _assert(len(state["source_audit_rows"]) == len(interface.SOURCE_PATHS), "stdout source assertion")
    print(f"source_boundary={len(interface.SOURCE_PATHS)}/{len(interface.SOURCE_PATHS)}")
    _assert(len(state["issue_rows"]) == 11, "stdout issue assertion")
    print("exact11_issue_inventory=11/11")
    _assert(invariant_count == 8, "stdout invariant assertion")
    print("direct_result_semantic_invariants=8/8")
    _assert(state["readiness"]["ready_for_training"] is False, "stdout readiness assertion")
    print("ready_for_training=false")
    for name in interface.OUTPUT_FILES:
        _assert(output_hashes[name] == EXPECTED_OUTPUT_SHA256[name], "stdout hash assertion")
        print(f"sha256 {name} {output_hashes[name]}")
    print("ADMIT_007_STANDALONE_EVALUATOR_INTERFACE_CHECK=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
