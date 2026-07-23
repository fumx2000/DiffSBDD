"""Targeted tests for the pure ADMIT_014 standalone evaluator."""

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
    covapie_bulk_download_admission_admit_014_formal_evaluator_interface_contract_design_gate
    as design,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_014_rule_logic_interface
    as implementation,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / (
    "scripts/"
    "check_covapie_bulk_download_admission_admit_014_rule_logic_interface_v1.py"
)
TRUTH_PATH = ROOT / implementation.FORMAL_DESIGN_ROOT / (
    "covapie_admit_014_formal_evaluator_interface_truth_matrix.csv"
)


def _load_checker():
    spec = importlib.util.spec_from_file_location(
        "_admit014_checker_test", CHECKER_PATH
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
    root: Path, checker, *, tracked: bool = False
) -> tuple[Path, str]:
    root.mkdir()
    assert _git(root, "init", "-q").returncode == 0
    (root / "baseline.txt").write_text("baseline\n")
    assert _git(root, "add", "--", "baseline.txt").returncode == 0
    _commit(root, "baseline")
    base = _git(root, "rev-parse", "HEAD").stdout.strip()
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
    assert implementation.evaluate_admit_014().reason == (
        "STAGE_AUTHORIZATION_CONTEXT_REQUIRED"
    )
    with pytest.raises(RuntimeError, match="noncanonical"):
        implementation.build_artifacts(snapshot=())


def test_exact12_source_order_sha_tracking_and_safety(
    snapshot, payloads
) -> None:
    assert len(snapshot) == 12
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
    assert len(audit) == 12
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
    signature = inspect.signature(implementation.evaluate_admit_014)
    assert tuple(signature.parameters) == ("stage_authorization_context",)
    parameter = signature.parameters["stage_authorization_context"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.annotation is object
    assert parameter.default is implementation._MISSING
    assert signature.return_annotation is implementation.Admit014EvaluationResult
    assert implementation._MISSING is implementation._MISSING
    assert type(implementation._MISSING).__name__ == "_MissingAdmit014Value"
    with pytest.raises(TypeError):
        implementation.evaluate_admit_014(object())
    with pytest.raises(TypeError):
        implementation.evaluate_admit_014(unknown=True)


def test_omitted_and_none_are_structured_blocked() -> None:
    for result in (
        implementation.evaluate_admit_014(),
        implementation.evaluate_admit_014(
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
    result = implementation.evaluate_admit_014(
        stage_authorization_context=value
    )
    assert result.reason == "STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID"
    assert result.canonical_stage_authorization_record == ()
    assert result.validated_stage_authorization_fields == ()
    assert result.consumed_stage_authorization_fields == ()


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (KeyError("target"), "CURRENT_STAGE_DOWNLOAD_AUTHORIZED_MISSING"),
        (RuntimeError("boom"), "STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED"),
        (ValueError("boom"), "STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED"),
    ],
)
def test_lookup_failures_consume_target_once(
    error: BaseException, reason: str
) -> None:
    probe = Probe(error=error)
    result = implementation.evaluate_admit_014(
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
    result = implementation.evaluate_admit_014(
        stage_authorization_context=probe
    )
    assert result.reason == "CURRENT_STAGE_DOWNLOAD_AUTHORIZED_TYPE_INVALID"
    assert result.validated_stage_authorization_fields == ()
    assert result.consumed_stage_authorization_fields == (
        implementation.AUTHORIZATION_CONTEXT_ITEM,
    )
    assert probe.item_keys == [implementation.AUTHORIZATION_CONTEXT_ITEM]


@pytest.mark.parametrize("permission", [False, True])
def test_exact_bool_and_admit015_coexistence(permission: bool) -> None:
    probe = Probe(
        {
            implementation.ADMIT_015_CONTEXT_ITEM: not permission,
            "extra": object(),
            implementation.AUTHORIZATION_CONTEXT_ITEM: permission,
        }
    )
    result = implementation.evaluate_admit_014(
        stage_authorization_context=probe
    )
    assert result.outcome == ("passed" if permission else "blocked")
    assert result.reason == (
        "" if permission else "BULK_DOWNLOAD_NOT_AUTHORIZED"
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
    result = implementation.evaluate_admit_014(
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
    reconstructed = implementation.Admit014EvaluationResult(
        *(getattr(result, name) for name in implementation.RESULT_FIELDS)
    )
    assert reconstructed == result
    with pytest.raises(FrozenInstanceError):
        result.reason = "changed"

    class Subclass(implementation.Admit014EvaluationResult):
        pass

    with pytest.raises(TypeError):
        Subclass(
            *(getattr(result, name) for name in implementation.RESULT_FIELDS)
        )


def test_all_exact24_actual_malformed_results_rejected() -> None:
    checker = _load_checker()
    assert len(checker.NEGATIVE_RESULT_CASES) == 24
    for case_id in checker.NEGATIVE_RESULT_CASES:
        checker._reject_negative(implementation, case_id)


def test_actual_equals_committed_design_exact37() -> None:
    checker = _load_checker()
    sources = {
        implementation.FORMAL_DESIGN_ROOT
        / "covapie_admit_014_formal_evaluator_interface_truth_matrix.csv": (
            TRUTH_PATH.read_bytes()
        )
    }
    checker._check_actual(implementation, design, sources)


def test_formal_marker_prefix_ast_and_purity(payloads) -> None:
    source, full_sha, prefix_sha, digests = (
        implementation._formal_source_attestation()
    )
    manifest = json.loads(payloads[implementation.MANIFEST_FILE])
    assert source.decode().count(implementation.FORMAL_MARKER) == 1
    assert full_sha == (
        "5f0766a4eb9dac8b00b9729b7d593adfbe105fb212eabbd4e0a3e349b35f7399"
    )
    assert prefix_sha == (
        "503f60c182ab5840d1c56be31f562c94f2b72638b98918857ea0064da8c74cd3"
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
        / "covapie_admit_014_formal_evaluator_interface_issue_readiness_inventory.csv"
    ).read_bytes()
    assert payloads[implementation.ISSUE_FILE] == predecessor_issue
    assert hashlib.sha256(predecessor_issue).hexdigest() == (
        "d2510c9d2cf7ee1a1fc378e639eb69b68612e818f4e7af10a0e36dc0d788f54d"
    )
    manifest = json.loads(payloads[implementation.MANIFEST_FILE])
    assert manifest["precondition_transition"]["complete_count"] == 49
    assert manifest["precondition_transition"]["incomplete_count"] == 2
    assert manifest["precondition_transition"][
        "remaining_open_precondition_ids"
    ] == ["PRE_048", "PRE_049"]
    expected = {
        **{name: True for name in implementation.TRUE_READINESS},
        **{name: False for name in implementation.FALSE_READINESS},
    }
    assert manifest["readiness"] == expected
    assert manifest["current_permission"] is False
    assert manifest["authorized_admit_014_download_execution_count"] == 0
    assert manifest["recommended_next_step"] == (
        "design_covapie_admit_014_unified_adapter_contract_v1"
    )


def test_no_adapter_registry_exact14_enforcement_provider_or_training() -> None:
    source = (ROOT / (
        "src/covalent_ext/"
        "covapie_bulk_download_admission_admit_014_rule_logic_interface.py"
    )).read_text()
    prefix = source.split(implementation.FORMAL_MARKER, 1)[0]
    assert "_evaluate_registered_admit_014" not in prefix
    assert "EVALUATOR_REGISTRY" not in prefix
    assert "classify_admit_014_formal_evaluator_interface_design" not in prefix
    runtime = json.loads(
        (
            ROOT
            / "data/derived/covalent_small/"
            "covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1/"
            "covapie_admit_001_to_013_runtime_manifest.json"
        ).read_text()
    )
    assert runtime["known_not_registered_rule_ids"] == [
        "ADMIT_014", "ADMIT_015"
    ]
    assert runtime["admit_014_registered_in_engine"] is False
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
    with pytest.raises(OSError) as captured:
        implementation.materialize_contract(root)
    assert captured.value.errno == errno.EINVAL
    assert replace_called is False
    assert not root.exists()
    assert not list(tmp_path.glob(".*.staging"))


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
        staging_name: str, destination_name: str, parent_fd: int
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
    with pytest.raises(ValueError, match="owned staging lexical binding drift"):
        implementation.materialize_contract(root)
    assert foreign_name
    assert (tmp_path / foreign_name / "foreign.marker").is_file()


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


def test_checker_manifest_duplicate_missing_extra_reorder(payloads) -> None:
    checker = _load_checker()
    text = payloads[implementation.MANIFEST_FILE].decode()
    duplicate = text.replace(
        '{\n  "Admit014EvaluationResult_implemented"',
        '{\n  "project": "duplicate",\n'
        '  "project": "duplicate2",\n'
        '  "Admit014EvaluationResult_implemented"',
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
            "admit_014_standalone_evaluator_interface_implemented"
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
        checker._check_output_semantics(outputs, sources, ast_digests)


def test_checker_synchronized_tamper_rejected(
    payloads, snapshot, monkeypatch
) -> None:
    checker = _load_checker()
    sources = {record.path: record.content for record in snapshot}
    _, _, _, ast_digests = implementation._formal_source_attestation()
    outputs = dict(payloads)
    contract = outputs[implementation.CONTRACT_FILE].replace(
        b",true\n", b",false\n", 1
    )
    assert contract != outputs[implementation.CONTRACT_FILE]
    outputs[implementation.CONTRACT_FILE] = contract
    manifest = json.loads(outputs[implementation.MANIFEST_FILE])
    manifest["output_sha256"][implementation.CONTRACT_FILE] = hashlib.sha256(
        outputs[implementation.CONTRACT_FILE]
    ).hexdigest()
    outputs[implementation.MANIFEST_FILE] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode()
    monkeypatch.setitem(
        checker.EXPECTED_OUTPUT_SHA256,
        implementation.CONTRACT_FILE,
        hashlib.sha256(outputs[implementation.CONTRACT_FILE]).hexdigest(),
    )
    monkeypatch.setitem(
        checker.EXPECTED_OUTPUT_SHA256,
        implementation.MANIFEST_FILE,
        hashlib.sha256(outputs[implementation.MANIFEST_FILE]).hexdigest(),
    )
    with pytest.raises(ValueError):
        checker._check_output_semantics(outputs, sources, ast_digests)


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
    assert report["actual_design_rows"] == 37
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
    post, post_base = _seed_lifecycle(
        tmp_path / "post", checker, tracked=True
    )
    assert checker._lifecycle(post, post_base) == "post_commit"
    for case in (
        "mixed", "staged", "dirty", "missing", "ignored", "extra",
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
                repo / "docs/extra_admit_014_rule_logic_interface.md"
            ).write_text("extra\n")
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
    with pytest.raises(ValueError, match="candidate ignore check failed"):
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
