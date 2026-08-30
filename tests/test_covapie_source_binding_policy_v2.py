from __future__ import annotations

import ast
import hashlib
import importlib.util
import os
from pathlib import Path
import stat
from types import SimpleNamespace

import pytest

from covalent_ext import covapie_source_binding_policy_v2 as subject


REPO = Path(__file__).resolve().parents[1]
CHECKER_PATH = REPO / "scripts/check_covapie_source_binding_policy_v2.py"
SPEC = importlib.util.spec_from_file_location("check_source_binding_policy_v2", CHECKER_PATH)
assert SPEC is not None and SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)

PAYLOAD = b"fixed covapie v2 source bytes\n"
DIGEST = hashlib.sha256(PAYLOAD).hexdigest()


def _write_source(tmp_path: Path, payload: bytes = PAYLOAD, mode: int = 0o644) -> Path:
    path = tmp_path / "source.bin"
    path.write_bytes(payload)
    path.chmod(mode)
    return path


def _content(path: Path, *, byte_count: int | None = None, digest: str = DIGEST) -> bytes:
    return subject.verify_content_identity_v2(
        path=path,
        expected_byte_count=len(PAYLOAD) if byte_count is None else byte_count,
        expected_sha256=digest,
        label="TEST_SOURCE",
    )


def _bound(path: Path, *, digest: str = DIGEST) -> bytes:
    return subject.verify_bound_source_v2(
        path=path,
        expected_byte_count=len(PAYLOAD),
        expected_sha256=digest,
        label="TEST_SOURCE",
        expected_executable=False,
    )


def test_exact_content_identity_returns_exact_payload(tmp_path: Path) -> None:
    path = _write_source(tmp_path)
    assert _content(path) == PAYLOAD


def test_content_identity_rejects_wrong_expected_byte_count(tmp_path: Path) -> None:
    path = _write_source(tmp_path)
    with pytest.raises(subject.SourceBindingPolicyV2Error, match="SOURCE_BYTE_COUNT_MISMATCH"):
        _content(path, byte_count=len(PAYLOAD) + 1)


def test_content_identity_rejects_wrong_sha(tmp_path: Path) -> None:
    path = _write_source(tmp_path)
    with pytest.raises(subject.SourceBindingPolicyV2Error, match="SOURCE_SHA256_MISMATCH"):
        _content(path, digest="0" * 64)


def test_content_identity_rejects_same_length_altered_bytes(tmp_path: Path) -> None:
    altered = bytes([PAYLOAD[0] ^ 1]) + PAYLOAD[1:]
    path = _write_source(tmp_path, altered)
    with pytest.raises(subject.SourceBindingPolicyV2Error, match="SOURCE_SHA256_MISMATCH"):
        _content(path)


@pytest.mark.parametrize("payload", [PAYLOAD[:-1], PAYLOAD + b"x"])
def test_content_identity_rejects_truncated_or_extra_bytes(
    tmp_path: Path, payload: bytes
) -> None:
    path = _write_source(tmp_path, payload)
    with pytest.raises(subject.SourceBindingPolicyV2Error, match="SOURCE_BYTE_COUNT_MISMATCH"):
        _content(path)


def test_content_identity_reports_read_failure(tmp_path: Path) -> None:
    path = tmp_path / "missing.bin"
    with pytest.raises(subject.SourceBindingPolicyV2Error, match="SOURCE_READ_FAILED"):
        _content(path)


@pytest.mark.parametrize("mode", [0o600, 0o644, 0o660, 0o664])
def test_safe_mode_family_passes_content_and_combined_gates(
    tmp_path: Path, mode: int
) -> None:
    path = _write_source(tmp_path, mode=mode)
    assert _content(path) == PAYLOAD
    assert _bound(path) == PAYLOAD


def test_checkout_mode_0644_to_0664_does_not_change_v2_content_identity(
    tmp_path: Path,
) -> None:
    path = _write_source(tmp_path, mode=0o644)
    before = _content(path)
    path.chmod(0o664)
    assert _content(path) == before == PAYLOAD


def test_checkout_mode_0600_to_0664_does_not_change_v2_content_identity(
    tmp_path: Path,
) -> None:
    path = _write_source(tmp_path, mode=0o600)
    before = _content(path)
    path.chmod(0o664)
    assert _content(path) == before == PAYLOAD


def test_content_identity_can_follow_symlink_because_security_is_separate(
    tmp_path: Path,
) -> None:
    path = _write_source(tmp_path)
    link = tmp_path / "source-link"
    link.symlink_to(path.name)
    assert _content(link) == PAYLOAD


def test_regular_safe_source_passes_security(tmp_path: Path) -> None:
    path = _write_source(tmp_path, mode=0o664)
    assert subject.verify_source_security_v2(path=path, label="SAFE") is None


def test_security_rejects_symlink(tmp_path: Path) -> None:
    path = _write_source(tmp_path)
    link = tmp_path / "source-link"
    link.symlink_to(path.name)
    with pytest.raises(subject.SourceBindingPolicyV2Error, match="SOURCE_SYMLINK_FORBIDDEN"):
        subject.verify_source_security_v2(path=link, label="SYMLINK")


def test_security_rejects_directory(tmp_path: Path) -> None:
    with pytest.raises(subject.SourceBindingPolicyV2Error, match="SOURCE_NOT_REGULAR"):
        subject.verify_source_security_v2(path=tmp_path, label="DIRECTORY")


def test_security_rejects_fifo_without_reading_it(tmp_path: Path) -> None:
    path = tmp_path / "source.fifo"
    os.mkfifo(path)
    with pytest.raises(subject.SourceBindingPolicyV2Error, match="SOURCE_NOT_REGULAR"):
        subject.verify_bound_source_v2(
            path=path,
            expected_byte_count=0,
            expected_sha256=hashlib.sha256(b"").hexdigest(),
            label="FIFO",
        )


@pytest.mark.parametrize("mode", [0o666, 0o777, 0o622])
def test_security_rejects_world_writable_regular_file(
    tmp_path: Path, mode: int
) -> None:
    path = _write_source(tmp_path, mode=mode)
    with pytest.raises(subject.SourceBindingPolicyV2Error, match="SOURCE_WORLD_WRITABLE"):
        subject.verify_source_security_v2(path=path, label="WORLD_WRITABLE")


def test_security_rejects_non_owner_readable_file(tmp_path: Path) -> None:
    path = _write_source(tmp_path, mode=0o040)
    with pytest.raises(subject.SourceBindingPolicyV2Error, match="SOURCE_OWNER_NOT_READABLE"):
        subject.verify_source_security_v2(path=path, label="OWNER_NOT_READABLE")


def test_security_rejects_unexpected_executable(tmp_path: Path) -> None:
    path = _write_source(tmp_path, mode=0o744)
    with pytest.raises(
        subject.SourceBindingPolicyV2Error,
        match="SOURCE_EXECUTABLE_CLASS_MISMATCH",
    ):
        subject.verify_source_security_v2(
            path=path,
            label="UNEXPECTED_EXECUTABLE",
            expected_executable=False,
        )


def test_security_rejects_missing_required_executable_class(tmp_path: Path) -> None:
    path = _write_source(tmp_path, mode=0o644)
    with pytest.raises(
        subject.SourceBindingPolicyV2Error,
        match="SOURCE_EXECUTABLE_CLASS_MISMATCH",
    ):
        subject.verify_source_security_v2(
            path=path,
            label="MISSING_EXECUTABLE",
            expected_executable=True,
        )


@pytest.mark.parametrize("mode", [0o700, 0o750, 0o755, 0o770, 0o775])
def test_security_accepts_safe_executable_class(tmp_path: Path, mode: int) -> None:
    path = _write_source(tmp_path, mode=mode)
    assert (
        subject.verify_source_security_v2(
            path=path,
            label="EXPECTED_EXECUTABLE",
            expected_executable=True,
        )
        is None
    )


def test_security_does_not_enforce_executable_when_unspecified(tmp_path: Path) -> None:
    path = _write_source(tmp_path, mode=0o755)
    assert subject.verify_source_security_v2(path=path, label="UNSPECIFIED") is None


def test_combined_gate_returns_payload_when_both_gates_pass(tmp_path: Path) -> None:
    path = _write_source(tmp_path, mode=0o664)
    assert _bound(path) == PAYLOAD


def test_combined_gate_rejects_safe_content_with_unsafe_security(tmp_path: Path) -> None:
    path = _write_source(tmp_path, mode=0o666)
    with pytest.raises(subject.SourceBindingPolicyV2Error, match="SOURCE_WORLD_WRITABLE"):
        _bound(path)


def test_combined_gate_rejects_safe_security_with_wrong_content(tmp_path: Path) -> None:
    path = _write_source(tmp_path, mode=0o664)
    with pytest.raises(subject.SourceBindingPolicyV2Error, match="SOURCE_SHA256_MISMATCH"):
        _bound(path, digest="f" * 64)


def test_combined_gate_rejects_object_identity_change_during_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _write_source(tmp_path)
    original = subject._inspect_source_security_v2
    call_count = 0

    def unstable_inspection(**kwargs: object) -> object:
        nonlocal call_count
        call_count += 1
        metadata = original(**kwargs)
        if call_count == 1:
            return metadata
        return SimpleNamespace(
            st_dev=metadata.st_dev,
            st_ino=metadata.st_ino + 1,
            st_mode=metadata.st_mode,
            st_size=metadata.st_size,
        )

    monkeypatch.setattr(subject, "_inspect_source_security_v2", unstable_inspection)
    with pytest.raises(subject.SourceBindingPolicyV2Error, match="SOURCE_CHANGED_DURING_READ"):
        _bound(path)


def test_public_api_is_exactly_minimal_v2_surface() -> None:
    checker._verify_public_api()
    assert subject.__all__ == (
        "SourceBindingPolicyV2Error",
        "verify_content_identity_v2",
        "verify_source_security_v2",
        "verify_bound_source_v2",
    )


def test_content_helper_has_no_exact_mode_semantic_gate() -> None:
    checker._verify_ast_separation(REPO)
    text = (REPO / checker.PRODUCTION_RELATIVE).read_text(encoding="utf-8")
    tree = ast.parse(text)
    content = checker._function_node(tree, "verify_content_identity_v2")
    content_text = ast.get_source_segment(text, content) or ""
    assert "stat.S_IMODE" not in content_text
    assert all(token not in content_text for token in ("0o600", "0o644", "0o664"))


def test_security_helper_inspects_permission_bits_separately() -> None:
    text = (REPO / checker.PRODUCTION_RELATIVE).read_text(encoding="utf-8")
    tree = ast.parse(text)
    security = checker._function_node(tree, "_inspect_source_security_v2")
    attributes = {
        checker._attribute_name(node)
        for node in ast.walk(security)
        if isinstance(node, ast.Attribute)
    }
    assert {"stat.S_IRUSR", "stat.S_IWOTH", "stat.S_IXUSR"} <= attributes


def test_production_has_no_registry_cache_or_global_mutable_state() -> None:
    checker._verify_ast_separation(REPO)
    text = (REPO / checker.PRODUCTION_RELATIVE).read_text(encoding="utf-8")
    tree = ast.parse(text)
    assert not any(isinstance(node, ast.Global) for node in ast.walk(tree))
    assert "registry" not in text.lower()
    assert "singleton" not in text.lower()


def test_phase_a_audit_summary_is_bound_and_ready() -> None:
    result = checker._verify_phase_a_dependency(REPO)
    assert result == {
        "published": True,
        "migration_occurrences": 12,
        "active_target_files": 8,
        "historical_rewrite_required": False,
    }


def test_current_2a2_census_is_known_good_content_binding_reference() -> None:
    result = checker._verify_good_reference(REPO)
    assert result == {
        "count": 108,
        "digest": checker.GOOD_BINDING_DIGEST,
        "mode_fields": 0,
    }


def test_all_eight_active_consumers_remain_byte_identical() -> None:
    assert checker._verify_active_consumers_untouched(REPO) == 8
    assert len(checker.ACTIVE_CONSUMER_SHA256) == 8


def test_historical_2a2_and_cht_owner_sha_regression_is_explicit() -> None:
    assert checker.ACTIVE_CONSUMER_SHA256[
        "src/covalent_ext/"
        "covapie_2a2_completed_decision_ingestion_and_task_label_availability_v1.py"
    ] == "57d42fcf673794f27adc7b897c0f51db4304d32f2d35a950b89d63cf4cf7060d"
    assert checker.ACTIVE_CONSUMER_SHA256[
        "src/covalent_ext/"
        "covapie_cht_completed_decision_ingestion_and_task_label_availability_v1.py"
    ] == "7a5561f1cb35465a2dbe6af8121f06a07b7aea6d82051e3945352cf1c669aff7"


def test_candidate_and_tracked_clean_are_only_success_lifecycle_profiles() -> None:
    expected = set(checker.EXACT4_PATHS)
    assert checker.classify_lifecycle_from_facts(
        tracked_exact4=set(),
        ordinary_untracked=expected,
        status_entries=tuple(f"?? {path}" for path in sorted(expected)),
        working_diff=set(),
        cached_diff=set(),
    ) == "CANDIDATE_UNTRACKED"
    assert checker.classify_lifecycle_from_facts(
        tracked_exact4=expected,
        ordinary_untracked=set(),
        status_entries=(),
        working_diff=set(),
        cached_diff=set(),
    ) == "TRACKED_CLEAN"


def test_committed_unpushed_and_published_relations_are_tracked_clean() -> None:
    changed = set(checker.EXACT4_PATHS)
    checker._validate_repository_relation_v2(
        profile="TRACKED_CLEAN",
        head="a" * 40,
        origin_main=checker.BASELINE_HEAD,
        ahead=1,
        behind=0,
        parent_shas=(checker.BASELINE_HEAD,),
        changed_paths=changed,
    )
    checker._validate_repository_relation_v2(
        profile="TRACKED_CLEAN",
        head="a" * 40,
        origin_main="a" * 40,
        ahead=0,
        behind=0,
        parent_shas=(checker.BASELINE_HEAD,),
        changed_paths=changed,
    )


@pytest.mark.parametrize(
    ("tracked", "untracked", "status", "working", "cached"),
    [
        (set(), set(checker.EXACT4_PATHS[1:]), (), set(), set()),
        (set(), set(checker.EXACT4_PATHS) | {"extra.txt"}, (), set(), set()),
        (set(), set(checker.EXACT4_PATHS), (" M existing.py",), {"existing.py"}, set()),
        (set(), set(checker.EXACT4_PATHS), ("A  staged.py",), set(), {"staged.py"}),
        ({checker.EXACT4_PATHS[0]}, set(checker.EXACT4_PATHS[1:]), (), set(), set()),
    ],
)
def test_partial_extra_dirty_staged_and_mixed_lifecycle_fail_closed(
    tracked: set[str],
    untracked: set[str],
    status: tuple[str, ...],
    working: set[str],
    cached: set[str],
) -> None:
    with pytest.raises(ValueError, match="GIT_LIFECYCLE_PROFILE_INVALID"):
        checker.classify_lifecycle_from_facts(
            tracked_exact4=tracked,
            ordinary_untracked=untracked,
            status_entries=status,
            working_diff=working,
            cached_diff=cached,
        )


def test_invalid_tracked_clean_commit_identity_fails_closed() -> None:
    with pytest.raises(ValueError, match="TRACKED_CLEAN_COMMIT_IDENTITY_INVALID"):
        checker._validate_repository_relation_v2(
            profile="TRACKED_CLEAN",
            head="a" * 40,
            origin_main=checker.BASELINE_HEAD,
            ahead=1,
            behind=0,
            parent_shas=(checker.BASELINE_HEAD,),
            changed_paths=set(checker.EXACT4_PATHS[1:]),
        )


def test_actual_candidate_lifecycle_and_exact4_hygiene() -> None:
    assert checker.verify_git_lifecycle(REPO) in {"CANDIDATE_UNTRACKED", "TRACKED_CLEAN"}
    records = checker.verify_exact4_file_hygiene(REPO)
    assert [record["path"] for record in records] == list(checker.EXACT4_PATHS)
    assert all(record["mode"] in {"0644", "0664"} for record in records)
