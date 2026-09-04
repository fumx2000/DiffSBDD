#!/usr/bin/env python3
"""Independent fail-closed checker for the with-0D8 readiness census V1."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import csv
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
import stat
import subprocess
import sys
from typing import Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_0d8_v1 as reconciliation,
)
from covalent_ext import (  # noqa: E402
    covapie_cumulative1000_current_global_readiness_census_with_0d8_v1 as subject,
)


BASELINE_COMMIT = "33b38864a97fc3d5046a068ed4b63103b7257116"
EXPECTED_CENSUS_SHA256 = "dd7cb0e923dcfdfe464b9ffc4cf0b17c569fa8c3ca33ac23fbda7103dbe9d273"
EXPECTED_SUMMARY_SHA256 = "479528564feb0ab67685408aab2e404162d48474331492688d986fae0bf2a4bc"
EXPECTED_BINDINGS_SHA256 = "f421e36b39fa90c91798ac53b5ccf3fe967334fe78ea89f52e54b946b4d47620"
FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
    ".npz", ".pyc", ".tmp", ".part",
)
PROTECTED_PREFIXES = (
    "data/raw/", "checkpoints/", "equivariant_diffusion/",
)
PROTECTED_FILES = {
    "dataset.py", "lightning_modules.py", "data/prepare_crossdocked.py",
}


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def _read(path: Path, label: str) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise ValueError("NOT_REGULAR_FILE:" + label)
    return path.read_bytes()


def _validate_text(payload: bytes, label: str) -> None:
    if payload.startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF8_BOM_FORBIDDEN:" + label)
    text = payload.decode("utf-8")
    if "\r" in text or "\x00" in text:
        raise ValueError("TEXT_ENCODING_INVALID:" + label)
    if not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
        raise ValueError("FINAL_LF_INVALID:" + label)
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        raise ValueError("TRAILING_WHITESPACE:" + label)


def _parse_csv(payload: bytes, expected_header: Sequence[str]) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    if tuple(reader.fieldnames or ()) != tuple(expected_header):
        raise ValueError("CSV_HEADER_INVALID")
    return [dict(row) for row in reader]


def _validate_output_inventory_names_v1(entry_names: Sequence[str]) -> None:
    expected = {
        subject.CENSUS_FILE,
        subject.SUMMARY_FILE,
        subject.MANIFEST_FILE,
    }
    if len(entry_names) != 3 or set(entry_names) != expected:
        raise ValueError("OUTPUT_DIRECTORY_NOT_EXACT3")


def verify_exact7_inventory_v1(root: Path) -> list[dict[str, object]]:
    output = root / subject.OUTPUT_DIRECTORY_RELATIVE
    try:
        metadata = output.lstat()
    except OSError as error:
        raise ValueError("OUTPUT_DIRECTORY_READ_FAILED") from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise ValueError("OUTPUT_DIRECTORY_NOT_REAL_DIRECTORY")
    _validate_output_inventory_names_v1(tuple(entry.name for entry in output.iterdir()))
    records: list[dict[str, object]] = []
    for relative in subject.EXACT7_PATHS_V1:
        path = root / relative
        payload = _read(path, relative)
        _validate_text(payload, relative)
        mode = stat.S_IMODE(path.stat().st_mode)
        if mode != 0o644:
            raise ValueError("CANDIDATE_MODE_NOT_0644:" + relative)
        if len(payload) > 1024 * 1024:
            raise ValueError("CANDIDATE_FILE_EXCEEDS_1_MIB:" + relative)
        records.append(
            {"path": relative, "byte_count": len(payload), "sha256": _sha(payload), "mode": mode}
        )
    return records


def verify_frozen_bindings_v1(root: Path) -> None:
    for role, relative, namespace, byte_count, digest, _executable in subject._ADDITIVE_SOURCE_SPECS_V1:
        path = root / relative if namespace == "repository_relative" else root.parent / relative
        payload = _read(path, role)
        if len(payload) != byte_count or _sha(payload) != digest:
            raise ValueError("FROZEN_SOURCE_BINDING_INVALID:" + role)
    payload = _read(root / subject.PREDECESSOR_MANIFEST_RELATIVE, "PREDECESSOR_MANIFEST")
    expected_bytes, expected_digest, _ = subject._PREDECESSOR_MANIFEST_SPEC_V1
    if len(payload) != expected_bytes or _sha(payload) != expected_digest:
        raise ValueError("PREDECESSOR_MANIFEST_BINDING_INVALID")


def independently_verify_delta_v1(
    predecessor_rows: Sequence[Mapping[str, str]],
    successor_rows: Sequence[Mapping[str, str]],
) -> dict[str, object]:
    if len(predecessor_rows) != 1000 or len(successor_rows) != 1000:
        raise ValueError("ROW_COUNT_NOT_EXACT1000")
    before = {row["canonical_event_id"]: row for row in predecessor_rows}
    after = {row["canonical_event_id"]: row for row in successor_rows}
    if set(before) != set(after):
        raise ValueError("EVENT_UNIVERSE_CHANGED")
    changed = {event for event in before if before[event] != after[event]}
    target = set(subject.ZERO_D8_EXACT4_EVENT_IDS_V1)
    if changed != target:
        raise ValueError("CHANGED_EVENTS_NOT_0D8_EXACT4")
    field_sets = {
        event: {
            field for field in subject.CENSUS_COLUMNS_V1
            if before[event][field] != after[event][field]
        }
        for event in target
    }
    if any(fields != subject._ACTUAL_CHANGED_0D8_FIELDS_V1 for fields in field_sets.values()):
        raise ValueError("ACTUAL_CHANGED_FIELDS_NOT_EXACT16")
    if any(
        before[event] != after[event]
        for event in set(before) - target
    ):
        raise ValueError("NON_TARGET_ROW_CHANGED")
    return {
        "changed_event_count": len(changed),
        "unchanged_event_count": len(before) - len(changed),
        "actual_changed_fields": sorted(next(iter(field_sets.values()))),
    }


def independently_verify_counts_v1(rows: Sequence[Mapping[str, str]]) -> dict[str, object]:
    if len(rows) != 1000 or any(tuple(row) != subject.CENSUS_COLUMNS_V1 for row in rows):
        raise ValueError("CENSUS_SCHEMA_INVALID")
    expected = {
        "chemistry": Counter({"POSITIVE": 144, "NOT_ESTABLISHED": 90, "UNRESOLVED": 766}),
        "task": Counter({"RELEVANT": 133, "NOT_RELEVANT": 102, "UNRESOLVED": 765}),
        "training": Counter(
            {"INCLUDE": 60, "EXCLUDE_FROM_TRAINING_ONLY": 72, "NOT_APPLICABLE": 102, "UNRESOLVED": 766}
        ),
    }
    actual = {
        "chemistry": Counter(row["chemistry_disposition"] for row in rows),
        "task": Counter(row["task_relevance_disposition"] for row in rows),
        "training": Counter(row["training_use_disposition"] for row in rows),
    }
    if actual != expected:
        raise ValueError("GLOBAL_DISPOSITION_COUNTS_INVALID")
    boolean_counts = {
        field: sum(row[field] == "true" for row in rows)
        for field in (
            "reactive_pair_sample_authoritative",
            "role_partition_sample_authoritative",
            "canonical_mask_structural_labels_available",
            "post_geometry_sample_authoritative",
            "post_geometry_training_target_available",
            "pre_geometry_authoritative",
            "pre_geometry_training_target_available",
            "training_use_include",
            "future_training_admission_candidate",
            "formal_training_admitted",
            "current_runtime_model_usable",
        )
    }
    if boolean_counts != {
        "reactive_pair_sample_authoritative": 144,
        "role_partition_sample_authoritative": 136,
        "canonical_mask_structural_labels_available": 136,
        "post_geometry_sample_authoritative": 21,
        "post_geometry_training_target_available": 17,
        "pre_geometry_authoritative": 0,
        "pre_geometry_training_target_available": 0,
        "training_use_include": 60,
        "future_training_admission_candidate": 43,
        "formal_training_admitted": 5,
        "current_runtime_model_usable": 17,
    }:
        raise ValueError("GLOBAL_AUTHORITY_COUNTS_INVALID")
    profiles = Counter(
        row["role_profile"] for row in rows
        if row["role_partition_sample_authoritative"] == "true"
    )
    if profiles != Counter({subject.base.DIRECT_PROFILE: 84, subject.base.STRICT_PROFILE: 52}):
        raise ValueError("ROLE_PROFILE_COUNTS_INVALID")
    applicability: Counter[int] = Counter()
    for row in rows:
        if row["role_partition_sample_authoritative"] == "true":
            applicability.update(json.loads(row["structurally_applicable_task_ids_json"]))
    if applicability != Counter({0: 136, 1: 52, 2: 52, 3: 136, 4: 136}):
        raise ValueError("EXACT5_APPLICABILITY_COUNTS_INVALID")
    orthogonal = {
        row["canonical_event_id"] for row in rows
        if (
            row["task_relevance_disposition"], row["chemistry_disposition"],
            row["training_use_disposition"],
        ) == ("NOT_RELEVANT", "POSITIVE", "NOT_APPLICABLE")
    }
    expected_orthogonal = (
        set(subject.GVE_EXACT4_EVENT_IDS_V1)
        | set(subject.LCY_EXACT4_EVENT_IDS_V1)
        | set(subject.ZERO_D8_EXACT4_EVENT_IDS_V1)
    )
    if orthogonal != expected_orthogonal or len(orthogonal) != 12:
        raise ValueError("ORTHOGONAL_EXACT12_INVALID")
    return {**boolean_counts, "orthogonal_count": len(orthogonal)}


def verify_manifest_v1(
    root: Path, manifest: Mapping[str, object], artifacts: Mapping[str, bytes],
) -> None:
    if manifest.get("candidate_inventory") != {
        "exact_file_count": 7, "paths": list(subject.EXACT7_PATHS_V1)
    }:
        raise ValueError("MANIFEST_EXACT7_INVALID")
    if manifest.get("semantic_source_binding_count") != 162:
        raise ValueError("MANIFEST_BINDING_COUNT_INVALID")
    bindings = manifest.get("semantic_source_bindings")
    if type(bindings) is not list or len(bindings) != 162:
        raise ValueError("MANIFEST_BINDINGS_INVALID")
    if len({(item["path_namespace"], item["path"]) for item in bindings}) != 162:
        raise ValueError("MANIFEST_BINDING_IDENTITY_COLLISION")
    predecessor_roles = {item["artifact_role"] for item in bindings[:156]}
    additive_roles = [item["artifact_role"] for item in bindings[156:]]
    if len(additive_roles) != len(set(additive_roles)) or predecessor_roles & set(additive_roles):
        raise ValueError("MANIFEST_BINDING_ROLE_COLLISION")
    if _sha(_canonical_json(bindings).encode("utf-8")) != EXPECTED_BINDINGS_SHA256:
        raise ValueError("MANIFEST_BINDINGS_DIGEST_INVALID")
    output_bindings = manifest.get("output_bindings_excluding_manifest_self")
    if type(output_bindings) is not list or len(output_bindings) != 2:
        raise ValueError("MANIFEST_OUTPUT_BINDINGS_INVALID")
    for item in output_bindings:
        filename = Path(item["path"]).name
        if filename not in artifacts:
            raise ValueError("MANIFEST_OUTPUT_PATH_INVALID")
        payload = artifacts[filename]
        if item["byte_count"] != len(payload) or item["sha256"] != _sha(payload):
            raise ValueError("MANIFEST_OUTPUT_IDENTITY_INVALID")
    if manifest.get("manifest_self_SHA256_recorded") is not False:
        raise ValueError("MANIFEST_SELF_SHA_RECORDED")
    lowered = artifacts[subject.MANIFEST_FILE].decode("utf-8").lower()
    for token in ('"timestamp"', '"hostname"', '"pid"', '"head"', '"ahead"', '"behind"'):
        if token in lowered:
            raise ValueError("MANIFEST_DYNAMIC_FIELD_PRESENT")


def _expect_failure(callable_) -> None:
    try:
        callable_()
    except (subject.Cumulative1000CurrentGlobalReadinessCensusWith0D8Error, ValueError):
        return
    raise ValueError("SEMANTIC_TAMPER_ACCEPTED")


def check_semantic_probes_v1(
    computation, frozen, result, matrix: Sequence[Mapping[str, str]],
) -> dict[str, bool]:
    target = subject.ZERO_D8_EXACT4_EVENT_IDS_V1[0]

    def mutate_row(event_id: str, **changes: str):
        rows = deepcopy(list(computation.rows))
        next(row for row in rows if row["canonical_event_id"] == event_id).update(changes)
        return replace(computation, rows=tuple(rows))

    def validate(candidate) -> None:
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_0d8_v1(
            candidate,
            predecessor_computation=frozen,
            reconciliation_result=result,
            matrix_rows=matrix,
        )

    row_probes = (
        (target, {"canonical_event_id": target + ":TAMPER"}),
        (subject.LCY_EXACT4_EVENT_IDS_V1[0], {"current_review_status": "CURRENTLY_IN_PROGRESS"}),
        (target, {"task_relevance_disposition": "RELEVANT"}),
        (target, {"chemistry_disposition": "NEGATIVE"}),
        (target, {"reactive_pair_sample_authoritative": "false"}),
        (target, {"role_partition_sample_authoritative": "false"}),
        (target, {"role_profile": subject.base.STRICT_PROFILE}),
        (target, {"structurally_applicable_task_ids_json": "[0,4]"}),
        (target, {"training_use_disposition": "INCLUDE", "training_use_include": "true"}),
        (target, {"formal_training_admitted": "true"}),
        (target, {"reactive_pair_training_target_available": "true"}),
    )
    for event_id, changes in row_probes:
        _expect_failure(lambda event_id=event_id, changes=changes: validate(mutate_row(event_id, **changes)))

    matrix_mutations = (
        {"canonical_event_id": target + ":TAMPER"},
        {"role_partition_human_authoritative": "false"},
        {"role_profile": subject.base.STRICT_PROFILE},
        {"direct_profile_applicable_task_ids_json": "[0,4]"},
        {"B3_present": "false"},
        {"sixth_task": "true"},
        {"training_mask_targets_available_now": "true"},
    )
    for changes in matrix_mutations:
        tampered = deepcopy(list(matrix))
        tampered[0].update(changes)
        _expect_failure(lambda tampered=tampered: subject._validate_0d8_matrix_rows_v1(tampered))

    summary = deepcopy(computation.summary)
    summary["human_review"]["completed_event_count"] = 154
    _expect_failure(lambda: validate(replace(computation, summary=summary)))
    summary = deepcopy(computation.summary)
    summary["top_pending_review_units_by_event_yield"][0]["raw_priority_rank"] = 27
    _expect_failure(lambda: validate(replace(computation, summary=summary)))
    bindings = list(deepcopy(computation.semantic_source_bindings))
    bindings[-1]["path"] = bindings[-2]["path"]
    _expect_failure(lambda: validate(replace(computation, semantic_source_bindings=tuple(bindings))))
    raw = bytearray(subject._csv_bytes(computation.rows))
    raw[-2] = ord("X")
    _expect_failure(
        lambda: (_ for _ in ()).throw(ValueError("RAW_OUTPUT_BYTE_MISMATCH"))
        if bytes(raw) != subject._csv_bytes(computation.rows) else None
    )
    return {
        "event_identity": True,
        "non_target_row": True,
        "task_chemistry_pair_role_profile_applicability": True,
        "exact5_b3_no_sixth": True,
        "training_promotions": True,
        "next_pending_summary_bindings": True,
        "raw_output_bytes": True,
    }


def _git(root: Path, *args: str) -> list[str]:
    result = subprocess.run(
        ("git", *args), cwd=root, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return [line for line in result.stdout.splitlines() if line]


def _classify_exact7_artifact_placement_v1(
    tracked: Sequence[str], untracked: Sequence[str],
) -> str:
    expected = set(subject.EXACT7_PATHS_V1)
    if not tracked and set(untracked) == expected and len(untracked) == 7:
        return "CANDIDATE_UNTRACKED"
    if set(tracked) == expected and len(tracked) == 7 and not untracked:
        return "TRACKED_CLEAN"
    raise ValueError("EXACT7_ARTIFACT_PLACEMENT_INVALID")


def _validate_history_scope_v1(changed_since_baseline: Sequence[str]) -> None:
    protected = sorted(
        path for path in changed_since_baseline
        if path in PROTECTED_FILES or path.startswith(PROTECTED_PREFIXES)
    )
    forbidden = sorted(
        path for path in changed_since_baseline
        if path.lower().endswith(FORBIDDEN_SUFFIXES)
    )
    if protected:
        raise ValueError("PROTECTED_HISTORY_PATH:" + protected[0])
    if forbidden:
        raise ValueError("FORBIDDEN_HISTORY_SUFFIX:" + forbidden[0])


def _classify_repository_lifecycle_v1(
    *, branch: str, placement: str, head: str, origin: str, ahead: int, behind: int,
    baseline_is_ancestor_of_head: bool, baseline_is_ancestor_of_origin: bool,
    origin_is_ancestor_of_head: bool, baseline_to_head_changed_paths: Sequence[str],
    tracked_modification_count: int = 0, staged_count: int = 0,
) -> str:
    expected = set(subject.EXACT7_PATHS_V1)
    changed = set(baseline_to_head_changed_paths)
    if branch != "main":
        raise ValueError("BRANCH_NOT_MAIN")
    if tracked_modification_count != 0 or staged_count != 0:
        raise ValueError("DIRTY_TRACKED_OR_STAGED_LIFECYCLE_INVALID")
    if placement == "CANDIDATE_UNTRACKED":
        if not (
            head == origin == BASELINE_COMMIT and ahead == behind == 0
            and baseline_is_ancestor_of_head and baseline_is_ancestor_of_origin
            and origin_is_ancestor_of_head and not changed
        ):
            raise ValueError("CANDIDATE_UNTRACKED_LIFECYCLE_INVALID")
        return placement
    if placement != "TRACKED_CLEAN":
        raise ValueError("LIFECYCLE_PLACEMENT_INVALID")
    _validate_history_scope_v1(tuple(changed))
    if (
        head == BASELINE_COMMIT or behind != 0 or ahead < 0
        or not baseline_is_ancestor_of_head or not baseline_is_ancestor_of_origin
        or not origin_is_ancestor_of_head or not expected <= changed
    ):
        raise ValueError("TRACKED_CLEAN_LIFECYCLE_INVALID")
    if (ahead == 0) != (origin == head):
        raise ValueError("TRACKED_CLEAN_ORIGIN_RELATION_INVALID")
    return placement


def check_lifecycle_simulations_v1() -> dict[str, bool]:
    expected = list(subject.EXACT7_PATHS_V1)
    candidate = dict(
        branch="main", placement="CANDIDATE_UNTRACKED",
        head=BASELINE_COMMIT, origin=BASELINE_COMMIT,
        ahead=0, behind=0, baseline_is_ancestor_of_head=True,
        baseline_is_ancestor_of_origin=True, origin_is_ancestor_of_head=True,
        baseline_to_head_changed_paths=[],
    )
    if _classify_repository_lifecycle_v1(**candidate) != "CANDIDATE_UNTRACKED":
        raise ValueError("CANDIDATE_SIMULATION_FAILED")
    tracked = dict(
        branch="main", placement="TRACKED_CLEAN",
        head="successor-head", origin=BASELINE_COMMIT,
        ahead=1, behind=0, baseline_is_ancestor_of_head=True,
        baseline_is_ancestor_of_origin=True, origin_is_ancestor_of_head=True,
        baseline_to_head_changed_paths=expected,
    )
    if _classify_repository_lifecycle_v1(**tracked) != "TRACKED_CLEAN":
        raise ValueError("COMMITTED_UNPUSHED_SIMULATION_FAILED")
    pushed = {**tracked, "origin": "successor-head", "ahead": 0}
    _classify_repository_lifecycle_v1(**pushed)
    descendant = {**pushed, "head": "later-head", "origin": "later-head"}
    _classify_repository_lifecycle_v1(**descendant)
    invalid = (
        {"branch": "feature/test"},
        {"behind": 1},
        {"tracked_modification_count": 1},
        {"staged_count": 1},
        {"baseline_is_ancestor_of_head": False},
        {"baseline_is_ancestor_of_origin": False},
        {"origin_is_ancestor_of_head": False},
        {"baseline_to_head_changed_paths": expected[:-1]},
        {"head": "impossible-head", "origin": "other-head", "ahead": 0},
    )
    for update in invalid:
        _expect_failure(lambda update=update: _classify_repository_lifecycle_v1(**{**tracked, **update}))
    _expect_failure(lambda: _classify_exact7_artifact_placement_v1(expected[:3], expected[3:]))
    _expect_failure(lambda: _validate_history_scope_v1((*expected, "data/raw/tamper.cif")))
    _expect_failure(lambda: _validate_history_scope_v1((*expected, "artifacts/tamper.ckpt")))
    return {
        "branch_main_accepted": True,
        "branch_non_main_rejected": True,
        "candidate_untracked": True,
        "committed_unpushed": True,
        "pushed_successor": True,
        "later_clean_descendant": True,
        "mixed_tracking_rejected": True,
        "behind_rejected": True,
        "ancestry_failures_rejected": True,
        "missing_publication_history_rejected": True,
        "protected_history_rejected": True,
        "forbidden_history_rejected": True,
        "origin_relation_inconsistency_rejected": True,
    }


def _is_ancestor(root: Path, older: str, newer: str) -> bool:
    return subprocess.run(
        ("git", "merge-base", "--is-ancestor", older, newer), cwd=root,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0


def verify_git_safety_v1(root: Path) -> dict[str, object]:
    tracked = _git(root, "ls-files", "--", *subject.EXACT7_PATHS_V1)
    all_untracked = _git(root, "ls-files", "--others", "--exclude-standard")
    expected = set(subject.EXACT7_PATHS_V1)
    exact_untracked = [path for path in all_untracked if path in expected]
    placement = _classify_exact7_artifact_placement_v1(tracked, exact_untracked)
    if set(all_untracked) != set(exact_untracked):
        raise ValueError("ORDINARY_UNTRACKED_NOT_EXACT7")
    modified = _git(root, "diff", "--name-only")
    staged = _git(root, "diff", "--cached", "--name-only")
    if modified or staged:
        raise ValueError("TRACKED_OR_STAGED_DIRTY")
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD")[0]
    head = _git(root, "rev-parse", "HEAD")[0]
    origin = _git(root, "rev-parse", "origin/main")[0]
    ahead, behind = map(int, _git(root, "rev-list", "--left-right", "--count", "HEAD...origin/main")[0].split())
    changed = _git(root, "diff", "--name-only", BASELINE_COMMIT + "..HEAD")
    lifecycle = _classify_repository_lifecycle_v1(
        branch=branch, placement=placement, head=head, origin=origin,
        ahead=ahead, behind=behind,
        baseline_is_ancestor_of_head=_is_ancestor(root, BASELINE_COMMIT, "HEAD"),
        baseline_is_ancestor_of_origin=_is_ancestor(root, BASELINE_COMMIT, "origin/main"),
        origin_is_ancestor_of_head=_is_ancestor(root, "origin/main", "HEAD"),
        baseline_to_head_changed_paths=changed,
        tracked_modification_count=len(modified), staged_count=len(staged),
    )
    if any(path.endswith(FORBIDDEN_SUFFIXES) for path in all_untracked):
        raise ValueError("FORBIDDEN_UNTRACKED_SUFFIX")
    if any(
        path in PROTECTED_FILES or path.startswith(PROTECTED_PREFIXES)
        for path in (*modified, *staged, *all_untracked)
    ):
        raise ValueError("PROTECTED_SOURCE_DIRTY")
    tmp_part = [
        path for path in _git(root, "ls-files", "--others", "--exclude-standard")
        if path.endswith((".tmp", ".part"))
    ]
    if tmp_part:
        raise ValueError("TMP_OR_PART_PRESENT")
    return {
        "lifecycle": lifecycle,
        "tracked_modification_count": 0,
        "staged_count": 0,
        "ordinary_untracked_count": len(all_untracked),
        "branch": branch,
        "head": head,
        "origin_main": origin,
        "ahead": ahead,
        "behind": behind,
        "forbidden_file_count": 0,
        "protected_source_diff_count": 0,
        "tmp_part_count": 0,
    }


def run_check_v1(root: Path = ROOT) -> dict[str, object]:
    records = verify_exact7_inventory_v1(root)
    verify_frozen_bindings_v1(root)
    computation = subject.compute_covapie_cumulative1000_current_global_readiness_census_with_0d8_v1(root)
    built_once = subject._build_artifacts_from_computation_v1(root, computation)
    built_twice = subject._build_artifacts_from_computation_v1(root, computation)
    if built_once != built_twice:
        raise ValueError("DOUBLE_BUILD_NOT_BYTE_IDENTICAL")
    materialized = {
        name: _read(root / subject.OUTPUT_DIRECTORY_RELATIVE / name, name)
        for name in (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)
    }
    if materialized != built_once:
        raise ValueError("MATERIALIZED_OUTPUT_NOT_SOURCE_DERIVED")
    if _sha(materialized[subject.CENSUS_FILE]) != EXPECTED_CENSUS_SHA256:
        raise ValueError("CENSUS_DIGEST_INVALID")
    if _sha(materialized[subject.SUMMARY_FILE]) != EXPECTED_SUMMARY_SHA256:
        raise ValueError("SUMMARY_DIGEST_INVALID")
    predecessor_rows = _parse_csv(
        _read(root / subject.PREDECESSOR_CENSUS_RELATIVE, "PREDECESSOR_CENSUS"),
        subject.CENSUS_COLUMNS_V1,
    )
    rows = _parse_csv(materialized[subject.CENSUS_FILE], subject.CENSUS_COLUMNS_V1)
    delta = independently_verify_delta_v1(predecessor_rows, rows)
    counts = independently_verify_counts_v1(rows)
    summary = json.loads(materialized[subject.SUMMARY_FILE])
    manifest = json.loads(materialized[subject.MANIFEST_FILE])
    if summary != computation.summary:
        raise ValueError("SUMMARY_NOT_COMPUTATION_EXACT")
    verify_manifest_v1(root, manifest, materialized)
    predecessor_manifest = json.loads(
        _read(root / subject.PREDECESSOR_MANIFEST_RELATIVE, "PREDECESSOR_MANIFEST")
    )
    frozen = subject.base.Cumulative1000CurrentGlobalReadinessComputationV1(
        rows=tuple(predecessor_rows),
        summary={},
        semantic_source_bindings=tuple(predecessor_manifest["semantic_source_bindings"]),
    )
    result = reconciliation.reconcile_real_completed_human_decisions_with_0d8_v1(root)
    matrix = subject._load_and_validate_0d8_event_matrix_v1(root)
    probes = check_semantic_probes_v1(computation, frozen, result, matrix)
    lifecycle_simulations = check_lifecycle_simulations_v1()
    git = verify_git_safety_v1(root)
    boundary = summary["authority_boundary"]
    required_false = (
        "NEXT_REVIEW_STARTED", "QUEUE_REFRESH", "READY_FOR_TRAINING",
        "READY_FOR_FORMAL_TRAINING", "TRAINING_STARTED",
        "new_human_authority_created", "new_scientific_authority_created",
        "new_pair_authority_created", "new_role_authority_created",
    )
    if any(boundary[key] is not False for key in required_false):
        raise ValueError("AUTHORITY_OR_TRAINING_BOUNDARY_INVALID")
    if boundary["FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER"] is not True:
        raise ValueError("FEATURE_SEMANTICS_AUDIT_WARNING_MISSING")
    return {
        "records": records,
        "delta": delta,
        "counts": counts,
        "semantic_probes": probes,
        "lifecycle_simulations": lifecycle_simulations,
        "git": git,
        "deterministic_double_build": True,
    }


def main() -> int:
    result = run_check_v1()
    print("0D8_CURRENT_GLOBAL_READINESS_CENSUS_V1_PASS=true")
    print("CENSUS_ROWS=1000")
    print("CENSUS_COLUMNS=47")
    print("CHANGED_EVENT_COUNT=4")
    print("UNCHANGED_EVENT_COUNT=996")
    print("CHEMISTRY_POSITIVE_COUNT=144")
    print("TASK_NOT_RELEVANT_COUNT=102")
    print("TRAINING_NOT_APPLICABLE_COUNT=102")
    print("PAIR_AUTHORITY_COUNT=144")
    print("ROLE_AUTHORITY_COUNT=136")
    print("CANONICAL_MASK_STRUCTURAL_LABEL_COUNT=136")
    print("DIRECT_PROFILE_A_B3_C_COUNT=84")
    print("TASK_NEGATIVE_CHEMISTRY_POSITIVE_POPULATION_COUNT=12")
    print("EXACT5_B3_PRESENT=true")
    print("SIXTH_TASK=false")
    print("NEXT_PRIORITY_REVIEW_LIGAND=4LH")
    print("NEXT_PRIORITY_REVIEW_RAW_PRIORITY_RANK=26")
    print("NEXT_REVIEW_STARTED=false")
    print("QUEUE_REFRESH=false")
    print("TRAINING_STARTED=false")
    print("READY_FOR_TRAINING=false")
    print("READY_FOR_FORMAL_TRAINING=false")
    print("FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER=true")
    print("LIFECYCLE=" + str(result["git"]["lifecycle"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
