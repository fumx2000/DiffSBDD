#!/usr/bin/env python3
"""Independent fail-closed checker for the ADMIT_010 adapter design gate."""

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
import tempfile
from collections import Counter
from dataclasses import fields
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = "covalent_ext.covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate"
OUTPUT_ROOT = ROOT / "data/derived/covalent_small/covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate_v1"
BASE = "4090769a3036e4019a65ce93ae61bd5ac8408983"
SUBJECT = "add CovaPIE standalone ADMIT_010 rule logic interface v1"
RULE_ID = "ADMIT_010"
RULE_NAME = "leakage_group_assignment_before_split"
ADAPTER_ID = "covapie_admit_010_unified_adapter_v1"
SCHEMA = "covapie_unified_admission_rule_evaluation_v1"
CURRENT_ORDER = tuple(f"ADMIT_{index:03d}" for index in range(1, 10))
FUTURE_ORDER = (*CURRENT_ORDER, RULE_ID)
KNOWN_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
RESULT_FIELDS = (
    "schema_version", "admission_rule_id", "admission_rule_name", "outcome",
    "passed", "blocks_candidate", "reason", "normalized_values",
    "validated_candidate_fields", "consumed_candidate_fields",
    "consumed_context_items", "evaluator_io_used", "adapter_id",
)
SOURCE_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_leakage_group_id", "validated_candidate_fields",
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
CANDIDATE_FIELDS = ("leakage_group_id",)
CONTEXT_ITEMS = ("leakage_group_assignment_provenance_contract",)
CANDIDATE_REASON = "ADMIT_010_CANDIDATE_RECORD_MAPPING_INVALID"
MISSING_REASON = "leakage_group_id_missing"
SOURCE_TYPE_REASON = "ADMIT_010_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
SOURCE_INVARIANT_REASON = "ADMIT_010_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
CONTEXT_REASONS = {
    "batch_context": "ADMIT_010_BATCH_CONTEXT_MUST_BE_NONE",
    "evaluation_context": "ADMIT_010_EVALUATION_CONTEXT_MAPPING_REQUIRED",
    "evaluation_context_key": "ADMIT_010_LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_CONTRACT_REQUIRED",
    "download_result_context": "ADMIT_010_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
    "stage_authorization_context": "ADMIT_010_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
}
ROUTING_ORDER = (
    "batch_context_must_be_none", "evaluation_context_mapping_validation",
    "leakage_group_assignment_provenance_contract_required_key_lookup",
    "download_result_context_must_be_none", "stage_authorization_context_must_be_none",
    "candidate_record_mapping_validation", "leakage_group_id_required_key_lookup",
    "formal_evaluator", "source_validation", "independent_oracle",
    "full_exact10_equality", "exact13_projection",
)
OUTPUTS = (
    "covapie_admit_010_unified_adapter_contract.csv",
    "covapie_admit_010_candidate_projection_and_context_routing_matrix.csv",
    "covapie_admit_010_unified_result_projection_truth_matrix.csv",
    "covapie_admit_010_unified_adapter_safety_audit.csv",
    "covapie_admit_010_unified_adapter_issue_readiness_inventory.csv",
    "covapie_admit_010_unified_adapter_contract_manifest.json",
)
FROZEN_OUTPUT_SHA256 = dict(zip(OUTPUTS, (
    "2116f5e0afe3e69be7ec5ea6d8c95e14112c1905904f663bf1d6990a41534d81",
    "044b7812d2b8a53d6d31c303d8c6d0b4cfa308b53cb9d02a16718346e676fdbc",
    "25a36e3bb08f2c354b1a52382485727bb5ccdf51d1465f087c21c6f622a8ba36",
    "9faf1a3ba6315218fac5521a99170b0ea38dc50185e61ddcadfe3719757764c5",
    "779932531b630072ff33721e689a2865defdad477df8335a9950c8e4537476bd",
    "6ee42e0baf26ece28df75201521babdf8f9ffe7a89b7544a346f92e5ecd39119",
), strict=True))
SOURCE_BOUNDARY = (
    ("src/covalent_ext/covapie_bulk_download_admission_admit_010_rule_logic_interface.py", "05a89049fca65b6f9d9480392eb57b333a1960064fbd6c2c5061efeac3bb9a1c"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_010_rule_logic_interface_v1/covapie_admit_010_rule_logic_interface_manifest.json", "5769c583bc5ade6dbeb81190b20e1774120f7b38dbf53d540f97b50dbf594d54"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_010_rule_logic_interface_v1/covapie_admit_010_rule_logic_interface_contract.csv", "809a591cca7bd5f94920100105dbc6d643d8e73f38dc7692933f244de954d774"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_010_rule_logic_interface_v1/covapie_admit_010_rule_logic_interface_truth_matrix.csv", "c5caa0f398f7d8592b2ef8ab14e4af4c47e9bfd7a06e476f617de55e6c627284"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_010_rule_logic_interface_v1/covapie_admit_010_rule_logic_interface_source_boundary_audit.csv", "8695ed6089fd576581ef1a50e7c48b07cac12a7aa6450f19a384bfbfabcef84d"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_010_rule_logic_interface_v1/covapie_admit_010_rule_logic_interface_safety_audit.csv", "85dbd9f38e39a5620c41081d6134774893250a43d67023b69cae94775224d2ab"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_010_rule_logic_interface_v1/covapie_admit_010_rule_logic_interface_issue_readiness_inventory.csv", "779932531b630072ff33721e689a2865defdad477df8335a9950c8e4537476bd"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate.py", "cbff1bd3fe4e6d65c9be33a5efee4d80ea1f9310cb7cb73e45dc4e1055a2de05"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate_v1/covapie_admit_010_leakage_group_assignment_provenance_contract_manifest.json", "33fb0d6f35b49dbf98e61e2c16fafece4b01cdfcce629ff7f1ac5afb1e7e5af2"),
    ("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009.py", "80bdc66d2b0b2a1d761b0a1eb07f644f47535516598c3869f75a92cddafbdb39"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1/covapie_admit_001_to_009_runtime_manifest.json", "b4d5092949292f27310a05ef2c5c77c8036e7ad0474a15b8a0574bc910931dfc"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate.py", "9fc1ca277220da3dd982e72c4198e74af911d4cc9d4df39e4864cb8ea0fe1c30"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_009_unified_adapter_contract_design_gate_v1/covapie_admit_009_unified_adapter_contract_manifest.json", "efe1da7f804a411028903a3a6fc498eb2f0cc5f2b0823b81b5aab3acd83d53c1"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_009_rule_logic_interface.py", "3649971eec020c5981a3ba8bfddeb604797f8557fb6036efd6094a2b0d6ab4e4"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_009_rule_logic_interface_v1/covapie_admit_009_rule_logic_interface_manifest.json", "b69941408b6f6098e926f7cf3f60cf526811e78a71cb07000c332511b19d5447"),
)
CONTRACT_COLUMNS = ("contract_order", "contract_id", "contract_group", "contract_subject", "contract_value", "contract_status")
ROUTING_COLUMNS = ("matrix_order", "matrix_group", "case_id", "condition", "expected_behavior", "expected_reason", "expected_result_json", "formal_call_count", "oracle_call_count", "candidate_access_status", "required_lookup_count", "identity_preserved", "case_passed")
TRUTH_COLUMNS = ("case_id", "case_group", "behavior", "expected_dispatch_code", "expected_reason", "source_exact10_json", "oracle_exact10_json", "unified_exact13_json", "formal_call_count", "oracle_call_count", "case_passed")
SAFETY_COLUMNS = ("safety_item", "expected_executed", "observed_executed", "safety_passed")
ISSUE_COLUMNS = ("issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status", "blocking_scope", "blocking_reason", "issue_origin", "integration_transition", "issue_count")


def _checker_resolved_output_target_is_authorized(
    root: Path,
    repo_root: Path,
    *,
    output_root_was_relative: bool,
) -> bool:
    """Checker-owned containment gate; it performs no output/source byte read."""
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
        resolved_root = root.resolve(strict=True)
        if Path(os.path.abspath(root)) != resolved_root:
            return False
        if output_root_was_relative:
            resolved_root.relative_to(resolved_repo)
    except (OSError, RuntimeError, ValueError):
        return False
    return True


def _git(*args: str, text: bool = False) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(("git", *args), cwd=ROOT, capture_output=True, check=False, text=text)


def _csv(path: Path, columns: tuple[str, ...]) -> tuple[dict[str, str], ...]:
    reader = csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"), newline=""))
    if tuple(reader.fieldnames or ()) != columns:
        raise AssertionError(f"header mismatch: {path.name}")
    rows = tuple(dict(row) for row in reader)
    if any(tuple(row) != columns or any(value is None for value in row.values()) for row in rows):
        raise AssertionError(f"row shape mismatch: {path.name}")
    return rows


def _verify_sources() -> tuple[dict[str, Any], ...]:
    if len(SOURCE_BOUNDARY) != 15 or len({path for path, _ in SOURCE_BOUNDARY}) != 15:
        raise AssertionError("Exact15 boundary drift")
    if _git("show", "-s", "--format=%s", BASE, text=True).stdout.rstrip("\n") != SUBJECT:
        raise AssertionError("base subject mismatch")
    if _git("merge-base", "--is-ancestor", BASE, "HEAD").returncode:
        raise AssertionError("base is not ancestor")
    structural: list[tuple[str, str]] = []
    for relative, expected in SOURCE_BOUNDARY:
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or path.parts[:2] == ("data", "raw") or path.parts[0] == "checkpoints":
            raise AssertionError("unsafe source")
        target = ROOT / path
        if _git("ls-files", "--error-unmatch", "--", relative).returncode:
            raise AssertionError(f"untracked source: {relative}")
        tree = _git("ls-tree", BASE, "--", relative, text=True)
        metadata = tree.stdout.split("\t", 1)[0].split() if tree.returncode == 0 else []
        mode = os.lstat(target).st_mode
        if len(metadata) != 3 or metadata[0] not in ("100644", "100755") or metadata[1] != "blob":
            raise AssertionError("base blob mismatch")
        if not stat.S_ISREG(mode) or stat.S_ISLNK(mode) or target.resolve(strict=True).relative_to(ROOT.resolve(strict=True)) is None:
            raise AssertionError("filesystem source type")
        structural.append((relative, expected))
    verified = []
    for index, (relative, expected) in enumerate(structural, 1):
        base_bytes = _git("show", f"{BASE}:{relative}").stdout
        fs_bytes = (ROOT / relative).read_bytes()
        base_sha = hashlib.sha256(base_bytes).hexdigest()
        fs_sha = hashlib.sha256(fs_bytes).hexdigest()
        if expected != base_sha or expected != fs_sha:
            raise AssertionError(f"source hash mismatch: {relative}")
        verified.append({
            "source_order": index, "source_relative_path": relative, "tracked": True,
            "base_tree_blob": True, "filesystem_regular": True, "non_symlink": True,
            "safe_descendant": True,
            "expected_sha256": expected, "base_tree_sha256": base_sha,
            "filesystem_sha256": fs_sha, "source_verified": True,
        })
    return tuple(verified)


def _verify_runtime_identity() -> None:
    runtime = importlib.import_module("covalent_ext.covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009")
    predecessor = runtime.predecessor
    for name in ("UnifiedAdmissionRuleEvaluation", "UnifiedAdmissionDispatchError", "RESULT_SCHEMA_VERSION", "RESULT_FIELDS", "DISPATCH_ERROR_FIELDS", "DISPATCH_ERROR_CODES", "OUTCOME_VOCABULARY"):
        if getattr(runtime, name) is not getattr(predecessor, name):
            raise AssertionError(f"current public identity drift: {name}")
    if tuple(runtime.KNOWN_RULE_IDS) != KNOWN_IDS or tuple(runtime.EVALUATOR_REGISTRY) != CURRENT_ORDER:
        raise AssertionError("current rule identity/order drift")
    if any(runtime.EVALUATOR_REGISTRY[rule] is not predecessor.EVALUATOR_REGISTRY[rule] for rule in CURRENT_ORDER[:8]):
        raise AssertionError("first-eight runtime identity drift")
    if runtime.EVALUATOR_REGISTRY["ADMIT_009"] is not runtime._evaluate_registered_admit_009:
        raise AssertionError("ninth runtime identity drift")
    expected = "(admission_rule_id: 'str', candidate_record: 'Mapping[str, object]', *, batch_context: 'Mapping[str, object] | None' = None, evaluation_context: 'Mapping[str, object] | None' = None, download_result_context: 'Mapping[str, object] | None' = None, stage_authorization_context: 'Mapping[str, object] | None' = None) -> 'UnifiedAdmissionRuleEvaluation'"
    if str(inspect.signature(runtime.evaluate_admission_rule)) != expected:
        raise AssertionError("current dispatcher signature drift")


def _expected_contract_rows() -> tuple[dict[str, str], ...]:
    definitions = (
        ("identity", "admission_rule_id", RULE_ID),
        ("identity", "admission_rule_name", RULE_NAME),
        ("identity", "adapter_id", ADAPTER_ID),
        ("identity", "candidate_field", CANDIDATE_FIELDS[0]),
        ("identity", "evaluation_context_item", CONTEXT_ITEMS[0]),
        ("identity", "formal_evaluator", "evaluate_admit_010"),
        ("identity", "formal_result_type", "Admit010EvaluationResult"),
        ("identity", "design_oracle", "classify_admit_010_leakage_group_assignment_provenance_design"),
        ("identity", "unified_schema", SCHEMA),
        ("runtime_reuse", "public_result_type", "UnifiedAdmissionRuleEvaluation_exact9_object_identity"),
        ("runtime_reuse", "public_error_type", "UnifiedAdmissionDispatchError_exact9_object_identity"),
        ("runtime_reuse", "public_constants", "RESULT_SCHEMA_VERSION|RESULT_FIELDS|DISPATCH_ERROR_FIELDS|DISPATCH_ERROR_CODES|OUTCOME_VOCABULARY_exact9_object_identity"),
        ("runtime_reuse", "known_rule_ids", "|".join(KNOWN_IDS)),
        ("runtime_reuse", "public_dispatch_signature", "exactly_equal_to_current_exact9"),
        ("successor", "dispatcher_identity", "new_function_object_not_current_exact9_dispatcher"),
        ("successor", "dispatcher_registry_binding", "successor_local_immutable_exact10_registry"),
        ("successor", "current_registry", "|".join(CURRENT_ORDER)),
        ("successor", "future_registry", "|".join(FUTURE_ORDER)),
        ("successor", "first_nine_handlers", "9_of_9_current_exact9_object_identity"),
        ("successor", "only_new_handler", "_evaluate_registered_admit_010"),
        ("successor", "known_not_registered", "|".join(KNOWN_IDS[10:])),
        ("routing", "precedence", "|".join(ROUTING_ORDER)),
        ("routing", "batch", "exact_none"),
        ("routing", "evaluation", "isinstance_collections.abc.Mapping"),
        ("routing", "evaluation_lookup", "single_direct_getitem_KeyError_only_missing"),
        ("routing", "download", "exact_none"),
        ("routing", "stage", "exact_none"),
        ("routing", "context_before_candidate", "all_context_checks_complete_before_candidate_access"),
        ("mapping", "copy", "none"),
        ("mapping", "iteration", "none"),
        ("mapping", "mutation", "none"),
        ("mapping", "extra_keys", "ignored"),
        ("mapping", "present_none", "present_not_missing"),
        ("mapping", "non_key_error", "propagates_unchanged"),
        ("candidate", "mapping_invalid", CANDIDATE_REASON),
        ("candidate", "required_key_absent", MISSING_REASON),
        ("candidate", "invalid_calls", "formal_0|oracle_0"),
        ("candidate", "invalid_consumed_candidate", CANDIDATE_FIELDS[0]),
        ("candidate", "invalid_consumed_context", CONTEXT_ITEMS[0]),
        ("candidate", "present_values", "forward_original_object_without_prevalidation"),
        ("call", "formal", "exactly_once_positional_scalar_then_provenance"),
        ("call", "formal_identity", "same_two_original_objects"),
        ("source", "exact_type", "type_source_is_Admit010EvaluationResult_subclass_rejected"),
        ("source", "storage", "vars_exact_builtin_dict_exact10_order"),
        ("source", "dataclass", "exact10_field_order"),
        ("source", "reads", "all_exact10_fields_in_order"),
        ("source", "reconstruction", "committed_type_post_init_and_full_equality"),
        ("source", "failure", "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY|adapter_ready_false|oracle_0|no_partial_exact13"),
        ("oracle", "call", "exactly_once_after_source_validation_same_two_objects"),
        ("oracle", "result", "Mapping_required"),
        ("oracle", "expected", "complete_committed_Admit010EvaluationResult"),
        ("oracle", "comparison", "full_exact10_equality"),
        ("projection", "fields", "|".join(RESULT_FIELDS)),
        ("projection", "normalized_values", "source.validated_candidate_fields"),
        ("projection", "consumed_context", "source.consumed_context_items_no_envelope_injection"),
        ("projection", "adapter_id", ADAPTER_ID),
        ("issues", "inventory", "Exact11_byte_identical_SHA256_779932531b630072ff33721e689a2865defdad477df8335a9950c8e4537476bd"),
        ("issues", "coverage", "open_ADMIT_010_through_ADMIT_015_unchanged"),
        ("provider", "mapping", "unvalidated_zero_real_provider_ids"),
        ("boundary", "runtime", "design_only_no_handler_registry_dispatcher_or_registration"),
        ("boundary", "operations", "no_provider_grouping_split_reassignment_raw_network_download_training"),
        ("training", "prerequisite", "feature_semantics_audit_required_Step12D_smoke_only"),
    )
    rows = tuple({
        "contract_order": str(index), "contract_id": f"CONTRACT_{index:03d}",
        "contract_group": group, "contract_subject": subject,
        "contract_value": value, "contract_status": "frozen",
    } for index, (group, subject, value) in enumerate(definitions, 1))
    if len(rows) != 62 or any(tuple(row) != CONTRACT_COLUMNS for row in rows):
        raise AssertionError("checker-owned Exact62 construction failed")
    return rows


def _json_mapping(value: dict[str, object]) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"))


def _source_mapping(value: object) -> dict[str, object]:
    return {name: getattr(value, name) for name in SOURCE_FIELDS}


def _unified_mapping_from_source(source: object) -> dict[str, object]:
    return dict(zip(RESULT_FIELDS, (
        SCHEMA, RULE_ID, RULE_NAME, source.outcome, source.passed,
        source.blocks_candidate, source.reason, source.validated_candidate_fields,
        source.validated_candidate_fields, source.consumed_candidate_fields,
        source.consumed_context_items, source.evaluator_io_used, ADAPTER_ID,
    ), strict=True))


def _candidate_invalid_mapping(reason: str) -> dict[str, object]:
    return dict(zip(RESULT_FIELDS, (
        SCHEMA, RULE_ID, RULE_NAME, "invalid", False, True, reason, (), (),
        CANDIDATE_FIELDS, CONTEXT_ITEMS, False, ADAPTER_ID,
    ), strict=True))


def _dispatch_mapping(
    reason: str, *, adapter_ready: bool = True,
    code: str = "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
) -> dict[str, object]:
    return dict(zip(ERROR_FIELDS, (
        code, RULE_ID, True, True, adapter_ready, reason,
    ), strict=True))


def _verify_contract(rows: tuple[dict[str, str], ...]) -> None:
    if rows != _expected_contract_rows():
        raise AssertionError("Exact62 contract complete equality")


def _checker_source_and_oracle(scalar: object, provenance: object) -> tuple[object, dict[str, object]]:
    standalone = importlib.import_module("covalent_ext.covapie_bulk_download_admission_admit_010_rule_logic_interface")
    oracle = importlib.import_module("covalent_ext.covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate")
    source = standalone.evaluate_admit_010(scalar, provenance)
    classification = oracle.classify_admit_010_leakage_group_assignment_provenance_design(scalar, provenance)
    expected = {"admission_rule_id": RULE_ID, **dict(classification)}
    if tuple(expected) != SOURCE_FIELDS or _source_mapping(source) != expected:
        raise AssertionError("checker semantic source Exact10 mismatch")
    return source, expected


def _expected_routing_rows() -> tuple[dict[str, str], ...]:
    standalone = importlib.import_module("covalent_ext.covapie_bulk_download_admission_admit_010_rule_logic_interface")
    scalar = "COVAPIE_LEAKAGE_GROUP_000001"
    provenance = standalone._valid_contract(candidate=scalar)
    passed, _ = _checker_source_and_oracle(scalar, provenance)
    none_result, _ = _checker_source_and_oracle(scalar, None)
    empty_result, _ = _checker_source_and_oracle("", provenance)
    malformed_result, _ = _checker_source_and_oracle("bad", provenance)
    passed_json = _json_mapping(_unified_mapping_from_source(passed))
    none_json = _json_mapping(_unified_mapping_from_source(none_result))
    empty_json = _json_mapping(_unified_mapping_from_source(empty_result))
    malformed_json = _json_mapping(_unified_mapping_from_source(malformed_result))
    candidate_invalid_json = _json_mapping(_candidate_invalid_mapping(CANDIDATE_REASON))
    missing_json = _json_mapping(_candidate_invalid_mapping(MISSING_REASON))
    dispatch = lambda reason: _json_mapping(_dispatch_mapping(reason))
    adapter_failure = lambda reason: _json_mapping(_dispatch_mapping(
        reason, adapter_ready=False, code="UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
    ))
    cases = (
        ("context", "batch_none", "batch exact None", "accepted", "", "", 1, 1, "accessed_after_context", 2, "true"),
        ("context", "batch_mapping", "batch Mapping non-None", "dispatch_error", CONTEXT_REASONS["batch_context"], dispatch(CONTEXT_REASONS["batch_context"]), 0, 0, "not_accessed", 0, "n/a"),
        ("context", "batch_object", "batch arbitrary object", "dispatch_error", CONTEXT_REASONS["batch_context"], dispatch(CONTEXT_REASONS["batch_context"]), 0, 0, "not_accessed", 0, "n/a"),
        ("context", "evaluation_none", "evaluation None", "dispatch_error", CONTEXT_REASONS["evaluation_context"], dispatch(CONTEXT_REASONS["evaluation_context"]), 0, 0, "not_accessed", 0, "n/a"),
        ("context", "evaluation_non_mapping", "evaluation arbitrary object", "dispatch_error", CONTEXT_REASONS["evaluation_context"], dispatch(CONTEXT_REASONS["evaluation_context"]), 0, 0, "not_accessed", 0, "n/a"),
        ("context", "evaluation_mapping_subclass", "evaluation Mapping subclass", "accepted_without_copy", "", passed_json, 1, 1, "accessed_after_context", 2, "true"),
        ("context", "evaluation_extra_keys", "evaluation extra keys", "ignored_without_iteration", "", passed_json, 1, 1, "accessed_after_context", 2, "true"),
        ("context", "evaluation_key_missing", "required evaluation key absent", "dispatch_error", CONTEXT_REASONS["evaluation_context_key"], dispatch(CONTEXT_REASONS["evaluation_context_key"]), 0, 0, "not_accessed", 1, "n/a"),
        ("context", "evaluation_none_present", "required value None", "forwarded_not_missing", none_result.reason, none_json, 1, 1, "value_read_once", 2, "true"),
        ("context", "context_identity", "provenance sentinel", "same_original_object", "", passed_json, 1, 1, "value_read_once", 2, "true"),
        ("context", "evaluation_direct_lookup", "single direct getitem", "one_lookup_no_get_or_contains", "", passed_json, 1, 1, "value_read_once", 2, "true"),
        ("context", "evaluation_lookup_non_key_error", "getitem raises RuntimeError", "exception_propagates", "RuntimeError", "", 0, 0, "not_accessed", 1, "n/a"),
        ("context", "download_non_none", "download non-None", "dispatch_error", CONTEXT_REASONS["download_result_context"], dispatch(CONTEXT_REASONS["download_result_context"]), 0, 0, "not_accessed", 1, "true"),
        ("context", "stage_non_none", "stage non-None", "dispatch_error", CONTEXT_REASONS["stage_authorization_context"], dispatch(CONTEXT_REASONS["stage_authorization_context"]), 0, 0, "not_accessed", 1, "true"),
        ("context", "multiple_failure_precedence", "all contexts invalid", "first_batch_error", CONTEXT_REASONS["batch_context"], dispatch(CONTEXT_REASONS["batch_context"]), 0, 0, "not_accessed", 0, "n/a"),
        ("context", "candidate_bomb", "context failure with inaccessible candidate", "candidate_not_accessed", CONTEXT_REASONS["evaluation_context"], dispatch(CONTEXT_REASONS["evaluation_context"]), 0, 0, "not_accessed", 0, "n/a"),
        ("candidate", "non_mapping", "candidate arbitrary object", "exact13_invalid", CANDIDATE_REASON, candidate_invalid_json, 0, 0, "envelope_checked", 1, "n/a"),
        ("candidate", "key_missing", "candidate key absent", "exact13_invalid", MISSING_REASON, missing_json, 0, 0, "single_lookup", 2, "n/a"),
        ("candidate", "mapping_subclass", "candidate Mapping subclass", "accepted_without_copy", "", passed_json, 1, 1, "value_read_once", 2, "true"),
        ("candidate", "extra_fields", "candidate extra fields", "ignored_without_iteration", "", passed_json, 1, 1, "value_read_once", 2, "true"),
        ("candidate", "mutable_not_mutated", "mutable candidate", "not_mutated", "", passed_json, 1, 1, "value_read_once", 2, "true"),
        ("candidate", "scalar_identity", "scalar sentinel", "same_original_object", "", passed_json, 1, 1, "value_read_once", 2, "true"),
        ("candidate", "direct_lookup", "single direct getitem", "one_lookup_no_get_or_contains", "", passed_json, 1, 1, "value_read_once", 2, "true"),
        ("candidate", "lookup_non_key_error", "getitem raises RuntimeError", "exception_propagates", "RuntimeError", "", 0, 0, "lookup_raised", 2, "n/a"),
        ("candidate", "none_present", "candidate None", "formal_invalid", "LEAKAGE_GROUP_ID_TYPE_INVALID", "", 1, 1, "value_read_once", 2, "true"),
        ("candidate", "empty_present", "candidate empty string", "formal_blocked", empty_result.reason, empty_json, 1, 1, "value_read_once", 2, "true"),
        ("candidate", "str_subclass", "candidate str subclass", "formal_invalid", "LEAKAGE_GROUP_ID_TYPE_INVALID", "", 1, 1, "value_read_once", 2, "true"),
        ("candidate", "canonical", "canonical candidate", "passed", "", passed_json, 1, 1, "value_read_once", 2, "true"),
        ("candidate", "malformed", "malformed candidate", "formal_invalid", malformed_result.reason, malformed_json, 1, 1, "value_read_once", 2, "true"),
        ("call", "formal_once", "valid envelope", "exactly_one_positional_call", "", passed_json, 1, 1, "value_read_once", 2, "true"),
        ("call", "oracle_once", "source validation succeeds", "exactly_one_positional_call", "", passed_json, 1, 1, "value_read_once", 2, "true"),
        ("source", "wrong_type", "formal returns object", "adapter_not_ready_no_oracle", SOURCE_TYPE_REASON, adapter_failure(SOURCE_TYPE_REASON), 1, 0, "value_read_once", 2, "true"),
        ("source", "subclass", "formal result subclass", "adapter_not_ready_no_oracle", SOURCE_TYPE_REASON, adapter_failure(SOURCE_TYPE_REASON), 1, 0, "value_read_once", 2, "true"),
        ("source", "storage_order", "vars order tamper", "adapter_not_ready_no_oracle", SOURCE_INVARIANT_REASON, adapter_failure(SOURCE_INVARIANT_REASON), 1, 0, "value_read_once", 2, "true"),
        ("source", "cross_field", "post-init invariant tamper", "adapter_not_ready_no_oracle", SOURCE_INVARIANT_REASON, adapter_failure(SOURCE_INVARIANT_REASON), 1, 0, "value_read_once", 2, "true"),
        ("source", "oracle_mismatch", "one of Exact10 differs", "adapter_not_ready_no_projection", SOURCE_INVARIANT_REASON, adapter_failure(SOURCE_INVARIANT_REASON), 1, 1, "value_read_once", 2, "true"),
        ("projection", "scalar_short", "empty candidate", "preserve_empty_context", empty_result.reason, empty_json, 1, 1, "value_read_once", 2, "true"),
        ("projection", "context_invalid", "provenance invalid", "preserve_canonical_and_context", none_result.reason, none_json, 1, 1, "value_read_once", 2, "true"),
        ("projection", "passed", "valid pair", "exact10_to_exact13", "", passed_json, 1, 1, "value_read_once", 2, "true"),
    )
    rows = tuple({
        "matrix_order": str(index), "matrix_group": group, "case_id": case_id,
        "condition": condition, "expected_behavior": behavior,
        "expected_reason": reason, "expected_result_json": result,
        "formal_call_count": str(formal), "oracle_call_count": str(oracle_calls),
        "candidate_access_status": access, "required_lookup_count": str(lookups),
        "identity_preserved": identity, "case_passed": "true",
    } for index, (group, case_id, condition, behavior, reason, result, formal, oracle_calls, access, lookups, identity) in enumerate(cases, 1))
    if len(rows) != 39 or any(tuple(row) != ROUTING_COLUMNS for row in rows):
        raise AssertionError("checker-owned Exact39 construction failed")
    return rows


def _expected_truth_rows() -> tuple[dict[str, str], ...]:
    standalone = importlib.import_module("covalent_ext.covapie_bulk_download_admission_admit_010_rule_logic_interface")
    rows: list[dict[str, str]] = []
    for group, case_id, scalar, provenance, _precedence in standalone._natural_cases():
        source, expected = _checker_source_and_oracle(scalar, provenance)
        rows.append({
            "case_id": f"STANDALONE_{case_id}",
            "case_group": f"standalone_{group}",
            "behavior": "exact10_to_exact13",
            "expected_dispatch_code": "",
            "expected_reason": source.reason,
            "source_exact10_json": _json_mapping(_source_mapping(source)),
            "oracle_exact10_json": _json_mapping(expected),
            "unified_exact13_json": _json_mapping(_unified_mapping_from_source(source)),
            "formal_call_count": "1", "oracle_call_count": "1",
            "case_passed": "true",
        })

    def failure(
        case_id: str, group: str, behavior: str, code: str, reason: str,
        *, unified: str = "", formal: int = 0, oracle_calls: int = 0,
    ) -> dict[str, str]:
        return {
            "case_id": case_id, "case_group": group, "behavior": behavior,
            "expected_dispatch_code": code, "expected_reason": reason,
            "source_exact10_json": "", "oracle_exact10_json": "",
            "unified_exact13_json": unified,
            "formal_call_count": str(formal), "oracle_call_count": str(oracle_calls),
            "case_passed": "true",
        }

    rows.extend((
        failure("ROUTING_batch_context", "routing_dispatch", "exact6_no_partial_result", "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", CONTEXT_REASONS["batch_context"]),
        failure("ROUTING_evaluation_context", "routing_dispatch", "exact6_no_partial_result", "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", CONTEXT_REASONS["evaluation_context"]),
        failure("ROUTING_evaluation_context_key", "routing_dispatch", "exact6_no_partial_result", "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", CONTEXT_REASONS["evaluation_context_key"]),
        failure("ROUTING_download_result_context", "routing_dispatch", "exact6_no_partial_result", "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", CONTEXT_REASONS["download_result_context"]),
        failure("ROUTING_stage_authorization_context", "routing_dispatch", "exact6_no_partial_result", "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", CONTEXT_REASONS["stage_authorization_context"]),
        failure("ROUTING_precedence", "routing_dispatch", "first_failure_no_candidate_access", "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", CONTEXT_REASONS["batch_context"]),
        failure("ROUTING_candidate_bomb", "routing_dispatch", "candidate_never_accessed", "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", CONTEXT_REASONS["evaluation_context"]),
        failure("CANDIDATE_non_mapping", "adapter_candidate_invalid", "adapter_generated_exact13", "", CANDIDATE_REASON, unified=_json_mapping(_candidate_invalid_mapping(CANDIDATE_REASON))),
        failure("CANDIDATE_key_absent", "adapter_candidate_invalid", "adapter_generated_exact13", "", MISSING_REASON, unified=_json_mapping(_candidate_invalid_mapping(MISSING_REASON))),
        failure("SOURCE_wrong_type", "source_validation_failure", "oracle_not_called_no_projection", "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", SOURCE_TYPE_REASON, formal=1),
        failure("SOURCE_subclass", "source_validation_failure", "oracle_not_called_no_projection", "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", SOURCE_TYPE_REASON, formal=1),
        failure("SOURCE_storage_or_order", "source_validation_failure", "oracle_not_called_no_projection", "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", SOURCE_INVARIANT_REASON, formal=1),
        failure("SOURCE_cross_field", "source_validation_failure", "reconstruction_rejected_no_oracle", "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", SOURCE_INVARIANT_REASON, formal=1),
        failure("SOURCE_oracle_mismatch", "source_validation_failure", "full_exact10_mismatch_no_projection", "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY", SOURCE_INVARIANT_REASON, formal=1, oracle_calls=1),
    ))
    expected = tuple(rows)
    if len(expected) != 85 or any(tuple(row) != TRUTH_COLUMNS for row in expected):
        raise AssertionError("checker-owned Exact85 construction failed")
    return expected


def _verify_truth(rows: tuple[dict[str, str], ...]) -> None:
    if rows != _expected_truth_rows():
        raise AssertionError("Exact85 truth complete equality")

def _verify_routing(rows: tuple[dict[str, str], ...]) -> None:
    if rows != _expected_routing_rows():
        raise AssertionError("Exact39 routing complete equality")


def _expected_safety_rows() -> tuple[dict[str, str], ...]:
    positive = (
        "adapter_contract_design", "context_routing_design", "candidate_projection_design",
        "standalone_source_validation_design", "exact10_oracle_equality_design",
        "exact10_to_exact13_projection_design", "future_identity_contract",
        "deterministic_materialization", "source_verification", "issue_byte_preservation",
    )
    negative = (
        "actual_adapter_handler", "registry_modification", "exact9_runtime",
        "provider_mapping", "provider_key_generation", "real_candidate_evaluation",
        "admit_011", "evaluate_all_rules", "combined_verdict", "raw_read", "network",
        "download", "checkpoint", "torch", "numpy", "rdkit", "model_forward",
        "model_loss", "training", "fine_tune", "parameter_update", "stage", "commit",
        "push", "gh",
    )
    rows = tuple({
        "safety_item": item, "expected_executed": str(expected).lower(),
        "observed_executed": str(expected).lower(), "safety_passed": "true",
    } for item, expected in (
        *((item, True) for item in positive),
        *((item, False) for item in negative),
    ))
    if len(rows) != 35 or any(tuple(row) != SAFETY_COLUMNS for row in rows):
        raise AssertionError("checker-owned Exact35 construction failed")
    return rows


def _readiness() -> dict[str, bool]:
    true = (
        "admit_010_standalone_evaluator_implemented", "evaluate_admit_010_implemented",
        "Admit010EvaluationResult_implemented", "admit_010_exact10_result_contract_frozen",
        "admit_010_unified_adapter_contract_frozen", "admit_010_candidate_projection_contract_frozen",
        "admit_010_context_routing_contract_frozen", "admit_010_formal_source_validation_contract_frozen",
        "admit_010_design_oracle_full_parity_contract_frozen", "admit_010_exact13_projection_contract_frozen",
        "admit_010_successor_dispatcher_contract_frozen", "admit_010_first_nine_handler_identity_reuse_frozen",
        "admit_010_provider_mapping_boundary_preserved", "ready_for_unified_dispatch_runtime_with_admit_001_to_010_implementation",
        "feature_semantics_audit_required_before_training",
    )
    false = (
        "leakage_group_id_provider_mapping_validated", "real_provider_leakage_group_id_count_nonzero",
        "admit_010_unified_adapter_implemented", "admit_010_registered_in_engine",
        "unified_dispatch_runtime_with_admit_001_to_010_implemented", "admit_011_started",
        "evaluate_all_rules_implemented", "combined_candidate_verdict_contract_frozen",
        "combined_candidate_verdict_implemented", "cross_rule_precedence_frozen",
        "real_candidate_evaluation", "ready_for_bulk_download_now", "ready_for_training", "ready_to_train_now",
    )
    return {**{key: True for key in true}, **{key: False for key in false}}


def _expected_manifest() -> dict[str, Any]:
    readiness = _readiness()
    source_verification = [{
        "source_order": index, "source_relative_path": relative,
        "tracked": True, "base_tree_blob": True, "filesystem_regular": True,
        "non_symlink": True, "safe_descendant": True,
        "expected_sha256": expected, "base_tree_sha256": expected,
        "filesystem_sha256": expected, "source_verified": True,
    } for index, (relative, expected) in enumerate(SOURCE_BOUNDARY, 1)]
    expected = {
        "project": "CovaPIE",
        "step": "ADMIT_010 unified adapter contract design gate v1",
        "stage": "covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate_v1",
        "manifest_schema_version": "covapie_admit_010_unified_adapter_contract_manifest_v1",
        "expected_base_commit": BASE,
        "expected_base_subject": SUBJECT,
        "admission_rule_id": RULE_ID,
        "admission_rule_name": RULE_NAME,
        "adapter_id": ADAPTER_ID,
        "formal_evaluator": "evaluate_admit_010", "formal_result_type": "Admit010EvaluationResult",
        "future_adapter_handler": "_evaluate_registered_admit_010",
        "independent_oracle": "classify_admit_010_leakage_group_assignment_provenance_design",
        "candidate_fields": list(CANDIDATE_FIELDS),
        "context_items": list(CONTEXT_ITEMS),
        "current_registered_rule_order": list(CURRENT_ORDER),
        "future_registered_rule_order": list(FUTURE_ORDER),
        "future_callable_discovered_rule_ids": list(FUTURE_ORDER),
        "future_adapter_ready_rule_ids": list(FUTURE_ORDER),
        "future_first_nine_handler_identity_reused": {rule: True for rule in CURRENT_ORDER},
        "known_rule_ids": list(KNOWN_IDS),
        "known_not_registered_rule_ids": list(KNOWN_IDS[10:]),
        "future_exact10_public_dispatch_contract": "new_function_object_same_exact9_signature_reads_successor_local_exact10_registry",
        "runtime_result_type_reused_by_identity": "UnifiedAdmissionRuleEvaluation",
        "runtime_dispatch_error_type_reused_by_identity": "UnifiedAdmissionDispatchError",
        "runtime_public_constants_reused_by_identity": [
            "RESULT_SCHEMA_VERSION", "RESULT_FIELDS", "DISPATCH_ERROR_FIELDS",
            "DISPATCH_ERROR_CODES", "OUTCOME_VOCABULARY",
        ],
        "result_schema_version": SCHEMA,
        "result_fields": list(RESULT_FIELDS),
        "standalone_result_fields": list(SOURCE_FIELDS),
        "dispatch_error_fields": list(ERROR_FIELDS),
        "dispatch_error_codes": list(ERROR_CODES),
        "outcome_vocabulary": list(OUTCOMES),
        "context_routing_order": list(ROUTING_ORDER),
        "context_routing_reasons": dict(CONTEXT_REASONS),
        "context_failure_dispatch_code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        "context_failure_flags": {"known_rule": True, "callable_discovered": True, "adapter_ready": True},
        "batch_context_contract": "exact_none",
        "evaluation_context_contract": "Mapping_single_direct_required_lookup_KeyError_only_missing_original_identity",
        "download_result_context_contract": "exact_none",
        "stage_authorization_context_contract": "exact_none",
        "context_before_candidate": True,
        "candidate_mapping_invalid_reason": CANDIDATE_REASON,
        "adapter_missing_categories": ["required_key_absent"],
        "adapter_missing_reason": MISSING_REASON,
        "formal_positional_argument_order": ["leakage_group_id_object", "leakage_group_assignment_provenance_contract_object"],
        "formal_call_count_after_candidate_gate": 1,
        "oracle_call_count_after_source_validation": 1,
        "original_object_identity_preserved": True,
        "adapter_side_normalization": False,
        "adapter_side_provider_mapping": False,
        "source_type_invalid_reason": SOURCE_TYPE_REASON,
        "source_invariant_invalid_reason": SOURCE_INVARIANT_REASON,
        "source_prevalidated_before_oracle": True,
        "source_exact_type_required": True,
        "source_exact10_full_invariant_validation": True,
        "source_oracle_full_exact10_equality_required": True,
        "no_partial_exact13_on_failure": True,
        "normalized_values_projection": "source.validated_candidate_fields",
        "candidate_invalid_projection": {
            "outcome": "invalid", "passed": False, "blocks_candidate": True,
            "normalized_values": [], "validated_candidate_fields": [],
            "consumed_candidate_fields": list(CANDIDATE_FIELDS),
            "consumed_context_items": list(CONTEXT_ITEMS),
            "evaluator_io_used": False, "adapter_id": ADAPTER_ID,
        },
        "contract_row_count": 62,
        "contract_pass_count": 62,
        "routing_matrix_row_count": 39,
        "routing_matrix_pass_count": 39,
        "routing_matrix_group_counts": {"call": 2, "candidate": 13, "context": 16, "projection": 3, "source": 5},
        "projection_truth_matrix_row_count": 85,
        "projection_truth_matrix_pass_count": 85,
        "projection_truth_matrix_group_counts": {
            "adapter_candidate_invalid": 2, "routing_dispatch": 7,
            "source_validation_failure": 5, "standalone_assignment_id": 5,
            "standalone_assignment_semantics": 9, "standalone_candidate_scalar": 14,
            "standalone_context_type": 4, "standalone_historical_group": 3,
            "standalone_member_count": 6, "standalone_membership": 12,
            "standalone_sample_id": 5, "standalone_sha256": 6,
            "standalone_static_fields": 7,
        },
        "safety_row_count": 35,
        "safety_pass_count": 35,
        "issue_inventory_row_count": 11,
        "issue_inventory_preserved_byte_identical": True,
        "issue_inventory_sha256": SOURCE_BOUNDARY[6][1],
        "coverage_issue_status": "open",
        "coverage_issue_affected_rules": "ADMIT_010–ADMIT_015",
        "coverage_issue_transition": "admit_009_implemented_and_removed_from_open_coverage_scope",
        "leakage_group_id_provider_mapping_validated": False,
        "real_provider_leakage_group_id_count": 0,
        "provider_fields_consumed": [],
        "source_boundary_name": "fixed_ordered_exact15_committed_source_boundary",
        "source_input_count": 15,
        "source_input_paths": [path for path, _ in SOURCE_BOUNDARY],
        "source_input_sha256": dict(SOURCE_BOUNDARY),
        "source_input_verification": source_verification,
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "output_file_count": 6,
        "output_files": list(OUTPUTS),
        "output_sha256": {name: FROZEN_OUTPUT_SHA256[name] for name in OUTPUTS[:5]},
        "output_sha256_excludes_manifest_self_hash": True,
        "stop_boundaries": [
            "adapter_handler_not_implemented", "exact9_runtime_unchanged",
            "admit_010_unregistered", "exact10_runtime_not_implemented",
            "provider_mapping_not_validated", "admit_011_not_started",
            "evaluate_all_rules_not_implemented", "combined_candidate_verdict_not_implemented",
            "real_candidate_evaluation_not_executed", "raw_network_download_forbidden",
            "training_forbidden",
        ],
        "recommended_next_step": "implement_covapie_unified_dispatch_runtime_with_admit_001_to_010_v1",
        "readiness": readiness,
        **readiness,
        "validation_failures": [],
        "all_checks_passed": True,
    }
    if len(expected) != 123 or len(readiness) != 29:
        raise AssertionError("checker-owned Exact123 construction failed")
    return expected


def _verify_manifest(manifest: dict[str, Any]) -> None:
    if type(manifest) is not dict or manifest != _expected_manifest():
        raise AssertionError("Exact123 manifest complete equality")


def _verify_ast() -> None:
    path = ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    assignments = {target.id for node in tree.body if isinstance(node, ast.Assign) for target in node.targets if isinstance(target, ast.Name)}
    if {"_evaluate_registered_admit_010", "evaluate_admission_rule"} & (functions | assignments) or "EVALUATOR_REGISTRY" in assignments:
        raise AssertionError("runtime implementation leaked")
    run_node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name.startswith("run_covapie_"))
    calls = [ast.unparse(node.func) for node in ast.walk(run_node) if isinstance(node, ast.Call)]
    if calls.index("_preflight_output_root") > calls.index("build_design_state") or "_postvalidate_output_root" not in calls:
        raise AssertionError("materializer preflight/postwrite order")
    for token in ("mkstemp", 'suffix=".tmp"', 'os.fdopen(descriptor, "wb")', "os.fsync", "os.replace"):
        if token not in source:
            raise AssertionError(f"atomic materializer drift: {token}")


def _validate_output_tree(output_root: Path = OUTPUT_ROOT, *, enforce_frozen_hashes: bool = True) -> dict[str, str]:
    output_root_was_relative = not output_root.is_absolute()
    root = ROOT / output_root if output_root_was_relative else output_root
    if not _checker_resolved_output_target_is_authorized(
        root, ROOT, output_root_was_relative=output_root_was_relative,
    ):
        raise AssertionError("output target resolved containment invalid")
    mode = os.lstat(root).st_mode
    entries = tuple(root.iterdir())
    if not stat.S_ISDIR(mode) or stat.S_ISLNK(mode) or {entry.name for entry in entries} != set(OUTPUTS):
        raise AssertionError("output inventory")
    if any(not stat.S_ISREG(os.lstat(entry).st_mode) or stat.S_ISLNK(os.lstat(entry).st_mode) for entry in entries):
        raise AssertionError("output entry type")
    hashes = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in OUTPUTS}
    contract = _csv(root / OUTPUTS[0], CONTRACT_COLUMNS)
    routing = _csv(root / OUTPUTS[1], ROUTING_COLUMNS)
    truth = _csv(root / OUTPUTS[2], TRUTH_COLUMNS)
    safety = _csv(root / OUTPUTS[3], SAFETY_COLUMNS)
    issues = _csv(root / OUTPUTS[4], ISSUE_COLUMNS)
    _verify_contract(contract)
    if Counter(row["matrix_group"] for row in routing) != {"context": 16, "candidate": 13, "source": 5, "projection": 3, "call": 2}:
        raise AssertionError("routing natural counts")
    if any(row["case_passed"] != "true" for row in routing):
        raise AssertionError("routing case status")
    _verify_routing(routing)
    _verify_truth(truth)
    if safety != _expected_safety_rows():
        raise AssertionError("Exact35 safety complete equality")
    predecessor_issue = ROOT / SOURCE_BOUNDARY[6][0]
    if (root / OUTPUTS[4]).read_bytes() != predecessor_issue.read_bytes() or len(issues) != 11:
        raise AssertionError("issue byte preservation")
    coverage = {row["issue_id"]: row for row in issues}["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]
    if coverage["affected_rules"] != "|".join(KNOWN_IDS[9:]) or coverage["integration_transition"] != "admit_009_implemented_and_removed_from_open_coverage_scope":
        raise AssertionError("coverage transition drift")
    verification = _verify_sources()
    if list(verification) != _expected_manifest()["source_input_verification"]:
        raise AssertionError("source verification evidence drift")
    manifest = json.loads((root / OUTPUTS[5]).read_text(encoding="utf-8"))
    _verify_manifest(manifest)
    if enforce_frozen_hashes and hashes != FROZEN_OUTPUT_SHA256:
        raise AssertionError("frozen output hash mismatch")
    return hashes


def main() -> int:
    _verify_ast()
    _verify_runtime_identity()
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in OUTPUT_ROOT.iterdir()}
    module = importlib.import_module(MODULE)
    after = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in OUTPUT_ROOT.iterdir()}
    if before != after:
        raise AssertionError("import side effect")
    hashes = _validate_output_tree()
    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        module.run_covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate_v1(Path(first), repo_root=ROOT)
        module.run_covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate_v1(Path(second), repo_root=ROOT)
        first_bytes = {name: (Path(first) / name).read_bytes() for name in OUTPUTS}
        second_bytes = {name: (Path(second) / name).read_bytes() for name in OUTPUTS}
        if first_bytes != second_bytes:
            raise AssertionError("double materialization differs")
        _validate_output_tree(Path(first), enforce_frozen_hashes=False)
        if any(hashlib.sha256(first_bytes[name]).hexdigest() != hashes[name] for name in OUTPUTS):
            raise AssertionError("materialization differs from frozen output")
    print(json.dumps({"checked": True, "output_sha256": hashes}, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
