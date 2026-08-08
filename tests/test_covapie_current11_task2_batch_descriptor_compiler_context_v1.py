from __future__ import annotations

import ast
import builtins
import copy
import hashlib
import importlib.util
import inspect
import json
import os
import pickle
import stat
import subprocess
import sys
import textwrap
from dataclasses import FrozenInstanceError, fields
from pathlib import Path
from typing import Sequence

import pytest

from covalent_ext import covapie_current11_runtime_batch_observation_extractor_v1 as extractor
from covalent_ext import covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1 as context_gate
from covalent_ext import covapie_current11_task2_batch_descriptor_compiler_context_v1 as product
from covalent_ext import covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1 as compiler_gate
from covalent_ext import covapie_current11_task2_batch_descriptor_compiler_v1 as compiler
from covalent_ext import covapie_current11_task2_batch_index_remap_adapter_v1 as adapter


REPO = Path(__file__).resolve().parents[1]
STATE = REPO.parent / "covapie-state"
ERROR = "COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_V1_ERROR"
COMPILER_ERROR = "COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_V1_ERROR"
BASE_COMMIT = "ac22f9cdb8438cf97e3da6e4668e9b124d484f95"
COMPILER_SHA256 = "a7a232a4f344e5cbac152ae8cc51921f4d9bf07deaaab0d55f1ce950e67b524a"
COMPILER_BLOB = "26037347244a7b33d23b475d32f565e4580eb7fe"
KNOWN_AUTHORITY_DIGEST = (
    "e3c7c14e5a94db2bf59b5195ae6902d7fd7269e58a8690589962548860348d44"
)
EXACT4 = (
    "src/covalent_ext/"
    "covapie_current11_task2_batch_descriptor_compiler_context_v1.py",
    "scripts/"
    "check_covapie_current11_task2_batch_descriptor_compiler_context_v1.py",
    "tests/"
    "test_covapie_current11_task2_batch_descriptor_compiler_context_v1.py",
    "docs/"
    "covapie_current11_task2_batch_descriptor_compiler_context_v1_guide.md",
)
SUCCESS_SPECS = (
    ("canonical", tuple(range(11)), compiler._JOINT_LAYOUT),
    ("reversed", tuple(reversed(range(11))), compiler._JOINT_LAYOUT),
    ("subset_10_4_0", (10, 4, 0), None),
    ("singleton_10", (10,), None),
)
FAILURE_STATUSES = {
    "source_contract_override": "SOURCE_CONTRACT_MISMATCH",
    "duplicate_runtime_key": "BATCH_SAMPLE_KEY_DUPLICATED",
    "wrong_ligand_length": "ROLE_LENGTH_MISMATCH",
    "wrong_ligand_membership": "MEMBERSHIP_MASK_MISMATCH",
    "unknown_joint_descriptor": "BATCH_OBSERVATION_SCHEMA_MISMATCH",
}


def _readiness_fixture() -> dict[str, bool]:
    return {
        "task2_batch_descriptor_compiler_contract_gate_implemented": True,
        "task2_batch_descriptor_compiler_contract_gate_passed": True,
        "task2_batch_descriptor_compiler_contract_designed": True,
        "formal_runtime_carrier_verified": True,
        "source_contract_verified": True,
        "identity_provider_verified": True,
        "compiler_input_schema_frozen": True,
        "compiler_output_schema_frozen": True,
        "compiler_status_vocabulary_frozen": True,
        "compiler_reference_composition_passed": True,
        "task2_batch_descriptor_compiler_implemented": True,
        "runtime_batch_observation_extractor_implemented": False,
        "ready_for_task2_batch_descriptor_compiler_implementation": False,
        "ready_for_runtime_batch_observation_extractor_design": True,
        "ready_for_dataloader_integration": False,
        "ready_for_model_integration": False,
        "ready_for_loss_integration": False,
        "feature_semantics_reaudit_required_before_training": True,
        "ready_for_training": False,
        "checkpoint_state_dict_change_required": False,
        "base_model_parameter_shape_change_required": False,
        "base_atom_feature_width_change_required": False,
        "egnn_or_se3_backbone_change_required": False,
        "checkpoint_bytes_read": False,
    }


def _source_fixture() -> dict[str, object]:
    return {
        "schema_version": compiler._SOURCE_SCHEMA,
        "source_projection_digest": compiler._PROJECTION_DIGEST,
        "source_payload_digest": compiler._PAYLOAD_DIGEST,
        "parser_schema_version": compiler._PARSER_SCHEMA,
        "collate_schema_version": compiler._COLLATE_SCHEMA,
        "source_sample_order": [
            {
                "sample_index_row_id": identity[0],
                "sample_preparation_input_id": identity[1],
                "pdb_id": identity[2],
                "ligand_comp_id": identity[3],
                "source_sample_index": index,
            }
            for index, identity in enumerate(compiler._SOURCE_IDENTITIES)
        ],
        "source_pair_values_int64": [list(pair) for pair in compiler._SOURCE_PAIRS],
        "source_sample_offsets_int64": list(range(12)),
        "source_entry_validity_bool": [True] * 11,
        "source_sample_validity_bool": [True] * 11,
    }


def _provider_fixture(source: dict[str, object]) -> list[dict[str, object]]:
    samples = source["source_sample_order"]
    assert type(samples) is list
    provider: list[dict[str, object]] = []
    for index, sample in enumerate(samples):
        assert type(sample) is dict
        roles: dict[str, object] = {}
        for role_index, role_name in enumerate(("pocket", "ligand")):
            selected_source = compiler._SOURCE_PAIRS[index][role_index]
            digest = hashlib.sha256(
                f"context-test:{index}:{role_name}".encode("utf-8")
            ).hexdigest()
            roles[role_name] = {
                "root_kind": "repo_root",
                "relative_path": f"fixture/{index}/{role_name}.csv",
                "SHA256": digest,
                "row_count": selected_source + 20,
                "row_order_digest": digest,
                "row_order_version": "physical_csv_data_row_order_v1",
                "selected_source_row_index_0based": selected_source,
                "selected_parser_local_index": 0,
                "parser_output_atom_count": index + role_index + 2,
                "source_to_parser_local": {str(selected_source): 0},
                "selected_atom_identity": {
                    "atom_site_id": str(index + 1),
                    "atom_name": "SG" if role_name == "pocket" else "C1",
                    "type_symbol": "S" if role_name == "pocket" else "C",
                    "residue_name_or_ligand_comp_id": (
                        "CYS" if role_name == "pocket" else sample["ligand_comp_id"]
                    ),
                    "auth_asym_id": "A",
                    "auth_seq_id": str(index + 1),
                    "label_asym_id": "A",
                    "label_seq_id": str(index + 1),
                },
            }
        provider.append(
            {
                "sample_identity": {
                    field: sample[field] for field in compiler._IDENTITY_FIELDS
                },
                "roles": roles,
            }
        )
    return provider


def _authority_fixture() -> tuple[
    dict[str, object], list[dict[str, object]], dict[str, bool]
]:
    source = _source_fixture()
    return source, _provider_fixture(source), _readiness_fixture()


def _membership(lengths: Sequence[int]) -> list[int]:
    return [ordinal for ordinal, length in enumerate(lengths) for _ in range(length)]


def _observation(
    authority: tuple[dict[str, object], list[dict[str, object]], dict[str, bool]],
    order: Sequence[int],
    joint: str | None,
) -> dict[str, object]:
    source, provider, _readiness = authority
    samples = source["source_sample_order"]
    assert type(samples) is list
    ligand = [provider[index]["roles"]["ligand"]["parser_output_atom_count"] for index in order]
    pocket = [provider[index]["roles"]["pocket"]["parser_output_atom_count"] for index in order]
    return {
        "schema_version": compiler._INPUT_SCHEMA,
        "runtime_batch_schema_version": compiler._RUNTIME_SCHEMA,
        "sample_key_schema_version": compiler._SAMPLE_KEY_SCHEMA,
        "batch_sample_keys": [samples[index]["sample_index_row_id"] for index in order],
        "ligand_lengths": ligand,
        "pocket_lengths": pocket,
        "ligand_membership": _membership(ligand),
        "pocket_membership": _membership(pocket),
        "joint_layout_descriptor": joint,
        "virtual_node_policy": compiler._VIRTUAL_POLICY,
        "receptors": [samples[index]["pdb_id"] for index in order],
        "consistency_buffer_lengths": {
            "ligand_coords": sum(ligand),
            "ligand_one_hot": sum(ligand),
            "pocket_coords": sum(pocket),
            "pocket_one_hot": sum(pocket),
        },
        "debug_coordinates": None,
        "debug_rank_metadata": None,
    }


def _failure_cases(
    authority: tuple[dict[str, object], list[dict[str, object]], dict[str, bool]],
) -> dict[str, dict[str, object]]:
    base = _observation(authority, (10, 4, 0), None)

    def changed(field: str, value: object) -> dict[str, object]:
        result = copy.deepcopy(base)
        result[field] = value
        return result

    return {
        "source_contract_override": {
            **copy.deepcopy(base),
            "source_projection_digest": compiler._PROJECTION_DIGEST,
        },
        "duplicate_runtime_key": changed(
            "batch_sample_keys", [base["batch_sample_keys"][0]] * 3
        ),
        "wrong_ligand_length": changed(
            "ligand_lengths", [base["ligand_lengths"][0] + 1, *base["ligand_lengths"][1:]]
        ),
        "wrong_ligand_membership": changed("ligand_membership", []),
        "unknown_joint_descriptor": changed("joint_layout_descriptor", "unknown"),
    }


def _install_fixture_builder(
    monkeypatch: pytest.MonkeyPatch,
    authority: tuple[dict[str, object], list[dict[str, object]], dict[str, bool]],
) -> list[tuple[Path, Path]]:
    calls: list[tuple[Path, Path]] = []
    digest = product._authority_snapshot_digest_v1(*authority)
    monkeypatch.setattr(product, "_EXPECTED_AUTHORITY_SNAPSHOT_DIGEST", digest)

    def fixture_authority(repo: Path, state: Path):
        calls.append((repo, state))
        return copy.deepcopy(authority)

    monkeypatch.setattr(compiler, "_authority", fixture_authority)
    return calls


@pytest.fixture()
def authority() -> tuple[dict[str, object], list[dict[str, object]], dict[str, bool]]:
    return _authority_fixture()


@pytest.fixture()
def built(
    monkeypatch: pytest.MonkeyPatch,
    authority: tuple[dict[str, object], list[dict[str, object]], dict[str, bool]],
) -> tuple[object, list[tuple[Path, Path]]]:
    calls = _install_fixture_builder(monkeypatch, authority)
    context = product.build_covapie_current11_task2_batch_descriptor_compiler_context_v1(
        repo_root=REPO, state_root=STATE
    )
    return context, calls


def _forged_context(context: object, field: str, value: object) -> object:
    forged = object.__new__(product._CompilerContextV1)
    for name in (*product._CONTEXT_SEMANTIC_FIELDS, "construction_seal"):
        object.__setattr__(forged, name, getattr(context, name))
    object.__setattr__(forged, field, value)
    return forged


def _reachable_values(context: object) -> list[object]:
    pending = [context]
    result: list[object] = []
    seen: set[int] = set()
    while pending:
        value = pending.pop()
        if id(value) in seen:
            continue
        seen.add(id(value))
        result.append(value)
        if type(value) is tuple:
            pending.extend(value)
        elif type(value) is product._CompilerContextV1:
            pending.extend(getattr(value, field.name) for field in fields(value))
        elif type(value) is product._FrozenMapV1:
            pending.append(value.items)
        elif type(value) is product._FrozenMapEntryV1:
            pending.extend((value.key, value.value))
        elif type(value) is product._FrozenListV1:
            pending.append(value.items)
    return result


def _container_ids(value: object) -> set[int]:
    result: set[int] = set()
    pending = [value]
    while pending:
        item = pending.pop()
        if type(item) is dict:
            result.add(id(item))
            pending.extend(item.values())
        elif type(item) is list:
            result.add(id(item))
            pending.extend(item)
    return result


def _load_checker():
    specification = importlib.util.spec_from_file_location(
        "covapie_compiler_context_checker_test", REPO / EXACT4[1]
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_public_exact2_keyword_only_annotations_and_silent_import() -> None:
    assert product.__all__ == (
        "build_covapie_current11_task2_batch_descriptor_compiler_context_v1",
        "compile_covapie_current11_task2_batch_descriptor_with_context_v1",
    )
    signatures = (
        inspect.signature(
            product.build_covapie_current11_task2_batch_descriptor_compiler_context_v1
        ),
        inspect.signature(
            product.compile_covapie_current11_task2_batch_descriptor_with_context_v1
        ),
    )
    assert tuple(signatures[0].parameters) == ("repo_root", "state_root")
    assert tuple(signatures[1].parameters) == ("context", "observation")
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for signature in signatures
        for parameter in signature.parameters.values()
    )
    assert str(signatures[0].return_annotation) == "object"
    assert str(signatures[1].return_annotation) == "dict[str, object]"
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import covalent_ext.covapie_current11_task2_batch_descriptor_compiler_context_v1",
        ],
        cwd=REPO,
        env={
            **os.environ,
            "PYTHONPATH": "src:.",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == ""


def test_product_imports_only_stdlib_and_compiler_and_has_no_cache() -> None:
    source = inspect.getsource(product)
    tree = ast.parse(source)
    roots = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert roots <= set(sys.stdlib_module_names) | {"__future__", "covalent_ext"}
    assert "context_contract_gate" not in source
    assert "batch_index_remap_adapter" not in source
    assert "lru_cache" not in source and "MappingProxyType" not in source
    assignments = {
        target.id
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (node.targets if isinstance(node, ast.Assign) else (node.target,))
        if isinstance(target, ast.Name)
    }
    assert not any("CACHE" in name.upper() for name in assignments)


def test_existing_compiler_public_surface_and_bytes_remain_frozen() -> None:
    path = REPO / "src/covalent_ext/covapie_current11_task2_batch_descriptor_compiler_v1.py"
    payload = path.read_bytes()
    assert compiler.__all__ == ("compile_covapie_current11_task2_batch_descriptor_v1",)
    assert hashlib.sha256(payload).hexdigest() == COMPILER_SHA256
    assert subprocess.run(
        ["git", "hash-object", str(path.relative_to(REPO))],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    ).stdout.strip() == COMPILER_BLOB


def test_private_context_shape_semantic_order_and_no_public_class(
    built: tuple[object, list[tuple[Path, Path]]]
) -> None:
    context, calls = built
    assert type(context) is product._CompilerContextV1
    assert product._CompilerContextV1.__name__.startswith("_")
    assert product._CompilerContextV1 not in product.__all__
    assert tuple(field.name for field in fields(context)) == (
        *product._CONTEXT_SEMANTIC_FIELDS,
        "construction_seal",
    )
    assert tuple(field.name for field in fields(context)[:12]) == (
        "context_schema_version",
        "compiler_product_commit",
        "compiler_contract_commit",
        "compiler_contract_digest",
        "provider_digest",
        "formal_carrier_aggregate",
        "formal_npz_sha256",
        "source_contract_digest",
        "authority_snapshot_digest",
        "source_exact10",
        "identity_provider_exact11",
        "readiness_template",
    )
    assert calls == [(REPO, STATE)]


def test_context_graph_has_no_reachable_builtin_dict_or_list_and_is_nested_frozen(
    built: tuple[object, list[tuple[Path, Path]]]
) -> None:
    values = _reachable_values(built[0])
    assert not any(type(value) in (dict, list) for value in values)
    assert any(type(value) is product._FrozenMapV1 for value in values)
    assert any(type(value) is product._FrozenListV1 for value in values)
    assert any(type(value) is product._FrozenMapEntryV1 for value in values)


def test_context_is_frozen_sealed_has_no_public_mutator_and_repr_hides_data(
    built: tuple[object, list[tuple[Path, Path]]]
) -> None:
    context = built[0]
    with pytest.raises(FrozenInstanceError):
        context.provider_digest = "changed"
    assert context.construction_seal is product._CONSTRUCTION_SEAL
    assert not [
        name
        for name, value in vars(type(context)).items()
        if not name.startswith("_") and callable(value)
    ]
    rendered = repr(context)
    assert "CYS_SG_SAMPLE_INDEX" not in rendered
    assert product._PROVIDER_DIGEST not in rendered
    assert product._EXPECTED_AUTHORITY_SNAPSHOT_DIGEST not in rendered


def test_context_is_explicitly_non_pickleable(
    built: tuple[object, list[tuple[Path, Path]]]
) -> None:
    context = built[0]
    with pytest.raises(TypeError, match=f"^{ERROR}$"):
        pickle.dumps(context)
    with pytest.raises(TypeError, match=f"^{ERROR}$"):
        context.__reduce__()
    with pytest.raises(TypeError, match=f"^{ERROR}$"):
        context.__reduce_ex__(4)


def test_freeze_thaw_preserves_order_returns_fresh_builtins_and_isolated_mutation() -> None:
    original = {"z": [{"inner": [3, 2, 1]}], "a": {"last": True}}
    frozen = product._freeze_value_v1(original)
    first = product._thaw_value_v1(frozen)
    second = product._thaw_value_v1(frozen)
    assert type(first) is dict and type(second) is dict
    assert tuple(first) == tuple(original)
    assert first == second == original
    assert _container_ids(first).isdisjoint(_container_ids(second))
    first["z"][0]["inner"].append(0)
    assert product._thaw_value_v1(frozen) == original


@pytest.mark.parametrize(
    "invalid",
    (
        (1, 2),
        {1: "not-a-string-key"},
        float("nan"),
        float("inf"),
        object(),
    ),
)
def test_freeze_rejects_non_json_safe_values(invalid: object) -> None:
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        product._freeze_value_v1(invalid)


def test_freeze_rejects_cycles() -> None:
    cyclic: list[object] = []
    cyclic.append(cyclic)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        product._freeze_value_v1(cyclic)


def test_canonical_snapshot_manual_framing_and_contract_helper_parity(
    authority: tuple[dict[str, object], list[dict[str, object]], dict[str, bool]]
) -> None:
    source, provider, readiness = copy.deepcopy(authority)
    snapshot = product._authority_snapshot_v1(source, provider, readiness)
    payload = json.dumps(
        snapshot,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    digest = hashlib.sha256(product._AUTHORITY_SNAPSHOT_DOMAIN)
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    assert digest.hexdigest() == product._authority_snapshot_digest_v1(
        source, provider, readiness
    )
    gate_snapshot, _components, gate_digest = context_gate._authority_snapshot(
        source, provider, readiness
    )
    assert snapshot == gate_snapshot
    assert digest.hexdigest() == gate_digest


def test_production_known_authority_digest_is_frozen() -> None:
    assert product._EXPECTED_AUTHORITY_SNAPSHOT_DIGEST == KNOWN_AUTHORITY_DIGEST
    assert product._AUTHORITY_SNAPSHOT_DOMAIN == context_gate._AUTHORITY_DOMAIN


def test_builder_validates_roots_calls_authority_once_and_never_calls_slow_public(
    monkeypatch: pytest.MonkeyPatch,
    authority: tuple[dict[str, object], list[dict[str, object]], dict[str, bool]],
) -> None:
    calls: list[tuple[str, object]] = []
    digest = product._authority_snapshot_digest_v1(*authority)
    monkeypatch.setattr(product, "_EXPECTED_AUTHORITY_SNAPSHOT_DIGEST", digest)

    def root(path: Path) -> Path:
        calls.append(("root", path))
        return path

    def acquire(repo: Path, state: Path):
        calls.append(("authority", (repo, state)))
        return copy.deepcopy(authority)

    def slow(**_kwargs: object):
        calls.append(("slow", None))
        raise AssertionError("slow public compiler called")

    monkeypatch.setattr(compiler, "_require_root", root)
    monkeypatch.setattr(compiler, "_authority", acquire)
    monkeypatch.setattr(compiler, "compile_covapie_current11_task2_batch_descriptor_v1", slow)
    context = product.build_covapie_current11_task2_batch_descriptor_compiler_context_v1(
        repo_root=REPO, state_root=STATE
    )
    assert type(context) is product._CompilerContextV1
    assert calls == [
        ("root", REPO),
        ("root", STATE),
        ("authority", (REPO, STATE)),
    ]


def test_builder_uses_single_authority_normalization_boundary(
    monkeypatch: pytest.MonkeyPatch,
    authority: tuple[dict[str, object], list[dict[str, object]], dict[str, bool]],
) -> None:
    build_source = inspect.getsource(product._build_context_v1)
    helper_source = inspect.getsource(product._acquire_verified_compiler_authority_v1)
    assert "_compiler._authority" not in build_source
    assert build_source.count("_acquire_verified_compiler_authority_v1(") == 1
    assert helper_source.count("_compiler._authority(") == 1
    assert "compile_covapie_current11_task2_batch_descriptor_v1" not in helper_source
    assert "context_contract_gate" not in helper_source
    assert "batch_index_remap_adapter" not in helper_source

    digest = product._authority_snapshot_digest_v1(*authority)
    calls: list[tuple[Path, Path]] = []

    def acquire(*, repo: Path, state: Path) -> object:
        calls.append((repo, state))
        return copy.deepcopy(authority)

    monkeypatch.setattr(product, "_EXPECTED_AUTHORITY_SNAPSHOT_DIGEST", digest)
    monkeypatch.setattr(product, "_acquire_verified_compiler_authority_v1", acquire)
    monkeypatch.setattr(
        compiler,
        "_authority",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("direct authority call")
        ),
    )
    context = product.build_covapie_current11_task2_batch_descriptor_compiler_context_v1(
        repo_root=REPO, state_root=STATE
    )
    assert type(context) is product._CompilerContextV1
    assert calls == [(REPO, STATE)]


def test_builder_does_not_mutate_authority(
    monkeypatch: pytest.MonkeyPatch,
    authority: tuple[dict[str, object], list[dict[str, object]], dict[str, bool]],
) -> None:
    before = copy.deepcopy(authority)
    digest = product._authority_snapshot_digest_v1(*authority)
    monkeypatch.setattr(product, "_EXPECTED_AUTHORITY_SNAPSHOT_DIGEST", digest)
    monkeypatch.setattr(compiler, "_authority", lambda _repo, _state: authority)
    product.build_covapie_current11_task2_batch_descriptor_compiler_context_v1(
        repo_root=REPO, state_root=STATE
    )
    assert authority == before


def test_builder_invalid_root_maps_compiler_error_and_preserves_cause() -> None:
    with pytest.raises(ValueError, match=f"^{ERROR}$") as captured:
        product.build_covapie_current11_task2_batch_descriptor_compiler_context_v1(
            repo_root=Path("relative"), state_root=STATE
        )
    assert type(captured.value.__cause__) is ValueError
    assert str(captured.value.__cause__) == COMPILER_ERROR


def test_builder_authority_failure_maps_and_preserves_compiler_cause(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def failure(_repo: Path, _state: Path):
        raise ValueError(COMPILER_ERROR)

    monkeypatch.setattr(compiler, "_authority", failure)
    with pytest.raises(ValueError, match=f"^{ERROR}$") as captured:
        product.build_covapie_current11_task2_batch_descriptor_compiler_context_v1(
            repo_root=REPO, state_root=STATE
        )
    assert type(captured.value.__cause__) is ValueError
    assert str(captured.value.__cause__) == COMPILER_ERROR


def test_builder_predecessor_authority_error_is_normalized_through_compiler_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[Path, Path]] = []

    def failure(repo: Path, state: Path):
        calls.append((repo, state))
        raise ValueError("SYNTHETIC_PREDECESSOR_GATE_ERROR")

    monkeypatch.setattr(compiler, "_authority", failure)
    with pytest.raises(ValueError, match=f"^{ERROR}$") as captured:
        product.build_covapie_current11_task2_batch_descriptor_compiler_context_v1(
            repo_root=REPO, state_root=STATE
        )
    compiler_cause = captured.value.__cause__
    assert type(compiler_cause) is ValueError
    assert str(compiler_cause) == COMPILER_ERROR
    predecessor_cause = compiler_cause.__cause__
    assert type(predecessor_cause) is ValueError
    assert str(predecessor_cause) == "SYNTHETIC_PREDECESSOR_GATE_ERROR"
    assert calls == [(REPO, STATE)]


def test_builder_unexpected_authority_error_is_normalized_through_compiler_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[Path, Path]] = []

    def failure(repo: Path, state: Path):
        calls.append((repo, state))
        raise RuntimeError("boom")

    monkeypatch.setattr(compiler, "_authority", failure)
    with pytest.raises(ValueError, match=f"^{ERROR}$") as captured:
        product.build_covapie_current11_task2_batch_descriptor_compiler_context_v1(
            repo_root=REPO, state_root=STATE
        )
    compiler_cause = captured.value.__cause__
    assert type(compiler_cause) is ValueError
    assert str(compiler_cause) == COMPILER_ERROR
    unexpected_cause = compiler_cause.__cause__
    assert type(unexpected_cause) is RuntimeError
    assert str(unexpected_cause) == "boom"
    assert calls == [(REPO, STATE)]


@pytest.mark.parametrize("malformed", ((), ({}, [], {}), ({}, (), {})))
def test_builder_rejects_malformed_authority_shape(
    monkeypatch: pytest.MonkeyPatch, malformed: object
) -> None:
    monkeypatch.setattr(compiler, "_authority", lambda _repo, _state: malformed)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        product.build_covapie_current11_task2_batch_descriptor_compiler_context_v1(
            repo_root=REPO, state_root=STATE
        )


def test_builder_rejects_authority_digest_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    authority: tuple[dict[str, object], list[dict[str, object]], dict[str, bool]],
) -> None:
    monkeypatch.setattr(compiler, "_authority", lambda _repo, _state: authority)
    assert product._authority_snapshot_digest_v1(*authority) != KNOWN_AUTHORITY_DIGEST
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        product.build_covapie_current11_task2_batch_descriptor_compiler_context_v1(
            repo_root=REPO, state_root=STATE
        )


@pytest.mark.parametrize(
    ("case_id", "order", "joint"), SUCCESS_SPECS, ids=[row[0] for row in SUCCESS_SPECS]
)
def test_fast_success_exact_public_slow_parity(
    monkeypatch: pytest.MonkeyPatch,
    authority: tuple[dict[str, object], list[dict[str, object]], dict[str, bool]],
    case_id: str,
    order: tuple[int, ...],
    joint: str | None,
) -> None:
    del case_id
    calls = _install_fixture_builder(monkeypatch, authority)
    context = product.build_covapie_current11_task2_batch_descriptor_compiler_context_v1(
        repo_root=REPO, state_root=STATE
    )
    observation = _observation(authority, order, joint)
    slow = compiler.compile_covapie_current11_task2_batch_descriptor_v1(
        repo_root=REPO, state_root=STATE, observation=copy.deepcopy(observation)
    )
    fast = product.compile_covapie_current11_task2_batch_descriptor_with_context_v1(
        context=context, observation=copy.deepcopy(observation)
    )
    assert calls == [(REPO, STATE), (REPO, STATE)]
    assert fast == slow
    assert fast["compiler_status"] == "COMPILED_EXACT"
    assert tuple(fast) == compiler._OUTPUT_FIELDS
    assert tuple(fast["adapter_input_exact18"]) == compiler._EXACT18_FIELDS


@pytest.mark.parametrize("case_id", tuple(FAILURE_STATUSES))
def test_fast_hard_failure_exact_public_slow_parity(
    monkeypatch: pytest.MonkeyPatch,
    authority: tuple[dict[str, object], list[dict[str, object]], dict[str, bool]],
    case_id: str,
) -> None:
    _install_fixture_builder(monkeypatch, authority)
    context = product.build_covapie_current11_task2_batch_descriptor_compiler_context_v1(
        repo_root=REPO, state_root=STATE
    )
    observation = _failure_cases(authority)[case_id]
    slow = compiler.compile_covapie_current11_task2_batch_descriptor_v1(
        repo_root=REPO, state_root=STATE, observation=copy.deepcopy(observation)
    )
    fast = product.compile_covapie_current11_task2_batch_descriptor_with_context_v1(
        context=context, observation=copy.deepcopy(observation)
    )
    assert fast == slow
    assert fast["compiler_status"] == FAILURE_STATUSES[case_id]
    assert fast["failure_reason"] == FAILURE_STATUSES[case_id]
    assert fast["adapter_input_exact18"] is None


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("context_schema_version", "wrong"),
        ("authority_snapshot_digest", "wrong"),
        ("provider_digest", "wrong"),
        ("construction_seal", object()),
    ),
)
def test_invalid_and_forged_context_fail_before_observation_kernel(
    monkeypatch: pytest.MonkeyPatch,
    built: tuple[object, list[tuple[Path, Path]]],
    field: str,
    value: object,
) -> None:
    calls: list[int] = []

    def forbidden(**_kwargs: object):
        calls.append(1)
        raise AssertionError("observation evaluated")

    monkeypatch.setattr(compiler, "_compile_with_verified_authority_v1", forbidden)
    forged = _forged_context(built[0], field, value)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        product.compile_covapie_current11_task2_batch_descriptor_with_context_v1(
            context=forged, observation={}
        )
    assert calls == []


def test_wrong_context_type_fails_before_observation_kernel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[int] = []
    monkeypatch.setattr(
        compiler,
        "_compile_with_verified_authority_v1",
        lambda **_kwargs: calls.append(1),
    )
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        product.compile_covapie_current11_task2_batch_descriptor_with_context_v1(
            context=object(), observation={}
        )
    assert calls == []


def test_valid_context_malformed_observation_returns_compiler_hard_failure(
    built: tuple[object, list[tuple[Path, Path]]]
) -> None:
    output = product.compile_covapie_current11_task2_batch_descriptor_with_context_v1(
        context=built[0], observation={}
    )
    assert tuple(output) == compiler._OUTPUT_FIELDS
    assert output["compiler_status"] == "BATCH_OBSERVATION_SCHEMA_MISMATCH"
    assert output["adapter_input_exact18"] is None


def test_unexpected_shared_kernel_error_maps_context_token_and_preserves_cause(
    monkeypatch: pytest.MonkeyPatch,
    built: tuple[object, list[tuple[Path, Path]]],
) -> None:
    monkeypatch.setattr(
        compiler,
        "_compile_with_verified_authority_v1",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("unexpected")),
    )
    with pytest.raises(ValueError, match=f"^{ERROR}$") as captured:
        product.compile_covapie_current11_task2_batch_descriptor_with_context_v1(
            context=built[0], observation={}
        )
    assert type(captured.value.__cause__) is RuntimeError


def test_fast_validation_source_is_o1_fixed_fields_only() -> None:
    source = inspect.getsource(product._validate_context_v1)
    assert all(name in source for name in (
        "context_schema_version",
        "compiler_product_commit",
        "compiler_contract_commit",
        "compiler_contract_digest",
        "provider_digest",
        "formal_carrier_aggregate",
        "formal_npz_sha256",
        "source_contract_digest",
        "authority_snapshot_digest",
        "construction_seal",
    ))
    assert all(name not in source for name in (
        "_authority",
        "_require_root",
        "_authority_snapshot_digest_v1",
        "_freeze_value_v1",
        "_thaw_value_v1",
        "read_bytes",
        "read_text",
    ))


def test_fast_thaw_is_fresh_and_output_mutation_does_not_change_context(
    built: tuple[object, list[tuple[Path, Path]]],
    authority: tuple[dict[str, object], list[dict[str, object]], dict[str, bool]],
) -> None:
    context = built[0]
    source_first = product._thaw_value_v1(context.source_exact10)
    source_second = product._thaw_value_v1(context.source_exact10)
    provider_first = product._thaw_value_v1(context.identity_provider_exact11)
    provider_second = product._thaw_value_v1(context.identity_provider_exact11)
    readiness_first = product._thaw_value_v1(context.readiness_template)
    readiness_second = product._thaw_value_v1(context.readiness_template)
    assert source_first == source_second == authority[0]
    assert provider_first == provider_second == authority[1]
    assert readiness_first == readiness_second == authority[2]
    assert _container_ids(source_first).isdisjoint(_container_ids(source_second))
    assert _container_ids(provider_first).isdisjoint(_container_ids(provider_second))
    assert _container_ids(readiness_first).isdisjoint(_container_ids(readiness_second))
    output = product.compile_covapie_current11_task2_batch_descriptor_with_context_v1(
        context=context, observation=_observation(authority, (10,), None)
    )
    output["readiness"]["ready_for_training"] = True
    output["adapter_input_exact18"]["source_pair_values_int64"][0][0] += 1
    assert product._thaw_value_v1(context.readiness_template) == authority[2]
    assert product._thaw_value_v1(context.source_exact10) == authority[0]


def test_fast_does_not_mutate_observation_or_context_and_is_deterministic(
    built: tuple[object, list[tuple[Path, Path]]],
    authority: tuple[dict[str, object], list[dict[str, object]], dict[str, bool]],
) -> None:
    context = built[0]
    observation = _observation(authority, (10, 4, 0), None)
    before_observation = copy.deepcopy(observation)
    before_context = tuple(getattr(context, field.name) for field in fields(context))
    first = product.compile_covapie_current11_task2_batch_descriptor_with_context_v1(
        context=context, observation=observation
    )
    second = product.compile_covapie_current11_task2_batch_descriptor_with_context_v1(
        context=context, observation=copy.deepcopy(observation)
    )
    assert observation == before_observation
    assert tuple(getattr(context, field.name) for field in fields(context)) == before_context
    assert first == second
    assert first is not second
    assert first["adapter_input_exact18"] is not second["adapter_input_exact18"]
    encoded = json.dumps(first, sort_keys=True)
    assert "context_schema_version" not in first
    assert "authority_snapshot_digest" not in encoded
    assert "construction_seal" not in encoded


def test_fast_dynamic_zero_authority_root_gate_filesystem_and_adapter(
    monkeypatch: pytest.MonkeyPatch,
    built: tuple[object, list[tuple[Path, Path]]],
    authority: tuple[dict[str, object], list[dict[str, object]], dict[str, bool]],
) -> None:
    counts = {
        "authority": 0,
        "root": 0,
        "compiler_gate": 0,
        "context_gate": 0,
        "fs": 0,
        "adapter": 0,
    }

    def forbidden(kind: str):
        def raising(*_args: object, **_kwargs: object):
            counts[kind] += 1
            raise AssertionError(f"{kind} called")

        return raising

    with monkeypatch.context() as guarded:
        guarded.setattr(compiler, "_authority", forbidden("authority"))
        guarded.setattr(compiler, "_require_root", forbidden("root"))
        guarded.setattr(
            compiler_gate,
            "build_covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1",
            forbidden("compiler_gate"),
        )
        guarded.setattr(
            context_gate,
            "build_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1",
            forbidden("context_gate"),
        )
        guarded.setattr(
            adapter,
            "build_covapie_current11_task2_batch_index_remap_adapter_v1",
            forbidden("adapter"),
        )
        guarded.setattr(builtins, "open", forbidden("fs"))
        for name in ("open", "read_bytes", "read_text", "stat", "lstat", "resolve"):
            guarded.setattr(Path, name, forbidden("fs"))
        output = product.compile_covapie_current11_task2_batch_descriptor_with_context_v1(
            context=built[0], observation=_observation(authority, (10,), None)
        )
    assert output["compiler_status"] == "COMPILED_EXACT"
    assert counts == {
        "authority": 0,
        "root": 0,
        "compiler_gate": 0,
        "context_gate": 0,
        "fs": 0,
        "adapter": 0,
    }


def test_checker_live_function_has_one_context_build_and_one_public_adapter_call() -> None:
    checker = _load_checker()
    source = inspect.getsource(checker._live_integration)
    tree = ast.parse(textwrap.dedent(source))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]
    assert sum(
        node.func.attr
        == "build_covapie_current11_task2_batch_descriptor_compiler_context_v1"
        for node in calls
    ) == 1
    assert sum(
        node.func.attr == "build_covapie_current11_task2_batch_index_remap_adapter_v1"
        for node in calls
    ) == 1
    assert "compile_covapie_current11_task2_batch_descriptor_v1" not in source


@pytest.mark.parametrize("lifecycle", ("precommit-untracked", "clean-tracked-successor"))
def test_checker_lifecycle_accepts_precommit_and_clean_successor(
    monkeypatch: pytest.MonkeyPatch, lifecycle: str
) -> None:
    checker = _load_checker()
    blob = "a" * 40

    def run_git(_repo: Path, arguments: Sequence[str]) -> str:
        call = tuple(arguments)
        if call == ("status", "--porcelain=v1", "--untracked-files=all"):
            if lifecycle == "precommit-untracked":
                return "\n".join(f"?? {path}" for path in EXACT4) + "\n"
            return ""
        if call == ("ls-files", "--stage", "--", *EXACT4):
            if lifecycle == "precommit-untracked":
                return ""
            return "\n".join(f"100644 {blob} 0\t{path}" for path in EXACT4) + "\n"
        if call[:2] == ("hash-object", "--no-filters") or call[0] == "rev-parse":
            return blob + "\n"
        pytest.fail(f"unexpected git call: {call!r}")

    monkeypatch.setattr(checker, "_run_git", run_git)
    assert checker._repository_lifecycle(REPO) == lifecycle


def test_checker_lifecycle_rejects_fifth_untracked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker()

    def run_git(_repo: Path, arguments: Sequence[str]) -> str:
        if tuple(arguments) == ("status", "--porcelain=v1", "--untracked-files=all"):
            return "\n".join(
                [*(f"?? {path}" for path in EXACT4), "?? fifth.txt"]
            )
        return ""

    monkeypatch.setattr(checker, "_run_git", run_git)
    with pytest.raises(ValueError, match=f"^{checker._ERROR}$"):
        checker._repository_lifecycle(REPO)


def test_checker_lineage_is_base_ancestry_only_and_does_not_use_origin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker()
    calls: list[tuple[str, ...]] = []

    def run_git(_repo: Path, arguments: Sequence[str]) -> str:
        call = tuple(arguments)
        calls.append(call)
        if call == ("branch", "--show-current"):
            return "main\n"
        if call == ("cat-file", "-e", f"{BASE_COMMIT}^{{commit}}"):
            return ""
        if call == ("merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"):
            return ""
        pytest.fail(f"unexpected git call: {call!r}")

    monkeypatch.setattr(checker, "_run_git", run_git)
    checker._validate_repository_lineage(REPO)
    assert len(calls) == 3
    assert all("origin" not in part for call in calls for part in call)


@pytest.mark.parametrize(
    "arguments",
    (
        (),
        ("--help",),
        ("--repo-root", str(REPO)),
        ("--state-root", str(STATE)),
        ("--repo-root", str(REPO), "--state-root", str(STATE), "--train"),
    ),
)
def test_checker_cli_rejects_missing_help_and_expanded_scope(
    arguments: tuple[str, ...]
) -> None:
    checker = _load_checker()
    with pytest.raises(ValueError, match=f"^{checker._ERROR}$"):
        checker._main(arguments)


def test_checker_main_uses_dynamic_lifecycle_and_emits_compact_pass_without_live(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    checker = _load_checker()
    expected_lifecycle = checker._repository_lifecycle(REPO)
    assert expected_lifecycle in ("precommit-untracked", "clean-tracked-successor")
    monkeypatch.setattr(checker, "_validate_repository_lineage", lambda _repo: None)
    monkeypatch.setattr(checker, "_safe_exact4", lambda _repo: None)
    monkeypatch.setattr(
        checker,
        "_fixture_fast_checks",
        lambda _repo, _state: {
            "success_parity": {"checked": 4, "passed": 4},
            "hard_failure_parity": {"checked": 5, "passed": 5},
        },
    )
    monkeypatch.setattr(
        checker,
        "_live_integration",
        lambda _repo, _state: {
            "live_authority_call_count": 1,
            "actual_fast_compiler_status": "COMPILED_EXACT",
            "actual_public_adapter_status": "REMAPPED_EXACT",
            "repository_unchanged": True,
            "formal_carrier_and_routing_unchanged": True,
        },
    )
    assert checker._main(
        ("--repo-root", str(REPO), "--state-root", str(STATE))
    ) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out.count("\n") == 1
    summary = json.loads(captured.out)
    assert summary["status"] == "PASS_COMPILER_CONTEXT_V1"
    assert summary["repository_lifecycle"] == expected_lifecycle
    assert summary["live_authority_call_count"] == 1


def test_repository_exact4_are_safe_precommit_or_clean_tracked_successor() -> None:
    status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    ).stdout.splitlines()
    index = subprocess.run(
        ["git", "ls-files", "--stage", "--", *EXACT4],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    ).stdout.splitlines()
    if status:
        assert set(status) == {f"?? {path}" for path in EXACT4}
        assert len(status) == 4 and index == []
    else:
        assert len(index) == 4
        for row in index:
            metadata, relative = row.split("\t", 1)
            mode, blob, stage = metadata.split()
            assert mode == "100644" and stage == "0" and relative in EXACT4
            worktree = subprocess.run(
                ["git", "hash-object", "--no-filters", relative],
                cwd=REPO,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            ).stdout.strip()
            head = subprocess.run(
                ["git", "rev-parse", f"HEAD:{relative}"],
                cwd=REPO,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            ).stdout.strip()
            assert blob == worktree == head
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
        text = payload.decode("utf-8", errors="strict")
        assert all(not line.endswith((" ", "\t")) for line in text.splitlines())


def test_checker_imports_published_extractor_but_product_does_not() -> None:
    checker = _load_checker()
    assert checker.extractor is extractor
    assert not hasattr(product, "extractor")
