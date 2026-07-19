#!/usr/bin/env python3
"""Fail-closed independent checker for ADMIT_009 standalone evaluator v1."""

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
    covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate
    as committed_oracle,
)
from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_009_rule_logic_interface as interface,
)


EXPECTED_BASE_COMMIT = "59dc50acc61b933bf36346a172964adc070a7170"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_009 duplicate identity key contract v1"
CHECKER_PREFIX = "covapie_dup_v1_sha256_"
CHECKER_REGEX = r"^covapie_dup_v1_sha256_[0-9a-f]{64}$"
CHECKER_POLICY = "covapie_duplicate_identity_key_contract_v1"
CHECKER_CANDIDATE_FIELDS = ("duplicate_identity_key",)
CHECKER_CONTEXT_ITEMS = ("duplicate_identity_key_contract", "batch_duplicate_identity_keys")
CHECKER_RESULT_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_duplicate_identity_key", "validated_candidate_fields",
    "consumed_candidate_fields", "consumed_context_items", "evaluator_io_used",
)
CHECKER_SCALAR_REASONS = (
    "DUPLICATE_IDENTITY_KEY_TYPE_INVALID", "DUPLICATE_IDENTITY_KEY_EMPTY",
    "DUPLICATE_IDENTITY_KEY_NON_ASCII", "DUPLICATE_IDENTITY_KEY_SYNTAX_INVALID",
)
CHECKER_POLICY_REASONS = (
    "DUPLICATE_IDENTITY_KEY_CONTRACT_TYPE_INVALID",
    "DUPLICATE_IDENTITY_KEY_CONTRACT_VALUE_INVALID",
)
CHECKER_BATCH_REASONS = (
    "BATCH_DUPLICATE_IDENTITY_KEYS_TYPE_INVALID",
    "BATCH_DUPLICATE_IDENTITY_KEYS_MEMBER_TYPE_INVALID",
    "BATCH_DUPLICATE_IDENTITY_KEYS_MEMBER_INVALID",
    "BATCH_DUPLICATE_IDENTITY_KEYS_ORDER_OR_UNIQUENESS_INVALID",
)
CHECKER_DUPLICATE_REASON = "DUPLICATE_IDENTITY_KEY_ALREADY_PRESENT"
CHECKER_REASON_VOCABULARY = (
    "", *CHECKER_SCALAR_REASONS, *CHECKER_POLICY_REASONS,
    *CHECKER_BATCH_REASONS, CHECKER_DUPLICATE_REASON,
)
CHECKER_GROUPS = {"scalar": 12, "policy": 4, "batch": 12, "outcome_state": 4}

CONTRACT_FILENAME = "covapie_admit_009_rule_logic_interface_contract.csv"
TRUTH_FILENAME = "covapie_admit_009_rule_logic_interface_truth_matrix.csv"
SOURCE_FILENAME = "covapie_admit_009_rule_logic_interface_source_boundary_audit.csv"
SAFETY_FILENAME = "covapie_admit_009_rule_logic_interface_safety_audit.csv"
ISSUE_FILENAME = "covapie_admit_009_rule_logic_interface_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_009_rule_logic_interface_manifest.json"
CSV_OUTPUTS = (CONTRACT_FILENAME, TRUTH_FILENAME, SOURCE_FILENAME, SAFETY_FILENAME, ISSUE_FILENAME)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)
OUTPUT_ROOT = REPO_ROOT / "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_rule_logic_interface_v1"
CONTRACT_COLUMNS = (
    "contract_id", "contract_kind", "contract_subject", "contract_value", "contract_status",
)
TRUTH_COLUMNS = (
    "case_id", "case_group", "key_input_kind", "key_input_display",
    "batch_input_kind", "batch_input_display", "policy_input_kind", "policy_input_display",
    "expected_full_result", "observed_full_result", "committed_design_oracle_full_result",
    "formal_expected_equality", "formal_design_oracle_equality", "case_passed",
)
SOURCE_COLUMNS = (
    "source_order", "source_relative_path", "source_kind", "boundary_necessity",
    "tracked", "base_tree_blob", "filesystem_regular", "non_symlink",
    "expected_sha256", "base_tree_sha256", "filesystem_sha256", "source_boundary_passed",
)
SAFETY_COLUMNS = ("safety_item", "expected_executed", "observed_executed", "safety_passed")
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status",
    "blocking_scope", "blocking_reason", "issue_origin", "integration_transition", "issue_count",
)

EXPECTED_SOURCE_PATHS = (
    "src/covalent_ext/covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate_v1/covapie_admit_009_duplicate_identity_key_contract_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate_v1/covapie_admit_009_duplicate_identity_key_contract.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate_v1/covapie_admit_009_batch_and_policy_context_contract.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate_v1/covapie_admit_009_equivalence_and_provider_boundary_matrix.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate_v1/covapie_admit_009_duplicate_identity_validation_truth_matrix.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate_v1/covapie_admit_009_duplicate_identity_issue_readiness_inventory.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_009_formal_evaluator_preconditions_manifest.json",
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1/covapie_admit_001_to_008_runtime_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1/covapie_admit_001_to_008_runtime_issue_inventory.csv",
    "src/covalent_ext/covapie_bulk_download_admission_admit_008_rule_logic_interface.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1/covapie_unified_admission_result_schema_and_outcome_contract.csv",
)
EXPECTED_SOURCE_SHA256 = dict(zip(EXPECTED_SOURCE_PATHS, (
    "bf20595836e9b178252d37ca72229641a466b97e7510d2ff535e015599110f26",
    "d0d0d19e491f27621214ee887f630a871c1a7cfaf4caca93778599b0162dc48c",
    "484072cd901f7ba5264d207202be493477fb16cc4ddfad4341eabd19d8495a85",
    "38ac90e04316d8efc8794d88d749a3fafc69a0ef66de5cf76cdfd82f6d9a9b57",
    "7b1d09956be5fa76f8b141c10a2a8efb895119271cfd75b9e816c37c88513297",
    "762255cc85a12501ccb592a6f3e82ea100221d33c244403386be743c99c64ac0",
    "2c461d4416742dda734789ba6768995c6d641fb2d1b6c460a0f80ea194482e92",
    "5d1be882bc51c3fad5eefa5dc106dec43ba5842eda0696c06eb04473db33a37b",
    "b5022ee4b6a4e965cf783abf15e70a5909860f4f500c89f983fb41b6b8fd87e2",
    "6047e110c29d8ca7300236f8af8dbce31a92f2a62576cbc2a8fa2d5d1baf32cf",
    "1c11f931b103fe8d523115b00f85d095956042ea1168741b8ec42bbf24a38128",
    "e26985c71dd5e86fbafe8f4cc5bb2051d1de0d59fb01677e58cf65ef2e7d2e01",
    "b09d1bc265cae80296450390c3486a942a9ac16fbd689331770e74024f33bbfa",
), strict=True))
EXPECTED_OUTPUT_SHA256 = {
    CONTRACT_FILENAME: "ea02293b7a43ee22c34c029192bdce4e3356fe9c69688bb66169a939b39eda67",
    TRUTH_FILENAME: "42b2373c398c737d697ffd8177b6971fe2ad9aa9cbfb813d594b9527b0eaa9b3",
    SOURCE_FILENAME: "1aff6a4201da02c24e316b53e0969192a422df49002fc689ddc73d605063541a",
    SAFETY_FILENAME: "81b06fb885d0a527bf5f0612e0a0f340c9bd07903436d7d31b3045f239338f6b",
    ISSUE_FILENAME: "2c461d4416742dda734789ba6768995c6d641fb2d1b6c460a0f80ea194482e92",
    MANIFEST_FILENAME: "b69941408b6f6098e926f7cf3f60cf526811e78a71cb07000c332511b19d5447",
}
BOUNDARY_NECESSITY = (
    "committed design source and independent oracle identity",
    "design manifest counts readiness boundaries and hashes",
    "Exact34 duplicate key contract",
    "Exact15 policy and batch context contract",
    "Exact18 equivalence and provider boundary",
    "ordered committed Exact32 semantic oracle corpus",
    "authoritative Exact11 issue inventory preservation baseline",
    "historical Exact24 formal evaluator precondition boundary",
    "current literal Exact8 runtime with absent ADMIT_009 registration",
    "current Exact8 runtime readiness and registry boundary",
    "current Exact8 runtime issue coverage cross-check",
    "mature ADMIT_008 standalone structural precedent",
    "unified result blocks_candidate and reason invariants",
)


@dataclass(frozen=True)
class CheckerExpectedResult:
    admission_rule_id: str
    outcome: str
    passed: bool
    blocks_candidate: bool
    reason: str
    canonical_duplicate_identity_key: str
    validated_candidate_fields: tuple[tuple[str, str], ...]
    consumed_candidate_fields: tuple[str, ...]
    consumed_context_items: tuple[str, ...]
    evaluator_io_used: bool


class _TruthStringSubclass(str):
    pass


class _TruthTupleSubclass(tuple):
    pass


def _assert(condition: bool, message: str) -> None:
    if condition is not True:
        raise AssertionError(message)


def _bool(value: bool) -> str:
    return "true" if value else "false"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _result_dict(value: object) -> dict[str, Any]:
    return {name: getattr(value, name) for name in CHECKER_RESULT_FIELDS}


def _checker_result(outcome: str, reason: str, canonical: str, contexts: tuple[str, ...]) -> CheckerExpectedResult:
    pair = () if canonical == "" else ((CHECKER_CANDIDATE_FIELDS[0], canonical),)
    return CheckerExpectedResult(
        "ADMIT_009", outcome, outcome == "passed", outcome != "passed", reason,
        canonical, pair, CHECKER_CANDIDATE_FIELDS, contexts, False,
    )


def _checker_expected(key: object, batch: object, policy: object) -> CheckerExpectedResult:
    if type(key) is not str:
        return _checker_result("invalid", CHECKER_SCALAR_REASONS[0], "", ())
    if key == "":
        return _checker_result("invalid", CHECKER_SCALAR_REASONS[1], "", ())
    if not all(ord(character) < 128 for character in key):
        return _checker_result("invalid", CHECKER_SCALAR_REASONS[2], "", ())
    if re.fullmatch(CHECKER_REGEX, key, flags=re.ASCII) is None:
        return _checker_result("invalid", CHECKER_SCALAR_REASONS[3], "", ())
    if type(policy) is not str:
        return _checker_result("invalid", CHECKER_POLICY_REASONS[0], key, CHECKER_CONTEXT_ITEMS[:1])
    if policy != CHECKER_POLICY:
        return _checker_result("invalid", CHECKER_POLICY_REASONS[1], key, CHECKER_CONTEXT_ITEMS[:1])
    if type(batch) is not tuple:
        return _checker_result("invalid", CHECKER_BATCH_REASONS[0], key, CHECKER_CONTEXT_ITEMS)
    if any(type(member) is not str for member in batch):
        return _checker_result("invalid", CHECKER_BATCH_REASONS[1], key, CHECKER_CONTEXT_ITEMS)
    if any(member == "" or not member.isascii() or re.fullmatch(CHECKER_REGEX, member, flags=re.ASCII) is None for member in batch):
        return _checker_result("invalid", CHECKER_BATCH_REASONS[2], key, CHECKER_CONTEXT_ITEMS)
    if any(left >= right for left, right in zip(batch, batch[1:])):
        return _checker_result("invalid", CHECKER_BATCH_REASONS[3], key, CHECKER_CONTEXT_ITEMS)
    if key in batch:
        return _checker_result("blocked", CHECKER_DUPLICATE_REASON, key, CHECKER_CONTEXT_ITEMS)
    return _checker_result("passed", "", key, CHECKER_CONTEXT_ITEMS)


def _oracle_expected(key: object, batch: object, policy: object) -> CheckerExpectedResult:
    observed = committed_oracle.classify_admit_009_duplicate_identity_key_design(key, batch, policy)
    return CheckerExpectedResult(
        "ADMIT_009", observed["outcome"], observed["passed"], observed["blocks_candidate"],
        observed["reason"], observed["canonical_duplicate_identity_key"],
        observed["validated_candidate_fields"], observed["consumed_candidate_fields"],
        observed["consumed_context_items"], observed["evaluator_io_used"],
    )


def _display(value: object) -> str:
    return f"{type(value).__name__}:{value!r}"


def _definitions() -> tuple[tuple[str, str, object, object, object], ...]:
    candidate = CHECKER_PREFIX + "1" * 64
    low = CHECKER_PREFIX + "0" * 64
    high = CHECKER_PREFIX + "2" * 64
    unrelated = CHECKER_PREFIX + "f" * 64
    empty: tuple[str, ...] = ()
    return (
        ("scalar", "scalar_none", None, empty, CHECKER_POLICY),
        ("scalar", "scalar_integer", 7, empty, CHECKER_POLICY),
        ("scalar", "scalar_str_subclass", _TruthStringSubclass(candidate), empty, CHECKER_POLICY),
        ("scalar", "scalar_empty", "", empty, CHECKER_POLICY),
        ("scalar", "scalar_non_ascii", CHECKER_PREFIX + "é" * 64, empty, CHECKER_POLICY),
        ("scalar", "scalar_wrong_prefix", "covapie_dup_v2_sha256_" + "1" * 64, empty, CHECKER_POLICY),
        ("scalar", "scalar_uppercase_digest", CHECKER_PREFIX + "A" * 64, empty, CHECKER_POLICY),
        ("scalar", "scalar_short_digest", CHECKER_PREFIX + "1" * 63, empty, CHECKER_POLICY),
        ("scalar", "scalar_long_digest", CHECKER_PREFIX + "1" * 65, empty, CHECKER_POLICY),
        ("scalar", "scalar_non_hex", CHECKER_PREFIX + "g" * 64, empty, CHECKER_POLICY),
        ("scalar", "scalar_whitespace", " " + candidate, empty, CHECKER_POLICY),
        ("scalar", "scalar_canonical", candidate, empty, CHECKER_POLICY),
        ("policy", "policy_none", candidate, empty, None),
        ("policy", "policy_str_subclass", candidate, empty, _TruthStringSubclass(CHECKER_POLICY)),
        ("policy", "policy_wrong_value", candidate, empty, "covapie_duplicate_identity_key_contract_v2"),
        ("policy", "policy_exact_valid", candidate, empty, CHECKER_POLICY),
        ("batch", "batch_none", candidate, None, CHECKER_POLICY),
        ("batch", "batch_list", candidate, [], CHECKER_POLICY),
        ("batch", "batch_tuple_subclass", candidate, _TruthTupleSubclass(), CHECKER_POLICY),
        ("batch", "batch_non_str_member", candidate, (7,), CHECKER_POLICY),
        ("batch", "batch_str_subclass_member", candidate, (_TruthStringSubclass(unrelated),), CHECKER_POLICY),
        ("batch", "batch_malformed_member", candidate, ("bad",), CHECKER_POLICY),
        ("batch", "batch_unsorted", candidate, (high, low), CHECKER_POLICY),
        ("batch", "batch_duplicate_members", candidate, (unrelated, unrelated), CHECKER_POLICY),
        ("batch", "batch_empty_valid", candidate, (), CHECKER_POLICY),
        ("batch", "batch_one_unrelated", candidate, (unrelated,), CHECKER_POLICY),
        ("batch", "batch_one_matching", candidate, (candidate,), CHECKER_POLICY),
        ("batch", "batch_multiple_contains", candidate, (low, candidate, high), CHECKER_POLICY),
        ("outcome_state", "canonical_unique_passed", candidate, (unrelated,), CHECKER_POLICY),
        ("outcome_state", "canonical_duplicate_blocked", candidate, (candidate,), CHECKER_POLICY),
        ("outcome_state", "policy_invalid_retains_pair", candidate, (), "wrong"),
        ("outcome_state", "batch_invalid_retains_pair", candidate, [candidate], CHECKER_POLICY),
    )


def _expected_truth_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for group, case_id, key, batch, policy in _definitions():
        expected = _checker_expected(key, batch, policy)
        design = _oracle_expected(key, batch, policy)
        observed = interface.evaluate_admit_009(key, batch, policy)
        expected_dict = _result_dict(expected)
        design_dict = _result_dict(design)
        observed_dict = _result_dict(observed)
        _assert(expected_dict == design_dict == observed_dict, f"three-way Exact10 mismatch {case_id}")
        full = json.dumps(expected_dict, separators=(",", ":"))
        rows.append({
            "case_id": case_id, "case_group": group,
            "key_input_kind": type(key).__name__, "key_input_display": _display(key),
            "batch_input_kind": type(batch).__name__, "batch_input_display": _display(batch),
            "policy_input_kind": type(policy).__name__, "policy_input_display": _display(policy),
            "expected_full_result": full, "observed_full_result": full,
            "committed_design_oracle_full_result": full,
            "formal_expected_equality": "true", "formal_design_oracle_equality": "true",
            "case_passed": "true",
        })
    return rows


def _expected_contract_rows() -> list[dict[str, str]]:
    values = (
        ("API_001", "public_api", "signature", "evaluate_admit_009(duplicate_identity_key, batch_duplicate_identity_keys, duplicate_identity_key_contract)"),
        ("API_002", "public_api", "inputs", "three_required_positional_or_keyword_direct_objects"),
        ("API_003", "public_api", "execution", "pure_in_memory_deterministic_no_input_mutation"),
        ("RESULT_001", "result_contract", "type", "exact_frozen_dataclass_no_subclasses"),
        ("RESULT_002", "result_contract", "field_count", "10"),
        ("RESULT_003", "result_contract", "field_order", "|".join(CHECKER_RESULT_FIELDS)),
        ("RESULT_004", "result_contract", "exact_types", "exact_str_bool_tuple_and_string_pairs"),
        ("RESULT_005", "result_contract", "outcomes", "passed|blocked|invalid"),
        ("RESULT_006", "result_contract", "passed", "true_iff_outcome_passed"),
        ("RESULT_007", "result_contract", "blocks_candidate", "true_iff_outcome_not_passed"),
        ("RESULT_008", "result_contract", "reason", "passed_empty_nonpassed_frozen_reason"),
        ("RESULT_009", "result_contract", "scalar_invalid", "empty_canonical_empty_validated_empty_context"),
        ("RESULT_010", "result_contract", "policy_invalid", "canonical_pair_policy_context"),
        ("RESULT_011", "result_contract", "batch_invalid", "canonical_pair_full_context"),
        ("RESULT_012", "result_contract", "passed_blocked", "canonical_pair_full_context"),
        ("RESULT_013", "result_contract", "consumed_candidate", "duplicate_identity_key"),
        ("RESULT_014", "result_contract", "evaluator_io_used", "exact_false"),
        ("KEY_001", "scalar_semantics", "type", "exact_builtin_str"),
        ("KEY_002", "scalar_semantics", "regex", CHECKER_REGEX),
        ("KEY_003", "scalar_semantics", "precedence", "type|nonempty|ascii|regex_fullmatch"),
        ("KEY_004", "scalar_semantics", "canonical", "input_exactly_unchanged"),
        ("KEY_005", "scalar_semantics", "normalization", "none"),
        ("KEY_006", "scalar_semantics", "composition", "opaque_producer_owned_zero_visible_components"),
        ("POLICY_001", "policy_semantics", "type", "exact_builtin_str"),
        ("POLICY_002", "policy_semantics", "value", CHECKER_POLICY),
        ("POLICY_003", "policy_semantics", "normalization", "none"),
        ("BATCH_001", "batch_semantics", "type", "exact_builtin_tuple_empty_allowed"),
        ("BATCH_002", "batch_semantics", "members", "exact_builtin_str_full_scalar_valid"),
        ("BATCH_003", "batch_semantics", "order", "strict_original_string_ascending"),
        ("BATCH_004", "batch_semantics", "uniqueness", "required"),
        ("BATCH_005", "batch_semantics", "repair", "no_sort_no_deduplicate_no_normalization"),
        ("BATCH_006", "batch_semantics", "snapshot", "earlier_candidates_current_record_excluded_by_caller"),
        ("PRECEDENCE_001", "rule_semantics", "validation", "scalar|policy|batch|exact_membership"),
        ("PRECEDENCE_002", "rule_semantics", "short_circuit_context", "none|policy_only|policy_and_batch"),
        ("MEMBERSHIP_001", "rule_semantics", "comparison", "exact_case_sensitive_python_string_equality"),
        ("MEMBERSHIP_002", "rule_semantics", "unique", "passed_empty_reason"),
        ("MEMBERSHIP_003", "rule_semantics", "duplicate", CHECKER_DUPLICATE_REASON),
        ("REASON_001", "rule_semantics", "historical_lowercase", "duplicate_identity_unresolved_not_used"),
        ("ORACLE_001", "oracle_contract", "production", "does_not_import_or_call_design_oracle"),
        ("ORACLE_002", "oracle_contract", "attestation", "checker_compares_all_exact10_fields"),
        ("ORACLE_003", "oracle_contract", "truth", "committed_exact32_full_equivalence"),
        ("PROVIDER_001", "provider_boundary", "mapping", "unvalidated_zero_real_keys"),
        ("PROVIDER_002", "provider_boundary", "fields", "candidate_group_leakage_fields_not_parsed"),
        ("BOUNDARY_001", "authorization_boundary", "runtime", "no_adapter_no_registration_no_exact9"),
        ("BOUNDARY_002", "authorization_boundary", "later_rules", "no_admit010_no_all_rules_no_combined_verdict"),
        ("BOUNDARY_003", "authorization_boundary", "operations", "no_raw_network_download_checkpoint_model_training"),
    )
    return [{"contract_id": i, "contract_kind": k, "contract_subject": s, "contract_value": v, "contract_status": "frozen"} for i, k, s, v in values]


EXECUTED = (
    "formal_evaluator_implementation", "exact10_result_class", "exact32_equivalence",
    "result_invariant_enforcement", "pure_call_graph_validation", "deterministic_materialization",
    "source_verification", "issue_byte_preservation",
)
NOT_EXECUTED = (
    "provider_key_generation", "provider_mapping", "real_candidate_evaluation", "adapter_design",
    "adapter_implementation", "admit_009_registration", "exact9_runtime", "admit_010",
    "evaluate_all_rules", "combined_candidate_verdict", "raw_read", "network", "bulk_download",
    "checkpoint", "torch_numpy_rdkit", "model_forward_loss", "training_fine_tune",
    "parameter_update", "stage", "commit", "push", "gh",
)
TRUE_READINESS = (
    "admit_009_standalone_evaluator_implemented", "admit_009_exact10_result_contract_frozen",
    "admit_009_result_class_exact_type_enforced", "admit_009_result_cross_field_invariants_enforced",
    "admit_009_blocks_candidate_invariant_enforced", "admit_009_scalar_contract_runtime_enforced",
    "admit_009_policy_contract_runtime_enforced", "admit_009_batch_contract_runtime_enforced",
    "admit_009_validation_precedence_runtime_enforced", "admit_009_membership_runtime_enforced",
    "admit_009_formal_exact32_equivalence_enforced", "admit_009_formal_evaluator_pure_in_memory",
    "admit_009_design_oracle_independence_preserved", "admit_009_provider_mapping_boundary_preserved",
    "ready_for_admit_009_unified_adapter_contract_design", "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "real_provider_duplicate_identity_mapping_validated", "real_provider_duplicate_identity_key_count_nonzero",
    "admit_009_unified_adapter_contract_frozen", "admit_009_unified_adapter_implemented",
    "admit_009_registered_in_engine", "unified_dispatch_runtime_with_admit_001_to_009_implemented",
    "admit_010_standalone_evaluator_implemented", "admit_010_to_015_registered_in_engine",
    "all_15_rules_covered", "evaluate_all_rules_implemented", "combined_candidate_verdict_contract_frozen",
    "combined_candidate_verdict_implemented", "cross_rule_precedence_frozen", "real_candidate_evaluation",
    "ready_for_bulk_download_now", "ready_for_training", "ready_to_train_now",
)
CHECKER_READINESS = {**{key: True for key in TRUE_READINESS}, **{key: False for key in FALSE_READINESS}}


def _expected_safety_rows() -> list[dict[str, str]]:
    return [{
        "safety_item": item, "expected_executed": _bool(executed),
        "observed_executed": _bool(executed), "safety_passed": "true",
    } for item, executed in (*((item, True) for item in EXECUTED), *((item, False) for item in NOT_EXECUTED))]


def _expected_source_rows() -> list[dict[str, str]]:
    return [{
        "source_order": str(index), "source_relative_path": path,
        "source_kind": Path(path).suffix.lstrip("."), "boundary_necessity": BOUNDARY_NECESSITY[index - 1],
        "tracked": "true", "base_tree_blob": "true", "filesystem_regular": "true", "non_symlink": "true",
        "expected_sha256": EXPECTED_SOURCE_SHA256[path], "base_tree_sha256": EXPECTED_SOURCE_SHA256[path],
        "filesystem_sha256": EXPECTED_SOURCE_SHA256[path], "source_boundary_passed": "true",
    } for index, path in enumerate(EXPECTED_SOURCE_PATHS, 1)]


def _csv(path: Path, header: tuple[str, ...]) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"), newline=""))
    _assert(tuple(reader.fieldnames or ()) == header, f"CSV header {path.name}")
    rows = [dict(row) for row in reader]
    _assert(all(tuple(row) == header and all(value is not None for value in row.values()) for row in rows), f"CSV rows {path.name}")
    return rows


def _read_verified_sources() -> dict[str, bytes]:
    _assert(len(EXPECTED_SOURCE_PATHS) == len(set(EXPECTED_SOURCE_PATHS)) == 13, "Exact13 paths")
    subject = subprocess.run(["git", "show", "-s", "--format=%s", EXPECTED_BASE_COMMIT], cwd=REPO_ROOT, text=True, capture_output=True)
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, "HEAD"], cwd=REPO_ROOT)
    _assert(subject.returncode == 0 and subject.stdout.strip() == EXPECTED_BASE_SUBJECT and ancestor.returncode == 0, "base lineage")
    for path in EXPECTED_SOURCE_PATHS:
        relative = Path(path)
        _assert(not relative.is_absolute() and ".." not in relative.parts and relative.parts[0] != "checkpoints" and relative.parts[:2] != ("data", "raw"), f"safe source {path}")
        metadata = os.lstat(REPO_ROOT / relative)
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", "--", path], cwd=REPO_ROOT, capture_output=True)
        tree = subprocess.run(["git", "ls-tree", EXPECTED_BASE_COMMIT, "--", path], cwd=REPO_ROOT, text=True, capture_output=True)
        values = tree.stdout.split("\t", 1)[0].split()
        _assert(tracked.returncode == tree.returncode == 0 and len(values) == 3 and values[0] in ("100644", "100755") and values[1] == "blob", f"source structure {path}")
        _assert(stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode), f"source regular {path}")
    sources: dict[str, bytes] = {}
    for path in EXPECTED_SOURCE_PATHS:
        base = subprocess.run(["git", "show", f"{EXPECTED_BASE_COMMIT}:{path}"], cwd=REPO_ROOT, capture_output=True)
        filesystem = (REPO_ROOT / path).read_bytes()
        digest = EXPECTED_SOURCE_SHA256[path]
        _assert(base.returncode == 0 and hashlib.sha256(base.stdout).hexdigest() == hashlib.sha256(filesystem).hexdigest() == digest, f"source SHA {path}")
        sources[path] = filesystem
    return sources


def _expected_manifest(output_sha: dict[str, str]) -> dict[str, Any]:
    readiness = dict(CHECKER_READINESS)
    verification = [{
        "source_order": index, "source_relative_path": path, "tracked": True,
        "base_tree_blob": True, "filesystem_regular": True, "non_symlink": True,
        "expected_sha256": EXPECTED_SOURCE_SHA256[path], "base_tree_sha256": EXPECTED_SOURCE_SHA256[path],
        "filesystem_sha256": EXPECTED_SOURCE_SHA256[path], "source_verified": True,
    } for index, path in enumerate(EXPECTED_SOURCE_PATHS, 1)]
    return {
        "project": "CovaPIE", "step": "ADMIT_009 standalone evaluator interface v1",
        "stage": "covapie_bulk_download_admission_admit_009_rule_logic_interface_v1",
        "manifest_schema_version": "covapie_admit_009_rule_logic_interface_manifest_v1",
        "expected_base_commit": EXPECTED_BASE_COMMIT, "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "admission_rule_id": "ADMIT_009", "admission_rule_name": "duplicate_identity_precheck",
        "candidate_fields": list(CHECKER_CANDIDATE_FIELDS), "context_items": list(CHECKER_CONTEXT_ITEMS),
        "public_api": "evaluate_admit_009(duplicate_identity_key, batch_duplicate_identity_keys, duplicate_identity_key_contract)",
        "public_signature_parameters": ["duplicate_identity_key", "batch_duplicate_identity_keys", "duplicate_identity_key_contract"],
        "public_signature_required_positional_or_keyword": True,
        "result_type": "Admit009EvaluationResult", "result_field_count": 10,
        "result_fields": list(CHECKER_RESULT_FIELDS), "outcome_vocabulary": ["passed", "blocked", "invalid"],
        "reason_vocabulary": list(CHECKER_REASON_VOCABULARY), "key_prefix": CHECKER_PREFIX,
        "key_regex": CHECKER_REGEX, "key_canonical_equals_input": True, "normalization_applied": False,
        "policy_contract_value": CHECKER_POLICY, "batch_exact_type": "builtins.tuple",
        "batch_empty_allowed": True, "batch_member_exact_type": "builtins.str",
        "batch_strict_ascending_unique": True, "batch_automatic_sort_or_deduplicate": False,
        "validation_precedence": ["scalar", "policy", "batch", "exact_membership"],
        "scalar_validation_reasons": list(CHECKER_SCALAR_REASONS),
        "policy_validation_reasons": list(CHECKER_POLICY_REASONS),
        "batch_validation_reasons": list(CHECKER_BATCH_REASONS),
        "duplicate_blocked_reason": CHECKER_DUPLICATE_REASON,
        "membership_semantics": "exact case-sensitive Python string equality",
        "blocks_candidate_invariant": "true_iff_outcome_not_passed",
        "scalar_invalid_consumed_context_items": [],
        "policy_invalid_consumed_context_items": list(CHECKER_CONTEXT_ITEMS[:1]),
        "batch_invalid_consumed_context_items": list(CHECKER_CONTEXT_ITEMS),
        "passed_blocked_consumed_context_items": list(CHECKER_CONTEXT_ITEMS),
        "independent_semantic_oracle": "classify_admit_009_duplicate_identity_key_design",
        "independent_semantic_oracle_attested": True, "production_oracle_import_or_call": False,
        "evaluator_call_graph": ["evaluate_admit_009", "_validate_scalar", "_validate_policy", "_validate_batch", "_result"],
        "evaluator_call_graph_pure_in_memory": True,
        "truth_matrix_contract": "Exact32", "truth_matrix_row_count": 32, "truth_matrix_pass_count": 32,
        "truth_matrix_group_counts": dict(CHECKER_GROUPS), "contract_row_count": 46, "contract_pass_count": 46,
        "source_boundary_name": "fixed_ordered_exact13_committed_source_boundary",
        "source_input_count": 13, "source_input_paths": list(EXPECTED_SOURCE_PATHS),
        "source_input_sha256": dict(EXPECTED_SOURCE_SHA256), "source_input_verification": verification,
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "source_audit_row_count": 13, "source_audit_pass_count": 13,
        "issue_inventory_row_count": 11, "issue_inventory_preserved_exactly": True,
        "issue_inventory_sha256": EXPECTED_SOURCE_SHA256[EXPECTED_SOURCE_PATHS[6]],
        "coverage_issue_status": "open", "coverage_issue_affected_rules": "ADMIT_009–ADMIT_015",
        "coverage_issue_transition": "admit_008_implemented_and_removed_from_open_coverage_scope",
        "real_provider_duplicate_identity_key_count": 0,
        "real_provider_duplicate_identity_mapping_validated": False, "provider_fields_consumed": [],
        "safety_row_count": 30, "safety_pass_count": 30,
        "output_files": list(OUTPUT_FILES), "output_file_count": 6,
        "output_sha256": output_sha, "output_sha256_excludes_manifest_self_hash": True,
        "readiness": readiness, **readiness,
        "all_source_boundary_checks_passed": True, "all_predecessor_contract_checks_passed": True,
        "all_result_contract_checks_passed": True, "all_semantic_checks_passed": True,
        "all_truth_matrix_checks_passed": True, "all_issue_checks_passed": True,
        "all_safety_checks_passed": True, "all_checks_passed": True,
        "stop_boundaries": [
            "no_provider_key_generation", "no_provider_mapping", "no_unified_adapter_design_or_implementation",
            "no_admit_009_registration", "no_exact8_runtime_modification", "no_exact9_runtime",
            "no_admit_010", "no_evaluate_all_rules", "no_combined_candidate_verdict",
            "no_real_candidate_evaluation", "no_raw_network_download_checkpoint_model_training",
        ],
        "recommended_next_step": "design_covapie_admit_009_unified_adapter_contract_v1",
        "validation_failures": [],
    }


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
    path = REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_009_rule_logic_interface.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    pending = ["evaluate_admit_009"]
    closure: set[str] = set()
    banned = {
        "classify_admit_009_duplicate_identity_key_design", "build_interface_state",
        "build_frozen_source_snapshot", "read_bytes", "read_text", "open", "run",
        "write", "getenv", "provider", "system", "Popen",
    }
    while pending:
        name = pending.pop()
        if name in closure:
            continue
        closure.add(name)
        calls = _called_names(functions[name])
        _assert(not calls.intersection(banned), f"banned evaluator call {calls.intersection(banned)}")
        pending.extend(call for call in calls if call in functions)
    _assert(closure == {"evaluate_admit_009", "_validate_scalar", "_validate_policy", "_validate_batch", "_result"}, "evaluator closure")
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            _assert("duplicate_identity_key_contract_design_gate" not in (node.module or ""), "production oracle import")
        elif isinstance(node, ast.Import):
            _assert(all("duplicate_identity_key_contract_design_gate" not in alias.name for alias in node.names), "production oracle import")


def _check_public_contract() -> None:
    signature = inspect.signature(interface.evaluate_admit_009)
    parameters = tuple(signature.parameters.values())
    _assert(tuple(parameter.name for parameter in parameters) == ("duplicate_identity_key", "batch_duplicate_identity_keys", "duplicate_identity_key_contract"), "signature names")
    _assert(all(parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD and parameter.default is inspect.Parameter.empty for parameter in parameters), "signature kinds")
    _assert(signature.return_annotation == "Admit009EvaluationResult", "return annotation")
    _assert(tuple(field.name for field in fields(interface.Admit009EvaluationResult)) == CHECKER_RESULT_FIELDS, "Exact10 fields")
    candidate = CHECKER_PREFIX + "1" * 64
    result = interface.evaluate_admit_009(candidate, (), CHECKER_POLICY)
    _assert(type(result) is interface.Admit009EvaluationResult and tuple(vars(result)) == CHECKER_RESULT_FIELDS, "exact result/storage")
    _assert(interface.REASON_VOCABULARY == CHECKER_REASON_VOCABULARY, "reason vocabulary")
    original_policy = interface._validate_policy
    interface._validate_policy = lambda _: (_ for _ in ()).throw(AssertionError("policy reached"))
    try:
        observed = interface.evaluate_admit_009(None, object(), object())
    finally:
        interface._validate_policy = original_policy
    _assert(observed.reason == CHECKER_SCALAR_REASONS[0] and observed.consumed_context_items == (), "scalar short circuit")


def _validate_output_tree(root: Path, *, enforce_frozen_hashes: bool = True) -> dict[str, Any]:
    _assert(root.is_dir() and not root.is_symlink(), "output root")
    entries = tuple(root.iterdir())
    _assert({entry.name for entry in entries} == set(OUTPUT_FILES), "output set")
    _assert(all(entry.is_file() and not entry.is_symlink() for entry in entries), "output entries")
    sources = _read_verified_sources()
    contracts = _csv(root / CONTRACT_FILENAME, CONTRACT_COLUMNS)
    truth = _csv(root / TRUTH_FILENAME, TRUTH_COLUMNS)
    source_rows = _csv(root / SOURCE_FILENAME, SOURCE_COLUMNS)
    safety = _csv(root / SAFETY_FILENAME, SAFETY_COLUMNS)
    issues = _csv(root / ISSUE_FILENAME, ISSUE_COLUMNS)
    _assert(contracts == _expected_contract_rows(), "contract semantics")
    _assert(truth == _expected_truth_rows(), "truth semantics")
    _assert(source_rows == _expected_source_rows(), "source semantics")
    _assert(safety == _expected_safety_rows(), "safety semantics")
    _assert((root / ISSUE_FILENAME).read_bytes() == sources[EXPECTED_SOURCE_PATHS[6]], "issue bytes")
    _assert(len(issues) == 11, "issue count")
    issue_map = {row["issue_id"]: row for row in issues}
    _assert(issue_map["DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED"]["status"] == "resolved", "semantics issue")
    _assert(issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"].startswith("ADMIT_009|"), "coverage")
    output_sha = {name: _sha(root / name) for name in CSV_OUTPUTS}
    manifest = json.loads((root / MANIFEST_FILENAME).read_text(encoding="utf-8"))
    expected_manifest = _expected_manifest(output_sha)
    _assert(type(manifest) is dict and set(manifest) == set(expected_manifest), "exact manifest keys")
    _assert(manifest == expected_manifest, "full manifest equality")
    _assert(all(manifest[key] is manifest["readiness"][key] for key in (*TRUE_READINESS, *FALSE_READINESS)), "readiness mirrors")
    if enforce_frozen_hashes:
        _assert({name: _sha(root / name) for name in OUTPUT_FILES} == EXPECTED_OUTPUT_SHA256, "frozen output SHA")
    return manifest


def _negative_checks(root: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="covapie-admit009-checker-") as temporary:
        base = Path(temporary)
        for mutation in ("missing", "extra", "symlink", "truth_rehash", "issue_rehash", "provider", "readiness", "unknown"):
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
                changed = (
                    original.replace("passed", "tampered", 1)
                    if mutation == "truth_rehash"
                    else original.replace("ADMIT_009|ADMIT_010", "ADMIT_010", 1)
                )
                path.write_text(changed, encoding="utf-8")
                manifest_path = victim / MANIFEST_FILENAME
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["output_sha256"][name] = _sha(path)
                manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            else:
                path = victim / MANIFEST_FILENAME
                manifest = json.loads(path.read_text(encoding="utf-8"))
                if mutation == "provider":
                    manifest["real_provider_duplicate_identity_key_count"] = 1
                    manifest["real_provider_duplicate_identity_mapping_validated"] = True
                    manifest["readiness"]["real_provider_duplicate_identity_mapping_validated"] = True
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
        "import covalent_ext.covapie_bulk_download_admission_admit_009_rule_logic_interface",
        "import importlib.util,sys; p='scripts/check_covapie_bulk_download_admission_admit_009_rule_logic_interface_v1.py'; s=importlib.util.spec_from_file_location('admit009_checker',p); m=importlib.util.module_from_spec(s); sys.modules[s.name]=m; s.loader.exec_module(m)",
    )
    for command in commands:
        result = subprocess.run([sys.executable, "-c", command], cwd=REPO_ROOT, env=environment, text=True, capture_output=True)
        _assert(result.returncode == 0 and result.stdout == result.stderr == "", "silent import")


def main() -> int:
    _check_public_contract()
    _assert(len(_definitions()) == 32, "Exact32")
    _assert({group: sum(row[0] == group for row in _definitions()) for group in CHECKER_GROUPS} == CHECKER_GROUPS, "Exact32 groups")
    _expected_truth_rows()
    _check_call_graph()
    first = interface.run_covapie_bulk_download_admission_admit_009_rule_logic_interface_v1(OUTPUT_ROOT)
    first_bytes = {name: (OUTPUT_ROOT / name).read_bytes() for name in OUTPUT_FILES}
    second = interface.run_covapie_bulk_download_admission_admit_009_rule_logic_interface_v1(OUTPUT_ROOT)
    second_bytes = {name: (OUTPUT_ROOT / name).read_bytes() for name in OUTPUT_FILES}
    _assert(first["manifest"] == second["manifest"] and first_bytes == second_bytes, "double materialization")
    manifest = _validate_output_tree(OUTPUT_ROOT)
    _negative_checks(OUTPUT_ROOT)
    _silent_imports()
    print("admit_009_truth_matrix=32/32")
    print("admit_009_truth_groups=scalar:12,policy:4,batch:12,outcome_state:4")
    print("admit_009_contract=46/46")
    print("source_boundary=13/13")
    print("safety_audit=30/30")
    print("exact11_issue_inventory=11/11")
    print(f"manifest_key_count={len(manifest)}")
    print(f"readiness_count={len(manifest['readiness'])}")
    print("real_provider_duplicate_identity_key_count=0")
    print("real_provider_duplicate_identity_mapping_validated=false")
    for name in OUTPUT_FILES:
        print(f"sha256 {name} {_sha(OUTPUT_ROOT / name)}")
    print("ADMIT_009_STANDALONE_EVALUATOR_INTERFACE_CHECK=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
