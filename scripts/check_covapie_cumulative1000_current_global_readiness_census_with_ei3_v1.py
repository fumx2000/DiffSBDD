#!/usr/bin/env python3
"""Independent fail-closed checker for the with-EI3 cumulative1000 census."""

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
    covapie_completed_human_decision_reconciliation_with_ei3_v1 as reconciliation_owner,
)
from covalent_ext import (  # noqa: E402
    covapie_cumulative1000_current_global_readiness_census_with_ei3_v1 as subject,
)


ERROR_TOKEN = "COVAPIE_WITH_EI3_CENSUS_CHECK_ERROR"
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


def _validate_semantic_artifacts_v1(
    artifacts: Mapping[str, bytes],
    *,
    root: Path,
    predecessor_computation: subject.base.Cumulative1000CurrentGlobalReadinessComputationV1,
    reconciliation: generic.ReconciliationResult,
    matrix_rows: Sequence[Mapping[str, str]],
) -> bool:
    """Validate artifact semantics after their manifest bindings have been checked."""

    expected_names = {subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE}
    if set(artifacts) != expected_names or any(type(value) is not bytes for value in artifacts.values()):
        _fail("SEMANTIC_ARTIFACT_INVENTORY_INVALID")
    try:
        reader = csv.DictReader(
            io.StringIO(artifacts[subject.CENSUS_FILE].decode("utf-8"), newline="")
        )
        rows = tuple(dict(row) for row in reader)
        summary = json.loads(artifacts[subject.SUMMARY_FILE])
        manifest = json.loads(artifacts[subject.MANIFEST_FILE])
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{ERROR_TOKEN}:SEMANTIC_ARTIFACT_PARSE_INVALID") from error
    if tuple(reader.fieldnames or ()) != subject.CENSUS_COLUMNS_V1 or len(rows) != 1000:
        _fail("SEMANTIC_CENSUS_SCHEMA_INVALID")
    expected_outputs = [
        {
            "artifact_role": "REFRESHED_CENSUS_CSV",
            "path": (subject.OUTPUT_DIRECTORY_RELATIVE / subject.CENSUS_FILE).as_posix(),
            "byte_count": len(artifacts[subject.CENSUS_FILE]),
            "sha256": subject._sha256(artifacts[subject.CENSUS_FILE]),
        },
        {
            "artifact_role": "REFRESHED_SUMMARY_JSON",
            "path": (subject.OUTPUT_DIRECTORY_RELATIVE / subject.SUMMARY_FILE).as_posix(),
            "byte_count": len(artifacts[subject.SUMMARY_FILE]),
            "sha256": subject._sha256(artifacts[subject.SUMMARY_FILE]),
        },
    ]
    if manifest.get("output_bindings_excluding_manifest_self") != expected_outputs:
        _fail("SEMANTIC_ARTIFACT_OUTPUT_BINDING_INVALID")
    self_binding = manifest.get("manifest_self_binding")
    if (
        type(self_binding) is not dict
        or self_binding.get("sha256_recorded_inside_self") is not False
        or "sha256" in self_binding
        or manifest.get("manifest_self_SHA256_recorded") is not False
    ):
        _fail("MANIFEST_SELF_REFERENCE_FORBIDDEN")
    bindings = manifest.get("semantic_source_bindings")
    if type(bindings) is not list:
        _fail("SEMANTIC_SOURCE_BINDINGS_NOT_LIST")
    computation = subject.base.Cumulative1000CurrentGlobalReadinessComputationV1(
        rows=rows,
        summary=summary,
        semantic_source_bindings=tuple(bindings),
    )
    return subject.validate_covapie_cumulative1000_current_global_readiness_census_with_ei3_v1(
        computation,
        repo_root=root,
        predecessor_computation=predecessor_computation,
        reconciliation_result=reconciliation,
        matrix_rows=matrix_rows,
    )


def _expect_subject_failure(name: str, expected: str, callback: Callable[[], object]) -> str:
    try:
        callback()
    except subject.Cumulative1000CurrentGlobalReadinessCensusWithEI3Error as error:
        actual = str(error)
        wanted = subject.ERROR_TOKEN + ":" + expected
        if actual != wanted:
            _fail("TAMPER_WRONG_TOKEN:" + name + ":" + actual)
        return expected
    except Exception as error:
        _fail("TAMPER_UNEXPECTED_EXCEPTION:" + name + ":" + type(error).__name__)
    _fail("TAMPER_DID_NOT_FAIL:" + name)


def _expect_checker_failure(name: str, expected: str, callback: Callable[[], object]) -> str:
    try:
        callback()
    except ValueError as error:
        actual = str(error)
        wanted = ERROR_TOKEN + ":" + expected
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
        return subject.validate_covapie_cumulative1000_current_global_readiness_census_with_ei3_v1(
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
    del rows[966]
    probes["target_missing"] = _expect_subject_failure(
        "target_missing", "CENSUS_SUMMARY_OR_BINDINGS_SCHEMA_INVALID", lambda: validate(_computation_copy(computation, rows=rows))
    )
    rows = deepcopy(list(computation.rows))
    rows[966]["canonical_event_id"] = rows[967]["canonical_event_id"]
    probes["target_duplicate"] = _expect_subject_failure(
        "target_duplicate", "CENSUS_EVENT_OR_RANK_IDENTITY_INVALID", lambda: validate(_computation_copy(computation, rows=rows))
    )
    row_probe("fourth_event", 970, "current_review_status", generic.COMPLETED_HUMAN_NEGATIVE, "PREDECESSOR_DELTA_NOT_EXACT_EI3_EXACT3")
    row_probe("non_target_997", 1, "chemistry_disposition", generic.CHEMISTRY_POSITIVE, "PREDECESSOR_DELTA_NOT_EXACT_EI3_EXACT3")
    row_probe("d2_relevant", 967, "task_relevance_disposition", generic.TASK_RELEVANT, "EI3_REFRESHED_SEMANTICS_INVALID:" + subject.EI3_EXACT3_EVENT_IDS_V1[0])
    row_probe("chemistry_negative", 967, "chemistry_disposition", subject.base.CHEMISTRY_NEGATIVE, "EI3_REFRESHED_SEMANTICS_INVALID:" + subject.EI3_EXACT3_EVENT_IDS_V1[0])
    row_probe("na_to_exclude", 967, "training_use_disposition", generic.TRAINING_EXCLUDE, "EI3_REFRESHED_SEMANTICS_INVALID:" + subject.EI3_EXACT3_EVENT_IDS_V1[0])
    row_probe("na_to_include", 967, "training_use_disposition", generic.TRAINING_INCLUDE, "EI3_REFRESHED_SEMANTICS_INVALID:" + subject.EI3_EXACT3_EVENT_IDS_V1[0])
    row_probe("pair_authority_lost", 967, "reactive_pair_sample_authoritative", "false", "EI3_CHANGED_FIELD_SET_NOT_EXACT12:" + subject.EI3_EXACT3_EVENT_IDS_V1[0])
    row_probe("pair_promoted_to_training_target", 967, "reactive_pair_training_target_available", "true", "EI3_CHANGED_FIELD_SET_NOT_EXACT12:" + subject.EI3_EXACT3_EVENT_IDS_V1[0])
    row_probe("role_authority_fabricated", 967, "role_partition_sample_authoritative", "true", "EI3_CHANGED_FIELD_SET_NOT_EXACT12:" + subject.EI3_EXACT3_EVENT_IDS_V1[0])
    row_probe("task_ids_empty_array", 967, "structurally_applicable_task_ids_json", "[]", "EI3_CHANGED_FIELD_SET_NOT_EXACT12:" + subject.EI3_EXACT3_EVENT_IDS_V1[0])
    row_probe("task_ids_nonempty", 967, "structurally_applicable_task_ids_json", "[0,3,4]", "EI3_CHANGED_FIELD_SET_NOT_EXACT12:" + subject.EI3_EXACT3_EVENT_IDS_V1[0])
    row_probe("role_profile_promoted", 967, "role_profile", subject.base.DIRECT_PROFILE, "EI3_CHANGED_FIELD_SET_NOT_EXACT12:" + subject.EI3_EXACT3_EVENT_IDS_V1[0])
    row_probe("training_admission_promoted", 967, "formal_training_admitted", "true", "EI3_CHANGED_FIELD_SET_NOT_EXACT12:" + subject.EI3_EXACT3_EVENT_IDS_V1[0])
    row_probe("future_candidate_promoted", 967, "future_training_admission_candidate", "true", "EI3_CHANGED_FIELD_SET_NOT_EXACT12:" + subject.EI3_EXACT3_EVENT_IDS_V1[0])
    row_probe("rank_changed", 967, "scaleup_rank", "966", "CENSUS_EVENT_OR_RANK_IDENTITY_INVALID")
    row_probe("event_identity_changed", 967, "canonical_event_id", "BROKEN", "CENSUS_EVENT_SET_IDENTITY_INVALID")
    rows = deepcopy(list(computation.rows)); rows[0] = dict(reversed(list(rows[0].items())))
    probes["column_order_changed"] = _expect_subject_failure(
        "column_order_changed", "CENSUS_SUMMARY_OR_BINDINGS_SCHEMA_INVALID", lambda: validate(_computation_copy(computation, rows=rows))
    )

    def matrix_probe(
        name: str,
        mutate: Callable[[list[dict[str, str]]], None],
        token: str,
    ) -> None:
        candidate = deepcopy([dict(row) for row in matrix_rows])
        mutate(candidate)
        probes[name] = _expect_subject_failure(
            name, token, lambda: subject._validate_ei3_matrix_rows_v1(candidate)
        )

    matrix_probe(
        "matrix_79_columns",
        lambda rows: [
            (row.pop("target_covalent_connection_count"), row.pop("metal_context_connection_count"))
            for row in rows
        ],
        "EI3_EVENT_MATRIX_IDENTITY_NOT_EXACT3_X_81",
    )
    matrix_probe(
        "nullable_role_became_array",
        lambda rows: rows[0].update(role_profile_raw_json="[]"),
        "EI3_EVENT_MATRIX_SEMANTICS_INVALID:" + subject.EI3_EXACT3_EVENT_IDS_V1[0],
    )
    matrix_probe(
        "metal_context_became_covalent",
        lambda rows: rows[2].update(
            target_covalent_connection_count="3", metal_context_connection_count="0"
        ),
        "EI3_EVENT_MATRIX_SEMANTICS_INVALID:" + subject.EI3_EXACT3_EVENT_IDS_V1[2],
    )
    matrix_probe(
        "pre_hard_prerequisite_reversed",
        lambda rows: rows[0].update(
            accurate_PRE_required_before_training_feature_contract="true"
        ),
        "EI3_EVENT_MATRIX_SEMANTICS_INVALID:" + subject.EI3_EXACT3_EVENT_IDS_V1[0],
    )

    def summary_probe(name: str, mutate: Callable[[dict[str, Any]], None]) -> None:
        summary = deepcopy(computation.summary); mutate(summary)
        probes[name] = _expect_subject_failure(
            name, "SUMMARY_NOT_EXACTLY_SOURCE_DERIVED", lambda: validate(_computation_copy(computation, summary=summary))
        )

    summary_probe("event_set_digest", lambda x: x["chemistry"]["POSITIVE"].update(event_set_sha256="0" * 64))
    summary_probe("source_composition", lambda x: x["chemistry"]["positive_source_composition"].update(EI3=2))
    summary_probe("global_negative_population", lambda x: x["global_status_distribution"]["counts"].update(COMPLETED_HUMAN_NEGATIVE=81))
    summary_probe("orthogonal_old23", lambda x: x["orthogonal_task_negative_chemistry_positive"].update(task_negative_chemistry_positive_population_count=23))
    summary_probe("next_pending_completed_ei3", lambda x: x["top_pending_review_units_by_event_yield"][0].update(review_unit_id=subject.EI3_REVIEW_UNIT_ID_V1))
    summary_probe("next_pending_pdb_truncated", lambda x: x["top_pending_review_units_by_event_yield"][0].update(pdb_ids=["2A5I"]))
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
    bindings = deepcopy(list(computation.semantic_source_bindings)); bindings[0]["sha256"] = "0" * 64
    probes["binding_prefix_changed"] = _expect_subject_failure(
        "binding_prefix_changed", "SEMANTIC_SOURCE_BINDING_SET_NOT_PREDECESSOR_PLUS_EXACT6", lambda: validate(_computation_copy(computation, bindings=bindings))
    )
    bindings = deepcopy(list(computation.semantic_source_bindings)); bindings[-1]["artifact_role"] = bindings[-2]["artifact_role"]
    probes["binding_role_collision"] = _expect_subject_failure(
        "binding_role_collision", "SEMANTIC_SOURCE_BINDING_SET_NOT_PREDECESSOR_PLUS_EXACT6", lambda: validate(_computation_copy(computation, bindings=bindings))
    )

    def semantic_artifact_probe(
        name: str, rank: int, field: str, value: str, token: str
    ) -> None:
        artifacts = dict(fresh)
        reader = csv.DictReader(
            io.StringIO(artifacts[subject.CENSUS_FILE].decode("utf-8"), newline="")
        )
        rows = [dict(row) for row in reader]
        rows[rank - 1][field] = value
        artifacts[subject.CENSUS_FILE] = subject._csv_bytes(rows)
        manifest = json.loads(artifacts[subject.MANIFEST_FILE])
        census_binding = manifest["output_bindings_excluding_manifest_self"][0]
        census_binding["byte_count"] = len(artifacts[subject.CENSUS_FILE])
        census_binding["sha256"] = subject._sha256(artifacts[subject.CENSUS_FILE])
        artifacts[subject.MANIFEST_FILE] = subject._json_bytes(manifest)
        probes[name] = _expect_subject_failure(
            name,
            token,
            lambda: _validate_semantic_artifacts_v1(
                artifacts,
                root=root,
                predecessor_computation=predecessor_computation,
                reconciliation=reconciliation,
                matrix_rows=matrix_rows,
            ),
        )

    semantic_artifact_probe(
        "semantic_task_relevance_with_synced_manifest",
        967,
        "task_relevance_disposition",
        generic.TASK_RELEVANT,
        "EI3_REFRESHED_SEMANTICS_INVALID:" + subject.EI3_EXACT3_EVENT_IDS_V1[0],
    )
    semantic_artifact_probe(
        "semantic_chemistry_with_synced_manifest",
        967,
        "chemistry_disposition",
        subject.base.CHEMISTRY_NEGATIVE,
        "EI3_REFRESHED_SEMANTICS_INVALID:" + subject.EI3_EXACT3_EVENT_IDS_V1[0],
    )
    semantic_artifact_probe(
        "semantic_training_with_synced_manifest",
        967,
        "training_use_disposition",
        generic.TRAINING_EXCLUDE,
        "EI3_REFRESHED_SEMANTICS_INVALID:" + subject.EI3_EXACT3_EVENT_IDS_V1[0],
    )
    semantic_artifact_probe(
        "semantic_role_authority_with_synced_manifest",
        967,
        "role_partition_sample_authoritative",
        "true",
        "EI3_CHANGED_FIELD_SET_NOT_EXACT12:" + subject.EI3_EXACT3_EVENT_IDS_V1[0],
    )
    semantic_artifact_probe(
        "semantic_task_ids_with_synced_manifest",
        967,
        "structurally_applicable_task_ids_json",
        "[]",
        "EI3_CHANGED_FIELD_SET_NOT_EXACT12:" + subject.EI3_EXACT3_EVENT_IDS_V1[0],
    )
    semantic_artifact_probe(
        "semantic_non_target_with_synced_manifest",
        1,
        "current_review_status",
        "BROKEN",
        "PREDECESSOR_DELTA_NOT_EXACT_EI3_EXACT3",
    )
    self_referencing = dict(fresh)
    self_manifest = json.loads(self_referencing[subject.MANIFEST_FILE])
    self_manifest["manifest_self_binding"]["sha256"] = "0" * 64
    self_referencing[subject.MANIFEST_FILE] = subject._json_bytes(self_manifest)
    probes["manifest_self_reference"] = _expect_checker_failure(
        "manifest_self_reference",
        "MANIFEST_SELF_REFERENCE_FORBIDDEN",
        lambda: _validate_semantic_artifacts_v1(
            self_referencing,
            root=root,
            predecessor_computation=predecessor_computation,
            reconciliation=reconciliation,
            matrix_rows=matrix_rows,
        ),
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
        root / subject.EI3_EVENT_MATRIX_RELATIVE, subject.ingestion.MATRIX_HEADER, 3
    )
    materialized_rows = _read_csv(
        root / subject.OUTPUT_DIRECTORY_RELATIVE / subject.CENSUS_FILE,
        subject.CENSUS_COLUMNS_V1,
        1000,
    )
    reconciliation = reconciliation_owner.reconcile_real_completed_human_decisions_with_ei3_v1(root)
    computation, frozen, computed_reconciliation, computed_matrix = subject._compute_components_v1(root)
    if (
        predecessor_rows != list(frozen.rows)
        or matrix_rows != list(computed_matrix)
        or reconciliation.review_summary != computed_reconciliation.review_summary
        or materialized_rows != list(computation.rows)
    ):
        _fail("INDEPENDENT_SOURCE_OR_COMPUTATION_MISMATCH")
    fresh_first = subject.build_covapie_cumulative1000_current_global_readiness_artifacts_with_ei3_v1(root)
    fresh_second = subject.build_covapie_cumulative1000_current_global_readiness_artifacts_with_ei3_v1(root)
    observed = {
        name: (root / subject.OUTPUT_DIRECTORY_RELATIVE / name).read_bytes()
        for name in (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)
    }
    _verify_materialized_and_double_build_v1(observed, fresh_first, fresh_second)
    _validate_semantic_artifacts_v1(
        observed,
        root=root,
        predecessor_computation=frozen,
        reconciliation=reconciliation,
        matrix_rows=matrix_rows,
    )
    summary = json.loads(observed[subject.SUMMARY_FILE])
    manifest = json.loads(observed[subject.MANIFEST_FILE])
    predecessor_manifest = json.loads((root / subject.PREDECESSOR_MANIFEST_RELATIVE).read_text())
    predecessor_bindings = predecessor_manifest["semantic_source_bindings"]
    bindings = manifest.get("semantic_source_bindings")
    expected_output_bindings = [
        {
            "artifact_role": "REFRESHED_CENSUS_CSV",
            "path": (subject.OUTPUT_DIRECTORY_RELATIVE / subject.CENSUS_FILE).as_posix(),
            "byte_count": len(observed[subject.CENSUS_FILE]),
            "sha256": subject._sha256(observed[subject.CENSUS_FILE]),
        },
        {
            "artifact_role": "REFRESHED_SUMMARY_JSON",
            "path": (subject.OUTPUT_DIRECTORY_RELATIVE / subject.SUMMARY_FILE).as_posix(),
            "byte_count": len(observed[subject.SUMMARY_FILE]),
            "sha256": subject._sha256(observed[subject.SUMMARY_FILE]),
        },
    ]
    if (
        summary != computation.summary
        or manifest.get("schema_version") != subject.SCHEMA_VERSION
        or manifest.get("candidate_inventory")
        != {"exact_file_count": 7, "paths": list(subject.EXACT7_PATHS_V1)}
        or manifest.get("output_inventory", {}).get("exact_output_count") != 3
        or manifest.get("output_bindings_excluding_manifest_self") != expected_output_bindings
        or manifest.get("semantic_source_binding_count") != 204
        or type(bindings) is not list
        or bindings[:198] != predecessor_bindings
        or len(bindings[198:]) != 6
        or len({(item["path_namespace"], item["path"]) for item in bindings}) != 204
        or len({item["artifact_role"] for item in bindings[198:]}) != 6
        or {item["artifact_role"] for item in bindings[:198]}
        & {item["artifact_role"] for item in bindings[198:]}
        or manifest.get("manifest_self_SHA256_recorded") is not False
        or manifest.get("manifest_self_binding", {}).get("sha256_recorded_inside_self") is not False
        or manifest.get("derived_projection_contract_digests")
        != {
            "refreshed_census_sha256": subject._EXPECTED_REFRESHED_CENSUS_SHA256_V1,
            "refreshed_summary_sha256": subject._EXPECTED_REFRESHED_SUMMARY_SHA256_V1,
            "semantic_source_bindings_sha256": subject._EXPECTED_REFRESHED_SEMANTIC_SOURCE_BINDINGS_SHA256_V1,
            "authority_created": False,
        }
    ):
        _fail("MANIFEST_OR_SEMANTIC_BINDINGS_INVALID")
    candidate_bindings = manifest.get("candidate_contract_bindings")
    if candidate_bindings != subject._candidate_contract_bindings_v1(root):
        _fail("CANDIDATE_CONTRACT_BINDINGS_INVALID")
    target = set(subject.EI3_EXACT3_EVENT_IDS_V1)
    changed = []
    field_sets = []
    for old, new in zip(predecessor_rows, materialized_rows, strict=True):
        if old != new:
            changed.append(new["canonical_event_id"])
            field_sets.append({field for field in subject.CENSUS_COLUMNS_V1 if old[field] != new[field]})
    if set(changed) != target or len(changed) != 3 or any(fields != subject._ACTUAL_CHANGED_EI3_FIELDS_V1 for fields in field_sets):
        _fail("INDEPENDENT_EXACT3_OR_EXACT12_INVALID")
    matrix_by_event = {row["canonical_event_id"]: row for row in matrix_rows}
    facts_by_event = {
        fact.canonical_event_id: fact
        for fact in reconciliation.normalized_facts
        if fact.canonical_event_id in target
    }
    materialized_by_event = {row["canonical_event_id"]: row for row in materialized_rows}
    nullable_matrix_fields = (
        "selected_role_candidate_json",
        "role_profile_raw_json",
        "warhead_atom_ids_json",
        "linker_atom_ids_json",
        "scaffold_atom_ids_json",
        "minimal_seed_json",
        "minimal_seed_atom_ids_json",
        "primary_anchor_json",
        "structurally_applicable_task_ids_json",
    )
    if (
        len(subject.ingestion.MATRIX_HEADER) != 81
        or set(matrix_by_event) != target
        or set(facts_by_event) != target
        or [matrix_by_event[event]["target_covalent_connection_count"] for event in subject.EI3_EXACT3_EVENT_IDS_V1]
        != ["1", "1", "1"]
        or [matrix_by_event[event]["metal_context_connection_count"] for event in subject.EI3_EXACT3_EVENT_IDS_V1]
        != ["0", "0", "2"]
        or any(
            matrix_by_event[event][field] != "null"
            for event in subject.EI3_EXACT3_EVENT_IDS_V1
            for field in nullable_matrix_fields
        )
    ):
        _fail("INDEPENDENT_EI3_MATRIX_81_OR_NULL_BOUNDARY_INVALID")
    for event in subject.EI3_EXACT3_EVENT_IDS_V1:
        row = materialized_by_event[event]
        matrix = matrix_by_event[event]
        fact = facts_by_event[event]
        expected = {
            "current_global_status": generic.COMPLETED_HUMAN_NEGATIVE,
            "current_review_status": generic.COMPLETED_HUMAN_NEGATIVE,
            "human_review_completed": "true",
            "human_review_authority_source": fact.source_binding_path,
            "chemistry_disposition": generic.CHEMISTRY_POSITIVE,
            "chemistry_authority_source": subject.EI3_EVENT_MATRIX_SOURCE,
            "positive_authority_source": subject.EI3_EVENT_MATRIX_SOURCE,
            "task_relevance_disposition": generic.TASK_NOT_RELEVANT,
            "task_relevance_authority_source": subject.EI3_EVENT_MATRIX_SOURCE,
            "training_use_disposition": generic.TRAINING_NOT_APPLICABLE,
            "human_training_excluded": "false",
            "reactive_pair_sample_authoritative": "true",
            "role_partition_sample_authoritative": "false",
            "role_profile": subject.base.ROLE_NOT_ESTABLISHED,
            "canonical_mask_structural_labels_available": "false",
            "structurally_applicable_task_ids_json": "null",
            "training_use_include": "false",
            "future_training_admission_candidate": "false",
            "training_materialization_allowed_current_source": "false",
        }
        if (
            any(row[field] != value for field, value in expected.items())
            or matrix["negative_chemistry"] != "false"
            or matrix["task_domain_negative"] != "true"
            or matrix["role_partition_sample_authoritative"] != "false"
            or matrix["task_label_authority"] != "false"
            or matrix["accurate_PRE_required_before_training_feature_contract"] != "false"
            or fact.source_binding_path != subject.EI3_HUMAN_DECISION_SOURCE
        ):
            _fail("INDEPENDENT_EI3_SOURCE_BOUND_ROW_INVALID:" + event)
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
        "global_unreviewed": 157,
        "global_negative": 84,
        "chemistry_positive": 170,
        "task_not_relevant": 116,
        "training_not_applicable": 116,
        "pair_authority": 170,
        "role_authority": 156,
        "structural_labels": 156,
    }:
        _fail("INDEPENDENT_ROW_COUNTS_INVALID")
    review = summary.get("human_review", {})
    if (
        len(reconciliation.source_bindings) != 29
        or len(reconciliation.normalized_facts) != 157
        or len(reconciliation.reconciled_rows) != 338
        or (review.get("completed_event_count"), review.get("completed_unit_count"))
        != (181, 33)
        or (
            review.get("completed_negative_event_count"),
            review.get("completed_negative_unit_count"),
        )
        != (54, 12)
        or (
            review.get("completed_positive_event_count"),
            review.get("completed_positive_unit_count"),
        )
        != (127, 21)
        or (review.get("unreviewed_event_count"), review.get("unreviewed_unit_count"))
        != (157, 98)
    ):
        _fail("INDEPENDENT_RECONCILIATION_OR_HUMAN_REVIEW_COUNTS_INVALID")
    next_pending = summary.get("top_pending_review_units_by_event_yield", [{}])[0]
    if (
        next_pending.get("review_unit_id") != subject.NEXT_PENDING_REVIEW_UNIT_ID_V1
        or next_pending.get("ligand_component_ids") != ["AZP"]
        or next_pending.get("pdb_ids") != ["2A5I", "2A5K"]
        or next_pending.get("event_count") != 3
        or next_pending.get("raw_priority_rank") != 34
        or next_pending.get("rank") != 1
    ):
        _fail("INDEPENDENT_NEXT_PENDING_INVALID")
    orthogonal = summary.get("orthogonal_task_negative_chemistry_positive", {})
    if orthogonal != computation.summary["orthogonal_task_negative_chemistry_positive"] or (
        orthogonal.get("task_negative_chemistry_positive_population_count") != 26
        or orthogonal.get("historical_exact23_population_count") != 23
        or orthogonal.get("ei3_orthogonal_population_count") != 3
        or orthogonal.get("population_equals_historical_exact23_union_ei3_exact3") is not True
    ):
        _fail("INDEPENDENT_ORTHOGONAL_POPULATION_INVALID")
    refresh_contract = manifest.get("refresh_contract", {})
    authority_boundary = manifest.get("authority_boundary", {})
    if (
        refresh_contract.get("historical_formal_training_admitted_count") != 5
        or refresh_contract.get("formal_training_admitted_by_refresh") is not False
        or refresh_contract.get("task_label_authority") is not False
        or refresh_contract.get("ready_for_training") is not False
        or refresh_contract.get("training_started") is not False
        or refresh_contract.get("queue_refreshed") is not False
        or refresh_contract.get("next_review_started") is not False
        or authority_boundary.get("FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING") is not True
        or authority_boundary.get("STEP12D_IS_ONLY_SMOKE_LEGALITY_CHECK") is not True
    ):
        _fail("INDEPENDENT_AUTHORITY_OR_TRAINING_BOUNDARY_INVALID")
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
            "ei3_overlay_event_count": 3,
            "non_ei3_changed_row_count": 0,
            "unchanged_row_count": 997,
            "authorized_overlay_field_count": 19,
            "authorized_but_unchanged_field_count": 7,
            "actual_changed_field_count": 12,
        },
        "counts": counts,
        "human_review": summary["human_review"],
        "orthogonal": summary["orthogonal_task_negative_chemistry_positive"],
        "semantic_source_bindings": {
            "predecessor": 198,
            "successor": 204,
            "prefix_preserved": True,
            "additive": 6,
        },
        "next_priority_review": summary["top_pending_review_units_by_event_yield"][0],
        "tamper_probes": probes,
        "tamper_probe_count": len(probes),
        "lifecycle_simulations": lifecycle,
        "materialized_equals_fresh_build": observed == fresh_first,
        "deterministic_double_build": fresh_first == fresh_second,
        "independent_fresh_build_count": 2,
        "semantic_artifact_validation": True,
        "normal_and_raw_paths_share_comparator": True,
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
        print("COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_WITH_EI3_V1_PASS=false")
        print("ERROR=" + str(error))
        return 1
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    print("COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_WITH_EI3_V1_PASS=true")
    print("lifecycle=" + str(report["repository"]["profile"]))
    print("EI3_OVERLAY_EVENT_COUNT=3")
    print("NON_EI3_CHANGED_ROW_COUNT=0")
    print("UNCHANGED_ROW_COUNT=997")
    print("AUTHORIZED_OVERLAY_FIELD_COUNT=19")
    print("AUTHORIZED_BUT_UNCHANGED_FIELD_COUNT=7")
    print("ACTUAL_CHANGED_FIELD_COUNT=12")
    print("CURRENTLY_UNREVIEWED=157")
    print("COMPLETED_HUMAN_NEGATIVE=84")
    print("COMPLETED_HUMAN_POSITIVE=127")
    print("HUMAN_COMPLETED_EVENT_COUNT=181")
    print("HUMAN_COMPLETED_UNIT_COUNT=33")
    print("CHEMISTRY_POSITIVE_COUNT=170")
    print("TASK_NOT_RELEVANT_COUNT=116")
    print("TRAINING_NOT_APPLICABLE_COUNT=116")
    print("REACTIVE_PAIR_SAMPLE_AUTHORITATIVE_COUNT=170")
    print("ROLE_PARTITION_SAMPLE_AUTHORITATIVE_COUNT=156")
    print("CANONICAL_MASK_STRUCTURAL_LABELS_AVAILABLE_COUNT=156")
    print("CANONICAL_TASK_APPLICABILITY_COUNTS=[156,56,56,156,156]")
    print("ORTHOGONAL_TASK_NEGATIVE_CHEMISTRY_POSITIVE_COUNT=26")
    print("PREDECESSOR_SEMANTIC_SOURCE_BINDING_COUNT=198")
    print("SUCCESSOR_SEMANTIC_SOURCE_BINDING_COUNT=204")
    print("NEXT_PRIORITY_REVIEW_LIGAND=AZP")
    print('NEXT_PRIORITY_REVIEW_PDB_IDS=["2A5I","2A5K"]')
    print("NEXT_PRIORITY_REVIEW_UNIT=COVAPIE_BULK_REVIEW_UNIT_7FB64BA2D198B24F")
    print("NEXT_PRIORITY_REVIEW_RAW_PRIORITY_RANK=34")
    print("NEXT_PRIORITY_REVIEW_CURRENT_PENDING_RANK=1")
    print("NEXT_PRIORITY_REVIEW_EVENT_COUNT=3")
    print("CENSUS_REFRESH_PERFORMED=true")
    print("QUEUE_REFRESH_PERFORMED=false")
    print("NEXT_REVIEW_STARTED=false")
    print("EI3_REVIEW_STATE_CREATED_BY_THIS_ROUND=false")
    print("NEW_HUMAN_AUTHORITY_CREATED=false")
    print("NEW_REUSABLE_AUTHORITY_CREATED=false")
    print("TASK_LABEL_AUTHORITY=false")
    print("FORMAL_TRAINING_ADMITTED_BY_THIS_ROUND=false")
    print("READY_FOR_TRAINING=false")
    print("TRAINING_STARTED=false")
    print("COMMIT_PERFORMED=false")
    print("PUSH_PERFORMED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
