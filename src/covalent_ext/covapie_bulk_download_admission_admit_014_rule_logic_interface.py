"""Pure ADMIT_014 standalone evaluator and deterministic evidence builder."""

from collections.abc import Mapping
from dataclasses import dataclass, fields


ADMISSION_RULE_ID = "ADMIT_014"
AUTHORIZATION_CONTEXT_ITEM = "current_stage_download_authorized"
ADMIT_015_CONTEXT_ITEM = "current_stage_training_authorized"
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
BLOCKER_REASONS = frozenset(REASON_VOCABULARY[1:])


class _MissingAdmit014Value:
    __slots__ = ()


_MISSING = _MissingAdmit014Value()


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
class Admit014EvaluationResult:
    admission_rule_id: str
    outcome: str
    passed: bool
    blocks_candidate: bool
    reason: str
    canonical_stage_authorization_record: tuple
    validated_stage_authorization_fields: tuple[str, ...]
    consumed_stage_authorization_fields: tuple[str, ...]
    evaluator_io_used: bool

    def __post_init__(self) -> None:
        if type(self) is not Admit014EvaluationResult:
            raise TypeError("exact Admit014EvaluationResult required")
        if tuple(field.name for field in fields(type(self))) != RESULT_FIELDS:
            raise TypeError("exact result field order required")
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
        if (self.outcome == "blocked") is not (
            self.reason in BLOCKER_REASONS
        ):
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


def _make_result(
    outcome: str,
    reason: str,
    canonical: tuple[tuple[str, bool], ...],
    validated: tuple[str, ...],
    consumed: tuple[str, ...],
) -> Admit014EvaluationResult:
    return Admit014EvaluationResult(
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


def evaluate_admit_014(
    *,
    stage_authorization_context: object = _MISSING,
) -> Admit014EvaluationResult:
    """Evaluate the frozen ADMIT_014 stage-authorization rule in memory."""
    if (
        stage_authorization_context is _MISSING
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


# === ADMIT_014 FORMAL EVALUATOR CLOSURE END ===


import ast
import csv
import ctypes
import errno
import hashlib
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any


PROJECT = "CovaPIE"
STAGE = "covapie_bulk_download_admission_admit_014_rule_logic_interface_v1"
BASE_COMMIT = "0ec764f03bd3fe227a1e346380f1cdf31837f023"
BASE_PARENT = "d56140d8558208ee34eb5a43773010a2dc69169b"
BASE_TREE = "13c3d43310ec6eaa53004f92550e7184d1f67229"
BASE_SUBJECT = "add CovaPIE ADMIT_014 formal evaluator interface contract v1"
RECOMMENDED_NEXT_STEP = "design_covapie_admit_014_unified_adapter_contract_v1"
CANONICAL_PYTHON_IMPLEMENTATION = "cpython"
CANONICAL_PYTHON_VERSION = (3, 10, 4)
AST_ATTESTATION_CROSS_PYTHON_VERSION_PORTABLE = False
NONCANONICAL_PYTHON_POLICY = (
    "evaluator_semantic_smoke_only; artifact_build_checker_and_frozen_ast_forbidden"
)
PYTHON_RUNTIME_MIGRATION_POLICY = "explicit_contract_refresh_required"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
FORMAL_DESIGN_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_014_"
    "formal_evaluator_interface_contract_v1"
)
FORMAL_DESIGN_PRODUCTION = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_admit_014_"
    "formal_evaluator_interface_contract_design_gate.py"
)

CONTRACT_FILE = "covapie_admit_014_rule_logic_interface_contract.csv"
TRUTH_FILE = "covapie_admit_014_rule_logic_interface_truth_matrix.csv"
SOURCE_FILE = "covapie_admit_014_rule_logic_interface_source_boundary_audit.csv"
PURITY_FILE = "covapie_admit_014_rule_logic_interface_purity_audit.csv"
ISSUE_FILE = "covapie_admit_014_rule_logic_interface_issue_readiness_inventory.csv"
MANIFEST_FILE = "covapie_admit_014_rule_logic_interface_manifest.json"
OUTPUT_FILES = (
    CONTRACT_FILE,
    TRUTH_FILE,
    SOURCE_FILE,
    PURITY_FILE,
    ISSUE_FILE,
    MANIFEST_FILE,
)
FORMAL_MARKER = "# === ADMIT_014 FORMAL " + "EVALUATOR CLOSURE END ==="
FORMAL_CLOSURE = (
    "_MissingAdmit014Value",
    "_canonical_record_valid",
    "_field_tuple_valid",
    "Admit014EvaluationResult",
    "Admit014EvaluationResult.__post_init__",
    "_make_result",
    "evaluate_admit_014",
)
PUBLIC_SIGNATURE = (
    "evaluate_admit_014(*, stage_authorization_context: object = _MISSING) "
    "-> Admit014EvaluationResult"
)

CONTRACT_COLUMNS = (
    "contract_order",
    "contract_section",
    "section_order",
    "public_name",
    "formal_type",
    "required",
    "frozen_value",
    "formal_invariant",
    "implementation_source",
    "contract_passed",
)
TRUTH_COLUMNS = (
    "case_order",
    "case_id",
    "case_group",
    "assertion_kind",
    "inherited_case_id",
    "stage_context_representation",
    "expected_design_result",
    "observed_formal_result",
    "exact_type_value_equality",
    "evaluator_io_used",
    "formal_source",
    "truth_passed",
)
SOURCE_COLUMNS = (
    "source_order",
    "source_relative_path",
    "source_kind",
    "base_tree_mode",
    "expected_sha256",
    "base_tree_sha256",
    "filesystem_sha256",
    "frozen_snapshot_sha256",
    "git_tracked",
    "index_stage_zero",
    "base_tree_blob",
    "filesystem_regular",
    "non_symlink",
    "parent_chain_non_symlink",
    "safe_descendant",
    "pinned_fd_read",
    "post_read_identity_verified",
    "triple_sha256_passed",
    "source_boundary_passed",
)
PURITY_COLUMNS = (
    "audit_order",
    "audit_kind",
    "definition_name",
    "definition_kind",
    "reachable_from",
    "normalized_ast_sha256",
    "permitted_global_bindings",
    "permitted_calls",
    "observed",
    "forbidden_io_absent",
    "mutation_absent",
    "dynamic_dispatch_absent",
    "purity_passed",
)

SOURCE_SHA256 = {
    FORMAL_DESIGN_PRODUCTION: (
        "af25eb2f2fb84230b29d2204fff05308626e7f455a7b950aa8efb922607c298e"
    ),
    FORMAL_DESIGN_ROOT
    / "covapie_admit_014_formal_evaluator_interface_and_result_contract.csv": (
        "7baea79ce0010e31efcf2e70f11350ee5fc05a5c358df3926f9df591da3d3524"
    ),
    FORMAL_DESIGN_ROOT
    / "covapie_admit_014_formal_evaluator_routing_and_consumption_contract.csv": (
        "9df1faddeb8aa14e8b29af10296222925361cd1f1f98c05a2cc3a2cc64c7f769"
    ),
    FORMAL_DESIGN_ROOT
    / "covapie_admit_014_formal_evaluator_interface_truth_matrix.csv": (
        "55dbbddf1f3bcdb4bbd6ce763d7a0c812020241157098c6af18799cc5ffac062"
    ),
    FORMAL_DESIGN_ROOT
    / "covapie_admit_014_formal_evaluator_interface_issue_readiness_inventory.csv": (
        "d2510c9d2cf7ee1a1fc378e639eb69b68612e818f4e7af10a0e36dc0d788f54d"
    ),
    FORMAL_DESIGN_ROOT
    / "covapie_admit_014_formal_evaluator_interface_contract_manifest.json": (
        "217490ef69526486b51117e4900d0669b4de466a023023ecb56ebdf0822fb731"
    ),
    Path(
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_admit_014_"
        "download_authorization_contract_v1/"
        "covapie_admit_014_download_authorization_truth_matrix.csv"
    ): "e4f39f5178b91906639670f5c1ddb1c02b40c802de9ce386aee2a6b6d49f8482",
    Path(
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_admit_014_"
        "download_authorization_contract_v1/"
        "covapie_admit_014_download_authorization_contract_manifest.json"
    ): "9c54c9d6cb11776b04938d9be048699041bfc4020dca4c00425faadaaaa5d4d2",
    Path(
        "src/covalent_ext/"
        "covapie_bulk_download_admission_admit_013_rule_logic_interface.py"
    ): "36a4d3080128dadcecbdda25c5a3e143ac054aba001e7ac9cd7de0e2c51307f4",
    Path(
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_admit_013_rule_logic_interface_v1/"
        "covapie_admit_013_rule_logic_interface_manifest.json"
    ): "3ecbbc4d99966c955b39cad4dae65ef9c8316c7847bd43ccef82c44863cd4fa5",
    Path(
        "src/covalent_ext/"
        "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013.py"
    ): "79f95b6e178044ff5b4f5abbd6445b6cd848e81ba1a8a16cacdf831b05b9b892",
    Path(
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1/"
        "covapie_admit_001_to_013_runtime_manifest.json"
    ): "2940e6cc02a92b4919cdece3b1fa7c2f5e27d844f2962bb18757197266c23f79",
}
SOURCE_PATHS = tuple(SOURCE_SHA256)


Identity = tuple[int, int, int, int, int, int]


@dataclass(frozen=True)
class _Source:
    path: Path
    content: bytes
    sha256: str
    base_mode: str
    base_blob: str


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


class _TupleSubclass(tuple):
    pass


class _PairTupleSubclass(tuple):
    pass


class _ResultSubclass(Admit014EvaluationResult):
    pass


def _validate_canonical_evidence_runtime_identity(
    implementation_name: str,
    version: tuple[int, int, int],
) -> None:
    if (
        implementation_name != CANONICAL_PYTHON_IMPLEMENTATION
        or tuple(version) != CANONICAL_PYTHON_VERSION
    ):
        observed = ".".join(str(part) for part in version)
        raise RuntimeError(
            "canonical evidence runtime required: CPython 3.10.4; "
            f"observed implementation: {implementation_name}; "
            f"observed version: {observed}; frozen AST evidence is "
            "version-sensitive; noncanonical Python may only be used for "
            "evaluator-only semantic smoke"
        )


def _assert_canonical_evidence_runtime() -> None:
    _validate_canonical_evidence_runtime_identity(
        sys.implementation.name,
        tuple(sys.version_info[:3]),
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


def _identity(item: os.stat_result) -> Identity:
    return (
        item.st_dev,
        item.st_ino,
        item.st_mode,
        item.st_size,
        item.st_mtime_ns,
        item.st_ctime_ns,
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
    if stat.S_ISLNK(root_before.st_mode) or not stat.S_ISDIR(
        root_before.st_mode
    ):
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
            if stat.S_ISLNK(lexical.st_mode) or not stat.S_ISDIR(
                lexical.st_mode
            ):
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
            chunks = []
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
                    raise ValueError(
                        f"source parent lexical replacement: {path}"
                    )
        if _identity(os.lstat(REPO_ROOT)) != root_identity:
            raise ValueError("repository root identity drift")
        return b"".join(chunks)
    finally:
        for descriptor, _, _, _ in reversed(descriptors):
            os.close(descriptor)


def build_frozen_source_snapshot() -> tuple[_Source, ...]:
    _assert_canonical_evidence_runtime()
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
    if len(SOURCE_PATHS) != 12 or len(set(SOURCE_PATHS)) != 12:
        raise ValueError("source boundary must be ordered Exact12")
    preflight = []
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
            or len(tree_fields[2]) != 40
            or any(
                character not in "0123456789abcdef"
                for character in tree_fields[2]
            )
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
    matches = [record for record in snapshot if record.path == path]
    if len(matches) != 1:
        raise ValueError(f"source lookup not unique: {path}")
    return matches[0]


def _source_csv(
    snapshot: tuple[_Source, ...], path: Path
) -> list[dict[str, str]]:
    return list(
        csv.DictReader(
            io.StringIO(_source(snapshot, path).content.decode(), newline="")
        )
    )


def _source_json(
    snapshot: tuple[_Source, ...], path: Path
) -> dict[str, Any]:
    value = json.loads(_source(snapshot, path).content)
    if type(value) is not dict:
        raise ValueError("JSON object required")
    return value


def _validate_predecessors(snapshot: tuple[_Source, ...]) -> None:
    formal = _source_json(
        snapshot,
        FORMAL_DESIGN_ROOT
        / "covapie_admit_014_formal_evaluator_interface_contract_manifest.json",
    )
    authorization_path = next(
        path
        for path in SOURCE_PATHS
        if path.name
        == "covapie_admit_014_download_authorization_contract_manifest.json"
    )
    authorization = _source_json(snapshot, authorization_path)
    admit013_path = next(
        path
        for path in SOURCE_PATHS
        if path.name == "covapie_admit_013_rule_logic_interface_manifest.json"
    )
    admit013 = _source_json(snapshot, admit013_path)
    runtime_path = next(
        path
        for path in SOURCE_PATHS
        if path.name == "covapie_admit_001_to_013_runtime_manifest.json"
    )
    runtime = _source_json(snapshot, runtime_path)
    if not (
        formal["base_commit"] == BASE_PARENT
        and formal["future_function_name"] == "evaluate_admit_014"
        and formal["future_result_type_name"] == "Admit014EvaluationResult"
        and formal["result_fields"] == list(RESULT_FIELDS)
        and formal["truth_matrix_row_count"] == 69
        and formal["precondition_transition"]["complete_count"] == 49
        and formal["precondition_transition"]["incomplete_count"] == 2
        and authorization["current_permission"] is False
        and authorization["ready_for_bulk_download_now"] is False
        and admit013["admit_013_standalone_evaluator_interface_implemented"]
        is True
        and runtime["registered_rule_ids"]
        == [f"ADMIT_{index:03d}" for index in range(1, 14)]
        and runtime["known_not_registered_rule_ids"]
        == ["ADMIT_014", "ADMIT_015"]
        and runtime["admit_014_registered_in_engine"] is False
        and runtime["combined_candidate_verdict_implemented"] is False
        and runtime["cross_rule_aggregation_implemented"] is False
        and runtime["provider_mapping_validated"] is False
        and runtime["ready_for_bulk_download_now"] is False
    ):
        raise ValueError("ADMIT_014 predecessor lineage drift")


def _load_design_oracle(snapshot: tuple[_Source, ...]) -> Any:
    source = _source(snapshot, FORMAL_DESIGN_PRODUCTION)
    if source.sha256 != SOURCE_SHA256[FORMAL_DESIGN_PRODUCTION]:
        raise ValueError("design oracle source not frozen")
    module_name = "_covapie_admit014_committed_design_oracle"
    spec = importlib.util.spec_from_file_location(
        module_name, REPO_ROOT / FORMAL_DESIGN_PRODUCTION
    )
    if spec is None or spec.loader is None:
        raise ValueError("isolated design oracle import unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(module_name, None)
    return module


def _formal_source_attestation() -> tuple[bytes, str, str, dict[str, str]]:
    _assert_canonical_evidence_runtime()
    relative = Path(
        "src/covalent_ext/"
        "covapie_bulk_download_admission_admit_014_rule_logic_interface.py"
    )
    item = os.lstat(REPO_ROOT / relative)
    if stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode):
        raise ValueError("unsafe formal production source")
    source = _pinned_read_relative(relative)
    text = source.decode()
    if text.count(FORMAL_MARKER) != 1:
        raise ValueError("formal closure marker drift")
    prefix = text.split(FORMAL_MARKER, 1)[0].encode()
    tree = ast.parse(prefix)
    definitions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    }
    if set(definitions) != {
        "_MissingAdmit014Value",
        "_canonical_record_valid",
        "_field_tuple_valid",
        "Admit014EvaluationResult",
        "_make_result",
        "evaluate_admit_014",
    }:
        raise ValueError("formal closure definition set drift")
    result_class = definitions["Admit014EvaluationResult"]
    post = next(
        node
        for node in result_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "__post_init__"
    )
    nodes = {
        name: post if name.endswith(".__post_init__") else definitions[name]
        for name in FORMAL_CLOSURE
    }
    forbidden_names = {
        "open",
        "eval",
        "exec",
        "getattr",
        "globals",
        "locals",
        "__import__",
        "os",
        "Path",
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "tempfile",
        "json",
        "csv",
        "hashlib",
        "importlib",
        "provider",
        "download",
        "raw",
        "registry",
        "dispatcher",
        "training",
    }
    for name, node in nodes.items():
        if any(
            isinstance(item, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal))
            for item in ast.walk(node)
        ):
            raise ValueError(f"formal purity statement forbidden: {name}")
        if any(
            isinstance(item, ast.Name) and item.id in forbidden_names
            for item in ast.walk(node)
        ):
            raise ValueError(f"formal purity binding forbidden: {name}")
        if any(
            isinstance(item, ast.Attribute)
            and item.attr in {"open", "read", "write", "fsync", "replace"}
            for item in ast.walk(node)
        ):
            raise ValueError(f"formal I/O attribute forbidden: {name}")
    digests = {
        name: hashlib.sha256(
            ast.dump(
                node, annotate_fields=True, include_attributes=False
            ).encode()
        ).hexdigest()
        for name, node in nodes.items()
    }
    return (
        source,
        hashlib.sha256(source).hexdigest(),
        hashlib.sha256(prefix).hexdigest(),
        digests,
    )


def _result_values(value: object) -> tuple[object, ...]:
    return tuple(getattr(value, name) for name in RESULT_FIELDS)


def _build_case_context(case_id: str) -> object:
    invalid = {
        "INT_ZERO": 0,
        "INT_ONE": 1,
        "FLOAT_ZERO": 0.0,
        "FLOAT_ONE": 1.0,
        "STRING_FALSE": "false",
        "STRING_TRUE": "true",
        "NONE_VALUE": None,
        "LIST_VALUE": [],
        "DICT_VALUE": {},
        "CUSTOM_TRUTHY": _Truthy(),
        "CUSTOM_FALSY": _Falsy(),
    }
    if case_id in {"OMITTED", "PROJECTION_OMITTED"}:
        return _MISSING
    if case_id == "EXPLICIT_NONE":
        return None
    if case_id == "CONTEXT_OBJECT":
        return object()
    if case_id == "CONTEXT_INT":
        return 7
    if case_id == "CONTEXT_STR":
        return "x"
    if case_id == "CONTEXT_LIST":
        return []
    if case_id in {
        "EMPTY_MAPPING",
        "PROJECTION_MISSING_KEY",
    }:
        return _InstrumentedMapping()
    if case_id == "UNRELATED_ONLY_MAPPING":
        return _InstrumentedMapping({"other": True})
    if case_id == "LOOKUP_KEYERROR":
        return _InstrumentedMapping(
            lookup_error=KeyError(AUTHORIZATION_CONTEXT_ITEM)
        )
    if case_id in {"LOOKUP_RUNTIMEERROR", "PROJECTION_LOOKUP_FAILED"}:
        return _InstrumentedMapping(lookup_error=RuntimeError("boom"))
    if case_id == "LOOKUP_VALUEERROR":
        return _InstrumentedMapping(lookup_error=ValueError("boom"))
    if case_id in invalid:
        return _InstrumentedMapping(
            {AUTHORIZATION_CONTEXT_ITEM: invalid[case_id]}
        )
    if case_id == "PROJECTION_INVALID_TYPE":
        return _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: "true"})
    if case_id in {"EXACT_FALSE", "PROJECTION_FALSE"}:
        return _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: False})
    if case_id in {"EXACT_TRUE", "PROJECTION_TRUE"}:
        return _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: True})
    if case_id == "ADMIT015_PLUS_TRUE":
        return _InstrumentedMapping(
            {
                ADMIT_015_CONTEXT_ITEM: False,
                AUTHORIZATION_CONTEXT_ITEM: True,
            }
        )
    if case_id == "ADMIT015_PLUS_FALSE":
        return _InstrumentedMapping(
            {
                ADMIT_015_CONTEXT_ITEM: True,
                AUTHORIZATION_CONTEXT_ITEM: False,
            }
        )
    if case_id == "MANY_EXTRA_PLUS_TRUE":
        return _InstrumentedMapping(
            {
                **{f"extra_{index}": object() for index in range(20)},
                AUTHORIZATION_CONTEXT_ITEM: True,
            }
        )
    if case_id in {
        "ITERATION_RAISES",
        "LEN_RAISES",
        "GET_RAISES",
        "CONTAINS_RAISES",
    }:
        return _InstrumentedMapping({AUTHORIZATION_CONTEXT_ITEM: True})
    raise ValueError(f"unknown executable truth case: {case_id}")


def _mapping_access_valid(value: object) -> bool:
    return not isinstance(value, _InstrumentedMapping) or (
        value.item_keys == [AUTHORIZATION_CONTEXT_ITEM]
        and value.iteration_count == 0
        and value.len_count == 0
        and value.get_count == 0
        and value.contains_count == 0
    )


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


def _reject_negative_result(case_id: str) -> str:
    baseline = evaluate_admit_014(
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
        Admit014EvaluationResult(*(values[name] for name in RESULT_FIELDS))
    except (TypeError, ValueError) as error:
        return f"RESULT_CONTRACT_REJECTED:{type(error).__name__}"
    raise ValueError(f"negative result case accepted: {case_id}")


def _truth_rows(
    snapshot: tuple[_Source, ...], design: Any
) -> list[dict[str, str]]:
    predecessor = _source_csv(
        snapshot,
        FORMAL_DESIGN_ROOT
        / "covapie_admit_014_formal_evaluator_interface_truth_matrix.csv",
    )
    inherited = [
        row for row in predecessor if row["case_group"] != "signature"
    ]
    if len(predecessor) != 69 or len(inherited) != 61:
        raise ValueError("committed formal truth Exact69/Exact61 drift")
    rows = []
    executable = 0
    negative = 0
    for order, prior in enumerate(inherited, 1):
        case_id = prior["case_id"]
        if prior["case_group"] == "negative_result_contract":
            observed = _reject_negative_result(case_id)
            expected = prior["observed_reason"]
            equal = (
                case_id in NEGATIVE_RESULT_CASES
                and observed == expected
                and observed.startswith("RESULT_CONTRACT_REJECTED:")
            )
            negative += 1
            assertion = "actual_result_malformed_direct_construction_rejected"
        else:
            actual_context = _build_case_context(case_id)
            design_context = _build_case_context(case_id)
            actual_kwargs = (
                {}
                if actual_context is _MISSING
                else {"stage_authorization_context": actual_context}
            )
            design_kwargs = (
                {}
                if design_context is _MISSING
                else {"stage_authorization_context": design_context}
            )
            design_result = (
                design.classify_admit_014_formal_evaluator_interface_design(
                    **design_kwargs
                )
            )
            actual_result = evaluate_admit_014(**actual_kwargs)
            expected_values = tuple(
                getattr(design_result, name) for name in RESULT_FIELDS
            )
            actual_values = _result_values(actual_result)
            equal = (
                type(actual_result) is Admit014EvaluationResult
                and type(design_result)
                is design.Admit014EvaluationResultContractDesign
                and actual_values == expected_values
                and all(
                    type(left) is type(right)
                    for left, right in zip(
                        actual_values, expected_values, strict=True
                    )
                )
                and actual_result.evaluator_io_used is False
                and design_result.evaluator_io_used is False
                and _mapping_access_valid(actual_context)
                and _mapping_access_valid(design_context)
            )
            observed = repr(actual_values)
            expected = repr(expected_values)
            executable += 1
            assertion = "actual_evaluator_design_oracle_exact9_projection"
        rows.append(
            {
                "case_order": str(order),
                "case_id": case_id,
                "case_group": prior["case_group"],
                "assertion_kind": assertion,
                "inherited_case_id": case_id,
                "stage_context_representation": prior[
                    "stage_context_representation"
                ],
                "expected_design_result": expected,
                "observed_formal_result": observed,
                "exact_type_value_equality": str(equal).lower(),
                "evaluator_io_used": "false",
                "formal_source": (
                    "evaluate_admit_014|Admit014EvaluationResult"
                ),
                "truth_passed": str(equal).lower(),
            }
        )
    if (
        executable != 37
        or negative != 24
        or not all(row["truth_passed"] == "true" for row in rows)
    ):
        raise ValueError("actual Exact37/Exact24 truth projection drift")
    return rows


def _contract_rows(
    ast_digests: dict[str, str]
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def add(
        section: str,
        name: str,
        formal_type: str,
        required: bool,
        value: str,
        invariant: str,
    ) -> None:
        rows.append(
            {
                "contract_order": str(len(rows) + 1),
                "contract_section": section,
                "section_order": str(
                    1
                    + sum(
                        row["contract_section"] == section for row in rows
                    )
                ),
                "public_name": name,
                "formal_type": formal_type,
                "required": str(required).lower(),
                "frozen_value": value,
                "formal_invariant": invariant,
                "implementation_source": "formal_closure",
                "contract_passed": "true",
            }
        )

    add(
        "signature_parameter",
        "stage_authorization_context",
        "object",
        False,
        "keyword_only|private_missing_singleton",
        "one parameter; no positional/varargs/varkw/unknown keyword",
    )
    result_types = (
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
    for name, formal_type in zip(
        RESULT_FIELDS, result_types, strict=True
    ):
        add(
            "result_field",
            name,
            formal_type,
            True,
            "Exact9_ordered",
            "exact built-in top-level type and reason-state invariant",
        )
    for reason in REASON_VOCABULARY:
        add(
            "reason_vocabulary",
            reason or "<empty>",
            "str",
            True,
            reason,
            "closed Exact7 ordered vocabulary",
        )
    for name in FORMAL_CLOSURE:
        add(
            "formal_closure",
            name,
            "normalized_ast_sha256",
            True,
            ast_digests[name],
            "pure in-memory reachable definition",
        )
    for name, invariant in (
        ("exact_result_type", "type(self) is Admit014EvaluationResult"),
        ("exact_result_storage", "dataclass fields equal RESULT_FIELDS"),
        ("exact_top_level_types", "exact str/bool/tuple only"),
        ("identity", "admission_rule_id == ADMIT_014"),
        ("outcome", "closed passed|blocked"),
        ("reason", "closed Exact7"),
        ("flags", "passed/blocks agree with outcome"),
        ("reason_emptiness", "reason empty iff passed"),
        ("evaluator_io", "evaluator_io_used is exact False"),
        (
            "projection",
            "canonical/validated/consumed agree with reason",
        ),
    ):
        add(
            "result_invariant",
            name,
            "invariant",
            True,
            invariant,
            "fail closed",
        )
    for name in (
        "no_adapter_registry_runtime",
        "no_provider_network_download_raw",
        "no_model_checkpoint_dataloader_training",
    ):
        add(
            "safety_boundary",
            name,
            "boolean",
            True,
            "true",
            "absence attested",
        )
    return rows


def _source_rows(
    snapshot: tuple[_Source, ...]
) -> list[dict[str, str]]:
    return [
        {
            "source_order": str(index),
            "source_relative_path": record.path.as_posix(),
            "source_kind": (
                "python_source"
                if record.path.suffix == ".py"
                else "committed_csv"
                if record.path.suffix == ".csv"
                else "committed_manifest"
            ),
            "base_tree_mode": record.base_mode,
            "expected_sha256": record.sha256,
            "base_tree_sha256": record.sha256,
            "filesystem_sha256": record.sha256,
            "frozen_snapshot_sha256": record.sha256,
            "git_tracked": "true",
            "index_stage_zero": "true",
            "base_tree_blob": record.base_blob,
            "filesystem_regular": "true",
            "non_symlink": "true",
            "parent_chain_non_symlink": "true",
            "safe_descendant": "true",
            "pinned_fd_read": "true",
            "post_read_identity_verified": "true",
            "triple_sha256_passed": "true",
            "source_boundary_passed": "true",
        }
        for index, record in enumerate(snapshot, 1)
    ]


def _purity_rows(
    full_sha: str, prefix_sha: str, digests: dict[str, str]
) -> list[dict[str, str]]:
    parents = (
        "evaluate_admit_014|signature_default",
        "Admit014EvaluationResult.__post_init__",
        "Admit014EvaluationResult.__post_init__",
        "_make_result|root",
        "Admit014EvaluationResult",
        "evaluate_admit_014",
        "root",
    )
    kinds = (
        "private_sentinel_class",
        "function",
        "function",
        "frozen_dataclass",
        "method",
        "function",
        "function",
    )
    rows = []
    for index, name in enumerate(FORMAL_CLOSURE):
        rows.append(
            {
                "audit_order": str(index + 1),
                "audit_kind": "closure_definition",
                "definition_name": name,
                "definition_kind": kinds[index],
                "reachable_from": parents[index],
                "normalized_ast_sha256": digests[name],
                "permitted_global_bindings": (
                    "immutable_formal_constants|Mapping|dataclass|fields|"
                    "pure_helpers"
                ),
                "permitted_calls": (
                    "exact_builtins|isinstance|formal_helpers|"
                    "Admit014EvaluationResult"
                ),
                "observed": "reachable_and_frozen",
                "forbidden_io_absent": "true",
                "mutation_absent": "true",
                "dynamic_dispatch_absent": "true",
                "purity_passed": "true",
            }
        )
    metadata = (
        ("production_full_sha256", full_sha),
        ("marker_prefix_sha256", prefix_sha),
        ("closure_complete", "|".join(FORMAL_CLOSURE)),
        (
            "reachable_global_bindings",
            "immutable constants|Mapping|dataclass|fields|formal helpers",
        ),
        (
            "forbidden_io",
            "os|pathlib|subprocess|tempfile|json|csv|hashlib|importlib|"
            "environment|socket|requests|urllib|provider|download|raw absent",
        ),
        (
            "forbidden_runtime",
            "evidence_builder|materializer|registry|dispatcher|model|"
            "training absent",
        ),
        (
            "forbidden_dynamic_dispatch",
            "dynamic_import|eval|exec|getattr|globals|locals absent",
        ),
        ("mutable_global_state", "absent"),
        ("purity_closure_complete", "true"),
    )
    for name, observed in metadata:
        rows.append(
            {
                "audit_order": str(len(rows) + 1),
                "audit_kind": "closure_metadata",
                "definition_name": name,
                "definition_kind": "attestation",
                "reachable_from": "checker_recomputed",
                "normalized_ast_sha256": "",
                "permitted_global_bindings": "",
                "permitted_calls": "",
                "observed": observed,
                "forbidden_io_absent": "true",
                "mutation_absent": "true",
                "dynamic_dispatch_absent": "true",
                "purity_passed": "true",
            }
        )
    return rows


TRUE_READINESS = (
    "admit_014_preconditions_audited",
    "admit_014_download_authorization_contract_designed",
    "admit_014_formal_evaluator_interface_contract_frozen",
    "admit_014_standalone_signature_frozen",
    "admit_014_formal_result_contract_frozen",
    "admit_014_result_representation_frozen",
    "admit_014_standalone_evaluator_interface_implemented",
    "evaluate_admit_014_implemented",
    "Admit014EvaluationResult_implemented",
    "admit_014_rule_logic_implemented",
    "admit_014_future_evaluator_pure_in_memory_possible",
    "ready_for_admit_014_unified_adapter_contract_design",
    "unified_dispatch_runtime_with_admit_001_to_013_implemented",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
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


def _csv_bytes(
    columns: tuple[str, ...], rows: list[dict[str, str]]
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=columns,
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def build_artifacts(
    snapshot: tuple[_Source, ...] | None = None,
) -> dict[str, bytes]:
    _assert_canonical_evidence_runtime()
    frozen = build_frozen_source_snapshot() if snapshot is None else snapshot
    _validate_predecessors(frozen)
    design = _load_design_oracle(frozen)
    formal_source, full_sha, prefix_sha, ast_digests = (
        _formal_source_attestation()
    )
    if not formal_source:
        raise ValueError("formal source attestation failed")
    contract_rows = _contract_rows(ast_digests)
    truth_rows = _truth_rows(frozen, design)
    source_rows = _source_rows(frozen)
    purity_rows = _purity_rows(full_sha, prefix_sha, ast_digests)
    issue_source = _source(
        frozen,
        FORMAL_DESIGN_ROOT
        / "covapie_admit_014_formal_evaluator_interface_issue_readiness_inventory.csv",
    )
    issue_rows = list(
        csv.DictReader(io.StringIO(issue_source.content.decode()))
    )
    by_id = {row["issue_id"]: row for row in issue_rows}
    required_open = (
        "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
        "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
        "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
        "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
    )
    if not (
        len(issue_rows) == 30
        and all(
            row["successor_effective_status"] == "resolved"
            for row in issue_rows[23:]
        )
        and all(
            by_id[name]["successor_effective_status"] == "open"
            for name in required_open
        )
        and by_id["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"][
            "affected_rules"
        ]
        == "ADMIT_014|ADMIT_015"
    ):
        raise ValueError("Exact30 issue continuity drift")
    payloads = {
        CONTRACT_FILE: _csv_bytes(CONTRACT_COLUMNS, contract_rows),
        TRUTH_FILE: _csv_bytes(TRUTH_COLUMNS, truth_rows),
        SOURCE_FILE: _csv_bytes(SOURCE_COLUMNS, source_rows),
        PURITY_FILE: _csv_bytes(PURITY_COLUMNS, purity_rows),
        ISSUE_FILE: issue_source.content,
    }
    readiness = {
        **{name: True for name in TRUE_READINESS},
        **{name: False for name in FALSE_READINESS},
    }
    manifest = {
        "manifest_schema_version": (
            "covapie_admit_014_rule_logic_interface_manifest_v1"
        ),
        "project": PROJECT,
        "stage": STAGE,
        "base_commit": BASE_COMMIT,
        "base_parent": BASE_PARENT,
        "base_tree": BASE_TREE,
        "base_subject": BASE_SUBJECT,
        "admission_rule_id": ADMISSION_RULE_ID,
        "public_evaluator": "evaluate_admit_014",
        "public_signature": PUBLIC_SIGNATURE,
        "parameter_order": ["stage_authorization_context"],
        "parameter_count": 1,
        "private_missing_singleton": True,
        "result_type": "Admit014EvaluationResult",
        "result_fields": list(RESULT_FIELDS),
        "result_field_count": 9,
        "result_field_exact_types": [
            "str",
            "str",
            "bool",
            "bool",
            "str",
            "tuple",
            "tuple",
            "tuple",
            "bool",
        ],
        "outcome_vocabulary": list(OUTCOME_VOCABULARY),
        "reason_vocabulary": list(REASON_VOCABULARY),
        "formal_evaluator_implemented": True,
        "formal_result_type_defined": True,
        "formal_production_sha256": full_sha,
        "formal_marker_prefix_sha256": prefix_sha,
        "formal_marker": FORMAL_MARKER,
        "formal_closure": list(FORMAL_CLOSURE),
        "formal_closure_count": len(FORMAL_CLOSURE),
        "formal_ast_sha256": ast_digests,
        "canonical_evidence_python_implementation": (
            CANONICAL_PYTHON_IMPLEMENTATION
        ),
        "canonical_evidence_python_version": "3.10.4",
        "ast_attestation_cross_python_version_portable": False,
        "noncanonical_python_policy": NONCANONICAL_PYTHON_POLICY,
        "python_runtime_migration_policy": PYTHON_RUNTIME_MIGRATION_POLICY,
        "mapping_consumption_contract": {
            "target_key": AUTHORIZATION_CONTEXT_ITEM,
            "target_lookup_exact_count_for_mappings": 1,
            "iteration_count": 0,
            "len_count": 0,
            "get_count": 0,
            "contains_count": 0,
            "admit_015_key_access_count": 0,
            "extra_keys_allowed": True,
        },
        "source_count": len(frozen),
        "source_boundary": [
            {
                "path": record.path.as_posix(),
                "sha256": record.sha256,
                "base_tree_mode": record.base_mode,
                "base_tree_blob": record.base_blob,
            }
            for record in frozen
        ],
        "source_validation_before_candidate_and_output_read": True,
        "row_counts": {
            "formal_contract": len(contract_rows),
            "truth_matrix": len(truth_rows),
            "actual_evaluator_design_projection": 37,
            "actual_result_negative_projection": 24,
            "source_boundary": len(source_rows),
            "purity_audit": len(purity_rows),
            "issue_inventory": len(issue_rows),
        },
        "actual_evaluator_design_oracle_projection_passed": 37,
        "actual_result_negative_projection_rejected": 24,
        "truth_matrix_passed": 61,
        "purity_closure_complete": True,
        "issue_transition_count": 0,
        "issue_inventory_byte_identical_to_formal_interface": True,
        "coverage_affected_rules": "ADMIT_014|ADMIT_015",
        "remaining_open_issue_ids": list(required_open),
        "precondition_transition": {
            "row_count": 51,
            "complete_count": 49,
            "incomplete_count": 2,
            "implementation_blocking_count": 2,
            "remaining_open_precondition_ids": ["PRE_048", "PRE_049"],
        },
        "readiness": readiness,
        **readiness,
        "current_permission": False,
        "authorized_admit_014_download_execution_count": 0,
        "adapter_registry_runtime_changed": False,
        "mandatory_pre_download_authorization_enforcement_implemented": False,
        "safety": {
            "provider": False,
            "network": False,
            "download": False,
            "raw_read_or_write": False,
            "model_or_checkpoint": False,
            "dataloader": False,
            "training_or_parameter_update": False,
            "combined_candidate_verdict": False,
            "cross_rule_aggregation": False,
            "stage_commit_push": False,
        },
        "output_files": list(OUTPUT_FILES),
        "output_file_count": 6,
        "materialization_policy": {
            "build_before_mutation": True,
            "exact_output_inventory": True,
            "o_excl_staging_leaves": True,
            "leaf_and_directory_fsync": True,
            "rename_noreplace_required": True,
            "gpfs_einval_fails_closed": True,
            "os_replace_fallback": False,
            "root_fd_no_follow": True,
            "leaf_open_dir_fd": True,
            "inode_preserving_exact_set_noop": True,
            "parent_fd_pinned": True,
            "staging_fd_pinned": True,
            "rename_relative_to_parent_fd": True,
            "destination_name_inode_binding": True,
            "post_fsync_destination_binding": True,
            "complete_exact6_post_read": True,
        },
        "output_sha256": {
            name: hashlib.sha256(content).hexdigest()
            for name, content in payloads.items()
        },
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "step12d_status": (
            "smoke_legality_only_not_final_training_feature_contract"
        ),
        "feature_semantics_audit_requirement": (
            "required_before_training; historical UNKNOWN_ATOM_FEATURE_POLICY "
            "and feature_semantics_known=False require audit"
        ),
        "all_checks_passed": True,
    }
    payloads[MANIFEST_FILE] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode()
    return {name: payloads[name] for name in OUTPUT_FILES}


def _rename_noreplace(
    source_name: str,
    destination_name: str,
    parent_fd: int,
) -> None:
    if os.uname().machine not in {"x86_64", "amd64"}:
        raise ValueError("renameat2 syscall number unavailable")
    result = ctypes.CDLL(None, use_errno=True).syscall(
        316,
        parent_fd,
        os.fsencode(source_name),
        parent_fd,
        os.fsencode(destination_name),
        1,
    )
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), destination_name)


def _write_exclusive_leaf(
    staging_fd: int,
    name: str,
    data: bytes,
) -> None:
    descriptor = os.open(
        name,
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0),
        0o644,
        dir_fd=staging_fd,
    )
    try:
        view = memoryview(data)
        while view:
            view = view[os.write(descriptor, view) :]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _make_staging_directory(parent_fd: int, root_name: str) -> str:
    for candidate in tempfile._get_candidate_names():
        name = f".{root_name}.{candidate}.staging"
        try:
            os.mkdir(name, 0o700, dir_fd=parent_fd)
        except FileExistsError:
            continue
        return name
    raise FileExistsError("unique staging directory unavailable")


def _read_output_descriptor(descriptor: int) -> bytes:
    chunks = []
    while True:
        chunk = os.read(descriptor, 1024 * 1024)
        if not chunk:
            break
        chunks.append(chunk)
    return b"".join(chunks)


def _read_exact_output_set(
    root: Path,
    payloads: dict[str, bytes],
    *,
    parent_fd: int | None = None,
    expected_parent_identity: Identity | None = None,
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
    lexical_parent_identity = _identity(parent_lexical)
    if (
        expected_parent_identity is not None
        and lexical_parent_identity[:3] != expected_parent_identity[:3]
    ):
        raise ValueError("output parent lexical identity mismatch")
    owns_parent_fd = parent_fd is None
    if parent_fd is None:
        parent_fd = os.open(parent, directory_flags)
    root_fd = -1
    leaves: list[tuple[str, int, Identity, bytes]] = []
    try:
        if _identity(os.fstat(parent_fd)) != lexical_parent_identity:
            raise ValueError("output parent stat/open race")
        root_item = os.stat(
            root.name, dir_fd=parent_fd, follow_symlinks=False
        )
        root_identity = _identity(root_item)
        if (
            stat.S_ISLNK(root_item.st_mode)
            or not stat.S_ISDIR(root_item.st_mode)
        ):
            raise ValueError("unsafe output root")
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
            item = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            if (
                stat.S_ISLNK(item.st_mode)
                or not stat.S_ISREG(item.st_mode)
                or item.st_size > 100 * 1024 * 1024
            ):
                raise ValueError("unsafe output leaf")
            identity = _identity(item)
            descriptor = os.open(name, leaf_flags, dir_fd=root_fd)
            if _identity(os.fstat(descriptor)) != identity:
                os.close(descriptor)
                raise ValueError("output leaf stat/open race")
            try:
                data = _read_output_descriptor(descriptor)
            except BaseException:
                os.close(descriptor)
                raise
            leaves.append(
                (
                    name,
                    descriptor,
                    identity,
                    data,
                )
            )
        if set(os.listdir(root_fd)) != set(OUTPUT_FILES):
            raise ValueError("output inventory drift after traversal")
        matches = True
        for name, descriptor, identity, data in leaves:
            if (
                _identity(os.fstat(descriptor)) != identity
                or _identity(
                    os.stat(name, dir_fd=root_fd, follow_symlinks=False)
                )
                != identity
            ):
                raise ValueError("output leaf identity drift after traversal")
            if data != payloads[name]:
                matches = False
        if (
            _identity(os.fstat(root_fd)) != root_identity
            or _identity(
                os.stat(
                    root.name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
            )
            != root_identity
            or _identity(os.fstat(parent_fd)) != lexical_parent_identity
            or _identity(os.lstat(parent)) != lexical_parent_identity
        ):
            raise ValueError("output parent/root identity drift")
        return matches
    finally:
        for _, descriptor, _, _ in leaves:
            os.close(descriptor)
        if root_fd >= 0:
            os.close(root_fd)
        if owns_parent_fd:
            os.close(parent_fd)


def _cleanup_owned_staging(
    parent_fd: int,
    staging_name: str,
    expected_identity: Identity,
) -> None:
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        lexical = os.stat(
            staging_name, dir_fd=parent_fd, follow_symlinks=False
        )
    except FileNotFoundError:
        raise ValueError("owned staging name disappeared")
    if (
        _identity(lexical)[:3] != expected_identity[:3]
        or stat.S_ISLNK(lexical.st_mode)
        or not stat.S_ISDIR(lexical.st_mode)
    ):
        raise ValueError("owned staging lexical binding drift")
    staging_fd = os.open(staging_name, directory_flags, dir_fd=parent_fd)
    try:
        if _identity(os.fstat(staging_fd))[:3] != expected_identity[:3]:
            raise ValueError("owned staging stat/open race")
        names = set(os.listdir(staging_fd))
        if names - set(OUTPUT_FILES):
            raise ValueError("owned staging inventory drift")
        for name in names:
            item = os.stat(name, dir_fd=staging_fd, follow_symlinks=False)
            if stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode):
                raise ValueError("unsafe owned staging leaf")
        for name in names:
            os.unlink(name, dir_fd=staging_fd)
        os.fsync(staging_fd)
        if (
            _identity(
                os.stat(
                    staging_name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
            )[:3]
            != _identity(os.fstat(staging_fd))[:3]
        ):
            raise ValueError("owned staging name/inode binding drift")
        os.rmdir(staging_name, dir_fd=parent_fd)
    finally:
        os.close(staging_fd)
    os.fsync(parent_fd)


def materialize_contract(
    output_root: Path | None = None,
) -> dict[str, Any]:
    """Build and atomically publish the deterministic Exact6 evidence."""
    _assert_canonical_evidence_runtime()
    root = (
        REPO_ROOT / DEFAULT_OUTPUT_ROOT
        if output_root is None
        else Path(output_root)
    )
    if not root.name or root.name in {".", ".."}:
        raise ValueError("unsafe output root name")
    parent = root.parent
    payloads = build_artifacts()
    parent_item = os.lstat(parent)
    if (
        stat.S_ISLNK(parent_item.st_mode)
        or not stat.S_ISDIR(parent_item.st_mode)
    ):
        raise ValueError("unsafe output parent")
    parent_identity = _identity(parent_item)
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    parent_fd = os.open(parent, directory_flags)
    staging_fd = -1
    staging_name = ""
    staging_identity: Identity | None = None
    published = False
    try:
        if _identity(os.fstat(parent_fd)) != parent_identity:
            raise ValueError("output parent stat/open race")
        try:
            os.stat(root.name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            if _read_exact_output_set(
                root,
                payloads,
                parent_fd=parent_fd,
                expected_parent_identity=parent_identity,
            ):
                return json.loads(payloads[MANIFEST_FILE])
            raise ValueError("existing output set mismatch")
        staging_name = _make_staging_directory(parent_fd, root.name)
        staging_lexical = os.stat(
            staging_name, dir_fd=parent_fd, follow_symlinks=False
        )
        staging_identity = _identity(staging_lexical)
        if (
            stat.S_ISLNK(staging_lexical.st_mode)
            or not stat.S_ISDIR(staging_lexical.st_mode)
        ):
            raise ValueError("unsafe staging directory")
        staging_fd = os.open(
            staging_name, directory_flags, dir_fd=parent_fd
        )
        if _identity(os.fstat(staging_fd)) != staging_identity:
            raise ValueError("staging stat/open race")
        for name in OUTPUT_FILES:
            _write_exclusive_leaf(staging_fd, name, payloads[name])
        os.fsync(staging_fd)
        try:
            _rename_noreplace(staging_name, root.name, parent_fd)
        except OSError as error:
            if error.errno == errno.EEXIST and _read_exact_output_set(
                root,
                payloads,
                parent_fd=parent_fd,
                expected_parent_identity=parent_identity,
            ):
                os.close(staging_fd)
                staging_fd = -1
                _cleanup_owned_staging(
                    parent_fd, staging_name, staging_identity
                )
                return json.loads(payloads[MANIFEST_FILE])
            raise
        published = True
        published_identity = _identity(os.fstat(staging_fd))
        if (
            _identity(
                os.stat(
                    root.name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
            )
            != published_identity
        ):
            raise ValueError("destination name/inode binding mismatch")
        os.fsync(parent_fd)
        if (
            _identity(os.fstat(staging_fd)) != published_identity
            or _identity(
                os.stat(
                    root.name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
            )
            != published_identity
            or _identity(os.fstat(parent_fd))
            != _identity(os.lstat(parent))
        ):
            raise ValueError("post-fsync destination binding drift")
        if not _read_exact_output_set(
            root,
            payloads,
            parent_fd=parent_fd,
            expected_parent_identity=parent_identity,
            expected_root_identity=published_identity,
        ):
            raise ValueError("published output postverify failed")
    except BaseException:
        if (
            not published
            and staging_identity is not None
            and staging_name
        ):
            if staging_fd >= 0:
                os.close(staging_fd)
                staging_fd = -1
            _cleanup_owned_staging(
                parent_fd, staging_name, staging_identity
            )
        raise
    finally:
        if staging_fd >= 0:
            os.close(staging_fd)
        os.close(parent_fd)
    return json.loads(payloads[MANIFEST_FILE])


def run_covapie_bulk_download_admission_admit_014_rule_logic_interface_v1(
    output_root: Path | None = None,
) -> dict[str, Any]:
    """Explicitly materialize the deterministic Exact6 evidence set."""
    return materialize_contract(output_root)


if __name__ == "__main__":
    materialize_contract()
