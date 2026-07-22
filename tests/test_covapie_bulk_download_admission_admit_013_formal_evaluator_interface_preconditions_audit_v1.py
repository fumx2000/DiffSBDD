from __future__ import annotations

import ast
import csv
import errno
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_013_formal_evaluator_interface_preconditions_audit as gate,
)

CHECKER_PATH = REPO_ROOT / "scripts/check_covapie_bulk_download_admission_admit_013_formal_evaluator_interface_preconditions_audit_v1.py"
SPEC = importlib.util.spec_from_file_location("admit013_preconditions_checker", CHECKER_PATH)
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
ROOT = REPO_ROOT / checker.OUTPUT_ROOT


@pytest.fixture(scope="module")
def snapshot():
    return gate.build_frozen_source_snapshot()


@pytest.fixture(scope="module")
def manifest():
    return json.loads((ROOT / gate.MANIFEST).read_text())


@pytest.fixture(scope="module")
def checker_records():
    return checker.snapshot()


def output_rows(name: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO((ROOT / name).read_text(), newline="")))


def copy_output(tmp_path: Path) -> Path:
    target = tmp_path / "out"
    shutil.copytree(ROOT, target)
    return target


def resync_manifest(root: Path) -> None:
    path = root / checker.MANIFEST
    value = json.loads(path.read_text())
    value["output_sha256"] = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in checker.FILES[:-1]
    }
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def reject_with_cached_snapshot(
    root: Path, monkeypatch: pytest.MonkeyPatch, records
) -> None:
    monkeypatch.setattr(checker, "snapshot", lambda: records)
    with pytest.raises(AssertionError):
        checker.validate(root, enforce_frozen_hashes=False)


def test_base_identity_and_clean_authority(snapshot) -> None:
    assert gate.BASE_COMMIT == "5ff12d358a633c44c333022f7e0ebe30f039d6fc"
    assert gate.BASE_SUBJECT == "add CovaPIE unified dispatch runtime with ADMIT_001 to ADMIT_012 v1"
    assert len(snapshot) == gate.EXPECTED_SOURCE_COUNT == 545


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("admission_rule_id", "ADMIT_013"),
        ("admission_rule_name", "download_failure_fail_closed"),
        ("evidence_source", "future_download_result"),
        ("required_status", "non_success_or_integrity_failure_not_admitted"),
        ("failure_severity", "blocking"),
        ("blocking_reason", "download_failure_must_fail_closed"),
        ("evaluation_phase", "post_download"),
    ],
)
def test_exact_registry_identity(manifest, key: str, expected: str) -> None:
    assert manifest[key] == expected


def test_rule_known_but_unregistered_and_exact12_coverage(snapshot) -> None:
    rows = gate._rows(snapshot, gate.RUNTIME_REGISTRY)
    assert next(row for row in rows if row["audit_item"] == "not_registered:ADMIT_013")["observed_value"] == "False"
    issues = gate._rows(snapshot, gate.RUNTIME_ISSUES)
    coverage = next(row for row in issues if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    assert coverage["affected_rules"] == "ADMIT_013|ADMIT_014|ADMIT_015"
    assert coverage["status"] == "open"


def test_exact32_preconditions_and_counts() -> None:
    rows = gate._preconditions()
    assert rows == checker.preconditions() == output_rows(gate.PRECONDITION)
    assert len(rows) == 32
    assert [row["precondition_id"] for row in rows] == [f"PRE_{number:03d}" for number in range(1, 33)]
    assert sum(row["completeness_status"] == "complete" for row in rows) == 16
    assert sum(row["completeness_status"] == "incomplete" for row in rows) == 16
    assert sum(row["implementation_blocking"] == "true" for row in rows) == 16


@pytest.mark.parametrize("precondition_id", [f"PRE_{number:03d}" for number in range(1, 13)])
def test_identity_and_exact4_prefix_is_complete(precondition_id: str) -> None:
    row = next(row for row in gate._preconditions() if row["precondition_id"] == precondition_id)
    assert row["completeness_status"] == "complete"
    assert row["implementation_blocking"] == "false"


@pytest.mark.parametrize(
    ("precondition_id", "blocker"),
    [
        ("PRE_013", "ADMIT_013_POST_DOWNLOAD_ROUTING_RESPONSIBILITY_UNRESOLVED"),
        ("PRE_014", "ADMIT_013_ADMIT_012_VALIDATION_DEPENDENCY_UNRESOLVED"),
        ("PRE_015", "ADMIT_013_ADMIT_012_VALIDATION_DEPENDENCY_UNRESOLVED"),
        ("PRE_016", "ADMIT_013_DOWNLOAD_OUTCOME_POLICY_UNRESOLVED"),
        ("PRE_018", "ADMIT_013_DOWNLOAD_OUTCOME_POLICY_UNRESOLVED"),
        ("PRE_019", "ADMIT_013_DOWNLOAD_OUTCOME_POLICY_UNRESOLVED"),
        ("PRE_020", "ADMIT_013_INTEGRITY_COMPARISON_AUTHORITY_UNRESOLVED"),
        ("PRE_021", "ADMIT_013_INTEGRITY_COMPARISON_AUTHORITY_UNRESOLVED"),
        ("PRE_022", "ADMIT_013_INTEGRITY_COMPARISON_AUTHORITY_UNRESOLVED"),
        ("PRE_023", "ADMIT_013_INTEGRITY_COMPARISON_AUTHORITY_UNRESOLVED"),
        ("PRE_024", "ADMIT_013_INTEGRITY_COMPARISON_AUTHORITY_UNRESOLVED"),
        ("PRE_026", "ADMIT_013_DOWNLOAD_OUTCOME_POLICY_UNRESOLVED"),
        ("PRE_027", "ADMIT_013_MULTI_FAILURE_PRECEDENCE_UNRESOLVED"),
        ("PRE_028", "ADMIT_013_DOWNLOAD_OUTCOME_POLICY_UNRESOLVED"),
        ("PRE_029", "ADMIT_013_STANDALONE_SIGNATURE_UNRESOLVED"),
        ("PRE_030", "ADMIT_013_RESULT_CONTRACT_UNRESOLVED"),
    ],
)
def test_incomplete_rows_fail_closed(precondition_id: str, blocker: str) -> None:
    row = next(row for row in gate._preconditions() if row["precondition_id"] == precondition_id)
    assert row["completeness_status"] == "incomplete"
    assert row["implementation_blocking"] == "true"
    assert row["blocking_reason"] == blocker
    assert row["precondition_passed"] == "false"


def test_status_exact_enum_and_admit013_boundary(snapshot) -> None:
    rows = [row for row in gate._rows(snapshot, gate.ADMIT012_STATUS_ENUM) if row["row_kind"] == "canonical_enum"]
    assert [(row["status_value"], row["success_member"]) for row in rows] == [("success", "true"), ("failure", "false")]
    assert rows[0]["future_admit_013_disposition"] == "pending_integrity_match_checks_not_implemented_here"
    assert rows[1]["future_admit_013_disposition"] == "blocked_not_implemented_here"
    assert next(row for row in gate._preconditions() if row["precondition_id"] == "PRE_017")["completeness_status"] == "complete"


@pytest.mark.parametrize(
    ("field_name", "exact_type"),
    [("download_result_status", "str"), ("observed_http_status", "int"),
     ("observed_content_length_bytes", "int"), ("observed_sha256", "str")],
)
def test_exact4_exact_builtin_types(snapshot, field_name: str, exact_type: str) -> None:
    row = next(row for row in gate._rows(snapshot, gate.ADMIT012_FIELD_CONTRACT) if row["field_name"] == field_name)
    assert row["exact_builtin_type"] == exact_type
    assert row["subclasses_allowed"] == "false"
    assert row["normalization_allowed"] == "false"


def test_http_structural_and_future_success_bounds_are_distinct(snapshot, manifest) -> None:
    row = next(row for row in gate._rows(snapshot, gate.ADMIT012_FIELD_CONTRACT) if row["field_name"] == "observed_http_status")
    assert (row["legal_minimum"], row["legal_maximum"]) == ("100", "599")
    assert (row["future_success_minimum"], row["future_success_maximum"]) == ("200", "299")
    assert row["admit_012_executes_success_judgment"] == "false"
    assert manifest["http_success_range_adopted_by_admit_013"] is False


def test_content_zero_allowed_and_not_recomputed(snapshot, manifest) -> None:
    row = next(row for row in gate._rows(snapshot, gate.ADMIT012_FIELD_CONTRACT) if row["field_name"] == "observed_content_length_bytes")
    assert ">= 0" in row["value_contract"] and "no V1 upper bound" in row["value_contract"]
    truth = {row["case_id"]: row for row in gate._rows(snapshot, gate.ADMIT012_FIELD_TRUTH)}
    assert truth["VALID_CONTENT_ZERO"]["observed_contract_outcome"] == "contract_valid"
    assert manifest["zero_content_length_structurally_allowed"] is True
    assert manifest["zero_content_length_admit_013_disposition"] == "unresolved"


def test_sha_exact_grammar_is_not_integrity(snapshot, manifest) -> None:
    row = next(row for row in gate._rows(snapshot, gate.ADMIT012_FIELD_CONTRACT) if row["field_name"] == "observed_sha256")
    assert row["value_contract"] == "exactly 64 ASCII lowercase hexadecimal characters [0-9a-f]{64}"
    assert manifest["syntactic_sha_is_integrity_verdict"] is False
    assert next(row for row in gate._preconditions() if row["precondition_id"] == "PRE_025")["completeness_status"] == "complete"


@pytest.mark.parametrize(
    "case_id",
    ["BOUNDARY_FAILURE_STATUS", "BOUNDARY_VALID_4XX", "BOUNDARY_VALID_5XX_FAILURE"],
)
def test_admit012_passes_structurally_legal_failure_4xx_5xx(snapshot, case_id: str) -> None:
    row = next(row for row in gate._rows(snapshot, gate.ADMIT012_FIELD_TRUTH) if row["case_id"] == case_id)
    assert row["observed_contract_outcome"] == "contract_valid"
    assert row["future_admit_013_disposition"] == "blocked_not_implemented_here"


@pytest.mark.parametrize(
    "manifest_key",
    [
        "expected_content_length_authority_present",
        "content_length_comparison_contract_present",
        "trusted_expected_sha256_authority_present",
        "sha256_comparison_contract_present",
        "explicit_integrity_verdict_authority_present",
        "source_or_artifact_sha_admissible_as_expected_download_sha",
        "provider_transport_failure_taxonomy_complete",
        "multi_failure_precedence_frozen",
        "reason_vocabulary_frozen",
        "standalone_signature_frozen",
        "formal_result_contract_frozen",
        "admit_012_exact10_direct_cross_rule_result_contract_available",
    ],
)
def test_missing_semantic_authority_stays_false(manifest, manifest_key: str) -> None:
    assert manifest[manifest_key] is False


def test_routing_and_prior_admit012_dependency_are_not_inferred(manifest) -> None:
    assert manifest["admit_013_routing_responsibility"] == "unresolved"
    assert manifest["admit_012_revalidation_or_prerequisite_boundary"] == "unresolved"
    assert manifest["cross_rule_aggregation_implemented"] is False


def test_no_current_real_download_observation_or_authorized_execution(manifest) -> None:
    assert manifest["authorized_admit_013_download_execution_count"] == 0
    assert manifest["real_download_result_observation_count"] == 0
    assert manifest["historical_real_download_or_provider_representation_count"] > 0


def test_occurrence_inventory_all_authority_classes_and_exact_count(snapshot, manifest) -> None:
    rows = gate._occurrences(snapshot)
    assert rows == output_rows(gate.OCCURRENCE)
    assert len(rows) == manifest["occurrence_row_count"] == 9517
    assert set(manifest["occurrence_authority_counts"]) == set(gate.AUTHORITY_LEVELS)
    assert all(manifest["occurrence_authority_counts"][key] > 0 for key in gate.AUTHORITY_LEVELS)


@pytest.mark.parametrize(
    "source_kind",
    [
        "synthetic_test_fixture", "source_or_artifact_attestation_hash",
        "historical_real_download_execution_observation",
        "historical_real_provider_observation", "schema_authority_absence",
        "schema_or_committed_contract_representation", "documentation_example",
        "placeholder", "unrelated_numeric_or_status_value",
    ],
)
def test_observed_inventory_classification_kinds(manifest, source_kind: str) -> None:
    assert manifest["observed_value_source_kind_counts"][source_kind] > 0


def test_attestation_hashes_never_become_trusted_download_authority() -> None:
    rows = output_rows(gate.OBSERVED)
    attestations = [row for row in rows if row["source_kind"] == "source_or_artifact_attestation_hash"]
    assert attestations
    assert all(row["trusted_comparison_authority"] == "false" for row in attestations)
    assert all("never a trusted expected download checksum" in row["notes"] for row in attestations)


def test_fixture_status_and_http_are_not_real_observations() -> None:
    rows = [row for row in output_rows(gate.OBSERVED) if row["source_kind"] == "synthetic_test_fixture"]
    assert rows
    assert all(row["real_observed_value"] == "false" for row in rows)
    assert all(row["produced_by_download_execution"] == "false" for row in rows)


def test_source_boundary_fixed_and_fully_pinned(snapshot) -> None:
    rows = gate._source_rows(snapshot)
    assert rows == output_rows(gate.SOURCE_AUDIT)
    assert len(rows) == 545
    assert all(row["tracked_regular_non_symlink"] == "true" for row in rows)
    assert all(row["pinned_fd_read"] == row["triple_sha256_passed"] == "true" for row in rows)
    digest = hashlib.sha256(json.dumps([source.path.as_posix() for source in snapshot], separators=(",", ":")).encode()).hexdigest()
    assert digest == gate.EXPECTED_PATH_LIST_SHA256


def test_exact16_issue_continuity_and_exact7_additions(snapshot) -> None:
    inherited = gate._rows(snapshot, gate.RUNTIME_ISSUES)
    actual = gate._issue_rows(snapshot)
    assert actual[:16] == inherited == output_rows(gate.ISSUE)[:16]
    assert len(actual) == 23
    assert [row["issue_id"] for row in actual[-7:]] == [item[0] for item in gate.NEW_ISSUES]
    assert all(row["issue_origin"] == gate.STAGE and row["integration_transition"] == "new_open" for row in actual[-7:])


def test_readiness_exact_true_and_false_sets(manifest) -> None:
    assert manifest["readiness"] == gate._readiness() == checker.readiness()
    assert all(manifest[key] is value for key, value in gate._readiness().items())
    assert manifest["recommended_next_step"] == "design_covapie_admit_013_download_outcome_and_integrity_contract_v1"
    assert manifest["step12d_status"] == "smoke_legality_only_not_final_training_feature_contract"


def test_production_contains_no_evaluator_result_adapter_or_runtime_implementation() -> None:
    path = REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_preconditions_audit.py"
    text = path.read_text()
    tree = ast.parse(text)
    names = {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    assert "evaluate_admit_013" not in names
    assert "Admit013EvaluationResult" not in names
    assert "_evaluate_registered_admit_013" not in names
    assert not {"EVALUATOR_REGISTRY", "evaluate_admission_rule"} & names


def test_materializer_deterministic_noop_and_mismatch_fail_closed(tmp_path, monkeypatch, snapshot) -> None:
    monkeypatch.setattr(gate, "build_frozen_source_snapshot", lambda: snapshot)
    first = tmp_path / "first"
    second = tmp_path / "second"
    gate.materialize_audit(first)
    gate.materialize_audit(second)
    assert {path.name: path.read_bytes() for path in first.iterdir()} == {path.name: path.read_bytes() for path in second.iterdir()}
    before = {path.name: (path.stat().st_ino, path.read_bytes()) for path in first.iterdir()}
    gate.materialize_audit(first)
    assert before == {path.name: (path.stat().st_ino, path.read_bytes()) for path in first.iterdir()}
    (first / gate.PRECONDITION).write_bytes(b"broken")
    with pytest.raises(ValueError, match="mismatch"):
        gate.materialize_audit(first)


def test_materializer_gpfs_einval_fails_closed_without_replace(tmp_path, monkeypatch, snapshot) -> None:
    monkeypatch.setattr(gate, "build_frozen_source_snapshot", lambda: snapshot)
    monkeypatch.setattr(gate, "_rename_noreplace", lambda source, target: (_ for _ in ()).throw(OSError(errno.EINVAL, "EINVAL")))
    root = tmp_path / "target"
    with pytest.raises(OSError) as error:
        gate.materialize_audit(root)
    assert error.value.errno == errno.EINVAL
    assert not root.exists() and not list(tmp_path.glob("*.staging"))
    tree = ast.parse((REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_preconditions_audit.py").read_text())
    assert not [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "os"
        and node.func.attr == "replace"
    ]


@pytest.mark.parametrize(
    ("filename", "needle", "replacement"),
    [
        (checker.PRE, "canonical failure-status decision", "canonical failure-status DECISION"),
        (checker.OCC, "primary_committed_contract", "committed_runtime_contract"),
        (checker.OBS, "schema_authority_absence", "synthetic_test_fixture"),
        (checker.SRC, "pinned_fd_read", "pinned_FD_read"),
        (checker.ISSUE, "ADMIT_013_RESULT_CONTRACT_UNRESOLVED", "ADMIT_013_RESULT_CONTRACT_RESOLVED"),
    ],
)
def test_synchronized_semantic_tamper_rejected(
    tmp_path, monkeypatch, checker_records, filename: str, needle: str, replacement: str
) -> None:
    root = copy_output(tmp_path)
    path = root / filename
    text = path.read_text()
    assert needle in text
    path.write_text(text.replace(needle, replacement, 1))
    resync_manifest(root)
    reject_with_cached_snapshot(root, monkeypatch, checker_records)


def test_synchronized_manifest_tamper_and_unknown_key_rejected(tmp_path, monkeypatch, checker_records) -> None:
    root = copy_output(tmp_path)
    path = root / checker.MANIFEST
    value = json.loads(path.read_text())
    value["source_count"] = 544
    value["unknown_key"] = True
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    reject_with_cached_snapshot(root, monkeypatch, checker_records)


def test_checker_pinned_output_traversal_and_regular_outputs(monkeypatch, checker_records) -> None:
    monkeypatch.setattr(checker, "snapshot", lambda: checker_records)
    checker.validate(ROOT)
    assert {path.name for path in ROOT.iterdir()} == set(checker.FILES)
    assert all(path.is_file() and not path.is_symlink() for path in ROOT.iterdir())


def test_source_identity_race_fails_closed(snapshot) -> None:
    source = snapshot[0]
    wrong = (0, 0, 0)
    with pytest.raises(ValueError, match="identity drift"):
        gate._pinned_read(source.path, wrong)


def test_checker_rejects_base_ancestry_before_output_read(monkeypatch) -> None:
    original = checker.git

    def fake(args, text=True):
        if args[:2] == ["merge-base", "--is-ancestor"]:
            return type("Result", (), {"returncode": 1, "stdout": ""})()
        return original(args, text)

    monkeypatch.setattr(checker, "git", fake)
    with pytest.raises(AssertionError):
        checker.snapshot()


@pytest.mark.parametrize(
    "relative_path",
    [
        "src/covalent_ext/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_preconditions_audit.py",
        "scripts/check_covapie_bulk_download_admission_admit_013_formal_evaluator_interface_preconditions_audit_v1.py",
    ],
)
def test_isolated_import_is_silent(relative_path: str) -> None:
    code = (
        "import importlib.util, pathlib, sys; "
        f"p=pathlib.Path({str(REPO_ROOT / relative_path)!r}); "
        "s=importlib.util.spec_from_file_location('isolated_module',p); "
        "m=importlib.util.module_from_spec(s); sys.modules[s.name]=m; s.loader.exec_module(m)"
    )
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(REPO_ROOT / "src")
    result = subprocess.run([sys.executable, "-B", "-c", code], cwd=REPO_ROOT, env=environment, capture_output=True, text=True, check=False)
    assert result.returncode == 0
    assert result.stdout == result.stderr == ""


def test_no_forbidden_artifacts_in_exact6() -> None:
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".tmp", ".part"}
    assert {path.name for path in ROOT.iterdir()} == set(gate.FILES)
    assert all(path.suffix not in forbidden for path in ROOT.iterdir())
