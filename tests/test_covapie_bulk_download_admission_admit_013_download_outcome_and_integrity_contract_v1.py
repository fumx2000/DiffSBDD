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
import stat
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_design_gate
    as gate,
)

CHECKER_PATH = REPO_ROOT / "scripts/check_covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1.py"
SPEC = importlib.util.spec_from_file_location("admit013_outcome_checker", CHECKER_PATH)
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
ROOT = REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT
STAGE_PATHS = (
    "src/covalent_ext/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_design_gate.py",
    "scripts/check_covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1.py",
    "tests/test_covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1.py",
    "docs/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1_summary.md",
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


def validate_stage_inventory(
    repository: Path, base_commit: str, stage_paths: tuple[str, ...] = STAGE_PATHS
) -> str:
    expected = set(stage_paths)
    assert len(expected) == 10
    assert git(
        repository, "merge-base", "--is-ancestor", base_commit, "HEAD"
    ).returncode == 0
    output_root = repository / gate.DEFAULT_OUTPUT_ROOT
    assert output_root.is_dir() and not output_root.is_symlink()
    assert {
        path.relative_to(repository).as_posix()
        for path in output_root.iterdir()
    } == {
        (gate.DEFAULT_OUTPUT_ROOT / name).as_posix() for name in gate.OUTPUT_FILES
    }
    observed_stage_paths = {
        path.relative_to(repository).as_posix()
        for directory in ("src/covalent_ext", "scripts", "tests", "docs")
        for path in (repository / directory).glob(
            "*admit_013_download_outcome_and_integrity_contract*"
        )
    } | {
        path.relative_to(repository).as_posix() for path in output_root.iterdir()
    }
    assert observed_stage_paths == expected
    for relative in stage_paths:
        path = repository / relative
        item = os.lstat(path)
        assert stat.S_ISREG(item.st_mode) and not stat.S_ISLNK(item.st_mode)
        assert path.stat().st_size < 100 * 1024 * 1024
        assert path.suffix not in FORBIDDEN_SUFFIXES
    assert git(
        repository, "diff", "--cached", "--quiet", "--", *stage_paths
    ).returncode == 0
    tracked = set(
        git(repository, "ls-files", "--", *stage_paths).stdout.splitlines()
    )
    untracked = set(
        git(
            repository, "ls-files", "--others", "--exclude-standard", "--",
            *stage_paths,
        ).stdout.splitlines()
    )
    if tracked == set() and untracked == expected:
        return "pre_commit"
    if tracked == expected and untracked == set():
        assert git(
            repository, "diff", "--quiet", "--", *stage_paths
        ).returncode == 0
        return "post_commit"
    raise AssertionError("unresolved or mixed stage lifecycle")


def seed_lifecycle_repository(tmp_path: Path) -> tuple[Path, str]:
    repository = tmp_path / "repo"
    repository.mkdir(parents=True)
    assert git(repository, "init", "-q").returncode == 0
    assert git(repository, "config", "user.name", "CovaPIE Test").returncode == 0
    assert git(repository, "config", "user.email", "covapie-test@example.invalid").returncode == 0
    (repository / ".gitignore").write_text(
        "**/__pycache__/\n*.pyc\n.pytest_cache/\n"
    )
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


def rows(name: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO((ROOT / name).read_text(), newline="")))


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


def reject(root: Path, monkeypatch: pytest.MonkeyPatch, records) -> None:
    monkeypatch.setattr(checker, "source_snapshot", lambda: records)
    with pytest.raises(AssertionError):
        checker.validate(root, enforce_frozen_hashes=False)


def test_base_commit_identity_and_ancestry(snapshot) -> None:
    assert gate.BASE_COMMIT == "30c644de3973ba2968ecaa8ebff97159c07678b9"
    assert gate.BASE_PARENT == "5ff12d358a633c44c333022f7e0ebe30f039d6fc"
    assert gate.BASE_SUBJECT == "add CovaPIE ADMIT_013 formal evaluator preconditions audit v1"
    assert len(snapshot) == 22
    result = subprocess.run(
        ["git", "show", "-s", "--format=%H%n%P%n%s", gate.BASE_COMMIT],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    )
    assert result.stdout.splitlines() == [gate.BASE_COMMIT, gate.BASE_PARENT, gate.BASE_SUBJECT]
    assert git(REPO_ROOT, "merge-base", "--is-ancestor", gate.BASE_COMMIT, "HEAD").returncode == 0
    gate._assert_base_lineage()
    checker._assert_base_lineage()


def test_lineage_rejects_nonancestor_and_never_requires_exact_head(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for module, error in ((gate, ValueError), (checker, AssertionError)):
        original = module._git

        def nonancestor(arguments, *, text=True, _original=original):
            if arguments[:2] == ["merge-base", "--is-ancestor"]:
                return subprocess.CompletedProcess(
                    ["git", *arguments], 1, "", "simulated non-ancestor"
                )
            return _original(arguments, text=text)

        with monkeypatch.context() as context:
            context.setattr(module, "_git", nonancestor)
            with pytest.raises(error):
                module._assert_base_lineage()

    for path in (
        REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_design_gate.py",
        CHECKER_PATH,
    ):
        source = path.read_text()
        assert '["rev-parse", "HEAD"]' not in source
        assert "merge-base" in source and "--is-ancestor" in source


def test_exact_source_boundary_and_triple_sha(snapshot) -> None:
    assert [record[0] for record in snapshot] == list(gate.SOURCE_PATHS)
    assert [(record[0].as_posix(), record[2]) for record in snapshot] == list(checker.SOURCE_BOUNDARY)
    assert gate.SOURCE_PATH_LIST_SHA256 == checker.PATH_SHA
    assert gate.SOURCE_PATH_SHA256_PAIRS_SHA256 == checker.PAIR_SHA
    assert all(record[3] in {"100644", "100755"} for record in snapshot)
    assert not any(path.parts[:2] == ("data", "raw") or path.parts[0] == "checkpoints" for path in gate.SOURCE_PATHS)


def test_canonical_rule_identity(manifest) -> None:
    assert {
        key: manifest[key] for key in (
            "admission_rule_id", "admission_rule_name", "evidence_source",
            "required_status", "blocking_reason", "evaluation_phase",
        )
    } == {
        "admission_rule_id": "ADMIT_013",
        "admission_rule_name": "download_failure_fail_closed",
        "evidence_source": "future_download_result",
        "required_status": "non_success_or_integrity_failure_not_admitted",
        "blocking_reason": "download_failure_must_fail_closed",
        "evaluation_phase": "post_download",
    }


def test_exact4_order_and_structural_contract_not_drifted(snapshot, manifest) -> None:
    assert tuple(manifest["exact4_fields"]) == gate.EXACT4_FIELDS == checker.FIELDS
    exact4 = gate._rows(
        snapshot,
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_integrity_field_contract.csv",
    )
    assert [row["field_name"] for row in exact4] == list(gate.EXACT4_FIELDS)
    assert [row["exact_builtin_type"] for row in exact4] == ["str", "int", "int", "str"]
    assert all(row["subclasses_allowed"] == row["normalization_allowed"] == "false" for row in exact4)


def test_admit012_dependency_boundary_is_three_distinct_concepts(manifest) -> None:
    boundary = manifest["admit_012_dependency_boundary"]
    assert boundary == {
        "Admit012EvaluationResult_consumed": False,
        "direct_cross_rule_result_consumption_allowed": False,
        "pipeline_level_prerequisite_allowed": True,
        "standalone_evaluator_self_validation_required": True,
    }
    policy = {row["policy_id"]: row for row in rows(gate.OUTCOME_FILE)}
    assert policy["DEPENDENCY_PIPELINE"]["disposition"] == "logical_prerequisite_only"
    assert policy["DEPENDENCY_SELF_VALIDATION"]["disposition"] == "required"
    assert policy["DEPENDENCY_NO_RESULT_OBJECT"]["disposition"] == "forbidden"


def test_routing_is_exact_and_forbidden_envelopes_are_closed(manifest) -> None:
    route = manifest["routing_contract"]
    assert route["download_result_context"] == list(gate.EXACT4_FIELDS)
    assert route["evaluation_context"] == list(gate.AUTHORITY_FIELDS)
    assert route["forbidden_envelopes"] == [
        "candidate_record", "batch_context", "stage_authorization_context", "fallback_envelope",
    ]
    assert route["normalization_inference_file_network_recompute_allowed"] is False


def test_http_200_through_299_is_continue_not_automatic_pass(manifest) -> None:
    assert manifest["http_success_range"] == [200, 299]
    policy = {row["policy_id"]: row for row in rows(gate.OUTCOME_FILE)}
    assert policy["HTTP_SUCCESS_RANGE"]["contract"] == "inclusive success range 200..299"
    assert policy["STATUS_SUCCESS_2XX"]["disposition"] == "continue_only"
    assert policy["STATUS_SUCCESS_NON2XX"]["disposition"] == "blocked"


def test_failure_status_always_blocks_and_precedes_http() -> None:
    truth = {row["case_id"]: row for row in rows(gate.TRUTH_FILE)}
    for case_id in ("FAILURE_WITH_2XX", "FAILURE_WITH_404", "STATUS_FAILURE_AND_SHA_MISMATCH"):
        assert truth[case_id]["expected_outcome"] == "blocked"
        assert truth[case_id]["expected_reason"] == "DOWNLOAD_RESULT_STATUS_FAILURE"
        assert truth[case_id]["expected_precedence_rank"] == "1"
    assert truth["SUCCESS_WITH_404"]["expected_reason"] == "OBSERVED_HTTP_STATUS_NOT_SUCCESS"


def test_zero_content_is_always_blocked_after_structural_validation(manifest) -> None:
    assert manifest["zero_content_length_structurally_allowed"] is True
    assert manifest["zero_content_length_admitted"] is False
    truth = {row["case_id"]: row for row in rows(gate.TRUTH_FILE)}
    for case_id in ("ZERO_CONTENT", "ZERO_ALL_AUTHORITIES_APPEAR_PASS"):
        assert truth[case_id]["expected_reason"] == "OBSERVED_CONTENT_EMPTY"
        assert truth[case_id]["expected_outcome"] == "blocked"


def test_sha_grammar_is_not_a_match_or_integrity_verdict() -> None:
    truth = {row["case_id"]: row for row in rows(gate.TRUTH_FILE)}
    row = truth["NO_STRONG_AUTHORITY"]
    assert len(row["observed_sha256"]) == 64
    assert set(row["observed_sha256"]) <= set("0123456789abcdef")
    assert row["expected_reason"] == "INTEGRITY_AUTHORITY_MISSING"


def test_expected_sha_match_mismatch_and_explicit_verdicts() -> None:
    truth = {row["case_id"]: row for row in rows(gate.TRUTH_FILE)}
    assert truth["PASS_SHA_MATCH"]["expected_outcome"] == "passed"
    assert truth["SHA_MISMATCH"]["expected_reason"] == "OBSERVED_SHA256_MISMATCH"
    assert truth["PASS_EXPLICIT_VERIFIED"]["expected_outcome"] == "passed"
    assert truth["EXPLICIT_FAILED"]["expected_reason"] == "EXPLICIT_INTEGRITY_VERDICT_FAILED"
    assert truth["SHA_MATCH_AND_EXPLICIT_FAILED"]["expected_reason"] == "EXPLICIT_INTEGRITY_VERDICT_FAILED"
    assert truth["SHA_MISMATCH_AND_EXPLICIT_VERIFIED"]["expected_reason"] == "OBSERVED_SHA256_MISMATCH"


def test_expected_length_match_is_only_corroborating_and_mismatch_blocks() -> None:
    truth = {row["case_id"]: row for row in rows(gate.TRUTH_FILE)}
    assert truth["PASS_ALL_AUTHORITIES"]["expected_content_length_bytes"] == truth["PASS_ALL_AUTHORITIES"]["observed_content_length_bytes"]
    assert truth["LENGTH_MISMATCH_WITH_SHA_MATCH"]["expected_reason"] == "OBSERVED_CONTENT_LENGTH_MISMATCH"
    assert truth["ONLY_LENGTH_MATCH"]["expected_reason"] == "INTEGRITY_AUTHORITY_MISSING"


def test_integrity_authority_exact_types_sources_and_forbidden_pseudo_authority() -> None:
    authority = rows(gate.AUTHORITY_FILE)
    assert [row["authority_name"] for row in authority] == list(gate.AUTHORITY_FIELDS)
    assert [row["exact_builtin_type"] for row in authority] == ["int", "str", "str"]
    assert all(row["presence_required"] == "false" for row in authority)
    assert all(row["subclasses_allowed"] == row["normalization_allowed"] == "false" for row in authority)
    assert authority[0]["minimum_value"] == "0"
    assert authority[1]["allowed_values_or_grammar"] == "ASCII lowercase [0-9a-f]{64}"
    assert authority[2]["allowed_values_or_grammar"] == "verified|failed"
    assert all(row["forbidden_pseudo_authorities"].split("|") == list(gate.FORBIDDEN_PSEUDO_AUTHORITIES) for row in authority)
    assert all(row["source_envelope"] == "evaluation_context" and row["evaluator_io_allowed"] == "false" for row in authority)


def test_closed_reason_vocabulary_and_exact_precedence(manifest) -> None:
    failure = rows(gate.FAILURE_FILE)
    assert manifest["reason_vocabulary"] == list(gate.REASON_VOCABULARY)
    assert [row["reason"] for row in failure] == list(gate.REASON_VOCABULARY[1:]) + [""]
    assert [row["precedence_rank"] for row in failure] == [str(value) for value in range(1, 9)]
    assert all(row["catch_all_allowed"] == "false" for row in failure)
    assert all(row["requires_structural_validation"] == "true" for row in failure)
    assert not {"UNKNOWN", "OTHER"} & set(manifest["reason_vocabulary"])


def test_truth_matrix_covers_required_cases_and_all_adjacent_conflicts(manifest) -> None:
    truth = rows(gate.TRUTH_FILE)
    assert len(truth) == manifest["row_counts"]["truth_matrix"] == 23
    assert len({row["case_id"] for row in truth}) == 23
    adjacent = [row for row in truth if row["case_group"] == "adjacent_precedence"]
    assert len(adjacent) == 6
    for rank, row in enumerate(adjacent, 1):
        active = row["active_failure_reasons"].split("|")
        assert gate.BUSINESS_FAILURE_REASONS[rank - 1] in active
        assert gate.BUSINESS_FAILURE_REASONS[rank] in active
        assert row["expected_precedence_rank"] == str(rank)
    triple = next(row for row in truth if row["case_id"] == "NON2XX_ZERO_INTEGRITY_FAILURE")
    assert len(triple["active_failure_reasons"].split("|")) >= 3
    assert all(row["case_passed"] == "true" for row in truth)


def test_issue_inventory_preserves_exact23_and_records_exact5_transitions(snapshot, manifest) -> None:
    inherited = gate._rows(
        snapshot,
        "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_preconditions_audit_v1/covapie_admit_013_issue_readiness_inventory.csv",
    )
    actual = rows(gate.ISSUE_FILE)
    assert len(actual) == len(inherited) == 23
    assert [row["issue_id"] for row in actual] == [row["issue_id"] for row in inherited]
    assert [row["inherited_order"] for row in actual] == [str(value) for value in range(1, 24)]
    transitioned = [row for row in actual if row["transition_action"] == "resolved_by_successor_contract_design"]
    assert [row["issue_id"] for row in transitioned] == list(gate.RESOLVED_TRANSITIONS)
    assert all(row["status"] == "open" and row["effective_status"] == "resolved" for row in transitioned)
    assert manifest["issue_transition_counts"]["resolved_by_this_stage"] == 5


def test_signature_result_coverage_and_aggregation_issues_remain_open() -> None:
    issues = {row["issue_id"]: row for row in rows(gate.ISSUE_FILE)}
    for issue_id in ("ADMIT_013_STANDALONE_SIGNATURE_UNRESOLVED", "ADMIT_013_RESULT_CONTRACT_UNRESOLVED"):
        assert issues[issue_id]["effective_status"] == "open"
    coverage = issues["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]
    assert coverage["affected_rules"] == "ADMIT_013|ADMIT_014|ADMIT_015"
    assert coverage["effective_status"] == "open"
    assert issues["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["effective_status"] == "open"


def test_exact32_transitions_and_readiness_are_fail_closed(manifest) -> None:
    assert manifest["resolved_precondition_ids"] == [
        "PRE_013", "PRE_014", "PRE_015", "PRE_016", "PRE_018", "PRE_019",
        "PRE_020", "PRE_021", "PRE_022", "PRE_023", "PRE_024", "PRE_026",
        "PRE_027", "PRE_028",
    ]
    assert manifest["remaining_open_precondition_ids"] == ["PRE_029", "PRE_030"]
    assert manifest["readiness"] == gate._readiness() == checker.readiness()
    assert manifest["recommended_next_step"] == "design_covapie_admit_013_formal_evaluator_interface_contract_v1"
    assert manifest["readiness"]["ready_for_training"] is False
    assert manifest["readiness"]["ready_for_bulk_download_now"] is False
    assert manifest["readiness"]["provider_mapping_validated"] is False
    assert manifest["readiness"]["feature_semantics_audit_required_before_training"] is True


def test_no_evaluator_result_adapter_registry_or_runtime_symbols() -> None:
    source = (REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_design_gate.py").read_text()
    tree = ast.parse(source)
    definitions = {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    assert "evaluate_admit_013" not in definitions
    assert "Admit013EvaluationResult" not in definitions
    assert "_evaluate_registered_admit_013" not in definitions
    assignments = {
        target.id for node in ast.walk(tree) if isinstance(node, ast.Assign)
        for target in node.targets if isinstance(target, ast.Name)
    }
    assert not {"EVALUATOR_REGISTRY", "RULE_NAMES", "ADAPTER_IDS"} & assignments


def test_no_provider_network_download_raw_model_or_training_execution(manifest) -> None:
    assert manifest["safety"] == {
        "provider": False, "network": False, "download": False, "raw": False,
        "model_or_checkpoint": False, "dataloader": False, "runtime_change": False,
        "training": False, "stage_commit_push": False,
    }
    assert all(row["evaluator_io_allowed"] == "false" for row in rows(gate.AUTHORITY_FILE))
    assert not any(path.parts[:2] == ("data", "raw") for path in gate.SOURCE_PATHS)


def test_deterministic_double_materialization_and_inode_noop(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    gate.materialize_contract(first)
    gate.materialize_contract(second)
    first_bytes = {path.name: path.read_bytes() for path in first.iterdir()}
    assert first_bytes == {path.name: path.read_bytes() for path in second.iterdir()}
    before = {path.name: (path.stat().st_ino, path.read_bytes()) for path in first.iterdir()}
    gate.materialize_contract(first)
    assert before == {path.name: (path.stat().st_ino, path.read_bytes()) for path in first.iterdir()}


def test_successful_publish_fsyncs_parent_before_postverify(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "published"
    calls: list[Path] = []
    original = gate._fsync_directory

    def recording_fsync(path: Path) -> None:
        calls.append(path)
        original(path)

    monkeypatch.setattr(gate, "_fsync_directory", recording_fsync)
    gate.materialize_contract(target)
    assert calls == [tmp_path]
    assert {path.name for path in target.iterdir()} == set(gate.OUTPUT_FILES)


def test_exact_set_noop_does_not_fsync_parent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "existing"
    gate.materialize_contract(target)
    before = {path.name: path.stat().st_ino for path in target.iterdir()}
    monkeypatch.setattr(
        gate, "_fsync_directory",
        lambda path: (_ for _ in ()).throw(AssertionError("no-op must not fsync")),
    )
    gate.materialize_contract(target)
    assert before == {path.name: path.stat().st_ino for path in target.iterdir()}


def test_existing_mismatch_fails_closed(tmp_path: Path) -> None:
    target = tmp_path / "target"
    gate.materialize_contract(target)
    (target / gate.OUTCOME_FILE).write_bytes(b"tampered")
    with pytest.raises(ValueError, match="mismatch"):
        gate.materialize_contract(target)


def test_gpfs_einval_fails_closed_without_replace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fsync_calls: list[Path] = []
    monkeypatch.setattr(
        gate, "_rename_noreplace",
        lambda source, destination: (_ for _ in ()).throw(OSError(errno.EINVAL, "EINVAL")),
    )
    monkeypatch.setattr(gate, "_fsync_directory", fsync_calls.append)
    target = tmp_path / "target"
    with pytest.raises(OSError) as error:
        gate.materialize_contract(target)
    assert error.value.errno == errno.EINVAL
    assert not target.exists() and not list(tmp_path.glob("*.staging"))
    assert fsync_calls == []
    tree = ast.parse((REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_design_gate.py").read_text())
    assert not [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name) and node.func.value.id == "os"
        and node.func.attr == "replace"
    ]


def test_parent_directory_fsync_failure_is_not_swallowed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "target"

    def fail_fsync(path: Path) -> None:
        assert path == tmp_path
        raise OSError(errno.EIO, "simulated parent fsync failure")

    monkeypatch.setattr(gate, "_fsync_directory", fail_fsync)
    with pytest.raises(OSError) as error:
        gate.materialize_contract(target)
    assert error.value.errno == errno.EIO
    assert target.is_dir()
    assert not list(tmp_path.glob("*.staging"))


def test_source_identity_race_fails_closed(snapshot) -> None:
    with pytest.raises(ValueError, match="identity drift"):
        gate._pinned_read(snapshot[0][0], (0, 0, 0))


def test_output_root_and_leaf_symlinks_are_rejected(
    tmp_path: Path,
) -> None:
    root_link = tmp_path / "root-link"
    root_link.symlink_to(ROOT, target_is_directory=True)
    with pytest.raises(ValueError, match="unsafe output root"):
        gate._read_exact_output_set(root_link, gate.build_artifacts())
    with pytest.raises(AssertionError):
        checker._read_outputs(root_link)

    production_root = copied_output(tmp_path / "production")
    checker_root = copied_output(tmp_path / "checker")
    for root in (production_root, checker_root):
        leaf = root / gate.OUTCOME_FILE
        leaf.unlink()
        leaf.symlink_to(gate.AUTHORITY_FILE)
    with pytest.raises(ValueError, match="unsafe output leaf"):
        gate._read_exact_output_set(production_root, gate.build_artifacts())
    with pytest.raises(AssertionError):
        checker._read_outputs(checker_root)


def test_output_leaf_identity_drift_is_rejected_via_root_fd(tmp_path: Path) -> None:
    root = copied_output(tmp_path)
    root_fd = os.open(root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        with pytest.raises(ValueError, match="identity drift"):
            gate._read_output_at(root_fd, gate.OUTCOME_FILE, (0, 0, 0))
        with pytest.raises(AssertionError):
            checker._read_output_at(root_fd, checker.OUTCOME, (0, 0, 0))
    finally:
        os.close(root_fd)


def test_production_and_checker_open_leaves_relative_to_pinned_root_fd() -> None:
    for path, reader_name in (
        (
            REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_design_gate.py",
            "_read_exact_output_set",
        ),
        (CHECKER_PATH, "_read_outputs"),
    ):
        tree = ast.parse(path.read_text())
        functions = {
            node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
        }
        leaf_reader = functions["_read_output_at"]
        leaf_opens = [
            node for node in ast.walk(leaf_reader)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "os" and node.func.attr == "open"
        ]
        assert len(leaf_opens) == 1
        assert isinstance(leaf_opens[0].args[0], ast.Name)
        assert leaf_opens[0].args[0].id == "name"
        assert any(
            keyword.arg == "dir_fd"
            and isinstance(keyword.value, ast.Name)
            and keyword.value.id == "root_fd"
            for keyword in leaf_opens[0].keywords
        )
        root_reader = functions[reader_name]
        assert any(
            (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "os" and node.attr == "O_DIRECTORY"
            )
            or (isinstance(node, ast.Constant) and node.value == "O_DIRECTORY")
            for node in ast.walk(root_reader)
        )


def test_checker_semantic_tamper_unknown_reason_duplicate_and_authority_weakening(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, checker_records
) -> None:
    scenarios = (
        (checker.OUTCOME, "inclusive success range 200..299", "inclusive success range 200..300"),
        (checker.AUTHORITY, "int,false,,0,false", "int,true,,0,false"),
        (checker.FAILURE, "OBSERVED_CONTENT_EMPTY", "UNKNOWN"),
        (checker.TRUTH, "PASS_SHA_MATCH", "PASS_ALL_AUTHORITIES"),
        (checker.ISSUE, "resolved_by_successor_contract_design", "unchanged"),
    )
    for index, (name, needle, replacement) in enumerate(scenarios):
        root = copied_output(tmp_path / str(index))
        path = root / name
        text = path.read_text()
        assert needle in text
        path.write_text(text.replace(needle, replacement, 1))
        resync_manifest(root)
        reject(root, monkeypatch, checker_records)


def test_checker_rejects_header_reorder_and_precedence_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, checker_records
) -> None:
    root = copied_output(tmp_path)
    path = root / checker.FAILURE
    lines = path.read_text().splitlines()
    header = lines[0].split(",")
    header[0], header[1] = header[1], header[0]
    lines[0] = ",".join(header)
    lines[1], lines[2] = lines[2], lines[1]
    path.write_text("\n".join(lines) + "\n")
    resync_manifest(root)
    reject(root, monkeypatch, checker_records)


def test_manifest_exact_keys_nested_keys_and_missing_extra_reordered_rejection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, checker_records
) -> None:
    canonical = json.loads((ROOT / checker.MANIFEST).read_text())
    expected_manifest = json.loads(checker.expected(checker_records)[checker.MANIFEST])
    assert list(canonical) == list(expected_manifest)
    assert list(canonical["readiness"]) == list(expected_manifest["readiness"])
    assert list(canonical["safety"]) == list(expected_manifest["safety"])

    for index, mode in enumerate(("missing", "extra", "reordered")):
        root = copied_output(tmp_path / mode)
        path = root / checker.MANIFEST
        value = json.loads(path.read_text())
        if mode == "missing":
            value.pop("all_checks_passed")
            path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        elif mode == "extra":
            value["unknown_key"] = True
            path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        else:
            reversed_value = dict(reversed(list(value.items())))
            path.write_text(json.dumps(reversed_value, indent=2, sort_keys=False) + "\n")
        reject(root, monkeypatch, checker_records)


def test_checker_source_lineage_precedes_output_read(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def output_bomb(root):
        nonlocal called
        called = True
        raise AssertionError("outputs must not be read")

    original_git = checker._git

    def nonancestor(arguments, *, text=True):
        if arguments[:2] == ["merge-base", "--is-ancestor"]:
            return subprocess.CompletedProcess(
                ["git", *arguments], 1, "", "simulated non-ancestor"
            )
        return original_git(arguments, text=text)

    monkeypatch.setattr(checker, "_git", nonancestor)
    monkeypatch.setattr(checker, "_read_outputs", output_bomb)
    with pytest.raises(AssertionError):
        checker.validate(ROOT)
    assert called is False


def test_checker_validates_frozen_sha_and_exact_output_set(checker_records, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(checker, "source_snapshot", lambda: checker_records)
    checker.validate(ROOT)
    assert {path.name for path in ROOT.iterdir()} == set(checker.FILES)
    assert all(path.is_file() and not path.is_symlink() for path in ROOT.iterdir())
    assert {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in checker.FILES} == checker.FROZEN_SHA256


def test_isolated_production_checker_and_test_imports_are_silent() -> None:
    targets = (
        REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_design_gate.py",
        CHECKER_PATH,
        Path(__file__),
    )
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


def test_exact_stage_inventory_matches_current_tracked_state() -> None:
    tracked = set(
        git(REPO_ROOT, "ls-files", "--", *STAGE_PATHS).stdout.splitlines()
    )
    expected = "post_commit" if tracked == set(STAGE_PATHS) else "pre_commit"
    assert validate_stage_inventory(REPO_ROOT, gate.BASE_COMMIT) == expected


def test_stage_inventory_supports_clean_committed_descendant_and_ignores_unrelated_files(
    tmp_path: Path,
) -> None:
    repository, base_commit = seed_lifecycle_repository(tmp_path)
    assert validate_stage_inventory(repository, base_commit) == "pre_commit"

    ignored = repository / ".pytest_cache/v/cache/nodeids"
    ignored.parent.mkdir(parents=True)
    ignored.write_text("[]\n")
    pyc = repository / "scripts/__pycache__/stage.cpython-310.pyc"
    pyc.parent.mkdir(parents=True)
    pyc.write_bytes(b"cache")
    assert validate_stage_inventory(repository, base_commit) == "pre_commit"

    unrelated = repository / "unrelated-fix.txt"
    unrelated.write_text("unrelated committed fix\n")
    assert git(repository, "add", "--", "unrelated-fix.txt").returncode == 0
    assert validate_stage_inventory(repository, base_commit) == "pre_commit"
    assert git(repository, "commit", "-q", "-m", "unrelated fix").returncode == 0
    assert git(repository, "rev-parse", "HEAD").stdout.strip() != base_commit
    assert validate_stage_inventory(repository, base_commit) == "pre_commit"

    assert git(repository, "add", "--", *STAGE_PATHS).returncode == 0
    assert git(repository, "commit", "-q", "-m", "stage candidate").returncode == 0
    (repository / "future-unrelated-stage.txt").write_text("unrelated\n")
    assert validate_stage_inventory(repository, base_commit) == "post_commit"
    assert git(
        repository, "add", "--", "future-unrelated-stage.txt"
    ).returncode == 0
    assert validate_stage_inventory(repository, base_commit) == "post_commit"


def test_stage_inventory_checks_ancestry_before_inventory(tmp_path: Path) -> None:
    repository, _ = seed_lifecycle_repository(tmp_path)
    shutil.rmtree(repository / gate.DEFAULT_OUTPUT_ROOT)
    with pytest.raises(AssertionError):
        validate_stage_inventory(repository, "0" * 40)


def test_stage_inventory_rejects_mixed_lifecycle(tmp_path: Path) -> None:
    repository, base_commit = seed_lifecycle_repository(tmp_path)
    assert git(repository, "add", "--", STAGE_PATHS[0]).returncode == 0
    assert git(repository, "commit", "-q", "-m", "partial stage").returncode == 0
    with pytest.raises(AssertionError):
        validate_stage_inventory(repository, base_commit)


def test_stage_inventory_rejects_staged_stage_path(tmp_path: Path) -> None:
    repository, base_commit = seed_lifecycle_repository(tmp_path)
    assert git(repository, "add", "--", STAGE_PATHS[0]).returncode == 0
    with pytest.raises(AssertionError):
        validate_stage_inventory(repository, base_commit)


def test_stage_inventory_rejects_postcommit_working_modification(
    tmp_path: Path,
) -> None:
    repository, base_commit = seed_lifecycle_repository(tmp_path)
    assert git(repository, "add", "--", *STAGE_PATHS).returncode == 0
    assert git(repository, "commit", "-q", "-m", "stage candidate").returncode == 0
    (repository / STAGE_PATHS[0]).write_text("modified stage path\n")
    with pytest.raises(AssertionError):
        validate_stage_inventory(repository, base_commit)


def test_stage_inventory_rejects_extra_output(tmp_path: Path) -> None:
    repository, base_commit = seed_lifecycle_repository(tmp_path)
    output_root = repository / gate.DEFAULT_OUTPUT_ROOT
    (output_root / "unexpected.csv").write_text("unexpected\n")
    with pytest.raises(AssertionError):
        validate_stage_inventory(repository, base_commit)


def test_stage_inventory_rejects_missing_or_ignored_stage_path(tmp_path: Path) -> None:
    missing_repository, missing_base = seed_lifecycle_repository(tmp_path / "missing")
    (missing_repository / STAGE_PATHS[0]).unlink()
    with pytest.raises(AssertionError):
        validate_stage_inventory(missing_repository, missing_base)

    ignored_repository, ignored_base = seed_lifecycle_repository(tmp_path / "ignored")
    with (ignored_repository / ".gitignore").open("a") as stream:
        stream.write(f"/{STAGE_PATHS[0]}\n")
    assert git(ignored_repository, "add", "--", ".gitignore").returncode == 0
    assert git(ignored_repository, "commit", "-q", "-m", "ignore one stage path").returncode == 0
    with pytest.raises(AssertionError, match="unresolved or mixed"):
        validate_stage_inventory(ignored_repository, ignored_base)
