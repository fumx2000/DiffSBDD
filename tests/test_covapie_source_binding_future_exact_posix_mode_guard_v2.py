from __future__ import annotations

import ast
from collections import Counter
import hashlib
import importlib.util
import inspect
from pathlib import Path
import subprocess

import pytest

from covalent_ext import (
    covapie_source_binding_future_exact_posix_mode_guard_v2 as subject,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    ROOT
    / "scripts/check_covapie_source_binding_future_exact_posix_mode_guard_v2.py"
)
BASELINE = "54f98c41e2dc34d816a17242292ee2379e99783e"


def _load_checker():
    spec = importlib.util.spec_from_file_location("b4_future_guard_checker", CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def checker():
    return _load_checker()


@pytest.fixture(scope="session")
def result() -> dict[str, object]:
    return subject.verify_covapie_source_binding_future_exact_posix_mode_guard_v2(
        repo_root=ROOT
    )


def _python_classes(snippet: str, label: str = "control") -> set[str]:
    rows = subject._classify_python_text_v2(
        snippet,
        source_path=f"src/covalent_ext/synthetic_{label}.py",
        test_only=False,
    )
    return {str(row["semantic_class"]) for row in rows}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_strict_exact4_paths(checker) -> None:
    assert checker.EXACT4_PATHS == (
        "src/covalent_ext/covapie_source_binding_future_exact_posix_mode_guard_v2.py",
        "scripts/check_covapie_source_binding_future_exact_posix_mode_guard_v2.py",
        "tests/test_covapie_source_binding_future_exact_posix_mode_guard_v2.py",
        "docs/covapie_source_binding_future_exact_posix_mode_guard_v2_guide.md",
    )


def test_public_api_is_exact_and_keyword_only() -> None:
    assert subject.__all__ == (
        "SourceBindingFutureExactPosixModeGuardV2Error",
        "verify_covapie_source_binding_future_exact_posix_mode_guard_v2",
    )
    signature = inspect.signature(
        subject.verify_covapie_source_binding_future_exact_posix_mode_guard_v2
    )
    assert tuple(signature.parameters) == ("repo_root",)
    assert (
        signature.parameters["repo_root"].kind
        is inspect.Parameter.KEYWORD_ONLY
    )


def test_candidate_lifecycle_is_exact(checker) -> None:
    expected = set(checker.EXACT4_PATHS)
    assert (
        checker.classify_lifecycle_from_facts(
            tracked_exact4=set(),
            ordinary_untracked=expected,
            status_entries=tuple(f"?? {path}" for path in sorted(expected)),
            working_diff=set(),
            cached_diff=set(),
        )
        == "CANDIDATE_UNTRACKED"
    )


def test_tracked_clean_lifecycle_is_exact(checker) -> None:
    expected = set(checker.EXACT4_PATHS)
    assert (
        checker.classify_lifecycle_from_facts(
            tracked_exact4=expected,
            ordinary_untracked=set(),
            status_entries=(),
            working_diff=set(),
            cached_diff=set(),
        )
        == "TRACKED_CLEAN"
    )


@pytest.mark.parametrize(
    "mutation",
    ("dirty", "staged", "extra", "partial", "mixed"),
)
def test_lifecycle_dirty_staged_extra_and_partial_fail_closed(
    checker,
    mutation: str,
) -> None:
    expected = set(checker.EXACT4_PATHS)
    facts = {
        "tracked_exact4": set(),
        "ordinary_untracked": set(expected),
        "status_entries": tuple(f"?? {path}" for path in sorted(expected)),
        "working_diff": set(),
        "cached_diff": set(),
    }
    if mutation == "dirty":
        facts["working_diff"] = {checker.PRODUCTION_RELATIVE}
    elif mutation == "staged":
        facts["cached_diff"] = {checker.PRODUCTION_RELATIVE}
    elif mutation == "extra":
        facts["ordinary_untracked"].add("extra.txt")
        facts["status_entries"] += ("?? extra.txt",)
    elif mutation == "partial":
        facts["ordinary_untracked"].remove(checker.GUIDE_RELATIVE)
        facts["status_entries"] = tuple(
            f"?? {path}" for path in sorted(facts["ordinary_untracked"])
        )
    else:
        facts["tracked_exact4"] = {checker.PRODUCTION_RELATIVE}
    with pytest.raises(ValueError, match="GIT_LIFECYCLE_PROFILE_INVALID"):
        checker.classify_lifecycle_from_facts(**facts)


def test_candidate_repository_relation(checker) -> None:
    checker.validate_repository_relation_from_facts(
        profile="CANDIDATE_UNTRACKED",
        head=BASELINE,
        origin_main=BASELINE,
        ahead=0,
        behind=0,
        parent_shas=(),
        changed_paths=set(),
    )


@pytest.mark.parametrize("published", (False, True))
def test_tracked_clean_repository_relation(checker, published: bool) -> None:
    head = "a" * 40
    checker.validate_repository_relation_from_facts(
        profile="TRACKED_CLEAN",
        head=head,
        origin_main=head if published else BASELINE,
        ahead=0 if published else 1,
        behind=0,
        parent_shas=(BASELINE,),
        changed_paths=set(checker.EXACT4_PATHS),
    )


def test_b1_b3_owner_and_checker_exact_identities(checker) -> None:
    for _label, relative, byte_count, sha256 in checker.FROZEN_DEPENDENCIES:
        path = ROOT / relative
        assert path.stat().st_size == byte_count
        assert _sha(path) == sha256


def test_b3_commit_tree_subject_exact() -> None:
    output = subprocess.run(
        ("git", "show", "-s", "--format=%H%n%T%n%s", BASELINE),
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.splitlines()
    assert output == [
        BASELINE,
        "ba92ef88433c8290285dacf482ed17300753fbab",
        "add CovaPIE source binding historical immutability proof v2",
    ]


def test_b3_public_proof_is_actually_called(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0
    original = subject.historical_v2.verify_covapie_source_binding_historical_immutability_proof_v2

    def counted(*, repo_root: Path) -> dict[str, object]:
        nonlocal calls
        calls += 1
        return original(repo_root=repo_root)

    monkeypatch.setattr(
        subject.historical_v2,
        "verify_covapie_source_binding_historical_immutability_proof_v2",
        counted,
    )
    verified = subject.verify_covapie_source_binding_future_exact_posix_mode_guard_v2(
        repo_root=ROOT
    )
    assert calls == 1
    assert verified["b3_historical_immutability_verified"] is True


def test_b3_historical_proof_required_values(result) -> None:
    assert result["b3_historical_immutability_verified"] is True
    assert result["historical_exact_mode_occurrences_governed_by_b3"] is True
    assert result["historical_exact_mode_metadata_preserved"] is True
    assert result["historical_v1_rewrite_required"] is False


def test_forward_baseline_is_exact_and_ancestor(result) -> None:
    assert result["future_guard_baseline_commit"] == BASELINE
    assert result["future_guard_baseline_is_ancestor"] is True


def test_production_guard_is_not_one_child_only() -> None:
    source = Path(subject.__file__).read_text(encoding="utf-8")
    assert '"merge-base"' in source
    assert '"--is-ancestor"' in source
    assert '"rev-list"' not in source
    assert "parent_shas" not in source


def test_no_v1_filename_skip_in_production() -> None:
    source = Path(subject.__file__).read_text(encoding="utf-8")
    tree = compile(source, str(subject.__file__), "exec", ast.PyCF_ONLY_AST)
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            expression = ast.get_source_segment(source, node.test) or ""
            assert not (
                "_v1" in expression.lower()
                and ("path" in expression or "relative" in expression)
            )


def test_bad_simode_exact_comparison_is_forbidden() -> None:
    snippet = """
import stat
def verify_source_binding(path, expected_mode):
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode != expected_mode:
        _fail("SOURCE_MODE_DRIFT")
"""
    assert subject._SEMANTIC_SOURCE_IDENTITY in _python_classes(snippet, "simode")


def test_bad_0o7777_binding_mode_comparison_is_forbidden() -> None:
    snippet = """
def verify_source_binding(path, binding):
    actual = format(path.stat().st_mode & 0o7777, "04o")
    if actual != binding["mode"]:
        raise ValueError("SOURCE_MODE_DRIFT")
"""
    assert subject._SEMANTIC_SOURCE_IDENTITY in _python_classes(snippet, "mask")


def test_bad_live_binding_mode_equality_is_forbidden() -> None:
    snippet = """
import stat
def validate_bound_source(metadata, binding):
    actual_mode = f"{stat.S_IMODE(metadata.st_mode):04o}"
    valid = actual_mode == binding["mode"]
    return valid
"""
    assert subject._SEMANTIC_SOURCE_IDENTITY in _python_classes(snippet, "binding")


def test_bad_exact_mode_source_membership_is_forbidden() -> None:
    snippet = """
def admit_source_identity(source_mode):
    if source_mode not in {"0600", "0644", "0664", "0755"}:
        reject("SOURCE_IDENTITY_INVALID")
"""
    assert subject._SEMANTIC_SOURCE_IDENTITY in _python_classes(snippet, "membership")


def test_alias_binding_mode_is_semantic() -> None:
    snippet = """
import stat
def verify_source_binding(path, binding):
    actual = stat.S_IMODE(path.stat().st_mode)
    expected = binding["mode"]
    if actual != expected:
        reject("SOURCE_MODE_DRIFT")
"""
    assert subject._SEMANTIC_SOURCE_IDENTITY in _python_classes(snippet, "alias")


def test_transitive_alias_binding_mode_is_semantic() -> None:
    snippet = """
import stat
def verify_source_binding(path, binding):
    actual = stat.S_IMODE(path.stat().st_mode)
    observed = actual
    expected = binding["mode"]
    required = expected
    if observed != required:
        reject("SOURCE_MODE_DRIFT")
"""
    assert subject._SEMANTIC_SOURCE_IDENTITY in _python_classes(
        snippet,
        "transitive_alias",
    )


def test_unknown_full_mode_comparison_never_disappears() -> None:
    snippet = """
import stat
def verify_policy(path, policy_value):
    observed = stat.S_IMODE(path.stat().st_mode)
    if observed != policy_value:
        reject("UNKNOWN_MODE_POLICY")
"""
    classes = _python_classes(snippet, "unknown_full")
    assert classes
    assert subject._AMBIGUOUS in classes


def test_non_historical_exact_posix_mode_is_semantic() -> None:
    snippet = """
import stat
def verify_source_binding(path):
    actual = stat.S_IMODE(path.stat().st_mode)
    if actual != 0o640:
        reject("SOURCE_IDENTITY_INVALID")
"""
    assert subject._SEMANTIC_SOURCE_IDENTITY in _python_classes(snippet, "mode_640")


def test_candidate_wording_cannot_override_source_identity() -> None:
    snippet = """
import stat
def verify_candidate_source_binding(path):
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode != 0o644:
        reject("SOURCE_IDENTITY_INVALID")
"""
    classes = _python_classes(snippet, "candidate_source_collision")
    assert subject._SEMANTIC_SOURCE_IDENTITY in classes
    assert subject._CANDIDATE_HYGIENE not in classes


def test_executable_name_without_bit_evidence_cannot_allow_identity() -> None:
    snippet = """
import stat
def verify_source_binding(path, binding):
    actual = stat.S_IMODE(path.stat().st_mode)
    executable_policy = binding["mode"]
    if actual != executable_policy:
        reject("SOURCE_MODE_DRIFT")
"""
    classes = _python_classes(snippet, "executable_name_collision")
    assert classes & {subject._SEMANTIC_SOURCE_IDENTITY, subject._AMBIGUOUS}
    assert subject._GIT_OR_EXECUTABLE_CLASS not in classes


def test_historical_mode_cannot_propagate_into_live_identity() -> None:
    snippet = """
import stat
def verify_source(path, binding):
    actual = stat.S_IMODE(path.stat().st_mode)
    expected = binding["historical_mode"]
    if actual != expected:
        reject("SOURCE_MODE_DRIFT")
"""
    classes = _python_classes(snippet, "historical_live_identity")
    assert classes & {subject._SEMANTIC_SOURCE_IDENTITY, subject._AMBIGUOUS}
    assert subject._REPORTING_DIAGNOSTIC not in classes


def test_world_write_security_is_allowed() -> None:
    snippet = """
import stat
def verify_source_security(path):
    mode = path.stat().st_mode
    if mode & stat.S_IWOTH:
        fail("WORLD_WRITABLE")
"""
    classes = _python_classes(snippet, "world_write")
    assert classes == {subject._SECURITY_HYGIENE}


def test_executable_class_is_allowed() -> None:
    snippet = """
def verify_executable_class(path, expected_executable):
    mode = path.stat().st_mode
    actual_executable = bool(mode & 0o111)
    if actual_executable != expected_executable:
        fail("EXECUTABLE_CLASS")
"""
    classes = _python_classes(snippet, "exec")
    assert subject._GIT_OR_EXECUTABLE_CLASS in classes
    assert not classes & {subject._SEMANTIC_SOURCE_IDENTITY, subject._AMBIGUOUS}


def test_candidate_0644_0664_hygiene_is_allowed() -> None:
    snippet = """
import stat
def verify_candidate_exact4_hygiene(path):
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode not in {0o644, 0o664}:
        fail("CANDIDATE_MODE")
"""
    classes = _python_classes(snippet, "candidate")
    assert subject._CANDIDATE_HYGIENE in classes
    assert not classes & {subject._SEMANTIC_SOURCE_IDENTITY, subject._AMBIGUOUS}


def test_git_100644_100755_class_is_allowed() -> None:
    snippet = """
def verify_git_file_class(path_modes):
    if path_modes["owner.py"] not in {"100644", "100755"}:
        fail("GIT_FILE_CLASS")
"""
    classes = _python_classes(snippet, "git")
    assert classes == {subject._GIT_OR_EXECUTABLE_CLASS}


def test_historical_reporting_mode_is_allowed() -> None:
    snippet = """
def report_history(report):
    report["historical_mode"] = "0600"
"""
    assert _python_classes(snippet, "report") == {subject._REPORTING_DIAGNOSTIC}


def test_legacy_mode_to_exec_class_only_is_allowed() -> None:
    snippet = """
def legacy_provenance(legacy_mode):
    expected_executable = bool(int(legacy_mode, 8) & 0o111)
    return expected_executable
"""
    classes = _python_classes(snippet, "legacy_exec")
    assert subject._GIT_OR_EXECUTABLE_CLASS in classes
    assert not classes & {subject._SEMANTIC_SOURCE_IDENTITY, subject._AMBIGUOUS}


def test_python_unknown_live_mode_comparison_fails_closed() -> None:
    snippet = """
def verify_unknown(path, policy_value):
    mode = path.stat().st_mode
    if mode != policy_value:
        fail("UNKNOWN")
"""
    assert subject._AMBIGUOUS in _python_classes(snippet, "unknown")


def test_json_path_bytes_sha_mode_binding_is_forbidden() -> None:
    text = (
        '{"path":"source.csv","byte_count":12,'
        '"sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",'
        '"mode":"0644"}'
    )
    rows = subject._classify_json_text_v2(
        text,
        source_path="data/derived/covalent_small/bad.json",
    )
    assert _classes(rows) == {subject._SEMANTIC_SOURCE_IDENTITY}


def _classes(rows: tuple[dict[str, object], ...]) -> set[str]:
    return {str(row["semantic_class"]) for row in rows}


def test_json_reporting_only_historical_mode_is_allowed() -> None:
    rows = subject._classify_json_text_v2(
        '{"historical_mode":"0600","purpose":"reporting_only"}',
        source_path="data/derived/covalent_small/reporting.json",
    )
    assert _classes(rows) == {subject._REPORTING_DIAGNOSTIC}


def test_json_ambiguous_binding_fails_closed() -> None:
    rows = subject._classify_json_text_v2(
        '{"path":"source.csv","expected_mode":"0644"}',
        source_path="data/derived/covalent_small/ambiguous.json",
    )
    assert subject._AMBIGUOUS in _classes(rows)


def test_json_historical_mode_identity_collision_fails_closed() -> None:
    text = (
        '{"path":"source.csv","byte_count":12,'
        '"sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",'
        '"historical_mode":"0644"}'
    )
    rows = subject._classify_json_text_v2(
        text,
        source_path="data/derived/covalent_small/historical_identity.json",
    )
    assert _classes(rows) & {subject._SEMANTIC_SOURCE_IDENTITY, subject._AMBIGUOUS}
    assert subject._REPORTING_DIAGNOSTIC not in _classes(rows)


def test_test_only_negative_snippet_does_not_become_violation() -> None:
    text = '''
BAD = """
import stat
mode = stat.S_IMODE(path.stat().st_mode)
if mode != expected_mode:
    fail("SOURCE_MODE_DRIFT")
"""
'''
    rows = subject._classify_python_text_v2(
        text,
        source_path="tests/test_covapie_synthetic_negative.py",
    )
    assert rows
    assert all(row["context_class"] == "TEST_ONLY" for row in rows)


def test_unchanged_legacy_v1_is_outside_current_scan(result) -> None:
    assert result["known_legacy_v1_contains_forbidden_pattern"] is True
    assert result["unchanged_legacy_v1_not_counted_as_future_violation"] is True
    scanned = set(result["future_guard_scanned_python_paths"])
    assert subject._LEGACY_CONTROL_RELATIVE not in scanned


def test_same_legacy_bytes_as_future_are_detected(result) -> None:
    path = ROOT / subject._LEGACY_CONTROL_RELATIVE
    rows = subject._classify_python_text_v2(
        path.read_text(encoding="utf-8"),
        source_path=subject._LEGACY_CONTROL_RELATIVE,
        test_only=False,
    )
    assert subject._SEMANTIC_SOURCE_IDENTITY in _classes(rows)
    assert result["same_legacy_bytes_simulated_as_future_modification_detected"] is True


def test_b4_production_and_checker_self_scan_clean(result) -> None:
    assert result["B4_PRODUCTION_SELF_SCAN_PASSED"] is True
    assert result["B4_CHECKER_SELF_SCAN_PASSED"] is True
    scanned = set(result["future_guard_scanned_python_paths"])
    assert subject._PRODUCTION_RELATIVE in scanned
    assert subject._CHECKER_RELATIVE in scanned
    assert result["new_semantic_exact_posix_mode_occurrence_count"] == 0
    assert result["new_ambiguous_mode_occurrence_count"] == 0


def test_current_lifecycle_scan_surface_counts(result) -> None:
    tracked = subprocess.run(
        ("git", "ls-files", "--", subject._PRODUCTION_RELATIVE),
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.strip()
    assert result["post_b3_tracked_changed_relevant_path_count"] == (3 if tracked else 0)
    assert result["working_tree_modified_relevant_path_count"] == 0
    assert result["ordinary_untracked_relevant_path_count"] == (0 if tracked else 3)
    assert result["future_guard_scanned_python_file_count"] == 3
    assert result["future_guard_scanned_json_file_count"] == 0
    assert result["future_guard_scanned_total_file_count"] == 3


def test_worktree_symlink_read_fails_closed(tmp_path: Path) -> None:
    target = tmp_path / "target.py"
    target.write_text("VALUE = 1\n", encoding="utf-8")
    link = tmp_path / "link.py"
    link.symlink_to(target.name)
    with pytest.raises(
        subject.SourceBindingFutureExactPosixModeGuardV2Error,
        match="SYMLINK_COMPONENT_FORBIDDEN",
    ):
        subject._read_worktree_text(tmp_path.resolve(), "link.py")


def test_canonical_exact5_and_training_boundary(result) -> None:
    assert result["global_canonical_task_count"] == 5
    assert result["B3_present"] is True
    assert result["sixth_task_present"] is False
    assert result["ready_for_training"] is False
    assert result["ready_to_close_source_binding_filesystem_mode_v2_migration"] is True


def test_allowed_counts_are_reported_without_zero_assumption(result) -> None:
    keys = (
        "security_hygiene_occurrence_count",
        "executable_class_occurrence_count",
        "git_file_class_occurrence_count",
        "candidate_hygiene_occurrence_count",
        "reporting_diagnostic_occurrence_count",
        "test_only_occurrence_count",
    )
    assert all(type(result[key]) is int and result[key] >= 0 for key in keys)
    assert result["test_only_occurrence_count"] > 0


def test_classifier_order_is_deterministic() -> None:
    text = Path(subject.__file__).read_text(encoding="utf-8")
    first = subject._classify_python_text_v2(
        text,
        source_path=subject._PRODUCTION_RELATIVE,
    )
    second = subject._classify_python_text_v2(
        text,
        source_path=subject._PRODUCTION_RELATIVE,
    )
    assert first == second
    assert Counter(row["semantic_class"] for row in first) == Counter(
        row["semantic_class"] for row in second
    )
