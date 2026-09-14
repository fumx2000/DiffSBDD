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
from covalent_ext import (
    covapie_current11_auxiliary_model_and_loss_v1 as current_loss_owner,
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


def _prepare_without_real_execution(**kwargs):
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
            **kwargs,
        )


@pytest.fixture(scope="module")
def prepared():
    return _prepare_without_real_execution()


@pytest.fixture(scope="module")
def candidate_prepared():
    return _prepare_without_real_execution(
        learning_rate=subject.CANDIDATE_LEARNING_RATE_V1
    )


@pytest.fixture(scope="module")
def diffusion_only_prepared():
    return _prepare_without_real_execution(
        learning_rate=subject.CANDIDATE_LEARNING_RATE_V1,
        training_objective_profile="diffusion_only",
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
    assert summary.legacy_constructor_learning_rate == 1.0e-3
    assert summary.requested_run_learning_rate == 1.0e-3
    assert not summary.requested_run_learning_rate_differs_from_legacy_reference
    assert summary.learning_rate_application_stage == "NOT_APPLIED_PREPARE_ONLY"
    assert summary.model_learning_rate_before_application == "NOT_OBSERVED"
    assert summary.model_learning_rate_after_application == "NOT_OBSERVED"
    assert summary.actual_optimizer_param_group_learning_rates == "NOT_OBSERVED"
    assert summary.requested_training_objective_profile == "joint_default"
    assert (
        summary.declared_training_loss_weights
        == bounded_owner.DEFAULT_LOSS_WEIGHTS_V1
    )
    assert summary.original_constructor_training_loss_weights == "NOT_OBSERVED"
    assert summary.model_training_loss_weights_before_application == "NOT_OBSERVED"
    assert summary.model_training_loss_weights_after_application == "NOT_OBSERVED"
    assert (
        summary.training_objective_application_stage
        == "NOT_APPLIED_PREPARE_ONLY"
    )


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


def test_candidate_prepare_is_lr_only_and_cli_remains_prepare_only(
    prepared, candidate_prepared, monkeypatch, capsys
):
    reference_payload = json.loads(
        subject.serialize_covapie_batch001_train_validation_lifecycle_prepare_v1(
            prepared
        )
    )
    candidate_payload = json.loads(
        subject.serialize_covapie_batch001_train_validation_lifecycle_prepare_v1(
            candidate_prepared
        )
    )
    differing_fields = {
        key
        for key in reference_payload
        if reference_payload[key] != candidate_payload[key]
    }
    assert differing_fields == {
        "requested_run_learning_rate",
        "requested_run_learning_rate_differs_from_legacy_reference",
    }
    assert candidate_payload["legacy_constructor_learning_rate"] == 1.0e-3
    assert candidate_payload["requested_run_learning_rate"] == 1.0e-4
    assert candidate_payload[
        "requested_run_learning_rate_differs_from_legacy_reference"
    ] is True
    assert candidate_payload["actual_model_construction_count"] == 0
    assert candidate_payload["actual_optimizer_construction_count"] == 0
    assert candidate_payload["actual_optimizer_step_count"] == 0
    assert candidate_payload["parameter_update_performed"] is False
    assert (
        candidate_prepared.summary.training_carrier_fingerprints
        == prepared.summary.training_carrier_fingerprints
    )
    assert (
        candidate_prepared.summary.training_scheduled_task_ids
        == prepared.summary.training_scheduled_task_ids
    )
    assert (
        candidate_prepared.summary.validation_profile_task_matrix
        == prepared.summary.validation_profile_task_matrix
    )

    observed = []

    def prepare_spy(**kwargs):
        observed.append(kwargs)
        return candidate_prepared

    monkeypatch.setattr(
        subject,
        "prepare_covapie_batch001_train_validation_lifecycle_v1",
        prepare_spy,
    )
    assert subject.main(["--learning-rate", "0.0001"]) == 0
    assert observed[0]["learning_rate"] == 1.0e-4
    assert json.loads(capsys.readouterr().out) == candidate_payload
    assert "execute_covapie" not in inspect.getsource(subject.main)


def test_diffusion_only_1e4_prepare_differs_only_by_objective_fields(
    candidate_prepared,
    diffusion_only_prepared,
    monkeypatch,
    capsys,
):
    joint_payload = json.loads(
        subject.serialize_covapie_batch001_train_validation_lifecycle_prepare_v1(
            candidate_prepared
        )
    )
    diffusion_payload = json.loads(
        subject.serialize_covapie_batch001_train_validation_lifecycle_prepare_v1(
            diffusion_only_prepared
        )
    )
    assert {
        key
        for key in joint_payload
        if joint_payload[key] != diffusion_payload[key]
    } == {
        "requested_training_objective_profile",
        "declared_training_loss_weights",
    }
    assert diffusion_payload["requested_training_objective_profile"] == (
        "diffusion_only"
    )
    assert diffusion_payload["declared_training_loss_weights"] == {
        "base_diffusion": 1.0,
        "covalent_pair_prediction": 0.0,
        "pre_post_geometry": 0.0,
        "covalent_pair_contrastive": 0.0,
    }
    invariant_fields = (
        "requested_run_learning_rate",
        "training_carrier_fingerprints",
        "training_scheduled_task_ids",
        "formal_train_event_ids",
        "formal_validation_event_ids",
        "formal_test_event_ids",
        "validation_root_seeds",
        "validation_context_seed",
        "validation_profile_task_matrix",
        "planned_max_optimizer_step_count",
        "planned_validation4_call_count",
    )
    assert all(
        joint_payload[name] == diffusion_payload[name]
        for name in invariant_fields
    )
    for prefix in (
        "actual_checkpoint_load_count",
        "actual_model_construction_count",
        "actual_trainer_construction_count",
        "actual_optimizer_construction_count",
        "actual_fit_call_count",
        "actual_validation4_call_count",
        "actual_backward_count",
        "actual_optimizer_step_count",
    ):
        assert diffusion_payload[prefix] == 0
    assert diffusion_payload["parameter_update_performed"] is False

    observed = []

    def prepare_spy(**kwargs):
        observed.append(kwargs)
        return diffusion_only_prepared

    monkeypatch.setattr(
        subject,
        "prepare_covapie_batch001_train_validation_lifecycle_v1",
        prepare_spy,
    )
    assert subject.main([
        "--learning-rate",
        "0.0001",
        "--training-objective-profile",
        "diffusion_only",
    ]) == 0
    assert observed == [{
        "repository_root": None,
        "state_root": None,
        "cache_root": None,
        "learning_rate": 1.0e-4,
        "training_objective_profile": "diffusion_only",
    }]
    assert json.loads(capsys.readouterr().out) == diffusion_payload


@pytest.mark.parametrize(
    "invalid",
    (
        True,
        False,
        "0.001",
        float("nan"),
        float("inf"),
        float("-inf"),
        0.0,
        -1.0e-4,
        1.0e-2,
        1,
    ),
)
def test_invalid_learning_rate_is_rejected_before_preparation(
    invalid, monkeypatch
):
    directory_probe = mock.Mock(side_effect=_forbidden)
    monkeypatch.setattr(subject, "_require_directory", directory_probe)
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="RUN_LEARNING_RATE_NOT_EXPLICITLY_ALLOWED",
    ):
        subject.prepare_covapie_batch001_train_validation_lifecycle_v1(
            learning_rate=invalid
        )
    directory_probe.assert_not_called()


@pytest.mark.parametrize(
    "invalid",
    (
        "unknown",
        True,
        False,
        None,
        {},
        {"base_diffusion": 1.0},
    ),
)
def test_invalid_training_objective_profile_is_rejected_before_preparation(
    invalid, monkeypatch
):
    directory_probe = mock.Mock(side_effect=_forbidden)
    monkeypatch.setattr(subject, "_require_directory", directory_probe)
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="TRAINING_OBJECTIVE_PROFILE_NOT_EXPLICITLY_ALLOWED",
    ):
        subject.prepare_covapie_batch001_train_validation_lifecycle_v1(
            learning_rate=subject.CANDIDATE_LEARNING_RATE_V1,
            training_objective_profile=invalid,
        )
    directory_probe.assert_not_called()


def test_diffusion_only_without_explicit_1e4_is_rejected_before_preparation(
    monkeypatch,
):
    directory_probe = mock.Mock(side_effect=_forbidden)
    monkeypatch.setattr(subject, "_require_directory", directory_probe)
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="DIFFUSION_ONLY_REQUIRES_EXPLICIT_1E4_LEARNING_RATE",
    ):
        subject.prepare_covapie_batch001_train_validation_lifecycle_v1(
            training_objective_profile="diffusion_only"
        )
    directory_probe.assert_not_called()


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
        self.lr = 1.0e-3
        self.hparams = {"lr": 1.0e-3}
        self.covapie_current11_loss_weights = bounded_owner.DEFAULT_LOSS_WEIGHTS_V1
        self.train()
        self.branch.eval()
        self.weight.grad = torch.tensor([7.0, 11.0])


class _FakeOptimizer:
    def __init__(self, model, *, learning_rate):
        self.param_groups = [
            {"params": list(model.parameters()), "lr": learning_rate}
        ]
        self.state = {0: {"step": torch.tensor(5.0), "moment": torch.tensor([1.0])}}

    def state_dict(self):
        return {
            "state": self.state,
            "param_groups": [
                {
                    "params": list(range(len(self.param_groups[0]["params"]))),
                    "lr": self.param_groups[0]["lr"],
                }
            ],
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
    training_objective_profile,
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
        evidence_scope="SYNTHETIC_TEST_FIXTURE_NOT_REAL_LEARNING_RATE_EXPERIMENT",
        primary_metric_name=validation_owner.PRIMARY_METRIC_NAME_V1,
        validation_model_weight_source=validation_owner.VALIDATION_MODEL_WEIGHT_SOURCE_V1,
        declared_training_objective_profile=training_objective_profile,
        validated_actual_training_loss_weights=(
            model.covapie_current11_loss_weights
        ),
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


def _callbacks(prepared, *, post_offset=10.0, optimizer_learning_rate=None):
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
        assert model.lr == prepared.summary.requested_run_learning_rate
        assert kwargs["training_objective_profile"] == (
            prepared.summary.requested_training_objective_profile
        )
        assert model.covapie_current11_loss_weights == (
            prepared.summary.declared_training_loss_weights
        )
        assert kwargs["execution_opt_in"] is True
        assert kwargs["caller_confirms_model_is_quiescent"] is True
        assert not validation_owner._trainer_running(model)
        return _validation_fixture_result(
            prepared.validation,
            model=model,
            stage=stage,
            stage_evidence=kwargs["caller_stage_evidence"],
            training_objective_profile=kwargs["training_objective_profile"],
            offset=(0.0 if stage == subject.PRE_FIT_MODEL_STAGE_V1 else post_offset),
        )

    def fit(value):
        calls.append("fit")
        assert value is runtime
        assert model.lr == prepared.summary.requested_run_learning_rate
        assert model.covapie_current11_loss_weights == (
            prepared.summary.declared_training_loss_weights
        )
        runtime.fit_call_count += 1
        trainer.state.status = "running"
        trainer.fit_loop.running = True
        with torch.no_grad():
            model.weight.add_(1.0)
        optimizer = _FakeOptimizer(
            model,
            learning_rate=(
                prepared.summary.requested_run_learning_rate
                if optimizer_learning_rate is None
                else optimizer_learning_rate
            ),
        )
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


def _ready_synthetic_run(prepared):
    callbacks = _callbacks(prepared)
    run = subject.create_covapie_batch001_train_validation_lifecycle_run_v1(
        prepared=prepared
    )
    run.execution_consumed = True
    run.terminal_status = "RUNNING"
    run.runtime_build_request_count = 1
    run.runtime_build_completion_count = 1
    run.runtime = callbacks.runtime
    run.model = callbacks.model
    run.model_object_identity = id(callbacks.model)
    return run, callbacks


def test_candidate_lr_application_changes_only_effective_configuration_and_not_rng(
    candidate_prepared,
):
    run, callbacks = _ready_synthetic_run(candidate_prepared)
    before = validation_owner._snapshot_model_state_v1(callbacks.model)
    rng_before = torch.random.get_rng_state().clone()
    subject._apply_pre_fit_learning_rate_v1(
        run, synthetic_fixture_mode=True
    )
    after = validation_owner._snapshot_model_state_v1(callbacks.model)
    assert run.A0 is None
    assert run.model_learning_rate_before_application == 1.0e-3
    assert run.model_learning_rate_after_application == 1.0e-4
    assert run.constructor_hparams_learning_rate_after_application == 1.0e-3
    assert (
        run.learning_rate_application_stage
        == subject.LEARNING_RATE_APPLICATION_STAGE_V1
    )
    assert run.actual_optimizer_param_group_learning_rates == "NOT_OBSERVED"
    assert before.model_state_sha256 == after.model_state_sha256
    assert before.parameter_entries == after.parameter_entries
    assert before.buffer_entries == after.buffer_entries
    assert before.gradient_entries == after.gradient_entries
    assert before.module_entries == after.module_entries
    assert before.state_keys == after.state_keys
    assert before.training_flags == after.training_flags
    assert before.node_distribution_identity == after.node_distribution_identity
    assert before.node_distribution_sha256 == after.node_distribution_sha256
    assert before.configuration_sha256 != after.configuration_sha256
    assert torch.equal(torch.random.get_rng_state(), rng_before)


def test_optimizer_exists_fit_started_or_repeat_lr_application_fails_closed(
    candidate_prepared,
):
    optimizer_run, optimizer_callbacks = _ready_synthetic_run(candidate_prepared)
    optimizer_callbacks.trainer.optimizers = [
        _FakeOptimizer(
            optimizer_callbacks.model,
            learning_rate=subject.LEGACY_CONSTRUCTOR_LEARNING_RATE_V1,
        )
    ]
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="OPTIMIZER_MUST_NOT_EXIST_BEFORE_LEARNING_RATE_APPLICATION",
    ):
        subject._apply_pre_fit_learning_rate_v1(
            optimizer_run, synthetic_fixture_mode=True
        )
    assert optimizer_callbacks.model.lr == 1.0e-3

    fit_run, fit_callbacks = _ready_synthetic_run(candidate_prepared)
    fit_callbacks.runtime.fit_call_count = 1
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="RUN_LEARNING_RATE_APPLICATION_TOO_LATE",
    ):
        subject._apply_pre_fit_learning_rate_v1(
            fit_run, synthetic_fixture_mode=True
        )
    assert fit_callbacks.model.lr == 1.0e-3

    repeat_run, repeat_callbacks = _ready_synthetic_run(candidate_prepared)
    subject._apply_pre_fit_learning_rate_v1(
        repeat_run, synthetic_fixture_mode=True
    )
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="RUN_LEARNING_RATE_ALREADY_APPLIED",
    ):
        subject._apply_pre_fit_learning_rate_v1(
            repeat_run, synthetic_fixture_mode=True
        )
    assert repeat_callbacks.model.lr == 1.0e-4


def test_objective_profile_applies_before_a0_without_state_or_rng_change(
    prepared,
    diffusion_only_prepared,
):
    joint_run, joint_callbacks = _ready_synthetic_run(prepared)
    original_joint_weights = joint_callbacks.model.covapie_current11_loss_weights
    subject._apply_pre_fit_training_objective_profile_v1(
        joint_run, synthetic_fixture_mode=True
    )
    assert (
        joint_callbacks.model.covapie_current11_loss_weights
        is original_joint_weights
    )
    assert joint_run.requested_training_objective_profile == "joint_default"

    run, callbacks = _ready_synthetic_run(diffusion_only_prepared)
    before = validation_owner._snapshot_model_state_v1(callbacks.model)
    rng_before = torch.random.get_rng_state().clone()
    subject._apply_pre_fit_training_objective_profile_v1(
        run, synthetic_fixture_mode=True
    )
    after = validation_owner._snapshot_model_state_v1(callbacks.model)
    expected = diffusion_only_prepared.summary.declared_training_loss_weights
    assert run.A0 is None
    assert run.original_constructor_training_loss_weights == (
        bounded_owner.DEFAULT_LOSS_WEIGHTS_V1
    )
    assert run.model_training_loss_weights_before_application == (
        bounded_owner.DEFAULT_LOSS_WEIGHTS_V1
    )
    assert run.model_training_loss_weights_after_application == expected
    assert callbacks.model.covapie_current11_loss_weights is expected
    assert run.training_objective_application_stage == (
        subject.TRAINING_OBJECTIVE_APPLICATION_STAGE_V1
    )
    assert before.model_state_sha256 == after.model_state_sha256
    assert before.parameter_entries == after.parameter_entries
    assert before.buffer_entries == after.buffer_entries
    assert before.gradient_entries == after.gradient_entries
    assert before.module_entries == after.module_entries
    assert before.state_keys == after.state_keys
    assert before.training_flags == after.training_flags
    assert before.node_distribution_identity == after.node_distribution_identity
    assert before.node_distribution_sha256 == after.node_distribution_sha256
    assert before.configuration_sha256 != after.configuration_sha256
    assert torch.equal(torch.random.get_rng_state(), rng_before)


def test_optimizer_fit_or_repeat_objective_application_fails_closed(
    diffusion_only_prepared,
):
    optimizer_run, optimizer_callbacks = _ready_synthetic_run(
        diffusion_only_prepared
    )
    optimizer_callbacks.trainer.optimizers = [
        _FakeOptimizer(
            optimizer_callbacks.model,
            learning_rate=subject.CANDIDATE_LEARNING_RATE_V1,
        )
    ]
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="OPTIMIZER_MUST_NOT_EXIST_BEFORE_TRAINING_OBJECTIVE_APPLICATION",
    ):
        subject._apply_pre_fit_training_objective_profile_v1(
            optimizer_run, synthetic_fixture_mode=True
        )
    assert (
        optimizer_callbacks.model.covapie_current11_loss_weights
        == bounded_owner.DEFAULT_LOSS_WEIGHTS_V1
    )

    fit_run, fit_callbacks = _ready_synthetic_run(diffusion_only_prepared)
    fit_callbacks.runtime.fit_call_count = 1
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="RUN_TRAINING_OBJECTIVE_APPLICATION_TOO_LATE",
    ):
        subject._apply_pre_fit_training_objective_profile_v1(
            fit_run, synthetic_fixture_mode=True
        )

    repeat_run, repeat_callbacks = _ready_synthetic_run(
        diffusion_only_prepared
    )
    subject._apply_pre_fit_training_objective_profile_v1(
        repeat_run, synthetic_fixture_mode=True
    )
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="RUN_TRAINING_OBJECTIVE_ALREADY_APPLIED",
    ):
        subject._apply_pre_fit_training_objective_profile_v1(
            repeat_run, synthetic_fixture_mode=True
        )
    assert repeat_callbacks.model.covapie_current11_loss_weights == (
        diffusion_only_prepared.summary.declared_training_loss_weights
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
    assert run.legacy_constructor_learning_rate == 1.0e-3
    assert run.requested_run_learning_rate == 1.0e-3
    assert run.model_learning_rate_before_application == 1.0e-3
    assert run.model_learning_rate_after_application == 1.0e-3
    assert run.constructor_hparams_learning_rate_after_application == 1.0e-3
    assert (
        run.learning_rate_application_stage
        == subject.LEARNING_RATE_APPLICATION_STAGE_V1
    )
    assert run.actual_optimizer_param_group_learning_rates == (1.0e-3,)
    assert run.requested_training_objective_profile == "joint_default"
    assert run.declared_training_loss_weights == (
        bounded_owner.DEFAULT_LOSS_WEIGHTS_V1
    )
    assert run.original_constructor_training_loss_weights == (
        bounded_owner.DEFAULT_LOSS_WEIGHTS_V1
    )
    assert run.model_training_loss_weights_before_application == (
        bounded_owner.DEFAULT_LOSS_WEIGHTS_V1
    )
    assert run.model_training_loss_weights_after_application == (
        bounded_owner.DEFAULT_LOSS_WEIGHTS_V1
    )
    assert run.training_objective_application_stage == (
        subject.TRAINING_OBJECTIVE_APPLICATION_STAGE_V1
    )
    assert (
        run.pre_fit_validation_result.evidence_scope
        == "SYNTHETIC_TEST_FIXTURE_NOT_REAL_LEARNING_RATE_EXPERIMENT"
    )
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


def test_candidate_synthetic_lifecycle_applies_before_a0_preserves_isolation_and_accepts_worse_metric(
    candidate_prepared,
):
    callbacks = _callbacks(candidate_prepared, post_offset=10.0)
    rng_before = torch.random.get_rng_state().clone()
    run = _execute_synthetic(candidate_prepared, callbacks)
    assert callbacks.calls == ["build", "pre", "fit", "post"]
    assert run.terminal_status == "COMPLETED"
    assert run.requested_run_learning_rate == 1.0e-4
    assert run.requested_run_learning_rate_differs_from_legacy_reference
    assert run.model_learning_rate_before_application == 1.0e-3
    assert run.model_learning_rate_after_application == 1.0e-4
    assert run.constructor_hparams_learning_rate_after_application == 1.0e-3
    assert (
        run.learning_rate_application_stage
        == subject.LEARNING_RATE_APPLICATION_STAGE_V1
    )
    assert run.actual_optimizer_param_group_learning_rates == (1.0e-4,)
    assert run.A0.configuration_sha256 == run.A1.configuration_sha256
    assert run.B0.configuration_sha256 == run.B1.configuration_sha256
    assert run.A1.configuration_sha256 == run.B0.configuration_sha256
    assert run.pre_fit_state_isolation_pass is True
    assert run.post_fit_state_isolation_pass is True
    assert run.post_fit_optimizer_isolation_pass is True
    assert run.same_model_and_parameter_objects_pass is True
    assert run.paired_comparison.event_macro_post_minus_pre == pytest.approx(10.0)
    assert torch.equal(torch.random.get_rng_state(), rng_before)


def test_diffusion_only_synthetic_lifecycle_passes_same_profile_to_both_evaluations(
    diffusion_only_prepared,
):
    callbacks = _callbacks(diffusion_only_prepared, post_offset=10.0)
    run = _execute_synthetic(diffusion_only_prepared, callbacks)
    expected = diffusion_only_prepared.summary.declared_training_loss_weights
    assert callbacks.calls == ["build", "pre", "fit", "post"]
    assert run.terminal_status == "COMPLETED"
    assert run.requested_run_learning_rate == 1.0e-4
    assert run.requested_training_objective_profile == "diffusion_only"
    assert run.original_constructor_training_loss_weights == (
        bounded_owner.DEFAULT_LOSS_WEIGHTS_V1
    )
    assert run.model_training_loss_weights_after_application == expected
    assert callbacks.model.covapie_current11_loss_weights is expected
    assert (
        run.pre_fit_validation_result.declared_training_objective_profile
        == run.post_fit_validation_result.declared_training_objective_profile
        == "diffusion_only"
    )
    assert (
        run.pre_fit_validation_result.validated_actual_training_loss_weights
        == run.post_fit_validation_result.validated_actual_training_loss_weights
        == expected
    )
    assert run.A0.configuration_sha256 == run.A1.configuration_sha256
    assert run.A1.configuration_sha256 == run.B0.configuration_sha256
    assert run.B0.configuration_sha256 == run.B1.configuration_sha256
    assert run.paired_comparison.event_macro_post_minus_pre == pytest.approx(10.0)


def test_optimizer_observation_mismatch_fails_closed(candidate_prepared):
    callbacks = _callbacks(
        candidate_prepared,
        optimizer_learning_rate=subject.LEGACY_CONSTRUCTOR_LEARNING_RATE_V1,
    )
    run = subject.create_covapie_batch001_train_validation_lifecycle_run_v1(
        prepared=candidate_prepared
    )
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="BOUNDED_FIT_COMPLETION_STATE_REJECTED",
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
    assert run.failure_stage == "BOUNDED_FIT"
    assert run.actual_optimizer_param_group_learning_rates == (1.0e-3,)
    assert run.post_fit_validation_result is None


def test_production_configure_optimizers_reads_selected_model_lr_without_construction():
    ddpm_parameters = (object(), object())
    auxiliary_parameters = (object(),)
    fake_self = SimpleNamespace(
        ddpm=SimpleNamespace(parameters=lambda: ddpm_parameters),
        covapie_current11_auxiliary_model_v1=SimpleNamespace(
            parameters=lambda: auxiliary_parameters
        ),
        lr=subject.CANDIDATE_LEARNING_RATE_V1,
    )
    optimizer_sentinel = object()
    adamw_factory = mock.Mock(return_value=optimizer_sentinel)
    with mock.patch.object(torch.optim, "AdamW", new=adamw_factory):
        observed = (
            bounded_owner.CovapieBatch001BoundedTrainingLigandPocketDDPMV1
            .configure_optimizers(fake_self)
        )
    assert observed is optimizer_sentinel
    adamw_factory.assert_called_once_with(
        list(ddpm_parameters) + list(auxiliary_parameters),
        lr=subject.CANDIDATE_LEARNING_RATE_V1,
        amsgrad=True,
        weight_decay=1.0e-12,
    )


def test_SYNTHETIC_published_loss_weighting_preserves_all_raw_diagnostics(prepared):
    # SYNTHETIC: fixed tensors only; this is not a model, training, or validation run.
    supervision = prepared.training.carriers[0].supervision
    sample_count = len(supervision.sample_training_admitted)
    ligand_count = len(supervision.ligand_role_id)
    pocket_count = len(supervision.target_residue_membership_mask)
    pair_count = int(supervision.pair_candidate_offsets[-1].item())
    model_output = current_loss_owner.CovapieCurrent11ModelOutputV1(
        diffusion_epsilon_prediction_ligand=torch.zeros(ligand_count, 13),
        denoised_ligand_xh=torch.zeros(ligand_count, 13),
        diffusion_timestep_int=torch.ones(sample_count, dtype=torch.long),
        ligand_node_hidden=torch.zeros(ligand_count, 1),
        pocket_node_hidden=torch.zeros(pocket_count, 1),
        role_mask_anchor_hidden_delta=torch.zeros(ligand_count, 1),
        pair_embeddings=torch.zeros(pair_count, 1),
        pair_logits=torch.linspace(-1.0, 1.0, pair_count),
        pre_post_geometry_predictions_angstrom=torch.ones(pair_count, 2),
        target_pair_consistency=torch.ones(sample_count, dtype=torch.bool),
        canonical_task_id=supervision.canonical_task_id,
        pair_candidate_offsets=supervision.pair_candidate_offsets,
        pair_candidate_batch_index=supervision.pair_candidate_batch_index,
        pair_candidate_ligand_local_index=(
            supervision.pair_candidate_ligand_local_index
        ),
        pair_candidate_residue_local_index=(
            supervision.pair_candidate_residue_local_index
        ),
        pair_candidate_ligand_flat_index=(
            supervision.pair_candidate_ligand_flat_index
        ),
        pair_candidate_pocket_flat_index=(
            supervision.pair_candidate_pocket_flat_index
        ),
    )
    trace = SimpleNamespace(
        base_objective_per_sample=torch.linspace(
            0.25, 1.25, sample_count
        )
    )
    profile_weights = dict(
        validation_owner.TRAINING_OBJECTIVE_PROFILE_LOSS_WEIGHTS_V1
    )
    joint = current_loss_owner.compute_covapie_current11_training_losses_v1(
        model_output=model_output,
        supervision=supervision,
        diffusion_trace=trace,
        loss_weights=profile_weights["joint_default"],
    )
    diffusion_only = (
        current_loss_owner.compute_covapie_current11_training_losses_v1(
            model_output=model_output,
            supervision=supervision,
            diffusion_trace=trace,
            loss_weights=profile_weights["diffusion_only"],
        )
    )
    raw_names = (
        "loss_base_diffusion",
        "loss_covalent_pair_prediction",
        "loss_pre_post_geometry",
        "loss_covalent_pair_contrastive",
    )
    count_names = (
        "base_diffusion_valid_sample_count",
        "covalent_pair_prediction_valid_sample_count",
        "pre_post_geometry_valid_sample_count",
        "covalent_pair_contrastive_valid_sample_count",
    )
    assert all(
        torch.equal(getattr(joint, name), getattr(diffusion_only, name))
        for name in raw_names
    )
    assert all(
        getattr(joint, name) == getattr(diffusion_only, name)
        for name in count_names
    )
    assert torch.allclose(
        joint.loss_total,
        joint.loss_base_diffusion
        + joint.loss_covalent_pair_prediction
        + 0.1 * joint.loss_covalent_pair_contrastive,
    )
    assert torch.equal(
        diffusion_only.loss_total,
        diffusion_only.loss_base_diffusion,
    )
    assert joint.loss_covalent_pair_prediction.item() > 0.0
    assert joint.loss_covalent_pair_contrastive.item() > 0.0
    training_step_source = inspect.getsource(
        bounded_owner.CovapieBatch001BoundedTrainingLigandPocketDDPMV1
        ._shared_covapie_training_step_v1
    )
    assert '"loss": losses.loss_total' in training_step_source


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


def test_objective_weight_drift_during_validation_is_not_repaired_or_accepted(
    diffusion_only_prepared,
):
    callbacks = _callbacks(diffusion_only_prepared)
    ordinary_evaluate = callbacks.evaluate

    def drift(**kwargs):
        result = ordinary_evaluate(**kwargs)
        callbacks.model.covapie_current11_loss_weights = (
            bounded_owner.DEFAULT_LOSS_WEIGHTS_V1
        )
        return result

    callbacks.evaluate = drift
    run = subject.create_covapie_batch001_train_validation_lifecycle_run_v1(
        prepared=diffusion_only_prepared
    )
    with pytest.raises(
        subject.CovapieBatch001TrainValidationLifecycleExecutionErrorV1,
        match="PRE_FIT_VALIDATION_FAILED",
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
    assert callbacks.calls == ["build", "pre"]
    assert run.pre_fit_state_isolation_pass is False
    assert run.fit_request_count == 0
    assert (
        callbacks.model.covapie_current11_loss_weights
        is bounded_owner.DEFAULT_LOSS_WEIGHTS_V1
    )


def test_objective_weight_drift_during_fit_prevents_post_validation(
    diffusion_only_prepared,
):
    callbacks = _callbacks(diffusion_only_prepared)
    ordinary_fit = callbacks.fit

    def drift(runtime):
        ordinary_fit(runtime)
        callbacks.model.covapie_current11_loss_weights = (
            bounded_owner.DEFAULT_LOSS_WEIGHTS_V1
        )

    callbacks.fit = drift
    run = subject.create_covapie_batch001_train_validation_lifecycle_run_v1(
        prepared=diffusion_only_prepared
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
            runtime_builder=callbacks.build,
            evaluator=callbacks.evaluate,
            fit_invoker=callbacks.fit,
            synthetic_fixture_mode=True,
        )
    assert callbacks.calls == ["build", "pre", "fit"]
    assert run.fit_completion_count == 1
    assert run.validation_request_count == 1
    assert run.post_fit_validation_result is None


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
            training_objective_profile=kwargs["training_objective_profile"],
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
            expected_training_objective_profile=(
                run.requested_training_objective_profile
            ),
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
