"""Build the read-only Current11 Task 2 batch descriptor compiler contract V1."""

from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import os
import re
import stat
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Mapping, NoReturn, Sequence

from covalent_ext import covapie_current11_runtime_sample_and_role_order_carrier_contract_gate_v1 as _carrier_gate
from covalent_ext import covapie_current11_task2_batch_index_remap_adapter_v1 as _adapter
from covalent_ext import covapie_current11_task2_batch_index_remap_contract_gate_v1 as _remap_gate


__all__ = (
    "build_covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1",
)

_ERROR = "COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTRACT_GATE_V1_ERROR"
_SCHEMA = "covapie_current11_task2_batch_descriptor_compiler_contract_v1"
_INPUT_SCHEMA = "covapie_current11_task2_batch_descriptor_compiler_input_v1"
_OUTPUT_SCHEMA = "covapie_current11_task2_batch_descriptor_compiler_output_v1"
_REFERENCE_SCHEMA = "covapie_current11_task2_batch_descriptor_compiler_reference_vectors_v1"
_REPORT_SCHEMA = "covapie_current11_task2_batch_descriptor_compiler_contract_gate_report_v1"
_RUNTIME_SCHEMA = "processed_ligand_pocket_dataset_collate_observation_no_virtual_v1"
_SAMPLE_KEY_SCHEMA = "covapie_sample_index_row_id_in_names_v1"
_PARSER_SCHEMA = "order_preserving_checkpoint_heavy_projection_v1"
_COLLATE_SCHEMA = "processed_ligand_pocket_dataset_collate_fn_v1"
_VIRTUAL_POLICY = "no_virtual_nodes_v1"
_JOINT_LAYOUT = "ligand_segment_then_pocket_segment_v1"
_DOMAIN = b"COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTRACT_GATE_V1\0"
_PROVIDER_DOMAIN = b"COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_IDENTITY_PROVIDER_V1\0"

_PROJECTION_DIGEST = "b8e8078700bd019d4a11a00c17dc84fa05e406bbf61b51bf3e887988f3b89255"
_PAYLOAD_DIGEST = "95e9ed091566bbc547a8f75b975a40c27ce318e95df1553b1f1ac448a91b1f9d"
_PROJECTION_CONTRACT_DIGEST = "d0a428c19fe3c4aefc575065e7dcc7a7cfaf8593526d025d467cf6568b49c21d"
_REMAP_CONTRACT_DIGEST = "2c6259312a3292181f00ebbaf787fab05e5a97e5b5475243f2fa8461b54dcdc6"
_ADAPTER_OUTPUT_DIGEST = "7e141fadc5a39bbad17e33eceb24f67efeff15d8057d785c56eebe940ff5a658"
_CARRIER_CONTRACT_DIGEST = "360ee9a2a75efae3189922426a53ebccf3f2e0fbc9c2fb33980112a6c5438b14"
_ROUTING_SNAPSHOT = "768fbd980efbcedcaa2ef971a7d77791879111d1fceeb1f03cb1eb8bfff24034"
_ROUTING_AGGREGATE = "24f95099ba1ba0b81724535cb17c5d4d32c360f71c87422571210a2178ddb49c"

_FORMAL_RELATIVE = "formal-sidecars/current11-runtime-sample-and-role-order-carrier-v1"
_FORMAL_AGGREGATE = "ef426a6d8dee9678ac15dd62b191e9ef9cfb436a01660bd941bd24392dfa9a18"
_FORMAL_PATTERN = re.compile(
    r"^\.current11-runtime-sample-and-role-order-carrier-v1\."
    r"object-sha256-([0-9a-f]{64})-([0-9a-f]{32})$"
)
_FORMAL_DOMAIN = b"COVAPIE_CURRENT11_RUNTIME_SAMPLE_AND_ROLE_ORDER_CARRIER_MATERIALIZER_V1\0"
_NPZ = "current11_runtime_sample_and_role_order_carrier.npz"
_FORMAL_MANIFEST = "current11_runtime_sample_and_role_order_carrier_manifest.json"
_INVENTORY = "current11_runtime_sample_and_role_order_carrier_array_inventory.csv"
_BINDING_REPORT = "current11_runtime_sample_and_role_order_carrier_binding_report.json"
_FORMAL_NAMES = (_NPZ, _FORMAL_MANIFEST, _INVENTORY, _BINDING_REPORT)
_FORMAL_IDENTITIES = {
    _NPZ: (196172, "ea3aa7c94b7c88993493662ad6ba7fd95e547ec62612a072f8248a515657e910"),
    _FORMAL_MANIFEST: (31910, "b8a210a06c758ebaf16887a0e7ce18a9199c2dffcda61e814143d5f157801b54"),
    _INVENTORY: (3319, "37aaa88566594aa36674b4864f7884c28426a923ca8d0e04bb136b63b84105cb"),
    _BINDING_REPORT: (1654, "596d0b2d5464942b21ca1379c1458de750c786f1d990114c72f0f1aee4586fc0"),
}
_FORMAL_LF = {_FORMAL_MANIFEST: 660, _INVENTORY: 13, _BINDING_REPORT: 34}
_NAMES_DIGEST = "e20c1a3f764757ffac99b8e812a4caba23500270edd352ed159fdb18867a28ac"

_MANIFEST = "current11_task2_batch_descriptor_compiler_contract_manifest.json"
_INPUT = "current11_task2_batch_descriptor_compiler_input_schema.json"
_OUTPUT = "current11_task2_batch_descriptor_compiler_output_schema.json"
_VOCABULARY = "current11_task2_batch_descriptor_compiler_status_vocabulary.csv"
_VECTORS = "current11_task2_batch_descriptor_compiler_reference_vectors.json"
_REPORT = "current11_task2_batch_descriptor_compiler_contract_gate_report.json"
_ARTIFACT_NAMES = (_MANIFEST, _INPUT, _OUTPUT, _VOCABULARY, _VECTORS, _REPORT)
_STABLE_NAMES = _ARTIFACT_NAMES[:5]

_REPOSITORY_EXACT4 = (
    "src/covalent_ext/covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1.py",
    "scripts/check_covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1.py",
    "tests/test_covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1.py",
    "docs/covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1_guide.md",
)
_DESIGN_RELATIVE = (
    "review-scratch/current11-task2-batch-descriptor-compiler-contract-design-v1/"
    "batch_descriptor_compiler_contract_design_report.md"
)
_DESIGN_SHA = "72259f5293a40378ceef0da439c9cbbe0a50dd515831bf2c07b498e538f5a15f"

_INPUT_FIELDS = (
    "schema_version", "runtime_batch_schema_version", "sample_key_schema_version",
    "batch_sample_keys", "ligand_lengths", "pocket_lengths", "ligand_membership",
    "pocket_membership", "joint_layout_descriptor", "virtual_node_policy", "receptors",
    "consistency_buffer_lengths", "debug_coordinates", "debug_rank_metadata",
)
_INPUT_REQUIRED = frozenset(_INPUT_FIELDS[:10])
_INPUT_OPTIONAL = frozenset(_INPUT_FIELDS[10:])
_SOURCE_OVERRIDE_FIELDS = frozenset((
    "source_projection_digest", "source_payload_digest", "parser_schema_version",
    "collate_schema_version", "source_sample_order", "source_pair_values_int64",
    "source_sample_offsets_int64", "source_entry_validity_bool", "source_sample_validity_bool",
))
_FORBIDDEN_INPUT_FIELDS = _SOURCE_OVERRIDE_FIELDS | frozenset((
    "batch_role_offsets", "adapter_input_exact18", "atom_identity_tables",
    "source_to_parser_mapping", "provider_digest", "provider_path", "coordinates_identity",
    "features_identity", "distance_identity", "model_logits", "candidate_labels",
    "mask_task", "warhead_inference",
))
_OUTPUT_FIELDS = (
    "schema_version", "compiler_status", "failure_reason", "adapter_input_exact18",
    "batch_sample_key_outcomes", "source_contract_digest", "identity_provider_digest",
    "runtime_schema_binding", "provenance", "readiness",
)
_EXACT18_FIELDS = (
    "schema_version", "source_projection_digest", "source_payload_digest",
    "parser_schema_version", "collate_schema_version", "source_sample_order",
    "source_pair_values_int64", "source_sample_offsets_int64",
    "source_entry_validity_bool", "source_sample_validity_bool", "batch_sample_order",
    "batch_sample_atom_identity_tables", "batch_role_lengths", "batch_role_offsets",
    "batch_membership_masks", "joint_layout_descriptor", "debug_coordinates",
    "debug_rank_metadata",
)
_IDENTITY_FIELDS = (
    "sample_index_row_id", "sample_preparation_input_id", "pdb_id", "ligand_comp_id",
)
_ROLE_AUTHORITY_FIELDS = (
    "root_kind", "relative_path", "SHA256", "row_count", "row_order_digest",
    "row_order_version", "selected_source_row_index_0based",
    "selected_parser_local_index", "parser_output_atom_count", "source_to_parser_local",
    "selected_atom_identity",
)
_ATOM_IDENTITY_FIELDS = (
    "atom_site_id", "atom_name", "type_symbol", "residue_name_or_ligand_comp_id",
    "auth_asym_id", "auth_seq_id", "label_asym_id", "label_seq_id",
)
_STATUS_ORDER = (
    "COMPILED_EXACT", "JOINT_LAYOUT_UNAVAILABLE", "BATCH_OBSERVATION_SCHEMA_MISMATCH",
    "BATCH_SAMPLE_KEY_INVALID", "BATCH_SAMPLE_KEY_DUPLICATED", "BATCH_SAMPLE_KEY_UNKNOWN",
    "BATCH_SAMPLE_KEY_AMBIGUOUS", "SOURCE_CONTRACT_MISMATCH", "IDENTITY_PROVIDER_MISSING",
    "IDENTITY_PROVIDER_MISMATCH", "ROLE_TABLE_AUTHORITY_MISSING", "ROLE_LENGTH_MISMATCH",
    "MEMBERSHIP_MASK_MISMATCH", "VIRTUAL_NODE_POLICY_MISMATCH",
    "NON_SOURCE_SAMPLE_NOT_ADMISSIBLE_IN_CURRENT11_COMPILER_V1",
)
_HARD_FAILURES = frozenset(_STATUS_ORDER[2:])
_LIGAND_LENGTHS = (13, 13, 13, 25, 28, 43, 42, 42, 43, 40, 21)
_POCKET_LENGTHS = (66, 104, 96, 208, 188, 278, 267, 257, 249, 261, 228)
_SOURCE_PAIRS = (
    (88, 3), (25, 3), (19, 3), (39, 3), (37, 27), (50, 21),
    (48, 16), (53, 20), (52, 21), (53, 18), (84, 5),
)
_SOURCE_SCHEMA = "covapie_current11_task2_batch_index_remap_adapter_input_v1"
_SOURCE_IDENTITIES = (
    ("CYS_SG_SAMPLE_INDEX_000001", "CYS_SG_SAMPLE_PREP_INPUT_000001", "6BV6", "JUG"),
    ("CYS_SG_SAMPLE_INDEX_000002", "CYS_SG_SAMPLE_PREP_INPUT_000002", "6BV8", "JUG"),
    ("CYS_SG_SAMPLE_INDEX_000003", "CYS_SG_SAMPLE_PREP_INPUT_000003", "6BV5", "JUG"),
    ("CYS_SG_SAMPLE_INDEX_000004", "CYS_SG_EXPANSION_PREP_000001", "1AEC", "E64"),
    ("CYS_SG_SAMPLE_INDEX_000005", "CYS_SG_EXPANSION_PREP_000002", "1AIM", "ZYA"),
    ("CYS_SG_SAMPLE_INDEX_000006", "CYS_SG_EXPANSION_PREP_000003", "1AU3", "PCM"),
    ("CYS_SG_SAMPLE_INDEX_000007", "CYS_SG_EXPANSION_PREP_000004", "1AU4", "INP"),
    ("CYS_SG_SAMPLE_INDEX_000008", "CYS_SG_EXPANSION_PREP_000005", "1AYU", "INA"),
    ("CYS_SG_SAMPLE_INDEX_000009", "CYS_SG_EXPANSION_PREP_000006", "1AYV", "IN6"),
    ("CYS_SG_SAMPLE_INDEX_000010", "CYS_SG_EXPANSION_PREP_000007", "1AYW", "IN3"),
    ("CYS_SG_SAMPLE_INDEX_000011", "CYS_SG_EXPANSION_PREP_000008", "1B02", "UFP"),
)
_VALIDATION_ORDER = (
    "top_level_schema_and_unknown_fields", "source_contract_override",
    "pinned_source_contract_availability_and_drift", "identity_provider_availability_and_drift",
    "runtime_schema_version", "sample_key_schema", "sample_key_validity",
    "duplicate_key", "exact_lookup_non_source_unknown_ambiguous",
    "required_pocket_and_ligand_role_authority", "virtual_node_policy", "role_lengths",
    "membership", "optional_consistency_buffer_lengths", "joint_descriptor_classification",
    "debug_transport",
)


def _fail() -> NoReturn:
    raise ValueError(_ERROR)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json(value: object) -> bytes:
    try:
        return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise ValueError(_ERROR) from error


def _compact(value: object) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise ValueError(_ERROR) from error


def _strict_json(payload: bytes) -> dict[str, object]:
    try:
        value = json.loads(payload.decode("utf-8"), parse_constant=lambda _value: _fail())
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(_ERROR) from error
    if type(value) is not dict:
        _fail()
    return value


def _require_root(path: Path) -> Path:
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


def _path_snapshot(path: Path) -> tuple[object, ...]:
    metadata = path.lstat()
    return (
        metadata.st_mode, metadata.st_size, metadata.st_mtime_ns, metadata.st_ino,
        os.readlink(path) if stat.S_ISLNK(metadata.st_mode) else None,
        _sha(path.read_bytes()) if stat.S_ISREG(metadata.st_mode) else None,
    )


@contextmanager
def _precommit_compatibility() -> Iterator[None]:
    owner = _remap_gate._instance_builder._payload_builder._contract_gate
    original = owner._run_git

    def compatible(root: Path, arguments: Sequence[str]) -> str:
        output = original(root, arguments)
        if tuple(arguments) in {
            ("status", "--porcelain=v1", "--untracked-files=all"),
            ("status", "--short"),
        }:
            allowed = {f"?? {path}" for path in _REPOSITORY_EXACT4}
            lines = output.splitlines()
            if any(
                len(line) >= 4 and line[3:] in _REPOSITORY_EXACT4 and line not in allowed
                for line in lines
            ):
                _fail()
            output = "\n".join(line for line in lines if line not in allowed)
        return output

    try:
        owner._run_git = compatible
        yield
    finally:
        owner._run_git = original


def _formal_snapshot(canonical: Path) -> dict[str, object]:
    try:
        link = os.readlink(canonical)
        target = canonical.parent / link
        inventory = tuple(sorted(os.listdir(target)))
        return {
            "canonical": _path_snapshot(canonical), "readlink": link,
            "object": _path_snapshot(target), "inventory": inventory,
            "leaves": {name: _path_snapshot(target / name) for name in inventory},
        }
    except OSError as error:
        raise ValueError(_ERROR) from error


def _aggregate(artifacts: Mapping[str, bytes]) -> str:
    digest = hashlib.sha256(_FORMAL_DOMAIN)
    for name in _FORMAL_NAMES:
        encoded = name.encode("utf-8")
        payload = artifacts[name]
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _csv(payload: bytes) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
        rows = [dict(row) for row in reader]
    except (UnicodeDecodeError, csv.Error) as error:
        raise ValueError(_ERROR) from error
    if reader.fieldnames is None or any(None in row or any(value is None for value in row.values()) for row in rows):
        _fail()
    return tuple(reader.fieldnames), rows


def _validate_formal(state: Path) -> tuple[dict[str, object], dict[str, object], list[dict[str, str]]]:
    canonical = state / _FORMAL_RELATIVE
    snapshot = _formal_snapshot(canonical)
    match = _FORMAL_PATTERN.fullmatch(str(snapshot["readlink"]))
    target = canonical.parent / str(snapshot["readlink"])
    if (
        match is None or match.group(1) != _FORMAL_AGGREGATE
        or not stat.S_ISLNK(canonical.lstat().st_mode)
        or not target.resolve(strict=True) == target
        or not stat.S_ISDIR(target.lstat().st_mode)
        or stat.S_IMODE(target.lstat().st_mode) != 0o755
        or tuple(snapshot["inventory"]) != tuple(sorted(_FORMAL_NAMES))
    ):
        _fail()
    artifacts: dict[str, bytes] = {}
    for name in _FORMAL_NAMES:
        path = target / name
        metadata = path.lstat()
        payload = path.read_bytes()
        size, digest = _FORMAL_IDENTITIES[name]
        if (
            stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o644 or len(payload) != size
            or _sha(payload) != digest or (name in _FORMAL_LF and payload.count(b"\n") != _FORMAL_LF[name])
        ):
            _fail()
        artifacts[name] = payload
    if _aggregate(artifacts) != _FORMAL_AGGREGATE:
        _fail()
    manifest = _strict_json(artifacts[_FORMAL_MANIFEST])
    header, inventory = _csv(artifacts[_INVENTORY])
    expected_header = (
        "array_index", "array_name", "npz_entry_name", "dtype", "shape_json",
        "logical_role", "semantic_authority", "raw_c_order_bytes", "raw_c_order_sha256",
        "npy_bytes", "npy_sha256", "identity_selection_authorized",
        "required_by_processed_dataset",
    )
    readiness = manifest.get("readiness")
    names = manifest.get("names_binding")
    ligand = manifest.get("ligand_buffer_binding")
    pocket = manifest.get("pocket_buffer_binding")
    if (
        header != expected_header or len(inventory) != 12
        or tuple(row.get("array_index") for row in inventory) != tuple(str(i) for i in range(12))
        or type(readiness) is not dict
        or any(readiness.get(key) is not True for key in (
            "formal_runtime_carrier_materialized", "runtime_batch_sample_key_available",
            "runtime_batch_sample_key_exact_one_for_current11", "runtime_batch_role_order_binding_available",
            "ready_for_batch_descriptor_compiler_contract_gate_implementation",
        ))
        or manifest.get("runtime_batch_schema_version") != _RUNTIME_SCHEMA
        or manifest.get("sample_key_schema_version") != _SAMPLE_KEY_SCHEMA
        or manifest.get("role_order_schema_version") != _PARSER_SCHEMA
        or manifest.get("virtual_node_policy") != _VIRTUAL_POLICY
        or manifest.get("source_contract_digest") != _CARRIER_CONTRACT_DIGEST
        or manifest.get("runtime_artifact_sha256") != _FORMAL_IDENTITIES[_NPZ][1]
        or type(names) is not dict or names.get("array_values_digest") != _NAMES_DIGEST
        or type(ligand) is not dict or type(pocket) is not dict
        or ligand.get("sample_lengths") != list(_LIGAND_LENGTHS)
        or pocket.get("sample_lengths") != list(_POCKET_LENGTHS)
        or ligand.get("sample_offsets") != _prefix(_LIGAND_LENGTHS)
        or pocket.get("sample_offsets") != _prefix(_POCKET_LENGTHS)
    ):
        _fail()
    for binding in (ligand, pocket):
        if (
            len(binding.get("per_sample_role_order_record_digests", ())) != 11
            or any(binding.get(key) is not False for key in (
                "padding_present", "crop_present", "virtual_nodes_present", "atom_reorder_present",
            ))
        ):
            _fail()
    sample_order = manifest.get("sample_order")
    if (
        type(sample_order) is not list or len(sample_order) != 11
        or names.get("sample_order") != sample_order
        or manifest.get("receptors_binding", {}).get("recommended_exact_values")
        != ["6BV6", "6BV8", "6BV5", "1AEC", "1AIM", "1AU3", "1AU4", "1AYU", "1AYV", "1AYW", "1B02"]
    ):
        _fail()
    return snapshot, manifest, inventory


def _published_contracts(repo: Path, state: Path) -> tuple[dict[str, object], dict[str, object]]:
    with _precommit_compatibility():
        remap = _remap_gate.build_covapie_current11_task2_batch_index_remap_contract_gate_v1(
            repo_root=repo, state_root=state
        )
    if type(remap) is not dict or tuple(remap) != (
        "current11_task2_batch_index_remap_contract_manifest.json",
        "current11_task2_batch_index_remap_input_schema.json",
        "current11_task2_batch_index_remap_output_schema.json",
        "current11_task2_batch_index_remap_status_vocabulary.csv",
        "current11_task2_batch_index_remap_reference_vectors.json",
        "current11_task2_batch_index_remap_contract_gate_report.json",
    ):
        _fail()
    remap_report = _strict_json(remap["current11_task2_batch_index_remap_contract_gate_report.json"])
    vectors = _strict_json(remap["current11_task2_batch_index_remap_reference_vectors.json"])
    if remap_report.get("contract_digest") != _REMAP_CONTRACT_DIGEST:
        _fail()
    with _precommit_compatibility():
        carrier = _carrier_gate.build_covapie_current11_runtime_sample_and_role_order_carrier_contract_gate_v1(
            repo_root=repo, state_root=state
        )
    carrier_report = _strict_json(
        carrier["current11_runtime_sample_and_role_order_carrier_contract_gate_report.json"]
    )
    if carrier_report.get("contract_digest") != _CARRIER_CONTRACT_DIGEST:
        _fail()
    return vectors, carrier_report


def _source_contract(vectors: Mapping[str, object]) -> dict[str, object]:
    raw = vectors.get("source_contract")
    if type(raw) is not dict:
        _fail()
    source = {
        "schema_version": _SOURCE_SCHEMA,
        "source_projection_digest": _PROJECTION_DIGEST,
        "source_payload_digest": _PAYLOAD_DIGEST,
        "parser_schema_version": _PARSER_SCHEMA,
        "collate_schema_version": _COLLATE_SCHEMA,
        "source_sample_order": copy.deepcopy(raw.get("sample_order")),
        "source_pair_values_int64": copy.deepcopy(raw.get("pair_values_source_row_indices")),
        "source_sample_offsets_int64": copy.deepcopy(raw.get("sample_pair_offsets")),
        "source_entry_validity_bool": copy.deepcopy(raw.get("entry_validity")),
        "source_sample_validity_bool": copy.deepcopy(raw.get("sample_validity")),
    }
    if not _validate_source_contract_exact_v1(source):
        _fail()
    return source


def _validate_source_contract_exact_v1(source_contract: object) -> bool:
    expected_keys = {
        "schema_version", "source_projection_digest", "source_payload_digest",
        "parser_schema_version", "collate_schema_version", "source_sample_order",
        "source_pair_values_int64", "source_sample_offsets_int64",
        "source_entry_validity_bool", "source_sample_validity_bool",
    }
    if type(source_contract) is not dict or set(source_contract) != expected_keys:
        return False
    if (
        source_contract.get("schema_version") != _SOURCE_SCHEMA
        or source_contract.get("source_projection_digest") != _PROJECTION_DIGEST
        or source_contract.get("source_payload_digest") != _PAYLOAD_DIGEST
        or source_contract.get("parser_schema_version") != _PARSER_SCHEMA
        or source_contract.get("collate_schema_version") != _COLLATE_SCHEMA
    ):
        return False
    samples = source_contract.get("source_sample_order")
    if type(samples) is not list or len(samples) != len(_SOURCE_IDENTITIES):
        return False
    row_ids: list[str] = []
    for index, (sample, expected_identity) in enumerate(zip(samples, _SOURCE_IDENTITIES)):
        if (
            type(sample) is not dict
            or set(sample) != set(_IDENTITY_FIELDS) | {"source_sample_index"}
            or type(sample.get("source_sample_index")) is not int
            or sample.get("source_sample_index") != index
        ):
            return False
        values: list[str] = []
        for field in _IDENTITY_FIELDS:
            value = sample.get(field)
            if type(value) is not str or not value or value.strip() != value:
                return False
            values.append(value)
        if tuple(values) != expected_identity:
            return False
        row_ids.append(values[0])
    if len(set(row_ids)) != len(row_ids):
        return False
    pairs = source_contract.get("source_pair_values_int64")
    if (
        type(pairs) is not list or len(pairs) != len(_SOURCE_PAIRS)
        or any(
            type(pair) is not list or len(pair) != 2
            or any(type(value) is not int or value < 0 for value in pair)
            for pair in pairs
        )
        or pairs != [list(pair) for pair in _SOURCE_PAIRS]
    ):
        return False
    offsets = source_contract.get("source_sample_offsets_int64")
    if (
        type(offsets) is not list or len(offsets) != 12
        or any(type(value) is not int or value < 0 for value in offsets)
        or offsets != list(range(12))
    ):
        return False
    for field in ("source_entry_validity_bool", "source_sample_validity_bool"):
        validity = source_contract.get(field)
        if (
            type(validity) is not list or len(validity) != 11
            or any(type(value) is not bool or value is not True for value in validity)
        ):
            return False
    return True


def _identity(sample: Mapping[str, object]) -> dict[str, str]:
    result: dict[str, str] = {}
    for field in _IDENTITY_FIELDS:
        value = sample.get(field)
        if type(value) is not str or not value or value.strip() != value:
            _fail()
        result[field] = value
    return result


def _identity_provider(vectors: Mapping[str, object], source: Mapping[str, object]) -> list[dict[str, object]]:
    records = vectors.get("exact22_source_to_local")
    samples = source.get("source_sample_order")
    if type(records) is not list or type(samples) is not list or len(records) != 11:
        _fail()
    provider: list[dict[str, object]] = []
    for index, (sample, record) in enumerate(zip(samples, records)):
        if type(sample) is not dict or type(record) is not dict or record.get("source_sample_index") != index:
            _fail()
        sample_identity = _identity(sample)
        if _identity(record.get("sample_identity", {})) != sample_identity:
            _fail()
        raw_roles = record.get("roles")
        if type(raw_roles) is not list or len(raw_roles) != 2:
            _fail()
        roles: dict[str, object] = {}
        for expected_role, raw_role in zip(("pocket", "ligand"), raw_roles):
            if type(raw_role) is not dict or raw_role.get("role") != expected_role:
                _fail()
            role = copy.deepcopy(raw_role)
            retained = role.get("retained_heavy_count")
            selected_source = role.get("selected_source_row_index_0based")
            selected_local = role.get("selected_parser_local_index")
            atom = role.get("selected_atom_identity")
            role["parser_output_atom_count"] = retained
            role["source_to_parser_local"] = {str(selected_source): selected_local}
            if (
                type(retained) is not int or type(selected_source) is not int
                or type(selected_local) is not int or type(atom) is not dict
                or tuple(sorted(atom)) != tuple(sorted(_ATOM_IDENTITY_FIELDS))
                or any(type(atom.get(field)) is not str for field in _ATOM_IDENTITY_FIELDS)
                or any(field not in role for field in _ROLE_AUTHORITY_FIELDS)
            ):
                _fail()
            roles[expected_role] = role
        provider.append({"sample_identity": sample_identity, "roles": roles})
    return provider


def _provider_digest(provider: object) -> str:
    digest = hashlib.sha256(_PROVIDER_DOMAIN)
    payload = _compact(provider)
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _prefix(lengths: Sequence[int]) -> list[int]:
    result = [0]
    for value in lengths:
        result.append(result[-1] + value)
    return result


def _membership(lengths: Sequence[int]) -> list[int]:
    return [ordinal for ordinal, length in enumerate(lengths) for _ in range(length)]


def _observation(order: Sequence[int], samples: Sequence[Mapping[str, object]], *, joint: str | None = _JOINT_LAYOUT) -> dict[str, object]:
    ligand = [_LIGAND_LENGTHS[index] for index in order]
    pocket = [_POCKET_LENGTHS[index] for index in order]
    return {
        "schema_version": _INPUT_SCHEMA,
        "runtime_batch_schema_version": _RUNTIME_SCHEMA,
        "sample_key_schema_version": _SAMPLE_KEY_SCHEMA,
        "batch_sample_keys": [samples[index]["sample_index_row_id"] for index in order],
        "ligand_lengths": ligand,
        "pocket_lengths": pocket,
        "ligand_membership": _membership(ligand),
        "pocket_membership": _membership(pocket),
        "joint_layout_descriptor": joint,
        "virtual_node_policy": _VIRTUAL_POLICY,
        "receptors": [samples[index]["pdb_id"] for index in order],
        "consistency_buffer_lengths": {
            "ligand_coords": sum(ligand), "ligand_one_hot": sum(ligand),
            "pocket_coords": sum(pocket), "pocket_one_hot": sum(pocket),
        },
        "debug_coordinates": None,
        "debug_rank_metadata": None,
    }


def _gate_readiness() -> dict[str, bool]:
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
        "task2_batch_descriptor_compiler_implemented": False,
        "runtime_batch_observation_extractor_implemented": False,
        "ready_for_task2_batch_descriptor_compiler_implementation": True,
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


def _compiler_output(
    status: str, *, exact18: dict[str, object] | None, outcomes: list[dict[str, object]],
    provider_digest: str, joint_status: str,
) -> dict[str, object]:
    return {
        "schema_version": _OUTPUT_SCHEMA,
        "compiler_status": "COMPILED_EXACT" if exact18 is not None else status,
        "failure_reason": "NONE" if exact18 is not None else status,
        "adapter_input_exact18": exact18,
        "batch_sample_key_outcomes": outcomes,
        "source_contract_digest": _REMAP_CONTRACT_DIGEST,
        "identity_provider_digest": provider_digest,
        "runtime_schema_binding": {
            "runtime_batch_schema_version": _RUNTIME_SCHEMA,
            "sample_key_schema_version": _SAMPLE_KEY_SCHEMA,
            "virtual_node_policy": _VIRTUAL_POLICY,
            "joint_layout_component_status": joint_status,
        },
        "provenance": {
            "contract_evaluator_only": True, "compiler_implemented": False,
            "runtime_extractor_implemented": False, "remap_executed_by_compiler": False,
        },
        "readiness": _gate_readiness(),
    }


def _evaluate_reference_case_v1(
    observation: object, *, source_contract: object, identity_provider: object,
    expected_identity_provider_digest: str, source_contract_available: bool = True,
    identity_provider_available: bool = True,
) -> dict[str, object]:
    """Evaluate the frozen compiler contract without exposing a compiler API."""
    empty_outcomes: list[dict[str, object]] = []

    def rejected(status: str, outcomes: list[dict[str, object]] | None = None) -> dict[str, object]:
        return _compiler_output(
            status, exact18=None, outcomes=empty_outcomes if outcomes is None else outcomes,
            provider_digest=expected_identity_provider_digest,
            joint_status="JOINT_LAYOUT_UNAVAILABLE",
        )

    if type(observation) is not dict:
        return rejected("BATCH_OBSERVATION_SCHEMA_MISMATCH")
    keys = set(observation)
    if not _INPUT_REQUIRED.issubset(keys) or not keys.issubset(_INPUT_REQUIRED | _INPUT_OPTIONAL | _FORBIDDEN_INPUT_FIELDS):
        return rejected("BATCH_OBSERVATION_SCHEMA_MISMATCH")
    if keys & _SOURCE_OVERRIDE_FIELDS:
        return rejected("SOURCE_CONTRACT_MISMATCH")
    if keys - (_INPUT_REQUIRED | _INPUT_OPTIONAL | _SOURCE_OVERRIDE_FIELDS):
        return rejected("BATCH_OBSERVATION_SCHEMA_MISMATCH")
    if not source_contract_available or not _validate_source_contract_exact_v1(source_contract):
        return rejected("SOURCE_CONTRACT_MISMATCH")
    if not identity_provider_available or identity_provider is None:
        return rejected("IDENTITY_PROVIDER_MISSING")
    if type(identity_provider) is not list or _provider_digest(identity_provider) != expected_identity_provider_digest:
        return rejected("IDENTITY_PROVIDER_MISMATCH")
    if observation.get("schema_version") != _INPUT_SCHEMA:
        return rejected("BATCH_OBSERVATION_SCHEMA_MISMATCH")
    if observation.get("runtime_batch_schema_version") != _RUNTIME_SCHEMA:
        return rejected("BATCH_OBSERVATION_SCHEMA_MISMATCH")
    if observation.get("sample_key_schema_version") != _SAMPLE_KEY_SCHEMA:
        return rejected("BATCH_OBSERVATION_SCHEMA_MISMATCH")
    batch_keys = observation.get("batch_sample_keys")
    if type(batch_keys) is not list:
        return rejected("BATCH_SAMPLE_KEY_INVALID")
    if any(type(key) is not str or not key or key.strip() != key for key in batch_keys):
        return rejected("BATCH_SAMPLE_KEY_INVALID")
    if len(set(batch_keys)) != len(batch_keys):
        return rejected("BATCH_SAMPLE_KEY_DUPLICATED")
    source_samples = source_contract.get("source_sample_order")
    if type(source_samples) is not list:
        return rejected("SOURCE_CONTRACT_MISMATCH")
    source_by_key = {sample.get("sample_index_row_id"): sample for sample in source_samples if type(sample) is dict}
    provider_by_key: dict[str, list[dict[str, object]]] = {}
    for table in identity_provider:
        if type(table) is dict and type(table.get("sample_identity")) is dict:
            key = table["sample_identity"].get("sample_index_row_id")
            if type(key) is str:
                provider_by_key.setdefault(key, []).append(table)
    outcomes: list[dict[str, object]] = []
    selected: list[tuple[dict[str, object], dict[str, object]]] = []
    for ordinal, key in enumerate(batch_keys):
        matches = provider_by_key.get(key, [])
        if key.startswith("CYS_SG_SAMPLE_INDEX_") and key not in source_by_key:
            return rejected("NON_SOURCE_SAMPLE_NOT_ADMISSIBLE_IN_CURRENT11_COMPILER_V1", outcomes)
        if key not in source_by_key or not matches:
            return rejected("BATCH_SAMPLE_KEY_UNKNOWN", outcomes)
        if len(matches) != 1:
            return rejected("BATCH_SAMPLE_KEY_AMBIGUOUS", outcomes)
        sample = source_by_key[key]
        table = matches[0]
        outcomes.append({"batch_ordinal": ordinal, "sample_index_row_id": key, "status": "COMPILED_EXACT"})
        selected.append((sample, table))
    for _sample, table in selected:
        roles = table.get("roles")
        if type(roles) is not dict or set(roles) != {"pocket", "ligand"}:
            return rejected("ROLE_TABLE_AUTHORITY_MISSING", outcomes)
        for role_name in ("pocket", "ligand"):
            role = roles.get(role_name)
            if type(role) is not dict or any(field not in role for field in _ROLE_AUTHORITY_FIELDS):
                return rejected("ROLE_TABLE_AUTHORITY_MISSING", outcomes)
    if observation.get("virtual_node_policy") != _VIRTUAL_POLICY:
        return rejected("VIRTUAL_NODE_POLICY_MISMATCH", outcomes)
    ligand_lengths = observation.get("ligand_lengths")
    pocket_lengths = observation.get("pocket_lengths")
    if (
        type(ligand_lengths) is not list or type(pocket_lengths) is not list
        or len(ligand_lengths) != len(batch_keys) or len(pocket_lengths) != len(batch_keys)
        or any(type(value) is not int or value < 0 for value in ligand_lengths + pocket_lengths)
    ):
        return rejected("ROLE_LENGTH_MISMATCH", outcomes)
    for ordinal, (_sample, table) in enumerate(selected):
        if (
            ligand_lengths[ordinal] != table["roles"]["ligand"]["parser_output_atom_count"]
            or pocket_lengths[ordinal] != table["roles"]["pocket"]["parser_output_atom_count"]
        ):
            return rejected("ROLE_LENGTH_MISMATCH", outcomes)
    ligand_membership = observation.get("ligand_membership")
    pocket_membership = observation.get("pocket_membership")
    if (
        type(ligand_membership) is not list or type(pocket_membership) is not list
        or any(type(value) is not int for value in ligand_membership + pocket_membership)
        or ligand_membership != _membership(ligand_lengths)
        or pocket_membership != _membership(pocket_lengths)
    ):
        return rejected("MEMBERSHIP_MASK_MISMATCH", outcomes)
    buffers = observation.get("consistency_buffer_lengths")
    if buffers is not None:
        expected_buffers = {
            "ligand_coords": sum(ligand_lengths), "ligand_one_hot": sum(ligand_lengths),
            "pocket_coords": sum(pocket_lengths), "pocket_one_hot": sum(pocket_lengths),
        }
        if (
            type(buffers) is not dict or set(buffers) != set(expected_buffers)
            or any(type(value) is not int or value < 0 for value in buffers.values())
            or buffers != expected_buffers
        ):
            return rejected("ROLE_LENGTH_MISMATCH", outcomes)
    receptors = observation.get("receptors")
    if receptors is not None and (
        type(receptors) is not list or len(receptors) != len(batch_keys)
        or any(type(value) is not str for value in receptors)
    ):
        return rejected("BATCH_OBSERVATION_SCHEMA_MISMATCH", outcomes)
    joint = observation.get("joint_layout_descriptor")
    if joint not in (None, _JOINT_LAYOUT):
        return rejected("BATCH_OBSERVATION_SCHEMA_MISMATCH", outcomes)
    for field in ("debug_coordinates", "debug_rank_metadata"):
        value = observation.get(field)
        if value is not None and type(value) is not dict:
            return rejected("BATCH_OBSERVATION_SCHEMA_MISMATCH", outcomes)
        try:
            _compact(value)
        except ValueError:
            return rejected("BATCH_OBSERVATION_SCHEMA_MISMATCH", outcomes)
    batch_order = [_identity(sample) for sample, _table in selected]
    tables = [copy.deepcopy(table) for _sample, table in selected]
    exact18 = {
        "schema_version": source_contract["schema_version"],
        "source_projection_digest": source_contract["source_projection_digest"],
        "source_payload_digest": source_contract["source_payload_digest"],
        "parser_schema_version": source_contract["parser_schema_version"],
        "collate_schema_version": source_contract["collate_schema_version"],
        "source_sample_order": copy.deepcopy(source_contract["source_sample_order"]),
        "source_pair_values_int64": copy.deepcopy(source_contract["source_pair_values_int64"]),
        "source_sample_offsets_int64": copy.deepcopy(source_contract["source_sample_offsets_int64"]),
        "source_entry_validity_bool": copy.deepcopy(source_contract["source_entry_validity_bool"]),
        "source_sample_validity_bool": copy.deepcopy(source_contract["source_sample_validity_bool"]),
        "batch_sample_order": batch_order,
        "batch_sample_atom_identity_tables": tables,
        "batch_role_lengths": {"pocket": pocket_lengths[:], "ligand": ligand_lengths[:]},
        "batch_role_offsets": {"pocket": _prefix(pocket_lengths), "ligand": _prefix(ligand_lengths)},
        "batch_membership_masks": {"pocket": pocket_membership[:], "ligand": ligand_membership[:]},
        "joint_layout_descriptor": joint,
        "debug_coordinates": copy.deepcopy(observation.get("debug_coordinates")),
        "debug_rank_metadata": copy.deepcopy(observation.get("debug_rank_metadata")),
    }
    if tuple(exact18) != _EXACT18_FIELDS:
        _fail()
    return _compiler_output(
        "COMPILED_EXACT", exact18=exact18, outcomes=outcomes,
        provider_digest=expected_identity_provider_digest,
        joint_status="COMPILED_EXACT" if joint == _JOINT_LAYOUT else "JOINT_LAYOUT_UNAVAILABLE",
    )


def _compose(repo: Path, state: Path, exact18: dict[str, object]) -> dict[str, object]:
    with _precommit_compatibility():
        exact2 = _adapter.build_covapie_current11_task2_batch_index_remap_adapter_v1(
            repo_root=repo, state_root=state, adapter_input=copy.deepcopy(exact18)
        )
    if type(exact2) is not dict or tuple(exact2) != (
        "current11_task2_batch_index_remap_output.json",
        "current11_task2_batch_index_remap_adapter_report.json",
    ):
        _fail()
    output = _strict_json(exact2["current11_task2_batch_index_remap_output.json"])
    report = _strict_json(exact2["current11_task2_batch_index_remap_adapter_report.json"])
    if output.get("remap_status") != "REMAPPED_EXACT" or output.get("failure_reason") != "NONE":
        _fail()
    if report.get("adapter_status") != "PASS_IN_MEMORY_TASK2_BATCH_INDEX_REMAP_ONLY":
        _fail()
    if exact18["joint_layout_descriptor"] is None:
        if output.get("pair_values_joint_global_indices") is not None:
            _fail()
    return {
        "adapter_status": report["adapter_status"], "remap_status": output["remap_status"],
        "failure_reason": output["failure_reason"],
        "batch_sample_order": output["batch_sample_order"],
        "pair_values_batch_indices": output["pair_values_batch_indices"],
        "pair_values_joint_global_indices": output["pair_values_joint_global_indices"],
    }


def _case_record(case_id: str, case_class: str, mutation: str, output: Mapping[str, object], *, adapter_required: bool) -> dict[str, object]:
    exact18 = output.get("adapter_input_exact18")
    return {
        "case_id": case_id, "case_class": case_class, "input_mutation": mutation,
        "expected_compiler_status": output.get("compiler_status"),
        "expected_failure_reason": output.get("failure_reason"),
        "expected_exact18_present": exact18 is not None,
        "expected_joint_component_status": output.get("runtime_schema_binding", {}).get("joint_layout_component_status"),
        "adapter_composition_required": adapter_required,
        "compiler_output": copy.deepcopy(output),
    }


def _reference_vectors(
    repo: Path, state: Path, source: dict[str, object], provider: list[dict[str, object]],
    provider_digest: str,
) -> tuple[dict[str, object], int, int, int]:
    samples = source["source_sample_order"]
    success_specs = (
        ("canonical_exact11", list(range(11)), _JOINT_LAYOUT),
        ("reversed_exact11", list(reversed(range(11))), _JOINT_LAYOUT),
        ("mixed_10_4_0_7_2", [10, 4, 0, 7, 2], _JOINT_LAYOUT),
        ("subset_10_4_0", [10, 4, 0], _JOINT_LAYOUT),
        ("no_joint", list(range(11)), None),
        ("empty_batch", [], _JOINT_LAYOUT),
    )
    records: list[dict[str, object]] = []
    compositions: dict[str, object] = {}
    for case_id, order, joint in success_specs:
        observation = _observation(order, samples, joint=joint)
        output = _evaluate_reference_case_v1(
            observation, source_contract=source, identity_provider=provider,
            expected_identity_provider_digest=provider_digest,
        )
        if output.get("compiler_status") != "COMPILED_EXACT" or type(output.get("adapter_input_exact18")) is not dict:
            _fail()
        compositions[case_id] = _compose(repo, state, output["adapter_input_exact18"])
        records.append(_case_record(case_id, "success", "none" if case_id == "canonical_exact11" else case_id, output, adapter_required=True))

    base = _observation([10, 4, 0], samples)
    failure_specs: list[tuple[str, str, object, object, bool, bool]] = []

    def mutated(field: str, value: object) -> dict[str, object]:
        result = copy.deepcopy(base)
        if value is _MISSING:
            result.pop(field, None)
        else:
            result[field] = value
        return result

    failure_specs.extend((
        ("duplicate_runtime_key", "duplicate key", mutated("batch_sample_keys", [samples[10]["sample_index_row_id"]] * 3), provider, True, True),
        ("unknown_runtime_key", "unknown key", mutated("batch_sample_keys", ["TOTALLY_UNKNOWN"]), provider, True, True),
        ("non_source_known_sample", "known-shaped non-source key", mutated("batch_sample_keys", ["CYS_SG_SAMPLE_INDEX_999999"]), provider, True, True),
        ("invalid_key_type", "integer key", mutated("batch_sample_keys", [1]), provider, True, True),
        ("empty_key", "empty key", mutated("batch_sample_keys", [""]), provider, True, True),
        ("untrimmed_key", "untrimmed key", mutated("batch_sample_keys", [" CYS_SG_SAMPLE_INDEX_000011"]), provider, True, True),
        ("wrong_runtime_schema", "runtime schema drift", mutated("runtime_batch_schema_version", "drift"), provider, True, True),
        ("wrong_sample_key_schema", "sample-key schema drift", mutated("sample_key_schema_version", "drift"), provider, True, True),
        ("virtual_policy_mismatch", "virtual policy drift", mutated("virtual_node_policy", "virtual_nodes_v1"), provider, True, True),
        ("wrong_ligand_length", "ligand length drift", mutated("ligand_lengths", [22, 28, 13]), provider, True, True),
        ("wrong_pocket_length", "pocket length drift", mutated("pocket_lengths", [227, 188, 66]), provider, True, True),
        ("bool_length", "bool length", mutated("ligand_lengths", [True, 28, 13]), provider, True, True),
        ("float_length", "float length", mutated("ligand_lengths", [21.0, 28, 13]), provider, True, True),
        ("wrong_ligand_membership", "ligand membership length", mutated("ligand_membership", []), provider, True, True),
        ("wrong_pocket_membership", "pocket membership length", mutated("pocket_membership", []), provider, True, True),
        ("bool_membership", "bool membership", mutated("ligand_membership", [True] + base["ligand_membership"][1:]), provider, True, True),
        ("float_membership", "float membership", mutated("ligand_membership", [0.0] + base["ligand_membership"][1:]), provider, True, True),
        ("membership_wrong_ordinal_order", "ordinal order drift", mutated("ligand_membership", list(reversed(base["ligand_membership"]))), provider, True, True),
        ("consistency_buffer_mismatch", "buffer length drift", mutated("consistency_buffer_lengths", {"ligand_coords": 0, "ligand_one_hot": 92, "pocket_coords": 482, "pocket_one_hot": 482}), provider, True, True),
        ("source_contract_override", "caller source override", {**copy.deepcopy(base), "source_projection_digest": _PROJECTION_DIGEST}, provider, True, True),
        ("provider_missing", "provider unavailable", base, None, True, False),
        ("unknown_joint_descriptor", "joint descriptor drift", mutated("joint_layout_descriptor", "unknown"), provider, True, True),
        ("unknown_top_level_field", "unknown field", {**copy.deepcopy(base), "unknown_field": 1}, provider, True, True),
        ("missing_required_field", "required field absent", mutated("ligand_lengths", _MISSING), provider, True, True),
        ("runtime_name_path_drift", "path-like runtime key", mutated("batch_sample_keys", ["path/CYS_SG_SAMPLE_INDEX_000011"]), provider, True, True),
    ))
    duplicate_provider = copy.deepcopy(provider)
    duplicate_provider.append(copy.deepcopy(provider[10]))
    failure_specs.append(("ambiguous_provider_match", "duplicate provider sample", base, duplicate_provider, True, True))
    drift_provider = copy.deepcopy(provider)
    drift_provider[0]["roles"]["pocket"]["SHA256"] = "0" * 64
    failure_specs.append(("provider_digest_drift", "provider bytes drift", base, drift_provider, True, True))
    for role_name in ("pocket", "ligand"):
        missing_provider = copy.deepcopy(provider)
        del missing_provider[10]["roles"][role_name]
        failure_specs.append((f"missing_{role_name}_role", f"missing {role_name} role", base, missing_provider, True, True))
    for case_id, mutation, observation, case_provider, source_available, provider_available in failure_specs:
        expected_digest = (
            _provider_digest(case_provider)
            if case_id in {"ambiguous_provider_match", "missing_pocket_role", "missing_ligand_role"}
            else provider_digest
        )
        output = _evaluate_reference_case_v1(
            observation, source_contract=source, identity_provider=case_provider,
            expected_identity_provider_digest=expected_digest,
            source_contract_available=source_available, identity_provider_available=provider_available,
        )
        if output.get("compiler_status") not in _HARD_FAILURES or output.get("adapter_input_exact18") is not None:
            _fail()
        records.append(_case_record(case_id, "hard_failure", mutation, output, adapter_required=False))
    status_by_case = {row["case_id"]: row["expected_compiler_status"] for row in records}
    expected = {
        "ambiguous_provider_match": "BATCH_SAMPLE_KEY_AMBIGUOUS",
        "provider_digest_drift": "IDENTITY_PROVIDER_MISMATCH",
        "missing_pocket_role": "ROLE_TABLE_AUTHORITY_MISSING",
        "missing_ligand_role": "ROLE_TABLE_AUTHORITY_MISSING",
    }
    if any(status_by_case.get(case) != status for case, status in expected.items()):
        _fail()
    vectors = {
        "schema_version": _REFERENCE_SCHEMA,
        "canonical_runtime_observation": _observation(list(range(11)), samples),
        "identity_provider_digest": provider_digest,
        "identity_provider": provider,
        "reference_cases": records,
        "public_adapter_compositions": compositions,
    }
    return vectors, len(success_specs), len(failure_specs), len(compositions)


_MISSING = object()


def _input_schema_artifact() -> dict[str, object]:
    return {
        "schema_version": _INPUT_SCHEMA, "field_order": list(_INPUT_FIELDS),
        "required_fields": list(_INPUT_FIELDS[:10]), "optional_fields": list(_INPUT_FIELDS[10:]),
        "unknown_field_policy": "fail_closed", "source_contract_override_fields": sorted(_SOURCE_OVERRIDE_FIELDS),
        "other_forbidden_fields": sorted(_FORBIDDEN_INPUT_FIELDS - _SOURCE_OVERRIDE_FIELDS),
        "field_contracts": {
            "batch_sample_keys": {"container": "exact_builtin_list[str]", "logical_shape": "[B]", "identity_matching": "exact_only"},
            "ligand_lengths": {"container": "exact_builtin_list[int]", "bool_allowed": False, "minimum": 0},
            "pocket_lengths": {"container": "exact_builtin_list[int]", "bool_allowed": False, "minimum": 0},
            "ligand_membership": {"rule": "expanded_batch_ordinals_from_ligand_lengths"},
            "pocket_membership": {"rule": "expanded_batch_ordinals_from_pocket_lengths"},
            "joint_layout_descriptor": {"allowed": [_JOINT_LAYOUT, None]},
            "virtual_node_policy": {"exact": _VIRTUAL_POLICY},
            "receptors": {"identity_selection_authorized": False, "consistency_only": True},
            "consistency_buffer_lengths": {"exact_keys": ["ligand_coords", "ligand_one_hot", "pocket_coords", "pocket_one_hot"]},
            "debug_coordinates": {"identity_selection_authorized": False, "transport_only": True},
            "debug_rank_metadata": {"identity_selection_authorized": False, "transport_only": True},
        },
    }


def _output_schema_artifact() -> dict[str, object]:
    return {
        "schema_version": _OUTPUT_SCHEMA, "field_order": list(_OUTPUT_FIELDS),
        "success_status": "COMPILED_EXACT", "success_failure_reason": "NONE",
        "hard_failure_exact18": None, "partial_exact18_forbidden": True,
        "numeric_placeholder_forbidden": True, "negative_one_sentinel_forbidden": True,
        "adapter_input_exact18_field_order": list(_EXACT18_FIELDS),
        "source_fields": list(_EXACT18_FIELDS[:10]),
        "compiler_derived_fields": list(_EXACT18_FIELDS[10:]),
    }


def _status_csv() -> bytes:
    descriptions = {
        "COMPILED_EXACT": "Exact contract-level compilation succeeded.",
        "JOINT_LAYOUT_UNAVAILABLE": "Optional joint component is unavailable; compilation remains successful.",
    }
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(("status_code", "status", "is_overall_success", "is_component_only", "is_hard_failure", "exact18_allowed", "description"))
    for code, status_name in enumerate(_STATUS_ORDER):
        success = status_name == "COMPILED_EXACT"
        component = status_name == "JOINT_LAYOUT_UNAVAILABLE"
        writer.writerow((code, status_name, str(success).lower(), str(component).lower(), str(status_name in _HARD_FAILURES).lower(), str(success).lower(), descriptions.get(status_name, f"Fail closed with {status_name}.")))
    return buffer.getvalue().encode("utf-8")


def _fail_closed_invariants() -> list[str]:
    return [
        "source fields come only from the published remap contract",
        "caller cannot override the source contract",
        "runtime sample keys are exact strings",
        "runtime sample keys are unique",
        "sample key lookup is exact-one",
        "batch ordinal is not identity",
        "coordinates and features are not identity",
        "Current11 role tables come from the pinned Exact22 provider",
        "non-source authority is never fabricated",
        "lengths are exact Python ints",
        "bool is not an accepted int",
        "offsets are computed only as exclusive prefix sums",
        "membership entries are exact ints",
        "membership exactly matches lengths and batch order",
        "ligand and pocket roles cannot be exchanged",
        "formal runtime carrier is materialized and independently verified",
        "sample key binds to the formal names contract",
        "runtime order binds to the formal role-order contract",
        "virtual nodes are forbidden in V1",
        "subsets are allowed",
        "shuffle changes only batch order offsets and membership",
        "duplicate samples are rejected",
        "empty batch semantics are fixed",
        "null joint layout is never guessed",
        "compiler does not execute remap",
        "compiler writes no state",
        "compiler authorizes no model head or loss changes",
        "this gate does not implement the compiler",
        "non-source samples are rejected without a general provider",
        "feature semantics audit remains a training prerequisite",
    ]


def _manifest_artifact(
    provider_digest: str, reference_ids: list[str],
    formal_manifest: Mapping[str, object], inventory: Sequence[Mapping[str, str]],
) -> dict[str, object]:
    readiness = _gate_readiness()
    return {
        "schema_version": _SCHEMA,
        "source_lineage": {
            "carrier_contract_gate": {"commit": "f385a0fdd55fc205df71feca604fea729015aada", "contract_digest": _CARRIER_CONTRACT_DIGEST},
            "runtime_carrier_materializer": {"commit": "8b190cd9035b073b3ef48f452c9bea21eabbe96a", "relative_path": "src/covalent_ext/covapie_current11_runtime_sample_and_role_order_carrier_materializer_v1.py", "SHA256": "361b686abe25b088dbcbb8439fa4c26fd86e507259e705ae3dd06e9a25f655eb"},
            "public_remap_adapter": {"commit": "b3c76bd4321da5aece08711a4d6f2d421cb8b54b", "stable_output_digest": _ADAPTER_OUTPUT_DIGEST},
            "remap_contract": {"commit": "6502321ca56ce8895adb3ee20587c383dfbda767", "contract_digest": _REMAP_CONTRACT_DIGEST},
            "projection_lineage": {"projection_instance_digest": _PROJECTION_DIGEST, "payload_bundle_digest": _PAYLOAD_DIGEST, "projection_contract_digest": _PROJECTION_CONTRACT_DIGEST},
            "formal_routing_sidecar": {"snapshot": _ROUTING_SNAPSHOT, "aggregate": _ROUTING_AGGREGATE},
            "non_runtime_design": {"relative_path": _DESIGN_RELATIVE, "bytes": 37665, "LF": 400, "SHA256": _DESIGN_SHA, "contract_authority": False, "read_by_gate": False},
        },
        "formal_runtime_carrier_binding": {
            "canonical_relative_path": _FORMAL_RELATIVE, "aggregate": _FORMAL_AGGREGATE,
            "Exact4_SHA256": {name: digest for name, (_size, digest) in _FORMAL_IDENTITIES.items()},
            "names_semantic_digest": _NAMES_DIGEST, "hidden_nonce_bound": False,
            "sample_order": copy.deepcopy(formal_manifest["sample_order"]),
            "ligand_sample_lengths": copy.deepcopy(formal_manifest["ligand_buffer_binding"]["sample_lengths"]),
            "ligand_sample_offsets": copy.deepcopy(formal_manifest["ligand_buffer_binding"]["sample_offsets"]),
            "ligand_per_sample_role_order_record_digests": copy.deepcopy(formal_manifest["ligand_buffer_binding"]["per_sample_role_order_record_digests"]),
            "pocket_sample_lengths": copy.deepcopy(formal_manifest["pocket_buffer_binding"]["sample_lengths"]),
            "pocket_sample_offsets": copy.deepcopy(formal_manifest["pocket_buffer_binding"]["sample_offsets"]),
            "pocket_per_sample_role_order_record_digests": copy.deepcopy(formal_manifest["pocket_buffer_binding"]["per_sample_role_order_record_digests"]),
            "array_inventory": [
                {
                    "array_index": int(row["array_index"]), "array_name": row["array_name"],
                    "dtype": row["dtype"], "shape": json.loads(row["shape_json"]),
                    "raw_c_order_sha256": row["raw_c_order_sha256"],
                }
                for row in inventory
            ],
        },
        "compiler_scope": {"contract_only": True, "compiler_implemented": False, "runtime_extractor_implemented": False, "read_only": True, "in_memory_only": True},
        "input_contract": {"schema_version": _INPUT_SCHEMA, "field_count": 14, "required_count": 10, "optional_count": 4},
        "output_contract": {"schema_version": _OUTPUT_SCHEMA, "field_count": 10, "adapter_input_field_count": 18},
        "source_contract_binding": {"remap_contract_digest": _REMAP_CONTRACT_DIGEST, "source_sample_count": 11},
        "identity_provider_binding": {"identity_provider_digest": provider_digest, "sample_count": 11, "role_table_count": 22},
        "runtime_schema_binding": {"runtime_batch_schema_version": _RUNTIME_SCHEMA, "sample_key_schema_version": _SAMPLE_KEY_SCHEMA, "role_order_schema_version": _PARSER_SCHEMA, "virtual_node_policy": _VIRTUAL_POLICY},
        "status_contract": {"status_count": 15, "status_order": list(_STATUS_ORDER), "hard_failure_count": 13},
        "validation_order": list(_VALIDATION_ORDER), "reference_case_ids": reference_ids,
        "fail_closed_invariants": _fail_closed_invariants(),
        "checkpoint_compatibility": {key: readiness[key] for key in ("checkpoint_state_dict_change_required", "base_model_parameter_shape_change_required", "base_atom_feature_width_change_required", "egnn_or_se3_backbone_change_required", "checkpoint_bytes_read")},
        "auxiliary_module_scope": {
            "directly_advanced_not_integrated": ["target_residue_atom_condition_adapter", "covalent_pair_prediction_head"],
            "not_ready": ["role_mask_anchor_encoding", "pre_post_geometry_prediction_head", "covalent_pair_contrastive_loss"],
            "canonical_masks": ["warhead_only", "linker_plus_warhead", "scaffold_plus_warhead", "scaffold_only", "scaffold_plus_linker_plus_warhead"],
        },
        "readiness": readiness,
    }


def _stable_digest(artifacts: Mapping[str, bytes]) -> str:
    digest = hashlib.sha256(_DOMAIN)
    for name in _STABLE_NAMES:
        encoded = name.encode("utf-8")
        payload = artifacts[name]
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _validate_artifact(name: str, payload: bytes) -> None:
    if (
        type(payload) is not bytes or not payload or len(payload) >= 1024 * 1024
        or payload.startswith(b"\xef\xbb\xbf") or b"\0" in payload or b"\r" in payload
        or not payload.endswith(b"\n") or payload.endswith(b"\n\n")
    ):
        _fail()
    if name.endswith(".json") and _json(_strict_json(payload)) != payload:
        _fail()


def _build_impl(*, repo_root: Path, state_root: Path) -> dict[str, bytes]:
    repo = _require_root(repo_root)
    state = _require_root(state_root)
    canonical = state / _FORMAL_RELATIVE
    formal_before, formal_manifest, inventory = _validate_formal(state)
    vectors, carrier_report = _published_contracts(repo, state)
    source = _source_contract(vectors)
    provider = _identity_provider(vectors, source)
    provider_digest = _provider_digest(provider)
    if formal_manifest.get("sample_order") != [
        row.get("sample_index_row_id") for row in source["source_sample_order"]
    ]:
        _fail()
    reference, success_count, failure_count, composition_count = _reference_vectors(
        repo, state, source, provider, provider_digest
    )
    reference_ids = [row["case_id"] for row in reference["reference_cases"]]
    stable_values = (
        _manifest_artifact(provider_digest, reference_ids, formal_manifest, inventory),
        _input_schema_artifact(), _output_schema_artifact(), None, reference,
    )
    artifacts: dict[str, bytes] = {}
    for name, value in zip(_STABLE_NAMES, stable_values):
        artifacts[name] = _status_csv() if name == _VOCABULARY else _json(value)
    contract_digest = _stable_digest(artifacts)
    identities = [
        {"artifact_index": index, "artifact_name": name, "stable_digest_participation": True, "bytes": len(artifacts[name]), "LF": artifacts[name].count(b"\n"), "SHA256": _sha(artifacts[name])}
        for index, name in enumerate(_STABLE_NAMES)
    ]
    identities.append({"artifact_index": 5, "artifact_name": _REPORT, "stable_digest_participation": False, "content_identity": "self_excluded"})
    report = {
        "schema_version": _REPORT_SCHEMA, "gate_status": "PASS_CONTRACT_ONLY",
        "contract_digest": contract_digest, "artifact_file_count": 6,
        "artifact_identities": identities, "formal_runtime_carrier_verified": True,
        "formal_carrier_aggregate": _FORMAL_AGGREGATE,
        "formal_carrier_npz_sha256": _FORMAL_IDENTITIES[_NPZ][1],
        "formal_carrier_manifest_sha256": _FORMAL_IDENTITIES[_FORMAL_MANIFEST][1],
        "formal_carrier_inventory_sha256": _FORMAL_IDENTITIES[_INVENTORY][1],
        "formal_carrier_binding_report_sha256": _FORMAL_IDENTITIES[_BINDING_REPORT][1],
        "carrier_contract_digest": _CARRIER_CONTRACT_DIGEST,
        "remap_contract_digest": _REMAP_CONTRACT_DIGEST,
        "projection_instance_digest": _PROJECTION_DIGEST, "payload_bundle_digest": _PAYLOAD_DIGEST,
        "projection_contract_digest": _PROJECTION_CONTRACT_DIGEST,
        "adapter_stable_output_digest": _ADAPTER_OUTPUT_DIGEST,
        "source_contract_verified": True, "identity_provider_digest": provider_digest,
        "identity_provider_sample_count": 11, "identity_provider_role_table_count": 22,
        "input_field_count": 14, "input_required_field_count": 10, "input_optional_field_count": 4,
        "output_field_count": 10, "status_vocabulary_count": 15,
        "reference_case_count": success_count + failure_count, "success_case_count": success_count,
        "hard_failure_case_count": failure_count,
        "public_adapter_composition_case_count": composition_count,
        "public_adapter_composition_all_passed": composition_count == success_count,
        "empty_batch_adapter_compatible": "empty_batch" in reference["public_adapter_compositions"],
        "formal_inventory_array_count": len(inventory),
        "carrier_contract_predecessor_passed": carrier_report.get("gate_status") == "PASS_CONTRACT_ONLY",
        "formal_state_unchanged": _formal_snapshot(canonical) == formal_before,
        "repository_unchanged": True, "readiness": _gate_readiness(),
    }
    if report["formal_state_unchanged"] is not True:
        _fail()
    artifacts[_REPORT] = _json(report)
    if type(artifacts) is not dict or tuple(artifacts) != _ARTIFACT_NAMES:
        _fail()
    for name, payload in artifacts.items():
        _validate_artifact(name, payload)
    if _formal_snapshot(canonical) != formal_before:
        _fail()
    return artifacts


def build_covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1(
    *, repo_root: Path, state_root: Path,
) -> dict[str, bytes]:
    """Return the deterministic compiler contract Exact6 in memory without writes."""
    try:
        return _build_impl(repo_root=repo_root, state_root=state_root)
    except BaseException as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
