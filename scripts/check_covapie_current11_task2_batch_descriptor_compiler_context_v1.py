#!/usr/bin/env python3
"""Check the Current11 Task 2 batch descriptor compiler context V1."""

from __future__ import annotations

import argparse
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
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, NoReturn, Sequence


sys.dont_write_bytecode = True

from covalent_ext import covapie_current11_runtime_batch_observation_extractor_v1 as extractor  # noqa: E402
from covalent_ext import covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1 as context_gate  # noqa: E402
from covalent_ext import covapie_current11_task2_batch_descriptor_compiler_context_v1 as product  # noqa: E402
from covalent_ext import covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1 as compiler_contract_gate  # noqa: E402
from covalent_ext import covapie_current11_task2_batch_descriptor_compiler_v1 as compiler  # noqa: E402
from covalent_ext import covapie_current11_task2_batch_index_remap_adapter_v1 as adapter  # noqa: E402


_ERROR = "COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_V1_CHECK_ERROR"
_STATUS = "PASS_COMPILER_CONTEXT_V1"
_BASE_COMMIT = "ac22f9cdb8438cf97e3da6e4668e9b124d484f95"
_CONTEXT_CONTRACT_COMMIT = "df3f570d8ec98440856bdfa311387443b24ca1fa"
_CONTEXT_CONTRACT_DIGEST = (
    "6de2401bbbd8ad60a295405cd70af948edff8a985521be5f3dc47e409fbb8c4f"
)
_AUTHORITY_SNAPSHOT_DIGEST = (
    "e3c7c14e5a94db2bf59b5195ae6902d7fd7269e58a8690589962548860348d44"
)
_CARRIER_AGGREGATE = (
    "ef426a6d8dee9678ac15dd62b191e9ef9cfb436a01660bd941bd24392dfa9a18"
)
_CARRIER_NPZ_SHA256 = (
    "ea3aa7c94b7c88993493662ad6ba7fd95e547ec62612a072f8248a515657e910"
)
_ROUTING_SNAPSHOT = (
    "768fbd980efbcedcaa2ef971a7d77791879111d1fceeb1f03cb1eb8bfff24034"
)
_ROUTING_AGGREGATE = (
    "24f95099ba1ba0b81724535cb17c5d4d32c360f71c87422571210a2178ddb49c"
)
_DATASET_BLOB = "5cd1531e9beeca2f53c17b705949676bf457a967"
_CARRIER_RELATIVE = Path(
    "formal-sidecars/current11-runtime-sample-and-role-order-carrier-v1"
)
_ROUTING_RELATIVE = Path(
    "formal-sidecars/current11-dataset-partial-supervision-routing-sidecar-v1"
)
_NPZ = "current11_runtime_sample_and_role_order_carrier.npz"
_BINDING = "current11_runtime_sample_and_role_order_carrier_binding_report.json"
_EXACT4 = (
    "src/covalent_ext/"
    "covapie_current11_task2_batch_descriptor_compiler_context_v1.py",
    "scripts/"
    "check_covapie_current11_task2_batch_descriptor_compiler_context_v1.py",
    "tests/"
    "test_covapie_current11_task2_batch_descriptor_compiler_context_v1.py",
    "docs/"
    "covapie_current11_task2_batch_descriptor_compiler_context_v1_guide.md",
)
_SUCCESS_SPECS = (
    ("canonical", tuple(range(11)), compiler._JOINT_LAYOUT),
    ("reversed", tuple(reversed(range(11))), compiler._JOINT_LAYOUT),
    ("subset_10_4_0", (10, 4, 0), None),
    ("singleton_10", (10,), None),
)
_FAILURE_IDS = (
    "source_contract_override",
    "duplicate_runtime_key",
    "wrong_ligand_length",
    "wrong_ligand_membership",
    "unknown_joint_descriptor",
)


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        del message
        raise ValueError(_ERROR)


def _fail() -> NoReturn:
    raise ValueError(_ERROR)


def _root(path: Path) -> Path:
    if type(path) is not type(Path()) or not path.is_absolute():
        _fail()
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ValueError(_ERROR) from error
    if resolved != path or stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        _fail()
    return path


def _run_git(repo: Path, arguments: Sequence[str]) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repo,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
    )
    if completed.returncode != 0 or completed.stderr:
        _fail()
    return completed.stdout


def _validate_repository_lineage(repo: Path) -> None:
    if _run_git(repo, ("branch", "--show-current")).strip() != "main":
        _fail()
    _run_git(repo, ("cat-file", "-e", f"{_BASE_COMMIT}^{{commit}}"))
    _run_git(repo, ("merge-base", "--is-ancestor", _BASE_COMMIT, "HEAD"))


def _stage_rows(repo: Path) -> dict[str, tuple[str, str, str]]:
    rows: dict[str, tuple[str, str, str]] = {}
    for row in _run_git(repo, ("ls-files", "--stage", "--", *_EXACT4)).splitlines():
        try:
            metadata, relative = row.split("\t", 1)
            mode, blob, stage = metadata.split()
        except ValueError as error:
            raise ValueError(_ERROR) from error
        if relative not in _EXACT4 or relative in rows:
            _fail()
        rows[relative] = (mode, blob, stage)
    return rows


def _repository_lifecycle(repo: Path) -> str:
    status = _run_git(
        repo, ("status", "--porcelain=v1", "--untracked-files=all")
    ).splitlines()
    rows = _stage_rows(repo)
    if set(status) == {f"?? {relative}" for relative in _EXACT4} and len(status) == 4:
        if rows:
            _fail()
        return "precommit-untracked"
    if status or set(rows) != set(_EXACT4):
        _fail()
    for relative, (mode, blob, stage) in rows.items():
        if (
            mode != "100644"
            or stage != "0"
            or _run_git(repo, ("hash-object", "--no-filters", relative)).strip()
            != blob
            or _run_git(repo, ("rev-parse", f"HEAD:{relative}")).strip() != blob
        ):
            _fail()
    return "clean-tracked-successor"


def _repository_snapshot(repo: Path) -> tuple[str, ...]:
    return (
        _run_git(repo, ("status", "--porcelain=v1", "--untracked-files=all")),
        _run_git(repo, ("diff", "--name-status")),
        _run_git(repo, ("diff", "--cached", "--name-status")),
        _run_git(repo, ("rev-parse", "HEAD")),
    )


def _path_identity(path: Path) -> tuple[object, ...]:
    metadata = path.lstat()
    payload_digest = (
        hashlib.sha256(path.read_bytes()).hexdigest()
        if stat.S_ISREG(metadata.st_mode)
        else None
    )
    return (
        int(metadata.st_dev),
        int(metadata.st_ino),
        stat.S_IFMT(metadata.st_mode),
        stat.S_IMODE(metadata.st_mode),
        int(metadata.st_size),
        int(metadata.st_mtime_ns),
        payload_digest,
    )


def _alias_snapshot(canonical: Path) -> tuple[object, ...]:
    try:
        target_name = os.readlink(canonical)
        target = canonical.parent / target_name
        inventory = tuple(sorted(os.listdir(target)))
    except OSError as error:
        raise ValueError(_ERROR) from error
    return (
        _path_identity(canonical),
        target_name,
        _path_identity(target),
        inventory,
        tuple((name, _path_identity(target / name)) for name in inventory),
    )


def _formal_snapshot(state: Path) -> tuple[object, ...]:
    carrier = state / _CARRIER_RELATIVE
    routing = state / _ROUTING_RELATIVE
    carrier_snapshot = _alias_snapshot(carrier)
    routing_snapshot = _alias_snapshot(routing)
    try:
        binding = json.loads((carrier / _BINDING).read_text(encoding="utf-8"))
        npz_digest = hashlib.sha256((carrier / _NPZ).read_bytes()).hexdigest()
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(_ERROR) from error
    if (
        _CARRIER_AGGREGATE not in str(carrier_snapshot[1])
        or _ROUTING_AGGREGATE not in str(routing_snapshot[1])
        or npz_digest != _CARRIER_NPZ_SHA256
        or binding.get("runtime_npz_sha256") != _CARRIER_NPZ_SHA256
        or binding.get("formal_routing_sidecar_snapshot_sha256")
        != _ROUTING_SNAPSHOT
        or binding.get("formal_routing_sidecar_aggregate_sha256")
        != _ROUTING_AGGREGATE
    ):
        _fail()
    return carrier_snapshot, routing_snapshot


def _safe_exact4(repo: Path) -> None:
    for relative in _EXACT4:
        path = repo / relative
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
        except OSError as error:
            raise ValueError(_ERROR) from error
        if (
            not stat.S_ISREG(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o644
            or not payload
            or len(payload) >= 1024 * 1024
            or payload.startswith(b"\xef\xbb\xbf")
            or b"\0" in payload
            or b"\r" in payload
            or not payload.endswith(b"\n")
            or payload.endswith(b"\n\n")
        ):
            _fail()
        try:
            text = payload.decode("utf-8", errors="strict")
        except UnicodeError as error:
            raise ValueError(_ERROR) from error
        if any(line.endswith((" ", "\t")) for line in text.splitlines()):
            _fail()


@contextmanager
def _hide_exact4_from_historical_git(owner: object) -> Iterator[None]:
    original = getattr(owner, "_run_git", None)
    if not callable(original):
        _fail()

    def compatible(root: Path, arguments: Sequence[str]) -> str:
        output = original(root, arguments)
        if tuple(arguments) in {
            ("status", "--porcelain=v1", "--untracked-files=all"),
            ("status", "--short"),
        }:
            allowed = {f"?? {relative}" for relative in _EXACT4}
            lines = output.splitlines()
            if any(
                len(line) >= 4
                and line[3:] in _EXACT4
                and line not in allowed
                for line in lines
            ):
                _fail()
            output = "\n".join(line for line in lines if line not in allowed)
        return output

    try:
        setattr(owner, "_run_git", compatible)
        yield
    finally:
        setattr(owner, "_run_git", original)


def _compiler_git_owner() -> object:
    return compiler._contract_gate._remap_gate._instance_builder._payload_builder._contract_gate


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
    if type(samples) is not list:
        _fail()
    provider: list[dict[str, object]] = []
    for index, sample in enumerate(samples):
        if type(sample) is not dict:
            _fail()
        roles: dict[str, object] = {}
        for role_index, role_name in enumerate(("pocket", "ligand")):
            selected_source = compiler._SOURCE_PAIRS[index][role_index]
            digest = hashlib.sha256(
                f"context-checker:{index}:{role_name}".encode("utf-8")
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
    if type(samples) is not list:
        _fail()
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


def _failure_observations(
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


def _assert_no_reachable_dict_or_list(context: object) -> None:
    pending = [context]
    seen: set[int] = set()
    while pending:
        value = pending.pop()
        if id(value) in seen:
            continue
        seen.add(id(value))
        if type(value) in (dict, list):
            _fail()
        if type(value) is tuple:
            pending.extend(value)
        elif type(value) is product._CompilerContextV1:
            pending.extend(
                getattr(value, field)
                for field in (*product._CONTEXT_SEMANTIC_FIELDS, "construction_seal")
            )
        elif type(value) is product._FrozenMapV1:
            pending.append(value.items)
        elif type(value) is product._FrozenMapEntryV1:
            pending.extend((value.key, value.value))
        elif type(value) is product._FrozenListV1:
            pending.append(value.items)


def _forged_context(context: object, field: str, value: object) -> object:
    forged = object.__new__(product._CompilerContextV1)
    for name in (*product._CONTEXT_SEMANTIC_FIELDS, "construction_seal"):
        object.__setattr__(forged, name, getattr(context, name))
    object.__setattr__(forged, field, value)
    return forged


def _guarded_fast_compile(
    context: object, observation: dict[str, object]
) -> tuple[dict[str, object], dict[str, int]]:
    counts = {
        "authority": 0,
        "root": 0,
        "compiler_gate": 0,
        "context_gate": 0,
        "filesystem": 0,
        "adapter": 0,
    }

    def forbidden(kind: str):
        def raising(*_args: object, **_kwargs: object) -> NoReturn:
            counts[kind] += 1
            raise AssertionError(f"{kind} called")

        return raising

    originals = {
        "authority": compiler._authority,
        "root": compiler._require_root,
        "compiler_gate": compiler_contract_gate.build_covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1,
        "context_gate": context_gate.build_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1,
        "adapter": adapter.build_covapie_current11_task2_batch_index_remap_adapter_v1,
        "open": builtins.open,
        **{f"Path.{name}": getattr(Path, name) for name in (
            "open", "read_bytes", "read_text", "stat", "lstat", "resolve"
        )},
    }
    try:
        compiler._authority = forbidden("authority")
        compiler._require_root = forbidden("root")
        compiler_contract_gate.build_covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1 = forbidden("compiler_gate")
        context_gate.build_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1 = forbidden("context_gate")
        adapter.build_covapie_current11_task2_batch_index_remap_adapter_v1 = forbidden("adapter")
        builtins.open = forbidden("filesystem")
        for name in ("open", "read_bytes", "read_text", "stat", "lstat", "resolve"):
            setattr(Path, name, forbidden("filesystem"))
        output = product.compile_covapie_current11_task2_batch_descriptor_with_context_v1(
            context=context,
            observation=observation,
        )
    finally:
        compiler._authority = originals["authority"]
        compiler._require_root = originals["root"]
        compiler_contract_gate.build_covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1 = originals["compiler_gate"]
        context_gate.build_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1 = originals["context_gate"]
        adapter.build_covapie_current11_task2_batch_index_remap_adapter_v1 = originals["adapter"]
        builtins.open = originals["open"]
        for name in ("open", "read_bytes", "read_text", "stat", "lstat", "resolve"):
            setattr(Path, name, originals[f"Path.{name}"])
    if any(counts.values()):
        _fail()
    return output, counts


def _fixture_fast_checks(repo: Path, state: Path) -> dict[str, object]:
    authority = _authority_fixture()
    fixture_digest = product._authority_snapshot_digest_v1(*authority)
    original_expected = product._EXPECTED_AUTHORITY_SNAPSHOT_DIGEST
    original_authority = compiler._authority
    original_slow = compiler.compile_covapie_current11_task2_batch_descriptor_v1
    authority_calls = 0
    slow_public_calls = 0

    def fixture_authority(actual_repo: Path, actual_state: Path):
        nonlocal authority_calls
        if actual_repo != repo or actual_state != state:
            _fail()
        authority_calls += 1
        return copy.deepcopy(authority)

    def forbidden_slow(**_kwargs: object) -> NoReturn:
        nonlocal slow_public_calls
        slow_public_calls += 1
        raise AssertionError("slow public compiler called")

    try:
        product._EXPECTED_AUTHORITY_SNAPSHOT_DIGEST = fixture_digest
        compiler._authority = fixture_authority
        compiler.compile_covapie_current11_task2_batch_descriptor_v1 = forbidden_slow
        context = product.build_covapie_current11_task2_batch_descriptor_compiler_context_v1(
            repo_root=repo, state_root=state
        )
        if authority_calls != 1 or slow_public_calls != 0:
            _fail()
        _assert_no_reachable_dict_or_list(context)
        if type(context) is not product._CompilerContextV1:
            _fail()
        try:
            pickle.dumps(context)
        except TypeError as error:
            if str(error) != product._ERROR:
                _fail()
        else:
            _fail()

        successes = {
            case_id: _observation(authority, order, joint)
            for case_id, order, joint in _SUCCESS_SPECS
        }
        failures = _failure_observations(authority)
        if tuple(failures) != _FAILURE_IDS:
            _fail()
        for observation in (*successes.values(), *failures.values()):
            expected = compiler._compile_with_verified_authority_v1(
                authority=copy.deepcopy(authority), observation=copy.deepcopy(observation)
            )
            actual = product.compile_covapie_current11_task2_batch_descriptor_with_context_v1(
                context=context, observation=copy.deepcopy(observation)
            )
            if actual != expected:
                _fail()
        if any(
            product.compile_covapie_current11_task2_batch_descriptor_with_context_v1(
                context=context, observation=copy.deepcopy(observation)
            ).get("compiler_status")
            != "COMPILED_EXACT"
            for observation in successes.values()
        ):
            _fail()

        invalid_contexts = (
            object(),
            _forged_context(context, "context_schema_version", "wrong"),
            _forged_context(context, "authority_snapshot_digest", "wrong"),
            _forged_context(context, "provider_digest", "wrong"),
            _forged_context(context, "construction_seal", object()),
        )
        original_kernel = compiler._compile_with_verified_authority_v1
        kernel_calls = 0

        def forbidden_kernel(**_kwargs: object) -> NoReturn:
            nonlocal kernel_calls
            kernel_calls += 1
            raise AssertionError("kernel called for invalid context")

        compiler._compile_with_verified_authority_v1 = forbidden_kernel
        try:
            for invalid in invalid_contexts:
                try:
                    product.compile_covapie_current11_task2_batch_descriptor_with_context_v1(
                        context=invalid, observation={}
                    )
                except ValueError as error:
                    if str(error) != product._ERROR:
                        _fail()
                else:
                    _fail()
        finally:
            compiler._compile_with_verified_authority_v1 = original_kernel
        if kernel_calls != 0:
            _fail()

        guarded, counts = _guarded_fast_compile(
            context, copy.deepcopy(successes["singleton_10"])
        )
        if guarded.get("compiler_status") != "COMPILED_EXACT":
            _fail()
        canonical = product.compile_covapie_current11_task2_batch_descriptor_with_context_v1(
            context=context, observation=copy.deepcopy(successes["canonical"])
        )
        if (
            tuple(canonical) != compiler._OUTPUT_FIELDS
            or tuple(canonical["adapter_input_exact18"]) != compiler._EXACT18_FIELDS
        ):
            _fail()
        return {
            "fixture_authority_build_count": authority_calls,
            "builder_slow_public_compiler_call_count": slow_public_calls,
            "fixture_authority_snapshot_digest": fixture_digest,
            "success_parity": {"checked": 4, "passed": 4},
            "hard_failure_parity": {"checked": 5, "passed": 5},
            "invalid_context": {"checked": 5, "passed": 5},
            "output_exact10_field_order_preserved": True,
            "adapter_exact18_field_order_preserved": True,
            "context_reachable_dict_or_list": False,
            "context_pickleable": False,
            "fast_guard_counts": counts,
        }
    finally:
        product._EXPECTED_AUTHORITY_SNAPSHOT_DIGEST = original_expected
        compiler._authority = original_authority
        compiler.compile_covapie_current11_task2_batch_descriptor_v1 = original_slow


def _validate_and_load_dataset(repo: Path):
    path = repo / "dataset.py"
    try:
        metadata = path.lstat()
    except OSError as error:
        raise ValueError(_ERROR) from error
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != 0o644
        or _run_git(repo, ("rev-parse", "HEAD:dataset.py")).strip() != _DATASET_BLOB
        or _run_git(repo, ("hash-object", "--no-filters", "dataset.py")).strip()
        != _DATASET_BLOB
    ):
        _fail()
    specification = importlib.util.spec_from_file_location(
        "covapie_compiler_context_checker_dataset", path
    )
    if specification is None or specification.loader is None:
        _fail()
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    dataset_type = getattr(module, "ProcessedLigandPocketDataset", None)
    if not isinstance(dataset_type, type):
        _fail()
    return dataset_type


def _live_integration(repo: Path, state: Path) -> dict[str, object]:
    repository_before = _repository_snapshot(repo)
    formal_before = _formal_snapshot(state)
    original_authority = compiler._authority
    authority_calls = 0

    def counted_authority(actual_repo: Path, actual_state: Path):
        nonlocal authority_calls
        authority_calls += 1
        return original_authority(actual_repo, actual_state)

    compiler._authority = counted_authority
    started = time.perf_counter()
    try:
        with _hide_exact4_from_historical_git(_compiler_git_owner()):
            context = product.build_covapie_current11_task2_batch_descriptor_compiler_context_v1(
                repo_root=repo, state_root=state
            )
    finally:
        compiler._authority = original_authority
    build_elapsed = time.perf_counter() - started
    if authority_calls != 1:
        _fail()

    dataset_type = _validate_and_load_dataset(repo)
    npz = state / _CARRIER_RELATIVE / _NPZ
    dataset = dataset_type(npz, center=False)
    batch = dataset_type.collate_fn([dataset[index] for index in (10, 4, 0)])
    observation = extractor.extract_covapie_current11_runtime_batch_observation_v1(
        batch=batch
    )
    if (
        type(observation) is not dict
        or len(observation) != 14
        or observation.get("joint_layout_descriptor") is not None
    ):
        _fail()
    compiled, fast_counts = _guarded_fast_compile(context, observation)
    exact18 = compiled.get("adapter_input_exact18")
    if (
        compiled.get("compiler_status") != "COMPILED_EXACT"
        or type(exact18) is not dict
        or tuple(exact18) != compiler._EXACT18_FIELDS
    ):
        _fail()

    original_adapter = adapter.build_covapie_current11_task2_batch_index_remap_adapter_v1
    adapter_calls = 0

    def counted_adapter(**kwargs: object):
        nonlocal adapter_calls
        adapter_calls += 1
        return original_adapter(**kwargs)

    adapter.build_covapie_current11_task2_batch_index_remap_adapter_v1 = counted_adapter
    try:
        with _hide_exact4_from_historical_git(adapter._projection_contract_gate):
            artifacts = adapter.build_covapie_current11_task2_batch_index_remap_adapter_v1(
                repo_root=repo,
                state_root=state,
                adapter_input=exact18,
            )
    finally:
        adapter.build_covapie_current11_task2_batch_index_remap_adapter_v1 = original_adapter
    if adapter_calls != 1 or type(artifacts) is not dict:
        _fail()
    try:
        remapped = json.loads(
            artifacts["current11_task2_batch_index_remap_output.json"].decode("utf-8")
        )
    except (KeyError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(_ERROR) from error
    if (
        remapped.get("remap_status") != "REMAPPED_EXACT"
        or remapped.get("pair_values_joint_global_indices") is not None
    ):
        _fail()

    repository_unchanged = _repository_snapshot(repo) == repository_before
    formal_unchanged = _formal_snapshot(state) == formal_before
    if not repository_unchanged or not formal_unchanged:
        _fail()
    return {
        "live_authority_call_count": authority_calls,
        "live_context_build_elapsed_seconds": build_elapsed,
        "actual_subset_order": [10, 4, 0],
        "actual_extractor_field_count": 14,
        "actual_fast_compiler_status": compiled["compiler_status"],
        "actual_public_adapter_call_count": adapter_calls,
        "actual_public_adapter_status": remapped["remap_status"],
        "pair_values_joint_global_indices_is_none": True,
        "live_fast_guard_counts": fast_counts,
        "repository_unchanged": repository_unchanged,
        "formal_carrier_and_routing_unchanged": formal_unchanged,
    }


def _main(arguments: Sequence[str]) -> int:
    parser = _Parser(add_help=False, allow_abbrev=False)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--state-root", required=True, type=Path)
    namespace = parser.parse_args(arguments)
    repo = _root(namespace.repo_root)
    state = _root(namespace.state_root)
    _validate_repository_lineage(repo)
    lifecycle_before = _repository_lifecycle(repo)
    _safe_exact4(repo)
    fixture = _fixture_fast_checks(repo, state)
    live = _live_integration(repo, state)
    lifecycle_after = _repository_lifecycle(repo)
    if lifecycle_after != lifecycle_before:
        _fail()
    public_signatures = (
        inspect.signature(
            product.build_covapie_current11_task2_batch_descriptor_compiler_context_v1
        ),
        inspect.signature(
            product.compile_covapie_current11_task2_batch_descriptor_with_context_v1
        ),
    )
    if (
        product.__all__
        != (
            "build_covapie_current11_task2_batch_descriptor_compiler_context_v1",
            "compile_covapie_current11_task2_batch_descriptor_with_context_v1",
        )
        or any(
            parameter.kind is not inspect.Parameter.KEYWORD_ONLY
            for signature in public_signatures
            for parameter in signature.parameters.values()
        )
        or product._EXPECTED_AUTHORITY_SNAPSHOT_DIGEST
        != _AUTHORITY_SNAPSHOT_DIGEST
    ):
        _fail()
    readiness = {
        "compiler_hot_loop_authority_context_contract_designed": True,
        "compiler_hot_loop_authority_context_contract_gate_implemented": True,
        "compiler_hot_loop_authority_context_contract_gate_passed": True,
        "compiler_shared_pure_kernel_refactor_implemented": True,
        "compiler_shared_pure_kernel_refactor_passed": True,
        "compiler_hot_loop_authority_context_implemented": True,
        "compiler_hot_loop_authority_context_passed": True,
        "ready_for_compiler_hot_loop_authority_context_module_implementation": False,
        "runtime_batch_observation_extractor_implemented": True,
        "task2_batch_descriptor_compiler_implemented": True,
        "ready_for_public_remap_adapter_hot_loop_audit": True,
        "ready_for_dataloader_integration": False,
        "public_remap_adapter_hot_loop_audit_required_before_dataloader_integration": True,
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
    summary = {
        "status": _STATUS,
        "repository_lifecycle": lifecycle_after,
        "context_contract_commit": _CONTEXT_CONTRACT_COMMIT,
        "context_contract_digest": _CONTEXT_CONTRACT_DIGEST,
        "authority_snapshot_digest": _AUTHORITY_SNAPSHOT_DIGEST,
        "formal_carrier_aggregate": _CARRIER_AGGREGATE,
        "formal_carrier_npz_sha256": _CARRIER_NPZ_SHA256,
        "formal_routing_snapshot": _ROUTING_SNAPSHOT,
        "formal_routing_aggregate": _ROUTING_AGGREGATE,
        "public___all__": list(product.__all__),
        **fixture,
        **live,
        "readiness": readiness,
    }
    sys.stdout.write(
        json.dumps(
            summary,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(_main(sys.argv[1:]))
    except BaseException as error:
        if type(error) is SystemExit and type(error.code) is int and error.code == 0:
            raise
        sys.stderr.write(_ERROR + "\n")
        raise SystemExit(1) from None
