from __future__ import annotations

import copy
import hashlib
import inspect
import os
import shutil
import subprocess
import sys
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch
from torch.utils.data import RandomSampler, SequentialSampler

import constants
import pytorch_lightning as pl
from dataset import ProcessedLigandPocketDataset
from covalent_ext import covapie_current11_checkpoint_migration_v1 as migration
from covalent_ext import covapie_current11_formal_trainer_v1 as subject
from covalent_ext import (
    covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1
    as context_bridge,
)
from covalent_ext import (
    covapie_current11_task2_lightning_runtime_integration_v1
    as runtime_integration,
)
from covalent_ext.covapie_current11_training_lightning_module_v1 import (
    AUTHORITATIVE_SUPERVISION_BATCH_FIELD_V1,
    CovapieCurrent11TrainingLigandPocketDDPM,
)
from pytorch_lightning.trainer.configuration_validator import (
    _verify_loop_configurations,
)
from pytorch_lightning.trainer.states import TrainerFn
from scripts import (
    check_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1
    as bridge_checker,
)

import train_covapie_current11_v1 as cli


ROOT = Path(__file__).resolve().parents[1]
STATE = (ROOT.parent / "covapie-state").resolve()
CHECKPOINT = ROOT / "checkpoints/crossdocked_fullatom_cond.ckpt"
ERROR = subject.FORMAL_TRAINER_ERROR
MIGRATION_ERROR = migration.COVAPIE_CURRENT11_CHECKPOINT_MIGRATION_V1_ERROR
SAMPLE_KEYS = tuple(
    f"CYS_SG_SAMPLE_INDEX_{index:06d}" for index in range(1, 12)
)


def _assert_formal_error(callable_object) -> None:
    with pytest.raises(ValueError) as error:
        callable_object()
    assert str(error.value) == ERROR


@pytest.fixture(scope="module")
def session_and_boundary_calls():
    calls = {
        "forward": 0,
        "training_step": 0,
        "configure_optimizers": 0,
        "fit": 0,
    }
    model_class = subject.CovapieCurrent11FormalTrainOnlyLigandPocketDDPMV1
    original_fit = pl.Trainer.fit

    def forbidden(name):
        def call(*args, **kwargs):
            del args, kwargs
            calls[name] += 1
            raise AssertionError(f"forbidden formal-stage call: {name}")

        return call

    model_class.forward = forbidden("forward")
    model_class.training_step = forbidden("training_step")
    model_class.configure_optimizers = forbidden("configure_optimizers")
    pl.Trainer.fit = forbidden("fit")
    try:
        session = subject.build_covapie_current11_formal_train_only_session_v1(
            repository_root=ROOT,
            state_root=STATE,
            legacy_init_checkpoint=CHECKPOINT,
        )
    finally:
        del model_class.forward
        del model_class.training_step
        del model_class.configure_optimizers
        pl.Trainer.fit = original_fit
    return session, calls


@pytest.fixture(scope="module")
def session(session_and_boundary_calls):
    return session_and_boundary_calls[0]


@pytest.fixture(scope="module")
def setup_model(session):
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
    return model


@pytest.fixture(scope="module")
def attached_batches(setup_model):
    outputs = []
    raw_batches = []
    for unused in range(2):
        del unused
        raw = next(iter(setup_model.train_dataloader()))
        raw_batches.append(raw)
        outputs.append(setup_model.on_before_batch_transfer(raw, 0))
    return raw_batches, outputs


@pytest.fixture(scope="module")
def real_checkpoint_payload():
    return torch.load(CHECKPOINT, map_location="cpu", weights_only=False)


def test_formal_session_builds_exact_model_migration_without_training(
    session_and_boundary_calls,
) -> None:
    session, calls = session_and_boundary_calls
    assert calls == {
        "forward": 0,
        "training_step": 0,
        "configure_optimizers": 0,
        "fit": 0,
    }
    assert type(session.model) is (
        subject.CovapieCurrent11FormalTrainOnlyLigandPocketDDPMV1
    )
    assert isinstance(session.model, CovapieCurrent11TrainingLigandPocketDDPM)
    assert len(session.model.state_dict()) == 141
    assert session.checkpoint_metadata["checkpoint_sha256"] == (
        migration.COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SHA256_V1
    )
    assert session.checkpoint_metadata["checkpoint_state_dict_key_count"] == 122
    assert "state_dict" not in session.checkpoint_metadata
    assert session.migration_metadata["shared_key_count"] == 122
    assert session.migration_metadata["target_only_key_count"] == 19
    assert session.migration_metadata["checkpoint_only_key_count"] == 0
    assert session.migration_metadata["shared_shape_mismatch_count"] == 0
    assert session.migration_metadata["full_target_strict_load"] is True
    assert session.preflight_metadata["runtime_git_head_binding_used"] is False
    assert session.preflight_metadata["trainer_fit_called"] is False


def test_formal_model_exact_architecture_dataset_info_and_loss_weights(
    session,
) -> None:
    model = session.model
    dynamics = model.ddpm.dynamics
    assert model.mode == "pocket_conditioning"
    assert model.pocket_representation == "full-atom"
    assert model.dataset_name == "crossdock"
    assert model.dataset_info is constants.dataset_params["crossdock"]
    assert model.lig_type_encoder == {
        "C": 0, "N": 1, "O": 2, "S": 3, "B": 4,
        "Br": 5, "Cl": 6, "P": 7, "I": 8, "F": 9,
    }
    assert model.pocket_type_encoder == model.lig_type_encoder
    assert model.atom_nf == model.aa_nf == 10
    assert dynamics.atom_encoder[-1].out_features == 32
    assert len(dynamics.egnn._modules) > 0
    egnn = session.checkpoint_metadata["legacy_constructor"]["egnn_params"]
    assert (egnn["joint_nf"], egnn["hidden_nf"], egnn["n_layers"]) == (
        32, 128, 5
    )
    assert model.virtual_nodes is False
    assert model.target_residue_atom_conditioning is True
    assert model.auxiliary_loss is False
    assert model.clip_grad is False
    assert vars(model.covapie_current11_loss_weights) == {
        "base_diffusion": 1.0,
        "covalent_pair_prediction": 1.0,
        "pre_post_geometry": 0.0,
        "covalent_pair_contrastive": 0.1,
    }


def test_formal_training_hparams_are_complete_and_primitive(session) -> None:
    hparams = session.model.hparams
    assert hparams["formal_trainer_schema_version"] == subject.FORMAL_TRAINER_SCHEMA_V1
    assert hparams["covapie_current11_training_enabled"] is True
    assert hparams["covapie_current11_task_schedule_seed"] == 0
    assert hparams["covapie_current11_pair_contrastive_temperature"] == 1.0
    assert hparams["covapie_current11_loss_weights"] == {
        "base_diffusion": 1.0,
        "covalent_pair_prediction": 1.0,
        "pre_post_geometry": 0.0,
        "covalent_pair_contrastive": 0.1,
    }
    assert hparams["covapie_current11_authoritative_supervision_batch_field"] == (
        AUTHORITATIVE_SUPERVISION_BATCH_FIELD_V1
    )
    assert hparams["formal_carrier_sha256"] == subject.FORMAL_CARRIER_SHA256_V1
    assert hparams["decision_authority_sha256"] == (
        "104cc3ec5c9cf6a250f07348695c0a52ca938ed3be082a61e4a983e6f1359ae4"
    )
    assert hparams["legacy_initialization_checkpoint_sha256"] == (
        migration.COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SHA256_V1
    )
    assert hparams["checkpoint_channel_order"] == (
        "C:0|N:1|O:2|S:3|B:4|Br:5|Cl:6|P:7|I:8|F:9"
    )
    assert hparams["formal_node_histogram_source"] == (
        "exact_legacy_checkpoint_hyperparameters"
    )
    assert hparams["synthetic_node_histogram_used"] is False
    assert hparams["formal_training_class_identity"].endswith(
        ".CovapieCurrent11FormalTrainOnlyLigandPocketDDPMV1"
    )
    assert hparams["covapie_current11_task2_runtime_enabled"] is True
    assert hparams["target_residue_atom_conditioning"] is True


def test_exact_real_trainer_envelope_and_no_callbacks_or_logger(session) -> None:
    trainer = session.trainer
    assert type(trainer) is pl.Trainer
    assert trainer.accelerator.__class__.__name__ == "CPUAccelerator"
    assert trainer.num_devices == 1
    assert trainer.num_nodes == 1
    assert trainer.strategy.__class__.__name__ == "SingleDeviceStrategy"
    assert str(trainer.strategy.root_device) == "cpu"
    assert trainer.precision == "32-true"
    assert trainer.max_epochs == trainer.min_epochs == 5
    assert trainer.max_steps == -1
    assert trainer.limit_train_batches == 1
    assert trainer.limit_val_batches == 0
    assert trainer.limit_test_batches == 0
    assert trainer.num_sanity_val_steps == 0
    assert trainer.check_val_every_n_epoch == 1
    assert trainer.val_check_interval == 1.0
    assert trainer.checkpoint_callback is None
    assert trainer.callbacks == []
    assert trainer.logger is None
    assert trainer.loggers == []
    assert trainer.gradient_clip_val is None
    assert trainer.accumulate_grad_batches == 1
    assert torch.are_deterministic_algorithms_enabled() is True
    assert torch.backends.cudnn.benchmark is False
    assert trainer.reload_dataloaders_every_n_epochs == 0
    assert trainer._accelerator_connector.use_distributed_sampler is False
    assert trainer._accelerator_connector._layer_sync is None
    assert trainer.log_every_n_steps == 1
    assert trainer.progress_bar_callback is None
    assert os.environ["PL_GLOBAL_SEED"] == "20260816"
    assert os.environ["PL_SEED_WORKERS"] == "1"


def test_active_lightning_26_configuration_and_clipping_shims(session) -> None:
    model = session.model
    trainer = session.trainer
    assert callable(model.validation_epoch_end) is False
    signature = inspect.signature(type(model).configure_gradient_clipping)
    assert tuple(signature.parameters) == (
        "self",
        "optimizer",
        "gradient_clip_val",
        "gradient_clip_algorithm",
    )
    assert "optimizer_idx" not in signature.parameters
    model.configure_gradient_clipping(
        object(), gradient_clip_val=None, gradient_clip_algorithm=None
    )
    _assert_formal_error(
        lambda: model.configure_gradient_clipping(
            object(), gradient_clip_val=1.0, gradient_clip_algorithm="norm"
        )
    )
    trainer.strategy.connect(model)
    trainer.state.fn = TrainerFn.FITTING
    _verify_loop_configurations(trainer)


def test_setup_and_exact_sequential_full_batch_dataloader(setup_model) -> None:
    model = setup_model
    assert type(model.train_dataset) is ProcessedLigandPocketDataset
    assert model.train_dataset.transform is None
    assert model._covapie_current11_formal_dataset_center_v1 is False
    assert model.val_dataset is None
    assert model.test_dataset is None
    loader = model.train_dataloader()
    assert len(loader) == 1
    assert loader.batch_size == 11
    assert loader.num_workers == 0
    assert loader.drop_last is False
    assert loader.pin_memory is False
    assert loader.persistent_workers is False
    assert type(loader.sampler) is SequentialSampler
    assert not isinstance(loader.sampler, RandomSampler)
    batch = next(iter(loader))
    assert tuple(batch["names"]) == SAMPLE_KEYS
    assert len(batch["num_lig_atoms"]) == 11
    assert int(batch["num_lig_atoms"].sum()) == 323
    assert int(batch["num_pocket_nodes"].sum()) == 2202
    assert batch["lig_one_hot"].shape == (323, 10)
    assert batch["pocket_one_hot"].shape == (2202, 10)
    with np.load(
        STATE / subject.FORMAL_CARRIER_RELATIVE_PATH_V1, allow_pickle=False
    ) as carrier:
        assert torch.equal(batch["lig_coords"], torch.from_numpy(carrier["lig_coords"]))
        assert torch.equal(
            batch["pocket_coords"], torch.from_numpy(carrier["pocket_coords"])
        )


def test_setup_non_fit_stages_and_val_test_lanes_fail_closed(setup_model) -> None:
    _assert_formal_error(lambda: setup_model.setup("test"))
    _assert_formal_error(lambda: setup_model.setup(None))
    _assert_formal_error(lambda: setup_model.setup("predict"))
    assert setup_model.val_dataloader() is None
    assert setup_model.test_dataloader() is None
    with pytest.raises(ValueError):
        setup_model.validation_step({}, 0)
    with pytest.raises(ValueError):
        setup_model.test_step({}, 0)


def test_automatic_runtime_and_authoritative_supervision_attachment(
    attached_batches,
) -> None:
    raw_batches, outputs = attached_batches
    for raw, attached in zip(raw_batches, outputs, strict=True):
        assert runtime_integration.SIDECAR_FIELD not in raw
        assert AUTHORITATIVE_SUPERVISION_BATCH_FIELD_V1 not in raw
        assert "pocket_target_residue_atom_condition_indicator" not in raw
        runtime = attached[runtime_integration.SIDECAR_FIELD]
        supervision = attached[AUTHORITATIVE_SUPERVISION_BATCH_FIELD_V1]
        assert runtime["runtime_status"] == "full_success"
        assert tuple(runtime["batch_sample_keys_or_none"]) == SAMPLE_KEYS
        assert supervision["sample_keys"] == list(SAMPLE_KEYS)
        assert supervision["sample_training_admitted"] == [True] * 11
        assert supervision["ligand_node_offsets"][-1] == 323
        assert supervision["pocket_node_offsets"][-1] == 2202
        assert supervision["formal_carrier_feature_binding"][
            "checkpoint_channel_order"
        ] == "C:0|N:1|O:2|S:3|B:4|Br:5|Cl:6|P:7|I:8|F:9"
        assert "pocket_target_residue_atom_condition_indicator" not in attached
        for key, value in raw.items():
            assert attached[key] is value


def test_attachment_is_repeatable_no_cache_and_preserves_raw_tensors(
    attached_batches,
) -> None:
    raw_batches, outputs = attached_batches
    assert raw_batches[0] is not raw_batches[1]
    assert outputs[0] is not outputs[1]
    assert (
        outputs[0][AUTHORITATIVE_SUPERVISION_BATCH_FIELD_V1]
        is not outputs[1][AUTHORITATIVE_SUPERVISION_BATCH_FIELD_V1]
    )
    left = outputs[0][AUTHORITATIVE_SUPERVISION_BATCH_FIELD_V1]
    right = outputs[1][AUTHORITATIVE_SUPERVISION_BATCH_FIELD_V1]
    for key in left:
        if key == "pre_post_geometry_target_angstrom":
            assert np.array_equal(
                np.asarray(left[key]), np.asarray(right[key]), equal_nan=True
            )
        else:
            assert left[key] == right[key]
    assert outputs[0][runtime_integration.SIDECAR_FIELD] == (
        outputs[1][runtime_integration.SIDECAR_FIELD]
    )
    for raw in raw_batches:
        assert torch.equal(raw["lig_coords"], raw["lig_coords"].clone())
        assert torch.equal(raw["pocket_coords"], raw["pocket_coords"].clone())
        assert torch.equal(raw["lig_one_hot"], raw["lig_one_hot"].clone())
        assert torch.equal(raw["pocket_one_hot"], raw["pocket_one_hot"].clone())


def test_attachment_rejects_collision_wrong_lane_and_non_mapping(
    setup_model,
) -> None:
    raw = next(iter(setup_model.train_dataloader()))
    collision = dict(raw)
    collision[AUTHORITATIVE_SUPERVISION_BATCH_FIELD_V1] = {}
    _assert_formal_error(
        lambda: setup_model.on_before_batch_transfer(collision, 0)
    )
    _assert_formal_error(lambda: setup_model.on_before_batch_transfer(raw, 1))
    _assert_formal_error(
        lambda: setup_model.on_before_batch_transfer(tuple(raw.items()), 0)
    )


@pytest.mark.parametrize(
    "field,mutated",
    (
        ("node_histogram", None),
        ("node_histogram", []),
        ("joint_nf", 64),
        ("hidden_nf", 256),
        ("n_layers", 6),
        ("mode", "joint"),
        ("pocket_representation", "CA"),
        ("virtual_nodes", True),
        ("auxiliary_loss", True),
    ),
)
def test_legacy_constructor_metadata_drift_fails_closed(
    monkeypatch, real_checkpoint_payload, field, mutated,
) -> None:
    payload = dict(real_checkpoint_payload)
    hparams = dict(real_checkpoint_payload["hyper_parameters"])
    if field == "node_histogram" and mutated is None:
        del hparams[field]
    elif field in ("joint_nf", "hidden_nf", "n_layers"):
        egnn = dict(vars(hparams["egnn_params"]))
        egnn[field] = mutated
        hparams["egnn_params"] = Namespace(**egnn)
    else:
        hparams[field] = mutated
    payload["hyper_parameters"] = hparams
    monkeypatch.setattr(
        migration.torch,
        "load",
        lambda *args, **kwargs: payload,
    )
    with pytest.raises(ValueError) as error:
        migration.load_covapie_current11_legacy_checkpoint_v1(
            checkpoint_path=CHECKPOINT
        )
    assert str(error.value) == MIGRATION_ERROR


@pytest.mark.parametrize(
    "repository,state,checkpoint",
    (
        (Path("relative-repository"), STATE, CHECKPOINT),
        (ROOT, Path("relative-state"), CHECKPOINT),
        (ROOT, STATE, Path("relative-checkpoint.ckpt")),
    ),
)
def test_relative_formal_paths_fail_before_construction(
    repository, state, checkpoint,
) -> None:
    _assert_formal_error(
        lambda: subject.build_covapie_current11_formal_train_only_session_v1(
            repository_root=repository,
            state_root=state,
            legacy_init_checkpoint=checkpoint,
        )
    )


def _copy_state_authorities(destination: Path) -> tuple[Path, Path]:
    carrier = destination / subject.FORMAL_CARRIER_RELATIVE_PATH_V1
    decision = destination / (
        "manual-review-aids/current11-trainable-supervision-role-seed-v1/"
        "current11_role_seed_review_decisions.csv"
    )
    carrier.parent.mkdir(parents=True, exist_ok=True)
    decision.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(STATE / subject.FORMAL_CARRIER_RELATIVE_PATH_V1, carrier)
    shutil.copyfile(
        STATE
        / "manual-review-aids/current11-trainable-supervision-role-seed-v1/"
        "current11_role_seed_review_decisions.csv",
        decision,
    )
    carrier.chmod(0o644)
    decision.chmod(0o644)
    return carrier, decision


def test_wrong_checkpoint_carrier_and_decision_identity_fail_closed(
    tmp_path,
) -> None:
    wrong_checkpoint = tmp_path / "wrong.ckpt"
    wrong_checkpoint.write_bytes(b"not-the-authorized-checkpoint")
    _assert_formal_error(
        lambda: subject.build_covapie_current11_formal_train_only_session_v1(
            repository_root=ROOT,
            state_root=STATE,
            legacy_init_checkpoint=wrong_checkpoint,
        )
    )
    missing_state = tmp_path / "missing-authorities"
    missing_state.mkdir()
    _assert_formal_error(
        lambda: subject.build_covapie_current11_formal_train_only_session_v1(
            repository_root=ROOT,
            state_root=missing_state,
            legacy_init_checkpoint=CHECKPOINT,
        )
    )
    state_copy = tmp_path / "state-copy"
    carrier, decision = _copy_state_authorities(state_copy)
    carrier.write_bytes(carrier.read_bytes() + b"drift")
    _assert_formal_error(
        lambda: subject.build_covapie_current11_formal_train_only_session_v1(
            repository_root=ROOT,
            state_root=state_copy,
            legacy_init_checkpoint=CHECKPOINT,
        )
    )
    carrier, decision = _copy_state_authorities(state_copy)
    decision.chmod(0o600)
    _assert_formal_error(
        lambda: subject.build_covapie_current11_formal_train_only_session_v1(
            repository_root=ROOT,
            state_root=state_copy,
            legacy_init_checkpoint=CHECKPOINT,
        )
    )
    carrier, decision = _copy_state_authorities(state_copy)
    decision.write_bytes(decision.read_bytes() + b"drift")
    _assert_formal_error(
        lambda: subject.build_covapie_current11_formal_train_only_session_v1(
            repository_root=ROOT,
            state_root=state_copy,
            legacy_init_checkpoint=CHECKPOINT,
        )
    )


@pytest.mark.parametrize("drift", ("sample_count", "sample_order", "feature_width"))
def test_formal_carrier_structural_drift_fails_preflight(
    monkeypatch, tmp_path, drift,
) -> None:
    state_copy = tmp_path / drift
    carrier, unused_decision = _copy_state_authorities(state_copy)
    del unused_decision
    with np.load(carrier, allow_pickle=False) as source:
        arrays = {name: source[name] for name in source.files}
    if drift == "sample_count":
        arrays["names"] = arrays["names"][:-1]
        arrays["receptors"] = arrays["receptors"][:-1]
    elif drift == "sample_order":
        arrays["names"] = arrays["names"].copy()
        arrays["names"][[0, 1]] = arrays["names"][[1, 0]]
    else:
        arrays["lig_one_hot"] = arrays["lig_one_hot"][:, :9]
    np.savez(carrier, **arrays)
    carrier.chmod(0o644)
    digest = hashlib.sha256(carrier.read_bytes()).hexdigest()
    monkeypatch.setattr(subject, "FORMAL_CARRIER_SHA256_V1", digest)
    _assert_formal_error(
        lambda: subject.build_covapie_current11_formal_train_only_session_v1(
            repository_root=ROOT,
            state_root=state_copy,
            legacy_init_checkpoint=CHECKPOINT,
        )
    )


def test_wrong_dataset_info_channel_order_fails_preflight(monkeypatch) -> None:
    dataset_info = copy.deepcopy(constants.dataset_params["crossdock"])
    dataset_info["atom_encoder"] = dict(dataset_info["atom_encoder"])
    dataset_info["atom_encoder"]["C"] = 1
    dataset_info["atom_encoder"]["N"] = 0
    monkeypatch.setitem(constants.dataset_params, "crossdock", dataset_info)
    _assert_formal_error(
        lambda: subject.build_covapie_current11_formal_train_only_session_v1(
            repository_root=ROOT,
            state_root=STATE,
            legacy_init_checkpoint=CHECKPOINT,
        )
    )


def test_cli_surface_resume_rejection_and_fit_ckpt_none(monkeypatch) -> None:
    actions = {
        action.dest for action in cli._parser()._actions if action.dest != "help"
    }
    assert actions == {
        "repository_root", "state_root", "legacy_init_checkpoint"
    }
    completed = subprocess.run(
        (
            sys.executable,
            str(ROOT / "train_covapie_current11_v1.py"),
            "--repository-root", str(ROOT),
            "--state-root", str(STATE),
            "--legacy-init-checkpoint", str(CHECKPOINT),
            "--resume", str(CHECKPOINT),
        ),
        cwd=ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": ".:src"},
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    assert completed.returncode == 2
    assert "unrecognized arguments: --resume" in completed.stderr

    calls = []

    class FakeTrainer:
        def fit(self, **kwargs):
            calls.append(kwargs)

    fake_model = object()
    fake_session = SimpleNamespace(model=fake_model, trainer=FakeTrainer())
    monkeypatch.setattr(
        subject,
        "build_covapie_current11_formal_train_only_session_v1",
        lambda **kwargs: fake_session,
    )
    cli.main((
        "--repository-root", str(ROOT),
        "--state-root", str(STATE),
        "--legacy-init-checkpoint", str(CHECKPOINT),
    ))
    assert calls == [{"model": fake_model, "ckpt_path": None}]


def test_product_sources_have_no_git_runtime_or_historical_train_import() -> None:
    formal_source = Path(subject.__file__).read_text(encoding="utf-8")
    cli_source = (ROOT / "train_covapie_current11_v1.py").read_text(
        encoding="utf-8"
    )
    assert "import subprocess" not in formal_source
    assert "git rev-parse" not in formal_source
    assert "git status" not in formal_source
    assert "strict" + "=False" not in formal_source
    assert "from train import" not in cli_source
    assert "import train" not in cli_source
    assert "ckpt_path=None" in cli_source
