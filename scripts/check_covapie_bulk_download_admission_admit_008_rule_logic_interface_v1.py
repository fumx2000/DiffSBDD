#!/usr/bin/env python3
"""Fail-closed independent checker for ADMIT_008 standalone evaluator v1."""

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
    covapie_bulk_download_admission_admit_008_rule_logic_interface as interface,
)
from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate
    as committed_oracle,
)


EXPECTED_BASE_COMMIT = "96039c9a69c4973461307aed78ee6ec931896a7d"
EXPECTED_BASE_SUBJECT = "add CovaPIE ADMIT_008 topology restoration disposition enum contract v1"
CHECKER_ENUM = (
    "approved_restoration_template", "explicit_manual_review_approved",
    "manual_review_required", "quarantine_required",
)
CHECKER_ALLOWED = CHECKER_ENUM[:2]
CHECKER_SYNTAX = r"[a-z][a-z0-9_]{0,63}"
CHECKER_SCALAR_REASONS = (
    "TOPOLOGY_RESTORATION_DISPOSITION_TYPE_INVALID",
    "TOPOLOGY_RESTORATION_DISPOSITION_EMPTY",
    "TOPOLOGY_RESTORATION_DISPOSITION_NON_ASCII",
    "TOPOLOGY_RESTORATION_DISPOSITION_SYNTAX_INVALID",
    "TOPOLOGY_RESTORATION_DISPOSITION_UNKNOWN",
)
CHECKER_CONTEXT_REASONS = (
    "ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS_TYPE_INVALID",
    "ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS_CONTENT_INVALID",
)
CHECKER_BLOCKED = {
    "manual_review_required": "TOPOLOGY_RESTORATION_MANUAL_REVIEW_REQUIRED",
    "quarantine_required": "TOPOLOGY_RESTORATION_QUARANTINE_REQUIRED",
}
CHECKER_CANDIDATE_FIELDS = ("topology_restoration_disposition",)
CHECKER_CONTEXT_ITEMS = ("allowed_topology_restoration_dispositions",)
CHECKER_RESULT_FIELDS = (
    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",
    "canonical_topology_restoration_disposition", "validated_candidate_fields",
    "consumed_candidate_fields", "consumed_context_items", "evaluator_io_used",
)
CHECKER_GROUPS = {"canonical": 4, "scalar_type": 6, "empty_syntax": 11, "unknown": 5, "context": 12}
CHECKER_CONTRACT_FILENAME = "covapie_admit_008_rule_logic_interface_contract.csv"
CHECKER_TRUTH_FILENAME = "covapie_admit_008_rule_logic_interface_truth_matrix.csv"
CHECKER_SOURCE_AUDIT_FILENAME = "covapie_admit_008_rule_logic_interface_source_boundary_audit.csv"
CHECKER_SAFETY_FILENAME = "covapie_admit_008_rule_logic_interface_safety_audit.csv"
CHECKER_ISSUE_FILENAME = "covapie_admit_008_rule_logic_interface_issue_readiness_inventory.csv"
CHECKER_MANIFEST_FILENAME = "covapie_admit_008_rule_logic_interface_manifest.json"
CHECKER_CSV_OUTPUTS = (
    CHECKER_CONTRACT_FILENAME, CHECKER_TRUTH_FILENAME, CHECKER_SOURCE_AUDIT_FILENAME,
    CHECKER_SAFETY_FILENAME, CHECKER_ISSUE_FILENAME,
)
CHECKER_OUTPUT_FILES = (*CHECKER_CSV_OUTPUTS, CHECKER_MANIFEST_FILENAME)
CHECKER_CONTRACT_COLUMNS = (
    "contract_id", "contract_kind", "contract_subject", "contract_value", "contract_status",
)
CHECKER_TRUTH_COLUMNS = (
    "case_id", "case_group", "scalar_input_kind", "scalar_input_display",
    "context_input_kind", "context_input_display", "expected_full_result",
    "observed_full_result", "committed_oracle_full_result",
    "production_oracle_equality", "case_passed",
)
CHECKER_SOURCE_AUDIT_COLUMNS = (
    "source_order", "source_relative_path", "source_kind", "boundary_necessity",
    "tracked", "base_tree_blob", "filesystem_regular", "non_symlink",
    "expected_sha256", "base_tree_sha256", "filesystem_sha256", "source_boundary_passed",
)
CHECKER_SAFETY_COLUMNS = (
    "safety_item", "expected_executed", "observed_executed", "safety_passed",
)
CHECKER_ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status",
    "blocking_scope", "blocking_reason", "issue_origin", "integration_transition", "issue_count",
)
EXPECTED_SOURCE_PATHS = (
    "src/covalent_ext/covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1/covapie_admit_008_topology_restoration_disposition_enum_contract_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1/covapie_admit_008_topology_restoration_disposition_enum_registry.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1/covapie_admit_008_topology_restoration_disposition_validation_truth_matrix.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1/covapie_admit_008_topology_restoration_disposition_category_mapping_matrix.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_topology_restoration_disposition_enum_contract_design_gate_v1/covapie_admit_008_topology_restoration_disposition_issue_readiness_inventory.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_008_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_008_formal_evaluator_preconditions_manifest.json",
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1/covapie_admit_001_to_007_runtime_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007_v1/covapie_admit_001_to_007_runtime_issue_inventory.csv",
    "src/covalent_ext/covapie_bulk_download_admission_admit_007_rule_logic_interface.py",
)
EXPECTED_SOURCE_SHA256 = dict(zip(EXPECTED_SOURCE_PATHS, (
    "d4b2480e5d1cff17377fa0856eeac007629c4db1e5cdb413e4ea83771d08461d",
    "4da97951abe63d46ded0ad5ffc6048e1a1c40eb2fdedd3553de094ac1ad0c85b",
    "38e41ef09b62848e55e6d43fa2ee65ecc3b24378fd8ac9ca72fd2e313261556a",
    "d15cc2f468b158bdd0871386af041231f563af34ff394c2d25e8b5797fa3599b",
    "f449e7441045f52a2222f70f2b7378446424ea46610859641ae2baf5e4565be4",
    "229251600f0c6ae389633fff86af8859280b86664521ecce04c494906dc39695",
    "e93c43df4f64b6ce70c19c526546d3b1090c55f9150a944a76109ed0038cc136",
    "d9fb64a473de1c456115c871a10b06d16f80dac9dc04f87302e43cc01a40a0cd",
    "0a4cb44812ff5398ffba9a077f1217db3da3624d870922eec87848b60091c96e",
    "47de07417697808b044d30260f153ec7e5d46fb7c5b0e2c1f41187bcb09b89a0",
    "ce5cbf09765e8b12db162458ca9518d71d431b175f3225e5558a8b57fdd133f6",
), strict=True))
EXPECTED_OUTPUT_SHA256 = {
    CHECKER_CONTRACT_FILENAME: "62fdcf8c18f5baf3b08cd29515804abba7543d5da21056d2d93a392d5c188ac9",
    CHECKER_TRUTH_FILENAME: "a78510cf512782f9bd586e040d26a7fb459ba8b0e1eec310195b417cd0b9c636",
    CHECKER_SOURCE_AUDIT_FILENAME: "5fc2c67e7d2e4aecb6d55029314ad7f93456ab0e0ce44bd00071cec3c83d275f",
    CHECKER_SAFETY_FILENAME: "f88c6d23bfa3c5b52c09ddd37af08991d027868cdd2b1ffc42fe586db53542c9",
    CHECKER_ISSUE_FILENAME: "229251600f0c6ae389633fff86af8859280b86664521ecce04c494906dc39695",
    CHECKER_MANIFEST_FILENAME: "ae5fc1c5aa28618765ed07fe5aae67c02d31e7650fb5921dae954c0a3cfefd7e",
}


@dataclass(frozen=True)
class CheckerExpectedResult:
    admission_rule_id: str
    outcome: str
    passed: bool
    blocks_candidate: bool
    reason: str
    canonical_topology_restoration_disposition: str
    validated_candidate_fields: tuple[tuple[str, str], ...]
    consumed_candidate_fields: tuple[str, ...]
    consumed_context_items: tuple[str, ...]
    evaluator_io_used: bool


class _StringSubclass(str):
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


def _checker_scalar(scalar: object) -> tuple[str, str]:
    if type(scalar) is not str:
        return "", CHECKER_SCALAR_REASONS[0]
    if scalar == "":
        return "", CHECKER_SCALAR_REASONS[1]
    if not all(ord(character) < 128 for character in scalar):
        return "", CHECKER_SCALAR_REASONS[2]
    if re.fullmatch(CHECKER_SYNTAX, scalar, flags=re.ASCII) is None:
        return "", CHECKER_SCALAR_REASONS[3]
    if scalar not in CHECKER_ENUM:
        return "", CHECKER_SCALAR_REASONS[4]
    return scalar, ""


def _checker_context(context: object) -> str:
    if type(context) is not tuple:
        return CHECKER_CONTEXT_REASONS[0]
    if len(context) != 2 or any(type(member) is not str for member in context) or context != CHECKER_ALLOWED:
        return CHECKER_CONTEXT_REASONS[1]
    return ""


def _checker_expected(scalar: object, context: object) -> CheckerExpectedResult:
    canonical, scalar_reason = _checker_scalar(scalar)
    if scalar_reason:
        outcome, reason = "invalid", scalar_reason
    else:
        context_reason = _checker_context(context)
        if context_reason:
            outcome, reason = "invalid", context_reason
        elif canonical in CHECKER_BLOCKED:
            outcome, reason = "blocked", CHECKER_BLOCKED[canonical]
        else:
            outcome, reason = "passed", ""
    validated = () if canonical == "" else ((CHECKER_CANDIDATE_FIELDS[0], canonical),)
    return CheckerExpectedResult(
        "ADMIT_008", outcome, outcome == "passed", outcome != "passed", reason,
        canonical, validated, CHECKER_CANDIDATE_FIELDS, CHECKER_CONTEXT_ITEMS, False,
    )


def _oracle_expected(scalar: object, context: object) -> CheckerExpectedResult:
    design = committed_oracle.classify_admit_008_topology_restoration_disposition_design(scalar, context)
    outcome = design.admit_008
    return CheckerExpectedResult(
        "ADMIT_008", outcome.outcome, outcome.passed, outcome.blocks_candidate,
        outcome.reason, outcome.canonical_value, outcome.validated_candidate_fields,
        CHECKER_CANDIDATE_FIELDS, CHECKER_CONTEXT_ITEMS, False,
    )


def _display(value: object) -> str:
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


def _definitions() -> tuple[tuple[str, str, object, str, object], ...]:
    exact = CHECKER_ALLOWED
    scalars = (
        ("canonical_approved_template", "canonical", CHECKER_ENUM[0]),
        ("canonical_manual_approved", "canonical", CHECKER_ENUM[1]),
        ("canonical_manual_required", "canonical", CHECKER_ENUM[2]),
        ("canonical_quarantine", "canonical", CHECKER_ENUM[3]),
        ("type_none", "scalar_type", None), ("type_int", "scalar_type", 7),
        ("type_bool", "scalar_type", True),
        ("type_str_subclass", "scalar_type", _StringSubclass(CHECKER_ENUM[0])),
        ("type_list", "scalar_type", [CHECKER_ENUM[0]]),
        ("type_mapping", "scalar_type", {"value": CHECKER_ENUM[0]}),
        ("empty", "empty_syntax", ""), ("whitespace", "empty_syntax", " "),
        ("leading_whitespace", "empty_syntax", " approved_restoration_template"),
        ("trailing_whitespace", "empty_syntax", "approved_restoration_template "),
        ("uppercase", "empty_syntax", "Approved_restoration_template"),
        ("hyphen", "empty_syntax", "approved-restoration-template"),
        ("dot", "empty_syntax", "approved.restoration"),
        ("slash", "empty_syntax", "approved/restoration"),
        ("non_ascii", "empty_syntax", "approved_restoratión"),
        ("over_length", "empty_syntax", "a" * 65),
        ("leading_digit", "empty_syntax", "1approved"),
        ("unknown_valid", "unknown", "unregistered_disposition"),
        ("unknown_approved_looking", "unknown", "approved_manual_review"),
        ("unknown_manual_review_looking", "unknown", "manual_review_approved"),
        ("unknown_other", "unknown", "other"), ("unknown_unknown", "unknown", "unknown"),
    )
    contexts = (
        ("context_exact_tuple", exact), ("context_none", None),
        ("context_list", list(exact)), ("context_set", set(exact)),
        ("context_frozenset", frozenset(exact)),
        ("context_reversed", tuple(reversed(exact))), ("context_missing", exact[:1]),
        ("context_duplicate", (exact[0], exact[0])),
        ("context_blocked_added", (*exact, CHECKER_ENUM[2])),
        ("context_unknown", (*exact, "unknown")),
        ("context_str_subclass_member", (_StringSubclass(exact[0]), exact[1])),
        ("context_extra", (*exact, "explicit_approval")),
    )
    result = [(name, group, scalar, "exact_tuple", exact) for name, group, scalar in scalars]
    result.extend((name, "context", CHECKER_ENUM[0], name.removeprefix("context_"), context) for name, context in contexts)
    return tuple(result)


def _expected_truth_rows() -> list[dict[str, str]]:
    rows = []
    for index, (name, group, scalar, context_kind, context) in enumerate(_definitions(), 1):
        expected = _checker_expected(scalar, context)
        oracle = _oracle_expected(scalar, context)
        observed = interface.evaluate_admit_008(scalar, context)
        expected_dict = _result_dict(expected)
        oracle_dict = _result_dict(oracle)
        observed_dict = _result_dict(observed)
        _assert(expected_dict == oracle_dict == observed_dict, f"three-way Exact10 mismatch row {index}")
        full = json.dumps(expected_dict, separators=(",", ":"))
        rows.append({
            "case_id": f"CASE_{index:03d}_{name}", "case_group": group,
            "scalar_input_kind": type(scalar).__name__, "scalar_input_display": _display(scalar),
            "context_input_kind": context_kind, "context_input_display": _display(context),
            "expected_full_result": full, "observed_full_result": full,
            "committed_oracle_full_result": full,
            "production_oracle_equality": "true", "case_passed": "true",
        })
    return rows


def _expected_contract_rows() -> list[dict[str, str]]:
    values = (
        ("API_001", "public_api", "signature", "evaluate_admit_008(topology_restoration_disposition, allowed_topology_restoration_dispositions)"),
        ("API_002", "public_api", "inputs", "two_required_positional_or_keyword_direct_objects"),
        ("API_003", "public_api", "execution", "pure_in_memory_deterministic_no_input_mutation"),
        ("RESULT_001", "result_contract", "type", "exact_frozen_dataclass_no_subclasses"),
        ("RESULT_002", "result_contract", "field_count", "10"),
        ("RESULT_003", "result_contract", "field_order", "|".join(CHECKER_RESULT_FIELDS)),
        ("RESULT_004", "result_contract", "exact_types", "exact_str_bool_tuple_and_string_pairs"),
        ("RESULT_005", "result_contract", "outcomes", "passed|blocked|invalid"),
        ("RESULT_006", "result_contract", "passed", "true_iff_outcome_passed"),
        ("RESULT_007", "result_contract", "blocks_candidate", "true_iff_outcome_not_passed"),
        ("RESULT_008", "result_contract", "reason", "passed_empty_nonpassed_frozen_reason"),
        ("RESULT_009", "result_contract", "canonical_state", "scalar_invalid_empty|exact4_preserved_otherwise"),
        ("RESULT_010", "result_contract", "validated_state", "scalar_invalid_empty|canonical_single_pair"),
        ("RESULT_011", "result_contract", "consumed", "exact_candidate_and_context_tuples"),
        ("RESULT_012", "result_contract", "evaluator_io_used", "exact_false"),
        ("SCALAR_001", "scalar_semantics", "type", "exact_builtin_str"),
        ("SCALAR_002", "scalar_semantics", "precedence", "type|nonempty|ascii|syntax|exact4_membership"),
        ("SCALAR_003", "scalar_semantics", "syntax", CHECKER_SYNTAX),
        ("SCALAR_004", "scalar_semantics", "enum", "|".join(CHECKER_ENUM)),
        ("SCALAR_005", "scalar_semantics", "normalization", "none"),
        ("CONTEXT_001", "context_semantics", "type", "exact_builtin_tuple"),
        ("CONTEXT_002", "context_semantics", "members", "exact_builtin_str"),
        ("CONTEXT_003", "context_semantics", "content", "|".join(CHECKER_ALLOWED)),
        ("CONTEXT_004", "context_semantics", "order_and_cardinality", "exact2_no_extra"),
        ("OUTCOME_001", "rule_semantics", "passed_members", "approved_restoration_template|explicit_manual_review_approved"),
        ("OUTCOME_002", "rule_semantics", "manual_review_required", CHECKER_BLOCKED[CHECKER_ENUM[2]]),
        ("OUTCOME_003", "rule_semantics", "quarantine_required", CHECKER_BLOCKED[CHECKER_ENUM[3]]),
        ("OUTCOME_004", "rule_semantics", "blocked_reason_bijection", "two_distinct_exact_reasons"),
        ("OUTCOME_005", "rule_semantics", "precedence", "scalar_failure|context_failure|canonical_classification"),
        ("REASON_001", "rule_semantics", "historical_lowercase", "topology_restoration_unapproved_not_used"),
        ("MISSING_001", "standalone_boundary", "candidate_missing", "adapter_owned_not_standalone"),
        ("PROVIDER_001", "provider_boundary", "fields", "restoration_rule_and_provenance_not_consumed"),
        ("PROVIDER_002", "provider_boundary", "real_values", "zero_mapping_unvalidated"),
        ("ORACLE_001", "oracle_contract", "production", "does_not_import_or_call_design_oracle"),
        ("ORACLE_002", "oracle_contract", "attestation", "checker_and_tests_compare_complete_exact10"),
        ("BOUNDARY_001", "authorization_boundary", "excluded", "adapter|runtime|registration|admit009|aggregation|real_evaluation"),
        ("BOUNDARY_002", "authorization_boundary", "operations", "no_raw_network_download_model_training"),
    )
    return [{"contract_id": i, "contract_kind": k, "contract_subject": s, "contract_value": v, "contract_status": "frozen"} for i, k, s, v in values]


BOUNDARY_NECESSITY = (
    "normative Exact4/Exact2 definitions and independent oracle identity",
    "committed enum contract counts, precedence, readiness, and hashes",
    "ordered Exact4 registry and exact blocked-reason mapping",
    "complete committed Exact38 semantic expectation corpus",
    "Exact12 policy boundary with no real provider execution",
    "authoritative Exact11 successor issue inventory preservation baseline",
    "historical precondition and zero-provider-value boundary",
    "current literal Exact7 runtime and absent ADMIT_008 registration",
    "current Exact7 runtime readiness and output boundary",
    "current runtime Exact11 issue boundary cross-check",
    "mature ADMIT_007 standalone structural precedent",
)


def _expected_source_rows() -> list[dict[str, str]]:
    return [{
        "source_order": str(index), "source_relative_path": path,
        "source_kind": Path(path).suffix.lstrip("."), "boundary_necessity": BOUNDARY_NECESSITY[index - 1],
        "tracked": "true", "base_tree_blob": "true", "filesystem_regular": "true", "non_symlink": "true",
        "expected_sha256": EXPECTED_SOURCE_SHA256[path], "base_tree_sha256": EXPECTED_SOURCE_SHA256[path],
        "filesystem_sha256": EXPECTED_SOURCE_SHA256[path], "source_boundary_passed": "true",
    } for index, path in enumerate(EXPECTED_SOURCE_PATHS, 1)]


EXECUTED = (
    "standalone_evaluator_implementation", "exact10_result_validation", "scalar_validation",
    "context_validation", "exact38_synthetic_truth", "independent_oracle_equivalence",
    "source_verification", "evaluator_pure_in_memory_audit",
)
NOT_EXECUTED = (
    "provider_mapping", "provider_values", "unified_adapter", "exact7_runtime_modification",
    "admit_008_registration", "admit_009", "evaluate_all_rules", "combined_candidate_verdict",
    "real_candidate_evaluation", "raw_read", "network", "bulk_download", "checkpoint",
    "torch_numpy_rdkit", "model_forward_loss", "training_fine_tune", "parameter_update",
)


def _expected_safety_rows() -> list[dict[str, str]]:
    return [{"safety_item": item, "expected_executed": _bool(done), "observed_executed": _bool(done), "safety_passed": "true"} for item, done in (
        *((item, True) for item in EXECUTED), *((item, False) for item in NOT_EXECUTED)
    )]


TRUE_READINESS = (
    "admit_008_standalone_evaluator_implemented", "admit_008_scalar_semantics_implemented",
    "admit_008_context_semantics_implemented", "admit_008_reason_outcome_contract_implemented",
    "admit_008_formal_result_contract_frozen", "admit_008_synthetic_truth_matrix_passed",
    "admit_008_independent_semantic_oracle_attested", "evaluator_call_graph_pure_in_memory",
    "admit_008_provider_mapping_boundary_preserved", "ready_for_admit_008_unified_adapter_contract_design",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "real_provider_topology_disposition_mapping_validated", "real_provider_value_count_nonzero",
    "admit_008_unified_adapter_contract_frozen", "admit_008_unified_adapter_implemented",
    "admit_008_registered_in_engine", "exact7_runtime_modified",
    "admit_009_standalone_evaluator_implemented", "admit_009_to_015_registered_in_engine",
    "all_15_rules_covered", "evaluate_all_rules_implemented", "combined_candidate_verdict_contract_frozen",
    "combined_candidate_verdict_implemented", "cross_rule_precedence_frozen", "real_candidate_evaluation",
    "exact11_real_rows_evaluated", "ready_for_bulk_download_now", "ready_for_training", "ready_to_train_now",
)
CHECKER_READINESS = {**{key: True for key in TRUE_READINESS}, **{key: False for key in FALSE_READINESS}}


def _csv(path: Path, header: tuple[str, ...]) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"), newline=""))
    _assert(tuple(reader.fieldnames or ()) == header, f"CSV header {path.name}")
    rows = [dict(row) for row in reader]
    _assert(all(tuple(row) == header and all(value is not None for value in row.values()) for row in rows), f"CSV rows {path.name}")
    return rows


def _read_verified_sources() -> dict[str, bytes]:
    subject = subprocess.run(["git", "show", "-s", "--format=%s", EXPECTED_BASE_COMMIT], cwd=REPO_ROOT, text=True, capture_output=True)
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, "HEAD"], cwd=REPO_ROOT)
    _assert(subject.returncode == 0 and subject.stdout.strip() == EXPECTED_BASE_SUBJECT and ancestor.returncode == 0, "base lineage")
    for path in EXPECTED_SOURCE_PATHS:
        metadata = os.lstat(REPO_ROOT / path)
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", "--", path], cwd=REPO_ROOT, capture_output=True)
        tree = subprocess.run(["git", "ls-tree", EXPECTED_BASE_COMMIT, "--", path], cwd=REPO_ROOT, text=True, capture_output=True)
        values = tree.stdout.split("\t", 1)[0].split()
        _assert(tracked.returncode == tree.returncode == 0 and len(values) == 3 and values[1] == "blob", f"source structure {path}")
        _assert(stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode), f"source file {path}")
    result = {}
    for path in EXPECTED_SOURCE_PATHS:
        filesystem = (REPO_ROOT / path).read_bytes()
        base = subprocess.run(["git", "show", f"{EXPECTED_BASE_COMMIT}:{path}"], cwd=REPO_ROOT, capture_output=True)
        digest = EXPECTED_SOURCE_SHA256[path]
        _assert(base.returncode == 0 and hashlib.sha256(base.stdout).hexdigest() == hashlib.sha256(filesystem).hexdigest() == digest, f"source SHA {path}")
        result[path] = filesystem
    return result


def _expected_manifest(output_sha: dict[str, str]) -> dict[str, Any]:
    groups = dict(CHECKER_GROUPS)
    readiness = dict(CHECKER_READINESS)
    verification = [{
        "source_order": index, "source_relative_path": path, "tracked": True,
        "base_tree_blob": True, "filesystem_regular": True, "non_symlink": True,
        "expected_sha256": EXPECTED_SOURCE_SHA256[path], "base_tree_sha256": EXPECTED_SOURCE_SHA256[path],
        "filesystem_sha256": EXPECTED_SOURCE_SHA256[path], "source_verified": True,
    } for index, path in enumerate(EXPECTED_SOURCE_PATHS, 1)]
    return {
        "project": "CovaPIE", "step": "ADMIT_008 standalone evaluator interface v1",
        "stage": "covapie_bulk_download_admission_admit_008_rule_logic_interface_v1",
        "manifest_schema_version": "covapie_admit_008_rule_logic_interface_manifest_v1",
        "expected_base_commit": EXPECTED_BASE_COMMIT, "expected_base_subject": EXPECTED_BASE_SUBJECT,
        "admission_rule_id": "ADMIT_008", "admission_rule_name": "topology_restoration_disposition",
        "candidate_field": CHECKER_CANDIDATE_FIELDS[0], "context_item": CHECKER_CONTEXT_ITEMS[0],
        "public_api": "evaluate_admit_008(topology_restoration_disposition, allowed_topology_restoration_dispositions)",
        "public_signature_parameters": [*CHECKER_CANDIDATE_FIELDS, *CHECKER_CONTEXT_ITEMS],
        "public_signature_required_positional_or_keyword": True,
        "result_type": "Admit008EvaluationResult", "result_field_count": 10,
        "result_fields": list(CHECKER_RESULT_FIELDS), "outcome_vocabulary": ["passed", "blocked", "invalid"],
        "reason_vocabulary": ["", *CHECKER_SCALAR_REASONS, *CHECKER_CONTEXT_REASONS, *CHECKER_BLOCKED.values()],
        "canonical_enum_members": list(CHECKER_ENUM), "allowed_topology_restoration_dispositions": list(CHECKER_ALLOWED),
        "canonical_syntax": CHECKER_SYNTAX,
        "scalar_validation_precedence": ["exact_builtin_str", "nonempty", "ascii", "syntax", "exact4_membership"],
        "scalar_validation_reasons": list(CHECKER_SCALAR_REASONS),
        "context_validation_precedence": ["exact_builtin_tuple", "exact_builtin_str_members", "exact2_content_and_order"],
        "context_validation_reasons": list(CHECKER_CONTEXT_REASONS),
        "evaluator_precedence": ["scalar_failure", "context_failure", "canonical_member_classification"],
        "passed_members": list(CHECKER_ALLOWED), "blocked_reason_mapping": dict(CHECKER_BLOCKED),
        "historical_lowercase_reason_used": False, "scalar_invalid_canonical_empty": True,
        "canonical_context_invalid_retains_validated_pair": True, "passed_and_blocked_retain_validated_pair": True,
        "normalization_applied": False, "candidate_mapping_accepted": False,
        "candidate_key_missing_handled_by_standalone": False, "provider_fields_consumed": [],
        "real_provider_value_count": 0, "real_provider_mapping_executed": False,
        "independent_semantic_oracle": "classify_admit_008_topology_restoration_disposition_design",
        "independent_semantic_oracle_attested": True, "production_oracle_call": False,
        "evaluator_call_graph": ["evaluate_admit_008", "_validate_scalar", "_validate_context", "_result"],
        "evaluator_call_graph_pure_in_memory": True,
        "truth_matrix_row_count": 38, "truth_matrix_pass_count": 38, "truth_matrix_group_counts": groups,
        "contract_row_count": 37, "contract_pass_count": 37,
        "source_boundary_name": "fixed_ordered_exact11_committed_source_boundary",
        "source_input_count": 11, "source_input_paths": list(EXPECTED_SOURCE_PATHS),
        "source_input_sha256": dict(EXPECTED_SOURCE_SHA256), "source_input_verification": verification,
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "source_audit_row_count": 11, "source_audit_pass_count": 11,
        "issue_inventory_row_count": 11, "issue_inventory_preserved_exactly": True,
        "issue_inventory_sha256": EXPECTED_SOURCE_SHA256[EXPECTED_SOURCE_PATHS[5]],
        "unified_engine_coverage_issue_still_includes_admit_008": True,
        "safety_row_count": 25, "safety_pass_count": 25,
        "output_files": list(CHECKER_OUTPUT_FILES), "output_file_count": 6,
        "output_sha256": output_sha, "output_sha256_excludes_manifest_self_hash": True,
        "readiness": readiness, **readiness,
        "all_source_boundary_checks_passed": True, "all_predecessor_contract_checks_passed": True,
        "all_result_contract_checks_passed": True, "all_semantic_checks_passed": True,
        "all_truth_matrix_checks_passed": True, "all_issue_checks_passed": True,
        "all_safety_checks_passed": True, "all_checks_passed": True,
        "stop_boundaries": ["no_provider_mapping", "no_unified_adapter", "no_runtime_modification", "no_admit_008_registration", "no_admit_009", "no_evaluate_all_rules", "no_combined_candidate_verdict", "no_real_candidate_evaluation", "no_raw_network_download", "no_model_forward_loss_training"],
        "recommended_next_step": "design_covapie_admit_008_unified_adapter_contract_v1", "validation_failures": [],
    }


def _called_names(node: ast.AST) -> set[str]:
    result = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                result.add(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                result.add(child.func.attr)
    return result


def _check_call_graph() -> None:
    tree = ast.parse((REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_008_rule_logic_interface.py").read_text())
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    pending = ["evaluate_admit_008"]
    closure = set()
    banned = {"classify_admit_008_topology_restoration_disposition_design", "build_interface_state", "build_frozen_source_snapshot", "read_bytes", "read_text", "open", "run", "write", "provider"}
    while pending:
        name = pending.pop()
        if name in closure:
            continue
        closure.add(name)
        calls = _called_names(functions[name])
        _assert(not calls.intersection(banned), f"banned evaluator call {calls.intersection(banned)}")
        pending.extend(call for call in calls if call in functions)
    _assert(closure == {"evaluate_admit_008", "_validate_scalar", "_validate_context", "_result"}, "evaluator closure")
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            _assert("topology_restoration_disposition_enum_contract_design_gate" not in (node.module or ""), "production oracle import")
        if isinstance(node, ast.Import):
            _assert(all("topology_restoration_disposition_enum_contract_design_gate" not in alias.name for alias in node.names), "production oracle import")


def _check_independent_builders() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    independent = (
        "_bool", "_checker_scalar", "_checker_context", "_checker_expected",
        "_display", "_definitions", "_expected_contract_rows",
        "_expected_source_rows", "_expected_safety_rows", "_expected_manifest",
    )
    banned = {
        "interface", "_truth_definitions", "_independent_expected", "_truth_rows",
        "CONTRACT_COLUMNS", "TRUTH_COLUMNS", "SOURCE_AUDIT_COLUMNS", "SAFETY_COLUMNS",
        "ISSUE_COLUMNS", "SOURCE_PATHS", "SOURCE_SHA256", "OUTPUT_FILES",
    }
    for name in independent:
        _assert(name in functions, f"missing independent builder {name}")
        for node in ast.walk(functions[name]):
            if isinstance(node, ast.Name):
                _assert(node.id not in banned, f"independent builder leak {name}:{node.id}")
            if isinstance(node, ast.Attribute):
                root = node.value
                while isinstance(root, ast.Attribute):
                    root = root.value
                _assert(not isinstance(root, ast.Name) or root.id != "interface", f"independent interface leak {name}")


def _check_public_contract() -> None:
    signature = inspect.signature(interface.evaluate_admit_008)
    parameters = tuple(signature.parameters.values())
    _assert(tuple(parameter.name for parameter in parameters) == (*CHECKER_CANDIDATE_FIELDS, *CHECKER_CONTEXT_ITEMS), "signature names")
    _assert(all(parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD and parameter.default is inspect.Parameter.empty for parameter in parameters), "signature kinds/defaults")
    _assert(signature.return_annotation == "Admit008EvaluationResult", "return annotation")
    _assert(tuple(field.name for field in fields(interface.Admit008EvaluationResult)) == CHECKER_RESULT_FIELDS, "Exact10 fields")
    _assert(interface.CANONICAL_ENUM_MEMBERS == CHECKER_ENUM and interface.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS == CHECKER_ALLOWED, "Exact4/Exact2")
    _assert(interface.BLOCKED_REASONS == CHECKER_BLOCKED, "blocked reasons")
    _assert("topology_restoration_unapproved" not in interface.REASON_VOCABULARY, "historical reason leaked")
    original = interface._validate_context
    interface._validate_context = lambda _: (_ for _ in ()).throw(AssertionError("context reached"))
    try:
        observed = interface.evaluate_admit_008(None, object())
    finally:
        interface._validate_context = original
    _assert(observed.reason == CHECKER_SCALAR_REASONS[0], "scalar short circuit")


def _validate_output_tree(root: Path, *, enforce_frozen_hashes: bool = True) -> dict[str, Any]:
    _assert(root.is_dir() and not root.is_symlink(), "output root")
    entries = tuple(root.iterdir())
    _assert({entry.name for entry in entries} == set(CHECKER_OUTPUT_FILES), "output set")
    _assert(all(entry.is_file() and not entry.is_symlink() for entry in entries), "output entries")
    sources = _read_verified_sources()
    contracts = _csv(root / CHECKER_CONTRACT_FILENAME, CHECKER_CONTRACT_COLUMNS)
    truth = _csv(root / CHECKER_TRUTH_FILENAME, CHECKER_TRUTH_COLUMNS)
    source_rows = _csv(root / CHECKER_SOURCE_AUDIT_FILENAME, CHECKER_SOURCE_AUDIT_COLUMNS)
    safety = _csv(root / CHECKER_SAFETY_FILENAME, CHECKER_SAFETY_COLUMNS)
    issues = _csv(root / CHECKER_ISSUE_FILENAME, CHECKER_ISSUE_COLUMNS)
    expected_truth = _expected_truth_rows()
    _assert(contracts == _expected_contract_rows(), "contract semantics")
    _assert(truth == expected_truth, "truth semantics")
    _assert(source_rows == _expected_source_rows(), "source semantics")
    _assert(safety == _expected_safety_rows(), "safety semantics")
    _assert((root / CHECKER_ISSUE_FILENAME).read_bytes() == sources[EXPECTED_SOURCE_PATHS[5]], "issue bytes")
    _assert(len(issues) == 11, "issue count")
    issue_map = {row["issue_id"]: row for row in issues}
    _assert(issue_map["TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED"]["status"] == "resolved", "enum issue")
    _assert(issue_map["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"].startswith("ADMIT_008|"), "coverage transition")
    output_sha = {name: _sha(root / name) for name in CHECKER_CSV_OUTPUTS}
    manifest = json.loads((root / CHECKER_MANIFEST_FILENAME).read_text())
    expected_manifest = _expected_manifest(output_sha)
    _assert(set(manifest) == set(expected_manifest), "exact manifest key set")
    _assert(manifest == expected_manifest, "full manifest equality")
    _assert(all(manifest[key] is manifest["readiness"][key] for key in (*TRUE_READINESS, *FALSE_READINESS)), "readiness mirrors")
    if enforce_frozen_hashes:
        hashes = {name: _sha(root / name) for name in CHECKER_OUTPUT_FILES}
        _assert(hashes == EXPECTED_OUTPUT_SHA256, "frozen output SHA")
    return manifest


def _negative_checks(root: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="covapie-admit008-checker-") as temporary:
        temp = Path(temporary)
        for mutation in ("missing", "extra", "symlink", "truth_rehash", "readiness", "provider", "issue"):
            victim = temp / mutation
            shutil.copytree(root, victim)
            if mutation == "missing":
                (victim / CHECKER_CONTRACT_FILENAME).unlink()
            elif mutation == "extra":
                (victim / "extra.txt").write_text("extra")
            elif mutation == "symlink":
                outside = temp / "outside"
                outside.write_text("outside")
                (victim / CHECKER_CONTRACT_FILENAME).unlink()
                (victim / CHECKER_CONTRACT_FILENAME).symlink_to(outside)
            elif mutation == "truth_rehash":
                path = victim / CHECKER_TRUTH_FILENAME
                rows = list(csv.DictReader(io.StringIO(path.read_text(), newline="")))
                rows[0]["observed_full_result"] = rows[1]["observed_full_result"]
                stream = io.StringIO(newline="")
                writer = csv.DictWriter(stream, fieldnames=CHECKER_TRUTH_COLUMNS, lineterminator="\n")
                writer.writeheader(); writer.writerows(rows); path.write_text(stream.getvalue())
                manifest_path = victim / CHECKER_MANIFEST_FILENAME
                manifest = json.loads(manifest_path.read_text())
                manifest["output_sha256"][CHECKER_TRUTH_FILENAME] = _sha(path)
                manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
            elif mutation in ("readiness", "provider"):
                path = victim / CHECKER_MANIFEST_FILENAME
                manifest = json.loads(path.read_text())
                key = "ready_for_training" if mutation == "readiness" else "real_provider_topology_disposition_mapping_validated"
                manifest[key] = manifest["readiness"][key] = True
                if mutation == "provider":
                    manifest["real_provider_value_count"] = 1
                path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
            else:
                path = victim / CHECKER_ISSUE_FILENAME
                path.write_text(path.read_text().replace("ADMIT_008|ADMIT_009", "ADMIT_009", 1))
                manifest_path = victim / CHECKER_MANIFEST_FILENAME
                manifest = json.loads(manifest_path.read_text())
                manifest["output_sha256"][CHECKER_ISSUE_FILENAME] = _sha(path)
                manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
            try:
                _validate_output_tree(victim, enforce_frozen_hashes=False)
            except (AssertionError, OSError, ValueError, json.JSONDecodeError):
                continue
            raise AssertionError(f"negative mutation accepted: {mutation}")


def _silent_imports() -> None:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(SRC_ROOT)
    commands = (
        "import covalent_ext.covapie_bulk_download_admission_admit_008_rule_logic_interface",
        "import importlib.util,sys; p='scripts/check_covapie_bulk_download_admission_admit_008_rule_logic_interface_v1.py'; s=importlib.util.spec_from_file_location('admit008_checker',p); m=importlib.util.module_from_spec(s); sys.modules[s.name]=m; s.loader.exec_module(m)",
    )
    for command in commands:
        result = subprocess.run([sys.executable, "-c", command], cwd=REPO_ROOT, env=environment, text=True, capture_output=True)
        _assert(result.returncode == 0 and result.stdout == result.stderr == "", "silent import")


def main() -> int:
    _check_public_contract()
    definitions = _definitions()
    _assert(len(definitions) == 38, "Exact38")
    groups = {group: sum(row[1] == group for row in definitions) for group in CHECKER_GROUPS}
    _assert(groups == CHECKER_GROUPS, "Exact38 groups")
    _expected_truth_rows()
    _check_call_graph()
    _check_independent_builders()
    output_root = REPO_ROOT / interface.DEFAULT_OUTPUT_ROOT
    first = interface.run_covapie_bulk_download_admission_admit_008_rule_logic_interface_v1(output_root)
    first_bytes = {name: (output_root / name).read_bytes() for name in CHECKER_OUTPUT_FILES}
    second = interface.run_covapie_bulk_download_admission_admit_008_rule_logic_interface_v1(output_root)
    second_bytes = {name: (output_root / name).read_bytes() for name in CHECKER_OUTPUT_FILES}
    _assert(first["manifest"] == second["manifest"] and first_bytes == second_bytes, "double materialization")
    manifest = _validate_output_tree(output_root)
    _negative_checks(output_root)
    _silent_imports()
    print("admit_008_truth_matrix=38/38")
    print("admit_008_truth_groups=canonical:4,scalar_type:6,empty_syntax:11,unknown:5,context:12")
    print("admit_008_contract=37/37")
    print("source_boundary=11/11")
    print("safety_audit=25/25")
    print("exact11_issue_inventory=11/11")
    print(f"manifest_key_count={len(manifest)}")
    print(f"readiness_count={len(manifest['readiness'])}")
    print("real_provider_value_count=0")
    print("real_provider_mapping_validated=false")
    for name in CHECKER_OUTPUT_FILES:
        print(f"sha256 {name} {_sha(output_root / name)}")
    print("ADMIT_008_STANDALONE_EVALUATOR_INTERFACE_CHECK=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
