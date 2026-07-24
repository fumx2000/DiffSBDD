from __future__ import annotations

import ast
import csv
import ctypes
import errno
import hashlib
import importlib
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
    "with_admit_001_to_014_v1"
)
runtime = importlib.import_module(
    "covalent_ext."
    "covapie_bulk_download_admission_unified_dispatch_runtime_"
    "with_admit_001_to_014"
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
    return runtime._evaluate_registered_admit_014(
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
    assert "simulate_admit_014_unified_adapter_contract_design" not in prefix
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
    assert str(inspect.signature(runtime._evaluate_registered_admit_014)) == (
        "(candidate_record: 'object', *, batch_context: 'object', "
        "evaluation_context: 'object', "
        "download_result_context: 'object', "
        "stage_authorization_context: 'object') -> "
        "'UnifiedAdmissionRuleEvaluation'"
    )


def test_registry_exact14_order_immutability_and_first13_identity():
    registered = tuple(f"ADMIT_{index:03d}" for index in range(1, 15))
    assert type(runtime.EVALUATOR_REGISTRY) is MappingProxyType
    assert tuple(runtime.EVALUATOR_REGISTRY) == registered
    assert tuple(runtime.RULE_NAMES) == registered
    assert tuple(runtime.ADAPTER_IDS) == registered
    assert type(runtime.RULE_NAMES) is MappingProxyType
    assert type(runtime.ADAPTER_IDS) is MappingProxyType
    assert all(
        runtime.EVALUATOR_REGISTRY[rule_id]
        is runtime.predecessor.EVALUATOR_REGISTRY[rule_id]
        for rule_id in registered[:13]
    )
    assert (
        runtime.EVALUATOR_REGISTRY["ADMIT_014"]
        is runtime._evaluate_registered_admit_014
    )
    assert "ADMIT_015" not in runtime.EVALUATOR_REGISTRY
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
            "ADMIT_015",
            "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
            True,
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
            "ADMIT_014_BATCH_CONTEXT_MUST_BE_NONE",
        ),
        (
            {"evaluation": object(), "download": object()},
            "ADMIT_014_EVALUATION_CONTEXT_MUST_BE_NONE",
        ),
        (
            {"download": object()},
            "ADMIT_014_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
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

    monkeypatch.setattr(runtime.admit014, "evaluate_admit_014", formal)
    monkeypatch.setattr(
        runtime.admit014_oracle,
        "classify_admit_014_formal_evaluator_interface_design",
        oracle,
    )
    stage = CountingStage({"current_stage_download_authorized": True})
    result = _handler(object(), stage=stage)
    assert tuple(getattr(result, name) for name in runtime.RESULT_FIELDS) == (
        runtime.RESULT_SCHEMA_VERSION,
        "ADMIT_014",
        "current_gate_grants_no_download_permission",
        "invalid",
        False,
        True,
        "ADMIT_014_CANDIDATE_RECORD_MAPPING_INVALID",
        (),
        (),
        (),
        (),
        False,
        "covapie_admit_014_unified_adapter_v1",
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
            "CURRENT_STAGE_DOWNLOAD_AUTHORIZED_MISSING",
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
            CountingStage({"current_stage_download_authorized": False}),
            "blocked",
            "BULK_DOWNLOAD_NOT_AUTHORIZED",
            (("current_stage_download_authorized", "false"),),
            2,
        ),
        (
            CountingStage({"current_stage_download_authorized": True}),
            "passed",
            "",
            (("current_stage_download_authorized", "true"),),
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
        "ADMIT_014_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
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
            "{target:True,training:True,extra:1}",
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
    assert coverage["affected_rules"] == "ADMIT_015"
    assert coverage["successor_effective_status"] == "open"
    manifest = json.loads(runtime.build_artifacts(runtime_state)[runtime.MANIFEST_FILENAME])
    assert manifest["precondition_transition"]["resolved_precondition_ids"] == [
        "PRE_049"
    ]
    assert manifest["precondition_transition"]["complete_count"] == 51
    assert manifest["precondition_transition"]["incomplete_count"] == 0
    assert manifest["precondition_transition"][
        "implementation_blocking_count"
    ] == 0
    assert manifest["current_permission"] is False
    assert manifest["authorized_admit_014_download_execution_count"] == 0
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
                    "admit_014_registered_in_engine"
                ] = False
            elif mode == "source_blob":
                first = next(iter(manifest["source_input_sha256"]))
                manifest["source_input_sha256"][first] = "0" * 64
            elif mode == "handler_signature":
                manifest["admit_014_handler_signature"] = "tampered"
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
        insertion = '"Admit014EvaluationResult_implemented": true,'
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
                "Admit014EvaluationResult_implemented"
            )
            manifest["readiness"][
                "Admit014EvaluationResult_implemented"
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
                "admit_014_registered_in_engine"
            ] = False
        elif mutation == "ast":
            manifest["candidate_production_source_attestation"][
                "normalized_ast_sha256"
            ]["_raise_dispatch_error"] = "0" * 64
        else:
            manifest["truth_matrix_group_counts"][
                "public_dispatch"
            ] = 4
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
    assert not tuple(tmp_path.glob(".exact14-runtime-stage-*"))


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
    assert not tuple(tmp_path.glob(".exact14-runtime-stage-*"))


def test_materializer_gpfs_einval_fails_closed(
    tmp_path, artifacts, monkeypatch
):
    class RenameEINVAL:
        def __call__(self, *args):
            ctypes.set_errno(errno.EINVAL)
            return -1

    output = tmp_path / "published"
    monkeypatch.setattr(runtime, "_RENAMEAT2", RenameEINVAL())
    with pytest.raises(OSError) as captured:
        runtime._materialize_set(
            runtime._inspect_output_target_read_only(output, ROOT),
            artifacts,
        )
    assert captured.value.errno == errno.EINVAL
    assert not output.exists()
    assert not tuple(tmp_path.glob(".exact14-runtime-stage-*"))


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
    with pytest.raises(ValueError, match="staging lexical"):
        runtime._materialize_set(
            runtime._inspect_output_target_read_only(output, ROOT),
            artifacts,
        )
    assert not output.exists()
    assert foreign_path is not None and foreign_path.is_dir()
    if race == "open_foreign_populated":
        assert (foreign_path / "foreign.txt").read_bytes() == b"foreign\n"


def test_cleanup_rechecks_staging_ownership_and_preserves_foreign(
    tmp_path,
    artifacts,
    monkeypatch,
):
    output = tmp_path / "published"
    original_cleanup = runtime._cleanup_owned_staging
    original_open = os.open
    foreign_path = None

    def fail_rename(*args):
        raise OSError(errno.EINVAL, "forced cleanup")

    def racing_cleanup(
        plan,
        parent_fd,
        root_fd,
        staging_name,
        staging_identity,
        staged,
    ):
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
        foreign_fd = original_open(
            staging_name,
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
        return original_cleanup(
            plan,
            parent_fd,
            root_fd,
            staging_name,
            staging_identity,
            staged,
        )

    monkeypatch.setattr(runtime, "_rename_noreplace", fail_rename)
    monkeypatch.setattr(
        runtime,
        "_cleanup_owned_staging",
        racing_cleanup,
    )
    with pytest.raises(OSError):
        runtime._materialize_set(
            runtime._inspect_output_target_read_only(output, ROOT),
            artifacts,
        )
    assert not output.exists()
    assert foreign_path is not None and foreign_path.is_dir()
    assert (foreign_path / "foreign.txt").read_bytes() == b"foreign\n"


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

    def racing_complete(root_fd, payloads, expected=None):
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
        return original_complete(root_fd, payloads, expected)

    def racing_rename(parent_fd, source, target):
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
        return original_rename(parent_fd, source, target)

    monkeypatch.setattr(
        runtime,
        "_verify_destination_binding",
        racing_verify,
    )
    monkeypatch.setattr(runtime.os, "fsync", racing_fsync)
    monkeypatch.setattr(runtime, "_verify_complete_set", racing_complete)
    monkeypatch.setattr(runtime, "_rename_noreplace", racing_rename)
    with pytest.raises(
        (ValueError, OSError, FileNotFoundError)
    ):
        runtime._materialize_set(
            runtime._inspect_output_target_read_only(output, ROOT),
            artifacts,
        )
    assert acted
    assert not tuple(tmp_path.glob(".exact14-runtime-stage-*"))
    assert foreign_marker is not None and foreign_marker.read_bytes().startswith(
        b"foreign"
    )


def test_materializer_source_contains_no_os_replace():
    source = (ROOT / checker.CANDIDATE).read_text()
    assert "os.replace" not in source
    assert "RENAME_NOREPLACE" in source


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
                "with_admit_001_to_014_extra.py"
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
            "training",
        )
    )
    assert not hasattr(runtime, "evaluate_all_rules")
    assert not hasattr(runtime, "combined_candidate_verdict")
