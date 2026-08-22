from __future__ import annotations

import inspect
import os
from dataclasses import replace
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest
import torch
from torch import nn

from covalent_ext import (  # noqa: E402
    covapie_batch001_train5_five_epoch_task_schedule_refresh_trainer_smoke_v1
    as subject,
)
from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (
    CovapieCurrent11LossWeightsV1,
)


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT.parent / "covapie-state"
CACHE = STATE / "bulk-multisource-cys-sg-v1/rcsb"
CHECKPOINT = ROOT / "checkpoints/crossdocked_fullatom_cond.ckpt"


def _assert_public_error(callable_object, reason: str) -> None:
    with pytest.raises(ValueError) as error:
        callable_object()
    assert str(error.value) == (
        subject.BATCH001_TRAIN5_FIVE_EPOCH_TASK_SCHEDULE_REFRESH_TRAINER_SMOKE_ERROR_V1
        + ":"
        + reason
    )


@pytest.fixture(scope="module")
def prepared():
    train5 = subject.forward_predecessor._prepare_train5_batch(
        repository_root=ROOT,
        cache_root=CACHE,
        requested_sample_identities=None,
    )
    return train5, subject._build_five_epoch_carriers(train5)


@pytest.fixture(scope="module")
def real_result():
    return (
        subject
        .run_covapie_batch001_train5_five_epoch_task_schedule_refresh_trainer_smoke_v1(
            repository_root=ROOT,
            state_root=STATE,
            cache_root=CACHE,
            checkpoint_path=CHECKPOINT,
        )
    )


def test_candidate_is_exact_predecessor_alias_and_default_remains_geometry_zero(
) -> None:
    assert subject.INITIAL_FIVE_EPOCH_JOINT_LOSS_CANDIDATE_V1 is (
        subject.bounded_predecessor
        .INITIAL_BOUNDED_TRAINER_JOINT_LOSS_CANDIDATE_V1
    )
    default, candidate = subject._validate_loss_policy(None)
    assert default.pre_post_geometry == 0.0
    assert candidate.pre_post_geometry == 1.0
    assert candidate.covalent_pair_contrastive == 0.1
    wrong = CovapieCurrent11LossWeightsV1(pre_post_geometry=0.5)
    with pytest.raises(subject.bounded_predecessor._SmokeInvariantError):
        subject._validate_loss_policy(wrong)


def test_exact_formal_train5_five_carriers_schedule_masks_and_static_parity(
    prepared,
) -> None:
    train5, built = prepared
    assert train5.sample_identities == subject.forward_predecessor.FORMAL_TRAIN_EVENT_IDS_V1
    assert train5.authority.DJK_train_event_count == 2
    assert train5.authority.PTG_train_event_count == 3
    assert len(built.carriers) == 5
    assert tuple(carrier.epoch for carrier in built.carriers) == (0, 1, 2, 3, 4)
    assert built.sample_task_cycles == (
        (4, 0, 1, 2, 3),
        (4, 0, 1, 2, 3),
        (2, 3, 4, 0, 1),
        (0, 1, 2, 3, 4),
        (4, 0, 1, 2, 3),
    )
    assert built.epoch_task_vectors == (
        (4, 4, 2, 0, 4),
        (0, 0, 3, 1, 0),
        (1, 1, 4, 2, 1),
        (2, 2, 0, 3, 2),
        (3, 3, 1, 4, 3),
    )
    assert all(set(row) == set(range(5)) for row in built.sample_task_cycles)
    assert built.per_sample_unique_generation_mask_count == (5, 5, 5, 5, 5)
    assert built.cross_epoch_static_label_parity is True
    assert all(
        carrier.supervision.canonical_task_id.tolist()
        == list(carrier.scheduled_task_ids)
        for carrier in built.carriers
    )
    assert all(
        bool(carrier.supervision.sample_training_admitted.all().item())
        for carrier in built.carriers
    )
    assert all(
        carrier.supervision.pre_post_geometry_component_loss_mask.tolist()
        == [[False, True]] * 5
        for carrier in built.carriers
    )


def test_schedule_and_carrier_fail_closed_on_epoch_vector_population_and_cycle(
    prepared,
) -> None:
    train5, built = prepared
    carrier = built.carriers[0]
    with pytest.raises(subject._SmokeInvariantError, match="EPOCH_OUTSIDE"):
        subject._validate_carrier(replace(carrier, epoch=5))
    with pytest.raises(subject._SmokeInvariantError, match="CARRIER_CONTRACT"):
        subject._validate_carrier(
            replace(carrier, scheduled_task_ids=(0, 0, 0, 0, 0))
        )
    with pytest.raises(subject._SmokeInvariantError, match="CARRIER_CONTRACT"):
        subject._validate_carrier(replace(
            carrier,
            sample_identities=carrier.sample_identities
            + ("COVAPIE_CYS_SG_EVENT_V1:LN5_VALIDATION_FORBIDDEN",),
        ))
    missing_cycle = replace(
        train5,
        five_epoch_task_schedule_audit=(
            (4, 0, 1, 2, 2),
            *train5.five_epoch_task_schedule_audit[1:],
        ),
    )
    with pytest.raises(subject._SmokeInvariantError, match="PERMUTATION"):
        subject._build_five_epoch_carriers(missing_cycle)
    duplicate_cycle = replace(
        train5,
        five_epoch_task_schedule_audit=(
            (4, 0, 1, 1, 3),
            *train5.five_epoch_task_schedule_audit[1:],
        ),
    )
    with pytest.raises(subject._SmokeInvariantError, match="PERMUTATION"):
        subject._build_five_epoch_carriers(duplicate_cycle)


@pytest.mark.parametrize(
    "forbidden_identity",
    (
        "COVAPIE_CYS_SG_EVENT_V1:LN5_VALIDATION_FORBIDDEN",
        "COVAPIE_CYS_SG_EVENT_V1:NDU_UNRESOLVED_FORBIDDEN",
        "COVAPIE_CYS_SG_EVENT_V1:NON_TARGET_COMPONENT_FORBIDDEN",
    ),
)
def test_validation_ndu_and_non_target_population_insertion_fail_closed(
    prepared, forbidden_identity: str,
) -> None:
    unused_train5, built = prepared
    carrier = built.carriers[0]
    with pytest.raises(subject._SmokeInvariantError, match="CARRIER_CONTRACT"):
        subject._validate_carrier(replace(
            carrier,
            sample_identities=carrier.sample_identities + (forbidden_identity,),
        ))


def test_generation_mask_staleness_and_static_chemistry_drift_fail_closed(
    prepared,
) -> None:
    unused_train5, built = prepared
    carriers = list(built.carriers)
    epoch0 = carriers[0].supervision
    epoch1 = carriers[1].supervision
    stale_supervision = replace(
        epoch1,
        ligand_base_generation_mask=epoch0.ligand_base_generation_mask,
        ligand_base_fixed_mask=epoch0.ligand_base_fixed_mask,
        ligand_base_target_mask=epoch0.ligand_base_target_mask,
        ligand_base_context_mask=epoch0.ligand_base_context_mask,
        ligand_active_diffusion_loss_mask=epoch0.ligand_active_diffusion_loss_mask,
    )
    carriers[1] = replace(carriers[1], supervision=stale_supervision)
    with pytest.raises(subject._SmokeInvariantError, match="MASK_NOT_REFRESHED"):
        subject._generation_mask_unique_counts(carriers)

    carriers = list(built.carriers)
    drift = carriers[1].supervision.observed_complex_pair_distance_angstrom.clone()
    drift[0, 0] += 0.25
    carriers[1] = replace(
        carriers[1],
        supervision=replace(
            carriers[1].supervision,
            observed_complex_pair_distance_angstrom=drift,
        ),
    )
    with pytest.raises(subject._SmokeInvariantError, match="STATIC_CHEMISTRY"):
        subject._validate_static_label_parity(carriers)


def test_adapter_inherits_product_training_step_and_optimizer_exactly() -> None:
    for adapter in (
        subject._Train5FiveEpochTrainerAdapterV1,
        subject._Train5FiveEpochTrainerCompatibilityAdapterV1,
    ):
        assert adapter.training_step is (
            subject.CovapieCurrent11TrainingLigandPocketDDPM.training_step
        )
        assert adapter.configure_optimizers is (
            subject.CovapieCurrent11TrainingLigandPocketDDPM.configure_optimizers
        )
    assert subject._Train5FiveEpochTrainerCompatibilityAdapterV1.validation_epoch_end is None


def test_active_trainer_signature_requires_exact_five_epoch_reload(tmp_path: Path) -> None:
    kwargs, compatibility = subject._trainer_configuration_for_signature(
        signature=inspect.signature(subject.pl.Trainer.__init__),
        callbacks=[],
        root=tmp_path,
    )
    subject._validate_trainer_kwargs(kwargs)
    assert kwargs["accelerator"] == "cpu"
    assert kwargs["devices"] == 1
    assert kwargs["max_epochs"] == 5
    assert kwargs["min_epochs"] == 5
    assert kwargs["max_steps"] == 5
    assert kwargs["reload_dataloaders_every_n_epochs"] == 1
    assert kwargs[compatibility["sampler_control_parameter"]] is False
    assert compatibility["precision_argument"] in (32, "32-true")


@pytest.mark.parametrize(
    ("key", "value"),
    (
        ("accelerator", "gpu"),
        ("devices", 2),
        ("max_epochs", 6),
        ("min_epochs", 4),
        ("max_steps", 6),
        ("limit_train_batches", 2),
        ("limit_val_batches", 1),
        ("limit_test_batches", 1),
        ("enable_checkpointing", True),
        ("logger", True),
        ("gradient_clip_val", 1.0),
        ("accumulate_grad_batches", 2),
        ("reload_dataloaders_every_n_epochs", 0),
    ),
)
def test_unsafe_trainer_configuration_fails_closed(
    tmp_path: Path, key: str, value: object,
) -> None:
    kwargs, unused = subject._trainer_configuration_for_signature(
        signature=inspect.signature(subject.pl.Trainer.__init__),
        callbacks=[],
        root=tmp_path,
    )
    kwargs[key] = value
    with pytest.raises(subject._SmokeInvariantError):
        subject._validate_trainer_kwargs(kwargs)


def test_epoch_refresh_datamodule_calls_exact_epoch_loaders_and_rejects_stale(
    prepared,
) -> None:
    unused_train5, built = prepared
    datamodule = subject._FiveEpochRefreshDataModuleV1(built.carriers)
    trainer = SimpleNamespace(current_epoch=0)
    datamodule.trainer = trainer
    for epoch in range(5):
        trainer.current_epoch = epoch
        loader = datamodule.train_dataloader()
        assert len(loader) == 1
        assert type(loader.sampler) is subject.SequentialSampler
    assert tuple(datamodule.train_dataloader_epoch_sequence) == (0, 1, 2, 3, 4)
    assert datamodule.train_dataloader_call_count == 5

    stale = subject._FiveEpochRefreshDataModuleV1(built.carriers)
    stale.trainer = SimpleNamespace(current_epoch=1)
    with pytest.raises(subject._SmokeInvariantError, match="REFRESH_SEQUENCE"):
        stale.train_dataloader()
    dataset = subject._SingleEpochCarrierDatasetV1(built.carriers[0])
    assert dataset[0] is built.carriers[0]
    with pytest.raises(subject._SmokeInvariantError, match="SECOND_TRAIN_BATCH"):
        dataset[0]


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
    (
        "wrong_parent",
        "wrong_subject",
        "extra_path",
        "executable_mode",
        "extra_untracked",
    ),
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


def test_nonfinite_gradient_geometry_and_no_parameter_change_fail_closed() -> None:
    parameter = nn.Parameter(torch.ones(1))
    parameter.grad = torch.tensor([float("nan")])
    stats = subject.single_step_predecessor._gradient_group_stats(
        group_name="NONFINITE",
        named_parameters={"p": parameter},
        parameter_names=("p",),
    )
    with pytest.raises(
        subject.single_step_predecessor._SmokeInvariantError,
        match="NONFINITE_GRADIENT",
    ):
        subject.single_step_predecessor._require_gradient_gate(
            stats, reason="NONFINITE_GRADIENT"
        )

    weight = nn.Parameter(torch.ones(2, 3))
    bias = nn.Parameter(torch.ones(2))
    parameters = {
        subject.single_step_predecessor.GEOMETRY_FINAL_WEIGHT_NAME_V1: weight,
        subject.single_step_predecessor.GEOMETRY_FINAL_BIAS_NAME_V1: bias,
    }
    weight.grad = torch.tensor([[1.0, 0.0, 0.0], [1.0, 1.0, 1.0]])
    bias.grad = torch.ones(2)
    with pytest.raises(
        subject.single_step_predecessor._SmokeInvariantError,
        match="PRE_OUTPUT_COMPONENT",
    ):
        subject.single_step_predecessor._geometry_component_gradient(parameters)
    weight.grad.zero_()
    bias.grad.zero_()
    with pytest.raises(
        subject.single_step_predecessor._SmokeInvariantError,
        match="POST_OUTPUT_COMPONENT",
    ):
        subject.single_step_predecessor._geometry_component_gradient(parameters)

    model = nn.Linear(2, 1)
    before = {name: value.detach().clone() for name, value in model.named_parameters()}
    delta = subject.single_step_predecessor._parameter_delta_group_stats(
        group_name="UNCHANGED",
        named_parameters=dict(model.named_parameters()),
        parameter_names=tuple(before),
        before=before,
    )
    with pytest.raises(
        subject.single_step_predecessor._SmokeInvariantError,
        match="NO_PARAMETER_CHANGE",
    ):
        subject.single_step_predecessor._require_delta_gate(
            delta, reason="NO_PARAMETER_CHANGE"
        )


def test_sixth_lifecycle_and_nonfinite_loss_fail_closed(prepared) -> None:
    unused_train5, built = prepared
    groups = (("ALL_PARAMETERS", ("weight",), "DELTA"),)
    observer = subject._FiveEpochTrainerObserverV1(
        original_carriers=built.carriers,
        checkpoint_state={},
        parameter_groups=groups,
    )
    observer.after_backward_count = 5
    with pytest.raises(subject._SmokeInvariantError, match="SIXTH_AUTOMATIC"):
        observer.on_after_backward(None, None)
    observer.before_zero_grad_count = 5
    with pytest.raises(subject._SmokeInvariantError, match="SIXTH_ZERO_GRAD"):
        observer.on_before_zero_grad(None, None, None)
    loss = torch.tensor(float("nan"), requires_grad=True)
    with pytest.raises(subject._SmokeInvariantError, match="BACKWARD_INPUT"):
        subject._FiveEpochTrainerObserverV1(
            original_carriers=built.carriers,
            checkpoint_state={},
            parameter_groups=groups,
        ).on_before_backward(None, None, loss)


@pytest.mark.parametrize(
    "mutation",
    (
        "model_replaced",
        "optimizer_replaced",
        "checkpoint_reloaded",
        "checkpoint_remigrated",
        "sixth_train_batch",
    ),
)
def test_model_optimizer_checkpoint_continuity_fail_closed(mutation: str) -> None:
    kwargs = {
        "model_object_identities": (11,) * 5,
        "optimizer_object_identities": (22,) * 5,
        "checkpoint_payload_load_call_count": 1,
        "actual_trained_model_migration_call_count": 1,
        "train_batch_count": 5,
    }
    if mutation == "model_replaced":
        kwargs["model_object_identities"] = (11, 11, 12, 11, 11)
    elif mutation == "optimizer_replaced":
        kwargs["optimizer_object_identities"] = (22, 22, 23, 22, 22)
    elif mutation == "checkpoint_reloaded":
        kwargs["checkpoint_payload_load_call_count"] = 2
    elif mutation == "checkpoint_remigrated":
        kwargs["actual_trained_model_migration_call_count"] = 2
    else:
        kwargs["model_object_identities"] = (11,) * 6
        kwargs["optimizer_object_identities"] = (22,) * 6
        kwargs["train_batch_count"] = 6
    with pytest.raises(subject._SmokeInvariantError, match="CONTINUITY_INVALID"):
        subject._validate_runtime_continuity_v1(**kwargs)


def test_public_non_cpu_wrong_checkpoint_and_persistence_reject_before_execution(
    tmp_path: Path,
) -> None:
    _assert_public_error(
        lambda: subject.run_covapie_batch001_train5_five_epoch_task_schedule_refresh_trainer_smoke_v1(
            device="cuda"
        ),
        "NON_CPU_TRAINER_REJECTED",
    )
    _assert_public_error(
        lambda: subject.run_covapie_batch001_train5_five_epoch_task_schedule_refresh_trainer_smoke_v1(
            repository_root=ROOT,
            state_root=STATE,
            cache_root=CACHE,
            checkpoint_path=tmp_path / "wrong.ckpt",
        ),
        "CHECKPOINT_PATH_NOT_EXACT_PUBLISHED_PATH",
    )
    _assert_public_error(
        lambda: subject.run_covapie_batch001_train5_five_epoch_task_schedule_refresh_trainer_smoke_v1(
            persistent_output_path=tmp_path / "forbidden"
        ),
        "PERSISTENT_OUTPUT_PATH_FORBIDDEN",
    )
    assert not any(tmp_path.iterdir())


def test_real_trainer_epoch_reload_lifecycle_and_identity_continuity(real_result) -> None:
    result = real_result
    assert result.trainer_fit_invoked is True
    assert result.trainer_epoch_sequence == (0, 1, 2, 3, 4)
    assert result.train_dataloader_epoch_sequence == (0, 1, 2, 3, 4)
    assert result.trainer_fit_train_batch_count == 5
    assert result.trainer_global_step == 5
    assert result.automatic_backward_call_count == 5
    assert result.trainer_optimizer_step_count == 5
    assert result.zero_grad_lifecycle_call_count == 5
    assert result.train_dataloader_call_count == 5
    assert result.dataset_getitem_call_count == 5
    assert result.collator_call_count == 5
    assert result.before_batch_transfer_call_count == 5
    assert result.model_transfer_batch_to_device_call_count == 5
    assert result.after_batch_transfer_call_count == 5
    assert result.diffusion_seed_hook_call_count == 5
    assert result.unique_model_identity_count == 1
    assert result.unique_optimizer_identity_count == 1
    assert result.checkpoint_reload_between_epochs is False
    assert result.model_reinitialization_during_epochs is False
    assert result.validation_step_call_count == 0
    assert result.test_step_call_count == 0


def test_real_per_epoch_losses_gradients_and_geometry_components(real_result) -> None:
    result = real_result
    assert len(result.runtime_losses_each_epoch) == 5
    assert all(
        torch.isfinite(torch.tensor(value))
        for losses in result.runtime_losses_each_epoch
        for unused_name, value in losses
    )
    assert all(
        difference <= 1.0e-7
        for difference in result.weighted_total_formula_absolute_difference_each_epoch
    )
    assert all(dict(counts) == {
        "base": 5,
        "pair": 5,
        "POST_geometry": 5,
        "contrastive": 5,
        "PRE_geometry": 0,
    } for counts in result.valid_sample_counts_each_epoch)
    required = {
        "ALL_PARAMETERS",
        "SHARED_PRETRAINED",
        "TARGET_RESIDUE_CONDITIONING",
        "ROLE_TASK_MASK_ANCHOR",
        "PAIR_HEAD",
        "GEOMETRY_HEAD",
    }
    assert all({item.group_name for item in epoch} == required
               for epoch in result.gradient_group_stats_each_epoch)
    assert all(item.all_gradients_finite
               for epoch in result.gradient_group_stats_each_epoch
               for item in epoch)
    assert all(item.nonzero_gradient_tensor_count > 0
               for epoch in result.gradient_group_stats_each_epoch
               for item in epoch)
    assert all(item.PRE_output_component_gradient_exact_zero
               for item in result.geometry_component_gradient_each_epoch)
    assert all(item.POST_output_component_gradient_finite_nonzero
               for item in result.geometry_component_gradient_each_epoch)


def test_real_per_step_and_cumulative_parameter_deltas(real_result) -> None:
    result = real_result
    required = {
        "ALL_PARAMETERS",
        "SHARED_PRETRAINED",
        "NEW_COVAPIE",
        "TARGET_RESIDUE_CONDITIONING",
        "ROLE_TASK_MASK_ANCHOR",
        "PAIR_HEAD",
        "GEOMETRY_HEAD",
    }
    assert all({item.group_name for item in epoch} == required
               for epoch in result.parameter_delta_group_stats_each_epoch)
    assert all(item.changed_parameter_tensor_count > 0
               for epoch in result.parameter_delta_group_stats_each_epoch
               for item in epoch)
    assert all(item.parameter_delta_l2 > 0.0
               for epoch in result.parameter_delta_group_stats_each_epoch
               for item in epoch)
    assert {item.group_name for item in result.cumulative_parameter_delta_group_stats} == required
    assert all(item.changed_parameter_tensor_count > 0
               for item in result.cumulative_parameter_delta_group_stats)
    assert all(item.parameter_delta_l2 > 0.0
               for item in result.cumulative_parameter_delta_group_stats)
    assert result.all_parameters_finite_after_each_step == (True,) * 5
    assert result.cumulative_changed_parameter_tensor_count > 0


def test_real_migration_integrity_publication_profile_and_readiness(real_result) -> None:
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
    assert result.checkpoint_payload_load_call_count == 1
    assert result.actual_trained_model_migration_call_count == 1
    assert result.checkpoint_file_changed is False
    assert result.protected_sources_changed is False
    assert result.protected_state_unchanged is True
    assert result.raw_tree_unchanged is True
    assert result.original_epoch_carriers_unchanged is True
    assert result.temporary_trainer_root_removed is True
    assert result.persistent_output_created is False
    assert result.repository_branch == "main"
    assert result.repository_ahead == 0
    assert result.repository_behind == 0
    assert result.repository_staged_count == 0
    assert len(result.candidate_file_observations) == 3
    assert {item[0] for item in result.candidate_file_observations} == (
        subject.CANDIDATE_RELATIVE_PATHS_V1
    )
    assert all(len(item[2]) == 64 and not (int(item[3], 8) & 0o111)
               for item in result.candidate_file_observations)
    assert result.geometry_weight_optimal is False
    assert result.production_joint_loss_policy_finalized is False
    assert result.full_training_authorized is False
    assert result.ready_for_gpt_review is True
    assert result.ready_for_mainline_data_scale_and_validation_design is True
    assert result.recommended_next_step_exactly == subject.RECOMMENDED_NEXT_STEP_EXACTLY_V1


def test_import_has_no_execution_or_persistent_side_effect(tmp_path: Path) -> None:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join((str(ROOT / "src"), str(ROOT)))
    completed = subprocess.run(
        (
            sys.executable,
            "-c",
            "import covalent_ext."
            "covapie_batch001_train5_five_epoch_task_schedule_refresh_trainer_smoke_v1",
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


def test_source_contains_no_manual_backward_step_or_persistence() -> None:
    text = (ROOT / (
        "src/covalent_ext/"
        "covapie_batch001_train5_five_epoch_task_schedule_refresh_trainer_smoke_v1.py"
    )).read_text(encoding="utf-8")
    assert ".backward(" not in text
    assert "optimizer.step(" not in text
    assert "torch.save(" not in text
    assert "Trainer.fit(" not in text
    assert text.count("runtime.trainer.fit(") == 1
