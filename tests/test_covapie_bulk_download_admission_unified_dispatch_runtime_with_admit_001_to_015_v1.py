from __future__ import annotations

import ast
import csv
import ctypes
import errno
import hashlib
import importlib
import inspect
import io
import json
import os
import shutil
import stat
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

checker = importlib.import_module(
    "check_covapie_bulk_download_admission_unified_dispatch_runtime_"
    "with_admit_001_to_015_v1"
)
runtime = importlib.import_module(
    "covalent_ext."
    "covapie_bulk_download_admission_unified_dispatch_runtime_"
    "with_admit_001_to_015"
)


@pytest.fixture(scope="module")
def source_records():
    return checker.verify_sources()


@pytest.fixture(scope="module")
def runtime_state(source_records):
    snapshot = runtime.build_frozen_source_snapshot(ROOT)
    return runtime.build_runtime_state(snapshot)


@pytest.fixture(scope="module")
def artifacts(runtime_state):
    return runtime.build_artifacts(runtime_state)


class CandidateBomb(Mapping[str, object]):
    def __init__(self) -> None:
        self.accesses = 0

    def __getitem__(self, key: str) -> object:
        self.accesses += 1
        raise AssertionError("candidate read")

    def __iter__(self):
        self.accesses += 1
        raise AssertionError("candidate iteration")

    def __len__(self) -> int:
        self.accesses += 1
        raise AssertionError("candidate length")

    def get(self, key: str, default: object = None) -> object:
        self.accesses += 1
        raise AssertionError("candidate get")

    def __contains__(self, key: object) -> bool:
        self.accesses += 1
        raise AssertionError("candidate contains")


class CountingStage(Mapping[str, object]):
    def __init__(
        self,
        values: Mapping[str, object] | None = None,
        *,
        error: BaseException | None = None,
        alternating: bool = False,
    ) -> None:
        self.values = {} if values is None else dict(values)
        self.error = error
        self.alternating = alternating
        self.calls: list[str] = []

    def __getitem__(self, key: str) -> object:
        self.calls.append(key)
        if self.error is not None:
            raise self.error
        if self.alternating:
            return len(self.calls) == 1
        return self.values[key]

    def __iter__(self):
        raise AssertionError("stage iteration")

    def __len__(self) -> int:
        raise AssertionError("stage length")

    def get(self, key: str, default: object = None) -> object:
        raise AssertionError("stage get")

    def __contains__(self, key: object) -> bool:
        raise AssertionError("stage contains")


def _handler(
    candidate: object,
    *,
    batch: object = None,
    evaluation: object = None,
    download: object = None,
    stage: object = None,
):
    return runtime._evaluate_registered_admit_015(
        candidate,
        batch_context=batch,
        evaluation_context=evaluation,
        download_result_context=download,
        stage_authorization_context=stage,
    )


def _git(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *arguments),
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _rewrite_csv(
    content: bytes,
    mutate,
) -> bytes:
    reader = csv.DictReader(io.StringIO(content.decode(), newline=""))
    header = tuple(reader.fieldnames or ())
    rows = list(reader)
    mutate(rows)
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=header,
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def _synchronized_payloads(
    artifacts: Mapping[str, bytes],
    *,
    csv_name: str | None = None,
    csv_mutate=None,
    manifest_mutate=None,
) -> dict[str, bytes]:
    payloads = dict(artifacts)
    if csv_name is not None:
        payloads[csv_name] = _rewrite_csv(
            payloads[csv_name],
            csv_mutate,
        )
    manifest = json.loads(payloads[checker.OUTPUTS[5]])
    if csv_name is not None:
        manifest["output_sha256"][csv_name] = hashlib.sha256(
            payloads[csv_name]
        ).hexdigest()
    if manifest_mutate is not None:
        manifest_mutate(manifest)
    payloads[checker.OUTPUTS[5]] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode()
    return payloads


def _write_exact6(root: Path, payloads: Mapping[str, bytes]) -> None:
    root.mkdir(parents=True)
    for name, content in payloads.items():
        (root / name).write_bytes(content)


def _replace_at(
    original_open,
    directory_fd: int,
    name: str,
    content: bytes,
) -> None:
    os.rename(
        name,
        f"{name}.replaced",
        src_dir_fd=directory_fd,
        dst_dir_fd=directory_fd,
    )
    descriptor = original_open(
        name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o600,
        dir_fd=directory_fd,
    )
    try:
        os.write(descriptor, content)
    finally:
        os.close(descriptor)


def _legacy_pinned_read_without_final_parent_root(
    root: Path,
    relative: Path,
    mutate_after_first_parent_root,
) -> bytes:
    root_identity = checker._full_identity(os.lstat(root))
    root_fd = os.open(root, checker.DIR_FLAGS)
    descriptors = [root_fd]
    bindings = []
    try:
        parent_fd = root_fd
        for part in relative.parts[:-1]:
            lexical = os.stat(
                part, dir_fd=parent_fd, follow_symlinks=False
            )
            identity = checker._full_identity(lexical)
            child_fd = os.open(
                part, checker.DIR_FLAGS, dir_fd=parent_fd
            )
            descriptors.append(child_fd)
            bindings.append((parent_fd, part, child_fd, identity))
            parent_fd = child_fd
        before = os.stat(
            relative.name,
            dir_fd=parent_fd,
            follow_symlinks=False,
        )
        leaf_identity = checker._full_identity(before)
        leaf_fd = os.open(
            relative.name,
            checker.READ_FLAGS,
            dir_fd=parent_fd,
        )
        descriptors.append(leaf_fd)
        chunks = []
        while True:
            chunk = os.read(leaf_fd, 1 << 16)
            if not chunk:
                break
            chunks.append(chunk)
        assert checker._full_identity(os.fstat(leaf_fd)) == leaf_identity
        assert checker._full_identity(
            os.stat(
                relative.name,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
        ) == leaf_identity
        for lexical_parent, name, child_fd, identity in reversed(
            bindings
        ):
            assert checker._full_identity(
                os.stat(
                    name,
                    dir_fd=lexical_parent,
                    follow_symlinks=False,
                )
            ) == identity
            assert checker._full_identity(os.fstat(child_fd)) == identity
        assert checker._full_identity(os.lstat(root)) == root_identity
        assert checker._full_identity(os.fstat(root_fd)) == root_identity
        mutate_after_first_parent_root()
        assert checker._full_identity(os.fstat(leaf_fd)) == leaf_identity
        assert checker._full_identity(
            os.stat(
                relative.name,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
        ) == leaf_identity
        return b"".join(chunks)
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _legacy_output_read_without_final_inventory_binding(
    parent: Path,
    payloads: Mapping[str, bytes],
    mutate_during_final_leaf,
) -> dict[str, bytes]:
    stage = parent / "stage"
    parent_identity = checker._full_identity(os.lstat(parent))
    root_identity = checker._full_identity(os.lstat(stage))
    parent_fd = os.open(parent, checker.DIR_FLAGS)
    root_fd = os.open("stage", checker.DIR_FLAGS, dir_fd=parent_fd)
    leaves = []
    try:
        assert set(os.listdir(root_fd)) == set(checker.OUTPUTS)
        for name in checker.OUTPUTS:
            item = os.stat(
                name, dir_fd=root_fd, follow_symlinks=False
            )
            identity = checker._full_identity(item)
            descriptor = os.open(
                name, checker.READ_FLAGS, dir_fd=root_fd
            )
            leaves.append((name, descriptor, identity))
        observed = {}
        for name, descriptor, _ in leaves:
            chunks = []
            while True:
                chunk = os.read(descriptor, 1 << 16)
                if not chunk:
                    break
                chunks.append(chunk)
            observed[name] = b"".join(chunks)
        for name, descriptor, identity in leaves:
            assert checker._full_identity(os.fstat(descriptor)) == identity
            assert checker._full_identity(
                os.stat(
                    name,
                    dir_fd=root_fd,
                    follow_symlinks=False,
                )
            ) == identity
        assert checker._full_identity(os.fstat(root_fd)) == root_identity
        assert checker._full_identity(
            os.stat("stage", dir_fd=parent_fd, follow_symlinks=False)
        ) == root_identity
        assert checker._full_identity(os.fstat(parent_fd)) == parent_identity
        assert checker._full_identity(os.lstat(parent)) == parent_identity
        assert set(os.listdir(root_fd)) == set(checker.OUTPUTS)
        for index, (name, descriptor, identity) in enumerate(leaves):
            if index == len(leaves) - 1:
                mutate_during_final_leaf()
            assert checker._full_identity(os.fstat(descriptor)) == identity
            assert checker._full_identity(
                os.stat(
                    name,
                    dir_fd=root_fd,
                    follow_symlinks=False,
                )
            ) == identity
        return observed
    finally:
        for _, descriptor, _ in leaves:
            os.close(descriptor)
        os.close(root_fd)
        os.close(parent_fd)


def _init_synthetic_repo(
    root: Path,
    *,
    missing: Path | None = None,
    ignore: str | None = None,
) -> str:
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "checker@example.invalid")
    _git(root, "config", "user.name", "Checker")
    (root / "baseline.txt").write_text("baseline\n")
    if ignore is not None:
        (root / ".gitignore").write_text(ignore + "\n")
    _git(root, "add", "baseline.txt")
    if ignore is not None:
        _git(root, "add", ".gitignore")
    assert _git(root, "commit", "-qm", "baseline").returncode == 0
    for relative in checker.EXACT10:
        if relative == missing:
            continue
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(relative.as_posix().encode() + b"\n")
    return _git(root, "rev-parse", "HEAD").stdout.strip()


def test_canonical_runtime_and_frozen_base_identity(source_records):
    checker.canonical_guard()
    assert sys.implementation.name == "cpython"
    assert tuple(sys.version_info[:3]) == (3, 10, 4)
    assert len(source_records) == 20
    assert tuple(
        row["source_relative_path"] for row in source_records
    ) == tuple(path for path, _ in checker.SOURCE_BOUNDARY)


def test_exact20_sources_are_git_blob_and_filesystem_identical(
    source_records,
):
    assert all(row["index_stage"] == 0 for row in source_records)
    assert all(
        row["base_tree_blob"] == row["index_blob"]
        for row in source_records
    )
    assert all(
        row["expected_sha256"]
        == row["base_tree_sha256"]
        == row["filesystem_sha256"]
        for row in source_records
    )


def test_public_marker_prefix_exact11_and_frozen_ast():
    evidence = checker.attest_candidate()
    assert evidence["full_sha256"] == checker.EXPECTED_PRODUCTION_SHA256
    assert (
        evidence["prefix_sha256"]
        == checker.EXPECTED_MARKER_PREFIX_SHA256
    )
    assert (
        tuple(evidence["definition_ast_sha256"])
        == checker.PUBLIC_DEFINITIONS
    )


def test_public_closure_has_only_allowed_imports_and_no_simulator():
    source = (ROOT / checker.CANDIDATE).read_text()
    prefix = source.split(checker.PUBLIC_MARKER, 1)[0]
    tree = ast.parse(prefix)
    imports = [
        node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    assert len(imports) == 8
    assert "unified_adapter_contract_design_gate" not in prefix
    assert "simulate_admit_015_unified_adapter_contract_design" not in prefix
    assert all(
        token not in prefix
        for token in (
            "pathlib",
            "os.",
            "json",
            "csv",
            "hashlib",
            "provider",
            "downloader",
            "data/raw",
            "checkpoints",
        )
    )


@pytest.mark.parametrize(
    "name",
    (
        "UnifiedAdmissionRuleEvaluation",
        "UnifiedAdmissionDispatchError",
        "RESULT_SCHEMA_VERSION",
        "RESULT_FIELDS",
        "DISPATCH_ERROR_FIELDS",
        "DISPATCH_ERROR_CODES",
        "OUTCOME_VOCABULARY",
    ),
)
def test_shared_exact13_objects_preserve_identity(name):
    assert getattr(runtime, name) is getattr(runtime.predecessor, name)


def test_handler_and_dispatcher_signatures_are_frozen():
    import inspect

    assert inspect.signature(runtime.evaluate_admission_rule) == inspect.signature(
        runtime.predecessor.evaluate_admission_rule
    )
    assert str(inspect.signature(runtime._evaluate_registered_admit_015)) == (
        "(candidate_record: 'object', *, batch_context: 'object', "
        "evaluation_context: 'object', "
        "download_result_context: 'object', "
        "stage_authorization_context: 'object') -> "
        "'UnifiedAdmissionRuleEvaluation'"
    )


def test_registry_exact15_order_immutability_and_first14_identity():
    registered = tuple(f"ADMIT_{index:03d}" for index in range(1, 16))
    assert type(runtime.EVALUATOR_REGISTRY) is MappingProxyType
    assert tuple(runtime.EVALUATOR_REGISTRY) == registered
    assert tuple(runtime.RULE_NAMES) == registered
    assert tuple(runtime.ADAPTER_IDS) == registered
    assert type(runtime.RULE_NAMES) is MappingProxyType
    assert type(runtime.ADAPTER_IDS) is MappingProxyType
    assert all(
        runtime.EVALUATOR_REGISTRY[rule_id]
        is runtime.predecessor.EVALUATOR_REGISTRY[rule_id]
        for rule_id in registered[:14]
    )
    assert (
        runtime.EVALUATOR_REGISTRY["ADMIT_015"]
        is runtime._evaluate_registered_admit_015
    )
    assert "ADMIT_015" in runtime.EVALUATOR_REGISTRY
    with pytest.raises(TypeError):
        runtime.EVALUATOR_REGISTRY["ADMIT_015"] = object()


@pytest.mark.parametrize(
    ("rule_id", "code", "known", "callable_discovered", "ready"),
    (
        (True, "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", False, False, False),
        (14, "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID", False, False, False),
        (
            "ADMIT_999",
            "UNIFIED_ADMISSION_RULE_ID_UNKNOWN",
            False,
            False,
            False,
        ),
        (
            type("_RuleIdSubclass", (str,), {})("ADMIT_015"),
            "UNIFIED_ADMISSION_RULE_ID_TYPE_INVALID",
            False,
            False,
            False,
        ),
    ),
)
def test_dispatcher_exact_precedence(
    rule_id, code, known, callable_discovered, ready
):
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as captured:
        runtime.evaluate_admission_rule(rule_id, {})
    error = captured.value
    assert (
        error.code,
        error.known_rule,
        error.callable_discovered,
        error.adapter_ready,
    ) == (code, known, callable_discovered, ready)


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    (
        (
            {
                "batch": object(),
                "evaluation": object(),
                "download": object(),
            },
            "ADMIT_015_BATCH_CONTEXT_MUST_BE_NONE",
        ),
        (
            {"evaluation": object(), "download": object()},
            "ADMIT_015_EVALUATION_CONTEXT_MUST_BE_NONE",
        ),
        (
            {"download": object()},
            "ADMIT_015_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
        ),
    ),
)
def test_handler_context_precedence_is_fail_closed(kwargs, reason):
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as captured:
        _handler(object(), **kwargs)
    error = captured.value
    assert (
        error.code,
        error.reason,
        error.known_rule,
        error.callable_discovered,
        error.adapter_ready,
    ) == (
        "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        reason,
        True,
        True,
        True,
    )


def test_candidate_invalid_has_exact13_and_zero_calls(monkeypatch):
    calls = {"formal": 0, "oracle": 0}

    def formal(**kwargs):
        calls["formal"] += 1
        raise AssertionError("formal called")

    def oracle(**kwargs):
        calls["oracle"] += 1
        raise AssertionError("oracle called")

    monkeypatch.setattr(runtime.admit015, "evaluate_admit_015", formal)
    monkeypatch.setattr(
        runtime.admit015_oracle,
        "classify_admit_015_formal_evaluator_interface_design",
        oracle,
    )
    stage = CountingStage({"current_stage_training_authorized": True})
    result = _handler(object(), stage=stage)
    assert tuple(getattr(result, name) for name in runtime.RESULT_FIELDS) == (
        runtime.RESULT_SCHEMA_VERSION,
        "ADMIT_015",
        "current_gate_grants_no_training_permission",
        "invalid",
        False,
        True,
        "ADMIT_015_CANDIDATE_RECORD_MAPPING_INVALID",
        (),
        (),
        (),
        (),
        False,
        "covapie_admit_015_unified_adapter_v1",
    )
    assert calls == {"formal": 0, "oracle": 0}
    assert stage.calls == []


@pytest.mark.parametrize(
    ("stage", "outcome", "reason", "normalized", "accesses"),
    (
        (
            None,
            "blocked",
            "STAGE_AUTHORIZATION_CONTEXT_REQUIRED",
            (),
            None,
        ),
        (
            object(),
            "blocked",
            "STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID",
            (),
            None,
        ),
        (
            CountingStage(),
            "blocked",
            "CURRENT_STAGE_TRAINING_AUTHORIZED_MISSING",
            (),
            2,
        ),
        (
            CountingStage(error=RuntimeError("lookup")),
            "blocked",
            "STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED",
            (),
            2,
        ),
        (
            CountingStage({"current_stage_training_authorized": False}),
            "blocked",
            "TRAINING_NOT_AUTHORIZED",
            (("current_stage_training_authorized", "false"),),
            2,
        ),
        (
            CountingStage({"current_stage_training_authorized": True}),
            "passed",
            "",
            (("current_stage_training_authorized", "true"),),
            2,
        ),
    ),
)
def test_stage_projection_and_access_contract(
    stage, outcome, reason, normalized, accesses
):
    candidate = CandidateBomb()
    result = _handler(candidate, stage=stage)
    assert result.outcome == outcome
    assert result.reason == reason
    assert result.normalized_values == normalized
    assert result.validated_candidate_fields == ()
    assert result.consumed_candidate_fields == ()
    assert candidate.accesses == 0
    if accesses is not None:
        assert len(stage.calls) == accesses


def test_stateful_stage_mapping_mismatch_fails_closed():
    stage = CountingStage(alternating=True)
    with pytest.raises(runtime.UnifiedAdmissionDispatchError) as captured:
        _handler({}, stage=stage)
    assert captured.value.reason == (
        "ADMIT_015_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
    )
    assert len(stage.calls) == 2


def test_exact42_is_independently_executed():
    observations = checker.verify_exact42(runtime)
    assert len(observations) == 42
    assert all(row["candidate_access"] == 0 for row in observations)
    assert all(row["adapter_access"] == 0 for row in observations)


def test_truth_exact42_input_representations_are_case_specific(
    runtime_state,
):
    inherited = runtime_state["truth_rows"][:42]
    assert tuple(row["case_id"] for row in inherited) == tuple(
        runtime.EXACT42_INPUT_REPRESENTATIONS
    )
    assert all(
        tuple(
            row[name]
            for name in runtime.TRUTH_INPUT_REPRESENTATION_COLUMNS
        )
        == runtime.EXACT42_INPUT_REPRESENTATIONS[row["case_id"]]
        for row in inherited
    )
    by_id = {row["case_id"]: row for row in inherited}
    expected = {
        "batch_non_none": (
            "{}", "object", "None", "None", "{target:True}",
        ),
        "evaluation_empty_mapping": (
            "{}", "None", "{}", "None", "{target:True}",
        ),
        "multiple_invalid_batch_first": (
            "object", "object", "object", "object", "{target:True}",
        ),
        "candidate_non_mapping": (
            "object", "None", "None", "None", "{}",
        ),
        "candidate_instrumented": (
            "instrumented_mapping", "None", "None", "None", "None",
        ),
        "stage_false": (
            "{}", "None", "None", "None", "{target:False}",
        ),
        "stage_extra_keys": (
            "{}", "None", "None", "None",
            "{target:True,download:True,extra:1}",
        ),
        "nonrepeatable_mismatch": (
            "{}", "None", "None", "None", "alternating_mapping",
        ),
        "source_wrong_type": (
            "{}", "None", "None", "None", "None",
        ),
        "oracle_wrong_type": (
            "{}", "None", "None", "None", "None",
        ),
    }
    assert all(
        tuple(
            by_id[case_id][name]
            for name in runtime.TRUTH_INPUT_REPRESENTATION_COLUMNS
        )
        == representations
        for case_id, representations in expected.items()
    )
    mismatch = runtime._truth_row(
        "representation_mismatch",
        "test",
        "passed",
        "passed",
        "{}",
        "{}",
        expected_input_representations=(
            "object", "None", "None", "None", "None",
        ),
    )
    assert mismatch["case_passed"] == "false"


def test_truth_batch_evaluation_download_columns_not_all_none(
    runtime_state,
):
    inherited = runtime_state["truth_rows"][:42]
    assert {
        row["batch_context_representation"] for row in inherited
    } == {"None", "object", "{}"}
    assert {
        row["evaluation_context_representation"] for row in inherited
    } == {"None", "object", "{}"}
    assert {
        row["download_result_context_representation"] for row in inherited
    } == {"None", "object", "{}"}


def test_truth_input_representation_no_cross_envelope_leakage(
    runtime_state,
):
    rows = runtime_state["truth_rows"]
    runtime._validate_truth_input_representations(rows)
    assert all(
        row["candidate_representation"]
        in {"{}", "object", "instrumented_mapping"}
        and row["batch_context_representation"]
        in {"None", "object", "{}"}
        and row["evaluation_context_representation"]
        in {"None", "object", "{}"}
        and row["download_result_context_representation"]
        in {"None", "object", "{}"}
        and not row["stage_authorization_context_representation"].startswith(
            ("batch=", "evaluation=", "download=")
        )
        for row in rows
    )


def test_checker_rebuilds_all_five_input_representations(monkeypatch):
    def production_representation_helper_forbidden(*args, **kwargs):
        raise AssertionError("production representation helper imported")

    monkeypatch.setattr(
        runtime,
        "_runtime_input_representations",
        production_representation_helper_forbidden,
    )
    specs = checker._independent_specs()
    observations = checker.verify_exact42(runtime)
    assert len(specs) == len(observations) == 42
    assert all(
        observation["input_representations"]
        == spec["input_representations"]
        for spec, observation in zip(specs, observations, strict=True)
    )


def test_checker_exact42_has_no_predecessor_checker_dependency(
    monkeypatch,
):
    predecessor_name = (
        "check_covapie_bulk_download_admission_admit_014_"
        "unified_adapter_contract_v1"
    )

    class Poisoned:
        @staticmethod
        def _independent_route_specs():
            raise AssertionError("unfrozen predecessor checker used")

    monkeypatch.setitem(sys.modules, predecessor_name, Poisoned())
    monkeypatch.setattr(
        sys,
        "path",
        [item for item in sys.path if item != SCRIPTS],
    )
    assert len(checker._independent_specs()) == 42
    source = (ROOT / checker.TOP_LEVEL[1]).read_text()
    assert predecessor_name not in source
    assert "_independent_route_specs" not in source


def test_checker_specs_load_without_scripts_on_sys_path():
    checker_path = ROOT / checker.TOP_LEVEL[1]
    code = (
        "import importlib.util,sys;"
        f"sys.path=[p for p in sys.path if p!={SCRIPTS!r}];"
        f"s=importlib.util.spec_from_file_location('isolated',{str(checker_path)!r});"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "assert len(m._independent_specs())==42"
    )
    completed = subprocess.run(
        (sys.executable, "-B", "-c", code),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode()


def test_exact11_source_and_exact8_oracle_negatives():
    assert checker.verify_negative_contracts(runtime) == (11, 8)


def test_predecessor_representative_dispatch_continuity():
    assert checker.verify_runtime(runtime) == {
        "exact42_count": 42,
        "source_negative_count": 11,
        "oracle_negative_count": 8,
    }


def test_runtime_state_exact_counts_transition_and_readiness(runtime_state):
    assert len(runtime_state["contract_rows"]) == 45
    assert len(runtime_state["truth_rows"]) == 79
    assert len(runtime_state["registry_rows"]) == 27
    assert len(runtime_state["safety_rows"]) == 32
    assert len(runtime_state["issue_rows"]) == 30
    assert all(
        row["case_passed"] == "true"
        for row in runtime_state["truth_rows"]
    )
    assert tuple(runtime_state["truth_rows"][0]) == checker.TRUTH_HEADER
    stable = next(
        row
        for row in runtime_state["truth_rows"]
        if row["case_id"] == "stage_true"
    )
    assert (
        stable["expected_call_order"],
        stable["observed_call_order"],
        stable["expected_stage_context_identity_preserved"],
        stable["observed_stage_context_identity_preserved"],
        stable["adapter_stage_target_access_count"],
        stable["formal_stage_target_access_count"],
        stable["oracle_stage_target_access_count"],
        stable["stage_target_access_count"],
    ) == ("formal|oracle", "formal|oracle", "true", "true", "0", "1", "1", "2")
    coverage = next(
        row
        for row in runtime_state["issue_rows"]
        if row["issue_id"]
        == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
    )
    assert coverage["affected_rules"] == ""
    assert coverage["successor_effective_status"] == "resolved"
    manifest = json.loads(runtime.build_artifacts(runtime_state)[runtime.MANIFEST_FILENAME])
    assert manifest["precondition_transition"]["resolved_precondition_ids"] == [
        "PRE_032",
        "PRE_033",
    ]
    assert manifest["precondition_transition"]["complete_count"] == 40
    assert manifest["precondition_transition"]["incomplete_count"] == 5
    assert manifest["precondition_transition"][
        "implementation_blocking_count"
    ] == 5
    assert manifest["current_permission"] is False
    assert manifest["authorized_admit_015_training_execution_count"] == 0
    assert manifest["truth_input_representation_columns"] == list(
        checker.TRUTH_INPUT_REPRESENTATION_COLUMNS
    )
    assert (
        manifest[
            "truth_input_representation_semantics_independently_verified"
        ]
        is True
    )
    assert all(manifest[name] is True for name in checker.TRUE_READINESS)
    assert all(manifest[name] is False for name in checker.FALSE_READINESS)


def test_artifacts_are_byte_deterministic(runtime_state, artifacts):
    assert tuple(artifacts) == checker.OUTPUTS
    assert artifacts == runtime.build_artifacts(runtime_state)
    assert artifacts == runtime.build_artifacts(runtime_state)


@pytest.mark.parametrize(
    "mode",
    (
        "contract",
        "truth_result",
        "truth_call_order",
        "truth_identity",
        "truth_access",
        "registry_identity",
        "registry_registered",
        "safety",
        "issue_noncoverage",
        "issue_coverage_extra",
        "precondition",
        "readiness",
        "source_blob",
        "handler_signature",
        "truth_representation_columns",
        "truth_representation_semantics",
        "output_materialization",
    ),
)
def test_independent_checker_rejects_semantic_tamper_after_sha_bypass(
    artifacts,
    source_records,
    monkeypatch,
    mode,
):
    csv_name = None
    csv_mutate = None
    manifest_mutate = None
    if mode == "contract":
        csv_name = checker.OUTPUTS[0]
        csv_mutate = lambda rows: rows[0].__setitem__(
            "expected_value", "tampered"
        )
    elif mode in {
        "truth_result",
        "truth_call_order",
        "truth_identity",
        "truth_access",
    }:
        csv_name = checker.OUTPUTS[1]
        field = {
            "truth_result": "expected_result_json",
            "truth_call_order": "expected_call_order",
            "truth_identity": (
                "expected_stage_context_identity_preserved"
            ),
            "truth_access": "formal_stage_target_access_count",
        }[mode]
        csv_mutate = lambda rows, field=field: rows[16].__setitem__(
            field, "tampered"
        )
    elif mode.startswith("registry_"):
        csv_name = checker.OUTPUTS[2]
        field = {
            "registry_identity": "observed_handler_identity",
            "registry_registered": "registered",
        }[mode]
        csv_mutate = lambda rows, field=field: rows[13].__setitem__(
            field, "false"
        )
    elif mode == "safety":
        csv_name = checker.OUTPUTS[3]
        csv_mutate = lambda rows: rows[0].__setitem__(
            "observed_state", "false"
        )
    elif mode.startswith("issue_"):
        csv_name = checker.OUTPUTS[4]

        def issue_mutation(rows):
            if mode == "issue_noncoverage":
                row = next(
                    item
                    for item in rows
                    if item["issue_id"]
                    != "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
                )
                row["severity"] = "tampered"
            else:
                row = next(
                    item
                    for item in rows
                    if item["issue_id"]
                    == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"
                )
                row["status"] = "tampered"

        csv_mutate = issue_mutation
    else:
        def mutate_manifest(manifest):
            if mode == "precondition":
                manifest["precondition_transition"]["row_count"] = 50
            elif mode == "readiness":
                manifest["readiness"][
                    "admit_015_registered_in_engine"
                ] = False
            elif mode == "source_blob":
                first = next(iter(manifest["source_input_sha256"]))
                manifest["source_input_sha256"][first] = "0" * 64
            elif mode == "handler_signature":
                manifest["admit_015_handler_signature"] = "tampered"
            elif mode == "truth_representation_columns":
                manifest["truth_input_representation_columns"][0] = (
                    "tampered"
                )
            elif mode == "truth_representation_semantics":
                manifest[
                    "truth_input_representation_"
                    "semantics_independently_verified"
                ] = False
            else:
                manifest["output_materialization"][
                    "staging_lexical_binding_verified"
                ] = False

        manifest_mutate = mutate_manifest
    tampered = _synchronized_payloads(
        artifacts,
        csv_name=csv_name,
        csv_mutate=csv_mutate,
        manifest_mutate=manifest_mutate,
    )
    monkeypatch.setattr(
        checker,
        "EXPECTED_OUTPUT_SHA256",
        {
            name: hashlib.sha256(content).hexdigest()
            for name, content in tampered.items()
        },
    )
    with pytest.raises(AssertionError):
        checker.verify_artifacts(tampered, source_records, runtime)


@pytest.mark.parametrize(
    "mode",
    (
        "public_signature_match",
        "registry_proxy",
        "known_delete",
        "callable_reorder",
        "adapter_add",
        "legacy_nonempty",
        "registered_count_bool",
        "result_schema",
        "dispatch_codes",
        "cardinality",
        "precedence",
        "source_path_digest",
        "source_pair_digest",
        "issue_id",
        "remaining_issues",
        "permission",
        "execution",
        "delete_b3",
        "sixth_mask",
        "feature_semantics",
        "mandatory_enforcement",
        "materialization",
        "lifecycle",
        "bool_to_int",
        "nested_missing",
        "nested_extra",
        "nested_reorder",
    ),
)
def test_full_manifest_rebuild_rejects_synchronized_sha_bypass(
    artifacts,
    source_records,
    monkeypatch,
    mode,
):
    def mutate(manifest):
        if mode == "public_signature_match":
            manifest["public_dispatch_signature_matches_exact14"] = False
        elif mode == "registry_proxy":
            manifest["registry_mapping_proxy_type"] = False
        elif mode == "known_delete":
            manifest["known_rule_ids"].remove("ADMIT_015")
        elif mode == "callable_reorder":
            manifest["callable_discovered_rule_ids"].reverse()
        elif mode == "adapter_add":
            manifest["adapter_ready_rule_ids"].append("ADMIT_016")
        elif mode == "legacy_nonempty":
            manifest["legacy_adapter_not_ready_rule_ids"] = ["ADMIT_015"]
        elif mode == "registered_count_bool":
            manifest["registered_rule_count"] = True
        elif mode == "result_schema":
            manifest["result_schema_version"] = "drift"
        elif mode == "dispatch_codes":
            manifest["dispatch_error_codes"].append("DRIFT")
        elif mode == "cardinality":
            manifest["public_dispatch_cardinality"] = "multi_rule"
        elif mode == "precedence":
            manifest["public_dispatch_precedence"].reverse()
        elif mode == "source_path_digest":
            manifest["source_path_list_sha256"] = "0" * 64
        elif mode == "source_pair_digest":
            manifest["source_path_sha256_pairs_sha256"] = "0" * 64
        elif mode == "issue_id":
            manifest["issue_transition_id"] = "DRIFT"
        elif mode == "remaining_issues":
            manifest["remaining_open_issue_ids"] = []
        elif mode == "permission":
            manifest["current_permission"] = True
        elif mode == "execution":
            manifest["authorized_admit_015_training_execution_count"] = 1
        elif mode == "delete_b3":
            manifest["canonical_masks"] = [
                item
                for item in manifest["canonical_masks"]
                if item["alias"] != "B3"
            ]
        elif mode == "sixth_mask":
            manifest["canonical_masks"].append(
                {"semantic_name": "forbidden", "alias": "D"}
            )
        elif mode == "feature_semantics":
            manifest["feature_semantics_audit_completed"] = True
        elif mode == "mandatory_enforcement":
            manifest[
                "mandatory_training_authorization_enforcement_implemented"
            ] = True
        elif mode == "materialization":
            manifest["output_materialization"][
                "complete_set_postverify"
            ] = False
        elif mode == "lifecycle":
            manifest["lifecycle_policy"][
                "bounded_recursive_no_follow"
            ] = False
        elif mode == "bool_to_int":
            manifest["all_checks_passed"] = 1
        elif mode == "nested_missing":
            manifest["source_read_policy"].pop("six_field_identity")
        elif mode == "nested_extra":
            manifest["output_read_policy"]["unexpected"] = True

    tampered = _synchronized_payloads(
        artifacts,
        manifest_mutate=mutate,
    )
    if mode == "nested_reorder":
        manifest = json.loads(tampered[checker.OUTPUTS[5]])
        nested = manifest["source_read_policy"]
        manifest["source_read_policy"] = dict(
            reversed(tuple(nested.items()))
        )
        tampered[checker.OUTPUTS[5]] = (
            json.dumps(manifest, indent=2, sort_keys=False) + "\n"
        ).encode()
    monkeypatch.setattr(
        checker,
        "EXPECTED_OUTPUT_SHA256",
        {
            name: hashlib.sha256(content).hexdigest()
            for name, content in tampered.items()
        },
    )
    with pytest.raises(AssertionError) as captured:
        checker.verify_artifacts(tampered, source_records, runtime)
    assert "manifest" in str(captured.value).lower()
    assert "sha drift" not in str(captured.value).lower()


@pytest.mark.parametrize(
    ("field", "row_index"),
    (
        ("candidate_representation", 6),
        ("batch_context_representation", 0),
        ("evaluation_context_representation", 2),
        ("download_result_context_representation", 4),
        ("stage_authorization_context_representation", 16),
    ),
)
def test_synchronized_truth_input_representation_tamper_rejected_after_sha_bypass(
    artifacts,
    source_records,
    monkeypatch,
    field,
    row_index,
):
    tampered = _synchronized_payloads(
        artifacts,
        csv_name=checker.OUTPUTS[1],
        csv_mutate=lambda rows: rows[row_index].__setitem__(
            field, "tampered"
        ),
    )
    monkeypatch.setattr(
        checker,
        "EXPECTED_OUTPUT_SHA256",
        {
            name: hashlib.sha256(content).hexdigest()
            for name, content in tampered.items()
        },
    )
    with pytest.raises(AssertionError):
        checker.verify_artifacts(tampered, source_records, runtime)


@pytest.mark.parametrize("mutation", ("duplicate", "missing", "extra", "reorder"))
def test_manifest_exact_schema_rejects_mutations(artifacts, mutation):
    content = artifacts[checker.OUTPUTS[5]]
    manifest = json.loads(content)
    if mutation == "duplicate":
        text = content.decode()
        insertion = '"Admit015EvaluationResult_implemented": true,'
        altered = text.replace(insertion, insertion + "\n  " + insertion, 1)
    elif mutation == "missing":
        manifest.pop(next(iter(manifest)))
        altered = json.dumps(manifest).encode()
    elif mutation == "extra":
        manifest["unexpected"] = True
        altered = json.dumps(manifest, sort_keys=True).encode()
    else:
        altered = json.dumps(
            dict(reversed(tuple(manifest.items()))),
            sort_keys=False,
        ).encode()
    with pytest.raises(AssertionError):
        checker._manifest(altered)


@pytest.mark.parametrize(
    "mutation",
    (
        "nested_duplicate",
        "nested_missing",
        "nested_extra",
        "nested_reorder",
        "source_row_missing",
        "source_row_extra",
        "source_row_reorder",
        "output_materialization",
        "readiness",
        "ast",
        "trace_group_count",
    ),
)
def test_manifest_nested_exact_schema_rejects_mutations(
    artifacts,
    mutation,
):
    content = artifacts[checker.OUTPUTS[5]]
    manifest = json.loads(content)
    if mutation == "nested_duplicate":
        line = '    "GPFS_EINVAL_fail_closed": true,'
        altered = content.decode().replace(
            line,
            f"{line}\n{line}",
            1,
        ).encode()
    else:
        if mutation == "nested_missing":
            manifest["output_materialization"].pop(
                "GPFS_EINVAL_fail_closed"
            )
        elif mutation == "nested_extra":
            manifest["readiness"]["unexpected"] = True
        elif mutation == "nested_reorder":
            item = manifest["readiness"].pop(
                "Admit015EvaluationResult_implemented"
            )
            manifest["readiness"][
                "Admit015EvaluationResult_implemented"
            ] = item
        elif mutation.startswith("source_row_"):
            row = manifest["source_input_verification"][0]
            if mutation == "source_row_missing":
                row.pop("tracked")
            elif mutation == "source_row_extra":
                row["unexpected"] = True
            else:
                item = row.pop("base_tree_blob")
                row["base_tree_blob"] = item
        elif mutation == "output_materialization":
            manifest["output_materialization"][
                "staging_lexical_binding_verified"
            ] = False
        elif mutation == "readiness":
            manifest["readiness"][
                "admit_015_registered_in_engine"
            ] = False
        elif mutation == "ast":
            manifest["candidate_production_source_attestation"][
                "normalized_ast_sha256"
            ]["_raise_dispatch_error"] = "0" * 64
        else:
            manifest["truth_matrix_group_counts"][
                "public_dispatch"
            ] = 5
        altered = json.dumps(
            manifest,
            indent=2,
            sort_keys=False,
        ).encode()
    with pytest.raises(AssertionError):
        checker._manifest(altered)


def test_committed_exact6_schema_sha_and_semantics(source_records):
    payloads = checker.output_bytes()
    checked = checker.verify_artifacts(payloads, source_records, runtime)
    assert checked["hashes"] == checker.EXPECTED_OUTPUT_SHA256


def test_materializer_new_publish_and_inode_preserving_noop(
    tmp_path, artifacts
):
    output = tmp_path / "published"
    plan = runtime._inspect_output_target_read_only(output, ROOT)
    runtime._materialize_set(plan, artifacts)
    before = {name: os.lstat(output / name).st_ino for name in artifacts}
    plan = runtime._inspect_output_target_read_only(output, ROOT)
    runtime._materialize_set(plan, artifacts)
    after = {name: os.lstat(output / name).st_ino for name in artifacts}
    assert before == after
    assert {name: (output / name).read_bytes() for name in artifacts} == artifacts
    assert not tuple(tmp_path.glob(".exact15-runtime-stage-*"))


def test_materializer_mismatch_fails_closed_without_repair(
    tmp_path, artifacts
):
    output = tmp_path / "published"
    runtime._materialize_set(
        runtime._inspect_output_target_read_only(output, ROOT),
        artifacts,
    )
    leaf = output / checker.OUTPUTS[0]
    leaf.write_bytes(b"tamper\n")
    before = leaf.read_bytes()
    plan = runtime._inspect_output_target_read_only(output, ROOT)
    with pytest.raises(ValueError, match="repair forbidden"):
        runtime._materialize_set(plan, artifacts)
    assert leaf.read_bytes() == before
    assert not tuple(tmp_path.glob(".exact15-runtime-stage-*"))


def test_materializer_gpfs_einval_fails_closed(
    tmp_path, artifacts, monkeypatch
):
    class RenameEINVAL:
        def __call__(self, *args):
            ctypes.set_errno(errno.EINVAL)
            return -1

    output = tmp_path / "published"
    monkeypatch.setattr(runtime, "_RENAMEAT2", RenameEINVAL())
    with pytest.raises(
        runtime.MaterializationRetentionError,
        match="failure staging retained at",
    ) as captured:
        runtime._materialize_set(
            runtime._inspect_output_target_read_only(output, ROOT),
            artifacts,
        )
    assert isinstance(captured.value.__cause__, OSError)
    assert captured.value.__cause__.errno == errno.EINVAL
    assert captured.value.binding_authenticated is True
    assert captured.value.authenticated_retained_path is not None
    assert not output.exists()
    retained = tuple(tmp_path.glob(".exact15-runtime-stage-*"))
    assert retained == (captured.value.authenticated_retained_path,)
    assert {path.name for path in retained[0].iterdir()} == set(
        runtime.OUTPUT_FILES
    )


@pytest.mark.parametrize(
    "race",
    ("open_foreign_empty", "open_foreign_populated", "pre_rename"),
)
def test_staging_lexical_replacement_preserves_foreign_directory(
    tmp_path,
    artifacts,
    monkeypatch,
    race,
):
    output = tmp_path / "published"
    original = runtime._assert_staging_name_binding
    original_open = os.open
    calls = 0
    foreign_path = None

    def replace_staging(parent_fd, staging_name, populated):
        nonlocal foreign_path
        parent = Path(os.readlink(f"/proc/self/fd/{parent_fd}"))
        foreign_path = parent / staging_name
        os.rename(
            staging_name,
            f"{staging_name}.owned-moved",
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
        )
        os.mkdir(staging_name, dir_fd=parent_fd)
        if populated:
            directory_fd = original_open(
                staging_name,
                runtime.DIRECTORY_FLAGS,
                dir_fd=parent_fd,
            )
            try:
                descriptor = original_open(
                    "foreign.txt",
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0o600,
                    dir_fd=directory_fd,
                )
                os.write(descriptor, b"foreign\n")
                os.close(descriptor)
            finally:
                os.close(directory_fd)

    def racing_binding(
        plan,
        parent_fd,
        staging_name,
        root_fd,
        staging_identity,
    ):
        nonlocal calls
        calls += 1
        trigger = 4 if race == "pre_rename" else 1
        if calls == trigger:
            replace_staging(
                parent_fd,
                staging_name,
                race == "open_foreign_populated",
            )
        return original(
            plan,
            parent_fd,
            staging_name,
            root_fd,
            staging_identity,
        )

    monkeypatch.setattr(
        runtime,
        "_assert_staging_name_binding",
        racing_binding,
    )
    with pytest.raises(
        runtime.MaterializationRetentionError,
        match="lexical binding lost",
    ) as captured:
        runtime._materialize_set(
            runtime._inspect_output_target_read_only(output, ROOT),
            artifacts,
        )
    assert not output.exists()
    assert foreign_path is not None and foreign_path.is_dir()
    if race == "open_foreign_populated":
        assert (foreign_path / "foreign.txt").read_bytes() == b"foreign\n"
    assert captured.value.binding_authenticated is False
    assert captured.value.authenticated_retained_path is None


def test_failure_path_contains_no_cleanup_primitive():
    source = inspect.getsource(runtime._materialize_set)
    assert all(
        token not in source
        for token in (
            "os.unlink",
            "os.remove",
            "Path.unlink",
            "os.rmdir",
            "shutil.rmtree",
        )
    )


@pytest.mark.parametrize(
    "race",
    (
        "before_first_binding",
        "before_parent_fsync",
        "after_parent_fsync",
        "after_root_fsync",
        "final_leaf",
        "output_root",
        "output_parent",
        "eexist_destination",
    ),
)
def test_materializer_real_destination_races_fail_closed(
    tmp_path,
    artifacts,
    monkeypatch,
    race,
):
    output = tmp_path / "published"
    original_verify = runtime._verify_destination_binding
    original_complete = runtime._verify_complete_set
    original_fsync = os.fsync
    original_rename = runtime._rename_noreplace
    original_open = os.open
    verify_calls = 0
    complete_calls = 0
    acted = False
    foreign_marker = None

    def replace_output_root():
        nonlocal acted, foreign_marker
        os.rename(output, output.with_name("published.owned-moved"))
        output.mkdir()
        foreign_marker = output / "foreign.txt"
        foreign_marker.write_bytes(b"foreign\n")
        acted = True

    def replace_output_parent():
        nonlocal acted, foreign_marker
        moved = tmp_path.with_name(f"{tmp_path.name}.owned-moved")
        os.rename(tmp_path, moved)
        os.mkdir(tmp_path)
        foreign_marker = tmp_path / "foreign-parent.txt"
        foreign_marker.write_bytes(b"foreign-parent\n")
        acted = True

    def racing_verify(*args, **kwargs):
        nonlocal verify_calls
        verify_calls += 1
        if not acted and (
            race in {"before_first_binding", "output_root"}
            and verify_calls == 1
            or race == "after_parent_fsync"
            and verify_calls == 2
            or race == "after_root_fsync"
            and verify_calls == 3
        ):
            replace_output_root()
        if (
            not acted
            and race == "output_parent"
            and verify_calls == 2
        ):
            replace_output_parent()
        return original_verify(*args, **kwargs)

    def racing_fsync(descriptor):
        identity = runtime._identity(os.fstat(descriptor))
        parent_identity = runtime._identity(os.lstat(tmp_path))
        if (
            race == "before_parent_fsync"
            and not acted
            and identity == parent_identity
            and output.exists()
        ):
            replace_output_root()
        return original_fsync(descriptor)

    def racing_complete(
        root_fd, payloads, expected=None, **kwargs
    ):
        nonlocal complete_calls, acted, foreign_marker
        complete_calls += 1
        if race == "final_leaf" and not acted and complete_calls == 4:
            name = checker.OUTPUTS[-1]
            _replace_at(
                original_open,
                root_fd,
                name,
                b"foreign\n",
            )
            foreign_marker = output / name
            acted = True
        return original_complete(
            root_fd, payloads, expected, **kwargs
        )

    def racing_rename(
        plan,
        parent_fd,
        source,
        staging_fd,
        staging_identity,
        target,
    ):
        nonlocal acted, foreign_marker
        if race == "eexist_destination" and not acted:
            os.mkdir(target, dir_fd=parent_fd)
            foreign_fd = original_open(
                target,
                runtime.DIRECTORY_FLAGS,
                dir_fd=parent_fd,
            )
            try:
                descriptor = original_open(
                    "foreign.txt",
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0o600,
                    dir_fd=foreign_fd,
                )
                os.write(descriptor, b"foreign\n")
                os.close(descriptor)
            finally:
                os.close(foreign_fd)
            foreign_marker = output / "foreign.txt"
            acted = True
        return original_rename(
            plan,
            parent_fd,
            source,
            staging_fd,
            staging_identity,
            target,
        )

    monkeypatch.setattr(
        runtime,
        "_verify_destination_binding",
        racing_verify,
    )
    monkeypatch.setattr(runtime.os, "fsync", racing_fsync)
    monkeypatch.setattr(runtime, "_verify_complete_set", racing_complete)
    monkeypatch.setattr(runtime, "_rename_noreplace", racing_rename)
    with pytest.raises(
        (
            ValueError,
            OSError,
            FileNotFoundError,
            runtime.MaterializationRetentionError,
        )
    ):
        runtime._materialize_set(
            runtime._inspect_output_target_read_only(output, ROOT),
            artifacts,
        )
    assert acted
    retained = tuple(tmp_path.glob(".exact15-runtime-stage-*"))
    if race == "eexist_destination":
        assert len(retained) == 1
        assert {path.name for path in retained[0].iterdir()} == set(
            runtime.OUTPUT_FILES
        )
    else:
        assert not retained
    assert foreign_marker is not None and foreign_marker.read_bytes().startswith(
        b"foreign"
    )


def test_materializer_source_contains_no_os_replace():
    source = (ROOT / checker.CANDIDATE).read_text()
    assert "os.replace" not in source
    assert "RENAME_NOREPLACE" in source


@pytest.mark.parametrize("owner", ("production", "checker"))
@pytest.mark.parametrize("race", ("root", "parent"))
def test_source_final_leaf_gap_reproduced_and_final_binding_rejects(
    tmp_path,
    monkeypatch,
    owner,
    race,
):
    old = b"old source bytes\n"
    new = b"new lexical source bytes\n"
    relative = Path("a/b/leaf.txt")

    def make_tree(name):
        root = tmp_path / name
        leaf = root / relative
        leaf.parent.mkdir(parents=True)
        leaf.write_bytes(old)
        return root

    def replace_tree(root):
        if race == "root":
            moved = root.with_name(f"{root.name}.moved")
            root.rename(moved)
            lexical_leaf = root / relative
        else:
            moved = root / "a.moved"
            (root / "a").rename(moved)
            lexical_leaf = root / relative
        lexical_leaf.parent.mkdir(parents=True)
        lexical_leaf.write_bytes(new)
        moved_leaf = (
            moved / relative
            if race == "root"
            else moved / Path("b/leaf.txt")
        )
        return lexical_leaf, moved_leaf

    legacy_root = make_tree("legacy-root")
    evidence = {}

    def legacy_mutation():
        lexical_leaf, moved_leaf = replace_tree(legacy_root)
        evidence.update(
            lexical_leaf=lexical_leaf,
            moved_leaf=moved_leaf,
        )

    legacy_result = _legacy_pinned_read_without_final_parent_root(
        legacy_root,
        relative,
        legacy_mutation,
    )
    assert legacy_result == old
    assert evidence["lexical_leaf"].read_bytes() == new
    assert evidence["moved_leaf"].read_bytes() == old
    assert (
        evidence["lexical_leaf"].stat().st_ino
        != evidence["moved_leaf"].stat().st_ino
    )

    fixed_root = make_tree("fixed-root")
    module = runtime if owner == "production" else checker
    reader = (
        runtime._pinned_read
        if owner == "production"
        else checker.pinned_read
    )
    original_stat = os.stat
    leaf_stats = 0
    fixed_evidence = {}

    def racing_stat(path, *args, **kwargs):
        nonlocal leaf_stats
        if path == "leaf.txt" and kwargs.get("dir_fd") is not None:
            leaf_stats += 1
            if leaf_stats == 3:
                lexical_leaf, moved_leaf = replace_tree(fixed_root)
                fixed_evidence.update(
                    lexical_leaf=lexical_leaf,
                    moved_leaf=moved_leaf,
                )
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(module.os, "stat", racing_stat)
    returned = None
    with pytest.raises(
        (ValueError, AssertionError, FileNotFoundError)
    ):
        returned = reader(fixed_root, relative)
    assert returned is None
    assert fixed_evidence["lexical_leaf"].read_bytes() == new
    assert fixed_evidence["moved_leaf"].read_bytes() == old
    assert (
        fixed_evidence["lexical_leaf"].stat().st_ino
        != fixed_evidence["moved_leaf"].stat().st_ino
    )


@pytest.mark.parametrize("owner", ("production", "checker"))
@pytest.mark.parametrize(
    "race",
    (
        "same_byte_leaf",
        "in_place_mutation",
        "unlink_recreate",
        "parent_replacement",
        "root_replacement",
        "stat_open",
        "final_leaf_after_parent",
    ),
)
def test_real_pinned_source_races_fail_closed(
    tmp_path,
    monkeypatch,
    owner,
    race,
):
    module = runtime if owner == "production" else checker
    read = runtime._pinned_read if owner == "production" else checker.pinned_read
    root = tmp_path / "root"
    parent = root / "a" / "b"
    parent.mkdir(parents=True)
    leaf = parent / "leaf.txt"
    payload = b"payload\n"
    leaf.write_bytes(payload)
    original_stat = os.stat
    original_lstat = os.lstat
    original_open = os.open
    leaf_stats = 0
    parent_stats = 0
    root_lstats = 0
    acted = False

    def replace_leaf(directory_fd, *, rename=True, content=payload):
        nonlocal acted
        if rename:
            _replace_at(
                original_open,
                directory_fd,
                "leaf.txt",
                content,
            )
        else:
            os.unlink("leaf.txt", dir_fd=directory_fd)
            descriptor = original_open(
                "leaf.txt",
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
                dir_fd=directory_fd,
            )
            try:
                os.write(descriptor, content)
            finally:
                os.close(descriptor)
        acted = True

    def racing_stat(path, *args, **kwargs):
        nonlocal leaf_stats, parent_stats, acted
        directory_fd = kwargs.get("dir_fd")
        if path == "leaf.txt" and directory_fd is not None:
            leaf_stats += 1
            trigger = 3 if race == "final_leaf_after_parent" else 2
            if not acted and race in {
                "same_byte_leaf",
                "in_place_mutation",
                "unlink_recreate",
                "final_leaf_after_parent",
            } and leaf_stats == trigger:
                if race == "in_place_mutation":
                    descriptor = original_open(
                        "leaf.txt",
                        os.O_WRONLY | os.O_TRUNC,
                        dir_fd=directory_fd,
                    )
                    try:
                        os.write(descriptor, b"changed-longer\n")
                    finally:
                        os.close(descriptor)
                    acted = True
                else:
                    replace_leaf(
                        directory_fd,
                        rename=race != "unlink_recreate",
                    )
        if path == "b" and directory_fd is not None:
            parent_stats += 1
            if (
                race == "parent_replacement"
                and not acted
                and parent_stats == 2
            ):
                os.rename(
                    "b",
                    "b.replaced",
                    src_dir_fd=directory_fd,
                    dst_dir_fd=directory_fd,
                )
                os.mkdir("b", dir_fd=directory_fd)
                acted = True
        return original_stat(path, *args, **kwargs)

    def racing_lstat(path, *args, **kwargs):
        nonlocal root_lstats, acted
        if Path(path) == root:
            root_lstats += 1
            if race == "root_replacement" and not acted and root_lstats == 2:
                original_root = root.with_name("root.replaced")
                os.rename(root, original_root)
                os.mkdir(root)
                acted = True
        return original_lstat(path, *args, **kwargs)

    def racing_open(path, flags, *args, **kwargs):
        nonlocal acted
        directory_fd = kwargs.get("dir_fd")
        if (
            race == "stat_open"
            and not acted
            and path == "leaf.txt"
            and directory_fd is not None
            and not flags & os.O_DIRECTORY
        ):
            replace_leaf(directory_fd)
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(module.os, "stat", racing_stat)
    monkeypatch.setattr(module.os, "lstat", racing_lstat)
    monkeypatch.setattr(module.os, "open", racing_open)
    with pytest.raises(
        (ValueError, AssertionError, FileNotFoundError)
    ):
        read(root, Path("a/b/leaf.txt"))
    assert acted


def test_pinned_source_race_fails_closed(monkeypatch):
    original = runtime._full_identity
    calls = 0

    def drifting_identity(item):
        nonlocal calls
        calls += 1
        identity = original(item)
        if calls == 4:
            return (*identity[:-1], identity[-1] + 1)
        return identity

    monkeypatch.setattr(runtime, "_full_identity", drifting_identity)
    with pytest.raises(ValueError):
        runtime._pinned_read(ROOT, Path(checker.SOURCE_BOUNDARY[0][0]))


def test_checker_pinned_output_race_fails_closed(monkeypatch):
    original = checker._full_identity
    calls = 0

    def drifting_identity(item):
        nonlocal calls
        calls += 1
        identity = original(item)
        if calls == 7:
            return (*identity[:-1], identity[-1] + 1)
        return identity

    monkeypatch.setattr(checker, "_full_identity", drifting_identity)
    with pytest.raises(AssertionError):
        checker.output_bytes()


@pytest.mark.parametrize("race", ("root", "parent", "seventh"))
def test_legacy_exact6_final_traversal_gap_is_reproduced(
    tmp_path,
    artifacts,
    race,
):
    parent = tmp_path / "legacy-case"
    stage = parent / "stage"
    _write_exact6(stage, artifacts)
    evidence = {}

    def mutate():
        if race == "root":
            moved = parent / "stage.moved"
            stage.rename(moved)
            _write_exact6(
                stage,
                {
                    name: b"new " + content
                    for name, content in artifacts.items()
                },
            )
            evidence["moved"] = moved
        elif race == "parent":
            moved = parent.with_name("legacy-case.moved")
            parent.rename(moved)
            parent.mkdir()
            _write_exact6(
                parent / "stage",
                {
                    name: b"new " + content
                    for name, content in artifacts.items()
                },
            )
            evidence["moved"] = moved / "stage"
        else:
            (stage / "seventh.csv").write_bytes(b"seventh\n")

    observed = _legacy_output_read_without_final_inventory_binding(
        parent,
        artifacts,
        mutate,
    )
    assert observed == artifacts
    if race in {"root", "parent"}:
        assert {
            name: (evidence["moved"] / name).read_bytes()
            for name in checker.OUTPUTS
        } == artifacts
        assert (parent / "stage" / checker.OUTPUTS[0]).read_bytes().startswith(
            b"new "
        )
    else:
        assert len(tuple(stage.iterdir())) == 7


@pytest.mark.parametrize(
    "race",
    ("root", "parent", "seventh", "missing", "last_leaf"),
)
def test_checker_exact6_final_traversal_closes_real_bypasses(
    tmp_path,
    artifacts,
    monkeypatch,
    race,
):
    parent = tmp_path / "fixed-case"
    stage = parent / "stage"
    _write_exact6(stage, artifacts)
    original_stat = os.stat
    original_open = os.open
    last_name = checker.OUTPUTS[-1]
    last_stats = 0
    acted = False

    def racing_stat(path, *args, **kwargs):
        nonlocal last_stats, acted
        directory_fd = kwargs.get("dir_fd")
        if path == last_name and directory_fd is not None:
            last_stats += 1
            if last_stats == 3 and not acted:
                if race == "last_leaf":
                    result = original_stat(path, *args, **kwargs)
                    _replace_at(
                        original_open,
                        directory_fd,
                        last_name,
                        b"replacement\n",
                    )
                    acted = True
                    return result
                if race == "root":
                    stage.rename(parent / "stage.moved")
                    _write_exact6(
                        stage,
                        {
                            name: b"new " + content
                            for name, content in artifacts.items()
                        },
                    )
                elif race == "parent":
                    parent.rename(parent.with_name("fixed-case.moved"))
                    parent.mkdir()
                    _write_exact6(
                        parent / "stage",
                        {
                            name: b"new " + content
                            for name, content in artifacts.items()
                        },
                    )
                elif race == "seventh":
                    descriptor = original_open(
                        "seventh.csv",
                        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                        0o600,
                        dir_fd=directory_fd,
                    )
                    os.close(descriptor)
                else:
                    os.unlink(checker.OUTPUTS[0], dir_fd=directory_fd)
                acted = True
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(checker.os, "stat", racing_stat)
    with pytest.raises((AssertionError, FileNotFoundError)):
        checker.output_bytes(parent, Path("stage"))
    assert acted


@pytest.mark.parametrize("owner", ("production", "checker"))
@pytest.mark.parametrize(
    "race",
    (
        "first_leaf",
        "middle_leaf",
        "last_leaf",
        "final_extra",
        "final_missing",
    ),
)
def test_real_complete_set_leaf_and_inventory_races_fail_closed(
    tmp_path,
    artifacts,
    monkeypatch,
    owner,
    race,
):
    module = runtime if owner == "production" else checker
    stage = tmp_path / "stage"
    _write_exact6(stage, artifacts)
    selected = {
        "first_leaf": checker.OUTPUTS[0],
        "middle_leaf": checker.OUTPUTS[2],
        "last_leaf": checker.OUTPUTS[-1],
    }.get(race)
    original_stat = os.stat
    original_listdir = os.listdir
    original_open = os.open
    counts: dict[str, int] = {}
    inventories = 0
    acted = False

    def racing_stat(path, *args, **kwargs):
        nonlocal acted
        directory_fd = kwargs.get("dir_fd")
        if path == selected and directory_fd is not None:
            counts[path] = counts.get(path, 0) + 1
            if not acted and counts[path] == 2:
                _replace_at(
                    original_open,
                    directory_fd,
                    path,
                    artifacts[path],
                )
                acted = True
        return original_stat(path, *args, **kwargs)

    def racing_listdir(path):
        nonlocal inventories, acted
        if type(path) is int:
            inventories += 1
            if not acted and inventories == 2:
                if race == "final_extra":
                    descriptor = original_open(
                        "unexpected.csv",
                        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                        0o600,
                        dir_fd=path,
                    )
                    os.close(descriptor)
                    acted = True
                elif race == "final_missing":
                    os.unlink(checker.OUTPUTS[-1], dir_fd=path)
                    acted = True
        return original_listdir(path)

    monkeypatch.setattr(module.os, "stat", racing_stat)
    monkeypatch.setattr(module.os, "listdir", racing_listdir)
    if owner == "production":
        root_fd = os.open(stage, runtime.DIRECTORY_FLAGS)
        try:
            identities = {
                name: runtime._full_identity(
                    original_stat(
                        name,
                        dir_fd=root_fd,
                        follow_symlinks=False,
                    )
                )
                for name in checker.OUTPUTS
            }
            with pytest.raises((ValueError, FileNotFoundError)):
                runtime._verify_complete_set(
                    root_fd,
                    artifacts,
                    identities,
                )
        finally:
            os.close(root_fd)
    else:
        with pytest.raises((AssertionError, FileNotFoundError)):
            checker.output_bytes(tmp_path, Path("stage"))
    assert acted


@pytest.mark.parametrize("owner", ("production", "checker"))
@pytest.mark.parametrize("race", ("output_root", "output_parent"))
def test_real_complete_set_root_and_parent_races_fail_closed(
    tmp_path,
    artifacts,
    monkeypatch,
    owner,
    race,
):
    module = runtime if owner == "production" else checker
    stage = tmp_path / "stage"
    _write_exact6(stage, artifacts)
    plan = runtime._inspect_output_target_read_only(stage, ROOT)
    original_stat = os.stat
    original_lstat = os.lstat
    root_stats = 0
    parent_lstats = 0
    acted = False

    def racing_stat(path, *args, **kwargs):
        nonlocal root_stats, acted
        if path == "stage" and kwargs.get("dir_fd") is not None:
            root_stats += 1
            trigger = 2 if owner == "production" else 1
            if race == "output_root" and not acted and root_stats == trigger:
                os.rename(
                    "stage",
                    "stage.replaced",
                    src_dir_fd=kwargs["dir_fd"],
                    dst_dir_fd=kwargs["dir_fd"],
                )
                os.mkdir("stage", dir_fd=kwargs["dir_fd"])
                acted = True
        return original_stat(path, *args, **kwargs)

    def racing_lstat(path, *args, **kwargs):
        nonlocal parent_lstats, acted
        if Path(path) == tmp_path:
            parent_lstats += 1
            if (
                race == "output_parent"
                and not acted
                and parent_lstats == 2
            ):
                moved = tmp_path.with_name(f"{tmp_path.name}.replaced")
                os.rename(tmp_path, moved)
                os.mkdir(tmp_path)
                acted = True
        return original_lstat(path, *args, **kwargs)

    monkeypatch.setattr(module.os, "stat", racing_stat)
    monkeypatch.setattr(module.os, "lstat", racing_lstat)
    if owner == "production":
        parent_fd = os.open(plan.parent, runtime.DIRECTORY_FLAGS)
        root_fd = os.open(
            plan.root_name,
            runtime.DIRECTORY_FLAGS,
            dir_fd=parent_fd,
        )
        try:
            with pytest.raises((ValueError, FileNotFoundError)):
                runtime._verify_destination_binding(
                    plan,
                    parent_fd,
                    root_fd,
                    plan.root_identity,
                    artifacts,
                    dict(plan.leaf_identities),
                )
        finally:
            os.close(root_fd)
            os.close(parent_fd)
    else:
        with pytest.raises((AssertionError, FileNotFoundError)):
            checker.output_bytes(tmp_path, Path("stage"))
    assert acted


def test_lifecycle_pre_commit_and_post_commit(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    base = _init_synthetic_repo(root)
    assert checker.lifecycle(root, checker.EXACT10, base=base) == "pre_commit"
    assert _git(
        root, "add", "--", *(path.as_posix() for path in checker.EXACT10)
    ).returncode == 0
    assert _git(root, "commit", "-qm", "candidate").returncode == 0
    assert checker.lifecycle(root, checker.EXACT10, base=base) == "post_commit"


def test_lifecycle_descendant_base_pre_commit(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    base = _init_synthetic_repo(root)
    (root / "descendant.txt").write_text("descendant\n")
    assert _git(root, "add", "descendant.txt").returncode == 0
    assert _git(root, "commit", "-qm", "descendant").returncode == 0
    assert checker.lifecycle(root, checker.EXACT10, base=base) == "pre_commit"


def _assert_generic_symlink_fails_closed(
    tmp_path,
    monkeypatch,
    *,
    tracked: bool,
    directory_target: bool,
):
    root = tmp_path / "repo"
    root.mkdir()
    _init_synthetic_repo(root)
    token = (
        "hidden_covapie_bulk_download_admission_unified_dispatch_runtime_"
        "with_admit_001_to_015_v1.py"
    )
    if directory_target:
        external = tmp_path / "external"
        external.mkdir()
        sentinel = external / token
    else:
        external = tmp_path / "external.txt"
        sentinel = external
    sentinel.write_bytes(b"external sentinel\n")
    link = root / "docs/nested"
    link.symlink_to(external, target_is_directory=directory_target)
    assert not checker._matches_stage_family(link.name)

    if tracked:
        assert _git(root, "add", "docs/nested").returncode == 0
        assert _git(
            root,
            "commit",
            "-qm",
            "tracked generic symlink",
        ).returncode == 0
        mode = _git(root, "ls-files", "-s", "--", "docs/nested").stdout
        assert mode.startswith("120000 ")
        ignored = False
    else:
        (root / ".gitignore").write_text("docs/nested\n")
        assert _git(root, "add", ".gitignore").returncode == 0
        assert _git(
            root,
            "commit",
            "-qm",
            "ignore generic symlink",
        ).returncode == 0
        assert (
            _git(
                root,
                "check-ignore",
                "--no-index",
                "-q",
                "--",
                "docs/nested",
            ).returncode
            == 0
        )
        ignored = True
    base = _git(root, "rev-parse", "HEAD").stdout.strip()
    assert set(
        _git(
            root,
            "ls-files",
            "--others",
            "--exclude-standard",
        ).stdout.splitlines()
    ) == {path.as_posix() for path in checker.EXACT10}

    link_identity = checker._full_identity(os.lstat(link))
    link_value = os.readlink(link)
    sentinel_identity = checker._full_identity(os.lstat(sentinel))
    sentinel_bytes = sentinel.read_bytes()
    external_scandir_calls = 0
    original_scandir = checker.os.scandir

    def guarded_scandir(path):
        nonlocal external_scandir_calls
        if Path(os.path.abspath(path)) == (
            external if directory_target else external.parent
        ):
            external_scandir_calls += 1
            raise AssertionError("external symlink target traversed")
        return original_scandir(path)

    monkeypatch.setattr(checker.os, "scandir", guarded_scandir)
    with pytest.raises(
        AssertionError,
        match="same-stage bounded scan symlink rejected",
    ):
        checker.lifecycle(root, checker.EXACT10, base=base)

    assert external_scandir_calls == 0
    assert link.is_symlink()
    assert os.readlink(link) == link_value
    assert checker._full_identity(os.lstat(link)) == link_identity
    assert checker._full_identity(os.lstat(sentinel)) == sentinel_identity
    assert sentinel.read_bytes() == sentinel_bytes
    assert tracked is not ignored


def test_generic_tracked_symlink_directory_fails_closed(
    tmp_path,
    monkeypatch,
):
    _assert_generic_symlink_fails_closed(
        tmp_path,
        monkeypatch,
        tracked=True,
        directory_target=True,
    )


def test_generic_ignored_symlink_directory_fails_closed(
    tmp_path,
    monkeypatch,
):
    _assert_generic_symlink_fails_closed(
        tmp_path,
        monkeypatch,
        tracked=False,
        directory_target=True,
    )


def test_generic_tracked_symlink_leaf_fails_closed(
    tmp_path,
    monkeypatch,
):
    _assert_generic_symlink_fails_closed(
        tmp_path,
        monkeypatch,
        tracked=True,
        directory_target=False,
    )


def test_generic_ignored_symlink_leaf_fails_closed(
    tmp_path,
    monkeypatch,
):
    _assert_generic_symlink_fails_closed(
        tmp_path,
        monkeypatch,
        tracked=False,
        directory_target=False,
    )


def _fd_target(descriptor: int) -> Path:
    return Path(os.readlink(f"/proc/self/fd/{descriptor}"))


def _path_is_within(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def _init_recursive_race_repo(
    tmp_path,
    *,
    tracked_nested: bool = False,
):
    root = tmp_path / "repo"
    root.mkdir()
    _init_synthetic_repo(root)
    if tracked_nested:
        nested = root / "docs/nested"
        nested.mkdir()
        (nested / "tracked.txt").write_text("tracked\n")
        assert _git(
            root,
            "add",
            "docs/nested/tracked.txt",
        ).returncode == 0
        assert _git(
            root,
            "commit",
            "-qm",
            "tracked nested directory",
        ).returncode == 0
    base = _git(root, "rev-parse", "HEAD").stdout.strip()
    assert set(
        _git(
            root,
            "ls-files",
            "--others",
            "--exclude-standard",
        ).stdout.splitlines()
    ) == {path.as_posix() for path in checker.EXACT10}
    return root, base


def _external_snapshot(paths):
    return {
        path: (
            checker._full_identity(os.lstat(path)),
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )
        for path in paths
    }


def _mutate_on_final_derived_inventory(
    root: Path,
    monkeypatch,
    action,
):
    original_listdir = checker.os.listdir
    derived_parent = root / "data/derived/covalent_small"
    calls = 0
    mutated = False

    def racing_listdir(directory_fd):
        nonlocal calls, mutated
        if (
            type(directory_fd) is int
            and _fd_target(directory_fd) == derived_parent
        ):
            calls += 1
            if calls == 2:
                action()
                mutated = True
        return original_listdir(directory_fd)

    monkeypatch.setattr(checker.os, "listdir", racing_listdir)
    return lambda: (calls, mutated)


def _lifecycle_git_snapshot(root: Path):
    index = subprocess.run(
        ("git", "ls-files", "--stage", "-z"),
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert index.returncode == 0
    return {
        "head": _git(root, "rev-parse", "HEAD").stdout.strip(),
        "tree": _git(root, "rev-parse", "HEAD^{tree}").stdout.strip(),
        "index": index.stdout,
        "identities": {
            path: checker._full_identity(os.lstat(root / path))
            for path in checker.EXACT10
        },
        "untracked": tuple(
            _git(
                root,
                "ls-files",
                "--others",
                "--exclude-standard",
            ).stdout.splitlines()
        ),
        "cached": _git(
            root,
            "diff",
            "--cached",
            "--name-only",
        ).stdout,
        "working": _git(root, "diff", "--name-only").stdout,
    }


@pytest.mark.parametrize("initial_state", ("pre_commit", "post_commit"))
def test_lifecycle_rejects_real_allow_empty_head_drift(
    tmp_path,
    monkeypatch,
    initial_state,
):
    root = tmp_path / "repo"
    root.mkdir()
    base = _init_synthetic_repo(root)
    if initial_state == "post_commit":
        assert _git(
            root,
            "add",
            "--",
            *(path.as_posix() for path in checker.EXACT10),
        ).returncode == 0
        assert _git(root, "commit", "-qm", "candidate").returncode == 0
    before = _lifecycle_git_snapshot(root)

    def allow_empty_commit():
        assert _git(
            root,
            "commit",
            "--allow-empty",
            "-qm",
            "late empty commit",
        ).returncode == 0

    state = _mutate_on_final_derived_inventory(
        root,
        monkeypatch,
        allow_empty_commit,
    )
    with pytest.raises(AssertionError, match="repository HEAD drift"):
        checker.lifecycle(root, checker.EXACT10, base=base)
    calls, mutated = state()
    after = _lifecycle_git_snapshot(root)
    assert calls == 2 and mutated
    assert before["head"] != after["head"]
    assert before["tree"] == after["tree"]
    assert before["index"] == after["index"]
    assert before["identities"] == after["identities"]
    assert before["untracked"] == after["untracked"]
    assert before["cached"] == after["cached"] == ""
    assert before["working"] == after["working"] == ""
    if initial_state == "pre_commit":
        assert set(after["untracked"]) == {
            path.as_posix() for path in checker.EXACT10
        }
    else:
        assert after["untracked"] == ()


def test_lifecycle_rejects_unrelated_clean_tracked_commit(
    tmp_path,
    monkeypatch,
):
    root = tmp_path / "repo"
    root.mkdir()
    base = _init_synthetic_repo(root)
    before = _lifecycle_git_snapshot(root)

    def commit_unrelated_change():
        (root / "baseline.txt").write_text("unrelated clean change\n")
        assert _git(root, "add", "baseline.txt").returncode == 0
        assert _git(
            root,
            "commit",
            "-qm",
            "late unrelated clean commit",
        ).returncode == 0

    state = _mutate_on_final_derived_inventory(
        root,
        monkeypatch,
        commit_unrelated_change,
    )
    with pytest.raises(AssertionError, match="repository HEAD drift"):
        checker.lifecycle(root, checker.EXACT10, base=base)
    calls, mutated = state()
    after = _lifecycle_git_snapshot(root)
    assert calls == 2 and mutated
    assert before["head"] != after["head"]
    assert before["tree"] != after["tree"]
    assert before["index"] != after["index"]
    assert before["identities"] == after["identities"]
    assert before["untracked"] == after["untracked"]
    assert before["cached"] == after["cached"] == ""
    assert before["working"] == after["working"] == ""


@pytest.mark.parametrize(
    ("returncode", "stdout"),
    (
        (2, b""),
        (0, b"0" * 39 + b"\n"),
        (0, b"A" * 40 + b"\n"),
        (0, b"0" * 40 + b"\nextra\n"),
    ),
)
def test_lifecycle_malformed_head_command_fails_closed(
    tmp_path,
    monkeypatch,
    returncode,
    stdout,
):
    root = tmp_path / "repo"
    root.mkdir()
    base = _init_synthetic_repo(root)
    original_git = checker._git

    def malformed_head(repo_root, *arguments):
        if arguments == (
            "rev-parse",
            "--verify",
            "HEAD^{commit}",
        ):
            return subprocess.CompletedProcess(
                arguments,
                returncode,
                stdout,
                b"malformed",
            )
        return original_git(repo_root, *arguments)

    monkeypatch.setattr(checker, "_git", malformed_head)
    with pytest.raises(AssertionError, match="HEAD commit"):
        checker.lifecycle(root, checker.EXACT10, base=base)


def test_pinned_scan_top_directory_pre_open_replacement_fails_closed(
    tmp_path,
    monkeypatch,
):
    root, base = _init_recursive_race_repo(
        tmp_path,
        tracked_nested=True,
    )
    external = tmp_path / "external"
    external.mkdir()
    sentinel = external / "sentinel.txt"
    sentinel.write_bytes(b"external sentinel\n")
    external_before = _external_snapshot((sentinel,))
    original_open = checker.os.open
    mutated = False
    external_open_count = 0

    def racing_open(name, flags, *args, **kwargs):
        nonlocal mutated, external_open_count
        directory_fd = kwargs.get("dir_fd")
        if (
            name == "nested"
            and directory_fd is not None
            and _fd_target(directory_fd) == root / "docs"
            and not mutated
        ):
            os.rename(
                "nested",
                "nested.old",
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
            )
            os.symlink(
                external,
                "nested",
                target_is_directory=True,
                dir_fd=directory_fd,
            )
            mutated = True
        descriptor = original_open(name, flags, *args, **kwargs)
        if _path_is_within(_fd_target(descriptor), external):
            external_open_count += 1
        return descriptor

    monkeypatch.setattr(checker.os, "open", racing_open)
    with pytest.raises(AssertionError, match="directory open failed"):
        checker.lifecycle(root, checker.EXACT10, base=base)
    assert mutated
    assert external_open_count == 0
    assert (root / "docs/nested").is_symlink()
    assert (root / "docs/nested.old").is_dir()
    assert _external_snapshot((sentinel,)) == external_before


def test_pinned_scan_top_directory_post_open_replacement_fails_closed(
    tmp_path,
    monkeypatch,
):
    root, base = _init_recursive_race_repo(
        tmp_path,
        tracked_nested=True,
    )
    external = tmp_path / "external"
    external.mkdir()
    sentinel = external / "sentinel.txt"
    sentinel.write_bytes(b"external sentinel\n")
    external_before = _external_snapshot((sentinel,))
    original_open = checker.os.open
    mutated = False
    external_open_count = 0

    def racing_open(name, flags, *args, **kwargs):
        nonlocal mutated, external_open_count
        descriptor = original_open(name, flags, *args, **kwargs)
        directory_fd = kwargs.get("dir_fd")
        if (
            name == "nested"
            and directory_fd is not None
            and _fd_target(directory_fd) == root / "docs"
            and not mutated
        ):
            os.rename(
                "nested",
                "nested.old",
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
            )
            os.symlink(
                external,
                "nested",
                target_is_directory=True,
                dir_fd=directory_fd,
            )
            mutated = True
        if _path_is_within(_fd_target(descriptor), external):
            external_open_count += 1
        return descriptor

    monkeypatch.setattr(checker.os, "open", racing_open)
    with pytest.raises(AssertionError, match="directory binding drift"):
        checker.lifecycle(root, checker.EXACT10, base=base)
    assert mutated
    assert external_open_count == 0
    assert (root / "docs/nested").is_symlink()
    assert (root / "docs/nested.old/tracked.txt").read_text() == "tracked\n"
    assert _external_snapshot((sentinel,)) == external_before


def test_final_git_inventory_rejects_added_old_path_bypass(
    tmp_path,
    monkeypatch,
):
    root, base = _init_recursive_race_repo(
        tmp_path,
        tracked_nested=True,
    )
    external = tmp_path / "external"
    external.mkdir()
    sentinel = external / "sentinel.txt"
    sentinel.write_bytes(b"external sentinel\n")
    external_before = _external_snapshot((sentinel,))

    def mutate():
        (root / "docs/nested").rename(root / "docs/nested.old")
        (root / "docs/nested").symlink_to(
            external,
            target_is_directory=True,
        )

    state = _mutate_on_final_derived_inventory(
        root,
        monkeypatch,
        mutate,
    )
    with pytest.raises(
        AssertionError,
        match="repository staged/dirty lifecycle",
    ):
        checker.lifecycle(root, checker.EXACT10, base=base)
    calls, mutated = state()
    assert calls == 2 and mutated
    assert (root / "docs/nested").is_symlink()
    assert (root / "docs/nested.old").is_dir()
    assert set(
        _git(
            root,
            "ls-files",
            "--others",
            "--exclude-standard",
        ).stdout.splitlines()
    ) != {path.as_posix() for path in checker.EXACT10}
    assert _external_snapshot((sentinel,)) == external_before


@pytest.mark.parametrize("phase", ("pre_open", "post_open"))
def test_pinned_scan_matching_derived_root_replacement_fails_closed(
    tmp_path,
    monkeypatch,
    phase,
):
    root, base = _init_recursive_race_repo(tmp_path)
    external = tmp_path / "external-stage"
    external.mkdir()
    for name in checker.OUTPUTS:
        (external / name).write_bytes(b"external exact6 sentinel\n")
    external_paths = tuple(external / name for name in checker.OUTPUTS)
    external_before = _external_snapshot(external_paths)
    original_open = checker.os.open
    mutated = False
    external_open_count = 0
    stage_name = checker.STAGE.name
    derived_parent = root / checker.STAGE.parent

    def racing_open(name, flags, *args, **kwargs):
        nonlocal mutated, external_open_count
        directory_fd = kwargs.get("dir_fd")
        selected = (
            name == stage_name
            and directory_fd is not None
            and _fd_target(directory_fd) == derived_parent
            and not mutated
        )
        if selected and phase == "pre_open":
            os.rename(
                stage_name,
                f"{stage_name}.old",
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
            )
            os.symlink(
                external,
                stage_name,
                target_is_directory=True,
                dir_fd=directory_fd,
            )
            mutated = True
        descriptor = original_open(name, flags, *args, **kwargs)
        if selected and phase == "post_open":
            os.rename(
                stage_name,
                f"{stage_name}.old",
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
            )
            os.symlink(
                external,
                stage_name,
                target_is_directory=True,
                dir_fd=directory_fd,
            )
            mutated = True
        if _path_is_within(_fd_target(descriptor), external):
            external_open_count += 1
        return descriptor

    monkeypatch.setattr(checker.os, "open", racing_open)
    reason = (
        "directory open failed"
        if phase == "pre_open"
        else "directory binding drift"
    )
    with pytest.raises(AssertionError, match=reason):
        checker.lifecycle(root, checker.EXACT10, base=base)
    assert mutated
    assert external_open_count == 0
    assert (root / checker.STAGE).is_symlink()
    assert (root / f"{checker.STAGE}.old").is_dir()
    assert _external_snapshot(external_paths) == external_before


def test_lifecycle_final_identity_rejects_same_byte_inode_replacement(
    tmp_path,
    monkeypatch,
):
    root, base = _init_recursive_race_repo(tmp_path)
    target = root / checker.TOP_LEVEL[-1]
    before = target.read_bytes()
    before_identity = checker._full_identity(os.lstat(target))
    retained = tmp_path / "retained-summary"

    def mutate():
        target.rename(retained)
        target.write_bytes(before)

    state = _mutate_on_final_derived_inventory(
        root,
        monkeypatch,
        mutate,
    )
    with pytest.raises(
        AssertionError,
        match="Exact10 final identity drift",
    ):
        checker.lifecycle(root, checker.EXACT10, base=base)
    calls, mutated = state()
    assert calls == 2 and mutated
    assert target.read_bytes() == before
    assert checker._full_identity(os.lstat(target)) != before_identity
    assert _git(root, "diff", "--name-only").stdout == ""
    assert set(
        _git(
            root,
            "ls-files",
            "--others",
            "--exclude-standard",
        ).stdout.splitlines()
    ) == {path.as_posix() for path in checker.EXACT10}


def test_lifecycle_final_identity_rejects_regular_to_symlink(
    tmp_path,
    monkeypatch,
):
    root, base = _init_recursive_race_repo(tmp_path)
    target = root / checker.TOP_LEVEL[-1]
    retained = tmp_path / "retained-summary"
    external = tmp_path / "external-summary"
    external.write_bytes(b"external sentinel\n")
    external_before = _external_snapshot((external,))

    def mutate():
        target.rename(retained)
        target.symlink_to(external)

    state = _mutate_on_final_derived_inventory(
        root,
        monkeypatch,
        mutate,
    )
    with pytest.raises(AssertionError, match="Exact10 leaf unsafe"):
        checker.lifecycle(root, checker.EXACT10, base=base)
    calls, mutated = state()
    assert calls == 2 and mutated
    assert target.is_symlink()
    assert retained.is_file()
    assert _external_snapshot((external,)) == external_before


def test_lifecycle_final_git_inventory_rejects_late_untracked_extra(
    tmp_path,
    monkeypatch,
):
    root, base = _init_recursive_race_repo(tmp_path)
    extra = root / "docs/late-extra.txt"

    def mutate():
        extra.write_text("late extra\n")

    state = _mutate_on_final_derived_inventory(
        root,
        monkeypatch,
        mutate,
    )
    with pytest.raises(
        AssertionError,
        match="entire untracked inventory is not Exact10",
    ):
        checker.lifecycle(root, checker.EXACT10, base=base)
    calls, mutated = state()
    assert calls == 2 and mutated
    assert extra.read_text() == "late extra\n"


def test_lifecycle_final_git_inventory_rejects_tracked_state_drift(
    tmp_path,
    monkeypatch,
):
    root, base = _init_recursive_race_repo(tmp_path)

    def mutate():
        assert _git(
            root,
            "add",
            "--",
            *(path.as_posix() for path in checker.EXACT10),
        ).returncode == 0
        assert _git(
            root,
            "commit",
            "-qm",
            "late candidate commit",
        ).returncode == 0

    state = _mutate_on_final_derived_inventory(
        root,
        monkeypatch,
        mutate,
    )
    with pytest.raises(
        AssertionError,
        match="repository final inventory drift",
    ):
        checker.lifecycle(root, checker.EXACT10, base=base)
    calls, mutated = state()
    assert calls == 2 and mutated
    assert _git(
        root,
        "ls-files",
        "--others",
        "--exclude-standard",
    ).stdout == ""


@pytest.mark.parametrize(
    "mode",
    (
        "nested_docs",
        "nested_ignored_docs",
        "nested_tracked_docs",
        "nested_src",
        "nested_scripts",
        "nested_tests",
        "nested_symlink_directory",
        "nested_forbidden_suffix",
        "nested_oversized",
        "sibling_derived_root",
        "ignored_sibling_root",
        "seventh_exact6",
        "nested_seventh_exact6",
    ),
)
def test_recursive_lifecycle_rejects_nested_stage_family_bypasses(
    tmp_path,
    mode,
):
    root = tmp_path / "repo"
    root.mkdir()
    base = _init_synthetic_repo(root)
    token = (
        "extra_covapie_bulk_download_admission_unified_dispatch_runtime_"
        "with_admit_001_to_015_v1"
    )
    target = None
    if mode in {
        "nested_docs",
        "nested_ignored_docs",
        "nested_tracked_docs",
    }:
        target = root / "docs/nested" / f"{token}.md"
    elif mode == "nested_src":
        target = root / "src/covalent_ext/nested" / f"{token}.py"
    elif mode == "nested_scripts":
        target = root / "scripts/nested" / f"{token}.py"
    elif mode == "nested_tests":
        target = root / "tests/nested" / f"test_{token}.py"
    elif mode == "nested_symlink_directory":
        target = root / "docs/nested" / f"{token}_link"
        target.parent.mkdir(parents=True)
        target.symlink_to(root / "docs", target_is_directory=True)
    elif mode == "nested_forbidden_suffix":
        target = root / "docs/nested" / f"{token}.tmp"
    elif mode == "nested_oversized":
        target = root / "docs/nested" / f"{token}.md"
    elif mode in {"sibling_derived_root", "ignored_sibling_root"}:
        target = (
            root
            / "data/derived/covalent_small"
            / f"{checker.STAGE_NAME}-sibling"
        )
        target.mkdir()
    elif mode == "seventh_exact6":
        target = root / checker.STAGE / "seventh.csv"
    else:
        target = root / checker.STAGE / "nested/seventh.csv"

    if mode != "nested_symlink_directory" and not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        if mode == "nested_oversized":
            with target.open("wb") as stream:
                stream.seek(checker.MAX_BYTES)
                stream.write(b"x")
        elif target.suffix:
            target.write_text("extra\n")

    if mode in {"nested_ignored_docs", "ignored_sibling_root"}:
        relative = target.relative_to(root).as_posix()
        (root / ".gitignore").write_text(relative + "\n")
        assert _git(root, "add", ".gitignore").returncode == 0
        assert _git(root, "commit", "-qm", "ignore nested").returncode == 0
        assert set(
            _git(
                root,
                "ls-files",
                "--others",
                "--exclude-standard",
            ).stdout.splitlines()
        ) == {path.as_posix() for path in checker.EXACT10}
    elif mode == "nested_tracked_docs":
        assert _git(
            root,
            "add",
            "--",
            target.relative_to(root).as_posix(),
        ).returncode == 0
        assert _git(root, "commit", "-qm", "tracked nested").returncode == 0

    if mode == "nested_ignored_docs":
        legacy_top = {
            path.relative_to(root)
            for parent in (
                root / "src/covalent_ext",
                root / "scripts",
                root / "tests",
                root / "docs",
            )
            for path in parent.iterdir()
            if (
                "covapie_bulk_download_admission_unified_dispatch_"
                "runtime_with_admit_001_to_015"
            )
            in path.name
        }
        assert legacy_top == set(checker.TOP_LEVEL)

    with pytest.raises(AssertionError):
        checker.lifecycle(root, checker.EXACT10, base=base)


@pytest.mark.parametrize(
    "mode",
    (
        "mixed",
        "staged",
        "dirty",
        "missing",
        "ignored",
        "tracked_ignored",
        "extra",
        "extra_top",
        "extra_derived",
        "seventh_output",
        "symlink",
        "oversized",
        "forbidden_suffix",
        "base_nonancestor",
    ),
)
def test_lifecycle_rejects_invalid_states(tmp_path, monkeypatch, mode):
    root = tmp_path / mode
    root.mkdir()
    missing = checker.EXACT10[-1] if mode == "missing" else None
    ignore = (
        checker.EXACT10[0].as_posix()
        if mode == "ignored"
        else None
    )
    base = _init_synthetic_repo(root, missing=missing, ignore=ignore)
    exact10 = checker.EXACT10
    if mode == "mixed":
        first = exact10[0].as_posix()
        assert _git(root, "add", "--", first).returncode == 0
        assert _git(root, "commit", "-qm", "one candidate").returncode == 0
    elif mode == "staged":
        assert _git(
            root, "add", "--", exact10[0].as_posix()
        ).returncode == 0
    elif mode == "dirty":
        assert _git(
            root, "add", "--", *(path.as_posix() for path in exact10)
        ).returncode == 0
        assert _git(root, "commit", "-qm", "candidate").returncode == 0
        (root / exact10[0]).write_text("dirty\n")
    elif mode == "tracked_ignored":
        assert _git(
            root, "add", "--", *(path.as_posix() for path in exact10)
        ).returncode == 0
        assert _git(root, "commit", "-qm", "candidate").returncode == 0
        (root / ".gitignore").write_text(exact10[0].as_posix() + "\n")
        assert _git(root, "add", ".gitignore").returncode == 0
        assert _git(root, "commit", "-qm", "ignore tracked").returncode == 0
    elif mode == "extra":
        (root / "extra.txt").write_text("extra\n")
    elif mode == "extra_top":
        target = (
            root
            / "scripts"
            / (
                "covapie_bulk_download_admission_unified_dispatch_runtime_"
                "with_admit_001_to_015_extra.py"
            )
        )
        target.write_text("extra\n")
    elif mode == "extra_derived":
        (root / f"{checker.STAGE}-extra").mkdir()
    elif mode == "seventh_output":
        (root / checker.STAGE / "seventh.csv").write_text("extra\n")
    elif mode == "symlink":
        target = root / exact10[0]
        target.unlink()
        target.symlink_to(root / "baseline.txt")
    elif mode == "oversized":
        monkeypatch.setattr(checker, "MAX_BYTES", 1)
    elif mode == "forbidden_suffix":
        replacement = exact10[3].with_suffix(".tmp")
        (root / replacement).write_text("forbidden\n")
        exact10 = (*exact10[:3], replacement, *exact10[4:])
    elif mode == "base_nonancestor":
        base = "0" * 40
    with pytest.raises(AssertionError):
        checker.lifecycle(root, exact10, base=base)


def test_lifecycle_check_ignore_abnormal_fails_closed(
    tmp_path, monkeypatch
):
    root = tmp_path / "repo"
    root.mkdir()
    base = _init_synthetic_repo(root)
    original = checker._git

    def abnormal(repo_root, *arguments):
        if arguments[:3] == ("check-ignore", "--no-index", "-q"):
            return subprocess.CompletedProcess(arguments, 2, b"", b"failure")
        return original(repo_root, *arguments)

    monkeypatch.setattr(checker, "_git", abnormal)
    with pytest.raises(AssertionError, match="check-ignore"):
        checker.lifecycle(root, checker.EXACT10, base=base)


@pytest.mark.parametrize(
    "target",
    (
        checker.CANDIDATE,
        checker.TOP_LEVEL[1],
        checker.TOP_LEVEL[2],
    ),
)
def test_isolated_imports_are_silent(target):
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        (str(ROOT / "src"), str(ROOT / "scripts"))
    )
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    code = (
        "import importlib; "
        f"importlib.import_module({checker.MODULE!r})"
        if target == checker.CANDIDATE
        else (
            "import importlib.util;"
            f"s=importlib.util.spec_from_file_location('isolated',"
            f"{str(ROOT / target)!r});"
            "m=importlib.util.module_from_spec(s);"
            "s.loader.exec_module(m)"
        )
    )
    completed = subprocess.run(
        (sys.executable, "-B", "-c", code),
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == b""
    assert completed.stderr == b""


def test_exact10_current_lifecycle_and_protected_boundaries():
    lifecycle = checker.lifecycle()
    assert lifecycle in {"pre_commit", "post_commit"}
    status = _git(ROOT, "diff", "--name-only")
    cached = _git(ROOT, "diff", "--cached", "--name-only")
    assert status.stdout == ""
    assert cached.stdout == ""
    untracked = set(
        _git(
            ROOT, "ls-files", "--others", "--exclude-standard"
        ).stdout.splitlines()
    )
    expected_exact10 = {path.as_posix() for path in checker.EXACT10}
    assert untracked == (
        expected_exact10 if lifecycle == "pre_commit" else set()
    )
    forbidden_prefixes = (
        "data/raw/",
        "checkpoints/",
        "equivariant_diffusion/",
    )
    assert not any(
        path.startswith(forbidden_prefixes) for path in expected_exact10
    )
    assert not any(
        path.endswith(checker.FORBIDDEN_SUFFIXES)
        for path in expected_exact10
    )
    assert all(
        not stat.S_ISLNK(os.lstat(ROOT / path).st_mode)
        and os.lstat(ROOT / path).st_size <= checker.MAX_BYTES
        for path in expected_exact10
    )


def test_no_enforcement_provider_download_aggregation_or_training_surface():
    public = (ROOT / checker.CANDIDATE).read_text().split(
        checker.PUBLIC_MARKER, 1
    )[0]
    assert all(
        token not in public
        for token in (
            "mandatory_pre_download",
            "provider_mapping",
            "network",
            "download_action",
            "evaluate_all_rules",
            "combined_candidate_verdict",
                "cross_rule_aggregation",
                "optimizer",
                "backward",
            )
        )
    assert not hasattr(runtime, "evaluate_all_rules")
    assert not hasattr(runtime, "combined_candidate_verdict")
