"""Tests for the Current11 GPFS atomic-alias routing sidecar materializer V2."""

from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT.parent / "covapie-state"
MODULE_NAME = (
    "covalent_ext.covapie_current11_dataset_partial_supervision_routing_sidecar_"
    "gpfs_atomic_alias_formal_materializer_v2"
)
CLI = (
    ROOT
    / "scripts/materialize_covapie_current11_dataset_partial_supervision_routing_sidecar_"
    "gpfs_atomic_alias_v2.py"
)
SOURCE_BINDINGS = {
    "src/covalent_ext/covapie_current11_dataset_partial_supervision_routing_sidecar_v1.py": (
        65524,
        1336,
        "1be932e473107a2944cf916c288580b614c7b6710556ca54c099d742971344a5",
        "eb05e70f438bb8170ad4e68d1edb3bda6198d052",
    ),
    "src/covalent_ext/covapie_current11_dataset_partial_supervision_routing_sidecar_formal_materializer_v1.py": (
        37785,
        1025,
        "5d189c0451a1aad515932bd4e537de9378b79fcbc2987f671d069e0db857aada",
        "45f44f54fad81c9fc45326bdc442a09cffb9d36a",
    ),
}


def _module():
    return importlib.import_module(MODULE_NAME)


def _output(parent: Path) -> Path:
    return parent / _module().CANONICAL_BASENAME


def _builder_artifacts() -> dict[str, bytes]:
    return _module()._v1._builder.build_covapie_current11_dataset_partial_supervision_routing_sidecar_v1(
        repo_root=ROOT, state_root=STATE
    )


def _materialize(parent: Path) -> dict[str, object]:
    return _module().materialize_covapie_current11_dataset_partial_supervision_routing_sidecar_gpfs_atomic_alias_v2(
        repo_root=ROOT, state_root=STATE, output_path=_output(parent)
    )


def _check(parent: Path) -> dict[str, object]:
    return _module()._verify_existing(
        repo_root=ROOT, state_root=STATE, output_path=_output(parent)
    )


def _cli(*arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        (sys.executable, "-B", os.fspath(CLI), *arguments),
        cwd=ROOT,
        check=False,
        capture_output=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


def _canonical_json(payload: bytes) -> dict[str, object]:
    assert payload.endswith(b"\n") and payload.count(b"\n") == 1
    parsed = json.loads(payload)
    assert payload == (
        json.dumps(parsed, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode("utf-8")
    return parsed


def _mutate_manifest(artifacts: dict[str, bytes], mutation) -> dict[str, bytes]:
    module = _module()
    changed = dict(artifacts)
    manifest = json.loads(changed[module.ARTIFACT_NAMES[3]])
    mutation(manifest)
    changed[module.ARTIFACT_NAMES[3]] = (
        json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n"
    ).encode("utf-8")
    return changed


def _install_builder_result(
    monkeypatch: pytest.MonkeyPatch, artifacts: dict[str, bytes]
) -> None:
    monkeypatch.setattr(
        _module()._v1._builder,
        "build_covapie_current11_dataset_partial_supervision_routing_sidecar_v1",
        lambda **_kwargs: artifacts,
    )


def _entry_snapshot(path: Path) -> tuple[int, int, int, int, bytes | str | None]:
    metadata = path.lstat()
    payload: bytes | str | None = None
    if stat.S_ISLNK(metadata.st_mode):
        payload = os.readlink(path)
    elif stat.S_ISREG(metadata.st_mode):
        payload = path.read_bytes()
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_mtime_ns,
        payload,
    )


def _published_paths(parent: Path) -> tuple[Path, Path, tuple[Path, ...]]:
    canonical = _output(parent)
    object_path = parent / os.readlink(canonical)
    leaves = tuple(object_path / name for name in _module().ARTIFACT_NAMES)
    return canonical, object_path, leaves


def _object_residue(parent: Path) -> tuple[Path, ...]:
    return tuple(parent.glob(f"{_module().OBJECT_PREFIX}*"))


def test_unique_keyword_only_public_api_and_silent_import(
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = importlib.reload(_module())
    assert capsys.readouterr() == ("", "")
    assert module.__all__ == (
        "materialize_covapie_current11_dataset_partial_supervision_routing_sidecar_gpfs_atomic_alias_v2",
    )
    signature = inspect.signature(
        module.materialize_covapie_current11_dataset_partial_supervision_routing_sidecar_gpfs_atomic_alias_v2
    )
    assert tuple(signature.parameters) == ("repo_root", "state_root", "output_path")
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )


def test_module_imports_are_stdlib_or_local() -> None:
    tree = ast.parse((ROOT / _module().MODULE_PATH).read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module != "__future__":
            roots.add((node.module or "").split(".")[0])
    assert roots <= set(sys.stdlib_module_names) | {"covalent_ext"}
    assert not {"torch", "rdkit", "openbabel"} & roots


def test_builder_and_v1_materializer_sources_are_frozen() -> None:
    for relative, (byte_count, line_count, digest, blob) in SOURCE_BINDINGS.items():
        payload = (ROOT / relative).read_bytes()
        assert (len(payload), payload.count(b"\n"), hashlib.sha256(payload).hexdigest()) == (
            byte_count,
            line_count,
            digest,
        )
        actual_blob = subprocess.run(
            ("git", "rev-parse", f"HEAD:{relative}"),
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        assert actual_blob == blob


def test_aggregate_known_vector_and_frozen_order() -> None:
    module = _module()
    payloads = (b"routing\n", b"tasks\0bytes", b"", b'{"manifest":true}\n')
    forward = {name: value for name, value in zip(module.ARTIFACT_NAMES, payloads)}
    reverse = {name: forward[name] for name in reversed(module.ARTIFACT_NAMES)}
    assert module._aggregate_sha256(forward) == (
        "1b90289cc99d6da2ef5066ddf2b771a91da8c0f2cfb9fab41c8678397e51dd32"
    )
    assert module._aggregate_sha256(reverse) == module._aggregate_sha256(forward)
    changed = dict(forward)
    changed[module.ARTIFACT_NAMES[0]] += b"x"
    assert module._aggregate_sha256(changed) != module._aggregate_sha256(forward)


@pytest.mark.parametrize(
    "name",
    (
        "",
        ".",
        "..",
        "../object",
        "/absolute",
        "nested/object",
        "object..name",
        ".current11-dataset-partial-supervision-routing-sidecar-v2.object-sha256-"
        + "A" * 64
        + "-"
        + "0" * 32,
        ".current11-dataset-partial-supervision-routing-sidecar-v2.object-sha256-"
        + "0" * 63
        + "-"
        + "0" * 32,
        ".current11-dataset-partial-supervision-routing-sidecar-v2.object-sha256-"
        + "0" * 64
        + "-"
        + "0" * 31,
        ".wrong.object-sha256-" + "0" * 64 + "-" + "0" * 32,
    ),
)
def test_object_basename_grammar_rejects_invalid(name: str) -> None:
    with pytest.raises(ValueError, match=_module().ERROR_TOKEN):
        _module()._parse_object_basename(name)


def test_materialize_relative_alias_complete_object_summary_and_single_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _module()
    expected = _builder_artifacts()
    real_symlink = module.os.symlink
    calls: list[tuple[object, ...]] = []

    def spy(*args, **kwargs):
        calls.append((*args, kwargs))
        canonical = _output(tmp_path)
        assert not os.path.lexists(canonical)
        object_path = tmp_path / args[0]
        assert stat.S_IMODE(object_path.lstat().st_mode) == 0o755
        assert {item.name for item in object_path.iterdir()} == set(module.ARTIFACT_NAMES)
        return real_symlink(*args, **kwargs)

    monkeypatch.setattr(module.os, "symlink", spy)
    summary = _materialize(tmp_path)
    canonical, object_path, leaves = _published_paths(tmp_path)
    assert len(calls) == 1
    source, target, keywords = calls[0]
    assert source == object_path.name and target == canonical.name
    assert keywords == {"target_is_directory": True, "dir_fd": keywords["dir_fd"]}
    assert canonical.is_symlink() and os.readlink(canonical) == object_path.name
    assert object_path.parent == canonical.parent
    aggregate, nonce = module._parse_object_basename(object_path.name)
    assert len(nonce) == 32 and aggregate == module._aggregate_sha256(expected)
    assert stat.S_IMODE(object_path.lstat().st_mode) == 0o755
    assert tuple(summary["artifacts"]) == module.ARTIFACT_NAMES
    for name, path in zip(module.ARTIFACT_NAMES, leaves):
        assert path.read_bytes() == expected[name]
        assert stat.S_ISREG(path.lstat().st_mode) and not path.is_symlink()
        assert stat.S_IMODE(path.lstat().st_mode) == 0o644
    assert summary["operation"] == "materialize"
    assert summary["output_path"] == str(canonical)
    assert summary["canonical_entry_type"] == "relative_symlink"
    assert summary["canonical_symlink_target"] == object_path.name
    assert summary["object_directory_name"] == object_path.name
    assert summary["canonical_identity"]["st_dev"] == tmp_path.stat().st_dev
    assert summary["object_identity"]["st_dev"] == tmp_path.stat().st_dev
    assert summary["aggregate_sha256"] == aggregate
    assert summary["artifact_file_count"] == 4
    assert summary["source_v1_materializer_commit"] == module.BASE_COMMIT
    assert summary["source_v1_materializer_sha256"] == module.SOURCE_V1_MATERIALIZER_SHA256
    assert summary["routing_record_count"] == 275
    assert summary["semantic_task_count"] == 25
    assert summary["sample_count"] == 11
    assert summary["unit_000001_parity_passed"] is True
    expected_lifecycle = module._derive_lifecycle(module._collect_lifecycle(ROOT))
    assert summary["repository_lifecycle"] == expected_lifecycle
    assert summary["readiness"] == module._readiness()
    assert set(tmp_path.iterdir()) == {canonical, object_path}


def test_second_materialize_fails_closed_and_preserves_published_tree(tmp_path: Path) -> None:
    _materialize(tmp_path)
    canonical, object_path, leaves = _published_paths(tmp_path)
    before = {path: _entry_snapshot(path) for path in (canonical, object_path, *leaves)}
    with pytest.raises(ValueError, match=_module().ERROR_TOKEN):
        _materialize(tmp_path)
    after = {path: _entry_snapshot(path) for path in (canonical, object_path, *leaves)}
    assert before == after
    assert len(_object_residue(tmp_path)) == 1


def test_check_double_run_is_read_only_and_reports_stored_manifest_sha(tmp_path: Path) -> None:
    module = _module()
    _materialize(tmp_path)
    canonical, object_path, leaves = _published_paths(tmp_path)
    paths = (canonical, object_path, *leaves)
    before = {path: _entry_snapshot(path) for path in paths}
    first = _check(tmp_path)
    middle = {path: _entry_snapshot(path) for path in paths}
    second = _check(tmp_path)
    after = {path: _entry_snapshot(path) for path in paths}
    expected_lifecycle = module._derive_lifecycle(module._collect_lifecycle(ROOT))
    assert first == second and first["operation"] == "check"
    assert first["repository_lifecycle"] == expected_lifecycle
    assert second["repository_lifecycle"] == expected_lifecycle
    assert before == middle == after
    manifest = object_path / module.ARTIFACT_NAMES[3]
    assert first["artifacts"][module.ARTIFACT_NAMES[3]]["sha256"] == hashlib.sha256(
        manifest.read_bytes()
    ).hexdigest()


def test_check_allows_only_fresh_manifest_dynamic_lifecycle_exact3(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _module()
    stored = _builder_artifacts()
    _materialize(tmp_path)

    def mutate(manifest: dict[str, object]) -> None:
        manifest["repository_lifecycle"].update(
            {"origin_main": "a" * 40, "ahead": 7, "behind": 3}
        )

    fresh = _mutate_manifest(stored, mutate)
    _install_builder_result(monkeypatch, fresh)
    first = _check(tmp_path)
    second = _check(tmp_path)
    assert first == second
    stored_manifest = stored[module.ARTIFACT_NAMES[3]]
    fresh_manifest = fresh[module.ARTIFACT_NAMES[3]]
    assert first["artifacts"][module.ARTIFACT_NAMES[3]]["sha256"] == hashlib.sha256(
        stored_manifest
    ).hexdigest()
    assert hashlib.sha256(stored_manifest).digest() != hashlib.sha256(fresh_manifest).digest()


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("lifecycle_profile", "drifted"),
        ("formal_candidate_commit", "b" * 40),
        ("base_commit", "c" * 40),
        ("future_formal_subject", "drifted"),
        ("candidate_paths", ["drifted/path"]),
        ("origin_main", "invalid"),
        ("ahead", -1),
        ("ahead", "1"),
        ("behind", False),
    ),
)
def test_check_rejects_manifest_lifecycle_contract_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
) -> None:
    _materialize(tmp_path)

    def mutate(manifest: dict[str, object]) -> None:
        manifest["repository_lifecycle"][field] = value

    _install_builder_result(monkeypatch, _mutate_manifest(_builder_artifacts(), mutate))
    with pytest.raises(ValueError, match=_module().ERROR_TOKEN):
        _check(tmp_path)


@pytest.mark.parametrize("which", ("repo_root", "state_root", "output_path"))
def test_relative_paths_fail_closed(tmp_path: Path, which: str) -> None:
    arguments = {
        "repo_root": ROOT,
        "state_root": STATE,
        "output_path": _output(tmp_path),
    }
    arguments[which] = Path("relative")
    with pytest.raises(ValueError, match=_module().ERROR_TOKEN):
        _module().materialize_covapie_current11_dataset_partial_supervision_routing_sidecar_gpfs_atomic_alias_v2(
            **arguments
        )


def test_wrong_basename_repository_output_and_missing_parent_fail_closed(
    tmp_path: Path,
) -> None:
    module = _module()
    outputs = (
        tmp_path / "wrong",
        ROOT / module.CANONICAL_BASENAME,
        tmp_path / "missing" / module.CANONICAL_BASENAME,
    )
    for output in outputs:
        with pytest.raises(ValueError, match=module.ERROR_TOKEN):
            module.materialize_covapie_current11_dataset_partial_supervision_routing_sidecar_gpfs_atomic_alias_v2(
                repo_root=ROOT, state_root=STATE, output_path=output
            )


@pytest.mark.parametrize("which", ("repo_root", "state_root", "output_path"))
def test_non_exact_path_types_fail_closed(tmp_path: Path, which: str) -> None:
    arguments: dict[str, object] = {
        "repo_root": ROOT,
        "state_root": STATE,
        "output_path": _output(tmp_path),
    }
    arguments[which] = os.fspath(arguments[which])
    with pytest.raises(ValueError, match=_module().ERROR_TOKEN):
        _module().materialize_covapie_current11_dataset_partial_supervision_routing_sidecar_gpfs_atomic_alias_v2(
            **arguments
        )


def test_symlink_parent_and_broken_canonical_fail_closed(tmp_path: Path) -> None:
    module = _module()
    real = tmp_path / "real"
    real.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    for output in (
        alias / module.CANONICAL_BASENAME,
        real / module.CANONICAL_BASENAME,
    ):
        if output.parent == real:
            output.symlink_to("missing", target_is_directory=True)
        with pytest.raises(ValueError, match=module.ERROR_TOKEN):
            module.materialize_covapie_current11_dataset_partial_supervision_routing_sidecar_gpfs_atomic_alias_v2(
                repo_root=ROOT, state_root=STATE, output_path=output
            )


@pytest.mark.parametrize("kind", ("file", "directory", "valid_symlink", "invalid_symlink"))
def test_preexisting_canonical_entry_fails_closed(tmp_path: Path, kind: str) -> None:
    target = _output(tmp_path)
    if kind == "file":
        target.write_bytes(b"competitor")
    elif kind == "directory":
        target.mkdir()
    elif kind == "valid_symlink":
        target.symlink_to("unrelated", target_is_directory=True)
    else:
        target.symlink_to("../outside", target_is_directory=True)
    before = _entry_snapshot(target)
    with pytest.raises(ValueError, match=_module().ERROR_TOKEN):
        _materialize(tmp_path)
    assert _entry_snapshot(target) == before
    assert not _object_residue(tmp_path)


def test_symlink_eexist_race_preserves_competitor_and_cleans_object(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _module()
    real_symlink = module.os.symlink
    competitor = b"competitor"

    def race(*_args, **_kwargs):
        _output(tmp_path).write_bytes(competitor)
        raise FileExistsError()

    monkeypatch.setattr(module.os, "symlink", race)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _materialize(tmp_path)
    assert _output(tmp_path).read_bytes() == competitor
    assert not _output(tmp_path).is_symlink()
    assert not _object_residue(tmp_path)
    monkeypatch.setattr(module.os, "symlink", real_symlink)


def test_object_nonce_collision_retries_without_removing_collision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _module()
    artifacts = _builder_artifacts()
    digest = module._aggregate_sha256(artifacts)
    first_nonce = "1" * 32
    second_nonce = "2" * 32
    collision = tmp_path / f"{module.OBJECT_PREFIX}{digest}-{first_nonce}"
    collision.mkdir()
    nonces = iter((first_nonce, second_nonce))
    monkeypatch.setattr(module.secrets, "token_hex", lambda _size: next(nonces))
    _materialize(tmp_path)
    assert collision.is_dir() and not list(collision.iterdir())
    assert os.readlink(_output(tmp_path)).endswith(second_nonce)


def test_sixty_four_object_collisions_fail_closed_without_removal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _module()
    digest = module._aggregate_sha256(_builder_artifacts())
    nonce = "3" * 32
    collision = tmp_path / f"{module.OBJECT_PREFIX}{digest}-{nonce}"
    collision.mkdir()
    monkeypatch.setattr(module.secrets, "token_hex", lambda _size: nonce)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _materialize(tmp_path)
    assert collision.is_dir() and not list(collision.iterdir())
    assert not os.path.lexists(_output(tmp_path))


@pytest.mark.parametrize("nonce", ("", "A" * 32, "0" * 31, "g" * 32, 0, None))
def test_invalid_monkeypatched_nonce_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, nonce: object
) -> None:
    monkeypatch.setattr(_module().secrets, "token_hex", lambda _size: nonce)
    with pytest.raises(ValueError, match=_module().ERROR_TOKEN):
        _materialize(tmp_path)
    assert not os.path.lexists(_output(tmp_path)) and not _object_residue(tmp_path)


@pytest.mark.parametrize(
    "failure",
    (
        "first_leaf_create",
        "second_leaf_create",
        "short_write",
        "file_chmod",
        "file_fsync",
        "object_chmod",
        "object_fsync",
        "prepublication_validation",
    ),
)
def test_prepublication_failures_clean_owned_object(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    module = _module()
    if failure in ("first_leaf_create", "second_leaf_create"):
        real_open = module.os.open
        creates = 0

        def fail_open(path, flags, *args, **kwargs):
            nonlocal creates
            if flags & os.O_CREAT:
                creates += 1
                if creates == (1 if failure == "first_leaf_create" else 2):
                    raise OSError("leaf create")
            return real_open(path, flags, *args, **kwargs)

        monkeypatch.setattr(module.os, "open", fail_open)
    elif failure == "short_write":
        monkeypatch.setattr(
            module,
            "_write_all",
            lambda *_args: (_ for _ in ()).throw(OSError("short write")),
        )
    elif failure in ("file_chmod", "object_chmod"):
        real_fchmod = module.os.fchmod

        def fail_chmod(fd: int, mode: int):
            is_directory = stat.S_ISDIR(os.fstat(fd).st_mode)
            if is_directory == (failure == "object_chmod"):
                raise OSError("chmod")
            return real_fchmod(fd, mode)

        monkeypatch.setattr(module.os, "fchmod", fail_chmod)
    elif failure in ("file_fsync", "object_fsync"):
        real_fsync = module.os.fsync

        def fail_fsync(fd: int):
            is_directory = stat.S_ISDIR(os.fstat(fd).st_mode)
            if is_directory == (failure == "object_fsync"):
                raise OSError("fsync")
            return real_fsync(fd)

        monkeypatch.setattr(module.os, "fsync", fail_fsync)
    else:
        monkeypatch.setattr(
            module,
            "_validate_stored_exact4",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError(module.ERROR_TOKEN)),
        )
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _materialize(tmp_path)
    assert not os.path.lexists(_output(tmp_path)) and not _object_residue(tmp_path)


def test_alias_unexpected_failure_with_absent_canonical_cleans_object(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _module()
    monkeypatch.setattr(
        module.os,
        "symlink",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("publication")),
    )
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _materialize(tmp_path)
    assert not os.path.lexists(_output(tmp_path)) and not _object_residue(tmp_path)


def test_alias_failure_with_unrelated_canonical_preserves_competitor_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _module()
    real_symlink = module.os.symlink

    def fail(*_args, **_kwargs):
        real_symlink("unrelated", _output(tmp_path), target_is_directory=True)
        raise OSError("publication")

    monkeypatch.setattr(module.os, "symlink", fail)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _materialize(tmp_path)
    assert _output(tmp_path).is_symlink() and os.readlink(_output(tmp_path)) == "unrelated"
    assert not _object_residue(tmp_path)


def test_alias_failure_pointing_to_owned_object_preserves_both(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _module()
    real_symlink = module.os.symlink

    def fail(source, target, **kwargs):
        real_symlink(source, target, **kwargs)
        raise OSError("ambiguous publication result")

    monkeypatch.setattr(module.os, "symlink", fail)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _materialize(tmp_path)
    assert _output(tmp_path).is_symlink()
    assert len(_object_residue(tmp_path)) == 1
    assert (tmp_path / os.readlink(_output(tmp_path))).is_dir()


def test_postpublication_parent_fsync_failure_preserves_alias_and_object(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _module()
    real_fsync = module.os.fsync
    directory_calls = 0

    def fail_second_directory_fsync(fd: int):
        nonlocal directory_calls
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            directory_calls += 1
            if directory_calls == 2:
                raise OSError("parent fsync")
        return real_fsync(fd)

    monkeypatch.setattr(module.os, "fsync", fail_second_directory_fsync)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _materialize(tmp_path)
    canonical, object_path, leaves = _published_paths(tmp_path)
    assert canonical.is_symlink() and object_path.is_dir() and len(leaves) == 4


def test_postpublication_validation_failure_preserves_alias_and_object(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _module()
    real_validate = module._validate_stored_exact4
    calls = 0

    def fail_second(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ValueError(module.ERROR_TOKEN)
        return real_validate(*args, **kwargs)

    monkeypatch.setattr(module, "_validate_stored_exact4", fail_second)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _materialize(tmp_path)
    canonical, object_path, leaves = _published_paths(tmp_path)
    assert canonical.is_symlink() and object_path.is_dir() and len(leaves) == 4


def test_cleanup_failure_uses_distinct_token_and_preserves_original_cause(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _module()
    original = OSError("publication")
    monkeypatch.setattr(
        module.os, "symlink", lambda *_args, **_kwargs: (_ for _ in ()).throw(original)
    )
    monkeypatch.setattr(
        module.os,
        "unlink",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("cleanup")),
    )
    with pytest.raises(ValueError, match=module.CLEANUP_ERROR_TOKEN) as caught:
        _materialize(tmp_path)
    assert caught.value.__cause__ is original
    assert len(_object_residue(tmp_path)) == 1


def test_cleanup_leaf_identity_replacement_fails_safe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _module()
    real_validate = module._validate_stored_exact4

    def replace_then_fail(stored, fresh, repository, **kwargs):
        result = real_validate(stored, fresh, repository, **kwargs)
        object_path = _object_residue(tmp_path)[0]
        leaf = object_path / module.ARTIFACT_NAMES[0]
        leaf.rename(object_path / "original-leaf")
        leaf.write_bytes(b"replacement")
        raise OSError("prepublication replacement")

    monkeypatch.setattr(module, "_validate_stored_exact4", replace_then_fail)
    with pytest.raises(ValueError, match=module.CLEANUP_ERROR_TOKEN):
        _materialize(tmp_path)
    object_path = _object_residue(tmp_path)[0]
    assert (object_path / module.ARTIFACT_NAMES[0]).read_bytes() == b"replacement"
    assert not os.path.lexists(_output(tmp_path))


def test_cleanup_object_identity_replacement_fails_safe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _module()

    def replace_then_fail(source, _target, **_kwargs):
        original = tmp_path / source
        backup = tmp_path / f"backup-{source}"
        original.rename(backup)
        original.mkdir(mode=0o700)
        raise OSError("publication after replacement")

    monkeypatch.setattr(module.os, "symlink", replace_then_fail)
    with pytest.raises(ValueError, match=module.CLEANUP_ERROR_TOKEN):
        _materialize(tmp_path)
    assert len(tuple(tmp_path.glob("backup-*"))) == 1
    assert len(_object_residue(tmp_path)) == 1


@pytest.mark.parametrize(
    "link_text",
    (
        ".current11-dataset-partial-supervision-routing-sidecar-v2.object-sha256-"
        + "0" * 64
        + "-"
        + "0" * 32,
        "missing",
        "/absolute",
        "nested/object",
        "..",
        "object..name",
        ".wrong.object-sha256-" + "0" * 64 + "-" + "0" * 32,
        ".current11-dataset-partial-supervision-routing-sidecar-v2.object-sha256-"
        + "0" * 63
        + "-"
        + "0" * 32,
        ".current11-dataset-partial-supervision-routing-sidecar-v2.object-sha256-"
        + "0" * 64
        + "-"
        + "A" * 32,
    ),
)
def test_check_rejects_broken_or_malformed_alias(tmp_path: Path, link_text: str) -> None:
    _output(tmp_path).symlink_to(link_text, target_is_directory=True)
    before = _entry_snapshot(_output(tmp_path))
    with pytest.raises(ValueError, match=_module().ERROR_TOKEN):
        _check(tmp_path)
    assert _entry_snapshot(_output(tmp_path)) == before


@pytest.mark.parametrize("kind", ("file", "directory"))
def test_check_rejects_non_symlink_canonical(tmp_path: Path, kind: str) -> None:
    target = _output(tmp_path)
    target.write_bytes(b"entry") if kind == "file" else target.mkdir()
    with pytest.raises(ValueError, match=_module().ERROR_TOKEN):
        _check(tmp_path)


@pytest.mark.parametrize("kind", ("file", "symlink"))
def test_check_rejects_object_file_or_symlink(tmp_path: Path, kind: str) -> None:
    module = _module()
    object_name = f"{module.OBJECT_PREFIX}{'0' * 64}-{'0' * 32}"
    object_path = tmp_path / object_name
    if kind == "file":
        object_path.write_bytes(b"not a directory")
    else:
        real = tmp_path / "real-object"
        real.mkdir()
        object_path.symlink_to(real, target_is_directory=True)
    _output(tmp_path).symlink_to(object_name, target_is_directory=True)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _check(tmp_path)


@pytest.mark.parametrize(
    "mutation",
    ("object_mode", "missing_leaf", "extra_leaf", "leaf_mode", "leaf_symlink", "leaf_special"),
)
def test_check_rejects_object_inventory_type_and_mode_drift(
    tmp_path: Path, mutation: str
) -> None:
    module = _module()
    _materialize(tmp_path)
    _canonical, object_path, leaves = _published_paths(tmp_path)
    if mutation == "object_mode":
        object_path.chmod(0o700)
    elif mutation == "missing_leaf":
        leaves[0].unlink()
    elif mutation == "extra_leaf":
        (object_path / "extra").write_bytes(b"extra")
    elif mutation == "leaf_mode":
        leaves[0].chmod(0o600)
    elif mutation == "leaf_symlink":
        leaves[0].unlink()
        leaves[0].symlink_to(leaves[1].name)
    else:
        leaves[0].unlink()
        os.mkfifo(leaves[0], 0o644)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _check(tmp_path)


def test_check_rejects_stored_aggregate_not_matching_object_name(tmp_path: Path) -> None:
    module = _module()
    _materialize(tmp_path)
    _canonical, object_path, _leaves = _published_paths(tmp_path)
    manifest_path = object_path / module.ARTIFACT_NAMES[3]
    manifest = json.loads(manifest_path.read_bytes())
    manifest["repository_lifecycle"].update(
        {"origin_main": "d" * 40, "ahead": 2, "behind": 1}
    )
    manifest_path.write_bytes(
        (json.dumps(manifest, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    )
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _check(tmp_path)


def test_check_rejects_stored_csv_byte_drift(tmp_path: Path) -> None:
    module = _module()
    _materialize(tmp_path)
    _canonical, object_path, _leaves = _published_paths(tmp_path)
    csv_path = object_path / module.ARTIFACT_NAMES[0]
    payload = csv_path.read_bytes()
    csv_path.write_bytes(payload[:-2] + b"X\n")
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _check(tmp_path)


@pytest.mark.parametrize("identity", ("alias", "object", "leaf"))
def test_check_detects_identity_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, identity: str
) -> None:
    module = _module()
    _materialize(tmp_path)
    canonical, object_path, leaves = _published_paths(tmp_path)
    real_validate = module._validate_stored_exact4
    changed = False

    def replace_after_validation(*args, **kwargs):
        nonlocal changed
        result = real_validate(*args, **kwargs)
        if changed:
            return result
        changed = True
        if identity == "alias":
            target = os.readlink(canonical)
            canonical.rename(tmp_path / "original-alias")
            canonical.symlink_to(target, target_is_directory=True)
        elif identity == "object":
            backup = tmp_path / "replaced-object"
            object_path.rename(backup)
            object_path.mkdir(mode=0o755)
        else:
            payload = leaves[0].read_bytes()
            leaves[0].rename(object_path / "original-leaf")
            leaves[0].write_bytes(payload)
            leaves[0].chmod(0o644)
        return result

    monkeypatch.setattr(module, "_validate_stored_exact4", replace_after_validation)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _check(tmp_path)


def test_v1_source_binding_drift_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(_module(), "SOURCE_V1_MATERIALIZER_SHA256", "0" * 64)
    with pytest.raises(ValueError, match=_module().ERROR_TOKEN):
        _materialize(tmp_path)
    assert not os.path.lexists(_output(tmp_path)) and not _object_residue(tmp_path)


@pytest.mark.parametrize("artifact_index", (0, 1, 2))
def test_check_rejects_fresh_csv_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, artifact_index: int
) -> None:
    module = _module()
    _materialize(tmp_path)
    artifacts = _builder_artifacts()
    name = module.ARTIFACT_NAMES[artifact_index]
    changed = dict(artifacts)
    changed[name] = changed[name][:-2] + b"X\n"
    _install_builder_result(monkeypatch, changed)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _check(tmp_path)


@pytest.mark.parametrize("mutation", ("stable_manifest", "source_binding", "readiness"))
def test_check_rejects_stable_manifest_source_and_readiness_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    _materialize(tmp_path)

    def change(manifest: dict[str, object]) -> None:
        if mutation == "stable_manifest":
            manifest["blocking_reason_vocabulary"].append("DRIFT")
        elif mutation == "source_binding":
            manifest["source_bindings"]["canonical_final_index"]["bytes"] += 1
        else:
            manifest["readiness"]["ready_for_training"] = True

    _install_builder_result(monkeypatch, _mutate_manifest(_builder_artifacts(), change))
    with pytest.raises(ValueError, match=_module().ERROR_TOKEN):
        _check(tmp_path)


def test_fresh_exact275_unit_provenance_exact5_and_closed_readiness() -> None:
    module = _module()
    artifacts = _builder_artifacts()
    manifest = module._v1._validate_builder_artifacts(artifacts, ROOT)
    records = module._v1._csv_rows(artifacts[module.ARTIFACT_NAMES[0]])
    assert len(records) == 275
    assert manifest["routing_record_count"] == 275
    assert manifest["sample_count"] == 11
    assert manifest["semantic_task_count"] == 25
    assert manifest["canonical_mask_semantics"] == list(module._v1.EXPECTED_MASKS)
    assert {item["semantic_name"] for item in manifest["canonical_mask_semantics"]} == {
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    }
    unit_ids = set(manifest["unit_000001_parity"]["sample_index_row_ids"])
    assert sum(record["sample_index_row_id"] in unit_ids for record in records) == 50
    assert sum(record["sample_index_row_id"] not in unit_ids for record in records) == 225
    assert manifest["unit_000001_parity"]["passed"] is True
    readiness = module._readiness()
    assert readiness["gpfs_atomic_alias_materializer_v2_implemented"] is True
    assert readiness["ready_for_formal_sidecar_materialization_execution"] is True
    assert readiness["ready_for_tensor_projection_contract_design"] is False
    assert readiness["ready_for_training"] is False


def test_cli_materialize_and_check_success(tmp_path: Path) -> None:
    common = (
        "--repo-root",
        str(ROOT),
        "--state-root",
        str(STATE),
        "--output-path",
        str(_output(tmp_path)),
    )
    materialized = _cli(*common)
    assert materialized.returncode == 0 and materialized.stderr == b""
    assert _canonical_json(materialized.stdout)["operation"] == "materialize"
    checked = _cli(*common, "--check")
    assert checked.returncode == 0 and checked.stderr == b""
    assert _canonical_json(checked.stdout)["operation"] == "check"


@pytest.mark.parametrize(
    "arguments",
    (
        (),
        ("-h",),
        ("--help",),
        ("--unknown",),
        ("--output-dir", "x"),
        ("--overwrite",),
        ("--force",),
        ("--repair",),
        ("--rename",),
        ("--renameat2",),
        ("--lock",),
        ("--copy",),
        ("--approve",),
        ("--tensorize",),
        ("--train",),
        ("--output-format", "json"),
        ("--manifest-only",),
        ("--nonce", "0" * 32),
        ("--digest", "0" * 64),
        ("--object-name", "object"),
        ("--publication", "override"),
        ("positional",),
    ),
)
def test_cli_invalid_interfaces_fail_closed(arguments: tuple[str, ...]) -> None:
    completed = _cli(*arguments)
    assert completed.returncode == 1
    assert completed.stdout == b""
    assert completed.stderr == b"ERROR " + _module().ERROR_TOKEN.encode("ascii") + b"\n"


def test_current_repository_lifecycle_profile() -> None:
    module = _module()
    facts = module._collect_lifecycle(ROOT)
    lifecycle = module._derive_lifecycle(facts)
    assert lifecycle["lifecycle_profile"] in {
        "dataset_routing_sidecar_gpfs_atomic_alias_materializer_v2_precommit_candidate",
        "dataset_routing_sidecar_gpfs_atomic_alias_materializer_v2_committed_unpushed",
        "dataset_routing_sidecar_gpfs_atomic_alias_materializer_v2_published_successor",
    }
    assert facts["branch"] == "main"


def test_lifecycle_exact3_in_base_anchored_temporary_git(
    tmp_path: Path, request: pytest.FixtureRequest
) -> None:
    module = _module()
    repository = tmp_path / ROOT.name
    node = f"{module.TEST_PATH}::test_current_repository_lifecycle_profile"

    def cleanup() -> None:
        if repository.exists():
            shutil.rmtree(repository)

    request.addfinalizer(cleanup)
    subprocess.run(
        ("git", "clone", "--no-hardlinks", "--quiet", str(ROOT), str(repository)),
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    def git(*arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ("git", *arguments),
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        )

    def run_node(expected: str) -> None:
        result = subprocess.run(
            (sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", node),
            cwd=repository,
            check=False,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src", "PYTHONDONTWRITEBYTECODE": "1"},
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "1 passed" in result.stdout
        script = (
            "import sys;sys.path.insert(0,'src');"
            f"from {MODULE_NAME} import _derive_lifecycle,_collect_lifecycle;"
            "from pathlib import Path;"
            "print(_derive_lifecycle(_collect_lifecycle(Path.cwd()))['lifecycle_profile'])"
        )
        profile = subprocess.run(
            (sys.executable, "-B", "-c", script),
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        ).stdout.strip()
        assert profile == expected

    git("checkout", "-B", "main", module.BASE_COMMIT)
    git("update-ref", "refs/remotes/origin/main", module.BASE_COMMIT)
    for relative in module.CANDIDATE_PATHS:
        target = repository / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
        target.chmod(0o644)
    run_node("dataset_routing_sidecar_gpfs_atomic_alias_materializer_v2_precommit_candidate")
    git("add", "--", *module.CANDIDATE_PATHS)
    git(
        "-c",
        "user.name=CovaPIE Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "--quiet",
        "-m",
        module.FORMAL_COMMIT_SUBJECT,
    )
    formal = git("rev-parse", "HEAD").stdout.strip()
    run_node("dataset_routing_sidecar_gpfs_atomic_alias_materializer_v2_committed_unpushed")
    git("update-ref", "refs/remotes/origin/main", formal)
    run_node("dataset_routing_sidecar_gpfs_atomic_alias_materializer_v2_published_successor")
    cleanup()
    assert not os.path.lexists(repository)


def test_repository_exact4_file_safety() -> None:
    module = _module()
    assert len(module.CANDIDATE_PATHS) == 4
    for relative in module.CANDIDATE_PATHS:
        path = ROOT / relative
        metadata = path.lstat()
        payload = path.read_bytes()
        assert stat.S_ISREG(metadata.st_mode) and not path.is_symlink()
        assert stat.S_IMODE(metadata.st_mode) == 0o644
        assert len(payload) < 1024 * 1024
        assert not payload.startswith(b"\xef\xbb\xbf") and b"\0" not in payload
        assert all(not line.endswith((b" ", b"\t")) for line in payload.splitlines())
