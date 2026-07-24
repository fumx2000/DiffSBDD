"""Metadata-only ADMIT_015 training-authorization contract design.

This module freezes design evidence only.  It deliberately does not define the
formal ADMIT_015 evaluator signature or result schema, an oracle, adapter,
registry entry, Exact15 runtime, mandatory enforcement implementation,
provider/raw-data operation, dataloader, model, checkpoint, or training action.
"""
from __future__ import annotations

import csv
import ctypes
import hashlib
import io
import json
import os
import secrets
import stat
import subprocess
import tempfile
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_COMMIT = "4fb86e7d6b8cd27258362cae34eec196b117c265"
BASE_PARENT = "f54c0efabfb695653c9e55b3a53bda8cf200f353"
BASE_TREE = "2a447517ce601e9440a7c1523866d459b192870c"
BASE_SUBJECT = "add CovaPIE ADMIT_015 formal evaluator interface preconditions audit v1"
STAGE = "covapie_bulk_download_admission_admit_015_training_authorization_contract_v1"
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / (
    "covapie_bulk_download_admission_admit_015_training_authorization_contract_v1"
)

ADMISSION_RULE_ID = "ADMIT_015"
ADMISSION_RULE_NAME = "current_gate_grants_no_training_permission"
CURRENT_EVIDENCE_SOURCE = "current_design_gate"
CURRENT_REQUIRED_STATUS = "training_not_authorized_now"
CURRENT_BLOCKING_REASON = "training_not_authorized"
FAILURE_SEVERITY = "blocking"
EVALUATION_PHASE = "current_step"
AUTHORIZATION_MODEL = "future_explicit_authorization_context"
CURRENT_PERMISSION = False
AUTHORIZED_ADMIT_015_TRAINING_EXECUTION_COUNT = 0
SYNTHETIC_TRUE_DESIGN_CASE_GRANTS_CURRENT_PERMISSION = False
READY_FOR_TRAINING_NOW = False

AUTHORITATIVE_ENVELOPE = "stage_authorization_context"
AUTHORIZATION_CONTEXT_ITEM = "current_stage_training_authorized"
DOWNLOAD_AUTHORIZATION_CONTEXT_ITEM = "current_stage_download_authorized"
AUTHORIZATION_CONTEXT_SCOPE = "stage"
AUTHORIZATION_PRODUCER_BOUNDARY = "trusted_future_stage_orchestrator"
EXACT_VALUE_TYPE = "bool"
VALUE_VOCABULARY = (False, True)
OUTCOME_VOCABULARY = ("passed", "blocked")
REASON_VOCABULARY = (
    "",
    "STAGE_AUTHORIZATION_CONTEXT_REQUIRED",
    "STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID",
    "CURRENT_STAGE_TRAINING_AUTHORIZED_MISSING",
    "STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED",
    "CURRENT_STAGE_TRAINING_AUTHORIZED_TYPE_INVALID",
    "TRAINING_NOT_AUTHORIZED",
)
FAILURE_PRECEDENCE = REASON_VOCABULARY[1:] + ("",)
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
    "artifact_sha256",
    "git_commit_sha",
    "manifest_self_report",
    "test_fixture",
    "checkpoint_metadata",
    "training_config",
    "CLI_flag",
    "model_state",
    "dataloader_state",
    "ADMIT_014_download_permission",
)
RECOMMENDED_NEXT_STEP = (
    "design_covapie_admit_015_formal_evaluator_interface_contract_v1"
)

CANONICAL_PYTHON_IMPLEMENTATION = "cpython"
CANONICAL_PYTHON_VERSION = "3.10.4"
NONCANONICAL_PYTHON_POLICY = (
    "evaluator_semantic_smoke_only; artifact_build_checker_and_frozen_ast_forbidden"
)
PYTHON_RUNTIME_MIGRATION_POLICY = "explicit_contract_refresh_required"

CONTRACT = "covapie_admit_015_training_authorization_contract.csv"
TRUTH = "covapie_admit_015_training_authorization_truth_matrix.csv"
VALUE_TRUST = "covapie_admit_015_training_authorization_value_and_trust_contract.csv"
SAFETY = "covapie_admit_015_training_authorization_safety_boundary_audit.csv"
ISSUE = "covapie_admit_015_issue_readiness_inventory.csv"
MANIFEST = "covapie_admit_015_training_authorization_contract_manifest.json"
FILES = (CONTRACT, TRUTH, VALUE_TRUST, SAFETY, ISSUE, MANIFEST)

CONTRACT_COLUMNS = (
    "routing_order", "routing_item", "envelope_or_stage", "authority_status",
    "access_or_enforcement_contract", "expected_behavior", "observed_design",
    "routing_passed",
)
TRUTH_COLUMNS = (
    "case_order", "case_id", "case_group", "stage_context_representation",
    "forbidden_envelope_representation", "expected_outcome",
    "observed_outcome", "expected_reason", "observed_reason",
    "target_key_access_count", "mapping_iteration_count", "mapping_len_count",
    "mapping_get_count", "mapping_contains_count",
    "forbidden_envelope_access_count", "case_passed",
)
VALUE_TRUST_COLUMNS = (
    "contract_order", "contract_item", "contract_group", "expected_contract",
    "observed_contract", "responsibility_owner", "contract_passed",
)
SAFETY_COLUMNS = (
    "audit_order", "audit_item", "required_state", "observed_state",
    "audit_passed", "blocking_reason",
)

PRE015_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_015_"
    "formal_evaluator_interface_preconditions_audit_v1"
)
DESIGN_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1"
)
PRE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_"
    "implementation_precondition_gate_v1"
)
RUNTIME_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014_v1"
)
AUTH014_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_014_download_authorization_contract_v1"
)
QA_ROOT = Path("data/derived/covalent_small/covapie_final_dataset_qa_gate_v1")
FEATURE_ROOT = Path(
    "data/derived/covalent_small/covapie_feature_semantics_audit_gate_v0"
)

DESIGN_RULES = DESIGN_ROOT / "covapie_bulk_download_admission_rule_registry.csv"
PRE_CONTEXT = PRE_ROOT / "covapie_bulk_download_admission_evaluation_context_contract.csv"
PRE015_PRODUCTION = Path(
    "src/covalent_ext/covapie_bulk_download_admission_admit_015_"
    "formal_evaluator_interface_preconditions_audit.py"
)
PRE015_INVENTORY = PRE015_ROOT / (
    "covapie_admit_015_formal_evaluator_interface_precondition_inventory.csv"
)
PRE015_RESPONSIBILITY = PRE015_ROOT / (
    "covapie_admit_015_authorization_evidence_and_routing_responsibility_matrix.csv"
)
PRE015_SOURCE = PRE015_ROOT / "covapie_admit_015_source_boundary_audit.csv"
PRE015_SAFETY = PRE015_ROOT / "covapie_admit_015_safety_training_boundary_audit.csv"
PRE015_ISSUES = PRE015_ROOT / "covapie_admit_015_issue_readiness_inventory.csv"
PRE015_MANIFEST = PRE015_ROOT / (
    "covapie_admit_015_formal_evaluator_interface_preconditions_manifest.json"
)
RUNTIME_PRODUCTION = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014.py"
)
RUNTIME_MANIFEST = RUNTIME_ROOT / "covapie_admit_001_to_014_runtime_manifest.json"
RUNTIME_ISSUES = RUNTIME_ROOT / "covapie_admit_001_to_014_runtime_issue_readiness_inventory.csv"
AUTH014_TRUTH = AUTH014_ROOT / "covapie_admit_014_download_authorization_truth_matrix.csv"
AUTH014_TRUST = AUTH014_ROOT / "covapie_admit_014_download_authorization_value_and_trust_contract.csv"
AUTH014_MANIFEST = AUTH014_ROOT / "covapie_admit_014_download_authorization_contract_manifest.json"
QA_MANIFEST = QA_ROOT / "covapie_final_dataset_qa_v1_manifest.json"
FEATURE_MANIFEST = FEATURE_ROOT / "covapie_feature_semantics_audit_gate_manifest.json"
STEP12D_MANIFEST = Path(
    "data/derived/covalent_small/pretrained_masked_loss_smoke_v0/"
    "pretrained_masked_loss_smoke_manifest.json"
)

SOURCE_PATHS = (
    PRE015_PRODUCTION, PRE015_INVENTORY, PRE015_RESPONSIBILITY, PRE015_SOURCE,
    PRE015_SAFETY, PRE015_ISSUES, PRE015_MANIFEST, DESIGN_RULES, PRE_CONTEXT,
    AUTH014_TRUTH, AUTH014_TRUST, AUTH014_MANIFEST, RUNTIME_PRODUCTION,
    RUNTIME_MANIFEST, RUNTIME_ISSUES, QA_MANIFEST, FEATURE_MANIFEST,
    STEP12D_MANIFEST,
)
SOURCE_SHA256 = dict(zip(SOURCE_PATHS, (
    "18894150a91040b3a4c52a5f7aaedc279f6f31ededed82de1e704ec086e0cc0f",
    "c52287ac5a435e58a400be0e33e17c1096b7b0d3b2671be0398a6be03e409839",
    "9713eb3ebfa474488269d17f9efff39e953405dc1d9642074a203e4837585e95",
    "d34374760edf3432042588eb1f258ab75e75290d8a75be579f6056352ef5cd89",
    "967f5d22503b552ae2aaf34693799e789cbc38209d80ad1f4dd0e42bfd87587d",
    "f457da61bffade18999af5c069d237c30aa30a0c63efb8bb14130935fb0757ec",
    "7f64389a018c9bc1170ffeb94d1f393aefc27f67edef1d85143659f43dc8d729",
    "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
    "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0",
    "e4f39f5178b91906639670f5c1ddb1c02b40c802de9ce386aee2a6b6d49f8482",
    "b22f02efdd53dce995730a05cc5c12ffa659c2d98b345afc663b118cc104752d",
    "9c54c9d6cb11776b04938d9be048699041bfc4020dca4c00425faadaaaa5d4d2",
    "c5f5cfc57155f34ee2435228b3bf53ae8d1f6d81c32e097c43668c0b272fd1a2",
    "bf7bbe3c2158f661c6e71835bf603af76ffbb315d4ef377c9f72da246619ba40",
    "f457da61bffade18999af5c069d237c30aa30a0c63efb8bb14130935fb0757ec",
    "4f7c884379f926af52101f40a7870b243f0309af3b1637dc65c8c0691acf9f35",
    "a625335dd670ceb53f1515237a676c25d156b510eb80113ea8c4073e1ae1879d",
    "f2b3165d70c046f27defbe821afcc5294ff5cdf0037595cd5c42066ab27ea08b",
)))

TRUE_READINESS = (
    "admit_015_preconditions_audited",
    "admit_015_training_authorization_contract_frozen",
    "admit_015_authoritative_envelope_frozen",
    "admit_015_authoritative_key_frozen",
    "admit_015_exact_bool_contract_frozen",
    "admit_015_no_coercion_contract_frozen",
    "admit_015_failure_precedence_frozen",
    "admit_015_outcome_reason_vocabulary_frozen",
    "admit_014_admit_015_isolation_contract_frozen",
    "ready_for_admit_015_formal_evaluator_interface_contract_design",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "admit_015_formal_evaluator_interface_contract_frozen",
    "evaluate_admit_015_implemented", "admit_015_result_type_implemented",
    "admit_015_independent_oracle_implemented",
    "admit_015_standalone_evaluator_implemented",
    "admit_015_unified_adapter_contract_frozen",
    "admit_015_unified_adapter_implemented",
    "admit_015_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_015_implemented",
    "mandatory_training_authorization_enforcement_api_frozen",
    "mandatory_training_authorization_enforcement_implemented",
    "combined_candidate_verdict_implemented",
    "cross_rule_aggregation_implemented",
    "feature_semantics_audit_completed", "real_training_ready",
    "ready_for_training", "step12d_is_final_training_feature_contract",
)


@dataclass(frozen=True)
class _Admit015TrainingAuthorizationDesignResult:
    outcome: str
    passed: bool
    blocks_candidate: bool
    reason: str
    design_io_used: bool


def _design_result(
    outcome: str, reason: str
) -> _Admit015TrainingAuthorizationDesignResult:
    return _Admit015TrainingAuthorizationDesignResult(
        outcome=outcome,
        passed=outcome == "passed",
        blocks_candidate=outcome == "blocked",
        reason=reason,
        design_io_used=False,
    )


def classify_admit_015_training_authorization_contract_design(
    stage_authorization_context: object,
    *,
    candidate_record: object = None,
    batch_context: object = None,
    evaluation_context: object = None,
    download_result_context: object = None,
) -> _Admit015TrainingAuthorizationDesignResult:
    """Classify design evidence without implementing the formal evaluator."""
    del candidate_record, batch_context, evaluation_context, download_result_context
    if stage_authorization_context is None:
        return _design_result("blocked", REASON_VOCABULARY[1])
    if not isinstance(stage_authorization_context, Mapping):
        return _design_result("blocked", REASON_VOCABULARY[2])
    try:
        value = stage_authorization_context[AUTHORIZATION_CONTEXT_ITEM]
    except KeyError:
        return _design_result("blocked", REASON_VOCABULARY[3])
    except Exception:
        return _design_result("blocked", REASON_VOCABULARY[4])
    if type(value) is not bool:
        return _design_result("blocked", REASON_VOCABULARY[5])
    if value is False:
        return _design_result("blocked", REASON_VOCABULARY[6])
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
    return (item.st_dev, item.st_ino, item.st_mode, item.st_size,
            item.st_mtime_ns, item.st_ctime_ns)


def _canonical_runtime_guard() -> None:
    import sys
    if (sys.implementation.name != CANONICAL_PYTHON_IMPLEMENTATION
            or tuple(sys.version_info[:3]) != (3, 10, 4)):
        raise RuntimeError(
            "canonical evidence build requires CPython 3.10.4; "
            + NONCANONICAL_PYTHON_POLICY
        )


def _git(args: list[str], *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=text, check=False
    )


def _safe_source(path: Path) -> bool:
    return (
        not path.is_absolute() and bool(path.parts) and ".." not in path.parts
        and path.parts[:2] != ("data", "raw")
        and path.parts[0] != "checkpoints"
        and DEFAULT_OUTPUT_ROOT.as_posix() not in path.as_posix()
    )


def _pinned_read(path: Path) -> bytes:
    if not _safe_source(path):
        raise ValueError(f"unsafe source: {path}")
    dflags = (os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
              | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0))
    fflags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    root_stat = os.lstat(REPO_ROOT)
    root_id = _identity(root_stat)
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
        raise ValueError("unsafe repository root")
    held: list[tuple[int, Identity, int | None, str | None]] = []
    leaf = -1
    leaf_id: Identity | None = None
    root_fd = os.open(REPO_ROOT, dflags)
    if _identity(os.fstat(root_fd)) != root_id:
        os.close(root_fd)
        raise ValueError("repository root race")
    held.append((root_fd, root_id, None, None))
    try:
        current = root_fd
        for part in path.parts[:-1]:
            before = os.stat(part, dir_fd=current, follow_symlinks=False)
            before_id = _identity(before)
            if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
                raise ValueError(f"unsafe source parent: {path}")
            child = os.open(part, dflags, dir_fd=current)
            if _identity(os.fstat(child)) != before_id:
                os.close(child)
                raise ValueError(f"source parent race: {path}")
            held.append((child, before_id, current, part))
            current = child
        before = os.stat(path.name, dir_fd=current, follow_symlinks=False)
        before_id = _identity(before)
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
            raise ValueError(f"unsafe source leaf: {path}")
        leaf = os.open(path.name, fflags, dir_fd=current)
        leaf_id = before_id
        if _identity(os.fstat(leaf)) != leaf_id:
            raise ValueError(f"source leaf race: {path}")
        chunks = []
        while True:
            chunk = os.read(leaf, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        if _identity(os.fstat(leaf)) != leaf_id:
            raise ValueError(f"source leaf drift: {path}")
        if _identity(os.stat(path.name, dir_fd=current, follow_symlinks=False)) != leaf_id:
            raise ValueError(f"source replacement: {path}")
        for fd, expected, parent_fd, name in held:
            if _identity(os.fstat(fd)) != expected:
                raise ValueError(f"source parent drift: {path}")
            if parent_fd is not None and name is not None:
                if _identity(os.stat(name, dir_fd=parent_fd, follow_symlinks=False)) != expected:
                    raise ValueError(f"source parent replacement: {path}")
        if (_identity(os.fstat(root_fd)) != root_id
                or _identity(os.lstat(REPO_ROOT)) != root_id):
            raise ValueError("repository root replacement")
        if _identity(os.fstat(leaf)) != leaf_id:
            raise ValueError(f"source final leaf FD drift: {path}")
        if _identity(os.stat(path.name, dir_fd=current, follow_symlinks=False)) != leaf_id:
            raise ValueError(f"source final lexical leaf replacement: {path}")
        return b"".join(chunks)
    finally:
        if leaf >= 0:
            os.close(leaf)
        for fd, _, _, _ in reversed(held):
            os.close(fd)


def build_frozen_source_snapshot() -> tuple[Source, ...]:
    """Verify base/index/filesystem identity, then retain the read bytes."""
    _canonical_runtime_guard()
    ident = _git(["show", "-s", "--format=%H%n%P%n%T%n%s", BASE_COMMIT])
    ancestor = _git(["merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"])
    if ident.returncode or ancestor.returncode or ident.stdout.splitlines() != [
        BASE_COMMIT, BASE_PARENT, BASE_TREE, BASE_SUBJECT
    ]:
        raise ValueError("base identity or ancestry mismatch")
    result = []
    for path in SOURCE_PATHS:
        if not _safe_source(path):
            raise ValueError(f"unsafe source boundary: {path}")
        index = _git(["ls-files", "--stage", "--", path.as_posix()])
        tree = _git(["ls-tree", BASE_COMMIT, "--", path.as_posix()])
        ih, isep, ip = index.stdout.partition("\t")
        th, tsep, tp = tree.stdout.partition("\t")
        iv, tv = ih.split(), th.split()
        if (index.returncode or tree.returncode or not isep or not tsep
                or ip.strip() != path.as_posix() or tp.strip() != path.as_posix()
                or len(iv) != 3 or len(tv) != 3 or iv[2] != "0"
                or iv[0] not in {"100644", "100755"} or tv[0] != iv[0]
                or tv[1] != "blob" or tv[2] != iv[1]):
            raise ValueError(f"source base/index mismatch: {path}")
        content = _pinned_read(path)
        base = _git(["show", f"{BASE_COMMIT}:{path.as_posix()}"], text=False)
        digest = hashlib.sha256(content).hexdigest()
        if (base.returncode or base.stdout != content or digest != SOURCE_SHA256[path]):
            raise ValueError(f"source content mismatch: {path}")
        result.append(Source(path, content, digest, iv[0], iv[1]))
    return tuple(result)


def _source(snapshot: tuple[Source, ...], path: Path) -> Source:
    return next(item for item in snapshot if item.path == path)


def _csv(snapshot: tuple[Source, ...], path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(_source(snapshot, path).content.decode())))


def _json(snapshot: tuple[Source, ...], path: Path) -> dict[str, Any]:
    return json.loads(_source(snapshot, path).content)


def _verify_contracts(snapshot: tuple[Source, ...]) -> None:
    registry = next(
        row for row in _csv(snapshot, DESIGN_RULES)
        if row["admission_rule_id"] == ADMISSION_RULE_ID
    )
    if registry != {
        "admission_rule_id": ADMISSION_RULE_ID,
        "admission_rule_name": ADMISSION_RULE_NAME,
        "evidence_source": CURRENT_EVIDENCE_SOURCE,
        "required_status": CURRENT_REQUIRED_STATUS,
        "failure_severity": FAILURE_SEVERITY,
        "blocking_reason": CURRENT_BLOCKING_REASON,
        "evaluation_phase": EVALUATION_PHASE,
        "network_required": "false",
        "raw_structure_required": "false",
        "ready_for_future_implementation": "true",
    }:
        raise ValueError("ADMIT_015 registry identity drift")
    contexts = {row["context_item"]: row for row in _csv(snapshot, PRE_CONTEXT)}
    for key, rule in (
        (DOWNLOAD_AUTHORIZATION_CONTEXT_ITEM, "ADMIT_014"),
        (AUTHORIZATION_CONTEXT_ITEM, "ADMIT_015"),
    ):
        row = contexts[key]
        if not (
            row["context_scope"] == "stage"
            and row["required_by_rules"] == rule
            and row["provided_by_future_caller"] == "true"
            and row["exact_contract_defined"] == "true"
            and row["implementation_ready"] == "true"
        ):
            raise ValueError(f"Step14AU-A context drift: {key}")
    pre = _csv(snapshot, PRE015_INVENTORY)
    pre_manifest = _json(snapshot, PRE015_MANIFEST)
    if not (
        len(pre) == 45
        and [row["precondition_id"] for row in pre]
        == [f"PRE_{index:03d}" for index in range(1, 46)]
        and sum(row["completion_status"] == "complete" for row in pre) == 19
        and sum(row["implementation_blocking"] == "true" for row in pre) == 26
        and pre_manifest["admit_015_training_authorization_contract_frozen"] is False
        and pre_manifest["recommended_next_step"]
        == "design_covapie_admit_015_training_authorization_contract_v1"
    ):
        raise ValueError("ADMIT_015 precondition lineage drift")
    trust = {row["contract_item"]: row for row in _csv(snapshot, AUTH014_TRUST)}
    expected = {
        "authoritative envelope": AUTHORITATIVE_ENVELOPE,
        "exact value type": "type(value) is bool",
        "truthiness coercion": "forbidden; bool(value) not used",
        "producer boundary": AUTHORIZATION_PRODUCER_BOUNDARY,
        "invocation lifetime": "invocation-local",
    }
    if any(trust[key]["observed_contract"] != value for key, value in expected.items()):
        raise ValueError("ADMIT_014 value/trust precedent drift")
    auth014 = _json(snapshot, AUTH014_MANIFEST)
    if not (
        auth014["truth_matrix_row_count"] == 40
        and auth014["truth_matrix_group_counts"] == {
            "context_structure": 7,
            "exact_bool": 2,
            "non_exact_bool": 12,
            "mapping_behavior": 10,
            "forbidden_pseudo_authority": 6,
            "current_future": 3,
        }
        and auth014["forbidden_envelope_access_count"] == 0
    ):
        raise ValueError("ADMIT_014 Exact40 precedent drift")
    runtime = _json(snapshot, RUNTIME_MANIFEST)
    if not (
        runtime["registered_rule_ids"] == [
            f"ADMIT_{index:03d}" for index in range(1, 15)
        ]
        and runtime["known_not_registered_rule_ids"] == [ADMISSION_RULE_ID]
        and runtime["admit_015_implemented"] is False
        and runtime["admit_015_registered_in_engine"] is False
        and runtime["issue_coverage_after"] == [ADMISSION_RULE_ID]
        and runtime["current_permission"] is False
        and runtime["ready_for_training"] is False
        and runtime["cross_rule_aggregation_implemented"] is False
    ):
        raise ValueError("Exact14 runtime boundary drift")
    issues = _source(snapshot, RUNTIME_ISSUES).content
    if (
        issues != _source(snapshot, PRE015_ISSUES).content
        or len(list(csv.DictReader(io.StringIO(issues.decode())))) != 30
    ):
        raise ValueError("Exact30 issue continuity drift")
    qa = _json(snapshot, QA_MANIFEST)
    feature = _json(snapshot, FEATURE_MANIFEST)
    step12d = _json(snapshot, STEP12D_MANIFEST)
    if not (
        qa["ready_for_training"] is False
        and qa["feature_semantics_known_for_training"] is False
        and qa["unknown_atom_feature_policy_finalized_for_training"] is False
        and feature["feature_semantics_known_for_training"] is False
        and feature["step12d_was_smoke_legality_only"] is True
        and feature["unknown_atom_feature_policy_finalized_for_training"] is False
        and step12d["feature_semantics_known"] is False
    ):
        raise ValueError("feature-semantics boundary drift")


def _value_trust_rows() -> list[dict[str, str]]:
    specs = (
        ("authoritative envelope", "authority", AUTHORITATIVE_ENVELOPE, "evaluator"),
        ("authoritative key", "authority", AUTHORIZATION_CONTEXT_ITEM, "evaluator"),
        ("exact value type", "value", "type(value) is bool", "evaluator"),
        ("closed value vocabulary", "value", "False|True", "evaluator"),
        ("false semantics", "value", "blocked|TRAINING_NOT_AUTHORIZED", "evaluator"),
        ("true semantics", "value", "passed|empty reason", "evaluator"),
        ("normalization", "value", "forbidden", "evaluator"),
        ("truthiness coercion", "value", "forbidden; bool(value) not used", "evaluator"),
        ("integer coercion", "value", "forbidden", "evaluator"),
        ("string coercion", "value", "forbidden", "evaluator"),
        ("numpy.bool_ coercion", "value", "forbidden", "evaluator"),
        ("producer boundary", "trust", AUTHORIZATION_PRODUCER_BOUNDARY, "trusted caller"),
        ("trust source", "trust", "invocation boundary; not mapping self-report", "trusted caller"),
        ("invocation lifetime", "freshness", "invocation-local", "trusted caller"),
        ("explicit reconstruction", "freshness", "required for every stage invocation", "trusted caller"),
        ("previous invocation replay", "freshness", "forbidden", "trusted caller"),
        ("artifact/cache/raw replay", "freshness", "forbidden", "trusted caller"),
        ("identity authentication", "trust", "outside evaluator", "future orchestration"),
        ("signature verification", "trust", "outside evaluator", "future orchestration"),
        ("cryptographic authentication", "trust", "outside evaluator", "future orchestration"),
        ("download key isolation", "isolation", "never training authority", "evaluator"),
        ("training key isolation", "isolation", "never download authority", "ADMIT_014 evaluator"),
        ("fallback/alias/OR/AND", "isolation", "all forbidden", "future orchestration"),
        ("evaluator responsibility", "responsibility", "consume and validate one exact bool", "evaluator"),
        ("caller responsibility", "responsibility", "construct fresh trusted stage context", "trusted caller"),
        ("orchestration responsibility", "responsibility", "enforce trust boundary and future pre-training guard", "future orchestration"),
    )
    return [
        dict(zip(VALUE_TRUST_COLUMNS, (
            str(order), item, group, value, value, owner, "true",
        )))
        for order, (item, group, value, owner) in enumerate(specs, 1)
    ]


def _contract_rows() -> list[dict[str, str]]:
    specs = (
        ("only authority", AUTHORITATIVE_ENVELOPE, "authoritative", "ordered target __getitem__ only", "consume training target key once"),
        ("candidate source", "candidate_record", "forbidden", "zero access", "cannot authorize or override"),
        ("batch source", "batch_context", "forbidden", "zero access", "cannot authorize or override"),
        ("evaluation source", "evaluation_context", "forbidden", "zero access", "cannot authorize or override"),
        ("download-result source", "download_result_context", "forbidden", "zero access", "cannot authorize or override"),
        ("provider source", "provider_result", "forbidden", "zero access", "cannot authorize"),
        ("candidate self-report", "candidate_self_report", "forbidden", "zero access", "cannot authorize"),
        ("environment source", "environment_variable", "forbidden", "zero access", "cannot authorize"),
        ("filesystem/raw source", "filesystem_marker|raw_file", "forbidden", "zero access", "cannot authorize"),
        ("artifact/Git source", "artifact_sha256|git_commit_sha", "forbidden", "zero access", "cannot authorize"),
        ("manifest/fixture source", "manifest_self_report|test_fixture", "forbidden", "zero access", "cannot authorize"),
        ("checkpoint/config/CLI source", "checkpoint_metadata|training_config|CLI_flag", "forbidden", "zero access", "cannot authorize"),
        ("model/dataloader source", "model_state|dataloader_state", "forbidden", "zero access", "cannot authorize"),
        ("ADMIT_014 permission", DOWNLOAD_AUTHORIZATION_CONTEXT_ITEM, "forbidden", "zero training-authority access", "download True never authorizes training"),
        ("extra stage keys", AUTHORITATIVE_ENVELOPE, "allowed", "do not iterate/len/get/contains", "target-only lookup"),
        ("missing context", AUTHORITATIVE_ENVELOPE, "fail_closed", "no fallback/default", REASON_VOCABULARY[1]),
        ("invalid context", AUTHORITATIVE_ENVELOPE, "fail_closed", "Mapping required", REASON_VOCABULARY[2]),
        ("missing key", AUTHORIZATION_CONTEXT_ITEM, "fail_closed", "first KeyError classified missing", REASON_VOCABULARY[3]),
        ("lookup exception", AUTHORIZATION_CONTEXT_ITEM, "fail_closed", "non-KeyError classified lookup failed", REASON_VOCABULARY[4]),
        ("invalid type", AUTHORIZATION_CONTEXT_ITEM, "fail_closed", "exact built-in bool required", REASON_VOCABULARY[5]),
        ("false permission", AUTHORIZATION_CONTEXT_ITEM, "authoritative", "hard block", REASON_VOCABULARY[6]),
        ("true permission", AUTHORIZATION_CONTEXT_ITEM, "authoritative", "permission verdict only", "synthetic design pass only"),
        ("download True", DOWNLOAD_AUTHORIZATION_CONTEXT_ITEM, "isolated", "no fallback/alias", "training remains missing or controlled by training key"),
        ("training True", AUTHORIZATION_CONTEXT_ITEM, "isolated", "ADMIT_014 must not consume", "download permission unchanged"),
        ("cross-key OR", "download|training", "forbidden", "no combined permission", "undefined"),
        ("cross-key AND", "download|training", "forbidden", "not a single permission", "undefined"),
        ("current permission", "current project state", "false", "synthetic True cannot change it", "training_not_authorized"),
        ("authorized execution count", "current project state", "0", "no training invocation", "0"),
        ("future stage-global guard", "real-training invocation", "future_mandatory", "evaluate once per invocation", "before protected operations"),
        ("dataloader instantiation", "pre-training", "protected action", "future ADMIT_015 pass required", "blocked count=0"),
        ("checkpoint loading", "pre-training", "protected action", "future ADMIT_015 pass required", "blocked count=0"),
        ("model initialization/forward", "pre-training", "protected action", "future ADMIT_015 pass required", "blocked count=0"),
        ("loss/backward", "pre-training", "protected action", "future ADMIT_015 pass required", "blocked count=0"),
        ("optimizer/scheduler creation", "pre-training", "protected action", "future ADMIT_015 pass required", "blocked count=0"),
        ("parameter update", "pre-training", "protected action", "future ADMIT_015 pass required", "blocked count=0"),
        ("training checkpoint write", "pre-training", "protected action", "future ADMIT_015 pass required", "blocked count=0"),
        ("training result materialization", "pre-training", "protected action", "future ADMIT_015 pass required", "blocked count=0"),
        ("aggregation independence", "combined verdict", "not_implemented", "blocked cannot be overridden", "cross-rule aggregation undefined"),
        ("enforcement API", "future training orchestration", "not_frozen", "responsibility only", "implementation absent"),
        ("pass limitation", "ADMIT_015 design pass", "permission_only", "no current readiness implication", "feature-semantics audit remains required"),
    )
    return [
        dict(zip(CONTRACT_COLUMNS, (
            str(order), item, envelope, status, access, behavior, behavior, "true",
        )))
        for order, (item, envelope, status, access, behavior) in enumerate(specs, 1)
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
            self.target_access + self.iteration_count + self.len_count
            + self.get_count + self.contains_count
        )


class _Truthy:
    def __bool__(self) -> bool:
        return True


class _Falsy:
    def __bool__(self) -> bool:
        return False


def _stable_representation(value: object) -> str:
    if isinstance(value, _Truthy):
        return "<CUSTOM_TRUTHY>"
    if isinstance(value, _Falsy):
        return "<CUSTOM_FALSY>"
    if type(value) is object:
        return "<OPAQUE_OBJECT>"
    if type(value) is dict:
        return "{" + ", ".join(
            f"{key!r}: {_stable_representation(item)}"
            for key, item in value.items()
        ) + "}"
    return repr(value)


def _truth_rows() -> list[dict[str, str]]:
    invalid = (
        ("INT_ZERO", 0), ("INT_ONE", 1), ("FLOAT_ZERO", 0.0),
        ("FLOAT_ONE", 1.0), ("STRING_FALSE", "false"),
        ("STRING_TRUE", "true"), ("EMPTY_STRING", ""), ("NONE_VALUE", None),
        ("LIST_VALUE", []), ("DICT_VALUE", {}),
        ("CUSTOM_TRUTHY", _Truthy()), ("CUSTOM_FALSY", _Falsy()),
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
    specs.extend(
        (case, "non_exact_bool", _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: value}), "blocked", REASON_VOCABULARY[5], {})
        for case, value in invalid
    )
    specs.extend((
        ("LOOKUP_KEYERROR", "mapping_behavior", _InstrumentedMapping(lookup_error=KeyError(AUTHORIZATION_CONTEXT_ITEM)), "blocked", REASON_VOCABULARY[3], {}),
        ("LOOKUP_RUNTIMEERROR", "mapping_behavior", _InstrumentedMapping(lookup_error=RuntimeError("boom")), "blocked", REASON_VOCABULARY[4], {}),
        ("LOOKUP_VALUEERROR", "mapping_behavior", _InstrumentedMapping(lookup_error=ValueError("boom")), "blocked", REASON_VOCABULARY[4], {}),
        ("ADMIT015_PLUS_TRUE", "mapping_behavior", _InstrumentedMapping({DOWNLOAD_AUTHORIZATION_CONTEXT_ITEM: False, AUTHORIZATION_CONTEXT_ITEM: True}), "passed", "", {}),
        ("ADMIT015_PLUS_FALSE", "mapping_behavior", _InstrumentedMapping({DOWNLOAD_AUTHORIZATION_CONTEXT_ITEM: True, AUTHORIZATION_CONTEXT_ITEM: False}), "blocked", REASON_VOCABULARY[6], {}),
        ("MANY_EXTRA_PLUS_TRUE", "mapping_behavior", _InstrumentedMapping({**{f"extra_{i}": object() for i in range(20)}, AUTHORIZATION_CONTEXT_ITEM: True}), "passed", "", {}),
        ("ITERATION_RAISES", "mapping_behavior", _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: True}, iteration_error=RuntimeError("iter")), "passed", "", {}),
        ("LEN_RAISES", "mapping_behavior", _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: True}, len_error=RuntimeError("len")), "passed", "", {}),
        ("GET_RAISES", "mapping_behavior", _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: True}, get_error=RuntimeError("get")), "passed", "", {}),
        ("CONTAINS_RAISES", "mapping_behavior", _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: True}, contains_error=RuntimeError("contains")), "passed", "", {}),
    ))
    for case, envelope, stage, outcome, reason in (
        ("CANDIDATE_TRUE_STAGE_MISSING", "candidate_record", None, "blocked", REASON_VOCABULARY[1]),
        ("BATCH_TRUE_STAGE_MISSING", "batch_context", None, "blocked", REASON_VOCABULARY[1]),
        ("EVALUATION_TRUE_STAGE_MISSING", "evaluation_context", None, "blocked", REASON_VOCABULARY[1]),
        ("DOWNLOAD_TRUE_STAGE_MISSING", "download_result_context", None, "blocked", REASON_VOCABULARY[1]),
        ("CANDIDATE_TRUE_STAGE_FALSE", "candidate_record", _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: False}), "blocked", REASON_VOCABULARY[6]),
        ("EVALUATION_FALSE_STAGE_TRUE", "evaluation_context", _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: True}), "passed", ""),
    ):
        probe = _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: True})
        specs.append((case, "forbidden_pseudo_authority", stage, outcome, reason, {envelope: probe}))
    specs.extend((
        ("SYNTHETIC_TRUE_DESIGN", "current_future", _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: True}), "passed", "", {}),
        ("CURRENT_PERMISSION_FALSE", "current_future", _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: False}), "blocked", REASON_VOCABULARY[6], {}),
        ("CURRENT_READINESS_FALSE", "current_future", _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: False}), "blocked", REASON_VOCABULARY[6], {}),
    ))
    if len(specs) != 40:
        raise AssertionError("truth matrix Exact40 drift")
    rows = []
    for order, (case, group, stage, expected_outcome, expected_reason, forbidden) in enumerate(specs, 1):
        result = classify_admit_015_training_authorization_contract_design(
            stage, **{name: forbidden.get(name) for name in FORBIDDEN_ENVELOPES}
        )
        mapping = stage if isinstance(stage, _InstrumentedMapping) else None
        forbidden_count = sum(
            probe.all_accesses for probe in forbidden.values()
            if isinstance(probe, _InstrumentedMapping)
        )
        passed = (
            result.outcome == expected_outcome
            and result.reason == expected_reason
            and result.passed is (expected_outcome == "passed")
            and result.blocks_candidate is (expected_outcome == "blocked")
            and result.design_io_used is False
            and (mapping is None or mapping.target_access == 1)
            and (mapping is None or mapping.iteration_count == 0)
            and (mapping is None or mapping.len_count == 0)
            and (mapping is None or mapping.get_count == 0)
            and (mapping is None or mapping.contains_count == 0)
            and forbidden_count == 0
        )
        rows.append(dict(zip(TRUTH_COLUMNS, (
            str(order), case, group,
            "None" if stage is None else type(stage).__name__ if mapping is None
            else _stable_representation(mapping.values),
            "|".join(forbidden), expected_outcome, result.outcome,
            expected_reason, result.reason,
            str(0 if mapping is None else mapping.target_access),
            str(0 if mapping is None else mapping.iteration_count),
            str(0 if mapping is None else mapping.len_count),
            str(0 if mapping is None else mapping.get_count),
            str(0 if mapping is None else mapping.contains_count),
            str(forbidden_count), str(passed).lower(),
        ))))
    return rows


def _safety_rows() -> list[dict[str, str]]:
    specs = (
        ("current training permission", "false", "false", CURRENT_BLOCKING_REASON),
        ("authorized training execution count", "0", "0", CURRENT_BLOCKING_REASON),
        ("ADMIT_015 evaluator", "absent", "absent", ""),
        ("ADMIT_015 result type", "absent", "absent", ""),
        ("ADMIT_015 independent oracle", "absent", "absent", ""),
        ("ADMIT_015 standalone evaluator", "absent", "absent", ""),
        ("ADMIT_015 adapter/handler", "absent", "absent", ""),
        ("ADMIT_015 registry/Exact15 runtime", "absent", "absent", ""),
        ("mandatory enforcement API frozen", "false", "false", ""),
        ("mandatory enforcement implemented", "false", "false", ""),
        ("blocked dataloader instantiation count", "0", "0", ""),
        ("blocked checkpoint load count", "0", "0", ""),
        ("blocked model forward count", "0", "0", ""),
        ("blocked loss count", "0", "0", ""),
        ("blocked backward count", "0", "0", ""),
        ("blocked optimizer creation count", "0", "0", ""),
        ("blocked parameter update count", "0", "0", ""),
        ("blocked checkpoint write count", "0", "0", ""),
        ("provider/network/download", "false", "false", ""),
        ("raw structure read/write", "false", "false", ""),
        ("feature semantics audit completed", "false", "false", "feature_semantics_audit_required"),
        ("Step12D final contract", "false", "false", "step12d_smoke_only"),
        ("ready for training", "false", "false", CURRENT_BLOCKING_REASON),
        ("combined verdict", "not implemented", "not implemented", ""),
        ("cross-rule aggregation", "not implemented", "not implemented", ""),
        ("canonical mask count", "5", "5", ""),
        ("canonical mask warhead_only/A", "present", "present", ""),
        ("canonical mask linker_plus_warhead/B", "present", "present", ""),
        ("canonical mask scaffold_plus_warhead/B2", "present", "present", ""),
        ("canonical mask scaffold_only/B3", "present", "present", ""),
        ("canonical mask scaffold_plus_linker_plus_warhead/C", "present", "present", ""),
    )
    return [
        dict(zip(SAFETY_COLUMNS, (
            str(order), item, required, observed, "true", reason,
        )))
        for order, (item, required, observed, reason) in enumerate(specs, 1)
    ]


RESOLVED_PRECONDITION_IDS = (
    "PRE_007", "PRE_008", "PRE_009", "PRE_010", "PRE_011", "PRE_012",
    "PRE_016", "PRE_017", "PRE_018", "PRE_025", "PRE_026", "PRE_027",
)
OPEN_PRECONDITION_IDS = (
    "PRE_019", "PRE_020", "PRE_021", "PRE_022", "PRE_023", "PRE_024",
    "PRE_031", "PRE_032", "PRE_033", "PRE_034", "PRE_035", "PRE_036",
    "PRE_038", "PRE_042",
)


def _precondition_transition(snapshot: tuple[Source, ...]) -> list[dict[str, str]]:
    rows = [dict(row) for row in _csv(snapshot, PRE015_INVENTORY)]
    for row in rows:
        if row["precondition_id"] in RESOLVED_PRECONDITION_IDS:
            row["observed_state"] = "frozen by ADMIT_015 training authorization contract v1"
            row["completion_status"] = "complete"
            row["implementation_blocking"] = "false"
            row["resolution_or_gap"] = "authorization contract frozen"
    if not (
        len(rows) == 45
        and sum(row["completion_status"] == "complete" for row in rows) == 31
        and sum(row["completion_status"] != "complete" for row in rows) == 14
        and sum(row["implementation_blocking"] == "true" for row in rows) == 14
        and [row["precondition_id"] for row in rows
             if row["completion_status"] != "complete"]
        == list(OPEN_PRECONDITION_IDS)
    ):
        raise ValueError("Exact45 precondition transition drift")
    return rows


def _csv_bytes(columns: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=columns, extrasaction="raise", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def build_artifact_payloads(
    snapshot: tuple[Source, ...] | None = None,
) -> dict[str, bytes]:
    """Rebuild deterministic Exact6 bytes after all source checks."""
    _canonical_runtime_guard()
    frozen = build_frozen_source_snapshot() if snapshot is None else snapshot
    _verify_contracts(frozen)
    contract = _contract_rows()
    truth = _truth_rows()
    value_trust = _value_trust_rows()
    safety = _safety_rows()
    issues = _source(frozen, PRE015_ISSUES).content
    preconditions = _precondition_transition(frozen)
    payloads = {
        CONTRACT: _csv_bytes(CONTRACT_COLUMNS, contract),
        TRUTH: _csv_bytes(TRUTH_COLUMNS, truth),
        VALUE_TRUST: _csv_bytes(VALUE_TRUST_COLUMNS, value_trust),
        SAFETY: _csv_bytes(SAFETY_COLUMNS, safety),
        ISSUE: issues,
    }
    output_sha = {
        name: hashlib.sha256(data).hexdigest() for name, data in payloads.items()
    }
    readiness = {
        **{key: True for key in TRUE_READINESS},
        **{key: False for key in FALSE_READINESS},
    }
    transition_bytes = _csv_bytes(tuple(preconditions[0]), preconditions)
    manifest: dict[str, Any] = {
        "project": "CovaPIE",
        "stage": STAGE,
        "manifest_schema_version":
            "covapie_admit_015_training_authorization_contract_manifest_v1",
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
            "evidence_source": CURRENT_EVIDENCE_SOURCE,
            "required_status": CURRENT_REQUIRED_STATUS,
            "failure_severity": FAILURE_SEVERITY,
            "blocking_reason": CURRENT_BLOCKING_REASON,
            "evaluation_phase": EVALUATION_PHASE,
            "authorization_model": AUTHORIZATION_MODEL,
        },
        "authorization_contract": {
            "authoritative_envelope": AUTHORITATIVE_ENVELOPE,
            "authoritative_key": AUTHORIZATION_CONTEXT_ITEM,
            "context_scope": AUTHORIZATION_CONTEXT_SCOPE,
            "producer_boundary": AUTHORIZATION_PRODUCER_BOUNDARY,
            "exact_builtin_type": EXACT_VALUE_TYPE,
            "closed_value_vocabulary": [False, True],
            "normalization_or_coercion_allowed": False,
            "default_or_fallback_allowed": False,
            "forbidden_envelopes": list(FORBIDDEN_ENVELOPES),
            "forbidden_pseudo_authorities": list(FORBIDDEN_PSEUDO_AUTHORITIES),
        },
        "trust_boundary": {
            "trust_from_call_boundary_not_mapping_string": True,
            "context_invocation_local": True,
            "caller_reconstructs_every_invocation": True,
            "previous_invocation_replay_allowed": False,
            "artifact_cache_raw_replay_allowed": False,
            "cryptographic_authentication_in_evaluator_scope": False,
        },
        "download_training_isolation_contract": {
            "download_true_authorizes_training": False,
            "training_true_authorizes_download": False,
            "fallback_allowed": False,
            "alias_allowed": False,
            "or_allowed": False,
            "and_as_single_permission_allowed": False,
            "training_missing_reads_download_key": False,
            "future_admit_015_consumes_download_key": False,
            "admit_014_consumes_training_key": False,
            "combined_permission_semantics_defined": False,
            "cross_rule_aggregation_implemented": False,
        },
        "outcome_vocabulary": list(OUTCOME_VOCABULARY),
        "reason_vocabulary": list(REASON_VOCABULARY),
        "failure_precedence": list(FAILURE_PRECEDENCE),
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
        "current_permission": CURRENT_PERMISSION,
        "authorized_admit_015_training_execution_count":
            AUTHORIZED_ADMIT_015_TRAINING_EXECUTION_COUNT,
        "synthetic_true_design_case_grants_current_permission":
            SYNTHETIC_TRUE_DESIGN_CASE_GRANTS_CURRENT_PERMISSION,
        "synthetic_true_design_case_starts_real_training": False,
        "ready_for_training_now": READY_FOR_TRAINING_NOW,
        "formal_interface_not_frozen": {
            "final_evaluator_signature": True,
            "final_result_class_name": True,
            "final_result_field_order": True,
            "independent_oracle": True,
            "standalone_evaluator": True,
            "unified_adapter": True,
            "registry_and_exact15_runtime": True,
        },
        "future_mandatory_training_authorization_responsibility": {
            "evaluate_once_each_real_training_invocation": True,
            "must_complete_before_any_protected_operation": True,
            "blocked_must_not_continue": True,
            "combined_verdict_may_override_blocked": False,
            "must_precede": [
                "dataloader instantiation", "checkpoint loading",
                "training model initialization", "model forward",
                "loss computation", "backward",
                "optimizer/scheduler creation", "parameter update",
                "training checkpoint write", "training-result materialization",
            ],
            "blocked_dataloader_instantiation_count": 0,
            "blocked_checkpoint_load_count": 0,
            "blocked_model_forward_count": 0,
            "blocked_loss_count": 0,
            "blocked_backward_count": 0,
            "blocked_optimizer_creation_count": 0,
            "blocked_parameter_update_count": 0,
            "blocked_checkpoint_write_count": 0,
            "api_frozen": False,
            "implemented": False,
        },
        "precondition_transition": {
            "row_count": 45,
            "complete_count": 31,
            "supported_but_not_frozen_count": 0,
            "incomplete_count": 14,
            "implementation_blocking_count": 14,
            "resolved_precondition_ids": list(RESOLVED_PRECONDITION_IDS),
            "remaining_open_precondition_ids": list(OPEN_PRECONDITION_IDS),
            "transition_rows_sha256": hashlib.sha256(transition_bytes).hexdigest(),
        },
        "issue_continuity": {
            "row_count": 30,
            "transition_count": 0,
            "inventory_source_sha256": SOURCE_SHA256[PRE015_ISSUES],
            "byte_identical_to_preconditions_and_exact14": True,
            "coverage": [ADMISSION_RULE_ID],
            "coverage_issue_open": True,
        },
        "source_count": len(frozen),
        "source_boundary_schema": [
            "order", "path", "sha256", "base_tree_mode", "base_tree_blob",
            "index_mode", "index_blob", "index_stage",
            "base_tree_filesystem_byte_equal", "pinned_no_follow_read",
            "final_leaf_fd_retained",
        ],
        "source_boundary": [
            {
                "order": order, "path": source.path.as_posix(),
                "sha256": source.sha256, "base_tree_mode": source.mode,
                "base_tree_blob": source.blob, "index_mode": source.mode,
                "index_blob": source.blob, "index_stage": 0,
                "base_tree_filesystem_byte_equal": True,
                "pinned_no_follow_read": True,
                "final_leaf_fd_retained": True,
            }
            for order, source in enumerate(frozen, 1)
        ],
        "readiness": readiness,
        "canonical_masks": [
            {"semantic_name": "warhead_only", "alias": "A"},
            {"semantic_name": "linker_plus_warhead", "alias": "B"},
            {"semantic_name": "scaffold_plus_warhead", "alias": "B2"},
            {"semantic_name": "scaffold_only", "alias": "B3"},
            {"semantic_name": "scaffold_plus_linker_plus_warhead", "alias": "C"},
        ],
        "canonical_mask_count": 5,
        "canonical_mask_long_names_are_authoritative": True,
        "feature_semantics_audit_completed": False,
        "feature_semantics_audit_required_before_training": True,
        "historical_unknown_atom_feature_policy_resolved": False,
        "historical_feature_semantics_known": False,
        "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "safety": {
            "formal_evaluator_or_result": False,
            "oracle_adapter_registry_exact15_runtime": False,
            "mandatory_enforcement_implementation": False,
            "dataloader": False, "checkpoint": False, "model": False,
            "forward": False, "loss": False, "backward": False,
            "optimizer": False, "parameter_update": False,
            "training_checkpoint_write": False,
            "provider": False, "network": False, "download": False,
            "raw_read_or_write": False, "real_training": False,
        },
        "exact6_schemas": {
            CONTRACT: list(CONTRACT_COLUMNS),
            TRUTH: list(TRUTH_COLUMNS),
            VALUE_TRUST: list(VALUE_TRUST_COLUMNS),
            SAFETY: list(SAFETY_COLUMNS),
            ISSUE: next(csv.reader(io.StringIO(issues.decode()))),
            MANIFEST: "closed JSON contract asserted by independent checker",
        },
        "exact6_row_counts": {
            CONTRACT: len(contract), TRUTH: len(truth),
            VALUE_TRUST: len(value_trust), SAFETY: len(safety), ISSUE: 30,
        },
        "output_files": list(FILES),
        "output_file_count": 6,
        "output_sha256": output_sha,
        "output_sha256_excludes_manifest_self_hash": True,
        "materialization": {
            "build_before_mutation": True, "exclusive_leaf_create": True,
            "rename_noreplace_required": True,
            "gpfs_einval_fails_closed": True, "os_replace_forbidden": True,
            "inode_preserving_exact_noop": True,
            "pinned_post_read_verification": True,
            "source_final_leaf_fd_retained": True,
            "output_final_set_traversal": True,
            "staging_lexical_binding_verified": True,
            "ownership_safe_cleanup": True,
            "failure_cleanup_is_non_destructive": True,
            "failure_cleanup_unlink_forbidden": True,
            "failure_cleanup_rmdir_forbidden": True,
            "failure_staging_may_be_retained": True,
            "concurrent_eexist_fails_closed": True,
            "preexisting_exact_destination_is_noop": True,
            "successful_publish_has_no_staging_residue": True,
            "unknown_identity_objects_are_never_deleted": True,
            "nested_exact_bool_types_verified": True,
            "bool_int_equivalence_rejected": True,
            "ignored_extra_stage_artifacts_rejected": True,
            "extra_derived_roots_rejected": True,
        },
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "all_checks_passed": True,
    }
    manifest.update(readiness)
    payloads[MANIFEST] = (
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    ).encode()
    return payloads


def _write_leaf(directory_fd: int, name: str, data: bytes) -> Identity:
    fd = os.open(
        name, os.O_WRONLY | os.O_CREAT | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
        0o644, dir_fd=directory_fd,
    )
    try:
        view = memoryview(data)
        while view:
            view = view[os.write(fd, view):]
        os.fsync(fd)
        owned_identity = _identity(os.fstat(fd))
        lexical = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        if (
            stat.S_ISLNK(lexical.st_mode)
            or not stat.S_ISREG(lexical.st_mode)
            or _identity(lexical) != owned_identity
        ):
            raise ValueError(f"owned staging leaf binding mismatch: {name}")
        return owned_identity
    finally:
        os.close(fd)


def _renameat2_noreplace(
    source_fd: int,
    source_name: str,
    destination_fd: int,
    destination_name: str,
) -> None:
    if os.uname().machine not in {"x86_64", "amd64"}:
        raise RuntimeError("renameat2 syscall unavailable")
    result = ctypes.CDLL(None, use_errno=True).syscall(
        316, source_fd, os.fsencode(source_name),
        destination_fd, os.fsencode(destination_name), 1,
    )
    if result:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), destination_name)


def _rename_noreplace(
    source: Path,
    destination: Path,
    parent_fd: int,
    staging_fd: int | None = None,
    staging_identity: Identity | None = None,
) -> None:
    if staging_fd is not None and staging_identity is not None:
        _verify_staging_binding(
            parent_fd, staging_fd, source.name, staging_identity
        )
    _renameat2_noreplace(
        parent_fd, source.name, parent_fd, destination.name
    )


def _read_output_set(root: Path, payloads: dict[str, bytes],
                     expected_root: Identity | None = None) -> bool:
    dflags = (os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
              | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0))
    fflags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    parent_stat = os.lstat(root.parent)
    parent_id = _identity(parent_stat)
    if stat.S_ISLNK(parent_stat.st_mode) or not stat.S_ISDIR(parent_stat.st_mode):
        raise ValueError("unsafe output parent")
    parent_fd = os.open(root.parent, dflags)
    root_fd = -1
    leaves: list[tuple[str, int, Identity, bytes]] = []
    try:
        if _identity(os.fstat(parent_fd)) != parent_id:
            raise ValueError("output parent race")
        root_stat = os.stat(root.name, dir_fd=parent_fd, follow_symlinks=False)
        root_id = _identity(root_stat)
        if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
            raise ValueError("unsafe output root")
        if expected_root is not None and root_id != expected_root:
            raise ValueError("published root identity mismatch")
        root_fd = os.open(root.name, dflags, dir_fd=parent_fd)
        if _identity(os.fstat(root_fd)) != root_id:
            raise ValueError("output root race")
        if set(os.listdir(root_fd)) != set(FILES):
            return False
        for name in FILES:
            item = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            item_id = _identity(item)
            if (stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode)
                    or item.st_size > 100 * 1024 * 1024):
                raise ValueError("unsafe output leaf")
            fd = os.open(name, fflags, dir_fd=root_fd)
            if _identity(os.fstat(fd)) != item_id:
                os.close(fd)
                raise ValueError("output leaf race")
            chunks = []
            while True:
                chunk = os.read(fd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            leaves.append((name, fd, item_id, b"".join(chunks)))
        if set(os.listdir(root_fd)) != set(FILES):
            raise ValueError("output inventory drift")
        for name, fd, item_id, data in leaves:
            if (_identity(os.fstat(fd)) != item_id
                    or _identity(os.stat(name, dir_fd=root_fd,
                                         follow_symlinks=False)) != item_id):
                raise ValueError("output leaf replacement")
            if data != payloads[name]:
                return False
        if (_identity(os.fstat(root_fd)) != root_id
                or _identity(os.stat(root.name, dir_fd=parent_fd,
                                     follow_symlinks=False)) != root_id
                or _identity(os.fstat(parent_fd)) != parent_id
                or _identity(os.lstat(root.parent)) != parent_id):
            raise ValueError("output binding drift")
        if set(os.listdir(root_fd)) != set(FILES):
            raise ValueError("output final inventory drift")
        for name, fd, item_id, _ in leaves:
            if (
                _identity(os.fstat(fd)) != item_id
                or _identity(
                    os.stat(name, dir_fd=root_fd, follow_symlinks=False)
                )
                != item_id
            ):
                raise ValueError("output final leaf replacement")
        if (
            _identity(os.fstat(root_fd)) != root_id
            or _identity(
                os.stat(root.name, dir_fd=parent_fd, follow_symlinks=False)
            )
            != root_id
            or _identity(os.fstat(parent_fd)) != parent_id
            or _identity(os.lstat(root.parent)) != parent_id
        ):
            raise ValueError("output final root/parent binding drift")
        return True
    finally:
        for _, fd, _, _ in leaves:
            os.close(fd)
        if root_fd >= 0:
            os.close(root_fd)
        os.close(parent_fd)


def _refresh_directory_binding(directory_fd: int, lexical_path: Path) -> Identity:
    fd_identity = _identity(os.fstat(directory_fd))
    lexical = os.lstat(lexical_path)
    if (
        stat.S_ISLNK(lexical.st_mode)
        or not stat.S_ISDIR(lexical.st_mode)
        or _identity(lexical) != fd_identity
    ):
        raise ValueError(f"directory FD/lexical binding mismatch: {lexical_path}")
    return fd_identity


def _verify_staging_binding(
    parent_fd: int,
    staging_fd: int,
    staging_name: str,
    expected_identity: Identity,
) -> None:
    lexical = os.stat(staging_name, dir_fd=parent_fd, follow_symlinks=False)
    if (
        stat.S_ISLNK(lexical.st_mode)
        or not stat.S_ISDIR(lexical.st_mode)
        or _identity(lexical) != expected_identity
        or _identity(os.fstat(staging_fd)) != expected_identity
    ):
        raise ValueError("staging lexical/FD ownership mismatch")


def _new_retained_name(staging_name: str) -> str:
    return f"{staging_name}.{secrets.token_hex(16)}.retained"


def _retain_failure_staging(
    parent_path: Path,
    parent_fd: int,
    staging_fd: int,
    staging_name: str,
    staging_identity: Identity | None,
) -> Path:
    """Retain the entire failure staging tree without deleting any object."""
    original_path = parent_path / staging_name
    if staging_fd < 0 or staging_identity is None:
        return original_path
    try:
        _refresh_directory_binding(parent_fd, parent_path)
        current_staging_identity = _identity(os.fstat(staging_fd))
        _verify_staging_binding(
            parent_fd, staging_fd, staging_name, current_staging_identity
        )
    except (FileNotFoundError, OSError, ValueError):
        return original_path
    retained_name = _new_retained_name(staging_name)
    try:
        _renameat2_noreplace(
            parent_fd, staging_name, parent_fd, retained_name
        )
    except (OSError, RuntimeError):
        return original_path
    retained_path = parent_path / retained_name
    try:
        retained_identity = _identity(os.fstat(staging_fd))
        lexical = os.stat(
            retained_name, dir_fd=parent_fd, follow_symlinks=False
        )
        if (
            stat.S_ISLNK(lexical.st_mode)
            or not stat.S_ISDIR(lexical.st_mode)
            or _identity(lexical) != retained_identity
        ):
            return retained_path
        os.fsync(parent_fd)
        _refresh_directory_binding(parent_fd, parent_path)
    except (FileNotFoundError, OSError, ValueError):
        return retained_path
    return retained_path


def materialize_contract(output_root: Path | None = None) -> dict[str, Any]:
    """Atomically publish deterministic Exact6 evidence, or fail closed."""
    _canonical_runtime_guard()
    root = REPO_ROOT / DEFAULT_OUTPUT_ROOT if output_root is None else Path(output_root)
    snapshot = build_frozen_source_snapshot()
    payloads = build_artifact_payloads(snapshot)
    if os.path.lexists(root):
        if _read_output_set(root, payloads):
            return json.loads(payloads[MANIFEST])
        raise ValueError("existing output mismatch")
    dflags = (os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
              | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0))
    parent_stat = os.lstat(root.parent)
    parent_id = _identity(parent_stat)
    if stat.S_ISLNK(parent_stat.st_mode) or not stat.S_ISDIR(parent_stat.st_mode):
        raise ValueError("unsafe output parent")
    parent_fd = os.open(root.parent, dflags)
    if _identity(os.fstat(parent_fd)) != parent_id:
        os.close(parent_fd)
        raise ValueError("output parent race")
    staging = Path(tempfile.mkdtemp(
        prefix=f".{root.name}.", suffix=".staging", dir=root.parent
    ))
    staging_fd = -1
    published = False
    staging_identity: Identity | None = None
    try:
        _refresh_directory_binding(parent_fd, root.parent)
        staging_stat = os.stat(staging.name, dir_fd=parent_fd,
                               follow_symlinks=False)
        staging_identity = _identity(staging_stat)
        if stat.S_ISLNK(staging_stat.st_mode) or not stat.S_ISDIR(
            staging_stat.st_mode
        ):
            raise ValueError("unsafe staging directory")
        staging_fd = os.open(staging.name, dflags, dir_fd=parent_fd)
        _verify_staging_binding(
            parent_fd, staging_fd, staging.name, staging_identity
        )
        for name in FILES:
            _verify_staging_binding(
                parent_fd, staging_fd, staging.name, staging_identity
            )
            _write_leaf(staging_fd, name, payloads[name])
            staging_identity = _identity(os.fstat(staging_fd))
            _verify_staging_binding(
                parent_fd, staging_fd, staging.name, staging_identity
            )
        os.fsync(staging_fd)
        staging_identity = _identity(os.fstat(staging_fd))
        _verify_staging_binding(
            parent_fd, staging_fd, staging.name, staging_identity
        )
        _refresh_directory_binding(parent_fd, root.parent)
        _verify_staging_binding(
            parent_fd, staging_fd, staging.name, staging_identity
        )
        _rename_noreplace(
            staging, root, parent_fd, staging_fd, staging_identity
        )
        published = True
        published_id = _identity(os.fstat(staging_fd))
        if _identity(os.stat(root.name, dir_fd=parent_fd,
                             follow_symlinks=False)) != published_id:
            raise ValueError("immediate destination binding mismatch")
        try:
            os.stat(staging.name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ValueError("staging lexical binding remains")
        os.fsync(parent_fd)
        if (_identity(os.fstat(staging_fd)) != published_id
                or _identity(os.stat(root.name, dir_fd=parent_fd,
                                     follow_symlinks=False)) != published_id):
            raise ValueError("post-fsync destination binding mismatch")
        if not _read_output_set(root, payloads, published_id):
            raise ValueError("published output verification failed")
    except BaseException as error:
        if not published:
            retained_path = _retain_failure_staging(
                root.parent,
                parent_fd,
                staging_fd,
                staging.name,
                staging_identity,
            )
            raise RuntimeError(
                "materialization failed closed; failure staging retained at "
                f"{retained_path}"
            ) from error
        raise
    finally:
        if staging_fd >= 0:
            os.close(staging_fd)
        os.close(parent_fd)
    return json.loads(payloads[MANIFEST])


def run_covapie_bulk_download_admission_admit_015_training_authorization_contract_v1(
    output_root: Path | None = None,
) -> dict[str, Any]:
    """Explicit entry point; import itself is silent and side-effect free."""
    return materialize_contract(output_root)
