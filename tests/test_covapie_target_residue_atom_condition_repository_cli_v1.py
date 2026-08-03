from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
import os
import subprocess
import sys
from collections import UserDict
from pathlib import Path
from types import MappingProxyType

import pytest
import torch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
CHECKPOINT = ROOT / "checkpoints/crossdocked_fullatom_cond.ckpt"
sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_target_residue_atom_condition_repository_cli_v1 as repository_cli,
)


ERROR = "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_REPOSITORY_CLI_INVALID"
TARGET_OPTIONS = {
    "--target_residue_atom_conditioning",
    "--target_chain_id",
    "--target_residue_sequence_number",
}
EXACT6_KEYS = (
    "chain_id",
    "residue_sequence_number",
    "residue_insertion_code",
    "residue_name",
    "atom_name",
    "element",
)


def _assert_invalid(action) -> None:
    with pytest.raises(ValueError) as caught:
        action()
    assert str(caught.value) == ERROR


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--ordinary", default="kept")
    return parser


def test_public_api_surface_and_keyword_only_signatures_are_exact():
    assert repository_cli.__all__ == (
        "add_covapie_target_residue_atom_condition_cli_arguments_v1",
        "resolve_covapie_target_residue_atom_condition_cli_args_v1",
        "load_covapie_target_residue_conditioned_model_from_checkpoint_v1",
    )
    for name in repository_cli.__all__:
        function = getattr(repository_cli, name)
        assert callable(function)
        assert all(
            parameter.kind is inspect.Parameter.KEYWORD_ONLY
            for parameter in inspect.signature(function).parameters.values()
        )


def test_import_is_silent_lightweight_and_does_not_touch_checkpoint(tmp_path):
    before = CHECKPOINT.stat()
    before_sha = hashlib.sha256(CHECKPOINT.read_bytes()).hexdigest()
    environment = dict(os.environ)
    environment.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": str(SRC),
            "PYTHONPYCACHEPREFIX": str(tmp_path / "pycache"),
        }
    )
    command = (
        "import sys; "
        "import covalent_ext.covapie_target_residue_atom_condition_repository_cli_v1; "
        "assert 'torch' not in sys.modules; "
        "assert 'lightning_modules' not in sys.modules"
    )
    completed = subprocess.run(
        [sys.executable, "-B", "-c", command],
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    after = CHECKPOINT.stat()
    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""
    assert (after.st_size, after.st_mtime_ns) == (before.st_size, before.st_mtime_ns)
    assert hashlib.sha256(CHECKPOINT.read_bytes()).hexdigest() == before_sha


def test_parser_addition_returns_identity_and_preserves_existing_argument():
    parser = _parser()
    before_options = set(parser._option_string_actions)
    returned = repository_cli.add_covapie_target_residue_atom_condition_cli_arguments_v1(
        parser=parser
    )
    assert returned is parser
    assert set(parser._option_string_actions) - before_options == TARGET_OPTIONS
    assert parser.parse_args([]) == argparse.Namespace(
        ordinary="kept",
        target_residue_atom_conditioning=False,
        target_chain_id=None,
        target_residue_sequence_number=None,
    )


def test_parser_uses_only_the_three_long_options_and_exact_actions():
    parser = argparse.ArgumentParser(add_help=False)
    repository_cli.add_covapie_target_residue_atom_condition_cli_arguments_v1(
        parser=parser
    )
    assert set(parser._option_string_actions) == TARGET_OPTIONS
    actions = {action.dest: action for action in parser._actions}
    assert isinstance(
        actions["target_residue_atom_conditioning"], argparse._StoreTrueAction
    )
    assert actions["target_residue_atom_conditioning"].default is False
    assert actions["target_chain_id"].type is str
    assert actions["target_chain_id"].default is None
    assert actions["target_residue_sequence_number"].type is int
    assert actions["target_residue_sequence_number"].default is None


@pytest.mark.parametrize("option", sorted(TARGET_OPTIONS))
def test_parser_rejects_any_preexisting_target_option(option):
    parser = _parser()
    parser.add_argument(option)
    original_actions = tuple(parser._actions)
    _assert_invalid(
        lambda: repository_cli.add_covapie_target_residue_atom_condition_cli_arguments_v1(
            parser=parser
        )
    )
    assert tuple(parser._actions) == original_actions


def test_parser_rejects_wrong_type():
    _assert_invalid(
        lambda: repository_cli.add_covapie_target_residue_atom_condition_cli_arguments_v1(
            parser=object()
        )
    )


def test_parser_registration_failure_is_normalized_and_rolled_back():
    class FailingParser(argparse.ArgumentParser):
        def __init__(self):
            self.target_additions = 0
            super().__init__(add_help=False)

        def add_argument(self, *args, **kwargs):
            if args and args[0] in TARGET_OPTIONS:
                self.target_additions += 1
                if self.target_additions == 2:
                    raise argparse.ArgumentError(None, "forced conflict")
            return super().add_argument(*args, **kwargs)

    parser = FailingParser()
    _assert_invalid(
        lambda: repository_cli.add_covapie_target_residue_atom_condition_cli_arguments_v1(
            parser=parser
        )
    )
    assert not TARGET_OPTIONS.intersection(parser._option_string_actions)


def test_store_true_parse_semantics_and_explicit_string_rejection(capsys):
    parser = argparse.ArgumentParser(add_help=False)
    repository_cli.add_covapie_target_residue_atom_condition_cli_arguments_v1(
        parser=parser
    )
    assert parser.parse_args([]).target_residue_atom_conditioning is False
    assert (
        parser.parse_args(["--target_residue_atom_conditioning"])
        .target_residue_atom_conditioning
        is True
    )
    with pytest.raises(SystemExit):
        parser.parse_args(["--target_residue_atom_conditioning", "true"])
    capsys.readouterr()


def test_real_parse_then_resolve_legacy_and_conditioned_paths():
    parser = argparse.ArgumentParser(add_help=False)
    repository_cli.add_covapie_target_residue_atom_condition_cli_arguments_v1(
        parser=parser
    )
    legacy = parser.parse_args([])
    assert (
        repository_cli.resolve_covapie_target_residue_atom_condition_cli_args_v1(
            arguments=legacy
        )
        is None
    )
    conditioned = parser.parse_args(
        [
            "--target_residue_atom_conditioning",
            "--target_chain_id",
            "A",
            "--target_residue_sequence_number",
            "123",
        ]
    )
    assert repository_cli.resolve_covapie_target_residue_atom_condition_cli_args_v1(
        arguments=conditioned
    ) == {
        "chain_id": "A",
        "residue_sequence_number": 123,
        "residue_insertion_code": " ",
        "residue_name": "CYS",
        "atom_name": "SG",
        "element": "S",
    }


@pytest.mark.parametrize(
    "arguments",
    [
        {},
        {"ordinary": "unchanged"},
        {
            "target_residue_atom_conditioning": False,
            "target_chain_id": None,
            "target_residue_sequence_number": None,
        },
    ],
)
def test_legacy_mode_returns_none(arguments):
    assert (
        repository_cli.resolve_covapie_target_residue_atom_condition_cli_args_v1(
            arguments=arguments
        )
        is None
    )


def test_mapping_and_namespace_inputs_are_not_modified():
    mapping_source = {
        "ordinary": ["preserved"],
        "target_residue_atom_conditioning": True,
        "target_chain_id": "AA",
        "target_residue_sequence_number": -8,
    }
    mapping = MappingProxyType(mapping_source)
    namespace = argparse.Namespace(**mapping_source)
    namespace_before = dict(vars(namespace))
    expected = {
        "chain_id": "AA",
        "residue_sequence_number": -8,
        "residue_insertion_code": " ",
        "residue_name": "CYS",
        "atom_name": "SG",
        "element": "S",
    }
    assert repository_cli.resolve_covapie_target_residue_atom_condition_cli_args_v1(
        arguments=mapping
    ) == expected
    assert repository_cli.resolve_covapie_target_residue_atom_condition_cli_args_v1(
        arguments=namespace
    ) == expected
    assert mapping_source["ordinary"] == ["preserved"]
    assert vars(namespace) == namespace_before


@pytest.mark.parametrize("residue_number", [-7, 0, 14])
def test_exact6_type_order_fixed_values_and_all_integer_signs(residue_number):
    selector = repository_cli.resolve_covapie_target_residue_atom_condition_cli_args_v1(
        arguments={
            "target_residue_atom_conditioning": True,
            "target_chain_id": "1",
            "target_residue_sequence_number": residue_number,
            "resi_list": [999],
            "ref_ligand": "ignored.sdf",
        }
    )
    assert type(selector) is dict
    assert tuple(selector) == EXACT6_KEYS
    assert selector == {
        "chain_id": "1",
        "residue_sequence_number": residue_number,
        "residue_insertion_code": " ",
        "residue_name": "CYS",
        "atom_name": "SG",
        "element": "S",
    }


@pytest.mark.parametrize(
    "enabled",
    [None, 0, 1, "true", "false", torch.tensor(True), torch.tensor(False)],
)
def test_enable_flag_requires_exact_bool(enabled):
    _assert_invalid(
        lambda: repository_cli.resolve_covapie_target_residue_atom_condition_cli_args_v1(
            arguments={"target_residue_atom_conditioning": enabled}
        )
    )


def test_numpy_bool_enable_flag_is_rejected():
    numpy = pytest.importorskip("numpy")
    _assert_invalid(
        lambda: repository_cli.resolve_covapie_target_residue_atom_condition_cli_args_v1(
            arguments={"target_residue_atom_conditioning": numpy.bool_(True)}
        )
    )


@pytest.mark.parametrize(
    "arguments",
    [
        {"target_residue_atom_conditioning": True},
        {"target_residue_atom_conditioning": True, "target_chain_id": "A"},
        {
            "target_residue_atom_conditioning": True,
            "target_residue_sequence_number": 1,
        },
        {"target_chain_id": "A"},
        {"target_residue_sequence_number": 1},
        {
            "target_residue_atom_conditioning": False,
            "target_chain_id": "A",
        },
        {
            "target_residue_atom_conditioning": False,
            "target_residue_sequence_number": 1,
        },
    ],
)
def test_partial_or_disabled_selector_fails_closed(arguments):
    _assert_invalid(
        lambda: repository_cli.resolve_covapie_target_residue_atom_condition_cli_args_v1(
            arguments=arguments
        )
    )


@pytest.mark.parametrize("chain", ["", " ", "\t", " A", "A ", "\tA", "A\t", 1])
def test_chain_requires_nonempty_already_stripped_exact_string(chain):
    _assert_invalid(
        lambda: repository_cli.resolve_covapie_target_residue_atom_condition_cli_args_v1(
            arguments={
                "target_residue_atom_conditioning": True,
                "target_chain_id": chain,
                "target_residue_sequence_number": 1,
            }
        )
    )


@pytest.mark.parametrize("chain", ["A", "B", "AA", "1"])
def test_valid_chain_forms_are_accepted(chain):
    selector = repository_cli.resolve_covapie_target_residue_atom_condition_cli_args_v1(
        arguments={
            "target_residue_atom_conditioning": True,
            "target_chain_id": chain,
            "target_residue_sequence_number": 1,
        }
    )
    assert selector["chain_id"] == chain


@pytest.mark.parametrize(
    "residue_number",
    [True, False, 1.0, "123", None, torch.tensor(1)],
)
def test_residue_number_requires_exact_int(residue_number):
    _assert_invalid(
        lambda: repository_cli.resolve_covapie_target_residue_atom_condition_cli_args_v1(
            arguments={
                "target_residue_atom_conditioning": True,
                "target_chain_id": "A",
                "target_residue_sequence_number": residue_number,
            }
        )
    )


def test_numpy_integer_residue_number_is_rejected():
    numpy = pytest.importorskip("numpy")
    _assert_invalid(
        lambda: repository_cli.resolve_covapie_target_residue_atom_condition_cli_args_v1(
            arguments={
                "target_residue_atom_conditioning": True,
                "target_chain_id": "A",
                "target_residue_sequence_number": numpy.int64(1),
            }
        )
    )


@pytest.mark.parametrize(
    "unknown",
    [
        "target_residue_insertion_code",
        "target_residue_name",
        "target_atom_name",
        "target_element",
        "target_residue",
        "target_atom",
        "target_unknown",
    ],
)
def test_unknown_target_fields_and_fixed_field_override_attempts_fail(unknown):
    _assert_invalid(
        lambda: repository_cli.resolve_covapie_target_residue_atom_condition_cli_args_v1(
            arguments={
                "target_residue_atom_conditioning": True,
                "target_chain_id": "A",
                "target_residue_sequence_number": 1,
                unknown: "override",
            }
        )
    )


@pytest.mark.parametrize("arguments", [object(), UserDict({1: "invalid"})])
def test_resolver_rejects_wrong_container_or_non_string_key(arguments):
    _assert_invalid(
        lambda: repository_cli.resolve_covapie_target_residue_atom_condition_cli_args_v1(
            arguments=arguments
        )
    )


def test_checkpoint_identity_reader_accepts_path_and_string():
    for checkpoint_path in (CHECKPOINT, str(CHECKPOINT)):
        path, checkpoint_bytes = repository_cli._read_frozen_checkpoint(
            checkpoint_path
        )
        assert path == CHECKPOINT
        assert len(checkpoint_bytes) == 17_861_341
        assert hashlib.sha256(checkpoint_bytes).hexdigest() == (
            "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
        )


def test_loader_returns_strict_conditioned_model_without_drift_or_output(
    monkeypatch, capfd
):
    import lightning_modules

    captured = {}
    real_torch_load = torch.load

    def capture_torch_load(*args, **kwargs):
        payload = real_torch_load(*args, **kwargs)
        state_dict = payload["state_dict"]
        captured["mapping"] = state_dict
        captured["keys"] = list(state_dict)
        captured["ids"] = {key: id(value) for key, value in state_dict.items()}
        captured["versions"] = {
            key: value._version for key, value in state_dict.items()
        }
        captured["values"] = {
            key: value.detach().clone() for key, value in state_dict.items()
        }
        captured["map_location"] = kwargs.get("map_location")
        captured["weights_only"] = kwargs.get("weights_only")
        return payload

    def forbidden_model_forward(*_args, **_kwargs):
        raise AssertionError("model execution is outside C1")

    monkeypatch.setattr(torch, "load", capture_torch_load)
    monkeypatch.setattr(
        lightning_modules.LigandPocketDDPM,
        "forward",
        forbidden_model_forward,
    )
    checkpoint_before = CHECKPOINT.read_bytes()
    checkpoint_stat_before = CHECKPOINT.stat()
    rng_before = torch.random.get_rng_state().clone()
    capfd.readouterr()
    model = repository_cli.load_covapie_target_residue_conditioned_model_from_checkpoint_v1(
        checkpoint_path=CHECKPOINT,
        map_location="cpu",
    )
    output = capfd.readouterr()
    rng_after = torch.random.get_rng_state().clone()
    checkpoint_stat_after = CHECKPOINT.stat()

    assert isinstance(model, lightning_modules.LigandPocketDDPM)
    assert model.target_residue_atom_conditioning is True
    assert model.ddpm.dynamics.target_residue_atom_conditioning is True
    parameter = model.ddpm.dynamics.target_residue_atom_condition_embedding
    assert isinstance(parameter, torch.nn.Parameter)
    assert list(parameter.shape) == [32]
    assert int(torch.count_nonzero(parameter).item()) == 0
    assert len(model.state_dict()) == 123
    assert output.out == ""
    assert output.err == ""
    assert torch.equal(rng_before, rng_after)
    assert captured["map_location"] == "cpu"
    assert captured["weights_only"] is False
    state_dict = captured["mapping"]
    assert list(state_dict) == captured["keys"]
    assert all(id(state_dict[key]) == captured["ids"][key] for key in state_dict)
    assert all(
        state_dict[key]._version == captured["versions"][key] for key in state_dict
    )
    assert all(
        torch.equal(state_dict[key], captured["values"][key]) for key in state_dict
    )
    assert CHECKPOINT.read_bytes() == checkpoint_before
    assert (checkpoint_stat_after.st_size, checkpoint_stat_after.st_mtime_ns) == (
        checkpoint_stat_before.st_size,
        checkpoint_stat_before.st_mtime_ns,
    )


def test_loader_restores_rng_and_suppresses_output_when_constructor_fails(
    monkeypatch, capfd
):
    import lightning_modules

    def failing_constructor(**_kwargs):
        print("suppressed stdout")
        print("suppressed stderr", file=sys.stderr)
        torch.rand(3)
        raise RuntimeError("forced constructor failure")

    monkeypatch.setattr(lightning_modules, "LigandPocketDDPM", failing_constructor)
    rng_before = torch.random.get_rng_state().clone()
    capfd.readouterr()
    _assert_invalid(
        lambda: repository_cli.load_covapie_target_residue_conditioned_model_from_checkpoint_v1(
            checkpoint_path=CHECKPOINT
        )
    )
    output = capfd.readouterr()
    assert output.out == ""
    assert output.err == ""
    assert torch.equal(torch.random.get_rng_state(), rng_before)


def test_loader_rejects_missing_directory_symlink_and_empty(tmp_path):
    directory = tmp_path / "directory"
    directory.mkdir()
    symlink = tmp_path / "checkpoint-link"
    symlink.symlink_to(CHECKPOINT)
    empty = tmp_path / "empty.ckpt"
    empty.write_bytes(b"")
    for invalid_path in (tmp_path / "missing.ckpt", directory, symlink, empty):
        _assert_invalid(
            lambda invalid_path=invalid_path: repository_cli.load_covapie_target_residue_conditioned_model_from_checkpoint_v1(
                checkpoint_path=invalid_path
            )
        )


def test_loader_rejects_modified_truncated_and_appended_copies(tmp_path):
    checkpoint_bytes = CHECKPOINT.read_bytes()
    modified_bytes = bytearray(checkpoint_bytes)
    modified_bytes[len(modified_bytes) // 2] ^= 1
    invalid_payloads = {
        "modified.ckpt": bytes(modified_bytes),
        "truncated.ckpt": checkpoint_bytes[:-1],
        "appended.ckpt": checkpoint_bytes + b"x",
    }
    for name, payload in invalid_payloads.items():
        path = tmp_path / name
        path.write_bytes(payload)
        _assert_invalid(
            lambda path=path: repository_cli.load_covapie_target_residue_conditioned_model_from_checkpoint_v1(
                checkpoint_path=path
            )
        )


@pytest.mark.parametrize("checkpoint_path", [None, 1, b"checkpoint", object()])
def test_loader_rejects_wrong_checkpoint_path_types(checkpoint_path):
    _assert_invalid(
        lambda: repository_cli.load_covapie_target_residue_conditioned_model_from_checkpoint_v1(
            checkpoint_path=checkpoint_path
        )
    )


def test_production_source_has_no_forbidden_execution_or_persistence_calls():
    source_path = (
        SRC
        / "covalent_ext/covapie_target_residue_atom_condition_repository_cli_v1.py"
    )
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    called_names = {
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Attribute, ast.Name))
    }
    assert "strict=False" not in source
    assert called_names.isdisjoint(
        {
            "forward",
            "prepare_pocket",
            "generate_ligands",
            "inpaint",
            "sample",
            "training_step",
            "backward",
            "optimizer",
            "save",
            "save_checkpoint",
        }
    )
