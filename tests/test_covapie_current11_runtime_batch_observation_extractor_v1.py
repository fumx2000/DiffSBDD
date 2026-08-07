from __future__ import annotations

import ast
import copy
import importlib.util
import inspect
import json
import os
import stat
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Sequence

import numpy as np
import pytest
import torch

from dataset import ProcessedLigandPocketDataset
from covalent_ext import covapie_current11_runtime_batch_observation_extractor_v1 as extractor
from covalent_ext import covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1 as gate
from covalent_ext import covapie_current11_task2_batch_descriptor_compiler_v1 as compiler
from covalent_ext import covapie_current11_task2_batch_index_remap_adapter_v1 as adapter


REPO = Path(__file__).resolve().parents[1]
STATE = REPO.parent / "covapie-state"
NPZ = (
    STATE
    / "formal-sidecars/current11-runtime-sample-and-role-order-carrier-v1/"
    "current11_runtime_sample_and_role_order_carrier.npz"
)
ERROR = "COVAPIE_CURRENT11_RUNTIME_BATCH_OBSERVATION_EXTRACTOR_V1_ERROR"
FIELDS = (
    "schema_version",
    "runtime_batch_schema_version",
    "sample_key_schema_version",
    "batch_sample_keys",
    "ligand_lengths",
    "pocket_lengths",
    "ligand_membership",
    "pocket_membership",
    "joint_layout_descriptor",
    "virtual_node_policy",
    "receptors",
    "consistency_buffer_lengths",
    "debug_coordinates",
    "debug_rank_metadata",
)
EXACT4 = (
    "src/covalent_ext/covapie_current11_runtime_batch_observation_extractor_v1.py",
    "scripts/check_covapie_current11_runtime_batch_observation_extractor_v1.py",
    "tests/test_covapie_current11_runtime_batch_observation_extractor_v1.py",
    "docs/covapie_current11_runtime_batch_observation_extractor_v1_guide.md",
)


def _classify_exact4_repository_lifecycle(
    *,
    status_lines: Sequence[str],
    index_lines: Sequence[str],
    worktree_blobs: dict[str, str],
    head_blobs: dict[str, str],
) -> str:
    expected_paths = set(EXACT4)
    expected_untracked = {f"?? {path}" for path in EXACT4}
    status_rows = list(status_lines)
    index_rows = list(index_lines)

    assert len(status_rows) == len(set(status_rows))
    if set(status_rows) == expected_untracked and len(status_rows) == len(EXACT4):
        assert index_rows == []
        assert worktree_blobs == {}
        assert head_blobs == {}
        return "precommit-untracked"

    assert status_rows == []
    assert len(index_rows) == len(EXACT4)
    index_blobs: dict[str, str] = {}
    for row in index_rows:
        metadata, path = row.split("\t", 1)
        mode, blob, stage = metadata.split()
        assert mode == "100644"
        assert stage == "0"
        assert path in expected_paths
        assert path not in index_blobs
        index_blobs[path] = blob
    assert set(index_blobs) == expected_paths
    assert set(worktree_blobs) == expected_paths
    assert set(head_blobs) == expected_paths
    for path in EXACT4:
        assert worktree_blobs[path] == index_blobs[path] == head_blobs[path]
    return "clean-tracked-successor"


def _exact4_clean_index_lines(
    *, mode: str = "100644", stage: str = "0"
) -> list[str]:
    return [f"{mode} {'a' * 40} {stage}\t{path}" for path in EXACT4]


def _exact4_matching_blobs() -> dict[str, str]:
    return {path: "a" * 40 for path in EXACT4}


@pytest.fixture(scope="session")
def actual_dataset() -> ProcessedLigandPocketDataset:
    return ProcessedLigandPocketDataset(NPZ, center=False)


def _expanded(lengths: Sequence[int]) -> list[int]:
    return [
        ordinal
        for ordinal, length in enumerate(lengths)
        for _ in range(length)
    ]


def _batch(
    *,
    names: list[object] | None = None,
    receptors: list[object] | None = None,
    ligand: Sequence[int] = (2, 1),
    pocket: Sequence[int] = (1, 2),
    membership_dtype: torch.dtype = torch.float32,
    length_dtype: torch.dtype = torch.int64,
) -> dict[str, object]:
    names = [np.str_("sample-a"), np.str_("sample-b")] if names is None else names
    receptors = [np.str_("A"), np.str_("B")] if receptors is None else receptors
    ligand_list = list(ligand)
    pocket_list = list(pocket)
    return {
        "names": names,
        "receptors": receptors,
        "num_lig_atoms": torch.tensor(ligand_list, dtype=length_dtype),
        "num_pocket_nodes": torch.tensor(pocket_list, dtype=length_dtype),
        "lig_mask": torch.tensor(_expanded(ligand_list), dtype=membership_dtype),
        "pocket_mask": torch.tensor(_expanded(pocket_list), dtype=membership_dtype),
        "lig_coords": torch.zeros((sum(ligand_list), 3), dtype=torch.float32),
        "lig_one_hot": torch.zeros((sum(ligand_list), 10), dtype=torch.float32),
        "pocket_coords": torch.zeros((sum(pocket_list), 3), dtype=torch.float32),
        "pocket_one_hot": torch.zeros((sum(pocket_list), 10), dtype=torch.float32),
    }


def _failure(batch: object, reason: str) -> ValueError:
    with pytest.raises(ValueError) as captured:
        extractor.extract_covapie_current11_runtime_batch_observation_v1(batch=batch)
    error = captured.value
    assert str(error) == ERROR
    assert error.args == (ERROR,)
    assert getattr(error, "reason", None) == reason
    return error


def _assert_builtins(value: object) -> None:
    if value is None or type(value) in (str, int, bool, float):
        return
    if type(value) is list:
        for item in value:
            _assert_builtins(item)
        return
    if type(value) is dict:
        for key, item in value.items():
            assert type(key) is str
            _assert_builtins(item)
        return
    pytest.fail(f"non-built-in output value: {type(value)!r}")


def _load_checker():
    path = REPO / "scripts/check_covapie_current11_runtime_batch_observation_extractor_v1.py"
    specification = importlib.util.spec_from_file_location(
        "covapie_runtime_batch_observation_extractor_checker", path
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


@contextmanager
def _published_git_compatibility() -> Iterator[None]:
    owners = (
        gate._remap_gate._instance_builder._payload_builder._contract_gate,
        adapter._projection_contract_gate,
    )
    originals = tuple(owner._run_git for owner in owners)

    def wrapped(original):
        def compatible(root: Path, arguments: Sequence[str]) -> str:
            output = original(root, arguments)
            if tuple(arguments) in {
                ("status", "--porcelain=v1", "--untracked-files=all"),
                ("status", "--short"),
            }:
                allowed = {f"?? {path}" for path in EXACT4}
                lines = output.splitlines()
                if any(
                    len(line) >= 4
                    and line[3:] in EXACT4
                    and line not in allowed
                    for line in lines
                ):
                    raise ValueError(ERROR)
                output = "\n".join(line for line in lines if line not in allowed)
            return output
        return compatible

    try:
        for owner, original in zip(owners, originals):
            owner._run_git = wrapped(original)
        yield
    finally:
        for owner, original in zip(owners, originals):
            owner._run_git = original


def test_public_api_is_unique_keyword_only_and_import_is_silent() -> None:
    assert extractor.__all__ == (
        "extract_covapie_current11_runtime_batch_observation_v1",
    )
    function = extractor.extract_covapie_current11_runtime_batch_observation_v1
    signature = inspect.signature(function)
    assert tuple(signature.parameters) == ("batch",)
    assert signature.parameters["batch"].kind is inspect.Parameter.KEYWORD_ONLY
    with pytest.raises(TypeError):
        function(_batch())
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import covalent_ext.covapie_current11_runtime_batch_observation_extractor_v1",
        ],
        cwd=REPO,
        env={
            **os.environ,
            "PYTHONPATH": "src",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == ""


def test_product_source_has_only_explicit_numpy_torch_and_stdlib_dependencies() -> None:
    path = REPO / EXACT4[0]
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert imports == {"__future__", "json", "typing", "numpy", "torch"}
    forbidden = (
        "covapie_current11_task2_batch_descriptor_compiler_v1",
        "covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1",
        "covapie_current11_task2_batch_index_remap_adapter_v1",
        "rdkit",
        "openbabel",
        "requests",
        "dataset.py",
    )
    assert not any(token in source.lower() for token in forbidden)
    assert not any(
        isinstance(node, ast.Call)
        and (
            isinstance(node.func, ast.Name) and node.func.id == "open"
            or isinstance(node.func, ast.Attribute)
            and node.func.attr
            in {
                "open", "read_text", "read_bytes", "write_text", "write_bytes",
                "mkdir", "unlink", "rename", "replace", "save", "load",
            }
        )
        for node in ast.walk(tree)
    )


def test_exact14_is_ordered_json_safe_and_has_canonical_identity() -> None:
    result = extractor.extract_covapie_current11_runtime_batch_observation_v1(
        batch=_batch()
    )
    assert type(result) is dict
    assert tuple(result) == FIELDS
    assert result == {
        "schema_version": "covapie_current11_task2_batch_descriptor_compiler_input_v1",
        "runtime_batch_schema_version": "processed_ligand_pocket_dataset_collate_observation_no_virtual_v1",
        "sample_key_schema_version": "covapie_sample_index_row_id_in_names_v1",
        "batch_sample_keys": ["sample-a", "sample-b"],
        "ligand_lengths": [2, 1],
        "pocket_lengths": [1, 2],
        "ligand_membership": [0, 0, 1],
        "pocket_membership": [0, 1, 1],
        "joint_layout_descriptor": None,
        "virtual_node_policy": "no_virtual_nodes_v1",
        "receptors": ["A", "B"],
        "consistency_buffer_lengths": {
            "ligand_coords": 3,
            "ligand_one_hot": 3,
            "pocket_coords": 3,
            "pocket_one_hot": 3,
        },
        "debug_coordinates": None,
        "debug_rank_metadata": None,
    }
    _assert_builtins(result)
    encoded = json.dumps(result, ensure_ascii=True, allow_nan=False)
    assert json.loads(encoded) == result


@pytest.mark.parametrize(
    ("order", "ligand", "pocket"),
    (
        (list(range(11)), [13, 13, 13, 25, 28, 43, 42, 42, 43, 40, 21], [66, 104, 96, 208, 188, 278, 267, 257, 249, 261, 228]),
        (list(reversed(range(11))), [21, 40, 43, 42, 42, 43, 28, 25, 13, 13, 13], [228, 261, 249, 257, 267, 278, 188, 208, 96, 104, 66]),
        ([10, 4, 0], [21, 28, 13], [228, 188, 66]),
        ([10], [21], [228]),
    ),
    ids=("canonical", "reversed", "subset", "singleton"),
)
def test_actual_runtime_orders_and_float_membership(
    actual_dataset: ProcessedLigandPocketDataset,
    order: list[int],
    ligand: list[int],
    pocket: list[int],
) -> None:
    batch = ProcessedLigandPocketDataset.collate_fn(
        [actual_dataset[index] for index in order]
    )
    assert type(batch["names"]) is list
    assert all(type(value) is np.str_ for value in batch["names"])
    assert batch["num_lig_atoms"].dtype is torch.int64
    assert batch["lig_mask"].dtype is torch.float32
    result = extractor.extract_covapie_current11_runtime_batch_observation_v1(
        batch=batch
    )
    assert result["batch_sample_keys"] == [
        f"CYS_SG_SAMPLE_INDEX_{index + 1:06d}" for index in order
    ]
    assert result["ligand_lengths"] == ligand
    assert result["pocket_lengths"] == pocket
    assert result["ligand_membership"] == _expanded(ligand)
    assert result["pocket_membership"] == _expanded(pocket)
    assert all(type(value) is int for value in result["ligand_membership"])
    assert result["joint_layout_descriptor"] is None


def test_string_conversion_accepts_only_exact_builtin_and_numpy_strings() -> None:
    batch = _batch(
        names=[" alpha ".strip(), np.str_("beta-β")],
        receptors=["R1", np.str_("R2")],
    )
    result = extractor.extract_covapie_current11_runtime_batch_observation_v1(
        batch=batch
    )
    assert result["batch_sample_keys"] == ["alpha", "beta-β"]
    assert result["receptors"] == ["R1", "R2"]
    assert all(type(value) is str for value in result["batch_sample_keys"])


@pytest.mark.parametrize("value", (b"sample", 7, object()))
def test_invalid_sample_key_scalar_types_fail(value: object) -> None:
    batch = _batch()
    batch["names"] = [value, "sample-b"]
    _failure(batch, "invalid_sample_key_scalar")


@pytest.mark.parametrize("value", ("", " sample", "sample ", "\tsample"))
def test_empty_or_untrimmed_sample_keys_fail(value: str) -> None:
    batch = _batch()
    batch["names"] = [value, "sample-b"]
    _failure(batch, "invalid_sample_key_scalar")


def test_arbitrary_string_conversion_is_never_called() -> None:
    class Trap:
        def __str__(self) -> str:
            raise AssertionError("arbitrary str() called")

    batch = _batch()
    batch["names"] = [Trap(), "sample-b"]
    _failure(batch, "invalid_sample_key_scalar")


def test_missing_names_and_non_list_names_have_distinct_closed_behavior() -> None:
    batch = _batch()
    batch.pop("names")
    _failure(batch, "missing_names")
    batch = _batch()
    batch["names"] = tuple(batch["names"])
    _failure(batch, "invalid_sample_key_scalar")


@pytest.mark.parametrize("value", (b"R", 1, object()))
def test_invalid_receptor_scalar_is_unsupported_runtime_type(value: object) -> None:
    batch = _batch()
    batch["receptors"] = [value, "B"]
    _failure(batch, "unsupported_runtime_type")


@pytest.mark.parametrize("dtype", (torch.int64, torch.int32, torch.int16, torch.uint8))
def test_safe_integral_role_length_dtypes_succeed(dtype: torch.dtype) -> None:
    result = extractor.extract_covapie_current11_runtime_batch_observation_v1(
        batch=_batch(length_dtype=dtype)
    )
    assert result["ligand_lengths"] == [2, 1]
    assert all(type(value) is int for value in result["ligand_lengths"])


@pytest.mark.parametrize(
    "value",
    (
        torch.tensor([True, True]),
        torch.tensor([2.0, 1.0]),
        torch.tensor([2 + 0j, 1 + 0j]),
        torch.tensor([[2, 1]]),
        torch.tensor([2]),
        torch.tensor([2, -1]),
        [2, 1],
        torch.empty(2, dtype=torch.int64, device="meta"),
    ),
    ids=("bool", "float", "complex", "rank", "wrong-b", "negative", "non-torch", "non-cpu"),
)
def test_invalid_role_lengths_fail(value: object) -> None:
    batch = _batch()
    batch["num_lig_atoms"] = value
    _failure(batch, "invalid_role_length")


def test_missing_pocket_length_fails_invalid_role_length() -> None:
    batch = _batch()
    batch.pop("num_pocket_nodes")
    _failure(batch, "invalid_role_length")


@pytest.mark.parametrize("dtype", (torch.float32, torch.float64, torch.int64, torch.int16))
def test_real_integral_membership_dtypes_normalize_to_python_int(dtype: torch.dtype) -> None:
    result = extractor.extract_covapie_current11_runtime_batch_observation_v1(
        batch=_batch(membership_dtype=dtype)
    )
    assert result["ligand_membership"] == [0, 0, 1]
    assert all(type(value) is int for value in result["ligand_membership"])


@pytest.mark.parametrize(
    "value",
    (
        torch.tensor([float("nan"), 0.0, 1.0]),
        torch.tensor([float("inf"), 0.0, 1.0]),
        torch.tensor([-float("inf"), 0.0, 1.0]),
        torch.tensor([0.0, 0.5, 1.0]),
        torch.tensor([0.0, 0.0, -1.0]),
        torch.tensor([0.0, 0.0]),
        torch.tensor([0.0, 1.0, 1.0]),
        torch.tensor([False, False, True]),
        torch.tensor([0 + 0j, 0 + 0j, 1 + 0j]),
        [0, 0, 1],
        torch.empty(3, dtype=torch.float32, device="meta"),
        torch.tensor([[0.0, 0.0, 1.0]]),
    ),
    ids=(
        "nan", "positive-inf", "negative-inf", "non-integral", "negative",
        "wrong-total", "wrong-ordinal", "bool", "complex", "non-torch",
        "non-cpu", "rank",
    ),
)
def test_invalid_membership_fails(value: object) -> None:
    batch = _batch()
    batch["lig_mask"] = value
    _failure(batch, "invalid_membership")


def test_missing_membership_fails() -> None:
    batch = _batch()
    batch.pop("pocket_mask")
    _failure(batch, "invalid_membership")


def test_empty_dataset_collate_and_fabricated_empty_batch_boundaries() -> None:
    with pytest.raises(IndexError) as captured:
        ProcessedLigandPocketDataset.collate_fn([])
    assert str(captured.value) == "list index out of range"
    batch = _batch(names=[], receptors=[], ligand=(), pocket=())
    _failure(batch, "unsupported_empty_batch")


def test_virtual_absent_and_all_zero_count_succeed() -> None:
    batch = _batch()
    assert extractor.extract_covapie_current11_runtime_batch_observation_v1(
        batch=batch
    )["virtual_node_policy"] == "no_virtual_nodes_v1"
    batch["num_virtual_atoms"] = torch.tensor([0, 0], dtype=torch.int64)
    assert extractor.extract_covapie_current11_runtime_batch_observation_v1(
        batch=batch
    )["virtual_node_policy"] == "no_virtual_nodes_v1"


@pytest.mark.parametrize(
    "value",
    (
        torch.tensor([0, 1]),
        torch.tensor([0.0, 0.0]),
        torch.tensor([False, False]),
        torch.tensor([0]),
        [0, 0],
    ),
    ids=("nonzero", "float", "bool", "wrong-b", "non-torch"),
)
def test_nonzero_or_malformed_virtual_count_fails(value: object) -> None:
    batch = _batch()
    batch["num_virtual_atoms"] = value
    _failure(batch, "virtual_nodes_not_supported")


def test_other_virtual_payload_fails_even_when_empty() -> None:
    batch = _batch()
    batch["virtual_coords"] = torch.empty((0, 3))
    _failure(batch, "virtual_nodes_not_supported")


@pytest.mark.parametrize(
    "field",
    ("lig_coords", "lig_one_hot", "pocket_coords", "pocket_one_hot"),
)
def test_each_missing_buffer_fails_length_mismatch(field: str) -> None:
    batch = _batch()
    batch.pop(field)
    _failure(batch, "buffer_length_mismatch")


@pytest.mark.parametrize(
    "field",
    ("lig_coords", "lig_one_hot", "pocket_coords", "pocket_one_hot"),
)
def test_each_rank_zero_buffer_fails_length_mismatch(field: str) -> None:
    batch = _batch()
    batch[field] = torch.tensor(0.0)
    _failure(batch, "buffer_length_mismatch")


@pytest.mark.parametrize(
    "field",
    ("lig_coords", "lig_one_hot", "pocket_coords", "pocket_one_hot"),
)
def test_each_wrong_leading_buffer_fails_length_mismatch(field: str) -> None:
    batch = _batch()
    batch[field] = torch.zeros((4, 3))
    _failure(batch, "buffer_length_mismatch")


@pytest.mark.parametrize(
    "value",
    ([1, 2, 3], torch.empty((3, 3), device="meta")),
    ids=("non-torch", "non-cpu"),
)
def test_buffer_unsupported_types_fail(value: object) -> None:
    batch = _batch()
    batch["lig_coords"] = value
    _failure(batch, "unsupported_runtime_type")


def test_determinism_and_no_input_mutation() -> None:
    batch = _batch()
    names = batch["names"]
    receptors = batch["receptors"]
    tensor_snapshots = {
        key: (id(value), value.clone(), value._version)
        for key, value in batch.items()
        if isinstance(value, torch.Tensor)
    }
    first = extractor.extract_covapie_current11_runtime_batch_observation_v1(
        batch=batch
    )
    second = extractor.extract_covapie_current11_runtime_batch_observation_v1(
        batch=batch
    )
    assert first == second
    assert json.dumps(
        first, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ) == json.dumps(
        second, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    )
    assert batch["names"] is names and batch["receptors"] is receptors
    assert names == [np.str_("sample-a"), np.str_("sample-b")]
    for key, (identity, content, version) in tensor_snapshots.items():
        current = batch[key]
        assert id(current) == identity
        assert torch.equal(current, content)
        assert current._version == version


def test_top_level_exact_dict_and_precedence() -> None:
    class DictSubclass(dict):
        pass

    _failure(DictSubclass(_batch()), "unsupported_runtime_type")
    batch = _batch()
    batch.pop("names")
    batch["num_lig_atoms"] = torch.tensor([1.0])
    _failure(batch, "missing_names")
    batch = _batch(names=[])
    batch["num_lig_atoms"] = torch.tensor([1.0])
    _failure(batch, "unsupported_empty_batch")
    batch = _batch()
    batch["num_lig_atoms"] = torch.tensor([2.0, 1.0])
    batch["receptors"] = [1, 2]
    _failure(batch, "invalid_role_length")


def test_unexpected_internal_exception_is_chained_and_normalized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = extractor._sample_keys

    def explode(batch: dict[str, object]) -> list[str]:
        del batch
        raise RuntimeError("boom")

    monkeypatch.setattr(extractor, "_sample_keys", explode)
    error = _failure(_batch(), "unsupported_runtime_type")
    assert type(error.__cause__) is RuntimeError
    monkeypatch.setattr(extractor, "_sample_keys", original)


def test_extractor_is_dynamically_gate_compiler_adapter_independent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args, **kwargs):
        del args, kwargs
        raise AssertionError("forbidden authority call")

    monkeypatch.setattr(
        gate,
        "build_covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1",
        forbidden,
    )
    monkeypatch.setattr(
        compiler,
        "compile_covapie_current11_task2_batch_descriptor_v1",
        forbidden,
    )
    monkeypatch.setattr(
        adapter,
        "build_covapie_current11_task2_batch_index_remap_adapter_v1",
        forbidden,
    )
    assert extractor.extract_covapie_current11_runtime_batch_observation_v1(
        batch=_batch()
    )["ligand_lengths"] == [2, 1]


@pytest.mark.parametrize(
    "arguments",
    (
        (),
        ("-h",),
        ("--help",),
        ("--repo-root", str(REPO)),
        ("--batch", "x"),
        ("--input", "x"),
        ("--json", "x"),
        ("--compiler", "x"),
        ("--adapter", "x"),
        ("--write", "x"),
        ("--output", "x"),
        ("--dataloader", "x"),
        ("--model", "x"),
        ("--loss", "x"),
        ("--train", "x"),
        ("extra",),
    ),
)
def test_checker_rejects_help_expanded_scope_and_missing_roots(
    arguments: tuple[str, ...],
) -> None:
    checker = _load_checker()
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        checker._main(arguments)


@pytest.mark.parametrize(
    ("lifecycle", "head", "origin"),
    (
        ("precommit-base", "05e8694eb3cdfe9c1aa4cd9728d4820b7322ba5e", "05e8694eb3cdfe9c1aa4cd9728d4820b7322ba5e"),
        ("committed-unpushed", "extractor-successor", "05e8694eb3cdfe9c1aa4cd9728d4820b7322ba5e"),
        ("published-successor", "extractor-successor", "extractor-successor"),
    ),
)
def test_checker_lineage_accepts_base_and_clean_successors_without_origin_admission(
    monkeypatch: pytest.MonkeyPatch,
    lifecycle: str,
    head: str,
    origin: str,
) -> None:
    checker = _load_checker()
    calls: list[tuple[str, ...]] = []

    def run_git(repo: Path, arguments: Sequence[str]) -> str:
        assert repo == REPO
        call = tuple(arguments)
        calls.append(call)
        if call == ("branch", "--show-current"):
            return "main\n"
        if call == (
            "cat-file", "-e", f"{checker._BASE_COMMIT}^{{commit}}",
        ):
            return ""
        if call == (
            "merge-base", "--is-ancestor", checker._BASE_COMMIT, "HEAD",
        ):
            assert lifecycle in {
                "precommit-base", "committed-unpushed", "published-successor",
            }
            assert head
            return ""
        if call == ("rev-parse", "origin/main"):
            pytest.fail(f"origin unexpectedly used for admission: {origin}")
        pytest.fail(f"unexpected git admission call: {call!r}")

    monkeypatch.setattr(checker, "_run_git", run_git)
    checker._validate_repository_lineage(REPO)
    assert calls == [
        ("branch", "--show-current"),
        ("cat-file", "-e", f"{checker._BASE_COMMIT}^{{commit}}"),
        ("merge-base", "--is-ancestor", checker._BASE_COMMIT, "HEAD"),
    ]
    if lifecycle == "committed-unpushed":
        assert head != origin == checker._BASE_COMMIT
    if lifecycle == "published-successor":
        assert head == origin != checker._BASE_COMMIT


@pytest.mark.parametrize(
    ("failure", "branch", "base_exists", "base_is_ancestor"),
    (
        ("wrong-branch", "feature", True, True),
        ("base-missing", "main", False, False),
        ("base-not-ancestor", "main", True, False),
    ),
)
def test_checker_lineage_fails_wrong_branch_missing_base_and_nonancestor(
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
    branch: str,
    base_exists: bool,
    base_is_ancestor: bool,
) -> None:
    checker = _load_checker()
    calls: list[tuple[str, ...]] = []

    def run_git(repo: Path, arguments: Sequence[str]) -> str:
        assert repo == REPO
        call = tuple(arguments)
        calls.append(call)
        if call == ("branch", "--show-current"):
            return branch + "\n"
        if call[0:2] == ("cat-file", "-e"):
            if base_exists:
                return ""
            raise ValueError(ERROR)
        if call[0:2] == ("merge-base", "--is-ancestor"):
            if base_is_ancestor:
                return ""
            raise ValueError(ERROR)
        pytest.fail(f"unexpected git admission call: {call!r}")

    monkeypatch.setattr(checker, "_run_git", run_git)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        checker._validate_repository_lineage(REPO)
    if failure == "wrong-branch":
        assert calls == [("branch", "--show-current")]
    elif failure == "base-missing":
        assert calls[-1][0:2] == ("cat-file", "-e")
    else:
        assert calls[-1][0:2] == ("merge-base", "--is-ancestor")


def test_checker_dataset_frozen_blob_drift_still_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker()

    def run_git(repo: Path, arguments: Sequence[str]) -> str:
        assert repo == REPO
        call = tuple(arguments)
        if call == ("rev-parse", "HEAD:dataset.py"):
            return "0" * 40 + "\n"
        if call == ("hash-object", "dataset.py"):
            return checker._DATASET_BLOB + "\n"
        pytest.fail(f"unexpected dataset identity call: {call!r}")

    monkeypatch.setattr(checker, "_run_git", run_git)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        checker._validate_dataset(REPO)


def test_checker_source_uses_base_as_ancestry_floor_not_exact_head_or_origin() -> None:
    checker = _load_checker()
    path = REPO / EXACT4[1]
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }
    lineage_source = ast.get_source_segment(
        source, functions["_validate_repository_lineage"]
    )
    main_source = ast.get_source_segment(source, functions["_main"])
    snapshot_source = ast.get_source_segment(source, functions["_repo_snapshot"])
    assert lineage_source is not None and main_source is not None
    assert snapshot_source is not None
    assert "_BASE_COMMIT" in lineage_source
    assert "cat-file" in lineage_source and "merge-base" in lineage_source
    assert "origin/main" not in lineage_source
    assert "rev-parse" not in lineage_source
    assert "_validate_repository_lineage(repo)" in main_source
    assert "_BASE_COMMIT" not in main_source and "origin/main" not in main_source
    assert "origin/main" in snapshot_source
    assert "_HEAD" not in source
    assert checker._BASE_COMMIT == "05e8694eb3cdfe9c1aa4cd9728d4820b7322ba5e"


def test_checker_is_extractor_only_and_success_cli_is_one_json_line() -> None:
    path = REPO / EXACT4[1]
    source = path.read_text(encoding="utf-8")
    assert "task2_batch_descriptor_compiler_v1" not in source
    assert "task2_batch_descriptor_compiler_contract_gate_v1" not in source
    assert "task2_batch_index_remap_adapter_v1" not in source
    completed = subprocess.run(
        [
            sys.executable,
            str(path),
            "--repo-root",
            str(REPO),
            "--state-root",
            str(STATE),
        ],
        cwd=REPO,
        env={
            **os.environ,
            "PYTHONPATH": "src",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stderr == ""
    assert completed.stdout.count("\n") == 1
    summary = json.loads(completed.stdout)
    assert summary["status"] == "PASS_RUNTIME_BATCH_OBSERVATION_EXTRACTOR_ONLY"
    assert summary["exact14_field_count"] == 14
    assert summary["formal_state_unchanged"] is True
    assert summary["repository_unchanged"] is True


def test_checker_failure_cli_has_empty_stdout_and_fixed_stderr() -> None:
    path = REPO / EXACT4[1]
    completed = subprocess.run(
        [sys.executable, str(path), "--help"],
        cwd=REPO,
        env={
            **os.environ,
            "PYTHONPATH": "src",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    assert completed.returncode == 1
    assert completed.stdout == ""
    assert completed.stderr == ERROR + "\n"


@pytest.mark.parametrize(
    ("status_lines", "index_lines", "worktree_blobs", "head_blobs", "expected"),
    [
        (
            [f"?? {path}" for path in EXACT4],
            [],
            {},
            {},
            "precommit-untracked",
        ),
        (
            [],
            _exact4_clean_index_lines(),
            _exact4_matching_blobs(),
            _exact4_matching_blobs(),
            "clean-tracked-successor",
        ),
    ],
    ids=("all-untracked", "clean-tracked-exact-blobs"),
)
def test_exact4_lifecycle_helper_accepts(
    status_lines: list[str],
    index_lines: list[str],
    worktree_blobs: dict[str, str],
    head_blobs: dict[str, str],
    expected: str,
) -> None:
    assert (
        _classify_exact4_repository_lifecycle(
            status_lines=status_lines,
            index_lines=index_lines,
            worktree_blobs=worktree_blobs,
            head_blobs=head_blobs,
        )
        == expected
    )


@pytest.mark.parametrize(
    ("status_lines", "index_lines", "worktree_blobs", "head_blobs"),
    [
        (
            [f"?? {EXACT4[0]}"],
            _exact4_clean_index_lines()[1:],
            {path: "a" * 40 for path in EXACT4[1:]},
            {path: "a" * 40 for path in EXACT4[1:]},
        ),
        ([f" M {EXACT4[0]}"], _exact4_clean_index_lines(), {}, {}),
        ([], _exact4_clean_index_lines(stage="1"), {}, {}),
        ([], _exact4_clean_index_lines(mode="100755"), {}, {}),
        (
            [],
            _exact4_clean_index_lines(),
            {**_exact4_matching_blobs(), EXACT4[0]: "b" * 40},
            _exact4_matching_blobs(),
        ),
    ],
    ids=("mixed", "tracked-dirty", "staged", "wrong-mode", "blob-drift"),
)
def test_exact4_lifecycle_helper_rejects(
    status_lines: list[str],
    index_lines: list[str],
    worktree_blobs: dict[str, str],
    head_blobs: dict[str, str],
) -> None:
    with pytest.raises(AssertionError):
        _classify_exact4_repository_lifecycle(
            status_lines=status_lines,
            index_lines=index_lines,
            worktree_blobs=worktree_blobs,
            head_blobs=head_blobs,
        )


def test_exact4_are_safe_text_files_in_precommit_or_clean_tracked_successor() -> None:
    status = subprocess.run(
        [
            "git",
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            *EXACT4,
        ],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    assert status.stderr == ""
    index = subprocess.run(
        ["git", "ls-files", "--stage", "--", *EXACT4],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    assert index.stderr == ""
    index_lines = index.stdout.splitlines()
    worktree_blobs: dict[str, str] = {}
    head_blobs: dict[str, str] = {}
    if index_lines:
        for relative in EXACT4:
            worktree_blobs[relative] = subprocess.run(
                ["git", "hash-object", "--no-filters", relative],
                cwd=REPO,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            ).stdout.strip()
            head_blobs[relative] = subprocess.run(
                ["git", "rev-parse", f"HEAD:{relative}"],
                cwd=REPO,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            ).stdout.strip()
    lifecycle = _classify_exact4_repository_lifecycle(
        status_lines=status.stdout.splitlines(),
        index_lines=index_lines,
        worktree_blobs=worktree_blobs,
        head_blobs=head_blobs,
    )
    assert lifecycle in ("precommit-untracked", "clean-tracked-successor")
    for relative in EXACT4:
        path = REPO / relative
        metadata = path.lstat()
        payload = path.read_bytes()
        assert stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
        assert stat.S_IMODE(metadata.st_mode) == 0o644
        assert 0 < len(payload) < 1024 * 1024
        assert not payload.startswith(b"\xef\xbb\xbf")
        assert b"\0" not in payload and b"\r" not in payload
        assert payload.endswith(b"\n") and not payload.endswith(b"\n\n")
        payload.decode("utf-8", errors="strict")
        assert all(not line.endswith((" ", "\t")) for line in payload.decode().splitlines())


def test_actual_subset_composes_once_through_published_compiler_and_adapter(
    actual_dataset: ProcessedLigandPocketDataset,
) -> None:
    batch = ProcessedLigandPocketDataset.collate_fn(
        [actual_dataset[index] for index in [10, 4, 0]]
    )
    observation = extractor.extract_covapie_current11_runtime_batch_observation_v1(
        batch=batch
    )
    assert observation["joint_layout_descriptor"] is None
    with _published_git_compatibility():
        compiled = compiler.compile_covapie_current11_task2_batch_descriptor_v1(
            repo_root=REPO,
            state_root=STATE,
            observation=observation,
        )
        assert compiled["compiler_status"] == "COMPILED_EXACT"
        exact2 = adapter.build_covapie_current11_task2_batch_index_remap_adapter_v1(
            repo_root=REPO,
            state_root=STATE,
            adapter_input=compiled["adapter_input_exact18"],
        )
    output = json.loads(
        exact2["current11_task2_batch_index_remap_output.json"].decode("utf-8")
    )
    report = json.loads(
        exact2["current11_task2_batch_index_remap_adapter_report.json"].decode("utf-8")
    )
    assert output["remap_status"] == "REMAPPED_EXACT"
    assert output["pair_values_joint_global_indices"] is None
    assert report["adapter_status"] == "PASS_IN_MEMORY_TASK2_BATCH_INDEX_REMAP_ONLY"
