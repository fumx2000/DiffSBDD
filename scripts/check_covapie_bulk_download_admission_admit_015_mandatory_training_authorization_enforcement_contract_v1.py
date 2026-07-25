#!/usr/bin/env python3
"""Independent checker for the ADMIT_015 mandatory-enforcement design."""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, NamedTuple

from covalent_ext import (
    covapie_bulk_download_admission_admit_015_mandatory_training_authorization_enforcement_contract_design_gate
    as gate,
)


ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "4a3e813912cf704a1c6508ab21cd198e911b6b3c"
BASE_PARENT = "d70d7d8919c3ec59e0b3d864ec8e496695ab770b"
BASE_TREE = "a9c634a60c989838dd9334a0d037de62f9d0ee75"
BASE_SUBJECT = (
    "add CovaPIE unified dispatch runtime with ADMIT_001 to ADMIT_015 v1"
)
STAGE_NAME = (
    "covapie_bulk_download_admission_admit_015_mandatory_training_"
    "authorization_enforcement_contract_v1"
)
STAGE = Path("data/derived/covalent_small") / STAGE_NAME
DERIVED_ROOT = ROOT / STAGE
PRODUCTION = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_admit_015_mandatory_training_"
    "authorization_enforcement_contract_design_gate.py"
)
CHECKER = Path(
    "scripts/"
    "check_covapie_bulk_download_admission_admit_015_mandatory_"
    "training_authorization_enforcement_contract_v1.py"
)
TEST = Path(
    "tests/"
    "test_covapie_bulk_download_admission_admit_015_mandatory_"
    "training_authorization_enforcement_contract_v1.py"
)
SUMMARY = Path(
    "docs/"
    "covapie_bulk_download_admission_admit_015_mandatory_training_"
    "authorization_enforcement_contract_v1_summary.md"
)
API_FILENAME = (
    "covapie_admit_015_mandatory_training_authorization_"
    "enforcement_api_contract.csv"
)
PROTECTED_FILENAME = (
    "covapie_admit_015_protected_training_action_boundary.csv"
)
TRUTH_FILENAME = (
    "covapie_admit_015_mandatory_enforcement_truth_matrix.csv"
)
SAFETY_FILENAME = (
    "covapie_admit_015_mandatory_enforcement_safety_audit.csv"
)
ISSUE_FILENAME = (
    "covapie_admit_015_mandatory_enforcement_issue_readiness_inventory.csv"
)
MANIFEST_FILENAME = (
    "covapie_admit_015_mandatory_training_authorization_"
    "enforcement_contract_manifest.json"
)
OUTPUT_FILES = (
    API_FILENAME,
    PROTECTED_FILENAME,
    TRUTH_FILENAME,
    SAFETY_FILENAME,
    ISSUE_FILENAME,
    MANIFEST_FILENAME,
)
EXACT10 = (
    PRODUCTION,
    CHECKER,
    TEST,
    SUMMARY,
    *(STAGE / name for name in OUTPUT_FILES),
)
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
STAGE_TOKEN = (
    "covapie_bulk_download_admission_admit_015_mandatory_training_"
    "authorization_enforcement_contract"
)
STAGE_FAMILY_TOKENS = (
    STAGE_TOKEN,
    "covapie_admit_015_mandatory_training_authorization_enforcement_api_contract",
    "covapie_admit_015_protected_training_action_boundary",
    "covapie_admit_015_mandatory_enforcement_truth_matrix",
    "covapie_admit_015_mandatory_enforcement_safety_audit",
    "covapie_admit_015_mandatory_enforcement_issue_readiness_inventory",
    "covapie_admit_015_mandatory_training_authorization_enforcement_contract_manifest",
)
MAX_BYTES = 100 * 1024 * 1024
DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC

EXPECTED_PRODUCTION_SHA256 = (
    "6acee7df5d64a1362e66646964bc6965a1ee5ffd3ac088fe81df056ea9ce1d46"
)
EXPECTED_OUTPUT_SHA256 = {
    API_FILENAME: (
        "e41e9da660a3651d7ed60a9614b9e744dac09379696c81e6c14f8c27d0dd64d3"
    ),
    PROTECTED_FILENAME: (
        "d30214188c824ef6803986c6d8e5a416af46d0a7a9528982c4eae1cc46998cd1"
    ),
    TRUTH_FILENAME: (
        "6566b9fc939bbb0117a8ef49277047c11e409b8cf5f97a709e1ec1966fccb2d8"
    ),
    SAFETY_FILENAME: (
        "57f82f1745e2c680842c981460b5829c2ed960dece51554d59fc14460c1124e6"
    ),
    ISSUE_FILENAME: (
        "c8ea16e335e43ed781bb5177e1aba0247a55714f55eeb5caf8bed23a539f431d"
    ),
    MANIFEST_FILENAME: (
        "d1300557d62d845fd40f62992baee3784bb0b8bb33c560e7fa7f656245528171"
    ),
}

FUTURE_PUBLIC_FUNCTION = "require_admit_015_training_authorization"
FUTURE_PUBLIC_SIGNATURE = (
    "require_admit_015_training_authorization("
    "candidate_record: Mapping[str, object], *, "
    "stage_authorization_context: Mapping[str, object] | None"
    ") -> UnifiedAdmissionRuleEvaluation"
)
FUTURE_RETURN_TYPE = "UnifiedAdmissionRuleEvaluation"
FUTURE_ERROR_TYPE = "Admit015TrainingAuthorizationEnforcementError"
FUTURE_ERROR_SCHEMA_VERSION = (
    "covapie_admit_015_training_authorization_enforcement_error_v1"
)
FUTURE_ERROR_FIELDS = (
    "schema_version",
    "error_code",
    "admission_rule_id",
    "reason",
)
FUTURE_ERROR_FIELD_TYPES = ("str", "str", "str", "str")
FUTURE_ERROR_SIGNATURE = (
    "Admit015TrainingAuthorizationEnforcementError("
    "schema_version: str, error_code: str, admission_rule_id: str, "
    "reason: str)"
)
FUTURE_ERROR_CODES = (
    "ADMIT_015_TRAINING_AUTHORIZATION_DISPATCH_FAILED",
    "ADMIT_015_TRAINING_AUTHORIZATION_RESULT_INVALID",
    "ADMIT_015_TRAINING_AUTHORIZATION_DENIED",
    "ADMIT_015_TRAINING_AUTHORIZATION_REPLAY_FORBIDDEN",
    "ADMIT_015_TRAINING_AUTHORIZATION_REPEATED_CALL_FORBIDDEN",
    "ADMIT_015_TRAINING_AUTHORIZATION_OVERRIDE_FORBIDDEN",
)
ADMISSION_RULE_ID = "ADMIT_015"
ADAPTER_ID = "covapie_admit_015_unified_adapter_v1"
AUTHORIZATION_ITEM = "current_stage_training_authorized"
RESULT_SCHEMA_VERSION = "covapie_unified_admission_rule_evaluation_v1"
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
PROTECTED_ACTIONS = (
    ("TRAIN_ACTION_001", "dataloader instantiation"),
    ("TRAIN_ACTION_002", "checkpoint loading"),
    ("TRAIN_ACTION_003", "model initialization"),
    ("TRAIN_ACTION_004", "model forward"),
    ("TRAIN_ACTION_005", "loss computation"),
    ("TRAIN_ACTION_006", "backward"),
    ("TRAIN_ACTION_007", "optimizer creation"),
    ("TRAIN_ACTION_008", "scheduler creation"),
    ("TRAIN_ACTION_009", "parameter update"),
    ("TRAIN_ACTION_010", "checkpoint write"),
    ("TRAIN_ACTION_011", "training-result materialization"),
)
ZERO_PROTECTED_ACTION_COUNTS = tuple(
    (action_id, 0) for action_id, _ in PROTECTED_ACTIONS
)
CANONICAL_MASKS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
RECOMMENDED_NEXT_STEP = (
    "implement_covapie_admit_015_mandatory_training_authorization_"
    "enforcement_v1"
)

API_COLUMNS = (
    "contract_order",
    "contract_group",
    "contract_item",
    "frozen_value",
    "implementation_status",
    "contract_passed",
)
PROTECTED_COLUMNS = (
    "action_order",
    "action_id",
    "action_semantic_name",
    "guard_required_before_action",
    "blocked_count_expected",
    "design_pass_executes_action",
    "combined_verdict_override_forbidden",
    "real_implementation_status",
    "boundary_passed",
)
TRUTH_COLUMNS = (
    "case_order",
    "case_id",
    "case_group",
    "expected_decision",
    "observed_decision",
    "expected_error_code",
    "observed_error_code",
    "runtime_call_count",
    "selected_rule_id",
    "batch_context_is_none",
    "evaluation_context_is_none",
    "download_result_context_is_none",
    "stage_context_identity_preserved",
    "protected_action_counts_json",
    "current_permission",
    "authorized_execution_count",
    "real_training_executed",
    "case_passed",
)
SAFETY_COLUMNS = (
    "audit_order",
    "audit_item",
    "expected_state",
    "observed_state",
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
        "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015.py",
        "1fc5ac24e54d134d3f1f7054dfd2f264a2d76f17f0602bac216bb2e4e7e00bd1",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015_v1/covapie_admit_001_to_015_runtime_contract.csv",
        "b6606d4111b7493e4b8cd531fb88c5281b5a685369788b85742b5e85d721a465",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015_v1/covapie_admit_001_to_015_dispatch_truth_matrix.csv",
        "f93a43cfa560d495ea7e14fca26a957c6eb087907cbfde91d7456d1a55440abb",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015_v1/covapie_admit_001_to_015_registry_and_identity_audit.csv",
        "eac4ea16fbd2193c3b53f8d6bdf11728f086a499390bba7c33e1e3d2e61cc75e",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015_v1/covapie_admit_001_to_015_runtime_safety_audit.csv",
        "50db14b8d823c162e694a74abaa5a9189006f54d6cb6716d6ad9406f509a05b2",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015_v1/covapie_admit_001_to_015_runtime_issue_readiness_inventory.csv",
        "c8ea16e335e43ed781bb5177e1aba0247a55714f55eeb5caf8bed23a539f431d",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015_v1/covapie_admit_001_to_015_runtime_manifest.json",
        "0fbd5999977d025a44b4bef854d9edfda5ea0e5ed79a7d5ff7b17cef7b6186d3",
    ),
    (
        "scripts/check_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015_v1.py",
        "b0a1a7cb6634c9a37d6ad6d72cfc0b6bdae018c2f96b99d48c1f0325f7aa12ce",
    ),
    (
        "src/covalent_ext/covapie_bulk_download_admission_admit_015_training_authorization_contract.py",
        "77d278f6c0666d9843c86151bb8189836639e89f93b9488c92c5e7169a3d76e1",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_015_training_authorization_contract_v1/covapie_admit_015_training_authorization_contract.csv",
        "d8cdc33a8debac9959563047b54a0975c5318c09ffefc3b69b9025e8e768254d",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_015_training_authorization_contract_v1/covapie_admit_015_training_authorization_truth_matrix.csv",
        "bc1070cb7df2db7ee05c4c8aa21ea9563a08974b620d44ee42c193c63b4fb37b",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_015_training_authorization_contract_v1/covapie_admit_015_training_authorization_value_and_trust_contract.csv",
        "eab6be6568b3a8a8fba298eab6fff052184922a70b2893663311d437c6735d7e",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_015_training_authorization_contract_v1/covapie_admit_015_training_authorization_safety_boundary_audit.csv",
        "ed6fb5650716c9135157393eff6b8882781c063c569a5be5aafc550c249969d0",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_015_training_authorization_contract_v1/covapie_admit_015_issue_readiness_inventory.csv",
        "f457da61bffade18999af5c069d237c30aa30a0c63efb8bb14130935fb0757ec",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_015_training_authorization_contract_v1/covapie_admit_015_training_authorization_contract_manifest.json",
        "16ea4bb5f781c6f6d8277fb4142258c2bee4849b942582e48692373caee5cda1",
    ),
    (
        "src/covalent_ext/covapie_bulk_download_admission_admit_015_standalone_evaluator_interface.py",
        "eacb5c1ac583649a34cdb9dcde4c004a861da43609b9ffb964a715a427883a82",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_015_standalone_evaluator_interface_v1/covapie_admit_015_standalone_evaluator_interface_contract.csv",
        "1ad1b44677abf7cd262d5928aee17381e5767dd82880aee689be07cd8b031245",
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
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_015_formal_evaluator_interface_contract_v1/covapie_admit_015_formal_evaluator_interface_and_result_contract.csv",
        "5e4e6b3a222ebe65c2ed89e8ce2d98a9ce31043235417bee9d166cb14199651d",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_015_formal_evaluator_interface_contract_v1/covapie_admit_015_formal_evaluator_routing_and_consumption_contract.csv",
        "a0c586281e96f063f67d7c47c1a0b8336a73cb0841b283ca1de64f30fe60cf66",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_015_formal_evaluator_interface_contract_v1/covapie_admit_015_formal_evaluator_interface_contract_manifest.json",
        "08ce241290c66e87881c983a563be9f406d904c39e99bd9c6830c78fc3b4b021",
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
        "src/covalent_ext/covapie_bulk_download_admission_admit_014_download_authorization_contract_design_gate.py",
        "b2616c01234c899695c08280daacfa21cb137b847a01f5bf6e52e807b0770434",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_014_download_authorization_contract_v1/covapie_admit_014_stage_authorization_routing_and_enforcement_contract.csv",
        "68bc56b214f212ffec359049146e371ac7ce48bed34bfd6bb80313a2fd7046a6",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_014_download_authorization_contract_v1/covapie_admit_014_download_authorization_contract_manifest.json",
        "9c54c9d6cb11776b04938d9be048699041bfc4020dca4c00425faadaaaa5d4d2",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_015_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_015_formal_evaluator_interface_precondition_inventory.csv",
        "c52287ac5a435e58a400be0e33e17c1096b7b0d3b2671be0398a6be03e409839",
    ),
    (
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_015_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_015_formal_evaluator_interface_preconditions_manifest.json",
        "7f64389a018c9bc1170ffeb94d1f393aefc27f67edef1d85143659f43dc8d729",
    ),
)
SOURCE_PATHS = tuple(Path(path) for path, _ in SOURCE_BOUNDARY)
SOURCE_SHA256 = {Path(path): digest for path, digest in SOURCE_BOUNDARY}

TRUE_READINESS = (
    "admit_015_preconditions_audited",
    "admit_015_training_authorization_contract_frozen",
    "admit_015_formal_evaluator_interface_contract_frozen",
    "admit_015_standalone_evaluator_implemented",
    "admit_015_unified_adapter_contract_frozen",
    "admit_015_unified_adapter_implemented",
    "admit_015_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_015_implemented",
    "mandatory_training_authorization_enforcement_api_frozen",
    "ready_for_admit_015_mandatory_training_authorization_enforcement_implementation",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "mandatory_training_authorization_enforcement_implemented",
    "combined_permission_semantics_frozen",
    "combined_candidate_verdict_implemented",
    "cross_rule_aggregation_implemented",
    "feature_semantics_audit_completed",
    "historical_unknown_atom_feature_policy_resolved",
    "historical_feature_semantics_known",
    "real_training_ready",
    "ready_for_training",
    "step12d_is_final_training_feature_contract",
)
PRECONDITION_TRANSITION = {
    "row_count": 45,
    "resolved_precondition_ids": ["PRE_034"],
    "remaining_open_precondition_ids": [
        "PRE_035",
        "PRE_036",
        "PRE_038",
        "PRE_042",
    ],
    "complete_count": 41,
    "supported_but_not_frozen_count": 0,
    "incomplete_count": 4,
    "implementation_blocking_count": 4,
}
TRUTH_GROUP_COUNTS = {
    "admit014_isolation": 1,
    "candidate_field_drift": 2,
    "canonical_blocked": 1,
    "canonical_pass": 1,
    "combined_verdict_non_override": 1,
    "consumed_context_drift": 1,
    "contradictory_pass_flags": 2,
    "current_permission_boundary": 1,
    "design_pass_boundary": 1,
    "dispatcher_failure": 1,
    "evaluator_io_drift": 1,
    "exactly_once": 1,
    "false_authorization": 1,
    "invalid_candidate": 1,
    "missing_stage_context": 1,
    "normalized_value_drift": 2,
    "protected_action_zero_boundary": 1,
    "reason_validation": 1,
    "result_field_order_drift": 1,
    "result_field_type_drift": 1,
    "result_identity_drift": 3,
    "result_replay": 1,
    "result_type_validation": 2,
}
API_SPECS = (
    ("identity", "future_public_function_name", FUTURE_PUBLIC_FUNCTION),
    ("identity", "future_public_signature", FUTURE_PUBLIC_SIGNATURE),
    ("identity", "future_return_type", FUTURE_RETURN_TYPE),
    ("identity", "future_error_type", FUTURE_ERROR_TYPE),
    ("identity", "future_error_schema", FUTURE_ERROR_SCHEMA_VERSION),
    ("identity", "future_error_fields", "|".join(FUTURE_ERROR_FIELDS)),
    (
        "identity",
        "future_error_field_types",
        "|".join(FUTURE_ERROR_FIELD_TYPES),
    ),
    ("identity", "future_error_signature", FUTURE_ERROR_SIGNATURE),
    ("input", "candidate_record_owner", "future_training_orchestrator"),
    ("input", "stage_context_owner", "trusted_future_stage_orchestrator"),
    ("runtime", "runtime_dependency", "current_exact15_runtime"),
    ("runtime", "selected_rule_id", ADMISSION_RULE_ID),
    ("runtime", "runtime_call_count_per_invocation", "exactly_one"),
    ("routing", "batch_context", "None"),
    ("routing", "evaluation_context", "None"),
    ("routing", "download_result_context", "None"),
    ("routing", "stage_context_object", "same_identity"),
    ("validation", "result_exact_type", "required_no_subclass"),
    ("validation", "result_field_order", "|".join(RESULT_FIELDS)),
    ("validation", "result_schema_version", RESULT_SCHEMA_VERSION),
    ("validation", "result_rule_id", ADMISSION_RULE_ID),
    ("validation", "result_outcome", "passed"),
    ("validation", "result_passed", "true"),
    ("validation", "result_blocks_candidate", "false"),
    ("validation", "result_reason", "empty"),
    ("validation", "result_evaluator_io_used", "false"),
    ("validation", "result_adapter_id", ADAPTER_ID),
    (
        "validation",
        "result_normalized_values",
        "current_stage_training_authorized=true",
    ),
    ("validation", "validated_candidate_fields", "empty_tuple"),
    ("validation", "consumed_candidate_fields", "empty_tuple"),
    ("validation", "consumed_context_items", AUTHORIZATION_ITEM),
    ("behavior", "only_pass_may_continue", "true"),
    ("behavior", "return_on_pass", "exact_validated_result"),
    ("behavior", "raise_on_denial_or_drift", FUTURE_ERROR_TYPE),
    ("behavior", "candidate_fields_are_authority", "false"),
    ("forbidden", "precomputed_bool_input", "forbidden"),
    ("forbidden", "precomputed_result_input", "forbidden"),
    ("forbidden", "combined_verdict_input", "forbidden"),
    ("forbidden", "admit_014_permission_substitution", "forbidden"),
    (
        "forbidden",
        "manifest_config_cli_environment_authority",
        "forbidden",
    ),
    ("boundary", "protected_action_count", "11"),
    ("boundary", "training_io_in_design", "false"),
    ("status", "future_api_frozen", "true"),
    ("status", "future_api_implemented", "false"),
)
TRUTH_CASES = (
    ("canonical_admit_015_pass", "canonical_pass", "", 1),
    (
        "canonical_admit_015_blocked",
        "canonical_blocked",
        FUTURE_ERROR_CODES[2],
        1,
    ),
    ("invalid_candidate", "invalid_candidate", FUTURE_ERROR_CODES[2], 1),
    (
        "missing_stage_context",
        "missing_stage_context",
        FUTURE_ERROR_CODES[2],
        1,
    ),
    ("false_authorization", "false_authorization", FUTURE_ERROR_CODES[2], 1),
    (
        "dispatcher_failure",
        "dispatcher_failure",
        FUTURE_ERROR_CODES[0],
        1,
    ),
    (
        "result_wrong_type",
        "result_type_validation",
        FUTURE_ERROR_CODES[1],
        1,
    ),
    (
        "result_subclass",
        "result_type_validation",
        FUTURE_ERROR_CODES[1],
        1,
    ),
    (
        "result_field_order_drift",
        "result_field_order_drift",
        FUTURE_ERROR_CODES[2],
        1,
    ),
    (
        "result_field_type_drift",
        "result_field_type_drift",
        FUTURE_ERROR_CODES[2],
        1,
    ),
    ("schema_drift", "result_identity_drift", FUTURE_ERROR_CODES[2], 1),
    ("rule_id_drift", "result_identity_drift", FUTURE_ERROR_CODES[2], 1),
    ("adapter_id_drift", "result_identity_drift", FUTURE_ERROR_CODES[2], 1),
    (
        "contradictory_passed_false",
        "contradictory_pass_flags",
        FUTURE_ERROR_CODES[2],
        1,
    ),
    (
        "contradictory_blocks_true",
        "contradictory_pass_flags",
        FUTURE_ERROR_CODES[2],
        1,
    ),
    ("nonempty_reason", "reason_validation", FUTURE_ERROR_CODES[2], 1),
    (
        "normalized_value_missing",
        "normalized_value_drift",
        FUTURE_ERROR_CODES[2],
        1,
    ),
    (
        "normalized_value_wrong",
        "normalized_value_drift",
        FUTURE_ERROR_CODES[2],
        1,
    ),
    ("evaluator_io_drift", "evaluator_io_drift", FUTURE_ERROR_CODES[2], 1),
    (
        "validated_candidate_fields_drift",
        "candidate_field_drift",
        FUTURE_ERROR_CODES[2],
        1,
    ),
    (
        "consumed_candidate_fields_drift",
        "candidate_field_drift",
        FUTURE_ERROR_CODES[2],
        1,
    ),
    (
        "consumed_context_drift",
        "consumed_context_drift",
        FUTURE_ERROR_CODES[2],
        1,
    ),
    (
        "repeated_runtime_call_attempt",
        "exactly_once",
        FUTURE_ERROR_CODES[4],
        0,
    ),
    (
        "precomputed_result_replay",
        "result_replay",
        FUTURE_ERROR_CODES[3],
        0,
    ),
    (
        "admit_014_true_cannot_authorize_training",
        "admit014_isolation",
        FUTURE_ERROR_CODES[5],
        0,
    ),
    (
        "combined_true_cannot_override_blocked",
        "combined_verdict_non_override",
        FUTURE_ERROR_CODES[5],
        0,
    ),
    (
        "blocked_protected_counts_zero",
        "protected_action_zero_boundary",
        FUTURE_ERROR_CODES[2],
        1,
    ),
    (
        "synthetic_true_changes_no_current_permission",
        "current_permission_boundary",
        "",
        1,
    ),
    (
        "pass_releases_future_in_memory_only",
        "design_pass_boundary",
        "",
        1,
    ),
)
SAFETY_STATES = (
    ("network_executed", False),
    ("provider_executed", False),
    ("download_executed", False),
    ("raw_accessed", False),
    ("torch_imported", False),
    ("dataloader_instantiated", False),
    ("checkpoint_loaded", False),
    ("model_initialized", False),
    ("model_forward_executed", False),
    ("loss_computed", False),
    ("backward_executed", False),
    ("optimizer_created", False),
    ("scheduler_created", False),
    ("parameter_updated", False),
    ("checkpoint_written", False),
    ("training_result_materialized", False),
    ("current_permission", False),
    ("authorized_execution_count_nonzero", False),
    ("mandatory_enforcement_implemented", False),
    ("combined_candidate_verdict_implemented", False),
    ("cross_rule_aggregation_implemented", False),
    ("feature_semantics_audit_completed", False),
    ("historical_unknown_atom_feature_policy_resolved", False),
    ("historical_feature_semantics_known", False),
    ("real_training_ready", False),
    ("ready_for_training", False),
    ("design_contract_only", True),
    ("exact11_protected_actions_frozen", True),
)


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def canonical_guard() -> None:
    if (
        sys.implementation.name != "cpython"
        or tuple(sys.version_info[:3]) != (3, 10, 4)
    ):
        raise AssertionError("checker requires CPython 3.10.4")


def _git(*arguments: str, check: bool = True) -> bytes:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and completed.returncode:
        raise AssertionError(f"git command failed: {arguments}")
    return completed.stdout


def _identity(item: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        int(item.st_dev),
        int(item.st_ino),
        int(item.st_mode),
        int(item.st_size),
        int(item.st_mtime_ns),
        int(item.st_ctime_ns),
    )


def _strict_json(content: bytes) -> dict[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise AssertionError("manifest duplicate key")
            result[key] = value
        return result

    try:
        value = json.loads(content, object_pairs_hook=unique)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AssertionError("manifest JSON invalid") from error
    if type(value) is not dict:
        raise AssertionError("manifest object required")
    return value


def _csv_rows(
    content: bytes, columns: Sequence[str]
) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(content.decode(), newline=""))
    if tuple(reader.fieldnames or ()) != tuple(columns):
        raise AssertionError("CSV header drift")
    rows = [dict(row) for row in reader]
    if any(tuple(row) != tuple(columns) for row in rows):
        raise AssertionError("CSV row schema drift")
    return rows


def _read_exact_outputs() -> dict[str, bytes]:
    parent = DERIVED_ROOT.parent
    parent_item = os.lstat(parent)
    root_item = os.lstat(DERIVED_ROOT)
    if (
        not stat.S_ISDIR(parent_item.st_mode)
        or stat.S_ISLNK(parent_item.st_mode)
        or not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
    ):
        raise AssertionError("output root/parent unsafe")
    parent_identity = _identity(parent_item)
    root_identity = _identity(root_item)
    parent_fd = os.open(
        parent,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
    )
    root_fd = os.open(
        DERIVED_ROOT.name,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
        dir_fd=parent_fd,
    )
    descriptors: dict[str, int] = {}
    identities: dict[str, tuple[int, int, int, int, int, int]] = {}
    try:
        def assert_parent_root_binding(reason: str) -> None:
            if (
                _identity(os.fstat(root_fd)) != root_identity
                or _identity(
                    os.stat(
                        DERIVED_ROOT.name,
                        dir_fd=parent_fd,
                        follow_symlinks=False,
                    )
                )
                != root_identity
                or _identity(os.fstat(parent_fd)) != parent_identity
                or _identity(os.lstat(parent)) != parent_identity
                or _identity(os.lstat(DERIVED_ROOT)) != root_identity
            ):
                raise AssertionError(reason)

        def exact_inventory(reason: str) -> tuple[str, ...]:
            names = tuple(sorted(os.listdir(root_fd)))
            if names != tuple(sorted(OUTPUT_FILES)):
                raise AssertionError(reason)
            return names

        def assert_all_leaves(reason: str) -> None:
            for name in OUTPUT_FILES:
                try:
                    lexical = os.stat(
                        name,
                        dir_fd=root_fd,
                        follow_symlinks=False,
                    )
                except OSError as error:
                    raise AssertionError(reason) from error
                if (
                    _identity(os.fstat(descriptors[name]))
                    != identities[name]
                    or _identity(lexical) != identities[name]
                    or not stat.S_ISREG(lexical.st_mode)
                    or stat.S_ISLNK(lexical.st_mode)
                ):
                    raise AssertionError(reason)

        # The final operation before returning is deliberately the final
        # parent/root binding.  No leaf traversal follows it.
        assert_parent_root_binding("output initial root/parent drift")
        initial_names = exact_inventory("output inventory not Exact6")
        for name in OUTPUT_FILES:
            item = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            if (
                not stat.S_ISREG(item.st_mode)
                or stat.S_ISLNK(item.st_mode)
                or item.st_size > MAX_BYTES
            ):
                raise AssertionError("output leaf unsafe")
            identities[name] = _identity(item)
            descriptor = os.open(
                name,
                os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=root_fd,
            )
            descriptors[name] = descriptor
            if _identity(os.fstat(descriptor)) != identities[name]:
                raise AssertionError("output stat/open race")
        payloads = {}
        for name in OUTPUT_FILES:
            chunks = []
            while True:
                chunk = os.read(descriptors[name], 1 << 16)
                if not chunk:
                    break
                chunks.append(chunk)
            payloads[name] = b"".join(chunks)
        assert_all_leaves("output first leaf drift")
        assert_parent_root_binding("output first root/parent drift")
        if exact_inventory("output second inventory drift") != initial_names:
            raise AssertionError("output second inventory drift")
        assert_all_leaves("output final leaf drift")
        if exact_inventory("output final inventory drift") != initial_names:
            raise AssertionError("output final inventory drift")
        assert_parent_root_binding("output final root/parent drift")
        return payloads
    finally:
        for descriptor in descriptors.values():
            os.close(descriptor)
        os.close(root_fd)
        os.close(parent_fd)


class LocalFrozenSource(NamedTuple):
    relative_path: Path
    expected_sha256: str
    base_tree_mode: str
    base_tree_blob: str
    index_mode: str
    index_blob: str
    index_stage: int
    filesystem_sha256: str
    content: bytes


def _parse_index(content: bytes, relative: str) -> tuple[str, str, int]:
    try:
        metadata, path = content.decode().rstrip("\n").split("\t", 1)
        mode, blob, stage_number = metadata.split(" ")
    except ValueError as error:
        raise AssertionError("source index entry malformed") from error
    if (
        path != relative
        or mode not in {"100644", "100755"}
        or re.fullmatch(r"[0-9a-f]{40}", blob) is None
    ):
        raise AssertionError("source index entry drift")
    return mode, blob, int(stage_number)


def _parse_tree(content: bytes, relative: str) -> tuple[str, str]:
    try:
        metadata, path = content.decode().rstrip("\n").split("\t", 1)
        mode, kind, blob = metadata.split(" ")
    except ValueError as error:
        raise AssertionError("source tree entry malformed") from error
    if (
        path != relative
        or kind != "blob"
        or mode not in {"100644", "100755"}
        or re.fullmatch(r"[0-9a-f]{40}", blob) is None
    ):
        raise AssertionError("source tree entry drift")
    return mode, blob


def _pinned_read(root: Path, relative: Path) -> bytes:
    root = Path(os.path.abspath(root))
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise AssertionError("unsafe pinned-read path")
    root_item = os.lstat(root)
    root_identity = _identity(root_item)
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
            for lexical_parent, name, child_fd, expected in reversed(
                bindings
            ):
                lexical = os.stat(
                    name,
                    dir_fd=lexical_parent,
                    follow_symlinks=False,
                )
                if (
                    _identity(lexical) != expected
                    or _identity(os.fstat(child_fd)) != expected
                    or not stat.S_ISDIR(lexical.st_mode)
                    or stat.S_ISLNK(lexical.st_mode)
                ):
                    raise AssertionError("pinned parent changed")
            lexical_root = os.lstat(root)
            if (
                _identity(lexical_root) != root_identity
                or _identity(os.fstat(descriptors[0])) != root_identity
                or not stat.S_ISDIR(lexical_root.st_mode)
                or stat.S_ISLNK(lexical_root.st_mode)
                or root.resolve(strict=True) != root
            ):
                raise AssertionError("pinned root changed")

        if _identity(os.fstat(descriptors[0])) != root_identity:
            raise AssertionError("pinned root race")
        parent_fd = descriptors[0]
        for part in relative.parts[:-1]:
            lexical = os.stat(
                part,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
            expected = _identity(lexical)
            if (
                not stat.S_ISDIR(lexical.st_mode)
                or stat.S_ISLNK(lexical.st_mode)
            ):
                raise AssertionError("unsafe pinned parent")
            child_fd = os.open(part, DIR_FLAGS, dir_fd=parent_fd)
            if _identity(os.fstat(child_fd)) != expected:
                os.close(child_fd)
                raise AssertionError("pinned parent race")
            descriptors.append(child_fd)
            bindings.append((parent_fd, part, child_fd, expected))
            parent_fd = child_fd
        before = os.stat(
            relative.name,
            dir_fd=parent_fd,
            follow_symlinks=False,
        )
        leaf_identity = _identity(before)
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_ISLNK(before.st_mode)
            or before.st_size > MAX_BYTES
        ):
            raise AssertionError("unsafe pinned leaf")
        leaf_fd = os.open(relative.name, READ_FLAGS, dir_fd=parent_fd)
        descriptors.append(leaf_fd)
        if _identity(os.fstat(leaf_fd)) != leaf_identity:
            raise AssertionError("pinned leaf stat/open race")
        chunks = []
        while True:
            chunk = os.read(leaf_fd, 1 << 16)
            if not chunk:
                break
            chunks.append(chunk)
        if (
            _identity(os.fstat(leaf_fd)) != leaf_identity
            or _identity(
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
            _identity(os.fstat(leaf_fd)) != leaf_identity
            or _identity(
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


def _build_local_source_snapshot() -> tuple[LocalFrozenSource, ...]:
    identity = _git(
        "show",
        "-s",
        "--format=%H%n%P%n%T%n%s",
        BASE_COMMIT,
    ).decode().splitlines()
    if identity != [BASE_COMMIT, BASE_PARENT, BASE_TREE, BASE_SUBJECT]:
        raise AssertionError("base identity drift")
    _git("merge-base", "--is-ancestor", BASE_COMMIT, "HEAD")
    if (
        len(SOURCE_BOUNDARY) != 34
        or len(set(SOURCE_PATHS)) != 34
        or tuple(SOURCE_SHA256) != SOURCE_PATHS
    ):
        raise AssertionError("Exact34 local source boundary drift")
    inspected = []
    for relative in SOURCE_PATHS:
        raw = relative.as_posix()
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or relative.parts[:2] == ("data", "raw")
            or relative.parts[0] == "checkpoints"
            or STAGE_NAME in relative.parts
        ):
            raise AssertionError("unsafe local source boundary")
        index_mode, index_blob, index_stage = _parse_index(
            _git("ls-files", "--stage", "--", raw),
            raw,
        )
        base_mode, base_blob = _parse_tree(
            _git("ls-tree", BASE_COMMIT, "--", raw),
            raw,
        )
        if (
            index_stage != 0
            or index_mode != base_mode
            or index_blob != base_blob
        ):
            raise AssertionError("source index/base identity drift")
        content = _pinned_read(ROOT, relative)
        expected_sha = SOURCE_SHA256[relative]
        filesystem_sha = _sha(content)
        git_content = _git("cat-file", "blob", base_blob)
        if (
            filesystem_sha != expected_sha
            or content != git_content
            or _sha(git_content) != expected_sha
        ):
            raise AssertionError("source content drift")
        inspected.append(
            LocalFrozenSource(
                relative_path=relative,
                expected_sha256=expected_sha,
                base_tree_mode=base_mode,
                base_tree_blob=base_blob,
                index_mode=index_mode,
                index_blob=index_blob,
                index_stage=index_stage,
                filesystem_sha256=filesystem_sha,
                content=content,
            )
        )
    return tuple(inspected)


def _verify_candidate_surface() -> None:
    source = _pinned_read(ROOT, PRODUCTION)
    if _sha(source) != EXPECTED_PRODUCTION_SHA256:
        raise AssertionError("Production SHA256 drift")
    tree = ast.parse(source)
    function_names = tuple(
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    )
    if FUTURE_PUBLIC_FUNCTION in function_names:
        raise AssertionError("future production enforcement function exists")
    candidate_constants = {
        "FUTURE_PUBLIC_FUNCTION": FUTURE_PUBLIC_FUNCTION,
        "FUTURE_PUBLIC_SIGNATURE": FUTURE_PUBLIC_SIGNATURE,
        "FUTURE_ERROR_TYPE": FUTURE_ERROR_TYPE,
        "FUTURE_ERROR_SCHEMA_VERSION": FUTURE_ERROR_SCHEMA_VERSION,
        "FUTURE_ERROR_FIELDS": FUTURE_ERROR_FIELDS,
        "FUTURE_ERROR_FIELD_TYPES": FUTURE_ERROR_FIELD_TYPES,
        "FUTURE_ERROR_SIGNATURE": FUTURE_ERROR_SIGNATURE,
        "FUTURE_ERROR_CODES": FUTURE_ERROR_CODES,
        "RESULT_FIELDS": RESULT_FIELDS,
        "RESULT_SCHEMA_VERSION": RESULT_SCHEMA_VERSION,
        "PROTECTED_ACTIONS": PROTECTED_ACTIONS,
        "CANONICAL_MASKS": CANONICAL_MASKS,
        "RECOMMENDED_NEXT_STEP": RECOMMENDED_NEXT_STEP,
    }
    for name, expected in candidate_constants.items():
        actual = getattr(gate, name)
        if type(actual) is not type(expected) or actual != expected:
            raise AssertionError(f"candidate constant drift: {name}")
    forbidden_import_roots = {
        "torch",
        "numpy",
        "rdkit",
        "Bio",
        "gemmi",
        "requests",
        "urllib",
    }
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
    if imports & forbidden_import_roots:
        raise AssertionError("forbidden production import")
    lowered = source.lower()
    forbidden_tokens = (
        b"data/raw",
        b"checkpoints/",
        b"optimizer.step(",
        b".backward(",
        b"torch.",
        b"requests.",
        b"urllib.",
    )
    if any(token in lowered for token in forbidden_tokens):
        raise AssertionError("forbidden production training/I/O surface")


def _csv_bytes(
    columns: Sequence[str],
    rows: Sequence[Mapping[str, str]],
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=list(columns),
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        if tuple(row) != tuple(columns):
            raise AssertionError("local CSV row schema drift")
        writer.writerow(row)
    return stream.getvalue().encode()


def _expected_api_rows() -> list[dict[str, str]]:
    return [
        {
            "contract_order": str(index),
            "contract_group": group,
            "contract_item": item,
            "frozen_value": value,
            "implementation_status": (
                "future_contract_only"
                if item
                not in {"future_api_frozen", "future_api_implemented"}
                else (
                    "frozen"
                    if item == "future_api_frozen"
                    else "not_implemented"
                )
            ),
            "contract_passed": "true",
        }
        for index, (group, item, value) in enumerate(API_SPECS, 1)
    ]


def _expected_protected_rows() -> list[dict[str, str]]:
    return [
        {
            "action_order": str(index),
            "action_id": action_id,
            "action_semantic_name": semantic,
            "guard_required_before_action": "true",
            "blocked_count_expected": "0",
            "design_pass_executes_action": "false",
            "combined_verdict_override_forbidden": "true",
            "real_implementation_status": "false",
            "boundary_passed": "true",
        }
        for index, (action_id, semantic) in enumerate(PROTECTED_ACTIONS, 1)
    ]


def _expected_truth_rows() -> list[dict[str, str]]:
    zero_counts = json.dumps(
        dict(ZERO_PROTECTED_ACTION_COUNTS),
        sort_keys=True,
        separators=(",", ":"),
    )
    rows = []
    for index, (case_id, group, error_code, call_count) in enumerate(
        TRUTH_CASES,
        1,
    ):
        release = error_code == ""
        routed = call_count == 1
        rows.append(
            {
                "case_order": str(index),
                "case_id": case_id,
                "case_group": group,
                "expected_decision": (
                    "future_in_memory_continuation"
                    if release
                    else "raise_fail_closed"
                ),
                "observed_decision": (
                    "future_in_memory_continuation"
                    if release
                    else "raise_fail_closed"
                ),
                "expected_error_code": error_code,
                "observed_error_code": error_code,
                "runtime_call_count": str(call_count),
                "selected_rule_id": ADMISSION_RULE_ID if routed else "",
                "batch_context_is_none": str(routed).lower(),
                "evaluation_context_is_none": str(routed).lower(),
                "download_result_context_is_none": str(routed).lower(),
                "stage_context_identity_preserved": str(routed).lower(),
                "protected_action_counts_json": zero_counts,
                "current_permission": "false",
                "authorized_execution_count": "0",
                "real_training_executed": "false",
                "case_passed": "true",
            }
        )
    return rows


def _expected_safety_rows() -> list[dict[str, str]]:
    return [
        {
            "audit_order": str(index),
            "audit_item": item,
            "expected_state": str(state).lower(),
            "observed_state": str(state).lower(),
            "safety_passed": "true",
        }
        for index, (item, state) in enumerate(SAFETY_STATES, 1)
    ]


def _source_content(
    snapshot: Sequence[LocalFrozenSource],
    basename: str,
) -> bytes:
    matches = [
        item.content
        for item in snapshot
        if item.relative_path.name == basename
    ]
    if len(matches) != 1:
        raise AssertionError("local source lookup not unique")
    return matches[0]


def _sorted_json(value: Any) -> Any:
    if type(value) is dict:
        return {
            key: _sorted_json(value[key])
            for key in sorted(value)
        }
    if type(value) is list:
        return [_sorted_json(item) for item in value]
    return value


def _assert_recursive_exact(
    actual: Any,
    expected: Any,
    path: str = "$",
) -> None:
    if type(actual) is not type(expected):
        raise AssertionError(f"{path}: exact type drift")
    if type(expected) is dict:
        if tuple(actual) != tuple(expected):
            raise AssertionError(f"{path}: dict inventory/order drift")
        for key in expected:
            _assert_recursive_exact(
                actual[key],
                expected[key],
                f"{path}.{key}",
            )
        return
    if type(expected) is list:
        if len(actual) != len(expected):
            raise AssertionError(f"{path}: list length drift")
        for index, (observed, required) in enumerate(
            zip(actual, expected, strict=True)
        ):
            _assert_recursive_exact(
                observed,
                required,
                f"{path}[{index}]",
            )
        return
    if actual != expected:
        raise AssertionError(f"{path}: scalar drift")


def _expected_manifest(
    snapshot: Sequence[LocalFrozenSource],
) -> dict[str, Any]:
    issue_bytes = _source_content(
        snapshot,
        "covapie_admit_001_to_015_runtime_issue_readiness_inventory.csv",
    )
    readiness = {name: True for name in TRUE_READINESS} | {
        name: False for name in FALSE_READINESS
    }
    source_paths_json = json.dumps(
        [path.as_posix() for path in SOURCE_PATHS],
        separators=(",", ":"),
    ).encode()
    source_pairs_json = json.dumps(
        [[path, digest] for path, digest in SOURCE_BOUNDARY],
        separators=(",", ":"),
    ).encode()
    manifest: dict[str, Any] = {
        "project": "CovaPIE",
        "step": (
            "ADMIT_015 mandatory training authorization enforcement "
            "contract v1"
        ),
        "stage": STAGE_NAME,
        "manifest_schema_version": (
            "covapie_admit_015_mandatory_training_authorization_"
            "enforcement_contract_manifest_v1"
        ),
        "base_identity": {
            "commit": BASE_COMMIT,
            "parent": BASE_PARENT,
            "tree": BASE_TREE,
            "subject": BASE_SUBJECT,
        },
        "canonical_evidence_runtime": {
            "implementation": "cpython",
            "version": "3.10.4",
            "migration_policy": "explicit_contract_refresh_required",
        },
        "source_boundary_name": (
            "fixed_ordered_exact34_committed_source_boundary"
        ),
        "source_count": 34,
        "source_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_sha256": {
            path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS
        },
        "source_path_list_sha256": _sha(source_paths_json),
        "source_path_sha256_pairs_sha256": _sha(source_pairs_json),
        "source_verification": [
            {
                "source_order": index,
                "path": item.relative_path.as_posix(),
                "base_tree_mode": item.base_tree_mode,
                "base_tree_blob": item.base_tree_blob,
                "index_mode": item.index_mode,
                "index_blob": item.index_blob,
                "index_stage": item.index_stage,
                "filesystem_sha256": item.filesystem_sha256,
                "git_blob_bytes_equal_filesystem_bytes": True,
                "pinned_no_follow_read": True,
                "six_field_identity": True,
                "final_leaf_then_parent_root_verified": True,
                "source_verified": True,
            }
            for index, item in enumerate(snapshot, 1)
        ],
        "future_api_contract": {
            "public_function_name": FUTURE_PUBLIC_FUNCTION,
            "exact_signature": FUTURE_PUBLIC_SIGNATURE,
            "return_type": FUTURE_RETURN_TYPE,
            "error_type": FUTURE_ERROR_TYPE,
            "error_schema_version": FUTURE_ERROR_SCHEMA_VERSION,
            "error_fields": list(FUTURE_ERROR_FIELDS),
            "error_field_types": list(FUTURE_ERROR_FIELD_TYPES),
            "error_signature": FUTURE_ERROR_SIGNATURE,
            "error_codes": list(FUTURE_ERROR_CODES),
            "runtime_dependency": (
                "covapie_bulk_download_admission_unified_dispatch_"
                "runtime_with_admit_001_to_015.evaluate_admission_rule"
            ),
            "selected_rule_id": ADMISSION_RULE_ID,
            "exactly_once_per_real_training_invocation": True,
            "batch_context": None,
            "evaluation_context": None,
            "download_result_context": None,
            "same_stage_context_object": True,
            "precomputed_bool_accepted": False,
            "precomputed_result_accepted": False,
            "combined_verdict_accepted": False,
            "candidate_field_authority": False,
            "only_pass_may_continue": True,
            "exception_on_denial": True,
            "implemented": False,
        },
        "pass_invariants": {
            "exact_result_type": "UnifiedAdmissionRuleEvaluation_no_subclass",
            "field_order": list(RESULT_FIELDS),
            "schema_version": RESULT_SCHEMA_VERSION,
            "admission_rule_id": ADMISSION_RULE_ID,
            "outcome": "passed",
            "passed": True,
            "blocks_candidate": False,
            "reason": "",
            "evaluator_io_used": False,
            "adapter_id": ADAPTER_ID,
            "normalized_values": [[AUTHORIZATION_ITEM, "true"]],
            "validated_candidate_fields": [],
            "consumed_candidate_fields": [],
            "consumed_context_items": [AUTHORIZATION_ITEM],
        },
        "protected_action_count": 11,
        "protected_actions": [
            {"action_id": action_id, "semantic_name": semantic}
            for action_id, semantic in PROTECTED_ACTIONS
        ],
        "blocked_protected_action_counts": {
            action_id: count
            for action_id, count in ZERO_PROTECTED_ACTION_COUNTS
        },
        "truth_matrix_schema": list(TRUTH_COLUMNS),
        "truth_matrix_row_count": 29,
        "truth_matrix_group_count": 23,
        "truth_matrix_group_counts": TRUTH_GROUP_COUNTS,
        "truth_matrix_all_cases_passed": True,
        "safety_schema": list(SAFETY_COLUMNS),
        "safety_row_count": 28,
        "precondition_transition": PRECONDITION_TRANSITION,
        "issue_continuity": {
            "row_count": 30,
            "transition_count": 0,
            "byte_identical_to_exact15_runtime": True,
            "sha256": EXPECTED_OUTPUT_SHA256[ISSUE_FILENAME],
            "remaining_required_open_issue_ids": [
                "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
                "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
                "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
            ],
        },
        "readiness": readiness,
        "current_permission": False,
        "authorized_admit_015_training_execution_count": 0,
        "mandatory_training_authorization_enforcement_implemented": False,
        "combined_permission_semantics_frozen": False,
        "combined_candidate_verdict_implemented": False,
        "cross_rule_aggregation_implemented": False,
        "canonical_mask_count": 5,
        "canonical_masks": [
            {"semantic_name": semantic, "alias": alias}
            for semantic, alias in CANONICAL_MASKS
        ],
        "canonical_mask_long_names_are_authoritative": True,
        "step12d_status": (
            "smoke_legality_only_not_final_training_feature_contract"
        ),
        "feature_semantics_note": (
            "feature-semantics audit remains mandatory before training; "
            "historical UNKNOWN_ATOM_FEATURE_POLICY and "
            "feature_semantics_known=False remain unresolved"
        ),
        "output_schema": {
            API_FILENAME: list(API_COLUMNS),
            PROTECTED_FILENAME: list(PROTECTED_COLUMNS),
            TRUTH_FILENAME: list(TRUTH_COLUMNS),
            SAFETY_FILENAME: list(SAFETY_COLUMNS),
            ISSUE_FILENAME: list(ISSUE_COLUMNS),
        },
        "output_sha256": {
            name: EXPECTED_OUTPUT_SHA256[name]
            for name in OUTPUT_FILES[:-1]
        },
        "output_sha256_excludes_manifest_self_hash": True,
        "output_materialization": {
            "build_before_mutation": True,
            "o_excl": True,
            "fsync": True,
            "rename_noreplace": True,
            "gpfs_einval_fail_closed": True,
            "os_replace_used": False,
            "destructive_cleanup_used": False,
            "retained_staging_requires_authenticated_binding": True,
            "complete_recursive_manifest_equality": True,
        },
        "design_scope": {
            "production_enforcement_function_defined": False,
            "training_integration": False,
            "training_io": False,
            "provider_network_download_raw": False,
            "combined_permission_semantics": False,
            "cross_rule_aggregation": False,
            "feature_semantics_resolution": False,
        },
        "all_checks_passed": True,
        "validation_failures": [],
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }
    manifest.update(readiness)
    expected = _sorted_json(manifest)
    if len(expected) != 64:
        raise AssertionError("local expected Manifest is not Exact64")
    if (
        _sha(
            (
                json.dumps(expected, indent=2, sort_keys=True) + "\n"
            ).encode()
        )
        != EXPECTED_OUTPUT_SHA256[MANIFEST_FILENAME]
    ):
        raise AssertionError("local expected Manifest reconstruction drift")
    if _sha(issue_bytes) != EXPECTED_OUTPUT_SHA256[ISSUE_FILENAME]:
        raise AssertionError("local Exact30 source continuity drift")
    return expected


def _assert_candidate_observations() -> None:
    observed_sets = (
        (API_COLUMNS, gate._api_rows(), _expected_api_rows()),
        (
            PROTECTED_COLUMNS,
            gate._protected_rows(),
            _expected_protected_rows(),
        ),
        (TRUTH_COLUMNS, gate._truth_rows(), _expected_truth_rows()),
        (SAFETY_COLUMNS, gate._safety_rows(), _expected_safety_rows()),
    )
    for columns, observed, expected in observed_sets:
        _assert_recursive_exact(observed, expected, "$.candidate_rows")
        if _csv_bytes(columns, observed) != _csv_bytes(columns, expected):
            raise AssertionError("candidate observed row serialization drift")


def _verify_semantics(
    payloads: Mapping[str, bytes],
    _candidate_expected: Mapping[str, bytes] | None = None,
    _candidate_snapshot: Sequence[Any] | None = None,
    *,
    local_snapshot: Sequence[LocalFrozenSource] | None = None,
) -> dict[str, Any]:
    if type(payloads) is not dict or tuple(payloads) != OUTPUT_FILES:
        raise AssertionError("output mapping inventory/order drift")
    for name in OUTPUT_FILES:
        if type(payloads[name]) is not bytes:
            raise AssertionError("output payload type drift")
        if _sha(payloads[name]) != EXPECTED_OUTPUT_SHA256[name]:
            raise AssertionError(f"local expected output SHA drift: {name}")
    snapshot = (
        tuple(local_snapshot)
        if local_snapshot is not None
        else _build_local_source_snapshot()
    )
    if (
        len(snapshot) != 34
        or tuple(item.relative_path for item in snapshot) != SOURCE_PATHS
    ):
        raise AssertionError("local source snapshot inventory drift")
    expected_rows = (
        (API_FILENAME, API_COLUMNS, _expected_api_rows()),
        (
            PROTECTED_FILENAME,
            PROTECTED_COLUMNS,
            _expected_protected_rows(),
        ),
        (TRUTH_FILENAME, TRUTH_COLUMNS, _expected_truth_rows()),
        (SAFETY_FILENAME, SAFETY_COLUMNS, _expected_safety_rows()),
    )
    for filename, columns, expected in expected_rows:
        actual = _csv_rows(payloads[filename], columns)
        _assert_recursive_exact(actual, expected, f"$.{filename}")
        if payloads[filename] != _csv_bytes(columns, expected):
            raise AssertionError(f"local full-row reconstruction drift: {filename}")
    issues = _csv_rows(payloads[ISSUE_FILENAME], ISSUE_COLUMNS)
    if len(issues) != 30:
        raise AssertionError("Exact30 row count drift")
    issue_source = _source_content(
        snapshot,
        "covapie_admit_001_to_015_runtime_issue_readiness_inventory.csv",
    )
    if payloads[ISSUE_FILENAME] != issue_source:
        raise AssertionError("Exact30 is not byte-identical")
    manifest = _strict_json(payloads[MANIFEST_FILENAME])
    expected_manifest = _expected_manifest(snapshot)
    _assert_recursive_exact(manifest, expected_manifest)
    _assert_candidate_observations()
    return manifest


def verify_artifacts() -> dict[str, Any]:
    canonical_guard()
    snapshot = _build_local_source_snapshot()
    payloads = _read_exact_outputs()
    _verify_candidate_surface()
    return _verify_semantics(payloads, local_snapshot=snapshot)


def _git_result(root: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ("git", *arguments),
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _matches_stage_family(name: str) -> bool:
    return any(token in name for token in STAGE_FAMILY_TOKENS)


def _bounded_recursive_stage_inventory(
    root: Path,
) -> tuple[dict[Path, os.stat_result], tuple[Path, ...]]:
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
            _identity(item) != expected
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
            child_fd = os.open(name, DIR_FLAGS, dir_fd=parent_fd)
        except OSError as error:
            raise AssertionError(f"{reason} directory open failed") from error
        try:
            assert_directory(os.fstat(child_fd), expected, reason)
        except BaseException:
            os.close(child_fd)
            raise
        return child_fd

    parent_identities: dict[
        int, tuple[int, int, int, int, int, int]
    ] = {}

    def assert_child_binding(
        parent_fd: int,
        name: str,
        child_fd: int,
        expected: tuple[int, int, int, int, int, int],
        reason: str,
    ) -> None:
        assert_directory(
            os.fstat(parent_fd),
            parent_identities[parent_fd],
            reason,
        )
        assert_directory(stat_at(parent_fd, name, reason), expected, reason)
        assert_directory(os.fstat(child_fd), expected, reason)

    def scan_directory(
        directory_fd: int,
        logical: Path,
        expected: tuple[int, int, int, int, int, int],
        *,
        observe_all: bool,
    ) -> None:
        assert_directory(os.fstat(directory_fd), expected, "bounded scan")
        initial_names = directory_names(
            directory_fd,
            "bounded scan initial",
        )
        identities: dict[
            str, tuple[int, int, int, int, int, int]
        ] = {}
        for name in initial_names:
            item = stat_at(directory_fd, name, "bounded scan entry")
            identity = _identity(item)
            identities[name] = identity
            # This is intentionally before the stage-family name filter.
            if stat.S_ISLNK(item.st_mode):
                raise AssertionError("bounded scan generic symlink rejected")
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
                _identity(final_item) != identities[name]
                or stat.S_ISLNK(final_item.st_mode)
            ):
                raise AssertionError("bounded scan entry identity drift")

    def scan_derived_parent(
        directory_fd: int,
        logical: Path,
        expected: tuple[int, int, int, int, int, int],
    ) -> None:
        assert_directory(os.fstat(directory_fd), expected, "derived parent")
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
            identity = _identity(item)
            if stat.S_ISLNK(item.st_mode) or not stat.S_ISDIR(item.st_mode):
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
    root_identity = _identity(root_item)
    if (
        not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
    ):
        raise AssertionError("bounded scan repository root unsafe")
    try:
        root_fd = os.open(root, DIR_FLAGS)
    except OSError as error:
        raise AssertionError(
            "bounded scan repository root open failed"
        ) from error
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
                item = stat_at(parent_fd, name, "bounded root component")
                identity = _identity(item)
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
            _identity(os.lstat(root)) != root_identity
            or _identity(os.fstat(root_fd)) != root_identity
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
    ignored = _git_result(
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
        or relative.suffix.lower() in FORBIDDEN_SUFFIXES
        or item.st_size > MAX_BYTES
    ):
        raise AssertionError("same-stage leaf unsafe")


def _assert_recursive_inventory(
    root: Path = ROOT,
    exact10: Sequence[Path] = EXACT10,
) -> None:
    observed, derived_roots = _bounded_recursive_stage_inventory(root)
    for relative, item in observed.items():
        _assert_stage_candidate_safe(root, relative, item)
    expected_paths = {Path(relative) for relative in exact10}
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
        or set(output_names) != set(OUTPUT_FILES)
    ):
        raise AssertionError("same-stage Exact6 drift")


def _assert_no_sibling_or_stage_residue() -> None:
    _assert_recursive_inventory()


def _read_head_commit(root: Path) -> str:
    result = _git_result(root, "rev-parse", "--verify", "HEAD^{commit}")
    if result.returncode:
        raise AssertionError("HEAD commit query failed")
    try:
        stdout = result.stdout.decode("ascii")
    except UnicodeDecodeError as error:
        raise AssertionError("HEAD commit malformed") from error
    if re.fullmatch(r"[0-9a-f]{40}\n", stdout) is None:
        raise AssertionError("HEAD commit malformed")
    return stdout[:-1]


class LifecycleSnapshot(NamedTuple):
    head: str
    identities: tuple[tuple[str, tuple[int, ...]], ...]
    tracked: frozenset[str]
    untracked: frozenset[str]
    listed_untracked: tuple[str, ...]
    staged: tuple[str, ...]
    unstaged: tuple[str, ...]
    status: bytes
    full_index: bytes


def _nul_paths(content: bytes, reason: str) -> tuple[str, ...]:
    try:
        values = tuple(
            value
            for value in content.decode("utf-8").split("\0")
            if value
        )
    except UnicodeDecodeError as error:
        raise AssertionError(f"{reason} path encoding drift") from error
    if len(values) != len(set(values)):
        raise AssertionError(f"{reason} duplicate path")
    return values


def _capture_lifecycle_state(
    root: Path,
    ordered: Sequence[str],
    *,
    base: str,
) -> LifecycleSnapshot:
    head = _read_head_commit(root)
    ancestor = _git_result(
        root,
        "merge-base",
        "--is-ancestor",
        base,
        head,
    )
    if ancestor.returncode:
        raise AssertionError("base is not an ancestor")
    identities = []
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
            or path.suffix.lower() in FORBIDDEN_SUFFIXES
            or not stat.S_ISREG(item.st_mode)
            or stat.S_ISLNK(item.st_mode)
            or item.st_size > MAX_BYTES
        ):
            raise AssertionError("Exact10 leaf unsafe")
        identities.append((relative, _identity(item)))
        ignored = _git_result(
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
        index = _git_result(
            root,
            "ls-files",
            "--stage",
            "--",
            relative,
        )
        if index.returncode:
            raise AssertionError("candidate index query failed")
        if index.stdout:
            mode, _, stage_number = _parse_index(index.stdout, relative)
            if stage_number != 0 or mode != "100644":
                raise AssertionError("candidate index mode/stage drift")
            tracked.add(relative)
        else:
            untracked.add(relative)
    commands = {
        "untracked": (
            "ls-files",
            "--others",
            "--exclude-standard",
            "-z",
        ),
        "staged": ("diff", "--cached", "--name-only", "-z"),
        "unstaged": ("diff", "--name-only", "-z"),
        "status": (
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
        ),
        "index": ("ls-files", "--stage", "-z"),
    }
    results = {
        name: _git_result(root, *arguments)
        for name, arguments in commands.items()
    }
    if any(result.returncode for result in results.values()):
        raise AssertionError("Git lifecycle query failed")
    listed_untracked = _nul_paths(
        results["untracked"].stdout,
        "untracked",
    )
    staged = _nul_paths(results["staged"].stdout, "staged")
    unstaged = _nul_paths(results["unstaged"].stdout, "unstaged")
    if staged or unstaged:
        raise AssertionError("repository staged/dirty lifecycle")
    if tracked and untracked:
        raise AssertionError("mixed lifecycle")
    if set(listed_untracked) != untracked:
        raise AssertionError("entire untracked inventory is not Exact10")
    return LifecycleSnapshot(
        head=head,
        identities=tuple(identities),
        tracked=frozenset(tracked),
        untracked=frozenset(untracked),
        listed_untracked=listed_untracked,
        staged=staged,
        unstaged=unstaged,
        status=results["status"].stdout,
        full_index=results["index"].stdout,
    )


def _assert_post_commit_history(
    root: Path,
    head: str,
    expected: set[str],
    base: str,
) -> None:
    changed = _git_result(
        root,
        "diff",
        "--name-only",
        "-z",
        f"{base}..{head}",
    )
    commits = _git_result(root, "rev-list", "--reverse", f"{base}..{head}")
    if changed.returncode or commits.returncode:
        raise AssertionError("post_commit history query failed")
    if set(_nul_paths(changed.stdout, "post_commit diff")) != expected:
        raise AssertionError("post_commit Exact10 diff drift")
    commit_ids = tuple(commits.stdout.decode("ascii").splitlines())
    if not commit_ids or commit_ids[-1] != head:
        raise AssertionError("post_commit descendant chain drift")
    for commit in commit_ids:
        if re.fullmatch(r"[0-9a-f]{40}", commit) is None:
            raise AssertionError("post_commit commit identity malformed")
        delta = _git_result(
            root,
            "diff-tree",
            "--root",
            "--no-commit-id",
            "--name-only",
            "-r",
            "-z",
            commit,
        )
        if delta.returncode:
            raise AssertionError("post_commit delta query failed")
        paths = set(_nul_paths(delta.stdout, "post_commit delta"))
        if not paths:
            raise AssertionError("allow-empty HEAD/history drift")
        if not paths <= expected:
            raise AssertionError("post_commit out-of-scope history")
    tree = _git_result(
        root,
        "ls-tree",
        "-r",
        "-z",
        head,
        "--",
        *sorted(expected),
    )
    if tree.returncode:
        raise AssertionError("post_commit tree query failed")
    entries = tuple(entry for entry in tree.stdout.split(b"\0") if entry)
    if len(entries) != 10:
        raise AssertionError("post_commit Exact10 tree count drift")
    for entry in entries:
        try:
            metadata, path = entry.decode().split("\t", 1)
            mode, kind, blob = metadata.split(" ")
        except ValueError as error:
            raise AssertionError("post_commit tree entry malformed") from error
        if (
            path not in expected
            or mode != "100644"
            or kind != "blob"
            or re.fullmatch(r"[0-9a-f]{40}", blob) is None
        ):
            raise AssertionError("post_commit Exact10 tree mode drift")


def _exact10_identities(
    root: Path = ROOT,
    exact10: Sequence[Path] = EXACT10,
) -> tuple[tuple[str, tuple[int, ...]], ...]:
    observed = []
    for relative in exact10:
        item = os.lstat(root / relative)
        if (
            not stat.S_ISREG(item.st_mode)
            or stat.S_ISLNK(item.st_mode)
            or item.st_size > MAX_BYTES
            or relative.suffix.lower() in FORBIDDEN_SUFFIXES
        ):
            raise AssertionError(f"Exact10 unsafe: {relative}")
        observed.append((relative.as_posix(), _identity(item)))
    return tuple(observed)


def verify_lifecycle(
    root: Path = ROOT,
    exact10: Sequence[Path] = EXACT10,
    *,
    base: str = BASE_COMMIT,
) -> str:
    root = Path(os.path.abspath(root))
    ordered = tuple(path.as_posix() for path in exact10)
    expected = set(ordered)
    if len(ordered) != 10 or len(expected) != 10:
        raise AssertionError("candidate is not Exact10")
    initial = _capture_lifecycle_state(root, ordered, base=base)
    _assert_recursive_inventory(root, exact10)
    final = _capture_lifecycle_state(root, ordered, base=base)
    if (
        final.head != initial.head
        or final.identities != initial.identities
        or final.tracked != initial.tracked
        or final.untracked != initial.untracked
        or final.listed_untracked != initial.listed_untracked
        or final.staged != initial.staged
        or final.unstaged != initial.unstaged
        or final.status != initial.status
        or final.full_index != initial.full_index
    ):
        raise AssertionError("final HEAD/inventory/index/identity drift")
    if initial.head == base:
        if initial.tracked or initial.untracked != expected:
            raise AssertionError("pre_commit lifecycle inventory drift")
        return "pre_commit"
    if initial.tracked != expected or initial.untracked:
        raise AssertionError("post_commit lifecycle inventory drift")
    _assert_post_commit_history(root, initial.head, expected, base)
    return "post_commit"


def main() -> int:
    verify_artifacts()
    lifecycle = verify_lifecycle()
    print(
        "CovaPIE ADMIT_015 mandatory training authorization "
        f"enforcement contract v1 passed; lifecycle={lifecycle}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
