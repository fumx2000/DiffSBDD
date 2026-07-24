"""Targeted tests for the pure ADMIT_015 standalone evaluator."""

import csv
import errno
import hashlib
import importlib.util
import inspect
import io
import json
import os
import subprocess
import sys
from collections.abc import Iterator, Mapping
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_bulk_download_admission_admit_015_standalone_evaluator_interface
    as implementation,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / (
    "scripts/"
    "check_covapie_bulk_download_admission_admit_015_standalone_evaluator_interface_v1.py"
)
TRUTH_PATH = ROOT / implementation.FORMAL_DESIGN_ROOT / (
    "covapie_admit_015_formal_evaluator_interface_truth_matrix.csv"
)


def _load_checker():
    spec = importlib.util.spec_from_file_location(
        "_admit015_checker_test", CHECKER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Probe(Mapping[str, object]):
    def __init__(
        self,
        values: dict[str, object] | None = None,
        *,
        error: BaseException | None = None,
    ) -> None:
        self.values = {} if values is None else values
        self.error = error
        self.item_keys: list[str] = []
        self.iteration = 0
        self.length = 0
        self.gets = 0
        self.contains = 0

    def __getitem__(self, key: str) -> object:
        self.item_keys.append(key)
        if self.error is not None:
            raise self.error
        return self.values[key]

    def __iter__(self) -> Iterator[str]:
        self.iteration += 1
        raise AssertionError("iteration forbidden")

    def __len__(self) -> int:
        self.length += 1
        raise AssertionError("len forbidden")

    def get(self, key: str, default: object = None) -> object:
        self.gets += 1
        raise AssertionError("get forbidden")

    def __contains__(self, key: object) -> bool:
        self.contains += 1
        raise AssertionError("contains forbidden")


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )


def _commit(repo: Path, message: str) -> None:
    result = _git(
        repo,
        "-c",
        "user.name=CovaPIE Test",
        "-c",
        "user.email=covapie-test@example.invalid",
        "commit",
        "-m",
        message,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def _seed_lifecycle(
    root: Path,
    checker,
    *,
    tracked: bool = False,
    descendant: bool = False,
) -> tuple[Path, str]:
    root.mkdir()
    assert _git(root, "init", "-q").returncode == 0
    (root / "baseline.txt").write_text("baseline\n")
    assert _git(root, "add", "--", "baseline.txt").returncode == 0
    _commit(root, "baseline")
    base = _git(root, "rev-parse", "HEAD").stdout.strip()
    if descendant:
        (root / "descendant.txt").write_text("descendant\n")
        assert _git(root, "add", "--", "descendant.txt").returncode == 0
        _commit(root, "descendant")
    for relative in checker.STAGE_PATHS:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"fixture:{relative.as_posix()}\n")
    if tracked:
        assert _git(
            root,
            "add",
            "--",
            *(path.as_posix() for path in checker.STAGE_PATHS),
        ).returncode == 0
        _commit(root, "Exact10")
    return root, base


def _write_exact6(root: Path, payloads: dict[str, bytes]) -> None:
    root.mkdir(parents=True)
    for name, content in payloads.items():
        (root / name).write_bytes(content)


def _replace_exact6_directory(
    root: Path,
    payloads: dict[str, bytes],
    suffix: str = "displaced",
) -> Path:
    displaced = root.with_name(f"{root.name}-{suffix}")
    os.rename(root, displaced)
    _write_exact6(root, payloads)
    return displaced


@pytest.fixture(scope="module")
def snapshot():
    return implementation.build_frozen_source_snapshot()


@pytest.fixture(scope="module")
def payloads(snapshot):
    return implementation.build_artifacts(snapshot)


def test_base_identity_and_canonical_python() -> None:
    result = _git(
        ROOT,
        "show",
        "-s",
        "--format=%H%n%P%n%T%n%s",
        implementation.BASE_COMMIT,
    )
    assert result.stdout.splitlines() == [
        implementation.BASE_COMMIT,
        implementation.BASE_PARENT,
        implementation.BASE_TREE,
        implementation.BASE_SUBJECT,
    ]
    assert _git(
        ROOT,
        "merge-base",
        "--is-ancestor",
        implementation.BASE_COMMIT,
        "HEAD",
    ).returncode == 0
    assert sys.implementation.name == "cpython"
    assert tuple(sys.version_info[:3]) == (3, 10, 4)


def test_canonical_guard_is_evidence_only(monkeypatch) -> None:
    def reject():
        raise RuntimeError("noncanonical")

    monkeypatch.setattr(
        implementation, "_assert_canonical_evidence_runtime", reject
    )
    assert implementation.evaluate_admit_015().reason == (
        "STAGE_AUTHORIZATION_CONTEXT_REQUIRED"
    )
    with pytest.raises(RuntimeError, match="noncanonical"):
        implementation.build_artifacts(snapshot=())


def test_exact15_source_order_sha_tracking_and_safety(
    snapshot, payloads
) -> None:
    assert len(snapshot) == 15
    assert tuple(record.path for record in snapshot) == (
        implementation.SOURCE_PATHS
    )
    assert [record.sha256 for record in snapshot] == list(
        implementation.SOURCE_SHA256.values()
    )
    audit = list(
        csv.DictReader(
            io.StringIO(payloads[implementation.SOURCE_FILE].decode())
        )
    )
    assert len(audit) == 15
    for row, record in zip(audit, snapshot, strict=True):
        assert not record.path.as_posix().startswith(
            ("data/raw/", "checkpoints/")
        )
        stage = _git(
            ROOT, "ls-files", "--stage", "--", record.path.as_posix()
        )
        assert stage.returncode == 0
        assert stage.stdout.split()[2] == "0"
        tree = _git(
            ROOT,
            "ls-tree",
            implementation.BASE_COMMIT,
            "--",
            record.path.as_posix(),
        )
        tree_fields = tree.stdout.partition("\t")[0].split()
        stage_fields = stage.stdout.partition("\t")[0].split()
        assert row["base_tree_blob"] != "true"
        assert len(row["base_tree_blob"]) == 40
        assert set(row["base_tree_blob"]) <= set("0123456789abcdef")
        assert row["base_tree_mode"] == tree_fields[0] == stage_fields[0]
        assert row["base_tree_blob"] == tree_fields[2] == stage_fields[1]
        assert row["expected_sha256"] == record.sha256


def test_actual_signature_private_missing_and_call_rejection() -> None:
    signature = inspect.signature(implementation.evaluate_admit_015)
    assert tuple(signature.parameters) == ("stage_authorization_context",)
    parameter = signature.parameters["stage_authorization_context"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.annotation is object
    assert parameter.default is implementation._MISSING
    assert signature.return_annotation is implementation.Admit015EvaluationResult
    assert implementation._MISSING is implementation._MISSING
    assert type(implementation._MISSING).__name__ == "_MissingAdmit015Value"
    with pytest.raises(TypeError):
        implementation.evaluate_admit_015(object())
    with pytest.raises(TypeError):
        implementation.evaluate_admit_015(unknown=True)


def test_omitted_and_none_are_structured_blocked() -> None:
    for result in (
        implementation.evaluate_admit_015(),
        implementation.evaluate_admit_015(
            stage_authorization_context=None
        ),
    ):
        assert (
            result.outcome,
            result.reason,
            result.canonical_stage_authorization_record,
            result.validated_stage_authorization_fields,
            result.consumed_stage_authorization_fields,
        ) == (
            "blocked",
            "STAGE_AUTHORIZATION_CONTEXT_REQUIRED",
            (),
            (),
            (),
        )


@pytest.mark.parametrize("value", [object(), 7, "x", []])
def test_nonmapping_blocks_without_consumption(value: object) -> None:
    result = implementation.evaluate_admit_015(
        stage_authorization_context=value
    )
    assert result.reason == "STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID"
    assert result.canonical_stage_authorization_record == ()
    assert result.validated_stage_authorization_fields == ()
    assert result.consumed_stage_authorization_fields == ()


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (KeyError("target"), "CURRENT_STAGE_TRAINING_AUTHORIZED_MISSING"),
        (RuntimeError("boom"), "STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED"),
        (ValueError("boom"), "STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED"),
    ],
)
def test_lookup_failures_consume_target_once(
    error: BaseException, reason: str
) -> None:
    probe = Probe(error=error)
    result = implementation.evaluate_admit_015(
        stage_authorization_context=probe
    )
    assert result.reason == reason
    assert result.canonical_stage_authorization_record == ()
    assert result.validated_stage_authorization_fields == ()
    assert result.consumed_stage_authorization_fields == (
        implementation.AUTHORIZATION_CONTEXT_ITEM,
    )
    assert probe.item_keys == [implementation.AUTHORIZATION_CONTEXT_ITEM]
    assert (
        probe.iteration, probe.length, probe.gets, probe.contains
    ) == (0, 0, 0, 0)


@pytest.mark.parametrize(
    "value",
    [0, 1, 0.0, 1.0, "false", "true", None, [], {}, object()],
)
def test_invalid_exact_bool_types_block_without_bool_coercion(
    value: object,
) -> None:
    probe = Probe({implementation.AUTHORIZATION_CONTEXT_ITEM: value})
    result = implementation.evaluate_admit_015(
        stage_authorization_context=probe
    )
    assert result.reason == "CURRENT_STAGE_TRAINING_AUTHORIZED_TYPE_INVALID"
    assert result.validated_stage_authorization_fields == ()
    assert result.consumed_stage_authorization_fields == (
        implementation.AUTHORIZATION_CONTEXT_ITEM,
    )
    assert probe.item_keys == [implementation.AUTHORIZATION_CONTEXT_ITEM]


@pytest.mark.parametrize("permission", [False, True])
def test_exact_bool_and_admit015_coexistence(permission: bool) -> None:
    probe = Probe(
        {
            implementation.DOWNLOAD_AUTHORIZATION_CONTEXT_ITEM: not permission,
            "extra": object(),
            implementation.AUTHORIZATION_CONTEXT_ITEM: permission,
        }
    )
    result = implementation.evaluate_admit_015(
        stage_authorization_context=probe
    )
    assert result.outcome == ("passed" if permission else "blocked")
    assert result.reason == (
        "" if permission else "TRAINING_NOT_AUTHORIZED"
    )
    assert result.canonical_stage_authorization_record == (
        (implementation.AUTHORIZATION_CONTEXT_ITEM, permission),
    )
    assert result.validated_stage_authorization_fields == (
        implementation.AUTHORIZATION_CONTEXT_ITEM,
    )
    assert result.consumed_stage_authorization_fields == (
        implementation.AUTHORIZATION_CONTEXT_ITEM,
    )
    assert probe.item_keys == [implementation.AUTHORIZATION_CONTEXT_ITEM]
    assert (
        probe.iteration, probe.length, probe.gets, probe.contains
    ) == (0, 0, 0, 0)


def test_exact9_types_frozen_reconstruction_and_subclass_rejection() -> None:
    result = implementation.evaluate_admit_015(
        stage_authorization_context={
            implementation.AUTHORIZATION_CONTEXT_ITEM: True
        }
    )
    assert tuple(field.name for field in fields(type(result))) == (
        implementation.RESULT_FIELDS
    )
    assert tuple(
        type(getattr(result, name)).__name__
        for name in implementation.RESULT_FIELDS
    ) == (
        "str", "str", "bool", "bool", "str",
        "tuple", "tuple", "tuple", "bool",
    )
    reconstructed = implementation.Admit015EvaluationResult(
        *(getattr(result, name) for name in implementation.RESULT_FIELDS)
    )
    assert reconstructed == result
    with pytest.raises(FrozenInstanceError):
        result.reason = "changed"

    with pytest.raises(TypeError):
        class Subclass(implementation.Admit015EvaluationResult):
            pass


def test_all_exact24_actual_malformed_results_rejected() -> None:
    checker = _load_checker()
    assert len(checker.NEGATIVE_RESULT_CASES) == 24
    for case_id in checker.NEGATIVE_RESULT_CASES:
        checker._reject_negative(implementation, case_id)


def test_actual_equals_independent_checker_oracle_exact37() -> None:
    checker = _load_checker()
    sources = {
        implementation.FORMAL_DESIGN_ROOT
        / "covapie_admit_015_formal_evaluator_interface_truth_matrix.csv": (
            TRUTH_PATH.read_bytes()
        )
    }
    checker._check_actual(implementation, sources)


def test_formal_marker_prefix_ast_and_purity(payloads) -> None:
    source, full_sha, prefix_sha, digests = (
        implementation._formal_source_attestation()
    )
    manifest = json.loads(payloads[implementation.MANIFEST_FILE])
    assert source.decode().count(implementation.FORMAL_MARKER) == 1
    assert full_sha == (
        "eacb5c1ac583649a34cdb9dcde4c004a861da43609b9ffb964a715a427883a82"
    )
    assert prefix_sha == (
        "d9c98704ea4464e12c6866d725b5445c566ab0183b67ca1e2e8f53860c47dbf9"
    )
    assert tuple(digests) == implementation.FORMAL_CLOSURE
    assert len(digests) == 7
    assert manifest["formal_ast_sha256"] == digests
    purity = list(
        csv.DictReader(
            io.StringIO(payloads[implementation.PURITY_FILE].decode())
        )
    )
    assert len(purity) == 16
    assert all(
        row["forbidden_io_absent"] == "true"
        and row["mutation_absent"] == "true"
        and row["dynamic_dispatch_absent"] == "true"
        and row["purity_passed"] == "true"
        for row in purity
    )


def test_truth_exact61_issue_byte_identity_preconditions_readiness(
    payloads,
) -> None:
    truth = list(
        csv.DictReader(
            io.StringIO(payloads[implementation.TRUTH_FILE].decode())
        )
    )
    assert len(truth) == 61
    assert sum(
        row["case_group"] != "negative_result_contract" for row in truth
    ) == 37
    assert sum(
        row["case_group"] == "negative_result_contract" for row in truth
    ) == 24
    assert all(row["truth_passed"] == "true" for row in truth)
    predecessor_issue = (
        ROOT
        / implementation.FORMAL_DESIGN_ROOT
        / "covapie_admit_015_formal_evaluator_interface_issue_readiness_inventory.csv"
    ).read_bytes()
    assert payloads[implementation.ISSUE_FILE] == predecessor_issue
    assert hashlib.sha256(predecessor_issue).hexdigest() == (
        "f457da61bffade18999af5c069d237c30aa30a0c63efb8bb14130935fb0757ec"
    )
    manifest = json.loads(payloads[implementation.MANIFEST_FILE])
    assert manifest["precondition_transition"]["complete_count"] == 37
    assert manifest["precondition_transition"]["incomplete_count"] == 8
    assert manifest["precondition_transition"][
        "remaining_open_precondition_ids"
    ] == [
        "PRE_031", "PRE_032", "PRE_033", "PRE_034",
        "PRE_035", "PRE_036", "PRE_038", "PRE_042",
    ]
    expected = {
        **{name: True for name in implementation.TRUE_READINESS},
        **{name: False for name in implementation.FALSE_READINESS},
    }
    assert manifest["readiness"] == expected
    assert manifest["current_permission"] is False
    assert manifest["authorized_admit_015_training_execution_count"] == 0
    assert manifest["recommended_next_step"] == (
        "design_covapie_admit_015_unified_adapter_contract_v1"
    )


def test_no_adapter_registry_exact14_enforcement_provider_or_training() -> None:
    source = (ROOT / (
        "src/covalent_ext/"
        "covapie_bulk_download_admission_admit_015_standalone_evaluator_interface.py"
    )).read_text()
    prefix = source.split(implementation.FORMAL_MARKER, 1)[0]
    assert "_evaluate_registered_admit_015" not in prefix
    assert "EVALUATOR_REGISTRY" not in prefix
    assert "classify_admit_015_formal_evaluator_interface_design" not in prefix
    runtime = json.loads(
        (
            ROOT
            / "data/derived/covalent_small/"
            "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014_v1/"
            "covapie_admit_001_to_014_runtime_manifest.json"
        ).read_text()
    )
    assert runtime["known_not_registered_rule_ids"] == ["ADMIT_015"]
    assert runtime["admit_015_registered_in_engine"] is False
    assert runtime["combined_candidate_verdict_implemented"] is False
    assert runtime["cross_rule_aggregation_implemented"] is False


def test_deterministic_build_and_materializer_noop(tmp_path, payloads) -> None:
    assert implementation.build_artifacts() == implementation.build_artifacts()
    root = tmp_path / "out"
    first = implementation.materialize_contract(root)
    before = {
        path.name: (path.stat().st_ino, path.read_bytes())
        for path in root.iterdir()
    }
    second = implementation.materialize_contract(root)
    assert first == second
    assert before == {
        path.name: (path.stat().st_ino, path.read_bytes())
        for path in root.iterdir()
    }
    assert {path.name: path.read_bytes() for path in root.iterdir()} == payloads
    assert not list(tmp_path.glob(".*.staging"))
    assert not list(tmp_path.rglob("*.tmp"))
    assert not list(tmp_path.rglob("*.part"))
    (root / implementation.CONTRACT_FILE).write_bytes(b"tampered\n")
    with pytest.raises(ValueError, match="existing output set mismatch"):
        implementation.materialize_contract(root)
    assert not list(tmp_path.glob(".*.staging"))


def test_gpfs_einval_fails_closed_and_no_os_replace(
    tmp_path, monkeypatch
) -> None:
    root = tmp_path / "out"
    replace_called = False

    def reject(*args):
        raise OSError(errno.EINVAL, "simulated GPFS EINVAL")

    def forbidden(*args):
        nonlocal replace_called
        replace_called = True
        raise AssertionError("os.replace fallback")

    monkeypatch.setattr(implementation, "_rename_noreplace", reject)
    monkeypatch.setattr(os, "replace", forbidden)
    with pytest.raises(RuntimeError, match="failure staging retained") as captured:
        implementation.materialize_contract(root)
    assert isinstance(captured.value.__cause__, OSError)
    assert captured.value.__cause__.errno == errno.EINVAL
    assert replace_called is False
    assert not root.exists()
    retained = list(tmp_path.glob(".out.*.staging"))
    assert len(retained) == 1
    assert {path.name for path in retained[0].iterdir()} == set(
        implementation.OUTPUT_FILES
    )


@pytest.mark.parametrize(
    "race",
    [
        "leaf_replacement",
        "root_replacement",
        "final_extra",
        "final_missing",
        "parent_replacement",
    ],
)
def test_production_existing_output_races_fail_closed(
    tmp_path, monkeypatch, payloads, race: str
) -> None:
    parent = tmp_path / "parent"
    root = parent / "out"
    _write_exact6(root, payloads)
    original_read = implementation.os.read
    original_listdir = implementation.os.listdir
    mutated = False
    inventory_count = 0

    def racing_read(descriptor: int, size: int) -> bytes:
        nonlocal mutated
        data = original_read(descriptor, size)
        if data and not mutated and race in {
            "leaf_replacement",
            "root_replacement",
            "parent_replacement",
        }:
            mutated = True
            if race == "leaf_replacement":
                leaf = root / implementation.CONTRACT_FILE
                replacement = root / "replacement"
                replacement.write_bytes(leaf.read_bytes())
                os.rename(replacement, leaf)
            elif race == "root_replacement":
                _replace_exact6_directory(root, payloads)
            else:
                displaced = parent.with_name("parent-displaced")
                os.rename(parent, displaced)
                _write_exact6(root, payloads)
        return data

    def racing_listdir(path) -> list[str]:
        nonlocal inventory_count, mutated
        inventory_count += 1
        if inventory_count == 2 and race in {"final_extra", "final_missing"}:
            mutated = True
            if race == "final_extra":
                (root / "seventh.csv").write_bytes(b"extra\n")
            else:
                (root / implementation.ISSUE_FILE).unlink()
        return original_listdir(path)

    monkeypatch.setattr(implementation.os, "read", racing_read)
    monkeypatch.setattr(implementation.os, "listdir", racing_listdir)
    with pytest.raises(ValueError):
        implementation._read_exact_output_set(root, payloads)
    assert mutated


def test_production_existing_output_normal_pinned_read(
    tmp_path, payloads
) -> None:
    root = tmp_path / "out"
    _write_exact6(root, payloads)
    assert implementation._read_exact_output_set(root, payloads) is True


@pytest.mark.parametrize("phase", ["before_parent_fsync", "before_post_read"])
def test_materializer_destination_binding_races_fail_closed(
    tmp_path, monkeypatch, payloads, phase: str
) -> None:
    root = tmp_path / "out"
    mutated = False
    if phase == "before_parent_fsync":
        original_fsync = implementation.os.fsync
        parent_stat = os.stat(tmp_path)

        def racing_fsync(descriptor: int) -> None:
            nonlocal mutated
            item = os.fstat(descriptor)
            if (
                not mutated
                and root.exists()
                and (item.st_dev, item.st_ino)
                == (parent_stat.st_dev, parent_stat.st_ino)
            ):
                mutated = True
                _replace_exact6_directory(root, payloads)
            original_fsync(descriptor)

        monkeypatch.setattr(implementation.os, "fsync", racing_fsync)
    else:
        original_read_set = implementation._read_exact_output_set

        def racing_read_set(*args, **kwargs):
            nonlocal mutated
            if kwargs.get("expected_root_identity") is not None and not mutated:
                mutated = True
                _replace_exact6_directory(root, payloads)
            return original_read_set(*args, **kwargs)

        monkeypatch.setattr(
            implementation, "_read_exact_output_set", racing_read_set
        )
    with pytest.raises(ValueError):
        implementation.materialize_contract(root)
    assert mutated
    assert not list(tmp_path.glob(".*.staging"))


def test_materializer_does_not_delete_foreign_staging_after_eexist(
    tmp_path, monkeypatch, payloads
) -> None:
    root = tmp_path / "out"
    foreign_name = ""

    def concurrent_publish(
        staging_name: str,
        destination_name: str,
        parent_fd: int,
        staging_fd: int,
        staging_identity: tuple[int, ...],
    ) -> None:
        nonlocal foreign_name
        _write_exact6(root, payloads)
        os.rename(
            staging_name,
            "owned-staging-moved",
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
        )
        os.mkdir(staging_name, dir_fd=parent_fd)
        foreign_name = staging_name
        foreign_fd = os.open(
            staging_name,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
            dir_fd=parent_fd,
        )
        try:
            marker = os.open(
                "foreign.marker",
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
                dir_fd=foreign_fd,
            )
            os.close(marker)
        finally:
            os.close(foreign_fd)
        raise OSError(errno.EEXIST, "concurrent publish")

    monkeypatch.setattr(
        implementation, "_rename_noreplace", concurrent_publish
    )
    with pytest.raises(RuntimeError, match="failure staging retained"):
        implementation.materialize_contract(root)
    assert foreign_name
    assert (tmp_path / foreign_name / "foreign.marker").is_file()


def test_staging_lexical_replacement_rejects_foreign_publish(
    tmp_path, monkeypatch
) -> None:
    root = tmp_path / "out"
    original_rename = implementation._rename_noreplace
    replacement_observed = False
    unlink_called = False
    rmdir_called = False

    def forbidden_cdll(*args, **kwargs):
        raise AssertionError("rename syscall reached after staging replacement")

    def forbidden_unlink(*args, **kwargs):
        nonlocal unlink_called
        unlink_called = True
        raise AssertionError("unlink forbidden")

    def forbidden_rmdir(*args, **kwargs):
        nonlocal rmdir_called
        rmdir_called = True
        raise AssertionError("rmdir forbidden")

    def replace_before_rename(
        staging_name: str,
        destination_name: str,
        parent_fd: int,
        staging_fd: int,
        staging_identity: tuple[int, ...],
    ) -> None:
        nonlocal replacement_observed
        replacement_observed = True
        os.rename(
            staging_name,
            "owned-away",
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
        )
        os.mkdir(staging_name, dir_fd=parent_fd)
        foreign_fd = os.open(
            staging_name,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
            dir_fd=parent_fd,
        )
        try:
            marker_fd = os.open(
                "foreign.marker",
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
                dir_fd=foreign_fd,
            )
            try:
                os.write(marker_fd, b"foreign bytes\n")
            finally:
                os.close(marker_fd)
        finally:
            os.close(foreign_fd)
        original_rename(
            staging_name,
            destination_name,
            parent_fd,
            staging_fd,
            staging_identity,
        )

    monkeypatch.setattr(
        implementation,
        "_rename_noreplace",
        replace_before_rename,
    )
    monkeypatch.setattr(implementation.ctypes, "CDLL", forbidden_cdll)
    monkeypatch.setattr(implementation.os, "unlink", forbidden_unlink)
    monkeypatch.setattr(implementation.os, "rmdir", forbidden_rmdir)
    with pytest.raises(RuntimeError, match="failure staging retained") as caught:
        implementation.materialize_contract(root)
    assert isinstance(caught.value.__cause__, ValueError)
    assert "staging lexical/FD ownership mismatch" in str(
        caught.value.__cause__
    )
    assert replacement_observed is True
    assert root.exists() is False
    assert (tmp_path / "owned-away").is_dir()
    assert {path.name for path in (tmp_path / "owned-away").iterdir()} == set(
        implementation.OUTPUT_FILES
    )
    foreign = [
        path
        for path in tmp_path.iterdir()
        if path.name.startswith(".out.") and path.name.endswith(".staging")
    ]
    assert len(foreign) == 1
    assert (foreign[0] / "foreign.marker").read_bytes() == b"foreign bytes\n"
    assert unlink_called is False
    assert rmdir_called is False


@pytest.mark.parametrize(
    "race",
    [
        "leaf_replacement",
        "in_place_mutation",
        "parent_lexical_replacement",
        "repo_root_replacement",
    ],
)
def test_pinned_source_races_fail_closed(
    tmp_path, monkeypatch, race: str
) -> None:
    repo = tmp_path / "repo"
    source = repo / "evidence/source.txt"
    source.parent.mkdir(parents=True)
    source.write_text("frozen\n")
    monkeypatch.setattr(implementation, "REPO_ROOT", repo)
    original_read = implementation.os.read
    mutated = False

    def racing_read(descriptor: int, size: int) -> bytes:
        nonlocal mutated
        data = original_read(descriptor, size)
        if data and not mutated:
            mutated = True
            if race == "leaf_replacement":
                replacement = source.with_name("replacement")
                replacement.write_bytes(source.read_bytes())
                os.rename(replacement, source)
            elif race == "in_place_mutation":
                with source.open("ab") as stream:
                    stream.write(b"x")
            elif race == "parent_lexical_replacement":
                old = repo / "evidence-old"
                os.rename(source.parent, old)
                source.parent.mkdir()
                source.write_text("frozen\n")
            else:
                old = repo.with_name("repo-old")
                os.rename(repo, old)
                source.parent.mkdir(parents=True)
                source.write_text("frozen\n")
        return data

    monkeypatch.setattr(implementation.os, "read", racing_read)
    with pytest.raises(ValueError):
        implementation._pinned_read_relative(Path("evidence/source.txt"))
    assert mutated


def test_pinned_source_parent_stat_open_race_fails_closed(
    tmp_path, monkeypatch
) -> None:
    repo = tmp_path / "repo"
    source = repo / "evidence/source.txt"
    source.parent.mkdir(parents=True)
    source.write_text("frozen\n")
    monkeypatch.setattr(implementation, "REPO_ROOT", repo)
    original_open = implementation.os.open
    mutated = False

    def racing_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal mutated
        if path == "evidence" and dir_fd is not None and not mutated:
            mutated = True
            os.rename(source.parent, repo / "evidence-old")
            source.parent.mkdir()
            source.write_text("frozen\n")
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(implementation.os, "open", racing_open)
    with pytest.raises(ValueError, match="source parent stat/open race"):
        implementation._pinned_read_relative(Path("evidence/source.txt"))
    assert mutated


def _exercise_real_late_source_leaf_replacement(
    module,
    reader,
    repo: Path,
    monkeypatch,
) -> None:
    source = repo / "a/b/source.txt"
    source.parent.mkdir(parents=True)
    old_bytes = b"old bytes\n"
    new_bytes = b"new bytes\n"
    source.write_bytes(old_bytes)
    original_read = module.os.read
    original_stat = module.os.stat
    original_fstat = module.os.fstat
    stable_items = {
        (item.st_dev, item.st_ino): item
        for item in (
            original_stat(repo),
            original_stat(repo / "a"),
            original_stat(repo / "a/b"),
            original_stat(source),
        )
    }
    read_complete = False
    replaced = False

    def stable(item: os.stat_result) -> os.stat_result:
        return stable_items.get((item.st_dev, item.st_ino), item)

    def racing_read(descriptor: int, size: int) -> bytes:
        nonlocal read_complete
        data = original_read(descriptor, size)
        if data == b"":
            read_complete = True
        return data

    def racing_fstat(descriptor: int) -> os.stat_result:
        return stable(original_fstat(descriptor))

    def racing_stat(
        path,
        *,
        dir_fd=None,
        follow_symlinks=True,
    ) -> os.stat_result:
        nonlocal replaced
        item = original_stat(
            path,
            dir_fd=dir_fd,
            follow_symlinks=follow_symlinks,
        )
        if (
            read_complete
            and not replaced
            and path == "source.txt"
            and dir_fd is not None
            and follow_symlinks is False
        ):
            replaced = True
            os.rename(source, source.with_name("source.old"))
            source.write_bytes(new_bytes)
        return stable(item)

    old_inode = original_stat(source).st_ino
    monkeypatch.setattr(module.os, "read", racing_read)
    monkeypatch.setattr(module.os, "fstat", racing_fstat)
    monkeypatch.setattr(module.os, "stat", racing_stat)
    with pytest.raises(ValueError, match="final lexical"):
        reader()
    new_inode = original_stat(source).st_ino
    assert replaced is True
    assert source.read_bytes() == new_bytes
    assert source.with_name("source.old").read_bytes() == old_bytes
    assert old_inode != new_inode


def test_production_real_late_source_leaf_replacement_fails_closed(
    tmp_path, monkeypatch
) -> None:
    repo = tmp_path / "production-repo"
    monkeypatch.setattr(implementation, "REPO_ROOT", repo)
    _exercise_real_late_source_leaf_replacement(
        implementation,
        lambda: implementation._pinned_read_relative(
            Path("a/b/source.txt")
        ),
        repo,
        monkeypatch,
    )


def test_checker_real_late_source_leaf_replacement_fails_closed(
    tmp_path, monkeypatch
) -> None:
    checker = _load_checker()
    repo = tmp_path / "checker-repo"
    _exercise_real_late_source_leaf_replacement(
        checker,
        lambda: checker._read_regular(Path("a/b/source.txt"), repo),
        repo,
        monkeypatch,
    )


@pytest.mark.parametrize(
    "race",
    [
        "leaf_replacement",
        "in_place_mutation",
        "parent_lexical_replacement",
        "repo_root_replacement",
    ],
)
def test_checker_pinned_source_races_fail_closed(
    tmp_path, monkeypatch, race: str
) -> None:
    checker = _load_checker()
    repo = tmp_path / "repo"
    source = repo / "evidence/source.txt"
    source.parent.mkdir(parents=True)
    source.write_text("frozen\n")
    original_read = checker.os.read
    mutated = False

    def racing_read(descriptor: int, size: int) -> bytes:
        nonlocal mutated
        data = original_read(descriptor, size)
        if data and not mutated:
            mutated = True
            if race == "leaf_replacement":
                replacement = source.with_name("replacement")
                replacement.write_bytes(source.read_bytes())
                os.rename(replacement, source)
            elif race == "in_place_mutation":
                with source.open("ab") as stream:
                    stream.write(b"x")
            elif race == "parent_lexical_replacement":
                os.rename(source.parent, repo / "evidence-old")
                source.parent.mkdir()
                source.write_text("frozen\n")
            else:
                os.rename(repo, repo.with_name("repo-old"))
                source.parent.mkdir(parents=True)
                source.write_text("frozen\n")
        return data

    monkeypatch.setattr(checker.os, "read", racing_read)
    with pytest.raises(ValueError):
        checker._read_regular(Path("evidence/source.txt"), repo)
    assert mutated


def test_checker_pinned_source_parent_stat_open_race_fails_closed(
    tmp_path, monkeypatch
) -> None:
    checker = _load_checker()
    repo = tmp_path / "repo"
    source = repo / "evidence/source.txt"
    source.parent.mkdir(parents=True)
    source.write_text("frozen\n")
    original_open = checker.os.open
    mutated = False

    def racing_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal mutated
        if path == "evidence" and dir_fd is not None and not mutated:
            mutated = True
            os.rename(source.parent, repo / "evidence-old")
            source.parent.mkdir()
            source.write_text("frozen\n")
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(checker.os, "open", racing_open)
    with pytest.raises(ValueError, match="source parent stat/open race"):
        checker._read_regular(Path("evidence/source.txt"), repo)
    assert mutated


@pytest.mark.parametrize(
    "race",
    [
        "leaf_replacement",
        "root_replacement",
        "final_extra",
        "final_missing",
        "parent_replacement",
    ],
)
def test_checker_pinned_output_races_fail_closed(
    tmp_path, monkeypatch, payloads, race: str
) -> None:
    checker = _load_checker()
    parent = tmp_path / "parent"
    root = parent / "out"
    _write_exact6(root, payloads)
    original_read = checker.os.read
    original_listdir = checker.os.listdir
    mutated = False
    inventory_count = 0

    def racing_read(descriptor: int, size: int) -> bytes:
        nonlocal mutated
        data = original_read(descriptor, size)
        if data and not mutated and race in {
            "leaf_replacement",
            "root_replacement",
            "parent_replacement",
        }:
            mutated = True
            if race == "leaf_replacement":
                leaf = root / implementation.CONTRACT_FILE
                replacement = root / "replacement"
                replacement.write_bytes(leaf.read_bytes())
                os.rename(replacement, leaf)
            elif race == "root_replacement":
                _replace_exact6_directory(root, payloads)
            else:
                os.rename(parent, parent.with_name("parent-displaced"))
                _write_exact6(root, payloads)
        return data

    def racing_listdir(path) -> list[str]:
        nonlocal inventory_count, mutated
        inventory_count += 1
        if inventory_count == 2 and race in {"final_extra", "final_missing"}:
            mutated = True
            if race == "final_extra":
                (root / "seventh.csv").write_bytes(b"extra\n")
            else:
                (root / implementation.ISSUE_FILE).unlink()
        return original_listdir(path)

    monkeypatch.setattr(checker.os, "read", racing_read)
    monkeypatch.setattr(checker.os, "listdir", racing_listdir)
    with pytest.raises(ValueError):
        checker._read_outputs(root)
    assert mutated


def test_checker_pinned_output_normal_read(tmp_path, payloads) -> None:
    checker = _load_checker()
    root = tmp_path / "out"
    _write_exact6(root, payloads)
    assert checker._read_outputs(root) == payloads


def _exercise_real_late_output_leaf_replacement(
    module,
    reader,
    root: Path,
    payloads: dict[str, bytes],
    monkeypatch,
) -> None:
    _write_exact6(root, payloads)
    target_name = implementation.CONTRACT_FILE
    target = root / target_name
    displaced = root.parent / f"{target_name}.old"
    old_bytes = target.read_bytes()
    new_bytes = b"new output leaf bytes\n"
    original_read = module.os.read
    original_stat = module.os.stat
    original_fstat = module.os.fstat
    original_lstat = module.os.lstat
    stable_directories = {
        (item.st_dev, item.st_ino): item
        for item in (
            original_stat(root.parent),
            original_stat(root),
        )
    }
    eof_count = 0
    replaced = False

    def stable_directory(item: os.stat_result) -> os.stat_result:
        return stable_directories.get((item.st_dev, item.st_ino), item)

    def racing_read(descriptor: int, size: int) -> bytes:
        nonlocal eof_count
        data = original_read(descriptor, size)
        if data == b"":
            eof_count += 1
        return data

    def racing_fstat(descriptor: int) -> os.stat_result:
        return stable_directory(original_fstat(descriptor))

    def racing_lstat(path) -> os.stat_result:
        return stable_directory(original_lstat(path))

    def racing_stat(
        path,
        *,
        dir_fd=None,
        follow_symlinks=True,
    ) -> os.stat_result:
        nonlocal replaced
        item = original_stat(
            path,
            dir_fd=dir_fd,
            follow_symlinks=follow_symlinks,
        )
        if (
            eof_count == len(implementation.OUTPUT_FILES)
            and not replaced
            and path == target_name
            and dir_fd is not None
            and follow_symlinks is False
        ):
            replaced = True
            os.rename(target, displaced)
            target.write_bytes(new_bytes)
        return stable_directory(item)

    old_inode = original_stat(target).st_ino
    monkeypatch.setattr(module.os, "read", racing_read)
    monkeypatch.setattr(module.os, "fstat", racing_fstat)
    monkeypatch.setattr(module.os, "lstat", racing_lstat)
    monkeypatch.setattr(module.os, "stat", racing_stat)
    with pytest.raises(ValueError, match="final leaf"):
        reader()
    new_inode = original_stat(target).st_ino
    assert replaced is True
    assert target.read_bytes() == new_bytes
    assert displaced.read_bytes() == old_bytes
    assert old_inode != new_inode


def test_production_real_late_output_leaf_replacement_fails_closed(
    tmp_path, payloads, monkeypatch
) -> None:
    root = tmp_path / "production" / "out"
    _exercise_real_late_output_leaf_replacement(
        implementation,
        lambda: implementation._read_exact_output_set(root, payloads),
        root,
        payloads,
        monkeypatch,
    )


def test_checker_real_late_output_leaf_replacement_fails_closed(
    tmp_path, payloads, monkeypatch
) -> None:
    checker = _load_checker()
    root = tmp_path / "checker" / "out"
    _exercise_real_late_output_leaf_replacement(
        checker,
        lambda: checker._read_outputs(root),
        root,
        payloads,
        monkeypatch,
    )


def test_checker_manifest_duplicate_missing_extra_reorder(payloads) -> None:
    checker = _load_checker()
    text = payloads[implementation.MANIFEST_FILE].decode()
    duplicate = text.replace(
        '{\n  "Admit015EvaluationResult_implemented"',
        '{\n  "project": "duplicate",\n'
        '  "project": "duplicate2",\n'
        '  "Admit015EvaluationResult_implemented"',
        1,
    )
    with pytest.raises(ValueError, match="duplicate manifest key"):
        checker._parse_manifest_exact(duplicate.encode())
    for case in ("missing", "extra", "reorder"):
        value = json.loads(text)
        if case == "missing":
            value.pop("project")
        elif case == "extra":
            value["unexpected"] = True
        else:
            value = dict(reversed(tuple(value.items())))
        tampered = (json.dumps(value, indent=2) + "\n").encode()
        with pytest.raises(
            ValueError, match="manifest top-level schema/order drift"
        ):
            checker._parse_manifest_exact(tampered)


@pytest.mark.parametrize(
    "name",
    [
        "readiness",
        "safety",
        "materialization_policy",
        "output_sha256",
        "precondition_transition",
        "mapping_consumption_contract",
        "row_counts",
        "formal_ast_sha256",
    ],
)
@pytest.mark.parametrize("case", ["missing", "extra", "reorder"])
def test_checker_manifest_nested_exact_schema_rejected(
    payloads, name: str, case: str
) -> None:
    checker = _load_checker()
    manifest = json.loads(payloads[implementation.MANIFEST_FILE])
    nested = manifest[name]
    if case == "missing":
        nested.pop(next(iter(nested)))
    elif case == "extra":
        nested["unexpected"] = True
    else:
        manifest[name] = dict(reversed(tuple(nested.items())))
    tampered = (json.dumps(manifest, indent=2) + "\n").encode()
    with pytest.raises(ValueError, match="manifest nested schema/order drift"):
        checker._parse_manifest_exact(tampered)


@pytest.mark.parametrize("case", ["missing", "extra", "reorder"])
def test_checker_manifest_source_entry_exact_schema_rejected(
    payloads, case: str
) -> None:
    checker = _load_checker()
    manifest = json.loads(payloads[implementation.MANIFEST_FILE])
    entry = manifest["source_boundary"][0]
    if case == "missing":
        entry.pop("base_tree_blob")
    elif case == "extra":
        entry["unexpected"] = True
    else:
        manifest["source_boundary"][0] = dict(
            reversed(tuple(entry.items()))
        )
    tampered = (json.dumps(manifest, indent=2) + "\n").encode()
    with pytest.raises(
        ValueError, match="manifest source_boundary schema/order drift"
    ):
        checker._parse_manifest_exact(tampered)


@pytest.mark.parametrize(
    "case", ["readiness_value", "policy_value", "source_blob"]
)
def test_checker_manifest_semantic_drift_rejected(
    payloads, snapshot, monkeypatch, case: str
) -> None:
    checker = _load_checker()
    outputs = dict(payloads)
    manifest = json.loads(outputs[implementation.MANIFEST_FILE])
    if case == "readiness_value":
        manifest["readiness"][
            "admit_015_standalone_evaluator_implemented"
        ] = False
    elif case == "policy_value":
        manifest["materialization_policy"]["parent_fd_pinned"] = False
    else:
        manifest["source_boundary"][0]["base_tree_blob"] = "0" * 40
    outputs[implementation.MANIFEST_FILE] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode()
    monkeypatch.setitem(
        checker.EXPECTED_OUTPUT_SHA256,
        implementation.MANIFEST_FILE,
        hashlib.sha256(outputs[implementation.MANIFEST_FILE]).hexdigest(),
    )
    sources = {record.path: record.content for record in snapshot}
    _, _, _, ast_digests = implementation._formal_source_attestation()
    with pytest.raises(ValueError):
        checker._check_output_semantics(
            outputs,
            sources,
            ast_digests,
            implementation,
        )


def test_checker_full_csv_rebuilders_match_every_artifact_field(
    payloads,
    snapshot,
) -> None:
    checker = _load_checker()
    sources = {record.path: record.content for record in snapshot}
    _, full_sha, prefix_sha, ast_digests = (
        implementation._formal_source_attestation()
    )
    contract = list(
        csv.DictReader(
            io.StringIO(payloads[implementation.CONTRACT_FILE].decode())
        )
    )
    truth = list(
        csv.DictReader(
            io.StringIO(payloads[implementation.TRUTH_FILE].decode())
        )
    )
    purity = list(
        csv.DictReader(
            io.StringIO(payloads[implementation.PURITY_FILE].decode())
        )
    )
    committed_formal_truth = list(
        csv.DictReader(
            io.StringIO(
                sources[
                    implementation.FORMAL_DESIGN_ROOT
                    / "covapie_admit_015_formal_evaluator_interface_truth_matrix.csv"
                ].decode()
            )
        )
    )
    assert contract == checker._expected_contract_rows(ast_digests)
    assert truth == checker._expected_truth_rows(
        committed_formal_truth,
        implementation,
    )
    assert purity == checker._expected_purity_rows(
        full_sha,
        prefix_sha,
        ast_digests,
    )
    assert (
        len(contract),
        len(tuple(contract[0])),
        len(truth),
        len(tuple(truth[0])),
        len(purity),
        len(tuple(purity[0])),
    ) == (37, 10, 61, 12, 16, 13)


SYNCHRONIZED_TAMPER_CASES = (
    "manifest_public_evaluator",
    "manifest_result_type",
    "manifest_parameter_count_bool",
    "manifest_formal_marker",
    "manifest_formal_ast_value",
    "manifest_add_sixth_mask",
    "manifest_delete_b3",
    "manifest_feature_semantics_known",
    "manifest_unknown_atom_resolved",
    "manifest_step12d_status",
    "manifest_current_permission_int",
    "manifest_execution_count_bool",
    "manifest_readiness_bool_int",
    "source_blob",
    "source_path",
    "source_stage",
    "manifest_materialization_flag",
    "manifest_output_file_reorder",
    "manifest_recommended_next_step",
    "manifest_top_extra",
    "manifest_top_missing",
    "manifest_top_reorder",
    "manifest_nested_extra",
    "manifest_nested_missing",
    "manifest_nested_reorder",
    "contract_semantics",
    "truth_semantics",
    "purity_semantics",
    "issue_semantics",
    "contract_field_public_name",
    "contract_field_formal_type",
    "contract_field_formal_invariant",
    "contract_field_frozen_value",
    "contract_field_implementation_source",
    "contract_field_contract_section",
    "contract_field_section_order",
    "truth_field_case_id",
    "truth_field_case_group",
    "truth_field_assertion_kind",
    "truth_field_inherited_case_id",
    "truth_field_stage_context_representation",
    "truth_field_expected_design_result",
    "truth_field_observed_formal_result",
    "truth_field_formal_source",
    "purity_field_definition_kind",
    "purity_field_reachable_from",
    "purity_field_permitted_global_bindings",
    "purity_field_permitted_calls",
    "purity_field_observed",
    "purity_field_forbidden_io_absent",
    "purity_field_mutation_absent",
    "purity_field_dynamic_dispatch_absent",
    "purity_field_normalized_ast_sha256",
    "purity_field_audit_kind",
)

CONTRACT_FIELD_TAMPERS = {
    "contract_field_public_name": (
        "public_name",
        "tampered_stage_authorization_context",
    ),
    "contract_field_formal_type": ("formal_type", "str"),
    "contract_field_formal_invariant": (
        "formal_invariant",
        "tampered invariant",
    ),
    "contract_field_frozen_value": ("frozen_value", "tampered"),
    "contract_field_implementation_source": (
        "implementation_source",
        "tampered_source",
    ),
    "contract_field_contract_section": (
        "contract_section",
        "tampered_section",
    ),
    "contract_field_section_order": ("section_order", "2"),
}
TRUTH_FIELD_TAMPERS = {
    "truth_field_case_id": ("case_id", "OMITTED_TAMPERED"),
    "truth_field_case_group": ("case_group", "tampered_group"),
    "truth_field_assertion_kind": (
        "assertion_kind",
        "tampered_assertion",
    ),
    "truth_field_inherited_case_id": (
        "inherited_case_id",
        "OMITTED_TAMPERED",
    ),
    "truth_field_stage_context_representation": (
        "stage_context_representation",
        "<TAMPERED>",
    ),
    "truth_field_expected_design_result": (
        "expected_design_result",
        "tampered expected result",
    ),
    "truth_field_observed_formal_result": (
        "observed_formal_result",
        "tampered observed result",
    ),
    "truth_field_formal_source": ("formal_source", "tampered_source"),
}
PURITY_FIELD_TAMPERS = {
    "purity_field_definition_kind": (
        "definition_kind",
        "tampered_kind",
    ),
    "purity_field_reachable_from": (
        "reachable_from",
        "tampered_parent",
    ),
    "purity_field_permitted_global_bindings": (
        "permitted_global_bindings",
        "tampered_globals",
    ),
    "purity_field_permitted_calls": (
        "permitted_calls",
        "tampered_calls",
    ),
    "purity_field_observed": ("observed", "tampered_observation"),
    "purity_field_forbidden_io_absent": (
        "forbidden_io_absent",
        "false",
    ),
    "purity_field_mutation_absent": ("mutation_absent", "false"),
    "purity_field_dynamic_dispatch_absent": (
        "dynamic_dispatch_absent",
        "false",
    ),
    "purity_field_normalized_ast_sha256": (
        "normalized_ast_sha256",
        "0" * 64,
    ),
    "purity_field_audit_kind": ("audit_kind", "tampered_audit"),
}


def _mutate_csv(
    data: bytes,
    mutate,
) -> bytes:
    reader = csv.DictReader(io.StringIO(data.decode(), newline=""))
    fieldnames = tuple(reader.fieldnames or ())
    rows = list(reader)
    mutate(rows)
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=fieldnames,
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def _apply_synchronized_tamper(
    outputs: dict[str, bytes],
    case: str,
) -> None:
    manifest = json.loads(outputs[implementation.MANIFEST_FILE])
    if case in CONTRACT_FIELD_TAMPERS:
        field, value = CONTRACT_FIELD_TAMPERS[case]
        outputs[implementation.CONTRACT_FILE] = _mutate_csv(
            outputs[implementation.CONTRACT_FILE],
            lambda rows: rows[0].__setitem__(field, value),
        )
    elif case in TRUTH_FIELD_TAMPERS:
        field, value = TRUTH_FIELD_TAMPERS[case]
        outputs[implementation.TRUTH_FILE] = _mutate_csv(
            outputs[implementation.TRUTH_FILE],
            lambda rows: rows[0].__setitem__(field, value),
        )
    elif case in PURITY_FIELD_TAMPERS:
        field, value = PURITY_FIELD_TAMPERS[case]
        outputs[implementation.PURITY_FILE] = _mutate_csv(
            outputs[implementation.PURITY_FILE],
            lambda rows: rows[0].__setitem__(field, value),
        )
    elif case == "source_blob":
        outputs[implementation.SOURCE_FILE] = _mutate_csv(
            outputs[implementation.SOURCE_FILE],
            lambda rows: rows[0].__setitem__("base_tree_blob", "0" * 40),
        )
    elif case == "source_path":
        outputs[implementation.SOURCE_FILE] = _mutate_csv(
            outputs[implementation.SOURCE_FILE],
            lambda rows: rows[0].__setitem__(
                "source_relative_path", "src/tampered.py"
            ),
        )
    elif case == "source_stage":
        outputs[implementation.SOURCE_FILE] = _mutate_csv(
            outputs[implementation.SOURCE_FILE],
            lambda rows: rows[0].__setitem__("index_stage_zero", "false"),
        )
    elif case == "contract_semantics":
        outputs[implementation.CONTRACT_FILE] = _mutate_csv(
            outputs[implementation.CONTRACT_FILE],
            lambda rows: rows[0].__setitem__("contract_passed", "false"),
        )
    elif case == "truth_semantics":
        outputs[implementation.TRUTH_FILE] = _mutate_csv(
            outputs[implementation.TRUTH_FILE],
            lambda rows: rows[0].__setitem__("truth_passed", "false"),
        )
    elif case == "purity_semantics":
        outputs[implementation.PURITY_FILE] = _mutate_csv(
            outputs[implementation.PURITY_FILE],
            lambda rows: rows[0].__setitem__("purity_passed", "false"),
        )
    elif case == "issue_semantics":
        outputs[implementation.ISSUE_FILE] = _mutate_csv(
            outputs[implementation.ISSUE_FILE],
            lambda rows: rows[0].__setitem__(
                "affected_rules", "ADMIT_014"
            ),
        )
    manifest["output_sha256"] = {
        name: hashlib.sha256(outputs[name]).hexdigest()
        for name in implementation.OUTPUT_FILES[:-1]
    }
    preserve_order = False
    if case == "manifest_public_evaluator":
        manifest["public_evaluator"] = "evaluate_admit_015_tampered"
    elif case == "manifest_result_type":
        manifest["result_type"] = "TamperedResult"
    elif case == "manifest_parameter_count_bool":
        manifest["parameter_count"] = True
    elif case == "manifest_formal_marker":
        manifest["formal_marker"] = "# tampered marker"
    elif case == "manifest_formal_ast_value":
        manifest["formal_ast_sha256"]["evaluate_admit_015"] = "0" * 64
    elif case == "manifest_add_sixth_mask":
        manifest["canonical_masks"].append(
            {"semantic_name": "forbidden_sixth", "alias": "D"}
        )
        manifest["canonical_mask_count"] = 6
    elif case == "manifest_delete_b3":
        manifest["canonical_masks"] = [
            item
            for item in manifest["canonical_masks"]
            if item["alias"] != "B3"
        ]
        manifest["canonical_mask_count"] = 4
    elif case == "manifest_feature_semantics_known":
        manifest["historical_feature_semantics_known"] = True
    elif case == "manifest_unknown_atom_resolved":
        manifest["historical_unknown_atom_feature_policy_resolved"] = True
    elif case == "manifest_step12d_status":
        manifest["step12d_status"] = "final_training_feature_contract"
    elif case == "manifest_current_permission_int":
        manifest["current_permission"] = 0
    elif case == "manifest_execution_count_bool":
        manifest["authorized_admit_015_training_execution_count"] = False
    elif case == "manifest_readiness_bool_int":
        manifest["readiness"]["evaluate_admit_015_implemented"] = 1
    elif case == "manifest_materialization_flag":
        manifest["materialization_policy"][
            "staging_lexical_binding_verified"
        ] = False
    elif case == "manifest_output_file_reorder":
        manifest["output_files"][0:2] = reversed(
            manifest["output_files"][0:2]
        )
    elif case == "manifest_recommended_next_step":
        manifest["recommended_next_step"] = "train_now"
    elif case == "manifest_top_extra":
        manifest["unexpected"] = True
    elif case == "manifest_top_missing":
        manifest.pop("project")
    elif case == "manifest_top_reorder":
        manifest = dict(reversed(tuple(manifest.items())))
        preserve_order = True
    elif case == "manifest_nested_extra":
        manifest["materialization_policy"]["unexpected"] = True
    elif case == "manifest_nested_missing":
        manifest["materialization_policy"].pop("parent_fd_pinned")
    elif case == "manifest_nested_reorder":
        nested = manifest["materialization_policy"]
        manifest["materialization_policy"] = dict(
            reversed(tuple(nested.items()))
        )
        preserve_order = True
    outputs[implementation.MANIFEST_FILE] = (
        json.dumps(
            manifest,
            indent=2,
            sort_keys=not preserve_order,
        )
        + "\n"
    ).encode()


@pytest.mark.parametrize("case", SYNCHRONIZED_TAMPER_CASES)
def test_checker_synchronized_tamper_rejected(
    payloads, snapshot, monkeypatch, case: str
) -> None:
    checker = _load_checker()
    sources = {record.path: record.content for record in snapshot}
    _, _, _, ast_digests = implementation._formal_source_attestation()
    outputs = dict(payloads)
    _apply_synchronized_tamper(outputs, case)
    frozen = {
        name: hashlib.sha256(outputs[name]).hexdigest()
        for name in implementation.OUTPUT_FILES
    }
    monkeypatch.setattr(checker, "EXPECTED_OUTPUT_SHA256", frozen)
    assert json.loads(outputs[implementation.MANIFEST_FILE]).get(
        "output_sha256"
    ) == {name: frozen[name] for name in implementation.OUTPUT_FILES[:-1]}
    with pytest.raises(ValueError) as captured:
        checker._check_output_semantics(
            outputs,
            sources,
            ast_digests,
            implementation,
        )
    assert "frozen output SHA drift" not in str(captured.value)
    if case.startswith("contract_field_") or case == "contract_semantics":
        assert "Contract Exact37x10" in str(captured.value)
    elif case.startswith("truth_field_") or case == "truth_semantics":
        assert "Truth Exact61x12" in str(captured.value)
    elif case.startswith("purity_field_") or case == "purity_semantics":
        assert "Purity Exact16x13" in str(captured.value)


def test_legacy_aggregate_csv_checks_allow_three_synchronized_bypasses(
    payloads, snapshot, monkeypatch
) -> None:
    checker = _load_checker()
    outputs = dict(payloads)
    outputs[implementation.CONTRACT_FILE] = _mutate_csv(
        outputs[implementation.CONTRACT_FILE],
        lambda rows: rows[0].__setitem__("public_name", "tampered_name"),
    )
    outputs[implementation.TRUTH_FILE] = _mutate_csv(
        outputs[implementation.TRUTH_FILE],
        lambda rows: rows[0].__setitem__("case_id", "OMITTED_TAMPERED"),
    )
    outputs[implementation.PURITY_FILE] = _mutate_csv(
        outputs[implementation.PURITY_FILE],
        lambda rows: rows[0].__setitem__("forbidden_io_absent", "false"),
    )
    manifest = json.loads(outputs[implementation.MANIFEST_FILE])
    manifest["output_sha256"] = {
        name: hashlib.sha256(outputs[name]).hexdigest()
        for name in implementation.OUTPUT_FILES[:-1]
    }
    outputs[implementation.MANIFEST_FILE] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode()
    contract = list(
        csv.DictReader(
            io.StringIO(outputs[implementation.CONTRACT_FILE].decode())
        )
    )
    truth = list(
        csv.DictReader(
            io.StringIO(outputs[implementation.TRUTH_FILE].decode())
        )
    )
    purity = list(
        csv.DictReader(
            io.StringIO(outputs[implementation.PURITY_FILE].decode())
        )
    )
    legacy_aggregate_accepts = (
        all(row["contract_passed"] == "true" for row in contract)
        and len(truth) == 61
        and [row["case_order"] for row in truth]
        == [str(index) for index in range(1, 62)]
        and all(
            row["exact_type_value_equality"] == "true"
            and row["evaluator_io_used"] == "false"
            and row["truth_passed"] == "true"
            for row in truth
        )
        and sum(
            row["case_group"] != "negative_result_contract"
            for row in truth
        )
        == 37
        and sum(
            row["case_group"] == "negative_result_contract"
            for row in truth
        )
        == 24
        and len(purity) == 16
        and [row["definition_name"] for row in purity[:7]]
        == list(checker.FORMAL_CLOSURE)
        and [row["normalized_ast_sha256"] for row in purity[:7]]
        == [
            checker.EXPECTED_AST_SHA256[name]
            for name in checker.FORMAL_CLOSURE
        ]
        and all(row["purity_passed"] == "true" for row in purity)
    )
    assert legacy_aggregate_accepts is True
    frozen = {
        name: hashlib.sha256(outputs[name]).hexdigest()
        for name in implementation.OUTPUT_FILES
    }
    monkeypatch.setattr(checker, "EXPECTED_OUTPUT_SHA256", frozen)
    sources = {record.path: record.content for record in snapshot}
    _, _, _, ast_digests = implementation._formal_source_attestation()
    with pytest.raises(
        ValueError,
        match="Contract Exact37x10 full semantic rebuild drift",
    ) as captured:
        checker._check_output_semantics(
            outputs,
            sources,
            ast_digests,
            implementation,
        )
    assert "frozen output SHA drift" not in str(captured.value)


def test_checker_passes_and_isolated_imports_silent(tmp_path) -> None:
    result = subprocess.run(
        [sys.executable, str(CHECKER_PATH)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == ""
    report = json.loads(result.stdout)
    assert report["truth_rows"] == 61
    assert report["actual_independent_oracle_rows"] == 37
    assert report["negative_result_rows"] == 24
    assert report["lifecycle"] in {"pre_commit", "post_commit"}
    for path in (
        ROOT / implementation.__file__,
        CHECKER_PATH,
        Path(__file__),
    ):
        actual = Path(path)
        code = (
            "import importlib.util,sys;"
            f"s=importlib.util.spec_from_file_location('isolated',{str(actual)!r});"
            "m=importlib.util.module_from_spec(s);sys.modules['isolated']=m;"
            "s.loader.exec_module(m)"
        )
        isolated = subprocess.run(
            [sys.executable, "-B", "-c", code],
            cwd=tmp_path,
            env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            capture_output=True,
            text=True,
            check=False,
        )
        assert isolated.returncode == 0
        assert isolated.stdout == isolated.stderr == ""


def test_lifecycle_pre_post_and_fail_closed_states(tmp_path) -> None:
    checker = _load_checker()
    pre, base = _seed_lifecycle(tmp_path / "pre", checker)
    assert checker._lifecycle(pre, base) == "pre_commit"
    descendant, descendant_base = _seed_lifecycle(
        tmp_path / "descendant",
        checker,
        descendant=True,
    )
    assert (
        checker._lifecycle(descendant, descendant_base) == "pre_commit"
    )
    post, post_base = _seed_lifecycle(
        tmp_path / "post", checker, tracked=True
    )
    assert checker._lifecycle(post, post_base) == "post_commit"
    for case in (
        "mixed", "staged", "dirty", "missing", "ignored", "extra",
        "nested_docs",
        "nested_docs_ignored",
        "nested_docs_tracked",
        "nested_src",
        "nested_scripts",
        "nested_tests",
        "nested_symlink_directory",
        "nested_forbidden_suffix",
        "nested_oversized",
        "sibling_derived_root",
        "ignored_only_sibling_derived_root",
        "seventh", "symlink", "oversized", "base_nonancestor",
        "forbidden_suffix",
    ):
        repo, case_base = _seed_lifecycle(
            tmp_path / case, checker, tracked=case == "dirty"
        )
        paths = checker.STAGE_PATHS
        if case == "mixed":
            assert _git(repo, "add", "--", paths[0].as_posix()).returncode == 0
            _commit(repo, "one tracked")
        elif case == "staged":
            assert _git(repo, "add", "--", paths[0].as_posix()).returncode == 0
        elif case == "dirty":
            with (repo / paths[0]).open("a") as stream:
                stream.write("dirty\n")
        elif case == "missing":
            (repo / paths[0]).unlink()
        elif case == "ignored":
            (repo / ".gitignore").write_text(paths[0].as_posix() + "\n")
        elif case == "extra":
            (
                repo / "docs/extra_admit_015_standalone_evaluator_interface.md"
            ).write_text("extra\n")
        elif case in {
            "nested_docs",
            "nested_docs_ignored",
            "nested_docs_tracked",
        }:
            extra = (
                repo
                / "docs/nested/"
                "extra_admit_015_standalone_evaluator_interface.md"
            )
            extra.parent.mkdir()
            extra.write_text("nested bypass\n")
            if case == "nested_docs_ignored":
                (repo / ".gitignore").write_text(
                    extra.relative_to(repo).as_posix() + "\n"
                )
            elif case == "nested_docs_tracked":
                assert _git(
                    repo,
                    "add",
                    "--",
                    extra.relative_to(repo).as_posix(),
                ).returncode == 0
                _commit(repo, "tracked nested stage artifact")
        elif case in {"nested_src", "nested_scripts", "nested_tests"}:
            root_name = {
                "nested_src": "src/covalent_ext",
                "nested_scripts": "scripts",
                "nested_tests": "tests",
            }[case]
            extra = (
                repo
                / root_name
                / "nested/extra_admit_015_standalone_evaluator_interface.py"
            )
            extra.parent.mkdir(parents=True, exist_ok=True)
            extra.write_text("nested bypass\n")
        elif case == "nested_symlink_directory":
            real = repo / "real-directory"
            real.mkdir()
            nested = repo / "docs/nested"
            nested.mkdir()
            (nested / "linked-directory").symlink_to(
                real,
                target_is_directory=True,
            )
        elif case in {"nested_forbidden_suffix", "nested_oversized"}:
            suffix = ".pt" if case == "nested_forbidden_suffix" else ".md"
            extra = (
                repo
                / "docs/nested"
                / (
                    "extra_admit_015_standalone_evaluator_interface"
                    + suffix
                )
            )
            extra.parent.mkdir()
            extra.write_text("nested bypass\n")
            if case == "nested_oversized":
                os.truncate(extra, 101 * 1024 * 1024)
        elif case in {
            "sibling_derived_root",
            "ignored_only_sibling_derived_root",
        }:
            sibling = (
                repo
                / checker.OUTPUT_ROOT.parent
                / (checker.OUTPUT_ROOT.name + "_sibling")
            )
            sibling.mkdir()
            if case == "ignored_only_sibling_derived_root":
                (sibling / "ignored.txt").write_text("ignored\n")
                (repo / ".gitignore").write_text(
                    sibling.relative_to(repo).as_posix() + "/\n"
                )
        elif case == "seventh":
            (repo / checker.OUTPUT_ROOT / "seventh.csv").write_text("extra\n")
        elif case == "symlink":
            target = repo / paths[3]
            target.unlink()
            target.symlink_to(repo / "baseline.txt")
        elif case == "oversized":
            os.truncate(repo / paths[0], 101 * 1024 * 1024)
        elif case == "base_nonancestor":
            case_base = "0" * 40
        else:
            paths = (paths[0].with_suffix(".pt"), *paths[1:])
        with pytest.raises((FileNotFoundError, ValueError)):
            checker._lifecycle(repo, case_base, paths)


def test_recursive_lifecycle_rejects_old_top_glob_bypass(tmp_path) -> None:
    checker = _load_checker()
    repo, base = _seed_lifecycle(tmp_path / "old-glob-bypass", checker)
    extra = (
        repo
        / "docs/nested/extra_admit_015_standalone_evaluator_interface.md"
    )
    extra.parent.mkdir()
    extra.write_text("nested bypass\n")
    suffix = "admit_015_standalone_evaluator_interface"
    old_top_glob = {
        path.relative_to(repo)
        for directory in ("src/covalent_ext", "scripts", "tests", "docs")
        for path in (repo / directory).glob(f"*{suffix}*")
        if path.is_file() or path.is_symlink()
    }
    assert extra.relative_to(repo) not in old_top_glob
    assert old_top_glob == set(checker.STAGE_PATHS[:4])
    with pytest.raises(ValueError):
        checker._lifecycle(repo, base)


def test_lifecycle_tracked_clean_ignored_candidate_rejected(tmp_path) -> None:
    checker = _load_checker()
    repo, base = _seed_lifecycle(
        tmp_path / "tracked-ignored", checker, tracked=True
    )
    (repo / ".gitignore").write_text(
        checker.STAGE_PATHS[0].as_posix() + "\n"
    )
    with pytest.raises(ValueError, match="ignored candidate"):
        checker._lifecycle(repo, base)


def test_lifecycle_check_ignore_error_fails_closed(
    tmp_path, monkeypatch
) -> None:
    checker = _load_checker()
    repo, base = _seed_lifecycle(tmp_path / "ignore-error", checker)
    original_git = checker._git

    def failing_check_ignore(args, repo_root=checker.REPO_ROOT, **kwargs):
        if args and args[0] == "check-ignore":
            return subprocess.CompletedProcess(
                ["git", *args], 128, "", "simulated failure"
            )
        return original_git(args, repo_root, **kwargs)

    monkeypatch.setattr(checker, "_git", failing_check_ignore)
    with pytest.raises(ValueError, match="git check-ignore failed closed"):
        checker._lifecycle(repo, base)


def test_exact10_inventory_protected_forbidden_large_temp() -> None:
    checker = _load_checker()
    assert len(checker.STAGE_PATHS) == len(set(checker.STAGE_PATHS)) == 10
    assert not any((ROOT / path).is_symlink() for path in checker.STAGE_PATHS)
    assert not any(
        path.suffix in checker.FORBIDDEN_SUFFIXES
        for path in checker.STAGE_PATHS
    )
    assert not any(
        (ROOT / path).stat().st_size > 100 * 1024 * 1024
        for path in checker.STAGE_PATHS
    )
    checker._protected_paths()
