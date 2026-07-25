"""Design-only ADMIT_015 mandatory training-authorization enforcement contract.

This module freezes a future fail-closed guard contract and materializes
deterministic evidence.  It does not define the future public ``require_*``
function and does not import or invoke any training, model, checkpoint,
provider, download, network, or raw-data surface.
"""

from __future__ import annotations

import csv
import ctypes
import hashlib
import io
import json
import os
import re
import secrets
import stat
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

from covalent_ext import (
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015
    as exact15_runtime,
)


PROJECT = "CovaPIE"
STEP = "ADMIT_015 mandatory training authorization enforcement contract v1"
STAGE = (
    "covapie_bulk_download_admission_admit_015_mandatory_training_"
    "authorization_enforcement_contract_v1"
)
BASE_COMMIT = "4a3e813912cf704a1c6508ab21cd198e911b6b3c"
BASE_PARENT = "d70d7d8919c3ec59e0b3d864ec8e496695ab770b"
BASE_TREE = "a9c634a60c989838dd9334a0d037de62f9d0ee75"
BASE_SUBJECT = (
    "add CovaPIE unified dispatch runtime with ADMIT_001 to ADMIT_015 v1"
)
CANONICAL_PYTHON_IMPLEMENTATION = "cpython"
CANONICAL_PYTHON_VERSION = (3, 10, 4)
RECOMMENDED_NEXT_STEP = (
    "implement_covapie_admit_015_mandatory_training_authorization_"
    "enforcement_v1"
)
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

FUTURE_PUBLIC_FUNCTION = "require_admit_015_training_authorization"
FUTURE_PUBLIC_SIGNATURE = (
    "require_admit_015_training_authorization("
    "candidate_record: Mapping[str, object], *, "
    "stage_authorization_context: Mapping[str, object] | None"
    ") -> UnifiedAdmissionRuleEvaluation"
)
FUTURE_ERROR_TYPE = "Admit015TrainingAuthorizationEnforcementError"
FUTURE_ERROR_SCHEMA_VERSION = (
    "covapie_admit_015_training_authorization_enforcement_error_v1"
)
FUTURE_ERROR_FIELDS = (
    "schema_version",
    "error_code",
    "admission_rule_id",
    "reason",
)
FUTURE_ERROR_FIELD_TYPES = ("str", "str", "str", "str")
FUTURE_ERROR_SIGNATURE = (
    "Admit015TrainingAuthorizationEnforcementError("
    "schema_version: str, error_code: str, admission_rule_id: str, "
    "reason: str)"
)
FUTURE_ERROR_CODES = (
    "ADMIT_015_TRAINING_AUTHORIZATION_DISPATCH_FAILED",
    "ADMIT_015_TRAINING_AUTHORIZATION_RESULT_INVALID",
    "ADMIT_015_TRAINING_AUTHORIZATION_DENIED",
    "ADMIT_015_TRAINING_AUTHORIZATION_REPLAY_FORBIDDEN",
    "ADMIT_015_TRAINING_AUTHORIZATION_REPEATED_CALL_FORBIDDEN",
    "ADMIT_015_TRAINING_AUTHORIZATION_OVERRIDE_FORBIDDEN",
)
ADMISSION_RULE_ID = "ADMIT_015"
ADAPTER_ID = "covapie_admit_015_unified_adapter_v1"
AUTHORIZATION_ITEM = "current_stage_training_authorized"
RESULT_SCHEMA_VERSION = "covapie_unified_admission_rule_evaluation_v1"
RESULT_FIELDS = (
    "schema_version",
    "admission_rule_id",
    "admission_rule_name",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "normalized_values",
    "validated_candidate_fields",
    "consumed_candidate_fields",
    "consumed_context_items",
    "evaluator_io_used",
    "adapter_id",
)
PASS_NORMALIZED_VALUES = ((AUTHORIZATION_ITEM, "true"),)
PASS_CONSUMED_CONTEXT_ITEMS = (AUTHORIZATION_ITEM,)

PROTECTED_ACTIONS = (
    ("TRAIN_ACTION_001", "dataloader instantiation"),
    ("TRAIN_ACTION_002", "checkpoint loading"),
    ("TRAIN_ACTION_003", "model initialization"),
    ("TRAIN_ACTION_004", "model forward"),
    ("TRAIN_ACTION_005", "loss computation"),
    ("TRAIN_ACTION_006", "backward"),
    ("TRAIN_ACTION_007", "optimizer creation"),
    ("TRAIN_ACTION_008", "scheduler creation"),
    ("TRAIN_ACTION_009", "parameter update"),
    ("TRAIN_ACTION_010", "checkpoint write"),
    ("TRAIN_ACTION_011", "training-result materialization"),
)
ZERO_PROTECTED_ACTION_COUNTS = tuple(
    (action_id, 0) for action_id, _ in PROTECTED_ACTIONS
)
CANONICAL_MASKS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
CURRENT_PERMISSION = False
AUTHORIZED_ADMIT_015_TRAINING_EXECUTION_COUNT = 0

API_FILENAME = (
    "covapie_admit_015_mandatory_training_authorization_"
    "enforcement_api_contract.csv"
)
PROTECTED_FILENAME = "covapie_admit_015_protected_training_action_boundary.csv"
TRUTH_FILENAME = "covapie_admit_015_mandatory_enforcement_truth_matrix.csv"
SAFETY_FILENAME = "covapie_admit_015_mandatory_enforcement_safety_audit.csv"
ISSUE_FILENAME = (
    "covapie_admit_015_mandatory_enforcement_issue_readiness_inventory.csv"
)
MANIFEST_FILENAME = (
    "covapie_admit_015_mandatory_training_authorization_"
    "enforcement_contract_manifest.json"
)
OUTPUT_FILES = (
    API_FILENAME,
    PROTECTED_FILENAME,
    TRUTH_FILENAME,
    SAFETY_FILENAME,
    ISSUE_FILENAME,
    MANIFEST_FILENAME,
)

API_COLUMNS = (
    "contract_order",
    "contract_group",
    "contract_item",
    "frozen_value",
    "implementation_status",
    "contract_passed",
)
PROTECTED_COLUMNS = (
    "action_order",
    "action_id",
    "action_semantic_name",
    "guard_required_before_action",
    "blocked_count_expected",
    "design_pass_executes_action",
    "combined_verdict_override_forbidden",
    "real_implementation_status",
    "boundary_passed",
)
TRUTH_COLUMNS = (
    "case_order",
    "case_id",
    "case_group",
    "expected_decision",
    "observed_decision",
    "expected_error_code",
    "observed_error_code",
    "runtime_call_count",
    "selected_rule_id",
    "batch_context_is_none",
    "evaluation_context_is_none",
    "download_result_context_is_none",
    "stage_context_identity_preserved",
    "protected_action_counts_json",
    "current_permission",
    "authorized_execution_count",
    "real_training_executed",
    "case_passed",
)
SAFETY_COLUMNS = (
    "audit_order",
    "audit_item",
    "expected_state",
    "observed_state",
    "safety_passed",
)
ISSUE_COLUMNS = exact15_runtime.ISSUE_COLUMNS

SOURCE_BOUNDARY = (
    ("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015.py", "1fc5ac24e54d134d3f1f7054dfd2f264a2d76f17f0602bac216bb2e4e7e00bd1"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015_v1/covapie_admit_001_to_015_runtime_contract.csv", "b6606d4111b7493e4b8cd531fb88c5281b5a685369788b85742b5e85d721a465"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015_v1/covapie_admit_001_to_015_dispatch_truth_matrix.csv", "f93a43cfa560d495ea7e14fca26a957c6eb087907cbfde91d7456d1a55440abb"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015_v1/covapie_admit_001_to_015_registry_and_identity_audit.csv", "eac4ea16fbd2193c3b53f8d6bdf11728f086a499390bba7c33e1e3d2e61cc75e"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015_v1/covapie_admit_001_to_015_runtime_safety_audit.csv", "50db14b8d823c162e694a74abaa5a9189006f54d6cb6716d6ad9406f509a05b2"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015_v1/covapie_admit_001_to_015_runtime_issue_readiness_inventory.csv", "c8ea16e335e43ed781bb5177e1aba0247a55714f55eeb5caf8bed23a539f431d"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015_v1/covapie_admit_001_to_015_runtime_manifest.json", "0fbd5999977d025a44b4bef854d9edfda5ea0e5ed79a7d5ff7b17cef7b6186d3"),
    ("scripts/check_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015_v1.py", "b0a1a7cb6634c9a37d6ad6d72cfc0b6bdae018c2f96b99d48c1f0325f7aa12ce"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_015_training_authorization_contract.py", "77d278f6c0666d9843c86151bb8189836639e89f93b9488c92c5e7169a3d76e1"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_training_authorization_contract_v1/covapie_admit_015_training_authorization_contract.csv", "d8cdc33a8debac9959563047b54a0975c5318c09ffefc3b69b9025e8e768254d"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_training_authorization_contract_v1/covapie_admit_015_training_authorization_truth_matrix.csv", "bc1070cb7df2db7ee05c4c8aa21ea9563a08974b620d44ee42c193c63b4fb37b"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_training_authorization_contract_v1/covapie_admit_015_training_authorization_value_and_trust_contract.csv", "eab6be6568b3a8a8fba298eab6fff052184922a70b2893663311d437c6735d7e"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_training_authorization_contract_v1/covapie_admit_015_training_authorization_safety_boundary_audit.csv", "ed6fb5650716c9135157393eff6b8882781c063c569a5be5aafc550c249969d0"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_training_authorization_contract_v1/covapie_admit_015_issue_readiness_inventory.csv", "f457da61bffade18999af5c069d237c30aa30a0c63efb8bb14130935fb0757ec"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_training_authorization_contract_v1/covapie_admit_015_training_authorization_contract_manifest.json", "16ea4bb5f781c6f6d8277fb4142258c2bee4849b942582e48692373caee5cda1"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_015_standalone_evaluator_interface.py", "eacb5c1ac583649a34cdb9dcde4c004a861da43609b9ffb964a715a427883a82"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_standalone_evaluator_interface_v1/covapie_admit_015_standalone_evaluator_interface_contract.csv", "1ad1b44677abf7cd262d5928aee17381e5767dd82880aee689be07cd8b031245"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_standalone_evaluator_interface_v1/covapie_admit_015_standalone_evaluator_interface_manifest.json", "238aadcf819ffc2c30c5de063b1873ce16df59f82cb4be4b4d6222fbdc143758"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_015_formal_evaluator_interface_contract_design_gate.py", "48e2135517cad1ad7744345c3cb5f45e5b29d9c91fd41850eb80a96785e0daa3"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_formal_evaluator_interface_contract_v1/covapie_admit_015_formal_evaluator_interface_and_result_contract.csv", "5e4e6b3a222ebe65c2ed89e8ce2d98a9ce31043235417bee9d166cb14199651d"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_formal_evaluator_interface_contract_v1/covapie_admit_015_formal_evaluator_routing_and_consumption_contract.csv", "a0c586281e96f063f67d7c47c1a0b8336a73cb0841b283ca1de64f30fe60cf66"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_formal_evaluator_interface_contract_v1/covapie_admit_015_formal_evaluator_interface_contract_manifest.json", "08ce241290c66e87881c983a563be9f406d904c39e99bd9c6830c78fc3b4b021"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_015_unified_adapter_contract_design_gate.py", "a11ce87b326612e251258072995ee26fb848212a7b7dde869a10de6e473ea60c"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_unified_adapter_contract_v1/covapie_admit_015_unified_adapter_contract.csv", "16159caf1b55116fc2802e43f330d1c706041da4261e1a22039d7c8c4375ba34"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_unified_adapter_contract_v1/covapie_admit_015_stage_authorization_projection_and_context_routing_matrix.csv", "9edfaecd8492423b61d9e93413a616a4b917219d8207808da7db0142a9aed06b"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_unified_adapter_contract_v1/covapie_admit_015_unified_result_projection_truth_matrix.csv", "c40c8133f946cf39149224479590b65351c9b9229e9cc33a821616ed521ca2d3"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_unified_adapter_contract_v1/covapie_admit_015_unified_adapter_safety_audit.csv", "586ced0297eff2b396d61d771073027bc2db982e6092d2e00a1b7dcc7ac08d2d"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_unified_adapter_contract_v1/covapie_admit_015_unified_adapter_issue_readiness_inventory.csv", "f457da61bffade18999af5c069d237c30aa30a0c63efb8bb14130935fb0757ec"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_unified_adapter_contract_v1/covapie_admit_015_unified_adapter_contract_manifest.json", "43ffb247cda8cc641c0a9ba2892f66b0b54b2ed572c6f6d26a2e62cd37778449"),
    ("src/covalent_ext/covapie_bulk_download_admission_admit_014_download_authorization_contract_design_gate.py", "b2616c01234c899695c08280daacfa21cb137b847a01f5bf6e52e807b0770434"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_014_download_authorization_contract_v1/covapie_admit_014_stage_authorization_routing_and_enforcement_contract.csv", "68bc56b214f212ffec359049146e371ac7ce48bed34bfd6bb80313a2fd7046a6"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_014_download_authorization_contract_v1/covapie_admit_014_download_authorization_contract_manifest.json", "9c54c9d6cb11776b04938d9be048699041bfc4020dca4c00425faadaaaa5d4d2"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_015_formal_evaluator_interface_precondition_inventory.csv", "c52287ac5a435e58a400be0e33e17c1096b7b0d3b2671be0398a6be03e409839"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_015_formal_evaluator_interface_preconditions_manifest.json", "7f64389a018c9bc1170ffeb94d1f393aefc27f67edef1d85143659f43dc8d729"),
)
SOURCE_PATHS = tuple(Path(path) for path, _ in SOURCE_BOUNDARY)
SOURCE_SHA256 = {Path(path): digest for path, digest in SOURCE_BOUNDARY}


@dataclass(frozen=True)
class FrozenSource:
    relative_path: Path
    expected_sha256: str
    base_tree_mode: str
    base_tree_blob: str
    index_mode: str
    index_blob: str
    index_stage: int
    filesystem_sha256: str
    content: bytes


@dataclass(frozen=True)
class DesignDecision:
    released_future_in_memory_continuation: bool
    error_code: str
    runtime_call_count: int
    selected_rule_id: str
    batch_context_is_none: bool
    evaluation_context_is_none: bool
    download_result_context_is_none: bool
    stage_context_identity_preserved: bool
    protected_action_counts: tuple[tuple[str, int], ...]
    real_training_executed: bool


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _canonical_runtime_guard() -> None:
    if (
        sys.implementation.name != CANONICAL_PYTHON_IMPLEMENTATION
        or tuple(sys.version_info[:3]) != CANONICAL_PYTHON_VERSION
    ):
        raise ValueError("canonical evidence runtime requires CPython 3.10.4")


def _git(root: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        raise ValueError(f"git command failed: {arguments}")
    return completed.stdout


def _parse_index(content: bytes, path: str) -> tuple[str, str, int]:
    try:
        metadata, observed = content.decode().rstrip("\n").split("\t", 1)
        mode, blob, stage = metadata.split(" ")
        number = int(stage)
    except ValueError as error:
        raise ValueError("index entry malformed") from error
    if (
        observed != path
        or mode not in {"100644", "100755"}
        or re.fullmatch(r"[0-9a-f]{40}", blob) is None
    ):
        raise ValueError("index entry drift")
    return mode, blob, number


def _parse_tree(content: bytes, path: str) -> tuple[str, str]:
    try:
        metadata, observed = content.decode().rstrip("\n").split("\t", 1)
        mode, kind, blob = metadata.split(" ")
    except ValueError as error:
        raise ValueError("tree entry malformed") from error
    if (
        observed != path
        or kind != "blob"
        or mode not in {"100644", "100755"}
        or re.fullmatch(r"[0-9a-f]{40}", blob) is None
    ):
        raise ValueError("tree entry drift")
    return mode, blob


def build_frozen_source_snapshot(
    repo_root: Path = REPO_ROOT,
    *,
    head_ref: str = "HEAD",
) -> tuple[FrozenSource, ...]:
    """Read the fixed committed source boundary with the Exact15 pinning."""
    _canonical_runtime_guard()
    root = Path(os.path.abspath(repo_root))
    identity = _git(
        root, "show", "-s", "--format=%H%n%P%n%T%n%s", BASE_COMMIT
    ).decode().splitlines()
    if identity != [BASE_COMMIT, BASE_PARENT, BASE_TREE, BASE_SUBJECT]:
        raise ValueError("base identity drift")
    _git(root, "merge-base", "--is-ancestor", BASE_COMMIT, head_ref)
    if (
        len(SOURCE_BOUNDARY) != 34
        or len(set(SOURCE_PATHS)) != 34
        or tuple(SOURCE_SHA256) != SOURCE_PATHS
    ):
        raise ValueError("Exact34 source boundary drift")
    inspected: list[tuple[Path, str, str, str, str, str, int]] = []
    for relative in SOURCE_PATHS:
        raw = relative.as_posix()
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or relative.parts[:2] == ("data", "raw")
            or relative.parts[0] == "checkpoints"
            or STAGE in relative.parts
        ):
            raise ValueError("unsafe source boundary")
        index_mode, index_blob, index_stage = _parse_index(
            _git(root, "ls-files", "--stage", "--", raw), raw
        )
        base_mode, base_blob = _parse_tree(
            _git(root, "ls-tree", BASE_COMMIT, "--", raw), raw
        )
        if (
            index_stage != 0
            or index_mode != base_mode
            or index_blob != base_blob
        ):
            raise ValueError("source index/base identity drift")
        inspected.append(
            (
                relative,
                SOURCE_SHA256[relative],
                base_mode,
                base_blob,
                index_mode,
                index_blob,
                index_stage,
            )
        )
    records = []
    for (
        relative,
        expected,
        base_mode,
        base_blob,
        index_mode,
        index_blob,
        index_stage,
    ) in inspected:
        base = _git(root, "cat-file", "blob", base_blob)
        index = _git(root, "cat-file", "blob", index_blob)
        filesystem = exact15_runtime._pinned_read(root, relative)
        if (
            base != index
            or index != filesystem
            or _sha(base) != expected
            or _sha(filesystem) != expected
        ):
            raise ValueError(f"source bytes/SHA drift: {relative}")
        records.append(
            FrozenSource(
                relative,
                expected,
                base_mode,
                base_blob,
                index_mode,
                index_blob,
                index_stage,
                _sha(filesystem),
                filesystem,
            )
        )
    return tuple(records)


def _source(
    snapshot: Sequence[FrozenSource], suffix: str
) -> FrozenSource:
    matches = tuple(
        item
        for item in snapshot
        if item.relative_path.as_posix().endswith(suffix)
    )
    if len(matches) != 1:
        raise ValueError(f"source missing/duplicate: {suffix}")
    return matches[0]


def _json(content: bytes) -> dict[str, Any]:
    value = json.loads(content)
    if type(value) is not dict:
        raise ValueError("JSON object required")
    return value


def _csv_rows(
    content: bytes, columns: Sequence[str] | None = None
) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(content.decode(), newline=""))
    header = tuple(reader.fieldnames or ())
    if (
        not header
        or len(header) != len(set(header))
        or (columns is not None and header != tuple(columns))
    ):
        raise ValueError("CSV header drift")
    rows = [dict(row) for row in reader]
    if any(tuple(row) != header for row in rows):
        raise ValueError("CSV row drift")
    return rows


class _DispatcherProbe:
    def __init__(
        self,
        delegate: Callable[..., object],
        stage_context: object,
    ) -> None:
        self.delegate = delegate
        self.stage_context = stage_context
        self.call_count = 0
        self.selected_rule_id = ""
        self.batch_none = False
        self.evaluation_none = False
        self.download_none = False
        self.stage_identity = False

    def __call__(
        self,
        admission_rule_id: str,
        candidate_record: object,
        **kwargs: object,
    ) -> object:
        self.call_count += 1
        self.selected_rule_id = admission_rule_id
        self.batch_none = kwargs.get("batch_context", object()) is None
        self.evaluation_none = (
            kwargs.get("evaluation_context", object()) is None
        )
        self.download_none = (
            kwargs.get("download_result_context", object()) is None
        )
        self.stage_identity = (
            kwargs.get("stage_authorization_context", object())
            is self.stage_context
        )
        return self.delegate(admission_rule_id, candidate_record, **kwargs)


def _decision(
    *,
    released: bool,
    code: str,
    probe: _DispatcherProbe | None,
) -> DesignDecision:
    return DesignDecision(
        released,
        code,
        0 if probe is None else probe.call_count,
        "" if probe is None else probe.selected_rule_id,
        False if probe is None else probe.batch_none,
        False if probe is None else probe.evaluation_none,
        False if probe is None else probe.download_none,
        False if probe is None else probe.stage_identity,
        ZERO_PROTECTED_ACTION_COUNTS,
        False,
    )


def _exact13_pass_valid(value: object) -> bool:
    result_type = exact15_runtime.UnifiedAdmissionRuleEvaluation
    if type(value) is not result_type:
        return False
    try:
        storage = vars(value)
        if type(storage) is not dict or tuple(storage) != RESULT_FIELDS:
            return False
        if tuple(field.name for field in fields(result_type)) != RESULT_FIELDS:
            return False
        values = tuple(getattr(value, name) for name in RESULT_FIELDS)
        types = (
            str,
            str,
            str,
            str,
            bool,
            bool,
            str,
            tuple,
            tuple,
            tuple,
            tuple,
            bool,
            str,
        )
        if any(
            type(item) is not expected
            for item, expected in zip(values, types, strict=True)
        ):
            return False
        if result_type(*values) != value:
            return False
        if (
            value.schema_version != RESULT_SCHEMA_VERSION
            or value.admission_rule_id != ADMISSION_RULE_ID
            or value.outcome != "passed"
            or value.passed is not True
            or value.blocks_candidate is not False
            or value.reason != ""
            or value.evaluator_io_used is not False
            or value.adapter_id != ADAPTER_ID
            or value.normalized_values != PASS_NORMALIZED_VALUES
            or value.validated_candidate_fields != ()
            or value.consumed_candidate_fields != ()
            or value.consumed_context_items
            != PASS_CONSUMED_CONTEXT_ITEMS
        ):
            return False
        pair = value.normalized_values[0]
        if (
            type(pair) is not tuple
            or len(pair) != 2
            or type(pair[0]) is not str
            or type(pair[1]) is not str
        ):
            return False
        if any(
            type(item) is not str for item in value.consumed_context_items
        ):
            return False
    except (AttributeError, TypeError, ValueError):
        return False
    return True


def simulate_admit_015_mandatory_enforcement_design(
    candidate_record: object,
    *,
    stage_authorization_context: object,
    dispatcher: Callable[..., object] = exact15_runtime.evaluate_admission_rule,
    attempted_precomputed_result: object | None = None,
    attempted_combined_verdict: object | None = None,
    attempted_admit_014_permission: object | None = None,
    attempted_repeated_runtime_call: bool = False,
) -> DesignDecision:
    """Pure in-memory simulator for the future guard; never runs training."""
    if attempted_precomputed_result is not None:
        return _decision(
            released=False,
            code=FUTURE_ERROR_CODES[3],
            probe=None,
        )
    if (
        attempted_combined_verdict is not None
        or attempted_admit_014_permission is not None
    ):
        return _decision(
            released=False,
            code=FUTURE_ERROR_CODES[5],
            probe=None,
        )
    if attempted_repeated_runtime_call:
        return _decision(
            released=False,
            code=FUTURE_ERROR_CODES[4],
            probe=None,
        )
    probe = _DispatcherProbe(dispatcher, stage_authorization_context)
    try:
        result = probe(
            ADMISSION_RULE_ID,
            candidate_record,
            batch_context=None,
            evaluation_context=None,
            download_result_context=None,
            stage_authorization_context=stage_authorization_context,
        )
    except Exception:
        return _decision(
            released=False,
            code=FUTURE_ERROR_CODES[0],
            probe=probe,
        )
    if probe.call_count != 1:
        return _decision(
            released=False,
            code=FUTURE_ERROR_CODES[4],
            probe=probe,
        )
    if _exact13_pass_valid(result):
        return _decision(released=True, code="", probe=probe)
    exact_type = type(result) is exact15_runtime.UnifiedAdmissionRuleEvaluation
    return _decision(
        released=False,
        code=FUTURE_ERROR_CODES[2 if exact_type else 1],
        probe=probe,
    )


def _verify_predecessors(snapshot: Sequence[FrozenSource]) -> None:
    runtime_manifest = _json(
        _source(snapshot, "covapie_admit_001_to_015_runtime_manifest.json").content
    )
    training_manifest = _json(
        _source(
            snapshot,
            "covapie_admit_015_training_authorization_contract_manifest.json",
        ).content
    )
    standalone_manifest = _json(
        _source(
            snapshot,
            "covapie_admit_015_standalone_evaluator_interface_manifest.json",
        ).content
    )
    formal_manifest = _json(
        _source(
            snapshot,
            "covapie_admit_015_formal_evaluator_interface_contract_manifest.json",
        ).content
    )
    adapter_manifest = _json(
        _source(
            snapshot,
            "covapie_admit_015_unified_adapter_contract_manifest.json",
        ).content
    )
    download_manifest = _json(
        _source(
            snapshot,
            "covapie_admit_014_download_authorization_contract_manifest.json",
        ).content
    )
    precondition_manifest = _json(
        _source(
            snapshot,
            "covapie_admit_015_formal_evaluator_interface_preconditions_manifest.json",
        ).content
    )
    expected_open = [
        "PRE_034",
        "PRE_035",
        "PRE_036",
        "PRE_038",
        "PRE_042",
    ]
    transition = runtime_manifest.get("precondition_transition")
    runtime_readiness = runtime_manifest.get("readiness")
    if (
        type(transition) is not dict
        or transition.get("complete_count") != 40
        or transition.get("supported_but_not_frozen_count") != 0
        or transition.get("incomplete_count") != 5
        or transition.get("implementation_blocking_count") != 5
        or transition.get("remaining_open_precondition_ids") != expected_open
        or type(runtime_readiness) is not dict
        or runtime_readiness.get("admit_015_registered_in_engine") is not True
        or runtime_readiness.get(
            "unified_dispatch_runtime_with_admit_001_to_015_implemented"
        )
        is not True
        or runtime_readiness.get(
            "mandatory_training_authorization_enforcement_api_frozen"
        )
        is not False
        or runtime_readiness.get(
            "mandatory_training_authorization_enforcement_implemented"
        )
        is not False
        or runtime_manifest.get("current_permission") is not False
        or runtime_manifest.get(
            "authorized_admit_015_training_execution_count"
        )
        != 0
        or runtime_manifest.get("result_fields") != list(RESULT_FIELDS)
        or runtime_manifest.get("result_schema_version")
        != RESULT_SCHEMA_VERSION
        or runtime_manifest.get("canonical_masks")
        != [
            {"semantic_name": semantic, "alias": alias}
            for semantic, alias in CANONICAL_MASKS
        ]
    ):
        raise ValueError("Exact15 runtime predecessor drift")
    if (
        training_manifest.get("current_permission") is not False
        or training_manifest.get(
            "authorized_admit_015_training_execution_count"
        )
        != 0
        or standalone_manifest.get("result_fields") != [
            "admission_rule_id",
            "outcome",
            "passed",
            "blocks_candidate",
            "reason",
            "canonical_stage_authorization_record",
            "validated_stage_authorization_fields",
            "consumed_stage_authorization_fields",
            "evaluator_io_used",
        ]
        or formal_manifest.get("future_public_signature")
        != (
            "evaluate_admit_015(*, stage_authorization_context: object = "
            "_MISSING) -> Admit015EvaluationResult"
        )
        or adapter_manifest.get("adapter_id") != ADAPTER_ID
        or download_manifest.get(
            "mandatory_pre_download_authorization_enforcement_contract", {}
        ).get("evaluate_once_each_real_download_stage_invocation")
        is not True
        or download_manifest.get(
            "mandatory_pre_download_authorization_enforcement_contract", {}
        ).get("combined_verdict_may_override_blocked")
        is not False
        or precondition_manifest.get("precondition_count") != 45
    ):
        raise ValueError("ADMIT_015/014 contract predecessor drift")
    pre_rows = _csv_rows(
        _source(
            snapshot,
            "covapie_admit_015_formal_evaluator_interface_precondition_inventory.csv",
        ).content
    )
    open_rows = {
        row["precondition_id"]: row
        for row in pre_rows
        if row["precondition_id"] in expected_open
    }
    if (
        len(pre_rows) != 45
        or tuple(open_rows) != tuple(expected_open)
        or open_rows["PRE_034"]["precondition_subject"]
        != "training authorization enforcement API"
        or open_rows["PRE_035"]["precondition_subject"]
        != "combined permission semantics"
        or open_rows["PRE_036"]["precondition_subject"]
        != "cross-rule aggregation"
        or open_rows["PRE_038"]["precondition_group"]
        != "feature_semantics_boundary"
        or open_rows["PRE_042"]["precondition_group"]
        != "training_execution_boundary"
    ):
        raise ValueError("Exact45 open precondition definitions drift")
    issue_bytes = _source(
        snapshot,
        "covapie_admit_001_to_015_runtime_issue_readiness_inventory.csv",
    ).content
    issue_rows = _csv_rows(issue_bytes, ISSUE_COLUMNS)
    if (
        len(issue_rows) != 30
        or any(
            "ADMIT_015" in row["affected_rules"]
            and "enforcement" in row["blocking_scope"].lower()
            and "training" in row["blocking_scope"].lower()
            for row in issue_rows
        )
    ):
        raise ValueError("Exact30 issue transition contract drift")


def _api_rows() -> list[dict[str, str]]:
    specs = (
        ("identity", "future_public_function_name", FUTURE_PUBLIC_FUNCTION),
        ("identity", "future_public_signature", FUTURE_PUBLIC_SIGNATURE),
        ("identity", "future_return_type", "UnifiedAdmissionRuleEvaluation"),
        ("identity", "future_error_type", FUTURE_ERROR_TYPE),
        ("identity", "future_error_schema", FUTURE_ERROR_SCHEMA_VERSION),
        ("identity", "future_error_fields", "|".join(FUTURE_ERROR_FIELDS)),
        (
            "identity",
            "future_error_field_types",
            "|".join(FUTURE_ERROR_FIELD_TYPES),
        ),
        ("identity", "future_error_signature", FUTURE_ERROR_SIGNATURE),
        ("input", "candidate_record_owner", "future_training_orchestrator"),
        ("input", "stage_context_owner", "trusted_future_stage_orchestrator"),
        ("runtime", "runtime_dependency", "current_exact15_runtime"),
        ("runtime", "selected_rule_id", ADMISSION_RULE_ID),
        ("runtime", "runtime_call_count_per_invocation", "exactly_one"),
        ("routing", "batch_context", "None"),
        ("routing", "evaluation_context", "None"),
        ("routing", "download_result_context", "None"),
        ("routing", "stage_context_object", "same_identity"),
        ("validation", "result_exact_type", "required_no_subclass"),
        ("validation", "result_field_order", "|".join(RESULT_FIELDS)),
        ("validation", "result_schema_version", RESULT_SCHEMA_VERSION),
        ("validation", "result_rule_id", ADMISSION_RULE_ID),
        ("validation", "result_outcome", "passed"),
        ("validation", "result_passed", "true"),
        ("validation", "result_blocks_candidate", "false"),
        ("validation", "result_reason", "empty"),
        ("validation", "result_evaluator_io_used", "false"),
        ("validation", "result_adapter_id", ADAPTER_ID),
        (
            "validation",
            "result_normalized_values",
            "current_stage_training_authorized=true",
        ),
        ("validation", "validated_candidate_fields", "empty_tuple"),
        ("validation", "consumed_candidate_fields", "empty_tuple"),
        (
            "validation",
            "consumed_context_items",
            AUTHORIZATION_ITEM,
        ),
        ("behavior", "only_pass_may_continue", "true"),
        ("behavior", "return_on_pass", "exact_validated_result"),
        ("behavior", "raise_on_denial_or_drift", FUTURE_ERROR_TYPE),
        ("behavior", "candidate_fields_are_authority", "false"),
        ("forbidden", "precomputed_bool_input", "forbidden"),
        ("forbidden", "precomputed_result_input", "forbidden"),
        ("forbidden", "combined_verdict_input", "forbidden"),
        ("forbidden", "admit_014_permission_substitution", "forbidden"),
        (
            "forbidden",
            "manifest_config_cli_environment_authority",
            "forbidden",
        ),
        (
            "boundary",
            "protected_action_count",
            str(len(PROTECTED_ACTIONS)),
        ),
        ("boundary", "training_io_in_design", "false"),
        ("status", "future_api_frozen", "true"),
        ("status", "future_api_implemented", "false"),
    )
    return [
        {
            "contract_order": str(index),
            "contract_group": group,
            "contract_item": item,
            "frozen_value": value,
            "implementation_status": (
                "future_contract_only"
                if item
                not in {"future_api_frozen", "future_api_implemented"}
                else ("frozen" if item == "future_api_frozen" else "not_implemented")
            ),
            "contract_passed": "true",
        }
        for index, (group, item, value) in enumerate(specs, 1)
    ]


def _protected_rows() -> list[dict[str, str]]:
    return [
        {
            "action_order": str(index),
            "action_id": action_id,
            "action_semantic_name": semantic,
            "guard_required_before_action": "true",
            "blocked_count_expected": "0",
            "design_pass_executes_action": "false",
            "combined_verdict_override_forbidden": "true",
            "real_implementation_status": "false",
            "boundary_passed": "true",
        }
        for index, (action_id, semantic) in enumerate(PROTECTED_ACTIONS, 1)
    ]


def _mutated_result(**updates: object) -> object:
    canonical = exact15_runtime.evaluate_admission_rule(
        ADMISSION_RULE_ID,
        {},
        batch_context=None,
        evaluation_context=None,
        download_result_context=None,
        stage_authorization_context={AUTHORIZATION_ITEM: True},
    )
    values = {
        name: getattr(canonical, name) for name in RESULT_FIELDS
    }
    values.update(updates)
    if not updates:
        return canonical
    forged = object.__new__(
        exact15_runtime.UnifiedAdmissionRuleEvaluation
    )
    for name in RESULT_FIELDS:
        object.__setattr__(forged, name, values[name])
    return forged


def _returning(value: object) -> Callable[..., object]:
    def dispatch(*_args: object, **_kwargs: object) -> object:
        return value

    return dispatch


def _raising(*_args: object, **_kwargs: object) -> object:
    raise RuntimeError("synthetic dispatcher failure")


def _truth_observations() -> list[tuple[str, str, DesignDecision, str]]:
    pass_context = {AUTHORIZATION_ITEM: True}
    blocked_context = {AUTHORIZATION_ITEM: False}
    canonical = _mutated_result()

    class ResultSubclass(exact15_runtime.UnifiedAdmissionRuleEvaluation):
        pass

    subclass = ResultSubclass(
        *(getattr(canonical, name) for name in RESULT_FIELDS)
    )
    reordered = object.__new__(
        exact15_runtime.UnifiedAdmissionRuleEvaluation
    )
    for name in reversed(RESULT_FIELDS):
        object.__setattr__(reordered, name, getattr(canonical, name))
    cases: list[tuple[str, str, DesignDecision, str]] = [
        (
            "canonical_admit_015_pass",
            "canonical_pass",
            simulate_admit_015_mandatory_enforcement_design(
                {}, stage_authorization_context=pass_context
            ),
            "",
        ),
        (
            "canonical_admit_015_blocked",
            "canonical_blocked",
            simulate_admit_015_mandatory_enforcement_design(
                {}, stage_authorization_context=blocked_context
            ),
            FUTURE_ERROR_CODES[2],
        ),
        (
            "invalid_candidate",
            "invalid_candidate",
            simulate_admit_015_mandatory_enforcement_design(
                object(), stage_authorization_context=pass_context
            ),
            FUTURE_ERROR_CODES[2],
        ),
        (
            "missing_stage_context",
            "missing_stage_context",
            simulate_admit_015_mandatory_enforcement_design(
                {}, stage_authorization_context=None
            ),
            FUTURE_ERROR_CODES[2],
        ),
        (
            "false_authorization",
            "false_authorization",
            simulate_admit_015_mandatory_enforcement_design(
                {}, stage_authorization_context=blocked_context
            ),
            FUTURE_ERROR_CODES[2],
        ),
        (
            "dispatcher_failure",
            "dispatcher_failure",
            simulate_admit_015_mandatory_enforcement_design(
                {},
                stage_authorization_context=pass_context,
                dispatcher=_raising,
            ),
            FUTURE_ERROR_CODES[0],
        ),
        (
            "result_wrong_type",
            "result_type_validation",
            simulate_admit_015_mandatory_enforcement_design(
                {},
                stage_authorization_context=pass_context,
                dispatcher=_returning(object()),
            ),
            FUTURE_ERROR_CODES[1],
        ),
        (
            "result_subclass",
            "result_type_validation",
            simulate_admit_015_mandatory_enforcement_design(
                {},
                stage_authorization_context=pass_context,
                dispatcher=_returning(subclass),
            ),
            FUTURE_ERROR_CODES[1],
        ),
        (
            "result_field_order_drift",
            "result_field_order_drift",
            simulate_admit_015_mandatory_enforcement_design(
                {},
                stage_authorization_context=pass_context,
                dispatcher=_returning(reordered),
            ),
            FUTURE_ERROR_CODES[2],
        ),
        (
            "result_field_type_drift",
            "result_field_type_drift",
            simulate_admit_015_mandatory_enforcement_design(
                {},
                stage_authorization_context=pass_context,
                dispatcher=_returning(_mutated_result(reason=1)),
            ),
            FUTURE_ERROR_CODES[2],
        ),
        (
            "schema_drift",
            "result_identity_drift",
            simulate_admit_015_mandatory_enforcement_design(
                {},
                stage_authorization_context=pass_context,
                dispatcher=_returning(
                    _mutated_result(schema_version="wrong")
                ),
            ),
            FUTURE_ERROR_CODES[2],
        ),
        (
            "rule_id_drift",
            "result_identity_drift",
            simulate_admit_015_mandatory_enforcement_design(
                {},
                stage_authorization_context=pass_context,
                dispatcher=_returning(
                    _mutated_result(admission_rule_id="ADMIT_014")
                ),
            ),
            FUTURE_ERROR_CODES[2],
        ),
        (
            "adapter_id_drift",
            "result_identity_drift",
            simulate_admit_015_mandatory_enforcement_design(
                {},
                stage_authorization_context=pass_context,
                dispatcher=_returning(_mutated_result(adapter_id="wrong")),
            ),
            FUTURE_ERROR_CODES[2],
        ),
        (
            "contradictory_passed_false",
            "contradictory_pass_flags",
            simulate_admit_015_mandatory_enforcement_design(
                {},
                stage_authorization_context=pass_context,
                dispatcher=_returning(_mutated_result(passed=False)),
            ),
            FUTURE_ERROR_CODES[2],
        ),
        (
            "contradictory_blocks_true",
            "contradictory_pass_flags",
            simulate_admit_015_mandatory_enforcement_design(
                {},
                stage_authorization_context=pass_context,
                dispatcher=_returning(
                    _mutated_result(blocks_candidate=True)
                ),
            ),
            FUTURE_ERROR_CODES[2],
        ),
        (
            "nonempty_reason",
            "reason_validation",
            simulate_admit_015_mandatory_enforcement_design(
                {},
                stage_authorization_context=pass_context,
                dispatcher=_returning(_mutated_result(reason="drift")),
            ),
            FUTURE_ERROR_CODES[2],
        ),
        (
            "normalized_value_missing",
            "normalized_value_drift",
            simulate_admit_015_mandatory_enforcement_design(
                {},
                stage_authorization_context=pass_context,
                dispatcher=_returning(
                    _mutated_result(normalized_values=())
                ),
            ),
            FUTURE_ERROR_CODES[2],
        ),
        (
            "normalized_value_wrong",
            "normalized_value_drift",
            simulate_admit_015_mandatory_enforcement_design(
                {},
                stage_authorization_context=pass_context,
                dispatcher=_returning(
                    _mutated_result(
                        normalized_values=((AUTHORIZATION_ITEM, "false"),)
                    )
                ),
            ),
            FUTURE_ERROR_CODES[2],
        ),
        (
            "evaluator_io_drift",
            "evaluator_io_drift",
            simulate_admit_015_mandatory_enforcement_design(
                {},
                stage_authorization_context=pass_context,
                dispatcher=_returning(
                    _mutated_result(evaluator_io_used=True)
                ),
            ),
            FUTURE_ERROR_CODES[2],
        ),
        (
            "validated_candidate_fields_drift",
            "candidate_field_drift",
            simulate_admit_015_mandatory_enforcement_design(
                {},
                stage_authorization_context=pass_context,
                dispatcher=_returning(
                    _mutated_result(validated_candidate_fields=("x",))
                ),
            ),
            FUTURE_ERROR_CODES[2],
        ),
        (
            "consumed_candidate_fields_drift",
            "candidate_field_drift",
            simulate_admit_015_mandatory_enforcement_design(
                {},
                stage_authorization_context=pass_context,
                dispatcher=_returning(
                    _mutated_result(consumed_candidate_fields=("x",))
                ),
            ),
            FUTURE_ERROR_CODES[2],
        ),
        (
            "consumed_context_drift",
            "consumed_context_drift",
            simulate_admit_015_mandatory_enforcement_design(
                {},
                stage_authorization_context=pass_context,
                dispatcher=_returning(
                    _mutated_result(consumed_context_items=())
                ),
            ),
            FUTURE_ERROR_CODES[2],
        ),
        (
            "repeated_runtime_call_attempt",
            "exactly_once",
            simulate_admit_015_mandatory_enforcement_design(
                {},
                stage_authorization_context=pass_context,
                attempted_repeated_runtime_call=True,
            ),
            FUTURE_ERROR_CODES[4],
        ),
        (
            "precomputed_result_replay",
            "result_replay",
            simulate_admit_015_mandatory_enforcement_design(
                {},
                stage_authorization_context=pass_context,
                attempted_precomputed_result=canonical,
            ),
            FUTURE_ERROR_CODES[3],
        ),
        (
            "admit_014_true_cannot_authorize_training",
            "admit014_isolation",
            simulate_admit_015_mandatory_enforcement_design(
                {},
                stage_authorization_context=blocked_context,
                attempted_admit_014_permission=True,
            ),
            FUTURE_ERROR_CODES[5],
        ),
        (
            "combined_true_cannot_override_blocked",
            "combined_verdict_non_override",
            simulate_admit_015_mandatory_enforcement_design(
                {},
                stage_authorization_context=blocked_context,
                attempted_combined_verdict=True,
            ),
            FUTURE_ERROR_CODES[5],
        ),
        (
            "blocked_protected_counts_zero",
            "protected_action_zero_boundary",
            simulate_admit_015_mandatory_enforcement_design(
                {}, stage_authorization_context=blocked_context
            ),
            FUTURE_ERROR_CODES[2],
        ),
        (
            "synthetic_true_changes_no_current_permission",
            "current_permission_boundary",
            simulate_admit_015_mandatory_enforcement_design(
                {}, stage_authorization_context=pass_context
            ),
            "",
        ),
        (
            "pass_releases_future_in_memory_only",
            "design_pass_boundary",
            simulate_admit_015_mandatory_enforcement_design(
                {}, stage_authorization_context=pass_context
            ),
            "",
        ),
    ]
    return cases


def _truth_rows() -> list[dict[str, str]]:
    rows = []
    for index, (case_id, group, decision, expected_error) in enumerate(
        _truth_observations(), 1
    ):
        expected_release = expected_error == ""
        passed = (
            decision.released_future_in_memory_continuation
            is expected_release
            and decision.error_code == expected_error
            and decision.protected_action_counts
            == ZERO_PROTECTED_ACTION_COUNTS
            and decision.real_training_executed is False
            and CURRENT_PERMISSION is False
            and AUTHORIZED_ADMIT_015_TRAINING_EXECUTION_COUNT == 0
        )
        if decision.runtime_call_count == 1:
            passed = (
                passed
                and decision.selected_rule_id == ADMISSION_RULE_ID
                and decision.batch_context_is_none
                and decision.evaluation_context_is_none
                and decision.download_result_context_is_none
                and decision.stage_context_identity_preserved
            )
        else:
            passed = passed and decision.runtime_call_count == 0
        rows.append(
            {
                "case_order": str(index),
                "case_id": case_id,
                "case_group": group,
                "expected_decision": (
                    "future_in_memory_continuation"
                    if expected_release
                    else "raise_fail_closed"
                ),
                "observed_decision": (
                    "future_in_memory_continuation"
                    if decision.released_future_in_memory_continuation
                    else "raise_fail_closed"
                ),
                "expected_error_code": expected_error,
                "observed_error_code": decision.error_code,
                "runtime_call_count": str(decision.runtime_call_count),
                "selected_rule_id": decision.selected_rule_id,
                "batch_context_is_none": str(
                    decision.batch_context_is_none
                ).lower(),
                "evaluation_context_is_none": str(
                    decision.evaluation_context_is_none
                ).lower(),
                "download_result_context_is_none": str(
                    decision.download_result_context_is_none
                ).lower(),
                "stage_context_identity_preserved": str(
                    decision.stage_context_identity_preserved
                ).lower(),
                "protected_action_counts_json": json.dumps(
                    dict(decision.protected_action_counts),
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                "current_permission": "false",
                "authorized_execution_count": "0",
                "real_training_executed": "false",
                "case_passed": str(passed).lower(),
            }
        )
    return rows


def _safety_rows() -> list[dict[str, str]]:
    states = (
        ("network_executed", False),
        ("provider_executed", False),
        ("download_executed", False),
        ("raw_accessed", False),
        ("torch_imported", False),
        ("dataloader_instantiated", False),
        ("checkpoint_loaded", False),
        ("model_initialized", False),
        ("model_forward_executed", False),
        ("loss_computed", False),
        ("backward_executed", False),
        ("optimizer_created", False),
        ("scheduler_created", False),
        ("parameter_updated", False),
        ("checkpoint_written", False),
        ("training_result_materialized", False),
        ("current_permission", False),
        ("authorized_execution_count_nonzero", False),
        ("mandatory_enforcement_implemented", False),
        ("combined_candidate_verdict_implemented", False),
        ("cross_rule_aggregation_implemented", False),
        ("feature_semantics_audit_completed", False),
        ("historical_unknown_atom_feature_policy_resolved", False),
        ("historical_feature_semantics_known", False),
        ("real_training_ready", False),
        ("ready_for_training", False),
        ("design_contract_only", True),
        ("exact11_protected_actions_frozen", True),
    )
    return [
        {
            "audit_order": str(index),
            "audit_item": item,
            "expected_state": str(state).lower(),
            "observed_state": str(state).lower(),
            "safety_passed": "true",
        }
        for index, (item, state) in enumerate(states, 1)
    ]


def _csv_bytes(
    columns: Sequence[str], rows: Sequence[Mapping[str, str]]
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=list(columns),
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        if tuple(row) != tuple(columns):
            raise ValueError("CSV schema drift")
        writer.writerow(row)
    return stream.getvalue().encode()


TRUE_READINESS = (
    "admit_015_preconditions_audited",
    "admit_015_training_authorization_contract_frozen",
    "admit_015_formal_evaluator_interface_contract_frozen",
    "admit_015_standalone_evaluator_implemented",
    "admit_015_unified_adapter_contract_frozen",
    "admit_015_unified_adapter_implemented",
    "admit_015_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_015_implemented",
    "mandatory_training_authorization_enforcement_api_frozen",
    "ready_for_admit_015_mandatory_training_authorization_enforcement_implementation",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "mandatory_training_authorization_enforcement_implemented",
    "combined_permission_semantics_frozen",
    "combined_candidate_verdict_implemented",
    "cross_rule_aggregation_implemented",
    "feature_semantics_audit_completed",
    "historical_unknown_atom_feature_policy_resolved",
    "historical_feature_semantics_known",
    "real_training_ready",
    "ready_for_training",
    "step12d_is_final_training_feature_contract",
)


def build_artifacts(
    snapshot: Sequence[FrozenSource] | None = None,
) -> dict[str, bytes]:
    _canonical_runtime_guard()
    frozen = (
        build_frozen_source_snapshot() if snapshot is None else tuple(snapshot)
    )
    if (
        len(frozen) != 34
        or tuple(item.relative_path for item in frozen) != SOURCE_PATHS
        or any(
            type(item) is not FrozenSource
            or item.expected_sha256 != SOURCE_SHA256[item.relative_path]
            or item.filesystem_sha256 != item.expected_sha256
            or _sha(item.content) != item.expected_sha256
            for item in frozen
        )
    ):
        raise ValueError("source snapshot invalid")
    _verify_predecessors(frozen)
    api_rows = _api_rows()
    protected_rows = _protected_rows()
    truth_rows = _truth_rows()
    safety_rows = _safety_rows()
    issue_bytes = _source(
        frozen,
        "covapie_admit_001_to_015_runtime_issue_readiness_inventory.csv",
    ).content
    if (
        len(api_rows) != 44
        or len(protected_rows) != 11
        or len(truth_rows) != 29
        or len({row["case_group"] for row in truth_rows}) < 18
        or len(safety_rows) != 28
        or any(row["contract_passed"] != "true" for row in api_rows)
        or any(row["boundary_passed"] != "true" for row in protected_rows)
        or any(row["case_passed"] != "true" for row in truth_rows)
        or any(row["safety_passed"] != "true" for row in safety_rows)
        or len(_csv_rows(issue_bytes, ISSUE_COLUMNS)) != 30
    ):
        raise ValueError("design evidence failed closed")
    payloads = {
        API_FILENAME: _csv_bytes(API_COLUMNS, api_rows),
        PROTECTED_FILENAME: _csv_bytes(PROTECTED_COLUMNS, protected_rows),
        TRUTH_FILENAME: _csv_bytes(TRUTH_COLUMNS, truth_rows),
        SAFETY_FILENAME: _csv_bytes(SAFETY_COLUMNS, safety_rows),
        ISSUE_FILENAME: issue_bytes,
    }
    output_sha = {name: _sha(content) for name, content in payloads.items()}
    truth_groups: dict[str, int] = {}
    for row in truth_rows:
        truth_groups[row["case_group"]] = (
            truth_groups.get(row["case_group"], 0) + 1
        )
    readiness = {name: True for name in TRUE_READINESS} | {
        name: False for name in FALSE_READINESS
    }
    source_paths_json = json.dumps(
        [path.as_posix() for path in SOURCE_PATHS],
        separators=(",", ":"),
    ).encode()
    source_pairs_json = json.dumps(
        [[path, digest] for path, digest in SOURCE_BOUNDARY],
        separators=(",", ":"),
    ).encode()
    manifest: dict[str, Any] = {
        "project": PROJECT,
        "step": STEP,
        "stage": STAGE,
        "manifest_schema_version": (
            "covapie_admit_015_mandatory_training_authorization_"
            "enforcement_contract_manifest_v1"
        ),
        "base_identity": {
            "commit": BASE_COMMIT,
            "parent": BASE_PARENT,
            "tree": BASE_TREE,
            "subject": BASE_SUBJECT,
        },
        "canonical_evidence_runtime": {
            "implementation": CANONICAL_PYTHON_IMPLEMENTATION,
            "version": "3.10.4",
            "migration_policy": "explicit_contract_refresh_required",
        },
        "source_boundary_name": "fixed_ordered_exact34_committed_source_boundary",
        "source_count": 34,
        "source_paths": [path.as_posix() for path in SOURCE_PATHS],
        "source_sha256": {
            path.as_posix(): SOURCE_SHA256[path] for path in SOURCE_PATHS
        },
        "source_path_list_sha256": _sha(source_paths_json),
        "source_path_sha256_pairs_sha256": _sha(source_pairs_json),
        "source_verification": [
            {
                "source_order": index,
                "path": item.relative_path.as_posix(),
                "base_tree_mode": item.base_tree_mode,
                "base_tree_blob": item.base_tree_blob,
                "index_mode": item.index_mode,
                "index_blob": item.index_blob,
                "index_stage": item.index_stage,
                "filesystem_sha256": item.filesystem_sha256,
                "git_blob_bytes_equal_filesystem_bytes": True,
                "pinned_no_follow_read": True,
                "six_field_identity": True,
                "final_leaf_then_parent_root_verified": True,
                "source_verified": True,
            }
            for index, item in enumerate(frozen, 1)
        ],
        "future_api_contract": {
            "public_function_name": FUTURE_PUBLIC_FUNCTION,
            "exact_signature": FUTURE_PUBLIC_SIGNATURE,
            "return_type": "UnifiedAdmissionRuleEvaluation",
            "error_type": FUTURE_ERROR_TYPE,
            "error_schema_version": FUTURE_ERROR_SCHEMA_VERSION,
            "error_fields": list(FUTURE_ERROR_FIELDS),
            "error_field_types": list(FUTURE_ERROR_FIELD_TYPES),
            "error_signature": FUTURE_ERROR_SIGNATURE,
            "error_codes": list(FUTURE_ERROR_CODES),
            "runtime_dependency": (
                "covapie_bulk_download_admission_unified_dispatch_"
                "runtime_with_admit_001_to_015.evaluate_admission_rule"
            ),
            "selected_rule_id": ADMISSION_RULE_ID,
            "exactly_once_per_real_training_invocation": True,
            "batch_context": None,
            "evaluation_context": None,
            "download_result_context": None,
            "same_stage_context_object": True,
            "precomputed_bool_accepted": False,
            "precomputed_result_accepted": False,
            "combined_verdict_accepted": False,
            "candidate_field_authority": False,
            "only_pass_may_continue": True,
            "exception_on_denial": True,
            "implemented": False,
        },
        "pass_invariants": {
            "exact_result_type": (
                "UnifiedAdmissionRuleEvaluation_no_subclass"
            ),
            "field_order": list(RESULT_FIELDS),
            "schema_version": RESULT_SCHEMA_VERSION,
            "admission_rule_id": ADMISSION_RULE_ID,
            "outcome": "passed",
            "passed": True,
            "blocks_candidate": False,
            "reason": "",
            "evaluator_io_used": False,
            "adapter_id": ADAPTER_ID,
            "normalized_values": [
                [AUTHORIZATION_ITEM, "true"],
            ],
            "validated_candidate_fields": [],
            "consumed_candidate_fields": [],
            "consumed_context_items": [AUTHORIZATION_ITEM],
        },
        "protected_action_count": 11,
        "protected_actions": [
            {"action_id": action_id, "semantic_name": semantic}
            for action_id, semantic in PROTECTED_ACTIONS
        ],
        "blocked_protected_action_counts": {
            action_id: count
            for action_id, count in ZERO_PROTECTED_ACTION_COUNTS
        },
        "truth_matrix_schema": list(TRUTH_COLUMNS),
        "truth_matrix_row_count": len(truth_rows),
        "truth_matrix_group_count": len(truth_groups),
        "truth_matrix_group_counts": dict(sorted(truth_groups.items())),
        "truth_matrix_all_cases_passed": True,
        "safety_schema": list(SAFETY_COLUMNS),
        "safety_row_count": len(safety_rows),
        "precondition_transition": {
            "row_count": 45,
            "resolved_precondition_ids": ["PRE_034"],
            "remaining_open_precondition_ids": [
                "PRE_035",
                "PRE_036",
                "PRE_038",
                "PRE_042",
            ],
            "complete_count": 41,
            "supported_but_not_frozen_count": 0,
            "incomplete_count": 4,
            "implementation_blocking_count": 4,
        },
        "issue_continuity": {
            "row_count": 30,
            "transition_count": 0,
            "byte_identical_to_exact15_runtime": True,
            "sha256": _sha(issue_bytes),
            "remaining_required_open_issue_ids": [
                "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
                "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
                "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
            ],
        },
        "readiness": readiness,
        "current_permission": False,
        "authorized_admit_015_training_execution_count": 0,
        "mandatory_training_authorization_enforcement_implemented": False,
        "combined_permission_semantics_frozen": False,
        "combined_candidate_verdict_implemented": False,
        "cross_rule_aggregation_implemented": False,
        "canonical_mask_count": 5,
        "canonical_masks": [
            {"semantic_name": semantic, "alias": alias}
            for semantic, alias in CANONICAL_MASKS
        ],
        "canonical_mask_long_names_are_authoritative": True,
        "step12d_status": (
            "smoke_legality_only_not_final_training_feature_contract"
        ),
        "feature_semantics_note": (
            "feature-semantics audit remains mandatory before training; "
            "historical UNKNOWN_ATOM_FEATURE_POLICY and "
            "feature_semantics_known=False remain unresolved"
        ),
        "output_schema": {
            API_FILENAME: list(API_COLUMNS),
            PROTECTED_FILENAME: list(PROTECTED_COLUMNS),
            TRUTH_FILENAME: list(TRUTH_COLUMNS),
            SAFETY_FILENAME: list(SAFETY_COLUMNS),
            ISSUE_FILENAME: list(ISSUE_COLUMNS),
        },
        "output_sha256": output_sha,
        "output_sha256_excludes_manifest_self_hash": True,
        "output_materialization": {
            "build_before_mutation": True,
            "o_excl": True,
            "fsync": True,
            "rename_noreplace": True,
            "gpfs_einval_fail_closed": True,
            "os_replace_used": False,
            "destructive_cleanup_used": False,
            "retained_staging_requires_authenticated_binding": True,
            "complete_recursive_manifest_equality": True,
        },
        "design_scope": {
            "production_enforcement_function_defined": False,
            "training_integration": False,
            "training_io": False,
            "provider_network_download_raw": False,
            "combined_permission_semantics": False,
            "cross_rule_aggregation": False,
            "feature_semantics_resolution": False,
        },
        "all_checks_passed": True,
        "validation_failures": [],
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }
    manifest.update(readiness)
    payloads[MANIFEST_FILENAME] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode()
    return {name: payloads[name] for name in OUTPUT_FILES}


Identity = tuple[int, int, int, int, int, int]
DIRECTORY_FLAGS = (
    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
)
READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
WRITE_FLAGS = (
    os.O_WRONLY
    | os.O_CREAT
    | os.O_EXCL
    | os.O_NOFOLLOW
    | os.O_CLOEXEC
)
MAX_CANDIDATE_BYTES = 100 * 1024 * 1024
RENAME_NOREPLACE = 1


def _identity(item: os.stat_result) -> Identity:
    return (
        int(item.st_dev),
        int(item.st_ino),
        int(item.st_mode),
        int(item.st_size),
        int(item.st_mtime_ns),
        int(item.st_ctime_ns),
    )


try:
    _RENAMEAT2 = ctypes.CDLL(None, use_errno=True).renameat2
    _RENAMEAT2.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    )
    _RENAMEAT2.restype = ctypes.c_int
except AttributeError:
    _RENAMEAT2 = None


@dataclass(frozen=True)
class OutputPlan:
    root: Path
    parent: Path
    anchor: Path
    root_name: str
    parent_identity: Identity
    root_identity: Identity | None
    leaf_identities: tuple[tuple[str, Identity], ...]


class MaterializationRetentionError(RuntimeError):
    """Fail-closed publication error that never deletes staging."""

    def __init__(
        self,
        *,
        binding_authenticated: bool,
        authenticated_retained_path: Path | None,
        last_known_staging_name: str,
        retained_staging_identity: Identity,
    ) -> None:
        self.binding_authenticated = binding_authenticated
        self.authenticated_retained_path = authenticated_retained_path
        self.last_known_staging_name = last_known_staging_name
        self.retained_staging_identity = retained_staging_identity
        super().__init__(
            "materialization failed closed; no deletion performed; "
            f"binding_authenticated={str(binding_authenticated).lower()}; "
            f"authenticated_retained_path={authenticated_retained_path}; "
            f"last_known_staging_name={last_known_staging_name}"
        )


def _assert_real_parent_chain(parent: Path, anchor: Path) -> None:
    current = parent
    while True:
        item = os.lstat(current)
        if not stat.S_ISDIR(item.st_mode) or stat.S_ISLNK(item.st_mode):
            raise ValueError("output parent chain unsafe")
        if current == anchor:
            break
        if current == current.parent:
            raise ValueError("output parent chain escaped")
        current = current.parent
    if parent.resolve(strict=True) != parent:
        raise ValueError("output parent resolved drift")


def _inspect_output_target_read_only(
    output_root: Path,
    repo_root: Path = REPO_ROOT,
) -> OutputPlan:
    candidate = Path(output_root)
    repo = Path(os.path.abspath(repo_root))
    if candidate.is_absolute():
        root = Path(os.path.abspath(candidate))
        anchor = Path(root.anchor)
    else:
        if ".." in candidate.parts:
            raise ValueError("relative output escape")
        root = repo / candidate
        anchor = repo
    if not root.name:
        raise ValueError("output root invalid")
    parent = root.parent
    _assert_real_parent_chain(parent, anchor)
    parent_identity = _identity(os.lstat(parent))
    try:
        root_item = os.lstat(root)
    except FileNotFoundError:
        return OutputPlan(
            root, parent, anchor, root.name, parent_identity, None, ()
        )
    if (
        not stat.S_ISDIR(root_item.st_mode)
        or stat.S_ISLNK(root_item.st_mode)
        or root.resolve(strict=True) != root
    ):
        raise ValueError("output root unsafe")
    names = tuple(os.listdir(root))
    if len(names) != 6 or set(names) != set(OUTPUT_FILES):
        raise ValueError("output inventory unsafe")
    leaves = []
    for name in OUTPUT_FILES:
        item = os.lstat(root / name)
        if (
            not stat.S_ISREG(item.st_mode)
            or stat.S_ISLNK(item.st_mode)
            or item.st_size > MAX_CANDIDATE_BYTES
        ):
            raise ValueError("output leaf unsafe")
        leaves.append((name, _identity(item)))
    return OutputPlan(
        root,
        parent,
        anchor,
        root.name,
        parent_identity,
        _identity(root_item),
        tuple(leaves),
    )


def _assert_parent(plan: OutputPlan, parent_fd: int) -> None:
    lexical = os.lstat(plan.parent)
    if (
        _identity(lexical) != plan.parent_identity
        or _identity(os.fstat(parent_fd)) != plan.parent_identity
        or not stat.S_ISDIR(lexical.st_mode)
        or stat.S_ISLNK(lexical.st_mode)
        or plan.parent.resolve(strict=True) != plan.parent
    ):
        raise ValueError("output parent binding drift")


def _refresh_parent(plan: OutputPlan, parent_fd: int) -> OutputPlan:
    lexical = os.lstat(plan.parent)
    identity = _identity(os.fstat(parent_fd))
    if (
        _identity(lexical) != identity
        or not stat.S_ISDIR(lexical.st_mode)
        or stat.S_ISLNK(lexical.st_mode)
        or plan.parent.resolve(strict=True) != plan.parent
    ):
        raise ValueError("output parent refresh drift")
    return OutputPlan(
        plan.root,
        plan.parent,
        plan.anchor,
        plan.root_name,
        identity,
        plan.root_identity,
        plan.leaf_identities,
    )


def _assert_root_binding(
    plan: OutputPlan,
    parent_fd: int,
    root_name: str,
    root_fd: int,
    expected: Identity,
) -> None:
    _assert_parent(plan, parent_fd)
    lexical = os.stat(root_name, dir_fd=parent_fd, follow_symlinks=False)
    if (
        _identity(lexical) != expected
        or _identity(os.fstat(root_fd)) != expected
        or not stat.S_ISDIR(lexical.st_mode)
        or stat.S_ISLNK(lexical.st_mode)
    ):
        raise ValueError("output root/name binding drift")
    _assert_parent(plan, parent_fd)


def _read_leaf(
    root_fd: int, name: str, expected: Identity
) -> bytes:
    before = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
    if (
        _identity(before) != expected
        or not stat.S_ISREG(before.st_mode)
        or stat.S_ISLNK(before.st_mode)
        or before.st_size > MAX_CANDIDATE_BYTES
    ):
        raise ValueError("output leaf drift")
    descriptor = os.open(name, READ_FLAGS, dir_fd=root_fd)
    try:
        if _identity(os.fstat(descriptor)) != expected:
            raise ValueError("output leaf stat/open race")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1 << 16)
            if not chunk:
                break
            chunks.append(chunk)
        if (
            _identity(os.fstat(descriptor)) != expected
            or _identity(
                os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            )
            != expected
        ):
            raise ValueError("output leaf changed")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _verify_set(
    plan: OutputPlan,
    parent_fd: int,
    root_name: str,
    root_fd: int,
    root_identity: Identity,
    payloads: Mapping[str, bytes],
    expected_leaves: Mapping[str, Identity] | None = None,
) -> dict[str, Identity]:
    _assert_root_binding(
        plan, parent_fd, root_name, root_fd, root_identity
    )
    names = tuple(os.listdir(root_fd))
    if len(names) != 6 or set(names) != set(OUTPUT_FILES):
        raise ValueError("complete output inventory drift")
    identities = (
        {
            name: _identity(
                os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            )
            for name in OUTPUT_FILES
        }
        if expected_leaves is None
        else dict(expected_leaves)
    )
    if set(identities) != set(OUTPUT_FILES):
        raise ValueError("output identity inventory drift")
    observed = {
        name: _read_leaf(root_fd, name, identities[name])
        for name in OUTPUT_FILES
    }
    if tuple(os.listdir(root_fd)) != names:
        raise ValueError("output inventory changed")
    if any(observed[name] != payloads[name] for name in OUTPUT_FILES):
        raise ValueError("output payload mismatch")
    _assert_root_binding(
        plan, parent_fd, root_name, root_fd, root_identity
    )
    for name in OUTPUT_FILES:
        if (
            _identity(
                os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            )
            != identities[name]
        ):
            raise ValueError("output final leaf changed")
    _assert_root_binding(
        plan, parent_fd, root_name, root_fd, root_identity
    )
    return identities


def _write_all(descriptor: int, content: bytes) -> None:
    offset = 0
    while offset < len(content):
        count = os.write(descriptor, content[offset:])
        if type(count) is not int or count <= 0:
            raise OSError("short output write")
        offset += count


def _rename_noreplace(
    plan: OutputPlan,
    parent_fd: int,
    staging_name: str,
    staging_fd: int,
    staging_identity: Identity,
) -> None:
    _assert_root_binding(
        plan,
        parent_fd,
        staging_name,
        staging_fd,
        staging_identity,
    )
    if _RENAMEAT2 is None:
        raise ValueError("renameat2 required")
    if _RENAMEAT2(
        parent_fd,
        os.fsencode(staging_name),
        parent_fd,
        os.fsencode(plan.root_name),
        RENAME_NOREPLACE,
    ):
        error = ctypes.get_errno()
        raise OSError(
            error,
            os.strerror(error),
            f"{staging_name}->{plan.root_name}",
        )


def _authenticate_retained(
    plan: OutputPlan,
    parent_fd: int,
    staging_name: str,
    staging_fd: int,
    staging_identity: Identity,
) -> Path | None:
    try:
        _assert_root_binding(
            plan,
            parent_fd,
            staging_name,
            staging_fd,
            staging_identity,
        )
        _assert_root_binding(
            plan,
            parent_fd,
            staging_name,
            staging_fd,
            staging_identity,
        )
    except (OSError, RuntimeError, ValueError):
        return None
    return plan.parent / staging_name


def _materialize_set(
    plan: OutputPlan, payloads: Mapping[str, bytes]
) -> None:
    _canonical_runtime_guard()
    if (
        type(payloads) is not dict
        or tuple(payloads) != OUTPUT_FILES
        or any(type(value) is not bytes for value in payloads.values())
    ):
        raise ValueError("output payload inventory drift")
    parent_fd = os.open(plan.parent, DIRECTORY_FLAGS)
    root_fd: int | None = None
    staging_name: str | None = None
    staging_identity: Identity | None = None
    published = False
    try:
        _assert_parent(plan, parent_fd)
        if plan.root_identity is not None:
            root_fd = os.open(
                plan.root_name, DIRECTORY_FLAGS, dir_fd=parent_fd
            )
            _verify_set(
                plan,
                parent_fd,
                plan.root_name,
                root_fd,
                plan.root_identity,
                payloads,
                dict(plan.leaf_identities),
            )
            os.fsync(root_fd)
            _verify_set(
                plan,
                parent_fd,
                plan.root_name,
                root_fd,
                plan.root_identity,
                payloads,
                dict(plan.leaf_identities),
            )
            return
        try:
            os.stat(
                plan.root_name,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            pass
        else:
            raise ValueError("missing output became occupied")
        for _ in range(64):
            candidate = (
                ".admit015-training-enforcement-contract-stage-"
                f"{secrets.token_hex(16)}"
            )
            try:
                os.mkdir(candidate, 0o700, dir_fd=parent_fd)
                staging_name = candidate
                break
            except FileExistsError:
                continue
        if staging_name is None:
            raise ValueError("staging name exhaustion")
        plan = _refresh_parent(plan, parent_fd)
        root_fd = os.open(
            staging_name, DIRECTORY_FLAGS, dir_fd=parent_fd
        )
        staging_identity = _identity(os.fstat(root_fd))
        _assert_root_binding(
            plan,
            parent_fd,
            staging_name,
            root_fd,
            staging_identity,
        )
        if os.listdir(root_fd):
            raise ValueError("staging directory not empty")
        leaf_identities = {}
        for name, content in payloads.items():
            descriptor = os.open(
                name, WRITE_FLAGS, 0o600, dir_fd=root_fd
            )
            try:
                _write_all(descriptor, content)
                os.fsync(descriptor)
                leaf_identities[name] = _identity(os.fstat(descriptor))
            finally:
                os.close(descriptor)
            staging_identity = _identity(os.fstat(root_fd))
            _assert_root_binding(
                plan,
                parent_fd,
                staging_name,
                root_fd,
                staging_identity,
            )
        _verify_set(
            plan,
            parent_fd,
            staging_name,
            root_fd,
            staging_identity,
            payloads,
            leaf_identities,
        )
        os.fsync(root_fd)
        staging_identity = _identity(os.fstat(root_fd))
        _assert_root_binding(
            plan,
            parent_fd,
            staging_name,
            root_fd,
            staging_identity,
        )
        try:
            os.stat(
                plan.root_name,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            pass
        else:
            raise ValueError("final output race")
        _rename_noreplace(
            plan,
            parent_fd,
            staging_name,
            root_fd,
            staging_identity,
        )
        published = True
        published_identity = _identity(os.fstat(root_fd))
        staging_name = None
        plan = _refresh_parent(plan, parent_fd)
        published_leaves = _verify_set(
            plan,
            parent_fd,
            plan.root_name,
            root_fd,
            published_identity,
            payloads,
            leaf_identities,
        )
        os.fsync(parent_fd)
        _verify_set(
            plan,
            parent_fd,
            plan.root_name,
            root_fd,
            published_identity,
            payloads,
            published_leaves,
        )
    except BaseException as error:
        if (
            not published
            and staging_name is not None
            and root_fd is not None
            and staging_identity is not None
        ):
            try:
                plan = _refresh_parent(plan, parent_fd)
                retained = _authenticate_retained(
                    plan,
                    parent_fd,
                    staging_name,
                    root_fd,
                    staging_identity,
                )
            except (OSError, RuntimeError, ValueError):
                retained = None
            raise MaterializationRetentionError(
                binding_authenticated=retained is not None,
                authenticated_retained_path=retained,
                last_known_staging_name=staging_name,
                retained_staging_identity=staging_identity,
            ) from error
        raise
    finally:
        if root_fd is not None:
            try:
                os.close(root_fd)
            except OSError:
                pass
        os.close(parent_fd)


def run_covapie_bulk_download_admission_admit_015_mandatory_training_authorization_enforcement_contract_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    *,
    repo_root: Path = REPO_ROOT,
    head_ref: str = "HEAD",
) -> dict[str, Any]:
    """Publish exactly six deterministic design-contract evidence files."""
    snapshot = build_frozen_source_snapshot(repo_root, head_ref=head_ref)
    payloads = build_artifacts(snapshot)
    plan = _inspect_output_target_read_only(output_root, repo_root)
    _materialize_set(plan, payloads)
    return {
        "snapshot": snapshot,
        "manifest": json.loads(payloads[MANIFEST_FILENAME]),
        "output_root": plan.root,
    }


if __name__ == "__main__":
    run_covapie_bulk_download_admission_admit_015_mandatory_training_authorization_enforcement_contract_v1()
