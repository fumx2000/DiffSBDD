"""Functional five-mask DDPM bridge and additive Current11 Lightning owner V1."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import NoReturn

import torch
from torch import nn
from torch_scatter import scatter_add, scatter_mean

from equivariant_diffusion.conditional_model import ConditionalDDPM
from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (
    CovapieCurrent11AuxiliaryModelV1,
    CovapieCurrent11LossOutputV1,
    CovapieCurrent11LossWeightsV1,
    CovapieCurrent11ModelOutputV1,
    compute_covapie_current11_training_losses_v1,
)
from covalent_ext.covapie_current11_task2_lightning_module_v1 import (
    CovapieCurrent11Task2LigandPocketDDPM,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
    tensorize_covapie_current11_training_supervision_v1,
)


__all__ = (
    "CovapieCurrent11DiffusionForwardTraceV1",
    "CovapieCurrent11FunctionalDynamicsOutputV1",
    "CovapieCurrent11TrainingForwardOutputV1",
    "CovapieCurrent11TrainingLigandPocketDDPM",
    "run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1",
    "run_covapie_current11_functional_dynamics_with_hidden_v1",
)


BRIDGE_ERROR = (
    "COVAPIE_CURRENT11_FIVE_MASK_DIFFUSION_AND_HIDDEN_READOUT_V1_ERROR"
)
TRAINING_MODULE_ERROR = (
    "COVAPIE_CURRENT11_TRAINING_LIGHTNING_MODULE_V1_ERROR"
)
AUTHORITATIVE_SUPERVISION_BATCH_FIELD_V1 = (
    "covapie_current11_authoritative_training_supervision_v1"
)


@dataclass(frozen=True)
class CovapieCurrent11FunctionalDynamicsOutputV1:
    decoded_ligand_dynamics: torch.Tensor
    decoded_pocket_dynamics: torch.Tensor
    ligand_node_hidden: torch.Tensor
    pocket_node_hidden: torch.Tensor
    coordinate_update_mask: torch.Tensor


@dataclass(frozen=True)
class CovapieCurrent11DiffusionForwardTraceV1:
    diffusion_epsilon_prediction_ligand: torch.Tensor
    diffusion_epsilon_prediction_pocket: torch.Tensor
    diffusion_timestep_int: torch.Tensor
    noised_ligand_xh: torch.Tensor
    sampled_epsilon_ligand: torch.Tensor
    clean_centered_ligand_xh: torch.Tensor
    clean_centered_pocket_xh: torch.Tensor
    denoised_ligand_xh: torch.Tensor
    ligand_node_hidden: torch.Tensor
    pocket_node_hidden: torch.Tensor
    role_mask_anchor_hidden_delta: torch.Tensor
    ligand_coordinate_update_mask: torch.Tensor
    masked_t_gt_0_error_per_sample: torch.Tensor
    masked_t0_x_per_sample: torch.Tensor
    masked_t0_h_per_sample: torch.Tensor
    masked_kl_prior_per_sample: torch.Tensor
    base_objective_per_sample: torch.Tensor
    coordinate_normalization: float


@dataclass(frozen=True)
class CovapieCurrent11TrainingForwardOutputV1:
    model_output: CovapieCurrent11ModelOutputV1
    loss_output: CovapieCurrent11LossOutputV1
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1
    diffusion_trace: CovapieCurrent11DiffusionForwardTraceV1


class _BridgeInvariantError(Exception):
    pass


def _fail() -> NoReturn:
    raise _BridgeInvariantError()


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


def _copy_tensor_dictionary(value: object) -> dict[str, object]:
    if type(value) is not dict:
        _fail()
    return {
        key: item.clone() if isinstance(item, torch.Tensor) else item
        for key, item in value.items()
    }


def _validate_ddpm_v1(ddpm: object) -> None:
    dynamics = getattr(ddpm, "dynamics", None)
    if (
        type(ddpm) is not ConditionalDDPM
        or not isinstance(dynamics, nn.Module)
        or getattr(ddpm, "loss_type", None) != "l2"
        or getattr(ddpm, "vnode_idx", None) is not None
        or getattr(dynamics, "mode", None) != "egnn_dynamics"
        or getattr(dynamics, "update_pocket_coords", None) is not False
        or getattr(dynamics, "condition_time", None) is not True
        or getattr(dynamics, "target_residue_atom_conditioning", None)
        is not True
    ):
        _fail()


def run_covapie_current11_functional_dynamics_with_hidden_v1(
    *,
    ddpm: nn.Module,
    xh_atoms: torch.Tensor,
    xh_residues: torch.Tensor,
    t: torch.Tensor,
    mask_atoms: torch.Tensor,
    mask_residues: torch.Tensor,
    ligand_coordinate_update_mask: torch.Tensor,
    role_mask_anchor_hidden_delta: torch.Tensor,
    pocket_target_residue_atom_condition_indicator: torch.Tensor,
) -> CovapieCurrent11FunctionalDynamicsOutputV1:
    """Replay the owned EGNNDynamics modules and additionally expose hidden."""

    try:
        _validate_ddpm_v1(ddpm)
        dynamics = ddpm.dynamics
        xh_atoms = _tensor(xh_atoms, ndim=2)
        xh_residues = _tensor(xh_residues, ndim=2)
        t = _tensor(t, ndim=2)
        mask_atoms = _tensor(mask_atoms, dtype=torch.long, ndim=1)
        mask_residues = _tensor(mask_residues, dtype=torch.long, ndim=1)
        ligand_coordinate_update_mask = _tensor(
            ligand_coordinate_update_mask, dtype=torch.bool, ndim=2
        )
        role_delta = _tensor(role_mask_anchor_hidden_delta, ndim=2)
        indicator = _tensor(
            pocket_target_residue_atom_condition_indicator,
            dtype=torch.bool,
            ndim=1,
        )
        if (
            len(xh_atoms) != len(mask_atoms)
            or len(xh_residues) != len(mask_residues)
            or ligand_coordinate_update_mask.shape != (len(xh_atoms), 1)
            or len(role_delta) != len(xh_atoms)
            or len(indicator) != len(xh_residues)
            or xh_atoms.shape[1] != dynamics.n_dims + ddpm.atom_nf
            or xh_residues.shape[1] != dynamics.n_dims + ddpm.residue_nf
        ):
            _fail()

        x_atoms = xh_atoms[:, :dynamics.n_dims].clone()
        h_atoms = xh_atoms[:, dynamics.n_dims:].clone()
        x_residues = xh_residues[:, :dynamics.n_dims].clone()
        h_residues = xh_residues[:, dynamics.n_dims:].clone()

        h_atoms = dynamics.atom_encoder(h_atoms)
        if h_atoms.shape != role_delta.shape:
            _fail()
        h_atoms = h_atoms + role_delta.to(dtype=h_atoms.dtype)
        h_residues = dynamics.residue_encoder(h_residues)
        h_residues = h_residues + (
            indicator.to(dtype=h_residues.dtype).unsqueeze(1)
            * dynamics.target_residue_atom_condition_embedding.unsqueeze(0)
        )

        x = torch.cat((x_atoms, x_residues), dim=0)
        h = torch.cat((h_atoms, h_residues), dim=0)
        mask = torch.cat((mask_atoms, mask_residues), dim=0)
        if t.numel() == 1:
            h_time = torch.empty_like(h[:, 0:1]).fill_(t.item())
        else:
            if t.shape[1] != 1 or len(t) <= int(mask.max().item()):
                _fail()
            h_time = t[mask]
        h = torch.cat((h, h_time), dim=1)

        edges = dynamics.get_edges(
            mask_atoms, mask_residues, x_atoms, x_residues
        )
        if not bool((mask[edges[0]] == mask[edges[1]]).all().item()):
            _fail()
        if dynamics.edge_nf > 0:
            edge_types = torch.zeros(
                edges.size(1), dtype=torch.long, device=edges.device
            )
            edge_types[
                (edges[0] < len(mask_atoms))
                & (edges[1] < len(mask_atoms))
            ] = 1
            edge_types[
                (edges[0] >= len(mask_atoms))
                & (edges[1] >= len(mask_atoms))
            ] = 2
            edge_attributes = dynamics.edge_embedding(edge_types)
        else:
            edge_attributes = None

        update_coords_mask = torch.cat((
            ligand_coordinate_update_mask.to(dtype=mask_atoms.dtype),
            torch.zeros(
                (len(mask_residues), 1),
                dtype=mask_residues.dtype,
                device=mask_residues.device,
            ),
        ), dim=0)
        h_final, x_final = dynamics.egnn(
            h,
            x,
            edges,
            update_coords_mask=update_coords_mask,
            batch_mask=mask,
            edge_attr=edge_attributes,
        )
        velocity = x_final - x
        h_final = h_final[:, :-1]
        h_final_atoms = h_final[:len(mask_atoms)]
        h_final_residues = h_final[len(mask_atoms):]
        decoded_atoms = dynamics.atom_decoder(h_final_atoms)
        decoded_residues = dynamics.residue_decoder(h_final_residues)
        if bool(torch.isnan(velocity).any().item()):
            if dynamics.training:
                velocity = torch.where(
                    torch.isnan(velocity),
                    torch.zeros_like(velocity),
                    velocity,
                )
            else:
                _fail()
        return CovapieCurrent11FunctionalDynamicsOutputV1(
            decoded_ligand_dynamics=torch.cat((
                velocity[:len(mask_atoms)], decoded_atoms
            ), dim=1),
            decoded_pocket_dynamics=torch.cat((
                velocity[len(mask_atoms):], decoded_residues
            ), dim=1),
            ligand_node_hidden=h_final_atoms,
            pocket_node_hidden=h_final_residues,
            coordinate_update_mask=update_coords_mask,
        )
    except Exception as error:
        if type(error) is ValueError and str(error) == BRIDGE_ERROR:
            raise
        raise ValueError(BRIDGE_ERROR) from error


def _masked_t0_categorical_loss_v1(
    *,
    ddpm: nn.Module,
    ligand: dict[str, object],
    z_t_ligand: torch.Tensor,
    gamma_t: torch.Tensor,
    active_mask: torch.Tensor,
) -> torch.Tensor:
    z_h = z_t_ligand[:, ddpm.n_dims:]
    sigma_0 = ddpm.sigma(gamma_t, target_tensor=z_t_ligand)
    sigma_0_cat = sigma_0 * ddpm.norm_values[1]
    ligand_one_hot = (
        ligand["one_hot"] * ddpm.norm_values[1] + ddpm.norm_biases[1]
    )
    estimated_one_hot = z_h * ddpm.norm_values[1] + ddpm.norm_biases[1]
    centered_one_hot = estimated_one_hot - 1
    mask = ligand["mask"]
    log_proportional = torch.log(
        ddpm.cdf_standard_gaussian(
            (centered_one_hot + 0.5) / sigma_0_cat[mask]
        )
        - ddpm.cdf_standard_gaussian(
            (centered_one_hot - 0.5) / sigma_0_cat[mask]
        )
        + 1e-10
    )
    log_probabilities = log_proportional - torch.logsumexp(
        log_proportional, dim=1, keepdim=True
    )
    row_log_probability = (log_probabilities * ligand_one_hot).sum(dim=1)
    return -scatter_add(
        row_log_probability * active_mask.to(row_log_probability.dtype),
        mask,
        dim=0,
        dim_size=len(ligand["size"]),
    )


def _masked_kl_prior_v1(
    *,
    ddpm: nn.Module,
    clean_centered_ligand_xh: torch.Tensor,
    ligand_mask: torch.Tensor,
    active_mask: torch.Tensor,
    active_count: torch.Tensor,
    task_c_mask: torch.Tensor,
) -> torch.Tensor:
    batch_size = len(active_count)
    ones_batch = torch.ones(
        (batch_size, 1), device=clean_centered_ligand_xh.device
    )
    gamma_t = ddpm.gamma(ones_batch)
    alpha_t = ddpm.alpha(gamma_t, clean_centered_ligand_xh)
    mu_t = alpha_t[ligand_mask] * clean_centered_ligand_xh
    mu_x = mu_t[:, :ddpm.n_dims]
    mu_h = mu_t[:, ddpm.n_dims:]
    sigma_x = ddpm.sigma(gamma_t, mu_x).squeeze()
    sigma_h = ddpm.sigma(gamma_t, mu_h).squeeze()
    active_float = active_mask.to(mu_t.dtype)
    mu_norm_h = scatter_add(
        (mu_h.square().sum(dim=1) * active_float),
        ligand_mask,
        dim=0,
        dim_size=batch_size,
    )
    mu_norm_x = scatter_add(
        (mu_x.square().sum(dim=1) * active_float),
        ligand_mask,
        dim=0,
        dim_size=batch_size,
    )
    kl_h = ddpm.gaussian_KL(
        mu_norm_h, sigma_h, torch.ones_like(sigma_h), d=1
    )
    # Fixed ligand supplies the translation reference, so partial tasks use
    # ordinary independent coordinate dimensions rather than an all-generated
    # zero-COM subspace.
    coordinate_dimensions = torch.where(
        task_c_mask,
        (active_count - 1) * ddpm.n_dims,
        active_count * ddpm.n_dims,
    )
    kl_x = ddpm.gaussian_KL(
        mu_norm_x,
        sigma_x,
        torch.ones_like(sigma_x),
        d=coordinate_dimensions,
    )
    return kl_x + kl_h


def _run_bridge_impl(
    *,
    ddpm: nn.Module,
    ligand: object,
    pocket: object,
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1,
    role_mask_anchor_hidden_delta: torch.Tensor,
    pocket_target_residue_atom_condition_indicator: torch.Tensor | None,
) -> CovapieCurrent11DiffusionForwardTraceV1:
    _validate_ddpm_v1(ddpm)
    # V1 owns only the training objective.  Historical evaluation samples its
    # main timestep from 1..T, then performs a separate t=0 noise/dynamics
    # forward and composes a VLB/NLL with SNR, constant, Jacobian, and node
    # prior terms.  Reusing the training-style expression below in eval mode
    # would therefore be neither historical nor an authorized masked VLB.
    if ddpm.training is not True:
        _fail()
    if not isinstance(
        supervision, CovapieCurrent11TrainingSupervisionTensorsV1
    ):
        _fail()
    ligand_normalized = _copy_tensor_dictionary(ligand)
    pocket_normalized = _copy_tensor_dictionary(pocket)
    ligand_mask = _tensor(
        ligand_normalized.get("mask"), dtype=torch.long, ndim=1
    )
    pocket_mask = _tensor(
        pocket_normalized.get("mask"), dtype=torch.long, ndim=1
    )
    ligand_size = _tensor(
        ligand_normalized.get("size"), dtype=torch.long, ndim=1
    )
    pocket_size = _tensor(
        pocket_normalized.get("size"), dtype=torch.long, ndim=1
    )
    ligand_x = _tensor(ligand_normalized.get("x"), ndim=2)
    pocket_x = _tensor(pocket_normalized.get("x"), ndim=2)
    ligand_one_hot = _tensor(ligand_normalized.get("one_hot"), ndim=2)
    pocket_one_hot = _tensor(pocket_normalized.get("one_hot"), ndim=2)
    generation = _tensor(
        supervision.ligand_base_generation_mask,
        dtype=torch.bool,
        ndim=2,
    )
    fixed = _tensor(
        supervision.ligand_base_fixed_mask, dtype=torch.bool, ndim=2
    )
    active = _tensor(
        supervision.ligand_active_diffusion_loss_mask,
        dtype=torch.bool,
        ndim=2,
    )
    role_delta = _tensor(role_mask_anchor_hidden_delta, ndim=2)
    if (
        len(ligand_size) == 0
        or len(ligand_size) != len(pocket_size)
        or len(ligand_x) != len(ligand_mask)
        or len(pocket_x) != len(pocket_mask)
        or len(ligand_one_hot) != len(ligand_x)
        or len(pocket_one_hot) != len(pocket_x)
        or generation.shape != (len(ligand_x), 1)
        or fixed.shape != generation.shape
        or active.shape != generation.shape
        or role_delta.shape[0] != len(ligand_x)
        or not bool((generation ^ fixed).all().item())
        or not torch.equal(active, generation)
        or not bool(supervision.sample_training_admitted.all().item())
        or not bool(supervision.canonical_task_valid.all().item())
        or ligand_one_hot.shape[1] != ddpm.atom_nf
        or pocket_one_hot.shape[1] != ddpm.residue_nf
    ):
        _fail()
    batch_size = len(ligand_size)
    generated_by_task = torch.tensor(
        (
            (False, False, True),
            (False, True, True),
            (True, False, True),
            (True, False, False),
            (True, True, True),
        ),
        dtype=torch.bool,
        device=ligand_mask.device,
    )
    task_by_node = supervision.canonical_task_id[ligand_mask]
    role_by_node = supervision.ligand_role_id
    if (
        bool(((task_by_node < 0) | (task_by_node > 4)).any().item())
        or bool(((role_by_node < 0) | (role_by_node > 2)).any().item())
        or not torch.equal(
            generation[:, 0],
            generated_by_task[task_by_node, role_by_node],
        )
    ):
        _fail()
    for sample in range(batch_size):
        sample_ligand = ligand_mask == sample
        if (
            not bool(generation[:, 0][sample_ligand].any().item())
            or (
                int(supervision.canonical_task_id[sample].item()) != 4
                and not bool(fixed[:, 0][sample_ligand].any().item())
            )
        ):
            _fail()

    indicator = ddpm._resolve_covapie_target_residue_atom_condition_indicator_v1(
        pocket_normalized,
        pocket_target_residue_atom_condition_indicator,
    )
    if indicator is None:
        _fail()
    indicator = indicator.to(device=pocket_x.device)
    ligand_normalized, pocket_normalized = ddpm.normalize(
        ligand_normalized, pocket_normalized
    )
    xh0_ligand = torch.cat((
        ligand_normalized["x"], ligand_normalized["one_hot"]
    ), dim=1)
    xh0_pocket = torch.cat((
        pocket_normalized["x"], pocket_normalized["one_hot"]
    ), dim=1)

    generation_flat = generation[:, 0]
    fixed_flat = fixed[:, 0]
    task_c = supervision.canonical_task_id == 4
    full_task_c_batch = bool(task_c.all().item())
    if full_task_c_batch:
        xh0_ligand[:, :ddpm.n_dims], xh0_pocket[:, :ddpm.n_dims] = (
            ddpm.remove_mean_batch(
                xh0_ligand[:, :ddpm.n_dims],
                xh0_pocket[:, :ddpm.n_dims],
                ligand_mask,
                pocket_mask,
            )
        )
    else:
        reference = scatter_mean(
            xh0_ligand[:, :ddpm.n_dims][fixed_flat],
            ligand_mask[fixed_flat],
            dim=0,
            dim_size=batch_size,
        )
        if bool(task_c.any().item()):
            ligand_mean = scatter_mean(
                xh0_ligand[:, :ddpm.n_dims],
                ligand_mask,
                dim=0,
                dim_size=batch_size,
            )
            reference = torch.where(task_c.unsqueeze(1), ligand_mean, reference)
        xh0_ligand[:, :ddpm.n_dims] = (
            xh0_ligand[:, :ddpm.n_dims] - reference[ligand_mask]
        )
        xh0_pocket[:, :ddpm.n_dims] = (
            xh0_pocket[:, :ddpm.n_dims] - reference[pocket_mask]
        )

    t_int_float = torch.randint(
        0,
        ddpm.T + 1,
        size=(batch_size, 1),
        device=ligand_x.device,
    ).float()
    s_int = t_int_float - 1
    t_is_zero = (t_int_float == 0).float()
    t_is_not_zero = 1 - t_is_zero
    s = s_int / ddpm.T
    t = t_int_float / ddpm.T
    gamma_s = ddpm.inflate_batch_array(ddpm.gamma(s), ligand_x)
    gamma_t = ddpm.inflate_batch_array(ddpm.gamma(t), ligand_x)
    alpha_t = ddpm.alpha(gamma_t, xh0_ligand)
    sigma_t = ddpm.sigma(gamma_t, xh0_ligand)

    sampled_epsilon = ddpm.sample_gaussian(
        size=(len(ligand_mask), ddpm.n_dims + ddpm.atom_nf),
        device=ligand_mask.device,
    )
    epsilon_ligand = sampled_epsilon * generation.to(sampled_epsilon.dtype)
    z_generated = (
        alpha_t[ligand_mask] * xh0_ligand
        + sigma_t[ligand_mask] * epsilon_ligand
    )
    z_t_ligand = torch.where(generation, z_generated, xh0_ligand)
    clean_centered_pocket = xh0_pocket.clone()
    if full_task_c_batch:
        z_t_ligand[:, :ddpm.n_dims], clean_centered_pocket[:, :ddpm.n_dims] = (
            ddpm.remove_mean_batch(
                z_t_ligand[:, :ddpm.n_dims],
                clean_centered_pocket[:, :ddpm.n_dims],
                ligand_mask,
                pocket_mask,
            )
        )
    elif bool(task_c.any().item()):
        z_mean = scatter_mean(
            z_t_ligand[:, :ddpm.n_dims],
            ligand_mask,
            dim=0,
            dim_size=batch_size,
        )
        z_t_ligand[:, :ddpm.n_dims] = torch.where(
            task_c[ligand_mask].unsqueeze(1),
            z_t_ligand[:, :ddpm.n_dims] - z_mean[ligand_mask],
            z_t_ligand[:, :ddpm.n_dims],
        )
        clean_centered_pocket[:, :ddpm.n_dims] = torch.where(
            task_c[pocket_mask].unsqueeze(1),
            clean_centered_pocket[:, :ddpm.n_dims] - z_mean[pocket_mask],
            clean_centered_pocket[:, :ddpm.n_dims],
        )

    dynamics_output = run_covapie_current11_functional_dynamics_with_hidden_v1(
        ddpm=ddpm,
        xh_atoms=z_t_ligand,
        xh_residues=clean_centered_pocket,
        t=t,
        mask_atoms=ligand_mask,
        mask_residues=pocket_mask,
        ligand_coordinate_update_mask=generation,
        role_mask_anchor_hidden_delta=role_delta,
        pocket_target_residue_atom_condition_indicator=indicator,
    )
    net_out_ligand = dynamics_output.decoded_ligand_dynamics
    denoised_generated = ddpm.xh_given_zt_and_epsilon(
        z_t_ligand, net_out_ligand, gamma_t, ligand_mask
    )
    denoised_ligand = (
        denoised_generated
        if full_task_c_batch
        else torch.where(generation, denoised_generated, xh0_ligand)
    )

    squared_error = (epsilon_ligand - net_out_ligand).square()
    active_flat = active[:, 0]
    active_count = scatter_add(
        active_flat.long(),
        ligand_mask,
        dim=0,
        dim_size=batch_size,
    )
    if bool((active_count <= 0).any().item()):
        _fail()

    if full_task_c_batch:
        # This branch intentionally calls the historical helpers with the same
        # tensors and operation order.  It is the numerical parity anchor.
        error_t = ddpm.sum_except_batch(squared_error, ligand_mask)
        error_t = error_t * t_is_not_zero.squeeze()
        log_p_x, log_p_h = ddpm.log_pxh_given_z0_without_constants(
            ligand_normalized,
            z_t_ligand,
            epsilon_ligand,
            net_out_ligand,
            gamma_t,
        )
        loss_t0_x = -log_p_x * t_is_zero.squeeze()
        loss_t0_h = -log_p_h * t_is_zero.squeeze()
        kl_prior = ddpm.kl_prior(
            xh0_ligand, ligand_mask, ligand_size
        )
    else:
        row_error = squared_error.sum(dim=1) * active_flat.to(
            squared_error.dtype
        )
        error_t = scatter_add(
            row_error,
            ligand_mask,
            dim=0,
            dim_size=batch_size,
        ) * t_is_not_zero.squeeze()
        coordinate_error = (
            squared_error[:, :ddpm.n_dims].sum(dim=1)
            * active_flat.to(squared_error.dtype)
        )
        loss_t0_x = 0.5 * scatter_add(
            coordinate_error,
            ligand_mask,
            dim=0,
            dim_size=batch_size,
        ) * t_is_zero.squeeze()
        loss_t0_h = _masked_t0_categorical_loss_v1(
            ddpm=ddpm,
            ligand=ligand_normalized,
            z_t_ligand=z_t_ligand,
            gamma_t=gamma_t,
            active_mask=active_flat,
        ) * t_is_zero.squeeze()
        kl_prior = _masked_kl_prior_v1(
            ddpm=ddpm,
            clean_centered_ligand_xh=xh0_ligand,
            ligand_mask=ligand_mask,
            active_mask=active_flat,
            active_count=active_count,
            task_c_mask=task_c,
        )

    denominator_t = active_count.to(error_t.dtype) * (
        ddpm.n_dims + ddpm.atom_nf
    )
    denominator_t0_x = active_count.to(loss_t0_x.dtype) * ddpm.n_dims
    base_per_sample = (
        0.5 * error_t / denominator_t
        + loss_t0_x / denominator_t0_x
        + loss_t0_h
        + kl_prior
    )
    if not bool(torch.isfinite(base_per_sample).all().item()):
        _fail()
    normalization = ddpm.norm_values[0]
    if (
        type(normalization) not in (int, float)
        or type(normalization) is bool
        or not math.isfinite(float(normalization))
        or float(normalization) <= 0
    ):
        _fail()
    return CovapieCurrent11DiffusionForwardTraceV1(
        diffusion_epsilon_prediction_ligand=net_out_ligand,
        diffusion_epsilon_prediction_pocket=(
            dynamics_output.decoded_pocket_dynamics
        ),
        diffusion_timestep_int=t_int_float.squeeze(1).long(),
        noised_ligand_xh=z_t_ligand,
        sampled_epsilon_ligand=epsilon_ligand,
        clean_centered_ligand_xh=xh0_ligand,
        clean_centered_pocket_xh=clean_centered_pocket,
        denoised_ligand_xh=denoised_ligand,
        ligand_node_hidden=dynamics_output.ligand_node_hidden,
        pocket_node_hidden=dynamics_output.pocket_node_hidden,
        role_mask_anchor_hidden_delta=role_delta,
        ligand_coordinate_update_mask=generation,
        masked_t_gt_0_error_per_sample=error_t,
        masked_t0_x_per_sample=loss_t0_x,
        masked_t0_h_per_sample=loss_t0_h,
        masked_kl_prior_per_sample=kl_prior,
        base_objective_per_sample=base_per_sample,
        coordinate_normalization=float(normalization),
    )


def run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1(
    *,
    ddpm: nn.Module,
    ligand: object,
    pocket: object,
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1,
    role_mask_anchor_hidden_delta: torch.Tensor,
    pocket_target_residue_atom_condition_indicator: torch.Tensor | None = None,
) -> CovapieCurrent11DiffusionForwardTraceV1:
    """Run mask-aware perturbation, the owned EGNN, and exact base terms."""

    try:
        return _run_bridge_impl(
            ddpm=ddpm,
            ligand=ligand,
            pocket=pocket,
            supervision=supervision,
            role_mask_anchor_hidden_delta=role_mask_anchor_hidden_delta,
            pocket_target_residue_atom_condition_indicator=(
                pocket_target_residue_atom_condition_indicator
            ),
        )
    except Exception as error:
        if type(error) is ValueError and str(error) == BRIDGE_ERROR:
            raise
        raise ValueError(BRIDGE_ERROR) from error


class CovapieCurrent11TrainingLigandPocketDDPM(
    CovapieCurrent11Task2LigandPocketDDPM
):
    """Opt-in additive training owner; historical selectors remain untouched."""

    def __init__(
        self,
        *args: object,
        covapie_current11_training_enabled: bool = True,
        covapie_current11_task_schedule_seed: int = 0,
        covapie_current11_pair_contrastive_temperature: float = 1.0,
        covapie_current11_loss_weights: CovapieCurrent11LossWeightsV1
        | dict[str, float] | None = None,
        covapie_current11_authoritative_supervision_batch_field: str = (
            AUTHORITATIVE_SUPERVISION_BATCH_FIELD_V1
        ),
        **kwargs: object,
    ):
        if (
            type(covapie_current11_training_enabled) is not bool
            or covapie_current11_training_enabled is not True
            or type(covapie_current11_task_schedule_seed) is not int
            or not 0 <= covapie_current11_task_schedule_seed <= 2**63 - 1
            or type(covapie_current11_pair_contrastive_temperature) is not float
            or covapie_current11_pair_contrastive_temperature != 1.0
            or type(covapie_current11_authoritative_supervision_batch_field)
            is not str
            or not covapie_current11_authoritative_supervision_batch_field
        ):
            raise ValueError(TRAINING_MODULE_ERROR)
        super().__init__(*args, **kwargs)
        if (
            getattr(self, "covapie_current11_task2_runtime_enabled", None)
            is not True
            or self.mode != "pocket_conditioning"
            or self.loss_type != "l2"
            or self.pocket_representation != "full-atom"
            or self.virtual_nodes is not False
            or self.target_residue_atom_conditioning is not True
            or self.auxiliary_loss is not False
        ):
            raise ValueError(TRAINING_MODULE_ERROR)
        dynamics = self.ddpm.dynamics
        final_atom_encoder = dynamics.atom_encoder[-1]
        if not isinstance(final_atom_encoder, nn.Linear):
            raise ValueError(TRAINING_MODULE_ERROR)
        joint_nf = final_atom_encoder.out_features
        self.covapie_current11_auxiliary_model_v1 = (
            CovapieCurrent11AuxiliaryModelV1(joint_nf=joint_nf)
        )
        self.covapie_current11_training_enabled = True
        self.covapie_current11_task_schedule_seed = (
            covapie_current11_task_schedule_seed
        )
        self.covapie_current11_pair_contrastive_temperature = (
            covapie_current11_pair_contrastive_temperature
        )
        self.covapie_current11_authoritative_supervision_batch_field = (
            covapie_current11_authoritative_supervision_batch_field
        )
        if covapie_current11_loss_weights is None:
            self.covapie_current11_loss_weights = (
                CovapieCurrent11LossWeightsV1()
            )
        elif isinstance(
            covapie_current11_loss_weights, CovapieCurrent11LossWeightsV1
        ):
            self.covapie_current11_loss_weights = (
                covapie_current11_loss_weights
            )
        elif type(covapie_current11_loss_weights) is dict:
            try:
                self.covapie_current11_loss_weights = (
                    CovapieCurrent11LossWeightsV1(
                        **covapie_current11_loss_weights
                    )
                )
            except (TypeError, ValueError) as error:
                raise ValueError(TRAINING_MODULE_ERROR) from error
        else:
            raise ValueError(TRAINING_MODULE_ERROR)

    def forward(self, data: object) -> CovapieCurrent11TrainingForwardOutputV1:
        # The transport superclass remains train/validation/test capable, but
        # this additive model/loss bridge V1 intentionally has no evaluation
        # objective.  Never mutate mode or enter tensorization/model execution.
        if self.training is not True:
            raise ValueError(TRAINING_MODULE_ERROR)
        if type(data) is not dict:
            raise ValueError(TRAINING_MODULE_ERROR)
        try:
            ligand, pocket = self.get_ligand_and_pocket(data)
            runtime_result = data[
                "covapie_current11_task2_runtime_result_v1"
            ]
            authoritative_supervision = data[
                self.covapie_current11_authoritative_supervision_batch_field
            ]
            supervision = tensorize_covapie_current11_training_supervision_v1(
                batch=data,
                runtime_result=runtime_result,
                authoritative_supervision=authoritative_supervision,
                device=ligand["x"].device,
                epoch=int(self.current_epoch),
                task_schedule_seed=self.covapie_current11_task_schedule_seed,
            )
            canonical_indicator = _tensor(
                supervision.target_residue_reactive_atom_mask,
                dtype=torch.bool,
                ndim=2,
            )
            if canonical_indicator.shape != (len(pocket["x"]), 1):
                _fail()
            canonical_indicator = canonical_indicator[:, 0]
            role_delta = (
                self.covapie_current11_auxiliary_model_v1
                .encode_role_mask_anchor_v1(
                    supervision=supervision,
                    ligand_batch_index=ligand["mask"],
                )
            )
            trace = (
                run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1(
                    ddpm=self.ddpm,
                    ligand=ligand,
                    pocket=pocket,
                    supervision=supervision,
                    role_mask_anchor_hidden_delta=role_delta,
                    pocket_target_residue_atom_condition_indicator=(
                        canonical_indicator
                    ),
                )
            )
            model_output = self.covapie_current11_auxiliary_model_v1(
                diffusion_trace=trace,
                supervision=supervision,
                role_mask_anchor_hidden_delta=role_delta,
            )
            loss_output = compute_covapie_current11_training_losses_v1(
                model_output=model_output,
                supervision=supervision,
                diffusion_trace=trace,
                loss_weights=self.covapie_current11_loss_weights,
                pair_contrastive_temperature=(
                    self.covapie_current11_pair_contrastive_temperature
                ),
                geometry_smooth_l1_beta=1.0,
            )
            return CovapieCurrent11TrainingForwardOutputV1(
                model_output=model_output,
                loss_output=loss_output,
                supervision=supervision,
                diffusion_trace=trace,
            )
        except Exception as error:
            if type(error) is ValueError and str(error) == TRAINING_MODULE_ERROR:
                raise
            raise ValueError(TRAINING_MODULE_ERROR) from error

    def _shared_covapie_training_step_v1(
        self, data: object, *, split: str
    ) -> dict[str, torch.Tensor]:
        output = self.forward(data)
        losses = output.loss_output
        metrics = {
            "loss": losses.loss_total,
            "loss_base_diffusion": losses.loss_base_diffusion,
            "loss_covalent_pair_prediction": (
                losses.loss_covalent_pair_prediction
            ),
            "loss_pre_post_geometry": losses.loss_pre_post_geometry,
            "loss_covalent_pair_contrastive": (
                losses.loss_covalent_pair_contrastive
            ),
        }
        self.log_metrics(
            metrics,
            split,
            batch_size=len(output.supervision.sample_training_admitted),
            sync_dist=(split != "train"),
        )
        return metrics

    def training_step(self, data: object, *unused: object) -> dict[str, torch.Tensor]:
        del unused
        return self._shared_covapie_training_step_v1(data, split="train")

    def validation_step(self, data: object, *unused: object) -> dict[str, torch.Tensor]:
        del data, unused
        raise ValueError(TRAINING_MODULE_ERROR)

    def test_step(self, data: object, *unused: object) -> dict[str, torch.Tensor]:
        del data, unused
        raise ValueError(TRAINING_MODULE_ERROR)

    def configure_optimizers(self) -> torch.optim.Optimizer:
        # Match historical ownership exactly, including the registered frozen
        # predefined-schedule parameter, then append each new parameter once.
        parameters = (
            list(self.ddpm.parameters())
            + list(self.covapie_current11_auxiliary_model_v1.parameters())
        )
        parameter_ids = [id(parameter) for parameter in parameters]
        if len(parameter_ids) != len(set(parameter_ids)):
            raise ValueError(TRAINING_MODULE_ERROR)
        return torch.optim.AdamW(
            parameters,
            lr=self.lr,
            amsgrad=True,
            weight_decay=1e-12,
        )
