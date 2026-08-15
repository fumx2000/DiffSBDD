"""Immutable compiler authority bridged from one sealed remap context V1."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import stat
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Mapping, NoReturn

from covalent_ext import (
    covapie_current11_task2_batch_descriptor_compiler_v1 as _compiler,
)
from covalent_ext import (
    covapie_current11_task2_batch_index_remap_adapter_context_v1
    as _adapter_context,
)


__all__ = (
    "build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1",
    "compile_covapie_current11_task2_batch_descriptor_with_remap_handoff_context_v1",
)

_ERROR = (
    "COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_"
    "FROM_REMAP_CONTEXT_V1_ERROR"
)
_CONTEXT_SCHEMA_VERSION = (
    "covapie_current11_task2_batch_descriptor_compiler_context_from_"
    "remap_context_v1"
)
_CONTEXT_CONTRACT_VERSION = (
    "7de09322699eb9529486f49f5e5c1367317d63143e967f6223b010a4ef972c78"
)
_ADAPTER_CONTEXT_OWNER_MODULE = (
    "src/covalent_ext/"
    "covapie_current11_task2_batch_index_remap_adapter_context_v1.py"
)
_ADAPTER_CONTEXT_OWNER_SCHEMA_VERSION = (
    "covapie_current11_task2_batch_index_remap_adapter_context_v1"
)
_ADAPTER_CONTEXT_OWNER_CONTRACT_VERSION = (
    "19649350ac39697138d1c38155a762403fa148db5d7f9ebc518466756c40d1dc"
)
_ADAPTER_CONTEXT_OWNER_SOURCE_SHA256 = (
    "1eb764aa4425ad857d59daa625e610a5e015a0a272594f332254998bed8191e6"
)
_ADAPTER_CONTEXT_PRIVATE_MATERIALIZER = "_validate_context_and_materialize"
_COMPILER_MODULE = (
    "src/covalent_ext/covapie_current11_task2_batch_descriptor_compiler_v1.py"
)
_COMPILER_PRODUCT_COMMIT = "05e8694eb3cdfe9c1aa4cd9728d4820b7322ba5e"
_COMPILER_SOURCE_SHA256 = (
    "a7a232a4f344e5cbac152ae8cc51921f4d9bf07deaaab0d55f1ce950e67b524a"
)
_COMPILER_PRIVATE_KERNEL = "_compile_with_verified_authority_v1"
_COMPILER_CONTRACT_DIGEST = (
    "bb9705173523377f28966064eec7393fbf337dce9ef6c70d2e3fbca3038e2dfd"
)
_SOURCE_CONTRACT_DIGEST = (
    "2c6259312a3292181f00ebbaf787fab05e5a97e5b5475243f2fa8461b54dcdc6"
)
_PROVIDER_DIGEST = (
    "a6193bfe7099b9c9436036f75101df31638739a893b598af8ac021bfa46aa186"
)
_HISTORICAL_AUTHORITY_COMPATIBILITY_DIGEST = (
    "e3c7c14e5a94db2bf59b5195ae6902d7fd7269e58a8690589962548860348d44"
)
_CONTEXT_FRESHNESS_MODEL = "explicit_rebuild_from_caller_owned_remap_context"

_LOGICAL_FIELD_ORDER = (
    "context_schema_version",
    "context_contract_version",
    "adapter_context_owner_module",
    "adapter_context_owner_schema_version",
    "adapter_context_owner_contract_version",
    "adapter_context_owner_source_sha256",
    "adapter_context_private_materializer",
    "compiler_module",
    "compiler_product_commit",
    "compiler_source_sha256",
    "compiler_private_kernel",
    "compiler_contract_digest",
    "source_contract_digest",
    "provider_digest",
    "historical_authority_compatibility_digest",
    "context_freshness_model",
    "source_exact10",
    "identity_provider_exact11",
    "readiness_template",
    "construction_seal",
)
_SOURCE_FIELDS = (
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
)
_IDENTITY_FIELDS = (
    "sample_index_row_id",
    "sample_preparation_input_id",
    "pdb_id",
    "ligand_comp_id",
)
_ROLE_ORDER = ("pocket", "ligand")
_ROLE_RECORD_FIELDS = (
    "SHA256",
    "committed_projection_matrix_local_index",
    "explicit_hydrogen_count",
    "relative_path",
    "retained_heavy_count",
    "role",
    "root_kind",
    "row_count",
    "row_order_digest",
    "row_order_version",
    "selected_atom_identity",
    "selected_parser_local_index",
    "selected_row_retained",
    "selected_source_row_index_0based",
    "source_to_parser_exact_one",
    "unsupported_nonhydrogen_count",
    "parser_output_atom_count",
    "source_to_parser_local",
)

_SOURCE_CANONICAL_BYTES = 2735
_SOURCE_CANONICAL_SHA256 = (
    "21bc3eb8a7b2f4b569f17d102715726eda09aed6467782e5477a7cfa285f98f2"
)
_SOURCE_COMPONENT_DIGEST = (
    "ffbd6311d0ae44e0729cf6c659493f14945414d7ce6aac3ddea107a321773aba"
)
_PROVIDER_CANONICAL_BYTES = 23364
_PROVIDER_CANONICAL_SHA256 = (
    "1345c9da88fd516677c1730d129ab8a19f487eb0862fa7b7580481bc15a43bc5"
)
_PROVIDER_COMPONENT_DIGEST = (
    "1c06fdec0313c481c60eadb9b6c20d278c682908c3681f99995f8fee5109564a"
)
_READINESS_COMPONENT_DIGEST = (
    "8d6bcae9f365f6c802e9109a8c1e53c1b85c8c8c23f04d005a162c09fcdb6890"
)

_SOURCE_COMPONENT_DOMAIN = (
    b"COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_"
    b"SOURCE_COMPONENT_V1\x00"
)
_PROVIDER_COMPONENT_DOMAIN = (
    b"COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_"
    b"PROVIDER_COMPONENT_V1\x00"
)
_READINESS_COMPONENT_DOMAIN = (
    b"COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_"
    b"READINESS_COMPONENT_V1\x00"
)
_SEAL_DOMAIN = (
    b"COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_"
    b"FROM_REMAP_CONTEXT_V1\x00"
)

_ADAPTER_OWNER_EXACT2 = (
    "build_covapie_current11_task2_batch_index_remap_adapter_context_v1",
    "remap_covapie_current11_task2_batch_index_with_context_v1",
)
_ADAPTER_OWNER_BYTES = 43578
_ADAPTER_OWNER_LF = 1211
_COMPILER_OWNER_BYTES = 31298
_COMPILER_OWNER_LF = 687

_READINESS_EXACT24 = (
    ("base_atom_feature_width_change_required", False),
    ("base_model_parameter_shape_change_required", False),
    ("checkpoint_bytes_read", False),
    ("checkpoint_state_dict_change_required", False),
    ("compiler_input_schema_frozen", True),
    ("compiler_output_schema_frozen", True),
    ("compiler_reference_composition_passed", True),
    ("compiler_status_vocabulary_frozen", True),
    ("egnn_or_se3_backbone_change_required", False),
    ("feature_semantics_reaudit_required_before_training", True),
    ("formal_runtime_carrier_verified", True),
    ("identity_provider_verified", True),
    ("ready_for_dataloader_integration", False),
    ("ready_for_loss_integration", False),
    ("ready_for_model_integration", False),
    ("ready_for_runtime_batch_observation_extractor_design", True),
    ("ready_for_task2_batch_descriptor_compiler_implementation", False),
    ("ready_for_training", False),
    ("runtime_batch_observation_extractor_implemented", False),
    ("source_contract_verified", True),
    ("task2_batch_descriptor_compiler_contract_designed", True),
    ("task2_batch_descriptor_compiler_contract_gate_implemented", True),
    ("task2_batch_descriptor_compiler_contract_gate_passed", True),
    ("task2_batch_descriptor_compiler_implemented", True),
)

_FIXED_SEMANTIC_VALUES = (
    _CONTEXT_SCHEMA_VERSION,
    _CONTEXT_CONTRACT_VERSION,
    _ADAPTER_CONTEXT_OWNER_MODULE,
    _ADAPTER_CONTEXT_OWNER_SCHEMA_VERSION,
    _ADAPTER_CONTEXT_OWNER_CONTRACT_VERSION,
    _ADAPTER_CONTEXT_OWNER_SOURCE_SHA256,
    _ADAPTER_CONTEXT_PRIVATE_MATERIALIZER,
    _COMPILER_MODULE,
    _COMPILER_PRODUCT_COMMIT,
    _COMPILER_SOURCE_SHA256,
    _COMPILER_PRIVATE_KERNEL,
    _COMPILER_CONTRACT_DIGEST,
    _SOURCE_CONTRACT_DIGEST,
    _PROVIDER_DIGEST,
    _HISTORICAL_AUTHORITY_COMPATIBILITY_DIGEST,
    _CONTEXT_FRESHNESS_MODEL,
)
_CONSTRUCTION_TOKEN = object()


class _BridgeInvariantError(Exception):
    pass


def _fail() -> NoReturn:
    raise _BridgeInvariantError()


@dataclass(frozen=True, slots=True, repr=False)
class _FrozenMapEntryV1:
    key: str
    value: object


@dataclass(frozen=True, slots=True, repr=False)
class _FrozenMapV1:
    items: tuple[_FrozenMapEntryV1, ...]


@dataclass(frozen=True, slots=True, repr=False)
class _FrozenListV1:
    items: tuple[object, ...]


@dataclass(frozen=True, slots=True, repr=False, init=False)
class _BridgeContextV1:
    _semantic: _FrozenMapV1
    _construction_token: object

    def __copy__(self) -> NoReturn:
        raise TypeError(_ERROR)

    def __deepcopy__(self, memo: dict[int, object]) -> NoReturn:
        del memo
        raise TypeError(_ERROR)

    def __reduce__(self) -> NoReturn:
        raise TypeError(_ERROR)

    def __reduce_ex__(self, protocol: int) -> NoReturn:
        del protocol
        raise TypeError(_ERROR)


def _freeze_value_v1(value: object, active: set[int] | None = None) -> object:
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            _fail()
        return value
    if type(value) not in (dict, list):
        _fail()
    active = set() if active is None else active
    marker = id(value)
    if marker in active:
        _fail()
    active.add(marker)
    try:
        if type(value) is list:
            return _FrozenListV1(
                tuple(_freeze_value_v1(item, active) for item in value)
            )
        entries: list[_FrozenMapEntryV1] = []
        for key, item in value.items():
            if type(key) is not str:
                _fail()
            entries.append(
                _FrozenMapEntryV1(key, _freeze_value_v1(item, active))
            )
        return _FrozenMapV1(tuple(entries))
    finally:
        active.remove(marker)


def _thaw_value_v1(value: object) -> object:
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            _fail()
        return value
    if type(value) is _FrozenListV1:
        return [_thaw_value_v1(item) for item in value.items]
    if type(value) is _FrozenMapV1:
        result: dict[str, object] = {}
        for entry in value.items:
            if type(entry) is not _FrozenMapEntryV1 or type(entry.key) is not str:
                _fail()
            if entry.key in result:
                _fail()
            result[entry.key] = _thaw_value_v1(entry.value)
        return result
    _fail()


def _compact_json_v1(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise _BridgeInvariantError() from error


def _framed_digest_v1(domain: bytes, value: object) -> str:
    payload = _compact_json_v1(value)
    digest = hashlib.sha256()
    digest.update(domain)
    digest.update(len(payload).to_bytes(8, "big", signed=False))
    digest.update(payload)
    return digest.hexdigest()


def _construction_seal_v1(semantic: Mapping[str, object]) -> str:
    if type(semantic) is not dict or tuple(semantic) != _LOGICAL_FIELD_ORDER[:19]:
        _fail()
    payload = _compact_json_v1(semantic)
    digest = hashlib.sha256()
    digest.update(_SEAL_DOMAIN)
    digest.update(len(payload).to_bytes(8, "big", signed=False))
    digest.update(payload)
    return digest.hexdigest()


def _read_owner_source_v1(
    module: ModuleType,
    *,
    expected_bytes: int,
    expected_lf: int,
    expected_sha256: str,
) -> bytes:
    module_file = getattr(module, "__file__", None)
    if type(module_file) is not str or not module_file:
        _fail()
    path = Path(module_file)
    try:
        metadata = path.lstat()
        payload = path.read_bytes()
    except OSError as error:
        raise _BridgeInvariantError() from error
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != 0o644
        or len(payload) != expected_bytes
        or payload.count(b"\n") != expected_lf
        or hashlib.sha256(payload).hexdigest() != expected_sha256
        or not payload.endswith(b"\n")
        or b"\r" in payload
    ):
        _fail()
    return payload


def _validate_owner_sources_v1() -> None:
    _read_owner_source_v1(
        _adapter_context,
        expected_bytes=_ADAPTER_OWNER_BYTES,
        expected_lf=_ADAPTER_OWNER_LF,
        expected_sha256=_ADAPTER_CONTEXT_OWNER_SOURCE_SHA256,
    )
    _read_owner_source_v1(
        _compiler,
        expected_bytes=_COMPILER_OWNER_BYTES,
        expected_lf=_COMPILER_OWNER_LF,
        expected_sha256=_COMPILER_SOURCE_SHA256,
    )
    materializer = getattr(
        _adapter_context, _ADAPTER_CONTEXT_PRIVATE_MATERIALIZER, None
    )
    kernel = getattr(_compiler, _COMPILER_PRIVATE_KERNEL, None)
    if (
        tuple(getattr(_adapter_context, "__all__", ()))
        != _ADAPTER_OWNER_EXACT2
        or _adapter_context.CONTEXT_SCHEMA_VERSION
        != _ADAPTER_CONTEXT_OWNER_SCHEMA_VERSION
        or _adapter_context.CONTEXT_CONTRACT_VERSION
        != _ADAPTER_CONTEXT_OWNER_CONTRACT_VERSION
        or not callable(materializer)
        or _compiler._CONTRACT_DIGEST != _COMPILER_CONTRACT_DIGEST
        or _compiler._REMAP_CONTRACT_DIGEST != _SOURCE_CONTRACT_DIGEST
        or _compiler._PROVIDER_DIGEST != _PROVIDER_DIGEST
        or not callable(kernel)
    ):
        _fail()


def _map_source_v1(
    source_contract: object,
    adapter_semantic: object,
) -> dict[str, object]:
    if type(source_contract) is not dict or type(adapter_semantic) is not dict:
        _fail()
    required = (
        "sample_order",
        "pair_values_source_row_indices",
        "sample_pair_offsets",
        "entry_validity",
        "sample_validity",
    )
    if any(field not in source_contract for field in required):
        _fail()
    source = {
        "schema_version": _compiler._SOURCE_SCHEMA,
        "source_projection_digest": adapter_semantic.get(
            "projection_instance_digest"
        ),
        "source_payload_digest": adapter_semantic.get("payload_bundle_digest"),
        "parser_schema_version": _compiler._PARSER_SCHEMA,
        "collate_schema_version": _compiler._COLLATE_SCHEMA,
        "source_sample_order": copy.deepcopy(source_contract["sample_order"]),
        "source_pair_values_int64": copy.deepcopy(
            source_contract["pair_values_source_row_indices"]
        ),
        "source_sample_offsets_int64": copy.deepcopy(
            source_contract["sample_pair_offsets"]
        ),
        "source_entry_validity_bool": copy.deepcopy(
            source_contract["entry_validity"]
        ),
        "source_sample_validity_bool": copy.deepcopy(
            source_contract["sample_validity"]
        ),
    }
    if tuple(source) != _SOURCE_FIELDS:
        _fail()
    return source


def _map_provider_v1(
    authority_tables: object,
    source: Mapping[str, object],
) -> list[dict[str, object]]:
    samples = source.get("source_sample_order")
    if (
        type(authority_tables) is not list
        or len(authority_tables) != 11
        or type(samples) is not list
        or len(samples) != 11
    ):
        _fail()
    provider: list[dict[str, object]] = []
    for ordinal, (sample, table) in enumerate(
        zip(samples, authority_tables, strict=True)
    ):
        if type(sample) is not dict or type(table) is not dict:
            _fail()
        table_identity = table.get("sample_identity")
        roles = table.get("roles")
        if (
            type(table_identity) is not dict
            or table_identity.get("source_sample_index") != ordinal
            or sample.get("source_sample_index") != ordinal
            or any(table_identity.get(field) != sample.get(field) for field in _IDENTITY_FIELDS)
            or type(roles) is not dict
            or tuple(roles) != _ROLE_ORDER
        ):
            _fail()
        projected_identity: dict[str, object] = {}
        for field in _IDENTITY_FIELDS:
            value = table_identity.get(field)
            if type(value) is not str:
                _fail()
            projected_identity[field] = value
        projected_roles: dict[str, object] = {}
        for role_name in _ROLE_ORDER:
            role = roles.get(role_name)
            if (
                type(role) is not dict
                or tuple(role) != _ROLE_RECORD_FIELDS
                or role.get("role") != role_name
            ):
                _fail()
            projected_roles[role_name] = copy.deepcopy(role)
        provider.append(
            {
                "sample_identity": projected_identity,
                "roles": projected_roles,
            }
        )
    return provider


def _validate_authority_golden_v1(
    source: object,
    provider: object,
    readiness: object,
) -> tuple[dict[str, object], list[dict[str, object]], dict[str, bool]]:
    if (
        type(source) is not dict
        or tuple(source) != _SOURCE_FIELDS
        or type(provider) is not list
        or type(readiness) is not dict
        or tuple(readiness.items()) != _READINESS_EXACT24
        or readiness != dict(_READINESS_EXACT24)
        or len(readiness) != 24
        or any(type(value) is not bool for value in readiness.values())
    ):
        _fail()
    try:
        validated_source = _compiler._validate_source(source)
        validated_provider = _compiler._validate_provider(provider, source)
        provider_digest = _compiler._provider_digest(provider)
    except Exception as error:
        raise _BridgeInvariantError() from error
    source_payload = _compact_json_v1(source)
    provider_payload = _compact_json_v1(provider)
    if (
        validated_source is not source
        or validated_provider is not provider
        or len(source_payload) != _SOURCE_CANONICAL_BYTES
        or hashlib.sha256(source_payload).hexdigest() != _SOURCE_CANONICAL_SHA256
        or _framed_digest_v1(_SOURCE_COMPONENT_DOMAIN, source)
        != _SOURCE_COMPONENT_DIGEST
        or len(provider_payload) != _PROVIDER_CANONICAL_BYTES
        or hashlib.sha256(provider_payload).hexdigest()
        != _PROVIDER_CANONICAL_SHA256
        or provider_digest != _PROVIDER_DIGEST
        or _framed_digest_v1(_PROVIDER_COMPONENT_DOMAIN, provider)
        != _PROVIDER_COMPONENT_DIGEST
        or _framed_digest_v1(_READINESS_COMPONENT_DOMAIN, readiness)
        != _READINESS_COMPONENT_DIGEST
    ):
        _fail()
    return source, provider, readiness


def _new_context_v1(semantic: dict[str, object]) -> _BridgeContextV1:
    if tuple(semantic) != _LOGICAL_FIELD_ORDER[:19]:
        _fail()
    logical = dict(semantic)
    logical["construction_seal"] = _construction_seal_v1(semantic)
    if tuple(logical) != _LOGICAL_FIELD_ORDER:
        _fail()
    frozen = _freeze_value_v1(logical)
    if type(frozen) is not _FrozenMapV1:
        _fail()
    context = object.__new__(_BridgeContextV1)
    object.__setattr__(context, "_semantic", frozen)
    object.__setattr__(context, "_construction_token", _CONSTRUCTION_TOKEN)
    return context


def _build_context_impl_v1(*, remap_context: object) -> object:
    _validate_owner_sources_v1()
    try:
        source_contract, authority_tables, adapter_semantic = (
            _adapter_context._validate_context_and_materialize(remap_context)
        )
    except Exception as error:
        raise _BridgeInvariantError() from error
    source = _map_source_v1(source_contract, adapter_semantic)
    provider = _map_provider_v1(authority_tables, source)
    readiness = dict(_READINESS_EXACT24)
    _validate_authority_golden_v1(source, provider, readiness)
    semantic = dict(
        zip(_LOGICAL_FIELD_ORDER[:16], _FIXED_SEMANTIC_VALUES, strict=True)
    )
    semantic["source_exact10"] = source
    semantic["identity_provider_exact11"] = provider
    semantic["readiness_template"] = readiness
    if tuple(semantic) != _LOGICAL_FIELD_ORDER[:19]:
        _fail()
    return _new_context_v1(semantic)


def _validate_context_and_materialize_v1(
    context: object,
) -> tuple[dict[str, object], list[dict[str, object]], dict[str, bool]]:
    if (
        type(context) is not _BridgeContextV1
        or context._construction_token is not _CONSTRUCTION_TOKEN
        or type(context._semantic) is not _FrozenMapV1
    ):
        _fail()
    logical = _thaw_value_v1(context._semantic)
    if (
        type(logical) is not dict
        or tuple(logical) != _LOGICAL_FIELD_ORDER
        or tuple(logical.get(field) for field in _LOGICAL_FIELD_ORDER[:16])
        != _FIXED_SEMANTIC_VALUES
    ):
        _fail()
    seal = logical.get("construction_seal")
    semantic = {field: logical[field] for field in _LOGICAL_FIELD_ORDER[:19]}
    if (
        type(seal) is not str
        or len(seal) != 64
        or seal != seal.lower()
        or any(character not in "0123456789abcdef" for character in seal)
        or _construction_seal_v1(semantic) != seal
    ):
        _fail()
    source = logical.get("source_exact10")
    provider = logical.get("identity_provider_exact11")
    readiness = logical.get("readiness_template")
    return _validate_authority_golden_v1(source, provider, readiness)


def _logical_context_value_v1(context: object) -> dict[str, object]:
    _validate_context_and_materialize_v1(context)
    logical = _thaw_value_v1(context._semantic)
    if type(logical) is not dict or tuple(logical) != _LOGICAL_FIELD_ORDER:
        _fail()
    return logical


def _compile_with_context_impl_v1(
    *,
    context: object,
    observation: dict[str, object],
) -> dict[str, object]:
    source, provider, readiness = _validate_context_and_materialize_v1(context)
    return _compiler._compile_with_verified_authority_v1(
        authority=(source, provider, readiness),
        observation=observation,
    )


def build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1(
    *,
    remap_context: object,
) -> object:
    """Build an opaque compiler context from one caller-owned remap context."""

    try:
        return _build_context_impl_v1(remap_context=remap_context)
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def compile_covapie_current11_task2_batch_descriptor_with_remap_handoff_context_v1(
    *,
    context: object,
    observation: dict[str, object],
) -> dict[str, object]:
    """Compile one observation through the verified pure compiler kernel."""

    try:
        return _compile_with_context_impl_v1(
            context=context,
            observation=observation,
        )
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
