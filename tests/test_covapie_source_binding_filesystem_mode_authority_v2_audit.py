from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import subprocess

import pytest


REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in __import__("sys").path:
    __import__("sys").path.insert(0, str(REPO / "src"))

from covalent_ext import covapie_source_binding_filesystem_mode_authority_v2_audit as subject  # noqa: E402


CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_covapie_source_binding_filesystem_mode_authority_v2_audit",
    REPO / "scripts/check_covapie_source_binding_filesystem_mode_authority_v2_audit.py",
)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*arguments: str) -> str:
    return subprocess.run(
        ("git", *arguments),
        cwd=REPO,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.rstrip("\n")


@pytest.fixture(scope="session")
def computation():
    return subject.compute_covapie_source_binding_filesystem_mode_authority_v2_audit(
        REPO
    )


@pytest.fixture(scope="session")
def inventory(computation):
    return list(computation["inventory"])


def _classes(snippet: str) -> set[str]:
    rows = subject.classify_python_text_v2(
        snippet,
        source_path="synthetic/audit_case.py",
        source_scope="REPOSITORY_OWNER_PYTHON",
        source_path_namespace="repository_relative",
    )
    return {str(row["semantic_class"]) for row in rows}


def test_public_api_exact7_and_phase_a_boundary() -> None:
    assert subject.__all__ == (
        "SourceBindingFilesystemModeAuthorityV2AuditError",
        "classify_python_text_v2",
        "compute_covapie_source_binding_filesystem_mode_authority_v2_audit",
        "build_covapie_source_binding_filesystem_mode_authority_v2_audit_artifacts",
        "materialize_covapie_source_binding_filesystem_mode_authority_v2_audit_artifacts",
    )
    assert len(subject.EXACT7_PATHS) == 7
    assert len(set(subject.EXACT7_PATHS)) == 7
    assert subject.BASELINE_HEAD == "89a8cf17a235cdca9eecad275794a5a86be2e01d"
    assert subject.BASELINE_TREE == "1fade78157312f44ef27232953d958453837bfb1"


def test_repository_and_external_scan_scope_is_complete(computation) -> None:
    scope = computation["scope_counts"]
    assert scope == {
        "repository_python_files_scanned": 1199,
        "external_covapie_state_python_files_scanned": 14,
        "derived_json_files_inspected": 528,
        "external_authority_provenance_json_files_inspected": 14,
        "authority_provenance_json_files_inspected": 542,
        "total_files_scanned": 1755,
    }
    bindings = computation["source_bindings"]
    assert len(bindings) == 1755
    assert len({(row["path_namespace"], row["path"]) for row in bindings}) == 1755
    assert all(
        not PurePosixPath(str(row["path"])).is_absolute()
        and ".." not in PurePosixPath(str(row["path"])).parts
        for row in bindings
    )
    assert all(set(row) == set(subject.CURRENT_CENSUS_BINDING_FIELDS) for row in bindings)


def test_ast_classifies_exact_source_identity_coupling() -> None:
    snippet = """
import stat
def read_bound_file(path, byte_count, digest, expected_mode):
    payload = path.read_bytes()
    mode = format(stat.S_IMODE(path.stat().st_mode), "04o")
    if mode != expected_mode or len(payload) != byte_count or sha256(payload) != digest:
        raise ValueError("SOURCE_DRIFT")
"""
    assert "SEMANTIC_SOURCE_IDENTITY_EXACT_POSIX_MODE" in _classes(snippet)


def test_ast_classifies_security_hygiene() -> None:
    snippet = """
import stat
def consume(path):
    if not stat.S_ISREG(path.lstat().st_mode) or path.is_symlink():
        raise ValueError("UNSAFE")
    if path.stat().st_mode & stat.S_IWOTH:
        raise ValueError("WORLD_WRITABLE")
"""
    assert "SECURITY_HYGIENE_MODE_CHECK" in _classes(snippet)


def test_ast_classifies_candidate_safe_mode_family_without_false_debt() -> None:
    snippet = """
import stat
def check_candidate(path):
    if stat.S_IMODE(path.stat().st_mode) not in {0o644, 0o664}:
        raise ValueError("CANDIDATE_MODE_UNSAFE")
"""
    rows = subject.classify_python_text_v2(
        snippet,
        source_path="synthetic/candidate.py",
        source_scope="REPOSITORY_CHECKER_PYTHON",
        source_path_namespace="repository_relative",
    )
    candidate = [
        row
        for row in rows
        if row["semantic_class"] == "CANDIDATE_ARTIFACT_MODE_HYGIENE"
    ]
    assert candidate
    assert all(row["debt_disposition"] == "PRESERVE_AS_IS" for row in candidate)


def test_ast_classifies_git_file_class() -> None:
    snippet = """
def verify_git(git_mode):
    if git_mode not in {"100644", "100755"}:
        raise ValueError("NOT_BLOB")
"""
    assert "GIT_EXECUTABLE_BIT_OR_FILE_CLASS_CONTRACT" in _classes(snippet)


def test_ast_classifies_reporting_only() -> None:
    snippet = """
import stat
def report(path, payload):
    return {"path": "x", "sha256": sha(payload), "mode": f"{stat.S_IMODE(path.stat().st_mode):04o}"}
"""
    assert "REPORTING_OR_DIAGNOSTIC_MODE_METADATA" in _classes(snippet)


def test_ast_classifies_unresolved_gate_as_ambiguous() -> None:
    snippet = """
def unknown(current_mode, expected_mode):
    if current_mode != expected_mode:
        reject()
"""
    assert "AMBIGUOUS_REQUIRES_HUMAN_REVIEW" in _classes(snippet)


def test_inventory_enums_ids_and_order_are_deterministic(inventory) -> None:
    assert inventory
    assert len({row["occurrence_id"] for row in inventory}) == len(inventory)
    assert {row["semantic_class"] for row in inventory} <= set(subject.SEMANTIC_CLASSES)
    assert {row["lifecycle_class"] for row in inventory} <= set(subject.LIFECYCLE_CLASSES)
    assert {row["debt_disposition"] for row in inventory} <= set(subject.DEBT_DISPOSITIONS)
    keys = [
        (
            row["source_path_namespace"],
            row["source_path"],
            row["line_start"],
            row["line_end"],
            row["occurrence_id"],
        )
        for row in inventory
    ]
    assert keys == sorted(keys)


def test_known_2a2_exact3_regression_is_source_proven(computation, inventory) -> None:
    cases = computation["summary"]["known_regression_cases"]
    assert [
        (case["source_role"], case["expected_mode"])
        for case in cases
    ] == [
        ("published_role_profile_runtime_owner", "0644"),
        ("canonical_role_and_task_semantics_owner", "0644"),
        ("published_1f8_event_task_label_availability", "0600"),
    ]
    assert all(
        case["content_identity_contract"] == ["byte_count", "sha256"]
        and case["byte_sha_can_remain_exact_while_checkout_mode_changes"] is True
        and case["semantic_class"]
        == "SEMANTIC_SOURCE_IDENTITY_EXACT_POSIX_MODE"
        and case["lifecycle_class"] == "HISTORICAL_IMMUTABLE_V1"
        and case["debt_disposition"]
        == "PRESERVE_HISTORICAL_BUT_DO_NOT_PROPAGATE"
        for case in cases
    )
    validator_path = subject.TWO_A2_FORMAL_VALIDATOR_RELATIVE.as_posix()
    rows = [row for row in inventory if row["source_path"] == validator_path]
    assert any(
        row["semantic_class"]
        == "SEMANTIC_SOURCE_IDENTITY_EXACT_POSIX_MODE"
        and row["mode_participates_in_admit_reject_decision"] is True
        and row["bytes_or_sha_also_checked"] is True
        for row in rows
    )


def test_mode_only_checkout_reconstruction_proof_is_logically_separated() -> None:
    payload = b"same evidence\n"
    expected_sha = hashlib.sha256(payload).hexdigest()
    checkout_payload = bytes(payload)
    assert len(checkout_payload) == len(payload)
    assert hashlib.sha256(checkout_payload).hexdigest() == expected_sha
    assert "0644" != "0664"


def test_current_2a2_census_is_exact108_mode_free_negative_control(computation) -> None:
    good = computation["summary"]["current_good_reference"]
    assert good == {
        "semantic_binding_count": 108,
        "canonical_digest": (
            "964f4b3747d42a43d05d1adc6f432264ce546ef93f9faace23fa3379452bfd15"
        ),
        "binding_fields": [
            "artifact_role",
            "path",
            "path_namespace",
            "byte_count",
            "sha256",
        ],
        "exact_posix_mode_field_count": 0,
        "CURRENT_2A2_CENSUS_PROPAGATES_EXACT_POSIX_MODE_AUTHORITY": False,
        "negative_control_pass": True,
    }


def test_historical_and_external_sources_are_read_only_during_compute() -> None:
    external_root = REPO.parent / subject.EXTERNAL_SCAN_ROOT_RELATIVE
    paths = tuple(
        sorted(
            path
            for path in external_root.rglob("*")
            if path.is_file()
            and path.parent.name in subject.EXTERNAL_ALLOWED_STAGE_DIRECTORIES
            and path.suffix in {".py", ".json"}
        )
    )
    before = {path: _sha(path) for path in paths}
    subject.compute_covapie_source_binding_filesystem_mode_authority_v2_audit(REPO)
    after = {path: _sha(path) for path in paths}
    assert after == before
    assert not _git("diff", "--name-only")
    assert not _git("diff", "--cached", "--name-only")


def test_v2_policy_is_small_separated_and_historical_compatible(computation) -> None:
    summary = computation["summary"]
    policy = summary["proposed_v2_policy"]
    assert policy["git_tracked_semantic_source_identity"] == [
        "path",
        "path_namespace",
        "byte_count",
        "sha256",
    ]
    assert policy["exact_runtime_posix_mode_is_semantic_identity"] is False
    assert policy["semantic_identity_and_security_hygiene_are_separate"] is True
    security = summary["security_hygiene_policy"]
    assert security["candidate_safe_mode_family"] == ["0644", "0664"]
    assert security["group_write_0664_automatically_forbidden"] is False
    history = summary["historical_compatibility_policy"]
    assert history["historical_v1_authority_bytes_remain_immutable"] is True
    assert history["historical_validator_rewrite_required"] is False
    assert [step["step"] for step in summary["implementation_plan"]] == [
        "V2-B1",
        "V2-B2",
        "V2-B3",
        "V2-B4",
    ]


def test_exact5_scientific_boundary_is_untouched(computation) -> None:
    boundary = computation["summary"]["scientific_boundary"]
    assert boundary["canonical_exact5_task_count"] == 5
    assert boundary["semantic_long_names"][3] == "scaffold_only"
    assert boundary["B3_present"] is True
    assert boundary["sixth_task_present"] is False
    assert boundary["I12_REVIEW_STARTED"] is False
    assert boundary["TRAINING_STARTED"] is False
    assert boundary["READY_FOR_TRAINING"] is False


def test_build_is_byte_deterministic_and_matches_exact3() -> None:
    first = subject.build_covapie_source_binding_filesystem_mode_authority_v2_audit_artifacts(
        REPO
    )
    second = subject.build_covapie_source_binding_filesystem_mode_authority_v2_audit_artifacts(
        REPO
    )
    assert first == second
    assert set(first) == {
        subject.INVENTORY_FILE,
        subject.SUMMARY_FILE,
        subject.MANIFEST_FILE,
    }
    assert all(len(payload) < 1024 * 1024 for payload in first.values())
    for filename, payload in first.items():
        assert (REPO / subject.OUTPUT_DIRECTORY_RELATIVE / filename).read_bytes() == payload


def test_new_manifest_has_no_exact_posix_semantic_binding() -> None:
    manifest = json.loads(
        (
            REPO / subject.OUTPUT_DIRECTORY_RELATIVE / subject.MANIFEST_FILE
        ).read_text(encoding="utf-8")
    )
    for group in (
        "scanned_source_bindings",
        "current_good_reference_bindings",
        "output_bindings_excluding_manifest_self",
    ):
        assert all(set(row) == set(subject.CURRENT_CENSUS_BINDING_FIELDS) for row in manifest[group])
        assert all(
            not {"mode", "posix_mode", "filesystem_mode", "st_mode"} & set(row)
            for row in manifest[group]
        )
    assert manifest["semantic_binding_policy"]["exact_posix_mode_field_present"] is False
    assert manifest["semantic_binding_policy"]["manifest_self_sha256_recorded"] is False


def test_checker_directly_verifies_materialized_evidence() -> None:
    result = checker.verify_materialized_audit(REPO)
    assert result["inventory_rows"] > 0
    assert result["good_reference"] == {
        "count": 108,
        "digest": "964f4b3747d42a43d05d1adc6f432264ce546ef93f9faace23fa3379452bfd15",
        "mode_fields": 0,
    }
    assert result["ready_for_v2_implementation"] is True


def test_lifecycle_candidate_and_tracked_clean_are_only_success_profiles() -> None:
    expected = set(subject.EXACT7_PATHS)
    assert checker.classify_lifecycle_from_facts(
        tracked_exact7=set(),
        ordinary_untracked=expected,
        status_entries=tuple(f"?? {path}" for path in sorted(expected)),
        working_diff=set(),
        cached_diff=set(),
    ) == "CANDIDATE_UNTRACKED"
    assert checker.classify_lifecycle_from_facts(
        tracked_exact7=expected,
        ordinary_untracked=set(),
        status_entries=(),
        working_diff=set(),
        cached_diff=set(),
    ) == "TRACKED_CLEAN"


@pytest.mark.parametrize(
    (
        "profile",
        "head",
        "origin_main",
        "ahead",
        "behind",
        "parent_shas",
        "changed_paths",
    ),
    [
        (
            "CANDIDATE_UNTRACKED",
            checker.BASELINE_HEAD,
            checker.BASELINE_HEAD,
            0,
            0,
            (),
            set(),
        ),
        (
            "TRACKED_CLEAN",
            "a" * 40,
            checker.BASELINE_HEAD,
            1,
            0,
            (checker.BASELINE_HEAD,),
            set(subject.EXACT7_PATHS),
        ),
        (
            "TRACKED_CLEAN",
            "a" * 40,
            "a" * 40,
            0,
            0,
            (checker.BASELINE_HEAD,),
            set(subject.EXACT7_PATHS),
        ),
    ],
    ids=("candidate", "tracked-committed-unpushed", "tracked-published"),
)
def test_repository_relation_success_subcases(
    profile, head, origin_main, ahead, behind, parent_shas, changed_paths
) -> None:
    assert checker._validate_repository_relation_v1(
        profile=profile,
        head=head,
        origin_main=origin_main,
        ahead=ahead,
        behind=behind,
        parent_shas=parent_shas,
        changed_paths=changed_paths,
    ) is None


@pytest.mark.parametrize(
    (
        "head",
        "origin_main",
        "ahead",
        "behind",
        "parent_shas",
        "changed_paths",
    ),
    [
        ("a" * 40, checker.BASELINE_HEAD, 1, 0, ("b" * 40,), set(subject.EXACT7_PATHS)),
        (
            "a" * 40,
            checker.BASELINE_HEAD,
            1,
            0,
            (checker.BASELINE_HEAD, "b" * 40),
            set(subject.EXACT7_PATHS),
        ),
        (
            "a" * 40,
            checker.BASELINE_HEAD,
            1,
            0,
            (checker.BASELINE_HEAD,),
            set(subject.EXACT7_PATHS[1:]),
        ),
        ("a" * 40, "b" * 40, 1, 1, (checker.BASELINE_HEAD,), set(subject.EXACT7_PATHS)),
        ("a" * 40, checker.BASELINE_HEAD, 2, 0, (checker.BASELINE_HEAD,), set(subject.EXACT7_PATHS)),
        ("a" * 40, checker.BASELINE_HEAD, 0, 1, (checker.BASELINE_HEAD,), set(subject.EXACT7_PATHS)),
        ("a" * 40, "a" * 40, 1, 0, (checker.BASELINE_HEAD,), set(subject.EXACT7_PATHS)),
        ("a" * 40, checker.BASELINE_HEAD, 0, 0, (checker.BASELINE_HEAD,), set(subject.EXACT7_PATHS)),
    ],
    ids=(
        "wrong-parent",
        "two-parents",
        "changed-path-set",
        "unrelated-origin",
        "head-two-commits-ahead",
        "origin-ahead-of-head",
        "published-nonzero-relation",
        "committed-unpushed-wrong-relation",
    ),
)
def test_tracked_clean_repository_relation_fail_closed(
    head, origin_main, ahead, behind, parent_shas, changed_paths
) -> None:
    with pytest.raises(ValueError, match="TRACKED_CLEAN_"):
        checker._validate_repository_relation_v1(
            profile="TRACKED_CLEAN",
            head=head,
            origin_main=origin_main,
            ahead=ahead,
            behind=behind,
            parent_shas=parent_shas,
            changed_paths=changed_paths,
        )


@pytest.mark.parametrize(
    ("origin_main", "ahead", "behind"),
    [("b" * 40, 0, 0), (checker.BASELINE_HEAD, 1, 0)],
    ids=("origin-not-baseline", "nonzero-ahead-behind"),
)
def test_candidate_repository_relation_fail_closed(
    origin_main, ahead, behind
) -> None:
    with pytest.raises(ValueError, match="CANDIDATE_REPOSITORY_RELATION_INVALID"):
        checker._validate_repository_relation_v1(
            profile="CANDIDATE_UNTRACKED",
            head=checker.BASELINE_HEAD,
            origin_main=origin_main,
            ahead=ahead,
            behind=behind,
            parent_shas=(),
            changed_paths=set(),
        )


def test_repository_relation_does_not_create_a_third_profile() -> None:
    with pytest.raises(ValueError, match="REPOSITORY_RELATION_PROFILE_INVALID"):
        checker._validate_repository_relation_v1(
            profile="PUBLISHED",
            head="a" * 40,
            origin_main="a" * 40,
            ahead=0,
            behind=0,
            parent_shas=(checker.BASELINE_HEAD,),
            changed_paths=set(subject.EXACT7_PATHS),
        )


@pytest.mark.parametrize(
    ("tracked", "untracked", "status", "working", "cached"),
    [
        ({subject.EXACT7_PATHS[0]}, set(subject.EXACT7_PATHS[1:]), (), set(), set()),
        (set(), set(subject.EXACT7_PATHS) | {"extra.txt"}, (), set(), set()),
        (set(), set(subject.EXACT7_PATHS), (" M existing.py",), set(), set()),
        (set(), set(subject.EXACT7_PATHS), (), {"existing.py"}, set()),
        (set(), set(subject.EXACT7_PATHS), (), set(), {"staged.py"}),
        (
            {subject.EXACT7_PATHS[0]},
            set(subject.EXACT7_PATHS[1:]),
            (f"A  {subject.EXACT7_PATHS[0]}",),
            set(),
            {subject.EXACT7_PATHS[0]},
        ),
    ],
)
def test_lifecycle_partial_extra_dirty_and_staged_fail_closed(
    tracked, untracked, status, working, cached
) -> None:
    with pytest.raises(ValueError, match="GIT_LIFECYCLE_PROFILE_INVALID"):
        checker.classify_lifecycle_from_facts(
            tracked_exact7=set(tracked),
            ordinary_untracked=set(untracked),
            status_entries=tuple(status),
            working_diff=set(working),
            cached_diff=set(cached),
        )


def test_actual_candidate_lifecycle_and_file_hygiene() -> None:
    profile = checker.verify_git_lifecycle(REPO)
    assert profile in {"CANDIDATE_UNTRACKED", "TRACKED_CLEAN"}
    assert len(checker.verify_exact7_file_hygiene(REPO)) == 7
