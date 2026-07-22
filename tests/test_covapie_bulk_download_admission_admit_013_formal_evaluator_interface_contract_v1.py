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
import stat
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_design_gate
    as gate,
)

CHECKER_PATH = REPO_ROOT / "scripts/check_covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1.py"
SPEC = importlib.util.spec_from_file_location("admit013_formal_checker", CHECKER_PATH)
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
ROOT = REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT
STAGE_PATHS = (
    "src/covalent_ext/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_design_gate.py",
    "scripts/check_covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1.py",
    "tests/test_covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1.py",
    "docs/covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1_summary.md",
    *((gate.DEFAULT_OUTPUT_ROOT / name).as_posix() for name in gate.OUTPUT_FILES),
)
FORBIDDEN_SUFFIXES = {
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
    ".npz", ".tmp", ".part",
}


def git(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments], cwd=root, capture_output=True, text=True, check=False
    )


def rows(name: str, root: Path = ROOT) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO((root / name).read_text(), newline="")))


def copied_output(tmp_path: Path) -> Path:
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


def reject(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    records: tuple[tuple[str, bytes, str, str], ...],
) -> None:
    monkeypatch.setattr(checker, "source_snapshot", lambda: records)
    with pytest.raises(AssertionError):
        checker.validate(root, enforce_frozen_hashes=False)


def validate_stage_inventory(
    repository: Path,
    base_commit: str,
    stage_paths: tuple[str, ...] = STAGE_PATHS,
) -> str:
    expected = set(stage_paths)
    assert len(expected) == 10
    assert git(repository, "merge-base", "--is-ancestor", base_commit, "HEAD").returncode == 0
    output_root = repository / gate.DEFAULT_OUTPUT_ROOT
    assert output_root.is_dir() and not output_root.is_symlink()
    assert {
        path.relative_to(repository).as_posix() for path in output_root.iterdir()
    } == {(gate.DEFAULT_OUTPUT_ROOT / name).as_posix() for name in gate.OUTPUT_FILES}
    observed = {
        path.relative_to(repository).as_posix()
        for directory in ("src/covalent_ext", "scripts", "tests", "docs")
        for path in (repository / directory).glob(
            "*admit_013_formal_evaluator_interface_contract*"
        )
    } | {
        path.relative_to(repository).as_posix() for path in output_root.iterdir()
    }
    assert observed == expected
    for relative in stage_paths:
        path = repository / relative
        item = os.lstat(path)
        assert stat.S_ISREG(item.st_mode) and not stat.S_ISLNK(item.st_mode)
        assert path.stat().st_size < 100 * 1024 * 1024
        assert path.suffix not in FORBIDDEN_SUFFIXES
    assert git(repository, "diff", "--cached", "--quiet", "--", *stage_paths).returncode == 0
    tracked = set(git(repository, "ls-files", "--", *stage_paths).stdout.splitlines())
    untracked = set(
        git(repository, "ls-files", "--others", "--exclude-standard", "--", *stage_paths).stdout.splitlines()
    )
    if tracked == set() and untracked == expected:
        return "pre_commit"
    if tracked == expected and untracked == set():
        assert git(repository, "diff", "--quiet", "--", *stage_paths).returncode == 0
        return "post_commit"
    raise AssertionError("unresolved or mixed stage lifecycle")


def seed_lifecycle_repository(tmp_path: Path) -> tuple[Path, str]:
    repository = tmp_path / "repo"
    repository.mkdir(parents=True)
    assert git(repository, "init", "-q").returncode == 0
    assert git(repository, "config", "user.name", "CovaPIE Test").returncode == 0
    assert git(repository, "config", "user.email", "covapie-test@example.invalid").returncode == 0
    (repository / ".gitignore").write_text("**/__pycache__/\n*.pyc\n.pytest_cache/\n")
    (repository / "README.md").write_text("base\n")
    assert git(repository, "add", ".gitignore", "README.md").returncode == 0
    assert git(repository, "commit", "-q", "-m", "base").returncode == 0
    base_commit = git(repository, "rev-parse", "HEAD").stdout.strip()
    for relative in STAGE_PATHS:
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"stage:{relative}\n")
    return repository, base_commit


@pytest.fixture(scope="module")
def snapshot():
    return gate.build_frozen_source_snapshot()


@pytest.fixture(scope="module")
def checker_records():
    return checker.source_snapshot()


@pytest.fixture(scope="module")
def manifest():
    return json.loads((ROOT / gate.MANIFEST_FILE).read_text())


def test_base_identity_ancestor_and_source_verification_precede_outputs(
    snapshot,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert [gate.BASE_COMMIT, gate.BASE_PARENT, gate.BASE_SUBJECT] == [
        "2eea08835c4ef88d5b810509134f8eef94e3e99e",
        "30c644de3973ba2968ecaa8ebff97159c07678b9",
        "add CovaPIE ADMIT_013 download outcome and integrity contract v1",
    ]
    assert len(snapshot) == 25
    assert git(REPO_ROOT, "merge-base", "--is-ancestor", gate.BASE_COMMIT, "HEAD").returncode == 0
    called = False
    original = checker._git

    def nonancestor(arguments, *, text=True):
        if arguments[:2] == ["merge-base", "--is-ancestor"]:
            return subprocess.CompletedProcess(["git", *arguments], 1, "", "nonancestor")
        return original(arguments, text=text)

    def output_bomb(root):
        nonlocal called
        called = True
        raise AssertionError("output must not be read")

    monkeypatch.setattr(checker, "_git", nonancestor)
    monkeypatch.setattr(checker, "_read_outputs", output_bomb)
    with pytest.raises(AssertionError):
        checker.validate(ROOT)
    assert called is False


def test_exact25_source_boundary_order_sha_mode_and_exclusions(snapshot, checker_records) -> None:
    assert [record.path.as_posix() for record in snapshot] == [path for path, _ in checker.SOURCE_BOUNDARY]
    assert [record.sha256 for record in snapshot] == [digest for _, digest in checker.SOURCE_BOUNDARY]
    assert gate.SOURCE_PATH_LIST_SHA256 == checker.PATH_SHA == "637ca9a10903370510a10d9d8bd619cbd34b9a0ece9e0a032dec74e01039fba5"
    assert gate.SOURCE_PATH_SHA256_PAIRS_SHA256 == checker.PAIR_SHA == "c723622aca05bccc163a0c6837fcc2bbfcd48b75d710101cace4817658245df1"
    assert len(checker_records) == 25
    assert all(record.base_mode in {"100644", "100755"} for record in snapshot)
    assert not any(record.path.parts[:2] == ("data", "raw") or record.path.parts[0] == "checkpoints" for record in snapshot)


def test_admit_013_identity_and_future_signature(manifest) -> None:
    assert manifest["admission_rule_id"] == "ADMIT_013"
    assert manifest["admission_rule_name"] == "download_failure_fail_closed"
    signature = gate.FORMAL_SIGNATURE_DESIGN
    assert list(signature.parameters) == list(gate.PARAMETERS)
    assert len(signature.parameters) == 7
    assert all(parameter.kind is inspect.Parameter.KEYWORD_ONLY for parameter in signature.parameters.values())
    assert all(parameter.default is gate._DESIGN_MISSING for parameter in signature.parameters.values())
    assert signature.return_annotation == "Admit013EvaluationResult"
    assert manifest["future_public_signature"] == gate.FUTURE_PUBLIC_SIGNATURE
    assert manifest["signature_varargs"] is manifest["signature_varkw"] is False
    assert manifest["signature_dynamic_mapping_or_policy_context"] is False
    with pytest.raises(TypeError):
        gate.classify_admit_013_formal_evaluator_interface_design("success")


def test_exact26_reason_exact3_outcome_and_exact5_phase_order(manifest) -> None:
    assert len(gate.REASON_VOCABULARY) == 26
    assert manifest["reason_vocabulary"] == list(gate.REASON_VOCABULARY)
    assert gate.REASON_VOCABULARY[0] == ""
    assert gate.OUTCOMES == ("passed", "blocked", "invalid")
    assert manifest["outcome_vocabulary"] == list(gate.OUTCOMES)
    assert manifest["validation_phase_order"] == list(gate.VALIDATION_PHASES)
    assert manifest["business_failure_precedence"] == list(gate.BUSINESS_REASONS)
    assert not {"UNKNOWN", "OTHER", "INTERNAL_ERROR", "UNEXPECTED"} & set(gate.REASON_VOCABULARY)


def test_exact4_presence_distinguishes_missing_none_false_zero_and_empty() -> None:
    classify = gate.classify_admit_013_formal_evaluator_interface_design
    missing = classify()
    assert (missing.outcome, missing.reason) == ("blocked", gate.MISSING_REASONS[0])
    for value, reason in (
        (None, gate.DOWNLOAD_TYPE_REASONS[0]),
        (False, gate.DOWNLOAD_TYPE_REASONS[0]),
        (0, gate.DOWNLOAD_TYPE_REASONS[0]),
        ("", gate.DOWNLOAD_VALUE_REASONS[0]),
    ):
        result = classify(
            download_result_status=value, observed_http_status=200,
            observed_content_length_bytes=10, observed_sha256=gate.SHA_A,
            expected_sha256=gate.SHA_A,
        )
        assert (result.outcome, result.reason) == ("invalid", reason)


def test_exact4_missing_and_type_value_prefix_semantics() -> None:
    missing = gate.classify_admit_013_formal_evaluator_interface_design(
        download_result_status="success",
    )
    assert missing.canonical_download_result_record == missing.canonical_integrity_authority_record == ()
    assert missing.validated_download_result_fields == ("download_result_status",)
    assert missing.consumed_download_result_fields == gate.DOWNLOAD_FIELDS[:2]
    assert missing.validated_integrity_authority_fields == missing.consumed_integrity_authority_fields == ()
    invalid = gate.classify_admit_013_formal_evaluator_interface_design(
        download_result_status="success", observed_http_status=200,
        observed_content_length_bytes=-1, observed_sha256=gate.SHA_A,
    )
    assert invalid.outcome == "invalid" and invalid.reason == gate.DOWNLOAD_VALUE_REASONS[2]
    assert invalid.canonical_download_result_record == ()
    assert invalid.validated_download_result_fields == gate.DOWNLOAD_FIELDS[:2]
    assert invalid.consumed_download_result_fields == gate.DOWNLOAD_FIELDS


def test_exact_types_ranges_grammar_and_no_normalization() -> None:
    truth = {row["case_id"]: row for row in rows(gate.TRUTH_FILE)}
    for case_id in (
        "STATUS_STR_SUBCLASS", "HTTP_BOOL", "HTTP_INT_SUBCLASS", "CONTENT_BOOL",
        "CONTENT_INT_SUBCLASS", "OBSERVED_SHA_STR_SUBCLASS", "OBSERVED_SHA_UPPERCASE",
        "OBSERVED_SHA_WHITESPACE",
    ):
        assert truth[case_id]["expected_outcome"] == "invalid"
    assert truth["HTTP_BOUNDARY_100"]["expected_outcome"] == "blocked"
    assert truth["HTTP_BOUNDARY_200"]["expected_outcome"] == "passed"
    assert truth["HTTP_BOUNDARY_299"]["expected_outcome"] == "passed"
    assert truth["HTTP_BOUNDARY_599"]["expected_outcome"] == "blocked"
    assert truth["CONTENT_ZERO_STRUCTURAL_BUSINESS_BLOCK"]["expected_reason"] == "OBSERVED_CONTENT_EMPTY"


def test_optional_authority_absence_type_value_and_prefix_semantics() -> None:
    classify = gate.classify_admit_013_formal_evaluator_interface_design
    result = classify(
        download_result_status="success", observed_http_status=200,
        observed_content_length_bytes=10, observed_sha256=gate.SHA_A,
        expected_sha256=gate.SHA_A,
    )
    assert result.outcome == "passed"
    assert result.canonical_integrity_authority_record == (("expected_sha256", gate.SHA_A),)
    assert result.validated_integrity_authority_fields == ("expected_sha256",)
    assert result.consumed_integrity_authority_fields == gate.AUTHORITY_FIELDS
    invalid = classify(
        download_result_status="success", observed_http_status=200,
        observed_content_length_bytes=10, observed_sha256=gate.SHA_A,
        expected_content_length_bytes=10, expected_sha256=gate.SHA_A,
        explicit_integrity_verdict=None,
    )
    assert invalid.reason == gate.AUTHORITY_TYPE_REASONS[2]
    assert invalid.canonical_integrity_authority_record == (
        ("expected_content_length_bytes", 10), ("expected_sha256", gate.SHA_A),
    )
    assert invalid.validated_integrity_authority_fields == gate.AUTHORITY_FIELDS[:2]
    assert invalid.consumed_integrity_authority_fields == gate.AUTHORITY_FIELDS


def test_cross_phase_precedence_structure_before_business() -> None:
    truth = {row["case_id"]: row for row in rows(gate.TRUTH_FILE)}
    expected = {
        "PRESENCE_FIRST_MISSING_AUTHORITY_INVALID": "DOWNLOAD_RESULT_STATUS_MISSING",
        "CROSS_EXACT4_TYPE_AUTHORITY_INVALID": "DOWNLOAD_RESULT_STATUS_TYPE_INVALID",
        "CROSS_EXACT4_VALUE_AUTHORITY_INVALID": "DOWNLOAD_RESULT_STATUS_VALUE_INVALID",
        "CROSS_EXPECTED_LENGTH_INVALID_STATUS_FAILURE": "EXPECTED_CONTENT_LENGTH_BYTES_TYPE_INVALID",
        "CROSS_EXPECTED_SHA_INVALID_STATUS_FAILURE": "EXPECTED_SHA256_TYPE_INVALID",
        "CROSS_VERDICT_INVALID_STATUS_FAILURE": "EXPLICIT_INTEGRITY_VERDICT_TYPE_INVALID",
        "CROSS_AUTHORITY_INVALID_HTTP": "EXPECTED_SHA256_TYPE_INVALID",
        "CROSS_AUTHORITY_INVALID_ZERO": "EXPECTED_SHA256_TYPE_INVALID",
        "CROSS_MULTIPLE_AUTHORITY_INVALID_FIRST": "EXPECTED_CONTENT_LENGTH_BYTES_TYPE_INVALID",
        "CROSS_MULTIPLE_AUTHORITY_INVALID_SECOND": "EXPECTED_SHA256_TYPE_INVALID",
    }
    assert {case_id: truth[case_id]["expected_reason"] for case_id in expected} == expected


def test_business_precedence_strong_authority_and_zero_content() -> None:
    truth = {row["inherited_case_id"]: row for row in rows(gate.TRUTH_FILE) if row["inherited_case_id"]}
    assert truth["FAILURE_WITH_404"]["expected_reason"] == gate.BUSINESS_REASONS[0]
    assert truth["NON2XX_ZERO_INTEGRITY_FAILURE"]["expected_reason"] == gate.BUSINESS_REASONS[1]
    assert truth["ZERO_ALL_AUTHORITIES_APPEAR_PASS"]["expected_reason"] == gate.BUSINESS_REASONS[2]
    assert truth["SHA_MISMATCH_AND_EXPLICIT_VERIFIED"]["expected_reason"] == gate.BUSINESS_REASONS[3]
    assert truth["SHA_MATCH_AND_EXPLICIT_FAILED"]["expected_reason"] == gate.BUSINESS_REASONS[4]
    assert truth["LENGTH_MISMATCH_WITH_SHA_MATCH"]["expected_reason"] == gate.BUSINESS_REASONS[5]
    assert truth["ONLY_LENGTH_MATCH"]["expected_reason"] == gate.BUSINESS_REASONS[6]
    assert truth["PASS_SHA_MATCH"]["expected_reason"] == ""


def test_exact12_result_fields_types_reconstruction_and_invariants(manifest) -> None:
    assert tuple(manifest["result_fields"]) == gate.RESULT_FIELDS
    assert manifest["result_field_count"] == 12
    result = gate.classify_admit_013_formal_evaluator_interface_design(
        download_result_status="success", observed_http_status=200,
        observed_content_length_bytes=10, observed_sha256=gate.SHA_A,
        expected_sha256=gate.SHA_A,
    )
    assert gate.validate_admit_013_evaluation_result_contract_design(result) is True
    assert result.passed is (result.outcome == "passed")
    assert result.blocks_candidate is (result.outcome != "passed")
    assert (result.reason == "") is result.passed
    assert result.evaluator_io_used is False
    with pytest.raises(TypeError):
        gate.Admit013EvaluationResultContractDesign(
            result.admission_rule_id, result.outcome, 1, result.blocks_candidate,
            result.reason, result.canonical_download_result_record,
            result.canonical_integrity_authority_record,
            result.validated_download_result_fields,
            result.validated_integrity_authority_fields,
            result.consumed_download_result_fields,
            result.consumed_integrity_authority_fields, result.evaluator_io_used,
        )


def test_result_negative_exact26_and_sentinel_no_leak() -> None:
    negative = [row for row in rows(gate.TRUTH_FILE) if row["case_group"] == "result_invariant_negative"]
    assert [row["case_id"] for row in negative] == list(gate.NEGATIVE_RESULT_CASES)
    assert len(negative) == 26
    assert all(row["observed_design_result"].startswith("RESULT_CONTRACT_REJECTED:") for row in negative)
    artifact_text = "".join((ROOT / name).read_text() for name in gate.OUTPUT_FILES)
    assert "_DesignMissingValue" not in artifact_text
    assert "object at 0x" not in artifact_text


def test_routing_scalar_envelopes_no_admit012_dependency_and_no_io(manifest) -> None:
    routing = manifest["routing_contract"]
    assert routing["download_result_context"] == list(gate.DOWNLOAD_FIELDS)
    assert routing["evaluation_context"] == list(gate.AUTHORITY_FIELDS)
    assert routing["Admit012EvaluationResult_consumed"] is False
    assert routing["scalar_keyword_consumption_only"] is True
    assert routing["forbidden_envelopes"] == [
        "candidate_record", "batch_context", "stage_authorization_context",
        "fallback_envelope", "filesystem", "network", "raw",
        "provider_or_download_execution_inside_evaluator",
    ]
    assert manifest["safety"] == {
        "dataloader": False, "download": False, "model_or_checkpoint": False,
        "network": False, "provider": False, "raw": False, "runtime_change": False,
        "stage_commit_push": False, "training": False,
    }


def test_truth_matrix_exact128_groups_and_exact23_projection(manifest, snapshot) -> None:
    truth = rows(gate.TRUTH_FILE)
    assert len(truth) == 128 == manifest["row_counts"]["truth_matrix"]
    assert len({row["case_id"] for row in truth}) == 128
    assert all(row["case_passed"] == "true" for row in truth)
    assert manifest["truth_matrix_group_counts"] == checker.GROUP_COUNTS
    inherited = [row for row in truth if row["inherited_case_id"]]
    predecessor = gate._source_rows(
        snapshot, "covapie_admit_013_download_outcome_and_integrity_truth_matrix.csv"
    )
    assert len(inherited) == len(predecessor) == 23
    assert [row["inherited_case_id"] for row in inherited] == [row["case_id"] for row in predecessor]


def test_exact23_issue_identity_exact2_transitions_and_remaining_open(manifest, snapshot) -> None:
    actual = rows(gate.ISSUE_FILE)
    inherited = gate._source_rows(
        snapshot,
        "covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1/covapie_admit_013_issue_readiness_inventory.csv",
    )
    assert [row["issue_id"] for row in actual] == [row["issue_id"] for row in inherited]
    transitioned = [row for row in actual if row["successor_transition_action"] == gate.ISSUE_TRANSITION_ACTION]
    assert [row["issue_id"] for row in transitioned] == list(gate.ISSUE_TRANSITIONS)
    assert all(row["status"] == "open" and row["successor_effective_status"] == "resolved" for row in transitioned)
    by_id = {row["issue_id"]: row for row in actual}
    assert by_id["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] == "ADMIT_013|ADMIT_014|ADMIT_015"
    assert by_id["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["successor_effective_status"] == "open"
    assert by_id["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["successor_effective_status"] == "open"
    assert manifest["issue_transition_count"] == 2


def test_readiness_true_false_and_recommended_next_step(manifest) -> None:
    assert manifest["readiness"] == gate._readiness() == checker.readiness()
    assert all(manifest["readiness"][name] is True for name in gate.TRUE_READINESS)
    assert all(manifest["readiness"][name] is False for name in gate.FALSE_READINESS)
    assert manifest["recommended_next_step"] == "implement_covapie_admit_013_standalone_evaluator_interface_v1"
    assert manifest["step12d_status"] == "smoke_legality_only_not_final_training_feature_contract"
    assert "UNKNOWN_ATOM_FEATURE_POLICY" in manifest["feature_semantics_audit_requirement"]


def test_no_formal_evaluator_result_adapter_registry_or_exact13_runtime() -> None:
    source = Path(gate.__file__).read_text()
    tree = ast.parse(source)
    definitions = {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    assert "evaluate_admit_013" not in definitions
    assert "Admit013EvaluationResult" not in definitions
    assert "_evaluate_registered_admit_013" not in definitions
    assignments = {
        target.id for node in ast.walk(tree) if isinstance(node, ast.Assign)
        for target in node.targets if isinstance(target, ast.Name)
    }
    assert "EVALUATOR_REGISTRY" not in assignments
    runtime = REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013.py"
    assert not runtime.exists()


def test_deterministic_double_materialization_and_inode_noop(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    gate.materialize_contract(first)
    gate.materialize_contract(second)
    assert {p.name: p.read_bytes() for p in first.iterdir()} == {p.name: p.read_bytes() for p in second.iterdir()}
    before = {p.name: (p.stat().st_ino, p.read_bytes()) for p in first.iterdir()}
    gate.materialize_contract(first)
    assert before == {p.name: (p.stat().st_ino, p.read_bytes()) for p in first.iterdir()}


def test_materialization_mismatch_gpfs_einval_parent_fsync_and_residue(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "mismatch"
    gate.materialize_contract(target)
    (target / gate.CONTRACT_FILE).write_bytes(b"tampered")
    with pytest.raises(ValueError, match="mismatch"):
        gate.materialize_contract(target)

    calls: list[Path] = []
    original_fsync = gate._fsync_directory

    def record(path: Path) -> None:
        calls.append(path)
        original_fsync(path)

    with monkeypatch.context() as context:
        context.setattr(gate, "_fsync_directory", record)
        published = tmp_path / "published"
        gate.materialize_contract(published)
    assert calls[-1] == tmp_path and calls[0].name.endswith(".staging")

    with monkeypatch.context() as context:
        context.setattr(
            gate, "_rename_noreplace",
            lambda source, destination: (_ for _ in ()).throw(OSError(errno.EINVAL, "EINVAL")),
        )
        failed = tmp_path / "einval"
        with pytest.raises(OSError) as error:
            gate.materialize_contract(failed)
        assert error.value.errno == errno.EINVAL
        assert not failed.exists()
        assert not list(tmp_path.glob("*.staging"))


def test_source_output_race_symlink_root_fd_and_no_replace(
    tmp_path: Path,
    snapshot,
) -> None:
    with pytest.raises(ValueError, match="identity drift"):
        gate._pinned_read(snapshot[0].path, (0, 0, 0))
    root_link = tmp_path / "root-link"
    root_link.symlink_to(ROOT, target_is_directory=True)
    with pytest.raises(ValueError, match="unsafe output root"):
        gate._read_exact_output_set(root_link, gate.build_artifacts(snapshot))
    copied = copied_output(tmp_path / "leaf")
    leaf = copied / gate.CONTRACT_FILE
    leaf.unlink()
    leaf.symlink_to(gate.ROUTING_FILE)
    with pytest.raises(ValueError, match="unsafe output leaf"):
        gate._read_exact_output_set(copied, gate.build_artifacts(snapshot))
    tree = ast.parse(Path(gate.__file__).read_text())
    assert not any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name) and node.func.value.id == "os"
        and node.func.attr == "replace" for node in ast.walk(tree)
    )
    for path, reader in ((Path(gate.__file__), "_read_exact_output_set"), (CHECKER_PATH, "_read_outputs")):
        parsed = ast.parse(path.read_text())
        functions = {node.name: node for node in parsed.body if isinstance(node, ast.FunctionDef)}
        assert any(
            isinstance(node, ast.keyword) and node.arg == "dir_fd"
            for node in ast.walk(functions["_read_output_at"])
        )
        assert "O_DIRECTORY" in ast.unparse(functions[reader])


def test_checker_rejects_semantic_and_synchronized_tamper(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    checker_records,
) -> None:
    scenarios = (
        (checker.CONTRACT, "optional,future private _MISSING", "required,future private _MISSING"),
        (checker.CONTRACT, "DOWNLOAD_RESULT_STATUS_MISSING", "UNKNOWN"),
        (checker.CONTRACT, "admission_rule_id,exact str", "outcome,exact str"),
        (checker.ROUTING, "download_result_context,download_result_status", "candidate_record,download_result_status"),
        (checker.TRUTH, "CONTENT_ZERO_STRUCTURAL_BUSINESS_BLOCK", "CONTENT_ZERO_TAMPER"),
        (checker.TRUTH, "INTEGRITY_AUTHORITY_MISSING", ""),
        (checker.ISSUE, checker.TRANSITION_ACTION, "unchanged"),
        (checker.SOURCE, checker.SOURCE_BOUNDARY[0][1], "0" * 64),
    )
    for index, (name, needle, replacement) in enumerate(scenarios):
        root = copied_output(tmp_path / str(index))
        path = root / name
        text = path.read_text()
        assert needle in text
        path.write_text(text.replace(needle, replacement, 1))
        resync_manifest(root)
        reject(root, monkeypatch, checker_records)


def test_checker_rejects_manifest_missing_extra_reorder_and_self_attestation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    checker_records,
) -> None:
    canonical = json.loads((ROOT / checker.MANIFEST).read_text())
    assert list(canonical) == list(checker.MANIFEST_KEYS)
    assert list(canonical["readiness"]) == sorted(canonical["readiness"])
    assert list(canonical["safety"]) == sorted(canonical["safety"])
    for mode in ("missing", "extra", "reordered", "self"):
        root = copied_output(tmp_path / mode)
        path = root / checker.MANIFEST
        value = json.loads(path.read_text())
        if mode == "missing":
            value.pop("all_checks_passed")
        elif mode == "extra":
            value["unknown_key"] = True
        elif mode == "reordered":
            value = dict(reversed(list(value.items())))
        else:
            value["output_sha256"][checker.MANIFEST] = "0" * 64
        path.write_text(json.dumps(value, indent=2, sort_keys=mode != "reordered") + "\n")
        reject(root, monkeypatch, checker_records)


def test_checker_frozen_exact6_and_independent_source(checker_records, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(checker, "source_snapshot", lambda: checker_records)
    checker.validate(ROOT)
    assert {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in checker.FILES} == checker.FROZEN_SHA256
    checker_source = CHECKER_PATH.read_text()
    assert "from covalent_ext" not in checker_source
    assert "import covalent_ext" not in checker_source


def test_isolated_production_checker_and_test_imports_are_silent() -> None:
    targets = (Path(gate.__file__), CHECKER_PATH, Path(__file__))
    for index, target in enumerate(targets):
        code = (
            "import importlib.util,pathlib,sys;"
            f"p=pathlib.Path({str(target)!r});"
            f"s=importlib.util.spec_from_file_location('isolated_{index}',p);"
            "m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)"
        )
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(REPO_ROOT / "src")
        result = subprocess.run(
            [sys.executable, "-B", "-c", code], cwd=REPO_ROOT, env=environment,
            capture_output=True, text=True, check=False,
        )
        assert result.returncode == 0
        assert result.stdout == result.stderr == ""


def test_exact10_lifecycle_matches_current_state() -> None:
    tracked = set(git(REPO_ROOT, "ls-files", "--", *STAGE_PATHS).stdout.splitlines())
    expected = "post_commit" if tracked == set(STAGE_PATHS) else "pre_commit"
    assert validate_stage_inventory(REPO_ROOT, gate.BASE_COMMIT) == expected


def test_lifecycle_descendant_unrelated_state_and_postcommit(tmp_path: Path) -> None:
    repository, base_commit = seed_lifecycle_repository(tmp_path)
    assert validate_stage_inventory(repository, base_commit) == "pre_commit"
    ignored = repository / ".pytest_cache/v/cache/nodeids"
    ignored.parent.mkdir(parents=True)
    ignored.write_text("[]\n")
    unrelated = repository / "unrelated.txt"
    unrelated.write_text("unrelated\n")
    assert git(repository, "add", "--", "unrelated.txt").returncode == 0
    assert validate_stage_inventory(repository, base_commit) == "pre_commit"
    assert git(repository, "commit", "-q", "-m", "unrelated").returncode == 0
    assert validate_stage_inventory(repository, base_commit) == "pre_commit"
    assert git(repository, "add", "--", *STAGE_PATHS).returncode == 0
    assert git(repository, "commit", "-q", "-m", "stage").returncode == 0
    assert validate_stage_inventory(repository, base_commit) == "post_commit"


def test_lifecycle_fails_closed_mixed_staged_dirty_missing_ignored_extra(
    tmp_path: Path,
) -> None:
    for mode in ("mixed", "staged", "dirty", "missing", "ignored", "extra", "nonancestor"):
        repository, base_commit = seed_lifecycle_repository(tmp_path / mode)
        if mode == "mixed":
            assert git(repository, "add", "--", STAGE_PATHS[0]).returncode == 0
            assert git(repository, "commit", "-q", "-m", "partial").returncode == 0
        elif mode == "staged":
            assert git(repository, "add", "--", STAGE_PATHS[0]).returncode == 0
        elif mode == "dirty":
            assert git(repository, "add", "--", *STAGE_PATHS).returncode == 0
            assert git(repository, "commit", "-q", "-m", "stage").returncode == 0
            (repository / STAGE_PATHS[0]).write_text("dirty\n")
        elif mode == "missing":
            (repository / STAGE_PATHS[0]).unlink()
        elif mode == "ignored":
            with (repository / ".gitignore").open("a") as stream:
                stream.write(f"/{STAGE_PATHS[0]}\n")
            assert git(repository, "add", "--", ".gitignore").returncode == 0
            assert git(repository, "commit", "-q", "-m", "ignore").returncode == 0
        elif mode == "extra":
            (repository / gate.DEFAULT_OUTPUT_ROOT / "extra.csv").write_text("extra\n")
        else:
            base_commit = "0" * 40
        with pytest.raises(AssertionError):
            validate_stage_inventory(repository, base_commit)


def test_exact10_regular_size_suffix_and_protected_path_boundary() -> None:
    assert len(STAGE_PATHS) == len(set(STAGE_PATHS)) == 10
    for relative in STAGE_PATHS:
        path = REPO_ROOT / relative
        item = os.lstat(path)
        assert stat.S_ISREG(item.st_mode) and not stat.S_ISLNK(item.st_mode)
        assert item.st_size < 100 * 1024 * 1024
        assert path.suffix not in FORBIDDEN_SUFFIXES
        assert not relative.startswith(("data/raw/", "checkpoints/", "equivariant_diffusion/"))
    assert not any(path.name.endswith((".tmp", ".part")) for path in ROOT.parent.glob(f".{ROOT.name}.*"))
