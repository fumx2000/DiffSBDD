"""Epoch-aware, data-only CPU train10 entry point for published composer carriers.

This module does not activate training. A future Trainer connection must set
reload_dataloaders_every_n_epochs=1; its lifecycle is not validated here.
"""

from __future__ import annotations

from dataclasses import fields
import hashlib
from pathlib import Path
import stat
import subprocess
from typing import NoReturn

import pytorch_lightning as pl
import torch
from torch.utils.data import DataLoader, Dataset, SequentialSampler

from covalent_ext import covapie_train10_cpu_batch_composer_v1 as composer


__all__ = (
    "TRAIN10_EPOCH_DATAMODULE_ERROR_V1",
    "CovapieTrain10EpochDataModuleV1",
    "prepare_covapie_train10_epoch_datamodule_v1",
    "validate_covapie_train10_epoch_datamodule_carrier_v1",
)

TRAIN10_EPOCH_DATAMODULE_ERROR_V1 = "COVAPIE_TRAIN10_EPOCH_DATAMODULE_V1_ERROR"
EXACT_EPOCHS_V1 = (0, 1, 2, 3, 4)
TASK_SCHEDULE_SEED_V1 = 0
_COMPOSER_RELATIVE_PATH_V1 = Path(
    "src/covalent_ext/covapie_train10_cpu_batch_composer_v1.py"
)
_COMPOSER_BYTES_V1 = 72926
_COMPOSER_SHA256_V1 = (
    "5c5e7fee4804586e0c6d2a9bdf39a301dd154da92ff2d029f971d6b2b77d2ddd"
)


def _fail(reason: str) -> NoReturn:
    raise ValueError(f"{TRAIN10_EPOCH_DATAMODULE_ERROR_V1}:{reason}")


def _epoch(epoch: object) -> int:
    if type(epoch) is not int or epoch not in EXACT_EPOCHS_V1:
        _fail("EPOCH_OUTSIDE_EXACT5")
    return epoch


def _verify_published_composer(repository_root: object) -> None:
    if not isinstance(repository_root, Path) or not repository_root.is_absolute():
        _fail("EXPLICIT_REPOSITORY_ROOT_REQUIRED")
    path = repository_root / _COMPOSER_RELATIVE_PATH_V1
    try:
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or path.is_symlink():
            _fail("COMPOSER_NOT_REGULAR")
        payload = path.read_bytes()
        source = Path(composer.__file__).resolve(strict=True)
        head = subprocess.run(
            ("git", "show", f"HEAD:{_COMPOSER_RELATIVE_PATH_V1.as_posix()}"),
            cwd=repository_root,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise ValueError(
            f"{TRAIN10_EPOCH_DATAMODULE_ERROR_V1}:COMPOSER_SOURCE_UNAVAILABLE"
        ) from error
    if (
        repository_root.resolve(strict=True) != repository_root
        or source != path
        or len(payload) != _COMPOSER_BYTES_V1
        or hashlib.sha256(payload).hexdigest() != _COMPOSER_SHA256_V1
        or head.returncode != 0
        or head.stdout != payload
    ):
        _fail("PUBLISHED_COMPOSER_PIN_DRIFT")


def _cpu_tensors(carrier: composer.CovapieTrain10CpuEpochBatchV1):
    for model in (
        carrier.model_input_batch,
        *(block.model_input_batch for block in carrier.source_audit_blocks),
    ):
        yield from (value for value in model.values() if isinstance(value, torch.Tensor))
    for supervision in (
        carrier.supervision,
        *(block.supervision for block in carrier.source_audit_blocks),
    ):
        yield from (getattr(supervision, field.name) for field in fields(supervision))


def validate_covapie_train10_epoch_datamodule_carrier_v1(
    carrier: object,
    *,
    current_epoch: object,
    task_schedule_seed: object = TASK_SCHEDULE_SEED_V1,
    dataloader_idx: object = 0,
    device: object = torch.device("cpu"),
) -> bool:
    """Fail closed at delivery/transfer without modifying the source carrier."""
    epoch = _epoch(current_epoch)
    if type(task_schedule_seed) is not int or task_schedule_seed != 0:
        _fail("SEED_OUTSIDE_FIXED_V1")
    if type(dataloader_idx) is not int or dataloader_idx != 0:
        _fail("TRAIN_DATALOADER_INDEX_REQUIRED")
    if device != torch.device("cpu") or type(device) is not torch.device:
        _fail("CPU_TARGET_REQUIRED")
    if type(carrier) is not composer.CovapieTrain10CpuEpochBatchV1:
        _fail("PUBLISHED_TRAIN10_CARRIER_REQUIRED")
    if carrier.epoch != epoch or type(carrier.epoch) is not int:
        _fail("STALE_OR_WRONG_EPOCH")
    if type(carrier.task_schedule_seed) is not int or carrier.task_schedule_seed != 0:
        _fail("CARRIER_SEED_OUTSIDE_FIXED_V1")
    try:
        if composer.validate_covapie_train10_cpu_epoch_batch_v1(carrier) is not True:
            _fail("PUBLISHED_COMPOSER_VALIDATOR_REJECTED")
    except ValueError as error:
        raise ValueError(
            f"{TRAIN10_EPOCH_DATAMODULE_ERROR_V1}:PUBLISHED_COMPOSER_VALIDATOR_REJECTED"
        ) from error
    if any(
        not isinstance(tensor, torch.Tensor) or tensor.device.type != "cpu"
        for tensor in _cpu_tensors(carrier)
    ):
        _fail("CARRIER_CPU_TENSORS_REQUIRED")
    return True


class _OneCarrierDatasetV1(Dataset):
    def __init__(self, carrier: composer.CovapieTrain10CpuEpochBatchV1):
        self.carrier = carrier

    def __len__(self) -> int:
        return 1

    def __getitem__(self, index: int) -> composer.CovapieTrain10CpuEpochBatchV1:
        if type(index) is not int or index != 0:
            raise IndexError(index)
        return self.carrier


class _OneCarrierCollatorV1:
    def __init__(self, module: CovapieTrain10EpochDataModuleV1, carrier: object):
        self.module = module
        self.carrier = carrier

    def __call__(self, rows: object) -> composer.CovapieTrain10CpuEpochBatchV1:
        if type(rows) is not list or len(rows) != 1 or rows[0] is not self.carrier:
            _fail("SINGLE_CARRIER_COLLATE_IDENTITY_REQUIRED")
        return self.module._delivery(self.carrier)


class CovapieTrain10EpochDataModuleV1(pl.LightningDataModule):
    """Own exactly five already-composed, formal-train CPU carriers."""

    def __init__(
        self,
        *,
        prepared: composer.CovapieTrain10CpuBatchPreparedV1,
        carriers: tuple[composer.CovapieTrain10CpuEpochBatchV1, ...],
    ) -> None:
        super().__init__()
        if type(prepared) is not composer.CovapieTrain10CpuBatchPreparedV1:
            _fail("PUBLISHED_PREPARED_REQUIRED")
        _verify_published_composer(prepared.repository_root)
        if type(carriers) is not tuple or len(carriers) != len(EXACT_EPOCHS_V1):
            _fail("EXACT_FIVE_CARRIERS_REQUIRED")
        self.prepared = prepared
        self.carriers = carriers
        self._fit_setup = False
        self._selected_epoch: int | None = None
        for epoch, carrier in zip(EXACT_EPOCHS_V1, carriers):
            validate_covapie_train10_epoch_datamodule_carrier_v1(
                carrier, current_epoch=epoch
            )
            if (
                carrier.repository_root != prepared.repository_root
                or carrier.state_root != prepared.state_root
                or carrier.cache_root != prepared.cache_root
                or carrier.sample_identities != prepared.sample_identities
                or carrier.canonical_event_ids != prepared.canonical_event_ids
                or carrier.formal_splits != prepared.formal_splits
                or carrier.leakage_group_ids != prepared.leakage_group_ids
            ):
                _fail("PREPARED_CARRIER_CONTEXT_MISMATCH")

    def setup(self, stage: str | None = None) -> None:
        if stage != "fit":
            _fail("FIT_SETUP_ONLY")
        self._fit_setup = True

    def _trainer_epoch(self) -> int:
        return _epoch(getattr(getattr(self, "trainer", None), "current_epoch", None))

    def _active_epoch(self) -> int:
        if getattr(self, "trainer", None) is not None:
            return self._trainer_epoch()
        return _epoch(self._selected_epoch)

    def _delivery(self, carrier: object) -> composer.CovapieTrain10CpuEpochBatchV1:
        epoch = self._active_epoch()
        if carrier is not self.carriers[epoch]:
            _fail("EXPECTED_CURRENT_CARRIER_IDENTITY_REQUIRED")
        validate_covapie_train10_epoch_datamodule_carrier_v1(
            carrier, current_epoch=epoch
        )
        return carrier

    def build_train_dataloader_for_epoch_v1(self, epoch: object) -> DataLoader:
        if not self._fit_setup:
            _fail("FIT_SETUP_REQUIRED")
        selected = _epoch(epoch)
        carrier = self.carriers[selected]
        validate_covapie_train10_epoch_datamodule_carrier_v1(
            carrier, current_epoch=selected
        )
        loader = DataLoader(
            _OneCarrierDatasetV1(carrier),
            batch_size=1,
            shuffle=False,
            num_workers=0,
            drop_last=False,
            pin_memory=False,
            persistent_workers=False,
            collate_fn=_OneCarrierCollatorV1(self, carrier),
            generator=torch.Generator(device="cpu").manual_seed(20260915 + selected),
        )
        if (
            len(loader) != 1
            or len(loader.dataset) != 1
            or loader.batch_size != 1
            or type(loader.sampler) is not SequentialSampler
            or loader.num_workers != 0
            or loader.drop_last is not False
            or loader.pin_memory is not False
            or loader.persistent_workers is not False
            or loader.generator is None
        ):
            _fail("EXACT_SINGLE_CARRIER_DATALOADER_CONFIGURATION_REQUIRED")
        self._selected_epoch = selected
        return loader

    def train_dataloader(self) -> DataLoader:
        return self.build_train_dataloader_for_epoch_v1(self._trainer_epoch())

    def on_before_batch_transfer(self, batch: object, dataloader_idx: int):
        return self._transfer_check(batch, dataloader_idx=dataloader_idx)

    def transfer_batch_to_device(
        self, batch: object, device: torch.device, dataloader_idx: int
    ):
        return self._transfer_check(
            batch, dataloader_idx=dataloader_idx, device=device
        )

    def on_after_batch_transfer(self, batch: object, dataloader_idx: int):
        return self._transfer_check(batch, dataloader_idx=dataloader_idx)

    def _transfer_check(
        self, batch: object, *, dataloader_idx: object, device: object = torch.device("cpu")
    ):
        epoch = self._active_epoch()
        if batch is not self.carriers[epoch]:
            _fail("EXPECTED_CURRENT_CARRIER_IDENTITY_REQUIRED")
        validate_covapie_train10_epoch_datamodule_carrier_v1(
            batch, current_epoch=epoch, dataloader_idx=dataloader_idx, device=device
        )
        return batch

    def val_dataloader(self) -> NoReturn:
        _fail("VALIDATION_NOT_SUPPORTED")

    def test_dataloader(self) -> NoReturn:
        _fail("TEST_NOT_SUPPORTED")

    def predict_dataloader(self) -> NoReturn:
        _fail("PREDICT_NOT_SUPPORTED")


def prepare_covapie_train10_epoch_datamodule_v1(
    *, repository_root: Path, state_root: Path, cache_root: Path
) -> CovapieTrain10EpochDataModuleV1:
    """The sole opt-in data construction path: one prepare and five builds."""
    _verify_published_composer(repository_root)
    prepared = composer.prepare_covapie_train10_cpu_batch_composer_v1(
        repository_root, state_root, cache_root
    )
    carriers = tuple(
        composer.build_covapie_train10_cpu_epoch_batch_v1(
            prepared, epoch, TASK_SCHEDULE_SEED_V1
        )
        for epoch in EXACT_EPOCHS_V1
    )
    return CovapieTrain10EpochDataModuleV1(prepared=prepared, carriers=carriers)
