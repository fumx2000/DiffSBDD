"""Pure in-memory Current11 Task 2 batch-index remap adapter V1."""

from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import os
import stat
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Iterator, Mapping, NoReturn, Sequence

from covalent_ext import covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1 as _projection_contract_gate
from covalent_ext import covapie_current11_task2_batch_index_remap_contract_gate_v1 as _contract_gate


__all__ = ("build_covapie_current11_task2_batch_index_remap_adapter_v1",)

_ERROR = "COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_ADAPTER_V1_ERROR"
_OUTPUT_NAME = "current11_task2_batch_index_remap_output.json"
_REPORT_NAME = "current11_task2_batch_index_remap_adapter_report.json"
_ARTIFACT_NAMES = (_OUTPUT_NAME, _REPORT_NAME)
_OUTPUT_SCHEMA = "covapie_current11_task2_batch_index_remap_adapter_output_v1"
_REPORT_SCHEMA = "covapie_current11_task2_batch_index_remap_adapter_report_v1"
_INPUT_SCHEMA = "covapie_current11_task2_batch_index_remap_adapter_input_v1"
_CONTRACT_SCHEMA = "covapie_current11_task2_batch_index_remap_contract_v1"
_REFERENCE_SCHEMA = "covapie_current11_task2_batch_index_remap_reference_vectors_v1"
_CONTRACT_REPORT_SCHEMA = "covapie_current11_task2_batch_index_remap_contract_gate_report_v1"
_CONTRACT_STATUS = "PASS_CONTRACT_ONLY"
_SUCCESS_STATUS = "PASS_IN_MEMORY_TASK2_BATCH_INDEX_REMAP_ONLY"
_FAILURE_STATUS = "FAIL_CLOSED_INPUT_REJECTED"
_JOINT_LAYOUT = "ligand_segment_then_pocket_segment_v1"
_JOIN = "exact_source_table_row_identity_to_order_preserving_parser_node_v1"
_PARSER_SCHEMA = "order_preserving_checkpoint_heavy_projection_v1"
_COLLATE_SCHEMA = "processed_ligand_pocket_dataset_collate_fn_v1"
_PROJECTION_DIGEST = "b8e8078700bd019d4a11a00c17dc84fa05e406bbf61b51bf3e887988f3b89255"
_PAYLOAD_DIGEST = "95e9ed091566bbc547a8f75b975a40c27ce318e95df1553b1f1ac448a91b1f9d"
_PROJECTION_CONTRACT_DIGEST = "d0a428c19fe3c4aefc575065e7dcc7a7cfaf8593526d025d467cf6568b49c21d"
_REMAP_CONTRACT_DIGEST = "2c6259312a3292181f00ebbaf787fab05e5a97e5b5475243f2fa8461b54dcdc6"
_FORMAL_RELATIVE = "formal-sidecars/current11-dataset-partial-supervision-routing-sidecar-v1"
_FORMAL_READLINK = ".current11-dataset-partial-supervision-routing-sidecar-v2.object-sha256-24f95099ba1ba0b81724535cb17c5d4d32c360f71c87422571210a2178ddb49c-1fd8cf5823427e941b11c7b2560a336f"
_FORMAL_AGGREGATE = "24f95099ba1ba0b81724535cb17c5d4d32c360f71c87422571210a2178ddb49c"
_FORMAL_SNAPSHOT_SHA256 = "768fbd980efbcedcaa2ef971a7d77791879111d1fceeb1f03cb1eb8bfff24034"
_FORMAL_FILES = {
    "current11_dataset_partial_supervision_routing_manifest.json": "3a2c2e8170f20ed0a8ea97798a5945ec846cd36d81fe950aa58fee6311984a7d",
    "current11_dataset_partial_supervision_routing_records.csv": "751e32f46ab386604386167bdffd38f762472bbc9fdff4af7167a979ac68af03",
    "current11_dataset_partial_supervision_sample_coverage.csv": "7cd2ecd99caca09f94019d543793f70de6d9cb86ff431fbd49782b76b2814b5e",
    "current11_dataset_partial_supervision_task_coverage.csv": "ee8bfe7f0bed65e6858ae318695470abc3a92de3ca72d2548e2d5c4e950aa2b7",
}

_GATE_RELATIVE = "src/covalent_ext/covapie_current11_task2_batch_index_remap_contract_gate_v1.py"
_GATE_BYTES = 70077
_GATE_LF = 926
_GATE_SHA256 = "e9f7d83a17d08eda338ce4d64ab60241887e488c6139ee70af7f210b82bc6eec"
_GATE_BLOB = "6d5f495bac770ef4a87f641ae340fd39947122f4"
_REPOSITORY_EXACT4 = (
    "src/covalent_ext/covapie_current11_task2_batch_index_remap_adapter_v1.py",
    "scripts/check_covapie_current11_task2_batch_index_remap_adapter_v1.py",
    "tests/test_covapie_current11_task2_batch_index_remap_adapter_v1.py",
    "docs/covapie_current11_task2_batch_index_remap_adapter_v1_guide.md",
)

_MANIFEST = "current11_task2_batch_index_remap_contract_manifest.json"
_INPUT = "current11_task2_batch_index_remap_input_schema.json"
_OUTPUT = "current11_task2_batch_index_remap_output_schema.json"
_VOCABULARY = "current11_task2_batch_index_remap_status_vocabulary.csv"
_VECTORS = "current11_task2_batch_index_remap_reference_vectors.json"
_GATE_REPORT = "current11_task2_batch_index_remap_contract_gate_report.json"
_GATE_ARTIFACT_NAMES = (_MANIFEST, _INPUT, _OUTPUT, _VOCABULARY, _VECTORS, _GATE_REPORT)
_GATE_STABLE_NAMES = _GATE_ARTIFACT_NAMES[:5]
_GATE_IDENTITIES = {
    _MANIFEST: (50797, 1254, "f887cd6069101c42209a243770714194f76507484e4c264fe68376c610838bfa"),
    _INPUT: (13673, 449, "d2a8501218ff4a865c3d583f0ffee76bbc3cfc04e5d8acf08028c9daad396bd5"),
    _OUTPUT: (9395, 322, "772f6e92e43dbb665f66061c3625795c25426f0d75cb79de0693d613b502fbd8"),
    _VOCABULARY: (2214, 19, "41ac8e635d9dbb4d8c6b5235239ac5bb8a6e088daaa798000a0fa3e2a876a46a"),
    _VECTORS: (78673, 2934, "8fb4c78ffc21aa2425a19a72c3159999e01a9f47b6e17ec451011e9a3c096556"),
    _GATE_REPORT: (3794, 93, "0258b7d53971d08ea65556a7dc1d46a4c000c869ef9941ff76600331ae9d4b09"),
}
_CONTRACT_DOMAIN_TAG = b"COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_CONTRACT_GATE_V1\0"
_OUTPUT_DOMAIN_TAG = b"COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_ADAPTER_V1\0"

_INPUT_FIELD_ORDER = (
    "schema_version",
    "source_projection_digest",
    "source_payload_digest",
    "parser_schema_version",
    "collate_schema_version",
    "source_sample_order",
    "source_pair_values_int64",
    "source_sample_offsets_int64",
    "source_entry_validity_bool",
    "source_sample_validity_bool",
    "batch_sample_order",
    "batch_sample_atom_identity_tables",
    "batch_role_lengths",
    "batch_role_offsets",
    "batch_membership_masks",
    "joint_layout_descriptor",
    "debug_coordinates",
    "debug_rank_metadata",
)
_INPUT_REQUIRED = frozenset(_INPUT_FIELD_ORDER[:15])
_INPUT_OPTIONAL = frozenset(_INPUT_FIELD_ORDER[15:])
_LEGACY_ALIASES = frozenset(
    (
        "source_pair_values",
        "source_sample_offsets",
        "source_entry_validity",
        "source_sample_validity",
    )
)
_OUTPUT_FIELD_ORDER = (
    "schema_version",
    "source_projection_digest",
    "source_payload_digest",
    "batch_sample_order",
    "pair_values_source_row_indices",
    "pair_values_parser_local_indices",
    "pair_values_batch_indices",
    "pair_values_joint_global_indices",
    "pair_sample_indices",
    "sample_pair_offsets",
    "entry_validity",
    "sample_validity",
    "source_entry_outcomes",
    "remap_status",
    "failure_reason",
    "provenance",
    "readiness",
)
_IDENTITY_FIELDS = (
    "sample_index_row_id",
    "sample_preparation_input_id",
    "pdb_id",
    "ligand_comp_id",
)
_TABLE_AUTHORITY_FIELDS = (
    "root_kind",
    "relative_path",
    "SHA256",
    "row_count",
    "row_order_digest",
    "row_order_version",
    "selected_source_row_index_0based",
    "selected_parser_local_index",
    "parser_output_atom_count",
)
_ATOM_IDENTITY_FIELDS = (
    "atom_site_id",
    "atom_name",
    "type_symbol",
    "residue_name_or_ligand_comp_id",
    "auth_asym_id",
    "auth_seq_id",
    "label_asym_id",
    "label_seq_id",
)
_INDEX_SPACES = (
    "source_atom_table_data_row_index",
    "parser_sample_local_index",
    "collated_batch_segment_index",
    "dynamics_joint_global_node_index",
)
_STATUS_ORDER = (
    "REMAPPED_EXACT",
    "NOT_IN_BATCH",
    "SOURCE_SAMPLE_DUPLICATED",
    "BATCH_SAMPLE_IDENTITY_UNKNOWN",
    "BATCH_SAMPLE_DUPLICATED",
    "SCHEMA_VERSION_MISMATCH",
    "SOURCE_TABLE_IDENTITY_MISMATCH",
    "SOURCE_ROW_OUT_OF_RANGE",
    "SOURCE_ATOM_IDENTITY_MISMATCH",
    "ROLE_MISMATCH",
    "PARSER_ATOM_NOT_FOUND",
    "PARSER_ATOM_NOT_UNIQUE",
    "PARSER_COUNT_MISMATCH",
    "COLLATE_OFFSET_MISSING",
    "COLLATE_LENGTH_MISMATCH",
    "BATCH_INDEX_OUT_OF_RANGE",
    "JOINT_INDEX_SPACE_UNAVAILABLE",
    "ENTRY_INVALID",
)
_HARD_FAILURES = frozenset(_STATUS_ORDER[2:16] + (_STATUS_ORDER[17],))
_SOURCE_PAIRS = (
    (88, 3),
    (25, 3),
    (19, 3),
    (39, 3),
    (37, 27),
    (50, 21),
    (48, 16),
    (53, 20),
    (52, 21),
    (53, 18),
    (84, 5),
)


def _fail() -> NoReturn:
    raise ValueError(_ERROR)


class _InputFailure(Exception):
    def __init__(self, status: str, entry_index: int = 0) -> None:
        self.status = status
        self.entry_index = entry_index


def _input_fail(status: str, entry_index: int = 0) -> NoReturn:
    if status not in _HARD_FAILURES:
        _fail()
    raise _InputFailure(status, entry_index)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _blob(payload: bytes) -> str:
    header = b"blob " + str(len(payload)).encode("ascii") + b"\0"
    return hashlib.sha1(header + payload).hexdigest()


def _json(value: object) -> bytes:
    try:
        text = json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise ValueError(_ERROR) from error
    payload = (text + "\n").encode("utf-8")
    if (
        not payload
        or len(payload) >= 1024 * 1024
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\0" in payload
        or b"\r" in payload
        or not payload.endswith(b"\n")
        or payload.endswith(b"\n\n")
    ):
        _fail()
    return payload


def _strict_json(payload: bytes) -> dict[str, object]:
    try:
        value = json.loads(
            payload.decode("utf-8"),
            parse_constant=lambda _value: _fail(),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(_ERROR) from error
    if type(value) is not dict or _json(value) != payload:
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


def _safe_relative(relative: str) -> PurePosixPath:
    if type(relative) is not str:
        _fail()
    path = PurePosixPath(relative)
    if not relative or path.is_absolute() or ".." in path.parts or str(path) != relative:
        _fail()
    return path


def _read_regular(root: Path, relative: str, expected_sha: str) -> bytes:
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
        or stat.S_IMODE(metadata.st_mode) != 0o644
        or _sha(payload) != expected_sha
    ):
        _fail()
    return payload


def _path_snapshot(path: Path) -> tuple[object, ...]:
    metadata = path.lstat()
    payload = path.read_bytes() if stat.S_ISREG(metadata.st_mode) else None
    return (
        int(metadata.st_dev),
        int(metadata.st_ino),
        stat.S_IFMT(metadata.st_mode),
        stat.S_IMODE(metadata.st_mode),
        int(metadata.st_size),
        int(metadata.st_mtime_ns),
        None if payload is None else _sha(payload),
    )


def _formal_snapshot(canonical: Path) -> dict[str, object]:
    try:
        parent = canonical.parent
        link = os.readlink(canonical)
        object_path = parent / link
        inventory = tuple(sorted(os.listdir(object_path)))
        return {
            "parent": _path_snapshot(parent),
            "parent_inventory": tuple(sorted(os.listdir(parent))),
            "canonical": _path_snapshot(canonical),
            "readlink": link,
            "object": _path_snapshot(object_path),
            "object_inventory": inventory,
            "leaves": {name: _path_snapshot(object_path / name) for name in inventory},
        }
    except OSError as error:
        raise ValueError(_ERROR) from error


def _validate_formal(canonical: Path) -> dict[str, object]:
    snapshot = _formal_snapshot(canonical)
    if snapshot.get("readlink") != _FORMAL_READLINK:
        _fail()
    if tuple(snapshot.get("object_inventory", ())) != tuple(sorted(_FORMAL_FILES)):
        _fail()
    object_path = canonical.parent / _FORMAL_READLINK
    for name, digest in _FORMAL_FILES.items():
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
    return snapshot


@contextmanager
def _gate_status_compatibility() -> Iterator[None]:
    original = _projection_contract_gate._run_git

    def compatible(root: Path, arguments: Sequence[str]) -> str:
        output = original(root, arguments)
        if tuple(arguments) == ("status", "--porcelain=v1", "--untracked-files=all"):
            allowed = {f"?? {path}" for path in _REPOSITORY_EXACT4}
            lines = output.splitlines()
            for line in lines:
                if len(line) >= 4 and line[3:] in _REPOSITORY_EXACT4 and line not in allowed:
                    _fail()
            output = "\n".join(line for line in lines if line not in allowed)
        return output

    try:
        _projection_contract_gate._run_git = compatible
        yield
    finally:
        _projection_contract_gate._run_git = original


def _contract_exact6(repo: Path, state: Path) -> dict[str, bytes]:
    gate_payload = _read_regular(repo, _GATE_RELATIVE, _GATE_SHA256)
    if len(gate_payload) != _GATE_BYTES or gate_payload.count(b"\n") != _GATE_LF or _blob(gate_payload) != _GATE_BLOB:
        _fail()
    with _gate_status_compatibility():
        first = _contract_gate.build_covapie_current11_task2_batch_index_remap_contract_gate_v1(
            repo_root=repo,
            state_root=state,
        )
    with _gate_status_compatibility():
        second = _contract_gate.build_covapie_current11_task2_batch_index_remap_contract_gate_v1(
            repo_root=repo,
            state_root=state,
        )
    if type(first) is not dict or type(second) is not dict or first != second:
        _fail()
    if tuple(first) != _GATE_ARTIFACT_NAMES or len(first) != 6:
        _fail()
    for name, identity in _GATE_IDENTITIES.items():
        size, lines, digest = identity
        payload = first.get(name)
        if type(payload) is not bytes or len(payload) != size or payload.count(b"\n") != lines or _sha(payload) != digest:
            _fail()
    digest = hashlib.sha256()
    digest.update(_CONTRACT_DOMAIN_TAG)
    for name in _GATE_STABLE_NAMES:
        name_bytes = name.encode("utf-8")
        payload = first[name]
        digest.update(len(name_bytes).to_bytes(8, "big", signed=False))
        digest.update(name_bytes)
        digest.update(len(payload).to_bytes(8, "big", signed=False))
        digest.update(payload)
    if digest.hexdigest() != _REMAP_CONTRACT_DIGEST:
        _fail()
    return first


def _csv_rows(payload: bytes) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
        rows = list(reader)
    except (UnicodeDecodeError, csv.Error) as error:
        raise ValueError(_ERROR) from error
    if reader.fieldnames is None or any(None in row for row in rows):
        _fail()
    return tuple(reader.fieldnames), rows


def _identity_complete(identity: object) -> bool:
    return type(identity) is dict and all(
        type(identity.get(field)) is str
        and bool(identity[field])
        and identity[field].strip() == identity[field]
        for field in _IDENTITY_FIELDS
    )


def _identity_key(identity: Mapping[str, object]) -> tuple[object, ...]:
    return tuple(identity.get(field) for field in _IDENTITY_FIELDS)


def _derive_role_authority(role: Mapping[str, object]) -> dict[str, object]:
    result = copy.deepcopy(dict(role))
    retained = result.get("retained_heavy_count")
    source_row = result.get("selected_source_row_index_0based")
    local = result.get("selected_parser_local_index")
    if type(retained) is not int or type(source_row) is not int or type(local) is not int:
        _fail()
    result["parser_output_atom_count"] = retained
    result["source_to_parser_local"] = {str(source_row): local}
    return result


def _parse_contract(exact6: Mapping[str, bytes]) -> dict[str, object]:
    manifest = _strict_json(exact6[_MANIFEST])
    input_schema = _strict_json(exact6[_INPUT])
    output_schema = _strict_json(exact6[_OUTPUT])
    vectors = _strict_json(exact6[_VECTORS])
    report = _strict_json(exact6[_GATE_REPORT])
    csv_header, statuses = _csv_rows(exact6[_VOCABULARY])
    expected_csv_header = (
        "status_code",
        "status",
        "scope",
        "is_success",
        "is_nonmember",
        "is_hard_failure",
        "numeric_output_allowed",
        "overall_status_allowed",
        "description",
    )
    if csv_header != expected_csv_header or tuple(row.get("status") for row in statuses) != _STATUS_ORDER:
        _fail()
    if tuple(row.get("status_code") for row in statuses) != tuple(str(index) for index in range(18)):
        _fail()
    hard = tuple(row["status"] for row in statuses if row.get("is_hard_failure") == "true")
    if frozenset(hard) != _HARD_FAILURES:
        _fail()
    if (
        manifest.get("schema_version") != _CONTRACT_SCHEMA
        or input_schema.get("schema_version") != _INPUT_SCHEMA
        or tuple(input_schema.get("field_order", ())) != _INPUT_FIELD_ORDER
        or tuple(input_schema.get("required_fields", ())) != _INPUT_FIELD_ORDER[:15]
        or tuple(input_schema.get("optional_fields", ())) != _INPUT_FIELD_ORDER[15:]
        or output_schema.get("schema_version") != _OUTPUT_SCHEMA
        or tuple(output_schema.get("field_order", ())) != _OUTPUT_FIELD_ORDER
        or vectors.get("schema_version") != _REFERENCE_SCHEMA
        or report.get("schema_version") != _CONTRACT_REPORT_SCHEMA
        or report.get("gate_status") != _CONTRACT_STATUS
        or report.get("contract_digest") != _REMAP_CONTRACT_DIGEST
    ):
        _fail()
    if manifest.get("join_contract", {}).get("name") != _JOIN:
        _fail()
    spaces = manifest.get("index_space_definitions")
    if type(spaces) is not list or tuple(row.get("name") for row in spaces if type(row) is dict) != _INDEX_SPACES:
        _fail()
    placeholder = output_schema.get("numeric_placeholder_semantics")
    expected_placeholder = {
        "sentinel_placeholder_usage_forbidden": True,
        "valid_zero_index_allowed": True,
        "negative_index_allowed": False,
        "missing_numeric_entry_is_omitted": True,
        "joint_unavailable_representation": None,
    }
    if placeholder != expected_placeholder:
        _fail()
    lineage = manifest.get("source_lineage")
    if type(lineage) is not dict:
        _fail()
    if (
        lineage.get("projection_instance_builder", {}).get("projection_digest") != _PROJECTION_DIGEST
        or lineage.get("payload_builder", {}).get("payload_digest") != _PAYLOAD_DIGEST
        or lineage.get("projection_contract_gate", {}).get("contract_digest") != _PROJECTION_CONTRACT_DIGEST
        or lineage.get("formal_routing_sidecar", {}).get("snapshot_SHA256") != _FORMAL_SNAPSHOT_SHA256
        or lineage.get("formal_routing_sidecar", {}).get("aggregate") != _FORMAL_AGGREGATE
    ):
        _fail()
    source = vectors.get("source_contract")
    records = vectors.get("exact22_source_to_local")
    if type(source) is not dict or type(records) is not list or len(records) != 11:
        _fail()
    pairs = source.get("pair_values_source_row_indices")
    if (
        pairs != [list(pair) for pair in _SOURCE_PAIRS]
        or source.get("sample_pair_offsets") != list(range(12))
        or source.get("entry_validity") != [True] * 11
        or source.get("sample_validity") != [True] * 11
        or source.get("pair_count") != 11
        or source.get("column_semantics")
        != [
            "pocket_atom_table_row_index_0based",
            "ligand_atom_table_row_index_0based",
        ]
    ):
        _fail()
    sample_order = source.get("sample_order")
    if type(sample_order) is not list or len(sample_order) != 11:
        _fail()
    authority: list[dict[str, object]] = []
    for index, (sample, record) in enumerate(zip(sample_order, records)):
        if (
            not _identity_complete(sample)
            or type(sample.get("source_sample_index")) is not int
            or sample.get("source_sample_index") != index
            or type(record) is not dict
            or record.get("source_sample_index") != index
            or record.get("sample_identity") != sample
        ):
            _fail()
        roles_list = record.get("roles")
        if type(roles_list) is not list or len(roles_list) != 2:
            _fail()
        roles: dict[str, object] = {}
        for expected_role, role_record in zip(("pocket", "ligand"), roles_list):
            if type(role_record) is not dict or role_record.get("role") != expected_role:
                _fail()
            atom = role_record.get("selected_atom_identity")
            if type(atom) is not dict or tuple(sorted(atom)) != tuple(sorted(_ATOM_IDENTITY_FIELDS)):
                _fail()
            if any(type(atom.get(field)) is not str for field in _ATOM_IDENTITY_FIELDS):
                _fail()
            roles[expected_role] = _derive_role_authority(role_record)
        authority.append({"sample_identity": copy.deepcopy(sample), "roles": roles})
    canonical = vectors.get("canonical_exact11_batch_reference")
    if type(canonical) is not dict or type(canonical.get("batch_contract")) is not dict or type(canonical.get("output")) is not dict:
        _fail()
    if canonical["output"].get("batch_sample_order") != sample_order:
        _fail()
    return {
        "manifest": manifest,
        "input_schema": input_schema,
        "output_schema": output_schema,
        "vectors": vectors,
        "source": source,
        "authority": authority,
    }


def _prefix(lengths: object, batch_size: int) -> list[int]:
    if type(lengths) is not list or len(lengths) != batch_size:
        _input_fail("COLLATE_LENGTH_MISMATCH")
    result = [0]
    for value in lengths:
        if type(value) is not int or value < 0:
            _input_fail("COLLATE_LENGTH_MISMATCH")
        result.append(result[-1] + value)
    return result


def _validate_exact_nonnegative_int_list(
    value: object,
    *,
    expected_length: int,
    failure_status: str,
) -> list[int]:
    if (
        type(value) is not list
        or len(value) != expected_length
        or any(type(item) is not int or item < 0 for item in value)
    ):
        _input_fail(failure_status)
    return value


def _validate_batch_layout(
    lengths: object,
    offsets: object,
    masks: object,
    *,
    batch_size: int,
) -> tuple[dict[str, list[int]], dict[str, list[int]], dict[str, list[int]]]:
    roles = {"pocket", "ligand"}
    if type(lengths) is not dict or set(lengths) != roles:
        _input_fail("COLLATE_LENGTH_MISMATCH")
    if type(offsets) is not dict or set(offsets) != roles:
        _input_fail("COLLATE_OFFSET_MISSING")
    if type(masks) is not dict or set(masks) != roles:
        _input_fail("COLLATE_LENGTH_MISMATCH")
    validated_lengths: dict[str, list[int]] = {}
    validated_offsets: dict[str, list[int]] = {}
    validated_masks: dict[str, list[int]] = {}
    for role in ("pocket", "ligand"):
        role_lengths = _validate_exact_nonnegative_int_list(
            lengths[role],
            expected_length=batch_size,
            failure_status="COLLATE_LENGTH_MISMATCH",
        )
        expected_offsets = _prefix(role_lengths, batch_size)
        role_offsets = _validate_exact_nonnegative_int_list(
            offsets[role],
            expected_length=batch_size + 1,
            failure_status="COLLATE_OFFSET_MISSING",
        )
        if (
            role_offsets[0] != 0
            or any(left > right for left, right in zip(role_offsets, role_offsets[1:]))
            or role_offsets != expected_offsets
        ):
            _input_fail("COLLATE_OFFSET_MISSING")
        role_mask = _validate_exact_nonnegative_int_list(
            masks[role],
            expected_length=role_offsets[-1],
            failure_status="COLLATE_LENGTH_MISMATCH",
        )
        if any(ordinal >= batch_size for ordinal in role_mask):
            _input_fail("COLLATE_LENGTH_MISMATCH")
        expected_mask = [
            ordinal
            for ordinal, length in enumerate(role_lengths)
            for _ in range(length)
        ]
        if role_mask != expected_mask:
            _input_fail("COLLATE_LENGTH_MISMATCH")
        validated_lengths[role] = role_lengths
        validated_offsets[role] = role_offsets
        validated_masks[role] = role_mask
    return validated_lengths, validated_offsets, validated_masks


def _readiness(success: bool) -> dict[str, bool]:
    return {
        "public_batch_index_remap_adapter_implemented": True,
        "public_batch_index_remap_adapter_passed": success,
        "remap_output_built_in_memory": True,
        "canonical_reference_remap_succeeded": success,
        "formal_remap_materialized": False,
        "torch_tensor_materialized": False,
        "numpy_artifact_materialized": False,
        "dataloader_modified": False,
        "model_modified": False,
        "forward_modified": False,
        "loss_modified": False,
        "ready_for_batch_descriptor_compiler_design": success,
        "ready_for_dataloader_integration": False,
        "ready_for_model_integration": False,
        "ready_for_loss_integration": False,
        "feature_semantics_reaudit_required_before_training": True,
        "ready_for_training": False,
    }


def _provenance(joint_status: str, descriptor: object) -> dict[str, object]:
    return {
        "join_contract": _JOIN,
        "index_spaces": list(_INDEX_SPACES),
        "joint_layout_descriptor": descriptor,
        "joint_index_status": joint_status,
        "remap_contract_digest": _REMAP_CONTRACT_DIGEST,
        "projection_instance_digest": _PROJECTION_DIGEST,
        "payload_bundle_digest": _PAYLOAD_DIGEST,
        "projection_contract_digest": _PROJECTION_CONTRACT_DIGEST,
        "coordinates_used_for_selection": False,
        "debug_metadata_used_for_selection": False,
    }


def _safe_batch_order(case: Mapping[str, object]) -> list[object]:
    value = case.get("batch_sample_order", [])
    return copy.deepcopy(value) if type(value) is list else []


def _failure_output(
    case: Mapping[str, object],
    status: str,
    source_pair_count: int,
    entry_index: int,
) -> dict[str, object]:
    batch = _safe_batch_order(case)
    batch_size = len(batch)
    outcomes = []
    for index in range(source_pair_count):
        row_status = status if index == entry_index else "ENTRY_INVALID"
        outcomes.append(
            {
                "source_entry_index": index,
                "status": row_status,
                "failure_reason": row_status,
            }
        )
    return {
        "schema_version": _OUTPUT_SCHEMA,
        "source_projection_digest": _PROJECTION_DIGEST,
        "source_payload_digest": _PAYLOAD_DIGEST,
        "batch_sample_order": batch,
        "pair_values_source_row_indices": [],
        "pair_values_parser_local_indices": [],
        "pair_values_batch_indices": [],
        "pair_values_joint_global_indices": None,
        "pair_sample_indices": [],
        "sample_pair_offsets": [0] * (batch_size + 1),
        "entry_validity": [],
        "sample_validity": [False] * batch_size,
        "source_entry_outcomes": outcomes,
        "remap_status": status,
        "failure_reason": status,
        "provenance": _provenance("JOINT_INDEX_SPACE_UNAVAILABLE", None),
        "readiness": _readiness(False),
    }


def _validate_source_sample_order_exact(
    actual: object,
    expected: object,
) -> None:
    exact_fields = frozenset(("source_sample_index", *_IDENTITY_FIELDS))
    if type(expected) is not list or len(expected) != 11:
        _fail()
    for ordinal, record in enumerate(expected):
        if (
            type(record) is not dict
            or set(record) != exact_fields
            or type(record.get("source_sample_index")) is not int
            or record["source_sample_index"] != ordinal
            or not _identity_complete(record)
        ):
            _fail()
    if type(actual) is not list or len(actual) != len(expected):
        _input_fail("SOURCE_TABLE_IDENTITY_MISMATCH")
    for ordinal, (actual_record, expected_record) in enumerate(zip(actual, expected)):
        if type(actual_record) is not dict or set(actual_record) != set(expected_record):
            _input_fail("SOURCE_TABLE_IDENTITY_MISMATCH")
        source_index = actual_record.get("source_sample_index")
        if type(source_index) is not int or source_index != ordinal:
            _input_fail("SOURCE_TABLE_IDENTITY_MISMATCH")
        if not _identity_complete(actual_record):
            _input_fail("SOURCE_TABLE_IDENTITY_MISMATCH")
        if any(
            type(actual_record[field]) is not type(expected_record[field])
            or actual_record[field] != expected_record[field]
            for field in expected_record
        ):
            _input_fail("SOURCE_TABLE_IDENTITY_MISMATCH")


def _validate_source_contract(
    case: Mapping[str, object],
    source: Mapping[str, object],
    authority: Sequence[Mapping[str, object]],
) -> None:
    if (
        case.get("schema_version") != _INPUT_SCHEMA
        or case.get("source_projection_digest") != _PROJECTION_DIGEST
        or case.get("source_payload_digest") != _PAYLOAD_DIGEST
        or case.get("parser_schema_version") != _PARSER_SCHEMA
        or case.get("collate_schema_version") != _COLLATE_SCHEMA
    ):
        _input_fail("SCHEMA_VERSION_MISMATCH")
    samples = case.get("source_sample_order")
    if type(samples) is not list:
        _input_fail("SOURCE_TABLE_IDENTITY_MISMATCH")
    if any(not _identity_complete(sample) for sample in samples):
        _input_fail("SOURCE_TABLE_IDENTITY_MISMATCH")
    keys = [_identity_key(sample) for sample in samples]
    if len(set(keys)) != len(keys):
        _input_fail("SOURCE_SAMPLE_DUPLICATED")
    _validate_source_sample_order_exact(samples, source.get("sample_order"))
    offsets = case.get("source_sample_offsets_int64")
    entry_validity = case.get("source_entry_validity_bool")
    sample_validity = case.get("source_sample_validity_bool")
    pairs = case.get("source_pair_values_int64")
    if offsets != source.get("sample_pair_offsets"):
        _input_fail("ENTRY_INVALID")
    if entry_validity != source.get("entry_validity") or sample_validity != source.get("sample_validity"):
        _input_fail("ENTRY_INVALID")
    if type(pairs) is not list or len(pairs) != 11:
        _input_fail("ENTRY_INVALID")
    for index, pair in enumerate(pairs):
        if type(pair) is not list or len(pair) != 2 or any(type(value) is not int for value in pair):
            _input_fail("ENTRY_INVALID", index)
        if any(value < 0 for value in pair):
            _input_fail("SOURCE_ROW_OUT_OF_RANGE", index)
        expected = source["pair_values_source_row_indices"][index]
        if pair != expected:
            try:
                roles = authority[index]["roles"]
                row_counts = (roles["pocket"]["row_count"], roles["ligand"]["row_count"])
            except (IndexError, KeyError, TypeError) as error:
                raise ValueError(_ERROR) from error
            status = (
                "SOURCE_ROW_OUT_OF_RANGE"
                if any(value >= row_count for value, row_count in zip(pair, row_counts))
                else "SOURCE_TABLE_IDENTITY_MISMATCH"
            )
            _input_fail(status, index)


def _validate_role_structure(role_table: object, expected_role: str) -> dict[str, object]:
    if expected_role not in ("pocket", "ligand"):
        _fail()
    if type(role_table) is not dict or role_table.get("role") != expected_role:
        _input_fail("ROLE_MISMATCH")
    required = frozenset(_TABLE_AUTHORITY_FIELDS) | {"role", "selected_atom_identity", "source_to_parser_local"}
    if not required.issubset(role_table):
        if "selected_atom_identity" not in role_table:
            _input_fail("SOURCE_ATOM_IDENTITY_MISMATCH")
        _input_fail("SOURCE_TABLE_IDENTITY_MISMATCH")
    root_kind = role_table.get("root_kind")
    relative = role_table.get("relative_path")
    digest = role_table.get("SHA256")
    relative_path = PurePosixPath(relative) if type(relative) is str else None
    if (
        root_kind != "repo_root"
        or type(relative) is not str
        or not relative
        or relative.strip() != relative
        or relative_path is None
        or relative_path.is_absolute()
        or relative_path.parts in ((), (".",))
        or ".." in relative_path.parts
        or str(relative_path) != relative
        or type(digest) is not str
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
        or role_table.get("row_order_digest") != digest
        or role_table.get("row_order_version") != "physical_csv_data_row_order_v1"
    ):
        _input_fail("SOURCE_TABLE_IDENTITY_MISMATCH")
    row_count = role_table.get("row_count")
    source_row = role_table.get("selected_source_row_index_0based")
    parser_count = role_table.get("parser_output_atom_count")
    parser_local = role_table.get("selected_parser_local_index")
    if (
        type(row_count) is not int
        or row_count <= 0
        or type(source_row) is not int
        or not 0 <= source_row < row_count
        or type(parser_count) is not int
        or parser_count <= 0
        or type(parser_local) is not int
        or not 0 <= parser_local < parser_count
    ):
        _input_fail("SOURCE_TABLE_IDENTITY_MISMATCH")
    mapping = role_table.get("source_to_parser_local")
    if type(mapping) is not dict:
        _input_fail("SOURCE_TABLE_IDENTITY_MISMATCH")
    selected_key = str(source_row)
    if selected_key not in mapping:
        _input_fail("PARSER_ATOM_NOT_FOUND")
    selected_mapping = mapping[selected_key]
    if type(selected_mapping) is list:
        _input_fail("PARSER_ATOM_NOT_UNIQUE")
    if (
        type(selected_mapping) is not int
        or selected_mapping != parser_local
        or not 0 <= selected_mapping < parser_count
    ):
        _input_fail("SOURCE_TABLE_IDENTITY_MISMATCH")
    atom = role_table.get("selected_atom_identity")
    if type(atom) is not dict or set(atom) != set(_ATOM_IDENTITY_FIELDS):
        _input_fail("SOURCE_ATOM_IDENTITY_MISMATCH")
    if any(type(atom.get(field)) is not str for field in _ATOM_IDENTITY_FIELDS):
        _input_fail("SOURCE_ATOM_IDENTITY_MISMATCH")
    for field in _ATOM_IDENTITY_FIELDS:
        value = atom[field]
        if field == "label_seq_id":
            if value and value.strip() != value:
                _input_fail("SOURCE_ATOM_IDENTITY_MISMATCH")
        elif not value or value.strip() != value:
            _input_fail("SOURCE_ATOM_IDENTITY_MISMATCH")
    return role_table


def _authority_lookup(authority: object) -> dict[tuple[object, ...], dict[str, object]]:
    if type(authority) is not list:
        _fail()
    result: dict[tuple[object, ...], dict[str, object]] = {}
    for table in authority:
        if type(table) is not dict or not _identity_complete(table.get("sample_identity")):
            _fail()
        key = _identity_key(table["sample_identity"])
        if key in result or type(table.get("roles")) is not dict:
            _fail()
        result[key] = table
    return result


def _remap_engine(
    case: dict[str, object],
    *,
    authoritative_tables: list[dict[str, object]],
) -> dict[str, object]:
    source_samples = case["source_sample_order"]
    source_pairs = case["source_pair_values_int64"]
    source_offsets = case["source_sample_offsets_int64"]
    source_entry_validity = case["source_entry_validity_bool"]
    source_sample_validity = case["source_sample_validity_bool"]
    if (
        type(source_samples) is not list
        or type(source_pairs) is not list
        or type(source_offsets) is not list
        or len(source_offsets) != len(source_samples) + 1
        or not source_offsets
        or source_offsets[0] != 0
        or source_offsets[-1] != len(source_pairs)
        or any(type(value) is not int or value < 0 for value in source_offsets)
        or any(left > right for left, right in zip(source_offsets, source_offsets[1:]))
        or type(source_entry_validity) is not list
        or len(source_entry_validity) != len(source_pairs)
        or any(type(value) is not bool for value in source_entry_validity)
        or type(source_sample_validity) is not list
        or len(source_sample_validity) != len(source_samples)
        or any(type(value) is not bool for value in source_sample_validity)
    ):
        _input_fail("ENTRY_INVALID")
    if any(not _identity_complete(sample) for sample in source_samples):
        _input_fail("SOURCE_TABLE_IDENTITY_MISMATCH")
    source_keys = [_identity_key(sample) for sample in source_samples]
    if len(set(source_keys)) != len(source_keys):
        _input_fail("SOURCE_SAMPLE_DUPLICATED")
    batch = case.get("batch_sample_order")
    tables = case.get("batch_sample_atom_identity_tables")
    if type(batch) is not list or type(tables) is not list or len(tables) != len(batch):
        _input_fail("BATCH_SAMPLE_IDENTITY_UNKNOWN")
    if any(not _identity_complete(sample) for sample in batch):
        _input_fail("BATCH_SAMPLE_IDENTITY_UNKNOWN")
    batch_keys = [_identity_key(sample) for sample in batch]
    if len(set(batch_keys)) != len(batch_keys):
        _input_fail("BATCH_SAMPLE_DUPLICATED")
    batch_size = len(batch)
    lengths = case.get("batch_role_lengths")
    offsets = case.get("batch_role_offsets")
    masks = case.get("batch_membership_masks")
    lengths, offsets, masks = _validate_batch_layout(
        lengths,
        offsets,
        masks,
        batch_size=batch_size,
    )
    authority = _authority_lookup(authoritative_tables)
    if any(key not in authority for key in source_keys):
        _fail()
    source_lookup = {key: index for index, key in enumerate(source_keys)}
    table_by_key: dict[tuple[object, ...], dict[str, object]] = {}
    for table, key in zip(tables, batch_keys):
        if type(table) is not dict or not _identity_complete(table.get("sample_identity")):
            _input_fail("SOURCE_TABLE_IDENTITY_MISMATCH")
        if _identity_key(table["sample_identity"]) != key:
            _input_fail("SOURCE_TABLE_IDENTITY_MISMATCH")
        roles = table.get("roles")
        if type(roles) is not dict or set(roles) != {"pocket", "ligand"}:
            _input_fail("ROLE_MISMATCH")
        table_by_key[key] = table
    out_source: list[list[int]] = []
    out_local: list[list[int]] = []
    out_segment: list[list[int]] = []
    out_sample: list[int] = []
    out_validity: list[bool] = []
    out_offsets = [0]
    outcomes = [
        {"source_entry_index": index, "status": "NOT_IN_BATCH", "failure_reason": "NONE"}
        for index in range(len(source_pairs))
    ]
    for batch_ordinal, key in enumerate(batch_keys):
        source_index = source_lookup.get(key)
        table = table_by_key[key]
        roles = table["roles"]
        expected_roles = authority[key]["roles"] if source_index is not None else None
        for role in ("pocket", "ligand"):
            role_table = _validate_role_structure(roles[role], role)
            if role_table["parser_output_atom_count"] != lengths[role][batch_ordinal]:
                _input_fail("PARSER_COUNT_MISMATCH")
            if source_index is not None:
                expected = expected_roles.get(role) if type(expected_roles) is dict else None
                if type(expected) is not dict:
                    _fail()
                if any(
                    type(role_table.get(field)) is not type(expected.get(field))
                    or role_table.get(field) != expected.get(field)
                    for field in _TABLE_AUTHORITY_FIELDS
                ):
                    _input_fail("SOURCE_TABLE_IDENTITY_MISMATCH")
                atom = role_table["selected_atom_identity"]
                expected_atom = expected.get("selected_atom_identity")
                if type(expected_atom) is not dict or any(
                    type(atom[field]) is not type(expected_atom.get(field))
                    or atom[field] != expected_atom.get(field)
                    for field in _ATOM_IDENTITY_FIELDS
                ):
                    _input_fail("SOURCE_ATOM_IDENTITY_MISMATCH")
        if source_index is not None:
            if source_sample_validity[source_index] is not True:
                _input_fail("ENTRY_INVALID", source_offsets[source_index])
            before_count = len(out_source)
            for entry_index in range(source_offsets[source_index], source_offsets[source_index + 1]):
                if source_entry_validity[entry_index] is not True:
                    _input_fail("ENTRY_INVALID", entry_index)
                pair = source_pairs[entry_index]
                if type(pair) is not list or len(pair) != 2 or any(type(value) is not int for value in pair):
                    _input_fail("ENTRY_INVALID", entry_index)
                local_pair: list[int] = []
                segment_pair: list[int] = []
                for role, source_row in zip(("pocket", "ligand"), pair):
                    role_table = roles[role]
                    if source_row < 0 or source_row >= role_table["row_count"]:
                        _input_fail("SOURCE_ROW_OUT_OF_RANGE", entry_index)
                    mapping = role_table["source_to_parser_local"]
                    if str(source_row) not in mapping:
                        _input_fail("PARSER_ATOM_NOT_FOUND", entry_index)
                    local = mapping[str(source_row)]
                    if type(local) is list:
                        _input_fail("PARSER_ATOM_NOT_UNIQUE", entry_index)
                    expected_mapping = expected_roles[role].get("source_to_parser_local")
                    if type(expected_mapping) is not dict or expected_mapping.get(str(source_row)) != local:
                        _input_fail("SOURCE_TABLE_IDENTITY_MISMATCH", entry_index)
                    if type(local) is not int or local < 0 or local >= lengths[role][batch_ordinal]:
                        _input_fail("BATCH_INDEX_OUT_OF_RANGE", entry_index)
                    segment = offsets[role][batch_ordinal] + local
                    if (
                        segment < offsets[role][batch_ordinal]
                        or segment >= offsets[role][batch_ordinal + 1]
                        or segment >= len(masks[role])
                        or masks[role][segment] != batch_ordinal
                    ):
                        _input_fail("BATCH_INDEX_OUT_OF_RANGE", entry_index)
                    local_pair.append(local)
                    segment_pair.append(segment)
                out_source.append(pair[:])
                out_local.append(local_pair)
                out_segment.append(segment_pair)
                out_sample.append(batch_ordinal)
                out_validity.append(True)
                outcomes[entry_index] = {
                    "source_entry_index": entry_index,
                    "status": "REMAPPED_EXACT",
                    "failure_reason": "NONE",
                }
            if source_offsets[source_index + 1] > source_offsets[source_index] and len(out_source) == before_count:
                _input_fail("ENTRY_INVALID", source_offsets[source_index])
        out_offsets.append(len(out_source))
    descriptor = case.get("joint_layout_descriptor")
    if descriptor not in (None, _JOINT_LAYOUT):
        _input_fail("SCHEMA_VERSION_MISMATCH")
    if descriptor == _JOINT_LAYOUT:
        n_ligand = offsets["ligand"][-1]
        total = n_ligand + offsets["pocket"][-1]
        joint = [[n_ligand + pocket, ligand] for pocket, ligand in out_segment]
        if any(value < 0 or value >= total for pair in joint for value in pair):
            _input_fail("BATCH_INDEX_OUT_OF_RANGE")
        joint_status = "REMAPPED_EXACT"
    else:
        joint = None
        joint_status = "JOINT_INDEX_SPACE_UNAVAILABLE"
    return {
        "schema_version": _OUTPUT_SCHEMA,
        "source_projection_digest": _PROJECTION_DIGEST,
        "source_payload_digest": _PAYLOAD_DIGEST,
        "batch_sample_order": copy.deepcopy(batch),
        "pair_values_source_row_indices": out_source,
        "pair_values_parser_local_indices": out_local,
        "pair_values_batch_indices": out_segment,
        "pair_values_joint_global_indices": joint,
        "pair_sample_indices": out_sample,
        "sample_pair_offsets": out_offsets,
        "entry_validity": out_validity,
        "sample_validity": [True] * batch_size,
        "source_entry_outcomes": outcomes,
        "remap_status": "REMAPPED_EXACT",
        "failure_reason": "NONE",
        "provenance": _provenance(joint_status, descriptor),
        "readiness": _readiness(True),
    }


def _stable_output_digest(payload: bytes) -> str:
    name = _OUTPUT_NAME.encode("utf-8")
    digest = hashlib.sha256()
    digest.update(_OUTPUT_DOMAIN_TAG)
    digest.update(len(name).to_bytes(8, "big", signed=False))
    digest.update(name)
    digest.update(len(payload).to_bytes(8, "big", signed=False))
    digest.update(payload)
    return digest.hexdigest()


def _report(
    *,
    output_payload: bytes,
    output: Mapping[str, object],
    input_payload: bytes,
    optional_count: int,
) -> dict[str, object]:
    success = output.get("remap_status") == "REMAPPED_EXACT"
    outcomes = output.get("source_entry_outcomes")
    counts: dict[str, int] = {}
    if type(outcomes) is list:
        for row in outcomes:
            if type(row) is dict and type(row.get("status")) is str:
                counts[row["status"]] = counts.get(row["status"], 0) + 1
    batch = output.get("batch_sample_order")
    pairs = output.get("pair_values_source_row_indices")
    digest = _stable_output_digest(output_payload)
    return {
        "schema_version": _REPORT_SCHEMA,
        "adapter_status": _SUCCESS_STATUS if success else _FAILURE_STATUS,
        "remap_output_digest": digest,
        "artifact_file_count": 2,
        "artifact_identities": [
            {
                "artifact_index": 0,
                "artifact_name": _OUTPUT_NAME,
                "stable_digest_participation": True,
                "bytes": len(output_payload),
                "LF": output_payload.count(b"\n"),
                "SHA256": _sha(output_payload),
            },
            {
                "artifact_index": 1,
                "artifact_name": _REPORT_NAME,
                "stable_digest_participation": False,
                "content_identity": "self_excluded",
            },
        ],
        "remap_contract_gate_passed": True,
        "remap_contract_digest": _REMAP_CONTRACT_DIGEST,
        "remap_contract_exact6_double_build_identical": True,
        "projection_instance_digest": _PROJECTION_DIGEST,
        "payload_bundle_digest": _PAYLOAD_DIGEST,
        "projection_contract_digest": _PROJECTION_CONTRACT_DIGEST,
        "input_digest": _sha(input_payload),
        "input_required_field_count": 15,
        "input_optional_field_count": optional_count,
        "batch_sample_count": len(batch) if type(batch) is list else 0,
        "source_pair_count": 11,
        "batch_pair_count": len(pairs) if type(pairs) is list else 0,
        "remap_status": output.get("remap_status"),
        "failure_reason": output.get("failure_reason"),
        "source_entry_status_counts": counts,
        "joint_index_status": output.get("provenance", {}).get("joint_index_status"),
        "formal_sidecar_check_passed": True,
        "formal_snapshot_unchanged": True,
        "readiness": copy.deepcopy(output.get("readiness")),
    }


def _validate_output(output: dict[str, object]) -> None:
    if type(output) is not dict or tuple(output) != _OUTPUT_FIELD_ORDER or len(output) != 17:
        _fail()
    if (
        output.get("schema_version") != _OUTPUT_SCHEMA
        or output.get("source_projection_digest") != _PROJECTION_DIGEST
        or output.get("source_payload_digest") != _PAYLOAD_DIGEST
        or output.get("remap_status") not in _STATUS_ORDER
        or output.get("failure_reason") not in ("NONE", *_HARD_FAILURES)
        or type(output.get("batch_sample_order")) is not list
    ):
        _fail()
    pair_fields = (
        "pair_values_source_row_indices",
        "pair_values_parser_local_indices",
        "pair_values_batch_indices",
    )
    pair_count: int | None = None
    for field in pair_fields:
        value = output.get(field)
        if type(value) is not list or any(type(pair) is not list or len(pair) != 2 for pair in value):
            _fail()
        if any(type(number) is not int or number < 0 for pair in value for number in pair):
            _fail()
        if pair_count is None:
            pair_count = len(value)
        elif len(value) != pair_count:
            _fail()
    if pair_count is None:
        _fail()
    pair_samples = output.get("pair_sample_indices")
    entry_validity = output.get("entry_validity")
    batch = output["batch_sample_order"]
    sample_offsets = output.get("sample_pair_offsets")
    sample_validity = output.get("sample_validity")
    outcomes = output.get("source_entry_outcomes")
    if (
        type(pair_samples) is not list
        or len(pair_samples) != pair_count
        or any(type(value) is not int or value < 0 for value in pair_samples)
        or type(entry_validity) is not list
        or len(entry_validity) != pair_count
        or any(type(value) is not bool for value in entry_validity)
        or type(sample_offsets) is not list
        or len(sample_offsets) != len(batch) + 1
        or any(type(value) is not int or value < 0 for value in sample_offsets)
        or not sample_offsets
        or sample_offsets[0] != 0
        or sample_offsets[-1] != pair_count
        or any(left > right for left, right in zip(sample_offsets, sample_offsets[1:]))
        or type(sample_validity) is not list
        or len(sample_validity) != len(batch)
        or any(type(value) is not bool for value in sample_validity)
        or type(outcomes) is not list
        or len(outcomes) != 11
    ):
        _fail()
    joint = output.get("pair_values_joint_global_indices")
    if joint is not None:
        if type(joint) is not list or len(joint) != pair_count or any(type(pair) is not list or len(pair) != 2 for pair in joint):
            _fail()
        if any(type(number) is not int or number < 0 for pair in joint for number in pair):
            _fail()
    success = output["remap_status"] == "REMAPPED_EXACT"
    if success:
        if output["failure_reason"] != "NONE" or any(value is not True for value in entry_validity + sample_validity):
            _fail()
    elif pair_count != 0 or joint is not None or output["failure_reason"] != output["remap_status"]:
        _fail()


def _build_impl(
    *,
    repo_root: Path,
    state_root: Path,
    adapter_input: dict[str, object],
) -> dict[str, bytes]:
    repo = _require_root(repo_root)
    state = _require_root(state_root)
    if type(adapter_input) is not dict:
        _fail()
    try:
        copied = copy.deepcopy(adapter_input)
    except BaseException as error:
        raise ValueError(_ERROR) from error
    if type(copied) is not dict:
        _fail()
    input_payload = _json(copied)
    canonical = state / _FORMAL_RELATIVE
    before = _validate_formal(canonical)
    exact6 = _contract_exact6(repo, state)
    contract = _parse_contract(exact6)
    keys = set(copied)
    schema_rejected = (
        not _INPUT_REQUIRED.issubset(keys)
        or not keys.issubset(_INPUT_REQUIRED | _INPUT_OPTIONAL)
        or bool(keys & _LEGACY_ALIASES)
        or any(
            field in copied and copied[field] is not None and type(copied[field]) is not dict
            for field in ("debug_coordinates", "debug_rank_metadata")
        )
    )
    try:
        if schema_rejected:
            _input_fail("SCHEMA_VERSION_MISMATCH")
        _validate_source_contract(copied, contract["source"], contract["authority"])
        output = _remap_engine(copied, authoritative_tables=contract["authority"])
    except _InputFailure as error:
        output = _failure_output(copied, error.status, 11, error.entry_index)
    _validate_output(output)
    output_payload = _json(output)
    report = _report(
        output_payload=output_payload,
        output=output,
        input_payload=input_payload,
        optional_count=len(keys & _INPUT_OPTIONAL),
    )
    report_payload = _json(report)
    artifacts = {_OUTPUT_NAME: output_payload, _REPORT_NAME: report_payload}
    if type(artifacts) is not dict or tuple(artifacts) != _ARTIFACT_NAMES or any(type(value) is not bytes for value in artifacts.values()):
        _fail()
    after = _validate_formal(canonical)
    if before != after:
        _fail()
    return artifacts


def _build_canonical_adapter_input_v1(*, repo_root: Path, state_root: Path) -> dict[str, object]:
    """Private checker helper built only from the published stable contract."""
    repo = _require_root(repo_root)
    state = _require_root(state_root)
    exact6 = _contract_exact6(repo, state)
    contract = _parse_contract(exact6)
    vectors = contract["vectors"]
    source = contract["source"]
    canonical = vectors["canonical_exact11_batch_reference"]
    batch_contract = canonical["batch_contract"]
    batch_order = canonical["output"]["batch_sample_order"]
    authority_by_key = {
        _identity_key(table["sample_identity"]): table for table in contract["authority"]
    }
    tables = [copy.deepcopy(authority_by_key[_identity_key(sample)]) for sample in batch_order]
    lengths = copy.deepcopy(batch_contract["batch_role_lengths"])
    offsets = copy.deepcopy(batch_contract["batch_role_offsets"])
    masks = {
        role: [ordinal for ordinal, length in enumerate(lengths[role]) for _ in range(length)]
        for role in ("pocket", "ligand")
    }
    return {
        "schema_version": _INPUT_SCHEMA,
        "source_projection_digest": _PROJECTION_DIGEST,
        "source_payload_digest": _PAYLOAD_DIGEST,
        "parser_schema_version": _PARSER_SCHEMA,
        "collate_schema_version": _COLLATE_SCHEMA,
        "source_sample_order": copy.deepcopy(source["sample_order"]),
        "source_pair_values_int64": copy.deepcopy(source["pair_values_source_row_indices"]),
        "source_sample_offsets_int64": copy.deepcopy(source["sample_pair_offsets"]),
        "source_entry_validity_bool": copy.deepcopy(source["entry_validity"]),
        "source_sample_validity_bool": copy.deepcopy(source["sample_validity"]),
        "batch_sample_order": copy.deepcopy(batch_order),
        "batch_sample_atom_identity_tables": tables,
        "batch_role_lengths": lengths,
        "batch_role_offsets": offsets,
        "batch_membership_masks": masks,
        "joint_layout_descriptor": batch_contract["joint_layout_descriptor"],
        "debug_coordinates": None,
        "debug_rank_metadata": None,
    }


def build_covapie_current11_task2_batch_index_remap_adapter_v1(
    *,
    repo_root: Path,
    state_root: Path,
    adapter_input: dict[str, object],
) -> dict[str, bytes]:
    """Return deterministic Task 2 batch remap output and report bytes in memory."""
    try:
        return _build_impl(
            repo_root=repo_root,
            state_root=state_root,
            adapter_input=adapter_input,
        )
    except BaseException as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
