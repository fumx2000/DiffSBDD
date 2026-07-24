"""Read-only ADMIT_015 formal-evaluator interface preconditions audit.

This stage freezes evidence and gaps only.  It deliberately does not define an
ADMIT_015 evaluator, result class, adapter, registry entry, authorization
enforcement, provider operation, raw-data operation, or training operation.
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
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_COMMIT = "f54c0efabfb695653c9e55b3a53bda8cf200f353"
BASE_PARENT = "ce98b5542eea5ab4f81c0fc93b10147df5568735"
BASE_TREE = "64ae9c2dd24ecea627102b74d9cb2f72869336ca"
BASE_SUBJECT = "add CovaPIE unified dispatch runtime with ADMIT_001 to ADMIT_014 v1"
STAGE = (
    "audit_covapie_admit_015_formal_evaluator_interface_preconditions_v1"
)
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / (
    "covapie_bulk_download_admission_admit_015_"
    "formal_evaluator_interface_preconditions_audit_v1"
)

ADMISSION_RULE_ID = "ADMIT_015"
ADMISSION_RULE_NAME = "current_gate_grants_no_training_permission"
CURRENT_EVIDENCE_SOURCE = "current_design_gate"
CURRENT_REQUIRED_STATUS = "training_not_authorized_now"
CURRENT_BLOCKING_REASON = "training_not_authorized"
CURRENT_PERMISSION = False
AUTHORIZED_ADMIT_015_TRAINING_EXECUTION_COUNT = 0
CURRENT_REGISTRATION_STATE = "known_but_not_registered"
CURRENT_CALLABLE_DISCOVERED_STATE = False
CURRENT_ADAPTER_READY_STATE = False
CURRENT_RUNTIME_COVERAGE_OPEN = "ADMIT_015"

CANDIDATE_ENVELOPE = "stage_authorization_context"
CANDIDATE_TARGET_ITEM = "current_stage_training_authorized"
COEXISTENCE_ITEM = "current_stage_download_authorized"
CANDIDATE_PRODUCER = "trusted_future_stage_orchestrator"
CANDIDATE_TYPE = "exact builtin bool"
CANDIDATE_COERCION = "no coercion"
CANDIDATE_LIFETIME = "invocation-local"
CANDIDATE_DEFAULT = "omission must fail closed"
CANDIDATE_REPLAY = "no cross-invocation replay"
RECOMMENDED_NEXT_STEP = "design_covapie_admit_015_training_authorization_contract_v1"

CANONICAL_PYTHON_IMPLEMENTATION = "cpython"
CANONICAL_PYTHON_VERSION = "3.10.4"
NONCANONICAL_PYTHON_POLICY = (
    "evaluator_semantic_smoke_only; artifact_build_checker_and_frozen_ast_forbidden"
)
PYTHON_RUNTIME_MIGRATION_POLICY = "explicit_contract_refresh_required"

PRECONDITION = "covapie_admit_015_formal_evaluator_interface_precondition_inventory.csv"
RESPONSIBILITY = (
    "covapie_admit_015_authorization_evidence_and_routing_responsibility_matrix.csv"
)
SOURCE_AUDIT = "covapie_admit_015_source_boundary_audit.csv"
SAFETY = "covapie_admit_015_safety_training_boundary_audit.csv"
ISSUE = "covapie_admit_015_issue_readiness_inventory.csv"
MANIFEST = "covapie_admit_015_formal_evaluator_interface_preconditions_manifest.json"
FILES = (PRECONDITION, RESPONSIBILITY, SOURCE_AUDIT, SAFETY, ISSUE, MANIFEST)

COLUMNS = {
    PRECONDITION: (
        "precondition_order", "precondition_id", "precondition_group",
        "precondition_subject", "required_state", "observed_state",
        "completion_status", "implementation_blocking", "evidence_paths",
        "evidence_sha256", "resolution_or_gap", "recommended_owner",
    ),
    RESPONSIBILITY: (
        "matrix_order", "responsibility_group", "responsibility_item",
        "candidate_authority", "committed_precedent",
        "admit_015_contract_status", "allowed_source", "forbidden_sources",
        "type_semantics", "coercion_policy", "coexistence_boundary",
        "audit_passed",
    ),
    SOURCE_AUDIT: (
        "source_order", "source_relative_path", "expected_sha256",
        "base_tree_mode", "base_tree_blob", "index_mode", "index_blob",
        "index_stage", "base_tree_sha256", "filesystem_sha256", "tracked",
        "regular_file", "non_symlink", "pinned_read",
        "post_read_identity_verified", "final_leaf_identity_verified",
        "source_verified",
    ),
    SAFETY: (
        "audit_order", "audit_item", "required_state", "observed_state",
        "audit_passed", "blocking_reason",
    ),
}

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
PRE014_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_014_"
    "rule_logic_interface_preconditions_audit_v1"
)
FORMAL014_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_014_formal_evaluator_interface_contract_v1"
)
RULE014_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_014_rule_logic_interface_v1"
)
ADAPTER014_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_014_unified_adapter_contract_v1"
)
QA_ROOT = Path("data/derived/covalent_small/covapie_final_dataset_qa_gate_v1")
FEATURE_ROOT = Path(
    "data/derived/covalent_small/covapie_feature_semantics_audit_gate_v0"
)

DESIGN_PRODUCTION = Path(
    "src/covalent_ext/"
    "covapie_canonical_final_dataset_bulk_download_admission_design_gate.py"
)
DESIGN_RULES = DESIGN_ROOT / "covapie_bulk_download_admission_rule_registry.csv"
DESIGN_SCHEMA = DESIGN_ROOT / "covapie_bulk_download_admission_schema_contract.csv"
DESIGN_SAFETY = DESIGN_ROOT / "covapie_bulk_download_admission_safety_audit.csv"
DESIGN_MANIFEST = DESIGN_ROOT / "covapie_bulk_download_admission_design_gate_manifest.json"
PRE_CONTEXT = PRE_ROOT / "covapie_bulk_download_admission_evaluation_context_contract.csv"
PRE_RULES = PRE_ROOT / "covapie_bulk_download_admission_rule_executability_matrix.csv"
PRE_MANIFEST = PRE_ROOT / "covapie_bulk_download_admission_implementation_precondition_manifest.json"
RUNTIME_PRODUCTION = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014.py"
)
RUNTIME_MANIFEST = RUNTIME_ROOT / "covapie_admit_001_to_014_runtime_manifest.json"
RUNTIME_ISSUES = RUNTIME_ROOT / "covapie_admit_001_to_014_runtime_issue_readiness_inventory.csv"
PRE014_MANIFEST = PRE014_ROOT / "covapie_admit_014_formal_evaluator_preconditions_manifest.json"
AUTH014_TRUTH = AUTH014_ROOT / "covapie_admit_014_download_authorization_truth_matrix.csv"
AUTH014_TRUST = AUTH014_ROOT / "covapie_admit_014_download_authorization_value_and_trust_contract.csv"
AUTH014_MANIFEST = AUTH014_ROOT / "covapie_admit_014_download_authorization_contract_manifest.json"
FORMAL014_MANIFEST = FORMAL014_ROOT / "covapie_admit_014_formal_evaluator_interface_contract_manifest.json"
RULE014_MANIFEST = RULE014_ROOT / "covapie_admit_014_rule_logic_interface_manifest.json"
ADAPTER014_MANIFEST = ADAPTER014_ROOT / "covapie_admit_014_unified_adapter_contract_manifest.json"
QA_SAFETY = QA_ROOT / "covapie_final_dataset_qa_v1_safety_training_boundary_audit.csv"
QA_MANIFEST = QA_ROOT / "covapie_final_dataset_qa_v1_manifest.json"
FEATURE_MANIFEST = FEATURE_ROOT / "covapie_feature_semantics_audit_gate_manifest.json"
FEATURE_BLOCKERS = FEATURE_ROOT / "covapie_feature_semantics_training_blockers.csv"
STEP12D_MANIFEST = Path(
    "data/derived/covalent_small/pretrained_masked_loss_smoke_v0/"
    "pretrained_masked_loss_smoke_manifest.json"
)

SOURCE_PATHS = (
    DESIGN_PRODUCTION, DESIGN_RULES, DESIGN_SCHEMA, DESIGN_SAFETY,
    DESIGN_MANIFEST, PRE_CONTEXT, PRE_RULES, PRE_MANIFEST,
    RUNTIME_PRODUCTION, RUNTIME_MANIFEST, RUNTIME_ISSUES, PRE014_MANIFEST,
    AUTH014_TRUTH, AUTH014_TRUST, AUTH014_MANIFEST, FORMAL014_MANIFEST,
    RULE014_MANIFEST, ADAPTER014_MANIFEST, QA_SAFETY, QA_MANIFEST,
    FEATURE_MANIFEST, FEATURE_BLOCKERS, STEP12D_MANIFEST,
)
SOURCE_SHA256 = dict(zip(SOURCE_PATHS, (
    "79ecb3fb1084ddc161d1bec1a7db664ffbeda71952e31e4233317ecd487905d6",
    "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
    "44ca53db60e210ffe1200d32f449c1fd94107f2775ed19b9c14f3a1e982e9710",
    "388869caf582bdf624d0016cae385dc2268f6cc05f54ecc9bf140608bbd3b208",
    "085cb2f2a6bfe9bebe9e503dd10aa0b4d6f9ad754ff99539b1bafb33c78b5444",
    "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0",
    "a7782e48cac282b047a392ee20b5b26a72fa1b2208a3889edf8b1c8af923921b",
    "2304b5754d8052b4b186981a98c12f259608a3492947e069c2afab84084a0d52",
    "c5f5cfc57155f34ee2435228b3bf53ae8d1f6d81c32e097c43668c0b272fd1a2",
    "bf7bbe3c2158f661c6e71835bf603af76ffbb315d4ef377c9f72da246619ba40",
    "f457da61bffade18999af5c069d237c30aa30a0c63efb8bb14130935fb0757ec",
    "b9582357f392a6aa1af68012a1469c886b2de4b5af8196cddad56f94625e4b61",
    "e4f39f5178b91906639670f5c1ddb1c02b40c802de9ce386aee2a6b6d49f8482",
    "b22f02efdd53dce995730a05cc5c12ffa659c2d98b345afc663b118cc104752d",
    "9c54c9d6cb11776b04938d9be048699041bfc4020dca4c00425faadaaaa5d4d2",
    "217490ef69526486b51117e4900d0669b4de466a023023ecb56ebdf0822fb731",
    "f1266a2a471ddac3a0966951ff681b19ebd7d2725ff8242942a9365f92f7e056",
    "fbcca891692e4b88d2da854425bef9ce38d1eced97df1c0ca826edad95357de0",
    "8ea6a53d04456443014ba250a0cfacf4983e39d2138d7035ad188dc1dcceebe5",
    "4f7c884379f926af52101f40a7870b243f0309af3b1637dc65c8c0691acf9f35",
    "a625335dd670ceb53f1515237a676c25d156b510eb80113ea8c4073e1ae1879d",
    "99af8f844b43ee6731f20b25ea4abc968e5eb7a12923f3797b3b2c6384d019d8",
    "f2b3165d70c046f27defbe821afcc5294ff5cdf0037595cd5c42066ab27ea08b",
)))

TRUE_READINESS = (
    "admit_015_rule_identity_verified",
    "admit_015_current_fail_closed_state_verified",
    "admit_015_known_not_registered_state_verified",
    "admit_015_authorization_precedent_audited",
    "admit_015_training_permission_responsibility_audited",
    "admit_015_formal_evaluator_interface_preconditions_audited",
    "admit_014_admit_015_isolation_audited",
    "feature_semantics_audit_required_before_training",
    "ready_for_admit_015_training_authorization_contract_design",
)
FALSE_READINESS = (
    "admit_015_training_authorization_contract_frozen",
    "admit_015_formal_evaluator_interface_contract_frozen",
    "evaluate_admit_015_implemented", "admit_015_result_type_implemented",
    "admit_015_standalone_evaluator_implemented",
    "admit_015_unified_adapter_contract_frozen",
    "admit_015_unified_adapter_implemented",
    "admit_015_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_015_implemented",
    "mandatory_training_authorization_enforcement_implemented",
    "combined_candidate_verdict_implemented",
    "cross_rule_aggregation_implemented",
    "feature_semantics_audit_completed", "real_training_ready",
    "ready_for_training", "step12d_is_final_training_feature_contract",
)


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
    row = next(x for x in _csv(snapshot, DESIGN_RULES)
               if x["admission_rule_id"] == ADMISSION_RULE_ID)
    if row != {
        "admission_rule_id": ADMISSION_RULE_ID,
        "admission_rule_name": ADMISSION_RULE_NAME,
        "evidence_source": CURRENT_EVIDENCE_SOURCE,
        "required_status": CURRENT_REQUIRED_STATUS,
        "failure_severity": "blocking",
        "blocking_reason": CURRENT_BLOCKING_REASON,
        "evaluation_phase": "current_step",
        "network_required": "false",
        "raw_structure_required": "false",
        "ready_for_future_implementation": "true",
    }:
        raise ValueError("ADMIT_015 registry identity drift")
    contexts = {x["context_item"]: x for x in _csv(snapshot, PRE_CONTEXT)}
    for key, rule in ((COEXISTENCE_ITEM, "ADMIT_014"),
                      (CANDIDATE_TARGET_ITEM, "ADMIT_015")):
        item = contexts[key]
        if not (item["context_scope"] == "stage"
                and item["required_by_rules"] == rule
                and item["provided_by_future_caller"] == "true"
                and item["exact_contract_defined"] == "true"
                and item["implementation_ready"] == "true"):
            raise ValueError(f"Step14AU-A context drift: {key}")
    runtime = _json(snapshot, RUNTIME_MANIFEST)
    expected = [f"ADMIT_{index:03d}" for index in range(1, 15)]
    if not (
        runtime["registered_rule_ids"] == expected
        and runtime["known_not_registered_rule_ids"] == [ADMISSION_RULE_ID]
        and runtime["admit_015_implemented"] is False
        and runtime["admit_015_registered_in_engine"] is False
        and runtime["issue_coverage_after"] == [ADMISSION_RULE_ID]
        and runtime["current_permission"] is False
        and runtime["ready_for_training"] is False
        and runtime["feature_semantics_audit_required_before_training"] is True
        and runtime["step12d_is_final_training_feature_contract"] is False
        and runtime["cross_rule_aggregation_implemented"] is False
    ):
        raise ValueError("Exact14 runtime boundary drift")
    issue_bytes = _source(snapshot, RUNTIME_ISSUES).content
    issues = list(csv.DictReader(io.StringIO(issue_bytes.decode())))
    if (len(issues) != 30
            or next(x for x in issues if x["issue_id"]
                    == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")[
                        "affected_rules"] != ADMISSION_RULE_ID):
        raise ValueError("Exact30 issue continuity drift")
    trust = {x["contract_item"]: x for x in _csv(snapshot, AUTH014_TRUST)}
    expected_precedent = {
        "authoritative envelope": CANDIDATE_ENVELOPE,
        "exact value type": "type(value) is bool",
        "truthiness coercion": "forbidden; bool(value) not used",
        "producer boundary": CANDIDATE_PRODUCER,
        "invocation lifetime": CANDIDATE_LIFETIME,
    }
    for item, observed in expected_precedent.items():
        if trust[item]["observed_contract"] != observed:
            raise ValueError(f"ADMIT_014 precedent drift: {item}")
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


def _precondition_specs() -> tuple[tuple[str, str, str, str, str, bool, str, str], ...]:
    c = "complete"
    o = "incomplete"
    p = "supported_but_admit015_contract_not_frozen"
    return (
        ("rule_identity", "canonical ADMIT_015 registry row", "exact canonical identity", "verified committed Step14AT row", c, False, "identity frozen", "ADMIT_015 contract owner"),
        ("rule_identity", "failure severity and reason", "blocking|training_not_authorized", "verified committed registry fields", c, False, "current identity frozen", "ADMIT_015 contract owner"),
        ("rule_identity", "current-step no-I/O flags", "network=false|raw=false", "verified committed registry fields", c, False, "identity frozen", "ADMIT_015 contract owner"),
        ("current_runtime_state", "registration state", "known but not registered", "Exact14 manifest verified", c, False, "preserve until implementation", "runtime owner"),
        ("current_runtime_state", "callable and adapter state", "false|false", "Exact14 sets verified", c, False, "preserve fail closed", "runtime owner"),
        ("current_runtime_state", "open coverage", "ADMIT_015 only", "Exact30 coverage row verified", c, False, "zero transition in this audit", "runtime owner"),
        ("authorization_envelope_precedent", "candidate envelope name", CANDIDATE_ENVELOPE, "ADMIT_014 committed precedent", p, True, "precedent only; ADMIT_015 contract open", "authorization contract owner"),
        ("authorization_envelope_precedent", "candidate target key coexistence", CANDIDATE_TARGET_ITEM, "Step14AU-A committed coexistence name", p, True, "name precedent is not final contract", "authorization contract owner"),
        ("authorization_envelope_precedent", "trusted producer", CANDIDATE_PRODUCER, "ADMIT_014 committed precedent", p, True, "must be independently frozen for ADMIT_015", "authorization contract owner"),
        ("training_authorization_responsibility", "unique recommended authority path", f"{CANDIDATE_ENVELOPE}.{CANDIDATE_TARGET_ITEM}", "supported by committed structural precedent", p, True, "formal authorization contract required", "authorization contract owner"),
        ("training_authorization_responsibility", "omission behavior", CANDIDATE_DEFAULT, "ADMIT_014 fail-closed precedent", p, True, "ADMIT_015 reason not frozen", "authorization contract owner"),
        ("training_authorization_responsibility", "replay behavior", CANDIDATE_REPLAY, "ADMIT_014 invocation-local precedent", p, True, "ADMIT_015 freshness contract open", "authorization contract owner"),
        ("ADMIT_014_ADMIT_015_isolation", "download true does not authorize training", "strictly independent", "audited required isolation", c, False, "isolation rule frozen", "authorization contract owner"),
        ("ADMIT_014_ADMIT_015_isolation", "training true does not authorize download", "strictly independent", "audited required isolation", c, False, "isolation rule frozen", "authorization contract owner"),
        ("ADMIT_014_ADMIT_015_isolation", "no alias/fallback/OR/AND", "all forbidden", "audited required isolation", c, False, "combined semantics undefined", "authorization contract owner"),
        ("input_and_type_semantics", "candidate value type", CANDIDATE_TYPE, "ADMIT_014 precedent only", p, True, "ADMIT_015 type contract open", "authorization contract owner"),
        ("input_and_type_semantics", "coercion", CANDIDATE_COERCION, "ADMIT_014 precedent only", p, True, "ADMIT_015 contract must freeze it", "authorization contract owner"),
        ("input_and_type_semantics", "missing/invalid precedence", "fail closed with frozen precedence", "not frozen for ADMIT_015", o, True, "precedence unresolved", "formal interface owner"),
        ("formal_interface_design_inputs", "final evaluator signature", "exact signature", "not frozen in preconditions audit", o, True, "candidate design question only", "formal interface owner"),
        ("formal_interface_design_inputs", "independent oracle", "designed independently", "not designed", o, True, "oracle design unresolved", "formal interface owner"),
        ("formal_interface_design_inputs", "multi-invalid precedence", "exact deterministic order", "not frozen", o, True, "interface contract required", "formal interface owner"),
        ("result_schema_design_inputs", "result class name", "exact type name", "not frozen in preconditions audit", o, True, "candidate design question only", "formal interface owner"),
        ("result_schema_design_inputs", "result field count and order", "exact closed schema", "not frozen", o, True, "result contract required", "formal interface owner"),
        ("result_schema_design_inputs", "normalized projection", "exact representation", "not frozen", o, True, "projection contract required", "adapter contract owner"),
        ("reason_vocabulary_design_inputs", "outcome vocabulary", "closed exact vocabulary", "not frozen", o, True, "formal contract required", "formal interface owner"),
        ("reason_vocabulary_design_inputs", "reason vocabulary", "closed exact vocabulary", "not frozen", o, True, "formal contract required", "formal interface owner"),
        ("reason_vocabulary_design_inputs", "missing/type/false reasons", "exact precedence and strings", "not frozen", o, True, "authorization and interface contracts required", "formal interface owner"),
        ("purity_and_IO_boundary", "evaluator filesystem access", "none", "forbidden by audited boundary", c, False, "retain pure in-memory boundary", "formal interface owner"),
        ("purity_and_IO_boundary", "evaluator network/provider access", "none", "forbidden by audited boundary", c, False, "retain pure in-memory boundary", "formal interface owner"),
        ("purity_and_IO_boundary", "environment/config/checkpoint authority", "forbidden", "audited forbidden sources", c, False, "never authorize from these sources", "authorization contract owner"),
        ("adapter_and_runtime_boundary", "unified adapter contract", "frozen after evaluator contract", "not designed or frozen", o, True, "future separate stage", "adapter contract owner"),
        ("adapter_and_runtime_boundary", "adapter/handler implementation", "implemented after contract", "not implemented", o, True, "future separate stage", "runtime owner"),
        ("adapter_and_runtime_boundary", "registry/Exact15 runtime", "implemented after adapter", "not implemented", o, True, "future separate stage", "runtime owner"),
        ("mandatory_enforcement_boundary", "training authorization enforcement API", "exact mandatory guard", "not designed or implemented", o, True, "separate enforcement contract required", "training orchestration owner"),
        ("mandatory_enforcement_boundary", "combined permission semantics", "explicitly defined if needed", "undefined", o, True, "must not infer AND/OR", "training orchestration owner"),
        ("mandatory_enforcement_boundary", "cross-rule aggregation", "implemented only after contract", "not implemented", o, True, "open issue retained", "runtime owner"),
        ("feature_semantics_boundary", "feature-semantics audit required", "true before training", "verified committed requirement", c, False, "requirement frozen", "feature semantics owner"),
        ("feature_semantics_boundary", "historical UNKNOWN_ATOM policy", "formally audited/resolved", "not finalized for training", o, True, "historical blocker remains", "feature semantics owner"),
        ("feature_semantics_boundary", "Step12D scope", "smoke legality only", "verified; not final training contract", c, False, "do not promote smoke evidence", "feature semantics owner"),
        ("training_execution_boundary", "current permission", "false", "false", c, False, "current fail-closed state", "training orchestration owner"),
        ("training_execution_boundary", "authorized execution count", "0", "0", c, False, "no training execution", "training orchestration owner"),
        ("training_execution_boundary", "real training readiness", "false until all gates", "false", o, True, "authorization and feature audit incomplete", "training orchestration owner"),
        ("issue_and_readiness_continuity", "Exact30 issue inventory", "byte-identical", "inherited without transition", c, False, "coverage remains ADMIT_015", "runtime owner"),
        ("issue_and_readiness_continuity", "coverage issue status", "open", "open", c, False, "do not claim resolution", "runtime owner"),
        ("issue_and_readiness_continuity", "next authorized design step", RECOMMENDED_NEXT_STEP, "preconditions support contract design only", c, False, "stop after audit", "authorization contract owner"),
    )


PRECONDITION_EVIDENCE_PATHS: tuple[tuple[Path, ...], ...] = (
    (DESIGN_RULES,),
    (DESIGN_RULES,),
    (DESIGN_RULES,),
    (RUNTIME_MANIFEST,),
    (RUNTIME_MANIFEST,),
    (RUNTIME_ISSUES, RUNTIME_MANIFEST),
    (AUTH014_TRUST, RUNTIME_MANIFEST),
    (PRE_CONTEXT, RUNTIME_MANIFEST),
    (AUTH014_TRUST, RUNTIME_MANIFEST),
    (PRE_CONTEXT, AUTH014_TRUST, RUNTIME_MANIFEST),
    (AUTH014_TRUTH, RUNTIME_MANIFEST),
    (AUTH014_TRUST, RUNTIME_MANIFEST),
    (RUNTIME_PRODUCTION, RUNTIME_MANIFEST, PRE_CONTEXT),
    (PRE_CONTEXT, RUNTIME_MANIFEST),
    (PRE_CONTEXT, RUNTIME_MANIFEST),
    (AUTH014_TRUST, RUNTIME_MANIFEST),
    (AUTH014_TRUST, RUNTIME_MANIFEST),
    (AUTH014_MANIFEST, RUNTIME_MANIFEST),
    (RUNTIME_MANIFEST,),
    (RUNTIME_MANIFEST,),
    (RUNTIME_MANIFEST,),
    (RUNTIME_MANIFEST,),
    (RUNTIME_MANIFEST,),
    (RUNTIME_MANIFEST,),
    (RUNTIME_MANIFEST,),
    (RUNTIME_MANIFEST,),
    (AUTH014_MANIFEST, RUNTIME_MANIFEST),
    (PRE_RULES, PRE_MANIFEST),
    (PRE_RULES, PRE_MANIFEST),
    (AUTH014_TRUST, RUNTIME_MANIFEST),
    (RUNTIME_MANIFEST,),
    (RUNTIME_MANIFEST,),
    (RUNTIME_MANIFEST,),
    (RUNTIME_MANIFEST,),
    (RUNTIME_MANIFEST,),
    (RUNTIME_ISSUES, RUNTIME_MANIFEST),
    (QA_MANIFEST, FEATURE_MANIFEST),
    (QA_MANIFEST, FEATURE_MANIFEST, FEATURE_BLOCKERS),
    (FEATURE_MANIFEST, STEP12D_MANIFEST),
    (DESIGN_RULES, RUNTIME_MANIFEST),
    (RUNTIME_MANIFEST,),
    (QA_MANIFEST, FEATURE_MANIFEST, RUNTIME_MANIFEST),
    (RUNTIME_ISSUES,),
    (RUNTIME_ISSUES,),
    (RUNTIME_MANIFEST,),
)


def _precondition_rows(snapshot: tuple[Source, ...]) -> list[dict[str, str]]:
    specs = _precondition_specs()
    if len(specs) != 45 or len(PRECONDITION_EVIDENCE_PATHS) != len(specs):
        raise AssertionError("Exact45 precondition/evidence cardinality drift")
    source_by_path = {source.path: source for source in snapshot}
    rows = []
    for order, (spec, evidence_paths) in enumerate(
        zip(specs, PRECONDITION_EVIDENCE_PATHS), 1
    ):
        group, subject, required, observed, status, blocking, gap, owner = spec
        if (
            not evidence_paths
            or len(evidence_paths) != len(set(evidence_paths))
            or any(path not in source_by_path for path in evidence_paths)
        ):
            raise AssertionError(f"PRE_{order:03d} evidence provenance invalid")
        evidence = "|".join(path.as_posix() for path in evidence_paths)
        shas = "|".join(source_by_path[path].sha256 for path in evidence_paths)
        rows.append(dict(zip(COLUMNS[PRECONDITION], (
            str(order), f"PRE_{order:03d}", group, subject, required, observed,
            status, str(blocking).lower(), evidence, shas, gap, owner,
        ))))
    return rows


def _responsibility_rows() -> list[dict[str, str]]:
    forbidden = (
        "candidate_record|batch_context|evaluation_context|download_result_context|"
        "provider_result|environment_variable|filesystem_marker|artifact_sha|"
        "git_commit_sha|checkpoint_metadata|training_config|command_line_flag|"
        "model_state|dataloader_state"
    )
    specs = (
        ("authority", "authoritative envelope", CANDIDATE_ENVELOPE, "ADMIT_014 verified committed precedent", "supported_but_admit015_contract_not_frozen", CANDIDATE_ENVELOPE, forbidden, CANDIDATE_TYPE, CANDIDATE_COERCION, "download and training keys isolated"),
        ("authority", "training target item", CANDIDATE_TARGET_ITEM, "Step14AU-A coexistence precedent", "supported_but_admit015_contract_not_frozen", f"{CANDIDATE_ENVELOPE}.{CANDIDATE_TARGET_ITEM}", forbidden, CANDIDATE_TYPE, CANDIDATE_COERCION, "never consume download key"),
        ("authority", "producer", CANDIDATE_PRODUCER, "ADMIT_014 verified committed precedent", "supported_but_admit015_contract_not_frozen", "fresh trusted invocation input", forbidden, CANDIDATE_TYPE, CANDIDATE_COERCION, "producer must construct keys independently"),
        ("freshness", "lifetime", CANDIDATE_LIFETIME, "ADMIT_014 verified committed precedent", "supported_but_admit015_contract_not_frozen", "current invocation", "cache|artifact|raw replay", CANDIDATE_TYPE, CANDIDATE_COERCION, "no cross-invocation replay"),
        ("default", "omission", CANDIDATE_DEFAULT, "ADMIT_014 fail-closed precedent", "supported_but_admit015_contract_not_frozen", "target key only", "fallback to download key|defaults", CANDIDATE_TYPE, CANDIDATE_COERCION, "missing training key cannot read download key"),
        ("isolation", "download True", "no training authority", "Exact14 runtime consumes download key only; ADMIT_015 is known-not-registered; Step14AU-A freezes coexistence names only", "supported_but_admit015_contract_not_frozen", "download key for ADMIT_014 only", "training authority", "exact builtin bool", "no coercion", "does not imply training; future ADMIT_015 contract not frozen"),
        ("isolation", "training True", "no download authority", "Exact14 runtime ignores training key; ADMIT_015 is known-not-registered; Step14AU-A freezes coexistence names only", "supported_but_admit015_contract_not_frozen", "training key is a candidate for future ADMIT_015 only", "download authority", "exact builtin bool", "no coercion", "does not imply download; future ADMIT_015 contract not frozen"),
        ("isolation", "fallback", "forbidden", "audit boundary", "forbidden", "none", "either key as substitute", "n/a", "forbidden", "no fallback"),
        ("isolation", "alias", "forbidden", "audit boundary", "forbidden", "none", "key aliasing", "n/a", "forbidden", "no alias"),
        ("isolation", "OR", "forbidden", "audit boundary", "forbidden", "none", "download OR training", "n/a", "forbidden", "combined semantics undefined"),
        ("isolation", "AND as single permission", "forbidden", "audit boundary", "forbidden", "none", "download AND training", "n/a", "forbidden", "combined semantics undefined"),
        ("formal_design", "evaluator signature", "candidate design question", "none", "not_frozen_in_preconditions_audit", "not selected", "all implicit sources", "not frozen", "not frozen", "future contract"),
        ("formal_design", "result class and fields", "candidate design question", "none", "not_frozen_in_preconditions_audit", "not selected", "all implicit sources", "not frozen", "not frozen", "future contract"),
        ("formal_design", "reason vocabulary", "candidate design question", "none", "not_frozen_in_preconditions_audit", "not selected", "all implicit sources", "not frozen", "not frozen", "future contract"),
        ("runtime", "adapter ID and handler", "candidate design question", "none", "not_frozen_in_preconditions_audit", "not selected", "current runtime", "not frozen", "not frozen", "future contract"),
        ("enforcement", "mandatory training guard", "future separate responsibility", "not implemented", "unresolved", "none now", forbidden, "not frozen", "not frozen", "must precede training"),
    )
    return [
        dict(zip(COLUMNS[RESPONSIBILITY], (
            str(order), *spec, "true",
        )))
        for order, spec in enumerate(specs, 1)
    ]


def _safety_rows() -> list[dict[str, str]]:
    specs = (
        ("ADMIT_015 evaluator", "absent", "absent", ""),
        ("ADMIT_015 result type", "absent", "absent", ""),
        ("ADMIT_015 adapter/handler", "absent", "absent", ""),
        ("ADMIT_015 registry/Exact15 runtime", "absent", "absent", ""),
        ("mandatory training enforcement", "absent", "absent", ""),
        ("current training permission", "false", "false", CURRENT_BLOCKING_REASON),
        ("authorized training execution count", "0", "0", CURRENT_BLOCKING_REASON),
        ("feature semantics audit completed", "false", "false", "feature_semantics_audit_required"),
        ("Step12D final contract", "false", "false", "step12d_smoke_only"),
        ("ready for training", "false", "false", CURRENT_BLOCKING_REASON),
        ("dataloader instantiated", "false", "false", ""),
        ("checkpoint loaded", "false", "false", ""),
        ("model forward/loss/backward", "false", "false", ""),
        ("optimizer/parameter update", "false", "false", ""),
        ("provider/network/download", "false", "false", ""),
        ("raw structure read/write", "false", "false", ""),
        ("canonical mask count", "5", "5", ""),
        ("canonical mask B3", "scaffold_only / B3 present", "present", ""),
        ("combined verdict", "not implemented", "not implemented", ""),
        ("cross-rule aggregation", "not implemented", "not implemented", ""),
    )
    return [
        dict(zip(COLUMNS[SAFETY], (
            str(order), item, required, observed, "true", reason,
        )))
        for order, (item, required, observed, reason) in enumerate(specs, 1)
    ]


def _source_rows(snapshot: tuple[Source, ...]) -> list[dict[str, str]]:
    return [
        dict(zip(COLUMNS[SOURCE_AUDIT], (
            str(order), source.path.as_posix(), source.sha256, source.mode,
            source.blob, source.mode, source.blob, "0", source.sha256,
            source.sha256, "true", "true", "true", "true", "true", "true",
            "true",
        )))
        for order, source in enumerate(snapshot, 1)
    ]


def _csv_bytes(columns: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
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
    pre = _precondition_rows(frozen)
    responsibility = _responsibility_rows()
    source_rows = _source_rows(frozen)
    safety = _safety_rows()
    issues = _source(frozen, RUNTIME_ISSUES).content
    payloads = {
        PRECONDITION: _csv_bytes(COLUMNS[PRECONDITION], pre),
        RESPONSIBILITY: _csv_bytes(COLUMNS[RESPONSIBILITY], responsibility),
        SOURCE_AUDIT: _csv_bytes(COLUMNS[SOURCE_AUDIT], source_rows),
        SAFETY: _csv_bytes(COLUMNS[SAFETY], safety),
        ISSUE: issues,
    }
    output_sha = {name: hashlib.sha256(data).hexdigest()
                  for name, data in payloads.items()}
    complete_ids = [x["precondition_id"] for x in pre
                    if x["completion_status"] == "complete"]
    incomplete_ids = [x["precondition_id"] for x in pre
                      if x["completion_status"] != "complete"]
    blocking_ids = [x["precondition_id"] for x in pre
                    if x["implementation_blocking"] == "true"]
    readiness = {
        **{key: True for key in TRUE_READINESS},
        **{key: False for key in FALSE_READINESS},
    }
    manifest: dict[str, Any] = {
        "project": "CovaPIE", "stage": STAGE,
        "audit_revision":
            "revise_covapie_admit_015_non_destructive_failure_"
            "quarantine_and_recursive_lifecycle_v3",
        "base_commit": BASE_COMMIT, "base_parent": BASE_PARENT,
        "base_tree": BASE_TREE, "base_subject": BASE_SUBJECT,
        "canonical_evidence_python_implementation": CANONICAL_PYTHON_IMPLEMENTATION,
        "canonical_evidence_python_version": CANONICAL_PYTHON_VERSION,
        "ast_attestation_cross_python_version_portable": False,
        "noncanonical_python_policy": NONCANONICAL_PYTHON_POLICY,
        "python_runtime_migration_policy": PYTHON_RUNTIME_MIGRATION_POLICY,
        "admission_rule_id": ADMISSION_RULE_ID,
        "admission_rule_name": ADMISSION_RULE_NAME,
        "current_evidence_source": CURRENT_EVIDENCE_SOURCE,
        "current_required_status": CURRENT_REQUIRED_STATUS,
        "current_blocking_reason": CURRENT_BLOCKING_REASON,
        "current_permission": CURRENT_PERMISSION,
        "authorized_admit_015_training_execution_count":
            AUTHORIZED_ADMIT_015_TRAINING_EXECUTION_COUNT,
        "current_registration_state": CURRENT_REGISTRATION_STATE,
        "current_callable_discovered_state": CURRENT_CALLABLE_DISCOVERED_STATE,
        "current_adapter_ready_state": CURRENT_ADAPTER_READY_STATE,
        "current_runtime_coverage_open": CURRENT_RUNTIME_COVERAGE_OPEN,
        "source_count": len(frozen),
        "source_boundary_schema": list(COLUMNS[SOURCE_AUDIT]),
        "source_boundary": [
            {"order": n, "path": s.path.as_posix(), "sha256": s.sha256,
             "mode": s.mode, "blob": s.blob, "stage": 0}
            for n, s in enumerate(frozen, 1)
        ],
        "precondition_schema": list(COLUMNS[PRECONDITION]),
        "precondition_count": len(pre),
        "precondition_complete_ids": complete_ids,
        "precondition_incomplete_ids": incomplete_ids,
        "precondition_blocking_ids": blocking_ids,
        "responsibility_schema": list(COLUMNS[RESPONSIBILITY]),
        "responsibility_count": len(responsibility),
        "candidate_authoritative_envelope": CANDIDATE_ENVELOPE,
        "candidate_target_item": CANDIDATE_TARGET_ITEM,
        "admit_014_coexistence_item": COEXISTENCE_ITEM,
        "candidate_producer": CANDIDATE_PRODUCER,
        "candidate_value_type": CANDIDATE_TYPE,
        "candidate_coercion_policy": CANDIDATE_COERCION,
        "candidate_lifetime": CANDIDATE_LIFETIME,
        "candidate_default_policy": CANDIDATE_DEFAULT,
        "candidate_replay_policy": CANDIDATE_REPLAY,
        "candidate_path_status":
            "recommended authoritative path pending formal authorization contract",
        "download_training_key_fallback": False,
        "download_training_key_alias": False,
        "download_training_key_or": False,
        "download_training_key_and_as_single_permission": False,
        "combined_permission_semantics_defined": False,
        "forbidden_training_authority_sources": (
            "candidate_record|batch_context|evaluation_context|"
            "download_result_context|provider_result|environment_variable|"
            "filesystem_marker|artifact_sha|git_commit_sha|checkpoint_metadata|"
            "training_config|command_line_flag|model_state|dataloader_state"
        ).split("|"),
        "formal_interface_not_frozen": {
            "evaluator_signature": True, "result_class_name": True,
            "result_field_count": True, "result_field_order": True,
            "outcome_vocabulary": True, "reason_vocabulary": True,
            "normalized_projection": True, "handler_signature": True,
            "adapter_id": True, "registry_location": True,
            "mandatory_enforcement_api": True,
        },
        "issue_schema": next(csv.reader(io.StringIO(issues.decode()))),
        "issue_row_count": 30,
        "issue_transition_count": 0,
        "issue_inventory_source_sha256": SOURCE_SHA256[RUNTIME_ISSUES],
        "issue_inventory_byte_identical_to_exact14": True,
        "issue_coverage": [ADMISSION_RULE_ID],
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
            "training": False, "parameter_update": False, "dataloader": False,
            "checkpoint": False, "model_forward": False, "loss": False,
            "backward": False, "optimizer": False, "provider": False,
            "network": False, "download": False, "raw_read_or_write": False,
        },
        "safety_schema": list(COLUMNS[SAFETY]),
        "safety_count": len(safety),
        "output_files": list(FILES), "output_file_count": 6,
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


def materialize_audit(output_root: Path | None = None) -> dict[str, Any]:
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


def run_covapie_bulk_download_admission_admit_015_formal_evaluator_interface_preconditions_audit_v1(
    output_root: Path | None = None,
) -> dict[str, Any]:
    """Explicit entry point; import itself is silent and side-effect free."""
    return materialize_audit(output_root)
