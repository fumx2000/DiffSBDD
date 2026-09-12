"""Opt-in real-checkpoint Batch001 train5 forward/replay validation V1.

Collection and ordinary test execution do not deserialize the real checkpoint,
instantiate the model, or run a model forward.  The real path is guarded by
``COVAPIE_RUN_BATCH001_CHECKPOINT_FORWARD_NO_UPDATE=1``.
"""

from __future__ import annotations

import ast
import contextlib
from dataclasses import fields, is_dataclass
import hashlib
import inspect
import io
import math
import os
from pathlib import Path
import stat
import textwrap
from typing import Iterator
from unittest import mock

import pytest


TASK_ID_V1 = "validate_covapie_batch001_checkpoint_forward_no_update_v1"
REAL_FORWARD_OPT_IN_V1 = (
    "COVAPIE_RUN_BATCH001_CHECKPOINT_FORWARD_NO_UPDATE"
)
EXPECTED_CHECKPOINT_SIZE_BYTES_V1 = 17_861_341
EXPECTED_CHECKPOINT_SHA256_V1 = (
    "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
)
EXPECTED_EPOCH0_TASK_IDS_V1 = (4, 4, 2, 0, 4)
DETERMINISM_ABSOLUTE_TOLERANCE_V1 = 1.0e-7
DETERMINISM_RELATIVE_TOLERANCE_V1 = 1.0e-7

ROOT = Path(__file__).resolve().parents[1]
STATE_ROOT = ROOT.parent / "covapie-state"
CACHE_ROOT = STATE_ROOT / "bulk-multisource-cys-sg-v1/rcsb"

# Fixed expectations for directly consumed sources outside the adapter's own
# published source-binding inventory.  They are deliberately not discovered
# and accepted from the current working tree at runtime.
ADDITIONAL_BOUND_SOURCE_SHA256_V1 = (
    (
        "src/covalent_ext/covapie_batch001_hidden_post_forward_adapter_v1.py",
        "a1830928e1784214980ae0c8bdad761802dd46c055c7335be0e7ee31005cd971",
    ),
    (
        "src/covalent_ext/covapie_current11_checkpoint_migration_v1.py",
        "fc36fb23844e6e5d2be2e1e43fcd0afe580d8b86faacca31bd69b8fe70f75ef3",
    ),
    (
        "src/covalent_ext/"
        "covapie_current11_checkpoint_migration_and_real_one_batch_train_path_smoke_v1.py",
        "e92d68fc7126eb2c3e20341ad1a3ae3dd48509533761694c482edca01d70df61",
    ),
    (
        "src/covalent_ext/checkpoint_compatible_model_instantiation.py",
        "dfd9957465460f66bc08ac12c264040fae0e2a300eb7359929c780dfa85d3024",
    ),
    (
        "src/covalent_ext/diffsbdd_model_instantiation.py",
        "5bc98bad19bad27a4260ce01d68194fbfe46096bd3955b7ff5e5efa4c70d5613",
    ),
    (
        "configs/crossdock_fullatom_joint.yml",
        "155ac1b9dba8af71946e1f4e17ca9176bd05acba0a6132e50b6929f2dbf3b0ea",
    ),
    (
        "data/derived/covalent_small/"
        "checkpoint_original_config_instantiation_design_v0/"
        "checkpoint_original_config_preview.json",
        "6960de3ebb1fa408b6188dac5fdade5e2b1fc1505408ca9142b1748e305d7f4a",
    ),
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_file_identity(path: Path) -> tuple[int, str]:
    metadata = path.lstat()
    assert stat.S_ISREG(metadata.st_mode)
    assert not path.is_symlink()
    return metadata.st_size, _sha256(path)


def _verify_additional_bound_sources() -> tuple[tuple[str, str], ...]:
    observed = []
    for relative, expected in ADDITIONAL_BOUND_SOURCE_SHA256_V1:
        size, actual = _safe_file_identity(ROOT / relative)
        assert size > 0
        assert actual == expected, relative
        observed.append((relative, actual))
    return tuple(observed)


def _evidence(message: str) -> None:
    print(f"COVAPIE_EVIDENCE {message}", flush=True)


def _snapshot_named_tensors(
    named_tensors: Iterator[tuple[str, object]],
) -> dict[str, object]:
    return {
        name: value.detach().clone()
        for name, value in named_tensors
    }


def _assert_snapshot_unchanged(
    snapshot: dict[str, object], current: Iterator[tuple[str, object]]
) -> None:
    current_map = dict(current)
    assert tuple(current_map) == tuple(snapshot)
    for name, before in snapshot.items():
        assert before.device.type == "cpu"
        assert current_map[name].device.type == "cpu"
        assert current_map[name].dtype == before.dtype
        assert current_map[name].shape == before.shape
        assert current_map[name].detach().equal(before), name


def _model_state_fingerprint(
    parameters: dict[str, object], buffers: dict[str, object]
) -> str:
    import torch

    digest = hashlib.sha256()
    for category, values in (("parameter", parameters), ("buffer", buffers)):
        for name in sorted(values):
            tensor = values[name].detach().contiguous().cpu()
            digest.update(category.encode("ascii"))
            digest.update(name.encode("utf-8"))
            digest.update(str(tensor.dtype).encode("ascii"))
            digest.update(str(tuple(tensor.shape)).encode("ascii"))
            digest.update(tensor.view(-1).view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def _all_gradients_none(model: object) -> bool:
    return all(parameter.grad is None for parameter in model.parameters())


def _function_attribute_names(function: object) -> frozenset[str]:
    tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
    return frozenset(
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    )


def _output_tensor_items(value: object, prefix: str = "") -> tuple[tuple[str, object], ...]:
    import torch

    if isinstance(value, torch.Tensor):
        return ((prefix, value),)
    if is_dataclass(value):
        result = []
        for field in fields(value):
            child = getattr(value, field.name)
            child_prefix = f"{prefix}.{field.name}" if prefix else field.name
            result.extend(_output_tensor_items(child, child_prefix))
        return tuple(result)
    return ()


def _compare_replayed_outputs(first: object, second: object) -> float:
    import torch

    first_items = dict(_output_tensor_items(first))
    second_items = dict(_output_tensor_items(second))
    assert tuple(first_items) == tuple(second_items)
    maximum = 0.0
    for name, left in first_items.items():
        right = second_items[name]
        assert left.dtype == right.dtype
        assert left.shape == right.shape
        torch.testing.assert_close(
            left,
            right,
            atol=DETERMINISM_ABSOLUTE_TOLERANCE_V1,
            rtol=DETERMINISM_RELATIVE_TOLERANCE_V1,
            equal_nan=True,
            msg=lambda message: f"{name}: {message}",
        )
        if torch.is_floating_point(left) and left.numel():
            finite = torch.isfinite(left) & torch.isfinite(right)
            if bool(finite.any().item()):
                maximum = max(
                    maximum,
                    float((left[finite] - right[finite]).abs().max().item()),
                )
    return maximum


def _loss_values(output: object) -> tuple[tuple[str, float], ...]:
    losses = output.loss_output
    return (
        ("base", float(losses.loss_base_diffusion.detach().item())),
        ("pair", float(losses.loss_covalent_pair_prediction.detach().item())),
        ("geometry", float(losses.loss_pre_post_geometry.detach().item())),
        ("contrastive", float(losses.loss_covalent_pair_contrastive.detach().item())),
        ("total", float(losses.loss_total.detach().item())),
    )


def _loss_counts(output: object) -> tuple[tuple[str, int], ...]:
    losses = output.loss_output
    return (
        ("base", losses.base_diffusion_valid_sample_count),
        ("pair", losses.covalent_pair_prediction_valid_sample_count),
        ("geometry", losses.pre_post_geometry_valid_sample_count),
        ("contrastive", losses.covalent_pair_contrastive_valid_sample_count),
    )


def _validate_and_emit_forward_measurement(
    *, round_index: int, output: object, carrier: object, diffusion_steps: int,
    loss_weights: object
) -> None:
    import torch

    timesteps = output.diffusion_trace.diffusion_timestep_int
    values = dict(_loss_values(output))
    counts = dict(_loss_counts(output))
    active = carrier.supervision.ligand_active_diffusion_loss_mask[:, 0]
    assert timesteps.dtype == torch.long
    assert tuple(timesteps.shape) == (5,)
    assert bool(((timesteps >= 0) & (timesteps <= diffusion_steps)).all().item())
    assert all(math.isfinite(value) for value in values.values())
    assert counts == {
        "base": 5,
        "pair": 5,
        "geometry": 5,
        "contrastive": 5,
    }
    assert bool(torch.isfinite(
        output.model_output.diffusion_epsilon_prediction_ligand[active]
    ).all().item())
    assert not any(
        tensor.requires_grad for _name, tensor in _output_tensor_items(output)
    )
    _evidence(
        f"forward_{round_index}_measurements=PASS "
        f"timesteps={tuple(timesteps.tolist())} "
        f"raw_losses={values} valid_counts={counts} "
        f"hidden_post_epoch0={counts['geometry']} "
        f"loss_weights={loss_weights} active_predictions_finite=true "
        "output_requires_grad=false"
    )


def _assert_centering_and_fixed_node_contract(
    *, model: object, carrier: object, transported: tuple[dict[str, object], dict[str, object]], output: object
) -> None:
    import torch

    ligand, pocket = transported
    ligand_copy = {
        name: value.clone() if isinstance(value, torch.Tensor) else value
        for name, value in ligand.items()
    }
    pocket_copy = {
        name: value.clone() if isinstance(value, torch.Tensor) else value
        for name, value in pocket.items()
    }
    normalized_ligand, normalized_pocket = model.ddpm.normalize(
        ligand_copy, pocket_copy
    )
    supervision = carrier.supervision
    ligand_mask = ligand["mask"]
    pocket_mask = pocket["mask"]
    generation = supervision.ligand_base_generation_mask
    fixed = supervision.ligand_base_fixed_mask[:, 0]
    trace = output.diffusion_trace
    expected_clean_ligand_xh = torch.cat((
        normalized_ligand["x"].clone(),
        normalized_ligand["one_hot"].clone(),
    ), dim=1)
    expected_pocket_xh = torch.cat((
        normalized_pocket["x"].clone(),
        normalized_pocket["one_hot"].clone(),
    ), dim=1)
    for sample, task_id in enumerate(
        supervision.canonical_task_id.tolist()
    ):
        sample_ligand = ligand_mask == sample
        sample_pocket = pocket_mask == sample
        if task_id == 4:
            reference = normalized_ligand["x"][sample_ligand].mean(0)
        else:
            reference = normalized_ligand["x"][sample_ligand & fixed].mean(0)
        expected_clean_ligand_xh[sample_ligand, :3] -= reference
        expected_pocket_xh[sample_pocket, :3] -= reference
    torch.testing.assert_close(
        trace.clean_centered_ligand_xh, expected_clean_ligand_xh
    )

    t = (
        trace.diffusion_timestep_int.to(dtype=expected_clean_ligand_xh.dtype)
        .unsqueeze(1)
        / model.ddpm.T
    )
    gamma_t = model.ddpm.inflate_batch_array(
        model.ddpm.gamma(t), expected_clean_ligand_xh
    )
    alpha_t = model.ddpm.alpha(gamma_t, expected_clean_ligand_xh)
    sigma_t = model.ddpm.sigma(gamma_t, expected_clean_ligand_xh)
    noised_generated = (
        alpha_t[ligand_mask] * expected_clean_ligand_xh
        + sigma_t[ligand_mask] * trace.sampled_epsilon_ligand
    )
    expected_noised_ligand_xh = torch.where(
        generation, noised_generated, expected_clean_ligand_xh
    )
    for sample, task_id in enumerate(
        supervision.canonical_task_id.tolist()
    ):
        if task_id != 4:
            continue
        sample_ligand = ligand_mask == sample
        sample_pocket = pocket_mask == sample
        post_noise_translation = expected_noised_ligand_xh[
            sample_ligand, :3
        ].mean(0)
        expected_noised_ligand_xh[
            sample_ligand, :3
        ] -= post_noise_translation
        expected_pocket_xh[sample_pocket, :3] -= post_noise_translation
    torch.testing.assert_close(
        trace.noised_ligand_xh, expected_noised_ligand_xh
    )
    torch.testing.assert_close(
        trace.clean_centered_pocket_xh, expected_pocket_xh
    )

    fixed_column = supervision.ligand_base_fixed_mask
    assert trace.ligand_coordinate_update_mask.equal(generation)
    assert trace.sampled_epsilon_ligand[fixed].equal(
        torch.zeros_like(trace.sampled_epsilon_ligand[fixed])
    )
    assert trace.noised_ligand_xh[fixed].equal(
        trace.clean_centered_ligand_xh[fixed]
    )
    assert trace.denoised_ligand_xh[fixed].equal(
        trace.clean_centered_ligand_xh[fixed]
    )
    assert not bool((generation & fixed_column).any().item())
    assert bool((generation | fixed_column).all().item())


def _install_no_training_tripwires(
    stack: contextlib.ExitStack, *, model: object
) -> list[str]:
    import pytorch_lightning as pl
    import torch

    calls: list[str] = []

    def forbidden(name: str):
        def tripwire(*_args: object, **_kwargs: object) -> None:
            calls.append(name)
            raise AssertionError(f"forbidden operation invoked: {name}")

        return tripwire

    direct_targets = (
        (torch.Tensor, "backward", "Tensor.backward"),
        (torch.autograd, "backward", "torch.autograd.backward"),
        (torch.autograd, "grad", "torch.autograd.grad"),
        (torch, "save", "torch.save"),
        (pl.Trainer, "__init__", "Trainer.__init__"),
        (pl.Trainer, "fit", "Trainer.fit"),
        (pl.Trainer, "validate", "Trainer.validate"),
        (pl.Trainer, "test", "Trainer.test"),
        (pl.Trainer, "predict", "Trainer.predict"),
        (pl.Trainer, "save_checkpoint", "Trainer.save_checkpoint"),
        (pl.LightningModule, "load_from_checkpoint", "load_from_checkpoint"),
        (model, "configure_optimizers", "model.configure_optimizers"),
        (model, "training_step", "model.training_step"),
        (model, "validation_step", "model.validation_step"),
        (model, "test_step", "model.test_step"),
    )
    for owner, attribute, name in direct_targets:
        stack.enter_context(
            mock.patch.object(owner, attribute, new=forbidden(name))
        )

    optimizer_classes = {
        value
        for value in vars(torch.optim).values()
        if isinstance(value, type)
        and issubclass(value, torch.optim.Optimizer)
    }
    for optimizer_class in optimizer_classes:
        if "__init__" in optimizer_class.__dict__:
            stack.enter_context(mock.patch.object(
                optimizer_class,
                "__init__",
                new=forbidden(f"{optimizer_class.__name__}.__init__"),
            ))
        if "step" in optimizer_class.__dict__:
            stack.enter_context(mock.patch.object(
                optimizer_class,
                "step",
                new=forbidden(f"{optimizer_class.__name__}.step"),
            ))
    return calls


def _instantiate_exact_adapter(
    *, checkpoint: dict[str, object], runtime_root: Path
) -> object:
    import constants
    import torch
    from covalent_ext import (
        checkpoint_compatible_model_instantiation as compatible_owner,
    )
    from covalent_ext import (
        covapie_batch001_hidden_post_forward_adapter_v1 as adapter,
    )
    from covalent_ext import (
        covapie_current11_checkpoint_migration_and_real_one_batch_train_path_smoke_v1
        as constructor_owner,
    )

    legacy = checkpoint["legacy_constructor"]
    preview_result = compatible_owner.load_config_preview_v0(
        ROOT / compatible_owner.CONFIG_PREVIEW_PATH
    )
    assert preview_result["config_preview_loaded"] is True
    compatible = compatible_owner.build_checkpoint_compatible_config_v0(
        preview_result["preview"], ROOT / compatible_owner.BEST_CONFIG_CANDIDATE_PATH
    )
    assert compatible["compatible_config_built"] is True
    config = compatible_owner._constructor_config_from_compatible_config(
        compatible,
        constructor_owner._DATASET_NAME_V1,
        "cpu",
        node_histogram=legacy["node_histogram"],
    )

    # Network, diffusion, normalization, and conditioning-shaping fields come
    # from and are checked against the validated legacy constructor.  Only the
    # published helper's CPU/non-training choices and local paths/batch size
    # differ here.
    assert config["egnn_params"] == dict(legacy["egnn_params"], device="cpu")
    assert config["diffusion_params"] == legacy["diffusion_params"]
    assert config["eval_params"] == legacy["eval_params"]
    assert config["loss_params"] == legacy["loss_params"]
    for key in (
        "lr",
        "num_workers",
        "augment_noise",
        "augment_rotation",
        "eval_epochs",
        "visualize_sample_epoch",
        "visualize_chain_epoch",
        "auxiliary_loss",
        "mode",
        "pocket_representation",
        "virtual_nodes",
    ):
        assert config[key] == legacy[key], key
    assert config["node_histogram"] == legacy["node_histogram"]
    assert config["clip_grad"] is False
    assert legacy["clip_grad"] is True

    legacy_setup = runtime_root / "legacy_setup_data"
    legacy_setup.mkdir(mode=0o700)
    config.update({
        "outdir": runtime_root / "model_output_not_persisted",
        "datadir": str(legacy_setup),
        "batch_size": 5,
    })
    kwargs = constructor_owner._constructor_kwargs(config)
    kwargs.update({
        "target_residue_atom_conditioning": True,
        "covapie_current11_task2_runtime_enabled": True,
        "covapie_repository_root": str(ROOT),
        "covapie_state_root": str(STATE_ROOT),
        "covapie_current11_training_enabled": True,
        "covapie_current11_task_schedule_seed": 0,
        "covapie_current11_pair_contrastive_temperature": 1.0,
        "covapie_batch001_hidden_post_forward_enabled": True,
    })
    torch.random.default_generator.manual_seed(20260821)
    dataset_name = config["dataset"]
    previous = constants.dataset_params.get(dataset_name)
    constants.dataset_params[dataset_name] = (
        compatible_owner._temporary_10d_dataset_info()
    )
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            model = adapter.CovapieBatch001HiddenPostForwardLigandPocketDDPMV1(
                **kwargs
            )
    finally:
        if previous is None:
            constants.dataset_params.pop(dataset_name, None)
        else:
            constants.dataset_params[dataset_name] = previous
    return model.to(torch.device("cpu"))


def test_checkpoint_identity_mismatch_rejects_before_deserialization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A mismatched candidate cannot reach ``torch.load``."""

    from covalent_ext import covapie_current11_checkpoint_migration_v1 as migration

    candidate = tmp_path / "identity-mismatch.ckpt"
    candidate.write_bytes(b"not-the-published-checkpoint")
    deserialization_calls = 0

    def forbidden_load(*_args: object, **_kwargs: object) -> None:
        nonlocal deserialization_calls
        deserialization_calls += 1
        raise AssertionError("mismatched checkpoint reached torch.load")

    monkeypatch.setattr(migration.torch, "load", forbidden_load)
    with pytest.raises(
        ValueError,
        match="^COVAPIE_CURRENT11_CHECKPOINT_MIGRATION_V1_ERROR$",
    ):
        migration.load_covapie_current11_legacy_checkpoint_v1(
            checkpoint_path=candidate
        )
    assert deserialization_calls == 0


def test_real_checkpoint_train5_forward_and_same_rng_replay_no_update(
    tmp_path: Path,
) -> None:
    """Run exactly two same-model train5 forwards when explicitly enabled."""

    if os.environ.get(REAL_FORWARD_OPT_IN_V1) != "1":
        pytest.skip(f"set {REAL_FORWARD_OPT_IN_V1}=1 for real checkpoint forward")
    _evidence(
        "opt_in=1 continuation_run=START "
        "prior_lifecycle_full_forward_count=2 this_run_budget=2"
    )

    import torch
    from covalent_ext import (
        covapie_batch001_13event_model_usable_split_materialization_and_activation_boundary_v1
        as activation_owner,
    )
    from covalent_ext import (
        covapie_batch001_feature_post_use_preflight_v1 as preflight_owner,
    )
    from covalent_ext import (
        covapie_batch001_hidden_post_forward_adapter_v1 as adapter,
    )
    from covalent_ext import (
        covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1
        as checkpoint_locator,
    )
    from covalent_ext import (
        covapie_current11_checkpoint_migration_v1 as migration_owner,
    )
    from covalent_ext import (
        covapie_current11_training_lightning_module_v1 as training_owner,
    )
    from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (
        CovapieCurrent11LossWeightsV1,
    )

    adapter_bindings = (
        adapter.verify_covapie_batch001_hidden_post_forward_adapter_sources_v1(
            repository_root=ROOT
        )
    )
    additional_bindings = _verify_additional_bound_sources()
    fixed_source_identity_before = adapter_bindings + additional_bindings

    checkpoint_path = ROOT / checkpoint_locator.CHECKPOINT_RELATIVE_PATH_V1
    checkpoint_size, checkpoint_sha = _safe_file_identity(checkpoint_path)
    assert checkpoint_size == EXPECTED_CHECKPOINT_SIZE_BYTES_V1
    assert checkpoint_sha == EXPECTED_CHECKPOINT_SHA256_V1
    assert checkpoint_size == (
        migration_owner.COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SIZE_BYTES_V1
    )
    assert checkpoint_sha == (
        migration_owner.COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SHA256_V1
    )
    _evidence(
        "checkpoint_identity=PASS "
        f"path={checkpoint_locator.CHECKPOINT_RELATIVE_PATH_V1} "
        f"bytes={checkpoint_size} sha256={checkpoint_sha} "
        "deserialized=false"
    )

    with contextlib.ExitStack() as safety_stack:
        # Install global no-training guards before deserialization/model
        # construction.  The sole exact checkpoint loader remains permitted.
        class _ModelTripwirePlaceholder:
            def configure_optimizers(self):
                raise AssertionError

            def training_step(self):
                raise AssertionError

            def validation_step(self):
                raise AssertionError

            def test_step(self):
                raise AssertionError

        placeholder = _ModelTripwirePlaceholder()
        global_tripwire_calls = _install_no_training_tripwires(
            safety_stack, model=placeholder
        )
        _evidence(
            "no_training_tripwires=INSTALLED "
            "backward=true autograd_grad=true optimizer=true trainer=true "
            "checkpoint_save=true cleanup=not_reached"
        )
        checkpoint = migration_owner.load_covapie_current11_legacy_checkpoint_v1(
            checkpoint_path=checkpoint_path
        )
        assert checkpoint["checkpoint_size_bytes"] == checkpoint_size
        assert checkpoint["checkpoint_sha256"] == checkpoint_sha
        checkpoint_state = checkpoint["state_dict"]
        assert checkpoint["checkpoint_state_dict_key_count"] == len(checkpoint_state)
        _evidence(
            "checkpoint_load=PASS "
            f"payload_type={checkpoint['checkpoint_payload_type']} "
            f"legacy_state_keys={len(checkpoint_state)}"
        )

        model = _instantiate_exact_adapter(
            checkpoint=checkpoint, runtime_root=tmp_path
        )
        # Add instance-specific guards without relaxing the already installed
        # global tripwires.
        model_tripwire_calls = _install_no_training_tripwires(
            safety_stack, model=model
        )
        migration = (
            migration_owner.migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
                model=model,
                checkpoint_state_dict=checkpoint_state,
            )
        )

        migrated_state = model.state_dict()
        target_keys = set(migrated_state)
        checkpoint_keys = set(checkpoint_state)
        shared_keys = target_keys & checkpoint_keys
        target_only = target_keys - checkpoint_keys
        assert migration["checkpoint_key_count"] == len(checkpoint_keys)
        assert migration["target_model_key_count"] == len(target_keys)
        assert migration["shared_key_count"] == len(shared_keys)
        assert migration["target_only_key_count"] == len(target_only)
        assert migration["checkpoint_only_key_count"] == 0
        assert migration["shared_shape_mismatch_count"] == 0
        assert migration["shared_checkpoint_tensor_equality_count"] == len(shared_keys)
        assert migration["migration_missing_keys"] == ()
        assert migration["migration_unexpected_keys"] == ()
        assert migration["full_target_strict_load"] is True
        assert set(migration["target_only_exact_keys"]) == set(
            migration_owner.LEGACY_ALLOWED_NEW_EXACT_KEYS_V1
        )
        assert set(migration["target_only_auxiliary_keys"]) == {
            key
            for key in target_only
            if key.startswith(migration_owner.LEGACY_ALLOWED_NEW_PREFIXES_V1)
        }
        assert target_only == (
            set(migration["target_only_exact_keys"])
            | set(migration["target_only_auxiliary_keys"])
        )
        for key in shared_keys:
            assert migrated_state[key].detach().cpu().equal(
                checkpoint_state[key].detach().cpu()
            ), key
        zero_delta_tensors = (
            model.ddpm.dynamics.target_residue_atom_condition_embedding,
            model.covapie_current11_auxiliary_model_v1.role_embedding.weight,
            model.covapie_current11_auxiliary_model_v1.task_embedding.weight,
            model.covapie_current11_auxiliary_model_v1.generation_state_embedding.weight,
            model.covapie_current11_auxiliary_model_v1.seed_indicator_embedding.weight,
            model.covapie_current11_auxiliary_model_v1.anchor_distance_encoder[-1].weight,
            model.covapie_current11_auxiliary_model_v1.anchor_distance_encoder[-1].bias,
        )
        assert all(tensor.detach().equal(torch.zeros_like(tensor)) for tensor in zero_delta_tensors)
        assert migration["target_residue_embedding_preserved_zero_after_migration"] is True
        assert migration["auxiliary_zero_delta_initialization_preserved"] is True
        _evidence(
            "checkpoint_migration=PASS "
            f"checkpoint_keys={migration['checkpoint_key_count']} "
            f"target_keys={migration['target_model_key_count']} "
            f"shared_keys={migration['shared_key_count']} "
            f"shared_equal={migration['shared_checkpoint_tensor_equality_count']} "
            f"target_only={migration['target_only_key_count']} "
            f"new_exact={len(migration['target_only_exact_keys'])} "
            f"new_auxiliary={len(migration['target_only_auxiliary_keys'])} "
            f"checkpoint_only={migration['checkpoint_only_key_count']} "
            f"shape_mismatch={migration['shared_shape_mismatch_count']} "
            "strict=true zero_delta_initialization=true"
        )

        dynamics = model.ddpm.dynamics
        assert type(model) is adapter.CovapieBatch001HiddenPostForwardLigandPocketDDPMV1
        assert model.device == torch.device("cpu")
        assert model.mode == "pocket_conditioning"
        assert model.pocket_representation == "full-atom"
        assert model.atom_nf == 10
        assert model.aa_nf == 10
        assert model.virtual_nodes is False
        assert model.auxiliary_loss is False
        assert model.ddpm.loss_type == "l2"
        assert model.ddpm.T == 500
        assert model.ddpm.norm_values == [1, 4]
        assert dynamics.target_residue_atom_conditioning is True
        assert dynamics.egnn.hidden_nf == 128
        assert dynamics.egnn.n_layers == 5
        assert model.covapie_current11_auxiliary_model_v1.joint_nf == 32
        assert model._trainer is None
        assert model.current_epoch == 0
        model.train()
        assert model.training is True
        assert model.ddpm.training is True
        _evidence(
            "model_configuration=PASS "
            f"class={type(model).__name__} mode={model.mode} "
            f"device={model.device} atom_nf={model.atom_nf} aa_nf={model.aa_nf} "
            f"diffusion_steps={model.ddpm.T} normalization={model.ddpm.norm_values} "
            "full_atom=true target_residue_conditioning=true "
            "virtual_nodes=false trainer_attached=false current_epoch=0 training_mode=true"
        )

        parameters_after_loading = _snapshot_named_tensors(
            model.named_parameters()
        )
        buffers_after_loading = _snapshot_named_tensors(model.named_buffers())
        state_fingerprint_after_loading = _model_state_fingerprint(
            parameters_after_loading, buffers_after_loading
        )
        assert _all_gradients_none(model)

        carrier = activation_owner.build_covapie_batch001_model_usable_split_batch_v1(
            split="train",
            epoch=0,
            task_schedule_seed=0,
            repository_root=ROOT,
            cache_root=CACHE_ROOT,
        )
        carrier_fingerprint_before, preflight_rows = (
            preflight_owner.audit_covapie_batch001_feature_post_use_carrier_v1(
                carrier
            )
        )
        assert carrier.formal_split == "train"
        assert carrier.epoch == 0
        assert carrier.task_schedule_seed == 0
        assert carrier.training_scheduled_task_ids == EXPECTED_EPOCH0_TASK_IDS_V1
        assert carrier.preview_tensorization_task_ids == EXPECTED_EPOCH0_TASK_IDS_V1
        assert tuple(carrier.supervision.canonical_task_id.tolist()) == (
            EXPECTED_EPOCH0_TASK_IDS_V1
        )
        assert len(carrier.sample_identities) == 5
        assert sum(row.preflight_effective_hidden_post_eligible for row in preflight_rows) == 5
        assert set(carrier.model_input_batch) == {
            "names",
            "receptors",
            "lig_coords",
            "pocket_coords",
            "lig_one_hot",
            "pocket_one_hot",
            "lig_source_row_index",
            "pocket_source_row_index",
            "lig_parser_local_index",
            "pocket_parser_local_index",
            "num_lig_atoms",
            "num_pocket_nodes",
            "lig_mask",
            "pocket_mask",
        }
        assert carrier.model_input_batch["lig_one_hot"].shape[1] == 10
        assert carrier.model_input_batch["pocket_one_hot"].shape[1] == 10
        generation_counts = tuple(
            int(carrier.supervision.ligand_base_generation_mask[
                carrier.model_input_batch["lig_mask"] == sample
            ].sum().item())
            for sample in range(5)
        )
        fixed_counts = tuple(
            int(carrier.supervision.ligand_base_fixed_mask[
                carrier.model_input_batch["lig_mask"] == sample
            ].sum().item())
            for sample in range(5)
        )
        _evidence(
            "train5_carrier=PASS "
            f"epoch={carrier.epoch} task_schedule_seed={carrier.task_schedule_seed} "
            f"tasks={carrier.training_scheduled_task_ids} "
            f"ligand_shape={tuple(carrier.model_input_batch['lig_coords'].shape)} "
            f"ligand_one_hot_shape={tuple(carrier.model_input_batch['lig_one_hot'].shape)} "
            f"pocket_shape={tuple(carrier.model_input_batch['pocket_coords'].shape)} "
            f"pocket_one_hot_shape={tuple(carrier.model_input_batch['pocket_one_hot'].shape)} "
            f"generated_counts={generation_counts} fixed_counts={fixed_counts} "
            f"carrier_fingerprint={carrier_fingerprint_before}"
        )

        # The pinned neural encoding functions do not read the POST target or
        # detached loss diagnostics.  The production loss is the sole consumer
        # of the POST target; receiving the supervision carrier itself is not
        # treated as proof that every field enters neural computation.
        forbidden_neural_attributes = {
            "pre_post_geometry_target_angstrom",
            "pair_prediction_per_sample_detached",
            "pre_post_geometry_per_sample_detached",
            "pair_contrastive_per_sample_detached",
        }
        role_attributes = _function_attribute_names(
            type(model.covapie_current11_auxiliary_model_v1).encode_role_mask_anchor_v1
        )
        auxiliary_attributes = _function_attribute_names(
            type(model.covapie_current11_auxiliary_model_v1).forward
        )
        assert forbidden_neural_attributes.isdisjoint(role_attributes)
        assert forbidden_neural_attributes.isdisjoint(auxiliary_attributes)

        observations: dict[str, object] = {
            "transport": [],
            "role": [],
            "bridge": [],
            "functional": [],
            "loss": [],
            "egnn_shapes": [],
            "atom_encoder_shapes": [],
            "residue_encoder_shapes": [],
            "anchor_inputs": [],
            "pair_inputs": [],
            "auxiliary_calls": 0,
        }
        observation_stack = contextlib.ExitStack()
        safety_stack.callback(observation_stack.close)

        original_transport = model.get_ligand_and_pocket
        original_role = (
            model.covapie_current11_auxiliary_model_v1.encode_role_mask_anchor_v1
        )
        original_bridge = adapter.run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1
        original_functional = training_owner.run_covapie_current11_functional_dynamics_with_hidden_v1
        original_loss = adapter.compute_covapie_current11_training_losses_v1

        def transport_spy(data: object):
            ligand, pocket = original_transport(data)
            observations["transport"].append((
                {
                    name: value.detach().clone() if isinstance(value, torch.Tensor) else value
                    for name, value in ligand.items()
                },
                {
                    name: value.detach().clone() if isinstance(value, torch.Tensor) else value
                    for name, value in pocket.items()
                },
            ))
            return ligand, pocket

        def role_spy(**kwargs: object):
            observations["role"].append({
                "supervision_identity": kwargs["supervision"] is carrier.supervision,
                "ligand_batch_index": kwargs["ligand_batch_index"].detach().clone(),
            })
            return original_role(**kwargs)

        def bridge_spy(**kwargs: object):
            observations["bridge"].append({
                "supervision_identity": kwargs["supervision"] is carrier.supervision,
                "role_shape": tuple(kwargs["role_mask_anchor_hidden_delta"].shape),
                "indicator": kwargs[
                    "pocket_target_residue_atom_condition_indicator"
                ].detach().clone(),
            })
            return original_bridge(**kwargs)

        def functional_spy(**kwargs: object):
            observations["functional"].append({
                "coordinate_update_mask": kwargs[
                    "ligand_coordinate_update_mask"
                ].detach().clone(),
                "indicator": kwargs[
                    "pocket_target_residue_atom_condition_indicator"
                ].detach().clone(),
                "ligand_xh_shape": tuple(kwargs["xh_atoms"].shape),
                "pocket_xh_shape": tuple(kwargs["xh_residues"].shape),
            })
            return original_functional(**kwargs)

        def loss_spy(**kwargs: object):
            observations["loss"].append({
                "purpose": kwargs["post_geometry_loss_purpose"],
                "supervision_identity": kwargs["supervision"] is carrier.supervision,
                "ligand_batch_shape": tuple(kwargs["ligand_batch_index"].shape),
                "pocket_batch_shape": tuple(kwargs["pocket_batch_index"].shape),
            })
            return original_loss(**kwargs)

        observation_stack.enter_context(
            mock.patch.object(model, "get_ligand_and_pocket", new=transport_spy)
        )
        observation_stack.enter_context(mock.patch.object(
            model.covapie_current11_auxiliary_model_v1,
            "encode_role_mask_anchor_v1",
            new=role_spy,
        ))
        observation_stack.enter_context(mock.patch.object(
            adapter,
            "run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1",
            new=bridge_spy,
        ))
        observation_stack.enter_context(mock.patch.object(
            training_owner,
            "run_covapie_current11_functional_dynamics_with_hidden_v1",
            new=functional_spy,
        ))
        observation_stack.enter_context(mock.patch.object(
            adapter,
            "compute_covapie_current11_training_losses_v1",
            new=loss_spy,
        ))

        def shape_hook(key: str):
            def hook(_module: object, inputs: tuple[object, ...], _output: object) -> None:
                observations[key].append(tuple(inputs[0].shape))

            return hook

        def auxiliary_hook(
            _module: object, _inputs: tuple[object, ...], _output: object
        ) -> None:
            observations["auxiliary_calls"] += 1

        hook_specs = (
            (dynamics.egnn, shape_hook("egnn_shapes")),
            (dynamics.atom_encoder, shape_hook("atom_encoder_shapes")),
            (dynamics.residue_encoder, shape_hook("residue_encoder_shapes")),
            (
                model.covapie_current11_auxiliary_model_v1.anchor_distance_encoder[0],
                shape_hook("anchor_inputs"),
            ),
            (
                model.covapie_current11_auxiliary_model_v1.pair_embedding[0],
                shape_hook("pair_inputs"),
            ),
            (model.covapie_current11_auxiliary_model_v1, auxiliary_hook),
        )
        hook_counts_before = tuple(
            len(module._forward_hooks) for module, _hook in hook_specs
        )
        for module, hook in hook_specs:
            handle = module.register_forward_hook(hook)
            observation_stack.callback(handle.remove)

        weights = model.covapie_current11_loss_weights
        assert weights == CovapieCurrent11LossWeightsV1(
            base_diffusion=1.0,
            covalent_pair_prediction=1.0,
            pre_post_geometry=0.0,
            covalent_pair_contrastive=0.1,
        )
        _evidence(f"loss_weights=PASS values={weights}")
        rng_before_first = torch.random.get_rng_state().clone()
        _evidence(
            "full_forward_1=START this_run_completed=0 "
            "lifecycle_completed=2 rng_state_saved=true"
        )
        with torch.no_grad():
            first = model(carrier)
        _evidence(
            "full_forward_1=COMPLETED this_run_completed=1 "
            "lifecycle_completed=3"
        )
        _validate_and_emit_forward_measurement(
            round_index=1,
            output=first,
            carrier=carrier,
            diffusion_steps=model.ddpm.T,
            loss_weights=weights,
        )
        _assert_snapshot_unchanged(
            parameters_after_loading, model.named_parameters()
        )
        _assert_snapshot_unchanged(buffers_after_loading, model.named_buffers())
        assert _all_gradients_none(model)
        carrier_fingerprint_after_first, _rows = (
            preflight_owner.audit_covapie_batch001_feature_post_use_carrier_v1(
                carrier
            )
        )
        assert carrier_fingerprint_after_first == carrier_fingerprint_before
        _evidence(
            "post_forward_1_invariance=PASS parameters_unchanged=true "
            "buffers_unchanged=true gradients_none=true carrier_unchanged=true"
        )

        # The only restored state is the CPU random-generator state.  Model
        # parameters/buffers and the carrier are neither reloaded nor restored.
        torch.random.set_rng_state(rng_before_first)
        _evidence(
            "full_forward_2=START this_run_completed=1 "
            "lifecycle_completed=3 cpu_rng_restored=true "
            "model_or_buffer_reloaded=false"
        )
        with torch.no_grad():
            second = model(carrier)
        _evidence(
            "full_forward_2=COMPLETED this_run_completed=2 "
            "lifecycle_completed=4"
        )
        _validate_and_emit_forward_measurement(
            round_index=2,
            output=second,
            carrier=carrier,
            diffusion_steps=model.ddpm.T,
            loss_weights=weights,
        )
        _assert_snapshot_unchanged(
            parameters_after_loading, model.named_parameters()
        )
        _assert_snapshot_unchanged(buffers_after_loading, model.named_buffers())
        assert _all_gradients_none(model)
        carrier_fingerprint_after_second, _rows = (
            preflight_owner.audit_covapie_batch001_feature_post_use_carrier_v1(
                carrier
            )
        )
        assert carrier_fingerprint_after_second == carrier_fingerprint_before
        _evidence(
            "post_forward_2_invariance=PASS parameters_unchanged=true "
            "buffers_unchanged=true gradients_none=true carrier_unchanged=true"
        )
        replay_maximum_difference = _compare_replayed_outputs(first, second)
        _evidence(
            "rng_replay_comparison=PASS "
            f"max_abs_difference={replay_maximum_difference} "
            f"atol={DETERMINISM_ABSOLUTE_TOLERANCE_V1} "
            f"rtol={DETERMINISM_RELATIVE_TOLERANCE_V1}"
        )

        assert first.supervision is carrier.supervision
        assert second.supervision is carrier.supervision
        assert first.diffusion_trace.diffusion_timestep_int.equal(
            second.diffusion_trace.diffusion_timestep_int
        )
        assert bool(torch.isfinite(
            first.model_output.diffusion_epsilon_prediction_ligand[
                carrier.supervision.ligand_active_diffusion_loss_mask[:, 0]
            ]
        ).all().item())
        assert all(math.isfinite(value) for _name, value in _loss_values(first))
        assert dict(_loss_counts(first)) == {
            "base": 5,
            "pair": 5,
            "geometry": 5,
            "contrastive": 5,
        }
        assert dict(_loss_counts(second)) == dict(_loss_counts(first))
        assert weights == CovapieCurrent11LossWeightsV1(
            base_diffusion=1.0,
            covalent_pair_prediction=1.0,
            pre_post_geometry=0.0,
            covalent_pair_contrastive=0.1,
        )
        assert first.loss_output.loss_pre_post_geometry.detach().isfinite()
        assert first.loss_output.pre_post_geometry_valid_sample_count == 5
        assert not any(
            tensor.requires_grad
            for _name, tensor in _output_tensor_items(first)
        )

        assert len(observations["transport"]) == 2
        assert len(observations["role"]) == 2
        assert len(observations["bridge"]) == 2
        assert len(observations["functional"]) == 2
        assert len(observations["loss"]) == 2
        assert observations["auxiliary_calls"] == 2
        assert observations["egnn_shapes"] == [(693, 33), (693, 33)]
        assert observations["atom_encoder_shapes"] == [(115, 10), (115, 10)]
        assert observations["residue_encoder_shapes"] == [(578, 10), (578, 10)]
        assert observations["pair_inputs"] == [
            (len(carrier.supervision.pair_candidate_batch_index), 129)
        ] * 2
        expected_anchor_rows = int((
            carrier.supervision.ligand_anchor_distance_valid
            & carrier.supervision.ligand_base_fixed_mask
            & ~carrier.supervision.ligand_base_generation_mask
        ).sum().item())
        assert observations["anchor_inputs"] == [
            (expected_anchor_rows, 1),
            (expected_anchor_rows, 1),
        ]
        for record in observations["role"]:
            assert record["supervision_identity"] is True
            assert record["ligand_batch_index"].equal(
                carrier.model_input_batch["lig_mask"]
            )
        for record in observations["bridge"]:
            assert record["supervision_identity"] is True
            assert record["role_shape"] == (115, 32)
            assert record["indicator"].equal(
                carrier.supervision.target_residue_reactive_atom_mask[:, 0]
            )
        for record in observations["functional"]:
            assert record["coordinate_update_mask"].equal(
                carrier.supervision.ligand_base_generation_mask
            )
            assert record["indicator"].equal(
                carrier.supervision.target_residue_reactive_atom_mask[:, 0]
            )
            assert record["ligand_xh_shape"] == (115, 13)
            assert record["pocket_xh_shape"] == (578, 13)
        for record in observations["loss"]:
            assert record == {
                "purpose": "independent_hidden_post_distance_v1",
                "supervision_identity": True,
                "ligand_batch_shape": (115,),
                "pocket_batch_shape": (578,),
            }
        _evidence(
            "observed_compute_boundaries=PASS "
            "transport=2 role_anchor=2 diffusion_bridge=2 "
            "functional_dynamics=2 egnn=2 auxiliary=2 production_loss=2"
        )

        indicator = carrier.supervision.target_residue_reactive_atom_mask[:, 0]
        pocket_mask = carrier.model_input_batch["pocket_mask"]
        assert int(indicator.sum().item()) == 5
        for sample, flat_index in enumerate(
            carrier.supervision.target_residue_reactive_atom_flat_index.tolist()
        ):
            assert bool(indicator[flat_index].item())
            assert int(pocket_mask[flat_index].item()) == sample

        _evidence(
            "c_task_coordinate_and_fixed_node_contract=START "
            "clean_reference=ligand_mean "
            "post_noise_reference=noised_ligand_mean"
        )
        try:
            _assert_centering_and_fixed_node_contract(
                model=model,
                carrier=carrier,
                transported=observations["transport"][0],
                output=first,
            )
        except BaseException as error:
            _evidence(
                "c_task_coordinate_and_fixed_node_contract=FAIL "
                f"error_type={type(error).__name__} "
                "hook_cleanup=not_reached tripwire_final_check=not_reached"
            )
            raise
        _evidence(
            "c_task_coordinate_and_fixed_node_contract=PASS "
            "clean_ligand=true noised_ligand=true pocket=true "
            "fixed_zero_noise=true coordinate_update_mask=true "
            "fixed_restoration=true feature_channels_unchanged=true"
        )

        observation_stack.close()
        hook_counts_after = tuple(
            len(module._forward_hooks) for module, _hook in hook_specs
        )
        assert hook_counts_after == hook_counts_before
        assert global_tripwire_calls == []
        assert model_tripwire_calls == []
        _evidence(
            "observation_hook_cleanup=PASS hooks_removed=true "
            "tripwire_invocations=0 safety_stack_cleanup=pending"
        )
        fixed_source_identity_after = (
            adapter.verify_covapie_batch001_hidden_post_forward_adapter_sources_v1(
                repository_root=ROOT
            )
            + _verify_additional_bound_sources()
        )
        assert fixed_source_identity_after == fixed_source_identity_before
        checkpoint_size_after, checkpoint_sha_after = _safe_file_identity(
            checkpoint_path
        )
        assert (checkpoint_size_after, checkpoint_sha_after) == (
            checkpoint_size,
            checkpoint_sha,
        )
        final_parameters = _snapshot_named_tensors(model.named_parameters())
        final_buffers = _snapshot_named_tensors(model.named_buffers())
        assert _model_state_fingerprint(
            final_parameters, final_buffers
        ) == state_fingerprint_after_loading
        _evidence(
            "final_in_memory_integrity=PASS parameters_unchanged=true "
            "buffers_unchanged=true carrier_unchanged=true "
            "sources_unchanged=true checkpoint_unchanged=true "
            "backward=false optimizer=false trainer=false checkpoint_save=false"
        )

    _evidence(
        "tripwire_and_context_cleanup=PASS safety_stack_closed=true "
        "this_run_full_forward_count=2 lifecycle_full_forward_count=4"
    )

    # Small, non-sensitive execution summary.  No coordinates, sequences,
    # hidden tensors, or weights are printed.
    print(f"TASK_ID={TASK_ID_V1}")
    print(
        "checkpoint="
        f"bytes:{checkpoint_size},sha256:{checkpoint_sha},"
        f"legacy_keys:{migration['checkpoint_key_count']},"
        f"target_keys:{migration['target_model_key_count']},"
        f"shared_equal:{migration['shared_checkpoint_tensor_equality_count']},"
        f"new_exact:{len(migration['target_only_exact_keys'])},"
        f"new_aux:{len(migration['target_only_auxiliary_keys'])},strict:true"
    )
    print(
        "model="
        f"class:{type(model).__name__},mode:{model.mode},device:{model.device},"
        f"atom_nf:{model.atom_nf},diffusion_steps:{model.ddpm.T},"
        "full_atom:true,target_residue_conditioning:true,virtual_nodes:false"
    )
    print(
        "inputs="
        f"ligand:{tuple(carrier.model_input_batch['lig_coords'].shape)},"
        f"ligand_one_hot:{tuple(carrier.model_input_batch['lig_one_hot'].shape)},"
        f"pocket:{tuple(carrier.model_input_batch['pocket_coords'].shape)},"
        f"pocket_one_hot:{tuple(carrier.model_input_batch['pocket_one_hot'].shape)}"
    )
    print(
        "train5="
        f"count:{len(carrier.sample_identities)},tasks:{carrier.training_scheduled_task_ids},"
        f"generated:{generation_counts},fixed:{fixed_counts}"
    )
    print(
        "calls=transport:2,role_anchor:2,diffusion_bridge:2,"
        "functional_dynamics:2,egnn:2,auxiliary:2,production_loss:2"
    )
    print(
        "timesteps="
        f"{tuple(first.diffusion_trace.diffusion_timestep_int.tolist())},"
        "active_predictions_finite:true"
    )
    print(f"loss_weights={weights}")
    print(f"raw_losses={dict(_loss_values(first))}")
    print(f"valid_counts={dict(_loss_counts(first))},hidden_post_epoch0:5")
    print(
        "state=parameters_unchanged:true,buffers_unchanged:true,"
        "grad_none:true,carrier_unchanged:true,sources_unchanged:true,"
        "checkpoint_unchanged:true"
    )
    print(
        "rng_replay="
        f"pass:true,atol:{DETERMINISM_ABSOLUTE_TOLERANCE_V1},"
        f"rtol:{DETERMINISM_RELATIVE_TOLERANCE_V1},"
        f"max_abs_difference:{replay_maximum_difference}"
    )
    print(
        "weight_origin=legacy_base:checkpoint,"
        "additive_layers:contract_initialized_not_covalently_trained"
    )
    print(
        "training_operations=backward:false,autograd_grad:false,"
        "optimizer_created:false,optimizer_step:false,trainer:false,"
        "checkpoint_saved:false"
    )
