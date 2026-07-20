from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import stat
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
from covalent_ext import covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit as gate  # noqa: E402

SPEC = importlib.util.spec_from_file_location("admit011_checker", REPO_ROOT / "scripts/check_covapie_bulk_download_admission_admit_011_formal_evaluator_interface_preconditions_audit_v1.py")
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)
OUTPUT_ROOT = REPO_ROOT / checker.EXPECTED_OUTPUT_ROOT


def _copied_outputs(tmp_path: Path) -> Path:
    root = tmp_path / "outputs"
    shutil.copytree(OUTPUT_ROOT, root)
    return root


def _rejects(root: Path) -> None:
    with pytest.raises(AssertionError):
        checker._validate_output_tree(root, enforce_frozen_hashes=False)


def test_canonical_identity_readiness_and_stop_boundary() -> None:
    state = gate.build_audit_state()
    assert state["contracts"]["rule"]["admission_rule_name"] == "raw_overwrite_forbidden"
    assert state["contracts"]["executable"]["candidate_field_dependencies"] == "raw_target_relative_path"
    assert state["readiness"]["ready_for_admit_011_raw_target_relative_path_contract_design"] is True
    assert state["readiness"]["ready_for_admit_011_standalone_evaluator_interface_implementation"] is False
    assert state["readiness"]["admit_011_rule_logic_implemented"] is False
    assert state["safety"]["raw_read"] is state["safety"]["filesystem_target_probe"] is False


def test_base_anchored_exact99_excludes_successor_stage_and_freezes_digests() -> None:
    paths = gate._base_source_paths()
    assert len(paths) == gate.EXPECTED_SOURCE_COUNT == 99
    assert all(gate.STAGE not in path.as_posix() for path in paths)
    assert hashlib.sha256(gate._canonical_json([path.as_posix() for path in paths])).hexdigest() == gate.EXPECTED_PATH_LIST_SHA256
    assert gate.RUNTIME_ISSUE_PATH in paths


def test_base_source_discovery_uses_base_not_worktree(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []
    original = gate._git

    def wrapped(args, repo_root, *, text=True):
        calls.append(args)
        return original(args, repo_root, text=text)

    monkeypatch.setattr(gate, "_git", wrapped)
    gate._base_source_paths()
    assert any(args[:5] == ["grep", "-l", "-I", "raw_target_relative_path", gate.EXPECTED_BASE_COMMIT] for args in calls)


def test_source_digest_drift_is_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate, "EXPECTED_PATH_LIST_SHA256", "0" * 64)
    with pytest.raises(ValueError, match="path-list digest"):
        gate._base_source_paths()


def test_path_sha_pair_digest_drift_is_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate, "EXPECTED_PATH_SHA256_PAIRS_SHA256", "0" * 64)
    with pytest.raises(ValueError, match="path/SHA"):
        gate.build_frozen_source_snapshot()


def test_all_structure_checks_finish_before_any_source_byte_read(monkeypatch: pytest.MonkeyPatch) -> None:
    reads = 0

    def no_read(self: Path) -> bytes:
        nonlocal reads
        reads += 1
        raise AssertionError("source bytes read before all structural checks")

    def fail_structure(*args, **kwargs):
        raise ValueError("synthetic structural failure")

    monkeypatch.setattr(Path, "read_bytes", no_read)
    monkeypatch.setattr(gate, "_source_structure", fail_structure)
    with pytest.raises(ValueError, match="synthetic"):
        gate.build_frozen_source_snapshot()
    assert reads == 0


def test_source_parent_symlink_escape_is_rejected_before_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, outside = tmp_path / "repo", tmp_path / "outside"
    repo.mkdir(); outside.mkdir()
    (outside / "leaf").write_text("x", encoding="utf-8")
    (repo / "parent").symlink_to(outside, target_is_directory=True)

    def fake_git(args, repo_root, *, text=True):
        if args[0] == "ls-tree":
            return SimpleNamespace(returncode=0, stdout="100644 blob deadbeef\tparent/leaf\n")
        return SimpleNamespace(returncode=0, stdout="")

    monkeypatch.setattr(gate, "_git", fake_git)
    with pytest.raises(ValueError, match="source parent"):
        gate._source_structure(Path("parent/leaf"), repo, repo.resolve())


@pytest.mark.parametrize("tree_stdout", ["120000 commit deadbeef\tparent/leaf\n", ""])
def test_base_blob_missing_or_nonregular_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tree_stdout: str) -> None:
    repo = tmp_path / "repo"; repo.mkdir()
    parent = repo / "parent"; parent.mkdir()
    (parent / "leaf").write_text("x", encoding="utf-8")

    def fake_git(args, repo_root, *, text=True):
        if args[0] == "ls-tree":
            return SimpleNamespace(returncode=0 if tree_stdout else 1, stdout=tree_stdout)
        return SimpleNamespace(returncode=0, stdout="")

    monkeypatch.setattr(gate, "_git", fake_git)
    with pytest.raises(ValueError, match="tree metadata"):
        gate._source_structure(Path("parent/leaf"), repo, repo.resolve())


def test_non_mutating_output_preflight_rejects_parent_symlink_and_repo_escape(tmp_path: Path) -> None:
    external = tmp_path / "external"; external.mkdir()
    link = tmp_path / "link"; link.symlink_to(external, target_is_directory=True)
    with pytest.raises(ValueError):
        gate._resolved_output_preflight(link / "out")
    with pytest.raises(ValueError):
        gate._resolved_output_preflight(Path("../admit011_escape"))


def test_unsafe_output_does_not_read_sources_or_mutate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    external = tmp_path / "external"; external.write_text("unchanged", encoding="utf-8")
    root = tmp_path / "out"; root.mkdir()
    (root / gate.PRECONDITION_FILENAME).symlink_to(external)
    called = False

    def source_called():
        nonlocal called
        called = True
        raise AssertionError("source snapshot must not be called")

    monkeypatch.setattr(gate, "build_frozen_source_snapshot", source_called)
    with pytest.raises(ValueError):
        gate.materialize_audit(root)
    assert not called and external.read_text(encoding="utf-8") == "unchanged"


def test_source_failure_has_no_missing_or_existing_output_side_effects(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    missing = tmp_path / "missing"
    existing = _copied_outputs(tmp_path)
    before = {item.name: (item.read_bytes(), item.stat().st_mtime_ns) for item in existing.iterdir()}
    monkeypatch.setattr(gate, "build_frozen_source_snapshot", lambda: (_ for _ in ()).throw(ValueError("source failure")))
    with pytest.raises(ValueError, match="source failure"):
        gate.materialize_audit(missing)
    with pytest.raises(ValueError, match="source failure"):
        gate.materialize_audit(existing)
    assert not missing.exists()
    assert before == {item.name: (item.read_bytes(), item.stat().st_mtime_ns) for item in existing.iterdir()}
    assert not list(tmp_path.glob("**/*.tmp")) and not list(tmp_path.glob("**/*.part"))


def test_newly_created_root_rejects_allowlisted_concurrent_occupant_before_first_write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "missing"
    marker = b"concurrent-allowlisted-occupant-must-remain-untouched"
    original = gate._validate_prewrite_output_root
    atomic_writes = 0

    def occupy_then_validate(candidate, repo_root, *, output_root_was_relative, newly_created):
        assert candidate == root and newly_created is True
        (candidate / gate.PRECONDITION_FILENAME).write_bytes(marker)
        original(candidate, repo_root, output_root_was_relative=output_root_was_relative, newly_created=newly_created)

    def counted_atomic_write(path, data):
        nonlocal atomic_writes
        atomic_writes += 1
        raise AssertionError("atomic write must not occur after concurrent occupation")

    monkeypatch.setattr(gate, "_validate_prewrite_output_root", occupy_then_validate)
    monkeypatch.setattr(gate, "_atomic_write", counted_atomic_write)
    with pytest.raises(ValueError, match="remain empty"):
        gate.materialize_audit(root)
    assert atomic_writes == 0
    assert (root / gate.PRECONDITION_FILENAME).read_bytes() == marker
    assert {entry.name for entry in root.iterdir()} == {gate.PRECONDITION_FILENAME}
    assert not list(root.glob("*.tmp")) and not list(root.glob("*.part"))


def test_normal_missing_and_existing_output_roots_materialize_successfully(tmp_path: Path) -> None:
    root = tmp_path / "normal"
    first = gate.materialize_audit(root)
    assert {entry.name for entry in root.iterdir()} == set(gate.OUTPUT_FILES)
    second = gate.materialize_audit(root)
    assert first["output_sha256"] == second["output_sha256"]


def test_deterministic_materialization_checker_and_exact_csv_hashes() -> None:
    first, second = gate.materialize_audit(), gate.materialize_audit()
    assert first["output_sha256"] == second["output_sha256"] == checker.EXPECTED_OUTPUT_SHA256
    checker._validate_output_tree(OUTPUT_ROOT)


@pytest.mark.parametrize("filename,old,new", [
    (gate.PRECONDITION_FILENAME, "registry fixes ADMIT_011/raw_overwrite_forbidden/pre_download", "tampered"),
    (gate.OCCURRENCE_FILENAME, "raw_target_relative_path", "raw_target_relative_PATH"),
    (gate.OBSERVED_FILENAME, "present_historical_or_fixture_value", "tampered"),
    (gate.SOURCE_BOUNDARY_FILENAME, "source_boundary_passed", "source_boundary_FAILED"),
])
def test_checker_rejects_semantic_csv_tamper(tmp_path: Path, filename: str, old: str, new: str) -> None:
    root = _copied_outputs(tmp_path)
    path = root / filename
    path.write_text(path.read_text(encoding="utf-8").replace(old, new, 1), encoding="utf-8")
    _rejects(root)


@pytest.mark.parametrize("mutate", [
    lambda value: value.__setitem__("recommended_next_step", "tampered"),
    lambda value: value["readiness"].__setitem__("ready_for_admit_011_standalone_evaluator_interface_implementation", True),
    lambda value: value.__setitem__("unknown_key", True),
])
def test_checker_rejects_manifest_semantic_tamper(tmp_path: Path, mutate) -> None:
    root = _copied_outputs(tmp_path)
    path = root / gate.MANIFEST_FILENAME
    value = json.loads(path.read_text(encoding="utf-8")); mutate(value)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _rejects(root)


def test_checker_rejects_issue_byte_tamper_and_production_constant_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _copied_outputs(tmp_path)
    issue = root / gate.ISSUE_FILENAME
    issue.write_bytes(issue.read_bytes().replace(b"RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED", b"RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED_X", 1))
    _rejects(root)
    monkeypatch.setattr(gate, "STAGE", "production_drift")
    checker._validate_output_tree(OUTPUT_ROOT)


def test_silent_import_and_exact_regular_outputs() -> None:
    assert {path.name for path in OUTPUT_ROOT.iterdir()} == set(gate.OUTPUT_FILES)
    assert all(stat.S_ISREG(os.lstat(path).st_mode) and not path.is_symlink() for path in OUTPUT_ROOT.iterdir())
