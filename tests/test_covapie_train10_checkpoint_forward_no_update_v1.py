"""Opt-in train10 real-checkpoint forward/replay validation V1.

Ordinary collection and execution are deliberately non-model-only.  The sole
real path is guarded by
``COVAPIE_RUN_TRAIN10_CHECKPOINT_FORWARD_NO_UPDATE=1`` and checks that guard
before checkpoint access, carrier construction, model construction, or runtime
directory creation.  A real run is limited to one checkpoint load, one model,
one epoch-0/seed-0 train10 carrier, and two same-RNG forwards without updates.
"""

from __future__ import annotations

import ast
import contextlib
from dataclasses import dataclass, fields, is_dataclass
import functools
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
from types import SimpleNamespace
from typing import Callable, Iterator, Mapping
from unittest import mock

import pytest
import torch


TASK_ID_V1 = "validate_covapie_train10_checkpoint_forward_no_update_v1"
REAL_FORWARD_OPT_IN_V1 = (
    "COVAPIE_RUN_TRAIN10_CHECKPOINT_FORWARD_NO_UPDATE"
)
EXPECTED_REPOSITORY_BASELINE_V1 = (
    "c6f9b3c0cc9af4f9616b101c9b7fb8321c579fe1"
)
EXPECTED_CHECKPOINT_SIZE_BYTES_V1 = 17_861_341
EXPECTED_CHECKPOINT_SHA256_V1 = (
    "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
)
MODEL_INITIALIZATION_SEED_V1 = 20_260_821
DIFFUSION_FORWARD_SEED_V1 = 11_030_037
DETERMINISM_ABSOLUTE_TOLERANCE_V1 = 1.0e-7
DETERMINISM_RELATIVE_TOLERANCE_V1 = 1.0e-7
COORDINATE_ABSOLUTE_TOLERANCE_V1 = 1.0e-5
COORDINATE_RELATIVE_TOLERANCE_V1 = 1.3e-6
POST_COMPONENT_V1 = 1

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


# An external test file must never infer these roots from test.__file__.
ROOT = _required_canonical_directory_v1("COVAPIE_TEST_REPOSITORY_ROOT")
STATE_ROOT = _required_canonical_directory_v1("COVAPIE_TEST_STATE_ROOT")
CACHE_ROOT = _required_canonical_directory_v1("COVAPIE_TEST_CACHE_ROOT")
assert CACHE_ROOT == STATE_ROOT / "bulk-multisource-cys-sg-v1/rcsb"


# Exact published sources directly consumed by this test, beyond the adapter's
# own fixed six-source inventory and the composer's recursively checked inputs.
# Expectations are from the requested published baseline, never learned from
# arbitrary runtime content.
BOUND_SOURCE_SHA256_V1 = (
    (
        "tests/test_covapie_batch001_checkpoint_forward_no_update_v1.py",
        "2bac1568af875b200829f9854497a07587339c2587b501bf3d54ef7720bc2bdb",
    ),
    (
        "src/covalent_ext/covapie_train10_hidden_post_forward_adapter_v1.py",
        "5beaa700e2e5af87265c022a919dddfe1c8054114a45415adc416e5fe25fa40d",
    ),
    (
        "src/covalent_ext/covapie_train10_cpu_batch_composer_v1.py",
        "5c5e7fee4804586e0c6d2a9bdf39a301dd154da92ff2d029f971d6b2b77d2ddd",
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
        "src/covalent_ext/"
        "covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1.py",
        "3f19d39148f374d14744fa714a2e7d648a37099168d539c14e7e2320d390ec21",
    ),
    (
        "src/covalent_ext/"
        "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1.py",
        "1d80862e7c4fa3215ac3f307a45ce3bc8f1e0d4613728133a0ea3118df2df241",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1/"
        "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_manifest.json",
        "24cb60ca4f080a72e8c60aef63d105d82ec2f432eecc9b90f3341f52576bb6e0",
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


def _sha256_v1(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_file_identity_v1(path: Path) -> tuple[int, str]:
    metadata = path.lstat()
    assert stat.S_ISREG(metadata.st_mode) and not path.is_symlink()
    return metadata.st_size, _sha256_v1(path)


def _verify_bound_sources_v1() -> tuple[tuple[str, str], ...]:
    observed = []
    for relative, expected in BOUND_SOURCE_SHA256_V1:
        size, actual = _safe_file_identity_v1(ROOT / relative)
        assert size > 0 and actual == expected, relative
        observed.append((relative, actual))
    return tuple(observed)


def _evidence_v1(message: str) -> None:
    print(f"COVAPIE_EVIDENCE {message}", flush=True)


def _exception_chain_v1(error: BaseException) -> tuple[BaseException, ...]:
    chain = []
    seen = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen:
        chain.append(current)
        seen.add(id(current))
        if current.__cause__ is not None:
            current = current.__cause__
        elif current.__context__ is not None and not current.__suppress_context__:
            current = current.__context__
        else:
            current = None
    return tuple(chain)


def _report_primary_failure_v1(
    *,
    primary: BaseException,
    phase: str,
    call_counts: Mapping[str, object],
    emitter: Callable[[str], None] = _evidence_v1,
) -> None:
    """Best-effort reporting that can never replace the primary exception."""

    chain = _exception_chain_v1(primary)
    lines = [
        "real_path_failure=PRIMARY "
        f"phase={phase} type={type(chain[0]).__name__} "
        f"message={str(chain[0])!r}"
    ]
    lines.extend(
        "real_path_failure_chain="
        f"{index} type={type(item).__name__} message={str(item)!r}"
        for index, item in enumerate(chain[1:], start=1)
    )
    lines.append(
        "real_path_call_counts="
        + json.dumps(call_counts, sort_keys=True, default=str)
    )
    try:
        for line in lines:
            emitter(line)
    except BaseException as secondary:
        primary.add_note(
            "secondary_reporting_error="
            f"{type(secondary).__name__}:{secondary}"
        )
        fallback = "\n".join(lines + [
            "SECONDARY_REPORTING_ERROR "
            f"type={type(secondary).__name__} message={str(secondary)!r}"
        ])
        try:
            print(fallback, file=sys.stderr, flush=True)
        except BaseException as tertiary:
            primary.add_note(
                "tertiary_reporting_error="
                f"{type(tertiary).__name__}:{tertiary}"
            )


def _load_published_legacy_tools_v1() -> object:
    """Load only fixed, side-effect-free helpers from the old test module."""

    relative = "tests/test_covapie_batch001_checkpoint_forward_no_update_v1.py"
    expected = dict(BOUND_SOURCE_SHA256_V1)[relative]
    path = ROOT / relative
    assert _safe_file_identity_v1(path)[1] == expected
    name = "_covapie_published_batch001_forward_test_tools_v1"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        specification.loader.exec_module(module)
    assert stdout.getvalue() == "" and stderr.getvalue() == ""
    assert Path(module.__file__).resolve(strict=True) == path
    for helper in (
        "_snapshot_named_tensors",
        "_assert_snapshot_unchanged",
        "_model_state_fingerprint",
        "_assert_centering_and_fixed_node_contract",
    ):
        assert callable(getattr(module, helper))
    # No old test_*, main, runner, or old real entry point is invoked here.
    return module


def _coordinate_comparison_stats_v1(
    actual: torch.Tensor, expected: torch.Tensor
) -> dict[str, object]:
    """Report the exact joint atol/rtol rule used by the old float32 oracle."""

    assert actual.dtype == expected.dtype
    assert actual.shape == expected.shape
    assert torch.isfinite(actual).all() and torch.isfinite(expected).all()
    difference = (actual - expected).abs()
    allowed = (
        COORDINATE_ABSOLUTE_TOLERANCE_V1
        + COORDINATE_RELATIVE_TOLERANCE_V1 * expected.abs()
    )
    mismatch = difference > allowed
    maximum_absolute_flat = int(difference.reshape(-1).argmax().item())
    maximum_absolute_index = tuple(
        int(value)
        for value in torch.unravel_index(
            torch.tensor(maximum_absolute_flat), difference.shape
        )
    )
    relative = torch.where(
        expected != 0,
        difference / expected.abs(),
        torch.where(
            difference == 0,
            torch.zeros_like(difference),
            torch.full_like(difference, float("inf")),
        ),
    )
    maximum_relative_flat = int(relative.reshape(-1).argmax().item())
    maximum_relative_index = tuple(
        int(value)
        for value in torch.unravel_index(
            torch.tensor(maximum_relative_flat), relative.shape
        )
    )
    return {
        "mismatch_count": int(mismatch.sum().item()),
        "element_count": actual.numel(),
        "maximum_absolute_difference": float(
            difference[maximum_absolute_index].item()
        ),
        "maximum_absolute_index": maximum_absolute_index,
        "maximum_relative_difference": float(
            relative[maximum_relative_index].item()
        ),
        "maximum_relative_index": maximum_relative_index,
        "atol": COORDINATE_ABSOLUTE_TOLERANCE_V1,
        "rtol": COORDINATE_RELATIVE_TOLERANCE_V1,
    }


def _assert_coordinate_close_v1(
    *, stage: str, actual: torch.Tensor, expected: torch.Tensor
) -> None:
    stats = _coordinate_comparison_stats_v1(actual, expected)
    _evidence_v1(
        f"coordinate_oracle_stage={stage} "
        + json.dumps(stats, sort_keys=True)
    )
    torch.testing.assert_close(
        actual,
        expected,
        atol=COORDINATE_ABSOLUTE_TOLERANCE_V1,
        rtol=COORDINATE_RELATIVE_TOLERANCE_V1,
        msg=lambda message: f"{stage}: {message}",
    )


def _train10_initial_centering_v1(
    *,
    ligand_xh: torch.Tensor,
    pocket_xh: torch.Tensor,
    ligand_mask: torch.Tensor,
    pocket_mask: torch.Tensor,
    fixed: torch.Tensor,
    task_ids: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Mirror the published mixed-task scatter reduction, test-side only."""

    from torch_scatter import scatter_mean

    assert ligand_xh.ndim == pocket_xh.ndim == 2
    assert ligand_xh.shape[1] == pocket_xh.shape[1]
    assert ligand_mask.dtype == pocket_mask.dtype == torch.long
    assert fixed.dtype == torch.bool and fixed.shape == ligand_mask.shape
    assert task_ids.dtype == torch.long and task_ids.ndim == 1
    batch_size = len(task_ids)
    assert batch_size > 0
    assert int(ligand_mask.min().item()) == 0
    assert int(pocket_mask.min().item()) == 0
    assert int(ligand_mask.max().item()) == batch_size - 1
    assert int(pocket_mask.max().item()) == batch_size - 1
    task_c = task_ids == 4
    # This V1 oracle is scoped to the authorized mixed epoch0 train10 batch.
    assert bool(task_c.any().item()) and not bool(task_c.all().item())
    fixed_reference = scatter_mean(
        ligand_xh[:, :3][fixed],
        ligand_mask[fixed],
        dim=0,
        dim_size=batch_size,
    )
    assert torch.isfinite(fixed_reference[~task_c]).all()
    ligand_reference = scatter_mean(
        ligand_xh[:, :3],
        ligand_mask,
        dim=0,
        dim_size=batch_size,
    )
    reference = torch.where(task_c.unsqueeze(1), ligand_reference, fixed_reference)
    centered_ligand = ligand_xh.clone()
    centered_pocket = pocket_xh.clone()
    centered_ligand[:, :3] = (
        centered_ligand[:, :3] - reference[ligand_mask]
    )
    centered_pocket[:, :3] = (
        centered_pocket[:, :3] - reference[pocket_mask]
    )
    assert torch.equal(centered_ligand[:, 3:], ligand_xh[:, 3:])
    assert torch.equal(centered_pocket[:, 3:], pocket_xh[:, 3:])
    return centered_ligand, centered_pocket, reference


def _train10_task_c_second_translation_v1(
    *,
    noised_ligand_xh: torch.Tensor,
    centered_pocket_xh: torch.Tensor,
    ligand_mask: torch.Tensor,
    pocket_mask: torch.Tensor,
    task_ids: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Apply the published mixed-branch Task C scatter translation."""

    from torch_scatter import scatter_mean

    batch_size = len(task_ids)
    task_c = task_ids == 4
    assert bool(task_c.any().item()) and not bool(task_c.all().item())
    translation = scatter_mean(
        noised_ligand_xh[:, :3],
        ligand_mask,
        dim=0,
        dim_size=batch_size,
    )
    translated_ligand = noised_ligand_xh.clone()
    translated_pocket = centered_pocket_xh.clone()
    translated_ligand[:, :3] = torch.where(
        task_c[ligand_mask].unsqueeze(1),
        translated_ligand[:, :3] - translation[ligand_mask],
        translated_ligand[:, :3],
    )
    translated_pocket[:, :3] = torch.where(
        task_c[pocket_mask].unsqueeze(1),
        translated_pocket[:, :3] - translation[pocket_mask],
        translated_pocket[:, :3],
    )
    assert torch.equal(translated_ligand[:, 3:], noised_ligand_xh[:, 3:])
    assert torch.equal(translated_pocket[:, 3:], centered_pocket_xh[:, 3:])
    return translated_ligand, translated_pocket, translation


def _assert_train10_centering_and_fixed_node_contract_v1(
    *,
    model: object,
    carrier: object,
    transported: tuple[dict[str, object], dict[str, object]],
    output: object,
) -> None:
    """Independent train10 oracle with published mixed-branch operation order."""

    ligand, pocket = transported
    ligand_copy = {
        name: value.clone() if isinstance(value, torch.Tensor) else value
        for name, value in ligand.items()
    }
    pocket_copy = {
        name: value.clone() if isinstance(value, torch.Tensor) else value
        for name, value in pocket.items()
    }
    assert model.ddpm.norm_values == [1, 4]
    assert tuple(model.ddpm.norm_biases) == (None, 0.0)
    normalized_ligand, normalized_pocket = model.ddpm.normalize(
        ligand_copy, pocket_copy
    )
    supervision = carrier.supervision
    ligand_mask = ligand["mask"]
    pocket_mask = pocket["mask"]
    generation = supervision.ligand_base_generation_mask
    fixed = supervision.ligand_base_fixed_mask[:, 0]
    task_ids = supervision.canonical_task_id
    trace = output.diffusion_trace
    raw_ligand_xh = torch.cat((
        normalized_ligand["x"].clone(),
        normalized_ligand["one_hot"].clone(),
    ), dim=1)
    raw_pocket_xh = torch.cat((
        normalized_pocket["x"].clone(),
        normalized_pocket["one_hot"].clone(),
    ), dim=1)
    expected_clean_ligand_xh, expected_pocket_xh, _reference = (
        _train10_initial_centering_v1(
            ligand_xh=raw_ligand_xh,
            pocket_xh=raw_pocket_xh,
            ligand_mask=ligand_mask,
            pocket_mask=pocket_mask,
            fixed=fixed,
            task_ids=task_ids,
        )
    )
    assert torch.equal(
        trace.clean_centered_ligand_xh[:, 3:],
        expected_clean_ligand_xh[:, 3:],
    )
    _assert_coordinate_close_v1(
        stage="initial_clean_centering",
        actual=trace.clean_centered_ligand_xh,
        expected=expected_clean_ligand_xh,
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
    expected_noised_ligand_xh, expected_pocket_xh, _translation = (
        _train10_task_c_second_translation_v1(
            noised_ligand_xh=expected_noised_ligand_xh,
            centered_pocket_xh=expected_pocket_xh,
            ligand_mask=ligand_mask,
            pocket_mask=pocket_mask,
            task_ids=task_ids,
        )
    )
    assert torch.equal(
        trace.noised_ligand_xh[:, 3:], expected_noised_ligand_xh[:, 3:]
    )
    assert torch.equal(
        trace.clean_centered_pocket_xh[:, 3:], expected_pocket_xh[:, 3:]
    )
    _assert_coordinate_close_v1(
        stage="task_c_post_noise_second_translation",
        actual=trace.noised_ligand_xh,
        expected=expected_noised_ligand_xh,
    )
    _assert_coordinate_close_v1(
        stage="pocket_common_translation",
        actual=trace.clean_centered_pocket_xh,
        expected=expected_pocket_xh,
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
    _evidence_v1(
        "coordinate_and_fixed_node_contract=PASS "
        "initial_scatter_centering=true task_c_second_scatter_translation=true "
        "pocket_common_translation=true feature_channels_unchanged_by_translation=true "
        "fixed_noise_zero=true update_mask=true fixed_restore=true"
    )


def _update_fingerprint_v1(
    digest: "hashlib._Hash", value: object, path: str
) -> None:
    digest.update(path.encode("utf-8"))
    digest.update(type(value).__qualname__.encode("utf-8"))
    if isinstance(value, torch.Tensor):
        tensor = value.detach().contiguous().cpu()
        digest.update(str(tensor.dtype).encode("ascii"))
        digest.update(str(tuple(tensor.shape)).encode("ascii"))
        digest.update(tensor.view(-1).view(torch.uint8).numpy().tobytes())
    elif is_dataclass(value):
        for field in fields(value):
            _update_fingerprint_v1(
                digest, getattr(value, field.name), f"{path}.{field.name}"
            )
    elif isinstance(value, dict):
        for key, item in value.items():
            _update_fingerprint_v1(digest, key, f"{path}.key")
            _update_fingerprint_v1(digest, item, f"{path}[{key!r}]")
    elif isinstance(value, (tuple, list)):
        for index, item in enumerate(value):
            _update_fingerprint_v1(digest, item, f"{path}[{index}]")
    elif isinstance(value, Path):
        digest.update(str(value).encode("utf-8"))
    elif value is None or type(value) in (bool, int, str):
        digest.update(repr(value).encode("utf-8"))
    elif type(value) is float:
        digest.update(value.hex().encode("ascii"))
    else:
        raise TypeError(f"unsupported fingerprint value at {path}: {type(value)}")


def _fingerprint_value_v1(value: object) -> str:
    digest = hashlib.sha256()
    _update_fingerprint_v1(digest, value, "root")
    return digest.hexdigest()


def _compare_replay_value_v1(
    first: object, second: object, path: str = "output"
) -> float:
    """Compare tensors NaN-aware and all discrete metadata exactly."""

    assert type(first) is type(second), path
    if isinstance(first, torch.Tensor):
        assert first.dtype == second.dtype, path
        assert first.shape == second.shape, path
        assert first.device == second.device, path
        maximum = 0.0
        if torch.is_floating_point(first):
            assert torch.equal(torch.isnan(first), torch.isnan(second)), path
            assert torch.equal(torch.isposinf(first), torch.isposinf(second)), path
            assert torch.equal(torch.isneginf(first), torch.isneginf(second)), path
            finite = torch.isfinite(first) & torch.isfinite(second)
            torch.testing.assert_close(
                first,
                second,
                atol=DETERMINISM_ABSOLUTE_TOLERANCE_V1,
                rtol=DETERMINISM_RELATIVE_TOLERANCE_V1,
                equal_nan=True,
                msg=lambda message: f"{path}: {message}",
            )
            if bool(finite.any().item()):
                maximum = float(
                    (first[finite] - second[finite]).abs().max().item()
                )
        else:
            assert torch.equal(first, second), path
        return maximum
    if is_dataclass(first):
        maximum = 0.0
        for field in fields(first):
            maximum = max(maximum, _compare_replay_value_v1(
                getattr(first, field.name),
                getattr(second, field.name),
                f"{path}.{field.name}",
            ))
        return maximum
    if isinstance(first, dict):
        assert tuple(first) == tuple(second), path
        maximum = 0.0
        for key in first:
            maximum = max(maximum, _compare_replay_value_v1(
                first[key], second[key], f"{path}[{key!r}]"
            ))
        return maximum
    if isinstance(first, (tuple, list)):
        assert len(first) == len(second), path
        maximum = 0.0
        for index, (left, right) in enumerate(zip(first, second, strict=True)):
            maximum = max(maximum, _compare_replay_value_v1(
                left, right, f"{path}[{index}]"
            ))
        return maximum
    if type(first) is float and math.isnan(first):
        assert math.isnan(second), path
    else:
        assert first == second, path
    return 0.0


def _new_call_stats_v1() -> dict[str, object]:
    return {
        "requested": 0,
        "returned": 0,
        "records": [],
        "secondary_errors": [],
    }


def _transparent_observer_v1(
    original: Callable[..., object],
    *,
    stats: dict[str, object],
    projector: Callable[[tuple[object, ...], dict[str, object], object], object],
    failure_reporter: Callable[[BaseException], None] | None = None,
) -> Callable[..., object]:
    """Observe one unchanged call; observer failures remain secondary."""

    signature = inspect.signature(original)

    @functools.wraps(original)
    def observed(*args: object, **kwargs: object) -> object:
        signature.bind(*args, **kwargs)
        stats["requested"] = int(stats["requested"]) + 1
        try:
            result = original(*args, **kwargs)
        except BaseException as primary:
            if failure_reporter is not None:
                try:
                    failure_reporter(primary)
                except BaseException as secondary:
                    stats["secondary_errors"].append(
                        f"{type(secondary).__name__}:{secondary}"
                    )
                    primary.add_note(
                        "secondary_observer_error="
                        f"{type(secondary).__name__}:{secondary}"
                    )
            raise
        stats["returned"] = int(stats["returned"]) + 1
        try:
            stats["records"].append(projector(args, kwargs, result))
        except BaseException as secondary:
            stats["secondary_errors"].append(
                f"{type(secondary).__name__}:{secondary}"
            )
        return result

    observed.__signature__ = signature  # type: ignore[attr-defined]
    assert inspect.signature(observed) == signature
    return observed


def _attribute_names_in_function_v1(
    relative_path: str, *, class_name: str | None, function_name: str
) -> frozenset[str]:
    tree = ast.parse((ROOT / relative_path).read_text(encoding="utf-8"))
    body = tree.body
    if class_name is not None:
        owner = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == class_name
        )
        body = owner.body
    function = next(
        node
        for node in body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == function_name
    )
    return frozenset(
        node.attr for node in ast.walk(function) if isinstance(node, ast.Attribute)
    )


def _hidden_post_eligibility_oracle_v1(carrier: object) -> tuple[int, ...]:
    """Independent scalar oracle for actual hidden-POST loss eligibility."""

    supervision = carrier.supervision
    ligand_membership = carrier.model_input_batch["lig_mask"]
    pocket_membership = carrier.model_input_batch["pocket_mask"]
    eligible = []
    for sample in range(len(carrier.sample_identities)):
        positive = int(supervision.pair_positive_candidate_index[sample].item())
        ligand_flat = int(
            supervision.pair_candidate_ligand_flat_index[positive].item()
        )
        pocket_flat = int(
            supervision.pair_candidate_pocket_flat_index[positive].item()
        )
        checks = (
            bool(supervision.sample_training_admitted[sample].item()),
            bool(supervision.canonical_task_valid[sample].item()),
            bool(supervision.target_residue_condition_valid[sample].item()),
            bool(supervision.pair_positive_candidate_valid[sample].item()),
            bool(supervision.pre_post_geometry_component_valid_mask[
                sample, POST_COMPONENT_V1
            ].item()),
            bool(supervision.pre_post_geometry_component_loss_mask[
                sample, POST_COMPONENT_V1
            ].item()),
            bool(supervision.pair_candidate_is_positive[positive].item()),
            int(supervision.pair_candidate_batch_index[positive].item()) == sample,
            int(ligand_membership[ligand_flat].item()) == sample,
            int(pocket_membership[pocket_flat].item()) == sample,
            pocket_flat == int(
                supervision.target_residue_reactive_atom_flat_index[sample].item()
            ),
            bool(supervision.ligand_role_valid[ligand_flat].item()),
            int(supervision.ligand_role_id[ligand_flat].item()) == 2,
            bool(supervision.ligand_base_generation_mask[
                ligand_flat, 0
            ].item()),
            not bool(supervision.ligand_base_fixed_mask[ligand_flat, 0].item()),
        )
        if all(checks):
            eligible.append(sample)
    return tuple(eligible)


def _carrier_measurements_v1(carrier: object) -> dict[str, object]:
    supervision = carrier.supervision
    ligand_mask = carrier.model_input_batch["lig_mask"]
    generation_counts = tuple(
        int(supervision.ligand_base_generation_mask[
            ligand_mask == sample
        ].sum().item())
        for sample in range(len(carrier.sample_identities))
    )
    fixed_counts = tuple(
        int(supervision.ligand_base_fixed_mask[
            ligand_mask == sample
        ].sum().item())
        for sample in range(len(carrier.sample_identities))
    )
    c_seed_counts = tuple(
        int(supervision.ligand_minimal_seed_or_anchor_mask[
            ligand_mask == sample
        ].sum().item())
        for sample, task in enumerate(carrier.scheduled_task_ids)
        if task == 4
    )
    return {
        "tasks": tuple(int(value) for value in carrier.scheduled_task_ids),
        "ligand_shape": tuple(carrier.model_input_batch["lig_coords"].shape),
        "ligand_one_hot_shape": tuple(
            carrier.model_input_batch["lig_one_hot"].shape
        ),
        "pocket_shape": tuple(carrier.model_input_batch["pocket_coords"].shape),
        "pocket_one_hot_shape": tuple(
            carrier.model_input_batch["pocket_one_hot"].shape
        ),
        "generated_counts": generation_counts,
        "fixed_counts": fixed_counts,
        "task_c_seed_counts": c_seed_counts,
        "hidden_post_eligible": _hidden_post_eligibility_oracle_v1(carrier),
        "payload_sha256": carrier.payload_sha256,
    }


@dataclass(frozen=True)
class _ModelSnapshotV1:
    parameter_values: dict[str, object]
    buffer_values: dict[str, object]
    parameter_object_ids: tuple[tuple[str, int], ...]
    state_dict_keys: tuple[str, ...]
    requires_grad_flags: tuple[tuple[str, bool], ...]
    gradient_states: tuple[tuple[str, object | None], ...]
    state_fingerprint: str
    configuration_fingerprint: str


def _model_configuration_snapshot_v1(model: object) -> dict[str, object]:
    ddpm = model.ddpm
    dynamics = ddpm.dynamics
    distribution = ddpm.size_distribution
    weights = model.covapie_current11_loss_weights
    return {
        "class": f"{type(model).__module__}.{type(model).__qualname__}",
        "batch_size": model.batch_size,
        "mode": model.mode,
        "pocket_representation": model.pocket_representation,
        "atom_nf": model.atom_nf,
        "aa_nf": model.aa_nf,
        "virtual_nodes": model.virtual_nodes,
        "auxiliary_loss": model.auxiliary_loss,
        "target_residue_atom_conditioning": (
            model.target_residue_atom_conditioning
        ),
        "training": model.training,
        "ddpm_training": ddpm.training,
        "current_epoch": model.current_epoch,
        "trainer_attached": model._trainer is not None,
        "diffusion_steps": ddpm.T,
        "loss_type": ddpm.loss_type,
        "parametrization": ddpm.parametrization,
        "normalization_values": tuple(ddpm.norm_values),
        "normalization_biases": tuple(ddpm.norm_biases),
        "dynamics_target_conditioning": (
            dynamics.target_residue_atom_conditioning
        ),
        "egnn_hidden_nf": dynamics.egnn.hidden_nf,
        "egnn_layer_count": dynamics.egnn.n_layers,
        "loss_weights": tuple(
            (field.name, getattr(weights, field.name)) for field in fields(weights)
        ),
        "node_prior_probability": distribution.prob.detach().clone(),
        "node_prior_index": distribution.idx_to_n_nodes.detach().clone(),
        "node_prior_mapping": tuple(sorted(distribution.n_nodes_to_idx.items())),
        "node_prior_categorical_probability": (
            distribution.m.probs.detach().clone()
        ),
    }


def _capture_model_snapshot_v1(model: object) -> _ModelSnapshotV1:
    tools = _load_published_legacy_tools_v1()
    named_parameters = tuple(model.named_parameters())
    named_buffers = tuple(model.named_buffers())
    parameter_values = tools._snapshot_named_tensors(iter(named_parameters))
    buffer_values = tools._snapshot_named_tensors(iter(named_buffers))
    gradient_states = tuple(
        (
            name,
            None if parameter.grad is None else parameter.grad.detach().clone(),
        )
        for name, parameter in named_parameters
    )
    assert all(value is None for _name, value in gradient_states)
    configuration = _model_configuration_snapshot_v1(model)
    return _ModelSnapshotV1(
        parameter_values=parameter_values,
        buffer_values=buffer_values,
        parameter_object_ids=tuple(
            (name, id(parameter)) for name, parameter in named_parameters
        ),
        state_dict_keys=tuple(model.state_dict()),
        requires_grad_flags=tuple(
            (name, bool(parameter.requires_grad))
            for name, parameter in named_parameters
        ),
        gradient_states=gradient_states,
        state_fingerprint=tools._model_state_fingerprint(
            parameter_values, buffer_values
        ),
        configuration_fingerprint=_fingerprint_value_v1(configuration),
    )


def _assert_model_snapshot_unchanged_v1(
    snapshot: _ModelSnapshotV1, model: object
) -> None:
    tools = _load_published_legacy_tools_v1()
    named_parameters = tuple(model.named_parameters())
    named_buffers = tuple(model.named_buffers())
    assert tuple((name, id(value)) for name, value in named_parameters) == (
        snapshot.parameter_object_ids
    )
    assert tuple(model.state_dict()) == snapshot.state_dict_keys
    assert tuple(
        (name, bool(value.requires_grad)) for name, value in named_parameters
    ) == snapshot.requires_grad_flags
    assert all(value.grad is None for _name, value in named_parameters)
    tools._assert_snapshot_unchanged(
        snapshot.parameter_values, iter(named_parameters)
    )
    tools._assert_snapshot_unchanged(snapshot.buffer_values, iter(named_buffers))
    current_parameters = tools._snapshot_named_tensors(iter(named_parameters))
    current_buffers = tools._snapshot_named_tensors(iter(named_buffers))
    assert tools._model_state_fingerprint(
        current_parameters, current_buffers
    ) == snapshot.state_fingerprint
    assert _fingerprint_value_v1(
        _model_configuration_snapshot_v1(model)
    ) == snapshot.configuration_fingerprint


def _loss_values_v1(output: object) -> dict[str, float]:
    losses = output.loss_output
    return {
        "base": float(losses.loss_base_diffusion.detach().item()),
        "pair": float(losses.loss_covalent_pair_prediction.detach().item()),
        "geometry": float(losses.loss_pre_post_geometry.detach().item()),
        "contrastive": float(
            losses.loss_covalent_pair_contrastive.detach().item()
        ),
        "total": float(losses.loss_total.detach().item()),
    }


def _loss_counts_v1(output: object) -> dict[str, int]:
    losses = output.loss_output
    return {
        "base": losses.base_diffusion_valid_sample_count,
        "pair": losses.covalent_pair_prediction_valid_sample_count,
        "geometry": losses.pre_post_geometry_valid_sample_count,
        "contrastive": losses.covalent_pair_contrastive_valid_sample_count,
    }


def _assert_diagnostic_validity_v1(
    diagnostic: torch.Tensor, valid: torch.Tensor
) -> None:
    assert diagnostic.shape == valid.shape
    assert valid.dtype == torch.bool
    assert torch.equal(torch.isfinite(diagnostic), valid)
    assert bool(torch.isnan(diagnostic[~valid]).all().item())


def _validate_forward_output_v1(
    *, round_index: int, output: object, carrier: object, model: object
) -> dict[str, object]:
    from covalent_ext.covapie_current11_training_lightning_module_v1 import (
        CovapieCurrent11TrainingForwardOutputV1,
    )

    assert type(output) is CovapieCurrent11TrainingForwardOutputV1
    assert output.supervision is carrier.supervision
    supervision = carrier.supervision
    trace = output.diffusion_trace
    model_output = output.model_output
    losses = output.loss_output
    batch_size = len(carrier.sample_identities)
    timesteps = trace.diffusion_timestep_int
    assert timesteps.dtype == torch.long and timesteps.shape == (batch_size,)
    assert bool(((timesteps >= 0) & (timesteps <= model.ddpm.T)).all().item())
    values = _loss_values_v1(output)
    assert all(math.isfinite(value) for value in values.values())

    eligible = _hidden_post_eligibility_oracle_v1(carrier)
    geometry_valid = torch.zeros(batch_size, dtype=torch.bool)
    geometry_valid[list(eligible)] = True
    pair_valid = supervision.pair_positive_candidate_valid
    contrastive_valid = supervision.pair_contrastive_sample_loss_mask
    admitted = supervision.sample_training_admitted
    _assert_diagnostic_validity_v1(
        losses.pair_prediction_per_sample_detached, pair_valid
    )
    _assert_diagnostic_validity_v1(
        losses.pre_post_geometry_per_sample_detached, geometry_valid
    )
    _assert_diagnostic_validity_v1(
        losses.pair_contrastive_per_sample_detached, contrastive_valid
    )
    counts = _loss_counts_v1(output)
    assert counts == {
        "base": int(admitted.sum().item()),
        "pair": int(pair_valid.sum().item()),
        "geometry": len(eligible),
        "contrastive": int(contrastive_valid.sum().item()),
    }

    finite_neural_tensors = (
        trace.diffusion_epsilon_prediction_ligand,
        trace.diffusion_epsilon_prediction_pocket,
        trace.noised_ligand_xh,
        trace.sampled_epsilon_ligand,
        trace.clean_centered_ligand_xh,
        trace.clean_centered_pocket_xh,
        trace.denoised_ligand_xh,
        trace.ligand_node_hidden,
        trace.pocket_node_hidden,
        trace.role_mask_anchor_hidden_delta,
        trace.base_objective_per_sample,
        model_output.diffusion_epsilon_prediction_ligand,
        model_output.denoised_ligand_xh,
        model_output.ligand_node_hidden,
        model_output.pocket_node_hidden,
        model_output.role_mask_anchor_hidden_delta,
        model_output.pair_embeddings,
        model_output.pair_logits,
        model_output.pre_post_geometry_predictions_angstrom,
        model_output.target_pair_consistency,
    )
    assert all(
        bool(torch.isfinite(value).all().item())
        for value in finite_neural_tensors
    )
    assert all(
        not tensor.requires_grad
        for tensor in finite_neural_tensors
        + (
            losses.loss_base_diffusion,
            losses.loss_covalent_pair_prediction,
            losses.loss_pre_post_geometry,
            losses.loss_covalent_pair_contrastive,
            losses.loss_total,
        )
    )
    assert model_output.canonical_task_id.equal(supervision.canonical_task_id)
    for name in (
        "pair_candidate_offsets",
        "pair_candidate_batch_index",
        "pair_candidate_ligand_local_index",
        "pair_candidate_residue_local_index",
        "pair_candidate_ligand_flat_index",
        "pair_candidate_pocket_flat_index",
    ):
        assert getattr(model_output, name).equal(getattr(supervision, name))

    measurements = _carrier_measurements_v1(carrier)
    result = {
        "round": round_index,
        "timesteps": tuple(int(value) for value in timesteps.tolist()),
        "raw_losses": values,
        "valid_counts": counts,
        "hidden_post_eligible": measurements["hidden_post_eligible"],
        "generated_counts": measurements["generated_counts"],
        "fixed_counts": measurements["fixed_counts"],
        "task_c_seed_counts": measurements["task_c_seed_counts"],
        "ligand_hidden_shape": tuple(trace.ligand_node_hidden.shape),
        "pocket_hidden_shape": tuple(trace.pocket_node_hidden.shape),
    }
    _evidence_v1(
        "forward_measurements=" + json.dumps(result, sort_keys=True)
    )
    return result


def _assert_train10_carrier_contract_v1(carrier: object) -> dict[str, object]:
    from covalent_ext import covapie_train10_cpu_batch_composer_v1 as composer
    from covalent_ext.covapie_current11_training_tensorizer_v1 import (
        CANONICAL_TASKS_V1,
    )

    assert type(carrier) is composer.CovapieTrain10CpuEpochBatchV1
    assert composer.validate_covapie_train10_cpu_epoch_batch_v1(carrier)
    assert carrier.epoch == 0 and carrier.task_schedule_seed == 0
    assert len(carrier.sample_identities) == 10
    assert tuple(CANONICAL_TASKS_V1) == CANONICAL_EXACT5_V1
    assert tuple(carrier.supervision.canonical_task_id.tolist()) == (
        carrier.scheduled_task_ids
    )
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
    assert carrier.source_branches == (
        ("BATCH001_FORMAL_TRAIN5_V1",) * 5
        + ("CURRENT11_LEGACY_TRAIN5_V1",) * 5
    )
    assert len(carrier.source_audit_blocks) == 6
    assert carrier.legacy_post_overlay_applied is False
    assert carrier.real_model_executed is False
    assert carrier.training_or_validation_executed is False
    assert carrier.parameter_update_performed is False
    assert carrier.ready_for_training is False
    assert carrier.feature_semantics_audit_required_later is True
    assert carrier.step12d_is_only_smoke_legality_check is True

    supervision = carrier.supervision
    assert supervision.pre_post_geometry_component_valid_mask[:5].tolist() == (
        [[False, True]] * 5
    )
    assert supervision.pre_post_geometry_component_loss_mask[:5].tolist() == (
        [[False, True]] * 5
    )
    assert supervision.pre_post_geometry_component_valid_mask[5:].tolist() == (
        [[False, False]] * 5
    )
    assert supervision.pre_post_geometry_component_loss_mask[5:].tolist() == (
        [[False, False]] * 5
    )
    assert torch.isfinite(
        supervision.pre_post_geometry_target_angstrom[:5, POST_COMPONENT_V1]
    ).all()
    assert torch.isnan(
        supervision.pre_post_geometry_target_angstrom[5:, POST_COMPONENT_V1]
    ).all()

    measurements = _carrier_measurements_v1(carrier)
    eligible = set(measurements["hidden_post_eligible"])
    # This is re-derived from the actual epoch-0 carrier, not inferred from the
    # 50 event-by-epoch coverage proof or from the ten admission flags.
    assert len(eligible) == 5
    first_half_c = 0
    second_half_c = 0
    ligand_mask = carrier.model_input_batch["lig_mask"]
    for sample, task in enumerate(carrier.scheduled_task_ids):
        sample_rows = ligand_mask == sample
        generation = supervision.ligand_base_generation_mask[sample_rows, 0]
        fixed = supervision.ligand_base_fixed_mask[sample_rows, 0]
        assert not bool((generation & fixed).any().item())
        assert bool((generation | fixed).all().item())
        if task == 3:
            # B3 remains part of Exact5, but its POST purpose is excluded.
            assert bool(generation.any().item())
            assert bool(fixed.any().item())
            assert sample not in eligible
        if task == 4:
            seed_valid = bool(
                supervision.ligand_minimal_seed_or_anchor_valid[sample].item()
            )
            seed_count = int(
                supervision.ligand_minimal_seed_or_anchor_mask[
                    sample_rows
                ].sum().item()
            )
            # Task C has no fixed ligand nodes on either source.  The legacy
            # seed is metadata/conditioning authority, not a fixed-node alias.
            assert int(fixed.sum().item()) == 0
            if sample < 5:
                first_half_c += 1
                assert seed_valid is False and seed_count == 0
            else:
                second_half_c += 1
                assert seed_valid is True and seed_count > 0
    assert first_half_c > 0 and second_half_c > 0
    return measurements


def _instantiate_train10_model_v1(
    *, checkpoint: dict[str, object], runtime_root: Path
) -> object:
    """Apply only the explicit train10 differences to published helpers."""

    import constants
    from covalent_ext import (
        checkpoint_compatible_model_instantiation as compatible_owner,
    )
    from covalent_ext import (
        covapie_current11_checkpoint_migration_and_real_one_batch_train_path_smoke_v1
        as constructor_owner,
    )
    from covalent_ext import (
        covapie_train10_hidden_post_forward_adapter_v1 as adapter,
    )

    legacy = checkpoint["legacy_constructor"]
    preview_result = compatible_owner.load_config_preview_v0(
        ROOT / compatible_owner.CONFIG_PREVIEW_PATH
    )
    assert preview_result["config_preview_loaded"] is True
    compatible = compatible_owner.build_checkpoint_compatible_config_v0(
        preview_result["preview"],
        ROOT / compatible_owner.BEST_CONFIG_CANDIDATE_PATH,
    )
    assert compatible["compatible_config_built"] is True
    config = compatible_owner._constructor_config_from_compatible_config(
        compatible,
        constructor_owner._DATASET_NAME_V1,
        "cpu",
        node_histogram=legacy["node_histogram"],
    )

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
    assert config["clip_grad"] is False and legacy["clip_grad"] is True

    legacy_setup = runtime_root / "legacy_setup_data"
    legacy_setup.mkdir(mode=0o700)
    config.update({
        "outdir": runtime_root / "model_output_not_persisted",
        "datadir": str(legacy_setup),
        "batch_size": 10,
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
        "covapie_train10_hidden_post_forward_enabled": True,
    })
    assert "covapie_batch001_hidden_post_forward_enabled" not in kwargs
    assert "covapie_current11_loss_weights" not in kwargs

    torch.random.default_generator.manual_seed(MODEL_INITIALIZATION_SEED_V1)
    dataset_name = config["dataset"]
    previous = constants.dataset_params.get(dataset_name)
    constants.dataset_params[dataset_name] = (
        compatible_owner._temporary_10d_dataset_info()
    )
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            model = adapter.CovapieTrain10HiddenPostForwardLigandPocketDDPMV1(
                **kwargs
            )
    finally:
        if previous is None:
            constants.dataset_params.pop(dataset_name, None)
        else:
            constants.dataset_params[dataset_name] = previous
    return model.to(torch.device("cpu"))


def _install_no_training_tripwires_v1(
    stack: contextlib.ExitStack, *, model: object | None = None
) -> list[str]:
    import pytorch_lightning as pl
    from lightning_modules import LigandPocketDDPM

    calls: list[str] = []

    def forbidden(name: str) -> Callable[..., None]:
        def tripwire(*_args: object, **_kwargs: object) -> None:
            calls.append(name)
            raise AssertionError(f"forbidden operation invoked: {name}")

        return tripwire

    direct_targets = (
        (torch.Tensor, "backward", "Tensor.backward"),
        (torch.autograd, "backward", "torch.autograd.backward"),
        (torch.autograd, "grad", "torch.autograd.grad"),
        (torch, "save", "torch.save"),
        (torch.jit, "save", "torch.jit.save"),
        (pl.Trainer, "__init__", "Trainer.__init__"),
        (pl.Trainer, "fit", "Trainer.fit"),
        (pl.Trainer, "validate", "Trainer.validate"),
        (pl.Trainer, "test", "Trainer.test"),
        (pl.Trainer, "predict", "Trainer.predict"),
        (pl.Trainer, "save_checkpoint", "Trainer.save_checkpoint"),
        (
            pl.LightningModule,
            "load_from_checkpoint",
            "LightningModule.load_from_checkpoint",
        ),
        (
            LigandPocketDDPM,
            "configure_optimizers",
            "LigandPocketDDPM.configure_optimizers",
        ),
        (LigandPocketDDPM, "training_step", "LigandPocketDDPM.training_step"),
        (
            LigandPocketDDPM,
            "validation_step",
            "LigandPocketDDPM.validation_step",
        ),
        (LigandPocketDDPM, "test_step", "LigandPocketDDPM.test_step"),
    )
    for owner, attribute, name in direct_targets:
        stack.enter_context(
            mock.patch.object(owner, attribute, new=forbidden(name))
        )
    if model is not None:
        for attribute in (
            "configure_optimizers",
            "training_step",
            "validation_step",
            "test_step",
        ):
            stack.enter_context(mock.patch.object(
                model,
                attribute,
                new=forbidden(f"model.{attribute}"),
            ))

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


def _call_count_view_v1(
    observations: Mapping[str, dict[str, object]]
) -> dict[str, object]:
    return {
        name: {
            "requested": int(stats["requested"]),
            "returned": int(stats["returned"]),
            "secondary_errors": tuple(stats["secondary_errors"]),
        }
        for name, stats in observations.items()
    }


def _patch_observer_v1(
    stack: contextlib.ExitStack,
    *,
    owner: object,
    attribute: str,
    stats: dict[str, object],
    projector: Callable[[tuple[object, ...], dict[str, object], object], object],
) -> None:
    original = getattr(owner, attribute)
    observed = _transparent_observer_v1(
        original,
        stats=stats,
        projector=projector,
        failure_reporter=lambda error: _evidence_v1(
            "observed_primary_exception="
            f"boundary={attribute} type={type(error).__name__} "
            f"message={str(error)!r}"
        ),
    )
    stack.enter_context(mock.patch.object(owner, attribute, new=observed))


def _clone_transport_v1(value: object) -> object:
    if isinstance(value, torch.Tensor):
        return value.detach().clone()
    if isinstance(value, dict):
        return {name: _clone_transport_v1(item) for name, item in value.items()}
    return value


def _assert_scoped_feature_use_prerequisites_v1() -> None:
    from covalent_ext import (
        covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1
        as feature_owner,
    )
    from covalent_ext.covapie_current11_training_tensorizer_v1 import (
        CANONICAL_TASKS_V1,
    )

    assert tuple(CANONICAL_TASKS_V1) == CANONICAL_EXACT5_V1
    assert feature_owner.CHECKPOINT_CHANNEL_ORDER == (
        "C:0|N:1|O:2|S:3|B:4|Br:5|Cl:6|P:7|I:8|F:9"
    )
    assert feature_owner.UNKNOWN_ATOM_POLICY == (
        "fail_closed_rejection_required_for_checkpoint_compatibility"
    )
    assert feature_owner.EXPLICIT_HYDROGEN_POLICY == (
        "exclude_before_checkpoint_model_projection"
    )
    manifest_relative = (
        "data/derived/covalent_small/"
        "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1/"
        "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_manifest.json"
    )
    manifest = json.loads((ROOT / manifest_relative).read_text(encoding="utf-8"))
    assert manifest["feature_semantics_known"] is True
    assert manifest["unknown_atom_feature_policy_resolved"] is True
    assert manifest["unknown_atom_policy_contract_resolved"] is True
    assert manifest["unknown_atom_runtime_enforcement_integrated"] is False
    assert manifest["observed_step12d_behavior_allowed_final_training_policy"] is False
    assert manifest["ready_for_model_integration"] is False
    assert manifest["ready_for_training"] is False
    assert manifest["training_used"] is False

    forbidden_post_attributes = {
        "pre_post_geometry_target_angstrom",
        "pair_prediction_per_sample_detached",
        "pre_post_geometry_per_sample_detached",
        "pair_contrastive_per_sample_detached",
    }
    auxiliary_source = (
        "src/covalent_ext/covapie_current11_auxiliary_model_and_loss_v1.py"
    )
    role_attributes = _attribute_names_in_function_v1(
        auxiliary_source,
        class_name="CovapieCurrent11AuxiliaryModelV1",
        function_name="encode_role_mask_anchor_v1",
    )
    auxiliary_attributes = _attribute_names_in_function_v1(
        auxiliary_source,
        class_name="CovapieCurrent11AuxiliaryModelV1",
        function_name="forward",
    )
    functional_attributes = _attribute_names_in_function_v1(
        "src/covalent_ext/covapie_current11_training_lightning_module_v1.py",
        class_name=None,
        function_name="run_covapie_current11_functional_dynamics_with_hidden_v1",
    )
    assert forbidden_post_attributes.isdisjoint(role_attributes)
    assert forbidden_post_attributes.isdisjoint(auxiliary_attributes)
    assert forbidden_post_attributes.isdisjoint(functional_attributes)

    adapter_source = (
        ROOT
        / "src/covalent_ext/covapie_train10_hidden_post_forward_adapter_v1.py"
    ).read_text(encoding="utf-8")
    assert "super().forward" not in adapter_source
    assert "tensorize_covapie_current11_training_supervision_v1" not in (
        adapter_source
    )
    assert "post_geometry_loss_purpose=TRAIN10_HIDDEN_POST_LOSS_PURPOSE_V1" in (
        adapter_source
    )

    constructor_source = inspect.getsource(_instantiate_train10_model_v1)
    assert "CovapieTrain10HiddenPostForwardLigandPocketDDPMV1" in constructor_source
    assert '"batch_size": 10' in constructor_source
    assert '"covapie_train10_hidden_post_forward_enabled": True' in (
        constructor_source
    )
    assert "CovapieBatch001HiddenPostForwardLigandPocketDDPMV1" not in (
        constructor_source
    )
    assert '"covapie_batch001_hidden_post_forward_enabled" not in kwargs' in (
        constructor_source
    )


def _load_real_path_dependencies_v1() -> dict[str, object]:
    """Import real-path owners only after the published adapter applies compat."""

    # This must remain the first real-owner import.  The published adapter owns
    # the established Biopython compatibility entry and imports the training
    # owner only after applying it.
    from covalent_ext import (
        covapie_train10_hidden_post_forward_adapter_v1 as adapter,
    )
    from Bio.PDB import Polypeptide

    assert hasattr(Polypeptide, "three_to_one")
    from covalent_ext import (
        covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1
        as checkpoint_locator,
    )
    from covalent_ext import (
        checkpoint_compatible_model_instantiation as compatible_owner,
    )
    from covalent_ext import (
        covapie_current11_checkpoint_migration_v1 as migration_owner,
    )
    from covalent_ext import (
        covapie_current11_training_lightning_module_v1 as training_owner,
    )
    from covalent_ext import (
        covapie_current11_training_tensorizer_v1 as tensorizer_owner,
    )
    from covalent_ext import (
        covapie_train10_cpu_batch_composer_v1 as composer_owner,
    )
    return {
        "adapter": adapter,
        "checkpoint_locator": checkpoint_locator,
        "compatible_owner": compatible_owner,
        "migration_owner": migration_owner,
        "training_owner": training_owner,
        "tensorizer_owner": tensorizer_owner,
        "composer_owner": composer_owner,
    }


def _run_real_checkpoint_validation_v1() -> None:

    phase = "dependency_import"
    observations = {
        name: _new_call_stats_v1()
        for name in (
            "checkpoint_deserialization",
            "model_initialization",
            "migration",
            "composer_prepare",
            "carrier_build",
            "model_forward",
            "transport",
            "role_encoding",
            "diffusion_bridge",
            "functional_dynamics",
            "egnn",
            "atom_encoder",
            "residue_encoder",
            "anchor_encoder",
            "pair_encoder",
            "auxiliary",
            "production_loss",
            "secondary_tensorization",
        )
    }
    rng_before_validation = torch.random.get_rng_state().clone()
    try:
        dependencies = _load_real_path_dependencies_v1()
        adapter = dependencies["adapter"]
        checkpoint_locator = dependencies["checkpoint_locator"]
        compatible_owner = dependencies["compatible_owner"]
        migration_owner = dependencies["migration_owner"]
        training_owner = dependencies["training_owner"]
        tensorizer_owner = dependencies["tensorizer_owner"]
        composer_owner = dependencies["composer_owner"]

        phase = "fixed_source_verification"
        fixed_sources_before = _verify_bound_sources_v1()
        adapter_sources_before = (
            adapter.verify_covapie_train10_hidden_post_forward_adapter_sources_v1(
                repository_root=ROOT
            )
        )
        _assert_scoped_feature_use_prerequisites_v1()
        assert checkpoint_locator.CHECKPOINT_RELATIVE_PATH_V1 == (
            compatible_owner.CHECKPOINT_PATH
        )
        assert not checkpoint_locator.CHECKPOINT_RELATIVE_PATH_V1.is_absolute()
        checkpoint_path = ROOT / checkpoint_locator.CHECKPOINT_RELATIVE_PATH_V1

        phase = "checkpoint_identity_before_deserialization"
        checkpoint_size, checkpoint_sha = _safe_file_identity_v1(checkpoint_path)
        assert checkpoint_size == EXPECTED_CHECKPOINT_SIZE_BYTES_V1
        assert checkpoint_sha == EXPECTED_CHECKPOINT_SHA256_V1
        assert checkpoint_size == (
            migration_owner.COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SIZE_BYTES_V1
        )
        assert checkpoint_sha == (
            migration_owner.COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SHA256_V1
        )
        _evidence_v1(
            "checkpoint_identity=PASS "
            f"relative_path={checkpoint_locator.CHECKPOINT_RELATIVE_PATH_V1} "
            f"bytes={checkpoint_size} sha256={checkpoint_sha} "
            "deserialized=false"
        )

        with contextlib.ExitStack() as stack:
            phase = "install_no_training_tripwires"
            tripwire_calls = _install_no_training_tripwires_v1(stack)

            _patch_observer_v1(
                stack,
                owner=migration_owner.torch,
                attribute="load",
                stats=observations["checkpoint_deserialization"],
                projector=lambda _args, _kwargs, result: {
                    "payload_type": type(result).__name__
                },
            )
            _patch_observer_v1(
                stack,
                owner=adapter.CovapieTrain10HiddenPostForwardLigandPocketDDPMV1,
                attribute="__init__",
                stats=observations["model_initialization"],
                projector=lambda _args, kwargs, _result: {
                    "batch_size": kwargs.get("batch_size"),
                    "train10_enabled": kwargs.get(
                        "covapie_train10_hidden_post_forward_enabled"
                    ),
                },
            )

            phase = "checkpoint_load"
            checkpoint = (
                migration_owner.load_covapie_current11_legacy_checkpoint_v1(
                    checkpoint_path=checkpoint_path
                )
            )
            assert observations["checkpoint_deserialization"]["requested"] == 1
            assert observations["checkpoint_deserialization"]["returned"] == 1
            assert checkpoint["checkpoint_size_bytes"] == checkpoint_size
            assert checkpoint["checkpoint_sha256"] == checkpoint_sha
            checkpoint_state = checkpoint["state_dict"]
            assert checkpoint["checkpoint_state_dict_key_count"] == len(
                checkpoint_state
            )
            _evidence_v1(
                "checkpoint_load=PASS "
                f"payload_type={checkpoint['checkpoint_payload_type']} "
                f"actual_legacy_state_keys={len(checkpoint_state)} "
                "loader_calls=1"
            )

            phase = "runtime_directory_creation"
            runtime_root = Path(tempfile.mkdtemp(
                prefix=(TASK_ID_V1 + "-"),
                dir=STATE_ROOT / "review-scratch",
            ))
            assert runtime_root.is_absolute() and runtime_root.is_dir()
            assert runtime_root.resolve(strict=True) == runtime_root
            _evidence_v1(f"runtime_preserved_path={runtime_root}")

            phase = "single_train10_model_initialization"
            model = _instantiate_train10_model_v1(
                checkpoint=checkpoint, runtime_root=runtime_root
            )
            assert observations["model_initialization"]["requested"] == 1
            assert observations["model_initialization"]["returned"] == 1
            model_tripwire_calls = _install_no_training_tripwires_v1(
                stack, model=model
            )

            phase = "strict_checkpoint_migration"
            target_state_before_migration = model.state_dict()
            target_keys = set(target_state_before_migration)
            checkpoint_keys = set(checkpoint_state)
            shared_keys = target_keys & checkpoint_keys
            target_only = target_keys - checkpoint_keys
            fresh_target_only = {
                key: target_state_before_migration[key].detach().clone()
                for key in target_only
            }
            observations["migration"]["requested"] = 1
            migration = (
                migration_owner.migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
                    model=model,
                    checkpoint_state_dict=checkpoint_state,
                )
            )
            observations["migration"]["returned"] = 1
            observations["migration"]["records"].append({
                "checkpoint_keys": migration["checkpoint_key_count"],
                "target_keys": migration["target_model_key_count"],
                "target_only": migration["target_only_key_count"],
            })
            migrated_state = model.state_dict()
            assert migration["checkpoint_key_count"] == len(checkpoint_keys)
            assert migration["target_model_key_count"] == len(target_keys)
            assert migration["shared_key_count"] == len(shared_keys)
            assert migration["target_only_key_count"] == len(target_only)
            assert migration["checkpoint_only_key_count"] == 0
            assert migration["shared_shape_mismatch_count"] == 0
            assert migration["migration_missing_keys"] == ()
            assert migration["migration_unexpected_keys"] == ()
            assert migration["full_target_strict_load"] is True
            assert migration["shared_checkpoint_tensor_equality_count"] == len(
                shared_keys
            )
            assert set(migration["target_only_exact_keys"]) == set(
                migration_owner.LEGACY_ALLOWED_NEW_EXACT_KEYS_V1
            )
            assert set(migration["target_only_auxiliary_keys"]) == {
                key
                for key in target_only
                if key.startswith(
                    migration_owner.LEGACY_ALLOWED_NEW_PREFIXES_V1
                )
            }
            assert target_only == (
                set(migration["target_only_exact_keys"])
                | set(migration["target_only_auxiliary_keys"])
            )
            for key in shared_keys:
                assert migrated_state[key].detach().cpu().equal(
                    checkpoint_state[key].detach().cpu()
                ), key
            for key in target_only:
                assert migrated_state[key].detach().cpu().equal(
                    fresh_target_only[key].detach().cpu()
                ), key
            _evidence_v1(
                "checkpoint_migration=PASS "
                f"actual_checkpoint_keys={len(checkpoint_keys)} "
                f"actual_target_keys={len(target_keys)} "
                f"actual_shared_keys={len(shared_keys)} "
                f"actual_target_only={len(target_only)} "
                f"actual_new_exact={len(migration['target_only_exact_keys'])} "
                f"actual_new_auxiliary={len(migration['target_only_auxiliary_keys'])} "
                "checkpoint_only=0 shape_mismatch=0 strict=true"
            )

            phase = "model_configuration_validation"
            legacy = checkpoint["legacy_constructor"]
            dynamics = model.ddpm.dynamics
            assert type(model) is (
                adapter.CovapieTrain10HiddenPostForwardLigandPocketDDPMV1
            )
            assert model.device == torch.device("cpu")
            assert model.batch_size == 10
            assert model.mode == legacy["mode"] == "pocket_conditioning"
            assert model.pocket_representation == legacy[
                "pocket_representation"
            ] == "full-atom"
            assert model.atom_nf == model.aa_nf == 10
            assert model.virtual_nodes is legacy["virtual_nodes"] is False
            assert model.auxiliary_loss is legacy["auxiliary_loss"] is False
            assert model.ddpm.loss_type == legacy["diffusion_params"][
                "diffusion_loss_type"
            ]
            assert model.ddpm.T == legacy["diffusion_params"]["diffusion_steps"]
            assert model.ddpm.norm_values == legacy["diffusion_params"][
                "normalize_factors"
            ]
            assert dynamics.target_residue_atom_conditioning is True
            assert dynamics.egnn.hidden_nf == legacy["egnn_params"]["hidden_nf"]
            assert dynamics.egnn.n_layers == legacy["egnn_params"]["n_layers"]
            assert model._trainer is None and model.current_epoch == 0
            assert model.ddpm.size_distribution.prob.shape == (
                len(legacy["node_histogram"]),
                len(legacy["node_histogram"][0]),
            )
            model.train()
            assert model.training is True and model.ddpm.training is True
            _evidence_v1(
                "model_configuration=PASS "
                f"class={type(model).__name__} batch_size={model.batch_size} "
                f"diffusion_steps={model.ddpm.T} "
                f"normalization={model.ddpm.norm_values} "
                f"node_prior_shape={tuple(model.ddpm.size_distribution.prob.shape)} "
                "full_atom=true target_residue_conditioning=true "
                "virtual_nodes=false training_mode=true trainer_attached=false"
            )

            phase = "single_epoch0_seed0_carrier_build"
            observations["composer_prepare"]["requested"] = 1
            prepared = composer_owner.prepare_covapie_train10_cpu_batch_composer_v1(
                ROOT, STATE_ROOT, CACHE_ROOT
            )
            observations["composer_prepare"]["returned"] = 1
            observations["carrier_build"]["requested"] = 1
            carrier = composer_owner.build_covapie_train10_cpu_epoch_batch_v1(
                prepared, 0, 0
            )
            observations["carrier_build"]["returned"] = 1
            carrier_measurements = _assert_train10_carrier_contract_v1(carrier)
            observations["carrier_build"]["records"].append(
                carrier_measurements
            )
            carrier_fingerprint = _fingerprint_value_v1(carrier)
            _evidence_v1(
                "train10_carrier=PASS "
                + json.dumps(carrier_measurements, sort_keys=True)
                + f" carrier_fingerprint={carrier_fingerprint}"
            )

            # The no-update baseline begins only after checkpoint migration and
            # carrier preparation have completed.
            phase = "post_migration_snapshot"
            model_snapshot = _capture_model_snapshot_v1(model)
            assert all(parameter.grad is None for parameter in model.parameters())
            _evidence_v1(
                "post_migration_snapshot=PASS "
                f"parameter_count={len(model_snapshot.parameter_values)} "
                f"buffer_count={len(model_snapshot.buffer_values)} "
                f"state_key_count={len(model_snapshot.state_dict_keys)} "
                f"state_fingerprint={model_snapshot.state_fingerprint} "
                f"configuration_fingerprint={model_snapshot.configuration_fingerprint} "
                f"carrier_fingerprint={carrier_fingerprint}"
            )

            phase = "transparent_observer_installation"
            _patch_observer_v1(
                stack,
                owner=model,
                attribute="forward",
                stats=observations["model_forward"],
                projector=lambda args, _kwargs, result: {
                    "carrier_identity": args[0] is carrier,
                    "supervision_identity": result.supervision is carrier.supervision,
                },
            )
            _patch_observer_v1(
                stack,
                owner=model,
                attribute="get_ligand_and_pocket",
                stats=observations["transport"],
                projector=lambda args, _kwargs, result: {
                    "model_input_identity": args[0] is carrier.model_input_batch,
                    "transported": _clone_transport_v1(result),
                },
            )
            _patch_observer_v1(
                stack,
                owner=model.covapie_current11_auxiliary_model_v1,
                attribute="encode_role_mask_anchor_v1",
                stats=observations["role_encoding"],
                projector=lambda _args, kwargs, result: {
                    "supervision_identity": kwargs["supervision"] is carrier.supervision,
                    "ligand_batch_identity": kwargs[
                        "ligand_batch_index"
                    ] is carrier.model_input_batch["lig_mask"],
                    "output_shape": tuple(result.shape),
                },
            )
            _patch_observer_v1(
                stack,
                owner=adapter,
                attribute="run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1",
                stats=observations["diffusion_bridge"],
                projector=lambda _args, kwargs, result: {
                    "supervision_identity": kwargs["supervision"] is carrier.supervision,
                    "role_shape": tuple(
                        kwargs["role_mask_anchor_hidden_delta"].shape
                    ),
                    "timestep_shape": tuple(result.diffusion_timestep_int.shape),
                },
            )
            _patch_observer_v1(
                stack,
                owner=training_owner,
                attribute="run_covapie_current11_functional_dynamics_with_hidden_v1",
                stats=observations["functional_dynamics"],
                projector=lambda _args, kwargs, result: {
                    "ligand_xh_shape": tuple(kwargs["xh_atoms"].shape),
                    "pocket_xh_shape": tuple(kwargs["xh_residues"].shape),
                    "coordinate_mask_equal": result.coordinate_update_mask[
                        : len(kwargs["mask_atoms"])
                    ].equal(kwargs["ligand_coordinate_update_mask"]),
                },
            )
            _patch_observer_v1(
                stack,
                owner=dynamics.egnn,
                attribute="forward",
                stats=observations["egnn"],
                projector=lambda args, _kwargs, result: {
                    "hidden_input_shape": tuple(args[0].shape),
                    "coordinate_input_shape": tuple(args[1].shape),
                    "hidden_output_shape": tuple(result[0].shape),
                    "coordinate_output_shape": tuple(result[1].shape),
                },
            )
            for owner, name in (
                (dynamics.atom_encoder, "atom_encoder"),
                (dynamics.residue_encoder, "residue_encoder"),
                (
                    model.covapie_current11_auxiliary_model_v1.anchor_distance_encoder[0],
                    "anchor_encoder",
                ),
                (
                    model.covapie_current11_auxiliary_model_v1.pair_embedding[0],
                    "pair_encoder",
                ),
            ):
                _patch_observer_v1(
                    stack,
                    owner=owner,
                    attribute="forward",
                    stats=observations[name],
                    projector=lambda args, _kwargs, result: {
                        "input_shape": tuple(args[0].shape),
                        "output_shape": tuple(result.shape),
                    },
                )
            _patch_observer_v1(
                stack,
                owner=model.covapie_current11_auxiliary_model_v1,
                attribute="forward",
                stats=observations["auxiliary"],
                projector=lambda _args, kwargs, result: {
                    "supervision_identity": kwargs["supervision"] is carrier.supervision,
                    "pair_shape": tuple(result.pair_logits.shape),
                    "geometry_shape": tuple(
                        result.pre_post_geometry_predictions_angstrom.shape
                    ),
                },
            )
            _patch_observer_v1(
                stack,
                owner=adapter,
                attribute="compute_covapie_current11_training_losses_v1",
                stats=observations["production_loss"],
                projector=lambda _args, kwargs, result: {
                    "purpose": kwargs["post_geometry_loss_purpose"],
                    "supervision_identity": kwargs["supervision"] is carrier.supervision,
                    "valid_counts": {
                        "base": result.base_diffusion_valid_sample_count,
                        "pair": result.covalent_pair_prediction_valid_sample_count,
                        "geometry": result.pre_post_geometry_valid_sample_count,
                        "contrastive": result.covalent_pair_contrastive_valid_sample_count,
                    },
                },
            )

            def forbidden_tensorization(
                *_args: object, **_kwargs: object
            ) -> None:
                observations["secondary_tensorization"]["requested"] = (
                    int(observations["secondary_tensorization"]["requested"]) + 1
                )
                raise AssertionError("secondary tensorization invoked during forward")

            stack.enter_context(mock.patch.object(
                tensorizer_owner,
                "tensorize_covapie_current11_training_supervision_v1",
                new=forbidden_tensorization,
            ))
            stack.enter_context(mock.patch.object(
                training_owner,
                "tensorize_covapie_current11_training_supervision_v1",
                new=forbidden_tensorization,
            ))

            weights = model.covapie_current11_loss_weights
            actual_weights = {
                field.name: getattr(weights, field.name) for field in fields(weights)
            }
            assert all(
                type(value) is float and math.isfinite(value)
                for value in actual_weights.values()
            )
            _evidence_v1(
                "production_default_loss_weights="
                + json.dumps(actual_weights, sort_keys=True)
            )

            phase = "first_real_forward"
            torch.manual_seed(DIFFUSION_FORWARD_SEED_V1)
            forward_rng_state = torch.random.get_rng_state().clone()
            _evidence_v1(
                "forward_seed_state=CAPTURED "
                f"model_initialization_seed={MODEL_INITIALIZATION_SEED_V1} "
                f"forward_seed={DIFFUSION_FORWARD_SEED_V1}"
            )
            _evidence_v1("full_forward_1=START requested_budget=1/2")
            with torch.no_grad():
                first = model(carrier)
            _evidence_v1("full_forward_1=RETURNED returned_count=1/2")
            first_measurements = _validate_forward_output_v1(
                round_index=1, output=first, carrier=carrier, model=model
            )
            # Immediate independent state check after forward one.
            _assert_model_snapshot_unchanged_v1(model_snapshot, model)
            assert _fingerprint_value_v1(carrier) == carrier_fingerprint
            _evidence_v1(
                "post_forward_1_invariance=PASS parameters=true buffers=true "
                "parameter_identity=true state_keys=true requires_grad=true "
                "gradients_none=true carrier_complete=true config_and_prior=true"
            )

            phase = "same_rng_replay_forward"
            torch.random.set_rng_state(forward_rng_state)
            _evidence_v1(
                "full_forward_2=START requested_budget=2/2 "
                "cpu_rng_restored=true model_reloaded=false carrier_rebuilt=false"
            )
            with torch.no_grad():
                second = model(carrier)
            _evidence_v1("full_forward_2=RETURNED returned_count=2/2")
            second_measurements = _validate_forward_output_v1(
                round_index=2, output=second, carrier=carrier, model=model
            )
            # Immediate independent state check after forward two, before replay.
            _assert_model_snapshot_unchanged_v1(model_snapshot, model)
            assert _fingerprint_value_v1(carrier) == carrier_fingerprint
            _evidence_v1(
                "post_forward_2_invariance=PASS parameters=true buffers=true "
                "parameter_identity=true state_keys=true requires_grad=true "
                "gradients_none=true carrier_complete=true config_and_prior=true"
            )

            phase = "replay_comparison"
            replay_maximum_difference = _compare_replay_value_v1(first, second)
            assert first_measurements["timesteps"] == second_measurements["timesteps"]
            _evidence_v1(
                "rng_replay_comparison=PASS "
                f"maximum_finite_absolute_difference={replay_maximum_difference} "
                f"atol={DETERMINISM_ABSOLUTE_TOLERANCE_V1} "
                f"rtol={DETERMINISM_RELATIVE_TOLERANCE_V1} "
                "nan_positions_equal=true dtype_shape_discrete_metadata_equal=true"
            )

            phase = "observer_and_neural_path_validation"
            twice = (
                "model_forward",
                "transport",
                "role_encoding",
                "diffusion_bridge",
                "functional_dynamics",
                "egnn",
                "atom_encoder",
                "residue_encoder",
                "anchor_encoder",
                "pair_encoder",
                "auxiliary",
                "production_loss",
            )
            for name in twice:
                assert observations[name]["requested"] == 2, name
                assert observations[name]["returned"] == 2, name
                assert observations[name]["secondary_errors"] == [], name
            assert observations["secondary_tensorization"]["requested"] == 0
            assert all(
                record["carrier_identity"] and record["supervision_identity"]
                for record in observations["model_forward"]["records"]
            )
            assert all(
                record["model_input_identity"]
                for record in observations["transport"]["records"]
            )
            assert all(
                record["purpose"] == "independent_hidden_post_distance_v1"
                and record["supervision_identity"]
                for record in observations["production_loss"]["records"]
            )
            ligand_count = len(carrier.model_input_batch["lig_mask"])
            pocket_count = len(carrier.model_input_batch["pocket_mask"])
            candidate_count = len(
                carrier.supervision.pair_candidate_batch_index
            )
            expected_anchor_rows = int((
                carrier.supervision.ligand_anchor_distance_valid
                & carrier.supervision.ligand_base_fixed_mask
                & ~carrier.supervision.ligand_base_generation_mask
            ).sum().item())
            assert expected_anchor_rows > 0
            assert all(
                record["input_shape"] == (ligand_count, 10)
                for record in observations["atom_encoder"]["records"]
            )
            assert all(
                record["input_shape"] == (pocket_count, 10)
                for record in observations["residue_encoder"]["records"]
            )
            assert all(
                record["hidden_input_shape"] == (
                    ligand_count + pocket_count, 33
                )
                for record in observations["egnn"]["records"]
            )
            assert all(
                record["input_shape"] == (expected_anchor_rows, 1)
                for record in observations["anchor_encoder"]["records"]
            )
            assert all(
                record["input_shape"] == (candidate_count, 129)
                for record in observations["pair_encoder"]["records"]
            )
            call_counts = _call_count_view_v1(observations)
            _evidence_v1(
                "observed_real_neural_path=PASS "
                + json.dumps(call_counts, sort_keys=True)
            )
            _evidence_v1(
                "scoped_neural_feature_use=PASS atom_input_10d=true "
                "pocket_input_10d=true egnn_input_33d=true "
                "post_target_or_diagnostics_appended_to_neural_features=false "
                "scope=observed_train10_epoch0_seed0_two_forward_path_only"
            )

            phase = "coordinate_and_fixed_node_oracle"
            transported = observations["transport"]["records"][0]["transported"]
            _assert_train10_centering_and_fixed_node_contract_v1(
                model=model,
                carrier=carrier,
                transported=transported,
                output=first,
            )
            _evidence_v1(
                "coordinate_and_fixed_node_contract=PASS "
                "task_c_second_common_translation=true task_c_vs_non_c=true "
                "fixed_noise_zero=true update_mask=true fixed_restore=true"
            )

            phase = "final_source_checkpoint_and_state_validation"
            assert _verify_bound_sources_v1() == fixed_sources_before
            assert (
                adapter.verify_covapie_train10_hidden_post_forward_adapter_sources_v1(
                    repository_root=ROOT
                )
                == adapter_sources_before
            )
            assert _safe_file_identity_v1(checkpoint_path) == (
                checkpoint_size,
                checkpoint_sha,
            )
            _assert_model_snapshot_unchanged_v1(model_snapshot, model)
            assert _fingerprint_value_v1(carrier) == carrier_fingerprint
            assert tripwire_calls == [] and model_tripwire_calls == []
            assert observations["checkpoint_deserialization"]["requested"] == 1
            assert observations["model_initialization"]["requested"] == 1
            assert observations["migration"]["requested"] == 1
            assert observations["composer_prepare"]["requested"] == 1
            assert observations["carrier_build"]["requested"] == 1
            _evidence_v1(
                "final_integrity=PASS sources=true checkpoint=true "
                "parameters=true buffers=true carrier=true hooks_pending_cleanup=true "
                "backward=false optimizer=false trainer=false save=false"
            )

        phase = "completed"
        print(f"TASK_ID={TASK_ID_V1}")
        print(f"RUNTIME_PRESERVED={runtime_root}")
        print(
            "CHECKPOINT="
            f"bytes:{checkpoint_size},sha256:{checkpoint_sha},"
            f"legacy_keys:{migration['checkpoint_key_count']},"
            f"target_keys:{migration['target_model_key_count']},"
            f"target_only:{migration['target_only_key_count']},strict:true"
        )
        print(
            "TRAIN10="
            f"tasks:{carrier_measurements['tasks']},"
            f"hidden_post:{carrier_measurements['hidden_post_eligible']},"
            f"generated:{carrier_measurements['generated_counts']},"
            f"fixed:{carrier_measurements['fixed_counts']},"
            f"task_c_seeds:{carrier_measurements['task_c_seed_counts']}"
        )
        print(f"TIMESTEPS={first_measurements['timesteps']}")
        print("RAW_LOSSES=" + json.dumps(first_measurements["raw_losses"], sort_keys=True))
        print("VALID_COUNTS=" + json.dumps(first_measurements["valid_counts"], sort_keys=True))
        print("LOSS_WEIGHTS=" + json.dumps(actual_weights, sort_keys=True))
        print("CALL_COUNTS=" + json.dumps(call_counts, sort_keys=True))
        print(
            "RNG_REPLAY="
            f"pass:true,atol:{DETERMINISM_ABSOLUTE_TOLERANCE_V1},"
            f"rtol:{DETERMINISM_RELATIVE_TOLERANCE_V1},"
            f"maximum_finite_absolute_difference:{replay_maximum_difference}"
        )
        print(
            "NO_UPDATE=parameters:true,buffers:true,identity:true,state_keys:true,"
            "requires_grad_flags:true,gradients_none:true,carrier:true,node_prior:true"
        )
        print(
            "TRAINING_OPERATIONS=backward:false,autograd_grad:false,"
            "optimizer_created:false,optimizer_step:false,trainer:false,"
            "checkpoint_saved:false"
        )
    except BaseException as primary:
        _report_primary_failure_v1(
            primary=primary,
            phase=phase,
            call_counts=_call_count_view_v1(observations),
        )
        raise
    finally:
        # Allowed cleanup only: restore the caller's CPU RNG.  ExitStack above
        # removes observers/tripwires.  No model/checkpoint/state reload occurs.
        torch.random.set_rng_state(rng_before_validation)


def _execute_real_path_if_enabled_v1() -> None:
    if os.environ.get(REAL_FORWARD_OPT_IN_V1) != "1":
        pytest.skip(
            f"set {REAL_FORWARD_OPT_IN_V1}=1 for the bounded real checkpoint path"
        )
    _evidence_v1(
        "real_opt_in=1 one_checkpoint_load=true one_model=true "
        "one_epoch0_seed0_carrier=true maximum_forward_count=2"
    )
    _run_real_checkpoint_validation_v1()


@pytest.fixture(autouse=True)
def _non_model_execution_tripwires_v1(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> Iterator[list[str]]:
    """Fail if any ordinary test reaches a real model/training boundary."""

    calls: list[str] = []
    if (
        request.node.name
        == "test_real_checkpoint_train10_forward_and_same_rng_replay_no_update"
        and os.environ.get(REAL_FORWARD_OPT_IN_V1) == "1"
    ):
        yield calls
        return

    import pytorch_lightning as pl
    from covalent_ext.biopython_compat import (
        patch_biopython_polypeptide_three_to_one,
    )

    # The same published compatibility entry used by the train10 adapter must
    # precede any import of the real training owner, even for tripwire setup.
    patch_biopython_polypeptide_three_to_one()
    from Bio.PDB import Polypeptide

    assert hasattr(Polypeptide, "three_to_one")
    from covalent_ext import (
        covapie_current11_auxiliary_model_and_loss_v1 as loss_owner,
    )
    from covalent_ext import (
        covapie_current11_training_lightning_module_v1 as training_owner,
    )
    from covalent_ext import (
        covapie_train10_hidden_post_forward_adapter_v1 as adapter,
    )
    from equivariant_diffusion.conditional_model import ConditionalDDPM
    from equivariant_diffusion.dynamics import EGNNDynamics
    from lightning_modules import LigandPocketDDPM

    def forbidden(name: str) -> Callable[..., None]:
        def tripwire(*_args: object, **_kwargs: object) -> None:
            calls.append(name)
            raise AssertionError(
                f"non-model test reached forbidden boundary: {name}"
            )

        return tripwire

    targets = (
        (torch, "load", "torch.load"),
        (torch, "save", "torch.save"),
        (torch.jit, "load", "torch.jit.load"),
        (torch.jit, "save", "torch.jit.save"),
        (torch.Tensor, "backward", "Tensor.backward"),
        (torch.autograd, "backward", "torch.autograd.backward"),
        (torch.autograd, "grad", "torch.autograd.grad"),
        (torch.optim.Optimizer, "__init__", "Optimizer.__init__"),
        (torch.optim.Optimizer, "step", "Optimizer.step"),
        (torch.optim.AdamW, "__init__", "AdamW.__init__"),
        (torch.optim.AdamW, "step", "AdamW.step"),
        (pl.Trainer, "__init__", "Trainer.__init__"),
        (pl.Trainer, "fit", "Trainer.fit"),
        (pl.Trainer, "validate", "Trainer.validate"),
        (pl.Trainer, "test", "Trainer.test"),
        (pl.Trainer, "predict", "Trainer.predict"),
        (pl.Trainer, "save_checkpoint", "Trainer.save_checkpoint"),
        (LigandPocketDDPM, "__init__", "LigandPocketDDPM.__init__"),
        (LigandPocketDDPM, "forward", "LigandPocketDDPM.forward"),
        (LigandPocketDDPM, "training_step", "LigandPocketDDPM.training_step"),
        (
            LigandPocketDDPM,
            "configure_optimizers",
            "LigandPocketDDPM.configure_optimizers",
        ),
        (ConditionalDDPM, "__init__", "ConditionalDDPM.__init__"),
        (ConditionalDDPM, "forward", "ConditionalDDPM.forward"),
        (EGNNDynamics, "__init__", "EGNNDynamics.__init__"),
        (EGNNDynamics, "forward", "EGNNDynamics.forward"),
        (
            loss_owner.CovapieCurrent11AuxiliaryModelV1,
            "__init__",
            "CovapieCurrent11AuxiliaryModelV1.__init__",
        ),
        (
            loss_owner.CovapieCurrent11AuxiliaryModelV1,
            "forward",
            "CovapieCurrent11AuxiliaryModelV1.forward",
        ),
        (
            adapter.CovapieTrain10HiddenPostForwardLigandPocketDDPMV1,
            "__init__",
            "Train10Adapter.__init__",
        ),
        (
            adapter.CovapieTrain10HiddenPostForwardLigandPocketDDPMV1,
            "forward",
            "Train10Adapter.forward",
        ),
        (
            adapter,
            "run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1",
            "train10_diffusion_bridge",
        ),
        (
            training_owner,
            "run_covapie_current11_functional_dynamics_with_hidden_v1",
            "functional_dynamics",
        ),
        (
            adapter,
            "compute_covapie_current11_training_losses_v1",
            "train10_production_loss",
        ),
        (
            loss_owner,
            "compute_covapie_current11_training_losses_v1",
            "production_loss",
        ),
    )
    for owner, attribute, name in targets:
        monkeypatch.setattr(owner, attribute, forbidden(name))
    yield calls
    assert calls == []


def test_fixed_published_helper_config_and_locator_sources() -> None:
    from covalent_ext import (
        checkpoint_compatible_model_instantiation as compatible_owner,
    )
    from covalent_ext import (
        covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1
        as checkpoint_locator,
    )
    from covalent_ext import (
        covapie_current11_checkpoint_migration_and_real_one_batch_train_path_smoke_v1
        as constructor_owner,
    )
    from covalent_ext import (
        covapie_current11_checkpoint_migration_v1 as migration_owner,
    )
    from covalent_ext import (
        covapie_train10_hidden_post_forward_adapter_v1 as adapter,
    )
    from covalent_ext import diffsbdd_model_instantiation as kwargs_owner

    observed = _verify_bound_sources_v1()
    assert len(observed) == len(BOUND_SOURCE_SHA256_V1)
    assert adapter.verify_covapie_train10_hidden_post_forward_adapter_sources_v1(
        repository_root=ROOT
    ) == adapter.DIRECT_BOUND_SOURCE_SHA256_V1
    assert checkpoint_locator.CHECKPOINT_RELATIVE_PATH_V1 == (
        compatible_owner.CHECKPOINT_PATH
    )
    assert not checkpoint_locator.CHECKPOINT_RELATIVE_PATH_V1.is_absolute()
    assert migration_owner.COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SIZE_BYTES_V1 == (
        EXPECTED_CHECKPOINT_SIZE_BYTES_V1
    )
    assert migration_owner.COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SHA256_V1 == (
        EXPECTED_CHECKPOINT_SHA256_V1
    )
    assert constructor_owner._constructor_kwargs is kwargs_owner._constructor_kwargs
    assert compatible_owner._constructor_kwargs is kwargs_owner._constructor_kwargs
    assert callable(compatible_owner._constructor_config_from_compatible_config)
    assert callable(compatible_owner._temporary_10d_dataset_info)


def test_default_opt_in_gate_precedes_the_entire_real_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    touched = []

    def forbidden_real_path() -> None:
        touched.append("real_path")
        raise AssertionError("default-disabled path was reached")

    monkeypatch.delenv(REAL_FORWARD_OPT_IN_V1, raising=False)
    monkeypatch.setattr(
        sys.modules[__name__],
        "_run_real_checkpoint_validation_v1",
        forbidden_real_path,
    )
    with pytest.raises(pytest.skip.Exception, match=REAL_FORWARD_OPT_IN_V1):
        _execute_real_path_if_enabled_v1()
    assert touched == []


def test_wrong_checkpoint_identity_rejects_before_deserialization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from covalent_ext import covapie_current11_checkpoint_migration_v1 as migration

    candidate = tmp_path / "identity-mismatch.bin"
    candidate.write_bytes(b"not-the-published-checkpoint")
    assert candidate.suffix == ".bin"
    deserialization_calls = []

    def forbidden_load(*_args: object, **_kwargs: object) -> None:
        deserialization_calls.append("torch.load")
        raise AssertionError("mismatched checkpoint reached torch.load")

    monkeypatch.setattr(migration.torch, "load", forbidden_load)
    with pytest.raises(
        ValueError,
        match="^COVAPIE_CURRENT11_CHECKPOINT_MIGRATION_V1_ERROR$",
    ):
        migration.load_covapie_current11_legacy_checkpoint_v1(
            checkpoint_path=candidate
        )
    assert deserialization_calls == []


@dataclass(frozen=True)
class _TinyReplayPayloadV1:
    values: torch.Tensor
    task_ids: torch.Tensor
    metadata: tuple[str, int, float]


def test_published_snapshot_and_nan_aware_replay_helpers_regressions() -> None:
    tools = _load_published_legacy_tools_v1()
    # Model parameter/buffer snapshots are exact and are required to stay
    # finite.  NaN-aware semantics are tested independently on replay output.
    before = torch.tensor([1.0, 2.0, 3.0], dtype=torch.float32)
    snapshot = tools._snapshot_named_tensors(iter((("value", before),)))
    tools._assert_snapshot_unchanged(snapshot, iter((("value", before),)))
    with pytest.raises(AssertionError):
        tools._assert_snapshot_unchanged(
            snapshot,
            iter((("value", torch.tensor([1.0, float("nan"), 4.0])),)),
        )

    first = _TinyReplayPayloadV1(
        values=torch.tensor([1.0, float("nan"), 2.0], dtype=torch.float64),
        task_ids=torch.tensor([0, 3, 4], dtype=torch.long),
        metadata=("scaffold_only", 3, float("nan")),
    )
    second = _TinyReplayPayloadV1(
        values=torch.tensor(
            [1.0 + 5.0e-8, float("nan"), 2.0], dtype=torch.float64
        ),
        task_ids=torch.tensor([0, 3, 4], dtype=torch.long),
        metadata=("scaffold_only", 3, float("nan")),
    )
    maximum = _compare_replay_value_v1(first, second)
    assert 0.0 < maximum <= DETERMINISM_ABSOLUTE_TOLERANCE_V1
    mismatched_nan = _TinyReplayPayloadV1(
        values=torch.tensor([1.0, 0.0, float("nan")], dtype=torch.float64),
        task_ids=second.task_ids,
        metadata=second.metadata,
    )
    with pytest.raises(AssertionError):
        _compare_replay_value_v1(first, mismatched_nan)


def test_transparent_observer_preserves_signature_arguments_and_single_call() -> None:
    calls = []
    result = object()

    def original(left: int, *, right: str) -> object:
        calls.append((left, right))
        return result

    stats = _new_call_stats_v1()
    wrapper = _transparent_observer_v1(
        original,
        stats=stats,
        projector=lambda args, kwargs, returned: {
            "args": args,
            "kwargs": kwargs,
            "same_result": returned is result,
        },
    )
    assert inspect.signature(wrapper) == inspect.signature(original)
    assert wrapper(7, right="B3") is result
    assert calls == [(7, "B3")]
    assert stats["requested"] == 1 and stats["returned"] == 1
    assert stats["records"] == [{
        "args": (7,),
        "kwargs": {"right": "B3"},
        "same_result": True,
    }]

    # A post-return observer failure is retained as secondary and cannot cause
    # the production callable to be retried or replace its returned object.
    failing_stats = _new_call_stats_v1()
    failing_wrapper = _transparent_observer_v1(
        original,
        stats=failing_stats,
        projector=lambda _args, _kwargs, _result: (_ for _ in ()).throw(
            RuntimeError("projection failed")
        ),
    )
    assert failing_wrapper(8, right="C") is result
    assert calls == [(7, "B3"), (8, "C")]
    assert failing_stats["requested"] == failing_stats["returned"] == 1
    assert failing_stats["secondary_errors"] == [
        "RuntimeError:projection failed"
    ]


def test_primary_exception_chain_survives_secondary_reporting_failure(
    capsys: pytest.CaptureFixture[str],
) -> None:
    root_cause = LookupError("root cause")
    stats = _new_call_stats_v1()
    production_calls = []

    def original() -> None:
        production_calls.append("called")
        raise RuntimeError("primary failure") from root_cause

    def secondary_reporter(_error: BaseException) -> None:
        raise ValueError("secondary observer failure")

    wrapper = _transparent_observer_v1(
        original,
        stats=stats,
        projector=lambda _args, _kwargs, result: result,
        failure_reporter=secondary_reporter,
    )
    with pytest.raises(RuntimeError, match="primary failure") as captured:
        wrapper()
    assert production_calls == ["called"]
    assert captured.value.__cause__ is root_cause
    assert stats["requested"] == 1 and stats["returned"] == 0
    assert stats["secondary_errors"] == [
        "ValueError:secondary observer failure"
    ]
    assert any(
        "secondary_observer_error=ValueError:secondary observer failure" in note
        for note in captured.value.__notes__
    )

    def broken_emitter(_message: str) -> None:
        raise OSError("report sink failed")

    _report_primary_failure_v1(
        primary=captured.value,
        phase="synthetic_failure_regression",
        call_counts={"production": {"requested": 1, "returned": 0}},
        emitter=broken_emitter,
    )
    stderr = capsys.readouterr().err
    assert "RuntimeError" in stderr and "primary failure" in stderr
    assert "LookupError" in stderr and "root cause" in stderr
    assert "SECONDARY_REPORTING_ERROR" in stderr
    assert any(
        "secondary_reporting_error=OSError:report sink failed" in note
        for note in captured.value.__notes__
    )


def test_scoped_feature_use_static_prerequisites_are_fail_closed() -> None:
    _verify_bound_sources_v1()
    _assert_scoped_feature_use_prerequisites_v1()


def test_fresh_process_real_dependency_helper_imports_adapter_first_no_model() -> None:
    """Cold-import the exact helper used by the real entry, with tripwires."""

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
assert candidate.is_absolute() and candidate.resolve(strict=True) == candidate
assert repo.is_absolute() and repo.resolve(strict=True) == repo
assert state.is_absolute() and state.resolve(strict=True) == state
assert "COVAPIE_RUN_TRAIN10_CHECKPOINT_FORWARD_NO_UPDATE" not in os.environ
runtime_parent = state / "review-scratch"
runtime_pattern = "validate_covapie_train10_checkpoint_forward_no_update_v1-*"
runtime_before = tuple(sorted(runtime_parent.glob(runtime_pattern)))

adapter_name = "covalent_ext.covapie_train10_hidden_post_forward_adapter_v1"
training_name = "covalent_ext.covapie_current11_training_lightning_module_v1"
assert adapter_name not in sys.modules
assert training_name not in sys.modules

spec = importlib.util.spec_from_file_location(
    "covapie_train10_checkpoint_fresh_dependency_candidate", candidate
)
assert spec is not None and spec.loader is not None
subject = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = subject
spec.loader.exec_module(subject)
assert adapter_name not in sys.modules
assert training_name not in sys.modules

from Bio.PDB import Polypeptide
compat_before = hasattr(Polypeptide, "three_to_one")
assert compat_before is False

import pytorch_lightning as pl
import torch
from covalent_ext import covapie_current11_checkpoint_migration_v1 as migration
from covalent_ext import covapie_train10_cpu_batch_composer_v1 as composer

assert adapter_name not in sys.modules
assert training_name not in sys.modules
tripwire_calls = []

def forbidden(name):
    def tripwire(*_args, **_kwargs):
        tripwire_calls.append(name)
        raise AssertionError("fresh dependency helper crossed boundary: " + name)
    return tripwire

profile_targets = {
    "CovapieTrain10HiddenPostForwardLigandPocketDDPMV1.__init__",
    "CovapieTrain10HiddenPostForwardLigandPocketDDPMV1.forward",
    "CovapieCurrent11TrainingLigandPocketDDPM.__init__",
    "CovapieCurrent11TrainingLigandPocketDDPM.forward",
    "LigandPocketDDPM.__init__",
    "LigandPocketDDPM.forward",
    "compute_covapie_current11_training_losses_v1",
    "run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1",
    "run_covapie_current11_functional_dynamics_with_hidden_v1",
}

def profiler(frame, event, _arg):
    if event == "call" and frame.f_code.co_qualname in profile_targets:
        tripwire_calls.append("profile:" + frame.f_code.co_qualname)
        raise AssertionError(
            "fresh dependency helper executed " + frame.f_code.co_qualname
        )

def audit_hook(event, arguments):
    if event == "open" and arguments:
        path = arguments[0]
        if isinstance(path, (str, bytes, os.PathLike)):
            rendered = os.fsdecode(path)
            if "/checkpoints/" in rendered or rendered.endswith(".ckpt"):
                tripwire_calls.append("checkpoint_open:" + rendered)
                raise AssertionError("fresh dependency helper opened checkpoint")
    if event == "os.mkdir" and arguments:
        path = arguments[0]
        if isinstance(path, (str, bytes, os.PathLike)):
            created = Path(os.fsdecode(path))
            if not created.is_absolute():
                created = Path.cwd() / created
            if created.parent == runtime_parent and created.match(runtime_pattern):
                tripwire_calls.append("model_runtime_mkdir:" + str(created))
                raise AssertionError(
                    "fresh dependency helper created a model runtime directory"
                )

sys.addaudithook(audit_hook)
with contextlib.ExitStack() as stack:
    for owner, attribute, name in (
        (torch, "load", "torch.load"),
        (torch, "save", "torch.save"),
        (torch.jit, "load", "torch.jit.load"),
        (torch.jit, "save", "torch.jit.save"),
        (torch.Tensor, "backward", "Tensor.backward"),
        (torch.autograd, "backward", "torch.autograd.backward"),
        (torch.autograd, "grad", "torch.autograd.grad"),
        (torch.optim.Optimizer, "__init__", "Optimizer.__init__"),
        (torch.optim.Optimizer, "step", "Optimizer.step"),
        (torch.optim.AdamW, "__init__", "AdamW.__init__"),
        (torch.optim.AdamW, "step", "AdamW.step"),
        (pl.Trainer, "__init__", "Trainer.__init__"),
        (pl.Trainer, "fit", "Trainer.fit"),
        (pl.Trainer, "validate", "Trainer.validate"),
        (pl.Trainer, "test", "Trainer.test"),
        (pl.Trainer, "predict", "Trainer.predict"),
        (pl.Trainer, "save_checkpoint", "Trainer.save_checkpoint"),
        (
            migration,
            "load_covapie_current11_legacy_checkpoint_v1",
            "checkpoint_loader",
        ),
        (
            composer,
            "prepare_covapie_train10_cpu_batch_composer_v1",
            "composer_prepare",
        ),
        (
            composer,
            "build_covapie_train10_cpu_epoch_batch_v1",
            "composer_build",
        ),
    ):
        stack.enter_context(mock.patch.object(owner, attribute, new=forbidden(name)))
    sys.setprofile(profiler)
    try:
        first = subject._load_real_path_dependencies_v1()
        second = subject._load_real_path_dependencies_v1()
    finally:
        sys.setprofile(None)

assert tripwire_calls == []
assert tuple(sorted(runtime_parent.glob(runtime_pattern))) == runtime_before
assert first.keys() == second.keys()
assert all(first[key] is second[key] for key in first)
adapter = first["adapter"]
training = first["training_owner"]
assert adapter is sys.modules[adapter_name]
assert training is sys.modules[training_name]
assert Path(adapter.__file__).resolve(strict=True) == (
    repo / "src/covalent_ext/covapie_train10_hidden_post_forward_adapter_v1.py"
)
assert Path(training.__file__).resolve(strict=True) == (
    repo / "src/covalent_ext/covapie_current11_training_lightning_module_v1.py"
)
assert hasattr(Polypeptide, "three_to_one")
assert adapter.BIOPYTHON_COMPAT_APPLIED_V1 is True
print(json.dumps({
    "adapter_path": str(Path(adapter.__file__).resolve(strict=True)),
    "training_owner_path": str(Path(training.__file__).resolve(strict=True)),
    "compat_before": compat_before,
    "compat_after": hasattr(Polypeptide, "three_to_one"),
    "helper_second_call_same_modules": True,
    "tripwire_call_count": len(tripwire_calls),
    "checkpoint_read": False,
    "carrier_built": False,
    "runtime_created": False,
    "model_instantiated": False,
    "forward_executed": False,
}, sort_keys=True))
'''
    environment = os.environ.copy()
    for name in (
        REAL_FORWARD_OPT_IN_V1,
        "COVAPIE_RUN_BATCH001_CHECKPOINT_FORWARD_NO_UPDATE",
        "COVAPIE_RUN_BATCH001_CHECKPOINT_BACKWARD_NO_UPDATE",
        "COVAPIE_RUN_BATCH001_CHECKPOINT_SINGLE_OPTIMIZER_STEP",
        "COVAPIE_TRAIN10_FORWARD_ADAPTER_CANDIDATE",
        "COVAPIE_TRAIN10_COMPOSER_CANDIDATE",
        "COVAPIE_CURRENT11_LEGACY_TRAIN5_DATA_ADAPTER_CANDIDATE",
        "COVAPIE_LEGACY_TRAIN5_ADAPTER_CANDIDATE",
        "COVAPIE_ADAPTER_CANDIDATE",
    ):
        environment.pop(name, None)
    environment.update({
        "COVAPIE_FRESH_PROCESS_CANDIDATE": str(
            Path(__file__).resolve(strict=True)
        ),
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
    assert result == {
        "adapter_path": str(
            ROOT
            / "src/covalent_ext/covapie_train10_hidden_post_forward_adapter_v1.py"
        ),
        "training_owner_path": str(
            ROOT
            / "src/covalent_ext/covapie_current11_training_lightning_module_v1.py"
        ),
        "compat_before": False,
        "compat_after": True,
        "helper_second_call_same_modules": True,
        "tripwire_call_count": 0,
        "checkpoint_read": False,
        "carrier_built": False,
        "runtime_created": False,
        "model_instantiated": False,
        "forward_executed": False,
    }
    print("FRESH_PROCESS_REAL_DEPENDENCY_IMPORT=" + lines[0], flush=True)


def test_cpu_train10_initial_centering_reduction_diagnostic_no_model() -> None:
    """Use one real carrier to isolate slice-mean versus scatter-mean arithmetic."""

    from equivariant_diffusion.en_diffusion import EnVariationalDiffusion
    from lightning_modules import LigandPocketDDPM
    from torch_scatter import scatter_mean
    from covalent_ext import covapie_train10_cpu_batch_composer_v1 as composer

    config_source = (ROOT / "configs/crossdock_fullatom_joint.yml").read_text(
        encoding="utf-8"
    )
    assert "normalize_factors: [1, 4]" in config_source
    norm_biases = inspect.signature(
        EnVariationalDiffusion.__init__
    ).parameters["norm_biases"].default
    assert norm_biases == (None, 0.0)

    prepared = composer.prepare_covapie_train10_cpu_batch_composer_v1(
        ROOT, STATE_ROOT, CACHE_ROOT
    )
    carrier = composer.build_covapie_train10_cpu_epoch_batch_v1(prepared, 0, 0)
    carrier_before = _fingerprint_value_v1(carrier)
    measurements = _assert_train10_carrier_contract_v1(carrier)
    transport_owner = SimpleNamespace(
        device=torch.device("cpu"), virtual_nodes=False
    )
    ligand, pocket = LigandPocketDDPM.get_ligand_and_pocket(
        transport_owner, carrier.model_input_batch
    )
    assert ligand["x"].dtype == pocket["x"].dtype == torch.float32
    assert ligand["mask"].dtype == pocket["mask"].dtype == torch.long
    normalizer = SimpleNamespace(
        norm_values=[1, 4], norm_biases=norm_biases
    )
    normalized_ligand, normalized_pocket = EnVariationalDiffusion.normalize(
        normalizer,
        {name: value.clone() for name, value in ligand.items()},
        {name: value.clone() for name, value in pocket.items()},
    )
    ligand_xh = torch.cat((
        normalized_ligand["x"], normalized_ligand["one_hot"]
    ), dim=1)
    pocket_xh = torch.cat((
        normalized_pocket["x"], normalized_pocket["one_hot"]
    ), dim=1)
    supervision = carrier.supervision
    task_ids = supervision.canonical_task_id
    fixed = supervision.ligand_base_fixed_mask[:, 0]
    ligand_mask = ligand["mask"]
    pocket_mask = pocket["mask"]
    batch_size = len(task_ids)

    loop_reference = torch.empty(
        (batch_size, 3), dtype=ligand_xh.dtype, device=ligand_xh.device
    )
    for sample, task_id in enumerate(task_ids.tolist()):
        sample_ligand = ligand_mask == sample
        selected = sample_ligand if task_id == 4 else sample_ligand & fixed
        loop_reference[sample] = ligand_xh[selected, :3].mean(0)
    loop_ligand = ligand_xh.clone()
    loop_pocket = pocket_xh.clone()
    loop_ligand[:, :3] -= loop_reference[ligand_mask]
    loop_pocket[:, :3] -= loop_reference[pocket_mask]

    scatter_ligand, scatter_pocket, scatter_reference = (
        _train10_initial_centering_v1(
            ligand_xh=ligand_xh,
            pocket_xh=pocket_xh,
            ligand_mask=ligand_mask,
            pocket_mask=pocket_mask,
            fixed=fixed,
            task_ids=task_ids,
        )
    )
    fixed_reference = scatter_mean(
        ligand_xh[:, :3][fixed],
        ligand_mask[fixed],
        dim=0,
        dim_size=batch_size,
    )
    ligand_reference = scatter_mean(
        ligand_xh[:, :3], ligand_mask, dim=0, dim_size=batch_size
    )
    independently_scattered = torch.where(
        (task_ids == 4).unsqueeze(1), ligand_reference, fixed_reference
    )
    assert torch.equal(scatter_reference, independently_scattered)
    assert torch.equal(loop_ligand[:, 3:], scatter_ligand[:, 3:])
    assert torch.equal(loop_pocket[:, 3:], scatter_pocket[:, 3:])

    stats = _coordinate_comparison_stats_v1(scatter_ligand, loop_ligand)
    assert stats["mismatch_count"] == 58
    assert stats["element_count"] == 4225
    assert stats["maximum_absolute_difference"] == 2.288818359375e-05
    assert stats["maximum_absolute_index"] == (285, 2)
    assert stats["maximum_relative_difference"] == 0.0012722646351903677
    assert stats["maximum_relative_index"] == (135, 2)

    sample_diagnostics = []
    maximum_common_translation_residual = 0.0
    for sample, task_id in enumerate(task_ids.tolist()):
        sample_ligand = ligand_mask == sample
        sample_pocket = pocket_mask == sample
        selected = sample_ligand if task_id == 4 else sample_ligand & fixed
        float64_reference = ligand_xh[selected, :3].double().mean(0)
        expected_delta = loop_reference[sample] - scatter_reference[sample]
        ligand_delta = (
            scatter_ligand[sample_ligand, :3]
            - loop_ligand[sample_ligand, :3]
        )
        pocket_delta = (
            scatter_pocket[sample_pocket, :3]
            - loop_pocket[sample_pocket, :3]
        )
        combined_delta = torch.cat((ligand_delta, pocket_delta), dim=0)
        residual = float(
            (combined_delta - expected_delta).abs().max().item()
        )
        maximum_common_translation_residual = max(
            maximum_common_translation_residual, residual
        )
        sample_diagnostics.append({
            "sample": sample,
            "task_id": task_id,
            "reference_kind": "all_ligand" if task_id == 4 else "fixed_ligand",
            "ligand_nodes": int(sample_ligand.sum().item()),
            "pocket_nodes": int(sample_pocket.sum().item()),
            "reference_nodes": int(selected.sum().item()),
            "loop_reference": loop_reference[sample].tolist(),
            "scatter_reference": scatter_reference[sample].tolist(),
            "float64_reference": float64_reference.tolist(),
            "scatter_minus_loop": (
                scatter_reference[sample] - loop_reference[sample]
            ).tolist(),
            "loop_abs_error_vs_float64": float(
                (loop_reference[sample].double() - float64_reference)
                .abs().max().item()
            ),
            "scatter_abs_error_vs_float64": float(
                (scatter_reference[sample].double() - float64_reference)
                .abs().max().item()
            ),
            "common_translation_residual": residual,
        })
    coordinate_scale = float(torch.cat((
        ligand_xh[:, :3].abs().reshape(-1),
        pocket_xh[:, :3].abs().reshape(-1),
    )).max().item())
    arithmetic_bound = (
        8.0 * torch.finfo(ligand_xh.dtype).eps * coordinate_scale
    )
    assert maximum_common_translation_residual <= arithmetic_bound
    assert _fingerprint_value_v1(carrier) == carrier_before
    print(
        "CPU_CENTERING_REDUCTION_DIAGNOSTIC="
        + json.dumps({
            "fixture_kind": "REAL_EPOCH0_SEED0_CPU_INPUT_PURE_ARITHMETIC",
            "actual_dtype": str(ligand_xh.dtype),
            "normalization_values": [1, 4],
            "normalization_biases": [None, 0.0],
            "tasks": measurements["tasks"],
            "ligand_nodes": len(ligand_xh),
            "pocket_nodes": len(pocket_xh),
            "coordinate_absolute_scale": coordinate_scale,
            "old_joint_tolerance_statistics": stats,
            "sample_diagnostics": sample_diagnostics,
            "maximum_common_translation_residual": (
                maximum_common_translation_residual
            ),
            "common_translation_arithmetic_bound": arithmetic_bound,
            "feature_columns_equal": True,
            "old_839_trace_read_back": False,
            "checkpoint_read": False,
            "model_instantiated": False,
            "neural_forward_executed": False,
        }, sort_keys=True),
        flush=True,
    )


class _SyntheticArithmeticDdpmV1:
    T = 10
    n_dims = 3
    norm_values = [1, 4]
    norm_biases = (None, 0.0)

    def normalize(
        self, ligand: dict[str, object], pocket: dict[str, object]
    ) -> tuple[dict[str, object], dict[str, object]]:
        for item in (ligand, pocket):
            item["x"] = item["x"] / self.norm_values[0]
            item["one_hot"] = (
                item["one_hot"].float() - self.norm_biases[1]
            ) / self.norm_values[1]
        return ligand, pocket

    @staticmethod
    def gamma(value: torch.Tensor) -> torch.Tensor:
        return torch.zeros_like(value)

    @staticmethod
    def inflate_batch_array(
        value: torch.Tensor, _target: torch.Tensor
    ) -> torch.Tensor:
        return value

    @staticmethod
    def alpha(value: torch.Tensor, _target: torch.Tensor) -> torch.Tensor:
        return torch.ones_like(value)

    @staticmethod
    def sigma(value: torch.Tensor, _target: torch.Tensor) -> torch.Tensor:
        return torch.ones_like(value)


def _synthetic_centering_contract_fixture_v1() -> tuple[object, object, object, object]:
    ligand_x = torch.tensor([
        [2.0, 0.0, 0.0],
        [4.0, 0.0, 0.0],
        [10.0, 0.0, 0.0],
        [0.0, 2.0, 0.0],
        [0.0, 6.0, 0.0],
    ])
    pocket_x = torch.tensor([
        [5.0, 1.0, 0.0],
        [0.0, 4.0, 0.0],
        [0.0, 5.0, 0.0],
        [0.0, 7.0, 0.0],
    ])
    ligand_one_hot = torch.tensor([
        [1.0, 0.0], [0.0, 1.0], [1.0, 0.0], [0.0, 1.0], [1.0, 0.0]
    ])
    pocket_one_hot = torch.tensor([
        [1.0, 0.0], [0.0, 1.0], [1.0, 0.0], [0.0, 1.0]
    ])
    ligand_mask = torch.tensor([0, 0, 0, 1, 1], dtype=torch.long)
    pocket_mask = torch.tensor([0, 1, 1, 1], dtype=torch.long)
    generation = torch.tensor(
        [[False], [False], [True], [True], [True]], dtype=torch.bool
    )
    fixed = ~generation
    task_ids = torch.tensor([0, 4], dtype=torch.long)
    normalized_ligand_h = ligand_one_hot / 4.0
    normalized_pocket_h = pocket_one_hot / 4.0
    clean_ligand_coordinates = torch.tensor([
        [-1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [7.0, 0.0, 0.0],
        [0.0, -2.0, 0.0],
        [0.0, 2.0, 0.0],
    ])
    final_pocket_coordinates = torch.tensor([
        [2.0, 1.0, 0.0],
        [-3.0, 0.0, 0.0],
        [-3.0, 1.0, 0.0],
        [-3.0, 3.0, 0.0],
    ])
    epsilon = torch.tensor([
        [0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0],
        [1.0, 2.0, 0.0, 0.5, -0.5],
        [2.0, 0.0, 0.0, 0.25, 0.0],
        [4.0, 0.0, 0.0, -0.25, 0.5],
    ])
    clean_ligand_xh = torch.cat((
        clean_ligand_coordinates, normalized_ligand_h
    ), dim=1)
    pretranslation_noised = torch.where(
        generation,
        clean_ligand_xh + epsilon,
        clean_ligand_xh,
    )
    expected_noised_coordinates = torch.tensor([
        [-1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [8.0, 2.0, 0.0],
        [-1.0, -2.0, 0.0],
        [1.0, 2.0, 0.0],
    ])
    noised_ligand_xh = torch.cat((
        expected_noised_coordinates, pretranslation_noised[:, 3:]
    ), dim=1)
    pocket_xh = torch.cat((
        final_pocket_coordinates, normalized_pocket_h
    ), dim=1)
    trace = SimpleNamespace(
        clean_centered_ligand_xh=clean_ligand_xh,
        clean_centered_pocket_xh=pocket_xh,
        diffusion_timestep_int=torch.tensor([1, 2], dtype=torch.long),
        sampled_epsilon_ligand=epsilon,
        noised_ligand_xh=noised_ligand_xh,
        denoised_ligand_xh=noised_ligand_xh.clone(),
        ligand_coordinate_update_mask=generation.clone(),
    )
    model = SimpleNamespace(ddpm=_SyntheticArithmeticDdpmV1())
    carrier = SimpleNamespace(supervision=SimpleNamespace(
        canonical_task_id=task_ids,
        ligand_base_generation_mask=generation,
        ligand_base_fixed_mask=fixed,
    ))
    transported = (
        {
            "x": ligand_x,
            "one_hot": ligand_one_hot,
            "size": torch.tensor([3, 2], dtype=torch.long),
            "mask": ligand_mask,
        },
        {
            "x": pocket_x,
            "one_hot": pocket_one_hot,
            "size": torch.tensor([1, 3], dtype=torch.long),
            "mask": pocket_mask,
        },
    )
    return model, carrier, transported, SimpleNamespace(diffusion_trace=trace)


def test_synthetic_train10_coordinate_and_fixed_node_semantic_probes() -> None:
    """Independent positive and fail-closed probes for every oracle boundary."""

    model, carrier, transported, output = _synthetic_centering_contract_fixture_v1()
    _assert_train10_centering_and_fixed_node_contract_v1(
        model=model, carrier=carrier, transported=transported, output=output
    )

    rejected = []

    def swapped_centers(trace: object) -> None:
        ligand = transported[0]
        raw = torch.cat((ligand["x"], ligand["one_hot"] / 4.0), dim=1)
        wrong = raw.clone()
        references = torch.tensor([[3.0, 0.0, 0.0], [0.0, 4.0, 0.0]]).flip(0)
        wrong[:, :3] -= references[ligand["mask"]]
        trace.clean_centered_ligand_xh = wrong

    def pocket_center_as_ligand_reference(trace: object) -> None:
        ligand, pocket = transported
        raw = torch.cat((ligand["x"], ligand["one_hot"] / 4.0), dim=1)
        pocket_reference = torch.stack((
            pocket["x"][pocket["mask"] == 0].mean(0),
            pocket["x"][pocket["mask"] == 1].mean(0),
        ))
        raw[:, :3] -= pocket_reference[ligand["mask"]]
        trace.clean_centered_ligand_xh = raw

    def omit_pocket_translation(trace: object) -> None:
        task_c_pocket = transported[1]["mask"] == 1
        trace.clean_centered_pocket_xh[task_c_pocket, 0] += 3.0

    def omit_task_c_second_translation(trace: object) -> None:
        task_c_ligand = transported[0]["mask"] == 1
        task_c_pocket = transported[1]["mask"] == 1
        trace.noised_ligand_xh[task_c_ligand, 0] += 3.0
        trace.clean_centered_pocket_xh[task_c_pocket, 0] += 3.0

    def modify_feature_column(trace: object) -> None:
        trace.clean_centered_ligand_xh[0, 3] += 1.0

    def add_fixed_node_noise(trace: object) -> None:
        trace.sampled_epsilon_ligand[0, 0] = 1.0

    def change_fixed_node_output(trace: object) -> None:
        trace.denoised_ligand_xh[0, 0] += 1.0

    def use_wrong_update_mask(trace: object) -> None:
        trace.ligand_coordinate_update_mask[0, 0] = True

    probes = (
        ("swapped_sample_centers", swapped_centers),
        ("pocket_center_used_as_ligand_reference", pocket_center_as_ligand_reference),
        ("ligand_only_translation", omit_pocket_translation),
        ("task_c_second_translation_omitted", omit_task_c_second_translation),
        ("feature_column_modified", modify_feature_column),
        ("fixed_node_noise_nonzero", add_fixed_node_noise),
        ("fixed_node_output_changed", change_fixed_node_output),
        ("coordinate_update_mask_wrong", use_wrong_update_mask),
    )
    for name, mutate in probes:
        probe_model, probe_carrier, probe_transport, probe_output = (
            _synthetic_centering_contract_fixture_v1()
        )
        mutate(probe_output.diffusion_trace)
        with contextlib.redirect_stdout(io.StringIO()):
            with pytest.raises(AssertionError):
                _assert_train10_centering_and_fixed_node_contract_v1(
                    model=probe_model,
                    carrier=probe_carrier,
                    transported=probe_transport,
                    output=probe_output,
                )
        rejected.append(name)
    assert tuple(rejected) == tuple(name for name, _mutate in probes)
    print(
        "SYNTHETIC_ARITHMETIC_FIXTURE="
        + json.dumps({
            "positive_contract": "PASS",
            "negative_probes_rejected": rejected,
            "asymmetric_ligand_pocket_counts": [[3, 1], [2, 3]],
            "task_ids": [0, 4],
            "initial_references": [[3.0, 0.0, 0.0], [0.0, 4.0, 0.0]],
            "task_c_second_translation": [3.0, 0.0, 0.0],
            "real_trace_substitution": False,
        }, sort_keys=True),
        flush=True,
    )


def test_epoch0_seed0_cpu_carrier_preflight_under_no_model_tripwires() -> None:
    from covalent_ext import covapie_train10_cpu_batch_composer_v1 as composer

    prepared = composer.prepare_covapie_train10_cpu_batch_composer_v1(
        ROOT, STATE_ROOT, CACHE_ROOT
    )
    carrier = composer.build_covapie_train10_cpu_epoch_batch_v1(prepared, 0, 0)
    before = _fingerprint_value_v1(carrier)
    measurements = _assert_train10_carrier_contract_v1(carrier)
    after = _fingerprint_value_v1(carrier)
    assert after == before
    print(
        "CPU_CARRIER_PREFLIGHT="
        + json.dumps(measurements, sort_keys=True),
        flush=True,
    )
    print("PENDING_REAL_EXECUTION=true", flush=True)


def test_real_checkpoint_train10_forward_and_same_rng_replay_no_update() -> None:
    """Run the bounded real path only under its independent explicit opt-in."""

    _execute_real_path_if_enabled_v1()
