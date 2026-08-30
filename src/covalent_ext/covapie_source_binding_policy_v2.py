"""Common V2 source-binding content identity and filesystem security gates."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat
from typing import NoReturn


__all__ = (
    "SourceBindingPolicyV2Error",
    "verify_content_identity_v2",
    "verify_source_security_v2",
    "verify_bound_source_v2",
)


_ERROR_PREFIX = "COVAPIE_SOURCE_BINDING_POLICY_V2_ERROR"


class SourceBindingPolicyV2Error(ValueError):
    """Raised when V2 content identity or filesystem security verification fails."""


def _fail(reason: str, label: str) -> NoReturn:
    raise SourceBindingPolicyV2Error(f"{_ERROR_PREFIX}:{reason}:{label}")


def verify_content_identity_v2(
    *,
    path: Path,
    expected_byte_count: int,
    expected_sha256: str,
    label: str,
) -> bytes:
    """Return the source bytes if byte count and SHA256 match exactly."""

    try:
        payload = path.read_bytes()
    except OSError as error:
        raise SourceBindingPolicyV2Error(
            f"{_ERROR_PREFIX}:SOURCE_READ_FAILED:{label}"
        ) from error
    if len(payload) != expected_byte_count:
        _fail("SOURCE_BYTE_COUNT_MISMATCH", label)
    if hashlib.sha256(payload).hexdigest() != expected_sha256:
        _fail("SOURCE_SHA256_MISMATCH", label)
    return payload


def _inspect_source_security_v2(
    *,
    path: Path,
    label: str,
    expected_executable: bool | None,
) -> os.stat_result:
    try:
        metadata = path.lstat()
    except OSError as error:
        raise SourceBindingPolicyV2Error(
            f"{_ERROR_PREFIX}:SOURCE_LSTAT_FAILED:{label}"
        ) from error
    if stat.S_ISLNK(metadata.st_mode):
        _fail("SOURCE_SYMLINK_FORBIDDEN", label)
    if not stat.S_ISREG(metadata.st_mode):
        _fail("SOURCE_NOT_REGULAR", label)
    if not metadata.st_mode & stat.S_IRUSR:
        _fail("SOURCE_OWNER_NOT_READABLE", label)
    if metadata.st_mode & stat.S_IWOTH:
        _fail("SOURCE_WORLD_WRITABLE", label)

    executable_bits = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    is_executable = bool(metadata.st_mode & executable_bits)
    if expected_executable is not None and is_executable is not expected_executable:
        _fail("SOURCE_EXECUTABLE_CLASS_MISMATCH", label)
    return metadata


def verify_source_security_v2(
    *,
    path: Path,
    label: str,
    expected_executable: bool | None = None,
) -> None:
    """Reject unsafe filesystem objects without enforcing an exact numeric mode."""

    _inspect_source_security_v2(
        path=path,
        label=label,
        expected_executable=expected_executable,
    )


def verify_bound_source_v2(
    *,
    path: Path,
    expected_byte_count: int,
    expected_sha256: str,
    label: str,
    expected_executable: bool | None = None,
) -> bytes:
    """Compose the V2 security and content gates with a stability check."""

    before = _inspect_source_security_v2(
        path=path,
        label=label,
        expected_executable=expected_executable,
    )
    payload = verify_content_identity_v2(
        path=path,
        expected_byte_count=expected_byte_count,
        expected_sha256=expected_sha256,
        label=label,
    )
    after = _inspect_source_security_v2(
        path=path,
        label=label,
        expected_executable=expected_executable,
    )
    before_identity = (
        before.st_dev,
        before.st_ino,
        stat.S_IFMT(before.st_mode),
        before.st_size,
    )
    after_identity = (
        after.st_dev,
        after.st_ino,
        stat.S_IFMT(after.st_mode),
        after.st_size,
    )
    if before_identity != after_identity:
        _fail("SOURCE_CHANGED_DURING_READ", label)
    return payload
