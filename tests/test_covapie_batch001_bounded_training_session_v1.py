"""No-update assembly tests for the bounded Batch001 training session V1."""

from __future__ import annotations

import contextlib
from dataclasses import fields, replace
import inspect
import json
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest
import torch
from torch.utils.data import SequentialSampler

from covalent_ext import covapie_batch001_bounded_training_session_v1 as owner
from covalent_ext import (
    covapie_batch001_hidden_post_forward_adapter_v1 as forward_adapter_owner,
)
from covalent_ext.covapie_current11_training_lightning_module_v1 import (
    CovapieCurrent11TrainingLigandPocketDDPM,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


ROOT = Path(__file__).resolve().parents[1]
CACHE_ROOT = ROOT.parent / "covapie-state/bulk-multisource-cys-sg-v1/rcsb"


@pytest.fixture(scope="module")
def prepared_no_update():
    """Run the real carrier prepare path under process-wide training tripwires."""

    calls: list[str] = []

    def forbidden(name: str):
        def tripwire(*_args: object, **_kwargs: object) -> None:
            calls.append(name)
            raise AssertionError(f"forbidden no-update call: {name}")

        return tripwire

    with contextlib.ExitStack() as stack:
        stack.enter_context(mock.patch.object(
            owner.migration_owner,
            "load_covapie_current11_legacy_checkpoint_v1",
            new=forbidden("checkpoint_deserialization"),
        ))
        stack.enter_context(mock.patch.object(
            owner.migration_owner,
            "migrate_covapie_current11_legacy_checkpoint_state_dict_v1",
            new=forbidden("checkpoint_migration"),
        ))
        stack.enter_context(mock.patch.object(
            torch,
            "load",
            new=forbidden("torch.load"),
        ))
        stack.enter_context(mock.patch.object(
            torch,
            "save",
            new=forbidden("torch.save"),
        ))
        stack.enter_context(mock.patch.object(
            owner.CovapieBatch001BoundedTrainingLigandPocketDDPMV1,
            "__new__",
            new=forbidden("real_model_construction"),
        ))
        stack.enter_context(mock.patch.object(
            owner.pl.Trainer,
            "__new__",
            new=forbidden("real_trainer_construction"),
        ))
        stack.enter_context(mock.patch.object(
            forward_adapter_owner.CovapieBatch001HiddenPostForwardLigandPocketDDPMV1,
            "forward",
            new=forbidden("real_model_forward"),
        ))
        stack.enter_context(mock.patch.object(
            forward_adapter_owner,
            "compute_covapie_current11_training_losses_v1",
            new=forbidden("production_loss"),
        ))
        stack.enter_context(mock.patch.object(
            torch.Tensor,
            "backward",
            new=forbidden("backward"),
        ))
        stack.enter_context(mock.patch.object(
            torch.autograd,
            "backward",
            new=forbidden("autograd.backward"),
        ))
        stack.enter_context(mock.patch.object(
            torch.optim.AdamW,
            "__init__",
            new=forbidden("optimizer_construction"),
        ))
        stack.enter_context(mock.patch.object(
            torch.optim.AdamW,
            "step",
            new=forbidden("optimizer_step"),
        ))
        prepared = owner.prepare_covapie_batch001_bounded_training_session_v1(
            repository_root=ROOT,
            cache_root=CACHE_ROOT,
        )
        assert calls == []
        yield prepared, calls
        assert calls == []


def _tensor_fields(carrier: object) -> tuple[torch.Tensor, ...]:
    model = tuple(
        value
        for value in carrier.model_input_batch.values()
        if isinstance(value, torch.Tensor)
    )
    supervision = tuple(
        getattr(carrier.supervision, field.name)
        for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
    )
    return model + supervision


def test_prepare_only_summary_and_checkpoint_identity(
    prepared_no_update: tuple[object, list[str]],
) -> None:
    prepared, calls = prepared_no_update
    summary = prepared.summary
    assert summary.task_id == owner.TASK_ID_V1
    assert summary.implementation_status == "PREPARED_NOT_EXECUTED"
    assert summary.default_prepare_only is True
    assert summary.checkpoint_identity_verified is True
    assert summary.checkpoint_size_bytes == 17_861_341
    assert summary.checkpoint_sha256 == (
        "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
    )
    assert summary.validation_enabled is False
    assert summary.formal_validation_runtime_integrated is False
    assert summary.test_evaluation_enabled is False
    assert summary.trainer_runtime_integration_validated is False
    assert summary.formal_scientific_training_started is False
    assert summary.ready_for_training is False
    assert summary.geometry_training_gradient_accepted is False
    assert summary.feature_semantics_audit_required_later is True
    assert summary.step12d_is_only_smoke_legality_check is True
    assert summary.prior_single_step_authorization_consumed is True
    assert all(
        getattr(summary, name) is False
        for name in (
            "checkpoint_loaded",
            "real_model_instantiated",
            "real_forward_executed",
            "production_loss_executed",
            "backward_executed",
            "optimizer_created",
            "optimizer_step_executed",
            "parameter_update_performed",
            "trainer_created",
            "trainer_fit_executed",
        )
    )
    assert calls == []


def test_current_source_drift_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    relative, digest = owner.DIRECT_BOUND_SOURCE_SHA256_V1[0]
    monkeypatch.setattr(
        owner,
        "DIRECT_BOUND_SOURCE_SHA256_V1",
        ((relative, "0" * 64),) + owner.DIRECT_BOUND_SOURCE_SHA256_V1[1:],
    )
    with pytest.raises(ValueError, match="DIRECT_BOUND_SOURCE_SHA256_MISMATCH"):
        owner.verify_covapie_batch001_bounded_training_session_sources_v1(
            repository_root=ROOT
        )
    assert digest != "0" * 64


def test_invalid_split_epoch_and_seed_are_rejected_before_prepare() -> None:
    valid = owner.CovapieBatch001BoundedTrainingSessionConfigV1()
    invalid = (
        replace(valid, formal_split="validation"),
        replace(valid, formal_split="test"),
        replace(valid, epochs=(0, 1, 2, 3)),
        replace(valid, epochs=(0, 1, 2, 3, 5)),
        replace(valid, task_schedule_seed=1),
    )
    for config in invalid:
        with pytest.raises(
            ValueError,
            match="SESSION_CONFIG_OUTSIDE_EXACT_BOUNDED_TRAIN5_POLICY",
        ):
            owner.prepare_covapie_batch001_bounded_training_session_v1(
                config=config,
                repository_root=ROOT,
                cache_root=CACHE_ROOT,
            )


def test_five_real_train5_carriers_refresh_tasks_and_hidden_post_eligibility(
    prepared_no_update: tuple[object, list[str]],
) -> None:
    prepared, _ = prepared_no_update
    carriers = prepared.carriers
    summaries = prepared.summary.epoch_summaries
    assert tuple(carrier.epoch for carrier in carriers) == (0, 1, 2, 3, 4)
    assert all(carrier.formal_split == "train" for carrier in carriers)
    assert all(
        carrier.sample_identities == prepared.authority.train_event_ids
        for carrier in carriers
    )
    for epoch, carrier in enumerate(carriers):
        assert owner.validate_covapie_batch001_train5_epoch_carrier_v1(
            carrier, expected_epoch=epoch
        )
        assert summaries[epoch].scheduled_task_ids == tuple(
            carrier.supervision.canonical_task_id.tolist()
        )
        assert summaries[epoch].generated_atom_counts == tuple(
            int(
                carrier.supervision.ligand_base_generation_mask[:, 0][
                    carrier.model_input_batch["lig_mask"] == sample
                ].sum().item()
            )
            for sample in range(5)
        )
    assert tuple(
        summary.hidden_post_eligible_count for summary in summaries
    ) == (5, 4, 5, 4, 2)
    for sample in range(5):
        assert {
            carrier.training_scheduled_task_ids[sample] for carrier in carriers
        } == set(range(5))
        assert len({
            tuple(
                carrier.supervision.ligand_base_generation_mask[:, 0][
                    carrier.model_input_batch["lig_mask"] == sample
                ].tolist()
            )
            for carrier in carriers
        }) == 5


def test_canonical_exact5_uses_semantic_long_names_and_preserves_b3(
    prepared_no_update: tuple[object, list[str]],
) -> None:
    prepared, _ = prepared_no_update
    assert prepared.summary.canonical_mask_semantic_names == (
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    )
    assert prepared.summary.canonical_mask_display_aliases == (
        "A", "B", "B2", "B3", "C"
    )
    assert len(prepared.summary.canonical_mask_semantic_names) == 5


def test_stale_epoch0_carrier_cannot_serve_other_epoch(
    prepared_no_update: tuple[object, list[str]],
) -> None:
    prepared, _ = prepared_no_update
    with pytest.raises(ValueError, match="CARRIER_EPOCH_MISMATCH"):
        owner.validate_covapie_batch001_train5_epoch_carrier_v1(
            prepared.carriers[0], expected_epoch=1
        )
    with pytest.raises(ValueError, match="CARRIER_TASK_SCHEDULE_SEED_MISMATCH"):
        owner.validate_covapie_batch001_train5_epoch_carrier_v1(
            prepared.carriers[0], expected_epoch=0, task_schedule_seed=1
        )


def test_loader_preserves_whole_carrier_without_default_collate_stacking(
    prepared_no_update: tuple[object, list[str]],
) -> None:
    prepared, _ = prepared_no_update
    datamodule = owner.CovapieBatch001BoundedTrainingDataModuleV1(
        carriers=prepared.carriers,
        config=prepared.config,
    )
    for epoch, carrier in enumerate(prepared.carriers):
        first = datamodule.build_train_dataloader_for_epoch_v1(epoch)
        second = datamodule.build_train_dataloader_for_epoch_v1(epoch)
        assert len(first) == len(second) == 1
        assert first.batch_size == second.batch_size == 1
        assert type(first.sampler) is SequentialSampler
        assert first.num_workers == 0
        assert first.drop_last is False
        assert list(first) == [carrier]
        assert list(second) == [carrier]
        yielded = list(
            datamodule.build_train_dataloader_for_epoch_v1(epoch)
        )[0]
        assert yielded is carrier
        assert torch.equal(
            yielded.model_input_batch["lig_source_row_index"],
            carrier.model_input_batch["lig_source_row_index"],
        )
        assert torch.equal(
            yielded.model_input_batch["pocket_source_row_index"],
            carrier.model_input_batch["pocket_source_row_index"],
        )


def test_cpu_transfer_rebuilds_dataclass_and_preserves_every_field(
    prepared_no_update: tuple[object, list[str]],
) -> None:
    prepared, _ = prepared_no_update
    original = prepared.carriers[3]
    before_fingerprint = prepared.summary.epoch_summaries[3].carrier_fingerprint
    transferred = owner.transfer_covapie_batch001_train5_carrier_to_cpu_v1(
        original, current_epoch=3
    )
    assert type(transferred) is type(original)
    assert transferred is not original
    assert transferred.model_input_batch is not original.model_input_batch
    assert transferred.supervision is not original.supervision
    for field in fields(type(original)):
        if field.name not in {"model_input_batch", "supervision"}:
            assert getattr(transferred, field.name) is getattr(original, field.name)
    assert tuple(transferred.model_input_batch) == tuple(original.model_input_batch)
    for name, before in original.model_input_batch.items():
        after = transferred.model_input_batch[name]
        if isinstance(before, torch.Tensor):
            assert after.device.type == "cpu"
            assert after.dtype == before.dtype
            assert after.shape == before.shape
            assert torch.equal(after, before)
        else:
            assert after is before
    for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1):
        before = getattr(original.supervision, field.name)
        after = getattr(transferred.supervision, field.name)
        assert after.device.type == "cpu"
        assert after.dtype == before.dtype
        assert after.shape == before.shape
        if before.is_floating_point():
            assert torch.allclose(
                after, before, rtol=0, atol=0, equal_nan=True
            )
        else:
            assert torch.equal(after, before)
    fingerprint, _ = owner.preflight_owner.audit_covapie_batch001_feature_post_use_carrier_v1(
        transferred
    )
    assert fingerprint == before_fingerprint
    assert all(tensor.device.type == "cpu" for tensor in _tensor_fields(transferred))


def test_heldout_carrier_and_loader_access_are_rejected(
    prepared_no_update: tuple[object, list[str]],
) -> None:
    prepared, _ = prepared_no_update
    datamodule = owner.CovapieBatch001BoundedTrainingDataModuleV1(
        carriers=prepared.carriers,
        config=prepared.config,
    )
    with pytest.raises(
        ValueError, match="FORMAL_VALIDATION_DATALOADER_NOT_INTEGRATED"
    ):
        datamodule.val_dataloader()
    with pytest.raises(
        ValueError, match="FORMAL_TEST_DATALOADER_ACCESS_FORBIDDEN"
    ):
        datamodule.test_dataloader()
    heldout_labeled = replace(prepared.carriers[0], formal_split="validation")
    with pytest.raises(ValueError, match="EXACT_TRAIN5_CARRIER_CONTRACT_INVALID"):
        owner.CovapieBatch001BoundedTrainingDataModuleV1(
            carriers=(heldout_labeled,) + prepared.carriers[1:],
            config=prepared.config,
        )


def test_trainer_plan_is_exact_and_out_of_bounds_overrides_fail_closed() -> None:
    kwargs = owner.build_covapie_batch001_bounded_trainer_kwargs_v1(
        default_root_dir=ROOT
    )
    assert kwargs["accelerator"] == "cpu"
    assert kwargs["devices"] == 1
    assert kwargs["max_epochs"] == 5
    assert kwargs["max_steps"] == 5
    assert kwargs["limit_train_batches"] == 1
    assert kwargs["accumulate_grad_batches"] == 1
    assert kwargs["reload_dataloaders_every_n_epochs"] == 1
    assert kwargs["limit_val_batches"] == 0
    assert kwargs["limit_test_batches"] == 0
    assert kwargs["num_sanity_val_steps"] == 0
    assert kwargs["logger"] is False
    assert kwargs["enable_checkpointing"] is False
    assert kwargs["callbacks"] == []
    assert kwargs["gradient_clip_val"] is None
    assert kwargs["precision"] in (32, "32-true")
    invalid_overrides = (
        {"accelerator": "gpu"},
        {"devices": 2},
        {"max_epochs": 6},
        {"max_steps": 6},
        {"limit_train_batches": 2},
        {"accumulate_grad_batches": 2},
        {"reload_dataloaders_every_n_epochs": 0},
        {"limit_val_batches": 1},
        {"enable_checkpointing": True},
        {"logger": True},
        {"callbacks": [object()]},
        {"gradient_clip_val": 1.0},
        {"precision": "16-mixed"},
    )
    for overrides in invalid_overrides:
        with pytest.raises(ValueError):
            owner.build_covapie_batch001_bounded_trainer_kwargs_v1(
                default_root_dir=ROOT,
                overrides=overrides,
            )
    with pytest.raises(ValueError, match="TRAINER_OVERRIDE_KEY_INVALID"):
        owner.build_covapie_batch001_bounded_trainer_kwargs_v1(
            default_root_dir=ROOT,
            overrides={"strategy": "ddp"},
        )


def test_model_mro_routing_and_no_new_parameter_owner() -> None:
    model_class = owner.CovapieBatch001BoundedTrainingLigandPocketDDPMV1
    assert model_class.__mro__[1] is (
        forward_adapter_owner.CovapieBatch001HiddenPostForwardLigandPocketDDPMV1
    )
    assert getattr(model_class, "forward") is (
        forward_adapter_owner.CovapieBatch001HiddenPostForwardLigandPocketDDPMV1.forward
    )
    assert getattr(model_class, "training_step") is (
        CovapieCurrent11TrainingLigandPocketDDPM.training_step
    )
    assert getattr(model_class, "configure_optimizers") is (
        CovapieCurrent11TrainingLigandPocketDDPM.configure_optimizers
    )
    assert "__init__" not in model_class.__dict__
    assert not any(
        isinstance(value, (torch.nn.Parameter, torch.nn.Module))
        for value in model_class.__dict__.values()
    )
    assert owner.DEFAULT_LOSS_WEIGHTS_V1.base_diffusion == 1.0
    assert owner.DEFAULT_LOSS_WEIGHTS_V1.covalent_pair_prediction == 1.0
    assert owner.DEFAULT_LOSS_WEIGHTS_V1.pre_post_geometry == 0.0
    assert owner.DEFAULT_LOSS_WEIGHTS_V1.covalent_pair_contrastive == 0.1


def test_model_setup_accepts_only_fit_with_the_bounded_datamodule(
    prepared_no_update: tuple[object, list[str]],
) -> None:
    prepared, _ = prepared_no_update
    datamodule = owner.CovapieBatch001BoundedTrainingDataModuleV1(
        carriers=prepared.carriers,
        config=prepared.config,
    )
    model_spy = SimpleNamespace(
        trainer=SimpleNamespace(datamodule=datamodule),
        train_dataset=None,
        val_dataset=None,
        test_dataset=None,
    )
    assert owner.CovapieBatch001BoundedTrainingLigandPocketDDPMV1.setup(
        model_spy, "fit"
    ) is None
    with pytest.raises(ValueError, match="MODEL_SETUP_FIT_ONLY"):
        owner.CovapieBatch001BoundedTrainingLigandPocketDDPMV1.setup(
            model_spy, "validate"
        )
    model_spy.trainer = SimpleNamespace(datamodule=object())
    with pytest.raises(ValueError, match="MODEL_SETUP_BOUNDED_DATAMODULE_REQUIRED"):
        owner.CovapieBatch001BoundedTrainingLigandPocketDDPMV1.setup(
            model_spy, "fit"
        )


def test_missing_execution_opt_in_stops_before_prepare_or_runtime_build(
    prepared_no_update: tuple[object, list[str]],
) -> None:
    prepared, _ = prepared_no_update
    with mock.patch.object(
        owner,
        "_instantiate_authorized_model_v1",
        side_effect=AssertionError("runtime construction reached"),
    ) as construct:
        with pytest.raises(
            ValueError, match="EXPLICIT_USER_EXECUTION_AUTHORIZATION_REQUIRED"
        ):
            owner.build_covapie_batch001_bounded_training_runtime_v1(
                prepared=prepared,
                runtime_root=ROOT,
            )
        construct.assert_not_called()
    with mock.patch.object(
        owner,
        "prepare_covapie_batch001_bounded_training_session_v1",
        side_effect=AssertionError("prepare reached"),
    ) as prepare:
        with pytest.raises(
            ValueError, match="EXPLICIT_USER_EXECUTION_AUTHORIZATION_REQUIRED"
        ):
            owner.execute_covapie_batch001_bounded_training_session_v1(
                runtime_root=ROOT
            )
        prepare.assert_not_called()


def test_fake_fit_failure_is_not_retried_or_state_reloaded(
    prepared_no_update: tuple[object, list[str]],
) -> None:
    """Interface-spy evidence only; this is not a Trainer lifecycle test."""

    prepared, _ = prepared_no_update

    class FitSpy:
        def __init__(self) -> None:
            self.calls = 0

        def fit(self, **kwargs: object) -> None:
            self.calls += 1
            assert set(kwargs) == {"model", "datamodule", "ckpt_path"}
            assert kwargs["ckpt_path"] is None
            raise RuntimeError("synthetic fit failure")

    fit_spy = FitSpy()
    runtime = owner.CovapieBatch001BoundedTrainingRuntimeV1(
        model=object(),
        datamodule=owner.CovapieBatch001BoundedTrainingDataModuleV1(
            carriers=prepared.carriers,
            config=prepared.config,
        ),
        trainer=fit_spy,
        checkpoint_metadata={},
        migration_metadata={},
        trainer_kwargs={},
    )
    with pytest.raises(RuntimeError, match="synthetic fit failure"):
        owner._invoke_fit_once_v1(runtime)
    assert fit_spy.calls == 1
    assert runtime.fit_call_count == 1
    with pytest.raises(ValueError, match="TRAINER_FIT_RETRY_FORBIDDEN"):
        owner._invoke_fit_once_v1(runtime)
    assert fit_spy.calls == 1
    execute_source = inspect.getsource(
        owner.execute_covapie_batch001_bounded_training_session_v1
    )
    assert execute_source.count("_invoke_fit_once_v1(runtime)") == 1
    assert "while " not in execute_source


def test_module_entry_is_prepare_only_and_emits_no_runtime_claim(
    prepared_no_update: tuple[object, list[str]],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    prepared, _ = prepared_no_update
    monkeypatch.setattr(
        owner,
        "prepare_covapie_batch001_bounded_training_session_v1",
        lambda **_kwargs: prepared,
    )
    assert owner.main([]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["default_prepare_only"] is True
    assert payload["implementation_status"] == "PREPARED_NOT_EXECUTED"
    assert payload["trainer_created"] is False
    assert payload["trainer_fit_executed"] is False
    parser_source = inspect.getsource(owner.main)
    assert "--execute" not in parser_source


def test_future_runtime_code_uses_strict_migration_once_and_no_manual_update() -> None:
    source = Path(owner.__file__).read_text(encoding="utf-8")
    build_source = inspect.getsource(
        owner.build_covapie_batch001_bounded_training_runtime_v1
    )
    invoke_source = inspect.getsource(owner._invoke_fit_once_v1)
    assert build_source.count(
        "load_covapie_current11_legacy_checkpoint_v1"
    ) == 1
    assert build_source.count(
        "migrate_covapie_current11_legacy_checkpoint_state_dict_v1"
    ) == 1
    assert 'migration.get("full_target_strict_load") is not True' in build_source
    assert "strict=False" not in source
    assert ".backward(" not in source
    assert ".step(" not in source
    assert "zero_grad(" not in source
    assert invoke_source.count(".fit(") == 1
