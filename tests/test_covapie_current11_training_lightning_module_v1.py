from __future__ import annotations

import copy
from argparse import Namespace
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch
from torch import nn
from Bio.PDB import Polypeptide as _polypeptide


if not hasattr(_polypeptide, "three_to_one"):
    _polypeptide.three_to_one = lambda name: (
        _polypeptide.protein_letters_3to1[name]
    )

import lightning_modules
from lightning_modules import LigandPocketDDPM
from equivariant_diffusion.conditional_model import ConditionalDDPM
from equivariant_diffusion.dynamics import EGNNDynamics
from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (
    CovapieCurrent11AuxiliaryModelV1,
    CovapieCurrent11LossWeightsV1,
    compute_covapie_current11_training_losses_v1,
)
from covalent_ext.covapie_current11_task2_lightning_module_v1 import (
    CovapieCurrent11Task2LigandPocketDDPM,
)
from covalent_ext.covapie_current11_training_lightning_module_v1 import (
    CovapieCurrent11TrainingLigandPocketDDPM,
    run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1,
    run_covapie_current11_functional_dynamics_with_hidden_v1,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT.parent / "covapie-state"
GENERATED_ROLES = {
    0: {2},
    1: {1, 2},
    2: {0, 2},
    3: {0},
    4: {0, 1, 2},
}


class _Params(SimpleNamespace):
    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)


def _ddpm() -> ConditionalDDPM:
    torch.manual_seed(11)
    dynamics = EGNNDynamics(
        atom_nf=10,
        residue_nf=10,
        n_dims=3,
        joint_nf=4,
        hidden_nf=8,
        device="cpu",
        act_fn=nn.SiLU(),
        n_layers=1,
        attention=False,
        tanh=False,
        norm_constant=1,
        inv_sublayers=1,
        sin_embedding=False,
        normalization_factor=1,
        aggregation_method="sum",
        edge_cutoff_ligand=None,
        edge_cutoff_pocket=None,
        edge_cutoff_interaction=None,
        update_pocket_coords=False,
        reflection_equivariant=True,
        edge_embedding_dim=None,
        target_residue_atom_conditioning=True,
    )
    ddpm = ConditionalDDPM(
        dynamics=dynamics,
        atom_nf=10,
        residue_nf=10,
        n_dims=3,
        timesteps=4,
        noise_schedule="polynomial_2",
        noise_precision=1e-4,
        loss_type="l2",
        norm_values=[1.0, 1.0],
        size_histogram=[[1] * 8 for _ in range(8)],
        virtual_node_idx=None,
    )
    ddpm.train()
    return ddpm


def _inputs(*, translation: torch.Tensor | None = None,
            rotation: torch.Tensor | None = None):
    ligand_x = torch.tensor([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [2.0, 0.0, 0.0],
    ])
    pocket_x = torch.tensor([
        [2.0, 0.0, 1.0],
        [3.0, 0.0, 0.0],
    ])
    if rotation is not None:
        ligand_x = ligand_x @ rotation.T
        pocket_x = pocket_x @ rotation.T
    if translation is not None:
        ligand_x = ligand_x + translation
        pocket_x = pocket_x + translation
    ligand = {
        "x": ligand_x,
        "one_hot": torch.eye(10)[torch.tensor([0, 1, 2])],
        "size": torch.tensor([3], dtype=torch.long),
        "mask": torch.tensor([0, 0, 0], dtype=torch.long),
    }
    pocket = {
        "x": pocket_x,
        "one_hot": torch.eye(10)[torch.tensor([3, 0])],
        "size": torch.tensor([2], dtype=torch.long),
        "mask": torch.tensor([0, 0], dtype=torch.long),
        "pocket_target_residue_atom_condition_indicator": torch.tensor(
            [True, False], dtype=torch.bool
        ),
    }
    return ligand, pocket


def _supervision(task_id: int, *, geometry: bool = False):
    generated = torch.tensor(
        [[role in GENERATED_ROLES[task_id]] for role in (0, 1, 2)],
        dtype=torch.bool,
    )
    nan = float("nan")
    return CovapieCurrent11TrainingSupervisionTensorsV1(
        sample_training_admitted=torch.tensor([True]),
        canonical_task_id=torch.tensor([task_id]),
        canonical_task_valid=torch.tensor([True]),
        ligand_role_id=torch.tensor([0, 1, 2]),
        ligand_role_valid=torch.tensor([True, True, True]),
        ligand_base_generation_mask=generated,
        ligand_base_fixed_mask=~generated,
        ligand_base_target_mask=generated.clone(),
        ligand_base_context_mask=(~generated).clone(),
        ligand_active_diffusion_loss_mask=generated.clone(),
        ligand_minimal_seed_or_anchor_mask=torch.tensor(
            [[task_id == 4], [False], [False]]
        ),
        ligand_minimal_seed_or_anchor_valid=torch.tensor([task_id == 4]),
        ligand_anchor_distance_angstrom=torch.tensor([[1.0], [2.0], [3.0]]),
        ligand_anchor_distance_valid=torch.tensor([[True], [True], [True]]),
        target_residue_membership_mask=torch.tensor([[True], [True]]),
        target_residue_reactive_atom_mask=torch.tensor([[True], [False]]),
        target_residue_reactive_atom_local_index=torch.tensor([0]),
        target_residue_reactive_atom_flat_index=torch.tensor([0]),
        target_residue_condition_valid=torch.tensor([True]),
        pair_candidate_offsets=torch.tensor([0, 6]),
        pair_candidate_batch_index=torch.tensor([0] * 6),
        pair_candidate_ligand_local_index=torch.tensor([0, 0, 1, 1, 2, 2]),
        pair_candidate_residue_local_index=torch.tensor([0, 1, 0, 1, 0, 1]),
        pair_candidate_ligand_flat_index=torch.tensor([0, 0, 1, 1, 2, 2]),
        pair_candidate_pocket_flat_index=torch.tensor([0, 1, 0, 1, 0, 1]),
        pair_candidate_is_positive=torch.tensor(
            [False, False, False, False, True, False]
        ),
        pair_candidate_is_negative=torch.tensor(
            [True, True, True, True, False, True]
        ),
        pair_positive_candidate_index=torch.tensor([4]),
        pair_positive_candidate_valid=torch.tensor([True]),
        pair_negative_count=torch.tensor([5]),
        pair_head_candidate_loss_mask=torch.tensor([True] * 6),
        pair_contrastive_sample_loss_mask=torch.tensor([True]),
        observed_complex_pair_distance_angstrom=torch.tensor([[1.0]]),
        observed_complex_pair_distance_valid=torch.tensor([[True]]),
        pre_post_geometry_target_angstrom=torch.tensor(
            [[2.0, nan]] if geometry else [[nan, nan]]
        ),
        pre_post_geometry_component_valid_mask=torch.tensor(
            [[True, False]] if geometry else [[False, False]]
        ),
        pre_post_geometry_component_loss_mask=torch.tensor(
            [[True, False]] if geometry else [[False, False]]
        ),
    )


def _mixed_inputs():
    ligand_0, pocket_0 = _inputs()
    ligand_1, pocket_1 = _inputs(translation=torch.tensor([8.0, 3.0, -4.0]))
    ligand = {
        "x": torch.cat((ligand_0["x"], ligand_1["x"]), dim=0),
        "one_hot": torch.cat((
            ligand_0["one_hot"], ligand_1["one_hot"]
        ), dim=0),
        "size": torch.tensor([3, 3], dtype=torch.long),
        "mask": torch.tensor([0, 0, 0, 1, 1, 1], dtype=torch.long),
    }
    pocket = {
        "x": torch.cat((pocket_0["x"], pocket_1["x"]), dim=0),
        "one_hot": torch.cat((
            pocket_0["one_hot"], pocket_1["one_hot"]
        ), dim=0),
        "size": torch.tensor([2, 2], dtype=torch.long),
        "mask": torch.tensor([0, 0, 1, 1], dtype=torch.long),
        "pocket_target_residue_atom_condition_indicator": torch.cat((
            pocket_0["pocket_target_residue_atom_condition_indicator"],
            pocket_1["pocket_target_residue_atom_condition_indicator"],
        )),
    }
    return ligand, pocket


def _mixed_task_c_and_b3_supervision():
    task_c = _supervision(4)
    task_b3 = _supervision(3)
    generation = torch.cat((
        task_c.ligand_base_generation_mask,
        task_b3.ligand_base_generation_mask,
    ))
    fixed = ~generation
    nan = float("nan")
    return replace(
        task_c,
        sample_training_admitted=torch.tensor([True, True]),
        canonical_task_id=torch.tensor([4, 3]),
        canonical_task_valid=torch.tensor([True, True]),
        ligand_role_id=torch.tensor([0, 1, 2, 0, 1, 2]),
        ligand_role_valid=torch.tensor([True] * 6),
        ligand_base_generation_mask=generation,
        ligand_base_fixed_mask=fixed,
        ligand_base_target_mask=generation.clone(),
        ligand_base_context_mask=fixed.clone(),
        ligand_active_diffusion_loss_mask=generation.clone(),
        ligand_minimal_seed_or_anchor_mask=torch.tensor([
            [True], [False], [False], [False], [False], [False]
        ]),
        ligand_minimal_seed_or_anchor_valid=torch.tensor([True, False]),
        ligand_anchor_distance_angstrom=torch.tensor([
            [1.0], [2.0], [3.0], [1.0], [2.0], [3.0]
        ]),
        ligand_anchor_distance_valid=torch.tensor([[True]] * 6),
        target_residue_membership_mask=torch.tensor([[True]] * 4),
        target_residue_reactive_atom_mask=torch.tensor([
            [True], [False], [True], [False]
        ]),
        target_residue_reactive_atom_local_index=torch.tensor([0, 0]),
        target_residue_reactive_atom_flat_index=torch.tensor([0, 2]),
        target_residue_condition_valid=torch.tensor([True, True]),
        pair_candidate_offsets=torch.tensor([0, 6, 12]),
        pair_candidate_batch_index=torch.tensor([0] * 6 + [1] * 6),
        pair_candidate_ligand_local_index=torch.tensor(
            [0, 0, 1, 1, 2, 2] * 2
        ),
        pair_candidate_residue_local_index=torch.tensor(
            [0, 1, 0, 1, 0, 1] * 2
        ),
        pair_candidate_ligand_flat_index=torch.tensor([
            0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5
        ]),
        pair_candidate_pocket_flat_index=torch.tensor([
            0, 1, 0, 1, 0, 1, 2, 3, 2, 3, 2, 3
        ]),
        pair_candidate_is_positive=torch.tensor(
            [False, False, False, False, True, False] * 2
        ),
        pair_candidate_is_negative=torch.tensor(
            [True, True, True, True, False, True] * 2
        ),
        pair_positive_candidate_index=torch.tensor([4, 10]),
        pair_positive_candidate_valid=torch.tensor([True, True]),
        pair_negative_count=torch.tensor([5, 5]),
        pair_head_candidate_loss_mask=torch.tensor([True] * 12),
        pair_contrastive_sample_loss_mask=torch.tensor([True, True]),
        observed_complex_pair_distance_angstrom=torch.tensor([[1.0], [1.0]]),
        observed_complex_pair_distance_valid=torch.tensor([[True], [True]]),
        pre_post_geometry_target_angstrom=torch.tensor([
            [nan, nan], [nan, nan]
        ]),
        pre_post_geometry_component_valid_mask=torch.tensor([
            [False, False], [False, False]
        ]),
        pre_post_geometry_component_loss_mask=torch.tensor([
            [False, False], [False, False]
        ]),
    )


@pytest.mark.parametrize("task_id", range(5))
def test_exact_five_mask_perturbation_update_and_loss_semantics(task_id: int) -> None:
    ddpm = _ddpm()
    ligand, pocket = _inputs()
    supervision = _supervision(task_id)
    torch.manual_seed(101)
    trace = run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1(
        ddpm=ddpm,
        ligand=ligand,
        pocket=pocket,
        supervision=supervision,
        role_mask_anchor_hidden_delta=torch.zeros(3, 4),
    )
    generated = supervision.ligand_base_generation_mask[:, 0]
    fixed = ~generated
    assert torch.equal(trace.ligand_coordinate_update_mask[:, 0], generated)
    assert torch.equal(trace.sampled_epsilon_ligand[fixed], torch.zeros_like(
        trace.sampled_epsilon_ligand[fixed]
    ))
    assert torch.count_nonzero(trace.sampled_epsilon_ligand[generated]) > 0
    assert torch.equal(
        trace.noised_ligand_xh[fixed],
        trace.clean_centered_ligand_xh[fixed],
    )
    assert torch.equal(
        trace.diffusion_epsilon_prediction_ligand[fixed, :3],
        torch.zeros_like(trace.diffusion_epsilon_prediction_ligand[fixed, :3]),
    )
    assert torch.equal(
        trace.diffusion_epsilon_prediction_pocket[:, :3],
        torch.zeros_like(trace.diffusion_epsilon_prediction_pocket[:, :3]),
    )
    assert trace.ligand_node_hidden.shape == (3, 4)
    assert trace.pocket_node_hidden.shape == (2, 4)
    assert trace.base_objective_per_sample.shape == (1,)
    assert torch.isfinite(trace.base_objective_per_sample).all()


def test_task_c_seed_is_orthogonal_to_generation_mask() -> None:
    supervision = _supervision(4)
    assert supervision.ligand_minimal_seed_or_anchor_mask.tolist() == [
        [True], [False], [False]
    ]
    assert supervision.ligand_base_generation_mask.all()
    assert not supervision.ligand_base_fixed_mask.any()
    assert supervision.ligand_active_diffusion_loss_mask.all()


def test_eval_allows_dynamics_helper_but_five_mask_objective_fails_closed() -> None:
    ddpm = _ddpm()
    ligand, pocket = _inputs()
    supervision = _supervision(4)
    ddpm.eval()

    # Hidden readout is objective-independent and remains usable in eval mode.
    functional = run_covapie_current11_functional_dynamics_with_hidden_v1(
        ddpm=ddpm,
        xh_atoms=torch.cat((ligand["x"], ligand["one_hot"]), dim=1),
        xh_residues=torch.cat((pocket["x"], pocket["one_hot"]), dim=1),
        t=torch.tensor([[0.5]]),
        mask_atoms=ligand["mask"],
        mask_residues=pocket["mask"],
        ligand_coordinate_update_mask=torch.ones((3, 1), dtype=torch.bool),
        role_mask_anchor_hidden_delta=torch.zeros((3, 4)),
        pocket_target_residue_atom_condition_indicator=(
            pocket["pocket_target_residue_atom_condition_indicator"]
        ),
    )
    assert functional.ligand_node_hidden.shape == (3, 4)

    # Historical eval needs a separate t=0 dynamics forward and VLB/NLL
    # composition.  V1 must reject eval instead of returning its training-style
    # loss with an impossible sampled t=0 branch.
    with pytest.raises(ValueError) as error:
        run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1(
            ddpm=ddpm,
            ligand=ligand,
            pocket=pocket,
            supervision=supervision,
            role_mask_anchor_hidden_delta=torch.zeros((3, 4)),
        )
    assert str(error.value) == (
        "COVAPIE_CURRENT11_FIVE_MASK_DIFFUSION_AND_HIDDEN_READOUT_V1_ERROR"
    )


def test_functional_dynamics_decoded_parity_and_hidden_equivariance() -> None:
    ddpm = _ddpm()
    with torch.no_grad():
        ddpm.dynamics.target_residue_atom_condition_embedding.copy_(
            torch.tensor([0.1, -0.2, 0.3, -0.4])
        )
    ligand, pocket = _inputs()
    xh_ligand = torch.cat((ligand["x"], ligand["one_hot"]), dim=1)
    xh_pocket = torch.cat((pocket["x"], pocket["one_hot"]), dim=1)
    t = torch.tensor([[0.5]])
    historical_ligand, historical_pocket = ddpm.dynamics(
        xh_ligand,
        xh_pocket,
        t,
        ligand["mask"],
        pocket["mask"],
        pocket_target_residue_atom_condition_indicator=(
            pocket["pocket_target_residue_atom_condition_indicator"]
        ),
    )
    functional = run_covapie_current11_functional_dynamics_with_hidden_v1(
        ddpm=ddpm,
        xh_atoms=xh_ligand,
        xh_residues=xh_pocket,
        t=t,
        mask_atoms=ligand["mask"],
        mask_residues=pocket["mask"],
        ligand_coordinate_update_mask=torch.ones((3, 1), dtype=torch.bool),
        role_mask_anchor_hidden_delta=torch.zeros((3, 4)),
        pocket_target_residue_atom_condition_indicator=(
            pocket["pocket_target_residue_atom_condition_indicator"]
        ),
    )
    assert torch.equal(functional.decoded_ligand_dynamics, historical_ligand)
    assert torch.equal(functional.decoded_pocket_dynamics, historical_pocket)

    rotation = torch.tensor([
        [0.0, -1.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0],
    ])
    translation = torch.tensor([7.0, -2.0, 5.0])
    transformed_ligand = xh_ligand.clone()
    transformed_pocket = xh_pocket.clone()
    transformed_ligand[:, :3] = xh_ligand[:, :3] @ rotation.T + translation
    transformed_pocket[:, :3] = xh_pocket[:, :3] @ rotation.T + translation
    transformed = run_covapie_current11_functional_dynamics_with_hidden_v1(
        ddpm=ddpm,
        xh_atoms=transformed_ligand,
        xh_residues=transformed_pocket,
        t=t,
        mask_atoms=ligand["mask"],
        mask_residues=pocket["mask"],
        ligand_coordinate_update_mask=torch.ones((3, 1), dtype=torch.bool),
        role_mask_anchor_hidden_delta=torch.zeros((3, 4)),
        pocket_target_residue_atom_condition_indicator=(
            pocket["pocket_target_residue_atom_condition_indicator"]
        ),
    )
    assert torch.allclose(
        functional.ligand_node_hidden,
        transformed.ligand_node_hidden,
        atol=1e-6,
        rtol=1e-6,
    )
    assert torch.allclose(
        functional.pocket_node_hidden,
        transformed.pocket_node_hidden,
        atol=1e-6,
        rtol=1e-6,
    )
    assert torch.allclose(
        functional.decoded_ligand_dynamics[:, :3] @ rotation.T,
        transformed.decoded_ligand_dynamics[:, :3],
        atol=1e-6,
        rtol=1e-6,
    )


@pytest.mark.parametrize("parity_seed", (0, 1))
def test_full_task_c_historical_base_objective_and_forward_trace_parity(
    monkeypatch: pytest.MonkeyPatch,
    parity_seed: int,
) -> None:
    ddpm = _ddpm()
    with torch.no_grad():
        ddpm.dynamics.target_residue_atom_condition_embedding.copy_(
            torch.tensor([0.2, -0.1, 0.05, 0.3])
        )
    supervision = _supervision(4)
    ligand, pocket = _inputs()
    captured: dict[str, torch.Tensor] = {}
    original_noised = ddpm.noised_representation

    def capture_noised(*args, **kwargs):
        result = original_noised(*args, **kwargs)
        captured["z_t_ligand"] = result[0].detach().clone()
        captured["xh_pocket"] = result[1].detach().clone()
        captured["epsilon"] = result[2].detach().clone()
        return result

    monkeypatch.setattr(ddpm, "noised_representation", capture_noised)
    def capture_dynamics(_module, _inputs, output):
        captured["decoded_ligand"] = output[0].detach().clone()
        captured["decoded_pocket"] = output[1].detach().clone()

    hook = ddpm.dynamics.register_forward_hook(capture_dynamics)
    historical_ligand = {key: value.clone() for key, value in ligand.items()}
    historical_pocket = {key: value.clone() for key, value in pocket.items()}
    torch.manual_seed(parity_seed)
    rng_state = torch.random.get_rng_state()
    historical = ddpm(historical_ligand, historical_pocket, return_info=True)
    hook.remove()
    (
        _, error_t_ligand, _, _, loss_t0_x, _, loss_t0_h, _, kl_prior,
        _, historical_t, historical_xh_hat, _,
    ) = historical
    denominator = (3 + ddpm.atom_nf) * ligand["size"]
    historical_nll = (
        0.5 * error_t_ligand / denominator
        + loss_t0_x / (3 * ligand["size"])
        + loss_t0_h
        + kl_prior
    )

    torch.random.set_rng_state(rng_state)
    trace = run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1(
        ddpm=ddpm,
        ligand=ligand,
        pocket=pocket,
        supervision=supervision,
        role_mask_anchor_hidden_delta=torch.zeros((3, 4)),
    )
    assert torch.equal(trace.diffusion_timestep_int, historical_t.long().view(-1))
    assert torch.equal(trace.noised_ligand_xh, captured["z_t_ligand"])
    assert torch.equal(trace.clean_centered_pocket_xh, captured["xh_pocket"])
    assert torch.equal(trace.sampled_epsilon_ligand, captured["epsilon"])
    assert torch.equal(
        trace.diffusion_epsilon_prediction_ligand,
        captured["decoded_ligand"],
    )
    assert torch.equal(
        trace.diffusion_epsilon_prediction_pocket,
        captured["decoded_pocket"],
    )
    assert torch.equal(trace.denoised_ligand_xh, historical_xh_hat)
    assert torch.equal(trace.masked_t_gt_0_error_per_sample, error_t_ligand)
    assert torch.equal(trace.masked_t0_x_per_sample, loss_t0_x.view(-1))
    assert torch.equal(trace.masked_t0_h_per_sample, loss_t0_h.view(-1))
    assert torch.equal(trace.masked_kl_prior_per_sample, kl_prior.view(-1))
    assert torch.equal(trace.base_objective_per_sample, historical_nll.view(-1))
    assert (
        (trace.base_objective_per_sample - historical_nll.view(-1))
        .abs().max().item()
        == 0.0
    )


@pytest.mark.parametrize("forced_timestep", (0, 2))
def test_mixed_batch_task_c_matches_single_historical_training_semantics(
    monkeypatch: pytest.MonkeyPatch,
    forced_timestep: int,
) -> None:
    ddpm = _ddpm()
    single_ligand, single_pocket = _inputs()
    mixed_ligand, mixed_pocket = _mixed_inputs()
    supervision = _mixed_task_c_and_b3_supervision()
    captured: dict[str, torch.Tensor] = {}
    kl_dimensions: list[torch.Tensor] = []

    original_noised = ddpm.noised_representation
    original_gaussian_kl = ddpm.gaussian_KL

    def capture_noised(*args, **kwargs):
        captured["clean_ligand"] = args[0].detach().clone()
        result = original_noised(*args, **kwargs)
        captured["noised_ligand"] = result[0].detach().clone()
        captured["centered_pocket"] = result[1].detach().clone()
        captured["epsilon"] = result[2].detach().clone()
        return result

    def capture_gaussian_kl(*args, **kwargs):
        dimension = args[3] if len(args) == 4 else kwargs["d"]
        kl_dimensions.append(torch.as_tensor(dimension).detach().clone())
        return original_gaussian_kl(*args, **kwargs)

    def deterministic_randint(low, high, size, *, device=None, **unused):
        del unused
        assert low <= forced_timestep < high
        return torch.full(size, forced_timestep, device=device, dtype=torch.long)

    def deterministic_gaussian(*, size, device):
        values = torch.arange(
            size[0] * size[1], device=device, dtype=torch.float32
        )
        return values.reshape(size).div(37.0).sub(0.5)

    monkeypatch.setattr(ddpm, "noised_representation", capture_noised)
    monkeypatch.setattr(ddpm, "gaussian_KL", capture_gaussian_kl)
    monkeypatch.setattr(ddpm, "sample_gaussian", deterministic_gaussian)
    monkeypatch.setattr(torch, "randint", deterministic_randint)

    historical = ddpm(
        {key: value.clone() for key, value in single_ligand.items()},
        {key: value.clone() for key, value in single_pocket.items()},
        return_info=True,
    )
    (
        _, historical_error_t, _, _, historical_t0_x, _, historical_t0_h,
        _, historical_kl, _, historical_t, _, _,
    ) = historical
    historical_base = (
        0.5 * historical_error_t / ((3 + ddpm.atom_nf) * 3)
        + historical_t0_x / (3 * 3)
        + historical_t0_h
        + historical_kl
    )
    historical_kl_dimensions = tuple(kl_dimensions)
    kl_dimensions.clear()

    trace = run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1(
        ddpm=ddpm,
        ligand=mixed_ligand,
        pocket=mixed_pocket,
        supervision=supervision,
        role_mask_anchor_hidden_delta=torch.zeros((6, 4)),
    )

    assert int(historical_t.item()) == forced_timestep
    assert trace.diffusion_timestep_int.tolist() == [
        forced_timestep, forced_timestep
    ]
    assert torch.equal(
        trace.clean_centered_ligand_xh[:3], captured["clean_ligand"]
    )
    assert torch.equal(
        trace.noised_ligand_xh[:3], captured["noised_ligand"]
    )
    assert torch.equal(
        trace.clean_centered_pocket_xh[:2], captured["centered_pocket"]
    )
    assert torch.equal(
        trace.sampled_epsilon_ligand[:3], captured["epsilon"]
    )
    assert torch.allclose(
        trace.noised_ligand_xh[:3, :3].mean(dim=0),
        torch.zeros(3),
        atol=3e-8,
        rtol=0,
    )
    assert trace.ligand_coordinate_update_mask[:3].all()
    assert supervision.ligand_active_diffusion_loss_mask[:3].all()
    assert torch.equal(
        trace.masked_t_gt_0_error_per_sample[:1], historical_error_t.view(-1)
    )
    assert torch.equal(
        trace.masked_t0_x_per_sample[:1], historical_t0_x.view(-1)
    )
    assert torch.equal(
        trace.masked_t0_h_per_sample[:1], historical_t0_h.view(-1)
    )
    assert torch.equal(
        trace.masked_kl_prior_per_sample[:1], historical_kl.view(-1)
    )
    assert torch.equal(
        trace.base_objective_per_sample[:1], historical_base.view(-1)
    )
    assert any(
        dimension.numel() == 1 and int(dimension.item()) == (3 - 1) * 3
        for dimension in historical_kl_dimensions
    )
    mixed_coordinate_dimensions = [
        dimension for dimension in kl_dimensions if dimension.numel() == 2
    ]
    assert len(mixed_coordinate_dimensions) == 1
    assert torch.equal(
        mixed_coordinate_dimensions[0], torch.tensor([6, 3])
    )


def test_synthetic_cpu_gradient_paths_reach_existing_ddpm_and_new_parameters() -> None:
    ddpm = _ddpm()
    ligand, pocket = _inputs()
    supervision = _supervision(4, geometry=True)
    auxiliary = CovapieCurrent11AuxiliaryModelV1(joint_nf=4)
    ligand_batch = ligand["mask"]
    role_delta = auxiliary.encode_role_mask_anchor_v1(
        supervision=supervision,
        ligand_batch_index=ligand_batch,
    )
    torch.manual_seed(71)
    trace = run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1(
        ddpm=ddpm,
        ligand=ligand,
        pocket=pocket,
        supervision=supervision,
        role_mask_anchor_hidden_delta=role_delta,
    )
    output = auxiliary(
        diffusion_trace=trace,
        supervision=supervision,
        role_mask_anchor_hidden_delta=role_delta,
    )
    losses = compute_covapie_current11_training_losses_v1(
        model_output=output,
        supervision=supervision,
        diffusion_trace=trace,
        loss_weights=CovapieCurrent11LossWeightsV1(pre_post_geometry=1.0),
    )
    pair_to_existing_gradient = torch.autograd.grad(
        losses.loss_covalent_pair_prediction,
        ddpm.dynamics.egnn.embedding.weight,
        retain_graph=True,
    )[0]
    assert torch.isfinite(pair_to_existing_gradient).all()
    assert torch.count_nonzero(pair_to_existing_gradient) > 0
    parameters = (
        ddpm.dynamics.atom_encoder[0].weight,
        auxiliary.role_embedding.weight,
        auxiliary.task_embedding.weight,
        auxiliary.generation_state_embedding.weight,
        auxiliary.seed_indicator_embedding.weight,
        auxiliary.anchor_distance_encoder[-1].weight,
        auxiliary.pair_logit.weight,
        auxiliary.pre_post_geometry_head[-1].weight,
    )
    gradients = torch.autograd.grad(
        losses.loss_total, parameters, allow_unused=True
    )
    assert all(gradient is not None for gradient in gradients)
    assert all(torch.isfinite(gradient).all() for gradient in gradients)


def _constructor_kwargs() -> dict[str, object]:
    return {
        "outdir": Path("/tmp/covapie-test-output"),
        "dataset": "crossdock",
        "datadir": "/tmp/covapie-test-data",
        "batch_size": 1,
        "lr": 1e-3,
        "egnn_params": _Params(
            joint_nf=4,
            device="cpu",
            hidden_nf=8,
            n_layers=1,
            attention=False,
            tanh=False,
            norm_constant=1,
            inv_sublayers=1,
            sin_embedding=False,
            normalization_factor=1,
            aggregation_method="sum",
            edge_cutoff_ligand=None,
            edge_cutoff_pocket=None,
            edge_cutoff_interaction=None,
            reflection_equivariant=True,
            edge_embedding_dim=None,
        ),
        "diffusion_params": _Params(
            diffusion_loss_type="l2",
            diffusion_steps=4,
            diffusion_noise_schedule="polynomial_2",
            diffusion_noise_precision=1e-4,
            normalize_factors=[1.0, 1.0],
        ),
        "num_workers": 0,
        "augment_noise": 0,
        "augment_rotation": False,
        "clip_grad": False,
        "eval_epochs": 1,
        "eval_params": _Params(eval_batch_size=1, smiles_file=None),
        "visualize_sample_epoch": 1,
        "visualize_chain_epoch": 1,
        "auxiliary_loss": False,
        "loss_params": _Params(),
        "mode": "pocket_conditioning",
        "node_histogram": [[1] * 8 for _ in range(8)],
        "pocket_representation": "full-atom",
        "virtual_nodes": False,
        "target_residue_atom_conditioning": True,
    }


def _patch_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        lightning_modules, "BasicMolecularMetrics", lambda *args: object()
    )
    monkeypatch.setattr(
        lightning_modules, "MoleculeProperties", lambda: object()
    )
    monkeypatch.setattr(
        lightning_modules, "CategoricalDistribution", lambda *args: object()
    )


def _training_model(
    monkeypatch: pytest.MonkeyPatch,
) -> CovapieCurrent11TrainingLigandPocketDDPM:
    _patch_metrics(monkeypatch)
    return CovapieCurrent11TrainingLigandPocketDDPM(
        **_constructor_kwargs(),
        covapie_current11_task2_runtime_enabled=True,
        covapie_repository_root=str(ROOT),
        covapie_state_root=str(STATE),
    )


def test_training_class_forward_eval_fails_before_transport_or_tensorizer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _training_model(monkeypatch)
    transport_call_count = 0

    def forbidden_transport(*unused):
        nonlocal transport_call_count
        del unused
        transport_call_count += 1
        raise AssertionError("eval forward entered transport")

    monkeypatch.setattr(model, "get_ligand_and_pocket", forbidden_transport)
    model.eval()
    with pytest.raises(ValueError) as error:
        model.forward({})
    assert str(error.value) == (
        "COVAPIE_CURRENT11_TRAINING_LIGHTNING_MODULE_V1_ERROR"
    )
    assert transport_call_count == 0
    assert model.training is False
    assert model.ddpm.training is False


@pytest.mark.parametrize("step_name", ("validation_step", "test_step"))
def test_unsupported_evaluation_steps_fail_before_forward(
    monkeypatch: pytest.MonkeyPatch,
    step_name: str,
) -> None:
    model = _training_model(monkeypatch)
    forward_call_count = 0

    def forbidden_forward(*unused):
        nonlocal forward_call_count
        del unused
        forward_call_count += 1
        raise AssertionError("unsupported evaluation step called forward")

    monkeypatch.setattr(model, "forward", forbidden_forward)
    with pytest.raises(ValueError) as error:
        getattr(model, step_name)({})
    assert str(error.value) == (
        "COVAPIE_CURRENT11_TRAINING_LIGHTNING_MODULE_V1_ERROR"
    )
    assert forward_call_count == 0


def test_additive_class_state_keys_and_parameter_ownership(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_metrics(monkeypatch)
    kwargs = _constructor_kwargs()
    torch.manual_seed(1)
    historical = LigandPocketDDPM(**kwargs)
    torch.manual_seed(1)
    task2 = CovapieCurrent11Task2LigandPocketDDPM(
        **kwargs,
        covapie_current11_task2_runtime_enabled=True,
        covapie_repository_root=str(ROOT),
        covapie_state_root=str(STATE),
    )
    torch.manual_seed(1)
    training = CovapieCurrent11TrainingLigandPocketDDPM(
        **kwargs,
        covapie_current11_task2_runtime_enabled=True,
        covapie_repository_root=str(ROOT),
        covapie_state_root=str(STATE),
    )
    historical_keys = set(historical.state_dict())
    task2_keys = set(task2.state_dict())
    training_keys = set(training.state_dict())
    assert historical_keys == task2_keys
    assert historical_keys <= training_keys
    new_keys = training_keys - historical_keys
    assert new_keys
    assert all(
        key.startswith("covapie_current11_auxiliary_model_v1.")
        for key in new_keys
    )
    assert {key for key in training_keys if key.startswith("ddpm.")} == {
        key for key in historical_keys if key.startswith("ddpm.")
    }
    parameter_ids = [id(parameter) for parameter in training.parameters()]
    assert len(parameter_ids) == len(set(parameter_ids))
    optimizer = training.configure_optimizers()
    optimizer_ids = [
        id(parameter)
        for group in optimizer.param_groups
        for parameter in group["params"]
    ]
    assert len(optimizer_ids) == len(set(optimizer_ids))
    assert set(optimizer_ids) == set(parameter_ids)
    assert LigandPocketDDPM.forward.__module__ == "lightning_modules"
    assert (
        CovapieCurrent11Task2LigandPocketDDPM.forward
        is LigandPocketDDPM.forward
    )
