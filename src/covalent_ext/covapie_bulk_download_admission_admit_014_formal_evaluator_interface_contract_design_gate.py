"""Design-only ADMIT_014 formal evaluator interface contract gate.

This module freezes the future one-keyword public signature and Exact9 result
contract.  It intentionally does not define ``evaluate_admit_014``, the formal
``Admit014EvaluationResult`` type, an adapter, registry entry, dispatcher
route, provider/download operation, or training operation.
"""
from __future__ import annotations

import csv
import ctypes
import errno
import hashlib
import inspect
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any


PROJECT = "CovaPIE"
STAGE = (
    "covapie_bulk_download_admission_admit_014_"
    "formal_evaluator_interface_contract_v1"
)
BASE_COMMIT = "d56140d8558208ee34eb5a43773010a2dc69169b"
BASE_PARENT = "30bbfaba4df0843d1f028e695d3dc499079a9b36"
BASE_TREE = "3dbdc1a9723d30e05a1f856cc02ac60af5a25120"
BASE_SUBJECT = "add CovaPIE ADMIT_014 download authorization contract v1"
RECOMMENDED_NEXT_STEP = (
    "implement_covapie_admit_014_standalone_evaluator_interface_v1"
)
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

CANONICAL_PYTHON_IMPLEMENTATION = "cpython"
CANONICAL_PYTHON_VERSION = "3.10.4"
NONCANONICAL_PYTHON_POLICY = (
    "evaluator_semantic_smoke_only; artifact_build_checker_and_frozen_ast_forbidden"
)
PYTHON_RUNTIME_MIGRATION_POLICY = "explicit_contract_refresh_required"

ADMISSION_RULE_ID = "ADMIT_014"
AUTHORIZATION_CONTEXT_ITEM = "current_stage_download_authorized"
ADMIT_015_CONTEXT_ITEM = "current_stage_training_authorized"
PARAMETERS = ("stage_authorization_context",)
RESULT_FIELDS = (
    "admission_rule_id",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "canonical_stage_authorization_record",
    "validated_stage_authorization_fields",
    "consumed_stage_authorization_fields",
    "evaluator_io_used",
)
RESULT_FIELD_TYPES = (
    "str",
    "str",
    "bool",
    "bool",
    "str",
    "tuple",
    "tuple",
    "tuple",
    "bool",
)
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
BLOCKER_REASONS = frozenset(REASON_VOCABULARY[1:])


class _DesignMissingValue:
    __slots__ = ()


_DESIGN_MISSING = _DesignMissingValue()


class _TupleSubclass(tuple):
    pass


class _PairTupleSubclass(tuple):
    pass


class _StringSubclass(str):
    pass


def _signature_design() -> inspect.Signature:
    return inspect.Signature(
        (
            inspect.Parameter(
                "stage_authorization_context",
                inspect.Parameter.KEYWORD_ONLY,
                default=_DESIGN_MISSING,
                annotation=object,
            ),
        ),
        return_annotation="Admit014EvaluationResult",
    )


FORMAL_SIGNATURE_DESIGN = _signature_design()
FUTURE_PUBLIC_SIGNATURE = (
    "evaluate_admit_014(*, stage_authorization_context: object = _MISSING) "
    "-> Admit014EvaluationResult"
)


@dataclass(frozen=True)
class Admit014FormalEvaluatorInterfaceContractDesign:
    signature: object = FORMAL_SIGNATURE_DESIGN
    parameter_order: tuple[str, ...] = PARAMETERS
    result_field_order: tuple[str, ...] = RESULT_FIELDS

    def __post_init__(self) -> None:
        if type(self) is not Admit014FormalEvaluatorInterfaceContractDesign:
            raise TypeError("interface ContractDesign subclasses are forbidden")
        if self.signature is not FORMAL_SIGNATURE_DESIGN:
            raise ValueError("formal signature Design identity changed")
        if type(self.parameter_order) is not tuple or self.parameter_order != PARAMETERS:
            raise ValueError("formal parameter order changed")
        if (
            type(self.result_field_order) is not tuple
            or self.result_field_order != RESULT_FIELDS
        ):
            raise ValueError("formal result field order changed")


def _canonical_record_valid(value: object) -> bool:
    if type(value) is not tuple or len(value) > 1:
        return False
    if not value:
        return True
    pair = value[0]
    return (
        type(pair) is tuple
        and len(pair) == 2
        and type(pair[0]) is str
        and pair[0] == AUTHORIZATION_CONTEXT_ITEM
        and type(pair[1]) is bool
    )


def _field_tuple_valid(value: object) -> bool:
    return (
        type(value) is tuple
        and value in ((), (AUTHORIZATION_CONTEXT_ITEM,))
        and all(type(item) is str for item in value)
    )


@dataclass(frozen=True)
class Admit014EvaluationResultContractDesign:
    admission_rule_id: object
    outcome: object
    passed: object
    blocks_candidate: object
    reason: object
    canonical_stage_authorization_record: object
    validated_stage_authorization_fields: object
    consumed_stage_authorization_fields: object
    evaluator_io_used: object

    def __post_init__(self) -> None:
        if type(self) is not Admit014EvaluationResultContractDesign:
            raise TypeError("result ContractDesign subclasses are forbidden")
        if tuple(field.name for field in fields(type(self))) != RESULT_FIELDS:
            raise TypeError("result ContractDesign storage order changed")
        if any(
            type(value) is not str
            for value in (self.admission_rule_id, self.outcome, self.reason)
        ):
            raise TypeError("result string fields require exact built-in str")
        if any(
            type(value) is not bool
            for value in (
                self.passed,
                self.blocks_candidate,
                self.evaluator_io_used,
            )
        ):
            raise TypeError("result boolean fields require exact built-in bool")
        if any(
            type(value) is not tuple
            for value in (
                self.canonical_stage_authorization_record,
                self.validated_stage_authorization_fields,
                self.consumed_stage_authorization_fields,
            )
        ):
            raise TypeError("result tuple fields require exact built-in tuple")
        if self.admission_rule_id != ADMISSION_RULE_ID:
            raise ValueError("result admission rule identity invalid")
        if self.outcome not in OUTCOME_VOCABULARY:
            raise ValueError("result outcome outside closed vocabulary")
        if self.reason not in REASON_VOCABULARY:
            raise ValueError("result reason outside closed vocabulary")
        if self.passed is not (self.outcome == "passed"):
            raise ValueError("passed flag contradicts outcome")
        if self.blocks_candidate is not (self.outcome == "blocked"):
            raise ValueError("blocks_candidate flag contradicts outcome")
        if (self.reason == "") is not (self.outcome == "passed"):
            raise ValueError("reason empty iff outcome passed invariant failed")
        if (self.outcome == "blocked") is not (self.reason in BLOCKER_REASONS):
            raise ValueError("blocked outcome/reason invariant failed")
        if self.evaluator_io_used is not False:
            raise ValueError("evaluator_io_used must be exact false")
        if not _canonical_record_valid(
            self.canonical_stage_authorization_record
        ):
            raise ValueError("canonical stage authorization record malformed")
        if not _field_tuple_valid(self.validated_stage_authorization_fields):
            raise ValueError("validated stage authorization fields malformed")
        if not _field_tuple_valid(self.consumed_stage_authorization_fields):
            raise ValueError("consumed stage authorization fields malformed")

        empty = ()
        field = (AUTHORIZATION_CONTEXT_ITEM,)
        canonical = self.canonical_stage_authorization_record
        validated = self.validated_stage_authorization_fields
        consumed = self.consumed_stage_authorization_fields
        if self.reason in REASON_VOCABULARY[1:3]:
            expected = (empty, empty, empty)
        elif self.reason in REASON_VOCABULARY[3:6]:
            expected = (empty, empty, field)
        elif self.reason == "BULK_DOWNLOAD_NOT_AUTHORIZED":
            expected = (
                ((AUTHORIZATION_CONTEXT_ITEM, False),),
                field,
                field,
            )
        else:
            expected = (
                ((AUTHORIZATION_CONTEXT_ITEM, True),),
                field,
                field,
            )
        if (canonical, validated, consumed) != expected:
            raise ValueError("result state contradicts frozen reason semantics")


def validate_admit_014_evaluation_result_contract_design(value: object) -> bool:
    if type(value) is not Admit014EvaluationResultContractDesign:
        raise TypeError("exact Admit014 EvaluationResult ContractDesign required")
    reconstructed = Admit014EvaluationResultContractDesign(
        *(getattr(value, name) for name in RESULT_FIELDS)
    )
    if reconstructed != value:
        raise ValueError("result ContractDesign reconstruction mismatch")
    return True


def _make_result(
    outcome: str,
    reason: str,
    canonical: tuple[tuple[str, bool], ...],
    validated: tuple[str, ...],
    consumed: tuple[str, ...],
) -> Admit014EvaluationResultContractDesign:
    return Admit014EvaluationResultContractDesign(
        ADMISSION_RULE_ID,
        outcome,
        outcome == "passed",
        outcome == "blocked",
        reason,
        canonical,
        validated,
        consumed,
        False,
    )


def classify_admit_014_formal_evaluator_interface_design(
    *,
    stage_authorization_context: object = _DESIGN_MISSING,
) -> Admit014EvaluationResultContractDesign:
    """Pure in-memory Design oracle; this is not the future public evaluator."""
    if (
        stage_authorization_context is _DESIGN_MISSING
        or stage_authorization_context is None
    ):
        return _make_result(
            "blocked",
            "STAGE_AUTHORIZATION_CONTEXT_REQUIRED",
            (),
            (),
            (),
        )
    if not isinstance(stage_authorization_context, Mapping):
        return _make_result(
            "blocked",
            "STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID",
            (),
            (),
            (),
        )
    consumed = (AUTHORIZATION_CONTEXT_ITEM,)
    try:
        value = stage_authorization_context[AUTHORIZATION_CONTEXT_ITEM]
    except KeyError:
        return _make_result(
            "blocked",
            "CURRENT_STAGE_DOWNLOAD_AUTHORIZED_MISSING",
            (),
            (),
            consumed,
        )
    except Exception:
        return _make_result(
            "blocked",
            "STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED",
            (),
            (),
            consumed,
        )
    if type(value) is not bool:
        return _make_result(
            "blocked",
            "CURRENT_STAGE_DOWNLOAD_AUTHORIZED_TYPE_INVALID",
            (),
            (),
            consumed,
        )
    canonical = ((AUTHORIZATION_CONTEXT_ITEM, value),)
    if value is False:
        return _make_result(
            "blocked",
            "BULK_DOWNLOAD_NOT_AUTHORIZED",
            canonical,
            consumed,
            consumed,
        )
    return _make_result("passed", "", canonical, consumed, consumed)


CONTRACT_FILE = (
    "covapie_admit_014_formal_evaluator_interface_and_result_contract.csv"
)
ROUTING_FILE = (
    "covapie_admit_014_formal_evaluator_routing_and_consumption_contract.csv"
)
TRUTH_FILE = "covapie_admit_014_formal_evaluator_interface_truth_matrix.csv"
SOURCE_FILE = (
    "covapie_admit_014_formal_evaluator_interface_source_boundary_audit.csv"
)
ISSUE_FILE = (
    "covapie_admit_014_formal_evaluator_interface_issue_readiness_inventory.csv"
)
MANIFEST_FILE = (
    "covapie_admit_014_formal_evaluator_interface_contract_manifest.json"
)
OUTPUT_FILES = (
    CONTRACT_FILE,
    ROUTING_FILE,
    TRUTH_FILE,
    SOURCE_FILE,
    ISSUE_FILE,
    MANIFEST_FILE,
)

CONTRACT_COLUMNS = (
    "contract_order",
    "contract_group",
    "contract_item",
    "future_public_name",
    "exact_contract",
    "exact_type_or_value",
    "contract_passed",
)
ROUTING_COLUMNS = (
    "routing_order",
    "routing_case",
    "input_state",
    "lookup_attempted",
    "canonical_record",
    "validated_fields",
    "consumed_fields",
    "expected_outcome",
    "expected_reason",
    "routing_passed",
)
TRUTH_COLUMNS = (
    "case_order",
    "case_id",
    "case_group",
    "invocation_form",
    "stage_context_representation",
    "expected_outcome",
    "observed_outcome",
    "expected_reason",
    "observed_reason",
    "expected_canonical_record",
    "observed_canonical_record",
    "expected_validated_fields",
    "observed_validated_fields",
    "expected_consumed_fields",
    "observed_consumed_fields",
    "result_contract_passed",
    "case_passed",
)
SOURCE_COLUMNS = (
    "source_order",
    "source_relative_path",
    "expected_sha256",
    "base_tree_mode",
    "tracked",
    "index_stage_zero",
    "base_tree_blob",
    "filesystem_regular",
    "non_symlink",
    "parent_chain_non_symlink",
    "safe_descendant",
    "pinned_fd_read",
    "post_read_identity_verified",
    "source_verified",
)

AUTH_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_014_"
    "download_authorization_contract_v1"
)
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
RUNTIME_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1"
)
AUTH_PRODUCTION = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_admit_014_"
    "download_authorization_contract_design_gate.py"
)
PRE_MATRIX = (
    PRE_ROOT / "covapie_admit_014_formal_evaluator_precondition_matrix.csv"
)
AUA_CONTEXT = (
    AUA_ROOT / "covapie_bulk_download_admission_evaluation_context_contract.csv"
)
RUNTIME_PRODUCTION = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013.py"
)
RUNTIME_MANIFEST = (
    RUNTIME_ROOT / "covapie_admit_001_to_013_runtime_manifest.json"
)

SOURCE_SHA256 = {
    AUTH_PRODUCTION: "b2616c01234c899695c08280daacfa21cb137b847a01f5bf6e52e807b0770434",
    AUTH_ROOT
    / "covapie_admit_014_download_authorization_value_and_trust_contract.csv": "b22f02efdd53dce995730a05cc5c12ffa659c2d98b345afc663b118cc104752d",
    AUTH_ROOT
    / "covapie_admit_014_stage_authorization_routing_and_enforcement_contract.csv": "68bc56b214f212ffec359049146e371ac7ce48bed34bfd6bb80313a2fd7046a6",
    AUTH_ROOT
    / "covapie_admit_014_failure_taxonomy_and_precedence.csv": "1970da57fdec24e9c5b6e518e1dfa7c2103d3bef6da065b24e3d61a296cdeffc",
    AUTH_ROOT
    / "covapie_admit_014_download_authorization_truth_matrix.csv": "e4f39f5178b91906639670f5c1ddb1c02b40c802de9ce386aee2a6b6d49f8482",
    AUTH_ROOT
    / "covapie_admit_014_issue_readiness_inventory.csv": "10e3475cb329d517c27fae26636294d0aa69a609a3c59a8b7f0119b0b123edbe",
    AUTH_ROOT
    / "covapie_admit_014_download_authorization_contract_manifest.json": "9c54c9d6cb11776b04938d9be048699041bfc4020dca4c00425faadaaaa5d4d2",
    PRE_MATRIX: "6b52a4e96dd960e7df53b7160f5cd00d63fbeb62ee5bc5ec9882623efd268c30",
    AUA_CONTEXT: "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0",
    RUNTIME_PRODUCTION: "79f95b6e178044ff5b4f5abbd6445b6cd848e81ba1a8a16cacdf831b05b9b892",
    RUNTIME_MANIFEST: "2940e6cc02a92b4919cdece3b1fa7c2f5e27d844f2962bb18757197266c23f79",
}
SOURCE_PATHS = tuple(SOURCE_SHA256)


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


@dataclass(frozen=True)
class _Source:
    path: Path
    content: bytes
    sha256: str
    mode: str
    blob: str


def _canonical_runtime_guard() -> None:
    if (
        sys.implementation.name != CANONICAL_PYTHON_IMPLEMENTATION
        or tuple(sys.version_info[:3]) != (3, 10, 4)
    ):
        raise RuntimeError(
            "canonical evidence build requires CPython 3.10.4; "
            + NONCANONICAL_PYTHON_POLICY
        )


def _git(
    arguments: list[str], *, text: bool = True
) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *arguments],
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
    root_before = os.lstat(REPO_ROOT)
    if stat.S_ISLNK(root_before.st_mode) or not stat.S_ISDIR(root_before.st_mode):
        raise ValueError("unsafe repository root")
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


def build_frozen_source_snapshot() -> tuple[_Source, ...]:
    _canonical_runtime_guard()
    identity = _git(
        ["show", "-s", "--format=%H%n%P%n%T%n%s", BASE_COMMIT]
    )
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
    if len(SOURCE_PATHS) != 11 or len(set(SOURCE_PATHS)) != 11:
        raise ValueError("source boundary must be ordered Exact11")
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
        snapshot.append(_Source(path, current, digest, mode, blob))
    return tuple(snapshot)


def _source(snapshot: tuple[_Source, ...], path: Path) -> _Source:
    return next(item for item in snapshot if item.path == path)


def _csv_rows(
    snapshot: tuple[_Source, ...], path: Path
) -> list[dict[str, str]]:
    return list(
        csv.DictReader(
            io.StringIO(_source(snapshot, path).content.decode(), newline="")
        )
    )


def _json(snapshot: tuple[_Source, ...], path: Path) -> dict[str, Any]:
    value = json.loads(_source(snapshot, path).content)
    if type(value) is not dict:
        raise ValueError("JSON object required")
    return value


def _verify_predecessors(snapshot: tuple[_Source, ...]) -> None:
    authorization = _json(
        snapshot,
        AUTH_ROOT
        / "covapie_admit_014_download_authorization_contract_manifest.json",
    )
    preconditions = _csv_rows(snapshot, PRE_MATRIX)
    contexts = _csv_rows(snapshot, AUA_CONTEXT)
    runtime = _json(snapshot, RUNTIME_MANIFEST)
    admit014 = next(
        row for row in contexts if row["required_by_rules"] == "ADMIT_014"
    )
    admit015 = next(
        row for row in contexts if row["required_by_rules"] == "ADMIT_015"
    )
    if not (
        authorization["base_commit"] == BASE_PARENT
        and authorization["current_permission"] is False
        and authorization["ready_for_bulk_download_now"] is False
        and authorization[
            "mandatory_pre_download_authorization_enforcement_contract"
        ]["implemented"]
        is False
        and authorization["precondition_transition"]["complete_count"] == 46
        and authorization["precondition_transition"]["incomplete_count"] == 5
        and len(preconditions) == 51
        and [row["precondition_id"] for row in preconditions]
        == [f"PRE_{index:03d}" for index in range(1, 52)]
        and admit014["context_item"] == AUTHORIZATION_CONTEXT_ITEM
        and admit014["context_scope"] == "stage"
        and admit015["context_item"] == ADMIT_015_CONTEXT_ITEM
        and admit015["context_scope"] == "stage"
        and runtime["registered_rule_ids"]
        == [f"ADMIT_{index:03d}" for index in range(1, 14)]
        and runtime["known_not_registered_rule_ids"] == ["ADMIT_014", "ADMIT_015"]
        and runtime["admit_014_registered_in_engine"] is False
        and runtime["combined_candidate_verdict_implemented"] is False
        and runtime["cross_rule_aggregation_implemented"] is False
        and runtime["provider_mapping_validated"] is False
        and runtime["ready_for_bulk_download_now"] is False
    ):
        raise ValueError("ADMIT_014 predecessor lineage drift")


def _contract_rows() -> list[dict[str, str]]:
    specs: list[tuple[str, str, str, str, str]] = [
        (
            "signature",
            "function",
            "evaluate_admit_014",
            FUTURE_PUBLIC_SIGNATURE,
            "public name",
        ),
        (
            "signature",
            "parameter count",
            "evaluate_admit_014",
            "1",
            "int",
        ),
        (
            "signature",
            "stage_authorization_context",
            "evaluate_admit_014",
            "keyword-only; annotation object; private _MISSING default",
            "inspect.Parameter",
        ),
        (
            "signature",
            "return annotation",
            "evaluate_admit_014",
            "Admit014EvaluationResult",
            "str forward annotation",
        ),
        (
            "signature",
            "forbidden call shapes",
            "evaluate_admit_014",
            "no positional; no *args; no **kwargs; no extra parameters",
            "closed signature",
        ),
    ]
    for name, exact_type in zip(RESULT_FIELDS, RESULT_FIELD_TYPES, strict=True):
        specs.append(
            (
                "result_field",
                name,
                "Admit014EvaluationResult",
                "Exact9 ordered frozen dataclass field",
                exact_type,
            )
        )
    specs.extend(
        (
            (
                "representation",
                "canonical_stage_authorization_record",
                "Admit014EvaluationResult",
                "() or exact one-pair tuple retaining exact False|True",
                "exact tuple of exact pair tuple",
            ),
            (
                "representation",
                "validated_stage_authorization_fields",
                "Admit014EvaluationResult",
                "() or ('current_stage_download_authorized',)",
                "exact tuple of exact str",
            ),
            (
                "representation",
                "consumed_stage_authorization_fields",
                "Admit014EvaluationResult",
                "() or ('current_stage_download_authorized',)",
                "exact tuple of exact str",
            ),
            (
                "invariant",
                "outcome and flags",
                "Admit014EvaluationResult",
                "passed iff outcome passed; blocks iff outcome blocked",
                "closed invariant",
            ),
            (
                "invariant",
                "reason",
                "Admit014EvaluationResult",
                "empty iff passed; six exact blockers",
                "closed vocabulary",
            ),
            (
                "invariant",
                "evaluator_io_used",
                "Admit014EvaluationResult",
                "exact False",
                "bool",
            ),
            (
                "formal_symbol_state",
                "formal evaluator",
                "evaluate_admit_014",
                "not implemented",
                "design assertion",
            ),
            (
                "formal_symbol_state",
                "formal result",
                "Admit014EvaluationResult",
                "not defined",
                "design assertion",
            ),
        )
    )
    return [
        {
            "contract_order": str(index),
            "contract_group": group,
            "contract_item": item,
            "future_public_name": public,
            "exact_contract": contract,
            "exact_type_or_value": exact_type,
            "contract_passed": "true",
        }
        for index, (group, item, public, contract, exact_type) in enumerate(
            specs, 1
        )
    ]


def _routing_rows() -> list[dict[str, str]]:
    field = (AUTHORIZATION_CONTEXT_ITEM,)
    specs = (
        (
            "OMITTED",
            "_MISSING",
            False,
            (),
            (),
            (),
            "blocked",
            REASON_VOCABULARY[1],
        ),
        (
            "EXPLICIT_NONE",
            "None",
            False,
            (),
            (),
            (),
            "blocked",
            REASON_VOCABULARY[1],
        ),
        (
            "NON_MAPPING",
            "object",
            False,
            (),
            (),
            (),
            "blocked",
            REASON_VOCABULARY[2],
        ),
        (
            "TARGET_KEYERROR",
            "Mapping target lookup raises KeyError",
            True,
            (),
            (),
            field,
            "blocked",
            REASON_VOCABULARY[3],
        ),
        (
            "TARGET_NONKEYERROR",
            "Mapping target lookup raises non-KeyError",
            True,
            (),
            (),
            field,
            "blocked",
            REASON_VOCABULARY[4],
        ),
        (
            "INVALID_TYPE",
            "Mapping target value type is not exact bool",
            True,
            (),
            (),
            field,
            "blocked",
            REASON_VOCABULARY[5],
        ),
        (
            "EXACT_FALSE",
            "Mapping target exact False",
            True,
            ((AUTHORIZATION_CONTEXT_ITEM, False),),
            field,
            field,
            "blocked",
            REASON_VOCABULARY[6],
        ),
        (
            "EXACT_TRUE",
            "Mapping target exact True",
            True,
            ((AUTHORIZATION_CONTEXT_ITEM, True),),
            field,
            field,
            "passed",
            "",
        ),
    )
    return [
        {
            "routing_order": str(index),
            "routing_case": case,
            "input_state": state,
            "lookup_attempted": str(lookup).lower(),
            "canonical_record": repr(canonical),
            "validated_fields": repr(validated),
            "consumed_fields": repr(consumed),
            "expected_outcome": outcome,
            "expected_reason": reason,
            "routing_passed": "true",
        }
        for index, (
            case,
            state,
            lookup,
            canonical,
            validated,
            consumed,
            outcome,
            reason,
        ) in enumerate(specs, 1)
    ]


class _InstrumentedMapping(Mapping[str, object]):
    def __init__(
        self,
        values: dict[str, object] | None = None,
        *,
        lookup_error: BaseException | None = None,
    ) -> None:
        self.values = {} if values is None else values
        self.lookup_error = lookup_error
        self.item_keys: list[str] = []
        self.iteration_count = 0
        self.len_count = 0
        self.get_count = 0
        self.contains_count = 0

    def __getitem__(self, key: str) -> object:
        self.item_keys.append(key)
        if self.lookup_error is not None:
            raise self.lookup_error
        return self.values[key]

    def __iter__(self) -> Iterator[str]:
        self.iteration_count += 1
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


class _Truthy:
    def __bool__(self) -> bool:
        return True


class _Falsy:
    def __bool__(self) -> bool:
        return False


@dataclass(frozen=True)
class _TruthCase:
    case_id: str
    group: str
    invocation: str
    context: object
    outcome: str
    reason: str
    negative: str = ""


NEGATIVE_RESULT_CASES = (
    "WRONG_ADMISSION_RULE_ID",
    "UNKNOWN_OUTCOME",
    "PASSED_NONEXACT_BOOL",
    "BLOCKS_NONEXACT_BOOL",
    "IO_NONEXACT_BOOL",
    "IO_TRUE",
    "PASS_NONEMPTY_REASON",
    "BLOCK_EMPTY_REASON",
    "CANONICAL_LIST",
    "CANONICAL_TUPLE_SUBCLASS",
    "PAIR_TUPLE_SUBCLASS",
    "WRONG_CANONICAL_KEY",
    "NONBOOL_CANONICAL_VALUE",
    "DUPLICATE_CANONICAL_PAIR",
    "VALIDATED_LIST",
    "VALIDATED_TUPLE_SUBCLASS",
    "UNKNOWN_VALIDATED_FIELD",
    "DUPLICATE_VALIDATED_FIELD",
    "CONSUMED_LIST",
    "CONSUMED_TUPLE_SUBCLASS",
    "UNKNOWN_CONSUMED_FIELD",
    "DUPLICATE_CONSUMED_FIELD",
    "CANONICAL_VALIDATED_MISMATCH",
    "VALIDATED_CONSUMED_MISMATCH",
)


class _ResultSubclass(Admit014EvaluationResultContractDesign):
    pass


def _reject_negative_result(case_id: str) -> str:
    baseline = classify_admit_014_formal_evaluator_interface_design(
        stage_authorization_context={AUTHORIZATION_CONTEXT_ITEM: True}
    )
    values = {name: getattr(baseline, name) for name in RESULT_FIELDS}
    try:
        if case_id == "WRONG_ADMISSION_RULE_ID":
            values["admission_rule_id"] = "ADMIT_015"
        elif case_id == "UNKNOWN_OUTCOME":
            values["outcome"] = "invalid"
        elif case_id == "PASSED_NONEXACT_BOOL":
            values["passed"] = 1
        elif case_id == "BLOCKS_NONEXACT_BOOL":
            values["blocks_candidate"] = 0
        elif case_id == "IO_NONEXACT_BOOL":
            values["evaluator_io_used"] = 0
        elif case_id == "IO_TRUE":
            values["evaluator_io_used"] = True
        elif case_id == "PASS_NONEMPTY_REASON":
            values["reason"] = "BULK_DOWNLOAD_NOT_AUTHORIZED"
        elif case_id == "BLOCK_EMPTY_REASON":
            values.update(outcome="blocked", passed=False, blocks_candidate=True)
        elif case_id == "CANONICAL_LIST":
            values["canonical_stage_authorization_record"] = list(
                values["canonical_stage_authorization_record"]
            )
        elif case_id == "CANONICAL_TUPLE_SUBCLASS":
            values["canonical_stage_authorization_record"] = _TupleSubclass(
                values["canonical_stage_authorization_record"]
            )
        elif case_id == "PAIR_TUPLE_SUBCLASS":
            values["canonical_stage_authorization_record"] = (
                _PairTupleSubclass((AUTHORIZATION_CONTEXT_ITEM, True)),
            )
        elif case_id == "WRONG_CANONICAL_KEY":
            values["canonical_stage_authorization_record"] = (
                (ADMIT_015_CONTEXT_ITEM, True),
            )
        elif case_id == "NONBOOL_CANONICAL_VALUE":
            values["canonical_stage_authorization_record"] = (
                (AUTHORIZATION_CONTEXT_ITEM, 1),
            )
        elif case_id == "DUPLICATE_CANONICAL_PAIR":
            pair = (AUTHORIZATION_CONTEXT_ITEM, True)
            values["canonical_stage_authorization_record"] = (pair, pair)
        elif case_id == "VALIDATED_LIST":
            values["validated_stage_authorization_fields"] = [
                AUTHORIZATION_CONTEXT_ITEM
            ]
        elif case_id == "VALIDATED_TUPLE_SUBCLASS":
            values["validated_stage_authorization_fields"] = _TupleSubclass(
                (AUTHORIZATION_CONTEXT_ITEM,)
            )
        elif case_id == "UNKNOWN_VALIDATED_FIELD":
            values["validated_stage_authorization_fields"] = (
                ADMIT_015_CONTEXT_ITEM,
            )
        elif case_id == "DUPLICATE_VALIDATED_FIELD":
            values["validated_stage_authorization_fields"] = (
                AUTHORIZATION_CONTEXT_ITEM,
                AUTHORIZATION_CONTEXT_ITEM,
            )
        elif case_id == "CONSUMED_LIST":
            values["consumed_stage_authorization_fields"] = [
                AUTHORIZATION_CONTEXT_ITEM
            ]
        elif case_id == "CONSUMED_TUPLE_SUBCLASS":
            values["consumed_stage_authorization_fields"] = _TupleSubclass(
                (AUTHORIZATION_CONTEXT_ITEM,)
            )
        elif case_id == "UNKNOWN_CONSUMED_FIELD":
            values["consumed_stage_authorization_fields"] = (
                ADMIT_015_CONTEXT_ITEM,
            )
        elif case_id == "DUPLICATE_CONSUMED_FIELD":
            values["consumed_stage_authorization_fields"] = (
                AUTHORIZATION_CONTEXT_ITEM,
                AUTHORIZATION_CONTEXT_ITEM,
            )
        elif case_id == "CANONICAL_VALIDATED_MISMATCH":
            values["validated_stage_authorization_fields"] = ()
        elif case_id == "VALIDATED_CONSUMED_MISMATCH":
            values["consumed_stage_authorization_fields"] = ()
        Admit014EvaluationResultContractDesign(
            *(values[name] for name in RESULT_FIELDS)
        )
    except (TypeError, ValueError) as error:
        return f"RESULT_CONTRACT_REJECTED:{type(error).__name__}"
    raise ValueError(f"negative result case accepted: {case_id}")


def _representation(value: object) -> str:
    if value is _DESIGN_MISSING:
        return "<MISSING>"
    if isinstance(value, _InstrumentedMapping):
        if value.lookup_error is not None:
            return f"<Mapping:{type(value.lookup_error).__name__}>"
        return (
            "{"
            + ", ".join(
                f"{key!r}: {_representation(item)}"
                for key, item in value.values.items()
            )
            + "}"
        )
    if isinstance(value, _Truthy):
        return "<CUSTOM_TRUTHY>"
    if isinstance(value, _Falsy):
        return "<CUSTOM_FALSY>"
    if type(value) is object:
        return "<OBJECT>"
    return repr(value)


def _positive_truth_cases() -> list[_TruthCase]:
    invalid = (
        ("INT_ZERO", 0),
        ("INT_ONE", 1),
        ("FLOAT_ZERO", 0.0),
        ("FLOAT_ONE", 1.0),
        ("STRING_FALSE", "false"),
        ("STRING_TRUE", "true"),
        ("NONE_VALUE", None),
        ("LIST_VALUE", []),
        ("DICT_VALUE", {}),
        ("CUSTOM_TRUTHY", _Truthy()),
        ("CUSTOM_FALSY", _Falsy()),
    )
    cases = [
        _TruthCase(
            "SIGNATURE_EXACT_STRING",
            "signature",
            FUTURE_PUBLIC_SIGNATURE,
            _DESIGN_MISSING,
            "verified",
            "",
        ),
        _TruthCase(
            "SIGNATURE_ONE_KEYWORD_ONLY",
            "signature",
            "one keyword-only parameter",
            _DESIGN_MISSING,
            "verified",
            "",
        ),
        _TruthCase(
            "SIGNATURE_PRIVATE_MISSING",
            "signature",
            "private missing singleton default",
            _DESIGN_MISSING,
            "verified",
            "",
        ),
        _TruthCase(
            "SIGNATURE_RETURN_ANNOTATION",
            "signature",
            "Admit014EvaluationResult",
            _DESIGN_MISSING,
            "verified",
            "",
        ),
        _TruthCase(
            "SIGNATURE_NO_VARARGS",
            "signature",
            "no *args",
            _DESIGN_MISSING,
            "verified",
            "",
        ),
        _TruthCase(
            "SIGNATURE_NO_VARKW",
            "signature",
            "no **kwargs",
            _DESIGN_MISSING,
            "verified",
            "",
        ),
        _TruthCase(
            "SIGNATURE_POSITIONAL_REJECTED",
            "signature",
            "positional invocation rejected",
            _DESIGN_MISSING,
            "rejected",
            "TypeError",
        ),
        _TruthCase(
            "SIGNATURE_UNKNOWN_KEYWORD_REJECTED",
            "signature",
            "unknown keyword rejected",
            _DESIGN_MISSING,
            "rejected",
            "TypeError",
        ),
        _TruthCase(
            "OMITTED",
            "context_structure",
            "omitted",
            _DESIGN_MISSING,
            "blocked",
            REASON_VOCABULARY[1],
        ),
        _TruthCase(
            "EXPLICIT_NONE",
            "context_structure",
            "explicit None",
            None,
            "blocked",
            REASON_VOCABULARY[1],
        ),
    ]
    for case_id, value in (
        ("CONTEXT_OBJECT", object()),
        ("CONTEXT_INT", 7),
        ("CONTEXT_STR", "x"),
        ("CONTEXT_LIST", []),
    ):
        cases.append(
            _TruthCase(
                case_id,
                "context_structure",
                "keyword",
                value,
                "blocked",
                REASON_VOCABULARY[2],
            )
        )
    cases.extend(
        (
            _TruthCase(
                "EMPTY_MAPPING",
                "context_structure",
                "keyword",
                _InstrumentedMapping(),
                "blocked",
                REASON_VOCABULARY[3],
            ),
            _TruthCase(
                "UNRELATED_ONLY_MAPPING",
                "context_structure",
                "keyword",
                _InstrumentedMapping({"other": True}),
                "blocked",
                REASON_VOCABULARY[3],
            ),
            _TruthCase(
                "LOOKUP_KEYERROR",
                "lookup",
                "keyword",
                _InstrumentedMapping(
                    lookup_error=KeyError(AUTHORIZATION_CONTEXT_ITEM)
                ),
                "blocked",
                REASON_VOCABULARY[3],
            ),
            _TruthCase(
                "LOOKUP_RUNTIMEERROR",
                "lookup",
                "keyword",
                _InstrumentedMapping(lookup_error=RuntimeError("boom")),
                "blocked",
                REASON_VOCABULARY[4],
            ),
            _TruthCase(
                "LOOKUP_VALUEERROR",
                "lookup",
                "keyword",
                _InstrumentedMapping(lookup_error=ValueError("boom")),
                "blocked",
                REASON_VOCABULARY[4],
            ),
        )
    )
    for case_id, value in invalid:
        cases.append(
            _TruthCase(
                case_id,
                "invalid_exact_type",
                "keyword",
                _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: value}),
                "blocked",
                REASON_VOCABULARY[5],
            )
        )
    cases.extend(
        (
            _TruthCase(
                "EXACT_FALSE",
                "business_outcome",
                "keyword",
                _InstrumentedMapping(
                    {AUTHORIZATION_CONTEXT_ITEM: False}
                ),
                "blocked",
                REASON_VOCABULARY[6],
            ),
            _TruthCase(
                "EXACT_TRUE",
                "business_outcome",
                "keyword",
                _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: True}),
                "passed",
                "",
            ),
            _TruthCase(
                "ADMIT015_PLUS_TRUE",
                "mapping_behavior",
                "keyword",
                _InstrumentedMapping(
                    {
                        ADMIT_015_CONTEXT_ITEM: False,
                        AUTHORIZATION_CONTEXT_ITEM: True,
                    }
                ),
                "passed",
                "",
            ),
            _TruthCase(
                "ADMIT015_PLUS_FALSE",
                "mapping_behavior",
                "keyword",
                _InstrumentedMapping(
                    {
                        ADMIT_015_CONTEXT_ITEM: True,
                        AUTHORIZATION_CONTEXT_ITEM: False,
                    }
                ),
                "blocked",
                REASON_VOCABULARY[6],
            ),
            _TruthCase(
                "MANY_EXTRA_PLUS_TRUE",
                "mapping_behavior",
                "keyword",
                _InstrumentedMapping(
                    {
                        **{f"extra_{index}": object() for index in range(20)},
                        AUTHORIZATION_CONTEXT_ITEM: True,
                    }
                ),
                "passed",
                "",
            ),
            _TruthCase(
                "ITERATION_RAISES",
                "mapping_behavior",
                "keyword",
                _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: True}),
                "passed",
                "",
            ),
            _TruthCase(
                "LEN_RAISES",
                "mapping_behavior",
                "keyword",
                _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: True}),
                "passed",
                "",
            ),
            _TruthCase(
                "GET_RAISES",
                "mapping_behavior",
                "keyword",
                _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: True}),
                "passed",
                "",
            ),
            _TruthCase(
                "CONTAINS_RAISES",
                "mapping_behavior",
                "keyword",
                _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: True}),
                "passed",
                "",
            ),
            _TruthCase(
                "PROJECTION_OMITTED",
                "result_projection",
                "omitted",
                _DESIGN_MISSING,
                "blocked",
                REASON_VOCABULARY[1],
            ),
            _TruthCase(
                "PROJECTION_MISSING_KEY",
                "result_projection",
                "keyword",
                _InstrumentedMapping(),
                "blocked",
                REASON_VOCABULARY[3],
            ),
            _TruthCase(
                "PROJECTION_LOOKUP_FAILED",
                "result_projection",
                "keyword",
                _InstrumentedMapping(lookup_error=RuntimeError("boom")),
                "blocked",
                REASON_VOCABULARY[4],
            ),
            _TruthCase(
                "PROJECTION_INVALID_TYPE",
                "result_projection",
                "keyword",
                _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: "true"}),
                "blocked",
                REASON_VOCABULARY[5],
            ),
            _TruthCase(
                "PROJECTION_FALSE",
                "result_projection",
                "keyword",
                _InstrumentedMapping(
                    {AUTHORIZATION_CONTEXT_ITEM: False}
                ),
                "blocked",
                REASON_VOCABULARY[6],
            ),
            _TruthCase(
                "PROJECTION_TRUE",
                "result_projection",
                "keyword",
                _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: True}),
                "passed",
                "",
            ),
        )
    )
    if len(cases) != 45:
        raise AssertionError("positive truth matrix Exact45 drift")
    return cases


def _expected_projection(
    outcome: str, reason: str
) -> tuple[tuple[tuple[str, bool], ...], tuple[str, ...], tuple[str, ...]]:
    field = (AUTHORIZATION_CONTEXT_ITEM,)
    if reason in REASON_VOCABULARY[1:3]:
        return (), (), ()
    if reason in REASON_VOCABULARY[3:6]:
        return (), (), field
    value = outcome == "passed"
    return ((AUTHORIZATION_CONTEXT_ITEM, value),), field, field


def _signature_truth_observation(case_id: str) -> tuple[str, str]:
    """Return deterministic signature-meta evidence from real checks."""
    signature = FORMAL_SIGNATURE_DESIGN
    if type(signature) is not inspect.Signature:
        raise ValueError("formal signature Design requires exact inspect.Signature")
    parameters = tuple(signature.parameters.values())
    frozen_public_signature = (
        "evaluate_admit_014(*, stage_authorization_context: object = _MISSING) "
        "-> Admit014EvaluationResult"
    )
    property_checks = {
        "SIGNATURE_EXACT_STRING": (
            FUTURE_PUBLIC_SIGNATURE == frozen_public_signature
        ),
        "SIGNATURE_ONE_KEYWORD_ONLY": (
            len(parameters) == 1
            and parameters[0].name == "stage_authorization_context"
            and parameters[0].kind is inspect.Parameter.KEYWORD_ONLY
        ),
        "SIGNATURE_PRIVATE_MISSING": (
            len(parameters) == 1
            and parameters[0].default is _DESIGN_MISSING
            and parameters[0].default is not None
        ),
        "SIGNATURE_RETURN_ANNOTATION": (
            signature.return_annotation == "Admit014EvaluationResult"
        ),
        "SIGNATURE_NO_VARARGS": not any(
            parameter.kind is inspect.Parameter.VAR_POSITIONAL
            for parameter in parameters
        ),
        "SIGNATURE_NO_VARKW": not any(
            parameter.kind is inspect.Parameter.VAR_KEYWORD
            for parameter in parameters
        ),
    }
    if case_id in property_checks:
        if not property_checks[case_id]:
            raise ValueError(f"signature property verification failed: {case_id}")
        return "verified", ""

    if case_id == "SIGNATURE_POSITIONAL_REJECTED":
        actions = (
            lambda: signature.bind(object()),
            lambda: classify_admit_014_formal_evaluator_interface_design(object()),
        )
    elif case_id == "SIGNATURE_UNKNOWN_KEYWORD_REJECTED":
        actions = (
            lambda: signature.bind(unknown=True),
            lambda: classify_admit_014_formal_evaluator_interface_design(
                unknown=True
            ),
        )
    else:
        raise ValueError(f"unknown signature truth case: {case_id}")
    for action in actions:
        try:
            action()
        except TypeError:
            continue
        except Exception as error:
            raise ValueError(
                f"signature rejection used wrong exception: {case_id}"
            ) from error
        raise ValueError(f"signature rejection accepted invalid call: {case_id}")
    return "rejected", "TypeError"


def _truth_rows() -> list[dict[str, str]]:
    cases = _positive_truth_cases()
    cases.extend(
        _TruthCase(
            case_id,
            "negative_result_contract",
            "direct result construction",
            _DESIGN_MISSING,
            "passed",
            "",
            case_id,
        )
        for case_id in NEGATIVE_RESULT_CASES
    )
    rows = []
    for order, case in enumerate(cases, 1):
        if case.group == "signature":
            expected_canonical = ()
            expected_validated = ()
            expected_consumed = ()
            observed_outcome, observed_reason = _signature_truth_observation(
                case.case_id
            )
            observed_canonical = ()
            observed_validated = ()
            observed_consumed = ()
            result_passed = (
                observed_outcome == case.outcome
                and observed_reason == case.reason
            )
        else:
            expected_canonical, expected_validated, expected_consumed = (
                _expected_projection(case.outcome, case.reason)
            )
        if case.negative:
            observed_outcome = "rejected"
            observed_reason = _reject_negative_result(case.negative)
            observed_canonical = ()
            observed_validated = ()
            observed_consumed = ()
            result_passed = observed_reason.startswith(
                "RESULT_CONTRACT_REJECTED:"
            )
        elif case.group != "signature":
            kwargs = (
                {}
                if case.context is _DESIGN_MISSING
                else {"stage_authorization_context": case.context}
            )
            result = classify_admit_014_formal_evaluator_interface_design(
                **kwargs
            )
            observed_outcome = result.outcome
            observed_reason = result.reason
            observed_canonical = result.canonical_stage_authorization_record
            observed_validated = result.validated_stage_authorization_fields
            observed_consumed = result.consumed_stage_authorization_fields
            mapping = (
                case.context
                if isinstance(case.context, _InstrumentedMapping)
                else None
            )
            result_passed = (
                validate_admit_014_evaluation_result_contract_design(result)
                and observed_outcome == case.outcome
                and observed_reason == case.reason
                and observed_canonical == expected_canonical
                and observed_validated == expected_validated
                and observed_consumed == expected_consumed
                and (
                    mapping is None
                    or (
                        mapping.item_keys == [AUTHORIZATION_CONTEXT_ITEM]
                        and mapping.iteration_count == 0
                        and mapping.len_count == 0
                        and mapping.get_count == 0
                        and mapping.contains_count == 0
                    )
                )
            )
        rows.append(
            {
                "case_order": str(order),
                "case_id": case.case_id,
                "case_group": case.group,
                "invocation_form": case.invocation,
                "stage_context_representation": _representation(case.context),
                "expected_outcome": (
                    "rejected" if case.negative else case.outcome
                ),
                "observed_outcome": observed_outcome,
                "expected_reason": (
                    "RESULT_CONTRACT_REJECTED"
                    if case.negative
                    else case.reason
                ),
                "observed_reason": observed_reason,
                "expected_canonical_record": repr(
                    () if case.negative else expected_canonical
                ),
                "observed_canonical_record": repr(observed_canonical),
                "expected_validated_fields": repr(
                    () if case.negative else expected_validated
                ),
                "observed_validated_fields": repr(observed_validated),
                "expected_consumed_fields": repr(
                    () if case.negative else expected_consumed
                ),
                "observed_consumed_fields": repr(observed_consumed),
                "result_contract_passed": str(result_passed).lower(),
                "case_passed": str(result_passed).lower(),
            }
        )
    if len(rows) != 69 or not all(
        row["case_passed"] == "true" for row in rows
    ):
        raise ValueError("truth matrix Exact69 drift")
    return rows


ISSUE_TRANSITIONS = {
    "ADMIT_014_STANDALONE_SIGNATURE_UNRESOLVED": (
        "future one-keyword-only signature with private missing singleton frozen"
    ),
    "ADMIT_014_RESULT_CONTRACT_UNRESOLVED": (
        "future Exact9 result fields types canonical validated consumed "
        "representations and invariants frozen"
    ),
}
ISSUE_TRANSITION_ACTION = (
    "resolved_by_successor_formal_interface_contract_design"
)
GLOBAL_OPEN_ISSUES = (
    "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
    "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
    "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
    "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
)


def _issue_rows(snapshot: tuple[_Source, ...]) -> list[dict[str, str]]:
    inherited = _csv_rows(
        snapshot,
        AUTH_ROOT / "covapie_admit_014_issue_readiness_inventory.csv",
    )
    rows = [dict(row) for row in inherited]
    for row in rows:
        evidence = ISSUE_TRANSITIONS.get(row["issue_id"])
        if evidence is not None:
            row["successor_effective_status"] = "resolved"
            row["successor_transition_stage"] = STAGE
            row["successor_transition_action"] = ISSUE_TRANSITION_ACTION
            row["successor_transition_evidence"] = evidence
    by_id = {row["issue_id"]: row for row in rows}
    if (
        len(rows) != 30
        or [row["inherited_order"] for row in rows]
        != [str(index) for index in range(1, 31)]
        or [row["issue_id"] for row in rows[:23]]
        != [row["issue_id"] for row in inherited[:23]]
        or any(
            by_id[issue]["successor_effective_status"] != "resolved"
            for issue in ISSUE_TRANSITIONS
        )
        or any(
            by_id[issue]["successor_effective_status"] != "open"
            for issue in GLOBAL_OPEN_ISSUES
        )
        or by_id["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"][
            "affected_rules"
        ]
        != "ADMIT_014|ADMIT_015"
        or any(
            row["successor_effective_status"] != "resolved"
            for row in rows[23:]
        )
    ):
        raise ValueError("Exact30 issue transition drift")
    return rows


def _source_rows_for_artifact(
    snapshot: tuple[_Source, ...],
) -> list[dict[str, str]]:
    return [
        {
            "source_order": str(index),
            "source_relative_path": record.path.as_posix(),
            "expected_sha256": record.sha256,
            "base_tree_mode": record.mode,
            "tracked": "true",
            "index_stage_zero": "true",
            "base_tree_blob": record.blob,
            "filesystem_regular": "true",
            "non_symlink": "true",
            "parent_chain_non_symlink": "true",
            "safe_descendant": "true",
            "pinned_fd_read": "true",
            "post_read_identity_verified": "true",
            "source_verified": "true",
        }
        for index, record in enumerate(snapshot, 1)
    ]


TRUE_READINESS = (
    "admit_014_preconditions_audited",
    "admit_014_download_authorization_contract_designed",
    "admit_014_formal_evaluator_interface_contract_frozen",
    "admit_014_standalone_signature_frozen",
    "admit_014_formal_result_contract_frozen",
    "admit_014_result_representation_frozen",
    "admit_014_stage_authorization_routing_resolved",
    "admit_014_exact_bool_value_contract_frozen",
    "admit_014_permission_transition_and_precedence_resolved",
    "admit_014_reason_vocabulary_frozen",
    "admit_014_mandatory_pre_download_enforcement_contract_frozen",
    "admit_014_future_evaluator_pure_in_memory_possible",
    "ready_for_admit_014_standalone_evaluator_interface_implementation",
    "unified_dispatch_runtime_with_admit_001_to_013_implemented",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "evaluate_admit_014_implemented",
    "Admit014EvaluationResult_implemented",
    "admit_014_rule_logic_implemented",
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


def _readiness() -> dict[str, bool]:
    return {
        **{name: True for name in TRUE_READINESS},
        **{name: False for name in FALSE_READINESS},
    }


def _csv_bytes(
    columns: tuple[str, ...], rows: list[dict[str, str]]
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=columns,
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def build_artifacts(
    snapshot: tuple[_Source, ...] | None = None,
) -> dict[str, bytes]:
    _canonical_runtime_guard()
    frozen = build_frozen_source_snapshot() if snapshot is None else snapshot
    _verify_predecessors(frozen)
    contract_rows = _contract_rows()
    routing_rows = _routing_rows()
    truth_rows = _truth_rows()
    source_rows = _source_rows_for_artifact(frozen)
    issue_rows = _issue_rows(frozen)
    payloads = {
        CONTRACT_FILE: _csv_bytes(CONTRACT_COLUMNS, contract_rows),
        ROUTING_FILE: _csv_bytes(ROUTING_COLUMNS, routing_rows),
        TRUTH_FILE: _csv_bytes(TRUTH_COLUMNS, truth_rows),
        SOURCE_FILE: _csv_bytes(SOURCE_COLUMNS, source_rows),
        ISSUE_FILE: _csv_bytes(tuple(issue_rows[0]), issue_rows),
    }
    output_sha256 = {
        name: hashlib.sha256(content).hexdigest()
        for name, content in payloads.items()
    }
    group_counts = {
        group: sum(row["case_group"] == group for row in truth_rows)
        for group in dict.fromkeys(row["case_group"] for row in truth_rows)
    }
    readiness = _readiness()
    manifest: dict[str, Any] = {
        "project": PROJECT,
        "stage": STAGE,
        "manifest_schema_version": (
            "covapie_admit_014_formal_evaluator_interface_contract_manifest_v1"
        ),
        "base_commit": BASE_COMMIT,
        "base_parent": BASE_PARENT,
        "base_tree": BASE_TREE,
        "base_subject": BASE_SUBJECT,
        "canonical_evidence_python_implementation": (
            CANONICAL_PYTHON_IMPLEMENTATION
        ),
        "canonical_evidence_python_version": CANONICAL_PYTHON_VERSION,
        "ast_attestation_cross_python_version_portable": False,
        "noncanonical_python_policy": NONCANONICAL_PYTHON_POLICY,
        "python_runtime_migration_policy": PYTHON_RUNTIME_MIGRATION_POLICY,
        "admission_rule_id": ADMISSION_RULE_ID,
        "future_function_name": "evaluate_admit_014",
        "future_result_type_name": "Admit014EvaluationResult",
        "future_public_signature": FUTURE_PUBLIC_SIGNATURE,
        "signature_parameters": list(PARAMETERS),
        "signature_parameter_count": 1,
        "signature_all_keyword_only": True,
        "signature_parameter_annotation": "object",
        "signature_private_missing_singleton_default": True,
        "signature_varargs": False,
        "signature_varkw": False,
        "signature_forbidden_parameters": [
            "candidate_record",
            "batch_context",
            "evaluation_context",
            "download_result_context",
            "provider_result",
            "policy_mapping",
            "fallback_envelope",
        ],
        "formal_evaluator_implemented": False,
        "formal_result_type_defined": False,
        "design_oracle": (
            "classify_admit_014_formal_evaluator_interface_design"
        ),
        "design_result_type": "Admit014EvaluationResultContractDesign",
        "result_fields": list(RESULT_FIELDS),
        "result_field_count": 9,
        "result_field_exact_types": list(RESULT_FIELD_TYPES),
        "result_dataclass_frozen": True,
        "result_subclassing_forbidden": True,
        "canonical_stage_authorization_record_representation": {
            "empty": "()",
            "false": (
                "(('current_stage_download_authorized', False),)"
            ),
            "true": "(('current_stage_download_authorized', True),)",
            "outer_type": "exact tuple",
            "pair_type": "exact tuple",
            "value_type": "exact bool",
        },
        "validated_stage_authorization_fields_representation": [
            "()",
            "('current_stage_download_authorized',)",
        ],
        "consumed_stage_authorization_fields_representation": [
            "()",
            "('current_stage_download_authorized',)",
        ],
        "outcome_vocabulary": list(OUTCOME_VOCABULARY),
        "reason_vocabulary": list(REASON_VOCABULARY),
        "failure_precedence": list(PRECEDENCE),
        "result_invariants": [
            "admission_rule_id == ADMIT_014",
            "passed == (outcome == passed)",
            "blocks_candidate == (outcome == blocked)",
            "reason empty iff outcome passed",
            "blocked iff reason is one of six blocker reasons",
            "evaluator_io_used is exact false",
        ],
        "projection_contract": {
            "omitted": ["()", "()", "()"],
            "explicit_none": ["()", "()", "()"],
            "non_mapping": ["()", "()", "()"],
            "missing_key": [
                "()",
                "()",
                "('current_stage_download_authorized',)",
            ],
            "lookup_failure": [
                "()",
                "()",
                "('current_stage_download_authorized',)",
            ],
            "invalid_type": [
                "()",
                "()",
                "('current_stage_download_authorized',)",
            ],
            "exact_false": [
                "(('current_stage_download_authorized', False),)",
                "('current_stage_download_authorized',)",
                "('current_stage_download_authorized',)",
            ],
            "exact_true": [
                "(('current_stage_download_authorized', True),)",
                "('current_stage_download_authorized',)",
                "('current_stage_download_authorized',)",
            ],
        },
        "mapping_consumption_contract": {
            "target_key": AUTHORIZATION_CONTEXT_ITEM,
            "target_lookup_maximum_count": 1,
            "iteration_count": 0,
            "len_count": 0,
            "get_count": 0,
            "contains_count": 0,
            "extra_keys_allowed": True,
            "admit_015_coexistence_key": ADMIT_015_CONTEXT_ITEM,
            "admit_015_key_access_count": 0,
        },
        "truth_matrix_schema": list(TRUTH_COLUMNS),
        "truth_matrix_row_count": len(truth_rows),
        "truth_matrix_positive_row_count": 45,
        "truth_matrix_negative_result_row_count": len(
            NEGATIVE_RESULT_CASES
        ),
        "truth_matrix_group_counts": group_counts,
        "truth_matrix_signature_meta_semantics": {
            "row_count": 8,
            "property_rows": 6,
            "property_meta_outcome": "verified",
            "rejection_rows": 2,
            "rejection_meta_outcome": "rejected",
            "rejection_reason": "TypeError",
            "generated_by_real_signature_introspection_bind_and_invocation": True,
            "meta_outcomes_are_formal_evaluator_outcomes": False,
        },
        "truth_matrix_all_cases_passed": all(
            row["case_passed"] == "true" for row in truth_rows
        ),
        "precondition_transition": {
            "row_count": 51,
            "complete_count": 49,
            "incomplete_count": 2,
            "implementation_blocking_count": 2,
            "resolved_precondition_ids": [
                "PRE_039",
                "PRE_040",
                "PRE_041",
            ],
            "remaining_open_precondition_ids": ["PRE_048", "PRE_049"],
        },
        "issue_transition": {
            "row_count": 30,
            "inherited_exact23_count": 23,
            "admit_014_specific_issue_count": 7,
            "resolved_by_this_stage_count": 2,
            "resolved_issue_ids": list(ISSUE_TRANSITIONS),
            "remaining_open_admit_014_issue_count": 0,
            "coverage_issue_affected_rules": "ADMIT_014|ADMIT_015",
        },
        "remaining_open_issue_ids": list(GLOBAL_OPEN_ISSUES),
        "current_permission": False,
        "synthetic_true_design_case_grants_current_permission": False,
        "mandatory_pre_download_authorization_enforcement_contract": {
            "frozen": True,
            "implemented": False,
            "only_pass_may_continue": True,
            "combined_verdict_required": False,
        },
        "unified_adapter_contract_frozen": False,
        "unified_adapter_implemented": False,
        "admit_014_registered_in_engine": False,
        "unified_dispatch_runtime_with_admit_001_to_014_implemented": False,
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
        "source_validation_before_candidate_and_output_read": True,
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
        "output_sha256": output_sha256,
        "output_sha256_excludes_manifest_self_hash": True,
        "renameat2_policy": (
            "RENAME_NOREPLACE_required; GPFS_EINVAL_fails_closed; "
            "no_os_replace_fallback"
        ),
        "step12d_status": (
            "smoke_legality_only_not_final_training_feature_contract"
        ),
        "feature_semantics_note": (
            "historical UNKNOWN_ATOM_FEATURE_POLICY and "
            "feature_semantics_known=false require an explicit "
            "feature-semantics audit before training"
        ),
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "all_checks_passed": True,
    }
    manifest.update(readiness)
    payloads[MANIFEST_FILE] = (
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    ).encode()
    return {name: payloads[name] for name in OUTPUT_FILES}


def _write_exclusive_leaf(
    directory_fd: int, name: str, data: bytes
) -> None:
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
    destination_name = (
        destination if parent_fd is None else Path(destination.name)
    )
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
    if (
        stat.S_ISLNK(parent_lexical.st_mode)
        or not stat.S_ISDIR(parent_lexical.st_mode)
    ):
        raise ValueError("unsafe output parent")
    parent_identity = _identity(parent_lexical)
    parent_fd = os.open(parent, directory_flags)
    root_fd = -1
    leaves: list[tuple[str, int, Identity, bytes]] = []
    try:
        if _identity(os.fstat(parent_fd)) != parent_identity:
            raise ValueError("output parent stat/open race")
        root_lexical = os.stat(
            root.name, dir_fd=parent_fd, follow_symlinks=False
        )
        if (
            stat.S_ISLNK(root_lexical.st_mode)
            or not stat.S_ISDIR(root_lexical.st_mode)
        ):
            raise ValueError("unsafe output root")
        root_identity = _identity(root_lexical)
        if (
            expected_root_identity is not None
            and root_identity != expected_root_identity
        ):
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
                os.stat(
                    root.name, dir_fd=parent_fd, follow_symlinks=False
                )
            )
            != root_identity
            or _identity(os.fstat(parent_fd)) != parent_identity
            or _identity(os.lstat(parent)) != parent_identity
        ):
            raise ValueError(
                "output parent/root identity drift after traversal"
            )
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


def materialize_contract(
    output_root: Path | None = None,
) -> dict[str, Any]:
    """Build and atomically publish the deterministic Exact6 evidence."""
    _canonical_runtime_guard()
    root = (
        REPO_ROOT / DEFAULT_OUTPUT_ROOT
        if output_root is None
        else Path(output_root)
    )
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
    if (
        stat.S_ISLNK(parent_lexical.st_mode)
        or not stat.S_ISDIR(parent_lexical.st_mode)
    ):
        raise ValueError("unsafe output parent")
    parent_fd = os.open(parent, directory_flags)
    if _identity(os.fstat(parent_fd)) != _identity(parent_lexical):
        os.close(parent_fd)
        raise ValueError("output parent stat/open race")
    staging = Path(
        tempfile.mkdtemp(
            prefix=f".{root.name}.",
            suffix=".staging",
            dir=parent,
        )
    )
    staging_fd = -1
    published = False
    try:
        staging_lexical = os.stat(
            staging.name, dir_fd=parent_fd, follow_symlinks=False
        )
        staging_fd = os.open(
            staging.name, directory_flags, dir_fd=parent_fd
        )
        if _identity(os.fstat(staging_fd)) != _identity(staging_lexical):
            raise ValueError("staging root stat/open race")
        for name in OUTPUT_FILES:
            _write_exclusive_leaf(staging_fd, name, payloads[name])
        os.fsync(staging_fd)
        staging_identity = _identity(os.fstat(staging_fd))
        try:
            _rename_noreplace(staging, root, parent_fd)
        except OSError as error:
            if error.errno == errno.EEXIST and _read_output_set(
                root, payloads
            ):
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
                os.stat(
                    root.name, dir_fd=parent_fd, follow_symlinks=False
                )
            )
            != published_identity
        ):
            raise ValueError("destination name/inode binding mismatch")
        os.fsync(parent_fd)
        if (
            _identity(
                os.stat(
                    root.name, dir_fd=parent_fd, follow_symlinks=False
                )
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


def run_covapie_bulk_download_admission_admit_014_formal_evaluator_interface_contract_v1(
    output_root: Path | None = None,
) -> dict[str, Any]:
    """Explicitly materialize the contract; import has no side effect."""
    return materialize_contract(output_root)
