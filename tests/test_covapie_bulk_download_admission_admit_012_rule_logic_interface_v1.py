"""Targeted tests for the formal ADMIT_012 standalone evaluator and evidence."""

import ast
import csv
import dataclasses
import errno
import hashlib
import importlib.util
import inspect
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
FORMAL_PATH = SRC / "covalent_ext/covapie_bulk_download_admission_admit_012_rule_logic_interface.py"
CHECKER_PATH = ROOT / "scripts/check_covapie_bulk_download_admission_admit_012_rule_logic_interface_v1.py"
PYTHON = Path("/cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/covapie-envs/diffsbdd-legacy-test-v1/bin/python3.10")

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import covapie_bulk_download_admission_admit_012_rule_logic_interface as formal

checker_spec = importlib.util.spec_from_file_location("admit012_standalone_checker_tests", CHECKER_PATH)
assert checker_spec is not None and checker_spec.loader is not None
checker = importlib.util.module_from_spec(checker_spec)
checker_spec.loader.exec_module(checker)


SHA = "0123456789abcdef" * 4
VALID_FIELDS = {
    "download_result_status": "success",
    "observed_http_status": 200,
    "observed_content_length_bytes": 1,
    "observed_sha256": SHA,
}
VALID_CONTEXTS = {
    "allowed_download_result_statuses": formal.ALLOWED_DOWNLOAD_RESULT_STATUSES,
    "successful_http_status_contract": formal.SUCCESSFUL_HTTP_STATUS_CONTRACT,
    "content_length_contract": formal.CONTENT_LENGTH_CONTRACT,
    "sha256_format_contract": formal.SHA256_FORMAT_CONTRACT,
}


def evaluate(**overrides):
    values = {**VALID_FIELDS, **VALID_CONTEXTS, **overrides}
    return formal.evaluate_admit_012(**values)


def baseline_values():
    result = evaluate()
    return {name: getattr(result, name) for name in formal.RESULT_FIELDS}


def test_public_name_signature_order_and_keyword_only():
    assert formal.evaluate_admit_012.__name__ == "evaluate_admit_012"
    signature = inspect.signature(formal.evaluate_admit_012)
    parameters = tuple(signature.parameters.values())
    assert tuple(item.name for item in parameters) == (*formal.EXACT4_FIELDS, *formal.EXACT4_CONTEXT_ITEMS)
    assert all(item.kind is inspect.Parameter.KEYWORD_ONLY for item in parameters)
    assert signature.return_annotation is formal.Admit012EvaluationResult


def test_private_shared_defaults_and_required_contexts():
    parameters = tuple(inspect.signature(formal.evaluate_admit_012).parameters.values())
    assert all(item.default is formal._MISSING for item in parameters[:4])
    assert all(item.default is inspect.Parameter.empty for item in parameters[4:])
    assert type(formal._MISSING).__name__ == "_MissingAdmit012Value"
    assert formal._MissingAdmit012Value.__slots__ == ()


def test_no_varargs_varkw_or_mapping_parameter():
    signature = inspect.signature(formal.evaluate_admit_012)
    assert not any(item.kind in {inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD} for item in signature.parameters.values())
    assert "mapping" not in str(signature).lower()


def test_positional_call_is_rejected():
    with pytest.raises(TypeError):
        formal.evaluate_admit_012("success", 200, 1, SHA, *VALID_CONTEXTS.values())


@pytest.mark.parametrize("context", formal.EXACT4_CONTEXT_ITEMS)
def test_missing_required_context_is_python_type_error(context):
    values = {**VALID_FIELDS, **VALID_CONTEXTS}
    del values[context]
    with pytest.raises(TypeError):
        formal.evaluate_admit_012(**values)


def test_exact10_field_order_annotations_and_frozen_shape():
    assert tuple(field.name for field in dataclasses.fields(formal.Admit012EvaluationResult)) == formal.RESULT_FIELDS
    assert tuple(field.type for field in dataclasses.fields(formal.Admit012EvaluationResult)) == (
        str, str, bool, bool, str, tuple, tuple, tuple[str, ...], tuple[str, ...], bool,
    )
    assert formal.Admit012EvaluationResult.__dataclass_params__.frozen is True
    assert formal.Admit012EvaluationResult.__bases__ == (object,)


def test_result_is_immutable_and_subclass_construction_rejected():
    result = evaluate()
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.outcome = "invalid"

    class Subclass(formal.Admit012EvaluationResult):
        pass

    with pytest.raises(TypeError):
        Subclass(*(getattr(result, name) for name in formal.RESULT_FIELDS))


@pytest.mark.parametrize("name,value", [
    ("admission_rule_id", str("ADMIT_012")),
    ("outcome", 1),
    ("passed", 1),
    ("blocks_candidate", 0),
    ("reason", object()),
    ("canonical_download_result_record", []),
    ("validated_download_result_fields", []),
    ("consumed_download_result_fields", []),
    ("consumed_context_items", []),
    ("evaluator_io_used", 0),
])
def test_result_exact_builtin_field_types(name, value):
    values = baseline_values()
    values[name] = value
    if name == "admission_rule_id":
        class StrSubclass(str):
            pass
        values[name] = StrSubclass(value)
    with pytest.raises((TypeError, ValueError)):
        formal.Admit012EvaluationResult(*(values[field] for field in formal.RESULT_FIELDS))


@pytest.mark.parametrize("name,value", [
    ("canonical_download_result_record", (("download_result_status", "success"),)),
    ("validated_download_result_fields", (("observed_http_status", 200),)),
    ("consumed_download_result_fields", tuple(reversed(formal.EXACT4_FIELDS))),
    ("consumed_context_items", tuple(reversed(formal.EXACT4_CONTEXT_ITEMS))),
])
def test_result_record_and_prefix_invariants(name, value):
    values = baseline_values()
    values[name] = value
    with pytest.raises(ValueError):
        formal.Admit012EvaluationResult(*(values[field] for field in formal.RESULT_FIELDS))


def test_pair_exact_tuple_and_name_type_are_enforced():
    values = baseline_values()

    class PairSubclass(tuple):
        pass

    values["canonical_download_result_record"] = (
        PairSubclass(values["canonical_download_result_record"][0]),
        *values["canonical_download_result_record"][1:],
    )
    with pytest.raises(TypeError):
        formal.Admit012EvaluationResult(*(values[field] for field in formal.RESULT_FIELDS))
    values = baseline_values()
    values["canonical_download_result_record"] = ((1, "success"), *values["canonical_download_result_record"][1:])
    with pytest.raises(TypeError):
        formal.Admit012EvaluationResult(*(values[field] for field in formal.RESULT_FIELDS))


@pytest.mark.parametrize("name,value", [
    ("admission_rule_id", "ADMIT_013"),
    ("outcome", "blocked"),
    ("passed", False),
    ("blocks_candidate", True),
    ("reason", "UNKNOWN_REASON"),
    ("evaluator_io_used", True),
])
def test_result_universal_invariants(name, value):
    values = baseline_values()
    values[name] = value
    with pytest.raises(ValueError):
        formal.Admit012EvaluationResult(*(values[field] for field in formal.RESULT_FIELDS))


@pytest.mark.parametrize("position,reason", list(enumerate(formal.MISSING_REASONS)))
def test_each_missing_position_short_circuits(position, reason):
    values = {**VALID_FIELDS, **VALID_CONTEXTS}
    for name in formal.EXACT4_FIELDS[position:]:
        values.pop(name)
    result = formal.evaluate_admit_012(**values)
    assert (result.outcome, result.reason) == ("blocked", reason)
    assert result.canonical_download_result_record == result.validated_download_result_fields == ()
    assert result.consumed_download_result_fields == formal.EXACT4_FIELDS[:position + 1]
    assert result.consumed_context_items == ()


@pytest.mark.parametrize("field,value,reason,validated_length", [
    ("download_result_status", None, "DOWNLOAD_RESULT_STATUS_TYPE_INVALID", 0),
    ("download_result_status", "SUCCESS", "DOWNLOAD_RESULT_STATUS_VALUE_INVALID", 0),
    ("observed_http_status", True, "OBSERVED_HTTP_STATUS_TYPE_INVALID", 1),
    ("observed_http_status", 600, "OBSERVED_HTTP_STATUS_RANGE_INVALID", 1),
    ("observed_content_length_bytes", False, "OBSERVED_CONTENT_LENGTH_BYTES_TYPE_INVALID", 2),
    ("observed_content_length_bytes", -1, "OBSERVED_CONTENT_LENGTH_BYTES_RANGE_INVALID", 2),
    ("observed_sha256", b"0" * 64, "OBSERVED_SHA256_TYPE_INVALID", 3),
    ("observed_sha256", "A" * 64, "OBSERVED_SHA256_FORMAT_INVALID", 3),
])
def test_each_field_type_value_failure(field, value, reason, validated_length):
    result = evaluate(**{field: value})
    assert (result.outcome, result.reason) == ("invalid", reason)
    assert result.canonical_download_result_record == ()
    assert len(result.validated_download_result_fields) == validated_length
    assert result.consumed_download_result_fields == formal.EXACT4_FIELDS
    assert result.consumed_context_items == ()


@pytest.mark.parametrize("context,type_value,content_value,type_reason,content_reason", [
    ("allowed_download_result_statuses", ["success", "failure"], ("failure", "success"), "ALLOWED_DOWNLOAD_RESULT_STATUSES_TYPE_INVALID", "ALLOWED_DOWNLOAD_RESULT_STATUSES_CONTENT_INVALID"),
    ("successful_http_status_contract", list(formal.SUCCESSFUL_HTTP_STATUS_CONTRACT), tuple(reversed(formal.SUCCESSFUL_HTTP_STATUS_CONTRACT)), "SUCCESSFUL_HTTP_STATUS_CONTRACT_TYPE_INVALID", "SUCCESSFUL_HTTP_STATUS_CONTRACT_CONTENT_INVALID"),
    ("content_length_contract", dict(formal.CONTENT_LENGTH_CONTRACT), formal.CONTENT_LENGTH_CONTRACT[:-1], "CONTENT_LENGTH_CONTRACT_TYPE_INVALID", "CONTENT_LENGTH_CONTRACT_CONTENT_INVALID"),
    ("sha256_format_contract", re.compile("[0-9a-f]{64}"), (*formal.SHA256_FORMAT_CONTRACT, ("extra", False)), "SHA256_FORMAT_CONTRACT_TYPE_INVALID", "SHA256_FORMAT_CONTRACT_CONTENT_INVALID"),
])
def test_each_context_type_and_content_failure(context, type_value, content_value, type_reason, content_reason):
    index = formal.EXACT4_CONTEXT_ITEMS.index(context)
    for value, reason in ((type_value, type_reason), (content_value, content_reason)):
        result = evaluate(**{context: value})
        assert (result.outcome, result.reason) == ("invalid", reason)
        assert result.canonical_download_result_record == result.validated_download_result_fields
        assert len(result.canonical_download_result_record) == 4
        assert result.consumed_download_result_fields == formal.EXACT4_FIELDS
        assert result.consumed_context_items == formal.EXACT4_CONTEXT_ITEMS[:index + 1]


def test_context_tuple_and_pair_subclasses_are_rejected():
    class TupleSubclass(tuple):
        pass

    class PairSubclass(tuple):
        pass

    result = evaluate(allowed_download_result_statuses=TupleSubclass(formal.ALLOWED_DOWNLOAD_RESULT_STATUSES))
    assert result.reason == "ALLOWED_DOWNLOAD_RESULT_STATUSES_TYPE_INVALID"
    contract = list(formal.SUCCESSFUL_HTTP_STATUS_CONTRACT)
    contract[0] = PairSubclass(contract[0])
    result = evaluate(successful_http_status_contract=tuple(contract))
    assert result.reason == "SUCCESSFUL_HTTP_STATUS_CONTRACT_CONTENT_INVALID"


def test_context_bool_int_distinction_and_no_normalization():
    contract = list(formal.SUCCESSFUL_HTTP_STATUS_CONTRACT)
    contract[0] = ("legal_minimum", True)
    assert evaluate(successful_http_status_contract=tuple(contract)).reason == "SUCCESSFUL_HTTP_STATUS_CONTRACT_CONTENT_INVALID"
    assert evaluate(download_result_status=" success ").reason == "DOWNLOAD_RESULT_STATUS_VALUE_INVALID"
    assert evaluate(observed_sha256=SHA.upper()).reason == "OBSERVED_SHA256_FORMAT_INVALID"


@pytest.mark.parametrize("status,http", [("failure", 200), ("success", 404), ("success", 500), ("failure", 599), ("success", 100)])
def test_legal_failure_status_4xx_5xx_pass_without_admit013(status, http):
    result = evaluate(download_result_status=status, observed_http_status=http)
    assert result.outcome == "passed" and result.reason == ""
    assert result.passed is True and result.blocks_candidate is False
    assert result.evaluator_io_used is False


def test_full_precedence_missing_then_field_then_context():
    values = {**VALID_FIELDS, **VALID_CONTEXTS}
    del values["download_result_status"]
    values["observed_http_status"] = object()
    values["allowed_download_result_statuses"] = object()
    assert formal.evaluate_admit_012(**values).reason == "DOWNLOAD_RESULT_STATUS_MISSING"
    values["download_result_status"] = object()
    assert formal.evaluate_admit_012(**values).reason == "DOWNLOAD_RESULT_STATUS_TYPE_INVALID"
    values["download_result_status"] = "success"
    values["observed_http_status"] = 200
    assert formal.evaluate_admit_012(**values).reason == "ALLOWED_DOWNLOAD_RESULT_STATUSES_TYPE_INVALID"


def test_formal_closure_marker_sha_ast_and_closed_world():
    attestation = checker.inspect_formal_source()
    assert tuple(attestation["digests"]) == checker.FORMAL_CLOSURE
    assert attestation["digests"] == checker.EXPECTED_AST_SHA256
    assert attestation["full_sha"] == checker.EXPECTED_PRODUCTION_SHA256
    assert attestation["prefix_sha"] == checker.EXPECTED_MARKER_PREFIX_SHA256


@pytest.mark.parametrize("payload", [
    "open('x')", "helper()", "__import__('os')", "getattr(object(), '__class__')",
    "classify_admit_012_formal_evaluator_interface_design()",
])
def test_closed_world_rejects_io_unknown_dynamic_dunder_or_oracle(payload):
    source = FORMAL_PATH.read_text()
    tree = ast.parse(source)
    definitions = checker._definition_nodes(tree)
    evaluator = definitions["evaluate_admit_012"]
    assert isinstance(evaluator, ast.FunctionDef)
    evaluator.body.insert(0, ast.Expr(ast.parse(payload, mode="eval").body))
    with pytest.raises(AssertionError):
        checker._check_closed_world(definitions)


def test_closed_world_rejects_indirect_helper_io_and_local_import():
    for statement in ("open('x')", "import os"):
        tree = ast.parse(FORMAL_PATH.read_text())
        definitions = checker._definition_nodes(tree)
        helper = definitions["_record"]
        assert isinstance(helper, ast.FunctionDef)
        helper.body.insert(0, ast.parse(statement).body[0])
        with pytest.raises(AssertionError):
            checker._check_closed_world(definitions)


def test_pre_and_post_marker_binding_tamper_rejected(tmp_path):
    source = FORMAL_PATH.read_text()
    pre = tmp_path / "pre.py"
    pre.write_text(source.replace("return _make_result(\"passed\"", "return _make_result(\"invalid\"", 1))
    with pytest.raises(AssertionError):
        checker.inspect_formal_source(pre, enforce_full_sha=False)
    post = tmp_path / "post.py"
    post.write_text(source + "\nevaluate_admit_012 = lambda **kwargs: None\n")
    with pytest.raises(AssertionError):
        checker.inspect_formal_source(post, enforce_full_sha=False)


def test_formal_source_identity_race_rejected(monkeypatch):
    original = checker._read_fd

    def drift(path, identity):
        checker._read_fd = original
        raise AssertionError("simulated identity drift")

    monkeypatch.setattr(checker, "_read_fd", drift)
    with pytest.raises(AssertionError, match="simulated identity drift"):
        checker.inspect_formal_source()


def test_all_105_committed_cases_execute_formally():
    snapshot = formal.build_frozen_source_snapshot()
    rows = formal._truth_rows(snapshot)
    assert len(rows) == 105
    assert all(row["truth_passed"] == "true" for row in rows)
    assert sum(row["case_id"].startswith("FIELD52_") for row in rows) == 52
    assert tuple(row["case_id"] for row in rows[-8:]) == formal.NEGATIVE_CASE_IDS


def test_literal_decoder_rejects_malicious_representation_without_execution(tmp_path):
    marker = tmp_path / "executed"
    payload = f"__import__('pathlib').Path({str(marker)!r}).write_text('bad')"
    with pytest.raises((ValueError, SyntaxError)):
        checker._decode(payload)
    assert not marker.exists()


def test_source_boundary_purity_issue_and_readiness_evidence():
    artifacts = formal.build_artifacts()
    source_rows = list(csv.DictReader(io.StringIO(artifacts[formal.SOURCE_FILE].decode())))
    purity_rows = list(csv.DictReader(io.StringIO(artifacts[formal.PURITY_FILE].decode())))
    issue_rows = list(csv.DictReader(io.StringIO(artifacts[formal.ISSUE_FILE].decode())))
    manifest = json.loads(artifacts[formal.MANIFEST_FILE])
    assert len(source_rows) == 18 and all(row["source_boundary_passed"] == "true" for row in source_rows)
    assert len(purity_rows) == 14 and all(row["purity_passed"] == "true" for row in purity_rows)
    assert len(issue_rows) == 16
    assert manifest["truth_matrix_passed"] == 105
    assert all(manifest["readiness"][name] is True for name in formal.TRUE_READINESS)
    assert all(manifest["readiness"][name] is False for name in formal.FALSE_READINESS)


def test_deterministic_double_build_is_byte_identical():
    first = formal.build_artifacts()
    second = formal.build_artifacts()
    assert first == second
    assert tuple(first) == formal.OUTPUT_FILES


def test_set_atomic_materializer_exact_noop(tmp_path):
    root = tmp_path / formal.STAGE
    first = formal.materialize_contract(root)
    identities = {name: os.lstat(root / name).st_ino for name in formal.OUTPUT_FILES}
    second = formal.materialize_contract(root)
    assert first == second
    assert identities == {name: os.lstat(root / name).st_ino for name in formal.OUTPUT_FILES}


def test_gpfs_einval_fails_closed_without_replace_or_residue(tmp_path, monkeypatch):
    root = tmp_path / formal.STAGE

    def unavailable(source, destination):
        raise OSError(errno.EINVAL, "simulated GPFS renameat2 rejection")

    monkeypatch.setattr(formal, "_rename_noreplace", unavailable)
    with pytest.raises(OSError) as error:
        formal.materialize_contract(root)
    assert error.value.errno == errno.EINVAL
    assert not root.exists()
    assert not tuple(tmp_path.glob("*.staging"))


def test_checker_validates_canonical_evidence():
    checker.validate_output_tree()


def test_synchronized_semantic_tamper_rejected_without_frozen_hashes(tmp_path):
    root = tmp_path / formal.STAGE
    formal.materialize_contract(root)
    truth_path = root / formal.TRUTH_FILE
    rows = list(csv.DictReader(truth_path.read_text().splitlines()))
    rows[0]["expected_outcome"] = "invalid"
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=formal.TRUTH_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    truth_path.write_text(stream.getvalue())
    manifest_path = root / formal.MANIFEST_FILE
    manifest = json.loads(manifest_path.read_text())
    manifest["output_sha256"][formal.TRUTH_FILE] = hashlib.sha256(truth_path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with pytest.raises(AssertionError):
        checker.validate_output_tree(root, enforce_frozen_hashes=False)


def test_pinned_output_traversal_rejects_extra_and_symlink(tmp_path):
    root = tmp_path / formal.STAGE
    formal.materialize_contract(root)
    (root / "extra").write_text("x")
    with pytest.raises(AssertionError):
        checker._read_output_tree(root)
    (root / "extra").unlink()
    leaf = root / formal.CONTRACT_FILE
    leaf.unlink()
    leaf.symlink_to(FORMAL_PATH)
    with pytest.raises(AssertionError):
        checker._read_output_tree(root)


@pytest.mark.parametrize("target", [FORMAL_PATH, CHECKER_PATH])
def test_silent_isolated_import(target):
    code = (
        "import importlib.util;"
        f"s=importlib.util.spec_from_file_location('silent_target',{str(target)!r});"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m)"
    )
    completed = subprocess.run([str(PYTHON), "-B", "-c", code], cwd=ROOT, capture_output=True, text=True, check=False)
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == ""


def test_no_registry_adapter_admit013_or_forbidden_operation_in_formal_closure():
    prefix = FORMAL_PATH.read_text().split(checker.MARKER, 1)[0]
    for forbidden in (
        "EVALUATOR_REGISTRY", "_evaluate_registered_", "ADMIT_013", "provider",
        "download(", "optimizer", "backward(", "checkpoint", "data/raw", "Mapping",
    ):
        assert forbidden not in prefix


def test_no_forbidden_artifacts_in_stage_file_set():
    allowed = {FORMAL_PATH, CHECKER_PATH, Path(__file__).resolve(), ROOT / "docs/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1_summary.md"}
    allowed.update((ROOT / formal.DEFAULT_OUTPUT_ROOT / name).resolve() for name in formal.OUTPUT_FILES)
    stage_paths = {
        path.resolve() for path in ROOT.rglob("*admit_012_rule_logic_interface*")
        if path.is_file() and formal.STAGE in str(path)
    }
    assert stage_paths <= allowed
    assert not any(path.suffix in {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".tmp", ".part"} for path in allowed)
