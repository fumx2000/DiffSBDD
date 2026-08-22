"""Batch001 exact13 model-usable split and train5 activation boundary V1.

This additive owner consumes the published NDU4 formal split authority.  It
reuses the published structural/preview tensorization path for all three
splits and the already-proven train5 supervision-cloning semantics for the
formal train population.  Validation and test retain labels while every
training loss mask remains inactive.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Mapping, NoReturn, Sequence

import torch

from covalent_ext import covapie_batch001_positive_structural_input_v1 as structural_owner
from covalent_ext import (
    covapie_batch001_to_existing_mixed_profile_supervision_bridge_v1
    as preview_owner,
)
from covalent_ext import (
    covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1
    as train5_predecessor,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


__all__ = (
    "BATCH001_13EVENT_MODEL_USABLE_SPLIT_BOUNDARY_ERROR_V1",
    "FORMAL_TRAIN_EVENT_IDS_V1",
    "FORMAL_VALIDATION_EVENT_IDS_V1",
    "FORMAL_TEST_EVENT_IDS_V1",
    "OUTPUT_ROOT_RELATIVE_V1",
    "OUTPUT_FILENAMES_V1",
    "CovapieBatch001ModelUsableSourceBindingV1",
    "CovapieBatch001FormalSplitRowV1",
    "CovapieBatch001FormalSplitAuthorityV1",
    "CovapieBatch001ModelUsableSplitBatchV1",
    "verify_covapie_batch001_model_usable_source_bindings_v1",
    "load_covapie_batch001_formal_split_authority_v1",
    "validate_covapie_batch001_formal_split_authority_v1",
    "validate_covapie_batch001_training_activation_population_v1",
    "build_covapie_batch001_model_usable_split_batch_v1",
    "validate_covapie_batch001_model_usable_split_batch_v1",
    "build_covapie_batch001_model_usable_split_artifacts_v1",
    "validate_covapie_batch001_model_usable_split_artifacts_v1",
    "materialize_covapie_batch001_model_usable_split_artifacts_v1",
)


BATCH001_13EVENT_MODEL_USABLE_SPLIT_BOUNDARY_ERROR_V1 = (
    "COVAPIE_BATCH001_13EVENT_MODEL_USABLE_SPLIT_MATERIALIZATION_AND_"
    "ACTIVATION_BOUNDARY_V1_ERROR"
)
BASELINE_HEAD_V1 = "fe034ea1b4e0e925cd8197c37f08c8675fa26cca"
FORMAL_VALIDATION_TASK_POLICY_V1 = (
    "ALL_APPLICABLE_TASKS_BY_PUBLISHED_FORMAL_EVALUATOR"
)
FORMAL_TEST_TASK_POLICY_V1 = "HELD_OUT_TEST_SPLIT_NO_FORMAL_TEST_EVALUATOR_YET"
TRAIN_ACTIVATION_REASON_V1 = (
    "EXACT_FORMAL_TRAIN5_MODEL_TRAINING_ACTIVATION_AUTHORIZED_V1"
)
VALIDATION_HOLDOUT_REASON_V1 = "FORMAL_VALIDATION4_HELD_OUT_TRAINING_INACTIVE_V1"
TEST_HOLDOUT_REASON_V1 = "FORMAL_TEST4_HELD_OUT_TRAINING_INACTIVE_V1"

FORMAL_TRAIN_EVENT_IDS_V1 = (
    "COVAPIE_CYS_SG_EVENT_V1:3LOK:A:CYS:345-:SG:C:DJK:C51",
    "COVAPIE_CYS_SG_EVENT_V1:3LOK:B:CYS:345-:SG:D:DJK:C51",
    "COVAPIE_CYS_SG_EVENT_V1:2ZK1:A:CYS:285-:SG:C:PTG:C8",
    "COVAPIE_CYS_SG_EVENT_V1:2ZK1:B:CYS:285-:SG:D:PTG:C8",
    "COVAPIE_CYS_SG_EVENT_V1:2ZK2:A:CYS:285-:SG:D:PTG:C8",
)
FORMAL_VALIDATION_EVENT_IDS_V1 = (
    "COVAPIE_CYS_SG_EVENT_V1:3I4A:A:CYS:274-:SG:C:LN5:CZ",
    "COVAPIE_CYS_SG_EVENT_V1:3I4A:B:CYS:274-:SG:D:LN5:CZ",
    "COVAPIE_CYS_SG_EVENT_V1:3O6T:A:CYS:37-:SG:E:PX5:C15",
    "COVAPIE_CYS_SG_EVENT_V1:3O6T:C:CYS:37-:SG:G:PX5:C15",
)
FORMAL_TEST_EVENT_IDS_V1 = (
    "COVAPIE_CYS_SG_EVENT_V1:3B9H:A:CYS:146-:SG:D:NDU:C6",
    "COVAPIE_CYS_SG_EVENT_V1:3BHL:A:CYS:146-:SG:C:NDU:C6",
    "COVAPIE_CYS_SG_EVENT_V1:3BHL:B:CYS:146-:SG:G:NDU:C6",
    "COVAPIE_CYS_SG_EVENT_V1:3BHR:A:CYS:146-:SG:E:NDU:C6",
)
_EXPECTED_SPLIT_IDS_V1 = (
    ("train", FORMAL_TRAIN_EVENT_IDS_V1),
    ("validation", FORMAL_VALIDATION_EVENT_IDS_V1),
    ("test", FORMAL_TEST_EVENT_IDS_V1),
)
_EXPECTED_COMPONENT_BY_ID_V1 = {
    event_id: event_id.split(":")[-2]
    for _, event_ids in _EXPECTED_SPLIT_IDS_V1
    for event_id in event_ids
}

OUTPUT_ROOT_RELATIVE_V1 = Path(
    "data/derived/covalent_small/"
    "covapie_batch001_13event_model_usable_split_materialization_and_"
    "activation_boundary_v1"
)
SPLIT_INDEX_V1 = "covapie_batch001_13event_model_usable_split_index_v1.csv"
SPLIT_REGISTRY_V1 = "covapie_batch001_model_usable_split_registry_v1.json"
SOURCE_BINDING_INVENTORY_V1 = (
    "covapie_batch001_model_usable_source_binding_inventory_v1.csv"
)
MANIFEST_V1 = (
    "covapie_batch001_13event_model_usable_split_materialization_and_"
    "activation_boundary_manifest_v1.json"
)
OUTPUT_FILENAMES_V1 = (
    SPLIT_INDEX_V1,
    SPLIT_REGISTRY_V1,
    SOURCE_BINDING_INVENTORY_V1,
    MANIFEST_V1,
)

_FORMAL_ROOT_V1 = Path(
    "data/derived/covalent_small/"
    "covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_v1"
)
_FORMAL_EVENT_PATH_V1 = (
    _FORMAL_ROOT_V1 / "covapie_batch001_ndu4_formal_event_split_admission_v1.csv"
)
_SOURCE_BINDING_SPECS_V1 = (
    (
        "PUBLISHED_FORMAL_SPLIT_AUTHORITY",
        _FORMAL_EVENT_PATH_V1.as_posix(),
        "944fd8447aead448a6f825296872dfb7a2d4e24733dfeede5c93553b45bcdff5",
        "exact13 formal event split membership and admission authority",
    ),
    (
        "PUBLISHED_FORMAL_COMPONENT_REGISTRY",
        (_FORMAL_ROOT_V1 / "covapie_batch001_ndu4_full_component_registry_v1.json").as_posix(),
        "3f0edbca6d2b43226321ac71e46b593029e18bc31ddc4693d6077530fe7996d2",
        "formal leakage-group classification and isolation lineage",
    ),
    (
        "PUBLISHED_RECOVERY_EVIDENCE",
        (_FORMAL_ROOT_V1 / "covapie_batch001_ndu4_leakage_recovery_evidence_v1.csv").as_posix(),
        "11fe6752a5269aedc8a18599b6cdc8ef860bd8586835654b1732bad680980f0f",
        "NDU4 recovery provenance lineage without recomputation",
    ),
    (
        "PUBLISHED_FORMAL_SOURCE_INVENTORY",
        (_FORMAL_ROOT_V1 / "covapie_batch001_ndu4_source_binding_inventory_v1.csv").as_posix(),
        "90658ab0803fbaee9f65e3837ca702cd66adb421bea5f8aa1102c490fe6d89a1",
        "published split authority source lineage",
    ),
    (
        "PUBLISHED_FORMAL_MANIFEST",
        (_FORMAL_ROOT_V1 / "covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_manifest_v1.json").as_posix(),
        "5e4eb3007c3434879ff7fc7506487406a268060979ffd1cb879a5e6a7b9dfeb8",
        "published successor counts, readiness, and safety contract",
    ),
    (
        "STRUCTURAL_INPUT_OWNER",
        "src/covalent_ext/covapie_batch001_positive_structural_input_v1.py",
        "c4cada3c5d3e8e86176b097cc5546854122162055437e4667288ba2f82629067",
        "exact13 retained ligand and pocket structural records",
    ),
    (
        "MIXED_PROFILE_PREVIEW_OWNER",
        "src/covalent_ext/covapie_batch001_to_existing_mixed_profile_supervision_bridge_v1.py",
        "168c819e0422b110880676c1a99b82a8531e94f9849a3dcfb7d4c45dbdd73400",
        "model inputs, role masks, labels, and inactive preview supervision",
    ),
    (
        "CURRENT11_TRAINING_TENSORIZER",
        "src/covalent_ext/covapie_current11_training_tensorizer_v1.py",
        "9fdc3f7f101fab5e5e5452e3d8e9f9b0b1e6e5fa8254a261f36310a1dfd0b606",
        "unchanged 37-field supervision tensor carrier",
    ),
    (
        "DIRECT_ATTACHMENT_RUNTIME",
        "src/covalent_ext/covapie_direct_attachment_optional_linker_runtime_v1.py",
        "434285a43fa0158e62d40f48ed95d137f5fd68ea9b00101cc20674025849c535",
        "role-profile task applicability and deterministic task scheduler",
    ),
    (
        "PAIR_LABEL_OWNER",
        "src/covalent_ext/covapie_tensor_label_and_loss_mask_contract_design_v1.py",
        "3d2d03cda56dfb4a54370444f255f9bb0ab433aaeb837901e769098272ff51ac",
        "pair candidate and positive-label projection semantics",
    ),
    (
        "TRAIN5_ADMISSION_PREDECESSOR",
        "src/covalent_ext/covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1.py",
        "3f19d39148f374d14744fa714a2e7d648a37099168d539c14e7e2320d390ec21",
        "already-proven exact train5 supervision activation cloning semantics",
    ),
)

_DEFAULT_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_CACHE_ROOT = (
    _DEFAULT_REPOSITORY_ROOT.parent
    / "covapie-state/bulk-multisource-cys-sg-v1/rcsb"
)
_PATH_TYPE = type(Path())


@dataclass(frozen=True)
class CovapieBatch001ModelUsableSourceBindingV1:
    source_category: str
    source_root_kind: str
    relative_path: str
    sha256: str
    consumed_for: str
    sha256_verified: bool


@dataclass(frozen=True)
class CovapieBatch001FormalSplitRowV1:
    canonical_event_id: str
    ligand_component_id: str
    leakage_classification: str
    formal_leakage_group_id: str
    formal_split: str
    model_integration_preview_ready: bool
    split_admission_authoritative: bool
    split_admission_status: str
    predecessor_sample_training_admitted: bool
    predecessor_model_training_activation_authorized: bool


@dataclass(frozen=True)
class CovapieBatch001FormalSplitAuthorityV1:
    rows: tuple[CovapieBatch001FormalSplitRowV1, ...]
    train_event_ids: tuple[str, ...]
    validation_event_ids: tuple[str, ...]
    test_event_ids: tuple[str, ...]
    source_bindings: tuple[CovapieBatch001ModelUsableSourceBindingV1, ...]
    event_identity_intersection_counts: tuple[tuple[str, int], ...]
    formal_leakage_group_cross_split_violation_count: int


@dataclass(frozen=True)
class CovapieBatch001ModelUsableSplitBatchV1:
    formal_split: str
    sample_identities: tuple[str, ...]
    role_profiles: tuple[str, ...]
    applicable_task_ids: tuple[tuple[int, ...], ...]
    training_scheduled_task_ids: tuple[int | None, ...]
    preview_tensorization_task_ids: tuple[int, ...]
    epoch: int
    task_schedule_seed: int
    structural_records: tuple[
        structural_owner.CovapieBatch001PositiveStructuralRecordV1, ...
    ]
    model_input_batch: dict[str, object]
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1
    split_admission_authoritative: tuple[bool, ...]
    model_usable: tuple[bool, ...]
    sample_training_admitted: tuple[bool, ...]
    model_training_activation_authorized: tuple[bool, ...]
    optimizer_population_eligible: tuple[bool, ...]
    formal_validation_population_member: tuple[bool, ...]
    formal_test_population_member: tuple[bool, ...]
    training_scheduler_eligible: tuple[bool, ...]
    activation_reasons: tuple[str, ...]
    formal_validation_task_policy: str
    formal_test_task_policy: str
    source_authority_bindings: tuple[CovapieBatch001ModelUsableSourceBindingV1, ...]


@dataclass(frozen=True)
class _BuildContextV1:
    repository_root: Path
    cache_root: Path
    authority: CovapieBatch001FormalSplitAuthorityV1
    records_by_identity: Mapping[
        str, structural_owner.CovapieBatch001PositiveStructuralRecordV1
    ]


class _BoundaryInvariantError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _fail(reason: str) -> NoReturn:
    raise _BoundaryInvariantError(reason)


def _public_error(error: BaseException) -> NoReturn:
    if type(error) is ValueError and str(error).startswith(
        BATCH001_13EVENT_MODEL_USABLE_SPLIT_BOUNDARY_ERROR_V1
    ):
        raise error
    reason = error.reason if isinstance(error, _BoundaryInvariantError) else "OWNER_REJECTED"
    raise ValueError(
        f"{BATCH001_13EVENT_MODEL_USABLE_SPLIT_BOUNDARY_ERROR_V1}:{reason}"
    ) from error


def _require_directory(value: object, *, default: Path, reason: str) -> Path:
    path = default if value is None else value
    if type(path) is not _PATH_TYPE or not path.is_absolute():
        _fail(reason)
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise _BoundaryInvariantError(reason) from error
    if resolved != path or path.is_symlink() or not path.is_dir():
        _fail(reason)
    return path


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    try:
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            _fail("BOUND_SOURCE_NOT_SAFE_REGULAR_FILE")
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError as error:
        raise _BoundaryInvariantError("BOUND_SOURCE_READ_FAILED") from error


def verify_covapie_batch001_model_usable_source_bindings_v1(
    *, repository_root: object = None
) -> tuple[CovapieBatch001ModelUsableSourceBindingV1, ...]:
    """Verify every direct semantic source before materialization or activation."""

    try:
        repo = _require_directory(
            repository_root,
            default=_DEFAULT_REPOSITORY_ROOT,
            reason="REPOSITORY_ROOT_INVALID",
        )
        bindings = []
        for category, relative, expected, consumed_for in _SOURCE_BINDING_SPECS_V1:
            actual = _sha256_file(repo / relative)
            if actual != expected:
                _fail("SOURCE_BINDING_SHA256_MISMATCH:" + relative)
            bindings.append(CovapieBatch001ModelUsableSourceBindingV1(
                source_category=category,
                source_root_kind="REPOSITORY",
                relative_path=relative,
                sha256=actual,
                consumed_for=consumed_for,
                sha256_verified=True,
            ))
        return tuple(bindings)
    except BaseException as error:
        _public_error(error)


def _bool_text(value: object, reason: str) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    _fail(reason)


def _read_formal_rows(
    repository_root: Path,
) -> tuple[CovapieBatch001FormalSplitRowV1, ...]:
    path = repository_root / _FORMAL_EVENT_PATH_V1
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            raw_rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as error:
        raise _BoundaryInvariantError("FORMAL_AUTHORITY_CSV_INVALID") from error
    required = {
        "canonical_event_id",
        "ligand_component_id",
        "leakage_classification",
        "formal_leakage_group_id",
        "assigned_split",
        "model_integration_preview_ready",
        "split_admission_authoritative",
        "split_admission_status",
        "sample_training_admitted",
        "model_training_activation_authorized",
    }
    if len(raw_rows) != 13 or not reader.fieldnames or not required.issubset(reader.fieldnames):
        _fail("FORMAL_AUTHORITY_SCHEMA_OR_COUNT_INVALID")
    return tuple(CovapieBatch001FormalSplitRowV1(
        canonical_event_id=row["canonical_event_id"],
        ligand_component_id=row["ligand_component_id"],
        leakage_classification=row["leakage_classification"],
        formal_leakage_group_id=row["formal_leakage_group_id"],
        formal_split=row["assigned_split"],
        model_integration_preview_ready=_bool_text(
            row["model_integration_preview_ready"], "FORMAL_AUTHORITY_BOOLEAN_INVALID"
        ),
        split_admission_authoritative=_bool_text(
            row["split_admission_authoritative"], "FORMAL_AUTHORITY_BOOLEAN_INVALID"
        ),
        split_admission_status=row["split_admission_status"],
        predecessor_sample_training_admitted=_bool_text(
            row["sample_training_admitted"], "FORMAL_AUTHORITY_BOOLEAN_INVALID"
        ),
        predecessor_model_training_activation_authorized=_bool_text(
            row["model_training_activation_authorized"],
            "FORMAL_AUTHORITY_BOOLEAN_INVALID",
        ),
    ) for row in raw_rows)


def _validate_authority_impl(
    authority: CovapieBatch001FormalSplitAuthorityV1,
) -> bool:
    if type(authority) is not CovapieBatch001FormalSplitAuthorityV1:
        _fail("FORMAL_AUTHORITY_TYPE_INVALID")
    rows = authority.rows
    identities = tuple(row.canonical_event_id for row in rows)
    if (
        len(rows) != 13
        or identities != structural_owner.BATCH001_POSITIVE_EVENT_IDS_V1
        or len(set(identities)) != 13
        or set(identities)
        != set(FORMAL_TRAIN_EVENT_IDS_V1 + FORMAL_VALIDATION_EVENT_IDS_V1 + FORMAL_TEST_EVENT_IDS_V1)
    ):
        _fail("FORMAL_AUTHORITY_EXACT13_POPULATION_INVALID")
    derived = tuple(
        tuple(row.canonical_event_id for row in rows if row.formal_split == split)
        for split, _ in _EXPECTED_SPLIT_IDS_V1
    )
    expected = tuple(event_ids for _, event_ids in _EXPECTED_SPLIT_IDS_V1)
    if derived != expected or (
        authority.train_event_ids,
        authority.validation_event_ids,
        authority.test_event_ids,
    ) != expected:
        _fail("FORMAL_SPLIT_IDENTITY_OR_ORDER_INVALID")
    if any(
        row.ligand_component_id != _EXPECTED_COMPONENT_BY_ID_V1[row.canonical_event_id]
        or not row.model_integration_preview_ready
        or not row.split_admission_authoritative
        or row.split_admission_status
        not in {
            "FORMALLY_ADMITTED_TO_FROZEN_SPLIT",
            "FORMALLY_ADMITTED_TO_EXISTING_FROZEN_SPLIT",
        }
        or row.predecessor_sample_training_admitted
        or row.predecessor_model_training_activation_authorized
        for row in rows
    ):
        _fail("FORMAL_AUTHORITY_ROW_SEMANTICS_INVALID")
    test_rows = tuple(row for row in rows if row.canonical_event_id in FORMAL_TEST_EVENT_IDS_V1)
    if any(
        row.formal_split != "test"
        or row.ligand_component_id != "NDU"
        or row.formal_leakage_group_id != "COVAPIE_LEAKAGE_GROUP_000005"
        or row.leakage_classification != "HISTORICAL_BASELINE_COMPONENT"
        for row in test_rows
    ):
        _fail("NDU4_FORMAL_TEST_AUTHORITY_INVALID")
    split_sets = {split: set(event_ids) for split, event_ids in _EXPECTED_SPLIT_IDS_V1}
    intersections = (
        ("train_validation", len(split_sets["train"] & split_sets["validation"])),
        ("train_test", len(split_sets["train"] & split_sets["test"])),
        ("validation_test", len(split_sets["validation"] & split_sets["test"])),
    )
    if authority.event_identity_intersection_counts != intersections or any(
        count != 0 for _, count in intersections
    ):
        _fail("FORMAL_SPLIT_EVENT_IDENTITY_INTERSECTION_INVALID")
    group_splits: dict[str, set[str]] = {}
    for row in rows:
        group_splits.setdefault(row.formal_leakage_group_id, set()).add(row.formal_split)
    violations = sum(len(splits) != 1 for splits in group_splits.values())
    if violations != 0 or authority.formal_leakage_group_cross_split_violation_count != 0:
        _fail("FORMAL_LEAKAGE_GROUP_CROSSES_SPLIT")
    if (
        len(authority.source_bindings) != len(_SOURCE_BINDING_SPECS_V1)
        or any(not binding.sha256_verified for binding in authority.source_bindings)
        or tuple((binding.source_category, binding.relative_path, binding.sha256) for binding in authority.source_bindings)
        != tuple((category, relative, sha) for category, relative, sha, _ in _SOURCE_BINDING_SPECS_V1)
    ):
        _fail("FORMAL_AUTHORITY_SOURCE_BINDINGS_INVALID")
    return True


def validate_covapie_batch001_formal_split_authority_v1(authority: object) -> bool:
    """Fail closed on population, split, leakage-group, or source-binding drift."""

    try:
        if type(authority) is not CovapieBatch001FormalSplitAuthorityV1:
            _fail("FORMAL_AUTHORITY_TYPE_INVALID")
        return _validate_authority_impl(authority)
    except BaseException as error:
        _public_error(error)


def load_covapie_batch001_formal_split_authority_v1(
    *, repository_root: object = None
) -> CovapieBatch001FormalSplitAuthorityV1:
    """Load exact split populations mechanically from the SHA-bound successor."""

    try:
        repo = _require_directory(
            repository_root,
            default=_DEFAULT_REPOSITORY_ROOT,
            reason="REPOSITORY_ROOT_INVALID",
        )
        bindings = verify_covapie_batch001_model_usable_source_bindings_v1(
            repository_root=repo
        )
        rows = _read_formal_rows(repo)
        split_sets = {
            split: {row.canonical_event_id for row in rows if row.formal_split == split}
            for split, _ in _EXPECTED_SPLIT_IDS_V1
        }
        group_splits: dict[str, set[str]] = {}
        for row in rows:
            group_splits.setdefault(row.formal_leakage_group_id, set()).add(row.formal_split)
        authority = CovapieBatch001FormalSplitAuthorityV1(
            rows=rows,
            train_event_ids=tuple(row.canonical_event_id for row in rows if row.formal_split == "train"),
            validation_event_ids=tuple(row.canonical_event_id for row in rows if row.formal_split == "validation"),
            test_event_ids=tuple(row.canonical_event_id for row in rows if row.formal_split == "test"),
            source_bindings=bindings,
            event_identity_intersection_counts=(
                ("train_validation", len(split_sets["train"] & split_sets["validation"])),
                ("train_test", len(split_sets["train"] & split_sets["test"])),
                ("validation_test", len(split_sets["validation"] & split_sets["test"])),
            ),
            formal_leakage_group_cross_split_violation_count=sum(
                len(splits) != 1 for splits in group_splits.values()
            ),
        )
        _validate_authority_impl(authority)
        return authority
    except BaseException as error:
        _public_error(error)


def validate_covapie_batch001_training_activation_population_v1(
    *, sample_identities: object, formal_splits: object
) -> bool:
    """Pure gate: only exact canonical-order formal train5 may be activated."""

    try:
        identities = (
            tuple(sample_identities)
            if type(sample_identities) in (tuple, list)
            else None
        )
        splits = tuple(formal_splits) if type(formal_splits) in (tuple, list) else None
        if (
            identities != FORMAL_TRAIN_EVENT_IDS_V1
            or splits != ("train",) * 5
            or identities is None
            or any(type(item) is not str for item in identities)
            or any(type(item) is not str for item in splits)
        ):
            _fail("TRAINING_ACTIVATION_REQUIRES_EXACT_CANONICAL_FORMAL_TRAIN5")
        return True
    except BaseException as error:
        _public_error(error)


def _same_tensor(left: torch.Tensor, right: torch.Tensor) -> bool:
    if left.dtype != right.dtype or left.shape != right.shape:
        return False
    if left.dtype.is_floating_point:
        return bool(
            torch.equal(torch.isnan(left), torch.isnan(right))
            and torch.equal(torch.nan_to_num(left), torch.nan_to_num(right))
        )
    return bool(torch.equal(left, right))


def _same_supervision(
    left: CovapieCurrent11TrainingSupervisionTensorsV1,
    right: CovapieCurrent11TrainingSupervisionTensorsV1,
) -> bool:
    return all(
        _same_tensor(getattr(left, field.name), getattr(right, field.name))
        for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
    )


def _clone_supervision(
    value: CovapieCurrent11TrainingSupervisionTensorsV1,
) -> CovapieCurrent11TrainingSupervisionTensorsV1:
    return CovapieCurrent11TrainingSupervisionTensorsV1(**{
        field.name: getattr(value, field.name).clone()
        for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
    })


def _clone_model_input(value: Mapping[str, object]) -> dict[str, object]:
    result: dict[str, object] = {}
    for name, item in value.items():
        if isinstance(item, torch.Tensor):
            result[name] = item.clone()
        elif type(item) is list:
            result[name] = list(item)
        else:
            result[name] = item
    return result


def _same_model_input(left: Mapping[str, object], right: Mapping[str, object]) -> bool:
    if tuple(left) != tuple(right):
        return False
    for name in left:
        left_value, right_value = left[name], right[name]
        if isinstance(left_value, torch.Tensor):
            if not isinstance(right_value, torch.Tensor) or not _same_tensor(left_value, right_value):
                return False
        elif left_value != right_value:
            return False
    return True


def _build_context(
    *, repository_root: object, cache_root: object
) -> _BuildContextV1:
    repo = _require_directory(
        repository_root,
        default=_DEFAULT_REPOSITORY_ROOT,
        reason="REPOSITORY_ROOT_INVALID",
    )
    cache = _require_directory(
        cache_root,
        default=_DEFAULT_CACHE_ROOT,
        reason="CACHE_ROOT_INVALID",
    )
    authority = load_covapie_batch001_formal_split_authority_v1(repository_root=repo)
    records = structural_owner.build_covapie_batch001_positive_structural_records_v1(
        repository_root=repo, cache_root=cache
    )
    if (
        tuple(record.sample_identity for record in records)
        != structural_owner.BATCH001_POSITIVE_EVENT_IDS_V1
        or len(records) != 13
    ):
        _fail("STRUCTURAL_OWNER_EXACT13_POPULATION_INVALID")
    return _BuildContextV1(
        repository_root=repo,
        cache_root=cache,
        authority=authority,
        records_by_identity={record.sample_identity: record for record in records},
    )


def _event_ids_for_split(
    authority: CovapieBatch001FormalSplitAuthorityV1, split: str
) -> tuple[str, ...]:
    if split == "train":
        return authority.train_event_ids
    if split == "validation":
        return authority.validation_event_ids
    if split == "test":
        return authority.test_event_ids
    _fail("FORMAL_SPLIT_INVALID")


def _build_split_from_context(
    *, context: _BuildContextV1, split: str, epoch: int, task_schedule_seed: int
) -> CovapieBatch001ModelUsableSplitBatchV1:
    if (
        type(split) is not str
        or split not in {"train", "validation", "test"}
        or type(epoch) is not int
        or epoch < 0
        or type(task_schedule_seed) is not int
        or not 0 <= task_schedule_seed <= 2**63 - 1
    ):
        _fail("SPLIT_BUILD_ARGUMENT_INVALID")
    identities = _event_ids_for_split(context.authority, split)
    records = tuple(context.records_by_identity[event_id] for event_id in identities)
    preview_tasks = tuple(
        preview_owner.canonical_task_id_for_covapie_batch001_sample_v1(
            sample_identity=event_id,
            epoch=epoch,
            task_schedule_seed=task_schedule_seed,
        )
        for event_id in identities
    )
    preview = preview_owner._tensorize_records_v1(
        records=records,
        task_ids=preview_tasks,
        epoch=epoch,
        task_schedule_seed=task_schedule_seed,
    )
    if not preview_owner.validate_covapie_batch001_preview_batch_v1(preview):
        _fail("PUBLISHED_PREVIEW_OWNER_REJECTED_SPLIT")
    preview_snapshot = _clone_supervision(preview.supervision)
    model_snapshot = _clone_model_input(preview.model_input_batch)
    admitted = split == "train"
    if admitted:
        validate_covapie_batch001_training_activation_population_v1(
            sample_identities=identities,
            formal_splits=("train",) * len(identities),
        )
        ligand_batch_index = preview.model_input_batch.get("lig_mask")
        if not isinstance(ligand_batch_index, torch.Tensor):
            _fail("TRAIN5_LIGAND_MEMBERSHIP_INVALID")
        supervision = train5_predecessor._clone_admitted_supervision(
            preview.supervision, ligand_batch_index
        )
    else:
        supervision = _clone_supervision(preview.supervision)
    if (
        not _same_supervision(preview.supervision, preview_snapshot)
        or not _same_model_input(preview.model_input_batch, model_snapshot)
    ):
        _fail("PUBLISHED_PREVIEW_TENSORS_MUTATED")
    count = len(identities)
    result = CovapieBatch001ModelUsableSplitBatchV1(
        formal_split=split,
        sample_identities=identities,
        role_profiles=tuple(record.role_profile for record in records),
        applicable_task_ids=tuple(record.applicable_canonical_task_ids for record in records),
        training_scheduled_task_ids=(
            tuple(preview_tasks) if admitted else (None,) * count
        ),
        preview_tensorization_task_ids=preview_tasks,
        epoch=epoch,
        task_schedule_seed=task_schedule_seed,
        structural_records=records,
        model_input_batch=_clone_model_input(preview.model_input_batch),
        supervision=supervision,
        split_admission_authoritative=(True,) * count,
        model_usable=(True,) * count,
        sample_training_admitted=(admitted,) * count,
        model_training_activation_authorized=(admitted,) * count,
        optimizer_population_eligible=(admitted,) * count,
        formal_validation_population_member=(split == "validation",) * count,
        formal_test_population_member=(split == "test",) * count,
        training_scheduler_eligible=(admitted,) * count,
        activation_reasons=(
            (TRAIN_ACTIVATION_REASON_V1,) * count
            if admitted
            else (VALIDATION_HOLDOUT_REASON_V1,) * count
            if split == "validation"
            else (TEST_HOLDOUT_REASON_V1,) * count
        ),
        formal_validation_task_policy=FORMAL_VALIDATION_TASK_POLICY_V1,
        formal_test_task_policy=FORMAL_TEST_TASK_POLICY_V1,
        source_authority_bindings=context.authority.source_bindings,
    )
    _validate_split_batch_impl(result, context.authority)
    return result


def build_covapie_batch001_model_usable_split_batch_v1(
    *,
    split: object,
    epoch: object,
    task_schedule_seed: object,
    repository_root: object = None,
    cache_root: object = None,
) -> CovapieBatch001ModelUsableSplitBatchV1:
    """Build one authoritative split; callers cannot supply event identities."""

    try:
        if type(split) is not str or type(epoch) is not int or type(task_schedule_seed) is not int:
            _fail("SPLIT_BUILD_ARGUMENT_INVALID")
        context = _build_context(
            repository_root=repository_root, cache_root=cache_root
        )
        return _build_split_from_context(
            context=context,
            split=split,
            epoch=epoch,
            task_schedule_seed=task_schedule_seed,
        )
    except BaseException as error:
        _public_error(error)


def _validate_split_batch_impl(
    batch: CovapieBatch001ModelUsableSplitBatchV1,
    authority: CovapieBatch001FormalSplitAuthorityV1,
) -> bool:
    if type(batch) is not CovapieBatch001ModelUsableSplitBatchV1:
        _fail("MODEL_USABLE_SPLIT_BATCH_TYPE_INVALID")
    expected_ids = _event_ids_for_split(authority, batch.formal_split)
    count = len(expected_ids)
    expected_admitted = batch.formal_split == "train"
    tuple_fields = (
        batch.role_profiles,
        batch.applicable_task_ids,
        batch.training_scheduled_task_ids,
        batch.preview_tensorization_task_ids,
        batch.split_admission_authoritative,
        batch.model_usable,
        batch.sample_training_admitted,
        batch.model_training_activation_authorized,
        batch.optimizer_population_eligible,
        batch.formal_validation_population_member,
        batch.formal_test_population_member,
        batch.training_scheduler_eligible,
        batch.activation_reasons,
    )
    if (
        batch.sample_identities != expected_ids
        or any(len(value) != count for value in tuple_fields)
        or batch.source_authority_bindings != authority.source_bindings
        or batch.model_input_batch.get("names") != list(expected_ids)
        or batch.supervision.sample_training_admitted.tolist()
        != [expected_admitted] * count
        or batch.sample_training_admitted != (expected_admitted,) * count
        or batch.model_training_activation_authorized != (expected_admitted,) * count
        or batch.optimizer_population_eligible != (expected_admitted,) * count
        or batch.training_scheduler_eligible != (expected_admitted,) * count
        or batch.split_admission_authoritative != (True,) * count
        or batch.model_usable != (True,) * count
        or batch.formal_validation_population_member
        != (batch.formal_split == "validation",) * count
        or batch.formal_test_population_member != (batch.formal_split == "test",) * count
    ):
        _fail("MODEL_USABLE_SPLIT_METADATA_OR_ACTIVATION_INVALID")
    if (
        batch.role_profiles
        != tuple(record.role_profile for record in batch.structural_records)
        or batch.applicable_task_ids
        != tuple(record.applicable_canonical_task_ids for record in batch.structural_records)
        or batch.preview_tensorization_task_ids
        != tuple(int(item) for item in batch.supervision.canonical_task_id.tolist())
    ):
        _fail("ROLE_PROFILE_OR_TASK_METADATA_INVALID")
    for event_id, profile, tasks in zip(
        batch.sample_identities, batch.role_profiles, batch.applicable_task_ids
    ):
        component = _EXPECTED_COMPONENT_BY_ID_V1[event_id]
        expected_profile = (
            preview_owner.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1
            if component == "PX5"
            else preview_owner.STRICT_LINKER_PRESENT_V1
        )
        expected_tasks = (0, 3, 4) if component == "PX5" else (0, 1, 2, 3, 4)
        preview_task = batch.preview_tensorization_task_ids[
            batch.sample_identities.index(event_id)
        ]
        if (
            profile != expected_profile
            or tasks != expected_tasks
            or preview_task not in expected_tasks
        ):
            _fail("ROLE_PROFILE_OR_APPLICABLE_TASK_DOMAIN_INVALID")
    if expected_admitted:
        validate_covapie_batch001_training_activation_population_v1(
            sample_identities=batch.sample_identities,
            formal_splits=(batch.formal_split,) * count,
        )
        if batch.training_scheduled_task_ids != tuple(batch.preview_tensorization_task_ids):
            _fail("TRAIN5_SCHEDULED_TASK_METADATA_INVALID")
    elif any(value is not None for value in batch.training_scheduled_task_ids):
        _fail("HELDOUT_SPLIT_MUST_NOT_HAVE_TRAINING_SCHEDULED_TASK")
    supervision = batch.supervision
    model_ligand_mask = batch.model_input_batch.get("lig_mask")
    if not isinstance(supervision, CovapieCurrent11TrainingSupervisionTensorsV1) or not isinstance(model_ligand_mask, torch.Tensor):
        _fail("MODEL_INPUT_OR_SUPERVISION_TYPE_INVALID")
    if (
        len(fields(CovapieCurrent11TrainingSupervisionTensorsV1)) != 37
        or not bool(supervision.canonical_task_valid.all().item())
        or not bool(supervision.ligand_role_valid.all().item())
        or int(supervision.pair_candidate_is_positive.sum().item()) != count
        or not bool(supervision.pair_positive_candidate_valid.all().item())
        or supervision.pre_post_geometry_component_valid_mask.tolist()
        != [[False, True]] * count
        or bool(supervision.pre_post_geometry_component_valid_mask[:, 0].any().item())
    ):
        _fail("MODEL_USABLE_LABEL_READINESS_INVALID")
    expected_active_diffusion = (
        supervision.ligand_base_generation_mask
        & supervision.canonical_task_valid[model_ligand_mask].unsqueeze(1)
        & supervision.sample_training_admitted[model_ligand_mask].unsqueeze(1)
    )
    if not torch.equal(supervision.ligand_active_diffusion_loss_mask, expected_active_diffusion):
        _fail("ACTIVE_DIFFUSION_MASK_FORMULA_INVALID")
    training_masks = (
        supervision.ligand_active_diffusion_loss_mask,
        supervision.pair_head_candidate_loss_mask,
        supervision.pair_contrastive_sample_loss_mask,
        supervision.pre_post_geometry_component_loss_mask,
    )
    if expected_admitted:
        if (
            not bool(supervision.sample_training_admitted.all().item())
            or not bool(supervision.pair_head_candidate_loss_mask.all().item())
            or not bool(supervision.pair_contrastive_sample_loss_mask.all().item())
            or supervision.pre_post_geometry_component_loss_mask.tolist()
            != [[False, True]] * count
            or bool(supervision.pre_post_geometry_component_loss_mask[:, 0].any().item())
            or int(supervision.pre_post_geometry_component_loss_mask[:, 1].sum().item()) != count
        ):
            _fail("TRAIN5_SUPERVISION_ACTIVATION_INVALID")
    elif (
        bool(supervision.sample_training_admitted.any().item())
        or any(bool(mask.any().item()) for mask in training_masks)
    ):
        _fail("HELDOUT_SUPERVISION_TRAINING_MASK_ACTIVE")
    return True


def validate_covapie_batch001_model_usable_split_batch_v1(
    batch: object, *, authority: object
) -> bool:
    """Validate a split batch against separately loaded formal authority."""

    try:
        if type(batch) is not CovapieBatch001ModelUsableSplitBatchV1:
            _fail("MODEL_USABLE_SPLIT_BATCH_TYPE_INVALID")
        if type(authority) is not CovapieBatch001FormalSplitAuthorityV1:
            _fail("FORMAL_AUTHORITY_TYPE_INVALID")
        _validate_authority_impl(authority)
        return _validate_split_batch_impl(batch, authority)
    except BaseException as error:
        _public_error(error)


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _csv_bytes(
    header: Sequence[str], rows: Sequence[Mapping[str, object]]
) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=tuple(header), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in header})
    return buffer.getvalue().encode("utf-8")


def _profile_summary(batch: CovapieBatch001ModelUsableSplitBatchV1) -> dict[str, int]:
    return {
        profile: batch.role_profiles.count(profile)
        for profile in sorted(set(batch.role_profiles))
    }


def _label_summary(batch: CovapieBatch001ModelUsableSplitBatchV1) -> dict[str, int]:
    supervision = batch.supervision
    return {
        "sample_count": len(batch.sample_identities),
        "pair_candidate_count": len(supervision.pair_candidate_batch_index),
        "pair_positive_candidate_count": int(supervision.pair_candidate_is_positive.sum().item()),
        "pair_positive_label_valid_count": int(supervision.pair_positive_candidate_valid.sum().item()),
        "PRE_geometry_label_valid_count": int(supervision.pre_post_geometry_component_valid_mask[:, 0].sum().item()),
        "POST_geometry_label_valid_count": int(supervision.pre_post_geometry_component_valid_mask[:, 1].sum().item()),
        "PRE_geometry_training_active_count": int(supervision.pre_post_geometry_component_loss_mask[:, 0].sum().item()),
        "POST_geometry_training_active_count": int(supervision.pre_post_geometry_component_loss_mask[:, 1].sum().item()),
    }


def _build_artifacts_impl(
    *, context: _BuildContextV1
) -> dict[str, bytes]:
    batches = {
        split: _build_split_from_context(
            context=context, split=split, epoch=0, task_schedule_seed=0
        )
        for split in ("train", "validation", "test")
    }
    batch_by_id = {
        event_id: batch
        for batch in batches.values()
        for event_id in batch.sample_identities
    }
    index_header = (
        "canonical_event_id",
        "ligand_component_id",
        "formal_leakage_group_id",
        "formal_split",
        "split_admission_authoritative",
        "role_profile",
        "applicable_task_ids",
        "model_integration_preview_ready",
        "model_usable",
        "sample_training_admitted",
        "model_training_activation_authorized",
        "optimizer_population_eligible",
        "formal_validation_population_member",
        "formal_test_population_member",
        "training_scheduler_eligible",
        "training_scheduled_task_id",
        "activation_reason",
        "authority_source",
    )
    authority_source = (
        _FORMAL_EVENT_PATH_V1.as_posix()
        + "@sha256:"
        + _SOURCE_BINDING_SPECS_V1[0][2]
    )
    index_rows = []
    for row in context.authority.rows:
        batch = batch_by_id[row.canonical_event_id]
        index = batch.sample_identities.index(row.canonical_event_id)
        scheduled = batch.training_scheduled_task_ids[index]
        index_rows.append({
            "canonical_event_id": row.canonical_event_id,
            "ligand_component_id": row.ligand_component_id,
            "formal_leakage_group_id": row.formal_leakage_group_id,
            "formal_split": row.formal_split,
            "split_admission_authoritative": "true",
            "role_profile": batch.role_profiles[index],
            "applicable_task_ids": "|".join(map(str, batch.applicable_task_ids[index])),
            "model_integration_preview_ready": "true",
            "model_usable": "true",
            "sample_training_admitted": str(batch.sample_training_admitted[index]).lower(),
            "model_training_activation_authorized": str(batch.model_training_activation_authorized[index]).lower(),
            "optimizer_population_eligible": str(batch.optimizer_population_eligible[index]).lower(),
            "formal_validation_population_member": str(batch.formal_validation_population_member[index]).lower(),
            "formal_test_population_member": str(batch.formal_test_population_member[index]).lower(),
            "training_scheduler_eligible": str(batch.training_scheduler_eligible[index]).lower(),
            "training_scheduled_task_id": "" if scheduled is None else str(scheduled),
            "activation_reason": batch.activation_reasons[index],
            "authority_source": authority_source,
        })
    index_payload = _csv_bytes(index_header, index_rows)
    cycles = {
        event_id: [
            preview_owner.canonical_task_id_for_covapie_batch001_sample_v1(
                sample_identity=event_id,
                epoch=epoch,
                task_schedule_seed=0,
            )
            for epoch in range(5)
        ]
        for event_id in FORMAL_TRAIN_EVENT_IDS_V1
    }
    registry = {
        "schema_version": "covapie_batch001_model_usable_split_registry_v1",
        "artifact_role": "FORMAL_SPLIT_CONSUMPTION_AND_EXACT_TRAIN5_ACTIVATION_BOUNDARY",
        "formal_split_populations": {
            "train_event_ids": list(context.authority.train_event_ids),
            "validation_event_ids": list(context.authority.validation_event_ids),
            "test_event_ids": list(context.authority.test_event_ids),
            "counts": {"train": 5, "validation": 4, "test": 4, "total": 13},
        },
        "role_profile_summary_by_split": {
            split: _profile_summary(batch) for split, batch in batches.items()
        },
        "task_applicability_by_event": {
            event_id: list(batch.applicable_task_ids[batch.sample_identities.index(event_id)])
            for event_id, batch in batch_by_id.items()
        },
        "training_activation_policy": {
            "population": "EXACT_CANONICAL_ORDER_FORMAL_TRAIN5_ONLY",
            "sample_training_admitted": True,
            "model_training_activation_authorized": True,
            "optimizer_population_eligible": True,
            "training_scheduler_eligible": True,
            "supervision_activation_semantics": "SHA_BOUND_PUBLISHED_TRAIN5_CLONE_ADMITTED_SUPERVISION_PARITY",
        },
        "validation_holdout_policy": {
            "population": "EXACT_FORMAL_VALIDATION4_LN5X2_PX5X2",
            "model_usable": True,
            "all_training_activation_fields": False,
            "formal_validation_task_policy": FORMAL_VALIDATION_TASK_POLICY_V1,
            "permanent_training_scheduled_task_assigned": False,
        },
        "test_holdout_policy": {
            "population": "EXACT_FORMAL_TEST4_NDU4",
            "model_usable": True,
            "all_training_activation_fields": False,
            "formal_test_task_policy": FORMAL_TEST_TASK_POLICY_V1,
            "formal_test_metric_implemented": False,
            "permanent_training_scheduled_task_assigned": False,
        },
        "label_readiness_summary_by_split": {
            split: _label_summary(batch) for split, batch in batches.items()
        },
        "train5_five_epoch_task_schedule_seed_0": cycles,
        "train5_five_epoch_task_domain_complete": all(
            set(cycle) == set(range(5)) for cycle in cycles.values()
        ),
        "cross_split_identity_intersection_counts": dict(
            context.authority.event_identity_intersection_counts
        ),
        "formal_leakage_group_cross_split_violation_count": 0,
        "source_authority_lineage": [
            {"relative_path": binding.relative_path, "sha256": binding.sha256}
            for binding in context.authority.source_bindings
        ],
        "production_geometry_weight_finalized": False,
        "full_training_authorized": False,
    }
    registry_payload = _canonical_json_bytes(registry)
    inventory_header = (
        "source_category",
        "source_root_kind",
        "relative_path",
        "sha256",
        "consumed_for",
        "sha256_verified",
    )
    inventory_rows = [
        {
            "source_category": binding.source_category,
            "source_root_kind": binding.source_root_kind,
            "relative_path": binding.relative_path,
            "sha256": binding.sha256,
            "consumed_for": binding.consumed_for,
            "sha256_verified": str(binding.sha256_verified).lower(),
        }
        for binding in context.authority.source_bindings
    ]
    inventory_payload = _csv_bytes(inventory_header, inventory_rows)
    manifest = {
        "schema_version": "covapie_batch001_13event_model_usable_split_materialization_and_activation_boundary_manifest_v1",
        "stage": "build_covapie_batch001_13event_model_usable_split_materialization_and_activation_boundary_v1",
        "baseline_HEAD": BASELINE_HEAD_V1,
        "input_authority_sha256": {
            Path(relative).name: sha
            for _, relative, sha, _ in _SOURCE_BINDING_SPECS_V1[:5]
        },
        "formal_train_event_ids": list(context.authority.train_event_ids),
        "formal_validation_event_ids": list(context.authority.validation_event_ids),
        "formal_test_event_ids": list(context.authority.test_event_ids),
        "population_counts": {
            "formal_positive_event_count": 13,
            "formal_train_event_count": 5,
            "formal_validation_event_count": 4,
            "formal_test_event_count": 4,
            "formal_split_authoritative_event_count": 13,
            "model_usable_event_count": 13,
            "sample_training_admitted_event_count": 5,
            "model_training_activation_authorized_event_count": 5,
            "optimizer_population_eligible_event_count": 5,
            "validation_training_admitted_event_count": 0,
            "test_training_admitted_event_count": 0,
            "validation_holdout_event_count": 4,
            "test_holdout_event_count": 4,
            "PRE_geometry_training_active_count": 0,
            "POST_geometry_training_active_train_count": 5,
        },
        "artifact_bindings": {
            SPLIT_INDEX_V1: {"sha256": _sha256_bytes(index_payload)},
            SPLIT_REGISTRY_V1: {"sha256": _sha256_bytes(registry_payload)},
            SOURCE_BINDING_INVENTORY_V1: {"sha256": _sha256_bytes(inventory_payload)},
        },
        "published_predecessor_artifacts_unchanged": True,
        "preview_owner_immutable_and_cloned": True,
        "train5_activation_predecessor_SHA_bound": True,
        "validation_supervision_training_inactive": True,
        "test_supervision_training_inactive": True,
        "formal_validation_task_policy": FORMAL_VALIDATION_TASK_POLICY_V1,
        "formal_test_task_policy": FORMAL_TEST_TASK_POLICY_V1,
        "formal_test_metric_implemented": False,
        "production_geometry_weight_finalized": False,
        "training_performed": False,
        "Trainer_used": False,
        "backward_performed": False,
        "optimizer_created": False,
        "full_training_authorized": False,
        "ready_for_training_datamodule_integration": True,
        "ready_for_gpt_review": True,
        "ready_for_publication": True,
        "recommended_next_step_exactly": "gpt_audit_batch001_13event_model_usable_split_activation_then_publish_if_pass",
    }
    manifest_payload = _canonical_json_bytes(manifest)
    return {
        SPLIT_INDEX_V1: index_payload,
        SPLIT_REGISTRY_V1: registry_payload,
        SOURCE_BINDING_INVENTORY_V1: inventory_payload,
        MANIFEST_V1: manifest_payload,
    }


def build_covapie_batch001_model_usable_split_artifacts_v1(
    *, repository_root: object = None, cache_root: object = None
) -> dict[str, bytes]:
    """Build exact deterministic metadata artifacts without writing files."""

    try:
        context = _build_context(
            repository_root=repository_root, cache_root=cache_root
        )
        artifacts = _build_artifacts_impl(context=context)
        if tuple(artifacts) != OUTPUT_FILENAMES_V1:
            _fail("ARTIFACT_SET_INVALID")
        _validate_artifacts_impl(artifacts, context.authority)
        return artifacts
    except BaseException as error:
        _public_error(error)


def _decoded_csv_rows(
    payload: bytes, reason: str
) -> tuple[tuple[str, ...], tuple[dict[str, str], ...]]:
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
        rows = tuple(reader)
    except (UnicodeError, csv.Error) as error:
        raise _BoundaryInvariantError(reason) from error
    if not reader.fieldnames or any(None in row for row in rows):
        _fail(reason)
    return tuple(reader.fieldnames), rows


def _decoded_json(payload: bytes, reason: str) -> dict[str, object]:
    try:
        value = json.loads(payload)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise _BoundaryInvariantError(reason) from error
    if type(value) is not dict:
        _fail(reason)
    return value


def _validate_artifacts_impl(
    artifacts: Mapping[str, bytes],
    authority: CovapieBatch001FormalSplitAuthorityV1,
) -> bool:
    if (
        type(artifacts) is not dict
        or tuple(artifacts) != OUTPUT_FILENAMES_V1
        or any(type(artifacts[name]) is not bytes for name in OUTPUT_FILENAMES_V1)
    ):
        _fail("ARTIFACT_SET_INVALID")
    _, index_rows = _decoded_csv_rows(
        artifacts[SPLIT_INDEX_V1], "SPLIT_INDEX_CSV_INVALID"
    )
    expected_order = tuple(row.canonical_event_id for row in authority.rows)
    if (
        len(index_rows) != 13
        or tuple(row["canonical_event_id"] for row in index_rows) != expected_order
        or len({row["canonical_event_id"] for row in index_rows}) != 13
    ):
        _fail("SPLIT_INDEX_EXACT13_POPULATION_INVALID")
    authority_by_id = {row.canonical_event_id: row for row in authority.rows}
    for row in index_rows:
        formal = authority_by_id[row["canonical_event_id"]]
        admitted = formal.formal_split == "train" and formal.split_admission_authoritative
        component = formal.ligand_component_id
        expected_tasks = "0|3|4" if component == "PX5" else "0|1|2|3|4"
        if (
            row["ligand_component_id"] != component
            or row["formal_leakage_group_id"] != formal.formal_leakage_group_id
            or row["formal_split"] != formal.formal_split
            or row["split_admission_authoritative"] != "true"
            or row["model_integration_preview_ready"] != "true"
            or row["model_usable"] != "true"
            or row["sample_training_admitted"] != str(admitted).lower()
            or row["model_training_activation_authorized"] != str(admitted).lower()
            or row["optimizer_population_eligible"] != str(admitted).lower()
            or row["training_scheduler_eligible"] != str(admitted).lower()
            or row["formal_validation_population_member"]
            != str(formal.formal_split == "validation").lower()
            or row["formal_test_population_member"]
            != str(formal.formal_split == "test").lower()
            or row["applicable_task_ids"] != expected_tasks
            or (admitted and row["training_scheduled_task_id"] == "")
            or (not admitted and row["training_scheduled_task_id"] != "")
        ):
            _fail("SPLIT_INDEX_ROW_SEMANTICS_INVALID")
        if component == "NDU" and (
            formal.formal_split != "test"
            or any(row[name] != "false" for name in (
                "sample_training_admitted",
                "model_training_activation_authorized",
                "optimizer_population_eligible",
                "training_scheduler_eligible",
            ))
        ):
            _fail("SPLIT_INDEX_NDU4_HOLDOUT_INVALID")
    registry = _decoded_json(
        artifacts[SPLIT_REGISTRY_V1], "SPLIT_REGISTRY_JSON_INVALID"
    )
    populations = registry.get("formal_split_populations")
    if (
        type(populations) is not dict
        or populations.get("train_event_ids") != list(authority.train_event_ids)
        or populations.get("validation_event_ids") != list(authority.validation_event_ids)
        or populations.get("test_event_ids") != list(authority.test_event_ids)
        or populations.get("counts")
        != {"train": 5, "validation": 4, "test": 4, "total": 13}
        or registry.get("cross_split_identity_intersection_counts")
        != dict(authority.event_identity_intersection_counts)
        or registry.get("formal_leakage_group_cross_split_violation_count") != 0
        or registry.get("train5_five_epoch_task_domain_complete") is not True
        or registry.get("production_geometry_weight_finalized") is not False
        or registry.get("full_training_authorized") is not False
    ):
        _fail("SPLIT_REGISTRY_SEMANTICS_INVALID")
    _, inventory_rows = _decoded_csv_rows(
        artifacts[SOURCE_BINDING_INVENTORY_V1],
        "SOURCE_BINDING_INVENTORY_CSV_INVALID",
    )
    if (
        len(inventory_rows) != len(authority.source_bindings)
        or tuple(
            (
                row["source_category"],
                row["relative_path"],
                row["sha256"],
                row["sha256_verified"],
            )
            for row in inventory_rows
        )
        != tuple(
            (
                binding.source_category,
                binding.relative_path,
                binding.sha256,
                "true",
            )
            for binding in authority.source_bindings
        )
    ):
        _fail("SOURCE_BINDING_INVENTORY_DRIFT")
    manifest = _decoded_json(
        artifacts[MANIFEST_V1], "BOUNDARY_MANIFEST_JSON_INVALID"
    )
    counts = manifest.get("population_counts")
    bindings = manifest.get("artifact_bindings")
    expected_counts = {
        "formal_positive_event_count": 13,
        "formal_train_event_count": 5,
        "formal_validation_event_count": 4,
        "formal_test_event_count": 4,
        "formal_split_authoritative_event_count": 13,
        "model_usable_event_count": 13,
        "sample_training_admitted_event_count": 5,
        "model_training_activation_authorized_event_count": 5,
        "optimizer_population_eligible_event_count": 5,
        "validation_training_admitted_event_count": 0,
        "test_training_admitted_event_count": 0,
        "validation_holdout_event_count": 4,
        "test_holdout_event_count": 4,
        "PRE_geometry_training_active_count": 0,
        "POST_geometry_training_active_train_count": 5,
    }
    if (
        counts != expected_counts
        or type(bindings) is not dict
        or set(bindings) != {
            SPLIT_INDEX_V1, SPLIT_REGISTRY_V1, SOURCE_BINDING_INVENTORY_V1
        }
        or MANIFEST_V1 in bindings
        or any(
            type(bindings.get(name)) is not dict
            or bindings[name].get("sha256") != _sha256_bytes(artifacts[name])
            for name in (SPLIT_INDEX_V1, SPLIT_REGISTRY_V1, SOURCE_BINDING_INVENTORY_V1)
        )
        or manifest.get("published_predecessor_artifacts_unchanged") is not True
        or manifest.get("production_geometry_weight_finalized") is not False
        or manifest.get("training_performed") is not False
        or manifest.get("Trainer_used") is not False
        or manifest.get("backward_performed") is not False
        or manifest.get("optimizer_created") is not False
        or manifest.get("full_training_authorized") is not False
        or manifest.get("ready_for_gpt_review") is not True
        or manifest.get("ready_for_publication") is not True
        or manifest.get("recommended_next_step_exactly")
        != "gpt_audit_batch001_13event_model_usable_split_activation_then_publish_if_pass"
    ):
        _fail("BOUNDARY_MANIFEST_SEMANTICS_INVALID")
    return True


def validate_covapie_batch001_model_usable_split_artifacts_v1(
    artifacts: object, *, authority: object
) -> bool:
    """Validate direct artifact evidence rather than trusting manifest booleans."""

    try:
        if type(artifacts) is not dict:
            _fail("ARTIFACT_SET_INVALID")
        if type(authority) is not CovapieBatch001FormalSplitAuthorityV1:
            _fail("FORMAL_AUTHORITY_TYPE_INVALID")
        _validate_authority_impl(authority)
        return _validate_artifacts_impl(artifacts, authority)
    except BaseException as error:
        _public_error(error)


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def materialize_covapie_batch001_model_usable_split_artifacts_v1(
    *, repository_root: object = None, cache_root: object = None
) -> dict[str, bytes]:
    """Write only the four authorized artifacts under the new output root."""

    try:
        repo = _require_directory(
            repository_root,
            default=_DEFAULT_REPOSITORY_ROOT,
            reason="REPOSITORY_ROOT_INVALID",
        )
        artifacts = build_covapie_batch001_model_usable_split_artifacts_v1(
            repository_root=repo, cache_root=cache_root
        )
        output_root = repo / OUTPUT_ROOT_RELATIVE_V1
        if output_root.exists():
            if not output_root.is_dir() or output_root.is_symlink():
                _fail("OUTPUT_ROOT_INVALID")
            unexpected = {
                path.name for path in output_root.iterdir()
                if path.name not in OUTPUT_FILENAMES_V1
            }
            if unexpected:
                _fail("OUTPUT_DIRECTORY_CONTAINS_UNEXPECTED_FILES")
        for name in OUTPUT_FILENAMES_V1:
            _atomic_write(output_root / name, artifacts[name])
        return artifacts
    except BaseException as error:
        _public_error(error)
