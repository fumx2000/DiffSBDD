from __future__ import annotations

import ast
import builtins
import copy
import hashlib
import inspect
import os
import subprocess
import sys
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace
from typing import Callable, NoReturn

import pytest
import torch
from torch import nn
from Bio.PDB import Polypeptide as _polypeptide


if not hasattr(_polypeptide, "three_to_one"):
    _polypeptide.three_to_one = lambda name: (
        _polypeptide.protein_letters_3to1[name]
    )

import lightning_modules
import train
from dataset import ProcessedLigandPocketDataset
from lightning_modules import LigandPocketDDPM
from covalent_ext import (
    covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1
    as compiler_context_owner,
)
from covalent_ext import (
    covapie_current11_task2_batch_index_remap_adapter_context_v1
    as remap_context_owner,
)
from covalent_ext import (
    covapie_current11_task2_batch_index_remap_contract_gate_v1
    as historical_remap_gate,
)
from covalent_ext import (
    covapie_current11_task2_lightning_runtime_integration_v1 as integration,
)
from covalent_ext.covapie_current11_task2_lightning_module_v1 import (
    CovapieCurrent11Task2LigandPocketDDPM,
)
from scripts import (
    check_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1
    as bridge_checker,
)
from scripts import check_covapie_current11_task2_runtime_caller_v1 as caller_checker


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT.parent / "covapie-state"
BASE_COMMIT = "3ec46092d33bac24e91ca5c1e3f4b8215399ad25"
FORMAL_CARRIER = STATE / caller_checker._FORMAL_CARRIER
FIELD = "covapie_current11_task2_runtime_result_v1"
TARGET_FIELD = "pocket_target_residue_atom_condition_indicator"
INTEGRATION_ERROR = (
    "COVAPIE_CURRENT11_TASK2_LIGHTNING_RUNTIME_INTEGRATION_V1_ERROR"
)
STRUCTURED_RUNTIME_FAILURE = (
    "COVAPIE_CURRENT11_TASK2_LIGHTNING_RUNTIME_INTEGRATION_V1_"
    "STRUCTURED_RUNTIME_FAILURE"
)
VIRTUAL_NODES_UNSUPPORTED = (
    "COVAPIE_CURRENT11_TASK2_LIGHTNING_RUNTIME_INTEGRATION_V1_"
    "VIRTUAL_NODES_UNSUPPORTED"
)
CALLER_ERROR = "COVAPIE_CURRENT11_TASK2_RUNTIME_CALLER_V1_ERROR"

SUCCESS_CASES = (
    ("canonical", list(range(11))),
    ("reversed", list(reversed(range(11)))),
    ("subset_10_4_0", [10, 4, 0]),
    ("singleton_10", [10]),
)
PRECOMMIT_PATHS = {
    "?? src/covalent_ext/covapie_current11_task2_lightning_runtime_integration_v1.py",
    "?? src/covalent_ext/covapie_current11_task2_lightning_module_v1.py",
    " M train.py",
    "?? tests/test_covapie_current11_task2_lightning_runtime_integration_v1.py",
}


class _Params(SimpleNamespace):
    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)


class _DummyDDPM(nn.Module):
    def __init__(self, *, dynamics: nn.Module, atom_nf: int, residue_nf: int,
                 **unused: object):
        super().__init__()
        del unused
        self.dynamics = dynamics
        self.atom_nf = atom_nf
        self.residue_nf = residue_nf


def _constructor_kwargs(**updates: object) -> dict[str, object]:
    values: dict[str, object] = {
        "outdir": Path("/tmp/covapie-test-output"),
        "dataset": "crossdock",
        "datadir": "/tmp/covapie-test-data",
        "batch_size": 2,
        "lr": 1e-3,
        "egnn_params": _Params(
            joint_nf=4,
            device="cpu",
            hidden_nf=8,
            n_layers=1,
            attention=False,
            tanh=False,
            norm_constant=1,
            inv_sublayers=1,
            sin_embedding=False,
            normalization_factor=1,
            aggregation_method="sum",
            edge_cutoff_ligand=None,
            edge_cutoff_pocket=None,
            edge_cutoff_interaction=None,
            reflection_equivariant=False,
            edge_embedding_dim=None,
        ),
        "diffusion_params": _Params(
            diffusion_loss_type="l2",
            diffusion_steps=2,
            diffusion_noise_schedule="polynomial_2",
            diffusion_noise_precision=1e-4,
            normalize_factors=[1, 1],
        ),
        "num_workers": 0,
        "augment_noise": 0,
        "augment_rotation": False,
        "clip_grad": False,
        "eval_epochs": 1,
        "eval_params": _Params(eval_batch_size=2, smiles_file=None),
        "visualize_sample_epoch": 1,
        "visualize_chain_epoch": 1,
        "auxiliary_loss": False,
        "loss_params": _Params(),
        "mode": "pocket_conditioning",
        "node_histogram": [0, 1, 1],
        "pocket_representation": "full-atom",
        "virtual_nodes": False,
        "target_residue_atom_conditioning": False,
    }
    values.update(updates)
    return values


def _patch_constructor_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        lightning_modules,
        "dataset_params",
        copy.deepcopy(lightning_modules.dataset_params),
    )
    monkeypatch.setattr(
        lightning_modules, "BasicMolecularMetrics", lambda *args: object()
    )
    monkeypatch.setattr(
        lightning_modules, "MoleculeProperties", lambda: object()
    )
    monkeypatch.setattr(
        lightning_modules, "CategoricalDistribution", lambda *args: object()
    )
    monkeypatch.setattr(
        lightning_modules, "EGNNDynamics", lambda **unused: nn.Identity()
    )
    monkeypatch.setattr(lightning_modules, "ConditionalDDPM", _DummyDDPM)
    monkeypatch.setattr(lightning_modules, "SimpleConditionalDDPM", _DummyDDPM)
    monkeypatch.setattr(lightning_modules, "EnVariationalDiffusion", _DummyDDPM)


def _construct_model(
    monkeypatch: pytest.MonkeyPatch, **updates: object
) -> CovapieCurrent11Task2LigandPocketDDPM:
    _patch_constructor_dependencies(monkeypatch)
    return CovapieCurrent11Task2LigandPocketDDPM(
        **_constructor_kwargs(**updates)
    )


def _bare_model(*, enabled: bool) -> CovapieCurrent11Task2LigandPocketDDPM:
    model = object.__new__(CovapieCurrent11Task2LigandPocketDDPM)
    nn.Module.__init__(model)
    model.covapie_current11_task2_runtime_enabled = enabled
    model.covapie_repository_root = str(ROOT) if enabled else None
    model.covapie_state_root = str(STATE) if enabled else None
    model._covapie_current11_task2_remap_context_v1 = None
    model._covapie_current11_task2_compiler_context_v1 = None
    model.datadir = "/unused"
    model.data_transform = None
    return model


def _assert_integration_error(action: Callable[[], object]) -> None:
    with pytest.raises(ValueError, match=f"^{INTEGRATION_ERROR}$"):
        action()


def _batch_fingerprint(value: object) -> object:
    if isinstance(value, torch.Tensor):
        return (
            "tensor",
            id(value),
            str(value.dtype),
            str(value.device),
            tuple(value.shape),
            int(value._version),
            value.detach().cpu().clone(),
        )
    if type(value) is dict:
        return (
            "dict",
            id(value),
            tuple((key, _batch_fingerprint(item)) for key, item in value.items()),
        )
    if type(value) is list:
        return ("list", id(value), tuple(_batch_fingerprint(x) for x in value))
    if type(value) is tuple:
        return ("tuple", id(value), tuple(_batch_fingerprint(x) for x in value))
    return ("scalar", type(value).__name__, value)


def _fingerprint_equal(left: object, right: object) -> bool:
    if type(left) is tuple and type(right) is tuple:
        if len(left) != len(right):
            return False
        if left and left[0] == right[0] == "tensor":
            return left[:-1] == right[:-1] and torch.equal(left[-1], right[-1])
        return all(_fingerprint_equal(a, b) for a, b in zip(left, right))
    return left == right


def _assert_builtin_only(value: object) -> None:
    if type(value) is dict:
        assert all(type(key) is str for key in value)
        for item in value.values():
            _assert_builtin_only(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _assert_builtin_only(item)
        return
    assert value is None or type(value) in (str, int, bool, float)


def _run_git(*arguments: str) -> str:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert completed.stderr == ""
    return completed.stdout


def _integration_repository_lifecycle() -> str:
    assert _run_git("branch", "--show-current").strip() == "main"
    head = _run_git("rev-parse", "HEAD").strip()
    origin = _run_git("rev-parse", "origin/main").strip()
    relation = _run_git(
        "rev-list", "--left-right", "--count", "HEAD...origin/main"
    ).strip()
    status = set(
        _run_git(
            "status", "--porcelain=v1", "--untracked-files=all"
        ).splitlines()
    )
    if (
        status == PRECOMMIT_PATHS
        and head == origin == BASE_COMMIT
        and relation == "0\t0"
    ):
        return "precommit-candidate"
    if not status and head == origin and relation == "0\t0":
        _run_git("merge-base", "--is-ancestor", BASE_COMMIT, "HEAD")
        return "clean-published-successor"
    raise AssertionError(
        {"head": head, "origin": origin, "relation": relation, "status": status}
    )


@pytest.fixture(scope="module")
def formal_bundle() -> dict[str, object]:
    lifecycle = _integration_repository_lifecycle()
    if lifecycle == "precommit-candidate":
        remap_context, acquisition = bridge_checker._acquire_remap_context(
            lifecycle="precommit-untracked",
            repo_root=ROOT,
            state_root=STATE,
        )
        assert acquisition["test_harness_only"] is True
        assert acquisition["real_public_remap_context_build_performed"] is False
        assert acquisition["production_monkeypatch_used"] is False
        real_public_context_build = False
    else:
        remap_context = remap_context_owner.build_covapie_current11_task2_batch_index_remap_adapter_context_v1(
            repo_root=ROOT,
            state_root=STATE,
        )
        real_public_context_build = True
    compiler_context = compiler_context_owner.build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1(
        remap_context=remap_context,
    )
    return {
        "lifecycle": lifecycle,
        "real_public_context_build": real_public_context_build,
        "remap_context": remap_context,
        "compiler_context": compiler_context,
        "dataset": ProcessedLigandPocketDataset(FORMAL_CARRIER, center=False),
    }


def _formal_batch(
    formal_bundle: dict[str, object], indices: list[int]
) -> dict[str, object]:
    dataset = formal_bundle["dataset"]
    assert isinstance(dataset, ProcessedLigandPocketDataset)
    return dataset.collate_fn([dataset[index] for index in indices])


def _formal_model(
    formal_bundle: dict[str, object]
) -> CovapieCurrent11Task2LigandPocketDDPM:
    model = _bare_model(enabled=True)
    model._covapie_current11_task2_remap_context_v1 = formal_bundle[
        "remap_context"
    ]
    model._covapie_current11_task2_compiler_context_v1 = formal_bundle[
        "compiler_context"
    ]
    return model


def test_helper_public_api_tokens_and_import_boundary() -> None:
    assert integration.__all__ == (
        "validate_covapie_current11_task2_lightning_runtime_configuration_v1",
        "build_or_reuse_covapie_current11_task2_lightning_runtime_context_pair_v1",
        "attach_covapie_current11_task2_lightning_runtime_result_v1",
    )
    assert integration.INTEGRATION_ERROR == INTEGRATION_ERROR
    assert integration.STRUCTURED_RUNTIME_FAILURE == STRUCTURED_RUNTIME_FAILURE
    assert integration.VIRTUAL_NODES_UNSUPPORTED == VIRTUAL_NODES_UNSUPPORTED
    assert integration.SIDECAR_FIELD == FIELD
    source = Path(integration.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert imports == {"__future__", "pathlib", "typing", "covalent_ext"}
    assert "pytorch_lightning" not in source
    assert "lightning_modules" not in source
    assert "from dataset" not in source
    assert "lru_cache" not in source


def test_frozen_base_owner_identity_and_historical_runtime_inventory() -> None:
    path = ROOT / "lightning_modules.py"
    payload = path.read_bytes()
    assert len(payload) == 50939
    assert payload.count(b"\n") == 1250
    assert hashlib.sha256(payload).hexdigest() == (
        "7431b5cf24d4f918df961eb97c75f2e296c8b3c523fb627063f3a6c2f08fc983"
    )
    assert _run_git("hash-object", "lightning_modules.py").strip() == (
        "d19f18ec2841a9a3163d099f4df451d97ce795d4"
    )
    assert _run_git("rev-parse", "HEAD:lightning_modules.py").strip() == (
        "d19f18ec2841a9a3163d099f4df451d97ce795d4"
    )
    inventory = historical_remap_gate._runtime_inventory(ROOT)
    row = next(
        item for item in inventory
        if item["relative_path"] == "lightning_modules.py"
    )
    assert row["bytes"] == 50939
    assert row["LF"] == 1250
    assert row["SHA256"] == hashlib.sha256(payload).hexdigest()
    assert row["Git_blob"] == _run_git(
        "hash-object", "lightning_modules.py"
    ).strip()


def test_train_covapie_import_is_function_local() -> None:
    tree = ast.parse((ROOT / "train.py").read_text(encoding="utf-8"))
    top_level = (
        node for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
    )
    assert not any(
        (
            isinstance(node, ast.ImportFrom)
            and node.module is not None
            and (
                node.module == "covalent_ext"
                or node.module.startswith("covalent_ext.")
            )
        )
        or (
            isinstance(node, ast.Import)
            and any(
                alias.name == "covalent_ext"
                or alias.name.startswith("covalent_ext.")
                for alias in node.names
            )
        )
        for node in top_level
    )
    selector = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_select_lightning_module_class"
    )
    lazy_imports = [
        node for node in ast.walk(selector)
        if isinstance(node, ast.ImportFrom)
        and node.module == (
            "covalent_ext."
            "covapie_current11_task2_lightning_module_v1"
        )
    ]
    assert len(lazy_imports) == 1
    assert [alias.name for alias in lazy_imports[0].names] == [
        "CovapieCurrent11Task2LigandPocketDDPM"
    ]


def test_historical_train_import_without_repository_src() -> None:
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    probe = subprocess.run(
        (
            sys.executable,
            "-B",
            "-c",
            "import sys; "
            "from pathlib import Path; "
            "from Bio.PDB import Polypeptide as _polypeptide; "
            "setattr(_polypeptide, 'three_to_one', "
            "lambda name: _polypeptide.protein_letters_3to1[name]) "
            "if not hasattr(_polypeptide, 'three_to_one') else None; "
            "assert str(Path.cwd() / 'src') not in sys.path; "
            "import train; "
            "assert not any(name == 'covalent_ext' or "
            "name.startswith('covalent_ext.') for name in sys.modules); "
            "print('historical_train_top_level_covapie_import=false')",
        ),
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert probe.returncode == 0, (probe.stdout, probe.stderr)
    assert probe.stdout.strip() == (
        "historical_train_top_level_covapie_import=false"
    )


def test_historical_selector_does_not_attempt_covapie_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    imported: list[str] = []
    real_import = builtins.__import__

    def tracked_import(
        name: str, *args: object, **kwargs: object
    ) -> object:
        if name == (
            "covalent_ext."
            "covapie_current11_task2_lightning_module_v1"
        ):
            imported.append(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", tracked_import)
    selected = train._select_lightning_module_class(Namespace(batch_size=2))
    assert selected is LigandPocketDDPM
    assert imported == []


def test_subclass_is_explicit_signature_mirrored_opt_in_owner() -> None:
    assert CovapieCurrent11Task2LigandPocketDDPM.__module__ == (
        "covalent_ext.covapie_current11_task2_lightning_module_v1"
    )
    assert CovapieCurrent11Task2LigandPocketDDPM.__bases__ == (
        LigandPocketDDPM,
    )
    assert "on_before_batch_transfer" not in LigandPocketDDPM.__dict__
    assert {
        name
        for name, value in CovapieCurrent11Task2LigandPocketDDPM.__dict__.items()
        if inspect.isfunction(value)
    } == {"__init__", "setup", "on_before_batch_transfer"}
    base = inspect.signature(LigandPocketDDPM.__init__)
    subclass = inspect.signature(CovapieCurrent11Task2LigandPocketDDPM.__init__)
    base_names = list(base.parameters)
    subclass_names = list(subclass.parameters)
    assert subclass_names[:len(base_names)] == base_names
    assert subclass_names[len(base_names):] == [
        "covapie_current11_task2_runtime_enabled",
        "covapie_repository_root",
        "covapie_state_root",
    ]


def test_constructor_defaults_state_hparams_and_context_exclusion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    signature = inspect.signature(CovapieCurrent11Task2LigandPocketDDPM.__init__)
    assert signature.parameters[
        "covapie_current11_task2_runtime_enabled"
    ].default is False
    assert signature.parameters["covapie_repository_root"].default is None
    assert signature.parameters["covapie_state_root"].default is None
    model = _construct_model(monkeypatch)
    assert model.covapie_current11_task2_runtime_enabled is False
    assert model.covapie_repository_root is None
    assert model.covapie_state_root is None
    assert model._covapie_current11_task2_remap_context_v1 is None
    assert model._covapie_current11_task2_compiler_context_v1 is None
    assert model.hparams["covapie_current11_task2_runtime_enabled"] is False
    assert model.hparams["covapie_repository_root"] is None
    assert model.hparams["covapie_state_root"] is None
    for historical_field in _constructor_kwargs():
        assert historical_field in model.hparams
    forbidden = {
        "_covapie_current11_task2_remap_context_v1",
        "_covapie_current11_task2_compiler_context_v1",
    }
    assert forbidden.isdisjoint(model.hparams)
    assert all(
        not any(name.endswith(field) for field in forbidden)
        for name in model.state_dict()
    )
    assert forbidden.isdisjoint(dict(model.named_parameters()))
    assert forbidden.isdisjoint(dict(model.named_buffers()))


def test_activation_validation_and_disabled_virtual_node_compatibility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validate = (
        integration.validate_covapie_current11_task2_lightning_runtime_configuration_v1
    )
    validate(
        enabled=False,
        repository_root=None,
        state_root=None,
        virtual_nodes=1,
    )
    model = _construct_model(monkeypatch, virtual_nodes=True)
    assert model.covapie_current11_task2_runtime_enabled is False
    assert model.virtual_nodes is True
    validate(
        enabled=True,
        repository_root="/does/not/need/to/exist",
        state_root="/also/explicit/and/absolute",
        virtual_nodes=False,
    )


@pytest.mark.parametrize(
    "virtual_nodes",
    (0, 1, None, "false", torch.tensor(False)),
)
def test_enabled_virtual_nodes_requires_exact_bool(
    virtual_nodes: object,
) -> None:
    _assert_integration_error(
        lambda: integration.validate_covapie_current11_task2_lightning_runtime_configuration_v1(
            enabled=True,
            repository_root=str(ROOT),
            state_root=str(STATE),
            virtual_nodes=virtual_nodes,
        )
    )


@pytest.mark.parametrize(
    "values",
    (
        {"enabled": 0, "repository_root": None, "state_root": None},
        {"enabled": False, "repository_root": "/repo", "state_root": None},
        {"enabled": False, "repository_root": None, "state_root": "/state"},
        {"enabled": True, "repository_root": None, "state_root": "/state"},
        {"enabled": True, "repository_root": "", "state_root": "/state"},
        {"enabled": True, "repository_root": "relative", "state_root": "/state"},
        {"enabled": True, "repository_root": Path("/repo"), "state_root": "/state"},
        {"enabled": True, "repository_root": "/repo", "state_root": "relative"},
    ),
)
def test_invalid_activation_configuration_fails_closed(
    values: dict[str, object],
) -> None:
    _assert_integration_error(
        lambda: integration.validate_covapie_current11_task2_lightning_runtime_configuration_v1(
            **values,
            virtual_nodes=False,
        )
    )


def test_enabled_virtual_nodes_fail_before_model_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_constructor_dependencies(monkeypatch)
    calls = 0

    def forbidden_dynamics(**unused: object) -> NoReturn:
        nonlocal calls
        del unused
        calls += 1
        raise AssertionError("model construction reached")

    monkeypatch.setattr(lightning_modules, "EGNNDynamics", forbidden_dynamics)
    with pytest.raises(ValueError, match=f"^{VIRTUAL_NODES_UNSUPPORTED}$"):
        CovapieCurrent11Task2LigandPocketDDPM(
            **_constructor_kwargs(
                virtual_nodes=True,
                covapie_current11_task2_runtime_enabled=True,
                covapie_repository_root=str(ROOT),
                covapie_state_root=str(STATE),
            )
        )
    assert calls == 0


def _activation(config: dict[str, object]) -> tuple[object, object, object]:
    args = Namespace(**config)
    return (
        getattr(args, "covapie_current11_task2_runtime_enabled", False),
        getattr(args, "covapie_repository_root", None),
        getattr(args, "covapie_state_root", None),
    )


def test_resume_case_a_old_checkpoint_and_old_config_defaults_disabled() -> None:
    merged = train.merge_configs({"batch_size": 2}, {"lr": 1e-3})
    assert _activation(merged) == (False, None, None)
    assert train._select_lightning_module_class(Namespace(**merged)) is (
        LigandPocketDDPM
    )


def test_resume_case_b_old_checkpoint_preserves_current_explicit_opt_in() -> None:
    current = {
        "covapie_current11_task2_runtime_enabled": True,
        "covapie_repository_root": str(ROOT),
        "covapie_state_root": str(STATE),
    }
    merged = train.merge_configs(dict(current), {"batch_size": 4})
    assert _activation(merged) == (
        True,
        str(ROOT),
        str(STATE),
    )
    assert train._select_lightning_module_class(Namespace(**merged)) is (
        CovapieCurrent11Task2LigandPocketDDPM
    )


def test_resume_case_c_new_checkpoint_restores_all_three_values() -> None:
    current = {
        "covapie_current11_task2_runtime_enabled": False,
        "covapie_repository_root": None,
        "covapie_state_root": None,
    }
    resumed = {
        "covapie_current11_task2_runtime_enabled": True,
        "covapie_repository_root": "/checkpoint/repository",
        "covapie_state_root": "/checkpoint/state",
    }
    with pytest.warns(UserWarning, match="will be overwritten"):
        merged = train.merge_configs(current, resumed)
    assert _activation(merged) == (
        True,
        "/checkpoint/repository",
        "/checkpoint/state",
    )
    assert train._select_lightning_module_class(Namespace(**merged)) is (
        CovapieCurrent11Task2LigandPocketDDPM
    )


def test_resume_case_d_saved_disabled_fields_still_select_subclass() -> None:
    merged = train.merge_configs(
        {"batch_size": 2},
        {
            "covapie_current11_task2_runtime_enabled": False,
            "covapie_repository_root": None,
            "covapie_state_root": None,
        },
    )
    assert _activation(merged) == (False, None, None)
    assert train._select_lightning_module_class(Namespace(**merged)) is (
        CovapieCurrent11Task2LigandPocketDDPM
    )


@pytest.mark.parametrize("field", train._COVAPIE_CURRENT11_TASK2_INTEGRATION_FIELDS)
def test_any_single_integration_field_lazy_imports_and_selects_subclass(
    field: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    imported: list[str] = []
    real_import = builtins.__import__

    def tracked_import(
        name: str, *args: object, **kwargs: object
    ) -> object:
        if name == (
            "covalent_ext."
            "covapie_current11_task2_lightning_module_v1"
        ):
            imported.append(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", tracked_import)
    assert train._select_lightning_module_class(
        Namespace(**{field: object()})
    ) is CovapieCurrent11Task2LigandPocketDDPM
    assert imported == [
        "covalent_ext.covapie_current11_task2_lightning_module_v1"
    ]


def test_train_forwards_missing_safe_getattr_defaults() -> None:
    tree = ast.parse((ROOT / "train.py").read_text(encoding="utf-8"))
    assignment = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "covapie_kwargs"
            for target in node.targets
        )
        and isinstance(node.value, ast.Dict)
        and len(node.value.keys) == 3
    )
    keywords = {
        ast.literal_eval(key): value
        for key, value in zip(
            assignment.value.keys, assignment.value.values, strict=True
        )
    }
    expected = {
        "covapie_current11_task2_runtime_enabled": False,
        "covapie_repository_root": None,
        "covapie_state_root": None,
    }
    for field, default in expected.items():
        value = keywords[field]
        assert isinstance(value, ast.Call)
        assert isinstance(value.func, ast.Name) and value.func.id == "getattr"
        assert isinstance(value.args[0], ast.Name) and value.args[0].id == "args"
        assert ast.literal_eval(value.args[1]) == field
        assert ast.literal_eval(value.args[2]) is default


def test_formal_context_uses_profile_appropriate_acquisition(
    formal_bundle: dict[str, object],
) -> None:
    lifecycle = formal_bundle["lifecycle"]
    assert lifecycle in {
        "precommit-candidate",
        "clean-published-successor",
    }
    assert formal_bundle["real_public_context_build"] is (
        lifecycle == "clean-published-successor"
    )


def test_enabled_setup_builds_before_dataset_and_reuses_same_pair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _bare_model(enabled=True)
    remap_context = object()
    compiler_context = object()
    events: list[object] = []

    def build_remap(**kwargs: object) -> object:
        events.append(("remap", kwargs))
        return remap_context

    def build_compiler(*, remap_context: object) -> object:
        events.append(("compiler", remap_context))
        return compiler_context

    def dataset(path: Path, transform: object) -> object:
        events.append(("dataset", path.name, transform))
        return object()

    monkeypatch.setattr(
        integration._remap_context_owner,
        "build_covapie_current11_task2_batch_index_remap_adapter_context_v1",
        build_remap,
    )
    monkeypatch.setattr(
        integration._compiler_context_owner,
        "build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1",
        build_compiler,
    )
    monkeypatch.setattr(lightning_modules, "ProcessedLigandPocketDataset", dataset)
    model.setup("fit")
    assert [event[0] for event in events] == [
        "remap",
        "compiler",
        "dataset",
        "dataset",
    ]
    assert events[1] == ("compiler", remap_context)
    assert model._covapie_current11_task2_remap_context_v1 is remap_context
    assert model._covapie_current11_task2_compiler_context_v1 is compiler_context
    events.clear()
    model.setup("fit")
    assert [event[0] for event in events] == ["dataset", "dataset"]
    assert model._covapie_current11_task2_remap_context_v1 is remap_context
    assert model._covapie_current11_task2_compiler_context_v1 is compiler_context


def test_context_assignment_is_atomic_on_compiler_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _bare_model(enabled=True)
    remap_context = object()
    dataset_calls = 0

    monkeypatch.setattr(
        integration._remap_context_owner,
        "build_covapie_current11_task2_batch_index_remap_adapter_context_v1",
        lambda **unused: remap_context,
    )

    def compiler_failure(*, remap_context: object) -> NoReturn:
        assert remap_context is not None
        raise RuntimeError("compiler build failed")

    def dataset(*unused: object, **unused_kwargs: object) -> object:
        nonlocal dataset_calls
        del unused, unused_kwargs
        dataset_calls += 1
        return object()

    monkeypatch.setattr(
        integration._compiler_context_owner,
        "build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1",
        compiler_failure,
    )
    monkeypatch.setattr(lightning_modules, "ProcessedLigandPocketDataset", dataset)
    _assert_integration_error(lambda: model.setup("fit"))
    assert model._covapie_current11_task2_remap_context_v1 is None
    assert model._covapie_current11_task2_compiler_context_v1 is None
    assert dataset_calls == 0


def test_first_enabled_test_setup_builds_pair_before_test_dataset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _bare_model(enabled=True)
    remap_context = object()
    compiler_context = object()
    events: list[object] = []

    def build_remap(**unused: object) -> object:
        del unused
        events.append("remap")
        return remap_context

    def build_compiler(*, remap_context: object) -> object:
        events.append(("compiler", remap_context))
        return compiler_context

    def dataset(path: Path, transform: object) -> object:
        del transform
        events.append(("dataset", path.name))
        return object()

    monkeypatch.setattr(
        integration._remap_context_owner,
        "build_covapie_current11_task2_batch_index_remap_adapter_context_v1",
        build_remap,
    )
    monkeypatch.setattr(
        integration._compiler_context_owner,
        "build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1",
        build_compiler,
    )
    monkeypatch.setattr(lightning_modules, "ProcessedLigandPocketDataset", dataset)
    model.setup("test")
    assert events == [
        "remap",
        ("compiler", remap_context),
        ("dataset", "test.npz"),
    ]
    assert model._covapie_current11_task2_remap_context_v1 is remap_context
    assert model._covapie_current11_task2_compiler_context_v1 is compiler_context


@pytest.mark.parametrize("missing", ("remap", "compiler"))
def test_partial_context_state_fails_closed_without_repair(
    monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    model = _bare_model(enabled=True)
    model._covapie_current11_task2_remap_context_v1 = (
        None if missing == "remap" else object()
    )
    model._covapie_current11_task2_compiler_context_v1 = (
        None if missing == "compiler" else object()
    )
    builder_calls = 0

    def forbidden(**unused: object) -> NoReturn:
        nonlocal builder_calls
        del unused
        builder_calls += 1
        raise AssertionError("partial state repaired")

    monkeypatch.setattr(
        integration._remap_context_owner,
        "build_covapie_current11_task2_batch_index_remap_adapter_context_v1",
        forbidden,
    )
    _assert_integration_error(lambda: model.setup("test"))
    assert builder_calls == 0


def test_disabled_setup_has_zero_context_builds_and_historical_dataset_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _bare_model(enabled=False)
    builds = 0
    paths: list[str] = []

    def forbidden(**unused: object) -> NoReturn:
        nonlocal builds
        del unused
        builds += 1
        raise AssertionError("disabled context build")

    def dataset(path: Path, transform: object) -> object:
        del transform
        paths.append(path.name)
        return object()

    monkeypatch.setattr(
        integration,
        "build_or_reuse_covapie_current11_task2_lightning_runtime_context_pair_v1",
        forbidden,
    )
    monkeypatch.setattr(lightning_modules, "ProcessedLigandPocketDataset", dataset)
    model.setup("fit")
    model.setup("test")
    assert builds == 0
    assert paths == ["train.npz", "val.npz", "test.npz"]


def test_disabled_hook_returns_same_object_without_batch_inspection_or_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _bare_model(enabled=False)
    calls = 0

    class MalformedBatch:
        def __iter__(self) -> NoReturn:
            raise AssertionError("batch inspected")

        def __contains__(self, unused: object) -> NoReturn:
            del unused
            raise AssertionError("batch inspected")

    batch = MalformedBatch()

    def forbidden(**unused: object) -> NoReturn:
        nonlocal calls
        del unused
        calls += 1
        raise AssertionError("caller reached")

    monkeypatch.setattr(
        integration._caller_owner,
        "run_covapie_current11_task2_runtime_caller_v1",
        forbidden,
    )
    assert model.on_before_batch_transfer(batch, 999) is batch
    assert calls == 0


@pytest.mark.parametrize(
    ("batch", "remap_context", "compiler_context"),
    (
        ([], object(), object()),
        ({}, None, None),
        ({}, object(), None),
        ({}, None, object()),
    ),
)
def test_enabled_hook_wrong_batch_and_missing_context_fail_without_lazy_build(
    monkeypatch: pytest.MonkeyPatch,
    batch: object,
    remap_context: object,
    compiler_context: object,
) -> None:
    model = _bare_model(enabled=True)
    model._covapie_current11_task2_remap_context_v1 = remap_context
    model._covapie_current11_task2_compiler_context_v1 = compiler_context
    calls = 0

    def forbidden(**unused: object) -> NoReturn:
        nonlocal calls
        del unused
        calls += 1
        raise AssertionError("caller reached")

    monkeypatch.setattr(
        integration._caller_owner,
        "run_covapie_current11_task2_runtime_caller_v1",
        forbidden,
    )
    _assert_integration_error(lambda: model.on_before_batch_transfer(batch, 0))
    assert calls == 0


def test_reserved_key_collision_preserves_original_and_skips_caller(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _bare_model(enabled=True)
    model._covapie_current11_task2_remap_context_v1 = object()
    model._covapie_current11_task2_compiler_context_v1 = object()
    original = object()
    batch = {FIELD: original}
    calls = 0

    def forbidden(**unused: object) -> NoReturn:
        nonlocal calls
        del unused
        calls += 1
        raise AssertionError("caller reached")

    monkeypatch.setattr(
        integration._caller_owner,
        "run_covapie_current11_task2_runtime_caller_v1",
        forbidden,
    )
    _assert_integration_error(lambda: model.on_before_batch_transfer(batch, 0))
    assert batch[FIELD] is original
    assert calls == 0


@pytest.mark.parametrize(
    "runtime_status",
    ("extractor_failure", "compiler_failure", "remap_failure"),
)
def test_structured_terminals_stop_before_step_dispatch(
    monkeypatch: pytest.MonkeyPatch, runtime_status: str
) -> None:
    model = _bare_model(enabled=True)
    model._covapie_current11_task2_remap_context_v1 = object()
    model._covapie_current11_task2_compiler_context_v1 = object()
    step_calls = 0

    monkeypatch.setattr(
        integration._caller_owner,
        "run_covapie_current11_task2_runtime_caller_v1",
        lambda **unused: {"runtime_status": runtime_status},
    )

    def step(unused_batch: object) -> None:
        nonlocal step_calls
        del unused_batch
        step_calls += 1

    batch: dict[str, object] = {}

    def transfer_then_step() -> None:
        wrapped = model.on_before_batch_transfer(batch, 0)
        step(wrapped)

    with pytest.raises(RuntimeError, match=f"^{STRUCTURED_RUNTIME_FAILURE}$"):
        transfer_then_step()
    assert step_calls == 0
    assert FIELD not in batch


def test_runtime_caller_programming_error_same_object_and_cause_propagate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _bare_model(enabled=True)
    model._covapie_current11_task2_remap_context_v1 = object()
    model._covapie_current11_task2_compiler_context_v1 = object()
    original_cause = RuntimeError("caller cause")
    original_error = ValueError(CALLER_ERROR)

    def programming_error(**unused: object) -> NoReturn:
        del unused
        raise original_error from original_cause

    monkeypatch.setattr(
        integration._caller_owner,
        "run_covapie_current11_task2_runtime_caller_v1",
        programming_error,
    )
    with pytest.raises(ValueError, match=f"^{CALLER_ERROR}$") as captured:
        model.on_before_batch_transfer({}, 0)
    assert captured.value is original_error
    assert captured.value.__cause__ is original_cause


@pytest.mark.parametrize(("case_id", "indices"), SUCCESS_CASES)
def test_formal_four_success_cases_shallow_wrap_exact_identity_and_cpu_entry(
    formal_bundle: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
    case_id: str,
    indices: list[int],
) -> None:
    del case_id
    model = _formal_model(formal_bundle)
    batch = _formal_batch(formal_bundle, indices)
    before = _batch_fingerprint(batch)
    existing = dict(batch)
    captured: dict[str, object] = {}
    caller_calls = 0
    original_caller = (
        integration._caller_owner.run_covapie_current11_task2_runtime_caller_v1
    )

    def counted_caller(**kwargs: object) -> dict[str, object]:
        nonlocal caller_calls
        caller_calls += 1
        caller_batch = kwargs["batch"]
        assert type(caller_batch) is dict
        assert FIELD not in caller_batch
        assert all(
            value.device.type == "cpu"
            for value in caller_batch.values()
            if isinstance(value, torch.Tensor)
        )
        result = original_caller(**kwargs)
        captured["result"] = result
        return result

    monkeypatch.setattr(
        integration._caller_owner,
        "run_covapie_current11_task2_runtime_caller_v1",
        counted_caller,
    )
    wrapped = model.on_before_batch_transfer(batch, 0)
    assert type(wrapped) is dict
    assert caller_calls == 1
    assert wrapped is not batch
    assert wrapped[FIELD] is captured["result"]
    assert wrapped[FIELD]["runtime_status"] == "full_success"
    assert set(wrapped) - set(batch) == {FIELD}
    assert len(wrapped) == len(batch) + 1
    assert all(wrapped[key] is value for key, value in existing.items())
    assert FIELD not in batch
    assert _fingerprint_equal(before, _batch_fingerprint(batch))


def test_multiple_hooks_do_not_build_contexts(
    formal_bundle: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    model = _formal_model(formal_bundle)
    builds = 0

    def forbidden(**unused: object) -> NoReturn:
        nonlocal builds
        del unused
        builds += 1
        raise AssertionError("per-batch context build")

    monkeypatch.setattr(
        integration._remap_context_owner,
        "build_covapie_current11_task2_batch_index_remap_adapter_context_v1",
        forbidden,
    )
    monkeypatch.setattr(
        integration._compiler_context_owner,
        "build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1",
        forbidden,
    )
    first = model.on_before_batch_transfer(_formal_batch(formal_bundle, [10]), 0)
    second = model.on_before_batch_transfer(_formal_batch(formal_bundle, [4]), 0)
    assert first[FIELD]["runtime_status"] == "full_success"
    assert second[FIELD]["runtime_status"] == "full_success"
    assert builds == 0


def test_target_residue_sidecar_coexists_without_semantic_change(
    formal_bundle: dict[str, object],
) -> None:
    model = _formal_model(formal_bundle)
    baseline_batch = _formal_batch(formal_bundle, [10, 4, 0])
    baseline = model.on_before_batch_transfer(baseline_batch, 0)[FIELD]
    batch = _formal_batch(formal_bundle, [10, 4, 0])
    indicator = torch.zeros(len(batch["pocket_coords"]), dtype=torch.bool)
    batch[TARGET_FIELD] = indicator
    wrapped = model.on_before_batch_transfer(batch, 0)
    assert wrapped[TARGET_FIELD] is indicator
    assert torch.equal(wrapped[TARGET_FIELD], indicator)
    assert wrapped[FIELD] == baseline
    assert wrapped[FIELD] is not wrapped[TARGET_FIELD]
    assert set((FIELD, TARGET_FIELD)).issubset(wrapped)


def test_unknown_generic_sample_fails_closed_as_compiler_failure(
    formal_bundle: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    model = _formal_model(formal_bundle)
    batch = _formal_batch(formal_bundle, [10])
    batch["names"] = ["not-a-current11-sample"]
    captured: dict[str, object] = {}
    original_caller = (
        integration._caller_owner.run_covapie_current11_task2_runtime_caller_v1
    )

    def capture_failure(**kwargs: object) -> dict[str, object]:
        result = original_caller(**kwargs)
        captured.update(result)
        return result

    monkeypatch.setattr(
        integration._caller_owner,
        "run_covapie_current11_task2_runtime_caller_v1",
        capture_failure,
    )
    with pytest.raises(RuntimeError, match=f"^{STRUCTURED_RUNTIME_FAILURE}$"):
        model.on_before_batch_transfer(batch, 0)
    assert captured["runtime_status"] == "compiler_failure"
    assert captured["failure_reason"] == "BATCH_SAMPLE_KEY_UNKNOWN"
    assert FIELD not in batch


def test_default_lightning_transfer_preserves_sidecar_semantics(
    formal_bundle: dict[str, object],
) -> None:
    model = _formal_model(formal_bundle)
    batch = _formal_batch(formal_bundle, [10, 4, 0])
    wrapped = model.on_before_batch_transfer(batch, 0)
    sidecar_before = copy.deepcopy(wrapped[FIELD])
    _assert_builtin_only(sidecar_before)
    tensor_before = {
        key: value.detach().clone()
        for key, value in wrapped.items()
        if isinstance(value, torch.Tensor)
    }
    transferred = model.transfer_batch_to_device(
        wrapped, torch.device("cpu"), 0
    )
    for key, value in tensor_before.items():
        assert transferred[key].device.type == "cpu"
        assert torch.equal(transferred[key], value)
    assert transferred[FIELD] == sidecar_before
    _assert_builtin_only(transferred[FIELD])
    assert not any(
        isinstance(value, torch.Tensor)
        for value in transferred[FIELD].values()
    )
