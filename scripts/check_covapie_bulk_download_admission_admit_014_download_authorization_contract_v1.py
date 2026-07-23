#!/usr/bin/env python3
"""Independent checker for the ADMIT_014 download-authorization Exact10."""
from __future__ import annotations

import ast
import csv
import hashlib
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE = "30bbfaba4df0843d1f028e695d3dc499079a9b36"
PARENT = "3ec07b2daa7e6fc2d51df2641e85c13be2196ff3"
TREE = "72390570480b5b81680acccc2db3250ad71a942c"
SUBJECT = "add CovaPIE ADMIT_014 formal evaluator preconditions audit v1"
STAGE = (
    "covapie_bulk_download_admission_admit_014_"
    "download_authorization_contract_v1"
)
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
VALUE = "covapie_admit_014_download_authorization_value_and_trust_contract.csv"
ROUTING = (
    "covapie_admit_014_stage_authorization_routing_and_enforcement_contract.csv"
)
FAILURE = "covapie_admit_014_failure_taxonomy_and_precedence.csv"
TRUTH = "covapie_admit_014_download_authorization_truth_matrix.csv"
ISSUE = "covapie_admit_014_issue_readiness_inventory.csv"
MANIFEST = "covapie_admit_014_download_authorization_contract_manifest.json"
FILES = (VALUE, ROUTING, FAILURE, TRUTH, ISSUE, MANIFEST)

PRODUCTION = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_admit_014_"
    "download_authorization_contract_design_gate.py"
)
CHECKER = Path(
    "scripts/"
    "check_covapie_bulk_download_admission_admit_014_"
    "download_authorization_contract_v1.py"
)
TEST = Path(
    "tests/"
    "test_covapie_bulk_download_admission_admit_014_"
    "download_authorization_contract_v1.py"
)
DOC = Path(
    "docs/"
    "covapie_bulk_download_admission_admit_014_"
    "download_authorization_contract_v1_summary.md"
)
EXACT10 = (PRODUCTION, CHECKER, TEST, DOC, *(OUTPUT_ROOT / name for name in FILES))

HEADERS = {
    VALUE: (
        "contract_order", "contract_item", "contract_group",
        "expected_contract", "observed_contract", "responsibility_owner",
        "contract_passed",
    ),
    ROUTING: (
        "routing_order", "routing_item", "envelope_or_stage",
        "authority_status", "access_or_enforcement_contract",
        "expected_behavior", "observed_design", "routing_passed",
    ),
    FAILURE: (
        "precedence_order", "failure_or_pass_id", "trigger", "outcome",
        "passed", "blocks_candidate", "reason", "later_checks_executed",
        "taxonomy_passed",
    ),
    TRUTH: (
        "case_order", "case_id", "case_group", "stage_context_representation",
        "forbidden_envelope_representation", "expected_outcome",
        "observed_outcome", "expected_reason", "observed_reason",
        "target_key_access_count", "mapping_iteration_count",
        "mapping_len_count", "mapping_get_count", "mapping_contains_count",
        "forbidden_envelope_access_count", "case_passed",
    ),
}
OUTPUT_SHA256 = {
    VALUE: "b22f02efdd53dce995730a05cc5c12ffa659c2d98b345afc663b118cc104752d",
    ROUTING: "68bc56b214f212ffec359049146e371ac7ce48bed34bfd6bb80313a2fd7046a6",
    FAILURE: "1970da57fdec24e9c5b6e518e1dfa7c2103d3bef6da065b24e3d61a296cdeffc",
    TRUTH: "e4f39f5178b91906639670f5c1ddb1c02b40c802de9ce386aee2a6b6d49f8482",
    ISSUE: "10e3475cb329d517c27fae26636294d0aa69a609a3c59a8b7f0119b0b123edbe",
    MANIFEST: "9c54c9d6cb11776b04938d9be048699041bfc4020dca4c00425faadaaaa5d4d2",
}
PRODUCTION_SHA256 = "b2616c01234c899695c08280daacfa21cb137b847a01f5bf6e52e807b0770434"
ADMIT014_CONTEXT_KEY = "current_stage_download_authorized"
ADMIT015_CONTEXT_KEY = "current_stage_training_authorized"

PRE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_014_"
    "rule_logic_interface_preconditions_audit_v1"
)
AUA_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_"
    "implementation_precondition_gate_v1"
)
AT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1"
)
RUNTIME_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1"
)
SOURCES = (
    (
        Path("src/covalent_ext/covapie_bulk_download_admission_admit_014_formal_evaluator_interface_preconditions_audit.py"),
        "d134e43f01860bd193eacab6a38171bb508b1e1e48fcf1559f8105d74d0e2632",
    ),
    (PRE_ROOT / "covapie_admit_014_formal_evaluator_precondition_matrix.csv", "6b52a4e96dd960e7df53b7160f5cd00d63fbeb62ee5bc5ec9882623efd268c30"),
    (PRE_ROOT / "covapie_admit_014_authorization_evidence_and_routing_responsibility_matrix.csv", "c1804d6ff7bd0a6eecb68877defa41316dd8afc999fb1152eba323f185b03834"),
    (PRE_ROOT / "covapie_admit_014_issue_readiness_inventory.csv", "6af875d474f0c0e1320f2584eec080acf6cf4d1097c25f004380430e4c5fab06"),
    (PRE_ROOT / "covapie_admit_014_formal_evaluator_preconditions_manifest.json", "b9582357f392a6aa1af68012a1469c886b2de4b5af8196cddad56f94625e4b61"),
    (AUA_ROOT / "covapie_bulk_download_admission_rule_executability_matrix.csv", "a7782e48cac282b047a392ee20b5b26a72fa1b2208a3889edf8b1c8af923921b"),
    (AUA_ROOT / "covapie_bulk_download_admission_evaluation_context_contract.csv", "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0"),
    (AT_ROOT / "covapie_bulk_download_admission_rule_registry.csv", "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc"),
    (
        Path("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013.py"),
        "79f95b6e178044ff5b4f5abbd6445b6cd848e81ba1a8a16cacdf831b05b9b892",
    ),
    (RUNTIME_ROOT / "covapie_admit_001_to_013_runtime_manifest.json", "2940e6cc02a92b4919cdece3b1fa7c2f5e27d844f2962bb18757197266c23f79"),
    (RUNTIME_ROOT / "covapie_admit_001_to_013_runtime_issue_readiness_inventory.csv", "477b4192579d3f64dac5bd0cc61c1a378b2f28c3355251e344b79999801a5d69"),
)

REASONS = (
    "",
    "STAGE_AUTHORIZATION_CONTEXT_REQUIRED",
    "STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID",
    "CURRENT_STAGE_DOWNLOAD_AUTHORIZED_MISSING",
    "STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED",
    "CURRENT_STAGE_DOWNLOAD_AUTHORIZED_TYPE_INVALID",
    "BULK_DOWNLOAD_NOT_AUTHORIZED",
)
TRANSITIONS = {
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
OPEN_ISSUES = (
    "ADMIT_014_STANDALONE_SIGNATURE_UNRESOLVED",
    "ADMIT_014_RESULT_CONTRACT_UNRESOLVED",
)
OPEN_PRECONDITIONS = ("PRE_039", "PRE_040", "PRE_041", "PRE_048", "PRE_049")
TRUE_KEYS = (
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
FALSE_KEYS = (
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
MANIFEST_KEYS = (
    "project", "stage", "manifest_schema_version", "base_commit", "base_parent",
    "base_tree", "base_subject", "canonical_evidence_python_implementation",
    "canonical_evidence_python_version",
    "ast_attestation_cross_python_version_portable",
    "noncanonical_python_policy", "python_runtime_migration_policy",
    "admission_rule_identity", "authorization_contract", "trust_boundary",
    "outcome_vocabulary", "reason_vocabulary", "failure_precedence",
    "result_invariants",
    "mandatory_pre_download_authorization_enforcement_contract",
    "current_permission", "synthetic_true_design_case_grants_current_permission",
    "ready_for_bulk_download_now", "truth_matrix_schema",
    "truth_matrix_row_count", "truth_matrix_group_counts",
    "truth_matrix_all_cases_passed", "forbidden_envelope_access_count",
    "precondition_transition", "issue_transition", "source_count",
    "source_boundary", "source_validation_before_output_read", "readiness",
    "safety", "output_file_count", "output_files", "output_sha256",
    "output_sha256_excludes_manifest_self_hash", "renameat2_policy",
    "step12d_status", "feature_semantics_note", "recommended_next_step",
    "all_checks_passed", *TRUE_KEYS,
    *(key for key in FALSE_KEYS if key != "ready_for_bulk_download_now"),
)


def _guard() -> None:
    if sys.implementation.name != "cpython" or tuple(sys.version_info[:3]) != (3, 10, 4):
        raise RuntimeError("independent checker requires canonical CPython 3.10.4")


def _git(
    args: list[str], repo_root: Path = REPO_ROOT
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


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


def _safe(path: Path) -> bool:
    return (
        not path.is_absolute()
        and bool(path.parts)
        and ".." not in path.parts
        and path.parts[:2] != ("data", "raw")
        and path.parts[0] != "checkpoints"
        and OUTPUT_ROOT.as_posix() not in path.as_posix()
    )


def _pinned_relative(path: Path, repo_root: Path = REPO_ROOT) -> bytes:
    if not _safe(path):
        raise ValueError(f"unsafe source path: {path}")
    directory_flags = (
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    )
    leaf_flags = (
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    )
    root_lexical = os.lstat(repo_root)
    if stat.S_ISLNK(root_lexical.st_mode) or not stat.S_ISDIR(root_lexical.st_mode):
        raise ValueError("unsafe repository root")
    root_identity = _identity(root_lexical)
    descriptors: list[tuple[int, Identity, int | None, str | None]] = []
    root_fd = os.open(repo_root, directory_flags)
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
                raise ValueError("unsafe source parent")
            child_fd = os.open(part, directory_flags, dir_fd=parent_fd)
            if _identity(os.fstat(child_fd)) != expected:
                os.close(child_fd)
                raise ValueError("source parent stat/open race")
            descriptors.append((child_fd, expected, parent_fd, part))
            parent_fd = child_fd
        before = os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
        expected_leaf = _identity(before)
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
            raise ValueError("unsafe source leaf")
        leaf_fd = os.open(path.name, leaf_flags, dir_fd=parent_fd)
        try:
            if _identity(os.fstat(leaf_fd)) != expected_leaf:
                raise ValueError("source stat/open race")
            chunks = []
            while True:
                chunk = os.read(leaf_fd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            if _identity(os.fstat(leaf_fd)) != expected_leaf:
                raise ValueError("source FD identity drift")
        finally:
            os.close(leaf_fd)
        if (
            _identity(
                os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
            )
            != expected_leaf
        ):
            raise ValueError("source lexical replacement")
        for descriptor, expected, lexical_parent, lexical_name in descriptors:
            if _identity(os.fstat(descriptor)) != expected:
                raise ValueError("source parent FD identity drift")
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
                    raise ValueError("source parent lexical replacement")
        if _identity(os.lstat(repo_root)) != root_identity:
            raise ValueError("repository root identity drift")
        return b"".join(chunks)
    finally:
        for descriptor, _, _, _ in reversed(descriptors):
            os.close(descriptor)


def _source_snapshot() -> dict[Path, bytes]:
    identity = _git(["show", "-s", "--format=%H%n%P%n%T%n%s", BASE])
    ancestor = _git(["merge-base", "--is-ancestor", BASE, "HEAD"])
    if identity.returncode or ancestor.returncode:
        raise ValueError("base identity/ancestry failure")
    if identity.stdout.splitlines() != [BASE, PARENT, TREE, SUBJECT]:
        raise ValueError("base identity mismatch")
    records = {}
    for path, digest in SOURCES:
        index = _git(["ls-files", "--stage", "--", path.as_posix()])
        tree = _git(["ls-tree", BASE, "--", path.as_posix()])
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
            or index_fields[0] != tree_fields[0]
            or index_fields[1] != tree_fields[2]
            or tree_fields[1] != "blob"
        ):
            raise ValueError(f"source index/base mode/blob drift: {path}")
        current = _pinned_relative(path)
        base = subprocess.run(
            ["git", "show", f"{BASE}:{path.as_posix()}"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
        if (
            hashlib.sha256(current).hexdigest() != digest
            or base.returncode
            or base.stdout != current
        ):
            raise ValueError(f"source SHA/base mismatch: {path}")
        records[path] = current
    return records


def _pinned_outputs(root: Path) -> dict[str, bytes]:
    directory_flags = (
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    )
    leaf_flags = (
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    )
    parent = root.parent
    parent_identity = _identity(os.lstat(parent))
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
        root_fd = os.open(root.name, directory_flags, dir_fd=parent_fd)
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("output root stat/open race")
        if set(os.listdir(root_fd)) != set(FILES):
            raise ValueError("missing or extra Exact6 output")
        for name in FILES:
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
                raise ValueError("output stat/open race")
            chunks = []
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            leaves.append((name, descriptor, expected, b"".join(chunks)))
        if set(os.listdir(root_fd)) != set(FILES):
            raise ValueError("output inventory drift after traversal")
        outputs = {}
        for name, descriptor, expected, data in leaves:
            if (
                _identity(os.fstat(descriptor)) != expected
                or _identity(
                    os.stat(name, dir_fd=root_fd, follow_symlinks=False)
                )
                != expected
            ):
                raise ValueError("output leaf identity drift after traversal")
            outputs[name] = data
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
        return outputs
    finally:
        for _, descriptor, _, _ in leaves:
            os.close(descriptor)
        if root_fd >= 0:
            os.close(root_fd)
        os.close(parent_fd)


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _parse_manifest_exact(data: bytes) -> dict[str, Any]:
    manifest = json.loads(data, object_pairs_hook=_pairs_no_duplicates)
    if tuple(manifest) != MANIFEST_KEYS:
        raise ValueError("manifest missing/extra/reordered keys")
    return manifest


def _rows(data: bytes) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(data.decode(), newline=""))
    if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("CSV duplicate/empty header")
    return list(reader)


class Probe(Mapping[str, object]):
    def __init__(
        self,
        values: dict[str, object] | None = None,
        *,
        error: BaseException | None = None,
    ) -> None:
        self.values = {} if values is None else values
        self.error = error
        self.item_count = 0
        self.item_keys: list[str] = []
        self.iter_count = 0
        self.len_count = 0
        self.get_count = 0
        self.contains_count = 0

    def __getitem__(self, key: str) -> object:
        self.item_count += 1
        self.item_keys.append(key)
        if self.error is not None:
            raise self.error
        return self.values[key]

    def __iter__(self) -> Iterator[str]:
        self.iter_count += 1
        raise AssertionError("mapping iteration forbidden")

    def __len__(self) -> int:
        self.len_count += 1
        raise AssertionError("mapping len forbidden")

    def get(self, key: str, default: object = None) -> object:
        self.get_count += 1
        raise AssertionError("mapping get forbidden")

    def __contains__(self, key: object) -> bool:
        self.contains_count += 1
        raise AssertionError("mapping contains forbidden")

    @property
    def access_count(self) -> int:
        return (
            self.item_count + self.iter_count + self.len_count
            + self.get_count + self.contains_count
        )


def _load_classifier():
    path = REPO_ROOT / PRODUCTION
    content = _pinned_relative(PRODUCTION)
    if hashlib.sha256(content).hexdigest() != PRODUCTION_SHA256:
        raise ValueError("candidate production SHA mismatch")
    spec = importlib.util.spec_from_file_location("admit014_design_isolated", path)
    if spec is None or spec.loader is None:
        raise ValueError("isolated production import unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.classify_admit_014_download_authorization_contract_design


def _validate_classifier() -> None:
    classify = _load_classifier()
    definitions = (
        (None, "blocked", REASONS[1]),
        (object(), "blocked", REASONS[2]),
        (Probe(), "blocked", REASONS[3]),
        (Probe(error=KeyError("x")), "blocked", REASONS[3]),
        (Probe(error=RuntimeError("x")), "blocked", REASONS[4]),
        (Probe({"current_stage_download_authorized": 0}), "blocked", REASONS[5]),
        (Probe({"current_stage_download_authorized": 1}), "blocked", REASONS[5]),
        (Probe({"current_stage_download_authorized": "true"}), "blocked", REASONS[5]),
        (Probe({"current_stage_download_authorized": False}), "blocked", REASONS[6]),
        (Probe({"other": object(), "current_stage_download_authorized": True}), "passed", ""),
    )
    for context, outcome, reason in definitions:
        forbidden = {name: Probe({"current_stage_download_authorized": True}) for name in (
            "candidate_record", "batch_context", "evaluation_context",
            "download_result_context",
        )}
        result = classify(context, **forbidden)
        if (
            result.outcome != outcome
            or result.reason != reason
            or result.passed is not (outcome == "passed")
            or result.blocks_candidate is not (outcome == "blocked")
            or result.evaluator_io_used is not False
            or any(probe.access_count for probe in forbidden.values())
        ):
            raise ValueError("independent classifier semantic mismatch")
        if isinstance(context, Probe):
            if (
                context.item_count != 1
                or context.iter_count
                or context.len_count
                or context.get_count
                or context.contains_count
            ):
                raise ValueError("target-only lookup contract violated")
    coexistence = Probe(
        {
            ADMIT015_CONTEXT_KEY: False,
            ADMIT014_CONTEXT_KEY: True,
        }
    )
    coexistence_result = classify(coexistence)
    if (
        coexistence_result.outcome != "passed"
        or coexistence.item_keys != [ADMIT014_CONTEXT_KEY]
        or coexistence.iter_count
        or coexistence.len_count
        or coexistence.get_count
        or coexistence.contains_count
    ):
        raise ValueError("ADMIT_014/015 target-only coexistence drift")


def _validate_admit015_context_lineage(
    sources: dict[Path, bytes],
    truth: list[dict[str, str]],
    outputs: dict[str, bytes],
) -> None:
    context_source = (
        AUA_ROOT / "covapie_bulk_download_admission_evaluation_context_contract.csv"
    )
    contexts = _rows(sources[context_source])
    admit014 = [
        row for row in contexts if row["required_by_rules"] == "ADMIT_014"
    ]
    admit015 = [
        row for row in contexts if row["required_by_rules"] == "ADMIT_015"
    ]
    if len(admit014) != 1 or admit014[0]["context_item"] != ADMIT014_CONTEXT_KEY:
        raise ValueError("canonical ADMIT_014 context lineage drift")
    if len(admit015) != 1 or admit015[0] != {
        "context_item": ADMIT015_CONTEXT_KEY,
        "context_scope": "stage",
        "required_by_rules": "ADMIT_015",
        "provided_by_future_caller": "true",
        "filesystem_access_inside_evaluator": "false",
        "network_access_inside_evaluator": "false",
        "deterministic_now": "true",
        "deterministic_after_contract_freeze": "true",
        "exact_contract_defined": "true",
        "implementation_ready": "true",
        "blocking_reasons": "",
    }:
        raise ValueError("canonical ADMIT_015 context lineage drift")
    truth_by_id = {row["case_id"]: row for row in truth}
    obsolete_key = "current_stage_" + "admit_015_authorized"
    for case_id in ("ADMIT015_PLUS_TRUE", "ADMIT015_PLUS_FALSE"):
        representation = truth_by_id[case_id]["stage_context_representation"]
        if ADMIT015_CONTEXT_KEY not in representation or obsolete_key in representation:
            raise ValueError("ADMIT_015 truth-matrix coexistence key drift")
    candidate_bytes = {
        "production": _pinned_relative(PRODUCTION),
        "tests": _pinned_relative(TEST),
        "truth matrix": outputs[TRUTH],
        "summary": _pinned_relative(DOC),
        "manifest": outputs[MANIFEST],
    }
    if any(obsolete_key.encode() in data for data in candidate_bytes.values()):
        raise ValueError("obsolete ADMIT_015 context key remains")


def _lifecycle(
    repo_root: Path = REPO_ROOT,
    base: str = BASE,
    exact10: tuple[Path, ...] = EXACT10,
) -> str:
    if _git(["merge-base", "--is-ancestor", base, "HEAD"], repo_root).returncode:
        raise ValueError("base nonancestor")
    if len(exact10) != 10 or len(set(exact10)) != 10:
        raise ValueError("Exact10 path contract drift")
    forbidden_suffixes = {
        ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
        ".npz", ".tmp", ".part",
    }
    states = []
    for path in exact10:
        target = repo_root / path
        if not target.exists() or target.is_symlink() or target.stat().st_size > 100 * 1024 * 1024:
            raise ValueError(f"unsafe candidate: {path}")
        if path.suffix in forbidden_suffixes:
            raise ValueError("forbidden candidate suffix")
        ignored = _git(["check-ignore", "--no-index", "-q", "--", path.as_posix()], repo_root)
        if ignored.returncode == 0:
            raise ValueError(f"ignored candidate: {path}")
        if ignored.returncode != 1:
            raise ValueError("candidate ignore check failed")
        tracked = _git(["ls-files", "--error-unmatch", "--", path.as_posix()], repo_root)
        untracked = _git(["ls-files", "--others", "--exclude-standard", "--", path.as_posix()], repo_root)
        staged = _git(["diff", "--cached", "--name-only", "--", path.as_posix()], repo_root)
        working = _git(["diff", "--name-only", "--", path.as_posix()], repo_root)
        if staged.stdout.strip():
            raise ValueError(f"stage path is staged: {path}")
        if tracked.returncode == 0:
            if untracked.stdout.strip() or working.stdout.strip():
                raise ValueError(f"dirty post-commit candidate: {path}")
            states.append("post_commit")
        else:
            if untracked.stdout.splitlines() != [path.as_posix()] or working.stdout.strip():
                raise ValueError(f"invalid pre-commit candidate: {path}")
            states.append("pre_commit")
    if len(set(states)) != 1:
        raise ValueError("mixed lifecycle")
    suffix = "admit_014_download_authorization_contract"
    expected_top = set(exact10[:4])
    observed_top = {
        path.relative_to(repo_root)
        for directory in ("src/covalent_ext", "scripts", "tests", "docs")
        for path in (repo_root / directory).glob(f"*{suffix}*")
        if path.is_file() or path.is_symlink()
    }
    if observed_top != expected_top:
        raise ValueError("extra or missing same-stage top-level candidate")
    roots = sorted((repo_root / OUTPUT_ROOT.parent).glob(f"{OUTPUT_ROOT.name}*"))
    if roots != [repo_root / OUTPUT_ROOT]:
        raise ValueError("extra or missing same-stage derived root")
    if {path.name for path in (repo_root / OUTPUT_ROOT).iterdir()} != set(FILES):
        raise ValueError("missing or seventh Exact6 output")
    return states[0]


def _validate_ast() -> None:
    content = _pinned_relative(PRODUCTION)
    tree = ast.parse(content)
    forbidden = {
        "evaluate_admit_014", "Admit014EvaluationResult",
        "_evaluate_registered_admit_014", "EVALUATOR_REGISTRY",
        "evaluate_admission_rule",
    }
    definitions = {
        node.name for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    assignments = {
        target.id for node in ast.walk(tree) if isinstance(node, ast.Assign)
        for target in node.targets if isinstance(target, ast.Name)
    }
    if forbidden & (definitions | assignments):
        raise ValueError("production contains forbidden evaluator/adapter/runtime")
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    if imports & {"requests", "urllib", "torch", "numpy", "rdkit", "Bio", "gemmi"}:
        raise ValueError("production imports forbidden dependency")
    if b"os.replace" in content:
        raise ValueError("forbidden replacement fallback")


def validate() -> str:
    _guard()
    sources = _source_snapshot()  # committed authority before candidate/output
    lifecycle = _lifecycle()
    outputs = _pinned_outputs(REPO_ROOT / OUTPUT_ROOT)
    if set(outputs) != set(FILES):
        raise ValueError("Exact6 key mismatch")
    for name, digest in OUTPUT_SHA256.items():
        if hashlib.sha256(outputs[name]).hexdigest() != digest:
            raise ValueError(f"frozen output SHA mismatch: {name}")
    manifest = _parse_manifest_exact(outputs[MANIFEST])
    values = _rows(outputs[VALUE])
    routing = _rows(outputs[ROUTING])
    failure = _rows(outputs[FAILURE])
    truth = _rows(outputs[TRUTH])
    issues = _rows(outputs[ISSUE])
    for name, rows in (
        (VALUE, values), (ROUTING, routing), (FAILURE, failure), (TRUTH, truth)
    ):
        if tuple(rows[0]) != HEADERS[name]:
            raise ValueError(f"{name} schema mismatch")
    if not (
        len(values) == 20
        and len(routing) == 25
        and len(failure) == 7
        and len(truth) == 40
        and len(issues) == 30
        and all(row["contract_passed"] == "true" for row in values)
        and all(row["routing_passed"] == "true" for row in routing)
        and all(row["taxonomy_passed"] == "true" for row in failure)
        and all(row["case_passed"] == "true" for row in truth)
    ):
        raise ValueError("Exact6 row count or pass drift")
    if [row["reason"] for row in failure] != list(REASONS[1:]) + [""]:
        raise ValueError("closed reason/precedence drift")
    if [row["outcome"] for row in failure] != ["blocked"] * 6 + ["passed"]:
        raise ValueError("outcome taxonomy drift")
    if any(
        int(row[column])
        for row in truth
        for column in (
            "mapping_iteration_count", "mapping_len_count", "mapping_get_count",
            "mapping_contains_count", "forbidden_envelope_access_count",
        )
    ):
        raise ValueError("forbidden mapping/envelope access observed")
    _validate_admit015_context_lineage(sources, truth, outputs)
    inherited = _rows(
        sources[
            PRE_ROOT / "covapie_admit_014_issue_readiness_inventory.csv"
        ]
    )
    if [row["issue_id"] for row in issues] != [row["issue_id"] for row in inherited]:
        raise ValueError("Exact30 identity/order drift")
    if issues[:23] != inherited[:23]:
        raise ValueError("inherited Exact23 byte-semantic continuity drift")
    by_id = {row["issue_id"]: row for row in issues}
    for issue_id, evidence in TRANSITIONS.items():
        row = by_id[issue_id]
        if (
            row["successor_effective_status"] != "resolved"
            or row["successor_transition_action"]
            != "resolved_by_successor_contract_design"
            or row["successor_transition_evidence"] != evidence
        ):
            raise ValueError("Exact5 issue transition drift")
    if any(by_id[issue_id]["successor_effective_status"] != "open" for issue_id in OPEN_ISSUES):
        raise ValueError("Exact2 remaining-open drift")
    coverage = by_id["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]
    if coverage["affected_rules"] != "ADMIT_014|ADMIT_015":
        raise ValueError("coverage drift")
    expected_readiness = {
        **{key: True for key in TRUE_KEYS},
        **{key: False for key in FALSE_KEYS},
    }
    if (
        manifest["readiness"] != expected_readiness
        or any(manifest[key] is not True for key in TRUE_KEYS)
        or any(manifest[key] is not False for key in FALSE_KEYS)
    ):
        raise ValueError("readiness drift")
    identity = manifest["admission_rule_identity"]
    if identity != {
        "admission_rule_id": "ADMIT_014",
        "admission_rule_name": "current_gate_grants_no_download_permission",
        "evidence_source": "current_design_gate",
        "required_status": "bulk_download_not_authorized_now",
        "failure_severity": "blocking",
        "blocking_reason": "bulk_download_not_authorized",
        "evaluation_phase": "current_step",
        "evaluator_model": "future_explicit_authorization_context",
    }:
        raise ValueError("ADMIT_014 identity drift")
    authorization = manifest["authorization_contract"]
    if not (
        authorization["authoritative_envelope"] == "stage_authorization_context"
        and authorization["authoritative_key"]
        == "current_stage_download_authorized"
        and authorization["exact_builtin_type"] == "bool"
        and authorization["closed_value_vocabulary"] == [False, True]
        and authorization["normalization_or_coercion_allowed"] is False
    ):
        raise ValueError("authorization contract drift")
    enforcement = manifest[
        "mandatory_pre_download_authorization_enforcement_contract"
    ]
    if not (
        enforcement["stage_global_guard"] is True
        and enforcement["evaluate_once_each_real_download_stage_invocation"] is True
        and enforcement["only_pass_may_continue"] is True
        and enforcement["combined_verdict_required"] is False
        and enforcement["combined_verdict_may_override_blocked"] is False
        and enforcement["implemented"] is False
        and all(
            enforcement[key] == 0
            for key in (
                "blocked_provider_call_count", "blocked_network_call_count",
                "blocked_download_count", "blocked_raw_write_count",
            )
        )
    ):
        raise ValueError("mandatory enforcement contract drift")
    pre = manifest["precondition_transition"]
    if not (
        pre["complete_count"] == 46
        and pre["incomplete_count"] == 5
        and pre["implementation_blocking_count"] == 5
        and pre["remaining_open_precondition_ids"] == list(OPEN_PRECONDITIONS)
    ):
        raise ValueError("precondition transition drift")
    if not (
        manifest["current_permission"] is False
        and manifest["synthetic_true_design_case_grants_current_permission"] is False
        and manifest["ready_for_bulk_download_now"] is False
        and manifest["forbidden_envelope_access_count"] == 0
        and manifest["source_count"] == len(SOURCES)
        and manifest["output_files"] == list(FILES)
        and manifest["output_sha256"]
        == {name: OUTPUT_SHA256[name] for name in FILES[:-1]}
        and manifest["recommended_next_step"]
        == "design_covapie_admit_014_formal_evaluator_interface_contract_v1"
        and not any(manifest["safety"].values())
    ):
        raise ValueError("manifest boundary drift")
    _validate_ast()
    _validate_classifier()
    return lifecycle


def main() -> int:
    lifecycle = validate()
    print(f"stage={STAGE}")
    print(f"base_commit={BASE}")
    print("canonical_evidence_python=cpython-3.10.4")
    print(f"source_count={len(SOURCES)}")
    print("truth_matrix_rows=40")
    print("precondition_complete=46")
    print("precondition_open=5")
    print("issue_rows=30")
    print("issue_transitions=5")
    print("remaining_open_admit_014_issues=2")
    print("current_permission=false")
    print("ready_for_bulk_download_now=false")
    print("mandatory_enforcement_implemented=false")
    print("recommended_next_step=design_covapie_admit_014_formal_evaluator_interface_contract_v1")
    print(f"lifecycle={lifecycle}")
    print(f"{STAGE}_passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
