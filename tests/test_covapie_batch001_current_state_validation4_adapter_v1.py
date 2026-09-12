from __future__ import annotations

import ast
from dataclasses import replace
import json
import math
from pathlib import Path
from unittest import mock

import pytest
import torch
from torch import nn

from covalent_ext import (
    covapie_batch001_bounded_training_session_v1 as bounded_owner,
)
from covalent_ext import (
    covapie_batch001_current_state_validation4_adapter_v1 as subject,
)
from covalent_ext import (
    covapie_current11_formal_validation4_lightning_integration_v1
    as old_integration,
)
from covalent_ext import (
    covapie_current11_formal_validation4_masked_vlb_nll_v1 as evaluator,
)
from covalent_ext import covapie_current11_checkpoint_migration_v1 as migration_owner


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CACHE_ROOT = (
    REPOSITORY_ROOT.parent / "covapie-state/bulk-multisource-cys-sg-v1/rcsb"
)
SOURCE_PATH = REPOSITORY_ROOT / (
    "src/covalent_ext/"
    "covapie_batch001_current_state_validation4_adapter_v1.py"
)


def _forbidden(*_args, **_kwargs):
    raise AssertionError("forbidden model, checkpoint, training, or old run invoked")


@pytest.fixture(scope="module")
def prepared():
    return subject.prepare_covapie_batch001_current_state_validation4_v1(
        repository_root=REPOSITORY_ROOT,
        cache_root=CACHE_ROOT,
    )


def test_fixed_current_source_and_helper_semantic_bindings_are_verified():
    bindings = subject.verify_covapie_batch001_current_state_validation4_sources_v1(
        repository_root=REPOSITORY_ROOT
    )
    assert tuple(
        (row.relative_path, row.observed_sha256) for row in bindings
    ) == subject.CURRENT_BOUND_SOURCE_AND_ARTIFACT_SHA256_V1
    by_path = {row.relative_path: row.observed_sha256 for row in bindings}
    assert by_path[
        "src/covalent_ext/covapie_batch001_bounded_training_session_v1.py"
    ] == "f38c3f88822723e44fb55b31a60d0ec1a34236553c71b7e87ecdadd9f7ce3620"
    assert by_path[
        "src/covalent_ext/covapie_current11_training_lightning_module_v1.py"
    ] == "a61041ef44e79c0622645965461bf4cc0275e5f3bec9a756fcf7d36a4c9c391b"
    assert by_path[
        "src/covalent_ext/covapie_current11_auxiliary_model_and_loss_v1.py"
    ] == "bb797fdb0c96ce669a348a3ddf3975771398263cdfa2a22f3d9c55b0011271cd"
    assert by_path[
        "src/covalent_ext/"
        "covapie_current11_formal_validation4_masked_vlb_nll_v1.py"
    ] == "3f53e1bb668dfe5751f154793ba0d4e1f1001e9619f7a8613b7df31b522be755"


def test_current_source_drift_fails_closed(monkeypatch):
    original = subject._sha256_file

    def drift(path):
        if path.name == "covapie_batch001_bounded_training_session_v1.py":
            return "0" * 64
        return original(path)

    monkeypatch.setattr(subject, "_sha256_file", drift)
    with pytest.raises(ValueError, match="CURRENT_SOURCE_SHA256_MISMATCH"):
        subject.verify_covapie_batch001_current_state_validation4_sources_v1(
            repository_root=REPOSITORY_ROOT
        )


def test_default_prepare_and_missing_opt_in_never_reach_model_evaluation(
    monkeypatch,
):
    monkeypatch.setattr(subject, "_guarded_slice_collection_v1", _forbidden)
    monkeypatch.setattr(subject, "_validate_current_source_model_v1", _forbidden)
    with pytest.raises(ValueError, match="EXPLICIT_MODEL_EVALUATION_OPT_IN_REQUIRED"):
        subject.evaluate_covapie_batch001_current_state_validation4_v1(
            source_model=object(),
            execution_opt_in=False,
            caller_model_stage="CALLER_STAGE",
            caller_stage_evidence="SYNTHETIC_TEST_METADATA",
            caller_confirms_model_is_quiescent=True,
            repository_root=REPOSITORY_ROOT,
            cache_root=CACHE_ROOT,
        )


def test_real_prepare_uses_exact_validation4_and_never_constructs_model():
    with (
        mock.patch.object(torch, "load", side_effect=_forbidden),
        mock.patch.object(
            migration_owner,
            "load_covapie_current11_legacy_checkpoint_v1",
            side_effect=_forbidden,
        ),
        mock.patch.object(
            bounded_owner, "_instantiate_authorized_model_v1", side_effect=_forbidden
        ),
        mock.patch.object(
            evaluator,
            "run_covapie_current11_formal_validation4_masked_vlb_nll_v1",
            side_effect=_forbidden,
        ),
        mock.patch.object(evaluator, "_run_impl", side_effect=_forbidden),
        mock.patch.object(
            old_integration,
            "_evaluate_current_model_on_cpu_shadow_v1",
            side_effect=_forbidden,
        ),
        mock.patch.object(torch.Tensor, "backward", side_effect=_forbidden),
        mock.patch.object(torch.optim.Optimizer, "step", side_effect=_forbidden),
        mock.patch.object(bounded_owner.pl, "Trainer", side_effect=_forbidden),
    ):
        value = subject.prepare_covapie_batch001_current_state_validation4_v1(
            repository_root=REPOSITORY_ROOT,
            cache_root=CACHE_ROOT,
        )
    summary = value.summary
    assert summary.formal_validation_event_ids == evaluator.FORMAL_VALIDATION_EVENT_IDS_V1
    assert summary.formal_train_event_ids == evaluator.FORMAL_TRAIN_EVENT_IDS_V1
    assert summary.formal_test_event_ids == value.authority.test_event_ids
    assert summary.validation_ligand_components == ("LN5", "LN5", "PX5", "PX5")
    assert tuple(plan.event_count for plan in summary.task_plans) == (4, 2, 2, 4, 4)
    assert tuple(
        plan.canonical_task_name for plan in summary.task_plans
    ) == tuple(row[1] for row in subject.CANONICAL_MASK_CONTRACT_V1)
    assert summary.task_plans[3].canonical_task_name == "scaffold_only"
    assert all(plan.all_training_masks_closed for plan in summary.task_plans)
    assert summary.validation_training_admission_closed
    assert summary.validation_training_loss_masks_closed
    assert summary.labels_retained_for_evaluation
    assert not summary.test_model_input_constructed
    assert not summary.checkpoint_loaded
    assert not summary.model_constructed
    assert not summary.shadow_model_constructed
    assert not summary.optimizer_created
    assert not summary.Trainer_created
    assert not summary.model_evaluation_executed


def test_prepare_plan_counts_are_not_reported_as_execution(prepared):
    summary = prepared.summary
    assert summary.root_validation_seeds == evaluator.FORMAL_VALIDATION_ROOT_SEEDS_V1
    assert summary.planned_event_count == 4
    assert summary.planned_event_task_combination_count == 16
    assert summary.planned_event_task_seed_estimate_count == 64
    assert summary.planned_task_seed_slice_count == 20
    assert summary.planned_main_dynamics_call_count == 20
    assert summary.planned_t0_dynamics_call_count == 20
    assert summary.planned_total_dynamics_call_count == 40
    assert summary.actual_model_evaluation_count == 0
    assert summary.actual_main_dynamics_call_count == 0
    assert summary.actual_t0_dynamics_call_count == 0
    assert not summary.formal_validation_runtime_validated
    assert not summary.train_validation_lifecycle_integrated


def test_prepare_serialization_is_deterministic_and_explicitly_nonexecution(
    prepared,
):
    first = subject.serialize_covapie_batch001_current_state_validation4_prepare_v1(
        prepared
    )
    second = subject.serialize_covapie_batch001_current_state_validation4_prepare_v1(
        prepared
    )
    assert first == second
    payload = json.loads(first)
    assert payload["implementation_status"] == "PREPARED_NOT_EXECUTED"
    assert payload["primary_metric_name"] == "MASKED_CONDITIONAL_VLB_NLL_V1"
    assert payload["actual_model_evaluation_count"] == 0
    assert payload["checkpoint_loaded"] is False
    assert payload["model_constructed"] is False
    assert payload["formal_validation_runtime_validated"] is False
    assert payload["feature_semantics_audit_required_later"] is True
    assert payload["step12d_is_only_smoke_legality_check"] is True


def _function(tree: ast.Module, name: str) -> ast.FunctionDef:
    return next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def _call_names(node: ast.AST) -> set[str]:
    result = set()
    for call in ast.walk(node):
        if not isinstance(call, ast.Call):
            continue
        if isinstance(call.func, ast.Name):
            result.add(call.func.id)
        elif isinstance(call.func, ast.Attribute):
            result.add(call.func.attr)
    return result


def test_production_route_consumes_caller_model_and_has_checkpoint_loader_tripwire():
    tree = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
    evaluation = _function(
        tree, "evaluate_covapie_batch001_current_state_validation4_v1"
    )
    guarded = _function(tree, "_guarded_slice_collection_v1")
    evaluation_text = ast.unparse(evaluation)
    calls = _call_names(evaluation) | _call_names(guarded)
    assert "_validate_current_source_model_v1(source_model)" in evaluation_text
    assert "_guarded_slice_collection_v1(source_model=source_model" in evaluation_text
    assert "inference_mode" in calls
    assert "eval" in calls
    forbidden = {
        "load",
        "load_covapie_current11_legacy_checkpoint_v1",
        "_instantiate_authorized_model_v1",
        "build_covapie_batch001_bounded_training_runtime_v1",
        "run_covapie_current11_formal_validation4_masked_vlb_nll_v1",
        "fit",
        "backward",
        "step",
        "save",
    }
    assert calls.isdisjoint(forbidden)


class _ProbeModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.weight = nn.Parameter(torch.tensor([2.0, -3.0]))
        self.register_buffer("running", torch.tensor([5.0]))
        self.branch = nn.Linear(2, 1)
        self.mode = "SYNTHETIC_PROBE"
        self.loss_type = "SYNTHETIC"
        self.covapie_current11_loss_weights = None


def _probe_with_mixed_modes_and_grad() -> _ProbeModel:
    model = _ProbeModel()
    model.train()
    model.branch.eval()
    model.weight.grad = torch.tensor([7.0, 11.0])
    return model


def _synthetic_empty_slice(seen, *, model, **_unused):
    assert not torch.is_grad_enabled()
    assert torch.is_inference_mode_enabled()
    assert all(not module.training for module in model.modules())
    seen.append(id(model))
    torch.rand(3)
    return evaluator._SliceOutputV1(
        estimates=(),
        main_calls=1,
        t0_calls=1,
        fixed_clean=True,
        indicator_reused=True,
        tensors_require_grad=False,
    )


def test_synthetic_normal_path_restores_mixed_modes_rng_and_existing_grad(
    prepared,
):
    model = _probe_with_mixed_modes_and_grad()
    modes_before = tuple(module.training for module in model.modules())
    rng_before = torch.random.get_rng_state().clone()
    grad_object = model.weight.grad
    grad_before = grad_object.clone()
    seen = []
    output = subject._guarded_slice_collection_v1(
        source_model=model,
        prepared=prepared,
        slice_evaluator=lambda **kwargs: _synthetic_empty_slice(seen, **kwargs),
        evidence_kind="SYNTHETIC_TEST_FIXTURE",
    )
    assert len(seen) == 20
    assert set(seen) == {id(model)}
    assert output.evidence_kind == "SYNTHETIC_TEST_FIXTURE"
    assert output.main_calls == output.t0_calls == 20
    assert tuple(module.training for module in model.modules()) == modes_before
    assert torch.equal(torch.random.get_rng_state(), rng_before)
    assert model.weight.grad is grad_object
    assert torch.equal(model.weight.grad, grad_before)
    assert output.parameters_unchanged
    assert output.buffers_unchanged
    assert output.gradients_unchanged
    assert output.requires_grad_unchanged
    assert output.parameter_identities_unchanged
    assert output.buffer_identities_unchanged
    assert output.module_identities_unchanged
    assert output.state_keys_unchanged
    assert output.configuration_unchanged
    assert output.carriers_unchanged
    assert output.training_flags_restored
    assert output.CPU_rng_restored
    assert output.CPU_determinism_settings_restored


def test_synthetic_exception_path_restores_each_mode_and_rng_without_grad_change(
    prepared,
):
    model = _probe_with_mixed_modes_and_grad()
    modes_before = tuple(module.training for module in model.modules())
    rng_before = torch.random.get_rng_state().clone()
    grad_object = model.weight.grad
    grad_before = grad_object.clone()

    def explode(**_kwargs):
        torch.rand(4)
        raise RuntimeError("SYNTHETIC_SLICE_FAILURE")

    with pytest.raises(RuntimeError, match="SYNTHETIC_SLICE_FAILURE"):
        subject._guarded_slice_collection_v1(
            source_model=model,
            prepared=prepared,
            slice_evaluator=explode,
            evidence_kind="SYNTHETIC_TEST_FIXTURE",
        )
    assert tuple(module.training for module in model.modules()) == modes_before
    assert torch.equal(torch.random.get_rng_state(), rng_before)
    assert model.weight.grad is grad_object
    assert torch.equal(model.weight.grad, grad_before)


@pytest.mark.parametrize("target", ("parameter", "buffer"))
def test_synthetic_parameter_or_buffer_mutation_is_detected_not_repaired(
    prepared, target,
):
    model = _probe_with_mixed_modes_and_grad()
    before = (
        model.weight.detach().clone()
        if target == "parameter"
        else model.running.detach().clone()
    )

    def mutate(*, model, **_unused):
        with torch.no_grad():
            if target == "parameter":
                model.weight.add_(1.0)
            else:
                model.running.add_(1.0)
        return evaluator._SliceOutputV1(
            estimates=(),
            main_calls=1,
            t0_calls=1,
            fixed_clean=True,
            indicator_reused=True,
            tensors_require_grad=False,
        )

    with pytest.raises(
        subject._AdapterInvariantError,
        match="SOURCE_MODEL_STATE_MUTATED_DURING_VALIDATION",
    ):
        subject._guarded_slice_collection_v1(
            source_model=model,
            prepared=prepared,
            slice_evaluator=mutate,
            evidence_kind="SYNTHETIC_TEST_FIXTURE",
        )
    after = model.weight.detach() if target == "parameter" else model.running
    assert not torch.equal(after, before)


def test_synthetic_new_module_parameter_and_state_key_are_rejected(prepared):
    model = _probe_with_mixed_modes_and_grad()

    def register(*, model, **_unused):
        model.illegal_persistent_shadow = nn.Linear(2, 2)
        return evaluator._SliceOutputV1(
            estimates=(),
            main_calls=1,
            t0_calls=1,
            fixed_clean=True,
            indicator_reused=True,
            tensors_require_grad=False,
        )

    with pytest.raises(
        subject._AdapterInvariantError,
        match="SOURCE_MODEL_STATE_MUTATED_DURING_VALIDATION",
    ):
        subject._guarded_slice_collection_v1(
            source_model=model,
            prepared=prepared,
            slice_evaluator=register,
            evidence_kind="SYNTHETIC_TEST_FIXTURE",
        )
    assert "illegal_persistent_shadow" in dict(model.named_modules())
    assert any(
        name.startswith("illegal_persistent_shadow.")
        for name in model.state_dict()
    )


def _synthetic_rows(prepared):
    values = dict(zip(prepared.summary.formal_validation_event_ids, (0.0, 10.0, 100.0, 110.0)))
    rows = []
    for task_id, preview in prepared.task_batches:
        supervision = preview.supervision
        ligand_mask = preview.model_input_batch["lig_mask"]
        for seed in evaluator.FORMAL_VALIDATION_ROOT_SEEDS_V1:
            for sample, event_id in enumerate(preview.sample_identities):
                record = prepared.record_by_event[event_id]
                sample_nodes = ligand_mask == sample
                generated = int(
                    supervision.ligand_base_generation_mask[
                        sample_nodes, 0
                    ].sum().item()
                )
                fixed = int(
                    supervision.ligand_base_fixed_mask[
                        sample_nodes, 0
                    ].sum().item()
                )
                pair_count = int(
                    supervision.pair_candidate_offsets[sample + 1].item()
                    - supervision.pair_candidate_offsets[sample].item()
                )
                value = values[event_id]
                task4 = task_id == 4
                rows.append(evaluator.FormalValidationEstimateV1(
                    canonical_event_id=event_id,
                    pdb_id=record.pdb_id,
                    ligand_component_id=record.ligand_component_id,
                    formal_split="validation",
                    leakage_group=prepared.leakage_by_event[event_id],
                    profile=evaluator._profile_name(record),
                    canonical_task_id=task_id,
                    canonical_task_name=subject.CANONICAL_MASK_CONTRACT_V1[task_id][1],
                    canonical_task_alias=subject.CANONICAL_MASK_CONTRACT_V1[task_id][2],
                    root_validation_seed=seed,
                    main_timestep_int=1,
                    generated_atom_count=generated,
                    fixed_atom_count=fixed,
                    coordinate_dimension=3 * (generated - int(task4)),
                    main_active_epsilon_error=1.0,
                    SNR_weight=1.0,
                    loss_t=1.0,
                    t0_coordinate_loss=1.0,
                    t0_categorical_loss=1.0,
                    negative_log_coordinate_constant=1.0,
                    kl_prior=1.0,
                    masked_delta_log_px=1.0,
                    masked_conditional_vlb_nll=value,
                    task4_log_pN=1.0 if task4 else None,
                    task4_historical_joint_nll_with_node_prior_diagnostic=(
                        value - 1.0 if task4 else None
                    ),
                    pair_BCE=2.0,
                    POST_geometry_loss=3.0,
                    POST_geometry_prediction_angstrom=4.0,
                    POST_geometry_target_angstrom=5.0,
                    pair_contrastive_loss=6.0,
                    PRE_geometry_valid=False,
                    target_cys_sg_indicator_count=1,
                    pair_candidate_count=pair_count,
                    fixed_ligand_clean_main=True,
                    fixed_ligand_clean_t0=True,
                ))
    return tuple(rows)


def test_published_aggregate_is_called_and_event_macro_differs_from_micro(
    prepared, monkeypatch,
):
    rows = _synthetic_rows(prepared)
    original = evaluator._aggregate
    called = []

    def spy(values):
        called.append(values)
        return original(values)

    monkeypatch.setattr(evaluator, "_aggregate", spy)
    result = subject._validate_and_aggregate_rows_v1(
        estimates=rows, prepared=prepared
    )
    _task_means, _event_means, event_macro, micro, profiles, profile_balanced = result
    assert called == [rows]
    assert event_macro == pytest.approx(55.0)
    assert micro == pytest.approx(42.5)
    assert event_macro != micro
    assert tuple(name for name, _value in profiles) == (
        "STRICT_LINKER_PRESENT",
        "DIRECT_ATTACHMENT_OPTIONAL_LINKER",
    )
    assert tuple(value for _name, value in profiles) == pytest.approx(
        (5.0, 105.0)
    )
    assert profile_balanced == pytest.approx(55.0)


@pytest.mark.parametrize(
    "mutation",
    (
        lambda rows, prepared: rows[:-1],
        lambda rows, prepared: rows[:-1] + (rows[0],),
        lambda rows, prepared: (
            replace(rows[0], canonical_task_id=99),
        ) + rows[1:],
        lambda rows, prepared: (
            replace(rows[0], root_validation_seed=123),
        ) + rows[1:],
        lambda rows, prepared: (
            replace(rows[0], masked_conditional_vlb_nll=float("nan")),
        ) + rows[1:],
        lambda rows, prepared: (
            replace(
                rows[0],
                canonical_event_id=prepared.authority.train_event_ids[0],
            ),
        ) + rows[1:],
        lambda rows, prepared: (
            replace(
                rows[0],
                canonical_event_id=prepared.authority.test_event_ids[0],
            ),
        ) + rows[1:],
    ),
)
def test_duplicate_missing_illegal_nonfinite_train_or_test_rows_fail_closed(
    prepared, mutation,
):
    with pytest.raises(subject._AdapterInvariantError):
        subject._validate_and_aggregate_rows_v1(
            estimates=mutation(_synthetic_rows(prepared), prepared),
            prepared=prepared,
        )


def test_caller_metadata_never_proves_historical_training_origin():
    stage, evidence = subject._validate_caller_metadata(
        caller_model_stage="CALLER_ASSERTED_AFTER_FIT",
        caller_stage_evidence="SYNTHETIC_TEST_METADATA_ONLY",
        caller_confirms_model_is_quiescent=True,
    )
    assert stage == "CALLER_ASSERTED_AFTER_FIT"
    assert evidence == "SYNTHETIC_TEST_METADATA_ONLY"
    assert "UNPROVEN" in subject.MODEL_STATE_TRAINING_PROVENANCE_V1
    assert "NOT_HISTORICAL_OUTPUT644_RECOVERY" in (
        subject.MODEL_STATE_TRAINING_PROVENANCE_V1
    )


def test_canonical_contract_is_exact5_with_b3_and_no_sixth_task():
    assert subject.CANONICAL_MASK_CONTRACT_V1 == (
        (0, "warhead_only", "A"),
        (1, "linker_plus_warhead", "B"),
        (2, "scaffold_plus_warhead", "B2"),
        (3, "scaffold_only", "B3"),
        (4, "scaffold_plus_linker_plus_warhead", "C"),
    )
    assert len(subject.CANONICAL_MASK_CONTRACT_V1) == 5
