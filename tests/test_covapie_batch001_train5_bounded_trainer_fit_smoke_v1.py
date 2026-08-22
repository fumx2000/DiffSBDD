from __future__ import annotations

import inspect
import os
from dataclasses import replace
from pathlib import Path
import subprocess
import sys

import pytest
import torch
from torch import nn
from torch.utils.data import SequentialSampler

from covalent_ext import (
    covapie_batch001_train5_bounded_trainer_fit_smoke_v1 as subject,
)
from covalent_ext import (
    covapie_batch001_train5_single_backward_optimizer_step_smoke_v1
    as single_step_predecessor,
)
from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (
    CovapieCurrent11LossWeightsV1,
)
from covalent_ext.covapie_current11_training_lightning_module_v1 import (
    CovapieCurrent11TrainingLigandPocketDDPM,
)


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT.parent / "covapie-state"
CACHE = STATE / "bulk-multisource-cys-sg-v1/rcsb"
CHECKPOINT = ROOT / "checkpoints/crossdocked_fullatom_cond.ckpt"
ERROR = subject.BATCH001_TRAIN5_BOUNDED_TRAINER_FIT_SMOKE_ERROR_V1


def _assert_error(callable_object, reason: str) -> None:
    with pytest.raises(ValueError, match=rf"^{ERROR}:{reason}$"):
        callable_object()


@pytest.fixture(scope="module")
def prepared():
    value = subject.forward_predecessor._prepare_train5_batch(
        repository_root=ROOT,
        cache_root=CACHE,
        requested_sample_identities=None,
    )
    return value, subject._carrier_from_prepared(value)


@pytest.fixture(scope="module")
def real_result():
    return subject.run_covapie_batch001_train5_bounded_trainer_fit_smoke_v1(
        repository_root=ROOT,
        state_root=STATE,
        cache_root=CACHE,
        checkpoint_path=CHECKPOINT,
    )


def test_candidate_is_exact_predecessor_alias_and_global_default_is_geometry_zero() -> None:
    assert (
        subject.INITIAL_BOUNDED_TRAINER_JOINT_LOSS_CANDIDATE_V1
        is single_step_predecessor.SMOKE_ONLY_GEOMETRY_WEIGHT_CANDIDATE_V1
    )
    assert subject._loss_weights_tuple(
        subject.INITIAL_BOUNDED_TRAINER_JOINT_LOSS_CANDIDATE_V1
    ) == (
        ("base_diffusion", 1.0),
        ("covalent_pair_prediction", 1.0),
        ("pre_post_geometry", 1.0),
        ("covalent_pair_contrastive", 0.1),
    )
    assert CovapieCurrent11LossWeightsV1().pre_post_geometry == 0.0


def test_exact_formal_train5_carrier_and_dataloader(prepared) -> None:
    value, carrier = prepared
    assert value.sample_identities == subject.forward_predecessor.FORMAL_TRAIN_EVENT_IDS_V1
    assert value.authority.DJK_train_event_count == 2
    assert value.authority.PTG_train_event_count == 3
    assert value.authority.formal_validation_event_ids
    assert value.authority.formal_unresolved_event_ids
    assert carrier.scheduled_task_ids == (4, 4, 2, 0, 4)
    assert len(carrier.model_input_batch["lig_mask"]) == 115
    assert len(carrier.model_input_batch["pocket_mask"]) == 578
    assert len(carrier.supervision.pair_candidate_batch_index) == 690
    assert carrier.supervision.pre_post_geometry_component_loss_mask.tolist() == [
        [False, True]
    ] * 5
    datamodule = subject._Train5DataModuleV1(carrier)
    datamodule.setup("fit")
    loader = datamodule.train_dataloader()
    assert len(datamodule.dataset) == 1
    assert len(loader) == 1
    assert loader.batch_size == 1
    assert type(loader.sampler) is SequentialSampler
    assert loader.num_workers == 0
    assert loader.drop_last is False
    assert loader.pin_memory is False
    assert loader.persistent_workers is False
    assert next(iter(loader)) is carrier


def test_adapter_inherits_product_training_step_and_optimizer_exactly() -> None:
    adapter = subject._Train5BoundedTrainerAdapterV1
    compatibility = subject._Train5BoundedTrainerCompatibilityAdapterV1
    assert adapter.__bases__ == (CovapieCurrent11TrainingLigandPocketDDPM,)
    assert getattr(adapter, "training_step") is CovapieCurrent11TrainingLigandPocketDDPM.training_step
    assert getattr(adapter, "configure_optimizers") is CovapieCurrent11TrainingLigandPocketDDPM.configure_optimizers
    assert getattr(compatibility, "training_step") is CovapieCurrent11TrainingLigandPocketDDPM.training_step
    assert getattr(compatibility, "configure_optimizers") is CovapieCurrent11TrainingLigandPocketDDPM.configure_optimizers
    assert compatibility.validation_epoch_end is None


def test_active_trainer_signature_configuration_is_exact(tmp_path: Path) -> None:
    kwargs, compatibility = subject._trainer_configuration_for_signature(
        signature=inspect.signature(subject.pl.Trainer.__init__),
        callbacks=[],
        root=tmp_path,
    )
    subject._validate_trainer_kwargs(kwargs)
    assert kwargs["accelerator"] == "cpu"
    assert kwargs["devices"] == 1
    assert kwargs["max_steps"] == 1
    assert kwargs["limit_train_batches"] == 1
    assert kwargs["limit_val_batches"] == 0
    assert kwargs["enable_checkpointing"] is False
    assert kwargs["logger"] is False
    assert kwargs["gradient_clip_val"] is None
    assert kwargs["accumulate_grad_batches"] == 1
    assert kwargs[compatibility["sampler_control_parameter"]] is False
    assert compatibility["precision_argument"] in (32, "32-true")


def _published_repository_observation():
    future_head = "f" * 40
    return subject._RepositoryObservationV1(
        branch="main",
        head=future_head,
        subject=subject.PUBLISHED_SUCCESSOR_SUBJECT_V1,
        origin_main=future_head,
        ahead=0,
        behind=0,
        tracked_status=(),
        staged_paths=(),
        untracked_paths=(),
        head_parents=(subject.EXPECTED_HEAD_V1,),
        head_changed_paths=tuple(sorted(
            ("A", path) for path in subject.CANDIDATE_RELATIVE_PATHS_V1
        )),
        head_tree_modes=tuple(sorted(
            ("100644", path) for path in subject.CANDIDATE_RELATIVE_PATHS_V1
        )),
    )


def test_published_successor_repository_profile_simulation_passes() -> None:
    assert subject._classify_repository_profile_v1(
        _published_repository_observation()
    ) == subject.PUBLISHED_SUCCESSOR_PROFILE_V1


@pytest.mark.parametrize(
    "mutation",
    ("wrong_parent", "wrong_subject", "extra_path", "executable_mode", "untracked_extra"),
)
def test_published_successor_repository_profile_simulation_fails_closed(
    mutation: str,
) -> None:
    observation = _published_repository_observation()
    if mutation == "wrong_parent":
        observation = replace(observation, head_parents=("e" * 40,))
    elif mutation == "wrong_subject":
        observation = replace(observation, subject="wrong")
    elif mutation == "extra_path":
        observation = replace(
            observation,
            head_changed_paths=observation.head_changed_paths + (("A", "extra.py"),),
        )
    elif mutation == "executable_mode":
        path = sorted(subject.CANDIDATE_RELATIVE_PATHS_V1)[0]
        observation = replace(
            observation,
            head_tree_modes=tuple(
                ("100755" if candidate == path else mode, candidate)
                for mode, candidate in observation.head_tree_modes
            ),
        )
    else:
        observation = replace(observation, untracked_paths=("extra.txt",))
    with pytest.raises(subject._SmokeInvariantError, match="REPOSITORY_PROFILE_INVALID"):
        subject._classify_repository_profile_v1(observation)


def test_direct_success_uses_exact_pre_fit_snapshot_without_resnapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = nn.Linear(2, 1)
    original_snapshot = single_step_predecessor._parameter_snapshot
    calls = 0

    def counted_snapshot(named_parameters):
        nonlocal calls
        calls += 1
        return original_snapshot(named_parameters)

    monkeypatch.setattr(
        single_step_predecessor, "_parameter_snapshot", counted_snapshot
    )
    snapshot = subject._capture_pre_optimizer_step_parameter_snapshot_v1(
        model,
        branch="direct_success",
        trainer_global_step=0,
        optimizer_step_count=0,
    )
    before_weight = snapshot.tensors["weight"].clone()
    with torch.no_grad():
        model.weight.add_(0.25)
    selected_snapshot = subject._select_trained_pre_optimizer_step_snapshot_v1(
        compatibility_used=False,
        direct_snapshot=snapshot,
        compatibility_snapshot=None,
    )
    assert selected_snapshot is snapshot
    selected = subject._parameter_before_from_pre_optimizer_step_snapshot_v1(
        selected_snapshot,
        trained_model=model,
        expected_branch="direct_success",
    )
    assert calls == 1
    assert selected is snapshot.tensors
    assert torch.equal(selected["weight"], before_weight)
    stats = single_step_predecessor._parameter_delta_group_stats(
        group_name="DIRECT_SUCCESS",
        named_parameters=dict(model.named_parameters()),
        parameter_names=("weight",),
        before=selected,
    )
    assert stats.changed_parameter_tensor_count == 1
    assert stats.parameter_delta_l2 > 0.0
    with pytest.raises(
        subject._SmokeInvariantError,
        match="PARAMETER_SNAPSHOT_NOT_CAPTURED_BEFORE_OPTIMIZER_STEP",
    ):
        subject._capture_pre_optimizer_step_parameter_snapshot_v1(
            model,
            branch="direct_success",
            trainer_global_step=1,
            optimizer_step_count=1,
        )


def test_real_trainer_lifecycle_transfer_and_no_validation(real_result) -> None:
    result = real_result
    assert result.implementation_status == "passed"
    assert result.trainer_fit_invoked is True
    assert result.trainer_fit_train_batch_count == 1
    assert result.trainer_global_step == 1
    assert result.automatic_optimization is True
    assert result.automatic_backward_call_count == 1
    assert result.trainer_optimizer_step_count == 1
    assert result.zero_grad_lifecycle_call_count == 1
    assert result.datamodule_setup_fit_call_count == 1
    assert result.dataset_getitem_call_count == 1
    assert result.collator_call_count == 1
    assert result.before_batch_transfer_call_count == 1
    assert result.model_transfer_batch_to_device_call_count == 1
    assert result.after_batch_transfer_call_count == 1
    assert result.transferred_batch_rebuilt is True
    assert result.transferred_metadata_unchanged is True
    assert result.transferred_tensors_on_model_device is True
    assert result.validation_step_call_count == 0
    assert result.test_step_call_count == 0
    assert result.diffusion_seed_hook_call_count == 1
    assert result.diffusion_seed == 11030037
    assert result.parameter_delta_snapshot_branch == "compatibility_fallback"
    assert result.parameter_delta_snapshot_optimizer_step_count_at_capture == 0
    assert result.parameter_delta_snapshot_captured_before_optimizer_step is True


def test_real_loss_counts_formula_and_manual_parity(real_result) -> None:
    result = real_result
    assert set(dict(result.training_step_metrics)) == subject.EXPECTED_METRIC_KEYS_V1
    assert all(torch.isfinite(torch.tensor(value)) for _, value in result.runtime_losses)
    assert result.base_diffusion_valid_sample_count == 5
    assert result.covalent_pair_prediction_valid_sample_count == 5
    assert result.POST_geometry_valid_sample_count == 5
    assert result.PRE_geometry_valid_sample_count == 0
    assert result.covalent_pair_contrastive_valid_sample_count == 5
    losses = dict(result.runtime_losses)
    assert losses["loss_pre_post_geometry"] > 0.0
    assert result.weighted_total_formula_absolute_difference <= 1.0e-7
    assert result.max_abs_loss_difference <= 1.0e-7
    assert result.manual_reference_loss_tuple == result.trainer_loss_tuple


def test_real_optimizer_gradient_and_post_only_geometry_gates(real_result) -> None:
    result = real_result
    optimizer = result.optimizer_metadata
    assert optimizer.optimizer_type == "AdamW"
    assert optimizer.model_lr == 0.001
    assert optimizer.amsgrad is True
    assert optimizer.weight_decay == 1.0e-12
    assert optimizer.model_parameter_tensor_count == 135
    assert optimizer.optimizer_parameter_tensor_count == 135
    assert optimizer.optimizer_unique_parameter_count == 135
    assert optimizer.optimizer_parameter_set_exact is True
    gradients = {item.group_name: item for item in result.gradient_group_stats}
    assert set(gradients) == {
        "ALL_PARAMETERS", "SHARED_PRETRAINED", "TARGET_RESIDUE_CONDITIONING",
        "ROLE_TASK_MASK_ANCHOR", "PAIR_HEAD", "GEOMETRY_HEAD",
    }
    assert all(item.all_gradients_finite for item in gradients.values())
    assert all(item.nonzero_gradient_tensor_count > 0 for item in gradients.values())
    assert all(item.gradient_l2_norm > 0.0 for item in gradients.values())
    geometry = result.geometry_component_gradient
    assert geometry.PRE_output_component_gradient_exact_zero is True
    assert geometry.POST_output_component_gradient_finite_nonzero is True
    assert geometry.PRE_weight_row_l2_norm == 0.0
    assert geometry.PRE_bias_gradient_abs == 0.0
    assert geometry.POST_weight_row_l2_norm > 0.0
    assert geometry.POST_bias_gradient_abs > 0.0


def test_real_required_parameter_groups_change_and_safety_holds(real_result) -> None:
    result = real_result
    deltas = {item.group_name: item for item in result.parameter_delta_group_stats}
    assert set(deltas) == {
        "ALL_PARAMETERS", "SHARED_PRETRAINED", "NEW_COVAPIE",
        "TARGET_RESIDUE_CONDITIONING", "ROLE_TASK_MASK_ANCHOR",
        "PAIR_HEAD", "GEOMETRY_HEAD",
    }
    assert all(item.changed_parameter_tensor_count > 0 for item in deltas.values())
    assert all(item.parameter_delta_l2 > 0.0 for item in deltas.values())
    assert all(item.all_parameters_finite for item in deltas.values())
    assert result.all_parameters_finite_after_fit is True
    assert result.checkpoint_file_changed is False
    assert result.protected_sources_changed is False
    assert result.protected_state_unchanged is True
    assert result.raw_tree_unchanged is True
    assert result.original_batch_unchanged is True
    assert result.original_supervision_unchanged is True
    assert result.temporary_trainer_root_removed is True
    assert result.persistent_output_created is False
    assert result.GPU_used is False
    assert result.network_used is False


def test_real_migration_repository_and_bounded_readiness(real_result) -> None:
    result = real_result
    assert dict(result.migration_counts) == {
        "checkpoint_key_count": 122,
        "target_model_key_count": 141,
        "shared_key_count": 122,
        "target_only_key_count": 19,
        "checkpoint_only_key_count": 0,
        "shared_shape_mismatch_count": 0,
        "shared_checkpoint_tensor_equality_count": 122,
    }
    assert result.migration_missing_keys == ()
    assert result.migration_unexpected_keys == ()
    assert result.repository_branch == "main"
    assert result.repository_profile in {
        subject.CANDIDATE_PRECOMMIT_PROFILE_V1,
        subject.PUBLISHED_SUCCESSOR_PROFILE_V1,
    }
    assert result.repository_ahead == 0
    assert result.repository_behind == 0
    assert result.repository_staged_count == 0
    if result.repository_profile == subject.CANDIDATE_PRECOMMIT_PROFILE_V1:
        assert result.repository_HEAD == subject.EXPECTED_HEAD_V1
        assert result.repository_origin_main == subject.EXPECTED_HEAD_V1
        assert frozenset(result.repository_untracked_paths) == subject.CANDIDATE_RELATIVE_PATHS_V1
        assert len(result.repository_untracked_paths) == 3
    else:
        assert result.repository_HEAD == result.repository_origin_main
        assert result.repository_HEAD != subject.EXPECTED_HEAD_V1
        assert result.repository_untracked_paths == ()
    assert result.published_default_modified is False
    assert result.initial_joint_loss_candidate_validated_for_bounded_trainer_fit is True
    assert result.geometry_weight_optimal is False
    assert result.production_joint_loss_policy_finalized is False
    assert result.full_training_authorized is False
    assert result.ready_for_gpt_review is True
    assert result.ready_for_five_epoch_train5_schedule_refresh_trainer_smoke is True


def test_wrong_geometry_candidate_and_invalid_carrier_fail_closed(prepared) -> None:
    wrong = CovapieCurrent11LossWeightsV1(
        base_diffusion=1.0,
        covalent_pair_prediction=1.0,
        pre_post_geometry=0.5,
        covalent_pair_contrastive=0.1,
    )
    with pytest.raises(subject._SmokeInvariantError) as candidate_error:
        subject._validate_loss_policy(wrong)
    assert candidate_error.value.reason == "SMOKE_ONLY_GEOMETRY_WEIGHT_CANDIDATE_INVALID"
    unused, carrier = prepared
    invalid = replace(
        carrier,
        sample_identities=carrier.sample_identities
        + ("COVAPIE_CYS_SG_EVENT_V1:LN5_VALIDATION_FORBIDDEN",),
    )
    with pytest.raises(subject._SmokeInvariantError) as carrier_error:
        subject._validate_carrier(invalid)
    assert carrier_error.value.reason == "TRAIN5_CARRIER_CONTRACT_INVALID"


def test_mutated_global_default_and_wrong_bound_files_fail_closed(tmp_path: Path) -> None:
    mutated_default = CovapieCurrent11LossWeightsV1(
        base_diffusion=1.0,
        covalent_pair_prediction=1.0,
        pre_post_geometry=1.0,
        covalent_pair_contrastive=0.1,
    )
    with pytest.raises(subject._SmokeInvariantError) as default_error:
        subject._validate_loss_policy(None, published_default=mutated_default)
    assert default_error.value.reason == "PUBLISHED_DEFAULT_LOSS_WEIGHTS_MUTATED"
    wrong_source = tmp_path / "wrong_predecessor.py"
    wrong_source.write_text("wrong\n", encoding="utf-8")
    _assert_error(
        lambda: subject.verify_covapie_batch001_train5_bounded_trainer_predecessor_source_v1(
            predecessor_source_path=wrong_source
        ),
        "PREDECESSOR_SOURCE_SHA256_MISMATCH",
    )
    wrong_checkpoint = tmp_path / "wrong_checkpoint.bin"
    wrong_checkpoint.write_bytes(b"wrong")
    with pytest.raises(ValueError, match="CHECKPOINT_SHA256_MISMATCH"):
        subject.forward_predecessor.verify_covapie_batch001_train5_checkpoint_file_v1(
            checkpoint_path=wrong_checkpoint
        )


def test_second_lifecycle_calls_and_nonfinite_loss_fail_closed(prepared) -> None:
    unused, carrier = prepared
    dataset = subject._SingleTrain5DatasetV1(carrier)
    assert dataset[0] is carrier
    with pytest.raises(subject._SmokeInvariantError, match="SECOND_DATASET_ITEM_REQUESTED"):
        dataset[0]
    observer = subject._TrainerObserverV1(
        original_carrier=carrier, checkpoint_state={}
    )
    observer.on_after_backward(None, None)
    with pytest.raises(subject._SmokeInvariantError, match="SECOND_AUTOMATIC_BACKWARD_REJECTED"):
        observer.on_after_backward(None, None)
    observer.before_optimizer_step_count = 1
    with pytest.raises(subject._SmokeInvariantError, match="SECOND_OR_INVALID_OPTIMIZER_STEP_REJECTED"):
        observer.on_before_optimizer_step(None, None, None)
    observer.on_before_zero_grad(None, None, None)
    with pytest.raises(subject._SmokeInvariantError, match="SECOND_ZERO_GRAD_LIFECYCLE_REJECTED"):
        observer.on_before_zero_grad(None, None, None)
    nonfinite = torch.tensor(float("nan"), requires_grad=True)
    with pytest.raises(subject._SmokeInvariantError, match="AUTOMATIC_BACKWARD_INPUT_INVALID"):
        subject._TrainerObserverV1(
            original_carrier=carrier, checkpoint_state={}
        ).on_before_backward(None, None, nonfinite)


def test_optimizer_nonfinite_gradient_and_geometry_component_fail_closed() -> None:
    model = nn.Linear(2, 1)
    incomplete = torch.optim.AdamW([model.weight], lr=0.001, amsgrad=True, weight_decay=1.0e-12)
    with pytest.raises(single_step_predecessor._SmokeInvariantError, match="OPTIMIZER_PARAMETER_SET_NOT_EXACT"):
        single_step_predecessor._validate_optimizer_parameter_coverage(model, incomplete)
    parameter = nn.Parameter(torch.ones(1))
    parameter.grad = torch.tensor([float("nan")])
    stats = single_step_predecessor._gradient_group_stats(
        group_name="NONFINITE", named_parameters={"p": parameter}, parameter_names=("p",)
    )
    with pytest.raises(single_step_predecessor._SmokeInvariantError, match="NONFINITE_GRADIENT_REJECTED"):
        single_step_predecessor._require_gradient_gate(
            stats, reason="NONFINITE_GRADIENT_REJECTED"
        )
    weight = nn.Parameter(torch.ones(2, 3))
    bias = nn.Parameter(torch.ones(2))
    weight.grad = torch.tensor([[1.0, 0.0, 0.0], [1.0, 1.0, 1.0]])
    bias.grad = torch.tensor([1.0, 1.0])
    geometry_parameters = {
        single_step_predecessor.GEOMETRY_FINAL_WEIGHT_NAME_V1: weight,
        single_step_predecessor.GEOMETRY_FINAL_BIAS_NAME_V1: bias,
    }
    with pytest.raises(single_step_predecessor._SmokeInvariantError, match="PRE_OUTPUT_COMPONENT_GRADIENT_NOT_EXACT_ZERO"):
        single_step_predecessor._geometry_component_gradient(geometry_parameters)
    weight.grad.zero_()
    bias.grad.zero_()
    with pytest.raises(single_step_predecessor._SmokeInvariantError, match="POST_OUTPUT_COMPONENT_GRADIENT_NOT_NONZERO"):
        single_step_predecessor._geometry_component_gradient(geometry_parameters)


@pytest.mark.parametrize(
    ("key", "value"),
    (
        ("accelerator", "gpu"), ("devices", 2), ("max_steps", 2),
        ("limit_train_batches", 2), ("limit_val_batches", 1),
        ("enable_checkpointing", True), ("logger", True),
        ("gradient_clip_val", 1.0), ("accumulate_grad_batches", 2),
    ),
)
def test_unsafe_trainer_configuration_fails_closed(
    tmp_path: Path, key: str, value: object
) -> None:
    kwargs, unused = subject._trainer_configuration_for_signature(
        signature=inspect.signature(subject.pl.Trainer.__init__),
        callbacks=[],
        root=tmp_path,
    )
    kwargs[key] = value
    with pytest.raises(subject._SmokeInvariantError):
        subject._validate_trainer_kwargs(kwargs)


def test_public_non_cpu_wrong_checkpoint_and_persistence_fail_before_execution(
    tmp_path: Path,
) -> None:
    _assert_error(
        lambda: subject.run_covapie_batch001_train5_bounded_trainer_fit_smoke_v1(
            device="cuda"
        ),
        "NON_CPU_TRAINER_REJECTED",
    )
    _assert_error(
        lambda: subject.run_covapie_batch001_train5_bounded_trainer_fit_smoke_v1(
            repository_root=ROOT,
            state_root=STATE,
            cache_root=CACHE,
            checkpoint_path=tmp_path / "wrong.ckpt",
        ),
        "CHECKPOINT_PATH_NOT_EXACT_PUBLISHED_PATH",
    )
    _assert_error(
        lambda: subject.run_covapie_batch001_train5_bounded_trainer_fit_smoke_v1(
            persistent_output_path=tmp_path / "forbidden"
        ),
        "PERSISTENT_OUTPUT_PATH_FORBIDDEN",
    )
    assert not any(tmp_path.iterdir())


def test_compatibility_clipping_hook_is_bounded_noop() -> None:
    hook = subject._Train5BoundedTrainerCompatibilityAdapterV1.configure_gradient_clipping
    optimizer = object()
    hook(object(), optimizer, None, None)
    with pytest.raises(subject._SmokeInvariantError):
        hook(object(), optimizer, 1.0, None)


def test_import_has_no_execution_or_persistent_side_effect(tmp_path: Path) -> None:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join((str(ROOT / "src"), str(ROOT)))
    completed = subprocess.run(
        (
            sys.executable,
            "-c",
            "import covalent_ext.covapie_batch001_train5_bounded_trainer_fit_smoke_v1",
        ),
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == ""
    assert completed.stderr == ""
    assert not any(tmp_path.iterdir())


def test_source_contains_no_manual_trainer_backward_step_or_persistence() -> None:
    text = (ROOT / "src/covalent_ext/covapie_batch001_train5_bounded_trainer_fit_smoke_v1.py").read_text(
        encoding="utf-8"
    )
    assert ".backward(" not in text
    assert "optimizer.step(" not in text
    assert "torch.save(" not in text
    assert "Trainer.fit(" not in text
    assert text.count("runtime.trainer.fit(") == 1
