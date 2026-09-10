"""Additive Current11 hidden conditioning, auxiliary heads, and losses V1."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, NoReturn

import torch
from torch import nn
import torch.nn.functional as F

from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


__all__ = (
    "CovapieCurrent11AuxiliaryModelV1",
    "CovapieCurrent11LossOutputV1",
    "CovapieCurrent11LossWeightsV1",
    "CovapieCurrent11ModelOutputV1",
    "compute_covapie_current11_training_losses_v1",
)


AUXILIARY_ERROR = "COVAPIE_CURRENT11_AUXILIARY_MODEL_AND_LOSS_V1_ERROR"
_EXISTING_COMPONENT_MASKS_PURPOSE_V1 = "existing_component_masks_v1"
_INDEPENDENT_HIDDEN_POST_DISTANCE_PURPOSE_V1 = (
    "independent_hidden_post_distance_v1"
)
_POST_GEOMETRY_COMPONENT_INDEX_V1 = 1


@dataclass(frozen=True)
class CovapieCurrent11LossWeightsV1:
    base_diffusion: float = 1.0
    covalent_pair_prediction: float = 1.0
    pre_post_geometry: float = 0.0
    covalent_pair_contrastive: float = 0.1


@dataclass(frozen=True)
class CovapieCurrent11ModelOutputV1:
    diffusion_epsilon_prediction_ligand: torch.Tensor
    denoised_ligand_xh: torch.Tensor
    diffusion_timestep_int: torch.Tensor
    ligand_node_hidden: torch.Tensor
    pocket_node_hidden: torch.Tensor
    role_mask_anchor_hidden_delta: torch.Tensor
    pair_embeddings: torch.Tensor
    pair_logits: torch.Tensor
    pre_post_geometry_predictions_angstrom: torch.Tensor
    target_pair_consistency: torch.Tensor
    canonical_task_id: torch.Tensor
    pair_candidate_offsets: torch.Tensor
    pair_candidate_batch_index: torch.Tensor
    pair_candidate_ligand_local_index: torch.Tensor
    pair_candidate_residue_local_index: torch.Tensor
    pair_candidate_ligand_flat_index: torch.Tensor
    pair_candidate_pocket_flat_index: torch.Tensor


@dataclass(frozen=True)
class CovapieCurrent11LossOutputV1:
    loss_base_diffusion: torch.Tensor
    loss_covalent_pair_prediction: torch.Tensor
    loss_pre_post_geometry: torch.Tensor
    loss_covalent_pair_contrastive: torch.Tensor
    loss_total: torch.Tensor
    base_diffusion_valid_sample_count: int
    covalent_pair_prediction_valid_sample_count: int
    pre_post_geometry_valid_sample_count: int
    covalent_pair_contrastive_valid_sample_count: int
    pair_prediction_per_sample_detached: torch.Tensor
    pre_post_geometry_per_sample_detached: torch.Tensor
    pair_contrastive_per_sample_detached: torch.Tensor


class _AuxiliaryInvariantError(Exception):
    pass


def _fail() -> NoReturn:
    raise _AuxiliaryInvariantError()


def _tensor(
    value: object,
    *,
    dtype: torch.dtype | None = None,
    ndim: int | None = None,
) -> torch.Tensor:
    if (
        not isinstance(value, torch.Tensor)
        or (dtype is not None and value.dtype != dtype)
        or (ndim is not None and value.ndim != ndim)
    ):
        _fail()
    return value


def _assign_rows(
    output: torch.Tensor, rows: torch.Tensor, values: torch.Tensor
) -> torch.Tensor:
    if rows.dtype != torch.bool or rows.ndim != 1 or len(rows) != len(output):
        _fail()
    if rows.any():
        output = output.index_copy(0, torch.nonzero(rows).flatten(), values)
    return output


class CovapieCurrent11AuxiliaryModelV1(nn.Module):
    """Single registered owner for all new Current11 trainable parameters."""

    def __init__(self, *, joint_nf: int):
        super().__init__()
        if type(joint_nf) is not int or joint_nf <= 0:
            raise ValueError(AUXILIARY_ERROR)
        self.joint_nf = joint_nf

        self.role_embedding = nn.Embedding(3, joint_nf)
        self.task_embedding = nn.Embedding(5, joint_nf)
        self.generation_state_embedding = nn.Embedding(2, joint_nf)
        self.seed_indicator_embedding = nn.Embedding(2, joint_nf)
        self.anchor_distance_encoder = nn.Sequential(
            nn.Linear(1, joint_nf),
            nn.SiLU(),
            nn.Linear(joint_nf, joint_nf),
        )

        self.pair_embedding = nn.Sequential(
            nn.Linear(4 * joint_nf + 1, joint_nf),
            nn.SiLU(),
            nn.Linear(joint_nf, joint_nf),
        )
        self.pair_logit = nn.Linear(joint_nf, 1)
        self.pre_post_geometry_head = nn.Sequential(
            nn.Linear(joint_nf, joint_nf),
            nn.SiLU(),
            nn.Linear(joint_nf, 2),
        )
        self._reset_zero_delta_parameters_v1()

    def _reset_zero_delta_parameters_v1(self) -> None:
        with torch.no_grad():
            self.role_embedding.weight.zero_()
            self.task_embedding.weight.zero_()
            self.generation_state_embedding.weight.zero_()
            self.seed_indicator_embedding.weight.zero_()
            final_anchor = self.anchor_distance_encoder[-1]
            if not isinstance(final_anchor, nn.Linear):
                _fail()
            final_anchor.weight.zero_()
            final_anchor.bias.zero_()

    def encode_role_mask_anchor_v1(
        self,
        *,
        supervision: CovapieCurrent11TrainingSupervisionTensorsV1,
        ligand_batch_index: torch.Tensor,
    ) -> torch.Tensor:
        """Create the additive ligand hidden delta without invalid gathers."""

        try:
            if not isinstance(
                supervision, CovapieCurrent11TrainingSupervisionTensorsV1
            ):
                _fail()
            ligand_batch_index = _tensor(
                ligand_batch_index, dtype=torch.long, ndim=1
            )
            role_id = _tensor(
                supervision.ligand_role_id, dtype=torch.long, ndim=1
            )
            role_valid = _tensor(
                supervision.ligand_role_valid, dtype=torch.bool, ndim=1
            )
            anchor_valid_mask = _tensor(
                supervision.ligand_anchor_distance_valid,
                dtype=torch.bool,
                ndim=2,
            )
            fixed_mask = _tensor(
                supervision.ligand_base_fixed_mask,
                dtype=torch.bool,
                ndim=2,
            )
            generation_mask = _tensor(
                supervision.ligand_base_generation_mask,
                dtype=torch.bool,
                ndim=2,
            )
            anchor_distance = _tensor(
                supervision.ligand_anchor_distance_angstrom,
                ndim=2,
            )
            ligand_column_shape = (len(role_id), 1)
            if (
                len(role_id) != len(ligand_batch_index)
                or len(role_valid) != len(role_id)
                or ligand_batch_index.device != role_id.device
                or role_id.device != self.role_embedding.weight.device
                or anchor_valid_mask.shape != ligand_column_shape
                or fixed_mask.shape != ligand_column_shape
                or generation_mask.shape != ligand_column_shape
                or anchor_distance.shape != ligand_column_shape
                or not torch.is_floating_point(anchor_distance)
                or anchor_valid_mask.device != role_id.device
                or fixed_mask.device != role_id.device
                or generation_mask.device != role_id.device
                or anchor_distance.device != role_id.device
            ):
                _fail()
            if bool((fixed_mask & generation_mask).any().item()):
                _fail()
            batch_size = len(supervision.canonical_task_id)
            if (
                len(ligand_batch_index) == 0
                or int(ligand_batch_index.min().item()) < 0
                or int(ligand_batch_index.max().item()) >= batch_size
            ):
                _fail()
            dtype = self.role_embedding.weight.dtype
            delta = torch.zeros(
                (len(role_id), self.joint_nf),
                dtype=dtype,
                device=role_id.device,
            )

            if bool(role_valid.any().item()):
                valid_roles = role_id[role_valid]
                if bool(((valid_roles < 0) | (valid_roles > 2)).any().item()):
                    _fail()
                delta = _assign_rows(
                    delta,
                    role_valid,
                    self.role_embedding(valid_roles),
                )
            task_valid_by_node = supervision.canonical_task_valid[
                ligand_batch_index
            ]
            task_id_by_node = supervision.canonical_task_id[
                ligand_batch_index
            ]
            if bool(task_valid_by_node.any().item()):
                valid_task_ids = task_id_by_node[task_valid_by_node]
                if bool(((valid_task_ids < 0) | (valid_task_ids > 4)).any().item()):
                    _fail()
                task_delta = torch.zeros_like(delta)
                task_delta = _assign_rows(
                    task_delta,
                    task_valid_by_node,
                    self.task_embedding(valid_task_ids),
                )
                delta = delta + task_delta

            generation_state = generation_mask[:, 0].long()
            delta = delta + self.generation_state_embedding(generation_state)

            seed_valid_by_node = supervision.ligand_minimal_seed_or_anchor_valid[
                ligand_batch_index
            ]
            seed_indicator = supervision.ligand_minimal_seed_or_anchor_mask[
                :, 0
            ].long()
            if bool(seed_valid_by_node.any().item()):
                seed_delta = torch.zeros_like(delta)
                seed_delta = _assign_rows(
                    seed_delta,
                    seed_valid_by_node,
                    self.seed_indicator_embedding(
                        seed_indicator[seed_valid_by_node]
                    ),
                )
                delta = delta + seed_delta

            effective_anchor_valid = (
                anchor_valid_mask & fixed_mask & ~generation_mask
            )[:, 0]
            if bool(effective_anchor_valid.any().item()):
                distance = anchor_distance[effective_anchor_valid]
                if (
                    not bool(torch.isfinite(distance).all().item())
                    or bool((distance < 0).any().item())
                ):
                    _fail()
                anchor_delta = torch.zeros_like(delta)
                encoded = self.anchor_distance_encoder(torch.log1p(distance))
                anchor_delta = _assign_rows(
                    anchor_delta, effective_anchor_valid, encoded
                )
                delta = delta + anchor_delta
            return delta
        except Exception as error:
            if type(error) is ValueError and str(error) == AUXILIARY_ERROR:
                raise
            raise ValueError(AUXILIARY_ERROR) from error

    def forward(
        self,
        *,
        diffusion_trace: object,
        supervision: CovapieCurrent11TrainingSupervisionTensorsV1,
        role_mask_anchor_hidden_delta: torch.Tensor,
    ) -> CovapieCurrent11ModelOutputV1:
        """Vectorize pair/geometry heads over the frozen candidate domain."""

        try:
            ligand_hidden = _tensor(
                getattr(diffusion_trace, "ligand_node_hidden", None), ndim=2
            )
            pocket_hidden = _tensor(
                getattr(diffusion_trace, "pocket_node_hidden", None), ndim=2
            )
            epsilon_prediction = _tensor(
                getattr(
                    diffusion_trace,
                    "diffusion_epsilon_prediction_ligand",
                    None,
                ),
                ndim=2,
            )
            denoised_ligand_xh = _tensor(
                getattr(diffusion_trace, "denoised_ligand_xh", None), ndim=2
            )
            clean_pocket_xh = _tensor(
                getattr(diffusion_trace, "clean_centered_pocket_xh", None),
                ndim=2,
            )
            timestep = _tensor(
                getattr(diffusion_trace, "diffusion_timestep_int", None),
                dtype=torch.long,
                ndim=1,
            )
            role_delta = _tensor(role_mask_anchor_hidden_delta, ndim=2)
            if (
                ligand_hidden.shape != role_delta.shape
                or ligand_hidden.shape[1] != self.joint_nf
                or pocket_hidden.shape[1] != self.joint_nf
                or len(epsilon_prediction) != len(ligand_hidden)
                or len(denoised_ligand_xh) != len(ligand_hidden)
                or len(clean_pocket_xh) != len(pocket_hidden)
                or epsilon_prediction.shape[1] < 4
                or denoised_ligand_xh.shape[1] < 4
                or clean_pocket_xh.shape[1] < 4
            ):
                _fail()

            lig_index = supervision.pair_candidate_ligand_flat_index
            pocket_index = supervision.pair_candidate_pocket_flat_index
            if (
                lig_index.dtype != torch.long
                or pocket_index.dtype != torch.long
                or lig_index.ndim != 1
                or pocket_index.shape != lig_index.shape
                or (len(lig_index) and (
                    int(lig_index.min().item()) < 0
                    or int(lig_index.max().item()) >= len(ligand_hidden)
                    or int(pocket_index.min().item()) < 0
                    or int(pocket_index.max().item()) >= len(pocket_hidden)
                ))
            ):
                _fail()
            h_ligand = ligand_hidden[lig_index]
            h_pocket = pocket_hidden[pocket_index]
            coordinate_normalization = getattr(
                diffusion_trace, "coordinate_normalization", None
            )
            if (
                type(coordinate_normalization) not in (int, float)
                or type(coordinate_normalization) is bool
                or not math.isfinite(float(coordinate_normalization))
                or float(coordinate_normalization) <= 0
            ):
                _fail()
            distance_angstrom = torch.linalg.vector_norm(
                (
                    denoised_ligand_xh[lig_index, :3]
                    - clean_pocket_xh[pocket_index, :3]
                ) * float(coordinate_normalization),
                dim=1,
                keepdim=True,
            )
            pair_input = torch.cat((
                h_ligand,
                h_pocket,
                h_ligand * h_pocket,
                torch.abs(h_ligand - h_pocket),
                distance_angstrom,
            ), dim=1)
            pair_embeddings = self.pair_embedding(pair_input)
            pair_logits = self.pair_logit(pair_embeddings).squeeze(-1)
            geometry = F.softplus(
                self.pre_post_geometry_head(pair_embeddings)
            )

            positive = supervision.pair_positive_candidate_index
            positive_valid = supervision.pair_positive_candidate_valid
            target_flat = supervision.target_residue_reactive_atom_flat_index
            target_pair_consistency = torch.zeros(
                len(positive), dtype=torch.bool, device=pair_logits.device
            )
            if bool(positive_valid.any().item()):
                valid_samples = torch.nonzero(positive_valid).flatten()
                candidate_indices = positive[valid_samples]
                target_pair_consistency[valid_samples] = (
                    supervision.pair_candidate_pocket_flat_index[
                        candidate_indices
                    ] == target_flat[valid_samples]
                )
            if not bool(target_pair_consistency[positive_valid].all().item()):
                _fail()
            return CovapieCurrent11ModelOutputV1(
                diffusion_epsilon_prediction_ligand=epsilon_prediction,
                denoised_ligand_xh=denoised_ligand_xh,
                diffusion_timestep_int=timestep,
                ligand_node_hidden=ligand_hidden,
                pocket_node_hidden=pocket_hidden,
                role_mask_anchor_hidden_delta=role_delta,
                pair_embeddings=pair_embeddings,
                pair_logits=pair_logits,
                pre_post_geometry_predictions_angstrom=geometry,
                target_pair_consistency=target_pair_consistency,
                canonical_task_id=supervision.canonical_task_id,
                pair_candidate_offsets=supervision.pair_candidate_offsets,
                pair_candidate_batch_index=(
                    supervision.pair_candidate_batch_index
                ),
                pair_candidate_ligand_local_index=(
                    supervision.pair_candidate_ligand_local_index
                ),
                pair_candidate_residue_local_index=(
                    supervision.pair_candidate_residue_local_index
                ),
                pair_candidate_ligand_flat_index=lig_index,
                pair_candidate_pocket_flat_index=pocket_index,
            )
        except Exception as error:
            if type(error) is ValueError and str(error) == AUXILIARY_ERROR:
                raise
            raise ValueError(AUXILIARY_ERROR) from error


def _validated_weights(
    value: object,
) -> CovapieCurrent11LossWeightsV1:
    if isinstance(value, CovapieCurrent11LossWeightsV1):
        weights = value
    elif type(value) is dict and tuple(sorted(value)) == tuple(sorted((
        "base_diffusion",
        "covalent_pair_prediction",
        "pre_post_geometry",
        "covalent_pair_contrastive",
    ))):
        weights = CovapieCurrent11LossWeightsV1(**value)
    else:
        _fail()
    for item in (
        weights.base_diffusion,
        weights.covalent_pair_prediction,
        weights.pre_post_geometry,
        weights.covalent_pair_contrastive,
    ):
        if (
            type(item) not in (int, float)
            or type(item) is bool
            or not math.isfinite(float(item))
            or float(item) < 0
        ):
            _fail()
    return weights


def _hidden_post_effective_component_loss_mask_v1(
    *,
    model_output: CovapieCurrent11ModelOutputV1,
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1,
    ligand_batch_index: torch.Tensor | None,
    pocket_batch_index: torch.Tensor | None,
) -> torch.Tensor:
    """Restrict only POST to independently verified hidden endpoints."""

    geometry_predictions = _tensor(
        model_output.pre_post_geometry_predictions_angstrom, ndim=2
    )
    ligand_hidden = _tensor(model_output.ligand_node_hidden, ndim=2)
    pocket_hidden = _tensor(model_output.pocket_node_hidden, ndim=2)
    admitted = _tensor(
        supervision.sample_training_admitted, dtype=torch.bool, ndim=1
    )
    batch_size = len(admitted)
    candidate_count = len(geometry_predictions)
    ligand_count = len(ligand_hidden)
    pocket_count = len(pocket_hidden)
    device = geometry_predictions.device
    if (
        batch_size == 0
        or geometry_predictions.shape != (candidate_count, 2)
        or not torch.is_floating_point(geometry_predictions)
        or ligand_hidden.device != device
        or pocket_hidden.device != device
    ):
        _fail()

    sample_bool_masks = (
        admitted,
        _tensor(
            supervision.canonical_task_valid,
            dtype=torch.bool,
            ndim=1,
        ),
        _tensor(
            supervision.target_residue_condition_valid,
            dtype=torch.bool,
            ndim=1,
        ),
        _tensor(
            supervision.pair_positive_candidate_valid,
            dtype=torch.bool,
            ndim=1,
        ),
    )
    if any(
        item.shape != (batch_size,) or item.device != device
        for item in sample_bool_masks
    ):
        _fail()
    _, canonical_task_valid, target_condition_valid, positive_valid = (
        sample_bool_masks
    )

    component_valid = _tensor(
        supervision.pre_post_geometry_component_valid_mask,
        dtype=torch.bool,
        ndim=2,
    )
    component_loss = _tensor(
        supervision.pre_post_geometry_component_loss_mask,
        dtype=torch.bool,
        ndim=2,
    )
    geometry_targets = _tensor(
        supervision.pre_post_geometry_target_angstrom, ndim=2
    )
    if (
        component_valid.shape != (batch_size, 2)
        or component_loss.shape != (batch_size, 2)
        or geometry_targets.shape != (batch_size, 2)
        or not torch.is_floating_point(geometry_targets)
        or component_valid.device != device
        or component_loss.device != device
        or geometry_targets.device != device
    ):
        _fail()

    generation = _tensor(
        supervision.ligand_base_generation_mask,
        dtype=torch.bool,
        ndim=2,
    )
    fixed = _tensor(
        supervision.ligand_base_fixed_mask,
        dtype=torch.bool,
        ndim=2,
    )
    role_valid = _tensor(
        supervision.ligand_role_valid, dtype=torch.bool, ndim=1
    )
    role_id = _tensor(
        supervision.ligand_role_id, dtype=torch.long, ndim=1
    )
    if (
        generation.shape != (ligand_count, 1)
        or fixed.shape != (ligand_count, 1)
        or role_valid.shape != (ligand_count,)
        or role_id.shape != (ligand_count,)
        or generation.device != device
        or fixed.device != device
        or role_valid.device != device
        or role_id.device != device
        or bool((generation & fixed).any().item())
    ):
        _fail()

    ligand_batch = _tensor(ligand_batch_index, dtype=torch.long, ndim=1)
    pocket_batch = _tensor(pocket_batch_index, dtype=torch.long, ndim=1)
    if (
        ligand_batch.shape != (ligand_count,)
        or pocket_batch.shape != (pocket_count,)
        or ligand_batch.device != device
        or pocket_batch.device != device
        or (
            ligand_count
            and bool(
                ((ligand_batch < 0) | (ligand_batch >= batch_size))
                .any()
                .item()
            )
        )
        or (
            pocket_count
            and bool(
                ((pocket_batch < 0) | (pocket_batch >= batch_size))
                .any()
                .item()
            )
        )
    ):
        _fail()

    canonical_task_id = _tensor(
        supervision.canonical_task_id, dtype=torch.long, ndim=1
    )
    model_task_id = _tensor(
        model_output.canonical_task_id, dtype=torch.long, ndim=1
    )
    if (
        canonical_task_id.shape != (batch_size,)
        or model_task_id.shape != (batch_size,)
        or canonical_task_id.device != device
        or model_task_id.device != device
        or not torch.equal(canonical_task_id, model_task_id)
        or bool(
            (
                canonical_task_valid
                & ((canonical_task_id < 0) | (canonical_task_id > 4))
            )
            .any()
            .item()
        )
    ):
        _fail()

    offsets = _tensor(
        supervision.pair_candidate_offsets, dtype=torch.long, ndim=1
    )
    model_offsets = _tensor(
        model_output.pair_candidate_offsets, dtype=torch.long, ndim=1
    )
    positive_index = _tensor(
        supervision.pair_positive_candidate_index,
        dtype=torch.long,
        ndim=1,
    )
    target_pocket_flat = _tensor(
        supervision.target_residue_reactive_atom_flat_index,
        dtype=torch.long,
        ndim=1,
    )
    if (
        offsets.shape != (batch_size + 1,)
        or model_offsets.shape != offsets.shape
        or positive_index.shape != (batch_size,)
        or target_pocket_flat.shape != (batch_size,)
        or offsets.device != device
        or model_offsets.device != device
        or positive_index.device != device
        or target_pocket_flat.device != device
        or not torch.equal(offsets, model_offsets)
    ):
        _fail()
    if (
        int(offsets[0].item()) != 0
        or int(offsets[-1].item()) != candidate_count
        or bool((offsets[1:] < offsets[:-1]).any().item())
    ):
        _fail()

    candidate_field_names = (
        "pair_candidate_batch_index",
        "pair_candidate_ligand_local_index",
        "pair_candidate_residue_local_index",
        "pair_candidate_ligand_flat_index",
        "pair_candidate_pocket_flat_index",
    )
    candidate_fields: dict[str, torch.Tensor] = {}
    for field_name in candidate_field_names:
        supervision_value = _tensor(
            getattr(supervision, field_name), dtype=torch.long, ndim=1
        )
        model_value = _tensor(
            getattr(model_output, field_name), dtype=torch.long, ndim=1
        )
        if (
            supervision_value.shape != (candidate_count,)
            or model_value.shape != (candidate_count,)
            or supervision_value.device != device
            or model_value.device != device
            or not torch.equal(supervision_value, model_value)
        ):
            _fail()
        candidate_fields[field_name] = supervision_value
    candidate_is_positive = _tensor(
        supervision.pair_candidate_is_positive,
        dtype=torch.bool,
        ndim=1,
    )
    if (
        candidate_is_positive.shape != (candidate_count,)
        or candidate_is_positive.device != device
    ):
        _fail()

    endpoint_is_hidden = torch.zeros(
        batch_size, dtype=torch.bool, device=device
    )
    for sample in range(batch_size):
        if not bool(positive_valid[sample].item()):
            continue
        start = int(offsets[sample].item())
        end = int(offsets[sample + 1].item())
        candidate = int(positive_index[sample].item())
        if candidate < 0 or not start <= candidate < end:
            _fail()

        candidate_batch = int(
            candidate_fields["pair_candidate_batch_index"][candidate].item()
        )
        ligand_local = int(
            candidate_fields[
                "pair_candidate_ligand_local_index"
            ][candidate].item()
        )
        pocket_local = int(
            candidate_fields[
                "pair_candidate_residue_local_index"
            ][candidate].item()
        )
        ligand_flat = int(
            candidate_fields[
                "pair_candidate_ligand_flat_index"
            ][candidate].item()
        )
        pocket_flat = int(
            candidate_fields[
                "pair_candidate_pocket_flat_index"
            ][candidate].item()
        )
        ligand_nodes = torch.nonzero(
            ligand_batch == sample, as_tuple=False
        ).flatten()
        pocket_nodes = torch.nonzero(
            pocket_batch == sample, as_tuple=False
        ).flatten()
        if (
            not bool(candidate_is_positive[candidate].item())
            or candidate_batch != sample
            or ligand_local < 0
            or ligand_local >= len(ligand_nodes)
            or pocket_local < 0
            or pocket_local >= len(pocket_nodes)
            or ligand_flat < 0
            or ligand_flat >= ligand_count
            or pocket_flat < 0
            or pocket_flat >= pocket_count
            or int(ligand_nodes[ligand_local].item()) != ligand_flat
            or int(pocket_nodes[pocket_local].item()) != pocket_flat
            or int(ligand_batch[ligand_flat].item()) != sample
            or int(pocket_batch[pocket_flat].item()) != sample
            or pocket_flat != int(target_pocket_flat[sample].item())
            or not bool(role_valid[ligand_flat].item())
            or int(role_id[ligand_flat].item()) != 2
        ):
            _fail()
        endpoint_is_hidden[sample] = bool(
            generation[ligand_flat, 0].item()
            and not fixed[ligand_flat, 0].item()
        )

    effective = component_loss.clone()
    effective[:, _POST_GEOMETRY_COMPONENT_INDEX_V1] = (
        component_loss[:, _POST_GEOMETRY_COMPONENT_INDEX_V1]
        & component_valid[:, _POST_GEOMETRY_COMPONENT_INDEX_V1]
        & admitted
        & canonical_task_valid
        & target_condition_valid
        & positive_valid
        & endpoint_is_hidden
    )
    return effective


def compute_covapie_current11_training_losses_v1(
    *,
    model_output: CovapieCurrent11ModelOutputV1,
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1,
    diffusion_trace: object,
    loss_weights: CovapieCurrent11LossWeightsV1 | Mapping[str, float],
    pair_contrastive_temperature: float = 1.0,
    geometry_smooth_l1_beta: float = 1.0,
    post_geometry_loss_purpose: str = _EXISTING_COMPONENT_MASKS_PURPOSE_V1,
    ligand_batch_index: torch.Tensor | None = None,
    pocket_batch_index: torch.Tensor | None = None,
) -> CovapieCurrent11LossOutputV1:
    """Apply the exact per-sample reductions and graph-connected zero policy."""

    try:
        if (
            not isinstance(model_output, CovapieCurrent11ModelOutputV1)
            or not isinstance(
                supervision, CovapieCurrent11TrainingSupervisionTensorsV1
            )
            or type(pair_contrastive_temperature) is not float
            or pair_contrastive_temperature != 1.0
            or type(geometry_smooth_l1_beta) is not float
            or geometry_smooth_l1_beta != 1.0
            or type(post_geometry_loss_purpose) is not str
            or post_geometry_loss_purpose not in (
                _EXISTING_COMPONENT_MASKS_PURPOSE_V1,
                _INDEPENDENT_HIDDEN_POST_DISTANCE_PURPOSE_V1,
            )
        ):
            _fail()
        weights = _validated_weights(loss_weights)
        if (
            post_geometry_loss_purpose
            == _INDEPENDENT_HIDDEN_POST_DISTANCE_PURPOSE_V1
        ):
            effective_geometry_component_loss_mask = (
                _hidden_post_effective_component_loss_mask_v1(
                    model_output=model_output,
                    supervision=supervision,
                    ligand_batch_index=ligand_batch_index,
                    pocket_batch_index=pocket_batch_index,
                )
            )
        else:
            effective_geometry_component_loss_mask = (
                supervision.pre_post_geometry_component_loss_mask
            )
        base_per_sample = _tensor(
            getattr(diffusion_trace, "base_objective_per_sample", None),
            ndim=1,
        )
        admitted = supervision.sample_training_admitted
        if (
            admitted.dtype != torch.bool
            or admitted.ndim != 1
            or len(admitted) != len(base_per_sample)
            or not bool(admitted.any().item())
            or not bool(torch.isfinite(base_per_sample[admitted]).all().item())
        ):
            _fail()
        loss_base = base_per_sample[admitted].mean()

        logits = model_output.pair_logits
        geometry_predictions = (
            model_output.pre_post_geometry_predictions_angstrom
        )
        batch_size = len(admitted)
        pair_per_sample: list[torch.Tensor] = []
        pair_diagnostic = logits.new_full((batch_size,), float("nan"))
        pair_valid_count = 0
        for sample in range(batch_size):
            if not bool(supervision.pair_positive_candidate_valid[sample]):
                continue
            start = int(supervision.pair_candidate_offsets[sample].item())
            end = int(supervision.pair_candidate_offsets[sample + 1].item())
            positive_index = int(
                supervision.pair_positive_candidate_index[sample].item()
            )
            if (
                not start <= positive_index < end
                or not bool(
                    supervision.pair_head_candidate_loss_mask[
                        positive_index
                    ].item()
                )
                or not bool(
                    supervision.pair_candidate_is_positive[
                        positive_index
                    ].item()
                )
            ):
                _fail()
            positive_bce = F.binary_cross_entropy_with_logits(
                logits[positive_index], logits.new_ones(())
            )
            segment_indices = torch.arange(
                start, end, device=logits.device, dtype=torch.long
            )
            negative_mask = (
                supervision.pair_candidate_is_negative[start:end]
                & supervision.pair_head_candidate_loss_mask[start:end]
            )
            negative_indices = segment_indices[negative_mask]
            if len(negative_indices):
                negative_bce = F.binary_cross_entropy_with_logits(
                    logits[negative_indices],
                    torch.zeros_like(logits[negative_indices]),
                    reduction="mean",
                )
                sample_loss = 0.5 * positive_bce + 0.5 * negative_bce
            else:
                sample_loss = positive_bce
            pair_per_sample.append(sample_loss)
            pair_diagnostic[sample] = sample_loss.detach()
            pair_valid_count += 1
        loss_pair = (
            torch.stack(pair_per_sample).mean()
            if pair_per_sample
            else logits.sum() * 0.0
        )

        contrastive_per_sample: list[torch.Tensor] = []
        contrastive_diagnostic = logits.new_full(
            (batch_size,), float("nan")
        )
        contrastive_valid_count = 0
        for sample in range(batch_size):
            if not bool(
                supervision.pair_contrastive_sample_loss_mask[sample]
            ):
                continue
            start = int(supervision.pair_candidate_offsets[sample].item())
            end = int(supervision.pair_candidate_offsets[sample + 1].item())
            positive_index = int(
                supervision.pair_positive_candidate_index[sample].item()
            )
            segment_mask = supervision.pair_head_candidate_loss_mask[
                start:end
            ]
            if (
                not bool(segment_mask.all().item())
                or end - start < 2
                or not start <= positive_index < end
            ):
                _fail()
            positive_ordinal = positive_index - start
            sample_loss = -F.log_softmax(
                logits[start:end] / pair_contrastive_temperature,
                dim=0,
            )[positive_ordinal]
            contrastive_per_sample.append(sample_loss)
            contrastive_diagnostic[sample] = sample_loss.detach()
            contrastive_valid_count += 1
        loss_contrastive = (
            torch.stack(contrastive_per_sample).mean()
            if contrastive_per_sample
            else logits.sum() * 0.0
        )

        geometry_per_sample: list[torch.Tensor] = []
        geometry_diagnostic = logits.new_full(
            (batch_size,), float("nan")
        )
        geometry_valid_count = 0
        for sample in range(batch_size):
            component_mask = effective_geometry_component_loss_mask[sample]
            if not bool(component_mask.any().item()):
                continue
            if not bool(supervision.pair_positive_candidate_valid[sample]):
                _fail()
            positive_index = int(
                supervision.pair_positive_candidate_index[sample].item()
            )
            targets = supervision.pre_post_geometry_target_angstrom[
                sample, component_mask
            ]
            selected_predictions = geometry_predictions[
                positive_index, component_mask
            ]
            if (
                not bool(torch.isfinite(targets).all().item())
                or not bool(torch.isfinite(selected_predictions).all().item())
                or bool((targets < 0).any().item())
                or bool((selected_predictions < 0).any().item())
            ):
                _fail()
            component_losses = F.smooth_l1_loss(
                selected_predictions,
                targets,
                reduction="none",
                beta=geometry_smooth_l1_beta,
            )
            sample_loss = component_losses.mean()
            geometry_per_sample.append(sample_loss)
            geometry_diagnostic[sample] = sample_loss.detach()
            geometry_valid_count += 1
        loss_geometry = (
            torch.stack(geometry_per_sample).mean()
            if geometry_per_sample
            else geometry_predictions.reshape(-1)[:0].sum()
        )

        loss_total = (
            float(weights.base_diffusion) * loss_base
            + float(weights.covalent_pair_prediction) * loss_pair
            + float(weights.pre_post_geometry) * loss_geometry
            + float(weights.covalent_pair_contrastive) * loss_contrastive
        )
        return CovapieCurrent11LossOutputV1(
            loss_base_diffusion=loss_base,
            loss_covalent_pair_prediction=loss_pair,
            loss_pre_post_geometry=loss_geometry,
            loss_covalent_pair_contrastive=loss_contrastive,
            loss_total=loss_total,
            base_diffusion_valid_sample_count=int(admitted.sum().item()),
            covalent_pair_prediction_valid_sample_count=pair_valid_count,
            pre_post_geometry_valid_sample_count=geometry_valid_count,
            covalent_pair_contrastive_valid_sample_count=(
                contrastive_valid_count
            ),
            pair_prediction_per_sample_detached=pair_diagnostic.detach(),
            pre_post_geometry_per_sample_detached=(
                geometry_diagnostic.detach()
            ),
            pair_contrastive_per_sample_detached=(
                contrastive_diagnostic.detach()
            ),
        )
    except Exception as error:
        if type(error) is ValueError and str(error) == AUXILIARY_ERROR:
            raise
        raise ValueError(AUXILIARY_ERROR) from error
