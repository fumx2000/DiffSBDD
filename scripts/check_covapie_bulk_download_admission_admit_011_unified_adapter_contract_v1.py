#!/usr/bin/env python3
"""Independent checker for the ADMIT_011 unified-adapter design gate."""
from __future__ import annotations

import ast
import csv
import hashlib
import importlib
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import fields
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
MODULE = "covalent_ext.covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate"
BASE = "da7367cfdcf54bff8c30e05ba6f7d16cc5dbda2e"
SUBJECT = "add CovaPIE ADMIT_011 standalone evaluator interface v1"
STAGE = "covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1"
OUTPUT_ROOT = ROOT / "data/derived/covalent_small" / STAGE
RULE_ID = "ADMIT_011"
RULE_NAME = "raw_overwrite_forbidden"
ADAPTER_ID = "covapie_admit_011_unified_adapter_v1"
SCHEMA = "covapie_unified_admission_rule_evaluation_v1"
CURRENT_ORDER = tuple(f"ADMIT_{index:03d}" for index in range(1, 11))
FUTURE_ORDER = (*CURRENT_ORDER, RULE_ID)
KNOWN_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
CANDIDATE_FIELDS = ("raw_target_relative_path",)
CONTEXT_ITEMS = ("raw_target_relative_path_contract", "existing_raw_target_relative_paths")
SOURCE_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_raw_target_relative_path", "validated_candidate_fields",
    "consumed_candidate_fields", "consumed_context_items", "evaluator_io_used",
)
RESULT_FIELDS = (
    "schema_version", "admission_rule_id", "admission_rule_name", "outcome", "passed",
    "blocks_candidate", "reason", "normalized_values", "validated_candidate_fields",
    "consumed_candidate_fields", "consumed_context_items", "evaluator_io_used", "adapter_id",
)
ERROR_FIELDS = ("code", "admission_rule_id", "known_rule", "callable_discovered", "adapter_ready", "reason")
ERROR_CODES = (
    "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", "UNIFIED_ADMISSION_RULE_ID_UNKNOWN",
    "UNIFIED_ADMISSION_RULE_NOT_REGISTERED", "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
    "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
)
OUTCOMES = ("passed", "blocked", "invalid", "rejected")
ROUTING_ORDER = (
    "batch_context_must_be_none", "evaluation_context_mapping_validation",
    "raw_target_relative_path_contract_required_key_lookup",
    "existing_raw_target_relative_paths_required_key_lookup",
    "download_result_context_must_be_none", "stage_authorization_context_must_be_none",
    "candidate_record_mapping_validation", "raw_target_relative_path_required_key_lookup",
    "formal_evaluator", "standalone_source_validation", "independent_oracle",
    "full_exact10_equality", "exact13_projection",
)
CONTEXT_REASONS = {
    "batch_context": "ADMIT_011_BATCH_CONTEXT_MUST_BE_NONE",
    "evaluation_context": "ADMIT_011_EVALUATION_CONTEXT_MAPPING_REQUIRED",
    "contract_key": "ADMIT_011_RAW_TARGET_RELATIVE_PATH_CONTRACT_REQUIRED",
    "snapshot_key": "ADMIT_011_EXISTING_RAW_TARGET_RELATIVE_PATHS_REQUIRED",
    "download_result_context": "ADMIT_011_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
    "stage_authorization_context": "ADMIT_011_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
}
CANDIDATE_REASON = "ADMIT_011_CANDIDATE_RECORD_MAPPING_INVALID"
MISSING_REASON = "raw_target_relative_path_missing"
SOURCE_TYPE_REASON = "ADMIT_011_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
SOURCE_INVARIANT_REASON = "ADMIT_011_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
OUTPUTS = (
    "covapie_admit_011_unified_adapter_contract.csv",
    "covapie_admit_011_candidate_projection_and_context_routing_matrix.csv",
    "covapie_admit_011_unified_result_projection_truth_matrix.csv",
    "covapie_admit_011_unified_adapter_safety_audit.csv",
    "covapie_admit_011_unified_adapter_issue_readiness_inventory.csv",
    "covapie_admit_011_unified_adapter_contract_manifest.json",
)
FROZEN_OUTPUT_SHA256 = {
    "covapie_admit_011_candidate_projection_and_context_routing_matrix.csv": "be12ce9e9c551f5891cac9840d130dd9feabfb99fe849385db08dcf767486845",
    "covapie_admit_011_unified_adapter_contract.csv": "4b4b41295364fcb83f807c054e2e561ca2c4a31fbf27fd55d04607f3c127c2cc",
    "covapie_admit_011_unified_adapter_contract_manifest.json": "d5ad2622b5182898c418d774e4c0deb33fc2fb643caaa5da0507cabb3824f884",
    "covapie_admit_011_unified_adapter_issue_readiness_inventory.csv": "eb36931b833800c4a7c9dffa33a690c4197ba0bb161cfbda742b90c3b3d8d1c0",
    "covapie_admit_011_unified_adapter_safety_audit.csv": "8c1cfae97131a7b76acc2c1b92381359d458c0ef9640ca3870975bf1724759bc",
    "covapie_admit_011_unified_result_projection_truth_matrix.csv": "deb4b71376a27d00317d9255e822c9e534c39fc16f0a6636dc149a6ca205b01a",
}
SOURCE_BOUNDARY = (
    ("src/covalent_ext/covapie_bulk_download_admission_admit_011_rule_logic_interface.py", "73adad5c617ecae0dc5772d04ae5d777970a3d2a8c8963c3d2c4c4b19cbf85fc"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_contract.csv", "7624bfda25b7aca2a3db11fab18a883c52dee0e598a295ada0b0676a1847aea2"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_truth_matrix.csv", "974bc68fdd8c6d8c500cce3f70970bd16d18f07d49d7e4162776bd62cd0e064b"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_source_boundary_audit.csv", "096f0016610a428a39aa63c071e145c8f78051a8cf500510057a0712638904b6"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_purity_audit.csv", "e4f6df108d51188e87ac0d7d0de9363b82cd22f18f0b2f97a79e0fd448f4a93e"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_issue_readiness_inventory.csv", "eb36931b833800c4a7c9dffa33a690c4197ba0bb161cfbda742b90c3b3d8d1c0"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_rule_logic_interface_v1/covapie_admit_011_rule_logic_interface_manifest.json", "a3c053d7b4af149b67b818721f11bb6920b5de00d5d15fb5ec176e10e5a70c3c"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate.py", "c515afab9ac6dc4390d9ef0bf385de4261c612bb1cbe67a19b008c40c288cd7d"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1/covapie_admit_011_raw_target_relative_path_contract_manifest.json", "9718090b212e3338bddef1fb7d6fb62e39d95e1911fe5bdd0ff6613b364e8bf4"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_v1/covapie_admit_011_raw_target_relative_path_grammar_truth_matrix.csv", "1b32c3cc658433da18b804336afec8c63a275bcf44f68556faf75804e3b386ca"),
    ("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010.py", "b613321aa1563c7c559208fc08cf82d1e2ccee07cdc6b9c8c338d87b14c78436"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1/covapie_admit_001_to_010_runtime_manifest.json", "46dcef1d5e62c5a8904e9ff66b145b6ee9dae88fc406e42d669a8a7002285198"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate.py", "dd2f88da8024d75d9b4fd9f1b8698a402c3395ebbfca6c9f17b0e19b84bb5095"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate_v1/covapie_admit_010_unified_adapter_contract_manifest.json", "6ee42e0baf26ece28df75201521babdf8f9ffe7a89b7544a346f92e5ecd39119"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate.py", "9fc1ca277220da3dd982e72c4198e74af911d4cc9d4df39e4864cb8ea0fe1c30"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate_v1/covapie_admit_009_unified_adapter_contract_manifest.json", "efe1da7f804a411028903a3a6fc498eb2f0cc5f2b0823b81b5aab3acd83d53c1"),
)
CONTRACT_COLUMNS = ("contract_order", "contract_id", "contract_group", "contract_subject", "contract_value", "contract_status")
ROUTING_COLUMNS = ("matrix_order", "matrix_group", "case_id", "condition", "expected_behavior", "expected_reason", "expected_result_json", "formal_call_count", "oracle_call_count", "candidate_access_status", "required_lookup_count", "identity_preserved", "case_passed")
TRUTH_COLUMNS = ("case_id", "case_group", "behavior", "expected_dispatch_code", "expected_reason", "source_exact10_json", "oracle_exact10_json", "unified_exact13_json", "formal_call_count", "oracle_call_count", "case_passed")
SAFETY_COLUMNS = ("safety_item", "expected_executed", "observed_executed", "safety_passed")
ISSUE_COLUMNS = ("issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status", "blocking_scope", "blocking_reason", "issue_origin", "integration_transition", "issue_count")
TRUE_READINESS = (
    "admit_011_rule_logic_implemented", "admit_011_standalone_interface_frozen",
    "admit_011_unified_adapter_contract_frozen", "candidate_projection_contract_frozen",
    "context_routing_contract_frozen", "standalone_source_validation_contract_frozen",
    "independent_oracle_equivalence_contract_frozen", "exact10_to_exact13_projection_frozen",
    "future_registered_rule_order_frozen", "ready_for_unified_dispatch_runtime_with_admit_001_to_011_implementation",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "admit_011_runtime_adapter_implemented", "admit_011_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_011_implemented", "provider_mapping_validated",
    "real_provider_evaluation_ready", "combined_candidate_verdict_implemented",
    "ready_for_bulk_download_now", "checkpoint_compatibility_validated",
    "full_repository_canonical_validated", "ready_for_training",
)
MANIFEST_KEYS = frozenset("""
adapter_id adapter_side_normalization adapter_side_path_repair_or_resolution admission_rule_id
admission_rule_name admit_011_registered_in_engine admit_011_rule_logic_implemented
admit_011_runtime_adapter_implemented admit_011_standalone_interface_frozen
admit_011_unified_adapter_contract_frozen all_checks_passed candidate_fields
candidate_invalid_projection candidate_mapping_invalid_reason candidate_missing_reason
candidate_projection_contract_frozen checkpoint_compatibility_validated
combined_candidate_verdict_implemented context_failure_dispatch_code context_failure_flags
context_items context_routing_contract_frozen context_routing_order context_routing_reasons
contract_pass_count contract_row_count coverage_issue_affected_rules coverage_issue_status
cross_rule_aggregation_issue_status current_registered_rule_order dispatch_error_codes
dispatch_error_fields exact10_to_exact13_projection_frozen expected_base_commit expected_base_subject
feature_semantics_audit_required_before_training formal_call_count_after_candidate_gate
formal_evaluator formal_positional_argument_order formal_result_type full_repository_canonical_validated
future_adapter_handler future_registered_rule_order future_registered_rule_order_frozen
independent_oracle independent_oracle_equivalence_contract_frozen independent_oracle_result_type
issue_inventory_preserved_byte_identical issue_inventory_row_count issue_inventory_sha256
known_not_registered_rule_ids known_rule_ids manifest_schema_version normalized_values_projection
oracle_call_count_after_source_validation oracle_exact_type_required original_object_identity_preserved
outcome_vocabulary output_file_count output_files output_sha256 output_sha256_excludes_manifest_self_hash
project projection_truth_matrix_group_counts projection_truth_matrix_historical_count
projection_truth_matrix_pass_count projection_truth_matrix_row_count provider_mapping_validated
raw_target_context_issue_status readiness ready_for_bulk_download_now ready_for_training
ready_for_unified_dispatch_runtime_with_admit_001_to_011_implementation real_provider_evaluation_ready
recommended_next_step required_lookup_counts result_fields result_schema_version
routing_matrix_group_counts routing_matrix_pass_count routing_matrix_row_count safety_pass_count
safety_row_count source_boundary_name source_exact10_full_invariant_validation source_exact_type_required
source_input_count source_input_paths source_input_sha256 source_input_verification
source_invariant_invalid_reason source_oracle_full_exact10_equality_required
source_structural_checks_before_first_explicit_content_read source_type_invalid_reason stage
standalone_result_fields standalone_source_validation_contract_frozen step
step12d_is_final_training_feature_contract step12d_status stop_boundaries
unified_dispatch_runtime_with_admit_001_to_011_implemented validation_failures
""".split())


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _git(*arguments: str) -> bytes:
    result = subprocess.run(("git", *arguments), cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
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
    if _git("show", "-s", "--format=%s", BASE).decode().rstrip("\n") != SUBJECT:
        raise AssertionError("base subject")
    _git("merge-base", "--is-ancestor", BASE, "HEAD")
    inspected = []
    for relative, expected in SOURCE_BOUNDARY:
        path = ROOT / relative
        _parent_chain(path.parent, ROOT)
        item = os.lstat(path)
        if not stat.S_ISREG(item.st_mode) or stat.S_ISLNK(item.st_mode) or path.resolve(strict=True) != path:
            raise AssertionError("source structure")
        if _git("ls-files", "--error-unmatch", "--", relative).decode() != f"{relative}\n":
            raise AssertionError("source tracked")
        tree = _git("ls-tree", BASE, "--", relative).splitlines()
        if len(tree) != 1 or tree[0].split(maxsplit=2)[:2] not in ([b"100644", b"blob"], [b"100755", b"blob"]):
            raise AssertionError("source base blob")
        inspected.append((relative, expected, path, (item.st_dev, item.st_ino, item.st_mode)))
    rows = []
    for index, (relative, expected, path, identity) in enumerate(inspected, 1):
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            if (os.fstat(descriptor).st_dev, os.fstat(descriptor).st_ino, os.fstat(descriptor).st_mode) != identity:
                raise AssertionError("source descriptor identity")
            chunks = []
            while True:
                chunk = os.read(descriptor, 1 << 16)
                if not chunk:
                    break
                chunks.append(chunk)
        finally:
            os.close(descriptor)
        filesystem = b"".join(chunks)
        base = _git("show", f"{BASE}:{relative}")
        if expected != _sha(filesystem) or expected != _sha(base):
            raise AssertionError("source SHA")
        rows.append({"source_order": index, "source_relative_path": relative, "expected_sha256": expected, "content": filesystem})
    return tuple(rows)


def _output_bytes(output_root: Path) -> dict[str, bytes]:
    root = Path(os.path.abspath(output_root))
    _parent_chain(root.parent, Path(root.anchor))
    root_item = os.lstat(root)
    if not stat.S_ISDIR(root_item.st_mode) or stat.S_ISLNK(root_item.st_mode) or root.resolve(strict=True) != root:
        raise AssertionError("output root unsafe")
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        if set(os.listdir(descriptor)) != set(OUTPUTS):
            raise AssertionError("output inventory")
        result = {}
        for name in OUTPUTS:
            item = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            if not stat.S_ISREG(item.st_mode) or stat.S_ISLNK(item.st_mode):
                raise AssertionError("output leaf type")
            leaf = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=descriptor)
            try:
                chunks = []
                while True:
                    chunk = os.read(leaf, 1 << 16)
                    if not chunk:
                        break
                    chunks.append(chunk)
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


def _literal_registry_keys(source: bytes) -> tuple[str, ...]:
    tree = ast.parse(source.decode())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "EVALUATOR_REGISTRY" for target in node.targets):
            value = node.value.args[0] if isinstance(node.value, ast.Call) and node.value.args else node.value
            if isinstance(value, ast.Dict):
                return tuple(key.value for key in value.keys if isinstance(key, ast.Constant))
    raise AssertionError("runtime registry missing")


def _verify_design_ast() -> None:
    source = (ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate.py").read_text()
    tree = ast.parse(source)
    functions = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assignments = {target.id for node in tree.body if isinstance(node, ast.Assign) for target in node.targets if isinstance(target, ast.Name)}
    if {"_evaluate_registered_admit_011", "evaluate_admission_rule"} & (functions | assignments) or "EVALUATOR_REGISTRY" in assignments:
        raise AssertionError("runtime implementation leaked into design gate")


def _validate_source_object(value: object, result_type: type) -> None:
    if type(value) is not result_type or tuple(field.name for field in fields(result_type)) != SOURCE_FIELDS:
        raise AssertionError("Exact10 type or fields")
    storage = vars(value)
    if type(storage) is not dict or tuple(storage) != SOURCE_FIELDS:
        raise AssertionError("Exact10 storage")
    values = tuple(getattr(value, name) for name in SOURCE_FIELDS)
    if result_type(*values) != value:
        raise AssertionError("Exact10 reconstruction")


def _verify_truth(rows: tuple[dict[str, str], ...]) -> None:
    standalone = importlib.import_module("covalent_ext.covapie_bulk_download_admission_admit_011_rule_logic_interface")
    oracle = importlib.import_module("covalent_ext.covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate")
    with (ROOT / SOURCE_BOUNDARY[2][0]).open(newline="", encoding="utf-8") as handle:
        predecessor = tuple(csv.DictReader(handle))
    if len(rows) != 84 or len(predecessor) != 84:
        raise AssertionError("Exact84 cardinality")
    expected_groups = {
        "historical_observed": 47, "scalar_reason": 19, "contract_reason": 2,
        "snapshot_reason": 2, "cross_context_mismatch": 5, "collision": 1,
        "passed": 1, "multi_invalid": 7,
    }
    if Counter(row["case_group"] for row in rows) != expected_groups:
        raise AssertionError("Exact84 semantic groups")
    for observed, truth in zip(rows, predecessor, strict=True):
        candidate = ast.literal_eval(truth["candidate_representation"])
        contract, snapshot = standalone._case_context(dict(truth))
        source = standalone.evaluate_admit_011(candidate, snapshot, contract)
        oracle_result = oracle.classify_admit_011_raw_target_relative_path_design(candidate, snapshot, contract)
        _validate_source_object(source, standalone.Admit011EvaluationResult)
        _validate_source_object(oracle_result, oracle.Admit011EvaluationResultDesign)
        expected = standalone.Admit011EvaluationResult(*(getattr(oracle_result, name) for name in SOURCE_FIELDS))
        if source != expected:
            raise AssertionError("formal/oracle Exact10 mismatch")
        source_json = json.loads(observed["source_exact10_json"])
        oracle_json = json.loads(observed["oracle_exact10_json"])
        unified = json.loads(observed["unified_exact13_json"])
        expected_source_json = json.loads(json.dumps({name: getattr(source, name) for name in SOURCE_FIELDS}))
        if (
            observed["case_id"] != truth["case_id"]
            or observed["case_group"] != truth["matrix_group"]
            or observed["behavior"] != "exact10_to_exact13"
            or observed["expected_dispatch_code"] != ""
        ):
            raise AssertionError("truth identity")
        if source_json != expected_source_json or oracle_json != expected_source_json:
            raise AssertionError("truth Exact10 JSON")
        if tuple(unified) != RESULT_FIELDS or unified["schema_version"] != SCHEMA or unified["admission_rule_id"] != RULE_ID or unified["admission_rule_name"] != RULE_NAME or unified["adapter_id"] != ADAPTER_ID:
            raise AssertionError("truth Exact13 identity")
        if unified["normalized_values"] != source_json["validated_candidate_fields"] or unified["validated_candidate_fields"] != source_json["validated_candidate_fields"]:
            raise AssertionError("truth projection")
        for key in ("outcome", "passed", "blocks_candidate", "reason", "consumed_candidate_fields", "consumed_context_items", "evaluator_io_used"):
            if unified[key] != source_json[key]:
                raise AssertionError("truth passthrough")
        if observed["expected_reason"] != source.reason or observed["formal_call_count"] != "1" or observed["oracle_call_count"] != "1" or observed["case_passed"] != "true":
            raise AssertionError("truth metadata")


def _expected_contract_rows() -> tuple[dict[str, str], ...]:
    definitions = (
        ("identity", "rule", f"{RULE_ID}|{RULE_NAME}|{ADAPTER_ID}"),
        ("registry", "current_order", "|".join(CURRENT_ORDER)),
        ("registry", "future_order", "|".join(FUTURE_ORDER)),
        ("registry", "known_ids", "|".join(KNOWN_IDS)),
        ("candidate", "fields", "raw_target_relative_path"),
        ("context", "standalone_consumption_order", "raw_target_relative_path_contract|existing_raw_target_relative_paths"),
        ("formal", "public_parameter_order", "raw_target_relative_path|existing_raw_target_relative_paths|raw_target_relative_path_contract"),
        ("formal", "exactly_once", "true"),
        ("oracle", "exactly_once_after_source_validation", "true"),
        ("oracle", "exact_result_type", "Admit011EvaluationResultDesign"),
        ("source", "exact10_fields", "|".join(SOURCE_FIELDS)),
        ("projection", "exact13_fields", "|".join(RESULT_FIELDS)),
        ("dispatch", "exact6_fields", "|".join(ERROR_FIELDS)),
        ("dispatch", "error_codes", "|".join(ERROR_CODES)),
        ("result", "outcomes", "|".join(OUTCOMES)),
        ("routing", "precedence", "|".join(ROUTING_ORDER)),
        ("routing", "mapping", "Mapping_subclasses_allowed_direct_lookup_once_KeyError_only"),
        ("routing", "lookup_counts", "contract=1|snapshot=1|candidate=1"),
        ("identity", "object_identity", "candidate_snapshot_contract_preserved_for_formal_and_oracle"),
        ("source", "validation", "exact_type_storage_order_types_reconstruction_post_init_full_invariants"),
        ("source", "oracle_equivalence", "all_Exact10_values_and_types_equal"),
        ("projection", "normalized_values", "source.validated_candidate_fields"),
        ("projection", "adapter_side_path_processing", "none"),
        ("boundary", "runtime", "design_only_no_handler_registry_or_dispatcher"),
        ("boundary", "operations", "no_provider_mapping_raw_network_download_model_checkpoint_training"),
        ("training", "prerequisite", "feature_semantics_audit_required_Step12D_smoke_only"),
    )
    expected = tuple({
        "contract_order": str(index), "contract_id": f"CONTRACT_{index:03d}",
        "contract_group": group, "contract_subject": subject,
        "contract_value": value, "contract_status": "frozen",
    } for index, (group, subject, value) in enumerate(definitions, 1))
    if len(expected) != 26 or any(tuple(row) != CONTRACT_COLUMNS for row in expected):
        raise AssertionError("checker-owned Exact26 construction")
    return expected


def _verify_contract(rows: tuple[dict[str, str], ...]) -> None:
    if rows != _expected_contract_rows():
        raise AssertionError("Exact26 contract complete equality")


def _candidate_invalid_json(reason: str) -> str:
    value = {
        "schema_version": SCHEMA, "admission_rule_id": RULE_ID,
        "admission_rule_name": RULE_NAME, "outcome": "invalid", "passed": False,
        "blocks_candidate": True, "reason": reason, "normalized_values": [],
        "validated_candidate_fields": [], "consumed_candidate_fields": list(CANDIDATE_FIELDS),
        "consumed_context_items": list(CONTEXT_ITEMS), "evaluator_io_used": False,
        "adapter_id": ADAPTER_ID,
    }
    if tuple(value) != RESULT_FIELDS:
        raise AssertionError("checker-owned candidate Exact13 construction")
    return json.dumps(value, separators=(",", ":"))


def _expected_routing_rows() -> tuple[dict[str, str], ...]:
    invalid_mapping = _candidate_invalid_json(CANDIDATE_REASON)
    missing = _candidate_invalid_json(MISSING_REASON)
    cases = (
        ("context", "batch_non_none", "batch non-None", "dispatch_error", CONTEXT_REASONS["batch_context"], "", 0, 0, "not_accessed", 0, "n/a"),
        ("context", "evaluation_non_mapping", "evaluation non-Mapping", "dispatch_error", CONTEXT_REASONS["evaluation_context"], "", 0, 0, "not_accessed", 0, "n/a"),
        ("context", "contract_missing", "contract key absent", "dispatch_error", CONTEXT_REASONS["contract_key"], "", 0, 0, "not_accessed", 1, "n/a"),
        ("context", "snapshot_missing", "snapshot key absent", "dispatch_error", CONTEXT_REASONS["snapshot_key"], "", 0, 0, "not_accessed", 2, "n/a"),
        ("context", "download_non_none", "download non-None", "dispatch_error", CONTEXT_REASONS["download_result_context"], "", 0, 0, "not_accessed", 2, "n/a"),
        ("context", "stage_non_none", "stage non-None", "dispatch_error", CONTEXT_REASONS["stage_authorization_context"], "", 0, 0, "not_accessed", 2, "n/a"),
        ("context", "mapping_subclass", "evaluation Mapping subclass", "accepted", "", "", 1, 1, "value_read_once", 3, "true"),
        ("context", "extra_keys", "extra evaluation keys", "ignored", "", "", 1, 1, "value_read_once", 3, "true"),
        ("context", "contract_lookup_once", "repeat lookup bomb", "accepted_single_lookup", "", "", 1, 1, "value_read_once", 3, "true"),
        ("context", "snapshot_lookup_once", "repeat lookup bomb", "accepted_single_lookup", "", "", 1, 1, "value_read_once", 3, "true"),
        ("precedence", "batch_blocks_evaluation", "batch and evaluation invalid", "first_batch_error", CONTEXT_REASONS["batch_context"], "", 0, 0, "not_accessed", 0, "n/a"),
        ("precedence", "evaluation_blocks_lookup", "evaluation and keys invalid", "evaluation_error", CONTEXT_REASONS["evaluation_context"], "", 0, 0, "not_accessed", 0, "n/a"),
        ("precedence", "contract_blocks_snapshot", "both keys absent", "contract_error", CONTEXT_REASONS["contract_key"], "", 0, 0, "not_accessed", 1, "n/a"),
        ("precedence", "snapshot_blocks_candidate", "snapshot absent and candidate bomb", "snapshot_error", CONTEXT_REASONS["snapshot_key"], "", 0, 0, "not_accessed", 2, "n/a"),
        ("precedence", "download_blocks_candidate", "download invalid and candidate bomb", "download_error", CONTEXT_REASONS["download_result_context"], "", 0, 0, "not_accessed", 2, "n/a"),
        ("precedence", "stage_blocks_candidate", "stage invalid and candidate bomb", "stage_error", CONTEXT_REASONS["stage_authorization_context"], "", 0, 0, "not_accessed", 2, "n/a"),
        ("candidate", "non_mapping", "candidate non-Mapping", "exact13_invalid", CANDIDATE_REASON, invalid_mapping, 0, 0, "envelope_checked", 2, "n/a"),
        ("candidate", "field_missing", "candidate key absent", "exact13_invalid", MISSING_REASON, missing, 0, 0, "single_lookup", 3, "n/a"),
        ("candidate", "mapping_subclass", "candidate Mapping subclass", "accepted", "", "", 1, 1, "value_read_once", 3, "true"),
        ("candidate", "extra_keys", "extra candidate keys", "ignored", "", "", 1, 1, "value_read_once", 3, "true"),
        ("candidate", "lookup_once", "candidate repeat lookup bomb", "accepted_single_lookup", "", "", 1, 1, "value_read_once", 3, "true"),
        ("call", "formal_once", "valid routing", "one positional candidate_snapshot_contract call", "", "", 1, 1, "value_read_once", 3, "true"),
        ("call", "oracle_once", "valid source", "one positional candidate_snapshot_contract call", "", "", 1, 1, "value_read_once", 3, "true"),
        ("call", "formal_exception", "formal raises", "exception_no_source_or_oracle", "", "", 1, 0, "value_read_once", 3, "true"),
        ("source", "wrong_type", "formal object", "adapter_not_ready_no_oracle", SOURCE_TYPE_REASON, "", 1, 0, "value_read_once", 3, "true"),
        ("source", "subclass", "formal subclass", "adapter_not_ready_no_oracle", SOURCE_TYPE_REASON, "", 1, 0, "value_read_once", 3, "true"),
        ("source", "invariant", "Exact10 invariant drift", "adapter_not_ready_no_oracle", SOURCE_INVARIANT_REASON, "", 1, 0, "value_read_once", 3, "true"),
        ("oracle", "exception", "oracle raises", "adapter_not_ready_no_projection", SOURCE_INVARIANT_REASON, "", 1, 1, "value_read_once", 3, "true"),
        ("oracle", "type_drift", "oracle wrong type", "adapter_not_ready_no_projection", SOURCE_INVARIANT_REASON, "", 1, 1, "value_read_once", 3, "true"),
        ("oracle", "mismatch", "full Exact10 mismatch", "adapter_not_ready_no_projection", SOURCE_INVARIANT_REASON, "", 1, 1, "value_read_once", 3, "true"),
        ("projection", "passed", "unoccupied canonical path", "exact10_to_exact13", "", "", 1, 1, "value_read_once", 3, "true"),
        ("projection", "collision", "occupied canonical path", "exact10_to_exact13_blocked", "", "", 1, 1, "value_read_once", 3, "true"),
        ("projection", "invalid_scalar", "scalar grammar invalid", "exact10_to_exact13_invalid", "", "", 1, 1, "value_read_once", 3, "true"),
    )
    expected = tuple({
        "matrix_order": str(index), "matrix_group": group, "case_id": case_id,
        "condition": condition, "expected_behavior": behavior, "expected_reason": reason,
        "expected_result_json": result, "formal_call_count": str(formal),
        "oracle_call_count": str(oracle_calls), "candidate_access_status": access,
        "required_lookup_count": str(lookups), "identity_preserved": identity,
        "case_passed": "true",
    } for index, (group, case_id, condition, behavior, reason, result, formal, oracle_calls, access, lookups, identity) in enumerate(cases, 1))
    if (
        len(expected) != 33
        or any(tuple(row) != ROUTING_COLUMNS for row in expected)
        or len({(row["matrix_group"], row["case_id"]) for row in expected}) != 33
        or Counter(row["matrix_group"] for row in expected) != {"context": 10, "precedence": 6, "candidate": 5, "call": 3, "source": 3, "oracle": 3, "projection": 3}
    ):
        raise AssertionError("checker-owned Exact33 construction")
    return expected


def _verify_routing(rows: tuple[dict[str, str], ...]) -> None:
    if rows != _expected_routing_rows():
        raise AssertionError("Exact33 routing complete equality")


def _expected_safety_rows() -> tuple[dict[str, str], ...]:
    positive = (
        "adapter_contract_design", "candidate_projection_design", "context_routing_design",
        "standalone_source_validation_design", "independent_oracle_equivalence_design",
        "exact10_to_exact13_projection_design", "formal_exactly_once", "oracle_exactly_once",
        "candidate_context_identity_preserved", "deterministic_set_atomic_materialization",
        "source_attestation", "issue_inventory_preservation", "design_only_status",
    )
    negative = (
        "runtime_handler", "registry_modification", "dispatcher_modification",
        "adapter_filesystem_use", "network", "raw_read_or_enumeration", "checkpoint",
        "provider_mapping", "download", "candidate_context_mutation", "model_forward",
        "model_loss", "dataloader", "training", "fine_tune", "parameter_update",
        "stage", "commit", "push",
    )
    expected = tuple({
        "safety_item": item, "expected_executed": str(executed).lower(),
        "observed_executed": str(executed).lower(), "safety_passed": "true",
    } for item, executed in (*((item, True) for item in positive), *((item, False) for item in negative)))
    if len(expected) != 32 or len({row["safety_item"] for row in expected}) != 32 or any(tuple(row) != SAFETY_COLUMNS for row in expected):
        raise AssertionError("checker-owned Exact32 construction")
    return expected


def _verify_safety(rows: tuple[dict[str, str], ...]) -> None:
    if rows != _expected_safety_rows():
        raise AssertionError("Exact32 safety complete equality")


def _verify_manifest(manifest: dict[str, Any], hashes: Mapping[str, str]) -> None:
    if set(manifest) != MANIFEST_KEYS:
        raise AssertionError("manifest exact keyset")
    expected_scalars = {
        "project": "CovaPIE", "step": "ADMIT_011 unified adapter contract design gate v1",
        "stage": STAGE, "manifest_schema_version": "covapie_admit_011_unified_adapter_contract_manifest_v1",
        "expected_base_commit": BASE, "expected_base_subject": SUBJECT, "admission_rule_id": RULE_ID,
        "admission_rule_name": RULE_NAME, "adapter_id": ADAPTER_ID, "formal_evaluator": "evaluate_admit_011",
        "formal_result_type": "Admit011EvaluationResult", "future_adapter_handler": "_evaluate_registered_admit_011",
        "independent_oracle": "classify_admit_011_raw_target_relative_path_design",
        "result_schema_version": SCHEMA, "source_input_count": 16, "output_file_count": 6,
        "projection_truth_matrix_row_count": 84, "projection_truth_matrix_historical_count": 47,
        "recommended_next_step": "implement_covapie_unified_dispatch_runtime_with_admit_001_to_011_v1",
        "step12d_is_final_training_feature_contract": False,
        "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "all_checks_passed": True,
    }
    if any(manifest.get(key) != value for key, value in expected_scalars.items()):
        raise AssertionError("manifest identity/scalar")
    expected_lists = {
        "candidate_fields": list(CANDIDATE_FIELDS), "context_items": list(CONTEXT_ITEMS),
        "current_registered_rule_order": list(CURRENT_ORDER), "future_registered_rule_order": list(FUTURE_ORDER),
        "known_rule_ids": list(KNOWN_IDS), "known_not_registered_rule_ids": list(KNOWN_IDS[10:]),
        "result_fields": list(RESULT_FIELDS), "standalone_result_fields": list(SOURCE_FIELDS),
        "dispatch_error_fields": list(ERROR_FIELDS), "dispatch_error_codes": list(ERROR_CODES),
        "outcome_vocabulary": list(OUTCOMES), "context_routing_order": list(ROUTING_ORDER),
        "output_files": list(OUTPUTS), "source_input_paths": [path for path, _ in SOURCE_BOUNDARY],
    }
    if any(manifest.get(key) != value for key, value in expected_lists.items()):
        raise AssertionError("manifest ordered contract")
    readiness = {**{key: True for key in TRUE_READINESS}, **{key: False for key in FALSE_READINESS}}
    if manifest.get("readiness") != readiness or any(manifest.get(key) is not value for key, value in readiness.items()):
        raise AssertionError("manifest readiness")
    if manifest.get("source_input_sha256") != dict(SOURCE_BOUNDARY):
        raise AssertionError("manifest source SHA")
    expected_verification = [{
        "source_order": index, "source_relative_path": relative,
        "tracked": True, "base_tree_blob": True, "base_tree_mode": "100644_or_100755",
        "filesystem_regular": True, "non_symlink": True, "parent_chain_non_symlink": True,
        "safe_descendant": True, "expected_sha256": expected,
        "base_tree_sha256": expected, "filesystem_sha256": expected, "source_verified": True,
    } for index, (relative, expected) in enumerate(SOURCE_BOUNDARY, 1)]
    expected_other = {
        "independent_oracle_result_type": "Admit011EvaluationResultDesign",
        "context_failure_dispatch_code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        "context_failure_flags": {"known_rule": True, "callable_discovered": True, "adapter_ready": True},
        "context_routing_reasons": CONTEXT_REASONS,
        "candidate_mapping_invalid_reason": CANDIDATE_REASON,
        "candidate_missing_reason": MISSING_REASON,
        "candidate_invalid_projection": {
            "outcome": "invalid", "passed": False, "blocks_candidate": True,
            "normalized_values": [], "validated_candidate_fields": [],
            "consumed_candidate_fields": list(CANDIDATE_FIELDS),
            "consumed_context_items": list(CONTEXT_ITEMS), "evaluator_io_used": False,
            "adapter_id": ADAPTER_ID,
        },
        "formal_positional_argument_order": ["raw_target_relative_path_object", "existing_raw_target_relative_paths_object", "raw_target_relative_path_contract_object"],
        "formal_call_count_after_candidate_gate": 1, "oracle_call_count_after_source_validation": 1,
        "required_lookup_counts": {"raw_target_relative_path": 1, "raw_target_relative_path_contract": 1, "existing_raw_target_relative_paths": 1},
        "original_object_identity_preserved": True, "adapter_side_normalization": False,
        "adapter_side_path_repair_or_resolution": False, "source_type_invalid_reason": SOURCE_TYPE_REASON,
        "source_invariant_invalid_reason": SOURCE_INVARIANT_REASON, "source_exact_type_required": True,
        "source_exact10_full_invariant_validation": True, "oracle_exact_type_required": True,
        "source_oracle_full_exact10_equality_required": True,
        "normalized_values_projection": "source.validated_candidate_fields",
        "contract_row_count": 26, "contract_pass_count": 26,
        "routing_matrix_row_count": 33, "routing_matrix_pass_count": 33,
        "routing_matrix_group_counts": {"call": 3, "candidate": 5, "context": 10, "oracle": 3, "precedence": 6, "projection": 3, "source": 3},
        "projection_truth_matrix_pass_count": 84,
        "projection_truth_matrix_group_counts": {"collision": 1, "contract_reason": 2, "cross_context_mismatch": 5, "historical_observed": 47, "multi_invalid": 7, "passed": 1, "scalar_reason": 19, "snapshot_reason": 2},
        "safety_row_count": 32, "safety_pass_count": 32,
        "issue_inventory_row_count": 11, "issue_inventory_preserved_byte_identical": True,
        "issue_inventory_sha256": SOURCE_BOUNDARY[5][1],
        "coverage_issue_status": "open", "coverage_issue_affected_rules": "ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015",
        "cross_rule_aggregation_issue_status": "open", "raw_target_context_issue_status": "resolved",
        "source_boundary_name": "fixed_ordered_exact16_committed_source_boundary",
        "source_input_verification": expected_verification,
        "source_structural_checks_before_first_explicit_content_read": True,
        "output_sha256_excludes_manifest_self_hash": True,
        "feature_semantics_audit_required_before_training": True,
        "stop_boundaries": ["runtime_handler_not_implemented", "registry_unchanged", "dispatcher_unchanged", "provider_mapping_not_validated", "real_provider_evaluation_not_executed", "raw_network_download_forbidden", "model_checkpoint_training_forbidden"],
        "validation_failures": [],
    }
    if any(manifest.get(key) != value for key, value in expected_other.items()):
        raise AssertionError("manifest complete semantic contract")
    expected_output_hash = {name: hashes[name] for name in OUTPUTS[:-1]}
    if manifest.get("output_sha256") != expected_output_hash:
        raise AssertionError("manifest output SHA")


def _validate_output_tree(output_root: Path = OUTPUT_ROOT, *, enforce_frozen_hashes: bool = True) -> dict[str, str]:
    source_rows = _verify_sources()
    if len(source_rows) != 16 or _literal_registry_keys(source_rows[10]["content"]) != CURRENT_ORDER:
        raise AssertionError("current registry Exact10")
    contents = _output_bytes(output_root)
    hashes = {name: _sha(content) for name, content in contents.items()}
    _verify_contract(_csv(contents[OUTPUTS[0]], CONTRACT_COLUMNS))
    _verify_routing(_csv(contents[OUTPUTS[1]], ROUTING_COLUMNS))
    _verify_truth(_csv(contents[OUTPUTS[2]], TRUTH_COLUMNS))
    _verify_safety(_csv(contents[OUTPUTS[3]], SAFETY_COLUMNS))
    issues = _csv(contents[OUTPUTS[4]], ISSUE_COLUMNS)
    predecessor_issue = source_rows[5]["content"]
    if contents[OUTPUTS[4]] != predecessor_issue or len(issues) != 11:
        raise AssertionError("Exact11 issue byte preservation")
    issue_map = {row["issue_id"]: row for row in issues}
    if issue_map["RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED"]["status"] != "resolved" or issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] != "|".join(KNOWN_IDS[10:]) or issue_map["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["status"] != "open":
        raise AssertionError("issue state")
    manifest = json.loads(contents[OUTPUTS[5]].decode())
    if type(manifest) is not dict:
        raise AssertionError("manifest root")
    _verify_manifest(manifest, hashes)
    if enforce_frozen_hashes and hashes != FROZEN_OUTPUT_SHA256:
        raise AssertionError("frozen output hash")
    return hashes


def main() -> int:
    _verify_design_ast()
    before = _output_bytes(OUTPUT_ROOT)
    module = importlib.import_module(MODULE)
    if _output_bytes(OUTPUT_ROOT) != before:
        raise AssertionError("production import side effect")
    hashes = _validate_output_tree()
    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        first_root, second_root = Path(first) / "set", Path(second) / "set"
        module.run_covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1(first_root, repo_root=ROOT)
        module.run_covapie_bulk_download_admission_admit_011_unified_adapter_contract_design_gate_v1(second_root, repo_root=ROOT)
        if _output_bytes(first_root) != _output_bytes(second_root) or _output_bytes(first_root) != before:
            raise AssertionError("deterministic materialization")
        _validate_output_tree(first_root, enforce_frozen_hashes=False)
    print(json.dumps({"checked": True, "output_sha256": hashes}, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
