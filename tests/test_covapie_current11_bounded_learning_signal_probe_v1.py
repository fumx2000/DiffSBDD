from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch
from torch import nn

from covalent_ext import (
    covapie_current11_bounded_learning_signal_probe_v1 as subject,
)
from covalent_ext import (
    covapie_current11_formal_trainer_v1 as formal,
)
from covalent_ext import (
    covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1
    as context_bridge,
)
from scripts import (
    check_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1
    as bridge_checker,
)


ROOT = Path(__file__).resolve().parents[1]
STATE = (ROOT.parent / "covapie-state").resolve()
CHECKPOINT = ROOT / "checkpoints/crossdocked_fullatom_cond.ckpt"
ERROR = subject.BOUNDED_LEARNING_SIGNAL_PROBE_ERROR_V1
SCHEMA = subject.BOUNDED_LEARNING_SIGNAL_PROBE_SCHEMA_V1
EXPECTED_SEEDS = (
    3607114108067373088,
    5234281069836337458,
    943838421517204528,
    8302249223822712381,
    1647965958990608988,
)
EXPECTED_TASKS = (
    (3, 2, 3, 0, 2, 4, 0, 0, 4, 4, 1),
    (4, 3, 4, 1, 3, 0, 1, 1, 0, 0, 2),
    (0, 4, 0, 2, 4, 1, 2, 2, 1, 1, 3),
    (1, 0, 1, 3, 0, 2, 3, 3, 2, 2, 4),
    (2, 1, 2, 4, 1, 3, 4, 4, 3, 3, 0),
)


def _assert_probe_error(callable_object) -> None:
    with pytest.raises(ValueError) as error:
        callable_object()
    assert str(error.value) == ERROR


@pytest.fixture(scope="module")
def real_session_and_attached_batch():
    session = formal.build_covapie_current11_formal_train_only_session_v1(
        repository_root=ROOT,
        state_root=STATE,
        legacy_init_checkpoint=CHECKPOINT,
    )
    remap_context, evidence = bridge_checker._acquire_remap_context(
        lifecycle="precommit-untracked",
        repo_root=ROOT,
        state_root=STATE,
    )
    assert evidence["test_harness_only"] is True
    assert evidence["production_monkeypatch_used"] is False
    compiler_context = (
        context_bridge.build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1(
            remap_context=remap_context
        )
    )
    model = session.model
    model._covapie_current11_task2_remap_context_v1 = remap_context
    model._covapie_current11_task2_compiler_context_v1 = compiler_context
    model.setup("fit")
    raw_batch = next(iter(model.train_dataloader()))
    attached_batch = model.on_before_batch_transfer(raw_batch, 0)
    assert model.current_epoch == 0
    assert model.global_step == 0
    return session, attached_batch


@pytest.fixture(scope="module")
def real_preprobe_pair(real_session_and_attached_batch):
    session, attached_batch = real_session_and_attached_batch
    first = subject.run_covapie_current11_deterministic_exact5_probe_v1(
        model=session.model,
        attached_batch=attached_batch,
    )
    second = subject.run_covapie_current11_deterministic_exact5_probe_v1(
        model=session.model,
        attached_batch=attached_batch,
    )
    return first, second


def _make_epoch(
    epoch: int,
    *,
    base: float,
    pair: float,
    geometry: float,
    contrastive: float,
    total: float,
    margin: float,
) -> subject.CovapieCurrent11ProbeEpochResultV1:
    return subject.CovapieCurrent11ProbeEpochResultV1(
        schema_version=SCHEMA,
        probe_epoch=epoch,
        derived_epoch_seed=EXPECTED_SEEDS[epoch],
        canonical_task_ids=EXPECTED_TASKS[epoch],
        diffusion_timesteps=tuple(epoch + index for index in range(11)),
        effective_sampled_epsilon_sha256=f"{epoch + 1:064x}",
        loss_base_diffusion=base,
        loss_covalent_pair_prediction=pair,
        loss_pre_post_geometry=geometry,
        loss_covalent_pair_contrastive=contrastive,
        loss_total=total,
        base_diffusion_valid_sample_count=11,
        covalent_pair_prediction_valid_sample_count=11,
        pre_post_geometry_valid_sample_count=0,
        covalent_pair_contrastive_valid_sample_count=11,
        geometry_head_forward=True,
        geometry_predictions_finite=True,
        geometry_formal_weight=0.0,
        target_pair_consistency=True,
        pair_candidate_consistency=True,
        pair_positive_logit_mean=2.0,
        pair_negative_logit_mean=1.0,
        pair_margin_mean=margin,
        pair_rank_mean=1.0,
        pair_top1_accuracy=1.0,
        pair_rank_by_sample=(1,) * 11,
        pair_top1_by_sample=(True,) * 11,
    )


def _make_probe(
    *,
    base: float = 5.0,
    pair: float = 3.0,
    geometry: float = 0.0,
    contrastive: float = 2.0,
    total: float = 8.2,
    margin: float = 1.0,
    parameter_digest: str = "parameters",
) -> subject.CovapieCurrent11DeterministicExact5ProbeResultV1:
    epochs = tuple(
        _make_epoch(
            epoch,
            base=base,
            pair=pair,
            geometry=geometry,
            contrastive=contrastive,
            total=total,
            margin=margin,
        )
        for epoch in range(5)
    )
    return subject.CovapieCurrent11DeterministicExact5ProbeResultV1(
        schema_version=SCHEMA,
        probe_seed=20_260_816,
        derived_epoch_seeds=EXPECTED_SEEDS,
        epoch_results=epochs,
        sample_task_evaluation_count=55,
        input_configuration_fingerprint_before="input-config",
        input_configuration_fingerprint_after="input-config",
        probe_base_mean=base,
        probe_pair_mean=pair,
        probe_geometry_mean=geometry,
        probe_contrastive_mean=contrastive,
        probe_total_mean=total,
        pair_positive_logit_mean=2.0,
        pair_negative_logit_mean=1.0,
        pair_margin_mean=margin,
        pair_rank_mean=1.0,
        pair_top1_accuracy=1.0,
        parameter_digest_before=parameter_digest,
        parameter_digest_after=parameter_digest,
        buffer_digest_before="buffers",
        buffer_digest_after="buffers",
        gradient_digest_before="gradients",
        gradient_digest_after="gradients",
        mode_digest_before="modes",
        mode_digest_after="modes",
        batch_tensor_digest_before="batch",
        batch_tensor_digest_after="batch",
        trainer_counter_digest_before="counters",
        trainer_counter_digest_after="counters",
        parameter_unchanged=True,
        buffer_unchanged=True,
        gradient_state_unchanged=True,
        mode_flags_restored=True,
        batch_unchanged=True,
        trainer_counters_unchanged=True,
        torch_cpu_rng_digest_before="rng",
        torch_cpu_rng_digest_after="rng",
        probe_rng_used_domains=("torch_cpu",),
        cpu_rng_state_restored=True,
        all_probe_rng_domains_restored=True,
        global_rng_restored=True,
        probe_model_mode="train",
        no_grad_used=True,
        optimizer_created=False,
        backward_called=False,
        optimizer_step_called=False,
        stateful_train_mode_layer_blocker_found=False,
    )


def _repeatability(
    *, repeatable: bool,
) -> subject.CovapieCurrent11ProbeRepeatabilityResultV1:
    return subject.CovapieCurrent11ProbeRepeatabilityResultV1(
        schema_version=SCHEMA,
        repeatable=repeatable,
        outcome=(
            "LEARNING_SIGNAL_PASS" if repeatable else "PROBE_NONDETERMINISTIC"
        ),
        exact_evidence_equal=repeatable,
        maximum_absolute_discrepancies=tuple(
            (name, 0.0) for name in subject._FLOAT_METRIC_FIELDS_V1
        ),
    )


def _decision(outcome: str) -> subject.CovapieCurrent11LearningSignalDecisionV1:
    return subject.CovapieCurrent11LearningSignalDecisionV1(
        schema_version=SCHEMA,
        outcome=outcome,
        tolerances=(),
        improvements=(),
        total_criterion_passed=(outcome == "LEARNING_SIGNAL_PASS"),
        covalent_criterion_passed=(outcome == "LEARNING_SIGNAL_PASS"),
        geometry_in_acceptance=False,
    )


def test_seed_derivation_is_exact_unique_and_in_signed_63_bit_domain() -> None:
    seeds = tuple(
        subject._derive_covapie_current11_probe_epoch_seed_v1(
            probe_seed=20_260_816, probe_epoch=epoch
        )
        for epoch in range(5)
    )
    assert seeds == EXPECTED_SEEDS
    assert len(set(seeds)) == 5
    assert all(0 <= seed <= 2**63 - 1 for seed in seeds)


@pytest.mark.parametrize("seed", (True, -1, 2**63, 1.0, "20260816"))
def test_invalid_probe_seed_rejected(seed: object) -> None:
    _assert_probe_error(
        lambda: subject.run_covapie_current11_deterministic_exact5_probe_v1(
            model=object(), attached_batch={}, probe_seed=seed
        )
    )


@pytest.mark.parametrize("epoch", (True, -1, 5, 0.0, "0", None))
def test_invalid_probe_epoch_rejected(epoch: object) -> None:
    _assert_probe_error(
        lambda: subject._derive_covapie_current11_probe_epoch_seed_v1(
            probe_seed=20_260_816, probe_epoch=epoch
        )
    )


def test_real_epoch_zero_published_forward_has_bit_exact_probe_path_parity(
    real_session_and_attached_batch,
) -> None:
    session, attached_batch = real_session_and_attached_batch
    model = session.model
    assert model.current_epoch == 0
    modes_before = tuple(
        (name, module.training) for name, module in model.named_modules()
    )
    parameters_before = {
        name: parameter.detach().clone()
        for name, parameter in model.named_parameters()
    }
    buffers_before = {
        name: buffer.detach().clone() for name, buffer in model.named_buffers()
    }
    gradients_before = {
        name: None if parameter.grad is None else parameter.grad.detach().clone()
        for name, parameter in model.named_parameters()
    }
    batch_before = subject._value_digest_v1(
        attached_batch, root_name="attached_batch"
    )
    rng_before = torch.random.get_rng_state().clone()
    seed = EXPECTED_SEEDS[0]
    try:
        model.train()
        with torch.random.fork_rng(devices=[], enabled=True):
            torch.manual_seed(seed)
            with torch.no_grad():
                published = model.forward(attached_batch)
        with torch.random.fork_rng(devices=[], enabled=True):
            torch.manual_seed(seed)
            with torch.no_grad():
                probe = subject._run_covapie_current11_probe_epoch_forward_v1(
                    model=model,
                    attached_batch=attached_batch,
                    probe_epoch=0,
                )
    finally:
        subject._restore_mode_map_v1(model, modes_before)

    supervision_fields = (
        "canonical_task_id",
        "canonical_task_valid",
        "pair_candidate_offsets",
        "pair_candidate_batch_index",
        "pair_candidate_ligand_local_index",
        "pair_candidate_residue_local_index",
        "pair_candidate_ligand_flat_index",
        "pair_candidate_pocket_flat_index",
        "pair_candidate_is_positive",
        "pair_candidate_is_negative",
        "pair_positive_candidate_index",
        "pair_positive_candidate_valid",
        "pair_head_candidate_loss_mask",
        "pair_contrastive_sample_loss_mask",
    )
    trace_fields = (
        "diffusion_timestep_int",
        "sampled_epsilon_ligand",
        "base_objective_per_sample",
        "role_mask_anchor_hidden_delta",
        "diffusion_epsilon_prediction_ligand",
        "diffusion_epsilon_prediction_pocket",
        "denoised_ligand_xh",
        "ligand_node_hidden",
        "pocket_node_hidden",
    )
    model_output_fields = (
        "canonical_task_id",
        "diffusion_timestep_int",
        "diffusion_epsilon_prediction_ligand",
        "denoised_ligand_xh",
        "ligand_node_hidden",
        "pocket_node_hidden",
        "role_mask_anchor_hidden_delta",
        "pair_embeddings",
        "pair_logits",
        "pre_post_geometry_predictions_angstrom",
        "target_pair_consistency",
        "pair_candidate_offsets",
        "pair_candidate_batch_index",
        "pair_candidate_ligand_local_index",
        "pair_candidate_residue_local_index",
        "pair_candidate_ligand_flat_index",
        "pair_candidate_pocket_flat_index",
    )
    loss_tensor_fields = (
        "loss_base_diffusion",
        "loss_covalent_pair_prediction",
        "loss_pre_post_geometry",
        "loss_covalent_pair_contrastive",
        "loss_total",
    )
    loss_count_fields = (
        "base_diffusion_valid_sample_count",
        "covalent_pair_prediction_valid_sample_count",
        "pre_post_geometry_valid_sample_count",
        "covalent_pair_contrastive_valid_sample_count",
    )
    for name in supervision_fields:
        assert torch.equal(
            getattr(published.supervision, name), getattr(probe.supervision, name)
        )
    for name in trace_fields:
        assert torch.equal(
            getattr(published.diffusion_trace, name),
            getattr(probe.diffusion_trace, name),
        )
    for name in model_output_fields:
        assert torch.equal(
            getattr(published.model_output, name),
            getattr(probe.model_output, name),
        )
    for name in loss_tensor_fields:
        assert torch.equal(
            getattr(published.loss_output, name), getattr(probe.loss_output, name)
        )
    for name in loss_count_fields:
        assert getattr(published.loss_output, name) == getattr(probe.loss_output, name)
    assert subject._canonical_tensor_sha256_v1(
        name="effective_sampled_epsilon_ligand",
        value=published.diffusion_trace.sampled_epsilon_ligand,
    ) == subject._canonical_tensor_sha256_v1(
        name="effective_sampled_epsilon_ligand",
        value=probe.diffusion_trace.sampled_epsilon_ligand,
    )
    assert torch.equal(torch.random.get_rng_state(), rng_before)
    assert tuple((name, module.training) for name, module in model.named_modules()) == modes_before
    assert all(
        torch.equal(parameter, parameters_before[name])
        for name, parameter in model.named_parameters()
    )
    assert all(
        torch.equal(buffer, buffers_before[name])
        for name, buffer in model.named_buffers()
    )
    for name, parameter in model.named_parameters():
        before = gradients_before[name]
        assert (before is None) == (parameter.grad is None)
        if before is not None:
            assert torch.equal(before, parameter.grad)
    assert subject._value_digest_v1(
        attached_batch, root_name="attached_batch"
    ) == batch_before


def test_real_preprobe_repeatability_exact5_coverage_and_rng_evidence(
    real_preprobe_pair,
) -> None:
    first, second = real_preprobe_pair
    assert first.derived_epoch_seeds == EXPECTED_SEEDS
    assert tuple(epoch.canonical_task_ids for epoch in first.epoch_results) == EXPECTED_TASKS
    assert first.sample_task_evaluation_count == 55
    for sample in range(11):
        assert {epoch.canonical_task_ids[sample] for epoch in first.epoch_results} == {
            0, 1, 2, 3, 4
        }
    repeatability = subject.validate_covapie_current11_preprobe_repeatability_v1(
        first=first, second=second
    )
    assert repeatability.repeatable is True
    assert repeatability.exact_evidence_equal is True
    assert dict(repeatability.maximum_absolute_discrepancies) == {
        metric: 0.0 for metric in subject._FLOAT_METRIC_FIELDS_V1
    }
    for left, right in zip(first.epoch_results, second.epoch_results, strict=True):
        assert left.diffusion_timesteps == right.diffusion_timesteps
        assert left.effective_sampled_epsilon_sha256 == right.effective_sampled_epsilon_sha256
    assert first.probe_rng_used_domains == ("torch_cpu",)
    assert first.cpu_rng_state_restored is True
    assert first.all_probe_rng_domains_restored is True
    assert first.global_rng_restored is True


def test_real_probe_preserves_model_gradient_mode_batch_and_trainer_state(
    real_preprobe_pair,
) -> None:
    for result in real_preprobe_pair:
        assert result.parameter_unchanged is True
        assert result.parameter_digest_before == result.parameter_digest_after
        assert result.buffer_unchanged is True
        assert result.buffer_digest_before == result.buffer_digest_after
        assert result.gradient_state_unchanged is True
        assert result.gradient_digest_before == result.gradient_digest_after
        assert result.mode_flags_restored is True
        assert result.mode_digest_before == result.mode_digest_after
        assert result.batch_unchanged is True
        assert result.batch_tensor_digest_before == result.batch_tensor_digest_after
        assert result.trainer_counters_unchanged is True
        assert result.trainer_counter_digest_before == result.trainer_counter_digest_after
        assert result.optimizer_created is False
        assert result.backward_called is False
        assert result.optimizer_step_called is False
        assert result.no_grad_used is True
        assert all(
            epoch.geometry_formal_weight == 0.0
            for epoch in result.epoch_results
        )


def test_real_probe_accepts_controlled_finite_postfit_state(
    real_session_and_attached_batch,
) -> None:
    session, attached_batch = real_session_and_attached_batch
    model = session.model
    parameter = next(model.parameters())
    parameter_before = parameter.detach().clone()
    gradient_before = (
        None if parameter.grad is None else parameter.grad.detach().clone()
    )
    modes_before = tuple(
        (name, module.training) for name, module in model.named_modules()
    )
    trainer_before = model._trainer
    try:
        with torch.no_grad():
            parameter.view(-1)[0].add_(0.001)
        assert not torch.equal(parameter, parameter_before)
        parameter.grad = torch.full_like(parameter, 0.25)
        model.eval()
        model._trainer = SimpleNamespace(
            current_epoch=5,
            global_step=5,
            optimizers=[object()],
        )
        result = subject.run_covapie_current11_deterministic_exact5_probe_v1(
            model=model,
            attached_batch=attached_batch,
        )
        assert result.parameter_unchanged is True
        assert result.gradient_state_unchanged is True
        assert result.mode_flags_restored is True
        assert model.training is False
        assert result.trainer_counters_unchanged is True
        assert result.trainer_counter_digest_before == (
            result.trainer_counter_digest_after
        )
    finally:
        with torch.no_grad():
            parameter.copy_(parameter_before)
        parameter.grad = gradient_before
        subject._restore_mode_map_v1(model, modes_before)
        model._trainer = trainer_before


def test_cpu_rng_and_modes_restore_when_probe_epoch_raises(
    monkeypatch: pytest.MonkeyPatch,
    real_session_and_attached_batch,
) -> None:
    session, attached_batch = real_session_and_attached_batch
    model = session.model
    rng_before = torch.random.get_rng_state().clone()
    modes_before = tuple(
        (name, module.training) for name, module in model.named_modules()
    )

    def injected_failure(**unused):
        del unused
        torch.rand(17)
        raise RuntimeError("injected probe failure")

    monkeypatch.setattr(
        subject, "_run_covapie_current11_probe_epoch_forward_v1", injected_failure
    )
    _assert_probe_error(
        lambda: subject.run_covapie_current11_deterministic_exact5_probe_v1(
            model=model, attached_batch=attached_batch
        )
    )
    assert torch.equal(torch.random.get_rng_state(), rng_before)
    assert tuple((name, module.training) for name, module in model.named_modules()) == modes_before


def test_future_stateful_training_layer_fails_before_probe_forward(
    real_session_and_attached_batch,
) -> None:
    session, attached_batch = real_session_and_attached_batch
    model = session.model
    model.add_module("_future_probe_batch_norm", nn.BatchNorm1d(1))
    try:
        _assert_probe_error(
            lambda: subject.run_covapie_current11_deterministic_exact5_probe_v1(
                model=model, attached_batch=attached_batch
            )
        )
    finally:
        delattr(model, "_future_probe_batch_norm")


def test_pair_ranking_is_per_sample_and_ties_are_pessimistic() -> None:
    logits = torch.tensor([2.0, 1.0, 2.0] + [3.0, 0.0] * 10)
    offsets = torch.tensor([0, 3] + [3 + 2 * index for index in range(1, 11)])
    positive = torch.tensor([0] + [3 + 2 * index for index in range(10)])
    negative = torch.ones(23, dtype=torch.bool)
    negative[positive] = False
    result = subject._compute_pair_ranking_diagnostics_v1(
        pair_logits=logits,
        pair_candidate_offsets=offsets,
        pair_positive_candidate_index=positive,
        pair_positive_candidate_valid=torch.ones(11, dtype=torch.bool),
        pair_candidate_is_negative=negative,
        pair_head_candidate_loss_mask=torch.ones(23, dtype=torch.bool),
    )
    assert result.positive_logits[0] == 2.0
    assert result.negative_logit_means[0] == 1.5
    assert result.margins[0] == 0.5
    assert result.ranks[0] == 2
    assert result.top1[0] is False
    assert result.ranks[1:] == (1,) * 10
    assert result.top1[1:] == (True,) * 10
    assert result.negative_logit_mean == pytest.approx(1.5 / 11)
    assert result.margin_mean == pytest.approx(30.5 / 11)
    assert result.top1_accuracy == pytest.approx(10 / 11)


def test_repeatability_uses_documented_float32_limit_and_exact_fields() -> None:
    first = _make_probe()
    limit = 8 * 1.1920928955078125e-7 * max(1.0, first.probe_total_mean)
    within = _make_probe(total=first.probe_total_mean + 0.5 * limit)
    outside = _make_probe(total=first.probe_total_mean + 2.0 * limit)
    assert subject.validate_covapie_current11_preprobe_repeatability_v1(
        first=first, second=within
    ).repeatable is True
    assert subject.validate_covapie_current11_preprobe_repeatability_v1(
        first=first, second=outside
    ).outcome == "PROBE_NONDETERMINISTIC"
    changed_epoch = replace(
        first.epoch_results[0], diffusion_timesteps=(99,) * 11
    )
    changed = replace(first, epoch_results=(changed_epoch,) + first.epoch_results[1:])
    assert subject.validate_covapie_current11_preprobe_repeatability_v1(
        first=first, second=changed
    ).repeatable is False


def test_tau_formula_strict_boundary_geometry_exclusion_and_outcomes() -> None:
    before = _make_probe()
    repeat = _make_probe()
    tau_total = 1e-6 + 1e-5 * abs(before.probe_total_mean)
    exact_boundary = _make_probe(total=before.probe_total_mean - tau_total)
    boundary = subject.compare_covapie_current11_learning_signal_v1(
        before=before, repeated_before=repeat, after=exact_boundary
    )
    assert dict(boundary.tolerances)["probe_total"] == tau_total
    assert boundary.total_criterion_passed is False
    assert boundary.outcome == "NO_LEARNING_SIGNAL"

    passed = subject.compare_covapie_current11_learning_signal_v1(
        before=before,
        repeated_before=repeat,
        after=_make_probe(total=8.0, pair=2.8, parameter_digest="post"),
    )
    assert passed.outcome == "LEARNING_SIGNAL_PASS"
    assert passed.total_criterion_passed is True
    assert passed.covalent_criterion_passed is True

    weak = subject.compare_covapie_current11_learning_signal_v1(
        before=before,
        repeated_before=repeat,
        after=_make_probe(pair=2.8, parameter_digest="post"),
    )
    assert weak.outcome == "LEARNING_SIGNAL_WEAK"

    no_signal = subject.compare_covapie_current11_learning_signal_v1(
        before=before,
        repeated_before=repeat,
        after=_make_probe(geometry=0.0, parameter_digest="post"),
    )
    assert no_signal.outcome == "NO_LEARNING_SIGNAL"
    assert no_signal.geometry_in_acceptance is False

    changed_epoch = replace(
        repeat.epoch_results[0], effective_sampled_epsilon_sha256="f" * 64
    )
    nondeterministic_repeat = replace(
        repeat, epoch_results=(changed_epoch,) + repeat.epoch_results[1:]
    )
    nondeterministic = subject.compare_covapie_current11_learning_signal_v1(
        before=before,
        repeated_before=nondeterministic_repeat,
        after=_make_probe(parameter_digest="post"),
    )
    assert nondeterministic.outcome == "PROBE_NONDETERMINISTIC"

    training_failed = subject.compare_covapie_current11_learning_signal_v1(
        before=before,
        repeated_before=repeat,
        after=replace(_make_probe(parameter_digest="post"), probe_total_mean=float("nan")),
    )
    assert training_failed.outcome == "TRAINING_FAILED"
    assert set(subject.BOUNDED_LEARNING_SIGNAL_OUTCOMES_V1) == {
        "LEARNING_SIGNAL_PASS",
        "LEARNING_SIGNAL_WEAK",
        "NO_LEARNING_SIGNAL",
        "PROBE_NONDETERMINISTIC",
        "TRAINING_FAILED",
    }


def test_pre_to_post_fixed_evidence_excludes_legitimate_training_progress() -> None:
    before = _make_probe()
    after = replace(
        _make_probe(parameter_digest="trained-parameters"),
        gradient_digest_before="postfit-gradients",
        gradient_digest_after="postfit-gradients",
        mode_digest_before="postfit-modes",
        mode_digest_after="postfit-modes",
        trainer_counter_digest_before="epoch5-step5",
        trainer_counter_digest_after="epoch5-step5",
    )
    assert subject._same_fixed_probe_evidence_v1(before, after) is True
    assert subject._same_fixed_probe_evidence_v1(
        before,
        replace(after, input_configuration_fingerprint_before="changed-input"),
    ) is False
    assert subject._same_fixed_probe_evidence_v1(
        before,
        replace(after, buffer_digest_before="changed-buffer"),
    ) is False


def test_formal_fit_postconditions_accept_epoch5_step5_finite_parameters() -> None:
    session = SimpleNamespace(
        trainer=SimpleNamespace(current_epoch=5, global_step=5),
        model=nn.Linear(2, 1),
    )
    subject._validate_formal_fit_postconditions_v1(session)


@pytest.mark.parametrize(
    "current_epoch,global_step,nonfinite",
    (
        (4, 5, False),
        (6, 5, False),
        (5, 4, False),
        (5, 6, False),
        (5, 5, True),
    ),
)
def test_formal_fit_postconditions_reject_wrong_counters_and_nonfinite_parameters(
    current_epoch: int,
    global_step: int,
    nonfinite: bool,
) -> None:
    model = nn.Linear(2, 1)
    if nonfinite:
        with torch.no_grad():
            next(model.parameters()).view(-1)[0] = float("nan")
    session = SimpleNamespace(
        trainer=SimpleNamespace(
            current_epoch=current_epoch,
            global_step=global_step,
        ),
        model=model,
    )
    with pytest.raises(subject._ProbeInvariantError):
        subject._validate_formal_fit_postconditions_v1(session)


@pytest.mark.parametrize("outcome", ("LEARNING_SIGNAL_WEAK", "NO_LEARNING_SIGNAL"))
def test_fake_experiment_calls_fit_once_without_retry_and_ckpt_none(
    monkeypatch: pytest.MonkeyPatch, outcome: str,
) -> None:
    actions: list[object] = []
    pre1 = _make_probe()
    pre2 = _make_probe()
    post = _make_probe(parameter_digest="post")
    probes = iter((pre1, pre2, post))

    class FakeTrainer:
        def fit(self, **kwargs):
            actions.append(("fit", kwargs))

    model = object()
    session = SimpleNamespace(model=model, trainer=FakeTrainer())
    monkeypatch.setattr(
        subject,
        "_build_formal_probe_session_and_batch_v1",
        lambda **unused: (actions.append("build") or (session, {})),
    )

    def fake_probe(**unused):
        actions.append("probe")
        return next(probes)

    monkeypatch.setattr(
        subject, "run_covapie_current11_deterministic_exact5_probe_v1", fake_probe
    )
    monkeypatch.setattr(
        subject,
        "validate_covapie_current11_preprobe_repeatability_v1",
        lambda **unused: (actions.append("repeatability") or _repeatability(repeatable=True)),
    )
    monkeypatch.setattr(
        subject,
        "_validate_formal_fit_postconditions_v1",
        lambda unused: actions.append("postconditions"),
    )
    monkeypatch.setattr(
        subject,
        "compare_covapie_current11_learning_signal_v1",
        lambda **unused: (actions.append("compare") or _decision(outcome)),
    )
    result = subject.run_covapie_current11_bounded_learning_signal_experiment_v1(
        repository_root=ROOT,
        state_root=STATE,
        legacy_init_checkpoint=CHECKPOINT,
    )
    assert actions == [
        "build",
        "probe",
        "probe",
        "repeatability",
        ("fit", {"model": model, "ckpt_path": None}),
        "postconditions",
        "probe",
        "compare",
    ]
    assert result.outcome == outcome
    assert result.fit_call_count == 1
    assert result.fit_ckpt_path_was_none is True
    assert result.training_completed is True


def test_fake_pre_nondeterminism_stops_before_fit_and_compare(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actions: list[str] = []
    probes = iter((_make_probe(), _make_probe()))

    class ForbiddenTrainer:
        def fit(self, **unused):
            actions.append("fit")
            raise AssertionError("fit must not run")

    session = SimpleNamespace(model=object(), trainer=ForbiddenTrainer())
    monkeypatch.setattr(
        subject,
        "_build_formal_probe_session_and_batch_v1",
        lambda **unused: (session, {}),
    )
    monkeypatch.setattr(
        subject,
        "run_covapie_current11_deterministic_exact5_probe_v1",
        lambda **unused: (actions.append("probe") or next(probes)),
    )
    monkeypatch.setattr(
        subject,
        "validate_covapie_current11_preprobe_repeatability_v1",
        lambda **unused: (
            actions.append("repeatability") or _repeatability(repeatable=False)
        ),
    )
    monkeypatch.setattr(
        subject,
        "compare_covapie_current11_learning_signal_v1",
        lambda **unused: (_ for _ in ()).throw(AssertionError("compare must not run")),
    )
    result = subject.run_covapie_current11_bounded_learning_signal_experiment_v1(
        repository_root=ROOT,
        state_root=STATE,
        legacy_init_checkpoint=CHECKPOINT,
    )
    assert actions == ["probe", "probe", "repeatability"]
    assert result.outcome == "PROBE_NONDETERMINISTIC"
    assert result.fit_call_count == 0
    assert result.training_completed is False


@pytest.mark.parametrize(
    "failure_phase,expected_stage,training_completed,post_retained",
    (
        ("fit", "trainer_fit", False, False),
        ("postconditions", "formal_fit_postconditions", False, False),
        ("postprobe", "postprobe", True, False),
        ("comparison", "comparison", True, True),
    ),
)
def test_fake_postpre_failures_have_exact_stage_and_never_retry_fit(
    monkeypatch: pytest.MonkeyPatch,
    failure_phase: str,
    expected_stage: str,
    training_completed: bool,
    post_retained: bool,
) -> None:
    fit_calls = 0
    probe_calls = 0
    post = _make_probe(parameter_digest="post")

    class FailingTrainer:
        def fit(self, **kwargs):
            nonlocal fit_calls
            fit_calls += 1
            assert kwargs["ckpt_path"] is None
            if failure_phase == "fit":
                raise RuntimeError("injected fit failure")

    session = SimpleNamespace(model=object(), trainer=FailingTrainer())

    def fake_probe(**unused):
        nonlocal probe_calls
        del unused
        probe_calls += 1
        if probe_calls == 3:
            if failure_phase == "postprobe":
                raise RuntimeError("injected postprobe failure")
            return post
        return _make_probe()

    monkeypatch.setattr(
        subject,
        "_build_formal_probe_session_and_batch_v1",
        lambda **unused: (session, {}),
    )
    monkeypatch.setattr(
        subject,
        "run_covapie_current11_deterministic_exact5_probe_v1",
        fake_probe,
    )
    monkeypatch.setattr(
        subject,
        "validate_covapie_current11_preprobe_repeatability_v1",
        lambda **unused: _repeatability(repeatable=True),
    )

    def fake_postconditions(unused):
        del unused
        if failure_phase == "postconditions":
            raise RuntimeError("injected formal postcondition failure")

    monkeypatch.setattr(
        subject,
        "_validate_formal_fit_postconditions_v1",
        fake_postconditions,
    )

    def fake_comparison(**unused):
        del unused
        if failure_phase == "comparison":
            raise RuntimeError("injected comparison failure")
        raise AssertionError("comparison must not run")

    monkeypatch.setattr(
        subject,
        "compare_covapie_current11_learning_signal_v1",
        fake_comparison,
    )
    result = subject.run_covapie_current11_bounded_learning_signal_experiment_v1(
        repository_root=ROOT,
        state_root=STATE,
        legacy_init_checkpoint=CHECKPOINT,
    )
    assert fit_calls == 1
    assert result.outcome == "TRAINING_FAILED"
    assert result.failure_stage == expected_stage
    assert result.fit_call_count == 1
    assert result.fit_ckpt_path_was_none is True
    assert result.training_completed is training_completed
    assert (result.post is post) is post_retained
    assert result.decision is None


def test_import_and_source_have_no_probe_side_effect_or_random_monkeypatch(
    tmp_path: Path,
) -> None:
    source_path = Path(subject.__file__)
    source = source_path.read_text(encoding="utf-8")
    assert "torch.randint(" not in source
    assert "torch.randn(" not in source
    assert ".sample_gaussian(" not in source
    assert ".backward(" not in source
    assert ".zero_grad(" not in source
    assert ".configure_optimizers(" not in source
    assert 'failure_stage="training_or_postprobe"' not in source
    assert all(
        f'failure_stage="{stage}"' in source
        for stage in (
            "trainer_fit",
            "formal_fit_postconditions",
            "postprobe",
            "comparison",
        )
    )
    before = tuple(tmp_path.iterdir())
    completed = subprocess.run(
        (
            sys.executable,
            "-c",
            "import covalent_ext.covapie_current11_bounded_learning_signal_probe_v1",
        ),
        cwd=tmp_path,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": f"{ROOT}:{ROOT / 'src'}",
        },
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert tuple(tmp_path.iterdir()) == before
