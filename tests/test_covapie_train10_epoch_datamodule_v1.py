"""Data-only, no-training tests for the external train10 DataModule Exact2."""

from __future__ import annotations

import ast
import contextlib
import copy
from collections import Counter, defaultdict
from dataclasses import fields, replace
import hashlib
import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace
import sys
from unittest import mock

import pytest
import pytorch_lightning as pl
import torch
from torch.utils.data import SequentialSampler

from covalent_ext import (
    covapie_batch001_13event_model_usable_split_materialization_and_activation_boundary_v1
    as batch001_owner,
)
from covalent_ext import covapie_train10_cpu_batch_composer_v1 as composer
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CANONICAL_TASKS_V1,
    canonical_task_id_for_covapie_current11_sample_v1,
)


def _load_subject():
    candidate = os.environ.get("COVAPIE_TRAIN10_EPOCH_DATAMODULE_CANDIDATE")
    if candidate is None:
        from covalent_ext import covapie_train10_epoch_datamodule_v1 as installed

        return installed
    path = Path(candidate).resolve(strict=True)
    spec = importlib.util.spec_from_file_location(
        "covapie_train10_epoch_datamodule_v1_candidate", path
    )
    assert spec is not None and spec.loader is not None
    subject = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = subject
    spec.loader.exec_module(subject)
    assert Path(subject.__file__).resolve(strict=True) == path
    return subject


subject = _load_subject()
ERROR = subject.TRAIN10_EPOCH_DATAMODULE_ERROR_V1
EXPECTED_MASKS = (
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
)
EXPECTED_BATCH001_EVENTS = (
    "COVAPIE_CYS_SG_EVENT_V1:3LOK:A:CYS:345-:SG:C:DJK:C51",
    "COVAPIE_CYS_SG_EVENT_V1:3LOK:B:CYS:345-:SG:D:DJK:C51",
    "COVAPIE_CYS_SG_EVENT_V1:2ZK1:A:CYS:285-:SG:C:PTG:C8",
    "COVAPIE_CYS_SG_EVENT_V1:2ZK1:B:CYS:285-:SG:D:PTG:C8",
    "COVAPIE_CYS_SG_EVENT_V1:2ZK2:A:CYS:285-:SG:D:PTG:C8",
)
EXPECTED_LEGACY_EVENTS = (
    "COVAPIE_CYS_SG_EVENT_V1:1AU3:A:CYS:25-:SG:B:PCM:C22",
    "COVAPIE_CYS_SG_EVENT_V1:1AU4:A:CYS:25-:SG:B:INP:C17",
    "COVAPIE_CYS_SG_EVENT_V1:1AYU:A:CYS:25-:SG:B:INA:C21",
    "COVAPIE_CYS_SG_EVENT_V1:1AYV:A:CYS:25-:SG:B:IN6:C21",
    "COVAPIE_CYS_SG_EVENT_V1:1AYW:A:CYS:25-:SG:B:IN3:C21",
)
EXPECTED_IDENTITIES = EXPECTED_BATCH001_EVENTS + tuple(
    f"CYS_SG_SAMPLE_INDEX_{index:06d}" for index in range(6, 11)
)
EXPECTED_EVENTS = EXPECTED_BATCH001_EVENTS + EXPECTED_LEGACY_EVENTS


def _reject(call, reason: str | None = None):
    with pytest.raises(ValueError) as error:
        call()
    assert str(error.value).startswith(ERROR)
    if reason is not None:
        assert reason in str(error.value)


def _snapshot(carrier):
    """Full semantic and numeric observation, preserving legal NaNs."""
    result = []
    for model in (
        carrier.model_input_batch,
        *(block.model_input_batch for block in carrier.source_audit_blocks),
    ):
        result.append(tuple(model.keys()))
        result.append(tuple(
            (key, value.clone() if isinstance(value, torch.Tensor) else copy.deepcopy(value))
            for key, value in model.items()
        ))
    for supervision in (
        carrier.supervision,
        *(block.supervision for block in carrier.source_audit_blocks),
    ):
        result.append(tuple(
            (field.name, getattr(supervision, field.name).clone())
            for field in fields(supervision)
        ))
    result.append((
        carrier.sample_identities, carrier.canonical_event_ids,
        carrier.source_branches, carrier.formal_splits, carrier.leakage_group_ids,
        carrier.scheduled_task_ids, carrier.source_audit_blocks,
        carrier.direct_source_bindings, carrier.batch001_source_authority_bindings,
        carrier.legacy_source_bindings, carrier.payload_sha256,
    ))
    return tuple(result)


def _assert_snapshot_exact(carrier, snapshot):
    observed = _snapshot(carrier)
    for left, right in zip(observed[:-1], snapshot[:-1]):
        if left and type(left[0]) is tuple and len(left[0]) == 2:
            for (name, actual), (saved_name, saved) in zip(left, right):
                assert name == saved_name
                if isinstance(actual, torch.Tensor):
                    assert actual.dtype == saved.dtype
                    assert actual.device == saved.device
                    torch.testing.assert_close(actual, saved, rtol=0, atol=0, equal_nan=True)
                else:
                    assert actual == saved
        else:
            assert left == right
    # Source-block dataclasses contain tensors and cannot use dataclass ==.
    for index, (actual, saved) in enumerate(zip(observed[-1], snapshot[-1])):
        if index != 6:
            assert actual == saved
        else:
            assert all(a is b for a, b in zip(actual, saved))


@pytest.fixture(scope="session")
def real_data():
    repo = Path(os.environ["COVAPIE_TEST_REPOSITORY_ROOT"]).resolve(strict=True)
    state = Path(os.environ["COVAPIE_TEST_STATE_ROOT"]).resolve(strict=True)
    cache = Path(os.environ["COVAPIE_TEST_CACHE_ROOT"]).resolve(strict=True)
    calls = Counter()
    true_prepare = composer.prepare_covapie_train10_cpu_batch_composer_v1
    true_build = composer.build_covapie_train10_cpu_epoch_batch_v1

    def tracked_prepare(*args):
        calls["prepare"] += 1
        return true_prepare(*args)

    def tracked_build(*args):
        calls["build"] += 1
        return true_build(*args)

    def forbidden(name):
        def fail(*_args, **_kwargs):
            calls[f"FORBIDDEN:{name}"] += 1
            raise AssertionError(f"no-training tripwire: {name}")
        return fail

    with contextlib.ExitStack() as stack:
        stack.enter_context(mock.patch.object(composer, "prepare_covapie_train10_cpu_batch_composer_v1", tracked_prepare))
        stack.enter_context(mock.patch.object(composer, "build_covapie_train10_cpu_epoch_batch_v1", tracked_build))
        for owner, name, tag in (
            (torch, "load", "checkpoint_deserialization"),
            (torch, "save", "tensor_save"),
            (torch.Tensor, "backward", "backward"),
            (torch.autograd, "grad", "autograd_grad"),
            (torch.optim.AdamW, "__init__", "optimizer_creation"),
            (torch.optim.AdamW, "step", "optimizer_step"),
            (pl.Trainer, "__new__", "trainer_creation"),
            (torch.nn.Module, "__call__", "model_call"),
        ):
            stack.enter_context(mock.patch.object(owner, name, forbidden(tag)))
        module = subject.prepare_covapie_train10_epoch_datamodule_v1(
            repository_root=repo, state_root=state, cache_root=cache
        )
        module.setup("fit")
        assert calls == Counter(prepare=1, build=5)
        yield module, calls
        assert calls == Counter(prepare=1, build=5)


def test_static_import_boundary_and_published_pin():
    source_path = Path(subject.__file__).resolve(strict=True)
    source_text = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source_text)
    imported = {
        alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    assert not any(
        name and (name.startswith("tests") or name.startswith("equivariant_diffusion")
        or name in {"lightning_modules", "dataset"})
        for name in imported
    )
    assert "CovapieTrain10HiddenPostForwardLigandPocketDDPMV1" not in source_text
    assert "reload_dataloaders_every_n_epochs=1" in source_text
    assert subject._COMPOSER_SHA256_V1 == (
        "5c5e7fee4804586e0c6d2a9bdf39a301dd154da92ff2d029f971d6b2b77d2ddd"
    )
    assert subject.__all__ == (
        "TRAIN10_EPOCH_DATAMODULE_ERROR_V1",
        "CovapieTrain10EpochDataModuleV1",
        "prepare_covapie_train10_epoch_datamodule_v1",
        "validate_covapie_train10_epoch_datamodule_carrier_v1",
    )
    assert hashlib.sha256(source_path.read_bytes()).hexdigest() != "0" * 64


def test_real_five_epoch_loader_iteration_and_cpu_transfer_data_only(real_data):
    module, calls = real_data
    prepared = module.prepared
    context_before = (
        prepared.sample_identities, prepared.canonical_event_ids,
        prepared.formal_splits, prepared.leakage_group_ids, prepared.source_bindings,
        prepared._seal,
    )
    tasks_per_event = defaultdict(set)
    task_counts = Counter()
    rows = []
    assert tuple(task[1] for task in CANONICAL_TASKS_V1) == EXPECTED_MASKS
    assert CANONICAL_TASKS_V1[3][2] == "B3"
    for epoch in range(5):
        carrier = module.carriers[epoch]
        original = _snapshot(carrier)
        loader = module.build_train_dataloader_for_epoch_v1(epoch)
        assert len(loader) == 1 and len(loader.dataset) == 1
        assert loader.batch_size == 1 and type(loader.sampler) is SequentialSampler
        assert (loader.num_workers, loader.drop_last, loader.pin_memory, loader.persistent_workers) == (0, False, False, False)
        assert loader.dataset.carrier is carrier and loader.collate_fn.carrier is carrier
        assert loader.generator is not None and loader.generator.device.type == "cpu"
        iterator = iter(loader)
        assert next(iterator) is carrier
        with pytest.raises(StopIteration):
            next(iterator)
        batch = carrier
        assert module.on_before_batch_transfer(batch, 0) is batch
        assert module.transfer_batch_to_device(batch, torch.device("cpu"), 0) is batch
        assert module.on_after_batch_transfer(batch, 0) is batch
        _assert_snapshot_exact(batch, original)
        assert composer.validate_covapie_train10_cpu_epoch_batch_v1(batch)
        assert batch.sample_identities == EXPECTED_IDENTITIES
        assert batch.canonical_event_ids == EXPECTED_EVENTS
        assert batch.formal_splits == ("train",) * 10
        assert len(set(batch.leakage_group_ids)) == 3
        assert batch.batch_positions == tuple(range(10))
        expected_tasks = tuple(
            batch001_owner.preview_owner.canonical_task_id_for_covapie_batch001_sample_v1(
                sample_identity=identity, epoch=epoch, task_schedule_seed=0
            ) if sample < 5 else canonical_task_id_for_covapie_current11_sample_v1(
                sample_key=identity, epoch=epoch, task_schedule_seed=0
            )
            for sample, identity in enumerate(EXPECTED_IDENTITIES)
        )
        assert batch.scheduled_task_ids == expected_tasks
        assert tuple(batch.supervision.canonical_task_id.tolist()) == expected_tasks
        assert batch.model_input_batch["lig_mask"].max().item() == 9
        assert batch.model_input_batch["pocket_mask"].max().item() == 9
        assert batch.legacy_post_overlay_applied is False
        assert batch.training_session_active is False
        assert batch.model_consumer_integrated is False
        assert batch.trainer_integrated is False
        for identity, event, task in zip(
            batch.sample_identities, batch.canonical_event_ids, batch.scheduled_task_ids
        ):
            rows.append((epoch, identity, event, CANONICAL_TASKS_V1[task][1]))
            tasks_per_event[event].add(task)
            task_counts[task] += 1
    assert len(rows) == 50
    assert len(tasks_per_event) == 10
    assert all(task_ids == set(range(5)) for task_ids in tasks_per_event.values())
    assert task_counts == Counter({task: 10 for task in range(5)})
    assert task_counts[3] == 10
    assert context_before == (
        prepared.sample_identities, prepared.canonical_event_ids,
        prepared.formal_splits, prepared.leakage_group_ids, prepared.source_bindings,
        prepared._seal,
    )
    assert calls == Counter(prepare=1, build=5)
    print("REAL_CPU_PREPARE=1 REAL_CARRIER_BUILDS=5 REAL_LOADER_ITERATIONS=5 REAL_EVENT_EPOCH_ROWS=50 TASK_COUNTS=" + str(dict(sorted(task_counts.items()))))


@pytest.mark.parametrize("epoch", (None, True, False, 0.0, 1.0, -1, 5, "0"))
def test_missing_and_wrong_epoch_fail_closed(real_data, epoch):
    module, _ = real_data
    _reject(lambda: module.build_train_dataloader_for_epoch_v1(epoch), "EPOCH_OUTSIDE_EXACT5")
    _reject(lambda: subject.validate_covapie_train10_epoch_datamodule_carrier_v1(
        module.carriers[0], current_epoch=epoch
    ))


def test_fit_only_setup_and_all_heldout_entrypoints_fail_closed(real_data):
    module, _ = real_data
    for stage in (None, "validate", "test", "predict", "train", "fit_test"):
        _reject(lambda stage=stage: module.setup(stage), "FIT_SETUP_ONLY")
    for method in (module.val_dataloader, module.test_dataloader, module.predict_dataloader):
        _reject(method)
    empty = subject.CovapieTrain10EpochDataModuleV1(
        prepared=module.prepared, carriers=module.carriers
    )
    _reject(lambda: empty.build_train_dataloader_for_epoch_v1(0), "FIT_SETUP_REQUIRED")
    assert empty.setup("fit") is None


def test_trainer_epoch_delegation_requires_metadata_only_current_epoch(real_data):
    module, _ = real_data
    try:
        module.trainer = None
        _reject(module.train_dataloader, "EPOCH_OUTSIDE_EXACT5")
        module.trainer = SimpleNamespace()  # metadata-only; not a Trainer
        _reject(module.train_dataloader, "EPOCH_OUTSIDE_EXACT5")
        for epoch in (True, 2.0, -1, 5):
            module.trainer.current_epoch = epoch
            _reject(module.train_dataloader)
        module.trainer.current_epoch = 3
        loader = module.train_dataloader()
        assert next(iter(loader)) is module.carriers[3]
        module.trainer.current_epoch = 4
        _reject(lambda: next(iter(loader)), "EXPECTED_CURRENT_CARRIER_IDENTITY_REQUIRED")
        assert next(iter(module.train_dataloader())) is module.carriers[4]
    finally:
        module.trainer = None


def test_collate_cardinality_type_and_identity_are_strict(real_data):
    module, _ = real_data
    carrier = module.carriers[0]
    loader = module.build_train_dataloader_for_epoch_v1(0)
    for rows in ([], [carrier, carrier], [object()], (carrier,), [module.carriers[1]]):
        _reject(lambda rows=rows: loader.collate_fn(rows), "SINGLE_CARRIER_COLLATE_IDENTITY_REQUIRED")
    assert loader.collate_fn([carrier]) is carrier
    assert next(iter(loader)) is carrier
    assert loader.dataset[0] is carrier
    for index in (True, 1, 0.0):
        with pytest.raises(IndexError):
            loader.dataset[index]


def test_stale_loader_and_old_iterator_rejected_before_delivery(real_data):
    module, _ = real_data
    old = module.build_train_dataloader_for_epoch_v1(0)
    old_iterator = iter(old)
    new = module.build_train_dataloader_for_epoch_v1(1)
    _reject(lambda: next(old_iterator), "EXPECTED_CURRENT_CARRIER_IDENTITY_REQUIRED")
    _reject(lambda: next(iter(old)), "EXPECTED_CURRENT_CARRIER_IDENTITY_REQUIRED")
    _reject(lambda: module.on_before_batch_transfer(module.carriers[0], 0))
    assert next(iter(new)) is module.carriers[1]
    assert module.carriers[0].epoch == 0


@pytest.mark.parametrize("idx,seed,device", (
    (True, 0, torch.device("cpu")),
    (1, 0, torch.device("cpu")),
    (0, True, torch.device("cpu")),
    (0, 1, torch.device("cpu")),
    (0, 0, torch.device("cuda:0")),  # descriptor only; no CUDA initialized
    (0, 0, "cpu"),
))
def test_wrong_index_seed_and_non_cpu_target_fail_closed(real_data, idx, seed, device):
    module, _ = real_data
    module.build_train_dataloader_for_epoch_v1(0)
    batch = module.carriers[0]
    _reject(lambda: subject.validate_covapie_train10_epoch_datamodule_carrier_v1(
        batch, current_epoch=0, dataloader_idx=idx, task_schedule_seed=seed, device=device
    ))
    if idx != 0 or type(idx) is not int:
        for call in (
            lambda: module.on_before_batch_transfer(batch, idx),
            lambda: module.transfer_batch_to_device(batch, torch.device("cpu"), idx),
            lambda: module.on_after_batch_transfer(batch, idx),
        ):
            _reject(call)
    if device != torch.device("cpu"):
        _reject(lambda: module.transfer_batch_to_device(batch, device, 0))


def test_wrong_carrier_type_heldout_metadata_and_seed_fail_closed(real_data):
    module, _ = real_data
    carrier = module.carriers[0]
    module.build_train_dataloader_for_epoch_v1(0)
    for forged in (
        object.__new__(batch001_owner.CovapieBatch001ModelUsableSplitBatchV1),
        SimpleNamespace(formal_split="validation", epoch=0),
        [carrier],
        carrier.model_input_batch,
        replace(carrier, formal_splits=("validation",) + ("train",) * 9),
        replace(carrier, task_schedule_seed=1),
    ):
        _reject(lambda forged=forged: subject.validate_covapie_train10_epoch_datamodule_carrier_v1(
            forged, current_epoch=0
        ))
        _reject(lambda forged=forged: module.on_before_batch_transfer(forged, 0))


@pytest.mark.parametrize("field", ("model_tensor", "supervision_tensor", "source_tensor", "metadata", "status"))
def test_one_off_mutable_copy_corruption_rejected_by_published_seal(real_data, field):
    module, _ = real_data
    module.build_train_dataloader_for_epoch_v1(0)
    original = module.carriers[0]
    baseline = _snapshot(original)
    forged = copy.deepcopy(original)  # never mutate the shared real fixture
    if field == "model_tensor":
        forged.model_input_batch["lig_coords"][0, 0] += 100
    elif field == "supervision_tensor":
        forged.supervision.ligand_role_id[0] = -1
    elif field == "source_tensor":
        forged.source_audit_blocks[0].model_input_batch["lig_coords"][0, 0] += 100
    elif field == "metadata":
        forged.model_input_batch["names"][0] = "forged"
    else:
        forged = replace(forged, trainer_integrated=True)
    _reject(lambda: subject.validate_covapie_train10_epoch_datamodule_carrier_v1(
        forged, current_epoch=0
    ), "PUBLISHED_COMPOSER_VALIDATOR_REJECTED")
    _reject(lambda: module.transfer_batch_to_device(forged, torch.device("cpu"), 0))
    _assert_snapshot_exact(original, baseline)
    assert composer.validate_covapie_train10_cpu_epoch_batch_v1(original)


def test_direct_source_expected_pin_drift_stops_before_prepare(real_data, monkeypatch):
    module, calls = real_data
    monkeypatch.setattr(subject, "_COMPOSER_SHA256_V1", "0" * 64)
    _reject(lambda: subject.prepare_covapie_train10_epoch_datamodule_v1(
        repository_root=module.prepared.repository_root,
        state_root=module.prepared.state_root,
        cache_root=module.prepared.cache_root,
    ), "PUBLISHED_COMPOSER_PIN_DRIFT")
    assert calls == Counter(prepare=1, build=5)


def test_dataloader_cpu_generator_does_not_touch_callers_global_rng(real_data):
    module, _ = real_data
    try:
        module.trainer = None
        global_before = torch.get_rng_state().clone()
        for epoch in range(5):
            loader = module.build_train_dataloader_for_epoch_v1(epoch)
            assert next(iter(loader)) is module.carriers[epoch]
            assert torch.equal(torch.get_rng_state(), global_before)
        assert torch.equal(torch.get_rng_state(), global_before)
    finally:
        module.trainer = None
