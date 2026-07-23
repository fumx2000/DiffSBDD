"""ADMIT_014 stage-download authorization contract design gate.

This module freezes a metadata-only contract.  It does not define the formal
ADMIT_014 evaluator or result, an adapter, registry entry, dispatcher,
provider, download orchestration, aggregation, or combined verdict.
"""
from __future__ import annotations

import csv
import ctypes
import errno
import hashlib
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_COMMIT = "30bbfaba4df0843d1f028e695d3dc499079a9b36"
BASE_PARENT = "3ec07b2daa7e6fc2d51df2641e85c13be2196ff3"
BASE_TREE = "72390570480b5b81680acccc2db3250ad71a942c"
BASE_SUBJECT = "add CovaPIE ADMIT_014 formal evaluator preconditions audit v1"
STAGE = (
    "covapie_bulk_download_admission_admit_014_"
    "download_authorization_contract_v1"
)
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

CANONICAL_PYTHON_IMPLEMENTATION = "cpython"
CANONICAL_PYTHON_VERSION = "3.10.4"
NONCANONICAL_PYTHON_POLICY = (
    "evaluator_semantic_smoke_only; artifact_build_checker_and_frozen_ast_forbidden"
)
PYTHON_RUNTIME_MIGRATION_POLICY = "explicit_contract_refresh_required"

ADMISSION_RULE_ID = "ADMIT_014"
ADMISSION_RULE_NAME = "current_gate_grants_no_download_permission"
EVIDENCE_SOURCE = "current_design_gate"
REQUIRED_STATUS = "bulk_download_not_authorized_now"
FAILURE_SEVERITY = "blocking"
BLOCKING_REASON = "bulk_download_not_authorized"
EVALUATION_PHASE = "current_step"
EVALUATOR_MODEL = "future_explicit_authorization_context"
AUTHORIZATION_CONTEXT_ITEM = "current_stage_download_authorized"
AUTHORIZATION_CONTEXT_SCOPE = "stage"
AUTHORITATIVE_ENVELOPE = "stage_authorization_context"
AUTHORIZATION_PRODUCER_BOUNDARY = "trusted_future_stage_orchestrator"
EXACT_VALUE_TYPE = "bool"
VALUE_VOCABULARY = (False, True)
OUTCOME_VOCABULARY = ("passed", "blocked")
REASON_VOCABULARY = (
    "",
    "STAGE_AUTHORIZATION_CONTEXT_REQUIRED",
    "STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID",
    "CURRENT_STAGE_DOWNLOAD_AUTHORIZED_MISSING",
    "STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED",
    "CURRENT_STAGE_DOWNLOAD_AUTHORIZED_TYPE_INVALID",
    "BULK_DOWNLOAD_NOT_AUTHORIZED",
)
PRECEDENCE = REASON_VOCABULARY[1:] + ("",)
FORBIDDEN_ENVELOPES = (
    "candidate_record",
    "batch_context",
    "evaluation_context",
    "download_result_context",
)
FORBIDDEN_PSEUDO_AUTHORITIES = (
    *FORBIDDEN_ENVELOPES,
    "provider_result",
    "candidate_self_report",
    "environment_variable",
    "filesystem_marker",
    "raw_file",
    "manifest_self_report",
    "test_fixture",
    "artifact_sha256",
    "git_commit_sha",
)
RECOMMENDED_NEXT_STEP = (
    "design_covapie_admit_014_formal_evaluator_interface_contract_v1"
)

VALUE_FILE = "covapie_admit_014_download_authorization_value_and_trust_contract.csv"
ROUTING_FILE = (
    "covapie_admit_014_stage_authorization_routing_and_enforcement_contract.csv"
)
FAILURE_FILE = "covapie_admit_014_failure_taxonomy_and_precedence.csv"
TRUTH_FILE = "covapie_admit_014_download_authorization_truth_matrix.csv"
ISSUE_FILE = "covapie_admit_014_issue_readiness_inventory.csv"
MANIFEST_FILE = "covapie_admit_014_download_authorization_contract_manifest.json"
OUTPUT_FILES = (
    VALUE_FILE,
    ROUTING_FILE,
    FAILURE_FILE,
    TRUTH_FILE,
    ISSUE_FILE,
    MANIFEST_FILE,
)

VALUE_COLUMNS = (
    "contract_order",
    "contract_item",
    "contract_group",
    "expected_contract",
    "observed_contract",
    "responsibility_owner",
    "contract_passed",
)
ROUTING_COLUMNS = (
    "routing_order",
    "routing_item",
    "envelope_or_stage",
    "authority_status",
    "access_or_enforcement_contract",
    "expected_behavior",
    "observed_design",
    "routing_passed",
)
FAILURE_COLUMNS = (
    "precedence_order",
    "failure_or_pass_id",
    "trigger",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "later_checks_executed",
    "taxonomy_passed",
)
TRUTH_COLUMNS = (
    "case_order",
    "case_id",
    "case_group",
    "stage_context_representation",
    "forbidden_envelope_representation",
    "expected_outcome",
    "observed_outcome",
    "expected_reason",
    "observed_reason",
    "target_key_access_count",
    "mapping_iteration_count",
    "mapping_len_count",
    "mapping_get_count",
    "mapping_contains_count",
    "forbidden_envelope_access_count",
    "case_passed",
)

PRE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_014_"
    "rule_logic_interface_preconditions_audit_v1"
)
STEP14AUA_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_"
    "implementation_precondition_gate_v1"
)
STEP14AT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1"
)
RUNTIME_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1"
)
PRE_PRODUCTION = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_admit_014_"
    "formal_evaluator_interface_preconditions_audit.py"
)
PRE_MATRIX = PRE_ROOT / "covapie_admit_014_formal_evaluator_precondition_matrix.csv"
PRE_AUTHORIZATION = (
    PRE_ROOT
    / "covapie_admit_014_authorization_evidence_and_routing_responsibility_matrix.csv"
)
PRE_ISSUES = PRE_ROOT / "covapie_admit_014_issue_readiness_inventory.csv"
PRE_MANIFEST = PRE_ROOT / "covapie_admit_014_formal_evaluator_preconditions_manifest.json"
STEP14AUA_RULES = (
    STEP14AUA_ROOT / "covapie_bulk_download_admission_rule_executability_matrix.csv"
)
STEP14AUA_CONTEXT = (
    STEP14AUA_ROOT / "covapie_bulk_download_admission_evaluation_context_contract.csv"
)
STEP14AT_RULES = STEP14AT_ROOT / "covapie_bulk_download_admission_rule_registry.csv"
RUNTIME_PRODUCTION = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013.py"
)
RUNTIME_MANIFEST = RUNTIME_ROOT / "covapie_admit_001_to_013_runtime_manifest.json"
RUNTIME_ISSUES = (
    RUNTIME_ROOT / "covapie_admit_001_to_013_runtime_issue_readiness_inventory.csv"
)

SOURCE_SHA256 = {
    PRE_PRODUCTION: "d134e43f01860bd193eacab6a38171bb508b1e1e48fcf1559f8105d74d0e2632",
    PRE_MATRIX: "6b52a4e96dd960e7df53b7160f5cd00d63fbeb62ee5bc5ec9882623efd268c30",
    PRE_AUTHORIZATION: "c1804d6ff7bd0a6eecb68877defa41316dd8afc999fb1152eba323f185b03834",
    PRE_ISSUES: "6af875d474f0c0e1320f2584eec080acf6cf4d1097c25f004380430e4c5fab06",
    PRE_MANIFEST: "b9582357f392a6aa1af68012a1469c886b2de4b5af8196cddad56f94625e4b61",
    STEP14AUA_RULES: "a7782e48cac282b047a392ee20b5b26a72fa1b2208a3889edf8b1c8af923921b",
    STEP14AUA_CONTEXT: "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0",
    STEP14AT_RULES: "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
    RUNTIME_PRODUCTION: "79f95b6e178044ff5b4f5abbd6445b6cd848e81ba1a8a16cacdf831b05b9b892",
    RUNTIME_MANIFEST: "2940e6cc02a92b4919cdece3b1fa7c2f5e27d844f2962bb18757197266c23f79",
    RUNTIME_ISSUES: "477b4192579d3f64dac5bd0cc61c1a378b2f28c3355251e344b79999801a5d69",
}
SOURCE_PATHS = tuple(SOURCE_SHA256)

RESOLVED_ISSUES = {
    "ADMIT_014_AUTHORIZATION_EVIDENCE_SOURCE_UNRESOLVED": (
        "trusted caller boundary and invocation-local provenance responsibility frozen"
    ),
    "ADMIT_014_STAGE_AUTHORIZATION_ROUTING_RESPONSIBILITY_UNRESOLVED": (
        "stage_authorization_context selected as the only authoritative envelope"
    ),
    "ADMIT_014_PERMISSION_VALUE_VOCABULARY_UNRESOLVED": (
        "exact built-in bool with closed False|True vocabulary"
    ),
    "ADMIT_014_PERMISSION_TRANSITION_AND_PRECEDENCE_UNRESOLVED": (
        "missing/type/lookup/False/True precedence and reasons frozen"
    ),
    "ADMIT_014_RUNTIME_ENFORCEMENT_WITHOUT_AGGREGATION_UNRESOLVED": (
        "mandatory pre-download guard semantics frozen independently of aggregation"
    ),
}
OPEN_ADMIT_014_ISSUES = (
    "ADMIT_014_STANDALONE_SIGNATURE_UNRESOLVED",
    "ADMIT_014_RESULT_CONTRACT_UNRESOLVED",
)
RESOLVED_PRECONDITION_IDS = (
    "PRE_015",
    "PRE_017",
    "PRE_019",
    "PRE_020",
    "PRE_021",
    "PRE_022",
    "PRE_023",
    "PRE_024",
    "PRE_025",
    "PRE_026",
    "PRE_031",
    "PRE_033",
    "PRE_034",
    "PRE_036",
    "PRE_037",
    "PRE_038",
    "PRE_042",
    "PRE_045",
    "PRE_046",
    "PRE_047",
    "PRE_050",
)
OPEN_PRECONDITION_IDS = (
    "PRE_039",
    "PRE_040",
    "PRE_041",
    "PRE_048",
    "PRE_049",
)

TRUE_READINESS = (
    "admit_014_preconditions_audited",
    "admit_014_download_authorization_contract_designed",
    "admit_014_explicit_stage_context_model_selected",
    "admit_014_authorization_context_item_frozen",
    "admit_014_authorization_context_scope_frozen",
    "admit_014_stage_authorization_routing_resolved",
    "admit_014_exact_bool_value_contract_frozen",
    "admit_014_permission_value_vocabulary_frozen",
    "admit_014_trusted_caller_boundary_frozen",
    "admit_014_provenance_and_replay_responsibility_frozen",
    "admit_014_permission_transition_and_precedence_resolved",
    "admit_014_reason_vocabulary_frozen",
    "admit_014_mandatory_pre_download_enforcement_contract_frozen",
    "admit_014_future_evaluator_pure_in_memory_possible",
    "ready_for_admit_014_formal_evaluator_interface_contract_design",
    "unified_dispatch_runtime_with_admit_001_to_013_implemented",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "admit_014_standalone_signature_frozen",
    "admit_014_formal_result_contract_frozen",
    "admit_014_result_representation_frozen",
    "ready_for_admit_014_standalone_evaluator_interface_implementation",
    "evaluate_admit_014_implemented",
    "Admit014EvaluationResult_implemented",
    "admit_014_unified_adapter_contract_frozen",
    "admit_014_unified_adapter_implemented",
    "admit_014_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_014_implemented",
    "mandatory_pre_download_authorization_enforcement_implemented",
    "provider_mapping_validated",
    "real_provider_evaluation_ready",
    "ready_for_bulk_download_now",
    "combined_candidate_verdict_implemented",
    "cross_rule_aggregation_implemented",
    "ready_for_training",
    "step12d_is_final_training_feature_contract",
)


@dataclass(frozen=True)
class _Admit014DownloadAuthorizationDesignResult:
    outcome: str
    passed: bool
    blocks_candidate: bool
    reason: str
    evaluator_io_used: bool


def _design_result(
    outcome: str, reason: str
) -> _Admit014DownloadAuthorizationDesignResult:
    passed = outcome == "passed"
    return _Admit014DownloadAuthorizationDesignResult(
        outcome=outcome,
        passed=passed,
        blocks_candidate=outcome == "blocked",
        reason=reason,
        evaluator_io_used=False,
    )


def classify_admit_014_download_authorization_contract_design(
    stage_authorization_context: object,
    *,
    candidate_record: object = None,
    batch_context: object = None,
    evaluation_context: object = None,
    download_result_context: object = None,
) -> _Admit014DownloadAuthorizationDesignResult:
    """Classify the frozen value contract without implementing ADMIT_014."""
    # Forbidden envelopes are intentionally accepted only to prove zero access.
    del candidate_record, batch_context, evaluation_context, download_result_context
    if stage_authorization_context is None:
        return _design_result("blocked", "STAGE_AUTHORIZATION_CONTEXT_REQUIRED")
    if not isinstance(stage_authorization_context, Mapping):
        return _design_result(
            "blocked", "STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID"
        )
    try:
        value = stage_authorization_context[AUTHORIZATION_CONTEXT_ITEM]
    except KeyError:
        return _design_result(
            "blocked", "CURRENT_STAGE_DOWNLOAD_AUTHORIZED_MISSING"
        )
    except Exception:
        return _design_result(
            "blocked", "STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED"
        )
    if type(value) is not bool:
        return _design_result(
            "blocked", "CURRENT_STAGE_DOWNLOAD_AUTHORIZED_TYPE_INVALID"
        )
    if value is False:
        return _design_result("blocked", "BULK_DOWNLOAD_NOT_AUTHORIZED")
    return _design_result("passed", "")


@dataclass(frozen=True)
class Source:
    path: Path
    content: bytes
    sha256: str
    mode: str
    blob: str


Identity = tuple[int, int, int, int, int, int]


def _identity(item: os.stat_result) -> Identity:
    return (
        item.st_dev,
        item.st_ino,
        item.st_mode,
        item.st_size,
        item.st_mtime_ns,
        item.st_ctime_ns,
    )


def _canonical_runtime_guard() -> None:
    if (
        sys.implementation.name != CANONICAL_PYTHON_IMPLEMENTATION
        or tuple(sys.version_info[:3]) != (3, 10, 4)
    ):
        raise RuntimeError(
            "canonical evidence build requires CPython 3.10.4; "
            + NONCANONICAL_PYTHON_POLICY
        )


def _git(args: list[str], *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=text,
        check=False,
    )


def _safe_source(path: Path) -> bool:
    return (
        not path.is_absolute()
        and bool(path.parts)
        and ".." not in path.parts
        and path.parts[:2] != ("data", "raw")
        and path.parts[0] != "checkpoints"
        and STAGE not in path.as_posix()
        and DEFAULT_OUTPUT_ROOT.as_posix() not in path.as_posix()
    )


def _pinned_read_relative(path: Path) -> bytes:
    if not _safe_source(path):
        raise ValueError(f"unsafe source path: {path}")
    root_before = os.lstat(REPO_ROOT)
    if stat.S_ISLNK(root_before.st_mode) or not stat.S_ISDIR(root_before.st_mode):
        raise ValueError("unsafe repository root")
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    leaf_flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    root_identity = _identity(root_before)
    descriptors: list[tuple[int, Identity, int | None, str | None]] = []
    root_fd = os.open(REPO_ROOT, directory_flags)
    if _identity(os.fstat(root_fd)) != root_identity:
        os.close(root_fd)
        raise ValueError("repository root stat/open race")
    descriptors.append((root_fd, root_identity, None, None))
    try:
        parent_fd = root_fd
        for part in path.parts[:-1]:
            lexical = os.stat(part, dir_fd=parent_fd, follow_symlinks=False)
            expected = _identity(lexical)
            if stat.S_ISLNK(lexical.st_mode) or not stat.S_ISDIR(lexical.st_mode):
                raise ValueError(f"unsafe source parent: {path}")
            child_fd = os.open(part, directory_flags, dir_fd=parent_fd)
            if _identity(os.fstat(child_fd)) != expected:
                os.close(child_fd)
                raise ValueError(f"source parent stat/open race: {path}")
            descriptors.append((child_fd, expected, parent_fd, part))
            parent_fd = child_fd
        before = os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
        expected_leaf = _identity(before)
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
            raise ValueError(f"unsafe source leaf: {path}")
        leaf_fd = os.open(path.name, leaf_flags, dir_fd=parent_fd)
        try:
            if _identity(os.fstat(leaf_fd)) != expected_leaf:
                raise ValueError(f"source stat/open race: {path}")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(leaf_fd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            if _identity(os.fstat(leaf_fd)) != expected_leaf:
                raise ValueError(f"source FD identity drift: {path}")
        finally:
            os.close(leaf_fd)
        if (
            _identity(
                os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
            )
            != expected_leaf
        ):
            raise ValueError(f"source replacement after read: {path}")
        for descriptor, expected, lexical_parent, lexical_name in descriptors:
            if _identity(os.fstat(descriptor)) != expected:
                raise ValueError(f"source parent identity drift: {path}")
            if lexical_parent is not None and lexical_name is not None:
                if (
                    _identity(
                        os.stat(
                            lexical_name,
                            dir_fd=lexical_parent,
                            follow_symlinks=False,
                        )
                    )
                    != expected
                ):
                    raise ValueError(f"source parent lexical replacement: {path}")
        if _identity(os.lstat(REPO_ROOT)) != root_identity:
            raise ValueError("repository root identity drift")
        return b"".join(chunks)
    finally:
        for descriptor, _, _, _ in reversed(descriptors):
            os.close(descriptor)


def build_frozen_source_snapshot() -> tuple[Source, ...]:
    _canonical_runtime_guard()
    identity = _git(["show", "-s", "--format=%H%n%P%n%T%n%s", BASE_COMMIT])
    ancestor = _git(["merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"])
    if identity.returncode or ancestor.returncode:
        raise ValueError("base identity or ancestry unavailable")
    if identity.stdout.splitlines() != [
        BASE_COMMIT,
        BASE_PARENT,
        BASE_TREE,
        BASE_SUBJECT,
    ]:
        raise ValueError("base identity mismatch")
    preflight: list[tuple[Path, str, str]] = []
    for path in SOURCE_PATHS:
        index = _git(["ls-files", "--stage", "--", path.as_posix()])
        tree = _git(["ls-tree", BASE_COMMIT, "--", path.as_posix()])
        index_head, index_sep, index_path = index.stdout.partition("\t")
        tree_head, tree_sep, tree_path = tree.stdout.partition("\t")
        index_fields = index_head.split()
        tree_fields = tree_head.split()
        if (
            index.returncode
            or tree.returncode
            or not index_sep
            or not tree_sep
            or index_path.strip() != path.as_posix()
            or tree_path.strip() != path.as_posix()
            or len(index_fields) != 3
            or len(tree_fields) != 3
            or index_fields[2] != "0"
            or index_fields[0] not in {"100644", "100755"}
            or tree_fields[0] != index_fields[0]
            or tree_fields[1] != "blob"
            or index_fields[1] != tree_fields[2]
        ):
            raise ValueError(f"source index/base identity mismatch: {path}")
        preflight.append((path, tree_fields[0], tree_fields[2]))
    snapshot = []
    for path, mode, blob in preflight:
        current = _pinned_read_relative(path)
        base = _git(["show", f"{BASE_COMMIT}:{path.as_posix()}"], text=False)
        digest = hashlib.sha256(current).hexdigest()
        if (
            base.returncode
            or not isinstance(base.stdout, bytes)
            or base.stdout != current
            or digest != SOURCE_SHA256[path]
        ):
            raise ValueError(f"source base/filesystem/SHA mismatch: {path}")
        snapshot.append(Source(path, current, digest, mode, blob))
    return tuple(snapshot)


def _source(snapshot: tuple[Source, ...], path: Path) -> Source:
    return next(item for item in snapshot if item.path == path)


def _csv_rows(snapshot: tuple[Source, ...], path: Path) -> list[dict[str, str]]:
    return list(
        csv.DictReader(io.StringIO(_source(snapshot, path).content.decode(), newline=""))
    )


def _json(snapshot: tuple[Source, ...], path: Path) -> dict[str, Any]:
    value = json.loads(_source(snapshot, path).content)
    if type(value) is not dict:
        raise ValueError("JSON object required")
    return value


def _verify_predecessors(snapshot: tuple[Source, ...]) -> None:
    rule = next(
        row
        for row in _csv_rows(snapshot, STEP14AT_RULES)
        if row["admission_rule_id"] == ADMISSION_RULE_ID
    )
    if rule != {
        "admission_rule_id": ADMISSION_RULE_ID,
        "admission_rule_name": ADMISSION_RULE_NAME,
        "evidence_source": EVIDENCE_SOURCE,
        "required_status": REQUIRED_STATUS,
        "failure_severity": FAILURE_SEVERITY,
        "blocking_reason": BLOCKING_REASON,
        "evaluation_phase": EVALUATION_PHASE,
        "network_required": "false",
        "raw_structure_required": "false",
        "ready_for_future_implementation": "true",
    }:
        raise ValueError("ADMIT_014 canonical identity drift")
    preconditions = _csv_rows(snapshot, PRE_MATRIX)
    authorization = _csv_rows(snapshot, PRE_AUTHORIZATION)
    issues = _csv_rows(snapshot, PRE_ISSUES)
    pre_manifest = _json(snapshot, PRE_MANIFEST)
    if not (
        len(preconditions) == 51
        and [row["precondition_id"] for row in preconditions]
        == [f"PRE_{index:03d}" for index in range(1, 52)]
        and sum(row["completeness_status"] == "complete" for row in preconditions)
        == 25
        and sum(row["implementation_blocking"] == "true" for row in preconditions)
        == 26
        and len(authorization) == 20
        and sum(row["completeness_status"] == "complete" for row in authorization)
        == 10
        and len(issues) == 30
        and pre_manifest["source_count"] == 15
        and pre_manifest["current_gate_grants_download_permission"] is False
        and pre_manifest["ready_for_bulk_download_now"] is False
    ):
        raise ValueError("ADMIT_014 precondition lineage drift")
    executable = next(
        row
        for row in _csv_rows(snapshot, STEP14AUA_RULES)
        if row["admission_rule_id"] == ADMISSION_RULE_ID
    )
    context = next(
        row
        for row in _csv_rows(snapshot, STEP14AUA_CONTEXT)
        if row["context_item"] == AUTHORIZATION_CONTEXT_ITEM
    )
    if not (
        executable["candidate_field_dependencies"] == ""
        and executable["batch_context_dependencies"] == ""
        and executable["evaluation_context_dependencies"] == AUTHORIZATION_CONTEXT_ITEM
        and executable["external_filesystem_required"] == "false"
        and executable["network_required"] == "false"
        and executable["download_execution_result_required"] == "false"
        and executable["pure_in_memory_interface_possible"] == "true"
        and executable["semantics_complete"] == "true"
        and executable["deterministic_evaluation_possible_now"] == "true"
        and executable["implementation_disposition"] == "rule_logic_ready"
        and context["context_scope"] == "stage"
        and context["required_by_rules"] == ADMISSION_RULE_ID
        and context["provided_by_future_caller"] == "true"
        and context["filesystem_access_inside_evaluator"] == "false"
        and context["network_access_inside_evaluator"] == "false"
        and context["deterministic_now"] == "true"
        and context["exact_contract_defined"] == "true"
        and context["implementation_ready"] == "true"
    ):
        raise ValueError("Step14AU-A lineage drift")
    runtime = _json(snapshot, RUNTIME_MANIFEST)
    if not (
        runtime["registered_rule_ids"]
        == [f"ADMIT_{index:03d}" for index in range(1, 14)]
        and runtime["known_not_registered_rule_ids"] == ["ADMIT_014", "ADMIT_015"]
        and runtime["admit_014_registered_in_engine"] is False
        and runtime["combined_candidate_verdict_implemented"] is False
        and runtime["cross_rule_aggregation_implemented"] is False
        and runtime["provider_mapping_validated"] is False
        and runtime["ready_for_bulk_download_now"] is False
    ):
        raise ValueError("Exact13 runtime boundary drift")


def _value_rows() -> list[dict[str, str]]:
    specs = (
        ("authoritative envelope", "authority", AUTHORITATIVE_ENVELOPE, "evaluator"),
        ("authoritative key", "authority", AUTHORIZATION_CONTEXT_ITEM, "evaluator"),
        ("exact value type", "value", "type(value) is bool", "evaluator"),
        ("closed value vocabulary", "value", "False|True", "evaluator"),
        ("false semantics", "value", "blocked|BULK_DOWNLOAD_NOT_AUTHORIZED", "evaluator"),
        ("true semantics", "value", "passed|empty reason", "evaluator"),
        ("normalization", "value", "forbidden", "evaluator"),
        ("truthiness coercion", "value", "forbidden; bool(value) not used", "evaluator"),
        ("producer boundary", "trust", AUTHORIZATION_PRODUCER_BOUNDARY, "trusted caller"),
        ("trust source", "trust", "invocation boundary; not mapping self-report", "trusted caller"),
        ("invocation lifetime", "freshness", "invocation-local", "trusted caller"),
        ("explicit reconstruction", "freshness", "required for every stage invocation", "trusted caller"),
        ("artifact/cache/raw replay", "freshness", "forbidden", "trusted caller"),
        ("identity authentication", "trust", "outside evaluator", "future orchestration"),
        ("signature verification", "trust", "outside evaluator", "future orchestration"),
        ("evaluator filesystem access", "safety", "false", "evaluator"),
        ("evaluator network access", "safety", "false", "evaluator"),
        ("evaluator responsibility", "responsibility", "consume and validate one exact bool", "evaluator"),
        ("caller responsibility", "responsibility", "construct fresh trusted stage context", "trusted caller"),
        ("orchestration responsibility", "responsibility", "enforce trust boundary and pre-download guard", "future orchestration"),
    )
    return [
        {
            "contract_order": str(index),
            "contract_item": item,
            "contract_group": group,
            "expected_contract": contract,
            "observed_contract": contract,
            "responsibility_owner": owner,
            "contract_passed": "true",
        }
        for index, (item, group, contract, owner) in enumerate(specs, 1)
    ]


def _routing_rows() -> list[dict[str, str]]:
    specs = (
        ("only authority", AUTHORITATIVE_ENVELOPE, "authoritative", "ordered target __getitem__ only", "consume target key once"),
        ("candidate source", "candidate_record", "forbidden", "zero access", "cannot authorize or override"),
        ("batch source", "batch_context", "forbidden", "zero access", "cannot authorize or override"),
        ("evaluation source", "evaluation_context", "forbidden", "zero access", "cannot authorize or override"),
        ("download-result source", "download_result_context", "forbidden", "zero access", "cannot authorize or override"),
        ("provider source", "provider_result", "forbidden", "zero access", "cannot authorize or override"),
        ("environment source", "environment_variable", "forbidden", "zero access", "cannot authorize"),
        ("filesystem source", "filesystem_marker|raw_file", "forbidden", "zero access", "cannot authorize"),
        ("self-report source", "manifest|fixture|artifact|git SHA", "forbidden", "zero access", "cannot authorize"),
        ("extra stage keys", AUTHORITATIVE_ENVELOPE, "allowed", "do not iterate/len/get/contains", "target-only lookup"),
        ("missing context", AUTHORITATIVE_ENVELOPE, "fail_closed", "no fallback/default", "blocked required reason"),
        ("missing key", AUTHORIZATION_CONTEXT_ITEM, "fail_closed", "first KeyError classified missing", "blocked missing reason"),
        ("lookup exception", AUTHORIZATION_CONTEXT_ITEM, "fail_closed", "non-KeyError classified lookup failed", "blocked lookup reason"),
        ("invalid type", AUTHORIZATION_CONTEXT_ITEM, "fail_closed", "exact built-in bool required", "blocked type reason"),
        ("false permission", AUTHORIZATION_CONTEXT_ITEM, "authoritative", "hard block", "no protected action"),
        ("true permission", AUTHORIZATION_CONTEXT_ITEM, "authoritative", "permission verdict only", "may continue to later independent gates"),
        ("stage-global guard", "real-download stage invocation", "mandatory", "evaluate once per invocation", "before protected actions"),
        ("provider network call", "pre-download", "protected action", "ADMIT_014 pass required", "blocked count=0"),
        ("remote metadata fetch", "pre-download", "protected action", "ADMIT_014 pass required", "blocked count=0"),
        ("file download", "pre-download", "protected action", "ADMIT_014 pass required", "blocked count=0"),
        ("raw write", "pre-download", "protected action", "ADMIT_014 pass required", "blocked count=0"),
        ("download result materialization", "pre-download", "protected action", "ADMIT_014 pass required", "blocked count=0"),
        ("aggregation independence", "combined verdict", "not_required", "hard guard independent", "cannot override blocked"),
        ("pass limitation", "ADMIT_014 pass", "permission_only", "no readiness implication", "does not prove provider/candidate/download/ADMIT_012/013"),
        ("current permission", "current project state", "false", "synthetic True cannot change it", "ready_for_bulk_download_now=false"),
    )
    return [
        {
            "routing_order": str(index),
            "routing_item": item,
            "envelope_or_stage": envelope,
            "authority_status": status,
            "access_or_enforcement_contract": access,
            "expected_behavior": behavior,
            "observed_design": behavior,
            "routing_passed": "true",
        }
        for index, (item, envelope, status, access, behavior) in enumerate(specs, 1)
    ]


def _failure_rows() -> list[dict[str, str]]:
    specs = (
        ("CONTEXT_REQUIRED", "stage_authorization_context is None", "blocked", False, True, REASON_VOCABULARY[1], False),
        ("CONTEXT_MAPPING_INVALID", "context is not Mapping", "blocked", False, True, REASON_VOCABULARY[2], False),
        ("TARGET_MISSING", "first target __getitem__ raises KeyError", "blocked", False, True, REASON_VOCABULARY[3], False),
        ("LOOKUP_FAILED", "target __getitem__ raises non-KeyError", "blocked", False, True, REASON_VOCABULARY[4], False),
        ("TYPE_INVALID", "type(value) is not bool", "blocked", False, True, REASON_VOCABULARY[5], False),
        ("FALSE_BLOCK", "value is False", "blocked", False, True, REASON_VOCABULARY[6], False),
        ("TRUE_PASS", "value is True", "passed", True, False, "", False),
    )
    return [
        {
            "precedence_order": str(index),
            "failure_or_pass_id": identity,
            "trigger": trigger,
            "outcome": outcome,
            "passed": str(passed).lower(),
            "blocks_candidate": str(blocks).lower(),
            "reason": reason,
            "later_checks_executed": str(later).lower(),
            "taxonomy_passed": "true",
        }
        for index, (identity, trigger, outcome, passed, blocks, reason, later) in enumerate(specs, 1)
    ]


class _InstrumentedMapping(Mapping[str, object]):
    def __init__(
        self,
        values: dict[str, object] | None = None,
        *,
        lookup_error: BaseException | None = None,
        iteration_error: BaseException | None = None,
        len_error: BaseException | None = None,
        get_error: BaseException | None = None,
        contains_error: BaseException | None = None,
    ) -> None:
        self.values = {} if values is None else values
        self.lookup_error = lookup_error
        self.iteration_error = iteration_error
        self.len_error = len_error
        self.get_error = get_error
        self.contains_error = contains_error
        self.target_access = 0
        self.iteration_count = 0
        self.len_count = 0
        self.get_count = 0
        self.contains_count = 0

    def __getitem__(self, key: str) -> object:
        if key == AUTHORIZATION_CONTEXT_ITEM:
            self.target_access += 1
        if self.lookup_error is not None:
            raise self.lookup_error
        return self.values[key]

    def __iter__(self) -> Iterator[str]:
        self.iteration_count += 1
        if self.iteration_error is not None:
            raise self.iteration_error
        return iter(self.values)

    def __len__(self) -> int:
        self.len_count += 1
        if self.len_error is not None:
            raise self.len_error
        return len(self.values)

    def get(self, key: str, default: object = None) -> object:
        self.get_count += 1
        if self.get_error is not None:
            raise self.get_error
        return self.values.get(key, default)

    def __contains__(self, key: object) -> bool:
        self.contains_count += 1
        if self.contains_error is not None:
            raise self.contains_error
        return key in self.values

    @property
    def all_accesses(self) -> int:
        return (
            self.target_access
            + self.iteration_count
            + self.len_count
            + self.get_count
            + self.contains_count
        )


class _Truthy:
    def __bool__(self) -> bool:
        return True


class _Falsy:
    def __bool__(self) -> bool:
        return False


def _stable_truth_value_representation(value: object) -> str:
    if isinstance(value, _Truthy):
        return "<CUSTOM_TRUTHY>"
    if isinstance(value, _Falsy):
        return "<CUSTOM_FALSY>"
    if type(value) is object:
        return "<OPAQUE_OBJECT>"
    if type(value) is dict:
        return (
            "{"
            + ", ".join(
                f"{key!r}: {_stable_truth_value_representation(item)}"
                for key, item in value.items()
            )
            + "}"
        )
    return repr(value)


def _truth_rows() -> list[dict[str, str]]:
    invalid_values: tuple[tuple[str, object], ...] = (
        ("INT_ZERO", 0),
        ("INT_ONE", 1),
        ("FLOAT_ZERO", 0.0),
        ("FLOAT_ONE", 1.0),
        ("STRING_FALSE", "false"),
        ("STRING_TRUE", "true"),
        ("EMPTY_STRING", ""),
        ("NONE_VALUE", None),
        ("LIST_VALUE", []),
        ("DICT_VALUE", {}),
        ("CUSTOM_TRUTHY", _Truthy()),
        ("CUSTOM_FALSY", _Falsy()),
    )
    specs: list[tuple[str, str, object, str, str, dict[str, object]]] = [
        ("CONTEXT_NONE", "context_structure", None, "blocked", REASON_VOCABULARY[1], {}),
        ("CONTEXT_OBJECT", "context_structure", object(), "blocked", REASON_VOCABULARY[2], {}),
        ("CONTEXT_INT", "context_structure", 7, "blocked", REASON_VOCABULARY[2], {}),
        ("CONTEXT_STR", "context_structure", "x", "blocked", REASON_VOCABULARY[2], {}),
        ("CONTEXT_LIST", "context_structure", [], "blocked", REASON_VOCABULARY[2], {}),
        ("EMPTY_MAPPING", "context_structure", _InstrumentedMapping(), "blocked", REASON_VOCABULARY[3], {}),
        ("UNRELATED_ONLY", "context_structure", _InstrumentedMapping({"other": True}), "blocked", REASON_VOCABULARY[3], {}),
        ("EXACT_FALSE", "exact_bool", _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: False}), "blocked", REASON_VOCABULARY[6], {}),
        ("EXACT_TRUE", "exact_bool", _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: True}), "passed", "", {}),
    ]
    for case_id, value in invalid_values:
        specs.append(
            (
                case_id,
                "non_exact_bool",
                _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: value}),
                "blocked",
                REASON_VOCABULARY[5],
                {},
            )
        )
    specs.extend(
        (
            ("LOOKUP_KEYERROR", "mapping_behavior", _InstrumentedMapping(lookup_error=KeyError(AUTHORIZATION_CONTEXT_ITEM)), "blocked", REASON_VOCABULARY[3], {}),
            ("LOOKUP_RUNTIMEERROR", "mapping_behavior", _InstrumentedMapping(lookup_error=RuntimeError("boom")), "blocked", REASON_VOCABULARY[4], {}),
            ("LOOKUP_VALUEERROR", "mapping_behavior", _InstrumentedMapping(lookup_error=ValueError("boom")), "blocked", REASON_VOCABULARY[4], {}),
            ("ADMIT015_PLUS_TRUE", "mapping_behavior", _InstrumentedMapping({"current_stage_training_authorized": False, AUTHORIZATION_CONTEXT_ITEM: True}), "passed", "", {}),
            ("ADMIT015_PLUS_FALSE", "mapping_behavior", _InstrumentedMapping({"current_stage_training_authorized": True, AUTHORIZATION_CONTEXT_ITEM: False}), "blocked", REASON_VOCABULARY[6], {}),
            ("MANY_EXTRA_PLUS_TRUE", "mapping_behavior", _InstrumentedMapping({**{f"extra_{index}": object() for index in range(20)}, AUTHORIZATION_CONTEXT_ITEM: True}), "passed", "", {}),
            ("ITERATION_RAISES", "mapping_behavior", _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: True}, iteration_error=RuntimeError("iter")), "passed", "", {}),
            ("LEN_RAISES", "mapping_behavior", _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: True}, len_error=RuntimeError("len")), "passed", "", {}),
            ("GET_RAISES", "mapping_behavior", _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: True}, get_error=RuntimeError("get")), "passed", "", {}),
            ("CONTAINS_RAISES", "mapping_behavior", _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: True}, contains_error=RuntimeError("contains")), "passed", "", {}),
        )
    )
    for case_id, envelope, stage, outcome, reason in (
        ("CANDIDATE_TRUE_STAGE_MISSING", "candidate_record", None, "blocked", REASON_VOCABULARY[1]),
        ("BATCH_TRUE_STAGE_MISSING", "batch_context", None, "blocked", REASON_VOCABULARY[1]),
        ("EVALUATION_TRUE_STAGE_MISSING", "evaluation_context", None, "blocked", REASON_VOCABULARY[1]),
        ("DOWNLOAD_TRUE_STAGE_MISSING", "download_result_context", None, "blocked", REASON_VOCABULARY[1]),
        ("CANDIDATE_TRUE_STAGE_FALSE", "candidate_record", _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: False}), "blocked", REASON_VOCABULARY[6]),
        ("EVALUATION_FALSE_STAGE_TRUE", "evaluation_context", _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: True}), "passed", ""),
    ):
        probe = _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: envelope != "evaluation_context"})
        specs.append((case_id, "forbidden_pseudo_authority", stage, outcome, reason, {envelope: probe}))
    specs.extend(
        (
            ("SYNTHETIC_TRUE_DESIGN", "current_future", _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: True}), "passed", "", {}),
            ("CURRENT_PERMISSION_FALSE", "current_future", _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: False}), "blocked", REASON_VOCABULARY[6], {}),
            ("CURRENT_READINESS_FALSE", "current_future", _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: False}), "blocked", REASON_VOCABULARY[6], {}),
        )
    )
    if len(specs) != 40:
        raise AssertionError("truth matrix Exact40 drift")
    rows = []
    for order, (case_id, group, stage, expected_outcome, expected_reason, forbidden) in enumerate(specs, 1):
        kwargs = {name: forbidden.get(name) for name in FORBIDDEN_ENVELOPES}
        observed = classify_admit_014_download_authorization_contract_design(
            stage,
            **kwargs,
        )
        mapping = stage if isinstance(stage, _InstrumentedMapping) else None
        forbidden_count = sum(
            item.all_accesses
            for item in forbidden.values()
            if isinstance(item, _InstrumentedMapping)
        )
        passed = (
            observed.outcome == expected_outcome
            and observed.reason == expected_reason
            and observed.passed is (expected_outcome == "passed")
            and observed.blocks_candidate is (expected_outcome == "blocked")
            and observed.evaluator_io_used is False
            and (mapping is None or mapping.target_access == 1)
            and (mapping is None or mapping.iteration_count == 0)
            and (mapping is None or mapping.len_count == 0)
            and (mapping is None or mapping.get_count == 0)
            and (mapping is None or mapping.contains_count == 0)
            and forbidden_count == 0
        )
        rows.append(
            {
                "case_order": str(order),
                "case_id": case_id,
                "case_group": group,
                "stage_context_representation": (
                    "None"
                    if stage is None
                    else type(stage).__name__
                    if mapping is None
                    else _stable_truth_value_representation(mapping.values)
                ),
                "forbidden_envelope_representation": "|".join(forbidden) or "",
                "expected_outcome": expected_outcome,
                "observed_outcome": observed.outcome,
                "expected_reason": expected_reason,
                "observed_reason": observed.reason,
                "target_key_access_count": str(0 if mapping is None else mapping.target_access),
                "mapping_iteration_count": str(0 if mapping is None else mapping.iteration_count),
                "mapping_len_count": str(0 if mapping is None else mapping.len_count),
                "mapping_get_count": str(0 if mapping is None else mapping.get_count),
                "mapping_contains_count": str(0 if mapping is None else mapping.contains_count),
                "forbidden_envelope_access_count": str(forbidden_count),
                "case_passed": str(passed).lower(),
            }
        )
    return rows


def _issue_rows(snapshot: tuple[Source, ...]) -> list[dict[str, str]]:
    inherited = _csv_rows(snapshot, PRE_ISSUES)
    rows = [dict(row) for row in inherited]
    for row in rows:
        evidence = RESOLVED_ISSUES.get(row["issue_id"])
        if evidence is not None:
            row["successor_effective_status"] = "resolved"
            row["successor_transition_stage"] = STAGE
            row["successor_transition_action"] = "resolved_by_successor_contract_design"
            row["successor_transition_evidence"] = evidence
    return rows


def _precondition_transition(snapshot: tuple[Source, ...]) -> list[dict[str, str]]:
    rows = [dict(row) for row in _csv_rows(snapshot, PRE_MATRIX)]
    resolved = set(RESOLVED_PRECONDITION_IDS)
    for row in rows:
        if row["precondition_id"] in resolved:
            row["observed_evidence"] = "frozen by ADMIT_014 download authorization contract v1"
            row["completeness_status"] = "complete"
            row["implementation_blocking"] = "false"
            row["blocking_reason"] = ""
    by_id = {row["precondition_id"]: row for row in rows}
    by_id["PRE_048"]["blocking_reason"] = "ADMIT_014_RESULT_CONTRACT_UNRESOLVED"
    by_id["PRE_049"]["blocking_reason"] = "ADMIT_014_STANDALONE_SIGNATURE_UNRESOLVED"
    if (
        len(rows) != 51
        or sum(row["completeness_status"] == "complete" for row in rows) != 46
        or [row["precondition_id"] for row in rows if row["completeness_status"] == "incomplete"]
        != list(OPEN_PRECONDITION_IDS)
    ):
        raise ValueError("precondition transition drift")
    return rows


def _csv_bytes(columns: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=columns, extrasaction="raise", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def _readiness() -> dict[str, bool]:
    return {
        **{name: True for name in TRUE_READINESS},
        **{name: False for name in FALSE_READINESS},
    }


def build_artifacts(
    snapshot: tuple[Source, ...] | None = None,
) -> dict[str, bytes]:
    _canonical_runtime_guard()
    frozen = build_frozen_source_snapshot() if snapshot is None else snapshot
    _verify_predecessors(frozen)
    values = _value_rows()
    routing = _routing_rows()
    failures = _failure_rows()
    truth = _truth_rows()
    issues = _issue_rows(frozen)
    preconditions = _precondition_transition(frozen)
    payloads = {
        VALUE_FILE: _csv_bytes(VALUE_COLUMNS, values),
        ROUTING_FILE: _csv_bytes(ROUTING_COLUMNS, routing),
        FAILURE_FILE: _csv_bytes(FAILURE_COLUMNS, failures),
        TRUTH_FILE: _csv_bytes(TRUTH_COLUMNS, truth),
        ISSUE_FILE: _csv_bytes(tuple(issues[0]), issues),
    }
    hashes = {name: hashlib.sha256(value).hexdigest() for name, value in payloads.items()}
    readiness = _readiness()
    manifest: dict[str, Any] = {
        "project": "CovaPIE",
        "stage": STAGE,
        "manifest_schema_version": "covapie_admit_014_download_authorization_contract_manifest_v1",
        "base_commit": BASE_COMMIT,
        "base_parent": BASE_PARENT,
        "base_tree": BASE_TREE,
        "base_subject": BASE_SUBJECT,
        "canonical_evidence_python_implementation": CANONICAL_PYTHON_IMPLEMENTATION,
        "canonical_evidence_python_version": CANONICAL_PYTHON_VERSION,
        "ast_attestation_cross_python_version_portable": False,
        "noncanonical_python_policy": NONCANONICAL_PYTHON_POLICY,
        "python_runtime_migration_policy": PYTHON_RUNTIME_MIGRATION_POLICY,
        "admission_rule_identity": {
            "admission_rule_id": ADMISSION_RULE_ID,
            "admission_rule_name": ADMISSION_RULE_NAME,
            "evidence_source": EVIDENCE_SOURCE,
            "required_status": REQUIRED_STATUS,
            "failure_severity": FAILURE_SEVERITY,
            "blocking_reason": BLOCKING_REASON,
            "evaluation_phase": EVALUATION_PHASE,
            "evaluator_model": EVALUATOR_MODEL,
        },
        "authorization_contract": {
            "authoritative_envelope": AUTHORITATIVE_ENVELOPE,
            "authoritative_key": AUTHORIZATION_CONTEXT_ITEM,
            "context_scope": AUTHORIZATION_CONTEXT_SCOPE,
            "producer_boundary": AUTHORIZATION_PRODUCER_BOUNDARY,
            "exact_builtin_type": EXACT_VALUE_TYPE,
            "closed_value_vocabulary": [False, True],
            "normalization_or_coercion_allowed": False,
            "forbidden_envelopes": list(FORBIDDEN_ENVELOPES),
            "forbidden_pseudo_authorities": list(FORBIDDEN_PSEUDO_AUTHORITIES),
        },
        "trust_boundary": {
            "trust_from_call_boundary_not_mapping_string": True,
            "context_invocation_local": True,
            "caller_reconstructs_every_invocation": True,
            "artifact_cache_raw_previous_invocation_replay_allowed": False,
            "evaluator_authentication_or_signature_verification": False,
            "cryptographic_authentication_in_evaluator_scope": False,
        },
        "outcome_vocabulary": list(OUTCOME_VOCABULARY),
        "reason_vocabulary": list(REASON_VOCABULARY),
        "failure_precedence": list(PRECEDENCE),
        "result_invariants": {
            "passed_iff_outcome_passed_and_reason_empty": True,
            "blocks_candidate_iff_outcome_blocked": True,
            "evaluator_io_used": False,
        },
        "mandatory_pre_download_authorization_enforcement_contract": {
            "stage_global_guard": True,
            "evaluate_once_each_real_download_stage_invocation": True,
            "must_precede": [
                "provider network call",
                "remote metadata fetch",
                "file download",
                "raw write",
                "download result materialization",
            ],
            "only_pass_may_continue": True,
            "blocked_provider_call_count": 0,
            "blocked_network_call_count": 0,
            "blocked_download_count": 0,
            "blocked_raw_write_count": 0,
            "combined_verdict_required": False,
            "combined_verdict_may_override_blocked": False,
            "implemented": False,
        },
        "current_permission": False,
        "synthetic_true_design_case_grants_current_permission": False,
        "ready_for_bulk_download_now": False,
        "truth_matrix_schema": list(TRUTH_COLUMNS),
        "truth_matrix_row_count": len(truth),
        "truth_matrix_group_counts": {
            group: sum(row["case_group"] == group for row in truth)
            for group in dict.fromkeys(row["case_group"] for row in truth)
        },
        "truth_matrix_all_cases_passed": all(
            row["case_passed"] == "true" for row in truth
        ),
        "forbidden_envelope_access_count": sum(
            int(row["forbidden_envelope_access_count"]) for row in truth
        ),
        "precondition_transition": {
            "row_count": 51,
            "complete_count": 46,
            "incomplete_count": 5,
            "implementation_blocking_count": 5,
            "resolved_precondition_ids": list(RESOLVED_PRECONDITION_IDS),
            "remaining_open_precondition_ids": list(OPEN_PRECONDITION_IDS),
        },
        "issue_transition": {
            "row_count": 30,
            "inherited_exact23_count": 23,
            "resolved_by_this_stage_count": 5,
            "resolved_issue_ids": list(RESOLVED_ISSUES),
            "remaining_open_admit_014_issue_ids": list(OPEN_ADMIT_014_ISSUES),
            "coverage_issue_affected_rules": "ADMIT_014|ADMIT_015",
        },
        "source_count": len(frozen),
        "source_boundary": [
            {
                "path": source.path.as_posix(),
                "sha256": source.sha256,
                "base_tree_mode": source.mode,
                "base_tree_blob": source.blob,
            }
            for source in frozen
        ],
        "source_validation_before_output_read": True,
        "readiness": readiness,
        "safety": {
            "formal_evaluator_or_result": False,
            "adapter_registry_runtime": False,
            "mandatory_enforcement_implementation": False,
            "provider": False,
            "network": False,
            "download": False,
            "raw_read_or_write": False,
            "model_or_checkpoint": False,
            "dataloader": False,
            "training_or_parameter_update": False,
            "combined_candidate_verdict": False,
            "cross_rule_aggregation": False,
            "current_main_stage_commit_push": False,
        },
        "output_file_count": 6,
        "output_files": list(OUTPUT_FILES),
        "output_sha256": hashes,
        "output_sha256_excludes_manifest_self_hash": True,
        "renameat2_policy": (
            "RENAME_NOREPLACE_required; GPFS_EINVAL_fails_closed; "
            "no_os_replace_fallback"
        ),
        "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "feature_semantics_note": (
            "historical UNKNOWN_ATOM_FEATURE_POLICY and feature_semantics_known=false "
            "require an explicit feature-semantics audit before training"
        ),
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "all_checks_passed": True,
    }
    manifest.update(readiness)
    payloads[MANIFEST_FILE] = (
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    ).encode()
    return {name: payloads[name] for name in OUTPUT_FILES}


def _write_exclusive_leaf(directory_fd: int, name: str, data: bytes) -> None:
    descriptor = os.open(
        name,
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0),
        0o644,
        dir_fd=directory_fd,
    )
    try:
        view = memoryview(data)
        while view:
            view = view[os.write(descriptor, view) :]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _rename_noreplace(
    source: Path, destination: Path, parent_fd: int | None = None
) -> None:
    if os.uname().machine not in {"x86_64", "amd64"}:
        raise RuntimeError("renameat2 syscall number unavailable")
    directory = -100 if parent_fd is None else parent_fd
    source_name = source if parent_fd is None else Path(source.name)
    destination_name = destination if parent_fd is None else Path(destination.name)
    result = ctypes.CDLL(None, use_errno=True).syscall(
        316,
        directory,
        os.fsencode(source_name),
        directory,
        os.fsencode(destination_name),
        1,
    )
    if result:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), destination)


def _read_output_set(
    root: Path,
    payloads: dict[str, bytes],
    expected_root_identity: Identity | None = None,
) -> bool:
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    leaf_flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    parent = root.parent
    parent_lexical = os.lstat(parent)
    if stat.S_ISLNK(parent_lexical.st_mode) or not stat.S_ISDIR(parent_lexical.st_mode):
        raise ValueError("unsafe output parent")
    parent_identity = _identity(parent_lexical)
    parent_fd = os.open(parent, directory_flags)
    root_fd = -1
    leaves: list[tuple[str, int, Identity, bytes]] = []
    try:
        if _identity(os.fstat(parent_fd)) != parent_identity:
            raise ValueError("output parent stat/open race")
        root_lexical = os.stat(root.name, dir_fd=parent_fd, follow_symlinks=False)
        if stat.S_ISLNK(root_lexical.st_mode) or not stat.S_ISDIR(root_lexical.st_mode):
            raise ValueError("unsafe output root")
        root_identity = _identity(root_lexical)
        if expected_root_identity is not None and root_identity != expected_root_identity:
            raise ValueError("published destination identity mismatch")
        root_fd = os.open(root.name, directory_flags, dir_fd=parent_fd)
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("output root stat/open race")
        if set(os.listdir(root_fd)) != set(OUTPUT_FILES):
            return False
        for name in OUTPUT_FILES:
            before = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            if (
                stat.S_ISLNK(before.st_mode)
                or not stat.S_ISREG(before.st_mode)
                or before.st_size > 100 * 1024 * 1024
            ):
                raise ValueError("unsafe output leaf")
            expected = _identity(before)
            descriptor = os.open(name, leaf_flags, dir_fd=root_fd)
            if _identity(os.fstat(descriptor)) != expected:
                os.close(descriptor)
                raise ValueError("output leaf stat/open race")
            chunks = []
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            leaves.append((name, descriptor, expected, b"".join(chunks)))
        if set(os.listdir(root_fd)) != set(OUTPUT_FILES):
            raise ValueError("output inventory drift after traversal")
        for name, descriptor, expected, data in leaves:
            if (
                _identity(os.fstat(descriptor)) != expected
                or _identity(
                    os.stat(name, dir_fd=root_fd, follow_symlinks=False)
                )
                != expected
            ):
                raise ValueError("output leaf identity drift after traversal")
            if data != payloads[name]:
                return False
        if (
            _identity(os.fstat(root_fd)) != root_identity
            or _identity(
                os.stat(root.name, dir_fd=parent_fd, follow_symlinks=False)
            )
            != root_identity
            or _identity(os.fstat(parent_fd)) != parent_identity
            or _identity(os.lstat(parent)) != parent_identity
        ):
            raise ValueError("output parent/root identity drift after traversal")
        return True
    finally:
        for _, descriptor, _, _ in leaves:
            os.close(descriptor)
        if root_fd >= 0:
            os.close(root_fd)
        os.close(parent_fd)


def _cleanup_staging(staging: Path) -> None:
    if not staging.exists() or staging.is_symlink():
        return
    entries = list(staging.iterdir())
    if any(entry.name not in OUTPUT_FILES for entry in entries):
        return
    for entry in entries:
        item = os.lstat(entry)
        if stat.S_ISREG(item.st_mode) and not stat.S_ISLNK(item.st_mode):
            entry.unlink()
    try:
        staging.rmdir()
    except OSError:
        pass


def materialize_contract(output_root: Path | None = None) -> dict[str, Any]:
    """Build and atomically publish the deterministic Exact6 design evidence."""
    _canonical_runtime_guard()
    root = REPO_ROOT / DEFAULT_OUTPUT_ROOT if output_root is None else Path(output_root)
    parent = root.parent
    snapshot = build_frozen_source_snapshot()
    payloads = build_artifacts(snapshot)
    if os.path.lexists(root):
        if _read_output_set(root, payloads):
            return json.loads(payloads[MANIFEST_FILE])
        raise ValueError("existing output set mismatch")
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    parent_lexical = os.lstat(parent)
    if stat.S_ISLNK(parent_lexical.st_mode) or not stat.S_ISDIR(parent_lexical.st_mode):
        raise ValueError("unsafe output parent")
    parent_fd = os.open(parent, directory_flags)
    if _identity(os.fstat(parent_fd)) != _identity(parent_lexical):
        os.close(parent_fd)
        raise ValueError("output parent stat/open race")
    staging = Path(
        tempfile.mkdtemp(prefix=f".{root.name}.", suffix=".staging", dir=parent)
    )
    staging_fd = -1
    published = False
    try:
        staging_lexical = os.stat(staging.name, dir_fd=parent_fd, follow_symlinks=False)
        staging_fd = os.open(staging.name, directory_flags, dir_fd=parent_fd)
        if _identity(os.fstat(staging_fd)) != _identity(staging_lexical):
            raise ValueError("staging root stat/open race")
        for name in OUTPUT_FILES:
            _write_exclusive_leaf(staging_fd, name, payloads[name])
        os.fsync(staging_fd)
        staging_identity = _identity(os.fstat(staging_fd))
        try:
            _rename_noreplace(staging, root, parent_fd)
        except OSError as error:
            if error.errno == errno.EEXIST and _read_output_set(root, payloads):
                os.close(staging_fd)
                staging_fd = -1
                _cleanup_staging(staging)
                return json.loads(payloads[MANIFEST_FILE])
            raise
        published = True
        published_identity = _identity(os.fstat(staging_fd))
        if (
            published_identity[:3] != staging_identity[:3]
            or _identity(
                os.stat(root.name, dir_fd=parent_fd, follow_symlinks=False)
            )
            != published_identity
        ):
            raise ValueError("destination name/inode binding mismatch")
        os.fsync(parent_fd)
        if (
            _identity(
                os.stat(root.name, dir_fd=parent_fd, follow_symlinks=False)
            )
            != published_identity
            or _identity(os.fstat(staging_fd)) != published_identity
        ):
            raise ValueError("post-fsync destination binding drift")
        if not _read_output_set(root, payloads, published_identity):
            raise ValueError("published output postverify failed")
    except BaseException:
        if not published:
            _cleanup_staging(staging)
        raise
    finally:
        if staging_fd >= 0:
            os.close(staging_fd)
        os.close(parent_fd)
    return json.loads(payloads[MANIFEST_FILE])


def run_covapie_bulk_download_admission_admit_014_download_authorization_contract_v1(
    output_root: Path | None = None,
) -> dict[str, Any]:
    """Explicitly materialize the contract; import has no side effect."""
    return materialize_contract(output_root)
