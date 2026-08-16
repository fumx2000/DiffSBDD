"""Code-frozen Current11 formal train-only Lightning orchestration V1."""

from __future__ import annotations

import hashlib
import inspect
import math
import stat
from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

import numpy as np
import torch
from torch.utils.data import DataLoader, SequentialSampler

from covalent_ext.biopython_compat import (
    patch_biopython_polypeptide_three_to_one,
)


patch_biopython_polypeptide_three_to_one()

import constants  # noqa: E402
import pytorch_lightning as pl  # noqa: E402
from dataset import ProcessedLigandPocketDataset  # noqa: E402
from covalent_ext import (  # noqa: E402
    covapie_current11_checkpoint_migration_v1 as _checkpoint_migration,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_role_seed_human_gold_ingestion_compiler_v1
    as _human_gold_compiler,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_task2_lightning_runtime_integration_v1
    as _runtime_integration,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_trainable_supervision_materializer_v1 as _materializer,
)
from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (  # noqa: E402
    CovapieCurrent11LossWeightsV1,
)
from covalent_ext.covapie_current11_training_lightning_module_v1 import (  # noqa: E402
    AUTHORITATIVE_SUPERVISION_BATCH_FIELD_V1,
    CovapieCurrent11TrainingLigandPocketDDPM,
)
from covalent_ext.covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1 import (  # noqa: E402
    CHECKPOINT_CHANNEL_ORDER,
    CHECKPOINT_TOKEN_TO_INDEX,
)


__all__ = (
    "FORMAL_TRAINER_SCHEMA_V1",
    "FORMAL_TRAINER_ERROR",
    "FORMAL_CARRIER_RELATIVE_PATH_V1",
    "FORMAL_CARRIER_SHA256_V1",
    "CovapieCurrent11FormalTrainOnlyLigandPocketDDPMV1",
    "CovapieCurrent11FormalTrainOnlySessionV1",
    "build_covapie_current11_formal_train_only_session_v1",
)


FORMAL_TRAINER_SCHEMA_V1 = "covapie_current11_formal_train_only_trainer_v1"
FORMAL_TRAINER_ERROR = "COVAPIE_CURRENT11_FORMAL_TRAINER_V1_ERROR"
FORMAL_CARRIER_RELATIVE_PATH_V1 = Path(
    "formal-sidecars/current11-runtime-sample-and-role-order-carrier-v1/"
    "current11_runtime_sample_and_role_order_carrier.npz"
)
FORMAL_CARRIER_SHA256_V1 = (
    "ea3aa7c94b7c88993493662ad6ba7fd95e547ec62612a072f8248a515657e910"
)
FORMAL_TRAINER_SEED_V1 = 20_260_816
FORMAL_TRAINING_CLASS_IDENTITY_V1 = (
    "covalent_ext.covapie_current11_formal_trainer_v1."
    "CovapieCurrent11FormalTrainOnlyLigandPocketDDPMV1"
)

_PATH_TYPE = type(Path())
_FORMAL_CARRIER_ARRAYS_V1 = (
    "names",
    "receptors",
    "lig_mask",
    "pocket_mask",
    "lig_coords",
    "pocket_coords",
    "lig_one_hot",
    "pocket_one_hot",
    "lig_source_row_index",
    "pocket_source_row_index",
    "lig_parser_local_index",
    "pocket_parser_local_index",
)
_CURRENT11_SAMPLE_KEYS_V1 = tuple(
    f"CYS_SG_SAMPLE_INDEX_{index:06d}" for index in range(1, 12)
)
_EXPECTED_ATOM_ENCODER_V1 = {
    "C": 0,
    "N": 1,
    "O": 2,
    "S": 3,
    "B": 4,
    "Br": 5,
    "Cl": 6,
    "P": 7,
    "I": 8,
    "F": 9,
}
_EXPECTED_ATOM_DECODER_V1 = (
    "C", "N", "O", "S", "B", "Br", "Cl", "P", "I", "F"
)
_FORMAL_LOSS_WEIGHTS_V1 = {
    "base_diffusion": 1.0,
    "covalent_pair_prediction": 1.0,
    "pre_post_geometry": 0.0,
    "covalent_pair_contrastive": 0.1,
}
_RAW_TARGET_INDICATOR_FIELD_V1 = (
    "pocket_target_residue_atom_condition_indicator"
)


class _FormalTrainerInvariantError(Exception):
    pass


def _fail() -> NoReturn:
    raise _FormalTrainerInvariantError()


def _public_error(error: BaseException) -> NoReturn:
    if type(error) is ValueError and str(error) == FORMAL_TRAINER_ERROR:
        raise error
    raise ValueError(FORMAL_TRAINER_ERROR) from error


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise _FormalTrainerInvariantError() from error
    return digest.hexdigest()


def _require_root(path: object) -> Path:
    if type(path) is not _PATH_TYPE or not path.is_absolute():
        _fail()
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise _FormalTrainerInvariantError() from error
    if (
        resolved != path
        or stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
    ):
        _fail()
    return path


def _require_regular_identity(
    path: Path, *, sha256: str, mode: int | None,
) -> dict[str, object]:
    try:
        metadata = path.lstat()
    except OSError as error:
        raise _FormalTrainerInvariantError() from error
    digest = _sha256(path)
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or (mode is not None and stat.S_IMODE(metadata.st_mode) != mode)
        or digest != sha256
    ):
        _fail()
    return {
        "relative_identity": path.name,
        "sha256": digest,
        "size_bytes": metadata.st_size,
        "mode": format(stat.S_IMODE(metadata.st_mode), "04o"),
    }


def _validate_dataset_info_v1() -> dict[str, object]:
    dataset_info = constants.dataset_params.get("crossdock")
    if (
        type(dataset_info) is not dict
        or type(dataset_info.get("atom_encoder")) is not dict
        or dataset_info["atom_encoder"] != _EXPECTED_ATOM_ENCODER_V1
        or tuple(dataset_info.get("atom_decoder", ()))
        != _EXPECTED_ATOM_DECODER_V1
        or len(dataset_info["atom_encoder"]) != 10
        or CHECKPOINT_TOKEN_TO_INDEX != _EXPECTED_ATOM_ENCODER_V1
        or CHECKPOINT_CHANNEL_ORDER
        != "C:0|N:1|O:2|S:3|B:4|Br:5|Cl:6|P:7|I:8|F:9"
    ):
        _fail()
    return {
        "dataset_info_source": "constants.dataset_params['crossdock']",
        "checkpoint_channel_order": CHECKPOINT_CHANNEL_ORDER,
        "ligand_atom_channel_count": 10,
        "full_atom_pocket_channel_count": 10,
    }


def _validate_formal_carrier_structure_v1(path: Path) -> dict[str, object]:
    try:
        with np.load(path, allow_pickle=False) as carrier:
            if tuple(carrier.files) != _FORMAL_CARRIER_ARRAYS_V1:
                _fail()
            arrays = {name: carrier[name] for name in carrier.files}
    except (OSError, ValueError, KeyError) as error:
        raise _FormalTrainerInvariantError() from error
    names = arrays["names"]
    receptors = arrays["receptors"]
    lig_mask = arrays["lig_mask"]
    pocket_mask = arrays["pocket_mask"]
    if (
        names.ndim != 1
        or tuple(str(item) for item in names.tolist())
        != _CURRENT11_SAMPLE_KEYS_V1
        or receptors.shape != (11,)
        or lig_mask.shape != (323,)
        or pocket_mask.shape != (2202,)
        or lig_mask.dtype != np.dtype("int64")
        or pocket_mask.dtype != np.dtype("int64")
        or not np.array_equal(
            np.unique(lig_mask), np.arange(11, dtype=np.int64)
        )
        or not np.array_equal(
            np.unique(pocket_mask), np.arange(11, dtype=np.int64)
        )
    ):
        _fail()
    expected_shapes = {
        "lig_coords": (323, 3),
        "pocket_coords": (2202, 3),
        "lig_one_hot": (323, 10),
        "pocket_one_hot": (2202, 10),
        "lig_source_row_index": (323,),
        "pocket_source_row_index": (2202,),
        "lig_parser_local_index": (323,),
        "pocket_parser_local_index": (2202,),
    }
    if any(arrays[name].shape != shape for name, shape in expected_shapes.items()):
        _fail()
    for name in ("lig_coords", "pocket_coords", "lig_one_hot", "pocket_one_hot"):
        if arrays[name].dtype != np.dtype("float32") or not np.isfinite(arrays[name]).all():
            _fail()
    for name in (
        "lig_source_row_index",
        "pocket_source_row_index",
        "lig_parser_local_index",
        "pocket_parser_local_index",
    ):
        if arrays[name].dtype != np.dtype("int64"):
            _fail()
    if (
        not np.allclose(arrays["lig_one_hot"].sum(axis=1), 1.0)
        or not np.allclose(arrays["pocket_one_hot"].sum(axis=1), 1.0)
    ):
        _fail()
    return {
        "sample_count": 11,
        "sample_order": _CURRENT11_SAMPLE_KEYS_V1,
        "ligand_node_count": 323,
        "pocket_node_count": 2202,
        "ligand_feature_width": 10,
        "pocket_feature_width": 10,
        "required_source_parser_identity_arrays_present": True,
    }


def _validate_legacy_constructor_envelope_v1(
    constructor: object,
) -> dict[str, object]:
    if type(constructor) is not dict:
        _fail()
    egnn = constructor.get("egnn_params")
    diffusion = constructor.get("diffusion_params")
    histogram = constructor.get("node_histogram")
    if (
        constructor.get("schema_version")
        != "covapie_current11_validated_legacy_constructor_contract_v1"
        or constructor.get("node_histogram_source")
        != "exact_legacy_checkpoint_hyperparameters"
        or constructor.get("synthetic_node_histogram_used") is not False
        or constructor.get("dataset") != "crossdock"
        or constructor.get("mode") != "pocket_conditioning"
        or constructor.get("pocket_representation") != "full-atom"
        or constructor.get("virtual_nodes") is not False
        or constructor.get("auxiliary_loss") is not False
        or type(egnn) is not dict
        or egnn.get("joint_nf") != 32
        or egnn.get("hidden_nf") != 128
        or egnn.get("n_layers") != 5
        or type(diffusion) is not dict
        or diffusion.get("diffusion_loss_type") != "l2"
        or type(histogram) is not list
        or len(histogram) != 107
        or any(type(row) is not list or len(row) != 1671 for row in histogram)
    ):
        _fail()
    return constructor


def _validate_formal_dataset_v1(
    dataset: object, *, carrier_path: Path,
) -> dict[str, object]:
    if (
        type(dataset) is not ProcessedLigandPocketDataset
        or dataset.transform is not None
        or len(dataset) != 11
        or tuple(str(item) for item in dataset.data.get("names", ()))
        != _CURRENT11_SAMPLE_KEYS_V1
    ):
        _fail()
    required = set(_FORMAL_CARRIER_ARRAYS_V1) | {
        "num_lig_atoms", "num_pocket_nodes"
    }
    if not required <= set(dataset.data):
        _fail()
    lig_coords = dataset.data["lig_coords"]
    pocket_coords = dataset.data["pocket_coords"]
    lig_one_hot = dataset.data["lig_one_hot"]
    pocket_one_hot = dataset.data["pocket_one_hot"]
    if (
        sum(len(value) for value in lig_coords) != 323
        or sum(len(value) for value in pocket_coords) != 2202
        or any(value.ndim != 2 or value.shape[1] != 10 for value in lig_one_hot)
        or any(value.ndim != 2 or value.shape[1] != 10 for value in pocket_one_hot)
    ):
        _fail()
    try:
        with np.load(carrier_path, allow_pickle=False) as carrier:
            parity = (
                torch.equal(torch.cat(lig_coords), torch.from_numpy(carrier["lig_coords"]))
                and torch.equal(
                    torch.cat(pocket_coords), torch.from_numpy(carrier["pocket_coords"])
                )
                and torch.equal(
                    torch.cat(lig_one_hot), torch.from_numpy(carrier["lig_one_hot"])
                )
                and torch.equal(
                    torch.cat(pocket_one_hot), torch.from_numpy(carrier["pocket_one_hot"])
                )
            )
    except (OSError, ValueError, KeyError) as error:
        raise _FormalTrainerInvariantError() from error
    if not parity:
        _fail()
    return {
        "dataset_type": "ProcessedLigandPocketDataset",
        "dataset_center": False,
        "transform": None,
        "sample_count": 11,
        "ligand_node_count": 323,
        "pocket_node_count": 2202,
        "ligand_feature_width": 10,
        "pocket_feature_width": 10,
        "coordinates_carrier_parity": True,
    }


class CovapieCurrent11FormalTrainOnlyLigandPocketDDPMV1(
    CovapieCurrent11TrainingLigandPocketDDPM
):
    """Exact11 train-only owner; evaluation remains intentionally unavailable."""

    validation_epoch_end = None

    def __init__(
        self,
        *,
        legacy_constructor: dict[str, object],
        repository_root: Path,
        state_root: Path,
        legacy_init_checkpoint_sha256: str,
    ) -> None:
        try:
            constructor = _validate_legacy_constructor_envelope_v1(
                legacy_constructor
            )
            repository = _require_root(repository_root)
            state = _require_root(state_root)
            if (
                legacy_init_checkpoint_sha256
                != _checkpoint_migration.COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SHA256_V1
            ):
                _fail()
            egnn_params = dict(constructor["egnn_params"])
            egnn_params["device"] = "cpu"
            loss_weights = dict(_FORMAL_LOSS_WEIGHTS_V1)
            super().__init__(
                outdir=constructor["outdir"],
                dataset="crossdock",
                datadir=constructor["datadir"],
                batch_size=11,
                lr=constructor["lr"],
                egnn_params=Namespace(**egnn_params),
                diffusion_params=Namespace(**constructor["diffusion_params"]),
                num_workers=0,
                augment_noise=constructor["augment_noise"],
                augment_rotation=constructor["augment_rotation"],
                clip_grad=False,
                eval_epochs=constructor["eval_epochs"],
                eval_params=Namespace(**constructor["eval_params"]),
                visualize_sample_epoch=constructor["visualize_sample_epoch"],
                visualize_chain_epoch=constructor["visualize_chain_epoch"],
                auxiliary_loss=False,
                loss_params=Namespace(**constructor["loss_params"]),
                mode="pocket_conditioning",
                node_histogram=constructor["node_histogram"],
                pocket_representation="full-atom",
                virtual_nodes=False,
                target_residue_atom_conditioning=True,
                covapie_current11_task2_runtime_enabled=True,
                covapie_repository_root=str(repository),
                covapie_state_root=str(state),
                covapie_current11_training_enabled=True,
                covapie_current11_task_schedule_seed=0,
                covapie_current11_pair_contrastive_temperature=1.0,
                covapie_current11_loss_weights=loss_weights,
                covapie_current11_authoritative_supervision_batch_field=(
                    AUTHORITATIVE_SUPERVISION_BATCH_FIELD_V1
                ),
            )
            self._covapie_current11_formal_carrier_path_v1 = (
                state / FORMAL_CARRIER_RELATIVE_PATH_V1
            )
            self._covapie_current11_formal_dataset_center_v1 = False
            self.save_hyperparameters({
                "formal_trainer_schema_version": FORMAL_TRAINER_SCHEMA_V1,
                "formal_training_class_identity": FORMAL_TRAINING_CLASS_IDENTITY_V1,
                "covapie_current11_training_enabled": True,
                "covapie_current11_task_schedule_seed": 0,
                "covapie_current11_pair_contrastive_temperature": 1.0,
                "covapie_current11_loss_weights": loss_weights,
                "covapie_current11_loss_weight_base_diffusion": 1.0,
                "covapie_current11_loss_weight_covalent_pair_prediction": 1.0,
                "covapie_current11_loss_weight_pre_post_geometry": 0.0,
                "covapie_current11_loss_weight_covalent_pair_contrastive": 0.1,
                "covapie_current11_authoritative_supervision_batch_field": (
                    AUTHORITATIVE_SUPERVISION_BATCH_FIELD_V1
                ),
                "formal_carrier_relative_path": str(FORMAL_CARRIER_RELATIVE_PATH_V1),
                "formal_carrier_sha256": FORMAL_CARRIER_SHA256_V1,
                "decision_authority_relative_path": str(
                    _human_gold_compiler.CURRENT11_ROLE_SEED_HUMAN_GOLD_DECISION_RELATIVE_PATH_V1
                ),
                "decision_authority_sha256": (
                    _human_gold_compiler.CURRENT11_ROLE_SEED_HUMAN_GOLD_DECISION_SHA256_V1
                ),
                "legacy_initialization_checkpoint_sha256": (
                    legacy_init_checkpoint_sha256
                ),
                "checkpoint_channel_order": CHECKPOINT_CHANNEL_ORDER,
                "formal_dataset_info_source": "constants.dataset_params['crossdock']",
                "formal_node_histogram_source": (
                    "exact_legacy_checkpoint_hyperparameters"
                ),
                "synthetic_node_histogram_used": False,
                "formal_dataset_center": False,
                "formal_batch_size": 11,
            })
            weights = self.covapie_current11_loss_weights
            if (
                self.mode != "pocket_conditioning"
                or self.pocket_representation != "full-atom"
                or self.atom_nf != 10
                or self.aa_nf != 10
                or self.batch_size != 11
                or self.num_workers != 0
                or self.clip_grad is not False
                or self.virtual_nodes is not False
                or self.target_residue_atom_conditioning is not True
                or self.auxiliary_loss is not False
                or self.covapie_current11_task2_runtime_enabled is not True
                or self.covapie_current11_training_enabled is not True
                or not isinstance(weights, CovapieCurrent11LossWeightsV1)
                or vars(weights) != _FORMAL_LOSS_WEIGHTS_V1
                or len(self.state_dict()) != 141
            ):
                _fail()
        except BaseException as error:
            _public_error(error)

    def setup(self, stage: str | None = None) -> None:
        try:
            if stage != "fit":
                _fail()
            (
                self._covapie_current11_task2_remap_context_v1,
                self._covapie_current11_task2_compiler_context_v1,
            ) = _runtime_integration.build_or_reuse_covapie_current11_task2_lightning_runtime_context_pair_v1(
                repository_root=self.covapie_repository_root,
                state_root=self.covapie_state_root,
                remap_context=self._covapie_current11_task2_remap_context_v1,
                compiler_context=self._covapie_current11_task2_compiler_context_v1,
            )
            _require_regular_identity(
                self._covapie_current11_formal_carrier_path_v1,
                sha256=FORMAL_CARRIER_SHA256_V1,
                mode=0o644,
            )
            _validate_formal_carrier_structure_v1(
                self._covapie_current11_formal_carrier_path_v1
            )
            if self.train_dataset is None:
                self.train_dataset = ProcessedLigandPocketDataset(
                    self._covapie_current11_formal_carrier_path_v1,
                    center=False,
                    transform=None,
                )
            _validate_formal_dataset_v1(
                self.train_dataset,
                carrier_path=self._covapie_current11_formal_carrier_path_v1,
            )
            if self.val_dataset is not None or self.test_dataset is not None:
                _fail()
        except BaseException as error:
            _public_error(error)

    def train_dataloader(self) -> DataLoader:
        try:
            _validate_formal_dataset_v1(
                self.train_dataset,
                carrier_path=self._covapie_current11_formal_carrier_path_v1,
            )
            loader = DataLoader(
                self.train_dataset,
                batch_size=11,
                shuffle=False,
                num_workers=0,
                collate_fn=self.train_dataset.collate_fn,
                pin_memory=False,
                drop_last=False,
                persistent_workers=False,
            )
            if (
                len(loader) != 1
                or loader.batch_size != 11
                or loader.num_workers != 0
                or loader.drop_last is not False
                or loader.pin_memory is not False
                or loader.persistent_workers is not False
                or type(loader.sampler) is not SequentialSampler
            ):
                _fail()
            return loader
        except BaseException as error:
            _public_error(error)

    def val_dataloader(self) -> None:
        return None

    def test_dataloader(self) -> None:
        return None

    def on_before_batch_transfer(
        self, batch: object, dataloader_idx: int,
    ) -> dict[str, object]:
        try:
            if (
                type(dataloader_idx) is not int
                or dataloader_idx != 0
                or type(batch) is not dict
                or AUTHORITATIVE_SUPERVISION_BATCH_FIELD_V1 in batch
                or _RAW_TARGET_INDICATOR_FIELD_V1 in batch
            ):
                _fail()
            original_items = tuple(batch.items())
            original_tensors = {
                key: value.detach().clone()
                for key, value in original_items
                if isinstance(value, torch.Tensor)
            }
            wrapped = super().on_before_batch_transfer(batch, dataloader_idx)
            runtime = wrapped.get(_runtime_integration.SIDECAR_FIELD)
            if (
                type(wrapped) is not dict
                or any(wrapped.get(key) is not value for key, value in original_items)
                or type(runtime) is not dict
                or runtime.get("runtime_status") != "full_success"
                or tuple(runtime.get("batch_sample_keys_or_none", ()))
                != _CURRENT11_SAMPLE_KEYS_V1
                or _RAW_TARGET_INDICATOR_FIELD_V1 in wrapped
            ):
                _fail()
            for key, before in original_tensors.items():
                after = wrapped.get(key)
                if not isinstance(after, torch.Tensor) or not torch.equal(after, before):
                    _fail()
            payload = _materializer.load_covapie_current11_machine_authority_payload_v1(
                repo_root=Path(self.covapie_repository_root),
                state_root=Path(self.covapie_state_root),
                runtime_output17=runtime.get("remap_output17_or_none"),
            )
            compiled = _human_gold_compiler.load_and_compile_covapie_current11_role_seed_human_gold_v1(
                state_root=Path(self.covapie_state_root),
                machine_authority_payload=payload,
            )
            bundle = _materializer.build_current11_training_supervision_v1(
                authority_payload=compiled.get("compiled_authority_payload")
            )
            summary = bundle.get("summary")
            supervision = bundle.get("authoritative_supervision")
            if (
                type(summary) is not dict
                or summary.get("sample_count") != 11
                or summary.get("exact3_role_human_gold_count") != 11
                or summary.get("minimal_seed_human_gold_count") != 11
                or summary.get("real_admitted_sample_count") != 11
                or summary.get("checkpoint_channel_order") != CHECKPOINT_CHANNEL_ORDER
                or type(supervision) is not dict
                or supervision.get("sample_keys") != list(_CURRENT11_SAMPLE_KEYS_V1)
                or supervision.get("sample_training_admitted") != [True] * 11
                or supervision.get("ligand_node_offsets", [None])[-1] != 323
                or supervision.get("pocket_node_offsets", [None])[-1] != 2202
                or type(supervision.get("formal_carrier_feature_binding")) is not dict
                or supervision["formal_carrier_feature_binding"].get(
                    "checkpoint_channel_order"
                ) != CHECKPOINT_CHANNEL_ORDER
                or AUTHORITATIVE_SUPERVISION_BATCH_FIELD_V1 in wrapped
            ):
                _fail()
            _materializer.validate_authoritative_current11_training_supervision_v1(
                authoritative_supervision=supervision
            )
            attached = dict(wrapped)
            attached[AUTHORITATIVE_SUPERVISION_BATCH_FIELD_V1] = supervision
            if (
                any(attached.get(key) is not value for key, value in original_items)
                or attached[_runtime_integration.SIDECAR_FIELD] is not runtime
                or _RAW_TARGET_INDICATOR_FIELD_V1 in attached
            ):
                _fail()
            return attached
        except BaseException as error:
            _public_error(error)

    def configure_gradient_clipping(
        self,
        optimizer,
        gradient_clip_val=None,
        gradient_clip_algorithm=None,
    ) -> None:
        del optimizer
        if gradient_clip_val is not None or gradient_clip_algorithm is not None:
            raise ValueError(FORMAL_TRAINER_ERROR)


@dataclass(frozen=True)
class CovapieCurrent11FormalTrainOnlySessionV1:
    model: CovapieCurrent11FormalTrainOnlyLigandPocketDDPMV1
    trainer: pl.Trainer
    checkpoint_metadata: dict[str, object]
    migration_metadata: dict[str, object]
    preflight_metadata: dict[str, object]


def _build_session_impl(
    *,
    repository_root: Path,
    state_root: Path,
    legacy_init_checkpoint: Path,
) -> CovapieCurrent11FormalTrainOnlySessionV1:
    repository = _require_root(repository_root)
    state = _require_root(state_root)
    if type(legacy_init_checkpoint) is not _PATH_TYPE or not legacy_init_checkpoint.is_absolute():
        _fail()
    dataset_info = _validate_dataset_info_v1()
    carrier_path = state / FORMAL_CARRIER_RELATIVE_PATH_V1
    carrier_identity = _require_regular_identity(
        carrier_path, sha256=FORMAL_CARRIER_SHA256_V1, mode=0o644
    )
    carrier_structure = _validate_formal_carrier_structure_v1(carrier_path)
    decision_path = (
        state
        / _human_gold_compiler.CURRENT11_ROLE_SEED_HUMAN_GOLD_DECISION_RELATIVE_PATH_V1
    )
    decision_identity = _require_regular_identity(
        decision_path,
        sha256=_human_gold_compiler.CURRENT11_ROLE_SEED_HUMAN_GOLD_DECISION_SHA256_V1,
        mode=0o644,
    )
    checkpoint = _checkpoint_migration.load_covapie_current11_legacy_checkpoint_v1(
        checkpoint_path=legacy_init_checkpoint
    )
    constructor = _validate_legacy_constructor_envelope_v1(
        checkpoint.get("legacy_constructor")
    )
    pl.seed_everything(FORMAL_TRAINER_SEED_V1, workers=True)
    model = CovapieCurrent11FormalTrainOnlyLigandPocketDDPMV1(
        legacy_constructor=constructor,
        repository_root=repository,
        state_root=state,
        legacy_init_checkpoint_sha256=checkpoint["checkpoint_sha256"],
    )
    migration = _checkpoint_migration.migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
        model=model,
        checkpoint_state_dict=checkpoint["state_dict"],
    )
    if (
        migration.get("checkpoint_key_count") != 122
        or migration.get("target_model_key_count") != 141
        or migration.get("shared_key_count") != 122
        or migration.get("target_only_key_count") != 19
        or migration.get("checkpoint_only_key_count") != 0
        or migration.get("shared_shape_mismatch_count") != 0
        or len(migration.get("target_only_auxiliary_keys", ())) != 18
        or migration.get("full_target_strict_load") is not True
    ):
        _fail()
    trainer = pl.Trainer(
        accelerator="cpu",
        devices=1,
        num_nodes=1,
        strategy="auto",
        precision="32-true",
        max_epochs=5,
        min_epochs=5,
        max_steps=-1,
        limit_train_batches=1,
        limit_val_batches=0,
        limit_test_batches=0,
        num_sanity_val_steps=0,
        check_val_every_n_epoch=1,
        val_check_interval=1.0,
        enable_checkpointing=False,
        callbacks=[],
        logger=False,
        gradient_clip_val=None,
        accumulate_grad_batches=1,
        deterministic=True,
        benchmark=False,
        reload_dataloaders_every_n_epochs=0,
        use_distributed_sampler=False,
        sync_batchnorm=False,
        enable_model_summary=False,
        log_every_n_steps=1,
        enable_progress_bar=False,
    )
    clipping_signature = inspect.signature(model.configure_gradient_clipping)
    if (
        callable(model.validation_epoch_end)
        or tuple(clipping_signature.parameters)
        != ("optimizer", "gradient_clip_val", "gradient_clip_algorithm")
        or trainer.num_devices != 1
        or trainer.max_epochs != 5
        or trainer.limit_train_batches != 1
        or trainer.limit_val_batches != 0
        or trainer.num_sanity_val_steps != 0
        or trainer.checkpoint_callback is not None
        or trainer.logger is not None
    ):
        _fail()
    checkpoint_metadata = {
        key: value for key, value in checkpoint.items() if key != "state_dict"
    }
    return CovapieCurrent11FormalTrainOnlySessionV1(
        model=model,
        trainer=trainer,
        checkpoint_metadata=checkpoint_metadata,
        migration_metadata=dict(migration),
        preflight_metadata={
            "schema_version": FORMAL_TRAINER_SCHEMA_V1,
            "runtime_git_head_binding_used": False,
            "repository_root_validated": True,
            "state_root_validated": True,
            "checkpoint_identity_validated": True,
            "carrier_identity": carrier_identity,
            "carrier_structure": carrier_structure,
            "decision_identity": decision_identity,
            "dataset_info": dataset_info,
            "formal_node_histogram_source": (
                "exact_legacy_checkpoint_hyperparameters"
            ),
            "synthetic_node_histogram_used": False,
            "trainer_seed": FORMAL_TRAINER_SEED_V1,
            "trainer_fit_called": False,
        },
    )


def build_covapie_current11_formal_train_only_session_v1(
    *,
    repository_root: Path,
    state_root: Path,
    legacy_init_checkpoint: Path,
) -> CovapieCurrent11FormalTrainOnlySessionV1:
    """Preflight, exact legacy-init, and construct a no-fit train-only session."""

    try:
        return _build_session_impl(
            repository_root=repository_root,
            state_root=state_root,
            legacy_init_checkpoint=legacy_init_checkpoint,
        )
    except BaseException as error:
        _public_error(error)
