"""Batch-001 bridge to the existing mixed-profile supervision contract V1.

The bridge creates CPU-only in-memory model inputs and reuses
``CovapieCurrent11TrainingSupervisionTensorsV1`` unchanged.  All 13 samples
retain auditable labels while training-admission-gated activity/loss masks are
false.  No model, loss, backward pass, optimizer, Trainer, or checkpoint is
invoked here.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping, NoReturn, Sequence

import torch

from covalent_ext import covapie_batch001_positive_structural_input_v1 as structural_owner
from covalent_ext import covapie_direct_attachment_optional_linker_runtime_v1 as direct_runtime
from covalent_ext import covapie_tensor_label_and_loss_mask_contract_design_v1 as pair_owner
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CANONICAL_TASKS_V1,
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


__all__ = (
    "BATCH001_MIXED_PROFILE_SUPERVISION_BRIDGE_ERROR_V1",
    "OUTPUT_ROOT_RELATIVE_V1",
    "OUTPUT_FILENAMES_V1",
    "CovapieBatch001ExistingSupervisionPreviewBatchV1",
    "valid_task_ids_for_covapie_batch001_sample_v1",
    "canonical_task_id_for_covapie_batch001_sample_v1",
    "tensorize_covapie_batch001_positive_sample_v1",
    "collate_covapie_batch001_preview_population_v1",
    "validate_covapie_batch001_preview_batch_v1",
    "build_covapie_batch001_bridge_artifacts_v1",
    "materialize_covapie_batch001_bridge_artifacts_v1",
)


BATCH001_MIXED_PROFILE_SUPERVISION_BRIDGE_ERROR_V1 = (
    "COVAPIE_BATCH001_TO_EXISTING_MIXED_PROFILE_SUPERVISION_BRIDGE_V1_ERROR"
)
INTEGRATION_PREVIEW_STATUS_V1 = (
    "MODEL_INTEGRATION_PREVIEW_NOT_TRAINING_ADMISSION"
)
STRICT_LINKER_PRESENT_V1 = direct_runtime.STRICT_LINKER_PRESENT_V1
DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1 = (
    direct_runtime.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1
)
OUTPUT_ROOT_RELATIVE_V1 = Path(
    "data/derived/covalent_small/"
    "covapie_batch001_to_existing_mixed_profile_supervision_bridge_v1"
)
SOURCE_BINDING_INVENTORY_V1 = (
    "covapie_batch001_model_input_source_binding_inventory_v1.csv"
)
EVENT_READINESS_V1 = "covapie_batch001_event_model_integration_readiness_v1.csv"
STRUCTURAL_EVIDENCE_V1 = "covapie_batch001_model_bound_structural_evidence_v1.json"
MANIFEST_V1 = (
    "covapie_batch001_to_existing_mixed_profile_supervision_bridge_manifest_v1.json"
)
OUTPUT_FILENAMES_V1 = (
    SOURCE_BINDING_INVENTORY_V1,
    EVENT_READINESS_V1,
    STRUCTURAL_EVIDENCE_V1,
    MANIFEST_V1,
)

_DEFAULT_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_CACHE_ROOT = (
    _DEFAULT_REPOSITORY_ROOT.parent
    / "covapie-state/bulk-multisource-cys-sg-v1/rcsb"
)
_PATH_TYPE = type(Path())
_MODEL_INPUT_CORE_FIELDS_V1 = frozenset((
    "names",
    "receptors",
    "lig_coords",
    "pocket_coords",
    "lig_one_hot",
    "pocket_one_hot",
    "lig_source_row_index",
    "pocket_source_row_index",
    "lig_parser_local_index",
    "pocket_parser_local_index",
    "num_lig_atoms",
    "num_pocket_nodes",
    "lig_mask",
    "pocket_mask",
))


@dataclass(frozen=True)
class CovapieBatch001ExistingSupervisionPreviewBatchV1:
    sample_identities: tuple[str, ...]
    role_profiles: tuple[str, ...]
    applicable_task_ids: tuple[tuple[int, ...], ...]
    canonical_task_ids: tuple[int, ...]
    epoch: int
    task_schedule_seed: int
    integration_preview_status: str
    structural_records: tuple[
        structural_owner.CovapieBatch001PositiveStructuralRecordV1, ...
    ]
    model_input_batch: dict[str, object]
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1


class _BridgeInvariantError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _fail(reason: str) -> NoReturn:
    raise _BridgeInvariantError(reason)


def _public_error(error: Exception) -> NoReturn:
    if isinstance(error, _BridgeInvariantError):
        raise ValueError(
            f"{BATCH001_MIXED_PROFILE_SUPERVISION_BRIDGE_ERROR_V1}:{error.reason}"
        ) from error
    if type(error) is ValueError and str(error).startswith(
        BATCH001_MIXED_PROFILE_SUPERVISION_BRIDGE_ERROR_V1
    ):
        raise error
    if type(error) is ValueError and (
        str(error).startswith(direct_runtime.RUNTIME_ERROR)
        or str(error).startswith(
            structural_owner.BATCH001_POSITIVE_STRUCTURAL_INPUT_ERROR_V1
        )
    ):
        raise ValueError(
            f"{BATCH001_MIXED_PROFILE_SUPERVISION_BRIDGE_ERROR_V1}:"
            f"REUSED_OWNER_REJECTED:{str(error)}"
        ) from error
    raise ValueError(BATCH001_MIXED_PROFILE_SUPERVISION_BRIDGE_ERROR_V1) from error


def _require_root(value: object, *, default: Path, reason: str) -> Path:
    path = default if value is None else value
    if type(path) is not _PATH_TYPE or not path.is_absolute():
        _fail(reason)
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise _BridgeInvariantError(reason) from error
    if resolved != path or not path.is_dir() or path.is_symlink():
        _fail(reason)
    return path


def _profile_for_identity(sample_identity: object) -> str:
    if type(sample_identity) is not str:
        _fail("SAMPLE_IDENTITY_NOT_IN_BATCH001_POSITIVE_POPULATION")
    if sample_identity not in structural_owner.BATCH001_POSITIVE_EVENT_IDS_V1:
        if ":ONL:" in sample_identity:
            _fail("ONL_EXCLUDED_FROM_BATCH001_POSITIVE_BRIDGE")
        if sample_identity.startswith("COVAPIE_CYS_SG_EVENT_V1:"):
            _fail("NEGATIVE_OR_UNKNOWN_EVENT_EXCLUDED_FROM_POSITIVE_BRIDGE")
        _fail("SAMPLE_IDENTITY_NOT_IN_BATCH001_POSITIVE_POPULATION")
    component = sample_identity.split(":")[-2]
    return (
        DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1
        if component == "PX5"
        else STRICT_LINKER_PRESENT_V1
    )


def valid_task_ids_for_covapie_batch001_sample_v1(
    sample_identity: object,
) -> tuple[int, ...]:
    """Return the exact profile-aware canonical task domain."""

    try:
        return direct_runtime.valid_canonical_task_ids_for_role_profile_v1(
            _profile_for_identity(sample_identity)
        )
    except Exception as error:
        _public_error(error)


def canonical_task_id_for_covapie_batch001_sample_v1(
    *, sample_identity: object, epoch: object, task_schedule_seed: object
) -> int:
    """Reuse the profile-separated, order/rank-independent scheduler."""

    try:
        profile = _profile_for_identity(sample_identity)
        return direct_runtime.canonical_task_id_for_role_profile_v1(
            role_profile=profile,
            sample_identity=sample_identity,
            epoch=epoch,
            task_schedule_seed=task_schedule_seed,
        )
    except Exception as error:
        _public_error(error)


def _one_hot(channels: Sequence[int]) -> torch.Tensor:
    if not channels or any(type(channel) is not int or channel not in range(10) for channel in channels):
        _fail("CHECKPOINT_CHANNEL_INDEX_INVALID")
    return torch.eye(10, dtype=torch.float32)[
        torch.tensor(tuple(channels), dtype=torch.long)
    ]


def _offsets(counts: Sequence[int]) -> tuple[int, ...]:
    result = [0]
    for count in counts:
        if type(count) is not int or count <= 0:
            _fail("NODE_COUNT_INVALID")
        result.append(result[-1] + count)
    return tuple(result)


def _coordinates(
    rows: Sequence[structural_owner.CovapieBatch001RetainedHeavyAtomV1],
) -> torch.Tensor:
    values = torch.tensor(
        tuple(row.coordinates_angstrom for row in rows), dtype=torch.float32
    )
    if values.ndim != 2 or values.shape[1:] != (3,) or not bool(torch.isfinite(values).all().item()):
        _fail("MODEL_INPUT_COORDINATES_INVALID")
    return values


def _require_task_for_record(
    record: structural_owner.CovapieBatch001PositiveStructuralRecordV1,
    task_id: object,
) -> int:
    if type(task_id) is not int or task_id not in range(5):
        _fail("CANONICAL_TASK_ID_INVALID")
    if task_id not in record.applicable_canonical_task_ids:
        _fail("TASK_NOT_APPLICABLE_FOR_ROLE_PROFILE")
    return task_id


def _tensorize_records_v1(
    *,
    records: Sequence[
        structural_owner.CovapieBatch001PositiveStructuralRecordV1
    ],
    task_ids: Sequence[int],
    epoch: int,
    task_schedule_seed: int,
) -> CovapieBatch001ExistingSupervisionPreviewBatchV1:
    record_tuple = tuple(records)
    tasks = tuple(task_ids)
    if (
        not record_tuple
        or len(record_tuple) != len(tasks)
        or type(epoch) is not int
        or epoch < 0
        or type(task_schedule_seed) is not int
        or not 0 <= task_schedule_seed <= 2**63 - 1
    ):
        _fail("TENSORIZATION_ARGUMENTS_INVALID")
    identities = tuple(record.sample_identity for record in record_tuple)
    if len(identities) != len(set(identities)):
        _fail("TENSORIZATION_SAMPLE_IDENTITY_DUPLICATE")
    for record, task_id in zip(record_tuple, tasks):
        structural_owner.validate_covapie_batch001_positive_structural_record_v1(record)
        _require_task_for_record(record, task_id)

    ligand_counts = tuple(len(record.ligand_retained_heavy_atoms) for record in record_tuple)
    pocket_counts = tuple(len(record.pocket_retained_heavy_atoms) for record in record_tuple)
    ligand_offsets = _offsets(ligand_counts)
    pocket_offsets = _offsets(pocket_counts)
    ligand_total, pocket_total = ligand_offsets[-1], pocket_offsets[-1]

    ligand_rows = tuple(
        row for record in record_tuple for row in record.ligand_retained_heavy_atoms
    )
    pocket_rows = tuple(
        row for record in record_tuple for row in record.pocket_retained_heavy_atoms
    )
    ligand_coordinates = _coordinates(ligand_rows)
    pocket_coordinates = _coordinates(pocket_rows)
    ligand_membership = torch.repeat_interleave(
        torch.arange(len(record_tuple), dtype=torch.long),
        torch.tensor(ligand_counts, dtype=torch.long),
    )
    pocket_membership = torch.repeat_interleave(
        torch.arange(len(record_tuple), dtype=torch.long),
        torch.tensor(pocket_counts, dtype=torch.long),
    )
    model_input_batch: dict[str, object] = {
        "names": list(identities),
        "receptors": [record.pdb_id for record in record_tuple],
        "lig_coords": ligand_coordinates,
        "pocket_coords": pocket_coordinates,
        "lig_one_hot": _one_hot(tuple(row.checkpoint_channel_index for row in ligand_rows)),
        "pocket_one_hot": _one_hot(tuple(row.checkpoint_channel_index for row in pocket_rows)),
        "lig_source_row_index": torch.tensor(
            tuple(row.source_atom_site_row_index_0based for row in ligand_rows),
            dtype=torch.long,
        ),
        "pocket_source_row_index": torch.tensor(
            tuple(row.source_atom_site_row_index_0based for row in pocket_rows),
            dtype=torch.long,
        ),
        "lig_parser_local_index": torch.tensor(
            tuple(index for count in ligand_counts for index in range(count)),
            dtype=torch.long,
        ),
        "pocket_parser_local_index": torch.tensor(
            tuple(index for count in pocket_counts for index in range(count)),
            dtype=torch.long,
        ),
        "num_lig_atoms": torch.tensor(ligand_counts, dtype=torch.long),
        "num_pocket_nodes": torch.tensor(pocket_counts, dtype=torch.long),
        "lig_mask": ligand_membership,
        "pocket_mask": pocket_membership,
    }

    role_id_parts: list[torch.Tensor] = []
    generation_parts: list[torch.Tensor] = []
    fixed_parts: list[torch.Tensor] = []
    target_membership_parts: list[torch.Tensor] = []
    target_reactive_parts: list[torch.Tensor] = []
    target_local: list[int] = []
    target_flat: list[int] = []
    anchor_parts: list[torch.Tensor] = []
    pair_specs: list[pair_owner.PairCandidateSampleSpec] = []
    observed_distances: list[float] = []
    geometry_rows: list[tuple[float, float]] = []
    for sample, (record, task_id) in enumerate(zip(record_tuple, tasks)):
        ligand_count, pocket_count = ligand_counts[sample], pocket_counts[sample]
        role_ids = torch.full((ligand_count,), -1, dtype=torch.long)
        for role, indices in enumerate((
            record.scaffold_retained_local_indices,
            record.linker_retained_local_indices,
            record.warhead_retained_local_indices,
        )):
            if indices:
                role_ids[list(indices)] = role
        if bool((role_ids < 0).any().item()):
            _fail("LIGAND_ROLE_PROJECTION_GAP")
        role_id_parts.append(role_ids)
        mask = direct_runtime.build_mask_for_role_profile_v1(
            role_profile=record.role_profile,
            canonical_task_id=task_id,
            scaffold_atoms=record.scaffold_retained_local_indices,
            linker_atoms=record.linker_retained_local_indices,
            warhead_atoms=record.warhead_retained_local_indices,
            num_ligand_atoms=ligand_count,
        )
        generation = torch.zeros(ligand_count, dtype=torch.bool)
        generation[list(mask.masked_atoms)] = True
        fixed = ~generation
        generated_roles = set(CANONICAL_TASKS_V1[task_id][3])
        if not torch.equal(generation, torch.tensor(
            tuple(role in generated_roles for role in role_ids.tolist()),
            dtype=torch.bool,
        )):
            _fail("CANONICAL_TASK_ROLE_MASK_MISMATCH")
        generation_parts.append(generation)
        fixed_parts.append(fixed)

        membership = torch.zeros(pocket_count, dtype=torch.bool)
        membership[list(record.target_cys_pocket_local_indices)] = True
        reactive = torch.zeros(pocket_count, dtype=torch.bool)
        reactive[record.target_sg_pocket_local_index] = True
        target_membership_parts.append(membership)
        target_reactive_parts.append(reactive)
        target_local.append(record.target_sg_pocket_local_index)
        target_flat_index = pocket_offsets[sample] + record.target_sg_pocket_local_index
        target_flat.append(target_flat_index)
        target_coordinate = pocket_coordinates[target_flat_index]
        lig_slice = ligand_coordinates[ligand_offsets[sample]:ligand_offsets[sample + 1]]
        distances = torch.linalg.vector_norm(lig_slice - target_coordinate, dim=1, keepdim=True)
        if not bool(torch.isfinite(distances).all().item()) or bool((distances < 0).any().item()):
            _fail("ANCHOR_DISTANCE_INVALID")
        anchor_parts.append(distances)
        pair_specs.append(pair_owner.PairCandidateSampleSpec(
            batch_sample_index_0based=sample,
            retained_ligand_count=ligand_count,
            retained_pocket_count=pocket_count,
            target_residue_pocket_local_indices=record.target_cys_pocket_local_indices,
            positive_ligand_local_index=record.ligand_reactive_retained_local_index,
            positive_pocket_local_index=record.target_sg_pocket_local_index,
        ))
        observed_distances.append(record.post_reactive_pair_distance_angstrom)
        geometry_rows.append((float("nan"), record.post_reactive_pair_distance_angstrom))

    try:
        pair_projection = pair_owner.build_pair_candidate_records_v1(
            pair_specs, ligand_offsets, pocket_offsets
        )
    except ValueError as error:
        raise _BridgeInvariantError("PAIR_CANDIDATE_PROJECTION_INVALID") from error
    if (
        not all(pair_projection.pair_positive_candidate_valid)
        or any(count <= 0 for count in pair_projection.pair_negative_count)
    ):
        _fail("PAIR_LABEL_READINESS_INVALID")

    ligand_role_id = torch.cat(role_id_parts)
    generation = torch.cat(generation_parts)
    fixed = torch.cat(fixed_parts)
    target_membership = torch.cat(target_membership_parts)
    target_reactive = torch.cat(target_reactive_parts)
    anchor_distance = torch.cat(anchor_parts)
    pair_count = len(pair_projection.records)
    batch_size = len(record_tuple)
    supervision = CovapieCurrent11TrainingSupervisionTensorsV1(
        sample_training_admitted=torch.zeros(batch_size, dtype=torch.bool),
        canonical_task_id=torch.tensor(tasks, dtype=torch.long),
        canonical_task_valid=torch.ones(batch_size, dtype=torch.bool),
        ligand_role_id=ligand_role_id,
        ligand_role_valid=torch.ones(ligand_total, dtype=torch.bool),
        ligand_base_generation_mask=generation.unsqueeze(1),
        ligand_base_fixed_mask=fixed.unsqueeze(1),
        ligand_base_target_mask=generation.unsqueeze(1),
        ligand_base_context_mask=fixed.unsqueeze(1),
        ligand_active_diffusion_loss_mask=torch.zeros((ligand_total, 1), dtype=torch.bool),
        ligand_minimal_seed_or_anchor_mask=torch.zeros((ligand_total, 1), dtype=torch.bool),
        ligand_minimal_seed_or_anchor_valid=torch.zeros(batch_size, dtype=torch.bool),
        ligand_anchor_distance_angstrom=anchor_distance,
        ligand_anchor_distance_valid=torch.ones((ligand_total, 1), dtype=torch.bool),
        target_residue_membership_mask=target_membership.unsqueeze(1),
        target_residue_reactive_atom_mask=target_reactive.unsqueeze(1),
        target_residue_reactive_atom_local_index=torch.tensor(target_local, dtype=torch.long),
        target_residue_reactive_atom_flat_index=torch.tensor(target_flat, dtype=torch.long),
        target_residue_condition_valid=torch.ones(batch_size, dtype=torch.bool),
        pair_candidate_offsets=torch.tensor(pair_projection.pair_candidate_offsets, dtype=torch.long),
        pair_candidate_batch_index=torch.tensor(pair_projection.pair_candidate_batch_index, dtype=torch.long),
        pair_candidate_ligand_local_index=torch.tensor(pair_projection.pair_candidate_ligand_local_index, dtype=torch.long),
        pair_candidate_residue_local_index=torch.tensor(pair_projection.pair_candidate_residue_local_index, dtype=torch.long),
        pair_candidate_ligand_flat_index=torch.tensor(pair_projection.pair_candidate_ligand_flat_index, dtype=torch.long),
        pair_candidate_pocket_flat_index=torch.tensor(pair_projection.pair_candidate_pocket_flat_index, dtype=torch.long),
        pair_candidate_is_positive=torch.tensor(pair_projection.pair_candidate_is_positive, dtype=torch.bool),
        pair_candidate_is_negative=torch.tensor(pair_projection.pair_candidate_is_negative, dtype=torch.bool),
        pair_positive_candidate_index=torch.tensor(pair_projection.pair_positive_candidate_index, dtype=torch.long),
        pair_positive_candidate_valid=torch.tensor(pair_projection.pair_positive_candidate_valid, dtype=torch.bool),
        pair_negative_count=torch.tensor(pair_projection.pair_negative_count, dtype=torch.long),
        pair_head_candidate_loss_mask=torch.zeros(pair_count, dtype=torch.bool),
        pair_contrastive_sample_loss_mask=torch.zeros(batch_size, dtype=torch.bool),
        observed_complex_pair_distance_angstrom=torch.tensor(observed_distances, dtype=torch.float32).unsqueeze(1),
        observed_complex_pair_distance_valid=torch.ones((batch_size, 1), dtype=torch.bool),
        pre_post_geometry_target_angstrom=torch.tensor(geometry_rows, dtype=torch.float32),
        pre_post_geometry_component_valid_mask=torch.tensor(
            [(False, True)] * batch_size, dtype=torch.bool
        ),
        pre_post_geometry_component_loss_mask=torch.zeros((batch_size, 2), dtype=torch.bool),
    )
    batch = CovapieBatch001ExistingSupervisionPreviewBatchV1(
        sample_identities=identities,
        role_profiles=tuple(record.role_profile for record in record_tuple),
        applicable_task_ids=tuple(record.applicable_canonical_task_ids for record in record_tuple),
        canonical_task_ids=tasks,
        epoch=epoch,
        task_schedule_seed=task_schedule_seed,
        integration_preview_status=INTEGRATION_PREVIEW_STATUS_V1,
        structural_records=record_tuple,
        model_input_batch=model_input_batch,
        supervision=supervision,
    )
    validate_covapie_batch001_preview_batch_v1(batch)
    return batch


def tensorize_covapie_batch001_positive_sample_v1(
    *,
    sample_identity: object,
    epoch: object,
    task_schedule_seed: object,
    canonical_task_id: object = None,
    repository_root: object = None,
    cache_root: object = None,
) -> CovapieBatch001ExistingSupervisionPreviewBatchV1:
    """Tensorize one exact positive event without activating training losses."""

    try:
        profile = _profile_for_identity(sample_identity)
        if type(epoch) is not int or epoch < 0 or type(task_schedule_seed) is not int:
            _fail("TENSORIZATION_ARGUMENTS_INVALID")
        repo = _require_root(repository_root, default=_DEFAULT_REPOSITORY_ROOT, reason="REPOSITORY_ROOT_INVALID")
        cache = _require_root(cache_root, default=_DEFAULT_CACHE_ROOT, reason="CACHE_ROOT_INVALID")
        records = structural_owner.build_covapie_batch001_positive_structural_records_v1(
            repository_root=repo, cache_root=cache
        )
        record = next(
            (item for item in records if item.sample_identity == sample_identity), None
        )
        if record is None or record.role_profile != profile:
            _fail("SAMPLE_IDENTITY_NOT_IN_BATCH001_POSITIVE_POPULATION")
        task_id = (
            canonical_task_id_for_covapie_batch001_sample_v1(
                sample_identity=sample_identity,
                epoch=epoch,
                task_schedule_seed=task_schedule_seed,
            )
            if canonical_task_id is None
            else _require_task_for_record(record, canonical_task_id)
        )
        return _tensorize_records_v1(
            records=(record,),
            task_ids=(task_id,),
            epoch=epoch,
            task_schedule_seed=task_schedule_seed,
        )
    except Exception as error:
        _public_error(error)


def collate_covapie_batch001_preview_population_v1(
    *,
    epoch: object,
    task_schedule_seed: object,
    sample_identities: object = None,
    repository_root: object = None,
    cache_root: object = None,
) -> CovapieBatch001ExistingSupervisionPreviewBatchV1:
    """Build and validate the exact 13-sample integration-preview batch."""

    try:
        if type(epoch) is not int or epoch < 0 or type(task_schedule_seed) is not int:
            _fail("COLLATION_ARGUMENTS_INVALID")
        repo = _require_root(repository_root, default=_DEFAULT_REPOSITORY_ROOT, reason="REPOSITORY_ROOT_INVALID")
        cache = _require_root(cache_root, default=_DEFAULT_CACHE_ROOT, reason="CACHE_ROOT_INVALID")
        records = structural_owner.build_covapie_batch001_positive_structural_records_v1(
            repository_root=repo, cache_root=cache
        )
        requested = (
            structural_owner.BATCH001_POSITIVE_EVENT_IDS_V1
            if sample_identities is None
            else tuple(sample_identities)
            if type(sample_identities) in (tuple, list)
            else None
        )
        if (
            requested is None
            or len(requested) != 13
            or len(set(requested)) != 13
            or set(requested) != set(structural_owner.BATCH001_POSITIVE_EVENT_IDS_V1)
            or any(type(item) is not str for item in requested)
        ):
            _fail("COLLATOR_REQUIRES_EXACT13_POSITIVE_EVENT_IDENTITIES")
        by_identity = {record.sample_identity: record for record in records}
        ordered = tuple(by_identity[identity] for identity in requested)
        tasks = tuple(
            canonical_task_id_for_covapie_batch001_sample_v1(
                sample_identity=identity,
                epoch=epoch,
                task_schedule_seed=task_schedule_seed,
            )
            for identity in requested
        )
        result = _tensorize_records_v1(
            records=ordered,
            task_ids=tasks,
            epoch=epoch,
            task_schedule_seed=task_schedule_seed,
        )
        validate_covapie_batch001_preview_batch_v1(
            result, require_exact13_population=True
        )
        return result
    except Exception as error:
        _public_error(error)


def _require_tensor(
    mapping: Mapping[str, object], name: str, *, dtype: torch.dtype, ndim: int
) -> torch.Tensor:
    value = mapping.get(name)
    if not isinstance(value, torch.Tensor) or value.dtype != dtype or value.ndim != ndim:
        _fail("MODEL_INPUT_TENSOR_INVALID:" + name)
    return value


def validate_covapie_batch001_preview_batch_v1(
    batch: object, *, require_exact13_population: object = False
) -> bool:
    """Validate shapes, exact indices, labels, and inactive loss masks."""

    try:
        if type(require_exact13_population) is not bool:
            _fail("VALIDATION_ARGUMENT_INVALID")
        if not isinstance(batch, CovapieBatch001ExistingSupervisionPreviewBatchV1):
            _fail("PREVIEW_BATCH_TYPE_INVALID")
        if (
            not batch.sample_identities
            or len(batch.sample_identities) != len(batch.structural_records)
            or len(batch.sample_identities) != len(batch.role_profiles)
            or len(batch.sample_identities) != len(batch.applicable_task_ids)
            or len(batch.sample_identities) != len(batch.canonical_task_ids)
            or len(set(batch.sample_identities)) != len(batch.sample_identities)
            or batch.integration_preview_status != INTEGRATION_PREVIEW_STATUS_V1
            or type(batch.epoch) is not int
            or batch.epoch < 0
            or type(batch.task_schedule_seed) is not int
            or not 0 <= batch.task_schedule_seed <= 2**63 - 1
        ):
            _fail("PREVIEW_BATCH_METADATA_INVALID")
        if require_exact13_population and (
            len(batch.sample_identities) != 13
            or set(batch.sample_identities)
            != set(structural_owner.BATCH001_POSITIVE_EVENT_IDS_V1)
        ):
            _fail("PREVIEW_BATCH_EXACT13_POPULATION_INVALID")
        for index, record in enumerate(batch.structural_records):
            structural_owner.validate_covapie_batch001_positive_structural_record_v1(record)
            if (
                record.sample_identity != batch.sample_identities[index]
                or record.role_profile != batch.role_profiles[index]
                or record.applicable_canonical_task_ids != batch.applicable_task_ids[index]
                or batch.canonical_task_ids[index] not in record.applicable_canonical_task_ids
                or record.split_admission_authoritative is not False
                or record.sample_training_admitted is not False
            ):
                _fail("PREVIEW_BATCH_RECORD_METADATA_MISMATCH")
        model = batch.model_input_batch
        if type(model) is not dict or not _MODEL_INPUT_CORE_FIELDS_V1.issubset(model):
            _fail("MODEL_INPUT_BATCH_CONTRACT_INVALID")
        batch_size = len(batch.sample_identities)
        ligand_counts = tuple(len(record.ligand_retained_heavy_atoms) for record in batch.structural_records)
        pocket_counts = tuple(len(record.pocket_retained_heavy_atoms) for record in batch.structural_records)
        ligand_offsets, pocket_offsets = _offsets(ligand_counts), _offsets(pocket_counts)
        ligand_total, pocket_total = ligand_offsets[-1], pocket_offsets[-1]
        if model.get("names") != list(batch.sample_identities) or model.get("receptors") != [
            record.pdb_id for record in batch.structural_records
        ]:
            _fail("MODEL_INPUT_IDENTITY_ORDER_INVALID")
        lig_coords = _require_tensor(model, "lig_coords", dtype=torch.float32, ndim=2)
        pocket_coords = _require_tensor(model, "pocket_coords", dtype=torch.float32, ndim=2)
        lig_one_hot = _require_tensor(model, "lig_one_hot", dtype=torch.float32, ndim=2)
        pocket_one_hot = _require_tensor(model, "pocket_one_hot", dtype=torch.float32, ndim=2)
        if (
            tuple(lig_coords.shape) != (ligand_total, 3)
            or tuple(pocket_coords.shape) != (pocket_total, 3)
            or tuple(lig_one_hot.shape) != (ligand_total, 10)
            or tuple(pocket_one_hot.shape) != (pocket_total, 10)
            or not bool(torch.isfinite(lig_coords).all().item())
            or not bool(torch.isfinite(pocket_coords).all().item())
            or not torch.equal(lig_one_hot.sum(1), torch.ones(ligand_total))
            or not torch.equal(pocket_one_hot.sum(1), torch.ones(pocket_total))
        ):
            _fail("MODEL_INPUT_SHAPE_OR_FEATURE_DOMAIN_INVALID")
        for name, total in (
            ("lig_source_row_index", ligand_total),
            ("pocket_source_row_index", pocket_total),
            ("lig_parser_local_index", ligand_total),
            ("pocket_parser_local_index", pocket_total),
            ("lig_mask", ligand_total),
            ("pocket_mask", pocket_total),
        ):
            tensor = _require_tensor(model, name, dtype=torch.long, ndim=1)
            if len(tensor) != total:
                _fail("MODEL_INPUT_INDEX_SHAPE_INVALID:" + name)
        if (
            _require_tensor(model, "num_lig_atoms", dtype=torch.long, ndim=1).tolist()
            != list(ligand_counts)
            or _require_tensor(model, "num_pocket_nodes", dtype=torch.long, ndim=1).tolist()
            != list(pocket_counts)
            or model["lig_mask"].tolist()
            != [sample for sample, count in enumerate(ligand_counts) for _ in range(count)]
            or model["pocket_mask"].tolist()
            != [sample for sample, count in enumerate(pocket_counts) for _ in range(count)]
        ):
            _fail("MODEL_INPUT_MEMBERSHIP_INVALID")

        supervision = batch.supervision
        if not isinstance(supervision, CovapieCurrent11TrainingSupervisionTensorsV1):
            _fail("SUPERVISION_DATACLASS_NOT_REUSED")
        if any(
            not isinstance(getattr(supervision, field.name), torch.Tensor)
            for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
        ):
            _fail("SUPERVISION_FIELD_NOT_TENSOR")
        if (
            supervision.sample_training_admitted.shape != (batch_size,)
            or bool(supervision.sample_training_admitted.any().item())
            or supervision.canonical_task_id.tolist() != list(batch.canonical_task_ids)
            or not bool(supervision.canonical_task_valid.all().item())
            or supervision.ligand_role_id.shape != (ligand_total,)
            or not bool(supervision.ligand_role_valid.all().item())
        ):
            _fail("SUPERVISION_SAMPLE_TASK_OR_ROLE_INVALID")
        label_masks = (
            supervision.ligand_base_generation_mask,
            supervision.ligand_base_fixed_mask,
            supervision.ligand_base_target_mask,
            supervision.ligand_base_context_mask,
        )
        if any(tensor.shape != (ligand_total, 1) or tensor.dtype != torch.bool for tensor in label_masks):
            _fail("SUPERVISION_ROLE_MASK_SHAPE_INVALID")
        if (
            not torch.equal(supervision.ligand_base_generation_mask, supervision.ligand_base_target_mask)
            or not torch.equal(supervision.ligand_base_fixed_mask, supervision.ligand_base_context_mask)
            or not torch.equal(
                supervision.ligand_base_fixed_mask,
                ~supervision.ligand_base_generation_mask,
            )
            or bool(supervision.ligand_active_diffusion_loss_mask.any().item())
        ):
            _fail("LABEL_AVAILABLE_VS_LOSS_ACTIVE_CONTRACT_INVALID")
        for sample, record in enumerate(batch.structural_records):
            lig_slice = slice(ligand_offsets[sample], ligand_offsets[sample + 1])
            observed_roles = supervision.ligand_role_id[lig_slice]
            expected_roles = torch.full((ligand_counts[sample],), -1, dtype=torch.long)
            for role, indices in enumerate((
                record.scaffold_retained_local_indices,
                record.linker_retained_local_indices,
                record.warhead_retained_local_indices,
            )):
                if indices:
                    expected_roles[list(indices)] = role
            if not torch.equal(observed_roles, expected_roles):
                _fail("SUPERVISION_ROLE_ID_INVALID")
            expected_mask = direct_runtime.build_mask_for_role_profile_v1(
                role_profile=record.role_profile,
                canonical_task_id=batch.canonical_task_ids[sample],
                scaffold_atoms=record.scaffold_retained_local_indices,
                linker_atoms=record.linker_retained_local_indices,
                warhead_atoms=record.warhead_retained_local_indices,
                num_ligand_atoms=ligand_counts[sample],
            )
            observed_generated = torch.nonzero(
                supervision.ligand_base_generation_mask[lig_slice, 0], as_tuple=False
            ).flatten().tolist()
            if observed_generated != list(expected_mask.masked_atoms):
                _fail("SUPERVISION_CANONICAL_TASK_MASK_INVALID")
        if (
            bool(supervision.ligand_minimal_seed_or_anchor_mask.any().item())
            or bool(supervision.ligand_minimal_seed_or_anchor_valid.any().item())
            or supervision.ligand_anchor_distance_angstrom.shape != (ligand_total, 1)
            or not bool(torch.isfinite(supervision.ligand_anchor_distance_angstrom).all().item())
            or bool((supervision.ligand_anchor_distance_angstrom < 0).any().item())
            or not bool(supervision.ligand_anchor_distance_valid.all().item())
        ):
            _fail("MINIMAL_SEED_OR_ANCHOR_DISTANCE_CONTRACT_INVALID")
        for sample, record in enumerate(batch.structural_records):
            lig_slice = slice(ligand_offsets[sample], ligand_offsets[sample + 1])
            target_flat = pocket_offsets[sample] + record.target_sg_pocket_local_index
            expected_distance = torch.linalg.vector_norm(
                lig_coords[lig_slice] - pocket_coords[target_flat], dim=1, keepdim=True
            )
            if not torch.allclose(
                supervision.ligand_anchor_distance_angstrom[lig_slice],
                expected_distance,
                rtol=0,
                atol=1e-6,
            ):
                _fail("ANCHOR_DISTANCE_RECOMPUTATION_MISMATCH")
        if (
            supervision.target_residue_membership_mask.shape != (pocket_total, 1)
            or supervision.target_residue_reactive_atom_mask.shape != (pocket_total, 1)
            or supervision.target_residue_reactive_atom_local_index.shape != (batch_size,)
            or supervision.target_residue_reactive_atom_flat_index.shape != (batch_size,)
            or not bool(supervision.target_residue_condition_valid.all().item())
        ):
            _fail("TARGET_CONDITION_SHAPE_INVALID")
        for sample, record in enumerate(batch.structural_records):
            pocket_slice = slice(pocket_offsets[sample], pocket_offsets[sample + 1])
            expected_members = torch.zeros(pocket_counts[sample], dtype=torch.bool)
            expected_members[list(record.target_cys_pocket_local_indices)] = True
            expected_reactive = torch.zeros(pocket_counts[sample], dtype=torch.bool)
            expected_reactive[record.target_sg_pocket_local_index] = True
            if (
                not torch.equal(supervision.target_residue_membership_mask[pocket_slice, 0], expected_members)
                or not torch.equal(supervision.target_residue_reactive_atom_mask[pocket_slice, 0], expected_reactive)
                or int(supervision.target_residue_reactive_atom_local_index[sample])
                != record.target_sg_pocket_local_index
                or int(supervision.target_residue_reactive_atom_flat_index[sample])
                != pocket_offsets[sample] + record.target_sg_pocket_local_index
            ):
                _fail("TARGET_CYS_SG_CONDITION_INVALID")

        offsets = supervision.pair_candidate_offsets.tolist()
        if (
            len(offsets) != batch_size + 1
            or offsets[0] != 0
            or any(left >= right for left, right in zip(offsets, offsets[1:]))
            or offsets[-1] != len(supervision.pair_candidate_batch_index)
        ):
            _fail("PAIR_CANDIDATE_OFFSETS_INVALID")
        pair_count = offsets[-1]
        pair_fields = (
            supervision.pair_candidate_batch_index,
            supervision.pair_candidate_ligand_local_index,
            supervision.pair_candidate_residue_local_index,
            supervision.pair_candidate_ligand_flat_index,
            supervision.pair_candidate_pocket_flat_index,
            supervision.pair_candidate_is_positive,
            supervision.pair_candidate_is_negative,
            supervision.pair_head_candidate_loss_mask,
        )
        if any(len(tensor) != pair_count for tensor in pair_fields):
            _fail("PAIR_CANDIDATE_FIELD_LENGTH_INVALID")
        if (
            not torch.equal(supervision.pair_candidate_is_negative, ~supervision.pair_candidate_is_positive)
            or bool(supervision.pair_head_candidate_loss_mask.any().item())
            or bool(supervision.pair_contrastive_sample_loss_mask.any().item())
            or not bool(supervision.pair_positive_candidate_valid.all().item())
            or bool((supervision.pair_negative_count <= 0).any().item())
        ):
            _fail("PAIR_LABEL_AVAILABLE_VS_LOSS_ACTIVE_INVALID")
        for sample, record in enumerate(batch.structural_records):
            start, end = offsets[sample:sample + 2]
            sample_slice = slice(start, end)
            if (
                not bool((supervision.pair_candidate_batch_index[sample_slice] == sample).all().item())
                or int(supervision.pair_candidate_is_positive[sample_slice].sum().item()) != 1
            ):
                _fail("PAIR_CANDIDATE_SAMPLE_OR_POSITIVE_COUNT_INVALID")
            lig_local = supervision.pair_candidate_ligand_local_index[sample_slice]
            pocket_local = supervision.pair_candidate_residue_local_index[sample_slice]
            if (
                not torch.equal(
                    supervision.pair_candidate_ligand_flat_index[sample_slice],
                    lig_local + ligand_offsets[sample],
                )
                or not torch.equal(
                    supervision.pair_candidate_pocket_flat_index[sample_slice],
                    pocket_local + pocket_offsets[sample],
                )
                or not set(pocket_local.tolist()).issubset(
                    set(record.target_cys_pocket_local_indices)
                )
            ):
                _fail("CROSS_SAMPLE_FLAT_INDEX_OR_CANDIDATE_DOMAIN_INVALID")
            positive_global = start + int(torch.nonzero(
                supervision.pair_candidate_is_positive[sample_slice], as_tuple=False
            )[0, 0])
            if (
                int(supervision.pair_positive_candidate_index[sample]) != positive_global
                or int(supervision.pair_candidate_ligand_local_index[positive_global])
                != record.ligand_reactive_retained_local_index
                or int(supervision.pair_candidate_residue_local_index[positive_global])
                != record.target_sg_pocket_local_index
                or int(supervision.pair_negative_count[sample]) != end - start - 1
            ):
                _fail("PAIR_POSITIVE_INDEX_CONSISTENCY_INVALID")
        geometry = supervision.pre_post_geometry_target_angstrom
        if (
            geometry.shape != (batch_size, 2)
            or not bool(torch.isnan(geometry[:, 0]).all().item())
            or not bool(torch.isfinite(geometry[:, 1]).all().item())
            or bool((geometry[:, 1] <= 0).any().item())
            or supervision.pre_post_geometry_component_valid_mask.tolist()
            != [[False, True]] * batch_size
            or bool(supervision.pre_post_geometry_component_loss_mask.any().item())
            or not bool(supervision.observed_complex_pair_distance_valid.all().item())
        ):
            _fail("POST_ONLY_GEOMETRY_CONTRACT_INVALID")
        expected_post = torch.tensor(
            [record.post_reactive_pair_distance_angstrom for record in batch.structural_records],
            dtype=torch.float32,
        )
        if (
            not torch.allclose(geometry[:, 1], expected_post, rtol=0, atol=1e-6)
            or not torch.allclose(
                supervision.observed_complex_pair_distance_angstrom[:, 0],
                expected_post,
                rtol=0,
                atol=1e-6,
            )
        ):
            _fail("POST_ONLY_GEOMETRY_RECOMPUTATION_MISMATCH")
        return True
    except Exception as error:
        _public_error(error)


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        + "\n"
    ).encode("utf-8")


def _csv_bytes(header: Sequence[str], rows: Sequence[Mapping[str, object]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=tuple(header), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({name: row.get(name, "") for name in header})
    return buffer.getvalue().encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _tensor_inventory(
    batch: CovapieBatch001ExistingSupervisionPreviewBatchV1,
) -> dict[str, dict[str, object]]:
    return {
        field.name: {
            "shape": list(getattr(batch.supervision, field.name).shape),
            "dtype": str(getattr(batch.supervision, field.name).dtype),
        }
        for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
    }


def build_covapie_batch001_bridge_artifacts_v1(
    *, repository_root: object = None, cache_root: object = None
) -> dict[str, bytes]:
    """Double-buildable deterministic evidence for the exact preview bridge."""

    try:
        repo = _require_root(repository_root, default=_DEFAULT_REPOSITORY_ROOT, reason="REPOSITORY_ROOT_INVALID")
        cache = _require_root(cache_root, default=_DEFAULT_CACHE_ROOT, reason="CACHE_ROOT_INVALID")
        source_bindings = structural_owner.verified_covapie_batch001_source_bindings_v1(
            repository_root=repo, cache_root=cache
        )
        records = structural_owner.build_covapie_batch001_positive_structural_records_v1(
            repository_root=repo, cache_root=cache
        )
        population = _tensorize_records_v1(
            records=records,
            task_ids=tuple(
                canonical_task_id_for_covapie_batch001_sample_v1(
                    sample_identity=record.sample_identity,
                    epoch=0,
                    task_schedule_seed=0,
                )
                for record in records
            ),
            epoch=0,
            task_schedule_seed=0,
        )
        validate_covapie_batch001_preview_batch_v1(
            population, require_exact13_population=True
        )
        source_header = (
            "source_category",
            "source_root_kind",
            "relative_path",
            "sha256",
            "consumed_for",
            "sha256_verified",
        )
        source_payload = _csv_bytes(source_header, source_bindings)
        readiness_header = (
            "canonical_event_id",
            "review_unit_id",
            "ligand_component_id",
            "role_profile",
            "applicable_task_ids",
            "not_applicable_task_ids",
            "historical_snapshot_mask_compatibility",
            "structural_input_ready",
            "feature_projection_ready",
            "target_condition_ready",
            "reactive_pair_ready",
            "role_partition_ready",
            "minimal_seed_ready",
            "anchor_distance_ready",
            "POST_geometry_ready",
            "pair_prediction_label_ready",
            "pair_contrastive_label_ready",
            "split_prediction_status",
            "predicted_split_if_any",
            "split_admission_authoritative",
            "sample_training_admitted",
            "model_integration_preview_ready",
        )
        readiness_rows = []
        for record in records:
            readiness_rows.append({
                "canonical_event_id": record.canonical_event_id,
                "review_unit_id": record.review_unit_id,
                "ligand_component_id": record.ligand_component_id,
                "role_profile": record.role_profile,
                "applicable_task_ids": "|".join(map(str, record.applicable_canonical_task_ids)),
                "not_applicable_task_ids": "|".join(map(str, record.not_applicable_canonical_task_ids)),
                "historical_snapshot_mask_compatibility": str(record.historical_snapshot_mask_compatibility).lower(),
                "structural_input_ready": "true",
                "feature_projection_ready": "true",
                "target_condition_ready": "true",
                "reactive_pair_ready": "true",
                "role_partition_ready": "true",
                "minimal_seed_ready": "false",
                "anchor_distance_ready": "true",
                "POST_geometry_ready": "true",
                "pair_prediction_label_ready": "true",
                "pair_contrastive_label_ready": "true",
                "split_prediction_status": record.split_prediction_status,
                "predicted_split_if_any": record.predicted_split_if_any,
                "split_admission_authoritative": "false",
                "sample_training_admitted": "false",
                "model_integration_preview_ready": "true",
            })
        readiness_payload = _csv_bytes(readiness_header, readiness_rows)
        evidence = {
            "schema_version": "covapie_batch001_model_bound_structural_evidence_v1",
            "artifact_role": "DETERMINISTIC_MODEL_INTEGRATION_PREVIEW_EVIDENCE_NOT_TRAINING_ADMISSION",
            "structural_source_root_kind": "REPOSITORY_PARENT_COVAPIE_STATE_BULK_MULTISOURCE_RCSB",
            "source_sha_bindings": list(source_bindings),
            "reused_structural_primitives": [
                "_validate_mmcif_payload",
                "parse_struct_conn_loop",
                "extract_atom_site_loop_rows_v0",
                "_connection_matches_event",
                "_endpoint_candidates",
                "_select_endpoint_pair",
                "_selected_ligand_atoms",
                "_selected_pocket_atoms(radius=6.0)",
                "parse_ccd_cif_v1",
                "project_type_symbols_to_checkpoint_heavy_v1",
            ],
            "pocket_contract": {
                "owner": "src/covalent_ext/covapie_bulk_cys_sg_dataset_expansion_v1.py",
                "selection": "protein_only_group_PDB_ATOM_retained_heavy_within_6.0_angstrom_of_selected_ligand",
                "radius_angstrom": 6.0,
            },
            "feature_contract": {
                "checkpoint_channel_order": "C:0|N:1|O:2|S:3|B:4|Br:5|Cl:6|P:7|I:8|F:9",
                "explicit_H_policy": "EXCLUDE_BEFORE_RETAINED_HEAVY_PROJECTION",
                "unsupported_non_H_policy": "REJECT_ENTIRE_SAMPLE_FAIL_CLOSED",
                "others_channel_present": False,
            },
            "event_count": 13,
            "events": [
                structural_owner.structural_record_as_evidence_dict_v1(record)
                for record in records
            ],
        }
        evidence_payload = _canonical_json_bytes(evidence)
        manifest = {
            "schema_version": "covapie_batch001_to_existing_mixed_profile_supervision_bridge_manifest_v1",
            "stage": "implement_covapie_batch001_to_existing_mixed_profile_supervision_bridge_v1",
            "artifact_role": "MODEL_INTEGRATION_PREVIEW_NOT_TRAINING_ADMISSION",
            "artifact_bindings": {
                SOURCE_BINDING_INVENTORY_V1: {"sha256": _sha256(source_payload)},
                EVENT_READINESS_V1: {"sha256": _sha256(readiness_payload)},
                STRUCTURAL_EVIDENCE_V1: {"sha256": _sha256(evidence_payload)},
            },
            "canonical_task_semantics": [
                {
                    "task_id": task_id,
                    "semantic_name": name,
                    "display_alias": alias,
                    "generated_role_ids": list(roles),
                }
                for task_id, name, alias, roles in CANONICAL_TASKS_V1
            ],
            "role_profile_contract": {
                STRICT_LINKER_PRESENT_V1: {"applicable_task_ids": [0, 1, 2, 3, 4]},
                DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1: {
                    "applicable_task_ids": [0, 3, 4],
                    "not_applicable_task_ids": [1, 2],
                    "not_applicable_status": "TASK_NOT_APPLICABLE_FOR_ROLE_PROFILE",
                },
            },
            "population_counts": {
                "positive_event_count": 13,
                "strict_profile_event_count": 11,
                "direct_profile_event_count": 2,
                "structural_input_ready_event_count": 13,
                "feature_projection_ready_event_count": 13,
                "target_condition_ready_event_count": 13,
                "reactive_pair_ready_event_count": 13,
                "role_partition_ready_event_count": 13,
                "minimal_seed_ready_event_count": 0,
                "anchor_distance_ready_event_count": 13,
                "POST_geometry_ready_event_count": 13,
                "pair_prediction_label_ready_event_count": 13,
                "pair_contrastive_label_ready_event_count": 13,
                "model_integration_preview_ready_event_count": 13,
                "in_memory_supervision_tensorized_event_count": 13,
                "split_admitted_event_count": 0,
                "sample_training_admitted_event_count": 0,
                "family_target_ready_event_count": 0,
                "excluded_task_domain_negative_event_count": 24,
                "excluded_ONL_event_count": 9,
            },
            "model_input_batch_shapes": {
                name: list(value.shape)
                for name, value in population.model_input_batch.items()
                if isinstance(value, torch.Tensor)
            },
            "in_memory_supervision_tensor_inventory": _tensor_inventory(population),
            "label_vs_loss_contract": {
                "roles_available": True,
                "target_condition_available": True,
                "reactive_pair_available": True,
                "anchor_distance_available": True,
                "POST_geometry_available": True,
                "pair_prediction_labels_available": True,
                "pair_contrastive_labels_available": True,
                "sample_training_admitted": False,
                "diffusion_loss_active": False,
                "pair_head_candidate_loss_active": False,
                "pair_contrastive_loss_active": False,
                "geometry_loss_active": False,
            },
            "minimal_seed_contract": {
                "authoritative_minimal_seed_event_count": 0,
                "ligand_minimal_seed_or_anchor_valid_all_false": True,
                "ligand_minimal_seed_or_anchor_mask_all_false": True,
                "sample_invalidated_by_missing_seed": False,
            },
            "POST_only_geometry_contract": {
                "component_0": "PRE_COVALENT_REACTIVE_PAIR_DISTANCE_ANGSTROM",
                "component_0_value": "NaN",
                "component_0_valid": False,
                "component_0_loss_active": False,
                "component_1": "POST_COVALENT_REACTIVE_PAIR_DISTANCE_ANGSTROM",
                "component_1_ready_event_count": 13,
                "component_1_loss_active": False,
            },
            "split_admission_contract": {
                "read_only_predicted_train_event_count": 6,
                "read_only_predicted_validation_event_count": 3,
                "leakage_evidence_incomplete_unassigned_event_count": 4,
                "split_admission_authoritative_event_count": 0,
                "sample_training_admitted_event_count": 0,
                "NDU_retained_in_model_integration_preview": True,
            },
            "architecture_impact": {
                "supervision_dataclass_reused": True,
                "supervision_dataclass_change_required": False,
                "core_model_architecture_change_required": False,
                "masking_py_change_required": False,
                "lightning_modules_change_required": False,
                "equivariant_diffusion_change_required": False,
                "new_Lightning_subclass_created": False,
            },
            "safety": {
                "network_used": False,
                "GPU_used": False,
                "model_forward_performed": False,
                "loss_performed": False,
                "backward_performed": False,
                "optimizer_step_performed": False,
                "Trainer_used": False,
                "checkpoint_read": False,
                "tensor_file_persisted": False,
                "published_batch001_predecessor_modified": False,
                "external_cache_modified": False,
                "historical_exact16_owner_modified": False,
            },
            "ready_for_gpt_review": True,
            "ready_for_training": False,
            "ready_for_training_reason": "FORMAL_BATCH001_SPLIT_LEAKAGE_ADMISSION_ABSENT",
            "recommended_next_step_exactly": "gpt_audit_batch001_supervision_bridge_then_build_formal_batch001_split_leakage_admission_successor_v1",
        }
        manifest_payload = _canonical_json_bytes(manifest)
        return {
            SOURCE_BINDING_INVENTORY_V1: source_payload,
            EVENT_READINESS_V1: readiness_payload,
            STRUCTURAL_EVIDENCE_V1: evidence_payload,
            MANIFEST_V1: manifest_payload,
        }
    except Exception as error:
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


def materialize_covapie_batch001_bridge_artifacts_v1(
    *, repository_root: object = None, cache_root: object = None
) -> dict[str, bytes]:
    """Write exactly the four authorized deterministic metadata artifacts."""

    try:
        repo = _require_root(repository_root, default=_DEFAULT_REPOSITORY_ROOT, reason="REPOSITORY_ROOT_INVALID")
        artifacts = build_covapie_batch001_bridge_artifacts_v1(
            repository_root=repo, cache_root=cache_root
        )
        output_root = repo / OUTPUT_ROOT_RELATIVE_V1
        if output_root.exists():
            unexpected = {
                path.name for path in output_root.iterdir()
                if path.name not in OUTPUT_FILENAMES_V1
            }
            if unexpected:
                _fail("OUTPUT_DIRECTORY_CONTAINS_UNEXPECTED_FILES")
        for name in OUTPUT_FILENAMES_V1:
            _atomic_write(output_root / name, artifacts[name])
        return artifacts
    except Exception as error:
        _public_error(error)
