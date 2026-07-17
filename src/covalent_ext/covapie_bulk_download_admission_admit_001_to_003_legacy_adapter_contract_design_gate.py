"""Step14AU-E1-E4 Phase 3 legacy-adapter contract design gate.

This module freezes metadata contracts for future ADMIT_001--ADMIT_003
adapters.  It deliberately does not import or execute the legacy evaluators,
implement adapters, or modify the Phase 2 runtime registry.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import os
import stat
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any


PROJECT = "CovaPIE"
STEP = "Step14AU-E1-E4 Phase 3"
STAGE = (
    "covapie_bulk_download_admission_admit_001_to_003_"
    "legacy_adapter_contract_design_gate_v1"
)
EXPECTED_BASE_COMMIT = "dfa3dbf06046b6db3b05f15a7dec79b96db61106"
EXPECTED_BASE_SUBJECT = "add CovaPIE minimal unified admission dispatch shell v1"
MANIFEST_SCHEMA_VERSION = (
    "covapie_admit_001_to_003_legacy_adapter_contract_design_manifest_v1"
)
RESULT_SCHEMA_VERSION = "covapie_unified_admission_rule_evaluation_v1"
RECOMMENDED_NEXT_STEP = (
    "implement_covapie_unified_admission_legacy_adapters_and_register_"
    "admit_001_to_003_v1"
)
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

PHASE2_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004_v1"
)
ADMIT001_EXAMPLE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_candidate_record_id_semantics_design_gate_v1"
)
ADMIT002_EXAMPLE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_pdb_identifier_semantics_design_gate_v1"
)
ADMIT003_EXAMPLE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_ligand_comp_id_semantics_design_gate_v1"
)
PHASE1_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1"
)

SOURCE_PATHS = tuple(
    Path(value)
    for value in (
        "src/covalent_ext/covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004.py",
        str(PHASE2_ROOT / "covapie_minimal_unified_dispatch_shell_contract.csv"),
        str(PHASE2_ROOT / "covapie_minimal_unified_dispatch_registry_and_routing_audit.csv"),
        str(PHASE2_ROOT / "covapie_minimal_unified_dispatch_shell_issue_inventory.csv"),
        str(PHASE2_ROOT / "covapie_minimal_unified_dispatch_shell_manifest.json"),
        "src/covalent_ext/covapie_bulk_download_admission_candidate_record_id_semantics_integration_gate.py",
        "src/covalent_ext/covapie_bulk_download_admission_candidate_record_id_semantics_design_gate.py",
        str(ADMIT001_EXAMPLE_ROOT / "covapie_candidate_record_id_semantics_examples.csv"),
        "src/covalent_ext/covapie_bulk_download_admission_pdb_identifier_semantics_integration_gate.py",
        "src/covalent_ext/covapie_bulk_download_admission_pdb_identifier_semantics_design_gate.py",
        str(ADMIT002_EXAMPLE_ROOT / "covapie_pdb_identifier_normalization_examples.csv"),
        "src/covalent_ext/covapie_bulk_download_admission_ligand_comp_id_semantics_integration_gate.py",
        "src/covalent_ext/covapie_bulk_download_admission_ligand_comp_id_semantics_design_gate.py",
        str(ADMIT003_EXAMPLE_ROOT / "covapie_ligand_comp_id_semantics_examples.csv"),
        str(PHASE1_ROOT / "covapie_unified_admission_evaluator_and_context_routing_matrix.csv"),
        str(PHASE1_ROOT / "covapie_unified_admission_result_schema_and_outcome_contract.csv"),
    )
)
SOURCE_SHA256 = dict(
    zip(
        SOURCE_PATHS,
        (
            "46023c4c3fc221a3e87c513210079e6ef5909ed7c377c1b52dc564fcf171f978",
            "b3b157823b1381066b42e453e5005998bea024de5b7ce697587ec5c59d5ece0d",
            "74945a7d26507d17442a5eb7af925c0ae231be2ba8baacd4a408fffbba4d1c07",
            "5295ee97d8cc3c81cd376116c4dc87489e1b04a65d700a6d08a927d5c72a9951",
            "702492ff08760f3cddcdedd724f8078795d998a736958c87bb39642fa793c097",
            "3246a131a3815aa184338637edef6d8c9020b2dc23f41794e5697812467d269b",
            "625b1b5e2e4da30aa0fff80efd8fd3ceaceb1807bd3a376d169f5374bbd6fda7",
            "1654d36a42cd405866ed152750508dbc46ed78371b7ebb25e47e8bfe9c8bbb9e",
            "c78ed4986551913dea75dc220609f97154941ebda5afffaa84ff252e9d36df83",
            "74395681955025519e35569b8d7353139e4363a840908d0749f5ea5c2cb51e0d",
            "35ea09ae36ddf2311b1dcf5a313d18e62888c68e542eb068bd98c04900379ce9",
            "8d616a02b5f87ea98be3029879d55acd3c06c26e7286a46cb293bd6a4a7f6e11",
            "2623377368459484daf25828db556fc6e6a2436893c70497f0628d95ffbb1792",
            "64a5ef19ceb0d37f37af65a5638d844e33de997ccfa3af4df61de0779ab75af6",
            "2d09f6ab5aa9c64419e7e7c4a90f6562a2883007f9b3ef82258a69b9df181b05",
            "b09d1bc265cae80296450390c3486a942a9ac16fbd689331770e74024f33bbfa",
        ),
        strict=True,
    )
)
(
    PHASE2_SOURCE_PATH,
    PHASE2_CONTRACT_PATH,
    PHASE2_REGISTRY_PATH,
    PHASE2_ISSUE_PATH,
    PHASE2_MANIFEST_PATH,
    ADMIT001_INTEGRATION_PATH,
    ADMIT001_DESIGN_PATH,
    ADMIT001_EXAMPLES_PATH,
    ADMIT002_INTEGRATION_PATH,
    ADMIT002_DESIGN_PATH,
    ADMIT002_EXAMPLES_PATH,
    ADMIT003_INTEGRATION_PATH,
    ADMIT003_DESIGN_PATH,
    ADMIT003_EXAMPLES_PATH,
    PHASE1_ROUTING_PATH,
    PHASE1_RESULT_PATH,
) = SOURCE_PATHS

CONTRACT_FILENAME = "covapie_admit_001_to_003_legacy_adapter_contract_matrix.csv"
REASON_FILENAME = "covapie_admit_001_to_003_legacy_reason_outcome_mapping_matrix.csv"
ROUTING_FILENAME = "covapie_admit_001_to_003_adapter_routing_and_projection_matrix.csv"
SAFETY_FILENAME = "covapie_admit_001_to_003_legacy_adapter_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_001_to_003_legacy_adapter_issue_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_001_to_003_legacy_adapter_contract_design_manifest.json"
CSV_OUTPUTS = (
    CONTRACT_FILENAME,
    REASON_FILENAME,
    ROUTING_FILENAME,
    SAFETY_FILENAME,
    ISSUE_FILENAME,
)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)

CONTRACT_COLUMNS = (
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
)
REASON_COLUMNS = (
    "mapping_order",
    "admission_rule_id",
    "rule_reason_order",
    "legacy_blocking_reason",
    "unified_outcome",
    "unified_passed",
    "unified_blocks_candidate",
    "legacy_reason_reachable_after_context_prevalidation",
    "context_prevalidation_disposition",
    "mapping_contract_passed",
)
ROUTING_COLUMNS = (
    "admission_rule_id",
    "contract_order",
    "contract_area",
    "contract_item",
    "exact_requirement",
    "failure_disposition",
    "dispatch_error_reason",
    "legacy_evaluator_called_on_failure",
    "contract_passed",
)
SAFETY_COLUMNS = (
    "safety_item",
    "expected_executed",
    "observed_executed",
    "safety_passed",
)
ISSUE_COLUMNS = (
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

RULE_SPECS = MappingProxyType(
    {
        "ADMIT_001": {
            "rule_name": "unique_candidate_identity",
            "callable": "evaluate_admit_001_candidate_record_id",
            "parameters": ("candidate_record_id", "batch_candidate_record_ids"),
            "keys": (
                "admission_rule_id",
                "passed",
                "normalized_candidate_record_id",
                "blocking_reason",
            ),
            "string_fields": (
                "admission_rule_id",
                "normalized_candidate_record_id",
                "blocking_reason",
            ),
            "adapter_id": "covapie_admit_001_unified_adapter_v1",
            "candidate_field": "candidate_record_id",
            "runtime_batch_item": "batch_candidate_record_ids",
            "allowed_outcomes": ("passed", "blocked", "invalid"),
            "normalized_source": "normalized_candidate_record_id",
            "integration_path": ADMIT001_INTEGRATION_PATH,
            "design_path": ADMIT001_DESIGN_PATH,
            "examples_path": ADMIT001_EXAMPLES_PATH,
            "non_mapping_reason": "ADMIT_001_CANDIDATE_RECORD_MAPPING_INVALID",
            "missing_reason": "ADMIT_001_CANDIDATE_FIELD_MISSING:candidate_record_id",
            "static_policy": "candidate_record_id_contract",
            "source_type_failure_reason": "ADMIT_001_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID",
            "source_invariant_failure_reason": "ADMIT_001_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
            "unknown_reason_failure_reason": "ADMIT_001_UNIFIED_ADAPTER_REASON_UNMAPPED",
            "semantic_oracle_callable": "evaluate_candidate_record_id_batch_uniqueness",
            "semantic_oracle_parameters": ("candidate_record_id", "batch_candidate_record_ids"),
            "semantic_oracle_source_parameters": ("candidate_record_id", "batch_candidate_record_ids"),
            "expected_legacy_result_projection": (
                "admission_rule_id=ADMIT_001;passed=oracle.passed;"
                "normalized_candidate_record_id=oracle.canonical_candidate_record_id;"
                "blocking_reason=oracle.blocking_reason"
            ),
        },
        "ADMIT_002": {
            "rule_name": "valid_pdb_id_format",
            "callable": "evaluate_admit_002_pdb_identifier",
            "parameters": ("value",),
            "keys": (
                "admission_rule_id",
                "passed",
                "canonical_pdb_id",
                "input_form",
                "blocking_reason",
            ),
            "string_fields": (
                "admission_rule_id",
                "canonical_pdb_id",
                "input_form",
                "blocking_reason",
            ),
            "adapter_id": "covapie_admit_002_unified_adapter_v1",
            "candidate_field": "pdb_id",
            "runtime_batch_item": "",
            "allowed_outcomes": ("passed", "invalid"),
            "normalized_source": "canonical_pdb_id",
            "integration_path": ADMIT002_INTEGRATION_PATH,
            "design_path": ADMIT002_DESIGN_PATH,
            "examples_path": ADMIT002_EXAMPLES_PATH,
            "non_mapping_reason": "ADMIT_002_CANDIDATE_RECORD_MAPPING_INVALID",
            "missing_reason": "ADMIT_002_CANDIDATE_FIELD_MISSING:pdb_id",
            "static_policy": "pdb_id_format_contract",
            "source_type_failure_reason": "ADMIT_002_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID",
            "source_invariant_failure_reason": "ADMIT_002_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
            "unknown_reason_failure_reason": "ADMIT_002_UNIFIED_ADAPTER_REASON_UNMAPPED",
            "semantic_oracle_callable": "normalize_pdb_identifier",
            "semantic_oracle_parameters": ("pdb_id",),
            "semantic_oracle_source_parameters": ("value",),
            "expected_legacy_result_projection": (
                "admission_rule_id=ADMIT_002;passed=oracle.syntax_valid;"
                "canonical_pdb_id=oracle.canonical_pdb_id;input_form=oracle.input_form;"
                "blocking_reason=oracle.blocking_reason"
            ),
        },
        "ADMIT_003": {
            "rule_name": "ligand_or_het_identity_present",
            "callable": "evaluate_admit_003_ligand_comp_id",
            "parameters": ("ligand_comp_id",),
            "keys": (
                "admission_rule_id",
                "passed",
                "canonical_ligand_comp_id",
                "blocking_reason",
            ),
            "string_fields": (
                "admission_rule_id",
                "canonical_ligand_comp_id",
                "blocking_reason",
            ),
            "adapter_id": "covapie_admit_003_unified_adapter_v1",
            "candidate_field": "ligand_comp_id",
            "runtime_batch_item": "",
            "allowed_outcomes": ("passed", "invalid"),
            "normalized_source": "canonical_ligand_comp_id",
            "integration_path": ADMIT003_INTEGRATION_PATH,
            "design_path": ADMIT003_DESIGN_PATH,
            "examples_path": ADMIT003_EXAMPLES_PATH,
            "non_mapping_reason": "ADMIT_003_CANDIDATE_RECORD_MAPPING_INVALID",
            "missing_reason": "ADMIT_003_CANDIDATE_FIELD_MISSING:ligand_comp_id",
            "static_policy": "ligand_comp_id_contract",
            "source_type_failure_reason": "ADMIT_003_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID",
            "source_invariant_failure_reason": "ADMIT_003_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
            "unknown_reason_failure_reason": "ADMIT_003_UNIFIED_ADAPTER_REASON_UNMAPPED",
            "semantic_oracle_callable": "normalize_ligand_comp_id",
            "semantic_oracle_parameters": ("ligand_comp_id",),
            "semantic_oracle_source_parameters": ("value",),
            "expected_legacy_result_projection": (
                "admission_rule_id=ADMIT_003;passed=oracle.passed;"
                "canonical_ligand_comp_id=oracle.canonical_ligand_comp_id;"
                "blocking_reason=oracle.blocking_reason"
            ),
        },
    }
)

REASON_SPECS = MappingProxyType(
    {
        "ADMIT_001": (
            ("", "passed"),
            ("candidate_record_id_not_exact_str", "invalid"),
            ("candidate_record_id_empty", "invalid"),
            ("candidate_record_id_non_ascii", "invalid"),
            ("candidate_record_id_length_out_of_range", "invalid"),
            ("candidate_record_id_pattern_invalid", "invalid"),
            ("candidate_record_id_missing_from_batch", "blocked"),
            ("candidate_record_id_repeated_in_batch", "blocked"),
            ("batch_candidate_record_ids_not_globally_unique", "blocked"),
        ),
        "ADMIT_002": (
            ("", "passed"),
            ("pdb_id_missing", "invalid"),
            ("pdb_id_not_string", "invalid"),
            ("pdb_id_empty", "invalid"),
            ("pdb_id_surrounding_whitespace_forbidden", "invalid"),
            ("pdb_id_non_ascii_forbidden", "invalid"),
            ("pdb_id_format_invalid", "invalid"),
            ("pdb_id_length_invalid", "invalid"),
        ),
        "ADMIT_003": (
            ("", "passed"),
            ("LIGAND_COMP_ID_TYPE_INVALID", "invalid"),
            ("LIGAND_COMP_ID_EMPTY", "invalid"),
            ("LIGAND_COMP_ID_NON_ASCII", "invalid"),
            ("LIGAND_COMP_ID_LENGTH_INVALID", "invalid"),
            ("LIGAND_COMP_ID_SYNTAX_INVALID", "invalid"),
        ),
    }
)
ADMIT001_CONTEXT_PREVALIDATED_REASONS = (
    "batch_candidate_record_ids_invalid_type",
    "batch_candidate_record_ids_empty",
    "batch_candidate_record_id_member_invalid",
)
EXECUTION_PRECEDENCE_CONTRACT = (
    "1:rule-ID validation|"
    "2:known/registered/adapter-ready validation|"
    "3:runtime context routing validation|"
    "4:candidate Mapping validation|"
    "5:required candidate-field validation|"
    "6:legacy evaluator call|"
    "7:exact legacy-result type/key/field validation|"
    "8:legacy-result semantic invariant and semantic-oracle equivalence validation|"
    "9:reason-to-outcome mapping|"
    "10:UnifiedAdmissionRuleEvaluation construction"
)
CONTEXT_ERROR_REASONS = MappingProxyType(
    {
        ("ADMIT_001", "batch_context_1_mapping"): "ADMIT_001_BATCH_CONTEXT_MAPPING_REQUIRED",
        ("ADMIT_001", "batch_context_2_key_presence"): "ADMIT_001_BATCH_CANDIDATE_RECORD_IDS_REQUIRED",
        ("ADMIT_001", "batch_context_3_exact_container"): "ADMIT_001_BATCH_CANDIDATE_RECORD_IDS_EXACT_LIST_OR_TUPLE_REQUIRED",
        ("ADMIT_001", "batch_context_4_nonempty"): "ADMIT_001_BATCH_CANDIDATE_RECORD_IDS_NONEMPTY_REQUIRED",
        ("ADMIT_001", "batch_context_5_member_syntax"): "ADMIT_001_BATCH_CANDIDATE_RECORD_ID_MEMBER_INVALID",
        ("ADMIT_001", "evaluation_context_6"): "ADMIT_001_EVALUATION_CONTEXT_MUST_BE_NONE",
        ("ADMIT_001", "download_result_context_7"): "ADMIT_001_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
        ("ADMIT_001", "stage_authorization_context_8"): "ADMIT_001_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
        ("ADMIT_002", "batch_context_1"): "ADMIT_002_BATCH_CONTEXT_MUST_BE_NONE",
        ("ADMIT_002", "evaluation_context_2"): "ADMIT_002_EVALUATION_CONTEXT_MUST_BE_NONE",
        ("ADMIT_002", "download_result_context_3"): "ADMIT_002_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
        ("ADMIT_002", "stage_authorization_context_4"): "ADMIT_002_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
        ("ADMIT_003", "batch_context_1"): "ADMIT_003_BATCH_CONTEXT_MUST_BE_NONE",
        ("ADMIT_003", "evaluation_context_2"): "ADMIT_003_EVALUATION_CONTEXT_MUST_BE_NONE",
        ("ADMIT_003", "download_result_context_3"): "ADMIT_003_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
        ("ADMIT_003", "stage_authorization_context_4"): "ADMIT_003_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
    }
)
LEGACY_VALUE_INVARIANT_CONTRACTS = MappingProxyType(
    {
        "ADMIT_001": (
            "admission_rule_id exact ADMIT_001;legacy passed exact bool and equals "
            "(mapped outcome == passed);passed=>reason empty,normalized_candidate_record_id "
            "nonempty exact str and equals original candidate_record_id;blocked=>reason in "
            "candidate_record_id_missing_from_batch|candidate_record_id_repeated_in_batch|"
            "batch_candidate_record_ids_not_globally_unique,normalized_candidate_record_id "
            "nonempty exact str and equals original candidate_record_id;invalid=>reason in "
            "candidate_record_id_not_exact_str|candidate_record_id_empty|"
            "candidate_record_id_non_ascii|candidate_record_id_length_out_of_range|"
            "candidate_record_id_pattern_invalid,normalized_candidate_record_id empty"
        ),
        "ADMIT_002": (
            "admission_rule_id exact ADMIT_002;legacy passed exact bool and equals "
            "(mapped outcome == passed);passed=>reason empty,canonical_pdb_id exact str "
            "matching ^pdb_[a-z0-9]{8}$,input_form in "
            "legacy_4_character|extended_12_character;invalid=>reason in "
            "pdb_id_missing|pdb_id_not_string|pdb_id_empty|"
            "pdb_id_surrounding_whitespace_forbidden|pdb_id_non_ascii_forbidden|"
            "pdb_id_format_invalid|pdb_id_length_invalid,canonical_pdb_id empty,"
            "input_form exact invalid"
        ),
        "ADMIT_003": (
            "admission_rule_id exact ADMIT_003;legacy passed exact bool and equals "
            "(mapped outcome == passed);passed=>reason empty,original ligand_comp_id "
            "exact str,canonical_ligand_comp_id nonempty exact str and equals original "
            "ligand_comp_id.upper() and matches ^[A-Z0-9]{1,32}$;invalid=>reason in "
            "LIGAND_COMP_ID_TYPE_INVALID|LIGAND_COMP_ID_EMPTY|LIGAND_COMP_ID_NON_ASCII|"
            "LIGAND_COMP_ID_LENGTH_INVALID|LIGAND_COMP_ID_SYNTAX_INVALID,"
            "canonical_ligand_comp_id empty"
        ),
    }
)

TRUE_READINESS = (
    "admit_001_to_003_legacy_adapter_contracts_design_frozen",
    "admit_001_legacy_adapter_contract_design_ready",
    "admit_002_legacy_adapter_contract_design_ready",
    "admit_003_legacy_adapter_contract_design_ready",
    "legacy_result_keysets_frozen",
    "legacy_reason_outcome_mapping_frozen",
    "candidate_projection_contracts_frozen",
    "runtime_context_routing_contracts_frozen",
    "static_policy_dependency_boundary_frozen",
    "unified_field_mapping_contracts_frozen",
    "ready_for_admit_001_to_003_legacy_adapter_implementation",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "legacy_evaluator_adapters_implemented",
    "admit_001_adapter_implemented",
    "admit_002_adapter_implemented",
    "admit_003_adapter_implemented",
    "admit_001_registered_in_engine",
    "admit_002_registered_in_engine",
    "admit_003_registered_in_engine",
    "phase2_runtime_registry_modified",
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
    "legacy_callable_ast_validation",
    "legacy_result_keyset_design",
    "legacy_reason_inventory_validation",
    "reason_outcome_mapping_design",
    "candidate_projection_contract_design",
    "runtime_context_routing_contract_design",
    "static_policy_dependency_boundary_design",
    "unified_field_mapping_design",
    "issue_transition_design",
)
FALSE_SAFETY_ITEMS = (
    "raw_read",
    "provenance_reference_dereference",
    "legacy_evaluator_execution",
    "adapter_implementation",
    "phase2_runtime_modification",
    "evaluator_registry_modification",
    "admit_001_registration",
    "admit_002_registration",
    "admit_003_registration",
    "admit_004_execution",
    "admit_005_to_015_execution",
    "evaluate_all_rules_implementation",
    "combined_candidate_verdict_implementation",
    "cross_rule_aggregation",
    "candidate_record_materialization",
    "real_candidate_evaluation",
    "exact11_real_evaluation",
    "parser_execution",
    "provider_execution",
    "network",
    "download",
    "checkpoint",
    "torch",
    "numpy",
    "rdkit",
    "model_forward_loss_training",
)


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
        ["git", *arguments],
        cwd=repo_root,
        text=text,
        capture_output=True,
        check=False,
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
    """Inspect source metadata without reading source content bytes."""
    if not _safe_relative_path(path):
        return False
    try:
        metadata = os.lstat(repo_root / path)
    except OSError:
        return False
    tracked = _git(
        ["ls-files", "--error-unmatch", "--", path.as_posix()], repo_root
    )
    tree = _git(
        ["ls-tree", EXPECTED_BASE_COMMIT, "--", path.as_posix()], repo_root
    )
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
    """Complete all Exact16 structural checks before the first byte read."""
    if (
        len(SOURCE_PATHS) != 16
        or len(set(SOURCE_PATHS)) != 16
        or tuple(SOURCE_SHA256) != SOURCE_PATHS
        or any(len(value) != 64 for value in SOURCE_SHA256.values())
    ):
        raise ValueError("Exact16 source boundary shape invalid")
    _validate_expected_base_lineage(repo_root, head_ref=head_ref)
    structural = tuple(
        _structural_source_check(path, repo_root) for path in SOURCE_PATHS
    )
    if not all(structural):
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
        and len(value.records) == 16
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
    matches = tuple(
        record for record in snapshot.records if record.relative_path == path
    )
    if len(matches) != 1:
        raise ValueError("frozen source missing or duplicate")
    return matches[0]


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


def _function_node(tree: ast.Module, name: str) -> ast.FunctionDef:
    matches = tuple(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )
    if len(matches) != 1:
        raise ValueError(f"legacy callable missing or duplicate: {name}")
    return matches[0]


def _legacy_callable_shape(
    tree: ast.Module, name: str
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    node = _function_node(tree, name)
    arguments = node.args
    if (
        arguments.posonlyargs
        or arguments.vararg is not None
        or arguments.kwonlyargs
        or arguments.kwarg is not None
        or arguments.defaults
        or arguments.kw_defaults
    ):
        raise ValueError(f"legacy callable signature invalid: {name}")
    parameters = tuple(argument.arg for argument in arguments.args)
    returns = tuple(
        child
        for child in ast.walk(node)
        if isinstance(child, ast.Return) and isinstance(child.value, ast.Dict)
    )
    if len(returns) != 1:
        raise ValueError(f"legacy callable exact dict return missing: {name}")
    keys: list[str] = []
    for key in returns[0].value.keys:
        if not isinstance(key, ast.Constant) or type(key.value) is not str:
            raise ValueError(f"legacy callable dict key invalid: {name}")
        keys.append(key.value)
    return parameters, tuple(keys)


def _pure_oracle_parameters(tree: ast.Module, name: str) -> tuple[str, ...]:
    node = _function_node(tree, name)
    arguments = node.args
    if (
        arguments.posonlyargs
        or arguments.vararg is not None
        or arguments.kwonlyargs
        or arguments.kwarg is not None
        or arguments.defaults
        or arguments.kw_defaults
    ):
        raise ValueError(f"semantic oracle signature invalid: {name}")
    return tuple(argument.arg for argument in arguments.args)


def _registry_literal_keys(tree: ast.Module) -> tuple[str, ...]:
    assignments = tuple(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "EVALUATOR_REGISTRY"
    )
    if len(assignments) != 1:
        raise ValueError("Phase 2 registry assignment missing or duplicate")
    value = assignments[0].value
    if (
        not isinstance(value, ast.Call)
        or not isinstance(value.func, ast.Name)
        or value.func.id != "MappingProxyType"
        or len(value.args) != 1
        or value.keywords
        or not isinstance(value.args[0], ast.Dict)
    ):
        raise ValueError("Phase 2 registry literal shape invalid")
    keys = []
    for key in value.args[0].keys:
        if not isinstance(key, ast.Constant) or type(key.value) is not str:
            raise ValueError("Phase 2 registry key invalid")
        keys.append(key.value)
    return tuple(keys)


def _string_constants(tree: ast.Module) -> set[str]:
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and type(node.value) is str
    }


def _keyed(
    rows: Sequence[Mapping[str, str]], key: str
) -> dict[str, Mapping[str, str]]:
    result: dict[str, Mapping[str, str]] = {}
    for row in rows:
        value = row.get(key, "")
        if not value or value in result:
            raise ValueError("missing or duplicate row key")
        result[value] = row
    return result


def _validate_examples(
    document: CsvDocument, rule_id: str, expected_reasons: set[str]
) -> None:
    expected_header = {
        "ADMIT_001": (
            "example_id",
            "example_scope",
            "input_type",
            "input_display",
            "batch_type",
            "batch_display",
            "expected_syntax_valid",
            "expected_batch_valid",
            "expected_passed",
            "expected_canonical_candidate_record_id",
            "expected_blocking_reason",
            "observed_syntax_valid",
            "observed_batch_valid",
            "observed_passed",
            "observed_canonical_candidate_record_id",
            "observed_blocking_reason",
            "example_passed",
        ),
        "ADMIT_002": (
            "example_id",
            "input_representation",
            "input_type",
            "expected_input_form",
            "expected_syntax_valid",
            "expected_canonical_pdb_id",
            "expected_normalization_applied",
            "expected_blocking_reason",
            "example_passed",
        ),
        "ADMIT_003": (
            "example_id",
            "example_class",
            "input_kind",
            "input_literal",
            "expected_passed",
            "expected_canonical_ligand_comp_id",
            "expected_blocking_reason",
            "observed_passed",
            "observed_canonical_ligand_comp_id",
            "observed_blocking_reason",
            "example_passed",
        ),
    }[rule_id]
    if document.header != expected_header or not document.rows:
        raise ValueError(f"{rule_id} committed examples schema invalid")
    if any(row["example_passed"] != "true" for row in document.rows):
        raise ValueError(f"{rule_id} committed examples contain failures")
    observed_reasons = {
        row["expected_blocking_reason"]
        for row in document.rows
        if row["expected_blocking_reason"]
    }
    if not expected_reasons <= observed_reasons:
        raise ValueError(f"{rule_id} committed reason examples incomplete")


def _validate_predecessors(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    phase2_tree = _ast_document(snapshot, PHASE2_SOURCE_PATH)
    if _registry_literal_keys(phase2_tree) != ("ADMIT_004",):
        raise ValueError("Phase 2 runtime registry changed")
    evaluate_node = _function_node(phase2_tree, "evaluate_admission_rule")
    if tuple(argument.arg for argument in evaluate_node.args.args) != (
        "admission_rule_id",
        "candidate_record",
    ) or tuple(argument.arg for argument in evaluate_node.args.kwonlyargs) != (
        "batch_context",
        "evaluation_context",
        "download_result_context",
        "stage_authorization_context",
    ):
        raise ValueError("Phase 2 public runtime signature changed")

    phase2_contract = _csv_document(snapshot, PHASE2_CONTRACT_PATH)
    phase2_registry = _csv_document(snapshot, PHASE2_REGISTRY_PATH)
    phase2_issues = _csv_document(snapshot, PHASE2_ISSUE_PATH)
    phase2_manifest = _json_document(snapshot, PHASE2_MANIFEST_PATH)
    if phase2_contract.header != (
        "contract_id",
        "contract_area",
        "contract_statement",
        "expected_value",
        "observed_value",
        "contract_passed",
    ) or any(row["contract_passed"] != "true" for row in phase2_contract.rows):
        raise ValueError("Phase 2 contract evidence invalid")
    if phase2_registry.header != (
        "admission_rule_id",
        "known_rule",
        "callable_discovered",
        "adapter_ready",
        "registered",
        "dispatch_disposition",
        "audit_passed",
    ) or tuple(
        row["admission_rule_id"] for row in phase2_registry.rows
    ) != tuple(f"ADMIT_{index:03d}" for index in range(1, 16)):
        raise ValueError("Phase 2 registry audit evidence invalid")
    if tuple(
        row["admission_rule_id"]
        for row in phase2_registry.rows
        if row["registered"] == "true"
    ) != ("ADMIT_004",) or any(
        row["audit_passed"] != "true" for row in phase2_registry.rows
    ):
        raise ValueError("Phase 2 registered rule evidence invalid")
    if phase2_issues.header != ISSUE_COLUMNS or len(phase2_issues.rows) != 12:
        raise ValueError("Phase 2 issue inventory shape invalid")
    issue_map = _keyed(phase2_issues.rows, "issue_id")
    if (
        phase2_manifest.get("registered_rule_ids") != ["ADMIT_004"]
        or phase2_manifest.get("registered_rule_count") != 1
        or phase2_manifest.get("admit_001_registered_in_engine") is not False
        or phase2_manifest.get("admit_002_registered_in_engine") is not False
        or phase2_manifest.get("admit_003_registered_in_engine") is not False
        or phase2_manifest.get("all_checks_passed") is not True
        or phase2_manifest.get("output_sha256", {}).get(PHASE2_CONTRACT_PATH.name)
        != SOURCE_SHA256[PHASE2_CONTRACT_PATH]
        or phase2_manifest.get("output_sha256", {}).get(PHASE2_REGISTRY_PATH.name)
        != SOURCE_SHA256[PHASE2_REGISTRY_PATH]
        or phase2_manifest.get("output_sha256", {}).get(PHASE2_ISSUE_PATH.name)
        != SOURCE_SHA256[PHASE2_ISSUE_PATH]
    ):
        raise ValueError("Phase 2 manifest evidence invalid")
    if (
        issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["status"] != "open"
        or issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["severity"]
        != "blocking"
        or issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["issue_count"]
        != "11"
        or issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["status"]
        != "open"
        or issue_map[
            "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"
        ]["status"]
        != "open"
    ):
        raise ValueError("Phase 2 blocking issue evidence invalid")

    phase1_routing = _csv_document(snapshot, PHASE1_ROUTING_PATH)
    phase1_result = _csv_document(snapshot, PHASE1_RESULT_PATH)
    routing_map = _keyed(phase1_routing.rows, "admission_rule_id")
    if len(routing_map) != 15:
        raise ValueError("Phase 1 routing cardinality invalid")
    for rule_id, spec in RULE_SPECS.items():
        row = routing_map[rule_id]
        expected_batch = spec["runtime_batch_item"]
        if (
            row["admission_rule_name"] != spec["rule_name"]
            or row["candidate_field_dependencies"] != spec["candidate_field"]
            or row["batch_context_dependencies"] != expected_batch
            or row["evaluation_context_dependencies"] != spec["static_policy"]
            or row["evaluator_callable_name"] != spec["callable"]
            or row["callable_discovered"] != "true"
            or row["result_adapter_contract_status"] != "unresolved"
        ):
            raise ValueError(f"Phase 1 routing evidence invalid: {rule_id}")
    result_map = _keyed(phase1_result.rows, "contract_order")
    if (
        len(result_map) != 29
        or result_map["15"]["contract_value"] != RESULT_SCHEMA_VERSION
        or result_map["16"]["contract_value"] != "passed|blocked|invalid|rejected"
        or result_map["25"]["field_name"] != "ADMIT_001|ADMIT_002|ADMIT_003"
        or result_map["25"]["contract_value"] != "adapter_mapping_unresolved"
    ):
        raise ValueError("Phase 1 result contract evidence invalid")

    callable_shapes: dict[str, dict[str, tuple[str, ...]]] = {}
    oracle_shapes: dict[str, dict[str, object]] = {}
    for rule_id, spec in RULE_SPECS.items():
        integration_tree = _ast_document(snapshot, spec["integration_path"])
        parameters, keys = _legacy_callable_shape(integration_tree, spec["callable"])
        if parameters != spec["parameters"] or keys != spec["keys"]:
            raise ValueError(f"legacy callable contract mismatch: {rule_id}")
        design_tree = _ast_document(snapshot, spec["design_path"])
        expected_reason_set = {
            reason for reason, _outcome in REASON_SPECS[rule_id] if reason
        }
        if rule_id == "ADMIT_001":
            expected_reason_set.update(ADMIT001_CONTEXT_PREVALIDATED_REASONS)
        if not expected_reason_set <= _string_constants(design_tree):
            raise ValueError(f"legacy reason inventory mismatch: {rule_id}")
        oracle_parameters = _pure_oracle_parameters(
            design_tree, spec["semantic_oracle_callable"]
        )
        if (
            oracle_parameters != spec["semantic_oracle_source_parameters"]
            or spec["semantic_oracle_callable"] == spec["callable"]
        ):
            raise ValueError(f"pure semantic oracle contract mismatch: {rule_id}")
        _validate_examples(
            _csv_document(snapshot, spec["examples_path"]),
            rule_id,
            expected_reason_set,
        )
        callable_shapes[rule_id] = {"parameters": parameters, "keys": keys}
        oracle_shapes[rule_id] = {
            "callable": spec["semantic_oracle_callable"],
            "source_parameters": oracle_parameters,
            "source_path": spec["design_path"],
        }

    return {
        "phase2_issues": phase2_issues,
        "phase2_manifest": phase2_manifest,
        "phase2_registry": phase2_registry,
        "phase1_routing": phase1_routing,
        "phase1_result": phase1_result,
        "callable_shapes": callable_shapes,
        "oracle_shapes": oracle_shapes,
    }


def _tuple_text(values: Sequence[str]) -> str:
    if not values:
        return "()"
    rendered = ",".join(json.dumps(value) for value in values)
    if len(values) == 1:
        rendered += ","
    return f"({rendered})"


def _invalid_result_payload_text(
    rule_id: str, spec: Mapping[str, Any], reason: str
) -> str:
    return ";".join(
        (
            f"schema_version={RESULT_SCHEMA_VERSION}",
            f"admission_rule_id={rule_id}",
            f"admission_rule_name={spec['rule_name']}",
            "outcome=invalid",
            "passed=false",
            "blocks_candidate=true",
            f"reason={reason}",
            "normalized_values=()",
            "validated_candidate_fields=()",
            f"consumed_candidate_fields={_tuple_text((spec['candidate_field'],))}",
            "consumed_context_items="
            + _tuple_text(
                (spec["runtime_batch_item"],)
                if spec["runtime_batch_item"]
                else ()
            ),
            "evaluator_io_used=false",
            f"adapter_id={spec['adapter_id']}",
            "legacy_evaluator_called=false",
        )
    )


def _adapter_side_invalid_result_contract(
    rule_id: str, spec: Mapping[str, Any]
) -> str:
    return (
        "candidate_non_mapping_unified_result:"
        + _invalid_result_payload_text(rule_id, spec, spec["non_mapping_reason"])
        + "|candidate_missing_field_unified_result:"
        + _invalid_result_payload_text(rule_id, spec, spec["missing_reason"])
    )


def _contract_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for rule_id, spec in RULE_SPECS.items():
        candidate_field = spec["candidate_field"]
        normalized_source = spec["normalized_source"]
        if rule_id == "ADMIT_001":
            validated = (
                f"((\"candidate_record_id\",{normalized_source}),) iff candidate syntax valid; else ()"
            )
        else:
            validated = (
                f"((\"{candidate_field}\",{normalized_source}),) iff passed; else ()"
            )
        input_form_contract = (
            "invariant_only;passed=>legacy_4_character|extended_12_character;"
            "invalid=>invalid;not_projected"
            if rule_id == "ADMIT_002"
            else "not_applicable"
        )
        rows.append(
            {
                "admission_rule_id": rule_id,
                "admission_rule_name": spec["rule_name"],
                "legacy_callable_name": spec["callable"],
                "legacy_callable_parameters": "|".join(spec["parameters"]),
                "legacy_result_exact_type": "dict",
                "legacy_result_key_order": "|".join(spec["keys"]),
                "legacy_exact_string_fields": "|".join(spec["string_fields"]),
                "adapter_id": spec["adapter_id"],
                "candidate_field": candidate_field,
                "runtime_batch_item": spec["runtime_batch_item"],
                "allowed_outcomes": "|".join(spec["allowed_outcomes"]),
                "normalized_values_contract": (
                    f"() iff {normalized_source} empty; else "
                    f"((\"{candidate_field}\",{normalized_source}),)"
                ),
                "validated_candidate_fields_contract": validated,
                "consumed_candidate_fields": _tuple_text((candidate_field,)),
                "consumed_context_items": _tuple_text(
                    (spec["runtime_batch_item"],)
                    if spec["runtime_batch_item"]
                    else ()
                ),
                "evaluator_io_used": "false",
                "input_form_contract": input_form_contract,
                "source_type_failure_reason": spec["source_type_failure_reason"],
                "source_invariant_failure_reason": spec[
                    "source_invariant_failure_reason"
                ],
                "unknown_reason_failure_reason": spec[
                    "unknown_reason_failure_reason"
                ],
                "legacy_value_invariant_contract": LEGACY_VALUE_INVARIANT_CONTRACTS[
                    rule_id
                ],
                "semantic_oracle_callable": spec["semantic_oracle_callable"],
                "semantic_oracle_parameters": "|".join(
                    spec["semantic_oracle_parameters"]
                ),
                "expected_legacy_result_projection": spec[
                    "expected_legacy_result_projection"
                ],
                "legacy_result_oracle_equivalence_required": "true",
                "adapter_side_invalid_result_contract": (
                    _adapter_side_invalid_result_contract(rule_id, spec)
                ),
                "malformed_result_disposition": (
                    "fail_closed:UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY;"
                    "no_partial_unified_result"
                ),
                "unknown_reason_disposition": (
                    "fail_closed:UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY;"
                    "do_not_guess_outcome"
                ),
                "adapter_implemented": "false",
                "registered_in_engine": "false",
                "contract_passed": "true",
            }
        )
    return rows


def _reason_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    mapping_order = 0
    for rule_id, specs in REASON_SPECS.items():
        for rule_reason_order, (reason, outcome) in enumerate(specs, 1):
            mapping_order += 1
            rows.append(
                {
                    "mapping_order": str(mapping_order),
                    "admission_rule_id": rule_id,
                    "rule_reason_order": str(rule_reason_order),
                    "legacy_blocking_reason": reason,
                    "unified_outcome": outcome,
                    "unified_passed": "true" if outcome == "passed" else "false",
                    "unified_blocks_candidate": (
                        "false" if outcome == "passed" else "true"
                    ),
                    "legacy_reason_reachable_after_context_prevalidation": "true",
                    "context_prevalidation_disposition": "not_intercepted",
                    "mapping_contract_passed": "true",
                }
            )
    return rows


def _routing_specs(rule_id: str, spec: Mapping[str, Any]) -> list[tuple[str, str, str, str, str]]:
    candidate_field = spec["candidate_field"]
    common = [
        (
            "execution_order",
            "execution_precedence",
            EXECUTION_PRECEDENCE_CONTRACT,
            "contract_invariant",
            "not_applicable",
        ),
        (
            "routing",
            "rule_id_and_registration",
            "validate rule ID and registration before every context check",
            "dispatch_fail_closed",
            "false",
        )
    ]
    if rule_id == "ADMIT_001":
        contexts = [
            ("routing", "batch_context_1_mapping", "Mapping or Mapping subclass", "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "false"),
            ("routing", "batch_context_2_key_presence", "batch_candidate_record_ids required", "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "false"),
            ("routing", "batch_context_3_exact_container", "type is exactly list or exactly tuple", "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "false"),
            ("routing", "batch_context_4_nonempty", "batch_candidate_record_ids nonempty", "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "false"),
            ("routing", "batch_context_5_member_syntax", "every member satisfies exact candidate-record ID syntax", "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "false"),
            ("routing", "evaluation_context_6", "must be None", "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "false"),
            ("routing", "download_result_context_7", "must be None", "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "false"),
            ("routing", "stage_authorization_context_8", "must be None", "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "false"),
        ]
    else:
        contexts = [
            ("routing", "batch_context_1", "must be None", "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "false"),
            ("routing", "evaluation_context_2", "must be None", "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "false"),
            ("routing", "download_result_context_3", "must be None", "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "false"),
            ("routing", "stage_authorization_context_4", "must be None", "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", "false"),
        ]
    projection = [
        ("candidate_projection", "candidate_record_type", "Mapping or Mapping subclass; non-Mapping yields invalid rule result", spec["non_mapping_reason"], "false"),
        ("candidate_projection", "required_field", f"{candidate_field} must be present; missing yields invalid rule result", spec["missing_reason"], "false"),
        ("candidate_projection", "candidate_non_mapping_unified_result", _invalid_result_payload_text(rule_id, spec, spec["non_mapping_reason"]), "adapter_side_invalid_unified_result", "false"),
        ("candidate_projection", "candidate_missing_field_unified_result", _invalid_result_payload_text(rule_id, spec, spec["missing_reason"]), "adapter_side_invalid_unified_result", "false"),
        ("candidate_projection", "field_value_identity", f"pass original {candidate_field} value object unchanged; no trim/coerce/normalize/copy", "fail_closed_if_violated", "not_applicable"),
        ("candidate_projection", "extra_fields", "do not pass candidate extra fields to legacy evaluator", "fail_closed_if_violated", "not_applicable"),
        ("candidate_projection", "candidate_mutation", "candidate record must not be mutated", "fail_closed_if_violated", "not_applicable"),
    ]
    static_boundary = [
        ("static_policy_boundary", spec["static_policy"], "committed source SHA plus future adapter implementation dependency; caller does not repeat; no dynamic filesystem load or fabricated context", "fail_closed_if_dependency_unavailable", "not_applicable"),
        ("static_policy_boundary", "runtime_evaluation_context", "None; static policy is not runtime caller evidence", "routing_contract_restatement", "not_applicable"),
    ]
    normalized_source = spec["normalized_source"]
    validated_requirement = (
        f"candidate syntax valid => ((\"{candidate_field}\",{normalized_source}),); else ()"
        if rule_id == "ADMIT_001"
        else f"passed => ((\"{candidate_field}\",{normalized_source}),); invalid => ()"
    )
    fields = [
        ("unified_field_mapping", "normalized_values", f"empty source => (); nonempty => ((\"{candidate_field}\",{normalized_source}),)", "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", "not_applicable"),
        ("unified_field_mapping", "validated_candidate_fields", validated_requirement, "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", "not_applicable"),
        ("unified_field_mapping", "consumed_candidate_fields", _tuple_text((candidate_field,)), "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", "not_applicable"),
        ("unified_field_mapping", "consumed_context_items", _tuple_text((spec["runtime_batch_item"],) if spec["runtime_batch_item"] else ()), "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", "not_applicable"),
        ("unified_field_mapping", "evaluator_io_used", "false", "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", "not_applicable"),
        ("unified_field_mapping", "adapter_id", spec["adapter_id"], "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", "not_applicable"),
    ]
    if rule_id == "ADMIT_002":
        fields.append(
            ("adapter_invariant", "input_form", "invariant check only; never project into any UnifiedAdmissionRuleEvaluation field", "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", "not_applicable")
        )
    invariant = [
        ("adapter_invariant", "legacy_result", "exact dict; exact ordered keyset; exact rule ID; passed exact bool; declared strings exact str; passed iff reason empty", "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY;no_partial_unified_result", "not_applicable"),
        ("adapter_invariant", "unknown_nonempty_reason", "reason must exist in exact per-rule mapping; no fallback row", "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY;do_not_guess_outcome", "not_applicable"),
    ]
    return [*common, *contexts, *projection, *static_boundary, *fields, *invariant]


def _routing_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for rule_id, spec in RULE_SPECS.items():
        for order, (area, item, requirement, failure, legacy_called) in enumerate(
            _routing_specs(rule_id, spec), 1
        ):
            rows.append(
                {
                    "admission_rule_id": rule_id,
                    "contract_order": str(order),
                    "contract_area": area,
                    "contract_item": item,
                    "exact_requirement": requirement,
                    "failure_disposition": failure,
                    "dispatch_error_reason": CONTEXT_ERROR_REASONS.get(
                        (rule_id, item), ""
                    ),
                    "legacy_evaluator_called_on_failure": legacy_called,
                    "contract_passed": "true",
                }
            )
    return rows


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


def _issue_rows(source_rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    old_issue = "UNIFIED_ADMISSION_LEGACY_EVALUATOR_ADAPTER_SEMANTICS_UNRESOLVED"
    new_issue = "UNIFIED_ADMISSION_LEGACY_EVALUATOR_ADAPTER_IMPLEMENTATION_PENDING"
    rows: list[dict[str, str]] = []
    replacement_count = 0
    for source in source_rows:
        if source["issue_id"] != old_issue:
            rows.append(dict(source))
            continue
        replacement_count += 1
        rows.append(
            {
                "issue_id": new_issue,
                "issue_type": "implementation_pending",
                "affected_fields": "candidate_record_id|pdb_id|ligand_comp_id",
                "affected_rules": "ADMIT_001|ADMIT_002|ADMIT_003",
                "severity": "blocking",
                "status": "open",
                "blocking_scope": "unified_admission_engine",
                "blocking_reason": new_issue,
                "issue_origin": STAGE,
                "integration_transition": "semantics_frozen_implementation_pending",
                "issue_count": "1",
            }
        )
    if replacement_count != 1:
        raise ValueError("legacy adapter issue replacement cardinality invalid")
    return rows


def _validate_design_rows(
    contract_rows: list[dict[str, str]],
    reason_rows: list[dict[str, str]],
    routing_rows: list[dict[str, str]],
    safety_rows: list[dict[str, str]],
    issue_rows: list[dict[str, str]],
    predecessor: Mapping[str, Any],
) -> None:
    if (
        len(contract_rows) != 3
        or tuple(row["admission_rule_id"] for row in contract_rows)
        != tuple(RULE_SPECS)
        or any(tuple(row) != CONTRACT_COLUMNS for row in contract_rows)
        or any(row["contract_passed"] != "true" for row in contract_rows)
    ):
        raise ValueError("adapter contract matrix invalid")
    for row in contract_rows:
        rule_id = row["admission_rule_id"]
        spec = RULE_SPECS[rule_id]
        if (
            row["source_type_failure_reason"]
            != spec["source_type_failure_reason"]
            or row["source_invariant_failure_reason"]
            != spec["source_invariant_failure_reason"]
            or row["unknown_reason_failure_reason"]
            != spec["unknown_reason_failure_reason"]
            or row["legacy_value_invariant_contract"]
            != LEGACY_VALUE_INVARIANT_CONTRACTS[rule_id]
            or row["semantic_oracle_callable"]
            != spec["semantic_oracle_callable"]
            or row["semantic_oracle_parameters"]
            != "|".join(spec["semantic_oracle_parameters"])
            or row["expected_legacy_result_projection"]
            != spec["expected_legacy_result_projection"]
            or row["legacy_result_oracle_equivalence_required"] != "true"
            or row["adapter_side_invalid_result_contract"]
            != _adapter_side_invalid_result_contract(rule_id, spec)
            or row["consumed_candidate_fields"]
            != _tuple_text((spec["candidate_field"],))
            or row["consumed_context_items"]
            != _tuple_text(
                (spec["runtime_batch_item"],)
                if spec["runtime_batch_item"]
                else ()
            )
        ):
            raise ValueError(f"revised adapter contract invalid: {rule_id}")
    if (
        len(reason_rows) != 23
        or tuple(row["mapping_order"] for row in reason_rows)
        != tuple(str(index) for index in range(1, 24))
        or tuple(
            sum(([(rule_id, reason, outcome) for reason, outcome in specs] for rule_id, specs in REASON_SPECS.items()), [])
        )
        != tuple(
            (row["admission_rule_id"], row["legacy_blocking_reason"], row["unified_outcome"])
            for row in reason_rows
        )
        or any(tuple(row) != REASON_COLUMNS for row in reason_rows)
        or any(row["mapping_contract_passed"] != "true" for row in reason_rows)
        or any(
            row["legacy_blocking_reason"] in ADMIT001_CONTEXT_PREVALIDATED_REASONS
            for row in reason_rows
        )
    ):
        raise ValueError("exact23 reason mapping invalid")
    by_rule_outcomes = {
        rule_id: {
            row["unified_outcome"]
            for row in reason_rows
            if row["admission_rule_id"] == rule_id
        }
        for rule_id in RULE_SPECS
    }
    if by_rule_outcomes != {
        rule_id: set(spec["allowed_outcomes"])
        for rule_id, spec in RULE_SPECS.items()
    }:
        raise ValueError("per-rule outcome subset invalid")
    if (
        len(routing_rows) != 74
        or any(tuple(row) != ROUTING_COLUMNS for row in routing_rows)
        or any(row["contract_passed"] != "true" for row in routing_rows)
    ):
        raise ValueError("routing and projection matrix invalid")
    context_rows = {
        (row["admission_rule_id"], row["contract_item"]): row
        for row in routing_rows
        if row["dispatch_error_reason"]
    }
    if (
        set(context_rows) != set(CONTEXT_ERROR_REASONS)
        or any(
            context_rows[key]["dispatch_error_reason"] != reason
            or context_rows[key]["failure_disposition"]
            != "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID"
            or context_rows[key]["legacy_evaluator_called_on_failure"] != "false"
            for key, reason in CONTEXT_ERROR_REASONS.items()
        )
    ):
        raise ValueError("exact context dispatch reasons invalid")
    precedence_rows = [
        row for row in routing_rows if row["contract_item"] == "execution_precedence"
    ]
    if (
        len(precedence_rows) != 3
        or tuple(row["admission_rule_id"] for row in precedence_rows)
        != tuple(RULE_SPECS)
        or any(
            row["exact_requirement"] != EXECUTION_PRECEDENCE_CONTRACT
            for row in precedence_rows
        )
    ):
        raise ValueError("explicit execution precedence invalid")
    invalid_rows = [
        row
        for row in routing_rows
        if row["contract_item"]
        in (
            "candidate_non_mapping_unified_result",
            "candidate_missing_field_unified_result",
        )
    ]
    if len(invalid_rows) != 6:
        raise ValueError("adapter-side invalid payload cardinality invalid")
    for row in invalid_rows:
        rule_id = row["admission_rule_id"]
        spec = RULE_SPECS[rule_id]
        reason = (
            spec["non_mapping_reason"]
            if row["contract_item"] == "candidate_non_mapping_unified_result"
            else spec["missing_reason"]
        )
        if (
            row["exact_requirement"]
            != _invalid_result_payload_text(rule_id, spec, reason)
            or row["failure_disposition"]
            != "adapter_side_invalid_unified_result"
            or row["dispatch_error_reason"] != ""
            or row["legacy_evaluator_called_on_failure"] != "false"
        ):
            raise ValueError(f"adapter-side invalid payload invalid: {rule_id}")
    if (
        safety_rows != _safety_rows()
        or any(tuple(row) != SAFETY_COLUMNS for row in safety_rows)
    ):
        raise ValueError("safety audit invalid")
    source_issue_rows = [dict(row) for row in predecessor["phase2_issues"].rows]
    if len(issue_rows) != 12 or any(tuple(row) != ISSUE_COLUMNS for row in issue_rows):
        raise ValueError("issue inventory shape invalid")
    for index, (source, current) in enumerate(zip(source_issue_rows, issue_rows, strict=True)):
        if index == 9:
            if current["issue_id"] != "UNIFIED_ADMISSION_LEGACY_EVALUATOR_ADAPTER_IMPLEMENTATION_PENDING":
                raise ValueError("issue replacement position invalid")
        elif current != source:
            raise ValueError("unrelated Phase 2 issue changed")
    issue_map = _keyed(issue_rows, "issue_id")
    if (
        issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["issue_count"] != "11"
        or issue_map["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["status"] != "open"
        or issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["severity"] != "blocking"
        or issue_map["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["status"] != "open"
    ):
        raise ValueError("preserved blocking issue invalid")


def _empty_state(
    snapshot: FrozenSourceSnapshot | None = None,
    failure: str = "SOURCE_BOUNDARY_VALIDATION_FAILED",
) -> dict[str, Any]:
    return {
        "source_snapshot": snapshot,
        "source_ok": False,
        "predecessor_ok": False,
        "contract_rows": [],
        "reason_rows": [],
        "routing_rows": [],
        "safety_rows": [],
        "issue_rows": [],
        "all_checks_passed": False,
        "validation_failures": [failure],
    }


def build_phase3_design_state(
    source_snapshot: FrozenSourceSnapshot | None = None,
    *,
    head_ref: str = "HEAD",
) -> dict[str, Any]:
    try:
        snapshot = source_snapshot or build_frozen_source_snapshot(head_ref=head_ref)
    except (OSError, subprocess.SubprocessError, TypeError, ValueError):
        return _empty_state()
    if not validate_frozen_source_snapshot(snapshot):
        return _empty_state(
            snapshot if type(snapshot) is FrozenSourceSnapshot else None
        )
    try:
        predecessor = _validate_predecessors(snapshot)
        contract_rows = _contract_rows()
        reason_rows = _reason_rows()
        routing_rows = _routing_rows()
        safety_rows = _safety_rows()
        issue_rows = _issue_rows(predecessor["phase2_issues"].rows)
        _validate_design_rows(
            contract_rows,
            reason_rows,
            routing_rows,
            safety_rows,
            issue_rows,
            predecessor,
        )
    except (
        KeyError,
        TypeError,
        ValueError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        SyntaxError,
    ):
        return _empty_state(snapshot, "PREDECESSOR_OR_DESIGN_VALIDATION_FAILED") | {
            "source_ok": True
        }
    return {
        "source_snapshot": snapshot,
        "source_ok": True,
        "predecessor_ok": True,
        "predecessor": predecessor,
        "contract_rows": contract_rows,
        "reason_rows": reason_rows,
        "routing_rows": routing_rows,
        "safety_rows": safety_rows,
        "issue_rows": issue_rows,
        "all_checks_passed": True,
        "validation_failures": [],
    }


def _csv_bytes(
    columns: Sequence[str], rows: Sequence[Mapping[str, str]]
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
        "source_input_count": 16,
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
        "adapter_contract_row_count": 3,
        "reason_outcome_mapping_row_count": 23,
        "reason_outcome_mapping_pass_count": 23,
        "reason_outcome_mapping_rule_counts": {
            "ADMIT_001": 9,
            "ADMIT_002": 8,
            "ADMIT_003": 6,
        },
        "context_prevalidated_legacy_reasons_excluded_from_adapter_mapping": list(
            ADMIT001_CONTEXT_PREVALIDATED_REASONS
        ),
        "routing_and_projection_row_count": len(state["routing_rows"]),
        "routing_column_count": len(ROUTING_COLUMNS),
        "execution_precedence_explicit_rule_count": 3,
        "execution_precedence_contract": EXECUTION_PRECEDENCE_CONTRACT,
        "context_dispatch_error_reason_count": 16,
        "context_dispatch_error_reasons": {
            f"{rule_id}:{item}": reason
            for (rule_id, item), reason in CONTEXT_ERROR_REASONS.items()
        },
        "adapter_failure_reasons": {
            rule_id: {
                "source_type_failure_reason": spec["source_type_failure_reason"],
                "source_invariant_failure_reason": spec[
                    "source_invariant_failure_reason"
                ],
                "unknown_reason_failure_reason": spec[
                    "unknown_reason_failure_reason"
                ],
            }
            for rule_id, spec in RULE_SPECS.items()
        },
        "semantic_oracle_contract_count": 3,
        "semantic_oracle_contracts": {
            rule_id: {
                "callable": spec["semantic_oracle_callable"],
                "parameters": list(spec["semantic_oracle_parameters"]),
                "source_path": spec["design_path"].as_posix(),
                "expected_legacy_result_projection": spec[
                    "expected_legacy_result_projection"
                ],
                "pure_in_memory": True,
                "uses_original_candidate_and_context_objects": True,
                "legacy_evaluator_is_not_oracle": True,
                "runtime_csv_json_oracle_forbidden": True,
            }
            for rule_id, spec in RULE_SPECS.items()
        },
        "legacy_result_oracle_equivalence_required_count": 3,
        "legacy_result_oracle_equivalence_required": {
            rule_id: True for rule_id in RULE_SPECS
        },
        "semantic_oracle_mismatch_dispatch_code": (
            "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
        ),
        "semantic_oracle_mismatch_failure_reasons": {
            rule_id: spec["source_invariant_failure_reason"]
            for rule_id, spec in RULE_SPECS.items()
        },
        "semantic_oracle_mismatch_partial_result_forbidden": True,
        "semantic_oracle_mismatch_correction_forbidden": True,
        "legacy_value_invariant_contracts": dict(
            LEGACY_VALUE_INVARIANT_CONTRACTS
        ),
        "adapter_side_invalid_payload_row_count": 6,
        "tuple_text_contracts": {
            rule_id: {
                "consumed_candidate_fields": _tuple_text(
                    (spec["candidate_field"],)
                ),
                "consumed_context_items": _tuple_text(
                    (spec["runtime_batch_item"],)
                    if spec["runtime_batch_item"]
                    else ()
                ),
            }
            for rule_id, spec in RULE_SPECS.items()
        },
        "active_issue_count": 12,
        "provider_blocking_issue_id": "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
        "provider_blocking_issue_count": 11,
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "legacy_callable_names": {
            rule_id: spec["callable"] for rule_id, spec in RULE_SPECS.items()
        },
        "legacy_result_key_orders": {
            rule_id: list(spec["keys"]) for rule_id, spec in RULE_SPECS.items()
        },
        "adapter_ids": {
            rule_id: spec["adapter_id"] for rule_id, spec in RULE_SPECS.items()
        },
        "allowed_rule_outcomes": {
            rule_id: list(spec["allowed_outcomes"])
            for rule_id, spec in RULE_SPECS.items()
        },
        "static_policy_dependencies": {
            rule_id: spec["static_policy"] for rule_id, spec in RULE_SPECS.items()
        },
        "runtime_evaluation_context_required": {
            rule_id: None for rule_id in RULE_SPECS
        },
        "consumed_context_items": {
            rule_id: (
                [spec["runtime_batch_item"]] if spec["runtime_batch_item"] else []
            )
            for rule_id, spec in RULE_SPECS.items()
        },
        "unknown_legacy_reason_failure_code": "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
        "phase2_runtime_source_sha256": SOURCE_SHA256[PHASE2_SOURCE_PATH],
        "phase2_runtime_registry_rule_ids": ["ADMIT_004"],
        "readiness": readiness,
        **readiness,
        "all_source_boundary_checks_passed": True,
        "all_predecessor_contract_checks_passed": True,
        "all_legacy_ast_checks_passed": True,
        "all_adapter_contract_checks_passed": True,
        "all_reason_mapping_checks_passed": True,
        "all_routing_projection_checks_passed": True,
        "all_issue_checks_passed": True,
        "all_safety_checks_passed": True,
        "all_checks_passed": True,
        "validation_failures": [],
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }


def _payloads(state: Mapping[str, Any]) -> tuple[dict[str, bytes], dict[str, Any]]:
    csv_payloads = {
        CONTRACT_FILENAME: _csv_bytes(CONTRACT_COLUMNS, state["contract_rows"]),
        REASON_FILENAME: _csv_bytes(REASON_COLUMNS, state["reason_rows"]),
        ROUTING_FILENAME: _csv_bytes(ROUTING_COLUMNS, state["routing_rows"]),
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
        MANIFEST_FILENAME: (
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8"),
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


def run_covapie_bulk_download_admission_admit_001_to_003_legacy_adapter_contract_design_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    state = build_phase3_design_state()
    if state["all_checks_passed"] is not True:
        raise RuntimeError(
            "legacy adapter contract design gate failed closed: "
            + "|".join(state["validation_failures"])
        )
    root = output_root if output_root.is_absolute() else REPO_ROOT / output_root
    _preflight_output_root(root)
    payloads, manifest = _payloads(state)
    for filename in OUTPUT_FILES:
        _atomic_write(root / filename, payloads[filename])
    return {"state": state, "manifest": manifest, "output_root": root}


if __name__ == "__main__":
    materialized = run_covapie_bulk_download_admission_admit_001_to_003_legacy_adapter_contract_design_gate_v1()
    print(json.dumps(materialized["manifest"], indent=2, sort_keys=True))
