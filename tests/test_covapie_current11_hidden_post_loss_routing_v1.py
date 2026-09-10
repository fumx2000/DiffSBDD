from __future__ import annotations

from dataclasses import fields, replace

import pytest
import torch
from Bio.PDB import Polypeptide as _polypeptide


if not hasattr(_polypeptide, "three_to_one"):
    _polypeptide.three_to_one = lambda name: (
        _polypeptide.protein_letters_3to1[name]
    )

from lightning_modules import LigandPocketDDPM
from covalent_ext import covapie_current11_training_lightning_module_v1 as subject
from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (
    AUXILIARY_ERROR,
    CovapieCurrent11AuxiliaryModelV1,
    CovapieCurrent11LossWeightsV1,
)
from covalent_ext.covapie_current11_training_lightning_module_v1 import (
    TRAINING_MODULE_ERROR,
    CovapieCurrent11DiffusionForwardTraceV1,
    CovapieCurrent11TrainingLigandPocketDDPM,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


LEGACY_PURPOSE = "existing_component_masks_v1"
HIDDEN_POST_PURPOSE = "independent_hidden_post_distance_v1"
POST = 1
LIGAND_BATCH_INDEX = torch.tensor([0, 0, 0, 1, 1, 1, 2, 2, 2])
POCKET_BATCH_INDEX = torch.tensor([0, 0, 1, 1, 2, 2])


def _supervision() -> CovapieCurrent11TrainingSupervisionTensorsV1:
    """Synthetic generated, fixed-B3, and generated-but-unrequested samples."""

    nan = float("nan")
    generation = torch.tensor(
        [
            [False], [False], [True],
            [True], [False], [False],
            [True], [True], [True],
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
        ligand_anchor_distance_angstrom=torch.arange(
            1.0, 10.0, dtype=torch.float32
        ).unsqueeze(1),
        ligand_anchor_distance_valid=torch.ones((9, 1), dtype=torch.bool),
        target_residue_membership_mask=torch.ones((6, 1), dtype=torch.bool),
        target_residue_reactive_atom_mask=torch.tensor(
            [[False], [True], [False], [True], [False], [True]]
        ),
        target_residue_reactive_atom_local_index=torch.tensor([1, 1, 1]),
        target_residue_reactive_atom_flat_index=torch.tensor([1, 3, 5]),
        target_residue_condition_valid=torch.tensor([True, True, True]),
        pair_candidate_offsets=torch.tensor([0, 4, 9, 12]),
        pair_candidate_batch_index=torch.tensor(
            [0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2]
        ),
        pair_candidate_ligand_local_index=torch.tensor(
            [0, 1, 2, 0, 0, 1, 0, 2, 2, 0, 2, 1]
        ),
        pair_candidate_residue_local_index=torch.tensor(
            [0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1]
        ),
        pair_candidate_ligand_flat_index=torch.tensor(
            [0, 1, 2, 0, 3, 4, 3, 5, 5, 6, 8, 7]
        ),
        pair_candidate_pocket_flat_index=torch.tensor(
            [0, 0, 1, 1, 2, 2, 3, 2, 3, 4, 5, 5]
        ),
        pair_candidate_is_positive=torch.tensor(
            [False, False, True, False, False, False, False, False, True,
             False, True, False]
        ),
        pair_candidate_is_negative=torch.tensor(
            [True, True, False, True, True, True, True, True, False,
             True, False, True]
        ),
        pair_positive_candidate_index=torch.tensor([2, 8, 10]),
        pair_positive_candidate_valid=torch.tensor([True, True, True]),
        pair_negative_count=torch.tensor([3, 4, 2]),
        pair_head_candidate_loss_mask=torch.tensor([True] * 12),
        pair_contrastive_sample_loss_mask=torch.tensor([False, False, False]),
        observed_complex_pair_distance_angstrom=torch.tensor(
            [[1.45], [2.05], [3.10]]
        ),
        observed_complex_pair_distance_valid=torch.tensor(
            [[True], [True], [True]]
        ),
        pre_post_geometry_target_angstrom=torch.tensor(
            [[nan, 7.25], [nan, 0.15], [nan, nan]]
        ),
        pre_post_geometry_component_valid_mask=geometry_valid,
        pre_post_geometry_component_loss_mask=geometry_valid.clone(),
    )


def _trace() -> CovapieCurrent11DiffusionForwardTraceV1:
    ligand_coordinates = torch.tensor(
        [
            [0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 2.0, 0.0],
            [0.0, 0.0, 1.0], [1.0, 1.0, 1.0], [2.0, 0.0, 1.0],
            [-1.0, 0.0, 0.0], [-1.0, 2.0, 0.0], [-2.0, 1.0, 2.0],
        ]
    )
    pocket_coordinates = torch.tensor(
        [
            [3.0, 0.0, 0.0], [0.0, 0.0, 1.0],
            [1.0, -1.0, 1.0], [2.0, 1.0, 0.0],
            [-2.0, 0.0, 0.0], [-2.0, 1.0, 0.0],
        ]
    )
    ligand_xh = torch.cat((ligand_coordinates, torch.zeros((9, 2))), dim=1)
    pocket_xh = torch.cat((pocket_coordinates, torch.zeros((6, 2))), dim=1)
    ligand_hidden = torch.arange(45, dtype=torch.float32).reshape(9, 5) / 17.0
    pocket_hidden = torch.arange(30, dtype=torch.float32).reshape(6, 5) / 13.0
    return CovapieCurrent11DiffusionForwardTraceV1(
        diffusion_epsilon_prediction_ligand=torch.zeros((9, 5)),
        diffusion_epsilon_prediction_pocket=torch.zeros((6, 5)),
        diffusion_timestep_int=torch.tensor([3, 5, 7]),
        noised_ligand_xh=ligand_xh.clone(),
        sampled_epsilon_ligand=torch.zeros((9, 5)),
        clean_centered_ligand_xh=ligand_xh.clone(),
        clean_centered_pocket_xh=pocket_xh,
        denoised_ligand_xh=ligand_xh,
        ligand_node_hidden=ligand_hidden,
        pocket_node_hidden=pocket_hidden,
        role_mask_anchor_hidden_delta=torch.zeros((9, 5)),
        ligand_coordinate_update_mask=torch.ones((9, 1), dtype=torch.bool),
        masked_t_gt_0_error_per_sample=torch.zeros(3),
        masked_t0_x_per_sample=torch.zeros(3),
        masked_t0_h_per_sample=torch.zeros(3),
        masked_kl_prior_per_sample=torch.zeros(3),
        base_objective_per_sample=torch.tensor([0.2, 0.4, 0.6]),
        coordinate_normalization=2.5,
    )


def _data() -> dict[str, object]:
    return {
        "lig_coords": torch.arange(27, dtype=torch.float32).reshape(9, 3),
        "lig_one_hot": torch.eye(5)[torch.tensor([0, 1, 2] * 3)],
        "num_lig_atoms": torch.tensor([3, 3, 3]),
        "lig_mask": LIGAND_BATCH_INDEX.clone(),
        "pocket_coords": torch.arange(18, dtype=torch.float32).reshape(6, 3),
        "pocket_one_hot": torch.eye(5)[torch.tensor([0, 1, 0, 1, 0, 1])],
        "num_pocket_nodes": torch.tensor([2, 2, 2]),
        "pocket_mask": POCKET_BATCH_INDEX.clone(),
        "covapie_current11_task2_runtime_result_v1": {"synthetic": True},
        "synthetic_authority": {"synthetic": True},
        # A batch string is never an authority for the keyword-only choice.
        "post_geometry_loss_purpose": HIDDEN_POST_PURPOSE,
    }


class _SyntheticForwardHarness:
    """Minimum CPU self for the real Current11.forward orchestration method."""

    forward = CovapieCurrent11TrainingLigandPocketDDPM.forward
    _shared_covapie_training_step_v1 = (
        CovapieCurrent11TrainingLigandPocketDDPM._shared_covapie_training_step_v1
    )
    training_step = CovapieCurrent11TrainingLigandPocketDDPM.training_step

    def __init__(
        self,
        *,
        supervision: CovapieCurrent11TrainingSupervisionTensorsV1 | None = None,
        training: bool = True,
    ) -> None:
        torch.manual_seed(73)
        self.training = training
        self.virtual_nodes = False
        self.device = torch.device("cpu")
        self.current_epoch = 0
        self.ddpm = object()
        self.covapie_current11_authoritative_supervision_batch_field = (
            "synthetic_authority"
        )
        self.covapie_current11_task_schedule_seed = 19
        self.covapie_current11_pair_contrastive_temperature = 1.0
        self.covapie_current11_loss_weights = CovapieCurrent11LossWeightsV1(
            base_diffusion=0.0,
            covalent_pair_prediction=0.0,
            pre_post_geometry=1.0,
            covalent_pair_contrastive=0.0,
        )
        self.covapie_current11_auxiliary_model_v1 = (
            CovapieCurrent11AuxiliaryModelV1(joint_nf=5)
        )
        self.supervision = _supervision() if supervision is None else supervision
        self.trace = _trace()
        self.transport_results: list[tuple[dict[str, object], dict[str, object]]] = []
        self.tensorizer_calls: list[dict[str, object]] = []
        self.bridge_calls: list[dict[str, object]] = []
        self.loss_calls: list[dict[str, object]] = []
        self.logged_metrics: list[tuple[object, ...]] = []

    def get_ligand_and_pocket(self, data: object):
        result = LigandPocketDDPM.get_ligand_and_pocket(self, data)
        self.transport_results.append(result)
        return result

    def log_metrics(self, *args: object, **kwargs: object) -> None:
        self.logged_metrics.append((*args, kwargs))


def _install_real_pipeline_with_stubbed_boundaries(
    monkeypatch: pytest.MonkeyPatch,
    harness: _SyntheticForwardHarness,
) -> None:
    real_loss = subject.compute_covapie_current11_training_losses_v1

    def tensorizer(**kwargs: object):
        harness.tensorizer_calls.append(kwargs)
        return harness.supervision

    def bridge(**kwargs: object):
        harness.bridge_calls.append(kwargs)
        return harness.trace

    def loss_spy(**kwargs: object):
        harness.loss_calls.append(kwargs)
        output = kwargs["model_output"]
        output.pre_post_geometry_predictions_angstrom.retain_grad()
        return real_loss(**kwargs)

    monkeypatch.setattr(
        subject, "tensorize_covapie_current11_training_supervision_v1", tensorizer
    )
    monkeypatch.setattr(
        subject,
        "run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1",
        bridge,
    )
    monkeypatch.setattr(
        subject, "compute_covapie_current11_training_losses_v1", loss_spy
    )


def _tensor_snapshot(value: object) -> dict[str, torch.Tensor]:
    return {
        field.name: getattr(value, field.name).clone()
        for field in fields(value)
        if isinstance(getattr(value, field.name), torch.Tensor)
    }


def _assert_snapshot(value: object, before: dict[str, torch.Tensor]) -> None:
    for name, expected in before.items():
        actual = getattr(value, name)
        if torch.is_floating_point(actual):
            torch.testing.assert_close(actual, expected, equal_nan=True)
        else:
            assert torch.equal(actual, expected)


def _smooth_l1(prediction: torch.Tensor, target: float) -> torch.Tensor:
    error = torch.abs(prediction - target)
    return torch.where(error < 1.0, 0.5 * error.square(), error - 0.5)


def test_real_forward_routes_scoped_purpose_masks_values_and_autograd(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = _SyntheticForwardHarness()
    _install_real_pipeline_with_stubbed_boundaries(monkeypatch, harness)
    data = _data()
    supervision_before = _tensor_snapshot(harness.supervision)
    data_before = {key: item.clone() for key, item in data.items()
                   if isinstance(item, torch.Tensor)}
    parameters_before = {
        name: parameter.detach().clone()
        for name, parameter in harness.covapie_current11_auxiliary_model_v1.named_parameters()
    }

    hidden_first = harness.forward(
        data, post_geometry_loss_purpose=HIDDEN_POST_PURPOSE
    )
    omitted = harness.forward(data)
    hidden_second = harness.forward(
        data, post_geometry_loss_purpose=HIDDEN_POST_PURPOSE
    )
    explicit_legacy = harness.forward(
        data, post_geometry_loss_purpose=LEGACY_PURPOSE
    )

    assert len(harness.loss_calls) == 4
    assert [call["post_geometry_loss_purpose"] for call in harness.loss_calls] == [
        HIDDEN_POST_PURPOSE,
        LEGACY_PURPOSE,
        HIDDEN_POST_PURPOSE,
        LEGACY_PURPOSE,
    ]
    outputs = (hidden_first, omitted, hidden_second, explicit_legacy)
    for index, (call, output) in enumerate(zip(harness.loss_calls, outputs)):
        ligand, pocket = harness.transport_results[index]
        assert call["ligand_batch_index"] is ligand["mask"]
        assert call["pocket_batch_index"] is pocket["mask"]
        assert call["supervision"] is output.supervision is harness.supervision
        assert call["diffusion_trace"] is output.diffusion_trace is harness.trace
        assert call["model_output"] is output.model_output
        assert harness.bridge_calls[index]["supervision"] is harness.supervision
        assert harness.bridge_calls[index]["role_mask_anchor_hidden_delta"] is (
            output.model_output.role_mask_anchor_hidden_delta
        )

    legacy_prediction = omitted.model_output.pre_post_geometry_predictions_angstrom
    expected_legacy = torch.stack(
        (_smooth_l1(legacy_prediction[2, POST], 7.25),
         _smooth_l1(legacy_prediction[8, POST], 0.15))
    ).mean()
    hidden_prediction = hidden_second.model_output.pre_post_geometry_predictions_angstrom
    expected_hidden = _smooth_l1(hidden_prediction[2, POST], 7.25)
    torch.testing.assert_close(
        omitted.loss_output.loss_pre_post_geometry, expected_legacy
    )
    torch.testing.assert_close(
        explicit_legacy.loss_output.loss_pre_post_geometry, expected_legacy
    )
    torch.testing.assert_close(
        hidden_first.loss_output.loss_pre_post_geometry, expected_hidden
    )
    torch.testing.assert_close(
        hidden_second.loss_output.loss_pre_post_geometry, expected_hidden
    )
    assert omitted.loss_output.pre_post_geometry_valid_sample_count == 2
    assert explicit_legacy.loss_output.pre_post_geometry_valid_sample_count == 2
    assert hidden_first.loss_output.pre_post_geometry_valid_sample_count == 1
    assert hidden_second.loss_output.pre_post_geometry_valid_sample_count == 1
    assert torch.isfinite(
        omitted.loss_output.pre_post_geometry_per_sample_detached[:2]
    ).all()
    assert torch.isnan(
        omitted.loss_output.pre_post_geometry_per_sample_detached[2]
    )
    assert torch.isfinite(
        hidden_second.loss_output.pre_post_geometry_per_sample_detached[0]
    )
    assert torch.isnan(
        hidden_second.loss_output.pre_post_geometry_per_sample_detached[1:]
    ).all()
    torch.testing.assert_close(
        hidden_first.loss_output.loss_pre_post_geometry,
        hidden_second.loss_output.loss_pre_post_geometry,
    )

    hidden_second.loss_output.loss_pre_post_geometry.backward()
    geometry_gradient = hidden_prediction.grad
    assert geometry_gradient is not None
    expected_gradient_support = torch.zeros((12, 2), dtype=torch.bool)
    expected_gradient_support[2, POST] = True
    assert torch.equal(geometry_gradient != 0, expected_gradient_support)
    _assert_snapshot(harness.supervision, supervision_before)
    for key, expected in data_before.items():
        assert torch.equal(data[key], expected)
    for name, parameter in harness.covapie_current11_auxiliary_model_v1.named_parameters():
        assert torch.equal(parameter.detach(), parameters_before[name])


def test_training_step_and_batch_string_keep_the_legacy_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = _SyntheticForwardHarness()
    _install_real_pipeline_with_stubbed_boundaries(monkeypatch, harness)
    data = _data()

    metrics = harness.training_step(data)

    assert harness.loss_calls[0]["post_geometry_loss_purpose"] == LEGACY_PURPOSE
    assert harness.loss_calls[0]["ligand_batch_index"] is (
        harness.transport_results[0][0]["mask"]
    )
    assert metrics["loss"] is harness.logged_metrics[0][0]["loss"]
    assert harness.logged_metrics[0][1] == "train"


@pytest.mark.parametrize(
    "purpose",
    (None, True, "", "INDEPENDENT_HIDDEN_POST_DISTANCE_V1",
     " independent_hidden_post_distance_v1",
     "independent_hidden_post_distance_v1 ", "unknown"),
)
def test_unknown_purpose_fails_before_every_computation_boundary(
    monkeypatch: pytest.MonkeyPatch,
    purpose: object,
) -> None:
    supervision = replace(
        _supervision(),
        pre_post_geometry_component_loss_mask=torch.zeros((3, 2), dtype=torch.bool),
    )
    harness = _SyntheticForwardHarness(supervision=supervision)
    _install_real_pipeline_with_stubbed_boundaries(monkeypatch, harness)

    with pytest.raises(ValueError, match=f"^{TRAINING_MODULE_ERROR}$"):
        harness.forward(_data(), post_geometry_loss_purpose=purpose)

    assert harness.transport_results == []
    assert harness.tensorizer_calls == []
    assert harness.bridge_calls == []
    assert harness.loss_calls == []


def test_evaluation_and_non_dictionary_rejections_remain_precomputation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evaluation = _SyntheticForwardHarness(training=False)
    _install_real_pipeline_with_stubbed_boundaries(monkeypatch, evaluation)
    with pytest.raises(ValueError, match=f"^{TRAINING_MODULE_ERROR}$"):
        evaluation.forward(
            _data(), post_geometry_loss_purpose=HIDDEN_POST_PURPOSE
        )
    assert evaluation.transport_results == []
    assert evaluation.tensorizer_calls == []

    training = _SyntheticForwardHarness()
    _install_real_pipeline_with_stubbed_boundaries(monkeypatch, training)
    with pytest.raises(ValueError, match=f"^{TRAINING_MODULE_ERROR}$"):
        training.forward([], post_geometry_loss_purpose=HIDDEN_POST_PURPOSE)
    assert training.transport_results == []
    assert training.tensorizer_calls == []


def test_real_loss_rejects_transport_node_membership_contradiction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = _SyntheticForwardHarness()
    _install_real_pipeline_with_stubbed_boundaries(monkeypatch, harness)
    data = _data()
    contradictory_ligand_batch = data["lig_mask"].clone()
    contradictory_ligand_batch[2] = 1
    data["lig_mask"] = contradictory_ligand_batch

    with pytest.raises(ValueError, match=f"^{TRAINING_MODULE_ERROR}$") as error:
        harness.forward(data, post_geometry_loss_purpose=HIDDEN_POST_PURPOSE)

    assert len(harness.transport_results) == 1
    assert len(harness.tensorizer_calls) == 1
    assert len(harness.bridge_calls) == 1
    assert len(harness.loss_calls) == 1
    assert harness.loss_calls[0]["post_geometry_loss_purpose"] == HIDDEN_POST_PURPOSE
    assert harness.loss_calls[0]["ligand_batch_index"] is (
        harness.transport_results[0][0]["mask"]
    )
    assert type(error.value.__cause__) is ValueError
    assert str(error.value.__cause__) == AUXILIARY_ERROR
