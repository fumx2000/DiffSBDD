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
            if (
                len(role_id) != len(ligand_batch_index)
                or len(role_valid) != len(role_id)
                or ligand_batch_index.device != role_id.device
                or role_id.device != self.role_embedding.weight.device
            ):
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

            generation_state = supervision.ligand_base_generation_mask[
                :, 0
            ].long()
            if generation_state.shape != role_id.shape:
                _fail()
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

            anchor_valid = supervision.ligand_anchor_distance_valid[:, 0]
            if bool(anchor_valid.any().item()):
                distance = supervision.ligand_anchor_distance_angstrom[
                    anchor_valid
                ]
                if (
                    not bool(torch.isfinite(distance).all().item())
                    or bool((distance < 0).any().item())
                ):
                    _fail()
                anchor_delta = torch.zeros_like(delta)
                encoded = self.anchor_distance_encoder(torch.log1p(distance))
                anchor_delta = _assign_rows(
                    anchor_delta, anchor_valid, encoded
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


def compute_covapie_current11_training_losses_v1(
    *,
    model_output: CovapieCurrent11ModelOutputV1,
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1,
    diffusion_trace: object,
    loss_weights: CovapieCurrent11LossWeightsV1 | Mapping[str, float],
    pair_contrastive_temperature: float = 1.0,
    geometry_smooth_l1_beta: float = 1.0,
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
        ):
            _fail()
        weights = _validated_weights(loss_weights)
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
            component_mask = (
                supervision.pre_post_geometry_component_loss_mask[sample]
            )
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
            if not bool(torch.isfinite(targets).all().item()):
                _fail()
            component_losses = F.smooth_l1_loss(
                geometry_predictions[positive_index, component_mask],
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
            else geometry_predictions.sum() * 0.0
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
