#!/usr/bin/env python3
"""Independent checker for the ADMIT_009 unified-adapter design gate."""

from __future__ import annotations

import ast
import csv
import hashlib
import importlib
import io
import json
import stat
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import fields
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
MODULE = "covalent_ext.covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate"
OUTPUT_ROOT = ROOT / "data/derived/covalent_small/covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate_v1"
BASE = "0c80b0b8ac4e5f874a99c9f8da03f530ad7cc09e"
SUBJECT = "add CovaPIE standalone ADMIT_009 rule logic interface v1"
RULE_ID = "ADMIT_009"
RULE_NAME = "duplicate_identity_precheck"
ADAPTER_ID = "covapie_admit_009_unified_adapter_v1"
SCHEMA = "covapie_unified_admission_rule_evaluation_v1"
NEXT_STEP = "implement_covapie_unified_dispatch_runtime_with_admit_001_to_009_v1"
CURRENT_ORDER = tuple(f"ADMIT_{index:03d}" for index in range(1, 9))
FUTURE_ORDER = (*CURRENT_ORDER, RULE_ID)
KNOWN_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
CANDIDATE_FIELDS = ("duplicate_identity_key",)
CONTEXT_ITEMS = ("duplicate_identity_key_contract", "batch_duplicate_identity_keys")
RESULT_FIELDS = (
    "schema_version", "admission_rule_id", "admission_rule_name", "outcome",
    "passed", "blocks_candidate", "reason", "normalized_values",
    "validated_candidate_fields", "consumed_candidate_fields",
    "consumed_context_items", "evaluator_io_used", "adapter_id",
)
SOURCE_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_duplicate_identity_key", "validated_candidate_fields",
    "consumed_candidate_fields", "consumed_context_items", "evaluator_io_used",
)
ERROR_FIELDS = (
    "code", "admission_rule_id", "known_rule", "callable_discovered",
    "adapter_ready", "reason",
)
ERROR_CODES = (
    "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN",
    "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
    "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
)
OUTCOMES = ("passed", "blocked", "invalid", "rejected")
ROUTING_ORDER = (
    "batch_context_mapping_validation",
    "batch_duplicate_identity_keys_required_key_lookup",
    "evaluation_context_mapping_validation",
    "duplicate_identity_key_contract_required_key_lookup",
    "download_result_context_must_be_none",
    "stage_authorization_context_must_be_none",
    "candidate_record_mapping_validation",
    "duplicate_identity_key_required_key_lookup",
    "formal_evaluator", "source_validation", "independent_oracle",
    "full_exact10_equality", "exact13_projection",
)
CONTEXT_REASONS = {
    "batch_context": "ADMIT_009_BATCH_CONTEXT_MAPPING_REQUIRED",
    "batch_context_key": "ADMIT_009_BATCH_DUPLICATE_IDENTITY_KEYS_REQUIRED",
    "evaluation_context": "ADMIT_009_EVALUATION_CONTEXT_MAPPING_REQUIRED",
    "evaluation_context_key": "ADMIT_009_DUPLICATE_IDENTITY_KEY_CONTRACT_REQUIRED",
    "download_result_context": "ADMIT_009_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
    "stage_authorization_context": "ADMIT_009_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
}
CANDIDATE_REASON = "ADMIT_009_CANDIDATE_RECORD_MAPPING_INVALID"
MISSING_REASON = "duplicate_identity_key_missing"
SOURCE_TYPE_REASON = "ADMIT_009_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
SOURCE_INVARIANT_REASON = "ADMIT_009_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"

OUTPUTS = (
    "covapie_admit_009_unified_adapter_contract.csv",
    "covapie_admit_009_candidate_projection_and_context_routing_matrix.csv",
    "covapie_admit_009_unified_result_projection_truth_matrix.csv",
    "covapie_admit_009_unified_adapter_safety_audit.csv",
    "covapie_admit_009_unified_adapter_issue_readiness_inventory.csv",
    "covapie_admit_009_unified_adapter_contract_manifest.json",
)
FROZEN_OUTPUT_SHA256 = {
    OUTPUTS[0]: "1b490f4b3263292e5d42a58ef53caf53e6b2e836d27d9966fc8250ccffb2f7b3",
    OUTPUTS[1]: "b91a358411f1ac4600868c6f6ef4e2d02e4348edd22cb25cb7b8822de9c9a5e6",
    OUTPUTS[2]: "f98d5c0ab1a41e02a6a389757e447b85469887e718cd8a9a07ac4d84d84892bd",
    OUTPUTS[3]: "95da584f09e6cb18b000623e593b114a88cfb57603bcabf729a1d2c7b3cef002",
    OUTPUTS[4]: "2c461d4416742dda734789ba6768995c6d641fb2d1b6c460a0f80ea194482e92",
    OUTPUTS[5]: "efe1da7f804a411028903a3a6fc498eb2f0cc5f2b0823b81b5aab3acd83d53c1",
}
SOURCE_BOUNDARY = (
    ("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008.py", "b5022ee4b6a4e965cf783abf15e70a5909860f4f500c89f983fb41b6b8fd87e2"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1/covapie_admit_001_to_008_runtime_manifest.json", "6047e110c29d8ca7300236f8af8dbce31a92f2a62576cbc2a8fa2d5d1baf32cf"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008_v1/covapie_admit_001_to_008_runtime_issue_inventory.csv", "1c11f931b103fe8d523115b00f85d095956042ea1168741b8ec42bbf24a38128"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_009_rule_logic_interface.py", "3649971eec020c5981a3ba8bfddeb604797f8557fb6036efd6094a2b0d6ab4e4"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_009_rule_logic_interface_v1/covapie_admit_009_rule_logic_interface_manifest.json", "b69941408b6f6098e926f7cf3f60cf526811e78a71cb07000c332511b19d5447"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_009_rule_logic_interface_v1/covapie_admit_009_rule_logic_interface_contract.csv", "ea02293b7a43ee22c34c029192bdce4e3356fe9c69688bb66169a939b39eda67"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_009_rule_logic_interface_v1/covapie_admit_009_rule_logic_interface_truth_matrix.csv", "42b2373c398c737d697ffd8177b6971fe2ad9aa9cbfb813d594b9527b0eaa9b3"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_009_rule_logic_interface_v1/covapie_admit_009_rule_logic_interface_issue_readiness_inventory.csv", "2c461d4416742dda734789ba6768995c6d641fb2d1b6c460a0f80ea194482e92"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate.py", "bf20595836e9b178252d37ca72229641a466b97e7510d2ff535e015599110f26"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate_v1/covapie_admit_009_duplicate_identity_key_contract_manifest.json", "d0d0d19e491f27621214ee887f630a871c1a7cfaf4caca93778599b0162dc48c"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate_v1/covapie_admit_009_duplicate_identity_key_contract.csv", "484072cd901f7ba5264d207202be493477fb16cc4ddfad4341eabd19d8495a85"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate_v1/covapie_admit_009_batch_and_policy_context_contract.csv", "38ac90e04316d8efc8794d88d749a3fafc69a0ef66de5cf76cdfd82f6d9a9b57"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate_v1/covapie_admit_009_equivalence_and_provider_boundary_matrix.csv", "7b1d09956be5fa76f8b141c10a2a8efb895119271cfd75b9e816c37c88513297"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate_v1/covapie_admit_009_duplicate_identity_validation_truth_matrix.csv", "762255cc85a12501ccb592a6f3e82ea100221d33c244403386be743c99c64ac0"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate.py", "930a8791bd129a06b272163766a5431aeaf1a3e79003b22df77d6af16319fecb"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_008_unified_adapter_contract_design_gate_v1/covapie_admit_008_unified_adapter_contract_manifest.json", "d7423c337512dff3f66a68209301c91dd3fee2bdd2a3a5b669185854c622d922"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1/covapie_unified_admission_result_schema_and_outcome_contract.csv", "b09d1bc265cae80296450390c3486a942a9ac16fbd689331770e74024f33bbfa"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_rule_engine_contract_design_gate_v1/covapie_unified_admission_evaluator_and_context_routing_matrix.csv", "2d09f6ab5aa9c64419e7e7c4a90f6562a2883007f9b3ef82258a69b9df181b05"),
)
CONTRACT_COLUMNS = ("contract_order", "contract_id", "contract_group", "contract_subject", "contract_value", "contract_status")
ROUTING_COLUMNS = ("matrix_order", "matrix_group", "case_id", "condition", "expected_behavior", "expected_reason", "expected_result_json", "formal_call_count", "oracle_call_count", "candidate_access_status", "case_passed")
TRUTH_COLUMNS = ("case_id", "case_group", "behavior", "expected_dispatch_code", "expected_reason", "source_exact10_json", "oracle_exact10_json", "unified_exact13_json", "formal_call_count", "oracle_call_count", "case_passed")
SAFETY_COLUMNS = ("safety_item", "expected_executed", "observed_executed", "safety_passed")
ISSUE_COLUMNS = ("issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status", "blocking_scope", "blocking_reason", "issue_origin", "integration_transition", "issue_count")
MANIFEST_NON_MIRROR_KEYS = (
    "adapter_id", "adapter_missing_categories", "adapter_missing_reason",
    "adapter_side_normalization", "adapter_side_provider_mapping", "admission_rule_id",
    "admission_rule_name", "all_checks_passed",
    "artifact_reference_paths_not_recursively_opened", "batch_context_contract",
    "candidate_fields", "candidate_invalid_projection", "candidate_mapping_invalid_reason",
    "context_before_candidate", "context_failure_dispatch_code", "context_failure_flags",
    "context_items", "context_routing_order", "context_routing_reasons",
    "contract_pass_count", "contract_row_count", "coverage_issue_affected_rules",
    "coverage_issue_status", "coverage_issue_transition", "current_registered_rule_order",
    "dispatch_error_codes", "dispatch_error_fields", "download_result_context_contract",
    "evaluation_context_contract", "expected_base_commit", "expected_base_subject",
    "formal_call_count_after_candidate_gate", "formal_evaluator",
    "formal_positional_argument_order", "formal_result_type", "future_adapter_handler",
    "future_adapter_ready_rule_ids", "future_callable_discovered_rule_ids",
    "future_first_eight_handler_identity_reused", "future_registered_rule_order",
    "independent_oracle", "issue_inventory_preserved_byte_identical",
    "issue_inventory_row_count", "issue_inventory_sha256", "known_not_registered_rule_ids",
    "known_rule_ids", "manifest_schema_version", "no_partial_exact13_on_failure",
    "normalized_values_projection", "oracle_call_count_after_source_validation",
    "original_object_identity_preserved", "outcome_vocabulary", "output_file_count",
    "output_files", "output_sha256", "output_sha256_excludes_manifest_self_hash",
    "project", "projection_truth_matrix_group_counts", "projection_truth_matrix_pass_count",
    "projection_truth_matrix_row_count", "provider_fields_consumed", "readiness",
    "real_provider_duplicate_identity_key_count", "recommended_next_step", "result_fields",
    "result_schema_version", "routing_matrix_group_counts", "routing_matrix_pass_count",
    "routing_matrix_row_count", "runtime_dispatch_error_type_reused_by_identity",
    "future_exact9_public_dispatch_contract", "runtime_public_constants_reused_by_identity",
    "runtime_result_type_reused_by_identity", "safety_pass_count", "safety_row_count",
    "source_boundary_name", "source_documents_parsed_only_from_frozen_snapshot_bytes",
    "source_exact10_full_invariant_validation", "source_exact_type_required",
    "source_input_count", "source_input_paths", "source_input_sha256",
    "source_input_verification", "source_invariant_invalid_reason",
    "source_oracle_full_exact10_equality_required", "source_prevalidated_before_oracle",
    "source_structural_checks_before_first_explicit_content_read", "source_type_invalid_reason",
    "stage", "stage_authorization_context_contract", "standalone_result_fields", "step",
    "stop_boundaries", "validation_failures",
)


class _StringSubclass(str):
    pass


class _TupleSubclass(tuple):
    pass


def _readiness() -> dict[str, bool]:
    true = (
        "admit_009_standalone_evaluator_implemented", "admit_009_unified_adapter_contract_frozen",
        "admit_009_candidate_projection_contract_frozen", "admit_009_context_routing_contract_frozen",
        "admit_009_context_before_candidate_enforced_by_design", "admit_009_key_absent_only_missing_contract_frozen",
        "admit_009_formal_exactly_once_contract_frozen", "admit_009_oracle_exactly_once_contract_frozen",
        "admit_009_original_object_identity_contract_frozen", "admit_009_standalone_source_exact_type_validation_frozen",
        "admit_009_standalone_exact10_invariant_validation_frozen", "admit_009_source_oracle_full_exact10_equality_frozen",
        "admit_009_exact10_to_exact13_projection_frozen", "admit_009_candidate_invalid_projection_frozen",
        "admit_009_dispatch_failure_boundaries_frozen", "admit_009_provider_mapping_boundary_preserved",
        "future_exact9_reuses_exact8_public_type_identity", "future_exact9_first_eight_handler_identity_frozen",
        "ready_for_unified_dispatch_runtime_with_admit_001_to_009_implementation",
        "feature_semantics_audit_required_before_training",
    )
    false = (
        "real_provider_duplicate_identity_mapping_validated", "real_provider_duplicate_identity_key_count_nonzero",
        "admit_009_unified_adapter_implemented", "admit_009_registered_in_engine",
        "unified_dispatch_runtime_with_admit_001_to_009_implemented", "admit_010_standalone_evaluator_implemented",
        "admit_010_to_015_registered_in_engine", "all_15_rules_covered", "evaluate_all_rules_implemented",
        "combined_candidate_verdict_contract_frozen", "combined_candidate_verdict_implemented",
        "cross_rule_precedence_frozen", "real_candidate_evaluation", "ready_for_bulk_download_now",
        "ready_for_training", "ready_to_train_now",
    )
    return {**{key: True for key in true}, **{key: False for key in false}}


def _git(*args: str, text: bool = False) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(("git", *args), cwd=ROOT, check=False, capture_output=True, text=text)


def _verify_sources() -> tuple[dict[str, Any], ...]:
    if len(SOURCE_BOUNDARY) != 18 or len({path for path, _ in SOURCE_BOUNDARY}) != 18:
        raise AssertionError("Exact18 boundary drift")
    if _git("show", "-s", "--format=%s", BASE, text=True).stdout.rstrip("\n") != SUBJECT:
        raise AssertionError("base subject mismatch")
    if _git("merge-base", "--is-ancestor", BASE, "HEAD").returncode:
        raise AssertionError("base is not ancestor")
    structural: list[tuple[Path, str]] = []
    for relative, expected in SOURCE_BOUNDARY:
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or path.parts[:2] == ("data", "raw") or path.parts[0] == "checkpoints":
            raise AssertionError("unsafe source")
        if _git("ls-files", "--error-unmatch", "--", relative).returncode:
            raise AssertionError(f"untracked source: {relative}")
        tree = _git("ls-tree", BASE, "--", relative, text=True)
        metadata = tree.stdout.split("\t", 1)[0].split() if tree.returncode == 0 else []
        target = ROOT / path
        try:
            mode = target.lstat().st_mode
            target.resolve().relative_to(ROOT.resolve())
        except (FileNotFoundError, ValueError) as error:
            raise AssertionError(f"unsafe source: {relative}") from error
        if len(metadata) != 3 or metadata[1] != "blob" or metadata[0] not in ("100644", "100755"):
            raise AssertionError(f"base blob invalid: {relative}")
        if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
            raise AssertionError(f"source type invalid: {relative}")
        structural.append((target, expected))
    verified = []
    for order, ((relative, expected), (target, _)) in enumerate(zip(SOURCE_BOUNDARY, structural, strict=True), 1):
        base_bytes = _git("show", f"{BASE}:{relative}").stdout
        fs_bytes = target.read_bytes()
        base_sha = hashlib.sha256(base_bytes).hexdigest()
        fs_sha = hashlib.sha256(fs_bytes).hexdigest()
        if base_sha != expected or fs_sha != expected:
            raise AssertionError(f"source hash mismatch: {relative}")
        if order == 1:
            tree = ast.parse(fs_bytes.decode("utf-8"))
            functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
            assignments = {
                target_node.id: ast.unparse(node.value)
                for node in tree.body if isinstance(node, ast.Assign)
                for target_node in node.targets if isinstance(target_node, ast.Name)
            }
            if "evaluate_admission_rule" not in functions or "evaluate_admission_rule" in assignments:
                raise AssertionError("Exact8 must define its own public successor dispatcher")
            expected_reuse = {
                "UnifiedAdmissionRuleEvaluation": "predecessor.UnifiedAdmissionRuleEvaluation",
                "UnifiedAdmissionDispatchError": "predecessor.UnifiedAdmissionDispatchError",
                "RESULT_SCHEMA_VERSION": "predecessor.RESULT_SCHEMA_VERSION",
                "RESULT_FIELDS": "predecessor.RESULT_FIELDS",
                "DISPATCH_ERROR_FIELDS": "predecessor.DISPATCH_ERROR_FIELDS",
                "DISPATCH_ERROR_CODES": "predecessor.DISPATCH_ERROR_CODES",
                "OUTCOME_VOCABULARY": "predecessor.OUTCOME_VOCABULARY",
            }
            if any(assignments.get(name) != value for name, value in expected_reuse.items()):
                raise AssertionError("Exact8 public type/constant identity precedent changed")
        verified.append({
            "source_order": order, "source_relative_path": relative, "tracked": True,
            "base_tree_blob": True, "filesystem_regular": True, "non_symlink": True,
            "expected_sha256": expected, "base_tree_sha256": base_sha,
            "filesystem_sha256": fs_sha, "source_verified": True,
        })
    return tuple(verified)


def _csv(path: Path, columns: tuple[str, ...]) -> tuple[dict[str, str], ...]:
    reader = csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"), newline=""))
    if tuple(reader.fieldnames or ()) != columns:
        raise AssertionError(f"header mismatch: {path.name}")
    rows = tuple(dict(row) for row in reader)
    if any(tuple(row) != columns or any(value is None for value in row.values()) for row in rows):
        raise AssertionError(f"row shape mismatch: {path.name}")
    return rows


def _verify_contract(rows: tuple[dict[str, str], ...]) -> None:
    if len(rows) != 75:
        raise AssertionError("contract count")
    if tuple(row["contract_order"] for row in rows) != tuple(map(str, range(1, 76))):
        raise AssertionError("contract order")
    if tuple(row["contract_id"] for row in rows) != tuple(f"CONTRACT_{i:03d}" for i in range(1, 76)):
        raise AssertionError("contract ids")
    if any(row["contract_status"] != "frozen" for row in rows):
        raise AssertionError("contract status")
    values = {(row["contract_group"], row["contract_subject"]): row["contract_value"] for row in rows}
    required = {
        ("identity", "admission_rule_id"): RULE_ID,
        ("identity", "admission_rule_name"): RULE_NAME,
        ("identity", "adapter_id"): ADAPTER_ID,
        ("identity", "formal_evaluator"): "evaluate_admit_009",
        ("identity", "formal_result_type"): "Admit009EvaluationResult",
        ("identity", "independent_oracle"): "classify_admit_009_duplicate_identity_key_design",
        ("runtime_continuity", "public_dispatch"): "new_successor_function_same_exact8_signature_and_dispatch_semantics_uses_exact9_registry_not_exact8_function_identity",
        ("registration", "current_exact8_order"): "|".join(CURRENT_ORDER),
        ("registration", "future_exact9_order"): "|".join(FUTURE_ORDER),
        ("registration", "first_eight_handler_identity"): "8_of_8_exact8_objects",
        ("routing", "complete_order"): "|".join(ROUTING_ORDER),
        ("candidate", "only_missing"): "required_key_absent_only",
        ("candidate", "non_mapping"): CANDIDATE_REASON,
        ("candidate", "key_absent"): MISSING_REASON,
        ("projection", "fields"): "|".join(RESULT_FIELDS),
        ("projection", "schema_version"): SCHEMA,
        ("projection", "adapter_id"): ADAPTER_ID,
        ("provider", "mapping"): "unvalidated",
        ("provider", "real_key_count"): "0",
        ("readiness", "next_step"): NEXT_STEP,
    }
    if any(values.get(key) != value for key, value in required.items()) or len(values) != 75:
        raise AssertionError("contract semantic drift")
    if rows[6]["contract_group"] != "runtime_continuity" or rows[6]["contract_subject"] != "public_dispatch":
        raise AssertionError("contract public-dispatch row position")
    if any("evaluate_admission_rule_exact8_identity" in row.values() for row in rows):
        raise AssertionError("obsolete public-dispatch identity claim")


def _verify_exact13(value: str, *, reason: str | None = None) -> None:
    record = json.loads(value)
    if tuple(record) != RESULT_FIELDS or record["schema_version"] != SCHEMA:
        raise AssertionError("Exact13 shape")
    if record["admission_rule_id"] != RULE_ID or record["admission_rule_name"] != RULE_NAME or record["adapter_id"] != ADAPTER_ID:
        raise AssertionError("Exact13 identity")
    if record["normalized_values"] != record["validated_candidate_fields"]:
        raise AssertionError("Exact13 normalized projection")
    consumed_context = record["consumed_context_items"]
    if record["consumed_candidate_fields"] != list(CANDIDATE_FIELDS) or consumed_context not in (
        [], [CONTEXT_ITEMS[0]], list(CONTEXT_ITEMS)
    ):
        raise AssertionError("Exact13 consumed fields")
    if record["evaluator_io_used"] is not False or record["blocks_candidate"] is (record["outcome"] == "passed"):
        raise AssertionError("Exact13 outcome invariant")
    if reason is not None and record["reason"] != reason:
        raise AssertionError("Exact13 reason")


def _verify_routing(rows: tuple[dict[str, str], ...]) -> None:
    ids = (
        "batch_none", "batch_non_mapping", "batch_key_missing", "evaluation_none",
        "evaluation_non_mapping", "evaluation_key_missing", "download_non_none", "stage_non_none",
        "multiple_failure_precedence", "candidate_bomb", "batch_mapping_subclass", "batch_extra_keys",
        "batch_identity_single_lookup", "evaluation_mapping_subclass", "evaluation_extra_keys",
        "policy_identity_single_lookup", "policy_none_present", "batch_empty_present",
        "candidate_non_mapping", "candidate_key_absent", "candidate_mapping_subclass",
        "candidate_extra_fields", "candidate_not_mutated", "scalar_identity_single_lookup",
        "scalar_none", "scalar_integer", "scalar_empty", "scalar_str_subclass", "scalar_non_ascii",
        "scalar_whitespace", "scalar_malformed", "canonical_unique", "canonical_duplicate",
        "invalid_policy", "invalid_batch", "formal_exactly_once", "oracle_exactly_once",
        "three_object_identity", "no_mutation_copy_normalization", "exact_type_accepted",
        "wrong_type_rejected", "subclass_rejected", "storage_order_rejected",
        "dataclass_order_rejected", "reconstruction_rejected", "failure_prevents_oracle",
        "full_exact10_mismatch", "passed", "blocked", "scalar_invalid", "policy_invalid", "batch_invalid",
    )
    if len(rows) != 52 or tuple(row["case_id"] for row in rows) != ids:
        raise AssertionError("routing inventory")
    if tuple(row["matrix_order"] for row in rows) != tuple(map(str, range(1, 53))):
        raise AssertionError("routing order")
    if Counter(row["matrix_group"] for row in rows) != Counter(context=18, candidate=6, forwarding=11, call=4, source=8, projection=5):
        raise AssertionError("routing groups")
    if any(row["case_passed"] != "true" or not row["condition"] or not row["expected_behavior"] for row in rows):
        raise AssertionError("routing status")
    by_id = {row["case_id"]: row for row in rows}
    failures = {
        "batch_none": CONTEXT_REASONS["batch_context"], "batch_non_mapping": CONTEXT_REASONS["batch_context"],
        "batch_key_missing": CONTEXT_REASONS["batch_context_key"], "evaluation_none": CONTEXT_REASONS["evaluation_context"],
        "evaluation_non_mapping": CONTEXT_REASONS["evaluation_context"], "evaluation_key_missing": CONTEXT_REASONS["evaluation_context_key"],
        "download_non_none": CONTEXT_REASONS["download_result_context"], "stage_non_none": CONTEXT_REASONS["stage_authorization_context"],
        "multiple_failure_precedence": CONTEXT_REASONS["batch_context"], "candidate_bomb": CONTEXT_REASONS["batch_context"],
    }
    for case_id, reason in failures.items():
        row = by_id[case_id]
        error = json.loads(row["expected_result_json"])
        if row["expected_reason"] != reason:
            raise AssertionError(f"routing expected reason: {case_id}")
        if tuple(error) != ERROR_FIELDS or tuple(error.values()) != ("UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", RULE_ID, True, True, True, reason):
            raise AssertionError(f"routing failure: {case_id}")
        if (row["formal_call_count"], row["oracle_call_count"], row["candidate_access_status"]) != ("0", "0", "not_accessed"):
            raise AssertionError(f"routing precedence: {case_id}")
    for case_id, reason in (("candidate_non_mapping", CANDIDATE_REASON), ("candidate_key_absent", MISSING_REASON)):
        row = by_id[case_id]
        _verify_exact13(row["expected_result_json"], reason=reason)
        if json.loads(row["expected_result_json"])["consumed_context_items"] != list(CONTEXT_ITEMS):
            raise AssertionError("candidate invalid canonical context order")
        if (row["formal_call_count"], row["oracle_call_count"]) != ("0", "0"):
            raise AssertionError("candidate gate calls")
    source_failures = {"wrong_type_rejected": SOURCE_TYPE_REASON, "subclass_rejected": SOURCE_TYPE_REASON,
                       "storage_order_rejected": SOURCE_INVARIANT_REASON, "dataclass_order_rejected": SOURCE_INVARIANT_REASON,
                       "reconstruction_rejected": SOURCE_INVARIANT_REASON, "failure_prevents_oracle": SOURCE_INVARIANT_REASON,
                       "full_exact10_mismatch": SOURCE_INVARIANT_REASON}
    for case_id, reason in source_failures.items():
        if by_id[case_id]["expected_reason"] != reason:
            raise AssertionError("source failure reason")
    for row in rows:
        if row["expected_result_json"] and row["case_id"] not in failures:
            document = json.loads(row["expected_result_json"])
            if tuple(document) == RESULT_FIELDS:
                _verify_exact13(row["expected_result_json"])
            elif tuple(document) != ERROR_FIELDS:
                raise AssertionError("routing result schema")


def _verify_truth(rows: tuple[dict[str, str], ...]) -> None:
    if len(rows) != 49 or Counter(row["case_group"] for row in rows) != Counter(
        standalone_exact32=32, routing_dispatch=8, adapter_candidate_invalid=2,
        source_validation_failure=5, issue_coverage_boundary=2,
    ):
        raise AssertionError("truth inventory")
    if any(row["case_passed"] != "true" for row in rows):
        raise AssertionError("truth status")
    standalone = importlib.import_module("covalent_ext.covapie_bulk_download_admission_admit_009_rule_logic_interface")
    oracle = importlib.import_module("covalent_ext.covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate")
    key = "covapie_dup_v1_sha256_" + "1" * 64
    low = "covapie_dup_v1_sha256_" + "0" * 64
    high = "covapie_dup_v1_sha256_" + "2" * 64
    other = "covapie_dup_v1_sha256_" + "f" * 64
    policy = "covapie_duplicate_identity_key_contract_v1"
    cases = (
        ("scalar_none", None, (), policy), ("scalar_integer", 7, (), policy),
        ("scalar_str_subclass", _StringSubclass(key), (), policy), ("scalar_empty", "", (), policy),
        ("scalar_non_ascii", "covapie_dup_v1_sha256_" + "é" * 64, (), policy),
        ("scalar_wrong_prefix", "covapie_dup_v2_sha256_" + "1" * 64, (), policy),
        ("scalar_uppercase_digest", "covapie_dup_v1_sha256_" + "A" * 64, (), policy),
        ("scalar_short_digest", "covapie_dup_v1_sha256_" + "1" * 63, (), policy),
        ("scalar_long_digest", "covapie_dup_v1_sha256_" + "1" * 65, (), policy),
        ("scalar_non_hex", "covapie_dup_v1_sha256_" + "g" * 64, (), policy),
        ("scalar_whitespace", " " + key, (), policy), ("scalar_canonical", key, (), policy),
        ("policy_none", key, (), None), ("policy_str_subclass", key, (), _StringSubclass(policy)),
        ("policy_wrong_value", key, (), "covapie_duplicate_identity_key_contract_v2"),
        ("policy_exact_valid", key, (), policy), ("batch_none", key, None, policy),
        ("batch_list", key, [], policy), ("batch_tuple_subclass", key, _TupleSubclass(), policy),
        ("batch_non_str_member", key, (7,), policy),
        ("batch_str_subclass_member", key, (_StringSubclass(other),), policy),
        ("batch_malformed_member", key, ("bad",), policy), ("batch_unsorted", key, (high, low), policy),
        ("batch_duplicate_members", key, (other, other), policy), ("batch_empty_valid", key, (), policy),
        ("batch_one_unrelated", key, (other,), policy), ("batch_one_matching", key, (key,), policy),
        ("batch_multiple_contains", key, (low, key, high), policy),
        ("canonical_unique_passed", key, (other,), policy),
        ("canonical_duplicate_blocked", key, (key,), policy),
        ("policy_invalid_retains_pair", key, (), "wrong"),
        ("batch_invalid_retains_pair", key, [key], policy),
    )
    if tuple(row["case_id"] for row in rows[:32]) != tuple(f"STANDALONE_{case_id}" for case_id, *_ in cases):
        raise AssertionError("truth standalone case order")
    for row, (_, scalar, batch, policy_value) in zip(rows[:32], cases, strict=True):
        observed_source = standalone.evaluate_admit_009(scalar, batch, policy_value)
        classification = oracle.classify_admit_009_duplicate_identity_key_design(scalar, batch, policy_value)
        observed_source_json = json.loads(json.dumps(vars(observed_source), ensure_ascii=True))
        observed_oracle_json = dict(zip(SOURCE_FIELDS, (
            RULE_ID, classification["outcome"], classification["passed"],
            classification["blocks_candidate"], classification["reason"],
            classification["canonical_duplicate_identity_key"], classification["validated_candidate_fields"],
            classification["consumed_candidate_fields"], classification["consumed_context_items"],
            classification["evaluator_io_used"],
        ), strict=True))
        observed_oracle_json = json.loads(json.dumps(observed_oracle_json, ensure_ascii=True))
        source = json.loads(row["source_exact10_json"])
        expected = json.loads(row["oracle_exact10_json"])
        unified = json.loads(row["unified_exact13_json"])
        if tuple(source) != SOURCE_FIELDS or source != expected or source != observed_source_json or expected != observed_oracle_json:
            raise AssertionError("truth Exact10 equality")
        if row["expected_reason"] != source["reason"]:
            raise AssertionError("truth expected reason")
        if tuple(unified) != RESULT_FIELDS or unified["normalized_values"] != source["validated_candidate_fields"]:
            raise AssertionError("truth projection")
        if unified["outcome"] != source["outcome"] or unified["reason"] != source["reason"]:
            raise AssertionError("truth passthrough")
        if (row["formal_call_count"], row["oracle_call_count"]) != ("1", "1"):
            raise AssertionError("truth call counts")
    for row in rows[32:40]:
        if row["expected_dispatch_code"] != "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID" or row["unified_exact13_json"]:
            raise AssertionError("truth context boundary")
    for row in rows[40:42]:
        _verify_exact13(row["unified_exact13_json"], reason=row["expected_reason"])
    for row in rows[42:47]:
        if row["expected_dispatch_code"] != "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY" or row["unified_exact13_json"]:
            raise AssertionError("truth source boundary")
    if tuple(row["case_id"] for row in rows[-2:]) != ("BOUNDARY_issue_bytes", "BOUNDARY_coverage"):
        raise AssertionError("truth issue boundary")


def _verify_safety(rows: tuple[dict[str, str], ...]) -> None:
    positive = (
        "adapter_contract_design", "context_routing_design", "candidate_projection_design",
        "standalone_source_validation_design", "exact10_oracle_equality_design",
        "exact10_to_exact13_projection_design", "future_identity_contract",
        "deterministic_materialization", "source_verification", "issue_byte_preservation",
    )
    negative = (
        "actual_adapter_handler", "registry_modification", "exact9_runtime", "provider_mapping",
        "provider_key_generation", "real_candidate_evaluation", "admit_010", "evaluate_all_rules",
        "combined_verdict", "raw_read", "network", "download", "checkpoint", "torch", "numpy",
        "rdkit", "model_forward", "model_loss", "training", "fine_tune", "parameter_update",
        "stage", "commit", "push", "gh",
    )
    expected = tuple((item, "true") for item in positive) + tuple((item, "false") for item in negative)
    observed = tuple((row["safety_item"], row["expected_executed"]) for row in rows)
    if observed != expected or any(row["observed_executed"] != row["expected_executed"] or row["safety_passed"] != "true" for row in rows):
        raise AssertionError("safety inventory")


def _verify_ast() -> None:
    path = ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    functions = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assignments: set[str] = set()
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else (node.target,) if isinstance(node, ast.AnnAssign) else ()
        assignments.update(target.id for target in targets if isinstance(target, ast.Name))
    if ({"_evaluate_registered_admit_009", "evaluate_admission_rule"} & (functions | assignments)) or "EVALUATOR_REGISTRY" in assignments:
        raise AssertionError("runtime implementation leaked into design gate")


def _verify_manifest(manifest: dict[str, Any], verification: tuple[dict[str, Any], ...], actual_hashes: dict[str, str]) -> None:
    readiness = _readiness()
    required = {
        "project": "CovaPIE", "step": "ADMIT_009 unified adapter contract design gate v1",
        "stage": "covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate_v1",
        "manifest_schema_version": "covapie_admit_009_unified_adapter_contract_manifest_v1",
        "expected_base_commit": BASE, "expected_base_subject": SUBJECT,
        "admission_rule_id": RULE_ID, "admission_rule_name": RULE_NAME, "adapter_id": ADAPTER_ID,
        "formal_evaluator": "evaluate_admit_009", "formal_result_type": "Admit009EvaluationResult",
        "future_adapter_handler": "_evaluate_registered_admit_009",
        "independent_oracle": "classify_admit_009_duplicate_identity_key_design",
        "candidate_fields": list(CANDIDATE_FIELDS), "context_items": list(CONTEXT_ITEMS),
        "current_registered_rule_order": list(CURRENT_ORDER), "future_registered_rule_order": list(FUTURE_ORDER),
        "future_callable_discovered_rule_ids": list(FUTURE_ORDER), "future_adapter_ready_rule_ids": list(FUTURE_ORDER),
        "known_rule_ids": list(KNOWN_IDS), "known_not_registered_rule_ids": list(KNOWN_IDS[9:]),
        "future_first_eight_handler_identity_reused": {rule_id: True for rule_id in CURRENT_ORDER},
        "future_exact9_public_dispatch_contract": "new_successor_function_same_exact8_signature_and_dispatch_semantics_uses_exact9_registry",
        "runtime_result_type_reused_by_identity": "UnifiedAdmissionRuleEvaluation",
        "runtime_dispatch_error_type_reused_by_identity": "UnifiedAdmissionDispatchError",
        "runtime_public_constants_reused_by_identity": [
            "RESULT_SCHEMA_VERSION", "RESULT_FIELDS", "DISPATCH_ERROR_FIELDS",
            "DISPATCH_ERROR_CODES", "OUTCOME_VOCABULARY",
        ],
        "result_schema_version": SCHEMA, "result_fields": list(RESULT_FIELDS),
        "standalone_result_fields": list(SOURCE_FIELDS), "dispatch_error_fields": list(ERROR_FIELDS),
        "dispatch_error_codes": list(ERROR_CODES), "outcome_vocabulary": list(OUTCOMES),
        "context_routing_order": list(ROUTING_ORDER), "context_routing_reasons": CONTEXT_REASONS,
        "context_failure_dispatch_code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        "context_failure_flags": {"known_rule": True, "callable_discovered": True, "adapter_ready": True},
        "batch_context_contract": "Mapping_single_direct_required_lookup_KeyError_only_missing_original_identity",
        "evaluation_context_contract": "Mapping_single_direct_required_lookup_KeyError_only_missing_original_identity",
        "download_result_context_contract": "exact_none", "stage_authorization_context_contract": "exact_none",
        "context_before_candidate": True,
        "candidate_mapping_invalid_reason": CANDIDATE_REASON, "adapter_missing_reason": MISSING_REASON,
        "adapter_missing_categories": ["required_key_absent"],
        "formal_positional_argument_order": ["scalar_object", "batch_duplicate_identity_keys_object", "duplicate_identity_key_contract_object"],
        "formal_call_count_after_candidate_gate": 1, "oracle_call_count_after_source_validation": 1,
        "original_object_identity_preserved": True, "adapter_side_normalization": False,
        "adapter_side_provider_mapping": False, "source_prevalidated_before_oracle": True,
        "source_exact_type_required": True, "source_exact10_full_invariant_validation": True,
        "source_oracle_full_exact10_equality_required": True, "no_partial_exact13_on_failure": True,
        "normalized_values_projection": "source.validated_candidate_fields",
        "source_type_invalid_reason": SOURCE_TYPE_REASON, "source_invariant_invalid_reason": SOURCE_INVARIANT_REASON,
        "contract_row_count": 75, "contract_pass_count": 75,
        "routing_matrix_row_count": 52, "routing_matrix_pass_count": 52,
        "routing_matrix_group_counts": {"call": 4, "candidate": 6, "context": 18, "forwarding": 11, "projection": 5, "source": 8},
        "projection_truth_matrix_row_count": 49, "projection_truth_matrix_pass_count": 49,
        "projection_truth_matrix_group_counts": {"adapter_candidate_invalid": 2, "issue_coverage_boundary": 2, "routing_dispatch": 8, "source_validation_failure": 5, "standalone_exact32": 32},
        "safety_row_count": 35, "safety_pass_count": 35, "issue_inventory_row_count": 11,
        "issue_inventory_preserved_byte_identical": True,
        "issue_inventory_sha256": SOURCE_BOUNDARY[7][1], "coverage_issue_status": "open",
        "coverage_issue_affected_rules": "ADMIT_009–ADMIT_015",
        "coverage_issue_transition": "admit_008_implemented_and_removed_from_open_coverage_scope",
        "real_provider_duplicate_identity_mapping_validated": False,
        "real_provider_duplicate_identity_key_count": 0, "provider_fields_consumed": [],
        "source_input_count": 18, "source_input_paths": [path for path, _ in SOURCE_BOUNDARY],
        "source_input_sha256": dict(SOURCE_BOUNDARY), "source_input_verification": list(verification),
        "source_boundary_name": "fixed_ordered_exact18_committed_source_boundary",
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "output_file_count": 6, "output_files": list(OUTPUTS),
        "output_sha256": {name: actual_hashes[name] for name in OUTPUTS[:5]},
        "output_sha256_excludes_manifest_self_hash": True,
        "stop_boundaries": [
            "adapter_handler_not_implemented", "exact8_runtime_unchanged", "admit_009_unregistered",
            "exact9_runtime_not_implemented", "provider_mapping_not_validated", "admit_010_not_started",
            "evaluate_all_rules_not_implemented", "combined_candidate_verdict_not_implemented",
            "real_candidate_evaluation_not_executed", "raw_network_download_forbidden", "training_forbidden",
        ],
        "recommended_next_step": NEXT_STEP, "readiness": readiness,
        "validation_failures": [], "all_checks_passed": True,
    }
    if any(manifest.get(key) != value for key, value in required.items()):
        raise AssertionError("manifest semantic mismatch")
    if any(manifest.get(key) is not value for key, value in readiness.items()):
        raise AssertionError("readiness mirror drift")
    if set(manifest) != set(MANIFEST_NON_MIRROR_KEYS) | set(readiness):
        raise AssertionError("manifest unknown key")
    if "runtime_public_api_reused_by_identity" in manifest:
        raise AssertionError("obsolete public dispatcher identity key")
    if len(manifest) != 130 or len(manifest["readiness"]) != 36:
        raise AssertionError("manifest key/readiness count")
    if manifest["future_first_eight_handler_identity_reused"] != {rule_id: True for rule_id in CURRENT_ORDER}:
        raise AssertionError("future handler identity")
    if manifest["adapter_side_normalization"] is not False or manifest["adapter_side_provider_mapping"] is not False:
        raise AssertionError("adapter/provider boundary")
    if manifest["candidate_invalid_projection"] != {
        "outcome": "invalid", "passed": False, "blocks_candidate": True,
        "normalized_values": [], "validated_candidate_fields": [],
        "consumed_candidate_fields": list(CANDIDATE_FIELDS),
        "consumed_context_items": list(CONTEXT_ITEMS), "evaluator_io_used": False,
        "adapter_id": ADAPTER_ID,
    }:
        raise AssertionError("candidate invalid manifest")


def _validate_output_tree(output_root: Path = OUTPUT_ROOT, *, enforce_frozen_hashes: bool = True) -> dict[str, str]:
    if output_root.is_symlink() or not output_root.is_dir():
        raise AssertionError("output root type")
    entries = tuple(output_root.iterdir())
    if {entry.name for entry in entries} != set(OUTPUTS) or any(entry.is_symlink() or not entry.is_file() for entry in entries):
        raise AssertionError("output inventory")
    hashes = {name: hashlib.sha256((output_root / name).read_bytes()).hexdigest() for name in OUTPUTS}
    contract = _csv(output_root / OUTPUTS[0], CONTRACT_COLUMNS)
    routing = _csv(output_root / OUTPUTS[1], ROUTING_COLUMNS)
    truth = _csv(output_root / OUTPUTS[2], TRUTH_COLUMNS)
    safety = _csv(output_root / OUTPUTS[3], SAFETY_COLUMNS)
    issues = _csv(output_root / OUTPUTS[4], ISSUE_COLUMNS)
    _verify_contract(contract)
    _verify_routing(routing)
    _verify_truth(truth)
    _verify_safety(safety)
    predecessor_issue = ROOT / SOURCE_BOUNDARY[7][0]
    if (output_root / OUTPUTS[4]).read_bytes() != predecessor_issue.read_bytes() or len(issues) != 11:
        raise AssertionError("issue bytes")
    issue_map = {row["issue_id"]: row for row in issues}
    if issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] != "|".join(KNOWN_IDS[8:]):
        raise AssertionError("coverage narrowed early")
    verification = _verify_sources()
    manifest = json.loads((output_root / OUTPUTS[5]).read_text(encoding="utf-8"))
    if type(manifest) is not dict:
        raise AssertionError("manifest root")
    _verify_manifest(manifest, verification, hashes)
    if enforce_frozen_hashes and hashes != FROZEN_OUTPUT_SHA256:
        raise AssertionError("frozen output hash mismatch")
    return hashes


def _verify_behavior(module: Any) -> None:
    if tuple(field.name for field in fields(module.UnifiedAdmissionEvaluationDesignRecord)) != RESULT_FIELDS:
        raise AssertionError("design Exact13 fields")
    key = "covapie_dup_v1_sha256_" + "1" * 64
    batch = ("covapie_dup_v1_sha256_" + "f" * 64,)
    policy = "covapie_duplicate_identity_key_contract_v1"
    calls: list[tuple[str, object, object, object]] = []
    formal = importlib.import_module("covalent_ext.covapie_bulk_download_admission_admit_009_rule_logic_interface").evaluate_admit_009
    oracle = importlib.import_module("covalent_ext.covapie_bulk_download_admission_admit_009_duplicate_identity_key_contract_design_gate").classify_admit_009_duplicate_identity_key_design
    def observed_formal(a: object, b: object, c: object) -> object:
        calls.append(("formal", a, b, c)); return formal(a, b, c)
    def observed_oracle(a: object, b: object, c: object) -> object:
        calls.append(("oracle", a, b, c)); return oracle(a, b, c)
    result = module.route_and_project_for_design(
        {CANDIDATE_FIELDS[0]: key}, batch_context={CONTEXT_ITEMS[1]: batch},
        evaluation_context={CONTEXT_ITEMS[0]: policy}, download_result_context=None,
        stage_authorization_context=None, formal_evaluator=observed_formal, oracle_callable=observed_oracle,
    )
    if [call[0] for call in calls] != ["formal", "oracle"] or any(call[1] is not key or call[2] is not batch or call[3] is not policy for call in calls):
        raise AssertionError("call count/order/identity")
    _verify_exact13(json.dumps({field.name: getattr(result, field.name) for field in fields(result)}, separators=(",", ":")))
    class Bomb:
        def __getitem__(self, key: object) -> object:
            raise AssertionError("candidate accessed")
    try:
        module.route_and_project_for_design(Bomb(), batch_context=None, evaluation_context=None,
                                            download_result_context=None, stage_authorization_context=None,
                                            formal_evaluator=observed_formal, oracle_callable=observed_oracle)
    except module.AdapterContractDesignError as error:
        if tuple(getattr(error, name) for name in ERROR_FIELDS) != (
            "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", RULE_ID, True, True, True, CONTEXT_REASONS["batch_context"]
        ):
            raise AssertionError("context failure shape")
    else:
        raise AssertionError("context failure not raised")


def main() -> int:
    _verify_ast()
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in OUTPUT_ROOT.iterdir()}
    module = importlib.import_module(MODULE)
    after = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in OUTPUT_ROOT.iterdir()}
    if before != after:
        raise AssertionError("import side effect")
    _verify_behavior(module)
    hashes = _validate_output_tree()
    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        module.run_covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate_v1(Path(first), repo_root=ROOT)
        module.run_covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate_v1(Path(second), repo_root=ROOT)
        first_bytes = {name: (Path(first) / name).read_bytes() for name in OUTPUTS}
        second_bytes = {name: (Path(second) / name).read_bytes() for name in OUTPUTS}
        if first_bytes != second_bytes:
            raise AssertionError("double materialization differs")
        _validate_output_tree(Path(first), enforce_frozen_hashes=False)
        if any(hashlib.sha256(first_bytes[name]).hexdigest() != hashes[name] for name in OUTPUTS):
            raise AssertionError("materialization differs from committed output")
    print(json.dumps({"checked": True, "output_sha256": hashes}, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
