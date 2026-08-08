"""Immutable authority context for the Current11 Task 2 compiler V1."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

from covalent_ext import covapie_current11_task2_batch_descriptor_compiler_v1 as _compiler


__all__ = (
    "build_covapie_current11_task2_batch_descriptor_compiler_context_v1",
    "compile_covapie_current11_task2_batch_descriptor_with_context_v1",
)

_ERROR = "COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_V1_ERROR"
_CONTEXT_SCHEMA = "covapie_current11_task2_batch_descriptor_compiler_context_v1"
_COMPILER_PRODUCT_COMMIT = "05e8694eb3cdfe9c1aa4cd9728d4820b7322ba5e"
_COMPILER_CONTRACT_COMMIT = "3b390cec784ed73a72f522145b6f26e3d8af704d"
_COMPILER_CONTRACT_DIGEST = (
    "bb9705173523377f28966064eec7393fbf337dce9ef6c70d2e3fbca3038e2dfd"
)
_PROVIDER_DIGEST = (
    "a6193bfe7099b9c9436036f75101df31638739a893b598af8ac021bfa46aa186"
)
_FORMAL_CARRIER_AGGREGATE = (
    "ef426a6d8dee9678ac15dd62b191e9ef9cfb436a01660bd941bd24392dfa9a18"
)
_FORMAL_NPZ_SHA256 = (
    "ea3aa7c94b7c88993493662ad6ba7fd95e547ec62612a072f8248a515657e910"
)
_SOURCE_CONTRACT_DIGEST = (
    "2c6259312a3292181f00ebbaf787fab05e5a97e5b5475243f2fa8461b54dcdc6"
)
_EXPECTED_AUTHORITY_SNAPSHOT_DIGEST = (
    "e3c7c14e5a94db2bf59b5195ae6902d7fd7269e58a8690589962548860348d44"
)
_AUTHORITY_SNAPSHOT_DOMAIN = (
    b"COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_"
    b"AUTHORITY_SNAPSHOT_V1\0"
)

_CONTEXT_SEMANTIC_FIELDS = (
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
_SOURCE_FIELDS = tuple(_compiler._SOURCE_FIELDS)
_IDENTITY_FIELDS = tuple(_compiler._IDENTITY_FIELDS)
_ROLE_AUTHORITY_FIELDS = tuple(_compiler._ROLE_AUTHORITY_FIELDS)
_ATOM_IDENTITY_FIELDS = tuple(_compiler._ATOM_IDENTITY_FIELDS)
_CONSTRUCTION_SEAL = object()


def _fail() -> NoReturn:
    raise ValueError(_ERROR)


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
class _CompilerContextV1:
    context_schema_version: str
    compiler_product_commit: str
    compiler_contract_commit: str
    compiler_contract_digest: str
    provider_digest: str
    formal_carrier_aggregate: str
    formal_npz_sha256: str
    source_contract_digest: str
    authority_snapshot_digest: str
    source_exact10: object
    identity_provider_exact11: object
    readiness_template: object
    construction_seal: object

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
            entries.append(_FrozenMapEntryV1(key, _freeze_value_v1(item, active)))
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
        raise ValueError(_ERROR) from error


def _authority_snapshot_v1(
    source: dict[str, object],
    provider: list[dict[str, object]],
    readiness: dict[str, bool],
) -> dict[str, object]:
    return {
        "schema_version": _CONTEXT_SCHEMA,
        "semantic_provenance": {
            "context_schema_version": _CONTEXT_SCHEMA,
            "compiler_product_commit": _COMPILER_PRODUCT_COMMIT,
            "compiler_contract_commit": _COMPILER_CONTRACT_COMMIT,
            "compiler_contract_digest": _COMPILER_CONTRACT_DIGEST,
            "provider_digest": _PROVIDER_DIGEST,
            "formal_carrier_aggregate": _FORMAL_CARRIER_AGGREGATE,
            "formal_npz_sha256": _FORMAL_NPZ_SHA256,
            "source_contract_digest": _SOURCE_CONTRACT_DIGEST,
        },
        "field_and_schema_order": {
            "context_semantic_fields": list(_CONTEXT_SEMANTIC_FIELDS),
            "source_exact10_fields": list(_SOURCE_FIELDS),
            "identity_fields": list(_IDENTITY_FIELDS),
            "provider_role_order": ["pocket", "ligand"],
            "role_authority_fields": list(_ROLE_AUTHORITY_FIELDS),
            "atom_identity_fields": list(_ATOM_IDENTITY_FIELDS),
            "readiness_fields": list(readiness),
        },
        "source_exact10": source,
        "identity_provider_exact11": provider,
        "readiness_template": readiness,
    }


def _authority_snapshot_digest_v1(
    source: dict[str, object],
    provider: list[dict[str, object]],
    readiness: dict[str, bool],
) -> str:
    payload = _compact_json_v1(_authority_snapshot_v1(source, provider, readiness))
    digest = hashlib.sha256(_AUTHORITY_SNAPSHOT_DOMAIN)
    digest.update(len(payload).to_bytes(8, "big", signed=False))
    digest.update(payload)
    return digest.hexdigest()


def _new_context_v1(
    *,
    authority_snapshot_digest: str,
    source: dict[str, object],
    provider: list[dict[str, object]],
    readiness: dict[str, bool],
) -> _CompilerContextV1:
    context = object.__new__(_CompilerContextV1)
    values = (
        _CONTEXT_SCHEMA,
        _COMPILER_PRODUCT_COMMIT,
        _COMPILER_CONTRACT_COMMIT,
        _COMPILER_CONTRACT_DIGEST,
        _PROVIDER_DIGEST,
        _FORMAL_CARRIER_AGGREGATE,
        _FORMAL_NPZ_SHA256,
        _SOURCE_CONTRACT_DIGEST,
        authority_snapshot_digest,
        _freeze_value_v1(source),
        _freeze_value_v1(provider),
        _freeze_value_v1(readiness),
        _CONSTRUCTION_SEAL,
    )
    for field, value in zip((*_CONTEXT_SEMANTIC_FIELDS, "construction_seal"), values):
        object.__setattr__(context, field, value)
    return context


def _acquire_verified_compiler_authority_v1(
    *, repo: Path, state: Path
) -> object:
    try:
        return _compiler._authority(repo, state)
    except BaseException as error:
        if type(error) is ValueError and str(error) == _compiler._ERROR:
            raise
        raise ValueError(_compiler._ERROR) from error


def _build_context_v1(*, repo_root: Path, state_root: Path) -> _CompilerContextV1:
    repo = _compiler._require_root(repo_root)
    state = _compiler._require_root(state_root)
    authority = _acquire_verified_compiler_authority_v1(repo=repo, state=state)
    if type(authority) is not tuple or len(authority) != 3:
        _fail()
    source, provider, readiness = authority
    if type(source) is not dict or type(provider) is not list or type(readiness) is not dict:
        _fail()
    authority_digest = _authority_snapshot_digest_v1(source, provider, readiness)
    if authority_digest != _EXPECTED_AUTHORITY_SNAPSHOT_DIGEST:
        _fail()
    return _new_context_v1(
        authority_snapshot_digest=authority_digest,
        source=source,
        provider=provider,
        readiness=readiness,
    )


def _validate_context_v1(context: object) -> _CompilerContextV1:
    if type(context) is not _CompilerContextV1:
        _fail()
    if (
        context.context_schema_version != _CONTEXT_SCHEMA
        or context.compiler_product_commit != _COMPILER_PRODUCT_COMMIT
        or context.compiler_contract_commit != _COMPILER_CONTRACT_COMMIT
        or context.compiler_contract_digest != _COMPILER_CONTRACT_DIGEST
        or context.provider_digest != _PROVIDER_DIGEST
        or context.formal_carrier_aggregate != _FORMAL_CARRIER_AGGREGATE
        or context.formal_npz_sha256 != _FORMAL_NPZ_SHA256
        or context.source_contract_digest != _SOURCE_CONTRACT_DIGEST
        or context.authority_snapshot_digest
        != _EXPECTED_AUTHORITY_SNAPSHOT_DIGEST
        or context.construction_seal is not _CONSTRUCTION_SEAL
    ):
        _fail()
    return context


def _compile_with_context_v1(
    *, context: object, observation: dict[str, object]
) -> dict[str, object]:
    verified = _validate_context_v1(context)
    source = _thaw_value_v1(verified.source_exact10)
    provider = _thaw_value_v1(verified.identity_provider_exact11)
    readiness = _thaw_value_v1(verified.readiness_template)
    if type(source) is not dict or type(provider) is not list or type(readiness) is not dict:
        _fail()
    return _compiler._compile_with_verified_authority_v1(
        authority=(source, provider, readiness),
        observation=observation,
    )


def build_covapie_current11_task2_batch_descriptor_compiler_context_v1(
    *, repo_root: Path, state_root: Path
) -> object:
    """Build one immutable compiler authority context without caching it."""
    try:
        return _build_context_v1(repo_root=repo_root, state_root=state_root)
    except BaseException as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def compile_covapie_current11_task2_batch_descriptor_with_context_v1(
    *, context: object, observation: dict[str, object]
) -> dict[str, object]:
    """Compile one observation using a previously verified immutable context."""
    try:
        return _compile_with_context_v1(context=context, observation=observation)
    except BaseException as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
