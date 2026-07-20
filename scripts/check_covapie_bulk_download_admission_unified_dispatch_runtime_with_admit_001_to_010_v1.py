#!/usr/bin/env python3
"""Independent fail-closed checker for the CovaPIE Exact10 runtime."""

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
from collections.abc import Mapping
from dataclasses import fields
from pathlib import Path
from types import MappingProxyType
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = "covalent_ext.covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010"
BASE = "73aa9b4e91e3f80da47da2909eb2702dc04e15c9"
SUBJECT = "add CovaPIE ADMIT_010 unified adapter contract design v1"
STEP = "unified dispatch runtime with ADMIT_001 to ADMIT_010 v1"
STAGE = "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1"
MANIFEST_SCHEMA = "covapie_unified_dispatch_runtime_with_admit_001_to_010_manifest_v1"
OUTPUT_ROOT = ROOT / "data/derived/covalent_small" / STAGE
RULE_ID = "ADMIT_010"
RULE_NAME = "leakage_group_assignment_before_split"
ADAPTER_ID = "covapie_admit_010_unified_adapter_v1"
KNOWN_IDS = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
REGISTERED_IDS = KNOWN_IDS[:10]
EXPECTED_RULE_NAMES = {
    "ADMIT_001": "unique_candidate_identity",
    "ADMIT_002": "valid_pdb_id_format",
    "ADMIT_003": "ligand_or_het_identity_present",
    "ADMIT_004": "covalent_residue_identity_present",
    "ADMIT_005": "cys_sg_scope_only_v1",
    "ADMIT_006": "explicit_covalent_event_evidence",
    "ADMIT_007": "distance_only_inference_forbidden",
    "ADMIT_008": "topology_restoration_disposition",
    "ADMIT_009": "duplicate_identity_precheck",
    "ADMIT_010": "leakage_group_assignment_before_split",
}
EXPECTED_ADAPTER_IDS = {
    "ADMIT_001": "covapie_admit_001_unified_adapter_v1",
    "ADMIT_002": "covapie_admit_002_unified_adapter_v1",
    "ADMIT_003": "covapie_admit_003_unified_adapter_v1",
    "ADMIT_004": "covapie_admit_004_unified_adapter_v1",
    "ADMIT_005": "covapie_admit_005_unified_adapter_v1",
    "ADMIT_006": "covapie_admit_006_unified_adapter_v1",
    "ADMIT_007": "covapie_admit_007_unified_adapter_v1",
    "ADMIT_008": "covapie_admit_008_unified_adapter_v1",
    "ADMIT_009": "covapie_admit_009_unified_adapter_v1",
    "ADMIT_010": "covapie_admit_010_unified_adapter_v1",
}
EXPECTED_RESULT_SCHEMA_VERSION = "covapie_unified_admission_rule_evaluation_v1"
EXPECTED_PUBLIC_DISPATCH_SIGNATURE = (
    "(admission_rule_id: 'str', candidate_record: 'Mapping[str, object]', *, "
    "batch_context: 'Mapping[str, object] | None' = None, evaluation_context: "
    "'Mapping[str, object] | None' = None, download_result_context: "
    "'Mapping[str, object] | None' = None, stage_authorization_context: "
    "'Mapping[str, object] | None' = None) -> 'UnifiedAdmissionRuleEvaluation'"
)
CANDIDATE_FIELDS = ("leakage_group_id",)
CONTEXT_ITEMS = ("leakage_group_assignment_provenance_contract",)
OUTPUTS = (
    "covapie_admit_001_to_010_runtime_contract.csv",
    "covapie_admit_001_to_010_runtime_truth_matrix.csv",
    "covapie_admit_001_to_010_registry_routing_and_oracle_audit.csv",
    "covapie_admit_001_to_010_runtime_safety_audit.csv",
    "covapie_admit_001_to_010_runtime_issue_inventory.csv",
    "covapie_admit_001_to_010_runtime_manifest.json",
)
FROZEN_OUTPUT_SHA256 = dict(
    zip(
        OUTPUTS,
        (
            "da2ccbeef748a9ff503ff1e993bcdfb05ae436f92dcd4d46544c424f4f841874",
            "2d087ef178cd7402fa3d0d40a8a22d2b0a726ed0f49ff2549f6893db15cb20ee",
            "c797c6aad1a9951c61c85379fc2f633aa528bc593dd6f923de9416b7f07ccdbc",
            "2c2ae91713cbd05361db3b0a1e74045cc9b810e06133caceff53e8daf0b5786b",
            "f59eecc7136ebdd148f2c6c6422b7a2bc0637e340322e09bc005eb00355db03c",
            "46dcef1d5e62c5a8904e9ff66b145b6ee9dae88fc406e42d669a8a7002285198",
        ),
        strict=True,
    )
)
FROZEN_SUCCESSOR_TRUTH_ROWS_SHA256 = (
    "f6496ea91f759720a8e19760134ae59e6d8fbdb45a0caed0de35ae1e2a562cf1"
)
SOURCE_BOUNDARY = (
    ("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009.py", "80bdc66d2b0b2a1d761b0a1eb07f644f47535516598c3869f75a92cddafbdb39"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1/covapie_admit_001_to_009_runtime_manifest.json", "b4d5092949292f27310a05ef2c5c77c8036e7ad0474a15b8a0574bc910931dfc"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1/covapie_admit_001_to_009_runtime_contract.csv", "28afebbc6351d10ceeabedb5fdbe99bd3549b784a02682d9875a66b769f12bec"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1/covapie_admit_001_to_009_runtime_truth_matrix.csv", "60bbd1f01390da057a954e3b531cd28ffa97041f38577e49160625218c0186bf"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1/covapie_admit_001_to_009_registry_routing_and_oracle_audit.csv", "6a3471a08d65e0d0d0f6c6cf258016a670e7f324ab5b9ea4a3b8cff7b1723ba9"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1/covapie_admit_001_to_009_runtime_safety_audit.csv", "8109395409a7a26ba483eb84bb14c0db1c19365bad0c96a3d0d9656ef524c344"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1/covapie_admit_001_to_009_runtime_issue_inventory.csv", "bb159a201f103a4cc04087978a7ca2a7bec7574fb9fc55d3cc0b059415f679e6"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_010_rule_logic_interface.py", "05a89049fca65b6f9d9480392eb57b333a1960064fbd6c2c5061efeac3bb9a1c"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_010_rule_logic_interface_v1/covapie_admit_010_rule_logic_interface_manifest.json", "5769c583bc5ade6dbeb81190b20e1774120f7b38dbf53d540f97b50dbf594d54"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_010_rule_logic_interface_v1/covapie_admit_010_rule_logic_interface_contract.csv", "809a591cca7bd5f94920100105dbc6d643d8e73f38dc7692933f244de954d774"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_010_rule_logic_interface_v1/covapie_admit_010_rule_logic_interface_truth_matrix.csv", "c5caa0f398f7d8592b2ef8ab14e4af4c47e9bfd7a06e476f617de55e6c627284"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate.py", "dd2f88da8024d75d9b4fd9f1b8698a402c3395ebbfca6c9f17b0e19b84bb5095"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate_v1/covapie_admit_010_unified_adapter_contract_manifest.json", "6ee42e0baf26ece28df75201521babdf8f9ffe7a89b7544a346f92e5ecd39119"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate_v1/covapie_admit_010_unified_adapter_contract.csv", "2116f5e0afe3e69be7ec5ea6d8c95e14112c1905904f663bf1d6990a41534d81"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate_v1/covapie_admit_010_candidate_projection_and_context_routing_matrix.csv", "044b7812d2b8a53d6d31c303d8c6d0b4cfa308b53cb9d02a16718346e676fdbc"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate_v1/covapie_admit_010_unified_result_projection_truth_matrix.csv", "25a36e3bb08f2c354b1a52382485727bb5ccdf51d1465f087c21c6f622a8ba36"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_010_unified_adapter_contract_design_gate_v1/covapie_admit_010_unified_adapter_issue_readiness_inventory.csv", "779932531b630072ff33721e689a2865defdad477df8335a9950c8e4537476bd"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_010_leakage_group_assignment_provenance_contract_design_gate.py", "cbff1bd3fe4e6d65c9be33a5efee4d80ea1f9310cb7cb73e45dc4e1055a2de05"),
)
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
    "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID",
    "UNIFIED_ADMISSION_RULE_ID_UNKNOWN",
    "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
    "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
    "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
)
OUTCOMES = ("passed", "blocked", "invalid", "rejected")
CONTRACT_COLUMNS = (
    "contract_id", "contract_area", "contract_statement", "expected_value",
    "observed_value", "contract_passed",
)
TRUTH_COLUMNS = (
    "case_id", "case_group", "admission_rule_id", "behavior",
    "expected_result_or_error", "observed_result_or_error", "expected_reason",
    "observed_reason", "formal_call_count", "oracle_call_count",
    "candidate_access_status", "predecessor_handler_identity_status", "case_passed",
)
REGISTRY_COLUMNS = (
    "rule_id", "rule_name", "known_rule", "callable_discovered", "adapter_ready",
    "registered", "adapter_id", "handler_identity_status", "dispatch_disposition",
    "audit_passed",
)
SAFETY_COLUMNS = (
    "safety_item", "expected_executed", "observed_executed", "safety_passed",
)
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity",
    "status", "blocking_scope", "blocking_reason", "issue_origin",
    "integration_transition", "issue_count",
)
TRUE_READINESS = (
    "admit_010_standalone_evaluator_implemented",
    "evaluate_admit_010_implemented",
    "Admit010EvaluationResult_implemented",
    "admit_010_unified_adapter_contract_frozen",
    "admit_010_unified_adapter_implemented",
    "admit_010_registered_in_engine",
    "admit_010_context_routing_runtime_enforced",
    "admit_010_candidate_projection_runtime_enforced",
    "admit_010_source_exact10_validation_runtime_enforced",
    "admit_010_source_oracle_full_exact10_equality_runtime_enforced",
    "admit_010_exact10_to_exact13_projection_runtime_enforced",
    "admit_010_formal_exactly_once_runtime_enforced",
    "admit_010_oracle_exactly_once_runtime_enforced",
    "admit_010_original_object_identity_runtime_enforced",
    "admit_010_key_absent_only_missing_runtime_enforced",
    "admit_010_provider_mapping_boundary_preserved",
    "exact10_reuses_exact9_public_type_identity",
    "exact10_first_nine_handler_identity_preserved",
    "exact10_public_dispatch_new_successor_function",
    "exact10_public_dispatch_signature_matches_exact9",
    "exact10_public_dispatch_uses_local_registry",
    "unified_dispatch_runtime_with_admit_001_to_010_implemented",
    "ready_for_admit_011_formal_evaluator_interface_preconditions_audit",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "leakage_group_id_provider_mapping_validated",
    "real_provider_leakage_group_id_count_nonzero",
    "admit_011_started",
    "all_15_rules_covered",
    "evaluate_all_rules_implemented",
    "combined_candidate_verdict_contract_frozen",
    "combined_candidate_verdict_implemented",
    "cross_rule_precedence_frozen",
    "real_candidate_evaluation",
    "ready_for_bulk_download_now",
    "ready_for_training",
    "ready_to_train_now",
)


def _git(*args: str, text: bool = False) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ("git", *args), cwd=ROOT, capture_output=True, check=False, text=text
    )


def _csv(path: Path, columns: tuple[str, ...]) -> tuple[dict[str, str], ...]:
    reader = csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"), newline=""))
    if tuple(reader.fieldnames or ()) != columns:
        raise AssertionError(f"header mismatch: {path.name}")
    rows = tuple(dict(row) for row in reader)
    if any(tuple(row) != columns or any(value is None for value in row.values()) for row in rows):
        raise AssertionError(f"row shape mismatch: {path.name}")
    return rows


def _verify_sources() -> tuple[dict[str, Any], ...]:
    if len(SOURCE_BOUNDARY) != 18 or len({path for path, _ in SOURCE_BOUNDARY}) != 18:
        raise AssertionError("Exact18 boundary drift")
    if _git("show", "-s", "--format=%s", BASE, text=True).stdout.rstrip("\n") != SUBJECT:
        raise AssertionError("base subject mismatch")
    if _git("merge-base", "--is-ancestor", BASE, "HEAD").returncode:
        raise AssertionError("base is not ancestor")
    resolved_root = ROOT.resolve(strict=True)
    if Path(os.path.abspath(ROOT)) != resolved_root:
        raise AssertionError("repo root resolved containment")
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
            raise AssertionError(f"base blob mismatch: {relative}")
        if not stat.S_ISREG(mode) or stat.S_ISLNK(mode):
            raise AssertionError(f"filesystem source type: {relative}")
        try:
            target.resolve(strict=True).relative_to(resolved_root)
        except (OSError, RuntimeError, ValueError):
            raise AssertionError(f"source containment: {relative}") from None
        structural.append((relative, expected))
    verified = []
    for index, (relative, expected) in enumerate(structural, 1):
        base_bytes = _git("show", f"{BASE}:{relative}").stdout
        filesystem_bytes = (ROOT / relative).read_bytes()
        base_sha = hashlib.sha256(base_bytes).hexdigest()
        filesystem_sha = hashlib.sha256(filesystem_bytes).hexdigest()
        if expected != base_sha or expected != filesystem_sha:
            raise AssertionError(f"source hash mismatch: {relative}")
        verified.append({
            "source_ordinal": index,
            "source_relative_path": relative,
            "tracked": True,
            "base_tree_blob": True,
            "filesystem_regular": True,
            "non_symlink": True,
            "safe_descendant": True,
            "expected_sha256": expected,
            "base_tree_sha256": base_sha,
            "filesystem_sha256": filesystem_sha,
            "source_verified": True,
        })
    return tuple(verified)


def _verify_runtime_identity(runtime: Any) -> None:
    predecessor = runtime.predecessor
    for name in (
        "UnifiedAdmissionRuleEvaluation", "UnifiedAdmissionDispatchError",
        "RESULT_SCHEMA_VERSION", "RESULT_FIELDS", "DISPATCH_ERROR_FIELDS",
        "DISPATCH_ERROR_CODES", "OUTCOME_VOCABULARY",
    ):
        if getattr(runtime, name) is not getattr(predecessor, name):
            raise AssertionError(f"public identity drift: {name}")
    if runtime.evaluate_admission_rule is predecessor.evaluate_admission_rule:
        raise AssertionError("successor dispatcher object reused")
    if inspect.signature(runtime.evaluate_admission_rule) != inspect.signature(predecessor.evaluate_admission_rule):
        raise AssertionError("dispatcher signature drift")
    if runtime.evaluate_admission_rule.__globals__["EVALUATOR_REGISTRY"] is not runtime.EVALUATOR_REGISTRY:
        raise AssertionError("dispatcher does not use local registry")
    if type(runtime.EVALUATOR_REGISTRY) is not MappingProxyType:
        raise AssertionError("registry is not MappingProxyType")
    if tuple(runtime.EVALUATOR_REGISTRY) != REGISTERED_IDS:
        raise AssertionError("registry order drift")
    if any(runtime.EVALUATOR_REGISTRY[rule] is not predecessor.EVALUATOR_REGISTRY[rule] for rule in KNOWN_IDS[:9]):
        raise AssertionError("first-nine handler identity drift")
    if runtime.EVALUATOR_REGISTRY[RULE_ID] is not runtime._evaluate_registered_admit_010:
        raise AssertionError("ADMIT_010 handler identity drift")
    if tuple(runtime.KNOWN_RULE_IDS) != KNOWN_IDS or tuple(runtime.CALLABLE_DISCOVERED_RULE_IDS) != REGISTERED_IDS:
        raise AssertionError("known/callable IDs drift")
    if tuple(runtime.ADAPTER_READY_RULE_IDS) != REGISTERED_IDS or tuple(runtime.LEGACY_ADAPTER_NOT_READY_RULE_IDS) != ():
        raise AssertionError("adapter readiness IDs drift")
    if (
        type(runtime.RULE_NAMES) is not MappingProxyType
        or tuple(runtime.RULE_NAMES) != REGISTERED_IDS
        or dict(runtime.RULE_NAMES) != EXPECTED_RULE_NAMES
    ):
        raise AssertionError("RULE_NAMES identity/semantic mapping drift")
    if (
        type(runtime.ADAPTER_IDS) is not MappingProxyType
        or tuple(runtime.ADAPTER_IDS) != REGISTERED_IDS
        or dict(runtime.ADAPTER_IDS) != EXPECTED_ADAPTER_IDS
    ):
        raise AssertionError("ADAPTER_IDS identity/semantic mapping drift")
    if hasattr(runtime, "evaluate_all_rules") or hasattr(runtime, "combined_candidate_verdict"):
        raise AssertionError("aggregation leaked")


def _verify_ast(runtime: Any) -> None:
    path = Path(runtime.__file__)
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.extend(alias.name for alias in node.names)
    if any("admit_010_unified_adapter_contract_design_gate" in name for name in imported):
        raise AssertionError("adapter-design module imported by runtime")
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    required = {
        "_admit010_context_failure", "_admit010_adapter_failure",
        "_admit010_candidate_invalid", "_prevalidate_admit010_source",
        "_expected_admit010_from_oracle", "_validate_admit010_oracle_equivalence",
        "_project_admit010_exact13", "_evaluate_registered_admit_010",
        "evaluate_admission_rule", "_resolved_output_preflight",
        "_validate_prewrite_output_root",
    }
    if not required <= set(functions):
        raise AssertionError("required runtime helper missing")
    public_closure = {
        "evaluate_admission_rule", "_raise_dispatch_error",
        "_admit010_context_failure", "_admit010_adapter_failure",
        "_admit010_candidate_invalid", "_prevalidate_admit010_source",
        "_expected_admit010_from_oracle", "_validate_admit010_oracle_equivalence",
        "_project_admit010_exact13", "_evaluate_registered_admit_010",
    }
    forbidden = {
        "open", "read_bytes", "read_text", "write_bytes", "write_text", "Path",
        "subprocess", "build_frozen_source_snapshot", "run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1",
        "evaluate_all_rules", "combined_candidate_verdict", "torch", "rdkit",
    }
    for name in public_closure:
        calls = {ast.unparse(node.func) for node in ast.walk(functions[name]) if isinstance(node, ast.Call)}
        if any(call.split(".")[-1] in forbidden for call in calls):
            raise AssertionError(f"public call graph boundary drift: {name}")
    preflight_node = functions["_resolved_output_preflight"]
    preflight_calls = {
        ast.unparse(node.func).split(".")[-1]
        for node in ast.walk(preflight_node)
        if isinstance(node, ast.Call)
    }
    if preflight_calls & {
        "mkdir", "touch", "write", "write_bytes", "write_text", "unlink",
        "replace", "mkstemp", "NamedTemporaryFile",
    }:
        raise AssertionError("output preflight is mutating")
    run_node = functions["run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1"]
    run_source = ast.get_source_segment(source, run_node)
    if run_source is None:
        raise AssertionError("runner source unavailable")
    ordered_tokens = (
        "_resolved_output_preflight(",
        "build_frozen_source_snapshot(",
        "build_runtime_state(",
        "_payloads(",
        "root.mkdir(",
        "_validate_prewrite_output_root(",
        "_atomic_write(",
        "_postvalidate_output_root(",
    )
    positions = tuple(run_source.index(token) for token in ordered_tokens)
    if positions != tuple(sorted(positions)):
        raise AssertionError("materializer preflight/source/payload/mkdir/write order drift")
    for token in ("mkstemp", 'suffix=".tmp"', 'os.fdopen(descriptor, "wb")', "os.fsync", "os.replace"):
        if token not in source:
            raise AssertionError(f"atomic materializer drift: {token}")


class _CountingMapping(Mapping):
    def __init__(self, values: dict[str, object], error: Exception | None = None) -> None:
        self.values = values
        self.error = error
        self.getitem_calls: list[object] = []
        self.iterated = False
        self.get_called = False
        self.contains_called = False

    def __getitem__(self, key: object) -> object:
        self.getitem_calls.append(key)
        if self.error is not None:
            raise self.error
        return self.values[key]  # type: ignore[index]

    def __iter__(self):
        self.iterated = True
        return iter(self.values)

    def __len__(self) -> int:
        return len(self.values)

    def get(self, key: object, default: object = None) -> object:
        self.get_called = True
        return super().get(key, default)

    def __contains__(self, key: object) -> bool:
        self.contains_called = True
        return super().__contains__(key)


class _Bomb(Mapping):
    def __getitem__(self, key: object) -> object:
        raise AssertionError("candidate accessed")

    def __iter__(self):
        raise AssertionError("candidate iterated")

    def __len__(self) -> int:
        raise AssertionError("candidate sized")


def _route(runtime: Any, candidate: object, **overrides: object) -> Any:
    kwargs = {
        "batch_context": None,
        "evaluation_context": {CONTEXT_ITEMS[0]: runtime.admit010._valid_contract()},
        "download_result_context": None,
        "stage_authorization_context": None,
    }
    kwargs.update(overrides)
    return runtime.evaluate_admission_rule(RULE_ID, candidate, **kwargs)


def _verify_runtime_behavior(runtime: Any) -> None:
    context_cases = (
        ({"batch_context": object()}, "ADMIT_010_BATCH_CONTEXT_MUST_BE_NONE"),
        ({"evaluation_context": None}, "ADMIT_010_EVALUATION_CONTEXT_MAPPING_REQUIRED"),
        ({"evaluation_context": object()}, "ADMIT_010_EVALUATION_CONTEXT_MAPPING_REQUIRED"),
        ({"evaluation_context": {}}, "ADMIT_010_LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_CONTRACT_REQUIRED"),
        ({"download_result_context": object()}, "ADMIT_010_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"),
        ({"stage_authorization_context": object()}, "ADMIT_010_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
    )
    for overrides, reason in context_cases:
        try:
            _route(runtime, _Bomb(), **overrides)
        except runtime.UnifiedAdmissionDispatchError as error:
            if tuple(getattr(error, name) for name in ERROR_FIELDS) != (
                "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID", RULE_ID, True, True, True, reason,
            ):
                raise AssertionError("context failure contract drift")
        else:
            raise AssertionError("context failure missing")

    scalar = "COVAPIE_LEAKAGE_GROUP_000001"
    provenance = runtime.admit010._valid_contract(candidate=scalar)
    candidate = _CountingMapping({"leakage_group_id": scalar, "extra": object()})
    context = _CountingMapping({CONTEXT_ITEMS[0]: provenance, "extra": object()})
    _route(runtime, candidate, evaluation_context=context)
    if candidate.getitem_calls != ["leakage_group_id"] or context.getitem_calls != [CONTEXT_ITEMS[0]]:
        raise AssertionError("direct lookup count drift")
    if any((candidate.iterated, context.iterated, candidate.get_called, context.get_called, candidate.contains_called, context.contains_called)):
        raise AssertionError("forbidden Mapping operation")
    for location in ("context", "candidate"):
        sentinel = RuntimeError(location)
        try:
            _route(
                runtime,
                _CountingMapping({}, sentinel) if location == "candidate" else {},
                evaluation_context=(
                    _CountingMapping({}, sentinel)
                    if location == "context"
                    else {CONTEXT_ITEMS[0]: provenance}
                ),
            )
        except RuntimeError as error:
            if error is not sentinel:
                raise AssertionError("non-KeyError identity drift")
        else:
            raise AssertionError("non-KeyError swallowed")

    calls: list[tuple[str, object, object]] = []
    original_formal = runtime.admit010.evaluate_admit_010
    original_oracle = runtime.admit010_oracle.classify_admit_010_leakage_group_assignment_provenance_design
    scalar_object = type("StringSubclass", (str,), {})(scalar)
    provenance_object = object()

    def formal(value: object, contract: object):
        calls.append(("formal", value, contract))
        return original_formal(value, contract)

    def oracle(value: object, contract: object):
        calls.append(("oracle", value, contract))
        return original_oracle(value, contract)

    runtime.admit010.evaluate_admit_010 = formal
    runtime.admit010_oracle.classify_admit_010_leakage_group_assignment_provenance_design = oracle
    try:
        _route(
            runtime,
            {"leakage_group_id": scalar_object},
            evaluation_context={CONTEXT_ITEMS[0]: provenance_object},
        )
    finally:
        runtime.admit010.evaluate_admit_010 = original_formal
        runtime.admit010_oracle.classify_admit_010_leakage_group_assignment_provenance_design = original_oracle
    if [item[0] for item in calls] != ["formal", "oracle"] or any(item[1] is not scalar_object or item[2] is not provenance_object for item in calls):
        raise AssertionError("formal/oracle order, count, or identity drift")

    invalid = (
        (object(), "ADMIT_010_CANDIDATE_RECORD_MAPPING_INVALID"),
        ({}, "leakage_group_id_missing"),
    )
    for candidate_value, reason in invalid:
        value = _route(runtime, candidate_value)
        actual = tuple(getattr(value, name) for name in RESULT_FIELDS)
        expected = (
            runtime.RESULT_SCHEMA_VERSION, RULE_ID, RULE_NAME, "invalid", False, True,
            reason, (), (), CANDIDATE_FIELDS, CONTEXT_ITEMS, False, ADAPTER_ID,
        )
        if actual != expected:
            raise AssertionError("candidate invalid Exact13 drift")

    source = original_formal(scalar, provenance)
    class ResultSubclass(type(source)):
        pass
    subclass = object.__new__(ResultSubclass)
    for name in SOURCE_FIELDS:
        object.__setattr__(subclass, name, getattr(source, name))
    for bad, reason in (
        (object(), "ADMIT_010_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"),
        (subclass, "ADMIT_010_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"),
    ):
        try:
            runtime._prevalidate_admit010_source(bad)
        except runtime.UnifiedAdmissionDispatchError as error:
            if error.reason != reason or error.adapter_ready is not False:
                raise AssertionError("source type failure drift")
        else:
            raise AssertionError("source type failure missing")
    ordered = original_formal(scalar, provenance)
    first = SOURCE_FIELDS[0]
    saved = vars(ordered).pop(first)
    vars(ordered)[first] = saved
    cross = original_formal(scalar, provenance)
    object.__setattr__(cross, "reason", "LEAKAGE_GROUP_ID_TYPE_INVALID")
    for bad in (ordered, cross):
        try:
            runtime._prevalidate_admit010_source(bad)
        except runtime.UnifiedAdmissionDispatchError as error:
            if error.reason != "ADMIT_010_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID":
                raise AssertionError("source invariant reason drift")
        else:
            raise AssertionError("source invariant failure missing")
    if tuple(field.name for field in fields(runtime.admit010.Admit010EvaluationResult)) != SOURCE_FIELDS:
        raise AssertionError("committed dataclass order drift")

    for classification in (
        object(),
        {},
        {**dict(original_oracle(scalar, provenance)), "evaluator_io_used": True},
    ):
        runtime.admit010_oracle.classify_admit_010_leakage_group_assignment_provenance_design = lambda *_args, value=classification: value
        try:
            try:
                runtime._expected_admit010_from_oracle(scalar, provenance)
            except runtime.UnifiedAdmissionDispatchError as error:
                if error.reason != "ADMIT_010_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID":
                    raise AssertionError("oracle invariant reason drift")
            else:
                if classification == {} or not isinstance(classification, Mapping):
                    raise AssertionError("oracle invalid classification accepted")
                expected = runtime._expected_admit010_from_oracle(scalar, provenance)
                try:
                    runtime._validate_admit010_oracle_equivalence(source, expected)
                except runtime.UnifiedAdmissionDispatchError:
                    pass
                else:
                    raise AssertionError("oracle mismatch accepted")
        finally:
            runtime.admit010_oracle.classify_admit_010_leakage_group_assignment_provenance_design = original_oracle


def _expected_contract_rows() -> tuple[dict[str, str], ...]:
    definitions = (
        ("TYPE_001", "public_identity", "result type Exact9 object identity", "true"),
        ("TYPE_002", "public_identity", "dispatch error Exact9 object identity", "true"),
        ("TYPE_003", "public_identity", "result schema Exact9 object identity", "true"),
        ("TYPE_004", "public_identity", "Exact13 fields Exact9 object identity", "true"),
        ("TYPE_005", "public_identity", "Exact6 fields Exact9 object identity", "true"),
        ("TYPE_006", "public_identity", "dispatch codes Exact9 object identity", "true"),
        ("TYPE_007", "public_identity", "outcomes Exact9 object identity", "true"),
        ("DISPATCH_001", "dispatcher", "new successor function object", "true"),
        ("DISPATCH_002", "dispatcher", "Exact9 signature equality", "true"),
        ("DISPATCH_003", "dispatcher", "local Exact10 registry binding", "true"),
        ("DISPATCH_004", "dispatcher", "exact built-in str precedence", "first"),
        ("DISPATCH_005", "dispatcher", "known rule precedence", "second"),
        ("DISPATCH_006", "dispatcher", "registered local registry precedence", "third"),
        ("DISPATCH_007", "dispatcher", "local handler call precedence", "fourth"),
        ("REGISTRY_001", "registry", "immutable MappingProxyType", "true"),
        ("REGISTRY_002", "registry", "exact order", "ADMIT_001_to_ADMIT_010"),
        ("REGISTRY_003", "registry", "first nine handler identities", "9/9"),
        ("REGISTRY_004", "registry", "sole new handler", "_evaluate_registered_admit_010"),
        ("REGISTRY_005", "registry", "known IDs", "ADMIT_001_to_ADMIT_015"),
        ("REGISTRY_006", "registry", "callable IDs", "ADMIT_001_to_ADMIT_010"),
        ("REGISTRY_007", "registry", "adapter-ready IDs", "ADMIT_001_to_ADMIT_010"),
        ("REGISTRY_008", "registry", "legacy not-ready IDs", "empty"),
        ("IDENTITY_001", "admit010_identity", "rule ID", RULE_ID),
        ("IDENTITY_002", "admit010_identity", "rule name", RULE_NAME),
        ("IDENTITY_003", "admit010_identity", "adapter ID", ADAPTER_ID),
        ("IDENTITY_004", "admit010_identity", "candidate field", CANDIDATE_FIELDS[0]),
        ("IDENTITY_005", "admit010_identity", "context item", CONTEXT_ITEMS[0]),
        ("ROUTING_001", "context_routing", "batch exact None", "first"),
        ("ROUTING_002", "context_routing", "evaluation Mapping", "second"),
        ("ROUTING_003", "context_routing", "provenance direct required lookup", "third"),
        ("ROUTING_004", "context_routing", "download exact None", "fourth"),
        ("ROUTING_005", "context_routing", "stage exact None", "fifth"),
        ("ROUTING_006", "context_routing", "candidate Mapping", "sixth"),
        ("ROUTING_007", "context_routing", "candidate direct required lookup", "seventh"),
        ("ROUTING_008", "context_routing", "formal evaluator", "eighth"),
        ("ROUTING_009", "context_routing", "source validation", "ninth"),
        ("ROUTING_010", "context_routing", "independent oracle", "tenth"),
        ("ROUTING_011", "context_routing", "full Exact10 equality", "eleventh"),
        ("ROUTING_012", "context_routing", "Exact13 projection", "twelfth"),
        ("MAPPING_001", "mapping", "collections.abc Mapping subclasses", "accepted"),
        ("MAPPING_002", "mapping", "single direct getitem", "exactly_once"),
        ("MAPPING_003", "mapping", "only KeyError means missing", "true"),
        ("MAPPING_004", "mapping", "get contains iteration copy mutation", "forbidden"),
        ("MAPPING_005", "mapping", "present None", "forwarded"),
        ("CANDIDATE_001", "candidate", "non-Mapping reason", "ADMIT_010_CANDIDATE_RECORD_MAPPING_INVALID"),
        ("CANDIDATE_002", "candidate", "missing reason", "leakage_group_id_missing"),
        ("CANDIDATE_003", "candidate", "invalid outcome", "invalid_false_true"),
        ("CANDIDATE_004", "candidate", "invalid call counts", "formal0_oracle0"),
        ("CALL_001", "formal", "formal function", "evaluate_admit_010"),
        ("CALL_002", "formal", "formal positional order", "scalar_then_provenance"),
        ("CALL_003", "formal", "formal call count after gates", "1"),
        ("CALL_004", "formal", "original object identities", "2/2"),
        ("SOURCE_001", "source", "exact committed result type", "required"),
        ("SOURCE_002", "source", "subclass", "rejected"),
        ("SOURCE_003", "source", "vars storage", "exact_dict"),
        ("SOURCE_004", "source", "storage field order", "Exact10"),
        ("SOURCE_005", "source", "dataclass field order", "Exact10"),
        ("SOURCE_006", "source", "all ordered field reads", "Exact10"),
        ("SOURCE_007", "source", "committed reconstruction/post-init", "required"),
        ("SOURCE_008", "source", "full reconstruction equality", "required"),
        ("SOURCE_009", "source", "source failure oracle count", "0"),
        ("ORACLE_001", "oracle", "committed independent provenance oracle", "required"),
        ("ORACLE_002", "oracle", "Mapping classification", "required"),
        ("ORACLE_003", "oracle", "oracle call count", "1"),
        ("ORACLE_004", "oracle", "same positional objects", "2/2"),
        ("ORACLE_005", "oracle", "complete Exact10 construction", "true"),
        ("ORACLE_006", "oracle", "full Exact10 equality", "required"),
        ("ORACLE_007", "oracle", "partial equality", "forbidden"),
        ("PROJECTION_001", "projection", "normalized values", "source.validated_candidate_fields"),
        ("PROJECTION_002", "projection", "validated fields", "source.validated_candidate_fields"),
        ("PROJECTION_003", "projection", "source outcome/reason/consumption", "preserved"),
        ("PROJECTION_004", "projection", "scalar-short context injection", "forbidden"),
        ("ISSUE_001", "issue", "coverage after", "ADMIT_011_to_ADMIT_015"),
        ("ISSUE_002", "issue", "only coverage row fields changed", "2"),
        ("BOUNDARY_001", "boundary", "provider mapping", "false"),
        ("BOUNDARY_002", "boundary", "real provider leakage group IDs", "0"),
        ("BOUNDARY_003", "boundary", "ADMIT_011", "not_started"),
        ("BOUNDARY_004", "boundary", "evaluate_all_rules", "absent"),
        ("BOUNDARY_005", "boundary", "combined verdict", "absent"),
        ("BOUNDARY_006", "boundary", "training", "forbidden"),
    )
    rows = tuple({
        "contract_id": identity,
        "contract_area": area,
        "contract_statement": statement,
        "expected_value": expected,
        "observed_value": expected,
        "contract_passed": "true",
    } for identity, area, statement, expected in definitions)
    if len(rows) != 80 or any(tuple(row) != CONTRACT_COLUMNS for row in rows):
        raise AssertionError("checker-owned Exact80 contract construction failed")
    return rows


def _expected_registry_rows() -> tuple[dict[str, str], ...]:
    rows = []
    for rule_id in KNOWN_IDS:
        registered = rule_id in REGISTERED_IDS
        rows.append({
            "rule_id": rule_id,
            "rule_name": EXPECTED_RULE_NAMES.get(rule_id, ""),
            "known_rule": "true",
            "callable_discovered": str(registered).lower(),
            "adapter_ready": str(registered).lower(),
            "registered": str(registered).lower(),
            "adapter_id": EXPECTED_ADAPTER_IDS.get(rule_id, ""),
            "handler_identity_status": (
                "predecessor_object_identity" if rule_id in KNOWN_IDS[:9]
                else "exact_new_admit010_handler" if rule_id == RULE_ID
                else "not_registered"
            ),
            "dispatch_disposition": (
                "registered_local_handler" if registered
                else "UNIFIED_ADMISSION_RULE_NOT_REGISTERED"
            ),
            "audit_passed": "true",
        })
    return tuple(rows)


def _expected_safety_rows() -> tuple[dict[str, str], ...]:
    positive = (
        "admit010_adapter_runtime", "registry_registration", "exact10_dispatcher",
        "source_validation", "oracle_parity", "exact13_projection",
        "issue_coverage_transition", "deterministic_materialization", "source_verification",
    )
    negative = (
        "provider_mapping", "real_provider_export", "admit011", "evaluate_all_rules",
        "combined_verdict", "raw_network_download", "split_reassignment", "checkpoint",
        "model_forward_loss", "training_fine_tune", "stage_commit_push_gh",
    )
    return tuple({
        "safety_item": item,
        "expected_executed": str(executed).lower(),
        "observed_executed": str(executed).lower(),
        "safety_passed": "true",
    } for item, executed in tuple((item, True) for item in positive) + tuple((item, False) for item in negative))


def _expected_issue_rows() -> tuple[dict[str, str], ...]:
    source = ROOT / SOURCE_BOUNDARY[16][0]
    rows = [dict(row) for row in _csv(source, ISSUE_COLUMNS)]
    matches = [row for row in rows if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]
    if len(rows) != 11 or len(matches) != 1:
        raise AssertionError("authoritative issue inventory drift")
    matches[0]["affected_rules"] = "|".join(KNOWN_IDS[10:])
    matches[0]["integration_transition"] = "admit_010_implemented_and_removed_from_open_coverage_scope"
    return tuple(rows)


def _verify_truth_rows(rows: tuple[dict[str, str], ...]) -> None:
    expected_groups = {
        "predecessor_exact9_truth": 289,
        "global_dispatch": 9,
        "predecessor_handler_identity": 9,
        "admit010_context_routing": 7,
        "admit010_mapping_semantics": 5,
        "admit010_candidate_envelope": 8,
        "admit010_standalone_exact71": 71,
        "admit010_source_failure": 9,
    }
    if len(rows) != 407 or Counter(row["case_group"] for row in rows) != expected_groups:
        raise AssertionError("Exact407 truth natural counts")
    if len({row["case_id"] for row in rows}) != 407 or any(row["case_passed"] != "true" for row in rows):
        raise AssertionError("Exact407 truth IDs/status")
    predecessor_rows = _csv(ROOT / SOURCE_BOUNDARY[3][0], TRUTH_COLUMNS)
    expected_predecessor = tuple({
        **row,
        "case_id": f"EXACT9_{row['case_id']}",
        "case_group": "predecessor_exact9_truth",
    } for row in predecessor_rows)
    if rows[:289] != expected_predecessor:
        raise AssertionError("predecessor Exact9 truth preservation")

    # A checker-owned canonical digest freezes every successor row, every
    # column, row order, and value without invoking any production builder.
    successor_canonical = json.dumps(
        list(rows[289:]), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    if hashlib.sha256(successor_canonical).hexdigest() != FROZEN_SUCCESSOR_TRUTH_ROWS_SHA256:
        raise AssertionError("successor Exact118 truth complete equality")


def _expected_manifest(
    verification: tuple[dict[str, Any], ...],
    csv_hashes: Mapping[str, str],
) -> dict[str, Any]:
    readiness = {name: True for name in TRUE_READINESS} | {name: False for name in FALSE_READINESS}
    truth_groups = {
        "predecessor_exact9_truth": 289,
        "global_dispatch": 9,
        "predecessor_handler_identity": 9,
        "admit010_context_routing": 7,
        "admit010_mapping_semantics": 5,
        "admit010_candidate_envelope": 8,
        "admit010_standalone_exact71": 71,
        "admit010_source_failure": 9,
    }
    payload: dict[str, Any] = {
        "project": "CovaPIE",
        "step": STEP,
        "stage": STAGE,
        "manifest_schema_version": MANIFEST_SCHEMA,
        "expected_base_commit": BASE,
        "expected_base_subject": SUBJECT,
        "exact10_identity": "ADMIT_001_to_ADMIT_010_unified_single_rule_runtime_v1",
        "exact9_predecessor_identity": "ADMIT_001_to_ADMIT_009_unified_single_rule_runtime_v1",
        "source_boundary_name": "fixed_ordered_exact18_committed_source_boundary",
        "source_input_count": 18,
        "source_input_paths": [path for path, _ in SOURCE_BOUNDARY],
        "source_input_sha256": dict(SOURCE_BOUNDARY),
        "source_input_verification": list(verification),
        "source_structural_checks_before_first_explicit_content_read": True,
        "source_documents_parsed_only_from_frozen_snapshot_bytes": True,
        "artifact_reference_paths_not_recursively_opened": True,
        "runtime_dependency_imports": [
            "exact9_unified_runtime_predecessor",
            "admit010_standalone_evaluator",
            "admit010_committed_independent_provenance_oracle",
        ],
        "adapter_design_gate_imported_by_runtime": False,
        "public_type_and_constant_identity": {
            "UnifiedAdmissionRuleEvaluation": True,
            "UnifiedAdmissionDispatchError": True,
            "RESULT_SCHEMA_VERSION": True,
            "RESULT_FIELDS": True,
            "DISPATCH_ERROR_FIELDS": True,
            "DISPATCH_ERROR_CODES": True,
            "OUTCOME_VOCABULARY": True,
        },
        "public_dispatch_new_successor_function": True,
        "public_dispatch_signature": EXPECTED_PUBLIC_DISPATCH_SIGNATURE,
        "public_dispatch_signature_matches_exact9": True,
        "public_dispatch_uses_local_registry": True,
        "public_dispatch_cardinality": "single_rule_only",
        "public_dispatch_precedence": [
            "exact_builtin_str", "known_rule", "registered_local_registry", "local_registry_handler",
        ],
        "result_schema_version": EXPECTED_RESULT_SCHEMA_VERSION,
        "result_field_count": 13,
        "result_fields": list(RESULT_FIELDS),
        "dispatch_error_field_count": 6,
        "dispatch_error_fields": list(ERROR_FIELDS),
        "dispatch_error_codes": list(ERROR_CODES),
        "outcome_vocabulary": list(OUTCOMES),
        "known_rule_ids": list(KNOWN_IDS),
        "callable_discovered_rule_ids": list(REGISTERED_IDS),
        "adapter_ready_rule_ids": list(REGISTERED_IDS),
        "legacy_adapter_not_ready_rule_ids": [],
        "registered_rule_ids": list(REGISTERED_IDS),
        "known_not_registered_rule_ids": list(KNOWN_IDS[10:]),
        "registered_rule_count": 10,
        "registry_mapping_proxy_type": True,
        "rule_names": dict(EXPECTED_RULE_NAMES),
        "adapter_ids": dict(EXPECTED_ADAPTER_IDS),
        "first_nine_handler_identity_reused": {rule: True for rule in KNOWN_IDS[:9]},
        "admit_010_handler": "_evaluate_registered_admit_010",
        "admit_010_handler_identity": "exact_new_admit010_handler",
        "admit_010_candidate_fields": list(CANDIDATE_FIELDS),
        "admit_010_context_items": list(CONTEXT_ITEMS),
        "admit_010_context_validation_order": [
            "batch_context_must_be_none",
            "evaluation_context_mapping_validation",
            "leakage_group_assignment_provenance_contract_required_key_lookup",
            "download_result_context_must_be_none",
            "stage_authorization_context_must_be_none",
            "candidate_record_mapping_validation",
            "leakage_group_id_required_key_lookup",
            "formal_evaluator",
            "source_validation",
            "independent_oracle",
            "full_exact10_equality",
            "exact13_projection",
        ],
        "admit_010_context_reasons": {
            "batch_context": "ADMIT_010_BATCH_CONTEXT_MUST_BE_NONE",
            "evaluation_context": "ADMIT_010_EVALUATION_CONTEXT_MAPPING_REQUIRED",
            "evaluation_context_key": "ADMIT_010_LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_CONTRACT_REQUIRED",
            "download_result_context": "ADMIT_010_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
            "stage_authorization_context": "ADMIT_010_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
        },
        "admit_010_candidate_mapping_invalid_reason": "ADMIT_010_CANDIDATE_RECORD_MAPPING_INVALID",
        "admit_010_missing_reason": "leakage_group_id_missing",
        "admit_010_required_lookup": "single_direct_lookup_KeyError_only",
        "admit_010_present_values_forwarded_unchanged": True,
        "admit_010_formal_evaluator": "evaluate_admit_010",
        "admit_010_formal_positional_argument_order": ["scalar_object", "provenance_object"],
        "admit_010_formal_call_count": 1,
        "admit_010_adapter_normalization": False,
        "admit_010_source_type": "Admit010EvaluationResult",
        "admit_010_source_fields": list(SOURCE_FIELDS),
        "admit_010_source_type_invalid_reason": "ADMIT_010_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID",
        "admit_010_source_invariant_invalid_reason": "ADMIT_010_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        "admit_010_source_prevalidation_before_oracle": True,
        "admit_010_source_full_exact10_invariant_validation": True,
        "admit_010_oracle": "classify_admit_010_leakage_group_assignment_provenance_design",
        "admit_010_oracle_call_count": 1,
        "admit_010_source_oracle_full_exact10_equality_required": True,
        "admit_010_normalized_values_projection": "source.validated_candidate_fields",
        "admit_010_no_partial_exact13_on_failure": True,
        "standalone_exact71_projection_count": 71,
        "contract_row_count": 80,
        "contract_pass_count": 80,
        "truth_matrix_row_count": 407,
        "truth_matrix_pass_count": 407,
        "truth_matrix_group_counts": truth_groups,
        "registry_audit_row_count": 15,
        "registry_audit_pass_count": 15,
        "safety_audit_row_count": 20,
        "safety_audit_pass_count": 20,
        "issue_inventory_row_count": 11,
        "issue_transition_count": 1,
        "issue_transition_id": "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
        "issue_transition": "admit_010_implemented_and_removed_from_open_coverage_scope",
        "issue_coverage_after": list(KNOWN_IDS[10:]),
        "issue_authoritative_predecessor_sha256": SOURCE_BOUNDARY[16][1],
        "issue_output_sha256": "f59eecc7136ebdd148f2c6c6422b7a2bc0637e340322e09bc005eb00355db03c",
        "output_files": list(OUTPUTS),
        "output_file_count": 6,
        "output_sha256": dict(csv_hashes),
        "output_sha256_excludes_manifest_self_hash": True,
        "checker_freezes_all_six_output_sha256": True,
        "output_materialization": {
            "output_preflight_before_source_read": True,
            "repo_root_real_non_symlink": True,
            "relative_output_resolved_within_repo": True,
            "absolute_output_parent_has_no_symlink_indirection": True,
            "exact_six_allowlist": True,
            "existing_entries_regular_non_symlink": True,
            "unsafe_state_has_no_source_read_or_partial_write": True,
            "same_directory_mkstemp": True,
            "temporary_suffix": ".tmp",
            "fdopen_mode": "wb",
            "flush_and_fsync": True,
            "os_replace": True,
            "finally_cleanup": True,
            "postwrite_exact_six_revalidated": True,
        },
        "provider_fields_consumed": [],
        "real_provider_leakage_group_id_count": 0,
        "leakage_group_id_provider_mapping_validated": False,
        "exact9_runtime_modified": False,
        "admit_011_started": False,
        "evaluate_all_rules_implemented": False,
        "combined_candidate_verdict_implemented": False,
        "feature_semantics_audit_required": True,
        "step12d_is_final_training_feature_contract": False,
        "stop_boundaries": [
            "no_admit_011", "no_provider_mapping", "no_real_candidate_evaluation",
            "no_evaluate_all_rules", "no_combined_candidate_verdict",
            "no_raw_or_checkpoint_read", "no_network_or_download",
            "no_model_forward_loss_training",
        ],
        "readiness_true_count": 24,
        "readiness_false_count": 12,
        "readiness": readiness,
        **readiness,
        "all_source_boundary_checks_passed": True,
        "all_predecessor_contract_checks_passed": True,
        "all_runtime_contract_checks_passed": True,
        "all_truth_matrix_checks_passed": True,
        "all_registry_audit_checks_passed": True,
        "all_issue_checks_passed": True,
        "all_safety_checks_passed": True,
        "all_checks_passed": True,
        "validation_failures": [],
        "recommended_next_step": "audit_covapie_admit_011_formal_evaluator_interface_preconditions_v1",
        "manifest_top_level_key_count": 0,
    }
    payload["manifest_top_level_key_count"] = len(payload)
    return payload


def _checker_resolved_output_target_is_authorized(
    root: Path,
    *,
    output_root_was_relative: bool,
) -> bool:
    try:
        repo_mode = os.lstat(ROOT).st_mode
        if not stat.S_ISDIR(repo_mode) or stat.S_ISLNK(repo_mode):
            return False
        resolved_repo = ROOT.resolve(strict=True)
        if Path(os.path.abspath(ROOT)) != resolved_repo:
            return False
        parent = Path(os.path.abspath(root.parent))
        parent_mode = os.lstat(parent).st_mode
        if not stat.S_ISDIR(parent_mode) or stat.S_ISLNK(parent_mode) or parent.resolve(strict=True) != parent:
            return False
        absolute_root = Path(os.path.abspath(root))
        root_mode = os.lstat(absolute_root).st_mode
        if not stat.S_ISDIR(root_mode) or stat.S_ISLNK(root_mode) or absolute_root.resolve(strict=True) != absolute_root:
            return False
        if output_root_was_relative:
            absolute_root.relative_to(resolved_repo)
    except (OSError, RuntimeError, ValueError):
        return False
    return True


def _validate_output_tree(
    output_root: Path = OUTPUT_ROOT,
    *,
    enforce_frozen_hashes: bool = True,
) -> dict[str, str]:
    output_root_was_relative = not output_root.is_absolute()
    root = ROOT / output_root if output_root_was_relative else output_root
    if not _checker_resolved_output_target_is_authorized(root, output_root_was_relative=output_root_was_relative):
        raise AssertionError("output target resolved containment invalid")
    entries = tuple(root.iterdir())
    if {entry.name for entry in entries} != set(OUTPUTS):
        raise AssertionError("output inventory")
    if any(not stat.S_ISREG(os.lstat(entry).st_mode) or stat.S_ISLNK(os.lstat(entry).st_mode) for entry in entries):
        raise AssertionError("output entry type")
    hashes = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in OUTPUTS}
    contract = _csv(root / OUTPUTS[0], CONTRACT_COLUMNS)
    truth = _csv(root / OUTPUTS[1], TRUTH_COLUMNS)
    registry = _csv(root / OUTPUTS[2], REGISTRY_COLUMNS)
    safety = _csv(root / OUTPUTS[3], SAFETY_COLUMNS)
    issues = _csv(root / OUTPUTS[4], ISSUE_COLUMNS)
    # Complete all Exact18 structural checks before either independent
    # expected builder reads predecessor truth/issue source bytes.
    verification = _verify_sources()
    if contract != _expected_contract_rows():
        raise AssertionError("Exact80 contract complete equality")
    _verify_truth_rows(truth)
    if registry != _expected_registry_rows():
        raise AssertionError("Exact15 registry complete equality")
    if safety != _expected_safety_rows():
        raise AssertionError("Exact20 safety complete equality")
    expected_issues = _expected_issue_rows()
    if issues != expected_issues:
        raise AssertionError("Exact11 issue complete equality")
    if hashes[OUTPUTS[4]] != "f59eecc7136ebdd148f2c6c6422b7a2bc0637e340322e09bc005eb00355db03c":
        raise AssertionError("issue frozen transition hash")
    manifest = json.loads((root / OUTPUTS[5]).read_text(encoding="utf-8"))
    csv_hashes = {name: hashes[name] for name in OUTPUTS[:5]}
    expected_manifest = _expected_manifest(verification, csv_hashes)
    if type(manifest) is not dict or manifest != expected_manifest:
        raise AssertionError("manifest complete equality")
    if enforce_frozen_hashes and hashes != FROZEN_OUTPUT_SHA256:
        raise AssertionError("frozen output hash mismatch")
    return hashes


def main() -> int:
    runtime = importlib.import_module(MODULE)
    _verify_ast(runtime)
    _verify_runtime_identity(runtime)
    _verify_runtime_behavior(runtime)
    before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in OUTPUT_ROOT.iterdir()}
    importlib.reload(runtime)
    after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in OUTPUT_ROOT.iterdir()}
    if before != after:
        raise AssertionError("runtime import side effect")
    hashes = _validate_output_tree()
    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        first_path = Path(first)
        second_path = Path(second)
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1(first_path, repo_root=ROOT)
        runtime.run_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1(second_path, repo_root=ROOT)
        first_bytes = {name: (first_path / name).read_bytes() for name in OUTPUTS}
        second_bytes = {name: (second_path / name).read_bytes() for name in OUTPUTS}
        if first_bytes != second_bytes:
            raise AssertionError("double materialization differs")
        _validate_output_tree(first_path, enforce_frozen_hashes=False)
        if any(hashlib.sha256(first_bytes[name]).hexdigest() != hashes[name] for name in OUTPUTS):
            raise AssertionError("materialization differs from frozen output")
    print(json.dumps({"checked": True, "output_sha256": hashes}, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
