from __future__ import annotations

import ast
import hashlib
import inspect
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest
import torch
from torch import nn


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import check_covapie_target_residue_atom_condition_model_consumption_v1 as checker  # noqa: E402
from covalent_ext import (  # noqa: E402
    covapie_target_residue_atom_condition_checkpoint_migration_v1 as migration,
)
from covalent_ext import (  # noqa: E402
    covapie_target_residue_atom_condition_model_consumption_design_v1 as design,
)
from equivariant_diffusion.conditional_model import (  # noqa: E402
    ConditionalDDPM,
    SimpleConditionalDDPM,
)
from equivariant_diffusion.dynamics import EGNNDynamics  # noqa: E402
from equivariant_diffusion.en_diffusion import EnVariationalDiffusion  # noqa: E402


ERROR = "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_MODEL_CONSUMPTION_INVALID"
FIELD = "pocket_target_residue_atom_condition_indicator"
NEW_PARAMETER = "target_residue_atom_condition_embedding"
NEW_STATE_KEY = f"ddpm.dynamics.{NEW_PARAMETER}"
BASE_COMMIT = "99425693056cd8800b9f93a19ea79a1e3e77c68e"
CHECKPOINT_PATH = ROOT / "checkpoints/crossdocked_fullatom_cond.ckpt"


def _assert_canonical_error(action) -> None:
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        action()


def _profile_dynamics_kwargs() -> dict[str, object]:
    return {
        "atom_nf": 10,
        "residue_nf": 10,
        "n_dims": 3,
        "joint_nf": 32,
        "device": "cpu",
        "hidden_nf": 128,
        "n_layers": 5,
        "attention": True,
        "tanh": True,
        "norm_constant": 1,
        "inv_sublayers": 1,
        "sin_embedding": False,
        "normalization_factor": 100,
        "aggregation_method": "sum",
        "edge_cutoff_ligand": None,
        "edge_cutoff_pocket": 5.0,
        "edge_cutoff_interaction": 5.0,
        "update_pocket_coords": False,
        "reflection_equivariant": False,
    }


def _tiny_dynamics_kwargs(joint_nf: int = 4) -> dict[str, object]:
    return {
        "atom_nf": 2,
        "residue_nf": 2,
        "n_dims": 3,
        "joint_nf": joint_nf,
        "device": "cpu",
        "hidden_nf": 8,
        "n_layers": 1,
        "update_pocket_coords": False,
    }


@pytest.fixture(scope="session")
def checkpoint_payload():
    return torch.load(CHECKPOINT_PATH, map_location="cpu", weights_only=False)


def _checkpoint_dynamics_state(checkpoint_payload) -> dict[str, torch.Tensor]:
    return {
        key.removeprefix("ddpm.dynamics."): value
        for key, value in checkpoint_payload["state_dict"].items()
        if key.startswith("ddpm.dynamics.")
    }


def test_enable_flag_defaults_false_and_lightning_forwards_it_explicitly():
    dynamics_default = inspect.signature(EGNNDynamics.__init__).parameters[
        "target_residue_atom_conditioning"
    ].default
    assert dynamics_default is False

    tree = ast.parse((ROOT / "lightning_modules.py").read_text())
    constructor = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name == "__init__"
        and any(
            isinstance(parent, ast.ClassDef) and parent.name == "LigandPocketDDPM"
            for parent in tree.body
            if isinstance(parent, ast.ClassDef) and node in parent.body
        )
    )
    assert constructor.args.args[-1].arg == "target_residue_atom_conditioning"
    assert isinstance(constructor.args.defaults[-1], ast.Constant)
    assert constructor.args.defaults[-1].value is False
    calls = [node for node in ast.walk(constructor) if isinstance(node, ast.Call)]
    egnn_call = next(
        call for call in calls
        if isinstance(call.func, ast.Name) and call.func.id == "EGNNDynamics"
    )
    assert any(
        keyword.arg == "target_residue_atom_conditioning"
        for keyword in egnn_call.keywords
    )


@pytest.mark.parametrize("bad_value", [0, 1, None, "true", torch.tensor(True)])
def test_enable_flag_requires_exact_bool(bad_value):
    _assert_canonical_error(
        lambda: EGNNDynamics(
            **_tiny_dynamics_kwargs(),
            target_residue_atom_conditioning=bad_value,
        )
    )


def test_disabled_profile_has_no_new_state_key():
    model = EGNNDynamics(**_tiny_dynamics_kwargs())
    assert model.target_residue_atom_conditioning is False
    assert model.target_residue_atom_condition_embedding is None
    assert NEW_PARAMETER not in model.state_dict()


def test_enabled_profile_has_exactly_one_new_parameter():
    disabled = EGNNDynamics(**_tiny_dynamics_kwargs())
    enabled = EGNNDynamics(
        **_tiny_dynamics_kwargs(), target_residue_atom_conditioning=True
    )
    assert set(enabled.state_dict()) - set(disabled.state_dict()) == {NEW_PARAMETER}
    assert set(disabled.state_dict()) - set(enabled.state_dict()) == set()
    assert set(dict(enabled.named_parameters())) - set(
        dict(disabled.named_parameters())
    ) == {NEW_PARAMETER}


@pytest.mark.parametrize("joint_nf", [4, 16, 32])
def test_enabled_parameter_shape_tracks_joint_nf(joint_nf):
    model = EGNNDynamics(
        **_tiny_dynamics_kwargs(joint_nf),
        target_residue_atom_conditioning=True,
    )
    assert list(model.target_residue_atom_condition_embedding.shape) == [joint_nf]


def test_actual_profile_parameter_is_zero_and_requires_grad():
    model = EGNNDynamics(
        **_profile_dynamics_kwargs(), target_residue_atom_conditioning=True
    )
    parameter = model.target_residue_atom_condition_embedding
    assert list(parameter.shape) == [32]
    assert parameter.requires_grad is True
    assert torch.count_nonzero(parameter).item() == 0


def test_disabled_actual_checkpoint_dynamics_strict_load(checkpoint_payload):
    model = EGNNDynamics(**_profile_dynamics_kwargs())
    base = _checkpoint_dynamics_state(checkpoint_payload)
    assert len(base) == len(model.state_dict()) == 120
    incompatible = model.load_state_dict(base, strict=True)
    assert list(incompatible.missing_keys) == []
    assert list(incompatible.unexpected_keys) == []


class _MigrationWrapper(nn.Module):
    def __init__(self, enabled: bool):
        super().__init__()
        self.ddpm = nn.Module()
        self.ddpm.dynamics = EGNNDynamics(
            **_tiny_dynamics_kwargs(32),
            target_residue_atom_conditioning=enabled,
        )


def _migration_case() -> tuple[_MigrationWrapper, dict[str, torch.Tensor]]:
    disabled = _MigrationWrapper(False)
    enabled = _MigrationWrapper(True)
    return enabled, {
        key: value.detach().clone() for key, value in disabled.state_dict().items()
    }


def test_migration_fills_exactly_one_key_and_strict_loads():
    model, base = _migration_case()
    report = migration.load_covapie_base_state_dict_into_target_residue_conditioned_model_v1(
        model=model, base_state_dict=base
    )
    assert report["filled_state_keys"] == [NEW_STATE_KEY]
    assert report["model_state_key_count"] == report["base_state_key_count"] + 1
    assert report["missing_keys"] == []
    assert report["unexpected_keys"] == []
    assert report["strict_load"] is True
    assert all(torch.equal(model.state_dict()[key], value) for key, value in base.items())


def test_migration_does_not_modify_base_mapping_or_tensors():
    model, base = _migration_case()
    ordered_keys = list(base)
    snapshot = {key: value.clone() for key, value in base.items()}
    migration.load_covapie_base_state_dict_into_target_residue_conditioned_model_v1(
        model=model, base_state_dict=base
    )
    assert list(base) == ordered_keys
    assert all(torch.equal(base[key], snapshot[key]) for key in base)


def test_migration_rejects_an_additional_missing_shared_key():
    model, base = _migration_case()
    base.pop(next(iter(base)))
    _assert_canonical_error(
        lambda: migration.load_covapie_base_state_dict_into_target_residue_conditioned_model_v1(
            model=model, base_state_dict=base
        )
    )


def test_migration_rejects_unexpected_base_key():
    model, base = _migration_case()
    base["unexpected"] = torch.zeros(1)
    _assert_canonical_error(
        lambda: migration.load_covapie_base_state_dict_into_target_residue_conditioned_model_v1(
            model=model, base_state_dict=base
        )
    )


def test_migration_rejects_shared_shape_drift():
    model, base = _migration_case()
    key = next(iter(base))
    base[key] = torch.zeros(base[key].numel() + 1, dtype=base[key].dtype)
    _assert_canonical_error(
        lambda: migration.load_covapie_base_state_dict_into_target_residue_conditioned_model_v1(
            model=model, base_state_dict=base
        )
    )


def test_migration_rejects_shared_dtype_drift():
    model, base = _migration_case()
    key = next(key for key, value in base.items() if value.is_floating_point())
    base[key] = base[key].double()
    _assert_canonical_error(
        lambda: migration.load_covapie_base_state_dict_into_target_residue_conditioned_model_v1(
            model=model, base_state_dict=base
        )
    )


def test_migration_rejects_nonzero_new_parameter():
    model, base = _migration_case()
    model.ddpm.dynamics.target_residue_atom_condition_embedding = nn.Parameter(
        torch.ones(32)
    )
    _assert_canonical_error(
        lambda: migration.load_covapie_base_state_dict_into_target_residue_conditioned_model_v1(
            model=model, base_state_dict=base
        )
    )


class _CaptureEGNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.h = None
        self.x = None

    def forward(self, h, x, edges, **kwargs):
        self.h = h.detach().clone()
        self.x = x.detach().clone()
        return h, x


def _capture_dynamics(enabled: bool = True):
    model = EGNNDynamics(
        **_tiny_dynamics_kwargs(), target_residue_atom_conditioning=enabled
    )
    capture = _CaptureEGNN()
    model.egnn = capture
    model.eval()
    return model, capture


def _dynamics_inputs():
    atoms = torch.tensor(
        [[0.0, 0.0, 0.0, 1.0, 0.0], [1.0, 0.0, 0.0, 0.0, 1.0]]
    )
    residues = torch.tensor(
        [
            [0.0, 1.0, 0.0, 1.0, 0.0],
            [0.0, 2.0, 0.0, 0.0, 1.0],
            [0.0, 3.0, 0.0, 1.0, 0.0],
        ]
    )
    atom_mask = torch.zeros(2, dtype=torch.long)
    residue_mask = torch.zeros(3, dtype=torch.long)
    return atoms, residues, torch.tensor([0.25]), atom_mask, residue_mask


def _run_dynamics(model, indicator=None):
    return model(
        *_dynamics_inputs(),
        pocket_target_residue_atom_condition_indicator=indicator,
    )


def test_dynamics_absent_condition_preserves_legacy_path():
    model, _ = _capture_dynamics(False)
    atom_output, residue_output = _run_dynamics(model)
    assert atom_output.shape == (2, 5)
    assert residue_output.shape == (3, 5)


def test_dynamics_present_condition_requires_enabled_flag():
    model, _ = _capture_dynamics(False)
    _assert_canonical_error(
        lambda: _run_dynamics(model, torch.tensor([True, False, False]))
    )


@pytest.mark.parametrize(
    "indicator",
    [
        torch.tensor([1, 0, 0]),
        torch.tensor([[True, False, False]]),
        torch.tensor([True, False]),
    ],
)
def test_dynamics_rejects_nonbool_2d_and_length_mismatch(indicator):
    model, _ = _capture_dynamics(True)
    _assert_canonical_error(lambda: _run_dynamics(model, indicator))


def test_zero_initialization_gives_exact_output_parity():
    model, _ = _capture_dynamics(True)
    absent = _run_dynamics(model)
    present = _run_dynamics(model, torch.tensor([False, True, False]))
    assert all(torch.equal(left, right) for left, right in zip(absent, present))


def test_nonzero_embedding_changes_only_target_residue_hidden_row():
    model, capture = _capture_dynamics(True)
    inputs = _dynamics_inputs()
    atom_nodes = inputs[0]
    target_pocket_local_index = 1
    model(*inputs)
    legacy_h = capture.h.clone()
    legacy_x = capture.x.clone()
    embedding = torch.tensor([1.0, 2.0, 3.0, 4.0])
    model.target_residue_atom_condition_embedding = nn.Parameter(embedding)
    model(
        *inputs,
        pocket_target_residue_atom_condition_indicator=torch.tensor(
            [False, True, False]
        ),
    )
    conditioned_h = capture.h
    target_combined_row = len(atom_nodes) + target_pocket_local_index
    expected_conditioned_h = legacy_h.clone()
    expected_conditioned_h[
        target_combined_row, : embedding.numel()
    ] = (
        expected_conditioned_h[target_combined_row, : embedding.numel()]
        + embedding
    )

    assert torch.equal(conditioned_h, expected_conditioned_h)
    assert torch.equal(conditioned_h[: len(atom_nodes)], legacy_h[: len(atom_nodes)])
    assert torch.equal(conditioned_h[len(atom_nodes)], legacy_h[len(atom_nodes)])
    assert torch.equal(conditioned_h[len(atom_nodes) + 2], legacy_h[len(atom_nodes) + 2])
    assert torch.equal(
        conditioned_h[target_combined_row, embedding.numel() :],
        legacy_h[target_combined_row, embedding.numel() :],
    )
    assert torch.equal(capture.x, legacy_x)


def test_nonzero_injection_oracle_is_stable_across_random_initializations():
    required_true_facts = (
        "zero_initialization_parity",
        "nonzero_target_row_changed",
        "non_target_rows_unchanged",
        "ligand_rows_not_directly_injected",
        "coordinates_unchanged",
        "injection_oracle_direct_expected_hidden_match",
    )
    cpu_rng_state = torch.random.get_rng_state()
    try:
        for seed in range(16):
            torch.manual_seed(seed)
            facts = checker._injection_facts()
            assert all(facts[name] is True for name in required_true_facts)
    finally:
        torch.random.set_rng_state(cpu_rng_state)


def test_node_permutation_keeps_indicator_aligned():
    model, capture = _capture_dynamics(True)
    model.target_residue_atom_condition_embedding = nn.Parameter(torch.ones(4))
    inputs = _dynamics_inputs()
    indicator = torch.tensor([False, True, False])
    model(*inputs, pocket_target_residue_atom_condition_indicator=indicator)
    original = capture.h[2:].clone()

    permutation = torch.tensor([2, 0, 1])
    model(
        inputs[0],
        inputs[1][permutation],
        inputs[2],
        inputs[3],
        inputs[4][permutation],
        pocket_target_residue_atom_condition_indicator=indicator[permutation],
    )
    assert torch.allclose(capture.h[2:], original[permutation])


class _FlagDynamics(nn.Module):
    def __init__(self, enabled=True):
        super().__init__()
        self.target_residue_atom_conditioning = enabled


class _ValidationHarness(EnVariationalDiffusion):
    def __init__(self, enabled=True):
        nn.Module.__init__(self)
        self.dynamics = _FlagDynamics(enabled)


def _pocket_batch():
    return {
        "x": torch.zeros(5, 3),
        "one_hot": torch.zeros(5, 2),
        "mask": torch.tensor([0, 0, 1, 1, 1]),
        "size": torch.tensor([2, 3]),
    }


def _valid_indicator():
    return torch.tensor([True, False, False, True, False])


@pytest.mark.parametrize("source", ["explicit", "dictionary", "both"])
def test_top_level_resolution_accepts_each_valid_source_without_mutation(source):
    model = _ValidationHarness(True)
    pocket = _pocket_batch()
    indicator = _valid_indicator()
    pocket_snapshot = {key: value.clone() for key, value in pocket.items()}
    explicit = None
    if source in {"dictionary", "both"}:
        pocket[FIELD] = indicator
        pocket_snapshot[FIELD] = indicator.clone()
    if source in {"explicit", "both"}:
        explicit = indicator if source == "explicit" else indicator.clone()
    resolved = model._resolve_covapie_target_residue_atom_condition_indicator_v1(
        pocket, explicit
    )
    expected = pocket[FIELD] if FIELD in pocket else indicator
    assert resolved is expected
    assert set(pocket) == set(pocket_snapshot)
    assert all(torch.equal(pocket[key], value) for key, value in pocket_snapshot.items())


def test_top_level_absent_condition_returns_none_when_disabled():
    model = _ValidationHarness(False)
    assert model._resolve_covapie_target_residue_atom_condition_indicator_v1(
        _pocket_batch()
    ) is None


@pytest.mark.parametrize(
    "mutator",
    [
        lambda pocket, indicator: indicator.long(),
        lambda pocket, indicator: indicator.unsqueeze(0),
        lambda pocket, indicator: indicator[:-1],
        lambda pocket, indicator: torch.zeros_like(indicator),
        lambda pocket, indicator: torch.tensor([True, True, False, True, False]),
        lambda pocket, indicator: torch.tensor([True, False, False, False, False]),
    ],
)
def test_top_level_rejects_invalid_dtype_shape_length_and_cardinality(mutator):
    model = _ValidationHarness(True)
    pocket = _pocket_batch()
    indicator = mutator(pocket, _valid_indicator())
    _assert_canonical_error(
        lambda: model._resolve_covapie_target_residue_atom_condition_indicator_v1(
            pocket, indicator
        )
    )


@pytest.mark.parametrize(
    "mutator",
    [
        lambda pocket: pocket.update(size=torch.tensor([2, 2])),
        lambda pocket: pocket.update(size=torch.tensor([[2, 3]])),
        lambda pocket: pocket.update(mask=torch.tensor([[0, 0, 1, 1, 1]])),
        lambda pocket: pocket.update(mask=torch.tensor([0, 1, 1, 1, 1])),
        lambda pocket: pocket.update(one_hot=torch.zeros(4, 2)),
    ],
)
def test_top_level_rejects_size_mask_and_node_alignment_drift(mutator):
    model = _ValidationHarness(True)
    pocket = _pocket_batch()
    mutator(pocket)
    _assert_canonical_error(
        lambda: model._resolve_covapie_target_residue_atom_condition_indicator_v1(
            pocket, _valid_indicator()
        )
    )


def test_top_level_rejects_non_long_pocket_mask_dtypes():
    model = _ValidationHarness(True)
    for dtype in (torch.float32, torch.bool, torch.int32):
        pocket = _pocket_batch()
        pocket["mask"] = pocket["mask"].to(dtype=dtype)
        _assert_canonical_error(
            lambda: model._resolve_covapie_target_residue_atom_condition_indicator_v1(
                pocket, _valid_indicator()
            )
        )


def test_top_level_rejects_non_long_pocket_size_dtypes():
    model = _ValidationHarness(True)
    for dtype in (torch.float32, torch.bool, torch.int32):
        pocket = _pocket_batch()
        pocket["size"] = torch.tensor([2, 3], dtype=dtype)
        _assert_canonical_error(
            lambda: model._resolve_covapie_target_residue_atom_condition_indicator_v1(
                pocket, _valid_indicator()
            )
        )


def test_dual_source_equal_numeric_values_with_dtype_drift_is_rejected():
    model = _ValidationHarness(True)
    valid = _valid_indicator()
    pairs = (
        (valid, valid.to(dtype=torch.long)),
        (valid, valid.to(dtype=torch.float32)),
        (valid.to(dtype=torch.long), valid),
    )
    for dictionary_indicator, explicit_indicator in pairs:
        pocket = _pocket_batch()
        pocket[FIELD] = dictionary_indicator
        _assert_canonical_error(
            lambda: model._resolve_covapie_target_residue_atom_condition_indicator_v1(
                pocket, explicit_indicator
            )
        )


def test_top_level_present_condition_requires_enabled_flag():
    model = _ValidationHarness(False)
    _assert_canonical_error(
        lambda: model._resolve_covapie_target_residue_atom_condition_indicator_v1(
            _pocket_batch(), _valid_indicator()
        )
    )


def test_dictionary_none_is_not_silently_ignored():
    model = _ValidationHarness(True)
    pocket = _pocket_batch()
    pocket[FIELD] = None
    _assert_canonical_error(
        lambda: model._resolve_covapie_target_residue_atom_condition_indicator_v1(
            pocket
        )
    )


def test_explicit_and_dictionary_conflict_is_rejected():
    model = _ValidationHarness(True)
    pocket = _pocket_batch()
    pocket[FIELD] = _valid_indicator()
    explicit = torch.tensor([False, True, False, True, False])
    _assert_canonical_error(
        lambda: model._resolve_covapie_target_residue_atom_condition_indicator_v1(
            pocket, explicit
        )
    )


class _SpyDynamics(nn.Module):
    def __init__(self, update_pocket_coords: bool):
        super().__init__()
        self.update_pocket_coords = update_pocket_coords
        self.target_residue_atom_conditioning = True
        self.conditions: list[torch.Tensor | None] = []

    def forward(
        self,
        atoms,
        residues,
        t,
        atom_mask,
        residue_mask,
        pocket_target_residue_atom_condition_indicator=None,
    ):
        self.conditions.append(pocket_target_residue_atom_condition_indicator)
        return torch.zeros_like(atoms), torch.zeros_like(residues)


def _diffusion_model(model_class, update_pocket_coords):
    spy = _SpyDynamics(update_pocket_coords)
    model = model_class(
        dynamics=spy,
        atom_nf=2,
        residue_nf=2,
        n_dims=3,
        size_histogram=[[1.0] * 5 for _ in range(5)],
        timesteps=2,
        noise_schedule="polynomial_2",
        noise_precision=1e-4,
        loss_type="l2",
        norm_values=(1.0, 1.0),
    )
    return model, spy


def _single_sample_batch():
    ligand = {
        "x": torch.zeros(2, 3),
        "one_hot": torch.eye(2),
        "mask": torch.zeros(2, dtype=torch.long),
        "size": torch.tensor([2]),
    }
    pocket = {
        "x": torch.zeros(3, 3),
        "one_hot": torch.tensor([[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]]),
        "mask": torch.zeros(3, dtype=torch.long),
        "size": torch.tensor([3]),
    }
    return ligand, pocket, torch.tensor([False, True, False])


@pytest.mark.parametrize(
    "model_class,update_pocket_coords,training,expected_calls",
    [
        (ConditionalDDPM, False, True, 1),
        (ConditionalDDPM, False, False, 2),
        (EnVariationalDiffusion, True, True, 1),
        (EnVariationalDiffusion, True, False, 2),
    ],
)
def test_training_and_eval_paths_reuse_same_validated_tensor(
    model_class, update_pocket_coords, training, expected_calls
):
    model, spy = _diffusion_model(model_class, update_pocket_coords)
    model.train(training)
    ligand, pocket, indicator = _single_sample_batch()
    with torch.no_grad():
        model(
            ligand,
            pocket,
            pocket_target_residue_atom_condition_indicator=indicator,
        )
    assert len(spy.conditions) == expected_calls
    assert all(condition is indicator for condition in spy.conditions)


@pytest.mark.parametrize(
    "path",
    ["sample_given_pocket", "diversify", "conditional_inpaint"],
)
def test_conditional_sampling_paths_thread_static_tensor_to_iterations_and_final(path):
    model, spy = _diffusion_model(ConditionalDDPM, False)
    model.eval()
    ligand, pocket, indicator = _single_sample_batch()
    with torch.no_grad():
        if path == "sample_given_pocket":
            model.sample_given_pocket(
                pocket,
                torch.tensor([2]),
                timesteps=2,
                pocket_target_residue_atom_condition_indicator=indicator,
            )
        elif path == "diversify":
            model.diversify(
                ligand,
                pocket,
                2,
                pocket_target_residue_atom_condition_indicator=indicator,
            )
        else:
            model.inpaint(
                ligand,
                pocket,
                torch.tensor([1.0, 0.0]),
                timesteps=2,
                pocket_target_residue_atom_condition_indicator=indicator,
            )
    assert len(spy.conditions) == 3
    assert all(condition is indicator for condition in spy.conditions)


def test_joint_inpaint_threads_static_tensor_to_iterations_and_final():
    model, spy = _diffusion_model(EnVariationalDiffusion, True)
    model.eval()
    ligand, pocket, indicator = _single_sample_batch()
    model.inpaint(
        ligand,
        pocket,
        torch.tensor([1.0, 0.0]),
        torch.tensor([1.0, 0.0, 0.0]),
        timesteps=2,
        pocket_target_residue_atom_condition_indicator=indicator,
    )
    assert len(spy.conditions) == 3
    assert all(condition is indicator for condition in spy.conditions)


@pytest.mark.parametrize("path", ["forward", "sample_given_pocket"])
def test_simple_conditional_overrides_explicitly_forward_condition(path):
    model, spy = _diffusion_model(SimpleConditionalDDPM, False)
    ligand, pocket, indicator = _single_sample_batch()
    with torch.no_grad():
        if path == "forward":
            model.eval()
            model(
                ligand,
                pocket,
                pocket_target_residue_atom_condition_indicator=indicator,
            )
            assert len(spy.conditions) == 2
        else:
            model.sample_given_pocket(
                pocket,
                torch.tensor([2]),
                timesteps=2,
                pocket_target_residue_atom_condition_indicator=indicator,
            )
            assert len(spy.conditions) == 3
    assert all(condition is indicator for condition in spy.conditions)


def _source_at_commit(relative_path: str) -> str:
    return subprocess.run(
        ["git", "show", f"{BASE_COMMIT}:{relative_path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _class_methods(source: str) -> dict[str, ast.FunctionDef]:
    result = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    result[f"{node.name}.{child.name}"] = child
    return result


def test_authorized_ast_change_boundary_is_exact():
    expected = {
        "lightning_modules.py": {"LigandPocketDDPM.__init__"},
        "equivariant_diffusion/dynamics.py": {
            "EGNNDynamics.__init__",
            "EGNNDynamics.forward",
        },
        "equivariant_diffusion/conditional_model.py": {
            "ConditionalDDPM.sample_p_xh_given_z0",
            "ConditionalDDPM.forward",
            "ConditionalDDPM.diversify",
            "ConditionalDDPM.sample_p_zs_given_zt",
            "ConditionalDDPM.sample_given_pocket",
            "ConditionalDDPM.inpaint",
            "SimpleConditionalDDPM.forward",
            "SimpleConditionalDDPM.sample_given_pocket",
        },
        "equivariant_diffusion/en_diffusion.py": {
            "EnVariationalDiffusion.forward",
            "EnVariationalDiffusion.sample_p_zs_given_zt",
            "EnVariationalDiffusion.sample_p_xh_given_z0",
            "EnVariationalDiffusion.inpaint",
        },
    }
    for relative_path, allowed in expected.items():
        before = _class_methods(_source_at_commit(relative_path))
        after = _class_methods((ROOT / relative_path).read_text())
        changed = {
            name
            for name in before.keys() & after
            if ast.dump(before[name], include_attributes=False)
            != ast.dump(after[name], include_attributes=False)
        }
        added = set(after) - set(before)
        if relative_path == "equivariant_diffusion/en_diffusion.py":
            assert added == {
                "EnVariationalDiffusion._validate_covapie_target_residue_atom_condition_indicator_v1",
                "EnVariationalDiffusion._resolve_covapie_target_residue_atom_condition_indicator_v1",
            }
        else:
            assert added == set()
        assert changed == allowed
        assert set(before) - set(after) == set()


def test_all_eight_dynamics_sites_thread_long_semantic_keyword():
    calls = []
    for relative_path in (
        "equivariant_diffusion/conditional_model.py",
        "equivariant_diffusion/en_diffusion.py",
    ):
        tree = ast.parse((ROOT / relative_path).read_text())
        calls.extend(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "self"
            and node.func.attr == "dynamics"
        )
    assert len(calls) == 8
    assert all(
        [keyword.arg for keyword in call.keywords] == [FIELD]
        for call in calls
    )


def test_internal_sampling_methods_do_not_repeat_top_level_cardinality_scan():
    for relative_path, method_names in {
        "equivariant_diffusion/conditional_model.py": {
            "ConditionalDDPM.sample_p_xh_given_z0",
            "ConditionalDDPM.sample_p_zs_given_zt",
        },
        "equivariant_diffusion/en_diffusion.py": {
            "EnVariationalDiffusion.sample_p_xh_given_z0",
            "EnVariationalDiffusion.sample_p_zs_given_zt",
        },
    }.items():
        methods = _class_methods((ROOT / relative_path).read_text())
        for name in method_names:
            attributes = {
                node.attr
                for node in ast.walk(methods[name])
                if isinstance(node, ast.Attribute)
            }
            assert not any("resolve_covapie" in attr for attr in attributes)
            assert not any("validate_covapie" in attr for attr in attributes)


def test_condition_is_not_hidden_in_kwargs_or_global_mutable_state():
    for relative_path in (
        "equivariant_diffusion/conditional_model.py",
        "equivariant_diffusion/en_diffusion.py",
        "equivariant_diffusion/dynamics.py",
    ):
        tree = ast.parse((ROOT / relative_path).read_text())
        assert not any(isinstance(node, (ast.Global, ast.Nonlocal)) for node in ast.walk(tree))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and FIELD in {
                argument.arg for argument in node.args.args
            }:
                assert node.args.kwarg is None


def _loss_projection(source: str, qualified_name: str) -> list[str]:
    method = _class_methods(source)[qualified_name]
    prefixes = (
        "delta_log",
        "error",
        "squared_error",
        "SNR_weight",
        "neg_log",
        "kl_prior",
        "loss",
        "log_p",
        "xh_lig_hat",
    )
    projection = []
    for node in ast.walk(method):
        if not isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        names = {
            child.id
            for target in targets
            for child in ast.walk(target)
            if isinstance(child, ast.Name)
        }
        if any(name.startswith(prefixes) for name in names):
            projection.append(ast.dump(node, include_attributes=False))
    return sorted(projection)


@pytest.mark.parametrize(
    "relative_path,qualified_name",
    [
        ("equivariant_diffusion/conditional_model.py", "ConditionalDDPM.forward"),
        ("equivariant_diffusion/en_diffusion.py", "EnVariationalDiffusion.forward"),
    ],
)
def test_loss_computation_ast_is_unchanged(relative_path, qualified_name):
    assert _loss_projection(
        _source_at_commit(relative_path), qualified_name
    ) == _loss_projection((ROOT / relative_path).read_text(), qualified_name)


def test_normalization_noise_and_unconditional_sample_ast_are_unchanged():
    before = _class_methods(_source_at_commit("equivariant_diffusion/en_diffusion.py"))
    after = _class_methods((ROOT / "equivariant_diffusion/en_diffusion.py").read_text())
    for name in (
        "EnVariationalDiffusion.normalize",
        "EnVariationalDiffusion.noised_representation",
        "EnVariationalDiffusion.sample",
    ):
        assert ast.dump(before[name], include_attributes=False) == ast.dump(
            after[name], include_attributes=False
        )


def test_existing_widths_and_state_shapes_are_unchanged(checkpoint_payload):
    disabled = EGNNDynamics(**_profile_dynamics_kwargs())
    enabled = EGNNDynamics(
        **_profile_dynamics_kwargs(), target_residue_atom_conditioning=True
    )
    base = _checkpoint_dynamics_state(checkpoint_payload)
    assert set(disabled.state_dict()) == set(base)
    assert all(disabled.state_dict()[key].shape == value.shape for key, value in base.items())
    assert enabled.atom_encoder[0].in_features == 10
    assert enabled.residue_encoder[0].in_features == 10
    assert enabled.node_nf == 33
    assert enabled.egnn.embedding.in_features == 33


@pytest.mark.parametrize(
    "relative_path,expected_sha256",
    [
        (
            "equivariant_diffusion/egnn_new.py",
            "87001209a047133519371d4a01e3e2bdddc55bf3d41e9a7ff68a2664badc2333",
        ),
        (
            "dataset.py",
            "d1c548185521692ca14be062e34d5bea617f8d3c89a22eaef4ddb13a52907c99",
        ),
    ],
)
def test_protected_sources_are_unchanged(relative_path, expected_sha256):
    payload = (ROOT / relative_path).read_bytes()
    assert hashlib.sha256(payload).hexdigest() == expected_sha256
    assert payload == subprocess.run(
        ["git", "show", f"{BASE_COMMIT}:{relative_path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout


def test_formal_checkpoint_is_unchanged():
    assert CHECKPOINT_PATH.stat().st_size == 17861341
    assert hashlib.sha256(CHECKPOINT_PATH.read_bytes()).hexdigest() == (
        "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
    )


def test_canonical_five_masks_include_scaffold_only():
    assert design.CANONICAL_MASK_SEMANTIC_NAMES == (
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    )


def test_no_training_backward_optimizer_or_checkpoint_write_is_implemented():
    new_sources = [
        ROOT / "src/covalent_ext/covapie_target_residue_atom_condition_checkpoint_migration_v1.py",
        ROOT / "scripts/check_covapie_target_residue_atom_condition_model_consumption_v1.py",
    ]
    for path in new_sources:
        if not path.exists():
            continue
        tree = ast.parse(path.read_text())
        attributes = {
            node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
        }
        assert "backward" not in attributes
        assert "step" not in attributes
        assert "save" not in attributes
        assert "save_checkpoint" not in attributes


def test_implementation_checker_design_commit_binding_uses_ancestor_not_exact_head():
    checker_source = (
        ROOT
        / "scripts/check_covapie_target_residue_atom_condition_model_consumption_v1.py"
    ).read_text()
    evaluate_source = inspect.getsource(checker.evaluate)
    assert '"rev-parse", "HEAD"' not in checker_source
    assert "BASE_COMMIT_SUBJECT" in evaluate_source
    assert "BASE_COMMIT_PARENT" in evaluate_source
    assert "DESIGN_PRODUCTION_PATH" in evaluate_source
    assert "DESIGN_SOURCE_SHA256" in evaluate_source
    assert "_git_commit_is_ancestor(" in evaluate_source

    assert checker._git("cat-file", "-e", f"{BASE_COMMIT}^{{commit}}") == b""
    assert checker._git("show", "-s", "--format=%s", BASE_COMMIT) == (
        f"{checker.BASE_COMMIT_SUBJECT}\n".encode()
    )
    assert checker._git("show", "-s", "--format=%P", BASE_COMMIT) == (
        f"{checker.BASE_COMMIT_PARENT}\n".encode()
    )
    committed_design = checker._git(
        "show", f"{BASE_COMMIT}:{checker.DESIGN_PRODUCTION_PATH}"
    )
    current_design = (ROOT / checker.DESIGN_PRODUCTION_PATH).read_bytes()
    assert committed_design == current_design
    assert hashlib.sha256(current_design).hexdigest() == checker.DESIGN_SOURCE_SHA256
    assert checker._git_commit_is_ancestor(
        repo_root=ROOT,
        base_commit=BASE_COMMIT,
        head_ref="HEAD",
    )


def test_candidate_path_scope_is_identical_before_and_after_commit(tmp_path):
    def run_git(*arguments):
        return subprocess.run(
            ["git", *arguments],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        ).stdout

    run_git("init", "-q")
    run_git("config", "user.name", "CovaPIE Test")
    run_git("config", "user.email", "covapie-test@example.invalid")

    for relative_path in checker.MODEL_SOURCE_PATHS:
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("base\n")
    run_git("add", *checker.MODEL_SOURCE_PATHS)
    run_git("commit", "-q", "-m", "base")
    base_commit = run_git("rev-parse", "HEAD").strip().decode()

    for relative_path in checker.MODEL_SOURCE_PATHS:
        (tmp_path / relative_path).write_text("modified\n")
    support_paths = checker.EXPECTED_AUTHORIZED_PATHS - set(
        checker.MODEL_SOURCE_PATHS
    )
    for relative_path in support_paths:
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("support\n")

    before_commit = checker._candidate_paths_since_base(
        repo_root=tmp_path,
        base_commit=base_commit,
    )
    assert before_commit == checker.EXPECTED_AUTHORIZED_PATHS

    run_git("add", *sorted(checker.EXPECTED_AUTHORIZED_PATHS))
    run_git("commit", "-q", "-m", "implementation")
    after_commit = checker._candidate_paths_since_base(
        repo_root=tmp_path,
        base_commit=base_commit,
    )
    assert after_commit == before_commit == checker.EXPECTED_AUTHORIZED_PATHS


def test_support_files_do_not_imply_repository_cli_forwarding():
    authorized = set(checker.EXPECTED_AUTHORIZED_PATHS)
    changed_callers, caller_bytes_bound = checker._repository_cli_path_evidence(
        repo_root=ROOT,
        candidate_paths=authorized,
    )
    assert changed_callers == set()
    assert caller_bytes_bound is True
    assert not changed_callers and caller_bytes_bound

    with_caller_drift = authorized | {"test.py"}
    changed_callers, caller_bytes_bound = checker._repository_cli_path_evidence(
        repo_root=ROOT,
        candidate_paths=with_caller_drift,
    )
    assert changed_callers == {"test.py"}
    assert caller_bytes_bound is True
    assert not (not changed_callers and caller_bytes_bound)


def test_repository_caller_evidence_is_implementation_commit_snapshot(monkeypatch):
    demo_path = ROOT / "scripts/covalent_inpaint_demo.py"
    relative_path = "scripts/covalent_inpaint_demo.py"
    expected_sha256 = checker.REPOSITORY_CALLER_SHA256[relative_path]
    historical_demo = checker._git_snapshot_file_bytes(
        repo_root=ROOT,
        commit=checker.IMPLEMENTATION_COMMIT,
        relative_path=relative_path,
        expected_sha256=expected_sha256,
    )
    assert hashlib.sha256(historical_demo).hexdigest() == (
        "1866dde2a7909fb431617dfa9f7de5a297b895de7930313655685823944f72a9"
    )

    original_read_bytes = Path.read_bytes

    def reject_live_demo(path):
        if path == demo_path:
            raise AssertionError("historical caller evidence read the live successor demo")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", reject_live_demo)
    changed, bound = checker._repository_cli_path_evidence(
        repo_root=ROOT,
        candidate_paths=set(checker.EXPECTED_AUTHORIZED_PATHS),
    )
    assert changed == set()
    assert bound is True
    assert checker.IMPLEMENTATION_CHECKER_CLAIMS_LIVE_SUCCESSOR_CALLER_BYTES is False
    assert checker.SUCCESSOR_CALLER_CHANGES_REQUIRE_PHASE_SPECIFIC_TESTS is True


def test_live_r1_demo_does_not_change_historical_design_response():
    response = checker._baseline_design_response()
    assert response["model_consumption_design_response_sha256"] == (
        checker.DESIGN_RESPONSE_SHA256
    )


def test_implementation_commit_scope_not_live_successor_scope():
    paths = checker._implementation_commit_paths(repo_root=ROOT)
    assert paths == checker.EXPECTED_AUTHORIZED_PATHS
    assert "scripts/covalent_inpaint_demo.py" not in paths


@pytest.mark.parametrize(
    "relative_path",
    ["/absolute", "../outside", "nested/../outside", "nul\x00path"],
)
def test_git_snapshot_reader_rejects_invalid_paths(relative_path):
    _assert_canonical_error(
        lambda: checker._git_snapshot_file_bytes(
            repo_root=ROOT,
            commit=checker.IMPLEMENTATION_COMMIT,
            relative_path=relative_path,
            expected_sha256="0" * 64,
        )
    )


@pytest.mark.parametrize("relative_path", ["missing-snapshot-blob", "."])
def test_git_snapshot_reader_rejects_missing_and_non_blob(relative_path):
    _assert_canonical_error(
        lambda: checker._git_snapshot_file_bytes(
            repo_root=ROOT,
            commit=checker.IMPLEMENTATION_COMMIT,
            relative_path=relative_path,
            expected_sha256="0" * 64,
        )
    )


def test_git_snapshot_reader_rejects_oversize_and_sha_drift():
    relative_path = "scripts/covalent_inpaint_demo.py"
    expected = checker.REPOSITORY_CALLER_SHA256[relative_path]
    source = inspect.getsource(checker._git_snapshot_file_bytes)
    assert 'run("cat-file", "-t", object_spec)' in source
    assert 'run("cat-file", "-s", object_spec)' in source
    assert 'run("show", object_spec)' in source
    assert all(token not in source for token in ("fetch", "checkout", "worktree"))
    _assert_canonical_error(
        lambda: checker._git_snapshot_file_bytes(
            repo_root=ROOT,
            commit=checker.IMPLEMENTATION_COMMIT,
            relative_path=relative_path,
            expected_sha256=expected,
            maximum=2,
        )
    )
    _assert_canonical_error(
        lambda: checker._git_snapshot_file_bytes(
            repo_root=ROOT,
            commit=checker.IMPLEMENTATION_COMMIT,
            relative_path=relative_path,
            expected_sha256="0" * 64,
        )
    )
