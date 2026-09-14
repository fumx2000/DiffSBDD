"""Source-bound, data-only CPU composer for the canonical CovaPIE train10.

The first source block is the published Batch001 formal train5 batch.  The
remaining five blocks are the published Current11 legacy-train5 singletons.
This module only clones, concatenates, and remaps those owner-produced CPU
tensors.  It never constructs or executes a model, loss, optimizer, Trainer,
or training lifecycle.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import stat
import struct
import subprocess
from dataclasses import dataclass, fields, is_dataclass, replace
from pathlib import Path
from typing import Mapping, NoReturn, Sequence

import torch

from covalent_ext import (
    covapie_batch001_13event_model_usable_split_materialization_and_activation_boundary_v1
    as _batch001_owner,
)
from covalent_ext import (
    covapie_current11_legacy_train5_data_adapter_v1 as _legacy_owner,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CANONICAL_TASKS_V1,
    CovapieCurrent11TrainingSupervisionTensorsV1,
    canonical_task_id_for_covapie_current11_sample_v1,
)


__all__ = (
    "TRAIN10_CPU_BATCH_COMPOSER_ERROR_V1",
    "TRAIN10_SAMPLE_IDENTITIES_V1",
    "TRAIN10_CANONICAL_EVENT_IDS_V1",
    "CovapieTrain10SourceBindingV1",
    "CovapieTrain10SourceBlockAuditV1",
    "CovapieTrain10CpuBatchPreparedV1",
    "CovapieTrain10CpuEpochBatchV1",
    "prepare_covapie_train10_cpu_batch_composer_v1",
    "build_covapie_train10_cpu_epoch_batch_v1",
    "validate_covapie_train10_cpu_epoch_batch_v1",
)


TRAIN10_CPU_BATCH_COMPOSER_ERROR_V1 = (
    "COVAPIE_TRAIN10_CPU_BATCH_COMPOSER_V1_ERROR"
)
TRAIN10_CPU_BATCH_SCHEMA_V1 = "covapie_train10_cpu_epoch_batch_v1"
_PREPARED_SCHEMA_V1 = "covapie_train10_cpu_batch_composer_prepared_v1"
_BATCH001_BRANCH_V1 = "BATCH001_FORMAL_TRAIN5_V1"
_LEGACY_BRANCH_V1 = "CURRENT11_LEGACY_TRAIN5_V1"
_BATCH001_SAMPLE_IDENTITIES_V1 = tuple(
    _batch001_owner.FORMAL_TRAIN_EVENT_IDS_V1
)
_LEGACY_TARGETS_V1 = tuple(_legacy_owner.CANONICAL_TARGETS_V1)
_LEGACY_SAMPLE_IDENTITIES_V1 = tuple(item[0] for item in _LEGACY_TARGETS_V1)
_LEGACY_CANONICAL_EVENT_IDS_V1 = tuple(item[1] for item in _LEGACY_TARGETS_V1)
TRAIN10_SAMPLE_IDENTITIES_V1 = (
    _BATCH001_SAMPLE_IDENTITIES_V1 + _LEGACY_SAMPLE_IDENTITIES_V1
)
TRAIN10_CANONICAL_EVENT_IDS_V1 = (
    _BATCH001_SAMPLE_IDENTITIES_V1 + _LEGACY_CANONICAL_EVENT_IDS_V1
)
_SOURCE_BRANCHES_V1 = (_BATCH001_BRANCH_V1,) * 5 + (_LEGACY_BRANCH_V1,) * 5
_FORMAL_SPLITS_V1 = ("train",) * 10
_BATCH_POSITIONS_V1 = tuple(range(10))
_EXPECTED_TASKS_V1 = (
    (0, "warhead_only", "A", (2,)),
    (1, "linker_plus_warhead", "B", (1, 2)),
    (2, "scaffold_plus_warhead", "B2", (0, 2)),
    (3, "scaffold_only", "B3", (0,)),
    (4, "scaffold_plus_linker_plus_warhead", "C", (0, 1, 2)),
)
_LEGACY_GROUP_V1 = "COVAPIE_LEAKAGE_GROUP_000004"
_EXPECTED_DISTINCT_GROUP_COUNT_V1 = 3
_SEAL_DOMAIN_V1 = b"COVAPIE_TRAIN10_CPU_BATCH_COMPOSER_V1\0"
_CONSTRUCTION_TOKEN = object()

_LEAKAGE_INVENTORY_V1 = (
    "data/derived/covalent_small/"
    "covapie_existing_positive_runtime_and_split_closure_v1/"
    "covapie_existing_positive_leakage_split_closure_inventory_v1.csv"
)
_DIRECT_SOURCE_SPECS_V1 = (
    (
        _LEAKAGE_INVENTORY_V1,
        16053,
        "2f673a8ca76217af1517d8254de79799d4fea333d9892af13a3ab0eeb90d8259",
        "published event-to-split and leakage-group closure",
    ),
    (
        "src/covalent_ext/"
        "covapie_batch001_13event_model_usable_split_materialization_and_"
        "activation_boundary_v1.py",
        59418,
        "e57d2b8d75cf53cb37992a33e8e41a4075dbf94422243ad6686197722d1b48f7",
        "published Batch001 formal train5 builder and activation owner",
    ),
    (
        "src/covalent_ext/covapie_current11_legacy_train5_data_adapter_v1.py",
        39045,
        "d6c9b8623659b3740aa2f359b3f1d3c0addcc684508ddc2f7a6c7dd749e525ca",
        "published Current11 legacy-train5 source adapter",
    ),
    (
        "src/covalent_ext/covapie_current11_training_tensorizer_v1.py",
        39144,
        "9fdc3f7f101fab5e5e5452e3d8e9f9b0b1e6e5fa8254a261f36310a1dfd0b606",
        "published 37-field supervision carrier and Current11 scheduler",
    ),
)

_MODEL_SAMPLE_FIELDS_V1 = ("names", "receptors", "num_lig_atoms", "num_pocket_nodes")
_MODEL_LIGAND_FIELDS_V1 = (
    "lig_coords",
    "lig_one_hot",
    "lig_source_row_index",
    "lig_parser_local_index",
)
_MODEL_POCKET_FIELDS_V1 = (
    "pocket_coords",
    "pocket_one_hot",
    "pocket_source_row_index",
    "pocket_parser_local_index",
)
_MODEL_MEMBERSHIP_FIELDS_V1 = ("lig_mask", "pocket_mask")
_MODEL_CORE_FIELDS_V1 = frozenset(
    _MODEL_SAMPLE_FIELDS_V1
    + _MODEL_LIGAND_FIELDS_V1
    + _MODEL_POCKET_FIELDS_V1
    + _MODEL_MEMBERSHIP_FIELDS_V1
)
_LEGACY_AUDIT_ONLY_FIELDS_V1 = frozenset((
    "covapie_current11_task2_runtime_result_v1",
    "covapie_current11_authoritative_training_supervision_v1",
))

_SAMPLE_SUPERVISION_FIELDS_V1 = (
    "sample_training_admitted",
    "canonical_task_id",
    "canonical_task_valid",
    "ligand_minimal_seed_or_anchor_valid",
    "target_residue_reactive_atom_local_index",
    "target_residue_condition_valid",
    "pair_positive_candidate_valid",
    "pair_negative_count",
    "pair_contrastive_sample_loss_mask",
    "observed_complex_pair_distance_angstrom",
    "observed_complex_pair_distance_valid",
    "pre_post_geometry_target_angstrom",
    "pre_post_geometry_component_valid_mask",
    "pre_post_geometry_component_loss_mask",
)
_LIGAND_SUPERVISION_FIELDS_V1 = (
    "ligand_role_id",
    "ligand_role_valid",
    "ligand_base_generation_mask",
    "ligand_base_fixed_mask",
    "ligand_base_target_mask",
    "ligand_base_context_mask",
    "ligand_active_diffusion_loss_mask",
    "ligand_minimal_seed_or_anchor_mask",
    "ligand_anchor_distance_angstrom",
    "ligand_anchor_distance_valid",
)
_POCKET_SUPERVISION_FIELDS_V1 = (
    "target_residue_membership_mask",
    "target_residue_reactive_atom_mask",
)
_CANDIDATE_DIRECT_SUPERVISION_FIELDS_V1 = (
    "pair_candidate_ligand_local_index",
    "pair_candidate_residue_local_index",
    "pair_candidate_is_positive",
    "pair_candidate_is_negative",
    "pair_head_candidate_loss_mask",
)
_REMAP_SUPERVISION_FIELDS_V1 = (
    "target_residue_reactive_atom_flat_index",
    "pair_candidate_offsets",
    "pair_candidate_batch_index",
    "pair_candidate_ligand_flat_index",
    "pair_candidate_pocket_flat_index",
    "pair_positive_candidate_index",
)
_SUPERVISION_FIELD_DOMAINS_V1 = {
    "sample": _SAMPLE_SUPERVISION_FIELDS_V1,
    "ligand": _LIGAND_SUPERVISION_FIELDS_V1,
    "pocket": _POCKET_SUPERVISION_FIELDS_V1,
    "candidate_direct": _CANDIDATE_DIRECT_SUPERVISION_FIELDS_V1,
    "semantic_remap": _REMAP_SUPERVISION_FIELDS_V1,
}
_LONG_SUPERVISION_FIELDS_V1 = frozenset((
    "canonical_task_id",
    "ligand_role_id",
    "target_residue_reactive_atom_local_index",
    "target_residue_reactive_atom_flat_index",
    "pair_candidate_offsets",
    "pair_candidate_batch_index",
    "pair_candidate_ligand_local_index",
    "pair_candidate_residue_local_index",
    "pair_candidate_ligand_flat_index",
    "pair_candidate_pocket_flat_index",
    "pair_positive_candidate_index",
    "pair_negative_count",
))
_FLOAT_SUPERVISION_FIELDS_V1 = frozenset((
    "ligand_anchor_distance_angstrom",
    "observed_complex_pair_distance_angstrom",
    "pre_post_geometry_target_angstrom",
))


@dataclass(frozen=True)
class CovapieTrain10SourceBindingV1:
    root_kind: str
    relative_path: str
    byte_count: int
    sha256: str
    consumed_for: str
    git_head_equal: bool


@dataclass(frozen=True)
class CovapieTrain10SourceBlockAuditV1:
    source_branch: str
    sample_start: int
    sample_end: int
    sample_identities: tuple[str, ...]
    canonical_event_ids: tuple[str, ...]
    formal_splits: tuple[str, ...]
    leakage_group_ids: tuple[str, ...]
    role_profiles: tuple[str, ...]
    scheduled_task_ids: tuple[int, ...]
    model_input_batch: dict[str, object]
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1
    payload_sha256: str


class CovapieTrain10CpuBatchPreparedV1:
    """Opaque and tamper-evident roots, authorities, and legacy context."""

    __slots__ = (
        "_repository_root",
        "_state_root",
        "_cache_root",
        "_sample_identities",
        "_canonical_event_ids",
        "_source_branches",
        "_formal_splits",
        "_leakage_group_ids",
        "_source_bindings",
        "_batch001_authority",
        "_legacy_prepared",
        "_seal",
    )

    def __init__(
        self,
        *,
        token: object,
        repository_root: Path,
        state_root: Path,
        cache_root: Path,
        leakage_group_ids: tuple[str, ...],
        source_bindings: tuple[CovapieTrain10SourceBindingV1, ...],
        batch001_authority: object,
        legacy_prepared: object,
    ) -> None:
        if token is not _CONSTRUCTION_TOKEN:
            raise ValueError(TRAIN10_CPU_BATCH_COMPOSER_ERROR_V1)
        self._repository_root = repository_root
        self._state_root = state_root
        self._cache_root = cache_root
        self._sample_identities = TRAIN10_SAMPLE_IDENTITIES_V1
        self._canonical_event_ids = TRAIN10_CANONICAL_EVENT_IDS_V1
        self._source_branches = _SOURCE_BRANCHES_V1
        self._formal_splits = _FORMAL_SPLITS_V1
        self._leakage_group_ids = leakage_group_ids
        self._source_bindings = source_bindings
        self._batch001_authority = batch001_authority
        self._legacy_prepared = legacy_prepared
        self._seal = _prepared_seal_v1(self)

    @property
    def schema_version(self) -> str:
        return _PREPARED_SCHEMA_V1

    @property
    def repository_root(self) -> Path:
        return self._repository_root

    @property
    def state_root(self) -> Path:
        return self._state_root

    @property
    def cache_root(self) -> Path:
        return self._cache_root

    @property
    def sample_identities(self) -> tuple[str, ...]:
        return self._sample_identities

    @property
    def canonical_event_ids(self) -> tuple[str, ...]:
        return self._canonical_event_ids

    @property
    def source_branches(self) -> tuple[str, ...]:
        return self._source_branches

    @property
    def formal_splits(self) -> tuple[str, ...]:
        return self._formal_splits

    @property
    def leakage_group_ids(self) -> tuple[str, ...]:
        return self._leakage_group_ids

    @property
    def source_bindings(self) -> tuple[CovapieTrain10SourceBindingV1, ...]:
        return self._source_bindings

    @property
    def verified_distinct_leakage_group_count(self) -> int:
        return len(set(self._leakage_group_ids))

    @property
    def training_session_active(self) -> bool:
        return False

    @property
    def ready_for_training(self) -> bool:
        return False

    @property
    def feature_semantics_audit_required_later(self) -> bool:
        return True

    @property
    def step12d_is_only_smoke_legality_check(self) -> bool:
        return True


@dataclass(frozen=True)
class CovapieTrain10CpuEpochBatchV1:
    schema_version: str
    repository_root: Path
    state_root: Path
    cache_root: Path
    sample_identities: tuple[str, ...]
    canonical_event_ids: tuple[str, ...]
    source_scheduler_sample_identities: tuple[str, ...]
    source_branches: tuple[str, ...]
    formal_splits: tuple[str, ...]
    leakage_group_ids: tuple[str, ...]
    batch_positions: tuple[int, ...]
    role_profiles: tuple[str, ...]
    scheduled_task_ids: tuple[int, ...]
    epoch: int
    task_schedule_seed: int
    model_input_batch: dict[str, object]
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1
    source_audit_blocks: tuple[CovapieTrain10SourceBlockAuditV1, ...]
    direct_source_bindings: tuple[CovapieTrain10SourceBindingV1, ...]
    batch001_source_authority_bindings: tuple[object, ...]
    legacy_source_bindings: tuple[object, ...]
    training_session_active: bool
    model_consumer_integrated: bool
    trainer_integrated: bool
    new_training_activation_created: bool
    legacy_post_overlay_applied: bool
    real_model_executed: bool
    training_or_validation_executed: bool
    parameter_update_performed: bool
    ready_for_training: bool
    feature_semantics_audit_required_later: bool
    step12d_is_only_smoke_legality_check: bool
    payload_sha256: str

    def __post_init__(self) -> None:
        if (
            type(self.model_input_batch) is not dict
            or type(self.supervision)
            is not CovapieCurrent11TrainingSupervisionTensorsV1
            or type(self.source_audit_blocks) is not tuple
        ):
            raise ValueError(TRAIN10_CPU_BATCH_COMPOSER_ERROR_V1)


class _ComposerInvariantError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _fail(reason: str) -> NoReturn:
    raise _ComposerInvariantError(reason)


def _public_error(error: BaseException) -> NoReturn:
    if type(error) is ValueError and str(error).startswith(
        TRAIN10_CPU_BATCH_COMPOSER_ERROR_V1
    ):
        raise error
    reason = error.reason if isinstance(error, _ComposerInvariantError) else "OWNER_OR_SOURCE_FAILURE"
    raise ValueError(f"{TRAIN10_CPU_BATCH_COMPOSER_ERROR_V1}:{reason}") from error


def _root(value: object, *, reason: str) -> Path:
    if not isinstance(value, (str, Path)) or isinstance(value, bool):
        _fail(reason)
    path = Path(value)
    if not path.is_absolute():
        _fail(reason)
    try:
        resolved = path.resolve(strict=True)
        metadata = path.stat()
    except OSError as error:
        raise _ComposerInvariantError(reason) from error
    if resolved != path or not stat.S_ISDIR(metadata.st_mode):
        _fail(reason)
    return path


def _roots(
    repository_root: object, state_root: object, cache_root: object
) -> tuple[Path, Path, Path]:
    repository = _root(repository_root, reason="REPOSITORY_ROOT_INVALID")
    state = _root(state_root, reason="STATE_ROOT_INVALID")
    cache = _root(cache_root, reason="CACHE_ROOT_INVALID")
    if (
        state != repository.parent / "covapie-state"
        or cache != state / "bulk-multisource-cys-sg-v1/rcsb"
    ):
        _fail("ROOT_RELATIONSHIP_INVALID")
    return repository, state, cache


def _git_head_bytes(repository: Path, relative_path: str) -> bytes:
    try:
        result = subprocess.run(
            ("git", "show", f"HEAD:{relative_path}"),
            cwd=repository,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as error:
        raise _ComposerInvariantError("REPOSITORY_SOURCE_NOT_PUBLISHED") from error
    if result.returncode != 0:
        _fail("REPOSITORY_SOURCE_NOT_PUBLISHED")
    return result.stdout


def _read_bound_source_v1(
    repository: Path,
    spec: tuple[str, int, str, str],
) -> tuple[CovapieTrain10SourceBindingV1, bytes]:
    relative_path, byte_count, expected_sha256, consumed_for = spec
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        _fail("SOURCE_BINDING_INVALID")
    path = repository / relative
    try:
        resolved = path.resolve(strict=True)
        metadata = path.stat()
        payload = path.read_bytes()
    except OSError as error:
        raise _ComposerInvariantError("SOURCE_UNAVAILABLE") from error
    if not resolved.is_relative_to(repository) or not stat.S_ISREG(metadata.st_mode):
        _fail("SOURCE_NOT_SAFE_REGULAR_FILE")
    actual_sha256 = hashlib.sha256(payload).hexdigest()
    head_equal = _git_head_bytes(repository, relative_path) == payload
    if (
        len(payload) != byte_count
        or actual_sha256 != expected_sha256
        or not head_equal
    ):
        _fail("SOURCE_BINDING_DRIFT:" + relative_path)
    return (
        CovapieTrain10SourceBindingV1(
            root_kind="repository",
            relative_path=relative_path,
            byte_count=byte_count,
            sha256=actual_sha256,
            consumed_for=consumed_for,
            git_head_equal=True,
        ),
        payload,
    )


def _verify_direct_sources_v1(
    repository: Path,
) -> tuple[tuple[CovapieTrain10SourceBindingV1, ...], dict[str, bytes]]:
    if len(_DIRECT_SOURCE_SPECS_V1) != 4:
        _fail("DIRECT_SOURCE_SPEC_SET_INVALID")
    bindings: list[CovapieTrain10SourceBindingV1] = []
    payloads: dict[str, bytes] = {}
    for spec in _DIRECT_SOURCE_SPECS_V1:
        binding, payload = _read_bound_source_v1(repository, spec)
        if binding.relative_path in payloads:
            _fail("DIRECT_SOURCE_SPEC_SET_INVALID")
        bindings.append(binding)
        payloads[binding.relative_path] = payload
    return tuple(bindings), payloads


def _csv_rows_v1(payload: bytes) -> list[dict[str, str]]:
    try:
        reader = csv.DictReader(
            io.StringIO(payload.decode("utf-8"), newline=""), strict=True
        )
        rows = list(reader)
    except (UnicodeDecodeError, csv.Error) as error:
        raise _ComposerInvariantError("LEAKAGE_INVENTORY_INVALID") from error
    required = {
        "canonical_event_id",
        "sample_identity",
        "leakage_evidence_complete",
        "leakage_group_id_after",
        "formal_split_authoritative_after",
        "formal_split_after",
        "split_membership_count",
        "split_closure_status",
        "training_admission_readiness",
    }
    if (
        not rows
        or reader.fieldnames is None
        or not required.issubset(reader.fieldnames)
        or any(None in row for row in rows)
    ):
        _fail("LEAKAGE_INVENTORY_INVALID")
    return rows


def _validate_combined_authority_v1(
    *,
    leakage_payload: bytes,
    batch001_authority: object,
) -> tuple[str, ...]:
    try:
        _batch001_owner.validate_covapie_batch001_formal_split_authority_v1(
            batch001_authority
        )
    except Exception as error:
        raise _ComposerInvariantError("BATCH001_FORMAL_AUTHORITY_INVALID") from error
    if (
        type(batch001_authority)
        is not _batch001_owner.CovapieBatch001FormalSplitAuthorityV1
        or batch001_authority.train_event_ids != _BATCH001_SAMPLE_IDENTITIES_V1
    ):
        _fail("BATCH001_FORMAL_TRAIN5_INVALID")
    rows = _csv_rows_v1(leakage_payload)
    expected_by_identity = dict(zip(
        TRAIN10_SAMPLE_IDENTITIES_V1, TRAIN10_CANONICAL_EVENT_IDS_V1
    ))
    batch_groups = {
        row.canonical_event_id: row.formal_leakage_group_id
        for row in batch001_authority.rows
        if row.canonical_event_id in _BATCH001_SAMPLE_IDENTITIES_V1
    }
    if tuple(batch_groups) != _BATCH001_SAMPLE_IDENTITIES_V1:
        _fail("BATCH001_FORMAL_TRAIN5_GROUP_ORDER_INVALID")
    expected_groups = {
        **batch_groups,
        **{identity: _LEGACY_GROUP_V1 for identity in _LEGACY_SAMPLE_IDENTITIES_V1},
    }
    selected: dict[str, dict[str, str]] = {}
    for identity in TRAIN10_SAMPLE_IDENTITIES_V1:
        matches = [row for row in rows if row.get("sample_identity") == identity]
        if len(matches) != 1:
            _fail("TARGET_LEAKAGE_ROW_NOT_EXACTLY_ONE")
        selected[identity] = matches[0]
    for identity, event_id in expected_by_identity.items():
        row = selected[identity]
        if (
            row.get("canonical_event_id") != event_id
            or row.get("leakage_evidence_complete") != "true"
            or row.get("leakage_group_id_after") != expected_groups[identity]
            or row.get("formal_split_authoritative_after") != "true"
            or row.get("formal_split_after") != "train"
            or row.get("split_membership_count") != "1"
            or row.get("split_closure_status") != "FROZEN_FORMAL_SPLIT_PRESERVED"
            or row.get("training_admission_readiness") != "FORMAL_TRAIN_ADMITTED"
        ):
            _fail("TARGET_LEAKAGE_OR_SPLIT_AUTHORITY_INVALID")
    target_groups = set(expected_groups.values())
    published_group_splits: dict[str, set[str]] = {}
    for row in rows:
        group = row.get("leakage_group_id_after")
        split = row.get("formal_split_after")
        if group in target_groups:
            published_group_splits.setdefault(group, set()).add(split)
    if (
        set(published_group_splits) != target_groups
        or any(splits != {"train"} for splits in published_group_splits.values())
        or len(target_groups) != _EXPECTED_DISTINCT_GROUP_COUNT_V1
    ):
        _fail("TARGET_LEAKAGE_GROUP_BOUNDARY_INVALID")
    batch_holdout_groups = {
        row.formal_leakage_group_id
        for row in batch001_authority.rows
        if row.formal_split in {"validation", "test"}
    }
    if target_groups & batch_holdout_groups:
        _fail("TARGET_GROUP_INTERSECTS_BATCH001_HOLDOUT")
    return tuple(expected_groups[identity] for identity in TRAIN10_SAMPLE_IDENTITIES_V1)


def _digest_value_v1(digest: object, value: object) -> None:
    update = digest.update
    if value is None:
        update(b"N")
    elif type(value) is bool:
        update(b"B1" if value else b"B0")
    elif type(value) is int:
        update(b"I" + str(value).encode("ascii") + b"\0")
    elif type(value) is float:
        update(b"F" + struct.pack(">d", value))
    elif type(value) is str:
        encoded = value.encode("utf-8")
        update(b"S" + str(len(encoded)).encode("ascii") + b":" + encoded)
    elif isinstance(value, Path):
        _digest_value_v1(digest, str(value))
    elif isinstance(value, torch.Tensor):
        tensor = value.detach().cpu().contiguous()
        update(b"T")
        _digest_value_v1(digest, str(tensor.dtype))
        _digest_value_v1(digest, tuple(tensor.shape))
        update(tensor.numpy().tobytes(order="C"))
    elif type(value) in (tuple, list):
        update(b"Q" if type(value) is tuple else b"L")
        _digest_value_v1(digest, len(value))
        for item in value:
            _digest_value_v1(digest, item)
    elif type(value) is dict:
        if any(type(key) is not str for key in value):
            _fail("DIGEST_VALUE_INVALID")
        update(b"D")
        for key in sorted(value):
            _digest_value_v1(digest, key)
            _digest_value_v1(digest, value[key])
    elif is_dataclass(value) and not isinstance(value, type):
        update(b"C")
        _digest_value_v1(digest, type(value).__qualname__)
        for field in fields(value):
            _digest_value_v1(digest, field.name)
            _digest_value_v1(digest, getattr(value, field.name))
    else:
        _fail("DIGEST_VALUE_INVALID")


def _prepared_seal_v1(prepared: CovapieTrain10CpuBatchPreparedV1) -> str:
    digest = hashlib.sha256(_SEAL_DOMAIN_V1 + b"PREPARED\0")
    legacy_seal = getattr(prepared._legacy_prepared, "_seal", None)
    _digest_value_v1(digest, (
        prepared._repository_root,
        prepared._state_root,
        prepared._cache_root,
        prepared._sample_identities,
        prepared._canonical_event_ids,
        prepared._source_branches,
        prepared._formal_splits,
        prepared._leakage_group_ids,
        prepared._source_bindings,
        prepared._batch001_authority,
        legacy_seal,
    ))
    return digest.hexdigest()


def _source_block_seal_v1(block: CovapieTrain10SourceBlockAuditV1) -> str:
    digest = hashlib.sha256(_SEAL_DOMAIN_V1 + b"SOURCE_BLOCK\0")
    _digest_value_v1(digest, (
        block.source_branch,
        block.sample_start,
        block.sample_end,
        block.sample_identities,
        block.canonical_event_ids,
        block.formal_splits,
        block.leakage_group_ids,
        block.role_profiles,
        block.scheduled_task_ids,
        block.model_input_batch,
        block.supervision,
    ))
    return digest.hexdigest()


def _batch_seal_v1(batch: CovapieTrain10CpuEpochBatchV1) -> str:
    digest = hashlib.sha256(_SEAL_DOMAIN_V1 + b"BATCH\0")
    values = tuple(
        getattr(batch, field.name)
        for field in fields(CovapieTrain10CpuEpochBatchV1)
        if field.name != "payload_sha256"
    )
    _digest_value_v1(digest, values)
    return digest.hexdigest()


def _clone_value_v1(value: object) -> object:
    if isinstance(value, torch.Tensor):
        return value.clone()
    if type(value) is dict:
        return {key: _clone_value_v1(item) for key, item in value.items()}
    if type(value) is list:
        return [_clone_value_v1(item) for item in value]
    if type(value) is tuple:
        return tuple(_clone_value_v1(item) for item in value)
    return copy.deepcopy(value)


def _clone_model_input_v1(value: Mapping[str, object]) -> dict[str, object]:
    return {name: _clone_value_v1(item) for name, item in value.items()}


def _clone_supervision_v1(
    value: CovapieCurrent11TrainingSupervisionTensorsV1,
) -> CovapieCurrent11TrainingSupervisionTensorsV1:
    return CovapieCurrent11TrainingSupervisionTensorsV1(**{
        field.name: getattr(value, field.name).clone()
        for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
    })


def _tensor_exact_v1(left: torch.Tensor, right: torch.Tensor) -> bool:
    if (
        left.dtype != right.dtype
        or left.shape != right.shape
        or left.device != right.device
    ):
        return False
    if left.dtype.is_floating_point or left.dtype.is_complex:
        return bool(((left == right) | (torch.isnan(left) & torch.isnan(right))).all().item())
    return bool(torch.equal(left, right))


def _assert_supervision_contract_v1() -> None:
    actual = tuple(
        field.name for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
    )
    explicit = tuple(
        name
        for domain in _SUPERVISION_FIELD_DOMAINS_V1.values()
        for name in domain
    )
    if (
        len(actual) != 37
        or len(explicit) != 37
        or len(set(explicit)) != 37
        or set(actual) != set(explicit)
    ):
        _fail("SUPERVISION_FIELD_DOMAIN_CONTRACT_DRIFT")


def _tensor_v1(
    value: object,
    *,
    name: str,
    ndim: int | None = None,
    dtype: torch.dtype | None = None,
) -> torch.Tensor:
    if (
        not isinstance(value, torch.Tensor)
        or value.device.type != "cpu"
        or (ndim is not None and value.ndim != ndim)
        or (dtype is not None and value.dtype != dtype)
    ):
        _fail(name.upper() + "_INVALID")
    return value


def _core_model_input_v1(
    value: object, *, source_branch: str
) -> dict[str, object]:
    if type(value) is not dict:
        _fail("SOURCE_MODEL_INPUT_INVALID")
    expected = set(_MODEL_CORE_FIELDS_V1)
    if source_branch == _LEGACY_BRANCH_V1:
        expected |= set(_LEGACY_AUDIT_ONLY_FIELDS_V1)
        if any(type(value.get(name)) is not dict for name in _LEGACY_AUDIT_ONLY_FIELDS_V1):
            _fail("LEGACY_AUDIT_SIDECAR_INVALID")
    elif source_branch != _BATCH001_BRANCH_V1:
        _fail("SOURCE_BRANCH_INVALID")
    if set(value) != expected:
        _fail("SOURCE_MODEL_FIELD_SET_INVALID")
    return {
        name: _clone_value_v1(value[name])
        for name in _MODEL_CORE_FIELDS_V1
    }


def _validate_model_core_v1(
    model: object, *, expected_names: tuple[str, ...] | None = None
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    if type(model) is not dict or set(model) != set(_MODEL_CORE_FIELDS_V1):
        _fail("MODEL_CORE_FIELD_SET_INVALID")
    names = model.get("names")
    receptors = model.get("receptors")
    if (
        type(names) is not list
        or not names
        or any(type(name) is not str or not name for name in names)
        or len(set(names)) != len(names)
        or type(receptors) is not list
        or len(receptors) != len(names)
        or any(type(receptor) is not str or not receptor for receptor in receptors)
        or (expected_names is not None and tuple(names) != expected_names)
    ):
        _fail("MODEL_SAMPLE_METADATA_INVALID")
    batch_size = len(names)
    ligand_counts_tensor = _tensor_v1(
        model.get("num_lig_atoms"), name="num_lig_atoms", ndim=1, dtype=torch.long
    )
    pocket_counts_tensor = _tensor_v1(
        model.get("num_pocket_nodes"),
        name="num_pocket_nodes",
        ndim=1,
        dtype=torch.long,
    )
    if (
        ligand_counts_tensor.shape != (batch_size,)
        or pocket_counts_tensor.shape != (batch_size,)
        or bool((ligand_counts_tensor <= 0).any().item())
        or bool((pocket_counts_tensor <= 0).any().item())
    ):
        _fail("MODEL_NODE_COUNTS_INVALID")
    ligand_counts = tuple(int(value) for value in ligand_counts_tensor.tolist())
    pocket_counts = tuple(int(value) for value in pocket_counts_tensor.tolist())
    ligand_total = sum(ligand_counts)
    pocket_total = sum(pocket_counts)
    lig_coords = _tensor_v1(model.get("lig_coords"), name="lig_coords", ndim=2)
    pocket_coords = _tensor_v1(
        model.get("pocket_coords"), name="pocket_coords", ndim=2
    )
    lig_one_hot = _tensor_v1(
        model.get("lig_one_hot"), name="lig_one_hot", ndim=2
    )
    pocket_one_hot = _tensor_v1(
        model.get("pocket_one_hot"), name="pocket_one_hot", ndim=2
    )
    if (
        lig_coords.shape != (ligand_total, 3)
        or pocket_coords.shape != (pocket_total, 3)
        or lig_one_hot.shape != (ligand_total, 10)
        or pocket_one_hot.shape != (pocket_total, 10)
        or not lig_coords.dtype.is_floating_point
        or not pocket_coords.dtype.is_floating_point
        or not lig_one_hot.dtype.is_floating_point
        or not pocket_one_hot.dtype.is_floating_point
        or not bool(torch.isfinite(lig_coords).all().item())
        or not bool(torch.isfinite(pocket_coords).all().item())
    ):
        _fail("MODEL_NODE_TENSOR_INVALID")
    for one_hot in (lig_one_hot, pocket_one_hot):
        if (
            not bool(((one_hot == 0) | (one_hot == 1)).all().item())
            or not bool((one_hot.sum(dim=1) == 1).all().item())
        ):
            _fail("MODEL_ONE_HOT_INVALID")
    lig_mask = _tensor_v1(model.get("lig_mask"), name="lig_mask", ndim=1, dtype=torch.long)
    pocket_mask = _tensor_v1(
        model.get("pocket_mask"), name="pocket_mask", ndim=1, dtype=torch.long
    )
    expected_lig_mask = torch.repeat_interleave(
        torch.arange(batch_size, dtype=torch.long), ligand_counts_tensor
    )
    expected_pocket_mask = torch.repeat_interleave(
        torch.arange(batch_size, dtype=torch.long), pocket_counts_tensor
    )
    if (
        not _tensor_exact_v1(lig_mask, expected_lig_mask)
        or not _tensor_exact_v1(pocket_mask, expected_pocket_mask)
    ):
        _fail("MODEL_MEMBERSHIP_INVALID")
    for name, total in (
        ("lig_source_row_index", ligand_total),
        ("lig_parser_local_index", ligand_total),
        ("pocket_source_row_index", pocket_total),
        ("pocket_parser_local_index", pocket_total),
    ):
        tensor = _tensor_v1(model.get(name), name=name, ndim=1, dtype=torch.long)
        if tensor.shape != (total,) or bool((tensor < 0).any().item()):
            _fail("MODEL_SOURCE_OR_LOCAL_INDEX_INVALID")
    expected_lig_local = torch.cat([
        torch.arange(count, dtype=torch.long) for count in ligand_counts
    ])
    expected_pocket_local = torch.cat([
        torch.arange(count, dtype=torch.long) for count in pocket_counts
    ])
    if (
        not _tensor_exact_v1(model["lig_parser_local_index"], expected_lig_local)
        or not _tensor_exact_v1(model["pocket_parser_local_index"], expected_pocket_local)
    ):
        _fail("PARSER_LOCAL_INDEX_SEMANTICS_INVALID")
    return ligand_counts, pocket_counts


def _field_expected_shape_v1(
    name: str, *, batch_size: int, ligand_total: int, pocket_total: int, candidate_total: int
) -> tuple[int, ...]:
    if name in _SAMPLE_SUPERVISION_FIELDS_V1:
        if name in {
            "observed_complex_pair_distance_angstrom",
            "observed_complex_pair_distance_valid",
        }:
            return (batch_size, 1)
        if name in {
            "pre_post_geometry_target_angstrom",
            "pre_post_geometry_component_valid_mask",
            "pre_post_geometry_component_loss_mask",
        }:
            return (batch_size, 2)
        return (batch_size,)
    if name in _LIGAND_SUPERVISION_FIELDS_V1:
        if name in {"ligand_role_id", "ligand_role_valid"}:
            return (ligand_total,)
        return (ligand_total, 1)
    if name in _POCKET_SUPERVISION_FIELDS_V1:
        return (pocket_total, 1)
    if name in _CANDIDATE_DIRECT_SUPERVISION_FIELDS_V1 or name in {
        "pair_candidate_batch_index",
        "pair_candidate_ligand_flat_index",
        "pair_candidate_pocket_flat_index",
    }:
        return (candidate_total,)
    if name == "pair_candidate_offsets":
        return (batch_size + 1,)
    if name in {
        "target_residue_reactive_atom_flat_index",
        "pair_positive_candidate_index",
    }:
        return (batch_size,)
    _fail("SUPERVISION_FIELD_UNCLASSIFIED:" + name)


def _validate_collated_domains_v1(
    model: object,
    supervision: object,
    *,
    expected_names: tuple[str, ...] | None = None,
) -> None:
    _assert_supervision_contract_v1()
    ligand_counts, pocket_counts = _validate_model_core_v1(
        model, expected_names=expected_names
    )
    if type(supervision) is not CovapieCurrent11TrainingSupervisionTensorsV1:
        _fail("SUPERVISION_TYPE_INVALID")
    batch_size = len(ligand_counts)
    ligand_total = sum(ligand_counts)
    pocket_total = sum(pocket_counts)
    offsets = _tensor_v1(
        supervision.pair_candidate_offsets,
        name="pair_candidate_offsets",
        ndim=1,
        dtype=torch.long,
    )
    if (
        offsets.shape != (batch_size + 1,)
        or int(offsets[0].item()) != 0
        or bool((offsets[1:] <= offsets[:-1]).any().item())
    ):
        _fail("PAIR_CANDIDATE_OFFSETS_INVALID")
    candidate_total = int(offsets[-1].item())
    for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1):
        name = field.name
        value = _tensor_v1(getattr(supervision, name), name=name)
        expected_shape = _field_expected_shape_v1(
            name,
            batch_size=batch_size,
            ligand_total=ligand_total,
            pocket_total=pocket_total,
            candidate_total=candidate_total,
        )
        if value.shape != expected_shape:
            _fail("SUPERVISION_FIELD_SHAPE_INVALID:" + name)
        if name in _LONG_SUPERVISION_FIELDS_V1 and value.dtype != torch.long:
            _fail("SUPERVISION_FIELD_DTYPE_INVALID:" + name)
        if name in _FLOAT_SUPERVISION_FIELDS_V1:
            if not value.dtype.is_floating_point:
                _fail("SUPERVISION_FIELD_DTYPE_INVALID:" + name)
        elif name not in _LONG_SUPERVISION_FIELDS_V1 and value.dtype != torch.bool:
            _fail("SUPERVISION_FIELD_DTYPE_INVALID:" + name)

    ligand_counts_tensor = model["num_lig_atoms"]
    pocket_counts_tensor = model["num_pocket_nodes"]
    ligand_offsets = torch.cat((
        torch.zeros(1, dtype=torch.long), torch.cumsum(ligand_counts_tensor, dim=0)
    ))
    pocket_offsets = torch.cat((
        torch.zeros(1, dtype=torch.long), torch.cumsum(pocket_counts_tensor, dim=0)
    ))
    expected_candidate_batch = torch.repeat_interleave(
        torch.arange(batch_size, dtype=torch.long), offsets[1:] - offsets[:-1]
    )
    candidate_batch = supervision.pair_candidate_batch_index
    ligand_flat = supervision.pair_candidate_ligand_flat_index
    pocket_flat = supervision.pair_candidate_pocket_flat_index
    if (
        not _tensor_exact_v1(candidate_batch, expected_candidate_batch)
        or bool(((ligand_flat < 0) | (ligand_flat >= ligand_total)).any().item())
        or bool(((pocket_flat < 0) | (pocket_flat >= pocket_total)).any().item())
        or not _tensor_exact_v1(candidate_batch, model["lig_mask"][ligand_flat])
        or not _tensor_exact_v1(candidate_batch, model["pocket_mask"][pocket_flat])
        or not _tensor_exact_v1(
            supervision.pair_candidate_is_negative,
            ~supervision.pair_candidate_is_positive,
        )
    ):
        _fail("PAIR_CANDIDATE_MEMBERSHIP_INVALID")

    target_local = supervision.target_residue_reactive_atom_local_index
    target_flat = supervision.target_residue_reactive_atom_flat_index
    target_valid = supervision.target_residue_condition_valid
    positive_index = supervision.pair_positive_candidate_index
    positive_valid = supervision.pair_positive_candidate_valid
    for sample in range(batch_size):
        lig_start, lig_end = int(ligand_offsets[sample]), int(ligand_offsets[sample + 1])
        pocket_start = int(pocket_offsets[sample])
        pocket_end = int(pocket_offsets[sample + 1])
        candidate_start = int(offsets[sample])
        candidate_end = int(offsets[sample + 1])
        candidate_slice = slice(candidate_start, candidate_end)
        expected_lig_local = ligand_flat[candidate_slice] - lig_start
        expected_pocket_local = pocket_flat[candidate_slice] - pocket_start
        if (
            not _tensor_exact_v1(
                expected_lig_local,
                supervision.pair_candidate_ligand_local_index[candidate_slice],
            )
            or not _tensor_exact_v1(
                expected_pocket_local,
                supervision.pair_candidate_residue_local_index[candidate_slice],
            )
            or bool((expected_lig_local < 0).any().item())
            or bool((expected_lig_local >= lig_end - lig_start).any().item())
            or bool((expected_pocket_local < 0).any().item())
            or bool((expected_pocket_local >= pocket_end - pocket_start).any().item())
        ):
            _fail("PAIR_FLAT_LOCAL_INDEX_INVALID")
        sample_positive_count = int(
            supervision.pair_candidate_is_positive[candidate_slice].sum().item()
        )
        if bool(positive_valid[sample].item()):
            index = int(positive_index[sample].item())
            if (
                sample_positive_count != 1
                or not candidate_start <= index < candidate_end
                or not bool(supervision.pair_candidate_is_positive[index].item())
            ):
                _fail("POSITIVE_CANDIDATE_INDEX_INVALID")
        elif int(positive_index[sample].item()) != -1 or sample_positive_count != 0:
            _fail("POSITIVE_CANDIDATE_SENTINEL_INVALID")
        if int(supervision.pair_negative_count[sample].item()) != int(
            supervision.pair_candidate_is_negative[candidate_slice].sum().item()
        ):
            _fail("PAIR_NEGATIVE_COUNT_INVALID")
        reactive = supervision.target_residue_reactive_atom_mask[
            pocket_start:pocket_end, 0
        ]
        if bool(target_valid[sample].item()):
            local = int(target_local[sample].item())
            flat = int(target_flat[sample].item())
            if (
                not 0 <= local < pocket_end - pocket_start
                or flat != pocket_start + local
                or int(reactive.sum().item()) != 1
                or not bool(supervision.target_residue_reactive_atom_mask[flat, 0].item())
                or not bool(supervision.target_residue_membership_mask[flat, 0].item())
            ):
                _fail("TARGET_REACTIVE_INDEX_INVALID")
            if bool(positive_valid[sample].item()) and int(
                pocket_flat[int(positive_index[sample].item())].item()
            ) != flat:
                _fail("POSITIVE_CANDIDATE_TARGET_MISMATCH")
        elif (
            int(target_local[sample].item()) != -1
            or int(target_flat[sample].item()) != -1
            or bool(reactive.any().item())
        ):
            _fail("TARGET_REACTIVE_SENTINEL_INVALID")

    generation = supervision.ligand_base_generation_mask
    fixed = supervision.ligand_base_fixed_mask
    expected_active = (
        generation
        & supervision.canonical_task_valid[model["lig_mask"]].unsqueeze(1)
        & supervision.sample_training_admitted[model["lig_mask"]].unsqueeze(1)
    )
    if (
        not bool((generation ^ fixed).all().item())
        or not _tensor_exact_v1(generation, supervision.ligand_base_target_mask)
        or not _tensor_exact_v1(fixed, supervision.ligand_base_context_mask)
        or not _tensor_exact_v1(expected_active, supervision.ligand_active_diffusion_loss_mask)
    ):
        _fail("LIGAND_MASK_SEMANTICS_INVALID")
    observed = supervision.observed_complex_pair_distance_angstrom
    observed_valid = supervision.observed_complex_pair_distance_valid
    if (
        bool((observed[observed_valid] < 0).any().item())
        or not bool(torch.isfinite(observed[observed_valid]).all().item())
        or not bool(torch.isnan(observed[~observed_valid]).all().item())
    ):
        _fail("OBSERVED_DISTANCE_VALIDITY_INVALID")
    geometry = supervision.pre_post_geometry_target_angstrom
    geometry_valid = supervision.pre_post_geometry_component_valid_mask
    geometry_loss = supervision.pre_post_geometry_component_loss_mask
    if (
        bool((geometry_loss & ~geometry_valid).any().item())
        or bool((geometry[geometry_valid] < 0).any().item())
        or not bool(torch.isfinite(geometry[geometry_valid]).all().item())
        or not bool(torch.isnan(geometry[~geometry_valid]).all().item())
    ):
        _fail("PRE_POST_GEOMETRY_VALIDITY_INVALID")


def _offset_valid_indices_v1(
    value: torch.Tensor, *, offset: int, valid: torch.Tensor
) -> torch.Tensor:
    if value.shape != valid.shape or value.dtype != torch.long or valid.dtype != torch.bool:
        _fail("SENTINEL_REMAP_INPUT_INVALID")
    if (
        bool((value[valid] < 0).any().item())
        or bool((value[~valid] != -1).any().item())
    ):
        _fail("SENTINEL_REMAP_VALUE_INVALID")
    result = value.clone()
    result[valid] += offset
    return result


def _collate_core_blocks_v1(
    blocks: object,
) -> tuple[dict[str, object], CovapieCurrent11TrainingSupervisionTensorsV1]:
    """Collate already source-validated blocks by explicit semantic domain."""

    _assert_supervision_contract_v1()
    if type(blocks) not in (tuple, list) or not blocks:
        _fail("SOURCE_BLOCK_SEQUENCE_INVALID")
    normalized = tuple(blocks)
    models: list[dict[str, object]] = []
    supervisions: list[CovapieCurrent11TrainingSupervisionTensorsV1] = []
    counts: list[tuple[int, int, int, int]] = []
    for item in normalized:
        if type(item) not in (tuple, list) or len(item) != 2:
            _fail("SOURCE_BLOCK_PAIR_INVALID")
        model, supervision = item
        ligand_counts, pocket_counts = _validate_model_core_v1(model)
        _validate_collated_domains_v1(model, supervision)
        candidate_count = int(supervision.pair_candidate_offsets[-1].item())
        models.append(model)
        supervisions.append(supervision)
        counts.append((len(ligand_counts), sum(ligand_counts), sum(pocket_counts), candidate_count))
    output_model: dict[str, object] = {
        "names": [name for model in models for name in model["names"]],
        "receptors": [value for model in models for value in model["receptors"]],
    }
    for name in _MODEL_LIGAND_FIELDS_V1 + _MODEL_POCKET_FIELDS_V1:
        output_model[name] = torch.cat([model[name] for model in models], dim=0)
    output_model["num_lig_atoms"] = torch.cat(
        [model["num_lig_atoms"] for model in models], dim=0
    )
    output_model["num_pocket_nodes"] = torch.cat(
        [model["num_pocket_nodes"] for model in models], dim=0
    )
    total_samples = sum(item[0] for item in counts)
    output_model["lig_mask"] = torch.repeat_interleave(
        torch.arange(total_samples, dtype=torch.long), output_model["num_lig_atoms"]
    )
    output_model["pocket_mask"] = torch.repeat_interleave(
        torch.arange(total_samples, dtype=torch.long), output_model["num_pocket_nodes"]
    )

    supervision_values: dict[str, torch.Tensor] = {}
    for name in (
        _SAMPLE_SUPERVISION_FIELDS_V1
        + _LIGAND_SUPERVISION_FIELDS_V1
        + _POCKET_SUPERVISION_FIELDS_V1
        + _CANDIDATE_DIRECT_SUPERVISION_FIELDS_V1
    ):
        supervision_values[name] = torch.cat(
            [getattr(supervision, name) for supervision in supervisions], dim=0
        )
    sample_offset = 0
    ligand_offset = 0
    pocket_offset = 0
    candidate_offset = 0
    target_flat_parts: list[torch.Tensor] = []
    candidate_batch_parts: list[torch.Tensor] = []
    candidate_ligand_flat_parts: list[torch.Tensor] = []
    candidate_pocket_flat_parts: list[torch.Tensor] = []
    positive_index_parts: list[torch.Tensor] = []
    combined_candidate_offsets = [0]
    for supervision, (sample_count, ligand_count, pocket_count, candidate_count) in zip(
        supervisions, counts
    ):
        target_flat_parts.append(_offset_valid_indices_v1(
            supervision.target_residue_reactive_atom_flat_index,
            offset=pocket_offset,
            valid=supervision.target_residue_condition_valid,
        ))
        candidate_batch_parts.append(
            supervision.pair_candidate_batch_index.clone() + sample_offset
        )
        candidate_ligand_flat_parts.append(
            supervision.pair_candidate_ligand_flat_index.clone() + ligand_offset
        )
        candidate_pocket_flat_parts.append(
            supervision.pair_candidate_pocket_flat_index.clone() + pocket_offset
        )
        positive_index_parts.append(_offset_valid_indices_v1(
            supervision.pair_positive_candidate_index,
            offset=candidate_offset,
            valid=supervision.pair_positive_candidate_valid,
        ))
        combined_candidate_offsets.extend(
            int(value) + candidate_offset
            for value in supervision.pair_candidate_offsets[1:].tolist()
        )
        sample_offset += sample_count
        ligand_offset += ligand_count
        pocket_offset += pocket_count
        candidate_offset += candidate_count
    supervision_values.update({
        "target_residue_reactive_atom_flat_index": torch.cat(target_flat_parts),
        "pair_candidate_offsets": torch.tensor(
            combined_candidate_offsets, dtype=torch.long
        ),
        "pair_candidate_batch_index": torch.cat(candidate_batch_parts),
        "pair_candidate_ligand_flat_index": torch.cat(candidate_ligand_flat_parts),
        "pair_candidate_pocket_flat_index": torch.cat(candidate_pocket_flat_parts),
        "pair_positive_candidate_index": torch.cat(positive_index_parts),
    })
    expected_fields = {
        field.name for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
    }
    if set(supervision_values) != expected_fields:
        _fail("COLLATED_SUPERVISION_FIELD_SET_INVALID")
    output_supervision = CovapieCurrent11TrainingSupervisionTensorsV1(
        **supervision_values
    )
    _validate_collated_domains_v1(output_model, output_supervision)
    return output_model, output_supervision


def _make_source_audit_block_v1(
    *,
    source_branch: str,
    sample_start: int,
    sample_identities: tuple[str, ...],
    canonical_event_ids: tuple[str, ...],
    formal_splits: tuple[str, ...],
    leakage_group_ids: tuple[str, ...],
    role_profiles: tuple[str, ...],
    scheduled_task_ids: tuple[int, ...],
    model_input_batch: dict[str, object],
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1,
) -> CovapieTrain10SourceBlockAuditV1:
    block = CovapieTrain10SourceBlockAuditV1(
        source_branch=source_branch,
        sample_start=sample_start,
        sample_end=sample_start + len(sample_identities),
        sample_identities=sample_identities,
        canonical_event_ids=canonical_event_ids,
        formal_splits=formal_splits,
        leakage_group_ids=leakage_group_ids,
        role_profiles=role_profiles,
        scheduled_task_ids=scheduled_task_ids,
        model_input_batch=_clone_model_input_v1(model_input_batch),
        supervision=_clone_supervision_v1(supervision),
        payload_sha256="",
    )
    return replace(block, payload_sha256=_source_block_seal_v1(block))


def _validate_source_audit_block_v1(
    block: object,
    *,
    expected_branch: str,
    expected_start: int,
    expected_identities: tuple[str, ...],
    expected_events: tuple[str, ...],
    expected_groups: tuple[str, ...],
) -> tuple[dict[str, object], CovapieCurrent11TrainingSupervisionTensorsV1]:
    if type(block) is not CovapieTrain10SourceBlockAuditV1:
        _fail("SOURCE_AUDIT_BLOCK_TYPE_INVALID")
    count = len(expected_identities)
    if (
        block.source_branch != expected_branch
        or block.sample_start != expected_start
        or block.sample_end != expected_start + count
        or block.sample_identities != expected_identities
        or block.canonical_event_ids != expected_events
        or block.formal_splits != ("train",) * count
        or block.leakage_group_ids != expected_groups
        or len(block.role_profiles) != count
        or len(block.scheduled_task_ids) != count
        or type(block.payload_sha256) is not str
        or len(block.payload_sha256) != 64
        or _source_block_seal_v1(block) != block.payload_sha256
    ):
        _fail("SOURCE_AUDIT_BLOCK_METADATA_OR_SEAL_INVALID")
    core = _core_model_input_v1(
        block.model_input_batch, source_branch=expected_branch
    )
    _validate_collated_domains_v1(
        core, block.supervision, expected_names=expected_identities
    )
    if tuple(int(value) for value in block.supervision.canonical_task_id.tolist()) != block.scheduled_task_ids:
        _fail("SOURCE_AUDIT_SCHEDULE_INVALID")
    return core, block.supervision


def _validate_source_roundtrip_v1(batch: CovapieTrain10CpuEpochBatchV1) -> None:
    sample_offset = ligand_offset = pocket_offset = candidate_offset = 0
    output_model = batch.model_input_batch
    output_supervision = batch.supervision
    for block in batch.source_audit_blocks:
        core = _core_model_input_v1(
            block.model_input_batch, source_branch=block.source_branch
        )
        sample_count = block.sample_end - block.sample_start
        ligand_count = int(core["num_lig_atoms"].sum().item())
        pocket_count = int(core["num_pocket_nodes"].sum().item())
        candidate_count = int(block.supervision.pair_candidate_offsets[-1].item())
        sample_slice = slice(sample_offset, sample_offset + sample_count)
        ligand_slice = slice(ligand_offset, ligand_offset + ligand_count)
        pocket_slice = slice(pocket_offset, pocket_offset + pocket_count)
        candidate_slice = slice(candidate_offset, candidate_offset + candidate_count)
        if (
            output_model["names"][sample_slice] != core["names"]
            or output_model["receptors"][sample_slice] != core["receptors"]
        ):
            _fail("SOURCE_MODEL_SAMPLE_ROUNDTRIP_FAILED")
        for name in ("num_lig_atoms", "num_pocket_nodes"):
            if not _tensor_exact_v1(output_model[name][sample_slice], core[name]):
                _fail("SOURCE_MODEL_COUNT_ROUNDTRIP_FAILED")
        for name in _MODEL_LIGAND_FIELDS_V1:
            if not _tensor_exact_v1(output_model[name][ligand_slice], core[name]):
                _fail("SOURCE_MODEL_LIGAND_ROUNDTRIP_FAILED")
        for name in _MODEL_POCKET_FIELDS_V1:
            if not _tensor_exact_v1(output_model[name][pocket_slice], core[name]):
                _fail("SOURCE_MODEL_POCKET_ROUNDTRIP_FAILED")
        if (
            not _tensor_exact_v1(output_model["lig_mask"][ligand_slice] - sample_offset, core["lig_mask"])
            or not _tensor_exact_v1(output_model["pocket_mask"][pocket_slice] - sample_offset, core["pocket_mask"])
        ):
            _fail("SOURCE_MODEL_MEMBERSHIP_ROUNDTRIP_FAILED")
        source_supervision = block.supervision
        for name in _SAMPLE_SUPERVISION_FIELDS_V1:
            if not _tensor_exact_v1(
                getattr(output_supervision, name)[sample_slice], getattr(source_supervision, name)
            ):
                _fail("SOURCE_SAMPLE_SUPERVISION_ROUNDTRIP_FAILED")
        for name in _LIGAND_SUPERVISION_FIELDS_V1:
            if not _tensor_exact_v1(
                getattr(output_supervision, name)[ligand_slice], getattr(source_supervision, name)
            ):
                _fail("SOURCE_LIGAND_SUPERVISION_ROUNDTRIP_FAILED")
        for name in _POCKET_SUPERVISION_FIELDS_V1:
            if not _tensor_exact_v1(
                getattr(output_supervision, name)[pocket_slice], getattr(source_supervision, name)
            ):
                _fail("SOURCE_POCKET_SUPERVISION_ROUNDTRIP_FAILED")
        for name in _CANDIDATE_DIRECT_SUPERVISION_FIELDS_V1:
            if not _tensor_exact_v1(
                getattr(output_supervision, name)[candidate_slice], getattr(source_supervision, name)
            ):
                _fail("SOURCE_CANDIDATE_SUPERVISION_ROUNDTRIP_FAILED")
        if not _tensor_exact_v1(
            output_supervision.target_residue_reactive_atom_flat_index[sample_slice],
            _offset_valid_indices_v1(
                source_supervision.target_residue_reactive_atom_flat_index,
                offset=pocket_offset,
                valid=source_supervision.target_residue_condition_valid,
            ),
        ):
            _fail("SOURCE_TARGET_FLAT_ROUNDTRIP_FAILED")
        source_offsets = source_supervision.pair_candidate_offsets
        observed_offsets = (
            output_supervision.pair_candidate_offsets[
                sample_offset:sample_offset + sample_count + 1
            ] - candidate_offset
        )
        if not _tensor_exact_v1(observed_offsets, source_offsets):
            _fail("SOURCE_CANDIDATE_OFFSETS_ROUNDTRIP_FAILED")
        remapped_candidate_expectations = (
            (
                output_supervision.pair_candidate_batch_index[candidate_slice],
                source_supervision.pair_candidate_batch_index + sample_offset,
            ),
            (
                output_supervision.pair_candidate_ligand_flat_index[candidate_slice],
                source_supervision.pair_candidate_ligand_flat_index + ligand_offset,
            ),
            (
                output_supervision.pair_candidate_pocket_flat_index[candidate_slice],
                source_supervision.pair_candidate_pocket_flat_index + pocket_offset,
            ),
            (
                output_supervision.pair_positive_candidate_index[sample_slice],
                _offset_valid_indices_v1(
                    source_supervision.pair_positive_candidate_index,
                    offset=candidate_offset,
                    valid=source_supervision.pair_positive_candidate_valid,
                ),
            ),
        )
        if any(not _tensor_exact_v1(left, right) for left, right in remapped_candidate_expectations):
            _fail("SOURCE_REMAP_ROUNDTRIP_FAILED")
        sample_offset += sample_count
        ligand_offset += ligand_count
        pocket_offset += pocket_count
        candidate_offset += candidate_count
    if (
        sample_offset != 10
        or ligand_offset != len(output_model["lig_coords"])
        or pocket_offset != len(output_model["pocket_coords"])
        or candidate_offset != len(output_supervision.pair_candidate_batch_index)
    ):
        _fail("SOURCE_BLOCK_TOTAL_ROUNDTRIP_FAILED")


def _validate_prepared_v1(
    prepared: object,
) -> CovapieTrain10CpuBatchPreparedV1:
    if type(prepared) is not CovapieTrain10CpuBatchPreparedV1:
        _fail("PREPARED_TYPE_INVALID")
    if (
        prepared._sample_identities != TRAIN10_SAMPLE_IDENTITIES_V1
        or prepared._canonical_event_ids != TRAIN10_CANONICAL_EVENT_IDS_V1
        or prepared._source_branches != _SOURCE_BRANCHES_V1
        or prepared._formal_splits != _FORMAL_SPLITS_V1
        or len(prepared._leakage_group_ids) != 10
        or len(set(prepared._leakage_group_ids)) != _EXPECTED_DISTINCT_GROUP_COUNT_V1
        or type(prepared._batch001_authority)
        is not _batch001_owner.CovapieBatch001FormalSplitAuthorityV1
        or type(prepared._legacy_prepared)
        is not _legacy_owner.CovapieCurrent11LegacyTrain5PreparedV1
        or type(prepared._seal) is not str
        or len(prepared._seal) != 64
        or _prepared_seal_v1(prepared) != prepared._seal
    ):
        _fail("PREPARED_METADATA_OR_SEAL_INVALID")
    bindings, payloads = _verify_direct_sources_v1(prepared._repository_root)
    if bindings != prepared._source_bindings:
        _fail("PREPARED_SOURCE_BINDING_DRIFT")
    groups = _validate_combined_authority_v1(
        leakage_payload=payloads[_LEAKAGE_INVENTORY_V1],
        batch001_authority=prepared._batch001_authority,
    )
    if groups != prepared._leakage_group_ids:
        _fail("PREPARED_LEAKAGE_AUTHORITY_DRIFT")
    return prepared


def _expected_scheduled_tasks_v1(
    *, epoch: int, task_schedule_seed: int
) -> tuple[int, ...]:
    batch001_tasks = tuple(
        _batch001_owner.preview_owner.canonical_task_id_for_covapie_batch001_sample_v1(
            sample_identity=identity,
            epoch=epoch,
            task_schedule_seed=task_schedule_seed,
        )
        for identity in _BATCH001_SAMPLE_IDENTITIES_V1
    )
    legacy_tasks = tuple(
        canonical_task_id_for_covapie_current11_sample_v1(
            sample_key=identity,
            epoch=epoch,
            task_schedule_seed=task_schedule_seed,
        )
        for identity in _LEGACY_SAMPLE_IDENTITIES_V1
    )
    return batch001_tasks + legacy_tasks


def _validate_batch_impl_v1(batch: CovapieTrain10CpuEpochBatchV1) -> bool:
    if type(batch) is not CovapieTrain10CpuEpochBatchV1:
        _fail("BATCH_TYPE_INVALID")
    if (
        type(batch.epoch) is not int
        or batch.epoch < 0
        or type(batch.task_schedule_seed) is not int
        or not 0 <= batch.task_schedule_seed <= 2**63 - 1
    ):
        _fail("BATCH_EPOCH_OR_SEED_INVALID")
    expected_tasks = _expected_scheduled_tasks_v1(
        epoch=batch.epoch, task_schedule_seed=batch.task_schedule_seed
    )
    inactive_statuses = (
        batch.training_session_active,
        batch.model_consumer_integrated,
        batch.trainer_integrated,
        batch.new_training_activation_created,
        batch.legacy_post_overlay_applied,
        batch.real_model_executed,
        batch.training_or_validation_executed,
        batch.parameter_update_performed,
        batch.ready_for_training,
    )
    if (
        batch.schema_version != TRAIN10_CPU_BATCH_SCHEMA_V1
        or batch.sample_identities != TRAIN10_SAMPLE_IDENTITIES_V1
        or batch.canonical_event_ids != TRAIN10_CANONICAL_EVENT_IDS_V1
        or batch.source_scheduler_sample_identities != TRAIN10_SAMPLE_IDENTITIES_V1
        or batch.source_branches != _SOURCE_BRANCHES_V1
        or batch.formal_splits != _FORMAL_SPLITS_V1
        or len(batch.leakage_group_ids) != 10
        or len(set(batch.leakage_group_ids)) != _EXPECTED_DISTINCT_GROUP_COUNT_V1
        or batch.batch_positions != _BATCH_POSITIONS_V1
        or len(batch.role_profiles) != 10
        or batch.scheduled_task_ids != expected_tasks
        or any(inactive_statuses)
        or not batch.feature_semantics_audit_required_later
        or not batch.step12d_is_only_smoke_legality_check
        or batch.payload_sha256 != _batch_seal_v1(batch)
    ):
        _fail("BATCH_METADATA_STATUS_OR_SEAL_INVALID")
    direct_bindings, payloads = _verify_direct_sources_v1(batch.repository_root)
    if direct_bindings != batch.direct_source_bindings:
        _fail("BATCH_DIRECT_SOURCE_BINDINGS_INVALID")
    authority = _batch001_owner.load_covapie_batch001_formal_split_authority_v1(
        repository_root=batch.repository_root
    )
    expected_groups = _validate_combined_authority_v1(
        leakage_payload=payloads[_LEAKAGE_INVENTORY_V1],
        batch001_authority=authority,
    )
    if (
        batch.leakage_group_ids != expected_groups
        or batch.batch001_source_authority_bindings != authority.source_bindings
        or len(batch.legacy_source_bindings) != 27
        or not all(
            type(binding) is _legacy_owner.SourceBindingV1
            for binding in batch.legacy_source_bindings
        )
    ):
        _fail("BATCH_OWNER_SOURCE_BINDINGS_INVALID")
    _validate_collated_domains_v1(
        batch.model_input_batch,
        batch.supervision,
        expected_names=TRAIN10_SAMPLE_IDENTITIES_V1,
    )
    if (
        tuple(int(value) for value in batch.supervision.canonical_task_id.tolist())
        != expected_tasks
        or batch.supervision.sample_training_admitted.tolist() != [True] * 10
        or not bool(batch.supervision.canonical_task_valid.all().item())
    ):
        _fail("BATCH_SCHEDULE_OR_ADMISSION_NOT_PRESERVED")
    if len(batch.source_audit_blocks) != 6:
        _fail("SOURCE_AUDIT_BLOCK_COUNT_INVALID")
    first_groups = expected_groups[:5]
    _validate_source_audit_block_v1(
        batch.source_audit_blocks[0],
        expected_branch=_BATCH001_BRANCH_V1,
        expected_start=0,
        expected_identities=_BATCH001_SAMPLE_IDENTITIES_V1,
        expected_events=_BATCH001_SAMPLE_IDENTITIES_V1,
        expected_groups=first_groups,
    )
    for ordinal, block in enumerate(batch.source_audit_blocks[1:]):
        index = 5 + ordinal
        _validate_source_audit_block_v1(
            block,
            expected_branch=_LEGACY_BRANCH_V1,
            expected_start=index,
            expected_identities=(_LEGACY_SAMPLE_IDENTITIES_V1[ordinal],),
            expected_events=(_LEGACY_CANONICAL_EVENT_IDS_V1[ordinal],),
            expected_groups=(_LEGACY_GROUP_V1,),
        )
    if (
        tuple(
            profile
            for block in batch.source_audit_blocks
            for profile in block.role_profiles
        ) != batch.role_profiles
        or tuple(
            task
            for block in batch.source_audit_blocks
            for task in block.scheduled_task_ids
        ) != batch.scheduled_task_ids
    ):
        _fail("SOURCE_AUDIT_METADATA_NOT_PRESERVED")
    _validate_source_roundtrip_v1(batch)
    return True


def validate_covapie_train10_cpu_epoch_batch_v1(batch: object) -> bool:
    """Independently validate identity, domains, remaps, and source round-trip."""

    try:
        if type(batch) is not CovapieTrain10CpuEpochBatchV1:
            _fail("BATCH_TYPE_INVALID")
        return _validate_batch_impl_v1(batch)
    except BaseException as error:
        _public_error(error)


def _prepare_impl_v1(
    repository_root: object, state_root: object, cache_root: object
) -> CovapieTrain10CpuBatchPreparedV1:
    _assert_supervision_contract_v1()
    if tuple(CANONICAL_TASKS_V1) != _EXPECTED_TASKS_V1:
        _fail("CANONICAL_EXACT5_CONTRACT_DRIFT")
    if (
        len(TRAIN10_SAMPLE_IDENTITIES_V1) != 10
        or len(set(TRAIN10_SAMPLE_IDENTITIES_V1)) != 10
        or len(set(TRAIN10_CANONICAL_EVENT_IDS_V1)) != 10
        or _BATCH001_SAMPLE_IDENTITIES_V1
        != tuple(_batch001_owner.FORMAL_TRAIN_EVENT_IDS_V1)
        or _LEGACY_TARGETS_V1 != tuple(_legacy_owner.CANONICAL_TARGETS_V1)
    ):
        _fail("TRAIN10_TARGET_POPULATION_DRIFT")
    repository, state, cache = _roots(repository_root, state_root, cache_root)
    bindings_before, payloads_before = _verify_direct_sources_v1(repository)
    authority = _batch001_owner.load_covapie_batch001_formal_split_authority_v1(
        repository_root=repository
    )
    groups = _validate_combined_authority_v1(
        leakage_payload=payloads_before[_LEAKAGE_INVENTORY_V1],
        batch001_authority=authority,
    )
    legacy_prepared = (
        _legacy_owner.prepare_covapie_current11_legacy_train5_data_adapter_v1(
            repository, state
        )
    )
    if (
        legacy_prepared.sample_order != _LEGACY_SAMPLE_IDENTITIES_V1
        or legacy_prepared.canonical_event_ids != _LEGACY_CANONICAL_EVENT_IDS_V1
        or legacy_prepared.formal_splits != ("train",) * 5
        or legacy_prepared.post_supervision_overlay_applied
        or legacy_prepared.training_session_active
        or legacy_prepared.ready_for_training
        or not legacy_prepared.feature_semantics_audit_required_later
        or not legacy_prepared.step12d_is_only_smoke_legality_check
    ):
        _fail("LEGACY_PREPARED_CONTRACT_INVALID")
    bindings_after, payloads_after = _verify_direct_sources_v1(repository)
    if bindings_after != bindings_before or payloads_after != payloads_before:
        _fail("SOURCE_CHANGED_DURING_PREPARE")
    return CovapieTrain10CpuBatchPreparedV1(
        token=_CONSTRUCTION_TOKEN,
        repository_root=repository,
        state_root=state,
        cache_root=cache,
        leakage_group_ids=groups,
        source_bindings=bindings_before,
        batch001_authority=authority,
        legacy_prepared=legacy_prepared,
    )


def prepare_covapie_train10_cpu_batch_composer_v1(
    repository_root: object,
    state_root: object,
    cache_root: object,
) -> CovapieTrain10CpuBatchPreparedV1:
    """Bind both published train5 sources and prepare one legacy context."""

    try:
        return _prepare_impl_v1(repository_root, state_root, cache_root)
    except BaseException as error:
        _public_error(error)


def _build_impl_v1(
    prepared: object, epoch: object, task_schedule_seed: object
) -> CovapieTrain10CpuEpochBatchV1:
    if (
        type(epoch) is not int
        or epoch < 0
        or type(task_schedule_seed) is not int
        or not 0 <= task_schedule_seed <= 2**63 - 1
    ):
        _fail("EPOCH_OR_TASK_SCHEDULE_SEED_INVALID")
    valid = _validate_prepared_v1(prepared)
    batch001 = _batch001_owner.build_covapie_batch001_model_usable_split_batch_v1(
        split="train",
        epoch=epoch,
        task_schedule_seed=task_schedule_seed,
        repository_root=valid._repository_root,
        cache_root=valid._cache_root,
    )
    try:
        _batch001_owner.validate_covapie_batch001_model_usable_split_batch_v1(
            batch001, authority=valid._batch001_authority
        )
    except Exception as error:
        raise _ComposerInvariantError("BATCH001_OWNER_BATCH_INVALID") from error
    legacy_samples = _legacy_owner.tensorize_covapie_current11_legacy_train5_epoch_v1(
        valid._legacy_prepared, epoch, task_schedule_seed
    )
    if (
        type(batch001)
        is not _batch001_owner.CovapieBatch001ModelUsableSplitBatchV1
        or batch001.formal_split != "train"
        or batch001.sample_identities != _BATCH001_SAMPLE_IDENTITIES_V1
        or batch001.training_scheduled_task_ids
        != tuple(batch001.preview_tensorization_task_ids)
        or type(legacy_samples) is not tuple
        or len(legacy_samples) != 5
        or tuple(item.sample_identity for item in legacy_samples)
        != _LEGACY_SAMPLE_IDENTITIES_V1
    ):
        _fail("OWNER_TARGET_POPULATION_OR_ORDER_INVALID")
    expected_tasks = _expected_scheduled_tasks_v1(
        epoch=epoch, task_schedule_seed=task_schedule_seed
    )
    batch001_tasks = tuple(int(value) for value in batch001.training_scheduled_task_ids)
    legacy_tasks = tuple(
        int(item.supervision.canonical_task_id[0].item()) for item in legacy_samples
    )
    if batch001_tasks + legacy_tasks != expected_tasks:
        _fail("OWNER_SCHEDULER_RESULT_INVALID")

    source_blocks: list[CovapieTrain10SourceBlockAuditV1] = []
    source_blocks.append(_make_source_audit_block_v1(
        source_branch=_BATCH001_BRANCH_V1,
        sample_start=0,
        sample_identities=_BATCH001_SAMPLE_IDENTITIES_V1,
        canonical_event_ids=_BATCH001_SAMPLE_IDENTITIES_V1,
        formal_splits=("train",) * 5,
        leakage_group_ids=valid._leakage_group_ids[:5],
        role_profiles=tuple(batch001.role_profiles),
        scheduled_task_ids=batch001_tasks,
        model_input_batch=batch001.model_input_batch,
        supervision=batch001.supervision,
    ))
    for ordinal, item in enumerate(legacy_samples):
        source_blocks.append(_make_source_audit_block_v1(
            source_branch=_LEGACY_BRANCH_V1,
            sample_start=5 + ordinal,
            sample_identities=(_LEGACY_SAMPLE_IDENTITIES_V1[ordinal],),
            canonical_event_ids=(_LEGACY_CANONICAL_EVENT_IDS_V1[ordinal],),
            formal_splits=("train",),
            leakage_group_ids=(_LEGACY_GROUP_V1,),
            role_profiles=(item.role_profile,),
            scheduled_task_ids=(legacy_tasks[ordinal],),
            model_input_batch=item.model_input_batch,
            supervision=item.supervision,
        ))
    core_blocks = tuple(
        (
            _core_model_input_v1(
                block.model_input_batch, source_branch=block.source_branch
            ),
            _clone_supervision_v1(block.supervision),
        )
        for block in source_blocks
    )
    model_input, supervision = _collate_core_blocks_v1(core_blocks)
    batch = CovapieTrain10CpuEpochBatchV1(
        schema_version=TRAIN10_CPU_BATCH_SCHEMA_V1,
        repository_root=valid._repository_root,
        state_root=valid._state_root,
        cache_root=valid._cache_root,
        sample_identities=TRAIN10_SAMPLE_IDENTITIES_V1,
        canonical_event_ids=TRAIN10_CANONICAL_EVENT_IDS_V1,
        source_scheduler_sample_identities=TRAIN10_SAMPLE_IDENTITIES_V1,
        source_branches=_SOURCE_BRANCHES_V1,
        formal_splits=_FORMAL_SPLITS_V1,
        leakage_group_ids=valid._leakage_group_ids,
        batch_positions=_BATCH_POSITIONS_V1,
        role_profiles=tuple(
            profile for block in source_blocks for profile in block.role_profiles
        ),
        scheduled_task_ids=expected_tasks,
        epoch=epoch,
        task_schedule_seed=task_schedule_seed,
        model_input_batch=model_input,
        supervision=supervision,
        source_audit_blocks=tuple(source_blocks),
        direct_source_bindings=valid._source_bindings,
        batch001_source_authority_bindings=valid._batch001_authority.source_bindings,
        legacy_source_bindings=valid._legacy_prepared.source_bindings,
        training_session_active=False,
        model_consumer_integrated=False,
        trainer_integrated=False,
        new_training_activation_created=False,
        legacy_post_overlay_applied=False,
        real_model_executed=False,
        training_or_validation_executed=False,
        parameter_update_performed=False,
        ready_for_training=False,
        feature_semantics_audit_required_later=True,
        step12d_is_only_smoke_legality_check=True,
        payload_sha256="",
    )
    batch = replace(batch, payload_sha256=_batch_seal_v1(batch))
    _validate_batch_impl_v1(batch)
    if _prepared_seal_v1(valid) != valid._seal:
        _fail("PREPARED_MUTATED_DURING_BUILD")
    return batch


def build_covapie_train10_cpu_epoch_batch_v1(
    prepared: object,
    epoch: object,
    task_schedule_seed: object = 0,
) -> CovapieTrain10CpuEpochBatchV1:
    """Build one real source-bound train10 CPU batch for the requested epoch."""

    try:
        return _build_impl_v1(prepared, epoch, task_schedule_seed)
    except BaseException as error:
        _public_error(error)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--epoch", type=int, default=0)
    parser.add_argument("--task-schedule-seed", type=int, default=0)
    arguments = parser.parse_args(argv)
    prepared = prepare_covapie_train10_cpu_batch_composer_v1(
        arguments.repository_root, arguments.state_root, arguments.cache_root
    )
    batch = build_covapie_train10_cpu_epoch_batch_v1(
        prepared, arguments.epoch, arguments.task_schedule_seed
    )
    model = batch.model_input_batch
    supervision = batch.supervision
    print(
        "BUILD_STATUS=PASS "
        f"EPOCH={batch.epoch} "
        f"TASK_SCHEDULE_SEED={batch.task_schedule_seed} "
        "TARGET_EVENT_COUNT=10 "
        f"DISTINCT_LEAKAGE_GROUP_COUNT={len(set(batch.leakage_group_ids))} "
        f"LIGAND_NODE_COUNT={len(model['lig_coords'])} "
        f"POCKET_NODE_COUNT={len(model['pocket_coords'])} "
        f"PAIR_CANDIDATE_COUNT={len(supervision.pair_candidate_batch_index)} "
        f"SAMPLE_IDENTITIES={','.join(batch.sample_identities)} "
        f"CANONICAL_EVENT_IDS={','.join(batch.canonical_event_ids)} "
        "MODEL_CONSUMER_INTEGRATED=false "
        "TRAINER_INTEGRATED=false "
        "REAL_MODEL_EXECUTED=false "
        "TRAINING_OR_VALIDATION_EXECUTED=false "
        "PARAMETER_UPDATE_PERFORMED=false "
        "READY_FOR_TRAINING=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
