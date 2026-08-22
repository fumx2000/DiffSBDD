from __future__ import annotations

import ast
from dataclasses import fields, replace
import importlib.util
from pathlib import Path
import sys

import pytest
import torch
from torch.utils.data import SequentialSampler

from covalent_ext import (
    covapie_batch001_13event_model_usable_split_materialization_and_activation_boundary_v1
    as activation_owner,
)
from covalent_ext import (
    covapie_batch001_formal_training_datamodule_and_train_validation_integration_v1
    as integration,
)
from covalent_ext import (
    covapie_batch001_train5_bounded_trainer_fit_smoke_v1 as bounded_predecessor,
)
from covalent_ext import (
    covapie_batch001_train5_single_backward_optimizer_step_smoke_v1
    as single_step_predecessor,
)
from covalent_ext import (
    covapie_current11_formal_validation4_lightning_integration_v1
    as formal_validation_owner,
)
from covalent_ext.covapie_current11_training_lightning_module_v1 import (
    CovapieCurrent11TrainingLigandPocketDDPM,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    REPOSITORY_ROOT
    / "scripts/check_covapie_batch001_formal_training_datamodule_and_train_validation_integration_v1.py"
)
SPEC = importlib.util.spec_from_file_location(
    "check_covapie_batch001_formal_train_validation_v1", CHECKER_PATH
)
assert SPEC is not None and SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)


@pytest.fixture(scope="module")
def datamodule():
    return integration.build_covapie_batch001_formal_training_datamodule_v1(
        repository_root=REPOSITORY_ROOT,
        epoch=0,
        task_schedule_seed=0,
    )


@pytest.fixture(scope="module")
def runtime_result():
    return integration.run_covapie_batch001_bounded_train_validation_integration_v1(
        repository_root=REPOSITORY_ROOT
    )


def test_bound_current_authorities_and_exact_5_4_4(datamodule):
    bindings = (
        integration.verify_covapie_batch001_formal_train_validation_source_bindings_v1(
            repository_root=REPOSITORY_ROOT
        )
    )
    assert dict(bindings)[
        "src/covalent_ext/covapie_batch001_13event_model_usable_split_"
        "materialization_and_activation_boundary_v1.py"
    ] == integration.ACTIVATION_SOURCE_SHA256_V1
    assert tuple(map(len, (
        datamodule.authority.train_event_ids,
        datamodule.authority.validation_event_ids,
        datamodule.authority.test_event_ids,
    ))) == (5, 4, 4)
    assert datamodule.authority.formal_leakage_group_cross_split_violation_count == 0
    assert (
        formal_validation_owner.FORMAL_VALIDATION4_REQUEST_SENTINEL_V1
        .formal_validation_event_ids
        == datamodule.authority.validation_event_ids
    )


def test_public_datamodule_exact_train_and_validation_loader_contract(datamodule):
    train_loader = datamodule.train_dataloader()
    validation_loader = datamodule.val_dataloader()
    for loader in (train_loader, validation_loader):
        assert len(loader) == 1
        assert loader.batch_size == 1
        assert type(loader.sampler) is SequentialSampler
        assert loader.num_workers == 0
        assert loader.drop_last is False
        assert loader.pin_memory is False
        assert loader.persistent_workers is False
    carrier = datamodule.train_carrier
    supervision = carrier.supervision
    assert carrier.sample_identities == datamodule.authority.train_event_ids
    assert carrier.scheduled_task_ids == (4, 4, 2, 0, 4)
    assert len(fields(CovapieCurrent11TrainingSupervisionTensorsV1)) == 37
    assert supervision.sample_training_admitted.tolist() == [True] * 5
    assert len(supervision.pair_candidate_batch_index) == 690
    assert supervision.pre_post_geometry_component_loss_mask.tolist() == [
        [False, True]
    ] * 5
    assert datamodule.test_dataset_getitem_count == 0
    with pytest.raises(ValueError, match="FORMAL_TEST_DATALOADER_ACCESS_FORBIDDEN"):
        datamodule.test_dataloader()


def test_datamodule_api_has_no_population_override_and_future_cycles_are_live():
    signature = integration.inspect.signature(
        integration.build_covapie_batch001_formal_training_datamodule_v1
    )
    assert tuple(signature.parameters) == (
        "epoch", "task_schedule_seed", "repository_root", "cache_root"
    )
    vectors = tuple(
        integration.build_covapie_batch001_formal_training_datamodule_v1(
            epoch=epoch,
            task_schedule_seed=0,
            repository_root=REPOSITORY_ROOT,
        ).train_carrier.scheduled_task_ids
        for epoch in range(5)
    )
    assert all(
        {vectors[epoch][sample] for epoch in range(5)} == set(range(5))
        for sample in range(5)
    )


def test_model_adapter_reuses_published_math_and_optimizer_owners():
    owner = integration.CovapieBatch001FormalTrainValidationLigandPocketDDPMV1
    assert issubclass(
        owner,
        formal_validation_owner.CovapieCurrent11FormalValidation4LigandPocketDDPMV1,
    )
    assert issubclass(owner, bounded_predecessor._Train5BoundedTrainerAdapterV1)
    assert owner.forward is bounded_predecessor._Train5BoundedTrainerAdapterV1.forward
    assert owner.training_step is CovapieCurrent11TrainingLigandPocketDDPM.training_step
    assert (
        owner.configure_optimizers
        is CovapieCurrent11TrainingLigandPocketDDPM.configure_optimizers
    )
    assert (
        integration.INTEGRATION_CANDIDATE_LOSS_WEIGHTS_V1
        is single_step_predecessor.SMOKE_ONLY_GEOMETRY_WEIGHT_CANDIDATE_V1
    )


def test_real_fit_exact_train_optimizer_then_formal_validation(runtime_result):
    result = runtime_result
    assert result.implementation_status == "passed"
    assert result.result_interpretation == integration.RESULT_INTERPRETATION_V1
    assert result.real_trainer_fit_invoked is True
    assert result.trainer_fit_call_count == 1
    assert result.train_batch_start_count == 1
    assert result.train_batch_end_count == 1
    assert result.automatic_backward_call_count == 1
    assert result.optimizer_step_count == 1
    assert result.trainer_global_step == 1
    assert result.changed_parameter_tensor_count > 0
    assert result.all_model_parameters_finite is True
    assert result.formal_validation_run_count == 1
    assert result.formal_validation_step_count == 1
    assert result.lifecycle_order.index("before_optimizer_step") < result.lifecycle_order.index(
        "validation_epoch_start"
    )
    trainer = dict(result.trainer_configuration)
    assert trainer["max_epochs"] == trainer["min_epochs"] == 1
    assert trainer["max_steps"] == -1
    assert trainer["limit_train_batches"] == 1
    assert trainer["limit_val_batches"] == 1
    assert trainer["limit_test_batches"] == 0
    assert trainer["num_sanity_val_steps"] == 0
    assert trainer["check_val_every_n_epoch"] == 1
    assert trainer["val_check_interval"] == 1.0


def test_real_runtime_current_state_and_validation_read_only(runtime_result):
    result = runtime_result
    assert result.pre_fit_state_fingerprint != result.post_optimizer_state_fingerprint
    assert (
        result.post_optimizer_state_fingerprint
        == result.validation_entry_state_fingerprint
    )
    assert result.validation_entry_state_fingerprint == result.validation_exit_state_fingerprint
    assert result.validation_entry_uses_post_optimizer_current_state is True
    assert result.active_state_unchanged_across_validation is True
    formal = result.formal_validation_result
    assert formal.validation_model_weight_source == "CURRENT_LIGHTNING_MODEL_STATE"
    assert formal.current_state_key_count == formal.shadow_state_key_count == 141
    assert formal.shadow_strict_state_copy_parity is True
    assert formal.checkpoint_weight_migration_call_count_inside_validation == 0
    assert formal.active_model_parameters_unchanged is True
    assert formal.active_model_buffers_unchanged is True
    assert formal.active_model_gradient_states_unchanged is True
    assert formal.active_model_registered_modules_unchanged is True
    assert formal.active_model_registered_parameters_unchanged is True
    assert formal.active_model_registered_buffers_unchanged is True


def test_real_formal_64_estimates_all_tasks_and_test4_untouched(runtime_result):
    result = runtime_result
    formal = result.formal_validation_result
    assert formal.formal_validation_event_count == 4
    assert formal.formal_validation_task_event_count == 16
    assert formal.formal_validation_estimate_count == 64
    assert formal.PRE_geometry_valid_count == 0
    assert formal.POST_geometry_valid_count == 64
    assert formal.all_applicable_primary_metrics_finite is True
    assert formal.all_applicable_auxiliary_metrics_finite is True
    assert dict(result.validation_task_domains) == {
        event_id: ((0, 3, 4) if ":PX5:" in event_id else (0, 1, 2, 3, 4))
        for event_id in result.formal_validation_event_ids
    }
    assert result.runtime_test_event_ids == ()
    assert result.formal_test_runtime_intersection_count == 0
    assert result.test_dataset_getitem_count == 0
    assert result.test_step_call_count == 0
    assert result.Trainer_test_invoked is False


def test_real_gradient_update_checkpoint_and_no_persistence(runtime_result):
    result = runtime_result
    assert all(item.all_gradients_finite for item in result.gradient_group_stats)
    assert all(
        item.nonzero_gradient_tensor_count > 0 for item in result.gradient_group_stats
    )
    assert all(
        item.changed_parameter_tensor_count > 0
        for item in result.parameter_delta_group_stats
    )
    geometry = result.geometry_component_gradient
    assert geometry.PRE_output_component_gradient_exact_zero is True
    assert geometry.POST_output_component_gradient_finite_nonzero is True
    assert dict(result.migration_counts) == {
        "checkpoint_key_count": 122,
        "target_model_key_count": 141,
        "shared_key_count": 122,
        "target_only_key_count": 19,
        "checkpoint_only_key_count": 0,
        "shared_shape_mismatch_count": 0,
        "shared_checkpoint_tensor_equality_count": 122,
    }
    assert result.checkpoint_unchanged is True
    assert result.protected_sources_changed is False
    assert result.protected_state_unchanged is True
    assert result.raw_tree_unchanged is True
    assert result.temporary_trainer_root_removed is True
    assert result.persistent_output_created is False
    assert result.GPU_used is False
    assert result.network_used is False
    assert result.production_geometry_weight_finalized is False
    assert result.production_joint_loss_policy_finalized is False
    assert result.full_training_authorized is False


def test_activation_source_and_artifact_sha_drift_fail_closed(monkeypatch):
    original = integration._sha256_file
    activation_name = (
        "covapie_batch001_13event_model_usable_split_materialization_and_"
        "activation_boundary_v1.py"
    )
    monkeypatch.setattr(
        integration,
        "_sha256_file",
        lambda path: "0" * 64 if path.name == activation_name else original(path),
    )
    with pytest.raises(ValueError, match="BOUND_SOURCE_SHA256_MISMATCH"):
        integration.verify_covapie_batch001_formal_train_validation_source_bindings_v1(
            repository_root=REPOSITORY_ROOT
        )
    monkeypatch.setattr(integration, "_sha256_file", original)
    monkeypatch.setattr(
        integration,
        "_sha256_file",
        lambda path: "0" * 64
        if path.name == activation_owner.SPLIT_INDEX_V1
        else original(path),
    )
    with pytest.raises(ValueError, match="ACTIVATION_ARTIFACT_SHA256_MISMATCH"):
        integration.verify_covapie_batch001_formal_train_validation_source_bindings_v1(
            repository_root=REPOSITORY_ROOT
        )


@pytest.mark.parametrize("replacement_kind", ("missing", "validation", "test"))
def test_train_population_substitution_fails_closed(datamodule, replacement_kind):
    identities = list(datamodule.train_split_batch.sample_identities)
    if replacement_kind == "missing":
        identities = identities[:-1]
    elif replacement_kind == "validation":
        identities[0] = datamodule.authority.validation_event_ids[0]
    else:
        identities[0] = datamodule.authority.test_event_ids[0]
    mutated = replace(
        datamodule.train_split_batch, sample_identities=tuple(identities)
    )
    with pytest.raises(ValueError):
        integration.CovapieBatch001FormalTrainingDataModuleV1(
            authority=datamodule.authority, train_batch=mutated
        )


def test_training_admission_optimizer_and_PRE_mutations_fail_closed(datamodule):
    for name, value in (
        ("sample_training_admitted", (False,) + (True,) * 4),
        ("model_training_activation_authorized", (False,) + (True,) * 4),
        ("optimizer_population_eligible", (False,) + (True,) * 4),
    ):
        mutated = replace(datamodule.train_split_batch, **{name: value})
        with pytest.raises(ValueError):
            integration.CovapieBatch001FormalTrainingDataModuleV1(
                authority=datamodule.authority, train_batch=mutated
            )
    mask = datamodule.train_split_batch.supervision.pre_post_geometry_component_loss_mask.clone()
    mask[0, 0] = True
    supervision = replace(
        datamodule.train_split_batch.supervision,
        pre_post_geometry_component_loss_mask=mask,
    )
    mutated = replace(datamodule.train_split_batch, supervision=supervision)
    with pytest.raises(ValueError):
        integration.CovapieBatch001FormalTrainingDataModuleV1(
            authority=datamodule.authority, train_batch=mutated
        )


@pytest.mark.parametrize("foreign_split", ("train", "test"))
def test_validation_owner_identity_mismatch_fails_closed(
    datamodule, monkeypatch, foreign_split
):
    sentinel = formal_validation_owner.FORMAL_VALIDATION4_REQUEST_SENTINEL_V1
    foreign_ids = getattr(datamodule.authority, f"{foreign_split}_event_ids")
    monkeypatch.setattr(
        formal_validation_owner,
        "FORMAL_VALIDATION4_REQUEST_SENTINEL_V1",
        replace(
            sentinel,
            formal_validation_event_ids=(
                foreign_ids[0],
                *sentinel.formal_validation_event_ids[1:],
            ),
        ),
    )
    with pytest.raises(
        integration._IntegrationInvariantError,
        match="FORMAL_VALIDATION_OWNER_IDENTITY_MISMATCH",
    ):
        integration._validate_current_authority(datamodule.authority)


def test_checkpoint_sha_drift_fails_before_data_or_fit(monkeypatch):
    original = integration._sha256_file
    monkeypatch.setattr(
        integration,
        "_sha256_file",
        lambda path: "0" * 64
        if path.name == integration.CHECKPOINT_RELATIVE_PATH_V1.name
        else original(path),
    )
    with pytest.raises(ValueError, match="CHECKPOINT_SHA256_MISMATCH"):
        integration.run_covapie_batch001_bounded_train_validation_integration_v1(
            repository_root=REPOSITORY_ROOT
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("formal_validation_estimate_count", 63),
        ("checkpoint_weight_migration_call_count_inside_validation", 1),
        ("active_model_parameters_unchanged", False),
        ("active_model_buffers_unchanged", False),
        ("active_model_gradient_states_unchanged", False),
    ),
)
def test_formal_result_mutations_fail_closed(
    runtime_result, field_name, value
):
    mutated = replace(runtime_result.formal_validation_result, **{field_name: value})
    with pytest.raises(
        integration._IntegrationInvariantError,
        match="FORMAL_CURRENT_STATE_VALIDATION_GATE_FAILED",
    ):
        integration._validate_formal_result(
            mutated,
            authority=activation_owner.load_covapie_batch001_formal_split_authority_v1(
                repository_root=REPOSITORY_ROOT
            ),
        )


def test_PX5_tasks_1_or_2_fail_closed(runtime_result):
    formal = runtime_result.formal_validation_result
    rows = list(formal.per_estimate_rows)
    index = next(
        index
        for index, row in enumerate(rows)
        if ":PX5:" in row.canonical_event_id
    )
    rows[index] = replace(rows[index], canonical_task_id=1)
    mutated = replace(formal, per_estimate_rows=tuple(rows))
    with pytest.raises(
        integration._IntegrationInvariantError,
        match="FORMAL_VALIDATION_TASK_DOMAIN_DRIFT",
    ):
        integration._validation_task_domains(mutated)


@pytest.mark.parametrize("failure", ("no_update", "wrong_entry", "mutated_validation"))
def test_state_transition_failures_are_closed(failure):
    pre = {"weight": torch.tensor([1.0])}
    post = {"weight": torch.tensor([2.0])}
    entry = {"weight": torch.tensor([2.0])}
    exit_state = {"weight": torch.tensor([2.0])}
    final = {"weight": torch.tensor([2.0])}
    if failure == "no_update":
        post = entry = exit_state = final = pre
    elif failure == "wrong_entry":
        entry = exit_state = final = {"weight": torch.tensor([3.0])}
    else:
        exit_state = final = {"weight": torch.tensor([3.0])}
    with pytest.raises(integration._IntegrationInvariantError):
        integration._validate_state_transition_snapshots(
            pre_fit=pre,
            post_optimizer=post,
            validation_entry=entry,
            validation_exit=exit_state,
            final_state=final,
        )


def test_source_has_no_scientific_formula_copy_test_call_or_persistence_shortcut():
    source_path = Path(integration.__file__)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    called = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert "test" not in called
    assert "save_checkpoint" not in called
    assert "save" not in called
    assert "urlopen" not in called
    assert "requests" not in source
    for duplicated_equation in (
        "compose_masked_conditional_vlb_nll_v1",
        "masked_gaussian_coordinate_constant_loss_v1",
        "masked_active_epsilon_error_v1",
        "historical_eval_loss_t_v1",
        "masked_t0_coordinate_loss_v1",
        "masked_normalization_delta_log_px_v1",
    ):
        assert duplicated_equation not in source
    for required_fail_closed_gate in (
        "SECOND_TRAIN_DATASET_ITEM_REJECTED",
        "SECOND_VALIDATION_ENTRY_REJECTED",
        "TRAIN_BATCH_ENDED_WITHOUT_EXACT_OPTIMIZER_STEP",
        "VALIDATION_BEFORE_EXACT_OPTIMIZER_LIFECYCLE",
        "FORMAL_TEST_RUNTIME_ACCESS_FORBIDDEN",
    ):
        assert required_fail_closed_gate in source


def _published_mutations():
    valid = checker.valid_published_successor_simulation_v1()
    extra = "scripts/not_authorized.py"
    return (
        replace(valid, head_parent_ids=("0" * 40,)),
        replace(valid, head_subject="wrong subject"),
        replace(
            valid,
            head_changed_entries=valid.head_changed_entries + (("A", extra),),
            head_candidate_path_modes=valid.head_candidate_path_modes + ((extra, "100644"),),
        ),
        replace(valid, head_changed_entries=valid.head_changed_entries[:-1]),
        replace(
            valid,
            head_changed_entries=(("M", valid.head_changed_entries[0][1]),)
            + valid.head_changed_entries[1:],
        ),
        replace(
            valid,
            head_candidate_path_modes=((valid.head_candidate_path_modes[0][0], "100755"),)
            + valid.head_candidate_path_modes[1:],
        ),
        replace(valid, status_entries=(("??", extra),)),
    )


def test_real_repository_profile_and_published_successor_simulation_survive_publication():
    snapshot = checker.collect_repository_git_snapshot_v1(
        repository_root=REPOSITORY_ROOT
    )
    profile = checker.classify_repository_snapshot_v1(snapshot)
    assert profile in {
        checker.CANDIDATE_PRECOMMIT_PROFILE_V1,
        checker.PUBLISHED_SUCCESSOR_PROFILE_V1,
    }
    assert snapshot.branch == "main"
    assert snapshot.ahead_behind == (0, 0)
    assert snapshot.tracked_modified_paths == ()
    assert snapshot.staged_modified_paths == ()
    if profile == checker.CANDIDATE_PRECOMMIT_PROFILE_V1:
        assert snapshot.head == checker.EXPECTED_BASELINE_HEAD_V1
        assert snapshot.origin_main == checker.EXPECTED_BASELINE_HEAD_V1
        assert tuple(sorted(snapshot.status_entries)) == tuple(sorted(
            ("??", path) for path in checker.AUTHORIZED_CANDIDATE_FILES_V1
        ))
        assert snapshot.head_parent_ids == (checker.EXPECTED_BASELINE_PARENT_V1,)
        assert snapshot.head_tree == checker.EXPECTED_BASELINE_TREE_V1
        assert snapshot.head_subject == checker.EXPECTED_BASELINE_SUBJECT_V1
        assert snapshot.head_candidate_path_modes == ()
    else:
        assert snapshot.head == snapshot.origin_main
        assert snapshot.head != checker.EXPECTED_BASELINE_HEAD_V1
        assert snapshot.status_entries == ()
        assert snapshot.head_parent_ids == (checker.EXPECTED_BASELINE_HEAD_V1,)
        assert snapshot.head_subject == checker.PUBLISHED_SUCCESSOR_SUBJECT_V1
        assert tuple(sorted(snapshot.head_changed_entries)) == tuple(sorted(
            ("A", path) for path in checker.AUTHORIZED_CANDIDATE_FILES_V1
        ))
        assert tuple(sorted(snapshot.head_candidate_path_modes)) == tuple(sorted(
            (path, "100644") for path in checker.AUTHORIZED_CANDIDATE_FILES_V1
        ))
    assert (
        checker.classify_repository_snapshot_v1(
            checker.valid_published_successor_simulation_v1()
        )
        == checker.PUBLISHED_SUCCESSOR_PROFILE_V1
    )


@pytest.mark.parametrize("snapshot", _published_mutations())
def test_invalid_published_successor_profiles_fail_closed(snapshot):
    with pytest.raises(ValueError, match=checker.CHECKER_ERROR_V1):
        checker.classify_repository_snapshot_v1(snapshot)


def test_checker_uses_independent_oracle_and_emits_required_markers(
    runtime_result, monkeypatch, capsys
):
    monkeypatch.setattr(
        checker.integration,
        "run_covapie_batch001_bounded_train_validation_integration_v1",
        lambda **unused: runtime_result,
    )
    checked = (
        checker.check_covapie_batch001_formal_training_datamodule_and_train_validation_integration_v1(
            repository_root=REPOSITORY_ROOT
        )
    )
    assert checked.oracle_train_event_ids == runtime_result.formal_train_event_ids
    assert checked.oracle_validation_event_ids == runtime_result.formal_validation_event_ids
    assert checked.oracle_test_event_ids == runtime_result.formal_test_event_ids
    real_profile = checker.classify_repository_profile_v1(
        repository_root=REPOSITORY_ROOT
    )
    expected_candidate_precommit_passed = (
        real_profile == checker.CANDIDATE_PRECOMMIT_PROFILE_V1
    )
    assert (
        checked.candidate_precommit_profile_passed
        is expected_candidate_precommit_passed
    )
    checker.main()
    output = capsys.readouterr().out
    expected_candidate_marker = (
        "candidate_precommit_profile_passed="
        f"{str(expected_candidate_precommit_passed).lower()}"
    )
    for marker in (
        "batch001_formal_training_datamodule_built=true",
        "real_trainer_fit_invoked=true",
        "trainer_fit_call_count=1",
        "formal_train_event_count=5",
        "formal_validation_event_count=4",
        "formal_test_event_count=4",
        "runtime_test_event_count=0",
        "formal_test_runtime_intersection_count=0",
        "automatic_backward_call_count=1",
        "optimizer_step_count=1",
        "formal_validation_estimate_count=64",
        "formal_validation_PRE_valid_count=0",
        "formal_validation_POST_valid_count=64",
        "validation_model_weight_source=CURRENT_LIGHTNING_MODEL_STATE",
        "validation_checkpoint_weight_migration_count=0",
        "test_step_call_count=0",
        "Trainer_test_invoked=false",
        "checkpoint_unchanged=true",
        "persistent_output_created=false",
        "GPU_used=false",
        "network_used=false",
        "full_training_authorized=false",
        expected_candidate_marker,
        "published_successor_profile_simulation_passed=true",
        "ready_for_gpt_review=true",
        "ready_for_publication=true",
    ):
        assert marker in output
