"""One real CPU prepare; all training-path checks use marked synthetic stubs."""

from __future__ import annotations

import ast
from collections import Counter
import contextlib
from dataclasses import replace
import importlib
import importlib.util
import inspect
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest import mock

import pytest
import pytorch_lightning as pl
import torch

from covalent_ext import covapie_train10_cpu_batch_composer_v1 as composer
from covalent_ext import covapie_train10_epoch_datamodule_v1 as data_owner
from covalent_ext import covapie_train10_hidden_post_forward_adapter_v1 as forward_owner
from covalent_ext import covapie_batch001_bounded_training_session_v1 as bounded_owner
from covalent_ext.covapie_current11_training_lightning_module_v1 import (
    CovapieCurrent11TrainingLigandPocketDDPM,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import CANONICAL_TASKS_V1


candidate = os.environ.get("COVAPIE_TRAIN10_BOUNDED_SESSION_CANDIDATE_PATH")
if candidate:
    candidate_path = Path(candidate).resolve(strict=True)
    assert candidate_path.name == "covapie_train10_bounded_training_session_v1.py"
    spec = importlib.util.spec_from_file_location(
        "covalent_ext.covapie_train10_bounded_training_session_v1", candidate_path
    )
    assert spec is not None and spec.loader is not None
    subject = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = subject
    spec.loader.exec_module(subject)
else:
    subject = importlib.import_module("covalent_ext.covapie_train10_bounded_training_session_v1")


def reject(call, reason):
    with pytest.raises(ValueError, match=subject.ERROR_V1) as caught:
        call()
    assert reason in str(caught.value)


def reject_published_owner(call, reason):
    with pytest.raises(ValueError) as caught:
        call()
    assert reason in str(caught.value)


@pytest.fixture(scope="session")
def real_prepared():
    repo = Path(os.environ["COVAPIE_TEST_REPOSITORY_ROOT"]).resolve(strict=True)
    state = Path(os.environ["COVAPIE_TEST_STATE_ROOT"]).resolve(strict=True)
    cache = Path(os.environ["COVAPIE_TEST_CACHE_ROOT"]).resolve(strict=True)
    calls = Counter()
    orig_data_prepare = data_owner.prepare_covapie_train10_epoch_datamodule_v1
    orig_composer_prepare = composer.prepare_covapie_train10_cpu_batch_composer_v1
    orig_carrier_build = composer.build_covapie_train10_cpu_epoch_batch_v1

    def track_data(*args, **kwargs):
        calls["real_data_prepare"] += 1
        return orig_data_prepare(*args, **kwargs)

    def track_composer(*args, **kwargs):
        calls["real_composer_prepare"] += 1
        return orig_composer_prepare(*args, **kwargs)

    def track_carrier(*args, **kwargs):
        calls["real_carrier_build"] += 1
        return orig_carrier_build(*args, **kwargs)

    def forbidden(tag):
        def deny(*_args, **_kwargs):
            calls["FORBIDDEN:" + tag] += 1
            raise AssertionError("real-training tripwire: " + tag)
        return deny

    with contextlib.ExitStack() as stack:
        stack.enter_context(mock.patch.object(data_owner, "prepare_covapie_train10_epoch_datamodule_v1", track_data))
        stack.enter_context(mock.patch.object(composer, "prepare_covapie_train10_cpu_batch_composer_v1", track_composer))
        stack.enter_context(mock.patch.object(composer, "build_covapie_train10_cpu_epoch_batch_v1", track_carrier))
        for owner, name, tag in (
            (torch, "load", "checkpoint_deserialization"),
            (torch, "save", "tensor_or_optimizer_state_save"),
            (torch.Tensor, "backward", "backward"),
            (torch.autograd, "grad", "autograd_grad"),
            (torch.nn.Module, "__call__", "real_model_forward"),
            (torch.optim.AdamW, "__init__", "optimizer_creation"),
            (torch.optim.AdamW, "step", "optimizer_step"),
            (pl.Trainer, "__new__", "real_trainer_creation"),
            (forward_owner, "compute_covapie_current11_training_losses_v1", "production_loss"),
            (forward_owner.CovapieTrain10HiddenPostForwardLigandPocketDDPMV1, "__init__", "real_neural_model_creation"),
        ):
            stack.enter_context(mock.patch.object(owner, name, forbidden(tag)))
        # Guard ONLY checkpoint targets, never normal CPU fixtures or third-party imports.
        for name in ("stat", "lstat", "open", "read_bytes"):
            original = getattr(Path, name)

            def checked(path, *args, _original=original, _name=name, **kwargs):
                if path.suffix == ".ckpt":
                    return forbidden("checkpoint_" + _name)()
                return _original(path, *args, **kwargs)

            stack.enter_context(mock.patch.object(Path, name, checked))
        prepared = subject.prepare_covapie_train10_bounded_training_session_v1(
            repository_root=repo, state_root=state, cache_root=cache
        )
        assert calls == Counter(real_data_prepare=1, real_composer_prepare=1, real_carrier_build=5)
        yield prepared, calls
        assert calls == Counter(real_data_prepare=1, real_composer_prepare=1, real_carrier_build=5)
        print("REAL_CPU_PREPARE=1 REAL_COMPOSER_PREPARE=1 REAL_CARRIER_BUILDS=5 REAL_TRAINER_FIT=0")


def test_fresh_process_silent_candidate_import_and_ast():
    source = Path(subject.__file__).resolve(strict=True)
    tree = ast.parse(source.read_text(encoding="utf-8"))
    imported = {
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    } | {
        alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert not any(name and (name.startswith("tests") or name == "dataset" or name == "lightning_modules") for name in imported)
    assert "train5_carrier_to_cpu" not in source.read_text(encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    script = (
        "import importlib.util,sys;"
        "s=importlib.util.spec_from_file_location('covalent_ext.covapie_train10_bounded_training_session_v1',sys.argv[1]);"
        "m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)"
    )
    completed = subprocess.run(
        (sys.executable, "-B", "-c", script, str(source)), env=env,
        capture_output=True, text=True, check=False
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == "" and completed.stderr == ""


def test_one_published_datamodule_five_cpu_carriers_and_exact5_plan(real_prepared):
    prepared, calls = real_prepared
    module, plan = prepared.datamodule, prepared.plan
    assert type(module) is data_owner.CovapieTrain10EpochDataModuleV1
    assert prepared.carriers is module.carriers
    assert module.prepared.training_session_active is False
    assert plan.epochs == (0, 1, 2, 3, 4) and plan.seed == 0
    assert plan.canonical_masks == tuple(row[:3] for row in CANONICAL_TASKS_V1)
    assert plan.canonical_masks[3][1:] == ("scaffold_only", "B3")
    assert plan.event_count == 10 and plan.leakage_group_count == 3
    assert plan.event_epoch_rows == 50 and plan.exact5_task_counts == (10,) * 5
    assert plan.carrier_seals == tuple(c.payload_sha256 for c in prepared.carriers)
    assert len(plan.source_bindings) == len(subject.DIRECT_SOURCE_PINS_V1)
    assert plan.source_bindings == subject.DIRECT_SOURCE_PINS_V1
    assert (plan.build_status, plan.execute_status) == ("NOT_RUN", "NOT_RUN")
    assert plan.checkpoint_identity_verified_this_prepare is False
    assert plan.trainer_runtime_validated is False and plan.ready_for_training is False
    assert plan.feature_semantics_audit_required_later is True
    assert plan.step12d_is_only_smoke_legality_check is True
    ids = module.prepared.sample_identities
    events = module.prepared.canonical_event_ids
    assert len(ids) == len(set(ids)) == len(events) == 10
    assert module.prepared.formal_splits == ("train",) * 10
    assert len(set(module.prepared.leakage_group_ids)) == 3
    assert len(module.prepared.source_bindings) > 0
    counts = Counter()
    for epoch, carrier in enumerate(prepared.carriers):
        assert carrier.epoch == epoch and carrier.task_schedule_seed == 0
        assert carrier.sample_identities == ids and carrier.canonical_event_ids == events
        assert carrier.formal_splits == ("train",) * 10
        assert carrier.source_audit_blocks[0].sample_identities == ids[:5]
        assert tuple(block.sample_identities for block in carrier.source_audit_blocks[1:]) == tuple((identity,) for identity in ids[5:])
        assert carrier.source_audit_blocks[0].supervision is not None
        assert carrier.supervision is carrier.supervision  # no rebuilt supervision
        assert tuple(carrier.supervision.canonical_task_id.tolist()) == carrier.scheduled_task_ids
        assert carrier.batch_positions == tuple(range(10))
        assert carrier.direct_source_bindings and carrier.batch001_source_authority_bindings and carrier.legacy_source_bindings
        assert composer.validate_covapie_train10_cpu_epoch_batch_v1(carrier) is True
        assert data_owner.validate_covapie_train10_epoch_datamodule_carrier_v1(carrier, current_epoch=epoch) is True
        assert carrier.legacy_post_overlay_applied is False
        assert carrier.training_session_active is False and carrier.trainer_integrated is False
        assert carrier.real_model_executed is False and carrier.parameter_update_performed is False
        counts.update(carrier.scheduled_task_ids)
    assert tuple(counts[index] for index in range(5)) == (10,) * 5
    module.setup("fit")
    for epoch, carrier in enumerate(prepared.carriers):
        loader = module.build_train_dataloader_for_epoch_v1(epoch)
        assert len(loader) == len(loader.dataset) == 1
        assert next(iter(loader)) is carrier
        assert module.on_before_batch_transfer(carrier, 0) is carrier
        assert module.transfer_batch_to_device(carrier, torch.device("cpu"), 0) is carrier
        assert module.on_after_batch_transfer(carrier, 0) is carrier
    assert calls == Counter(real_data_prepare=1, real_composer_prepare=1, real_carrier_build=5)
    print("REAL_EVENT_EPOCH_ROWS=50 EXACT5_TASK_COUNTS=10_EACH B3_PRESENT=true")


def test_static_model_route_lifecycle_and_installed_transfer_selector(real_prepared):
    prepared, _ = real_prepared
    owner = subject.CovapieTrain10BoundedTrainingLigandPocketDDPMV1
    assert owner.__mro__[1] is forward_owner.CovapieTrain10HiddenPostForwardLigandPocketDDPMV1
    assert owner.forward is forward_owner.CovapieTrain10HiddenPostForwardLigandPocketDDPMV1.forward
    assert owner.training_step is CovapieCurrent11TrainingLigandPocketDDPM.training_step
    assert owner.configure_optimizers is CovapieCurrent11TrainingLigandPocketDDPM.configure_optimizers
    assert "__init__" not in owner.__dict__ and owner.validation_epoch_end is None
    assert "transfer_batch_to_device" not in owner.__dict__
    from pytorch_lightning.trainer.connectors.data_connector import _DataHookSelector
    hook_source = inspect.getsource(_DataHookSelector.get_instance)
    assert hook_source.index("is_overridden(hook_name, self.datamodule)") < hook_source.index("is_overridden(hook_name, self.model)")
    assert all(name in data_owner.CovapieTrain10EpochDataModuleV1.__dict__ for name in (
        "on_before_batch_transfer", "transfer_batch_to_device", "on_after_batch_transfer"
    ))
    # Bare nn.Module is a synthetic, parameter-free hook receiver, not DDPM construction.
    synthetic = object.__new__(owner)
    torch.nn.Module.__init__(synthetic)
    synthetic._trainer = SimpleNamespace(datamodule=prepared.datamodule)
    assert synthetic.setup("fit") is None
    assert not any(hasattr(synthetic, name) for name in ("train_dataset", "val_dataset", "test_dataset"))
    reject(lambda: synthetic.setup("validate"), "MODEL_SETUP_FIT_ONLY")
    synthetic._trainer = SimpleNamespace(datamodule=object())
    reject(lambda: synthetic.setup("fit"), "PUBLISHED_TRAIN10_DATAMODULE_REQUIRED")
    synthetic._trainer = SimpleNamespace(datamodule=prepared.datamodule)
    synthetic.train_dataset = object()
    reject(lambda: synthetic.setup("fit"), "LEGACY_MODEL_DATASET_PRESENT")
    assert synthetic.configure_gradient_clipping(object()) is None
    reject(lambda: synthetic.configure_gradient_clipping(object(), gradient_clip_val=0.5), "GRADIENT_CLIPPING_DISABLED")


def test_pure_bounded_trainer_policy_and_override_rejection(real_prepared):
    prepared, _ = real_prepared
    kwargs = subject._trainer_kwargs(prepared.state_root)
    assert kwargs["default_root_dir"] == str(prepared.state_root)
    assert kwargs["precision"] == "32-true"
    assert kwargs["accelerator"] == "cpu"
    assert kwargs["devices"] == kwargs["num_nodes"] == 1
    assert kwargs["min_epochs"] == kwargs["max_epochs"] == kwargs["max_steps"] == 5
    assert kwargs["limit_train_batches"] == kwargs["accumulate_grad_batches"] == kwargs["reload_dataloaders_every_n_epochs"] == 1
    assert kwargs["limit_val_batches"] == kwargs["limit_test_batches"] == kwargs["num_sanity_val_steps"] == 0
    assert kwargs["gradient_clip_val"] is None and kwargs["gradient_clip_algorithm"] is None
    assert kwargs["use_distributed_sampler"] is False
    assert kwargs["callbacks"] == [] and kwargs["logger"] is False
    assert kwargs["enable_checkpointing"] is False and kwargs["enable_progress_bar"] is False
    assert kwargs["enable_model_summary"] is False and kwargs["profiler"] is None
    assert kwargs["deterministic"] is True
    assert "fast_dev_run" not in kwargs and "overfit_batches" not in kwargs
    for overrides in ({"max_steps": 6}, {"limit_val_batches": 1}, {"callbacks": [object()]}, {"gradient_clip_val": 1.0}, {"fast_dev_run": True}, {"precision": "16-mixed"}):
        reject_published_owner(lambda value=overrides: bounded_owner.build_covapie_batch001_bounded_trainer_kwargs_v1(default_root_dir=prepared.state_root, overrides=value), "TRAINER_")
    assert subject._trainer_kwargs(prepared.state_root) == kwargs


def test_default_denial_precedes_all_runtime_checkpoint_and_model_checks(real_prepared):
    prepared, calls = real_prepared
    before = calls.copy()
    for argument in (False, 0, 1, "true", None, object()):
        reject(lambda arg=argument: subject.build_covapie_train10_bounded_training_runtime_v1(
            execution_authorized=arg, prepared=prepared, runtime_root=object()
        ), "NEW_EXPLICIT_USER_EXECUTION_AUTHORIZATION_REQUIRED")
        reject(lambda arg=argument: subject.execute_covapie_train10_bounded_training_session_v1(
            execution_authorized=arg, runtime=object()
        ), "NEW_EXPLICIT_USER_EXECUTION_AUTHORIZATION_REQUIRED")
    assert calls == before
    reject(lambda: subject.prepare_covapie_train10_bounded_training_session_v1(
        repository_root=None, state_root=prepared.state_root, cache_root=prepared.cache_root
    ), "CANONICAL_REPOSITORY_ROOT_REQUIRED")
    reject(lambda: subject.prepare_covapie_train10_bounded_training_session_v1(
        repository_root=prepared.repository_root, state_root=prepared.repository_root, cache_root=prepared.cache_root
    ), "CANONICAL_STATE_ROOT_REQUIRED")
    reject(lambda: subject.prepare_covapie_train10_bounded_training_session_v1(
        repository_root=prepared.repository_root, state_root=prepared.state_root, cache_root=prepared.state_root
    ), "CANONICAL_CACHE_ROOT_REQUIRED")
    assert calls == before


def test_fail_closed_pins_prepared_identity_epoch_and_dangerous_runtime_roots(real_prepared, monkeypatch, tmp_path):
    prepared, calls = real_prepared
    before = calls.copy()
    pins = subject.DIRECT_SOURCE_PINS_V1
    monkeypatch.setattr(subject, "DIRECT_SOURCE_PINS_V1", ((pins[0][0], "0" * 64), *pins[1:]))
    reject(lambda: subject.verify_covapie_train10_bounded_training_sources_v1(prepared.repository_root), "DIRECT_SOURCE_PIN_DRIFT")
    monkeypatch.setattr(subject, "DIRECT_SOURCE_PINS_V1", pins)
    reject(lambda: subject._audit_prepared(replace(prepared, carriers=tuple(list(prepared.carriers)))), "PUBLISHED_DATAMODULE_OR_CARRIER_IDENTITY_REQUIRED")
    reject(lambda: subject._audit_prepared(replace(prepared, repository_root=tmp_path)), "PUBLISHED_DATAMODULE_OR_CARRIER_IDENTITY_REQUIRED")
    reject_published_owner(lambda: data_owner.validate_covapie_train10_epoch_datamodule_carrier_v1(prepared.carriers[0], current_epoch=True), "EPOCH_OUTSIDE_EXACT5")
    reject_published_owner(lambda: data_owner.validate_covapie_train10_epoch_datamodule_carrier_v1(prepared.carriers[0], current_epoch=5), "EPOCH_OUTSIDE_EXACT5")
    reject(lambda: subject._runtime_directory(prepared.repository_root, prepared), "NEW_EMPTY_RUNTIME_ROOT_REQUIRED")
    reject(lambda: subject._runtime_directory(prepared.state_root, prepared), "NEW_EMPTY_RUNTIME_ROOT_REQUIRED")
    assert calls == before


def test_synthetic_identity_single_fit_request_guard_and_exception_priority(real_prepared, tmp_path):
    prepared, calls = real_prepared
    before = calls.copy()
    runtime_root = tmp_path / "synthetic_empty_runtime_plan"
    runtime_root.mkdir()
    assert subject._runtime_directory(runtime_root, prepared) is runtime_root
    kwargs = subject._trainer_kwargs(runtime_root)
    fit_arguments = []
    model_stub = object()  # no real LightningModule/weights

    def stub_fit(*, model, datamodule, ckpt_path):
        fit_arguments.append((model, datamodule, ckpt_path))

    synthetic = subject.CovapieTrain10BoundedTrainingRuntimeV1(
        prepared=prepared, model=model_stub, datamodule=prepared.datamodule,
        trainer=SimpleNamespace(fit=stub_fit), runtime_root=runtime_root,
        checkpoint_metadata={}, migration_metadata={}, trainer_kwargs=kwargs,
    )
    reject(lambda: subject.execute_covapie_train10_bounded_training_session_v1(runtime=synthetic), "NEW_EXPLICIT_USER_EXECUTION_AUTHORIZATION_REQUIRED")
    assert synthetic.fit_request_count == 0 and not fit_arguments
    assert subject.execute_covapie_train10_bounded_training_session_v1(
        execution_authorized=True, runtime=synthetic
    ) is synthetic  # strictly synthetic stub; no production execution
    assert fit_arguments == [(model_stub, prepared.datamodule, None)]
    assert synthetic.fit_request_count == 1 and synthetic.trainer_runtime_validated is False
    reject(lambda: subject.execute_covapie_train10_bounded_training_session_v1(
        execution_authorized=True, runtime=synthetic
    ), "SINGLE_FIT_REQUEST_ONLY")
    assert len(fit_arguments) == 1

    thrown = RuntimeError("synthetic fit primary exception")

    def failing_fit(**_kwargs):
        raise thrown

    failed = replace(synthetic, trainer=SimpleNamespace(fit=failing_fit), fit_request_count=0)
    with pytest.raises(RuntimeError) as caught:
        subject.execute_covapie_train10_bounded_training_session_v1(
            execution_authorized=True, runtime=failed
        )
    assert caught.value is thrown and failed.fit_request_count == 1
    reject(lambda: subject.execute_covapie_train10_bounded_training_session_v1(
        execution_authorized=True, runtime=failed
    ), "SINGLE_FIT_REQUEST_ONLY")
    mismatch = replace(synthetic, datamodule=object(), fit_request_count=0)
    reject(lambda: subject.execute_covapie_train10_bounded_training_session_v1(
        execution_authorized=True, runtime=mismatch
    ), "RUNTIME_OBJECT_IDENTITY_REQUIRED")
    assert calls == before
    print("SYNTHETIC_FIT_REQUESTS=2 REAL_TRAINER_FIT=0")
