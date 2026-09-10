from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest
import torch

from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (
    AUXILIARY_ERROR,
    CovapieCurrent11AuxiliaryModelV1,
    CovapieCurrent11LossWeightsV1,
    compute_covapie_current11_training_losses_v1,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CANONICAL_TASKS_V1,
    CovapieCurrent11TrainingSupervisionTensorsV1,
)
from covalent_ext.covapie_exact16_post_geometry_partial_supervision_authority_v1 import (
    GEOMETRY_COMPONENT_REGISTRY_V1,
    POST_COVALENT_REACTIVE_PAIR_DISTANCE_COMPONENT_INDEX_V1,
    PRE_COVALENT_REACTIVE_PAIR_DISTANCE_COMPONENT_INDEX_V1,
)


PRE = PRE_COVALENT_REACTIVE_PAIR_DISTANCE_COMPONENT_INDEX_V1
POST = POST_COVALENT_REACTIVE_PAIR_DISTANCE_COMPONENT_INDEX_V1
EXISTING_PURPOSE = "existing_component_masks_v1"
HIDDEN_POST_PURPOSE = "independent_hidden_post_distance_v1"
LIGAND_BATCH_INDEX = torch.tensor([0, 0, 0, 1, 1, 1, 2, 2, 2])
POCKET_BATCH_INDEX = torch.tensor([0, 0, 1, 1, 2, 2])
_PURPOSE_OMITTED = object()


def _synthetic_supervision() -> CovapieCurrent11TrainingSupervisionTensorsV1:
    """Three legal synthetic samples: generated, fixed, and unrequested POST."""

    nan = float("nan")
    generation = torch.tensor(
        [
            [False],
            [False],
            [True],  # Task A: the positive warhead endpoint is generated.
            [True],
            [False],
            [False],  # Task B3: the positive warhead endpoint is fixed.
            [True],
            [True],
            [True],  # Task C: generated, but POST supervision is not requested.
        ],
        dtype=torch.bool,
    )
    fixed = ~generation
    geometry_valid = torch.tensor(
        [[False, True], [False, True], [False, False]], dtype=torch.bool
    )
    return CovapieCurrent11TrainingSupervisionTensorsV1(
        sample_training_admitted=torch.tensor([True, True, True]),
        canonical_task_id=torch.tensor([0, 3, 4], dtype=torch.long),
        canonical_task_valid=torch.tensor([True, True, True]),
        ligand_role_id=torch.tensor([0, 1, 2] * 3, dtype=torch.long),
        ligand_role_valid=torch.tensor([True] * 9),
        ligand_base_generation_mask=generation,
        ligand_base_fixed_mask=fixed,
        ligand_base_target_mask=generation.clone(),
        ligand_base_context_mask=fixed.clone(),
        ligand_active_diffusion_loss_mask=generation.clone(),
        ligand_minimal_seed_or_anchor_mask=torch.zeros((9, 1), dtype=torch.bool),
        ligand_minimal_seed_or_anchor_valid=torch.tensor([False, False, False]),
        ligand_anchor_distance_angstrom=torch.tensor(
            [[1.0], [1.2], [1.4], [1.6], [1.8], [2.0], [2.2], [2.4], [2.6]]
        ),
        ligand_anchor_distance_valid=torch.ones((9, 1), dtype=torch.bool),
        target_residue_membership_mask=torch.ones((6, 1), dtype=torch.bool),
        target_residue_reactive_atom_mask=torch.tensor(
            [[False], [True], [False], [True], [False], [True]]
        ),
        target_residue_reactive_atom_local_index=torch.tensor(
            [1, 1, 1], dtype=torch.long
        ),
        target_residue_reactive_atom_flat_index=torch.tensor(
            [1, 3, 5], dtype=torch.long
        ),
        target_residue_condition_valid=torch.tensor([True, True, True]),
        pair_candidate_offsets=torch.tensor([0, 4, 9, 12], dtype=torch.long),
        pair_candidate_batch_index=torch.tensor(
            [0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2], dtype=torch.long
        ),
        pair_candidate_ligand_local_index=torch.tensor(
            [0, 1, 2, 0, 0, 1, 0, 2, 2, 0, 2, 1], dtype=torch.long
        ),
        pair_candidate_residue_local_index=torch.tensor(
            [0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1], dtype=torch.long
        ),
        pair_candidate_ligand_flat_index=torch.tensor(
            [0, 1, 2, 0, 3, 4, 3, 5, 5, 6, 8, 7], dtype=torch.long
        ),
        pair_candidate_pocket_flat_index=torch.tensor(
            [0, 0, 1, 1, 2, 2, 3, 2, 3, 4, 5, 5], dtype=torch.long
        ),
        pair_candidate_is_positive=torch.tensor(
            [False, False, True, False, False, False, False, False, True,
             False, True, False]
        ),
        pair_candidate_is_negative=torch.tensor(
            [True, True, False, True, True, True, True, True, False,
             True, False, True]
        ),
        pair_positive_candidate_index=torch.tensor([2, 8, 10], dtype=torch.long),
        pair_positive_candidate_valid=torch.tensor([True, True, True]),
        pair_negative_count=torch.tensor([3, 4, 2], dtype=torch.long),
        pair_head_candidate_loss_mask=torch.tensor([True] * 12),
        pair_contrastive_sample_loss_mask=torch.tensor([False, False, False]),
        observed_complex_pair_distance_angstrom=torch.tensor(
            [[1.45], [2.05], [3.10]]
        ),
        observed_complex_pair_distance_valid=torch.tensor(
            [[True], [True], [True]]
        ),
        pre_post_geometry_target_angstrom=torch.tensor(
            [[nan, 7.25], [nan, 0.15], [nan, nan]], dtype=torch.float32
        ),
        pre_post_geometry_component_valid_mask=geometry_valid,
        pre_post_geometry_component_loss_mask=geometry_valid.clone(),
    )


def _synthetic_trace(*, joint_nf: int) -> SimpleNamespace:
    ligand_coordinates = torch.tensor(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 2.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 1.0, 1.0],
            [2.0, 0.0, 1.0],
            [-1.0, 0.0, 0.0],
            [-1.0, 2.0, 0.0],
            [-2.0, 1.0, 2.0],
        ]
    )
    pocket_coordinates = torch.tensor(
        [
            [3.0, 0.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, -1.0, 1.0],
            [2.0, 1.0, 0.0],
            [-2.0, 0.0, 0.0],
            [-2.0, 1.0, 0.0],
        ]
    )
    ligand_hidden = torch.arange(9 * joint_nf, dtype=torch.float32).reshape(
        9, joint_nf
    ) / 17.0
    pocket_hidden = torch.arange(6 * joint_nf, dtype=torch.float32).reshape(
        6, joint_nf
    ) / 13.0
    return SimpleNamespace(
        ligand_node_hidden=ligand_hidden,
        pocket_node_hidden=pocket_hidden,
        diffusion_epsilon_prediction_ligand=torch.zeros((9, 5)),
        denoised_ligand_xh=torch.cat(
            (ligand_coordinates, torch.zeros((9, 2))), dim=1
        ),
        clean_centered_pocket_xh=torch.cat(
            (pocket_coordinates, torch.zeros((6, 2))), dim=1
        ),
        diffusion_timestep_int=torch.tensor([3, 5, 7], dtype=torch.long),
        coordinate_normalization=2.5,
        base_objective_per_sample=torch.tensor([0.2, 0.4, 0.6]),
    )


def _model_fixture():
    torch.manual_seed(41)
    supervision = _synthetic_supervision()
    auxiliary = CovapieCurrent11AuxiliaryModelV1(joint_nf=5)
    ligand_batch_index = torch.tensor([0, 0, 0, 1, 1, 1, 2, 2, 2])
    role_delta = auxiliary.encode_role_mask_anchor_v1(
        supervision=supervision,
        ligand_batch_index=ligand_batch_index,
    )
    trace = _synthetic_trace(joint_nf=5)
    output = auxiliary(
        diffusion_trace=trace,
        supervision=supervision,
        role_mask_anchor_hidden_delta=role_delta,
    )
    return auxiliary, supervision, trace, role_delta, output


def _unit_beta_smooth_l1(prediction: torch.Tensor, target: float) -> torch.Tensor:
    absolute_error = torch.abs(prediction - target)
    return torch.where(
        absolute_error < 1.0,
        0.5 * absolute_error.square(),
        absolute_error - 0.5,
    )


def _geometry_losses(
    *,
    output,
    supervision,
    trace,
    purpose=_PURPOSE_OMITTED,
    ligand_batch_index=None,
    pocket_batch_index=None,
):
    keyword_arguments = {}
    if purpose is not _PURPOSE_OMITTED:
        keyword_arguments["post_geometry_loss_purpose"] = purpose
    return compute_covapie_current11_training_losses_v1(
        model_output=output,
        supervision=supervision,
        diffusion_trace=trace,
        loss_weights=CovapieCurrent11LossWeightsV1(
            base_diffusion=0.0,
            covalent_pair_prediction=0.0,
            pre_post_geometry=1.0,
            covalent_pair_contrastive=0.0,
        ),
        ligand_batch_index=ligand_batch_index,
        pocket_batch_index=pocket_batch_index,
        **keyword_arguments,
    )


def _hidden_geometry_losses(*, output, supervision, trace):
    return _geometry_losses(
        output=output,
        supervision=supervision,
        trace=trace,
        purpose=HIDDEN_POST_PURPOSE,
        ligand_batch_index=LIGAND_BATCH_INDEX.clone(),
        pocket_batch_index=POCKET_BATCH_INDEX.clone(),
    )


def _hidden_post_candidate_eligibility(
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1,
) -> torch.Tensor:
    """Test-only fail-closed policy for independent hidden-POST prediction."""

    requested = supervision.pre_post_geometry_component_loss_mask[:, POST]
    valid = supervision.pre_post_geometry_component_valid_mask[:, POST]
    eligible = torch.zeros_like(requested)
    for sample in range(len(requested)):
        if not bool(
            requested[sample]
            and valid[sample]
            and supervision.sample_training_admitted[sample]
            and supervision.canonical_task_valid[sample]
            and supervision.target_residue_condition_valid[sample]
            and supervision.pair_positive_candidate_valid[sample]
        ):
            continue
        candidate = int(supervision.pair_positive_candidate_index[sample].item())
        start = int(supervision.pair_candidate_offsets[sample].item())
        end = int(supervision.pair_candidate_offsets[sample + 1].item())
        if not (
            start <= candidate < end
            and bool(supervision.pair_candidate_is_positive[candidate])
            and int(supervision.pair_candidate_batch_index[candidate].item())
            == sample
            and int(
                supervision.pair_candidate_pocket_flat_index[candidate].item()
            )
            == int(
                supervision.target_residue_reactive_atom_flat_index[sample].item()
            )
        ):
            continue
        ligand_flat = int(
            supervision.pair_candidate_ligand_flat_index[candidate].item()
        )
        endpoint_generated = bool(
            supervision.ligand_base_generation_mask[ligand_flat, 0]
        )
        endpoint_fixed = bool(
            supervision.ligand_base_fixed_mask[ligand_flat, 0]
        )
        eligible[sample] = endpoint_generated and not endpoint_fixed
    return eligible


def test_real_registry_keeps_exact_pre_post_and_canonical_five_tasks() -> None:
    assert (PRE, POST) == (0, 1)
    assert tuple(
        (item.component_index, item.semantic_name, item.unit)
        for item in GEOMETRY_COMPONENT_REGISTRY_V1
    ) == (
        (0, "PRE_COVALENT_REACTIVE_PAIR_DISTANCE_ANGSTROM", "angstrom"),
        (1, "POST_COVALENT_REACTIVE_PAIR_DISTANCE_ANGSTROM", "angstrom"),
    )
    assert CANONICAL_TASKS_V1 == (
        (0, "warhead_only", "A", (2,)),
        (1, "linker_plus_warhead", "B", (1, 2)),
        (2, "scaffold_plus_warhead", "B2", (0, 2)),
        (3, "scaffold_only", "B3", (0,)),
        (4, "scaffold_plus_linker_plus_warhead", "C", (0, 1, 2)),
    )


def test_post_only_selects_component_one_positive_candidate_and_gradients() -> None:
    _, supervision, trace, _, output = _model_fixture()
    predictions = output.pre_post_geometry_predictions_angstrom
    predictions.retain_grad()

    assert supervision.pre_post_geometry_target_angstrom.shape == (3, 2)
    assert predictions.shape == (12, 2)
    assert torch.isnan(
        supervision.pre_post_geometry_target_angstrom[:, PRE]
    ).all()
    assert not supervision.pre_post_geometry_component_valid_mask[:, PRE].any()
    assert not supervision.pre_post_geometry_component_loss_mask[:, PRE].any()
    assert supervision.pair_positive_candidate_index.tolist() == [2, 8, 10]
    assert supervision.pair_candidate_offsets.tolist() == [0, 4, 9, 12]

    losses = _geometry_losses(
        output=output, supervision=supervision, trace=trace
    )
    expected_samples = torch.stack(
        (
            _unit_beta_smooth_l1(predictions[2, POST], 7.25),
            _unit_beta_smooth_l1(predictions[8, POST], 0.15),
        )
    )
    torch.testing.assert_close(
        losses.loss_pre_post_geometry, expected_samples.mean()
    )
    torch.testing.assert_close(
        losses.pre_post_geometry_per_sample_detached[:2],
        expected_samples.detach(),
    )
    assert torch.isnan(losses.pre_post_geometry_per_sample_detached[2])
    assert losses.pre_post_geometry_valid_sample_count == 2

    losses.loss_pre_post_geometry.backward()
    assert predictions.grad is not None
    expected_gradient_support = torch.zeros((12, 2), dtype=torch.bool)
    expected_gradient_support[2, POST] = True
    expected_gradient_support[8, POST] = True
    assert torch.equal(predictions.grad != 0, expected_gradient_support)


def test_targets_change_loss_not_prediction_and_observed_is_not_consumed() -> None:
    auxiliary, supervision, trace, role_delta, output = _model_fixture()
    baseline_losses = _geometry_losses(
        output=output, supervision=supervision, trace=trace
    )

    changed_targets = supervision.pre_post_geometry_target_angstrom.clone()
    changed_targets[:2, POST] = torch.tensor([17.25, 20.15])
    target_changed_supervision = replace(
        supervision,
        pre_post_geometry_target_angstrom=changed_targets,
    )
    target_changed_output = auxiliary(
        diffusion_trace=trace,
        supervision=target_changed_supervision,
        role_mask_anchor_hidden_delta=role_delta,
    )
    assert torch.equal(output.pair_embeddings, target_changed_output.pair_embeddings)
    assert torch.equal(output.pair_logits, target_changed_output.pair_logits)
    assert torch.equal(
        output.pre_post_geometry_predictions_angstrom,
        target_changed_output.pre_post_geometry_predictions_angstrom,
    )
    target_changed_losses = _geometry_losses(
        output=target_changed_output,
        supervision=target_changed_supervision,
        trace=trace,
    )
    assert target_changed_losses.loss_pre_post_geometry > (
        baseline_losses.loss_pre_post_geometry + 1.0
    )

    observed_changed_supervision = replace(
        supervision,
        observed_complex_pair_distance_angstrom=torch.tensor(
            [[101.0], [202.0], [303.0]]
        ),
    )
    observed_changed_output = auxiliary(
        diffusion_trace=trace,
        supervision=observed_changed_supervision,
        role_mask_anchor_hidden_delta=role_delta,
    )
    assert torch.equal(output.pair_embeddings, observed_changed_output.pair_embeddings)
    assert torch.equal(output.pair_logits, observed_changed_output.pair_logits)
    assert torch.equal(
        output.pre_post_geometry_predictions_angstrom,
        observed_changed_output.pre_post_geometry_predictions_angstrom,
    )
    observed_changed_losses = _geometry_losses(
        output=observed_changed_output,
        supervision=observed_changed_supervision,
        trace=trace,
    )
    assert torch.equal(
        baseline_losses.loss_pre_post_geometry,
        observed_changed_losses.loss_pre_post_geometry,
    )


def test_pair_embedding_receives_denoised_once_scaled_rigid_distance() -> None:
    auxiliary, supervision, trace, role_delta, _ = _model_fixture()
    captured_pair_inputs: list[torch.Tensor] = []

    def capture_pair_input(_module, inputs) -> None:
        captured_pair_inputs.append(inputs[0].detach().clone())

    handle = auxiliary.pair_embedding.register_forward_pre_hook(capture_pair_input)
    try:
        baseline_output = auxiliary(
            diffusion_trace=trace,
            supervision=supervision,
            role_mask_anchor_hidden_delta=role_delta,
        )

        changed_ligand = trace.denoised_ligand_xh.clone()
        changed_ligand[2, :3] += torch.tensor([0.75, -0.5, 1.25])
        changed_trace = SimpleNamespace(**trace.__dict__)
        changed_trace.denoised_ligand_xh = changed_ligand
        auxiliary(
            diffusion_trace=changed_trace,
            supervision=supervision,
            role_mask_anchor_hidden_delta=role_delta,
        )

        rotation = torch.tensor(
            [[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]]
        )
        translation = torch.tensor([8.0, -3.0, 4.0])
        rigid_ligand = trace.denoised_ligand_xh.clone()
        rigid_pocket = trace.clean_centered_pocket_xh.clone()
        rigid_ligand[:, :3] = rigid_ligand[:, :3] @ rotation.T + translation
        rigid_pocket[:, :3] = rigid_pocket[:, :3] @ rotation.T + translation
        rigid_trace = SimpleNamespace(**trace.__dict__)
        rigid_trace.denoised_ligand_xh = rigid_ligand
        rigid_trace.clean_centered_pocket_xh = rigid_pocket
        rigid_output = auxiliary(
            diffusion_trace=rigid_trace,
            supervision=supervision,
            role_mask_anchor_hidden_delta=role_delta,
        )
    finally:
        handle.remove()

    assert len(captured_pair_inputs) == 3
    ligand_index = supervision.pair_candidate_ligand_flat_index
    pocket_index = supervision.pair_candidate_pocket_flat_index

    def expected_distance(current_trace) -> torch.Tensor:
        return torch.linalg.vector_norm(
            (
                current_trace.denoised_ligand_xh[ligand_index, :3]
                - current_trace.clean_centered_pocket_xh[pocket_index, :3]
            )
            * current_trace.coordinate_normalization,
            dim=1,
        )

    baseline_distance = expected_distance(trace)
    changed_distance = expected_distance(changed_trace)
    rigid_distance = expected_distance(rigid_trace)
    torch.testing.assert_close(captured_pair_inputs[0][:, -1], baseline_distance)
    torch.testing.assert_close(captured_pair_inputs[1][:, -1], changed_distance)
    torch.testing.assert_close(captured_pair_inputs[2][:, -1], rigid_distance)
    assert not torch.allclose(
        captured_pair_inputs[0][:, -1],
        baseline_distance * trace.coordinate_normalization,
    )
    assert captured_pair_inputs[0][2, -1] != captured_pair_inputs[1][2, -1]
    torch.testing.assert_close(baseline_distance, rigid_distance)
    torch.testing.assert_close(
        baseline_output.pre_post_geometry_predictions_angstrom,
        rigid_output.pre_post_geometry_predictions_angstrom,
    )


def test_current_loss_accepts_fixed_endpoint_but_hidden_policy_excludes_it() -> None:
    _, supervision, trace, _, output = _model_fixture()
    observed_before = supervision.observed_complex_pair_distance_angstrom.clone()
    losses = _geometry_losses(
        output=output, supervision=supervision, trace=trace
    )

    positive_candidates = supervision.pair_positive_candidate_index
    positive_ligand_flat = supervision.pair_candidate_ligand_flat_index[
        positive_candidates
    ]
    assert positive_ligand_flat.tolist() == [2, 5, 8]
    assert supervision.ligand_role_id[positive_ligand_flat].tolist() == [2, 2, 2]
    assert supervision.ligand_base_generation_mask[
        positive_ligand_flat, 0
    ].tolist() == [True, False, True]
    assert supervision.ligand_base_fixed_mask[
        positive_ligand_flat, 0
    ].tolist() == [False, True, False]
    assert torch.isfinite(losses.pre_post_geometry_per_sample_detached[:2]).all()

    eligibility = _hidden_post_candidate_eligibility(supervision)
    assert eligibility.tolist() == [True, False, False]
    assert not supervision.pre_post_geometry_component_loss_mask[2, POST]
    assert torch.equal(
        observed_before, supervision.observed_complex_pair_distance_angstrom
    )


def test_real_hidden_purpose_tightens_post_and_preserves_legacy_default() -> None:
    _, supervision, trace, _, output = _model_fixture()
    loss_mask_before = supervision.pre_post_geometry_component_loss_mask.clone()
    valid_mask_before = supervision.pre_post_geometry_component_valid_mask.clone()
    targets_before = supervision.pre_post_geometry_target_angstrom.clone()

    legacy_predictions = torch.ones((12, 2), requires_grad=True)
    legacy_output = replace(
        output,
        pre_post_geometry_predictions_angstrom=legacy_predictions,
    )
    omitted = _geometry_losses(
        output=legacy_output, supervision=supervision, trace=trace
    )
    explicit = _geometry_losses(
        output=legacy_output,
        supervision=supervision,
        trace=trace,
        purpose=EXISTING_PURPOSE,
    )
    legacy_expected = torch.stack((
        _unit_beta_smooth_l1(legacy_predictions[2, POST], 7.25),
        _unit_beta_smooth_l1(legacy_predictions[8, POST], 0.15),
    ))
    torch.testing.assert_close(
        omitted.loss_pre_post_geometry, legacy_expected.mean()
    )
    assert torch.equal(
        omitted.loss_pre_post_geometry, explicit.loss_pre_post_geometry
    )
    assert omitted.pre_post_geometry_valid_sample_count == 2

    hidden_predictions = torch.ones((12, 2), requires_grad=True)
    hidden_output = replace(
        output,
        pre_post_geometry_predictions_angstrom=hidden_predictions,
    )
    hidden = _hidden_geometry_losses(
        output=hidden_output, supervision=supervision, trace=trace
    )
    hidden_expected = _unit_beta_smooth_l1(
        hidden_predictions[2, POST], 7.25
    )
    torch.testing.assert_close(hidden.loss_pre_post_geometry, hidden_expected)
    torch.testing.assert_close(
        hidden.pre_post_geometry_per_sample_detached[0],
        hidden_expected.detach(),
    )
    assert torch.isnan(hidden.pre_post_geometry_per_sample_detached[1:]).all()
    assert hidden.pre_post_geometry_valid_sample_count == 1
    hidden.loss_pre_post_geometry.backward()
    assert hidden_predictions.grad is not None
    expected_support = torch.zeros((12, 2), dtype=torch.bool)
    expected_support[2, POST] = True
    assert torch.equal(hidden_predictions.grad != 0, expected_support)

    assert torch.equal(
        supervision.pre_post_geometry_component_loss_mask, loss_mask_before
    )
    assert torch.equal(
        supervision.pre_post_geometry_component_valid_mask, valid_mask_before
    )
    torch.testing.assert_close(
        supervision.pre_post_geometry_target_angstrom,
        targets_before,
        equal_nan=True,
    )


def test_hidden_purpose_does_not_promote_independent_false_request() -> None:
    _, supervision, trace, _, output = _model_fixture()
    targets = torch.full((3, 2), float("nan"))
    targets[2, POST] = 4.0
    component_valid = torch.zeros((3, 2), dtype=torch.bool)
    component_valid[2, POST] = True
    request = torch.zeros((3, 2), dtype=torch.bool)
    supervision = replace(
        supervision,
        pre_post_geometry_target_angstrom=targets,
        pre_post_geometry_component_valid_mask=component_valid,
        pre_post_geometry_component_loss_mask=request,
    )

    assert supervision.sample_training_admitted[2]
    assert supervision.canonical_task_valid[2]
    assert supervision.target_residue_condition_valid[2]
    assert supervision.pair_positive_candidate_valid[2]
    assert supervision.ligand_base_generation_mask[8, 0]
    assert not supervision.ligand_base_fixed_mask[8, 0]
    assert _hidden_post_candidate_eligibility(supervision).tolist() == [
        False,
        False,
        False,
    ]
    losses = _hidden_geometry_losses(
        output=output, supervision=supervision, trace=trace
    )
    assert losses.loss_pre_post_geometry.item() == 0.0
    assert losses.pre_post_geometry_valid_sample_count == 0
    assert torch.isnan(losses.pre_post_geometry_per_sample_detached).all()


@pytest.mark.parametrize(
    "closed_condition",
    (
        "fixed",
        "both_false",
        "not_admitted",
        "component_invalid",
        "canonical_invalid",
        "target_condition_invalid",
    ),
)
def test_hidden_post_legal_closures_leave_requested_pre_active(
    closed_condition: str,
) -> None:
    _, supervision, trace, _, output = _model_fixture()
    sample = 1 if closed_condition == "fixed" else 0
    candidate = 8 if sample == 1 else 2
    targets = torch.full((3, 2), float("nan"))
    targets[sample] = torch.tensor([2.0, 5.0])
    component_valid = torch.zeros((3, 2), dtype=torch.bool)
    component_valid[sample] = True
    request = component_valid.clone()
    changes = {
        "pre_post_geometry_target_angstrom": targets,
        "pre_post_geometry_component_valid_mask": component_valid,
        "pre_post_geometry_component_loss_mask": request,
    }
    if closed_condition == "both_false":
        generation = supervision.ligand_base_generation_mask.clone()
        fixed = supervision.ligand_base_fixed_mask.clone()
        generation[2, 0] = False
        fixed[2, 0] = False
        changes.update(
            ligand_base_generation_mask=generation,
            ligand_base_fixed_mask=fixed,
        )
    elif closed_condition == "not_admitted":
        admitted = supervision.sample_training_admitted.clone()
        admitted[0] = False
        changes["sample_training_admitted"] = admitted
    elif closed_condition == "component_invalid":
        component_valid[0, POST] = False
    elif closed_condition == "canonical_invalid":
        canonical_valid = supervision.canonical_task_valid.clone()
        canonical_valid[0] = False
        changes["canonical_task_valid"] = canonical_valid
    elif closed_condition == "target_condition_invalid":
        condition_valid = supervision.target_residue_condition_valid.clone()
        condition_valid[0] = False
        changes["target_residue_condition_valid"] = condition_valid
    supervision = replace(supervision, **changes)

    predictions = torch.ones((12, 2), requires_grad=True)
    output = replace(output, pre_post_geometry_predictions_angstrom=predictions)
    losses = _hidden_geometry_losses(
        output=output, supervision=supervision, trace=trace
    )
    expected_pre = _unit_beta_smooth_l1(predictions[candidate, PRE], 2.0)
    torch.testing.assert_close(losses.loss_pre_post_geometry, expected_pre)
    assert losses.pre_post_geometry_valid_sample_count == 1
    assert torch.isfinite(losses.pre_post_geometry_per_sample_detached[sample])
    losses.loss_pre_post_geometry.backward()
    assert predictions.grad is not None
    expected_support = torch.zeros((12, 2), dtype=torch.bool)
    expected_support[candidate, PRE] = True
    assert torch.equal(predictions.grad != 0, expected_support)


def test_hidden_post_pair_invalid_sentinel_is_excluded_before_indexing() -> None:
    _, supervision, trace, _, output = _model_fixture()
    request = torch.zeros((3, 2), dtype=torch.bool)
    request[0, POST] = True
    valid = request.clone()
    targets = torch.full((3, 2), float("nan"))
    targets[0, POST] = 3.0
    pair_valid = supervision.pair_positive_candidate_valid.clone()
    pair_valid[0] = False
    positive_index = supervision.pair_positive_candidate_index.clone()
    positive_index[0] = -1
    supervision = replace(
        supervision,
        pair_positive_candidate_valid=pair_valid,
        pair_positive_candidate_index=positive_index,
        pre_post_geometry_target_angstrom=targets,
        pre_post_geometry_component_valid_mask=valid,
        pre_post_geometry_component_loss_mask=request,
    )
    losses = _hidden_geometry_losses(
        output=output, supervision=supervision, trace=trace
    )
    assert losses.loss_pre_post_geometry.item() == 0.0
    assert losses.pre_post_geometry_valid_sample_count == 0


@pytest.mark.parametrize(
    "purpose",
    (
        None,
        True,
        "",
        "INDEPENDENT_HIDDEN_POST_DISTANCE_V1",
        " independent_hidden_post_distance_v1",
        "independent_hidden_post_distance_v1 ",
        "unknown",
    ),
)
def test_loss_rejects_every_unknown_or_non_exact_purpose(purpose: object) -> None:
    _, supervision, trace, _, output = _model_fixture()
    with pytest.raises(ValueError, match=f"^{AUXILIARY_ERROR}$"):
        _geometry_losses(
            output=output,
            supervision=supervision,
            trace=trace,
            purpose=purpose,
            ligand_batch_index=LIGAND_BATCH_INDEX,
            pocket_batch_index=POCKET_BATCH_INDEX,
        )


@pytest.mark.parametrize("missing", ("ligand", "pocket", "both"))
def test_hidden_purpose_requires_both_independent_batch_indices(
    missing: str,
) -> None:
    _, supervision, trace, _, output = _model_fixture()
    ligand_batch = None if missing in ("ligand", "both") else LIGAND_BATCH_INDEX
    pocket_batch = None if missing in ("pocket", "both") else POCKET_BATCH_INDEX
    with pytest.raises(ValueError, match=f"^{AUXILIARY_ERROR}$"):
        _geometry_losses(
            output=output,
            supervision=supervision,
            trace=trace,
            purpose=HIDDEN_POST_PURPOSE,
            ligand_batch_index=ligand_batch,
            pocket_batch_index=pocket_batch,
        )


@pytest.mark.parametrize(
    "malformation",
    (
        "sample_mask_dtype",
        "sample_mask_shape",
        "component_mask_dtype",
        "component_mask_shape",
        "generation_dtype",
        "generation_shape",
        "overlapping_endpoint_masks",
        "positive_index_dtype",
        "offset_dtype",
        "candidate_index_dtype",
        "ligand_batch_dtype",
        "ligand_batch_shape",
        "ligand_batch_out_of_range",
        "pocket_batch_out_of_range",
        "batch_device_mismatch",
    ),
)
def test_hidden_purpose_rejects_mask_index_and_context_malformations(
    malformation: str,
) -> None:
    _, supervision, trace, _, output = _model_fixture()
    supervision_changes = {}
    ligand_batch = LIGAND_BATCH_INDEX.clone()
    pocket_batch = POCKET_BATCH_INDEX.clone()
    if malformation == "sample_mask_dtype":
        supervision_changes["sample_training_admitted"] = torch.ones(3)
    elif malformation == "sample_mask_shape":
        supervision_changes["canonical_task_valid"] = torch.ones(
            (3, 1), dtype=torch.bool
        )
    elif malformation == "component_mask_dtype":
        supervision_changes["pre_post_geometry_component_valid_mask"] = (
            torch.ones((3, 2))
        )
    elif malformation == "component_mask_shape":
        supervision_changes["pre_post_geometry_component_loss_mask"] = (
            torch.ones((3, 1), dtype=torch.bool)
        )
    elif malformation == "generation_dtype":
        supervision_changes["ligand_base_generation_mask"] = torch.zeros(
            (9, 1)
        )
    elif malformation == "generation_shape":
        supervision_changes["ligand_base_generation_mask"] = torch.zeros(
            9, dtype=torch.bool
        )
    elif malformation == "overlapping_endpoint_masks":
        fixed = supervision.ligand_base_fixed_mask.clone()
        fixed[2, 0] = True
        supervision_changes["ligand_base_fixed_mask"] = fixed
    elif malformation == "positive_index_dtype":
        supervision_changes["pair_positive_candidate_index"] = torch.tensor(
            [2.0, 8.0, 10.0]
        )
    elif malformation == "offset_dtype":
        supervision_changes["pair_candidate_offsets"] = torch.tensor(
            [0.0, 4.0, 9.0, 12.0]
        )
    elif malformation == "candidate_index_dtype":
        supervision_changes["pair_candidate_ligand_flat_index"] = (
            supervision.pair_candidate_ligand_flat_index.float()
        )
    elif malformation == "ligand_batch_dtype":
        ligand_batch = ligand_batch.float()
    elif malformation == "ligand_batch_shape":
        ligand_batch = ligand_batch.unsqueeze(1)
    elif malformation == "ligand_batch_out_of_range":
        ligand_batch[0] = 3
    elif malformation == "pocket_batch_out_of_range":
        pocket_batch[0] = -1
    elif malformation == "batch_device_mismatch":
        ligand_batch = torch.empty((9,), dtype=torch.long, device="meta")
    supervision = replace(supervision, **supervision_changes)
    with pytest.raises(ValueError, match=f"^{AUXILIARY_ERROR}$"):
        _geometry_losses(
            output=output,
            supervision=supervision,
            trace=trace,
            purpose=HIDDEN_POST_PURPOSE,
            ligand_batch_index=ligand_batch,
            pocket_batch_index=pocket_batch,
        )


@pytest.mark.parametrize(
    "contradiction",
    (
        "negative_positive_index",
        "positive_index_out_of_bounds",
        "wrong_candidate_segment",
        "wrong_candidate_batch",
        "cross_sample_ligand_flat",
        "cross_sample_pocket_flat",
        "negative_ligand_flat",
        "pocket_flat_out_of_bounds",
        "wrong_target_anchor",
        "wrong_ligand_local_identity",
        "positive_flag_false",
        "offsets_do_not_cover_candidates",
        "offsets_not_monotonic",
        "model_supervision_metadata_mismatch",
    ),
)
def test_hidden_purpose_rejects_structural_and_index_contradictions(
    contradiction: str,
) -> None:
    _, supervision, trace, _, output = _model_fixture()
    supervision_changes = {}
    output_changes = {}

    def aligned_candidate_change(field_name: str, index: int, value: int) -> None:
        changed = getattr(supervision, field_name).clone()
        changed[index] = value
        supervision_changes[field_name] = changed
        output_changes[field_name] = changed.clone()

    if contradiction == "negative_positive_index":
        changed = supervision.pair_positive_candidate_index.clone()
        changed[0] = -1
        supervision_changes["pair_positive_candidate_index"] = changed
    elif contradiction == "positive_index_out_of_bounds":
        changed = supervision.pair_positive_candidate_index.clone()
        changed[0] = 12
        supervision_changes["pair_positive_candidate_index"] = changed
    elif contradiction == "wrong_candidate_segment":
        changed = supervision.pair_positive_candidate_index.clone()
        changed[0] = 8
        supervision_changes["pair_positive_candidate_index"] = changed
    elif contradiction == "wrong_candidate_batch":
        aligned_candidate_change("pair_candidate_batch_index", 2, 1)
    elif contradiction == "cross_sample_ligand_flat":
        aligned_candidate_change("pair_candidate_ligand_flat_index", 2, 3)
        aligned_candidate_change("pair_candidate_ligand_local_index", 2, 0)
    elif contradiction == "cross_sample_pocket_flat":
        aligned_candidate_change("pair_candidate_pocket_flat_index", 2, 3)
        aligned_candidate_change("pair_candidate_residue_local_index", 2, 1)
        target = supervision.target_residue_reactive_atom_flat_index.clone()
        target[0] = 3
        supervision_changes["target_residue_reactive_atom_flat_index"] = target
    elif contradiction == "negative_ligand_flat":
        aligned_candidate_change("pair_candidate_ligand_flat_index", 2, -1)
    elif contradiction == "pocket_flat_out_of_bounds":
        aligned_candidate_change("pair_candidate_pocket_flat_index", 2, 6)
        target = supervision.target_residue_reactive_atom_flat_index.clone()
        target[0] = 6
        supervision_changes["target_residue_reactive_atom_flat_index"] = target
    elif contradiction == "wrong_target_anchor":
        target = supervision.target_residue_reactive_atom_flat_index.clone()
        target[0] = 0
        supervision_changes["target_residue_reactive_atom_flat_index"] = target
    elif contradiction == "wrong_ligand_local_identity":
        aligned_candidate_change("pair_candidate_ligand_local_index", 2, 1)
    elif contradiction == "positive_flag_false":
        positive = supervision.pair_candidate_is_positive.clone()
        positive[2] = False
        supervision_changes["pair_candidate_is_positive"] = positive
    elif contradiction == "offsets_do_not_cover_candidates":
        offsets = torch.tensor([0, 4, 9, 11], dtype=torch.long)
        supervision_changes["pair_candidate_offsets"] = offsets
        output_changes["pair_candidate_offsets"] = offsets.clone()
    elif contradiction == "offsets_not_monotonic":
        offsets = torch.tensor([0, 9, 4, 12], dtype=torch.long)
        supervision_changes["pair_candidate_offsets"] = offsets
        output_changes["pair_candidate_offsets"] = offsets.clone()
    elif contradiction == "model_supervision_metadata_mismatch":
        changed = output.pair_candidate_ligand_flat_index.clone()
        changed[0] = 1
        output_changes["pair_candidate_ligand_flat_index"] = changed
    supervision = replace(supervision, **supervision_changes)
    output = replace(output, **output_changes)
    with pytest.raises(ValueError, match=f"^{AUXILIARY_ERROR}$"):
        _hidden_geometry_losses(
            output=output, supervision=supervision, trace=trace
        )


def test_hidden_masked_nan_values_do_not_pollute_loss_or_gradients() -> None:
    _, supervision, trace, _, output = _model_fixture()
    targets = supervision.pre_post_geometry_target_angstrom.clone()
    targets[1, POST] = float("nan")
    targets[2, POST] = float("nan")
    supervision = replace(
        supervision, pre_post_geometry_target_angstrom=targets
    )
    predictions = torch.ones((12, 2))
    predictions[8, POST] = float("nan")
    predictions[10, POST] = float("nan")
    predictions.requires_grad_()
    output = replace(output, pre_post_geometry_predictions_angstrom=predictions)

    losses = _hidden_geometry_losses(
        output=output, supervision=supervision, trace=trace
    )
    assert torch.isfinite(losses.loss_pre_post_geometry)
    assert losses.pre_post_geometry_valid_sample_count == 1
    losses.loss_pre_post_geometry.backward()
    assert predictions.grad is not None
    expected_support = torch.zeros((12, 2), dtype=torch.bool)
    expected_support[2, POST] = True
    assert torch.equal(predictions.grad != 0, expected_support)


@pytest.mark.parametrize(
    ("invalid_kind", "invalid_value"),
    (
        ("target", float("nan")),
        ("target", -1.0),
        ("prediction", float("nan")),
        ("prediction", -1.0),
    ),
)
def test_hidden_selected_nonfinite_or_negative_distances_fail_closed(
    invalid_kind: str, invalid_value: float
) -> None:
    _, supervision, trace, _, output = _model_fixture()
    if invalid_kind == "target":
        targets = supervision.pre_post_geometry_target_angstrom.clone()
        targets[0, POST] = invalid_value
        supervision = replace(
            supervision, pre_post_geometry_target_angstrom=targets
        )
    else:
        predictions = output.pre_post_geometry_predictions_angstrom.detach().clone()
        predictions[2, POST] = invalid_value
        output = replace(
            output, pre_post_geometry_predictions_angstrom=predictions
        )
    with pytest.raises(ValueError, match=f"^{AUXILIARY_ERROR}$"):
        _hidden_geometry_losses(
            output=output, supervision=supervision, trace=trace
        )


def test_hidden_all_geometry_excluded_returns_finite_connected_zero() -> None:
    _, supervision, trace, _, output = _model_fixture()
    request = torch.zeros((3, 2), dtype=torch.bool)
    valid = torch.zeros((3, 2), dtype=torch.bool)
    targets = torch.full((3, 2), float("nan"))
    supervision = replace(
        supervision,
        pre_post_geometry_target_angstrom=targets,
        pre_post_geometry_component_valid_mask=valid,
        pre_post_geometry_component_loss_mask=request,
    )
    predictions = torch.full((12, 2), float("nan"), requires_grad=True)
    output = replace(output, pre_post_geometry_predictions_angstrom=predictions)
    losses = _hidden_geometry_losses(
        output=output, supervision=supervision, trace=trace
    )
    assert torch.isfinite(losses.loss_pre_post_geometry)
    assert losses.loss_pre_post_geometry.item() == 0.0
    assert losses.pre_post_geometry_valid_sample_count == 0
    losses.loss_pre_post_geometry.backward()
    assert predictions.grad is not None
    assert torch.equal(predictions.grad, torch.zeros_like(predictions.grad))


def test_hidden_pre_post_component_order_and_per_sample_reduction_are_exact() -> None:
    _, supervision, trace, _, output = _model_fixture()
    predictions = torch.ones((12, 2))
    predictions[2] = torch.tensor([1.0, 2.0])
    output = replace(output, pre_post_geometry_predictions_angstrom=predictions)

    def run(mask: torch.Tensor, targets: torch.Tensor):
        current = replace(
            supervision,
            pre_post_geometry_target_angstrom=targets,
            pre_post_geometry_component_valid_mask=mask.clone(),
            pre_post_geometry_component_loss_mask=mask.clone(),
        )
        return _hidden_geometry_losses(
            output=output, supervision=current, trace=trace
        )

    pre_mask = torch.zeros((3, 2), dtype=torch.bool)
    pre_mask[0, PRE] = True
    pre_targets = torch.full((3, 2), float("nan"))
    pre_targets[0, PRE] = 3.0
    pre_only = run(pre_mask, pre_targets)
    expected_pre = _unit_beta_smooth_l1(predictions[2, PRE], 3.0)
    torch.testing.assert_close(pre_only.loss_pre_post_geometry, expected_pre)

    post_mask = torch.zeros((3, 2), dtype=torch.bool)
    post_mask[0, POST] = True
    post_targets = torch.full((3, 2), float("nan"))
    post_targets[0, POST] = 5.0
    post_only = run(post_mask, post_targets)
    expected_post = _unit_beta_smooth_l1(predictions[2, POST], 5.0)
    torch.testing.assert_close(post_only.loss_pre_post_geometry, expected_post)

    both_mask = pre_mask | post_mask
    both_targets = torch.full((3, 2), float("nan"))
    both_targets[0] = torch.tensor([3.0, 5.0])
    both = run(both_mask, both_targets)
    torch.testing.assert_close(
        both.loss_pre_post_geometry,
        torch.stack((expected_pre, expected_post)).mean(),
    )
    assert both.pre_post_geometry_valid_sample_count == 1

    no_mask = torch.zeros((3, 2), dtype=torch.bool)
    no_targets = torch.full((3, 2), float("nan"))
    none = run(no_mask, no_targets)
    assert none.loss_pre_post_geometry.item() == 0.0
    assert none.pre_post_geometry_valid_sample_count == 0


@pytest.mark.parametrize("task_id", (0, 1, 2, 3, 4))
def test_hidden_purpose_uses_legal_endpoint_masks_not_task_aliases(
    task_id: int,
) -> None:
    _, supervision, trace, _, output = _model_fixture()
    generated_roles = {
        0: (False, False, True),
        1: (False, True, True),
        2: (True, False, True),
        3: (True, False, False),
        4: (True, True, True),
    }[task_id]
    generation = supervision.ligand_base_generation_mask.clone()
    generation[:3, 0] = torch.tensor(generated_roles, dtype=torch.bool)
    fixed = supervision.ligand_base_fixed_mask.clone()
    fixed[:3, 0] = ~generation[:3, 0]
    task_ids = supervision.canonical_task_id.clone()
    task_ids[0] = task_id
    targets = torch.full((3, 2), float("nan"))
    targets[0] = torch.tensor([2.0, 5.0])
    valid = torch.zeros((3, 2), dtype=torch.bool)
    valid[0, POST] = True
    request = valid.clone()
    if task_id == 3:
        valid[0, PRE] = True
        request[0, PRE] = True
    supervision = replace(
        supervision,
        canonical_task_id=task_ids,
        ligand_base_generation_mask=generation,
        ligand_base_fixed_mask=fixed,
        ligand_base_target_mask=generation.clone(),
        ligand_base_context_mask=fixed.clone(),
        ligand_active_diffusion_loss_mask=generation.clone(),
        pre_post_geometry_target_angstrom=targets,
        pre_post_geometry_component_valid_mask=valid,
        pre_post_geometry_component_loss_mask=request,
    )
    output = replace(output, canonical_task_id=task_ids.clone())
    predictions = torch.ones((12, 2))
    output = replace(output, pre_post_geometry_predictions_angstrom=predictions)
    losses = _hidden_geometry_losses(
        output=output, supervision=supervision, trace=trace
    )

    assert losses.pre_post_geometry_valid_sample_count == 1
    if task_id == 3:
        expected = _unit_beta_smooth_l1(predictions[2, PRE], 2.0)
        assert not generation[2, 0] and fixed[2, 0]
    else:
        expected = _unit_beta_smooth_l1(predictions[2, POST], 5.0)
        assert generation[2, 0] and not fixed[2, 0]
    torch.testing.assert_close(losses.loss_pre_post_geometry, expected)
