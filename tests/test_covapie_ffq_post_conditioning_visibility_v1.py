from __future__ import annotations

from dataclasses import fields, replace

import pytest
import torch

from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (
    CovapieCurrent11AuxiliaryModelV1,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


_LIGAND_BATCH_INDEX = torch.tensor([0, 0, 0, 0, 1, 1, 1, 1])
_GENERATED_NODE_INDICES = torch.tensor([0, 1, 4, 5])
_CANONICAL_TASK_NAMES = (
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
)


def _synthetic_supervision() -> CovapieCurrent11TrainingSupervisionTensorsV1:
    """Return two synthetic samples with every training/loss authority closed."""

    generation = torch.tensor(
        [[True], [True], [False], [False], [True], [True], [False], [False]]
    )
    fixed = ~generation
    empty_long = torch.empty(0, dtype=torch.long)
    empty_bool = torch.empty(0, dtype=torch.bool)
    false_by_sample = torch.zeros(2, dtype=torch.bool)
    false_by_node = torch.zeros((8, 1), dtype=torch.bool)
    false_geometry = torch.zeros((2, 2), dtype=torch.bool)
    return CovapieCurrent11TrainingSupervisionTensorsV1(
        sample_training_admitted=false_by_sample.clone(),
        canonical_task_id=torch.tensor([0, 3], dtype=torch.long),
        canonical_task_valid=torch.ones(2, dtype=torch.bool),
        ligand_role_id=torch.tensor([0, 1, 2, 0, 1, 2, 0, 1]),
        ligand_role_valid=torch.ones(8, dtype=torch.bool),
        ligand_base_generation_mask=generation,
        ligand_base_fixed_mask=fixed,
        ligand_base_target_mask=generation.clone(),
        ligand_base_context_mask=fixed.clone(),
        ligand_active_diffusion_loss_mask=false_by_node.clone(),
        ligand_minimal_seed_or_anchor_mask=false_by_node.clone(),
        ligand_minimal_seed_or_anchor_valid=false_by_sample.clone(),
        ligand_anchor_distance_angstrom=torch.tensor(
            [[1.0], [2.0], [4.0], [5.0], [2.0], [3.0], [4.0], [6.0]]
        ),
        ligand_anchor_distance_valid=torch.ones((8, 1), dtype=torch.bool),
        target_residue_membership_mask=torch.zeros((2, 1), dtype=torch.bool),
        target_residue_reactive_atom_mask=torch.zeros((2, 1), dtype=torch.bool),
        target_residue_reactive_atom_local_index=torch.full(
            (2,), -1, dtype=torch.long
        ),
        target_residue_reactive_atom_flat_index=torch.full(
            (2,), -1, dtype=torch.long
        ),
        target_residue_condition_valid=false_by_sample.clone(),
        pair_candidate_offsets=torch.zeros(3, dtype=torch.long),
        pair_candidate_batch_index=empty_long.clone(),
        pair_candidate_ligand_local_index=empty_long.clone(),
        pair_candidate_residue_local_index=empty_long.clone(),
        pair_candidate_ligand_flat_index=empty_long.clone(),
        pair_candidate_pocket_flat_index=empty_long.clone(),
        pair_candidate_is_positive=empty_bool.clone(),
        pair_candidate_is_negative=empty_bool.clone(),
        pair_positive_candidate_index=torch.full((2,), -1, dtype=torch.long),
        pair_positive_candidate_valid=false_by_sample.clone(),
        pair_negative_count=torch.zeros(2, dtype=torch.long),
        pair_head_candidate_loss_mask=empty_bool.clone(),
        pair_contrastive_sample_loss_mask=false_by_sample.clone(),
        observed_complex_pair_distance_angstrom=torch.tensor([[1.5], [2.5]]),
        observed_complex_pair_distance_valid=torch.ones((2, 1), dtype=torch.bool),
        pre_post_geometry_target_angstrom=torch.full((2, 2), float("nan")),
        pre_post_geometry_component_valid_mask=false_geometry.clone(),
        pre_post_geometry_component_loss_mask=false_geometry.clone(),
    )


def _assert_bounded_synthetic_contract(
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1,
) -> None:
    assert len(supervision.sample_training_admitted) == 2
    assert not bool(supervision.sample_training_admitted.any().item())
    assert not bool(supervision.ligand_active_diffusion_loss_mask.any().item())
    assert not bool(supervision.pair_head_candidate_loss_mask.any().item())
    assert not bool(supervision.pair_contrastive_sample_loss_mask.any().item())
    assert not bool(
        supervision.pre_post_geometry_component_loss_mask.any().item()
    )
    assert not bool(
        supervision.pre_post_geometry_component_valid_mask.any().item()
    )
    assert bool(
        torch.isnan(supervision.pre_post_geometry_target_angstrom).all().item()
    )
    generation = supervision.ligand_base_generation_mask
    fixed = supervision.ligand_base_fixed_mask
    assert generation.dtype == fixed.dtype == torch.bool
    assert generation.shape == fixed.shape == (8, 1)
    assert bool(generation.any().item())
    assert bool(fixed.any().item())
    assert not bool((generation & fixed).any().item())
    assert bool((generation ^ fixed).all().item())


def _fixed_nonzero_anchor_model() -> CovapieCurrent11AuxiliaryModelV1:
    model = CovapieCurrent11AuxiliaryModelV1(joint_nf=4)
    model.eval()
    with torch.no_grad():
        first = model.anchor_distance_encoder[0]
        final = model.anchor_distance_encoder[-1]
        assert isinstance(first, torch.nn.Linear)
        assert isinstance(final, torch.nn.Linear)
        first.weight.fill_(1.0)
        first.bias.zero_()
        final.weight.fill_(0.25)
        final.bias.zero_()
    assert bool((model.anchor_distance_encoder[0].weight != 0).all().item())
    assert bool((model.anchor_distance_encoder[-1].weight != 0).all().item())
    return model


def _fixed_nonzero_conditioning_model() -> CovapieCurrent11AuxiliaryModelV1:
    model = _fixed_nonzero_anchor_model()
    with torch.no_grad():
        model.role_embedding.weight.fill_(0.01)
        for task_id in range(5):
            model.task_embedding.weight[task_id].fill_(0.02 * (task_id + 1))
        model.generation_state_embedding.weight[0].fill_(0.03)
        model.generation_state_embedding.weight[1].fill_(0.04)
        model.seed_indicator_embedding.weight.fill_(0.05)
    return model


def _parameter_snapshot(
    model: CovapieCurrent11AuxiliaryModelV1,
) -> dict[str, torch.Tensor]:
    return {name: value.detach().clone() for name, value in model.named_parameters()}


def _assert_parameters_unchanged(
    model: CovapieCurrent11AuxiliaryModelV1,
    before: dict[str, torch.Tensor],
) -> None:
    after = dict(model.named_parameters())
    assert after.keys() == before.keys()
    for name, expected in before.items():
        assert torch.equal(after[name].detach(), expected), name
        assert after[name].grad is None, name


def _supervision_snapshot(
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1,
) -> dict[str, torch.Tensor]:
    return {
        field.name: getattr(supervision, field.name).detach().clone()
        for field in fields(supervision)
    }


def _assert_supervision_unchanged(
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1,
    before: dict[str, torch.Tensor],
) -> None:
    for name, expected in before.items():
        actual = getattr(supervision, name)
        if torch.is_floating_point(actual):
            torch.testing.assert_close(
                actual, expected, rtol=0, atol=0, equal_nan=True
            )
        else:
            assert torch.equal(actual, expected), name


def _encode(
    model: CovapieCurrent11AuxiliaryModelV1,
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1,
) -> torch.Tensor:
    with torch.no_grad():
        return model.encode_role_mask_anchor_v1(
            supervision=supervision,
            ligand_batch_index=_LIGAND_BATCH_INDEX,
        )


def _replace_only_anchor_distance(
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1,
    distance: torch.Tensor,
) -> CovapieCurrent11TrainingSupervisionTensorsV1:
    changed = replace(
        supervision,
        ligand_anchor_distance_angstrom=distance,
    )
    for field in fields(supervision):
        if field.name != "ligand_anchor_distance_angstrom":
            assert getattr(changed, field.name) is getattr(supervision, field.name)
    return changed


def test_zero_initialization_control_is_exact_zero_after_distance_change() -> None:
    supervision = _synthetic_supervision()
    _assert_bounded_synthetic_contract(supervision)
    changed_distance = supervision.ligand_anchor_distance_angstrom.clone()
    changed_distance[0, 0] = 3.0
    changed = _replace_only_anchor_distance(supervision, changed_distance)
    model = CovapieCurrent11AuxiliaryModelV1(joint_nf=4)
    model.eval()
    parameters_before = _parameter_snapshot(model)

    baseline_delta = _encode(model, supervision)
    changed_delta = _encode(model, changed)

    assert torch.equal(baseline_delta, torch.zeros_like(baseline_delta))
    assert torch.equal(changed_delta, torch.zeros_like(changed_delta))
    assert torch.equal(baseline_delta, changed_delta)
    _assert_parameters_unchanged(model, parameters_before)


def test_generated_finite_perturbation_is_hidden_with_other_embeddings_active() -> None:
    supervision = _synthetic_supervision()
    _assert_bounded_synthetic_contract(supervision)
    changed_distance = supervision.ligand_anchor_distance_angstrom.clone()
    changed_distance[0, 0] = 3.0
    assert int(
        torch.count_nonzero(
            changed_distance != supervision.ligand_anchor_distance_angstrom
        ).item()
    ) == 1
    assert bool(supervision.ligand_base_generation_mask[0, 0].item())
    changed = _replace_only_anchor_distance(supervision, changed_distance)
    model = _fixed_nonzero_conditioning_model()
    parameters_before = _parameter_snapshot(model)

    baseline_delta = _encode(model, supervision)
    changed_delta = _encode(model, changed)

    assert torch.isfinite(baseline_delta).all()
    assert torch.isfinite(changed_delta).all()
    assert torch.equal(baseline_delta, changed_delta)
    assert bool((baseline_delta[0] != 0).all().item())
    assert bool((baseline_delta[_GENERATED_NODE_INDICES] != 0).all().item())
    assert not torch.equal(
        model.anchor_distance_encoder[-1].weight,
        torch.zeros_like(model.anchor_distance_encoder[-1].weight),
    )
    _assert_parameters_unchanged(model, parameters_before)


def test_production_encoder_hides_every_generated_anchor_value_and_invalid_numeric() -> None:
    supervision = _synthetic_supervision()
    _assert_bounded_synthetic_contract(supervision)
    original_distance = supervision.ligand_anchor_distance_angstrom.clone()
    original_valid = supervision.ligand_anchor_distance_valid.clone()
    supervision_before = _supervision_snapshot(supervision)
    generation_mask = supervision.ligand_base_generation_mask
    model = _fixed_nonzero_conditioning_model()
    parameters_before = _parameter_snapshot(model)

    finite_perturbation = original_distance.clone()
    finite_perturbation[generation_mask] += torch.tensor([10.0, 20.0, 30.0, 40.0])
    assert bool(torch.isfinite(finite_perturbation[generation_mask]).all().item())
    assert bool(
        (finite_perturbation[generation_mask] != original_distance[generation_mask])
        .all()
        .item()
    )
    finite_changed = _replace_only_anchor_distance(
        supervision, finite_perturbation
    )
    invalid_perturbation = original_distance.clone()
    invalid_perturbation[generation_mask] = torch.tensor(
        [float("nan"), float("inf"), float("-inf"), -10.0]
    )
    invalid_changed = _replace_only_anchor_distance(
        supervision, invalid_perturbation
    )

    baseline_delta = _encode(model, supervision)
    finite_delta = _encode(model, finite_changed)
    invalid_delta = _encode(model, invalid_changed)

    assert torch.isfinite(baseline_delta).all()
    assert torch.isfinite(finite_delta).all()
    assert torch.isfinite(invalid_delta).all()
    assert torch.equal(baseline_delta, finite_delta)
    assert torch.equal(baseline_delta, invalid_delta)
    assert bool((baseline_delta[_GENERATED_NODE_INDICES] != 0).all().item())
    torch.testing.assert_close(
        supervision.ligand_anchor_distance_angstrom,
        original_distance,
        equal_nan=True,
    )
    assert torch.equal(supervision.ligand_anchor_distance_valid, original_valid)
    _assert_supervision_unchanged(supervision, supervision_before)
    _assert_parameters_unchanged(model, parameters_before)


def test_production_encoder_retains_visible_fixed_context_and_sample_isolation() -> None:
    supervision = _synthetic_supervision()
    _assert_bounded_synthetic_contract(supervision)
    original_distance = supervision.ligand_anchor_distance_angstrom.clone()
    original_valid = supervision.ligand_anchor_distance_valid.clone()
    changed_distance = original_distance.clone()
    changed_distance[2, 0] = 8.0
    assert bool(supervision.ligand_base_fixed_mask[2, 0].item())
    changed = _replace_only_anchor_distance(supervision, changed_distance)
    model = _fixed_nonzero_anchor_model()
    parameters_before = _parameter_snapshot(model)

    baseline_delta = _encode(model, supervision)
    changed_delta = _encode(model, changed)

    torch.testing.assert_close(
        baseline_delta[2], torch.full((4,), 1.34119826), rtol=1e-6, atol=1e-7
    )
    torch.testing.assert_close(
        changed_delta[2], torch.full((4,), 1.97750212), rtol=1e-6, atol=1e-7
    )
    assert not torch.equal(baseline_delta[2], changed_delta[2])
    unchanged_nodes = torch.tensor([0, 1, 3, 4, 5, 6, 7])
    assert torch.equal(
        baseline_delta[unchanged_nodes], changed_delta[unchanged_nodes]
    )
    assert torch.equal(baseline_delta[4:], changed_delta[4:])
    torch.testing.assert_close(
        supervision.ligand_anchor_distance_angstrom,
        original_distance,
        equal_nan=True,
    )
    assert torch.equal(supervision.ligand_anchor_distance_valid, original_valid)
    _assert_parameters_unchanged(model, parameters_before)


def test_fixed_row_with_original_valid_false_remains_hidden() -> None:
    supervision = _synthetic_supervision()
    anchor_valid = supervision.ligand_anchor_distance_valid.clone()
    anchor_valid[2, 0] = False
    hidden = replace(supervision, ligand_anchor_distance_valid=anchor_valid)
    changed_distance = hidden.ligand_anchor_distance_angstrom.clone()
    changed_distance[2, 0] = float("nan")
    changed = _replace_only_anchor_distance(hidden, changed_distance)
    model = _fixed_nonzero_conditioning_model()
    parameters_before = _parameter_snapshot(model)

    baseline_delta = _encode(model, hidden)
    changed_delta = _encode(model, changed)

    assert bool(supervision.ligand_base_fixed_mask[2, 0].item())
    assert not bool(hidden.ligand_anchor_distance_valid[2, 0].item())
    assert torch.equal(baseline_delta, changed_delta)
    assert torch.isfinite(changed_delta).all()
    assert bool((changed_delta[2] != 0).all().item())
    _assert_parameters_unchanged(model, parameters_before)


def test_neither_fixed_nor_generated_row_does_not_gain_anchor_visibility() -> None:
    supervision = _synthetic_supervision()
    fixed = supervision.ligand_base_fixed_mask.clone()
    generation = supervision.ligand_base_generation_mask.clone()
    fixed[2, 0] = False
    generation[2, 0] = False
    hidden = replace(
        supervision,
        ligand_base_fixed_mask=fixed,
        ligand_base_generation_mask=generation,
    )
    changed_distance = hidden.ligand_anchor_distance_angstrom.clone()
    changed_distance[2, 0] = float("-inf")
    changed = _replace_only_anchor_distance(hidden, changed_distance)
    model = _fixed_nonzero_conditioning_model()

    baseline_delta = _encode(model, hidden)
    changed_delta = _encode(model, changed)

    assert not bool(fixed[2, 0].item())
    assert not bool(generation[2, 0].item())
    assert bool(hidden.ligand_anchor_distance_valid[2, 0].item())
    assert torch.equal(baseline_delta, changed_delta)
    assert torch.isfinite(changed_delta).all()
    assert bool((changed_delta[2] != 0).all().item())


def test_all_generated_skips_anchor_encoder_but_keeps_other_conditioning() -> None:
    supervision = _synthetic_supervision()
    all_generated = replace(
        supervision,
        ligand_base_fixed_mask=torch.zeros((8, 1), dtype=torch.bool),
        ligand_base_generation_mask=torch.ones((8, 1), dtype=torch.bool),
        ligand_anchor_distance_angstrom=torch.tensor(
            [
                [float("nan")],
                [float("inf")],
                [float("-inf")],
                [-1.0],
                [float("nan")],
                [float("inf")],
                [float("-inf")],
                [-2.0],
            ]
        ),
    )
    before = _supervision_snapshot(all_generated)
    model = _fixed_nonzero_conditioning_model()
    parameters_before = _parameter_snapshot(model)
    encoder_inputs: list[torch.Tensor] = []

    def observe_encoder_input(
        _module: torch.nn.Module, inputs: tuple[torch.Tensor, ...]
    ) -> None:
        encoder_inputs.append(inputs[0].detach().clone())

    handle = model.anchor_distance_encoder.register_forward_pre_hook(
        observe_encoder_input
    )
    try:
        delta = _encode(model, all_generated)
    finally:
        handle.remove()

    assert encoder_inputs == []
    assert torch.isfinite(delta).all()
    assert bool((delta != 0).all().item())
    _assert_supervision_unchanged(all_generated, before)
    _assert_parameters_unchanged(model, parameters_before)


@pytest.mark.parametrize(
    "field_name",
    (
        "ligand_anchor_distance_valid",
        "ligand_base_fixed_mask",
        "ligand_base_generation_mask",
    ),
)
def test_anchor_visibility_masks_require_bool_before_use(field_name: str) -> None:
    supervision = _synthetic_supervision()
    invalid = replace(
        supervision,
        **{field_name: torch.ones((8, 1), dtype=torch.int64)},
    )

    with pytest.raises(ValueError, match="^COVAPIE_CURRENT11_AUXILIARY_MODEL_AND_LOSS_V1_ERROR$"):
        _encode(_fixed_nonzero_anchor_model(), invalid)


@pytest.mark.parametrize(
    "field_name",
    (
        "ligand_anchor_distance_valid",
        "ligand_base_fixed_mask",
        "ligand_base_generation_mask",
    ),
)
def test_anchor_visibility_masks_require_exact_l_by_one_shape(
    field_name: str,
) -> None:
    supervision = _synthetic_supervision()
    invalid = replace(
        supervision,
        **{field_name: torch.ones(8, dtype=torch.bool)},
    )

    with pytest.raises(ValueError, match="^COVAPIE_CURRENT11_AUXILIARY_MODEL_AND_LOSS_V1_ERROR$"):
        _encode(_fixed_nonzero_anchor_model(), invalid)


@pytest.mark.parametrize(
    "field_name",
    (
        "ligand_anchor_distance_valid",
        "ligand_base_fixed_mask",
        "ligand_base_generation_mask",
        "ligand_anchor_distance_angstrom",
    ),
)
def test_anchor_visibility_inputs_must_share_ligand_device(
    field_name: str,
) -> None:
    supervision = _synthetic_supervision()
    invalid = replace(
        supervision,
        **{field_name: getattr(supervision, field_name).to("meta")},
    )

    with pytest.raises(ValueError, match="^COVAPIE_CURRENT11_AUXILIARY_MODEL_AND_LOSS_V1_ERROR$"):
        _encode(_fixed_nonzero_anchor_model(), invalid)


@pytest.mark.parametrize(
    "distance",
    (
        torch.ones((8, 1), dtype=torch.int64),
        torch.ones(8),
        torch.ones((7, 1)),
    ),
    ids=("non_floating", "one_dimensional", "wrong_ligand_count"),
)
def test_anchor_distance_requires_floating_l_by_one_tensor(
    distance: torch.Tensor,
) -> None:
    supervision = replace(
        _synthetic_supervision(),
        ligand_anchor_distance_angstrom=distance,
    )

    with pytest.raises(ValueError, match="^COVAPIE_CURRENT11_AUXILIARY_MODEL_AND_LOSS_V1_ERROR$"):
        _encode(_fixed_nonzero_anchor_model(), supervision)


def test_fixed_and_generation_overlap_is_rejected() -> None:
    supervision = _synthetic_supervision()
    fixed = supervision.ligand_base_fixed_mask.clone()
    fixed[0, 0] = True
    invalid = replace(supervision, ligand_base_fixed_mask=fixed)

    with pytest.raises(ValueError, match="^COVAPIE_CURRENT11_AUXILIARY_MODEL_AND_LOSS_V1_ERROR$"):
        _encode(_fixed_nonzero_anchor_model(), invalid)


@pytest.mark.parametrize("invalid_value", (float("nan"), float("inf"), -1.0))
def test_visible_fixed_anchor_rejects_invalid_numeric(
    invalid_value: float,
) -> None:
    supervision = _synthetic_supervision()
    distance = supervision.ligand_anchor_distance_angstrom.clone()
    distance[2, 0] = invalid_value
    invalid = _replace_only_anchor_distance(supervision, distance)

    with pytest.raises(ValueError, match="^COVAPIE_CURRENT11_AUXILIARY_MODEL_AND_LOSS_V1_ERROR$"):
        _encode(_fixed_nonzero_anchor_model(), invalid)


def test_all_five_canonical_task_ids_use_the_same_anchor_visibility_rule() -> None:
    supervision = _synthetic_supervision()
    ligand_batch_index = torch.arange(5, dtype=torch.long).repeat_interleave(2)
    generation = torch.tensor([[True], [False]] * 5)
    fixed = ~generation
    distance = torch.tensor(
        [[1.0], [2.0], [2.0], [2.0], [3.0], [2.0], [4.0], [2.0], [5.0], [2.0]]
    )
    five_tasks = replace(
        supervision,
        canonical_task_id=torch.arange(5, dtype=torch.long),
        canonical_task_valid=torch.ones(5, dtype=torch.bool),
        ligand_role_id=torch.zeros(10, dtype=torch.long),
        ligand_role_valid=torch.ones(10, dtype=torch.bool),
        ligand_base_generation_mask=generation,
        ligand_base_fixed_mask=fixed,
        ligand_minimal_seed_or_anchor_mask=torch.zeros((10, 1), dtype=torch.bool),
        ligand_minimal_seed_or_anchor_valid=torch.zeros(5, dtype=torch.bool),
        ligand_anchor_distance_angstrom=distance,
        ligand_anchor_distance_valid=torch.ones((10, 1), dtype=torch.bool),
    )
    generated_changed_distance = distance.clone()
    generated_changed_distance[generation] = torch.tensor(
        [float("nan"), float("inf"), float("-inf"), -1.0, -2.0]
    )
    generated_changed = _replace_only_anchor_distance(
        five_tasks, generated_changed_distance
    )
    fixed_changed_distance = distance.clone()
    fixed_changed_distance[fixed] += 3.0
    fixed_changed = _replace_only_anchor_distance(five_tasks, fixed_changed_distance)
    model = _fixed_nonzero_conditioning_model()

    with torch.no_grad():
        baseline_delta = model.encode_role_mask_anchor_v1(
            supervision=five_tasks,
            ligand_batch_index=ligand_batch_index,
        )
        generated_delta = model.encode_role_mask_anchor_v1(
            supervision=generated_changed,
            ligand_batch_index=ligand_batch_index,
        )
        fixed_delta = model.encode_role_mask_anchor_v1(
            supervision=fixed_changed,
            ligand_batch_index=ligand_batch_index,
        )

    assert _CANONICAL_TASK_NAMES[3] == "scaffold_only"
    assert len(_CANONICAL_TASK_NAMES) == 5
    assert torch.equal(baseline_delta, generated_delta)
    assert torch.equal(baseline_delta[generation[:, 0]], fixed_delta[generation[:, 0]])
    assert bool(
        (baseline_delta[fixed[:, 0]] != fixed_delta[fixed[:, 0]]).all().item()
    )


def test_observed_distance_diagnostic_is_not_consumed_by_anchor_encoder() -> None:
    supervision = _synthetic_supervision()
    _assert_bounded_synthetic_contract(supervision)
    changed = replace(
        supervision,
        observed_complex_pair_distance_angstrom=torch.tensor([[999.0], [777.0]]),
    )
    assert (
        changed.ligand_anchor_distance_angstrom
        is supervision.ligand_anchor_distance_angstrom
    )
    assert (
        changed.ligand_anchor_distance_valid
        is supervision.ligand_anchor_distance_valid
    )
    model = _fixed_nonzero_anchor_model()
    parameters_before = _parameter_snapshot(model)

    baseline_delta = _encode(model, supervision)
    changed_delta = _encode(model, changed)

    assert torch.equal(baseline_delta, changed_delta)
    assert torch.isfinite(changed_delta).all()
    _assert_parameters_unchanged(model, parameters_before)
