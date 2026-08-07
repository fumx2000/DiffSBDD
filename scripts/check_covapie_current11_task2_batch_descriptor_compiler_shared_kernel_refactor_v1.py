#!/usr/bin/env python3
"""Check the fixture-only Current11 Task 2 compiler shared-kernel refactor V1."""

from __future__ import annotations

import argparse
import ast
import builtins
import copy
import hashlib
import inspect
import json
import os
import stat
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import NoReturn, Sequence


sys.dont_write_bytecode = True

from covalent_ext import covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1 as contract_gate  # noqa: E402
from covalent_ext import covapie_current11_task2_batch_descriptor_compiler_v1 as compiler  # noqa: E402
from covalent_ext import covapie_current11_task2_batch_index_remap_adapter_v1 as adapter  # noqa: E402


_ERROR = (
    "COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_"
    "SHARED_KERNEL_REFACTOR_V1_ERROR"
)
_BASE_COMMIT = "df3f570d8ec98440856bdfa311387443b24ca1fa"
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
_CARRIER_RELATIVE = Path(
    "formal-sidecars/current11-runtime-sample-and-role-order-carrier-v1"
)
_ROUTING_RELATIVE = Path(
    "formal-sidecars/current11-dataset-partial-supervision-routing-sidecar-v1"
)
_NPZ = "current11_runtime_sample_and_role_order_carrier.npz"
_BINDING = "current11_runtime_sample_and_role_order_carrier_binding_report.json"
_EXACT4 = (
    "src/covalent_ext/covapie_current11_task2_batch_descriptor_compiler_v1.py",
    "scripts/check_covapie_current11_task2_batch_descriptor_compiler_shared_kernel_refactor_v1.py",
    "tests/test_covapie_current11_task2_batch_descriptor_compiler_shared_kernel_refactor_v1.py",
    "docs/covapie_current11_task2_batch_descriptor_compiler_shared_kernel_refactor_v1_guide.md",
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
        if relative in rows or relative not in _EXACT4:
            _fail()
        rows[relative] = (mode, blob, stage)
    return rows


def _repository_lifecycle(repo: Path) -> str:
    status = _run_git(
        repo, ("status", "--porcelain=v1", "--untracked-files=all")
    ).splitlines()
    rows = _stage_rows(repo)
    compiler_path, *new_paths = _EXACT4
    precommit_status = {
        f" M {compiler_path}",
        *(f"?? {relative}" for relative in new_paths),
    }
    if set(status) == precommit_status and len(status) == len(_EXACT4):
        if set(rows) != {compiler_path}:
            _fail()
        mode, blob, stage = rows[compiler_path]
        head_blob = _run_git(repo, ("rev-parse", f"HEAD:{compiler_path}")).strip()
        worktree_blob = _run_git(
            repo, ("hash-object", "--no-filters", compiler_path)
        ).strip()
        if (
            mode != "100644"
            or stage != "0"
            or blob != head_blob
            or worktree_blob == blob
        ):
            _fail()
        return "precommit-mixed-candidate"
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
    digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    return (
        int(metadata.st_dev),
        int(metadata.st_ino),
        stat.S_IFMT(metadata.st_mode),
        stat.S_IMODE(metadata.st_mode),
        int(metadata.st_size),
        int(metadata.st_mtime_ns),
        digest,
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
        or binding.get("formal_routing_sidecar_snapshot_sha256") != _ROUTING_SNAPSHOT
        or binding.get("formal_routing_sidecar_aggregate_sha256") != _ROUTING_AGGREGATE
    ):
        _fail()
    return carrier_snapshot, routing_snapshot


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
    samples = [
        {
            "sample_index_row_id": identity[0],
            "sample_preparation_input_id": identity[1],
            "pdb_id": identity[2],
            "ligand_comp_id": identity[3],
            "source_sample_index": index,
        }
        for index, identity in enumerate(compiler._SOURCE_IDENTITIES)
    ]
    return {
        "schema_version": compiler._SOURCE_SCHEMA,
        "source_projection_digest": compiler._PROJECTION_DIGEST,
        "source_payload_digest": compiler._PAYLOAD_DIGEST,
        "parser_schema_version": compiler._PARSER_SCHEMA,
        "collate_schema_version": compiler._COLLATE_SCHEMA,
        "source_sample_order": samples,
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
            digest = hashlib.sha256(f"{index}:{role_name}".encode("utf-8")).hexdigest()
            roles[role_name] = {
                "root_kind": "repo_root",
                "relative_path": f"fixture/{index}/{role_name}.csv",
                "SHA256": digest,
                "row_count": selected_source + 10,
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


def _authority_fixture() -> tuple[dict[str, object], list[dict[str, object]], dict[str, bool]]:
    source = _source_fixture()
    return source, _provider_fixture(source), _readiness_fixture()


def _membership(lengths: Sequence[int]) -> list[int]:
    return [ordinal for ordinal, length in enumerate(lengths) for _ in range(length)]


def _observation(
    order: Sequence[int],
    authority: tuple[dict[str, object], list[dict[str, object]], dict[str, bool]],
    *,
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
    base = _observation((10, 4, 0), authority, joint=None)

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


def _validate_public_and_kernel_source() -> None:
    if compiler.__all__ != ("compile_covapie_current11_task2_batch_descriptor_v1",):
        _fail()
    public_signature = inspect.signature(
        compiler.compile_covapie_current11_task2_batch_descriptor_v1
    )
    if (
        tuple(public_signature.parameters) != ("repo_root", "state_root", "observation")
        or any(
            parameter.kind is not inspect.Parameter.KEYWORD_ONLY
            for parameter in public_signature.parameters.values()
        )
        or str(public_signature.return_annotation) != "dict[str, object]"
    ):
        _fail()
    kernel = getattr(compiler, "_compile_with_verified_authority_v1", None)
    if kernel is None or kernel.__name__ in compiler.__all__:
        _fail()
    kernel_signature = inspect.signature(kernel)
    if (
        tuple(kernel_signature.parameters) != ("authority", "observation")
        or any(
            parameter.kind is not inspect.Parameter.KEYWORD_ONLY
            for parameter in kernel_signature.parameters.values()
        )
    ):
        _fail()
    source = textwrap.dedent(inspect.getsource(kernel))
    tree = ast.parse(source)
    forbidden_names = {
        "repo_root",
        "state_root",
        "_require_root",
        "_authority",
        "_contract_gate",
        "adapter",
        "open",
        "subprocess",
        "git",
    }
    forbidden_attributes = {
        "open",
        "read_bytes",
        "read_text",
        "write_bytes",
        "write_text",
        "stat",
        "lstat",
        "resolve",
    }
    if any(isinstance(node, ast.Name) and node.id in forbidden_names for node in ast.walk(tree)):
        _fail()
    if any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in forbidden_attributes
        for node in ast.walk(tree)
    ):
        _fail()
    module_source = inspect.getsource(compiler)
    module_tree = ast.parse(module_source)
    if (
        "lru_cache" in module_source
        or "build_covapie_current11_task2_batch_descriptor_compiler_context_v1" in module_source
        or "compile_covapie_current11_task2_batch_descriptor_with_context_v1" in module_source
        or any(isinstance(node, ast.ClassDef) and "context" in node.name.lower() for node in module_tree.body)
    ):
        _fail()
    assignments = {
        target.id
        for node in module_tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (node.targets if isinstance(node, ast.Assign) else (node.target,))
        if isinstance(target, ast.Name)
    }
    if any("CACHE" in name.upper() for name in assignments):
        _fail()


def _direct_guarded(
    authority: tuple[dict[str, object], list[dict[str, object]], dict[str, bool]],
    observation: dict[str, object],
) -> dict[str, object]:
    counts = {"authority": 0, "root": 0, "gate": 0, "filesystem": 0, "adapter": 0}

    def forbidden(kind: str):
        def raising(*_args: object, **_kwargs: object) -> NoReturn:
            counts[kind] += 1
            raise AssertionError(f"{kind} called")

        return raising

    originals = {
        "authority": compiler._authority,
        "root": compiler._require_root,
        "gate": contract_gate.build_covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1,
        "adapter": adapter.build_covapie_current11_task2_batch_index_remap_adapter_v1,
        "open": builtins.open,
        "Path.open": Path.open,
        "Path.read_bytes": Path.read_bytes,
        "Path.read_text": Path.read_text,
        "Path.stat": Path.stat,
        "Path.lstat": Path.lstat,
        "Path.resolve": Path.resolve,
    }
    try:
        compiler._authority = forbidden("authority")
        compiler._require_root = forbidden("root")
        contract_gate.build_covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1 = forbidden("gate")
        adapter.build_covapie_current11_task2_batch_index_remap_adapter_v1 = forbidden("adapter")
        builtins.open = forbidden("filesystem")
        for name in ("open", "read_bytes", "read_text", "stat", "lstat", "resolve"):
            setattr(Path, name, forbidden("filesystem"))
        result = compiler._compile_with_verified_authority_v1(
            authority=authority,
            observation=observation,
        )
    finally:
        compiler._authority = originals["authority"]
        compiler._require_root = originals["root"]
        contract_gate.build_covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1 = originals["gate"]
        adapter.build_covapie_current11_task2_batch_index_remap_adapter_v1 = originals["adapter"]
        builtins.open = originals["open"]
        for name in ("open", "read_bytes", "read_text", "stat", "lstat", "resolve"):
            setattr(Path, name, originals[f"Path.{name}"])
    if counts != {"authority": 0, "root": 0, "gate": 0, "filesystem": 0, "adapter": 0}:
        _fail()
    return result


def _parity(
    repo: Path, state: Path
) -> tuple[dict[str, dict[str, object]], dict[str, dict[str, object]], int]:
    fixture = _authority_fixture()
    success = {
        case_id: _observation(order, fixture, joint=joint)
        for case_id, order, joint in _SUCCESS_SPECS
    }
    failures = _failure_observations(fixture)
    if tuple(failures) != _FAILURE_IDS:
        _fail()
    cases = {**success, **failures}
    slow_outputs: dict[str, dict[str, object]] = {}
    direct_outputs: dict[str, dict[str, object]] = {}
    authority_calls = 0
    original_authority = compiler._authority

    def fixture_authority(actual_repo: Path, actual_state: Path):
        nonlocal authority_calls
        if actual_repo != repo or actual_state != state:
            _fail()
        authority_calls += 1
        return copy.deepcopy(fixture)

    try:
        compiler._authority = fixture_authority
        for case_id, observation in cases.items():
            before = authority_calls
            slow_outputs[case_id] = (
                compiler.compile_covapie_current11_task2_batch_descriptor_v1(
                    repo_root=repo,
                    state_root=state,
                    observation=copy.deepcopy(observation),
                )
            )
            if authority_calls != before + 1:
                _fail()
    finally:
        compiler._authority = original_authority

    for case_id, observation in cases.items():
        direct_authority = copy.deepcopy(fixture)
        direct_observation = copy.deepcopy(observation)
        authority_before = copy.deepcopy(direct_authority)
        observation_before = copy.deepcopy(direct_observation)
        direct = _direct_guarded(direct_authority, direct_observation)
        if (
            direct != slow_outputs[case_id]
            or direct_authority != authority_before
            or direct_observation != observation_before
        ):
            _fail()
        direct_outputs[case_id] = direct
    repeated = _direct_guarded(copy.deepcopy(fixture), copy.deepcopy(success["canonical"]))
    if repeated != direct_outputs["canonical"]:
        _fail()
    return slow_outputs, direct_outputs, authority_calls


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


def _main(arguments: Sequence[str]) -> int:
    parser = _Parser(add_help=False, allow_abbrev=False)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--state-root", required=True, type=Path)
    namespace = parser.parse_args(arguments)
    repo = _root(namespace.repo_root)
    state = _root(namespace.state_root)
    _validate_repository_lineage(repo)
    lifecycle_before = _repository_lifecycle(repo)
    repository_before = _repository_snapshot(repo)
    formal_before = _formal_snapshot(state)
    _safe_exact4(repo)
    _validate_public_and_kernel_source()
    slow, direct, authority_calls = _parity(repo, state)
    success_ids = tuple(case_id for case_id, _order, _joint in _SUCCESS_SPECS)
    if (
        any(slow[case_id].get("compiler_status") != "COMPILED_EXACT" for case_id in success_ids)
        or any(direct[case_id].get("adapter_input_exact18") is None for case_id in success_ids)
        or any(direct[case_id].get("adapter_input_exact18") is not None for case_id in _FAILURE_IDS)
        or tuple(direct["canonical"]) != compiler._OUTPUT_FIELDS
        or tuple(direct["canonical"]["adapter_input_exact18"]) != compiler._EXACT18_FIELDS
        or authority_calls != len(_SUCCESS_SPECS) + len(_FAILURE_IDS)
    ):
        _fail()
    formal_unchanged = _formal_snapshot(state) == formal_before
    repository_unchanged = _repository_snapshot(repo) == repository_before
    lifecycle_after = _repository_lifecycle(repo)
    if (
        lifecycle_after != lifecycle_before
        or formal_unchanged is not True
        or repository_unchanged is not True
    ):
        _fail()
    readiness = {
        "compiler_hot_loop_authority_context_contract_designed": True,
        "compiler_hot_loop_authority_context_contract_gate_implemented": True,
        "compiler_hot_loop_authority_context_contract_gate_passed": True,
        "compiler_shared_pure_kernel_refactor_implemented": True,
        "compiler_shared_pure_kernel_refactor_passed": True,
        "compiler_hot_loop_authority_context_implemented": False,
        "ready_for_compiler_hot_loop_authority_context_module_implementation": True,
        "runtime_batch_observation_extractor_implemented": True,
        "task2_batch_descriptor_compiler_implemented": True,
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
        "status": "PASS_SHARED_KERNEL_REFACTOR_ONLY",
        "repository_lifecycle": lifecycle_after,
        "repository_unchanged": repository_unchanged,
        "formal_carrier_and_routing_unchanged": formal_unchanged,
        "context_contract_digest": _CONTEXT_CONTRACT_DIGEST,
        "authority_snapshot_digest": _AUTHORITY_SNAPSHOT_DIGEST,
        "formal_carrier_aggregate": _CARRIER_AGGREGATE,
        "formal_carrier_npz_sha256": _CARRIER_NPZ_SHA256,
        "formal_routing_snapshot": _ROUTING_SNAPSHOT,
        "formal_routing_aggregate": _ROUTING_AGGREGATE,
        "public___all__": list(compiler.__all__),
        "private_kernel": "_compile_with_verified_authority_v1",
        "slow_authority_calls_per_call": 1,
        "slow_authority_call_count": authority_calls,
        "direct_kernel_authority_call_count": 0,
        "direct_kernel_root_call_count": 0,
        "direct_kernel_gate_call_count": 0,
        "direct_kernel_filesystem_call_count": 0,
        "direct_kernel_adapter_call_count": 0,
        "success_parity": {"checked": 4, "passed": 4},
        "hard_failure_parity": {"checked": 5, "passed": 5},
        "output_exact10_field_order_preserved": True,
        "adapter_exact18_field_order_preserved": True,
        "authority_and_observation_unmodified": True,
        "deterministic_repeated_direct_call": True,
        "hidden_cache_present": False,
        "context_product_implemented": False,
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
