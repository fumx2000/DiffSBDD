"""Pure ADMIT_015 standalone evaluator and deterministic evidence builder."""

from collections.abc import Mapping
from dataclasses import dataclass, fields


ADMISSION_RULE_ID = "ADMIT_015"
AUTHORIZATION_CONTEXT_ITEM = "current_stage_training_authorized"
DOWNLOAD_AUTHORIZATION_CONTEXT_ITEM = "current_stage_download_authorized"
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
    "CURRENT_STAGE_TRAINING_AUTHORIZED_MISSING",
    "STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED",
    "CURRENT_STAGE_TRAINING_AUTHORIZED_TYPE_INVALID",
    "TRAINING_NOT_AUTHORIZED",
)
BLOCKER_REASONS = frozenset(REASON_VOCABULARY[1:])


class _MissingAdmit015Value:
    __slots__ = ()


_MISSING = _MissingAdmit015Value()


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
class Admit015EvaluationResult:
    admission_rule_id: str
    outcome: str
    passed: bool
    blocks_candidate: bool
    reason: str
    canonical_stage_authorization_record: tuple
    validated_stage_authorization_fields: tuple
    consumed_stage_authorization_fields: tuple
    evaluator_io_used: bool

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("Admit015EvaluationResult subclassing is forbidden")

    def __post_init__(self) -> None:
        if type(self) is not Admit015EvaluationResult:
            raise TypeError("exact Admit015EvaluationResult required")
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
        elif self.reason == "TRAINING_NOT_AUTHORIZED":
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
) -> Admit015EvaluationResult:
    return Admit015EvaluationResult(
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


def evaluate_admit_015(
    *,
    stage_authorization_context: object = _MISSING,
) -> Admit015EvaluationResult:
    """Evaluate the frozen ADMIT_015 stage-authorization rule in memory."""
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
            "CURRENT_STAGE_TRAINING_AUTHORIZED_MISSING",
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
            "CURRENT_STAGE_TRAINING_AUTHORIZED_TYPE_INVALID",
            (),
            (),
            consumed,
        )
    canonical = ((AUTHORIZATION_CONTEXT_ITEM, value),)
    if value is False:
        return _make_result(
            "blocked",
            "TRAINING_NOT_AUTHORIZED",
            canonical,
            consumed,
            consumed,
        )
    return _make_result("passed", "", canonical, consumed, consumed)


# === ADMIT_015 FORMAL EVALUATOR CLOSURE END ===


import ast
import csv
import ctypes
import hashlib
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
STAGE = "covapie_bulk_download_admission_admit_015_standalone_evaluator_interface_v1"
BASE_COMMIT = "809ec4f8c9494db893d2d66b7551856b2ead4401"
BASE_PARENT = "a7800cfad9f55809d6161c2db12f49c8312165fb"
BASE_TREE = "0a047613fed8bd6094675c8d4bc799284e53c43e"
BASE_SUBJECT = "add CovaPIE ADMIT_015 formal evaluator interface contract v1"
RECOMMENDED_NEXT_STEP = "design_covapie_admit_015_unified_adapter_contract_v1"
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
    "covapie_bulk_download_admission_admit_015_"
    "formal_evaluator_interface_contract_v1"
)
FORMAL_DESIGN_PRODUCTION = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_admit_015_"
    "formal_evaluator_interface_contract_design_gate.py"
)
AUTHORIZATION_MANIFEST = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_015_training_authorization_contract_v1/"
    "covapie_admit_015_training_authorization_contract_manifest.json"
)
PRECONDITION_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_015_"
    "formal_evaluator_interface_preconditions_audit_v1"
)
PRECONDITION_INVENTORY = PRECONDITION_ROOT / (
    "covapie_admit_015_formal_evaluator_interface_precondition_inventory.csv"
)
PRECONDITION_MANIFEST = PRECONDITION_ROOT / (
    "covapie_admit_015_formal_evaluator_interface_preconditions_manifest.json"
)
ADMIT014_STANDALONE_PRODUCTION = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_admit_014_rule_logic_interface.py"
)
ADMIT014_STANDALONE_MANIFEST = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_014_rule_logic_interface_v1/"
    "covapie_admit_014_rule_logic_interface_manifest.json"
)
EXACT14_RUNTIME_MANIFEST = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_"
    "admit_001_to_014_v1/covapie_admit_001_to_014_runtime_manifest.json"
)
FEATURE_SEMANTICS_MANIFEST = Path(
    "data/derived/covalent_small/covapie_feature_semantics_audit_gate_v0/"
    "covapie_feature_semantics_audit_gate_manifest.json"
)
STEP12D_MANIFEST = Path(
    "data/derived/covalent_small/pretrained_masked_loss_smoke_v0/"
    "pretrained_masked_loss_smoke_manifest.json"
)

CONTRACT_FILE = "covapie_admit_015_standalone_evaluator_interface_contract.csv"
TRUTH_FILE = "covapie_admit_015_standalone_evaluator_interface_truth_matrix.csv"
SOURCE_FILE = "covapie_admit_015_standalone_evaluator_interface_source_boundary_audit.csv"
PURITY_FILE = "covapie_admit_015_standalone_evaluator_interface_purity_audit.csv"
ISSUE_FILE = "covapie_admit_015_standalone_evaluator_interface_issue_readiness_inventory.csv"
MANIFEST_FILE = "covapie_admit_015_standalone_evaluator_interface_manifest.json"
OUTPUT_FILES = (
    CONTRACT_FILE,
    TRUTH_FILE,
    SOURCE_FILE,
    PURITY_FILE,
    ISSUE_FILE,
    MANIFEST_FILE,
)
FORMAL_MARKER = "# === ADMIT_015 FORMAL " + "EVALUATOR CLOSURE END ==="
FORMAL_CLOSURE = (
    "_MissingAdmit015Value",
    "_canonical_record_valid",
    "_field_tuple_valid",
    "Admit015EvaluationResult",
    "Admit015EvaluationResult.__post_init__",
    "_make_result",
    "evaluate_admit_015",
)
PUBLIC_SIGNATURE = (
    "evaluate_admit_015(*, stage_authorization_context: object = _MISSING) "
    "-> Admit015EvaluationResult"
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
        "48e2135517cad1ad7744345c3cb5f45e5b29d9c91fd41850eb80a96785e0daa3"
    ),
    FORMAL_DESIGN_ROOT
    / "covapie_admit_015_formal_evaluator_interface_and_result_contract.csv": (
        "5e4e6b3a222ebe65c2ed89e8ce2d98a9ce31043235417bee9d166cb14199651d"
    ),
    FORMAL_DESIGN_ROOT
    / "covapie_admit_015_formal_evaluator_routing_and_consumption_contract.csv": (
        "a0c586281e96f063f67d7c47c1a0b8336a73cb0841b283ca1de64f30fe60cf66"
    ),
    FORMAL_DESIGN_ROOT
    / "covapie_admit_015_formal_evaluator_interface_truth_matrix.csv": (
        "7b09b3c917e4bbc7d140daafa99a9b6a34584ce3a008e9f0193db804c57b4885"
    ),
    FORMAL_DESIGN_ROOT
    / "covapie_admit_015_formal_evaluator_interface_source_boundary_audit.csv": (
        "1725691b3659f4c166289cce17999caa7c13e172199d6df612fe11cf6f38fb43"
    ),
    FORMAL_DESIGN_ROOT
    / "covapie_admit_015_formal_evaluator_interface_issue_readiness_inventory.csv": (
        "f457da61bffade18999af5c069d237c30aa30a0c63efb8bb14130935fb0757ec"
    ),
    FORMAL_DESIGN_ROOT
    / "covapie_admit_015_formal_evaluator_interface_contract_manifest.json": (
        "08ce241290c66e87881c983a563be9f406d904c39e99bd9c6830c78fc3b4b021"
    ),
    AUTHORIZATION_MANIFEST:
        "16ea4bb5f781c6f6d8277fb4142258c2bee4849b942582e48692373caee5cda1",
    PRECONDITION_INVENTORY:
        "c52287ac5a435e58a400be0e33e17c1096b7b0d3b2671be0398a6be03e409839",
    PRECONDITION_MANIFEST:
        "7f64389a018c9bc1170ffeb94d1f393aefc27f67edef1d85143659f43dc8d729",
    ADMIT014_STANDALONE_PRODUCTION:
        "5f0766a4eb9dac8b00b9729b7d593adfbe105fb212eabbd4e0a3e349b35f7399",
    ADMIT014_STANDALONE_MANIFEST:
        "f1266a2a471ddac3a0966951ff681b19ebd7d2725ff8242942a9365f92f7e056",
    EXACT14_RUNTIME_MANIFEST:
        "bf7bbe3c2158f661c6e71835bf603af76ffbb315d4ef377c9f72da246619ba40",
    FEATURE_SEMANTICS_MANIFEST:
        "a625335dd670ceb53f1515237a676c25d156b510eb80113ea8c4073e1ae1879d",
    STEP12D_MANIFEST:
        "f2b3165d70c046f27defbe821afcc5294ff5cdf0037595cd5c42066ab27ea08b",
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
    leaf_fd = -1
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
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("repository root FD identity drift")
        if _identity(os.lstat(REPO_ROOT)) != root_identity:
            raise ValueError("repository root identity drift")
        if _identity(os.fstat(leaf_fd)) != expected_leaf:
            raise ValueError(f"source final FD identity drift: {path}")
        if (
            _identity(
                os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
            )
            != expected_leaf
        ):
            raise ValueError(f"source final lexical replacement: {path}")
        return b"".join(chunks)
    finally:
        if leaf_fd >= 0:
            os.close(leaf_fd)
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
    if len(SOURCE_PATHS) != 15 or len(set(SOURCE_PATHS)) != 15:
        raise ValueError("source boundary must be ordered Exact15")
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
        / "covapie_admit_015_formal_evaluator_interface_contract_manifest.json",
    )
    authorization = _source_json(snapshot, AUTHORIZATION_MANIFEST)
    preconditions = _source_json(snapshot, PRECONDITION_MANIFEST)
    precedent = _source_json(snapshot, ADMIT014_STANDALONE_MANIFEST)
    runtime = _source_json(snapshot, EXACT14_RUNTIME_MANIFEST)
    feature = _source_json(snapshot, FEATURE_SEMANTICS_MANIFEST)
    step12d = _source_json(snapshot, STEP12D_MANIFEST)
    if not (
        formal["base_commit"] == BASE_PARENT
        and formal["future_function_name"] == "evaluate_admit_015"
        and formal["future_result_type_name"] == "Admit015EvaluationResult"
        and formal["result_fields"] == list(RESULT_FIELDS)
        and formal["truth_matrix_row_count"] == 69
        and formal["precondition_transition"]["complete_count"] == 37
        and formal["precondition_transition"]["incomplete_count"] == 8
        and formal["formal_evaluator_implemented"] is False
        and formal["formal_result_type_defined"] is False
        and authorization["current_permission"] is False
        and authorization["authorized_admit_015_training_execution_count"] == 0
        and authorization["ready_for_training"] is False
        and preconditions["precondition_count"] == 45
        and preconditions["current_permission"] is False
        and precedent["admit_014_standalone_evaluator_interface_implemented"]
        is True
        and runtime["registered_rule_ids"]
        == [f"ADMIT_{index:03d}" for index in range(1, 15)]
        and runtime["known_not_registered_rule_ids"] == ["ADMIT_015"]
        and runtime["admit_015_registered_in_engine"] is False
        and runtime["unified_dispatch_runtime_with_admit_001_to_014_implemented"]
        is True
        and runtime["combined_candidate_verdict_implemented"] is False
        and runtime["cross_rule_aggregation_implemented"] is False
        and runtime["ready_for_training"] is False
        and feature["feature_semantics_known_for_training"] is False
        and feature["unknown_atom_feature_policy_finalized_for_training"]
        is False
        and step12d["feature_semantics_known"] is False
    ):
        raise ValueError("ADMIT_015 predecessor lineage drift")


def _formal_source_attestation() -> tuple[bytes, str, str, dict[str, str]]:
    _assert_canonical_evidence_runtime()
    relative = Path(
        "src/covalent_ext/"
        "covapie_bulk_download_admission_admit_015_standalone_evaluator_interface.py"
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
        "_MissingAdmit015Value",
        "_canonical_record_valid",
        "_field_tuple_valid",
        "Admit015EvaluationResult",
        "_make_result",
        "evaluate_admit_015",
    }:
        raise ValueError("formal closure definition set drift")
    result_class = definitions["Admit015EvaluationResult"]
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
        "environ",
        "getenv",
        "torch",
        "numpy",
        "pytorch_lightning",
        "rdkit",
        "dataset",
        "dataloader",
        "checkpoint",
        "model",
        "forward",
        "loss",
        "backward",
        "optimizer",
        "scheduler",
        "train",
        "fit",
        "save",
        "build_artifacts",
        "materialize_contract",
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
                DOWNLOAD_AUTHORIZATION_CONTEXT_ITEM: False,
                AUTHORIZATION_CONTEXT_ITEM: True,
            }
        )
    if case_id == "ADMIT015_PLUS_FALSE":
        return _InstrumentedMapping(
            {
                DOWNLOAD_AUTHORIZATION_CONTEXT_ITEM: True,
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
    baseline = evaluate_admit_015(
        stage_authorization_context={AUTHORIZATION_CONTEXT_ITEM: True}
    )
    values = {name: getattr(baseline, name) for name in RESULT_FIELDS}
    try:
        if case_id == "WRONG_ADMISSION_RULE_ID":
            values["admission_rule_id"] = "ADMIT_014"
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
            values["reason"] = "TRAINING_NOT_AUTHORIZED"
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
                (DOWNLOAD_AUTHORIZATION_CONTEXT_ITEM, True),
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
                DOWNLOAD_AUTHORIZATION_CONTEXT_ITEM,
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
                DOWNLOAD_AUTHORIZATION_CONTEXT_ITEM,
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
        Admit015EvaluationResult(*(values[name] for name in RESULT_FIELDS))
    except (TypeError, ValueError) as error:
        return f"RESULT_CONTRACT_REJECTED:{type(error).__name__}"
    raise ValueError(f"negative result case accepted: {case_id}")


def _independent_expected_values(case_id: str) -> tuple[object, ...]:
    field = (AUTHORIZATION_CONTEXT_ITEM,)
    if case_id in {"OMITTED", "EXPLICIT_NONE", "PROJECTION_OMITTED"}:
        outcome, reason, canonical, validated, consumed = (
            "blocked",
            "STAGE_AUTHORIZATION_CONTEXT_REQUIRED",
            (),
            (),
            (),
        )
    elif case_id in {
        "CONTEXT_OBJECT", "CONTEXT_INT", "CONTEXT_STR", "CONTEXT_LIST"
    }:
        outcome, reason, canonical, validated, consumed = (
            "blocked",
            "STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID",
            (),
            (),
            (),
        )
    elif case_id in {
        "EMPTY_MAPPING",
        "UNRELATED_ONLY_MAPPING",
        "LOOKUP_KEYERROR",
        "PROJECTION_MISSING_KEY",
    }:
        outcome, reason, canonical, validated, consumed = (
            "blocked",
            "CURRENT_STAGE_TRAINING_AUTHORIZED_MISSING",
            (),
            (),
            field,
        )
    elif case_id in {
        "LOOKUP_RUNTIMEERROR",
        "LOOKUP_VALUEERROR",
        "PROJECTION_LOOKUP_FAILED",
    }:
        outcome, reason, canonical, validated, consumed = (
            "blocked",
            "STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED",
            (),
            (),
            field,
        )
    elif case_id in {
        "INT_ZERO",
        "INT_ONE",
        "FLOAT_ZERO",
        "FLOAT_ONE",
        "STRING_FALSE",
        "STRING_TRUE",
        "NONE_VALUE",
        "LIST_VALUE",
        "DICT_VALUE",
        "CUSTOM_TRUTHY",
        "CUSTOM_FALSY",
        "PROJECTION_INVALID_TYPE",
    }:
        outcome, reason, canonical, validated, consumed = (
            "blocked",
            "CURRENT_STAGE_TRAINING_AUTHORIZED_TYPE_INVALID",
            (),
            (),
            field,
        )
    elif case_id in {"EXACT_FALSE", "ADMIT015_PLUS_FALSE", "PROJECTION_FALSE"}:
        outcome, reason, canonical, validated, consumed = (
            "blocked",
            "TRAINING_NOT_AUTHORIZED",
            ((AUTHORIZATION_CONTEXT_ITEM, False),),
            field,
            field,
        )
    elif case_id in {
        "EXACT_TRUE",
        "ADMIT015_PLUS_TRUE",
        "MANY_EXTRA_PLUS_TRUE",
        "ITERATION_RAISES",
        "LEN_RAISES",
        "GET_RAISES",
        "CONTAINS_RAISES",
        "PROJECTION_TRUE",
    }:
        outcome, reason, canonical, validated, consumed = (
            "passed",
            "",
            ((AUTHORIZATION_CONTEXT_ITEM, True),),
            field,
            field,
        )
    else:
        raise ValueError(f"independent oracle case unknown: {case_id}")
    return (
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


def _truth_rows(snapshot: tuple[_Source, ...]) -> list[dict[str, str]]:
    predecessor = _source_csv(
        snapshot,
        FORMAL_DESIGN_ROOT
        / "covapie_admit_015_formal_evaluator_interface_truth_matrix.csv",
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
            actual_kwargs = (
                {}
                if actual_context is _MISSING
                else {"stage_authorization_context": actual_context}
            )
            actual_result = evaluate_admit_015(**actual_kwargs)
            expected_values = _independent_expected_values(case_id)
            actual_values = _result_values(actual_result)
            equal = (
                type(actual_result) is Admit015EvaluationResult
                and actual_values == expected_values
                and all(
                    type(left) is type(right)
                    for left, right in zip(
                        actual_values, expected_values, strict=True
                    )
                )
                and actual_result.evaluator_io_used is False
                and _mapping_access_valid(actual_context)
            )
            observed = repr(actual_values)
            expected = repr(expected_values)
            executable += 1
            assertion = "actual_evaluator_independent_oracle_exact9_projection"
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
                    "evaluate_admit_015|Admit015EvaluationResult"
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
        ("exact_result_type", "type(self) is Admit015EvaluationResult"),
        ("exact_result_storage", "dataclass fields equal RESULT_FIELDS"),
        ("exact_top_level_types", "exact str/bool/tuple only"),
        ("identity", "admission_rule_id == ADMIT_015"),
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
        "evaluate_admit_015|signature_default",
        "Admit015EvaluationResult.__post_init__",
        "Admit015EvaluationResult.__post_init__",
        "_make_result|root",
        "Admit015EvaluationResult",
        "evaluate_admit_015",
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
                    "Admit015EvaluationResult"
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
    "admit_015_preconditions_audited",
    "admit_015_training_authorization_contract_frozen",
    "admit_015_formal_evaluator_interface_contract_frozen",
    "admit_015_standalone_signature_frozen",
    "admit_015_formal_result_contract_frozen",
    "admit_015_result_representation_frozen",
    "evaluate_admit_015_implemented",
    "Admit015EvaluationResult_implemented",
    "admit_015_rule_logic_implemented",
    "admit_015_standalone_evaluator_implemented",
    "admit_015_future_evaluator_pure_in_memory_possible",
    "feature_semantics_audit_required_before_training",
    "ready_for_admit_015_unified_adapter_contract_design",
)
FALSE_READINESS = (
    "admit_015_runtime_independent_oracle_implemented",
    "admit_015_unified_adapter_contract_frozen",
    "admit_015_unified_adapter_implemented",
    "admit_015_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_015_implemented",
    "mandatory_training_authorization_enforcement_api_frozen",
    "mandatory_training_authorization_enforcement_implemented",
    "combined_candidate_verdict_implemented",
    "cross_rule_aggregation_implemented",
    "feature_semantics_audit_completed",
    "real_training_ready",
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
    formal_source, full_sha, prefix_sha, ast_digests = (
        _formal_source_attestation()
    )
    if not formal_source:
        raise ValueError("formal source attestation failed")
    contract_rows = _contract_rows(ast_digests)
    truth_rows = _truth_rows(frozen)
    source_rows = _source_rows(frozen)
    purity_rows = _purity_rows(full_sha, prefix_sha, ast_digests)
    issue_source = _source(
        frozen,
        FORMAL_DESIGN_ROOT
        / "covapie_admit_015_formal_evaluator_interface_issue_readiness_inventory.csv",
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
        == "ADMIT_015"
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
            "covapie_admit_015_standalone_evaluator_interface_manifest_v1"
        ),
        "project": PROJECT,
        "stage": STAGE,
        "base_commit": BASE_COMMIT,
        "base_parent": BASE_PARENT,
        "base_tree": BASE_TREE,
        "base_subject": BASE_SUBJECT,
        "admission_rule_id": ADMISSION_RULE_ID,
        "public_evaluator": "evaluate_admit_015",
        "public_signature": PUBLIC_SIGNATURE,
        "parameter_order": ["stage_authorization_context"],
        "parameter_count": 1,
        "private_missing_singleton": True,
        "result_type": "Admit015EvaluationResult",
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
            "download_key_access_count": 0,
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
            "actual_evaluator_independent_oracle_projection": 37,
            "actual_result_negative_projection": 24,
            "source_boundary": len(source_rows),
            "purity_audit": len(purity_rows),
            "issue_inventory": len(issue_rows),
        },
        "actual_evaluator_independent_oracle_projection_passed": 37,
        "actual_result_negative_projection_rejected": 24,
        "truth_matrix_passed": 61,
        "purity_closure_complete": True,
        "issue_transition_count": 0,
        "issue_inventory_byte_identical_to_formal_interface": True,
        "coverage_affected_rules": "ADMIT_015",
        "remaining_open_issue_ids": list(required_open),
        "precondition_transition": {
            "row_count": 45,
            "complete_count": 37,
            "supported_but_not_frozen_count": 0,
            "incomplete_count": 8,
            "implementation_blocking_count": 8,
            "remaining_open_precondition_ids": [
                "PRE_031",
                "PRE_032",
                "PRE_033",
                "PRE_034",
                "PRE_035",
                "PRE_036",
                "PRE_038",
                "PRE_042",
            ],
        },
        "readiness": readiness,
        **readiness,
        "current_permission": False,
        "authorized_admit_015_training_execution_count": 0,
        "adapter_registry_runtime_changed": False,
        "mandatory_training_authorization_enforcement_implemented": False,
        "canonical_masks": [
            {"semantic_name": "warhead_only", "alias": "A"},
            {"semantic_name": "linker_plus_warhead", "alias": "B"},
            {"semantic_name": "scaffold_plus_warhead", "alias": "B2"},
            {"semantic_name": "scaffold_only", "alias": "B3"},
            {
                "semantic_name": "scaffold_plus_linker_plus_warhead",
                "alias": "C",
            },
        ],
        "canonical_mask_count": 5,
        "feature_semantics_audit_completed": False,
        "historical_unknown_atom_feature_policy_resolved": False,
        "historical_feature_semantics_known": False,
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
            "source_final_leaf_fd_retained": True,
            "output_final_set_traversal": True,
            "staging_lexical_binding_verified": True,
            "failure_path_non_destructive": True,
            "failure_staging_retained": True,
            "failure_cleanup_unlink_forbidden": True,
            "failure_cleanup_rmdir_forbidden": True,
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
    staging_fd: int,
    staging_identity: Identity,
) -> None:
    _verify_staging_binding(
        parent_fd, staging_fd, source_name, staging_identity
    )
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


def _refresh_directory_binding(
    directory_fd: int,
    lexical_path: Path,
) -> Identity:
    fd_identity = _identity(os.fstat(directory_fd))
    lexical = os.lstat(lexical_path)
    if (
        stat.S_ISLNK(lexical.st_mode)
        or not stat.S_ISDIR(lexical.st_mode)
        or _identity(lexical) != fd_identity
    ):
        raise ValueError(
            f"directory FD/lexical binding mismatch: {lexical_path}"
        )
    return fd_identity


def _verify_staging_binding(
    parent_fd: int,
    staging_fd: int,
    staging_name: str,
    expected_identity: Identity,
) -> None:
    lexical = os.stat(
        staging_name, dir_fd=parent_fd, follow_symlinks=False
    )
    if (
        stat.S_ISLNK(lexical.st_mode)
        or not stat.S_ISDIR(lexical.st_mode)
        or _identity(lexical) != expected_identity
        or _identity(os.fstat(staging_fd)) != expected_identity
    ):
        raise ValueError("staging lexical/FD ownership mismatch")


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
        if set(os.listdir(root_fd)) != set(OUTPUT_FILES):
            raise ValueError("output final inventory drift")
        for name, descriptor, identity, _ in leaves:
            if (
                _identity(os.fstat(descriptor)) != identity
                or _identity(
                    os.stat(name, dir_fd=root_fd, follow_symlinks=False)
                )
                != identity
            ):
                raise ValueError("output final leaf replacement")
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
            raise ValueError("output final parent/root identity drift")
        return matches
    finally:
        for _, descriptor, _, _ in leaves:
            os.close(descriptor)
        if root_fd >= 0:
            os.close(root_fd)
        if owns_parent_fd:
            os.close(parent_fd)


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
        _verify_staging_binding(
            parent_fd, staging_fd, staging_name, staging_identity
        )
        for name in OUTPUT_FILES:
            _verify_staging_binding(
                parent_fd, staging_fd, staging_name, staging_identity
            )
            _write_exclusive_leaf(staging_fd, name, payloads[name])
            staging_identity = _identity(os.fstat(staging_fd))
            _verify_staging_binding(
                parent_fd, staging_fd, staging_name, staging_identity
            )
        os.fsync(staging_fd)
        staging_identity = _identity(os.fstat(staging_fd))
        _verify_staging_binding(
            parent_fd, staging_fd, staging_name, staging_identity
        )
        _refresh_directory_binding(parent_fd, parent)
        _verify_staging_binding(
            parent_fd, staging_fd, staging_name, staging_identity
        )
        _verify_staging_binding(
            parent_fd, staging_fd, staging_name, staging_identity
        )
        _rename_noreplace(
            staging_name,
            root.name,
            parent_fd,
            staging_fd,
            staging_identity,
        )
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
    except BaseException as error:
        if not published and staging_name:
            retained = root.parent / staging_name
            raise RuntimeError(
                "materialization failed closed; failure staging retained at "
                f"{retained}"
            ) from error
        raise
    finally:
        if staging_fd >= 0:
            os.close(staging_fd)
        os.close(parent_fd)
    return json.loads(payloads[MANIFEST_FILE])


def run_covapie_bulk_download_admission_admit_015_standalone_evaluator_interface_v1(
    output_root: Path | None = None,
) -> dict[str, Any]:
    """Explicitly materialize the deterministic Exact6 evidence set."""
    return materialize_contract(output_root)


if __name__ == "__main__":
    materialize_contract()
