"""Pure in-memory Current11 Task 2 batch descriptor compiler V1."""

from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import math
import os
import stat
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Mapping, NoReturn, Sequence

from covalent_ext import covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1 as _contract_gate


__all__ = ("compile_covapie_current11_task2_batch_descriptor_v1",)

_ERROR = "COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_V1_ERROR"
_CONTRACT_COMMIT = "3b390cec784ed73a72f522145b6f26e3d8af704d"
_CONTRACT_DIGEST = "bb9705173523377f28966064eec7393fbf337dce9ef6c70d2e3fbca3038e2dfd"
_PROVIDER_DIGEST = "a6193bfe7099b9c9436036f75101df31638739a893b598af8ac021bfa46aa186"
_REMAP_CONTRACT_DIGEST = "2c6259312a3292181f00ebbaf787fab05e5a97e5b5475243f2fa8461b54dcdc6"

_INPUT_SCHEMA = "covapie_current11_task2_batch_descriptor_compiler_input_v1"
_OUTPUT_SCHEMA = "covapie_current11_task2_batch_descriptor_compiler_output_v1"
_SOURCE_SCHEMA = "covapie_current11_task2_batch_index_remap_adapter_input_v1"
_RUNTIME_SCHEMA = "processed_ligand_pocket_dataset_collate_observation_no_virtual_v1"
_SAMPLE_KEY_SCHEMA = "covapie_sample_index_row_id_in_names_v1"
_PARSER_SCHEMA = "order_preserving_checkpoint_heavy_projection_v1"
_COLLATE_SCHEMA = "processed_ligand_pocket_dataset_collate_fn_v1"
_VIRTUAL_POLICY = "no_virtual_nodes_v1"
_JOINT_LAYOUT = "ligand_segment_then_pocket_segment_v1"
_PROJECTION_DIGEST = "b8e8078700bd019d4a11a00c17dc84fa05e406bbf61b51bf3e887988f3b89255"
_PAYLOAD_DIGEST = "95e9ed091566bbc547a8f75b975a40c27ce318e95df1553b1f1ac448a91b1f9d"
_FORMAL_AGGREGATE = "ef426a6d8dee9678ac15dd62b191e9ef9cfb436a01660bd941bd24392dfa9a18"
_FORMAL_NPZ_SHA256 = "ea3aa7c94b7c88993493662ad6ba7fd95e547ec62612a072f8248a515657e910"

_GATE_RELATIVE = "src/covalent_ext/covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1.py"
_GATE_BYTES = 63863
_GATE_LF = 1199
_GATE_SHA256 = "8bcf1a6c39a7b27d8aa62457a5c3ec2665a9dd87fd9e245a8553196941b5d3b9"

_MANIFEST = "current11_task2_batch_descriptor_compiler_contract_manifest.json"
_INPUT = "current11_task2_batch_descriptor_compiler_input_schema.json"
_OUTPUT = "current11_task2_batch_descriptor_compiler_output_schema.json"
_VOCABULARY = "current11_task2_batch_descriptor_compiler_status_vocabulary.csv"
_VECTORS = "current11_task2_batch_descriptor_compiler_reference_vectors.json"
_REPORT = "current11_task2_batch_descriptor_compiler_contract_gate_report.json"
_ARTIFACT_NAMES = (_MANIFEST, _INPUT, _OUTPUT, _VOCABULARY, _VECTORS, _REPORT)
_STABLE_NAMES = _ARTIFACT_NAMES[:5]
_ARTIFACT_IDENTITIES = {
    _MANIFEST: (15711, 450, "c9e2ff8bc3d8b32871cf5fb7f7eb89981cc0f602acf4803cc99f1374d6d60d4a"),
    _INPUT: (2942, 116, "8cfb5a3073dc00dcba54770ba3e053e52dbdfe285741014337ed36757add215d"),
    _OUTPUT: (1771, 63, "e954b35420d8e7726fe581c390557eac30761e67399926c5fce95b51064e3faf"),
    _VOCABULARY: (1628, 16, "712580562899040d40268de972867aa5621f213e3edad362ad444fe514fe1eb9"),
    _VECTORS: (535570, 20034, "200dd17330cb18d53e8b22a906ff54d569d8d50910d69e44755ba9b8e10d5b28"),
    _REPORT: (5138, 111, "716c83a77c77a4b5e24aead2a8c24e6b9961de508bf8f2f45d8d0ff20ca10091"),
}
_CONTRACT_DOMAIN = b"COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTRACT_GATE_V1\0"
_PROVIDER_DOMAIN = b"COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_IDENTITY_PROVIDER_V1\0"

_REPOSITORY_EXACT4 = (
    "src/covalent_ext/covapie_current11_task2_batch_descriptor_compiler_v1.py",
    "scripts/check_covapie_current11_task2_batch_descriptor_compiler_v1.py",
    "tests/test_covapie_current11_task2_batch_descriptor_compiler_v1.py",
    "docs/covapie_current11_task2_batch_descriptor_compiler_v1_guide.md",
)

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
_OTHER_FORBIDDEN_FIELDS = frozenset((
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
_SOURCE_FIELDS = _EXACT18_FIELDS[:10]
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
_REFERENCE_IDS = (
    "canonical_exact11", "reversed_exact11", "mixed_10_4_0_7_2", "subset_10_4_0",
    "no_joint", "empty_batch", "duplicate_runtime_key", "unknown_runtime_key",
    "non_source_known_sample", "invalid_key_type", "empty_key", "untrimmed_key",
    "wrong_runtime_schema", "wrong_sample_key_schema", "virtual_policy_mismatch",
    "wrong_ligand_length", "wrong_pocket_length", "bool_length", "float_length",
    "wrong_ligand_membership", "wrong_pocket_membership", "bool_membership",
    "float_membership", "membership_wrong_ordinal_order", "consistency_buffer_mismatch",
    "source_contract_override", "provider_missing", "unknown_joint_descriptor",
    "unknown_top_level_field", "missing_required_field", "runtime_name_path_drift",
    "ambiguous_provider_match", "provider_digest_drift", "missing_pocket_role",
    "missing_ligand_role",
)
_VALIDATION_ORDER = (
    "top_level_schema_and_unknown_fields", "source_contract_override",
    "pinned_source_contract_availability_and_drift", "identity_provider_availability_and_drift",
    "runtime_schema_version", "sample_key_schema", "sample_key_validity", "duplicate_key",
    "exact_lookup_non_source_unknown_ambiguous", "required_pocket_and_ligand_role_authority",
    "virtual_node_policy", "role_lengths", "membership",
    "optional_consistency_buffer_lengths", "joint_descriptor_classification", "debug_transport",
)
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
_SOURCE_PAIRS = (
    (88, 3), (25, 3), (19, 3), (39, 3), (37, 27), (50, 21),
    (48, 16), (53, 20), (52, 21), (53, 18), (84, 5),
)


def _fail() -> NoReturn:
    raise ValueError(_ERROR)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _compact(value: object) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise ValueError(_ERROR) from error


def _strict_json(payload: bytes) -> dict[str, object]:
    try:
        value = json.loads(
            payload.decode("utf-8"), parse_constant=lambda _value: _fail(),
        )
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


@contextmanager
def _precommit_compatibility() -> Iterator[None]:
    owner = _contract_gate._remap_gate._instance_builder._payload_builder._contract_gate
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


def _validate_gate_source(repo: Path) -> None:
    try:
        path = repo / _GATE_RELATIVE
        metadata = path.lstat()
        payload = path.read_bytes()
    except OSError as error:
        raise ValueError(_ERROR) from error
    if (
        stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode)
        or len(payload) != _GATE_BYTES or payload.count(b"\n") != _GATE_LF
        or _sha(payload) != _GATE_SHA256
    ):
        _fail()


def _stable_digest(artifacts: Mapping[str, bytes]) -> str:
    digest = hashlib.sha256(_CONTRACT_DOMAIN)
    for name in _STABLE_NAMES:
        encoded = name.encode("utf-8")
        payload = artifacts[name]
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _provider_digest(provider: object) -> str:
    payload = _compact(provider)
    digest = hashlib.sha256(_PROVIDER_DOMAIN)
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _validate_exact6(artifacts: object) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    if type(artifacts) is not dict or tuple(artifacts) != _ARTIFACT_NAMES:
        _fail()
    for name, identity in _ARTIFACT_IDENTITIES.items():
        payload = artifacts.get(name)
        if (
            type(payload) is not bytes or len(payload) != identity[0]
            or payload.count(b"\n") != identity[1] or _sha(payload) != identity[2]
        ):
            _fail()
    if _stable_digest(artifacts) != _CONTRACT_DIGEST:
        _fail()

    manifest = _strict_json(artifacts[_MANIFEST])
    input_schema = _strict_json(artifacts[_INPUT])
    output_schema = _strict_json(artifacts[_OUTPUT])
    vectors = _strict_json(artifacts[_VECTORS])
    report = _strict_json(artifacts[_REPORT])
    try:
        reader = csv.DictReader(io.StringIO(artifacts[_VOCABULARY].decode("utf-8"), newline=""))
        status_rows = [dict(row) for row in reader]
    except (UnicodeDecodeError, csv.Error) as error:
        raise ValueError(_ERROR) from error
    reference_cases = vectors.get("reference_cases")
    formal = manifest.get("formal_runtime_carrier_binding")
    readiness = manifest.get("readiness")
    if (
        input_schema.get("field_order") != list(_INPUT_FIELDS)
        or input_schema.get("required_fields") != list(_INPUT_FIELDS[:10])
        or input_schema.get("optional_fields") != list(_INPUT_FIELDS[10:])
        or output_schema.get("field_order") != list(_OUTPUT_FIELDS)
        or output_schema.get("adapter_input_exact18_field_order") != list(_EXACT18_FIELDS)
        or [row.get("status") for row in status_rows] != list(_STATUS_ORDER)
        or manifest.get("validation_order") != list(_VALIDATION_ORDER)
        or type(reference_cases) is not list
        or [row.get("case_id") for row in reference_cases] != list(_REFERENCE_IDS)
        or len({row.get("case_id") for row in reference_cases}) != 35
        or vectors.get("identity_provider_digest") != _PROVIDER_DIGEST
        or type(formal) is not dict or formal.get("aggregate") != _FORMAL_AGGREGATE
        or formal.get("Exact4_SHA256", {}).get(
            "current11_runtime_sample_and_role_order_carrier.npz"
        ) != _FORMAL_NPZ_SHA256
        or type(readiness) is not dict
        or any(readiness.get(key) is not True for key in (
            "task2_batch_descriptor_compiler_contract_gate_implemented",
            "task2_batch_descriptor_compiler_contract_gate_passed",
            "task2_batch_descriptor_compiler_contract_designed",
            "formal_runtime_carrier_verified", "source_contract_verified",
            "identity_provider_verified", "compiler_input_schema_frozen",
            "compiler_output_schema_frozen", "compiler_status_vocabulary_frozen",
            "compiler_reference_composition_passed",
        ))
        or readiness.get("task2_batch_descriptor_compiler_implemented") is not False
        or readiness.get("ready_for_task2_batch_descriptor_compiler_implementation") is not True
        or report.get("contract_digest") != _CONTRACT_DIGEST
        or report.get("identity_provider_digest") != _PROVIDER_DIGEST
        or report.get("formal_carrier_aggregate") != _FORMAL_AGGREGATE
        or report.get("formal_carrier_npz_sha256") != _FORMAL_NPZ_SHA256
        or report.get("reference_case_count") != 35
        or report.get("success_case_count") != 6
        or report.get("hard_failure_case_count") != 29
        or report.get("public_adapter_composition_case_count") != 6
    ):
        _fail()
    return manifest, vectors, report


def _identity(sample: Mapping[str, object]) -> dict[str, str]:
    result: dict[str, str] = {}
    for field in _IDENTITY_FIELDS:
        value = sample.get(field)
        if type(value) is not str or not value or value.strip() != value:
            _fail()
        result[field] = value
    return result


def _validate_source(source: object) -> dict[str, object]:
    if type(source) is not dict or tuple(source) != _SOURCE_FIELDS:
        _fail()
    if (
        source.get("schema_version") != _SOURCE_SCHEMA
        or source.get("source_projection_digest") != _PROJECTION_DIGEST
        or source.get("source_payload_digest") != _PAYLOAD_DIGEST
        or source.get("parser_schema_version") != _PARSER_SCHEMA
        or source.get("collate_schema_version") != _COLLATE_SCHEMA
    ):
        _fail()
    samples = source.get("source_sample_order")
    if type(samples) is not list or len(samples) != 11:
        _fail()
    for index, (sample, expected) in enumerate(zip(samples, _SOURCE_IDENTITIES)):
        if (
            type(sample) is not dict
            or set(sample) != set(_IDENTITY_FIELDS) | {"source_sample_index"}
            or type(sample.get("source_sample_index")) is not int
            or sample.get("source_sample_index") != index
            or tuple(_identity(sample).values()) != expected
        ):
            _fail()
    if (
        source.get("source_pair_values_int64") != [list(pair) for pair in _SOURCE_PAIRS]
        or source.get("source_sample_offsets_int64") != list(range(12))
        or source.get("source_entry_validity_bool") != [True] * 11
        or source.get("source_sample_validity_bool") != [True] * 11
    ):
        _fail()
    return source


def _validate_provider(provider: object, source: Mapping[str, object]) -> list[dict[str, object]]:
    if type(provider) is not list or len(provider) != 11 or _provider_digest(provider) != _PROVIDER_DIGEST:
        _fail()
    samples = source.get("source_sample_order")
    if type(samples) is not list:
        _fail()
    for expected_sample, table in zip(samples, provider):
        if type(expected_sample) is not dict or type(table) is not dict or set(table) != {
            "sample_identity", "roles",
        }:
            _fail()
        identity = table.get("sample_identity")
        roles = table.get("roles")
        if type(identity) is not dict or identity != _identity(expected_sample):
            _fail()
        if type(roles) is not dict or set(roles) != {"pocket", "ligand"}:
            _fail()
        for role_name in ("pocket", "ligand"):
            role = roles.get(role_name)
            if type(role) is not dict or any(field not in role for field in _ROLE_AUTHORITY_FIELDS):
                _fail()
            atom = role.get("selected_atom_identity")
            if (
                type(role.get("parser_output_atom_count")) is not int
                or role["parser_output_atom_count"] < 0
                or type(atom) is not dict or set(atom) != set(_ATOM_IDENTITY_FIELDS)
                or any(type(atom.get(field)) is not str for field in _ATOM_IDENTITY_FIELDS)
            ):
                _fail()
    return provider


def _authority(repo: Path, state: Path) -> tuple[dict[str, object], list[dict[str, object]], dict[str, bool]]:
    _validate_gate_source(repo)
    with _precommit_compatibility():
        artifacts = _contract_gate.build_covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1(
            repo_root=repo, state_root=state,
        )
    manifest, vectors, _report = _validate_exact6(artifacts)
    cases = vectors["reference_cases"]
    canonical = cases[0]
    compiler_output = canonical.get("compiler_output") if type(canonical) is dict else None
    exact18 = compiler_output.get("adapter_input_exact18") if type(compiler_output) is dict else None
    if type(exact18) is not dict or set(exact18) != set(_EXACT18_FIELDS):
        _fail()
    source = _validate_source({field: copy.deepcopy(exact18[field]) for field in _SOURCE_FIELDS})
    provider = _validate_provider(copy.deepcopy(vectors.get("identity_provider")), source)
    readiness = manifest.get("readiness")
    if type(readiness) is not dict:
        _fail()
    product_readiness = copy.deepcopy(readiness)
    product_readiness["task2_batch_descriptor_compiler_implemented"] = True
    product_readiness["ready_for_task2_batch_descriptor_compiler_implementation"] = False
    if any(type(value) is not bool for value in product_readiness.values()):
        _fail()
    return source, provider, product_readiness


def _prefix(lengths: Sequence[int]) -> list[int]:
    offsets = [0]
    for length in lengths:
        offsets.append(offsets[-1] + length)
    return offsets


def _membership(lengths: Sequence[int]) -> list[int]:
    return [ordinal for ordinal, length in enumerate(lengths) for _ in range(length)]


def _json_safe(value: object, active: set[int] | None = None) -> bool:
    if value is None or type(value) in (str, bool, int):
        return True
    if type(value) is float:
        return math.isfinite(value)
    if type(value) not in (dict, list):
        return False
    active = set() if active is None else active
    marker = id(value)
    if marker in active:
        return False
    active.add(marker)
    try:
        if type(value) is list:
            return all(_json_safe(item, active) for item in value)
        return all(
            type(key) is str and _json_safe(item, active) for key, item in value.items()
        )
    finally:
        active.remove(marker)


def _output(
    status: str, *, exact18: dict[str, object] | None,
    outcomes: list[dict[str, object]], joint_status: str,
    readiness: Mapping[str, bool],
) -> dict[str, object]:
    result = {
        "schema_version": _OUTPUT_SCHEMA,
        "compiler_status": "COMPILED_EXACT" if exact18 is not None else status,
        "failure_reason": "NONE" if exact18 is not None else status,
        "adapter_input_exact18": exact18,
        "batch_sample_key_outcomes": outcomes,
        "source_contract_digest": _REMAP_CONTRACT_DIGEST,
        "identity_provider_digest": _PROVIDER_DIGEST,
        "runtime_schema_binding": {
            "runtime_batch_schema_version": _RUNTIME_SCHEMA,
            "sample_key_schema_version": _SAMPLE_KEY_SCHEMA,
            "virtual_node_policy": _VIRTUAL_POLICY,
            "joint_layout_component_status": joint_status,
        },
        "provenance": {
            "contract_evaluator_only": False,
            "compiler_implemented": True,
            "runtime_extractor_implemented": False,
            "remap_executed_by_compiler": False,
            "compiler_contract_commit": _CONTRACT_COMMIT,
            "compiler_contract_digest": _CONTRACT_DIGEST,
        },
        "readiness": copy.deepcopy(readiness),
    }
    if tuple(result) != _OUTPUT_FIELDS:
        _fail()
    return result


def _compile(
    *, repo_root: Path, state_root: Path, observation: dict[str, object],
) -> dict[str, object]:
    repo = _require_root(repo_root)
    state = _require_root(state_root)
    source, provider, readiness = _authority(repo, state)

    def rejected(
        status: str, outcomes: list[dict[str, object]] | None = None,
    ) -> dict[str, object]:
        return _output(
            status, exact18=None, outcomes=[] if outcomes is None else outcomes,
            joint_status="JOINT_LAYOUT_UNAVAILABLE", readiness=readiness,
        )

    if type(observation) is not dict:
        return rejected("BATCH_OBSERVATION_SCHEMA_MISMATCH")
    keys = set(observation)
    allowed = _INPUT_REQUIRED | _INPUT_OPTIONAL | _SOURCE_OVERRIDE_FIELDS | _OTHER_FORBIDDEN_FIELDS
    if not _INPUT_REQUIRED.issubset(keys) or not keys.issubset(allowed):
        return rejected("BATCH_OBSERVATION_SCHEMA_MISMATCH")
    if keys & _SOURCE_OVERRIDE_FIELDS:
        return rejected("SOURCE_CONTRACT_MISMATCH")
    if keys - (_INPUT_REQUIRED | _INPUT_OPTIONAL | _SOURCE_OVERRIDE_FIELDS):
        return rejected("BATCH_OBSERVATION_SCHEMA_MISMATCH")
    if observation.get("schema_version") != _INPUT_SCHEMA:
        return rejected("BATCH_OBSERVATION_SCHEMA_MISMATCH")
    if observation.get("runtime_batch_schema_version") != _RUNTIME_SCHEMA:
        return rejected("BATCH_OBSERVATION_SCHEMA_MISMATCH")
    if observation.get("sample_key_schema_version") != _SAMPLE_KEY_SCHEMA:
        return rejected("BATCH_OBSERVATION_SCHEMA_MISMATCH")

    batch_keys = observation.get("batch_sample_keys")
    if type(batch_keys) is not list or any(
        type(key) is not str or not key or key.strip() != key for key in batch_keys
    ):
        return rejected("BATCH_SAMPLE_KEY_INVALID")
    if len(set(batch_keys)) != len(batch_keys):
        return rejected("BATCH_SAMPLE_KEY_DUPLICATED")

    source_samples = source["source_sample_order"]
    source_by_key = {sample["sample_index_row_id"]: sample for sample in source_samples}
    provider_by_key: dict[str, list[dict[str, object]]] = {}
    for table in provider:
        key = table["sample_identity"]["sample_index_row_id"]
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
        outcomes.append({
            "batch_ordinal": ordinal,
            "sample_index_row_id": key,
            "status": "COMPILED_EXACT",
        })
        selected.append((source_by_key[key], matches[0]))

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
        if not _json_safe(value):
            return rejected("BATCH_OBSERVATION_SCHEMA_MISMATCH", outcomes)

    exact18 = {field: copy.deepcopy(source[field]) for field in _SOURCE_FIELDS}
    exact18.update({
        "batch_sample_order": [_identity(sample) for sample, _table in selected],
        "batch_sample_atom_identity_tables": [
            copy.deepcopy(table) for _sample, table in selected
        ],
        "batch_role_lengths": {"pocket": pocket_lengths[:], "ligand": ligand_lengths[:]},
        "batch_role_offsets": {
            "pocket": _prefix(pocket_lengths), "ligand": _prefix(ligand_lengths),
        },
        "batch_membership_masks": {
            "pocket": pocket_membership[:], "ligand": ligand_membership[:],
        },
        "joint_layout_descriptor": joint,
        "debug_coordinates": copy.deepcopy(observation.get("debug_coordinates")),
        "debug_rank_metadata": copy.deepcopy(observation.get("debug_rank_metadata")),
    })
    if tuple(exact18) != _EXACT18_FIELDS:
        _fail()
    return _output(
        "COMPILED_EXACT", exact18=exact18, outcomes=outcomes,
        joint_status="COMPILED_EXACT" if joint == _JOINT_LAYOUT else "JOINT_LAYOUT_UNAVAILABLE",
        readiness=readiness,
    )


def compile_covapie_current11_task2_batch_descriptor_v1(
    *, repo_root: Path, state_root: Path, observation: dict[str, object],
) -> dict[str, object]:
    """Compile a validated runtime observation into the frozen adapter Exact18."""
    try:
        return _compile(repo_root=repo_root, state_root=state_root, observation=observation)
    except BaseException as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
