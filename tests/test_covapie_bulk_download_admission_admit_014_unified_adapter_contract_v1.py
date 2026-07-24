"""Targeted tests for the ADMIT_014 unified-adapter design contract."""
from __future__ import annotations

import ast
import csv
import errno
import hashlib
import importlib.util
import inspect
import io
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import fields
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_bulk_download_admission_admit_014_rule_logic_interface as formal,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_014_formal_evaluator_interface_contract_design_gate
    as oracle,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_014_unified_adapter_contract_design_gate
    as design,
)


ROOT = Path(__file__).resolve().parents[1]
TARGET = "current_stage_download_authorized"
EXPECTED_FIELDS = (
    "schema_version", "admission_rule_id", "admission_rule_name", "outcome",
    "passed", "blocks_candidate", "reason", "normalized_values",
    "validated_candidate_fields", "consumed_candidate_fields",
    "consumed_context_items", "evaluator_io_used", "adapter_id",
)
OUTPUT_SHA = {
    "covapie_admit_014_unified_adapter_contract.csv": "cdcd5d3ae1f3f65d7faa3ff50e61b37b0fcb9133395868885253f487764aeafc",
    "covapie_admit_014_stage_authorization_projection_and_context_routing_matrix.csv": "0d423c4ad785ca92c14e8d3a4881649d7290a6220814e29ab0ed6d7737e653e4",
    "covapie_admit_014_unified_result_projection_truth_matrix.csv": "9c8e08358f806b3cb9172f460fe49da47d06f1ba028cc4b2a1df1ca8d0d5ff53",
    "covapie_admit_014_unified_adapter_safety_audit.csv": "d8530eeb4ecfacd8d26e1d1054112bd927e94ab204cf6eec4c7ab91c76bf6c4b",
    "covapie_admit_014_unified_adapter_issue_readiness_inventory.csv": "d2510c9d2cf7ee1a1fc378e639eb69b68612e818f4e7af10a0e36dc0d788f54d",
    "covapie_admit_014_unified_adapter_contract_manifest.json": "fbcca891692e4b88d2da854425bef9ce38d1eced97df1c0ca826edad95357de0",
}


def _load_checker():
    path = (
        ROOT
        / "scripts"
        / "check_covapie_bulk_download_admission_admit_014_"
        "unified_adapter_contract_v1.py"
    )
    spec = importlib.util.spec_from_file_location(
        f"admit014_adapter_checker_test_{id(path)}", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


checker = _load_checker()


class Probe(Mapping[str, object]):
    def __init__(
        self, values: dict[str, object] | None = None,
        error: BaseException | None = None,
    ) -> None:
        self.values = {} if values is None else values
        self.error = error
        self.accesses: list[str] = []
        self.iterations = self.lengths = self.gets = self.contains = 0

    def __getitem__(self, key: str) -> object:
        self.accesses.append(key)
        if self.error is not None:
            raise self.error
        return self.values[key]

    def __iter__(self):
        self.iterations += 1
        raise AssertionError("iteration forbidden")

    def __len__(self) -> int:
        self.lengths += 1
        raise AssertionError("len forbidden")

    def get(self, key: str, default: object = None) -> object:
        self.gets += 1
        raise AssertionError("get forbidden")

    def __contains__(self, key: object) -> bool:
        self.contains += 1
        raise AssertionError("contains forbidden")


class Alternating(Mapping[str, object]):
    def __init__(self) -> None:
        self.count = 0

    def __getitem__(self, key: str) -> object:
        self.count += 1
        return self.count == 1

    def __iter__(self):
        raise AssertionError

    def __len__(self) -> int:
        raise AssertionError


def simulate(candidate: object = {}, stage: object = None, **overrides):
    kwargs = {
        "batch_context": None,
        "evaluation_context": None,
        "download_result_context": None,
        "stage_authorization_context": stage,
    }
    kwargs.update(overrides)
    return design.simulate_admit_014_unified_adapter_contract_design(
        candidate, **kwargs
    )


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_base_and_canonical_runtime() -> None:
    result = subprocess.run(
        ("git", "show", "-s", "--format=%H%n%P%n%T%n%s", design.EXPECTED_BASE_COMMIT),
        cwd=ROOT, text=True, capture_output=True, check=True,
    )
    assert result.stdout.splitlines() == [
        "44b4306adfa42ef3587f87d08a4f66ed60101fa7",
        "0ec764f03bd3fe227a1e346380f1cdf31837f023",
        "627a3cd228a0c8ba48496171bda7adb61494ca9a",
        "add CovaPIE ADMIT_014 standalone evaluator interface v1",
    ]
    assert sys.implementation.name == "cpython"
    assert tuple(sys.version_info[:3]) == (3, 10, 4)


def test_exact17_sources_and_shared_exact13() -> None:
    snapshot = design.build_frozen_source_snapshot()
    assert len(snapshot.records) == 17
    for record in snapshot.records:
        assert record.index_stage == 0
        assert record.index_mode == record.base_tree_mode
        assert record.index_blob == record.base_tree_blob
        assert len(record.base_tree_blob) == 40
        assert len(record.index_blob) == 40
        assert record.base_tree_blob == record.base_tree_blob.lower()
        assert all(character in "0123456789abcdef" for character in record.base_tree_blob)
        base_bytes = subprocess.run(
            ("git", "cat-file", "blob", record.base_tree_blob),
            cwd=ROOT, capture_output=True, check=True,
        ).stdout
        index_bytes = subprocess.run(
            ("git", "cat-file", "blob", record.index_blob),
            cwd=ROOT, capture_output=True, check=True,
        ).stdout
        assert base_bytes == index_bytes == record.content
        assert record.base_tree_sha256 == record.expected_sha256
        assert record.filesystem_sha256 == record.expected_sha256
    assert tuple(field.name for field in fields(
        design.UnifiedAdmissionEvaluationDesignRecord
    )) == EXPECTED_FIELDS
    assert design.RESULT_FIELDS == EXPECTED_FIELDS


def test_adapter_identity_and_future_signature() -> None:
    assert (
        design.ADMISSION_RULE_ID,
        design.ADMISSION_RULE_NAME,
        design.ADAPTER_ID,
    ) == (
        "ADMIT_014",
        "current_gate_grants_no_download_permission",
        "covapie_admit_014_unified_adapter_v1",
    )
    expected = inspect.Signature(
        parameters=(
            inspect.Parameter(
                "candidate_record",
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                annotation=object,
            ),
            *(
                inspect.Parameter(
                    name,
                    inspect.Parameter.KEYWORD_ONLY,
                    annotation=object,
                )
                for name in (
                    "batch_context", "evaluation_context",
                    "download_result_context", "stage_authorization_context",
                )
            ),
        ),
        return_annotation="UnifiedAdmissionRuleEvaluation",
    )
    signature = design.FUTURE_HANDLER_SIGNATURE_DESIGN
    assert type(signature) is inspect.Signature
    assert signature == expected
    assert tuple(signature.parameters) == (
        "candidate_record", "batch_context", "evaluation_context",
        "download_result_context", "stage_authorization_context",
    )
    assert all(
        parameter.default is inspect.Parameter.empty
        and parameter.annotation is object
        for parameter in signature.parameters.values()
    )
    assert not any(
        parameter.kind in {
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        }
        for parameter in signature.parameters.values()
    )
    assert design.FUTURE_HANDLER_SIGNATURE_TEXT == (
        "_evaluate_registered_admit_014" + str(expected)
    )


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"batch_context": {}}, "ADMIT_014_BATCH_CONTEXT_MUST_BE_NONE"),
        ({"evaluation_context": {}}, "ADMIT_014_EVALUATION_CONTEXT_MUST_BE_NONE"),
        ({"download_result_context": {}}, "ADMIT_014_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE"),
        (
            {"batch_context": {}, "evaluation_context": {}, "download_result_context": {}},
            "ADMIT_014_BATCH_CONTEXT_MUST_BE_NONE",
        ),
        (
            {"evaluation_context": {}, "download_result_context": {}},
            "ADMIT_014_EVALUATION_CONTEXT_MUST_BE_NONE",
        ),
    ],
)
def test_context_routing_first_failure(kwargs, reason) -> None:
    with pytest.raises(design.AdapterContractDesignError) as captured:
        simulate(**kwargs)
    assert captured.value.code == "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID"
    assert captured.value.reason == reason


@pytest.mark.parametrize(
    ("stage", "reason"),
    [
        (None, "STAGE_AUTHORIZATION_CONTEXT_REQUIRED"),
        (object(), "STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID"),
    ],
)
def test_stage_none_and_nonmapping_are_business_results(stage, reason) -> None:
    result = simulate(stage=stage)
    assert result.reason == reason
    assert result.outcome == "blocked"


def test_candidate_invalid_exact13_and_zero_calls() -> None:
    calls = []
    result = design.simulate_admit_014_unified_adapter_contract_design(
        object(), batch_context=None, evaluation_context=None,
        download_result_context=None, stage_authorization_context=Probe(),
        formal_evaluator=lambda **kwargs: calls.append("formal"),
        oracle_callable=lambda **kwargs: calls.append("oracle"),
    )
    assert tuple(vars(result)) == EXPECTED_FIELDS
    assert result.reason == "ADMIT_014_CANDIDATE_RECORD_MAPPING_INVALID"
    assert result.normalized_values == ()
    assert result.validated_candidate_fields == ()
    assert result.consumed_candidate_fields == ()
    assert result.consumed_context_items == ()
    assert calls == []


@pytest.mark.parametrize(
    ("stage", "reason"),
    [
        (Probe(), "CURRENT_STAGE_DOWNLOAD_AUTHORIZED_MISSING"),
        (Probe(error=KeyError(TARGET)), "CURRENT_STAGE_DOWNLOAD_AUTHORIZED_MISSING"),
        (Probe(error=RuntimeError("x")), "STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED"),
        (Probe(error=ValueError("x")), "STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED"),
        (Probe({TARGET: 0}), "CURRENT_STAGE_DOWNLOAD_AUTHORIZED_TYPE_INVALID"),
        (Probe({TARGET: 1}), "CURRENT_STAGE_DOWNLOAD_AUTHORIZED_TYPE_INVALID"),
        (Probe({TARGET: "true"}), "CURRENT_STAGE_DOWNLOAD_AUTHORIZED_TYPE_INVALID"),
        (Probe({TARGET: None}), "CURRENT_STAGE_DOWNLOAD_AUTHORIZED_TYPE_INVALID"),
    ],
)
def test_all_blocked_business_outcomes(stage, reason) -> None:
    assert simulate(stage=stage).reason == reason


@pytest.mark.parametrize(
    ("value", "outcome", "reason", "text"),
    [
        (False, "blocked", "BULK_DOWNLOAD_NOT_AUTHORIZED", "false"),
        (True, "passed", "", "true"),
    ],
)
def test_exact_bool_lowercase_projection(value, outcome, reason, text) -> None:
    stage = Probe({TARGET: value, "current_stage_training_authorized": True, "extra": 1})
    result = simulate(stage=stage)
    assert result.outcome == outcome and result.reason == reason
    assert result.normalized_values == ((TARGET, text),)
    assert result.validated_candidate_fields == ()
    assert result.consumed_candidate_fields == ()
    assert result.consumed_context_items == (TARGET,)
    assert stage.accesses == [TARGET, TARGET]
    assert (stage.iterations, stage.lengths, stage.gets, stage.contains) == (0, 0, 0, 0)


def test_formal_oracle_exact_calls_and_identity() -> None:
    stage = Probe({TARGET: True})
    observed = []

    def formal_call(*, stage_authorization_context):
        observed.append(("formal", stage_authorization_context))
        return formal.evaluate_admit_014(
            stage_authorization_context=stage_authorization_context
        )

    def oracle_call(*, stage_authorization_context):
        observed.append(("oracle", stage_authorization_context))
        return oracle.classify_admit_014_formal_evaluator_interface_design(
            stage_authorization_context=stage_authorization_context
        )

    simulate(stage=stage, formal_evaluator=formal_call, oracle_callable=oracle_call)
    assert observed == [("formal", stage), ("oracle", stage)]
    assert stage.accesses == [TARGET, TARGET]


def test_nonrepeatable_mapping_mismatch_fails_closed() -> None:
    stage = Alternating()
    with pytest.raises(design.AdapterContractDesignError) as captured:
        simulate(stage=stage)
    assert captured.value.code == "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
    assert captured.value.reason == "ADMIT_014_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
    assert stage.count == 2


def test_source_wrong_type_and_oracle_not_called() -> None:
    calls = []
    with pytest.raises(design.AdapterContractDesignError) as captured:
        simulate(
            formal_evaluator=lambda **kwargs: object(),
            oracle_callable=lambda **kwargs: calls.append("oracle"),
        )
    assert captured.value.reason == "ADMIT_014_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"
    assert calls == []


def test_source_storage_reorder_fails_closed() -> None:
    source = formal.evaluate_admit_014(stage_authorization_context=None)
    storage = vars(source)
    reordered = {key: storage[key] for key in reversed(tuple(storage))}
    storage.clear()
    storage.update(reordered)
    with pytest.raises(design.AdapterContractDesignError) as captured:
        simulate(formal_evaluator=lambda **kwargs: source)
    assert captured.value.reason == "ADMIT_014_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"


@pytest.mark.parametrize("oracle_callable", [lambda **kwargs: object(), lambda **kwargs: (_ for _ in ()).throw(RuntimeError("x"))])
def test_oracle_wrong_type_or_exception_fails_closed(oracle_callable) -> None:
    with pytest.raises(design.AdapterContractDesignError) as captured:
        simulate(oracle_callable=oracle_callable)
    assert captured.value.reason == "ADMIT_014_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"


def test_future_registry_and_no_runtime_implementation() -> None:
    assert design.CURRENT_REGISTERED_RULE_ORDER == tuple(
        f"ADMIT_{index:03d}" for index in range(1, 14)
    )
    assert design.FUTURE_REGISTERED_RULE_ORDER == tuple(
        f"ADMIT_{index:03d}" for index in range(1, 15)
    )
    assert design.FUTURE_KNOWN_NOT_REGISTERED == ("ADMIT_015",)
    tree = ast.parse(Path(design.__file__).read_text())
    names = {
        node.name for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "_evaluate_registered_admit_014" not in names
    assert "evaluate_admission_rule" not in names
    checker._verify_registry_identity(design)


def test_issue_precondition_readiness_and_manifest_exactness() -> None:
    manifest = json.loads(
        (ROOT / design.DEFAULT_OUTPUT_ROOT / design.MANIFEST_FILENAME).read_bytes()
    )
    assert manifest["precondition_transition"]["complete_count"] == 50
    assert manifest["precondition_transition"]["remaining_open_precondition_ids"] == ["PRE_049"]
    assert manifest["issue_inventory_row_count"] == 30
    assert manifest["coverage_issue_affected_rules"] == "ADMIT_014|ADMIT_015"
    assert manifest["readiness"] == design.READINESS
    assert manifest["current_permission"] is False
    assert manifest["authorized_admit_014_download_execution_count"] == 0


def test_deterministic_build_and_frozen_sha() -> None:
    first = design.build_artifacts()
    second = design.build_artifacts()
    assert first == second
    assert {
        name: hashlib.sha256(content).hexdigest()
        for name, content in first.items()
    } == OUTPUT_SHA


def test_inode_preserving_noop_materialization() -> None:
    before = {
        name: os.lstat(ROOT / design.DEFAULT_OUTPUT_ROOT / name).st_ino
        for name in design.OUTPUT_FILES
    }
    design.run_covapie_bulk_download_admission_admit_014_unified_adapter_contract_design_gate_v1()
    after = {
        name: os.lstat(ROOT / design.DEFAULT_OUTPUT_ROOT / name).st_ino
        for name in design.OUTPUT_FILES
    }
    assert before == after


def test_local_set_atomic_materialization_and_mismatch(tmp_path: Path) -> None:
    output = tmp_path / "evidence"
    design.run_covapie_bulk_download_admission_admit_014_unified_adapter_contract_design_gate_v1(
        output
    )
    assert set(path.name for path in output.iterdir()) == set(design.OUTPUT_FILES)
    before = {path.name: path.stat().st_ino for path in output.iterdir()}
    design.run_covapie_bulk_download_admission_admit_014_unified_adapter_contract_design_gate_v1(
        output
    )
    assert before == {path.name: path.stat().st_ino for path in output.iterdir()}
    target = output / design.CONTRACT_FILENAME
    target.write_bytes(target.read_bytes() + b"tamper")
    with pytest.raises(ValueError, match="existing output differs"):
        design.run_covapie_bulk_download_admission_admit_014_unified_adapter_contract_design_gate_v1(
            output
        )


def test_output_extra_and_symlink_fail_closed(tmp_path: Path) -> None:
    extra = tmp_path / "extra"
    extra.mkdir()
    (extra / "unexpected").write_text("x")
    with pytest.raises(ValueError, match="output inventory unsafe"):
        design.run_covapie_bulk_download_admission_admit_014_unified_adapter_contract_design_gate_v1(
            extra
        )
    symlink = tmp_path / "symlink"
    symlink.symlink_to(extra, target_is_directory=True)
    with pytest.raises(ValueError, match="output root unsafe"):
        design.run_covapie_bulk_download_admission_admit_014_unified_adapter_contract_design_gate_v1(
            symlink
        )


def test_gpfs_einval_fails_closed_without_residue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "einval"

    def fail(*args):
        raise OSError(errno.EINVAL, os.strerror(errno.EINVAL))

    monkeypatch.setattr(design, "_rename_noreplace", fail)
    with pytest.raises(OSError) as captured:
        design.run_covapie_bulk_download_admission_admit_014_unified_adapter_contract_design_gate_v1(
            output
        )
    assert captured.value.errno == errno.EINVAL
    assert not output.exists()
    assert list(tmp_path.iterdir()) == []


def test_frozen_payload_and_no_os_replace(tmp_path: Path) -> None:
    source = Path(design.__file__).read_text()
    assert "os.replace" not in source
    payloads = design.build_artifacts()
    altered = dict(payloads)
    altered[design.CONTRACT_FILENAME] += b"x"
    plan = design._inspect_output_target_read_only(
        tmp_path / "never-created", ROOT
    )
    with pytest.raises(ValueError, match="frozen output payload SHA drift"):
        design._materialize_set(plan, altered)


def test_protected_paths_and_exact10_inventory() -> None:
    assert all(
        not path.startswith(("data/raw/", "checkpoints/"))
        for path, _ in design.SOURCE_BOUNDARY
    )
    untracked = subprocess.run(
        ("git", "ls-files", "--others", "--exclude-standard"),
        cwd=ROOT, text=True, capture_output=True, check=True,
    ).stdout.splitlines()
    expected = {path.as_posix() for path in checker.EXACT10}
    assert set(untracked) in (set(), expected)


def test_routing_exact42_and_truth_exact61_are_actual_observations() -> None:
    state = design.build_design_state()
    routing = state["routing_rows"]
    truth = state["truth_rows"]
    assert len(routing) == 42
    assert len(truth) == 61
    assert tuple(row["case_id"] for row in routing) == tuple(
        spec["case_id"] for spec in design._routing_case_specs()
    )
    for row in routing:
        assert row["case_passed"] == "true"
        assert row["expected_dispatch_code"] == row["observed_dispatch_code"]
        assert row["expected_reason"] == row["observed_reason"]
        assert row["expected_result_json"] == row["observed_result_json"]
        assert row["formal_call_count"] == row["observed_formal_call_count"]
        assert row["oracle_call_count"] == row["observed_oracle_call_count"]
        assert (
            row["candidate_key_access_count"]
            == row["observed_candidate_key_access_count"]
            == "0"
        )
        assert (
            row["adapter_stage_key_access_count"]
            == row["observed_adapter_stage_key_access_count"]
            == "0"
        )
    for route, row in zip(routing, truth[19:], strict=True):
        assert (
            row["source_result_representation"]
            == route["_source_result_representation"]
        )
        assert (
            row["oracle_result_representation"]
            == route["_oracle_result_representation"]
        )
        assert row["expected_unified_result_json"] == route["expected_result_json"]
        assert row["observed_unified_result_json"] == route["observed_result_json"]
        assert row["observed_unified_result_json"]
        assert row["case_passed"] == route["case_passed"] == "true"
        if route["observed_dispatch_code"]:
            error = json.loads(row["observed_unified_result_json"])
            assert tuple(error) == (
                "code", "admission_rule_id", "known_rule",
                "callable_discovered", "adapter_ready", "reason",
            )


def _mutated_source(mode: str):
    value = formal.evaluate_admit_014(stage_authorization_context=None)
    if mode == "subclass":
        subtype = type("TargetedSourceSubclass", (type(value),), {})
        result = object.__new__(subtype)
        for name in design.STANDALONE_RESULT_FIELDS:
            object.__setattr__(result, name, getattr(value, name))
        return result
    if mode == "storage_reorder":
        storage = vars(value)
        reordered = {name: storage[name] for name in reversed(tuple(storage))}
        storage.clear()
        storage.update(reordered)
    elif mode == "top_level_type":
        object.__setattr__(value, "outcome", 1)
    elif mode == "admission_rule_id":
        object.__setattr__(value, "admission_rule_id", "ADMIT_015")
    elif mode == "evaluator_io":
        object.__setattr__(value, "evaluator_io_used", True)
    elif mode == "outcome_reason":
        object.__setattr__(value, "outcome", "passed")
    elif mode == "canonical":
        object.__setattr__(
            value, "canonical_stage_authorization_record",
            (("unexpected", True),),
        )
    elif mode == "validated_tuple":
        object.__setattr__(value, "validated_stage_authorization_fields", (1,))
    elif mode == "consumed_tuple":
        object.__setattr__(value, "consumed_stage_authorization_fields", (1,))
    return value


@pytest.mark.parametrize(
    ("mode", "reason"),
    [
        ("wrong_type", "ADMIT_014_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"),
        ("subclass", "ADMIT_014_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID"),
        ("storage_reorder", "ADMIT_014_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        ("top_level_type", "ADMIT_014_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        ("admission_rule_id", "ADMIT_014_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        ("evaluator_io", "ADMIT_014_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        ("outcome_reason", "ADMIT_014_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        ("canonical", "ADMIT_014_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        ("validated_tuple", "ADMIT_014_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
        ("consumed_tuple", "ADMIT_014_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"),
    ],
)
def test_source_exact9_full_negative_contract(mode: str, reason: str) -> None:
    oracle_calls = []
    value = object() if mode == "wrong_type" else _mutated_source(mode)
    with pytest.raises(design.AdapterContractDesignError) as captured:
        simulate(
            formal_evaluator=lambda **kwargs: value,
            oracle_callable=lambda **kwargs: oracle_calls.append(kwargs),
        )
    assert captured.value.code == "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
    assert captured.value.reason == reason
    assert oracle_calls == []


def _mutated_oracle(mode: str):
    value = oracle.classify_admit_014_formal_evaluator_interface_design(
        stage_authorization_context=None
    )
    if mode == "subclass":
        subtype = type("TargetedOracleSubclass", (type(value),), {})
        result = object.__new__(subtype)
        for name in design.STANDALONE_RESULT_FIELDS:
            object.__setattr__(result, name, getattr(value, name))
        return result
    if mode == "storage_reorder":
        storage = vars(value)
        reordered = {name: storage[name] for name in reversed(tuple(storage))}
        storage.clear()
        storage.update(reordered)
    elif mode == "top_level_type":
        object.__setattr__(value, "outcome", 1)
    elif mode == "admission_rule_id":
        object.__setattr__(value, "admission_rule_id", "ADMIT_015")
    return value


@pytest.mark.parametrize(
    "mode",
    [
        "wrong_type", "subclass", "storage_reorder", "top_level_type",
        "admission_rule_id", "value_mismatch", "exception",
    ],
)
def test_oracle_exact9_full_negative_contract(mode: str) -> None:
    if mode == "wrong_type":
        callable_ = lambda **kwargs: object()
    elif mode == "value_mismatch":
        callable_ = lambda **kwargs: (
            oracle.classify_admit_014_formal_evaluator_interface_design(
                stage_authorization_context=object()
            )
        )
    elif mode == "exception":
        callable_ = lambda **kwargs: (_ for _ in ()).throw(RuntimeError("x"))
    else:
        value = _mutated_oracle(mode)
        callable_ = lambda **kwargs: value
    with pytest.raises(design.AdapterContractDesignError) as captured:
        simulate(oracle_callable=callable_)
    assert captured.value.code == "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
    assert (
        captured.value.reason
        == "ADMIT_014_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
    )


@pytest.mark.parametrize("fault", ["duplicate", "unexpected"])
def test_checker_rejects_actual_duplicate_or_unexpected_oracle_call(
    monkeypatch: pytest.MonkeyPatch, fault: str,
) -> None:
    routing = design.build_design_state()["routing_rows"]
    original = design.simulate_admit_014_unified_adapter_contract_design

    def faulty_simulator(
        candidate_record: object,
        *,
        oracle_callable,
        **kwargs,
    ):
        if fault == "unexpected":
            oracle_callable(
                stage_authorization_context=kwargs[
                    "stage_authorization_context"
                ]
            )
            return original(
                candidate_record,
                oracle_callable=oracle_callable,
                **kwargs,
            )

        def duplicate_oracle(**oracle_kwargs):
            first = oracle_callable(**oracle_kwargs)
            oracle_callable(**oracle_kwargs)
            return first

        return original(
            candidate_record,
            oracle_callable=duplicate_oracle,
            **kwargs,
        )

    monkeypatch.setattr(
        design,
        "simulate_admit_014_unified_adapter_contract_design",
        faulty_simulator,
    )
    with pytest.raises(ValueError, match="independent routing case failed"):
        checker._verify_routing(design, routing)


def test_manifest_real_blob_and_signature_evidence() -> None:
    payloads = design.build_artifacts()
    manifest = checker._parse_manifest_exact(payloads[design.MANIFEST_FILENAME])
    assert manifest["future_adapter_handler_signature"] == (
        design.FUTURE_HANDLER_SIGNATURE_TEXT
    )
    assert manifest["future_adapter_handler_signature_evidence"] == {
        "annotations": {
            "batch_context": "object",
            "candidate_record": "object",
            "download_result_context": "object",
            "evaluation_context": "object",
            "stage_authorization_context": "object",
        },
        "has_varargs": False,
        "has_varkw": False,
        "parameter_kinds": [
            "POSITIONAL_OR_KEYWORD", "KEYWORD_ONLY", "KEYWORD_ONLY",
            "KEYWORD_ONLY", "KEYWORD_ONLY",
        ],
        "parameter_order": [
            "candidate_record", "batch_context", "evaluation_context",
            "download_result_context", "stage_authorization_context",
        ],
        "required_count": 5,
        "return_annotation": "UnifiedAdmissionRuleEvaluation",
        "signature_text": design.FUTURE_HANDLER_SIGNATURE_TEXT,
    }
    for row in manifest["source_input_verification"]:
        assert type(row["base_tree_blob"]) is str
        assert type(row["index_blob"]) is str
        assert len(row["base_tree_blob"]) == len(row["index_blob"]) == 40
        assert row["base_tree_blob"] == row["index_blob"]
        assert row["base_tree_mode"] == row["index_mode"]
        assert row["index_stage"] == 0
        assert row["base_tree_blob"] is not True


def _write_exact6(root: Path, payloads: Mapping[str, bytes]) -> None:
    root.mkdir(parents=True)
    for name, content in payloads.items():
        (root / name).write_bytes(content)


@pytest.mark.parametrize(
    "race",
    [
        "same_byte_leaf_replacement", "in_place_mutation",
        "parent_replacement", "repo_root_replacement", "stat_open_race",
    ],
)
def test_checker_pinned_source_real_races_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, race: str,
) -> None:
    repo = tmp_path / "repo"
    source = repo / "evidence/source.txt"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"frozen source\n")
    original_read = checker.os.read
    original_open = checker.os.open
    mutated = False

    def mutate() -> None:
        nonlocal mutated
        if mutated:
            return
        mutated = True
        if race == "same_byte_leaf_replacement" or race == "stat_open_race":
            replacement = source.with_name("replacement")
            replacement.write_bytes(source.read_bytes())
            os.rename(replacement, source)
        elif race == "in_place_mutation":
            with source.open("ab") as stream:
                stream.write(b"mutation")
        elif race == "parent_replacement":
            os.rename(source.parent, repo / "evidence-old")
            source.parent.mkdir()
            source.write_bytes(b"frozen source\n")
        else:
            os.rename(repo, tmp_path / "repo-old")
            source.parent.mkdir(parents=True)
            source.write_bytes(b"frozen source\n")

    def racing_read(descriptor: int, size: int) -> bytes:
        data = original_read(descriptor, size)
        if data and race != "stat_open_race":
            mutate()
        return data

    def racing_open(path, *args, **kwargs):
        if path == source.name and race == "stat_open_race":
            mutate()
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(checker.os, "read", racing_read)
    monkeypatch.setattr(checker.os, "open", racing_open)
    with pytest.raises(ValueError):
        checker._pinned_source_read(repo, Path("evidence/source.txt"))
    assert mutated


def test_checker_pinned_output_normal_exact6(tmp_path: Path) -> None:
    payloads = design.build_artifacts()
    root = tmp_path / "normal"
    _write_exact6(root, payloads)
    assert checker._pinned_outputs(root) == payloads


@pytest.mark.parametrize(
    "race",
    [
        "leaf_replacement", "root_replacement", "final_extra",
        "final_missing", "parent_replacement",
    ],
)
def test_checker_pinned_output_real_races_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, race: str,
) -> None:
    payloads = design.build_artifacts()
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
            "leaf_replacement", "root_replacement", "parent_replacement",
        }:
            mutated = True
            if race == "leaf_replacement":
                target = root / design.CONTRACT_FILENAME
                replacement = root / "same-byte-replacement"
                replacement.write_bytes(target.read_bytes())
                os.rename(replacement, target)
            elif race == "root_replacement":
                os.rename(root, parent / "old-out")
                _write_exact6(root, payloads)
            else:
                os.rename(parent, tmp_path / "old-parent")
                _write_exact6(root, payloads)
        return data

    def racing_listdir(descriptor: int) -> list[str]:
        nonlocal inventory_count, mutated
        inventory_count += 1
        if inventory_count == 2 and not mutated:
            if race == "final_extra":
                mutated = True
                (root / "seventh.csv").write_bytes(b"extra\n")
            elif race == "final_missing":
                mutated = True
                (root / design.CONTRACT_FILENAME).unlink()
        return original_listdir(descriptor)

    monkeypatch.setattr(checker.os, "read", racing_read)
    monkeypatch.setattr(checker.os, "listdir", racing_listdir)
    with pytest.raises((ValueError, FileNotFoundError)):
        checker._pinned_outputs(root)
    assert mutated


def test_checker_manifest_duplicate_missing_extra_reorder_rejected() -> None:
    data = design.build_artifacts()[design.MANIFEST_FILENAME]
    text = data.decode()
    duplicate = text.replace(
        '{\n  "Admit014EvaluationResult_implemented"',
        '{\n  "Admit014EvaluationResult_implemented": true,\n'
        '  "Admit014EvaluationResult_implemented"',
        1,
    ).encode()
    with pytest.raises(ValueError, match="duplicate manifest key"):
        checker._parse_manifest_exact(duplicate)
    for case in ("missing", "extra", "reorder"):
        value = json.loads(data)
        if case == "missing":
            value.pop(next(iter(value)))
        elif case == "extra":
            value["unexpected"] = True
        else:
            value = dict(reversed(tuple(value.items())))
        tampered = (json.dumps(value, indent=2) + "\n").encode()
        with pytest.raises(ValueError, match="top-level"):
            checker._parse_manifest_exact(tampered)


@pytest.mark.parametrize(
    "name",
    [
        "forbidden_envelope_contract", "stage_authorization_contract",
        "candidate_record_contract", "candidate_invalid_call_counts",
        "exact13_projection", "precondition_transition", "readiness",
        "output_sha256", "source_input_sha256",
        "future_adapter_handler_signature_evidence",
    ],
)
@pytest.mark.parametrize("case", ["missing", "extra", "reorder"])
def test_checker_manifest_nested_exact_schema_rejected(
    name: str, case: str,
) -> None:
    value = json.loads(design.build_artifacts()[design.MANIFEST_FILENAME])
    nested = value[name]
    if case == "missing":
        nested.pop(next(iter(nested)))
    elif case == "extra":
        nested["unexpected"] = True
    else:
        value[name] = dict(reversed(tuple(nested.items())))
    data = (json.dumps(value, indent=2) + "\n").encode()
    with pytest.raises(ValueError, match="nested schema/order"):
        checker._parse_manifest_exact(data)


@pytest.mark.parametrize("case", ["missing", "extra", "reorder"])
def test_checker_manifest_source_row_exact_schema_rejected(case: str) -> None:
    value = json.loads(design.build_artifacts()[design.MANIFEST_FILENAME])
    row = value["source_input_verification"][0]
    if case == "missing":
        row.pop(next(iter(row)))
    elif case == "extra":
        row["unexpected"] = True
    else:
        value["source_input_verification"][0] = dict(
            reversed(tuple(row.items()))
        )
    data = (json.dumps(value, indent=2) + "\n").encode()
    with pytest.raises(ValueError, match="source verification schema/order"):
        checker._parse_manifest_exact(data)


def _rewrite_csv(
    content: bytes, row_index: int, field: str, value: str,
) -> bytes:
    source = io.StringIO(content.decode(), newline="")
    reader = csv.DictReader(source)
    rows = list(reader)
    rows[row_index][field] = value
    target = io.StringIO(newline="")
    writer = csv.DictWriter(
        target, fieldnames=reader.fieldnames, lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return target.getvalue().encode()


@pytest.mark.parametrize(
    "tamper",
    [
        "routing", "truth", "source_blob", "readiness", "handler_signature",
        "call_count", "precondition", "projection",
    ],
)
def test_checker_synchronized_manifest_tamper_still_rejected(
    monkeypatch: pytest.MonkeyPatch, tamper: str,
) -> None:
    payloads = dict(design.build_artifacts())
    manifest = json.loads(payloads[design.MANIFEST_FILENAME])
    if tamper == "routing":
        payloads[design.ROUTING_FILENAME] = _rewrite_csv(
            payloads[design.ROUTING_FILENAME],
            0, "observed_reason", "SYNCHRONIZED_TAMPER",
        )
        manifest["output_sha256"][design.ROUTING_FILENAME] = hashlib.sha256(
            payloads[design.ROUTING_FILENAME]
        ).hexdigest()
    elif tamper == "truth":
        payloads[design.TRUTH_FILENAME] = _rewrite_csv(
            payloads[design.TRUTH_FILENAME],
            0, "observed_unified_result_json", "{}",
        )
        manifest["output_sha256"][design.TRUTH_FILENAME] = hashlib.sha256(
            payloads[design.TRUTH_FILENAME]
        ).hexdigest()
    elif tamper == "source_blob":
        manifest["source_input_verification"][0]["base_tree_blob"] = "0" * 40
        manifest["source_input_verification"][0]["index_blob"] = "0" * 40
    elif tamper == "readiness":
        manifest["readiness"]["admit_014_unified_adapter_implemented"] = True
    elif tamper == "handler_signature":
        manifest["future_adapter_handler_signature"] = "tampered"
        manifest["future_adapter_handler_signature_evidence"][
            "signature_text"
        ] = "tampered"
    elif tamper == "call_count":
        manifest["candidate_invalid_call_counts"]["formal"] = 1
    elif tamper == "precondition":
        manifest["precondition_transition"]["complete_count"] = 49
    else:
        manifest["exact13_projection"]["validated_candidate_fields"] = [
            "unexpected"
        ]
    payloads[design.MANIFEST_FILENAME] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode()
    monkeypatch.setattr(
        checker,
        "OUTPUT_SHA256",
        {name: hashlib.sha256(data).hexdigest() for name, data in payloads.items()},
    )
    source_records = checker.verify_sources()
    module = checker.import_production()
    with pytest.raises(ValueError):
        checker._verify_artifact_payloads(payloads, module, source_records)


def _run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *args), cwd=repo, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )


def _make_lifecycle_repo(
    root: Path, *, tracked: bool = False,
) -> tuple[Path, str]:
    root.mkdir(parents=True)
    assert _run_git(root, "init", "-q").returncode == 0
    assert _run_git(root, "config", "user.email", "test@example.invalid").returncode == 0
    assert _run_git(root, "config", "user.name", "CovaPIE Test").returncode == 0
    (root / "README").write_text("base\n", encoding="utf-8")
    assert _run_git(root, "add", "--", "README").returncode == 0
    assert _run_git(root, "commit", "-qm", "base").returncode == 0
    base = _run_git(root, "rev-parse", "HEAD").stdout.strip()
    for path in checker.EXACT10:
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"{path.as_posix()}\n", encoding="utf-8")
    if tracked:
        assert _run_git(
            root, "add", "--", *(path.as_posix() for path in checker.EXACT10)
        ).returncode == 0
        assert _run_git(root, "commit", "-qm", "stage").returncode == 0
    return root, base


def test_lifecycle_pre_commit_and_tracked_clean_post_commit(
    tmp_path: Path,
) -> None:
    pre, pre_base = _make_lifecycle_repo(tmp_path / "pre")
    assert checker._lifecycle(pre, pre_base) == "pre_commit"
    post, post_base = _make_lifecycle_repo(tmp_path / "post", tracked=True)
    assert checker._lifecycle(post, post_base) == "post_commit"


@pytest.mark.parametrize(
    "case",
    [
        "mixed", "staged", "dirty", "missing", "untracked_ignored",
        "tracked_ignored", "check_ignore_128", "extra_top_level",
        "extra_derived_root", "extra_untracked", "seventh_exact6", "symlink",
        "forbidden_suffix", "oversized", "base_nonancestor",
    ],
)
def test_lifecycle_negative_states_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str,
) -> None:
    tracked = case in {"dirty", "tracked_ignored"}
    repo, base = _make_lifecycle_repo(tmp_path / case, tracked=tracked)
    if case == "mixed":
        first = checker.EXACT10[0]
        assert _run_git(repo, "add", "--", first.as_posix()).returncode == 0
        assert _run_git(repo, "commit", "-qm", "one candidate").returncode == 0
    elif case == "staged":
        assert _run_git(
            repo, "add", "--", checker.EXACT10[0].as_posix()
        ).returncode == 0
    elif case == "dirty":
        with (repo / checker.EXACT10[0]).open("a", encoding="utf-8") as stream:
            stream.write("dirty\n")
    elif case == "missing":
        (repo / checker.EXACT10[0]).unlink()
    elif case in {"untracked_ignored", "tracked_ignored"}:
        (repo / ".gitignore").write_text(
            checker.EXACT10[0].as_posix() + "\n", encoding="utf-8"
        )
    elif case == "check_ignore_128":
        original = checker._git_at

        def failing(root: Path, *arguments: str):
            if arguments[:3] == ("check-ignore", "--no-index", "-q"):
                return subprocess.CompletedProcess(arguments, 128, "", "failure")
            return original(root, *arguments)

        monkeypatch.setattr(checker, "_git_at", failing)
    elif case == "extra_top_level":
        extra = (
            repo
            / "docs"
            / "extra_admit_014_unified_adapter_contract_evidence.md"
        )
        extra.write_text("extra\n", encoding="utf-8")
    elif case == "extra_derived_root":
        extra = (
            repo
            / "data/derived/covalent_small"
            / "covapie_bulk_download_admission_admit_014_"
            "unified_adapter_contract_extra"
        )
        extra.mkdir()
    elif case == "extra_untracked":
        (repo / "unrelated-untracked.txt").write_text(
            "unexpected\n", encoding="utf-8"
        )
    elif case in {"seventh_exact6", "forbidden_suffix"}:
        suffix = "seventh.csv" if case == "seventh_exact6" else "seventh.tmp"
        (repo / checker.STAGE / suffix).write_text("extra\n", encoding="utf-8")
    elif case == "symlink":
        target = repo / checker.EXACT10[0]
        target.unlink()
        target.symlink_to(repo / "README")
    elif case == "oversized":
        with (repo / checker.EXACT10[0]).open("r+b") as stream:
            stream.truncate(checker.MAX_CANDIDATE_BYTES + 1)
    elif case == "base_nonancestor":
        base = "0" * 40
    with pytest.raises(ValueError):
        checker._lifecycle(repo, base)


def _replace_materialized_root(
    root: Path, payloads: Mapping[str, bytes], suffix: str,
) -> None:
    os.rename(root, root.with_name(f"{root.name}-{suffix}"))
    _write_exact6(root, payloads)


@pytest.mark.parametrize(
    "phase",
    [
        "after_rename_before_first_binding",
        "after_first_binding_before_parent_fsync",
        "after_parent_fsync", "after_root_fsync", "extra_leaf",
        "missing_leaf", "output_parent_replacement",
    ],
)
def test_materializer_real_destination_binding_races_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, phase: str,
) -> None:
    payloads = design.build_artifacts()
    parent = tmp_path / "parent"
    parent.mkdir()
    root = parent / "out"
    mutated = False
    original_rename = design._rename_noreplace
    original_binding = design._assert_destination_name_binding
    original_verify = design._verify_destination_binding
    original_fsync = design.os.fsync
    parent_identity = os.stat(parent)

    if phase == "after_rename_before_first_binding":
        def racing_rename(parent_fd: int, source: str, target: str) -> None:
            nonlocal mutated
            original_rename(parent_fd, source, target)
            mutated = True
            _replace_materialized_root(root, payloads, "old-immediate")

        monkeypatch.setattr(design, "_rename_noreplace", racing_rename)
    elif phase in {
        "after_first_binding_before_parent_fsync",
        "output_parent_replacement",
    }:
        calls = 0

        def racing_binding(*args, **kwargs) -> None:
            nonlocal calls, mutated
            original_binding(*args, **kwargs)
            calls += 1
            if calls == 1:
                mutated = True
                if phase == "after_first_binding_before_parent_fsync":
                    _replace_materialized_root(root, payloads, "old-first")
                else:
                    os.rename(parent, tmp_path / "old-parent")
                    _write_exact6(root, payloads)

        monkeypatch.setattr(
            design, "_assert_destination_name_binding", racing_binding
        )
    elif phase in {"after_parent_fsync", "after_root_fsync"}:
        def racing_fsync(descriptor: int) -> None:
            nonlocal mutated
            original_fsync(descriptor)
            if mutated or not root.exists():
                return
            item = os.fstat(descriptor)
            if phase == "after_parent_fsync":
                matches = (
                    item.st_dev, item.st_ino
                ) == (parent_identity.st_dev, parent_identity.st_ino)
            else:
                root_item = os.stat(root)
                matches = (
                    item.st_dev, item.st_ino
                ) == (root_item.st_dev, root_item.st_ino)
            if matches:
                mutated = True
                _replace_materialized_root(
                    root, payloads,
                    "old-parent-fsync"
                    if phase == "after_parent_fsync"
                    else "old-root-fsync",
                )

        monkeypatch.setattr(design.os, "fsync", racing_fsync)
    else:
        def racing_verify(*args, **kwargs) -> None:
            nonlocal mutated
            if not mutated:
                mutated = True
                if phase == "extra_leaf":
                    (root / "seventh.csv").write_bytes(b"extra\n")
                else:
                    (root / design.CONTRACT_FILENAME).unlink()
            original_verify(*args, **kwargs)

        monkeypatch.setattr(design, "_verify_destination_binding", racing_verify)
    with pytest.raises((ValueError, FileNotFoundError)):
        design.run_covapie_bulk_download_admission_admit_014_unified_adapter_contract_design_gate_v1(
            root
        )
    assert mutated
    assert not list(tmp_path.rglob(".admit014-adapter-stage-*"))


def test_materializer_real_eexist_race_fails_closed_without_residue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    payloads = design.build_artifacts()
    root = tmp_path / "out"
    original = design._rename_noreplace
    raced = False

    def concurrent_publish(
        parent_fd: int, source: str, target: str,
    ) -> None:
        nonlocal raced
        raced = True
        _write_exact6(root, payloads)
        original(parent_fd, source, target)

    monkeypatch.setattr(design, "_rename_noreplace", concurrent_publish)
    with pytest.raises(OSError) as captured:
        design.run_covapie_bulk_download_admission_admit_014_unified_adapter_contract_design_gate_v1(
            root
        )
    assert captured.value.errno == errno.EEXIST
    assert raced
    assert set(path.name for path in root.iterdir()) == set(design.OUTPUT_FILES)
    assert not list(tmp_path.rglob(".admit014-adapter-stage-*"))
