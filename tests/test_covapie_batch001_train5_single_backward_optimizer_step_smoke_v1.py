from __future__ import annotations

from dataclasses import fields
import math
from pathlib import Path

import pytest
import torch
from torch import nn

from covalent_ext import (
    covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1
    as predecessor,
)
from covalent_ext import (
    covapie_batch001_train5_single_backward_optimizer_step_smoke_v1
    as subject,
)
from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (
    CovapieCurrent11LossOutputV1,
    CovapieCurrent11LossWeightsV1,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT.parent / "covapie-state"
CACHE = STATE / "bulk-multisource-cys-sg-v1/rcsb"
CHECKPOINT = ROOT / "checkpoints/crossdocked_fullatom_cond.ckpt"
ERROR = subject.BATCH001_TRAIN5_SINGLE_BACKWARD_OPTIMIZER_STEP_SMOKE_ERROR_V1


def _assert_public_error(callable_object, reason: str) -> None:
    with pytest.raises(ValueError) as captured:
        callable_object()
    assert str(captured.value) == f"{ERROR}:{reason}"


def _assert_internal_error(callable_object, reason: str) -> None:
    with pytest.raises(subject._SmokeInvariantError) as captured:
        callable_object()
    assert captured.value.reason == reason


@pytest.fixture(scope="module")
def authority():
    return predecessor.audit_covapie_batch001_train5_formal_authority_v1(
        repository_root=ROOT
    )


@pytest.fixture(scope="module")
def prepared():
    return predecessor._prepare_train5_batch(
        repository_root=ROOT,
        cache_root=CACHE,
        requested_sample_identities=None,
    )


@pytest.fixture(scope="module")
def real_smoke_result(
) -> subject.CovapieBatch001Train5SingleBackwardOptimizerStepSmokeResultV1:
    return subject.run_covapie_batch001_train5_single_backward_optimizer_step_smoke_v1(
        repository_root=ROOT,
        state_root=STATE,
        cache_root=CACHE,
        checkpoint_path=CHECKPOINT,
    )


def test_exact_formal_train5_and_model_input_population(authority, prepared) -> None:
    assert authority.formal_train_event_ids == predecessor.FORMAL_TRAIN_EVENT_IDS_V1
    assert authority.DJK_train_event_count == 2
    assert authority.PTG_train_event_count == 3
    assert len(authority.formal_validation_event_ids) == 4
    assert len(authority.formal_unresolved_event_ids) == 4
    assert len(authority.non_target_component_event_ids) == 21
    assert prepared.sample_identities == predecessor.FORMAL_TRAIN_EVENT_IDS_V1
    assert prepared.scheduled_task_ids == (4, 4, 2, 0, 4)
    assert sum(
        len(record.ligand_retained_heavy_atoms)
        for record in prepared.structural_records
    ) == 115
    assert sum(
        len(record.pocket_retained_heavy_atoms)
        for record in prepared.structural_records
    ) == 578
    assert len(prepared.supervision.pair_candidate_batch_index) == 690
    assert int(prepared.supervision.pair_candidate_is_positive.sum().item()) == 5
    assert int(prepared.supervision.pair_candidate_is_negative.sum().item()) == 685
    assert isinstance(
        prepared.supervision, CovapieCurrent11TrainingSupervisionTensorsV1
    )
    assert len(fields(CovapieCurrent11TrainingSupervisionTensorsV1)) == 37
    assert prepared.preview_supervision.sample_training_admitted.tolist() == [False] * 5
    assert prepared.supervision.sample_training_admitted.tolist() == [True] * 5


@pytest.mark.parametrize("excluded_group", ("VALIDATION", "NDU", "NON_TARGET"))
def test_validation_unresolved_and_non_target_events_fail_closed(
    authority, excluded_group: str,
) -> None:
    replacement = {
        "VALIDATION": authority.formal_validation_event_ids[0],
        "NDU": authority.formal_unresolved_event_ids[0],
        "NON_TARGET": authority.non_target_component_event_ids[0],
    }[excluded_group]
    requested = (replacement,) + authority.formal_train_event_ids[1:]
    _assert_public_error(
        lambda: subject.run_covapie_batch001_train5_single_backward_optimizer_step_smoke_v1(
            repository_root=ROOT,
            state_root=STATE,
            cache_root=CACHE,
            checkpoint_path=CHECKPOINT,
            requested_sample_identities=requested,
        ),
        "ONLY_EXACT_FORMALLY_ADMITTED_TRAIN5_MAY_BE_SMOKE_ACTIVATED",
    )


def test_bound_predecessor_and_owner_sha256_are_exact(real_smoke_result) -> None:
    assert real_smoke_result.bound_source_sha256 == subject.ALL_BOUND_SOURCE_SHA256_V1
    assert dict(real_smoke_result.bound_source_sha256) == {
        str(subject.PREDECESSOR_SOURCE_RELATIVE_PATH_V1): subject.PREDECESSOR_SOURCE_SHA256_V1,
        str(subject.PREDECESSOR_CHECKER_RELATIVE_PATH_V1): subject.PREDECESSOR_CHECKER_SHA256_V1,
        str(subject.PREDECESSOR_TEST_RELATIVE_PATH_V1): subject.PREDECESSOR_TEST_SHA256_V1,
        **dict(subject.BOUND_OWNER_SHA256_V1),
    }
    assert real_smoke_result.checkpoint_sha256_before == predecessor.CHECKPOINT_SHA256_V1
    assert real_smoke_result.checkpoint_sha256_after == predecessor.CHECKPOINT_SHA256_V1


def test_smoke_only_geometry_weights_and_total_formula(real_smoke_result) -> None:
    result = real_smoke_result
    losses = dict(result.runtime_losses)
    assert dict(result.published_default_loss_weights) == {
        "base_diffusion": 1.0,
        "covalent_pair_prediction": 1.0,
        "pre_post_geometry": 0.0,
        "covalent_pair_contrastive": 0.1,
    }
    assert dict(result.smoke_only_loss_weights) == {
        "base_diffusion": 1.0,
        "covalent_pair_prediction": 1.0,
        "pre_post_geometry": 1.0,
        "covalent_pair_contrastive": 0.1,
    }
    assert all(math.isfinite(value) for value in losses.values())
    expected = (
        losses["loss_base_diffusion"]
        + losses["loss_covalent_pair_prediction"]
        + losses["loss_pre_post_geometry"]
        + 0.1 * losses["loss_covalent_pair_contrastive"]
    )
    assert result.weighted_total_formula_value == pytest.approx(expected)
    assert losses["loss_total"] == pytest.approx(expected)
    assert result.weighted_total_formula_absolute_difference <= 1.0e-7
    assert result.geometry_contribution_to_smoke_total == losses[
        "loss_pre_post_geometry"
    ]
    assert result.geometry_contribution_to_smoke_total > 0.0
    assert result.base_diffusion_valid_sample_count == 5
    assert result.covalent_pair_prediction_valid_sample_count == 5
    assert result.pre_post_geometry_valid_sample_count == 5
    assert result.covalent_pair_contrastive_valid_sample_count == 5
    assert result.PRE_geometry_valid_sample_count == 0
    assert result.published_default_modified is False


def test_optimizer_owner_coverage_and_exactly_once_counts(real_smoke_result) -> None:
    result = real_smoke_result
    optimizer = result.optimizer_metadata
    assert optimizer.optimizer_type == "AdamW"
    assert optimizer.amsgrad is True
    assert optimizer.weight_decay == 1.0e-12
    assert optimizer.model_lr == 0.001
    assert optimizer.optimizer_param_group_lrs == (optimizer.model_lr,)
    assert optimizer.model_parameter_tensor_count == 135
    assert optimizer.optimizer_parameter_tensor_count == 135
    assert optimizer.optimizer_unique_parameter_count == 135
    assert optimizer.optimizer_parameter_set_exact is True
    assert result.backward_call_count == 1
    assert result.optimizer_step_count == 1
    assert result.gradient_clipping_performed is False
    assert result.scheduler_step_performed is False


def test_all_required_gradient_groups_are_finite_and_nonzero(real_smoke_result) -> None:
    groups = {item.group_name: item for item in real_smoke_result.gradient_group_stats}
    assert set(groups) == {
        "ALL_PARAMETERS",
        "SHARED_PRETRAINED",
        "TARGET_RESIDUE_CONDITIONING",
        "ROLE_TASK_MASK_ANCHOR",
        "PAIR_HEAD",
        "GEOMETRY_HEAD",
    }
    assert groups["ALL_PARAMETERS"].parameter_tensor_count == 135
    assert groups["SHARED_PRETRAINED"].parameter_tensor_count == 116
    assert groups["TARGET_RESIDUE_CONDITIONING"].parameter_tensor_count == 1
    for stats in groups.values():
        assert stats.gradient_tensor_count > 0
        assert stats.nonzero_gradient_tensor_count > 0
        assert stats.gradient_l2_norm > 0.0
        assert stats.gradient_max_abs > 0.0
        assert stats.all_gradients_finite is True


def test_post_only_final_geometry_rows_are_exact(real_smoke_result) -> None:
    component = real_smoke_result.geometry_component_gradient
    assert component.final_weight_parameter_name == subject.GEOMETRY_FINAL_WEIGHT_NAME_V1
    assert component.final_bias_parameter_name == subject.GEOMETRY_FINAL_BIAS_NAME_V1
    assert component.PRE_weight_row_l2_norm == 0.0
    assert component.PRE_bias_gradient_abs == 0.0
    assert component.POST_weight_row_l2_norm > 0.0
    assert component.POST_bias_gradient_abs > 0.0
    assert component.PRE_output_component_gradient_exact_zero is True
    assert component.POST_output_component_gradient_finite_nonzero is True


def test_all_required_parameter_groups_change_safely(real_smoke_result) -> None:
    result = real_smoke_result
    groups = {
        item.group_name: item for item in result.parameter_delta_group_stats
    }
    assert set(groups) == {
        "ALL_PARAMETERS",
        "SHARED_PRETRAINED",
        "NEW_COVAPIE",
        "TARGET_RESIDUE_CONDITIONING",
        "ROLE_TASK_MASK_ANCHOR",
        "PAIR_HEAD",
        "GEOMETRY_HEAD",
    }
    for stats in groups.values():
        assert stats.changed_parameter_tensor_count > 0
        assert stats.parameter_delta_l2 > 0.0
        assert stats.parameter_delta_max_abs > 0.0
        assert stats.all_parameters_finite is True
    assert groups["TARGET_RESIDUE_CONDITIONING"].relative_delta_l2 is None
    for group_name in (
        "SHARED_PRETRAINED",
        "ROLE_TASK_MASK_ANCHOR",
        "PAIR_HEAD",
        "GEOMETRY_HEAD",
    ):
        assert groups[group_name].relative_delta_l2 is not None
        assert groups[group_name].relative_delta_l2 > 0.0
    assert result.all_parameters_finite_after_step is True
    assert result.in_memory_model_parameters_changed is True
    assert len(result.parameter_snapshots) == 135
    assert len({item.name for item in result.parameter_snapshots}) == 135
    assert all(item.initial_finite for item in result.parameter_snapshots)


def test_safety_and_interpretation_flags_do_not_overclaim(real_smoke_result) -> None:
    result = real_smoke_result
    assert result.implementation_status == "passed"
    assert result.result_interpretation == (
        "geometry_weight_candidate_validated_for_single_step_smoke"
    )
    assert result.validation_event_backward_count == 0
    assert result.unresolved_event_backward_count == 0
    assert result.non_target_component_event_backward_count == 0
    assert result.checkpoint_file_changed is False
    assert result.repository_predecessor_files_changed is False
    assert result.persistent_output_written is False
    assert result.checkpoint_saved is False
    assert result.model_saved is False
    assert result.Trainer_used is False
    assert result.GPU_used is False
    assert result.geometry_weight_candidate_validated_for_single_step_smoke is True
    assert result.geometry_weight_optimal is False
    assert result.production_geometry_weight_finalized is False
    assert result.ready_for_bounded_batch001_train5_trainer_fit_smoke is True
    assert result.ready_for_full_training is False


def test_wrong_geometry_candidate_and_mutated_default_fail_closed() -> None:
    wrong = CovapieCurrent11LossWeightsV1(pre_post_geometry=0.5)
    _assert_public_error(
        lambda: subject.run_covapie_batch001_train5_single_backward_optimizer_step_smoke_v1(
            repository_root=ROOT,
            state_root=STATE,
            cache_root=CACHE,
            checkpoint_path=CHECKPOINT,
            smoke_loss_weights=wrong,
        ),
        "SMOKE_ONLY_GEOMETRY_WEIGHT_CANDIDATE_INVALID",
    )
    mutated_default = CovapieCurrent11LossWeightsV1(pre_post_geometry=1.0)
    _assert_internal_error(
        lambda: subject._validate_loss_weight_policy(
            None, published_default=mutated_default
        ),
        "PUBLISHED_DEFAULT_LOSS_WEIGHTS_MUTATED",
    )


def test_wrong_formal_predecessor_and_checkpoint_sha_fail_closed(tmp_path: Path) -> None:
    corrupted = tmp_path / "corrupted"
    corrupted.write_bytes(b"not-published-evidence\n")
    _assert_public_error(
        lambda: subject.verify_covapie_batch001_train5_single_backward_predecessor_source_v1(
            predecessor_source_path=corrupted
        ),
        "PREDECESSOR_SOURCE_SHA256_MISMATCH",
    )
    with pytest.raises(ValueError):
        predecessor.verify_covapie_batch001_train5_formal_authority_file_v1(
            formal_authority_path=corrupted
        )
    with pytest.raises(ValueError):
        predecessor.verify_covapie_batch001_train5_checkpoint_file_v1(
            checkpoint_path=corrupted
        )
    _assert_internal_error(
        lambda: subject._require_unchanged_evidence(
            "checkpoint-before", "checkpoint-after", "CHECKPOINT_CHANGED"
        ),
        "CHECKPOINT_CHANGED",
    )


class _TwoParameterModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.first = nn.Parameter(torch.ones(1))
        self.second = nn.Parameter(torch.ones(1))
        self.lr = 0.001


def test_optimizer_missing_and_duplicate_parameters_fail_closed() -> None:
    missing_model = _TwoParameterModel()
    missing = torch.optim.AdamW(
        [missing_model.first], lr=missing_model.lr, amsgrad=True, weight_decay=1.0e-12
    )
    _assert_internal_error(
        lambda: subject._validate_optimizer_parameter_coverage(
            missing_model, missing
        ),
        "OPTIMIZER_PARAMETER_SET_NOT_EXACT",
    )
    duplicate_model = _TwoParameterModel()
    duplicate = torch.optim.AdamW(
        duplicate_model.parameters(),
        lr=duplicate_model.lr,
        amsgrad=True,
        weight_decay=1.0e-12,
    )
    duplicate.param_groups[0]["params"].append(duplicate_model.first)
    _assert_internal_error(
        lambda: subject._validate_optimizer_parameter_coverage(
            duplicate_model, duplicate
        ),
        "OPTIMIZER_PARAMETER_SET_NOT_EXACT",
    )


def _synthetic_loss_output(total: torch.Tensor) -> CovapieCurrent11LossOutputV1:
    finite = torch.tensor(1.0, requires_grad=True)
    diagnostic = torch.ones(5)
    return CovapieCurrent11LossOutputV1(
        loss_base_diffusion=finite,
        loss_covalent_pair_prediction=finite,
        loss_pre_post_geometry=finite,
        loss_covalent_pair_contrastive=finite,
        loss_total=total,
        base_diffusion_valid_sample_count=5,
        covalent_pair_prediction_valid_sample_count=5,
        pre_post_geometry_valid_sample_count=5,
        covalent_pair_contrastive_valid_sample_count=5,
        pair_prediction_per_sample_detached=diagnostic,
        pre_post_geometry_per_sample_detached=diagnostic,
        pair_contrastive_per_sample_detached=diagnostic,
    )


def test_nonfinite_total_and_gradient_and_zero_group_fail_closed(prepared) -> None:
    _assert_internal_error(
        lambda: subject._validate_finite_loss_contract(
            _synthetic_loss_output(torch.tensor(float("nan"), requires_grad=True)),
            prepared.supervision,
            subject.SMOKE_ONLY_GEOMETRY_WEIGHT_CANDIDATE_V1,
        ),
        "NON_FINITE_OR_NON_SCALAR_LOSS",
    )
    parameter = nn.Parameter(torch.ones(2))
    parameter.grad = torch.tensor([float("inf"), 0.0])
    nonfinite = subject._gradient_group_stats(
        group_name="TEST",
        named_parameters={"parameter": parameter},
        parameter_names=("parameter",),
    )
    _assert_internal_error(
        lambda: subject._require_gradient_gate(
            nonfinite, reason="NON_FINITE_GRADIENT_REJECTED"
        ),
        "NON_FINITE_GRADIENT_REJECTED",
    )
    parameter.grad = torch.zeros(2)
    zero = subject._gradient_group_stats(
        group_name="TEST",
        named_parameters={"parameter": parameter},
        parameter_names=("parameter",),
    )
    for reason in (
        "GEOMETRY_HEAD_GRADIENT_GATE_FAILED",
        "PAIR_HEAD_GRADIENT_GATE_FAILED",
        "SHARED_PRETRAINED_GRADIENT_GATE_FAILED",
    ):
        _assert_internal_error(
            lambda reason=reason: subject._require_gradient_gate(
                zero, reason=reason
            ),
            reason,
        )


def test_second_backward_and_optimizer_step_claims_fail_closed() -> None:
    backward_guard = subject._ExactlyOnceExecutionGuard()
    backward_guard.claim_backward()
    _assert_internal_error(
        backward_guard.claim_backward,
        "SECOND_BACKWARD_ATTEMPT_REJECTED",
    )
    step_guard = subject._ExactlyOnceExecutionGuard()
    step_guard.claim_optimizer_step()
    _assert_internal_error(
        step_guard.claim_optimizer_step,
        "SECOND_OPTIMIZER_STEP_ATTEMPT_REJECTED",
    )


def test_persistent_model_output_path_is_rejected(tmp_path: Path) -> None:
    _assert_public_error(
        lambda: subject.run_covapie_batch001_train5_single_backward_optimizer_step_smoke_v1(
            persistent_output_path=tmp_path / "model.ckpt"
        ),
        "PERSISTENT_MODEL_OUTPUT_PATH_FORBIDDEN",
    )


def test_candidate_source_has_one_execution_site_and_no_forbidden_lifecycle() -> None:
    source = Path(subject.__file__).read_text(encoding="utf-8")
    assert source.count("losses.loss_total.backward()") == 1
    assert source.count("optimizer.step()") == 1
    assert "torch.autograd.grad" not in source
    assert "retain_graph" not in source
    assert "Trainer(" not in source
    assert "scheduler.step(" not in source
    assert "torch.save" not in source
    assert ".save(" not in source
