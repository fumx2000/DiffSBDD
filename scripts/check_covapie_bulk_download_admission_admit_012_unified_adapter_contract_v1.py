#!/usr/bin/env python3
"""Independent checker for the ADMIT_012 unified-adapter Design contract."""
from __future__ import annotations

import ast
import csv
import hashlib
import importlib
import io
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import fields
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
MODULE = "covalent_ext.covapie_bulk_download_admission_admit_012_unified_adapter_contract_design_gate"
BASE = "16bedd92f97a4c52743f4f923d5c42ae8fee9a84"
SUBJECT = "add CovaPIE ADMIT_012 standalone evaluator interface v1"
STAGE = "covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1"
OUTPUT_ROOT = ROOT / "data/derived/covalent_small" / STAGE
RULE_ID = "ADMIT_012"
RULE_NAME = "future_download_integrity_fields_required"
ADAPTER_ID = "covapie_admit_012_unified_adapter_v1"
SCHEMA = "covapie_unified_admission_rule_evaluation_v1"
CURRENT_ORDER = tuple(f"ADMIT_{index:03d}" for index in range(1, 12))
FUTURE_ORDER = (*CURRENT_ORDER, RULE_ID)
KNOWN_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
DOWNLOAD_FIELDS = (
    "download_result_status", "observed_http_status",
    "observed_content_length_bytes", "observed_sha256",
)
CONTEXT_ITEMS = (
    "allowed_download_result_statuses", "successful_http_status_contract",
    "content_length_contract", "sha256_format_contract",
)
SOURCE_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_download_result_record", "validated_download_result_fields",
    "consumed_download_result_fields", "consumed_context_items", "evaluator_io_used",
)
RESULT_FIELDS = (
    "schema_version", "admission_rule_id", "admission_rule_name", "outcome",
    "passed", "blocks_candidate", "reason", "normalized_values",
    "validated_candidate_fields", "consumed_candidate_fields",
    "consumed_context_items", "evaluator_io_used", "adapter_id",
)
ERROR_FIELDS = (
    "code", "admission_rule_id", "known_rule", "callable_discovered",
    "adapter_ready", "reason",
)
ERROR_CODES = (
    "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID",
    "UNIFIED_ADMISSION_RULE_ID_UNKNOWN",
    "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
    "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
    "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
)
OUTCOMES = ("passed", "blocked", "invalid", "rejected")
ROUTING_ORDER = (
    "batch_context_must_be_none",
    "evaluation_context_mapping_validation",
    "allowed_download_result_statuses_required_key_lookup",
    "successful_http_status_contract_required_key_lookup",
    "content_length_contract_required_key_lookup",
    "sha256_format_contract_required_key_lookup",
    "download_result_context_mapping_validation",
    "stage_authorization_context_must_be_none",
    "candidate_record_mapping_validation",
    "download_result_exact4_lookup_first_missing_stops",
    "formal_evaluator_exactly_once",
    "standalone_source_exact10_validation",
    "independent_oracle_exactly_once",
    "full_exact10_equality",
    "typed_to_string_exact13_projection",
)
CONTEXT_REASONS = {
    "batch_context": "ADMIT_012_BATCH_CONTEXT_MUST_BE_NONE",
    "evaluation_context": "ADMIT_012_EVALUATION_CONTEXT_MAPPING_REQUIRED",
    "allowed_download_result_statuses": "ADMIT_012_ALLOWED_DOWNLOAD_RESULT_STATUSES_REQUIRED",
    "successful_http_status_contract": "ADMIT_012_SUCCESSFUL_HTTP_STATUS_CONTRACT_REQUIRED",
    "content_length_contract": "ADMIT_012_CONTENT_LENGTH_CONTRACT_REQUIRED",
    "sha256_format_contract": "ADMIT_012_SHA256_FORMAT_CONTRACT_REQUIRED",
    "download_result_context": "ADMIT_012_DOWNLOAD_RESULT_CONTEXT_MAPPING_REQUIRED",
    "stage_authorization_context": "ADMIT_012_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
}
CANDIDATE_REASON = "ADMIT_012_CANDIDATE_RECORD_MAPPING_INVALID"
SOURCE_TYPE_REASON = "ADMIT_012_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
SOURCE_INVARIANT_REASON = "ADMIT_012_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
OUTPUTS = (
    "covapie_admit_012_unified_adapter_contract.csv",
    "covapie_admit_012_download_result_projection_and_context_routing_matrix.csv",
    "covapie_admit_012_unified_result_projection_truth_matrix.csv",
    "covapie_admit_012_unified_adapter_safety_audit.csv",
    "covapie_admit_012_unified_adapter_issue_readiness_inventory.csv",
    "covapie_admit_012_unified_adapter_contract_manifest.json",
)
FROZEN_OUTPUT_SHA256 = {
    OUTPUTS[0]: "12228051428134223dc4db4ec418ced573637047189056f1fb8df908ca2fe6c8",
    OUTPUTS[1]: "50d0e3d8ba7352d139d35a6cda35afad7f40ef4ea111bbea7b3cd31200ec9839",
    OUTPUTS[2]: "843754e8e8c4246f156ac27079fe0b890e62ed1df0703398e21af9b5bdb94fe7",
    OUTPUTS[3]: "736066e78df6e0acf28c539c8432b539855212ef1ff76693feae94d4725cc499",
    OUTPUTS[4]: "bac586f54afac5a860a32ed161b6b8f41210b6ae06eb29f368045f10b3ac81e5",
    OUTPUTS[5]: "1df0e2a09817b7763ec4eb767663db169d3239385094da151af28150c2c55d25",
}
SOURCE_BOUNDARY = (
    ("src/covalent_ext/covapie_bulk_download_admission_admit_012_rule_logic_interface.py", "a7b8585ea6d0080e87fc97f29026fbf5df4667dff21729c95f3045d762a55840"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1/covapie_admit_012_rule_logic_interface_contract.csv", "c5c383e9a9e17c5eb5a4b2c92455da89a78e66f75df7ff31ce0494f08281433e"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1/covapie_admit_012_rule_logic_interface_truth_matrix.csv", "dc97cd08eabad03315a1533332e2b243122696b605c701051f3024f6189cb5d8"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1/covapie_admit_012_rule_logic_interface_issue_readiness_inventory.csv", "bac586f54afac5a860a32ed161b6b8f41210b6ae06eb29f368045f10b3ac81e5"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1/covapie_admit_012_rule_logic_interface_manifest.json", "ad131895c0acfdaf5b350105031647bdcac9667370fb6cd43baf8826bea995c8"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_design_gate.py", "eea31caa76e06507f7dd482dc7c6b2928f6d0f28ded33c47eb31d25b3be7a927"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_routing_and_consumption_contract.csv", "44709c3a679368476c87bcd97dafa2f9cf9bddb4af534c6eb950c565d0919aec"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_interface_truth_matrix.csv", "cc848914ea24b376e29c477c4c0b5e8d32d6fc7caee11873f7a73c4bd207d6db"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_interface_contract_manifest.json", "2845c2623a01087af8842177f4502402d0a8875a77ce12c6a49e2f77c60dae01"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_design_gate.py", "92d6ab08c4e9fa4bd448895687c897f06a596d4fb73a2e9cf7e88ffebaa6448f"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_integrity_field_contract.csv", "03aef0a14257d9a2c028fcc3dd84c161c29b09bca1a1c71456edc66e2e73c9ce"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_integrity_field_contract_manifest.json", "9fadff44ae15474783df2a3997c45f2c4d57a41ca2adbab0b40f1d890f51039f"),
    ("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011.py", "ca8e64897b30f961d999d37ce8af5eb985ddf34f332af40c29bf2142bad6e2c8"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1/covapie_admit_001_to_011_runtime_contract.csv", "9616573151091786f07b3c4d1b6c8343a1ceb796f439e495023abd2f3ad37626"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1/covapie_admit_001_to_011_runtime_manifest.json", "9895bf9b82eb9ca0f9c90ef8012af644a2b325dd971c3e6655b361fc8ff83011"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate.py", "93e6e726092f8c3e66b19c7ab4c6d363d47962c07eeb694c7237b2b0d5a31346"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1/covapie_admit_011_unified_adapter_contract.csv", "4b4b41295364fcb83f807c054e2e561ca2c4a31fbf27fd55d04607f3c127c2cc"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1/covapie_admit_011_unified_adapter_contract_manifest.json", "d5ad2622b5182898c418d774e4c0deb33fc2fb643caaa5da0507cabb3824f884"),
    ("src/covalent_ext/covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004.py", "46023c4c3fc221a3e87c513210079e6ef5909ed7c377c1b52dc564fcf171f978"),
)
PATH_DIGEST = "c541a32eb23ac4bc0e95f4778923b6d24f62cc8623c6b25992725c32eb66c233"
PAIR_DIGEST = "e40b85438e3f2068efd3747b050763a9ee9d98e92baebca928c20a3fcb9b2f4e"

CONTRACT_COLUMNS = (
    "contract_order", "contract_id", "contract_group", "contract_subject",
    "contract_value", "contract_status",
)
ROUTING_COLUMNS = (
    "matrix_order", "matrix_group", "case_id", "routing_condition",
    "envelope_representation", "lookup_count", "lookup_order",
    "candidate_key_access_count", "formal_call_count", "oracle_call_count",
    "identity_preserved", "expected_dispatch_code", "expected_reason",
    "expected_result_json", "case_passed",
)
TRUTH_COLUMNS = (
    "case_order", "case_id", "case_group", "routing_condition",
    "candidate_record_representation", "batch_context_representation",
    "evaluation_context_representation", "download_result_context_representation",
    "stage_authorization_context_representation", "evaluation_lookup_count",
    "download_lookup_count", "candidate_key_access_count", "lookup_order",
    "formal_call_count", "oracle_call_count", "source_exact10_json",
    "oracle_exact10_json", "projected_exact13_json", "identity_preserved",
    "expected_dispatch_code", "expected_reason", "case_passed",
)
SAFETY_COLUMNS = (
    "safety_order", "safety_item", "expected_executed",
    "observed_executed", "evidence", "safety_passed",
)
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity",
    "status", "blocking_scope", "blocking_reason", "issue_origin",
    "integration_transition", "issue_count",
)

TRUE_READINESS = (
    "admit_012_preconditions_audited",
    "admit_012_download_integrity_field_contract_frozen",
    "admit_012_field_semantics_complete",
    "admit_012_routing_responsibility_resolved",
    "admit_012_standalone_signature_frozen",
    "admit_012_formal_result_contract_frozen",
    "admit_012_standalone_evaluator_interface_implemented",
    "admit_012_rule_logic_implemented",
    "evaluate_admit_012_implemented",
    "Admit012EvaluationResult_implemented",
    "admit_012_unified_adapter_contract_frozen",
    "admit_012_exact10_to_exact13_projection_frozen",
    "admit_012_download_result_routing_contract_frozen",
    "ready_for_unified_dispatch_runtime_with_admit_001_to_012_implementation",
    "unified_dispatch_runtime_with_admit_001_to_011_implemented",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "admit_012_unified_adapter_implemented",
    "admit_012_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_012_implemented",
    "provider_mapping_validated", "real_provider_evaluation_ready",
    "ready_for_bulk_download_now", "combined_candidate_verdict_implemented",
    "ready_for_training", "step12d_is_final_training_feature_contract",
)

MANIFEST_KEYS = frozenset("""
Admit012EvaluationResult_implemented adapter_id admission_rule_id admission_rule_name
admit_012_download_integrity_field_contract_frozen admit_012_download_result_routing_contract_frozen
admit_012_exact10_to_exact13_projection_frozen admit_012_field_semantics_complete
admit_012_formal_result_contract_frozen admit_012_preconditions_audited admit_012_registered_in_engine
admit_012_routing_responsibility_resolved admit_012_rule_logic_implemented
admit_012_standalone_evaluator_interface_implemented admit_012_standalone_signature_frozen
admit_012_unified_adapter_contract_frozen admit_012_unified_adapter_implemented admit_013_implemented
all_checks_passed candidate_invalid_projection candidate_mapping_invalid_reason candidate_record_semantics
combined_candidate_verdict_implemented context_failure_dispatch_code context_failure_flags
context_routing_order context_routing_reasons contract_pass_count contract_row_count
coverage_issue_affected_rules coverage_issue_status cross_rule_aggregation_issue_status
current_registered_rule_order dispatch_error_codes dispatch_error_fields download_result_fields
evaluate_admit_012_implemented exact13_projection exact13_schema_widened existing_handler_identity_preserved
expected_base_commit expected_base_subject feature_semantics_audit_required_before_training
field_missing_contract formal_call_count_after_routing formal_evaluator formal_keyword_only formal_result_type
formal_exact105_formal_call_count formal_exact105_oracle_call_count formal_exact105_projection_count
future_adapter_handler future_adapter_handler_implemented future_registered_rule_order
historical_candidate_field_names_note independent_oracle independent_oracle_result_type
int_pair_allowed_in_exact13 issue_inventory_preserved_byte_identical issue_inventory_row_count
issue_inventory_sha256 known_not_registered_rule_ids_after_future known_rule_ids manifest_schema_version
oracle_call_count_after_source_validation oracle_exact_type_storage_validation outcome_vocabulary
output_file_count output_files output_sha256 output_sha256_excludes_manifest_self_hash policy_context_items
present_object_identity_preserved project projection_truth_formal_call_count projection_truth_matrix_group_counts
projection_truth_matrix_pass_count projection_truth_matrix_row_count projection_truth_oracle_call_count
provider_mapping_implemented provider_mapping_validated readiness ready_for_bulk_download_now ready_for_training
ready_for_unified_dispatch_runtime_with_admit_001_to_012_implementation real_download_executed
real_provider_evaluation_ready recommended_next_step result_fields result_schema_version routing_matrix_group_counts
routing_matrix_pass_count routing_matrix_row_count runtime_changed safety_pass_count safety_row_count
source_boundary_name source_exact10_full_invariant_validation source_exact_type_required source_input_count
source_input_paths source_input_sha256 source_input_verification source_invariant_invalid_reason
source_oracle_full_exact10_equality_required source_path_list_sha256 source_path_sha256_pairs_sha256
source_structural_checks_before_first_explicit_content_read source_type_invalid_reason stage standalone_result_fields
step step12d_is_final_training_feature_contract step12d_status string_projection_contract string_projection_function
unified_dispatch_runtime_with_admit_001_to_011_implemented
unified_dispatch_runtime_with_admit_001_to_012_implemented validation_failures
""".split())


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _git(*arguments: str) -> bytes:
    result = subprocess.run(
        ("git", *arguments), cwd=ROOT, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise AssertionError("source git command failed")
    return result.stdout


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
        raise AssertionError("resolved parent drift")


def _verify_sources() -> tuple[dict[str, Any], ...]:
    if len(SOURCE_BOUNDARY) != 19 or len({path for path, _ in SOURCE_BOUNDARY}) != 19:
        raise AssertionError("source Exact19")
    if _sha(json.dumps([path for path, _ in SOURCE_BOUNDARY], separators=(",", ":")).encode()) != PATH_DIGEST:
        raise AssertionError("source path digest")
    if _sha(json.dumps([[path, digest] for path, digest in SOURCE_BOUNDARY], separators=(",", ":")).encode()) != PAIR_DIGEST:
        raise AssertionError("source pair digest")
    if _git("show", "-s", "--format=%s", BASE).decode().rstrip("\n") != SUBJECT:
        raise AssertionError("base subject")
    _git("merge-base", "--is-ancestor", BASE, "HEAD")
    inspected = []
    for relative, expected in SOURCE_BOUNDARY:
        path = ROOT / relative
        if Path(relative).parts[:2] == ("data", "raw") or Path(relative).parts[0] == "checkpoints":
            raise AssertionError("protected source path")
        _parent_chain(path.parent, ROOT)
        item = os.lstat(path)
        identity = (item.st_dev, item.st_ino, item.st_mode)
        if not stat.S_ISREG(item.st_mode) or stat.S_ISLNK(item.st_mode) or path.resolve(strict=True) != path:
            raise AssertionError("source structure")
        if _git("ls-files", "--error-unmatch", "--", relative).decode() != f"{relative}\n":
            raise AssertionError("source tracked")
        tree = _git("ls-tree", BASE, "--", relative).splitlines()
        if len(tree) != 1 or b"\t" not in tree[0]:
            raise AssertionError("source base tree")
        metadata, tree_path = tree[0].split(b"\t", 1)
        parts = metadata.split()
        if tree_path.decode() != relative or len(parts) != 3 or parts[0] not in (b"100644", b"100755") or parts[1] != b"blob":
            raise AssertionError("source base blob/mode")
        inspected.append((relative, expected, path, identity, parts[0].decode()))
    rows = []
    for index, (relative, expected, path, identity, mode) in enumerate(inspected, 1):
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            item = os.fstat(descriptor)
            if (item.st_dev, item.st_ino, item.st_mode) != identity:
                raise AssertionError("source descriptor identity")
            chunks = []
            while True:
                chunk = os.read(descriptor, 1 << 16)
                if not chunk:
                    break
                chunks.append(chunk)
            item = os.fstat(descriptor)
            if (item.st_dev, item.st_ino, item.st_mode) != identity:
                raise AssertionError("source descriptor changed")
        finally:
            os.close(descriptor)
        filesystem = b"".join(chunks)
        base = _git("show", f"{BASE}:{relative}")
        if expected != _sha(filesystem) or expected != _sha(base):
            raise AssertionError("source SHA")
        rows.append({
            "source_order": index, "source_relative_path": relative,
            "expected_sha256": expected, "mode": mode, "content": filesystem,
        })
    return tuple(rows)


def _output_bytes(output_root: Path) -> dict[str, bytes]:
    root = Path(os.path.abspath(output_root))
    _parent_chain(root.parent, Path(root.anchor))
    root_item = os.lstat(root)
    root_identity = (root_item.st_dev, root_item.st_ino, root_item.st_mode)
    if not stat.S_ISDIR(root_item.st_mode) or stat.S_ISLNK(root_item.st_mode) or root.resolve(strict=True) != root:
        raise AssertionError("output root unsafe")
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        item = os.fstat(descriptor)
        if (item.st_dev, item.st_ino, item.st_mode) != root_identity:
            raise AssertionError("output root descriptor drift")
        if set(os.listdir(descriptor)) != set(OUTPUTS):
            raise AssertionError("output inventory")
        result = {}
        for name in OUTPUTS:
            item = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            identity = (item.st_dev, item.st_ino, item.st_mode)
            if not stat.S_ISREG(item.st_mode) or stat.S_ISLNK(item.st_mode):
                raise AssertionError("output leaf type")
            leaf = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=descriptor)
            try:
                current = os.fstat(leaf)
                if (current.st_dev, current.st_ino, current.st_mode) != identity:
                    raise AssertionError("output leaf descriptor drift")
                chunks = []
                while True:
                    chunk = os.read(leaf, 1 << 16)
                    if not chunk:
                        break
                    chunks.append(chunk)
                current = os.fstat(leaf)
                if (current.st_dev, current.st_ino, current.st_mode) != identity:
                    raise AssertionError("output leaf changed")
            finally:
                os.close(leaf)
            result[name] = b"".join(chunks)
        return result
    finally:
        os.close(descriptor)


def _csv(content: bytes, columns: Sequence[str]) -> tuple[dict[str, str], ...]:
    reader = csv.DictReader(io.StringIO(content.decode(), newline=""))
    if tuple(reader.fieldnames or ()) != tuple(columns):
        raise AssertionError("CSV schema")
    rows = tuple(dict(row) for row in reader)
    if any(tuple(row) != tuple(columns) or None in row.values() for row in rows):
        raise AssertionError("CSV row shape")
    return rows


def _candidate_invalid_json() -> str:
    value = {
        "schema_version": SCHEMA, "admission_rule_id": RULE_ID,
        "admission_rule_name": RULE_NAME, "outcome": "invalid", "passed": False,
        "blocks_candidate": True, "reason": CANDIDATE_REASON,
        "normalized_values": [], "validated_candidate_fields": [],
        "consumed_candidate_fields": [], "consumed_context_items": list(CONTEXT_ITEMS),
        "evaluator_io_used": False, "adapter_id": ADAPTER_ID,
    }
    if tuple(value) != RESULT_FIELDS:
        raise AssertionError("candidate Exact13 order")
    return json.dumps(value, separators=(",", ":"))


def _expected_contract_rows() -> tuple[dict[str, str], ...]:
    definitions = (
        ("identity", "rule", f"{RULE_ID}|{RULE_NAME}|{ADAPTER_ID}"),
        ("identity", "formal_evaluator", "evaluate_admit_012|Admit012EvaluationResult"),
        ("registry", "current_order", "|".join(CURRENT_ORDER)),
        ("registry", "future_order", "|".join(FUTURE_ORDER)),
        ("registry", "known_ids", "|".join(KNOWN_IDS)),
        ("routing", "five_envelopes", "candidate_record|batch_context|evaluation_context|download_result_context|stage_authorization_context"),
        ("routing", "precedence", "|".join(ROUTING_ORDER)),
        ("candidate", "mapping_only", "Mapping_envelope_only_zero_key_access"),
        ("candidate", "formal_source", "none"),
        ("candidate", "non_mapping_reason", CANDIDATE_REASON),
        ("batch", "required_value", "None"),
        ("stage", "required_value", "None"),
        ("evaluation", "mapping_and_ordered_keys", "|".join(CONTEXT_ITEMS)),
        ("download_result", "mapping_and_ordered_keys", "|".join(DOWNLOAD_FIELDS)),
        ("download_result", "missing", "omit_keyword_and_stop_later_lookup"),
        ("download_result", "private_sentinel", "not_imported_or_passed"),
        ("formal", "call", "keyword_only_exactly_once_after_routing"),
        ("formal", "identity", "all_present_fields_and_contexts_preserved"),
        ("oracle", "call", "same_kwargs_exactly_once_after_source_validation"),
        ("oracle", "result_type", "Admit012EvaluationResultContractDesign"),
        ("source", "exact10_fields", "|".join(SOURCE_FIELDS)),
        ("source", "validation", "exact_type_storage_order_types_reconstruction_reason_invariants"),
        ("source", "oracle_equality", "all_Exact10_values_and_types_equal"),
        ("projection", "exact13_fields", "|".join(RESULT_FIELDS)),
        ("projection", "canonical", "canonical_download_result_record_to_normalized_values"),
        ("projection", "validated", "validated_download_result_fields_to_historical_validated_candidate_fields"),
        ("projection", "consumed", "consumed_download_result_fields_to_historical_consumed_candidate_fields"),
        ("projection", "string_rule", "status_and_sha_exact_str_unchanged|http_and_content_exact_int_to_base10_ASCII_str"),
        ("projection", "strict_types", "bool_int_subclass_str_subclass_rejected"),
        ("projection", "no_schema_widening", "Exact13_string_pairs_only"),
        ("dispatch", "source_type", f"UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY|{SOURCE_TYPE_REASON}"),
        ("dispatch", "source_invariant", f"UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY|{SOURCE_INVARIANT_REASON}"),
        ("boundary", "runtime", "design_only_no_handler_registry_dispatcher_or_result_v2"),
        ("boundary", "admit_013", "not_implemented_or_judged"),
        ("boundary", "operations", "no_provider_raw_network_download_model_checkpoint_training"),
        ("training", "prerequisite", "feature_semantics_audit_required_Step12D_smoke_only"),
    )
    return tuple({
        "contract_order": str(index), "contract_id": f"CONTRACT_{index:03d}",
        "contract_group": group, "contract_subject": subject,
        "contract_value": value, "contract_status": "frozen",
    } for index, (group, subject, value) in enumerate(definitions, 1))


def _expected_routing_rows() -> tuple[dict[str, str], ...]:
    def spec(
        group: str, case: str, condition: str, envelope: str,
        lookups: Sequence[str] = (), candidate: int = 0, formal: int = 0,
        oracle: int = 0, identity: str = "n/a", code: str = "",
        reason: str = "", result: str = "",
    ) -> tuple[Any, ...]:
        return group, case, condition, envelope, tuple(lookups), candidate, formal, oracle, identity, code, reason, result

    error = "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID"
    cases = [
        spec("routing_failure", "batch_non_none", "batch_context non-None", "batch=object", code=error, reason=CONTEXT_REASONS["batch_context"]),
        spec("routing_failure", "evaluation_non_mapping", "evaluation_context non-Mapping", "evaluation=None", code=error, reason=CONTEXT_REASONS["evaluation_context"]),
    ]
    for index, name in enumerate(CONTEXT_ITEMS):
        cases.append(spec("routing_failure", f"evaluation_missing_{index + 1}", f"evaluation key missing: {name}", "evaluation=instrumented_mapping", CONTEXT_ITEMS[:index + 1], code=error, reason=CONTEXT_REASONS[name]))
    all_lookup = (*CONTEXT_ITEMS, *DOWNLOAD_FIELDS)
    cases.extend((
        spec("routing_failure", "download_non_mapping", "download_result_context non-Mapping", "download=None", CONTEXT_ITEMS, code=error, reason=CONTEXT_REASONS["download_result_context"]),
        spec("routing_failure", "stage_non_none", "stage_authorization_context non-None", "stage=object", CONTEXT_ITEMS, code=error, reason=CONTEXT_REASONS["stage_authorization_context"]),
        spec("candidate", "candidate_non_mapping", "candidate_record non-Mapping", "candidate=object", CONTEXT_ITEMS, reason=CANDIDATE_REASON, result=_candidate_invalid_json()),
        spec("candidate", "candidate_empty_mapping", "candidate empty Mapping", "candidate={}", all_lookup, formal=1, oracle=1, identity="true"),
        spec("candidate", "candidate_extra_fields", "candidate Mapping has unrelated keys", "candidate={extra:bomb}", all_lookup, formal=1, oracle=1, identity="true"),
        spec("candidate", "candidate_zero_key_access", "candidate access bomb", "candidate=instrumented_mapping", all_lookup, formal=1, oracle=1, identity="true"),
    ))
    for index, name in enumerate(DOWNLOAD_FIELDS):
        cases.append(spec("first_missing", f"first_missing_{index + 1}", f"first missing download key: {name}", "download=instrumented_mapping", (*CONTEXT_ITEMS, *DOWNLOAD_FIELDS[:index + 1]), formal=1, oracle=1, identity="true"))
    cases.extend((
        spec("first_missing", "empty_download_mapping", "all download keys absent", "download={}", (*CONTEXT_ITEMS, DOWNLOAD_FIELDS[0]), formal=1, oracle=1, identity="true"),
        spec("lookup", "present_none", "present None is not missing", "download status=None", all_lookup, formal=1, oracle=1, identity="true"),
        spec("lookup", "present_false", "present False is not missing", "download http=False", all_lookup, formal=1, oracle=1, identity="true"),
        spec("lookup", "present_zero", "present zero is not missing", "download content=0", all_lookup, formal=1, oracle=1, identity="true"),
        spec("lookup", "extra_download_key", "extra download key ignored", "download={Exact4,extra:bomb}", all_lookup, formal=1, oracle=1, identity="true"),
        spec("lookup", "identity_preserved", "present field/context objects forwarded", "identity_sentinels", all_lookup, formal=1, oracle=1, identity="true"),
        spec("call", "formal_once", "valid routing", "all_envelopes_valid", all_lookup, formal=1, oracle=1, identity="true"),
        spec("call", "oracle_once", "valid formal source", "all_envelopes_valid", all_lookup, formal=1, oracle=1, identity="true"),
        spec("call", "formal_exception", "formal raises", "all_envelopes_valid", all_lookup, formal=1, identity="true"),
        spec("source_failure", "formal_wrong_type", "formal returns object", "all_envelopes_valid", all_lookup, formal=1, identity="true", code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", reason=SOURCE_TYPE_REASON),
        spec("source_failure", "formal_storage_order", "formal storage order drift", "all_envelopes_valid", all_lookup, formal=1, identity="true", code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", reason=SOURCE_INVARIANT_REASON),
        spec("source_failure", "formal_top_level_type", "formal Exact10 top-level type drift", "all_envelopes_valid", all_lookup, formal=1, identity="true", code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", reason=SOURCE_INVARIANT_REASON),
        spec("source_failure", "formal_pair_type", "formal canonical pair type drift", "all_envelopes_valid", all_lookup, formal=1, identity="true", code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", reason=SOURCE_INVARIANT_REASON),
        spec("oracle_failure", "oracle_exception", "oracle raises", "all_envelopes_valid", all_lookup, formal=1, oracle=1, identity="true", code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", reason=SOURCE_INVARIANT_REASON),
        spec("oracle_failure", "oracle_wrong_type", "oracle exact type drift", "all_envelopes_valid", all_lookup, formal=1, oracle=1, identity="true", code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", reason=SOURCE_INVARIANT_REASON),
        spec("oracle_failure", "oracle_storage_order", "oracle storage order drift", "all_envelopes_valid", all_lookup, formal=1, oracle=1, identity="true", code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", reason=SOURCE_INVARIANT_REASON),
        spec("oracle_failure", "formal_oracle_mismatch", "full Exact10 mismatch", "all_envelopes_valid", all_lookup, formal=1, oracle=1, identity="true", code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", reason=SOURCE_INVARIANT_REASON),
        spec("projection", "full_success", "complete passed Exact10", "success|200|1|lower_sha", all_lookup, formal=1, oracle=1, identity="true"),
        spec("projection", "failure_status", "failure status remains passed", "failure|599|0|lower_sha", all_lookup, formal=1, oracle=1, identity="true"),
        spec("projection", "http_boundaries", "HTTP 100/200/404/599 canonical decimal", "http=100|200|404|599", all_lookup, formal=1, oracle=1, identity="true"),
        spec("projection", "content_values", "content 0/1/large canonical decimal", "content=0|1|large", all_lookup, formal=1, oracle=1, identity="true"),
        spec("projection", "validated_prefixes", "validated prefix lengths 0..4", "prefix=0|1|2|3|4", all_lookup, formal=1, oracle=1, identity="true"),
        spec("projection", "exact_string_pairs", "no int enters Exact13", "exact_string_pairs_only", all_lookup, formal=1, oracle=1, identity="true"),
        spec("registry", "current_exact11", "current order unchanged", "ADMIT_001..011"),
        spec("registry", "future_exact12", "future order frozen", "ADMIT_001..012"),
        spec("registry", "known_unregistered", "ADMIT_013..015 remain known unregistered", "ADMIT_013|ADMIT_014|ADMIT_015"),
        spec("registry", "handler_identity", "existing 11 handler identities unchanged", "identity_preserved", identity="true"),
    ))
    rows = []
    for index, value in enumerate(cases, 1):
        group, case, condition, envelope, lookups, candidate, formal, oracle_calls, identity, code, reason, result = value
        rows.append({
            "matrix_order": str(index), "matrix_group": group, "case_id": case,
            "routing_condition": condition, "envelope_representation": envelope,
            "lookup_count": str(len(lookups)), "lookup_order": "|".join(lookups),
            "candidate_key_access_count": str(candidate), "formal_call_count": str(formal),
            "oracle_call_count": str(oracle_calls), "identity_preserved": identity,
            "expected_dispatch_code": code, "expected_reason": reason,
            "expected_result_json": result, "case_passed": "true",
        })
    return tuple(rows)


def _expected_safety_rows() -> tuple[dict[str, str], ...]:
    positive = (
        ("production_design_only", "Design API and evidence builder only"),
        ("exact10_source_validation", "exact type/storage/order/types/reconstruction/invariants"),
        ("independent_oracle_equality", "full Exact10 types and values"),
        ("typed_to_string_projection", "exact int to canonical decimal str"),
        ("exact13_string_pair_enforcement", "both pair fields remain exact string pairs"),
        ("deterministic_materialization", "double build and set-atomic publish"),
        ("source_attestation", "fixed ordered Exact19 pinned reads"),
        ("issue_continuity", "standalone Exact16 byte-preserved"),
    )
    negative = (
        ("runtime_handler", "no future handler definition"),
        ("registry", "no registry definition or modification"),
        ("dispatcher", "no dispatcher definition or modification"),
        ("exact11_runtime_change", "committed source SHA frozen"),
        ("UnifiedAdmissionRuleEvaluation_redefinition", "Design suffix type only"),
        ("schema_widening", "no object/int pair allowance"),
        ("int_pair_in_exact13", "projection converts exact int"),
        ("private_standalone_sentinel", "not imported or passed"),
        ("candidate_field_sourcing", "candidate envelope only"),
        ("candidate_key_access", "zero"),
        ("batch_context_sourcing", "must be None"),
        ("stage_authorization_sourcing", "must be None"),
        ("network", "not imported or executed"),
        ("filesystem_in_adapter", "adapter Design path is pure memory"),
        ("raw_read_or_enumeration", "source boundary excludes data/raw"),
        ("provider_mapping", "not implemented or validated"),
        ("download", "not executed"),
        ("admit_013_judgment", "not implemented"),
        ("model_or_checkpoint", "not accessed or modified"),
        ("training", "no backward/optimizer/parameter update"),
        ("stage", "not executed"), ("commit", "not executed"),
        ("push", "not executed"),
    )
    pairs = (*((name, True, evidence) for name, evidence in positive), *((name, False, evidence) for name, evidence in negative))
    return tuple({
        "safety_order": str(index), "safety_item": name,
        "expected_executed": str(executed).lower(),
        "observed_executed": str(executed).lower(),
        "evidence": evidence, "safety_passed": "true",
    } for index, (name, executed, evidence) in enumerate(pairs, 1))


def _expected_adapter_truth_rows() -> tuple[dict[str, str], ...]:
    rows = []
    for offset, routing in enumerate(_expected_routing_rows(), 106):
        lookup_items = tuple(filter(None, routing["lookup_order"].split("|")))
        rows.append({
            "case_order": str(offset),
            "case_id": f"ADAPTER_{routing['case_id'].upper()}",
            "case_group": f"adapter_{routing['matrix_group']}",
            "routing_condition": routing["routing_condition"],
            "candidate_record_representation": "instrumented_mapping_or_declared_case",
            "batch_context_representation": "precedence_defined_by_case",
            "evaluation_context_representation": "instrumented_mapping_or_declared_case",
            "download_result_context_representation": routing["envelope_representation"],
            "stage_authorization_context_representation": "precedence_defined_by_case",
            "evaluation_lookup_count": str(sum(item in CONTEXT_ITEMS for item in lookup_items)),
            "download_lookup_count": str(sum(item in DOWNLOAD_FIELDS for item in lookup_items)),
            "candidate_key_access_count": routing["candidate_key_access_count"],
            "lookup_order": routing["lookup_order"],
            "formal_call_count": routing["formal_call_count"],
            "oracle_call_count": routing["oracle_call_count"],
            "source_exact10_json": "",
            "oracle_exact10_json": "",
            "projected_exact13_json": routing["expected_result_json"],
            "identity_preserved": routing["identity_preserved"],
            "expected_dispatch_code": routing["expected_dispatch_code"],
            "expected_reason": routing["expected_reason"],
            "case_passed": routing["case_passed"],
        })
    return tuple(rows)


class _Missing:
    __slots__ = ()


MISSING = _Missing()


class _StrSubclass(str):
    pass


class _IntSubclass(int):
    pass


class _TupleSubclass(tuple):
    pass


class _PairSubclass(tuple):
    pass


def _decode_token(text: str) -> object:
    if text == "<MISSING>":
        return MISSING
    if text == "<object>":
        return object()
    if text.startswith("<str-subclass:"):
        return _StrSubclass(ast.literal_eval(text[14:-1]))
    if text.startswith("<int-subclass:"):
        return _IntSubclass(ast.literal_eval(text[14:-1]))
    if text.startswith("<tuple-subclass:"):
        return _TupleSubclass(ast.literal_eval(text[16:-1]))
    if text.startswith("<tuple-member-str-subclass:"):
        prefix, representation = text[27:-1].split(":", 1)
        values = list(ast.literal_eval(representation))
        values[int(prefix)] = _StrSubclass(values[int(prefix)])
        return tuple(values)
    if text.startswith("<tuple-pair-subclass:"):
        prefix, representation = text[21:-1].split(":", 1)
        values = list(ast.literal_eval(representation))
        values[int(prefix)] = _PairSubclass(values[int(prefix)])
        return tuple(values)
    if text.startswith("<regex:"):
        return re.compile(ast.literal_eval(text[7:-1]))
    return ast.literal_eval(text)


def _validate_exact10(value: object, result_type: type) -> tuple[object, ...]:
    if type(value) is not result_type or tuple(field.name for field in fields(result_type)) != SOURCE_FIELDS:
        raise AssertionError("Exact10 type/order")
    storage = vars(value)
    if type(storage) is not dict or tuple(storage) != SOURCE_FIELDS:
        raise AssertionError("Exact10 storage")
    values = tuple(getattr(value, name) for name in SOURCE_FIELDS)
    types = (str, str, bool, bool, str, tuple, tuple, tuple, tuple, bool)
    if any(type(item) is not expected for item, expected in zip(values, types, strict=True)):
        raise AssertionError("Exact10 top-level type")
    if result_type(*values) != value or value.admission_rule_id != RULE_ID or value.evaluator_io_used is not False:
        raise AssertionError("Exact10 reconstruction/invariants")
    return values


def _project_pairs(value: object) -> tuple[tuple[str, str], ...]:
    if type(value) is not tuple or len(value) > 4:
        raise AssertionError("projection tuple")
    projected = []
    for index, pair in enumerate(value):
        if type(pair) is not tuple or len(pair) != 2 or type(pair[0]) is not str or pair[0] != DOWNLOAD_FIELDS[index]:
            raise AssertionError("projection pair")
        scalar = pair[1]
        if index in (0, 3):
            if type(scalar) is not str:
                raise AssertionError("projection exact str")
            encoded = scalar
        else:
            if type(scalar) is not int:
                raise AssertionError("projection exact int")
            encoded = str(scalar)
        projected.append((pair[0], encoded))
    return tuple(projected)


def _exact13_from_source(source: object) -> dict[str, object]:
    value = {
        "schema_version": SCHEMA,
        "admission_rule_id": source.admission_rule_id,
        "admission_rule_name": RULE_NAME,
        "outcome": source.outcome,
        "passed": source.passed,
        "blocks_candidate": source.blocks_candidate,
        "reason": source.reason,
        "normalized_values": _project_pairs(source.canonical_download_result_record),
        "validated_candidate_fields": _project_pairs(source.validated_download_result_fields),
        "consumed_candidate_fields": source.consumed_download_result_fields,
        "consumed_context_items": source.consumed_context_items,
        "evaluator_io_used": source.evaluator_io_used,
        "adapter_id": ADAPTER_ID,
    }
    if tuple(value) != RESULT_FIELDS:
        raise AssertionError("Exact13 order")
    return value


def _verify_truth(
    rows: tuple[dict[str, str], ...], source_rows: tuple[dict[str, Any], ...],
) -> None:
    standalone = importlib.import_module(
        "covalent_ext.covapie_bulk_download_admission_admit_012_rule_logic_interface"
    )
    oracle = importlib.import_module(
        "covalent_ext.covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_design_gate"
    )
    prior = _csv(source_rows[7]["content"], (
        "case_order", "case_id", "case_group", "assertion_kind",
        *(f"{name}_representation" for name in (*DOWNLOAD_FIELDS, *CONTEXT_ITEMS)),
        "expected_outcome", "expected_reason", "expected_canonical_download_result_record",
        "expected_validated_download_result_fields", "expected_consumed_download_result_fields",
        "expected_consumed_context_items", "expected_evaluator_io_used",
        "observed_design_result", "case_passed",
    ))
    expected_groups = {
        "context_validation": 39, "cross_phase_precedence": 6,
        "field52_admit_013_boundary": 3, "field52_canonical_valid": 9,
        "field52_content_invalid": 4, "field52_http_invalid": 5,
        "field52_missing": 6, "field52_multi_invalid_precedence": 7,
        "field52_sha_invalid": 12, "field52_status_invalid": 6,
        "result_invariant_negative": 8,
    }
    formal_rows = rows[:105]
    adapter_rows = rows[105:]
    if (
        len(rows) != 148 or len(prior) != 105
        or Counter(row["case_group"] for row in formal_rows) != expected_groups
        or adapter_rows != _expected_adapter_truth_rows()
    ):
        raise AssertionError("Exact105 groups")
    representation_columns = tuple(
        f"{name}_representation" for name in (*DOWNLOAD_FIELDS, *CONTEXT_ITEMS)
    )
    for observed, truth in zip(formal_rows, prior, strict=True):
        decoded = tuple(_decode_token(truth[column]) for column in representation_columns)
        field_kwargs: dict[str, object] = {}
        download_lookups = 0
        for name, value in zip(DOWNLOAD_FIELDS, decoded[:4], strict=True):
            download_lookups += 1
            if value is MISSING:
                break
            field_kwargs[name] = value
        context_kwargs = dict(zip(CONTEXT_ITEMS, decoded[4:], strict=True))
        source = standalone.evaluate_admit_012(**field_kwargs, **context_kwargs)
        classification = oracle.classify_admit_012_formal_evaluator_interface_design(
            **field_kwargs, **context_kwargs
        )
        source_values = _validate_exact10(source, standalone.Admit012EvaluationResult)
        oracle_values = _validate_exact10(
            classification, oracle.Admit012EvaluationResultContractDesign
        )
        if any(type(left) is not type(right) or left != right for left, right in zip(source_values, oracle_values, strict=True)):
            raise AssertionError("full Exact10 equality")
        source_json = json.loads(observed["source_exact10_json"])
        oracle_json = json.loads(observed["oracle_exact10_json"])
        projected_json = json.loads(observed["projected_exact13_json"])
        expected_source = json.loads(json.dumps(dict(zip(SOURCE_FIELDS, source_values, strict=True))))
        expected_projection = json.loads(json.dumps(_exact13_from_source(source)))
        evaluation_repr = "|".join(f"{name}={truth[f'{name}_representation']}" for name in CONTEXT_ITEMS)
        download_repr = "|".join(f"{name}={truth[f'{name}_representation']}" for name in DOWNLOAD_FIELDS)
        lookup_order = "|".join((*CONTEXT_ITEMS, *DOWNLOAD_FIELDS[:download_lookups]))
        expected_metadata = {
            "case_order": truth["case_order"], "case_id": truth["case_id"],
            "case_group": truth["case_group"],
            "routing_condition": "formal_Exact105_projection",
            "candidate_record_representation": "{}",
            "batch_context_representation": "None",
            "evaluation_context_representation": evaluation_repr,
            "download_result_context_representation": download_repr,
            "stage_authorization_context_representation": "None",
            "evaluation_lookup_count": "4", "download_lookup_count": str(download_lookups),
            "candidate_key_access_count": "0", "lookup_order": lookup_order,
            "formal_call_count": "1", "oracle_call_count": "1",
            "identity_preserved": "true", "expected_dispatch_code": "",
            "expected_reason": source.reason, "case_passed": "true",
        }
        if any(observed[key] != value for key, value in expected_metadata.items()):
            raise AssertionError("truth metadata")
        if source_json != expected_source or oracle_json != expected_source or projected_json != expected_projection:
            raise AssertionError("truth Exact10/Exact13")
        for field_name, field_value in (*projected_json["normalized_values"], *projected_json["validated_candidate_fields"]):
            if type(field_name) is not str or type(field_value) is not str:
                raise AssertionError("Exact13 non-string pair")


def _verify_design_ast() -> None:
    path = ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_012_unified_adapter_contract_design_gate.py"
    tree = ast.parse(path.read_bytes())
    functions = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    classes = {node.name for node in tree.body if isinstance(node, ast.ClassDef)}
    assignments = {
        target.id for node in tree.body if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in ((node.targets if isinstance(node, ast.Assign) else (node.target,)))
        if isinstance(target, ast.Name)
    }
    forbidden = {"_evaluate_registered_admit_012", "evaluate_admission_rule", "EVALUATOR_REGISTRY", "RULE_NAMES", "ADAPTER_IDS", "UnifiedAdmissionRuleEvaluation"}
    if forbidden & (functions | classes | assignments):
        raise AssertionError("runtime implementation leaked")
    if any(isinstance(node, ast.Name) and node.id == "_MISSING" for node in ast.walk(tree)):
        raise AssertionError("private standalone sentinel referenced")


def _verify_manifest(
    manifest: dict[str, Any], hashes: Mapping[str, str],
    source_rows: tuple[dict[str, Any], ...],
) -> None:
    if set(manifest) != MANIFEST_KEYS:
        raise AssertionError("manifest exact keyset")
    scalars = {
        "project": "CovaPIE", "step": "ADMIT_012 unified adapter contract design gate v1",
        "stage": STAGE, "manifest_schema_version": "covapie_admit_012_unified_adapter_contract_manifest_v1",
        "expected_base_commit": BASE, "expected_base_subject": SUBJECT,
        "admission_rule_id": RULE_ID, "admission_rule_name": RULE_NAME,
        "adapter_id": ADAPTER_ID, "formal_evaluator": "evaluate_admit_012",
        "formal_result_type": "Admit012EvaluationResult",
        "future_adapter_handler": "_evaluate_registered_admit_012",
        "future_adapter_handler_implemented": False,
        "independent_oracle": "classify_admit_012_formal_evaluator_interface_design",
        "independent_oracle_result_type": "Admit012EvaluationResultContractDesign",
        "candidate_record_semantics": "Mapping envelope validation only; zero candidate key access",
        "source_input_count": 19, "source_boundary_name": "fixed_ordered_exact19_committed_source_boundary",
        "source_path_list_sha256": PATH_DIGEST,
        "source_path_sha256_pairs_sha256": PAIR_DIGEST,
        "output_file_count": 6, "contract_row_count": 36, "contract_pass_count": 36,
        "routing_matrix_row_count": 43, "routing_matrix_pass_count": 43,
        "projection_truth_matrix_row_count": 148, "projection_truth_matrix_pass_count": 148,
        "formal_exact105_projection_count": 105,
        "formal_exact105_formal_call_count": 105,
        "formal_exact105_oracle_call_count": 105,
        "projection_truth_formal_call_count": 135,
        "projection_truth_oracle_call_count": 130,
        "safety_row_count": 31, "safety_pass_count": 31,
        "issue_inventory_row_count": 16,
        "issue_inventory_preserved_byte_identical": True,
        "issue_inventory_sha256": SOURCE_BOUNDARY[3][1],
        "coverage_issue_status": "open",
        "coverage_issue_affected_rules": "ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015",
        "cross_rule_aggregation_issue_status": "open",
        "recommended_next_step": "implement_covapie_unified_dispatch_runtime_with_admit_001_to_012_v1",
        "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "admit_013_implemented": False, "provider_mapping_implemented": False,
        "real_download_executed": False, "runtime_changed": False,
        "all_checks_passed": True,
    }
    if any(manifest.get(key) != value for key, value in scalars.items()):
        raise AssertionError("manifest scalar")
    lists = {
        "download_result_fields": list(DOWNLOAD_FIELDS),
        "policy_context_items": list(CONTEXT_ITEMS),
        "current_registered_rule_order": list(CURRENT_ORDER),
        "future_registered_rule_order": list(FUTURE_ORDER),
        "known_rule_ids": list(KNOWN_IDS),
        "known_not_registered_rule_ids_after_future": list(KNOWN_IDS[12:]),
        "result_fields": list(RESULT_FIELDS), "standalone_result_fields": list(SOURCE_FIELDS),
        "dispatch_error_fields": list(ERROR_FIELDS), "dispatch_error_codes": list(ERROR_CODES),
        "outcome_vocabulary": list(OUTCOMES), "context_routing_order": list(ROUTING_ORDER),
        "output_files": list(OUTPUTS), "source_input_paths": [path for path, _ in SOURCE_BOUNDARY],
    }
    if any(manifest.get(key) != value for key, value in lists.items()):
        raise AssertionError("manifest ordered contract")
    readiness = {**{key: True for key in TRUE_READINESS}, **{key: False for key in FALSE_READINESS}}
    if manifest.get("readiness") != readiness or any(manifest.get(key) is not value for key, value in readiness.items()):
        raise AssertionError("manifest readiness")
    if manifest.get("source_input_sha256") != dict(SOURCE_BOUNDARY):
        raise AssertionError("manifest source hashes")
    verification = [{
        "source_order": index, "source_relative_path": relative,
        "tracked": True, "base_tree_blob": True, "base_tree_mode": source_rows[index - 1]["mode"],
        "filesystem_regular": True, "non_symlink": True,
        "parent_chain_non_symlink": True, "safe_descendant": True,
        "pinned_fd_read": True, "expected_sha256": expected,
        "base_tree_sha256": expected, "filesystem_sha256": expected,
        "source_verified": True,
    } for index, (relative, expected) in enumerate(SOURCE_BOUNDARY, 1)]
    if manifest.get("source_input_verification") != verification:
        raise AssertionError("manifest source verification")
    semantic = {
        "existing_handler_identity_preserved": True,
        "context_routing_reasons": CONTEXT_REASONS,
        "context_failure_dispatch_code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        "context_failure_flags": {"known_rule": True, "callable_discovered": True, "adapter_ready": True},
        "candidate_mapping_invalid_reason": CANDIDATE_REASON,
        "candidate_invalid_projection": {
            "outcome": "invalid", "passed": False, "blocks_candidate": True,
            "normalized_values": [], "validated_candidate_fields": [],
            "consumed_candidate_fields": [], "consumed_context_items": list(CONTEXT_ITEMS),
            "evaluator_io_used": False, "adapter_id": ADAPTER_ID,
        },
        "field_missing_contract": "omit missing keyword; stop later lookup; no private sentinel",
        "formal_keyword_only": True, "formal_call_count_after_routing": 1,
        "oracle_call_count_after_source_validation": 1,
        "present_object_identity_preserved": True,
        "source_exact_type_required": True, "source_exact10_full_invariant_validation": True,
        "source_type_invalid_reason": SOURCE_TYPE_REASON,
        "source_invariant_invalid_reason": SOURCE_INVARIANT_REASON,
        "oracle_exact_type_storage_validation": True,
        "source_oracle_full_exact10_equality_required": True,
        "string_projection_function": "project_download_result_pairs_to_exact_string_pairs",
        "string_projection_contract": {
            "download_result_status": "exact str unchanged",
            "observed_http_status": "exact int to canonical base-10 ASCII str(value)",
            "observed_content_length_bytes": "exact int to canonical base-10 ASCII str(value)",
            "observed_sha256": "exact str unchanged",
        },
        "exact13_projection": {
            "normalized_values": "string-project(source.canonical_download_result_record)",
            "validated_candidate_fields": "string-project(source.validated_download_result_fields)",
            "consumed_candidate_fields": "source.consumed_download_result_fields",
            "consumed_context_items": "source.consumed_context_items",
        },
        "historical_candidate_field_names_note": "validated_candidate_fields and consumed_candidate_fields carry download-result semantics for ADMIT_012 and do not imply candidate_record sourcing",
        "exact13_schema_widened": False, "int_pair_allowed_in_exact13": False,
        "routing_matrix_group_counts": {"call": 3, "candidate": 4, "first_missing": 5, "lookup": 5, "oracle_failure": 4, "projection": 6, "registry": 4, "routing_failure": 8, "source_failure": 4},
        "projection_truth_matrix_group_counts": {"adapter_call": 3, "adapter_candidate": 4, "adapter_first_missing": 5, "adapter_lookup": 5, "adapter_oracle_failure": 4, "adapter_projection": 6, "adapter_registry": 4, "adapter_routing_failure": 8, "adapter_source_failure": 4, "context_validation": 39, "cross_phase_precedence": 6, "field52_admit_013_boundary": 3, "field52_canonical_valid": 9, "field52_content_invalid": 4, "field52_http_invalid": 5, "field52_missing": 6, "field52_multi_invalid_precedence": 7, "field52_sha_invalid": 12, "field52_status_invalid": 6, "result_invariant_negative": 8},
        "source_structural_checks_before_first_explicit_content_read": True,
        "output_sha256_excludes_manifest_self_hash": True,
        "validation_failures": [],
    }
    if any(manifest.get(key) != value for key, value in semantic.items()):
        raise AssertionError("manifest semantic contract")
    if manifest.get("output_sha256") != {name: hashes[name] for name in OUTPUTS[:-1]}:
        raise AssertionError("manifest output SHA")


def _validate_output_tree(
    output_root: Path = OUTPUT_ROOT, *, enforce_frozen_hashes: bool = True,
) -> dict[str, str]:
    source_rows = _verify_sources()
    contents = _output_bytes(output_root)
    hashes = {name: _sha(content) for name, content in contents.items()}
    contract = _csv(contents[OUTPUTS[0]], CONTRACT_COLUMNS)
    routing = _csv(contents[OUTPUTS[1]], ROUTING_COLUMNS)
    truth = _csv(contents[OUTPUTS[2]], TRUTH_COLUMNS)
    safety = _csv(contents[OUTPUTS[3]], SAFETY_COLUMNS)
    issues = _csv(contents[OUTPUTS[4]], ISSUE_COLUMNS)
    if contract != _expected_contract_rows() or len(contract) != 36:
        raise AssertionError("Exact36 contract complete equality")
    if routing != _expected_routing_rows() or len(routing) != 43:
        raise AssertionError("Exact43 routing complete equality")
    if safety != _expected_safety_rows() or len(safety) != 31:
        raise AssertionError("Exact31 safety complete equality")
    _verify_truth(truth, source_rows)
    if contents[OUTPUTS[4]] != source_rows[3]["content"] or len(issues) != 16:
        raise AssertionError("Exact16 issue byte continuity")
    issue_map = {row["issue_id"]: row for row in issues}
    resolved = {
        "DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED",
        "DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED",
        "ADMIT_012_PRESENCE_SEMANTICS_UNRESOLVED",
        "ADMIT_012_MULTI_INVALID_PRECEDENCE_UNRESOLVED",
        "ADMIT_012_POST_DOWNLOAD_ROUTING_RESPONSIBILITY_UNRESOLVED",
        "ADMIT_012_STANDALONE_SIGNATURE_UNRESOLVED",
        "ADMIT_012_RESULT_CONTRACT_UNRESOLVED",
    }
    if any(issue_map[name]["status"] != "resolved" for name in resolved):
        raise AssertionError("resolved issue regression")
    if issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] != "ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015" or issue_map["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["status"] != "open":
        raise AssertionError("open issue continuity")
    manifest = json.loads(contents[OUTPUTS[5]])
    if type(manifest) is not dict:
        raise AssertionError("manifest root")
    _verify_manifest(manifest, hashes, source_rows)
    if enforce_frozen_hashes and hashes != FROZEN_OUTPUT_SHA256:
        raise AssertionError("frozen output hashes")
    return hashes


def main() -> int:
    _verify_design_ast()
    before = _output_bytes(OUTPUT_ROOT)
    module = importlib.import_module(MODULE)
    if _output_bytes(OUTPUT_ROOT) != before:
        raise AssertionError("production import side effect")
    runtime = importlib.import_module(
        "covalent_ext.covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011"
    )
    original = importlib.import_module(
        "covalent_ext.covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004"
    )
    if (
        tuple(runtime.EVALUATOR_REGISTRY) != CURRENT_ORDER
        or runtime.UnifiedAdmissionRuleEvaluation is not original.UnifiedAdmissionRuleEvaluation
        or runtime.UnifiedAdmissionDispatchError is not original.UnifiedAdmissionDispatchError
        or runtime.RESULT_FIELDS != RESULT_FIELDS
    ):
        raise AssertionError("Exact11 runtime/object identity")
    hashes = _validate_output_tree()
    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        first_root, second_root = Path(first) / "set", Path(second) / "set"
        module.run_covapie_bulk_download_admission_admit_012_unified_adapter_contract_design_gate_v1(first_root, repo_root=ROOT)
        module.run_covapie_bulk_download_admission_admit_012_unified_adapter_contract_design_gate_v1(second_root, repo_root=ROOT)
        if _output_bytes(first_root) != _output_bytes(second_root) or _output_bytes(first_root) != before:
            raise AssertionError("deterministic double materialization")
        _validate_output_tree(first_root, enforce_frozen_hashes=False)
    print(json.dumps({"checked": True, "output_sha256": hashes}, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
