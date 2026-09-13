from __future__ import annotations

import ast
from dataclasses import replace
import inspect
import json
import math
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest
import torch
from torch import nn

from covalent_ext import (
    covapie_batch001_bounded_training_session_v1 as bounded_owner,
)
from covalent_ext import (
    covapie_batch001_current_state_validation4_adapter_v1 as validation_owner,
)
from covalent_ext import (
    covapie_batch001_train_validation_lifecycle_v1 as subject,
)
from covalent_ext import (
    covapie_current11_formal_validation4_masked_vlb_nll_v1 as evaluator_owner,
)
from covalent_ext import covapie_current11_checkpoint_migration_v1 as migration_owner


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
STATE_ROOT = REPOSITORY_ROOT.parent / "covapie-state"
CACHE_ROOT = STATE_ROOT / "bulk-multisource-cys-sg-v1/rcsb"
SOURCE_PATH = REPOSITORY_ROOT / (
    "src/covalent_ext/covapie_batch001_train_validation_lifecycle_v1.py"
)


def _forbidden(*_args, **_kwargs):
    raise AssertionError("forbidden real model, Trainer, optimizer, or execution path")


@pytest.fixture(scope="module")
def prepared():
    with (
        mock.patch.object(torch, "load", side_effect=_forbidden),
        mock.patch.object(torch, "save", side_effect=_forbidden),
        mock.patch.object(
            migration_owner,
            "load_covapie_current11_legacy_checkpoint_v1",
            side_effect=_forbidden,
        ),
        mock.patch.object(
            bounded_owner, "_instantiate_authorized_model_v1", side_effect=_forbidden
        ),
        mock.patch.object(
            bounded_owner, "build_covapie_batch001_bounded_training_runtime_v1",
            side_effect=_forbidden,
        ),
        mock.patch.object(
            validation_owner,
            "evaluate_covapie_batch001_current_state_validation4_v1",
            side_effect=_forbidden,
        ),
        mock.patch.object(
            evaluator_owner, "_evaluate_slice", side_effect=_forbidden
        ),
        mock.patch.object(
            bounded_owner.CovapieBatch001BoundedTrainingLigandPocketDDPMV1,
            "__new__",
            new=_forbidden,
        ),
        mock.patch.object(
            bounded_owner.pl.Trainer,
            "__new__",
            new=_forbidden,
        ),
        mock.patch.object(torch.optim.AdamW, "__init__", new=_forbidden),
        mock.patch.object(torch.Tensor, "backward", side_effect=_forbidden),
        mock.patch.object(torch.optim.Optimizer, "step", side_effect=_forbidden),
    ):
        return subject.prepare_covapie_batch001_train_validation_lifecycle_v1(
            repository_root=REPOSITORY_ROOT,
            state_root=STATE_ROOT,
            cache_root=CACHE_ROOT,
        )


def test_fixed_direct_sources_and_real_prepare_only_contract(prepared):
    bindings = subject.verify_covapie_batch001_train_validation_lifecycle_sources_v1(
        repository_root=REPOSITORY_ROOT
    )
    assert tuple(
        (row.relative_path, row.observed_sha256) for row in bindings
    ) == subject.DIRECT_BOUND_SOURCE_SHA256_V1
    summary = prepared.summary
    assert summary.implementation_status == "PREPARED_NOT_EXECUTED"
    assert summary.canonical_mask_semantic_names == (
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    )
    assert summary.training_epochs == (0, 1, 2, 3, 4)
    assert len(summary.training_carrier_fingerprints) == 5
    assert all(
        carrier.formal_split == "train"
        and carrier.sample_identities == prepared.training.authority.train_event_ids
        for carrier in prepared.training.carriers
    )
    assert prepared.validation.validation_carrier.formal_split == "validation"
    assert (
        prepared.validation.validation_carrier.sample_identities
        == prepared.training.authority.validation_event_ids
    )
    assert summary.formal_train_event_ids == prepared.training.authority.train_event_ids
    assert (
        summary.formal_validation_event_ids
        == prepared.training.authority.validation_event_ids
    )
    assert summary.formal_test_event_ids == prepared.training.authority.test_event_ids
    assert summary.event_identity_intersections_zero
    assert summary.leakage_group_cross_split_violation_count == 0
    assert summary.validation_training_admission_closed
    assert summary.validation_training_loss_masks_closed
    assert summary.validation_labels_retained_for_evaluation
    assert not summary.test_model_input_constructed
    assert summary.primary_metric_name == "MASKED_CONDITIONAL_VLB_NLL_V1"
    assert summary.validation_root_seeds == evaluator_owner.FORMAL_VALIDATION_ROOT_SEEDS_V1
    assert summary.validation_context_seed == validation_owner.VALIDATION_CONTEXT_SEED_V1


def test_prepare_plan_counts_are_distinct_from_zero_actual_calls(prepared):
    summary = prepared.summary
    assert summary.planned_checkpoint_load_count == 1
    assert summary.planned_model_construction_count == 1
    assert summary.planned_trainer_construction_count == 1
    assert summary.planned_optimizer_construction_count == 1
    assert summary.planned_fit_call_count == 1
    assert summary.planned_training_forward_count == 5
    assert summary.planned_max_optimizer_step_count == 5
    assert summary.planned_validation4_call_count == 2
    assert summary.planned_validation_event_count_per_call == 4
    assert summary.planned_validation_event_task_count_per_call == 16
    assert summary.planned_validation_estimate_count_per_call == 64
    assert summary.planned_validation_task_seed_slice_count_per_call == 20
    assert summary.planned_validation_main_dynamics_count_per_call == 20
    assert summary.planned_validation_t0_dynamics_count_per_call == 20
    assert summary.planned_validation_estimate_count_total == 128
    assert summary.planned_validation_dynamics_count_total == 80
    assert all(
        getattr(summary, field) == 0
        for field in (
            "actual_checkpoint_load_count",
            "actual_model_construction_count",
            "actual_trainer_construction_count",
            "actual_optimizer_construction_count",
            "actual_fit_call_count",
            "actual_validation4_call_count",
            "actual_validation_dynamics_count",
            "actual_backward_count",
            "actual_optimizer_step_count",
        )
    )
    assert summary.default_prepare_only
    assert summary.execution_opt_in_required
    assert summary.same_model_required_for_all_stages
    assert summary.validation_runs_outside_fit
    assert not summary.parameter_update_performed
    assert not summary.lightning_in_fit_validation_hook_integrated
    assert not summary.train_validation_lifecycle_runtime_validated
    assert not summary.formal_scientific_training_started
    assert not summary.ready_for_training
    assert not summary.geometry_training_gradient_accepted
    assert summary.feature_semantics_audit_required_later
    assert summary.step12d_is_only_smoke_legality_check


def test_prepare_serialization_is_deterministic_and_cli_has_no_execute_option(
    prepared, monkeypatch, capsys
):
    first = subject.serialize_covapie_batch001_train_validation_lifecycle_prepare_v1(
        prepared
    )
    second = subject.serialize_covapie_batch001_train_validation_lifecycle_prepare_v1(
        prepared
    )
    assert first == second
    payload = json.loads(first)
    assert payload["implementation_status"] == "PREPARED_NOT_EXECUTED"
    assert payload["actual_fit_call_count"] == 0
    assert payload["actual_validation4_call_count"] == 0
    assert payload["train_validation_lifecycle_runtime_validated"] is False
    monkeypatch.setattr(
        subject,
        "prepare_covapie_batch001_train_validation_lifecycle_v1",
        lambda **_kwargs: prepared,
    )
    assert subject.main([]) == 0
    assert json.loads(capsys.readouterr().out) == payload
    assert "--execute" not in inspect.getsource(subject.main)


def test_direct_source_drift_fails_closed(monkeypatch):
    original = subject._sha256_file

    def drift(path):
        if path.name == "covapie_batch001_bounded_training_session_v1.py":
            return "0" * 64
        return original(path)

    monkeypatch.setattr(subject, "_sha256_file", drift)
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="DIRECT_BOUND_SOURCE_SHA256_MISMATCH",
    ):
        subject.verify_covapie_batch001_train_validation_lifecycle_sources_v1(
            repository_root=REPOSITORY_ROOT
        )


def test_invalid_or_mixed_prepared_data_identity_is_rejected(prepared):
    mixed_validation = replace(
        prepared.validation,
        validation_carrier=replace(
            prepared.validation.validation_carrier,
            formal_split="train",
        ),
    )
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="TRAIN_VALIDATION_TEST_IDENTITY_MISMATCH",
    ):
        subject._validate_prepared_components_v1(
            training=prepared.training,
            validation=mixed_validation,
        )
    mixed_training = replace(
        prepared.training,
        carriers=(
            replace(prepared.training.carriers[0], formal_split="validation"),
        )
        + prepared.training.carriers[1:],
    )
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="TRAIN5_IDENTITY_OR_SCHEDULE_INVALID",
    ):
        subject._validate_prepared_components_v1(
            training=mixed_training,
            validation=prepared.validation,
        )


def test_missing_opt_in_stops_before_runtime_build(prepared, monkeypatch):
    run = subject.create_covapie_batch001_train_validation_lifecycle_run_v1(
        prepared=prepared
    )
    build = mock.Mock(side_effect=_forbidden)
    monkeypatch.setattr(
        bounded_owner,
        "build_covapie_batch001_bounded_training_runtime_v1",
        build,
    )
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="EXPLICIT_LIFECYCLE_EXECUTION_OPT_IN_REQUIRED",
    ):
        subject.execute_covapie_batch001_train_validation_lifecycle_v1(
            run=run,
            runtime_root=REPOSITORY_ROOT,
            repository_root=REPOSITORY_ROOT,
            state_root=STATE_ROOT,
            cache_root=CACHE_ROOT,
        )
    build.assert_not_called()
    assert not run.execution_consumed
    assert run.runtime_build_request_count == 0
    assert run.validation_request_count == 0
    assert run.fit_request_count == 0
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="FEATURE_SEMANTICS_USE_AUDIT_CONFIRMATION_REQUIRED",
    ):
        subject.execute_covapie_batch001_train_validation_lifecycle_v1(
            run=run,
            execution_opt_in=True,
            runtime_root=REPOSITORY_ROOT,
            repository_root=REPOSITORY_ROOT,
            state_root=STATE_ROOT,
            cache_root=CACHE_ROOT,
        )
    build.assert_not_called()
    assert not run.execution_consumed


class _ProbeModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.weight = nn.Parameter(torch.tensor([2.0, -3.0]))
        self.branch = nn.Linear(2, 1)
        self.register_buffer("running_buffer", torch.tensor([5.0]))
        self.mode = "SYNTHETIC_PROBE"
        self.loss_type = "SYNTHETIC"
        self.covapie_current11_loss_weights = None
        self.train()
        self.branch.eval()
        self.weight.grad = torch.tensor([7.0, 11.0])


class _FakeOptimizer:
    def __init__(self, model):
        self.param_groups = [{"params": list(model.parameters()), "lr": 0.001}]
        self.state = {0: {"step": torch.tensor(5.0), "moment": torch.tensor([1.0])}}

    def state_dict(self):
        return {
            "state": self.state,
            "param_groups": [{"params": list(range(len(self.param_groups[0]["params"]))), "lr": 0.001}],
        }


class _FakeTrainer:
    def __init__(self):
        self.global_step = 0
        self.current_epoch = 0
        self.state = SimpleNamespace(status="idle")
        self.fit_loop = SimpleNamespace(running=False)
        self.optimizers = []


def _rows(prepared_validation, offset):
    values = dict(
        zip(
            prepared_validation.summary.formal_validation_event_ids,
            (0.0, 10.0, 100.0, 110.0),
        )
    )
    rows = []
    for task_id, preview in prepared_validation.task_batches:
        supervision = preview.supervision
        ligand_mask = preview.model_input_batch["lig_mask"]
        for seed in evaluator_owner.FORMAL_VALIDATION_ROOT_SEEDS_V1:
            for sample, event_id in enumerate(preview.sample_identities):
                record = prepared_validation.record_by_event[event_id]
                sample_nodes = ligand_mask == sample
                generated = int(
                    supervision.ligand_base_generation_mask[
                        sample_nodes, 0
                    ].sum().item()
                )
                fixed = int(
                    supervision.ligand_base_fixed_mask[sample_nodes, 0].sum().item()
                )
                pair_count = int(
                    supervision.pair_candidate_offsets[sample + 1].item()
                    - supervision.pair_candidate_offsets[sample].item()
                )
                value = values[event_id] + offset
                task4 = task_id == 4
                rows.append(evaluator_owner.FormalValidationEstimateV1(
                    canonical_event_id=event_id,
                    pdb_id=record.pdb_id,
                    ligand_component_id=record.ligand_component_id,
                    formal_split="validation",
                    leakage_group=prepared_validation.leakage_by_event[event_id],
                    profile=evaluator_owner._profile_name(record),
                    canonical_task_id=task_id,
                    canonical_task_name=subject.CANONICAL_MASK_CONTRACT_V1[task_id][1],
                    canonical_task_alias=subject.CANONICAL_MASK_CONTRACT_V1[task_id][2],
                    root_validation_seed=seed,
                    main_timestep_int=1,
                    generated_atom_count=generated,
                    fixed_atom_count=fixed,
                    coordinate_dimension=3 * (generated - int(task4)),
                    main_active_epsilon_error=1.0 + offset,
                    SNR_weight=1.0,
                    loss_t=1.0 + offset,
                    t0_coordinate_loss=1.0 + offset,
                    t0_categorical_loss=1.0,
                    negative_log_coordinate_constant=1.0,
                    kl_prior=1.0,
                    masked_delta_log_px=1.0,
                    masked_conditional_vlb_nll=value,
                    task4_log_pN=1.0 if task4 else None,
                    task4_historical_joint_nll_with_node_prior_diagnostic=(
                        value - 1.0 if task4 else None
                    ),
                    pair_BCE=2.0 + offset,
                    POST_geometry_loss=3.0 + offset,
                    POST_geometry_prediction_angstrom=4.0 + offset,
                    POST_geometry_target_angstrom=5.0,
                    pair_contrastive_loss=6.0 + offset,
                    PRE_geometry_valid=False,
                    target_cys_sg_indicator_count=1,
                    pair_candidate_count=pair_count,
                    fixed_ligand_clean_main=True,
                    fixed_ligand_clean_t0=True,
                ))
    return tuple(rows)


def _mean(values):
    return math.fsum(values) / len(values)


def _validation_fixture_result(
    prepared_validation,
    *,
    model,
    stage,
    stage_evidence,
    offset,
    rows=None,
):
    rows = _rows(prepared_validation, offset) if rows is None else rows
    task_means, event_means, event_macro, micro, profiles, profile_balanced = (
        validation_owner._validate_and_aggregate_rows_v1(
            estimates=rows, prepared=prepared_validation
        )
    )
    snapshot = validation_owner._snapshot_model_state_v1(model)
    task4_joint = tuple(
        float(row.task4_historical_joint_nll_with_node_prior_diagnostic)
        for row in rows
        if row.task4_historical_joint_nll_with_node_prior_diagnostic is not None
    )
    return SimpleNamespace(
        implementation_status="EXECUTED",
        primary_metric_name=validation_owner.PRIMARY_METRIC_NAME_V1,
        validation_model_weight_source=validation_owner.VALIDATION_MODEL_WEIGHT_SOURCE_V1,
        caller_model_stage=stage,
        caller_stage_evidence=stage_evidence,
        caller_quiescence_asserted=True,
        model_training_provenance_status=validation_owner.MODEL_STATE_TRAINING_PROVENANCE_V1,
        historical_output644_model_state_recovered=False,
        source_model_state_sha256_before=snapshot.model_state_sha256,
        source_model_state_sha256_after=snapshot.model_state_sha256,
        formal_validation_event_ids=prepared_validation.summary.formal_validation_event_ids,
        root_validation_seeds=prepared_validation.summary.root_validation_seeds,
        formal_validation_event_count=4,
        formal_validation_task_event_count=16,
        formal_validation_estimate_count=64,
        formal_validation_task_slice_evaluation_count=20,
        main_dynamics_task_slice_call_count=20,
        t0_dynamics_task_slice_call_count=20,
        total_dynamics_task_slice_call_count=40,
        per_estimate_rows=rows,
        per_event_task_seed_means=task_means,
        per_event_means=event_means,
        event_macro_masked_conditional_vlb_nll=event_macro,
        micro_masked_conditional_vlb_nll=micro,
        profile_means=profiles,
        profile_balanced_masked_conditional_vlb_nll=profile_balanced,
        mean_pair_BCE=_mean(tuple(row.pair_BCE for row in rows)),
        mean_POST_geometry_loss=_mean(
            tuple(row.POST_geometry_loss for row in rows)
        ),
        mean_POST_geometry_prediction_angstrom=_mean(
            tuple(row.POST_geometry_prediction_angstrom for row in rows)
        ),
        mean_POST_geometry_target_angstrom=_mean(
            tuple(row.POST_geometry_target_angstrom for row in rows)
        ),
        mean_pair_contrastive_loss=_mean(
            tuple(row.pair_contrastive_loss for row in rows)
        ),
        mean_task4_historical_joint_nll_with_node_prior_diagnostic=_mean(
            task4_joint
        ),
        primary_node_prior_included=False,
        source_parameters_unchanged=True,
        source_buffers_unchanged=True,
        source_gradients_unchanged=True,
        source_requires_grad_unchanged=True,
        source_parameter_identities_unchanged=True,
        source_buffer_identities_unchanged=True,
        source_module_identities_unchanged=True,
        source_state_keys_unchanged=True,
        source_configuration_unchanged=True,
        evaluation_carriers_unchanged=True,
        source_training_flags_restored=True,
        CPU_rng_restored=True,
        CPU_determinism_settings_restored=True,
        no_new_parameter_module_or_state_key=True,
        metric_tensors_require_grad=False,
        all_validation_rows_finite=True,
        checkpoint_loaded_inside_validation=False,
        shadow_model_constructed=False,
        optimizer_created=False,
        Trainer_used=False,
        backward_performed=False,
        parameter_update_performed=False,
    )


def _callbacks(prepared, *, post_offset=10.0):
    calls = []
    model = _ProbeModel()
    trainer = _FakeTrainer()
    model._trainer = trainer
    optimizer_holder = []
    runtime = SimpleNamespace(
        model=model,
        trainer=trainer,
        datamodule=object(),
        fit_call_count=0,
    )

    def build(**kwargs):
        calls.append("build")
        assert kwargs["execution_authorized"] is True
        assert kwargs["prepared"] is prepared.training
        return runtime

    def evaluate(**kwargs):
        stage = kwargs["caller_model_stage"]
        calls.append("pre" if stage == subject.PRE_FIT_MODEL_STAGE_V1 else "post")
        assert kwargs["source_model"] is model
        assert kwargs["execution_opt_in"] is True
        assert kwargs["caller_confirms_model_is_quiescent"] is True
        assert not validation_owner._trainer_running(model)
        return _validation_fixture_result(
            prepared.validation,
            model=model,
            stage=stage,
            stage_evidence=kwargs["caller_stage_evidence"],
            offset=(0.0 if stage == subject.PRE_FIT_MODEL_STAGE_V1 else post_offset),
        )

    def fit(value):
        calls.append("fit")
        assert value is runtime
        runtime.fit_call_count += 1
        trainer.state.status = "running"
        trainer.fit_loop.running = True
        with torch.no_grad():
            model.weight.add_(1.0)
        optimizer = _FakeOptimizer(model)
        optimizer_holder.append(optimizer)
        trainer.optimizers = [optimizer]
        trainer.global_step = 5
        trainer.current_epoch = 5
        trainer.fit_loop.running = False
        trainer.state.status = "finished"

    return SimpleNamespace(
        calls=calls,
        model=model,
        trainer=trainer,
        runtime=runtime,
        optimizers=optimizer_holder,
        build=build,
        evaluate=evaluate,
        fit=fit,
    )


def _execute_synthetic(prepared, callbacks):
    run = subject.create_covapie_batch001_train_validation_lifecycle_run_v1(
        prepared=prepared
    )
    return subject._execute_lifecycle_with_callbacks_v1(
        run=run,
        execution_opt_in=True,
        runtime_root=REPOSITORY_ROOT,
        repository_root=REPOSITORY_ROOT,
        state_root=STATE_ROOT,
        cache_root=CACHE_ROOT,
        runtime_builder=callbacks.build,
        evaluator=callbacks.evaluate,
        fit_invoker=callbacks.fit,
        synthetic_fixture_mode=True,
    )


def test_synthetic_same_model_sequence_state_isolation_and_signed_worse_delta(
    prepared,
):
    callbacks = _callbacks(prepared, post_offset=10.0)
    modes_before = tuple(module.training for module in callbacks.model.modules())
    grad_object = callbacks.model.weight.grad
    grad_before = grad_object.clone()
    rng_before = torch.random.get_rng_state().clone()
    run = _execute_synthetic(prepared, callbacks)
    assert callbacks.calls == ["build", "pre", "fit", "post"]
    assert run.phase == "COMPLETED"
    assert run.terminal_status == "COMPLETED"
    assert run.runtime is callbacks.runtime
    assert run.model is callbacks.model
    assert run.model_object_identity == id(callbacks.model)
    assert run.runtime_build_request_count == run.runtime_build_completion_count == 1
    assert run.fit_request_count == run.fit_completion_count == 1
    assert run.validation_request_count == run.validation_completion_count == 2
    assert run.actual_global_step == 5
    assert run.actual_final_epoch == 5
    assert run.fit_returned is True
    assert run.parameter_update_observed is True
    assert run.pre_fit_state_isolation_pass is True
    assert run.post_fit_state_isolation_pass is True
    assert run.post_fit_optimizer_isolation_pass is True
    assert run.pre_fit_public_API_rng_isolation_pass is True
    assert run.post_fit_public_API_rng_isolation_pass is True
    assert run.same_model_and_parameter_objects_pass is True
    assert run.source_and_carrier_identity_final_pass is True
    assert tuple(module.training for module in callbacks.model.modules()) == modes_before
    assert callbacks.model.weight.grad is grad_object
    assert torch.equal(callbacks.model.weight.grad, grad_before)
    assert torch.equal(torch.random.get_rng_state(), rng_before)
    comparison = run.paired_comparison
    assert comparison.comparison_direction == "post_minus_pre"
    assert comparison.paired_estimate_count == 64
    assert comparison.paired_event_task_count == 16
    assert comparison.paired_event_count == 4
    assert comparison.event_macro_post_minus_pre == pytest.approx(10.0)
    assert comparison.micro_post_minus_pre == pytest.approx(10.0)
    assert comparison.profile_balanced_post_minus_pre == pytest.approx(10.0)
    assert all(
        row.masked_conditional_vlb_nll_post_minus_pre == pytest.approx(10.0)
        for row in comparison.per_estimate
    )


def test_pre_fit_failure_prevents_fit_and_post_validation(prepared):
    callbacks = _callbacks(prepared)

    def fail_pre(**_kwargs):
        callbacks.calls.append("pre_failed")
        raise RuntimeError("synthetic pre failure")

    callbacks.evaluate = fail_pre
    run = subject.create_covapie_batch001_train_validation_lifecycle_run_v1(
        prepared=prepared
    )
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="PRE_FIT_VALIDATION_FAILED",
    ) as caught:
        subject._execute_lifecycle_with_callbacks_v1(
            run=run,
            execution_opt_in=True,
            runtime_root=REPOSITORY_ROOT,
            repository_root=REPOSITORY_ROOT,
            state_root=STATE_ROOT,
            cache_root=CACHE_ROOT,
            runtime_builder=callbacks.build,
            evaluator=callbacks.evaluate,
            fit_invoker=callbacks.fit,
            synthetic_fixture_mode=True,
        )
    assert caught.value.run is run
    assert callbacks.calls == ["build", "pre_failed"]
    assert run.validation_request_count == 1
    assert run.validation_completion_count == 0
    assert run.fit_request_count == 0
    assert run.parameter_update_observed is None
    assert run.terminal_status == "FAILED"


def test_fit_failure_prevents_post_validation_and_preserves_update_fact(prepared):
    callbacks = _callbacks(prepared)

    def fail_fit(runtime):
        callbacks.calls.append("fit_failed")
        runtime.fit_call_count += 1
        runtime.trainer.global_step = 2
        with torch.no_grad():
            runtime.model.weight.add_(0.5)
        raise RuntimeError("synthetic partial fit failure")

    callbacks.fit = fail_fit
    run = subject.create_covapie_batch001_train_validation_lifecycle_run_v1(
        prepared=prepared
    )
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="BOUNDED_FIT_FAILED",
    ) as caught:
        subject._execute_lifecycle_with_callbacks_v1(
            run=run,
            execution_opt_in=True,
            runtime_root=REPOSITORY_ROOT,
            repository_root=REPOSITORY_ROOT,
            state_root=STATE_ROOT,
            cache_root=CACHE_ROOT,
            runtime_builder=callbacks.build,
            evaluator=callbacks.evaluate,
            fit_invoker=callbacks.fit,
            synthetic_fixture_mode=True,
        )
    assert caught.value.run is run
    assert callbacks.calls == ["build", "pre", "fit_failed"]
    assert run.fit_request_count == 1
    assert run.fit_completion_count == 0
    assert run.validation_request_count == 1
    assert run.actual_global_step == 2
    assert run.fit_returned is False
    assert run.parameter_update_observed is True
    assert run.post_fit_validation_result is None


def test_post_fit_failure_preserves_completed_training_update(prepared):
    callbacks = _callbacks(prepared)
    ordinary_evaluate = callbacks.evaluate

    def fail_post(**kwargs):
        if kwargs["caller_model_stage"] == subject.POST_FIT_MODEL_STAGE_V1:
            callbacks.calls.append("post_failed")
            raise RuntimeError("synthetic post failure")
        return ordinary_evaluate(**kwargs)

    callbacks.evaluate = fail_post
    run = subject.create_covapie_batch001_train_validation_lifecycle_run_v1(
        prepared=prepared
    )
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="POST_FIT_VALIDATION_FAILED_AFTER_TRAINING_UPDATE",
    ) as caught:
        subject._execute_lifecycle_with_callbacks_v1(
            run=run,
            execution_opt_in=True,
            runtime_root=REPOSITORY_ROOT,
            repository_root=REPOSITORY_ROOT,
            state_root=STATE_ROOT,
            cache_root=CACHE_ROOT,
            runtime_builder=callbacks.build,
            evaluator=callbacks.evaluate,
            fit_invoker=callbacks.fit,
            synthetic_fixture_mode=True,
        )
    assert caught.value.run is run
    assert callbacks.calls == ["build", "pre", "fit", "post_failed"]
    assert run.fit_completion_count == 1
    assert run.parameter_update_observed is True
    assert run.actual_global_step == 5
    assert run.validation_request_count == 2
    assert run.validation_completion_count == 1
    assert run.post_fit_validation_result is None


def test_model_replacement_running_trainer_and_state_mutation_fail_closed(prepared):
    replacement = _callbacks(prepared)
    ordinary_fit = replacement.fit

    def replace_after_fit(runtime):
        ordinary_fit(runtime)
        runtime.model = _ProbeModel()

    replacement.fit = replace_after_fit
    run = subject.create_covapie_batch001_train_validation_lifecycle_run_v1(
        prepared=prepared
    )
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="BOUNDED_FIT_COMPLETION_STATE_REJECTED",
    ):
        subject._execute_lifecycle_with_callbacks_v1(
            run=run,
            execution_opt_in=True,
            runtime_root=REPOSITORY_ROOT,
            repository_root=REPOSITORY_ROOT,
            state_root=STATE_ROOT,
            cache_root=CACHE_ROOT,
            runtime_builder=replacement.build,
            evaluator=replacement.evaluate,
            fit_invoker=replacement.fit,
            synthetic_fixture_mode=True,
        )
    running = _callbacks(prepared)
    running.trainer.state.status = "running"
    running.trainer.fit_loop.running = True
    run = subject.create_covapie_batch001_train_validation_lifecycle_run_v1(
        prepared=prepared
    )
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="RUNNING_TRAINER_MODEL_VALIDATION_FORBIDDEN",
    ):
        subject._execute_lifecycle_with_callbacks_v1(
            run=run,
            execution_opt_in=True,
            runtime_root=REPOSITORY_ROOT,
            repository_root=REPOSITORY_ROOT,
            state_root=STATE_ROOT,
            cache_root=CACHE_ROOT,
            runtime_builder=running.build,
            evaluator=running.evaluate,
            fit_invoker=running.fit,
            synthetic_fixture_mode=True,
        )
    assert running.calls == ["build"]
    assert run.execution_consumed
    assert run.terminal_status == "FAILED"
    assert run.failure_stage == subject.PRE_FIT_MODEL_STAGE_V1
    assert run.failure_reason == "RUNNING_TRAINER_MODEL_VALIDATION_FORBIDDEN"
    mutated = _callbacks(prepared)

    def mutate_model(**kwargs):
        with torch.no_grad():
            kwargs["source_model"].running_buffer.add_(1.0)
        return _validation_fixture_result(
            prepared.validation,
            model=kwargs["source_model"],
            stage=kwargs["caller_model_stage"],
            stage_evidence=kwargs["caller_stage_evidence"],
            offset=0.0,
        )

    mutated.evaluate = mutate_model
    run = subject.create_covapie_batch001_train_validation_lifecycle_run_v1(
        prepared=prepared
    )
    before = mutated.model.running_buffer.clone()
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="PRE_FIT_VALIDATION_RESULT_OR_ISOLATION_REJECTED",
    ):
        subject._execute_lifecycle_with_callbacks_v1(
            run=run,
            execution_opt_in=True,
            runtime_root=REPOSITORY_ROOT,
            repository_root=REPOSITORY_ROOT,
            state_root=STATE_ROOT,
            cache_root=CACHE_ROOT,
            runtime_builder=mutated.build,
            evaluator=mutated.evaluate,
            fit_invoker=mutated.fit,
            synthetic_fixture_mode=True,
        )
    assert not torch.equal(mutated.model.running_buffer, before)
    assert run.pre_fit_state_isolation_pass is False
    assert run.fit_request_count == 0


def test_public_evaluation_boundary_rng_and_optimizer_state_are_guarded(prepared):
    rng_callbacks = _callbacks(prepared)
    ordinary_evaluate = rng_callbacks.evaluate

    def mutate_rng(**kwargs):
        result = ordinary_evaluate(**kwargs)
        torch.rand(1)
        return result

    rng_callbacks.evaluate = mutate_rng
    run = subject.create_covapie_batch001_train_validation_lifecycle_run_v1(
        prepared=prepared
    )
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="PRE_FIT_VALIDATION_RESULT_OR_ISOLATION_REJECTED",
    ):
        subject._execute_lifecycle_with_callbacks_v1(
            run=run,
            execution_opt_in=True,
            runtime_root=REPOSITORY_ROOT,
            repository_root=REPOSITORY_ROOT,
            state_root=STATE_ROOT,
            cache_root=CACHE_ROOT,
            runtime_builder=rng_callbacks.build,
            evaluator=rng_callbacks.evaluate,
            fit_invoker=rng_callbacks.fit,
            synthetic_fixture_mode=True,
        )
    assert run.pre_fit_public_API_rng_isolation_pass is False
    optimizer_callbacks = _callbacks(prepared)
    ordinary_evaluate = optimizer_callbacks.evaluate

    def mutate_optimizer(**kwargs):
        result = ordinary_evaluate(**kwargs)
        if kwargs["caller_model_stage"] == subject.POST_FIT_MODEL_STAGE_V1:
            optimizer_callbacks.optimizers[0].state[0]["step"].add_(1.0)
        return result

    optimizer_callbacks.evaluate = mutate_optimizer
    run = subject.create_covapie_batch001_train_validation_lifecycle_run_v1(
        prepared=prepared
    )
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="POST_FIT_STATE_OR_PAIRED_COMPARISON_REJECTED",
    ):
        subject._execute_lifecycle_with_callbacks_v1(
            run=run,
            execution_opt_in=True,
            runtime_root=REPOSITORY_ROOT,
            repository_root=REPOSITORY_ROOT,
            state_root=STATE_ROOT,
            cache_root=CACHE_ROOT,
            runtime_builder=optimizer_callbacks.build,
            evaluator=optimizer_callbacks.evaluate,
            fit_invoker=optimizer_callbacks.fit,
            synthetic_fixture_mode=True,
        )
    assert run.parameter_update_observed is True
    assert run.post_fit_optimizer_isolation_pass is False


def test_duplicate_execution_second_fit_and_third_validation_are_forbidden(prepared):
    callbacks = _callbacks(prepared)
    run = _execute_synthetic(prepared, callbacks)
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="LIFECYCLE_ALREADY_CONSUMED_NO_RETRY_OR_RESUME",
    ):
        subject._execute_lifecycle_with_callbacks_v1(
            run=run,
            execution_opt_in=True,
            runtime_root=REPOSITORY_ROOT,
            repository_root=REPOSITORY_ROOT,
            state_root=STATE_ROOT,
            cache_root=CACHE_ROOT,
            runtime_builder=callbacks.build,
            evaluator=callbacks.evaluate,
            fit_invoker=callbacks.fit,
            synthetic_fixture_mode=True,
        )
    assert callbacks.calls == ["build", "pre", "fit", "post"]
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="SECOND_FIT_REQUEST_FORBIDDEN",
    ):
        subject._request_operation_v1(run, "FIT")
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="THIRD_VALIDATION_REQUEST_FORBIDDEN",
    ):
        subject._request_operation_v1(run, "VALIDATION")


@pytest.mark.parametrize("mutation", ("missing", "duplicate", "nonfinite", "illegal_seed"))
def test_paired_metric_domain_rejects_missing_duplicate_nonfinite_or_illegal(
    prepared, mutation
):
    callbacks = _callbacks(prepared)
    run = _execute_synthetic(prepared, callbacks)
    post = run.post_fit_validation_result
    rows = post.per_estimate_rows
    if mutation == "missing":
        changed = rows[:-1]
    elif mutation == "duplicate":
        changed = rows[:-1] + (rows[0],)
    elif mutation == "nonfinite":
        changed = (replace(rows[0], masked_conditional_vlb_nll=float("nan")),) + rows[1:]
    else:
        changed = (replace(rows[0], root_validation_seed=123),) + rows[1:]
    mutated = SimpleNamespace(**dict(vars(post), per_estimate_rows=changed))
    with pytest.raises(Exception):
        subject._build_paired_comparison_v1(
            pre_result=run.pre_fit_validation_result,
            post_result=mutated,
            prepared=prepared.validation,
            pre_snapshot=run.A0,
            post_snapshot=run.B0,
            pre_stage_evidence=run.pre_fit_validation_result.caller_stage_evidence,
            post_stage_evidence=post.caller_stage_evidence,
            synthetic_fixture_mode=True,
        )


def test_production_route_and_synthetic_fixture_boundary_are_explicit():
    public_signature = inspect.signature(
        subject.execute_covapie_batch001_train_validation_lifecycle_v1
    )
    assert "runtime_builder" not in public_signature.parameters
    assert "evaluator" not in public_signature.parameters
    assert "fit_invoker" not in public_signature.parameters
    tree = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
    source = SOURCE_PATH.read_text(encoding="utf-8")
    private_source = inspect.getsource(subject._execute_lifecycle_with_callbacks_v1)
    assert private_source.count(
        "build_covapie_batch001_bounded_training_runtime_v1"
    ) == 1
    assert private_source.count(
        "evaluate_covapie_batch001_current_state_validation4_v1"
    ) == 1
    assert private_source.count("bounded_owner._invoke_fit_once_v1") == 1
    assert ".backward(" not in source
    assert ".zero_grad(" not in source
    assert ".step(" not in source
    assert "Trainer.validate" not in source
    assert "Trainer.test" not in source
    assert "_trainer =" not in source
    assert any(
        isinstance(node, ast.FunctionDef)
        and node.name == "execute_covapie_batch001_train_validation_lifecycle_v1"
        for node in ast.walk(tree)
    )


def test_production_mode_rejects_callback_injection_and_unknowns_stay_unknown(prepared):
    run = subject.create_covapie_batch001_train_validation_lifecycle_run_v1(
        prepared=prepared
    )
    assert run.fit_returned is None
    assert run.parameter_update_observed is None
    assert run.pre_fit_state_isolation_pass is None
    assert run.post_fit_state_isolation_pass is None
    assert run.post_fit_optimizer_isolation_pass is None
    assert run.failure_stage is None
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="PRODUCTION_CALLBACK_INJECTION_FORBIDDEN",
    ):
        subject._execute_lifecycle_with_callbacks_v1(
            run=run,
            execution_opt_in=True,
            runtime_root=REPOSITORY_ROOT,
            repository_root=REPOSITORY_ROOT,
            state_root=STATE_ROOT,
            cache_root=CACHE_ROOT,
            runtime_builder=lambda **_kwargs: object(),
            synthetic_fixture_mode=False,
        )
    assert not run.execution_consumed
