# CovaPIE source-binding policy V2-B1 guide

## Purpose

V2-B1 provides one small common helper for a distinction that every future
source-binding consumer must preserve:

```text
content identity != filesystem security
```

Content identity answers whether a resolved path yielded the expected bytes.
Filesystem security answers whether the object at that path is safe and
acceptable to consume. A source can retain its semantic identity while its
security result changes.

This step adds only the common helper, its independent checker, targeted tests,
and this guide. It does not migrate active consumers, rewrite historical
validators, resolve path namespaces, add a manifest or registry, start I12
review, or authorize training.

## Public API

The production module exports exactly:

```python
SourceBindingPolicyV2Error

verify_content_identity_v2(
    *,
    path: Path,
    expected_byte_count: int,
    expected_sha256: str,
    label: str,
) -> bytes

verify_source_security_v2(
    *,
    path: Path,
    label: str,
    expected_executable: bool | None = None,
) -> None

verify_bound_source_v2(
    *,
    path: Path,
    expected_byte_count: int,
    expected_sha256: str,
    label: str,
    expected_executable: bool | None = None,
) -> bytes
```

The functions are stateless. There is no registry, cache, singleton, resolver,
or mutable global policy.

## Content identity

For an already resolved `Path`, content identity verifies only:

```text
byte_count
sha256
```

The path and path namespace belong to the binding record and remain the
consumer's responsibility. The helper does not implement repository-relative
or project-parent-relative resolution.

Exact runtime POSIX mode is not semantic identity. In particular, `0600`,
`0644`, and `0664` are not content-identity fields. The content helper does not
inspect permission bits or apply an exact numeric mode gate.

## Filesystem security

The separate security gate uses `lstat()` and requires:

```text
regular file
non-symlink
owner-readable
not world-writable
expected executable class, when requested
```

Group write is not automatically unsafe. Safe non-executable sources in the
`0600`, `0644`, `0660`, and `0664` families are accepted. In particular,
`0664` is a legitimate project mode.

`expected_executable=None` does not enforce executable class.
`expected_executable=False` rejects any executable bit.
`expected_executable=True` requires an executable bit but does not require one
exact numeric mode. Safe examples include `0700`, `0750`, `0755`, `0770`, and
`0775`.

World-writable files are rejected. Examples include `0666`, `0777`, and
`0622`.

## Concrete mode changes

### `0644` to `0664`

```text
bytes/SHA: unchanged
semantic identity: unchanged
security gate: PASS
```

The checkout reconstructed a group-writable but non-world-writable regular
file. V2 does not reproduce the historical exact-mode false failure.

The same semantic-identity rule applies to `0600` to `0664` when the bytes and
SHA remain exact.

### `0644` to `0666`

```text
bytes/SHA: unchanged
semantic identity: unchanged
security gate: FAIL (world-writable)
```

The bytes still identify the same content. That does not make the filesystem
object safe to consume.

### `0644` to `0755`

```text
bytes/SHA: unchanged
semantic identity: unchanged
security gate: depends on executable-class policy
```

It passes when executable class is not enforced or is required. It fails when
`expected_executable=False`. The decision is about executable class, not an
exact `0755` requirement.

## Combined verification and stability

The combined helper applies the security gate before reading, verifies exact
bytes and SHA, and applies the security gate again after reading. It compares
device, inode, file type, and size before and after the read. A change in those
fields fails with `SOURCE_CHANGED_DURING_READ`.

The stability check does not turn permissions or mtime into semantic identity.
A safe `0644` to safe `0664` mode-only change does not alter the content
identity contract.

All failures use `SourceBindingPolicyV2Error` with the stable prefix:

```text
COVAPIE_SOURCE_BINDING_POLICY_V2_ERROR
```

Semantic mismatch tokens are distinct from security failure tokens.

## Lifecycle and next boundary

The independent checker accepts exactly two successful publication lifecycle
profiles:

```text
CANDIDATE_UNTRACKED
TRACKED_CLEAN
```

The candidate profile requires the baseline HEAD and `origin/main`, an empty
index and working diff, and exactly the four V2-B1 files as ordinary untracked
files. The tracked-clean profile requires one exact child commit whose changed
paths are those same four files, either one commit ahead of the baseline remote
or published with `origin/main` at that child.

V2-B2 may migrate only the eight active/current consumers identified by the
published Phase A audit. That work is not part of V2-B1. Historical validators
and authority bytes remain immutable.

Dataset materialization, QA, this helper, and its smoke/runtime checks do not
establish training readiness. Before any formal training or parameter update,
the feature-semantics audit remains required, including resolution or formal
audit of the historical `UNKNOWN_ATOM_FEATURE_POLICY` and
`feature_semantics_known=False` state. Step12D remains a smoke legality check,
not a final training-feature contract.
