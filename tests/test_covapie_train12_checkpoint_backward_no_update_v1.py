"""Opt-in train12 checkpoint backward-without-update validation V1.

Ordinary collection and execution are non-model-only.  The sole real node is
guarded by ``COVAPIE_RUN_TRAIN12_CHECKPOINT_BACKWARD_NO_UPDATE=1`` before the
real runner can load a checkpoint, prepare a carrier, construct a model, run a
forward, or run a backward.  A separately authorized execution is bounded to
one checkpoint load, one train12 model/carrier/prepared binding, one
grad-enabled forward, and one call to the production ``loss_total.backward()``.
It never creates an optimizer or Trainer and never updates or saves state.
"""

from __future__ import annotations

import ast
import contextlib
from dataclasses import dataclass, fields
import hashlib
import importlib.util
import inspect
import io
import json
import math
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from types import ModuleType, SimpleNamespace
from typing import Callable, Iterator, Mapping, Sequence
from unittest import mock

import pytest
import torch


TASK_ID_V1 = "validate_covapie_train12_checkpoint_backward_no_update_v1"
REAL_BACKWARD_OPT_IN_V1 = (
    "COVAPIE_RUN_TRAIN12_CHECKPOINT_BACKWARD_NO_UPDATE"
)
EXPECTED_REPOSITORY_BASELINE_V1 = (
    "1f1ffb78766fa2757df3f8f8fd9a9bec01e42e14"
)
EXPECTED_CHECKPOINT_SIZE_BYTES_V1 = 17_861_341
EXPECTED_CHECKPOINT_SHA256_V1 = (
    "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
)
MODEL_INITIALIZATION_SEED_V1 = 20_260_821
DIFFUSION_FORWARD_SEED_V1 = 11_030_037
EXPECTED_EPOCH0_TASK_IDS_V1 = (4, 4, 2, 0, 4, 4, 0, 0, 4, 4, 3, 1)
EXPECTED_EPOCH0_HIDDEN_POST_ELIGIBLE_V1 = (0, 1, 2, 3, 4, 11)

CANONICAL_EXACT5_V1 = (
    (0, "warhead_only", "A", (2,)),
    (1, "linker_plus_warhead", "B", (1, 2)),
    (2, "scaffold_plus_warhead", "B2", (0, 2)),
    (3, "scaffold_only", "B3", (0,)),
    (4, "scaffold_plus_linker_plus_warhead", "C", (0, 1, 2)),
)


def _required_canonical_directory_v1(environment_name: str) -> Path:
    configured = os.environ.get(environment_name)
    assert configured is not None, environment_name
    path = Path(configured)
    assert path.is_absolute(), environment_name
    metadata = path.lstat()
    assert stat.S_ISDIR(metadata.st_mode) and not path.is_symlink()
    assert path.resolve(strict=True) == path
    return path


# The external candidate never derives a repository root from __file__.
ROOT = _required_canonical_directory_v1("COVAPIE_TEST_REPOSITORY_ROOT")
STATE_ROOT = _required_canonical_directory_v1("COVAPIE_TEST_STATE_ROOT")
CACHE_ROOT = _required_canonical_directory_v1("COVAPIE_TEST_CACHE_ROOT")
assert CACHE_ROOT == STATE_ROOT / "bulk-multisource-cys-sg-v1/rcsb"


# Direct consumers are fixed by filesystem SHA256 and baseline Git blob.  The
# train12 forward helper independently verifies its complete transitive set.
DIRECT_BOUND_SOURCE_IDENTITIES_V1 = (
    (
        "tests/test_covapie_train12_checkpoint_forward_no_update_v1.py",
        86_340,
        "43d17983f7b9b80820ee1a8aeaf340c41951284cb7ce2550ca4e1a50df970285",
        "4c51526f7b97fcb90289b95c46c37b3b16594cd2",
    ),
    (
        "tests/test_covapie_train10_checkpoint_backward_no_update_v1.py",
        67_691,
        "151bb2ccd74c3c3e9e78cc0dfb928e199ceb729cefdcd422657706f2d4e35d3d",
        "0ea7d5f2ab83cc8dba6f483760c1e16b9d1fea38",
    ),
    (
        "tests/test_covapie_batch001_checkpoint_backward_no_update_v1.py",
        58_548,
        "6a9590c9ed5f87f0fddad2a0844a1c9b2e02f7b9c1aee5a80fa0e4621ef8640f",
        "2950dd99d813cc96c82ff42739920958a4b99c38",
    ),
    (
        "src/covalent_ext/covapie_train12_hidden_post_forward_adapter_v1.py",
        16_701,
        "3d4ee01e0a2db0f64d22c5922b07506cea7133c8c442a08cc9ffa00f921ef294",
        "185369aba7555b93600fbb7a37aafed2eb91589f",
    ),
    (
        "src/covalent_ext/covapie_train12_cpu_batch_composer_v1.py",
        32_288,
        "4f67c695f50ca9d6e8cec30fd6a163db10fb05fd44647b2a189b9aeda6719722",
        "0b4a456592887e686ef984a862d703581b6056d7",
    ),
    (
        "src/covalent_ext/covapie_current11_checkpoint_migration_v1.py",
        14_953,
        "fc36fb23844e6e5d2be2e1e43fcd0afe580d8b86faacca31bd69b8fe70f75ef3",
        "b9d83c4c25a802cd918cf8d2757e519fec66b7cd",
    ),
    (
        "src/covalent_ext/covapie_current11_auxiliary_model_and_loss_v1.py",
        37_580,
        "bb797fdb0c96ce669a348a3ddf3975771398263cdfa2a22f3d9c55b0011271cd",
        "2994fb3833ede233e9964684a8be8695b0bc3897",
    ),
    (
        "src/covalent_ext/covapie_current11_training_lightning_module_v1.py",
        35_218,
        "a61041ef44e79c0622645965461bf4cc0275e5f3bec9a756fcf7d36a4c9c391b",
        "3fedcb28bf88eeae6d870001a3de53cae86ded44",
    ),
    (
        "src/covalent_ext/covapie_current11_training_tensorizer_v1.py",
        39_144,
        "9fdc3f7f101fab5e5e5452e3d8e9f9b0b1e6e5fa8254a261f36310a1dfd0b606",
        "567f3aacd8480a743353583753e657230f80f9a5",
    ),
    (
        "src/covalent_ext/covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1.py",
        51_490,
        "3f19d39148f374d14744fa714a2e7d648a37099168d539c14e7e2320d390ec21",
        "ff74ee8407f67741d725fe335f85e55d94f3145c",
    ),
    (
        "src/covalent_ext/checkpoint_compatible_model_instantiation.py",
        39_301,
        "dfd9957465460f66bc08ac12c264040fae0e2a300eb7359929c780dfa85d3024",
        "ae4cc3e924adfaafa7b75e02e889c36395fefd49",
    ),
    (
        "src/covalent_ext/covapie_current11_checkpoint_migration_and_real_one_batch_train_path_smoke_v1.py",
        29_303,
        "e92d68fc7126eb2c3e20341ad1a3ae3dd48509533761694c482edca01d70df61",
        "d87f97e1c2fbe4043f7179258d6890fb2889fdc0",
    ),
    (
        "src/covalent_ext/diffsbdd_model_instantiation.py",
        12_536,
        "5bc98bad19bad27a4260ce01d68194fbfe46096bd3955b7ff5e5efa4c70d5613",
        "1155162b532fc90c781ae9b5354820b2276f8ea0",
    ),
    (
        "equivariant_diffusion/en_diffusion.py",
        56_305,
        "46a00db84d05ea568786b99b42b1b20c448cec8a99638d162b23b59794172b10",
        "b4a92be4dec8f0ef924c7a44b3b6a7ffb248343f",
    ),
    (
        "configs/crossdock_fullatom_joint.yml",
        1_435,
        "155ac1b9dba8af71946e1f4e17ca9176bd05acba0a6132e50b6929f2dbf3b0ea",
        "e40443bdadd15f783a5fa3f1975b29c30d0da7b9",
    ),
)


def _sha256_v1(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_file_identity_v1(path: Path) -> tuple[int, str, int]:
    metadata = path.lstat()
    assert stat.S_ISREG(metadata.st_mode) and not path.is_symlink(), path
    return metadata.st_size, _sha256_v1(path), stat.S_IMODE(metadata.st_mode)


def _git_bytes_v1(*arguments: str) -> bytes:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    return completed.stdout


def _verify_direct_bound_sources_v1(
) -> tuple[tuple[str, int, str, str], ...]:
    ancestry = subprocess.run(
        (
            "git",
            "merge-base",
            "--is-ancestor",
            EXPECTED_REPOSITORY_BASELINE_V1,
            "HEAD",
        ),
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert ancestry.returncode == 0, "fixed baseline is not an ancestor of HEAD"
    observed = []
    for relative, expected_size, expected_sha, expected_blob in (
        DIRECT_BOUND_SOURCE_IDENTITIES_V1
    ):
        path = ROOT / relative
        size, sha, _mode = _safe_file_identity_v1(path)
        assert (size, sha) == (expected_size, expected_sha), relative
        blob = _git_bytes_v1("hash-object", "--", relative).decode().strip()
        assert blob == expected_blob, relative
        assert _git_bytes_v1("cat-file", "blob", expected_blob) == path.read_bytes()
        observed.append((relative, size, sha, blob))
    return tuple(observed)


def _load_pinned_test_module_v1(
    *, relative: str, module_name: str
) -> ModuleType:
    expected = next(
        row for row in DIRECT_BOUND_SOURCE_IDENTITIES_V1 if row[0] == relative
    )
    path = ROOT / relative
    assert _safe_file_identity_v1(path)[:2] == expected[1:3]
    existing = sys.modules.get(module_name)
    if existing is not None:
        assert Path(existing.__file__).resolve(strict=True) == path
        return existing
    specification = importlib.util.spec_from_file_location(module_name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[module_name] = module
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            specification.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    assert stdout.getvalue() == "" and stderr.getvalue() == ""
    assert Path(module.__file__).resolve(strict=True) == path
    return module


def _load_shared_dependencies_v1() -> dict[str, object]:
    """Load train12 adapter-first owners, then published backward helpers."""

    forward = _load_pinned_test_module_v1(
        relative="tests/test_covapie_train12_checkpoint_forward_no_update_v1.py",
        module_name="_covapie_published_train12_forward_tools_for_backward_v1",
    )
    # This published helper imports the train12 adapter first, applying the
    # published Biopython compatibility before any remaining real-path owner.
    dependencies = forward._load_real_path_dependencies_v1()
    backward = _load_pinned_test_module_v1(
        relative="tests/test_covapie_train10_checkpoint_backward_no_update_v1.py",
        module_name="_covapie_published_train10_backward_tools_for_train12_v1",
    )
    batch_backward = backward._backward_tools_v1()
    expected_batch_path = (
        ROOT / "tests/test_covapie_batch001_checkpoint_backward_no_update_v1.py"
    )
    assert Path(batch_backward.__file__).resolve(strict=True) == expected_batch_path
    for helper in (
        "_semantic_gradient_contract_before_backward_v1",
        "_validate_gradient_records_v1",
        "_assert_model_and_carrier_unchanged_allow_grad_v1",
        "_BackwardInvocationGuardV1",
        "_install_real_backward_tripwires_v1",
        "_merge_secondary_failure_v1",
    ):
        assert callable(getattr(backward, helper)), helper
    for helper in (
        "_published_predefined_noise_schedule_contract_v1",
        "_parameter_gradient_metadata_v1",
        "_gradient_group_stats",
        "_emit_gradient_stats",
    ):
        assert callable(getattr(batch_backward, helper)), helper
    return {
        "forward": forward,
        "backward": backward,
        "batch_backward": batch_backward,
        "dependencies": dependencies,
    }


def _evidence_v1(message: str) -> None:
    print(f"COVAPIE_EVIDENCE {message}", flush=True)


def _seed_branch_active_from_train12_carrier_v1(carrier: object) -> bool:
    valid = carrier.supervision.ligand_minimal_seed_or_anchor_valid
    tasks = carrier.supervision.canonical_task_id
    assert valid.dtype == torch.bool and valid.shape == tasks.shape == (12,)
    task_c = tasks == 4
    assert bool(task_c.any().item())
    assert not bool(valid[~task_c].any().item())
    return bool(valid[task_c].any().item())


def _semantic_gradient_contract_before_backward_v1(
    *,
    named_parameters: Mapping[str, object],
    checkpoint_parameter_names: Sequence[str],
    seed_branch_active: bool,
    geometry_weight: float,
) -> object:
    return _load_shared_dependencies_v1()[
        "backward"
    ]._semantic_gradient_contract_before_backward_v1(
        named_parameters=named_parameters,
        checkpoint_parameter_names=checkpoint_parameter_names,
        seed_branch_active=seed_branch_active,
        geometry_weight=geometry_weight,
    )


def _validate_gradient_records_v1(
    *, records: Sequence[object], semantics: object
) -> object:
    return _load_shared_dependencies_v1()[
        "backward"
    ]._validate_gradient_records_v1(records=records, semantics=semantics)


def _validate_grad_enabled_train12_output_v1(
    *, output: object, carrier: object, model: object, forward: ModuleType
) -> dict[str, object]:
    """Train12-only delta over generic published output inspection."""

    from covalent_ext.covapie_current11_training_lightning_module_v1 import (
        CovapieCurrent11TrainingForwardOutputV1,
    )

    assert type(output) is CovapieCurrent11TrainingForwardOutputV1
    assert output.supervision is carrier.supervision
    loss_output = output.loss_output
    loss_total = loss_output.loss_total
    assert loss_total is output.loss_output.loss_total
    assert loss_total.ndim == 0 and bool(torch.isfinite(loss_total).item())
    assert loss_total.requires_grad is True and loss_total.grad_fn is not None
    legacy = forward._load_published_train10_tools_v1()
    raw_losses = legacy._loss_values_v1(output)
    assert all(math.isfinite(value) for value in raw_losses.values())
    valid_counts = legacy._loss_counts_v1(output)
    eligible = forward._hidden_post_eligibility_oracle_v1(carrier)
    assert eligible == EXPECTED_EPOCH0_HIDDEN_POST_ELIGIBLE_V1
    supervision = carrier.supervision
    assert valid_counts == {
        "base": int(supervision.sample_training_admitted.sum().item()),
        "pair": int(supervision.pair_positive_candidate_valid.sum().item()),
        "geometry": len(eligible),
        "contrastive": int(
            supervision.pair_contrastive_sample_loss_mask.sum().item()
        ),
    }
    for diagnostic in (
        loss_output.pair_prediction_per_sample_detached,
        loss_output.pre_post_geometry_per_sample_detached,
        loss_output.pair_contrastive_per_sample_detached,
    ):
        assert diagnostic.requires_grad is False and diagnostic.grad_fn is None
    timesteps = output.diffusion_trace.diffusion_timestep_int
    assert timesteps.dtype == torch.long and tuple(timesteps.shape) == (12,)
    assert bool(((timesteps >= 0) & (timesteps <= model.ddpm.T)).all().item())
    tasks = tuple(int(value) for value in supervision.canonical_task_id.tolist())
    assert tasks == EXPECTED_EPOCH0_TASK_IDS_V1 and len(tasks) == 12
    return {
        "loss_total": loss_total,
        "raw_losses": raw_losses,
        "valid_counts": valid_counts,
        "timesteps": tuple(int(value) for value in timesteps.tolist()),
        "tasks": tasks,
        "hidden_post_eligible": eligible,
    }


def _assert_bound_prepared_unchanged_v1(
    *, model: object, prepared: object, prepared_snapshot: object,
    composer: object, forward: ModuleType, carrier: object,
) -> None:
    assert model._covapie_train12_bound_prepared_v1 is prepared
    assert model._covapie_train12_bound_prepared_identity_v1 == id(prepared)
    assert model._covapie_train12_bound_prepared_seal_v1 == prepared._seal
    assert model._covapie_train12_bound_repository_root_v1 == ROOT
    assert forward._prepared_snapshot_v1(prepared, composer) == prepared_snapshot
    assert composer.validate_covapie_train12_cpu_epoch_batch_v1(carrier, prepared)


def _assert_s2_state_unchanged_allow_grad_v1(
    *, snapshot: object, model: object, carrier_fingerprint: str,
    carrier: object, prepared: object, prepared_snapshot: object,
    composer: object, forward: ModuleType, backward: ModuleType,
) -> None:
    # Explicitly use the train12 carrier fingerprinter.  The reused helper
    # checks parameter/buffer values, identities, keys, requires-grad flags,
    # configuration, and node-prior state while deliberately allowing .grad.
    backward._assert_model_and_carrier_unchanged_allow_grad_v1(
        snapshot=snapshot,
        model=model,
        carrier_fingerprint=carrier_fingerprint,
        carrier=carrier,
        carrier_fingerprinter=forward._carrier_fingerprint_v1,
    )
    _assert_bound_prepared_unchanged_v1(
        model=model,
        prepared=prepared,
        prepared_snapshot=prepared_snapshot,
        composer=composer,
        forward=forward,
        carrier=carrier,
    )


def _assert_completion_v1(
    *, stages: Mapping[str, bool], guard: object
) -> None:
    required = (
        "s0",
        "forward",
        "s1",
        "coordinate_oracle",
        "backward",
        "s2",
        "gradient_classification",
        "final_integrity",
    )
    assert tuple(stages) == required
    assert all(stages.values()), ("incomplete_real_validation", stages)
    assert guard.forward_requested_count == guard.forward_returned_count == 1
    assert guard.top_level_backward_requested_count == 1
    assert guard.top_level_backward_returned_count == 1
    assert guard.internal_autograd_requested_count == 1
    assert guard.internal_autograd_returned_count == 1
    assert guard.forbidden_calls == []


def _run_real_checkpoint_validation_v1() -> None:
    """Future-authorized one-forward/one-backward train12 path."""

    phase = "dependency_import"
    primary: BaseException | None = None
    primary_traceback = None
    runtime_stack = contextlib.ExitStack()
    rng_before = torch.random.get_rng_state().clone()
    shared: dict[str, object] | None = None
    summary: dict[str, object] = {}
    stages = {
        "s0": False,
        "forward": False,
        "s1": False,
        "coordinate_oracle": False,
        "backward": False,
        "s2": False,
        "gradient_classification": False,
        "final_integrity": False,
    }
    guard: object | None = None
    try:
        shared = _load_shared_dependencies_v1()
        forward = shared["forward"]
        backward = shared["backward"]
        batch_backward = shared["batch_backward"]
        dependencies = shared["dependencies"]
        adapter = dependencies["adapter"]
        checkpoint_locator = dependencies["checkpoint_locator"]
        compatible_owner = dependencies["compatible_owner"]
        migration_owner = dependencies["migration_owner"]
        training_owner = dependencies["training_owner"]
        tensorizer_owner = dependencies["tensorizer_owner"]
        composer_owner = dependencies["composer_owner"]
        legacy_forward = forward._load_published_train10_tools_v1()
        guard = backward._BackwardInvocationGuardV1()

        phase = "fixed_sources_and_static_gradient_contract"
        direct_sources_before = _verify_direct_bound_sources_v1()
        forward_sources_before = forward._verify_bound_sources_v1()
        adapter_sources_before = (
            adapter.verify_covapie_train12_hidden_post_forward_adapter_sources_v1(
                repository_root=ROOT
            )
        )
        schedule = batch_backward._published_predefined_noise_schedule_contract_v1()
        assert (
            schedule.schedule_class_name,
            schedule.schedule_name,
            schedule.timesteps,
            schedule.frozen_parameter_names,
        ) == (
            "PredefinedNoiseSchedule",
            "polynomial_2",
            500,
            ("ddpm.gamma.gamma",),
        )

        phase = "checkpoint_identity_and_single_load"
        assert checkpoint_locator.CHECKPOINT_RELATIVE_PATH_V1 == (
            compatible_owner.CHECKPOINT_PATH
        )
        assert not checkpoint_locator.CHECKPOINT_RELATIVE_PATH_V1.is_absolute()
        checkpoint_path = ROOT / checkpoint_locator.CHECKPOINT_RELATIVE_PATH_V1
        checkpoint_identity = forward._safe_file_identity_v1(checkpoint_path)
        assert checkpoint_identity == (
            EXPECTED_CHECKPOINT_SIZE_BYTES_V1,
            EXPECTED_CHECKPOINT_SHA256_V1,
        )
        _evidence_v1("checkpoint_load=REQUESTED count=1")
        checkpoint = migration_owner.load_covapie_current11_legacy_checkpoint_v1(
            checkpoint_path=checkpoint_path
        )
        checkpoint_state = checkpoint["state_dict"]
        _evidence_v1(
            "checkpoint_load=RETURNED count=1 "
            f"legacy_state_keys={len(checkpoint_state)}"
        )

        phase = "single_model_and_strict_migration"
        runtime_root = Path(tempfile.mkdtemp(
            prefix=TASK_ID_V1 + "-", dir=STATE_ROOT / "review-scratch"
        ))
        _evidence_v1(f"model_construction=REQUESTED count=1 runtime={runtime_root}")
        model = forward._instantiate_train12_model_v1(
            checkpoint=checkpoint, runtime_root=runtime_root
        )
        _evidence_v1("model_construction=RETURNED count=1")
        _evidence_v1("strict_migration=REQUESTED count=1")
        migration = (
            migration_owner.migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
                model=model, checkpoint_state_dict=checkpoint_state
            )
        )
        assert migration["checkpoint_only_key_count"] == 0
        assert migration["shared_shape_mismatch_count"] == 0
        assert migration["migration_missing_keys"] == ()
        assert migration["migration_unexpected_keys"] == ()
        assert migration["full_target_strict_load"] is True
        _evidence_v1("strict_migration=RETURNED count=1 strict=true")
        model.train()
        assert model.training is True and model.ddpm.training is True
        assert model.device == torch.device("cpu")
        assert model.batch_size == 12
        assert model.pocket_representation == "full-atom"
        assert model.virtual_nodes is False
        assert model.ddpm.T == 500
        assert model.ddpm.dynamics.target_residue_atom_conditioning is True
        assert model._trainer is None

        phase = "single_prepare_build_and_bind"
        _evidence_v1("train12_prepare=REQUESTED count=1")
        prepared = composer_owner.prepare_covapie_train12_cpu_batch_composer_v1(
            ROOT, STATE_ROOT, CACHE_ROOT
        )
        prepared_snapshot = forward._prepared_snapshot_v1(
            prepared, composer_owner
        )
        _evidence_v1("train12_prepare=RETURNED count=1")
        _evidence_v1("train12_carrier_build=REQUESTED epoch=0 seed=0 count=1")
        carrier = composer_owner.build_covapie_train12_cpu_epoch_batch_v1(
            prepared, 0, 0
        )
        carrier_measurements = forward._assert_train12_carrier_contract_v1(
            carrier, prepared, composer_owner
        )
        assert forward._prepared_snapshot_v1(
            prepared, composer_owner
        ) == prepared_snapshot
        _evidence_v1(
            "train12_carrier_build=RETURNED count=1 "
            f"tasks={carrier_measurements['tasks']}"
        )
        prebind_parameter_ids = tuple(
            (name, id(value)) for name, value in model.named_parameters()
        )
        prebind_buffer_ids = tuple(
            (name, id(value)) for name, value in model.named_buffers()
        )
        prebind_state_keys = tuple(model.state_dict())
        _evidence_v1("prepared_bind=REQUESTED count=1")
        model.bind_covapie_train12_prepared_context_v1(prepared)
        assert tuple(
            (name, id(value)) for name, value in model.named_parameters()
        ) == prebind_parameter_ids
        assert tuple(
            (name, id(value)) for name, value in model.named_buffers()
        ) == prebind_buffer_ids
        assert tuple(model.state_dict()) == prebind_state_keys
        _assert_bound_prepared_unchanged_v1(
            model=model,
            prepared=prepared,
            prepared_snapshot=prepared_snapshot,
            composer=composer_owner,
            forward=forward,
            carrier=carrier,
        )
        _evidence_v1("prepared_bind=RETURNED count=1")

        phase = "s0_snapshot_and_semantics"
        model_snapshot = legacy_forward._capture_model_snapshot_v1(model)
        named_parameters = dict(model.named_parameters())
        assert all(parameter.grad is None for parameter in named_parameters.values())
        assert tuple(
            name for name, parameter in named_parameters.items()
            if not parameter.requires_grad
        ) == schedule.frozen_parameter_names
        weights = model.covapie_current11_loss_weights
        actual_weights = {
            field.name: getattr(weights, field.name) for field in fields(weights)
        }
        assert actual_weights == {
            "base_diffusion": 1.0,
            "covalent_pair_prediction": 1.0,
            "pre_post_geometry": 0.0,
            "covalent_pair_contrastive": 0.1,
        }
        seed_branch_active = _seed_branch_active_from_train12_carrier_v1(carrier)
        semantics = backward._semantic_gradient_contract_before_backward_v1(
            named_parameters=named_parameters,
            checkpoint_parameter_names=tuple(checkpoint_state),
            seed_branch_active=seed_branch_active,
            geometry_weight=actual_weights["pre_post_geometry"],
        )
        carrier_fingerprint = forward._carrier_fingerprint_v1(carrier)
        stages["s0"] = True
        _evidence_v1(
            "S0_SNAPSHOT_AND_GRADIENT_SEMANTICS=PASS gradients_none=true "
            f"seed_branch_active={str(seed_branch_active).lower()} "
            f"groups={tuple((name, len(members)) for name, members in semantics.groups)} "
            f"frozen={semantics.frozen_parameter_names} "
            f"inactive={semantics.inactive_trainable_parameter_names} "
            f"active_zero_allowed={semantics.active_zero_gradient_parameter_names}"
        )

        phase = "single_backward_guard_and_observers"
        backward._install_real_backward_tripwires_v1(
            runtime_stack, model=model, carrier=carrier, guard=guard
        )
        # Explicitly prohibit zero_grad even though no optimizer is constructed.
        runtime_stack.enter_context(mock.patch.object(
            torch.optim.Optimizer,
            "zero_grad",
            new=lambda *_args, **_kwargs: guard.reject("Optimizer.zero_grad"),
        ))
        transport: dict[str, object] = {"requested": 0, "returned": 0}
        original_transport = model.get_ligand_and_pocket

        def observed_transport(data: object) -> object:
            assert data is carrier.model_input_batch
            transport["requested"] = int(transport["requested"]) + 1
            assert transport["requested"] == 1
            result = original_transport(data)
            transport["value"] = legacy_forward._clone_transport_v1(result)
            transport["returned"] = int(transport["returned"]) + 1
            return result

        runtime_stack.enter_context(mock.patch.object(
            model, "get_ligand_and_pocket", new=observed_transport
        ))
        production_loss: dict[str, object] = {"requested": 0, "returned": 0}
        original_loss = adapter.compute_covapie_current11_training_losses_v1

        def observed_production_loss(*args: object, **kwargs: object) -> object:
            production_loss["requested"] = int(production_loss["requested"]) + 1
            assert production_loss["requested"] == 1
            result = original_loss(*args, **kwargs)
            production_loss["value"] = result
            production_loss["returned"] = int(production_loss["returned"]) + 1
            return result

        runtime_stack.enter_context(mock.patch.object(
            adapter,
            "compute_covapie_current11_training_losses_v1",
            new=observed_production_loss,
        ))

        def forbidden_secondary_tensorization(
            *_args: object, **_kwargs: object
        ) -> None:
            guard.reject("secondary_model_tensorization")

        runtime_stack.enter_context(mock.patch.object(
            tensorizer_owner,
            "tensorize_covapie_current11_training_supervision_v1",
            new=forbidden_secondary_tensorization,
        ))
        runtime_stack.enter_context(mock.patch.object(
            training_owner,
            "tensorize_covapie_current11_training_supervision_v1",
            new=forbidden_secondary_tensorization,
        ))

        phase = "single_grad_enabled_forward"
        assert composer_owner.validate_covapie_train12_cpu_epoch_batch_v1(
            carrier, prepared
        )
        assert forward._prepared_snapshot_v1(
            prepared, composer_owner
        ) == prepared_snapshot
        torch.manual_seed(DIFFUSION_FORWARD_SEED_V1)
        assert torch.is_grad_enabled() is True
        assert torch.is_inference_mode_enabled() is False
        assert all(parameter.grad is None for parameter in model.parameters())
        _evidence_v1("grad_enabled_forward=REQUESTED count=1")
        output = model(carrier)
        measurements = _validate_grad_enabled_train12_output_v1(
            output=output, carrier=carrier, model=model, forward=forward
        )
        stages["forward"] = True
        assert production_loss == {
            "requested": 1,
            "returned": 1,
            "value": output.loss_output,
        }
        _evidence_v1(
            "grad_enabled_forward=RETURNED count=1 "
            f"tasks={measurements['tasks']} timesteps={measurements['timesteps']} "
            f"raw_losses={measurements['raw_losses']} "
            f"valid_counts={measurements['valid_counts']}"
        )

        phase = "s1_post_forward_invariance"
        legacy_forward._assert_model_snapshot_unchanged_v1(model_snapshot, model)
        assert forward._carrier_fingerprint_v1(carrier) == carrier_fingerprint
        _assert_bound_prepared_unchanged_v1(
            model=model,
            prepared=prepared,
            prepared_snapshot=prepared_snapshot,
            composer=composer_owner,
            forward=forward,
            carrier=carrier,
        )
        stages["s1"] = True
        _evidence_v1(
            "S1_POST_FORWARD_INVARIANCE=PASS parameters=true buffers=true "
            "identity=true keys=true requires_grad=true gradients_none=true "
            "configuration_and_node_prior=true carrier=true prepared=true"
        )

        phase = "coordinate_and_fixed_node_oracle"
        assert transport["requested"] == transport["returned"] == 1
        with torch.no_grad():
            legacy_forward._assert_train10_centering_and_fixed_node_contract_v1(
                model=model,
                carrier=carrier,
                transported=transport["value"],
                output=output,
            )
        stages["coordinate_oracle"] = True
        _evidence_v1(
            "TRAIN12_COORDINATE_AND_FIXED_NODE_ORACLE=PASS "
            "atol=1e-05 rtol=1.3e-06 transport_calls=1"
        )

        phase = "single_original_total_loss_backward"
        loss_total = measurements["loss_total"]
        assert loss_total is output.loss_output.loss_total
        assert loss_total.requires_grad is True and loss_total.grad_fn is not None
        guard.expected_loss = loss_total
        _evidence_v1("loss_total_backward=REQUESTED count=1")
        loss_total.backward()
        stages["backward"] = True
        _evidence_v1(
            "loss_total_backward=RETURNED count=1 internal_autograd_count=1"
        )

        phase = "s2_post_backward_state_invariance"
        _assert_s2_state_unchanged_allow_grad_v1(
            snapshot=model_snapshot,
            model=model,
            carrier_fingerprint=carrier_fingerprint,
            carrier=carrier,
            prepared=prepared,
            prepared_snapshot=prepared_snapshot,
            composer=composer_owner,
            forward=forward,
            backward=backward,
        )
        stages["s2"] = True
        _evidence_v1(
            "S2_POST_BACKWARD_STATE_INVARIANCE=PASS parameters=true buffers=true "
            "identity=true keys=true requires_grad=true configuration_and_node_prior=true "
            "carrier=true prepared=true gradients_preserved=true"
        )

        phase = "post_s2_gradient_classification"
        named_parameters = dict(model.named_parameters())
        group_stats = []
        for group_name, parameter_names in semantics.groups:
            item = batch_backward._gradient_group_stats(
                group_name=group_name,
                named_parameters=named_parameters,
                parameter_names=parameter_names,
            )
            batch_backward._emit_gradient_stats(item)
            assert item.all_produced_gradients_finite
            assert math.isfinite(item.gradient_l2_norm)
            assert math.isfinite(item.gradient_max_abs)
            group_stats.append(item)
        stats_by_name = {item.group_name: item for item in group_stats}
        for active_group in (
            "legacy_ddpm_egnn",
            "target_residue_conditioning",
            "role_task_generation_seed_anchor_encoding",
            "pair_embedding_logit",
        ):
            assert stats_by_name[active_group].grad_nonzero_count > 0
        assert stats_by_name["geometry_head"].grad_nonzero_count == 0
        classification = backward._validate_gradient_records_v1(
            records=batch_backward._parameter_gradient_metadata_v1(
                named_parameters
            ),
            semantics=semantics,
        )
        assert classification.frozen_parameter_names == ("ddpm.gamma.gamma",)
        stages["gradient_classification"] = True
        _evidence_v1("TRAIN12_GRADIENT_CLASSIFICATION=PASS")

        phase = "final_integrity"
        assert _verify_direct_bound_sources_v1() == direct_sources_before
        assert forward._verify_bound_sources_v1() == forward_sources_before
        assert (
            adapter.verify_covapie_train12_hidden_post_forward_adapter_sources_v1(
                repository_root=ROOT
            )
            == adapter_sources_before
        )
        assert forward._safe_file_identity_v1(checkpoint_path) == checkpoint_identity
        _assert_s2_state_unchanged_allow_grad_v1(
            snapshot=model_snapshot,
            model=model,
            carrier_fingerprint=carrier_fingerprint,
            carrier=carrier,
            prepared=prepared,
            prepared_snapshot=prepared_snapshot,
            composer=composer_owner,
            forward=forward,
            backward=backward,
        )
        stages["final_integrity"] = True
        _assert_completion_v1(stages=stages, guard=guard)
        summary = {
            "runtime": str(runtime_root),
            "tasks": measurements["tasks"],
            "timesteps": measurements["timesteps"],
            "raw_losses": measurements["raw_losses"],
            "valid_counts": measurements["valid_counts"],
            "weights": actual_weights,
            "forward_requested": guard.forward_requested_count,
            "forward_returned": guard.forward_returned_count,
            "backward_requested": guard.top_level_backward_requested_count,
            "backward_returned": guard.top_level_backward_returned_count,
            "internal_backward_requested": guard.internal_autograd_requested_count,
            "internal_backward_returned": guard.internal_autograd_returned_count,
        }
        _evidence_v1(
            "final_integrity=PASS sources=true checkpoint=true state=true "
            "carrier=true prepared=true gradients=true optimizer=false "
            "trainer=false parameter_update=false save=false"
        )
    except BaseException as error:
        primary = error
        primary_traceback = error.__traceback__

    merge = (
        shared["backward"]._merge_secondary_failure_v1
        if shared is not None
        else None
    )
    if merge is None:
        try:
            runtime_stack.close()
        except BaseException as cleanup_error:
            if primary is None:
                primary = cleanup_error
                primary_traceback = cleanup_error.__traceback__
            else:
                primary.add_note(
                    "secondary_failure phase=observer_and_tripwire_cleanup "
                    f"type={type(cleanup_error).__name__} message={cleanup_error}"
                )
        try:
            torch.random.set_rng_state(rng_before)
        except BaseException as rng_error:
            if primary is None:
                primary = rng_error
                primary_traceback = rng_error.__traceback__
            else:
                primary.add_note(
                    "secondary_failure phase=caller_rng_restore "
                    f"type={type(rng_error).__name__} message={rng_error}"
                )
    else:
        primary = merge(
            primary,
            phase="observer_and_tripwire_cleanup",
            callback=runtime_stack.close,
        )
        primary = merge(
            primary,
            phase="caller_rng_restore",
            callback=lambda: torch.random.set_rng_state(rng_before),
        )
    if primary is not None:
        if shared is not None:
            legacy_forward = shared["forward"]._load_published_train10_tools_v1()
            primary = shared["backward"]._merge_secondary_failure_v1(
                primary,
                phase="primary_failure_reporting",
                callback=lambda: legacy_forward._report_primary_failure_v1(
                    primary=primary,
                    phase=phase,
                    call_counts={
                        "stages": dict(stages),
                        "forward_requested": (
                            0 if guard is None else guard.forward_requested_count
                        ),
                        "forward_returned": (
                            0 if guard is None else guard.forward_returned_count
                        ),
                        "backward_requested": (
                            0
                            if guard is None
                            else guard.top_level_backward_requested_count
                        ),
                        "backward_returned": (
                            0
                            if guard is None
                            else guard.top_level_backward_returned_count
                        ),
                    },
                ),
            )
        raise primary.with_traceback(primary_traceback)
    _evidence_v1(
        "REAL_TRAIN12_FORWARD_BACKWARD_NO_UPDATE=PASS "
        + json.dumps(summary, sort_keys=True)
    )


def _execute_real_path_if_enabled_v1() -> None:
    if os.environ.get(REAL_BACKWARD_OPT_IN_V1) != "1":
        pytest.skip(
            f"set {REAL_BACKWARD_OPT_IN_V1}=1 for the bounded real backward path"
        )
    _evidence_v1(
        "real_opt_in=1 checkpoint_load_budget=1 model_budget=1 "
        "prepare_budget=1 carrier_budget=1 bind_budget=1 forward_budget=1 "
        "total_backward_budget=1 optimizer_budget=0 trainer_budget=0 "
        "parameter_update_budget=0"
    )
    _run_real_checkpoint_validation_v1()


@pytest.fixture(autouse=True)
def _non_model_execution_tripwires_v1(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> Iterator[list[str]]:
    """Ordinary nodes fail closed at all real model/training boundaries."""

    calls: list[str] = []
    if (
        request.node.name
        == "test_real_checkpoint_train12_forward_backward_without_update"
        and os.environ.get(REAL_BACKWARD_OPT_IN_V1) == "1"
    ):
        yield calls
        return

    shared = _load_shared_dependencies_v1()
    dependencies = shared["dependencies"]
    adapter = dependencies["adapter"]
    composer = dependencies["composer_owner"]
    import pytorch_lightning as pl

    def forbidden(name: str) -> Callable[..., None]:
        def tripwire(*_args: object, **_kwargs: object) -> None:
            calls.append(name)
            raise AssertionError(f"non-model node crossed boundary: {name}")

        return tripwire

    targets = (
        (torch, "load", "torch.load"),
        (torch, "save", "torch.save"),
        (torch.Tensor, "backward", "Tensor.backward"),
        (torch.autograd, "backward", "torch.autograd.backward"),
        (torch.autograd, "grad", "torch.autograd.grad"),
        (torch.optim.Optimizer, "__init__", "Optimizer.__init__"),
        (torch.optim.Optimizer, "zero_grad", "Optimizer.zero_grad"),
        (torch.optim.Optimizer, "step", "Optimizer.step"),
        (pl.Trainer, "__init__", "Trainer.__init__"),
        (pl.Trainer, "fit", "Trainer.fit"),
        (pl.Trainer, "validate", "Trainer.validate"),
        (pl.Trainer, "test", "Trainer.test"),
        (pl.Trainer, "predict", "Trainer.predict"),
        (pl.Trainer, "save_checkpoint", "Trainer.save_checkpoint"),
        (
            composer,
            "prepare_covapie_train12_cpu_batch_composer_v1",
            "train12_prepare",
        ),
        (
            composer,
            "build_covapie_train12_cpu_epoch_batch_v1",
            "train12_carrier_build",
        ),
        (
            adapter.CovapieTrain12HiddenPostForwardLigandPocketDDPMV1,
            "__init__",
            "train12_model_init",
        ),
        (
            adapter.CovapieTrain12HiddenPostForwardLigandPocketDDPMV1,
            "forward",
            "train12_model_forward",
        ),
        (
            adapter,
            "compute_covapie_current11_training_losses_v1",
            "production_loss",
        ),
    )
    for owner, attribute, name in targets:
        monkeypatch.setattr(owner, attribute, forbidden(name))
    yield calls
    assert calls == []


def test_fixed_sources_adapter_first_helpers_and_static_real_budget() -> None:
    observed = _verify_direct_bound_sources_v1()
    assert len(observed) == len(DIRECT_BOUND_SOURCE_IDENTITIES_V1)
    shared = _load_shared_dependencies_v1()
    forward = shared["forward"]
    backward = shared["backward"]
    batch_backward = shared["batch_backward"]
    dependencies = shared["dependencies"]
    assert forward._verify_bound_sources_v1()
    assert dependencies["adapter"].verify_covapie_train12_hidden_post_forward_adapter_sources_v1(
        repository_root=ROOT
    )
    assert dependencies["composer_owner"]._verify_direct_helpers(ROOT)
    assert tuple(dependencies["composer_owner"].CANONICAL_TASKS_V1) == (
        CANONICAL_EXACT5_V1
    )
    assert CANONICAL_EXACT5_V1[3][1:3] == ("scaffold_only", "B3")
    assert len(CANONICAL_EXACT5_V1) == 5
    assert Path(forward.__file__).resolve(strict=True) == (
        ROOT / DIRECT_BOUND_SOURCE_IDENTITIES_V1[0][0]
    )
    assert Path(backward.__file__).resolve(strict=True) == (
        ROOT / DIRECT_BOUND_SOURCE_IDENTITIES_V1[1][0]
    )
    assert Path(batch_backward.__file__).resolve(strict=True) == (
        ROOT / DIRECT_BOUND_SOURCE_IDENTITIES_V1[2][0]
    )
    schedule = batch_backward._published_predefined_noise_schedule_contract_v1()
    assert schedule.frozen_parameter_names == ("ddpm.gamma.gamma",)
    assert schedule.timesteps == 500 and schedule.schedule_name == "polynomial_2"
    assert forward.EXPECTED_EPOCH0_TASK_IDS_V1 == EXPECTED_EPOCH0_TASK_IDS_V1
    assert forward.MODEL_INITIALIZATION_SEED_V1 == MODEL_INITIALIZATION_SEED_V1
    assert forward.DIFFUSION_FORWARD_SEED_V1 == DIFFUSION_FORWARD_SEED_V1
    assert forward.EXPECTED_CHECKPOINT_SIZE_BYTES_V1 == (
        EXPECTED_CHECKPOINT_SIZE_BYTES_V1
    )
    assert forward.EXPECTED_CHECKPOINT_SHA256_V1 == EXPECTED_CHECKPOINT_SHA256_V1

    run_tree = ast.parse(inspect.getsource(_run_real_checkpoint_validation_v1))
    backward_calls = [
        node
        for node in ast.walk(run_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "backward"
    ]
    assert len(backward_calls) == 1
    assert isinstance(backward_calls[0].func.value, ast.Name)
    assert backward_calls[0].func.value.id == "loss_total"
    assert backward_calls[0].args == [] and backward_calls[0].keywords == []

    def call_count(name: str) -> int:
        return sum(
            1
            for node in ast.walk(run_tree)
            if isinstance(node, ast.Call)
            and (
                (isinstance(node.func, ast.Name) and node.func.id == name)
                or (isinstance(node.func, ast.Attribute) and node.func.attr == name)
            )
        )

    assert call_count("load_covapie_current11_legacy_checkpoint_v1") == 1
    assert call_count("_instantiate_train12_model_v1") == 1
    assert call_count("migrate_covapie_current11_legacy_checkpoint_state_dict_v1") == 1
    assert call_count("prepare_covapie_train12_cpu_batch_composer_v1") == 1
    assert call_count("build_covapie_train12_cpu_epoch_batch_v1") == 1
    assert call_count("bind_covapie_train12_prepared_context_v1") == 1
    assert call_count("mkdtemp") == 1
    assert sum(
        1
        for node in ast.walk(run_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "model"
    ) == 1
    run_source = inspect.getsource(_run_real_checkpoint_validation_v1)
    for forbidden_source in (
        "autograd.grad",
        "retain_graph",
        "create_graph",
        ".step(",
        ".zero_grad(",
        "Trainer(",
        "load_state_dict(",
        ".copy_(",
        ".data",
    ):
        assert forbidden_source not in run_source
    output_source = inspect.getsource(_validate_grad_enabled_train12_output_v1)
    assert "(12,)" in output_source and "(10,)" not in output_source
    assert "_validate_grad_enabled_forward_output_v1" not in run_source
    assert call_count("_run_real_checkpoint_validation_v1") == 0


def test_default_gate_precedes_real_runner_and_old_switches_do_not_enable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    touched = []

    def forbidden_real_runner() -> None:
        touched.append("real_runner")
        raise AssertionError("default-disabled real runner was reached")

    monkeypatch.delenv(REAL_BACKWARD_OPT_IN_V1, raising=False)
    for old_switch in (
        "COVAPIE_RUN_TRAIN12_CHECKPOINT_FORWARD_NO_UPDATE",
        "COVAPIE_RUN_TRAIN10_CHECKPOINT_BACKWARD_NO_UPDATE",
        "COVAPIE_RUN_TRAIN10_CHECKPOINT_FORWARD_NO_UPDATE",
        "COVAPIE_RUN_BATCH001_CHECKPOINT_BACKWARD_NO_UPDATE",
        "COVAPIE_RUN_BATCH001_CHECKPOINT_FORWARD_NO_UPDATE",
        "COVAPIE_RUN_BATCH001_CHECKPOINT_SINGLE_OPTIMIZER_STEP",
        "COVAPIE_RUN_TRAIN10_BOUNDED_FIT",
    ):
        monkeypatch.setenv(old_switch, "1")
    monkeypatch.setattr(
        sys.modules[__name__],
        "_run_real_checkpoint_validation_v1",
        forbidden_real_runner,
    )
    with pytest.raises(pytest.skip.Exception, match=REAL_BACKWARD_OPT_IN_V1):
        _execute_real_path_if_enabled_v1()
    assert touched == []


def test_wrong_checkpoint_identity_rejected_before_deserialization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    migration = _load_shared_dependencies_v1()["dependencies"]["migration_owner"]
    candidate = tmp_path / "synthetic-wrong-checkpoint.bin"
    candidate.write_bytes(b"not-the-published-checkpoint")
    calls = []

    def forbidden_load(*_args: object, **_kwargs: object) -> None:
        calls.append("torch.load")
        raise AssertionError("identity mismatch reached deserialization")

    monkeypatch.setattr(migration.torch, "load", forbidden_load)
    with pytest.raises(
        ValueError, match="^COVAPIE_CURRENT11_CHECKPOINT_MIGRATION_V1_ERROR$"
    ):
        migration.load_covapie_current11_legacy_checkpoint_v1(
            checkpoint_path=candidate
        )
    assert calls == []


def _synthetic_parameter_name_contract_v1(
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    names = (
        "ddpm.gamma.gamma",
        "ddpm.dynamics.egnn.weight",
        "ddpm.dynamics.residue_decoder.weight",
        "ddpm.dynamics.target_residue_atom_condition_embedding",
        "covapie_current11_auxiliary_model_v1.role_embedding.weight",
        "covapie_current11_auxiliary_model_v1.seed_indicator_embedding.weight",
        "covapie_current11_auxiliary_model_v1.anchor_distance_encoder.0.weight",
        "covapie_current11_auxiliary_model_v1.anchor_distance_encoder.0.bias",
        "covapie_current11_auxiliary_model_v1.pair_embedding.0.weight",
        "covapie_current11_auxiliary_model_v1.pre_post_geometry_head.0.weight",
    )
    return names, names[:3]


def _synthetic_named_parameter_flags_v1() -> dict[str, object]:
    names, _checkpoint = _synthetic_parameter_name_contract_v1()
    return {
        name: SimpleNamespace(requires_grad=(name != "ddpm.gamma.gamma"))
        for name in names
    }


def _synthetic_gradient_records_v1(
    semantics: object,
    *,
    geometry_state: str = "none",
    override: tuple[str, str, bool, bool] | None = None,
) -> tuple[object, ...]:
    batch = _load_shared_dependencies_v1()["batch_backward"]
    names, _checkpoint = _synthetic_parameter_name_contract_v1()
    inactive = set(semantics.inactive_trainable_parameter_names)
    frozen = set(semantics.frozen_parameter_names)
    zero_allowed = set(semantics.active_zero_gradient_parameter_names)
    records = []
    for name in names:
        if name in frozen:
            state, finite, requires_grad = "none", True, False
        elif name.startswith(batch.GEOMETRY_PREFIX_V1):
            state, finite, requires_grad = geometry_state, True, True
        elif name in inactive:
            state, finite, requires_grad = "none", True, True
        elif name in zero_allowed:
            state, finite, requires_grad = "all_zero", True, True
        else:
            state, finite, requires_grad = "nonzero", True, True
        if override is not None and name == override[0]:
            state, finite, requires_grad = override[1:]
        records.append(batch._ParameterGradientMetadataV1(
            name=name,
            requires_grad=requires_grad,
            gradient_state=state,
            produced_gradient_finite=finite,
        ))
    return tuple(records)


@pytest.mark.parametrize("seed_branch_active", [False, True])
@pytest.mark.parametrize("geometry_state", ["none", "all_zero"])
def test_synthetic_gradient_classification_legal_states(
    seed_branch_active: bool, geometry_state: str
) -> None:
    """Direct metadata fixtures only; no Tensor.backward/autograd is invoked."""

    names, checkpoint_names = _synthetic_parameter_name_contract_v1()
    semantics = _semantic_gradient_contract_before_backward_v1(
        named_parameters=_synthetic_named_parameter_flags_v1(),
        checkpoint_parameter_names=checkpoint_names,
        seed_branch_active=seed_branch_active,
        geometry_weight=0.0,
    )
    seed_name = (
        "covapie_current11_auxiliary_model_v1.seed_indicator_embedding.weight"
    )
    assert (seed_name in semantics.inactive_trainable_parameter_names) is (
        not seed_branch_active
    )
    assert {
        name for _group, members in semantics.groups for name in members
    } == set(names)
    classification = _validate_gradient_records_v1(
        records=_synthetic_gradient_records_v1(
            semantics, geometry_state=geometry_state
        ),
        semantics=semantics,
    )
    assert classification.frozen_parameter_names == ("ddpm.gamma.gamma",)


def test_synthetic_gradient_classifier_fails_closed() -> None:
    names, checkpoint_names = _synthetic_parameter_name_contract_v1()
    semantics = _semantic_gradient_contract_before_backward_v1(
        named_parameters=_synthetic_named_parameter_flags_v1(),
        checkpoint_parameter_names=checkpoint_names,
        seed_branch_active=True,
        geometry_weight=0.0,
    )
    active = "ddpm.dynamics.egnn.weight"
    cases = (
        ((active, "none", True, True), "active_parameter_gradient_none"),
        ((active, "all_zero", True, True), "unexpected_active_zero_gradient"),
        ((active, "nonzero", False, True), "active_parameter_gradient_nonfinite"),
        ((active, "none", True, False), "frozen_parameter_contract_mismatch"),
    )
    for override, pattern in cases:
        with pytest.raises(AssertionError, match=pattern):
            _validate_gradient_records_v1(
                records=_synthetic_gradient_records_v1(
                    semantics, override=override
                ),
                semantics=semantics,
            )
    with pytest.raises(AssertionError):
        _validate_gradient_records_v1(
            records=_synthetic_gradient_records_v1(
                semantics, geometry_state="nonzero"
            ),
            semantics=semantics,
        )
    duplicate = _synthetic_gradient_records_v1(semantics)
    with pytest.raises(AssertionError):
        _validate_gradient_records_v1(
            records=duplicate + (duplicate[-1],), semantics=semantics
        )

    unknown = _synthetic_named_parameter_flags_v1()
    unknown["unclassified_new_module.weight"] = SimpleNamespace(
        requires_grad=True
    )
    with pytest.raises(AssertionError, match="unknown_or_multiply_grouped_parameter"):
        _semantic_gradient_contract_before_backward_v1(
            named_parameters=unknown,
            checkpoint_parameter_names=checkpoint_names,
            seed_branch_active=True,
            geometry_weight=0.0,
        )
    multiply_grouped_checkpoint = tuple(checkpoint_names) + (
        "ddpm.dynamics.target_residue_atom_condition_embedding",
    )
    with pytest.raises(AssertionError, match="unknown_or_multiply_grouped_parameter"):
        _semantic_gradient_contract_before_backward_v1(
            named_parameters=_synthetic_named_parameter_flags_v1(),
            checkpoint_parameter_names=multiply_grouped_checkpoint,
            seed_branch_active=True,
            geometry_weight=0.0,
        )
    assert len(names) == 10


def test_synthetic_direct_grad_metadata_stats_and_nonfinite_rejection() -> None:
    """Synthetic .grad assignment is fixture data, not a parameter update."""

    batch = _load_shared_dependencies_v1()["batch_backward"]
    names, checkpoint_names = _synthetic_parameter_name_contract_v1()
    parameters = {
        name: torch.nn.Parameter(
            torch.ones(2), requires_grad=(name != "ddpm.gamma.gamma")
        )
        for name in names
    }
    semantics = _semantic_gradient_contract_before_backward_v1(
        named_parameters=parameters,
        checkpoint_parameter_names=checkpoint_names,
        seed_branch_active=True,
        geometry_weight=0.0,
    )
    inactive = set(semantics.inactive_trainable_parameter_names)
    zero_allowed = set(semantics.active_zero_gradient_parameter_names)
    for name, parameter in parameters.items():
        if not parameter.requires_grad or name in inactive:
            continue
        parameter.grad = (
            torch.zeros_like(parameter)
            if name in zero_allowed
            else torch.ones_like(parameter)
        )
    records = batch._parameter_gradient_metadata_v1(parameters)
    _validate_gradient_records_v1(records=records, semantics=semantics)
    stats = {
        group: batch._gradient_group_stats(
            group_name=group,
            named_parameters=parameters,
            parameter_names=members,
        )
        for group, members in semantics.groups
    }
    assert stats["geometry_head"].grad_nonzero_count == 0
    assert stats["legacy_ddpm_egnn"].grad_nonzero_count > 0
    assert all(item.all_produced_gradients_finite for item in stats.values())
    for value in (float("nan"), float("inf")):
        parameters["ddpm.dynamics.egnn.weight"].grad = torch.full((2,), value)
        records = batch._parameter_gradient_metadata_v1(parameters)
        with pytest.raises(AssertionError, match="active_parameter_gradient_nonfinite"):
            _validate_gradient_records_v1(records=records, semantics=semantics)


class _SyntheticStateModelV1(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.weight = torch.nn.Parameter(torch.tensor([1.0, 2.0]))
        self.register_buffer("node_prior", torch.tensor([0.25, 0.75]))
        self.config_tag = "stable"


def _synthetic_configuration_v1(model: _SyntheticStateModelV1) -> object:
    return {
        "config_tag": model.config_tag,
        "node_prior": model.node_prior.clone(),
    }


def _synthetic_state_fixture_v1(
) -> tuple[object, object, dict[str, object], str, ModuleType, ModuleType]:
    shared = _load_shared_dependencies_v1()
    forward = shared["forward"]
    backward = shared["backward"]
    model = _SyntheticStateModelV1()
    carrier = {
        "tasks": EXPECTED_EPOCH0_TASK_IDS_V1,
        "payload": torch.tensor([3, 5]),
    }
    snapshot = backward._capture_synthetic_compatible_snapshot_v1(
        model, configuration_snapshotter=_synthetic_configuration_v1
    )
    fingerprint = forward._fingerprint_supported_v1(carrier)
    return model, snapshot, carrier, fingerprint, forward, backward


def _assert_synthetic_state_allow_grad_v1(
    *, model: object, snapshot: object, carrier: object,
    fingerprint: str, forward: ModuleType, backward: ModuleType,
) -> None:
    backward._assert_model_and_carrier_unchanged_allow_grad_v1(
        snapshot=snapshot,
        model=model,
        carrier_fingerprint=fingerprint,
        carrier=carrier,
        configuration_snapshotter=_synthetic_configuration_v1,
        carrier_fingerprinter=forward._fingerprint_supported_v1,
    )


def test_s1_requires_grad_none_while_s2_allows_legal_grad() -> None:
    model, snapshot, carrier, fingerprint, forward, backward = (
        _synthetic_state_fixture_v1()
    )
    assert all(parameter.grad is None for parameter in model.parameters())
    _assert_synthetic_state_allow_grad_v1(
        model=model,
        snapshot=snapshot,
        carrier=carrier,
        fingerprint=fingerprint,
        forward=forward,
        backward=backward,
    )
    # Synthetic direct .grad assignment models only the S1->S2 state change.
    model.weight.grad = torch.tensor([0.5, -0.5])
    with pytest.raises(AssertionError):
        assert all(parameter.grad is None for parameter in model.parameters())
    _assert_synthetic_state_allow_grad_v1(
        model=model,
        snapshot=snapshot,
        carrier=carrier,
        fingerprint=fingerprint,
        forward=forward,
        backward=backward,
    )


@pytest.mark.parametrize(
    "mutation",
    ["parameter", "buffer", "identity", "keys", "requires_grad", "config", "carrier"],
)
def test_s2_state_gate_rejects_non_gradient_mutation(mutation: str) -> None:
    model, snapshot, carrier, fingerprint, forward, backward = (
        _synthetic_state_fixture_v1()
    )
    if mutation == "parameter":
        with torch.no_grad():
            model.weight.add_(1.0)
    elif mutation == "buffer":
        model.node_prior.add_(0.1)
    elif mutation == "identity":
        model.weight = torch.nn.Parameter(model.weight.detach().clone())
    elif mutation == "keys":
        model.register_buffer("unexpected", torch.ones(1))
    elif mutation == "requires_grad":
        model.weight.requires_grad_(False)
    elif mutation == "config":
        model.config_tag = "changed"
    elif mutation == "carrier":
        carrier["tasks"] = (0,)
    with pytest.raises(AssertionError):
        _assert_synthetic_state_allow_grad_v1(
            model=model,
            snapshot=snapshot,
            carrier=carrier,
            fingerprint=fingerprint,
            forward=forward,
            backward=backward,
        )


class _SyntheticPreparedComposerV1:
    def __init__(self) -> None:
        self.train10 = SimpleNamespace(_prepared_seal_v1=lambda value: value.seal10)
        self.ready2 = SimpleNamespace(_seal=lambda value: value.seal_ready2)

    @staticmethod
    def _validate_prepared(value: object) -> object:
        assert value.valid is True
        return value


def _synthetic_prepared_v1() -> object:
    return SimpleNamespace(
        valid=True,
        _seal="outer-seal",
        _repo="repo",
        _state="state",
        _cache="cache",
        _groups=("group",),
        _gjj_profile=("gjj",),
        _helper_bindings=("helper",),
        _train10=SimpleNamespace(seal10="train10-seal"),
        _ready2=SimpleNamespace(seal_ready2="ready2-seal"),
        sample_identities=("s0",),
        canonical_event_ids=("e0",),
        leakage_group_ids=("g0",),
        ready_for_training=False,
        feature_semantics_audit_required_later=True,
        step12d_is_only_smoke_legality_check=True,
    )


def test_prepared_snapshot_rejects_identity_and_content_tamper() -> None:
    forward = _load_shared_dependencies_v1()["forward"]
    composer = _SyntheticPreparedComposerV1()
    prepared = _synthetic_prepared_v1()
    snapshot = forward._prepared_snapshot_v1(prepared, composer)
    assert forward._prepared_snapshot_v1(prepared, composer) == snapshot
    prepared._seal = "tampered"
    assert forward._prepared_snapshot_v1(prepared, composer) != snapshot
    replacement = _synthetic_prepared_v1()
    assert forward._prepared_snapshot_v1(replacement, composer) != snapshot


def test_single_backward_guard_bound_loss_and_nested_delegation() -> None:
    backward = _load_shared_dependencies_v1()["backward"]
    loss = object()
    guard = backward._BackwardInvocationGuardV1()
    guard.expected_loss = loss
    events = []

    def top_delegate(_loss: object) -> None:
        guard.invoke_internal_autograd_backward(
            (loss,), {}, lambda: events.append("internal_return")
        )

    guard.invoke_tensor_backward(loss, (), {}, top_delegate)
    assert events == ["internal_return"]
    assert guard.top_level_backward_requested_count == 1
    assert guard.top_level_backward_returned_count == 1
    assert guard.internal_autograd_requested_count == 1
    assert guard.internal_autograd_returned_count == 1
    with pytest.raises(AssertionError, match="second_top_level_call"):
        guard.invoke_tensor_backward(loss, (), {}, top_delegate)

    wrong = backward._BackwardInvocationGuardV1()
    wrong.expected_loss = loss
    with pytest.raises(AssertionError, match="unbound_loss"):
        wrong.invoke_tensor_backward(object(), (), {}, lambda _value: None)
    with pytest.raises(AssertionError, match="nondefault_options"):
        wrong.invoke_tensor_backward(
            loss, (), {"retain_graph": True}, lambda _value: None
        )
    outside = backward._BackwardInvocationGuardV1()
    with pytest.raises(AssertionError, match="outside_authorized_call"):
        outside.invoke_internal_autograd_backward((), {}, lambda: None)
    retained = backward._BackwardInvocationGuardV1()
    retained.expected_loss = loss
    with pytest.raises(AssertionError, match="graph_retention_requested"):
        retained.invoke_tensor_backward(
            loss,
            (),
            {},
            lambda _value: retained.invoke_internal_autograd_backward(
                (loss, None, True), {}, lambda: None
            ),
        )
    repeated = backward._BackwardInvocationGuardV1()
    repeated.expected_loss = loss

    def duplicate_internal(_value: object) -> None:
        repeated.invoke_internal_autograd_backward((loss,), {}, lambda: None)
        repeated.invoke_internal_autograd_backward((loss,), {}, lambda: None)

    with pytest.raises(AssertionError, match="unexpected_internal_count"):
        repeated.invoke_tensor_backward(loss, (), {}, duplicate_internal)


def test_primary_failure_and_completion_gate_fail_closed() -> None:
    backward = _load_shared_dependencies_v1()["backward"]

    class PrimaryFailure(RuntimeError):
        pass

    root = LookupError("root-cause")
    captured: PrimaryFailure | None = None
    try:
        raise root
    except LookupError as active_root:
        try:
            raise PrimaryFailure("primary-model-path-failure") from active_root
        except PrimaryFailure as error:
            captured = error
    assert captured is not None
    observed: BaseException | None = captured
    observed = backward._merge_secondary_failure_v1(
        observed,
        phase="summary",
        callback=lambda: (_ for _ in ()).throw(ValueError("summary-failure")),
    )
    observed = backward._merge_secondary_failure_v1(
        observed,
        phase="cleanup",
        callback=lambda: (_ for _ in ()).throw(OSError("cleanup-failure")),
    )
    assert observed is captured
    assert observed.__cause__ is root
    assert observed.__context__ is root
    assert len(observed.__notes__) == 2
    assert "summary-failure" in observed.__notes__[0]
    assert "cleanup-failure" in observed.__notes__[1]

    guard = backward._BackwardInvocationGuardV1()
    complete = {
        "s0": True,
        "forward": True,
        "s1": True,
        "coordinate_oracle": True,
        "backward": True,
        "s2": False,
        "gradient_classification": False,
        "final_integrity": False,
    }
    with pytest.raises(AssertionError, match="incomplete_real_validation"):
        _assert_completion_v1(stages=complete, guard=guard)


def test_fresh_process_dependency_helper_adapter_first_no_model() -> None:
    child_code = r'''
import contextlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from unittest import mock

candidate = Path(os.environ["COVAPIE_FRESH_PROCESS_CANDIDATE"])
repo = Path(os.environ["COVAPIE_TEST_REPOSITORY_ROOT"])
state = Path(os.environ["COVAPIE_TEST_STATE_ROOT"])
runtime_parent = state / "review-scratch"
runtime_pattern = "validate_covapie_train12_checkpoint_backward_no_update_v1-*"
runtime_before = tuple(sorted(runtime_parent.glob(runtime_pattern)))
adapter_name = "covalent_ext.covapie_train12_hidden_post_forward_adapter_v1"
training_name = "covalent_ext.covapie_current11_training_lightning_module_v1"
assert adapter_name not in sys.modules and training_name not in sys.modules
assert "COVAPIE_RUN_TRAIN12_CHECKPOINT_BACKWARD_NO_UPDATE" not in os.environ

spec = importlib.util.spec_from_file_location("cold_train12_backward_candidate", candidate)
assert spec is not None and spec.loader is not None
subject = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = subject
spec.loader.exec_module(subject)
assert adapter_name not in sys.modules and training_name not in sys.modules

from Bio.PDB import Polypeptide
compat_before = hasattr(Polypeptide, "three_to_one")
assert compat_before is False
import pytorch_lightning as pl
import torch

calls = []
def forbidden(name):
    def tripwire(*_args, **_kwargs):
        calls.append(name)
        raise AssertionError("cold dependency boundary: " + name)
    return tripwire

profile_targets = {
    "CovapieTrain12HiddenPostForwardLigandPocketDDPMV1.__init__",
    "CovapieTrain12HiddenPostForwardLigandPocketDDPMV1.forward",
    "CovapieCurrent11TrainingLigandPocketDDPM.__init__",
    "CovapieCurrent11TrainingLigandPocketDDPM.forward",
    "LigandPocketDDPM.__init__",
    "LigandPocketDDPM.forward",
    "compute_covapie_current11_training_losses_v1",
}
def profiler(frame, event, _arg):
    if event == "call" and frame.f_code.co_qualname in profile_targets:
        calls.append("profile:" + frame.f_code.co_qualname)
        raise AssertionError("cold dependency executed model path")

def audit_hook(event, arguments):
    if event == "open" and arguments:
        path = arguments[0]
        if isinstance(path, (str, bytes, os.PathLike)):
            rendered = os.fsdecode(path)
            if "/checkpoints/" in rendered or rendered.endswith(".ckpt"):
                calls.append("checkpoint_open:" + rendered)
                raise AssertionError("cold dependency opened checkpoint")
    if event == "os.mkdir" and arguments:
        path = arguments[0]
        if isinstance(path, (str, bytes, os.PathLike)):
            created = Path(os.fsdecode(path))
            if not created.is_absolute():
                created = Path.cwd() / created
            if created.parent == runtime_parent and created.match(runtime_pattern):
                calls.append("runtime_mkdir:" + str(created))
                raise AssertionError("cold dependency created runtime")

sys.addaudithook(audit_hook)
with contextlib.ExitStack() as stack:
    for owner, attribute, name in (
        (torch, "load", "torch.load"),
        (torch, "save", "torch.save"),
        (torch.Tensor, "backward", "Tensor.backward"),
        (torch.autograd, "backward", "torch.autograd.backward"),
        (torch.autograd, "grad", "torch.autograd.grad"),
        (torch.optim.Optimizer, "__init__", "Optimizer.__init__"),
        (torch.optim.Optimizer, "zero_grad", "Optimizer.zero_grad"),
        (torch.optim.Optimizer, "step", "Optimizer.step"),
        (pl.Trainer, "__init__", "Trainer.__init__"),
        (pl.Trainer, "fit", "Trainer.fit"),
    ):
        stack.enter_context(mock.patch.object(owner, attribute, new=forbidden(name)))
    sys.setprofile(profiler)
    try:
        first = subject._load_shared_dependencies_v1()
        second = subject._load_shared_dependencies_v1()
    finally:
        sys.setprofile(None)

assert calls == []
assert tuple(sorted(runtime_parent.glob(runtime_pattern))) == runtime_before
assert all(
    first[key] is second[key]
    for key in ("forward", "backward", "batch_backward")
)
assert first["dependencies"].keys() == second["dependencies"].keys()
assert all(
    first["dependencies"][key] is second["dependencies"][key]
    for key in first["dependencies"]
)
assert first["dependencies"]["adapter"] is sys.modules[adapter_name]
assert first["dependencies"]["training_owner"] is sys.modules[training_name]
assert hasattr(Polypeptide, "three_to_one")
assert first["dependencies"]["adapter"].BIOPYTHON_COMPAT_APPLIED_V1 is True
assert Path(first["forward"].__file__).resolve() == repo / "tests/test_covapie_train12_checkpoint_forward_no_update_v1.py"
assert Path(first["backward"].__file__).resolve() == repo / "tests/test_covapie_train10_checkpoint_backward_no_update_v1.py"
assert Path(first["batch_backward"].__file__).resolve() == repo / "tests/test_covapie_batch001_checkpoint_backward_no_update_v1.py"
print(json.dumps({
    "compat_before": compat_before,
    "compat_after": hasattr(Polypeptide, "three_to_one"),
    "adapter_path": str(Path(first["dependencies"]["adapter"].__file__).resolve()),
    "training_owner_path": str(Path(first["dependencies"]["training_owner"].__file__).resolve()),
    "forward_helper_path": str(Path(first["forward"].__file__).resolve()),
    "backward_helper_path": str(Path(first["backward"].__file__).resolve()),
    "batch_backward_helper_path": str(Path(first["batch_backward"].__file__).resolve()),
    "same_modules_on_second_call": True,
    "tripwire_calls": len(calls),
    "checkpoint_read": False,
    "carrier_built": False,
    "runtime_created": False,
    "model_instantiated": False,
    "forward_executed": False,
    "loss_executed": False,
    "backward_executed": False,
    "optimizer_created": False,
    "trainer_created": False,
}, sort_keys=True))
'''
    environment = os.environ.copy()
    for name in (
        REAL_BACKWARD_OPT_IN_V1,
        "COVAPIE_RUN_TRAIN12_CHECKPOINT_FORWARD_NO_UPDATE",
        "COVAPIE_RUN_TRAIN10_CHECKPOINT_BACKWARD_NO_UPDATE",
        "COVAPIE_RUN_TRAIN10_CHECKPOINT_FORWARD_NO_UPDATE",
        "COVAPIE_RUN_BATCH001_CHECKPOINT_FORWARD_NO_UPDATE",
        "COVAPIE_RUN_BATCH001_CHECKPOINT_BACKWARD_NO_UPDATE",
        "COVAPIE_RUN_BATCH001_CHECKPOINT_SINGLE_OPTIMIZER_STEP",
        "COVAPIE_RUN_TRAIN10_BOUNDED_FIT",
        "COVAPIE_TRAIN12_FORWARD_ADAPTER_CANDIDATE",
        "COVAPIE_TRAIN12_COMPOSER_CANDIDATE",
        "COVAPIE_TRAIN10_FORWARD_ADAPTER_CANDIDATE",
        "COVAPIE_TRAIN10_COMPOSER_CANDIDATE",
        "COVAPIE_ADAPTER_CANDIDATE",
        "PYTHONOPTIMIZE",
        "PYTEST_ADDOPTS",
    ):
        environment.pop(name, None)
    environment.update({
        "COVAPIE_FRESH_PROCESS_CANDIDATE": str(Path(__file__).resolve(strict=True)),
        "COVAPIE_TEST_REPOSITORY_ROOT": str(ROOT),
        "COVAPIE_TEST_STATE_ROOT": str(STATE_ROOT),
        "COVAPIE_TEST_CACHE_ROOT": str(CACHE_ROOT),
        "PYTHONPATH": f"{ROOT / 'src'}:{ROOT}",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUNBUFFERED": "1",
    })
    completed = subprocess.run(
        [sys.executable, "-B", "-c", child_code],
        cwd=ROOT,
        env=environment,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stdout
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    assert len(lines) == 1, completed.stdout
    result = json.loads(lines[0])
    assert result["compat_before"] is False
    assert result["compat_after"] is True
    assert result["same_modules_on_second_call"] is True
    assert result["tripwire_calls"] == 0
    for key in (
        "checkpoint_read",
        "carrier_built",
        "runtime_created",
        "model_instantiated",
        "forward_executed",
        "loss_executed",
        "backward_executed",
        "optimizer_created",
        "trainer_created",
    ):
        assert result[key] is False
    print("FRESH_PROCESS_DEPENDENCY_IMPORT=" + lines[0], flush=True)


def test_real_checkpoint_train12_forward_backward_without_update() -> None:
    _execute_real_path_if_enabled_v1()
