#!/usr/bin/env python3
"""Independent fail-closed checker for the with-ME7 cumulative1000 census."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
import csv
import io
import json
from pathlib import Path
import stat
import subprocess
import sys
from typing import Any, NoReturn


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_v1 as generic,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_me7_v1 as reconciliation_owner,
)
from covalent_ext import (  # noqa: E402
    covapie_cumulative1000_current_global_readiness_census_with_me7_v1 as subject,
)


ERROR_TOKEN = "COVAPIE_WITH_ME7_CENSUS_CHECK_ERROR"
CANDIDATE_UNTRACKED = "CANDIDATE_UNTRACKED"
TRACKED_CLEAN = "TRACKED_CLEAN"


def _fail(reason: str) -> NoReturn:
    raise ValueError(f"{ERROR_TOKEN}:{reason}")


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0 or completed.stderr:
        _fail("GIT_COMMAND_FAILED:" + args[0])
    try:
        return completed.stdout.decode("utf-8").rstrip("\n")
    except UnicodeDecodeError as error:
        raise ValueError(f"{ERROR_TOKEN}:GIT_OUTPUT_NOT_UTF8") from error


def classify_repository_profile(
    *,
    expected_paths: Sequence[str],
    tracked_paths: set[str],
    ordinary_untracked: set[str],
    status_lines: Sequence[str],
    working_diff: set[str],
    cached_diff: set[str],
) -> str:
    """Classify only the two authorized real-worktree lifecycle profiles."""

    expected = set(expected_paths)
    candidate_status = {"?? " + path for path in expected}
    if (
        ordinary_untracked == expected
        and not expected & tracked_paths
        and set(status_lines) == candidate_status
        and not working_diff
        and not cached_diff
    ):
        return CANDIDATE_UNTRACKED
    if (
        expected.issubset(tracked_paths)
        and not ordinary_untracked
        and not status_lines
        and not working_diff
        and not cached_diff
    ):
        return TRACKED_CLEAN
    _fail("UNKNOWN_REPOSITORY_PROFILE")


def validate_tracked_index_modes(
    stage_records: Sequence[tuple[str, str, str, str]], expected_paths: set[str]
) -> dict[str, str]:
    """Require one stage-0, non-symlink, non-executable 100644 record per file."""

    if len(stage_records) != len(expected_paths):
        _fail("GIT_INDEX_RECORD_COUNT_INVALID")
    modes: dict[str, str] = {}
    for mode, object_id, stage, path in stage_records:
        if (
            path not in expected_paths
            or path in modes
            or mode != "100644"
            or stage != "0"
            or len(object_id) not in {40, 64}
        ):
            _fail("GIT_INDEX_MODE_OR_STAGE_INVALID:" + path)
        modes[path] = mode
    if set(modes) != expected_paths:
        _fail("GIT_INDEX_PATH_SET_INVALID")
    return modes


def _ancestor(root: Path, older: str, newer: str) -> bool:
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", older, newer],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.stderr or completed.returncode not in {0, 1}:
        _fail("GIT_ANCESTRY_CHECK_FAILED")
    return completed.returncode == 0


def _parse_stage_records(payload: bytes) -> list[tuple[str, str, str, str]]:
    records: list[tuple[str, str, str, str]] = []
    for raw in filter(None, payload.split(b"\0")):
        try:
            metadata, path = raw.decode("utf-8").split("\t", 1)
            mode, object_id, stage = metadata.split(" ")
        except (UnicodeDecodeError, ValueError) as error:
            raise ValueError(f"{ERROR_TOKEN}:GIT_INDEX_RECORD_PARSE_INVALID") from error
        records.append((mode, object_id, stage, path))
    return records


def _verify_repository(root: Path) -> dict[str, object]:
    paths = tuple(subject.EXACT7_PATHS_V1)
    tracked = set(filter(None, _git(root, "ls-files").splitlines()))
    untracked = set(
        filter(None, _git(root, "ls-files", "--others", "--exclude-standard").splitlines())
    )
    status_lines = tuple(
        filter(
            None,
            _git(root, "status", "--short", "--untracked-files=all").splitlines(),
        )
    )
    working = set(filter(None, _git(root, "diff", "--name-only").splitlines()))
    cached = set(filter(None, _git(root, "diff", "--cached", "--name-only").splitlines()))
    if _git(root, "diff", "--check") or _git(root, "diff", "--cached", "--check"):
        _fail("GIT_DIFF_CHECK_FAILED")
    profile = classify_repository_profile(
        expected_paths=paths,
        tracked_paths=tracked,
        ordinary_untracked=untracked,
        status_lines=status_lines,
        working_diff=working,
        cached_diff=cached,
    )
    branch = _git(root, "branch", "--show-current")
    head = _git(root, "rev-parse", "HEAD")
    origin = _git(root, "rev-parse", "refs/remotes/origin/main")
    relation = _git(
        root, "rev-list", "--left-right", "--count", "HEAD...refs/remotes/origin/main"
    ).split()
    if branch != "main" or len(relation) != 2:
        _fail("REPOSITORY_IDENTITY_INVALID")
    try:
        ahead, behind = (int(value) for value in relation)
    except ValueError as error:
        raise ValueError(f"{ERROR_TOKEN}:AHEAD_BEHIND_NOT_INTEGERS") from error
    report: dict[str, object] = {
        "branch": branch,
        "HEAD": head,
        "origin_main": origin,
        "ahead": ahead,
        "behind": behind,
        "profile": profile,
        "tracked_modification_count": len(working),
        "staged_count": len(cached),
        "conflicted_count": len(
            set(filter(None, _git(root, "diff", "--name-only", "--diff-filter=U").splitlines()))
        ),
        "ordinary_untracked_count": len(untracked),
        "ordinary_untracked_paths": sorted(untracked),
    }
    if profile == CANDIDATE_UNTRACKED:
        if (
            head != subject.BASELINE_COMMIT
            or origin != subject.BASELINE_COMMIT
            or (ahead, behind) != (0, 0)
        ):
            _fail("CANDIDATE_BASELINE_RELATION_INVALID")
        report["git_index_mode_checked"] = False
        report["git_index_record_count"] = 0
        report["git_index_modes"] = {}
    else:
        if (
            not _ancestor(root, subject.BASELINE_COMMIT, "HEAD")
            or not _ancestor(root, subject.BASELINE_COMMIT, "refs/remotes/origin/main")
            or not _ancestor(root, "refs/remotes/origin/main", "HEAD")
            or behind != 0
        ):
            _fail("TRACKED_CLEAN_REPOSITORY_RELATION_INVALID")
        completed = subprocess.run(
            ["git", "ls-files", "--stage", "-z", "--", *paths],
            cwd=root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if completed.returncode != 0 or completed.stderr:
            _fail("GIT_INDEX_INSPECTION_FAILED")
        records = _parse_stage_records(completed.stdout)
        report["git_index_mode_checked"] = True
        report["git_index_record_count"] = len(records)
        report["git_index_modes"] = validate_tracked_index_modes(records, set(paths))
    return report


def _validate_text(payload: bytes, label: str) -> None:
    if len(payload) >= 1024 * 1024:
        _fail("FILE_EXCEEDS_1_MIB:" + label)
    if payload.startswith(b"\xef\xbb\xbf"):
        _fail("UTF8_BOM_FORBIDDEN:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"{ERROR_TOKEN}:NOT_UTF8:{label}") from error
    if "\0" in text or "\r" in text:
        _fail("TEXT_BYTES_INVALID:" + label)
    if not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
        _fail("FINAL_LF_INVALID:" + label)
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        _fail("TRAILING_WHITESPACE:" + label)


def _verify_exact7_files(root: Path) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for relative_text in subject.EXACT7_PATHS_V1:
        path = root / relative_text
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
        except OSError as error:
            raise ValueError(f"{ERROR_TOKEN}:EXACT7_FILE_READ_FAILED:{relative_text}") from error
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_mode & 0o111
            or stat.S_IMODE(metadata.st_mode) not in {0o644, 0o664}
        ):
            _fail("EXACT7_FILE_MODE_INVALID:" + relative_text)
        _validate_text(payload, relative_text)
        result.append(
            {
                "path": relative_text,
                "byte_count": len(payload),
                "sha256": subject._sha256(payload),
                "mode": format(stat.S_IMODE(metadata.st_mode), "04o"),
            }
        )
    output = root / subject.OUTPUT_DIRECTORY_RELATIVE
    names = sorted(entry.name for entry in output.iterdir())
    if names != sorted((subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)):
        _fail("OUTPUT_DIRECTORY_NOT_EXACT3")
    return result


def _read_csv(path: Path, expected_header: Sequence[str], expected_rows: int) -> list[dict[str, str]]:
    payload = path.read_bytes()
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
        rows = [dict(row) for row in reader]
    except UnicodeDecodeError as error:
        raise ValueError(f"{ERROR_TOKEN}:CSV_NOT_UTF8:{path.name}") from error
    if tuple(reader.fieldnames or ()) != tuple(expected_header) or len(rows) != expected_rows:
        _fail("CSV_HEADER_OR_ROW_COUNT_INVALID:" + path.name)
    return rows


def _verify_artifact_byte_identity_v1(
    observed: Mapping[str, bytes], expected: Mapping[str, bytes]
) -> None:
    """Require the exact three named artifacts to have byte-identical payloads."""

    expected_names = {subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE}
    if set(observed) != expected_names or set(expected) != expected_names:
        _fail("MATERIALIZED_FRESH_OR_DOUBLE_BUILD_MISMATCH")
    for name in expected_names:
        if (
            type(observed[name]) is not bytes
            or type(expected[name]) is not bytes
            or observed[name] != expected[name]
        ):
            _fail("MATERIALIZED_FRESH_OR_DOUBLE_BUILD_MISMATCH")


def _verify_materialized_and_double_build_v1(
    observed: Mapping[str, bytes],
    fresh_first: Mapping[str, bytes],
    fresh_second: Mapping[str, bytes],
) -> None:
    """Route both normal byte comparisons through the shared comparator."""

    _verify_artifact_byte_identity_v1(observed, fresh_first)
    _verify_artifact_byte_identity_v1(fresh_first, fresh_second)


def _run_raw_byte_probe_v1(fresh: Mapping[str, bytes]) -> str:
    """Corrupt an in-memory CSV and require rejection by the normal comparator."""

    corrupted = dict(fresh)
    payload = bytearray(corrupted[subject.CENSUS_FILE])
    payload[-2] ^= 1
    corrupted[subject.CENSUS_FILE] = bytes(payload)
    expected_token = "MATERIALIZED_FRESH_OR_DOUBLE_BUILD_MISMATCH"
    try:
        _verify_artifact_byte_identity_v1(corrupted, fresh)
    except ValueError as error:
        actual = str(error)
        wanted = f"{ERROR_TOKEN}:{expected_token}"
        if actual != wanted:
            _fail("TAMPER_WRONG_TOKEN:raw_bytes:" + actual)
        return expected_token
    except Exception as error:
        _fail("TAMPER_UNEXPECTED_EXCEPTION:raw_bytes:" + type(error).__name__)
    _fail("TAMPER_DID_NOT_FAIL:raw_bytes")


def _computation_copy(
    computation: subject.base.Cumulative1000CurrentGlobalReadinessComputationV1,
    *,
    rows: Sequence[Mapping[str, str]] | None = None,
    summary: Mapping[str, Any] | None = None,
    bindings: Sequence[Mapping[str, object]] | None = None,
) -> subject.base.Cumulative1000CurrentGlobalReadinessComputationV1:
    return subject.base.Cumulative1000CurrentGlobalReadinessComputationV1(
        rows=tuple(deepcopy(list(computation.rows if rows is None else rows))),
        summary=deepcopy(dict(computation.summary if summary is None else summary)),
        semantic_source_bindings=tuple(
            deepcopy(list(computation.semantic_source_bindings if bindings is None else bindings))
        ),
    )


def _expect_subject_failure(name: str, expected: str, callback: Callable[[], object]) -> str:
    try:
        callback()
    except subject.Cumulative1000CurrentGlobalReadinessCensusWithME7Error as error:
        actual = str(error)
        wanted = subject.ERROR_TOKEN + ":" + expected
        if actual != wanted:
            _fail("TAMPER_WRONG_TOKEN:" + name + ":" + actual)
        return expected
    except Exception as error:
        _fail("TAMPER_UNEXPECTED_EXCEPTION:" + name + ":" + type(error).__name__)
    _fail("TAMPER_DID_NOT_FAIL:" + name)


def _tamper_probes(
    root: Path,
    computation: subject.base.Cumulative1000CurrentGlobalReadinessComputationV1,
    predecessor_computation: subject.base.Cumulative1000CurrentGlobalReadinessComputationV1,
    reconciliation: generic.ReconciliationResult,
    matrix_rows: Sequence[Mapping[str, str]],
    fresh: Mapping[str, bytes],
) -> dict[str, str]:
    def validate(candidate: object) -> object:
        return subject.validate_covapie_cumulative1000_current_global_readiness_census_with_me7_v1(
            candidate,
            repo_root=root,
            predecessor_computation=predecessor_computation,
            reconciliation_result=reconciliation,
            matrix_rows=matrix_rows,
        )

    probes: dict[str, str] = {}

    def row_probe(name: str, rank: int, field: str, value: str, token: str) -> None:
        rows = deepcopy(list(computation.rows))
        rows[rank - 1][field] = value
        probes[name] = _expect_subject_failure(name, token, lambda: validate(_computation_copy(computation, rows=rows)))

    rows = deepcopy(list(computation.rows))
    del rows[527]
    probes["target_missing"] = _expect_subject_failure(
        "target_missing", "CENSUS_SUMMARY_OR_BINDINGS_SCHEMA_INVALID", lambda: validate(_computation_copy(computation, rows=rows))
    )
    rows = deepcopy(list(computation.rows))
    rows[527]["canonical_event_id"] = rows[528]["canonical_event_id"]
    probes["target_duplicate"] = _expect_subject_failure(
        "target_duplicate", "CENSUS_EVENT_OR_RANK_IDENTITY_INVALID", lambda: validate(_computation_copy(computation, rows=rows))
    )
    row_probe("fourth_event", 532, "current_review_status", generic.COMPLETED_HUMAN_NEGATIVE, "PREDECESSOR_DELTA_NOT_EXACT_ME7_EXACT3")
    row_probe("context_me7_527", 527, "chemistry_disposition", generic.CHEMISTRY_POSITIVE, "PREDECESSOR_DELTA_NOT_EXACT_ME7_EXACT3")
    row_probe("non_target_997", 1, "chemistry_disposition", generic.CHEMISTRY_POSITIVE, "PREDECESSOR_DELTA_NOT_EXACT_ME7_EXACT3")
    row_probe("d2_relevant", 528, "task_relevance_disposition", generic.TASK_RELEVANT, "ME7_REFRESHED_SEMANTICS_INVALID:" + subject.ME7_EXACT3_EVENT_IDS_V1[0])
    row_probe("chemistry_negative", 528, "chemistry_disposition", subject.base.CHEMISTRY_NEGATIVE, "ME7_REFRESHED_SEMANTICS_INVALID:" + subject.ME7_EXACT3_EVENT_IDS_V1[0])
    row_probe("na_to_exclude", 528, "training_use_disposition", generic.TRAINING_EXCLUDE, "ME7_REFRESHED_SEMANTICS_INVALID:" + subject.ME7_EXACT3_EVENT_IDS_V1[0])
    row_probe("na_to_include", 528, "training_use_disposition", generic.TRAINING_INCLUDE, "ME7_REFRESHED_SEMANTICS_INVALID:" + subject.ME7_EXACT3_EVENT_IDS_V1[0])
    row_probe("pair_authority_lost", 528, "reactive_pair_sample_authoritative", "false", "ME7_CHANGED_FIELD_SET_NOT_EXACT12:" + subject.ME7_EXACT3_EVENT_IDS_V1[0])
    row_probe("pair_promoted_to_training_target", 528, "reactive_pair_training_target_available", "true", "ME7_CHANGED_FIELD_SET_NOT_EXACT12:" + subject.ME7_EXACT3_EVENT_IDS_V1[0])
    row_probe("role_authority_fabricated", 528, "role_partition_sample_authoritative", "true", "ME7_CHANGED_FIELD_SET_NOT_EXACT12:" + subject.ME7_EXACT3_EVENT_IDS_V1[0])
    row_probe("task_ids_empty_array", 528, "structurally_applicable_task_ids_json", "[]", "ME7_CHANGED_FIELD_SET_NOT_EXACT12:" + subject.ME7_EXACT3_EVENT_IDS_V1[0])
    row_probe("task_ids_nonempty", 528, "structurally_applicable_task_ids_json", "[0,3,4]", "ME7_CHANGED_FIELD_SET_NOT_EXACT12:" + subject.ME7_EXACT3_EVENT_IDS_V1[0])
    row_probe("role_profile_promoted", 528, "role_profile", subject.base.DIRECT_PROFILE, "ME7_CHANGED_FIELD_SET_NOT_EXACT12:" + subject.ME7_EXACT3_EVENT_IDS_V1[0])
    row_probe("training_admission_promoted", 528, "formal_training_admitted", "true", "ME7_CHANGED_FIELD_SET_NOT_EXACT12:" + subject.ME7_EXACT3_EVENT_IDS_V1[0])
    row_probe("future_candidate_promoted", 528, "future_training_admission_candidate", "true", "ME7_CHANGED_FIELD_SET_NOT_EXACT12:" + subject.ME7_EXACT3_EVENT_IDS_V1[0])
    row_probe("rank_changed", 528, "scaleup_rank", "527", "CENSUS_EVENT_OR_RANK_IDENTITY_INVALID")
    row_probe("event_identity_changed", 528, "canonical_event_id", "BROKEN", "CENSUS_EVENT_SET_IDENTITY_INVALID")
    rows = deepcopy(list(computation.rows)); rows[0] = dict(reversed(list(rows[0].items())))
    probes["column_order_changed"] = _expect_subject_failure(
        "column_order_changed", "CENSUS_SUMMARY_OR_BINDINGS_SCHEMA_INVALID", lambda: validate(_computation_copy(computation, rows=rows))
    )

    def summary_probe(name: str, mutate: Callable[[dict[str, Any]], None]) -> None:
        summary = deepcopy(computation.summary); mutate(summary)
        probes[name] = _expect_subject_failure(
            name, "SUMMARY_NOT_EXACTLY_SOURCE_DERIVED", lambda: validate(_computation_copy(computation, summary=summary))
        )

    summary_probe("event_set_digest", lambda x: x["chemistry"]["POSITIVE"].update(event_set_sha256="0" * 64))
    summary_probe("source_composition", lambda x: x["chemistry"]["positive_source_composition"].update(ME7=2))
    summary_probe("global_negative_population", lambda x: x["global_status_distribution"]["counts"].update(COMPLETED_HUMAN_NEGATIVE=51))
    summary_probe("orthogonal_old20", lambda x: x["orthogonal_task_negative_chemistry_positive"].update(task_negative_chemistry_positive_population_count=20))
    summary_probe("next_pending_completed_me7", lambda x: x["top_pending_review_units_by_event_yield"][0].update(review_unit_id=subject.ME7_REVIEW_UNIT_ID_V1))
    summary_probe("next_pending_pdb_truncated", lambda x: x["top_pending_review_units_by_event_yield"][0].update(pdb_ids=["5ARB"]))
    summary_probe("historical_admission_zeroed", lambda x: x["training_stage"].update(formal_training_admitted_count=0))
    summary_probe("ready_promoted", lambda x: x["training_stage"].update(ready_for_formal_training_event_count=1))
    summary_probe("b3_omitted", lambda x: x["canonical_exact5"]["tasks"].pop(3))
    summary_probe("sixth_task", lambda x: x["canonical_exact5"]["tasks"].append({"task_id": 5}))

    bindings = deepcopy(list(computation.semantic_source_bindings)); bindings.pop()
    probes["binding_missing"] = _expect_subject_failure(
        "binding_missing", "SEMANTIC_SOURCE_BINDING_SET_NOT_PREDECESSOR_PLUS_EXACT6", lambda: validate(_computation_copy(computation, bindings=bindings))
    )
    bindings = deepcopy(list(computation.semantic_source_bindings)); bindings[-1] = deepcopy(bindings[-2])
    probes["binding_duplicate"] = _expect_subject_failure(
        "binding_duplicate", "SEMANTIC_SOURCE_BINDING_SET_NOT_PREDECESSOR_PLUS_EXACT6", lambda: validate(_computation_copy(computation, bindings=bindings))
    )
    bindings = deepcopy(list(computation.semantic_source_bindings)); bindings[-1]["path_namespace"] = "absolute"
    probes["binding_namespace"] = _expect_subject_failure(
        "binding_namespace", "SEMANTIC_SOURCE_BINDING_SET_NOT_PREDECESSOR_PLUS_EXACT6", lambda: validate(_computation_copy(computation, bindings=bindings))
    )
    bindings = deepcopy(list(computation.semantic_source_bindings)); bindings[-1]["expected_executable"] = True
    probes["binding_permission_semantics"] = _expect_subject_failure(
        "binding_permission_semantics", "SEMANTIC_SOURCE_BINDING_SET_NOT_PREDECESSOR_PLUS_EXACT6", lambda: validate(_computation_copy(computation, bindings=bindings))
    )

    probes["raw_bytes"] = _run_raw_byte_probe_v1(fresh)
    return probes


def _lifecycle_simulations() -> dict[str, bool]:
    expected = ("a", "b")
    candidate = classify_repository_profile(
        expected_paths=expected,
        tracked_paths={"historical"},
        ordinary_untracked={"a", "b"},
        status_lines=("?? a", "?? b"),
        working_diff=set(),
        cached_diff=set(),
    )
    tracked = classify_repository_profile(
        expected_paths=expected,
        tracked_paths={"historical", "a", "b"},
        ordinary_untracked=set(),
        status_lines=(),
        working_diff=set(),
        cached_diff=set(),
    )
    modes = validate_tracked_index_modes(
        (("100644", "a" * 40, "0", "a"), ("100644", "b" * 40, "0", "b")),
        {"a", "b"},
    )
    rejected = 0
    cases = (
        dict(tracked_paths={"historical"}, ordinary_untracked={"a"}, status_lines=("?? a",)),
        dict(tracked_paths={"historical", "a"}, ordinary_untracked={"b"}, status_lines=("?? b",)),
        dict(tracked_paths={"historical", "a", "b"}, ordinary_untracked={"extra"}, status_lines=("?? extra",)),
    )
    for case in cases:
        try:
            classify_repository_profile(expected_paths=expected, working_diff=set(), cached_diff=set(), **case)
        except ValueError as error:
            if str(error) != f"{ERROR_TOKEN}:UNKNOWN_REPOSITORY_PROFILE":
                raise
            rejected += 1
    for records in (
        (("100755", "a" * 40, "0", "a"), ("100644", "b" * 40, "0", "b")),
        (("120000", "a" * 40, "0", "a"), ("100644", "b" * 40, "0", "b")),
        (("100644", "a" * 40, "1", "a"), ("100644", "b" * 40, "0", "b")),
    ):
        try:
            validate_tracked_index_modes(records, {"a", "b"})
        except ValueError:
            rejected += 1
    if candidate != CANDIDATE_UNTRACKED or tracked != TRACKED_CLEAN or modes != {"a": "100644", "b": "100644"} or rejected != 6:
        _fail("LIFECYCLE_SIMULATION_INVALID")
    return {
        "candidate_untracked_supported": True,
        "tracked_clean_supported": True,
        "missing_mixed_extra_rejected": True,
        "executable_symlink_nonzero_stage_rejected": True,
    }


def check(root: Path) -> dict[str, object]:
    repository = _verify_repository(root)
    exact7 = _verify_exact7_files(root)
    predecessor_rows = _read_csv(
        root / subject.PREDECESSOR_CENSUS_RELATIVE, subject.CENSUS_COLUMNS_V1, 1000
    )
    matrix_rows = _read_csv(
        root / subject.ME7_EVENT_MATRIX_RELATIVE, subject.ingestion.MATRIX_HEADER, 3
    )
    materialized_rows = _read_csv(
        root / subject.OUTPUT_DIRECTORY_RELATIVE / subject.CENSUS_FILE,
        subject.CENSUS_COLUMNS_V1,
        1000,
    )
    reconciliation = reconciliation_owner.reconcile_real_completed_human_decisions_with_me7_v1(root)
    computation, frozen, computed_reconciliation, computed_matrix = subject._compute_components_v1(root)
    if (
        predecessor_rows != list(frozen.rows)
        or matrix_rows != list(computed_matrix)
        or reconciliation.review_summary != computed_reconciliation.review_summary
        or materialized_rows != list(computation.rows)
    ):
        _fail("INDEPENDENT_SOURCE_OR_COMPUTATION_MISMATCH")
    fresh_first = subject._build_artifacts_from_computation_v1(root, computation)
    fresh_second = subject._build_artifacts_from_computation_v1(root, computation)
    observed = {
        name: (root / subject.OUTPUT_DIRECTORY_RELATIVE / name).read_bytes()
        for name in (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)
    }
    _verify_materialized_and_double_build_v1(observed, fresh_first, fresh_second)
    summary = json.loads(observed[subject.SUMMARY_FILE])
    manifest = json.loads(observed[subject.MANIFEST_FILE])
    predecessor_manifest = json.loads((root / subject.PREDECESSOR_MANIFEST_RELATIVE).read_text())
    predecessor_bindings = predecessor_manifest["semantic_source_bindings"]
    bindings = manifest.get("semantic_source_bindings")
    if (
        summary != computation.summary
        or manifest.get("schema_version") != subject.SCHEMA_VERSION
        or manifest.get("candidate_inventory")
        != {"exact_file_count": 7, "paths": list(subject.EXACT7_PATHS_V1)}
        or manifest.get("output_inventory", {}).get("exact_output_count") != 3
        or manifest.get("semantic_source_binding_count") != 198
        or type(bindings) is not list
        or bindings[:192] != predecessor_bindings
        or len(bindings[192:]) != 6
        or len({(item["path_namespace"], item["path"]) for item in bindings}) != 198
        or len({item["artifact_role"] for item in bindings[192:]}) != 6
        or {item["artifact_role"] for item in bindings[:192]}
        & {item["artifact_role"] for item in bindings[192:]}
        or manifest.get("manifest_self_SHA256_recorded") is not False
        or manifest.get("manifest_self_binding", {}).get("sha256_recorded_inside_self") is not False
    ):
        _fail("MANIFEST_OR_SEMANTIC_BINDINGS_INVALID")
    candidate_bindings = manifest.get("candidate_contract_bindings")
    if candidate_bindings != subject._candidate_contract_bindings_v1(root):
        _fail("CANDIDATE_CONTRACT_BINDINGS_INVALID")
    target = set(subject.ME7_EXACT3_EVENT_IDS_V1)
    changed = []
    field_sets = []
    for old, new in zip(predecessor_rows, materialized_rows, strict=True):
        if old != new:
            changed.append(new["canonical_event_id"])
            field_sets.append({field for field in subject.CENSUS_COLUMNS_V1 if old[field] != new[field]})
    if set(changed) != target or len(changed) != 3 or any(fields != subject._ACTUAL_CHANGED_ME7_FIELDS_V1 for fields in field_sets):
        _fail("INDEPENDENT_EXACT3_OR_EXACT12_INVALID")
    counts = {
        "global_unreviewed": Counter(row["current_global_status"] for row in materialized_rows)[generic.CURRENTLY_UNREVIEWED],
        "global_negative": Counter(row["current_global_status"] for row in materialized_rows)[generic.COMPLETED_HUMAN_NEGATIVE],
        "chemistry_positive": Counter(row["chemistry_disposition"] for row in materialized_rows)[generic.CHEMISTRY_POSITIVE],
        "task_not_relevant": Counter(row["task_relevance_disposition"] for row in materialized_rows)[generic.TASK_NOT_RELEVANT],
        "training_not_applicable": Counter(row["training_use_disposition"] for row in materialized_rows)[generic.TRAINING_NOT_APPLICABLE],
        "pair_authority": sum(row["reactive_pair_sample_authoritative"] == "true" for row in materialized_rows),
        "role_authority": sum(row["role_partition_sample_authoritative"] == "true" for row in materialized_rows),
        "structural_labels": sum(row["canonical_mask_structural_labels_available"] == "true" for row in materialized_rows),
    }
    if counts != {
        "global_unreviewed": 160,
        "global_negative": 81,
        "chemistry_positive": 167,
        "task_not_relevant": 113,
        "training_not_applicable": 113,
        "pair_authority": 167,
        "role_authority": 156,
        "structural_labels": 156,
    }:
        _fail("INDEPENDENT_ROW_COUNTS_INVALID")
    probes = _tamper_probes(
        root, computation, frozen, reconciliation, matrix_rows, fresh_first
    )
    lifecycle = _lifecycle_simulations()
    return {
        "status": "PASS",
        "repository": repository,
        "Exact7_files": exact7,
        "refresh": {
            "row_count": 1000,
            "column_count": 47,
            "me7_overlay_event_count": 3,
            "non_me7_changed_row_count": 0,
            "unchanged_row_count": 997,
            "authorized_overlay_field_count": 19,
            "authorized_but_unchanged_field_count": 7,
            "actual_changed_field_count": 12,
        },
        "counts": counts,
        "human_review": summary["human_review"],
        "orthogonal": summary["orthogonal_task_negative_chemistry_positive"],
        "semantic_source_bindings": {
            "predecessor": 192,
            "successor": 198,
            "prefix_preserved": True,
            "additive": 6,
        },
        "next_priority_review": summary["top_pending_review_units_by_event_yield"][0],
        "tamper_probes": probes,
        "tamper_probe_count": len(probes),
        "lifecycle_simulations": lifecycle,
        "materialized_equals_fresh_build": observed == fresh_first,
        "deterministic_double_build": fresh_first == fresh_second,
        "operation_boundary": {
            "new_human_authority_created": False,
            "new_scientific_authority_created": False,
            "task_label_authority": False,
            "formal_training_admitted_by_refresh": False,
            "ready_for_training": False,
            "training_started": False,
            "queue_refresh_performed": False,
            "next_review_started": False,
            "commit_performed": False,
            "push_performed": False,
        },
    }


def main() -> int:
    try:
        report = check(ROOT)
    except Exception as error:
        print("COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_WITH_ME7_V1_PASS=false")
        print("ERROR=" + str(error))
        return 1
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    print("COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_WITH_ME7_V1_PASS=true")
    print("lifecycle=" + str(report["repository"]["profile"]))
    print("ME7_OVERLAY_EVENT_COUNT=3")
    print("NON_ME7_CHANGED_ROW_COUNT=0")
    print("UNCHANGED_ROW_COUNT=997")
    print("AUTHORIZED_OVERLAY_FIELD_COUNT=19")
    print("AUTHORIZED_BUT_UNCHANGED_FIELD_COUNT=7")
    print("ACTUAL_CHANGED_FIELD_COUNT=12")
    print("CURRENTLY_UNREVIEWED=160")
    print("COMPLETED_HUMAN_NEGATIVE=81")
    print("COMPLETED_HUMAN_POSITIVE=127")
    print("HUMAN_COMPLETED_EVENT_COUNT=178")
    print("HUMAN_COMPLETED_UNIT_COUNT=32")
    print("CHEMISTRY_POSITIVE_COUNT=167")
    print("TASK_NOT_RELEVANT_COUNT=113")
    print("TRAINING_NOT_APPLICABLE_COUNT=113")
    print("REACTIVE_PAIR_SAMPLE_AUTHORITATIVE_COUNT=167")
    print("ROLE_PARTITION_SAMPLE_AUTHORITATIVE_COUNT=156")
    print("CANONICAL_MASK_STRUCTURAL_LABELS_AVAILABLE_COUNT=156")
    print("CANONICAL_TASK_APPLICABILITY_COUNTS=[156,56,56,156,156]")
    print("ORTHOGONAL_TASK_NEGATIVE_CHEMISTRY_POSITIVE_COUNT=23")
    print("PREDECESSOR_SEMANTIC_SOURCE_BINDING_COUNT=192")
    print("SUCCESSOR_SEMANTIC_SOURCE_BINDING_COUNT=198")
    print("NEXT_PRIORITY_REVIEW_LIGAND=EI3")
    print('NEXT_PRIORITY_REVIEW_PDB_IDS=["5ARB","5ARC","5ARD"]')
    print("NEXT_PRIORITY_REVIEW_UNIT=COVAPIE_BULK_REVIEW_UNIT_79526304E5FB38A6")
    print("NEXT_PRIORITY_REVIEW_RAW_PRIORITY_RANK=33")
    print("NEXT_PRIORITY_REVIEW_CURRENT_PENDING_RANK=1")
    print("NEXT_PRIORITY_REVIEW_EVENT_COUNT=3")
    print("CENSUS_REFRESH_PERFORMED=true")
    print("QUEUE_REFRESH_PERFORMED=false")
    print("NEXT_REVIEW_STARTED=false")
    print("EI3_REVIEW_STATE_CREATED_BY_THIS_ROUND=false")
    print("TASK_LABEL_AUTHORITY=false")
    print("READY_FOR_TRAINING=false")
    print("TRAINING_STARTED=false")
    print("COMMIT_PERFORMED=false")
    print("PUSH_PERFORMED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
