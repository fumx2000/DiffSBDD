from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest
import torch
import torch.nn.functional as F

from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (
    AUXILIARY_ERROR,
    CovapieCurrent11AuxiliaryModelV1,
    CovapieCurrent11LossWeightsV1,
    compute_covapie_current11_training_losses_v1,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


def _supervision(*, geometry: bool = False):
    nan = float("nan")
    geometry_targets = torch.tensor(
        [[2.0, nan], [nan, nan]] if geometry else [[nan, nan], [nan, nan]],
        dtype=torch.float32,
    )
    geometry_valid = torch.tensor(
        [[True, False], [False, False]]
        if geometry else [[False, False], [False, False]],
        dtype=torch.bool,
    )
    return CovapieCurrent11TrainingSupervisionTensorsV1(
        sample_training_admitted=torch.tensor([True, True]),
        canonical_task_id=torch.tensor([4, 3], dtype=torch.long),
        canonical_task_valid=torch.tensor([True, True]),
        ligand_role_id=torch.tensor([0, 1, 2, 0, 1, 2]),
        ligand_role_valid=torch.tensor([True] * 6),
        ligand_base_generation_mask=torch.tensor(
            [[True], [True], [True], [True], [False], [False]]
        ),
        ligand_base_fixed_mask=torch.tensor(
            [[False], [False], [False], [False], [True], [True]]
        ),
        ligand_base_target_mask=torch.tensor(
            [[True], [True], [True], [True], [False], [False]]
        ),
        ligand_base_context_mask=torch.tensor(
            [[False], [False], [False], [False], [True], [True]]
        ),
        ligand_active_diffusion_loss_mask=torch.tensor(
            [[True], [True], [True], [True], [False], [False]]
        ),
        ligand_minimal_seed_or_anchor_mask=torch.tensor(
            [[True], [False], [False], [False], [False], [False]]
        ),
        ligand_minimal_seed_or_anchor_valid=torch.tensor([True, False]),
        ligand_anchor_distance_angstrom=torch.tensor(
            [[1.0], [2.0], [3.0], [1.0], [2.0], [3.0]]
        ),
        ligand_anchor_distance_valid=torch.tensor([[True]] * 6),
        target_residue_membership_mask=torch.tensor([[True]] * 4),
        target_residue_reactive_atom_mask=torch.tensor(
            [[True], [False], [True], [False]]
        ),
        target_residue_reactive_atom_local_index=torch.tensor([0, 0]),
        target_residue_reactive_atom_flat_index=torch.tensor([0, 2]),
        target_residue_condition_valid=torch.tensor([True, True]),
        pair_candidate_offsets=torch.tensor([0, 6, 12]),
        pair_candidate_batch_index=torch.tensor([0] * 6 + [1] * 6),
        pair_candidate_ligand_local_index=torch.tensor(
            [0, 0, 1, 1, 2, 2, 0, 0, 1, 1, 2, 2]
        ),
        pair_candidate_residue_local_index=torch.tensor(
            [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
        ),
        pair_candidate_ligand_flat_index=torch.tensor(
            [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5]
        ),
        pair_candidate_pocket_flat_index=torch.tensor(
            [0, 1, 0, 1, 0, 1, 2, 3, 2, 3, 2, 3]
        ),
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
        pre_post_geometry_target_angstrom=geometry_targets,
        pre_post_geometry_component_valid_mask=geometry_valid,
        pre_post_geometry_component_loss_mask=geometry_valid.clone(),
    )


def _trace(
    *,
    ligand_hidden: torch.Tensor,
    pocket_hidden: torch.Tensor,
    base: torch.Tensor | None = None,
):
    return SimpleNamespace(
        ligand_node_hidden=ligand_hidden,
        pocket_node_hidden=pocket_hidden,
        diffusion_epsilon_prediction_ligand=torch.randn(6, 13),
        denoised_ligand_xh=torch.cat((
            torch.tensor([
                [0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0],
                [0.0, 1.0, 0.0], [1.0, 1.0, 0.0], [2.0, 1.0, 0.0],
            ]),
            torch.zeros(6, 10),
        ), dim=1),
        clean_centered_pocket_xh=torch.cat((
            torch.tensor([
                [2.0, 0.0, 1.0], [3.0, 0.0, 0.0],
                [2.0, 1.0, 1.0], [3.0, 1.0, 0.0],
            ]),
            torch.zeros(4, 10),
        ), dim=1),
        diffusion_timestep_int=torch.tensor([1, 2]),
        coordinate_normalization=1.0,
        base_objective_per_sample=(
            torch.tensor([0.5, 1.5]) if base is None else base
        ),
    )


def _model_output(*, geometry: bool = False):
    torch.manual_seed(3)
    supervision = _supervision(geometry=geometry)
    auxiliary = CovapieCurrent11AuxiliaryModelV1(joint_nf=4)
    ligand_batch = torch.tensor([0, 0, 0, 1, 1, 1])
    delta = auxiliary.encode_role_mask_anchor_v1(
        supervision=supervision, ligand_batch_index=ligand_batch
    )
    trace = _trace(
        ligand_hidden=torch.randn(6, 4),
        pocket_hidden=torch.randn(4, 4),
    )
    output = auxiliary(
        diffusion_trace=trace,
        supervision=supervision,
        role_mask_anchor_hidden_delta=delta,
    )
    return auxiliary, supervision, trace, delta, output


def test_shapes_dtypes_zero_initial_delta_and_geometry_nonnegative() -> None:
    auxiliary, supervision, trace, delta, output = _model_output()
    del auxiliary, supervision, trace
    assert delta.shape == (6, 4)
    assert torch.equal(delta, torch.zeros_like(delta))
    assert output.ligand_node_hidden.shape == (6, 4)
    assert output.pocket_node_hidden.shape == (4, 4)
    assert output.pair_embeddings.shape == (12, 4)
    assert output.pair_logits.shape == (12,)
    assert output.pre_post_geometry_predictions_angstrom.shape == (12, 2)
    assert output.pair_logits.dtype == torch.float32
    assert torch.all(output.pre_post_geometry_predictions_angstrom >= 0)
    assert output.target_pair_consistency.tolist() == [True, True]


def test_anchor_invalid_rows_do_not_enter_encoder_or_receive_gradient() -> None:
    supervision = _supervision()
    supervision = replace(
        supervision,
        ligand_anchor_distance_angstrom=torch.tensor([
            [1.0], [float("nan")], [float("nan")],
            [float("nan")], [float("nan")], [float("nan")],
        ]),
        ligand_anchor_distance_valid=torch.tensor(
            [[True], [False], [False], [False], [False], [False]]
        ),
    )
    auxiliary = CovapieCurrent11AuxiliaryModelV1(joint_nf=4)
    with torch.no_grad():
        auxiliary.anchor_distance_encoder[-1].weight.fill_(1.0)
    delta = auxiliary.encode_role_mask_anchor_v1(
        supervision=supervision,
        ligand_batch_index=torch.tensor([0, 0, 0, 1, 1, 1]),
    )
    # Other embedding tables are still exact zero.
    assert torch.all(delta[1:] == 0)
    delta.sum().backward()
    assert auxiliary.anchor_distance_encoder[0].weight.grad is not None


def test_pair_bce_reduction_exact_per_sample_and_sample_isolation() -> None:
    _, supervision, trace, _, output = _model_output()
    logits = torch.tensor(
        [-2.0, -1.0, 0.0, 1.0, 2.0, 3.0,
         4.0, 3.0, 2.0, 1.0, 0.0, -1.0],
        requires_grad=True,
    )
    output = replace(output, pair_logits=logits)
    losses = compute_covapie_current11_training_losses_v1(
        model_output=output,
        supervision=supervision,
        diffusion_trace=trace,
        loss_weights=CovapieCurrent11LossWeightsV1(),
    )
    expected_samples = []
    for start, end, positive in ((0, 6, 4), (6, 12, 10)):
        pos = F.binary_cross_entropy_with_logits(
            logits[positive], torch.ones(())
        )
        negative = torch.cat((logits[start:positive], logits[positive + 1:end]))
        neg = F.binary_cross_entropy_with_logits(
            negative, torch.zeros_like(negative)
        )
        expected_samples.append(0.5 * pos + 0.5 * neg)
    assert torch.allclose(
        losses.loss_covalent_pair_prediction,
        torch.stack(expected_samples).mean(),
    )
    changed = logits.detach().clone()
    changed[6:] += 100
    changed_output = replace(output, pair_logits=changed)
    changed_losses = compute_covapie_current11_training_losses_v1(
        model_output=changed_output,
        supervision=supervision,
        diffusion_trace=trace,
        loss_weights=CovapieCurrent11LossWeightsV1(),
    )
    assert torch.equal(
        losses.pair_prediction_per_sample_detached[:1],
        changed_losses.pair_prediction_per_sample_detached[:1],
    )


def test_contrastive_formula_is_exact_and_sample_local() -> None:
    _, supervision, trace, _, output = _model_output()
    logits = torch.linspace(-1.0, 1.0, 12, requires_grad=True)
    output = replace(output, pair_logits=logits)
    losses = compute_covapie_current11_training_losses_v1(
        model_output=output,
        supervision=supervision,
        diffusion_trace=trace,
        loss_weights=CovapieCurrent11LossWeightsV1(),
    )
    expected = torch.stack((
        -F.log_softmax(logits[:6], dim=0)[4],
        -F.log_softmax(logits[6:], dim=0)[4],
    )).mean()
    assert torch.allclose(losses.loss_covalent_pair_contrastive, expected)


def test_geometry_mask_smooth_l1_and_observed_distance_not_consumed() -> None:
    _, supervision, trace, _, output = _model_output(geometry=True)
    losses = compute_covapie_current11_training_losses_v1(
        model_output=output,
        supervision=supervision,
        diffusion_trace=trace,
        loss_weights=CovapieCurrent11LossWeightsV1(pre_post_geometry=1.0),
    )
    expected = F.smooth_l1_loss(
        output.pre_post_geometry_predictions_angstrom[4, 0],
        torch.tensor(2.0),
        beta=1.0,
    )
    assert torch.allclose(losses.loss_pre_post_geometry, expected)
    changed = replace(
        supervision,
        observed_complex_pair_distance_angstrom=torch.tensor([[999.0], [777.0]]),
    )
    changed_losses = compute_covapie_current11_training_losses_v1(
        model_output=output,
        supervision=changed,
        diffusion_trace=trace,
        loss_weights=CovapieCurrent11LossWeightsV1(pre_post_geometry=1.0),
    )
    assert torch.equal(
        losses.loss_pre_post_geometry,
        changed_losses.loss_pre_post_geometry,
    )


def test_zero_valid_auxiliaries_are_graph_connected_exact_zero() -> None:
    _, supervision, trace, _, output = _model_output()
    supervision = replace(
        supervision,
        pair_positive_candidate_valid=torch.tensor([False, False]),
        pair_positive_candidate_index=torch.tensor([-1, -1]),
        pair_head_candidate_loss_mask=torch.tensor([False] * 12),
        pair_contrastive_sample_loss_mask=torch.tensor([False, False]),
    )
    losses = compute_covapie_current11_training_losses_v1(
        model_output=output,
        supervision=supervision,
        diffusion_trace=trace,
        loss_weights=CovapieCurrent11LossWeightsV1(),
    )
    assert losses.loss_covalent_pair_prediction.item() == 0.0
    assert losses.loss_covalent_pair_contrastive.item() == 0.0
    assert losses.loss_pre_post_geometry.item() == 0.0
    assert losses.covalent_pair_prediction_valid_sample_count == 0
    assert losses.covalent_pair_contrastive_valid_sample_count == 0
    assert losses.pre_post_geometry_valid_sample_count == 0
    combined = (
        losses.loss_covalent_pair_prediction
        + losses.loss_covalent_pair_contrastive
        + losses.loss_pre_post_geometry
    )
    gradients = torch.autograd.grad(
        combined,
        (output.pair_logits, output.pre_post_geometry_predictions_angstrom),
        allow_unused=True,
    )
    assert gradients[0] is not None and torch.equal(
        gradients[0], torch.zeros_like(gradients[0])
    )
    assert gradients[1] is not None and torch.equal(
        gradients[1], torch.zeros_like(gradients[1])
    )


def test_zero_negative_pair_positive_only_and_contrastive_zero() -> None:
    _, supervision, trace, _, output = _model_output()
    supervision = replace(
        supervision,
        sample_training_admitted=torch.tensor([True]),
        canonical_task_id=torch.tensor([4]),
        canonical_task_valid=torch.tensor([True]),
        pair_candidate_offsets=torch.tensor([0, 1]),
        pair_candidate_batch_index=torch.tensor([0]),
        pair_candidate_ligand_local_index=torch.tensor([2]),
        pair_candidate_residue_local_index=torch.tensor([0]),
        pair_candidate_ligand_flat_index=torch.tensor([2]),
        pair_candidate_pocket_flat_index=torch.tensor([0]),
        pair_candidate_is_positive=torch.tensor([True]),
        pair_candidate_is_negative=torch.tensor([False]),
        pair_positive_candidate_index=torch.tensor([0]),
        pair_positive_candidate_valid=torch.tensor([True]),
        pair_negative_count=torch.tensor([0]),
        pair_head_candidate_loss_mask=torch.tensor([True]),
        pair_contrastive_sample_loss_mask=torch.tensor([False]),
        pre_post_geometry_target_angstrom=torch.full((1, 2), float("nan")),
        pre_post_geometry_component_valid_mask=torch.tensor([[False, False]]),
        pre_post_geometry_component_loss_mask=torch.tensor([[False, False]]),
    )
    one_logit = output.pair_logits[:1]
    output = replace(
        output,
        pair_logits=one_logit,
        pre_post_geometry_predictions_angstrom=(
            output.pre_post_geometry_predictions_angstrom[:1]
        ),
        pair_candidate_offsets=torch.tensor([0, 1]),
        pair_candidate_batch_index=torch.tensor([0]),
        pair_candidate_ligand_local_index=torch.tensor([2]),
        pair_candidate_residue_local_index=torch.tensor([0]),
        pair_candidate_ligand_flat_index=torch.tensor([2]),
        pair_candidate_pocket_flat_index=torch.tensor([0]),
    )
    trace.base_objective_per_sample = trace.base_objective_per_sample[:1]
    losses = compute_covapie_current11_training_losses_v1(
        model_output=output,
        supervision=supervision,
        diffusion_trace=trace,
        loss_weights=CovapieCurrent11LossWeightsV1(),
    )
    expected = F.binary_cross_entropy_with_logits(one_logit[0], torch.ones(()))
    assert torch.allclose(losses.loss_covalent_pair_prediction, expected)
    assert losses.loss_covalent_pair_contrastive.item() == 0.0


def test_loss_total_weighting_exact() -> None:
    _, supervision, trace, _, output = _model_output(geometry=True)
    weights = CovapieCurrent11LossWeightsV1(
        base_diffusion=2.0,
        covalent_pair_prediction=3.0,
        pre_post_geometry=4.0,
        covalent_pair_contrastive=5.0,
    )
    losses = compute_covapie_current11_training_losses_v1(
        model_output=output,
        supervision=supervision,
        diffusion_trace=trace,
        loss_weights=weights,
    )
    expected = (
        2 * losses.loss_base_diffusion
        + 3 * losses.loss_covalent_pair_prediction
        + 4 * losses.loss_pre_post_geometry
        + 5 * losses.loss_covalent_pair_contrastive
    )
    assert torch.equal(losses.loss_total, expected)


def test_pair_logits_are_rigid_translation_rotation_invariant() -> None:
    auxiliary, supervision, trace, delta, output = _model_output()
    rotation = torch.tensor([
        [0.0, -1.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0],
    ])
    translation = torch.tensor([9.0, -4.0, 2.0])
    lig = trace.denoised_ligand_xh.clone()
    pocket = trace.clean_centered_pocket_xh.clone()
    lig[:, :3] = lig[:, :3] @ rotation.T + translation
    pocket[:, :3] = pocket[:, :3] @ rotation.T + translation
    transformed = SimpleNamespace(**trace.__dict__)
    transformed.denoised_ligand_xh = lig
    transformed.clean_centered_pocket_xh = pocket
    transformed_output = auxiliary(
        diffusion_trace=transformed,
        supervision=supervision,
        role_mask_anchor_hidden_delta=delta,
    )
    assert torch.allclose(output.pair_logits, transformed_output.pair_logits)


def test_synthetic_cpu_autograd_connects_base_role_pair_and_geometry_paths() -> None:
    torch.manual_seed(7)
    supervision = _supervision(geometry=True)
    auxiliary = CovapieCurrent11AuxiliaryModelV1(joint_nf=4)
    with torch.no_grad():
        auxiliary.role_embedding.weight.fill_(0.01)
        auxiliary.task_embedding.weight.fill_(0.01)
        auxiliary.generation_state_embedding.weight.fill_(0.01)
        auxiliary.seed_indicator_embedding.weight.fill_(0.01)
        auxiliary.anchor_distance_encoder[-1].weight.fill_(0.01)
    ligand_batch = torch.tensor([0, 0, 0, 1, 1, 1])
    delta = auxiliary.encode_role_mask_anchor_v1(
        supervision=supervision, ligand_batch_index=ligand_batch
    )
    existing_parameter = torch.nn.Parameter(torch.tensor(0.5))
    base_hidden = torch.randn(6, 4, requires_grad=True)
    pocket_hidden = torch.randn(4, 4, requires_grad=True)
    trace = _trace(
        ligand_hidden=base_hidden + existing_parameter * 0.1 + delta,
        pocket_hidden=pocket_hidden + existing_parameter * 0.1,
        base=torch.stack((existing_parameter.square(), existing_parameter + 1)),
    )
    output = auxiliary(
        diffusion_trace=trace,
        supervision=supervision,
        role_mask_anchor_hidden_delta=delta,
    )
    losses = compute_covapie_current11_training_losses_v1(
        model_output=output,
        supervision=supervision,
        diffusion_trace=trace,
        loss_weights=CovapieCurrent11LossWeightsV1(pre_post_geometry=1.0),
    )
    losses.loss_total.backward()
    assert existing_parameter.grad is not None and existing_parameter.grad != 0
    assert auxiliary.role_embedding.weight.grad is not None
    assert auxiliary.pair_logit.weight.grad is not None
    assert auxiliary.pre_post_geometry_head[-1].weight.grad is not None
    assert base_hidden.grad is not None
    assert pocket_hidden.grad is not None


@pytest.mark.parametrize("temperature", (0.5, 2.0, True))
def test_non_frozen_temperature_fails_closed(temperature: object) -> None:
    _, supervision, trace, _, output = _model_output()
    with pytest.raises(ValueError, match=f"^{AUXILIARY_ERROR}$"):
        compute_covapie_current11_training_losses_v1(
            model_output=output,
            supervision=supervision,
            diffusion_trace=trace,
            loss_weights=CovapieCurrent11LossWeightsV1(),
            pair_contrastive_temperature=temperature,
        )
