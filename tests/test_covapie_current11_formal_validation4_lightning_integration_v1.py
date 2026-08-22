from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
import inspect
import math
from pathlib import Path

import pytest
import torch
from torch.utils.data import SequentialSampler

from covalent_ext import (
    covapie_current11_checkpoint_migration_and_real_one_batch_train_path_smoke_v1
    as instantiation_owner,
)
from covalent_ext import (
    covapie_current11_formal_validation4_lightning_integration_v1 as subject,
)
from covalent_ext import (
    covapie_current11_formal_validation4_masked_vlb_nll_v1 as evaluator,
)
from covalent_ext.covapie_current11_training_lightning_module_v1 import (
    CovapieCurrent11TrainingLigandPocketDDPM,
)
from scripts import (
    check_covapie_current11_formal_validation4_lightning_integration_v1
    as checker,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
STATE_ROOT = REPOSITORY_ROOT.parent / "covapie-state"
CACHE_ROOT = STATE_ROOT / "bulk-multisource-cys-sg-v1/rcsb"
SOURCE_PATH = REPOSITORY_ROOT / (
    "src/covalent_ext/"
    "covapie_current11_formal_validation4_lightning_integration_v1.py"
)


@pytest.fixture(scope="module")
def unloaded_model():
    return subject.instantiate_covapie_current11_formal_validation4_lightning_model_v1(
        repository_root=REPOSITORY_ROOT,
        state_root=STATE_ROOT,
        cache_root=CACHE_ROOT,
    )


@pytest.fixture(scope="module")
def real_smoke():
    return checker.check_covapie_current11_formal_validation4_lightning_integration_v1(
        repository_root=REPOSITORY_ROOT,
        state_root=STATE_ROOT,
        cache_root=CACHE_ROOT,
    )


def _called_names(function: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        target = node.func
        if isinstance(target, ast.Name):
            names.add(target.id)
        elif isinstance(target, ast.Attribute):
            parts = [target.attr]
            value = target.value
            while isinstance(value, ast.Attribute):
                parts.append(value.attr)
                value = value.value
            if isinstance(value, ast.Name):
                parts.append(value.id)
            names.add(".".join(reversed(parts)))
    return names


def _function_node(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(name)


def test_exact_repository_state_supports_candidate_or_published_profile():
    snapshot = checker.collect_repository_git_snapshot_v1(
        repository_root=REPOSITORY_ROOT
    )
    profile = checker.classify_repository_snapshot_v1(snapshot)
    assert snapshot.branch == "main"
    assert snapshot.ahead_behind == (0, 0)
    assert snapshot.tracked_modified_paths == ()
    assert snapshot.staged_modified_paths == ()
    if profile == checker.CANDIDATE_PRECOMMIT_PROFILE_V1:
        assert snapshot.head == checker.EXPECTED_BASELINE_HEAD_V1
        assert snapshot.origin_main == checker.EXPECTED_BASELINE_HEAD_V1
        assert snapshot.head_parent_ids == (checker.EXPECTED_BASELINE_PARENT_V1,)
        assert snapshot.head_subject == checker.EXPECTED_BASELINE_SUBJECT_V1
        assert snapshot.head_tree == checker.EXPECTED_BASELINE_TREE_V1
        assert set(snapshot.status_entries) == {
            ("??", path) for path in checker.AUTHORIZED_CANDIDATE_FILES_V1
        }
    else:
        assert profile == checker.PUBLISHED_SUCCESSOR_PROFILE_V1
        assert snapshot.head == snapshot.origin_main
        assert snapshot.head != checker.EXPECTED_BASELINE_HEAD_V1
        assert snapshot.head_parent_ids == (checker.EXPECTED_BASELINE_HEAD_V1,)
        assert snapshot.head_subject == checker.PUBLISHED_SUCCESSOR_SUBJECT_V1
        assert snapshot.status_entries == ()


def test_published_evaluator_and_current_owner_sha_bindings_are_exact():
    assert evaluator._sha256_file(
        REPOSITORY_ROOT
        / "src/covalent_ext/covapie_current11_formal_validation4_masked_vlb_nll_v1.py"
    ) == "3f53e1bb668dfe5751f154793ba0d4e1f1001e9619f7a8613b7df31b522be755"
    assert subject._verify_current_owner_bindings_v1(REPOSITORY_ROOT) == (
        subject.BOUND_CURRENT_OWNER_SHA256_V1
    )


def test_owner_binding_drift_fails_closed(monkeypatch):
    original = subject._sha256_file

    def wrong_first(path):
        if path.name == "covapie_current11_formal_validation4_masked_vlb_nll_v1.py":
            return "0" * 64
        return original(path)

    monkeypatch.setattr(subject, "_sha256_file", wrong_first)
    with pytest.raises(Exception):
        subject._verify_current_owner_bindings_v1(REPOSITORY_ROOT)


def test_subclass_inheritance_and_training_owner_method_identity(unloaded_model):
    model_type = type(unloaded_model)
    base = CovapieCurrent11TrainingLigandPocketDDPM
    assert issubclass(model_type, base)
    assert model_type.forward is base.forward
    assert model_type.training_step is base.training_step
    assert model_type.configure_optimizers is base.configure_optimizers
    assert model_type.test_step is base.test_step
    assert model_type.validation_step is not base.validation_step
    assert model_type.validation_epoch_end is None
    assert len(unloaded_model.state_dict()) == 141


def test_production_validation_ast_excludes_standalone_migration_training_and_writes():
    tree = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
    validation_step = _function_node(tree, "validation_step")
    evaluation = _function_node(tree, "_evaluate_current_model_on_cpu_shadow_v1")
    calls = _called_names(validation_step) | _called_names(evaluation)
    forbidden_suffixes = {
        "run_covapie_current11_formal_validation4_masked_vlb_nll_v1",
        "migrate_covapie_current11_legacy_checkpoint_state_dict_v1",
        "backward",
        "optimizer.step",
        "Trainer.fit",
        "torch.save",
        "configure_optimizers",
        "forward",
    }
    assert not any(
        name == forbidden or name.endswith("." + forbidden)
        for name in calls
        for forbidden in forbidden_suffixes
    )
    source_text = SOURCE_PATH.read_text(encoding="utf-8")
    assert "run_covapie_current11_formal_validation4_masked_vlb_nll_v1" not in source_text


def test_published_semantic_helpers_are_reused_without_equation_copy():
    tree = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
    evaluation = _function_node(tree, "_evaluate_current_model_on_cpu_shadow_v1")
    calls = _called_names(evaluation)
    for name in (
        "published_evaluator._audit_formal_authority",
        "published_evaluator._task_batches",
        "published_evaluator._evaluate_slice",
        "published_evaluator._aggregate",
    ):
        if name.endswith("_audit_formal_authority") or name.endswith("_task_batches"):
            continue
        assert name in calls
    helper = _function_node(tree, "_prepare_published_formal_population_v1")
    helper_calls = _called_names(helper)
    assert "published_evaluator._audit_formal_authority" in helper_calls
    assert "published_evaluator._task_batches" in helper_calls
    assert "SNR_weight =" not in SOURCE_PATH.read_text(encoding="utf-8")


def test_sentinel_is_frozen_and_malformed_values_fail_closed(unloaded_model):
    sentinel = subject.FORMAL_VALIDATION4_REQUEST_SENTINEL_V1
    with pytest.raises(FrozenInstanceError):
        sentinel.version = "changed"
    malformed = replace(sentinel, primary_metric_identity="WRONG")
    with pytest.raises(ValueError) as captured:
        unloaded_model.on_before_batch_transfer(malformed, 0)
    assert str(captured.value) == subject.FORMAL_VALIDATION4_LIGHTNING_INTEGRATION_ERROR_V1


def test_setup_validate_and_exact_one_item_sequential_loader():
    model = subject.instantiate_covapie_current11_formal_validation4_lightning_model_v1(
        repository_root=REPOSITORY_ROOT,
        state_root=STATE_ROOT,
        cache_root=CACHE_ROOT,
    )
    model.setup("validate")
    dataset = model._covapie_formal_validation4_request_dataset_v1
    collator = model._covapie_formal_validation4_request_collator_v1
    model.setup("validate")
    assert model._covapie_formal_validation4_request_dataset_v1 is dataset
    assert model._covapie_formal_validation4_request_collator_v1 is collator
    assert model.train_dataset is None
    assert model.val_dataset is None
    assert model.test_dataset is None
    loaders = (model.val_dataloader(), model.val_dataloader())
    for loader in loaders:
        assert len(loader.dataset) == 1
        assert len(loader) == 1
        assert loader.batch_size == 1
        assert type(loader.sampler) is SequentialSampler
        assert loader.num_workers == 0
        assert loader.drop_last is False
        assert loader.pin_memory is False
        assert loader.persistent_workers is False
        assert next(iter(loader)) == subject.FORMAL_VALIDATION4_REQUEST_SENTINEL_V1
    assert model._covapie_formal_validation4_lifecycle_counts_v1["setup_validate"] == 2
    assert model._covapie_formal_validation4_lifecycle_counts_v1["validation_dataloader"] == 2
    assert dataset.getitem_call_count == 2
    assert collator.call_count == 2


def test_setup_validate_partial_lifecycle_state_fails_closed():
    model = subject.instantiate_covapie_current11_formal_validation4_lightning_model_v1(
        repository_root=REPOSITORY_ROOT,
        state_root=STATE_ROOT,
        cache_root=CACHE_ROOT,
    )
    model._covapie_formal_validation4_request_dataset_v1 = (
        subject._FormalValidation4RequestDatasetV1()
    )
    with pytest.raises(ValueError) as captured:
        model.setup("validate")
    assert str(captured.value) == subject.FORMAL_VALIDATION4_LIGHTNING_INTEGRATION_ERROR_V1


def test_request_dataset_rejects_nonzero_index_but_reuses_zero():
    dataset = subject._FormalValidation4RequestDatasetV1()
    assert dataset[0] is subject.FORMAL_VALIDATION4_REQUEST_SENTINEL_V1
    assert dataset[0] is subject.FORMAL_VALIDATION4_REQUEST_SENTINEL_V1
    assert dataset.getitem_call_count == 2
    with pytest.raises(Exception):
        dataset[1]


def test_request_collator_is_repeatable_and_still_validates_exact_sentinel():
    collator = subject._FormalValidation4RequestCollatorV1()
    items = [subject.FORMAL_VALIDATION4_REQUEST_SENTINEL_V1]
    assert collator(items) is items[0]
    assert collator(items) is items[0]
    assert collator.call_count == 2
    with pytest.raises(Exception):
        collator([])


def test_exact_sentinel_bypasses_both_transfer_hooks(unloaded_model):
    sentinel = subject.FORMAL_VALIDATION4_REQUEST_SENTINEL_V1
    assert unloaded_model.on_before_batch_transfer(sentinel, 0) is sentinel
    assert unloaded_model.transfer_batch_to_device(
        sentinel, torch.device("cpu"), 0
    ) is sentinel


def test_non_sentinel_transfer_paths_delegate_to_inherited_owner(
    unloaded_model, monkeypatch,
):
    batch = {"ordinary": object()}
    before_token = object()
    device_token = object()
    calls = []

    def inherited_before(self, value, index):
        calls.append(("before", value, index))
        return before_token

    def inherited_device(self, value, device, index):
        calls.append(("device", value, device, index))
        return device_token

    monkeypatch.setattr(
        CovapieCurrent11TrainingLigandPocketDDPM,
        "on_before_batch_transfer",
        inherited_before,
    )
    monkeypatch.setattr(
        CovapieCurrent11TrainingLigandPocketDDPM,
        "transfer_batch_to_device",
        inherited_device,
    )
    assert unloaded_model.on_before_batch_transfer(batch, 0) is before_token
    assert unloaded_model.transfer_batch_to_device(
        batch, torch.device("cpu"), 0
    ) is device_token
    assert [entry[0] for entry in calls] == ["before", "device"]


def _reset_validation_run_state(model) -> None:
    model.eval()
    model._covapie_formal_validation4_validation_run_active_v1 = False
    model._covapie_formal_validation4_validation_run_count_v1 = 0
    model._covapie_formal_validation4_current_run_step_count_v1 = 0
    model._covapie_formal_validation4_completed_run_step_counts_v1 = []
    model._covapie_formal_validation4_lifecycle_counts_v1["validation_step"] = 0


def test_validation_step_before_validation_run_start_fails_closed(unloaded_model):
    _reset_validation_run_state(unloaded_model)
    with torch.no_grad():
        with pytest.raises(ValueError) as captured:
            unloaded_model.validation_step(
                subject.FORMAL_VALIDATION4_REQUEST_SENTINEL_V1, 0, 0
            )
    assert str(captured.value) == subject.FORMAL_VALIDATION4_LIGHTNING_INTEGRATION_ERROR_V1


def test_validation_epoch_start_while_active_fails_closed(unloaded_model):
    _reset_validation_run_state(unloaded_model)
    unloaded_model.on_validation_epoch_start()
    with pytest.raises(ValueError) as captured:
        unloaded_model.on_validation_epoch_start()
    assert str(captured.value) == subject.FORMAL_VALIDATION4_LIGHTNING_INTEGRATION_ERROR_V1
    _reset_validation_run_state(unloaded_model)


def test_validation_epoch_end_with_zero_steps_fails_closed(unloaded_model):
    _reset_validation_run_state(unloaded_model)
    unloaded_model.on_validation_epoch_start()
    with pytest.raises(ValueError) as captured:
        unloaded_model.on_validation_epoch_end()
    assert str(captured.value) == subject.FORMAL_VALIDATION4_LIGHTNING_INTEGRATION_ERROR_V1
    _reset_validation_run_state(unloaded_model)


@pytest.mark.parametrize(
    ("batch_idx", "dataloader_idx", "training", "grad_enabled", "prior_calls"),
    (
        (1, 0, False, False, 0),
        (0, 1, False, False, 0),
        (0, 0, True, False, 0),
        (0, 0, False, True, 0),
        (0, 0, False, False, 1),
    ),
)
def test_validation_step_context_rejections_are_fail_closed(
    unloaded_model, batch_idx, dataloader_idx, training, grad_enabled, prior_calls,
):
    _reset_validation_run_state(unloaded_model)
    unloaded_model.on_validation_epoch_start()
    unloaded_model._covapie_formal_validation4_current_run_step_count_v1 = prior_calls
    unloaded_model.train(training)
    context = torch.enable_grad() if grad_enabled else torch.no_grad()
    with context:
        with pytest.raises(ValueError) as captured:
            unloaded_model.validation_step(
                subject.FORMAL_VALIDATION4_REQUEST_SENTINEL_V1,
                batch_idx,
                dataloader_idx,
            )
    assert str(captured.value) == subject.FORMAL_VALIDATION4_LIGHTNING_INTEGRATION_ERROR_V1
    _reset_validation_run_state(unloaded_model)


def test_second_step_same_run_fails_but_new_completed_run_is_allowed(
    unloaded_model, real_smoke, monkeypatch,
):
    _reset_validation_run_state(unloaded_model)
    monkeypatch.setattr(
        subject,
        "_evaluate_current_model_on_cpu_shadow_v1",
        lambda **unused: real_smoke.current_model_result,
    )
    monkeypatch.setattr(unloaded_model, "log", lambda *unused, **kwargs: None)
    with torch.no_grad():
        unloaded_model.on_validation_epoch_start()
        unloaded_model.validation_step(
            subject.FORMAL_VALIDATION4_REQUEST_SENTINEL_V1, 0, 0
        )
        with pytest.raises(ValueError):
            unloaded_model.validation_step(
                subject.FORMAL_VALIDATION4_REQUEST_SENTINEL_V1, 0, 0
            )
        unloaded_model.on_validation_epoch_end()
        unloaded_model.on_validation_epoch_start()
        unloaded_model.validation_step(
            subject.FORMAL_VALIDATION4_REQUEST_SENTINEL_V1, 0, 0
        )
        unloaded_model.on_validation_epoch_end()
    assert unloaded_model._covapie_formal_validation4_validation_run_count_v1 == 2
    assert tuple(
        unloaded_model._covapie_formal_validation4_completed_run_step_counts_v1
    ) == (1, 1)
    assert unloaded_model._covapie_formal_validation4_lifecycle_counts_v1[
        "validation_step"
    ] == 2
    assert unloaded_model._covapie_formal_validation4_validation_run_active_v1 is False
    _reset_validation_run_state(unloaded_model)


def test_current_state_cpu_shadow_strict_copy_and_source_unchanged(unloaded_model):
    before = {
        key: value.detach().clone() for key, value in unloaded_model.state_dict().items()
    }
    copied = subject.build_covapie_current11_cpu_shadow_from_current_state_v1(
        source_model=unloaded_model,
        repository_root=REPOSITORY_ROOT,
        state_root=STATE_ROOT,
    )
    assert copied.current_state_key_count == 141
    assert copied.shadow_state_key_count == 141
    assert copied.missing_keys == ()
    assert copied.unexpected_keys == ()
    assert copied.shape_mismatch_count == 0
    assert copied.post_load_tensor_equality
    assert copied.current_state_copied_to_cpu
    assert all(
        torch.equal(before[key], unloaded_model.state_dict()[key]) for key in before
    )
    assert all(parameter.device.type == "cpu" for parameter in copied.shadow_model.parameters())


def test_independent_test_only_current_weight_sensitivity_proof():
    proof = checker._state_sensitivity_proof_v1(
        repository_root=REPOSITORY_ROOT,
        state_root=STATE_ROOT,
        cache_root=CACHE_ROOT,
    )
    assert proof.verified
    assert proof.source_value_before_copy == proof.shadow_value_after_copy
    assert proof.source_value_after_copy == proof.source_value_before_copy
    assert proof.current_state_key_count == proof.shadow_state_key_count == 141


def test_shadow_shape_mismatch_fails_closed(unloaded_model, monkeypatch):
    original_state = unloaded_model.state_dict()
    wrong = {key: value.detach().clone() for key, value in original_state.items()}
    selected = next(key for key, value in wrong.items() if value.ndim > 0 and value.shape[0] > 1)
    wrong[selected] = wrong[selected][:-1]
    monkeypatch.setattr(unloaded_model, "state_dict", lambda: wrong)
    with pytest.raises(ValueError) as captured:
        subject.build_covapie_current11_cpu_shadow_from_current_state_v1(
            source_model=unloaded_model,
            repository_root=REPOSITORY_ROOT,
            state_root=STATE_ROOT,
        )
    assert str(captured.value) == subject.FORMAL_VALIDATION4_LIGHTNING_INTEGRATION_ERROR_V1


def test_shadow_missing_and_unexpected_key_domain_fails_closed(
    unloaded_model, monkeypatch,
):
    original_state = unloaded_model.state_dict()
    wrong = {key: value.detach().clone() for key, value in original_state.items()}
    removed_key, removed_value = wrong.popitem()
    wrong["unexpected.current_state.tensor"] = removed_value
    assert len(wrong) == 141 and removed_key not in wrong
    monkeypatch.setattr(unloaded_model, "state_dict", lambda: wrong)
    with pytest.raises(ValueError):
        subject.build_covapie_current11_cpu_shadow_from_current_state_v1(
            source_model=unloaded_model,
            repository_root=REPOSITORY_ROOT,
            state_root=STATE_ROOT,
        )


def test_process_control_exceptions_are_not_normalized(unloaded_model, monkeypatch):
    monkeypatch.setattr(
        instantiation_owner,
        "_instantiate_current11_model_v1",
        lambda **unused: (_ for _ in ()).throw(KeyboardInterrupt()),
    )
    with pytest.raises(KeyboardInterrupt):
        subject.build_covapie_current11_cpu_shadow_from_current_state_v1(
            source_model=unloaded_model,
            repository_root=REPOSITORY_ROOT,
            state_root=STATE_ROOT,
        )


def test_real_trainer_validate_lifecycle_counts_and_no_training(real_smoke):
    assert real_smoke.Trainer_validate_invoked
    assert real_smoke.Trainer_validate_call_count == 2
    assert real_smoke.validation_run_count == 2
    assert real_smoke.completed_validation_run_step_counts == (1, 1)
    assert real_smoke.setup_validate_call_count > 0
    assert real_smoke.validation_dataloader_call_count > 0
    assert real_smoke.validation_dataset_getitem_count == 2
    assert real_smoke.validation_collator_count == 2
    assert real_smoke.validation_step_call_count == 2
    assert real_smoke.training_step_call_count == 0
    assert real_smoke.test_step_call_count == 0
    assert real_smoke.Trainer_global_step == 0
    assert not real_smoke.optimizer_created_during_validation
    assert not real_smoke.backward_performed
    assert real_smoke.initial_model_checkpoint_migration_count == 1
    assert real_smoke.validation_checkpoint_weight_migration_count == 0
    assert real_smoke.repeatable_validation_run_lifecycle_ready
    assert real_smoke.repeatable_setup_validate_verified
    assert real_smoke.repeatable_val_dataloader_verified
    assert real_smoke.repeatable_dataset_getitem_verified
    assert real_smoke.repeatable_collator_verified


def test_same_model_two_real_validate_runs_have_exact_metric_parity(real_smoke):
    assert len(real_smoke.repeated_current_model_results) == 2
    assert len(real_smoke.repeated_trainer_returned_metrics) == 2
    assert real_smoke.repeated_validation_metric_parity
    first, second = real_smoke.repeated_current_model_results
    assert checker._metric_tuple_from_current(first) == pytest.approx(
        checker._metric_tuple_from_current(second), abs=1.0e-12, rel=0.0
    )
    assert (
        real_smoke.repeated_trainer_returned_metrics[0]
        == real_smoke.repeated_trainer_returned_metrics[1]
    )


def test_active_model_immutability_across_both_real_validate_runs(real_smoke):
    assert real_smoke.active_model_parameters_unchanged_across_both_runs
    assert real_smoke.active_model_buffers_unchanged_across_both_runs
    assert real_smoke.active_model_gradient_states_unchanged_across_both_runs
    assert real_smoke.active_model_registered_modules_unchanged_across_both_runs
    assert real_smoke.active_model_registered_parameters_unchanged_across_both_runs
    assert real_smoke.active_model_registered_buffers_unchanged_across_both_runs
    assert real_smoke.active_model_size_distribution_unchanged_across_both_runs
    assert real_smoke.active_model_optimizer_independent_state_unchanged_across_both_runs


def test_real_current_model_scientific_counts_and_finiteness(real_smoke):
    result = real_smoke.current_model_result
    assert result.primary_metric_name == "MASKED_CONDITIONAL_VLB_NLL_V1"
    assert result.formal_validation_event_count == 4
    assert result.formal_validation_task_event_count == 16
    assert len(result.root_validation_seeds) == 4
    assert result.formal_validation_estimate_count == 64
    assert result.formal_validation_task_slice_evaluation_count == 20
    assert result.main_dynamics_task_slice_call_count == 20
    assert result.t0_dynamics_task_slice_call_count == 20
    assert result.total_dynamics_task_slice_call_count == 40
    assert result.PRE_geometry_valid_count == 0
    assert result.POST_geometry_valid_count == 64
    assert not result.primary_node_prior_included
    assert result.all_applicable_primary_metrics_finite
    assert result.all_applicable_auxiliary_metrics_finite


def test_real_current_weight_authority_historical_prior_and_active_immutability(real_smoke):
    result = real_smoke.current_model_result
    assert result.validation_model_weight_source == "CURRENT_LIGHTNING_MODEL_STATE"
    assert result.current_state_copied_to_cpu_shadow
    assert result.shadow_strict_state_copy_parity
    assert result.shadow_missing_keys == ()
    assert result.shadow_unexpected_keys == ()
    assert result.checkpoint_metadata_read_count == 1
    assert result.checkpoint_weight_migration_call_count_inside_validation == 0
    assert result.historical_node_prior_source == "exact_legacy_checkpoint_hyperparameters"
    assert result.historical_node_histogram_shape == (107, 1671)
    assert not result.synthetic_node_histogram_used
    assert result.active_model_parameters_unchanged
    assert result.active_model_buffers_unchanged
    assert result.active_model_gradient_states_unchanged
    assert result.active_model_optimizer_independent_state_unchanged
    assert result.active_model_size_distribution_unchanged
    assert result.active_model_registered_modules_unchanged
    assert result.shadow_not_registered_on_active_model
    assert result.shadow_eval_mode_verified
    assert result.shadow_gradient_recording_disabled
    assert not result.metric_tensors_require_grad


def test_real_standalone_and_logged_metric_parity(real_smoke):
    assert real_smoke.standalone_initial_state_metric_parity
    assert real_smoke.lightning_primary_metric_logged
    assert real_smoke.lightning_logged_metric_parity
    returned = dict(real_smoke.trainer_returned_metrics)
    callback = dict(real_smoke.callback_metrics)
    assert tuple(returned) == subject.LIGHTNING_METRIC_KEYS_V1
    assert tuple(callback) == subject.LIGHTNING_METRIC_KEYS_V1
    current = checker._metric_tuple_from_current(real_smoke.current_model_result)
    standalone = checker._metric_tuple_from_standalone(real_smoke.standalone_reference)
    assert current == pytest.approx(standalone, abs=1.0e-12, rel=0.0)
    assert returned[subject.PRIMARY_LIGHTNING_MONITOR_KEY_V1] == pytest.approx(
        real_smoke.current_model_result.event_macro_masked_conditional_vlb_nll,
        abs=1.0e-12,
        rel=0.0,
    )


def test_real_metric_values_are_diagnostics_not_hardcoded_policy(real_smoke):
    result = real_smoke.current_model_result
    assert result.event_macro_masked_conditional_vlb_nll == pytest.approx(40.3449507477)
    assert result.micro_masked_conditional_vlb_nll == pytest.approx(34.7305753147)
    assert result.profile_balanced_masked_conditional_vlb_nll == pytest.approx(40.3449507477)
    assert result.mean_pair_BCE == pytest.approx(0.695623686537)
    assert result.mean_POST_geometry_loss == pytest.approx(0.669431589544)
    assert result.mean_pair_contrastive_loss == pytest.approx(4.44527275115)
    source_text = SOURCE_PATH.read_text(encoding="utf-8")
    assert "40.344950" not in source_text
    assert "34.730575" not in source_text


def test_current_result_schema_is_immutable(real_smoke):
    with pytest.raises(FrozenInstanceError):
        real_smoke.current_model_result.implementation_status = "changed"
    with pytest.raises(FrozenInstanceError):
        real_smoke.current_model_result.per_estimate_rows[0].canonical_task_id = 99


def _candidate_snapshot() -> checker.RepositoryGitSnapshotV1:
    return checker.collect_repository_git_snapshot_v1(repository_root=REPOSITORY_ROOT)


def _valid_successor_snapshot() -> checker.RepositoryGitSnapshotV1:
    candidate = _candidate_snapshot()
    successor_head = "1" * 40
    return replace(
        candidate,
        head=successor_head,
        origin_main=successor_head,
        status_entries=(),
        head_parent_ids=(checker.EXPECTED_BASELINE_HEAD_V1,),
        head_subject=checker.PUBLISHED_SUCCESSOR_SUBJECT_V1,
        head_tree="2" * 40,
        head_changed_entries=tuple(
            ("A", path) for path in checker.AUTHORIZED_CANDIDATE_FILES_V1
        ),
        head_candidate_path_modes=tuple(
            (path, "100644") for path in checker.AUTHORIZED_CANDIDATE_FILES_V1
        ),
    )


def test_valid_published_successor_profile_simulation():
    assert checker.classify_repository_snapshot_v1(_valid_successor_snapshot()) == (
        checker.PUBLISHED_SUCCESSOR_PROFILE_V1
    )


@pytest.mark.parametrize(
    "mutation",
    (
        lambda value: replace(value, head_parent_ids=("3" * 40,)),
        lambda value: replace(value, head_subject="wrong subject"),
        lambda value: replace(
            value,
            head_changed_entries=value.head_changed_entries + (("A", "extra.py"),),
        ),
        lambda value: replace(
            value,
            head_candidate_path_modes=(
                (checker.AUTHORIZED_CANDIDATE_FILES_V1[0], "100755"),
            ) + value.head_candidate_path_modes[1:],
        ),
        lambda value: replace(value, status_entries=(("??", "extra.txt"),)),
        lambda value: replace(
            value,
            head_changed_entries=(
                ("M", checker.AUTHORIZED_CANDIDATE_FILES_V1[0]),
            ) + value.head_changed_entries[1:],
        ),
    ),
)
def test_invalid_published_successor_profiles_fail_closed(mutation):
    with pytest.raises(ValueError) as captured:
        checker.classify_repository_snapshot_v1(mutation(_valid_successor_snapshot()))
    assert str(captured.value) == checker.CHECKER_ERROR_V1


def test_candidate_extra_untracked_and_tracked_modification_fail_closed():
    candidate = _candidate_snapshot()
    with pytest.raises(ValueError):
        checker.classify_repository_snapshot_v1(
            replace(candidate, status_entries=candidate.status_entries + (("??", "extra"),))
        )
    with pytest.raises(ValueError):
        checker.classify_repository_snapshot_v1(
            replace(candidate, tracked_modified_paths=("existing.py",))
        )


def test_checker_outputs_all_required_final_markers():
    source_text = inspect.getsource(checker.main)
    required = (
        "formal_validation4_lightning_integration_science_unchanged",
        "one_shot_validation_lifecycle_blocker_fixed",
        "validation_lifecycle_is_per_run_not_lifetime",
        "repeatable_validation_run_lifecycle_ready",
        "same_model_two_consecutive_Trainer_validate_runs_passed",
        "completed_validation_run_step_counts",
        "total_validation_step_call_count_after_repeat_probe",
        "repeated_validation_metric_parity",
        "repeatable_setup_validate_verified",
        "repeatable_val_dataloader_verified",
        "repeatable_dataset_getitem_verified",
        "repeatable_collator_verified",
        "formal_validation4_lightning_integration_built",
        "published_evaluator_reused_without_math_duplication",
        "standalone_public_wrapper_called_inside_validation",
        "validation_model_weight_source",
        "current_state_shadow_copy_sensitivity_verified",
        "checkpoint_weight_migration_call_count_inside_validation",
        "Trainer_validate_invoked",
        "lightning_logged_metric_parity",
        "real_repository_test_dual_profile",
        "postpublication_targeted_test_survivability",
        "ready_for_publication",
        "recommended_next_step_exactly",
    )
    assert all(marker in source_text for marker in required)
    assert checker.PUBLISHED_SUCCESSOR_SUBJECT_V1 == (
        "add CovaPIE formal validation4 Lightning integration v1"
    )


def test_no_gpu_runtime_or_training_readiness_overclaim(real_smoke):
    result = real_smoke.current_model_result
    assert result.cpu_shadow_validation_architecture_supports_non_cpu_source_state
    assert not result.real_gpu_validation_runtime_verified
    assert not result.training_performed
    assert not result.backward_performed
    assert not result.optimizer_created_during_validation
    assert real_smoke.same_model_two_consecutive_Trainer_validate_runs_passed
    assert all(math.isfinite(value) for value in checker._metric_tuple_from_current(result))
