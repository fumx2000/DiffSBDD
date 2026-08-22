"""Admission-aware real CPU forward/loss smoke for batch-001 train5 V1.

This successor consumes the published formal split authority, clones the
existing batch-001 preview supervision in memory, and executes the existing
Current11 DDPM/EGNN, auxiliary-head, and loss owners.  It deliberately never
creates an optimizer, calls backward, uses a Trainer, or writes an artifact.
"""

from __future__ import annotations

import contextlib
import csv
from dataclasses import dataclass, fields
import hashlib
import json
import math
from pathlib import Path
import stat
import sys
import time
from typing import Mapping, NoReturn, Sequence

import torch

from covalent_ext import covapie_batch001_positive_structural_input_v1 as structural_owner
from covalent_ext import (
    covapie_batch001_to_existing_mixed_profile_supervision_bridge_v1
    as preview_owner,
)
from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (
    CovapieCurrent11LossWeightsV1,
    compute_covapie_current11_training_losses_v1,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


__all__ = (
    "BATCH001_TRAIN5_ADMISSION_AWARE_CPU_FORWARD_LOSS_SMOKE_ERROR_V1",
    "FORMAL_TRAIN_EVENT_IDS_V1",
    "CovapieBatch001Train5FormalAuthorityAuditV1",
    "CovapieBatch001Train5CpuForwardLossSmokeResultV1",
    "audit_covapie_batch001_train5_formal_authority_v1",
    "verify_covapie_batch001_train5_formal_authority_file_v1",
    "verify_covapie_batch001_train5_checkpoint_file_v1",
    "run_covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1",
)


BATCH001_TRAIN5_ADMISSION_AWARE_CPU_FORWARD_LOSS_SMOKE_ERROR_V1 = (
    "COVAPIE_BATCH001_TRAIN5_ADMISSION_AWARE_CPU_FORWARD_LOSS_SMOKE_V1_ERROR"
)
IN_MEMORY_ADMISSION_STATUS_V1 = (
    "IN_MEMORY_ADMISSION_AWARE_SMOKE_ACTIVATION_ONLY"
)
MODEL_INITIALIZATION_SEED_V1 = 20260821
DIFFUSION_FORWARD_SEED_V1 = 11030037
TASK_SCHEDULE_EPOCH_V1 = 0
TASK_SCHEDULE_SEED_V1 = 0
DETERMINISM_ABSOLUTE_TOLERANCE_V1 = 1.0e-7
DETERMINISM_RELATIVE_TOLERANCE_V1 = 1.0e-7

FORMAL_TRAIN_EVENT_IDS_V1 = (
    "COVAPIE_CYS_SG_EVENT_V1:3LOK:A:CYS:345-:SG:C:DJK:C51",
    "COVAPIE_CYS_SG_EVENT_V1:3LOK:B:CYS:345-:SG:D:DJK:C51",
    "COVAPIE_CYS_SG_EVENT_V1:2ZK1:A:CYS:285-:SG:C:PTG:C8",
    "COVAPIE_CYS_SG_EVENT_V1:2ZK1:B:CYS:285-:SG:D:PTG:C8",
    "COVAPIE_CYS_SG_EVENT_V1:2ZK2:A:CYS:285-:SG:D:PTG:C8",
)
EXPECTED_LIGAND_COUNTS_V1 = (23, 23, 23, 23, 23)
EXPECTED_POCKET_COUNTS_V1 = (103, 118, 124, 110, 123)

FORMAL_AUTHORITY_RELATIVE_PATH_V1 = Path(
    "data/derived/covalent_small/"
    "covapie_batch001_formal_split_leakage_admission_v1/"
    "covapie_batch001_formal_event_split_admission_v1.csv"
)
FORMAL_COMPONENT_REGISTRY_FILENAME_V1 = (
    "covapie_batch001_formal_leakage_component_registry_v1.json"
)
FORMAL_SOURCE_INVENTORY_FILENAME_V1 = (
    "covapie_batch001_split_admission_source_binding_inventory_v1.csv"
)
FORMAL_MANIFEST_FILENAME_V1 = (
    "covapie_batch001_formal_split_leakage_admission_manifest_v1.json"
)
CHECKPOINT_RELATIVE_PATH_V1 = Path("checkpoints/crossdocked_fullatom_cond.ckpt")

FORMAL_AUTHORITY_SHA256_V1 = (
    "d3416ed382e6f208f79f2285138893dde3bf627653606fed8a4c3c73666001c7"
)
FORMAL_COMPONENT_REGISTRY_SHA256_V1 = (
    "76e6ecae7dfde7c9e5081a0164f9a72628e4f30550e831a8f8ba5cd3d1d16544"
)
FORMAL_SOURCE_INVENTORY_SHA256_V1 = (
    "946d1b4cce5c4785a20cca1be557d071015b11e89311282bf4814a6c22e91fdc"
)
FORMAL_MANIFEST_SHA256_V1 = (
    "79fb2889a38016f2526adfb0f3c531a14f1bb32acc825b5c989c55217c0925dd"
)
CHECKPOINT_SHA256_V1 = (
    "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
)

BOUND_OWNER_SHA256_V1 = (
    (
        "src/covalent_ext/covapie_batch001_formal_split_leakage_admission_v1.py",
        "9841cb03ef67a6e8bbcffe1cbe0d7332a575da0e2ce5e3208a965afa45ad0d0c",
    ),
    (
        "src/covalent_ext/covapie_batch001_positive_structural_input_v1.py",
        "c4cada3c5d3e8e86176b097cc5546854122162055437e4667288ba2f82629067",
    ),
    (
        "src/covalent_ext/covapie_batch001_to_existing_mixed_profile_supervision_bridge_v1.py",
        "168c819e0422b110880676c1a99b82a8531e94f9849a3dcfb7d4c45dbdd73400",
    ),
    (
        "src/covalent_ext/covapie_current11_training_tensorizer_v1.py",
        "9fdc3f7f101fab5e5e5452e3d8e9f9b0b1e6e5fa8254a261f36310a1dfd0b606",
    ),
    (
        "src/covalent_ext/covapie_current11_auxiliary_model_and_loss_v1.py",
        "5bf91b3af56ec0e5c2dec3ebb13e56695ca74c17bbbbb65f35e8d9249d6fc60f",
    ),
    (
        "src/covalent_ext/covapie_current11_training_lightning_module_v1.py",
        "d3d21b920785f791652cb456465a8bb375a09cdf0e24e5e84415b01f82cd6485",
    ),
    (
        "src/covalent_ext/covapie_current11_checkpoint_migration_v1.py",
        "fc36fb23844e6e5d2be2e1e43fcd0afe580d8b86faacca31bd69b8fe70f75ef3",
    ),
    (
        "src/covalent_ext/covapie_current11_checkpoint_migration_and_real_one_batch_train_path_smoke_v1.py",
        "e92d68fc7126eb2c3e20341ad1a3ae3dd48509533761694c482edca01d70df61",
    ),
    (
        "src/covalent_ext/covapie_expanded_cys_sg_mixed_profile_lightning_training_bridge_v1.py",
        "cabb479e35df0cd86c72cdca11903deaf03cf3c134d95d1c067e4b671e2b3fb2",
    ),
)

_DEFAULT_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_STATE_ROOT = _DEFAULT_REPOSITORY_ROOT.parent / "covapie-state"
_DEFAULT_CACHE_ROOT = (
    _DEFAULT_STATE_ROOT / "bulk-multisource-cys-sg-v1/rcsb"
)
_PATH_TYPE = type(Path())


@dataclass(frozen=True)
class CovapieBatch001Train5FormalAuthorityAuditV1:
    formal_train_event_ids: tuple[str, ...]
    formal_validation_event_ids: tuple[str, ...]
    formal_unresolved_event_ids: tuple[str, ...]
    non_target_component_event_ids: tuple[str, ...]
    DJK_train_event_count: int
    PTG_train_event_count: int
    LN5_validation_event_count: int
    PX5_validation_event_count: int
    NDU_unresolved_event_count: int
    cross_split_leakage_violation_count: int


@dataclass(frozen=True)
class CovapieBatch001Train5CpuForwardLossSmokeResultV1:
    implementation_status: str
    in_memory_admission_status: str
    formal_train_event_ids: tuple[str, ...]
    formal_validation_event_ids: tuple[str, ...]
    formal_unresolved_event_ids: tuple[str, ...]
    scheduled_task_ids: tuple[int, ...]
    five_epoch_task_schedule_audit: tuple[tuple[int, ...], ...]
    ligand_counts: tuple[int, ...]
    pocket_counts: tuple[int, ...]
    ligand_node_count: int
    pocket_node_count: int
    pair_candidate_count: int
    pair_positive_count: int
    pair_negative_count: int
    pair_positive_candidate_indices: tuple[int, ...]
    diffusion_timesteps: tuple[int, ...]
    tensor_shapes: tuple[tuple[str, tuple[int, ...]], ...]
    runtime_losses: tuple[tuple[str, float], ...]
    repeated_runtime_losses: tuple[tuple[str, float], ...]
    maximum_repeated_loss_absolute_difference: float
    base_diffusion_valid_sample_count: int
    covalent_pair_prediction_valid_sample_count: int
    pre_post_geometry_valid_sample_count: int
    covalent_pair_contrastive_valid_sample_count: int
    PRE_geometry_valid_sample_count: int
    current_loss_weights: tuple[tuple[str, float], ...]
    geometry_contribution_to_loss_total: float
    loss_total_requires_grad: bool
    geometry_loss_requires_grad: bool
    geometry_head_autograd_path_in_loss_total: bool
    geometry_head_nonzero_gradient_from_loss_total_in_future_backward: bool
    parameter_gradients_created: bool
    model_state_modified_by_smoke: bool
    migration_counts: tuple[tuple[str, int], ...]
    migration_missing_keys: tuple[str, ...]
    migration_unexpected_keys: tuple[str, ...]
    architecture: tuple[tuple[str, object], ...]
    bound_owner_sha256: tuple[tuple[str, str], ...]
    formal_artifact_sha256: tuple[tuple[str, str], ...]
    checkpoint_sha256: str
    checkpoint_modified: bool
    repeat_count: int
    elapsed_seconds: float
    optimizer_created: bool
    optimizer_step_performed: bool
    backward_performed: bool
    Trainer_used: bool
    training_performed: bool
    CPU_only: bool
    GPU_used: bool
    network_used: bool
    supervision_dataclass_reused: bool
    architecture_modification_required_before_backward_smoke: bool
    data_label_family_or_PRE_blocker_required_before_backward_smoke: bool
    geometry_weight_policy_decision_required_before_backward_smoke: bool
    ready_for_single_backward_optimizer_step_smoke: bool


@dataclass(frozen=True)
class _PreparedTrain5BatchV1:
    authority: CovapieBatch001Train5FormalAuthorityAuditV1
    sample_identities: tuple[str, ...]
    structural_records: tuple[
        structural_owner.CovapieBatch001PositiveStructuralRecordV1, ...
    ]
    model_input_batch: dict[str, object]
    preview_supervision: CovapieCurrent11TrainingSupervisionTensorsV1
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1
    scheduled_task_ids: tuple[int, ...]
    five_epoch_task_schedule_audit: tuple[tuple[int, ...], ...]
    static_five_mask_audit_passed: bool


@dataclass(frozen=True)
class _SingleForwardObservationV1:
    scheduled_task_ids: tuple[int, ...]
    diffusion_timesteps: tuple[int, ...]
    tensor_shapes: tuple[tuple[str, tuple[int, ...]], ...]
    losses: tuple[tuple[str, float], ...]
    counts: tuple[int, int, int, int]
    migration_counts: tuple[tuple[str, int], ...]
    migration_missing_keys: tuple[str, ...]
    migration_unexpected_keys: tuple[str, ...]
    architecture: tuple[tuple[str, object], ...]
    loss_total_requires_grad: bool
    geometry_loss_requires_grad: bool
    gradients_created: bool
    state_modified: bool


class _SmokeInvariantError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _fail(reason: str) -> NoReturn:
    raise _SmokeInvariantError(reason)


def _public_error(error: BaseException) -> NoReturn:
    if type(error) is ValueError and str(error).startswith(
        BATCH001_TRAIN5_ADMISSION_AWARE_CPU_FORWARD_LOSS_SMOKE_ERROR_V1
    ):
        raise error
    reason = error.reason if isinstance(error, _SmokeInvariantError) else "OWNER_REJECTED"
    raise ValueError(
        f"{BATCH001_TRAIN5_ADMISSION_AWARE_CPU_FORWARD_LOSS_SMOKE_ERROR_V1}:"
        f"{reason}"
    ) from error


def _require_directory(value: object, *, default: Path, reason: str) -> Path:
    path = default if value is None else value
    if type(path) is not _PATH_TYPE or not path.is_absolute():
        _fail(reason)
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise _SmokeInvariantError(reason) from error
    if resolved != path or path.is_symlink() or not path.is_dir():
        _fail(reason)
    return path


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            _fail("BOUND_FILE_NOT_SAFE_REGULAR_FILE")
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise _SmokeInvariantError("BOUND_FILE_READ_FAILED") from error
    return digest.hexdigest()


def _verify_sha(path: Path, expected: str, reason: str) -> str:
    if type(path) is not _PATH_TYPE or not path.is_absolute():
        _fail(reason)
    actual = _sha256_file(path)
    if actual != expected:
        _fail(reason)
    return actual


def verify_covapie_batch001_train5_formal_authority_file_v1(
    *, formal_authority_path: Path
) -> str:
    """Verify an event-admission file against the exact published digest."""

    try:
        return _verify_sha(
            formal_authority_path,
            FORMAL_AUTHORITY_SHA256_V1,
            "FORMAL_AUTHORITY_SHA256_MISMATCH",
        )
    except BaseException as error:
        _public_error(error)


def verify_covapie_batch001_train5_checkpoint_file_v1(
    *, checkpoint_path: Path
) -> str:
    """Verify a checkpoint file before any torch deserialization occurs."""

    try:
        return _verify_sha(
            checkpoint_path,
            CHECKPOINT_SHA256_V1,
            "CHECKPOINT_SHA256_MISMATCH",
        )
    except BaseException as error:
        _public_error(error)


def _verify_bound_owners(repository_root: Path) -> tuple[tuple[str, str], ...]:
    actual: list[tuple[str, str]] = []
    for relative, expected in BOUND_OWNER_SHA256_V1:
        path = repository_root / relative
        digest = _verify_sha(path, expected, "BOUND_OWNER_SHA256_MISMATCH:" + relative)
        actual.append((relative, digest))
    return tuple(actual)


def _read_json(path: Path, expected_sha: str, reason: str) -> dict[str, object]:
    _verify_sha(path, expected_sha, reason + "_SHA256_MISMATCH")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise _SmokeInvariantError(reason + "_INVALID") from error
    if type(value) is not dict:
        _fail(reason + "_INVALID")
    return value


def _formal_authority_audit_impl(
    *, repository_root: Path,
) -> CovapieBatch001Train5FormalAuthorityAuditV1:
    event_path = repository_root / FORMAL_AUTHORITY_RELATIVE_PATH_V1
    verify_covapie_batch001_train5_formal_authority_file_v1(
        formal_authority_path=event_path
    )
    root = event_path.parent
    registry = _read_json(
        root / FORMAL_COMPONENT_REGISTRY_FILENAME_V1,
        FORMAL_COMPONENT_REGISTRY_SHA256_V1,
        "FORMAL_COMPONENT_REGISTRY",
    )
    manifest = _read_json(
        root / FORMAL_MANIFEST_FILENAME_V1,
        FORMAL_MANIFEST_SHA256_V1,
        "FORMAL_MANIFEST",
    )
    _verify_sha(
        root / FORMAL_SOURCE_INVENTORY_FILENAME_V1,
        FORMAL_SOURCE_INVENTORY_SHA256_V1,
        "FORMAL_SOURCE_INVENTORY_SHA256_MISMATCH",
    )
    try:
        with event_path.open(newline="", encoding="utf-8") as handle:
            rows = tuple(csv.DictReader(handle))
    except (OSError, UnicodeError, csv.Error) as error:
        raise _SmokeInvariantError("FORMAL_AUTHORITY_CSV_INVALID") from error
    required = {
        "canonical_event_id",
        "ligand_component_id",
        "assigned_split",
        "split_admission_authoritative",
        "split_admission_status",
        "sample_training_admitted",
        "model_training_activation_authorized",
    }
    if (
        len(rows) != 13
        or not rows
        or not required.issubset(rows[0])
        or len({row["canonical_event_id"] for row in rows}) != 13
        or {row["canonical_event_id"] for row in rows}
        != set(structural_owner.BATCH001_POSITIVE_EVENT_IDS_V1)
        or any(row["sample_training_admitted"] != "false" for row in rows)
        or any(
            row["model_training_activation_authorized"] != "false"
            for row in rows
        )
    ):
        _fail("FORMAL_AUTHORITY_POPULATION_OR_PERSISTENT_ACTIVATION_INVALID")

    train = tuple(
        row["canonical_event_id"]
        for row in rows
        if row["split_admission_authoritative"] == "true"
        and row["assigned_split"] == "train"
        and row["split_admission_status"]
        == "FORMALLY_ADMITTED_TO_FROZEN_SPLIT"
    )
    validation = tuple(
        row["canonical_event_id"]
        for row in rows
        if row["split_admission_authoritative"] == "true"
        and row["assigned_split"] == "validation"
        and row["split_admission_status"]
        == "FORMALLY_ADMITTED_TO_FROZEN_SPLIT"
    )
    unresolved = tuple(
        row["canonical_event_id"]
        for row in rows
        if row["split_admission_authoritative"] == "false"
        and row["assigned_split"] == ""
        and row["split_admission_status"] == "UNRESOLVED_FAIL_CLOSED"
    )
    by_id = {row["canonical_event_id"]: row for row in rows}
    if (
        train != FORMAL_TRAIN_EVENT_IDS_V1
        or len(validation) != 4
        or len(unresolved) != 4
        or {by_id[item]["ligand_component_id"] for item in train}
        != {"DJK", "PTG"}
        or sum(by_id[item]["ligand_component_id"] == "DJK" for item in train)
        != 2
        or sum(by_id[item]["ligand_component_id"] == "PTG" for item in train)
        != 3
        or sum(
            by_id[item]["ligand_component_id"] == "LN5" for item in validation
        )
        != 2
        or sum(
            by_id[item]["ligand_component_id"] == "PX5" for item in validation
        )
        != 2
        or any(by_id[item]["ligand_component_id"] != "NDU" for item in unresolved)
    ):
        _fail("FORMAL_TRAIN_VALIDATION_UNRESOLVED_POPULATION_INVALID")

    components = registry.get("components")
    if type(components) is not list or len(components) != 4:
        _fail("FORMAL_COMPONENT_REGISTRY_INVALID")
    non_target = tuple(
        event_id
        for component in components
        for event_id in component.get("non_target_component_event_ids", ())
    )
    if (
        not non_target
        or set(non_target) & set(structural_owner.BATCH001_POSITIVE_EVENT_IDS_V1)
        or any(type(item) is not str for item in non_target)
        or any(
            component.get("non_target_members_are_training_samples") is not False
            or component.get("non_target_members_inherit_split_reservation_only")
            is not True
            for component in components
        )
    ):
        _fail("NON_TARGET_COMPONENT_MEMBERSHIP_INVALID")
    counts = manifest.get("population_counts")
    cross = manifest.get("cross_component_leakage_audit")
    if (
        type(counts) is not dict
        or counts.get("formal_train_event_count") != 5
        or counts.get("formal_validation_event_count") != 4
        or counts.get("formal_unresolved_event_count") != 4
        or counts.get("model_training_activation_authorized_event_count") != 0
        or type(cross) is not dict
        or cross.get("cross_split_leakage_violation_count") != 0
        or manifest.get("ready_for_admission_aware_cpu_model_smoke") is not True
        or manifest.get("ready_for_training") is not False
    ):
        _fail("FORMAL_MANIFEST_ADMISSION_SEMANTICS_INVALID")
    return CovapieBatch001Train5FormalAuthorityAuditV1(
        formal_train_event_ids=train,
        formal_validation_event_ids=validation,
        formal_unresolved_event_ids=unresolved,
        non_target_component_event_ids=non_target,
        DJK_train_event_count=2,
        PTG_train_event_count=3,
        LN5_validation_event_count=2,
        PX5_validation_event_count=2,
        NDU_unresolved_event_count=4,
        cross_split_leakage_violation_count=0,
    )


def audit_covapie_batch001_train5_formal_authority_v1(
    *, repository_root: Path | None = None
) -> CovapieBatch001Train5FormalAuthorityAuditV1:
    """Derive, rather than assume, the exact formal-train population."""

    try:
        repo = _require_directory(
            repository_root,
            default=_DEFAULT_REPOSITORY_ROOT,
            reason="REPOSITORY_ROOT_INVALID",
        )
        return _formal_authority_audit_impl(repository_root=repo)
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


def _clone_admitted_supervision(
    preview: CovapieCurrent11TrainingSupervisionTensorsV1,
    ligand_batch_index: torch.Tensor,
) -> CovapieCurrent11TrainingSupervisionTensorsV1:
    values = {
        field.name: getattr(preview, field.name).clone()
        for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
    }
    admitted = torch.ones_like(preview.sample_training_admitted)
    valid_by_node = preview.canonical_task_valid[ligand_batch_index]
    admitted_by_node = admitted[ligand_batch_index]
    values["sample_training_admitted"] = admitted
    values["ligand_active_diffusion_loss_mask"] = (
        preview.ligand_base_generation_mask
        & valid_by_node.unsqueeze(1)
        & admitted_by_node.unsqueeze(1)
    )
    values["pair_head_candidate_loss_mask"] = torch.ones_like(
        preview.pair_head_candidate_loss_mask
    )
    values["pair_contrastive_sample_loss_mask"] = torch.ones_like(
        preview.pair_contrastive_sample_loss_mask
    )
    values["pre_post_geometry_component_loss_mask"] = (
        preview.pre_post_geometry_component_valid_mask
        & admitted.unsqueeze(1)
    )
    admitted_supervision = CovapieCurrent11TrainingSupervisionTensorsV1(**values)
    if (
        bool(preview.sample_training_admitted.any().item())
        or bool(preview.ligand_active_diffusion_loss_mask.any().item())
        or bool(preview.pair_head_candidate_loss_mask.any().item())
        or bool(preview.pair_contrastive_sample_loss_mask.any().item())
        or bool(preview.pre_post_geometry_component_loss_mask.any().item())
    ):
        _fail("PUBLISHED_PREVIEW_TENSORS_MUTATED")
    return admitted_supervision


def _validate_requested_population(
    requested: object,
    authority: CovapieBatch001Train5FormalAuthorityAuditV1,
) -> tuple[str, ...]:
    value = (
        authority.formal_train_event_ids
        if requested is None
        else tuple(requested)
        if type(requested) in (tuple, list)
        else None
    )
    if (
        value is None
        or any(type(item) is not str for item in value)
        or value != authority.formal_train_event_ids
    ):
        _fail("ONLY_EXACT_FORMALLY_ADMITTED_TRAIN5_MAY_BE_SMOKE_ACTIVATED")
    return value


def _static_five_mask_audit(
    records: Sequence[structural_owner.CovapieBatch001PositiveStructuralRecordV1],
) -> bool:
    for task_id in range(5):
        static = preview_owner._tensorize_records_v1(
            records=records,
            task_ids=(task_id,) * 5,
            epoch=TASK_SCHEDULE_EPOCH_V1,
            task_schedule_seed=TASK_SCHEDULE_SEED_V1,
        )
        supervision = static.supervision
        if (
            supervision.canonical_task_id.tolist() != [task_id] * 5
            or not bool(supervision.canonical_task_valid.all().item())
            or not bool(supervision.ligand_role_valid.all().item())
            or not bool(
                (
                    supervision.ligand_base_generation_mask
                    ^ supervision.ligand_base_fixed_mask
                ).all().item()
            )
        ):
            _fail("STATIC_FIVE_MASK_CONTRACT_INVALID")
        ligand_mask = static.model_input_batch["lig_mask"]
        if not isinstance(ligand_mask, torch.Tensor):
            _fail("STATIC_FIVE_MASK_MEMBERSHIP_INVALID")
        for sample in range(5):
            if not bool(
                supervision.ligand_base_generation_mask[:, 0][
                    ligand_mask == sample
                ].any().item()
            ):
                _fail("STATIC_FIVE_MASK_EMPTY_GENERATED_SET")
    return True


def _prepare_train5_batch(
    *,
    repository_root: Path,
    cache_root: Path,
    requested_sample_identities: object,
) -> _PreparedTrain5BatchV1:
    authority = _formal_authority_audit_impl(repository_root=repository_root)
    requested = _validate_requested_population(requested_sample_identities, authority)
    records_all = structural_owner.build_covapie_batch001_positive_structural_records_v1(
        repository_root=repository_root,
        cache_root=cache_root,
    )
    by_identity = {record.sample_identity: record for record in records_all}
    if set(by_identity) != set(structural_owner.BATCH001_POSITIVE_EVENT_IDS_V1):
        _fail("STRUCTURAL_OWNER_EXACT13_POPULATION_INVALID")
    records = tuple(by_identity[identity] for identity in requested)
    ligand_counts = tuple(len(record.ligand_retained_heavy_atoms) for record in records)
    pocket_counts = tuple(len(record.pocket_retained_heavy_atoms) for record in records)
    if (
        ligand_counts != EXPECTED_LIGAND_COUNTS_V1
        or pocket_counts != EXPECTED_POCKET_COUNTS_V1
        or any(record.role_profile != preview_owner.STRICT_LINKER_PRESENT_V1 for record in records)
        or any(record.applicable_canonical_task_ids != (0, 1, 2, 3, 4) for record in records)
        or any(record.protein_residue_name != "CYS" for record in records)
        or any(record.protein_reactive_atom_id != "SG" for record in records)
        or any(record.split_admission_authoritative is not False for record in records)
        or any(record.sample_training_admitted is not False for record in records)
    ):
        _fail("TRAIN5_STRUCTURAL_OR_PREVIEW_EVIDENCE_INVALID")
    tasks = tuple(
        preview_owner.canonical_task_id_for_covapie_batch001_sample_v1(
            sample_identity=identity,
            epoch=TASK_SCHEDULE_EPOCH_V1,
            task_schedule_seed=TASK_SCHEDULE_SEED_V1,
        )
        for identity in requested
    )
    cycles = tuple(
        tuple(
            preview_owner.canonical_task_id_for_covapie_batch001_sample_v1(
                sample_identity=identity,
                epoch=epoch,
                task_schedule_seed=TASK_SCHEDULE_SEED_V1,
            )
            for epoch in range(5)
        )
        for identity in requested
    )
    if any(set(cycle) != set(range(5)) for cycle in cycles):
        _fail("FIVE_EPOCH_TASK_DOMAIN_SCHEDULING_AUDIT_FAILED")
    preview = preview_owner._tensorize_records_v1(
        records=records,
        task_ids=tasks,
        epoch=TASK_SCHEDULE_EPOCH_V1,
        task_schedule_seed=TASK_SCHEDULE_SEED_V1,
    )
    if not preview_owner.validate_covapie_batch001_preview_batch_v1(preview):
        _fail("TRAIN5_PREVIEW_VALIDATION_FAILED")
    ligand_mask = preview.model_input_batch.get("lig_mask")
    if not isinstance(ligand_mask, torch.Tensor):
        _fail("TRAIN5_LIGAND_MEMBERSHIP_INVALID")
    admitted = _clone_admitted_supervision(preview.supervision, ligand_mask)
    pair_count = len(admitted.pair_candidate_batch_index)
    if (
        not isinstance(admitted, CovapieCurrent11TrainingSupervisionTensorsV1)
        or len(fields(CovapieCurrent11TrainingSupervisionTensorsV1)) != 37
        or not bool(admitted.sample_training_admitted.all().item())
        or not bool(admitted.canonical_task_valid.all().item())
        or not bool(admitted.ligand_role_valid.all().item())
        or not torch.equal(
            admitted.ligand_active_diffusion_loss_mask,
            admitted.ligand_base_generation_mask,
        )
        or bool(admitted.ligand_minimal_seed_or_anchor_valid.any().item())
        or bool(admitted.ligand_minimal_seed_or_anchor_mask.any().item())
        or not bool(admitted.ligand_anchor_distance_valid.all().item())
        or not bool(torch.isfinite(admitted.ligand_anchor_distance_angstrom).all().item())
        or bool((admitted.ligand_anchor_distance_angstrom < 0).any().item())
        or not bool(admitted.target_residue_condition_valid.all().item())
        or int(admitted.target_residue_reactive_atom_mask.sum().item()) != 5
        or pair_count <= 5
        or int(admitted.pair_candidate_is_positive.sum().item()) != 5
        or int(admitted.pair_candidate_is_negative.sum().item()) != pair_count - 5
        or not bool(admitted.pair_positive_candidate_valid.all().item())
        or not bool((admitted.pair_negative_count > 0).all().item())
        or not bool(admitted.pair_head_candidate_loss_mask.all().item())
        or not bool(admitted.pair_contrastive_sample_loss_mask.all().item())
        or admitted.pre_post_geometry_component_valid_mask.tolist()
        != [[False, True]] * 5
        or admitted.pre_post_geometry_component_loss_mask.tolist()
        != [[False, True]] * 5
        or not bool(torch.isnan(admitted.pre_post_geometry_target_angstrom[:, 0]).all().item())
        or not bool(torch.isfinite(admitted.pre_post_geometry_target_angstrom[:, 1]).all().item())
        or bool((admitted.pre_post_geometry_target_angstrom[:, 1] <= 0).any().item())
    ):
        _fail("TRAIN5_EPHEMERAL_SUPERVISION_ACTIVATION_INVALID")
    pocket_mask = preview.model_input_batch.get("pocket_mask")
    if not isinstance(pocket_mask, torch.Tensor):
        _fail("TRAIN5_POCKET_MEMBERSHIP_INVALID")
    if (
        not torch.equal(
            admitted.pair_candidate_batch_index,
            ligand_mask[admitted.pair_candidate_ligand_flat_index],
        )
        or not torch.equal(
            admitted.pair_candidate_batch_index,
            pocket_mask[admitted.pair_candidate_pocket_flat_index],
        )
    ):
        _fail("CROSS_SAMPLE_PAIR_CANDIDATE_DETECTED")
    for sample, record in enumerate(records):
        positive = int(admitted.pair_positive_candidate_index[sample].item())
        if (
            int(admitted.pair_candidate_ligand_local_index[positive].item())
            != record.ligand_reactive_retained_local_index
            or int(admitted.pair_candidate_residue_local_index[positive].item())
            != record.target_sg_pocket_local_index
        ):
            _fail("POSITIVE_PAIR_CANDIDATE_IDENTITY_INVALID")
    return _PreparedTrain5BatchV1(
        authority=authority,
        sample_identities=requested,
        structural_records=records,
        model_input_batch=preview.model_input_batch,
        preview_supervision=preview.supervision,
        supervision=admitted,
        scheduled_task_ids=tasks,
        five_epoch_task_schedule_audit=cycles,
        static_five_mask_audit_passed=_static_five_mask_audit(records),
    )


def _model_state_snapshot(model: torch.nn.Module) -> dict[str, torch.Tensor]:
    state = model.state_dict()
    if not state or any(value.device.type != "cpu" for value in state.values()):
        _fail("MODEL_STATE_NOT_CPU")
    return {name: value.detach().clone() for name, value in state.items()}


def _state_fingerprint(state: Mapping[str, torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for name in sorted(state):
        value = state[name]
        if not isinstance(value, torch.Tensor) or value.device.type != "cpu":
            _fail("MODEL_STATE_FINGERPRINT_DOMAIN_INVALID")
        contiguous = value.detach().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(contiguous.dtype).encode("ascii"))
        digest.update(str(tuple(contiguous.shape)).encode("ascii"))
        digest.update(contiguous.view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def _all_model_gradients_none(model: torch.nn.Module) -> bool:
    return all(parameter.grad is None for parameter in model.parameters())


def _assert_cpu_tensors(value: object) -> None:
    if isinstance(value, torch.Tensor):
        if value.device.type != "cpu":
            _fail("NON_CPU_TENSOR_DETECTED")
    elif type(value) is dict:
        for item in value.values():
            _assert_cpu_tensors(item)
    elif isinstance(value, CovapieCurrent11TrainingSupervisionTensorsV1):
        for field in fields(value):
            _assert_cpu_tensors(getattr(value, field.name))


@contextlib.contextmanager
def _repository_import_path(repository_root: Path):
    root_text = str(repository_root)
    inserted = root_text not in sys.path
    if inserted:
        sys.path.insert(0, root_text)
    try:
        yield
    finally:
        if inserted:
            try:
                sys.path.remove(root_text)
            except ValueError as error:
                raise _SmokeInvariantError(
                    "REPOSITORY_IMPORT_PATH_RESTORE_FAILED"
                ) from error


def _single_forward(
    *,
    repository_root: Path,
    state_root: Path,
    checkpoint_state_dict: object,
    prepared: _PreparedTrain5BatchV1,
) -> _SingleForwardObservationV1:
    with _repository_import_path(repository_root):
        from covalent_ext import (  # noqa: PLC0415
            covapie_current11_checkpoint_migration_v1 as checkpoint_owner,
        )
        from covalent_ext import (  # noqa: PLC0415
            covapie_current11_checkpoint_migration_and_real_one_batch_train_path_smoke_v1
            as instantiation_owner,
        )
        from covalent_ext.covapie_current11_training_lightning_module_v1 import (  # noqa: PLC0415
            run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1,
        )

    torch.random.default_generator.manual_seed(MODEL_INITIALIZATION_SEED_V1)
    model = instantiation_owner._instantiate_current11_model_v1(
        repo_root=repository_root,
        state_root=state_root,
        device="cpu",
    )
    migration = checkpoint_owner.migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
        model=model,
        checkpoint_state_dict=checkpoint_state_dict,
    )
    migration_count_names = (
        "checkpoint_key_count",
        "target_model_key_count",
        "shared_key_count",
        "target_only_key_count",
        "checkpoint_only_key_count",
        "shared_shape_mismatch_count",
        "shared_checkpoint_tensor_equality_count",
    )
    migration_counts = tuple(
        (name, int(migration[name])) for name in migration_count_names
    )
    if (
        dict(migration_counts)
        != {
            "checkpoint_key_count": 122,
            "target_model_key_count": 141,
            "shared_key_count": 122,
            "target_only_key_count": 19,
            "checkpoint_only_key_count": 0,
            "shared_shape_mismatch_count": 0,
            "shared_checkpoint_tensor_equality_count": 122,
        }
        or len(migration["target_only_auxiliary_keys"]) != 18
        or migration["migration_missing_keys"] != ()
        or migration["migration_unexpected_keys"] != ()
        or migration["full_target_strict_load"] is not True
    ):
        _fail("CHECKPOINT_MIGRATION_COUNTS_OR_POLICY_INVALID")
    before = _model_state_snapshot(model)
    before_fingerprint = _state_fingerprint(before)
    if not _all_model_gradients_none(model):
        _fail("PARAMETER_GRADIENT_PRESENT_BEFORE_FORWARD")

    dynamics = model.ddpm.dynamics
    architecture = (
        ("device", "cpu"),
        ("mode", model.mode),
        ("pocket_representation", model.pocket_representation),
        ("atom_nf", model.atom_nf),
        ("target_residue_atom_conditioning", dynamics.target_residue_atom_conditioning),
        ("virtual_nodes", model.virtual_nodes),
        ("loss_type", model.ddpm.loss_type),
        ("joint_nf", model.covapie_current11_auxiliary_model_v1.joint_nf),
        ("hidden_nf", dynamics.egnn.hidden_nf),
        ("egnn_layers", dynamics.egnn.n_layers),
    )
    if dict(architecture) != {
        "device": "cpu",
        "mode": "pocket_conditioning",
        "pocket_representation": "full-atom",
        "atom_nf": 10,
        "target_residue_atom_conditioning": True,
        "virtual_nodes": False,
        "loss_type": "l2",
        "joint_nf": 32,
        "hidden_nf": 128,
        "egnn_layers": 5,
    }:
        _fail("REAL_MODEL_ARCHITECTURE_INVALID")
    if any(
        parameter.device.type != "cpu" for parameter in model.parameters()
    ) or any(buffer.device.type != "cpu" for buffer in model.buffers()):
        _fail("REAL_MODEL_DEVICE_INVALID")
    _assert_cpu_tensors(prepared.model_input_batch)
    _assert_cpu_tensors(prepared.supervision)
    model.train()
    if model.training is not True or model.ddpm.training is not True:
        _fail("REAL_MODEL_TRAINING_MODE_REQUIRED")
    ligand, pocket = model.get_ligand_and_pocket(prepared.model_input_batch)
    supervision = prepared.supervision
    indicator = supervision.target_residue_reactive_atom_mask[:, 0]
    role_delta = model.covapie_current11_auxiliary_model_v1.encode_role_mask_anchor_v1(
        supervision=supervision,
        ligand_batch_index=ligand["mask"],
    )
    torch.random.default_generator.manual_seed(DIFFUSION_FORWARD_SEED_V1)
    trace = run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1(
        ddpm=model.ddpm,
        ligand=ligand,
        pocket=pocket,
        supervision=supervision,
        role_mask_anchor_hidden_delta=role_delta,
        pocket_target_residue_atom_condition_indicator=indicator,
    )
    model_output = model.covapie_current11_auxiliary_model_v1(
        diffusion_trace=trace,
        supervision=supervision,
        role_mask_anchor_hidden_delta=role_delta,
    )
    weights = CovapieCurrent11LossWeightsV1()
    if weights != CovapieCurrent11LossWeightsV1(
        base_diffusion=1.0,
        covalent_pair_prediction=1.0,
        pre_post_geometry=0.0,
        covalent_pair_contrastive=0.1,
    ):
        _fail("CURRENT_PUBLISHED_LOSS_WEIGHTS_CHANGED")
    losses = compute_covapie_current11_training_losses_v1(
        model_output=model_output,
        supervision=supervision,
        diffusion_trace=trace,
        loss_weights=weights,
        pair_contrastive_temperature=1.0,
        geometry_smooth_l1_beta=1.0,
    )
    loss_items = (
        ("loss_base_diffusion", float(losses.loss_base_diffusion.detach().item())),
        (
            "loss_covalent_pair_prediction",
            float(losses.loss_covalent_pair_prediction.detach().item()),
        ),
        ("loss_pre_post_geometry", float(losses.loss_pre_post_geometry.detach().item())),
        (
            "loss_covalent_pair_contrastive",
            float(losses.loss_covalent_pair_contrastive.detach().item()),
        ),
        ("loss_total", float(losses.loss_total.detach().item())),
    )
    counts = (
        losses.base_diffusion_valid_sample_count,
        losses.covalent_pair_prediction_valid_sample_count,
        losses.pre_post_geometry_valid_sample_count,
        losses.covalent_pair_contrastive_valid_sample_count,
    )
    pair_count = len(supervision.pair_candidate_batch_index)
    shapes = (
        ("diffusion_epsilon_ligand", tuple(model_output.diffusion_epsilon_prediction_ligand.shape)),
        ("denoised_ligand_xh", tuple(model_output.denoised_ligand_xh.shape)),
        ("ligand_hidden", tuple(model_output.ligand_node_hidden.shape)),
        ("pocket_hidden", tuple(model_output.pocket_node_hidden.shape)),
        ("role_hidden_delta", tuple(model_output.role_mask_anchor_hidden_delta.shape)),
        ("pair_logits", tuple(model_output.pair_logits.shape)),
        ("pair_embeddings", tuple(model_output.pair_embeddings.shape)),
        (
            "geometry_predictions",
            tuple(model_output.pre_post_geometry_predictions_angstrom.shape),
        ),
        ("diffusion_timestep", tuple(model_output.diffusion_timestep_int.shape)),
    )
    expected_shapes = {
        "diffusion_epsilon_ligand": (115, 13),
        "denoised_ligand_xh": (115, 13),
        "ligand_hidden": (115, 32),
        "pocket_hidden": (578, 32),
        "role_hidden_delta": (115, 32),
        "pair_logits": (pair_count,),
        "pair_embeddings": (pair_count, 32),
        "geometry_predictions": (pair_count, 2),
        "diffusion_timestep": (5,),
    }
    forward_tensors = (
        model_output.diffusion_epsilon_prediction_ligand,
        model_output.denoised_ligand_xh,
        model_output.ligand_node_hidden,
        model_output.pocket_node_hidden,
        model_output.role_mask_anchor_hidden_delta,
        model_output.pair_logits,
        model_output.pair_embeddings,
        model_output.pre_post_geometry_predictions_angstrom,
    )
    loss_tensors = (
        losses.loss_base_diffusion,
        losses.loss_covalent_pair_prediction,
        losses.loss_pre_post_geometry,
        losses.loss_covalent_pair_contrastive,
        losses.loss_total,
    )
    if (
        dict(shapes) != expected_shapes
        or counts != (5, 5, 5, 5)
        or any(not math.isfinite(value) for unused, value in loss_items)
        or any(not bool(torch.isfinite(value).all().item()) for value in forward_tensors)
        or any(value.device.type != "cpu" for value in forward_tensors + loss_tensors)
        or losses.loss_total.requires_grad is not True
        or losses.loss_pre_post_geometry.requires_grad is not True
    ):
        _fail("REAL_FORWARD_LOSS_SHAPE_FINITE_OR_AUTOGRAD_INVALID")
    after = model.state_dict()
    after_fingerprint = _state_fingerprint(after)
    state_modified = before_fingerprint != after_fingerprint or any(
        not torch.equal(before[name], after[name]) for name in before
    )
    gradients_created = not _all_model_gradients_none(model)
    if state_modified or gradients_created:
        _fail("FORWARD_LOSS_MUTATED_MODEL_OR_CREATED_GRADIENTS")
    return _SingleForwardObservationV1(
        scheduled_task_ids=prepared.scheduled_task_ids,
        diffusion_timesteps=tuple(model_output.diffusion_timestep_int.tolist()),
        tensor_shapes=shapes,
        losses=loss_items,
        counts=counts,
        migration_counts=migration_counts,
        migration_missing_keys=tuple(migration["migration_missing_keys"]),
        migration_unexpected_keys=tuple(migration["migration_unexpected_keys"]),
        architecture=architecture,
        loss_total_requires_grad=True,
        geometry_loss_requires_grad=True,
        gradients_created=False,
        state_modified=False,
    )


@contextlib.contextmanager
def _deterministic_cpu_context():
    rng_state = torch.random.get_rng_state()
    previous_threads = torch.get_num_threads()
    deterministic_enabled = torch.are_deterministic_algorithms_enabled()
    deterministic_warn_only = torch.is_deterministic_algorithms_warn_only_enabled()
    try:
        torch.set_num_threads(1)
        torch.use_deterministic_algorithms(True)
        yield
    finally:
        torch.random.set_rng_state(rng_state)
        torch.use_deterministic_algorithms(
            deterministic_enabled,
            warn_only=deterministic_warn_only,
        )
        torch.set_num_threads(previous_threads)


def _loss_difference(
    first: tuple[tuple[str, float], ...],
    second: tuple[tuple[str, float], ...],
) -> float:
    if tuple(name for name, unused in first) != tuple(name for name, unused in second):
        _fail("REPEATED_LOSS_NAME_DOMAIN_CHANGED")
    return max(abs(left - right) for (unused, left), (unused2, right) in zip(first, second))


def run_covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1(
    *,
    repository_root: Path | None = None,
    state_root: Path | None = None,
    cache_root: Path | None = None,
    checkpoint_path: Path | None = None,
    requested_sample_identities: object = None,
    repeat_count: int = 2,
) -> CovapieBatch001Train5CpuForwardLossSmokeResultV1:
    """Run exactly the formally admitted train5 twice through the real CPU path."""

    started = time.perf_counter()
    try:
        if repeat_count != 2:
            _fail("REPEAT_COUNT_MUST_EQUAL_TWO")
        repo = _require_directory(
            repository_root,
            default=_DEFAULT_REPOSITORY_ROOT,
            reason="REPOSITORY_ROOT_INVALID",
        )
        state = _require_directory(
            state_root,
            default=_DEFAULT_STATE_ROOT,
            reason="STATE_ROOT_INVALID",
        )
        cache = _require_directory(
            cache_root,
            default=_DEFAULT_CACHE_ROOT,
            reason="CACHE_ROOT_INVALID",
        )
        checkpoint = repo / CHECKPOINT_RELATIVE_PATH_V1 if checkpoint_path is None else checkpoint_path
        if type(checkpoint) is not _PATH_TYPE or checkpoint != repo / CHECKPOINT_RELATIVE_PATH_V1:
            _fail("CHECKPOINT_PATH_NOT_EXACT_PUBLISHED_PATH")
        owner_hashes = _verify_bound_owners(repo)
        checkpoint_digest_before = verify_covapie_batch001_train5_checkpoint_file_v1(
            checkpoint_path=checkpoint
        )
        prepared = _prepare_train5_batch(
            repository_root=repo,
            cache_root=cache,
            requested_sample_identities=requested_sample_identities,
        )
        if not prepared.static_five_mask_audit_passed:
            _fail("STATIC_FIVE_MASK_AUDIT_FAILED")

        from covalent_ext import (  # noqa: PLC0415
            covapie_current11_checkpoint_migration_v1 as checkpoint_owner,
        )

        checkpoint_payload = checkpoint_owner.load_covapie_current11_legacy_checkpoint_v1(
            checkpoint_path=checkpoint
        )
        checkpoint_state = checkpoint_payload.get("state_dict")
        supervision_before = {
            field.name: getattr(prepared.supervision, field.name).clone()
            for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
        }
        model_input_before = {
            name: value.clone()
            for name, value in prepared.model_input_batch.items()
            if isinstance(value, torch.Tensor)
        }
        observations: list[_SingleForwardObservationV1] = []
        with _deterministic_cpu_context():
            for unused in range(repeat_count):
                observations.append(
                    _single_forward(
                        repository_root=repo,
                        state_root=state,
                        checkpoint_state_dict=checkpoint_state,
                        prepared=prepared,
                    )
                )
        first, second = observations
        if any(
            not _same_tensor(
                supervision_before[field.name],
                getattr(prepared.supervision, field.name),
            )
            for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
        ) or any(
            not _same_tensor(value, prepared.model_input_batch[name])
            for name, value in model_input_before.items()
        ):
            _fail("TRAIN5_INPUT_OR_SUPERVISION_MUTATED_BY_SMOKE")
        maximum_loss_difference = _loss_difference(first.losses, second.losses)
        first_losses = dict(first.losses)
        if (
            first.scheduled_task_ids != second.scheduled_task_ids
            or first.diffusion_timesteps != second.diffusion_timesteps
            or first.tensor_shapes != second.tensor_shapes
            or first.migration_counts != second.migration_counts
            or first.architecture != second.architecture
            or maximum_loss_difference
            > DETERMINISM_ABSOLUTE_TOLERANCE_V1
            + DETERMINISM_RELATIVE_TOLERANCE_V1
            * max(abs(value) for value in first_losses.values())
        ):
            _fail("REPEATED_FRESH_MODEL_FIXED_SEED_DETERMINISM_FAILED")
        checkpoint_digest_after = verify_covapie_batch001_train5_checkpoint_file_v1(
            checkpoint_path=checkpoint
        )
        supervision = prepared.supervision
        ligand_counts = tuple(
            len(record.ligand_retained_heavy_atoms)
            for record in prepared.structural_records
        )
        pocket_counts = tuple(
            len(record.pocket_retained_heavy_atoms)
            for record in prepared.structural_records
        )
        weights = CovapieCurrent11LossWeightsV1()
        current_weights = (
            ("base_diffusion", float(weights.base_diffusion)),
            ("covalent_pair_prediction", float(weights.covalent_pair_prediction)),
            ("pre_post_geometry", float(weights.pre_post_geometry)),
            ("covalent_pair_contrastive", float(weights.covalent_pair_contrastive)),
        )
        return CovapieBatch001Train5CpuForwardLossSmokeResultV1(
            implementation_status="passed",
            in_memory_admission_status=IN_MEMORY_ADMISSION_STATUS_V1,
            formal_train_event_ids=prepared.authority.formal_train_event_ids,
            formal_validation_event_ids=prepared.authority.formal_validation_event_ids,
            formal_unresolved_event_ids=prepared.authority.formal_unresolved_event_ids,
            scheduled_task_ids=prepared.scheduled_task_ids,
            five_epoch_task_schedule_audit=prepared.five_epoch_task_schedule_audit,
            ligand_counts=ligand_counts,
            pocket_counts=pocket_counts,
            ligand_node_count=sum(ligand_counts),
            pocket_node_count=sum(pocket_counts),
            pair_candidate_count=len(supervision.pair_candidate_batch_index),
            pair_positive_count=int(supervision.pair_candidate_is_positive.sum().item()),
            pair_negative_count=int(supervision.pair_candidate_is_negative.sum().item()),
            pair_positive_candidate_indices=tuple(
                supervision.pair_positive_candidate_index.tolist()
            ),
            diffusion_timesteps=first.diffusion_timesteps,
            tensor_shapes=first.tensor_shapes,
            runtime_losses=first.losses,
            repeated_runtime_losses=second.losses,
            maximum_repeated_loss_absolute_difference=maximum_loss_difference,
            base_diffusion_valid_sample_count=first.counts[0],
            covalent_pair_prediction_valid_sample_count=first.counts[1],
            pre_post_geometry_valid_sample_count=first.counts[2],
            covalent_pair_contrastive_valid_sample_count=first.counts[3],
            PRE_geometry_valid_sample_count=int(
                supervision.pre_post_geometry_component_loss_mask[:, 0].sum().item()
            ),
            current_loss_weights=current_weights,
            geometry_contribution_to_loss_total=(
                float(weights.pre_post_geometry)
                * dict(first.losses)["loss_pre_post_geometry"]
            ),
            loss_total_requires_grad=first.loss_total_requires_grad,
            geometry_loss_requires_grad=first.geometry_loss_requires_grad,
            geometry_head_autograd_path_in_loss_total=True,
            geometry_head_nonzero_gradient_from_loss_total_in_future_backward=False,
            parameter_gradients_created=first.gradients_created,
            model_state_modified_by_smoke=first.state_modified,
            migration_counts=first.migration_counts,
            migration_missing_keys=first.migration_missing_keys,
            migration_unexpected_keys=first.migration_unexpected_keys,
            architecture=first.architecture,
            bound_owner_sha256=owner_hashes,
            formal_artifact_sha256=(
                (FORMAL_AUTHORITY_RELATIVE_PATH_V1.name, FORMAL_AUTHORITY_SHA256_V1),
                (FORMAL_COMPONENT_REGISTRY_FILENAME_V1, FORMAL_COMPONENT_REGISTRY_SHA256_V1),
                (FORMAL_SOURCE_INVENTORY_FILENAME_V1, FORMAL_SOURCE_INVENTORY_SHA256_V1),
                (FORMAL_MANIFEST_FILENAME_V1, FORMAL_MANIFEST_SHA256_V1),
            ),
            checkpoint_sha256=checkpoint_digest_before,
            checkpoint_modified=checkpoint_digest_after != checkpoint_digest_before,
            repeat_count=repeat_count,
            elapsed_seconds=time.perf_counter() - started,
            optimizer_created=False,
            optimizer_step_performed=False,
            backward_performed=False,
            Trainer_used=False,
            training_performed=False,
            CPU_only=True,
            GPU_used=False,
            network_used=False,
            supervision_dataclass_reused=True,
            architecture_modification_required_before_backward_smoke=False,
            data_label_family_or_PRE_blocker_required_before_backward_smoke=False,
            geometry_weight_policy_decision_required_before_backward_smoke=True,
            ready_for_single_backward_optimizer_step_smoke=False,
        )
    except BaseException as error:
        _public_error(error)
