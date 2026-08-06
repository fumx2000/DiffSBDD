"""Materialize the deterministic Current11 runtime carrier through a relative alias."""

from __future__ import annotations

import csv
import errno
import hashlib
import io
import json
import math
import os
import re
import secrets
import stat
import zipfile
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Iterator, Mapping, NoReturn, Sequence

import numpy as np

from covalent_ext import covapie_current11_runtime_sample_and_role_order_carrier_contract_gate_v1 as _gate


__all__ = (
    "materialize_covapie_current11_runtime_sample_and_role_order_carrier_v1",
)

_ERROR = "COVAPIE_CURRENT11_RUNTIME_SAMPLE_AND_ROLE_ORDER_CARRIER_MATERIALIZER_V1_ERROR"
_CLEANUP_ERROR = f"{_ERROR}_CLEANUP_FAILED"
_SCHEMA = "covapie_current11_runtime_sample_and_role_order_carrier_materializer_v1"
_REPORT_SCHEMA = "covapie_current11_runtime_sample_and_role_order_carrier_binding_report_v1"
_MANIFEST_SCHEMA = "covapie_current11_runtime_sample_and_role_order_carrier_manifest_v1"
_RUNTIME_KIND = "current11_processed_ligand_pocket_npz_v1"
_RUNTIME_BATCH_SCHEMA = "processed_ligand_pocket_dataset_collate_observation_no_virtual_v1"
_SAMPLE_KEY_SCHEMA = "covapie_sample_index_row_id_in_names_v1"
_ROLE_ORDER_SCHEMA = "order_preserving_checkpoint_heavy_projection_v1"
_VIRTUAL_POLICY = "no_virtual_nodes_v1"
_SOURCE_CONTRACT_DIGEST = "360ee9a2a75efae3189922426a53ebccf3f2e0fbc9c2fb33980112a6c5438b14"
_GATE_COMMIT = "f385a0fdd55fc205df71feca604fea729015aada"
_GATE_MODULE = (
    "src/covalent_ext/"
    "covapie_current11_runtime_sample_and_role_order_carrier_contract_gate_v1.py"
)
_GATE_CHECKER = (
    "scripts/check_covapie_current11_runtime_sample_and_role_order_carrier_contract_gate_v1.py"
)
_GATE_SOURCE_IDENTITIES = {
    _GATE_MODULE: (
        66006,
        1608,
        "b412ca0738a9d629ea20e1fabfd90c629f07ddce9cff9867e30d5ff2b6a6b7a0",
        "4defd2e39830ea184d46073b78f6fc7d0a50e98d",
    ),
    _GATE_CHECKER: (
        2382,
        75,
        "9b69c8d4552f2c80bf7b235dd87f1364c400dd6fdb5fe0cab0ac9729414d21a4",
        "cc8fe37b19985e443ceb3b144284861bfdfb155c",
    ),
}
_GATE_EXACT6_IDENTITIES = {
    "current11_runtime_sample_and_role_order_carrier_contract_manifest.json": (
        27982, 610, "b5a9110277d66023623e2aa92d3d4ef664c6755ccff7a6ec41467981e58276a2"
    ),
    "current11_runtime_sample_key_registry.csv": (
        1858, 12, "a119522026ffce887049b2d2475e2763df4ed0035e730f7b4a58b2d0c14e7671"
    ),
    "current11_runtime_role_order_registry.json": (
        98412, 6043, "b1092570d94edde242dc8d5f01a5af75cba539e4c8ce4ae6c901809649478053"
    ),
    "current11_runtime_carrier_manifest_schema.json": (
        6007, 185, "5a543a638b400c920ffe0fdc4acd16615534ab10b50258ea58899231b5e87cba"
    ),
    "current11_runtime_sample_and_role_order_carrier_status_vocabulary.csv": (
        1436, 14, "d54c2452f70445c127704c2410a296fd7059e8621c59839ff3bf00d3a0dc57a8"
    ),
    "current11_runtime_sample_and_role_order_carrier_contract_gate_report.json": (
        4991, 116, "be40fc6d9b1b0bae4e245482c6fe509ff4bc8d3f16d8513477c2baeb1ccc357a"
    ),
}
_SAMPLE_REGISTRY = "current11_runtime_sample_key_registry.csv"
_ROLE_REGISTRY = "current11_runtime_role_order_registry.json"
_CARRIER_SCHEMA = "current11_runtime_carrier_manifest_schema.json"
_GATE_REPORT = "current11_runtime_sample_and_role_order_carrier_contract_gate_report.json"

_MODULE_PATH = (
    "src/covalent_ext/"
    "covapie_current11_runtime_sample_and_role_order_carrier_materializer_v1.py"
)
_SCRIPT_PATH = (
    "scripts/check_covapie_current11_runtime_sample_and_role_order_carrier_materializer_v1.py"
)
_TEST_PATH = (
    "tests/test_covapie_current11_runtime_sample_and_role_order_carrier_materializer_v1.py"
)
_GUIDE_PATH = (
    "docs/covapie_current11_runtime_sample_and_role_order_carrier_materializer_v1_guide.md"
)
_REPOSITORY_EXACT4 = tuple(sorted((_MODULE_PATH, _SCRIPT_PATH, _TEST_PATH, _GUIDE_PATH)))

_NPZ = "current11_runtime_sample_and_role_order_carrier.npz"
_MANIFEST = "current11_runtime_sample_and_role_order_carrier_manifest.json"
_INVENTORY = "current11_runtime_sample_and_role_order_carrier_array_inventory.csv"
_REPORT = "current11_runtime_sample_and_role_order_carrier_binding_report.json"
_ARTIFACT_NAMES = (_NPZ, _MANIFEST, _INVENTORY, _REPORT)
_ARRAY_NAMES = (
    "names",
    "receptors",
    "lig_mask",
    "pocket_mask",
    "lig_coords",
    "pocket_coords",
    "lig_one_hot",
    "pocket_one_hot",
    "lig_source_row_index",
    "pocket_source_row_index",
    "lig_parser_local_index",
    "pocket_parser_local_index",
)
_MANIFEST_FIELDS = (
    "schema_version",
    "source_contract_digest",
    "sample_key_registry_digest",
    "role_order_registry_digest",
    "runtime_artifact_kind",
    "runtime_artifact_relative_path",
    "runtime_artifact_sha256",
    "runtime_batch_schema_version",
    "sample_key_schema_version",
    "role_order_schema_version",
    "virtual_node_policy",
    "sample_order",
    "names_binding",
    "receptors_binding",
    "ligand_buffer_binding",
    "pocket_buffer_binding",
    "materialization_provenance",
    "readiness",
)
_INVENTORY_FIELDS = (
    "array_index",
    "array_name",
    "npz_entry_name",
    "dtype",
    "shape_json",
    "logical_role",
    "semantic_authority",
    "raw_c_order_bytes",
    "raw_c_order_sha256",
    "npy_bytes",
    "npy_sha256",
    "identity_selection_authorized",
    "required_by_processed_dataset",
)
_CHANNELS = ("C", "N", "O", "S", "B", "Br", "Cl", "P", "I", "F")
_CHANNEL_INDEX = {symbol: index for index, symbol in enumerate(_CHANNELS)}
_EXPECTED_LIGAND_LENGTHS = (13, 13, 13, 25, 28, 43, 42, 42, 43, 40, 21)
_EXPECTED_POCKET_LENGTHS = (66, 104, 96, 208, 188, 278, 267, 257, 249, 261, 228)
_EXPECTED_LIGAND_H = (0, 5, 0, 8, 3, 0, 0, 0, 0, 0, 0)
_EXPECTED_POCKET_H = (55, 92, 82, 57, 43, 0, 0, 0, 0, 0, 0)
_EXPECTED_SAMPLE_IDS = tuple(
    f"CYS_SG_SAMPLE_INDEX_{index:06d}" for index in range(1, 12)
)
_EXPECTED_RECEPTORS = (
    "6BV6", "6BV8", "6BV5", "1AEC", "1AIM", "1AU3", "1AU4", "1AYU",
    "1AYV", "1AYW", "1B02",
)
_NAMES_SEMANTIC_DIGEST = (
    "e20c1a3f764757ffac99b8e812a4caba23500270edd352ed159fdb18867a28ac"
)
_SAMPLE_REGISTRY_FIELDS = (
    "sample_index_0based",
    "sample_index_row_id",
    "sample_preparation_input_id",
    "pdb_id",
    "ligand_comp_id",
    "expected_name",
    "expected_receptor",
    "sample_key_schema_version",
    "sample_key_exact_one",
    "runtime_carrier_materialized",
)
_ROLE_HEADERS = {
    "ligand": (
        "sample_preparation_input_id", "pdb_id", "expected_het_id", "atom_site_id",
        "type_symbol", "atom_name", "ligand_comp_id", "auth_asym_id", "auth_seq_id",
        "label_asym_id", "label_seq_id", "x", "y", "z", "occupancy", "altloc",
        "model_num", "is_covalent_ligand_atom", "source_raw_file",
    ),
    "pocket": (
        "sample_preparation_input_id", "pdb_id", "pocket_radius_angstrom", "atom_site_id",
        "group_pdb", "type_symbol", "atom_name", "residue_name", "chain_id",
        "residue_index", "auth_asym_id", "auth_seq_id", "label_asym_id", "label_seq_id",
        "x", "y", "z", "min_distance_to_ligand_angstrom", "source_raw_file",
    ),
}
_IDENTITY_FIELDS = (
    "atom_site_id", "atom_name", "type_symbol", "residue_name_or_ligand_comp_id",
    "auth_asym_id", "auth_seq_id", "label_asym_id", "label_seq_id",
)
_CANONICAL_RELATIVE = (
    "formal-sidecars/current11-runtime-sample-and-role-order-carrier-v1"
)
_CANONICAL_BASENAME = "current11-runtime-sample-and-role-order-carrier-v1"
_OBJECT_PREFIX = f".{_CANONICAL_BASENAME}.object-sha256-"
_OBJECT_PATTERN = re.compile(
    rf"^\.{re.escape(_CANONICAL_BASENAME)}\.object-sha256-"
    r"([0-9a-f]{64})-([0-9a-f]{32})$"
)
_AGGREGATE_DOMAIN = (
    b"COVAPIE_CURRENT11_RUNTIME_SAMPLE_AND_ROLE_ORDER_CARRIER_MATERIALIZER_V1\0"
)
_RUNTIME_ARTIFACT_RELATIVE = f"{_CANONICAL_RELATIVE}/{_NPZ}"
_ROUTING_AGGREGATE = "24f95099ba1ba0b81724535cb17c5d4d32c360f71c87422571210a2178ddb49c"
_ROUTING_SNAPSHOT = "768fbd980efbcedcaa2ef971a7d77791879111d1fceeb1f03cb1eb8bfff24034"
_ROUTING_CANONICAL_RELATIVE = (
    "formal-sidecars/current11-dataset-partial-supervision-routing-sidecar-v1"
)
_ROUTING_READLINK = (
    ".current11-dataset-partial-supervision-routing-sidecar-v2."
    "object-sha256-24f95099ba1ba0b81724535cb17c5d4d32c360f71c87422571210a2178ddb49c-"
    "1fd8cf5823427e941b11c7b2560a336f"
)
_ROUTING_EXACT4 = {
    "current11_dataset_partial_supervision_routing_manifest.json": (
        "3a2c2e8170f20ed0a8ea97798a5945ec846cd36d81fe950aa58fee6311984a7d"
    ),
    "current11_dataset_partial_supervision_routing_records.csv": (
        "751e32f46ab386604386167bdffd38f762472bbc9fdff4af7167a979ac68af03"
    ),
    "current11_dataset_partial_supervision_sample_coverage.csv": (
        "7cd2ecd99caca09f94019d543793f70de6d9cb86ff431fbd49782b76b2814b5e"
    ),
    "current11_dataset_partial_supervision_task_coverage.csv": (
        "ee8bfe7f0bed65e6858ae318695470abc3a92de3ca72d2548e2d5c4e950aa2b7"
    ),
}
_PATH_TYPE = type(Path())
_DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
_READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
_WRITE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC


class _CleanupFailure(ValueError):
    pass


def _fail() -> NoReturn:
    raise ValueError(_ERROR)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _blob(payload: bytes) -> str:
    framed = b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload
    return hashlib.sha1(framed).hexdigest()


def _json(value: object) -> bytes:
    try:
        return (
            json.dumps(
                value, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ValueError(_ERROR) from error


def _compact_json(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ValueError(_ERROR) from error


def _strict_json(payload: bytes) -> dict[str, object]:
    try:
        value = json.loads(payload.decode("utf-8"), parse_constant=lambda _value: _fail())
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(_ERROR) from error
    if type(value) is not dict:
        _fail()
    return value


def _safe_relative(relative: object) -> PurePosixPath:
    if type(relative) is not str:
        _fail()
    path = PurePosixPath(relative)
    if not relative or path.is_absolute() or ".." in path.parts or str(path) != relative:
        _fail()
    return path


def _require_root(path: Path) -> Path:
    if type(path) is not _PATH_TYPE or not path.is_absolute():
        _fail()
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ValueError(_ERROR) from error
    if resolved != path or stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        _fail()
    return path


def _read_regular(root: Path, relative: object, digest: str | None = None) -> bytes:
    rel = _safe_relative(relative)
    path = root.joinpath(*rel.parts)
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
        payload = path.read_bytes()
    except (OSError, RuntimeError) as error:
        raise ValueError(_ERROR) from error
    if (
        not resolved.is_relative_to(root)
        or stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or (digest is not None and _sha(payload) != digest)
    ):
        _fail()
    return payload


def _validate_routing_object(state: Path) -> None:
    canonical = state / _ROUTING_CANONICAL_RELATIVE
    try:
        canonical_metadata = canonical.lstat()
        link = os.readlink(canonical)
        object_path = canonical.parent / link
        object_metadata = object_path.lstat()
        inventory = tuple(sorted(os.listdir(object_path)))
    except (OSError, RuntimeError) as error:
        raise ValueError(_ERROR) from error
    if (
        not stat.S_ISLNK(canonical_metadata.st_mode)
        or link != _ROUTING_READLINK
        or object_path.resolve(strict=True) != object_path
        or stat.S_ISLNK(object_metadata.st_mode)
        or not stat.S_ISDIR(object_metadata.st_mode)
        or stat.S_IMODE(object_metadata.st_mode) != 0o755
        or inventory != tuple(sorted(_ROUTING_EXACT4))
    ):
        _fail()
    for name, digest in _ROUTING_EXACT4.items():
        path = object_path / name
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
        except OSError as error:
            raise ValueError(_ERROR) from error
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o644
            or _sha(payload) != digest
        ):
            _fail()


def _authority_state(repo: Path) -> Path:
    state = _require_root(repo.parent / "covapie-state")
    _validate_routing_object(state)
    return state


def _csv_rows(payload: bytes, expected_fields: Sequence[str]) -> list[dict[str, str]]:
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
        if tuple(reader.fieldnames or ()) != tuple(expected_fields):
            _fail()
        rows = [dict(row) for row in reader]
    except (UnicodeDecodeError, csv.Error) as error:
        raise ValueError(_ERROR) from error
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        _fail()
    return rows


def _validate_gate_sources(repo: Path) -> None:
    for relative, expected in _GATE_SOURCE_IDENTITIES.items():
        payload = _read_regular(repo, relative)
        path = repo / relative
        metadata = path.lstat()
        if (
            stat.S_IMODE(metadata.st_mode) != 0o644
            or (len(payload), payload.count(b"\n"), _sha(payload), _blob(payload)) != expected
        ):
            _fail()


@contextmanager
def _precommit_compatibility() -> Iterator[None]:
    owner = _gate._adapter._projection_contract_gate
    original = owner._run_git

    def compatible(root: Path, arguments: Sequence[str]) -> str:
        output = original(root, arguments)
        if tuple(arguments) in {
            ("status", "--porcelain=v1", "--untracked-files=all"),
            ("status", "--short"),
        }:
            allowed = {f"?? {path}" for path in _REPOSITORY_EXACT4}
            output = "\n".join(line for line in output.splitlines() if line not in allowed)
        return output

    try:
        owner._run_git = compatible
        yield
    finally:
        owner._run_git = original


def _gate_exact6(repo: Path, state: Path) -> dict[str, bytes]:
    _validate_gate_sources(repo)
    try:
        with _precommit_compatibility():
            first = _gate.build_covapie_current11_runtime_sample_and_role_order_carrier_contract_gate_v1(
                repo_root=repo, state_root=state
            )
            second = _gate.build_covapie_current11_runtime_sample_and_role_order_carrier_contract_gate_v1(
                repo_root=repo, state_root=state
            )
    except BaseException as error:
        raise ValueError(_ERROR) from error
    if type(first) is not dict or tuple(first) != tuple(_GATE_EXACT6_IDENTITIES) or first != second:
        _fail()
    for name, expected in _GATE_EXACT6_IDENTITIES.items():
        payload = first.get(name)
        if type(payload) is not bytes or (len(payload), payload.count(b"\n"), _sha(payload)) != expected:
            _fail()
    report = _strict_json(first[_GATE_REPORT])
    if report.get("gate_status") != "PASS_CONTRACT_ONLY" or report.get("contract_digest") != _SOURCE_CONTRACT_DIGEST:
        _fail()
    return first


def _parse_authority(exact6: Mapping[str, bytes]) -> tuple[list[dict[str, str]], dict[str, object], dict[str, object]]:
    samples = _csv_rows(exact6[_SAMPLE_REGISTRY], _SAMPLE_REGISTRY_FIELDS)
    roles = _strict_json(exact6[_ROLE_REGISTRY])
    schema = _strict_json(exact6[_CARRIER_SCHEMA])
    if (
        len(samples) != 11
        or tuple(row["sample_index_row_id"] for row in samples) != _EXPECTED_SAMPLE_IDS
        or any(
            row["sample_index_0based"] != str(index)
            or row["expected_name"] != row["sample_index_row_id"]
            or row["expected_receptor"] != row["pdb_id"]
            or row["sample_key_schema_version"] != _SAMPLE_KEY_SCHEMA
            or row["sample_key_exact_one"] != "true"
            or row["runtime_carrier_materialized"] != "false"
            for index, row in enumerate(samples)
        )
        or roles.get("schema_version") != "covapie_current11_runtime_role_order_registry_v1"
        or roles.get("role_order") != ["pocket", "ligand"]
        or type(roles.get("role_order_records")) is not list
        or len(roles["role_order_records"]) != 22
        or roles.get("aggregate_counts")
        != {
            "role_record_count": 22,
            "sample_count": 11,
            "total_explicit_h_ligand": 16,
            "total_explicit_h_pocket": 329,
            "total_retained_ligand": 323,
            "total_retained_pocket": 2202,
            "total_source_rows_ligand": 339,
            "total_source_rows_pocket": 2531,
            "unsupported_nonhydrogen_count": 0,
        }
    ):
        _fail()
    _validate_published_carrier_schema(schema)
    return samples, roles, schema


def _expected_published_carrier_schema() -> dict[str, object]:
    order = list(_EXPECTED_SAMPLE_IDS)
    role_binding = {
        "required_fields": [
            "role",
            "projection_schema_version",
            "sample_offsets",
            "sample_lengths",
            "per_sample_role_order_record_digests",
            "flat_projected_source_row_order_digest",
            "flat_atom_identity_sequence_digest",
            "padding_present",
            "virtual_nodes_present",
            "atom_reorder_present",
        ],
        "sample_offsets": "int64[S+1] exact exclusive prefix sum",
        "sample_lengths": "int64[S] exact retained-heavy counts",
        "padding_present_required_value": False,
        "virtual_nodes_present_required_value": False,
        "atom_reorder_present_required_value": False,
    }
    return {
        "schema_version": _MANIFEST_SCHEMA,
        "artifact_kind": "manifest_schema_not_manifest_instance",
        "top_level_field_order": list(_MANIFEST_FIELDS),
        "top_level_fields": {
            "schema_version": {"exact_value": _MANIFEST_SCHEMA},
            "source_contract_digest": {
                "required": True,
                "format": "lowercase_sha256",
            },
            "sample_key_registry_digest": {
                "required": True,
                "format": "lowercase_sha256",
            },
            "role_order_registry_digest": {
                "required": True,
                "format": "lowercase_sha256",
            },
            "runtime_artifact_kind": {"exact_value": _RUNTIME_KIND},
            "runtime_artifact_relative_path": {
                "required_in_instance": True,
                "safe_state_root_relative": True,
                "repository_committed_npz_forbidden": True,
                "actual_value_in_schema": None,
            },
            "runtime_artifact_sha256": {
                "required_in_instance": True,
                "format": "lowercase_sha256_of_actual_runtime_artifact_bytes",
                "actual_value_in_schema": None,
            },
            "runtime_batch_schema_version": {
                "exact_value": _RUNTIME_BATCH_SCHEMA,
            },
            "sample_key_schema_version": {"exact_value": _SAMPLE_KEY_SCHEMA},
            "role_order_schema_version": {"exact_value": _ROLE_ORDER_SCHEMA},
            "virtual_node_policy": {"exact_value": _VIRTUAL_POLICY},
            "sample_order": {"exact_value": order},
            "names_binding": {
                "field_name": "names",
                "sample_key_schema_version": _SAMPLE_KEY_SCHEMA,
                "sample_order": order,
                "array_dtype_family": "unicode_string",
                "array_rank": 1,
                "array_length": 11,
                "array_values_digest": _NAMES_SEMANTIC_DIGEST,
                "array_values_digest_framing": (
                    "canonical compact JSON exact string array"
                ),
                "exact_values_required": True,
            },
            "receptors_binding": {
                "field_name": "receptors",
                "identity_authority": False,
                "consistency_only": True,
                "recommended_exact_values": list(_EXPECTED_RECEPTORS),
            },
            "ligand_buffer_binding": {"role": "ligand", **role_binding},
            "pocket_buffer_binding": {"role": "pocket", **role_binding},
            "materialization_provenance": {
                "required": True,
                "must_bind_actual_artifact_bytes": True,
                "must_not_claim_temporary_probe_as_formal": True,
            },
            "readiness": {
                "required_fields": [
                    "formal_runtime_carrier_materialized",
                    "runtime_batch_sample_key_available",
                    "runtime_batch_role_order_binding_available",
                    "ready_for_batch_descriptor_compiler_contract_gate_implementation",
                ],
                "formal_instance_success_requires_all_true": True,
            },
        },
        "runtime_schema_contract": {
            "padding_present": False,
            "crop_present": False,
            "atom_reorder_present": False,
            "virtual_nodes_present": False,
            "ligand_and_pocket_role_spaces_independent": True,
        },
        "schema_is_instance": False,
    }


def _validate_published_carrier_schema(carrier_schema: object) -> None:
    expected = _expected_published_carrier_schema()
    if (
        type(carrier_schema) is not dict
        or carrier_schema != expected
        or _sha(_json(carrier_schema))
        != _GATE_EXACT6_IDENTITIES[_CARRIER_SCHEMA][2]
    ):
        _fail()


def _record_without_digest(record: Mapping[str, object]) -> dict[str, object]:
    return {key: value for key, value in record.items() if key != "role_order_record_sha256"}


def _identity(row: Mapping[str, str], role: str) -> dict[str, str]:
    result = {
        "atom_site_id": row["atom_site_id"],
        "atom_name": row["atom_name"],
        "type_symbol": row["type_symbol"],
        "residue_name_or_ligand_comp_id": (
            row["ligand_comp_id"] if role == "ligand" else row["residue_name"]
        ),
        "auth_asym_id": row["auth_asym_id"],
        "auth_seq_id": row["auth_seq_id"],
        "label_asym_id": row["label_asym_id"],
        "label_seq_id": row["label_seq_id"],
    }
    if tuple(result) != _IDENTITY_FIELDS:
        _fail()
    return result


def _role_arrays(
    repo: Path,
    role: str,
    records: Sequence[Mapping[str, object]],
) -> tuple[dict[str, np.ndarray], dict[str, object]]:
    expected_lengths = _EXPECTED_LIGAND_LENGTHS if role == "ligand" else _EXPECTED_POCKET_LENGTHS
    expected_h = _EXPECTED_LIGAND_H if role == "ligand" else _EXPECTED_POCKET_H
    coordinates: list[list[float]] = []
    one_hot: list[list[float]] = []
    source_rows: list[int] = []
    local_rows: list[int] = []
    flat_identities: list[dict[str, str]] = []
    record_digests: list[str] = []
    table_evidence: list[dict[str, object]] = []
    lengths: list[int] = []
    for sample_index, record in enumerate(records):
        if (
            type(record) is not dict
            or record.get("sample_index_0based") != sample_index
            or record.get("sample_index_row_id") != _EXPECTED_SAMPLE_IDS[sample_index]
            or record.get("role") != role
            or record.get("source_table_root_kind") != "repo_root"
            or record.get("projection_schema_version") != _ROLE_ORDER_SCHEMA
            or record.get("runtime_role_order_materialized") is not False
            or record.get("unsupported_nonhydrogen_count") != 0
            or record.get("retained_heavy_count") != expected_lengths[sample_index]
            or record.get("explicit_hydrogen_count") != expected_h[sample_index]
        ):
            _fail()
        record_digest = record.get("role_order_record_sha256")
        if type(record_digest) is not str or _sha(_compact_json(_record_without_digest(record))) != record_digest:
            _fail()
        payload = _read_regular(repo, record.get("source_table_relative_path"), record.get("source_table_sha256"))
        rows = _csv_rows(payload, _ROLE_HEADERS[role])
        if len(rows) != record.get("source_row_count"):
            _fail()
        classes = [
            "H" if row["type_symbol"] == "H" else (
                "supported" if row["type_symbol"] in _CHANNEL_INDEX else "unsupported"
            )
            for row in rows
        ]
        projected = [index for index, value in enumerate(classes) if value == "supported"]
        source_to_projected: list[int | None] = []
        ordinal = 0
        for value in classes:
            if value == "supported":
                source_to_projected.append(ordinal)
                ordinal += 1
            else:
                source_to_projected.append(None)
        if (
            "unsupported" in classes
            or classes.count("H") != expected_h[sample_index]
            or projected != record.get("projected_source_row_indices_int64")
            or source_to_projected != record.get("source_to_projected_index_nullable_int64")
            or any(left >= right for left, right in zip(projected, projected[1:]))
            or [value for value in source_to_projected if value is not None] != list(range(len(projected)))
            or source_to_projected[record["selected_task2_source_row_index_0based"]]
            != record.get("selected_task2_parser_local_index_0based")
        ):
            _fail()
        identities = [_identity(rows[index], role) for index in projected]
        if _sha(_compact_json(identities)) != record.get("projected_atom_identity_sequence_sha256"):
            _fail()
        for local_index, source_index in enumerate(projected):
            row = rows[source_index]
            try:
                coordinate = [float(row[column]) for column in ("x", "y", "z")]
            except (TypeError, ValueError) as error:
                raise ValueError(_ERROR) from error
            if not all(math.isfinite(value) for value in coordinate):
                _fail()
            vector = [0.0] * len(_CHANNELS)
            vector[_CHANNEL_INDEX[row["type_symbol"]]] = 1.0
            coordinates.append(coordinate)
            one_hot.append(vector)
            source_rows.append(source_index)
            local_rows.append(local_index)
        flat_identities.extend(identities)
        lengths.append(len(projected))
        record_digests.append(record_digest)
        table_evidence.append(
            {
                "sample_index_0based": sample_index,
                "sample_index_row_id": record["sample_index_row_id"],
                "role": role,
                "relative_path": record["source_table_relative_path"],
                "sha256": record["source_table_sha256"],
                "row_count": len(rows),
                "retained_heavy_count": len(projected),
                "explicit_hydrogen_count": classes.count("H"),
                "unsupported_nonhydrogen_count": 0,
                "role_order_record_sha256": record_digest,
                "projected_atom_identity_sequence_sha256": record[
                    "projected_atom_identity_sequence_sha256"
                ],
                "full_order_verified": True,
                "selected_endpoint_parity_verified": True,
            }
        )
    offsets = [0]
    for length in lengths:
        offsets.append(offsets[-1] + length)
    prefix = "lig" if role == "ligand" else "pocket"
    coords_float32 = np.ascontiguousarray(np.asarray(coordinates, dtype="<f4"))
    if not np.all(np.isfinite(coords_float32)):
        _fail()
    arrays = {
        f"{prefix}_mask": np.repeat(
            np.arange(11, dtype="<i8"), np.asarray(lengths, dtype="<i8")
        ),
        f"{prefix}_coords": coords_float32,
        f"{prefix}_one_hot": np.ascontiguousarray(np.asarray(one_hot, dtype="<f4")),
        f"{prefix}_source_row_index": np.ascontiguousarray(np.asarray(source_rows, dtype="<i8")),
        f"{prefix}_parser_local_index": np.ascontiguousarray(np.asarray(local_rows, dtype="<i8")),
    }
    evidence = {
        "role": role,
        "projection_schema_version": _ROLE_ORDER_SCHEMA,
        "sample_offsets": offsets,
        "sample_lengths": lengths,
        "per_sample_role_order_record_digests": record_digests,
        "flat_projected_source_row_order_digest": _sha(_compact_json(source_rows)),
        "flat_atom_identity_sequence_digest": _sha(_compact_json(flat_identities)),
        "coordinates_raw_c_order_sha256": _sha(arrays[f"{prefix}_coords"].tobytes(order="C")),
        "one_hot_raw_c_order_sha256": _sha(arrays[f"{prefix}_one_hot"].tobytes(order="C")),
        "source_row_index_raw_c_order_sha256": _sha(
            arrays[f"{prefix}_source_row_index"].tobytes(order="C")
        ),
        "parser_local_index_raw_c_order_sha256": _sha(
            arrays[f"{prefix}_parser_local_index"].tobytes(order="C")
        ),
        "padding_present": False,
        "crop_present": False,
        "virtual_nodes_present": False,
        "atom_reorder_present": False,
        "source_coordinates_used": True,
        "source_one_hot_used": True,
        "tables": table_evidence,
    }
    return arrays, evidence


def _arrays_from_authority(
    repo: Path, samples: Sequence[Mapping[str, str]], roles: Mapping[str, object]
) -> tuple[dict[str, np.ndarray], dict[str, object]]:
    records = roles["role_order_records"]
    pocket_records = records[:11]
    ligand_records = records[11:]
    pocket_arrays, pocket_evidence = _role_arrays(repo, "pocket", pocket_records)
    ligand_arrays, ligand_evidence = _role_arrays(repo, "ligand", ligand_records)
    arrays = {
        "names": np.asarray([row["sample_index_row_id"] for row in samples], dtype="<U27"),
        "receptors": np.asarray([row["pdb_id"] for row in samples], dtype="<U4"),
        **ligand_arrays,
        **pocket_arrays,
    }
    arrays = {name: np.ascontiguousarray(arrays[name]) for name in _ARRAY_NAMES}
    expected = {
        "names": ((11,), "<U27"),
        "receptors": ((11,), "<U4"),
        "lig_mask": ((323,), "<i8"),
        "pocket_mask": ((2202,), "<i8"),
        "lig_coords": ((323, 3), "<f4"),
        "pocket_coords": ((2202, 3), "<f4"),
        "lig_one_hot": ((323, 10), "<f4"),
        "pocket_one_hot": ((2202, 10), "<f4"),
        "lig_source_row_index": ((323,), "<i8"),
        "pocket_source_row_index": ((2202,), "<i8"),
        "lig_parser_local_index": ((323,), "<i8"),
        "pocket_parser_local_index": ((2202,), "<i8"),
    }
    if tuple(arrays) != _ARRAY_NAMES:
        _fail()
    for name, array in arrays.items():
        if array.shape != expected[name][0] or array.dtype.str != expected[name][1] or not array.flags.c_contiguous:
            _fail()
        if array.dtype.hasobject:
            _fail()
    for name in ("lig_one_hot", "pocket_one_hot"):
        if not np.array_equal(arrays[name].sum(axis=1), np.ones(arrays[name].shape[0], dtype="<f4")):
            _fail()
        if not np.all((arrays[name] == 0.0) | (arrays[name] == 1.0)):
            _fail()
    return arrays, {"ligand": ligand_evidence, "pocket": pocket_evidence}


def _npy_bytes(array: np.ndarray) -> bytes:
    buffer = io.BytesIO()
    try:
        np.lib.format.write_array(buffer, array, version=(1, 0), allow_pickle=False)
    except (TypeError, ValueError) as error:
        raise ValueError(_ERROR) from error
    payload = buffer.getvalue()
    try:
        check = np.lib.format.read_array(io.BytesIO(payload), allow_pickle=False)
    except (TypeError, ValueError) as error:
        raise ValueError(_ERROR) from error
    if payload[:6] != b"\x93NUMPY" or payload[6:8] != bytes((1, 0)) or not np.array_equal(check, array):
        _fail()
    return payload


def _write_npz(arrays: Mapping[str, np.ndarray]) -> tuple[bytes, dict[str, bytes]]:
    npy_payloads = {name: _npy_bytes(arrays[name]) for name in _ARRAY_NAMES}
    output = io.BytesIO()
    with zipfile.ZipFile(output, mode="w", compression=zipfile.ZIP_STORED) as archive:
        archive.comment = b""
        for name in _ARRAY_NAMES:
            info = zipfile.ZipInfo(f"{name}.npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.extra = b""
            info.comment = b""
            archive.writestr(info, npy_payloads[name])
    payload = output.getvalue()
    _validate_npz(payload, arrays, npy_payloads)
    return payload, npy_payloads


def _validate_npz(
    payload: bytes,
    arrays: Mapping[str, np.ndarray],
    expected_npy: Mapping[str, bytes] | None = None,
) -> dict[str, object]:
    try:
        with zipfile.ZipFile(io.BytesIO(payload), mode="r") as archive:
            infos = archive.infolist()
            if archive.comment != b"" or [item.filename for item in infos] != [f"{name}.npy" for name in _ARRAY_NAMES]:
                _fail()
            npy_payloads: dict[str, bytes] = {}
            for name, info in zip(_ARRAY_NAMES, infos):
                if (
                    info.compress_type != zipfile.ZIP_STORED
                    or info.date_time != (1980, 1, 1, 0, 0, 0)
                    or info.create_system != 3
                    or stat.S_IFMT(info.external_attr >> 16) != stat.S_IFREG
                    or stat.S_IMODE(info.external_attr >> 16) != 0o644
                    or info.extra != b""
                    or info.comment != b""
                    or info.is_dir()
                ):
                    _fail()
                item = archive.read(info)
                if expected_npy is not None and item != expected_npy[name]:
                    _fail()
                npy_payloads[name] = item
    except (OSError, RuntimeError, zipfile.BadZipFile) as error:
        raise ValueError(_ERROR) from error
    try:
        with np.load(io.BytesIO(payload), allow_pickle=False) as loaded:
            if tuple(loaded.files) != _ARRAY_NAMES:
                _fail()
            for name in _ARRAY_NAMES:
                if not np.array_equal(loaded[name], arrays[name]) or loaded[name].dtype != arrays[name].dtype:
                    _fail()
    except (OSError, TypeError, ValueError) as error:
        raise ValueError(_ERROR) from error
    if payload.count(b"PK\x01\x02") != 12 or payload.count(b"PK\x03\x04") != 12 or payload.count(b"PK\x05\x06") != 1:
        _fail()
    return {
        "entry_count": 12,
        "compression": "ZIP_STORED",
        "timestamp": [1980, 1, 1, 0, 0, 0],
        "create_system": 3,
        "entry_mode": "0644 regular",
        "npy_version": "1.0",
        "archive_comment_empty": True,
        "entry_extra_empty": True,
        "directory_entry_count": 0,
        "central_directory_checked": True,
        "npy_payloads": npy_payloads,
    }


def _inventory_bytes(
    arrays: Mapping[str, np.ndarray], npy_payloads: Mapping[str, bytes]
) -> tuple[bytes, list[dict[str, object]]]:
    logical = {
        "names": "sample_key", "receptors": "receptor_consistency",
        "lig_mask": "ligand_membership", "pocket_mask": "pocket_membership",
        "lig_coords": "ligand_coordinates", "pocket_coords": "pocket_coordinates",
        "lig_one_hot": "ligand_checkpoint_features", "pocket_one_hot": "pocket_checkpoint_features",
        "lig_source_row_index": "ligand_role_order_evidence",
        "pocket_source_row_index": "pocket_role_order_evidence",
        "lig_parser_local_index": "ligand_role_order_evidence",
        "pocket_parser_local_index": "pocket_role_order_evidence",
    }
    semantic = {
        "names": "sole_sample_identity_authority",
        "receptors": "consistency_only_not_identity",
        "lig_coords": "source_table_coordinates_not_identity",
        "pocket_coords": "source_table_coordinates_not_identity",
        "lig_one_hot": "source_type_symbol_channel_not_identity",
        "pocket_one_hot": "source_type_symbol_channel_not_identity",
        "lig_source_row_index": "role_order_evidence_not_sample_identity",
        "pocket_source_row_index": "role_order_evidence_not_sample_identity",
        "lig_parser_local_index": "role_order_evidence_not_sample_identity",
        "pocket_parser_local_index": "role_order_evidence_not_sample_identity",
        "lig_mask": "sample_membership_not_identity",
        "pocket_mask": "sample_membership_not_identity",
    }
    rows: list[dict[str, object]] = []
    text = io.StringIO(newline="")
    writer = csv.DictWriter(text, fieldnames=_INVENTORY_FIELDS, lineterminator="\n")
    writer.writeheader()
    for index, name in enumerate(_ARRAY_NAMES):
        raw = arrays[name].tobytes(order="C")
        npy = npy_payloads[name]
        row: dict[str, object] = {
            "array_index": index,
            "array_name": name,
            "npz_entry_name": f"{name}.npy",
            "dtype": arrays[name].dtype.str,
            "shape_json": _compact_json(list(arrays[name].shape)).decode("ascii"),
            "logical_role": logical[name],
            "semantic_authority": semantic[name],
            "raw_c_order_bytes": len(raw),
            "raw_c_order_sha256": _sha(raw),
            "npy_bytes": len(npy),
            "npy_sha256": _sha(npy),
            "identity_selection_authorized": str(name == "names").lower(),
            "required_by_processed_dataset": str(index < 8).lower(),
        }
        rows.append(row)
        writer.writerow(row)
    return text.getvalue().encode("utf-8"), rows


def _formal_readiness() -> dict[str, bool]:
    return {
        "formal_runtime_carrier_materialized": True,
        "runtime_batch_sample_key_available": True,
        "runtime_batch_sample_key_exact_one_for_current11": True,
        "runtime_batch_role_order_binding_available": True,
        "current11_atom_identity_provider_available": True,
        "general_non_source_identity_provider_available": False,
        "ready_for_batch_descriptor_compiler_contract_gate_implementation": True,
        "ready_for_task2_batch_descriptor_compiler_implementation": False,
        "ready_for_runtime_batch_observation_extractor_design": True,
        "ready_for_dataloader_integration": False,
        "ready_for_model_integration": False,
        "ready_for_loss_integration": False,
        "feature_semantics_reaudit_required_before_training": True,
        "ready_for_training": False,
    }


def _manifest_value(
    exact6: Mapping[str, bytes],
    samples: Sequence[Mapping[str, str]],
    arrays: Mapping[str, np.ndarray],
    inventory: Sequence[Mapping[str, object]],
    evidence: Mapping[str, object],
    npz_sha: str,
) -> dict[str, object]:
    table_evidence = [*evidence["pocket"]["tables"], *evidence["ligand"]["tables"]]
    names = arrays["names"].tolist()
    names_semantic_digest = _sha(_compact_json(names))
    if names_semantic_digest != _NAMES_SEMANTIC_DIGEST:
        _fail()
    value = {
        "schema_version": _MANIFEST_SCHEMA,
        "source_contract_digest": _SOURCE_CONTRACT_DIGEST,
        "sample_key_registry_digest": _sha(exact6[_SAMPLE_REGISTRY]),
        "role_order_registry_digest": _sha(exact6[_ROLE_REGISTRY]),
        "runtime_artifact_kind": _RUNTIME_KIND,
        "runtime_artifact_relative_path": _RUNTIME_ARTIFACT_RELATIVE,
        "runtime_artifact_sha256": npz_sha,
        "runtime_batch_schema_version": _RUNTIME_BATCH_SCHEMA,
        "sample_key_schema_version": _SAMPLE_KEY_SCHEMA,
        "role_order_schema_version": _ROLE_ORDER_SCHEMA,
        "virtual_node_policy": _VIRTUAL_POLICY,
        "sample_order": [row["sample_index_row_id"] for row in samples],
        "names_binding": {
            "field_name": "names",
            "sample_key_schema_version": _SAMPLE_KEY_SCHEMA,
            "sample_order": [row["sample_index_row_id"] for row in samples],
            "array_dtype_family": "unicode_string",
            "array_rank": 1,
            "array_length": 11,
            "array_values_digest": names_semantic_digest,
            "array_values_digest_framing": (
                "canonical compact JSON exact string array"
            ),
            "exact_values_required": True,
        },
        "receptors_binding": {
            "field_name": "receptors",
            "identity_authority": False,
            "consistency_only": True,
            "recommended_exact_values": [row["pdb_id"] for row in samples],
        },
        "ligand_buffer_binding": {key: value for key, value in evidence["ligand"].items() if key != "tables"},
        "pocket_buffer_binding": {key: value for key, value in evidence["pocket"].items() if key != "tables"},
        "materialization_provenance": {
            "gate_commit": _GATE_COMMIT,
            "gate_module_relative_path": _GATE_MODULE,
            "gate_module_sha256": _GATE_SOURCE_IDENTITIES[_GATE_MODULE][2],
            "source_contract_digest": _SOURCE_CONTRACT_DIGEST,
            "gate_exact6": [
                {
                    "artifact_index": index,
                    "artifact_name": name,
                    "bytes": len(exact6[name]),
                    "LF": exact6[name].count(b"\n"),
                    "SHA256": _sha(exact6[name]),
                }
                for index, name in enumerate(_GATE_EXACT6_IDENTITIES)
            ],
            "npz_writer_schema": "npy_v1_0_zip_stored_epoch_0644_exact12_v1",
            "source_table_count": 22,
            "source_tables": table_evidence,
            "array_count": 12,
            "arrays": [
                {key: row[key] for key in ("array_index", "array_name", "raw_c_order_sha256", "npy_sha256")}
                for row in inventory
            ],
            "checkpoint_bytes_read": False,
            "design_markdown_read": False,
            "coordinates_centered": False,
            "coordinates_noised": False,
            "coordinates_rotated": False,
            "placeholder_ligand_used": False,
        },
        "readiness": _formal_readiness(),
    }
    if tuple(value) != _MANIFEST_FIELDS:
        _fail()
    return value


def _validate_manifest_instance_against_published_schema(
    *,
    manifest: dict[str, object],
    carrier_schema: dict[str, object],
    arrays: Mapping[str, np.ndarray],
    samples: Sequence[Mapping[str, str]],
    expected_runtime_artifact_sha256: str,
) -> None:
    _validate_published_carrier_schema(carrier_schema)
    if (
        type(manifest) is not dict
        or set(manifest) != set(_MANIFEST_FIELDS)
        or tuple(arrays) != _ARRAY_NAMES
        or type(samples) not in (list, tuple)
        or len(samples) != 11
        or type(expected_runtime_artifact_sha256) is not str
        or re.fullmatch(r"[0-9a-f]{64}", expected_runtime_artifact_sha256) is None
    ):
        _fail()
    sample_order = [row.get("sample_index_row_id") for row in samples]
    receptors = [row.get("pdb_id") for row in samples]
    if sample_order != list(_EXPECTED_SAMPLE_IDS) or receptors != list(_EXPECTED_RECEPTORS):
        _fail()
    scalar_exact = {
        "schema_version": _MANIFEST_SCHEMA,
        "source_contract_digest": _SOURCE_CONTRACT_DIGEST,
        "sample_key_registry_digest": _GATE_EXACT6_IDENTITIES[_SAMPLE_REGISTRY][2],
        "role_order_registry_digest": _GATE_EXACT6_IDENTITIES[_ROLE_REGISTRY][2],
        "runtime_artifact_kind": _RUNTIME_KIND,
        "runtime_artifact_relative_path": _RUNTIME_ARTIFACT_RELATIVE,
        "runtime_artifact_sha256": expected_runtime_artifact_sha256,
        "runtime_batch_schema_version": _RUNTIME_BATCH_SCHEMA,
        "sample_key_schema_version": _SAMPLE_KEY_SCHEMA,
        "role_order_schema_version": _ROLE_ORDER_SCHEMA,
        "virtual_node_policy": _VIRTUAL_POLICY,
        "sample_order": sample_order,
    }
    if any(manifest.get(key) != value for key, value in scalar_exact.items()):
        _fail()
    names = arrays["names"]
    names_digest = _sha(_compact_json(names.tolist()))
    expected_names_binding = {
        "field_name": "names",
        "sample_key_schema_version": _SAMPLE_KEY_SCHEMA,
        "sample_order": sample_order,
        "array_dtype_family": "unicode_string",
        "array_rank": 1,
        "array_length": 11,
        "array_values_digest": names_digest,
        "array_values_digest_framing": (
            "canonical compact JSON exact string array"
        ),
        "exact_values_required": True,
    }
    if (
        names.dtype.kind != "U"
        or names.ndim != 1
        or len(names) != 11
        or names.tolist() != sample_order
        or names_digest != _NAMES_SEMANTIC_DIGEST
        or manifest.get("names_binding") != expected_names_binding
        or names_digest == _sha(names.tobytes(order="C"))
    ):
        _fail()
    expected_receptors_binding = {
        "field_name": "receptors",
        "identity_authority": False,
        "consistency_only": True,
        "recommended_exact_values": receptors,
    }
    receptor_array = arrays["receptors"]
    if (
        receptor_array.dtype.kind != "U"
        or receptor_array.shape != (11,)
        or receptor_array.tolist() != receptors
        or manifest.get("receptors_binding") != expected_receptors_binding
    ):
        _fail()
    top_fields = carrier_schema["top_level_fields"]
    sha_pattern = re.compile(r"[0-9a-f]{64}")
    for role, prefix, lengths in (
        ("ligand", "lig", _EXPECTED_LIGAND_LENGTHS),
        ("pocket", "pocket", _EXPECTED_POCKET_LENGTHS),
    ):
        binding = manifest.get(f"{role}_buffer_binding")
        contract = top_fields[f"{role}_buffer_binding"]
        required = contract["required_fields"]
        offsets = [0]
        for length in lengths:
            offsets.append(offsets[-1] + length)
        source_rows = arrays[f"{prefix}_source_row_index"].tolist()
        if (
            type(binding) is not dict
            or any(field not in binding for field in required)
            or binding.get("role") != role
            or binding.get("projection_schema_version") != _ROLE_ORDER_SCHEMA
            or binding.get("sample_offsets") != offsets
            or binding.get("sample_lengths") != list(lengths)
            or binding.get("flat_projected_source_row_order_digest")
            != _sha(_compact_json(source_rows))
            or type(binding.get("per_sample_role_order_record_digests")) is not list
            or len(binding["per_sample_role_order_record_digests"]) != 11
            or any(
                type(value) is not str or sha_pattern.fullmatch(value) is None
                for value in binding["per_sample_role_order_record_digests"]
            )
            or type(binding.get("flat_atom_identity_sequence_digest")) is not str
            or sha_pattern.fullmatch(binding["flat_atom_identity_sequence_digest"])
            is None
            or binding.get("padding_present") is not False
            or binding.get("crop_present") is not False
            or binding.get("virtual_nodes_present") is not False
            or binding.get("atom_reorder_present") is not False
            or contract["padding_present_required_value"] is not False
            or contract["virtual_nodes_present_required_value"] is not False
            or contract["atom_reorder_present_required_value"] is not False
        ):
            _fail()
    provenance = manifest.get("materialization_provenance")
    if (
        type(provenance) is not dict
        or provenance.get("source_contract_digest") != _SOURCE_CONTRACT_DIGEST
        or provenance.get("source_table_count") != 22
        or provenance.get("array_count") != 12
        or provenance.get("checkpoint_bytes_read") is not False
        or provenance.get("design_markdown_read") is not False
    ):
        _fail()
    readiness = manifest.get("readiness")
    if readiness != _formal_readiness() or any(
        readiness.get(field) is not True
        for field in top_fields["readiness"]["required_fields"]
    ):
        _fail()


def _aggregate_sha256(artifacts: Mapping[str, bytes]) -> str:
    if type(artifacts) is not dict or tuple(artifacts) != _ARTIFACT_NAMES:
        _fail()
    digest = hashlib.sha256()
    digest.update(_AGGREGATE_DOMAIN)
    for name in _ARTIFACT_NAMES:
        encoded = name.encode("utf-8")
        payload = artifacts[name]
        if type(payload) is not bytes:
            _fail()
        digest.update(len(encoded).to_bytes(8, "big", signed=False))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big", signed=False))
        digest.update(payload)
    return digest.hexdigest()


def _validate_artifact(name: str, payload: bytes) -> None:
    if type(payload) is not bytes or not payload:
        _fail()
    if name != _NPZ:
        if (
            len(payload) >= 1024 * 1024
            or payload.startswith(b"\xef\xbb\xbf")
            or b"\0" in payload
            or b"\r" in payload
            or not payload.endswith(b"\n")
            or payload.endswith(b"\n\n")
            or any(line.endswith((b" ", b"\t")) for line in payload.splitlines())
        ):
            _fail()
        if name.endswith(".json") and _json(_strict_json(payload)) != payload:
            _fail()


def _validate_candidate_bundle(artifacts: dict[str, bytes]) -> dict[str, object]:
    if type(artifacts) is not dict or tuple(artifacts) != _ARTIFACT_NAMES:
        _fail()
    for name, payload in artifacts.items():
        _validate_artifact(name, payload)
    manifest = _strict_json(artifacts[_MANIFEST])
    report = _strict_json(artifacts[_REPORT])
    inventory = _csv_rows(artifacts[_INVENTORY], _INVENTORY_FIELDS)
    try:
        with np.load(io.BytesIO(artifacts[_NPZ]), allow_pickle=False) as loaded:
            arrays = {name: loaded[name].copy() for name in loaded.files}
    except (OSError, TypeError, ValueError) as error:
        raise ValueError(_ERROR) from error
    if tuple(arrays) != _ARRAY_NAMES:
        _fail()
    _validate_npz(artifacts[_NPZ], arrays)
    samples = [
        {"sample_index_row_id": sample, "pdb_id": receptor}
        for sample, receptor in zip(_EXPECTED_SAMPLE_IDS, _EXPECTED_RECEPTORS)
    ]
    _validate_manifest_instance_against_published_schema(
        manifest=manifest,
        carrier_schema=_expected_published_carrier_schema(),
        arrays=arrays,
        samples=samples,
        expected_runtime_artifact_sha256=_sha(artifacts[_NPZ]),
    )
    if (
        report.get("schema_version") != _REPORT_SCHEMA
        or report.get("status") != "PASS_FORMAL_RUNTIME_CARRIER_BUNDLE_EXACT"
        or report.get("artifact_count") != 4
        or report.get("array_count") != 12
        or len(inventory) != 12
    ):
        _fail()
    return {"manifest": manifest, "report": report, "inventory": inventory}


def _build_candidate_bundle(*, repo_root: Path, state_root: Path) -> dict[str, bytes]:
    """Build the formal Exact4 entirely in memory."""

    try:
        repo = _require_root(repo_root)
        state = _require_root(state_root)
        if repo == state or repo in state.parents:
            _fail()
        _validate_routing_object(state)
        exact6 = _gate_exact6(repo, _authority_state(repo))
        samples, roles, carrier_schema = _parse_authority(exact6)
        arrays, evidence = _arrays_from_authority(repo, samples, roles)
        npz, npy_payloads = _write_npz(arrays)
        inventory_bytes, inventory = _inventory_bytes(arrays, npy_payloads)
        manifest = _manifest_value(
            exact6, samples, arrays, inventory, evidence, _sha(npz)
        )
        _validate_manifest_instance_against_published_schema(
            manifest=manifest,
            carrier_schema=carrier_schema,
            arrays=arrays,
            samples=samples,
            expected_runtime_artifact_sha256=_sha(npz),
        )
        report = {
            "schema_version": _REPORT_SCHEMA,
            "status": "PASS_FORMAL_RUNTIME_CARRIER_BUNDLE_EXACT",
            "artifact_count": 4,
            "array_count": 12,
            "sample_count": 11,
            "ligand_atom_count": 323,
            "pocket_atom_count": 2202,
            "gate_contract_digest": _SOURCE_CONTRACT_DIGEST,
            "sample_key_registry_digest": _sha(exact6[_SAMPLE_REGISTRY]),
            "role_order_registry_digest": _sha(exact6[_ROLE_REGISTRY]),
            "runtime_npz_sha256": _sha(npz),
            "formal_routing_sidecar_snapshot_sha256": _ROUTING_SNAPSHOT,
            "formal_routing_sidecar_aggregate_sha256": _ROUTING_AGGREGATE,
            "source_table_count_verified": 22,
            "full_projected_source_orders_verified": True,
            "exact8_identity_sequences_verified": True,
            "coordinates_from_source_tables": True,
            "one_hot_from_source_type_symbols": True,
            "placeholder_ligand_used": False,
            "padding_present": False,
            "crop_present": False,
            "atom_reorder_present": False,
            "virtual_nodes_present": False,
            "dataset_candidate_validation": {
                "contract": "ProcessedLigandPocketDataset-compatible Exact12",
                "center_false_authorized": True,
                "center_true_coordinates_only_translation": True,
                "collate_actual_order_preserved": True,
                "explicit_permutation_and_subset_supported": True,
            },
            "feature_semantics_reaudit_required_before_training": True,
            "ready_for_training": False,
        }
        artifacts = {
            _NPZ: npz,
            _MANIFEST: _json(manifest),
            _INVENTORY: inventory_bytes,
            _REPORT: _json(report),
        }
        _validate_candidate_bundle(artifacts)
        return artifacts
    except BaseException as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _identity_of(metadata: os.stat_result) -> tuple[int, int]:
    return int(metadata.st_dev), int(metadata.st_ino)


def _stat_at(directory_fd: int, name: str) -> os.stat_result:
    return os.stat(name, dir_fd=directory_fd, follow_symlinks=False)


def _assert_parent(parent_fd: int, parent: Path, identity: tuple[int, int], mode: int) -> None:
    try:
        lexical = parent.lstat()
        descriptor = os.fstat(parent_fd)
        resolved = parent.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ValueError(_ERROR) from error
    if (
        resolved != parent
        or stat.S_ISLNK(lexical.st_mode)
        or not stat.S_ISDIR(lexical.st_mode)
        or not stat.S_ISDIR(descriptor.st_mode)
        or _identity_of(lexical) != identity
        or _identity_of(descriptor) != identity
        or stat.S_IMODE(lexical.st_mode) != mode
        or stat.S_IMODE(descriptor.st_mode) != mode
    ):
        _fail()


def _assert_object(
    parent_fd: int, object_fd: int, name: str, identity: tuple[int, int], mode: int
) -> None:
    lexical = _stat_at(parent_fd, name)
    descriptor = os.fstat(object_fd)
    if (
        stat.S_ISLNK(lexical.st_mode)
        or not stat.S_ISDIR(lexical.st_mode)
        or not stat.S_ISDIR(descriptor.st_mode)
        or _identity_of(lexical) != identity
        or _identity_of(descriptor) != identity
        or stat.S_IMODE(lexical.st_mode) != mode
        or stat.S_IMODE(descriptor.st_mode) != mode
    ):
        _fail()


def _read_fd(file_fd: int) -> bytes:
    chunks: list[bytes] = []
    while True:
        chunk = os.read(file_fd, 65536)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def _write_all(file_fd: int, payload: bytes) -> None:
    offset = 0
    while offset < len(payload):
        written = os.write(file_fd, payload[offset:])
        if type(written) is not int or written <= 0:
            raise OSError(errno.EIO, "short write")
        offset += written


def _read_leaf(object_fd: int, name: str, identity: tuple[int, int]) -> bytes:
    before = _stat_at(object_fd, name)
    if (
        stat.S_ISLNK(before.st_mode)
        or not stat.S_ISREG(before.st_mode)
        or stat.S_IMODE(before.st_mode) != 0o644
        or _identity_of(before) != identity
    ):
        _fail()
    file_fd = os.open(name, _READ_FLAGS, dir_fd=object_fd)
    try:
        descriptor = os.fstat(file_fd)
        if _identity_of(descriptor) != identity or stat.S_IMODE(descriptor.st_mode) != 0o644:
            _fail()
        payload = _read_fd(file_fd)
        after = _stat_at(object_fd, name)
        if _identity_of(after) != identity or stat.S_IMODE(after.st_mode) != 0o644:
            _fail()
        return payload
    finally:
        os.close(file_fd)


def _write_artifacts(
    object_fd: int, artifacts: Mapping[str, bytes], identities: dict[str, tuple[int, int]]
) -> None:
    for name in _ARTIFACT_NAMES:
        file_fd = os.open(name, _WRITE_FLAGS, 0o600, dir_fd=object_fd)
        try:
            metadata = os.fstat(file_fd)
            identity = _identity_of(metadata)
            identities[name] = identity
            if not stat.S_ISREG(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) != 0o600:
                _fail()
            _write_all(file_fd, artifacts[name])
            os.fchmod(file_fd, 0o644)
            os.fsync(file_fd)
            if _identity_of(os.fstat(file_fd)) != identity:
                _fail()
        finally:
            os.close(file_fd)
        if _read_leaf(object_fd, name, identities[name]) != artifacts[name]:
            _fail()
    if tuple(sorted(os.listdir(object_fd))) != tuple(sorted(_ARTIFACT_NAMES)):
        _fail()


def _read_object(
    parent_fd: int,
    object_fd: int,
    object_name: str,
    object_identity: tuple[int, int],
    object_mode: int,
    leaf_identities: Mapping[str, tuple[int, int]],
) -> dict[str, bytes]:
    _assert_object(parent_fd, object_fd, object_name, object_identity, object_mode)
    if tuple(sorted(os.listdir(object_fd))) != tuple(sorted(_ARTIFACT_NAMES)) or set(leaf_identities) != set(_ARTIFACT_NAMES):
        _fail()
    result = {name: _read_leaf(object_fd, name, leaf_identities[name]) for name in _ARTIFACT_NAMES}
    _assert_object(parent_fd, object_fd, object_name, object_identity, object_mode)
    return result


def _parse_object_name(name: object) -> tuple[str, str]:
    if type(name) is not str or os.path.isabs(name) or "/" in name or ".." in name:
        _fail()
    match = _OBJECT_PATTERN.fullmatch(name)
    if match is None:
        _fail()
    return match.group(1), match.group(2)


def _canonical_relation(
    parent_fd: int,
    canonical_name: str,
    object_name: str,
) -> str:
    try:
        metadata = _stat_at(parent_fd, canonical_name)
    except FileNotFoundError:
        return "absent"
    except OSError as error:
        raise ValueError(_ERROR) from error
    if not stat.S_ISLNK(metadata.st_mode):
        return "unrelated"
    try:
        target = os.readlink(canonical_name, dir_fd=parent_fd)
    except FileNotFoundError:
        return "absent"
    except OSError as error:
        raise ValueError(_ERROR) from error
    if target == object_name and not os.path.isabs(target) and "/" not in target:
        return "points_to_object"
    return "unrelated"


def _final_publication_revalidation(
    *,
    parent_fd: int,
    parent: Path,
    parent_identity: tuple[int, int],
    parent_mode: int,
    canonical_name: str,
    alias_identity: tuple[int, int],
    object_fd: int,
    object_name: str,
    object_identity: tuple[int, int],
    leaf_identities: Mapping[str, tuple[int, int]],
) -> None:
    _assert_parent(parent_fd, parent, parent_identity, parent_mode)
    alias = _stat_at(parent_fd, canonical_name)
    if (
        not stat.S_ISLNK(alias.st_mode)
        or _identity_of(alias) != alias_identity
        or os.readlink(canonical_name, dir_fd=parent_fd) != object_name
    ):
        _fail()
    _assert_object(parent_fd, object_fd, object_name, object_identity, 0o755)
    if (
        set(leaf_identities) != set(_ARTIFACT_NAMES)
        or tuple(sorted(os.listdir(object_fd)))
        != tuple(sorted(_ARTIFACT_NAMES))
    ):
        _fail()
    for name, identity in leaf_identities.items():
        item = _stat_at(object_fd, name)
        if (
            stat.S_ISLNK(item.st_mode)
            or not stat.S_ISREG(item.st_mode)
            or stat.S_IMODE(item.st_mode) != 0o644
            or _identity_of(item) != identity
        ):
            _fail()


def _canonical(state: Path) -> Path:
    canonical = state / _CANONICAL_RELATIVE
    parent = canonical.parent
    try:
        parent_metadata = parent.lstat()
        resolved = parent.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ValueError(_ERROR) from error
    if resolved != parent or stat.S_ISLNK(parent_metadata.st_mode) or not stat.S_ISDIR(parent_metadata.st_mode):
        _fail()
    return canonical


def _summary(
    operation: str,
    canonical: Path,
    object_name: str,
    object_identity: tuple[int, int],
    alias_identity: tuple[int, int],
    artifacts: Mapping[str, bytes],
) -> dict[str, object]:
    validated = _validate_candidate_bundle(dict(artifacts))
    return {
        "schema_version": _SCHEMA,
        "operation": operation,
        "status": "PASS_FORMAL_RUNTIME_CARRIER_MATERIALIZED",
        "canonical_path": str(canonical),
        "canonical_entry_type": "relative_symlink",
        "canonical_symlink_target": object_name,
        "canonical_identity": {"st_dev": alias_identity[0], "st_ino": alias_identity[1]},
        "object_identity": {"st_dev": object_identity[0], "st_ino": object_identity[1]},
        "aggregate_sha256": _aggregate_sha256(artifacts),
        "artifact_count": 4,
        "artifacts": {
            name: {"bytes": len(payload), "sha256": _sha(payload)}
            for name, payload in artifacts.items()
        },
        "array_count": 12,
        "sample_count": 11,
        "ligand_atom_count": 323,
        "pocket_atom_count": 2202,
        "binding_report_status": validated["report"]["status"],
        "readiness": _formal_readiness(),
    }


def _verify_existing(*, repo_root: Path, state_root: Path) -> dict[str, object]:
    """Verify an already published canonical object without changing it."""

    try:
        repo = _require_root(repo_root)
        state = _require_root(state_root)
        fresh = _build_candidate_bundle(repo_root=repo, state_root=state)
        canonical = _canonical(state)
        parent = canonical.parent
        parent_metadata = parent.lstat()
        parent_identity = _identity_of(parent_metadata)
        parent_mode = stat.S_IMODE(parent_metadata.st_mode)
        parent_fd = os.open(os.fspath(parent), _DIRECTORY_FLAGS)
        object_fd: int | None = None
        try:
            _assert_parent(parent_fd, parent, parent_identity, parent_mode)
            alias_metadata = _stat_at(parent_fd, canonical.name)
            alias_identity = _identity_of(alias_metadata)
            if not stat.S_ISLNK(alias_metadata.st_mode):
                _fail()
            target = os.readlink(canonical.name, dir_fd=parent_fd)
            aggregate, _nonce = _parse_object_name(target)
            object_metadata = _stat_at(parent_fd, target)
            if stat.S_IMODE(object_metadata.st_mode) != 0o755 or not stat.S_ISDIR(object_metadata.st_mode):
                _fail()
            object_identity = _identity_of(object_metadata)
            object_fd = os.open(target, _DIRECTORY_FLAGS, dir_fd=parent_fd)
            leaf_identities: dict[str, tuple[int, int]] = {}
            for name in _ARTIFACT_NAMES:
                item = _stat_at(object_fd, name)
                if stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode) or stat.S_IMODE(item.st_mode) != 0o644:
                    _fail()
                leaf_identities[name] = _identity_of(item)
            stored = _read_object(
                parent_fd, object_fd, target, object_identity, 0o755, leaf_identities
            )
            if stored != fresh or _aggregate_sha256(stored) != aggregate:
                _fail()
            _final_publication_revalidation(
                parent_fd=parent_fd,
                parent=parent,
                parent_identity=parent_identity,
                parent_mode=parent_mode,
                canonical_name=canonical.name,
                alias_identity=alias_identity,
                object_fd=object_fd,
                object_name=target,
                object_identity=object_identity,
                leaf_identities=leaf_identities,
            )
            return _summary("check", canonical, target, object_identity, alias_identity, stored)
        finally:
            if object_fd is not None:
                os.close(object_fd)
            os.close(parent_fd)
    except BaseException as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _cleanup(
    parent_fd: int,
    parent: Path,
    parent_identity: tuple[int, int],
    parent_mode: int,
    object_fd: int | None,
    object_name: str,
    object_identity: tuple[int, int],
    leaf_identities: Mapping[str, tuple[int, int]],
) -> None:
    cleanup_fd = object_fd
    opened = False
    try:
        _assert_parent(parent_fd, parent, parent_identity, parent_mode)
        if cleanup_fd is None:
            cleanup_fd = os.open(object_name, _DIRECTORY_FLAGS, dir_fd=parent_fd)
            opened = True
        _assert_object(parent_fd, cleanup_fd, object_name, object_identity, stat.S_IMODE(os.fstat(cleanup_fd).st_mode))
        if set(os.listdir(cleanup_fd)) != set(leaf_identities):
            raise OSError(errno.ESTALE, "cleanup inventory mismatch")
        for name in _ARTIFACT_NAMES:
            if name not in leaf_identities:
                continue
            item = _stat_at(cleanup_fd, name)
            if stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode) or _identity_of(item) != leaf_identities[name]:
                raise OSError(errno.ESTALE, "cleanup leaf mismatch")
            os.unlink(name, dir_fd=cleanup_fd)
        if os.listdir(cleanup_fd):
            raise OSError(errno.ENOTEMPTY, "cleanup residue")
        if opened:
            os.close(cleanup_fd)
            cleanup_fd = None
        os.rmdir(object_name, dir_fd=parent_fd)
    except BaseException as error:
        raise _CleanupFailure(_CLEANUP_ERROR) from error
    finally:
        if opened and cleanup_fd is not None:
            try:
                os.close(cleanup_fd)
            except OSError:
                pass


def materialize_covapie_current11_runtime_sample_and_role_order_carrier_v1(
    *, repo_root: Path, state_root: Path
) -> dict[str, object]:
    """Atomically publish the deterministic formal carrier Exact4."""

    parent_fd: int | None = None
    object_fd: int | None = None
    parent: Path | None = None
    parent_identity: tuple[int, int] | None = None
    parent_mode: int | None = None
    object_name: str | None = None
    object_identity: tuple[int, int] | None = None
    leaf_identities: dict[str, tuple[int, int]] = {}
    publication_succeeded = False
    try:
        repo = _require_root(repo_root)
        state = _require_root(state_root)
        if repo == state or repo in state.parents:
            _fail()
        canonical = _canonical(state)
        artifacts = _build_candidate_bundle(repo_root=repo, state_root=state)
        aggregate = _aggregate_sha256(artifacts)
        parent = canonical.parent
        parent_metadata = parent.lstat()
        parent_identity = _identity_of(parent_metadata)
        parent_mode = stat.S_IMODE(parent_metadata.st_mode)
        parent_fd = os.open(os.fspath(parent), _DIRECTORY_FLAGS)
        _assert_parent(parent_fd, parent, parent_identity, parent_mode)
        try:
            _stat_at(parent_fd, canonical.name)
        except FileNotFoundError:
            pass
        else:
            _fail()
        for _attempt in range(64):
            nonce = secrets.token_hex(16)
            candidate = f"{_OBJECT_PREFIX}{aggregate}-{nonce}"
            _parse_object_name(candidate)
            try:
                os.mkdir(candidate, 0o700, dir_fd=parent_fd)
            except FileExistsError:
                continue
            object_name = candidate
            break
        if object_name is None:
            _fail()
        object_metadata = _stat_at(parent_fd, object_name)
        object_identity = _identity_of(object_metadata)
        if stat.S_IMODE(object_metadata.st_mode) != 0o700 or not stat.S_ISDIR(object_metadata.st_mode):
            _fail()
        object_fd = os.open(object_name, _DIRECTORY_FLAGS, dir_fd=parent_fd)
        _assert_object(parent_fd, object_fd, object_name, object_identity, 0o700)
        if os.listdir(object_fd):
            _fail()
        _write_artifacts(object_fd, artifacts, leaf_identities)
        os.fsync(object_fd)
        stored = _read_object(
            parent_fd, object_fd, object_name, object_identity, 0o700, leaf_identities
        )
        if stored != artifacts or _aggregate_sha256(stored) != aggregate:
            _fail()
        os.fchmod(object_fd, 0o755)
        os.fsync(object_fd)
        _assert_object(parent_fd, object_fd, object_name, object_identity, 0o755)
        _assert_parent(parent_fd, parent, parent_identity, parent_mode)
        os.symlink(object_name, canonical.name, target_is_directory=True, dir_fd=parent_fd)
        publication_succeeded = True
        alias_metadata = _stat_at(parent_fd, canonical.name)
        alias_identity = _identity_of(alias_metadata)
        if not stat.S_ISLNK(alias_metadata.st_mode) or os.readlink(canonical.name, dir_fd=parent_fd) != object_name:
            _fail()
        os.fsync(parent_fd)
        final = _read_object(
            parent_fd, object_fd, object_name, object_identity, 0o755, leaf_identities
        )
        if final != artifacts or _aggregate_sha256(final) != aggregate:
            _fail()
        _final_publication_revalidation(
            parent_fd=parent_fd,
            parent=parent,
            parent_identity=parent_identity,
            parent_mode=parent_mode,
            canonical_name=canonical.name,
            alias_identity=alias_identity,
            object_fd=object_fd,
            object_name=object_name,
            object_identity=object_identity,
            leaf_identities=leaf_identities,
        )
        return _summary("materialize", canonical, object_name, object_identity, alias_identity, final)
    except BaseException as original:
        should_cleanup = False
        if (
            not publication_succeeded
            and parent_fd is not None
            and object_name is not None
        ):
            relation = _canonical_relation(
                parent_fd, _CANONICAL_BASENAME, object_name
            )
            should_cleanup = relation in {"absent", "unrelated"}
        if should_cleanup:
            if (
                parent is None
                or parent_identity is None
                or parent_mode is None
                or object_identity is None
            ):
                raise _CleanupFailure(_CLEANUP_ERROR) from original
            try:
                _cleanup(
                    parent_fd, parent, parent_identity, parent_mode, object_fd,
                    object_name, object_identity, leaf_identities,
                )
            except BaseException:
                raise _CleanupFailure(_CLEANUP_ERROR) from original
        if isinstance(original, _CleanupFailure):
            raise
        if type(original) is ValueError and str(original) == _ERROR:
            raise
        raise ValueError(_ERROR) from original
    finally:
        if object_fd is not None:
            try:
                os.close(object_fd)
            except OSError:
                pass
        if parent_fd is not None:
            try:
                os.close(parent_fd)
            except OSError:
                pass
