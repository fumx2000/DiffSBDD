"""Exact16 mixed-profile scheduling, collation, and one-batch smoke V1.

This bounded owner schedules the published Current11 and K36 populations,
delegates singleton construction to the published mixed-profile tensorizer,
collates one real Exact16 batch, and optionally executes one in-memory model
core forward/backward/AdamW step.  It does not implement a mixed Lightning
``forward`` or Trainer integration and never writes state or checkpoints.
"""

from __future__ import annotations

import hashlib
import stat
from dataclasses import dataclass, fields
from pathlib import Path
from typing import NoReturn, Sequence

import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from covalent_ext import (
    covapie_expanded_cys_sg_mixed_profile_tensorizer_v1 as mixed_tensorizer,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
    canonical_task_id_for_covapie_current11_sample_v1,
)


__all__ = (
    "COVAPIE_EXPANDED_CYS_SG_MIXED_PROFILE_BATCH_SCHEDULER_AND_ONE_BATCH_SMOKE_V1_ERROR",
    "K36_TASK_SCHEDULE_DOMAIN_V1",
    "K36_VALID_TASK_IDS_V1",
    "EXACT16_MEMBER_IDENTITIES_V1",
    "EXACT16_STRICT_PROFILE_COUNT_V1",
    "EXACT16_DIRECT_PROFILE_COUNT_V1",
    "CovapieExpandedCysSgScheduleInputV1",
    "CovapieExpandedCysSgMixedBatchV1",
    "canonical_task_id_for_covapie_expanded_cys_sg_sample_v1",
    "collate_covapie_expanded_cys_sg_exact16_tensorized_samples_v1",
    "validate_covapie_expanded_cys_sg_exact16_mixed_batch_v1",
    "run_covapie_expanded_cys_sg_mixed_profile_one_batch_smoke_v1",
    "run_covapie_expanded_cys_sg_mixed_profile_batch_scheduler_and_one_batch_smoke_v1",
)


COVAPIE_EXPANDED_CYS_SG_MIXED_PROFILE_BATCH_SCHEDULER_AND_ONE_BATCH_SMOKE_V1_ERROR = (
    "COVAPIE_EXPANDED_CYS_SG_MIXED_PROFILE_BATCH_SCHEDULER_AND_ONE_BATCH_"
    "SMOKE_V1_ERROR"
)
K36_TASK_SCHEDULE_DOMAIN_V1 = (
    b"COVAPIE_EXPANDED_CYS_SG_K36_DIRECT_TASK_SCHEDULE_V1\0"
)
K36_VALID_TASK_IDS_V1 = mixed_tensorizer.K36_VALID_TASK_IDS_V1
EXACT16_MEMBER_IDENTITIES_V1 = (
    mixed_tensorizer.CURRENT11_MEMBER_IDENTITIES_V1
    + mixed_tensorizer.K36_MEMBER_IDENTITIES_V1
)
EXACT16_STRICT_PROFILE_COUNT_V1 = 11
EXACT16_DIRECT_PROFILE_COUNT_V1 = 5

_PATH_TYPE = type(Path())
_EXPECTED_BASELINE_HEAD_V1 = "f690802c24b78ace19f9a47285ced7be73cfc55b"
_EXPECTED_CHECKPOINT_SHA256_V1 = (
    "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
)
_EXPECTED_CHECKPOINT_SIZE_V1 = 17_861_341
_EXPECTED_K36_REACTION_FAMILY_AUTHORITY_SHA256_V1 = (
    "5eb39ac01770dbb8721a48d7ae6bf77fc6cb07493ca00a0eb5756ebf10921461"
)
_EXPECTED_K36_WARHEAD_RULE_AUTHORITY_SHA256_V1 = (
    "1b8927693386aa8c72fed8677d59bdb3b5b56d4e89a09d88a908341fec0a19b2"
)
_EXPECTED_CURRENT11_FORMAL_CARRIER_SHA256_V1 = (
    "ea3aa7c94b7c88993493662ad6ba7fd95e547ec62612a072f8248a515657e910"
)
_EXPECTED_CURRENT11_HUMAN_DECISION_SHA256_V1 = (
    "104cc3ec5c9cf6a250f07348695c0a52ca938ed3be082a61e4a983e6f1359ae4"
)
_MODEL_TENSOR_FIELDS_BY_DOMAIN_V1 = {
    "ligand": (
        "lig_coords",
        "lig_one_hot",
        "lig_source_row_index",
        "lig_parser_local_index",
    ),
    "pocket": (
        "pocket_coords",
        "pocket_one_hot",
        "pocket_source_row_index",
        "pocket_parser_local_index",
    ),
}
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
_CANDIDATE_DIRECT_FIELDS_V1 = (
    "pair_candidate_ligand_local_index",
    "pair_candidate_residue_local_index",
    "pair_candidate_is_positive",
    "pair_candidate_is_negative",
    "pair_head_candidate_loss_mask",
)
_K36_REACTION_FAMILY_AUTHORITY_RELATIVE_PATH_V1 = Path(
    "manual-review/recovered7-targeted-chemistry-review-v1/"
    "COVAPIE_RECOVERED7_CHEM_REVIEW_CLASS_"
    "83E9C7B9D43444D7E50FBFD7E6C3DAFEF5E0DC92CF1A7C571E3F4E3FE4E08D92/"
    "reaction_family_authority_v1.json"
)
_K36_WARHEAD_RULE_AUTHORITY_RELATIVE_PATH_V1 = (
    _K36_REACTION_FAMILY_AUTHORITY_RELATIVE_PATH_V1.parent
    / "warhead_rule_authority_v1.json"
)
_CURRENT11_FORMAL_CARRIER_RELATIVE_PATH_V1 = Path(
    "formal-sidecars/current11-runtime-sample-and-role-order-carrier-v1/"
    "current11_runtime_sample_and_role_order_carrier.npz"
)
_CURRENT11_HUMAN_DECISION_RELATIVE_PATH_V1 = Path(
    "manual-review-aids/current11-trainable-supervision-role-seed-v1/"
    "current11_role_seed_review_decisions.csv"
)


class _MixedBatchInvariantError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _fail(reason: str) -> NoReturn:
    raise _MixedBatchInvariantError(reason)


def _public_error(error: Exception) -> NoReturn:
    if isinstance(error, _MixedBatchInvariantError):
        raise ValueError(
            f"{COVAPIE_EXPANDED_CYS_SG_MIXED_PROFILE_BATCH_SCHEDULER_AND_ONE_BATCH_SMOKE_V1_ERROR}:"
            f"{error.reason}"
        ) from error
    if (
        type(error) is ValueError
        and str(error).startswith(
            COVAPIE_EXPANDED_CYS_SG_MIXED_PROFILE_BATCH_SCHEDULER_AND_ONE_BATCH_SMOKE_V1_ERROR
        )
    ):
        raise error
    raise ValueError(
        COVAPIE_EXPANDED_CYS_SG_MIXED_PROFILE_BATCH_SCHEDULER_AND_ONE_BATCH_SMOKE_V1_ERROR
    ) from error


def _require_epoch_seed(
    *, epoch: object, task_schedule_seed: object
) -> tuple[int, int]:
    if (
        type(epoch) is not int
        or epoch < 0
        or type(task_schedule_seed) is not int
        or not 0 <= task_schedule_seed <= 2**63 - 1
    ):
        _fail("SCHEDULE_INPUT_INVALID")
    return epoch, task_schedule_seed


def canonical_task_id_for_covapie_expanded_cys_sg_sample_v1(
    *, sample_identity: object, epoch: object, task_schedule_seed: object
) -> int:
    """Return the order/rank-independent task for one exact integration member."""

    try:
        epoch_value, seed_value = _require_epoch_seed(
            epoch=epoch, task_schedule_seed=task_schedule_seed
        )
        if type(sample_identity) is not str:
            _fail("SAMPLE_IDENTITY_NOT_IN_EXACT16")
        if sample_identity in mixed_tensorizer.CURRENT11_MEMBER_IDENTITIES_V1:
            return canonical_task_id_for_covapie_current11_sample_v1(
                sample_key=sample_identity,
                epoch=epoch_value,
                task_schedule_seed=seed_value,
            )
        if sample_identity not in mixed_tensorizer.K36_MEMBER_IDENTITIES_V1:
            _fail("SAMPLE_IDENTITY_NOT_IN_EXACT16")
        try:
            encoded_identity = sample_identity.encode("ascii")
        except UnicodeEncodeError as error:
            raise _MixedBatchInvariantError(
                "SAMPLE_IDENTITY_NOT_IN_EXACT16"
            ) from error
        payload = (
            K36_TASK_SCHEDULE_DOMAIN_V1
            + str(seed_value).encode("ascii")
            + b"\0"
            + encoded_identity
        )
        base = int.from_bytes(
            hashlib.sha256(payload).digest()[:8], "big", signed=False
        ) % len(K36_VALID_TASK_IDS_V1)
        return K36_VALID_TASK_IDS_V1[
            (base + epoch_value) % len(K36_VALID_TASK_IDS_V1)
        ]
    except Exception as error:
        _public_error(error)


@dataclass(frozen=True)
class CovapieExpandedCysSgScheduleInputV1:
    sample_identity: str
    epoch: int
    task_schedule_seed: int

    def __post_init__(self) -> None:
        canonical_task_id_for_covapie_expanded_cys_sg_sample_v1(
            sample_identity=self.sample_identity,
            epoch=self.epoch,
            task_schedule_seed=self.task_schedule_seed,
        )


@dataclass(frozen=True)
class CovapieExpandedCysSgMixedBatchV1:
    model_input_batch: dict[str, object]
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1
    sample_identities: tuple[str, ...]
    role_profiles: tuple[str, ...]
    scheduled_task_ids: tuple[int, ...]
    epoch: int
    task_schedule_seed: int
    current11_batch_indices: tuple[int, ...]
    k36_batch_indices: tuple[int, ...]

    def __post_init__(self) -> None:
        if (
            type(self.model_input_batch) is not dict
            or not isinstance(
                self.supervision,
                CovapieCurrent11TrainingSupervisionTensorsV1,
            )
            or type(self.sample_identities) is not tuple
            or type(self.role_profiles) is not tuple
            or type(self.scheduled_task_ids) is not tuple
        ):
            raise ValueError(
                COVAPIE_EXPANDED_CYS_SG_MIXED_PROFILE_BATCH_SCHEDULER_AND_ONE_BATCH_SMOKE_V1_ERROR
            )


def _tensor(
    value: object,
    *,
    name: str,
    dtype: torch.dtype | None = None,
    ndim: int | None = None,
) -> torch.Tensor:
    if (
        not isinstance(value, torch.Tensor)
        or (dtype is not None and value.dtype != dtype)
        or (ndim is not None and value.ndim != ndim)
    ):
        _fail(f"{name.upper()}_INVALID")
    return value


def _tensor_exact(left: torch.Tensor, right: torch.Tensor) -> bool:
    if (
        left.dtype != right.dtype
        or left.shape != right.shape
        or left.device != right.device
    ):
        return False
    if left.dtype.is_floating_point or left.dtype.is_complex:
        equal = left == right
        nan_equal = torch.isnan(left) & torch.isnan(right)
        return bool((equal | nan_equal).all().item())
    return bool(torch.equal(left, right))


def _expected_profile(identity: str) -> tuple[str, tuple[int, ...]]:
    if identity in mixed_tensorizer.CURRENT11_MEMBER_IDENTITIES_V1:
        return mixed_tensorizer.STRICT_LINKER_PRESENT_V1, (0, 1, 2, 3, 4)
    if identity in mixed_tensorizer.K36_MEMBER_IDENTITIES_V1:
        return mixed_tensorizer.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1, (0, 3, 4)
    _fail("SAMPLE_IDENTITY_NOT_IN_EXACT16")


def _validate_singleton_v1(
    sample: object,
    *,
    expected_identity: str,
    epoch: int,
    task_schedule_seed: int,
) -> tuple[int, int, int]:
    if type(sample) is not mixed_tensorizer.CovapieExpandedCysSgTensorizedSampleV1:
        _fail("TENSORIZED_SAMPLE_TYPE_INVALID")
    if sample.sample_identity != expected_identity:
        _fail("EXACT16_SAMPLE_ORDER_INVALID")
    expected_profile, expected_valid_tasks = _expected_profile(expected_identity)
    if (
        sample.role_profile != expected_profile
        or sample.valid_task_ids != expected_valid_tasks
    ):
        _fail("SAMPLE_PROFILE_METADATA_INVALID")
    expected_task = canonical_task_id_for_covapie_expanded_cys_sg_sample_v1(
        sample_identity=expected_identity,
        epoch=epoch,
        task_schedule_seed=task_schedule_seed,
    )
    batch = sample.model_input_batch
    supervision = sample.supervision
    if type(batch) is not dict or type(supervision) is not CovapieCurrent11TrainingSupervisionTensorsV1:
        _fail("SINGLETON_PAYLOAD_TYPE_INVALID")
    names = batch.get("names")
    receptors = batch.get("receptors")
    if (
        type(names) not in (list, tuple)
        or len(names) != 1
        or str(names[0]) != expected_identity
        or type(receptors) not in (list, tuple)
        or len(receptors) != 1
        or not isinstance(receptors[0], str)
    ):
        _fail("SINGLETON_IDENTITY_METADATA_INVALID")
    lig_count_tensor = _tensor(
        batch.get("num_lig_atoms"),
        name="num_lig_atoms",
        dtype=torch.long,
        ndim=1,
    )
    pocket_count_tensor = _tensor(
        batch.get("num_pocket_nodes"),
        name="num_pocket_nodes",
        dtype=torch.long,
        ndim=1,
    )
    if lig_count_tensor.shape != (1,) or pocket_count_tensor.shape != (1,):
        _fail("SINGLETON_NODE_COUNT_SHAPE_INVALID")
    ligand_count = int(lig_count_tensor[0].item())
    pocket_count = int(pocket_count_tensor[0].item())
    if ligand_count <= 0 or pocket_count <= 0:
        _fail("SINGLETON_NODE_COUNT_INVALID")
    ligand_coords = _tensor(
        batch.get("lig_coords"), name="lig_coords", ndim=2
    )
    pocket_coords = _tensor(
        batch.get("pocket_coords"), name="pocket_coords", ndim=2
    )
    ligand_one_hot = _tensor(
        batch.get("lig_one_hot"), name="lig_one_hot", ndim=2
    )
    pocket_one_hot = _tensor(
        batch.get("pocket_one_hot"), name="pocket_one_hot", ndim=2
    )
    if (
        ligand_coords.shape != (ligand_count, 3)
        or pocket_coords.shape != (pocket_count, 3)
        or ligand_one_hot.shape != (ligand_count, 10)
        or pocket_one_hot.shape != (pocket_count, 10)
    ):
        _fail("SINGLETON_MODEL_NODE_SHAPE_INVALID")
    for name in ("lig_source_row_index", "lig_parser_local_index"):
        if _tensor(batch.get(name), name=name, dtype=torch.long, ndim=1).shape != (
            ligand_count,
        ):
            _fail("SINGLETON_LIGAND_INDEX_SHAPE_INVALID")
    for name in ("pocket_source_row_index", "pocket_parser_local_index"):
        if _tensor(batch.get(name), name=name, dtype=torch.long, ndim=1).shape != (
            pocket_count,
        ):
            _fail("SINGLETON_POCKET_INDEX_SHAPE_INVALID")
    ligand_mask = _tensor(
        batch.get("lig_mask"), name="lig_mask", ndim=1
    )
    pocket_mask = _tensor(
        batch.get("pocket_mask"), name="pocket_mask", ndim=1
    )
    if (
        ligand_mask.shape != (ligand_count,)
        or pocket_mask.shape != (pocket_count,)
        or bool(ligand_mask.any().item())
        or bool(pocket_mask.any().item())
    ):
        _fail("SINGLETON_BATCH_MEMBERSHIP_INVALID")

    sample_shapes = {
        "sample_training_admitted": ((1,), torch.bool),
        "canonical_task_id": ((1,), torch.long),
        "canonical_task_valid": ((1,), torch.bool),
        "ligand_minimal_seed_or_anchor_valid": ((1,), torch.bool),
        "target_residue_reactive_atom_local_index": ((1,), torch.long),
        "target_residue_reactive_atom_flat_index": ((1,), torch.long),
        "target_residue_condition_valid": ((1,), torch.bool),
        "pair_positive_candidate_index": ((1,), torch.long),
        "pair_positive_candidate_valid": ((1,), torch.bool),
        "pair_negative_count": ((1,), torch.long),
        "pair_contrastive_sample_loss_mask": ((1,), torch.bool),
        "observed_complex_pair_distance_angstrom": ((1, 1), None),
        "observed_complex_pair_distance_valid": ((1, 1), torch.bool),
        "pre_post_geometry_target_angstrom": ((1, 2), None),
        "pre_post_geometry_component_valid_mask": ((1, 2), torch.bool),
        "pre_post_geometry_component_loss_mask": ((1, 2), torch.bool),
    }
    for name, (shape, dtype) in sample_shapes.items():
        value = _tensor(getattr(supervision, name), name=name, dtype=dtype)
        if value.shape != shape:
            _fail("SINGLETON_SAMPLE_SUPERVISION_SHAPE_INVALID")
    if (
        supervision.canonical_task_id.tolist() != [expected_task]
        or expected_task not in expected_valid_tasks
        or supervision.sample_training_admitted.tolist() != [True]
        or supervision.canonical_task_valid.tolist() != [True]
        or supervision.target_residue_condition_valid.tolist() != [True]
        or supervision.pair_positive_candidate_valid.tolist() != [True]
        or supervision.pair_contrastive_sample_loss_mask.tolist() != [True]
    ):
        _fail("SINGLETON_SAMPLE_SEMANTICS_INVALID")

    ligand_shapes = {
        "ligand_role_id": ((ligand_count,), torch.long),
        "ligand_role_valid": ((ligand_count,), torch.bool),
        "ligand_base_generation_mask": ((ligand_count, 1), torch.bool),
        "ligand_base_fixed_mask": ((ligand_count, 1), torch.bool),
        "ligand_base_target_mask": ((ligand_count, 1), torch.bool),
        "ligand_base_context_mask": ((ligand_count, 1), torch.bool),
        "ligand_active_diffusion_loss_mask": ((ligand_count, 1), torch.bool),
        "ligand_minimal_seed_or_anchor_mask": ((ligand_count, 1), torch.bool),
        "ligand_anchor_distance_angstrom": ((ligand_count, 1), None),
        "ligand_anchor_distance_valid": ((ligand_count, 1), torch.bool),
    }
    for name, (shape, dtype) in ligand_shapes.items():
        value = _tensor(getattr(supervision, name), name=name, dtype=dtype)
        if value.shape != shape:
            _fail("SINGLETON_LIGAND_SUPERVISION_SHAPE_INVALID")
    for name in _POCKET_SUPERVISION_FIELDS_V1:
        value = _tensor(
            getattr(supervision, name), name=name, dtype=torch.bool, ndim=2
        )
        if value.shape != (pocket_count, 1):
            _fail("SINGLETON_POCKET_SUPERVISION_SHAPE_INVALID")
    generation = supervision.ligand_base_generation_mask
    fixed = supervision.ligand_base_fixed_mask
    if (
        not bool((generation ^ fixed).all().item())
        or not _tensor_exact(generation, supervision.ligand_base_target_mask)
        or not _tensor_exact(fixed, supervision.ligand_base_context_mask)
        or not _tensor_exact(
            generation, supervision.ligand_active_diffusion_loss_mask
        )
        or not bool(generation.any().item())
    ):
        _fail("SINGLETON_MASK_SEMANTICS_INVALID")
    generated_roles = {
        task_id: set(task_roles)
        for task_id, _name, _alias, task_roles in mixed_tensorizer.GLOBAL_TASK_VOCABULARY_V1
    }[expected_task]
    expected_generation = torch.tensor(
        [int(role) in generated_roles for role in supervision.ligand_role_id],
        dtype=torch.bool,
        device=generation.device,
    ).unsqueeze(1)
    if not _tensor_exact(generation, expected_generation):
        _fail("SINGLETON_TASK_ROLE_MASK_INVALID")

    target_local = int(
        supervision.target_residue_reactive_atom_local_index[0].item()
    )
    target_flat = int(
        supervision.target_residue_reactive_atom_flat_index[0].item()
    )
    if (
        not 0 <= target_local < pocket_count
        or target_flat != target_local
        or int(supervision.target_residue_reactive_atom_mask.sum().item()) != 1
        or not bool(
            supervision.target_residue_reactive_atom_mask[target_local, 0]
        )
        or not bool(supervision.target_residue_membership_mask[target_local, 0])
    ):
        _fail("SINGLETON_TARGET_INDEX_INVALID")

    offsets = _tensor(
        supervision.pair_candidate_offsets,
        name="pair_candidate_offsets",
        dtype=torch.long,
        ndim=1,
    )
    if offsets.shape != (2,) or int(offsets[0].item()) != 0:
        _fail("SINGLETON_CANDIDATE_OFFSETS_INVALID")
    candidate_count = int(offsets[1].item())
    if candidate_count < 2:
        _fail("SINGLETON_CANDIDATE_COUNT_INVALID")
    candidate_shapes = {
        "pair_candidate_batch_index": torch.long,
        "pair_candidate_ligand_local_index": torch.long,
        "pair_candidate_residue_local_index": torch.long,
        "pair_candidate_ligand_flat_index": torch.long,
        "pair_candidate_pocket_flat_index": torch.long,
        "pair_candidate_is_positive": torch.bool,
        "pair_candidate_is_negative": torch.bool,
        "pair_head_candidate_loss_mask": torch.bool,
    }
    for name, dtype in candidate_shapes.items():
        value = _tensor(
            getattr(supervision, name), name=name, dtype=dtype, ndim=1
        )
        if value.shape != (candidate_count,):
            _fail("SINGLETON_CANDIDATE_SHAPE_INVALID")
    ligand_local = supervision.pair_candidate_ligand_local_index
    pocket_local = supervision.pair_candidate_residue_local_index
    positive = supervision.pair_candidate_is_positive
    positive_index = int(supervision.pair_positive_candidate_index[0].item())
    if (
        bool(supervision.pair_candidate_batch_index.any().item())
        or bool(((ligand_local < 0) | (ligand_local >= ligand_count)).any().item())
        or bool(((pocket_local < 0) | (pocket_local >= pocket_count)).any().item())
        or not _tensor_exact(
            ligand_local, supervision.pair_candidate_ligand_flat_index
        )
        or not _tensor_exact(
            pocket_local, supervision.pair_candidate_pocket_flat_index
        )
        or int(positive.sum().item()) != 1
        or not _tensor_exact(~positive, supervision.pair_candidate_is_negative)
        or not bool(supervision.pair_head_candidate_loss_mask.all().item())
        or not 0 <= positive_index < candidate_count
        or not bool(positive[positive_index])
        or int(supervision.pair_negative_count[0].item()) != candidate_count - 1
        or int(pocket_local[positive_index].item()) != target_local
    ):
        _fail("SINGLETON_PAIR_SEMANTICS_INVALID")
    if expected_identity in mixed_tensorizer.K36_MEMBER_IDENTITIES_V1 and int(
        ligand_local[positive_index].item()
    ) != 20:
        _fail("K36_POSITIVE_LIGAND_NOT_C21")
    if (
        bool(supervision.pre_post_geometry_component_valid_mask.any().item())
        or bool(supervision.pre_post_geometry_component_loss_mask.any().item())
        or not bool(
            torch.isnan(supervision.pre_post_geometry_target_angstrom).all().item()
        )
    ):
        _fail("PRE_GEOMETRY_AUTHORITY_UNEXPECTED")
    return ligand_count, pocket_count, candidate_count


def _cat_supervision_fields(
    samples: Sequence[mixed_tensorizer.CovapieExpandedCysSgTensorizedSampleV1],
    names: Sequence[str],
) -> dict[str, torch.Tensor]:
    return {
        name: torch.cat(
            [getattr(sample.supervision, name) for sample in samples], dim=0
        )
        for name in names
    }


def _validate_preservation_v1(
    *,
    samples: Sequence[mixed_tensorizer.CovapieExpandedCysSgTensorizedSampleV1],
    mixed_batch: CovapieExpandedCysSgMixedBatchV1,
) -> None:
    supervision = mixed_batch.supervision
    ligand_offset = 0
    pocket_offset = 0
    candidate_offset = 0
    for batch_index, sample in enumerate(samples):
        singleton = sample.supervision
        ligand_count = int(sample.model_input_batch["num_lig_atoms"][0].item())
        pocket_count = int(
            sample.model_input_batch["num_pocket_nodes"][0].item()
        )
        candidate_count = int(singleton.pair_candidate_offsets[-1].item())
        for name in _SAMPLE_SUPERVISION_FIELDS_V1:
            if not _tensor_exact(
                getattr(supervision, name)[batch_index : batch_index + 1],
                getattr(singleton, name),
            ):
                _fail("SAMPLE_SUPERVISION_NOT_PRESERVED")
        for name in _LIGAND_SUPERVISION_FIELDS_V1:
            if not _tensor_exact(
                getattr(supervision, name)[
                    ligand_offset : ligand_offset + ligand_count
                ],
                getattr(singleton, name),
            ):
                _fail("LIGAND_SUPERVISION_NOT_PRESERVED")
        for name in _POCKET_SUPERVISION_FIELDS_V1:
            if not _tensor_exact(
                getattr(supervision, name)[
                    pocket_offset : pocket_offset + pocket_count
                ],
                getattr(singleton, name),
            ):
                _fail("POCKET_SUPERVISION_NOT_PRESERVED")
        candidate_slice = slice(
            candidate_offset, candidate_offset + candidate_count
        )
        for name in _CANDIDATE_DIRECT_FIELDS_V1:
            if not _tensor_exact(
                getattr(supervision, name)[candidate_slice],
                getattr(singleton, name),
            ):
                _fail("PAIR_SUPERVISION_NOT_PRESERVED")
        expected_target_flat = (
            singleton.target_residue_reactive_atom_flat_index + pocket_offset
        )
        expected_ligand_flat = (
            singleton.pair_candidate_ligand_flat_index + ligand_offset
        )
        expected_pocket_flat = (
            singleton.pair_candidate_pocket_flat_index + pocket_offset
        )
        expected_positive = (
            singleton.pair_positive_candidate_index + candidate_offset
        )
        if (
            not _tensor_exact(
                supervision.target_residue_reactive_atom_flat_index[
                    batch_index : batch_index + 1
                ],
                expected_target_flat,
            )
            or not _tensor_exact(
                supervision.pair_candidate_ligand_flat_index[candidate_slice],
                expected_ligand_flat,
            )
            or not _tensor_exact(
                supervision.pair_candidate_pocket_flat_index[candidate_slice],
                expected_pocket_flat,
            )
            or not _tensor_exact(
                supervision.pair_positive_candidate_index[
                    batch_index : batch_index + 1
                ],
                expected_positive,
            )
            or supervision.pair_candidate_batch_index[candidate_slice].tolist()
            != [batch_index] * candidate_count
        ):
            _fail("FLAT_INDEX_REMAP_NOT_PRESERVED")
        ligand_offset += ligand_count
        pocket_offset += pocket_count
        candidate_offset += candidate_count


def collate_covapie_expanded_cys_sg_exact16_tensorized_samples_v1(
    samples: object,
    *,
    epoch: object,
    task_schedule_seed: object,
) -> CovapieExpandedCysSgMixedBatchV1:
    """Collate the canonical Exact16 singleton objects into one real batch."""

    try:
        epoch_value, seed_value = _require_epoch_seed(
            epoch=epoch, task_schedule_seed=task_schedule_seed
        )
        if type(samples) not in (list, tuple):
            _fail("TENSORIZED_SAMPLE_SEQUENCE_INVALID")
        normalized = tuple(samples)
        if len(normalized) != len(EXACT16_MEMBER_IDENTITIES_V1):
            _fail("EXACT16_MEMBER_COUNT_INVALID")
        if len({id(sample) for sample in normalized}) != len(normalized):
            _fail("DUPLICATE_TENSORIZED_SAMPLE_OBJECT")
        counts = [
            _validate_singleton_v1(
                sample,
                expected_identity=identity,
                epoch=epoch_value,
                task_schedule_seed=seed_value,
            )
            for sample, identity in zip(normalized, EXACT16_MEMBER_IDENTITIES_V1)
        ]
        ligand_counts = tuple(item[0] for item in counts)
        pocket_counts = tuple(item[1] for item in counts)
        candidate_counts = tuple(item[2] for item in counts)
        model_batch: dict[str, object] = {
            "names": list(EXACT16_MEMBER_IDENTITIES_V1),
            "receptors": [
                sample.model_input_batch["receptors"][0] for sample in normalized
            ],
        }
        for names in _MODEL_TENSOR_FIELDS_BY_DOMAIN_V1.values():
            for name in names:
                model_batch[name] = torch.cat(
                    [sample.model_input_batch[name] for sample in normalized],
                    dim=0,
                )
        count_device = normalized[0].model_input_batch["num_lig_atoms"].device
        model_batch["num_lig_atoms"] = torch.tensor(
            ligand_counts, dtype=torch.long, device=count_device
        )
        model_batch["num_pocket_nodes"] = torch.tensor(
            pocket_counts, dtype=torch.long, device=count_device
        )
        model_batch["lig_mask"] = torch.repeat_interleave(
            torch.arange(len(normalized), dtype=torch.long, device=count_device),
            model_batch["num_lig_atoms"],
        )
        model_batch["pocket_mask"] = torch.repeat_interleave(
            torch.arange(len(normalized), dtype=torch.long, device=count_device),
            model_batch["num_pocket_nodes"],
        )

        supervision_values = _cat_supervision_fields(
            normalized,
            _SAMPLE_SUPERVISION_FIELDS_V1
            + _LIGAND_SUPERVISION_FIELDS_V1
            + _POCKET_SUPERVISION_FIELDS_V1
            + _CANDIDATE_DIRECT_FIELDS_V1,
        )
        ligand_offsets = [0]
        pocket_offsets = [0]
        candidate_offsets = [0]
        for ligand_count, pocket_count, candidate_count in counts:
            ligand_offsets.append(ligand_offsets[-1] + ligand_count)
            pocket_offsets.append(pocket_offsets[-1] + pocket_count)
            candidate_offsets.append(candidate_offsets[-1] + candidate_count)
        supervision_values.update({
            "target_residue_reactive_atom_flat_index": torch.cat([
                sample.supervision.target_residue_reactive_atom_flat_index
                + pocket_offsets[index]
                for index, sample in enumerate(normalized)
            ]),
            "pair_candidate_offsets": torch.tensor(
                candidate_offsets,
                dtype=torch.long,
                device=normalized[0].supervision.pair_candidate_offsets.device,
            ),
            "pair_candidate_batch_index": torch.cat([
                torch.full_like(
                    sample.supervision.pair_candidate_batch_index, index
                )
                for index, sample in enumerate(normalized)
            ]),
            "pair_candidate_ligand_flat_index": torch.cat([
                sample.supervision.pair_candidate_ligand_flat_index
                + ligand_offsets[index]
                for index, sample in enumerate(normalized)
            ]),
            "pair_candidate_pocket_flat_index": torch.cat([
                sample.supervision.pair_candidate_pocket_flat_index
                + pocket_offsets[index]
                for index, sample in enumerate(normalized)
            ]),
            "pair_positive_candidate_index": torch.cat([
                sample.supervision.pair_positive_candidate_index
                + candidate_offsets[index]
                for index, sample in enumerate(normalized)
            ]),
        })
        expected_fields = {field.name for field in fields(
            CovapieCurrent11TrainingSupervisionTensorsV1
        )}
        if set(supervision_values) != expected_fields:
            _fail("COLLATED_SUPERVISION_FIELD_SET_INVALID")
        supervision = CovapieCurrent11TrainingSupervisionTensorsV1(
            **supervision_values
        )
        tasks = tuple(
            int(sample.supervision.canonical_task_id[0].item())
            for sample in normalized
        )
        result = CovapieExpandedCysSgMixedBatchV1(
            model_input_batch=model_batch,
            supervision=supervision,
            sample_identities=EXACT16_MEMBER_IDENTITIES_V1,
            role_profiles=tuple(sample.role_profile for sample in normalized),
            scheduled_task_ids=tasks,
            epoch=epoch_value,
            task_schedule_seed=seed_value,
            current11_batch_indices=tuple(range(11)),
            k36_batch_indices=tuple(range(11, 16)),
        )
        validate_covapie_expanded_cys_sg_exact16_mixed_batch_v1(result)
        _validate_preservation_v1(samples=normalized, mixed_batch=result)
        return result
    except Exception as error:
        _public_error(error)


def validate_covapie_expanded_cys_sg_exact16_mixed_batch_v1(
    mixed_batch: object,
) -> None:
    """Fail closed on metadata, membership, offset, or cross-sample drift."""

    try:
        if type(mixed_batch) is not CovapieExpandedCysSgMixedBatchV1:
            _fail("MIXED_BATCH_TYPE_INVALID")
        epoch, seed = _require_epoch_seed(
            epoch=mixed_batch.epoch,
            task_schedule_seed=mixed_batch.task_schedule_seed,
        )
        expected_profiles = tuple(
            _expected_profile(identity)[0]
            for identity in EXACT16_MEMBER_IDENTITIES_V1
        )
        expected_tasks = tuple(
            canonical_task_id_for_covapie_expanded_cys_sg_sample_v1(
                sample_identity=identity,
                epoch=epoch,
                task_schedule_seed=seed,
            )
            for identity in EXACT16_MEMBER_IDENTITIES_V1
        )
        if (
            mixed_batch.sample_identities != EXACT16_MEMBER_IDENTITIES_V1
            or mixed_batch.role_profiles != expected_profiles
            or mixed_batch.scheduled_task_ids != expected_tasks
            or mixed_batch.role_profiles.count(
                mixed_tensorizer.STRICT_LINKER_PRESENT_V1
            )
            != EXACT16_STRICT_PROFILE_COUNT_V1
            or mixed_batch.role_profiles.count(
                mixed_tensorizer.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1
            )
            != EXACT16_DIRECT_PROFILE_COUNT_V1
            or mixed_batch.current11_batch_indices != tuple(range(11))
            or mixed_batch.k36_batch_indices != tuple(range(11, 16))
        ):
            _fail("MIXED_BATCH_SCHEDULE_METADATA_INVALID")
        batch = mixed_batch.model_input_batch
        supervision = mixed_batch.supervision
        if type(batch) is not dict or type(supervision) is not CovapieCurrent11TrainingSupervisionTensorsV1:
            _fail("MIXED_BATCH_PAYLOAD_TYPE_INVALID")
        if (
            batch.get("names") != list(EXACT16_MEMBER_IDENTITIES_V1)
            or type(batch.get("receptors")) is not list
            or len(batch["receptors"]) != 16
        ):
            _fail("MIXED_BATCH_IDENTITY_ORDER_INVALID")
        ligand_counts = _tensor(
            batch.get("num_lig_atoms"),
            name="num_lig_atoms",
            dtype=torch.long,
            ndim=1,
        )
        pocket_counts = _tensor(
            batch.get("num_pocket_nodes"),
            name="num_pocket_nodes",
            dtype=torch.long,
            ndim=1,
        )
        if (
            ligand_counts.shape != (16,)
            or pocket_counts.shape != (16,)
            or bool((ligand_counts <= 0).any().item())
            or bool((pocket_counts <= 0).any().item())
        ):
            _fail("MIXED_BATCH_NODE_COUNTS_INVALID")
        ligand_total = int(ligand_counts.sum().item())
        pocket_total = int(pocket_counts.sum().item())
        ligand_mask = _tensor(
            batch.get("lig_mask"), name="lig_mask", dtype=torch.long, ndim=1
        )
        pocket_mask = _tensor(
            batch.get("pocket_mask"),
            name="pocket_mask",
            dtype=torch.long,
            ndim=1,
        )
        expected_ligand_mask = torch.repeat_interleave(
            torch.arange(16, device=ligand_counts.device), ligand_counts
        ).long()
        expected_pocket_mask = torch.repeat_interleave(
            torch.arange(16, device=pocket_counts.device), pocket_counts
        ).long()
        if (
            not _tensor_exact(ligand_mask, expected_ligand_mask)
            or not _tensor_exact(pocket_mask, expected_pocket_mask)
        ):
            _fail("MIXED_BATCH_MEMBERSHIP_INVALID")
        for name in _MODEL_TENSOR_FIELDS_BY_DOMAIN_V1["ligand"]:
            value = _tensor(batch.get(name), name=name)
            if value.ndim == 0 or len(value) != ligand_total:
                _fail("MIXED_BATCH_LIGAND_MODEL_SHAPE_INVALID")
        for name in _MODEL_TENSOR_FIELDS_BY_DOMAIN_V1["pocket"]:
            value = _tensor(batch.get(name), name=name)
            if value.ndim == 0 or len(value) != pocket_total:
                _fail("MIXED_BATCH_POCKET_MODEL_SHAPE_INVALID")
        if (
            supervision.sample_training_admitted.shape != (16,)
            or supervision.canonical_task_id.shape != (16,)
            or supervision.canonical_task_id.tolist() != list(expected_tasks)
            or not bool(supervision.sample_training_admitted.all().item())
            or not bool(supervision.canonical_task_valid.all().item())
            or not bool(supervision.target_residue_condition_valid.all().item())
        ):
            _fail("MIXED_BATCH_SAMPLE_SUPERVISION_INVALID")
        for name in _LIGAND_SUPERVISION_FIELDS_V1:
            value = _tensor(getattr(supervision, name), name=name)
            if value.ndim == 0 or len(value) != ligand_total:
                _fail("MIXED_BATCH_LIGAND_SUPERVISION_INVALID")
        for name in _POCKET_SUPERVISION_FIELDS_V1:
            value = _tensor(getattr(supervision, name), name=name)
            if value.shape != (pocket_total, 1):
                _fail("MIXED_BATCH_POCKET_SUPERVISION_INVALID")
        offsets = supervision.pair_candidate_offsets
        if (
            offsets.dtype != torch.long
            or offsets.shape != (17,)
            or int(offsets[0].item()) != 0
            or bool((offsets[1:] <= offsets[:-1]).any().item())
        ):
            _fail("MIXED_BATCH_CANDIDATE_OFFSETS_INVALID")
        candidate_total = int(offsets[-1].item())
        for name in (
            "pair_candidate_batch_index",
            "pair_candidate_ligand_local_index",
            "pair_candidate_residue_local_index",
            "pair_candidate_ligand_flat_index",
            "pair_candidate_pocket_flat_index",
            "pair_candidate_is_positive",
            "pair_candidate_is_negative",
            "pair_head_candidate_loss_mask",
        ):
            value = _tensor(getattr(supervision, name), name=name, ndim=1)
            if len(value) != candidate_total:
                _fail("MIXED_BATCH_CANDIDATE_SHAPE_INVALID")
        ligand_flat = supervision.pair_candidate_ligand_flat_index
        pocket_flat = supervision.pair_candidate_pocket_flat_index
        candidate_batch = supervision.pair_candidate_batch_index
        if (
            bool(((ligand_flat < 0) | (ligand_flat >= ligand_total)).any().item())
            or bool(((pocket_flat < 0) | (pocket_flat >= pocket_total)).any().item())
            or not _tensor_exact(candidate_batch, ligand_mask[ligand_flat])
            or not _tensor_exact(candidate_batch, pocket_mask[pocket_flat])
        ):
            _fail("CROSS_SAMPLE_PAIR_CANDIDATE")
        ligand_offsets = torch.cat((
            ligand_counts.new_zeros(1), torch.cumsum(ligand_counts, dim=0)
        ))
        pocket_offsets = torch.cat((
            pocket_counts.new_zeros(1), torch.cumsum(pocket_counts, dim=0)
        ))
        target_local = supervision.target_residue_reactive_atom_local_index
        target_flat = supervision.target_residue_reactive_atom_flat_index
        if target_local.shape != (16,) or target_flat.shape != (16,):
            _fail("MIXED_BATCH_TARGET_INDEX_SHAPE_INVALID")
        for sample_index in range(16):
            start = int(offsets[sample_index].item())
            end = int(offsets[sample_index + 1].item())
            candidate_slice = slice(start, end)
            positive_index = int(
                supervision.pair_positive_candidate_index[sample_index].item()
            )
            local_target = int(target_local[sample_index].item())
            flat_target = int(target_flat[sample_index].item())
            ligand_start = int(ligand_offsets[sample_index].item())
            ligand_end = int(ligand_offsets[sample_index + 1].item())
            pocket_start = int(pocket_offsets[sample_index].item())
            pocket_end = int(pocket_offsets[sample_index + 1].item())
            if (
                candidate_batch[candidate_slice].tolist()
                != [sample_index] * (end - start)
                or not 0 <= local_target < pocket_end - pocket_start
                or flat_target != pocket_start + local_target
                or pocket_mask[flat_target].item() != sample_index
                or not bool(
                    supervision.target_residue_reactive_atom_mask[
                        flat_target, 0
                    ]
                )
                or not start <= positive_index < end
                or int(
                    supervision.pair_candidate_is_positive[candidate_slice]
                    .sum()
                    .item()
                )
                != 1
                or not bool(
                    supervision.pair_candidate_is_positive[positive_index]
                )
                or int(supervision.pair_negative_count[sample_index].item())
                != end - start - 1
            ):
                _fail("MIXED_BATCH_PER_SAMPLE_PAIR_INVALID")
            expected_ligand_local = (
                ligand_flat[candidate_slice] - ligand_start
            )
            expected_pocket_local = (
                pocket_flat[candidate_slice] - pocket_start
            )
            if (
                not _tensor_exact(
                    expected_ligand_local,
                    supervision.pair_candidate_ligand_local_index[
                        candidate_slice
                    ],
                )
                or not _tensor_exact(
                    expected_pocket_local,
                    supervision.pair_candidate_residue_local_index[
                        candidate_slice
                    ],
                )
                or bool((expected_ligand_local < 0).any().item())
                or bool(
                    (expected_ligand_local >= ligand_end - ligand_start)
                    .any()
                    .item()
                )
                or bool((expected_pocket_local < 0).any().item())
                or bool(
                    (expected_pocket_local >= pocket_end - pocket_start)
                    .any()
                    .item()
                )
                or int(pocket_flat[positive_index].item()) != flat_target
            ):
                _fail("MIXED_BATCH_FLAT_LOCAL_INDEX_INVALID")
            if sample_index >= 11 and int(
                supervision.pair_candidate_ligand_local_index[
                    positive_index
                ].item()
            ) != 20:
                _fail("K36_POSITIVE_LIGAND_NOT_C21")
            sample_active = supervision.ligand_active_diffusion_loss_mask[
                ligand_start:ligand_end, 0
            ]
            if not bool(sample_active.any().item()):
                _fail("MIXED_BATCH_SAMPLE_ACTIVE_MASK_EMPTY")
        if (
            int(supervision.pair_candidate_is_positive.sum().item()) != 16
            or not _tensor_exact(
                ~supervision.pair_candidate_is_positive,
                supervision.pair_candidate_is_negative,
            )
            or not bool(supervision.pair_head_candidate_loss_mask.all().item())
            or not bool(supervision.pair_positive_candidate_valid.all().item())
            or not bool((supervision.pair_negative_count > 0).all().item())
            or bool(
                supervision.pre_post_geometry_component_valid_mask.any().item()
            )
            or bool(
                supervision.pre_post_geometry_component_loss_mask.any().item()
            )
            or not bool(
                torch.isnan(
                    supervision.pre_post_geometry_target_angstrom
                ).all().item()
            )
        ):
            _fail("MIXED_BATCH_GLOBAL_SUPERVISION_INVALID")
        return None
    except Exception as error:
        _public_error(error)


class _Exact16ScheduleDatasetV1(Dataset[CovapieExpandedCysSgScheduleInputV1]):
    def __init__(self, *, epoch: int, task_schedule_seed: int) -> None:
        self._rows = tuple(
            CovapieExpandedCysSgScheduleInputV1(
                sample_identity=identity,
                epoch=epoch,
                task_schedule_seed=task_schedule_seed,
            )
            for identity in EXACT16_MEMBER_IDENTITIES_V1
        )

    def __len__(self) -> int:
        return len(self._rows)

    def __getitem__(self, index: int) -> CovapieExpandedCysSgScheduleInputV1:
        return self._rows[index]


class _Exact16DataLoaderCollatorV1:
    def __init__(
        self,
        *,
        current11_batch: dict[str, object],
        current11_runtime_result: dict[str, object],
        current11_authoritative_supervision: dict[str, object],
        repository_root: Path,
        state_root: Path,
    ) -> None:
        self.current11_batch = current11_batch
        self.current11_runtime_result = current11_runtime_result
        self.current11_authoritative_supervision = (
            current11_authoritative_supervision
        )
        self.repository_root = repository_root
        self.state_root = state_root

    def __call__(
        self, rows: list[CovapieExpandedCysSgScheduleInputV1]
    ) -> CovapieExpandedCysSgMixedBatchV1:
        if (
            len(rows) != 16
            or tuple(row.sample_identity for row in rows)
            != EXACT16_MEMBER_IDENTITIES_V1
            or len({row.epoch for row in rows}) != 1
            or len({row.task_schedule_seed for row in rows}) != 1
        ):
            _fail("DATALOADER_SCHEDULE_ROWS_INVALID")
        epoch = rows[0].epoch
        seed = rows[0].task_schedule_seed
        tensorized = []
        for row in rows:
            task_id = canonical_task_id_for_covapie_expanded_cys_sg_sample_v1(
                sample_identity=row.sample_identity,
                epoch=epoch,
                task_schedule_seed=seed,
            )
            if row.sample_identity in mixed_tensorizer.CURRENT11_MEMBER_IDENTITIES_V1:
                sample = mixed_tensorizer.tensorize_covapie_expanded_cys_sg_sample_v1(
                    sample_identity=row.sample_identity,
                    task_id=task_id,
                    device="cpu",
                    epoch=epoch,
                    task_schedule_seed=seed,
                    current11_batch=self.current11_batch,
                    current11_runtime_result=self.current11_runtime_result,
                    current11_authoritative_supervision=(
                        self.current11_authoritative_supervision
                    ),
                )
            else:
                sample = mixed_tensorizer.tensorize_covapie_expanded_cys_sg_sample_v1(
                    sample_identity=row.sample_identity,
                    task_id=task_id,
                    device="cpu",
                    repository_root=self.repository_root,
                    state_root=self.state_root,
                )
            tensorized.append(sample)
        return collate_covapie_expanded_cys_sg_exact16_tensorized_samples_v1(
            tensorized, epoch=epoch, task_schedule_seed=seed
        )


def _safe_root(value: object, *, reason: str) -> Path:
    if type(value) is not _PATH_TYPE or not value.is_absolute():
        _fail(reason)
    try:
        metadata = value.lstat()
        resolved = value.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise _MixedBatchInvariantError(reason) from error
    if (
        resolved != value
        or stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
    ):
        _fail(reason)
    return value


def _file_fingerprint(path: Path) -> tuple[int, str]:
    try:
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            _fail("PROTECTED_SOURCE_INVALID")
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise _MixedBatchInvariantError("PROTECTED_SOURCE_INVALID") from error
    return metadata.st_size, digest.hexdigest()


def _protected_sources_v1(
    *, repository_root: Path, state_root: Path, checkpoint_path: Path
) -> dict[str, Path]:
    return {
        "k36_effective_supervision_carrier": (
            state_root / mixed_tensorizer.K36_EFFECTIVE_CARRIER_RELATIVE_PATH_V1
        ),
        "k36_reaction_family_authority": (
            state_root / _K36_REACTION_FAMILY_AUTHORITY_RELATIVE_PATH_V1
        ),
        "k36_warhead_rule_authority": (
            state_root / _K36_WARHEAD_RULE_AUTHORITY_RELATIVE_PATH_V1
        ),
        "current11_formal_carrier": (
            state_root / _CURRENT11_FORMAL_CARRIER_RELATIVE_PATH_V1
        ),
        "current11_human_review_decision": (
            state_root / _CURRENT11_HUMAN_DECISION_RELATIVE_PATH_V1
        ),
        "k36_structural_evidence": (
            repository_root
            / mixed_tensorizer.K36_STRUCTURAL_EVIDENCE_RELATIVE_PATH_V1
        ),
        "legacy_checkpoint": checkpoint_path,
    }


def _nonzero_finite_gradient(parameter: nn.Parameter) -> bool:
    gradient = parameter.grad
    return bool(
        gradient is not None
        and torch.isfinite(gradient).all().item()
        and torch.count_nonzero(gradient).item() > 0
    )


def _all_finite(values: Sequence[torch.Tensor]) -> bool:
    return all(bool(torch.isfinite(value).all().item()) for value in values)


def _clone_head_v1(repository_root: Path, clone_root: Path) -> None:
    import subprocess

    completed = subprocess.run(
        (
            "git",
            "clone",
            "--local",
            "--no-hardlinks",
            str(repository_root),
            str(clone_root),
        ),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
    )
    if completed.returncode != 0:
        _fail("LOCAL_CLONE_FAILED")
    baseline_commit = subprocess.run(
        (
            "git",
            "rev-parse",
            "--verify",
            f"{_EXPECTED_BASELINE_HEAD_V1}^{{commit}}",
        ),
        cwd=clone_root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
    )
    if (
        baseline_commit.returncode != 0
        or baseline_commit.stdout.strip() != _EXPECTED_BASELINE_HEAD_V1
    ):
        _fail("FROZEN_BASELINE_COMMIT_UNAVAILABLE")
    checkout = subprocess.run(
        (
            "git",
            "checkout",
            "-B",
            "main",
            _EXPECTED_BASELINE_HEAD_V1,
        ),
        cwd=clone_root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
    )
    if checkout.returncode != 0:
        _fail("FROZEN_BASELINE_CHECKOUT_FAILED")
    for path in clone_root.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        mode = stat.S_IMODE(path.stat().st_mode)
        path.chmod(0o755 if mode & 0o111 else 0o644)
    resolved = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=clone_root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
    )
    if resolved.returncode != 0 or resolved.stdout.strip() != _EXPECTED_BASELINE_HEAD_V1:
        _fail("LOCAL_CLONE_BASELINE_INVALID")


def _run_smoke_impl(
    *,
    repository_root: Path,
    state_root: Path,
    checkpoint_path: Path,
    device: str,
) -> dict[str, object]:
    import tempfile

    from covalent_ext import (
        covapie_current11_checkpoint_migration_and_real_one_batch_train_path_smoke_v1
        as current11_smoke,
    )
    from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (
        compute_covapie_current11_training_losses_v1,
    )
    from covalent_ext.covapie_current11_training_lightning_module_v1 import (
        run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1,
    )

    repository = _safe_root(repository_root, reason="REPOSITORY_ROOT_INVALID")
    state = _safe_root(state_root, reason="STATE_ROOT_INVALID")
    if (
        type(checkpoint_path) is not _PATH_TYPE
        or not checkpoint_path.is_absolute()
        or device != "cpu"
    ):
        _fail("SMOKE_INPUT_INVALID")
    protected_paths = _protected_sources_v1(
        repository_root=repository,
        state_root=state,
        checkpoint_path=checkpoint_path,
    )
    before = {
        name: _file_fingerprint(path)
        for name, path in protected_paths.items()
    }
    expected_digests = {
        "k36_effective_supervision_carrier": (
            mixed_tensorizer.K36_EFFECTIVE_CARRIER_SHA256_V1
        ),
        "k36_reaction_family_authority": (
            _EXPECTED_K36_REACTION_FAMILY_AUTHORITY_SHA256_V1
        ),
        "k36_warhead_rule_authority": (
            _EXPECTED_K36_WARHEAD_RULE_AUTHORITY_SHA256_V1
        ),
        "current11_formal_carrier": (
            _EXPECTED_CURRENT11_FORMAL_CARRIER_SHA256_V1
        ),
        "current11_human_review_decision": (
            _EXPECTED_CURRENT11_HUMAN_DECISION_SHA256_V1
        ),
        "k36_structural_evidence": (
            mixed_tensorizer.K36_STRUCTURAL_EVIDENCE_SHA256_V1
        ),
        "legacy_checkpoint": _EXPECTED_CHECKPOINT_SHA256_V1,
    }
    if any(
        before[name][1] != expected_digest
        for name, expected_digest in expected_digests.items()
    ):
        _fail("PROTECTED_SOURCE_SHA256_MISMATCH")
    if before["legacy_checkpoint"] != (
        _EXPECTED_CHECKPOINT_SIZE_V1,
        _EXPECTED_CHECKPOINT_SHA256_V1,
    ):
        _fail("LEGACY_CHECKPOINT_IDENTITY_INVALID")

    with tempfile.TemporaryDirectory(prefix="covapie_exact16_smoke_") as temporary:
        clone_root = Path(temporary) / "repository"
        _clone_head_v1(repository, clone_root)
        real = current11_smoke._build_real_current11_batch_v1(
            repo_root=clone_root,
            state_root=state,
        )
        dataset = _Exact16ScheduleDatasetV1(
            epoch=0, task_schedule_seed=0
        )
        loader = DataLoader(
            dataset,
            batch_size=16,
            shuffle=False,
            num_workers=0,
            drop_last=False,
            collate_fn=_Exact16DataLoaderCollatorV1(
                current11_batch=real["model_batch"],
                current11_runtime_result=real["runtime"],
                current11_authoritative_supervision=(
                    real["authoritative_supervision"]
                ),
                repository_root=repository,
                state_root=state,
            ),
        )
        iterator = iter(loader)
        mixed_batch = next(iterator)
        try:
            next(iterator)
        except StopIteration:
            pass
        else:
            _fail("DATALOADER_YIELDED_MORE_THAN_ONE_BATCH")

        checkpoint = current11_smoke.load_covapie_current11_legacy_checkpoint_v1(
            checkpoint_path=checkpoint_path
        )
        checkpoint_state = checkpoint["state_dict"]
        torch.manual_seed(20260818)
        model = current11_smoke._instantiate_current11_model_v1(
            repo_root=repository, state_root=state, device=device
        )
        migration = (
            current11_smoke.migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
                model=model, checkpoint_state_dict=checkpoint_state
            )
        )
        if (
            migration["checkpoint_key_count"] != 122
            or migration["target_model_key_count"] != 141
            or migration["shared_key_count"] != 122
            or migration["checkpoint_only_key_count"] != 0
            or migration["shared_shape_mismatch_count"] != 0
            or migration["full_target_strict_load"] is not True
            or migration["migration_missing_keys"] != ()
            or migration["migration_unexpected_keys"] != ()
        ):
            _fail("CHECKPOINT_MIGRATION_NOT_EXACT")

        model.train()
        model_batch = mixed_batch.model_input_batch
        supervision = mixed_batch.supervision
        ligand, pocket = model.get_ligand_and_pocket(model_batch)
        role_delta = (
            model.covapie_current11_auxiliary_model_v1
            .encode_role_mask_anchor_v1(
                supervision=supervision,
                ligand_batch_index=ligand["mask"],
            )
        )
        indicator = supervision.target_residue_reactive_atom_mask[:, 0]
        torch.manual_seed(20260818)
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
        losses = compute_covapie_current11_training_losses_v1(
            model_output=model_output,
            supervision=supervision,
            diffusion_trace=trace,
            loss_weights=model.covapie_current11_loss_weights,
            pair_contrastive_temperature=(
                model.covapie_current11_pair_contrastive_temperature
            ),
            geometry_smooth_l1_beta=1.0,
        )
        forward_tensors = (
            trace.diffusion_epsilon_prediction_ligand,
            trace.diffusion_epsilon_prediction_pocket,
            trace.ligand_node_hidden,
            trace.pocket_node_hidden,
            trace.base_objective_per_sample,
            model_output.pair_embeddings,
            model_output.pair_logits,
            model_output.pre_post_geometry_predictions_angstrom,
        )
        loss_tensors = (
            losses.loss_base_diffusion,
            losses.loss_covalent_pair_prediction,
            losses.loss_pre_post_geometry,
            losses.loss_covalent_pair_contrastive,
            losses.loss_total,
        )
        k36_indices = mixed_batch.k36_batch_indices
        if (
            trace.base_objective_per_sample.shape != (16,)
            or losses.pair_prediction_per_sample_detached.shape != (16,)
            or losses.pair_contrastive_per_sample_detached.shape != (16,)
            or not _all_finite(forward_tensors)
            or not _all_finite(loss_tensors)
            or losses.base_diffusion_valid_sample_count != 16
            or losses.covalent_pair_prediction_valid_sample_count != 16
            or losses.pre_post_geometry_valid_sample_count != 0
            or losses.covalent_pair_contrastive_valid_sample_count != 16
            or float(losses.loss_pre_post_geometry.detach().item()) != 0.0
            or not bool(
                torch.isfinite(
                    trace.base_objective_per_sample[list(k36_indices)]
                ).all().item()
            )
            or not bool(
                torch.isfinite(
                    losses.pair_prediction_per_sample_detached[
                        list(k36_indices)
                    ]
                ).all().item()
            )
            or not bool(
                torch.isfinite(
                    losses.pair_contrastive_per_sample_detached[
                        list(k36_indices)
                    ]
                ).all().item()
            )
        ):
            _fail("MIXED_MODEL_FORWARD_OR_LOSS_INVALID")
        for index in k36_indices:
            ligand_rows = model_batch["lig_mask"] == index
            if (
                not bool(supervision.sample_training_admitted[index])
                or not bool(supervision.canonical_task_valid[index])
                or not bool(
                    supervision.ligand_active_diffusion_loss_mask[
                        ligand_rows, 0
                    ].any().item()
                )
                or not bool(supervision.pair_positive_candidate_valid[index])
                or int(supervision.pair_negative_count[index].item()) <= 0
            ):
                _fail("K36_NOT_IN_ACTUAL_MIXED_OBJECTIVE")

        optimizer = model.configure_optimizers()
        named_parameters = dict(model.named_parameters())
        model_parameters = list(model.parameters())
        model_parameter_ids = [id(parameter) for parameter in model_parameters]
        optimizer_parameters = [
            parameter
            for group in optimizer.param_groups
            for parameter in group["params"]
        ]
        optimizer_parameter_ids = [id(parameter) for parameter in optimizer_parameters]
        if (
            not isinstance(optimizer, torch.optim.AdamW)
            or len(model_parameter_ids) != len(set(model_parameter_ids))
            or len(optimizer_parameter_ids) != len(set(optimizer_parameter_ids))
            or set(model_parameter_ids) != set(optimizer_parameter_ids)
        ):
            _fail("OPTIMIZER_PARAMETER_OWNERSHIP_INVALID")
        parameter_before = {
            name: parameter.detach().clone()
            for name, parameter in named_parameters.items()
        }
        shared_names = {
            name for name in named_parameters if name in checkpoint_state
        }
        new_names = set(named_parameters) - shared_names
        target_name = current11_smoke.LEGACY_ALLOWED_NEW_EXACT_KEYS_V1[0]
        role_names = {
            name
            for name in named_parameters
            if name.startswith((
                "covapie_current11_auxiliary_model_v1.role_embedding.",
                "covapie_current11_auxiliary_model_v1.task_embedding.",
                "covapie_current11_auxiliary_model_v1.generation_state_embedding.",
                "covapie_current11_auxiliary_model_v1.seed_indicator_embedding.",
                "covapie_current11_auxiliary_model_v1.anchor_distance_encoder.",
            ))
        }
        pair_names = {
            name
            for name in named_parameters
            if name.startswith((
                "covapie_current11_auxiliary_model_v1.pair_embedding.",
                "covapie_current11_auxiliary_model_v1.pair_logit.",
            ))
        }
        geometry_names = {
            name
            for name in named_parameters
            if name.startswith(
                "covapie_current11_auxiliary_model_v1.pre_post_geometry_head."
            )
        }
        if (
            "ddpm.dynamics.egnn.embedding.weight" not in shared_names
            or target_name not in named_parameters
            or not role_names
            or not pair_names
            or not geometry_names
        ):
            _fail("GRADIENT_PARAMETER_GROUP_INVALID")
        optimizer.zero_grad(set_to_none=True)
        if (
            losses.loss_total.ndim != 0
            or not losses.loss_total.requires_grad
            or not bool(torch.isfinite(losses.loss_total).item())
        ):
            _fail("TOTAL_LOSS_NOT_BACKWARD_READY")
        losses.loss_total.backward()
        gradients = [
            parameter.grad
            for parameter in model_parameters
            if parameter.grad is not None
        ]
        shared_gradient = any(
            _nonzero_finite_gradient(named_parameters[name])
            for name in shared_names
        )
        target_gradient = _nonzero_finite_gradient(
            named_parameters[target_name]
        )
        role_gradient = any(
            _nonzero_finite_gradient(named_parameters[name])
            for name in role_names
        )
        pair_gradient = any(
            _nonzero_finite_gradient(named_parameters[name])
            for name in pair_names
        )
        geometry_gradient = any(
            _nonzero_finite_gradient(named_parameters[name])
            for name in geometry_names
        )
        if (
            not gradients
            or not _all_finite(gradients)
            or not shared_gradient
            or not target_gradient
            or not role_gradient
            or not pair_gradient
            or geometry_gradient
        ):
            _fail("MIXED_BACKWARD_GRADIENT_INVALID")
        optimizer.step()
        changed_names = {
            name
            for name, parameter in named_parameters.items()
            if not torch.equal(parameter.detach(), parameter_before[name])
        }
        shared_changed = bool(changed_names & shared_names)
        new_changed = bool(changed_names & new_names)
        target_changed = target_name in changed_names
        all_parameters_finite = all(
            bool(torch.isfinite(parameter).all().item())
            for parameter in model_parameters
        )
        if (
            not shared_changed
            or not new_changed
            or not target_changed
            or not all_parameters_finite
        ):
            _fail("MIXED_OPTIMIZER_STEP_INVALID")

        after = {
            name: _file_fingerprint(path)
            for name, path in protected_paths.items()
        }
        if after != before:
            _fail("PROTECTED_SOURCE_MODIFIED")
        ligand_node_count = len(model_batch["lig_coords"])
        pocket_node_count = len(model_batch["pocket_coords"])
        pair_candidate_count = len(supervision.pair_candidate_batch_index)
        k36_tasks = tuple(
            mixed_batch.scheduled_task_ids[index] for index in k36_indices
        )
        return {
            "implementation_status": "passed",
            "baseline_HEAD": _EXPECTED_BASELINE_HEAD_V1,
            "candidate_scope_exact2": True,
            "scheduler_current11_exact_parity": True,
            "scheduler_k36_valid_tasks_exact_0_3_4": True,
            "scheduler_order_independent": True,
            "scheduler_deterministic": True,
            "integration_population_exact16": True,
            "mixed_batch_sample_count": 16,
            "mixed_batch_current11_count": 11,
            "mixed_batch_k36_count": 5,
            "mixed_batch_ligand_node_count": ligand_node_count,
            "mixed_batch_pocket_node_count": pocket_node_count,
            "mixed_batch_pair_candidate_count": pair_candidate_count,
            "mixed_batch_positive_pair_count": int(
                supervision.pair_candidate_is_positive.sum().item()
            ),
            "no_cross_sample_pair_candidates": True,
            "current11_supervision_preserved_in_mixed_batch": True,
            "k36_supervision_preserved_in_mixed_batch": True,
            "K36_participated_in_actual_mixed_objective": True,
            "k36_actual_batch_indices": k36_indices,
            "k36_scheduled_task_ids": k36_tasks,
            "DataLoader_executed": True,
            "DataLoader_batch_count": 1,
            "legacy_checkpoint_SHA256": checkpoint["checkpoint_sha256"],
            "legacy_checkpoint_size_bytes": checkpoint["checkpoint_size_bytes"],
            "checkpoint_key_count": migration["checkpoint_key_count"],
            "target_model_key_count": migration["target_model_key_count"],
            "shared_exact_key_count": migration["shared_key_count"],
            "checkpoint_only_key_count": migration["checkpoint_only_key_count"],
            "shape_mismatch_count": migration["shared_shape_mismatch_count"],
            "checkpoint_migration_exact": True,
            "model_core_forward": True,
            "mixed_profile_model_core_forward": True,
            "base_loss": float(losses.loss_base_diffusion.detach().item()),
            "pair_prediction_loss": float(
                losses.loss_covalent_pair_prediction.detach().item()
            ),
            "geometry_loss": float(
                losses.loss_pre_post_geometry.detach().item()
            ),
            "contrastive_loss": float(
                losses.loss_covalent_pair_contrastive.detach().item()
            ),
            "total_loss": float(losses.loss_total.detach().item()),
            "base_valid_sample_count": losses.base_diffusion_valid_sample_count,
            "pair_valid_sample_count": losses.covalent_pair_prediction_valid_sample_count,
            "geometry_valid_sample_count": losses.pre_post_geometry_valid_sample_count,
            "contrastive_valid_sample_count": losses.covalent_pair_contrastive_valid_sample_count,
            "all_enabled_losses_finite": True,
            "backward": True,
            "all_existing_gradients_finite": True,
            "shared_pretrained_nonzero_gradient": shared_gradient,
            "target_residue_embedding_nonzero_gradient": target_gradient,
            "role_mask_anchor_group_nonzero_gradient": role_gradient,
            "pair_head_nonzero_gradient": pair_gradient,
            "geometry_head_nonzero_gradient": geometry_gradient,
            "optimizer_type": type(optimizer).__name__,
            "optimizer_parameter_unique": True,
            "optimizer_parameter_set_exact": True,
            "optimizer_step": True,
            "optimizer_step_count": 1,
            "shared_parameter_changed": shared_changed,
            "new_covapie_parameter_changed": new_changed,
            "target_residue_parameter_changed": target_changed,
            "all_parameters_finite_after_step": all_parameters_finite,
            "PRE_geometry_supervision_authority_complete": False,
            "exact10_feature_semantics_reopened": False,
            "exact10_feature_semantics_status": "RESOLVED_AND_CLOSED",
            "protected_sources_byte_unchanged": True,
            "checkpoint_byte_unchanged": True,
            "state_modified": False,
            "mixed_profile_batch_scheduling_tested": True,
            "mixed_profile_collation_tested": True,
            "mixed_profile_exact16_one_batch_built": True,
            "mixed_profile_losses_computed": True,
            "mixed_profile_one_batch_smoke_pass": True,
            "existing_Current11_Lightning_forward_used_for_mixed": False,
            "published_lower_level_CovaPIE_model_bridge_used": True,
            "ready_for_mixed_profile_lightning_training_bridge": True,
            "Trainer_fit": False,
            "ready_for_training": False,
            "K2Z_status": "PENDING_EMBEDDED_WARHEAD_MULTI_BOUNDARY_RUNTIME",
            "1ZB_status": "READY_FOR_HUMAN_APPROVAL",
            "remaining_blockers": (
                "EXPANDED_MIXED_PROFILE_LIGHTNING_FORWARD_NOT_IMPLEMENTED",
                "EXPANDED_MIXED_PROFILE_TRAINER_FIT_SMOKE_ABSENT",
                "PRE_GEOMETRY_SUPERVISION_AUTHORITY_NOT_ESTABLISHED",
            ),
            "recommended_next_step_exactly": (
                "review_and_publish_covapie_expanded_cys_sg_mixed_profile_"
                "batch_scheduler_and_one_batch_smoke_v1"
            ),
        }


def run_covapie_expanded_cys_sg_mixed_profile_one_batch_smoke_v1(
    *,
    repository_root: Path,
    state_root: Path,
    checkpoint_path: Path,
    device: str = "cpu",
) -> dict[str, object]:
    """Execute exactly one real Exact16 forward/backward/AdamW step on CPU."""

    try:
        return _run_smoke_impl(
            repository_root=repository_root,
            state_root=state_root,
            checkpoint_path=checkpoint_path,
            device=device,
        )
    except Exception as error:
        _public_error(error)


def run_covapie_expanded_cys_sg_mixed_profile_batch_scheduler_and_one_batch_smoke_v1(
    *,
    repository_root: Path,
    state_root: Path,
    checkpoint_path: Path,
    device: str = "cpu",
) -> dict[str, object]:
    """Exact task-name alias for the bounded mixed-profile smoke."""

    return run_covapie_expanded_cys_sg_mixed_profile_one_batch_smoke_v1(
        repository_root=repository_root,
        state_root=state_root,
        checkpoint_path=checkpoint_path,
        device=device,
    )
