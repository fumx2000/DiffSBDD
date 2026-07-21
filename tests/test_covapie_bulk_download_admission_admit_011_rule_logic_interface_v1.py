from __future__ import annotations

import ast
import csv
import hashlib
import io
import importlib
import inspect
import json
import os
import shutil
import subprocess
import sys
from dataclasses import fields
from pathlib import Path

import pytest

from covalent_ext import covapie_bulk_download_admission_admit_011_rule_logic_interface as formal
from covalent_ext.covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate import (
    CONTRACT_FIELDS, CONTRACT_REASONS, DEFAULT_CONTRACT, ExistingRawTargetRelativePathsSnapshot,
    RawTargetRelativePathContract, SCALAR_REASONS, SNAPSHOT_FIELDS, SNAPSHOT_REASONS,
    STANDALONE_CONTEXT_VALIDATION_ORDER,
)
from scripts import check_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1 as checker


def _empty() -> ExistingRawTargetRelativePathsSnapshot:
    return ExistingRawTargetRelativePathsSnapshot(
        "covapie_existing_raw_target_relative_paths_snapshot_v1", DEFAULT_CONTRACT.canonical_raw_root_identity,
        DEFAULT_CONTRACT.candidate_coordinate_system, DEFAULT_CONTRACT.path_grammar_version,
        DEFAULT_CONTRACT.equality_policy, DEFAULT_CONTRACT.snapshot_phase, True, (),
    )


def _unsafe_contract() -> RawTargetRelativePathContract:
    value = object.__new__(RawTargetRelativePathContract)
    for name in CONTRACT_FIELDS:
        object.__setattr__(value, name, getattr(DEFAULT_CONTRACT, name))
    object.__setattr__(value, "contract_id", "wrong")
    return value


def _unsafe_snapshot(**changes: object) -> ExistingRawTargetRelativePathsSnapshot:
    value = object.__new__(ExistingRawTargetRelativePathsSnapshot)
    base = _empty()
    for name in SNAPSHOT_FIELDS:
        object.__setattr__(value, name, getattr(base, name))
    for name, item in changes.items():
        object.__setattr__(value, name, item)
    return value


def _result_values(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "admission_rule_id": "ADMIT_011", "outcome": "passed", "passed": True,
        "blocks_candidate": False, "reason": "", "canonical_raw_target_relative_path": "data/raw/a.cif",
        "validated_candidate_fields": (("raw_target_relative_path", "data/raw/a.cif"),),
        "consumed_candidate_fields": ("raw_target_relative_path",),
        "consumed_context_items": STANDALONE_CONTEXT_VALIDATION_ORDER, "evaluator_io_used": False,
    }
    values.update(overrides)
    return values


def test_public_signature_and_exact10_result_contract() -> None:
    assert tuple(inspect.signature(formal.evaluate_admit_011).parameters) == (
        "raw_target_relative_path", "existing_raw_target_relative_paths", "raw_target_relative_path_contract",
    )
    assert tuple(field.name for field in fields(formal.Admit011EvaluationResult)) == formal.RESULT_FIELDS
    value = formal.evaluate_admit_011("data/raw/a.cif", _empty(), DEFAULT_CONTRACT)
    assert type(value) is formal.Admit011EvaluationResult and value.passed is True


def test_result_subclass_and_illegal_direct_construction_fail_closed() -> None:
    class Child(formal.Admit011EvaluationResult):
        pass
    with pytest.raises(TypeError):
        Child(**_result_values())
    for update in (
        {"evaluator_io_used": True}, {"passed": False}, {"reason": "bad"},
        {"validated_candidate_fields": ()}, {"consumed_context_items": ()},
        {"canonical_raw_target_relative_path": "docs/a"}, {"passed": 1},
    ):
        with pytest.raises((TypeError, ValueError)):
            formal.Admit011EvaluationResult(**_result_values(**update))


@pytest.mark.parametrize("candidate,reason", [
    (None, SCALAR_REASONS[0]), ("", SCALAR_REASONS[1]), ("data/raw/café", SCALAR_REASONS[2]),
    ("data/raw/a\0", SCALAR_REASONS[3]), ("data/raw/a\x01", SCALAR_REASONS[4]),
    ("data/raw/a b", SCALAR_REASONS[5]), ("/data/raw/a", SCALAR_REASONS[6]),
    ("C:\\data/raw/a", SCALAR_REASONS[7]), ("\\\\server\\a", SCALAR_REASONS[8]),
    ("https://x//y", SCALAR_REASONS[9]), ("data/raw/%2e", SCALAR_REASONS[10]),
    ("~/data/raw/a", SCALAR_REASONS[11]), ("$RAW/a", SCALAR_REASONS[12]),
    ("data/raw\\a", SCALAR_REASONS[13]), ("data/raw/a/", SCALAR_REASONS[14]),
    ("data/raw//a", SCALAR_REASONS[15]), ("data/raw/./a", SCALAR_REASONS[16]),
    ("data/raw/../a", SCALAR_REASONS[17]), ("docs/a", SCALAR_REASONS[18]),
])
def test_all_scalar_reasons_and_precedence(candidate: object, reason: str) -> None:
    result = formal.evaluate_admit_011(candidate, object(), object())
    assert result.reason == reason and result.outcome == "invalid"
    assert result.canonical_raw_target_relative_path == "" and result.consumed_context_items == ()


@pytest.mark.parametrize("candidate,reason", [
    ("data/raw/café x", SCALAR_REASONS[2]), ("/data/raw/../a", SCALAR_REASONS[6]),
    ("C:\\data/raw\\a", SCALAR_REASONS[7]), ("https://x//y", SCALAR_REASONS[9]),
    ("data/raw/%2e%2e/a", SCALAR_REASONS[10]), ("docs/a", SCALAR_REASONS[18]),
])
def test_scalar_multi_invalid_precedence(candidate: str, reason: str) -> None:
    assert formal.evaluate_admit_011(candidate, object(), object()).reason == reason


def test_contract_type_value_and_context_order() -> None:
    type_invalid = formal.evaluate_admit_011("data/raw/a.cif", _empty(), object())
    value_invalid = formal.evaluate_admit_011("data/raw/a.cif", _empty(), _unsafe_contract())
    assert type_invalid.reason == CONTRACT_REASONS[0] and value_invalid.reason == CONTRACT_REASONS[1]
    assert type_invalid.consumed_context_items == value_invalid.consumed_context_items == ("raw_target_relative_path_contract",)


def test_snapshot_type_value_duplicate_and_noncanonical_rejected() -> None:
    cases = (object(), _unsafe_snapshot(schema_version="wrong"), _unsafe_snapshot(snapshot_complete=False), _unsafe_snapshot(occupied_relative_paths=("data/raw/a", "data/raw/a")), _unsafe_snapshot(occupied_relative_paths=("docs/a",)))
    for value in cases:
        result = formal.evaluate_admit_011("data/raw/a.cif", value, DEFAULT_CONTRACT)
        assert result.reason in SNAPSHOT_REASONS[:2]
        assert result.consumed_context_items == STANDALONE_CONTEXT_VALIDATION_ORDER


@pytest.mark.parametrize("field,reason", [
    ("canonical_raw_root_identity", SNAPSHOT_REASONS[2]), ("candidate_coordinate_system", SNAPSHOT_REASONS[3]),
    ("path_grammar_version", SNAPSHOT_REASONS[4]), ("equality_policy", SNAPSHOT_REASONS[5]),
    ("snapshot_phase", SNAPSHOT_REASONS[6]),
])
def test_all_cross_context_mismatches(field: str, reason: str) -> None:
    result = formal.evaluate_admit_011("data/raw/a.cif", _unsafe_snapshot(**{field: "wrong"}), DEFAULT_CONTRACT)
    assert result.reason == reason and result.consumed_context_items == STANDALONE_CONTEXT_VALIDATION_ORDER


def test_collision_and_case_sensitive_membership_and_passed() -> None:
    occupied = ExistingRawTargetRelativePathsSnapshot(
        "covapie_existing_raw_target_relative_paths_snapshot_v1", DEFAULT_CONTRACT.canonical_raw_root_identity,
        DEFAULT_CONTRACT.candidate_coordinate_system, DEFAULT_CONTRACT.path_grammar_version,
        DEFAULT_CONTRACT.equality_policy, DEFAULT_CONTRACT.snapshot_phase, True, ("data/raw/A.cif",),
    )
    assert formal.evaluate_admit_011("data/raw/A.cif", occupied, DEFAULT_CONTRACT).outcome == "blocked"
    assert formal.evaluate_admit_011("data/raw/a.cif", occupied, DEFAULT_CONTRACT).outcome == "passed"


def test_exact47_historical_and_exact84_full_truth_parity() -> None:
    rows = list(csv.DictReader(checker.DESIGN_TRUTH.read_text(encoding="utf-8").splitlines()))
    assert len(rows) == 84 and sum(row["matrix_group"] == "historical_observed" for row in rows) == 47
    checker.validate_output_tree()


def test_evaluator_ast_closure_excludes_design_oracle_and_io() -> None:
    checker._check_ast_closure()
    source = Path(formal.__file__).read_text(encoding="utf-8")
    closure = source[source.index("def evaluate_admit_011"):source.index("# Everything below")]
    assert "classify_admit_011_raw_target_relative_path_design" not in closure


def test_double_materialization_is_deterministic(tmp_path: Path) -> None:
    root = tmp_path / "stage"
    first = formal.run_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1(root)
    before = {path.name: path.read_bytes() for path in root.iterdir()}
    second = formal.run_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1(root)
    assert first == second and before == {path.name: path.read_bytes() for path in root.iterdir()}
    checker.validate_output_tree(root)


@pytest.mark.parametrize("name,needle,replacement", [
    (formal.TRUTH_FILENAME, "RAW_TARGET_RELATIVE_PATH_ALREADY_OCCUPIED", ""),
    (formal.TRUTH_FILENAME, '[""raw_target_relative_path_contract""]', '[""raw_target_relative_path_contract"",""existing_raw_target_relative_paths""]'),
    (formal.TRUTH_FILENAME, '[[""raw_target_relative_path"",""data/raw/a.cif""]]', '[]'),
    (formal.PURITY_FILENAME, "false", "true"),
])
def test_checker_rejects_synchronized_semantic_tamper(tmp_path: Path, name: str, needle: str, replacement: str) -> None:
    copied = tmp_path / "copied"; shutil.copytree(checker.STAGE, copied)
    target = copied / name
    content = target.read_text(encoding="utf-8")
    assert needle in content
    target.write_text(content.replace(needle, replacement, 1), encoding="utf-8")
    manifest_path = copied / formal.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["output_sha256"] = {entry: hashlib.sha256((copied / entry).read_bytes()).hexdigest() for entry in formal.OUTPUT_FILES[:-1]}
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        checker.validate_output_tree(copied, enforce_frozen_hashes=False)


def test_checker_rejects_manifest_key_readiness_and_next_step_tamper(tmp_path: Path) -> None:
    copied = tmp_path / "copied"; shutil.copytree(checker.STAGE, copied)
    manifest_path = copied / formal.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["readiness"]["ready_for_training"] = True
    manifest["recommended_next_step"] = "tampered"
    manifest["extra"] = False
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        checker.validate_output_tree(copied, enforce_frozen_hashes=False)


def test_silent_import_has_no_output_or_file_side_effect(tmp_path: Path) -> None:
    command = [sys.executable, "-B", "-c", "import covalent_ext.covapie_bulk_download_admission_admit_011_rule_logic_interface"]
    result = subprocess.run(command, cwd=tmp_path, env={**__import__("os").environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")}, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    assert result.stdout == result.stderr == "" and list(tmp_path.iterdir()) == []


def _materializer_snapshot(root: Path) -> tuple[tuple[int, int, int], dict[str, tuple[tuple[int, int, int], bytes]]]:
    return (
        (root.stat().st_dev, root.stat().st_ino, root.stat().st_mode),
        {name: ((item.stat().st_dev, item.stat().st_ino, item.stat().st_mode), item.read_bytes()) for name in formal.OUTPUT_FILES for item in (root / name,)},
    )


def _assert_no_owned_staging(parent: Path, root: Path) -> None:
    assert not root.exists()
    assert not list(parent.glob(".admit011-stage-*"))
    assert not list(parent.glob("*.tmp"))
    assert not list(parent.glob("*.part"))


def test_materializer_preserves_frozen_prefix_and_six_formal_outputs() -> None:
    source = Path(formal.__file__).read_text(encoding="utf-8")
    prefix = source[:source.index("# Everything below this line is deliberately outside the evaluator closure.")]
    assert hashlib.sha256(prefix.encode("utf-8")).hexdigest() == "dd5ea58fa4d1fa229a596723ae2c1abefe9fa092246097da43f6d012cdc2e251"
    assert {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in checker.STAGE.iterdir()} == checker.FROZEN_OUTPUT_SHA256


@pytest.mark.parametrize("kind", ("missing_parent", "parent_symlink", "root_symlink", "broken_root_symlink", "root_file", "root_fifo", "unexpected_inventory"))
def test_materializer_read_only_preflight_rejects_unsafe_targets_before_build(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str) -> None:
    parent = tmp_path / "parent"; parent.mkdir()
    root = parent / "stage"
    if kind == "missing_parent":
        root = tmp_path / "missing" / "stage"
    elif kind == "parent_symlink":
        target = tmp_path / "real-parent"; target.mkdir(); parent.rmdir(); parent.symlink_to(target, target_is_directory=True)
    elif kind == "root_symlink":
        target = tmp_path / "real-root"; target.mkdir(); root.symlink_to(target, target_is_directory=True)
    elif kind == "broken_root_symlink":
        root.symlink_to(tmp_path / "does-not-exist", target_is_directory=True)
    elif kind == "root_file":
        root.write_bytes(b"not a directory")
    elif kind == "root_fifo":
        os.mkfifo(root)
    else:
        root.mkdir(); (root / "unexpected").write_bytes(b"x")
    called = False
    def fail_build(_: Path) -> dict[str, bytes]:
        nonlocal called
        called = True
        raise AssertionError("artifact build must not run after unsafe preflight")
    monkeypatch.setattr(formal, "build_interface_artifacts", fail_build)
    with pytest.raises(ValueError):
        formal.run_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1(root)
    assert called is False


@pytest.mark.parametrize("kind", ("leaf_symlink", "leaf_directory", "leaf_fifo"))
def test_materializer_rejects_unsafe_leaf_inventory(tmp_path: Path, kind: str) -> None:
    root = tmp_path / "stage"
    formal.run_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1(root)
    leaf = root / formal.OUTPUT_FILES[0]
    leaf.unlink()
    if kind == "leaf_symlink":
        leaf.symlink_to(root / formal.OUTPUT_FILES[1])
    elif kind == "leaf_directory":
        leaf.mkdir()
    else:
        os.mkfifo(leaf)
    with pytest.raises(ValueError):
        formal.run_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1(root)


def test_materializer_build_failure_has_no_output_mutation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "stage"
    def fail_build(_: Path) -> dict[str, bytes]:
        raise RuntimeError("synthetic build failure")
    monkeypatch.setattr(formal, "build_interface_artifacts", fail_build)
    with pytest.raises(RuntimeError, match="synthetic"):
        formal.run_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1(root)
    _assert_no_owned_staging(tmp_path, root)


def test_materializer_existing_exact_root_is_inode_preserving_noop_and_mismatch_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "stage"
    first = formal.run_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1(root)
    before = _materializer_snapshot(root)
    second = formal.run_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1(root)
    assert first == second and _materializer_snapshot(root) == before
    changed = root / formal.OUTPUT_FILES[0]
    changed.write_bytes(b"mismatch")
    mismatch_before = _materializer_snapshot(root)
    with pytest.raises(ValueError, match="differs"):
        formal.run_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1(root)
    assert _materializer_snapshot(root) == mismatch_before


def test_materializer_ordinary_rename_and_replace_are_unreachable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = inspect.getsource(formal.run_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1)
    assert "os.rename" not in source and "os.replace" not in source
    monkeypatch.setattr(formal.os, "rename", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("ordinary rename called")))
    monkeypatch.setattr(formal.os, "replace", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("replace called")))
    formal.run_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1(tmp_path / "stage")


@pytest.mark.parametrize("failure", tuple(range(1, 7)))
def test_materializer_staging_write_failures_clean_only_owned_set(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: int) -> None:
    root = tmp_path / "stage"
    original = formal._write_all
    calls = 0
    def fail_nth(fd: int, data: bytes) -> None:
        nonlocal calls
        calls += 1
        if calls == failure:
            raise OSError("synthetic write failure")
        original(fd, data)
    monkeypatch.setattr(formal, "_write_all", fail_nth)
    with pytest.raises(OSError, match="synthetic"):
        formal.run_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1(root)
    _assert_no_owned_staging(tmp_path, root)


@pytest.mark.parametrize("mode", ("file_fsync", "staging_verify", "staging_fsync", "rename_failure"))
def test_materializer_prepublication_failures_leave_no_final_or_owned_staging(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str) -> None:
    root = tmp_path / "stage"
    if mode == "file_fsync":
        monkeypatch.setattr(formal.os, "fsync", lambda _fd: (_ for _ in ()).throw(OSError("synthetic file fsync")))
    elif mode == "staging_verify":
        original = formal._read_at
        calls = 0
        def fail_read(*args: object) -> bytes:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise ValueError("synthetic staging verification")
            return original(*args)
        monkeypatch.setattr(formal, "_read_at", fail_read)
    elif mode == "staging_fsync":
        original = formal.os.fsync
        calls = 0
        def fail_seventh(fd: int) -> None:
            nonlocal calls
            calls += 1
            if calls == 7:
                raise OSError("synthetic staging fsync")
            original(fd)
        monkeypatch.setattr(formal.os, "fsync", fail_seventh)
    else:
        monkeypatch.setattr(formal, "_rename_noreplace_at", lambda *_args: (_ for _ in ()).throw(OSError("synthetic rename")))
    with pytest.raises((OSError, ValueError), match="synthetic"):
        formal.run_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1(root)
    _assert_no_owned_staging(tmp_path, root)


def test_materializer_precheck_race_and_renameat2_noreplace_race_reject_without_overwrite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "stage"
    original_stage = formal._stage_payloads
    def stage_then_race(fd: int, files: dict[str, bytes], staged: dict[str, tuple[int, int, int]]) -> None:
        original_stage(fd, files, staged)
        root.mkdir()
    monkeypatch.setattr(formal, "_stage_payloads", stage_then_race)
    with pytest.raises(ValueError, match="race"):
        formal.run_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1(root)
    assert root.is_dir() and list(root.iterdir()) == [] and not list(tmp_path.glob(".admit011-stage-*"))

    root.rmdir()
    monkeypatch.setattr(formal, "_stage_payloads", original_stage)
    original_rename = formal._rename_noreplace_at
    def race_in_rename(parent_fd: int, source: str, target: str) -> None:
        os.mkdir(target, dir_fd=parent_fd)
        original_rename(parent_fd, source, target)
    monkeypatch.setattr(formal, "_rename_noreplace_at", race_in_rename)
    with pytest.raises(OSError):
        formal.run_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1(root)
    assert root.is_dir() and list(root.iterdir()) == [] and not list(tmp_path.glob(".admit011-stage-*"))


def test_materializer_parent_fsync_failure_leaves_only_complete_published_set(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "stage"
    original = formal.os.fsync
    calls = 0
    def fail_parent_fsync(fd: int) -> None:
        nonlocal calls
        calls += 1
        if calls == 8:
            raise OSError("synthetic parent fsync")
        original(fd)
    monkeypatch.setattr(formal.os, "fsync", fail_parent_fsync)
    with pytest.raises(OSError, match="parent"):
        formal.run_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1(root)
    assert root.is_dir() and {path.name for path in root.iterdir()} == set(formal.OUTPUT_FILES)
    assert not list(tmp_path.glob(".admit011-stage-*"))


def test_materializer_unknown_staging_entry_is_not_deleted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "stage"
    original = formal._stage_payloads
    def stage_unknown(fd: int, files: dict[str, bytes], staged: dict[str, tuple[int, int, int]]) -> None:
        original(fd, files, staged)
        unknown_fd = os.open("unknown", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=fd)
        os.close(unknown_fd)
    monkeypatch.setattr(formal, "_stage_payloads", stage_unknown)
    with pytest.raises(ValueError, match="inventory"):
        formal.run_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1(root)
    stages = list(tmp_path.glob(".admit011-stage-*"))
    assert not root.exists() and len(stages) == 1 and (stages[0] / "unknown").is_file()


def test_materializer_success_publishes_exact_complete_set_without_residue(tmp_path: Path) -> None:
    root = tmp_path / "stage"
    formal.run_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1(root)
    assert {path.name for path in root.iterdir()} == set(formal.OUTPUT_FILES)
    assert not list(tmp_path.glob(".admit011-stage-*"))
    assert not list(tmp_path.glob("*.tmp")) and not list(tmp_path.glob("*.part"))


def _copied_output_tree(tmp_path: Path) -> Path:
    copied = tmp_path / "copied"
    shutil.copytree(checker.STAGE, copied)
    return copied


def _refresh_output_hashes(root: Path) -> None:
    manifest_path = root / checker.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["output_sha256"] = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in checker.OUTPUT_FILES[:-1]
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _rewrite_csv(root: Path, filename: str, columns: tuple[str, ...], mutate: object) -> None:
    path = root / filename
    rows = list(csv.DictReader(path.read_text(encoding="utf-8").splitlines()))
    assert tuple(rows[0]) == columns
    mutate(rows)
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=columns, lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
    path.write_text(output.getvalue(), encoding="utf-8")


def test_transitive_ast_closure_is_exact_for_real_source() -> None:
    source = Path(formal.__file__).read_text(encoding="utf-8")
    result = checker._check_ast_closure(source)
    assert result.reachable_definitions == checker.EXPECTED_CLOSURE
    assert checker._computed_reachable_helpers(result) == checker.EXPECTED_REACHABLE_HELPERS


@pytest.mark.parametrize("source", [
    "from pathlib import Path\ndef evaluate_admit_011():\n return Path('x').read_text()\n",
    "from pathlib import Path\ndef evaluate_admit_011():\n return _evil_helper()\ndef _evil_helper():\n return Path('x').read_text()\n",
    "import os\ndef evaluate_admit_011():\n return _one()\ndef _one():\n return _two()\ndef _two():\n return os.stat('x')\n",
    "import subprocess\ndef evaluate_admit_011():\n return _evil_helper()\ndef _evil_helper():\n return subprocess.run(['x'])\n",
    "def evaluate_admit_011():\n return _evil_helper()\ndef _evil_helper():\n return open('x')\n",
    "def evaluate_admit_011():\n return _evil_helper()\ndef _evil_helper():\n return __import__('pathlib')\n",
    "def evaluate_admit_011():\n return _evil_helper()\ndef _evil_helper():\n return eval('1')\n",
    "def evaluate_admit_011():\n return _evil_helper()\ndef _evil_helper():\n exec('x=1')\n return compile('1','x','eval')\n",
    "from pathlib import Path\nP=Path\ndef evaluate_admit_011():\n return _evil_helper()\ndef _evil_helper():\n return P('x').read_text()\n",
    "import os\nO=os\ndef evaluate_admit_011():\n return _evil_helper()\ndef _evil_helper():\n return O.stat('x')\n",
    "def evaluate_admit_011():\n return _pure_helper()\ndef _pure_helper():\n return 1\n",
    "def evaluate_admit_011():\n return _contract_valid()\ndef _contract_valid():\n return getattr(value, field, 'fallback')\n",
    "from frozen import classify_admit_011_raw_target_relative_path_design\ndef evaluate_admit_011():\n return _evil_helper()\ndef _evil_helper():\n return classify_admit_011_raw_target_relative_path_design()\n",
    "def evaluate_admit_011():\n return _evil_helper()\ndef _evil_helper():\n return build_interface_artifacts()\ndef build_interface_artifacts():\n return 1\n",
])
def test_transitive_ast_rejects_direct_indirect_alias_and_closure_drift(source: str) -> None:
    with pytest.raises(AssertionError):
        checker._check_ast_closure(source)


@pytest.mark.parametrize("mode", ("reorder", "field", "contract", "passed", "extra_column", "missing_column", "extra_row", "missing_row"))
def test_checker_rejects_synchronized_contract_exact10_tamper(tmp_path: Path, mode: str) -> None:
    copied = _copied_output_tree(tmp_path)
    path = copied / checker.CONTRACT_FILENAME
    rows = list(csv.DictReader(path.read_text(encoding="utf-8").splitlines()))
    if mode == "reorder":
        rows[0], rows[1] = rows[1], rows[0]
    elif mode == "field":
        rows[0]["field"] = "renamed"
    elif mode == "contract":
        rows[0]["contract"] = "tampered"
    elif mode == "passed":
        rows[0]["passed"] = "false"
    elif mode == "extra_row":
        rows.append(dict(rows[-1]))
    elif mode == "missing_row":
        rows.pop()
    if mode in {"extra_column", "missing_column"}:
        columns = checker.CONTRACT_COLUMNS + ("extra",) if mode == "extra_column" else checker.CONTRACT_COLUMNS[:-1]
    else:
        columns = checker.CONTRACT_COLUMNS
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
    path.write_text(output.getvalue(), encoding="utf-8")
    _refresh_output_hashes(copied)
    with pytest.raises(AssertionError):
        checker.validate_output_tree(copied, enforce_frozen_hashes=False)


@pytest.mark.parametrize("field,value", [
    ("matrix_group", "tampered_group"), ("candidate_representation", "'data/raw/tampered.cif'"),
    ("contract_state", "tampered_contract"), ("snapshot_state", "tampered_snapshot"),
    ("admission_rule_id", "ADMIT_BAD"), ("outcome", "blocked"), ("passed", "false"),
    ("blocks_candidate", "true"), ("reason", "TAMPERED_REASON"),
    ("canonical_raw_target_relative_path", "data/raw/tampered.cif"), ("validated_candidate_fields", "[]"),
    ("consumed_candidate_fields", "[]"), ("consumed_context_items", "[]"), ("evaluator_io_used", "true"),
    ("expected_precedence", "tampered_precedence"), ("truth_passed", "false"),
    ("case_order", "999"), ("case_id", "TAMPERED_CASE"),
])
def test_checker_rejects_synchronized_exact84_all_field_class_tamper(tmp_path: Path, field: str, value: str) -> None:
    copied = _copied_output_tree(tmp_path)
    def mutate(rows: list[dict[str, str]]) -> None:
        rows[0][field] = value
    _rewrite_csv(copied, checker.TRUTH_FILENAME, checker.TRUTH_COLUMNS, mutate)
    _refresh_output_hashes(copied)
    with pytest.raises(AssertionError):
        checker.validate_output_tree(copied, enforce_frozen_hashes=False)


def test_checker_rejects_malicious_candidate_representation_without_execution(tmp_path: Path) -> None:
    copied = _copied_output_tree(tmp_path)
    marker = tmp_path / "malicious-marker"
    expression = f'__import__("pathlib").Path({str(marker)!r}).write_text("owned")'
    def mutate(rows: list[dict[str, str]]) -> None:
        rows[0]["candidate_representation"] = expression
    _rewrite_csv(copied, checker.TRUTH_FILENAME, checker.TRUTH_COLUMNS, mutate)
    _refresh_output_hashes(copied)
    with pytest.raises(AssertionError, match="literal"):
        checker.validate_output_tree(copied, enforce_frozen_hashes=False)
    assert not marker.exists()


@pytest.mark.parametrize("field,value", [
    ("status", "closed"), ("affected_rules", "ADMIT_011"), ("integration_transition", "tampered_transition"),
])
def test_checker_rejects_synchronized_exact11_issue_field_tamper(tmp_path: Path, field: str, value: str) -> None:
    copied = _copied_output_tree(tmp_path)
    def mutate(rows: list[dict[str, str]]) -> None:
        rows[0][field] = value
    _rewrite_csv(copied, checker.ISSUE_FILENAME, checker.ISSUE_COLUMNS, mutate)
    _refresh_output_hashes(copied)
    with pytest.raises(AssertionError):
        checker.validate_output_tree(copied, enforce_frozen_hashes=False)


def test_checker_rejects_synchronized_exact11_issue_reorder(tmp_path: Path) -> None:
    copied = _copied_output_tree(tmp_path)
    def mutate(rows: list[dict[str, str]]) -> None:
        rows[0], rows[1] = rows[1], rows[0]
    _rewrite_csv(copied, checker.ISSUE_FILENAME, checker.ISSUE_COLUMNS, mutate)
    _refresh_output_hashes(copied)
    with pytest.raises(AssertionError):
        checker.validate_output_tree(copied, enforce_frozen_hashes=False)


@pytest.mark.parametrize("row_index,value", [(1, "tampered_helper"), (2, "tampered forbidden row"), (3, "true")])
def test_checker_rejects_synchronized_purity_csv_tamper(tmp_path: Path, row_index: int, value: str) -> None:
    copied = _copied_output_tree(tmp_path)
    def mutate(rows: list[dict[str, str]]) -> None:
        rows[row_index]["observed"] = value
    _rewrite_csv(copied, checker.PURITY_FILENAME, checker.PURITY_COLUMNS, mutate)
    _refresh_output_hashes(copied)
    with pytest.raises(AssertionError):
        checker.validate_output_tree(copied, enforce_frozen_hashes=False)


def _production_source_text() -> str:
    return Path(formal.__file__).read_text(encoding="utf-8")


def _with_module_prefix(source: str, prefix: str) -> str:
    anchor = "from __future__ import annotations\n"
    assert anchor in source
    return source.replace(anchor, anchor + prefix, 1)


def _with_function_statement(source: str, function_name: str, statement: str) -> str:
    anchor = f"def {function_name}"
    offset = source.index(anchor)
    newline = source.index("\n", offset) + 1
    return source[:newline] + statement + source[newline:]


def _with_class_body_statement(source: str, statement: str) -> str:
    anchor = "    def __post_init__(self) -> None:\n"
    assert anchor in source
    return source.replace(anchor, statement + anchor, 1)


def _with_class_extra_method(source: str) -> str:
    anchor = "\n\ndef _result(outcome: str, reason: str, canonical: str)"
    assert anchor in source
    extra = "\n    def evil_method(self) -> object:\n        return 1\n"
    return source.replace(anchor, extra + anchor, 1)


def _closed_world_case(kind: str) -> str:
    source = _production_source_text()
    if kind == "module_socket":
        return _with_function_statement(_with_module_prefix(source, "import socket\n"), "_scalar_reason", "    socket.socket()\n")
    if kind == "local_socket":
        return _with_function_statement(source, "_scalar_reason", "    import socket\n    socket.socket()\n")
    if kind == "indirect_socket":
        return _with_function_statement(_with_module_prefix(source, "import socket\n"), "_canonical_path", "    socket.create_connection(('127.0.0.1', 1))\n")
    if kind == "requests":
        return _with_function_statement(_with_module_prefix(source, "import requests\n"), "_scalar_reason", "    requests.get('https://example.invalid')\n")
    if kind == "urllib":
        return _with_function_statement(_with_module_prefix(source, "import urllib.request\n"), "_scalar_reason", "    urllib.request.urlopen('https://example.invalid')\n")
    if kind == "importlib":
        return _with_function_statement(_with_module_prefix(source, "import importlib\n"), "_scalar_reason", "    importlib.import_module('os')\n")
    if kind == "builtins_subscript":
        return _with_function_statement(_with_module_prefix(source, "import builtins\n"), "_scalar_reason", "    builtins.__dict__['open']('x')\n")
    if kind == "lambda":
        return _with_function_statement(source, "_scalar_reason", "    (lambda: 1)()\n")
    if kind == "subclasses":
        return _with_function_statement(source, "_scalar_reason", "    object.__subclasses__()\n")
    if kind == "getattribute":
        return _with_function_statement(source, "_scalar_reason", "    object.__getattribute__(value, '__class__')\n")
    if kind == "ctypes":
        return _with_function_statement(_with_module_prefix(source, "import ctypes\n"), "_scalar_reason", "    ctypes.CDLL(None)\n")
    if kind == "global":
        return _with_function_statement(source, "_scalar_reason", "    global evil_global\n")
    if kind == "nonlocal":
        return _with_function_statement(source, "_scalar_reason", "    nonlocal evil_nonlocal\n")
    if kind == "with":
        return _with_function_statement(source, "_scalar_reason", "    with value:\n        pass\n")
    if kind == "module_alias":
        return _with_function_statement(_with_module_prefix(source, "import socket\nSOCKET = socket\n"), "_scalar_reason", "    SOCKET.socket()\n")
    if kind == "evil_decorator":
        decorated = _with_module_prefix(source, "import socket\ndef evil_decorator(cls):\n    socket.socket()\n    return cls\n")
        return decorated.replace("@dataclass(frozen=True)\nclass Admit011EvaluationResult:", "@evil_decorator\n@dataclass(frozen=True)\nclass Admit011EvaluationResult:", 1)
    if kind == "second_decorator":
        decorated = _with_module_prefix(source, "def extra_decorator(cls):\n    return cls\n")
        return decorated.replace("@dataclass(frozen=True)\nclass Admit011EvaluationResult:", "@extra_decorator\n@dataclass(frozen=True)\nclass Admit011EvaluationResult:", 1)
    if kind == "base_class":
        return source.replace("class Admit011EvaluationResult:", "class Admit011EvaluationResult(object):", 1)
    if kind == "extra_method":
        return _with_class_extra_method(source)
    if kind == "class_statement":
        return _with_class_body_statement(source, "    evil = 1\n\n")
    raise AssertionError(f"unknown closed-world case: {kind}")


@pytest.mark.parametrize("kind", (
    "module_socket", "local_socket", "indirect_socket", "requests", "urllib", "importlib", "builtins_subscript",
    "lambda", "subclasses", "getattribute", "ctypes", "global", "nonlocal", "with", "module_alias",
    "evil_decorator", "second_decorator", "base_class", "extra_method", "class_statement",
))
def test_closed_world_analyzer_rejects_real_source_network_dynamic_and_class_envelope_bypasses(kind: str) -> None:
    with pytest.raises(AssertionError):
        checker._check_ast_closure(_closed_world_case(kind))


def test_closed_world_allowlists_and_real_class_envelope_are_exact() -> None:
    assert checker.APPROVED_GLOBAL_SYMBOLS == {
        "CANDIDATE_FIELD", "COLLISION_REASON", "CONTRACT_FIELDS", "CONTRACT_REASONS", "DEFAULT_CONTRACT",
        "ExistingRawTargetRelativePathsSnapshot", "RawTargetRelativePathContract", "REASON_VOCABULARY", "RULE_ID",
        "SCALAR_REASONS", "SNAPSHOT_FIELDS", "SNAPSHOT_REASONS", "STANDALONE_CONTEXT_VALIDATION_ORDER",
        "RESULT_FIELDS", "CONSUMED_CANDIDATE_FIELDS", "OUTCOMES", "Admit011EvaluationResult", "_scalar_reason",
        "_canonical_path", "_result", "_contract_valid", "_snapshot_valid", "fields",
    }
    assert checker.APPROVED_ATTRIBUTE_CALLS == {"isascii", "startswith", "isspace", "split", "isalpha", "endswith"}
    assert checker._check_ast_closure(_production_source_text()).reachable_definitions == checker.EXPECTED_CLOSURE


def _source_with_before_marker(source: str, addition: str) -> str:
    marker = checker.EVALUATOR_CLOSURE_MARKER
    assert source.count(marker) == 1
    return source.replace(marker, addition + marker, 1)


def _runtime_binding_mutation(source: str, kind: str) -> str:
    if kind == "scalar_after_marker":
        return source + "\n_ORIGINAL_SCALAR_REASON = _scalar_reason\n_scalar_reason = lambda value: (\n    __import__(\"pathlib\").Path(\"/tmp/marker\").write_text(\"x\"),\n    _ORIGINAL_SCALAR_REASON(value),\n)[1]\n"
    if kind == "scalar_before_marker":
        return _source_with_before_marker(source, "_scalar_reason = lambda value: \"\"\n\n")
    if kind == "fields_rebind":
        return source + "\nfields = lambda value: ()\n"
    if kind == "dataclass_rebind":
        anchor = "@dataclass(frozen=True)\nclass Admit011EvaluationResult:"
        assert anchor in source
        return source.replace(anchor, "dataclass = lambda **kwargs: (lambda value: value)\n" + anchor, 1)
    if kind == "default_contract_rebind":
        return source + "\nDEFAULT_CONTRACT = object()\n"
    if kind == "scalar_reasons_rebind":
        return source + "\nSCALAR_REASONS = ()\n"
    if kind == "second_fields_import":
        return source + "\nfrom dataclasses import fields\n"
    if kind == "evaluate_import_alias":
        return source + "\nimport pathlib as evaluate_admit_011\n"
    if kind == "delete_protected":
        return source + "\ndel RULE_ID\n"
    if kind == "comprehension_binding":
        return source + "\nIGNORED = [_scalar_reason for _scalar_reason in ()]\n"
    if kind == "except_binding":
        return source + "\ntry:\n    pass\nexcept Exception as fields:\n    pass\n"
    raise AssertionError(f"unknown runtime binding mutation: {kind}")


@pytest.mark.parametrize("kind", (
    "scalar_after_marker", "scalar_before_marker", "fields_rebind", "dataclass_rebind",
    "default_contract_rebind", "scalar_reasons_rebind", "second_fields_import", "evaluate_import_alias",
    "delete_protected", "comprehension_binding", "except_binding",
))
def test_runtime_binding_provenance_rejects_real_source_rebindings(tmp_path: Path, kind: str) -> None:
    source_path = tmp_path / "formal_copy.py"
    source_path.write_text(_runtime_binding_mutation(_production_source_text(), kind), encoding="utf-8")
    mutated = source_path.read_text(encoding="utf-8")
    with pytest.raises(AssertionError):
        checker._check_runtime_binding_provenance(ast.parse(mutated))


def test_marker_after_scalar_rebinding_keeps_prefix_and_closure_but_is_rejected(tmp_path: Path) -> None:
    source = _production_source_text()
    mutated_path = tmp_path / "formal_copy.py"
    mutated_path.write_text(_runtime_binding_mutation(source, "scalar_after_marker"), encoding="utf-8")
    mutated = mutated_path.read_text(encoding="utf-8")
    marker = checker.EVALUATOR_CLOSURE_MARKER
    prefix = mutated[:mutated.index(marker)]
    assert hashlib.sha256(prefix.encode("utf-8")).hexdigest() == checker.EXPECTED_EVALUATOR_PREFIX_SHA256
    assert checker._check_ast_closure(mutated).reachable_definitions == checker.EXPECTED_CLOSURE
    with pytest.raises(AssertionError):
        checker._check_runtime_binding_provenance(ast.parse(mutated))
    with pytest.raises(AssertionError):
        checker._check_frozen_production_source(mutated)


@pytest.mark.parametrize("kind", ("duplicate", "deleted", "benign_after_marker"))
def test_full_source_freeze_rejects_marker_and_post_marker_drift(tmp_path: Path, kind: str) -> None:
    source = _production_source_text()
    if kind == "duplicate":
        mutated = source + "\n" + checker.EVALUATOR_CLOSURE_MARKER + "\n"
    elif kind == "deleted":
        mutated = source.replace(checker.EVALUATOR_CLOSURE_MARKER, "", 1)
    else:
        mutated = source + "\n_BENIGN_AFTER_MARKER_ASSIGNMENT = 1\n"
    source_path = tmp_path / "formal_copy.py"
    source_path.write_text(mutated, encoding="utf-8")
    with pytest.raises(AssertionError):
        checker._check_frozen_production_source(source_path.read_text(encoding="utf-8"))


def test_formal_checker_rejects_source_drift_before_output_business_checks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original = checker._read_attested_source
    def source_drift(plan: checker.SourcePlan) -> bytes:
        content = original(plan)
        return content + b"\n_AFTER_MARKER_DRIFT = 1\n" if plan.relative == checker.FORMAL_RELATIVE_PATH else content
    monkeypatch.setattr(checker, "_read_attested_source", source_drift)
    importer_called = False
    def importer(_: checker.FormalAttestation) -> checker.ModuleBundle:
        nonlocal importer_called
        importer_called = True
        raise AssertionError("lazy importer must not run")
    def output_read_must_not_run(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("derived business content was read")
    monkeypatch.setattr(checker, "_read_pinned_output_bytes", output_read_must_not_run)
    with pytest.raises(AssertionError, match="production source SHA256 mismatch"):
        checker.validate_output_tree(checker.STAGE, lazy_importer=importer)
    assert importer_called is False


def test_frozen_source_runtime_provenance_and_exact8_ast_digests_pass() -> None:
    source = _production_source_text()
    tree = checker._check_frozen_production_source(source)
    assert tuple(checker._reachable_ast_nodes(tree)) == tuple(checker.EXPECTED_REACHABLE_AST_SHA256)
    assert set(checker.PROTECTED_RUNTIME_BINDINGS) == {
        "evaluate_admit_011", "_scalar_reason", "_canonical_path", "_result", "_contract_valid",
        "_snapshot_valid", "Admit011EvaluationResult", "dataclass", "fields", "CANDIDATE_FIELD",
        "COLLISION_REASON", "CONTRACT_FIELDS", "CONTRACT_REASONS", "DEFAULT_CONTRACT",
        "ExistingRawTargetRelativePathsSnapshot", "RawTargetRelativePathContract", "REASON_VOCABULARY",
        "RULE_ID", "SCALAR_REASONS", "SNAPSHOT_FIELDS", "SNAPSHOT_REASONS",
        "STANDALONE_CONTEXT_VALIDATION_ORDER", "VALIDATION_PRECEDENCE", "RESULT_FIELDS",
        "CONSUMED_CANDIDATE_FIELDS", "OUTCOMES",
    }
    assert checker.EXPECTED_IMPORTED_BINDINGS["dataclass"] == "dataclasses.dataclass"
    assert checker.EXPECTED_IMPORTED_BINDINGS["fields"] == "dataclasses.fields"


@pytest.mark.parametrize("old,new", (
    (
        'RESULT_FIELDS = (\n    "admission_rule_id", "outcome", "passed", "blocks_candidate", "reason",',
        'RESULT_FIELDS = (\n    "outcome", "admission_rule_id", "passed", "blocks_candidate", "reason",',
    ),
    ('CONSUMED_CANDIDATE_FIELDS = (CANDIDATE_FIELD,)', 'CONSUMED_CANDIDATE_FIELDS = ("raw_target_relative_path",)'),
    ('OUTCOMES = ("passed", "blocked", "invalid")', 'OUTCOMES = ("passed", "blocked", "tampered")'),
))
def test_runtime_provenance_rejects_frozen_module_constant_ast_value_drift(old: str, new: str) -> None:
    source = _production_source_text()
    assert old in source
    with pytest.raises(AssertionError):
        checker._check_runtime_binding_provenance(ast.parse(source.replace(old, new, 1)))


def _reachable_mutation_source(kind: str) -> str:
    source = _production_source_text()
    if kind == "attribute_store":
        return _with_function_statement(source, "_snapshot_valid", "    value.snapshot_complete = False\n")
    if kind == "attribute_delete":
        return _with_function_statement(source, "_snapshot_valid", "    del value.snapshot_complete\n")
    if kind == "subscript_store":
        return _with_function_statement(source, "_snapshot_valid", "    value.occupied_relative_paths[0] = \"data/raw/mutated.cif\"\n")
    if kind == "method_before_type_guard":
        return _with_function_statement(source, "_scalar_reason", "    value.startswith(\"\")\n")
    if kind == "type_guard_after_method":
        old = "    if type(value) is not str:\n        return SCALAR_REASONS[0]\n    if value == \"\":\n        return SCALAR_REASONS[1]\n    if not value.isascii():\n        return SCALAR_REASONS[2]\n"
        new = "    if not value.isascii():\n        return SCALAR_REASONS[2]\n    if type(value) is not str:\n        return SCALAR_REASONS[0]\n    if value == \"\":\n        return SCALAR_REASONS[1]\n"
        assert old in source
        return source.replace(old, new, 1)
    if kind == "pure_assignment":
        return _with_function_statement(source, "_scalar_reason", "    pure_local = 1\n")
    if kind == "if_order":
        old = "    if \"%\" in value:\n        return SCALAR_REASONS[10]\n    if value.startswith(\"~\"):\n        return SCALAR_REASONS[11]\n"
        new = "    if value.startswith(\"~\"):\n        return SCALAR_REASONS[11]\n    if \"%\" in value:\n        return SCALAR_REASONS[10]\n"
        assert old in source
        return source.replace(old, new, 1)
    if kind == "reason_index":
        return source.replace("return SCALAR_REASONS[0]", "return SCALAR_REASONS[1]", 1)
    raise AssertionError(f"unknown reachable mutation: {kind}")


@pytest.mark.parametrize("kind", ("attribute_store", "attribute_delete", "subscript_store"))
def test_reachable_mutation_rules_reject_attribute_and_subscript_writes(kind: str) -> None:
    with pytest.raises(AssertionError, match="mutation"):
        checker._check_ast_closure(_reachable_mutation_source(kind))


@pytest.mark.parametrize("kind", (
    "method_before_type_guard", "type_guard_after_method", "pure_assignment", "if_order", "reason_index",
))
def test_exact_ast_digests_reject_allowed_shape_semantic_drift(kind: str) -> None:
    source = _reachable_mutation_source(kind)
    checker._check_ast_closure(source)
    with pytest.raises(AssertionError, match="exact AST digest"):
        checker._check_reachable_ast_digests(ast.parse(source))


def test_checker_import_is_stdlib_only_and_has_no_side_effect(tmp_path: Path) -> None:
    command = [
        sys.executable, "-B", "-c",
        "import sys; import scripts.check_covapie_bulk_download_admission_admit_011_rule_logic_interface_v1; "
        "assert not any(name == 'covalent_ext' or name.startswith('covalent_ext.') for name in sys.modules)",
    ]
    result = subprocess.run(command, cwd=tmp_path, env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])}, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    assert result.stdout == result.stderr == "" and list(tmp_path.iterdir()) == []


def test_design_source_drift_blocks_lazy_import_and_output_byte_read(monkeypatch: pytest.MonkeyPatch) -> None:
    original = checker._read_attested_source
    def source_drift(plan: checker.SourcePlan) -> bytes:
        content = original(plan)
        return b"drift" if plan.relative == checker.FROZEN_SOURCE_BOUNDARY[0][0] else content
    monkeypatch.setattr(checker, "_read_attested_source", source_drift)
    importer_called = False
    def importer(_: checker.FormalAttestation) -> checker.ModuleBundle:
        nonlocal importer_called
        importer_called = True
        raise AssertionError("lazy importer must not run")
    monkeypatch.setattr(checker, "_read_pinned_output_bytes", lambda *_: (_ for _ in ()).throw(AssertionError("output bytes must not be read")))
    with pytest.raises(AssertionError, match="fixed source SHA256"):
        checker.validate_output_tree(lazy_importer=importer)
    assert importer_called is False


def test_import_time_marker_source_drift_is_not_executed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    marker = tmp_path / "import-time-marker"
    original = checker._read_attested_source
    def source_drift(plan: checker.SourcePlan) -> bytes:
        content = original(plan)
        payload = f'\nPath({str(marker)!r}).write_text("executed")\n'.encode("utf-8")
        return content + payload if plan.relative == checker.FORMAL_RELATIVE_PATH else content
    monkeypatch.setattr(checker, "_read_attested_source", source_drift)
    with pytest.raises(AssertionError, match="production source SHA256 mismatch"):
        checker.validate_output_tree(lazy_importer=lambda _: (_ for _ in ()).throw(AssertionError("must not import")))
    assert not marker.exists()


def test_successful_attestation_calls_lazy_importer_before_pinned_output_read(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    original_importer = checker._default_lazy_importer
    original_reader = checker._read_pinned_output_bytes
    def importer(attestation: checker.FormalAttestation) -> checker.ModuleBundle:
        calls.append("import")
        return original_importer(attestation)
    def reader(tree: checker.PinnedOutputTree) -> dict[str, bytes]:
        calls.append("read")
        return original_reader(tree)
    monkeypatch.setattr(checker, "_read_pinned_output_bytes", reader)
    checker.validate_output_tree(lazy_importer=importer)
    assert calls[:2] == ["import", "read"]


def test_imported_module_path_and_runtime_binding_mismatches_fail_closed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    plan = checker._inspect_attested_leaf(checker.FORMAL_SOURCE_PATH, checker.ROOT)
    content = checker._read_attested_source(plan)
    attestation = checker.FormalAttestation(plan.path, plan.identity, content, content.decode("utf-8"), checker._check_frozen_production_source(content.decode("utf-8"), content))
    bundle = checker._default_lazy_importer(attestation)
    original_file = bundle.formal.__file__
    monkeypatch.setattr(bundle.formal, "__file__", str(tmp_path / "wrong.py"))
    with pytest.raises(AssertionError, match="path identity"):
        checker._verify_imported_modules(bundle, attestation)
    monkeypatch.setattr(bundle.formal, "__file__", original_file)
    monkeypatch.setattr(bundle.formal, "_scalar_reason", lambda _value: "")
    with pytest.raises(AssertionError, match="runtime local binding"):
        checker._verify_imported_modules(bundle, attestation)


@pytest.mark.parametrize("kind", ("parent_symlink", "root_symlink_inside", "root_symlink_outside", "broken_root_symlink", "root_file", "root_fifo", "unexpected", "missing"))
def test_pinned_output_preflight_rejects_unsafe_trees_before_source_attestation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str) -> None:
    parent = tmp_path / "parent"; parent.mkdir(); root = parent / "stage"
    if kind == "parent_symlink":
        target = tmp_path / "real"; target.mkdir(); parent.rmdir(); parent.symlink_to(target, target_is_directory=True)
    elif kind == "root_symlink_inside":
        root.symlink_to(checker.STAGE, target_is_directory=True)
    elif kind == "root_symlink_outside":
        target = tmp_path / "target"; target.mkdir(); root.symlink_to(target, target_is_directory=True)
    elif kind == "broken_root_symlink":
        root.symlink_to(tmp_path / "missing", target_is_directory=True)
    elif kind == "root_file":
        root.write_bytes(b"x")
    elif kind == "root_fifo":
        os.mkfifo(root)
    else:
        shutil.copytree(checker.STAGE, root)
        if kind == "unexpected":
            (root / "unexpected").write_bytes(b"x")
        else:
            (root / checker.OUTPUT_FILES[0]).unlink()
    monkeypatch.setattr(checker, "_validate_repository_lineage", lambda: (_ for _ in ()).throw(AssertionError("source attestation must not run")))
    with pytest.raises(AssertionError):
        checker.validate_output_tree(root)


@pytest.mark.parametrize("kind", ("leaf_symlink", "leaf_directory", "leaf_fifo", "root_replaced", "leaf_replaced"))
def test_pinned_output_reader_detects_post_preflight_replacement(tmp_path: Path, kind: str) -> None:
    root = tmp_path / "stage"; shutil.copytree(checker.STAGE, root)
    if kind in {"leaf_symlink", "leaf_directory", "leaf_fifo"}:
        leaf = root / checker.OUTPUT_FILES[0]; leaf.unlink()
        if kind == "leaf_symlink":
            leaf.symlink_to(root / checker.OUTPUT_FILES[1])
        elif kind == "leaf_directory":
            leaf.mkdir()
        else:
            os.mkfifo(leaf)
        with pytest.raises(AssertionError):
            checker._open_pinned_output_tree(root)
        return
    tree = checker._open_pinned_output_tree(root)
    try:
        if kind == "root_replaced":
            moved = tmp_path / "moved"; root.rename(moved); root.mkdir()
        else:
            leaf = root / checker.OUTPUT_FILES[0]; leaf.unlink(); leaf.write_bytes(b"replacement")
        with pytest.raises(AssertionError):
            checker._read_pinned_output_bytes(tree)
    finally:
        os.close(tree.root_fd)


@pytest.mark.parametrize("field", (
    "manifest_schema_version", "stage", "base_commit", "base_subject", "admission_rule_id", "admission_rule_name",
    "public_api", "public_signature_parameters", "result_type", "result_fields", "source_paths", "source_input_count",
    "output_files", "output_file_count", "row_counts", "reason_vocabulary", "validation_precedence", "readiness",
    "feature_semantics_audit_required_before_training", "step12d_is_final_training_feature_contract", "step12d_status",
    "recommended_next_step", "safety", "output_sha256", "all_checks_passed",
))
def test_manifest_all_top_level_exact_values_reject_synchronized_tamper(tmp_path: Path, field: str) -> None:
    copied = _copied_output_tree(tmp_path)
    path = copied / checker.MANIFEST_FILENAME
    manifest = json.loads(path.read_text(encoding="utf-8"))
    value = manifest[field]
    if isinstance(value, bool):
        manifest[field] = not value
    elif isinstance(value, int):
        manifest[field] = value + 1
    elif isinstance(value, str):
        manifest[field] = value + "_tampered"
    elif isinstance(value, list):
        manifest[field] = list(reversed(value))
    elif isinstance(value, dict):
        changed = dict(value); first = next(iter(changed)); changed[first] = (not changed[first]) if isinstance(changed[first], bool) else "tampered"; manifest[field] = changed
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        checker.validate_output_tree(copied, enforce_frozen_hashes=False)


@pytest.mark.parametrize("kind", ("manifest_extra", "manifest_missing", "readiness_extra", "readiness_missing", "projection_mismatch", "output_hash_extra", "output_hash_missing"))
def test_manifest_keyset_and_projection_tampers_reject(tmp_path: Path, kind: str) -> None:
    copied = _copied_output_tree(tmp_path)
    path = copied / checker.MANIFEST_FILENAME
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if kind == "manifest_extra":
        manifest["unexpected"] = False
    elif kind == "manifest_missing":
        del manifest["all_checks_passed"]
    elif kind == "readiness_extra":
        manifest["readiness"]["unexpected"] = False
    elif kind == "readiness_missing":
        del manifest["readiness"]["ready_for_training"]
    elif kind == "projection_mismatch":
        manifest["ready_for_training"] = True
    elif kind == "output_hash_extra":
        manifest["output_sha256"]["unexpected"] = "0" * 64
    else:
        del manifest["output_sha256"][checker.OUTPUT_FILES[0]]
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        checker.validate_output_tree(copied, enforce_frozen_hashes=False)


@pytest.mark.parametrize("key", (*checker.TRUE_READINESS, *checker.FALSE_READINESS))
def test_manifest_every_readiness_projection_flip_rejects(tmp_path: Path, key: str) -> None:
    copied = _copied_output_tree(tmp_path)
    path = copied / checker.MANIFEST_FILENAME
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["readiness"][key] = not manifest["readiness"][key]
    manifest[key] = manifest["readiness"][key]
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        checker.validate_output_tree(copied, enforce_frozen_hashes=False)


@pytest.mark.parametrize("group,key", tuple(("row_counts", key) for key in ("contract", "truth", "truth_historical", "source_boundary", "purity", "issue")) + tuple(("safety", key) for key in ("filesystem_used_by_evaluator", "network_used_by_evaluator", "raw_read_by_evaluator", "mutation_by_evaluator")))
def test_manifest_every_row_count_and_safety_value_rejects(tmp_path: Path, group: str, key: str) -> None:
    copied = _copied_output_tree(tmp_path)
    path = copied / checker.MANIFEST_FILENAME
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest[group][key] = manifest[group][key] + 1 if group == "row_counts" else True
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        checker.validate_output_tree(copied, enforce_frozen_hashes=False)


@pytest.mark.parametrize("field,value", (
    ("source_order", "99"), ("source_relative_path", "docs/tampered"), ("expected_sha256", "0" * 64),
    ("base_tree_sha256", "0" * 64), ("filesystem_sha256", "0" * 64), ("git_tracked", "false"),
    ("regular", "false"), ("non_symlink", "false"), ("source_boundary_passed", "false"),
))
def test_source_boundary_csv_exact11_fields_reject_synchronized_tamper(tmp_path: Path, field: str, value: str) -> None:
    copied = _copied_output_tree(tmp_path)
    _rewrite_csv(copied, checker.SOURCE_FILENAME, checker.SOURCE_COLUMNS, lambda rows: rows[0].__setitem__(field, value))
    _refresh_output_hashes(copied)
    with pytest.raises(AssertionError):
        checker.validate_output_tree(copied, enforce_frozen_hashes=False)


@pytest.mark.parametrize("kind", ("reorder", "extra_row", "missing_row", "extra_column", "missing_column"))
def test_source_boundary_csv_exact11_shape_tampers_reject(tmp_path: Path, kind: str) -> None:
    copied = _copied_output_tree(tmp_path)
    path = copied / checker.SOURCE_FILENAME
    rows = list(csv.DictReader(path.read_text(encoding="utf-8").splitlines()))
    columns = checker.SOURCE_COLUMNS
    if kind == "reorder":
        rows[0], rows[1] = rows[1], rows[0]
    elif kind == "extra_row":
        rows.append(dict(rows[-1]))
    elif kind == "missing_row":
        rows.pop()
    elif kind == "extra_column":
        columns = checker.SOURCE_COLUMNS + ("extra",)
    elif kind == "missing_column":
        columns = checker.SOURCE_COLUMNS[:-1]
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
    path.write_text(output.getvalue(), encoding="utf-8")
    _refresh_output_hashes(copied)
    with pytest.raises(AssertionError):
        checker.validate_output_tree(copied, enforce_frozen_hashes=False)


def test_production_checker_and_frozen_source_boundary_rows_are_identical() -> None:
    assert formal._source_rows(formal.REPO_ROOT) == checker._expected_source_rows()
