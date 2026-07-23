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
from types import SimpleNamespace

import pytest

from covalent_ext import (
    covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_design_gate
    as oracle,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_013_rule_logic_interface as standalone,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_013_unified_adapter_contract_design_gate
    as design,
)
from covalent_ext import (
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012
    as runtime,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "scripts/check_covapie_bulk_download_admission_admit_013_unified_adapter_contract_v1.py"
OUTPUT_ROOT = ROOT / "data/derived/covalent_small" / design.STAGE
SHA_A = "0123456789abcdef" * 4
SHA_B = "abcdef0123456789" * 4


def checker_module():
    spec = importlib.util.spec_from_file_location("admit013_adapter_checker_test", CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CountingMapping(Mapping):
    def __init__(self, values=(), *, failures=()):
        self.values = dict(values)
        self.failures = dict(failures)
        self.lookups: list[str] = []

    def __getitem__(self, key):
        self.lookups.append(key)
        failure = self.failures.get(key)
        if failure is not None:
            raise failure
        return self.values[key]

    def __iter__(self):
        return iter(self.values)

    def __len__(self):
        return len(self.values)


class CandidateBomb(Mapping):
    def __init__(self):
        self.accesses = 0

    def __getitem__(self, key):
        self.accesses += 1
        raise AssertionError("candidate key accessed")

    def __iter__(self):
        self.accesses += 1
        raise AssertionError("candidate iterated")

    def __len__(self):
        return 1


def valid_download(extra=()):
    return CountingMapping((
        ("download_result_status", "success"),
        ("observed_http_status", 200),
        ("observed_content_length_bytes", 10),
        ("observed_sha256", SHA_A),
        *extra,
    ))


def valid_authority(extra=()):
    return CountingMapping((
        ("expected_content_length_bytes", 10),
        ("expected_sha256", SHA_A),
        ("explicit_integrity_verdict", "verified"),
        *extra,
    ))


def route(candidate=None, evaluation=None, download=None, **overrides):
    arguments = {
        "candidate_record": CandidateBomb() if candidate is None else candidate,
        "batch_context": None,
        "evaluation_context": valid_authority() if evaluation is None else evaluation,
        "download_result_context": valid_download() if download is None else download,
        "stage_authorization_context": None,
    }
    arguments.update(overrides)
    return design.simulate_admit_013_unified_adapter_design(**arguments)


def read_csv(name):
    with (OUTPUT_ROOT / name).open(newline="") as stream:
        return list(csv.DictReader(stream))


def copied_outputs(tmp_path: Path) -> Path:
    target = tmp_path / design.STAGE
    shutil.copytree(OUTPUT_ROOT, target)
    return target


def test_base_identity_ancestor_and_canonical_runtime():
    assert design.EXPECTED_BASE_COMMIT == "da7bf5258365ecebde20ba1f09081b075312ebaf"
    assert design.EXPECTED_BASE_PARENT == "79e63dce368722b126ad21208a3de13f7ea4b6df"
    assert design.EXPECTED_BASE_TREE == "63fa16eeb3ccb53b0d900b2117ef91623f89e7c6"
    assert sys.implementation.name == "cpython"
    assert sys.version_info[:3] == (3, 10, 4)
    subprocess.run(
        ("git", "merge-base", "--is-ancestor", design.EXPECTED_BASE_COMMIT, "HEAD"),
        cwd=ROOT, check=True,
    )


def test_source_before_output_and_exact19_boundary(monkeypatch):
    events = []
    original_build = design.build_design_state
    original_inspect = design._inspect_output_target_read_only
    monkeypatch.setattr(design, "build_design_state", lambda *a, **k: (events.append("source"), original_build(*a, **k))[1])
    monkeypatch.setattr(design, "_inspect_output_target_read_only", lambda *a, **k: (events.append("output"), original_inspect(*a, **k))[1])
    design.run_covapie_bulk_download_admission_admit_013_unified_adapter_contract_design_gate_v1()
    assert events == ["source", "output"]
    assert len(design.SOURCE_BOUNDARY) == 19
    assert all(not path.startswith(("data/raw/", "checkpoints/")) for path, _ in design.SOURCE_BOUNDARY)


def test_shared_exact13_schema_identity_and_no_widening():
    assert design.RESULT_FIELDS == runtime.RESULT_FIELDS
    assert tuple(field.name for field in fields(runtime.UnifiedAdmissionRuleEvaluation)) == design.RESULT_FIELDS
    result = route()
    runtime_result = runtime.UnifiedAdmissionRuleEvaluation(
        *(getattr(result, name) for name in design.RESULT_FIELDS)
    )
    assert type(runtime_result) is runtime.UnifiedAdmissionRuleEvaluation
    assert all(type(pair) is tuple and all(type(value) is str for value in pair) for pair in result.normalized_values)


def test_five_envelope_design_signature_and_frozen_routing_order():
    parameters = inspect.signature(design.simulate_admit_013_unified_adapter_design).parameters
    assert tuple(parameters) == (
        "candidate_record", "batch_context", "evaluation_context",
        "download_result_context", "stage_authorization_context",
        "formal_evaluator", "oracle_callable",
    )
    assert design.CONTEXT_ROUTING_ORDER == (
        "batch_context_must_be_none", "evaluation_context_mapping_validation",
        "download_result_context_mapping_validation",
        "stage_authorization_context_must_be_none",
        "candidate_record_mapping_validation",
        "download_result_exact4_required_lookup_first_missing_stops",
        "integrity_authority_exact3_optional_lookup_all",
        "formal_evaluator_exactly_once", "standalone_source_exact12_validation",
        "independent_design_oracle_exactly_once",
        "full_exact12_exact_type_value_equality",
        "typed_to_string_exact13_projection",
    )


@pytest.mark.parametrize("name,value,reason", (
    ("batch_context", object(), "ADMIT_013_BATCH_CONTEXT_MUST_BE_NONE"),
    ("evaluation_context", None, "ADMIT_013_EVALUATION_CONTEXT_MAPPING_REQUIRED"),
    ("download_result_context", None, "ADMIT_013_DOWNLOAD_RESULT_CONTEXT_MAPPING_REQUIRED"),
    ("stage_authorization_context", object(), "ADMIT_013_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE"),
))
def test_envelope_failures_have_exact_error_flags_and_zero_calls(name, value, reason):
    calls = []
    with pytest.raises(design.AdapterContractDesignError) as captured:
        route(**{name: value}, formal_evaluator=lambda **kwargs: calls.append(kwargs))
    assert captured.value.as_dict() == {
        "code": "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID",
        "admission_rule_id": "ADMIT_013", "known_rule": True,
        "callable_discovered": True, "adapter_ready": True, "reason": reason,
    }
    assert calls == []


def test_batch_and_stage_failure_precedence_avoids_later_mapping_access():
    evaluation = CountingMapping(failures={"expected_content_length_bytes": AssertionError()})
    download = CountingMapping(failures={"download_result_status": AssertionError()})
    with pytest.raises(design.AdapterContractDesignError) as batch:
        route(evaluation=evaluation, download=download, batch_context=object(), stage_authorization_context=object())
    assert batch.value.reason == design.CONTEXT_REASONS["batch_context"]
    assert evaluation.lookups == download.lookups == []
    with pytest.raises(design.AdapterContractDesignError) as stage:
        route(evaluation=evaluation, download=download, stage_authorization_context=object())
    assert stage.value.reason == design.CONTEXT_REASONS["stage_authorization_context"]
    assert evaluation.lookups == download.lookups == []


def test_candidate_invalid_exact13_has_zero_candidate_context_and_calls():
    evaluation = valid_authority()
    download = valid_download()
    calls = []
    result = route(
        candidate=object(), evaluation=evaluation, download=download,
        formal_evaluator=lambda **kwargs: calls.append(kwargs),
        oracle_callable=lambda **kwargs: calls.append(kwargs),
    )
    assert result == design.candidate_invalid_exact13_for_design()
    assert result.normalized_values == result.validated_candidate_fields == ()
    assert result.consumed_candidate_fields == result.consumed_context_items == ()
    assert evaluation.lookups == download.lookups == calls == []


def test_candidate_mapping_has_exact_zero_key_access():
    candidate = CandidateBomb()
    result = route(candidate=candidate)
    assert result.outcome == "passed"
    assert candidate.accesses == 0


@pytest.mark.parametrize("missing_index", range(4))
def test_each_required_first_missing_stops_later_and_skips_authority(missing_index):
    values = list(zip(design.DOWNLOAD_RESULT_FIELDS, ("success", 200, 10, SHA_A)))
    values.pop(missing_index)
    download = CountingMapping(values)
    evaluation = valid_authority()
    formal_calls = []
    oracle_calls = []
    result = route(
        evaluation=evaluation, download=download,
        formal_evaluator=lambda **kwargs: (formal_calls.append(kwargs), standalone.evaluate_admit_013(**kwargs))[1],
        oracle_callable=lambda **kwargs: (oracle_calls.append(kwargs), oracle.classify_admit_013_formal_evaluator_interface_design(**kwargs))[1],
    )
    assert download.lookups == list(design.DOWNLOAD_RESULT_FIELDS[:missing_index + 1])
    assert evaluation.lookups == []
    assert tuple(formal_calls[0]) == design.DOWNLOAD_RESULT_FIELDS[:missing_index]
    assert formal_calls == oracle_calls
    assert result.reason == standalone.MISSING_REASONS[missing_index]


def test_required_non_keyerror_is_routing_failure_and_zero_calls():
    download = CountingMapping(failures={"download_result_status": RuntimeError("boom")})
    calls = []
    with pytest.raises(design.AdapterContractDesignError) as captured:
        route(download=download, formal_evaluator=lambda **kwargs: calls.append(kwargs))
    assert captured.value.reason == "ADMIT_013_DOWNLOAD_RESULT_CONTEXT_LOOKUP_FAILED"
    assert captured.value.adapter_ready is True
    assert calls == []


@pytest.mark.parametrize("missing_name", design.INTEGRITY_AUTHORITY_FIELDS)
def test_each_authority_missing_is_optional_and_all_later_keys_are_looked_up(missing_name):
    values = [("expected_content_length_bytes", 10), ("expected_sha256", SHA_A), ("explicit_integrity_verdict", "verified")]
    values = [pair for pair in values if pair[0] != missing_name]
    evaluation = CountingMapping(values)
    result = route(evaluation=evaluation)
    assert evaluation.lookups == list(design.INTEGRITY_AUTHORITY_FIELDS)
    assert missing_name not in dict(result.normalized_values)
    assert result.consumed_context_items == design.INTEGRITY_AUTHORITY_FIELDS


def test_all_authority_missing_is_legal_and_later_lookups_continue():
    evaluation = CountingMapping()
    result = route(evaluation=evaluation)
    assert evaluation.lookups == list(design.INTEGRITY_AUTHORITY_FIELDS)
    assert result.reason == "INTEGRITY_AUTHORITY_MISSING"
    assert result.normalized_values == (
        ("download_result_status", "success"), ("observed_http_status", "200"),
        ("observed_content_length_bytes", "10"), ("observed_sha256", SHA_A),
    )


def test_authority_non_keyerror_is_routing_failure():
    evaluation = CountingMapping(failures={"expected_content_length_bytes": RuntimeError("boom")})
    with pytest.raises(design.AdapterContractDesignError) as captured:
        route(evaluation=evaluation)
    assert captured.value.reason == "ADMIT_013_EVALUATION_CONTEXT_LOOKUP_FAILED"
    assert captured.value.adapter_ready is True


def test_original_value_identity_is_preserved_to_formal_and_oracle():
    status, http, content, sha = "success", 200, 10, SHA_A
    expected_length, expected_sha, verdict = 10, SHA_A, "verified"
    formal_calls, oracle_calls = [], []
    route(
        download=CountingMapping(zip(design.DOWNLOAD_RESULT_FIELDS, (status, http, content, sha))),
        evaluation=CountingMapping(zip(design.INTEGRITY_AUTHORITY_FIELDS, (expected_length, expected_sha, verdict))),
        formal_evaluator=lambda **kwargs: (formal_calls.append(kwargs), standalone.evaluate_admit_013(**kwargs))[1],
        oracle_callable=lambda **kwargs: (oracle_calls.append(kwargs), oracle.classify_admit_013_formal_evaluator_interface_design(**kwargs))[1],
    )
    for name, value in zip((*design.DOWNLOAD_RESULT_FIELDS, *design.INTEGRITY_AUTHORITY_FIELDS), (status, http, content, sha, expected_length, expected_sha, verdict)):
        assert formal_calls[0][name] is value
        assert oracle_calls[0][name] is value


def test_formal_and_oracle_exactly_once_and_formal_exception_propagates():
    formal_calls, oracle_calls = [], []
    route(
        formal_evaluator=lambda **kwargs: (formal_calls.append(kwargs), standalone.evaluate_admit_013(**kwargs))[1],
        oracle_callable=lambda **kwargs: (oracle_calls.append(kwargs), oracle.classify_admit_013_formal_evaluator_interface_design(**kwargs))[1],
    )
    assert len(formal_calls) == len(oracle_calls) == 1
    with pytest.raises(RuntimeError, match="formal boom"):
        route(
            formal_evaluator=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("formal boom")),
            oracle_callable=lambda **kwargs: pytest.fail("oracle called"),
        )


def _mutated_source(*, reverse=False, **changes):
    baseline = standalone.evaluate_admit_013(
        download_result_status="success", observed_http_status=200,
        observed_content_length_bytes=10, observed_sha256=SHA_A,
        expected_sha256=SHA_A,
    )
    value = object.__new__(standalone.Admit013EvaluationResult)
    names = reversed(design.STANDALONE_RESULT_FIELDS) if reverse else design.STANDALONE_RESULT_FIELDS
    for name in names:
        object.__setattr__(value, name, changes.get(name, getattr(baseline, name)))
    return value


def test_source_exact_type_subclass_storage_and_invariant_rejections():
    valid = _mutated_source()
    assert design.validate_source_shape_and_invariants_for_design(valid).accepted

    class ResultSubclass(standalone.Admit013EvaluationResult):
        pass

    subclass = object.__new__(ResultSubclass)
    for name in design.STANDALONE_RESULT_FIELDS:
        object.__setattr__(subclass, name, getattr(valid, name))
    decision = design.validate_source_shape_and_invariants_for_design(subclass)
    assert (decision.reason, decision.adapter_ready) == (design.SOURCE_TYPE_REASON, False)
    for invalid in (
        _mutated_source(reverse=True),
        _mutated_source(passed=1),
        _mutated_source(reason="DOWNLOAD_RESULT_STATUS_FAILURE"),
        _mutated_source(canonical_download_result_record=(("download_result_status", object()),)),
    ):
        decision = design.validate_source_shape_and_invariants_for_design(invalid)
        assert (decision.reason, decision.adapter_ready) == (design.SOURCE_INVARIANT_REASON, False)


def test_source_failure_occurs_before_oracle_and_has_exact_flags():
    with pytest.raises(design.AdapterContractDesignError) as captured:
        route(formal_evaluator=lambda **kwargs: object(), oracle_callable=lambda **kwargs: pytest.fail("oracle called"))
    assert captured.value.as_dict() == {
        "code": "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY",
        "admission_rule_id": "ADMIT_013", "known_rule": True,
        "callable_discovered": True, "adapter_ready": False,
        "reason": design.SOURCE_TYPE_REASON,
    }


def test_oracle_exact_type_storage_and_full_exact12_mismatch_rejected():
    for callable_ in (
        lambda **kwargs: object(),
        lambda **kwargs: oracle.classify_admit_013_formal_evaluator_interface_design(
            download_result_status="failure", observed_http_status=200,
            observed_content_length_bytes=10, observed_sha256=SHA_A,
            expected_sha256=SHA_A,
        ),
    ):
        with pytest.raises(design.AdapterContractDesignError) as captured:
            route(oracle_callable=callable_)
        assert captured.value.code == "UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY"
        assert captured.value.reason == design.SOURCE_INVARIANT_REASON
        assert captured.value.adapter_ready is False


def test_combined_projection_and_historical_field_semantics():
    result = route()
    assert result.normalized_values == (
        ("download_result_status", "success"), ("observed_http_status", "200"),
        ("observed_content_length_bytes", "10"), ("observed_sha256", SHA_A),
        ("expected_content_length_bytes", "10"), ("expected_sha256", SHA_A),
        ("explicit_integrity_verdict", "verified"),
    )
    assert result.validated_candidate_fields == result.normalized_values[:4]
    assert result.consumed_candidate_fields == design.DOWNLOAD_RESULT_FIELDS
    assert result.consumed_context_items == design.INTEGRITY_AUTHORITY_FIELDS
    assert not set(name for name, _ in result.validated_candidate_fields) & set(design.INTEGRITY_AUTHORITY_FIELDS)


def test_missing_required_projects_validated_download_prefix_from_routed_objects():
    download = CountingMapping((("download_result_status", "success"),))
    result = route(download=download)
    assert result.reason == "OBSERVED_HTTP_STATUS_MISSING"
    assert result.normalized_values == ()
    assert result.validated_candidate_fields == (("download_result_status", "success"),)
    assert result.consumed_candidate_fields == ("download_result_status", "observed_http_status")
    assert result.consumed_context_items == ()


def test_integer_projection_is_canonical_and_rejects_bool_subclasses_and_bad_pairs():
    pairs = (
        ("observed_http_status", 100),
        ("observed_content_length_bytes", 10**30),
        ("expected_content_length_bytes", 0),
    )
    assert design.project_named_pairs_to_exact_string_pairs(pairs) == (
        ("observed_http_status", "100"),
        ("observed_content_length_bytes", str(10**30)),
        ("expected_content_length_bytes", "0"),
    )
    for invalid in (
        (("observed_http_status", True),),
        (("observed_http_status", type("IntSub", (int,), {})(200)),),
        (["observed_http_status", 200],),
        (("expected_sha256", object()),),
    ):
        with pytest.raises(TypeError):
            design.project_named_pairs_to_exact_string_pairs(invalid)


def test_no_private_sentinel_reference_or_leak():
    text = Path(design.__file__).read_text()
    assert "_MISSING" not in text
    for row in read_csv(design.TRUTH_FILENAME):
        assert "MissingAdmit013" not in "|".join(row.values())


def test_committed_exact128_projection_and_exact23_business_inheritance():
    formal = list(csv.DictReader((ROOT / design.SOURCE_BOUNDARY[8][0]).open()))
    truth = read_csv(design.TRUTH_FILENAME)
    assert len(formal) == 128 and len(truth) == 172
    assert [row["case_id"] for row in truth[:128]] == [row["case_id"] for row in formal]
    normal = [row for row in truth[:128] if row["routing_condition"] == "committed_Exact128_projection"]
    negative = [row for row in truth[:128] if row["routing_condition"].endswith("negative_attestation")]
    assert (len(normal), len(negative)) == (102, 26)
    assert all(row["formal_call_count"] == row["oracle_call_count"] == "1" for row in normal)
    inherited = [row for row in formal if row["case_group"] == "inherited_exact7_business_projection"]
    assert len(inherited) == 23


def test_current_and_future_registry_contract_without_runtime_mutation():
    assert tuple(runtime.EVALUATOR_REGISTRY) == design.CURRENT_REGISTERED_RULE_ORDER
    identities = tuple(runtime.EVALUATOR_REGISTRY.values())
    assert design.FUTURE_REGISTERED_RULE_ORDER == (*tuple(runtime.EVALUATOR_REGISTRY), "ADMIT_013")
    assert design.FUTURE_CALLABLE_DISCOVERED_RULE_IDS == design.FUTURE_REGISTERED_RULE_ORDER
    assert design.FUTURE_ADAPTER_READY_RULE_IDS == design.FUTURE_REGISTERED_RULE_ORDER
    assert design.FUTURE_KNOWN_NOT_REGISTERED == ("ADMIT_014", "ADMIT_015")
    assert tuple(runtime.EVALUATOR_REGISTRY.values()) == identities


def test_design_source_defines_no_formal_handler_registry_dispatcher_or_shared_result():
    tree = ast.parse(Path(design.__file__).read_text())
    functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    classes = {node.name for node in tree.body if isinstance(node, ast.ClassDef)}
    assert "_evaluate_registered_admit_013" not in functions
    assert "evaluate_admission_rule" not in functions
    assert "UnifiedAdmissionRuleEvaluation" not in classes
    assert not any(
        isinstance(node, (ast.Assign, ast.AnnAssign))
        and any(
            isinstance(target, ast.Name) and target.id == "EVALUATOR_REGISTRY"
            for target in (node.targets if isinstance(node, ast.Assign) else (node.target,))
        )
        for node in tree.body
    )


def test_artifact_schemas_counts_hashes_readiness_and_issues():
    state = design.build_design_state()
    assert (len(state["contract_rows"]), len(state["routing_rows"]), len(state["truth_rows"]), len(state["safety_rows"]), len(state["issue_rows"])) == (48, 44, 172, 32, 23)
    assert {name: hashlib.sha256((OUTPUT_ROOT / name).read_bytes()).hexdigest() for name in design.OUTPUT_FILES} == design.FROZEN_OUTPUT_SHA256
    manifest = json.loads((OUTPUT_ROOT / design.MANIFEST_FILENAME).read_text())
    assert manifest["issue_transition_count"] == 0
    assert manifest["coverage_issue_affected_rules"] == "ADMIT_013|ADMIT_014|ADMIT_015"
    assert all(manifest["readiness"][key] is True for key in design.TRUE_READINESS)
    assert all(manifest["readiness"][key] is False for key in design.FALSE_READINESS)
    assert manifest["recommended_next_step"] == design.RECOMMENDED_NEXT_STEP


def test_deterministic_double_build_and_inode_preserving_materialization(tmp_path):
    first = design.build_artifacts()
    second = design.build_artifacts()
    assert first == second
    target = tmp_path / design.STAGE
    design.run_covapie_bulk_download_admission_admit_013_unified_adapter_contract_design_gate_v1(target)
    before = {path.name: path.stat().st_ino for path in target.iterdir()}
    design.run_covapie_bulk_download_admission_admit_013_unified_adapter_contract_design_gate_v1(target)
    after = {path.name: path.stat().st_ino for path in target.iterdir()}
    assert before == after


def test_materializer_mismatch_and_gpfs_einval_fail_closed(tmp_path, monkeypatch):
    mismatch = copied_outputs(tmp_path / "mismatch")
    (mismatch / design.CONTRACT_FILENAME).write_bytes(b"tampered\n")
    with pytest.raises(ValueError, match="repair forbidden"):
        design.run_covapie_bulk_download_admission_admit_013_unified_adapter_contract_design_gate_v1(mismatch)
    target = tmp_path / "new" / design.STAGE
    target.parent.mkdir(parents=True)
    monkeypatch.setattr(design, "_rename_noreplace", lambda *args: (_ for _ in ()).throw(OSError(errno.EINVAL, "GPFS")))
    with pytest.raises(OSError) as captured:
        design.run_covapie_bulk_download_admission_admit_013_unified_adapter_contract_design_gate_v1(target)
    assert captured.value.errno == errno.EINVAL
    assert not target.exists()
    assert not list(target.parent.glob(".admit013-adapter-stage-*"))


def test_materializer_has_no_os_replace_fallback_and_rejects_traversal(tmp_path):
    tree = ast.parse(Path(design.__file__).read_text())
    calls = [ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)]
    assert "os.replace" not in calls
    with pytest.raises(ValueError, match="escape"):
        design.run_covapie_bulk_download_admission_admit_013_unified_adapter_contract_design_gate_v1(Path("../escape"))


def test_canonical_runtime_identity_validation_is_explicit_and_clear():
    design._validate_canonical_evidence_runtime_identity("cpython", (3, 10, 4))
    checker = checker_module()
    checker._validate_canonical_evidence_runtime_identity("cpython", (3, 10, 4))
    for validate, implementation, version in (
        (design._validate_canonical_evidence_runtime_identity, "cpython", (3, 12, 0)),
        (design._validate_canonical_evidence_runtime_identity, "pypy", (3, 10, 4)),
        (checker._validate_canonical_evidence_runtime_identity, "cpython", (3, 12, 0)),
        (checker._validate_canonical_evidence_runtime_identity, "pypy", (3, 10, 4)),
    ):
        with pytest.raises((ValueError, AssertionError)) as captured:
            validate(implementation, version)
        message = str(captured.value)
        assert "required: CPython 3.10.4" in message
        assert f"observed implementation: {implementation}" in message
        assert f"observed version: {'.'.join(map(str, version))}" in message
        assert "frozen evidence is Python-version-sensitive" in message
        assert "noncanonical Python is not authorized to build artifacts or run the checker" in message


def test_build_artifacts_prebuilt_state_rejects_runtime_before_serialization(monkeypatch):
    fake_sys = SimpleNamespace(
        implementation=SimpleNamespace(name="cpython"),
        version_info=(3, 12, 0),
    )
    monkeypatch.setattr(design, "sys", fake_sys)
    monkeypatch.setattr(
        design, "_csv_bytes",
        lambda *args, **kwargs: pytest.fail("serialization reached"),
    )
    with pytest.raises(ValueError, match="required: CPython 3.10.4"):
        design.build_artifacts({"prebuilt": "state"})


def _configure_single_source_snapshot(
    tmp_path: Path, monkeypatch, *, tracked_output: bytes | None,
):
    relative = Path("fixture/source.txt")
    path = tmp_path / relative
    path.parent.mkdir()
    content = b"same committed bytes\n"
    path.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    monkeypatch.setattr(design, "SOURCE_BOUNDARY", ((relative.as_posix(), digest),))
    monkeypatch.setattr(design, "_assert_base_lineage", lambda *args: None)

    def fake_git(root, arguments):
        if arguments[0] == "ls-files":
            if tracked_output is None:
                raise ValueError("source-boundary git command failed")
            return tracked_output
        if arguments[0] == "ls-tree":
            return f"100644 blob frozenblob\t{relative.as_posix()}\n".encode()
        if arguments[:2] == ("cat-file", "blob"):
            return content
        raise AssertionError(arguments)

    monkeypatch.setattr(design, "_git", fake_git)
    return relative, content


def test_production_source_requires_exact_current_index_tracking(tmp_path, monkeypatch):
    relative, content = _configure_single_source_snapshot(
        tmp_path, monkeypatch,
        tracked_output=b"fixture/source.txt\n",
    )
    snapshot = design.build_frozen_source_snapshot(tmp_path)
    assert snapshot.records[0].tracked_in_current_index is True
    assert snapshot.records[0].content == content
    assert snapshot.records[0].relative_path == relative


@pytest.mark.parametrize("tracked_output", (None, b"fixture/source.txt\nalternate/source.txt\n"))
def test_production_source_rejects_untracked_or_alternate_same_byte_file(
    tmp_path, monkeypatch, tracked_output,
):
    _configure_single_source_snapshot(
        tmp_path, monkeypatch, tracked_output=tracked_output,
    )
    with pytest.raises(ValueError, match="tracking|git command"):
        design.build_frozen_source_snapshot(tmp_path)


def _replace_leaf_after_first_read(module, monkeypatch, leaf: Path):
    original_read = module.os.read
    original_content = leaf.read_bytes()
    fired = False

    def raced(descriptor, size):
        nonlocal fired
        chunk = original_read(descriptor, size)
        if chunk and not fired:
            fired = True
            old = leaf.with_name(f"{leaf.name}.old")
            leaf.rename(old)
            leaf.write_bytes(original_content)
        return chunk

    monkeypatch.setattr(module.os, "read", raced)


def _replace_parent_after_first_read(module, monkeypatch, parent: Path, leaf_name: str):
    original_read = module.os.read
    content = (parent / leaf_name).read_bytes()
    fired = False

    def raced(descriptor, size):
        nonlocal fired
        chunk = original_read(descriptor, size)
        if chunk and not fired:
            fired = True
            old = parent.with_name(f"{parent.name}.old")
            parent.rename(old)
            parent.mkdir()
            (parent / leaf_name).write_bytes(content)
        return chunk

    monkeypatch.setattr(module.os, "read", raced)


def test_production_source_postread_rejects_leaf_and_parent_replacement(
    tmp_path, monkeypatch,
):
    parent = tmp_path / "source-parent"
    parent.mkdir()
    leaf = parent / "source.txt"
    leaf.write_bytes(b"pinned source bytes\n")
    expected = design._full_identity(os.lstat(leaf))
    _replace_leaf_after_first_read(design, monkeypatch, leaf)
    with pytest.raises(
        ValueError, match="source changed during read|lexical leaf",
    ):
        design._pinned_read(tmp_path, Path("source-parent/source.txt"))

    monkeypatch.undo()
    second_root = tmp_path / "second-root"
    second_parent = second_root / "source-parent"
    second_parent.mkdir(parents=True)
    second_leaf = second_parent / "source.txt"
    second_leaf.write_bytes(b"pinned source bytes\n")
    _replace_parent_after_first_read(
        design, monkeypatch, second_parent, second_leaf.name,
    )
    with pytest.raises(
        ValueError,
        match=(
            "source changed during read|source lexical leaf identity changed"
            "|source lexical parent identity changed"
        ),
    ):
        design._pinned_read(second_root, Path("source-parent/source.txt"))
    assert expected[3] == len(b"pinned source bytes\n")


def test_checker_source_tracking_mode_and_postread_replacements(tmp_path, monkeypatch):
    checker = checker_module()
    original_git = checker._git

    def untracked_git(*arguments, **kwargs):
        if arguments[0] == "ls-files":
            raise AssertionError("source current index untracked")
        return original_git(*arguments, **kwargs)

    monkeypatch.setattr(checker, "_git", untracked_git)
    with pytest.raises(AssertionError, match="untracked"):
        checker._verify_sources()

    monkeypatch.undo()
    checker = checker_module()
    original_git = checker._git
    changed = False

    def mode_drift_git(*arguments, **kwargs):
        nonlocal changed
        value = original_git(*arguments, **kwargs)
        if arguments[0] == "ls-tree" and not changed:
            changed = True
            return value.replace(b"100644", b"120000", 1)
        return value

    monkeypatch.setattr(checker, "_git", mode_drift_git)
    with pytest.raises(AssertionError, match="blob/mode"):
        checker._verify_sources()

    monkeypatch.undo()
    checker = checker_module()
    parent = tmp_path / "checker-source"
    parent.mkdir()
    leaf = parent / "source.txt"
    leaf.write_bytes(b"checker pinned source\n")
    expected = checker._full_identity(os.lstat(leaf))
    _replace_leaf_after_first_read(checker, monkeypatch, leaf)
    with pytest.raises(
        AssertionError,
        match="source descriptor changed|source lexical leaf changed",
    ):
        checker._read_pinned(
            tmp_path, Path("checker-source/source.txt"), expected,
        )

    monkeypatch.undo()
    checker = checker_module()
    second_root = tmp_path / "checker-second-root"
    second_parent = second_root / "checker-source"
    second_parent.mkdir(parents=True)
    second_leaf = second_parent / "source.txt"
    second_leaf.write_bytes(b"checker pinned source\n")
    expected = checker._full_identity(os.lstat(second_leaf))
    _replace_parent_after_first_read(
        checker, monkeypatch, second_parent, second_leaf.name,
    )
    with pytest.raises(
        AssertionError,
        match=(
            "source descriptor changed|source lexical leaf changed"
            "|source lexical parent changed"
        ),
    ):
        checker._read_pinned(
            second_root, Path("checker-source/source.txt"), expected,
        )


def test_checker_source_symlink_and_source_before_output(tmp_path, monkeypatch):
    checker = checker_module()
    target = tmp_path / "target.txt"
    target.write_bytes(b"target\n")
    link = tmp_path / "link.txt"
    link.symlink_to(target)
    with pytest.raises((AssertionError, OSError)):
        checker._read_pinned(
            tmp_path, Path("link.txt"), checker._full_identity(os.lstat(link)),
        )

    events = []
    original_sources = checker._verify_sources

    def sources():
        events.append("source")
        return original_sources()

    def output():
        events.append("output")
        raise AssertionError("stop after ordering evidence")

    monkeypatch.setattr(checker, "_verify_sources", sources)
    monkeypatch.setattr(checker, "_verify_design_ast", lambda: None)
    monkeypatch.setattr(checker, "_validate_lifecycle", lambda: "pre_commit")
    monkeypatch.setattr(checker, "_output_bytes", output)
    with pytest.raises(AssertionError, match="ordering evidence"):
        checker.main()
    assert events == ["source", "output"]


def _configure_checker_output(checker, target: Path):
    checker.OUTPUT_ROOT = target
    checker.ROOT = target.parent


def _race_checker_output(module, monkeypatch, action, *, after_eof_count=None):
    original_read = module.os.read
    fired = False
    eof_count = 0

    def raced(descriptor, size):
        nonlocal fired, eof_count
        chunk = original_read(descriptor, size)
        if after_eof_count is None:
            if chunk and not fired:
                fired = True
                action()
        elif not chunk:
            eof_count += 1
            if eof_count == after_eof_count and not fired:
                fired = True
                action()
        return chunk

    monkeypatch.setattr(module.os, "read", raced)


def test_checker_output_post_traversal_rejects_root_and_leaf_replacement(
    tmp_path, monkeypatch,
):
    checker = checker_module()
    target = copied_outputs(tmp_path / "root-race")
    _configure_checker_output(checker, target)
    old = target.with_name(f"{target.name}.old")
    _race_checker_output(
        checker, monkeypatch,
        lambda: (target.rename(old), target.mkdir()),
    )
    with pytest.raises(AssertionError, match="root changed"):
        checker._output_bytes()

    monkeypatch.undo()
    checker = checker_module()
    target = copied_outputs(tmp_path / "leaf-race")
    _configure_checker_output(checker, target)
    leaf = target / checker.OUTPUT_FILES[0]
    content = leaf.read_bytes()

    def replace_leaf():
        leaf.unlink()
        leaf.write_bytes(content)

    _race_checker_output(checker, monkeypatch, replace_leaf)
    with pytest.raises(
        AssertionError, match="output leaf changed|output lexical leaf changed",
    ):
        checker._output_bytes()


@pytest.mark.parametrize("mutation", ("extra", "missing"))
def test_checker_output_post_traversal_rejects_inventory_races(
    tmp_path, monkeypatch, mutation,
):
    checker = checker_module()
    target = copied_outputs(tmp_path / mutation)
    _configure_checker_output(checker, target)

    def mutate():
        if mutation == "extra":
            (target / "seventh.csv").write_bytes(b"extra\n")
        else:
            (target / checker.OUTPUT_FILES[0]).unlink()

    _race_checker_output(
        checker, monkeypatch, mutate,
        after_eof_count=len(checker.OUTPUT_FILES),
    )
    with pytest.raises(AssertionError, match="inventory"):
        checker._output_bytes()


def _race_existing_output(design_module, monkeypatch, action):
    original = design_module._read_at
    fired = False

    def raced(*args, **kwargs):
        nonlocal fired
        value = original(*args, **kwargs)
        if not fired:
            fired = True
            action()
        return value

    monkeypatch.setattr(design_module, "_read_at", raced)


@pytest.mark.parametrize("mutation", ("root", "leaf", "extra", "missing"))
def test_publisher_existing_set_rejects_destination_and_inventory_races(
    tmp_path, monkeypatch, mutation,
):
    target = copied_outputs(tmp_path / mutation)
    leaf = target / design.OUTPUT_FILES[0]
    content = leaf.read_bytes()

    def mutate():
        if mutation == "root":
            old = target.with_name(f"{target.name}.old")
            target.rename(old)
            target.mkdir()
        elif mutation == "leaf":
            leaf.unlink()
            leaf.write_bytes(content)
        elif mutation == "extra":
            (target / "seventh.csv").write_bytes(b"extra\n")
        else:
            leaf.unlink()

    _race_existing_output(design, monkeypatch, mutate)
    with pytest.raises((ValueError, FileNotFoundError)):
        design.run_covapie_bulk_download_admission_admit_013_unified_adapter_contract_design_gate_v1(target)


def _successful_test_rename(parent_fd, source, target):
    os.rename(
        source, target, src_dir_fd=parent_fd, dst_dir_fd=parent_fd,
    )


def test_publisher_postrename_normal_success_binds_destination_inode(
    tmp_path, monkeypatch,
):
    target = tmp_path / "normal" / design.STAGE
    target.parent.mkdir()
    monkeypatch.setattr(design, "_rename_noreplace", _successful_test_rename)
    design.run_covapie_bulk_download_admission_admit_013_unified_adapter_contract_design_gate_v1(target)
    assert set(path.name for path in target.iterdir()) == set(design.OUTPUT_FILES)
    assert {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in target.iterdir()
    } == design.FROZEN_OUTPUT_SHA256


@pytest.mark.parametrize("mutation", ("replace", "delete", "leaf", "parent"))
def test_publisher_postrename_rejects_destination_races(
    tmp_path, monkeypatch, mutation,
):
    parent = tmp_path / mutation
    parent.mkdir()
    target = parent / design.STAGE
    first_payload = (OUTPUT_ROOT / design.OUTPUT_FILES[0]).read_bytes()

    def raced_rename(parent_fd, source, target_name):
        _successful_test_rename(parent_fd, source, target_name)
        if mutation == "replace":
            os.rename(
                target_name, f"{target_name}.old",
                src_dir_fd=parent_fd, dst_dir_fd=parent_fd,
            )
            os.mkdir(target_name, dir_fd=parent_fd)
        elif mutation == "delete":
            os.rename(
                target_name, f"{target_name}.orphan",
                src_dir_fd=parent_fd, dst_dir_fd=parent_fd,
            )
        elif mutation == "leaf":
            leaf = target / design.OUTPUT_FILES[0]
            leaf.unlink()
            leaf.write_bytes(first_payload)
        else:
            old_parent = parent.with_name(f"{parent.name}.old")
            parent.rename(old_parent)
            parent.mkdir()

    monkeypatch.setattr(design, "_rename_noreplace", raced_rename)
    with pytest.raises((ValueError, FileNotFoundError)):
        design.run_covapie_bulk_download_admission_admit_013_unified_adapter_contract_design_gate_v1(target)


def test_checker_independently_rejects_synchronized_csv_manifest_tamper(tmp_path):
    checker = checker_module()
    target = copied_outputs(tmp_path)
    contract_path = target / design.CONTRACT_FILENAME
    rows = list(csv.DictReader(contract_path.open()))
    rows[0]["contract_value"] = "tampered"
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=design.CONTRACT_COLUMNS, lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
    contract_path.write_text(stream.getvalue())
    manifest_path = target / design.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text())
    manifest["output_sha256"][design.CONTRACT_FILENAME] = hashlib.sha256(contract_path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    source_rows = checker._verify_sources()
    checker.OUTPUT_ROOT = target
    checker.ROOT = target.parent
    with pytest.raises(AssertionError, match="frozen output SHA"):
        checker._verify_semantics(checker._output_bytes(), source_rows)


def test_checker_rejects_manifest_duplicate_reorder_and_output_symlink(tmp_path):
    checker = checker_module()
    duplicate = b'{"a":1,"a":2}\n'
    with pytest.raises(AssertionError, match="duplicate"):
        checker._json_no_duplicates(duplicate)
    with pytest.raises(AssertionError, match="order"):
        checker._json_no_duplicates(b'{"b":1,"a":2}\n')
    target = copied_outputs(tmp_path)
    leaf = target / design.CONTRACT_FILENAME
    leaf.unlink()
    leaf.symlink_to(OUTPUT_ROOT / design.CONTRACT_FILENAME)
    checker.OUTPUT_ROOT = target
    checker.ROOT = target.parent
    with pytest.raises(AssertionError, match="leaf structure"):
        checker._output_bytes()


def test_lifecycle_pre_or_post_exact10_and_no_extra_stage_file():
    checker = checker_module()
    assert checker._validate_lifecycle() in {"pre_commit", "post_commit"}
    assert len(checker.CANDIDATE_PATHS) == 10
    assert set(path.name for path in OUTPUT_ROOT.iterdir()) == set(design.OUTPUT_FILES)


def test_lifecycle_rejects_extra_stage_top_level_file():
    checker = checker_module()
    extra = ROOT / "docs/covapie_bulk_download_admission_admit_013_unified_adapter_contract_extra.md"
    extra.write_text("temporary test fixture\n")
    try:
        with pytest.raises(AssertionError, match="inventory"):
            checker._validate_lifecycle()
    finally:
        extra.unlink()


def test_isolated_imports_are_silent_and_side_effect_free():
    for relative in (design.__file__, CHECKER_PATH, Path(__file__)):
        code = (
            "import importlib.util,sys;"
            f"s=importlib.util.spec_from_file_location('isolated_module',{str(relative)!r});"
            "m=importlib.util.module_from_spec(s);sys.modules['isolated_module']=m;"
            "s.loader.exec_module(m)"
        )
        result = subprocess.run(
            (sys.executable, "-c", code), cwd=ROOT,
            env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        assert result.returncode == 0
        assert result.stdout == result.stderr == b""


def test_protected_paths_forbidden_suffixes_and_current_runtime_are_unchanged():
    changed = subprocess.run(
        ("git", "diff", "--name-only"), cwd=ROOT,
        stdout=subprocess.PIPE, check=True,
    ).stdout.decode().splitlines()
    assert all(not path.startswith((
        "data/raw/", "checkpoints/", "equivariant_diffusion/",
    )) for path in changed)
    assert "lightning_modules.py" not in changed
    assert "dataset.py" not in changed
    assert "data/prepare_crossdocked.py" not in changed
    assert runtime.__file__ is not None
    assert hashlib.sha256(Path(runtime.__file__).read_bytes()).hexdigest() == design.SOURCE_BOUNDARY[12][1]
