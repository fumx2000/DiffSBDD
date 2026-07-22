from __future__ import annotations

import ast
import csv
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
    covapie_bulk_download_admission_admit_012_download_integrity_field_contract_design_gate as gate,
)

CHECKER_PATH = REPO_ROOT / "scripts/check_covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1.py"
SPEC = importlib.util.spec_from_file_location("admit012_field_checker", CHECKER_PATH)
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
ROOT = REPO_ROOT / checker.OUTPUT_ROOT
VALID_SHA = "0123456789abcdef" * 4


class StringSubclass(str):
    pass


class IntSubclass(int):
    pass


def _classify(status: object = "success", http: object = 200,
              content: object = 1, sha: object = VALID_SHA):
    return gate.classify_admit_012_download_integrity_fields_design(status, http, content, sha)


def _copied(tmp_path: Path) -> Path:
    target = tmp_path / "outputs"
    shutil.copytree(ROOT, target)
    return target


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=tuple(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(stream.getvalue())


def _resync(root: Path) -> None:
    path = root / checker.MANIFEST_FILE
    manifest = json.loads(path.read_text())
    manifest["output_sha256"] = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in checker.FILES[:-1]
    }
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def _reject(root: Path) -> None:
    with pytest.raises(AssertionError):
        checker.validate(root, enforce_frozen_hashes=False)


def test_rule_identity_phase_and_exact4_contract():
    assert gate.ADMISSION_RULE_ID == "ADMIT_012"
    assert gate.ADMISSION_RULE_NAME == "future_download_integrity_fields_required"
    assert gate.EVIDENCE_SOURCE == "future_download_result"
    assert gate.EVALUATION_PHASE == "post_download"
    assert gate.REQUIRED_STATUS == "download_status_http_status_content_length_and_sha256_present"
    assert gate.BLOCKING_REASON == "download_integrity_fields_missing"
    assert gate.EXACT4_FIELDS == checker.FIELDS


def test_exact_field_order_and_full_contract_rows():
    rows = gate._contract_rows()
    assert rows == checker._expected_contract_rows()
    assert [row["field_order"] for row in rows] == ["1", "2", "3", "4"]
    assert [row["field_name"] for row in rows] == list(gate.EXACT4_FIELDS)
    assert all(row["presence_required"] == "true" and row["subclasses_allowed"] == "false" for row in rows)


@pytest.mark.parametrize("value", [None, 1, StringSubclass("success")])
def test_status_requires_exact_builtin_str_and_rejects_subclass(value: object):
    result = _classify(status=value)
    assert result.contract_outcome == "invalid"
    assert result.reason == "DOWNLOAD_RESULT_STATUS_TYPE_INVALID"


def test_status_complete_closed_enum_and_no_alias_normalization():
    assert gate.ALLOWED_DOWNLOAD_RESULT_STATUSES == ("success", "failure")
    assert _classify(status="success").contract_outcome == "contract_valid"
    assert _classify(status="failure").contract_outcome == "contract_valid"
    for value in ("", "unknown", "SUCCESS", " success", "success "):
        assert _classify(status=value).reason == "DOWNLOAD_RESULT_STATUS_VALUE_INVALID"


def test_status_success_subset_is_exact_and_admit012_does_not_apply_it():
    assert gate.SUCCESS_DOWNLOAD_RESULT_STATUSES == ("success",)
    assert _classify(status="failure").contract_outcome == "contract_valid"
    canonical = [row for row in gate._enum_rows() if row["row_kind"] == "canonical_enum"]
    assert [row["status_value"] for row in canonical] == ["success", "failure"]
    assert [row["success_member"] for row in canonical] == ["true", "false"]


@pytest.mark.parametrize("value", [100, 200, 299, 300, 599])
def test_http_exact_int_structural_range_accepts_boundaries(value: int):
    assert _classify(http=value).contract_outcome == "contract_valid"


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        (False, "OBSERVED_HTTP_STATUS_TYPE_INVALID"),
        (IntSubclass(200), "OBSERVED_HTTP_STATUS_TYPE_INVALID"),
        ("200", "OBSERVED_HTTP_STATUS_TYPE_INVALID"),
        (99, "OBSERVED_HTTP_STATUS_RANGE_INVALID"),
        (600, "OBSERVED_HTTP_STATUS_RANGE_INVALID"),
    ],
)
def test_http_rejects_bool_subclass_string_and_out_of_range(value: object, reason: str):
    assert _classify(http=value).reason == reason


@pytest.mark.parametrize("value", [0, 1, 10**30])
def test_content_length_accepts_zero_one_and_unbounded_large_integer(value: int):
    assert _classify(content=value).contract_outcome == "contract_valid"


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        (False, "OBSERVED_CONTENT_LENGTH_BYTES_TYPE_INVALID"),
        (IntSubclass(1), "OBSERVED_CONTENT_LENGTH_BYTES_TYPE_INVALID"),
        ("1", "OBSERVED_CONTENT_LENGTH_BYTES_TYPE_INVALID"),
        (-1, "OBSERVED_CONTENT_LENGTH_BYTES_RANGE_INVALID"),
    ],
)
def test_content_length_rejects_bool_subclass_string_and_negative(value: object, reason: str):
    assert _classify(content=value).reason == reason


def test_sha_accepts_only_exact_lowercase_ascii_hex64():
    assert len(VALID_SHA) == 64
    assert _classify(sha=VALID_SHA).contract_outcome == "contract_valid"
    assert _classify(sha="abcdef0123456789" * 4).contract_outcome == "contract_valid"


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        (None, "OBSERVED_SHA256_TYPE_INVALID"),
        (VALID_SHA.encode(), "OBSERVED_SHA256_TYPE_INVALID"),
        (StringSubclass(VALID_SHA), "OBSERVED_SHA256_TYPE_INVALID"),
        ("", "OBSERVED_SHA256_FORMAT_INVALID"),
        ("a" * 63, "OBSERVED_SHA256_FORMAT_INVALID"),
        ("a" * 65, "OBSERVED_SHA256_FORMAT_INVALID"),
        (VALID_SHA.upper(), "OBSERVED_SHA256_FORMAT_INVALID"),
        ("A" + VALID_SHA[1:], "OBSERVED_SHA256_FORMAT_INVALID"),
        ("g" + VALID_SHA[1:], "OBSERVED_SHA256_FORMAT_INVALID"),
        (" " + VALID_SHA[:63], "OBSERVED_SHA256_FORMAT_INVALID"),
        ("0x" + VALID_SHA[:62], "OBSERVED_SHA256_FORMAT_INVALID"),
        ("sha256:" + VALID_SHA[:57], "OBSERVED_SHA256_FORMAT_INVALID"),
    ],
)
def test_sha_rejects_type_length_case_nonhex_whitespace_and_prefixes(value: object, reason: str):
    assert _classify(sha=value).reason == reason


def test_missing_and_present_but_invalid_are_distinct():
    missing = gate.classify_admit_012_download_integrity_fields_design()
    none_present = _classify(status=None)
    empty_present = _classify(status="")
    zero_present = _classify(content=0)
    false_present = _classify(http=False)
    assert (missing.contract_outcome, missing.reason) == ("missing", "DOWNLOAD_RESULT_STATUS_MISSING")
    assert none_present.contract_outcome == empty_present.contract_outcome == false_present.contract_outcome == "invalid"
    assert zero_present.contract_outcome == "contract_valid"


def test_presence_phase_precedes_all_type_and_value_validation():
    result = gate.classify_admit_012_download_integrity_fields_design(
        "unknown", 99, -1, gate._MISSING
    )
    assert (result.contract_outcome, result.reason, result.first_failing_field) == (
        "missing", "OBSERVED_SHA256_MISSING", "observed_sha256"
    )


def test_all_present_field_order_and_type_before_value_precedence():
    assert _classify(status="unknown", http=99).reason == "DOWNLOAD_RESULT_STATUS_VALUE_INVALID"
    assert _classify(http="200", content=-1).reason == "OBSERVED_HTTP_STATUS_TYPE_INVALID"
    assert _classify(http=99, content=-1).reason == "OBSERVED_HTTP_STATUS_RANGE_INVALID"
    assert _classify(content=-1, sha=VALID_SHA.upper()).reason == "OBSERVED_CONTENT_LENGTH_BYTES_RANGE_INVALID"


def test_multi_invalid_truth_cases_freeze_exact_precedence():
    rows = {row["case_id"]: row for row in gate._truth_rows()}
    expected = {
        "MULTI_EARLIER_INVALID_LATER_MISSING": "OBSERVED_SHA256_MISSING",
        "MULTI_MISSING_PRECEDENCE": "DOWNLOAD_RESULT_STATUS_MISSING",
        "MULTI_TYPE_FAILURES": "DOWNLOAD_RESULT_STATUS_TYPE_INVALID",
        "MULTI_TYPE_VALUE_FAILURES": "OBSERVED_HTTP_STATUS_TYPE_INVALID",
        "MULTI_STATUS_HTTP_INVALID": "DOWNLOAD_RESULT_STATUS_VALUE_INVALID",
        "MULTI_HTTP_CONTENT_INVALID": "OBSERVED_HTTP_STATUS_RANGE_INVALID",
        "MULTI_CONTENT_SHA_INVALID": "OBSERVED_CONTENT_LENGTH_BYTES_RANGE_INVALID",
    }
    assert {case_id: rows[case_id]["expected_reason"] for case_id in expected} == expected


def test_structurally_valid_failure_status_is_admit012_contract_valid():
    result = _classify(status="failure", http=200)
    assert result.contract_outcome == "contract_valid"
    row = next(row for row in gate._truth_rows() if row["case_id"] == "BOUNDARY_FAILURE_STATUS")
    assert row["future_admit_013_disposition"] == "blocked_not_implemented_here"


@pytest.mark.parametrize("http", [404, 503])
def test_structurally_valid_4xx_and_5xx_are_not_rejected_by_admit012(http: int):
    assert _classify(http=http).contract_outcome == "contract_valid"
    row = next(row for row in gate._truth_rows() if row["observed_http_status_representation"] == str(http) and row["case_group"] == "admit_013_boundary")
    assert row["future_admit_013_disposition"] == "blocked_not_implemented_here"


def test_design_result_and_classifier_are_explicitly_nonformal():
    result = _classify()
    assert type(result) is gate.Admit012DownloadIntegrityClassificationDesign
    assert result.contract_outcome == "contract_valid"
    assert "Design" in type(result).__name__
    assert gate.Admit012DownloadIntegrityFieldContractDesign().field_order == gate.EXACT4_FIELDS


def test_exact16_issue_successor_closes_only_authorized_four():
    rows = gate._issue_rows(gate.build_frozen_source_snapshot())
    assert len(rows) == 16
    by_id = {row["issue_id"]: row for row in rows}
    assert all(by_id[issue]["status"] == "resolved" and by_id[issue]["integration_transition"] == gate.ISSUE_TRANSITION for issue in gate.RESOLVED_ISSUES)
    assert all(by_id[issue]["status"] == "open" for issue in gate.OPEN_REQUIRED_ISSUES)
    assert by_id["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] == "ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015"


def test_routing_signature_result_and_runtime_readiness_remain_false_or_open():
    readiness = gate._readiness()
    true_keys = {
        "admit_012_preconditions_audited", "admit_012_download_integrity_field_contract_frozen",
        "admit_012_download_result_status_enum_frozen", "admit_012_field_semantics_complete",
        "admit_012_presence_semantics_resolved", "admit_012_validation_precedence_resolved",
        "admit_012_admit_013_field_contract_boundary_frozen", "feature_semantics_audit_required_before_training",
    }
    assert all(readiness[key] is True for key in true_keys)
    assert all(value is False for key, value in readiness.items() if key not in true_keys)
    manifest = json.loads((ROOT / gate.MANIFEST_FILE).read_text())
    assert manifest["ADMIT_012_STANDALONE_SIGNATURE_UNRESOLVED"] == "open"
    assert manifest["ADMIT_012_RESULT_CONTRACT_UNRESOLVED"] == "open"


def test_no_evaluator_formal_result_adapter_registry_dispatcher_or_admit013_implementation():
    path = REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_design_gate.py"
    tree = ast.parse(path.read_text())
    functions = {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    classes = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    assert "evaluate_admit_012" not in functions
    assert "Admit012EvaluationResult" not in classes
    assert not {name for name in functions if name.startswith("register_") or "dispatcher" in name or "adapter" in name}
    assert not {name for name in functions if "admit_013" in name.lower()}


def test_design_classifier_is_pure_in_memory_and_does_not_recompute_files():
    source = ast.get_source_segment(
        (REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_design_gate.py").read_text(),
        next(node for node in ast.walk(ast.parse((REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_design_gate.py").read_text())) if isinstance(node, ast.FunctionDef) and node.name == "classify_admit_012_download_integrity_fields_design"),
    )
    assert source is not None
    assert all(token not in source for token in ("open(", "Path(", "socket", "urlopen", "requests", "hashlib"))
    assert _classify().contract_outcome == "contract_valid"


def test_source_boundary_is_minimal_fixed_order_and_triple_sha_attested():
    snapshot = gate.build_frozen_source_snapshot()
    rows = gate._source_rows(snapshot)
    assert len(snapshot) == len(rows) == gate.EXPECTED_SOURCE_COUNT == 29
    assert [row["source_relative_path"] for row in rows] == list(gate.SOURCE_PATHS)
    assert all(row["pinned_fd_read"] == row["triple_sha256_passed"] == row["source_boundary_passed"] == "true" for row in rows)
    assert all(not row["source_relative_path"].startswith(("data/raw/", "checkpoints/")) for row in rows)


def test_materializer_is_deterministic_inode_preserving_noop_and_mismatch_closed(tmp_path: Path):
    root = tmp_path / "generated"
    gate.materialize_contract(root)
    before = {path.name: (path.stat().st_ino, path.read_bytes()) for path in root.iterdir()}
    gate.materialize_contract(root)
    assert before == {path.name: (path.stat().st_ino, path.read_bytes()) for path in root.iterdir()}
    (root / gate.CONTRACT_FILE).write_text("tampered\n")
    with pytest.raises(ValueError, match="mismatch"):
        gate.materialize_contract(root)


def test_materializer_gpfs_einval_fails_closed_without_replace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path / "target"
    monkeypatch.setattr(gate, "_rename_noreplace", lambda _source, _target: (_ for _ in ()).throw(OSError(22, "EINVAL")))
    with pytest.raises(OSError) as caught:
        gate.materialize_contract(root)
    assert caught.value.errno == 22 and not root.exists()
    assert not list(tmp_path.glob(".*.staging"))
    tree = ast.parse((REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_design_gate.py").read_text())
    assert not [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "os"
        and node.func.attr == "replace"
    ]


def test_materializer_rejects_symlink_output_parent(tmp_path: Path):
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError, match="parent"):
        gate.materialize_contract(link / "outputs")


def test_checker_rejects_synchronized_contract_and_enum_semantic_tamper(tmp_path: Path):
    root = _copied(tmp_path / "contract")
    rows = list(csv.DictReader((root / checker.CONTRACT_FILE).read_text().splitlines()))
    rows[0]["subclasses_allowed"] = "true"
    _write_csv(root / checker.CONTRACT_FILE, rows)
    _resync(root)
    _reject(root)

    root = _copied(tmp_path / "enum")
    rows = list(csv.DictReader((root / checker.ENUM_FILE).read_text().splitlines()))
    rows[2]["promoted_to_canonical"] = "true"
    _write_csv(root / checker.ENUM_FILE, rows)
    _resync(root)
    _reject(root)


def test_checker_rejects_synchronized_truth_issue_and_source_semantic_tamper(tmp_path: Path):
    root = _copied(tmp_path / "truth")
    rows = list(csv.DictReader((root / checker.TRUTH_FILE).read_text().splitlines()))
    target = next(row for row in rows if row["case_id"] == "BOUNDARY_VALID_4XX")
    target["future_admit_013_disposition"] = "pending_integrity_match_checks_not_implemented_here"
    _write_csv(root / checker.TRUTH_FILE, rows)
    _resync(root)
    _reject(root)

    root = _copied(tmp_path / "issue")
    rows = list(csv.DictReader((root / checker.ISSUE_FILE).read_text().splitlines()))
    next(row for row in rows if row["issue_id"] == "DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED")["status"] = "open"
    _write_csv(root / checker.ISSUE_FILE, rows)
    _resync(root)
    _reject(root)

    root = _copied(tmp_path / "source")
    rows = list(csv.DictReader((root / checker.SOURCE_FILE).read_text().splitlines()))
    rows[0]["filesystem_sha256"] = "0" * 64
    _write_csv(root / checker.SOURCE_FILE, rows)
    _resync(root)
    _reject(root)


def test_checker_rejects_manifest_readiness_tamper_and_unknown_key(tmp_path: Path):
    root = _copied(tmp_path / "readiness")
    path = root / checker.MANIFEST_FILE
    value = json.loads(path.read_text())
    value["ready_for_training"] = True
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    _reject(root)

    root = _copied(tmp_path / "unknown")
    path = root / checker.MANIFEST_FILE
    value = json.loads(path.read_text())
    value["unknown_key"] = True
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    _reject(root)


def test_checker_validates_exact_output_inventory_and_frozen_hashes():
    checker.validate(ROOT)
    assert set(checker.FROZEN_SHA256) == set(checker.FILES)
    assert {path.name for path in ROOT.iterdir()} == set(checker.FILES)


def test_production_and_checker_import_silently_without_output_or_pyc(tmp_path: Path):
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(REPO_ROOT / "src")
    production = subprocess.run(
        [sys.executable, "-B", "-c", "import covalent_ext.covapie_bulk_download_admission_admit_012_download_integrity_field_contract_design_gate"],
        cwd=tmp_path, env=environment, capture_output=True, text=True, check=False,
    )
    checker_import = subprocess.run(
        [sys.executable, "-B", "-c", f"import importlib.util; s=importlib.util.spec_from_file_location('c', {str(CHECKER_PATH)!r}); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)"],
        cwd=tmp_path, env=environment, capture_output=True, text=True, check=False,
    )
    assert production.returncode == checker_import.returncode == 0
    assert production.stdout == production.stderr == checker_import.stdout == checker_import.stderr == ""
    assert not list(tmp_path.rglob("*.pyc"))


def test_no_forbidden_or_extra_derived_artifacts():
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".tmp", ".part"}
    assert len(list(ROOT.iterdir())) == 6
    assert all(path.is_file() and path.suffix not in forbidden for path in ROOT.iterdir())
    manifest = json.loads((ROOT / checker.MANIFEST_FILE).read_text())
    assert manifest["output_files"] == list(checker.FILES)
    assert manifest["authorized_admit_012_download_execution_count"] == 0
