"""Tests for the Current11 routing-sidecar formal materializer."""

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
    "covalent_ext."
    "covapie_current11_dataset_partial_supervision_routing_sidecar_formal_materializer_v1"
)
CLI = ROOT / "scripts/materialize_covapie_current11_dataset_partial_supervision_routing_sidecar_v1.py"
SOURCE_EXACT4 = {
    "src/covalent_ext/covapie_current11_dataset_partial_supervision_routing_sidecar_v1.py": (
        65524,
        1336,
        "1be932e473107a2944cf916c288580b614c7b6710556ca54c099d742971344a5",
        "eb05e70f438bb8170ad4e68d1edb3bda6198d052",
    ),
    "scripts/check_covapie_current11_dataset_partial_supervision_routing_sidecar_v1.py": (
        2477,
        75,
        "6f0f8958fd589c21aaaa60ca867ee2a49c28f8a1aad6ff61d177502ac601946a",
        "19fd29aeb059b26dc80e2d47c8f6bebcf8b427aa",
    ),
    "tests/test_covapie_current11_dataset_partial_supervision_routing_sidecar_v1.py": (
        40866,
        875,
        "9ab8e08b7107394c3ac314ab8b9eed12272b37494ba35ef9046686d8af6f3979",
        "0d2d5bab0c307a0744c2c24ac41b43a9650267f7",
    ),
    "docs/covapie_current11_dataset_partial_supervision_routing_sidecar_v1_guide.md": (
        2860,
        23,
        "ed4d817952a1e5b2d2eb2f89593ca9fef774abd0fd212855d678d297368181a1",
        "a328ac7622cf68db0f5ad1de16d1bc790984ad09",
    ),
}


def _module():
    return importlib.import_module(MODULE_NAME)


def _builder_artifacts() -> dict[str, bytes]:
    return _module()._builder.build_covapie_current11_dataset_partial_supervision_routing_sidecar_v1(
        repo_root=ROOT, state_root=STATE
    )


def _materialize(output: Path) -> dict[str, object]:
    return _module().materialize_covapie_current11_dataset_partial_supervision_routing_sidecar_v1(
        repo_root=ROOT, state_root=STATE, output_dir=output
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


def _install_builder_result(monkeypatch: pytest.MonkeyPatch, artifacts: dict[str, bytes]) -> None:
    monkeypatch.setattr(
        _module()._builder,
        "build_covapie_current11_dataset_partial_supervision_routing_sidecar_v1",
        lambda **_kwargs: artifacts,
    )


def _with_lifecycle_values(
    artifacts: dict[str, bytes], **values: object
) -> dict[str, bytes]:
    def mutate(manifest: dict[str, object]) -> None:
        manifest["repository_lifecycle"].update(values)

    return _mutate_manifest(artifacts, mutate)


def test_unique_keyword_only_public_api_and_silent_import(
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = importlib.reload(_module())
    assert capsys.readouterr() == ("", "")
    assert module.__all__ == (
        "materialize_covapie_current11_dataset_partial_supervision_routing_sidecar_v1",
    )
    signature = inspect.signature(
        module.materialize_covapie_current11_dataset_partial_supervision_routing_sidecar_v1
    )
    assert tuple(signature.parameters) == ("repo_root", "state_root", "output_dir")
    assert all(item.kind is inspect.Parameter.KEYWORD_ONLY for item in signature.parameters.values())


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


def test_published_builder_exact4_is_frozen() -> None:
    for relative, (byte_count, line_count, digest, blob) in SOURCE_EXACT4.items():
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


def test_materialize_exact4_modes_bytes_summary_and_no_residue(tmp_path: Path) -> None:
    module = _module()
    expected = _builder_artifacts()
    target = tmp_path / "formal-target"
    summary = _materialize(target)
    assert summary["schema_version"] == module.SCHEMA_VERSION
    assert summary["operation"] == "materialize"
    assert summary["output_dir"] == str(target)
    assert summary["artifact_file_count"] == 4
    assert tuple(summary["artifacts"]) == module.ARTIFACT_NAMES
    assert summary["source_builder_schema_version"] == module.SOURCE_BUILDER_SCHEMA_VERSION
    assert summary["source_builder_commit"] == module.SOURCE_BUILDER_COMMIT
    assert summary["source_builder_sha256"] == module.SOURCE_BUILDER_SHA256
    assert summary["sample_count"] == 11
    assert summary["semantic_task_count"] == 25
    assert summary["routing_record_count"] == 275
    assert summary["global_state_counts"] == module.EXPECTED_GLOBAL_COUNTS
    assert summary["unit_000001_parity_passed"] is True
    expected_lifecycle = module._derive_lifecycle(module._collect_lifecycle(ROOT))
    assert summary["repository_lifecycle"] == expected_lifecycle
    assert summary["readiness"] == module._readiness()
    assert stat.S_IMODE(target.lstat().st_mode) == 0o755 and not target.is_symlink()
    assert tuple(expected) == module.ARTIFACT_NAMES
    assert set(item.name for item in target.iterdir()) == set(module.ARTIFACT_NAMES)
    for name, payload in expected.items():
        path = target / name
        assert path.read_bytes() == payload
        assert stat.S_ISREG(path.lstat().st_mode) and not path.is_symlink()
        assert stat.S_IMODE(path.lstat().st_mode) == 0o644
        assert summary["artifacts"][name] == {
            "bytes": len(payload),
            "lines": payload.count(b"\n"),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    assert not list(tmp_path.glob(".covapie-current11-routing-stage-*"))
    assert _builder_artifacts() == expected


def test_second_materialize_fails_closed_without_target_change(tmp_path: Path) -> None:
    target = tmp_path / "target"
    _materialize(target)
    before = {path.name: (path.lstat(), path.read_bytes()) for path in target.iterdir()}
    with pytest.raises(ValueError, match=_module().ERROR_TOKEN):
        _materialize(target)
    after = {path.name: (path.lstat(), path.read_bytes()) for path in target.iterdir()}
    assert {name: value[1] for name, value in after.items()} == {
        name: value[1] for name, value in before.items()
    }
    assert {name: (value[0].st_dev, value[0].st_ino, value[0].st_mode) for name, value in after.items()} == {
        name: (value[0].st_dev, value[0].st_ino, value[0].st_mode) for name, value in before.items()
    }


def test_check_success_is_read_only_and_double_run_identical(tmp_path: Path) -> None:
    module = _module()
    target = tmp_path / "target"
    _materialize(target)
    before = {
        path.relative_to(tmp_path): (path.lstat().st_dev, path.lstat().st_ino, path.lstat().st_mode, path.lstat().st_mtime_ns)
        for path in (target, *target.iterdir())
    }
    first = module._verify_existing(repo_root=ROOT, state_root=STATE, output_dir=target)
    second = module._verify_existing(repo_root=ROOT, state_root=STATE, output_dir=target)
    assert first == second and first["operation"] == "check"
    after = {
        path.relative_to(tmp_path): (path.lstat().st_dev, path.lstat().st_ino, path.lstat().st_mode, path.lstat().st_mtime_ns)
        for path in (target, *target.iterdir())
    }
    assert before == after


def test_check_allows_only_dynamic_builder_lifecycle_exact3_and_reports_target_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _module()
    target = tmp_path / "target"
    target_artifacts = _builder_artifacts()
    _materialize(target)
    fresh_artifacts = _with_lifecycle_values(
        target_artifacts,
        origin_main="a" * 40,
        ahead=7,
        behind=3,
    )
    target_manifest = json.loads(target_artifacts[module.ARTIFACT_NAMES[3]])
    fresh_manifest = json.loads(fresh_artifacts[module.ARTIFACT_NAMES[3]])
    assert target_artifacts[module.ARTIFACT_NAMES[3]] != fresh_artifacts[module.ARTIFACT_NAMES[3]]
    assert module._stable_builder_manifest_projection(
        target_manifest
    ) == module._stable_builder_manifest_projection(fresh_manifest)
    assert all(
        target_artifacts[name] == fresh_artifacts[name] for name in module.ARTIFACT_NAMES[:3]
    )
    before = {
        path.name: (path.lstat().st_dev, path.lstat().st_ino, path.lstat().st_mode, path.read_bytes())
        for path in target.iterdir()
    }
    _install_builder_result(monkeypatch, fresh_artifacts)
    first = module._verify_existing(repo_root=ROOT, state_root=STATE, output_dir=target)
    second = module._verify_existing(repo_root=ROOT, state_root=STATE, output_dir=target)
    target_manifest_payload = target_artifacts[module.ARTIFACT_NAMES[3]]
    fresh_manifest_payload = fresh_artifacts[module.ARTIFACT_NAMES[3]]
    assert first == second
    assert first["artifacts"][module.ARTIFACT_NAMES[3]] == {
        "bytes": len(target_manifest_payload),
        "lines": target_manifest_payload.count(b"\n"),
        "sha256": hashlib.sha256(target_manifest_payload).hexdigest(),
    }
    assert first["artifacts"][module.ARTIFACT_NAMES[3]]["sha256"] != hashlib.sha256(
        fresh_manifest_payload
    ).hexdigest()
    after = {
        path.name: (path.lstat().st_dev, path.lstat().st_ino, path.lstat().st_mode, path.read_bytes())
        for path in target.iterdir()
    }
    assert before == after


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("lifecycle_profile", "dataset_partial_supervision_sidecar_committed_unpushed"),
        ("formal_candidate_commit", "b" * 40),
        ("base_commit", "c" * 40),
        ("future_formal_subject", "drifted subject"),
        ("candidate_paths", ["drifted/path"]),
    ),
)
def test_check_rejects_builder_lifecycle_stable_field_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
) -> None:
    target = tmp_path / "target"
    _materialize(target)
    changed = _with_lifecycle_values(_builder_artifacts(), **{field: value})
    _install_builder_result(monkeypatch, changed)
    with pytest.raises(ValueError, match=_module().ERROR_TOKEN):
        _module()._verify_existing(repo_root=ROOT, state_root=STATE, output_dir=target)


@pytest.mark.parametrize(
    ("mutation", "field", "value"),
    (
        ("missing", "ahead", None),
        ("extra", "unexpected", 0),
        ("invalid", "origin_main", "not-a-commit"),
        ("invalid", "ahead", -1),
        ("invalid", "ahead", "1"),
        ("invalid", "ahead", True),
        ("invalid", "behind", -1),
        ("invalid", "behind", "0"),
        ("invalid", "behind", False),
    ),
)
def test_check_rejects_builder_lifecycle_inventory_or_dynamic_type_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    field: str,
    value: object,
) -> None:
    target = tmp_path / "target"
    _materialize(target)
    artifacts = _builder_artifacts()

    def mutate(manifest: dict[str, object]) -> None:
        lifecycle = manifest["repository_lifecycle"]
        if mutation == "missing":
            lifecycle.pop(field)
        else:
            lifecycle[field] = value

    changed = _mutate_manifest(artifacts, mutate)
    _install_builder_result(monkeypatch, changed)
    with pytest.raises(ValueError, match=_module().ERROR_TOKEN):
        _module()._verify_existing(repo_root=ROOT, state_root=STATE, output_dir=target)


@pytest.mark.parametrize("mutation", ("non_lifecycle", "source_bindings", "readiness"))
def test_check_rejects_non_lifecycle_manifest_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    target = tmp_path / "target"
    _materialize(target)
    artifacts = _builder_artifacts()

    def mutate(manifest: dict[str, object]) -> None:
        if mutation == "non_lifecycle":
            manifest["blocking_reason_vocabulary"].append("DRIFTED_REASON")
        elif mutation == "source_bindings":
            manifest["source_bindings"]["canonical_final_index"]["bytes"] += 1
        else:
            manifest["readiness"]["ready_for_training"] = True

    _install_builder_result(monkeypatch, _mutate_manifest(artifacts, mutate))
    with pytest.raises(ValueError, match=_module().ERROR_TOKEN):
        _module()._verify_existing(repo_root=ROOT, state_root=STATE, output_dir=target)


@pytest.mark.parametrize("artifact_index", (0, 1, 2))
def test_check_rejects_fresh_csv_byte_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, artifact_index: int
) -> None:
    module = _module()
    target = tmp_path / "target"
    _materialize(target)
    artifacts = _builder_artifacts()
    name = module.ARTIFACT_NAMES[artifact_index]
    changed = dict(artifacts)
    old, new = (
        (b"CYS_SG_SAMPLE_INDEX_000001", b"CYS_SG_SAMPLE_INDEX_000000")
        if artifact_index != 1
        else (b"sample_identity_supervision", b"sample_identity_supervisioN")
    )
    changed[name] = changed[name].replace(old, new, 1)
    assert changed[name] != artifacts[name] and len(changed[name]) == len(artifacts[name])
    _install_builder_result(monkeypatch, changed)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        module._verify_existing(repo_root=ROOT, state_root=STATE, output_dir=target)


@pytest.mark.parametrize("which", ("repo", "state", "output"))
def test_relative_roots_fail_closed(tmp_path: Path, which: str) -> None:
    arguments = {"repo_root": ROOT, "state_root": STATE, "output_dir": tmp_path / "target"}
    arguments[f"{which}_root" if which != "output" else "output_dir"] = Path("relative")
    with pytest.raises(ValueError, match=_module().ERROR_TOKEN):
        _module().materialize_covapie_current11_dataset_partial_supervision_routing_sidecar_v1(
            **arguments
        )


def test_repository_output_missing_parent_and_symlink_parent_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=_module().ERROR_TOKEN):
        _materialize(ROOT / "forbidden-output")
    with pytest.raises(ValueError, match=_module().ERROR_TOKEN):
        _materialize(tmp_path / "missing" / "target")
    real = tmp_path / "real"
    real.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError, match=_module().ERROR_TOKEN):
        _materialize(alias / "target")
    assert not (real / "target").exists()


def test_existing_directory_file_and_symlink_targets_fail_closed(tmp_path: Path) -> None:
    for kind in ("directory", "file", "symlink"):
        parent = tmp_path / kind
        parent.mkdir()
        target = parent / "target"
        if kind == "directory":
            target.mkdir()
        elif kind == "file":
            target.write_text("competitor\n", encoding="utf-8")
        else:
            (parent / "elsewhere").mkdir()
            target.symlink_to(parent / "elsewhere", target_is_directory=True)
        with pytest.raises(ValueError, match=_module().ERROR_TOKEN):
            _materialize(target)
        assert os.path.lexists(target)


def test_publication_race_preserves_competitor_and_cleans_staging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _module()
    target = tmp_path / "target"

    def race(parent_fd: int, source: str, destination: str) -> None:
        del source
        os.mkdir(destination, 0o755, dir_fd=parent_fd)
        raise FileExistsError(errno.EEXIST, "competitor")

    import errno

    monkeypatch.setattr(module, "_rename_noreplace_at", race)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _materialize(target)
    assert target.is_dir() and not tuple(target.iterdir())
    assert not list(tmp_path.glob(".covapie-current11-routing-stage-*"))


@pytest.mark.parametrize(
    "failure", ("staging_open", "first_create", "second_write", "fsync", "chmod", "rename")
)
def test_staging_failures_leave_no_target_or_residue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    module = _module()
    target = tmp_path / "target"
    if failure == "staging_open":
        original = module.os.open
        failed = False

        def fail_staging_open(path, flags, *args, **kwargs):
            nonlocal failed
            if (
                not failed
                and isinstance(path, str)
                and path.startswith(".covapie-current11-routing-stage-")
                and flags & os.O_DIRECTORY
            ):
                failed = True
                raise OSError("staging open failure")
            return original(path, flags, *args, **kwargs)

        monkeypatch.setattr(module.os, "open", fail_staging_open)
    elif failure == "first_create":
        original = module.os.open

        def fail_open(path, flags, *args, **kwargs):
            if flags & os.O_EXCL:
                raise OSError("create failure")
            return original(path, flags, *args, **kwargs)

        monkeypatch.setattr(module.os, "open", fail_open)
    elif failure == "second_write":
        original = module._write_all
        calls = 0

        def fail_second(file_fd: int, payload: bytes) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("second write failure")
            original(file_fd, payload)

        monkeypatch.setattr(module, "_write_all", fail_second)
    elif failure == "fsync":
        monkeypatch.setattr(module.os, "fsync", lambda _fd: (_ for _ in ()).throw(OSError("fsync")))
    elif failure == "chmod":
        monkeypatch.setattr(module.os, "fchmod", lambda _fd, _mode: (_ for _ in ()).throw(OSError("chmod")))
    else:
        monkeypatch.setattr(
            module,
            "_rename_noreplace_at",
            lambda *_args: (_ for _ in ()).throw(OSError("rename")),
        )
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _materialize(target)
    assert not os.path.lexists(target)
    assert not list(tmp_path.glob(".covapie-current11-routing-stage-*"))


def test_postpublication_drift_fails_without_deleting_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _module()
    target = tmp_path / "target"
    original = module._verify_directory_fd

    def drift(directory_fd, identity, artifacts, repo_root):
        file_fd = os.open(module.ARTIFACT_NAMES[0], os.O_WRONLY | os.O_TRUNC, dir_fd=directory_fd)
        os.close(file_fd)
        original(directory_fd, identity, artifacts, repo_root)

    monkeypatch.setattr(module, "_verify_directory_fd", drift)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _materialize(target)
    assert target.is_dir()
    assert (target / module.ARTIFACT_NAMES[0]).read_bytes() == b""


def test_cleanup_identity_replacement_is_reported_and_not_deleted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _module()
    target = tmp_path / "target"

    def replace_then_fail(parent_fd: int, source: str, destination: str) -> None:
        del destination
        os.rename(source, f"{source}-original", src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
        os.mkdir(source, 0o700, dir_fd=parent_fd)
        raise OSError("publication failure")

    monkeypatch.setattr(module, "_rename_noreplace_at", replace_then_fail)
    with pytest.raises(module._CleanupFailure, match=module.CLEANUP_ERROR_TOKEN) as captured:
        _materialize(target)
    assert isinstance(captured.value.__cause__, OSError)
    assert not os.path.lexists(target)
    names = {path.name for path in tmp_path.iterdir()}
    assert any(name.endswith("-original") for name in names)
    assert any(name.startswith(".covapie-current11-routing-stage-") for name in names)


def test_cleanup_operation_failure_reports_original_as_cause(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _module()
    monkeypatch.setattr(
        module,
        "_rename_noreplace_at",
        lambda *_args: (_ for _ in ()).throw(OSError("original publication failure")),
    )
    monkeypatch.setattr(
        module,
        "_cleanup_staging",
        lambda *_args: (_ for _ in ()).throw(OSError("cleanup failure")),
    )
    with pytest.raises(module._CleanupFailure, match=module.CLEANUP_ERROR_TOKEN) as captured:
        _materialize(tmp_path / "target")
    assert isinstance(captured.value.__cause__, OSError)
    assert "original publication failure" in str(captured.value.__cause__)


@pytest.mark.parametrize(
    "mutation",
    ("missing", "extra", "bytes", "file_mode", "directory_mode", "symlink", "subdirectory"),
)
def test_check_inventory_bytes_modes_and_types_fail_closed(tmp_path: Path, mutation: str) -> None:
    module = _module()
    target = tmp_path / "target"
    _materialize(target)
    first = target / module.ARTIFACT_NAMES[0]
    if mutation == "missing":
        first.unlink()
    elif mutation == "extra":
        (target / "extra.txt").write_text("extra\n", encoding="utf-8")
    elif mutation == "bytes":
        first.write_bytes(first.read_bytes() + b"drift\n")
    elif mutation == "file_mode":
        first.chmod(0o600)
    elif mutation == "directory_mode":
        target.chmod(0o700)
    elif mutation == "symlink":
        first.unlink()
        first.symlink_to(target / module.ARTIFACT_NAMES[1])
    else:
        (target / "child").mkdir()
    with pytest.raises((ValueError, OSError), match=module.ERROR_TOKEN):
        module._verify_existing(repo_root=ROOT, state_root=STATE, output_dir=target)


@pytest.mark.parametrize(
    "mutation",
    ("records_rows", "task_rows", "sample_rows", "manifest_json", "manifest_lifecycle", "manifest_readiness"),
)
def test_check_content_contract_drift_fails_closed(tmp_path: Path, mutation: str) -> None:
    module = _module()
    target = tmp_path / "target"
    _materialize(target)
    if mutation in {"records_rows", "task_rows", "sample_rows"}:
        index = {"records_rows": 0, "task_rows": 1, "sample_rows": 2}[mutation]
        path = target / module.ARTIFACT_NAMES[index]
        lines = path.read_bytes().splitlines(keepends=True)
        path.write_bytes(b"".join(lines[:-1]))
    else:
        path = target / module.ARTIFACT_NAMES[3]
        if mutation == "manifest_json":
            path.write_bytes(b"{broken\n")
        else:
            manifest = json.loads(path.read_bytes())
            if mutation == "manifest_lifecycle":
                manifest["repository_lifecycle"]["lifecycle_profile"] = "drifted"
            else:
                manifest["readiness"]["ready_for_training"] = True
            path.write_bytes(
                (json.dumps(manifest, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
            )
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        module._verify_existing(repo_root=ROOT, state_root=STATE, output_dir=target)


@pytest.mark.parametrize("artifact_index", (0, 1, 2))
def test_builder_row_count_drift_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, artifact_index: int
) -> None:
    module = _module()
    artifacts = _builder_artifacts()
    name = module.ARTIFACT_NAMES[artifact_index]
    changed = dict(artifacts)
    changed[name] = changed[name].split(b"\n", 1)[0] + b"\n"
    _install_builder_result(monkeypatch, changed)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _materialize(tmp_path / "target")


def test_manifest_json_damage_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _module()
    artifacts = _builder_artifacts()
    artifacts[module.ARTIFACT_NAMES[3]] = b"{broken\n"
    _install_builder_result(monkeypatch, artifacts)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _materialize(tmp_path / "target")


@pytest.mark.parametrize("mutation", ("count", "name", "readiness", "unit", "b3", "sixth"))
def test_builder_inventory_and_semantics_drift_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    module = _module()
    artifacts = _builder_artifacts()
    if mutation == "count":
        artifacts.pop(module.ARTIFACT_NAMES[-1])
    elif mutation == "name":
        artifacts["unexpected.json"] = artifacts.pop(module.ARTIFACT_NAMES[-1])
    elif mutation == "readiness":
        artifacts = _mutate_manifest(
            artifacts, lambda manifest: manifest["readiness"].__setitem__("ready_for_training", True)
        )
    elif mutation == "unit":
        artifacts = _mutate_manifest(
            artifacts,
            lambda manifest: manifest["unit_000001_parity"]["state_counts"].__setitem__(
                "admissible_now", 9
            ),
        )
    elif mutation == "b3":
        artifacts = _mutate_manifest(
            artifacts, lambda manifest: manifest["canonical_mask_semantics"].pop(3)
        )
    else:
        artifacts = _mutate_manifest(
            artifacts,
            lambda manifest: manifest["canonical_mask_semantics"].append(
                {"semantic_name": "sixth_mask", "display_alias": "D"}
            ),
        )
    _install_builder_result(monkeypatch, artifacts)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _materialize(tmp_path / "target")


def test_unit_provenance_drift_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _module()
    artifacts = _builder_artifacts()
    lines = artifacts[module.ARTIFACT_NAMES[0]].decode("utf-8").splitlines()
    position = next(
        index for index, line in enumerate(lines)
        if "published_unit_000001_gate" in line
    )
    lines[position] = lines[position].replace(
        "published_unit_000001_gate", "coverage_audit_lineage"
    )
    changed = dict(artifacts)
    changed[module.ARTIFACT_NAMES[0]] = ("\n".join(lines) + "\n").encode("utf-8")
    _install_builder_result(monkeypatch, changed)
    with pytest.raises(ValueError, match=module.ERROR_TOKEN):
        _materialize(tmp_path / "target")


def test_fresh_builder_exact275_unit_provenance_masks_and_closed_flags() -> None:
    module = _module()
    artifacts = _builder_artifacts()
    manifest = module._validate_builder_artifacts(artifacts, ROOT)
    records = module._csv_rows(artifacts[module.ARTIFACT_NAMES[0]])
    assert len(records) == 275
    assert manifest["global_state_counts"] == module.EXPECTED_GLOBAL_COUNTS
    assert manifest["unit_000001_parity"]["state_counts"] == module.EXPECTED_UNIT_COUNTS
    assert tuple(manifest["canonical_mask_semantics"]) == module.EXPECTED_MASKS
    assert module.EXPECTED_MASKS[3] == {"semantic_name": "scaffold_only", "display_alias": "B3"}
    unit_ids = set(manifest["unit_000001_parity"]["sample_index_row_ids"])
    assert sum(record["sample_index_row_id"] in unit_ids for record in records) == 50
    assert sum(record["sample_index_row_id"] not in unit_ids for record in records) == 225
    assert {record["availability_mask_required"] for record in records} == {"true"}
    assert {record["current_runtime_consumer_available"] for record in records} == {"false"}
    assert {record["training_loss_authorized"] for record in records} == {"false"}


def test_cli_materialize_and_check_success(tmp_path: Path) -> None:
    target = tmp_path / "target"
    common = (
        "--repo-root",
        str(ROOT),
        "--state-root",
        str(STATE),
        "--output-dir",
        str(target),
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
        ("--overwrite",),
        ("--force",),
        ("--repair",),
        ("--approve",),
        ("--tensorize",),
        ("--train",),
        ("--output-format", "json"),
        ("--manifest-only",),
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
        "dataset_routing_sidecar_materializer_precommit_candidate",
        "dataset_routing_sidecar_materializer_committed_unpushed",
        "dataset_routing_sidecar_materializer_published_successor",
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
            ("git", *arguments), cwd=repository, check=True, capture_output=True, text=True
        )

    def run_node() -> None:
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

    git("checkout", "-B", "main", module.BASE_COMMIT)
    git("update-ref", "refs/remotes/origin/main", module.BASE_COMMIT)
    for relative in module.CANDIDATE_PATHS:
        target = repository / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
        target.chmod(0o644)
    run_node()
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
    run_node()
    git("update-ref", "refs/remotes/origin/main", formal)
    unrelated = repository / "UNRELATED_MATERIALIZER_SUCCESSOR.txt"
    unrelated.write_text("unrelated successor\n", encoding="utf-8")
    unrelated.chmod(0o644)
    git("add", "--", unrelated.name)
    git(
        "-c",
        "user.name=CovaPIE Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "--quiet",
        "-m",
        "unrelated materializer successor",
    )
    git("update-ref", "refs/remotes/origin/main", git("rev-parse", "HEAD").stdout.strip())
    run_node()
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
