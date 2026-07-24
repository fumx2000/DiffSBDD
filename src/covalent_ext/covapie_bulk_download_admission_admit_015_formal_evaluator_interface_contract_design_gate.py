"""Design-only ADMIT_015 formal evaluator interface contract gate.

This module freezes the future one-keyword public signature and Exact9 result
contract.  It intentionally does not define ``evaluate_admit_015``, the formal
``Admit015EvaluationResult`` type, an adapter, registry entry, dispatcher
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
import secrets
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
    "covapie_bulk_download_admission_admit_015_"
    "formal_evaluator_interface_contract_v1"
)
BASE_COMMIT = "a7800cfad9f55809d6161c2db12f49c8312165fb"
BASE_PARENT = "4fb86e7d6b8cd27258362cae34eec196b117c265"
BASE_TREE = "7f74b75e63e2f949a5ed73b7f7df6aa921235132"
BASE_SUBJECT = "add CovaPIE ADMIT_015 training authorization contract v1"
RECOMMENDED_NEXT_STEP = (
    "implement_covapie_admit_015_standalone_evaluator_interface_v1"
)
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

CANONICAL_PYTHON_IMPLEMENTATION = "cpython"
CANONICAL_PYTHON_VERSION = "3.10.4"
NONCANONICAL_PYTHON_POLICY = (
    "evaluator_semantic_smoke_only; artifact_build_checker_and_frozen_ast_forbidden"
)
PYTHON_RUNTIME_MIGRATION_POLICY = "explicit_contract_refresh_required"

ADMISSION_RULE_ID = "ADMIT_015"
AUTHORIZATION_CONTEXT_ITEM = "current_stage_training_authorized"
DOWNLOAD_AUTHORIZATION_CONTEXT_ITEM = "current_stage_download_authorized"
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
    "CURRENT_STAGE_TRAINING_AUTHORIZED_MISSING",
    "STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED",
    "CURRENT_STAGE_TRAINING_AUTHORIZED_TYPE_INVALID",
    "TRAINING_NOT_AUTHORIZED",
)
PRECEDENCE = REASON_VOCABULARY[1:] + ("",)
BLOCKER_REASONS = frozenset(REASON_VOCABULARY[1:])


class _DesignMissingValue:
    __slots__ = ()


_MISSING = _DesignMissingValue()


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
                default=_MISSING,
                annotation=object,
            ),
        ),
        return_annotation="Admit015EvaluationResult",
    )


FORMAL_SIGNATURE_DESIGN = _signature_design()
FUTURE_PUBLIC_SIGNATURE = (
    "evaluate_admit_015(*, stage_authorization_context: object = _MISSING) "
    "-> Admit015EvaluationResult"
)


@dataclass(frozen=True)
class Admit015FormalEvaluatorInterfaceContractDesign:
    signature: object = FORMAL_SIGNATURE_DESIGN
    parameter_order: tuple[str, ...] = PARAMETERS
    result_field_order: tuple[str, ...] = RESULT_FIELDS

    def __post_init__(self) -> None:
        if type(self) is not Admit015FormalEvaluatorInterfaceContractDesign:
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
class Admit015EvaluationResultContractDesign:
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
        if type(self) is not Admit015EvaluationResultContractDesign:
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


def validate_admit_015_evaluation_result_contract_design(value: object) -> bool:
    if type(value) is not Admit015EvaluationResultContractDesign:
        raise TypeError("exact Admit015 EvaluationResult ContractDesign required")
    reconstructed = Admit015EvaluationResultContractDesign(
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
) -> Admit015EvaluationResultContractDesign:
    return Admit015EvaluationResultContractDesign(
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


def classify_admit_015_formal_evaluator_interface_design(
    *,
    stage_authorization_context: object = _MISSING,
) -> Admit015EvaluationResultContractDesign:
    """Pure in-memory Design oracle; this is not the future public evaluator."""
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


CONTRACT_FILE = (
    "covapie_admit_015_formal_evaluator_interface_and_result_contract.csv"
)
ROUTING_FILE = (
    "covapie_admit_015_formal_evaluator_routing_and_consumption_contract.csv"
)
TRUTH_FILE = "covapie_admit_015_formal_evaluator_interface_truth_matrix.csv"
SOURCE_FILE = (
    "covapie_admit_015_formal_evaluator_interface_source_boundary_audit.csv"
)
ISSUE_FILE = (
    "covapie_admit_015_formal_evaluator_interface_issue_readiness_inventory.csv"
)
MANIFEST_FILE = (
    "covapie_admit_015_formal_evaluator_interface_contract_manifest.json"
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
    "covapie_bulk_download_admission_admit_015_"
    "download_authorization_contract_v1"
)
PRE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_015_"
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
    "covapie_bulk_download_admission_admit_015_"
    "download_authorization_contract_design_gate.py"
)
PRE_MATRIX = (
    PRE_ROOT / "covapie_admit_015_formal_evaluator_precondition_matrix.csv"
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
    / "covapie_admit_015_download_authorization_value_and_trust_contract.csv": "b22f02efdd53dce995730a05cc5c12ffa659c2d98b345afc663b118cc104752d",
    AUTH_ROOT
    / "covapie_admit_015_stage_authorization_routing_and_enforcement_contract.csv": "68bc56b214f212ffec359049146e371ac7ce48bed34bfd6bb80313a2fd7046a6",
    AUTH_ROOT
    / "covapie_admit_015_failure_taxonomy_and_precedence.csv": "1970da57fdec24e9c5b6e518e1dfa7c2103d3bef6da065b24e3d61a296cdeffc",
    AUTH_ROOT
    / "covapie_admit_015_download_authorization_truth_matrix.csv": "e4f39f5178b91906639670f5c1ddb1c02b40c802de9ce386aee2a6b6d49f8482",
    AUTH_ROOT
    / "covapie_admit_015_issue_readiness_inventory.csv": "10e3475cb329d517c27fae26636294d0aa69a609a3c59a8b7f0119b0b123edbe",
    AUTH_ROOT
    / "covapie_admit_015_download_authorization_contract_manifest.json": "9c54c9d6cb11776b04938d9be048699041bfc4020dca4c00425faadaaaa5d4d2",
    PRE_MATRIX: "6b52a4e96dd960e7df53b7160f5cd00d63fbeb62ee5bc5ec9882623efd268c30",
    AUA_CONTEXT: "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0",
    RUNTIME_PRODUCTION: "79f95b6e178044ff5b4f5abbd6445b6cd848e81ba1a8a16cacdf831b05b9b892",
    RUNTIME_MANIFEST: "2940e6cc02a92b4919cdece3b1fa7c2f5e27d844f2962bb18757197266c23f79",
}
SOURCE_PATHS = tuple(SOURCE_SHA256)

# ADMIT_015 v1 freezes the precondition-audit source schema rather than the
# older ADMIT_014 interface-gate schema.
SOURCE_COLUMNS = (
    "source_order",
    "source_relative_path",
    "expected_sha256",
    "base_tree_mode",
    "base_tree_blob",
    "index_mode",
    "index_blob",
    "index_stage",
    "base_tree_sha256",
    "filesystem_sha256",
    "tracked",
    "regular_file",
    "non_symlink",
    "pinned_read",
    "post_read_identity_verified",
    "final_leaf_identity_verified",
    "source_verified",
)
AUTH_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_015_"
    "training_authorization_contract_v1"
)
PRE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_015_"
    "formal_evaluator_interface_preconditions_audit_v1"
)
PRECEDENT_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_admit_014_"
    "formal_evaluator_interface_contract_v1"
)
RUNTIME_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014_v1"
)
AUTH_PRODUCTION = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_admit_015_"
    "training_authorization_contract.py"
)
PRE_INVENTORY = PRE_ROOT / (
    "covapie_admit_015_formal_evaluator_interface_precondition_inventory.csv"
)
PRE_MANIFEST = PRE_ROOT / (
    "covapie_admit_015_formal_evaluator_interface_preconditions_manifest.json"
)
PRECEDENT_PRODUCTION = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_admit_014_"
    "formal_evaluator_interface_contract_design_gate.py"
)
RUNTIME_MANIFEST = (
    RUNTIME_ROOT / "covapie_admit_001_to_014_runtime_manifest.json"
)
FEATURE_MANIFEST = Path(
    "data/derived/covalent_small/covapie_feature_semantics_audit_gate_v0/"
    "covapie_feature_semantics_audit_gate_manifest.json"
)
STEP12D_MANIFEST = Path(
    "data/derived/covalent_small/pretrained_masked_loss_smoke_v0/"
    "pretrained_masked_loss_smoke_manifest.json"
)
SOURCE_SHA256 = {
    AUTH_PRODUCTION:
        "77d278f6c0666d9843c86151bb8189836639e89f93b9488c92c5e7169a3d76e1",
    AUTH_ROOT / "covapie_admit_015_training_authorization_contract.csv":
        "d8cdc33a8debac9959563047b54a0975c5318c09ffefc3b69b9025e8e768254d",
    AUTH_ROOT / "covapie_admit_015_training_authorization_truth_matrix.csv":
        "bc1070cb7df2db7ee05c4c8aa21ea9563a08974b620d44ee42c193c63b4fb37b",
    AUTH_ROOT
    / "covapie_admit_015_training_authorization_value_and_trust_contract.csv":
        "eab6be6568b3a8a8fba298eab6fff052184922a70b2893663311d437c6735d7e",
    AUTH_ROOT
    / "covapie_admit_015_training_authorization_safety_boundary_audit.csv":
        "ed6fb5650716c9135157393eff6b8882781c063c569a5be5aafc550c249969d0",
    AUTH_ROOT / "covapie_admit_015_issue_readiness_inventory.csv":
        "f457da61bffade18999af5c069d237c30aa30a0c63efb8bb14130935fb0757ec",
    AUTH_ROOT / "covapie_admit_015_training_authorization_contract_manifest.json":
        "16ea4bb5f781c6f6d8277fb4142258c2bee4849b942582e48692373caee5cda1",
    PRE_INVENTORY:
        "c52287ac5a435e58a400be0e33e17c1096b7b0d3b2671be0398a6be03e409839",
    PRE_MANIFEST:
        "7f64389a018c9bc1170ffeb94d1f393aefc27f67edef1d85143659f43dc8d729",
    PRECEDENT_PRODUCTION:
        "af25eb2f2fb84230b29d2204fff05308626e7f455a7b950aa8efb922607c298e",
    PRECEDENT_ROOT
    / "covapie_admit_014_formal_evaluator_interface_and_result_contract.csv":
        "7baea79ce0010e31efcf2e70f11350ee5fc05a5c358df3926f9df591da3d3524",
    PRECEDENT_ROOT
    / "covapie_admit_014_formal_evaluator_routing_and_consumption_contract.csv":
        "9df1faddeb8aa14e8b29af10296222925361cd1f1f98c05a2cc3a2cc64c7f769",
    PRECEDENT_ROOT
    / "covapie_admit_014_formal_evaluator_interface_truth_matrix.csv":
        "55dbbddf1f3bcdb4bbd6ce763d7a0c812020241157098c6af18799cc5ffac062",
    PRECEDENT_ROOT
    / "covapie_admit_014_formal_evaluator_interface_issue_readiness_inventory.csv":
        "d2510c9d2cf7ee1a1fc378e639eb69b68612e818f4e7af10a0e36dc0d788f54d",
    PRECEDENT_ROOT
    / "covapie_admit_014_formal_evaluator_interface_contract_manifest.json":
        "217490ef69526486b51117e4900d0669b4de466a023023ecb56ebdf0822fb731",
    RUNTIME_MANIFEST:
        "bf7bbe3c2158f661c6e71835bf603af76ffbb315d4ef377c9f72da246619ba40",
    FEATURE_MANIFEST:
        "a625335dd670ceb53f1515237a676c25d156b510eb80113ea8c4073e1ae1879d",
    STEP12D_MANIFEST:
        "f2b3165d70c046f27defbe821afcc5294ff5cdf0037595cd5c42066ab27ea08b",
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
    leaf_fd = -1
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
    if len(SOURCE_PATHS) != 18 or len(set(SOURCE_PATHS)) != 18:
        raise ValueError("source boundary must be ordered Exact18")
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
        / "covapie_admit_015_training_authorization_contract_manifest.json",
    )
    preconditions = _csv_rows(snapshot, PRE_INVENTORY)
    pre_manifest = _json(snapshot, PRE_MANIFEST)
    precedent = _json(
        snapshot,
        PRECEDENT_ROOT
        / "covapie_admit_014_formal_evaluator_interface_contract_manifest.json",
    )
    runtime = _json(snapshot, RUNTIME_MANIFEST)
    feature = _json(snapshot, FEATURE_MANIFEST)
    step12d = _json(snapshot, STEP12D_MANIFEST)
    if not (
        authorization["base_commit"] == BASE_PARENT
        and authorization["current_permission"] is False
        and authorization["authorized_admit_015_training_execution_count"] == 0
        and authorization["admit_015_training_authorization_contract_frozen"]
        is True
        and authorization["admit_015_formal_evaluator_interface_contract_frozen"]
        is False
        and authorization["ready_for_training"] is False
        and authorization[
            "future_mandatory_training_authorization_responsibility"
        ]["implemented"]
        is False
        and authorization["precondition_transition"]["complete_count"] == 31
        and authorization["precondition_transition"]["incomplete_count"] == 14
        and len(preconditions) == 45
        and [row["precondition_id"] for row in preconditions]
        == [f"PRE_{index:03d}" for index in range(1, 46)]
        and pre_manifest["precondition_count"] == 45
        and precedent["truth_matrix_row_count"] == 69
        and precedent["truth_matrix_positive_row_count"] == 45
        and precedent["truth_matrix_negative_result_row_count"] == 24
        and precedent["formal_evaluator_implemented"] is False
        and precedent["formal_result_type_defined"] is False
        and runtime["registered_rule_ids"]
        == [f"ADMIT_{index:03d}" for index in range(1, 15)]
        and runtime["known_not_registered_rule_ids"] == ["ADMIT_015"]
        and runtime["admit_015_registered_in_engine"] is False
        and runtime["combined_candidate_verdict_implemented"] is False
        and runtime["cross_rule_aggregation_implemented"] is False
        and runtime["ready_for_training"] is False
        and feature["feature_semantics_known_for_training"] is False
        and feature["unknown_atom_feature_policy_finalized_for_training"]
        is False
        and step12d["feature_semantics_known"] is False
    ):
        raise ValueError("ADMIT_015 predecessor lineage drift")


def _contract_rows() -> list[dict[str, str]]:
    specs: list[tuple[str, str, str, str, str]] = [
        (
            "signature",
            "function",
            "evaluate_admit_015",
            FUTURE_PUBLIC_SIGNATURE,
            "public name",
        ),
        (
            "signature",
            "parameter count",
            "evaluate_admit_015",
            "1",
            "int",
        ),
        (
            "signature",
            "stage_authorization_context",
            "evaluate_admit_015",
            "keyword-only; annotation object; private _MISSING default",
            "inspect.Parameter",
        ),
        (
            "signature",
            "return annotation",
            "evaluate_admit_015",
            "Admit015EvaluationResult",
            "str forward annotation",
        ),
        (
            "signature",
            "forbidden call shapes",
            "evaluate_admit_015",
            "no positional; no *args; no **kwargs; no extra parameters",
            "closed signature",
        ),
    ]
    for name, exact_type in zip(RESULT_FIELDS, RESULT_FIELD_TYPES, strict=True):
        specs.append(
            (
                "result_field",
                name,
                "Admit015EvaluationResult",
                "Exact9 ordered frozen dataclass field",
                exact_type,
            )
        )
    specs.extend(
        (
            (
                "representation",
                "canonical_stage_authorization_record",
                "Admit015EvaluationResult",
                "() or exact one-pair tuple retaining exact False|True",
                "exact tuple of exact pair tuple",
            ),
            (
                "representation",
                "validated_stage_authorization_fields",
                "Admit015EvaluationResult",
                "() or ('current_stage_training_authorized',)",
                "exact tuple of exact str",
            ),
            (
                "representation",
                "consumed_stage_authorization_fields",
                "Admit015EvaluationResult",
                "() or ('current_stage_training_authorized',)",
                "exact tuple of exact str",
            ),
            (
                "invariant",
                "outcome and flags",
                "Admit015EvaluationResult",
                "passed iff outcome passed; blocks iff outcome blocked",
                "closed invariant",
            ),
            (
                "invariant",
                "reason",
                "Admit015EvaluationResult",
                "empty iff passed; six exact blockers",
                "closed vocabulary",
            ),
            (
                "invariant",
                "evaluator_io_used",
                "Admit015EvaluationResult",
                "exact False",
                "bool",
            ),
            (
                "formal_symbol_state",
                "formal evaluator",
                "evaluate_admit_015",
                "not implemented",
                "design assertion",
            ),
            (
                "formal_symbol_state",
                "formal result",
                "Admit015EvaluationResult",
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


class _ResultSubclass(Admit015EvaluationResultContractDesign):
    pass


def _reject_negative_result(case_id: str) -> str:
    baseline = classify_admit_015_formal_evaluator_interface_design(
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
        Admit015EvaluationResultContractDesign(
            *(values[name] for name in RESULT_FIELDS)
        )
    except (TypeError, ValueError) as error:
        return f"RESULT_CONTRACT_REJECTED:{type(error).__name__}"
    raise ValueError(f"negative result case accepted: {case_id}")


def _representation(value: object) -> str:
    if value is _MISSING:
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
            _MISSING,
            "verified",
            "",
        ),
        _TruthCase(
            "SIGNATURE_ONE_KEYWORD_ONLY",
            "signature",
            "one keyword-only parameter",
            _MISSING,
            "verified",
            "",
        ),
        _TruthCase(
            "SIGNATURE_PRIVATE_MISSING",
            "signature",
            "private missing singleton default",
            _MISSING,
            "verified",
            "",
        ),
        _TruthCase(
            "SIGNATURE_RETURN_ANNOTATION",
            "signature",
            "Admit015EvaluationResult",
            _MISSING,
            "verified",
            "",
        ),
        _TruthCase(
            "SIGNATURE_NO_VARARGS",
            "signature",
            "no *args",
            _MISSING,
            "verified",
            "",
        ),
        _TruthCase(
            "SIGNATURE_NO_VARKW",
            "signature",
            "no **kwargs",
            _MISSING,
            "verified",
            "",
        ),
        _TruthCase(
            "SIGNATURE_POSITIONAL_REJECTED",
            "signature",
            "positional invocation rejected",
            _MISSING,
            "rejected",
            "TypeError",
        ),
        _TruthCase(
            "SIGNATURE_UNKNOWN_KEYWORD_REJECTED",
            "signature",
            "unknown keyword rejected",
            _MISSING,
            "rejected",
            "TypeError",
        ),
        _TruthCase(
            "OMITTED",
            "context_structure",
            "omitted",
            _MISSING,
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
                        DOWNLOAD_AUTHORIZATION_CONTEXT_ITEM: False,
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
                        DOWNLOAD_AUTHORIZATION_CONTEXT_ITEM: True,
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
                _MISSING,
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
        "evaluate_admit_015(*, stage_authorization_context: object = _MISSING) "
        "-> Admit015EvaluationResult"
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
            and parameters[0].default is _MISSING
            and parameters[0].default is not None
        ),
        "SIGNATURE_RETURN_ANNOTATION": (
            signature.return_annotation == "Admit015EvaluationResult"
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
            lambda: classify_admit_015_formal_evaluator_interface_design(object()),
        )
    elif case_id == "SIGNATURE_UNKNOWN_KEYWORD_REJECTED":
        actions = (
            lambda: signature.bind(unknown=True),
            lambda: classify_admit_015_formal_evaluator_interface_design(
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
            _MISSING,
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
                if case.context is _MISSING
                else {"stage_authorization_context": case.context}
            )
            result = classify_admit_015_formal_evaluator_interface_design(
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
                validate_admit_015_evaluation_result_contract_design(result)
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


GLOBAL_OPEN_ISSUES = (
    "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
    "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
    "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
    "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
)


def _issue_rows(snapshot: tuple[_Source, ...]) -> list[dict[str, str]]:
    inherited = _csv_rows(
        snapshot,
        AUTH_ROOT / "covapie_admit_015_issue_readiness_inventory.csv",
    )
    rows = [dict(row) for row in inherited]
    by_id = {row["issue_id"]: row for row in rows}
    if (
        len(rows) != 30
        or [row["inherited_order"] for row in rows]
        != [str(index) for index in range(1, 31)]
        or [row["issue_id"] for row in rows[:23]]
        != [row["issue_id"] for row in inherited[:23]]
        or any(
            by_id[issue]["successor_effective_status"] != "open"
            for issue in GLOBAL_OPEN_ISSUES
        )
        or by_id["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"][
            "affected_rules"
        ]
        != "ADMIT_015"
    ):
        raise ValueError("Exact30 issue continuity drift")
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
            "base_tree_blob": record.blob,
            "index_mode": record.mode,
            "index_blob": record.blob,
            "index_stage": "0",
            "base_tree_sha256": record.sha256,
            "filesystem_sha256": record.sha256,
            "tracked": "true",
            "regular_file": "true",
            "non_symlink": "true",
            "pinned_read": "true",
            "post_read_identity_verified": "true",
            "final_leaf_identity_verified": "true",
            "source_verified": "true",
        }
        for index, record in enumerate(snapshot, 1)
    ]


AUTHORIZATION_RESOLVED_PRECONDITION_IDS = (
    "PRE_007",
    "PRE_008",
    "PRE_009",
    "PRE_010",
    "PRE_011",
    "PRE_012",
    "PRE_016",
    "PRE_017",
    "PRE_018",
    "PRE_025",
    "PRE_026",
    "PRE_027",
)
INTERFACE_RESOLVED_PRECONDITION_IDS = (
    "PRE_019",
    "PRE_020",
    "PRE_021",
    "PRE_022",
    "PRE_023",
    "PRE_024",
)
OPEN_PRECONDITION_IDS = (
    "PRE_031",
    "PRE_032",
    "PRE_033",
    "PRE_034",
    "PRE_035",
    "PRE_036",
    "PRE_038",
    "PRE_042",
)


def _precondition_transition(
    snapshot: tuple[_Source, ...],
) -> list[dict[str, str]]:
    rows = [dict(row) for row in _csv_rows(snapshot, PRE_INVENTORY)]
    for row in rows:
        identifier = row["precondition_id"]
        if identifier in AUTHORIZATION_RESOLVED_PRECONDITION_IDS:
            row["observed_state"] = (
                "frozen by ADMIT_015 training authorization contract v1"
            )
            row["completion_status"] = "complete"
            row["implementation_blocking"] = "false"
            row["resolution_or_gap"] = "authorization contract frozen"
        elif identifier in INTERFACE_RESOLVED_PRECONDITION_IDS:
            row["observed_state"] = (
                "frozen by ADMIT_015 formal evaluator interface contract v1"
            )
            row["completion_status"] = "complete"
            row["implementation_blocking"] = "false"
            row["resolution_or_gap"] = (
                "formal interface and result design contract frozen"
            )
    if not (
        len(rows) == 45
        and sum(row["completion_status"] == "complete" for row in rows) == 37
        and sum(
            row["completion_status"] == "supported_but_not_frozen"
            for row in rows
        )
        == 0
        and sum(row["completion_status"] == "incomplete" for row in rows) == 8
        and sum(row["implementation_blocking"] == "true" for row in rows) == 8
        and [
            row["precondition_id"]
            for row in rows
            if row["completion_status"] != "complete"
        ]
        == list(OPEN_PRECONDITION_IDS)
    ):
        raise ValueError("Exact45 precondition transition drift")
    return rows


TRUE_READINESS = (
    "admit_015_preconditions_audited",
    "admit_015_training_authorization_contract_frozen",
    "admit_015_formal_evaluator_interface_contract_frozen",
    "admit_015_standalone_signature_frozen",
    "admit_015_formal_result_contract_frozen",
    "admit_015_result_representation_frozen",
    "admit_015_design_oracle_contract_frozen",
    "admit_015_multi_invalid_precedence_frozen",
    "admit_015_stage_authorization_routing_resolved",
    "admit_015_exact_bool_value_contract_frozen",
    "admit_015_reason_vocabulary_frozen",
    "admit_015_future_evaluator_pure_in_memory_possible",
    "future_mandatory_training_authorization_responsibility_frozen",
    "ready_for_admit_015_standalone_evaluator_interface_implementation",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "evaluate_admit_015_implemented",
    "Admit015EvaluationResult_implemented",
    "admit_015_rule_logic_implemented",
    "admit_015_runtime_independent_oracle_implemented",
    "admit_015_standalone_evaluator_implemented",
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
    issue_bytes = _source(
        frozen, AUTH_ROOT / "covapie_admit_015_issue_readiness_inventory.csv"
    ).content
    precondition_rows = _precondition_transition(frozen)
    precondition_bytes = _csv_bytes(
        tuple(precondition_rows[0]), precondition_rows
    )
    payloads = {
        CONTRACT_FILE: _csv_bytes(CONTRACT_COLUMNS, contract_rows),
        ROUTING_FILE: _csv_bytes(ROUTING_COLUMNS, routing_rows),
        TRUTH_FILE: _csv_bytes(TRUTH_COLUMNS, truth_rows),
        SOURCE_FILE: _csv_bytes(SOURCE_COLUMNS, source_rows),
        ISSUE_FILE: issue_bytes,
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
            "covapie_admit_015_formal_evaluator_interface_contract_manifest_v1"
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
        "future_function_name": "evaluate_admit_015",
        "future_result_type_name": "Admit015EvaluationResult",
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
            "current_stage_training_authorized",
            "current_stage_download_authorized",
        ],
        "formal_evaluator_implemented": False,
        "formal_result_type_defined": False,
        "design_oracle": (
            "classify_admit_015_formal_evaluator_interface_design"
        ),
        "design_result_type": "Admit015EvaluationResultContractDesign",
        "result_fields": list(RESULT_FIELDS),
        "result_field_count": 9,
        "result_field_exact_types": list(RESULT_FIELD_TYPES),
        "result_dataclass_frozen": True,
        "result_subclassing_forbidden": True,
        "canonical_stage_authorization_record_representation": {
            "empty": "()",
            "false": (
                "(('current_stage_training_authorized', False),)"
            ),
            "true": "(('current_stage_training_authorized', True),)",
            "outer_type": "exact tuple",
            "pair_type": "exact tuple",
            "value_type": "exact bool",
        },
        "validated_stage_authorization_fields_representation": [
            "()",
            "('current_stage_training_authorized',)",
        ],
        "consumed_stage_authorization_fields_representation": [
            "()",
            "('current_stage_training_authorized',)",
        ],
        "outcome_vocabulary": list(OUTCOME_VOCABULARY),
        "reason_vocabulary": list(REASON_VOCABULARY),
        "failure_precedence": list(PRECEDENCE),
        "result_invariants": [
            "admission_rule_id == ADMIT_015",
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
                "('current_stage_training_authorized',)",
            ],
            "lookup_failure": [
                "()",
                "()",
                "('current_stage_training_authorized',)",
            ],
            "invalid_type": [
                "()",
                "()",
                "('current_stage_training_authorized',)",
            ],
            "exact_false": [
                "(('current_stage_training_authorized', False),)",
                "('current_stage_training_authorized',)",
                "('current_stage_training_authorized',)",
            ],
            "exact_true": [
                "(('current_stage_training_authorized', True),)",
                "('current_stage_training_authorized',)",
                "('current_stage_training_authorized',)",
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
            "download_coexistence_key": DOWNLOAD_AUTHORIZATION_CONTEXT_ITEM,
            "download_key_access_count": 0,
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
            "row_count": 45,
            "complete_count": 37,
            "supported_but_not_frozen_count": 0,
            "incomplete_count": 8,
            "implementation_blocking_count": 8,
            "resolved_precondition_ids": list(
                INTERFACE_RESOLVED_PRECONDITION_IDS
            ),
            "remaining_open_precondition_ids": list(OPEN_PRECONDITION_IDS),
            "transition_rows_sha256": hashlib.sha256(
                precondition_bytes
            ).hexdigest(),
        },
        "issue_continuity": {
            "row_count": 30,
            "transition_count": 0,
            "inventory_source_sha256": SOURCE_SHA256[
                AUTH_ROOT / "covapie_admit_015_issue_readiness_inventory.csv"
            ],
            "byte_identical_to_training_authorization_contract": True,
            "coverage": ["ADMIT_015"],
            "coverage_issue_open": True,
        },
        "remaining_open_issue_ids": list(GLOBAL_OPEN_ISSUES),
        "current_permission": False,
        "authorized_admit_015_training_execution_count": 0,
        "synthetic_true_design_case_grants_current_permission": False,
        "synthetic_true_design_case_starts_real_training": False,
        "future_mandatory_training_authorization_responsibility": {
            "frozen": True,
            "api_frozen": False,
            "implemented": False,
            "evaluate_once_each_real_training_invocation": True,
            "must_complete_before_any_protected_operation": True,
            "blocked_must_not_continue": True,
            "combined_verdict_may_override_blocked": False,
        },
        "unified_adapter_contract_frozen": False,
        "unified_adapter_implemented": False,
        "admit_015_registered_in_engine": False,
        "unified_dispatch_runtime_with_admit_001_to_015_implemented": False,
        "source_count": len(frozen),
        "source_boundary_schema": list(SOURCE_COLUMNS),
        "source_boundary": [
            {
                "order": order,
                "path": source.path.as_posix(),
                "sha256": source.sha256,
                "base_tree_mode": source.mode,
                "base_tree_blob": source.blob,
                "index_mode": source.mode,
                "index_blob": source.blob,
                "index_stage": 0,
                "base_tree_filesystem_byte_equal": True,
                "pinned_no_follow_read": True,
                "post_read_identity_verified": True,
                "final_leaf_fd_retained": True,
            }
            for order, source in enumerate(frozen, 1)
        ],
        "source_validation_before_candidate_and_output_read": True,
        "readiness": readiness,
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
        "canonical_mask_long_names_are_authoritative": True,
        "feature_semantics_audit_completed": False,
        "feature_semantics_audit_required_before_training": True,
        "historical_unknown_atom_feature_policy_resolved": False,
        "historical_feature_semantics_known": False,
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
        "exact6_schemas": {
            CONTRACT_FILE: list(CONTRACT_COLUMNS),
            ROUTING_FILE: list(ROUTING_COLUMNS),
            TRUTH_FILE: list(TRUTH_COLUMNS),
            SOURCE_FILE: list(SOURCE_COLUMNS),
            ISSUE_FILE: list(issue_rows[0]),
            MANIFEST_FILE: "closed JSON contract asserted by independent checker",
        },
        "exact6_row_counts": {
            CONTRACT_FILE: len(contract_rows),
            ROUTING_FILE: len(routing_rows),
            TRUTH_FILE: len(truth_rows),
            SOURCE_FILE: len(source_rows),
            ISSUE_FILE: len(issue_rows),
        },
        "output_file_count": 6,
        "output_files": list(OUTPUT_FILES),
        "output_sha256": output_sha256,
        "output_sha256_excludes_manifest_self_hash": True,
        "renameat2_policy": (
            "RENAME_NOREPLACE_required; GPFS_EINVAL_fails_closed; "
            "no_os_replace_fallback"
        ),
        "materialization": {
            "build_before_mutation": True,
            "exclusive_leaf_create": True,
            "rename_noreplace_required": True,
            "gpfs_einval_fails_closed": True,
            "os_replace_forbidden": True,
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
        if set(os.listdir(root_fd)) != set(OUTPUT_FILES):
            return False
        for name in OUTPUT_FILES:
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
        if set(os.listdir(root_fd)) != set(OUTPUT_FILES):
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
        if set(os.listdir(root_fd)) != set(OUTPUT_FILES):
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
    payloads = build_artifacts(snapshot)
    if os.path.lexists(root):
        if _read_output_set(root, payloads):
            return json.loads(payloads[MANIFEST_FILE])
        raise ValueError("existing output set mismatch")
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
        for name in OUTPUT_FILES:
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
    return json.loads(payloads[MANIFEST_FILE])


def run_covapie_bulk_download_admission_admit_015_formal_evaluator_interface_contract_v1(
    output_root: Path | None = None,
) -> dict[str, Any]:
    """Explicit entry point; import itself is silent and side-effect free."""
    return materialize_contract(output_root)
